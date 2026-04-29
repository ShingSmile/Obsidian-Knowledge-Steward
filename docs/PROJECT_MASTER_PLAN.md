# Obsidian Knowledge Steward 项目主文档

## 0. 文档头信息

| 字段 | 内容 |
| --- | --- |
| 项目名称 | Obsidian Knowledge Steward |
| 副标题 | 基于 LangGraph 的个人学习知识治理与复盘 Agent |
| 当前版本号 | v0.2.60 |
| 最近更新时间 | 2026-04-10 CST |
| 当前开发阶段 | 当前执行状态请见 [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md)；本文件不再维护动态阶段描述。 |
| 当前负责人 | qingfeng Qi |
| 文档定位 | 这是项目的稳定架构主文档，主要承载模块边界、阶段路线、ADR、风险与长期叙事。当前任务事实以 `docs/TASK_QUEUE.md` 为准，最近执行状态以 `docs/CURRENT_STATE.md`、`docs/SESSION_LOG.md` 为准，面试问答库与版本变更已分别拆到 `docs/INTERVIEW_PLAYBOOK.md`、`docs/CHANGELOG.md`。 |

### 0.0.1 执行基准原则

- 项目的 interview-first north star 仍然来自 [Obsidian Knowledge Steward 项目初步实现指南.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/Obsidian%20Knowledge%20Steward%20项目初步实现指南.md)。
- 任务绑定、范围边界与验收标准统一以 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 为准。
- 动态状态、最近完成、默认下一任务与当前风险统一以 [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md) 和 [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md) 为准。
- 本文件只维护稳定架构、模块边界、路线原则、ADR 与长期风险，不再滚动承载高波动的 next-action 或逐次勘误清单。

### 0.1 变更记录

完整版本流水已迁移到 [docs/CHANGELOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CHANGELOG.md)。

当前版本 `v0.2.60` 已同步到 `TASK-049` 的完成态：ask 继续保持 Faithfulness / Answer Relevancy / Context Precision / Context Recall 四维度离线面板，governance 已新增 `Rationale Faithfulness / Patch Safety`，digest 已新增 `Faithfulness / Coverage`，`TASK-048` umbrella 也已随 `TASK-054` 一并收口；与此同时 backend / plugin / persistence / retrieval 继续维持 `TASK-055` 收敛后的 `vault-relative` note path contract，ask 的工具调用主路径也已从 prompt-based JSON 协议升级为 API 级 Structured Tool Calling，并对不支持该协议的 provider 保留 fallback。默认下一 medium 现回到已后移的 `TASK-031`，随后进入 `TASK-032`。

### 0.2 当前事实边界

- 项目的起点确实是“只有实现指南的空仓”，但当前已经进入“基线骨架已落地”的阶段：仓库内已有 `backend/`、`plugin/`、`eval/`、`README.md` 与 `sample_vault/`；早期 vendored 的 `ObsidianRAG` 参考镜像已从当前仓库移除。
- 当前事实不再是“尚未开始工程落地”，而是“已完成第一轮基线搭建与样本验证，并接通了 `DAILY_DIGEST -> approval -> local writeback -> audit/checkpoint` 的最小闭环，但多数业务路径仍未完整接通”。
- 本文档中的“已实现/半实现/未实现”判断继续严格基于仓库文件和已验证命令结果，不基于设想。
- 本文档中的建议目录结构、模块路径、类名、数据表和工作流，凡未明确标注“当前已存在”者，仍然视为设计方案或建议落位。
- 2026-03-29 当前 ask 已新增 `get_note_outline`、fail-closed `find_backlinks` 与 verified-only tool reentry；插件写回已支持 `replace_section / add_wikilink`，且 [backend/app/services/proposal_validation.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/proposal_validation.py) 已把这两个新 op 纳入正式支持的持久化校验能力，并补齐 payload-specific validation，因此 `TASK-045` 已完成。
- 2026-03-29 当前 ask 的 `context/assembly.py` 已升级为四阶段质量控制管线：相关性过滤、来源多样性控制、结构化增强与加权预算分配均已落地，`ContextBundle` 现已输出 `source_notes / assembly_metadata`，而 [backend/app/context/render.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/context/render.py) 与 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py) 已确保 prompt / citation 只消费 post-assembly 可见 evidence，因此 `TASK-047` 已完成。
- 2026-04-01 当前 ask 的执行模型已从线性三节点图升级为 graph-only ReAct： [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py) 现使用 `prepare_ask -> llm_call -> tool_node -> finalize_ask` 的 conditional-edge 循环，[backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py) 不再保留 `run_minimal_ask` 这条完整 ask 主入口，而是拆为初始装配、工具判定、工具执行与最终回答 helper，[backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py) 也已新增 `tool_call_rounds`，因此 `TASK-046` 已完成。
- 2026-04-06 当前 ask 的工具调用主路径已从 prompt-based JSON 约定升级为 Structured Tool Calling： [backend/app/tools/registry.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/tools/registry.py) 已可把现有 `ToolSpec.name / purpose / input_schema` 直接映射为 OpenAI-compatible `tools` payload，[backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py) 现已优先消费结构化 `message.tool_calls`，并在 provider 不支持或 structured payload 不可用时回落到 legacy prompt-based path；图级 ReAct、guardrail 与 `tool_node` 执行路径保持不变，因此 `TASK-049` 已完成。
- 2026-04-02 当前 [backend/app/quality/faithfulness.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/quality/faithfulness.py) 已从 ask 专属启发式 helper 升级为共享 claim-level semantic faithfulness core：它可以把中文回答 / rationale / digest / proposal summary 拆成原子 claim，对 `(claim, evidence)` 输出 `entailed / contradicted / neutral` verdict，并在 embedding provider 可用时走更强的 semantic backend；[eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py) 也已让 ask / governance / digest 共用这套判定层，因此 `TASK-051` 已完成。
- 2026-04-02 当前 ask / digest runtime 已真正消费这套共享语义底座： [backend/app/quality/faithfulness.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/quality/faithfulness.py) 新增 `RuntimeFaithfulnessSignal`， [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py) 与 [backend/app/services/digest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/digest.py) 已把 `score / threshold / outcome / backend / reason` 接进 ask / digest runtime；[backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py) 也已让 ask / digest 结果输出结构化 runtime faithfulness metadata，因此 `TASK-052` 已完成。
- 2026-04-06 当前 ask 离线评估已真正补齐为四维度回归基线： [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py) 现已把 ask 质量面板正式收敛为 Faithfulness / Answer Relevancy / Context Precision / Context Recall，并以 `answer_relevancy` 作为正式 key、`relevancy` 作为兼容 alias； [eval/golden/ask_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/ask_cases.json) 也已扩充到覆盖 grounded / unsupported / partial support 的 ask quality case，因此 `TASK-053` 已完成。
- 2026-04-06 当前 note path contract 已在 backend / plugin / persistence / retrieval 收敛为 `vault-relative`： [backend/app/path_semantics.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/path_semantics.py) 与 [plugin/src/writeback/pathSemantics.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/pathSemantics.ts) 已把 vault 内真实绝对路径归一化为 canonical relative path，并把 `/vault/...` 明确降级为仅供历史迁移使用的 legacy 格式；proposal / writeback / evidence / retrieval 的正式 contract 已不再接受它作为普通执行路径输入，因此 `TASK-055` 已完成。
- 当前 Python 开发环境路线已在代码与 README 中收敛为工作区本地 conda prefix `./.conda/knowledge-steward`，并新增 `backend/environment.yml` 与 `python -m app.main` 统一入口；`backend/.venv` 仍可能作为历史残留存在，但不再作为推荐或验收标准。2026-03-12 已在提权环境中完成 `python -m app.main` 启动与 `/health` 命中验证，因此该路线记为“已收敛、已验收”。
- 当前已新增 `backend/app/indexing/store.py`、`backend/app/indexing/ingest.py`、`backend/app/retrieval/sqlite_fts.py`、`backend/app/retrieval/embeddings.py`、`backend/app/retrieval/sqlite_vector.py`、`backend/app/retrieval/hybrid.py`、`backend/app/services/ask.py`、`backend/app/services/digest.py`、`backend/app/services/ingest_proposal.py`、`backend/app/services/resume_workflow.py`、`backend/app/services/rollback_workflow.py`、`backend/app/graphs/runtime.py`、`backend/app/graphs/checkpoint.py`、`backend/app/graphs/ask_graph.py`、`backend/app/graphs/ingest_graph.py`、`backend/app/graphs/digest_graph.py`、`backend/app/observability/runtime_trace.py` 与 retrieval / ask / ingest / digest / graph / observability contract；可通过 `python -m app.indexing.store` 初始化 SQLite schema，通过 `python -m app.indexing.ingest` 执行全量或 scoped ingest，并使用 FTS / vector / hybrid retrieval、ask / ingest / digest graph、waiting proposal、`/workflows/resume` / `/workflows/rollback` / `pending-approvals`、插件 pending inbox / backend runtime / 受限写回，以及 `eval/run_eval.py` 的 23 条样本回归组成当前最小可演示骨架。
- `SES-20260401-02` 先补上了 ask runtime 的共享 faithfulness snapshot；`SES-20260401-03` 又将其升级为共享 claim-level semantic faithfulness core：ask / governance / digest 的离线评估现已共用 claim 拆解、`entailed / contradicted / neutral` verdict 与 embedding 可用时的 semantic backend，governance / digest 的 faithfulness 不再直接退回 `context_recall` 充当替代指标。
- 当前恢复已不再只停留在 completed checkpoint 短路返回，`DAILY_DIGEST` 与 `INGEST_STEWARD` 已各有一条真实 waiting proposal 路径，且插件待审批收件箱已可加载真实 pending item；ask 仍未 proposal 化，`INGEST_STEWARD` 的多 note proposal 合并、向量索引 coverage 观测、写回成功但后端记账失败的跨会话恢复、scoped ingest 的增量 FTS 同步，以及 rollback 成功后的 scoped ingest 刷新仍未完成。基于 `TASK-044`、`TASK-045`、`TASK-046`、`TASK-047`、`TASK-049`、`TASK-050`、`TASK-051`、`TASK-052`、`TASK-053`、`TASK-054` 与 `TASK-055` 的完成，`TASK-048` umbrella 已由 `TASK-050` 到 `TASK-054` 全部收口，不再保留未完成的 `medium`；若继续开发，默认回到已后移的 `TASK-031`，然后进入 `TASK-032`；`TASK-033` 已被 `TASK-050` / `TASK-052` 吸收。插件产品形态、后端最小启动控制、受限写回安全链路、post-writeback 索引一致性、最小 rollback、最小向量底座、hybrid retrieval、graph-only ReAct、Structured Tool Calling，以及当前 ask / governance / digest 的基础 tracing、ask 四维度离线评估与分场景 benchmark 已视为 interview-first 下限达成；pending inbox freshness、CLI scoped parity、新笔记治理 proposal 的风险分级 / patch 模板收敛、rollback diff 预览，以及 faithfulness 停用词 / allowlist 收敛继续后移。digest 主体当前仍是模板化摘要，不包含调度、写回草稿或 LLM 聚类。

### 0.3 当前输入来源

| 来源 | 路径 | 用途 | 可信度 |
| --- | --- | --- | --- |
| 仓库事实 | `./` 目录扫描结果 | 判断当前是否存在代码、配置、测试、文档目录 | 高 |
| 初步实现指南 | `./Obsidian Knowledge Steward 项目初步实现指南.md` | 提取项目目标、推荐技术路线、两周内实现建议 | 中高 |
| 示例 Vault | `./sample_vault/` | 验证真实语料结构、任务密度、链接分布、模板类型与复盘场景 | 高 |
| 用户目标说明 | 当前会话要求 | 确定主文档必须覆盖的章节、粒度和面试导向 | 高 |

## 1. 项目一句话定义

Obsidian Knowledge Steward 是一个面向个人学习场景的知识治理系统：它围绕新笔记治理、周期复盘、可解释问答、人工审批写回、审计与评估闭环，构建一个有状态、可恢复、可审计的 LangGraph 工作流，而不是一个黑盒聊天助手。

它不等于“把 LLM 接进 Obsidian 做聊天问答”，也不等于“普通 RAG 插件”。它要解决的是个人知识库在持续写入后出现的结构腐化问题，包括重复、冲突、孤立、遗忘、开放问题堆积，以及缺乏安全写回与评估机制的问题。

项目的核心主张是三点：

- 重点是知识治理，不是聊天陪聊。
- 重点是有状态工作流，不是单轮 prompt 拼接。
- 重点是可审计、可中断、可恢复、可评估，不是“模型看起来好像能用”。

## 2. 业务目标与非目标

### 2.1 核心目标

1. 对新写入或新修改的笔记执行治理动作，包括标签补全、双链建议、重复检测、冲突检测、摘要生成、行动项提取。
2. 对近期学习内容执行每日或周期复盘，输出聚类主题、未解决问题、行动项与复习计划草稿。
3. 提供一个基于笔记的问答兜底链路，但结果必须带引用、可解释、可回溯。
4. 对任何会写回 Vault 的操作引入 Human-in-the-loop 审批，避免 LLM 直接破坏用户知识库。
5. 建立 tracing、audit log、checkpoint、eval 回归等工程闭环，使项目具备面试可讲述性与演示稳定性。

### 2.2 非目标

- 不做通用聊天机器人。聊天只是交互壳，不是核心价值。
- 不做大而全的个人 second brain 平台。项目边界聚焦在 Obsidian Vault 内的知识治理。
- 不在两周内追求多端同步、团队协作、云端托管、OCR、复杂图数据库或全自动批量写回。
- 不追求“完全无人值守自动改笔记”。高风险写回必须有人批准。
- 不把面试叙事建立在“模型特别聪明”上，而是建立在“系统结构可控、错误可诊断、质量可评估”上。

### 2.3 为什么这个场景贴近日常学习、且高频

- 个人学习最常见的问题不是“我能不能问一句话”，而是“我写过很多东西，但随着时间过去越来越难维护”。
- Obsidian 用户的典型行为是持续写短笔记、碎片记录、课程/论文摘录、日记式反思、任务夹带在笔记里，这天然会产生重复、冲突和链接缺失。
- 学习复盘本身就是高频场景。每日复盘、每周复盘、复习计划，本质上都需要聚合近期内容并抽取开放环。
- 与企业知识库不同，个人 Vault 结构通常更混乱、命名更随意、标签更不规范，因此更需要治理而不是只做检索。

### 2.4 为什么它适合作为面试项目而不是玩具项目

#### 为什么不是普通 RAG

- 普通 RAG 只回答“找得到什么”，但不回答“知识库为什么越来越难维护”。
- 普通 RAG 没有写回、安全审批、审计日志、中断恢复、周期性复盘这些有状态需求。
- 如果只做 RAG，面试官会追问“你为什么一定要用 LangGraph、为什么不是一个检索加生成的 API 服务”。答案会很弱。

#### 为什么不是普通 Obsidian AI 助手

- 普通 AI 助手强调聊天、总结、改写；Knowledge Steward 强调治理流程和系统责任边界。
- 普通 AI 助手的输出通常是文本；Knowledge Steward 的输出包括结构化 proposal、patch、审计记录、评估结果。
- 普通插件通常缺少写回前审批和回放机制，无法证明“不会把用户知识库搞坏”。

#### 为什么 LangGraph 在这里是必要的

- 新笔记治理、周期复盘、审批写回都不是单轮调用，而是多节点、带条件路由、带状态持久化的长流程。
- 需要中断和恢复。审批不是一次函数调用的附属动作，而是工作流中的控制点。
- 需要 checkpoint、thread_id、幂等控制、失败重试、回放和调试；这类需求更适合 graph/state machine，而不是黑盒 agent。

#### 为什么 HITL 是必要的

- 任何修改 Vault 的操作都可能产生不可逆的知识损坏，尤其是 frontmatter 覆盖、链接替换、段落删除。
- LLM 的错误常常不是“语法报错”，而是“看起来合理但改坏事实结构”，这类错误只有 diff 审查才能有效兜底。
- 面试中最容易被拷打的问题之一就是“如果模型改错笔记怎么办”，HITL 是必须准备好的答案。

#### 为什么需要 eval / tracing

- 没有 tracing，就无法定位延迟到底卡在检索、rerank、模型还是写回。
- 没有 eval，就无法回答“为什么你说这个系统有效”，也无法做回归。
- 面试官会问“你怎么知道 reranker 值得开、你怎么知道复盘质量稳定、你怎么知道 hybrid retrieval 比单一路径好”，这些都需要数据支持。

## 3. 当前项目现状盘点（基于代码）

### 3.1 当前目录结构概览

本轮分析开始时，仓库实际目录结构如下：

```text
.
├── .git/
└── Obsidian Knowledge Steward 项目初步实现指南.md
```

创建本文档后的当前目录结构如下：

```text
.
├── .git/
├── Obsidian Knowledge Steward 项目初步实现指南.md
└── docs/
    └── PROJECT_MASTER_PLAN.md
```

当前新增样本后的目录结构如下：

```text
.
├── .git/
├── Obsidian Knowledge Steward 项目初步实现指南.md
├── README.md
├── backend/
├── plugin/
├── eval/
├── data/
├── docs/
│   └── PROJECT_MASTER_PLAN.md
└── sample_vault/
    └── 日常/
```

分析时更细一级的文件事实如下：

```text
./.git/HEAD
./.git/config
./.git/description
./Obsidian Knowledge Steward 项目初步实现指南.md
```

结论：

- 现在已经有真实业务代码骨架：`backend/`、`plugin/`、`eval/`、`README.md`。
- 后端已具备 `pyproject.toml`、FastAPI 入口、协议模型、样本统计服务。
- 插件已具备 `package.json`、`manifest.json`、最小 view、设置页与后端 API 客户端。
- 早期曾 vendored `ObsidianRAG` 作为只读参考镜像；当前仓库已移除该目录，保留的是已经沉淀进主文档与实现决策的对照结论。
- 已有一个真实示例语料库 `sample_vault/`，包含 205 篇 Markdown 笔记，可直接作为首版索引、复盘、问答和评估样本来源。

### 3.2 已实现模块

| 模块 | 文件路径 | 模块职责 | 当前完成度 | 是否可直接复用 | 是否需要重构 |
| --- | --- | --- | --- | --- | --- |
| 项目初步实现指南 | `Obsidian Knowledge Steward 项目初步实现指南.md` | 提供项目目标、推荐技术路线、两周实现建议、伪代码示例 | 设计稿级别，约 70% 的方案输入 | 可复用为设计输入，不可直接运行 | 需要拆成工程主文档、实施任务和后续 ADR |
| 项目主文档 | `docs/PROJECT_MASTER_PLAN.md` | 单一事实来源，固化架构、路线图、风险与维护规则 | 工程文档级别，持续维护中 | 是 | 需随代码持续更新 |
| 后端基线 | `backend/app/main.py`、`backend/app/contracts/workflow.py`、`backend/app/graphs/state.py`、`backend/app/graphs/runtime.py`、`backend/app/graphs/checkpoint.py`、`backend/app/graphs/ask_graph.py`、`backend/app/graphs/ingest_graph.py`、`backend/app/graphs/digest_graph.py`、`backend/app/observability/runtime_trace.py`、`backend/app/services/sample_vault.py`、`backend/app/services/ask.py`、`backend/app/services/digest.py`、`backend/app/services/ingest_proposal.py`、`backend/app/services/resume_workflow.py` | 暴露 `/health`、`/workflows/invoke`、`/workflows/resume`、状态 schema、协议模型、样本统计、最小 ask / ingest / digest 服务与审批恢复控制面，以及 JSONL + SQLite `run_trace` + LangGraph `SqliteSaver(checkpoints/writes)` + SQLite `workflow_checkpoint` 业务元数据层的最小观测与恢复骨架 | 基线 + 最小 ask / ingest / digest graph / trace / checkpoint / approval resume，并已打通 `DAILY_DIGEST` 与 `INGEST_STEWARD` 的真实 proposal / waiting 路径，约 88% | 是 | 后续需扩展到 ask proposal、provider 健壮性、ingest richer evidence 与更强的 digest / writeback 质量控制 |
| 索引预处理基线 | `backend/app/indexing/parser.py`、`backend/app/indexing/models.py` | 解析 Markdown、提取标题路径、wikilink、任务数并推断 `daily_note / summary_note` | 首版可运行级别，约 20% | 是 | 后续需补 frontmatter、block ref、表格与代码块增强 |
| 插件基线 | `plugin/src/main.ts`、`plugin/src/views/KnowledgeStewardView.ts`、`plugin/src/api/client.ts`、`plugin/src/settings.ts`、`plugin/src/backend/runtime.ts`、`plugin/src/writeback/` | 最小插件入口、设置、面板、后端探活 / 启动控制、审批面板与受限写回执行 | 基线 + 审批 UI + 本地受限写回 + pending inbox + backend runtime 控制级别，并已可加载 / 刷新真实 waiting proposal、执行受限 patch、回传 `writeback_result`，支持用户提供启动命令后的最小本地自启、状态展示与失败降级，约 70% | 是 | 后续需接入更多 workflow 调用、freshness 治理、跨会话恢复、Stop/Restart 与宿主级验证 |
| Eval 目录基线 | `eval/README.md`、`eval/golden/`、`eval/results/`、`eval/run_eval.py` | 固化评估目录、golden case、离线回归执行器、分场景 benchmark 与最小指标输出 | golden benchmark 级别，约 68% | 是 | 后续需补 markdown 报告导出、更强 judge 与宿主级 benchmark 消费视图 |

事实说明：

- 当前仓库已经不再是纯文档空仓，已存在可启动的双端骨架。
- 但“已实现”仍主要集中在基线与最小演示层：索引、ask API、`DAILY_DIGEST -> proposal -> local writeback` 最小闭环与首版离线 eval 已接通，更完整的多 workflow 治理与 richer 评估闭环仍未接通。

### 3.3 半实现模块

| 模块 | 当前证据 | 状态判断 | 问题 |
| --- | --- | --- | --- |
| LangGraph 工作流设想 | `backend/app/graphs/state.py`、`backend/app/graphs/runtime.py`、`backend/app/graphs/checkpoint.py`、`backend/app/graphs/ask_graph.py`、`backend/app/graphs/ingest_graph.py`、`backend/app/graphs/digest_graph.py` 与 `backend/app/services/resume_workflow.py` 已落最小 ask / ingest / digest graph、checkpoint 与审批恢复控制面，`/workflows/invoke` 和 `/workflows/resume` 已能消费最小恢复协议 | 半实现于 ask / ingest / digest graph、checkpoint、审批恢复协议和入口层 | `DAILY_DIGEST` 与 `INGEST_STEWARD` 都已真实产出 waiting checkpoint；但 ask 尚未接入 proposal 节点，ingest 也仍缺多 note / richer proposal 路径，细粒度节点恢复和副作用续跑仍未实现 |
| 插件-后端通信 | `plugin/src/api/client.ts` + `plugin/src/backend/runtime.ts` + `backend/app/main.py` | 半实现，可完成探活、基于 `/health` 的 readiness 判定、本地启动控制、workflow 调用、pending proposal 收件箱查询、真实 `DAILY_DIGEST` proposal 注入、插件本地写回与审批恢复提交 | ask 结果类型已收敛、resume 错误映射与 `writeback_result` 回传已补齐，backend runtime 也已支持最小本地启动与失败降级；但插件侧还没有 ask 命令、引用渲染、freshness 提示、跨会话待同步入口与更强的进程管理 |
| 检索方案 | `backend/app/retrieval/sqlite_fts.py`、`backend/app/retrieval/embeddings.py`、`backend/app/retrieval/sqlite_vector.py`、`backend/app/retrieval/hybrid.py`、`backend/app/contracts/workflow.py`、`backend/app/services/ask.py`、`backend/app/services/ingest_proposal.py` 与 `sample_vault` 分析 | 半实现于 FTS5、metadata filter、`chunk_embedding` 持久化、最小向量检索、RRF hybrid candidate 输出、最小引用式 ask 与编号级 citation 对齐校验 | rerank、共享 semantic faithfulness core 的 runtime gate 接线、向量 coverage / 性能治理与更多 hybrid 调试观测仍未实现 |
| HITL 写回方案 | `backend/app/contracts/workflow.py`、`backend/app/graphs/state.py`、`backend/app/indexing/store.py`、`backend/app/services/resume_workflow.py` 与插件侧 `plugin/src/views/KnowledgeStewardView.ts` / `plugin/src/main.ts` / `plugin/src/writeback/` 已落 proposal / patch / audit contract、审批恢复控制面、面板骨架、pending inbox 与首版受限写回执行器 | 半实现于 contract / state / schema / approval resume / plugin panel / limited writeback executor 层 | `DAILY_DIGEST` 与 `INGEST_STEWARD` 已有真实 proposal 生成节点、waiting proposal 注入、pending inbox 和本地写回路径，但 ask proposal、多 note proposal 合并、写回后增量 ingest 与跨会话恢复仍未实现 |
| 评估方案 | `eval/run_eval.py`、`eval/golden/*.json`、`eval/results/` | 半实现于 23 条 golden set、离线执行器、结果文件产出、governance suite、分场景 benchmark 与最小质量指标层 | 已能回归 ask / governance / digest / proposal / `resume_workflow` 代表场景，并输出最小 `faithfulness / relevancy / context` 指标；其中 faithfulness 已由共享 claim-level semantic report 驱动，ask / governance / digest 共用同一套 claim verdict 层，但尚未覆盖真实 Obsidian 宿主、markdown 报告导出与更强 judge |

### 3.4 尚未实现模块

| 模块 | 当前文件路径 | 目标职责 | 当前完成度 | 是否可直接复用 | 是否需要重构 |
| --- | --- | --- | --- | --- | --- |
| LangGraph 工作流层 | `backend/app/graphs/state.py`、`backend/app/graphs/runtime.py`、`backend/app/graphs/checkpoint.py`、`backend/app/graphs/ask_graph.py`、`backend/app/graphs/ingest_graph.py`、`backend/app/graphs/digest_graph.py`、`backend/app/services/resume_workflow.py` | ingest / digest / ask 三类 graph、状态持久化、中断恢复 | 80% | 是 | ask / ingest / digest graph、最小 checkpoint 与 approval resume 已落地，且 `DAILY_DIGEST` 与 `INGEST_STEWARD` 已接入 waiting proposal；后续需补 ask proposal 节点、ingest richer proposal 路径和细粒度 interrupt |
| Vault 读写层 | `plugin/src/writeback/applyProposalWriteback.ts`、`plugin/src/writeback/helpers.ts` | 读取 note、frontmatter 处理、受限 patch 应用与 `before_hash` 校验 | 52% | 是 | 当前已覆盖 `merge_frontmatter`、`insert_under_heading`、`replace_section` 与 `add_wikilink`，并补了 `add_wikilink` 重复检测；后续需补 `replace_section` 的 `max_changed_lines`、跨会话恢复与宿主级验证 |
| Metadata 解析层 | `backend/app/indexing/parser.py` | frontmatter、headings、links、block refs 解析 | 20% | 是 | 当前只覆盖 headings、links、任务与模板推断 |
| 索引构建层 | `backend/app/indexing/store.py`、`backend/app/indexing/ingest.py` | schema migration、Markdown 全量 ingest、scoped note ingest、note 级 replace/upsert、FTS 重建入口与 `chunk_embedding` 持久化 | 56% | 是 | 当前已支持 vault 内 scoped note / note list 同步、FTS 重建与 best-effort embedding 写入，后续需补更细粒度增量更新、脏标记、向量 coverage 观测与 FTS 漂移控制 |
| 检索层 | `backend/app/retrieval/sqlite_fts.py`、`backend/app/retrieval/embeddings.py`、`backend/app/retrieval/sqlite_vector.py`、`backend/app/retrieval/hybrid.py`、`backend/app/contracts/workflow.py`、`backend/app/services/ask.py`、`backend/app/services/ingest_proposal.py` | SQLite FTS5 top-k chunk candidate、metadata filter、filter fallback、最小向量检索、RRF hybrid candidate 输出、最小 ask 引用式返回、治理 related retrieve 与编号级 citation 对齐校验 | 68% | 是 | 后续需补 rerank、共享 semantic faithfulness core 的 runtime gate 接线、更细粒度的 filter 放宽策略、向量 coverage 观测与大 Vault 性能治理 |
| 审批与写回层 | `backend/app/contracts/workflow.py`、`backend/app/graphs/state.py`、`backend/app/indexing/store.py`、`backend/app/services/resume_workflow.py`、`plugin/src/main.ts`、`plugin/src/views/KnowledgeStewardView.ts`、`plugin/src/writeback/` | proposal / patch / audit schema、审批结果、审批面板、写回执行与审计记录 | 81% | 是 | `DAILY_DIGEST` 的真实 proposal 注入、待审批收件箱、最小写回执行器、`before_hash` 校验、`replace_section / add_wikilink`、proposal validator 对新 op 的正式支持与 `writeback_result` 回传已完成；后续需补 freshness 治理、跨会话恢复与写回后增量 ingest |
| tracing / logging 层 | `backend/app/graphs/runtime.py`、`backend/app/graphs/ask_graph.py`、`backend/app/graphs/ingest_graph.py`、`backend/app/observability/runtime_trace.py` | 运行日志、审计日志、节点耗时、错误和 token 指标 | 35% | 是 | ask / ingest 路径已落 JSONL runtime trace 与 SQLite `run_trace` 聚合，后续需补更细粒度事件、脱敏规范与文件治理 |
| eval 内容层 | `eval/run_eval.py`、`eval/golden/*.json`、`eval/results/` | golden set、回归脚本、质量指标与分场景 benchmark | 72% | 是 | 已有 ask / governance / digest / proposal / `resume_workflow` 回归，且结果已补最小 `quality_metrics`、`metric_overview`、`benchmark_overview`、场景级 `core_metrics` 与最小 `failure_type_breakdown`；后续需补宿主级验证、markdown 报告导出与样本治理 |
| 配置与模型路由层 | `backend/app/config.py` | 模型选择、本地/云切换、特性开关、延迟/成本策略 | 20% | 是 | 需补 provider 细节和秘钥管理 |

### 3.5 技术债与隐患

当前最大的技术债已经从“完全没有代码”变成“已有基线骨架，但离可验证业务闭环仍有明显距离”。这会带来以下隐患：

1. 基线已落地，但功能链路尚未接通。如果迟迟不把索引和 ask 接上，仓库会长期停留在“骨架很多、能力很少”的状态。
2. Python 开发环境已新增 `backend/environment.yml` 与 `python -m app.main` 统一入口，插件侧也已补齐最小 backend runtime 控制；但真实 Obsidian 宿主下的启动命令、shell 环境与联合启动仍未补完验证，如果后续又把 `backend/.venv` 当默认入口、或把用户手写 shell 命令包装成“完整自动化”，环境漂移和演示失真风险会再次出现。
3. 目录与模块边界初步明确，retrieval、writeback、observability 都已经有可运行基线；但实现深度仍不均衡，后续仍可能发生职责漂移。
4. 状态 schema 和 API contract 已初步固化，ask / ingest / digest graph、最小 `run_trace` 聚合、`workflow_checkpoint`、`proposal` / `patch_ops` / `audit_log` schema、`/workflows/resume` 审批恢复控制面、插件审批面板，以及 `DAILY_DIGEST` / `INGEST_STEWARD` 的最小真实 proposal 路径都已进入运行链路；写回成功后的 note 级索引刷新也已接入 `/workflows/resume`，但 ask proposal、跨会话恢复和更细粒度的多 graph trace 还没有真正接通，仍存在二次推翻风险。
5. 已有 23 条 golden set、离线 `run_eval.py`、结果文件、governance suite、最小 `quality_metrics` / `metric_overview`，以及 `question_answering / governance` 两套 benchmark、场景级 `core_metrics` 与最小 `failure_type_breakdown`；但 markdown 报告导出、demo 脚本、宿主级演示路径和更强 judge 仍未补齐，如果后续不继续扩展，评估闭环仍会停在“能解释链路差异，但还不够易展示、也不够强语义评审”的层级。
6. 最小 ask 与 ask graph 已跑通，且 generated answer 已新增程序级 citation 对齐校验；当前 ask 的离线 eval 也已能把“编号合法但答案语义超出证据”的 bad case 分桶为 `unsupported_claim`。剩余风险不再是“这类问题完全不可见”，而是“线上仍不会自动拦截，且 rule-based 分桶仍可能误报 / 漏报”。
7. ask / ingest / digest graph 已补最小 JSONL + SQLite `run_trace` 双写与按 `run_id` / `thread_id` 查询，同时已新增 SQLite `workflow_checkpoint`；但仍缺字段版本治理、文件轮转、checkpoint 清理、断流发现和更细粒度的多 graph 统一语义；如果长期停在当前状态，项目仍会停留在“graph 能跑、但治理与观测仍偏骨架”的半成品状态。
8. 当前 checkpoint 以 `thread_id + graph_name` 命中最近状态，而审批恢复以 `thread_id + proposal_id` 命中等待中的业务事实；这已经比纯 thread 恢复更稳，但如果调用方误复用旧 thread 或 proposal，仍可能打到过期状态，后续需要更强的请求指纹、版本约束或显式恢复 UX。
9. 插件审批面板已经不再只依赖本地 demo proposal；`GET /workflows/pending-approvals` 与插件侧最小 inbox 已能加载真实 waiting proposal。但当前仍只有最小更新时间排序，没有 freshness 提示、自动失效或更细的 stale item 治理；如果后续把它包装成“审批中心已完成”，依然会有明显玩具感断层。
10. `DAILY_DIGEST` 当前的 `source_notes` 选择仍依赖 `note_type` / `template_family` 启发式和最近更新时间排序；如果样本分类漂移或 Vault 很大，digest 可能结构正确但来源窗口失真。
11. 当前“本地写回成功但 `/workflows/resume` 失败”只在当前审批面板内用内存态结果避免重复落盘；如果下一阶段不补跨会话待同步入口，控制面和副作用面的恢复边界仍然偏弱。

### 3.6 当前最小可运行链路

当前已经有一个“最小可验证链路”，但还不是完整产品链路：

1. 后端可通过 `backend/app/main.py` 暴露 `/health` 与 `/workflows/invoke`。
2. `/health` 已在本地 conda 环境中验证通过，能正确返回 `sample_vault` 的统计结果。
3. `/workflows/invoke` 已能接受 `ask_qa` 与 `ingest_steward` 请求，并分别进入 [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py) 与 [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)，再返回 `ask_result` 或 `ingest_result`；其中 `ingest_steward` 已支持全量与 scoped note 两种入口。
4. 插件侧已具备 `Open panel`、`Ping backend`、`Refresh pending approvals`、`Load daily digest approval` 与 `Open approval demo` 命令，侧边栏 view 也已能展示最小 pending inbox、审批面板、patch preview 和 approve / reject 交互。
5. `backend/app/indexing/parser.py` 已能对真实样例笔记输出 `note_type`、`template_family`、`heading_path`、任务数和 wikilink 列表。
6. ask / ingest / digest graph 已能在 state 中记录最小 `trace_events`，并通过 [backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py) 默认把 runtime trace 双写到 `data/traces/ask_runtime.jsonl` 与 SQLite `run_trace`；单个 sink 写入失败会降级为其他 sink / hook 继续执行，不阻断主链路。
7. ask / ingest / digest graph 已能通过 LangGraph `SqliteSaver` 将 graph state 写入 SQLite `checkpoints` / `writes`，并在显式携带 `resume_from_checkpoint=true` + `thread_id` 的情况下从 saver 读取最近状态；`workflow_checkpoint` 同时保留 `checkpoint_status`、节点指针与 last_run_id 这层业务元数据。completed checkpoint 仍由业务层短路返回，避免重复 ask 调用、重复 scoped ingest 或重复 digest 生成。
8. [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py) 已新增 `POST /workflows/resume`，当 thread 级 checkpoint 处于 `waiting_for_approval` 且存在匹配 proposal 时，后端可消费 `thread_id / proposal_id / approval_decision`，将审批结果写入 append-only `audit_log` 并同步推进 checkpoint 状态；当本地写回已成功时，该入口还会 best-effort 触发 scoped ingest，并通过 `post_writeback_sync` 把索引刷新成功 / 失败结果一并返回。与此同时，`/workflows/invoke` 的 `DAILY_DIGEST` 与 `INGEST_STEWARD` 在显式 proposal 模式下都已能真实返回 waiting proposal，ask / ingest / digest 的普通 invoke 路径也已在 `TASK-042` 中通过 handler registry + 统一 invoker / outcome / response builder 收口为同一入口控制面。

这意味着：

- 项目已从“空仓”进入“基线骨架已落地”的阶段。
- 当前已经可以演示“后端侧最小问答兜底 + 引用式返回 + ask graph 入口 + 最小 ingest workflow 入口 + 统一 trace 语义”，不再只是协议占位。
- 下一阶段的重点不再是“继续补 P0 底座”或“再补 interview-first 保留 P1”，因为 `TASK-040`、`TASK-041`、`TASK-042`、`TASK-045`、`TASK-046`、`TASK-047`、`TASK-049`、`TASK-050`、`TASK-051`、`TASK-052`、`TASK-053`、`TASK-054` 与 `TASK-055` 都已完成；approval control-plane 到真实写回 side-effect plane 的最小闭环、post-writeback 索引一致性、最小 rollback、插件侧后端启动控制、向量 / hybrid retrieval、分场景 benchmark、ask 上下文装配层、graph-only ReAct 循环、Structured Tool Calling、共享 claim-level semantic faithfulness core、ask / digest runtime semantic gate，以及统一的 vault-relative path contract 都已接通。`TASK-048` umbrella 也已由 `TASK-050` 到 `TASK-054` 全部收口。若继续开发，默认回到已后移的 `TASK-031`，然后进入 `TASK-032`；`TASK-033` 已被 `TASK-050` / `TASK-052` 吸收。

### 3.7 Gap Analysis：现状 vs 理想目标

#### 已有能力

- 有清晰的项目目标和面试叙事方向。
- 有一份较完整的初步实现指南，已经提出 LangGraph、hybrid retrieval、HITL、eval 的大方向。
- 用户对项目边界要求非常清楚，避免了“做着做着退化为聊天机器人”。
- 已确认采用“Obsidian 插件 + Python FastAPI 后端”的双端架构。
- 已确认模型路线为“架构兼容云与本地，首版云模型优先，本地作为 fallback 或质量基线”。
- 已提供 `sample_vault/` 作为真实语料，当前已确认其包含 205 篇笔记、0 份 frontmatter、约 50 处 wikilink、473 个任务复选框。

#### 缺失能力

- 缺少 ask 的真实 proposal 主线，以及 `INGEST_STEWARD` 更强的多 note / 跨 note duplicate-conflict 治理能力；当前新笔记治理虽已从“单 note parser 信号”推进到“单 note scoped ingest + SQLite FTS related retrieve + 最小结构化 `analysis_result` + cross-note evidence”，但仍停留在单 note、FTS 启发式、现有受限 patch op 和冷索引安全 fallback 边界内。
- ask / governance / digest 的离线 faithfulness 已收敛到共享 claim-level semantic core，但仍缺更稳健的 runtime gate、LLM judge 抽样辅助或更完整的四维度 / 场景化评估。
- 后端已有可复现的 conda 环境定义与统一启动入口，插件侧也已补最小 backend runtime 控制；当前剩余缺口不再是“完全不能从插件拉起”，而是用户手写启动命令的配置脆弱性、Stop/Restart 缺失与真实 Obsidian 宿主联调记录。
- 基础 tracing（ask / ingest / digest 的节点级 JSONL + SQLite `run_trace`）已足够覆盖 interview-first P0 下限，`writeback -> reindex_incremental` 也已由 `TASK-030` 收口；当前仍缺更完整的 trace 治理、更大规模的 golden set、demo 脚本，以及 scoped ingest 的 FTS 成本基准和 CLI parity。

#### 高优先级补齐项

注：interview-first 保留主线（`TASK-040`、`TASK-041`、`TASK-042`）现已全部收口。以下列的是默认回到的下一批 medium backlog，而不是再新增一轮主线扩张。

`TASK-049` 已由 `SES-20260406-02` 完成：ask 现已优先使用 API 级 `tools / tool_calls` 做 Structured Tool Calling，并为不支持该协议的 provider 保留 fallback。下面保留的是当前真正尚未完成的 backlog。

| 优先级 | 补齐项 | 原因 | 不做会怎样 |
| --- | --- | --- | --- |
| P2 | 执行 `TASK-031`：为本地写回成功但 `/workflows/resume` 失败补跨会话恢复入口 | 当前仍只有面板内存态 `pendingWritebackResult`，插件重启后就失去只补后端记账的恢复能力 | 审计 / checkpoint 与本地副作用之间仍缺跨会话恢复控制面，无法证明真正的幂等补偿能力 |
| P2 | 执行 `TASK-032`：为 scoped ingest 落地增量 FTS 同步策略 | 当前 scoped ingest 仍会整库重建 `chunk_fts`，已经开始影响它是否适合作为持续主路径 | 写回后或单 note 治理越频繁，整库 FTS 重建越会成为明显成本与时延负担 |

#### 可延后项

- GraphRAG 的复杂图扩展。
- 自动聚类的高级算法。
- 图片 OCR、附件解析、移动端适配。
- 多模型自动路由和复杂缓存。
- 自动回滚和三方合并。

#### 两周内能做完的范围

- 插件壳、后端壳、基本配置、文档骨架。
- Markdown 结构解析、基础 chunking、SQLite FTS5 或轻量 BM25、向量召回、简单 rerank 开关。
- LangGraph 的 ingest / ask / daily digest 三条最小工作流。
- proposal 生成、审批中断、插件侧 diff 审批、单文件写回。
- JSONL trace、SQLite audit_log、最小 golden set 与脚本化回归。

#### 两周内不该碰的范围

- 复杂多 agent 协作。
- 全自动批量修改整个 Vault。
- 自研图数据库。
- 复杂 UI 美化。
- 针对未知大规模 Vault 做极致性能优化。

### 3.8 当前关键假设、风险、待确认与后续行动

| 类型 | 内容 |
| --- | --- |
| Assumption | 将采用 TypeScript Obsidian 插件 + Python FastAPI 后端 + LangGraph 的双端架构，因为这与初步实现指南一致且最便于面试讲述。 |
| Risk | 当前 `INGEST_STEWARD` 已接入 retrieval-backed `analysis_result` 与 cross-note evidence，ask 与治理也已共享同一条 hybrid candidate 底座，`TASK-040` 到 `TASK-054` 也已把 23 条 baseline 收敛到 ask / governance / digest / resume 四个 suite，并继续聚合为 `question_answering / governance` 两套 benchmark；但向量侧仍只有 best-effort 写入、最小禁用语义和固定 RRF 融合，没有 coverage 观测、branch 调试快照或 rerank，评估侧也还没有 markdown 报告导出、宿主级 benchmark 消费视图或更强 judge。 |
| Open Question | 首版云模型 provider 具体选哪家；本地 fallback 采用 Ollama 还是其他本地推理方式。 |
| Next Action | `TASK-030`、`TASK-034`、`TASK-035`、`TASK-036`、`TASK-037`、`TASK-038`、`TASK-039`、`TASK-040`、`TASK-041`、`TASK-042`、`TASK-045`、`TASK-046`、`TASK-047`、`TASK-049`、`TASK-050`、`TASK-051`、`TASK-052`、`TASK-053`、`TASK-054` 与 `TASK-055` 已完成；interview-first 保留主线已收口，`TASK-048` umbrella 也已闭环。若继续推进 medium，默认回到已后移的 `TASK-031`，然后进入 `TASK-032`；`TASK-033` 已被 `TASK-050` / `TASK-052` 吸收，其余 small 派生项继续后移。 |

## 4. 总体架构设计

### 4.1 系统组件划分

| 层级 | 负责什么 | 不负责什么 | 建议落位路径（Assumption） | 当前状态 |
| --- | --- | --- | --- | --- |
| Obsidian 插件层 | 命令入口、侧边栏 UI、设置页、与后端通信、审批交互、最终执行写回 | 不负责复杂检索、不负责 graph 编排、不负责评估 | `plugin/` | 基线已落地，审批面板骨架、真实 `DAILY_DIGEST` proposal 加载命令、pending inbox、demo fallback、受限写回执行器与 `before_hash` 校验已接通，freshness 提示与跨会话恢复仍未实现 |
| 本地后端层 | FastAPI API、任务入口、工作流调度、模型调用、索引查询、proposal 生成 | 不直接操作 Obsidian UI、不直接绕过插件修改 Vault | `backend/app/` | 基线已落地，ask / ingest / digest graph、最小 checkpoint、`DAILY_DIGEST` 与 `INGEST_STEWARD` 的真实 waiting proposal 以及 `/workflows/resume` 写回结果记账已接通，后端仍坚持不直接写 Vault |
| LangGraph 工作流层 | 定义 ingest / digest / ask 的节点、状态、路由、checkpoint、中断恢复 | 不承担最终文件写回职责 | `backend/app/graphs/` | `state.py`、`runtime.py`、`checkpoint.py`、`ask_graph.py`、`ingest_graph.py` 与 `digest_graph.py` 已落地，最小 approval resume 控制面已补齐，且 `DAILY_DIGEST` 与 `INGEST_STEWARD` 都已有 graph 内 waiting proposal 节点；ask waiting 与细粒度 interrupt 仍未实现 |
| 检索与索引层 | Markdown 解析、chunking、metadata schema、FTS/vector/hybrid/rerank | 不负责 UI、不负责审批决策 | `backend/app/indexing/`、`backend/app/retrieval/` | 解析器、SQLite schema、ingest、FTS、metadata filter、`chunk_embedding` 持久化、最小向量检索、RRF hybrid retrieval，以及四阶段 ask context assembly、`source_notes / assembly_metadata` 输出和 post-assembly citation 对齐校验都已落地；ask / governance / digest 的离线 claim-level faithfulness 评估与 ask / digest runtime semantic gate 也已接通，`runtime_faithfulness` score / threshold / outcome 已进入 contract 与 trace；当前仍缺 coverage 观测、插件侧 score 暴露与更系统的性能治理 |
| 写回与审批层 | proposal schema、diff 预览、审批结果、patch 应用、审计记录 | 不决定检索算法和模型路由 | 插件：`plugin/src/writeback/`；后端：`backend/app/writeback/` | `workflow.py`、`state.py`、`store.py` 与 `services/resume_workflow.py` 已落 proposal / patch / audit contract、schema 与 resume 控制面，`plugin/src/views/KnowledgeStewardView.ts` 与 `plugin/src/writeback/applyProposalWriteback.ts` 已接通最小 pending inbox、审批面板、受限 patch 执行、`before_hash` 校验和 `writeback_result` 回传；写回后增量 ingest、freshness 治理与跨会话恢复入口仍未实现 |
| 观测与评估层 | tracing、运行日志、错误日志、golden set、回归脚本、报告输出 | 不参与正常用户交互主链路 | `backend/app/observability/`、`eval/` | ask / ingest / digest graph 已有最小 trace hook，JSONL trace 与 SQLite `run_trace` 聚合已覆盖三条 graph，`eval/run_eval.py` 也已落 ask / governance / digest / `resume_workflow` golden 回归与共享 claim-level faithfulness report；更完整 observability 模块、指标聚合与宿主级验证仍未实现 |
| 存储层 | SQLite、向量存储、checkpoint、JSONL trace、配置文件 | 不提供业务逻辑 | `data/`、`backend/data/` | SQLite `note/chunk`、`chunk_embedding`、`run_trace`、LangGraph `checkpoints` / `writes`、`workflow_checkpoint`、`proposal`、`patch_op` 与 `audit_log` 已落地；当前向量侧仍是 SQLite 内持久化与 JSON embedding，不是独立向量库，更完整持久化治理与性能优化仍未实现 |

### 4.2 数据流

#### 4.2.1 新笔记治理的数据流

1. 用户在 Obsidian 中保存或主动触发“治理当前笔记”命令。
2. 插件读取当前文件路径、可选读取 MetadataCache，并调用后端 `/workflow/ingest`。
3. 后端加载笔记内容与元数据，执行相关内容召回与重复/冲突/孤立分析。
4. 后端生成结构化 proposal 和 patch plan，而不是直接改文件。
5. LangGraph 在审批节点 `interrupt`，把 proposal 返回给插件。
6. 插件展示 diff、证据引用和风险提示，等待人工批准。
7. 人工批准后，插件执行写回；插件将实际写回结果与新 hash 回传后端。
8. 后端记录 audit log，触发增量索引更新，并结束 thread。

#### 4.2.2 每日复盘的数据流

1. 用户手动触发或定时触发“每日复盘”。
2. 后端选择时间窗口，收集近期笔记并做规则聚合或轻量聚类。
3. 从聚合结果中提取主题、开放问题、行动项、复习候选。
4. 后端生成复盘草稿 proposal。
5. 进入审批节点，由插件展示将要写入的复盘 note 内容。
6. 审批通过后，插件新建或更新复盘 note。
7. 后端记录审计日志和本次复盘统计。

#### 4.2.3 问答兜底的数据流

1. 用户输入问题。
2. 后端执行 query 解析与 metadata pre-filter。
3. 执行 hybrid retrieval。
4. 可选执行 rerank。
5. 基于引用生成答案，输出来源路径、片段和置信提示。
6. 插件展示答案、引用和相关 chunk，必要时允许用户发起“对结果相关笔记执行治理”。

### 4.3 模块边界

#### 插件层边界

- 负责用户交互、审批、最终写回执行。
- 读取 Vault 时可做轻量缓存，但不负责复杂索引和图逻辑。
- 不允许在没有后端确认的情况下自行生成大段治理建议。

#### 后端层边界

- 负责所有“需要状态和策略”的动作，如工作流、索引、检索、模型路由、评估。
- 不直接操纵 Obsidian 界面。
- 不绕过插件直接改 Vault，避免权限、同步和审计边界不清。

#### 工作流层边界

- 只负责状态转移和节点编排。
- 节点内部调用 retrieval、proposal、logging 等服务，但 graph 不直接嵌入过多业务细节。
- 中断节点之后的副作用节点必须具备幂等保障。

### 4.4 为什么这么分层

- 如果把所有逻辑塞进插件，会导致本地 UI 线程、索引、模型调用、写回和评估混在一起，开发体验与稳定性都会很差。
- 如果让后端直接改 Vault，虽然实现更快，但审计边界模糊，面试时很难回答“为什么安全”。
- 将审批与写回留在插件层，可以更贴近用户交互，也更便于用 Obsidian 官方 API 做原子 frontmatter 处理。
- 将 graph、检索、评估留在后端层，可以单独测试、独立运行、后续易于脚本化回归。
- 当前新增的 `/health` 与协议模型进一步验证了这套分层是可落地的：插件只需理解少量 contract，不需要知道后端内部 graph 和索引细节。

### 4.5 关键技术选型

| 选型 | 角色 | 选择原因 | 不这样做会怎样 | 备选方案 | 当前风险 |
| --- | --- | --- | --- | --- | --- |
| LangGraph | 工作流编排、状态持久化、中断恢复 | 项目核心是长流程、有状态、可中断、可恢复，不是单轮调用 | 很难优雅支持审批、恢复、线程级审计 | 纯函数编排、自写状态机、LangChain 高层 Agent | 团队需要先熟悉 state graph 与幂等思维 |
| Obsidian Plugin API | UI、命令、Vault 写回、MetadataCache | 官方 API 能直接处理笔记和 frontmatter，避免黑客式文件读写 | 写回可靠性差，容易破坏用户文件 | 纯文件系统 watcher | 插件生态 API 需要适配桌面端习惯 |
| Python + FastAPI | 后端服务、图执行、评估脚本 | LangGraph/Python 生态更成熟，eval 和数据处理也更顺手 | 图、eval、检索逻辑难以组织 | 纯 TypeScript 后端 | 双语言仓库会增加工程复杂度 |
| SQLite + FTS5 | metadata、审计、checkpoint、轻量全文检索 | 本地优先、部署成本低、两周可落地 | 需要额外引擎，复杂度上升 | Postgres、Meilisearch、tantivy | 当 Vault 规模大时扩展性有限 |
| SQLite `chunk_embedding` + Python 余弦检索（MVP） | embedding 存储与最小向量检索 | 复用现有 SQLite schema、本地部署边界和 note/chunk 生命周期，不把 `TASK-037` 扩成第二套基础设施接入 | 会让当前会话被新存储选型、迁移和部署成本打穿 | Chroma、FAISS、LanceDB、Qdrant、本地 SQLite 扩展 | 当前是全量扫描 JSON embedding 的 MVP，实现简单但不适合大 Vault，后续仍需评估 ANN 或独立向量库 |
| Cross-encoder reranker | 精排 | Obsidian 语料短小碎片多，粗召回后精排收益大 | hybrid top-k 易出现相关但排序差的问题 | 不用 rerank、LLM rerank | 延迟可能高 |
| Cloud-primary / Local-compatible Provider | 模型与 embedding 路由策略 | 当前已确认云模型优先，但保留本地 fallback 和质量基线能力 | 如果只做本地优先，会拖慢首版交付；如果只做云优先，会丢失离线演示与 fallback | 完全云优先、完全本地优先 | 网络稳定性、API key、双 provider 测试矩阵会增加复杂度 |
| audit log + checkpoint + trace | 审计与回放 | 这是“可审计、可恢复、可评估”的硬基础设施 | 项目会退化成演示型 Demo | 只打普通日志 | 初期容易觉得慢，但不能省 |

### 4.6 替代方案与放弃原因

| 替代方案 | 为什么放弃 |
| --- | --- |
| 只用单个 ReAct agent | 不可控，状态难管理，审批和恢复都会很别扭，面试中难自圆其说。 |
| 全靠 LangChain 高层封装 | 能更快起步，但会弱化你对状态、边界、幂等和审计的掌控力。项目主卖点是工程化闭环，不是快速拼装。 |
| 不做本地后端，只做单体 Obsidian 插件 | 实现似乎更省事，但索引、模型调用、graph、eval、trace 全塞在插件里会很乱，也不利于测试与回归。 |
| 只做向量检索 | 对 Obsidian 这种有标题、标签、术语、代码块、wikilink 的语料不够稳；关键词和 metadata filter 很重要。 |
| 省掉人工审批 | 可以更快做自动化，但无法保证安全写回，面试会被直接质疑“如何避免把用户笔记改坏”。 |

### 4.7 当前关键假设、风险、待确认与后续行动

| 类型 | 内容 |
| --- | --- |
| Assumption | 首版采用双端架构，模型层兼容云与本地，但默认优先调用云模型。 |
| Risk | 双端架构会增加调试成本；虽然插件现已支持最小 backend runtime 控制，但启动命令仍依赖用户本地 shell / 环境配置，云模型优先也会把网络稳定性和密钥配置变成首版风险源。 |
| Open Question | 首版是只支持一个云 provider，还是一开始做多 provider 抽象。 |
| Next Action | `TASK-030`、`TASK-034`、`TASK-035`、`TASK-036`、`TASK-037`、`TASK-038`、`TASK-039`、`TASK-040`、`TASK-041`、`TASK-042`、`TASK-045`、`TASK-046`、`TASK-047`、`TASK-049`、`TASK-050`、`TASK-051`、`TASK-052`、`TASK-053`、`TASK-054` 与 `TASK-055` 已完成；interview-first 保留主线已收口，`TASK-048` umbrella 也已闭环。若继续推进 medium，默认回到已后移的 `TASK-031`，然后进入 `TASK-032`；`TASK-033` 已被 `TASK-050` / `TASK-052` 吸收，其余 small 派生项继续后移。 |

## 5. LangGraph 工作流详细设计

### 5.1 新笔记治理工作流

#### 5.1.1 目标

输入一个新建或最近修改的笔记，输出一份经过证据支撑的治理 proposal，并在人工审批通过后执行有限写回和增量索引更新。

#### 5.1.2 节点级流程

| 节点名称 | 输入 | 输出 | 依赖 | 是否调用 LLM | 是否读写索引 | 是否写 Vault | 风险等级 | 失败模式 | retry / fallback 策略 | 面试追问点 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `trigger_ingest` | `note_path`、`trigger_source`、`thread_id` | 规范化请求 | 插件命令/API | 否 | 否 | 否 | 低 | 插件未传入活动文件 | 直接失败并提示重新选择文件 | 为什么不把保存事件直接做成自动写回 |
| `read_note` | `note_path` | `raw_markdown`、`file_stat` | Vault 读取接口 | 否 | 否 | 否 | 低 | 文件不存在、编码异常 | 重读一次；失败则终止 | 为什么读取要在 graph 里而不是插件直接传全文 |
| `parse_metadata` | `raw_markdown` | `frontmatter`、`headings`、`links`、`block_refs` | Markdown parser / MetadataCache | 否 | 可写解析缓存 | 否 | 中 | frontmatter 非法、标题层级混乱 | 解析失败时降级为全文块 | 解析为什么不能只靠正则 |
| `retrieve_related` | `title`、`headings`、`links`、`raw_markdown` | `candidate_chunks`、`retrieval_queries` | SQLite FTS、metadata filter | 否 | 读索引 | 否 | 中 | 索引不存在、冷索引下无旧笔记命中、错误召回 target note 自身 | 当前仅做 FTS fallback；自匹配直接排除，召回不足时返回空 related evidence 而不是硬造低置信结论 | 为什么 `TASK-035` 先用 FTS 而不是一步到位做 hybrid |
| `analyze_duplicate_conflict_orphan` | `current_note`、`candidate_chunks` | `analysis_result`、`issues[]`、`evidence[]` | 规则 | 否 | 读索引 | 否 | 中 | related candidate 噪声高、冷索引导致 evidence 缺失、启发式误判 | 只输出保守的 `orphan_hint / duplicate_hint` 与本地结构信号；证据不足时不扩张成更强结论 | 你怎么定义 duplicate / orphan_hint，为什么当前不让 LLM 直接判 |
| `generate_proposal` | `issues`、`evidence`、`note_meta` | `proposal`、`patch_plan`、`risk_summary` | LLM、schema validator | 是 | 否 | 否 | 高 | JSON 结构错、修改范围过大 | 强制 schema 校验；失败则只输出只读建议 | 为什么 proposal 不直接是自然语言 |
| `human_approval` | `proposal`、`patch_plan` | `approval_decision` | LangGraph interrupt、插件审批 UI | 否 | 否 | 否 | 高 | UI 未响应、用户取消 | thread 持久化等待；用户拒绝则归档 | interrupt 应放在哪里，为什么 |
| `build_patch` | `approved_proposal` | `patch_ops`、`idempotency_key` | patch builder | 否 | 否 | 否 | 高 | patch 与当前文件不匹配 | 先检查前置 hash；不匹配则重新预览 | 为什么 patch 要结构化 |
| `apply_writeback` | `patch_ops`、`before_hash` | `writeback_result` | 插件执行写回 | 否 | 否 | 是 | 极高 | 写回失败、前置内容漂移 | 不自动重试破坏性写回；回到审批界面 | 为什么必须插件执行而不是后端写文件 |
| `audit_record` | `proposal`、`approval`、`writeback_result` | `audit_event_id` | audit store | 否 | 写审计表 | 否 | 中 | 日志写入失败 | 降级为 JSONL 本地落盘 | 审计日志要记录哪些字段 |
| `incremental_reindex` | `note_path`、`writeback_result` | `reindex_status` | 索引器 | 否 | 写索引 | 否 | 中 | 索引脏数据、嵌入失败 | 标记 dirty，后台重试 | 为什么不在写回前先删旧索引 |

#### 5.1.3 设计动机

- 新笔记治理是整个项目最能体现“知识治理而非问答”的主战场。
- 必须把召回、分析、proposal、审批、写回拆开，因为这些步骤的风险等级和责任边界不同。
- 只有 proposal 被结构化后，后续 diff、审计、eval 才有基础。

#### 5.1.4 输入输出边界

- 输入边界：单个 note 路径、触发来源、可选的活动上下文。
- 输出边界：结构化 proposal、patch plan、审计事件，不直接输出“模型自由发挥后的文件全文”。
- 禁止边界：未审批时不允许修改 Vault。

### 5.2 每日复盘工作流

#### 5.2.1 目标

对最近一个时间窗口内的笔记集合进行聚合，输出主题摘要、开放问题、行动项和复习计划草稿，并通过审批后写入复盘 note。

#### 5.2.2 节点级流程

| 节点名称 | 输入 | 输出 | 依赖 | 是否调用 LLM | 是否读写索引 | 是否写 Vault | 风险等级 | 失败模式 | retry / fallback 策略 | 面试追问点 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `select_window` | `date`、`window_rule` | `start_ts`、`end_ts` | 时间策略配置 | 否 | 否 | 否 | 低 | 时区或规则错误 | 使用本地时区并落日志 | 为什么不用 cron 外部做 |
| `collect_recent_notes` | 时间窗口 | `note_paths[]`、`stats` | 文件时间索引 | 否 | 读索引 | 否 | 中 | mtime 不可靠 | 可加 frontmatter / folder / tag 过滤 | 复盘为什么不直接全库扫 |
| `group_topics` | `note_paths[]`、`chunk_vectors` | `topic_groups[]` | 规则分组或轻量聚类 | 可选 | 读索引 | 否 | 中 | 聚类过散或过混 | P0 先按 tag/folder/time 规则分组 | 什么时候需要真正聚类算法 |
| `extract_open_questions` | `topic_groups[]` | `open_questions[]` | 规则 + LLM | 是 | 可读索引 | 否 | 中 | 提取出伪问题 | 置信低时只输出候选 | 如何定义开放问题 |
| `extract_action_items` | `topic_groups[]`、`open_questions[]` | `action_items[]` | 规则 + LLM | 是 | 否 | 否 | 中 | 行动项太泛泛 | 限制动词模板并引用来源 | 行动项如何避免空话 |
| `generate_review_plan` | `action_items[]`、`topic_groups[]` | `review_plan` | LLM | 是 | 否 | 否 | 中 | 计划过长、不现实 | 约束输出长度和日期粒度 | 复习计划如何评价质量 |
| `draft_digest_note` | 所有聚合结果 | `digest_proposal`、`patch_plan` | 模板引擎 + LLM | 是 | 否 | 否 | 中高 | 草稿重复、格式不稳 | 使用固定模板，LLM 仅填内容区 | 为什么不直接自由生成整篇复盘 |
| `human_approval` | `digest_proposal` | `approval_decision` | 插件审批 UI | 否 | 否 | 否 | 高 | 用户拒绝 | 保留草稿，可手动编辑后再提交 | 审批为什么对复盘也必要 |
| `write_digest_note` | 已批准草稿 | `writeback_result` | 插件写回 | 否 | 否 | 是 | 高 | 文件冲突、路径不存在 | 新建草稿文件并提示用户调整 | 复盘 note 应新建还是覆盖 |
| `audit_record` | 复盘 proposal + result | `audit_event_id` | 审计存储 | 否 | 写日志 | 否 | 中 | 日志失败 | JSONL 降级 | 如何回溯某次复盘依据 |

#### 5.2.3 设计动机

- 复盘不是问答拼装，而是聚合多篇近期笔记后的治理动作。
- 与新笔记治理不同，这里输入是集合，输出是复盘资产和后续行动闭环。
- 复盘工作流能让项目从“单次响应工具”升级为“持续治理系统”。

### 5.3 问答兜底工作流

#### 5.3.1 目标

在用户确实需要查询历史知识时，提供基于当前 Vault 的可解释检索问答；该工作流不负责写回，只负责给出答案与来源。

#### 5.3.2 节点级流程

| 节点名称 | 输入 | 输出 | 依赖 | 是否调用 LLM | 是否读写索引 | 是否写 Vault | 风险等级 | 失败模式 | retry / fallback 策略 | 面试追问点 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `parse_query` | `user_query`、可选活动 note | `intent`、`filters`、`query_terms` | 规则 + 轻量模型 | 可选 | 否 | 否 | 低 | 误判过滤条件 | 默认不过滤，只提示范围大 | 为什么 query parsing 有必要 |
| `metadata_prefilter` | `filters` | `candidate_note_ids[]` | metadata store | 否 | 读索引 | 否 | 低 | 过滤过严 | 降级为无过滤 | 过滤会不会伤 recall |
| `hybrid_retrieval` | query + filters | `retrieved_chunks[]` | FTS/vector | 否 | 读索引 | 否 | 中 | 只命中局部词或语义漂移 | 提高 top-k、返回低置信标志 | 为什么 hybrid 比单路径稳 |
| `rerank` | `retrieved_chunks[]` | `ranked_chunks[]` | cross-encoder | 否 | 读索引 | 否 | 中 | 过慢、模型不可用 | 可配置关闭；仅保留召回结果 | 什么时候不值得开 rerank |
| `cite_generate` | `ranked_chunks[]`、query | `answer`、`citations[]` | LLM | 是 | 否 | 否 | 中 | 幻觉引用、遗漏来源 | 约束引用必须来自候选 chunk；失败则返回摘要式检索结果 | 如何保证 answer grounded |
| `return_result` | `answer`、`citations` | 给插件的响应 | API 层 | 否 | 否 | 否 | 低 | SSE 中断 | 返回非流式备选 | 为什么问答链路不写回笔记 |

#### 5.3.3 设计动机

- 问答是兜底，不是主价值；但没有问答，用户很难感知索引层收益。
- 通过问答链路可以先独立验证 retrieval、rerank、citation 是否工作正常。
- 它是最适合先跑通的低风险链路，可作为整个系统的技术基线。

### 5.4 节点设计统一约束

| 约束 | 说明 |
| --- | --- |
| 幂等 | 所有包含副作用的节点必须接收 `idempotency_key` 或 `before_hash`，避免恢复执行时重复写回。 |
| 可观察 | 每个节点至少记录开始时间、结束时间、输入摘要、输出摘要、错误状态。 |
| 可恢复 | 审批节点之前的状态必须可持久化，审批节点之后的副作用必须可被识别为“已执行”或“未执行”。 |
| 可降级 | 检索、rerank、聚类、LLM 分析等节点都要定义无模型/低置信 fallback。 |
| 可评估 | 检索节点输出 chunk id 和分数；proposal 节点输出结构化结果，便于自动评估和抽样复核。 |

### 5.5 条件路由与状态设计

#### 5.5.1 state schema

建议首版定义统一的 `StewardState`，核心字段如下：

| 字段 | 类型 | 是否持久化 | 说明 |
| --- | --- | --- | --- |
| `thread_id` | `str` | 是 | 一个工作流实例的稳定标识，审批恢复必须依赖它。 |
| `run_id` | `str` | 是 | 单次运行 ID，用于 tracing 和审计关联。 |
| `action_type` | `enum` | 是 | `INGEST_STEWARD` / `DAILY_DIGEST` / `ASK_QA`。 |
| `note_path` | `str \| null` | 是 | 当前单笔记治理的目标路径。 |
| `note_paths` | `list[str]` | 是 | 复盘场景的输入笔记集合。 |
| `raw_markdown` | `str \| null` | 否 | 原文可大，可按需放外部缓存或仅在当前轮使用。 |
| `note_meta` | `dict` | 是 | 标题、tags、links、mtime 等解析结果。 |
| `retrieved_chunks` | `list[dict]` | 是 | 检索结果 ID、分数、摘要和来源。 |
| `analysis_issues` | `list[dict]` | 是 | 重复、冲突、孤立等分析结果。 |
| `proposal` | `dict \| null` | 是 | 审批前最关键的结构化输出。 |
| `approval_required` | `bool` | 是 | 是否需要中断审批。 |
| `approval_decision` | `dict \| null` | 是 | 人工审批结果及备注。 |
| `patch_plan` | `list[dict]` | 是 | 结构化 patch 操作列表。 |
| `before_hash` | `str \| null` | 是 | 写回前文件摘要。 |
| `writeback_result` | `dict \| null` | 是 | 写回状态、after hash、错误信息。 |
| `audit_event_id` | `str \| null` | 是 | 审计日志主键。 |
| `errors` | `list[dict]` | 是 | 节点级错误历史。 |
| `transient_prompt_context` | `dict` | 否 | 仅供当前节点使用的 prompt 上下文，不需要永久保存。 |

#### 5.5.2 thread_id / checkpoint 组织方式

- 以单个工作流实例作为一个 `thread_id`。
- 插件触发时生成或复用 `thread_id`，后端按 `thread_id` 从 checkpointer 恢复。
- `run_id` 与 `thread_id` 分离：前者代表一次执行，后者代表跨中断和恢复的同一事务。
- 对审批场景，恢复时必须显式带上 `thread_id` 和 `approval_decision`。

#### 5.5.3 哪些字段必须持久化

- `thread_id`、`action_type`、`proposal`、`approval_required`、`approval_decision`、`patch_plan`、`before_hash`、`writeback_result`、`audit_event_id`。
- 这些字段直接决定是否能恢复、是否能避免重复写回、是否能审计回放。

#### 5.5.4 哪些字段只在单轮临时存在

- 原始 prompt 拼接文本。
- LLM 中间推理草稿。
- 长文本原文的完整副本。
- 大体量 embedding 向量。

#### 5.5.5 中断恢复时如何避免副作用重复执行

1. 将 `interrupt` 放在独立审批节点，后续副作用节点不得与审批逻辑混在一起。
2. 写回前记录 `before_hash`，插件执行时校验当前文件 hash 是否一致。
3. `patch_plan` 生成后分配 `proposal_id` 和 `idempotency_key`。
4. 审批恢复后先检查该 `proposal_id` 是否已应用；若已应用，只补日志和索引，不重复写回。
5. 审计日志中记录 `writeback_applied=true/false`，恢复流程必须先查该标志。

### 5.6 当前关键假设、风险、待确认与后续行动

| 类型 | 内容 |
| --- | --- |
| Assumption | graph 层采用“独立 graph 文件 + 共享 runtime helper”模式，避免单文件堆积多条链路；当前 ask / ingest 已验证这一路线可行。 |
| Risk | 如果一开始不定义 proposal / patch 的结构化协议，graph 会退化成一堆自由文本节点，后续很难加审批、评估和回滚。 |
| Open Question | 共享 `thread_id + graph_name` 的 SQLite checkpointer 已落地，后续是否要升级到节点级 / 副作用分层恢复语义，还是继续维持线程级快照恢复。 |
| Next Action | `TASK-030`、`TASK-034`、`TASK-035`、`TASK-036`、`TASK-037`、`TASK-038`、`TASK-039`、`TASK-040`、`TASK-041`、`TASK-042`、`TASK-045`、`TASK-046`、`TASK-047`、`TASK-049`、`TASK-050`、`TASK-051`、`TASK-052`、`TASK-053`、`TASK-054` 与 `TASK-055` 已完成；interview-first 保留主线已收口，`TASK-048` umbrella 也已闭环。若继续推进 medium，默认回到已后移的 `TASK-031`，然后进入 `TASK-032`；`TASK-033` 已被 `TASK-050` / `TASK-052` 吸收，其余 small 派生项继续后移。 |

## 6. 检索与索引系统设计

### 6.1 文档解析策略

| 结构元素 | 解析策略 | 为什么这样做 | 失败模式 | 降级策略 |
| --- | --- | --- | --- | --- |
| frontmatter | 单独解析为结构化 metadata，并保留原始 YAML 文本 | tags、aliases、status、date 等强结构字段对检索和写回都关键 | YAML 非法、字段类型不一 | 保留原文并记录解析错误，不阻塞全文索引 |
| headings | 建立 heading tree，生成 `heading_path` | Obsidian 内容天然按标题组织，适合 section-level chunking | 标题跳级、重复标题 | 允许跳级并保留原始顺序 |
| sections | 按 heading 边界切分正文段落 | 比纯 token chunk 更符合笔记结构 | 超长 section | 再按段落或句子二次切分 |
| code block | 单独 chunk，记录语言和位置 | 代码块的检索特征不同，关键词命中价值更高 | 代码块未闭合 | 按原文兜底，不做结构化增强 |
| table | 单独 chunk，并提取表头和行文本 | 表格在向量模型中表现常不稳定，BM25 更重要 | 表格格式不规范 | 保留原表文本 |
| internal links | 解析 `[[note]]`、`[[note#heading]]`、`[[note#^block]]` | 这些是知识图和治理建议的基础 | 链接别名、路径歧义 | 保留原始 link token，延后解析 |
| block references | 记录 block id 与所在 section | 支持更细粒度引用和写回定位 | block id 缺失或不规范 | 只保留 section 级别 |
| unresolved links | 记录未解析 link 及出现位置 | 可用于治理“应该创建还是修正目标 note” | 误把普通文本当链接 | 仅在 link 语法合法时记录 |

### 6.2 chunking 策略

#### 为什么不能粗暴按 token 切

- Obsidian 笔记不是 PDF 长文，而是大量短文、层级标题、列表、表格、代码块和链接。
- 粗暴按 token 切会破坏标题上下文、frontmatter 对齐和后续写回定位。
- 知识治理需要知道“建议插在哪个标题下”“这个结论来自哪个 section”，纯 token chunk 无法支撑。
- 当前 `sample_vault/` 进一步证明了这一点：大量日记采用固定标题模板，如 `Task Planner / Long Target / Day Life / Summary` 或 `一、工作任务 / 二、学习目标 / 三、今日进程 / 四、今日总结`，这些天然就是首版最佳 chunk 边界。

#### 建议的 chunk 类型

| chunk_type | 用途 | 是否参与向量召回 | 是否参与 FTS | 是否可回写定位 |
| --- | --- | --- | --- | --- |
| `frontmatter` | 标签、别名、日期、状态等结构化信息 | 可选 | 是 | 是 |
| `section_parent` | 标题级大块，保留完整上下文 | 否，更多用于返回上下文 | 是 | 是 |
| `section_child` | 段落或列表级小块，用于精细召回 | 是 | 是 | 是 |
| `code` | 代码检索 | 是 | 是 | 是 |
| `table` | 表格检索 | 可选 | 是 | 是 |
| `summary_stub` | 对超长内容的压缩摘要块 | 可选 | 否 | 否 |

#### parent-child 关系怎么做

- `section_parent` 保存完整标题下内容。
- `section_child` 保存父 section 内的更细片段。
- 向量召回优先命中 child，最终返回时同时带上 parent 以保证上下文完整性。
- 元数据中必须保留 `parent_chunk_id`、`heading_path`、`start_line`、`end_line`。

#### metadata 设计原则

- 尽量把“检索过滤所需字段”放结构化列，不要每次 LLM 再猜。
- 所有 chunk 必须可追溯到 note path 和原文位置。
- 对治理场景，链接出入度和 note type 比单纯 embedding 更重要。
- 当前样本几乎没有 frontmatter，因此 `note_type`、`daily_note_date`、`template_family` 更应该从路径和标题模板推断，而不是依赖 YAML。

#### 基于 `sample_vault/` 的首版语料结论

| 观察 | 结论 | 对设计的影响 |
| --- | --- | --- |
| 205 篇 Markdown，集中在 `sample_vault/日常/` | 规模适合首版全量索引与离线评估 | 首版不需要复杂分布式索引 |
| 0 份 frontmatter | 不能把治理重点押在 YAML 补全上 | 首版 metadata 以路径、标题、任务、链接、时间为主 |
| 约 50 处 wikilink | 已有链接信号，但不密 | 双链建议仍有价值，但 GraphRAG 不是 P0 |
| 473 个任务复选框 | 任务抽取与复盘是高价值场景 | 每日复盘优先支持未完成任务聚合 |
| 存在两类稳定模板：中英两套日记标题 | 可通过模板识别做 note_type 推断 | chunking、复盘聚合和 proposal 模板都应优先适配 daily note |
| 含迭代总结、任务分解、周报类文档 | 复盘和问答不只是 daily note 摘要 | 首版问答与 digest 都应支持“总结型 note” |

### 6.3 metadata schema

| 字段 | 类型 | 来源 | 必选 | 用途 |
| --- | --- | --- | --- | --- |
| `path` | `str` | 文件系统 / Vault | 是 | 唯一路径标识与引用来源 |
| `title` | `str` | 文件名或一级标题 | 是 | 标题检索与展示 |
| `tags` | `list[str]` | frontmatter / inline tags | 是 | metadata filter、治理建议 |
| `aliases` | `list[str]` | frontmatter | 否 | 别名检索、重复检测 |
| `ctime` | `datetime` | 文件属性 | 否 | 时间窗口筛选 |
| `mtime` | `datetime` | 文件属性 | 是 | 增量索引、复盘窗口 |
| `heading_path` | `str` | 标题树 | 否 | section 级定位 |
| `chunk_type` | `str` | chunking | 是 | 检索与写回策略分流 |
| `block_id` | `str \| null` | block ref | 否 | 块级引用 |
| `out_links` | `list[str]` | wikilinks | 否 | 知识图扩展、孤立检测 |
| `in_links_count` | `int` | 反向统计 | 否 | 孤立笔记判定 |
| `note_type` | `str \| null` | 规则或 frontmatter | 否 | 区分 daily note / project / source note |
| `source_type` | `str \| null` | 外部来源标记 | 否 | 论文摘录、课程笔记等分层治理 |
| `folder` | `str` | 路径 | 否 | 范围过滤 |
| `hash` | `str` | 内容摘要 | 是 | 幂等、增量索引 |

### 6.4 检索策略

#### 首版策略

1. `metadata pre-filter`
   - 根据 path、folder、tags、note_type、mtime 做预过滤。
   - 目的不是代替检索，而是减少无关噪声。

2. `BM25 / FTS`
   - 对标题、标签、代码块、表格和术语匹配非常重要。
   - 首版优先 SQLite FTS5，降低依赖复杂度。

3. `vector retrieval`
   - 用于语义召回，覆盖同义表达和非精确措辞。

4. `hybrid fusion`
   - 首版使用加权 RRF 或简单归一化加权。
   - 输出统一分数与来源。

5. `reranker`
   - 只对 top-k 候选做精排，默认 top-k 不超过 12。
   - 配置开关必须可关闭。

6. `wikilink / graph expansion`
   - P1 可做。对高分结果的相邻链接做一跳扩展，用于解释和治理推荐。

### 6.5 为什么这样设计

- Obsidian 语料强结构、弱规范。仅向量会丢掉很多标题、术语、标签的精确信号。
- 个人笔记常有短句、列表、碎片记录，embedding 对超短块不总是稳定，FTS 更稳。
- 知识治理场景比问答更依赖 metadata，比如“找近期无链接的概念笔记”“找和当前标签重合但观点冲突的内容”。
- chunking 需要同时服务检索和写回。如果 chunk 无法回指原文位置，proposal 很难落成 patch。

### 6.6 评估方式

#### 怎么测 recall

- 对问答场景，为每条样本标注一组“应该命中的 chunk_id / note_path”。
- 计算 Top-K 是否覆盖参考证据。
- 对治理场景，可标注“应该召回的相关旧笔记/冲突笔记/重复笔记”。

#### 怎么测 precision

- 看 Top-K 结果中真正相关项占比。
- 看相关项在前排的集中度，而不是只看是否命中过。

#### 怎么看 rerank 是否值得

- 对同一批样本对比“有 rerank / 无 rerank”的 Context Precision、P95 延迟和成本。
- 如果质量提升不明显但延迟显著上升，则默认关闭，仅在高风险治理和困难问答中开启。

#### 哪些 bad case 最容易出现

- 术语很短，向量命中弱。
- 标题重名或概念混用。
- 表格和代码块被错排。
- 笔记非常短，信息不足但标题诱导性强。
- wikilink 未解析或 alias 很多，导致路径歧义。

### 6.7 面试官追问点（至少 10 个）

| 问题 | 回答要点 |
| --- | --- |
| 为什么不是只做 embedding search | Obsidian 语料里标题、标签、短术语、代码块很多，关键词匹配和 metadata filter 的价值很高。 |
| 为什么不是只做 BM25 | 同义表达、模糊查询和概念性召回需要向量；只靠关键词会漏掉很多相关内容。 |
| 你怎么定义 chunk 边界 | 以 heading、frontmatter、代码块、表格和段落为主，而不是纯 token。目标是既方便检索，也方便定位回写。 |
| 为什么需要 parent-child | child 提供精度，parent 提供完整上下文；这对引用生成和 proposal 证据都重要。 |
| metadata filter 会不会伤 recall | 会，所以它必须是可配置的 pre-filter，且失败时能回退到宽松模式。 |
| 为什么 rerank 不直接用 LLM | LLM rerank 成本和延迟更高，不稳定；cross-encoder 更适合作为 deterministic 的精排组件。 |
| 如何评估 hybrid 比单一路径好 | 用同一 golden set 对比 recall、precision、延迟和 bad case 分布，不用主观感觉。 |
| 代码块和表格为什么要单独处理 | 它们的结构和检索信号与自然语言段落不同，如果混在一起会拉低排序质量。 |
| 你怎么利用 Obsidian 的 link 结构 | 用于孤立笔记检测、相关内容扩展、复盘主题归并和未来的 GraphRAG。 |
| 如果用户标签很乱怎么办 | 标签不是唯一信号；还要结合路径、链接、标题、时间和正文内容。治理本身也要补标签。 |

### 6.8 当前关键假设、风险、待确认与后续行动

| 类型 | 内容 |
| --- | --- |
| Assumption | 首版索引继续以 SQLite 为主：`note/chunk` 与 `chunk_embedding` 共用同一持久化边界，不额外引入独立向量服务；embedding 与生成默认优先走云模型。 |
| Risk | 云 embedding 如果网络不稳，会让系统进入“主索引成功、向量侧 best-effort 降级”的部分可用状态；当前 hybrid 已能安全退回 FTS，但在 coverage 观测和 branch 调试仍缺失的前提下，这仍会直接影响首版 ingest 与检索体验。 |
| Open Question | `sample_vault/` 是否代表真实使用模式，还是只是日常笔记子集。 |
| Next Action | 在 pending inbox、scoped ingest、首条 ingest proposal、ask graph-only ReAct 循环、post-writeback scoped reindex、retrieval-backed analyze、插件 backend runtime 控制、最小向量写入 / 检索、hybrid retrieval、分场景 benchmark、最小 rollback、统一 workflow contract、`TASK-047` 的四阶段上下文装配管线、`TASK-049` 的 Structured Tool Calling、`TASK-050` 的 ask runtime faithfulness 首刀、`TASK-051` 的共享 claim-level semantic faithfulness core、`TASK-052` 的 ask / digest runtime semantic gate、`TASK-053` 的 ask 四维度离线评估、`TASK-054` 的 governance / digest 场景化指标，以及 `TASK-055` 的 vault-relative path contract 都已落地的基础上，当前 interview-first 保留主线已收口，`TASK-048` umbrella 也已闭环；若继续推进 medium，默认回到已后移的 `TASK-031`，然后进入 `TASK-032`，`TASK-033` 已被 `TASK-050` / `TASK-052` 吸收，`TASK-041`、`TASK-046` 与 `TASK-047` 的既有 `small` 派生项继续后移。 |

## 7. 写回系统与 Human-in-the-loop 设计

### 7.1 为什么写回必须人工审批

- Knowledge Steward 的核心价值不是“会说”，而是“敢改但不乱改”。
- 笔记写回一旦出错，损失的是用户长期积累的知识资产，不是一次对话结果。
- 高风险操作必须让用户看见证据、变更范围和目标位置，否则无法证明系统可信。

### 7.2 哪些操作属于高风险

| 操作 | 风险原因 | 首版策略 |
| --- | --- | --- |
| frontmatter 覆盖 | 容易丢失手工字段或破坏 YAML | 强制审批，原子处理 |
| 删除正文段落 | 可能误删用户原始思考 | 首版默认不自动删除，只标记建议 |
| 批量插入 links | 易产生错误链接污染 | 单文件少量插入可审批，大批量延后 |
| 合并重复笔记 | 最容易误伤语义和结构 | 两周内只给合并建议，不做自动执行 |
| 修改文件名或路径 | 会影响链接和组织结构 | 首版不做 |
| 批量标签重写 | 影响范围大且难回滚 | 首版不做 |

### 7.3 proposal 的结构设计

proposal 必须是结构化对象，建议如下：

```json
{
  "proposal_id": "prop_20260311_xxx",
  "action_type": "INGEST_STEWARD",
  "target_note_path": "notes/example.md",
  "summary": "补充 2 个标签，插入 3 条相关链接，新增一段摘要",
  "risk_level": "high",
  "evidence": [
    {
      "source_path": "notes/related.md",
      "heading_path": "Topic > Subtopic",
      "chunk_id": "chunk_123",
      "reason": "内容主题重合，且当前笔记缺少该概念回链"
    }
  ],
  "patch_ops": [
    {
      "op": "merge_frontmatter",
      "payload": {
        "tags_add": ["langgraph", "knowledge-governance"]
      }
    },
    {
      "op": "insert_under_heading",
      "payload": {
        "heading_path": "Summary",
        "text": "- Related: [[related-note]]"
      }
    }
  ],
  "safety_checks": {
    "before_hash": "sha256:xxx",
    "max_changed_lines": 30,
    "contains_delete": false
  }
}
```

为什么要这样设计：

- 结构化 proposal 才能做 schema 校验、diff 预览、审批恢复和自动评估。
- 如果 proposal 只是自然语言，用户能看懂，但系统无法安全执行。

### 7.4 diff 预览怎么组织

diff 面板至少展示：

1. 文件路径和变更摘要。
2. 风险等级。
3. 证据来源列表。
4. frontmatter diff。
5. 正文 diff。
6. “为什么建议这样改”的说明。

首版不追求复杂 merge UI，但必须做到用户能看懂“改了哪里、为什么改、依据是什么”。

#### 7.3.1 note path contract

- 所有跨边界、可持久化、可审计的 note path 字段一律使用 `vault-relative`，例如 `target_note_path`、`patch_ops.target_path`、`evidence.source_path` 与 retrieval/context evidence 的 `source_path`。
- 后端与插件的输入层可以兼容“位于当前 vault 内的真实绝对路径”，但一旦进入 proposal、writeback、API 返回、audit 或持久化边界，就必须先归一化为 canonical `vault-relative`。
- `/vault/...` 只作为历史迁移格式保留，不再是正常执行路径可接受的正式 contract；新代码、新 fixture 与新 API payload 都不应继续写出这种伪绝对路径。
- 运行时真正访问文件时，再由适配层把 `vault-relative` 解析回当前机器上的真实绝对路径；业务层不直接持久化机器相关路径。

### 7.5 frontmatter 写回怎么做

- 由后端生成结构化操作，不直接拼整段 YAML。
- 插件侧使用 Obsidian 官方 API 的 frontmatter 处理能力做原子修改。
- 必须保留未知字段，不得整体覆盖。
- 对数组字段执行 merge 而不是 replace，除非用户明确同意覆盖。

### 7.6 正文 patch 写回怎么做

- 首版只支持少数明确操作：
  - 在指定 heading 下插入文本。
  - 在文末追加总结或行动项块。
  - 替换系统自己之前生成的标记块。
- 首版不支持自由删除、跨段重排、自动重写整篇笔记。
- 每个 patch op 都要带目标路径、定位信息、预期前置 hash。

### 7.7 如何避免误删与破坏性修改

1. 默认禁止删除用户原始正文，只允许追加或替换系统托管区域。
2. 写回前校验 `before_hash`。
3. 限制单次最大改动行数和最大 patch op 数。
4. 包含删除动作时强制更高风险等级和额外确认。
5. 所有高风险修改先写草稿预览，不直接应用。

### 7.8 审批拒绝后如何处理

- 记录拒绝原因。
- 不写回文件。
- 保留 proposal 供后续编辑或重试。
- 如果用户只是不接受部分变更，支持未来引入“部分应用”的增量功能，但首版可不做。

### 7.9 审计日志结构

| 字段 | 说明 |
| --- | --- |
| `audit_event_id` | 审计主键 |
| `thread_id` | 对应工作流线程 |
| `proposal_id` | 对应 proposal |
| `action_type` | ingest / digest / ask |
| `target_note_path` | 影响的 note |
| `approval_required` | 是否经过审批 |
| `approval_decision` | approve / reject / edited |
| `before_hash` | 写回前 hash |
| `after_hash` | 写回后 hash |
| `patch_ops` | 实际应用的操作 |
| `retrieved_chunk_ids` | 这次建议依赖了哪些证据 |
| `model_info` | 使用的模型与版本 |
| `latency_ms` | 端到端耗时 |
| `error` | 错误详情 |

### 7.10 如何支持回滚 / 撤销

当前已落地最小 rollback，但边界刻意保守：

- 插件只对“当前会话里亲手执行的真实写回”抓 `LocalRollbackContext` 快照，不对历史 / 推断为已应用的 writeback 硬造 rollback。
- rollback 前必须命中精确 `after_hash`；一旦文件已被用户继续修改，就直接拒绝撤销，而不是尝试智能 merge。
- `POST /workflows/rollback` 会把 rollback 成功 / 失败都记入 append-only `audit_log`，但只有成功 rollback 才会更新 checkpoint，避免失败尝试污染最终状态。
- 当前 rollback 仍是本地整文快照恢复，不支持跨多文件事务、自由文本 patch 自动逆推或跨会话 completed history。
- rollback 成功后的 scoped ingest 刷新尚未补齐，因此“Vault 已恢复、索引仍暂时陈旧”仍是现阶段真实边界。

### 7.11 关键问题直接回答

#### 为什么不能让 LLM 直接改文件

- LLM 输出不稳定，天然不适合直接作为文件系统写入源。
- 直接改文件意味着没有结构化审计、没有 idempotency、没有 diff 边界。

#### 为什么 patch 应由后端生成、插件执行

- 后端更适合做分析、约束和 patch 生成。
- 插件更适合贴近 Obsidian API 和用户交互，便于审批和原子写回。
- 这样职责清晰：后端负责“决定改什么”，插件负责“在用户许可下怎么安全地改”。

#### 为什么 interrupt 位置很关键

- 如果把 interrupt 放在含副作用的节点中间，恢复时很容易重复执行前半段逻辑。
- 审批必须是纯控制节点，前后副作用分离。

#### 恢复执行时副作用重复怎么办

- 依赖 `proposal_id`、`idempotency_key`、`before_hash`、`writeback_applied` 标志。
- 恢复时先查审计表和当前文件摘要，再决定是否真的执行 patch。

### 7.12 当前关键假设、风险、待确认与后续行动

| 类型 | 内容 |
| --- | --- |
| Assumption | 首版只允许低复杂度 patch op，不支持任意自由编辑。 |
| Risk | 如果过早支持复杂 patch，会直接把项目拖进“写回正确性地狱”。 |
| Open Question | 用户是否接受“部分变更应用”和“草稿先写到单独文件”的交互方式。 |
| Next Action | `TASK-030`、`TASK-040`、`TASK-041` 与 `TASK-042` 已完成；写回侧当前剩余主线不再是索引一致性、rollback 兜底、benchmark 收口或 workflow contract 收敛，而是回到跨会话恢复 `TASK-031`、scoped ingest 增量 FTS `TASK-032` 与 post-rollback scoped ingest 等后移 backlog。 |

## 8. 可观测性、日志与评估闭环

### 8.1 tracing 设计

| 维度 | 采集内容 | 用途 |
| --- | --- | --- |
| 节点耗时 | 每个 graph node 的 start/end/duration | 定位瓶颈 |
| 模型耗时 | 每次模型调用的 latency、token 数、模型名 | 评估成本与稳定性 |
| token 消耗 | prompt / completion token | 成本分析与路由决策 |
| 检索命中内容 | chunk_id、path、score、retrieval source | 回溯结果依据 |
| proposal 生成链路 | 使用了哪些 evidence、输出了哪些 patch op | 解释写回原因 |
| 审批决策 | 审批结果、人工备注、耗时 | 看用户是否信任系统 |
| 写回结果 | before/after hash、成功失败、变更摘要 | 审计与回滚 |

首版 tracing 输出建议：

- 一个结构化 JSONL 文件用于本地调试。
- 一个 SQLite `run_trace` 表用于聚合查询。
- 如后续启用 LangSmith，可作为可视化加分项，但不是 P0 依赖。

当前代码事实：

- ask / ingest 路径已经通过 [backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py) 同时落地 `data/traces/ask_runtime.jsonl` 与 SQLite `run_trace` 聚合，每次 ask / ingest graph 执行都会默认双写两条持久化路径。
- 当前已支持按 `run_id` 或 `thread_id` 做最小 `run_trace` 查询，避免 trace 长期停留在“能写但不好查”的状态。
- 单个 trace sink 写入失败会降级为其他 sink、内存态 `trace_events` 和外部 hook 继续执行，不会阻断 ask / ingest 主链路。
- 多 graph tracing、更细粒度 latency / token 指标、断流发现与轮转治理仍未实现。

### 8.2 日志设计

| 日志类型 | 记录内容 | 存储位置 | 保留策略 |
| --- | --- | --- | --- |
| 运行日志 | API 请求、节点开始结束、普通状态 | `logs/runtime.jsonl` 或 SQLite | 最近 30 天 |
| 审计日志 | proposal、审批、写回结果、证据来源 | SQLite `audit_log` | 长期保留 |
| 错误日志 | 异常堆栈、失败节点、请求上下文 | `logs/error.jsonl` | 长期保留 |
| 评估结果日志 | 每次 benchmark 的指标和版本 | `eval/results/*.json` | 长期保留 |

### 8.3 Eval 设计

#### golden dataset 的结构

```json
{
  "sample_id": "qa_001",
  "scenario": "ASK_QA",
  "input": "我之前在哪写过 checkpoint 和 interrupt 的关系？",
  "expected_notes": ["notes/langgraph.md"],
  "expected_chunk_ids": ["chunk_101", "chunk_102"],
  "reference_answer": "应提到 checkpoint 持久化、interrupt 中断恢复和 thread_id 的关系",
  "risk_level": "low"
}
```

#### 样本来源

- `sample_vault/` 中的真实个人笔记抽样。
- 人工构造少量边界样本，如重名概念、代码块、表格、冲突笔记。
- 每次功能开发后新增坏例样本，防止回归。

#### 样本分类

- `ASK_QA`
- `INGEST_STEWARD_DUPLICATE`
- `INGEST_STEWARD_CONFLICT`
- `INGEST_STEWARD_TAG_LINK`
- `DAILY_DIGEST`
- `WRITEBACK_SAFETY`

#### RAG 评估指标

- Recall@K / Context Recall
- Precision@K / Context Precision
- Citation accuracy
- Faithfulness
- Answer relevance

#### proposal / writeback 类功能如何评估

- proposal schema 合法率。
- 审批通过率与拒绝原因分布。
- patch 应用成功率。
- 错误写回率。
- 人工抽样“建议是否合理、证据是否充分、修改是否过度”。

#### 哪些内容自动评估，哪些必须人工抽样

自动评估：

- 检索 recall / precision。
- schema 合法率。
- patch 应用成功率。
- 节点耗时与失败率。

人工抽样：

- 冲突检测是否合理。
- 标签和双链建议是否“像人写的”。
- 复盘草稿是否真正抓到重点。
- 高风险 proposal 是否保守。

### 8.4 当前可实现的最小 Eval 方案

当前仓库已经有真实代码、真实 `sample_vault/` 与最小离线 `run_eval.py`，因此首个最小 Eval 方案已先落成以下 baseline：

1. 先用 23 条样本把 ask / governance / digest / resume-writeback 四类核心场景打成统一 baseline，再进一步收敛成 `question_answering / governance` 两套 benchmark，不强行追求一次性做满 benchmark 平台。
2. 样本继续混合真实 `sample_vault` 场景和 deterministic fixture bad case，并为 hybrid retrieval 加入 prewarm ingest 与 embedding mock，避免回归只覆盖 FTS fallback。
3. 当前结果 schema 已升级到 `1.3`，除 workflow status、fallback 信号、citation / proposal 结构外，还会输出最小 `quality_metrics`、全局 `metric_overview`、`question_answering / governance` 两套 `benchmark_overview`、场景级 `core_metrics` 与最小 `failure_type_breakdown`；其中 faithfulness 已由共享 claim-level semantic report 驱动，governance / digest 不再直接退回 `context_recall` 充当替代指标。
4. proposal / writeback 质量仍保留人工抽样和结构化断言，不急着把本轮扩成在线 judge 或复杂 dashboard。
5. 每次执行至少保证产出一份带时间戳的 `eval/results/*.json`，并能稳定复现 governance / hybrid 的代表坏路径。

### 8.5 面试追问点（至少 10 个）

| 问题 | 回答要点 |
| --- | --- |
| 你怎么证明系统不是“看起来能用” | 用 golden set、回归脚本、审计日志和 tracing 指标，而不是只看 Demo。 |
| 检索指标和生成指标为什么都要有 | 检索命中不代表答案忠实；答案流畅也不代表证据充分。 |
| proposal 怎么评估 | 看 schema 合法率、审批通过率、人工抽样正确性和最终写回错误率。 |
| 为什么要单独做审计日志 | 普通运行日志无法回答“改了什么、为什么改、谁批准的、能不能回滚”。 |
| 复盘质量如何量化 | 首版以人工抽样为主，辅以结构指标，如是否提到高频主题、开放问题和行动项。 |
| tracing 最关键的字段是什么 | 节点耗时、模型耗时、检索证据和写回结果。没有这些就无法定位问题。 |
| 如果指标变差，你怎么定位 | 先看检索，再看 rerank，再看生成 prompt 和写回约束；别一上来怪模型。 |
| 为什么不一开始就接入 LangSmith | 可以接，但不是 P0 阻塞项；本地 JSONL 和 SQLite trace 更便于先跑通。 |
| 为什么要同时保留 JSONL 和 SQLite `run_trace` | JSONL 适合原始事件留存和抽样排障，SQLite 适合按 `run_id` / `thread_id` 聚合查询；两者职责不同，但后续要治理双写一致性和膨胀问题。 |
| 你怎么区分模型问题和系统问题 | 模型问题表现为同输入高波动；系统问题表现为检索缺证据、状态丢失、trace 断流、写回错位等可观测症状。 |
| 为什么要给高风险链路单独评估 | 因为出错成本最高，不能用问答链路的“差一点也能用”标准来衡量。 |

### 8.6 当前关键假设、风险、待确认与后续行动

| 类型 | 内容 |
| --- | --- |
| Assumption | 首版允许评估以离线脚本为主，不强依赖复杂平台。 |
| Risk | `sample_vault/` 如果主要是日常工作记录，可能不足以覆盖更泛化的知识卡片场景。 |
| Open Question | 后续是否还会补充“概念笔记 / 技术总结 / 主题卡片”类型样本。 |
| Next Action | 在 23 条样本、governance suite、`schema_version=1.3`、`quality_metrics`、`metric_overview`、`benchmark_overview`、最小 `failure_type_breakdown`、rollback、统一 workflow contract、`TASK-047` 的 ask 装配回归、`TASK-046` 的 graph-only ReAct 循环、`TASK-049` 的 Structured Tool Calling、`TASK-050` 的 ask runtime faithfulness 首刀、`TASK-051` 的共享 claim-level semantic faithfulness core、`TASK-052` 的 ask / digest runtime semantic gate、`TASK-053` 的 ask 四维度离线基线与 `TASK-054` 的 governance / digest 场景化指标都已补齐的基础上，评估侧的 umbrella 已收口；若继续推进 medium，则默认回到已后移的 `TASK-031`，随后进入 `TASK-032`，`TASK-033` 已被 `TASK-050` / `TASK-052` 吸收。 |

## 9. 模块级详细说明（面试拷打版）

> 说明：以下“核心文件路径”中，凡标记“建议落位”的，当前仓库均不存在。若某模块已有基线文件，则以“当前已存在”优先标注；这部分的价值是同时维护责任边界和真实实现状态，防止后续开发时职责漂移。

### 9.1 Obsidian 插件入口层

- 模块职责：提供命令入口、侧边栏视图、设置页、与后端通信、审批 UI、最终写回执行。
- 核心文件路径：当前已存在 `plugin/src/main.ts`、`plugin/src/views/KnowledgeStewardView.ts`、`plugin/src/settings.ts`、`plugin/src/api/client.ts`。
- 上下游依赖：上游是用户操作和 Obsidian API；下游是本地后端 HTTP 接口。
- 关键类 / 函数 / 数据结构：`KnowledgeStewardPlugin`、`activateView()`、`pingBackend()`、`KnowledgeStewardApiClient`。
- 为什么要有这个模块：没有插件入口，项目就不能嵌入 Obsidian 的日常使用流。
- 如果删掉它会怎样：系统只能剩后端脚本，无法完成面向 Obsidian 的真实交互与安全写回。
- 容易出 bug 的地方：状态和 UI 不同步、活动文件变化、后端断开、审批后重复提交。
- 可替代实现：纯命令面板、纯 modal、纯 chat view；但侧边栏更适合展示 proposal 和 diff。
- 当前版本是否稳定：部分实现。插件已支持 panel 打开、设置保存、`/health` 探活、用户提供启动命令后的最小 backend 自启 / auto-start / 状态展示、pending inbox 刷新、真实 `DAILY_DIGEST` proposal 加载、审批提交以及审批通过后的受限本地写回；但 freshness 提示、插件 ask UI、Stop/Restart 控制与跨会话恢复入口仍未实现。
- 面试官会怎么问：为什么不直接用现成聊天面板承载全部交互。
- 如何回答：聊天面板更适合问答，不适合高风险审批和结构化 diff；治理项目的主视图应该以 workflow 和 proposal 为中心。

### 9.2 Vault 读写层

- 模块职责：读取 note、获取当前文件、处理 frontmatter、应用受限 patch。
- 核心文件路径：当前已存在 `plugin/src/writeback/applyProposalWriteback.ts`、`plugin/src/writeback/helpers.ts`；如后续继续扩展，可再抽到 `plugin/src/vault/vaultService.ts`、`plugin/src/vault/frontmatterService.ts`。
- 上下游依赖：上游是审批结果；下游是 Obsidian Vault / FileManager API。
- 关键类 / 函数 / 数据结构：`readNote(path)`、`applyPatchOps(ops)`、`mergeFrontmatter()`、`WritebackResult`。
- 为什么要有这个模块：读写是高风险区域，必须从 UI 和后端逻辑中剥离，单独约束。
- 如果删掉它会怎样：写回逻辑会散落在多个地方，无法证明安全边界。
- 容易出 bug 的地方：frontmatter 覆盖、定位错位、文件在审批期间被用户修改。
- 可替代实现：后端直接改文件系统；不推荐，因为审计和权限边界会变糊。
- 当前版本是否稳定：部分实现。已支持按 `proposal.patch_ops` 执行受限写回，覆盖 `merge_frontmatter`（兼容历史别名 `frontmatter_merge`）、`insert_under_heading`、`replace_section` 与 `add_wikilink` 四类操作，并在写回前校验 `before_hash`；proposal 持久化校验也已正式支持这四类 op，并对 `add_wikilink` 施加 vault 内 existing-note 约束；但路径语义统一、跨会话恢复与更完整 patch 能力仍未完成。
- 面试官会怎么问：为什么不让后端直接对 markdown 文件打 patch。
- 如何回答：后端生成 patch，插件执行写回，能同时满足安全、交互、API 兼容和审计边界。

### 9.3 Metadata 解析层

- 模块职责：解析 frontmatter、headings、links、block refs、tables、code blocks。
- 核心文件路径：当前已存在 `backend/app/indexing/parser.py`、`backend/app/indexing/models.py`。
- 上下游依赖：上游是 ingest pipeline；下游是索引构建和治理分析。
- 关键类 / 函数 / 数据结构：`ParsedNote`、`HeadingInfo`、`NoteChunk`、`parse_markdown_note()`。
- 为什么要有这个模块：检索和治理的质量上限，很大程度取决于结构解析是否靠谱。
- 如果删掉它会怎样：只能做粗暴全文检索，无法支持 heading 级引用、frontmatter 写回和孤立检测。
- 容易出 bug 的地方：复杂 Markdown、非法 YAML、嵌套列表、未闭合代码块、模板推断过拟合。
- 可替代实现：全靠 Obsidian MetadataCache；但后端仍需要一份可离线运行的解析能力。
- 当前版本是否稳定：部分实现。已支持 heading、wikilink、任务复选框与 `daily_note / summary_note` 推断，未支持 block ref、table、code block 和 frontmatter 深解析。
- 面试官会怎么问：为什么不只用文件名和全文。
- 如何回答：因为治理动作依赖结构位置，不解析结构就无法安全落 patch。

当前实现补充：

- 输入：`Path` 指向的 Markdown 文件。
- 输出：`ParsedNote`，包含 `note_type`、`template_family`、`heading_path`、chunks、任务数和 wikilinks。
- 失败模式：UTF-8 读取失败、标题识别偏差、模板误判、超长 section 导致 chunk 过大。
- fallback：保持 `generic_note` 分类，按原始 note body 输出单块，不阻塞后续索引。
- eval 方法：对 `sample_vault` 抽样检查 `daily_cn_template / daily_en_template / summary_note` 分类准确率，以及 heading_path 与任务数统计是否正确。
- 面试追问点：为什么首版用模板推断 `note_type`，而不是等待 frontmatter 补全后再做。

### 9.4 索引构建层

- 模块职责：chunking、embedding、FTS、增量更新、索引脏标记。
- 核心文件路径：当前已有 `backend/app/indexing/store.py`、`backend/app/indexing/ingest.py`；后续继续补 `backend/app/indexing/chunker.py`。
- 上下游依赖：上游是解析层；下游是 retrieval 和评估。
- 关键类 / 函数 / 数据结构：`NoteRecord`、`ChunkRecord`、`build_note_record()`、`build_chunk_records()`、`initialize_index_db()`、`sync_note_and_chunks()`、`ingest_vault()`。
- 为什么要有这个模块：检索和治理都依赖它，是整个系统的底层基础设施。
- 如果删掉它会怎样：问答和治理都只能临时扫文件，性能和质量都不可接受。
- 容易出 bug 的地方：增量索引重复、删除文件后旧索引残留、chunk 元数据与原文不一致。
- 可替代实现：每次现查现算；不现实。
- 当前版本是否稳定：部分实现。已落 schema migration、record mapping、全量 ingest、note 级 replace/upsert、FTS 重建入口和 CLI；未实现增量更新、dirty mark 与 FTS 漂移检测。
- 面试官会怎么问：为什么先做索引，不直接做问答。
- 如何回答：没有索引，任何后续质量、性能、评估与可观测都无从谈起。

### 9.5 检索层

- 模块职责：metadata filter、FTS、vector、fusion、candidate 输出。
- 核心文件路径：当前已有 `backend/app/retrieval/sqlite_fts.py`、`backend/app/retrieval/embeddings.py`、`backend/app/retrieval/sqlite_vector.py`、`backend/app/retrieval/hybrid.py`、`backend/app/contracts/workflow.py`；后续继续补 `backend/app/retrieval/rerank.py`。
- 上下游依赖：上游是用户 query 或治理上下文；下游是 rerank 和 generation。
- 关键类 / 函数 / 数据结构：`RetrievalMetadataFilter`、`RetrievedChunkCandidate`、`RetrievalSearchResponse`、`search_chunks()`、`search_chunks_in_db()`、`search_chunk_vectors()`、`embed_texts()`。
- 为什么要有这个模块：Obsidian 语料的相关性判断不能全交给 LLM。
- 如果删掉它会怎样：graph 会退化成“读一篇当前笔记 + 模型猜建议”，完全不可信。
- 容易出 bug 的地方：融合策略不稳、过滤过严、短文本误召回。
- 可替代实现：只用一个检索器；质量不稳。
- 当前版本是否稳定：部分实现。已落 SQLite FTS5 top-k candidate、metadata filter、filter fallback、`chunk_embedding` 持久化、最小向量检索、RRF hybrid retrieval，并由 `backend/app/services/ask.py` 与 `backend/app/services/ingest_proposal.py` 复用统一 candidate 输出；仍未实现 rerank、更强的 answer grounding 校验与 hybrid branch 调试快照 / coverage 观测。
- 面试官会怎么问：为什么把 filter 放在 SQL 阶段；为什么 retrieval fallback 和 model fallback 要分开；为什么向量检索要显式区分“provider 不可用”“索引未就绪”和“真的没召回”；为什么这轮先用 RRF 而不是硬做线性加权或直接上 rerank。
- 如何回答：因为要避免先截断 top-k 再过滤造成 recall 假象，同时把“检索过严”“模型不可用”“向量能力当前不可用”拆成不同的可观测降级面；当前先用 rank-based RRF 收敛共享 candidate 底座，避免在分数量纲还没校准时把会话扩成调参问题。`TASK-040` 已把问答 vs 治理的 benchmark 切开，`TASK-041` 已补齐最小 rollback，`TASK-042` 也已完成 workflow contract 收口；接下来是否值得继续上 rerank 或更复杂的融合，应该由 benchmark 与调试观测决定，而不是再靠直觉加料。

### 9.6 rerank 层

- 模块职责：对 candidate 进行精排，提升前排相关性。
- 核心文件路径：当前无；建议落位 `backend/app/retrieval/rerank.py`。
- 上下游依赖：上游是 hybrid retrieval；下游是 answer / proposal 生成。
- 关键类 / 函数 / 数据结构：`rerank_candidates()`、`RerankConfig`。
- 为什么要有这个模块：混合检索的 top-k 往往包含“相关但顺序不优”的结果，治理场景很吃前排质量。
- 如果删掉它会怎样：答案和 proposal 仍能工作，但质量和可解释性会明显差。
- 容易出 bug 的地方：延迟高、batch 处理不稳定、模型不可用。
- 可替代实现：不做 rerank 或让 LLM 重新排序；前者质量差，后者成本高。
- 当前版本是否稳定：未实现。
- 面试官会怎么问：什么时候应该把 rerank 关掉。
- 如何回答：在延迟预算紧、候选本来很准或本地设备很弱时要关；这需要指标支持。

### 9.7 LangGraph 工作流层

- 模块职责：定义 state、nodes、edges、interrupt、checkpoint、恢复协议。
- 核心文件路径：当前已存在 `backend/app/graphs/state.py`、`backend/app/graphs/runtime.py`、`backend/app/graphs/checkpoint.py`、`backend/app/graphs/__init__.py`、`backend/app/graphs/ask_graph.py`、`backend/app/graphs/ingest_graph.py`、`backend/app/graphs/digest_graph.py`。
- 上下游依赖：上游是 API 层；下游调用 retrieval、proposal、logging 等服务。
- 关键类 / 函数 / 数据结构：`StewardState`、`open_sqlite_checkpointer()`、`invoke_checkpointed_compiled_graph()`、`PersistedGraphCheckpoint`、`resume_workflow()`。
- 为什么要有这个模块：这是项目与普通 RAG 系统拉开差距的关键。
- 如果删掉它会怎样：审批、恢复、复盘和多场景路由都会变成临时 if-else 泥球。
- 容易出 bug 的地方：状态字段漂移、中断恢复重复执行、副作用节点不幂等。
- 可替代实现：自写状态机；但两周内不如 LangGraph 稳。
- 当前版本是否稳定：部分实现。`StewardState`、共享 graph runtime、ask / ingest / digest graph、SQLite checkpoint、`waiting_for_approval` 状态与 `/workflows/resume` 控制面已落地；其中 `DAILY_DIGEST` 与 `INGEST_STEWARD` 都已接入 graph 级 waiting proposal 节点，但 ask waiting、ingest richer proposal 路径与细粒度 interrupt 仍未实现。
- 面试官会怎么问：为什么不用简单函数链。
- 如何回答：因为需要中断、恢复、线程状态与 checkpoint，这超出了简单函数链的舒适区。

### 9.8 HITL 审批层

- 模块职责：展示 proposal、收集用户批准/拒绝/备注、恢复 graph。
- 核心文件路径：当前后端已存在 `backend/app/contracts/workflow.py`、`backend/app/services/resume_workflow.py`、`backend/app/graphs/checkpoint.py`、`backend/app/graphs/digest_graph.py`、`backend/app/services/digest.py`、`backend/app/graphs/ingest_graph.py` 与 `backend/app/services/ingest_proposal.py`；插件侧当前已落 [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts) 与 [plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts) 中的审批面板、pending inbox、真实 `DAILY_DIGEST` proposal 加载命令与 demo fallback，后续可再抽到 `plugin/src/approval/ApprovalPanel.ts`。
- 上下游依赖：上游是 proposal 节点；下游是写回节点。
- 关键类 / 函数 / 数据结构：`WorkflowResumeRequest`、`ApprovalDecision`、`resume_workflow()`。
- 为什么要有这个模块：这是系统可信度的第一道门。
- 如果删掉它会怎样：所有写回安全、审计、面试叙事都会坍塌。
- 容易出 bug 的地方：审批版本过期、UI 展示和实际 patch 不一致、重复提交。
- 可替代实现：命令行审批；可用于开发期，但不适合最终演示。
- 当前版本是否稳定：部分实现。后端审批恢复协议、append-only audit 记录、checkpoint 状态推进、`writeback_result` 持久化与 pending approval 查询接口已落地，插件审批面板、最小 diff 展示、pending inbox、人工 approve / reject 交互以及审批通过后的最小本地写回也已落地；但 freshness 治理、多 workflow proposal 化和跨会话恢复入口仍未实现。
- 面试官会怎么问：为什么不做“自动通过低风险修改”。
- 如何回答：可以做，但首版先保守，先把风险界限和审计链路打稳。

### 9.9 patch / writeback 层

- 模块职责：把 proposal 转成受限 patch op，并应用到具体 note。
- 核心文件路径：当前已有 `backend/app/contracts/workflow.py`、`backend/app/graphs/state.py`、`backend/app/indexing/store.py` 中的 proposal / patch / audit contract 与 SQLite schema，以及 `plugin/src/writeback/applyProposalWriteback.ts`、`plugin/src/writeback/helpers.ts`；后续可再补 `backend/app/writeback/patch_builder.py` 做更完整 builder 抽象。
- 上下游依赖：上游是审批层；下游是 Vault API。
- 关键类 / 函数 / 数据结构：`PatchOp`、`PatchPlan`、`applyPatchOps()`。
- 为什么要有这个模块：proposal 是语义层，patch 是执行层，这两者必须分离。
- 如果删掉它会怎样：后端输出无法稳定落地，或者插件只能整篇覆盖。
- 容易出 bug 的地方：定位偏移、前置内容不一致、系统块标记丢失。
- 可替代实现：整篇全文替换；非常危险。
- 当前版本是否稳定：部分实现。`PatchOp`、`Proposal`、`AuditEvent` contract 和 SQLite `proposal` / `patch_op` / `audit_log` schema 已落地，插件侧也已有最小执行器与真实 `before_hash` 校验；但 patch builder 仍较轻量，写回后增量 ingest、跨会话恢复与更多 patch op 仍未实现。
- 面试官会怎么问：为什么不直接让 LLM 输出新全文。
- 如何回答：那样无法做局部审计、局部回滚和幂等控制，风险不可接受。

### 9.10 tracing / logging 层

- 模块职责：记录运行链路、节点耗时、错误、审计和评估结果。
- 核心文件路径：当前共享 trace event 追加逻辑位于 `backend/app/graphs/runtime.py`，ask / ingest 侧 graph 位于 `backend/app/graphs/ask_graph.py` 与 `backend/app/graphs/ingest_graph.py`，JSONL 与 SQLite `run_trace` 持久化及最小查询入口位于 `backend/app/observability/runtime_trace.py`；建议后续补更完整的 `backend/app/observability/tracer.py`、`backend/app/observability/logger.py`。
- 上下游依赖：所有模块都会调用它。
- 关键类 / 函数 / 数据结构：`TraceEvent`、`AuditEvent`、`log_node_event()`。
- 为什么要有这个模块：没有可观测，就没有可调试、可复现、可辩护。
- 如果删掉它会怎样：面试官一问性能、质量、失败定位，你只能靠主观描述。
- 容易出 bug 的地方：日志量过大、隐私泄漏、字段不一致。
- 可替代实现：只打 console log；不够。
- 当前版本是否稳定：起步实现。ask / ingest graph 已能发出 runtime trace event，并默认双写 JSONL 与 SQLite `run_trace`，支持按 `run_id` / `thread_id` 最小查询；但尚未补更细粒度事件、多 graph trace 治理、断流治理和更完整的 tracer/logger 模块。
- 面试官会怎么问：trace 和 audit 的区别是什么。
- 如何回答：trace 关注过程，audit 关注副作用和责任归属。
- 面试官还会怎么追问：为什么要同时保留 JSONL 和 SQLite `run_trace`，而不是二选一。
- 如何回答：JSONL 负责原始事件留存与抽样排障，SQLite 负责结构化查询与聚合分析；首版双写是工程折中，不是最终形态。

### 9.11 eval 层

- 模块职责：维护 golden set、执行 benchmark、产出回归结果。
- 核心文件路径：当前已存在 `eval/README.md`、`eval/golden/ask_cases.json`、`eval/golden/digest_cases.json`、`eval/results/`、`eval/run_eval.py`。
- 上下游依赖：上游是索引、检索、工作流；下游是路线图和调参。
- 关键类 / 函数 / 数据结构：`GoldenSample`、`EvalReport`、`run_eval()`。
- 为什么要有这个模块：项目目标里已经写明“可评估”，不做 eval 等于自毁卖点。
- 如果删掉它会怎样：只能靠 Demo，无法支撑工程可信度。
- 容易出 bug 的地方：样本太少、答案标准过于主观、不同场景指标混用。
- 可替代实现：完全手工评估；只能短期过渡。
- 当前版本是否稳定：部分实现。已能执行 ask / governance / digest / `resume_workflow` 的最小 golden 回归、按 `case_id` 过滤执行并生成 `eval/results/*.json`；ask 已稳定输出四维度离线指标，governance 已输出 `rationale_faithfulness / patch_safety`，digest 已输出 `faithfulness / coverage`，benchmark overview 也能按实际 metric key 聚合；但样本规模、事实级 coverage 标注、宿主级验证和长期样本治理仍未完成。
- 面试官会怎么问：proposal 这种结构化建议怎么评估。
- 如何回答：自动评 schema 和写回成功率，人审评建议合理性和风险控制。

### 9.12 配置与模型路由层

- 模块职责：统一管理模型、embedding、rerank、路径、开关和预算策略。
- 核心文件路径：当前已存在 `backend/app/config.py`、`backend/.env.example`，插件侧配置已落在 `plugin/src/settings.ts`。
- 运行时环境定义：当前已存在 `backend/environment.yml`，作为唯一推荐的后端开发环境清单。
- 上下游依赖：几乎所有后端模块。
- 关键类 / 函数 / 数据结构：`Settings`、`get_settings()`、`KnowledgeStewardSettings`、`DEFAULT_SETTINGS`。
- 为什么要有这个模块：没有统一配置，开发期很快会充满硬编码。
- 如果删掉它会怎样：模型、索引和调试参数散落，难以复现。
- 容易出 bug 的地方：环境变量不一致、本地和生产配置混淆、功能开关失控。
- 可替代实现：模块内硬编码；不可接受。
- 当前版本是否稳定：部分实现。已能描述 cloud-primary / local-compatible 路线、端口和样本路径，并支撑 ask 场景的最小 provider 选择与 `KS_CLOUD_API_KEY` 读取；还没有真正的 provider 探活、秘钥校验和更强的响应约束逻辑。
- 面试官会怎么问：为什么需要模型路由。
- 如何回答：不同场景的质量、延迟和成本约束不同，复盘、治理和问答不应该共用一套固定模型策略。

### 9.13 后端 API / 协议层

- 模块职责：固化插件与后端之间的最小 contract，提供 `/health` 与 `/workflows/invoke` 的统一入口。
- 核心文件路径：`backend/app/main.py`、`backend/app/contracts/workflow.py`。
- 上下游依赖：上游是插件 API 客户端；下游是未来的 graph、索引和写回服务。
- 关键类 / 函数 / 数据结构：`HealthResponse`、`WorkflowInvokeRequest`、`WorkflowInvokeResponse`、`AskWorkflowResult`、`AskCitation`、`IngestWorkflowResult`、`DigestWorkflowResult`、`Proposal`、`PatchOp`、`ApprovalDecision`。
- 为什么要有这个模块：如果协议不先收敛，插件和后端会在开发过程中各自长出一套临时字段，后面很难做审批、恢复和评估。
- 如果删掉它会怎样：插件只能和后端传自由 JSON，无法保证版本兼容和状态恢复的可演进性。
- 当前版本是否稳定：部分实现。`/health` 已通过本地 conda 环境验证，`/workflows/invoke` 已支持 `ask_qa` 返回真实 `ask_result`、citations 与 retrieval/model fallback，支持 `ingest_steward` 返回真实 `ingest_result`，并支持 `daily_digest` 返回最小 `digest_result`、`source_notes` 与安全 fallback。
- 输入：健康检查无输入；workflow 调用接收 `action_type`、`thread_id`、`note_path`、`user_query`、`provider_preference`、`retrieval_filter` 等字段。
- 输出：`/health` 返回服务状态、provider 描述和 `sample_vault` 统计；`/workflows/invoke` 返回 `run_id`、`thread_id`、`status`、`approval_required`，在 `ask_qa` 场景下返回 `ask_result`，在 `ingest_steward` 场景下返回 `ingest_result`，在 `daily_digest` 场景下返回 `digest_result` 与 `source_notes`。
- 失败模式：字段漂移、插件与后端版本不兼容、ask 结果结构变动、ingest / digest scope 语义模糊、provider 自由文本没有引用、digest 来源选择失真、未实现 action 被误认为完成。
- fallback：对 `ask_qa`，模型不可用时返回 `retrieval_only`，无检索命中时返回 `no_hits`；对 `ingest_steward`，当前对未支持的 partial scope 明确返回 400；对 `daily_digest`，索引为空时返回安全 fallback，当前对未支持的 scoped digest 明确返回 400；对仍未实现的 workflow 继续明确返回 `not_implemented`；健康检查最少返回服务名、版本和错误信息。
- eval 方法：使用 `TestClient` 对 `/health` 与 `/workflows/invoke` 做 contract test，校验 ask / ingest 结果字段、fallback 语义和样本统计。
- 面试追问点：
  - 为什么在真正实现 graph 前先写协议层。
  - 为什么 `/health` 要返回 `sample_vault` 统计，而不是只返回 `ok`。
  - 为什么 ask 先接在 `/workflows/invoke`，而不是独立新建 `/ask`。
  - 为什么 `Proposal` 和 `PatchOp` 要先进入 contract，而不是等写回实现时再补。

## 10. 开发路线图（可执行步骤）

### 10.1 总阶段

| 阶段 | 名称 | 目标 | 当前状态 |
| --- | --- | --- | --- |
| Phase 0 | 基线建立 | 从空仓变成有目录、有依赖、有文档、有最小运行链路 | `已完成` |
| Phase 1 | 插件与后端壳 | 跑通 Obsidian 插件和本地后端通信 | `进行中` |
| Phase 2 | 索引与检索成型 | 跑通 ingest、索引、hybrid retrieval、最小问答 | `已完成` |
| Phase 3 | LangGraph 工作流接入 | 跑通 ingest / ask / digest 三条 graph 链路 | `进行中` |
| Phase 4 | HITL 与写回 | 接入 proposal、审批、diff、受限 patch 写回 | `进行中` |
| Phase 5 | 观测、评估与演示 | 建立 tracing、audit、eval、demo 脚本和面试材料 | `进行中` |

### 10.2 各阶段执行细项

#### 10.2.1 Phase 0：基线建立

- 目标：建立目录结构、依赖清单、主文档、开发脚本和空实现。
- 输入条件：当前空仓，只有本主文档与初步实现指南。
- 输出产物：
  - `docs/PROJECT_MASTER_PLAN.md`
  - `README.md`
  - `plugin/` 目录骨架
  - `backend/` 目录骨架
  - `eval/` 与 `data/` 目录
- 具体子任务：
  - 新建 `docs/PROJECT_MASTER_PLAN.md`。
  - 新建 `README.md`，简述项目目标与启动方式。
  - 新建插件目录并补 `package.json`、`manifest.json`、`tsconfig.json`。
  - 新建后端目录并补 `pyproject.toml` 或 `requirements.txt`。
  - 新建 `eval/golden/`、`eval/results/`、`data/` 目录。
  - 新建 `.gitignore`。
- 依赖关系：无。
- 验收标准：仓库能安装依赖，目录清晰，无歧义命名。
- 风险点：过早陷入技术选型争论。
- 预计优先级：P0。

当前子任务状态：

| 子任务 | 状态 |
| --- | --- |
| 新建 `docs/PROJECT_MASTER_PLAN.md` | `已完成` |
| 新建 `README.md` | `已完成` |
| 新建插件目录并补 `package.json`、`manifest.json`、`tsconfig.json` | `已完成` |
| 新建后端目录并补 `pyproject.toml` 或 `requirements.txt` | `已完成` |
| 新建 `eval/golden/`、`eval/results/`、`data/` 目录 | `已完成` |
| 新建 `.gitignore` | `已完成` |
| 形成可复现依赖安装方式 | `部分完成` |
| 收敛 Python 环境策略并处理 `backend/.venv` / conda 并存问题 | `部分完成` |

#### 10.2.2 Phase 1：插件与后端壳

- 目标：跑通插件加载、后端启动、基础 API 探活。
- 输入条件：Phase 0 完成。
- 输出产物：
  - 插件能在 Obsidian Dev Vault 中加载
  - 后端能本地启动
  - 插件能调用 `/health`
- 具体子任务：
  - 跑通插件开发环境。
  - 跑通后端 dev server。
  - 实现 `GET /health`。
  - 插件设置页中增加后端地址配置。
  - 插件增加一个命令：`Open Knowledge Steward`。
  - 插件增加一个命令：`Ping Backend`。
  - 后端增加基础日志输出。
- 依赖关系：依赖 Phase 0。
- 验收标准：用户在 Obsidian 中点击命令后可看到后端健康状态。
- 风险点：插件构建配置和桌面 Dev Vault 环境。
- 预计优先级：P0。

当前子任务状态：

| 子任务 | 状态 |
| --- | --- |
| 跑通插件开发环境 | `进行中` |
| 跑通后端 dev server | `进行中` |
| 实现 `GET /health` | `已完成` |
| 插件设置页中增加后端地址配置 | `已完成` |
| 插件增加一个命令：`Open Knowledge Steward` | `已完成` |
| 插件增加一个命令：`Ping Backend` | `已完成` |
| 后端增加基础日志输出 | `未开始` |

#### 10.2.3 Phase 2：索引与检索成型

- 目标：建立最小 ingest pipeline 和可解释问答链路。
- 输入条件：插件与后端通信已打通。
- 输出产物：
  - Markdown 解析器
  - chunk 表和 note 表
  - FTS 和向量召回
  - `/ask` 或 `/ask/stream`
- 具体子任务：
  - 为 chunk 表补充 `heading_path` 字段。
  - 为 note 表补充 `tags`、`aliases`、`mtime`、`hash` 字段。
  - 实现 Markdown frontmatter / heading / link 解析。
  - 实现基础 chunking。
  - 实现 SQLite FTS5 索引。
- 接入 embedding 存储。
- 实现 metadata filter。
- 实现 hybrid retrieval。
- 接入 reranker 开关。
- 确认现有 ask 流程。
- 输出引用式问答结果。
- 依赖关系：依赖 Phase 1。
- 验收标准：能对样例 Vault 跑索引，问答结果能返回引用来源。
- 风险点：样例数据不足、embedding / rerank 环境差异。
- 预计优先级：P0。

当前子任务状态：

| 子任务 | 状态 |
| --- | --- |
| 为 chunk 表补充 `heading_path` 字段 | `已完成` |
| 为 note 表补充 `tags`、`aliases`、`mtime`、`hash` 字段 | `已完成` |
| 实现 Markdown frontmatter / heading / link 解析 | `进行中` |
| 实现基础 chunking | `进行中` |
| 实现 SQLite FTS5 索引 | `已完成` |
| 接入 embedding 存储 | `已完成` |
| 实现 metadata filter | `已完成` |
| 实现 hybrid retrieval | `已完成` |
| 接入 reranker 开关 | `未开始` |
| 确认现有 ask 流程 | `已完成` |
| 输出引用式问答结果 | `已完成` |

#### 10.2.4 Phase 3：LangGraph 工作流接入

- 目标：把 ask / ingest / digest 三个场景从普通 API 串起来升级为可持久化 graph。
- 输入条件：已有基本索引和问答链路。
- 输出产物：
  - `StewardState`
  - ask graph
  - ingest graph
  - daily digest graph
  - checkpointer
- 具体子任务：
  - 新建 `backend/app/graphs/state.py`。
  - 新建 `backend/app/graphs/ask_graph.py`。
  - 新建 `backend/app/graphs/ingest_graph.py`。
  - 新建 `backend/app/graphs/digest_graph.py`。
  - 接入 SQLite checkpoint。
  - 统一 `thread_id` 协议。
  - 给图节点补 tracing。
  - 明确 graph 输入输出 contract。
- 依赖关系：依赖 Phase 2。
- 验收标准：三条图都可启动，ask 至少支持从头跑通到结果返回。
- 风险点：状态 schema 漂移。
- 预计优先级：P0。

当前子任务状态：

| 子任务 | 状态 |
| --- | --- |
| 新建 `backend/app/graphs/state.py` | `已完成` |
| 新建 `backend/app/graphs/ask_graph.py` | `已完成` |
| 新建 `backend/app/graphs/ingest_graph.py` | `已完成` |
| 新建 `backend/app/graphs/digest_graph.py` | `已完成` |
| 接入 SQLite checkpoint | `已完成（ask / ingest / digest 正常路径已迁到 LangGraph SqliteSaver 的 checkpoints/writes；workflow_checkpoint 继续保留业务元数据，与 waiting_for_approval 状态兼容的 v6 schema 也已补齐）` |
| 统一 `thread_id` 协议 | `已完成（ask / ingest / digest 路径）` |
| 给图节点补 tracing | `进行中（ask / ingest / digest 路径已落 JSONL + SQLite run_trace，trace path 命名与治理未收敛）` |
| 明确 graph 输入输出 contract | `已完成（TASK-042 已在 backend/app/graphs/runtime.py 与 backend/app/main.py 中收敛 ask / ingest / digest 的共享 execution contract、基础 workflow state 与统一 invoke response 装配；ask proposal 与更大的 writeback runtime 平台仍不在本 phase 范围内）` |

#### 10.2.5 Phase 4：HITL 与写回

- 目标：把治理 proposal 变成可审批、可写回、可审计的闭环。
- 输入条件：ingest graph 已能生成结构化建议。
- 输出产物：
  - proposal schema
  - diff 面板
  - 审批恢复接口
  - audit_log 表
  - 基础写回执行器
- 具体子任务：
  - 在 proposal 节点输出结构化 patch。
  - 新建 `audit_log` 表。
  - 新建 `proposal` / `patch_ops` schema。
  - 插件侧增加审批面板。
  - 插件侧实现 frontmatter merge。
  - 插件侧实现正文受限插入。
  - 后端增加 `resume_workflow` 接口。
  - 写回前校验 `before_hash`。
  - 写回后触发增量索引更新。
- 依赖关系：依赖 Phase 3。
- 验收标准：用户能看到 proposal、批准、写回、审计记录。
- 风险点：写回正确性和审批恢复一致性。
- 预计优先级：P0。

当前子任务状态：

| 子任务 | 状态 |
| --- | --- |
| 新建 `audit_log` 表 | `已完成（SQLite audit_log append-only 表、索引与最小写入 helper 已落地）` |
| 新建 `proposal` / `patch_ops` schema | `已完成（proposal、proposal_evidence、patch_op 与最小 save/load helper 已落地）` |
| 在 proposal 节点输出结构化 patch | `已完成（DAILY_DIGEST 已可在显式 proposal 模式下输出结构化 proposal / patch、写入 waiting checkpoint，并通过 /workflows/invoke 返回给插件）` |
| 插件侧增加审批面板 | `已完成（KnowledgeStewardView 已支持 proposal 展示、risk / evidence / patch preview、approve / reject、真实 DAILY_DIGEST proposal 加载与 demo fallback）` |
| 插件侧实现 frontmatter merge | 已完成：`plugin/src/writeback/applyProposalWriteback.ts` 已支持 `merge_frontmatter`，并兼容历史别名 `frontmatter_merge` |
| 插件侧实现正文受限插入 | 已完成：`plugin/src/writeback/applyProposalWriteback.ts` 已支持 `insert_under_heading` |
| 插件侧实现章节替换与受限链接写回 | 已完成：`plugin/src/writeback/applyProposalWriteback.ts` 已支持 `replace_section` 与 `add_wikilink`，并对重复 wikilink 做拒绝 |
| 后端 proposal 静态校验支持新 patch op | `已完成（proposal_validation.py 已正式支持 replace_section / add_wikilink，并补齐 payload-specific validation、危险模式拦截与 add_wikilink existing-note 约束）` |
| 后端增加 `resume_workflow` 接口 | `已完成（/workflows/resume、resume service、approve/reject/幂等恢复测试已落地）` |
| 写回前校验 `before_hash` | `已完成（插件写回前会对目标文件计算 SHA-256，并与 proposal 的 `before_hash` 做一致性校验）` |
| 写回后触发增量索引更新 | `已完成（TASK-030 已在 /workflows/resume 的 successful writeback 路径上触发 best-effort scoped ingest，并通过 post_writeback_sync 返回刷新成功 / 失败结果）` |

#### 10.2.6 Phase 5：观测、评估与演示

- 目标：让系统从“能跑”升级为“可证明、可展示、可面试”。
- 输入条件：至少一条治理链路已闭环。
- 输出产物：
  - trace 输出
  - eval 样本集
  - benchmark 脚本
  - demo 路径脚本
- 具体子任务：
  - 增加 JSONL runtime trace。
  - 增加错误日志。
  - 增加 golden set 目录与样本格式。
  - 编写 `eval/run_eval.py`。
  - 编写 `scripts/demo_paths.md`。
  - 记录 P50 / P95、schema 合法率、问答命中率。
  - 准备 3 条稳定演示路径。
- 依赖关系：依赖 Phase 4。
- 验收标准：每次提交后都能跑一轮最小评估，并能复现 Demo。
- 风险点：样本质量不足，指标无代表性。
- 预计优先级：P1。

当前子任务状态：

| 子任务 | 状态 |
| --- | --- |
| 增加 JSONL runtime trace | `已完成（ask / ingest / digest 路径）` |
| 增加 SQLite `run_trace` 聚合查询 | `已完成（ask / ingest / digest 路径）` |
| 增加错误日志 | `未开始` |
| 增加 golden set 目录与样本格式 | `已完成（已新增 ask / digest 两套最小 golden case，混合 sample_vault 回归与 deterministic fixture bad case）` |
| 编写 `eval/run_eval.py` | `已完成` |
| 编写 `scripts/demo_paths.md` | `未开始` |
| 记录 P50 / P95、schema 合法率、问答命中率 | `未开始` |
| 准备 3 条稳定演示路径 | `未开始` |

### 10.3 两周内建议执行顺序

1. Day 1-2：Phase 0 + Phase 1。
2. Day 3-5：Phase 2。
3. Day 6-8：Phase 3 + Phase 4 前半。
4. Day 9-10：Phase 4 后半 + Phase 5。

### 10.4 会话级执行规则

为避免后续开发再次退化成“一个会话同时推多个半成品”，从 `v0.2.4` 开始，默认采用会话化推进规则。

#### 10.4.1 基本原则

1. 一个会话只解决一个中等粒度问题。
2. 中等粒度问题必须具备明确输入、明确输出、明确验收标准，不能是“继续完善系统”这类泛任务。
3. 同一个会话允许顺手做少量文档同步、测试补充或小型重构，但不允许同时开启第二个中等粒度功能。
4. 如果执行中发现当前问题需要拆分，立即停在可交付边界，把剩余部分登记到下一个会话，而不是本会话继续扩张。

#### 10.4.2 唯一会话 ID 规则

- 会话 ID 格式：`SES-YYYYMMDD-XX`
- 同一天内按顺序递增，如 `SES-20260311-02`
- 每个会话必须同时出现在：
  - `docs/SESSION_LOG.md`
  - `docs/TASK_QUEUE.md`

#### 10.4.3 中等粒度问题的判定标准

一个任务可以算“中等粒度”，通常要满足以下条件中的大部分：

- 能在一次会话中闭环交付，不依赖继续并行做 2 到 3 个子系统。
- 交付结果可以通过命令、接口、测试、截图或文档状态明确验收。
- 影响面可控，通常落在一个模块或一条最小链路切片上。
- 失败时能明确回退，不会把路线图整体拖乱。

反例：

- “把索引系统做完”
- “把工作流全部接好”
- “完善问答和复盘”

正例：

- “设计并落地 `note/chunk` SQLite schema”
- “实现 SQLite FTS5 检索并返回 top-k candidate”
- “跑通 `/ask` 的最小引用式返回”

### 10.5 会话级任务队列位置

- 会话级任务队列已迁移到 `docs/TASK_QUEUE.md`。
- `docs/PROJECT_MASTER_PLAN.md` 不再维护具体会话任务明细，只保留规则、架构、路线图和决策。
- 所有新会话都必须先绑定 `docs/TASK_QUEUE.md` 中的一个任务项，再开始执行。
- 默认只允许会话绑定 `scope=medium` 的任务；`small` 任务只能作为伴随改动，`large` 任务必须先拆分。
- 如果当前任务不在 `docs/TASK_QUEUE.md` 中，必须先补充任务项，再开始实现。

## 11. 决策记录（Architecture Decision Record）

### 11.1 ADR-001：为什么选 LangGraph

- 日期：2026-03-11
- 背景：项目需要可中断、可恢复、可审计的多步骤工作流，而不是单轮问答。
- 备选方案：纯函数编排；LangChain 高层 agent；自写状态机。
- 最终选择：LangGraph。
- 选择原因：
  - 天然适合状态图和条件路由。
  - 支持 checkpoint、thread_id 和 interrupt 模式。
  - 比黑盒 agent 更适合解释系统行为。
- 代价：需要更早定义 state schema、幂等和副作用边界。
- 后续影响：后端架构必须围绕 graph 设计，而不是围绕 chat 设计。

### 11.2 ADR-002：为什么选 Obsidian 作为场景

- 日期：2026-03-11
- 背景：需要一个真实、高频、个人化且有结构化资产的知识场景。
- 备选方案：Notion、通用本地文件夹、浏览器书签系统。
- 最终选择：Obsidian。
- 选择原因：
  - Markdown 文本和 wikilink 结构适合做知识治理。
  - 用户习惯是持续记笔记，治理问题明显。
  - 本地知识库优先，适合做隐私、本地后端与受控写回叙事。
- 代价：需要理解插件 API 和本地桌面开发环境。
- 后续影响：模块设计必须尊重 Vault、MetadataCache 和插件交互方式。

### 11.3 ADR-003：为什么做本地后端

- 日期：2026-03-11
- 背景：索引、graph、评估、日志和模型调用都较重。
- 备选方案：纯插件；云后端。
- 最终选择：本地后端。
- 选择原因：
  - 更适合承载索引、graph 和 eval。
  - 不把复杂逻辑压到 Obsidian 插件线程。
  - 便于脚本化回归和独立测试。
- 代价：双端通信与调试成本更高。
- 后续影响：必须明确插件与后端协议，不能职责混乱。

### 11.4 ADR-004：为什么需要 HITL

- 日期：2026-03-11
- 背景：任何 Vault 写回都可能带来知识资产损坏。
- 备选方案：全自动写回；只给建议不写回。
- 最终选择：高风险操作必须 HITL。
- 选择原因：
  - 能证明系统安全边界。
  - 能为审计和回滚提供控制点。
  - 更符合“知识治理”而不是“模型替你写一切”。
- 代价：用户体验上多一步审批。
- 后续影响：proposal、diff、resume 协议必须先定义。

### 11.5 ADR-005：为什么做 hybrid retrieval

- 日期：2026-03-11
- 背景：Obsidian 语料包含标题、标签、短语、代码块、表格和结构化元数据。
- 备选方案：只做 BM25；只做 vector。
- 最终选择：hybrid retrieval。
- 选择原因：
  - 关键词和语义召回各有覆盖盲区。
  - 治理场景强依赖 metadata 和结构。
  - 问答与治理都需要稳定的前排结果。
- 代价：系统更复杂，需额外评估 fusion 和 rerank 收益。
- 后续影响：必须准备 golden set 来比较不同检索路径。

### 11.6 ADR-006：为什么主打知识治理而不是问答

- 日期：2026-03-11
- 背景：市场上已有很多“Obsidian AI 问答”项目。
- 备选方案：做通用聊天插件；做知识治理系统。
- 最终选择：主打知识治理，问答作为兜底。
- 选择原因：
  - 更贴近日常学习痛点。
  - 更能体现 LangGraph、HITL、审计和 eval 的必要性。
  - 更适合面试中讲工程深度，而不是 API 拼装。
- 代价：实现复杂度明显高于单纯问答。
- 后续影响：路线图必须优先治理链路，避免项目叙事被问答带偏。

### 11.7 ADR-007：为什么采用云优先、本地兼容的模型策略

- 日期：2026-03-11
- 背景：项目当前目标是尽快跑通可演示链路，同时保留后续离线 fallback 和本地质量基线能力。
- 备选方案：完全本地优先；完全云优先；云优先且本地兼容。
- 最终选择：云优先、本地兼容。
- 选择原因：
  - 云模型优先能减少首版在本地模型调优、推理速度和安装体验上的阻力。
  - 本地兼容可以保留离线演示、隐私兜底和质量对比能力，尤其适合后续在 M 系列 Mac 上做 fallback。
  - 该策略已经反映到当前基线代码：`backend/app/config.py` 和 `/health` 返回的 `model_strategy` 均采用 `cloud_primary_local_compatible`。
- 代价：
  - 增加 provider 抽象和配置复杂度。
  - 网络、API key、配额会成为首版风险源。
  - 需要避免把双 provider 支持做成过度工程。
- 后续影响：
  - 后端必须引入显式 provider contract，而不是把模型调用硬编码在 graph 节点里。
  - 评估时应区分 cloud primary 与 local fallback 的结果和延迟。

## 12. 风险清单与降级策略

| 风险描述 | 触发条件 | 影响范围 | 检测方式 | 降级策略 | 是否影响面试演示 |
| --- | --- | --- | --- | --- | --- |
| 模型不可用 | 云模型 API key 无效、配额耗尽、请求超时；或本地 fallback 未启动 | 问答、治理分析、复盘生成 | 模型调用错误率、健康检查 | 提供 mock / 小模型 / 仅检索模式，并保留本地 fallback 接口 | 是 |
| generated answer / governance rationale / digest 仍可能质量不足 | provider 虽然给出合法编号、proposal 摘要或模板化 digest，但结论仍可能超出证据、过度概括或覆盖不足 | ask / governance / digest 可信度、演示可信度 | 人工抽样、golden set、共享 claim-level faithfulness report / runtime_faithfulness trace | 当前 ask 已完成四维度离线评估，governance / digest 也已补齐 `rationale_faithfulness / patch_safety / coverage` 等最小离线基线；后续继续收敛 patch_safety 标签稳定性、digest coverage 标注规范与阈值校准 | 是 |
| 云 provider 不稳定 | 网络抖动、区域限流、供应商波动、SSE 断流 | `ask`、proposal 生成、演示稳定性 | provider 错误码、超时率、流式中断率 | 先切非流式返回，再降级为仅检索结果；保留本地 provider 接口但不默认启用 | 是 |
| reranker 太慢 | 无 GPU、候选过多 | 问答和治理延迟 | P95 latency、节点耗时 | 关闭 rerank、减少 top-k | 是 |
| 索引过慢 | Vault 较大、embedding 慢 | 首次体验、增量更新 | ingest 耗时、队列积压 | 分批索引、后台索引、先 FTS 后向量 | 是 |
| patch 错误 | 定位错位、前置 hash 不一致 | 写回安全 | 写回失败率、审计异常 | 不自动重试，回到审批界面 | 是 |
| Python 环境漂移 | 非推荐 `backend/.venv` 被重新当作入口，或 `./.conda/knowledge-steward` 与 `backend/environment.yml` 发生漂移 | 后端启动、依赖复现、团队协作 | README、`backend/environment.yml` 与实际启动命令不一致；导入错误；锁文件缺失 | 当前已统一推荐路线为工作区本地 conda prefix，并以 `python -m app.main` 为统一入口；后续若新增环境路线，必须同步 README 与验证命令 | 是 |
| Vault 结构混乱 | 标签不规范、链接失效、命名重复 | 检索和治理质量 | bad case 抽样、召回质量 | 先加规则清洗，降低自动化程度 | 是 |
| 模板推断过拟合 `sample_vault` | `note_type` 和 `template_family` 过度依赖当前日记模板 | 解析、索引、复盘和治理建议质量 | 新样本分类错误率、人工抽样 | 保留 `generic_note` fallback，不把模板推断作为唯一分流条件 | 是 |
| `summary_note` 识别不稳 | 部分“迭代总结”笔记未被稳定归类为 `summary_note` | metadata filter、ask 置信提示 | filter fallback 触发率、抽样误分类数 | 收敛 parser 模板规则，必要时增加 path / 标题兜底 | 是 |
| evaluation 做不出来 | 无真实样本、无标准答案 | 无法证明质量 | eval 样本数、报告空缺 | 先做小型 golden set 和人工抽样 | 是 |
| 复盘质量不稳定 | source note 选择偏差、聚类弱、提示词漂移 | digest 可信度 | `source_notes` 抽样、人工抽样、审批通过率 | 首版固定模板并暴露 `source_notes`，后续补时间窗口和过滤输入 | 是 |
| 提示词漂移 | 多轮改动后行为不一致 | proposal 和复盘质量 | 回归结果波动 | 把 prompt 版本化，纳入 eval | 是 |
| 中断恢复出错 | thread / proposal / patch 状态不一致 | 审批和写回链路 | 审计记录与运行状态不一致 | 恢复前校验 proposal_id 和 writeback 状态 | 是 |
| 插件与后端通信失败 | 本地端口占用、服务未启动、CORS/协议错误 | 全链路不可用 | 健康检查、前端错误提示 | 提供重试、离线 mock、清晰报错 | 是 |

## 13. 面试问答库

原第 13 节面试问答库已迁移到 [docs/INTERVIEW_PLAYBOOK.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/INTERVIEW_PLAYBOOK.md)。

本文件只保留架构、风险、路线与 ADR；具体面试追问、回答思路和“哪些回答会显得像没做过项目”的口径统一去 playbook 查。

## 14. 后续维护规则

1. 每次开发完一个功能，至少必须更新以下章节：
   - 先为本次会话分配唯一会话 ID，并在 `docs/SESSION_LOG.md` 追加一条新记录。
   - 每次会话必须绑定 `docs/TASK_QUEUE.md` 中的一个任务项；如果会话范围变化，先更新 `docs/TASK_QUEUE.md` 再继续开发。
   - 涉及模块实现时，更新第 3 节现状盘点和第 9 节模块说明。
   - 涉及架构边界变化时，更新第 4 节和第 11 节 ADR。
   - 涉及工作流变化时，更新第 5 节。
   - 涉及索引或检索变化时，更新第 6 节。
   - 涉及写回和审批变化时，更新第 7 节。
   - 涉及 tracing / eval 变化时，更新第 8 节。
   - 涉及计划变化时，更新第 10 节。

2. 代码实现与注释规则：
   - 后续所有代码开发都必须增加必要的中文注释，尤其是状态流转、边界条件、降级逻辑、恢复逻辑、协议映射、复杂 SQL / 检索策略、易误解的数据结构和非直观的业务分支。
   - 注释必须解释“为什么这样做”或“这里在防什么问题”，不能用中文重复代码表面语义。
   - 对显而易见的一行赋值、简单透传或纯样板代码，不要求强行加注释，避免注释噪音。
   - 如果某段逻辑靠注释才能勉强读懂，同时代码本身还能继续拆分或命名优化，应优先优化代码结构，再补必要注释。

3. 新增模块时，必须补齐以下字段：
   - 模块职责
   - 核心文件路径
   - 上下游依赖
   - 关键类 / 函数 / 数据结构
   - 为什么要有这个模块
   - 易错点
   - 当前稳定性
   - 面试追问点

4. 技术选型变化时，必须更新对应 ADR：
   - 工作流框架变化，更新 ADR-001。
   - 场景变化，更新 ADR-002。
   - 架构部署变化，更新 ADR-003。
   - HITL 策略变化，更新 ADR-004。
   - 检索路线变化，更新 ADR-005。
   - 项目主叙事变化，更新 ADR-006。
   - 模型策略、provider 路线或本地/云优先级变化，更新 ADR-007。

5. 每周必须回顾以下 KPI / 风险 / 待办：
   - 当前最小可运行链路是否仍能跑通。
   - 最新 golden set 指标是否退化。
   - 写回错误率是否上升。
   - P50 / P95 延迟是否超预算。
   - 当前未决 Open Question 是否阻塞后续阶段。
   - Python 环境是否已收敛为单一开发入口，README 与真实运行方式是否一致。

6. 明确禁止事项：
   - 不允许只改代码不改文档。
   - 不允许一个会话同时并行推进多个中等粒度功能项。
   - 不允许把“建议路径”写成“已实现路径”。
   - 不允许在未更新 ADR 的情况下悄悄替换核心技术路线。
   - 不允许把高风险自动写回偷偷降成默认开启。
   - 不允许在复杂实现落地时完全不写中文注释，导致后续无法快速判断设计意图、失败模式和边界条件。

7. 文档版本管理规则：
   - 任何影响架构、协议、状态 schema、proposal schema、评估方法的变更，都必须提升版本号并补变更记录。
   - 小型文字修正可不升主版本，但必须更新“最近更新时间”。
