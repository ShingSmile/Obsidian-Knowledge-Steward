from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Sequence

from app.config import Settings
from app.retrieval.embeddings import embed_texts

from app.contracts.workflow import AskResultMode, AskWorkflowResult, GuardrailAction
from app.contracts.workflow import RuntimeFaithfulnessOutcome, RuntimeFaithfulnessSignal


CITATION_PATTERN = re.compile(r"\[(\d+)\]")
CLAIM_SPLIT_PATTERN = re.compile(r"[。！？!?；;\n]+")
LEADING_BULLET_PATTERN = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+|#+\s*)")
LATIN_TOKEN_PATTERN = re.compile(r"[a-z0-9_]{3,}")
CJK_SEQUENCE_PATTERN = re.compile(r"[\u4e00-\u9fff]{2,}")
INLINE_MARKUP_PATTERN = re.compile(r"[*_`~]+")
CLAIM_PREAMBLE_PATTERN = re.compile(
    r"^\s*(?:根据(?:检索证据|[^，,:：]{0,40}(?:记录|笔记|内容|总结|结果|显示|可知))[,，:：]?\s*)+"
)
PHRASE_SPLIT_PATTERN = re.compile(r"[：:，,、/（）()\[\]-]+")
PHRASE_CONNECTOR_PATTERN = re.compile(r"(?:以及|及|与|并|和)")
PURE_NUMBER_PATTERN = re.compile(r"^\d+$")
NEGATION_TOKENS = (
    "不",
    "不是",
    "并非",
    "没有",
    "没",
    "未",
    "无",
    "尚未",
)
EMBEDDING_ENTAILMENT_THRESHOLD = 0.82
EMBEDDING_SUPPORT_THRESHOLD = 0.68
LEXICAL_ENTAILMENT_THRESHOLD = 0.72
LEXICAL_CONTRADICTION_THRESHOLD = 0.5
PHRASE_SUPPORT_THRESHOLD = 0.67
RUNTIME_FAITHFULNESS_SCORE_THRESHOLD = 0.67
GENERIC_PHRASE_PREFIXES = (
    "根据",
    "包括",
    "包含",
    "涵盖",
    "主要",
    "重点",
    "明确",
    "总结了",
    "总结",
    "提到",
    "说明",
    "配置",
    "功能点",
    "注意点",
)
GENERIC_PHRASE_SUFFIXES = (
    "等展示内容",
    "展示内容",
    "等内容",
    "等功能点",
    "功能点",
    "等功能",
    "功能",
    "等注意点",
    "注意点",
)
CONTEXTUAL_PHRASE_MARKERS = (
    "今日总结",
    "今日进程",
    "工作任务",
    "待完成事项",
    "未完成事项",
    "以下模块",
    "以下四个模块",
    "根据检索证据",
)


@dataclass(frozen=True)
class _ClaimVerdict:
    claim: str
    verdict: str
    reason: str
    best_evidence: str | None
    lexical_overlap: float
    similarity: float | None


def build_ask_faithfulness_snapshot(
    ask_result: AskWorkflowResult,
) -> dict[str, Any]:
    if ask_result.guardrail_action == GuardrailAction.REFUSE_STRONG_CLAIM:
        return {
            "bucket": "unsupported_claim",
            "consistent": False,
            "reason": "answer_contains_terms_not_found_in_cited_evidence",
            "citation_numbers": list(range(1, len(ask_result.citations) + 1)),
            "cited_candidate_count": len(ask_result.citations),
            "unsupported_terms": [],
            "answer_text": _strip_citation_markers(ask_result.answer),
        }

    if ask_result.mode != AskResultMode.GENERATED_ANSWER:
        return {
            "bucket": "not_generated_answer",
            "consistent": None,
            "reason": "ask_result_not_generated_answer",
            "citation_numbers": [],
            "cited_candidate_count": 0,
            "unsupported_terms": [],
            "answer_text": _strip_citation_markers(ask_result.answer),
        }

    citation_numbers = _dedupe_preserve_order(
        int(match.group(1)) for match in CITATION_PATTERN.finditer(ask_result.answer)
    )
    if not citation_numbers:
        return {
            "bucket": "citation_missing",
            "consistent": False,
            "reason": "answer_has_no_citation_markers",
            "citation_numbers": [],
            "cited_candidate_count": 0,
            "unsupported_terms": [],
            "answer_text": _strip_citation_markers(ask_result.answer),
        }

    invalid_numbers = [
        citation_number
        for citation_number in citation_numbers
        if citation_number < 1 or citation_number > len(ask_result.retrieved_candidates)
    ]
    if invalid_numbers:
        return {
            "bucket": "citation_invalid",
            "consistent": False,
            "reason": "answer_references_missing_candidates",
            "citation_numbers": citation_numbers,
            "invalid_citation_numbers": invalid_numbers,
            "cited_candidate_count": 0,
            "unsupported_terms": [],
            "answer_text": _strip_citation_markers(ask_result.answer),
        }

    cited_candidates = [
        ask_result.retrieved_candidates[citation_number - 1]
        for citation_number in citation_numbers
    ]
    answer_text = _strip_citation_markers(ask_result.answer)
    evidence_text = "\n".join(candidate.text for candidate in cited_candidates)
    unsupported_terms = _find_unsupported_answer_terms(
        answer_text=answer_text,
        evidence_text=evidence_text,
    )
    if unsupported_terms:
        return {
            "bucket": "unsupported_claim",
            "consistent": False,
            "reason": "answer_contains_terms_not_found_in_cited_evidence",
            "citation_numbers": citation_numbers,
            "cited_candidate_count": len(cited_candidates),
            "unsupported_terms": unsupported_terms,
            "answer_text": answer_text,
        }

    return {
        "bucket": "grounded",
        "consistent": True,
        "reason": "all_answer_terms_supported_by_cited_evidence",
        "citation_numbers": citation_numbers,
        "cited_candidate_count": len(cited_candidates),
        "unsupported_terms": [],
        "answer_text": answer_text,
    }


def build_ask_groundedness_snapshot(
    ask_result: AskWorkflowResult,
) -> dict[str, Any]:
    return build_ask_faithfulness_snapshot(ask_result)


def split_atomic_claims(text: str) -> list[str]:
    normalized_text = _strip_citation_markers(text)
    normalized_fragments: list[str] = []
    for raw_fragment in CLAIM_SPLIT_PATTERN.split(normalized_text):
        fragment = _normalize_claim_fragment(raw_fragment)
        if len(fragment) < 2:
            continue
        normalized_fragments.append(fragment)

    claims: list[str] = []
    for index, fragment in enumerate(normalized_fragments):
        if _should_skip_claim_fragment(
            fragment,
            has_following_fragment=index < len(normalized_fragments) - 1,
        ):
            continue
        if fragment not in claims:
            claims.append(fragment)
    return claims


def build_claim_faithfulness_report(
    text: str,
    evidence_texts: Sequence[str],
    *,
    settings: Settings | None = None,
    provider_preference: str | None = None,
) -> dict[str, Any]:
    claims = split_atomic_claims(text)
    evidence_fragments = _collect_evidence_fragments(evidence_texts)
    if not claims:
        return {
            "backend": "not_applicable",
            "score": None,
            "reason": "semantic_claim_report:not_applicable:no_claims",
            "claim_count": 0,
            "verdict_breakdown": {},
            "claims": [],
        }
    if not evidence_fragments:
        return {
            "backend": "lexical_semantic",
            "score": 0.0,
            "reason": "semantic_claim_report:lexical_semantic:no_evidence",
            "claim_count": len(claims),
            "verdict_breakdown": {"neutral": len(claims)},
            "claims": [
                {
                    "claim": claim,
                    "verdict": "neutral",
                    "reason": "no_evidence_fragments_available",
                    "best_evidence": None,
                    "lexical_overlap": 0.0,
                    "similarity": None,
                }
                for claim in claims
            ],
        }

    similarity_rows, backend_name = _compute_similarity_rows(
        claims=claims,
        evidence_fragments=evidence_fragments,
        settings=settings,
        provider_preference=provider_preference,
    )

    verdicts: list[_ClaimVerdict] = []
    for claim_index, claim in enumerate(claims):
        verdicts.append(
            _classify_claim(
                claim=claim,
                evidence_fragments=evidence_fragments,
                similarity_row=similarity_rows[claim_index] if similarity_rows is not None else None,
            )
        )

    entailed_count = sum(1 for verdict in verdicts if verdict.verdict == "entailed")
    contradicted_count = sum(
        1 for verdict in verdicts if verdict.verdict == "contradicted"
    )
    neutral_count = sum(1 for verdict in verdicts if verdict.verdict == "neutral")
    score = round(entailed_count / len(verdicts), 4) if verdicts else None
    if contradicted_count:
        reason_suffix = "contradicted"
    elif neutral_count:
        reason_suffix = "partial_or_neutral"
    else:
        reason_suffix = "all_entailed"

    return {
        "backend": backend_name,
        "score": score,
        "reason": f"semantic_claim_report:{backend_name}:{reason_suffix}",
        "claim_count": len(verdicts),
        "verdict_breakdown": {
            "entailed": entailed_count,
            "contradicted": contradicted_count,
            "neutral": neutral_count,
        },
        "claims": [
            {
                "claim": verdict.claim,
                "verdict": verdict.verdict,
                "reason": verdict.reason,
                "best_evidence": verdict.best_evidence,
                "lexical_overlap": verdict.lexical_overlap,
                "similarity": verdict.similarity,
            }
            for verdict in verdicts
        ],
    }


def build_runtime_faithfulness_signal(
    text: str,
    *,
    evidence_texts: Sequence[str],
    failure_outcome: RuntimeFaithfulnessOutcome,
    settings: Settings | None = None,
    provider_preference: str | None = None,
) -> RuntimeFaithfulnessSignal:
    report = build_claim_faithfulness_report(
        text,
        evidence_texts,
        settings=settings,
        provider_preference=provider_preference,
    )
    outcome = RuntimeFaithfulnessOutcome.ALLOW
    score = report.get("score")
    if score is not None and score < RUNTIME_FAITHFULNESS_SCORE_THRESHOLD:
        outcome = failure_outcome

    return _build_runtime_signal_from_report(report, outcome=outcome)


def build_runtime_ask_faithfulness_signal(
    ask_result: AskWorkflowResult,
    *,
    settings: Settings | None = None,
    provider_preference: str | None = None,
) -> RuntimeFaithfulnessSignal:
    if ask_result.mode != AskResultMode.GENERATED_ANSWER:
        return RuntimeFaithfulnessSignal(
            outcome=RuntimeFaithfulnessOutcome.ALLOW,
            threshold=RUNTIME_FAITHFULNESS_SCORE_THRESHOLD,
            backend="not_applicable",
            reason="runtime_semantic_gate:not_generated_answer",
        )

    # Citation alignment is enforced elsewhere. The runtime semantic gate should judge
    # support against the full prompt-visible evidence set; otherwise a model that
    # reuses `[1]` across sibling chunks from the same note gets downgraded even when
    # the answer is grounded in the provided context.
    evidence_texts = [
        candidate.text.strip()
        for candidate in ask_result.retrieved_candidates
        if candidate.text.strip()
    ]

    report = build_claim_faithfulness_report(
        _strip_citation_markers(ask_result.answer),
        evidence_texts=evidence_texts,
        settings=settings,
        provider_preference=provider_preference,
    )
    verdict_breakdown = report.get("verdict_breakdown", {})
    contradicted_count = int(verdict_breakdown.get("contradicted", 0) or 0)
    score = report.get("score")

    if contradicted_count:
        outcome = RuntimeFaithfulnessOutcome.DOWNGRADE_TO_RETRIEVAL_ONLY
    elif score is not None and score < RUNTIME_FAITHFULNESS_SCORE_THRESHOLD:
        outcome = RuntimeFaithfulnessOutcome.LOW_CONFIDENCE
    else:
        outcome = RuntimeFaithfulnessOutcome.ALLOW

    return _build_runtime_signal_from_report(report, outcome=outcome)


def _find_unsupported_answer_terms(
    *,
    answer_text: str,
    evidence_text: str,
) -> list[str]:
    answer_terms = _extract_semantic_terms(answer_text)
    evidence_terms = set(_extract_semantic_terms(evidence_text))

    unsupported_terms: list[str] = []
    for term in answer_terms:
        if term in evidence_terms or term in unsupported_terms:
            continue
        unsupported_terms.append(term)
    return unsupported_terms[:8]


def _extract_semantic_terms(text: str) -> list[str]:
    normalized_text = text.casefold()
    terms: list[str] = []

    for token in LATIN_TOKEN_PATTERN.findall(normalized_text):
        if token not in terms:
            terms.append(token)

    for sequence in CJK_SEQUENCE_PATTERN.findall(text):
        if len(sequence) <= 4:
            if sequence not in terms:
                terms.append(sequence)
            continue

        for window_size in (2, 3, 4):
            if len(sequence) < window_size:
                continue
            for index in range(0, len(sequence) - window_size + 1):
                token = sequence[index : index + window_size]
                if token not in terms:
                    terms.append(token)

    return terms


def _strip_citation_markers(text: str) -> str:
    return CITATION_PATTERN.sub("", text).strip()


def _build_runtime_signal_from_report(
    report: dict[str, Any],
    *,
    outcome: RuntimeFaithfulnessOutcome,
) -> RuntimeFaithfulnessSignal:
    verdict_breakdown = report.get("verdict_breakdown", {})
    contradicted_count = int(verdict_breakdown.get("contradicted", 0) or 0)
    neutral_count = int(verdict_breakdown.get("neutral", 0) or 0)
    score = report.get("score")
    return RuntimeFaithfulnessSignal(
        outcome=outcome,
        score=float(score) if score is not None else None,
        threshold=RUNTIME_FAITHFULNESS_SCORE_THRESHOLD,
        backend=str(report.get("backend", "not_applicable") or "not_applicable"),
        reason=str(report.get("reason", "")),
        claim_count=int(report.get("claim_count", 0) or 0),
        unsupported_claim_count=contradicted_count + neutral_count,
    )


def _normalize_claim_fragment(text: str) -> str:
    normalized = INLINE_MARKUP_PATTERN.sub("", text)
    normalized = LEADING_BULLET_PATTERN.sub("", normalized).strip()
    normalized = CLAIM_PREAMBLE_PATTERN.sub("", normalized).strip()
    return normalized


def _should_skip_claim_fragment(
    fragment: str,
    *,
    has_following_fragment: bool,
) -> bool:
    if has_following_fragment and fragment.endswith(("：", ":")):
        return True
    return False


def _extract_semantic_phrases(text: str) -> list[str]:
    phrases: list[str] = []

    for raw_piece in CLAIM_SPLIT_PATTERN.split(_strip_citation_markers(text)):
        piece = _normalize_claim_fragment(raw_piece)
        if not piece:
            continue

        split_chunks: list[str] = []
        for chunk in PHRASE_SPLIT_PATTERN.split(piece):
            if not chunk:
                continue
            split_chunks.extend(
                candidate for candidate in PHRASE_CONNECTOR_PATTERN.split(chunk) if candidate
            )

        for raw_phrase in split_chunks:
            phrase = _normalize_semantic_phrase(raw_phrase)
            if not phrase:
                continue
            if _is_contextual_phrase(phrase):
                continue
            if phrase not in phrases:
                phrases.append(phrase)

    return phrases


def _normalize_semantic_phrase(text: str) -> str:
    phrase = INLINE_MARKUP_PATTERN.sub("", text).strip()
    phrase = phrase.replace("以展示", "展示")
    phrase = phrase.strip("，,：:；;。.!?\"'“”‘’ ")
    if PURE_NUMBER_PATTERN.fullmatch(phrase):
        return ""

    changed = True
    while changed:
        changed = False
        for prefix in GENERIC_PHRASE_PREFIXES:
            if phrase.startswith(prefix) and len(phrase) > len(prefix) + 1:
                phrase = phrase[len(prefix) :].strip()
                changed = True
        for suffix in GENERIC_PHRASE_SUFFIXES:
            if phrase.endswith(suffix) and len(phrase) > len(suffix) + 1:
                phrase = phrase[: -len(suffix)].strip()
                changed = True

    if len(phrase) < 2:
        return ""
    return phrase


def _is_contextual_phrase(phrase: str) -> bool:
    if PURE_NUMBER_PATTERN.fullmatch(phrase):
        return True
    return any(marker in phrase for marker in CONTEXTUAL_PHRASE_MARKERS)


def _phrase_support_ratio(claim: str, evidence_fragments: Sequence[str]) -> float:
    claim_phrases = _extract_semantic_phrases(claim)
    if not claim_phrases:
        return 0.0

    normalized_evidence = "\n".join(
        INLINE_MARKUP_PATTERN.sub("", fragment)
        for fragment in evidence_fragments
    )
    supported_count = sum(1 for phrase in claim_phrases if phrase in normalized_evidence)
    return supported_count / len(claim_phrases)


def _dedupe_preserve_order(values: Any) -> list[Any]:
    deduped_values: list[Any] = []
    for value in values:
        if value in deduped_values:
            continue
        deduped_values.append(value)
    return deduped_values


def _collect_evidence_fragments(evidence_texts: Sequence[str]) -> list[str]:
    evidence_fragments: list[str] = []
    for evidence_text in evidence_texts:
        for fragment in split_atomic_claims(evidence_text):
            if fragment not in evidence_fragments:
                evidence_fragments.append(fragment)
        stripped_text = evidence_text.strip()
        if stripped_text and stripped_text not in evidence_fragments:
            evidence_fragments.append(stripped_text)
    return evidence_fragments[:48]


def _compute_similarity_rows(
    *,
    claims: Sequence[str],
    evidence_fragments: Sequence[str],
    settings: Settings | None,
    provider_preference: str | None,
) -> tuple[list[list[float]] | None, str]:
    if settings is None:
        return None, "lexical_semantic"

    texts = [*claims, *evidence_fragments]
    try:
        embedding_result = embed_texts(
            texts,
            settings=settings,
            provider_preference=provider_preference,
        )
    except Exception:
        return None, "lexical_semantic"

    if embedding_result.disabled or not embedding_result.embeddings:
        return None, "lexical_semantic"

    claim_vectors = embedding_result.embeddings[: len(claims)]
    evidence_vectors = embedding_result.embeddings[len(claims) :]
    if len(claim_vectors) != len(claims) or len(evidence_vectors) != len(evidence_fragments):
        return None, "lexical_semantic"

    similarity_rows: list[list[float]] = []
    for claim_vector in claim_vectors:
        similarity_rows.append(
            [
                round(_cosine_similarity(claim_vector, evidence_vector), 4)
                for evidence_vector in evidence_vectors
            ]
        )
    return similarity_rows, "embedding_semantic"


def _classify_claim(
    *,
    claim: str,
    evidence_fragments: Sequence[str],
    similarity_row: Sequence[float] | None,
) -> _ClaimVerdict:
    claim_terms = set(_extract_semantic_terms(claim))
    claim_has_negation = _contains_negation(claim)
    phrase_support = _phrase_support_ratio(claim, evidence_fragments)
    best_fragment: str | None = None
    best_overlap = 0.0
    best_similarity: float | None = None
    best_contradiction = False

    for index, evidence_fragment in enumerate(evidence_fragments):
        overlap = _lexical_overlap_ratio(claim_terms, evidence_fragment)
        similarity = (
            float(similarity_row[index]) if similarity_row is not None and index < len(similarity_row) else None
        )
        contradiction = (
            overlap >= LEXICAL_CONTRADICTION_THRESHOLD
            and claim_has_negation != _contains_negation(evidence_fragment)
        )
        if best_fragment is None:
            best_fragment = evidence_fragment
            best_overlap = overlap
            best_similarity = similarity
            best_contradiction = contradiction
            continue
        candidate_key = (
            similarity if similarity is not None else -1.0,
            overlap,
        )
        best_key = (
            best_similarity if best_similarity is not None else -1.0,
            best_overlap,
        )
        if candidate_key > best_key:
            best_fragment = evidence_fragment
            best_overlap = overlap
            best_similarity = similarity
            best_contradiction = contradiction

    if best_fragment is None:
        return _ClaimVerdict(
            claim=claim,
            verdict="neutral",
            reason="no_matching_evidence_fragment",
            best_evidence=None,
            lexical_overlap=0.0,
            similarity=None,
        )

    if phrase_support >= PHRASE_SUPPORT_THRESHOLD:
        return _ClaimVerdict(
            claim=claim,
            verdict="entailed",
            reason="high_phrase_support",
            best_evidence=best_fragment,
            lexical_overlap=round(best_overlap, 4),
            similarity=best_similarity,
        )

    if best_contradiction:
        return _ClaimVerdict(
            claim=claim,
            verdict="contradicted",
            reason="negation_conflict_with_overlapping_evidence",
            best_evidence=best_fragment,
            lexical_overlap=round(best_overlap, 4),
            similarity=best_similarity,
        )

    if best_overlap >= LEXICAL_ENTAILMENT_THRESHOLD:
        return _ClaimVerdict(
            claim=claim,
            verdict="entailed",
            reason="high_lexical_support",
            best_evidence=best_fragment,
            lexical_overlap=round(best_overlap, 4),
            similarity=best_similarity,
        )

    if best_similarity is not None and best_similarity >= EMBEDDING_ENTAILMENT_THRESHOLD:
        return _ClaimVerdict(
            claim=claim,
            verdict="entailed",
            reason="high_embedding_similarity",
            best_evidence=best_fragment,
            lexical_overlap=round(best_overlap, 4),
            similarity=best_similarity,
        )

    if best_similarity is not None and best_similarity >= EMBEDDING_SUPPORT_THRESHOLD and best_overlap >= 0.25:
        return _ClaimVerdict(
            claim=claim,
            verdict="entailed",
            reason="embedding_supported_with_partial_overlap",
            best_evidence=best_fragment,
            lexical_overlap=round(best_overlap, 4),
            similarity=best_similarity,
        )

    return _ClaimVerdict(
        claim=claim,
        verdict="neutral",
        reason="insufficient_semantic_support",
        best_evidence=best_fragment,
        lexical_overlap=round(best_overlap, 4),
        similarity=best_similarity,
    )


def _contains_negation(text: str) -> bool:
    normalized = text.casefold()
    return any(token in normalized for token in NEGATION_TOKENS)


def _lexical_overlap_ratio(claim_terms: set[str], evidence_fragment: str) -> float:
    if not claim_terms:
        return 0.0
    evidence_terms = set(_extract_semantic_terms(evidence_fragment))
    if not evidence_terms:
        return 0.0
    overlap_count = len(claim_terms & evidence_terms)
    return overlap_count / len(claim_terms)


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    left_norm = sum(value * value for value in left) ** 0.5
    right_norm = sum(value * value for value in right) ** 0.5
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right, strict=True))
    return dot_product / (left_norm * right_norm)
