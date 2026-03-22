# Session Log

## 使用规则

- 本文件用于累计记录多个开发会话，必须持续追加，不允许每次覆盖重写。
- 每次会话都必须分配唯一会话 ID，格式统一为 `SES-YYYYMMDD-XX`。
- 新会话默认追加在文件顶部；旧会话只允许补充勘误，不允许重写结论。
- 从当前版本开始，默认执行规则是：`一个会话只解决一个中等粒度问题`。
- 如果某次会话是“启动会话 / 基线搭建会话”，允许覆盖多个中等粒度问题，但必须在日志中明确标记为例外。
- 所有新会话都必须先绑定 `docs/TASK_QUEUE.md` 中的一个任务项，再开始执行。

## 会话索引

| 会话 ID | 日期 | 主题 | 类型 | 状态 | 对应主文档任务 |
| --- | --- | --- | --- | --- | --- |
| `SES-20260318-07` | 2026-03-18 | 统一 ask / digest / ingest 的入口路由与共享 workflow contract | `Refactor` | `已完成` | `TASK-042` |
| `SES-20260318-06` | 2026-03-18 | 为受限 patch op 落地最小撤销 / 回滚能力 | `Feature` | `已完成` | `TASK-041` |
| `SES-20260318-05` | 2026-03-18 | 建立治理 vs 问答的分场景 benchmark | `Eval` | `已完成` | `TASK-040` |
| `SES-20260318-04` | 2026-03-18 | 将离线 eval 升级到 interview-first P0 基线 | `Eval` | `已完成` | `TASK-039` |
| `SES-20260318-03` | 2026-03-18 | 实现 hybrid retrieval 融合并接入 ask / governance 主链路 | `Feature` | `已完成` | `TASK-038` |
| `SES-20260318-02` | 2026-03-18 | 为 chunk 索引补最小向量写入与向量检索入口 | `Feature` | `已完成` | `TASK-037` |
| `SES-20260318-01` | 2026-03-18 | 为插件补后端自启 / 探活 / 降级启动控制 | `Feature` | `已完成` | `TASK-036` |
| `SES-20260317-07` | 2026-03-17 | 为 `INGEST_STEWARD` 接入 retrieval-backed analyze_consistency | `Feature` | `已完成` | `TASK-035` |
| `SES-20260317-06` | 2026-03-17 | 写回成功后触发 scoped ingest 并刷新索引 | `Feature` | `已完成` | `TASK-030` |
| `SES-20260317-05` | 2026-03-17 | 将后续任务优先级重新对齐到《初步实现指南》的 interview-first MVP | `Docs` | `已完成` | `TASK-034` |
| `SES-20260317-04` | 2026-03-17 | 继续拆解 `TASK-028` 之后的下一批 medium 队列任务 | `Docs` | `已完成` | `TASK-029` |
| `SES-20260317-03` | 2026-03-17 | 为 ask 增加语义级 groundedness 离线评估 | `Eval` | `已完成` | `TASK-028` |
| `SES-20260317-02` | 2026-03-17 | 让 `INGEST_STEWARD` 在 scoped note 上产出首条治理 proposal | `Feature` | `已完成` | `TASK-027` |
| `SES-20260317-01` | 2026-03-17 | 为 `INGEST_STEWARD` 打开 scoped note ingest 入口 | `Feature` | `已完成` | `TASK-026` |
| `SES-20260316-03` | 2026-03-16 | 实现待审批 proposal 查询接口与插件审批收件箱 | `Feature` | `已完成` | `TASK-025` |
| `SES-20260316-02` | 2026-03-16 | 将 `resume_workflow` / `writeback_result` 纳入最小离线 eval | `Eval` | `已完成` | `TASK-024` |
| `SES-20260316-01` | 2026-03-16 | 继续拆解 `TASK-021` 之后的下一批 medium 队列任务 | `Docs` | `已完成` | `TASK-023` |
| `SES-20260315-04` | 2026-03-15 | 构建最小 golden set 与离线 `eval/run_eval.py` | `Eval` | `已完成` | `TASK-021` |
| `SES-20260315-03` | 2026-03-15 | 为 ask 路径补程序级 citation 对齐校验 | `Feature` | `已完成` | `TASK-020` |
| `SES-20260315-02` | 2026-03-15 | 实现插件侧受限写回执行器与 `before_hash` 校验 | `Feature` | `已完成` | `TASK-019` |
| `SES-20260315-01` | 2026-03-15 | 打通 `DAILY_DIGEST` proposal 产出与插件审批面板真实上下文 | `Feature` | `已完成` | `TASK-022` |
| `SES-20260314-14` | 2026-03-14 | 实现插件审批面板与 diff 预览骨架 | `Feature` | `已完成` | `TASK-018` |
| `SES-20260314-13` | 2026-03-14 | 实现 `resume_workflow` 协议与审批中断 contract | `Feature` | `已完成` | `TASK-017` |
| `SES-20260314-12` | 2026-03-14 | 设计并落地 `proposal` / `patch_ops` / `audit_log` 的 SQLite schema | `Feature` | `已完成` | `TASK-016` |
| `SES-20260314-11` | 2026-03-14 | 实现 `digest_graph` 骨架与最小 `DAILY_DIGEST` 返回 | `Feature` | `已完成` | `TASK-014` |
| `SES-20260314-10` | 2026-03-14 | 为 ask / ingest 路径接入 SQLite checkpoint 与 `thread_id` 恢复协议 | `Feature` | `已完成` | `TASK-015` |
| `SES-20260314-09` | 2026-03-14 | 实现 `ingest_graph` 骨架与 `INGEST_STEWARD` workflow 入口 | `Feature` | `已完成` | `TASK-013` |
| `SES-20260314-08` | 2026-03-14 | 继续拆解主计划并登记下一批 medium 队列任务 | `Docs` | `已完成` | `TASK-012` |
| `SES-20260314-07` | 2026-03-14 | 为 ask trace 增加 SQLite `run_trace` 聚合表与最小查询入口 | `Infra` | `已完成` | `TASK-011` |
| `SES-20260314-06` | 2026-03-14 | 落地 ask runtime trace 的 JSONL 持久化骨架 | `Infra` | `已完成` | `TASK-010` |
| `SES-20260314-05` | 2026-03-14 | 实现 `ask_graph` 骨架与 `thread_id` 贯通 | `Feature` | `已完成` | `TASK-009` |
| `SES-20260314-04` | 2026-03-14 | 跑通最小 ask 链路与引用式响应 | `Feature` | `已完成` | `TASK-008` |
| `SES-20260314-03` | 2026-03-14 | 实现 metadata filter 与 candidate 标准格式 | `Feature` | `已完成` | `TASK-007` |
| `SES-20260314-02` | 2026-03-14 | 实现 SQLite FTS5 检索 | `Feature` | `已完成` | `TASK-006` |
| `SES-20260314-01` | 2026-03-14 | 实现最小 ingest pipeline 并写入 SQLite | `Feature` | `已完成` | `TASK-005` |
| `SES-20260312-04` | 2026-03-12 | 设计并落地 `note/chunk` SQLite schema | `Feature` | `已完成` | `TASK-004` |
| `SES-20260312-03` | 2026-03-12 | 完成统一启动入口的真实运行验证 | `Infra` | `已完成` | `TASK-003` |
| `SES-20260312-02` | 2026-03-12 | 收敛 Python 开发环境与统一启动入口 | `Infra` | `部分完成` | `TASK-003` |
| `SES-20260312-01` | 2026-03-12 | 重构会话级任务队列到独立 `TASK_QUEUE.md` | `Docs` | `已完成` | `TASK-002` |
| `SES-20260311-01` | 2026-03-11 | 启动会话：主文档、双端基线、解析器与参考实现对照 | `Bootstrap Exception` | `已完成` | Phase 0、Phase 1 基线、Phase 2/3/4/5 的前置骨架 |

---

## [SES-20260318-07] 统一 ask / digest / ingest 的入口路由与共享 workflow contract

- 日期：2026-03-18
- task_id：`TASK-042`
- 类型：`Refactor`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应任务：`TASK-042`
- 本会话唯一目标：在不重写 ask / ingest / digest 业务节点、不扩成未来任意 workflow 平台的前提下，把现有三条 graph 的公共控制面收敛为共享 workflow runtime contract，统一 `/workflows/invoke` 的入口路由、基础 state、trace/checkpoint 语义与响应装配样板。

### 1. 本次目标

- 把当前 `/workflows/invoke` 中 ask / ingest / digest 三条链路各自分叉的执行样板收口为统一入口，而不是继续在 API 层维护三套并行分支。
- 把现有共享但分散的 runtime 语义进一步显式化，至少统一 graph execution contract、基础 workflow state 与 runtime trace hook 组装方式。
- 在不改变现有三条主链路业务行为的前提下，为后续新增 workflow 降低复制 API / trace / checkpoint / response 样板的成本。

### 2. 本次完成内容

- 复核 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)、[docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)、[docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 与 [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md) 后，确认当前最合适绑定任务为 `TASK-042`；2026-03-18 当天 `SES-20260318-01` 到 `SES-20260318-06` 已占用，因此本次会话使用 `SES-20260318-07`。
- 更新 [backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py)，新增共享 `WorkflowGraphExecution`、`build_base_workflow_state()`、`build_workflow_runtime_trace_hook()` 与 `build_workflow_graph_execution()`，把 ask / ingest / digest 三条 graph 的公共执行上下文、基础 state 与 trace hook 组装统一收口。
- 更新 [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)、[backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py) 与 [backend/app/graphs/digest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/digest_graph.py)，让 `AskGraphExecution` / `IngestGraphExecution` / `DigestGraphExecution` 统一继承共享 execution contract，并改为复用共享 base state 与 runtime trace hook；业务节点、proposal 生成和 waiting 语义保持不变。
- 更新 [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)，把 `/workflows/invoke` 从三个大分支改为 handler registry + 统一 invoker / outcome builder / response builder，保留原有 ask / ingest / digest 的 completed / waiting / resume 语义。
- 更新 [backend/app/graphs/__init__.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/__init__.py)，导出共享 `WorkflowGraphExecution`，避免多入口继续各自拼装 execution 类型。
- 新增 [backend/tests/test_workflow_invoke_contract.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_workflow_invoke_contract.py)，并更新 [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)、[backend/tests/test_ingest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ingest_workflow.py) 与 [backend/tests/test_digest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_digest_workflow.py)，把共享 execution 字段与统一 invoke contract 的多入口响应形状固定下来。

### 3. 本次未完成内容

- 没有把 ask / ingest / digest 进一步抽成“任意新 workflow 可注册”的通用平台；当前 registry 仍只服务现有三条主链路。
- 没有顺手把 waiting / proposal / resume / rollback 全部统一成更大的 runtime 框架；本次只收口到 invoke 入口、共享 execution contract 与基础 state / trace 语义。
- 没有处理 `KS_ASK_RUNTIME_TRACE_PATH` / `ask_runtime.jsonl` 的历史命名包袱；虽然现在三条 workflow 已共用一套 trace hook 组装，但配置名仍沿用 ask 时期的旧命名。
- 没有新增 ask proposal、跨会话恢复、增量 FTS 或 groundedness gate；这些仍分别留在 `TASK-031`、`TASK-032`、`TASK-033` 和既有 small 派生项里。

### 4. 关键决策

- 没有把这次统一做成“重写三条 graph”的大手术，而是优先收敛公共控制面；原因是当前真正重复的是入口分派、execution 包装、基础 state 与 response 组装，不是业务节点本身。
- 没有直接上未来任意 workflow 都可插拔的 registry 框架；原因是当前只有 ask / ingest / digest 三条链路，先把现有重复样板压实，比提前设计过宽平台更可控。
- 没有把 waiting / proposal 分支也强行做成完全同构；原因是 `INGEST_STEWARD` 与 `DAILY_DIGEST` 的审批语义虽然相近，但 ask 当前并不 proposal 化，过度抽象会把本会话扩成新的 medium。
- 没有为统一 contract 改动外层 `WorkflowInvokeResponse` 结构；原因是当前目标是“收敛内部控制面”，不是对外再开一个兼容性迁移面。

### 5. 修改过的文件

- [backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py)
- [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)
- [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)
- [backend/app/graphs/digest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/digest_graph.py)
- [backend/app/graphs/__init__.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/__init__.py)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/tests/test_workflow_invoke_contract.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_workflow_invoke_contract.py)
- [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)
- [backend/tests/test_ingest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ingest_workflow.py)
- [backend/tests/test_digest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_digest_workflow.py)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 6. 验证与测试

- 跑了什么命令
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_workflow_invoke_contract tests.test_ask_workflow tests.test_ingest_workflow tests.test_digest_workflow -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m compileall app tests`
- 结果如何
  - 定向 37 条测试全部通过，覆盖共享 invoke contract、ask / ingest / digest execution 字段与 waiting / completed 主链路。
  - backend 全量 77 条测试通过，没有引入 ask / ingest / digest / resume / retrieval 回归。
  - `compileall` 通过，没有留下 Python 语法问题。
- 哪些没法验证
  - 没有在真实 Obsidian 宿主里手工触发一次 ask / ingest / digest 的三入口联调；当前验证主要停留在 backend contract 与 unittest。
  - 没有验证新增第四条 workflow 的真实接入成本；本次只证明现有三条链路已共用控制面。
- 哪些只是静态修改
  - [backend/app/graphs/__init__.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/__init__.py)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 7. 范围偏移与原因

- 没有发生超出 `TASK-042` 的 `medium` 级偏移。
- 伴随改动包括：
  - 为三条 graph 补统一 execution contract
  - 为 `/workflows/invoke` 补 handler registry 与共享 response builder
  - 为多入口共享 contract 增加最小测试
- 这些改动都直接服务于“统一 workflow contract、减少新增 workflow 样板复制、保持现有行为不回退”的验收标准，不构成新的中等功能。

### 8. 未解决问题

- 当前 `KS_ASK_RUNTIME_TRACE_PATH` 与 `data/traces/ask_runtime.jsonl` 的命名仍会误导后续维护者，以为 trace 只服务 ask；这已经从实现重复问题收敛成命名债。
- 当前 handler registry 统一的是 ask / ingest / digest 三条既有链路，但 future workflow 的 waiting / proposal / rollback 语义是否还能继续复用同一层 outcome builder，尚未被更多实例验证。
- ask 仍未 proposal 化，因此共享 contract 目前并没有把“所有 workflow 都可能进入 approval”变成真实事实。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果后续会话把这次改动包装成“已经有完整 workflow 平台”，会被直接追问穿。真实边界仍是“现有三条 graph 共用一套 runtime contract 和入口控制面”，不是 supervisor 或任意插件式平台。
- 技术债：trace 配置命名仍然带 ask 历史包袱，后续若继续扩 workflow 数量，命名误导会再次诱发复制式配置。
- 技术债：共享 outcome builder 目前仍保留 action 级差异分支；如果未来 waiting / completed / proposal 语义继续增长，可能还需要再抽一层显式的 workflow spec。
- 假设：interview-first 保留主线到 `TASK-042` 已全部收口；如果继续推进 medium 任务，默认应回到已后移的 `TASK-031`、`TASK-032`、`TASK-033`，而不是重新发明新的主线。

### 10. 下一步最优先任务

1. 若继续推进 medium 主线，先回到 `TASK-031`，补“本地写回成功但 `/workflows/resume` 失败”的跨会话恢复入口。
2. 之后进入 `TASK-032`，把 scoped ingest 从整库 FTS 重建收敛为真正的局部 FTS 同步。
3. 再推进 `TASK-033`，把 ask 的 groundedness 风险从离线 eval 推进到 runtime gate。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py)
- [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)
- [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)
- [backend/app/graphs/digest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/digest_graph.py)
- [backend/tests/test_workflow_invoke_contract.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_workflow_invoke_contract.py)
- [backend/tests/test_resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_resume_workflow.py)

### 12. 当前最容易被面试官追问的点

- 你说统一 workflow contract，到底统一了什么？如果只是把三个 `if` 抽成 helper，这不叫平台化。你必须能准确说出：共享了 `WorkflowGraphExecution`、基础 workflow state、runtime trace hook 组装、handler registry 和统一 response builder，且这些收敛点分别消掉了哪类样板。
- 为什么这次没有把 waiting / proposal / resume / rollback 也一起抽成完整 runtime 框架？如果回答成“先这样简单做”，会像没做过复杂系统。正确回答必须落到 scope control：这次目标是先收敛现有三条链路公共控制面，避免把会话扩成新的平台设计题。
- 新增第四条 workflow 时，到底还有哪些代码要写？如果答不出“业务 graph 包装 + outcome 特有字段映射”之外大部分 invoke 样板已经消失，会显得你没有真正衡量抽象收益。
- `KS_ASK_RUNTIME_TRACE_PATH` 现在还叫 ask，你却说 runtime contract 已统一，这说明什么？如果回答不出，会暴露你只收了代码层重复，却没意识到配置命名仍可能诱导未来维护者再复制一套。
- 为什么不直接改外层 `WorkflowInvokeResponse` 结构？如果回答只是“怕麻烦”，会显得没有兼容意识。正确答案要落到：这次优先收敛内部控制面，先守住现有 API 兼容，再决定是否值得开第二轮协议迁移。

---

## [SES-20260318-06] 为受限 patch op 落地最小撤销 / 回滚能力

- 日期：2026-03-18
- task_id：`TASK-041`
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应任务：`TASK-041`
- 本会话唯一目标：在不扩成 completed history、跨会话回放平台、三方合并或多文件事务回滚的前提下，为当前已支持的 `merge_frontmatter` / `insert_under_heading` 受限写回链路补最小可执行 rollback。

### 1. 本次目标

- 让当前两类受限 patch op 至少存在一条保守、可执行的最小撤销路径，而不是继续只有“能改”没有“能撤”。
- 在 rollback 前继续校验目标文件状态，避免文件已经漂移时误覆盖用户后续修改。
- 把 rollback 成功 / 失败结果写入最小审计事实，并对成功 rollback 更新 checkpoint 状态。

### 2. 本次完成内容

- 复核 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)、[docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)、[docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 与 [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md) 后，确认当前最合适绑定任务为 `TASK-041`；2026-03-18 当天 `SES-20260318-01` 到 `SES-20260318-05` 已占用，因此本次会话使用 `SES-20260318-06`。
- 更新 [plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts)，把正向写回执行器扩成 `LocalWritebackExecution`：在真实落盘前抓取 `LocalRollbackContext`，并新增 `rollbackProposalWriteback()`，仅当当前文件仍命中精确 `after_hash` 时才允许恢复整文快照。
- 更新 [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)、[plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts) 与 [plugin/src/api/client.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/api/client.ts)，新增 `WorkflowRollbackRequest/Response` 与插件侧 `rollbackWorkflow()` API 客户端。
- 新增 [backend/app/services/rollback_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/rollback_workflow.py)，并在 [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py) 中新增 `POST /workflows/rollback`：
  - 只允许对已有 successful `writeback_result` 的 completed checkpoint 记 rollback
  - rollback 失败也会进入 append-only `audit_log`
  - 只有 successful rollback 才会把 `rollback_result` 与 `rollback_audit_event_id` 回写到 checkpoint，避免一次失败尝试锁死后续合法重试
- 更新 [backend/app/graphs/state.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/state.py) 与 [backend/app/graphs/checkpoint.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/checkpoint.py)，让 rollback 结果进入最小持久化状态。
- 更新 [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)，在 approval 成功后补最小 rollback 区块，并保留“本地 rollback 已成功但后端同步失败时只重试同步、不重复改文件”的保护。
- 更新 [backend/tests/test_resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_resume_workflow.py)，新增：
  - successful rollback 会写 audit + checkpoint 的断言
  - 文件漂移导致 rollback 拒绝时，仍会写 audit，但不会污染 checkpoint 的断言

### 3. 本次未完成内容

- 没有为历史 / 推断为“已应用”的写回补跨会话可执行 rollback；当前 rollback 仍依赖当前插件会话内抓到的本地快照。
- 没有在 rollback 成功后自动触发 scoped ingest 刷新；当前索引可能短时仍停留在 rollback 前状态。
- 没有补 reviewer-facing rollback diff 预览；这继续保留为 `TASK-041` 的 `small` 派生项。
- 没有在真实 Obsidian 宿主里手工点击一次 `Approve -> Rollback -> /workflows/rollback` 的端到端交互验证。

### 4. 关键决策

- 没有把 rollback 做成“根据 patch 反推逆操作”的通用引擎，而是先用插件本地快照恢复；原因是当前 `merge_frontmatter` 只记录 patch，不记录旧值，直接反推会把会话扩成更大的状态设计问题。
- 没有让 rollback 在文件已漂移时继续尝试智能 merge；原因是此时最危险的不是“撤不回去”，而是“把用户后续手动修改覆盖掉”。首版必须保守拒绝。
- 没有把 rollback 硬塞进 `/workflows/resume`，而是新增 `/workflows/rollback`；原因是审批恢复和已完成副作用的回滚记账属于不同控制面，继续混在一个 endpoint 里会让状态语义更乱。
- 没有在 rollback 失败时改写 completed checkpoint；原因是失败尝试只是“试图撤销”，不是“已经撤销”。如果把失败也写成最终状态，会直接堵死后续合法重试。

### 5. 修改过的文件

- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/app/graphs/state.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/state.py)
- [backend/app/graphs/checkpoint.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/checkpoint.py)
- [backend/app/services/rollback_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/rollback_workflow.py)
- [backend/tests/test_resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_resume_workflow.py)
- [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)
- [plugin/src/api/client.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/api/client.ts)
- [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)
- [plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 6. 验证与测试

- 跑了什么命令
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_resume_workflow -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m compileall app`
  - `cd plugin && npm test`
  - `cd plugin && npm run build`
- 结果如何
  - `tests.test_resume_workflow` 12 个测试全部通过，覆盖 approve / reject / writeback success / writeback failure / rollback success / rollback refusal。
  - backend 全量 75 个测试通过，没有引入 ask / ingest / digest / eval / retrieval 回归。
  - `compileall` 通过，没有留下 Python 语法问题。
  - plugin `npm test` 8 个测试通过，`npm run build` 通过。
- 哪些没法验证
  - 没有在真实 Obsidian 宿主里手工验证 rollback 按钮、Notice 和面板冻结行为。
  - 没有验证 rollback 成功后索引刷新，因为本次没有实现 post-rollback scoped ingest。
- 哪些只是静态修改
  - [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
  - [backend/app/graphs/state.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/state.py)
  - [backend/app/graphs/checkpoint.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/checkpoint.py)
  - [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)
  - [plugin/src/api/client.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/api/client.ts)

### 7. 范围偏移与原因

- 没有发生超出 `TASK-041` 的 `medium` 级偏移。
- 伴随改动包括：
  - 为 rollback 新增独立 backend endpoint
  - 为 checkpoint state 增加 `rollback_result`
  - 为插件面板增加 rollback 入口和防重同步保护
- 这些改动都直接服务于“最小可执行 rollback + 审计 + 状态校验”验收标准，不构成新的中等功能。

### 8. 未解决问题

- 当前 rollback 依赖当前插件进程内的 `LocalRollbackContext`；插件重启后，历史 successful writeback 仍只有 audit，没有可执行 rollback。
- rollback 成功后当前不会自动触发 scoped ingest，因此 DB / FTS 可能仍保留 rollback 前内容。
- rollback 仍是整文快照恢复，不支持用户手动编辑与系统 patch 的混合场景下做局部智能 merge。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果外部叙事把这版 rollback 说成“完整回滚系统”，会被直接追问穿。真实边界只是“当前插件会话内、两类受限 patch op、命中精确 after_hash 时的保守 rollback”。
- 技术债：当前 audit 已能记录 rollback 成功 / 失败，但 rollback 成功后还没有索引一致性补偿；这会让 Vault 与 SQLite/FTS 出现短时分叉。
- 技术债：`WritebackResult` 被 rollback 复用为回滚结果结构，首版足够省事，但语义上仍偏“副作用结果”而不是“专门的 rollback event”；后续若要扩 completed history 或 diff 预览，可能需要更清晰的事件模型。
- 假设：下一次主线 medium 会话应直接前移到 `TASK-042`，统一 ask / digest / ingest 的 workflow contract，而不是回头把 `TASK-041` 扩成 completed history 或跨会话 rollback 平台。

### 10. 下一步最优先任务

1. 绑定 `TASK-042`，统一 ask / digest / ingest 的入口路由与共享 workflow contract。
2. `TASK-042` 完成后，再视优先级回到 `TASK-041` 的既有 `small` 派生项，例如 rollback diff 预览和 post-rollback scoped ingest。
3. 保持 `TASK-031`、`TASK-032`、`TASK-033` 继续后移，不要把跨会话恢复、增量 FTS 或 groundedness gate 混回当前 rollback 任务。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/app/graphs/state.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/state.py)
- [backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)
- [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)
- [backend/tests/test_ingest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ingest_workflow.py)
- [backend/tests/test_digest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_digest_workflow.py)

### 12. 当前最容易被面试官追问的点

- 你这个 rollback 为什么只能在当前插件会话里做？如果回答成“先这样实现比较简单”，会像没做过副作用系统。正确回答必须落到：`merge_frontmatter` 当前没有旧值快照，历史 writeback 只有 patch 和 hash，不足以可靠恢复，所以首版必须把“可执行 rollback”收窄到本地真实写回时抓到的快照。
- 你为什么不用 patch 反推逆操作，而要整文快照恢复？如果回答成“我懒得做”，会直接掉分。你要说清楚：当前两类 patch 的可逆性并不对称，尤其 frontmatter merge 不保留旧值；在这个阶段强行泛化逆操作，极容易把任务扩成不可靠的半成品。
- rollback 为什么命中 `after_hash` 失败就直接拒绝？如果回答只是“为了安全”，会太空。你必须进一步说：这里防的不是技术异常，而是用户在 writeback 之后又手动改了文件；此时任何自动覆盖都可能抹掉真实用户编辑，拒绝撤销比误撤销更可接受。
- rollback 失败为什么也要写 audit？如果回答不出，会显得你对控制面没概念。正确解释是：失败 rollback 本身就是重要操作事实，它说明系统尝试过恢复且被边界保护拦住；这对排障、审计和后续人工介入都关键。
- 现在你能不能说“写回链路已经完整可恢复”？如果回答“可以”，会像包装项目。真实答案必须承认：当前只证明“当前插件会话里的最小 rollback”成立，跨会话恢复、rollback 后索引一致性补偿和 completed history 仍没做。

---

## [SES-20260318-05] 建立治理 vs 问答的分场景 benchmark

- 日期：2026-03-18
- task_id：`TASK-040`
- 类型：`Eval`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应任务：`TASK-040`
- 本会话唯一目标：在不把范围扩成 markdown 报告导出、在线 judge、runtime gate 或 benchmark 平台的前提下，把现有离线 eval 从“全局平均 + case 明细”升级到“问答链路 vs 治理链路”的分场景 benchmark。

### 1. 本次目标

- 把现有 `ask / governance / digest / resume_workflow` case 显式收敛成对面试叙事有用的两条 benchmark 主线，而不是继续只有全局 `metric_overview`。
- 为不同场景补最小 `core_metrics` 与 `failure_type_breakdown`，避免结果文件只能回答“过没过”，不能回答“哪条链路更稳、主要坏在哪”。
- 保持现有 golden case、脚本化回归与 unittest 能稳定复用，不引入新的外部依赖。

### 2. 本次完成内容

- 复核 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)、[docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)、[docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 与 [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md) 后，确认当前最合适绑定任务为 `TASK-040`；当天已有 `SES-20260318-01` 到 `SES-20260318-04`，因此本次会话使用未占用的 `SES-20260318-05`。
- 更新 [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)，把结果 schema 升到 `1.3`，新增 `benchmark_overview`，并显式把现有 case 映射为 `question_answering` 与 `governance` 两套 benchmark。
- 在 [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py) 中新增 `scenario_overview`、场景级 `core_metrics` 与最小 `failure_type_breakdown`：ask 会输出 `generated_answer_rate / retrieval_only_rate / unsupported_claim_rate`，governance / digest / resume_workflow 会分别输出 proposal、fallback、writeback outcome 等核心指标。
- 在 [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py) 中把 `proposal` 快照补成显式 `present=true`，避免治理 benchmark 继续依赖“非空字典即 proposal 存在”的隐式约定。
- 更新 [backend/tests/test_eval_runner.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_eval_runner.py)，补齐 benchmark 分组、digest / governance / resume KPI 与 failure type 断言。
- 生成真实结果文件 [eval/results/eval-20260318-064721.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/results/eval-20260318-064721.json)，确认全量 18 条 case 在新 schema 下全部通过，并已能输出 `question_answering` 与 `governance` 两套 benchmark 视图。

### 3. 本次未完成内容

- 没有补 `TASK-040` 的派生 `small`：markdown 报告导出。
- 没有为 `run_eval.py` 增加按 benchmark 直接过滤的 CLI 参数。
- 没有接入 Ragas、LLM judge、真实联网 provider E2E 或 Obsidian 宿主级端到端 benchmark。

### 4. 关键决策

- 没有把 benchmark 分成四套完全独立报告，而是先收敛为“问答 vs 治理”两大类；原因是 `TASK-040` 的验收目标是服务当前面试叙事，先证明两条主链路的质量边界，而不是做完整评测平台。
- 没有把 failure type 分类建立在自由文本语义归纳上，而是优先复用现有稳定信号，例如 `model_fallback_reason`、`retrieval_fallback_reason`、`ask_groundedness.bucket`、`digest_result.fallback_reason` 与 `writeback_result.error`；原因是首版 benchmark 的重点是可重复、可回归，而不是“分类看起来很聪明”。
- 没有新发明一套 benchmark case 协议，而是继续复用 golden case 里的 `scenario` 字段；原因是这次要补的是汇总层，不是再造一层 case 描述 DSL。
- 没有顺手改业务主链路，也没有把 ask / governance 的 runtime gate 混进来；原因是本次任务边界是“离线 benchmark 解释力”，不是线上行为收敛。

### 5. 修改过的文件

- [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
- [backend/tests/test_eval_runner.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_eval_runner.py)
- [eval/results/eval-20260318-064721.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/results/eval-20260318-064721.json)

### 6. 验证与测试

- 跑了什么命令：
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_eval_runner -v`
  - `./.conda/knowledge-steward/bin/python eval/run_eval.py`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
- 结果如何：
  - `test_eval_runner` 5 个测试全部通过，覆盖 benchmark 分组、governance / digest / resume KPI 与 failure type 汇总。
  - 全量 eval 18 条 case 全部通过，并生成 [eval/results/eval-20260318-064721.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/results/eval-20260318-064721.json)。
  - 后端全量 73 个测试全部通过，没有引入 ask / ingest / digest / resume / retrieval 回归。
- 哪些没法验证：
  - 没有验证真实联网 judge、真实 provider 或 Obsidian 宿主下的 benchmark 消费链路。
- 哪些只是静态修改：
  - `benchmark_overview`、场景级 `core_metrics` 与 `failure_type_breakdown` 的结果 schema 扩展，主要通过 unittest 与离线脚本回归验证，没有新增 UI 或宿主交互验证。

### 7. 范围偏移与原因

- 没有发生超出 `TASK-040` 边界的 `medium` 级偏移。
- 伴随改动只包括 `proposal.present` 显式语义补齐和测试更新；这是为了让治理 benchmark 能稳定统计 proposal 产出率，而不是另起新任务。

### 8. 未解决问题

- 当前 benchmark 已能解释“问答 vs 治理”，但还没有 markdown 报告导出，面试前复盘仍需要直接读 JSON。
- 当前 failure type 仍基于稳定信号映射，不是更强的 judge 或人工标签；它解决了“没有分类”的问题，但还没有解决“更细粒度语义归因”的问题。
- `question_answering` 与 `governance` 两套 benchmark 已经可用，但治理大类内部仍混合了 governance / digest / resume_workflow 三种场景；如果后续要做更细的对外展示，需要额外设计报告层，而不是继续往本轮任务里塞字段。

### 9. 新增风险 / 技术债 / 假设

- 技术债：结果 schema 已升到 `1.3`，任何消费 `eval/results/*.json` 的文档或后续脚本都需要同步认识 `benchmark_overview`，否则会继续按 `1.2` 理解结果。
- 风险：当前 failure type 统计仍是 deterministic signal aggregation；如果以后引入更复杂的错误模式，但不治理信号源，benchmark 解释力会再次下降。
- 假设：当前“ask -> question_answering，governance / digest / resume_workflow -> governance”的分组能满足当前 interview-first 叙事；若后续要拆成更多 benchmark，应另行登记，而不是在 `TASK-040` 内持续膨胀。

### 10. 下一步最优先任务

1. 绑定 `TASK-041`，为受限 patch op 落地最小撤销 / 回滚能力。
2. `TASK-041` 完成后，再进入 `TASK-042`，统一 ask / digest / ingest 的 workflow contract。
3. 若后续要补 markdown 报告导出，可作为 `TASK-040` 的既有 `small` 派生项单独处理，不要和 `TASK-041` 混做。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts)
- [plugin/src/writeback/helpers.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/helpers.ts)
- [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py)
- [backend/tests/test_resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_resume_workflow.py)
- [eval/results/eval-20260318-064721.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/results/eval-20260318-064721.json)

### 12. 当前最容易被面试官追问的点

- 你为什么把 `digest` 和 `resume_workflow` 也放进 governance benchmark，而不是单独再切三套报告？如果回答成“我觉得都算治理”，会像没想清楚 benchmark 的决策用途。正确回答必须落到工程目标：这轮是 interview-first 两大主线，不是评测平台。
- 你这个 `failure_type_breakdown` 到底是不是靠谱？如果回答只有“我做了分类统计”，会显得很虚。你必须说清楚它依赖的是哪些稳定信号、哪些只是首版保守代理、为什么现在不直接上 judge。
- 为什么 `question_answering` 的 `unsupported_claim_rate=0.25`、`retrieval_only_rate=0.5` 仍然算可接受？如果回答成“测试都过了就行”，会暴露你没有质量意识。正确回答必须指出：benchmark 的价值是揭示边界，不是把所有问题藏成通过率。


## [SES-20260318-04] 将离线 eval 升级到 interview-first P0 基线

- 日期：2026-03-18
- task_id：`TASK-039`
- 类型：`Eval`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应任务：`TASK-039`
- 本会话唯一目标：在不把范围扩成 benchmark 平台、在线 judge、dashboard 或 runtime gate 的前提下，把现有离线 eval 从“13 条最小 baseline”升级到 interview-first P0 水位。

### 1. 本次目标

- 扩容 golden set，不再只停留在 ask / digest / resume 的最小 contract 回归。
- 把治理链路显式纳入离线 eval，覆盖 ask / governance / digest / resume-writeback 四类核心场景。
- 为结果 JSON 增加最小可解释指标，而不是继续只有 selected / passed / failed 计数。

### 2. 本次完成内容

- 复核 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)、[docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)、[docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 与 [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md) 后，确认当前最合适绑定任务为 `TASK-039`；当天已有 `SES-20260318-01`、`02`、`03`，因此本次会话使用未占用的 `SES-20260318-04`。
- 更新 [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)，把结果 schema 升到 `1.2`，新增 `quality_metrics` 与全局 `metric_overview`，并为 ask / governance / digest / resume case 统一输出最小 `faithfulness`、`relevancy`、`context_precision`、`context_recall`。
- 在 [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py) 中新增 deterministic fixture、prewarm ingest 与 embedding mock profile，确保 hybrid retrieval 能在离线回归里稳定命中，而不是只覆盖 FTS fallback。
- 更新 [eval/golden/ask_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/ask_cases.json)，为既有 grounded / semantic overclaim case 补充质量指标断言，并新增 `ask_fixture_hybrid_retrieval_only` 覆盖 hybrid candidate 命中。
- 更新 [eval/golden/digest_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/digest_cases.json)，为 structured result / waiting proposal 场景补充 `quality_reference` 与指标断言。
- 新增 [eval/golden/governance_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/governance_cases.json)，把 `INGEST_STEWARD` 的 waiting proposal 与 no-proposal fallback 纳入离线回归，并显式断言 retrieval-backed analysis evidence 与 hybrid related candidate。
- 更新 [backend/tests/test_eval_runner.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_eval_runner.py)，新增 hybrid / governance / `metric_overview` 断言。
- 生成真实结果文件 [eval/results/eval-20260318-060855.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/results/eval-20260318-060855.json)，本轮全量 18 条 case 全部通过。

### 3. 本次未完成内容

- 没有接入 Ragas、LLM judge 或任何在线评测服务。
- 没有把本次会话扩成 `TASK-040` 的分场景 benchmark、失败类型聚合或对外报告视图。
- 没有补真实 Obsidian 宿主端到端自动化，也没有把 groundedness / faithfulness gate 接进 ask runtime。

### 4. 关键决策

- 没有把指标实现绑定到在线 judge，而是先落本地、可解释、可重复的等价指标；原因是 `TASK-039` 的核心目标是把 baseline 变成稳定可回归资产，而不是引入额外的不确定外部依赖。
- 没有只扩 deterministic fixture，也没有只扩真实 `sample_vault` case，而是继续采用“真实样本 + deterministic bad case”混合策略；原因是前者负责验证业务贴近度，后者负责稳定覆盖坏路径。
- 没有在主链路代码里顺手插入新的 runtime gate；原因是本次目标是评估闭环，不是改 ask / governance 的线上行为边界。
- 没有把 `TASK-039` 顺手做成 `TASK-040`；原因是这轮先收口 baseline、样本覆盖与指标 contract，分场景 benchmark 和失败类型统计属于下一层任务。

### 5. 修改过的文件

- [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
- [eval/golden/ask_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/ask_cases.json)
- [eval/golden/digest_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/digest_cases.json)
- [eval/golden/governance_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/governance_cases.json)
- [backend/tests/test_eval_runner.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_eval_runner.py)

### 6. 验证与测试

- 跑了什么命令：
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_eval_runner -v`
  - `./.conda/knowledge-steward/bin/python eval/run_eval.py`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
- 结果如何：
  - `test_eval_runner` 5 个测试全部通过，覆盖 case 过滤、groundedness 分桶、hybrid / governance 指标输出与 `metric_overview`。
  - 全量 eval 18 条 case 全部通过，并生成 [eval/results/eval-20260318-060855.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/results/eval-20260318-060855.json)。
  - 后端全量 73 个测试全部通过，没有回归 ask / ingest / digest / resume / retrieval 既有行为。
- 哪些没法验证：
  - 没有验证真实外部 judge、真实联网 provider 或 Obsidian 宿主端到端场景进入这轮 eval。
- 哪些只是静态修改：
  - 结果 schema、golden case 与测试断言的结构调整，主要通过脚本回归和 unittest 验证，没有新增 UI / 宿主侧交互验证。

### 7. 范围偏移与原因

- 没有发生超出 `TASK-039` 边界的 `medium` 级偏移。
- 伴随改动只包括 eval fixture / case / runner / 测试补齐，以及为了稳定覆盖 hybrid retrieval 所需的最小 embedding mock / prewarm 适配，这些都属于完成 P0 eval baseline 所必需的局部改动。

### 8. 未解决问题

- 当前 `quality_metrics` 仍是本地等价实现，不是外部 judge；它解决了“没有指标”的问题，但还没有解决“如何做更强语义评审”的问题。
- 全量结果里的 `context_precision` 平均值只有 `0.4479`；这不表示回归失败，但说明下一步必须进入 `TASK-040` 做分场景解释，而不能把单个全局均值包装成“系统已经很强”。
- 当前 hybrid eval 通过 deterministic embedding mock 达成稳定回归，但还没有补 coverage / ready 观测，也没有真实联网 provider E2E。

### 9. 新增风险 / 技术债 / 假设

- 技术债：本地等价指标可重复、可解释，但对开放语义质量的刻画仍弱于人工评审或更强 judge。
- 风险：如果后续不尽快把 `TASK-040` 做成分场景 benchmark，当前 `metric_overview` 会停留在“有全局平均值，但治理 vs 问答不可区分”的中间状态。
- 假设：后续 benchmark 会继续复用本轮的 `schema_version=1.2` 结果结构，而不是重新发明第二套 eval 输出协议。

### 10. 下一步最优先任务

1. 绑定 `TASK-040`，把当前 baseline 结果正式切成治理 vs 问答的分场景 benchmark。
2. 继续保留 `TASK-041`、`TASK-042` 作为当前仅存的其余 P1，不在下一会话回头扩 `TASK-031` 到 `TASK-033`。
3. 若后续要引入更强 judge 或 runtime gate，应另行登记，不要把它们伪装成 `TASK-040` 的顺手小改。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
- [eval/golden/governance_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/governance_cases.json)
- [eval/golden/ask_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/ask_cases.json)
- [backend/tests/test_eval_runner.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_eval_runner.py)
- [eval/results/eval-20260318-060855.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/results/eval-20260318-060855.json)

### 12. 当前最容易被面试官追问的点

- 你说自己做了 `faithfulness / relevancy / context` 指标，这些分数到底基于什么 ground truth？如果回答成“参考了 Ragas，所以应该差不多”，会像没真正做过评估系统。
- 为什么治理 proposal / resume-writeback 这种非纯 QA 链路，也能谈 `relevancy` 和 `context_precision`？如果回答只有“统一都打一套分”，会暴露你没有认真定义指标边界。
- 你怎么证明 hybrid retrieval 真被 eval 覆盖了，而不是大多数 case 仍在向量禁用时退回 FTS？如果回答不出 embedding mock、prewarm ingest 和 `retrieval_source` 断言，会显得回归只是在跑 happy path。
- 为什么 `TASK-039` 没顺手做成 benchmark？正确回答必须落到 scope control：本轮先补 baseline、样本覆盖和结果 schema；场景聚合、失败类型统计和对外报告是 `TASK-040`，不是顺手完成的附属物。

## [SES-20260318-03] 实现 hybrid retrieval 融合并接入 ask / governance 主链路

- 日期：2026-03-18
- task_id：`TASK-038`
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应任务：`TASK-038`
- 本会话唯一目标：在不把范围扩成 reranker、ANN、复杂 query planner 或 eval 基线升级的前提下，把现有 FTS / metadata filter 与 `sqlite_vector` 融合成最小 hybrid retrieval，并接入 ask 与至少一条治理链路。

### 1. 本次目标

- 新增统一 hybrid retrieval 入口，复用现有 `RetrievedChunkCandidate` / `RetrievalSearchResponse` contract，而不是让 ask 和治理分析各自拼接两路检索结果。
- 让 ask 路径改为消费 hybrid candidate，同时保持现有 retrieval fallback、citation 对齐校验与 `retrieval_only` 降级语义不回退。
- 让 `INGEST_STEWARD` 的 related retrieve 也能复用 hybrid candidate 作为 analysis evidence，并在向量不可用时稳定退回 FTS。

### 2. 本次完成内容

- 复核 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)、[docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)、[docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 与 [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md) 后，确认当前最合适绑定任务为 `TASK-038`；当天已有 `SES-20260318-01` 与 `SES-20260318-02`，因此本次会话使用未占用的 `SES-20260318-03`。
- 新增 [backend/app/retrieval/hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/hybrid.py)，落地最小 hybrid 检索入口：统一调度 `sqlite_fts` 与 `sqlite_vector`，使用 rank-based RRF 融合去掉分数量纲差异，并在双路命中时输出 `retrieval_source=hybrid_rrf`。
- 在 [backend/app/retrieval/hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/hybrid.py) 中把 metadata filter fallback 收敛到 hybrid 总入口统一处理，避免 FTS / vector 各自放宽条件后产生不一致 candidate 集合。
- 更新 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)，让 `run_minimal_ask()` 从纯 FTS 切到 hybrid candidate，同时保持现有 `generated_answer / retrieval_only / no_hits` 三种返回模式不变。
- 更新 [backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py) 与 [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)，让 scoped ingest proposal 的 related retrieve 改走 hybrid，并显式透传运行态 `settings / provider_preference`，避免治理路径绕过向量配置。
- 新增 [backend/tests/test_retrieval_hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_retrieval_hybrid.py)，覆盖 hybrid 命中、向量不可用时退回 FTS 与共享 metadata filter fallback。
- 更新 [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py) 与 [backend/tests/test_ingest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ingest_workflow.py)，分别覆盖 ask 消费 hybrid candidate、以及治理 analysis 使用 hybrid related evidence 的分支。

### 3. 本次未完成内容

- 没有实现 reranker，也没有把本次会话扩成 cross-encoder 或复杂 query planner。
- 没有引入 ANN、外部向量库或更高性能的向量索引结构；当前仍保持 SQLite 持久化 + Python 余弦 + RRF 融合的 MVP 方案。
- 没有做真实云 / 本地 embedding provider 的联网 E2E 验证；当前验证范围仍停留在本地单元测试和静态编译。
- 没有补向量 coverage / ready 的显式观测，也没有暴露 branch score / fusion snapshot 的调试输出。

### 4. 关键决策

- 没有直接用 FTS 分数和 cosine 分数做线性加权，而是先用 RRF 做 rank-based 融合；原因是当前两路检索分数量纲不同，硬相加会把本会话扩成调参和校准问题。
- 没有在 ask 与治理分析里各自实现一套融合逻辑，而是新增单独的 [backend/app/retrieval/hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/hybrid.py)；原因是 filter fallback、重复 chunk 去重和向量禁用降级语义必须先收敛为统一底座。
- 没有把向量分支的 `disabled_reason` 继续向上暴露成 ask / governance 主链路错误，而是维持“向量不可用时稳定退回 FTS”的安全边界；原因是 `TASK-038` 的验收目标是补共享检索底座，不是把向量可用性提升为主链路强依赖。
- 没有新增第二套 candidate contract，而是继续复用 `RetrievedChunkCandidate`，只用 `retrieval_source=hybrid_rrf` 区分双路融合命中；原因是让 `TASK-039` 的 eval 和后续 rerank 都建立在已经稳定的候选协议上。

### 5. 修改过的文件

- [backend/app/retrieval/hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/hybrid.py)
- [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)
- [backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py)
- [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)
- [backend/tests/test_retrieval_hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_retrieval_hybrid.py)
- [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)
- [backend/tests/test_ingest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ingest_workflow.py)

### 6. 验证与测试

- 跑了什么命令：
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_retrieval_fts tests.test_retrieval_vector tests.test_retrieval_hybrid tests.test_ask_workflow tests.test_ingest_workflow -v`
  - `cd backend && PYTHONPYCACHEPREFIX=/tmp/ks-pycache ../.conda/knowledge-steward/bin/python -m compileall app tests`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
- 结果如何：
  - 目标测试集通过，共 37 条测试覆盖 retrieval / ask / ingest 与新增 hybrid 分支。
  - `compileall` 通过，新增 `hybrid.py` 与测试可完成静态编译。
  - 后端全量 72 条测试通过，未观察到 hybrid 接线导致的 ask / ingest / resume / eval 回归。
- 哪些没法验证：
  - 没有对真实 embedding provider 做联网调用验证，因此还不能把“真实云 / 本地 provider 已在在线环境下跑通 hybrid”写成已完成。
  - 没有对大 Vault 下的 hybrid 延迟、内存占用和 partial coverage 影响做性能基准。
- 哪些只是静态修改：
  - [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py) 中的 `provider_preference` 透传，以及 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py) / [backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py) 的调用切换，主要通过单元测试和编译验证，没有额外 UI 侧 E2E。

### 7. 范围偏移与原因

- 没有发生超出 `TASK-038` 边界的 `medium` 级偏移。
- 伴随改动只包括 retrieval helper 抽取、ask / ingest proposal 接线、`settings` / `provider_preference` 透传和测试补齐，这些都属于为了完成 hybrid retrieval 主链路接入所必需的接口适配与局部重构。

### 8. 未解决问题

- 当前 RRF 融合是固定策略，还没有 reviewer-facing 的 branch 贡献快照，排查“为什么这条在前面”仍需要读代码或打断点。
- 当前 partial embedding coverage 仍缺显式观测；向量分支即使不是完全 disabled，也可能只覆盖一部分 chunk，主链路暂时不会直接暴露这一点。
- 当前 hybrid 仍只解决召回融合，不解决 rerank、语义级 groundedness runtime gate 和大 Vault 性能问题。

### 9. 新增风险 / 技术债 / 假设

- 技术债：当前 hybrid 仍建立在 SQLite JSON embedding 全量扫描之上，Vault 规模继续增长后会先遇到向量分支的延迟和内存压力，再影响融合整体体验。
- 风险：如果后续仍不补 coverage / ready 统计，系统可能进入“FTS 可用、vector 部分可用、hybrid 还能返回结果”的灰度状态，而调用方只能看到最终候选，难以判断语义召回到底是否真正参与。
- 假设：`TASK-039` 会把 hybrid retrieval 纳入新的 eval baseline，而不是继续只回归纯 FTS / vector 单路分支。

### 10. 下一步最优先任务

1. 绑定 `TASK-039`，把离线 eval 升级到 interview-first P0 基线，并把 hybrid retrieval 纳入回归样本和指标。
2. 保持现有 `small` 派生项，不在下一会话把 `TASK-039` 顺手扩成 rerank、coverage 观测或 runtime groundedness gate。
3. `TASK-039` 完成后，再进入保留的第一个 P1：`TASK-040`，构建治理 vs 问答的分场景 benchmark。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
- [eval/golden/ask_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/ask_cases.json)
- [eval/golden/digest_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/digest_cases.json)
- [backend/tests/test_eval_runner.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_eval_runner.py)
- [backend/app/retrieval/hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/hybrid.py)

### 12. 当前最容易被面试官追问的点

- 为什么你这轮先用 RRF，而不是直接把 FTS 分数和 cosine 分数做加权融合？如果回答只有“RRF 简单”，会像没做过检索系统；必须讲清楚量纲不一致、先收敛可回归底座、再决定是否值得引入更重的校准或 rerank。
- 为什么 ask 和治理分析都要共用同一个 hybrid 入口？如果回答成“方便复用”，太浅；你必须能讲清楚 filter fallback、去重语义、disabled 降级和 candidate contract 统一，否则会被追问成两套逻辑拼装的玩具工程。
- 向量分支 disabled、index_not_ready、partial coverage 三种状态在 hybrid 里怎么区分？如果回答只有“失败就退回 FTS”，会显得你没有真正定义运行态边界和可观测性。
- 为什么 duplicate chunk 融合后保留 lexical candidate 的正文和 snippet，而不是重新定义一套 merged payload？如果回答不出“先稳住上游 citation / evidence contract，避免把 `TASK-038` 扩成协议重构”，会显得 scope control 很差。

## [SES-20260318-02] 为 chunk 索引补最小向量写入与向量检索入口

- 日期：2026-03-18
- task_id：`TASK-037`
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应任务：`TASK-037`
- 本会话唯一目标：在不提前推进 hybrid retrieval、rerank 或 ask / governance 主链路改造的前提下，为现有 SQLite `chunk` 索引补最小 embedding 写入与向量检索入口，补齐 retrieval P0 的向量侧底座。

### 1. 本次目标

- 为现有 `chunk` 数据补一份可持久化的 embedding 记录，并保证 note 级 replace / scoped ingest 不会残留旧向量。
- 提供独立于 FTS 的最小向量检索入口，返回与现有 `RetrievedChunkCandidate` 对齐的标准 candidate。
- 在 embedding provider / model 不可用、或当前 provider/model 下还没有向量数据时，返回显式禁用语义，而不是伪装成普通 no-hit。

### 2. 本次完成内容

- 复核 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)、[docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)、[docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 与 [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md) 后，确认当前最合适绑定任务为 `TASK-037`；当天已有 `SES-20260318-01`，因此本次会话使用未占用的 `SES-20260318-02`。
- 更新 [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)，把 schema 升到 `v7`，新增 `chunk_embedding` 表与对应 helper，持久化 `provider/model`、维度、向量范数、`content_hash` 与 embedding JSON。
- 新增 [backend/app/retrieval/embeddings.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/embeddings.py)，补最小 embedding provider 路由与 openai-compatible 请求封装，复用现有 cloud-primary / local-compatible 配置，并支持首选 provider 失败后的受控 fallback。
- 更新 [backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py)，让 ingest 在 note/chunk 主索引成功后 best-effort 写入 `chunk_embedding`；provider 不可用或中途失败时，主索引仍保持成功，不把 `TASK-037` 扩成 ingest 主链路硬失败。
- 新增 [backend/app/retrieval/sqlite_vector.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_vector.py)，实现基于 SQLite `chunk_embedding` 的最小向量检索、metadata filter 复用、标准 candidate 输出，以及 `retrieval_source=sqlite_vector`。
- 更新 [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)，为 `RetrievalSearchResponse` 增加 `disabled`、`disabled_reason`、`provider_name`、`model_name`，让“provider 不可用”与“向量索引未就绪”可被显式观测。
- 更新 [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py) 与 [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py)，显式向 ingest 透传运行态 `settings`，避免 graph / resume 路径绕过 embedding 配置。
- 补充 [backend/tests/test_indexing_store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_store.py)、[backend/tests/test_indexing_ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_ingest.py) 与新增 [backend/tests/test_retrieval_vector.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_retrieval_vector.py)，覆盖 schema、写入替换、标准 candidate 返回、provider 不可用禁用与索引未就绪禁用。

### 3. 本次未完成内容

- 没有实现 `TASK-038` 的 hybrid retrieval 融合，也没有把 ask / governance 主链路直接切到向量或混合召回。
- 没有引入 ANN、外部向量库或更高性能的向量索引结构；当前仍是 SQLite 持久化 + Python 余弦计算的 MVP 方案。
- 没有做真实云 / 本地 embedding provider 的联网 E2E 验证；当前验证范围停留在本地单元测试与静态编译。

### 4. 关键决策

- 没有在 `TASK-037` 里引入第二套向量基础设施，而是先复用现有 SQLite schema，新建 `chunk_embedding` 表；原因是本轮目标是补齐 P0 的向量底座，而不是把会话边界扩成新的存储平台接入。
- 没有把 embedding 写入定义成 ingest 主链路的 hard requirement，而是采用 note/chunk 主索引优先、向量侧 best-effort 降级；原因是 provider / 网络抖动不应该破坏最基本的索引一致性。
- 没有为向量检索再定义第二套 candidate contract，而是继续复用 `RetrievedChunkCandidate`；原因是 `TASK-038` 的 hybrid 融合应该建立在稳定候选协议上，而不是先做两套不兼容返回。
- 没有把“无向量结果”统一解释成 no-hit，而是增加 `disabled_reason`；原因是“provider 不可用”“索引未就绪”和“真的没召回”是三种完全不同的工程状态，必须可观测、可区分。

### 5. 修改过的文件

- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)
- [backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py)
- [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- [backend/app/retrieval/embeddings.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/embeddings.py)
- [backend/app/retrieval/sqlite_vector.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_vector.py)
- [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py)
- [backend/tests/test_indexing_store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_store.py)
- [backend/tests/test_indexing_ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_ingest.py)
- [backend/tests/test_retrieval_vector.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_retrieval_vector.py)

### 6. 验证与测试

- 跑了什么命令：
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_indexing_store tests.test_indexing_ingest tests.test_retrieval_fts tests.test_retrieval_vector tests.test_ingest_workflow tests.test_resume_workflow -v`
  - `cd backend && PYTHONPYCACHEPREFIX=/tmp/ks-pycache ../.conda/knowledge-steward/bin/python -m compileall app tests`
- 结果如何：
  - 聚合单测通过，共 40 条测试覆盖 schema、ingest、FTS、不回归的 ingest / resume graph，以及新增的向量检索分支。
  - `compileall` 通过，新增模块与测试可完成静态编译。
- 哪些没法验证：
  - 没有对真实 embedding provider 做联网调用验证，因此还不能把“云 provider / 本地 provider 都已在真实网络环境跑通”写成已完成。
  - 没有对大 Vault 下的向量检索耗时与索引成本做性能基准。
- 哪些只是静态修改：
  - `workflow.py` 的响应字段扩展、graph / resume 的 `settings` 透传等改动，主要通过单元测试与编译验证，没有额外 UI 侧 E2E。

### 7. 范围偏移与原因

- 没有发生超出 `TASK-037` 边界的 `medium` 级偏移。
- 伴随改动只包括 retrieval contract 扩展、graph / resume 的 `settings` 透传、schema migration 与测试补齐，这些都属于为了完成“最小 embedding 写入 + 向量检索入口”所必需的接口适配和局部重构。

### 8. 未解决问题

- 当前 `sqlite_vector` 是对 SQLite 中的 JSON embedding 做 Python 侧余弦计算，适合作为 P0 底座，但不适合大 Vault 或更高 QPS。
- 当前“向量索引是否就绪”的判断仍较保守：对当前 provider/model 完全无 embedding 时会显式禁用，但对“只写入了一部分 chunk”的 partial coverage 还没有单独观测。
- ask / ingest proposal 仍然没有消费 hybrid retrieval；下一步主线必须收敛到 `TASK-038`，不能回头继续把 `TASK-037` 扩成融合任务。

### 9. 新增风险 / 技术债 / 假设

- 技术债：向量检索当前缺少 ANN、分片或更高效的存储格式，Vault 规模继续增长后会遇到延迟和内存压力。
- 风险：embedding provider 不稳定时，ingest 会进入“主索引成功、向量侧降级”的部分可用状态；如果没有额外 coverage 观测，用户可能误解为向量能力已经完全可用。
- 假设：`TASK-038` 会继续复用当前 `RetrievedChunkCandidate` 与 `disabled_reason` 语义，而不是再定义第二套混合检索 contract。

### 10. 下一步最优先任务

1. 绑定 `TASK-038`，实现 FTS + 向量的最小 hybrid retrieval，并接入 ask / governance 主链路。
2. 在 `TASK-038` 不扩 scope 的前提下，视需要补一个 small 派生项：向量索引 coverage / ready 统计，避免 partial embedding 状态下的观测歧义。
3. 完成 `TASK-038` 后，再执行 `TASK-039`，把 eval 基线升级到 interview-first P0 水位。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/retrieval/embeddings.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/embeddings.py)
- [backend/app/retrieval/sqlite_vector.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_vector.py)
- [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- [backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py)

### 12. 当前最容易被面试官追问的点

- 为什么 `TASK-037` 先把向量持久化继续放在 SQLite 体系里，而不是直接上 Chroma / FAISS / Qdrant？如果回答只是“实现简单”，会像没做过；必须讲清楚 scope control、部署复杂度和现有 schema 连续性。
- note 级 replace / scoped ingest 后，你怎么保证旧 embedding 不脏、不残留、不会和新 chunk 错位？如果回答成“重跑一下就好了”，会显得没有定义一致性边界。
- provider 中途失败、部分 chunk 已写 embedding、另一部分还没写时系统怎么降级、怎么观测、怎么恢复？如果回答只有“报错”或“跳过”，会显得没有处理真实运行态。
- 为什么本轮只做到向量入口，不顺手把 ask / governance 一起切到 hybrid？如果回答成“先做一半”，会很弱；必须落到 candidate contract 先收敛、`TASK-038` 单独控 scope 的工程理由。

## [SES-20260318-01] 为插件补后端自启 / 探活 / 降级启动控制

- 日期：2026-03-18
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-036`
- 本会话唯一目标：在不扩成多进程 supervisor、跨平台安装器或第二套后端部署方案的前提下，为插件补最小本地后端启动控制、health-based readiness 判定和失败降级提示，让演示链路不再依赖“先手工开两个终端再口头解释”

### 1. 本次目标

- 让插件不再只有一次性的 `/health` ping，而是显式区分 `checking / starting / ready / unavailable / failed` 等运行态。
- 在用户提供可执行启动命令的前提下，让插件能从 Obsidian 内发起最小本地后端启动，并通过 `/health` 探针判断真正 ready，而不是把 `spawn` 成功误判成可用。
- 在后端不可用、启动失败、启动超时或进程提前退出时，给出明确的降级提示和最近错误上下文，而不是静默失败。

### 2. 本次完成内容

- 确认 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中 `TASK-036` 是当前最合适绑定的 `P0 medium` 任务，且 2026-03-18 当天尚无已占用会话，因此本次会话使用 `SES-20260318-01`。
- 新增 [plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts)，把插件侧后端控制收敛成独立 runtime：
  - 基于 `/health` 做 readiness 判定，而不是把子进程拉起本身当成成功
  - 显式维护 `checking / starting / ready / unavailable / failed` 五种状态
  - 记录 `tracked_pid`、最近一次检查时间、最近一次启动时间、最近错误、退出码和最近输出尾部
  - 在已跟踪子进程提前退出、启动超时或启动命令未配置时给出结构化失败 / 降级信息
- 更新 [plugin/src/settings.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/settings.ts)，新增：
  - `backendStartCommand`
  - `backendStartWorkingDirectory`
  - `backendStartupTimeoutMs`
  - `backendHealthCheckIntervalMs`
  - `autoStartBackendOnLoad`
- 更新 [plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts)：
  - 注入共享 `KnowledgeStewardBackendRuntime`
  - 新增 `Start backend` 命令
  - 让 `Ping backend` 走统一 runtime probe，而不是直接裸调 `client.getHealth()`
  - 插件加载时可按设置触发 `maybeAutoStartBackend()`
- 更新 [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)：
  - 新增 `Backend Runtime` 区块
  - 展示当前状态、最近检查时间、最近启动时间、`tracked_pid`、退出码、最近错误与最近输出
  - 增加 `Check backend` / `Start backend` 按钮，并在未配置启动命令时明确提示手动启动降级路径
  - 保留现有 approval / inbox 逻辑，不把本轮扩成新的 workflow UI
- 更新 [plugin/src/api/client.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/api/client.ts)，抽出共享 `formatApiErrorMessage()`，避免 runtime / view / API 层各自维护一套错误格式化逻辑。
- 更新 [plugin/styles.css](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/styles.css)，为 runtime 状态卡片和状态 pill 补最小样式。
- 新增 [plugin/src/backend/runtime.test.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.test.ts)，覆盖：
  - 未配置启动命令时的 `unavailable` 降级
  - 启动后 health probe 成功进入 `ready`
  - 子进程在 ready 前退出时进入 `failed`
- 更新 [plugin/package.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/package.json) 测试脚本，把 backend runtime 测试纳入插件最小回归。

### 3. 本次未完成内容

- 没有实现 `Stop / Restart backend` 控制，也没有持久化跨会话的进程所有权。
- 没有做真实 Obsidian 宿主里的手工端到端验证，因此仍未验证用户实际配置的 shell 命令在宿主环境中的可执行性。
- 没有把启动命令做成跨平台安装器、预置模板或自动探测 conda 环境；当前仍要求用户提供可执行命令。
- 没有扩成插件 ask UI、provider 探活或其他新的 `medium` 主线。

### 4. 关键决策

- 没有把“启动成功”定义成 `spawn` 成功，而是必须命中 `/health` 才进入 `ready`；原因是本地后端最容易出现“进程拉起了，但端口还没 ready 或依赖失败”的假阳性。
- 没有把启动命令硬编码成固定 conda 路线，而是要求用户显式配置；原因是仓库路径、shell 环境和 Obsidian 宿主的启动上下文都可能不同，硬编码更容易制造看似自动化、实际不可复用的假闭环。
- 没有把 runtime 控制继续塞进 [plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts)，而是抽成独立模块；原因是进程状态、health probe、尾日志与 UI 展示已经形成单独责任边界，继续堆在入口文件里会迅速失控。
- 没有在本轮顺手加 Stop / Restart；原因是本任务验收口径是“可拉起、可探活、可降级”，不是做完整本地进程 supervisor。

### 5. 修改过的文件

- [plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts)
- [plugin/src/backend/runtime.test.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.test.ts)
- [plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts)
- [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)
- [plugin/src/settings.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/settings.ts)
- [plugin/src/api/client.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/api/client.ts)
- [plugin/styles.css](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/styles.css)
- [plugin/package.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/package.json)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 6. 验证与测试

- 跑了什么命令
  - `cd plugin && npm test`
  - `cd plugin && npm run build`
- 结果如何
  - `npm test` 最终通过，当前插件测试共 8 条通过。
  - `npm run build` 通过，说明 runtime 控制、settings、view 和命令接入在现有插件构建边界内可打包。
  - 验证过程中先后暴露出两类本地构建问题：
    - Node strip-only TypeScript 模式不支持 parameter property，后续已把 runtime / client 的相关构造函数改为显式字段赋值
    - runtime 测试链路的 ESM 解析要求显式 `.ts` 扩展名，后续已在测试触达路径上收敛 import
- 哪些没法验证
  - 没有在真实 Obsidian 宿主里点击 `Start backend`，验证用户提供的启动命令、shell 环境和 working directory 是否按预期执行。
  - 没有验证 Windows / Linux 下的实际 shell 行为差异。
- 哪些只是静态修改
  - [plugin/styles.css](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/styles.css)
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 本次伴随改动包括：
  - 抽 runtime 模块
  - 增加设置项
  - 增加最小 runtime 测试
  - 为 runtime 状态补最小样式和错误格式化复用
- 这些都直接服务于 `TASK-036` 的验收标准，不构成新的 `medium` 功能。

### 8. 未解决问题

- 启动命令仍依赖用户手写 shell / conda 命令，配置错误时只能给出错误上下文，不能自动纠正。
- 当前只能跟踪插件本次启动出的子进程，不能管理插件重启前或外部终端启动的 backend 进程生命周期。
- 还没有 `Stop / Restart` 操作，也没有 stale `tracked_pid` 的更强治理。
- 没有真实 Obsidian 宿主下的手工回归记录。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果面试里把现在的“用户提供命令 + 插件拉起 + `/health` 判 ready”包装成完整进程管理，会被直接追问到宿主环境、端口占用、重复启动和跨会话进程所有权，暴露边界不清。
- 技术债：当前 runtime 控制仍依赖用户配置的 shell 命令，配置体验和跨平台兼容性都偏脆；后续若要进一步产品化，需要补模板、预检或更稳的启动封装。
- 技术债：runtime 状态只存在于插件当前进程内，重启 Obsidian 后无法回溯上次启动的受控 backend。
- 假设：下一次主线 medium 会话应前移到 `TASK-037`，补最小向量写入与向量检索入口，而不是继续把 `TASK-036` 扩成本地 supervisor 或跨平台安装器。

### 10. 下一步最优先任务

1. 绑定 `TASK-037`，为 chunk 索引补最小向量写入与向量检索入口。
2. 保持 `TASK-038` 作为 hybrid retrieval 的下一步，不要把融合逻辑顺手塞进 `TASK-037`。
3. 将 backend runtime 的 `Stop / Restart`、命令模板预检和 stale PID 提示继续留在 `small`，不要因为“现在顺手”再开新的 medium。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- [backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py)
- [backend/app/retrieval/sqlite_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_fts.py)
- [backend/app/config.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/config.py)
- [backend/tests/test_indexing_ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_ingest.py)
- [backend/tests/test_retrieval_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_retrieval_fts.py)

### 12. 当前最容易被面试官追问的点

- 你为什么不把“子进程拉起成功”直接当成 backend ready，而还要多做一层 `/health` readiness probe？如果回答只是“更稳一点”，会很像没做过真实本地进程控制；正确答案必须落到假阳性、端口未 ready、依赖失败和 contract-based readiness。
- 你为什么让用户自己提供启动命令，而不是在插件里硬编码 conda 路径或一套固定脚本？如果回答成“实现简单”，会显得你没有正视宿主环境、repo 路径、shell 上下文和可移植性问题。
- 你现在只做了 Start，没有 Stop / Restart，这是不是半成品？如果回答不出“本轮目标是拉起/探活/降级控制，而不是 supervisor；否则任务边界会被打穿”，会显得你没有 scope control。
- 如果用户点了两次 Start backend、或者第一次拉起后端很慢、或者端口其实已经被外部进程占了，会发生什么？如果回答不出“状态机、已跟踪进程、health poll 和失败降级”的组合边界，会很像只是拼了个 demo。

## [SES-20260317-07] 为 `INGEST_STEWARD` 接入 retrieval-backed analyze_consistency

- 日期：2026-03-17
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-035`
- 本会话唯一目标：在不扩成向量检索、hybrid retrieval、多 note proposal 合并或第二套审批协议的前提下，为 `INGEST_STEWARD` 的单 note scoped proposal 路径补最小 `related_retrieve -> analyze -> propose` 主线，让 proposal evidence 不再只来自当前 note 自身

### 1. 本次目标

- 在现有 scoped ingest proposal 已可运行的基础上，把治理 proposal 从“只依赖 parser 局部结构信号”推进到“最小 retrieval-backed analysis”。
- 让 `/workflows/invoke` 的 `INGEST_STEWARD` 在 proposal 模式下返回最小结构化 `analysis_result`，并把 related retrieve 命中的 cross-note evidence 接入 proposal。
- 在不引入 LLM judge、向量检索和多 note 合并的前提下，先把保守可回归的一层 `orphan_hint / duplicate_hint` 与本地结构信号打通。

### 2. 本次完成内容

- 确认 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中 `TASK-035` 是当前最合适绑定的 `P0 medium` 任务，且当天 `SES-20260317-01` 到 `SES-20260317-06` 已占用，因此本次会话使用 `SES-20260317-07`。
- 更新 [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)、[backend/app/graphs/state.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/state.py)、[backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py) 与 [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)，新增 `IngestAnalysisResult` / `IngestAnalysisFinding`，并把 `analysis_result` 接进 ingest state、workflow response 和 trace 统计。
- 重写 [backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py) 的 proposal 构造逻辑：
  - 在 proposal 路径里复用现有 SQLite FTS 做最小 related retrieve，而不是新开向量或 hybrid 分支
  - 基于 related candidate 与本地结构信号生成保守的 `orphan_hint / duplicate_hint / missing_frontmatter / has_open_tasks / unclassified_note_type`
  - 显式排除目标 note 自身，避免 proposal 把“刚 ingest 的当前笔记”当成 related evidence 自证
  - 把 related candidate 对齐到 proposal evidence、review markdown 和 `merge_frontmatter` 的 `analysis_scope=retrieval_backed`
  - 无问题时返回结构化 `analysis_result` + safe fallback，而不是硬造 waiting proposal
- 更新 [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)，让插件侧 contract 跟上新的 `analysis_result` 字段，但没有在本轮继续扩审批面板 UI。
- 更新 [backend/tests/test_ingest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ingest_workflow.py)：
  - 新增 retrieval-backed analysis 命中断言
  - 断言 related evidence 会落到 `Beta.md` 而不是 `Alpha.md` 自身
  - 覆盖 no-proposal fallback 时的 `analysis_result.fallback_used`
  - 覆盖 trace 中的 `related_candidate_count`

### 3. 本次未完成内容

- 没有把 retrieval-backed analyze 扩成向量检索或 hybrid retrieval；这仍属于 `TASK-037` / `TASK-038`。
- 没有补多 note proposal 合并、跨 note 真正的 conflict 判定或 LLM 解释；当前仍是保守规则分析。
- 没有让插件审批面板展示 `analysis_result` 本身，只同步了 TS contract。
- 没有解决 cold-index 场景：如果是 fresh DB 且只做单 note scoped ingest，索引里本来就没有“旧笔记上下文”，related evidence 会安全缺失。

### 4. 关键决策

- 没有新开 schema 或 proposal 子表来持久化 `analysis_result`，而是先把它放进 workflow response / checkpoint state；原因是本轮要补的是治理分析主线，不是再开一轮持久化设计任务。
- 没有把 retrieval-backed analyze 直接做成 LLM 节点；原因是当前更需要低噪声、可回归、失败可降级的保守分析，而不是把新风险交给不可控 judge。
- 没有在 fresh DB 下偷偷改成“为了拿到 related evidence 先整库 ingest 一遍”；原因是这会把 scoped ingest 语义打散，也会越界到索引策略和成本问题。
- 没有把当前实现包装成“已经做完 duplicate/conflict 引擎”；当前事实只是：已把 `INGEST_STEWARD` 从纯单 note 结构规则推进到最小 retrieval-backed analysis。

### 5. 修改过的文件

- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/app/graphs/state.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/state.py)
- [backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py)
- [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/tests/test_ingest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ingest_workflow.py)
- [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 6. 验证与测试

- 跑了什么命令
  - `python -m py_compile backend/app/contracts/workflow.py backend/app/graphs/state.py backend/app/services/ingest_proposal.py backend/app/graphs/ingest_graph.py backend/app/main.py backend/tests/test_ingest_workflow.py`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_ingest_workflow -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_indexing_ingest -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
  - `cd plugin && npm run build`
- 结果如何
  - `py_compile` 通过，说明新增 contract / service / graph / test 没有语法错误。
  - 首次从仓库根目录执行 `./.conda/knowledge-steward/bin/python -m unittest backend.tests.test_ingest_workflow -v` 因 `app` 模块导入根不对失败，确认是命令工作目录问题后改在 `backend/` 目录重跑通过。
  - `test_ingest_workflow` 定向 10 个测试全部通过，覆盖 retrieval-backed 命中、self-match 排除、no-proposal fallback 和 trace 计数。
  - `test_indexing_ingest` 定向 4 个测试通过，没有把既有 scoped ingest / FTS 一致性撞坏。
  - backend 全量 62 个测试通过。
  - plugin `npm run build` 通过。
- 哪些没法验证
  - 没有在真实 Obsidian 宿主里手工点一次审批面板，确认 UI 对 `analysis_result` 的展示需求。
  - 没有测大 Vault 或冷启动 DB 下 retrieval-backed analyze 的成本与命中质量。
- 哪些只是静态修改
  - [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 唯一伴随改动是：
  - 为 ingest response 增加最小 `analysis_result` contract
  - 为 trace 增加 `related_candidate_count`
  - 为插件 TS contract 做字段同步
- 这些都直接服务于 `TASK-035` 的验收标准，不构成新的 `medium` 功能。

### 8. 未解决问题

- retrieval-backed 命中当前依赖索引中已经存在“旧笔记上下文”；fresh DB 下单 note scoped ingest 仍可能只有本地结构分析。
- `duplicate_hint` / `orphan_hint` 仍是启发式规则，不是完整 conflict engine。
- `analysis_result` 目前只在 API / checkpoint 层可见，审批面板还不能直接渲染它。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果后续把本轮实现包装成“新笔记治理已经具备完整 duplicate/conflict 判断”，会被直接追问到冷启动索引、误召回和规则边界，暴露项目口径失真。
- 技术债：当前 retrieval-backed analyze 仍完全建立在 FTS 和少量标题 / wikilink / heading query 上；等 `TASK-037`、`TASK-038` 完成后，需要重新评估 evidence 质量和融合策略。
- 技术债：`analysis_result` 还没有进入 proposal 主存储，也没有进入插件审批视图，当前更偏 control-plane contract，而不是 reviewer-facing 成品。
- 假设：下一次主线 medium 会话应前移到 `TASK-036`，先补插件侧后端自启 / 探活 / 降级启动控制，而不是继续把 retrieval 线扩成 hybrid 或把 cold-index 问题升格成新的 medium。

### 10. 下一步最优先任务

1. 绑定 `TASK-036`，为插件补后端自启 / 探活 / 降级启动控制。
2. 保持 `TASK-037`、`TASK-038` 作为 retrieval 主线后续两步，不要把向量 / hybrid 顺手塞回 `TASK-035`。
3. 把 cold-index 提示或预热检查保留为 `small`，不要因为这个边界再临时新开一个 medium。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts)
- [plugin/src/api/client.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/api/client.ts)
- [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)
- [plugin/src/settings.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/settings.ts)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 12. 当前最容易被面试官追问的点

- 你为什么现在先用 FTS 做 retrieval-backed analyze，而不是直接等 `TASK-037`、`TASK-038` 完成后再一次性做向量 + hybrid？如果回答只是“先做简单的”，会很像没做过；正确答案必须落到已有索引底座复用、P0 收口顺序和低噪声可回归分析。
- 你怎么证明 related evidence 不是把当前目标 note 自己检索回来后自证？如果回答不出“显式排除目标 note、自身命中不算 related evidence、无命中就降级”，会直接暴露你没有处理过 evidence 污染。
- 为什么 fresh DB 下你不偷偷先整库 ingest 一遍来制造 related context？如果回答只是“懒得做”，会很像玩具项目。正确答案要落到 scoped ingest 语义、索引成本和 control-plane 责任边界。
- 你现在说有 `duplicate_hint / orphan_hint`，那 conflict 到底怎么定义，为什么这轮没做？如果回答不出“当前是保守启发式分析、不是完整 conflict engine；否则会把任务边界打穿到 `TASK-037/038` 之后的更大问题”，会显得你没有 scope control。

## [SES-20260317-06] 写回成功后触发 scoped ingest 并刷新索引

- 日期：2026-03-17
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-030`
- 本会话唯一目标：让 approval + successful writeback 路径自动触发 scoped ingest / 索引刷新，并在刷新失败时返回明确降级结果，而不是把本地写回伪装成“完全成功”

### 1. 本次目标

- 在不扩成跨会话恢复、增量 FTS 或第二套 workflow 协议的前提下，把插件本地真实写回和后端 scoped ingest 接起来。
- 让 `/workflows/resume` 在 `approved + writeback_result.applied=true` 时自动对 `target_note_path` 执行 note 级索引刷新。
- 让写回成功但后续 scoped ingest 失败时，仍然落审计和 completed checkpoint，但要返回明确的降级信息，不能继续冒充“完全成功”。

### 2. 本次完成内容

- 确认 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中 `TASK-030` 是当前最合适绑定的 `P0 medium` 任务，且当天 `SES-20260317-01` 到 `SES-20260317-05` 已占用，因此本次会话使用 `SES-20260317-06`。
- 更新 [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)、[backend/app/graphs/state.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/checkpoint.py) 与 [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)，新增 `PostWritebackSyncResult` 并把它接进 `WorkflowResumeResponse`、checkpoint state 与 `/workflows/resume` 返回体。
- 更新 [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py)：
  - 仅在 `approved + writeback_result.applied=true` 时触发 post-writeback scoped ingest
  - 复用 [backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py) 的 `ingest_vault(..., note_path=proposal.target_note_path)` 做 note 级索引刷新
  - 刷新成功时返回结构化 `post_writeback_sync`，并把结果一并写入 completed checkpoint
  - 刷新失败时仍落审计与 checkpoint，但 message 和 `post_writeback_sync` 会显式暴露降级事实
  - completed checkpoint 的幂等恢复会回放已持久化的 `post_writeback_sync`，避免同一决策重复触发副作用
- 更新 [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts) 与 [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)，让插件能够展示 scoped reindex 的成功 / 失败结果，而不是只显示笼统的 resume message。
- 更新 [backend/tests/test_resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_resume_workflow.py)，新增：
  - 写回成功后 DB / chunk / FTS 真刷新断言
  - scoped ingest 刷新失败时显式降级、但 audit / checkpoint 仍完成的断言

### 3. 本次未完成内容

- 没有补“本地写回成功但 `/workflows/resume` 失败”的跨会话恢复入口；这仍属于 `TASK-031`。
- 没有把 scoped ingest 的 FTS 重建优化成局部同步；当前仍复用整库 `rebuild_chunk_fts_index()`，这仍属于 `TASK-032`。
- 没有在真实 Obsidian 宿主里手工点一次 approval 面板完成写回后 reindex 的端到端验证。

### 4. 关键决策

- 没有让插件在本地写回成功后再单独打一遍新的 ingest API，而是把 post-writeback reindex 收口到 `/workflows/resume`；原因是本轮要补的是“审计事实、索引一致性和失败降级的同一控制面”，不是再拆出第二套半独立协议。
- 没有把 reindex 失败继续升级成 HTTP 错误并让 thread 保持 `waiting_for_approval`；原因是本地写回事实已经发生，再把业务状态伪装成“还没审批完”只会制造更大的状态分叉。
- 没有在本轮强行新增新的 `RunStatus`，而是保持 `completed` + 明确 `message` + 结构化 `post_writeback_sync`；原因是当前任务的重点是表达真实降级事实，而不是扩散成更大的状态机重构。
- 没有复用 `ingest_graph` 重新跑一条完整 workflow，而是先复用 [backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py) 的 scoped ingest 共享能力；原因是本轮要补的是 note 级索引刷新，不是再引入一条新的 checkpoint / trace 语义分支。

### 5. 修改过的文件

- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/app/graphs/state.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/state.py)
- [backend/app/graphs/checkpoint.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/checkpoint.py)
- [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/tests/test_resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_resume_workflow.py)
- [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)
- [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 6. 验证与测试

- 跑了什么命令
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_resume_workflow -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_ingest_workflow tests.test_indexing_ingest -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
  - `cd plugin && npm run build`
  - `cd plugin && npm test`
- 结果如何
  - `test_resume_workflow` 定向 10 个测试全部通过，覆盖 approval、rejection、successful writeback refresh、refresh failure degrade 与幂等恢复。
  - `test_ingest_workflow` + `test_indexing_ingest` 定向 14 个测试全部通过，没有把既有 scoped ingest / checkpoint 语义撞坏。
  - backend 全量 62 个测试通过。
  - plugin `npm run build` 与现有 5 个写回测试全部通过。
- 哪些没法验证
  - 没有在真实 Obsidian 宿主里手工点一次 `Approve -> 本地写回 -> /workflows/resume -> scoped ingest refresh` 的宿主级链路。
  - 没有测大 Vault 下连续多次 approval 导致的 FTS 重建成本。
- 哪些只是静态修改
  - [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 唯一伴随改动是：
  - 为 `/workflows/resume` 扩了 `post_writeback_sync` 的最小结构化返回
  - 为 checkpoint state 增加对应持久化字段
  - 为插件 view 增加 scoped reindex 结果展示
- 这些都直接服务于 `TASK-030` 的验收标准，不构成新的 `medium` 功能。

### 8. 未解决问题

- 当前 post-writeback reindex 仍是 best-effort：失败会显式降级，但没有跨会话补偿或重试入口。
- 当前 scoped ingest 仍会整库重建 FTS；连续 approval 时的成本还没有优化。
- `proposal.target_note_path` 仍依赖“插件当前 vault 与后端 configured vault 对齐”这一前提；更强的路径协议治理还没做。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果后续把 `post_writeback_sync` 的失败 message 包装成“只是提示信息”，而不承认这意味着索引仍可能陈旧，面试时会被追问成“你只是把错误文案写漂亮了，并没有真正处理一致性边界”。
- 技术债：当前完成态 checkpoint 会保留 failed `post_writeback_sync`，但没有后续补偿路径；这不是 bug，而是本轮刻意保守的边界，后续要由 `TASK-031` 明确承接。
- 技术债：当前 reindex 仍直接复用 `ingest_vault()`，因此会沿用整库 FTS 重建策略；真实性能优化仍留在 `TASK-032`。
- 假设：下一次主线 medium 会话应前移到 `TASK-035`，开始补 retrieval-backed analyze_consistency，而不是继续回头扩 `TASK-030` 的批量调度或 retry 机制。

### 10. 下一步最优先任务

1. 绑定 `TASK-035`，为 `INGEST_STEWARD` 增加 retrieval-backed analyze_consistency 节点。
2. 保持 `TASK-031` 为后续恢复控制面任务，不要把跨会话补偿顺手塞回当前任务。
3. 保持 `TASK-032` 为单独 retrieval / indexing 任务，不要把 FTS 局部增量同步混进治理分析主线。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py)
- [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)
- [backend/app/retrieval/sqlite_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_fts.py)
- [backend/tests/test_ingest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ingest_workflow.py)
- [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py)

### 12. 当前最容易被面试官追问的点

- 你为什么把 post-writeback reindex 放到 `/workflows/resume` 控制面，而不是让插件本地写回成功后再顺手打一遍 ingest API？如果回答只是“实现方便”或“这样少写代码”，会很像没做过副作用系统。正确回答必须落到：谁真正改了 Vault、谁持有审计事实、谁负责幂等重试，以及为什么索引一致性和审批恢复要在同一后端事务语义下收口。
- reindex 失败了，为什么 thread 还是 `completed`，而不是继续留在 `waiting_for_approval` 或直接返回 HTTP 失败？如果回答不出“本地写回事实已经发生，不能再把业务事实伪装成未审批”，会直接暴露你没有处理过 control-plane / side-effect-plane 分叉。

## [SES-20260317-05] 将后续任务优先级重新对齐到《初步实现指南》的 interview-first MVP

- 日期：2026-03-17
- 类型：`Docs`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-034`
- 本会话唯一目标：在不实现任何新功能的前提下，基于《初步实现指南》的 MVP 清单、主文档和真实代码状态，把后续路线明确收敛为“先补齐剩余 P0，再只做前三个 P1”，并修正仍残留在主文档 / README 中的旧任务顺序

### 1. 本次目标

- 复核《初步实现指南》中的 P0 / P1 MVP 清单，确认当前哪些能力已经达到面试版下限，哪些仍是必须补齐的剩余 P0。
- 在不推翻“主文档 + 当前代码事实”为执行基准的前提下，把项目的 interview-first north star 显式前置到核心位置，避免后续会话继续顺着旧的 `TASK-030 -> TASK-031 -> TASK-032 -> TASK-033` 路线机械推进。
- 同步修正文档之间的漂移：`docs/TASK_QUEUE.md` 已经登记了 `TASK-034` 与新任务，但 [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 与 [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md) 仍残留多处旧 `Next Action` 表述。

### 2. 本次完成内容

- 确认 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中 `TASK-034` 是当前最合适绑定的 `planned / scope=medium` 文档治理任务，且 2026-03-17 当天 `SES-20260317-01` 到 `SES-20260317-04` 已占用，因此本次会话使用 `SES-20260317-05`。
- 复读 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)、[docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)、[docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)、[README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md) 与 [Obsidian Knowledge Steward 项目初步实现指南.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/Obsidian%20Knowledge%20Steward%20项目初步实现指南.md)，并结合 [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)、[backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)、[backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py)、[backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py)、[plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)、[plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts) 与 [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py) 的当前事实，确认：
  - 剩余 P0 应收敛为 `TASK-030`、`TASK-035`、`TASK-036`、`TASK-037`、`TASK-038`、`TASK-039`
  - 当前只保留的三个 P1 应收敛为 `TASK-040`、`TASK-041`、`TASK-042`
  - `TASK-031`、`TASK-032`、`TASK-033` 虽然仍有价值，但不属于这轮 interview-first 收口范围
- 在 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中完成 `TASK-034` 收尾说明补强，明确“产品形态、受限写回安全链路和当前 ask / ingest / digest 的基础 tracing 已达到 interview-first P0 下限”，因此没有额外新增一个独立 tracing P0 任务。
- 更新 [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)：
  - 版本推进到 `v0.2.38`
  - 在核心位置保留“当前执行优先级约束”
  - 修正“当前事实边界”“高优先级补齐项”和 6 处仍残留旧路线的 `Next Action`
  - 明确当前只剩哪些 P0 需要补齐，以及为什么 `TASK-031` 到 `TASK-033` 被后移
  - 在第 13 节补记两条新的关键面试追问：为什么当前不继续推进 `TASK-031` 到 `TASK-033`，以及为什么基础 tracing 不再单独立 P0
- 更新 [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)，新增“当前优先级提醒”并同步新的主线任务顺序，避免后续只看仓库首页时继续误判路线。
- 在 [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md) 中补记本次正式会话记录，确保 `TASK-034` 不再处于“队列里已完成、但会话日志缺失”的半同步状态。

### 3. 本次未完成内容

- 没有实现 `TASK-030`、`TASK-035` 到 `TASK-042` 中的任何业务能力；本会话只做路线治理和文档同步。
- 没有改变 `TASK-031`、`TASK-032`、`TASK-033` 的任务定义本身，只改变了它们在当前路线中的优先级位置。
- 没有增加新的运行时逻辑、测试样本或接口行为。

### 4. 关键决策

- “主文档 + 当前代码事实”继续是执行层面的唯一基准，但项目的 interview-first north star 仍来自 [Obsidian Knowledge Steward 项目初步实现指南.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/Obsidian%20Knowledge%20Steward%20项目初步实现指南.md)；这两者不是互相推翻，而是“执行基准”和“路线优先级”的分层。
- 没有把所有仍未完成的能力都重新打成第一优先，而是只保留“三个 P1”：分场景 benchmark、最小撤销 / 回滚、统一 workflow contract；原因是这三项最能显著提升面试里的质量闭环、失败恢复和系统设计叙事。
- 没有为 tracing 再单独新增一个 P0 medium；原因是当前 ask / ingest / digest 已有 JSONL + SQLite `run_trace` 的节点级基础 tracing，足以覆盖《初步实现指南》里 interview-first P0 的“基础 tracing”下限。更强的 LangSmith、聚合看板和 richer 指标继续保留为后续优化，而不是再插入新的 P0 阻塞项。
- `TASK-031` 到 `TASK-033` 被明确后移；原因不是这些问题不重要，而是它们既不属于当前剩余 P0，也不属于已经明确保留的前三个 P1。如果现在继续推进，只会把路线重新拉散。

### 5. 修改过的文件

- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 6. 验证与测试

- 跑了什么命令
  - `rg -n "TASK-03[0-9]|TASK-04[0-2]|SES-20260317-05|当前开发阶段|当前后续主线|Next Action|P0|P1|初步实现指南|interview-first" docs/TASK_QUEUE.md docs/PROJECT_MASTER_PLAN.md README.md docs/SESSION_LOG.md`
  - `sed -n '1,260p' docs/PROJECT_MASTER_PLAN.md`
  - `sed -n '1,260p' README.md`
  - `sed -n '1,260p' docs/SESSION_LOG.md`
  - `sed -n '330,390p' docs/PROJECT_MASTER_PLAN.md`
  - `sed -n '470,520p' docs/PROJECT_MASTER_PLAN.md`
  - `sed -n '632,660p' docs/PROJECT_MASTER_PLAN.md`
  - `sed -n '800,820p' docs/PROJECT_MASTER_PLAN.md`
  - `sed -n '970,990p' docs/PROJECT_MASTER_PLAN.md`
  - `sed -n '1105,1120p' docs/PROJECT_MASTER_PLAN.md`
  - `sed -n '1760,1835p' docs/PROJECT_MASTER_PLAN.md`
  - `rg -n "MVP|P0|P1|tracing|可观测|Golden|向量|BM25|插件可自启|工作流" "Obsidian Knowledge Steward 项目初步实现指南.md"`
- 结果如何
  - 已确认《初步实现指南》里的剩余 P0 与当前最值得保留的三个 P1 都能在现有代码事实基础上对齐成清晰任务，而不需要再额外发明新的主线。
  - 已确认一个明确的文档不一致：`TASK_QUEUE` 已按 `TASK-034` 调整优先级，但主文档和 README 多处仍沿用 `TASK-030 -> TASK-031 -> TASK-032 -> TASK-033` 的旧顺序；本次已全部修正。
  - 已确认“基础 tracing 是否仍需新建一个 P0”这个问题已有答案：当前 runtime trace baseline 可视为达标，不再单独立项。
  - 已在主文档第 13 节补入与当前路线一致的面试追问，避免路线已经回正，但面试叙事仍停留在旧优先级。
- 哪些没法验证
  - 本次没有业务代码改动，因此不存在新的运行时链路可做 unittest、集成测试或手工功能验证。
  - 新队列本身只是优先级治理，不能把未来任务的 acceptance criteria 误写成“已验证通过”。
- 哪些只是静态修改
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 本次所有补充都直接服务于 `TASK-034`：要么是确认《初步实现指南》的真实 P0/P1 边界，要么是修正文档之间已经形成的优先级漂移。
- 没有借机推进任何新的 medium 功能实现。

### 8. 未解决问题

- `TASK-030` 到 `TASK-039` 仍然只是登记完毕，尚未开始真实实现。
- `TASK-031` 到 `TASK-033` 虽然被后移，但相关风险并未消失，只是在当前面试版路线里不再抢占第一批主线。
- 当前 tracing 虽已达到 interview-first P0 下限，但更强的 LangSmith / dashboard / 指标聚合仍未实现。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果后续会话忽略这次新增的核心提醒，再次按旧路线先做 `TASK-031` 到 `TASK-033`，项目会重新陷入“优先级看起来很多，但 P0 仍未收口”的状态。
- 风险：`TASK-037` 与 `TASK-038` 一旦真正开做，会把 embedding provider、向量写入与 hybrid 融合的工程复杂度暴露出来，需要严格守住“不顺手把 reranker 也一起做掉”的边界。
- 技术债：当前把基础 tracing 视作 P0 达线，是基于 interview-first 收口策略做的保守判断；若后续面试叙事升级到更强调线上稳定性，仍需要补更强的 trace 聚合与展示。
- 假设：接下来的会话会严格按“先补齐剩余 P0，再只做保留的三个 P1”的顺序执行，而不是再次从 README 或旧日志中抽取过时路线。

### 10. 下一步最优先任务

1. 绑定 `TASK-030`，补齐 `writeback -> scoped ingest reindex` 的一致性断口。
2. 依次推进剩余 P0：`TASK-035`、`TASK-036`、`TASK-037`、`TASK-038`、`TASK-039`。
3. 在 P0 收口后，只推进 `TASK-040`、`TASK-041`、`TASK-042` 三个保留的 P1。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)
- [Obsidian Knowledge Steward 项目初步实现指南.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/Obsidian%20Knowledge%20Steward%20项目初步实现指南.md)
- [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)
- [plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts)
- [backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py)
- [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)
- [backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py)
- [backend/app/retrieval/sqlite_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_fts.py)
- [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)

### 12. 当前最容易被面试官追问的点

- 你为什么说“主文档 + 代码事实”是执行基准，却又坚持让《初步实现指南》决定优先级？如果回答只剩“因为最开始这么设计”，会显得你没有工程判断。正确回答必须落到分层：主文档负责约束事实和边界，指南负责提醒项目最初要证明的能力集合，二者共同决定“先做什么”。
- 你为什么把 `TASK-031` 到 `TASK-033` 后移？如果回答只是“现在先不做优化”，会很像没做过复杂系统。正确回答必须指出：这些项虽然真实存在，但不属于当前剩余 P0，也不属于对面试最有价值的三个 P1；如果继续抢主线，只会让 P0 永远收不完。
- 你为什么没有再新增一个 tracing P0 任务？如果回答只有“现在差不多够了”，会显得非常心虚。真正有说服力的回答是：当前 ask / ingest / digest 已经具备节点级 runtime trace、错误落盘和检索上下文回溯，满足《初步实现指南》里的基础 tracing 下限；真正没收口的是 retrieval 和 eval 底座，而不是先去追更花的观测平台。

## [SES-20260317-04] 继续拆解 `TASK-028` 之后的下一批 medium 队列任务

- 日期：2026-03-17
- 类型：`Docs`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-029`
- 本会话唯一目标：基于 `TASK-028` 完成后的真实代码状态，重新拆解并登记下一批可执行 medium 任务，避免队列在 ask groundedness eval 之后再次断档

### 1. 本次目标

- 在不推进任何新功能实现的前提下，基于真实代码和既有文档，为 `TASK-028` 之后的主线补齐下一批 `medium` 任务。
- 重新判断哪些遗留项已经长成独立的中等粒度问题，哪些仍应继续留在 `small / derived_tasks`，避免把 backlog 重新打包成“杂项收尾包”。
- 同步修正文档中仍写着“下一步优先执行 `TASK-029`”的过时描述，并收敛 README / eval 文档里的状态漂移。

### 2. 本次完成内容

- 确认 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中 `TASK-029` 是当前唯一可绑定的 `planned / scope=medium` 任务，且 2026-03-17 当天 `SES-20260317-01`、`SES-20260317-02`、`SES-20260317-03` 已占用，因此本次会话分配 `SES-20260317-04`。
- 补读 [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md) 中 `SES-20260317-03`，确认上一会话已明确要求下一步先绑定 `TASK-029`，不要凭直觉直接进入新的功能实现。
- 复核 [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)、[README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)、[eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)、[eval/golden/ask_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/ask_cases.json)、[backend/tests/test_eval_runner.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_eval_runner.py)、[backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py)、[backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py)、[backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)、[backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)、[backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)、[plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts) 与 [plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts)，确认当前值得升格的新缺口集中在四处：
  - 写回成功后 SQLite / FTS 索引仍陈旧
  - 本地写回成功但 `/workflows/resume` 失败时，恢复入口仍停留在插件内存态
  - scoped ingest 仍然整库重建 `chunk_fts`
  - ask groundedness 仍只存在于离线 eval，没有进入 runtime gate
- 同时确认两项遗留问题仍应保留为 `small`：
  - pending inbox 已按 `updated_at DESC` 排序，并暴露 `proposal_created_at / proposal_updated_at / checkpoint_updated_at`；后续只需继续补 freshness 提示或生命周期治理
  - `python -m app.indexing.ingest` 当前只缺 `--note-path / --note-paths` 参数暴露，CLI parity 还不足以单独占用一整个 `medium`
- 在 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中将 `TASK-029` 标记为 `completed`，并新增 `TASK-030` 到 `TASK-033` 四个后续 medium 任务。
- 在 [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 中同步更新版本、最近更新时间、当前开发阶段、`Next Action` 和当前事实边界，把主线路线从 `TASK-029` 前移到 `TASK-030`。
- 更新 [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)，同步新的主线任务顺序。
- 修正 [eval/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/README.md) 与当前实现不一致的问题：旧文档仍写“首版直接从 `sample_vault/` 抽 30 条样本”，但当前真实事实已经是 13 条可运行 golden case 与可落盘结果文件。

### 3. 本次未完成内容

- 没有实现 `TASK-030` 到 `TASK-033` 中的任何业务能力；本会话只完成队列治理和项目文档同步。
- 没有把 freshness 提示、CLI scoped parity、新笔记治理 proposal 风险分级 / patch 模板收敛，以及 groundedness allowlist / 停用词收敛升级成新的 medium。
- 没有新增任何测试、接口或运行时逻辑；本次所有改动都停留在文档层。

### 4. 关键决策

- 没有把 “writeback 后增量 ingest” 和 “跨会话恢复入口” 继续留在 `small`；原因是 `TASK-019`、`TASK-026` 之后，这两个问题都已经跨越插件、后端和索引一致性边界，具备清晰输入、输出和验收条件。
- 没有把 freshness 再升格为新的 medium；原因是当前后端查询已经按 `workflow_checkpoint.updated_at DESC` 排序，插件也展示了 `checkpoint_updated_at`，剩余工作更像产品提示与生命周期治理，而不是新的主链路能力。
- 没有把 CLI scoped parity 单独拆成 medium；原因是当前 `backend/app/indexing/ingest.py` 已具备 scoped note 能力，CLI 只差参数暴露，不足以单独占一个会话。
- `TASK-032` 被拆成“scoped ingest 增量 FTS 同步”，而不是宽泛写成“继续优化 ingest 性能”；原因是当前真正失真的不是泛泛性能，而是 scoped ingest 仍整库重建 FTS，已经影响它是否适合作为后续写回同步主路径。
- `TASK-033` 选择“保守 runtime gate + 失败即降级”，而不是直接引入 LLM judge；原因是当前最需要的是把 `unsupported_claim` 风险从离线结果文件推进到线上安全边界，而不是把可复现问题重新交给高噪声 judge。

### 5. 修改过的文件

- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)
- [eval/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/README.md)

### 6. 验证与测试

- 跑了什么命令
  - `sed -n '1,260p' docs/TASK_QUEUE.md`
  - `sed -n '1,260p' docs/SESSION_LOG.md`
  - `sed -n '1,260p' docs/PROJECT_MASTER_PLAN.md`
  - `sed -n '1,260p' README.md`
  - `sed -n '1,260p' eval/run_eval.py`
  - `sed -n '1,260p' eval/golden/ask_cases.json`
  - `sed -n '1,260p' backend/tests/test_eval_runner.py`
  - `sed -n '1,260p' backend/app/services/resume_workflow.py`
  - `sed -n '1,260p' backend/app/indexing/ingest.py`
  - `sed -n '1,260p' backend/app/indexing/store.py`
  - `sed -n '1,320p' backend/app/graphs/ingest_graph.py`
  - `sed -n '1,260p' backend/app/services/ask.py`
  - `sed -n '1,260p' plugin/src/views/KnowledgeStewardView.ts`
  - `sed -n '1,260p' plugin/src/writeback/applyProposalWriteback.ts`
  - `rg -n ...` 针对 pending approvals 排序字段、scoped ingest / FTS 重建、`pendingWritebackResult` 与 resume 失败分支做定点检索
- 结果如何
  - 已确认 `TASK-029` 是唯一可绑定的 medium，且 2026-03-17 应分配的 `session_id` 为 `SES-20260317-04`。
  - 已确认 freshness 和 CLI parity 仍不值得升为新的 medium。
  - 已确认新增 `TASK-030` 到 `TASK-033` 都有足够的代码事实支撑，且边界独立、验收可写清。
  - 已确认 [eval/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/README.md) 存在与当前实现状态不一致的过时描述，已在本次文档同步中修正。
- 哪些没法验证
  - 本次没有业务代码改动，因此没有新的运行时链路可做 unittest、集成测试或手工功能验证。
  - 新增任务本身只完成登记，尚未实现，不能把未来验收条件写成“已验证通过”。
- 哪些只是静态修改
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)
  - [eval/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/README.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 唯一扩展是为了重新分级 backlog，额外补读了 pending inbox、writeback、resume_workflow、scoped ingest、FTS 写库和 ask groundedness 相关实现；这些都直接服务于 `TASK-029` 的队列拆解，不构成新的功能推进。
- 本次没有顺手实现 post-writeback ingest、跨会话恢复、增量 FTS 或 ask runtime gate，只做了文档治理。

### 8. 未解决问题

- approval 成功后的目标 note 仍不会自动刷新索引，写回后 ask / digest 可能继续读取旧内容。
- 本地写回成功但 resume 失败时，恢复入口仍停留在面板内存态；插件重启后无法继续“只补记账、不重复写回”。
- scoped ingest 仍整库重建 FTS，一旦被写回链路频繁复用，成本会放大。
- ask 仍只能在离线 eval 中暴露 `unsupported_claim`，线上回答还没有最保守的 semantic gate。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果下一会话继续跳过 `TASK-030`，项目会出现“本地笔记已改，但问答 / digest 仍读旧索引”的明显可信度断层。
- 风险：如果把“本地写回成功但 resume 失败”的恢复问题继续当成小问题，面试里会被直接追问为什么你的审计链路只能靠当前面板不关闭才能自洽。
- 技术债：当前 pending inbox 已有排序和时间戳，但 freshness 仍停留在 UI 提示层，没有生命周期治理。
- 技术债：groundedness 规则仍以 term overlap 为主，若直接放大使用边界而不先做保守 gate，会引入误杀风险。
- 假设：下一批主线 medium 会话应优先从 `TASK-030`、`TASK-031`、`TASK-032`、`TASK-033` 中按顺序推进，而不是重新发散到未登记的大任务。

### 10. 下一步最优先任务

1. 绑定 `TASK-030`，让写回成功后的目标 note 自动进入 scoped ingest，补齐索引一致性缺口。
2. 再推进 `TASK-031`，为“本地写回成功但后端记账失败”的场景补跨会话恢复入口。
3. 随后进入 `TASK-032` 与 `TASK-033`，分别解决 scoped ingest 的整库 FTS 重建问题，以及 ask runtime 缺少 groundedness gate 的问题。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)
- [plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts)
- [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py)
- [backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py)
- [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)
- [backend/tests/test_resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_resume_workflow.py)
- [backend/tests/test_ingest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ingest_workflow.py)
- [backend/tests/test_indexing_ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_ingest.py)
- [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)
- [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)

### 12. 当前最容易被面试官追问的点

- 你为什么把“写回后最小增量 ingest”从以前的 `small` 升成了新的 `TASK-030`？如果回答成“现在顺手做一下比较方便”，会很像拍脑袋。正确回答必须落到前置条件变化：`TASK-019` 和 `TASK-026` 之后，写回和 scoped ingest 都已真实存在，索引陈旧已经从“附带优化”变成“主链路一致性缺口”。
- 你为什么不继续把“本地写回成功但 resume 失败”留在插件重试提示里，而要单独拆 `TASK-031`？如果回答只有“体验不好”，会显得太浅。真正的问题是审计 / checkpoint 与本地副作用解耦后，系统缺少跨会话恢复控制面，无法证明幂等与可追责。
- 你为什么不直接把 ask 的 groundedness 问题做成 LLM judge，而是先登记保守 runtime gate？如果回答不出“低噪声、可回归、失败即降级”的工程理由，会暴露你只会堆概念，不会控线上风险。

## [SES-20260317-03] 为 ask 增加语义级 groundedness 离线评估

- 日期：2026-03-17
- 类型：`Eval`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-028`
- 本会话唯一目标：在不改 ask 主 contract 的前提下，为 ask 的离线 eval 增加最小语义级 groundedness / answer-citation consistency 检查，并补对应 golden case 与测试

### 1. 本次目标

- 在 `TASK-020` 已落地编号级 citation alignment、`TASK-021` 已有最小 eval runner 的前提下，补 ask 侧“编号合法但语义越界”的离线评估空白。
- 保持改动严格收敛在 eval 层，不把 groundedness 启发式规则直接塞进 ask runtime 主链路，也不改 `AskWorkflowResult` 外层 contract。
- 让新场景继续可在不依赖联网 provider 的前提下稳定执行，避免把 `TASK-028` 做成高噪声、低复现性的 judge 实验。

### 2. 本次完成内容

- 确认 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中 `TASK-028` 是当前唯一可执行的 `planned / scope=medium` 任务，且 2026-03-17 当天 `SES-20260317-01`、`SES-20260317-02` 已占用，因此本次会话分配 `SES-20260317-03`。
- 更新 [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)，新增：
  - `ask_groundedness` 快照字段
  - `grounded / unsupported_claim / citation_missing / citation_invalid / not_generated_answer` 最小分桶
  - 基于 cited evidence 的 rule-based term extraction 与 unsupported term 输出
  - `ask_groundedness` 的结构化断言入口，保证 golden case 可直接验证 consistency bucket
- 更新 [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py) 中的 `ask_basic` fixture，使 deterministic evidence 不再只停留在英文标题，而是包含中文“问答结果需要携带引用”的真实支撑片段。
- 更新 [eval/golden/ask_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/ask_cases.json)：
  - 收敛原合法 generated-answer case，使其引用真正命中的 evidence chunk
  - 新增两条“编号合法但语义越界 / 过度概括”的 deterministic bad case
  - 为 grounded case 和 semantic overclaim case 都补 `ask_groundedness` 预期断言
- 更新 [backend/tests/test_eval_runner.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_eval_runner.py)，新增 groundedness bucket 与 semantic overclaim case 的 runner 测试。
- 生成验证结果文件：
  - [eval/results/eval-20260317-072723.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/results/eval-20260317-072723.json)
  - [eval/results/eval-20260317-072736.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/results/eval-20260317-072736.json)
  - [eval/results/eval-20260317-073846.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/results/eval-20260317-073846.json)
- 在收尾中同步更新 [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)、[docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)、[docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 与 [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)，把主线路线从 `TASK-028` 前移到新的队列治理任务。

### 3. 本次未完成内容

- 没有把 `unsupported_claim` 分桶直接接入 ask runtime 拦截或自动降级。
- 没有引入 LLM-as-a-judge、在线 judge 平台或 richer metrics dashboard。
- 没有扩展到插件 ask UI、真实联网 provider 长尾输出对齐，或宿主级 Obsidian 端到端评估。
- 没有继续拆下一批 medium 功能实现；本次只补齐 `TASK-028` 并在收尾中登记后续队列入口。

### 4. 关键决策

- groundedness 先落在离线 eval，而不是直接进线上回答拦截；原因是本次目标是稳定暴露风险、补回归基线，而不是把启发式规则直接变成用户可见决策。
- 语义一致性首版不依赖 LLM judge，而是使用 deterministic fixture + cited evidence term overlap；原因是 `TASK-028` 的验收重点是“可复现、可落盘、可回归”，不是“模型评委看起来更聪明”。
- `ask_groundedness` 没有写进 `AskWorkflowResult` 或插件 ask contract；原因是队列已经明确把本任务边界限定在 eval 层，不能借机扩成新的协议改造。
- grounded case 最终使用 `[2]` 而不是 `[1]`；原因是 `ask_basic` fixture 的第一个候选是标题 chunk，真正承载“问答结果需要携带引用”事实的是第二个 evidence chunk。如果继续把 `[1]` 当 grounded，会把错误样本伪装成“规则误报”。

### 5. 修改过的文件

- [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
- [eval/golden/ask_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/ask_cases.json)
- [backend/tests/test_eval_runner.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_eval_runner.py)
- [eval/results/eval-20260317-072723.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/results/eval-20260317-072723.json)
- [eval/results/eval-20260317-072736.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/results/eval-20260317-072736.json)
- [eval/results/eval-20260317-073846.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/results/eval-20260317-073846.json)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 6. 验证与测试

- 跑了什么命令
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_eval_runner -v`
  - `./.conda/knowledge-steward/bin/python eval/run_eval.py --case-id ask_fixture_generated_answer_citation_valid --case-id ask_fixture_semantic_overclaim_writeback --case-id ask_fixture_semantic_overclaim_governance`
  - `./.conda/knowledge-steward/bin/python eval/run_eval.py`
- 结果如何
  - `tests.test_eval_runner` 最终 4 个测试全部通过，新增 groundedness bucket 与 semantic overclaim 覆盖已生效。
  - 定向 ask eval 3 条 case 全部通过，说明 grounded case 与 `unsupported_claim` bad case 都能稳定落盘。
  - 全量 eval 13 条 case 全部通过，没有打断 digest / proposal / `resume_workflow` 既有回归。
- 哪些没法验证
  - 没有验证真实联网 provider 的长尾改写、强 paraphrase 或多段富文本输出在 groundedness 规则下的表现。
  - 没有验证真实 Obsidian 宿主里的 ask UI，因为本次明确不涉及插件 ask 交互。
  - 没有验证把 groundedness bucket 直接拉入线上 gate 的副作用，因为这本来就在 out of scope。
- 哪些只是静态修改
  - [eval/golden/ask_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/ask_cases.json)
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 唯一伴随改动是把 `ask_basic` fixture 的 grounded case 从 `[1]` 收敛到 `[2]`，以及补 `ask_groundedness` 快照 / 断言。这些都直接服务于 `TASK-028` 的“稳定离线评估”验收，不构成新的 medium 功能。
- 本次没有顺手推进 ask runtime gate、插件 ask UI 或新的检索能力。

### 8. 未解决问题

- 当前 groundedness 仍是 rule-based term overlap，遇到强 paraphrase、近义表达或更复杂的中文分词场景，仍可能误报或漏报。
- 当前 `unsupported_claim` 只存在于离线 eval 结果，不会自动阻断线上回答。
- 当前还没有 failure type 聚合、term normalization、停用词治理和 richer metrics。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果把这轮实现包装成“ask 已经 fully grounded”，会被直接追问为什么线上回答仍可能带着合法编号输出语义越界结论；当前事实只是“离线 eval 已能显式抓出这一类 bad case”。
- 技术债：groundedness term extractor 当前用中文短窗 + 英文 token 的轻量启发式，稳定性高于 LLM judge，但并不等于语义理解充分。
- 技术债：`ask_groundedness` 目前只用于结果文件和断言，不参与 runtime trace 聚合与长期指标统计。
- 假设：下一次主线 medium 会话不应凭直觉直接跳进某个新功能，而应先绑定 `TASK-029`，重新拆解 `TASK-028` 之后的下一批队列任务。

### 10. 下一步最优先任务

1. 绑定 `TASK-029`，继续拆解 `TASK-028` 之后的下一批 medium 队列任务。
2. 继续以 `small` 形式评估是否需要引入 LLM judge 作为 groundedness 抽样辅助。
3. 继续以 `small` 形式收敛 groundedness rule-based term extractor 的停用词 / allowlist，降低中文短窗误报。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
- [eval/golden/ask_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/ask_cases.json)
- [backend/tests/test_eval_runner.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_eval_runner.py)
- [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 12. 当前最容易被面试官追问的点

- 你为什么把 `unsupported_claim` 先做成离线 eval 分桶，而不是直接线上拦截？如果回答成“先简单做一下”，会显得你没做过真实质量门控。正确回答必须落到误判成本、可复现性、用户信任边界和 why-now scope control。
- 你这个 groundedness 规则为什么不用 LLM judge？如果回答只有“为了省钱”，会很像玩具项目。你得把 deterministic 回归、噪声控制、样本稳定复现和结果可比性讲明白。
- 你怎么证明这是“语义越界”，而不是 retrieval 本身没召回到足够证据？如果你分不清“answer 超出当前 cited evidence”与“retrieval coverage 不足”这两个失败面，面试里会被继续追问到失守。

## [SES-20260317-02] 让 `INGEST_STEWARD` 在 scoped note 上产出首条治理 proposal

- 日期：2026-03-17
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-027`
- 本会话唯一目标：让 `INGEST_STEWARD` 在 scoped note 上产出首条真实治理 `proposal + waiting_for_approval checkpoint`

### 1. 本次目标

- 在 scoped ingest 路径上补一条真实可用的 proposal / waiting 主线，而不是继续让“新笔记治理”只停留在 scoped sync。
- 复用现有 `proposal`、pending inbox、审批面板、`/workflows/resume` 与受限写回链路，不新起第二套审批协议。
- 严格限制在单 note、规则驱动、现有受限 patch op 边界内，不扩成 ask proposal、多 note proposal merge 或跨 note duplicate/conflict 引擎。

### 2. 本次完成内容

- 确认 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中 `TASK-027` 是当前最合适绑定的 `P0 medium` 任务，并分配 `SES-20260317-02`。
- 新增 [backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py)，实现首版 scoped ingest proposal builder：
  - 只接受单 note scoped ingest
  - 只使用 parser 已有的标题、heading、wikilink、task_count、note_type、template_family 等结构信号
  - 只生成插件现有已支持的 `merge_frontmatter` / `insert_under_heading`
  - 在无足够治理信号时显式返回 no-proposal skip reason，而不是硬造 proposal
- 更新 [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)：
  - 新增 ingest proposal / waiting 分支
  - 新增 proposal + `waiting_for_approval` checkpoint 原子落盘
  - 新增 no-proposal fallback 与 proposal skipped trace
  - 新增 waiting 线程拒绝 `resume_from_checkpoint`，强制审批恢复走 `/workflows/resume`
- 更新 [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)，让 `/workflows/invoke` 在命中 ingest proposal 时返回 `202 + waiting_for_approval + proposal + ingest_result`，并在显式 proposal 模式无可安全 proposal 时返回 no-proposal message。
- 更新 [backend/tests/test_ingest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ingest_workflow.py)，新增 proposal 产出、waiting checkpoint、pending inbox、no-proposal fallback 与 waiting thread resume 拒绝覆盖。
- 在收尾中同步更新 [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)、[docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)、[docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 与 [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)，把主线路线从 `TASK-027` 前移到 `TASK-028`。

### 3. 本次未完成内容

- 没有做 ask proposal 化。
- 没有做多 note proposal 合并。
- 没有做跨 note duplicate / conflict 分析。
- 没有做写回后自动触发增量 ingest。

### 4. 关键决策

- ingest proposal 没有对所有 scoped ingest 默认开启，而是要求显式 `metadata.approval_mode="proposal"`；原因是当前要新增的是首条治理主线，不是把既有 scoped sync 默认退化成全部卡审批。
- 首版 proposal 严格限制为单 note scoped ingest；原因是如果一开始做多 note proposal merge，本会话会直接越过 `TASK-027` 的首条 proposal 边界。
- proposal builder 只使用 parser 当前已实现的结构信号，不把主计划中的 duplicate/conflict/LLM 分析设计稿包装成既有能力。
- proposal 只生成现有插件已支持的 patch op；原因是如果补新的 patch 执行语义，会把任务扩到写回层 medium。
- waiting proposal 与 checkpoint 采用原子落盘；原因是必须避免 pending inbox、审批面板与 thread 恢复状态错位。

### 5. 修改过的文件

- [backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py)
- [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/tests/test_ingest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ingest_workflow.py)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 6. 验证与测试

- 跑了什么命令
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_ingest_workflow -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_digest_workflow tests.test_resume_workflow -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
- 结果如何
  - `tests.test_ingest_workflow` 新增 proposal / waiting / fallback 用例全部通过。
  - `tests.test_digest_workflow` 与 `tests.test_resume_workflow` 全部通过，说明现有审批恢复链路未被回归打断。
  - 后端全量 60 个测试全部通过。
- 哪些没法验证
  - 没有在真实运行中的 FastAPI server 上手工 curl 一次 ingest proposal 返回体。
  - 没有在真实 Obsidian 宿主里点击一遍 ingest proposal 的端到端审批流程。
- 哪些只是静态修改
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 唯一伴随改动是新增 proposal builder、waiting 分支、no-proposal fallback 与 waiting thread 恢复边界，这些都直接服务于 `TASK-027` 的验收，不构成新的 medium 功能。

### 8. 未解决问题

- 当前 ingest proposal 仍是规则驱动、单 note、单次 patch 模板输出。
- 当前还没有跨 note duplicate / conflict 证据链。
- 当前还没有写回成功后的自动增量 ingest 或 dirty 标记恢复。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果把本轮实现包装成“新笔记治理全链路已完成”，会被追问 evidence 是否真的来自跨 note 分析；当前事实只是“单 note scoped ingest 已具备首条 proposal 主线”。
- 技术债：proposal 触发仍依赖 parser 已有信号，误报 / 漏报概率尚未量化。
- 假设：下一次主线 medium 会话应前移到 `TASK-028`，而 ingest proposal 的风险分级 / patch 模板收敛继续留在 `small`。

### 10. 下一步最优先任务

1. 绑定 `TASK-028`，为 ask 增加语义级 groundedness 离线评估。
2. 继续以 `small` 形式收敛新笔记治理 proposal 的风险分级与 patch 模板。
3. 继续以 `small` 形式评估 scoped ingest 的 FTS 成本与 CLI parity。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
- [eval/golden/ask_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/ask_cases.json)
- [backend/tests/test_eval_runner.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_eval_runner.py)
- [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)

### 12. 当前最容易被面试官追问的点

- 你说 `INGEST_STEWARD` 已经进入真实 proposal 主线了，那为什么首版 proposal 只基于单 note parser 信号，而不是跨 note duplicate/conflict 分析？如果回答还是“后面会接 LLM”，会显得你在拿设计图冒充实现。你必须把当前输入边界、可验证证据、现有 patch 能力和 why-now trade-off 讲清楚。
- 为什么要显式 `metadata.approval_mode="proposal"`，而不是让所有 scoped ingest 默认进入 waiting？如果只说“为了简单”，会像没做过真实系统；你得把兼容性、用户体验回退、恢复语义和副作用边界讲明白。

## [SES-20260317-01] 为 `INGEST_STEWARD` 打开 scoped note ingest 入口

- 日期：2026-03-17
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-026`
- 本会话唯一目标：让 `INGEST_STEWARD` 支持 `note_path / note_paths` 范围执行，结束当前 scoped ingest 被显式拒绝、只能整库同步的状态

### 1. 本次目标

- 为 `/workflows/invoke` 的 `INGEST_STEWARD` 打开单 note 和 note 列表两种 scoped ingest 入口，而不是继续把 `note_path / note_paths` 当成“协议里有、能力上拒绝”。
- 保持现有 full-vault ingest、SQLite FTS 与 checkpoint 主链路不回退，只在当前任务边界内补 scoped note 路径。
- 在不扩成 proposal、审批节点或自动写回后同步的前提下，补齐最小路径校验、恢复边界和测试覆盖。

### 2. 本次完成内容

- 确认 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中 `TASK-026` 是当前最合适绑定的 `P0 medium` 任务，且 2026-03-17 当天没有已占用会话号，因此本次会话分配 `SES-20260317-01`。
- 更新 [backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py)，新增：
  - `resolve_requested_markdown_notes()` 与 vault 根目录规范化逻辑
  - 对 `note_path / note_paths` 的 vault 内路径校验、`.md` 后缀校验、去重与稳定排序
  - `ingest_vault()` 的 programmatic scoped ingest 能力，使其既可全量遍历，也可只同步目标 note 集合
- 更新 [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)：
  - 移除对 scoped ingest 的硬拒绝
  - 把请求中的单 note / 多 note 统一收敛为规范化 `note_paths`
  - 在 trace 中补 `ingest_scope`、`requested_note_count` 与 `requested_note_paths`
  - 让 graph 执行节点按 scoped note 集合调用 ingest
- 更新 [backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py)，为线性 checkpoint runner 增加 `resume_match_fields`，并在 checkpoint miss 时暴露 scope mismatch 细节，避免同一 `thread_id` 在不同 ingest scope 间误复用已完成 checkpoint。
- 更新 [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)，让 `INGEST_STEWARD` 在 scoped 成功时返回 `Ingest workflow completed with scoped note sync.`，与 full-vault 成功消息区分。
- 更新测试：
  - [backend/tests/test_indexing_ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_ingest.py)：覆盖单 note scoped ingest、note list scoped ingest 与 scoped 后 FTS 一致性
  - [backend/tests/test_ingest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ingest_workflow.py)：覆盖 scoped workflow 成功、vault 外路径拒绝、以及 scope 变更时不应错误 resume 旧 checkpoint
- 在收尾中同步更新 [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)、[docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)、[docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 与 [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)，把主线路线从 `TASK-026` 前移到 `TASK-027`。

### 3. 本次未完成内容

- 没有让 `INGEST_STEWARD` 产出治理 proposal；这仍属于 `TASK-027`。
- 没有做写回后自动触发 scoped ingest。
- 没有把 scoped ingest 的 FTS 同步策略优化成更细粒度增量更新。
- 没有为 `python -m app.indexing.ingest` CLI 暴露 `--note-path / --note-paths` 参数。

### 4. 关键决策

- scoped ingest 的 state 没有同时保留 `note_path` 和 `note_paths` 两种语义，而是统一收敛为规范化后的 `note_paths` 列表；原因是 checkpoint 恢复需要稳定的 scope 指纹，不能让“同一批 note 因参数形态不同”产生恢复串味。
- scoped ingest 后仍然保留整张 FTS 重建，而不是顺手改成局部同步；原因是本任务验收要求是“一致性可用”，不是“性能最优”，先把写库和检索可用性维持在单一同步点。
- checkpoint runner 新增 `resume_match_fields=("note_paths",)`，而不是继续只按 `thread_id + graph_name` 命中；原因是 scoped ingest 的输入边界已经变成业务语义的一部分，如果 scope 不参与恢复匹配，同一 thread 的历史完成态会直接污染后续请求。

### 5. 修改过的文件

- [backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py)
- [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)
- [backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/tests/test_indexing_ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_ingest.py)
- [backend/tests/test_ingest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ingest_workflow.py)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 6. 验证与测试

- 跑了什么命令
  - `./.conda/knowledge-steward/bin/python -m unittest backend.tests.test_indexing_ingest backend.tests.test_ingest_workflow -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_indexing_ingest tests.test_ingest_workflow -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
- 结果如何
  - 第一条命令在仓库根目录执行时因既有测试导入约定触发 `ModuleNotFoundError: app`，随后按项目现有方式切到 `backend/` 目录重跑；这不是 scoped ingest 逻辑缺陷。
  - 定向 10 个测试全部通过，覆盖 scoped ingest、非法路径拒绝和 checkpoint scope 防串味。
  - 后端全量 56 个测试全部通过，没有回归 ask / digest / eval / resume / retrieval / store 既有行为。
- 哪些没法验证
  - 没有在真实运行中的 FastAPI dev server 上用 curl 手工跑一次 scoped ingest。
  - 没有在真实 Obsidian 宿主或插件 UI 中联动 scoped ingest。
  - 没有对大 Vault 下 scoped ingest 的 FTS 重建耗时做基准。
- 哪些只是静态修改
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 唯一伴随改动是 [backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py) 的 checkpoint scope 匹配增强；这直接服务于 `TASK-026` 的“scoped ingest + 恢复不串味”验收，不构成新的 medium 功能。

### 8. 未解决问题

- scoped ingest 当前仍在每轮同步结束后整库重建 FTS，大 Vault 下的代价还没有实测。
- CLI 入口目前仍只支持全量 ingest，不支持直接传 `--note-path / --note-paths` 做局部调试。
- `INGEST_STEWARD` 现在只解决“局部同步”，还没有进入“新笔记治理 proposal”主线。

### 9. 新增风险 / 技术债 / 假设

- 风险：scoped ingest 已可用，但如果后续直接把“支持局部同步”包装成“已完成增量索引优化”，面试时会被追问为什么还在整库重建 FTS。
- 技术债：checkpoint runner 目前只对 `note_paths` 做 scope 匹配；这是因为当前 ingest 语义只由目标 note 集合决定。若后续再引入更强的 ingest metadata scope，需要同步扩展恢复指纹。
- 假设：下一次主线 medium 会话应前移到 `TASK-027`，在 scoped ingest 之上让 `INGEST_STEWARD` 产出首条真实治理 proposal，而不是继续在 scoped ingest 线上扩第二个 medium。

### 10. 下一步最优先任务

1. 绑定 `TASK-027`，让 `INGEST_STEWARD` 在 scoped note 上产出首条治理 proposal。
2. 随后推进 `TASK-028`，补 ask 的语义级 groundedness 离线评估。
3. 把 scoped ingest 的 FTS 代价评估和 CLI parity 保持在派生 `small` 范围内处理。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)
- [backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py)
- [backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py)
- [backend/app/indexing/parser.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/parser.py)
- [backend/tests/test_ingest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ingest_workflow.py)

### 12. 当前最容易被面试官追问的点

- 你为什么 scoped ingest 已经落地了，却还在每次 scoped sync 后整库重建 FTS？如果回答只是“实现简单”，会显得你没做过真实索引系统。正确回答必须把 trade-off 讲清楚：这轮任务优先守的是“目标 note 写库后检索仍一致”的单一同步点，不是吞掉所有大 Vault 性能问题；同时你还要能继续解释，为什么又补了 `note_paths` 级 checkpoint 匹配，而不是只按 `thread_id` 恢复，否则同一个 thread 在不同 scope 下会直接误命中旧完成态。

## [SES-20260316-03] 实现待审批 proposal 查询接口与插件审批收件箱

- 日期：2026-03-16
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-025`
- 本会话唯一目标：去掉当前插件只能“实时触发 `DAILY_DIGEST` proposal”或“打开本地 demo”才能进入审批面板的断层，为真实 waiting proposal 提供最小收件箱

### 1. 本次目标

- 为后端补最小 pending proposal 查询入口，返回插件加载收件箱所需的必要字段，而不是继续让插件靠命令即时触发或本地 demo 注入上下文。
- 在插件侧边栏增加最小待审批列表，并把真实 waiting proposal 接回现有审批面板，而不是重做一套审批 UI。
- 在不扩成通知中心、后台轮询、复杂筛选或多 reviewer 流程的前提下，补齐 `TASK-025` 的最小产品化入口。

### 2. 本次完成内容

- 确认 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中 `TASK-025` 是当前最合适绑定的 `P0 medium` 任务，且 2026-03-16 当天 `SES-20260316-01`、`SES-20260316-02` 已占用，因此本次会话分配 `SES-20260316-03`。
- 更新 [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)，新增 `PendingApprovalItem` 与 `WorkflowPendingApprovalsResponse`，把待审批收件箱所需字段钉成独立 contract。
- 更新 [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)，新增 `PendingApprovalRecord` 与 `list_pending_approval_records()`：
  - 显式以 `workflow_checkpoint.checkpoint_status='waiting_for_approval'` 作为“当前仍待审批”的状态来源
  - 再联合 `proposal` 主表补齐 `summary`、`target_note_path`、`risk_level` 与完整 `proposal`
  - 跳过缺失 proposal 或 `thread_id` 不一致的脏记录，避免收件箱把已漂移状态重新暴露给插件
- 更新 [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)，新增 `GET /workflows/pending-approvals`，返回按更新时间排序的最小 pending inbox 列表。
- 更新 [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts) 与 [plugin/src/api/client.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/api/client.ts)，补齐 pending approval 类型和 `listPendingApprovals()` 客户端调用。
- 更新 [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)，新增：
  - `Pending Inbox` 区块与手动刷新入口
  - 待审批卡片列表及“Load”操作
  - inbox 空态、接口错误、陈旧 proposal 提示
  - 提交 approve 成功后从本地 inbox 移除已处理 proposal
  - 对 404 / 409 这类 stale proposal 冲突做前端降级提示并触发 inbox 刷新
- 更新 [plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts)，新增 `Refresh pending approvals` 命令，并在 `Load daily digest approval` 成功后顺手刷新收件箱。
- 更新 [plugin/styles.css](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/styles.css)，补充 inbox 区块头部与选中态样式。
- 更新测试：
  - [backend/tests/test_indexing_store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_store.py)：验证只返回 `waiting_for_approval` checkpoint 对应 proposal
  - [backend/tests/test_digest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_digest_workflow.py)：验证 waiting digest proposal 能出现在 pending inbox
  - [backend/tests/test_resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_resume_workflow.py)：验证 proposal 经 `/workflows/resume` 处理后从 inbox 消失
- 在收尾中确认：`TASK-025` 已满足“存在最小 pending proposal 查询入口、插件侧边栏可展示并加载真实 proposal、无 pending / stale / 错误时有明确提示、存在最小测试和构建验证”四条验收标准。

### 3. 本次未完成内容

- 没有做后台轮询、通知中心、复杂筛选、分页或历史归档。
- 没有把 freshness 排序、过期阈值或更复杂的 stale item 治理扩成单独子系统。
- 没有把 ask / ingest workflow 一并 proposal 化；真实 waiting proposal 仍主要来自 `DAILY_DIGEST`。

### 4. 关键决策

- 待审批收件箱没有直接扫描 `proposal` 表，而是显式以 `workflow_checkpoint.waiting_for_approval` 为准，再 join `proposal` 主表；原因是 `proposal` 是业务事实存储，不等于“当前仍待审批”的状态源。如果只扫 `proposal`，已审批或过期 proposal 很容易重新混进收件箱。
- 插件 inbox 没有新起一套审批视图，而是把“列表选择”接回现有 `approvalContext` 面板；原因是本轮要补的是入口治理，不是重写审批 UI。
- 对 stale proposal 只做最小降级：前端在加载/提交冲突时提示并刷新 inbox，而不是本轮继续上 freshness 规则、自动失效或后台同步；原因是这些都属于 `small` 派生项，不能把 `TASK-025` 扩成第二个 medium。

### 5. 修改过的文件

- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/tests/test_indexing_store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_store.py)
- [backend/tests/test_digest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_digest_workflow.py)
- [backend/tests/test_resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_resume_workflow.py)
- [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)
- [plugin/src/api/client.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/api/client.ts)
- [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)
- [plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts)
- [plugin/styles.css](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/styles.css)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 6. 验证与测试

- 跑了什么命令
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_indexing_store tests.test_digest_workflow tests.test_resume_workflow -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
  - `cd plugin && npm run build`
  - `cd plugin && npm test`
- 结果如何
  - 后端定向 24 个测试全部通过，覆盖 store / digest / resume 新增的 pending inbox 行为。
  - 后端全量 52 个测试全部通过，没有回归 ask / ingest / digest / eval / resume / retrieval 既有行为。
  - 插件 `npm run build` 通过。
  - 插件现有 5 个写回相关测试全部通过。
- 哪些没法验证
  - 没有在真实 Obsidian 宿主里手工点击 inbox 列表、加载 proposal 并完成一次 UI 级端到端审批。
  - 没有验证多窗口同时打开同一 stale proposal 时的宿主交互细节。
- 哪些只是静态修改
  - [plugin/styles.css](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/styles.css)
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 唯一伴随改动是为 contract、store helper、插件 client 和样式补最小适配，以及把 stale proposal 冲突提示纳入前端降级逻辑；这些都直接服务于 `TASK-025` 的验收，不构成新的 medium 功能。

### 8. 未解决问题

- pending inbox 目前只有最小更新时间排序，没有 freshness 阈值、风险排序或分组策略。
- 当前 waiting proposal 仍主要来自 `DAILY_DIGEST`，多 workflow 收件箱还没出现真实混流场景。
- 本地写回成功但后端 resume 失败后的跨会话待同步入口仍未实现，当前仍只靠单次面板内存态保护。

### 9. 新增风险 / 技术债 / 假设

- 风险：pending inbox 当前按 checkpoint `updated_at` 做最小排序，但还没有 freshness 提示或自动失效规则；如果后续直接把“能列出来”包装成“收件箱已产品化”，面试时会被追问 stale item 治理。
- 技术债：`GET /workflows/pending-approvals` 现在直接返回完整 `proposal`，对首版收件箱足够，但如果后续 proposal 体积增长过快，接口可能需要拆成 summary list + detail load 两层。
- 假设：下一次主线 medium 会话应按队列顺序进入 `TASK-026`，优先补 scoped note ingest，而不是继续在 inbox 上扩排序、轮询或通知中心。

### 10. 下一步最优先任务

1. 绑定 `TASK-026`，为 `INGEST_STEWARD` 打开 scoped note ingest 入口。
2. 随后推进 `TASK-027`，让新笔记治理也能产出真实 waiting proposal。
3. 保留 `TASK-025` 的既有 `small` 派生项，后续补 freshness 提示或更稳的排序字段。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py)
- [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)
- [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- [backend/tests/test_ingest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ingest_workflow.py)
- [backend/tests/test_indexing_ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_ingest.py)
- [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)

### 12. 当前最容易被面试官追问的点

- 你为什么不直接把 `proposal` 表当成待审批列表，而要再查 `workflow_checkpoint`？如果回答只是“这样更安全”，会显得你没有分清“业务事实存储”和“当前等待态”的 source of truth。正确回答必须落到状态语义：`proposal` 记录的是曾经生成过什么，`workflow_checkpoint.waiting_for_approval` 才表示它现在真的还在待处理。

---

## [SES-20260316-02] 将 `resume_workflow` / `writeback_result` 纳入最小离线 eval

- 日期：2026-03-16
- 类型：`Eval`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-024`
- 本会话唯一目标：在 ask / digest / proposal 已有最小 golden baseline 的前提下，把 `resume_workflow + writeback_result` 的高风险副作用链路补进统一离线回归

### 1. 本次目标

- 在不扩成真实 Obsidian 宿主自动化、复杂 dashboard 或协议重构的前提下，把 approve / reject / writeback success / failure 的代表场景纳入 `eval/run_eval.py`。
- 让离线 eval 不再只停在 `waiting_for_approval`，而是能验证 `/workflows/resume` 返回、checkpoint 持久化和 `audit_log` 记账的一致性。
- 复用现有 `resume_workflow` 单测已验证的稳定 fixture 边界，而不是另起一套演示专用协议。

### 2. 本次完成内容

- 确认 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中 `TASK-024` 是当前最合适绑定的 `P0 medium` 任务，且 2026-03-16 当天 `SES-20260316-01` 已占用，因此本次会话分配 `SES-20260316-02`。
- 更新 [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)，新增：
  - `resume` entrypoint 分支，允许对 `/workflows/resume` 做离线 golden 回归
  - deterministic `resume_waiting_digest` fixture，直接 seed waiting proposal 与 checkpoint
  - `response + checkpoint + audit_log` 三层快照构造与断言，避免只测表层返回 contract
- 新增 [eval/golden/resume_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/resume_cases.json)，覆盖：
  - reject waiting proposal
  - approve + successful writeback result
  - approve + failed writeback result
- 更新 [backend/tests/test_eval_runner.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_eval_runner.py)，新增 `resume_workflow` eval 场景执行验证。
- 生成一次真实结果文件 [eval/results/eval-20260316-053219.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/results/eval-20260316-053219.json)，证明新增 case 可落盘执行。
- 在收尾中确认：`TASK-024` 已满足“覆盖 approve / reject / writeback success / failure 代表 case、结果文件继续按时间戳落盘、不依赖外部 provider 或真实宿主、存在最小测试验证”四条验收标准。

### 3. 本次未完成内容

- 没有把 eval 扩成真实 Obsidian 宿主端到端自动化。
- 没有为 writeback / resume eval 增加失败类型聚合或 richer metrics。
- 没有把 ask 语义级 groundedness 评估一并塞进本轮；这仍属于 `TASK-028`。

### 4. 关键决策

- 没有把 `TASK-024` 做成“先跑一遍真实 digest proposal，再接一遍 resume”的多阶段编排，而是直接 seed deterministic waiting proposal fixture；原因是本轮要锁定的风险是审批恢复事务一致性，不是再重复验证上游 digest 文案。
- `resume` 场景的 golden 快照显式拉入 checkpoint 和 `audit_log`，而不是只断言 HTTP 返回；否则最危险的坏场景会退化成“接口返回看起来对，持久化事实其实漂了”。
- 没有引入真实插件宿主或网络 provider；当前回归优先级是稳定、可重复和能进 CI，而不是演示层面的“全栈真跑一遍”。

### 5. 修改过的文件

- [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
- [eval/golden/resume_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/resume_cases.json)
- [eval/results/eval-20260316-053219.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/results/eval-20260316-053219.json)
- [backend/tests/test_eval_runner.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_eval_runner.py)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 6. 验证与测试

- 跑了什么命令
  - `./.conda/knowledge-steward/bin/python -m unittest backend.tests.test_eval_runner -v`
  - `./.conda/knowledge-steward/bin/python eval/run_eval.py --case-id resume_fixture_reject_waiting_proposal --case-id resume_fixture_writeback_success --case-id resume_fixture_writeback_failure`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_resume_workflow -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
- 结果如何
  - `test_eval_runner` 3 个测试全部通过，新增 `resume_workflow` eval 场景稳定执行。
  - 定向 `run_eval.py` 3 条 `resume` case 全部通过，并生成 `eval/results/eval-20260316-053219.json`。
  - `resume_workflow` 定向 8 个测试全部通过。
  - 后端全量 49 个测试全部通过，没有回归 ask / digest / ingest / resume / retrieval 既有行为。
  - 一次从仓库根目录执行 `python -m unittest discover -s backend/tests -v` 出现 `ModuleNotFoundError: app`；确认这是测试工作目录不符合仓库既有约定导致的无效验证方式，不是本次代码回归，随后改回 `cd backend` 的既有执行方式后通过。
- 哪些没法验证
  - 没有在真实 Obsidian 宿主环境里做自动化或手工 E2E 验证。
  - 没有验证插件本地真实写回之后再进 `/workflows/resume` 的宿主级链路进入 eval。
- 哪些只是静态修改
  - [eval/golden/resume_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/resume_cases.json)
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 唯一伴随改动是让 `eval/run_eval.py` 支持第二个协议入口、补一个 deterministic resume fixture，并把 checkpoint / `audit_log` 持久化事实纳入断言；这些都直接服务于 `TASK-024` 的验收，不构成新的 `medium` 功能。

### 8. 未解决问题

- 当前离线 eval 仍不覆盖真实 Obsidian 宿主、副作用文件改动和插件 UI 交互。
- `resume_workflow` 回归虽然已覆盖成功 / 失败记账，但还没有失败类型聚合视图。
- ask 仍缺语义级 groundedness 离线评估，`TASK-028` 尚未开始。

### 9. 新增风险 / 技术债 / 假设

- 风险：`resume` eval 目前依赖 deterministic fixture；如果后续 proposal schema 或 checkpoint 状态字段演进过快，而不及时同步 fixture，可能出现“协议已变、回归样本还停在旧世界”的假绿风险。
- 技术债：`eval/run_eval.py` 现在已同时承载 `invoke` 和 `resume` 两类入口；如果后续继续叠更多控制面场景而不收敛抽象，runner 会逐渐膨胀。
- 假设：下一次主线 medium 会话应按队列顺序进入 `TASK-025`，优先补 waiting proposal 收件箱，而不是继续把 eval 线扩成更大的平台化工程。

### 10. 下一步最优先任务

1. 绑定 `TASK-025`，实现待审批 proposal 查询接口与插件审批收件箱。
2. 再进入 `TASK-026`，为 `INGEST_STEWARD` 打开 scoped note ingest 入口。
3. 随后推进 `TASK-027` 与 `TASK-028`，分别补新笔记治理 proposal 主线和 ask 语义级 groundedness eval。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- [backend/app/graphs/checkpoint.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/checkpoint.py)
- [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)
- [plugin/src/api/client.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/api/client.ts)
- [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)

### 12. 当前最容易被面试官追问的点

- 你现在说“`resume_workflow` 已进入离线回归”，那为什么还不做真实 Obsidian 宿主端到端自动化？如果回答只是“时间不够”或“单测已经够了”，会直接显得没做过高风险副作用系统。正确回答必须落到分层验证：本轮先把最危险的后端事务一致性面锁住，包括 HTTP contract、checkpoint 和 `audit_log` 的对齐；宿主自动化是另一个成本更高、稳定性更差的验证面，必须单独立项，而不是在 `TASK-024` 里顺手糊过去。

---

## [SES-20260316-01] 继续拆解 `TASK-021` 之后的下一批 medium 队列任务

- 日期：2026-03-16
- 类型：`Docs`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-023`
- 本会话唯一目标：基于 `TASK-021` 完成后的真实代码状态，重新拆解并登记下一批可执行 medium 任务，避免任务队列在 eval baseline 之后断档

### 1. 本次目标

- 在不推进任何新功能实现的前提下，基于真实代码与既有文档，补齐 `TASK-021` 之后的下一批 medium 队列任务。
- 判断哪些缺口已经收敛成新的中等粒度问题，哪些仍应保留为 `small / derived_tasks`，避免“杂项收尾包”式任务污染队列边界。
- 同步修正主文档里仍写着“Next Action = `TASK-023`”的过时描述，保持任务队列、会话日志和主文档路线一致。

### 2. 本次完成内容

- 确认 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中 `TASK-023` 是当前唯一可绑定的 `planned / scope=medium` 任务。
- 由于收尾发生在 2026-03-16，当天 `session_id` 尚未占用，本次会话最终分配 `SES-20260316-01`，而不是分析阶段临时推断的前一日编号。
- 按规则补读 [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md) 中 `SES-20260315-04`，确认上一会话已明确要求下一步优先绑定 `TASK-023`。
- 复核 [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)、[README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)、[eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)、[backend/tests/test_eval_runner.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_eval_runner.py)、[backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py)、[backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)、[backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py)、[plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts)、[plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts) 与 [plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts)，确认当前高风险缺口集中在：
  - `writeback / resume` 未进入离线 eval
  - 待审批 proposal 收件箱缺失
  - `INGEST_STEWARD` 仍拒绝 scoped note ingest
  - proposal 真实产出仍只停在 `DAILY_DIGEST`
  - ask 仍缺语义级 groundedness 离线评估
- 在 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中将 `TASK-023` 标记为 `completed`，并新增 `TASK-024` 到 `TASK-028` 五个后续 medium 任务。
- 保持“写回后最小增量 ingest”和“本地写回成功但 `/workflows/resume` 记账失败的跨会话恢复入口”为派生 `small`，没有把它们强行打包成一个新的 medium。
- 在 [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 中同步更新版本、最近更新时间和所有仍指向 `TASK-023` 的 `Next Action` 描述。
- 在 [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md) 中补一段最小路线同步，说明下一批 medium 优先级已经重新拆解。

### 3. 本次未完成内容

- 没有实现 `TASK-024` 到 `TASK-028` 中的任何业务能力；本会话只完成队列治理和文档同步。
- 没有把“写回后最小增量 ingest”和“跨会话恢复入口”升级成新的 medium，因为当前证据仍更支持它们继续作为派生 `small`。
- 没有新增任何测试、接口或代码逻辑；本次收尾只落文档，不改业务实现。

### 4. 关键决策

- 没有把多个派生 small 打包成一个“杂项收尾” medium，而是按单一问题边界拆成独立任务；原因是 medium 必须有清晰目标和验收，不应该靠“都没做完”来凑会话粒度。
- `TASK-024` 被放到后续优先级最前，是因为当前离线 eval 还没有覆盖最危险的 `resume_workflow + writeback_result` 副作用链路；这比继续堆一个新的 UI 或新 workflow 更影响系统可信度。
- `TASK-026` 和 `TASK-027` 被拆成两个任务，而不是一个“大而全的新笔记治理任务”；前者解决 scoped ingest 的底座，后者才解决 proposal 化，避免把输入边界和治理输出边界混成同一会话。
- ask 的语义级 groundedness 评估被单独拆成 `TASK-028`，而不是顺手塞进 `TASK-024`；两者虽然都属于 eval，但一个针对副作用恢复链路，一个针对问答可信度，失败模式和验收标准不同。

### 5. 修改过的文件

- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 6. 验证与测试

- 跑了什么命令
  - `sed -n '1,260p' docs/TASK_QUEUE.md`
  - `sed -n '1,260p' docs/SESSION_LOG.md`
  - `sed -n '1,260p' docs/PROJECT_MASTER_PLAN.md`
  - `sed -n '1,220p' README.md`
  - `rg -n 'TASK-023|Next Action|waiting_for_approval|writeback_result|resume|proposal' docs/PROJECT_MASTER_PLAN.md docs/TASK_QUEUE.md docs/SESSION_LOG.md backend/app plugin/src eval`
  - `date '+%Y-%m-%d %H:%M:%S %Z'`
- 结果如何
  - 已确认 `TASK-023` 是唯一可绑定的 medium，且在 2026-03-16 应分配的 `session_id` 为 `SES-20260316-01`。
  - 已确认主文档多处 `Next Action` 仍指向 `TASK-023`，如果不同步会与本次任务状态变化发生文档不一致。
  - 已确认当前代码事实足以支撑新增 `TASK-024` 到 `TASK-028`，同时不支持把两个派生 small 混打为单个 medium。
- 哪些没法验证
  - 本次没有代码改动，因此没有新的运行时链路可做自动化或手工功能验证。
  - 新增任务本身只完成登记，尚未实现，不能把未来验收条件写成“已验证通过”。
- 哪些只是静态修改
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 唯一扩展是为了判断任务粒度，额外补读了插件审批面板、写回执行器、`resume_workflow`、`INGEST_STEWARD` 和 eval 入口代码；这直接服务于 `TASK-023` 的任务拆解，不构成新的功能推进。
- 本次没有顺手实现任何后续 medium，只做了队列治理和项目文档同步。

### 8. 未解决问题

- `writeback / resume` 高风险链路仍未进入统一离线 eval，当前只能靠 unittest 和演示路径支撑。
- 插件仍然没有待审批 proposal 收件箱，真实审批入口依然依赖“现触发一条新的 `DAILY_DIGEST` proposal”。
- `INGEST_STEWARD` 仍拒绝 `note_path / note_paths`，新笔记治理还没有进入真实 waiting proposal 主线。
- ask 仍只能证明“编号级引用没漂”，不能证明答案语义真的被证据支撑。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果下一会话不先把 `TASK-024` 这种高风险副作用链路拉进离线回归，而是继续堆新功能，系统会越来越像“能演示，但不能稳定证明”的项目。
- 技术债：当前 proposal 真实产出仍只有 `DAILY_DIGEST` 一条业务路径，治理主叙事还不够均衡。
- 技术债：插件审批面板虽然可用，但没有待审批收件箱，用户交互入口仍带明显 demo 感。
- 假设：下一批主线 medium 会话将优先从 `TASK-024`、`TASK-025`、`TASK-026`、`TASK-027`、`TASK-028` 中按优先级顺序推进，而不是重新发散到未登记的大任务。

### 10. 下一步最优先任务

1. 绑定 `TASK-024`，把 `resume_workflow` / `writeback_result` 高风险链路补进最小离线 eval。
2. 再进入 `TASK-025`，为 waiting proposal 建立最小后端查询接口和插件审批收件箱。
3. 随后推进 `TASK-026` 与 `TASK-027`，先打开 scoped ingest，再让 `INGEST_STEWARD` 产出首条真实治理 proposal。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
- [backend/tests/test_eval_runner.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_eval_runner.py)
- [backend/tests/test_resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_resume_workflow.py)
- [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts)
- [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)
- [backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py)
- [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)

### 12. 当前最容易被面试官追问的点

- 你为什么在已经有最小 eval 之后，不是继续堆新功能，而是先把 `writeback / resume` 拉进离线回归？如果回答成“这个更重要”会非常空；你必须说清楚副作用链路没有统一回归时，演示成功率、审计可信度和恢复边界会一起失真。
- 你为什么不把两个派生 small 打包成一个 medium 收尾任务？如果回答成“反正都没做完，就一起做了”，会显得你没有任务边界意识；你要明确 medium 的定义是单一中等问题，不是零碎未完成项的垃圾桶。
- 为什么 proposal 主线下一步先选 `INGEST_STEWARD`，而不是继续给 `DAILY_DIGEST` 加花活或者把 ask 也 proposal 化？如果回答不出“项目主叙事是知识治理，不是复盘模板或问答展示”，会很像做了很多功能，但没有真正想清楚项目定位。

## [SES-20260315-04] 构建最小 golden set 与离线 `eval/run_eval.py`

- 日期：2026-03-15
- 类型：`Eval`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-021`
- 本会话唯一目标：基于现有 `sample_vault/` 与稳定 fixture，落地最小 golden set 和离线 `eval/run_eval.py`，让 ask / digest / proposal 相关能力从“可演示”走向“可回归”

### 1. 本次目标

- 在不扩成完整 benchmark 平台、外部评测服务或复杂 dashboard 的前提下，补一个最小离线评估执行器。
- 让 ask 与至少一个 digest / proposal 场景具备可重复执行、可落结果文件的 golden 回归入口。
- 把现有测试里已经稳定的结构化 contract 抽成 golden 样本，而不是继续停留在“只有 unittest、没有回归数据集”的状态。

### 2. 本次完成内容

- 确认 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中 `TASK-021` 是当前最合适绑定的 `planned / scope=medium` 任务，且没有预分配 `session_id`；`SES-20260315-01` 到 `SES-20260315-03` 已占用，因此本次会话分配 `SES-20260315-04`。
- 新增 [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)，落地最小离线评估执行器，支持：
  - 读取 `eval/golden/*.json` 的 case 定义
  - 基于 `--case-id` 过滤执行
  - 对 `sample_vault` 与 deterministic fixture 自动建索引 / 运行 workflow
  - 对 ask 场景 mock provider 返回，避免 golden 回归受外部联网可用性影响
  - 将结果稳定写入 `eval/results/eval-YYYYMMDD-HHMMSS.json`
- 新增 [eval/golden/ask_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/ask_cases.json)，覆盖：
  - `sample_vault` 下的 retrieval-only ask 回归
  - metadata filter 过严时的 retrieval fallback
  - 合法 citation 的 generated answer
  - 越界 citation 的保守降级
  - `no_hits` 安全返回
- 新增 [eval/golden/digest_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/digest_cases.json)，覆盖：
  - `sample_vault` 下的结构化 digest
  - `proposal + waiting_for_approval` 返回
  - 空索引 fallback
- 新增 [backend/tests/test_eval_runner.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_eval_runner.py)，验证：
  - 过滤执行的 fixture case 可稳定通过
  - 真实 `sample_vault` case 可落盘结果文件并返回通过状态
- 生成一次真实结果文件 [eval/results/eval-20260315-072444.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/results/eval-20260315-072444.json)，作为本次验收样本输出。
- 在收尾中确认：`TASK-021` 已满足“存在可运行 golden 样本、存在 `eval/run_eval.py`、执行会产出带时间戳结果文件、覆盖 ask 与 digest / proposal 场景”四条验收标准。

### 3. 本次未完成内容

- 没有把 golden set 扩到 README 中原先设想的“30 条左右”；本次先落 8 条代表性样本，优先守住可运行和稳定性。
- 没有把 eval 扩展到 `resume_workflow`、插件本地写回、副作用一致性和宿主级 Obsidian 手工链路。
- 没有引入 LLM-as-a-judge、语义级 groundedness 判分、P50 / P95 统计或可视化 dashboard。
- 没有解决 `sample_vault` 长期演进导致 golden case 漂移的问题；当前只做了最小稳定集。

### 4. 关键决策

- 没有新起一套“eval 专用协议”，而是直接复用 [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py) 的 `/workflows/invoke` contract，因为本次要证明的是现有业务入口是否可回归，而不是再造第二套调用面。
- golden set 采用“真实 `sample_vault` + deterministic fixture”混合策略：前者保证评估不脱离真实语料，后者负责稳定覆盖 citation 越界、空索引等高风险 bad case，避免纯真实语料回归过脆。
- 断言重点放在结构化字段、fallback 信号和关键子串，而不是整段自然语言全文相等；这是为了避免模板文案轻微改动就把整套 eval 跑成误报。
- ask generated answer 的 case 统一 mock provider 返回，而不是依赖真实联网模型，是为了把回归噪声压到最低，优先验证协议与降级边界。

### 5. 修改过的文件

- [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
- [eval/golden/ask_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/ask_cases.json)
- [eval/golden/digest_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/digest_cases.json)
- [eval/results/eval-20260315-072444.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/results/eval-20260315-072444.json)
- [backend/tests/test_eval_runner.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_eval_runner.py)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 6. 验证与测试

- 跑了什么命令
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_eval_runner -v`
  - `./.conda/knowledge-steward/bin/python eval/run_eval.py`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
- 结果如何
  - `test_eval_runner` 2 个测试全部通过，覆盖过滤执行与真实 `sample_vault` case 落盘。
  - 全量 eval 8 条 case 全部通过，并生成 `eval/results/eval-20260315-072444.json`。
  - 后端全量 48 个测试全部通过，没有回归 ask / digest / ingest / resume / retrieval 既有行为。
- 哪些没法验证
  - 没有验证真实联网 provider 的长尾输出格式在 golden 体系里的表现；相关 case 仍依赖 mock provider。
  - 没有验证真实 Obsidian 宿主里的 proposal / local writeback / resume 端到端链路进入 eval。
- 哪些只是静态修改
  - [eval/golden/ask_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/ask_cases.json)
  - [eval/golden/digest_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/digest_cases.json)
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 唯一伴随改动是补 [backend/tests/test_eval_runner.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_eval_runner.py)、生成一次 `eval/results/*.json` 验证文件，并在收尾中补一个新的队列治理任务以避免 `TASK-021` 完成后任务队列断档。
- 上述伴随改动都直接服务于 `TASK-021` 的验收和项目队列连续性，不构成新的功能实现会话。

### 8. 未解决问题

- 当前 eval 仍只覆盖 ask / digest，尚未覆盖 `resume_workflow`、local writeback、副作用一致性和跨会话恢复。
- `sample_vault` 一旦发生较大内容漂移，部分 golden case 可能出现“真实能力没退化，但样本预期变了”的假红。
- 当前结果文件主要记录 pass/fail、关键字段和错误堆栈，还没有 latency / cost / richer metrics。
- 仍没有 demo 脚本和宿主级稳定演示路径，离“评估 + 演示”双闭环还差一步。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果后续继续往功能侧推进，却不把 golden set 持续扩到写回 / 恢复等高风险链路，eval 会重新退化成“只验证低风险 happy path”的装饰层。
- 技术债：当前真实语料回归和 deterministic fixture 回归混在同一套执行器里，后续需要更明确地区分“稳定合约回归”和“真实样本回归”。
- 技术债：结果文件当前主要面向人工查看，尚未沉淀成稳定的指标聚合格式。
- 假设：下一次会话不应直接盲目进入某个新功能，而应先绑定新的队列治理任务，为 `TASK-021` 之后的主线重新拆解并登记下一批 medium 任务。

### 10. 下一步最优先任务

1. 绑定 `TASK-023`，继续拆解 `TASK-021` 之后的下一批 medium 队列任务，避免后续会话无任务可绑。
2. 在新的主线任务里优先决定：是先补高风险副作用链路的回归覆盖，还是先推进待审批列表 / 增量 ingest / 跨会话恢复中的一个。
3. 以 `TASK-021` 的派生小任务形式，继续把最常见 bad case 固化为回归黑名单，而不是让 golden set 长期停在 8 条样本。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
- [eval/golden/ask_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/ask_cases.json)
- [eval/golden/digest_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/digest_cases.json)
- [backend/tests/test_eval_runner.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_eval_runner.py)
- [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)
- [backend/app/services/digest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/digest.py)

### 12. 当前最容易被面试官追问的点

- 你为什么不直接用 LLM-as-a-judge，而是先做结构化字段断言？如果回答成“先这样简单做一下”，会显得你没想过评估噪声和可复现性；正确回答必须落到离线回归的稳定性优先。
- 为什么 golden set 要混合 `sample_vault` 和 deterministic fixture？如果回答只说“方便写测试”，会显得你没有正视真实语料漂移和 bad case 稳定复现之间的 trade-off。
- 你这个 eval 真在证明系统有效，还是只是把 unittest 换了个目录？如果回答不出“它复用了真实 workflow contract、生成独立结果文件、对真实样本和代表性 bad case 做回归”，会很像没做过工程评估闭环。

## [SES-20260315-03] 为 ask 路径补程序级 citation 对齐校验

- 日期：2026-03-15
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-020`
- 本会话唯一目标：为当前 ask 路径的 `generated_answer` 增加程序级 citation 对齐校验，在引用缺失、越界或编号漂移时稳定降级到 `retrieval_only`，且不改变现有 ask contract

### 1. 本次目标

- 在不扩展到语义级 groundedness 评分、插件 ask UI、rerank 或 eval 执行器的前提下，为 `generated_answer` 增加最小程序级 citation 兜底。
- 让 ask 链路不再只依赖 prompt 要求引用，而是在服务端落地答案编号解析与合法性校验。
- 保持 `/workflows/invoke`、`AskWorkflowResult` 与 ask graph 外层 contract 稳定，只通过既有 fallback 字段表达降级原因。

### 2. 本次完成内容

- 确认 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中 `TASK-020` 是当前最合适绑定的 `planned / scope=medium` 任务，且没有预分配 `session_id`；`SES-20260315-01` 与 `SES-20260315-02` 已占用，因此本次会话分配 `SES-20260315-03`。
- 更新 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)，新增：
  - `generated_answer` 的引用编号解析
  - 缺少引用编号时的保守降级
  - 引用编号越界或与当前候选集合不对齐时的保守降级
  - 新的 `model_fallback_reason`：`citation_alignment_missing_reference`、`citation_alignment_out_of_range`
- 保持 [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py) 外层 contract 不变，继续通过 `AskWorkflowResult` 的既有 fallback 字段向上游表达降级，而不是另起新字段或新接口。
- 更新 [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)，新增：
  - provider 返回合法 `[1]` 引用时仍保留 `generated_answer`
  - provider 返回无引用答案时降级为 `retrieval_only`
  - provider 返回越界编号时降级为 `retrieval_only`
  - `/workflows/invoke` 层最终 message 仍保持 retrieval-only fallback 语义
- 在收尾中确认：`TASK-020` 已满足“检测缺引用 / 越界编号 / 编号与当前候选集合不对齐的 bad case、校验失败稳定退回 `retrieval_only`、不改变 ask 主体 contract、补成功/失败分支测试”四条验收标准。

### 3. 本次未完成内容

- 没有实现语义级 groundedness 判分；当前只校验编号对齐，不判断答案陈述是否真的被证据充分支撑。
- 没有实现插件 ask 结果中的引用编号映射展示。
- 没有引入 golden set、人工抽样脚本或离线 answer-citation consistency 评测。
- 没有验证真实联网 provider 返回的长尾输出格式；当前回归主要依赖 mock 测试。

### 4. 关键决策

- 没有把 citation 校验做成新接口或 graph 新节点，而是直接落在 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py) 的生成答案落地前，因为本次要解决的是 ask 服务返回前的最小可信度兜底，而不是扩展 workflow 编排边界。
- 对任何“不确定是否合法”的生成答案默认保守降级为 `retrieval_only`，是为了优先守住问答可信度边界；首版不追求“尽可能保留生成答案”。
- 没有顺手做语义级 groundedness 校验，是因为这会把本次 `medium` 任务扩成新的评估/判分子系统；当前只承诺编号级 answer-citation alignment。

### 5. 修改过的文件

- [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)
- [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 6. 验证与测试

- 跑了什么命令
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_workflow -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
- 结果如何
  - ask 定向 15 个测试全部通过，新增 bad case 分支已被覆盖。
  - 后端全量 46 个测试全部通过，没有回归既有 ingest / digest / resume / retrieval 行为。
- 哪些没法验证
  - 没有验证真实联网 provider 在长答案、多段输出或非常规引用格式下的行为。
  - 没有验证插件 ask UI，因为本次明确不涉及插件侧。
- 哪些只是静态修改
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 唯一伴随改动是新增少量 `model_fallback_reason` 字符串语义和测试断言，它们都直接服务于 `TASK-020` 的验收目标，不构成新的 `medium` 功能。
- 本次没有顺手推进 `TASK-021` 的 golden set / eval，也没有扩展插件 ask 交互。

### 8. 未解决问题

- 当前只能检测编号层面的 citation 漂移，仍不能识别“引用编号合法，但答案语义已经超出证据”的 bad case。
- provider 如果输出非常规引用格式，当前正则规则可能会直接触发保守降级。
- 插件侧还没有把引用编号和原始 chunk 的对应关系展示出来，人工校对成本仍偏高。

### 9. 新增风险 / 技术债 / 假设

- 风险：ask 可信度已经比“纯 prompt 约束”更稳，但仍不等于真正 grounded；如果后续把“编号合法”包装成“答案已被充分证明”，面试时会被直接追问语义级对齐缺口。
- 技术债：citation 校验目前是轻量正则解析，对 provider 的输出格式仍有假设；如果后续引入更多 provider 或富文本响应，规则需要继续收敛。
- 假设：下一次主线 medium 会话应优先进入 `TASK-021`，补最小 golden set 与 `eval/run_eval.py`，把 ask / digest / proposal 从“可演示”继续推进到“可回归”。

### 10. 下一步最优先任务

1. 绑定 `TASK-021`，构建最小 golden set 与 `eval/run_eval.py`。
2. 保留 `TASK-020` 现有的轻量派生项，后续在插件 ask 结果中渲染引用编号与原始 chunk 的对应关系。
3. 在后续评估或检索主线中，再决定是否要补语义级 groundedness 判分，而不是在本次会话里顺手扩 scope。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)
- [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)
- [eval/](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/)

### 12. 当前最容易被面试官追问的点

- 你为什么这次只做了编号级 citation alignment，而没有做语义级 groundedness 判分？如果回答成“这样已经够了”，会显得你没有正视问答可信度边界；正确回答必须直说这是一次 scope control，先补最容易失真的编号层 bad case。
- provider 返回了 `[1]` 就一定可信吗？如果你回答“有编号就可信”，会直接暴露你没区分“编号合法”和“语义被证据支持”。
- 为什么 citation 校验失败时直接退回 `retrieval_only`，而不是继续把生成答案放出去并附个低置信提示？如果回答不出“错误答案比保守答案更伤可信度”，会显得你没做过真实演示和风控权衡。

## [SES-20260315-02] 实现插件侧受限写回执行器与 `before_hash` 校验

- 日期：2026-03-15
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-019`
- 本会话唯一目标：把 `DAILY_DIGEST -> proposal -> approval panel` 的控制面接到真实插件侧写回边界，至少支持 `frontmatter merge` 与指定 heading 下插入，并在执行前校验 `before_hash`

### 1. 本次目标

- 在不扩成待审批列表、partial patch approval、自动回滚或写回后增量 ingest 的前提下，实现插件本地受限写回执行器。
- 让审批面板从“只记录 approve / reject”升级为“本地执行受限 patch 后，再把真实 `writeback_result` 回传 `/workflows/resume`”。
- 为成功 / 失败写回结果补最小测试与构建验证，避免 Phase 4 继续停留在只有 control-plane、没有 side-effect plane 的状态。

### 2. 本次完成内容

- 确认 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中 `TASK-019` 是当前最合适绑定的 `P0 medium` 任务，且没有预分配 `session_id`；`SES-20260315-01` 已占用，当天未占用的下一个会话号为 `SES-20260315-02`。
- 更新 [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)，为 `WorkflowResumeRequest` 增加可选 `writeback_result`，保持 `/workflows/resume` 为唯一恢复入口，不新增独立写回 API。
- 更新 [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py)，新增：
  - 对 `writeback_result` 的合法性校验
  - approval + writeback 的幂等冲突判断
  - 将真实 `writeback_result` 一并写入 `audit_log` 与 completed checkpoint
  - 成功写回 / 失败写回两类恢复消息
- 新增 [plugin/src/writeback/helpers.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/helpers.ts) 与 [plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts)，落地首版插件侧受限写回执行器：
  - 兼容 `merge_frontmatter` 与历史别名 `frontmatter_merge`
  - 支持 `insert_under_heading`
  - 对绝对 / 相对 `target_note_path` 做最小兼容
  - 写回前校验 `before_hash`
  - 检测“当前文件已处于 proposal 目标状态”时避免重复落盘
- 更新 [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)，把审批提交流程改成：
  - approve 时先在插件本地执行写回
  - 再把真实 `writeback_result` 回传 `/workflows/resume`
  - 如果本地写回已成功但后端记账失败，则冻结 reject 路径，只允许 retry approve 同步控制面
- 更新 [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)，补齐插件侧 `WorkflowResumeRequest.writeback_result`。
- 更新 [backend/tests/test_resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_resume_workflow.py)，新增：
  - 成功写回结果入 checkpoint / audit 断言
  - 失败写回结果入 checkpoint / audit 断言
  - reject 时携带 `writeback_result` 的非法 payload 拒绝断言
- 新增 [plugin/src/writeback/writeback.test.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/writeback.test.ts)，覆盖：
  - patch op 名称兼容
  - heading 下插入成功 / 拒绝
  - frontmatter merge 数组合并与未知字段保留
  - `sha256:` hash 输出格式
- 更新 [plugin/package.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/package.json) 与 [plugin/tsconfig.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/tsconfig.json)，补 `npm test` 入口与 TS 扩展导入兼容，使写回纯函数测试能稳定执行。
- 在收尾中确认：`TASK-019` 已满足“两类受限 patch op 执行、`before_hash` 校验、最小成功 / 失败状态回传、允许 / 拒绝分支测试覆盖”四条验收标准。

### 3. 本次未完成内容

- 没有实现写回成功后的最小增量 ingest。
- 没有实现待审批列表、跨会话待同步入口或 stale proposal 收件箱。
- 没有统一清理 `merge_frontmatter` / `frontmatter_merge` 双命名，只在执行器侧做兼容。
- 没有在真实 Obsidian 宿主环境里手工点击 approval 面板完成一次端到端写回验证。

### 4. 关键决策

- 没有新增独立 `/workflows/writeback` 接口，而是复用现有 `/workflows/resume` 并扩展 `writeback_result`，因为本次要解决的是“审批恢复控制面如何拿到真实副作用结果”，不是再引入第二套恢复协议。
- 写回必须先在插件本地执行，再把结果回传后端；否则后端会重新踩到“谁实际改了 Vault、谁掌握 Obsidian API、谁对审计负责”的边界混乱。
- `before_hash` 冲突默认保守失败，不尝试自动重试或自动 merge，因为 Phase 4 首个真实副作用闭环更需要守住安全边界，而不是追求“尽量写进去”。
- 对“本地写回成功但 `/workflows/resume` 失败”的场景，先用面板内存态 `pendingWritebackResult` 守住不重复落盘，再把跨会话恢复留作派生小任务；因为继续扩展成 query/inbox 会超出本次 `medium` 范围。

### 5. 修改过的文件

- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py)
- [backend/tests/test_resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_resume_workflow.py)
- [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)
- [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)
- [plugin/src/writeback/helpers.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/helpers.ts)
- [plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts)
- [plugin/src/writeback/writeback.test.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/writeback.test.ts)
- [plugin/package.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/package.json)
- [plugin/tsconfig.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/tsconfig.json)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 6. 验证与测试

- 跑了什么命令
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_resume_workflow -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
  - `cd plugin && npm test`
  - `cd plugin && npx tsc --noEmit`
  - `cd plugin && npm run build`
- 结果如何
  - `resume_workflow` 定向 8 个测试通过，覆盖成功写回、失败写回、reject 非法 payload、幂等恢复等分支。
  - 后端全量 43 个测试通过，说明新增 `writeback_result` 协议没有破坏 ask / ingest / digest / retrieval 既有行为。
  - 插件写回纯函数 5 个测试通过，说明 patch op 兼容、heading 插入、frontmatter merge 与 hash helper 至少通过逻辑级验证。
  - `tsc --noEmit` 与 `npm run build` 通过，说明新增插件写回模块和审批视图改造没有留下静态类型或打包错误。
- 哪些没法验证
  - 没有在真实 Obsidian 宿主环境里点一次 `Load daily digest approval -> Approve`，验证 `processFrontMatter()`、`vault.modify()` 和面板交互细节。
  - 没有验证写回成功后触发最小增量 ingest，因为这仍是派生小任务。
- 哪些只是静态修改
  - [plugin/package.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/package.json)
  - [plugin/tsconfig.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/tsconfig.json)
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 唯一伴随改动是：
  - 为复用现有恢复控制面，给 `/workflows/resume` 扩了 `writeback_result`
  - 为插件纯函数写回逻辑补了最小 `npm test` 入口和 `tsconfig` 兼容项
  - 为避免重复副作用，在面板内增加 `pendingWritebackResult` 重试保护
- 这三项都直接服务于 `TASK-019` 的验收标准，不构成新的 `medium` 功能。

### 8. 未解决问题

- 当前“本地写回成功但 `/workflows/resume` 失败”只能依赖当前面板内存态重试，跨会话没有恢复入口。
- `merge_frontmatter` / `frontmatter_merge` 双命名仍未统一，当前只是执行器兼容。
- `target_note_path` 仍兼容绝对 / 相对两种语义，没有统一成最终协议事实。
- 写回后还没有最小增量 ingest，索引可能短时间内落后于 Vault 真实内容。

### 9. 新增风险 / 技术债 / 假设

- 风险：本地写回成功但后端审计同步失败时，真实副作用事实已经发生；如果后续没有跨会话待同步入口，只靠当前 panel 内存态保护，演示和面试时会被追问一致性恢复边界。
- 技术债：`frontmatter_merge` 历史别名仍存活，当前通过执行器兼容掩住了协议分叉，但没有彻底收敛。
- 技术债：绝对 / 相对 `target_note_path` 当前用最小兼容处理；跨平台、软链接或非文件系统 adapter 下仍可能暴露路径语义问题。
- 假设：下一次主线 medium 会话应优先进入 `TASK-020`，补 ask 路径的程序级 citation 对齐校验；而 `TASK-019` 的增量 ingest 与跨会话恢复只作为后续伴随小任务处理。

### 10. 下一步最优先任务

1. 绑定 `TASK-020`，为 generated answer 增加程序级 citation 对齐校验，把 ask 的可信度缺口补上。
2. 以 `TASK-020` 或后续主线会话的伴随小任务形式，补 `TASK-019` 派生项：写回成功后的最小增量 ingest。
3. 以 `TASK-020` 或后续主线会话的伴随小任务形式，补“本地写回已成功但 `/workflows/resume` 失败”的跨会话恢复 / 待同步入口。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)
- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)
- [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py)
- [plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts)
- [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)

### 12. 当前最容易被面试官追问的点

- 你为什么坚持“插件先写回、本地成功后再调用 `/workflows/resume`”，而不是让后端先记账再异步执行？如果回答只是“插件更方便”，会显得你没处理过副作用边界；必须答到 Obsidian API 边界、谁实际改了 Vault、谁掌握用户交互和谁负责审计。
- 如果本地写回成功了，但 `/workflows/resume` 因网络超时失败，你怎么避免下一次重复写回？如果回答只是“用户不要重复点”，会直接显得没做过线上恢复；正确回答应该落到 `before_hash`、已应用检测、`pendingWritebackResult` 重试保护，以及当前仍缺跨会话恢复入口这层真实边界。
- 你为什么不新开一个 `/workflows/writeback` 接口，而是把 `writeback_result` 塞回 `/workflows/resume`？如果回答不出“审批恢复控制面”和“副作用结果回填”本来就是同一条业务事务，就会显得你只是在堆接口。
- 现在你能不能说“完整 HITL 闭环已完成”？如果回答直接说“完成了”，会暴露你把“最小真实写回闭环”夸成“产品化闭环”；正确回答必须明确：当前只打通了 `DAILY_DIGEST -> proposal -> local writeback -> audit/checkpoint` 的最小路径，待审批列表、写回后增量 ingest、跨会话恢复和多 workflow proposal 化仍未完成。

## [SES-20260315-01] 打通 `DAILY_DIGEST` proposal 产出与插件审批面板真实上下文

- 日期：2026-03-15
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-022`
- 本会话唯一目标：让至少一条真实业务 workflow 能产出 `proposal + waiting_for_approval checkpoint`，并把 `thread_id / proposal_id / proposal` 真实注入插件审批面板，去掉当前只能靠本地 demo proposal 验证审批 UI 的断层

### 1. 本次目标

- 选择一条最小可控的业务 workflow，真实产出结构化 proposal，并把 thread 级 checkpoint 推进到 `waiting_for_approval`。
- 让插件审批面板消费后端真实返回的 proposal 上下文，而不是继续只靠本地 demo 命令灌数据。
- 在不扩成真实写回执行器、待审批列表或多 workflow proposal 化的前提下，补齐 `TASK-022` 的最小闭环。

### 2. 本次完成内容

- 确认 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中 `TASK-022` 是当前最合适绑定的 `P0 medium` 任务，且没有预分配 `session_id`；`SES-20260315-01` 当天未被占用，因此本次会话分配该 ID。
- 更新 [backend/app/services/digest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/digest.py)，新增 `build_digest_approval_proposal()`，让 `DAILY_DIGEST` 可以基于真实 `source_notes` 构造首版受限 proposal：
  - 目标 note 优先选择 daily note
  - patch op 仅允许 `merge_frontmatter` + `insert_under_heading`
  - 自动附带 source note 证据、`before_hash` 与最小 safety checks
- 更新 [backend/app/graphs/digest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/digest_graph.py)，让 `DAILY_DIGEST` 在显式 `metadata.approval_mode="proposal"` 时进入真实 approval proposal 路径：
  - 执行 `prepare_digest -> build_digest`
  - 追加 `build_digest_proposal` 与 `human_approval` waiting trace event
  - 在同一事务里落 proposal 与 `waiting_for_approval` checkpoint
  - 对 waiting thread 显式拒绝 `resume_from_checkpoint`，要求改走 `/workflows/resume`
- 更新 [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)，把 proposal 持久化拆成 `save_proposal()` + `save_proposal_record()`，以便 graph 在已有事务中和 checkpoint 原子提交。
- 更新 [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)，让 `/workflows/invoke` 的 `DAILY_DIGEST` 能返回：
  - `status=waiting_for_approval`
  - `approval_required=true`
  - 真实 `proposal`
  - 同时保留原 completed / fallback digest 语义不回退
- 更新 [plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts)，新增 `Load daily digest approval` 命令，直接触发真实 `DAILY_DIGEST` proposal 请求，并把返回的 `thread_id / proposal` 注入审批面板。
- 更新 [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)，补 `approvalStatusMessage` 空态 / 降级提示；无 pending proposal 时不再继续误导用户“只能用 demo”。
- 更新 [backend/tests/test_digest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_digest_workflow.py)，新增：
  - 真实 waiting proposal 产出断言
  - waiting checkpoint 持久化断言
  - empty approval proposal fallback 断言
  - waiting thread 拒绝 `resume_from_checkpoint` 断言
- 在收尾中确认：`TASK-022` 已满足“至少一条 workflow 真实产出 proposal + waiting checkpoint、插件审批面板消费真实上下文、无 proposal 时有降级提示、存在最小测试验证”这四条验收标准。

### 3. 本次未完成内容

- 没有实现待审批列表、通知中心或“最近一次待审批项”查询入口。
- 没有把 ask / ingest workflow 一并 proposal 化；当前真实 waiting proposal 只覆盖 `DAILY_DIGEST`。
- 没有实现真实写回执行器、`before_hash` 真校验、审批后副作用续跑或增量 ingest 回补。
- 没有在真实 Obsidian 宿主环境里手工点击 `Load daily digest approval` 做 UI 级端到端验证。

### 4. 关键决策

- 选择 `DAILY_DIGEST` 作为首条真实 waiting proposal 路径，而不是 ask / ingest，是因为 `resume_workflow` 现有 fixture、digest 结构化返回和审批叙事都更贴近 proposal 场景，能在不扩边界的前提下最小闭环。
- 没有直接把 `require_approval=true` 的所有 digest 调用都切成 waiting，而是加了显式 `metadata.approval_mode="proposal"` 开关，因为 `WorkflowInvokeRequest.require_approval` 默认值本来就是 `true`；如果直接切，会把现有 completed digest 行为全部改语义。
- proposal 与 waiting checkpoint 必须在同一个 SQLite 事务内提交，而不是先写 proposal 再补 checkpoint；否则插件可能拿到 proposal_id，但 thread 状态还没进入 waiting，恢复链路会出现事实分叉。
- 保留 `Open approval demo`，但把它降级为离线 fallback，而不是继续把它包装成主入口；因为当前缺的是 inbox/list，不是 UI 渲染能力。

### 5. 修改过的文件

- [backend/app/services/digest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/digest.py)
- [backend/app/graphs/digest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/digest_graph.py)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- [backend/tests/test_digest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_digest_workflow.py)
- [plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts)
- [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 6. 验证与测试

- 跑了什么命令
  - `cd backend && PYTHONPYCACHEPREFIX=/tmp/ks-pycache ../.conda/knowledge-steward/bin/python -m compileall app tests`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_digest_workflow tests.test_resume_workflow tests.test_indexing_store -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
  - `cd plugin && npm run build`
- 结果如何
  - `compileall` 通过，没有语法错误。
  - digest / resume / store 相关 18 个测试通过，新增 waiting proposal 分支稳定。
  - 后端全量 40 个测试通过，说明新增 digest approval proposal 路径没有破坏 ask / ingest / retrieval / resume 既有行为。
  - 插件 `npm run build` 通过，说明新增真实 proposal 加载命令与面板空态处理至少通过构建级验证。
- 哪些没法验证
  - 没有启动真实 HTTP 服务后用 `curl` 手工跑一次 `DAILY_DIGEST -> waiting_for_approval -> /workflows/resume` 跨进程演示。
  - 没有在真实 Obsidian 宿主中点击 `Load daily digest approval` 验证视图刷新和交互细节。
  - 没有验证审批通过后继续推进到真实写回，因为 `TASK-019` 尚未开始。
- 哪些只是静态修改
  - [plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts)
  - [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 唯一伴随改动是：
  - 为了保证 proposal 与 checkpoint 原子提交，把 proposal 写库逻辑拆出 `save_proposal_record()`
  - 引入显式 `approval_mode="proposal"` 元数据开关，守住已有 digest completed 语义
  - 为插件补一条真实 workflow 加载命令与无 proposal 空态提示
- 这三项都直接服务于 `TASK-022` 的验收标准，不构成新的 `medium` 功能。

### 8. 未解决问题

- 当前仍没有待审批 proposal 收件箱或列表接口，真实 proposal 只能通过再次调用 `DAILY_DIGEST` 触发。
- 当前只有 `DAILY_DIGEST` 走通了真实 waiting proposal；ask / ingest 还没有对应 waiting 节点。
- proposal 的 `target_note_path` 当前沿用了现有索引中的绝对路径事实，路径规范还没有统一到写回执行器期望的最终语义。
- `PatchOp.op` 仍同时出现 `merge_frontmatter` 和 `frontmatter_merge` 两种命名，当前尚未统一。

### 9. 新增风险 / 技术债 / 假设

- 风险：当前真实 proposal 注入是命令触发式而不是 inbox/list；如果后续直接把它包装成“审批中心已完成”，面试或演示时会被追问入口治理和 stale item 管理。
- 技术债：`DAILY_DIGEST` approval proposal 路径依赖显式 `metadata.approval_mode="proposal"`，这能守住兼容性，但后续如果 workflow 越来越多，需要抽成更清晰的控制面 contract，而不是继续堆 metadata 特殊键。
- 技术债：proposal target path 当前受现有 note.path 存储语义影响，跨平台、路径别名和未来写回执行器会继续受 absolute/relative path 语义影响。
- 假设：下一次主线会话应优先进入 `TASK-019`，实现受限写回执行器与 `before_hash` 校验；而不是先做 UI 打磨或把更多 workflow 一起 proposal 化。

### 10. 下一步最优先任务

1. 绑定 `TASK-019`，实现插件侧受限写回执行器与 `before_hash` 校验，把 approval control-plane 接到真实副作用边界。
2. 以 `TASK-019` 的伴随改动或派生小任务形式，收敛 `proposal.target_note_path` 的绝对/相对路径语义。
3. 以 `TASK-019` 的伴随改动或派生小任务形式，统一 `merge_frontmatter` / `frontmatter_merge` 的 patch op 命名。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/graphs/digest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/digest_graph.py)
- [backend/app/services/digest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/digest.py)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py)
- [backend/tests/test_digest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_digest_workflow.py)
- [plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts)
- [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)

### 12. 当前最容易被面试官追问的点

- 你为什么要额外引入 `metadata.approval_mode="proposal"`，而不是直接靠 `require_approval=true` 切换到 waiting？如果回答只是“这样方便”，会显得你没意识到 `require_approval` 默认值已经是 `true`，也没看到向后兼容风险。
- 你怎么证明 proposal 和 checkpoint 没有写成两份互相打架的事实源？如果回答不出“同一 SQLite 事务内原子提交”这层，就会显得你没有真的处理过恢复一致性问题。
- 你为什么先把 `DAILY_DIGEST` proposal 化，而不是 ask / ingest？如果回答只是“digest 更容易做”，会显得你在碰运气；正确回答应该落到结构化返回已存在、resume fixture 形态已对齐、且不需要提前触碰真实写回副作用边界。
- 现在插件虽然能加载真实 proposal，但为什么还不能叫“完整 HITL 闭环”？如果回答把“真实上下文注入”直接包装成“写回闭环已完成”，会暴露你混淆了 control-plane 和 side-effect plane。

## [SES-20260314-14] 实现插件审批面板与 diff 预览骨架

- 日期：2026-03-14
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-018`
- 本会话唯一目标：在不扩展到真实 proposal 产出、待审批列表、部分 patch 应用或真实写回执行器的前提下，为插件补齐最小审批面板、diff 预览与 approve / reject 提交骨架，让后端 `resume_workflow` 协议第一次拥有可交互前端入口

### 1. 本次目标

- 在插件侧补一个能展示 proposal 摘要、风险、证据和最小 patch preview 的审批面板，而不是继续停留在 health-only view。
- 让插件能够基于现有 `POST /workflows/resume` 发起 approve / reject，并对后端异常给出最小可读提示。
- 在不新增待审批列表接口和不推进真实写回的前提下，提供一个最小可验证的 proposal 上下文加载方式，证明审批 UI 不是纸面协议。

### 2. 本次完成内容

- 确认 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中 `TASK-018` 是当前最合适绑定的 `medium` 任务，且没有预分配 `session_id`；`SES-20260314-01` 到 `SES-20260314-13` 已被占用，因此本次会话分配 `SES-20260314-14`。
- 更新 [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)，把原本只有 health 展示的侧边栏升级为最小审批面板：
  - 新增 `ApprovalPanelContext`
  - 渲染 proposal 摘要、风险等级、安全检查、证据来源与 patch preview
  - 新增 reviewer / comment 输入
  - 支持 approve / reject 提交和成功 / 失败反馈
  - 在提交成功后冻结当前 proposal 上下文，避免同一份陈旧 proposal 被重复改判
- 更新 [plugin/src/api/client.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/api/client.ts)，新增：
  - `KnowledgeStewardApiError`
  - 后端 `detail` 字段解析
  - 请求超时错误映射
- 更新 [plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts)：
  - 让 view 能注入 API client
  - 新增 `Open approval demo` 命令
  - 用本地 demo proposal 构造最小可验证的审批上下文
- 更新 [plugin/styles.css](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/styles.css)，补最小审批面板样式，包括卡片、风险 badge、callout、表单与 diff 区块。
- 生成 [plugin/package-lock.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/package-lock.json) 并重新构建 [plugin/main.js](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/main.js)，确保插件依赖和打包产物与当前源码一致。
- 在收尾中确认：本次面板之所以采用本地 demo proposal，不是因为后端 resume 协议不够，而是因为当前没有任何业务 graph 真正产出 `proposal + waiting_for_approval` 的真实上下文；这个断层已拆成后续 `TASK-022`。

### 3. 本次未完成内容

- 没有让 ask / ingest / digest graph 真实产出 waiting proposal，也没有把真实 proposal 自动注入插件审批面板。
- 没有实现待审批列表、通知中心或“最近一次待审批项”的查询入口。
- 没有实现部分 patch 应用、真实写回执行器、`before_hash` 校验或写回后增量 ingest。
- 没有在真实 Obsidian 宿主环境里手工演示审批面板和 `/workflows/resume` 的端到端交互。

### 4. 关键决策

- 没有为了让面板“看起来更真”而顺手新增待审批列表接口或 proposal 查询接口，因为这会把本轮范围从插件审批骨架扩大成新的 workflow / control-plane 任务。
- 采用本地 demo proposal 命令而不是把面板做成完全不可验证的纯静态 UI，是为了让 `TASK-018` 至少能验证“渲染 + 表单 + resume 提交 + 错误展示”这条最小交互链路。
- approve 时显式提交完整 `proposal.patch_ops`，reject 时提交空数组，是因为后端当前明确不支持 partial patch approval；前端如果偷偷允许局部勾选，会把任务边界直接扩大成 `TASK-019` 之后的问题。
- 提交成功后冻结当前 proposal 上下文，而不是允许继续二次修改，是为了防止同一份面板中的旧 proposal 被重复提交不同决策，先守住控制面一致性。

### 5. 修改过的文件

- [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)
- [plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts)
- [plugin/src/api/client.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/api/client.ts)
- [plugin/styles.css](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/styles.css)
- [plugin/package-lock.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/package-lock.json)
- [plugin/main.js](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/main.js)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)

### 6. 验证与测试

- 跑了什么命令
  - `cd plugin && npm install`
  - `cd plugin && npm run build`
- 结果如何
  - `npm install` 成功安装插件依赖并生成 `package-lock.json`。
  - `npm run build` 通过，说明新增审批面板、demo 命令、错误映射和样式改动至少通过了插件侧的打包验证。
- 哪些没法验证
  - 没有在真实 Obsidian 宿主里点击命令并手工验证面板交互。
  - 没有拿真实 `waiting_for_approval` proposal 跑 `/workflows/resume`，因为当前系统还没有任何业务 graph 真正产出这类 proposal。
  - 没有做组件级自动化测试；当前只有构建级验证。
- 哪些只是静态修改
  - [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)
  - [plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts)
  - [plugin/src/api/client.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/api/client.ts)
  - [plugin/styles.css](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/styles.css)

### 7. 范围偏移与原因

- 无实质超范围。
- 唯一伴随改动是：
  - 补 `KnowledgeStewardApiError` 与超时 / 后端 `detail` 解析
  - 新增 `Open approval demo` 本地验证命令
  - 生成插件依赖锁文件和构建产物
- 这三项都直接服务于 `TASK-018` 的“审批面板骨架 + 最小验证”目标，不构成新的 `medium` 功能。

### 8. 未解决问题

- 当前插件审批面板仍依赖本地 demo proposal，上下文并非来自真实 workflow。
- 当前没有待审批 proposal 的查询或注入入口，也没有“无待审批项”的真实后端空态协议。
- ask / ingest / digest graph 仍不会产出 `proposal -> waiting_for_approval -> plugin approval panel` 的主线链路。
- `README.md` 里关于 digest、proposal / audit 和审批 UI 状态的描述仍有漂移，本次只按要求同步了 `docs/` 下主文档。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果后续直接开始做 `TASK-019` 的写回执行器，而不先打通真实 proposal 注入链路，就会出现“写回逻辑只能对 demo proposal 运行”的玩具化断层。
- 技术债：当前审批面板还没有 stale proposal freshness 提示、proposal 版本感知或重复提交防抖 UI；现阶段只靠后端幂等与面板冻结兜底。
- 技术债：插件侧虽然能展示 diff 和风险，但没有真实待审批收件箱；如果不补这层，HITL 交互仍会停留在演示命令而不是业务入口。
- 假设：下一次相关会话不应直接进入 `TASK-019`，而应先绑定 `TASK-022`，让至少一条业务 workflow 真实产出 waiting proposal 并注入插件审批面板。

### 10. 下一步最优先任务

1. 绑定 `TASK-022`，打通 workflow proposal 产出与插件审批面板真实上下文，去掉 demo-only 断层。
2. 在 `TASK-022` 之后推进 `TASK-019`，实现受限写回执行器与 `before_hash` 校验。
3. 保留现有轻量派生项，后续在插件调试面板中显示最近一次 `proposal_id / thread_id`，便于恢复链路排障。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)
- [plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts)
- [plugin/src/api/client.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/api/client.ts)
- [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py)
- [backend/app/graphs/checkpoint.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/checkpoint.py)

### 12. 当前最容易被面试官追问的点

- 你这个审批面板为什么要先用本地 demo proposal，而不是直接接真实 workflow？如果回答只有“先把 UI 做出来”，会显得你没有定义输入边界，也没意识到 demo-only 面板和真实控制面的差别。
- 既然后端已经有 `/workflows/resume`，为什么还不能算 HITL 闭环？如果回答把“控制面恢复”包装成“端到端审批链路已通”，面试官会立刻追问 proposal 是谁产出的、waiting checkpoint 是谁写的、插件凭什么知道该审哪一条。
- 你为什么在前端不支持 partial patch selection？如果回答只是“后端没做”，会显得你没想清楚 partial approve 会牵扯 diff 重算、幂等边界和执行一致性。
- 你这轮只有 `npm run build`，没有 Obsidian 宿主手工验证，为什么还敢说任务完成？正确回答应该是这轮任务的验收标准是“审批面板骨架 + 最小交互 + 构建级验证”，但真实 proposal 注入和宿主级回归没有完成，所以必须拆出 `TASK-022`；如果你把它包装成“完整审批 UI 已联通”，会暴露你在夸大实现。

## [SES-20260314-13] 实现 `resume_workflow` 协议与审批中断 contract

- 日期：2026-03-14
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-017`
- 本会话唯一目标：在不扩展到插件审批 UI、真实写回执行器、部分应用 proposal 或完整 proposal 生成链路的前提下，为现有 proposal / checkpoint / audit 骨架补齐后端 `resume_workflow` 协议与审批恢复控制面

### 1. 本次目标

- 在后端补独立的 `resume_workflow` 协议，而不是继续把审批恢复塞进 `resume_from_checkpoint` 的最小短路语义里。
- 让审批决策 payload 与 `thread_id` / `proposal_id` 的绑定关系显式化，并能从 SQLite `workflow_checkpoint` / `proposal` / `audit_log` 读到恢复所需状态。
- 至少覆盖 approve / reject 基础分支，并保证 reject 也被当作业务事实写入审计，而不是当成异常。

### 2. 本次完成内容

- 确认 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中 `TASK-017` 是当前最合适绑定的 `medium` 任务，且没有预分配 `session_id`；`SES-20260314-01` 到 `SES-20260314-12` 已被占用，因此本次会话分配 `SES-20260314-13`。
- 更新 [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)，新增：
  - `WorkflowResumeRequest`
  - `WorkflowResumeResponse`
  - `WorkflowInvokeResponse.proposal`
- 更新 [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)，新增 `POST /workflows/resume`，并对 `not found / conflict / validation` 分别返回 `404 / 409 / 400`。
- 新增 [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py)，落地最小审批恢复控制面：
  - 按 `thread_id` 查询 thread 级 checkpoint
  - 按 `proposal_id` 读取 proposal 主存储
  - 校验 `thread_id / proposal_id` 关联关系
  - 拒绝部分 patch 审批
  - 对相同审批决策做幂等返回，避免重复写 audit
  - 在同一个 SQLite 事务里同时写 append-only `audit_log` 和更新 thread 级 checkpoint
- 更新 [backend/app/graphs/checkpoint.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/checkpoint.py)：
  - 新增 `WorkflowCheckpointStatus.WAITING_FOR_APPROVAL`
  - 新增 `save_graph_checkpoint_record()`
  - 新增 `list_graph_checkpoints_for_thread()`
- 更新 [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)，将 schema 升到 `v6`，让 `workflow_checkpoint.checkpoint_status` 支持 `waiting_for_approval`，并通过迁移重建方式兼容旧库。
- 更新插件协议文件 [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts) 与客户端 [plugin/src/api/client.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/api/client.ts)，同步补齐 proposal / approval / resume contract 和 `resumeWorkflow()` 调用入口，避免插件协议继续落后于后端。
- 新增 [backend/tests/test_resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_resume_workflow.py)，覆盖：
  - approve 分支
  - reject 分支
  - `thread_id / proposal_id` 不匹配
  - partial patch approval 拒绝
  - 相同审批决策的幂等恢复

### 3. 本次未完成内容

- 没有让 ask / ingest / digest graph 自己生成 `WAITING_FOR_APPROVAL` checkpoint；当前测试仍通过 fixture 直接构造 waiting 状态。
- 没有实现插件审批 UI、diff 预览或真实写回执行器。
- 没有实现 `before_hash` 真校验、`writeback_applied` 幂等防重或增量 ingest 回补。
- 没有实现审批后继续推进到真实副作用节点的细粒度 interrupt/resume runner；当前恢复仍停留在“控制面 + 持久化状态推进”。

### 4. 关键决策

- 没把审批恢复继续塞进 `/workflows/invoke` 的 `resume_from_checkpoint`，而是单独增加 `/workflows/resume`，因为二者语义不同：前者是“重用已有 thread 状态”，后者是“消费一条人工决策并推进业务事实”。
- 审批恢复时同时依赖 `thread_id` 和 `proposal_id`，而不是只靠 `thread_id` 命中最新 checkpoint，是为了避免 thread 误复用时把审批决策打到错误 proposal 上。
- reject 也写 append-only `audit_log`，因为拒绝不是异常而是业务事实；如果 reject 不落审计，后续就没法解释为什么某个 proposal 没有继续走写回。
- 对同一审批决策做幂等返回，而不是每次重试都重复插审计，是为了守住后续真实写回阶段的副作用边界；如果控制面阶段都做不到幂等，`TASK-019` 会直接变成事故放大器。
- 本次显式拒绝 partial patch approval，是为了严格守住 `TASK-017` 边界；部分应用 proposal 会直接把范围扩大到 patch 选择、diff 重算和执行幂等，应该留给后续单独任务。

### 5. 修改过的文件

- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py)
- [backend/app/graphs/checkpoint.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/checkpoint.py)
- [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- [backend/tests/test_resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_resume_workflow.py)
- [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)
- [plugin/src/api/client.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/api/client.ts)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)

### 6. 验证与测试

- 跑了什么命令
  - `cd backend && PYTHONPYCACHEPREFIX=/tmp/ks-pycache ../.conda/knowledge-steward/bin/python -m compileall app tests`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_resume_workflow -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_indexing_store -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
- 结果如何
  - `compileall` 通过，没有语法错误。
  - `tests.test_resume_workflow` 新增 5 个用例全部通过，覆盖 approve / reject / partial reject / 线程与 proposal 关联校验 / 幂等恢复。
  - `tests.test_indexing_store` 通过，证明 schema 升到 `v6` 后没有破坏既有存储断言。
  - 推荐 conda 环境下后端全量 37 个测试全部通过。
- 哪些没法验证
  - 没有启动真实 HTTP 服务后再通过 `curl` 演示 `/workflows/resume` 的跨进程调用。
  - 没有验证插件侧真实消费 `resumeWorkflow()` 的 UI 行为，因为 `TASK-018` 尚未开始。
  - 没有验证审批恢复后衔接真实写回副作用，因为 `TASK-019` 仍未开始。
- 哪些只是静态修改
  - [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)
  - [plugin/src/api/client.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/api/client.ts)
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 唯一伴随改动是：
  - 为 `workflow_checkpoint` 增加 `waiting_for_approval` 状态及 `v6` 迁移
  - 为插件 contract / API client 补齐 resume 协议
  - 在收尾阶段同步 `TASK_QUEUE` 与主文档事实
- 这三项都直接服务于 `TASK-017` 的验收标准，不构成新的 `medium` 功能。

### 8. 未解决问题

- 当前没有任何业务 graph 真正产出 `proposal -> waiting_for_approval -> /workflows/resume` 的完整运行链路，resume 控制面目前是“协议和持久化先落地”。
- `thread_id + proposal_id` 已比只用 `thread_id` 更安全，但还没有请求指纹、proposal 版本号或 checkpoint freshness 约束。
- `approval_decision.metadata` 当前只作为预留字段，没有进入恢复逻辑的业务判断。
- `writeback_result` 仍只停留在 contract 层；approve 后不会真正执行 patch，也不会更新 `writeback_applied`。
- `README.md` 对 `digest_graph`、多 graph checkpoint 覆盖和 `audit_log` 状态仍有漂移，本次按规则没有同步。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果后续 graph 产出 proposal 时没有把 checkpoint、proposal 和 audit 的写入顺序固定好，`/workflows/resume` 现在的控制面仍可能命中“checkpoint 有 proposal_id，但 proposal 主表还没写完”的竞态。
- 技术债：当前 `resume_workflow` 实际完成的是“审批决策落审计 + checkpoint 状态推进”，还不是“审批后自动续跑到写回节点”的完整 interrupt 平台。
- 技术债：`waiting_for_approval` 已进入 schema，但 ask / ingest / digest graph 还没有统一的 waiting 节点语义；后续如果每条 graph 自己长一套暂停逻辑，恢复协议很快会漂移。
- 假设：下一次相关会话应优先进入 `TASK-018`，先把插件审批面板和最小 diff 预览补起来，再推进 `TASK-019` 的真实写回。

### 10. 下一步最优先任务

1. 绑定 `TASK-018`，实现插件审批面板与 diff 预览骨架，让 `/workflows/resume` 真正有前端交互入口。
2. 在 `TASK-018` 之后推进 `TASK-019`，补受限写回执行器与 `before_hash` 校验。
3. 保留本次新增的轻量派生项，后续补 resume 请求指纹或 freshness 校验，降低 thread / proposal 误复用风险。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py)
- [backend/app/graphs/checkpoint.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/checkpoint.py)
- [backend/tests/test_resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_resume_workflow.py)
- [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)
- [plugin/src/api/client.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/api/client.ts)

### 12. 当前最容易被面试官追问的点

- 你这个 `/workflows/resume` 到底是在恢复 graph，还是只是在消费一条人工审批回调？如果回答把两者混成一件事，会显得你没区分“控制面恢复”和“节点级续跑”。
- 为什么现在必须同时带 `thread_id` 和 `proposal_id`，而不是只靠最新 checkpoint？如果回答只有“更安全”，会暴露你没想清楚 thread 误复用、旧 checkpoint 命中和审批打错 proposal 的事故面。
- 为什么 reject 也必须写 audit，并把 checkpoint 推进到 completed？如果你把 reject 当异常分支，而不是业务事实，面试官会继续追问你如何解释“为什么没写回、是谁拒绝了、能不能重放”。
- 你现在说自己“实现了审批恢复”，那为什么还不能自动继续执行写回节点？正确回答应该直说这轮只完成了 resume 控制面和持久化一致性，真实副作用续跑留在 `TASK-019` 之后；如果你包装成“完整 HITL 闭环已完成”，会立刻暴露在夸大实现。

## [SES-20260314-12] 设计并落地 `proposal` / `patch_ops` / `audit_log` 的 SQLite schema

- 日期：2026-03-14
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-016`
- 本会话唯一目标：在不扩展到 `resume_workflow`、插件审批 UI、真实写回执行器或自动回滚的前提下，为后续 HITL 审批、写回执行和审计回放落地稳定的 SQLite `proposal` / `patch_ops` / `audit_log` 存储骨架

### 1. 本次目标

- 在 [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py) 中新增 `proposal`、`proposal_evidence`、`patch_op`、`audit_log` 的 schema migration。
- 让 schema 与现有 [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py) 中的 `Proposal`、`PatchOp`、`ApprovalDecision`、`WritebackResult`、`AuditEvent` contract 对齐，而不是再发明一套独立协议。
- 补最小持久化 helper 与测试，证明表结构、索引、约束和最小 roundtrip 可用。

### 2. 本次完成内容

- 确认 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中 `TASK-016` 是当前最合适绑定的 `medium` 任务，且没有预分配 `session_id`，因此为本次会话分配 `SES-20260314-12`。
- 更新 [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)，将 schema 升到 `v5`，新增：
  - `proposal` 表：持久化 `proposal_id`、`thread_id`、`run_id`、`target_note_path`、`risk_level`、`idempotency_key`、`before_hash`、`safety_checks_json`
  - `proposal_evidence` 表：按 `proposal_id + ordinal` 挂证据来源，覆盖 `source_path`、`heading_path`、`chunk_id`、`reason`
  - `patch_op` 表：按 `proposal_id + ordinal` 挂结构化 patch op，覆盖 `op`、`target_path`、`payload_json`
  - `audit_log` 表：append-only 审计记录，覆盖 `approval_status`、`reviewer`、`before_hash`、`after_hash`、`writeback_applied`、`retrieved_chunk_ids_json`、`model_info_json`、`approval_payload_json`、`writeback_result_json`
- 在 [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py) 中新增：
  - `PersistedProposal`
  - `save_proposal()`
  - `load_proposal()`
  - `append_audit_log_event()`
- 关键持久化边界决策已固化到代码里：
  - `proposal` 用主表 upsert + 子表整 proposal 替换，避免 evidence / patch op 残留
  - `audit_log` 保持 append-only，避免恢复或重放时覆盖旧审批事实
  - `idempotency_key` 单独建唯一索引，为后续审批恢复和副作用幂等留出查询抓手
- 更新 [backend/tests/test_indexing_store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_store.py)，新增覆盖：
  - 新表和索引初始化断言
  - proposal roundtrip
  - `idempotency_key` 冲突约束
  - audit log 扁平字段与 JSON 快照写入
- 在本次收尾中同步更新 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 与 [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)，关闭 `TASK-016` 并修正主文档中“proposal schema / audit_log 尚未开始”的状态漂移。

### 3. 本次未完成内容

- 没有实现 `resume_workflow` 控制面或审批恢复协议。
- 没有实现 proposal 生成节点，也没有让任一 graph 真正写入 proposal / audit 记录。
- 没有实现插件审批 UI、diff 预览或真实写回执行器。
- 没有实现 `before_hash` 真校验、`writeback_applied` 幂等检查或自动回滚。
- 没有给 `proposal` / `audit_log` 补查询 CLI、清理策略或排障视图。

### 4. 关键决策

- 没有把 proposal 继续只塞在 checkpoint JSON 里，而是单独建 `proposal` 表，是因为 checkpoint 只是 thread 级恢复快照，不适合承担 proposal 的长期主存储；如果两者都做主，后续 `TASK-017` 会立即陷入 source of truth 冲突。
- 没有把 evidence、patch op、approval、writeback 全部揉进一个大 JSON blob，而是把后续恢复、幂等和审计真正要查的字段结构化落列，把高波动 payload 保留 JSON，是为了守住 `TASK-016` 的 medium 边界，同时不给 `TASK-017` / `TASK-019` 留“看不见、查不动”的烂账。
- `audit_log` 明确做成 append-only，而不是 upsert，是为了保住审计语义；审批拒绝、再次审批、写回失败这些都是独立历史事实，不应该被后一次覆盖掉。
- `idempotency_key` 先落到 `proposal` 表并做唯一索引，而不是等恢复协议再补，是因为恢复去重需要先有稳定的查找锚点；没有这一步，后续“恢复不重复写回”只能停留在文档口号。

### 5. 修改过的文件

- [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- [backend/tests/test_indexing_store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_store.py)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)

### 6. 验证与测试

- 跑了什么命令
  - `cd backend && python -m unittest tests.test_indexing_store -v`
  - `cd backend && PYTHONPYCACHEPREFIX=/tmp/ks-pycache python -m compileall app tests`
  - `cd backend && python -m unittest discover -s tests -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_indexing_store -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
- 结果如何
  - `tests.test_indexing_store` 在当前 shell Python 和推荐 conda Python 下均通过，新增 6 个用例全部通过。
  - `compileall` 通过，没有语法错误。
  - 当前 shell 的 `python -m unittest discover -s tests -v` 失败，原因是该环境缺少 `fastapi`，不是本次 schema 改动引入的代码回归。
  - 使用推荐环境 `../.conda/knowledge-steward/bin/python` 跑后端全量测试时，32 个测试全部通过。
- 哪些没法验证
  - 没有启动真实 HTTP 服务，也没有演示 proposal / audit 被 graph 真实写入，因为本次只落 schema 和最小 helper。
  - 没有验证跨会话 `proposal_id` / `idempotency_key` 在真实审批恢复链路中的行为，因为 `TASK-017` 还未开始。
- 哪些只是静态修改
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 唯一伴随改动是给 schema 补最小持久化 helper 和测试，以及在收尾阶段同步任务队列与主文档事实；这三项都直接服务于 `TASK-016` 的“schema + 约束 + 可验证初始化入口”，不构成新的 medium 功能。
- 本次没有顺手推进 `TASK-017` 的 `resume_workflow` 协议，也没有顺手做 `TASK-019` 的真实写回执行器。

### 8. 未解决问题

- 当前 proposal / audit schema 已落地，但还没有任一 graph 真正把 proposal 生成、审批决策或写回结果写进这些表。
- `approval_status` 当前只从 `approved/rejected` 两态映射，`edited` 只是为后续保留，尚未进入运行链路。
- 还没有 `proposal` / `audit_log` 查询 helper，排障仍主要依赖 SQLite 手工查表。
- README 中关于 `digest`、trace 覆盖范围和 checkpoint 覆盖范围的状态描述仍有漂移，本次收尾没有一并修改。

### 9. 新增风险 / 技术债 / 假设

- 风险：proposal 已有独立表，但如果 `TASK-017` 继续把恢复逻辑只盯 checkpoint 而忽略 proposal / audit 主存储，后续很容易出现恢复命中旧 checkpoint、却看不到新 proposal 事实的分叉。
- 技术债：`patch_plan` 当前仍只存在于 `StewardState`，没有与 `proposal.patch_ops` 的持久化边界完全收敛；后续要避免 state 内外出现两套 patch 语义。
- 技术债：`audit_log` 已落表，但还没有 append-only 查询和清理策略；如果后续大量重放或失败重试，排障成本会迅速上升。
- 假设：下一次相关会话应优先进入 `TASK-017`，把 `resume_workflow` 协议、审批决策 payload 和 proposal / checkpoint / audit 之间的恢复控制面接起来。

### 10. 下一步最优先任务

1. 绑定 `TASK-017`，实现 `resume_workflow` 协议与审批中断 contract。
2. 在 `TASK-017` 之后推进 `TASK-018`，补插件审批面板与 diff 预览骨架。
3. 保留 `TASK-019` 作为后续高风险副作用任务，不要跳过审批恢复协议直接做真实写回。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/app/graphs/state.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/state.py)
- [backend/app/graphs/checkpoint.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/checkpoint.py)
- [backend/tests/test_indexing_store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_store.py)

### 12. 当前最容易被面试官追问的点

- 你为什么不直接把 proposal 挂在 checkpoint 的 `state_json` 里就完事？如果回答只有“单独建表更规范”，会显得你没做过恢复协议，因为真正的问题是 source of truth、审计回放和副作用幂等，而不是表设计洁癖。
- 你为什么把 `proposal_evidence` 和 `patch_op` 拆成子表，而不是整块 JSON？如果说不清哪些字段后续要被查询、校验、去重和 diff 复用，你的 schema 设计看起来就像玩具。
- `audit_log` 为什么必须 append-only？如果你的回答没有涉及“拒绝不是异常、重放不是覆盖、恢复前要查 `writeback_applied`”，面试官会继续追问你到底有没有想清楚审计与恢复的一致性。
- 你现在只做了 schema，没有 graph 真写 proposal，这会不会显得半成品？正确回答应该直说这是 contract-first 的 Phase 4 前置骨架；如果你把它包装成“已经完成 HITL 主链路”，会立刻暴露你在夸大实现状态。

## [SES-20260314-11] 实现 `digest_graph` 骨架与最小 `DAILY_DIGEST` 返回

- 日期：2026-03-14
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-014`
- 本会话唯一目标：在不扩展到定时调度、写回草稿、插件 digest UI 或审批恢复协议的前提下，为 `DAILY_DIGEST` 场景补最小 `digest_graph` 与结构化返回骨架，让 `/workflows/invoke` 不再返回纯占位响应

### 1. 本次目标

- 新增 `backend/app/graphs/digest_graph.py`，把 `DAILY_DIGEST` 接进最小 graph。
- 让 `/workflows/invoke` 的 `DAILY_DIGEST` 返回结构化 `digest_result`，至少包含 digest 主体和来源 note 集合。
- 复用 ask / ingest 已有的 trace、checkpoint 和 `thread_id` 语义，而不是再起一套 digest 专用运行时协议。

### 2. 本次完成内容

- 确认 `TASK-014` 是 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中当前最合适绑定的 `medium` 任务，且 `SES-20260314-01` 到 `SES-20260314-10` 已占用，因此为本次会话分配 `SES-20260314-11`。
- 更新 [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)，新增：
  - `DigestSourceNote`
  - `DigestWorkflowResult`
  - `WorkflowInvokeResponse.digest_result`
- 更新 [backend/app/graphs/state.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/state.py)，新增 `digest_result` 状态字段。
- 更新 [backend/app/graphs/checkpoint.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/checkpoint.py)，把 `digest_result` 纳入 SQLite checkpoint 持久化与恢复白名单，避免 digest 接进 graph 后恢复协议仍只覆盖 ask / ingest。
- 新增 [backend/app/services/digest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/digest.py)，落地首版模板化 digest 构建：
  - 优先从 SQLite `note` 表中选择最近的 `daily_note` / `summary_note`
  - 当索引里暂时没有 digest-like note 时，安全退回最近更新的 generic note
  - 当索引为空时，返回结构化 fallback，而不是抛异常
- 新增 [backend/app/graphs/digest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/digest_graph.py)，落地：
  - `prepare_digest -> build_digest -> finalize_digest` 三节点最小 graph
  - ask / ingest 同款 JSONL + SQLite `run_trace` sink 复用
  - ask / ingest 同款 SQLite checkpoint / `resume_from_checkpoint` 复用
  - 对 `note_path / note_paths` scoped digest 请求的显式拒绝
- 更新 [backend/app/graphs/__init__.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/__init__.py)，导出 digest graph 入口。
- 更新 [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)，让 `/workflows/invoke` 的 `DAILY_DIGEST`：
  - 真实走 `invoke_digest_graph()`
  - 在正常命中、checkpoint 恢复命中和安全 fallback 三种结果下返回不同 message
  - 返回 `COMPLETED + digest_result`
- 更新 [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)，同步补齐 `DigestWorkflowResult`，避免插件 contract 再次落后于后端。
- 新增 [backend/tests/test_digest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_digest_workflow.py)，覆盖：
  - digest graph 正常返回结构化 digest 与 trace
  - 索引为空时的安全 fallback
  - completed checkpoint 恢复命中
  - scoped digest 请求返回 400

### 3. 本次未完成内容

- 没有实现定时调度或 digest 定时触发。
- 没有实现写回草稿、proposal 或审批中断。
- 没有实现插件端 digest UI。
- 没有实现显式时间窗口 / source note 过滤输入；当前仍是“基于已索引 note 的全局 recent digest”。
- 没有实现基于 LLM 的主题聚类、复习计划或更强的 digest 质量评估；当前是模板化、可验证的最小返回。

### 4. 关键决策

- 首版先做“SQLite note 元数据驱动的模板化 digest”，而不是立即把 `DAILY_DIGEST` 绑定到云模型可用性，是为了先把 graph 边界、返回 contract、fallback 和 source note 可解释性钉住，避免 digest 主线一开始就退化成不可验证的自由文本。
- `DAILY_DIGEST` 当前显式拒绝 `note_path / note_paths`，而不是静默忽略，是为了把“当前只支持 indexed-vault 级 digest”做成清晰协议边界，避免后续误以为已经支持 scoped digest。
- digest 直接复用 ask / ingest 已有的 checkpoint 与 trace runner，是为了继续收敛多 graph 的最小运行时语义，而不是让每条 graph 各自长出一套恢复和观测协议。
- 当索引里没有 `daily_note / summary_note` 时退回 generic note，而不是直接失败，是为了让 digest 在样本还不规范、模板识别还不稳定的早期阶段仍有可演示的安全降级路径。

### 5. 修改过的文件

- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/app/graphs/state.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/state.py)
- [backend/app/graphs/checkpoint.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/checkpoint.py)
- [backend/app/graphs/digest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/digest_graph.py)
- [backend/app/graphs/__init__.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/__init__.py)
- [backend/app/services/digest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/digest.py)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/tests/test_digest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_digest_workflow.py)
- [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)

### 6. 验证与测试

- 跑了什么命令
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_digest_workflow -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
  - `cd backend && PYTHONPYCACHEPREFIX=/tmp/ks-pycache ../.conda/knowledge-steward/bin/python -m compileall app tests`
- 结果如何
  - `test_digest_workflow` 新增 4 个用例全部通过，覆盖 digest graph 入口、fallback、checkpoint 恢复命中和 scope 拒绝分支。
  - 后端全量 29 个测试全部通过，没有回归 ask / ingest / retrieval / store 既有行为。
  - `compileall` 通过，没有语法错误。
- 哪些没法验证
  - 没有启动真实 HTTP 服务再用 `curl` 演示 `DAILY_DIGEST` 的跨进程调用；本次验收主要依赖单元测试和代码路径。
  - 没有验证大 Vault 下 digest source selection 的稳定性和摘要质量；当前只验证了最小 contract、fallback 与恢复语义。
  - 没有验证插件端对 `digest_result` 的真实消费，因为插件还没有 digest UI。
- 哪些只是静态修改
  - [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 唯一伴随改动是补 `digest_result` contract、把 digest 纳入共享 checkpoint 持久化，以及同步插件 contract 类型；这三项都直接服务于 `TASK-014` 的“graph + contract + 结构化返回 + 基础 fallback”，不构成新的 medium 功能。
- 本次没有顺手推进 `TASK-016`、`TASK-017`、调度、写回草稿或 digest UI，只把未支持的 scoped digest 请求明确拦截成 400。

### 8. 未解决问题

- `DAILY_DIGEST` 当前没有显式时间窗口、来源过滤或 scoped input，面对大 Vault 时可能过于粗糙。
- digest source selection 仍依赖 `note_type` / `template_family` 启发式；如果模板推断失准，digest 的来源集合会发生漂移。
- digest 当前是模板化摘要，不包含 LLM 聚类、复习计划或更强的内容组织能力。
- digest 也复用了 `KS_ASK_RUNTIME_TRACE_PATH` 对应路径，配置命名继续偏 ask 语义，尚未治理。

### 9. 新增风险 / 技术债 / 假设

- 风险：当前 digest 以最近 note 为主做 source selection，如果索引长期混入大量 generic note 或旧 thread 被误复用，可能出现“摘要结构正确但来源窗口不对”的失真。
- 技术债：`source_notes` 选择仍主要依赖 `daily_note / summary_note` 识别结果，尚未引入显式时间窗口、质量过滤或更稳的复盘候选选择器。
- 技术债：digest 已复用 checkpoint，但恢复语义仍是 thread 级快照与 completed checkpoint 短路，不是 digest 专属的内容新鲜度校验机制。
- 假设：下一次相关会话应优先进入 `TASK-016`，先把 `proposal` / `patch_ops` / `audit_log` 的 SQLite schema 钉住，再继续推进 `TASK-017` 的审批恢复协议。

### 10. 下一步最优先任务

1. 绑定 `TASK-016`，设计并落地 `proposal` / `patch_ops` / `audit_log` 的 SQLite schema。
2. 在 `TASK-016` 之后推进 `TASK-017`，补 `resume_workflow` 协议与审批中断 contract。
3. 保留本次新增的轻量派生项，后续为 `DAILY_DIGEST` 增加显式时间窗口或 source note 过滤输入。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/services/digest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/digest.py)
- [backend/app/graphs/digest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/digest_graph.py)
- [backend/app/graphs/checkpoint.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/checkpoint.py)
- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/tests/test_digest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_digest_workflow.py)

### 12. 当前最容易被面试官追问的点

- 你为什么首版 `DAILY_DIGEST` 先做模板化 digest，而不是直接接模型？如果回答只有“先做个 demo”，会显得你没想清楚 contract 稳定性、fallback 和可验证性。
- 你现在 digest 的 `source_notes` 到底怎么选？如果 `note_type` / `template_family` 误判，digest 会不会把完全不该复盘的 note 混进去？如果回答里没有 source selection、误分类检测和降级策略，会显得你没做过脏数据场景。
- 你把 digest 也接进了 checkpoint，如何证明 resumed digest 不是陈旧结果缓存？如果回答里没有 `thread_id` 复用风险、内容新鲜度和恢复边界，会被继续追问到“这到底是 workflow recovery 还是结果缓存”。
- 你为什么直接拒绝 scoped digest，而不是先把 `note_path` 悄悄忽略？如果说不清输入边界和错误语义，只会暴露你在 workflow 协议设计上没有工程判断。

## [SES-20260314-10] 为 ask / ingest 路径接入 SQLite checkpoint 与 `thread_id` 恢复协议

- 日期：2026-03-14
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-015`
- 本会话唯一目标：在不扩展到 `digest_graph`、审批恢复、proposal schema 或细粒度节点级 interrupt/resume 的前提下，为 ask / ingest 路径接入 SQLite checkpoint 与最小 `thread_id` 恢复协议，让 `thread_id` 不再只是 trace 关联键

### 1. 本次目标

- 为 ask / ingest 两条 graph 路径接入可复用的 SQLite checkpoint 适配层。
- 让 ask / ingest 至少有一条显式恢复路径能按 `thread_id` 复用状态。
- 保证 checkpoint 读写失败不会破坏现有 ask / ingest 主链路。

### 2. 本次完成内容

- 确认 `TASK-015` 是 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中当前最合适绑定的 `medium` 任务，且未预分配 `session_id`，因此为本次会话分配 `SES-20260314-10`。
- 更新 [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)，为 `WorkflowInvokeRequest` 新增 `resume_from_checkpoint` 标志。
- 新增 [backend/app/graphs/checkpoint.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/checkpoint.py)，落地：
  - `WorkflowCheckpointStatus`
  - `PersistedGraphCheckpoint`
  - 仅持久化恢复真正需要的 `StewardState` 字段
  - ask / ingest 可复用的 SQLite checkpoint 保存与读取逻辑
- 更新 [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)，将 schema 升到 `v4` 并新增 `workflow_checkpoint` 表与索引。
- 更新 [backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py)，新增共享 `invoke_checkpointed_linear_graph()` 线性 runner，使 ask / ingest 可以：
  - 在每个节点后持久化 checkpoint
  - 在 `resume_from_checkpoint=true` 时按 `thread_id + graph_name` 读取最近 checkpoint
  - 命中 completed checkpoint 时直接短路返回，避免重复 ask 调用或重复整库 ingest
  - 在 checkpoint 读写失败时把错误写入 state，而不是拖垮主链路
- 更新 [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)，把 ask graph 接到共享 checkpoint runner，并把 checkpoint 恢复命中信息带回执行结果。
- 更新 [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)，让 ingest graph 也复用共享 checkpoint runner。
- 更新 [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)，拒绝缺少显式 `thread_id` 的恢复请求，并在 ask / ingest 命中 checkpoint 时返回 resumed message。
- 更新 [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)，同步补齐 `resume_from_checkpoint` 字段，避免插件 contract 落后于后端。
- 更新测试：
  - [backend/tests/test_indexing_store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_store.py) 覆盖 `workflow_checkpoint` schema 与 checkpoint roundtrip
  - [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py) 覆盖 ask completed checkpoint 恢复命中、缺失 `thread_id` 的恢复请求拒绝、checkpoint 保存失败降级
  - [backend/tests/test_ingest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ingest_workflow.py) 覆盖 ingest completed checkpoint 恢复命中

### 3. 本次未完成内容

- 没有实现 `digest_graph` 的 checkpoint 或恢复。
- 没有实现审批中断后的 `resume_workflow` 控制面协议。
- 没有实现细粒度节点级 interrupt/resume；当前恢复仍停留在线性 graph 的 thread 级状态快照与 completed checkpoint 短路返回。
- 没有实现 `workflow_checkpoint` 的清理策略、查询 CLI 或排障视图。

### 4. 关键决策

- 先把恢复能力压成“共享 SQLite checkpoint + 线性 graph runner”，而不是一口气引入完整 interrupt / approval resume 平台，是为了严格守住 `TASK-015` 的 medium 边界，只解决“checkpoint 能不能用”和“最小恢复协议怎么长”。
- completed checkpoint 命中时直接短路返回，是为了先把 ask 的模型调用和 ingest 的整库副作用挡住；如果这一步还要强行重跑，`thread_id` 恢复就只剩下装饰意义。
- checkpoint 只持久化恢复真正需要的结构化 state，而不把 trace、临时 prompt 上下文和长文本原文一起塞进去，是为了防止恢复语义和观测语义重新耦死。
- 恢复请求必须显式带 `thread_id`，而不是允许匿名“猜最新 checkpoint”，是为了把恢复边界做成显式协议，避免错误命中历史 thread。

### 5. 修改过的文件

- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/app/graphs/checkpoint.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/checkpoint.py)
- [backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py)
- [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)
- [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)
- [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/tests/test_indexing_store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_store.py)
- [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)
- [backend/tests/test_ingest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ingest_workflow.py)
- [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)

### 6. 验证与测试

- 跑了什么命令
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_indexing_store -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_workflow -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_ingest_workflow -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
  - `cd backend && PYTHONPYCACHEPREFIX=/tmp/ks-pycache ../.conda/knowledge-steward/bin/python -m compileall app tests`
  - `cd backend && PYTHONPYCACHEPREFIX=/tmp/ks-pycache python3 -m compileall app tests`
- 结果如何
  - `test_indexing_store`、`test_ask_workflow`、`test_ingest_workflow` 以及后端全量 25 个测试全部通过，覆盖 checkpoint schema、roundtrip、ask / ingest 恢复命中和 checkpoint 保存失败降级。
  - 使用推荐 conda Python 3.12 环境执行 `compileall` 通过。
  - 使用系统 `python3` 执行 `compileall` 失败，原因是系统环境为 Python 3.9.6，而仓库当前依赖 Python 3.12；失败点位于既有 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py) 的 3.12 语法，不是本次 checkpoint 改动引入的新回归。
- 哪些没法验证
  - 没有启动真实 HTTP 服务再通过 `curl` 演示跨进程恢复，只验证了代码路径和测试层面的恢复协议。
  - 没有验证 in-progress / failed checkpoint 在复杂副作用节点上的恢复安全性；当前 ask / ingest 都还是最小线性图。
  - 没有验证插件侧真实消费 `resume_from_checkpoint` 的 UI 行为，因为插件尚无恢复入口。
- 哪些只是静态修改
  - [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)
  - [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 唯一伴随改动是为落地恢复协议所必需的 SQLite schema 升级、插件 contract 补齐与最小 README / 主文档同步，不构成新的 medium 功能。
- 收尾时顺手纠正了 [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 中已经确认的 `proposal / patch_ops schema` 状态漂移，属于事实同步，不是新功能推进。

### 8. 未解决问题

- `resume_from_checkpoint` 目前没有独立的 `resume_workflow` 接口；它只是现有 `/workflows/invoke` 的最小恢复标志。
- checkpoint 粒度还比较粗，尤其 `execute_ingest` 仍是整库副作用节点；这意味着“节点级精细续跑”还没真正解决。
- `thread_id + graph_name` 作为最新 checkpoint 键虽然简单，但如果调用方误复用 `thread_id`，会存在命中历史 completed checkpoint 的风险。
- `workflow_checkpoint` 目前没有清理、查询或健康检查策略，长期运行后可能积累排障负担。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果插件或调用方错误复用旧 `thread_id`，当前 completed checkpoint 的短路返回可能命中过期状态；后续需要请求指纹、版本号或更明确的恢复 UX 约束。
- 技术债：当前恢复能力更接近“thread 级状态快照 + completed checkpoint 短路返回”，还不是可覆盖复杂 interrupt / side-effect 场景的通用恢复平台。
- 技术债：`workflow_checkpoint` 已进入主 SQLite，但还没有清理策略、最小查询工具和表膨胀治理。
- 假设：下一次相关会话应优先进入 `TASK-014`，先补最小 `digest_graph`，再继续推进 `TASK-016` / `TASK-017`，避免把恢复与 HITL 写回协议在同一轮重新揉大。

### 10. 下一步最优先任务

1. 绑定 `TASK-014`，实现 `digest_graph` 骨架与最小 `DAILY_DIGEST` 返回。
2. 在 `TASK-014` 之后推进 `TASK-016`，补 `proposal` / `patch_ops` / `audit_log` 的 SQLite schema。
3. 保留本次新增的轻量派生项，后续补 `workflow_checkpoint` 的清理与查询入口。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/graphs/checkpoint.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/checkpoint.py)
- [backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py)
- [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)
- [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)
- [backend/tests/test_ingest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ingest_workflow.py)

### 12. 当前最容易被面试官追问的点

- 你说自己实现了 checkpoint，但你这次恢复到底是“节点级中断续跑”，还是“thread 级状态快照 + 已完成态短路返回”？如果回答只说“都算恢复”，会显得你没有区分真正的 workflow recovery 和结果缓存。
- 为什么 checkpoint 放在主 SQLite 里自己维护 `workflow_checkpoint`，而不是直接依赖 LangGraph 的官方 saver？如果回答只有“这样方便”，会显得你没想过部署依赖、查询可观测性、schema 演进和本地单文件事实源的取舍。
- ingest 是带副作用的整库流程，你为什么敢让 completed checkpoint 直接短路？如果说不清 `execute_ingest` 当前是单节点幂等覆盖、以及为什么这还不足以证明复杂中断恢复安全，会被继续追问到写库重复执行和状态一致性。
- 你现在用 `thread_id + graph_name` 命中最新 checkpoint，如果前端误复用 thread_id 会发生什么？如果回答里没有请求指纹、版本校验或显式恢复 UX 约束，会显得恢复协议边界根本没定义清楚。

## [SES-20260314-09] 实现 `ingest_graph` 骨架与 `INGEST_STEWARD` workflow 入口

- 日期：2026-03-14
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-013`
- 本会话唯一目标：在不生成 proposal、不实现写回或审批、也不接入 checkpoint 恢复的前提下，把当前 CLI 级别的 ingest 能力接入最小 `ingest_graph` 与 `/workflows/invoke` 入口，让 `INGEST_STEWARD` 不再停留在占位响应

### 1. 本次目标

- 新增 `backend/app/graphs/ingest_graph.py`，把现有 full ingest 逻辑接进最小 graph。
- 让 `/workflows/invoke` 的 `INGEST_STEWARD` 真实进入 graph，并返回最小 ingest 结果。
- 复用 ask 路径已有的 `thread_id` / `run_id` / runtime trace 语义，而不是另起一套 workflow 协议。

### 2. 本次完成内容

- 确认 `TASK-013` 在 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中没有预分配 `session_id`，且 `SES-20260314-01` 到 `SES-20260314-08` 已占用，因此为本次会话分配 `SES-20260314-09`。
- 新增 [backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py)，抽出：
  - `RuntimeTraceEvent`
  - `TraceHook`
  - LangGraph 缺失时的兼容 runner
  - 统一的 `append_trace_event()`
- 更新 [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)，改为复用共享 graph runtime，而不是继续在 ask 内部维护一套重复的 runner / trace event 追加逻辑。
- 新增 [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)，落地：
  - `invoke_ingest_graph()`
  - `IngestGraphExecution`
  - `prepare_ingest -> execute_ingest -> finalize_ingest` 三节点最小 graph
  - 对现有 `ingest_vault()` 的 graph 封装
  - `JSONL + SQLite + 外部 hook` 的 runtime trace 复用
  - 对 `note_path / note_paths` 局部 ingest 请求的显式拒绝，避免当前任务悄悄越界到增量 / 定向 ingest
- 更新 [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)，新增：
  - `IngestWorkflowResult`
  - `WorkflowInvokeResponse.ingest_result`
- 更新 [backend/app/graphs/state.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/state.py)，补齐 `ingest_result` 状态字段，避免 ingest graph 继续塞回非结构化 message。
- 更新 [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)，让 `/workflows/invoke` 的 `INGEST_STEWARD`：
  - 统一沿用 API 入口生成的 `thread_id` / `run_id`
  - 真实走 `invoke_ingest_graph()`
  - 返回 `COMPLETED + ingest_result`
- 更新 [backend/app/graphs/__init__.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/__init__.py)，导出 ingest graph 入口。
- 新增 [backend/tests/test_ingest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ingest_workflow.py)，覆盖：
  - ingest graph 返回统计结果
  - `thread_id` / `run_id` 贯通
  - ingest 路径 runtime trace JSONL 与 SQLite `run_trace` 写入
  - 对未支持的 partial scope 请求返回 400
- 更新 [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)，同步补最小 `ingest_result` 类型，避免插件端 workflow contract 再次落后于后端。

### 3. 本次未完成内容

- 没有实现 `note_path` / `note_paths` 定向 ingest；当前仍只支持 full-vault ingest。
- 没有实现 checkpoint、恢复协议或 ingest graph 的中断续跑。
- 没有实现 digest graph，也没有把 ingest 扩成治理 proposal 闭环。
- 没有把 `execute_ingest` 节点继续拆成更细粒度的扫描 / 解析 / 写库 / FTS 重建事件；当前 trace 粒度仍是最小骨架级别。

### 4. 关键决策

- 先把现有 `ingest_vault()` 作为一个业务节点接进 graph，而不是顺手重写为更细节点，是为了严格守住 `TASK-013` 的 medium 边界，优先解决 workflow 入口、状态和 trace 语义，而不是重做一轮 ingest 功能。
- `INGEST_STEWARD` 当前明确拒绝 `note_path / note_paths`，而不是静默忽略，是为了把“还没做的定向 ingest”暴露成清晰输入边界，避免后续误以为系统已经支持局部范围同步。
- ask / ingest 共用 [backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py) 的 runner 与 trace event 追加逻辑，是为了先收敛多 graph 的最小运行时语义，避免 graph 数量一增加就复制粘贴两套兼容逻辑。
- ingest graph 当前复用 `KS_ASK_RUNTIME_TRACE_PATH` 对应的 JSONL 路径，不是因为 ingest 只配叫“ask trace”，而是因为本轮目标是先打通多 graph 最小 runtime trace；配置命名与按 graph 分流属于后续轻量治理项。

### 5. 修改过的文件

- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/app/graphs/state.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/state.py)
- [backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py)
- [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)
- [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)
- [backend/app/graphs/__init__.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/__init__.py)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/tests/test_ingest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ingest_workflow.py)
- [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)

### 6. 验证与测试

- 跑了什么命令
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_ingest_workflow -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
  - `cd backend && PYTHONPYCACHEPREFIX=/tmp/ks-pycache python3 -m compileall app tests`
- 结果如何
  - 新增 ingest workflow 专项 3 个用例全部通过，覆盖 graph 入口、trace 写入和 partial scope 拒绝分支。
  - 后端全量 20 个用例全部通过，没有回归 ask / ingest / retrieval / store 既有行为。
  - `compileall` 通过，没有语法错误。
- 哪些没法验证
  - 没有运行真实 HTTP 服务再用 `curl` 触发 `INGEST_STEWARD` 做命令级端到端演示；本次验收主要依赖单元测试和代码路径。
  - 没有验证大 Vault 下 ingest graph 的长耗时、锁竞争和 trace 膨胀问题。
  - 没有验证插件侧对 `ingest_result` 类型的真实消费，因为插件还没有 ingest UI。
- 哪些只是静态修改
  - [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 唯一伴随改动是抽 [backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py) 复用 ask / ingest 的 graph 运行时逻辑，并同步插件 contract 类型；这两项都直接服务于 `TASK-013` 的“graph + contract + trace 语义贯通”，不构成新的 medium 功能。
- 本次没有顺手推进 `TASK-014`、`TASK-015` 或增量 ingest，只是把未支持的 partial scope 明确拦截成 400。

### 8. 未解决问题

- `INGEST_STEWARD` 当前只有 full-vault 模式，局部 ingest、删除文件回收和变更窗口优化仍未实现。
- ingest graph 还没有 checkpoint、resume 或更细粒度节点 trace。
- `KS_ASK_RUNTIME_TRACE_PATH` 现在已承载 ask / ingest 共用的 runtime trace 落盘语义，配置命名开始与实际用途出现偏差。
- 插件侧虽然已同步 `ingest_result` 类型，但还没有 ingest 命令、状态展示或 trace 调试入口。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果后续直接在 `INGEST_STEWARD` 上叠加局部路径 ingest，而不先定义清楚 scope / 删除语义，容易把 full ingest、partial ingest 和后续增量索引揉成一坨。
- 技术债：ingest graph 当前把整轮 ingest 作为单节点执行，trace 对“卡在扫描、解析、写库还是 FTS 重建”还不够细。
- 技术债：`KS_ASK_RUNTIME_TRACE_PATH` 已从 ask 专用配置演化成多 graph 共用最小 runtime trace path，命名漂移如果不收敛，后续 observability 配置会越来越难讲清。
- 假设：下一次相关会话会优先进入 `TASK-015`，在 ask / ingest 已接图的前提下补 checkpoint 与恢复协议，而不是先把 ingest graph 彻底重写成细粒度节点。

### 10. 下一步最优先任务

1. 绑定 `TASK-015`，为 ask / ingest 路径接入 SQLite checkpoint 与 `thread_id` 恢复协议。
2. 在 `TASK-015` 之后继续推进 `TASK-014`，补最小 `digest_graph` 与 `DAILY_DIGEST` 返回。
3. 保留本次新增的轻量派生项，后续收敛 runtime trace 配置命名或分流策略。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py)
- [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)
- [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/tests/test_ingest_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ingest_workflow.py)

### 12. 当前最容易被面试官追问的点

- 你现在说 `ingest_graph` 已经落地，但 `execute_ingest` 里本质上还是一次整库 `ingest_vault()`；如果回答只是“先统一架构”，会显得像给 CLI 函数外面套了一层框架壳，而不是你真的想清楚了 graph 的工程价值。
- 你为什么在 `INGEST_STEWARD` 明确拒绝 `note_path / note_paths`，而不是先默默忽略；如果回答只有“还没做”，会显得你没有定义好输入边界、错误语义和未来 partial ingest 的风险面。
- 你把 ingest trace 也挂到了 `KS_ASK_RUNTIME_TRACE_PATH` 对应路径上；如果回答成“反正先能跑起来”，会显得你没意识到配置语义漂移、后续多 graph trace 治理和运维可理解性问题。
- 你现在 trace 只有 `prepare / execute / finalize` 三条事件，真正的长耗时都压在单个 `execute_ingest` 节点里；如果回答只有“后面再细化”，会显得你对长流程观测、失败定位和 checkpoint 粒度没有工程判断。

## [SES-20260314-08] 继续拆解主计划并登记下一批 medium 队列任务

- 日期：2026-03-14
- 类型：`Docs`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-012`
- 本会话唯一目标：在不实现任何业务功能、也不改动总体架构路线的前提下，继续把 `docs/PROJECT_MASTER_PLAN.md` 中已足够清晰的后续主线拆成可执行的 medium 任务，并登记进 `docs/TASK_QUEUE.md`

### 1. 本次目标

- 避免 `TASK-011` 完成后任务队列出现断档。
- 把 Phase 3 / Phase 4 / Phase 5 中最优先、边界最清晰的一批工作收敛成可执行任务。
- 让主文档中的“下一步先补新的 medium 任务登记”落成事实，而不是继续停留在提示语。

### 2. 本次完成内容

- 确认 `TASK_QUEUE` 在 `TASK-011` 完成后暂时没有新的已登记 medium 任务，且 `SESSION_LOG` 中 `SES-20260314-01` 到 `SES-20260314-07` 已占用，因此为本次会话分配 `SES-20260314-08`。
- 在 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中新增并关闭 [TASK-012](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)，把本次会话绑定为“继续拆解主计划并登记下一批 medium 队列任务”的 docs 类任务。
- 在 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中新增下一批任务：
  - `TASK-013`：实现 `ingest_graph` 骨架与 `INGEST_STEWARD` workflow 入口
  - `TASK-014`：实现 `digest_graph` 骨架与最小 `DAILY_DIGEST` 返回
  - `TASK-015`：为 ask / ingest 路径接入 SQLite checkpoint 与 `thread_id` 恢复协议
  - `TASK-016`：设计并落地 `proposal` / `patch_ops` / `audit_log` 的 SQLite schema
  - `TASK-017`：实现 `resume_workflow` 协议与审批中断 contract
  - `TASK-018`：实现插件审批面板与 diff 预览骨架
  - `TASK-019`：实现插件侧受限写回执行器与 `before_hash` 校验
  - `TASK-020`：为 generated answer 增加程序级 citation 对齐校验
  - `TASK-021`：构建最小 golden set 与 `eval/run_eval.py`
- 更新 [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)，把“优先补新的 medium 任务登记”的状态改为已完成，并把主文档中的下一步动作更新为优先执行新登记的 `TASK-013` 及其后续主线。

### 3. 本次未完成内容

- 没有实现任何新功能，所有新增任务仍停留在队列规划层。
- 没有把 Phase 2/3/4/5 的所有 backlog 一次性全部拆完；本次只登记了当前最清晰、最接近执行的下一批任务。
- 没有为更远期的多 graph tracing 平台化、复杂 UI 打磨、全面性能优化等内容建新任务，因为当前边界仍偏大。

### 4. 关键决策

- 先把 Phase 3 / Phase 4 的主闭环任务补进队列，再登记 citation 校验和最小 eval，是因为这些更贴近当前项目主叙事；如果这时优先排 hybrid / rerank 等次级补强，队列会再次偏向“问答功能堆叠”，削弱知识治理主线。
- 本次新增的 `TASK-015` 只要求 ask / ingest 路径接入 checkpoint，而不是一口气覆盖所有 graph，是为了把 checkpoint 任务压回 medium 边界，避免又出现一个“看起来合理但做不完”的大任务。
- `TASK-019` 只允许 frontmatter merge 和受限正文插入，不把自由删除、整篇重写和自动回滚塞进同一任务，是为了守住写回安全边界，避免 Phase 4 一上来就失控。
- `TASK-021` 明确要求“30 条左右的最小样本 + 脚本执行器”，而不是完整评测平台，是为了让 eval 任务保持可落地，而不是继续停留在面试叙事层。

### 5. 修改过的文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)

### 6. 验证与测试

- 跑了什么命令
  - `sed -n '1388,1505p' docs/PROJECT_MASTER_PLAN.md`
  - `rg -n "Next Action|未实现|进行中|建议后续补|后续需补" docs/PROJECT_MASTER_PLAN.md`
  - `rg -n "^### TASK-" docs/TASK_QUEUE.md`
  - `rg -n "TASK-012|TASK-013|TASK-021|SES-20260314-08" docs/TASK_QUEUE.md docs/SESSION_LOG.md docs/PROJECT_MASTER_PLAN.md`
- 结果如何
  - 已基于主文档中仍处于 `进行中 / 未开始` 的块完成下一批任务拆解。
  - 关键 `task_id` / `session_id` 已落盘且无冲突。
  - 主文档中“先补新的 medium 任务登记”的旧表述已同步修正。
- 哪些没法验证
  - 这是一次 docs / 队列规划会话，没有可执行代码路径，因此没有运行单元测试或端到端测试。
  - 新增任务的粒度是否最优，需要在后续真正执行时继续校正。
- 哪些只是静态修改
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 本次没有顺手落任何代码实现，也没有借“拆任务”名义调整架构路线。
- 唯一的范围取舍是没有把所有 backlog 一次性全部入队；这是有意收敛，不是遗漏。

### 8. 未解决问题

- 当前队列已经补齐主线下一批任务，但更后期的 retrieval 补强、trace 治理深化、复杂 UI 与性能优化还没有继续拆成独立任务。
- `TASK-014` 到 `TASK-021` 的具体执行顺序仍可能因实现时的阻塞情况微调。
- 一些当前仍偏大的主题，如“完整多 graph tracing 平台化”与“全面插件体验打磨”，后续还需要继续拆分。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果后续执行中不严格按新队列推进，项目仍可能重新滑回“主计划很完整、队列却断档”的状态。
- 技术债：当前 `TASK-021` 之前还没有真实 eval 执行器，后续任务优先级一旦继续向功能偏移，评估闭环仍会滞后。
- 假设：下一阶段优先执行 Phase 3 / Phase 4 主线，而不是突然切回较远期的次要优化项。

### 10. 下一步最优先任务

1. 绑定 `TASK-013`，实现 `ingest_graph` 骨架与 `INGEST_STEWARD` workflow 入口。
2. 再根据 `TASK-013` 的实际结果，继续推进 `TASK-014` 或 `TASK-015`。
3. Phase 4 相关任务应保持顺序依赖，不要跳过 schema / resume contract 直接做高风险写回。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)
- [backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py)
- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)

### 12. 当前最容易被面试官追问的点

- 你为什么在 queue 里先排 `ingest_graph` 和 HITL 主线，而不是继续做 hybrid / rerank；如果回答只是“因为文档这么写”，会显得你没有真正理解主叙事和技术债优先级。
- 你把 checkpoint、approval contract、plugin 审批面板和受限写回拆成多条任务，边界看起来合理；但如果问你“为什么这些不合并成一个会话”，你得说清楚副作用、恢复协议和 UI 三件事为什么必须分层推进。
- 你现在把 eval 放在相对后面，面试官会继续追问：如果前面几个功能任务都做了，却迟迟不补 golden set 和回归，你怎么证明不是一直在堆 demo 能力。

---

## [SES-20260314-07] 为 ask trace 增加 SQLite `run_trace` 聚合表与最小查询入口

- 日期：2026-03-14
- 类型：`Infra`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-011`
- 本会话唯一目标：在不接外部观测平台、不扩展到 ingest / digest graph tracing、也不引入 dashboard / 告警系统的前提下，为 ask trace 增加 SQLite `run_trace` 聚合表与最小查询入口，并保持聚合失败不阻断 ask 主链路

### 1. 本次目标

- 把 ask graph 的核心 trace 字段聚合到 SQLite，避免 trace 长期停留在“只会写 JSONL、不好查”的状态。
- 支持按 `run_id` 或 `thread_id` 做最小查询，形成可本地验证的 observability 骨架。
- 保持 SQLite 聚合失败不阻断 ask 主链路，不改变 `AskWorkflowResult` / `WorkflowInvokeResponse` contract。

### 2. 本次完成内容

- 确认 `TASK-011` 在 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中没有预分配 `session_id`，且 `SES-20260314-01` 到 `SES-20260314-06` 已占用，因此为本次会话分配 `SES-20260314-07`。
- 更新 [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)，将 SQLite schema 升级到 `v3`，新增 `run_trace` 表以及按 `run_id` / `thread_id` / `graph_name` 查询所需索引。
- 更新 [backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py)，新增：
  - SQLite trace sink
  - `PersistedRunTraceEvent`
  - `query_run_trace_events()` / `query_run_trace_events_in_db()`
  - `python -m app.observability.runtime_trace` 的最小 CLI 查询入口
  - `trace_id` 生成、`details_json` 序列化与查询反序列化
- 更新 [backend/app/observability/__init__.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/__init__.py)，导出 SQLite sink 和查询 helper。
- 更新 [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)，让 ask graph 默认组合 `JSONL + SQLite + 外部 hook` 三路 trace sink，并继续沿用“单 sink 异常隔离”的降级策略。
- 更新 [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)，新增或扩展：
  - `run_trace` 写库与按 `run_id` / `thread_id` 查询验证
  - SQLite sink 失败不阻断 ask 的降级验证
- 更新 [backend/tests/test_indexing_store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_store.py)，补 `run_trace` 表结构与索引验证。
- 在本次收尾中同步更新 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)、[docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 与 [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)，修正文档中“SQLite trace 聚合仍未实现”的状态漂移。

### 3. 本次未完成内容

- 没有实现 ingest / digest graph 的 trace 聚合，当前仍只有 ask 路径接入 `run_trace`。
- 没有补 trace 文件轮转、SQLite 清理压缩、断流发现或健康检查。
- 没有补模型 latency、token 用量、检索 SQL 耗时等更细粒度指标。
- 没有新增 HTTP / 插件侧 trace 查询界面；当前最小查询入口仍是模块 helper 和 CLI。

### 4. 关键决策

- `run_trace` 复用现有 [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py) 的 SQLite migration，而不是再拆一套 trace 专用数据库，是为了让索引事实和运行轨迹先落在同一份本地事实源里，避免首版就分裂出第二套持久化入口。
- ask trace 保留 `JSONL + SQLite` 双写，而不是二选一，是因为两者承担不同职责：JSONL 适合原始事件留存和快速抽样排障，SQLite 适合按 `run_id` / `thread_id` 做结构化聚合查询。
- `trace_id` 用事件关键字段和 `details_json` 的哈希生成，并在 SQLite 侧 `ON CONFLICT DO NOTHING`，是为了先兜住“同一事件被重复落库”这一类幂等问题，而不引入更重的事件版本治理。
- SQLite sink 仍然放在组合 hook 中按单 sink 异常隔离，是为了保证 observability 故障不会反向拖垮 ask 主链路；这条降级边界延续了 `TASK-010` 的设计。

### 5. 修改过的文件

- [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- [backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py)
- [backend/app/observability/__init__.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/__init__.py)
- [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)
- [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)
- [backend/tests/test_indexing_store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_store.py)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 6. 验证与测试

- 跑了什么命令
  - `python3 -m compileall backend/app backend/tests`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_indexing_store tests.test_ask_workflow -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
- 结果如何
  - `compileall` 通过，没有语法错误。
  - `test_indexing_store` + `test_ask_workflow` 共 11 个用例全部通过，覆盖 `run_trace` schema、查询与 SQLite sink 失败降级。
  - 后端全量 17 个用例全部通过，没有回归既有 ingest / retrieval / ask 行为。
- 哪些没法验证
  - 没有验证高并发下 JSONL / SQLite 双写的一致性和锁竞争。
  - 没有验证长时间运行后的 SQLite 膨胀、查询性能衰减和清理策略。
  - 没有重新跑真实 HTTP 服务后用 CLI 查询 `run_trace` 的端到端命令级演示；本次验收主要依赖单元测试和代码路径。
- 哪些只是静态修改
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 唯一伴随改动是为 `run_trace` 查询补一个极薄的 CLI 入口和表结构测试；它们都直接服务于“最小查询入口”这一验收目标，不构成新的 medium 功能。
- 主文档与 README 同步属于本次显式收尾要求，不属于功能范围扩张。

### 8. 未解决问题

- `run_trace` 目前只覆盖 ask 路径，多 graph trace 还没有统一字段和复用策略。
- 事件字段仍然偏粗，暂时不足以拆解模型耗时、token 成本和检索耗时。
- 当前没有 trace 断流告警；如果 JSONL 和 SQLite 长期双写失败，只能靠人工检查或测试暴露。
- SQLite sink 目前是逐事件落库，后续可能遇到吞吐、锁竞争和批量写入效率问题。

### 9. 新增风险 / 技术债 / 假设

- 风险：JSONL + SQLite 双写虽然补齐了“可留存 + 可查询”，但也引入了双写一致性和长期膨胀治理问题。
- 技术债：`run_trace` 当前没有事件版本字段，也没有 schema 演进策略；后续细化 `details` 时要避免把查询端打碎。
- 技术债：SQLite sink 目前是同步逐条写入，未来若 ask 吞吐增加，可能需要批量缓冲或异步落盘。
- 假设：当前 ask trace 的事件结构在后续一两个会话内不会被大幅推翻，否则 `trace_id` 和查询字段需要同步迁移。

### 10. 下一步最优先任务

1. 如果继续推进编码，下一次会话应先在 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中登记新的 medium 任务；建议优先回到 Phase 3 主线，拆出 ingest graph 骨架与 workflow 入口。
2. 保留 `TASK-011` 现有的轻量派生项，后续补 `run_trace` / JSONL 的清理压缩与断流治理。
3. 在 observability 侧再往前推进时，应优先补更细粒度指标，而不是急着堆 dashboard。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- [backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py)
- [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)
- [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)
- [backend/tests/test_indexing_store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_store.py)

### 12. 当前最容易被面试官追问的点

- 你为什么坚持把 `run_trace` 落在现有业务 SQLite，而不是单独做 trace DB；如果主库损坏、锁竞争或 schema 演进冲突，你怎么隔离风险。
- 你为什么选择 `JSONL + SQLite` 双写，而不是只保留一种；两边不一致时谁是准、怎么追责、怎么修复。
- 你现在的 `trace_id` 是哈希生成的，看起来像“先跑起来”；那遇到事件结构变更、重放、补写和版本演进时，你准备怎么保证幂等和兼容。
- 你说聚合失败不阻断 ask 是对的，但如果 SQLite sink 一周都在静默失败，你靠什么发现；如果回答只有“看日志”，会显得你没做过真正的可观测性治理。

---

## [SES-20260314-06] 落地 ask runtime trace 的 JSONL 持久化骨架

- 日期：2026-03-14
- 类型：`Infra`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-010`
- 本会话唯一目标：在不改现有 ask 返回 contract、也不扩展到 audit log、ingest/digest graph tracing 或外部观测平台的前提下，把 ask graph 的 runtime trace 落到本地 JSONL，形成最小可查询 tracing 骨架

### 1. 本次目标

- 为 ask graph 每次执行默认写出包含 `thread_id`、`run_id`、`node_name`、`event_type`、时间戳等核心字段的 JSONL trace。
- 保持 tracing 失败不阻断 ask 主链路，避免观测层反向拖垮业务链路。
- 在不改变 `AskWorkflowResult` / `WorkflowInvokeResponse` contract 的前提下，补最小测试验证文件生成与失败降级。

### 2. 本次完成内容

- 确认 `TASK-010` 在 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中没有预分配 `session_id`，且 `SES-20260314-01` 到 `SES-20260314-05` 已占用，因此为本次会话分配 `SES-20260314-06`。
- 更新 [backend/app/config.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/config.py)，新增 `ask_runtime_trace_path`，默认落到 `data/traces/ask_runtime.jsonl`，并允许通过 `KS_ASK_RUNTIME_TRACE_PATH` 覆盖。
- 新增 [backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py) 与 [backend/app/observability/__init__.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/__init__.py)，落地：
  - JSONL append sink
  - trace hook 组合器
  - 基础 JSON 序列化适配
  - 单 sink 异常隔离
- 更新 [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)，让 `invoke_ask_graph()` 在保留外部 `trace_hook` 的同时，默认接入 JSONL 落盘。
- 更新 [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)，新增或扩展：
  - JSONL 文件生成验证
  - 持久化 trace 的核心字段校验
  - trace 写盘失败不阻断 ask 的降级验证
- 在本次收尾中同步更新 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)、[docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 与 [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)，修正文档中“持久化 trace 仍未开始”的状态漂移。

### 3. 本次未完成内容

- 没有实现 SQLite `run_trace` 聚合表或最小查询入口；当前 trace 仍是本地 JSONL 调试骨架。
- 没有实现 ingest / digest graph tracing，多 graph 统一字段治理仍未开始。
- 没有实现 trace 文件轮转、压缩、清理策略，也没有断流健康检查。
- 没有新增外部观测平台接入、告警或 dashboard。

### 4. 关键决策

- JSONL sink 放在 [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py) 的 `invoke_ask_graph()` 里统一接入，而不是只在 API 层补，是为了覆盖直接调用 graph 的测试和后续复用入口，避免只有 `/workflows/invoke` 才落 trace。
- 默认 JSONL 落盘与调用方自定义 `trace_hook` 采用组合 hook，而不是二选一，是为了同时满足“最小持久化”和“测试/扩展 sink”两类需求。
- 每个 trace sink 的异常都在组合器内单独吞掉，并继续执行后续 sink，是为了防止某个持久化路径失效时顺手把其他观测路径和 ask 主链路一起拖垮。
- 当前先做 JSONL，而不是直接上 SQLite `run_trace`，是为了先解决“可落盘、可保留、可抽样查看”的事实缺口，再决定聚合查询和 schema 演进策略。

### 5. 修改过的文件

- [backend/app/config.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/config.py)
- [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)
- [backend/app/observability/__init__.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/__init__.py)
- [backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py)
- [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 6. 验证与测试

- 跑了什么命令
  - `python3 -m compileall backend/app backend/tests`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_workflow -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
- 结果如何
  - `compileall` 通过，没有语法错误。
  - ask 专项 7 个用例全部通过，覆盖持久化文件生成、核心字段和 trace 写失败降级。
  - 后端全量 15 个用例全部通过，没有回归既有 ingest / retrieval / ask 行为。
- 哪些没法验证
  - 没有验证多进程并发追加同一 JSONL 文件时的竞争与半行写入风险。
  - 没有验证真实运行中的 trace 文件轮转、磁盘占用控制和长期断流发现。
  - 没有重新跑一遍真实 HTTP 服务 + `curl` 端到端 ask 调用；本次验收主要依赖单元测试与代码级路径。
- 哪些只是静态修改
  - [backend/app/config.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/config.py)
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 唯一伴随改动是新增一个极薄的 [backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py) 模块和配置项；这是完成 `TASK-010` 必需的接口适配，不构成新的 medium 功能。
- README 与主文档同步属于本次显式收尾要求，不属于开发范围扩张。

### 8. 未解决问题

- JSONL trace 目前只是 append-only 调试骨架，缺少 SQLite 聚合查询、字段版本治理和回放工具。
- `details` 字段仍然比较粗，暂时不足以定位“检索慢还是模型慢”这类更细粒度问题。
- 当前没有 trace 断流告警；如果落盘长期失败，只能靠人工检查文件或测试暴露。
- 只有 ask 路径默认落盘，ingest / digest graph 尚未接入相同 observability 语义。

### 9. 新增风险 / 技术债 / 假设

- 风险：JSONL 采用本地文件追加，长时间运行后可能出现文件无限增长、查询效率下降和轮转治理缺失的问题。
- 技术债：当前 trace sink 没有跨进程锁和健康探测，仍是 best-effort 调试级实现。
- 技术债：`backend/app/observability/` 目前只有 runtime trace writer，还没有错误日志、统一 tracer/logger 抽象和 SQLite 聚合层。
- 假设：下一次 observability 相关会话会基于当前 JSONL 事实继续补 `run_trace` 聚合或 trace health，而不是推翻现有 event 结构。

### 10. 下一步最优先任务

1. 绑定 `TASK-011`，在 ask JSONL trace 已落地的前提下补 SQLite `run_trace` 聚合表与最小查询入口，避免 trace 长期停留在“可落盘但不好查”的状态。
2. 保留 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中的轻量派生项，后续补 trace 文件轮转 / 健康检查和插件侧 `run_id` / `thread_id` 暴露。
3. 再之后回到 Phase 3 主线，评估 ingest / digest graph 的接入顺序。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)
- [backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py)
- [backend/app/config.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/config.py)
- [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)

### 12. 当前最容易被面试官追问的点

- 你说 tracing 已经落地了，但为什么只先写 JSONL，不直接做 SQLite `run_trace` 或外部平台；你到底是在控制范围，还是在回避真正的查询和聚合设计。
- 你把 trace 写失败吞掉是对的，但你怎么发现长期静默断流；如果线上一个月都没写进文件，你靠什么证明观测没有失效。
- 现在 trace 只有 `prepare_ask / execute_ask / finalize_ask` 三个粗节点，没有模型 latency、token 用量、检索 SQL 耗时；那你拿什么支撑“可定位瓶颈”这件事。
- 为什么把默认落盘接在 graph 入口，而不是 FastAPI 路由；如果后续还有 CLI、批处理、其他 graph，你的 trace 语义如何保持一致。

---

## [SES-20260314-05] 实现 `ask_graph` 骨架与 `thread_id` 贯通

- 日期：2026-03-14
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-009`
- 本会话唯一目标：在不扩展到 ingest/digest graph、HITL 写回、持久化 checkpoint 和完整 observability 子系统的前提下，把 ask 从普通 API 分支升级为最小 `ask_graph`，统一 `thread_id` / `run_id` 与 state 入口，并补最小 tracing hook

### 1. 本次目标

- 新增 `ask_graph` 文件与最小节点骨架，避免 ask 继续停留在普通 API 分支。
- 让 `thread_id` 在 API、state 与 graph 入口之间保持一致，并补齐 `run_id` 的单次运行语义。
- 在不把 tracing 扩成新一轮 medium 功能的前提下，补一个最小 trace hook / trace event 机制，给后续持久化 tracing 留入口。

### 2. 本次完成内容

- 确认 `TASK-009` 在 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中没有预分配 `session_id`，且 `SES-20260314-01` 到 `SES-20260314-04` 已被占用，因此为本次会话分配 `SES-20260314-05`。
- 新增 [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)，落地：
  - `invoke_ask_graph()`
  - `AskGraphExecution`
  - `RuntimeTraceEvent`
  - `prepare_ask -> execute_ask -> finalize_ask` 三节点最小 graph
  - `trace_hook` 与 state 内 `trace_events`
  - 在 `langgraph` 未安装时可运行的最小兼容 runner，避免环境漂移直接把开发链路打断
- 更新 [backend/app/graphs/state.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/state.py)，补齐 ask graph 直接使用的状态字段：
  - `provider_preference`
  - `retrieval_filter`
  - `request_metadata`
  - `ask_result`
  - `trace_events`
- 更新 [backend/app/graphs/__init__.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/__init__.py)，导出 ask graph 入口与 trace event 类型。
- 更新 [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)，让 `/workflows/invoke` 的 `ask_qa`：
  - 在 API 入口统一生成 `thread_id` 与 `run_id`
  - 走 `invoke_ask_graph()`，而不是直接调用 `run_minimal_ask()`
  - 继续复用既有 `AskWorkflowResult` 返回语义，不推翻 `TASK-008` 的 contract
- 更新 [backend/pyproject.toml](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/pyproject.toml) 与 [backend/environment.yml](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/environment.yml)，把 `langgraph` 补进依赖声明，修正“项目主张是 LangGraph，但环境声明里没有 LangGraph”的事实漂移。
- 更新 [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)，新增：
  - 显式 `thread_id` 透传验证
  - `invoke_ask_graph()` 的 trace event 验证
  - `run_id` 生成与 ask 结果不回退验证
- 在 `conda env update` 因外部源连接失败和 `NoWritablePkgsDirError` 无法完成的情况下，改用 `./.conda/knowledge-steward/bin/pip install langgraph` 将真实依赖安装进工作区本地环境，并用解释器导入检查确认 `langgraph=True`。

### 3. 本次未完成内容

- 没有实现 SQLite checkpoint、恢复执行或 `thread_id` 级持久化恢复；当前只是把 `thread_id` / `run_id` 语义先收敛到 ask graph。
- 没有把 trace event 落到 JSONL / SQLite；当前 tracing 仍停留在 graph 内存态和 hook 层。
- 没有实现 ingest graph、digest graph，也没有统一三条 graph 的共享状态演化策略。
- 没有补 generated answer 的程序级 citation 对齐校验；这仍是 ask 质量闭环中的明显缺口。
- 没有验证插件侧是否消费 `run_id` / `thread_id`，也没有补 resume / 调试 UI。

### 4. 关键决策

- 先用一个很薄的 ask graph 包住现有 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py) 业务逻辑，而不是在本轮顺手重写 ask 节点链，是为了严格守住 `TASK-009` 的范围边界，优先解决“状态与协议”而不是重新做一轮 ask 功能开发。
- `thread_id` 与 `run_id` 放在 API 入口统一生成，而不是 graph 内外各自生成，是为了避免后续 trace、audit、checkpoint 关联键从第一天就漂移。
- trace 里只记录 query 长度和过滤条件摘要，不直接复制原始用户 query，是为了在 tracing 还没有脱敏策略前，先避免把原始输入扩散到观测数据。
- trace hook 的异常被显式吞掉，是为了让观测层故障不反向拖垮 ask 主链路；这是典型的“trace 失败不能影响业务结果”的降级策略。
- 代码里保留 `langgraph` 缺失时的兼容 runner，不是为了长期规避依赖，而是为了避免开发环境一旦少装包就完全无法进入现有 ask graph 路径；同时本次仍然把 `langgraph` 补进了依赖声明并完成了本地真实安装。

### 5. 修改过的文件

- [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)
- [backend/app/graphs/state.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/state.py)
- [backend/app/graphs/__init__.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/__init__.py)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)
- [backend/pyproject.toml](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/pyproject.toml)
- [backend/environment.yml](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/environment.yml)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 6. 验证与测试

- 跑了什么命令
  - `cd backend && PYTHONPYCACHEPREFIX=/tmp/ks-pycache python3 -m compileall app tests`
  - `cd backend && python3 -m unittest tests.test_ask_workflow -v`
  - `cd backend && python3 -m unittest discover -s tests -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_workflow -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
  - `conda env update --prefix ./.conda/knowledge-steward --file backend/environment.yml --prune`
  - `./.conda/knowledge-steward/bin/pip install langgraph`
  - `cd backend && ../.conda/knowledge-steward/bin/python - <<'PY' ... importlib.util.find_spec('langgraph') ... PY`
- 结果如何
  - `compileall` 通过，没有语法错误。
  - 系统自带 `python3` 跑 `unittest` 时失败，原因是该解释器里没有 `fastapi`，这说明系统 Python 不是项目验收环境。
  - 改用工作区本地 conda Python 后，ask 专项 6 个用例全部通过，后端全量 14 个用例全部通过，没有回归 `TASK-005` 到 `TASK-008` 的既有行为。
  - `conda env update` 因外部源 `HTTP 000 CONNECTION FAILED` 和 `NoWritablePkgsDirError` 未能完成。
  - 直接使用工作区本地环境里的 `pip` 安装 `langgraph` 成功，随后导入检查返回 `True`，并确认 [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py) 中 `LANGGRAPH_AVAILABLE` 为 `True`。
- 哪些没法验证
  - 还没有 checkpoint / resume，因此无法验证 `thread_id` 在跨进程恢复时是否仍然可靠。
  - 还没有 JSONL / SQLite trace sink，因此无法验证 trace 数据的持久化、查询和回放。
  - 还没有真实 provider 联网验证，因此 ask graph 只证明了 graph 包装和 contract 不回退，不证明线上模型端到端稳定性。
  - 还没有跑插件构建，无法验证插件侧是否已经消费 `run_id` / `thread_id`。
- 哪些只是静态修改
  - [backend/pyproject.toml](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/pyproject.toml)
  - [backend/environment.yml](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/environment.yml)
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 唯一伴随改动是补 `langgraph` 依赖声明并在工作区本地环境里实际安装，因为当前仓库已经把项目主张写成“基于 LangGraph”，但本次开工前依赖文件里并没有 `langgraph`；这属于完成 `TASK-009` 的必要接口与环境适配，不构成新的 medium 功能。
- `conda env update` 失败后改用工作区本地 `pip` 安装 `langgraph`，属于同一目标下的降级执行路径，不属于范围扩张。

### 8. 未解决问题

- 当前 trace 只是内存态 `trace_events` + hook，没有落盘，不具备真正可查询的 runtime tracing 能力。
- 当前 ask graph 只有一个真正的业务执行节点，图层价值主要体现在状态、ID 语义和 trace 钩子，离 checkpoint / interrupt / recovery 还很远。
- 当前代码保留了 `langgraph` 缺失时的兼容 runner；这能降低开发阻塞，但也可能掩盖某些环境其实没有走真实 LangGraph 语义。
- 插件侧没有展示 `run_id` / `thread_id`，也没有提供 resume/debug 入口。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果其他环境没有安装 `langgraph` 却依赖兼容 runner 通过了功能测试，后续可能会出现“本地没暴露、上线才暴露”的语义差异风险。
- 技术债：当前 tracing 只是 graph 内存态事件，既没有 JSONL / SQLite 存储，也没有字段演进规则和脱敏规范。
- 技术债：当前 ask graph 仍把 `run_minimal_ask()` 作为一个整体节点调用，检索、生成和引用校验还没有拆成更细粒度节点，因此 trace 粒度仍偏粗。
- 假设：下一次相关会话会在当前 `trace_hook` 基础上落 runtime trace 持久化，而不是重新推翻本轮 event 结构。

### 10. 下一步最优先任务

1. 绑定 `TASK-010`，把当前 ask graph 的内存态 `trace_events` 落到本地 JSONL runtime trace，形成最小可查询 tracing 骨架。
2. 继续保留 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中已有的轻量派生项，为 ask graph 与后续 ingest graph 收敛共享 state 字段。
3. 再之后评估 generated answer 的程序级 citation 对齐校验，避免 `AskWorkflowResult` 的 `generated_answer` 继续只靠 prompt 约束。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)
- [backend/app/graphs/state.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/state.py)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)
- [backend/pyproject.toml](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/pyproject.toml)

### 12. 当前最容易被面试官追问的点

- 你现在说“接入了 LangGraph”，但 ask graph 里真正的业务节点只有一个，检索和生成也没拆开，checkpoint 也没做；这到底是工程上必要的状态机骨架，还是只是给普通 API 外面套了一层框架名词。
- 你把 `thread_id` 和 `run_id` 接通了，但 trace 只在内存里，进程重启后什么都查不到；那你怎么证明这套 thread 语义真的支撑可恢复、可审计，而不是只停留在响应字段层面。
- 为什么你允许 `langgraph` 缺失时走兼容 runner；这是不是在掩盖环境治理不严的问题。你怎么保证 CI / 演示机 / 面试机不是跑在“伪 LangGraph”路径上。
- 你把 trace hook 设计成异常吞掉，这符合“观测不拖垮主链路”，但如果 trace 长期静默失败，你怎么发现，怎么告警，怎么证明观测数据没有长期断流。

## [SES-20260314-04] 跑通最小 ask 链路与引用式响应

- 日期：2026-03-14
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-008`
- 本会话唯一目标：在不扩展到 `ask_graph`、streaming、审批写回和完整 provider 子系统的前提下，把现有 FTS candidate 接进真实 `ask_qa` 返回链路，让 `/workflows/invoke` 可以返回最小引用式响应，并在模型不可用时显式降级为 retrieval-only

### 1. 本次目标

- 让 `/workflows/invoke` 的 `ask_qa` 不再返回 `not_implemented`，而是执行真实问答兜底链路。
- 复用 `TASK-007` 已落地的标准 candidate / metadata filter 结果，避免再定义第二套 ask 候选协议。
- 在模型不可用、provider 调用失败或没有检索命中时，明确返回可解释的降级结果，而不是伪造“已回答”。

### 2. 本次完成内容

- 确认 `TASK-008` 没有预分配 `session_id`，且 `SES-20260314-01` 到 `SES-20260314-03` 已被占用，因此为本次会话分配 `SES-20260314-04`。
- 更新 [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)，新增：
  - `AskResultMode`
  - `AskCitation`
  - `AskWorkflowResult`
  - `WorkflowInvokeRequest.retrieval_filter`
  - `WorkflowInvokeResponse.ask_result`
- 更新 [backend/app/config.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/config.py)，补齐 `KS_CLOUD_API_KEY` 的读取，并与 [backend/.env.example](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/.env.example) 中既有的变量样例保持一致，避免 ask 侧模型调用和配置说明脱节。
- 新增 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)，落地：
  - 基于 `search_chunks_in_db()` 的最小 ask 服务
  - `generated_answer` / `retrieval_only` / `no_hits` 三种返回模式
  - retrieval fallback 与 model fallback 分离表达
  - openai-compatible `chat/completions` 的最小 HTTP 调用
  - retrieval-only 文本组装与引用映射
- 更新 [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)，让 `/workflows/invoke`：
  - 对 `ask_qa` 返回 200 + `RunStatus.COMPLETED`
  - 对空 `user_query` 返回 400
  - 继续保持非 ask action 为 `not_implemented`
  - 让 `/health` 中 provider `enabled` 语义和 ask 实际可用条件保持一致
- 更新 [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)，同步 ask 结果、citation 和 retrieval filter 的类型定义，避免前后端 contract 漂移。
- 新增 [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)，覆盖：
  - 无 provider 时 retrieval-only fallback
  - provider 调用成功时 generated answer
  - metadata filter 过严时 retrieval fallback 信号
  - 空 query bad case

### 3. 本次未完成内容

- 没有实现 `ask_graph`、`thread_id` 贯通或 tracing 钩子，这仍属于 `TASK-009`。
- 没有实现 `/ask` 或 `/ask/stream` 独立端点；当前 ask 仍挂在 `/workflows/invoke`。
- 没有对模型输出做强制引用编号校验或 groundedness 二次校验；当前只做最小 prompt 约束和结构抽取。
- 没有验证真实云 provider 或本地 provider 的联网调用；模型成功分支目前只通过 mock 单测覆盖。
- 没有验证插件构建或 ask UI 展示；本次只同步了 TS contract。

### 4. 关键决策

- ask 先接在 [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py) 的 `ask_qa` 分支，而不是本轮直接新建 `ask_graph`，是为了严格遵守 `TASK-008` 的范围边界，把“先跑通最小可演示链路”和“再升级为 graph”拆成两次中等任务。
- 复用 [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py) 中已经稳定下来的 `RetrievedChunkCandidate` / `RetrievalSearchResponse`，而不是再定义 ask 专用 candidate，是为了避免协议刚收敛就二次分叉。
- retrieval fallback 与 model fallback 分开返回，是为了让上游明确知道“是过滤条件过严”还是“模型能力不可用”，避免所有降级都被混成一句“低置信”。
- 模型调用只实现 openai-compatible 的最小 HTTP 形态，而不是这轮顺手接一个完整 SDK，是因为当前依赖和任务边界都不支持把 provider 子系统扩成新的 medium 功能。
- `/health` 中 provider `enabled` 改成“base_url + model 至少具备其一”的组合条件，而不是只看 `base_url`，是为了防止健康检查把不可用 provider 误报成可用，削弱 ask fallback 的可解释性。

### 5. 修改过的文件

- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/app/contracts/__init__.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/__init__.py)
- [backend/app/config.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/config.py)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)
- [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)
- [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)
- [backend/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/README.md)

### 6. 验证与测试

- 跑了什么命令
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_workflow -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
  - `cd backend && PYTHONPYCACHEPREFIX=/tmp/ks-pycache ../.conda/knowledge-steward/bin/python -m compileall app tests`
  - `cd backend && ../.conda/knowledge-steward/bin/python - <<'PY' ... TestClient(main.app) ... /workflows/invoke ... PY`
- 结果如何
  - ask 专项测试 4 个用例全部通过，覆盖空 query、retrieval-only fallback、generated answer 分支和 retrieval fallback 信号。
  - 后端全量 `unittest` 12 个用例全部通过，没有回归 `TASK-005` / `TASK-006` / `TASK-007` 既有行为。
  - `compileall` 通过，没有语法错误。
  - `TestClient` 命令级验证成功返回 `200 / completed / retrieval_only / retrieval_fallback_used=True / model_fallback_reason=no_available_chat_provider`，说明 `/workflows/invoke` 的 ask 分支已经是可调用链路。
- 哪些没法验证
  - 没有真实联网验证 openai-compatible 或本地 provider，因此无法证明当前最小 HTTP 调用已在真实模型服务上稳定可用。
  - 没有跑插件构建；当前工作区没有 `plugin/node_modules`，因此未验证 TS contract 变更是否已通过前端构建。
  - 没有验证 generated answer 一定带合法引用编号；当前只验证模型成功分支可以返回内容，不验证引用格式约束。
- 哪些只是静态修改
  - [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
  - [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)
  - [backend/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/README.md)

### 7. 范围偏移与原因

- 无实质超范围。
- 唯一伴随改动是同步 [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md) 和 [backend/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/README.md) 的事实漂移，因为它们仍把 metadata filter 和 ask 引用式返回写成未完成；这属于本次收尾阶段的必要文档对齐，不构成新的 medium 功能。

### 8. 未解决问题

- 当前 generated answer 只靠 prompt 约束要求引用编号，没有程序级 citation 对齐校验。
- 当前 ask 仍是普通 API 分支，不具备 `TASK-009` 要求的 `thread_id` / state / tracing / checkpoint 语义。
- 当前 provider 调用只支持 openai-compatible 最小 HTTP 形态，没有更完整的错误分类、重试和 schema 校验。
- 插件侧还没有 ask 命令或引用渲染 UI，因此最小可演示能力当前主要停留在后端 API 层。

### 9. 新增风险 / 技术债 / 假设

- 风险：模型即使返回了文本，也可能没有严格按 `[1]`、`[2]` 引用候选片段；如果没有程序校验，前端很容易把“看起来像答案”的自由文本误当成 grounded answer。
- 技术债：当前 ask 生成路径使用标准库 `urllib` 做最小 HTTP 调用，缺少更细的超时、重试、错误码映射和流式能力。
- 技术债：当前 provider 可用性判断只做最小静态条件检查，没有真正的启动期探活或秘钥合法性校验。
- 假设：`TASK-009` 会在保留当前 `AskWorkflowResult` 语义的前提下，把 ask 迁移到 graph 入口，而不是重新推翻已有 API contract。

### 10. 下一步最优先任务

1. 绑定 `TASK-009`，把当前 ask 普通 API 链路升级为 `ask_graph` 骨架，并贯通 `thread_id`、state 与最小 tracing 钩子。
2. 作为轻量派生项，为 generated answer 增加引用编号和 groundedness 校验，避免模型输出与 `citations` 脱节。
3. 再之后评估是否需要独立 `/ask` 或 `/ask/stream`，以及插件侧 ask 交互入口。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)
- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)
- [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)

### 12. 当前最容易被面试官追问的点

- 你现在说“ask 跑通了”，但真实模型调用并没有联网验证，这到底是一个后端 contract 演示，还是一个真正稳定可用的问答链路；你怎么证明不是在包装 retrieval-only。
- 为什么 ask 先挂在 `/workflows/invoke`，而不是单独开 `/ask`；如果后面再接 `ask_graph`，你怎么避免 API 语义二次漂移。
- 为什么要把 retrieval fallback 和 model fallback 分开；如果两个降级同时发生，前端和用户到底该怎么理解结果置信度。
- 你让模型按引用编号回答，但代码里没有做 citation 对齐校验；如果模型输出了一个没有编号、或者编号和候选不对应的答案，系统为什么还敢标成 `generated_answer`。

## [SES-20260314-03] 实现 metadata filter 与 candidate 标准格式

- 日期：2026-03-14
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应主文档任务：`TASK-007`
- 本会话唯一目标：在不扩展到 `/ask`、hybrid retrieval、rerank、graph 和写回 proposal 的前提下，基于当前 SQLite FTS5 检索补齐 metadata filter、统一 candidate 标准格式，并为过滤过严时提供可恢复 fallback

### 1. 本次目标

- 在当前 FTS 查询之上支持 path、note_type、template_family、时间等基础 metadata 过滤条件。
- 将检索结果收敛成后续 answer generation 可直接复用的标准 candidate 结构。
- 为 filter 过严导致的空结果提供清晰可观测的 fallback，并补测试与命令级验证。

### 2. 本次完成内容

- 确认 `TASK-007` 没有预分配 `session_id`，且 `SES-20260314-01`、`SES-20260314-02` 已被占用，因此为本次会话分配新的 `SES-20260314-03`。
- 更新 [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)，新增：
  - `RetrievalMetadataFilter`
  - `RetrievedChunkCandidate`
  - `RetrievalSearchResponse`
- 更新 [backend/app/retrieval/sqlite_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_fts.py)，新增：
  - metadata filter 归一化与输入校验
  - 基于 `note` / `chunk` / `chunk_fts` JOIN 的 SQL 级过滤
  - `requested_filters` / `effective_filters` / `fallback_used` 返回语义
  - `path_prefix`、`note_type`、`template_family` 的 CLI 过滤参数
- 更新 [backend/tests/test_retrieval_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_retrieval_fts.py)，验证：
  - `note_type` + `template_family` 的过滤命中
  - `path_prefix` 过滤
  - 过滤过严时自动退回无 filter 的 FTS 查询
  - 标点噪声 query 归一化和空 query bad case
- 同步更新 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)、[docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 和 [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)，关闭 `TASK-007`，并修正文档中“FTS 已落地但检索层仍被写成未实现”的状态漂移。

### 3. 本次未完成内容

- 没有实现 hybrid retrieval、向量检索或 rerank。
- 没有把标准 candidate 结构接入 `/ask` 或 `/workflows/invoke`。
- 没有实现分级放宽 filter 的细粒度 fallback；当前只支持“整组 filter 失效时退回纯 FTS”。

### 4. 关键决策

- candidate 与 filter 协议落在 [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)，而不是继续沿用 retrieval 内部 dataclass，是为了让 `TASK-008` 直接复用返回结构，不再重复做一次协议映射。
- metadata filter 放在 SQL 查询阶段与 FTS 一起执行，而不是先取 top-k 再做 Python 侧过滤；这样可以避免 top-k 被提前截断后出现“看起来 filter 正确，实际上 recall 已经丢光”的假象。
- fallback 显式返回 `requested_filters` / `effective_filters` / `fallback_reason`，而不是悄悄放宽条件，是为了让后续 ask 链路和审计层能准确区分“严格命中”和“被动降级”。

### 5. 修改过的文件

- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/app/retrieval/sqlite_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_fts.py)
- [backend/tests/test_retrieval_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_retrieval_fts.py)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)

### 6. 验证与测试

- 跑了什么命令
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_retrieval_fts -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
  - `cd backend && PYTHONPYCACHEPREFIX=/tmp/ks-pycache python3 -m compileall app tests`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m app.indexing.ingest --db-path /tmp/knowledge-steward-task007.sqlite3`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m app.retrieval.sqlite_fts --db-path /tmp/knowledge-steward-task007.sqlite3 --query "总结" --note-type summary_note --limit 3`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m app.retrieval.sqlite_fts --db-path /tmp/knowledge-steward-task007.sqlite3 --query "总结" --note-type daily_note --limit 3`
- 结果如何
  - 检索专项测试 4 个用例全部通过。
  - 后端全量 `unittest` 8 个用例全部通过，没有回归 `TASK-005` / `TASK-006` 既有行为。
  - `compileall` 通过，没有语法错误。
  - 对 `sample_vault/` 的真实 ingest 成功写入 `205` 条 note、`1057` 条 chunk。
  - `summary_note` 过滤的 CLI 查询触发了 fallback，暴露出当前样本里部分“迭代总结”并没有稳定被 parser 归成 `summary_note`。
  - `daily_note` 过滤的 CLI 查询在真实数据上成功返回命中结果，说明 metadata filter 正向链路可用。
- 哪些没法验证
  - 还没有 `/ask` 引用式返回链路，因此无法验证 `RetrievedChunkCandidate` 是否已被上游 API 直接消费。
  - 还没有 hybrid/vector/rerank，因此无法验证 filter 与多路召回叠加时的 recall / precision 变化。
- 哪些只是静态修改
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)

### 7. 范围偏移与原因

- 无实质范围偏移。
- 唯一新增的是从真实 `sample_vault` 验证里暴露出的轻量派生项：`summary_note` 的模板识别不够稳定，会影响 `note_type` 过滤体验；这属于 parser 规则收敛，不构成新的 medium 功能。

### 8. 未解决问题

- 当前 fallback 是“整组 filter 失效后直接退回纯 FTS”，还不是按维度逐层放宽。
- `sample_vault/` 中部分“迭代总结”笔记没有被稳定识别为 `summary_note`，会让 `note_type` 过滤过早退化到 fallback。
- 还没有把 candidate 标准结构接入最小 ask 链路，因此真正的引用式响应尚未跑通。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果 `note_type` / `template_family` 识别继续依赖脆弱模板规则，metadata filter 的空结果与 fallback 频率会被语料噪声放大。
- 技术债：当前 fallback 是 all-or-nothing，可能在严格过滤失败后把召回面一下子放得过宽，后续需要更细的分层放宽策略。
- 假设：`TASK-008` 会直接消费 `RetrievedChunkCandidate` 和 `RetrievalSearchResponse`，而不是再定义第二套 ask 专用候选结构。

### 10. 下一步最优先任务

1. 绑定 `TASK-008`，把当前标准 candidate 结果接进最小 `/ask` 链路与引用式响应。
2. 在 ask 链路里利用 `fallback_used` / `fallback_reason` 输出低置信提示，避免用户把降级结果误认为强命中。
3. 作为轻量派生项，补抽样校正 `summary_note` 的模板识别规则，减少 `note_type` 过滤的误回退。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/app/retrieval/sqlite_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_fts.py)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/tests/test_retrieval_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_retrieval_fts.py)

### 12. 当前最容易被面试官追问的点

- 你为什么把 metadata filter 放进 SQL 查询，而不是先召回再过滤；如果 top-k 被提前截断导致 recall 丢失，你怎么证明不是你把问题藏起来了。
- 你为什么在 filter 失效时直接退回纯 FTS；这个降级边界为什么不是“只放宽一个维度”，你怎么控制误召回和可解释性。
- 你为什么把 candidate 协议提前放进 `workflow.py`；如果后续 ask 还要补引用字段、置信度或 rerank 分数，现有结构会不会再次推翻。
- 真实样本里“迭代总结”都没被稳定识别成 `summary_note`，那你现在的 metadata filter 到底是在过滤真实语义，还是在放大 parser 规则噪声。

## [SES-20260314-02] 实现 SQLite FTS5 检索

- 日期：2026-03-14
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`满足`
- 对应主文档任务：`TASK-006`
- 本会话唯一目标：在不扩展到 metadata filter、hybrid retrieval、答案生成和 graph 的前提下，基于已入库 `note/chunk` 数据落地最小 SQLite FTS5 检索，返回 top-k chunk candidate 与 snippet，并补最小 bad case 验证

### 1. 本次目标

- 为当前 SQLite `note/chunk` 数据补上最小可用的 FTS5 索引。
- 提供 query -> top-k chunk candidate -> snippet 的最小检索链路。
- 覆盖标题匹配、正文匹配和至少一个 bad case。

### 2. 本次完成内容

- 确认 `TASK-006` 没有预分配 `session_id`，且 `SES-20260314-01` 已被占用，因此为本次会话分配新的 `SES-20260314-02`。
- 更新 [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)，新增：
  - SQLite schema v2
  - `chunk_fts` FTS5 虚表
  - `rebuild_chunk_fts_index()`
- 更新 [backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py)，让全量 ingest 在写库完成后统一重建 FTS 索引，避免 note/chunk 与检索层漂移。
- 新增 [backend/app/retrieval/sqlite_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_fts.py)，提供：
  - 最小安全 query 归一化
  - `search_chunks()` / `search_chunks_in_db()`
  - `python -m app.retrieval.sqlite_fts` CLI
  - top-k chunk candidate 与 snippet 输出
- 新增 [backend/tests/test_retrieval_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_retrieval_fts.py)，验证：
  - 标题与正文的基本全文匹配
  - 标点噪声 query 归一化
  - 空 query bad case
- 更新 [backend/tests/test_indexing_store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_store.py) 与 [backend/tests/test_indexing_ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_ingest.py)，补充 `chunk_fts` schema 与 ingest 后 FTS 文档数对齐校验。
- 更新 [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)、[backend/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/README.md)、[docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 和 [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)，同步当前状态与最小检索命令。

### 3. 本次未完成内容

- 没有实现 metadata filter。
- 没有实现 hybrid retrieval、rerank 或答案生成。
- 没有实现 FTS 增量同步或漂移检测。

### 4. 关键决策

- 首版 FTS 采用独立 `chunk_fts` 虚表拍平 `title / heading_path / text`，而不是直接在查询时做多表全文拼装；这样可以先把 query 行为和结果结构稳定下来。
- ingest 结束后统一做整库 FTS 重建，而不是本次就接触发器或逐 note 增量同步；这样可以把“恢复检索可用状态”的路径压缩成一个明确入口。
- query 先做最小安全归一化，只保留可检索词项并降到 AND 匹配，优先避免 FTS MATCH 因标点噪声报语法错误。

### 5. 修改过的文件

- [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- [backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py)
- [backend/app/retrieval/__init__.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/__init__.py)
- [backend/app/retrieval/sqlite_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_fts.py)
- [backend/tests/test_indexing_store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_store.py)
- [backend/tests/test_indexing_ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_ingest.py)
- [backend/tests/test_retrieval_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_retrieval_fts.py)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)
- [backend/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/README.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)

### 6. 验证与测试

- 跑了什么命令
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m app.indexing.ingest --db-path /tmp/knowledge-steward-task006.sqlite3`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m app.retrieval.sqlite_fts --db-path /tmp/knowledge-steward-task006.sqlite3 --query "总结" --limit 3`
  - `cd backend && PYTHONPYCACHEPREFIX=/tmp/ks-pycache python3 -m compileall app tests`
- 结果如何
  - `unittest` 6 个用例全部通过。
  - 对 `sample_vault/` 的真实 ingest 成功写入 `205` 条 note、`1057` 条 chunk，并同步生成 FTS 文档。
  - FTS CLI 对 `总结` 查询成功返回 top-3 chunk candidate，结果包含 `path / chunk_id / score / snippet`。
  - `compileall` 通过，没有语法错误。
- 哪些没法验证
  - 还没有 metadata filter，因此没有验证 path / note_type 等结构化过滤。
  - 还没有 ask 链路，因此没有验证检索结果是否已满足最终答案生成。
- 哪些只是静态修改
  - [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)
  - [backend/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/README.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)

### 7. 范围偏移与原因

- 无实质范围偏移。
- 唯一伴随改动是把 ingest 补成“写库后重建 FTS”的同步点，并同步 README/主计划状态；这仍属于 `TASK-006` 的必要适配，没有扩成新的 medium 功能。

### 8. 未解决问题

- 当前 FTS 同步仍是整库重建，不是增量更新。
- query 归一化只做了最小词项抽取，对复杂中文分词、前缀匹配和高级布尔语法都没有专门支持。
- 当前返回结构足够支撑 `TASK-006`，但还不是 `TASK-007` 要求的 candidate 标准格式。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果后续 Vault 规模明显变大，整库重建 `chunk_fts` 的 IO 成本会快速上升。
- 技术债：当前没有显式的 FTS 漂移检测，只是把“写库后立即重建”作为同步策略。
- 假设：`TASK-007` 会在当前 `ChunkSearchHit` 基础上收敛 candidate 标准格式，而不是再推翻 top-k 返回字段。

### 10. 下一步最优先任务

1. 绑定 `TASK-007`，在当前 FTS 结果上补 path / note_type / template_family 等基础 metadata filter。
2. 为 filter 过严时设计 fallback，避免 ask 链路一上来就被空候选卡死。
3. 之后再进入 `TASK-008`，把检索结果接进最小引用式响应。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/retrieval/sqlite_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_fts.py)
- [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- [backend/tests/test_retrieval_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_retrieval_fts.py)

### 12. 当前最容易被面试官追问的点

- 你为什么选择整库重建 `chunk_fts`，而不是触发器同步或按 note 增量刷新；这个决策的恢复成本和性能上限是什么。
- 你为什么把 `title / heading_path / text` 拍平成独立 FTS 文档，而不是直接在 `chunk` 上做全文索引；这对 schema 演进和 query 成本有什么影响。
- 你为什么在首版 query 里主动屏蔽复杂 FTS 语法；这到底是在做安全兜底，还是在牺牲可表达性掩盖问题。
- 如果中文查询词切分不好、query 全是符号、或 note 标题变化但 FTS 没重建，当前系统分别会怎么退化、怎么恢复。

## [SES-20260314-01] 实现最小 ingest pipeline 并写入 SQLite

- 日期：2026-03-14
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`满足`
- 对应主文档任务：`TASK-005`
- 本会话唯一目标：在不扩展到 FTS、metadata filter、ask 和 graph 的前提下，打通 `sample_vault/` 的最小全量 ingest 链路，把 parser 结果稳定写入 SQLite，并保证重复执行不会产生明显脏重复

### 1. 本次目标

- 为当前已落地的 `note/chunk` schema 接上真实写库入口。
- 提供对 `sample_vault/` 的最小全量 ingest 命令。
- 处理重复执行时的幂等覆盖和旧 chunk 清理。

### 2. 本次完成内容

- 确认 `TASK-005` 没有预分配 `session_id`，且 `docs/TASK_QUEUE.md` 与本文件中不存在已占用的 `SES-20260314-XX`，因此为本次会话分配 `SES-20260314-01`。
- 更新 [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)，新增：
  - `upsert_note()`
  - `replace_chunks_for_note()`
  - `sync_note_and_chunks()`
  - `NoteSyncResult`
- 新增 [backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py)，提供：
  - `sample_vault/` 的 Markdown 全量遍历
  - `parse -> build record -> sync note/chunks` 的最小 ingest 编排
  - `python -m app.indexing.ingest` CLI
  - 最小 ingest 统计输出
- 新增 [backend/tests/test_indexing_ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_ingest.py)，验证：
  - 首次 ingest 会真实写入 `note/chunk`
  - 重复执行不会产生重复行
  - note 内容变化后旧 chunk 会被替换，不会残留脏数据
- 更新 [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md) 与 [backend/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/README.md)，补齐 ingest 基线与 CLI 用法。
- 同步更新 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 与 [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)，关闭 `TASK-005` 并修正文档里“ingest 待开始”的状态漂移。

### 3. 本次未完成内容

- 没有实现删除文件后的 note 清理。
- 没有实现增量扫描、dirty mark 或变更窗口优化。
- 没有实现 FTS5、metadata filter、ask 或 graph 接入。

### 4. 关键决策

- 首版 ingest 采用“按 note 做整 note replace”的事务边界，而不是现在就做 chunk 级 diff/upsert；这样可以优先解决标题重排、段落缩减后的旧 chunk 残留问题。
- CLI 默认直接吃 `sample_vault_dir` 和 `index_db_path` 配置，避免在 `TASK-005` 阶段引入新的服务层或 API 入口。
- ingest 统计先聚焦 `scanned/created/updated/current_chunk_count/replaced_chunk_count`，先把可验证性和可讲述性补齐，不提前扩成完整审计日志。

### 5. 修改过的文件

- [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- [backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py)
- [backend/tests/test_indexing_ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_ingest.py)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)
- [backend/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/README.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)

### 6. 验证与测试

- 跑了什么命令
  - `cd backend && ../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m app.indexing.ingest --db-path /tmp/knowledge-steward-task005.sqlite3`
  - `cd backend && sqlite3 /tmp/knowledge-steward-task005.sqlite3 "SELECT 'note', COUNT(*) FROM note UNION ALL SELECT 'chunk', COUNT(*) FROM chunk;"`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m app.indexing.ingest --db-path /tmp/knowledge-steward-task005.sqlite3`
  - `cd backend && PYTHONPYCACHEPREFIX=/tmp/ks-pycache python3 -m compileall app tests`
- 结果如何
  - `unittest` 4 个用例全部通过。
  - 首次真实 ingest 成功写入 `205` 条 note 和 `1057` 条 chunk。
  - 第二次对同一数据库重复执行后，note/chunk 总数保持不变，CLI 返回 `0 created / 205 updated / 1057 old chunks replaced`，说明重复执行没有产生脏重复。
  - `compileall` 通过，没有语法错误。
- 哪些没法验证
  - 还没有删除文件同步逻辑，因此本次没有验证“文件从 Vault 消失后索引是否自动回收”。
  - 还没有 FTS5 和 retrieval API，因此本次无法验证 ingest 结果能否直接被检索层消费。
- 哪些只是静态修改
  - [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)
  - [backend/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/README.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)

### 7. 范围偏移与原因

- 无实质范围偏移。
- 唯一伴随改动是为 CLI 增加最小 ingest 统计输出，并同步 README/主计划状态；这属于 `TASK-005` 已登记的轻量派生项，没有扩成新任务。

### 8. 未解决问题

- 当前 full ingest 不会删除数据库里已经不存在于 Vault 的 note。
- `sample_vault` 的遍历逻辑目前在 `services/sample_vault.py` 和 `indexing/ingest.py` 各有一份，后续如果目录扫描规则变复杂，需要考虑抽公共入口。
- `updated_notes` 当前表示“本次覆盖写入了已有 note”，并不区分内容真的变化还是重复写入同样内容。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果后续直接做多 Vault 或子目录定向 ingest，而仍然沿用当前 full ingest 语义，可能需要额外 source scope 信息来避免误删或误判“缺失 note”。
- 技术债：当前幂等是“结果不重复”，不是“无变更时零写入”；后续如果要控制大 Vault 的 IO 成本，需要补更细的变更检测。
- 假设：`TASK-006` 会直接复用当前 `note/chunk` 表和 ingest 产物，而不是再引入第二套检索前置存储。

### 10. 下一步最优先任务

1. 绑定 `TASK-006`，基于当前 `note/chunk` 数据接入 SQLite FTS5 检索。
2. 在 `TASK-006` 内先返回最小 top-k candidate 和 snippet，不提前混入 metadata filter。
3. 之后进入 `TASK-007`，在 FTS 结果上补 path / note_type / template_family 等基础过滤与 fallback。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py)
- [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- [backend/tests/test_indexing_ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_ingest.py)

### 12. 当前最容易被面试官追问的点

- 你为什么在 `TASK-005` 选择 note 级 replace，而不是 chunk 级 diff/upsert；这个选择牺牲了什么、换来了什么。
- 你怎么定义“重复执行不会产生明显脏重复”；为什么第二次 ingest 仍然记成 `205 updated`，这和增量索引有什么本质差异。
- 如果文件被删除了、或者只 ingest 某个子目录，当前方案会不会留下脏 note；为什么你在这个阶段没有解决它。
- 你为什么把 ingest 入口做成 `python -m app.indexing.ingest`，而不是直接挂进 FastAPI 或 LangGraph；你的模块边界依据是什么。

## [SES-20260312-04] 设计并落地 `note/chunk` SQLite schema

- 日期：2026-03-12
- 类型：`Feature`
- 状态：`已完成`
- 验收结论：`满足`
- 对应主文档任务：`TASK-004`
- 本会话唯一目标：在不扩展到 ingest、FTS 和 ask 的前提下，落地与当前 parser 输出对齐的 `note/chunk` SQLite schema，并提供最小初始化或迁移入口

### 1. 本次目标

- 为后续 `TASK-005` 和 `TASK-006` 提供稳定的 SQLite 存储骨架。
- 明确 `note` / `chunk` 表的核心字段、索引和约束。
- 给出可执行的初始化入口，并验证它能真正建表。

### 2. 本次完成内容

- 确认 `TASK-004` 没有预分配 `session_id`，因此为本次会话分配新的 `SES-20260312-04`。
- 新增 [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)，落地以下内容：
  - `SCHEMA_VERSION=1` 的 SQLite migration 骨架
  - `note` / `chunk` 两张基础表
  - 围绕 `path`、`content_hash`、`heading_path`、`chunk_type` 的关键索引和约束
  - `build_note_record()` / `build_chunk_records()`，把当前 parser 输出映射到持久化记录
  - `python -m app.indexing.store` 初始化入口
- 更新 [backend/app/config.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/config.py)，新增 `KS_INDEX_DB_PATH` / `index_db_path`，把 SQLite 文件路径显式化。
- 新增 [backend/tests/test_indexing_store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_store.py)，验证：
  - 表结构与索引创建成功
  - `PRAGMA user_version` 与当前 schema 版本一致
  - `ParsedNote` / `NoteChunk` 可映射到新 schema 需要的关键字段
- 更新 [backend/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/README.md)，补充 SQLite schema 初始化命令。
- 同步更新 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 与 [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)，关闭 `TASK-004` 并修正“schema 尚未开始”的状态漂移。

### 3. 本次未完成内容

- 没有实现 `upsert note/chunk` 的写库流程。
- 没有实现 FTS5 虚表、query API 或 metadata filter。
- 没有把 schema 初始化自动挂到应用启动流程中。

### 4. 关键决策

- 本会话只落存储骨架，不实现 ingest/upsert，避免把 `TASK-004` 扩成 `TASK-005`。
- `tags`、`aliases`、`out_links` 首版先落 JSON 文本列，而不是现在就拆关联表；这能先保住 SQLite 单文件分发和最小 schema 复杂度。
- 迁移版本先用 SQLite 自带的 `PRAGMA user_version`，避免在 schema 任务里过早引入额外 migration framework。
- `content_hash` 与 `source_mtime_ns` 同时保留：前者服务幂等和变更识别，后者服务后续增量索引窗口判断。

### 5. 修改过的文件

- [backend/app/config.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/config.py)
- [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- [backend/tests/test_indexing_store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_store.py)
- [backend/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/README.md)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)

### 6. 验证与测试

- 跑了什么命令
  - `cd backend && python3 -m unittest discover -s tests -v`
  - `cd backend && python3 -m app.indexing.store --db-path /tmp/knowledge-steward-task004.sqlite3`
  - `python3 -m compileall backend/app backend/tests`
- 结果如何
  - 两个 `unittest` 全部通过。
  - CLI 初始化入口可真实创建 SQLite 文件和 schema。
  - `compileall` 通过，没有语法或导入错误。
- 哪些没法验证
  - 还没有可用的 ingest 入口，因此本次无法验证真实写库后的幂等行为和删除清理逻辑。
  - 还没有 FTS5 或检索 API，因此本次无法验证 retrieval 层是否能直接复用当前 schema。
- 哪些只是静态修改
  - [backend/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/README.md)
  - [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  - [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
  - [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)

### 7. 范围偏移与原因

- 无实质范围偏移。
- 唯一伴随修正是移除 `app.indexing.__init__` 对 `store` 的包级重导出，避免 `python -m app.indexing.store` 触发 `runpy` warning；这属于初始化入口的最小接口修正，没有扩成新任务。

### 8. 未解决问题

- `tags`、`aliases` 当前只在 schema 中预留列，真实填充值仍依赖后续 frontmatter / inline tag 解析。
- `chunk` 表已预留 `parent_chunk_id`，但当前 parser 还没有真正产出 `section_parent` / `section_child` 的 parent-child 关系。
- 还没有 `note/chunk` 的 upsert 或删除清理逻辑，因此数据库幂等写入与脏数据回收仍未解决。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果 `chunk_id` 继续只依赖路径和行号，当标题重排或大段改写时，后续增量索引会出现大量“看似删除再新增”的漂移。
- 技术债：当前 `tags_json` / `aliases_json` 先落单列，后续如果过滤需求快速增长，可能要补关联表或 FTS 辅助列。
- 假设：`TASK-005` 会复用当前 `NoteRecord` / `ChunkRecord` 映射，而不是重新定义一套平行的数据结构。

### 10. 下一步最优先任务

1. 绑定 `TASK-005`，实现 ingest pipeline，把 parser 结果真正写入 SQLite。
2. 在 `TASK-005` 内处理重复执行的幂等问题、旧 chunk 清理和最小统计输出。
3. 之后进入 `TASK-006`，基于当前 schema 接入 SQLite FTS5 检索。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- [backend/app/indexing/parser.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/parser.py)
- [backend/tests/test_indexing_store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_indexing_store.py)

### 12. 当前最容易被面试官追问的点

- 你为什么在 schema 阶段选择 `PRAGMA user_version`，而不是直接上 Alembic 或更完整的 migration 框架。
- 你为什么把 `tags` / `aliases` 先存成 JSON 文本列，这会不会给后续 filter 和索引带来隐患。
- `content_hash` 和 `source_mtime_ns` 同时保留的价值分别是什么，删掉一个会丢什么能力。
- 为什么 `TASK-004` 只做到 schema，不把 ingest 和 FTS 一次做完；你的 scope 控制依据是什么。

## [SES-20260312-03] 完成统一启动入口的真实运行验证

- 日期：2026-03-12
- 类型：`Infra`
- 状态：`已完成`
- 验收结论：`满足`
- 对应主文档任务：`TASK-003`
- 本会话唯一目标：补完 `python -m app.main` 的真实启动与 `/health` 命中验证，确认当前唯一推荐环境和统一启动入口确实可复现，并据此决定 `TASK-003` 是否可转为 `completed`

### 1. 本次目标

- 在当前推荐的工作区本地 conda prefix 下，补跑统一后端入口。
- 命中 `/health`，确认返回 contract 与 `sample_vault` 统计。
- 只同步与本次验证直接相关的任务状态和文档事实，不扩展到新的 `medium` 任务。

### 2. 本次完成内容

- 确认本次新会话不能复用已被占用的 `SES-20260312-02`，因此为 `TASK-003` 分配新的 `session_id`：`SES-20260312-03`。
- 在提权环境中使用当前推荐命令成功启动后端：
  - `cd backend && ../.conda/knowledge-steward/bin/python -m app.main`
- 使用同一运行边界下的 `curl` 命中 `/health` 并拿到 `200 OK`，确认以下事实：
  - `service_name=knowledge-steward-backend`
  - `model_strategy=cloud_primary_local_compatible`
  - `supported_actions` 包含 `ask_qa`、`ingest_steward`、`daily_digest`
  - `sample_vault` 当前返回 `205` 篇笔记、`50` 处 wikilink、`473` 个任务复选框
- 同步更新 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)，将 `TASK-003` 标记为 `completed`。
- 同步更新 [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)，修正“统一入口未完全验收”和 `sample_vault` 旧统计值的文档漂移。
- 按用户新增约束，继续更新 [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)，在“后续维护规则”中补入“后续代码开发必须增加必要的中文注释”的项目级要求，并明确注释应聚焦状态流转、边界条件、降级/恢复逻辑与复杂策略解释。

### 3. 关键决策

- `TASK-003` 的验收边界仍然限定在“环境路线 + 启动入口 + 最小运行验证”，不借此推进插件联调、索引或 graph 功能。
- 真实运行验证必须和启动命令处于同一网络边界；沙箱内 `curl` 打不到提权进程，不应误判为应用启动失败。
- 当前唯一推荐环境仍然是工作区本地 conda prefix，`backend/.venv` 继续保留为历史痕迹而非标准入口。

### 4. 修改过的文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)

### 5. 验证与测试

- 跑了什么命令
  - `./.conda/knowledge-steward/bin/python -V`
  - `./.conda/knowledge-steward/bin/python -c 'import fastapi, uvicorn, pydantic; ...'`
  - `cd backend && ../.conda/knowledge-steward/bin/python -c 'from app.main import app, main, settings; ...'`
  - `cd backend && ../.conda/knowledge-steward/bin/python -m app.main`
  - `curl -sS http://127.0.0.1:8787/health`
- 结果如何
  - 沙箱内直接启动仍报 `Operation not permitted`，问题来自端口 / watcher 权限边界，而不是代码导入失败。
  - 提权后 `watchfiles + uvicorn` 成功启动。
  - `/health` 返回 `200 OK`，统一入口的真实运行验证完成。
- 哪些没做
  - 没有补做插件 dev 模式与新后端入口的实际联调。
  - 没有把联合启动封装成脚本。

### 6. 范围偏移与原因

- 存在轻微范围偏移：按用户新增约束，在主文档中补入“后续代码开发必须增加必要的中文注释”的项目级维护规则。
- 该偏移属于 `small` 级文档治理改动，没有超出 `TASK-003` 的 `medium` 边界，也不需要拆分为下一会话。

### 7. 未解决问题

- 插件 dev 模式与新后端入口的实际联调还没有在本地 GUI / Obsidian 环境中补做。
- `backend/environment.yml` 与 `backend/pyproject.toml` 仍是双份依赖描述，后续需要继续防漂移。

### 8. 新增风险 / 技术债 / 假设

- 风险：如果后续只看旧文档统计而不再以运行结果为准，`sample_vault` 指标会继续漂移。
- 技术债：当前运行验证依赖提权环境；如果后续要做自动化 CI 验证，需要补一个不依赖本地端口绑定的 contract 测试路径。
- 假设：下一次进入 `TASK-004` 时，环境与统一入口不再是主阻塞项。

### 9. 下一步最优先任务

1. 绑定 `TASK-004`，设计并落地 `note/chunk` 的 SQLite schema。
2. 如需补小项，在允许本地 GUI / Obsidian 的环境中补做插件 dev 模式与新后端入口联调记录。
3. 后续再进入 `TASK-005` 与 `TASK-006`，把 ingest 与 FTS 检索接进当前骨架。

### 10. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [backend/app/indexing/models.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/models.py)
- [backend/app/indexing/parser.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/parser.py)

### 11. 当前最容易被面试官追问的点

- 你为什么坚持要做一次真实 `python -m app.main` 启动验证，而不是只用 `TestClient` 或导入检查。
- 为什么 `sample_vault` 的任务复选框统计从文档中的 `449` 变成了运行结果里的 `473`，你如何防止这类事实漂移。
- 你怎么区分“沙箱权限问题”和“应用启动失败”，避免把环境问题误报成代码问题。

## [SES-20260312-02] 收敛 Python 开发环境与统一启动入口

- 日期：2026-03-12
- 类型：`Infra`
- 状态：`部分完成`
- 验收结论：`部分满足`
- 对应主文档任务：`TASK-003`
- 本会话唯一目标：在 `backend/.venv` 与工作区 conda 并存的现状下，明确唯一推荐开发环境、统一启动命令，并消除 README 与真实运行方式不一致的问题

### 1. 本次目标

- 明确当前唯一推荐的 Python 开发环境路线。
- 统一根 README 与 `backend/README.md` 的后端启动命令。
- 给出最小验证命令，并判断当前是否能把 `TASK-003` 记为完成。

### 2. 本次完成内容

- 确认当前真实依赖环境是工作区本地 conda prefix：`./.conda/knowledge-steward`。
- 确认 `backend/.venv` 当前只是历史残留：
  - `backend/.venv/bin/python -m pip show fastapi uvicorn pydantic` 未找到依赖。
  - `.conda/knowledge-steward` 中可见 `fastapi`、`uvicorn`、`pydantic` 已安装。
- 新增 [backend/environment.yml](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/environment.yml)，把当前推荐开发环境显式化。
- 更新 [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)，新增 `python -m app.main` 统一启动入口。
- 更新 [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md) 与 [backend/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/README.md)：
  - 收敛为同一条 conda 路线。
  - 收敛为同一条后端启动命令。
  - 补充最小验证命令。
  - 明确 `backend/.venv` 不再作为推荐入口。
- 同步更新 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 与 [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)，使任务状态和主文档描述与当前代码一致。
- 在 [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 的“面试问答库”前新增统一角色设定，明确所有面试相关输出默认使用“大厂资深大模型应用工程师兼高级面试官”视角。

### 3. 本次未完成内容

- 没有完成 `python -m app.main` 的非沙箱真机验证，因此未把 `TASK-003` 直接记为 `completed`。
- 没有完成插件 dev 模式与新后端入口的联调验证。
- 没有补自动化脚本化的双终端联合启动。

### 4. 关键决策

- 唯一推荐环境路线收敛为工作区本地 conda prefix：`./.conda/knowledge-steward`。
- `backend/environment.yml` 作为当前推荐开发环境的显式清单。
- `python -m app.main` 作为当前统一后端启动入口。
- `backend/.venv` 保留为历史痕迹，不删除，但不再作为 README、验收或调试时的默认入口。
- 在无法完成真机启动验证的情况下，不把“文档已统一”误写成“任务已完全验收”。

### 5. 修改过的文件

- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)
- [backend/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/README.md)
- [backend/environment.yml](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/environment.yml)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)

### 6. 验证与测试

- 跑了什么命令
  - `backend/.venv/bin/python -m pip show fastapi uvicorn pydantic`
  - `.conda/knowledge-steward/bin/python -V`
  - `.conda/knowledge-steward/bin/python -c 'import fastapi, uvicorn, pydantic; ...'`
  - `cd backend && ../.conda/knowledge-steward/bin/python -c 'from app.main import app; ...'`
  - `python3 -m compileall backend/app`
  - `cd backend && ../.conda/knowledge-steward/bin/python -c 'from app.main import app, main, settings; ...'`
- 结果如何
  - 已确认 `.venv` 中缺少后端核心依赖。
  - 已确认 `.conda/knowledge-steward` 中存在当前后端所需依赖。
  - 已确认新增的 `main()` 入口可被导入，`app.title`、`settings.host`、`settings.port` 均可读取。
  - `python3 -m compileall backend/app` 通过。
- 哪些没法验证
  - `python -m app.main` 的真实 dev server 启动与 `/health` HTTP 访问未完成验证。
  - 原因 1：沙箱内绑定 `127.0.0.1:8787` 报 `operation not permitted`。
  - 原因 2：尝试按规则提权启动时，用户中断了该次验证。
- 哪些只是静态修改
  - `README.md`、`backend/README.md`、`backend/environment.yml`、`docs/TASK_QUEUE.md`、`docs/PROJECT_MASTER_PLAN.md`、本文件。

### 7. 范围偏移与原因

- 无实质范围偏移。
- 本会话仍然围绕 `TASK-003`，伴随改动只包括统一启动入口、环境定义文件与必要文档同步。

### 8. 未解决问题

- `python -m app.main` 尚未在非沙箱环境完成一次真正启动与 `/health` 命中验证。
- 插件 dev 模式与新后端入口的联合启动顺序虽已写入 README，但还未实际联调。
- `backend/.env.example` 目前仍只是变量清单，当前基线没有自动加载 `.env` 文件。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果后续有人继续用 `backend/.venv` 本地调试，环境漂移会再次出现。
- 技术债：`backend/environment.yml` 与 `backend/pyproject.toml` 现在形成双份依赖描述，后续必须一起维护。
- 假设：后续允许在非沙箱环境或提权环境中补一次真实 dev server 验证。

### 10. 下一步最优先任务

1. 先在允许本地端口绑定的环境中补跑 `python -m app.main` 与 `/health`，决定 `TASK-003` 是否可转为 `completed`。
2. 完成后绑定 `TASK-004`，设计并落地 `note/chunk` 的 SQLite schema。
3. 再进入 `TASK-005` 与 `TASK-006`，把 ingest 与 FTS 检索接进当前骨架。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)
- [backend/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/README.md)
- [backend/environment.yml](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/environment.yml)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)

### 12. 当前最容易被面试官追问的点

- 你为什么最终选择工作区本地 conda prefix，而不是继续保留 `backend/.venv` 作为标准入口。
- 你为什么要新增 `backend/environment.yml`，这会不会和 `pyproject.toml` 重复维护。
- 你怎么证明“环境已经收敛”，而不是只把文档改一致了。
- 如果线上或演示机上端口绑定失败、watchfiles 失效、conda 环境漂移，你怎么降级、怎么定位、怎么恢复。

## [SES-20260312-01] 重构会话级任务队列到独立 TASK_QUEUE

- 日期：2026-03-12
- 类型：`Docs`
- 状态：`已完成`
- 对应主文档任务：`TASK-002`
- 本会话唯一目标：将原本耦合在 `docs/PROJECT_MASTER_PLAN.md` 中的会话级任务明细迁移到独立文件 `docs/TASK_QUEUE.md`

### 1. 本次目标

- 新建稳定的会话级任务队列文件。
- 让主文档回到“架构主文档”定位，不再直接承载任务明细。
- 统一后续会话的绑定规则，使新会话必须先绑定 `TASK_QUEUE.md` 中的一个任务。

### 2. 本次完成内容

- 新建 [TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)。
- 将原 `docs/PROJECT_MASTER_PLAN.md` 第 10.5 节中的会话任务明细迁移到新文件。
- 为任务队列补充稳定字段：
  - `task_id`
  - `session_id`
  - `title`
  - `category`
  - `priority`
  - `status`
  - `scope`
  - `goal`
  - `out_of_scope`
  - `acceptance_criteria`
  - `depends_on`
  - `related_files`
  - `derived_tasks`
  - `notes`
- 更新 [PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)：
  - 升级到 `v0.2.5`
  - 移除具体会话任务表
  - 新增“队列已迁移到 `docs/TASK_QUEUE.md`”的说明
  - 将所有原指向第 10.5 节的引用改为 `docs/TASK_QUEUE.md`
- 更新本文件，使 `SES-20260312-01` 与 `TASK-002` 对齐。

### 3. 关键决策

- `docs/TASK_QUEUE.md` 现在是会话级任务的唯一来源。
- `docs/PROJECT_MASTER_PLAN.md` 继续作为架构、路线图、ADR 和风险主文档，不再承担具体队列职责。
- 后续默认规则保持不变：一个会话只解决一个 `scope=medium` 的任务项。

### 4. 修改过的文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)

### 5. 验证与测试

- 主要验证方式：文档结构检查和交叉引用检查。
- 已检查：
  - `PROJECT_MASTER_PLAN.md` 中不再保留具体会话任务明细
  - 原先“绑定第 10.5 节任务”的表述已改为绑定 `docs/TASK_QUEUE.md`
  - `TASK_QUEUE.md` 中已保留历史启动任务和后续 planned 任务
- 未做：
  - 没有代码运行测试，因为本会话只处理文档结构

### 6. 未解决问题

- 任务状态枚举当前使用英文：`planned / in_progress / blocked / completed / cancelled`，是否长期保留还未定。
- 当前队列中的 planned 任务主要来自原 10.5 节，后续可能需要继续扩展插件 Dev Vault 验证、audit_log、resume_workflow 等任务。

### 7. 新增风险 / 技术债 / 假设

- 风险：如果后续只更新 `PROJECT_MASTER_PLAN.md` 而忘记同步 `TASK_QUEUE.md`，任务状态会重新分叉。
- 技术债：`SESSION_LOG.md` 当前仍同时承担“会话摘要”和“规则提示”职责，后续可能还要继续瘦身。
- 假设：后续会话确实会严格按 `scope=medium` 执行，不会把 `small` 任务单独拉成一轮会话。

### 8. 下一步最优先任务

1. 绑定 `TASK-003`，收敛 Python 开发环境与统一启动入口。
2. 完成后再进入 `TASK-004`，设计并落地 `note/chunk` SQLite schema。
3. 队列新增任务时，优先保持“可一次会话闭环”的中等粒度。

### 9. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)
- [backend/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/README.md)

### 10. 当前最容易被面试官追问的点

- 为什么要把任务队列从主文档拆出去，和“架构文档单一事实来源”是否矛盾。
- 为什么一个会话只允许绑定一个 `scope=medium` 任务，这个约束如何提高工程可控性。
- 为什么 `TASK_QUEUE.md` 要有 `out_of_scope` 和 `acceptance_criteria` 这类字段。
- 为什么历史启动会话允许保留 `scope=large` 例外，而后续不再允许。

## [SES-20260311-01] 启动会话：主文档、双端基线、解析器与参考实现对照

- 日期：2026-03-11
- 类型：`Bootstrap Exception`
- 状态：`已完成`
- 说明：这是项目启动会话，范围大于后续“单会话单中等粒度问题”的常规规则。后续会话应收敛为单问题推进。

### 1. 本次目标

- 基于当前仓库、实现指南、`sample_vault/` 和项目目标，建立项目单一事实来源文档。
- 将仓库从“只有设计输入的空仓”推进到“可开发、可验证的双端基线”。
- 锁定架构方向、模型路线，并为后续索引、检索、LangGraph 工作流和 HITL 写回预留稳定落点。

### 2. 本次完成内容

- 创建并持续更新主文档 [PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)，当前版本已到 `v0.2.4`。
- 新增 [SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md) 的唯一会话 ID 规范，并把后续实现任务切换为“一个会话一个中等粒度问题”的推进方式。
- 建立仓库基线：
  - 后端基线：FastAPI 入口、`/health`、`/workflows/invoke`、协议模型、状态 schema、样本统计服务。
  - 插件基线：Obsidian 插件入口、设置页、侧边栏 view、后端探活客户端。
  - 评估基线：`eval/README.md`、`eval/golden/`、`eval/results/`。
- 新增首版 Markdown 解析器，已支持 heading/path 解析、wikilink 提取、task checkbox 计数、`daily_note / summary_note / generic_note` 推断、模板分类。
- 分析 `sample_vault/`：
  - 共 205 篇笔记
  - 基本无 frontmatter
  - 约 50 处 wikilink
  - 约 449 个任务复选框
  - 以中英两套日记模板为主，夹杂少量迭代总结/复盘总结
- 拉取只读参考仓库 `references/ObsidianRAG/`，完成对照分析，明确可借鉴点与不应照搬点。
- 完成最小验证：
  - `python3 -m compileall backend/app` 通过
  - 用工作区 conda 环境验证 `/health` 与 `/workflows/invoke`
  - `/health` 已返回 `sample_vault` 统计与 `cloud_primary_local_compatible`

### 3. 关键决策

- 架构确认：`Obsidian 插件 + Python FastAPI 本地后端` 双端架构。
- 模型路线确认：架构兼容云与本地，实现优先级为“云优先，本地作为后续 fallback / 质量基线”。
- 主叙事确认：项目主价值是“知识治理 + 有状态工作流 + 审批写回 + 审计评估”，不是普通聊天/RAG 插件。
- 写回边界确认：后端生成 proposal/patch，插件执行最终写回；不允许 LLM 直接改 Vault 文件。
- 参考仓库策略确认：`ObsidianRAG` 只做参考实现，不直接 fork 或并入主代码。

### 4. 修改过的文件

#### 文档

- [PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)

#### 仓库基线

- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)
- [.gitignore](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/.gitignore)
- [backend/pyproject.toml](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/pyproject.toml)
- [backend/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/README.md)
- [backend/.env.example](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/.env.example)

#### 后端核心

- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/app/config.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/config.py)
- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/app/graphs/state.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/state.py)
- [backend/app/services/sample_vault.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/sample_vault.py)
- [backend/app/indexing/models.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/models.py)
- [backend/app/indexing/parser.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/parser.py)

#### 插件基线

- [plugin/package.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/package.json)
- [plugin/manifest.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/manifest.json)
- [plugin/tsconfig.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/tsconfig.json)
- [plugin/esbuild.config.mjs](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/esbuild.config.mjs)
- [plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts)
- [plugin/src/api/client.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/api/client.ts)
- [plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts)
- [plugin/src/settings.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/settings.ts)
- [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)
- [plugin/styles.css](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/styles.css)

#### 评估与参考

- [eval/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/README.md)
- [references/ObsidianRAG](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/references/ObsidianRAG)

#### 说明

- `sample_vault/` 是本次会话的重要输入样本，由用户提供，不是我生成的业务代码。
- 工作区中还存在 `.conda/knowledge-steward` 与 `backend/.venv` 两套 Python 环境痕迹，尚未收敛。

### 5. 未解决问题

- 还没有真正的 `note/chunk` 持久化、SQLite FTS5、embedding 存储和 hybrid retrieval。
- `ask / ingest / digest` graph 只有 `StewardState` 和占位入口，没有真正节点实现。
- 插件与后端的联通只验证到了探活和占位接口，尚未在真实 Obsidian Dev Vault 中完整走通审批/写回链路。
- 还没有 `proposal schema`、`patch_ops schema`、`audit_log`、`resume_workflow` 真正进入运行链路。
- 还没有 golden set 内容、`eval/run_eval.py`、trace/audit 持久化。
- Python 环境路线未收敛：当前验证使用工作区 conda，但仓库内存在 `backend/.venv`。
- 首版云 provider 还没最终确定。

### 6. 下一步最优先任务

1. 实现索引持久化基线：补 `note/chunk` schema、SQLite FTS5、最小 ingest pipeline。
2. 跑通最小 `ask` 链路：metadata filter + hybrid retrieval + 引用式返回。
3. 收敛环境与启动方式：明确 `conda` 或 `venv/uv` 为唯一开发入口，并补启动脚本/验证命令。

### 7. 下一次新会话应该先读哪些文件

- [SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md)
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- [backend/app/graphs/state.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/state.py)
- [backend/app/indexing/parser.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/parser.py)
- [backend/app/indexing/models.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/models.py)
- [backend/app/services/sample_vault.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/sample_vault.py)
- [plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts)
- [plugin/src/api/client.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/api/client.ts)
- [references/ObsidianRAG/docs/developer-guide/architecture.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/references/ObsidianRAG/docs/developer-guide/architecture.md)
- [references/ObsidianRAG/backend/obsidianrag/api/server.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/references/ObsidianRAG/backend/obsidianrag/api/server.py)
- [references/ObsidianRAG/plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/references/ObsidianRAG/plugin/src/main.ts)

### 8. 当前最容易被面试官追问的点

- 为什么这里必须是 LangGraph，而不是普通函数链、ReAct agent 或简单 API 编排。
- 为什么采用双端架构，而不是纯 Obsidian 插件或纯云后端。
- 为什么模型路线是“云优先、本地兼容”，而不是一开始就完全本地优先。
- 为什么不能让 LLM 直接改 Vault 文件，为什么必须“后端生成 patch、插件执行写回”。
- 为什么 `sample_vault` 几乎没有 frontmatter 的情况下，仍然先做模板推断和结构解析。
- 为什么 `/health` 返回样本统计，而不是只返回 `ok`。
- 为什么参考 `ObsidianRAG` 但不直接 fork；两者在 chat-first 与 workflow-first 上的边界差异是什么。

### 补充说明

- 当前主文档是唯一主设计文档；下一次会话如果新增功能，必须同步更新 [PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)。
- 下一次会话最容易出错的地方不是“不会写代码”，而是继续增加骨架却不把索引、检索和最小 ask 链路接通。
