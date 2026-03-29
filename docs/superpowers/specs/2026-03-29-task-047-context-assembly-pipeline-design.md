# TASK-047 Context Assembly Pipeline Design

## 1. Session Binding

- `task_id`: `TASK-047`
- `session_id`: `SES-20260329-02`
- `status`: `drafted`
- `owner`: `Codex`

## 2. Goal

将 ask 链路中的上下文装配层从当前的“去重 + 预算截断”最小实现，升级为一个可解释、可测试、可追踪的四阶段质量控制管线：

1. 相关性过滤
2. 来源多样性控制
3. 结构化上下文增强
4. 相关性加权预算分配

目标是让 `backend/app/context/assembly.py` 真正成为检索与回答之间的独立控制层，而不是对检索候选做一次无语义的轻量拼接。

## 3. Why Now

当前代码已经具备 hybrid retrieval、citation 对齐和最小 ask graph，但装配层仍只有以下能力：

- 按 `chunk_id` 去重
- 按字符预算丢弃尾部 chunk
- 过滤明显可疑文本

这和 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中 `TASK-047` 的验收目标存在明显缺口，也让“独立上下文装配层”在面试追问下缺少技术深度。

## 4. Scope

### In Scope

- 扩展 `ContextBundle` 与相关 contract，使 ask 可返回更结构化的装配结果。
- 在 ask 装配路径中实现四阶段装配管线。
- 让 prompt 渲染能够消费更丰富的 evidence 定位信息。
- 为装配元数据补最小测试覆盖，确保 ask 现有主链路不回退。

### Out of Scope

- 不修改 hybrid retrieval 的 RRF 融合逻辑。
- 不引入 cross-encoder、reranker 或模型摘要。
- 不改变 `AskWorkflowResult` 外层 API contract。
- 不实现 `TASK-046` 的 ReAct 多轮工具调用。
- 不处理中途文档同步；治理文档更新留到会话收尾统一判断级别。

## 5. Current State

### 5.1 Existing Ask Assembly

[backend/app/context/assembly.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/context/assembly.py) 当前流程：

1. `chunk_id` 去重
2. 按 `token_budget` 近似字符预算顺序截断
3. 过滤命中 `detect_safety_flags()` 的文本
4. 生成 `ContextEvidenceItem`

这条路径不会：

- 按分数过滤低价值噪声
- 控制单篇笔记的贡献上限
- 暴露来源笔记级摘要与装配统计
- 为低分 chunk 做更小的预算分配

### 5.2 Existing Prompt Consumption

[backend/app/context/render.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/context/render.py) 当前只消费：

- `source_path`
- `heading_path`
- `text`

缺少：

- `source_note_title`
- `position_hint`
- `source_notes`
- `assembly_metadata`

## 6. Chosen Approach

采用“装配层内聚，检索层不动”的方案。

### 6.1 Rationale

- `TASK-047` 明确要求改造的是 assembly，而不是 retrieval。
- 如果把过滤、多样性和预算分配前推到 [backend/app/retrieval/hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/hybrid.py)，会把召回职责与提示词消费职责耦合。
- 现有 ask service 已经把 `ContextBundle` 作为 prompt 渲染和 citation 选择的中间层，继续在这里增强是最小且最一致的路径。

## 7. Design

### 7.1 Contract Changes

在 [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py) 中扩展以下结构：

- `ContextEvidenceItem`
  - 新增 `source_note_title: str | None`
  - 新增 `position_hint: str | None`
  - 保留现有 `heading_path / score / source_kind`
- `ContextBundle`
  - 新增 `source_notes: list[ContextSourceNote]`
  - 新增 `assembly_metadata: ContextAssemblyMetadata`
- 新增 `ContextSourceNote`
  - `source_path`
  - `title`
  - `chunk_count`
  - `max_score`
- 新增 `ContextAssemblyMetadata`
  - `initial_candidate_count`
  - `relevance_filtered_count`
  - `diversity_filtered_count`
  - `budget_filtered_count`
  - `suspicious_filtered_count`
  - `final_evidence_count`
  - `relevance_threshold`
  - `per_source_limit`
  - `full_text_char_budget`
  - `summary_char_budget`

这些结构只服务 ask 装配；ingest / digest 可先填默认值，避免外层 contract 被 ask 特例破坏。

### 7.2 Four Pipeline Stages

#### Stage 1: Relevance Filter

输入：hybrid retrieval candidates

规则：

- 以 top-1 score 为锚点，计算动态阈值 `top_score * ratio`
- score 低于阈值的候选直接丢弃
- 若全部被过滤，保底保留 top-1，避免出现“检索有命中但装配全空”

默认配置：

- `ratio = 0.35`

#### Stage 2: Source Diversity

规则：

- 按 score 从高到低遍历 Stage 1 输出
- 同一路径最多保留 `N` 条 chunk
- 超限部分按低分优先淘汰

默认配置：

- `N = 2`

#### Stage 3: Structured Enrichment

对保留的每条 evidence 生成：

- `source_note_title`: 直接使用 candidate.title
- `heading_path`: 复用现有字段
- `position_hint`: 以“第 X 段 / 共 Y 段（该笔记被保留的 evidence）”形式生成近似定位提示

同时汇总 `source_notes`：

- 按路径去重
- 记录每篇笔记贡献的 evidence 数量与最高分

#### Stage 4: Weighted Budget Allocation

规则：

- 先按 score 降序排序
- 高分 evidence 分配“全文预算”
- 低分 evidence 分配“摘要预算”，仅保留前 `summary_char_budget` 字符
- 总字符消耗不得超过 `token_budget`

默认配置：

- `full_text_char_budget = 900`
- `summary_char_budget = 280`
- 高分与低分分界先用排序位置决定：前 2 条优先全文，其余走摘要预算

这里不引入模型摘要，只做保守截取，保持可预测性和零额外推理成本。

### 7.3 Prompt Rendering

在 [backend/app/context/render.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/context/render.py) 中：

- 检索证据块增加 `source_note_title`
- 增加 `position_hint`
- 保持引用编号仍只对应 retrieval evidence
- 不把 `assembly_metadata` 直接暴露给模型，避免提示词冗余

### 7.4 Ask Service Integration

在 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py) 中：

- 继续通过 `build_ask_context_bundle()` 统一拿装配结果
- `retrieved_candidates` 和 `citations` 仍从最终可见 retrieval evidence 反推
- 不新增新的结果字段，避免扩大外层 contract 变更范围

## 8. Testing Strategy

遵循 TDD，只在看到失败测试后写生产代码。

优先新增以下回归：

1. relevance filter 会淘汰明显低分尾部噪声
2. diversity control 会限制单篇笔记最多贡献 2 条 evidence
3. 预算分配会让高分项保留更完整文本，低分项被摘要截断
4. prompt 渲染能包含 `source_note_title` 与 `position_hint`
5. ask 现有 hybrid retrieval 主路径仍保持 retrieval-only fallback 语义

测试主落点：

- [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)

如需要更细粒度单测，可补：

- `backend/tests/test_context_assembly.py`

但只有在 ask 现有测试文件无法清晰表达装配行为时才新增，避免无谓扩散。

## 9. Risks

- 当前 `score` 是 hybrid RRF 分数，不是校准后的绝对相关性分值；阈值只能作为相对过滤，不应伪装成通用相关性判断。
- `position_hint` 是近似提示，不是笔记真实章节序号；其职责是辅助模型定位，不是审计级精确坐标。
- 当前工作区很脏，且已有大量未提交 docs 改动；实施时必须只触碰 `TASK-047` 相关文件，避免把别的历史改动混进来。

## 10. Deferred Follow-ups

以下内容继续后移，不并入本次 `medium`：

- 为 `assembly_metadata` 增加 runtime trace 挂载
- 为被 diversity 淘汰的 chunk 建“备选池”
- 为阈值比例增加离线 eval 对比实验
- 将装配阶段参数抽到统一配置层

## 11. Acceptance Mapping

| `TASK-047` 验收项 | 设计映射 |
| --- | --- |
| 相关性过滤 | Stage 1 relevance filter + `relevance_filtered_count` |
| 来源多样性 | Stage 2 per-source cap + `diversity_filtered_count` |
| 结构化增强 | `source_note_title` + `heading_path` + `position_hint` |
| 预算分配 | Stage 4 full-text vs summary budgeting |
| `ContextBundle` 扩展 | `source_notes` + `assembly_metadata` |
| ask 回归不退化 | ask workflow tests + hybrid case 回归 |

## 12. Open Tail Sync Item

[docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 当前仍残留多处旧 `Next Action = TASK-031 / TASK-032 / TASK-033` 口径，与 [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md) 已切到 `TASK-047` 的动态控制面不一致。本次实现阶段不静默改文档，留待会话收尾按影响级别统一处理。
