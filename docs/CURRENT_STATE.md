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

## 最近完成

| task_id | 日期 | 结果 |
| --- | --- | --- |
| `TASK-047` | 2026-03-29 | 已完成：ask 上下文装配层已升级为四阶段质量控制管线，`ContextBundle` 输出 `source_notes / assembly_metadata`，prompt 可见 `source_note_title / position_hint`，`tests.test_context_assembly + tests.test_ask_workflow` 共 54 tests 与 2 条 ask eval case 全部通过 |
| `TASK-045` | 2026-03-29 | 已完成：proposal validator 已正式支持 `replace_section / add_wikilink`，补齐 payload-specific validation、dangerous-pattern 拦截与 `add_wikilink` existing-note 约束；相关 backend 86 tests、plugin 11 tests 与 plugin build 全部通过 |
| `TASK-044` | 2026-03-27 | ask / ingest / digest 正常路径迁到 LangGraph `SqliteSaver`，保留 `workflow_checkpoint` 业务封装层 |
| `TASK-043` | 2026-03-23 | 新增 `CURRENT_STATE`、拆出 `INTERVIEW_PLAYBOOK` / `CHANGELOG`、建立 `TASK_QUEUE` / `SESSION_LOG` archive 结构 |
| `TASK-042` | 2026-03-18 | 统一 ask / ingest / digest 的入口路由与共享 workflow contract |

## 默认下一任务

- 默认进入 `TASK-046`
  - 主题：ask 链路内部引入 ReAct 多轮工具调用循环，ingest / digest 保持静态编排。
- 若继续业务功能 medium：`TASK-031`
  - 主题：为”本地写回成功但 `/workflows/resume` 失败”补跨会话恢复入口。
- 若先补检索路径的可持续性：`TASK-032`
  - 主题：把 scoped ingest 从整库 FTS 重建收敛为局部 FTS 同步。
- 若先补问答可信度 runtime gate：`TASK-033`
  - 主题：把 groundedness 从离线 eval 前移到 ask 主链路的保守降级控制。
- 若回溯刚完成的 `TASK-047`
  - 主题：已完成；仅剩 assembly trace、diversity overflow 备选池与相关性阈值 eval 覆盖三个 `small` 尾项，不应再单独开一个 `medium`。
- 若回溯刚完成的 `TASK-045`
  - 主题：已完成；仅剩 `replace_section.max_changed_lines` 与 validator 配置化两个 `small` 尾项，不应再单独开一个 `medium`。

## 当前风险

- `TASK-047` 已完成，但仍留有三个 `small` 尾项：`assembly_metadata` 还没有写入结构化 trace，多样性淘汰的 chunk 还没有备选池，相关性阈值比例也还缺离线 eval 覆盖。
- `TASK-045` 已完成，但仍留有两个 `small` 尾项：`replace_section` 的 `max_changed_lines` 安全检查尚未落地，proposal validator 的阈值 / 白名单也还没抽到配置层。
- 控制面与副作用面仍有断口：本地写回成功但后端记账失败时，当前还没有跨会话恢复入口，对应 `TASK-031`。
- scoped ingest 仍会整库重建 `chunk_fts`，一旦 approval 高频触发，成本会持续放大，对应 `TASK-032`。
- ask 的 semantic groundedness 仍只在离线 eval 中暴露，没有进入 runtime 保守 gate，对应 `TASK-033`。
- 本地工作区仍然是脏的：`stash@{0}` 仍在，且根工作区还存在与当前任务无关的已修改 / 未跟踪文件；继续开发前需要明确哪些改动要保留、哪些只是历史或环境产物。

## 默认读取顺序

新会话默认按以下顺序读取：

1. [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
2. [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md)
3. [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md) 中最近相关记录
4. 相关代码入口文件

## 建议先读文件

### 若继续 `TASK-046`

- [backend/app/services/ask.py](backend/app/services/ask.py)
- [backend/app/tools/registry.py](backend/app/tools/registry.py)
- [backend/app/graphs/ask_graph.py](backend/app/graphs/ask_graph.py)
- [backend/app/observability/runtime_trace.py](backend/app/observability/runtime_trace.py)

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
