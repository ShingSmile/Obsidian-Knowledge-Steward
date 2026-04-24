# CURRENT_STATE

本文件是项目唯一的动态控制面入口。

它只承载高波动事实：

- 当前阶段
- 最近完成
- 默认下一任务
- 当前风险
- 新会话建议先读文件

稳定架构、模块边界、ADR 与长期风险继续以 [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 为准。
任务绑定与验收以 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 为准。
最近相关会话与历史归档以 [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md) 为准。

## 当前阶段

- interview-first 主线 `TASK-030` 到 `TASK-042` 已全部收口。
- `TASK-043` 已在 `SES-20260323-02` 完成，当前文档控制面已拆成 `CURRENT_STATE / INTERVIEW_PLAYBOOK / CHANGELOG / archive` 分层。
- `TASK-044` 已在 `SES-20260327-01` 完成并合并到 `main`：ask / ingest / digest 正常路径的 checkpoint 持久化已迁到 LangGraph `SqliteSaver`，`workflow_checkpoint` 继续只承担业务元数据与恢复策略层。
- `TASK-045` 已由 `SES-20260327-02` 的第一阶段实现和 `SES-20260329-01` 的 validator 收口共同完成：ask 已新增 `get_note_outline`、fail-closed `find_backlinks` 与 verified-only tool reentry，插件写回已支持 `replace_section / add_wikilink`，后端 proposal persistence / resume 静态校验也已正式支持这两个新 op 并补齐 payload-specific validation。
- `TASK-047` 已在 `SES-20260329-02` 完成：ask 上下文装配层已从“去重 + 截断”升级为相关性过滤、来源多样性控制、结构化增强与加权预算分配四阶段管线，`ContextBundle` 现可输出 `source_notes / assembly_metadata`，prompt 与 citation 也已对齐 post-assembly 可见 evidence。
- `TASK-046` 已在 `SES-20260401-01` 完成：ask 已从线性三节点图重构为 `prepare_ask -> llm_call -> tool_node -> finalize_ask` 的图级 ReAct 循环，`run_minimal_ask` 主入口已移除，`AskWorkflowResult` 新增 `tool_call_rounds`，每轮 LLM / tool 节点都进入 LangGraph checkpoint 与 runtime trace。
- `TASK-049` 已在 `SES-20260406-02` 完成并合并到 `main`：ask 的 tool selection 现优先通过 API 级 `tools / tool_calls` 走 Structured Tool Calling，现有 `ToolSpec` 可直接映射为 OpenAI-compatible tools payload；对不支持 Structured Tool Calling 的 provider 保留 prompt-based fallback，`tool_node` 与 guardrail 执行链路不变。
- `TASK-048` 已在 `SES-20260401-02` 确认超出单个 `medium` 边界，现重定义为 umbrella，并拆为 `TASK-050` 到 `TASK-054` 五段执行。
- `TASK-050` 已在 `SES-20260401-02` 完成：ask runtime 已接入共享 faithfulness snapshot，对明显 `unsupported_claim` 的 generated answer 会保守降级为 `retrieval_only`，离线 eval 也已复用同一判定层。
- `TASK-051` 已在 `SES-20260401-03` 完成： [backend/app/quality/faithfulness.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/quality/faithfulness.py) 已升级为共享 claim-level faithfulness core，可输出 `entailed / contradicted / neutral` verdict，并在 embedding provider 可用时走更强的 semantic backend；[eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py) 也已让 ask / governance / digest 共用这套判定层，governance / digest 的 faithfulness 不再直接退回 `context_recall` 充当替代指标。
- `TASK-052` 已在 `SES-20260402-01` 完成：ask / digest runtime 已共用基于 claim-level semantic core 的 `RuntimeFaithfulnessSignal`；ask 对低分 generated answer 会保守降级为 `retrieval_only`，digest 现已输出结构化 `runtime_faithfulness` quality outcome，ask / digest trace 与 checkpoint serializer allowlist 也已对齐新 contract。
- `TASK-053` 已在 `SES-20260402-02` 完成并合并到 `main`：ask 离线评估现已稳定输出 Faithfulness / Answer Relevancy / Context Precision / Context Recall 四维度，`answer_relevancy` 成为正式 metric key，并保留 `relevancy` 兼容 alias；ask golden 已扩到 5 条以上 quality case，覆盖 grounded / unsupported / partial support。
- `TASK-054` 已在 `SES-20260406-01` 完成： [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py) 现已按 scenario 输出 governance 的 `Rationale Faithfulness / Patch Safety` 与 digest 的 `Faithfulness / Coverage`， [eval/golden/governance_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/governance_cases.json) 现已补到 3 条 governance golden case， [backend/tests/test_eval_runner.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_eval_runner.py) 也已补齐 mixed ask / governance / digest overview 回归。
- `TASK-048` 已由 `TASK-050` 到 `TASK-054` 全部收口：跨链路内容质量评估与 runtime faithfulness 治理 umbrella 不再保留未完成的 `medium` 切片。
- `TASK-055` 已在 `SES-20260402-02` 作为 retroactive completed refactor 回填：backend / plugin / persistence / retrieval 已统一采用 `vault-relative` note path contract，输入层兼容 vault 内真实绝对路径并立即归一化，`/vault/...` 只作为历史迁移格式，普通执行路径拒绝。
- `TASK-056` 已在 `SES-20260418-01` 完成：基于 2026-04-18 的评测校准，已把“golden regression baseline -> resume-grade ask benchmark”正式登记为新的治理主线，并新增 `TASK-057` 到 `TASK-060` 四个 benchmark `medium`；动态控制面默认下一任务不再先回到 `TASK-031 / TASK-032`，而是先进入 ask-only benchmark 主线。
- `TASK-061` 已在 `SES-20260418-02` 完成：benchmark 主线已按第二轮设计校准重排为双层评测、三段执行：`TASK-057` 固定为 `50` 条 query 的数据集任务，`TASK-058` 固定为 retrieval baseline，`TASK-059` 固定为真实 provider 的 answer benchmark；`TASK-060` 已改为 deferred，不再阻塞当前主线。
- `TASK-057` 已在 `SES-20260419-01` 完成：`eval/benchmark/ask_benchmark_cases.json` 已落成 `50` 条正式人工审核 case，bucket 分布满足 `single_hop=20 / multi_hop=10 / metadata_filter=8 / abstain_or_no_hit=6 / tool_allowed=6`，`ask_benchmark_review_backlog.json` 当前为空，dataset `validate` 与三组 benchmark 相关 `unittest` 已通过。
- `TASK-058` 已在 `SES-20260422-01` 完成：retrieval benchmark runner、local-only preflight 与正式 dataset 接线都已落地，headline 子集固定为 `38` 条 case；当前 retrieval baseline 为 `fts_only Recall@10=0.2368 / NDCG@10=0.2368`、`vector_only Recall@10=0.6842 / NDCG@10=0.4612`、`hybrid_rrf Recall@10=0.7895 / NDCG@10=0.5636`。同时 FTS 已补齐中文自然语言、日期 / 版本号 hint、pre-limit truncation 与 identifier-only query 的检索回归。
- `TASK-059` 已在 `SES-20260424-02` 完成 v1：真实 provider answer benchmark 入口、固定 `10` 条 smoke subset、三种 answer variant 与 artifact metadata 已落地，并用 `qwen3.6-flash-2026-04-16` 跑通 smoke；当前结果只能证明真实生成链路与指标落盘可用，不能证明装配层或 runtime gate 已带来质量收益。

## 最近完成

| task_id | 日期 | 结果 |
| --- | --- | --- |
| `TASK-049` | 2026-04-06 | 已完成：ask 现已优先使用 API 级 `tools / tool_calls` 做 Structured Tool Calling，`ToolSpec` 可直接映射为 tools payload；provider 不支持时保留 fallback，定向 backend `49/49` tests 与 ask eval `12/12` case 通过 |
| `TASK-054` | 2026-04-06 | 已完成：eval runner 现已按场景输出 governance 的 `Rationale Faithfulness / Patch Safety` 与 digest 的 `Faithfulness / Coverage`，governance golden 已补到 3 条 case，`backend.tests.test_eval_runner` 7 tests 与 5 条 targeted governance / digest eval case 通过 |
| `TASK-055` | 2026-04-06 | 已完成：跨 backend / plugin / persistence / retrieval 的 note path contract 已收敛为 `vault-relative`，输入层兼容 vault 内真实绝对路径并立即归一化，普通执行路径拒绝新的 `/vault/...`；相关 backend 179 tests 与 plugin 20 tests 通过，随后与 `TASK-053` 合流后的 `main` 继续通过 backend 180 tests |
| `TASK-056` | 2026-04-18 | 已完成：登记 `TASK-057` 到 `TASK-060` 四个 ask-only benchmark `medium`，并将动态控制面的默认下一任务切到 `TASK-057`，不再继续沿旧的 `TASK-031 / TASK-032` 优先级推进 |
| `TASK-061` | 2026-04-18 | 已完成：按双层评测方案重构 ask benchmark 主线定义，明确 `TASK-059` 必须接真实 provider 且 ask 真走 `generated_answer` 路径，并将 `TASK-060` 改为 deferred |
| `TASK-057` | 2026-04-19 | 已完成：正式 ask benchmark 数据集已落成 `50` 条 approved case，分布满足 `20 / 10 / 8 / 6 / 6`，`manage_ask_benchmark.py validate` 与 benchmark 相关 `59` 个 `unittest` 通过 |
| `TASK-058` | 2026-04-22 | 已完成：retrieval benchmark runner、local-only preflight 与 FTS query normalization / hint-aware reranking 修复已合并到 `main`，当前 headline `38` 条 case baseline 为 `hybrid_rrf Recall@10=0.7895 / NDCG@10=0.5636` |
| `TASK-059` | 2026-04-24 | 已完成 v1：真实 provider answer benchmark CLI、固定 10-case smoke、三种 variant、prompt version 与 artifact metadata 已落地；`qwen3.6-flash-2026-04-16` smoke 跑通，规则正确性评分暴露出需由 `TASK-062` 继续补语义 judge |
| `TASK-053` | 2026-04-06 | 已完成：ask eval 已正式输出 Faithfulness / Answer Relevancy / Context Precision / Context Recall 四维度，`answer_relevancy` 成为正式 metric key 并保留 `relevancy` alias；ask golden 已扩到 5 条以上 quality case，定向 eval runner 7 tests 与 ask eval 5 case 通过 |
| `TASK-052` | 2026-04-02 | 已完成：ask / digest runtime 已共用 `RuntimeFaithfulnessSignal`，ask 会在低分时保守降级为 `retrieval_only`，digest 新增结构化 `runtime_faithfulness` outcome 与 trace 字段；相关 backend 66 tests 全部通过 |
| `TASK-051` | 2026-04-02 | 已完成：共享 claim-level semantic faithfulness core 已落到 [backend/app/quality/faithfulness.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/quality/faithfulness.py)，`eval/run_eval.py` 已让 ask / governance / digest 共用同一套 claim verdict 层；相关 backend 15 tests 与 4 条 targeted eval case 全部通过 |
| `TASK-050` | 2026-04-01 | 已完成：共享 ask faithfulness 判定层已抽出到 `backend/app/quality/faithfulness.py`，ask runtime 会对 `unsupported_claim` 保守降级到 `retrieval_only`，相关 backend 45 tests 与 7 条 targeted eval case 全部通过 |
| `TASK-046` | 2026-04-01 | 已完成：ask 已收敛为 graph-only ReAct 循环，新增 `tool_call_rounds`，`tests.test_ask_workflow` 共 32 tests 与 2 条 ask eval case 全部通过 |
| `TASK-047` | 2026-03-29 | 已完成：ask 上下文装配层已升级为四阶段质量控制管线，`ContextBundle` 输出 `source_notes / assembly_metadata`，prompt 可见 `source_note_title / position_hint`，`tests.test_context_assembly + tests.test_ask_workflow` 共 54 tests 与 2 条 ask eval case 全部通过 |
| `TASK-045` | 2026-03-29 | 已完成：proposal validator 已正式支持 `replace_section / add_wikilink`，补齐 payload-specific validation、dangerous-pattern 拦截与 `add_wikilink` existing-note 约束；相关 backend 86 tests、plugin 11 tests 与 plugin build 全部通过 |
| `TASK-044` | 2026-03-27 | ask / ingest / digest 正常路径迁到 LangGraph `SqliteSaver`，保留 `workflow_checkpoint` 业务封装层 |
| `TASK-043` | 2026-03-23 | 新增 `CURRENT_STATE`、拆出 `INTERVIEW_PLAYBOOK` / `CHANGELOG`、建立 `TASK_QUEUE` / `SESSION_LOG` archive 结构 |

## 默认下一任务

- 默认进入 `TASK-062`
  - 主题：为 ask answer benchmark 接入离线 LLM-as-judge 语义正确性评分，保留规则判分作为 deterministic smoke，同时新增 judge correctness 作为分析装配层 / 检索 / runtime gate 改进价值的主质量信号。
- `TASK-062` 收口后，再回到 `TASK-031`
  - 主题：为“本地写回成功但 `/workflows/resume` 失败”补跨会话恢复入口。
- 若回溯刚完成的 `TASK-059`
  - 主题：已完成 v1；仅剩 full 50-case 显式运行、token / cost 统计与 LLM-as-judge 语义评分等后续项，不应继续塞回 `TASK-059`。
- 旧 `TASK-060` 已从 active queue 删除
  - 主题：原人工校准、bad case taxonomy 与报告导出任务不再作为独立 `medium` 维护；历史定义已随 2026-04-24 active backlog 瘦身归档。
- 若回溯刚完成的 `TASK-058`
  - 主题：已完成；仅剩 residual hybrid misses taxonomy、query bucket 聚合与 rewrite / chunking 覆盖判断等 `small` 尾项，不应再单独开一个新的 `medium`。
- 若回溯刚完成的 `TASK-049`
  - 主题：已完成；仅剩 ToolSpec `description` 字段评估、tools token 消耗 trace 与 parallel tool calls 评估三个 `small` 尾项，不应再单独开一个 `medium`。
- 若回溯刚完成的 `TASK-054`
  - 主题：已完成；仅剩 Patch Safety 违规项分类标签稳定化与 digest coverage 关键事实标注规范两个 `small` 尾项，不应再单独开一个 `medium`。
- 若回溯刚完成的 `TASK-053`
  - 主题：已完成；仅剩 Context Recall 标注规范与 answer relevancy deterministic fallback 两个 `small` 尾项，不应再单独开一个 `medium`。
- 若回溯刚完成的 `TASK-055`
  - 主题：已完成；仅剩历史 `/vault/...` 样例清理与真实旧库覆盖率抽样两个 `small` 尾项，不应再单独开一个 `medium`。
- 若回溯刚完成的 `TASK-052`
  - 主题：已完成；仅剩 runtime faithfulness score 的插件侧暴露与 digest `low_confidence` 更细粒度 reason code 两个 `small` 尾项，不应再单独开一个 `medium`。
- 若查看原 umbrella：`TASK-048`
  - 主题：已由 `TASK-050` 到 `TASK-054` 全部完成，不应再作为单个 `medium` 直接执行。
- 若先补检索路径的可持续性：`TASK-032`
  - 主题：把 scoped ingest 从整库 FTS 重建收敛为局部 FTS 同步。
- 若回溯刚完成的 `TASK-046`
  - 主题：已完成；仅剩 token 消耗累计统计、多轮 tool-call eval case 与循环中间 context 增量去重三个 `small` 尾项，不应再单独开一个 `medium`。
- 若回溯刚完成的 `TASK-047`
  - 主题：已完成；仅剩 assembly trace、diversity overflow 备选池与相关性阈值 eval 覆盖三个 `small` 尾项，不应再单独开一个 `medium`。
- 若回溯刚完成的 `TASK-045`
  - 主题：已完成；仅剩 `replace_section.max_changed_lines` 与 validator 配置化两个 `small` 尾项，不应再单独开一个 `medium`。
- 若回溯刚完成的 `TASK-051`
  - 主题：已完成；claim 拆解的中文停用词 / allowlist 仍未落地，而 runtime score / threshold / low-confidence trace 已由 `TASK-052` 的 shared runtime signal 先补到运行时层，不应再单独开一个 `medium`。

## 当前风险

- `TASK-059` 已把真实 provider answer-level benchmark 跑通到 smoke 层，但尚未跑 full 50-case；当前不应把 10-case smoke 当成最终质量结论。
- answer benchmark 的规则正确性评分仍依赖字符串命中，容易把语义正确但表述不完全连续的回答判错；`TASK-062` 已登记为下一步 judge correctness 补强任务。
- 当前 retrieval baseline 仍有 `8` 个 `hybrid_rrf` miss case，说明 answer 层开启前，后续仍可能需要一个 `small` 级 failure taxonomy 来区分 query rewrite、chunking、heading 粒度与 path prior 的剩余断口。
- `TASK-046` 已完成，但仍留有三个 `small` 尾项：ReAct 循环还没有 token 消耗累计统计、多轮工具调用场景还没有独立 eval golden case，循环中间 context 的增量去重也还没落地。
- `TASK-047` 已完成，但仍留有三个 `small` 尾项：`assembly_metadata` 还没有写入结构化 trace，多样性淘汰的 chunk 还没有备选池，相关性阈值比例也还缺离线 eval 覆盖。
- `TASK-045` 已完成，但仍留有两个 `small` 尾项：`replace_section` 的 `max_changed_lines` 安全检查尚未落地，proposal validator 的阈值 / 白名单也还没抽到配置层。
- `TASK-052` 已完成，但仍留有两个 `small` 尾项：runtime faithfulness score 还没有作为可选质量元数据暴露给插件侧，digest 的 `low_confidence` 文案 reason code 也还较粗。
- `TASK-051` 已完成，但 claim 拆解的中文停用词 / allowlist 仍未落地；运行时阈值、score 与 low-confidence trace 已由 `TASK-052` 的 shared runtime signal 在 ask / digest 链路先补齐。
- note path contract 已收敛为 `vault-relative`，但历史 `/vault/...` 样例、旧 eval artifact 或外部旧库仍可能残留伪绝对路径；新增 fixture / API payload 不应再重新写回这种格式。
- `TASK-054` 已完成，但仍留有两个 `small` 尾项：Patch Safety 的违规项分类标签还不稳定，digest coverage 的关键事实抽取标注规范也还未收敛。
- 控制面与副作用面仍有断口：本地写回成功但后端记账失败时，当前还没有跨会话恢复入口，对应 `TASK-031`。
- scoped ingest 仍会整库重建 `chunk_fts`，一旦 approval 高频触发，成本会持续放大，对应 `TASK-032`。

## 默认读取顺序

新会话默认按以下顺序读取：

1. [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
2. [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md)
3. [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md) 中最近相关记录
4. 相关代码入口文件

## 建议先读文件

### 若回溯已完成的 `TASK-046`

- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)
- [backend/app/graphs/state.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/state.py)
- [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)
- [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)

### 若回溯已完成的 `TASK-047`

- [backend/app/context/assembly.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/context/assembly.py)
- [backend/app/context/render.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/context/render.py)
- [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)
- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/tests/test_context_assembly.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_context_assembly.py)
- [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)

### 若回溯已完成的 `TASK-045`

- [backend/app/services/proposal_validation.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/proposal_validation.py)
- [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- [backend/app/tools/registry.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/tools/registry.py)
- [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)
- [plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts)

### 若继续 `TASK-031`

- [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)
- [plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts)
- [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py)
- [docs/archive/session_logs/SESSION_LOG_2026-03.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/archive/session_logs/SESSION_LOG_2026-03.md)

### 若继续 `TASK-032`

- [backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py)
- [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- [backend/app/retrieval/sqlite_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_fts.py)
  - [docs/archive/task_queue/TASK_QUEUE_20260323_pre_split.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/archive/task_queue/TASK_QUEUE_20260323_pre_split.md)

### 若继续 `TASK-062` 或回溯 `TASK-059` / `TASK-058` 尾项

- [eval/benchmark/ask_benchmark_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/benchmark/ask_benchmark_cases.json)
- [eval/benchmark/ask_benchmark_spec.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/benchmark/ask_benchmark_spec.md)
- [eval/benchmark/run_answer_benchmark.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/benchmark/run_answer_benchmark.py)
- [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
- [eval/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/README.md)
- [backend/app/benchmark/ask_answer_benchmark.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_answer_benchmark.py)
- [backend/app/benchmark/ask_answer_benchmark_scoring.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_answer_benchmark_scoring.py)
- [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)
- [backend/app/retrieval/hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/hybrid.py)
- [backend/app/context/assembly.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/context/assembly.py)
- [backend/app/quality/faithfulness.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/quality/faithfulness.py)
- [backend/app/tools/registry.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/tools/registry.py)
- [sample_vault/](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/sample_vault)

### 若回溯已完成的 `TASK-049`

- [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)
- [backend/app/tools/registry.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/tools/registry.py)
- [backend/app/context/render.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/context/render.py)
- [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)
- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)

### 若回溯已完成的 `TASK-051`

- [backend/app/quality/faithfulness.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/quality/faithfulness.py)
- [backend/app/quality/__init__.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/quality/__init__.py)
- [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
- [backend/tests/test_faithfulness.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_faithfulness.py)
- [backend/tests/test_ask_guardrails.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_guardrails.py)
- [backend/tests/test_eval_runner.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_eval_runner.py)
- [eval/golden/ask_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/ask_cases.json)
- [eval/golden/governance_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/governance_cases.json)
- [eval/golden/digest_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/digest_cases.json)

### 若回溯已完成的 `TASK-052`

- [backend/app/quality/faithfulness.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/quality/faithfulness.py)
- [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)
- [backend/app/guardrails/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/guardrails/ask.py)
- [backend/app/services/digest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/digest.py)
- [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)
- [backend/app/graphs/digest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/digest_graph.py)
- [backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py)
- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/tests/test_faithfulness.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_faithfulness.py)
- [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)
- [backend/tests/test_digest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_digest_workflow.py)

### 若回溯已完成的 `TASK-053`

- [backend/app/quality/faithfulness.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/quality/faithfulness.py)
- [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
- [eval/golden/ask_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/ask_cases.json)
- [backend/tests/test_eval_runner.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_eval_runner.py)
- [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)

### 若回溯已完成的 `TASK-055`

- [backend/app/path_semantics.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/path_semantics.py)
- [backend/app/services/proposal_validation.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/proposal_validation.py)
- [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- [backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py)
- [backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py)
- [backend/app/services/rollback_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/rollback_workflow.py)
- [backend/app/tools/ask_tools.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/tools/ask_tools.py)
- [backend/app/retrieval/sqlite_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_fts.py)
- [plugin/src/writeback/pathSemantics.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/pathSemantics.ts)
- [plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts)
- [plugin/src/writeback/writeback.test.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/writeback.test.ts)

### 若回溯已完成的 `TASK-054`

- [backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py)
- [backend/app/services/digest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/digest.py)
- [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
- [eval/golden/governance_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/governance_cases.json)
- [eval/golden/digest_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/digest_cases.json)
- [eval/golden/resume_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/resume_cases.json)
- [backend/tests/test_eval_runner.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_eval_runner.py)

## 历史归档

- 任务队列完整快照：
  [docs/archive/task_queue/TASK_QUEUE_20260323_pre_split.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/archive/task_queue/TASK_QUEUE_20260323_pre_split.md)
- 会话日志 2026-03 月归档：
  [docs/archive/session_logs/SESSION_LOG_2026-03.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/archive/session_logs/SESSION_LOG_2026-03.md)
