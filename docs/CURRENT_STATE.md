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
- `TASK-045` 已在 `SES-20260327-02` 落地第一阶段并合入本地 `main`：ask 已新增 `get_note_outline`、fail-closed `find_backlinks` 与 verified-only tool reentry，插件写回已支持 `replace_section / add_wikilink`，并补上 proposal 静态校验接线与回归测试。
- `TASK-045` 仍未完全收口：`backend/app/services/proposal_validation.py` 还没有把 `replace_section / add_wikilink` 作为正式支持的持久化校验 op 收口，因此当前最优先仍是继续 `TASK-045`，而不是直接切到 `TASK-046`。

## 最近完成

| task_id | 日期 | 结果 |
| --- | --- | --- |
| `TASK-045` | 2026-03-28 | 部分完成：outline/backlinks、ask verified-only tool reentry、插件 `replace_section / add_wikilink` 与静态校验接线已合入本地 `main`，但 proposal validator 对新 op 的正式支持仍待收口 |
| `TASK-044` | 2026-03-27 | ask / ingest / digest 正常路径迁到 LangGraph `SqliteSaver`，保留 `workflow_checkpoint` 业务封装层 |
| `TASK-043` | 2026-03-23 | 新增 `CURRENT_STATE`、拆出 `INTERVIEW_PLAYBOOK` / `CHANGELOG`、建立 `TASK_QUEUE` / `SESSION_LOG` archive 结构 |
| `TASK-042` | 2026-03-18 | 统一 ask / ingest / digest 的入口路由与共享 workflow contract |

## 默认下一任务

- 若继续收口当前 medium：`TASK-045`
  - 主题：补 proposal persistence validator 对 `replace_section / add_wikilink` 的正式支持，并把控制面文档同步到真实代码边界。
- 若在 `TASK-045` 收口后升级上下文装配层（简历检索深度）：`TASK-047`
  - 主题：将装配层从去重+截断升级为四阶段质量控制管线（相关性过滤、来源多样性、结构化增强、加权预算分配）。
- 若在 `TASK-045` 收口后升级 ask 编排范式（简历强项）：`TASK-046`
  - 主题：ask 链路内部引入 ReAct 多轮工具调用循环，ingest / digest 保持静态编排。
- 若继续业务功能 medium：`TASK-031`
  - 主题：为”本地写回成功但 `/workflows/resume` 失败”补跨会话恢复入口。
- 若先补检索路径的可持续性：`TASK-032`
  - 主题：把 scoped ingest 从整库 FTS 重建收敛为局部 FTS 同步。
- 若先补问答可信度 runtime gate：`TASK-033`
  - 主题：把 groundedness 从离线 eval 前移到 ask 主链路的保守降级控制。

## 当前风险

- `proposal_validation.py` 与插件写回能力边界仍有断口：`replace_section / add_wikilink` 已在插件执行器和测试层落地，但后端持久化校验仍未把它们作为正式支持 op 收口。
- 控制面与副作用面仍有断口：本地写回成功但后端记账失败时，当前还没有跨会话恢复入口，对应 `TASK-031`。
- scoped ingest 仍会整库重建 `chunk_fts`，一旦 approval 高频触发，成本会持续放大，对应 `TASK-032`。
- ask 的 semantic groundedness 仍只在离线 eval 中暴露，没有进入 runtime 保守 gate，对应 `TASK-033`。
- 本地 `main` 仍保留本次 merge 生成的 `stash@{0}` 作为安全兜底；继续开发前需要明确哪些工作区改动要保留、哪些只作为 merge 备份存在。

## 默认读取顺序

新会话默认按以下顺序读取：

1. [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
2. [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md)
3. [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md) 中最近相关记录
4. 相关代码入口文件

## 建议先读文件

### 若继续 `TASK-047`

- [backend/app/context/assembly.py](backend/app/context/assembly.py)
- [backend/app/retrieval/hybrid.py](backend/app/retrieval/hybrid.py)
- [backend/app/services/ask.py](backend/app/services/ask.py)
- [backend/app/contracts/workflow.py](backend/app/contracts/workflow.py)

### 若继续 `TASK-045`

- [backend/app/services/proposal_validation.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/proposal_validation.py)
- [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- [backend/app/tools/registry.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/tools/registry.py)
- [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)
- [plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts)

### 若继续 `TASK-046`

- [backend/app/services/ask.py](backend/app/services/ask.py)
- [backend/app/tools/registry.py](backend/app/tools/registry.py)
- [backend/app/graphs/ask_graph.py](backend/app/graphs/ask_graph.py)
- [backend/app/observability/runtime_trace.py](backend/app/observability/runtime_trace.py)

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

### 若继续 `TASK-033`

- [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)
- [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
- [eval/golden/ask_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/ask_cases.json)
- [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)

## 历史归档

- 任务队列完整快照：
  [docs/archive/task_queue/TASK_QUEUE_20260323_pre_split.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/archive/task_queue/TASK_QUEUE_20260323_pre_split.md)
- 会话日志 2026-03 月归档：
  [docs/archive/session_logs/SESSION_LOG_2026-03.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/archive/session_logs/SESSION_LOG_2026-03.md)
