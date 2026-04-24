# Session Log

## 使用规则

- 本文件用于累计记录最近相关开发会话，必须持续追加，不允许覆盖当前结论。
- 每次会话都必须分配唯一会话 ID，格式统一为 `SES-YYYYMMDD-XX`。
- 新会话默认追加在文件顶部；旧会话只允许补充勘误，不允许重写历史事实。
- 所有新会话都必须先绑定 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中的一个任务项，再开始执行。
- 2026-03-23 起，主文件只保留活跃 / 最近内容；更早历史统一查 archive。

## 会话索引（活跃 / 最近）

| 会话 ID | 日期 | 主题 | 类型 | 状态 | 对应任务 |
| --- | --- | --- | --- | --- | --- |
| `SES-20260424-02` | 2026-04-24 | 完成 `TASK-059` 真实 provider answer benchmark v1 并收口 smoke 结论 | `Eval` | `已完成` | `TASK-059` |
| `SES-20260424-01` | 2026-04-24 | 清理治理主文件、删除旧 `TASK-060` 并登记 `TASK-062` | `Docs` | `已完成` | `TASK-043` small tail |
| `SES-20260422-01` | 2026-04-22 | 完成 `TASK-058` retrieval benchmark、local preflight 与 FTS baseline 修复并收口治理同步 | `Retrieval / Eval` | `已完成` | `TASK-058` |
| `SES-20260419-01` | 2026-04-19 | 完成 `TASK-057` 的 50 条 ask benchmark 数据集并收口治理同步 | `Eval` | `已完成` | `TASK-057` |
| `SES-20260418-02` | 2026-04-18 | 按双层评测方案重构 ask benchmark 主线任务定义 | `Docs / Eval Governance` | `已完成` | `TASK-061` |
| `SES-20260418-01` | 2026-04-18 | 登记 ask benchmark 主线任务并重排动态控制面 | `Docs / Eval Governance` | `已完成` | `TASK-056` |

## Archive

- 2026-03 起，历史会话按月归档到 `docs/archive/session_logs/`。
- 2026-04-01 到 2026-04-10 的完整会话记录已归档到：
  [docs/archive/session_logs/SESSION_LOG_2026-04-01_to_2026-04-10.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/archive/session_logs/SESSION_LOG_2026-04-01_to_2026-04-10.md)
- 当前 2026-03 历史快照位于：
  [docs/archive/session_logs/SESSION_LOG_2026-03.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/archive/session_logs/SESSION_LOG_2026-03.md)
- 更早历史会话、旧索引与旧任务阶段记录，请优先查 archive，再按 `task_id` 回溯。

## [SES-20260424-02] 完成 `TASK-059` 真实 provider answer benchmark v1 并收口 smoke 结论

- 日期：2026-04-24
- task_id：`TASK-059`
- 类型：`Eval`
- 状态：`已完成`
- 验收结论：`满足 v1 工程目标；质量解释缺口拆入 TASK-062`
- 对应任务：`TASK-059`
- 本会话唯一目标：为 `ASK_QA` 建立真实 provider answer benchmark，使固定数据集能在手动触发下通过真实模型走 `generated_answer` 路径，并比较 `hybrid`、`hybrid_assembly`、`hybrid_assembly_gate` 三种变体。

### 1. 本次目标

- 建立独立于 regression runner 的 answer benchmark CLI。
- 固定 cloud provider / canonical model 口径，当前为 `openai-compatible` + `qwen3.6-flash-2026-04-16`。
- 先用固定 `10` 条 smoke subset 控成本，验证真实 provider、prompt version、variant toggles、artifact schema 与规则评分都能跑通。

### 2. 本次完成内容

- 新增 answer benchmark runner、variant matrix、preflight 与 deterministic scoring：
  - [eval/benchmark/run_answer_benchmark.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/benchmark/run_answer_benchmark.py)
  - [backend/app/benchmark/ask_answer_benchmark.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_answer_benchmark.py)
  - [backend/app/benchmark/ask_answer_benchmark_variants.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_answer_benchmark_variants.py)
  - [backend/app/benchmark/ask_answer_benchmark_preflight.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_answer_benchmark_preflight.py)
  - [backend/app/benchmark/ask_answer_benchmark_scoring.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_answer_benchmark_scoring.py)
- 新增固定 smoke subset 文件 [eval/benchmark/ask_answer_benchmark_smoke_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/benchmark/ask_answer_benchmark_smoke_cases.json)，并用测试锁定 subset membership 与 prompt version。
- 在 ask 链路补齐 benchmark toggles，使同一批 query 可比较 `hybrid`、`hybrid + assembly`、`hybrid + assembly + runtime gate`。
- 修复 raw benchmark context 预算问题：关闭 context assembly 时仍会按 prompt budget 截断可见 evidence，而不是把所有 retrieval text 全量塞进 prompt。
- 调整 runtime faithfulness gate 过度严格的问题，让它保守拦截明显矛盾，而不是把 smoke 里的正常回答全部降级。
- 完成 review feedback 中的三个 P1：固定 smoke subset、稳定 prompt version contract、raw context budget cap。

### 3. 本次未完成内容

- 没有跑 full 50-case answer benchmark；本轮只完成 smoke 级真实 provider 验证，避免调试阶段成本失控。
- 没有把 rule correctness 升级为 LLM-as-judge；该缺口已登记为 `TASK-062`。
- 没有证明 context assembly 或 runtime gate 一定提升正确率；当前 smoke 结果反而显示 assembly variant 的 rule correctness 更低，且 runtime gate 未带来拦截收益。

### 4. 关键决策

- 调试期模型固定为 `qwen3.6-flash-2026-04-16`，不用 qwen-max，避免真实 provider smoke 成本过高。
- `TASK-059` 保留 deterministic rule score 作为可重复 smoke signal，不在本任务内引入 LLM-as-judge。
- runtime faithfulness gate 继续定位为保守安全闸门，而不是为了提高 answer correctness 主动改写答案。
- 旧 `TASK-060` 编号已被历史设计占用，新的 judge correctness 任务使用 `TASK-062`。

### 5. 修改过的文件

- [backend/app/benchmark/ask_answer_benchmark.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_answer_benchmark.py)
- [backend/app/benchmark/ask_answer_benchmark_scoring.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_answer_benchmark_scoring.py)
- [backend/app/benchmark/ask_answer_benchmark_preflight.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_answer_benchmark_preflight.py)
- [backend/app/benchmark/ask_answer_benchmark_variants.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_answer_benchmark_variants.py)
- [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)
- [backend/app/context/assembly.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/context/assembly.py)
- [backend/app/quality/faithfulness.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/quality/faithfulness.py)
- [backend/app/retrieval/sqlite_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_fts.py)
- [eval/benchmark/run_answer_benchmark.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/benchmark/run_answer_benchmark.py)
- [eval/benchmark/ask_answer_benchmark_smoke_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/benchmark/ask_answer_benchmark_smoke_cases.json)
- [eval/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/README.md)
- `backend/tests/test_ask_answer_benchmark*.py`、[backend/tests/test_ask_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_workflow.py)、[backend/tests/test_faithfulness.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_faithfulness.py)、[backend/tests/test_retrieval_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_retrieval_fts.py)

### 6. 验证与测试

- 跑了什么命令
  - `/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/.conda/knowledge-steward/bin/python -m unittest tests.test_ask_answer_benchmark tests.test_ask_answer_benchmark_scoring tests.test_ask_answer_benchmark_preflight tests.test_ask_answer_benchmark_cli -v`
  - `git diff --check`
  - 真实 provider smoke 已产出 `/tmp/task-059-answer-benchmark-smoke-final-20260424.json`
- 结果如何
  - answer benchmark 相关回归 `24/24` 通过。
  - `git diff --check` 通过。
  - smoke artifact：`run_status=passed`，`selected_case_count=10`，`provider_name=openai-compatible`，`model_name=qwen3.6-flash-2026-04-16`，`prompt_version=tool:2026-04-22-tool-v1|answer:2026-04-22-grounded-v1`。
  - smoke 聚合：`hybrid answer_correctness=0.65`，`hybrid_assembly=0.45`，`hybrid_assembly_gate=0.45`；三个 variant 均为 `generated_answer_rate=1.0`、`retrieval_only_rate=0`、`unsupported_claim_rate=0`。
- 哪些没法验证
  - 没有重跑 full 50-case benchmark。
  - 没有用 LLM-as-judge 复核 answer correctness。
  - smoke artifact 记录 `worktree_dirty=true`，因为 worktree 中存在与本任务无关的 `package-lock.json / node_modules` 脏改。

### 7. 范围偏移

- 运行中发现旧 `TASK-060` 已存在且 active governance 文件过长；该问题已作为 `TASK-043` small tail 用 `SES-20260424-01` 单独处理，没有混入 `TASK-059` 实现。
- 讨论过 LLM-as-judge，但没有把它塞进 `TASK-059`；已拆为 `TASK-062`。

### 8. 未解决问题

- 当前 rule-based `answer_correctness` 不足以可靠判断语义正确性。
- `hybrid_assembly` 在 10-case smoke 中低于 raw `hybrid`，但在 judge 前不能确认这是装配层真实负收益还是规则评分误伤。
- runtime faithfulness gate 在本次 smoke 中没有产生有效拦截，说明它更像安全兜底，不是 correctness uplift 机制。
- full benchmark 仍需显式手动触发。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果后续直接引用本次 `answer_correctness` 数字，会夸大 deterministic rule score 的可信度。
- 技术债：artifact 还没有 token / cost 统计，不利于讲 trade-off。
- 假设：下一步应优先做 `TASK-062`，先把 correctness judge 可信度补上，再决定是否继续调 context assembly 或 runtime gate。

### 10. 下一步最优先任务

- 默认进入 `TASK-062`：为 ask answer benchmark 接入离线 LLM-as-judge 语义正确性评分。
- `TASK-062` 后再决定是否跑 full 50-case benchmark，或回头调 assembly / gate。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [eval/benchmark/run_answer_benchmark.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/benchmark/run_answer_benchmark.py)
- [backend/app/benchmark/ask_answer_benchmark_scoring.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_answer_benchmark_scoring.py)
- [backend/app/benchmark/ask_answer_benchmark.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_answer_benchmark.py)
- [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)

### 12. 当前最容易被追问的点

- 为什么 `hybrid_assembly` 的 rule correctness 低于 raw `hybrid`，这是否说明装配层有害？
- 为什么 runtime faithfulness gate 没有拦截，是否说明它没有价值？
- 为什么 rule-based `answer_correctness` 不够可靠，LLM-as-judge 应如何设计才不会变成更贵的不稳定指标？

## [SES-20260424-01] 清理治理主文件、删除旧 `TASK-060` 并登记 `TASK-062`

- 日期：2026-04-24
- task_id：`TASK-043` small tail
- 类型：`Docs`
- 状态：`已完成`
- 验收结论：`完成静态治理整理`
- 对应任务：`TASK-043` 的 archive / active control-plane cleanup 尾项
- 本会话唯一目标：按 `project-session-governor` 的 active / recent 约定，收缩治理主文件，并修正旧 `TASK-060` 与新 LLM-as-judge 任务的编号冲突。

### 1. 本次目标

- 删除 active queue 中已无意义的旧 `TASK-060`。
- 把 LLM-as-judge 语义正确性评分登记为新的 `TASK-062`，避免复用旧编号。
- 把 `TASK_QUEUE.md` 与 `SESSION_LOG.md` 中过长的旧完成记录移入 archive，让主文件恢复“活跃 / 最近入口”的用途。

### 2. 本次完成内容

- 在 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中移除旧 `TASK-060` 主块，并新增 `TASK-062` 作为 `TASK-059` 后续的 LLM-as-judge correctness 任务。
- 将旧完成 / 吸收任务块归档到 [docs/archive/task_queue/TASK_QUEUE_20260424_pruned_from_active.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/archive/task_queue/TASK_QUEUE_20260424_pruned_from_active.md)。
- 将 2026-04-01 到 2026-04-10 的完整会话记录归档到 [docs/archive/session_logs/SESSION_LOG_2026-04-01_to_2026-04-10.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/archive/session_logs/SESSION_LOG_2026-04-01_to_2026-04-10.md)。
- 在 [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md) 中把旧 `TASK-060` 改为已删除口径，并补充 `TASK-062` 的读取入口与风险说明。

### 3. 本次未完成内容

- 没有实现 `TASK-062`。
- 没有整理 `PROJECT_MASTER_PLAN.md`、`CHANGELOG.md` 或面试沉淀文档。
- 没有处理 main 工作区中既有未提交的非本轮文档与代码改动。

### 4. 关键决策

- 新 judge 任务使用 `TASK-062`，不复用旧 `TASK-060`；原因是旧编号已经在 `TASK-056 / TASK-061` 的历史设计中出现过。
- 主 `TASK_QUEUE.md` 保留 benchmark 当前主线、两个旧业务 planned 任务和最近 benchmark 上下文；旧完成任务块转入 archive。
- 主 `SESSION_LOG.md` 保留 2026-04-18 以来的 benchmark 相关完整记录；更早 4 月记录转入 archive，3 月记录继续使用既有 archive。

### 5. 修改过的文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/archive/task_queue/TASK_QUEUE_20260424_pruned_from_active.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/archive/task_queue/TASK_QUEUE_20260424_pruned_from_active.md)
- [docs/archive/session_logs/SESSION_LOG_2026-04-01_to_2026-04-10.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/archive/session_logs/SESSION_LOG_2026-04-01_to_2026-04-10.md)

### 6. 验证与测试

- 跑了什么命令
  - `rg -n "TASK-060|TASK-062|^### TASK-" docs/TASK_QUEUE.md docs/archive/task_queue/TASK_QUEUE_20260424_pruned_from_active.md`
  - `rg -n "SESSION_LOG_2026-04-01_to_2026-04-10|^## \\[SES-" docs/SESSION_LOG.md docs/archive/session_logs/SESSION_LOG_2026-04-01_to_2026-04-10.md`
  - `wc -l docs/TASK_QUEUE.md docs/SESSION_LOG.md docs/archive/task_queue/TASK_QUEUE_20260424_pruned_from_active.md docs/archive/session_logs/SESSION_LOG_2026-04-01_to_2026-04-10.md`
- 结果如何
  - `TASK_QUEUE.md` 从整理前约 `867` 行收缩到约 `327` 行。
  - `SESSION_LOG.md` 在 cleanup 后收缩到约 `539` 行；随后本文件又追加了 `TASK-059` closeout 记录。
- 哪些没法验证
  - 本次是 docs-only，没有运行 backend / plugin 测试。

### 7. 范围偏移

- 没有开启新的业务 medium。
- 本次作为 `TASK-043` 的治理归档尾项处理，避免为了清理文档再膨胀出一个新的 active task。

### 8. 未解决问题

- 主工作区仍有此前已存在的未提交变更，提交前需要单独判断是否一起收束。
- `CURRENT_STATE.md` 的“最近完成”表仍偏长，但体量已经远小于 `SESSION_LOG.md`，本轮没有继续压缩。

### 9. 新增风险 / 技术债 / 假设

- 假设：旧 `TASK-060` 不再作为独立任务维护，其有价值部分后续由 `TASK-062` 的 judge correctness 与必要的人审校准小尾项覆盖。
- 技术债：archive 目前仍是手工文件，没有自动一致性检查脚本。

### 10. 下一步最优先任务

- 继续收口 `TASK-059` 的真实 provider answer benchmark。
- `TASK-059` 跑稳后，再进入 `TASK-062` 接入 LLM-as-judge semantic correctness。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [eval/benchmark/run_answer_benchmark.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/benchmark/run_answer_benchmark.py)
- [backend/app/benchmark/ask_answer_benchmark_scoring.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_answer_benchmark_scoring.py)

### 12. 当前最容易被追问的点

- 为什么旧 `TASK-060` 删除而不是复用？
- 为什么 LLM-as-judge 应作为离线 benchmark 能力，而不是接入 runtime？
- 为什么主治理文件需要定期 archive，而不是一直追加完整历史？

## [SES-20260422-01] 完成 `TASK-058` retrieval benchmark、local preflight 与 FTS baseline 修复并收口治理同步

- 日期：2026-04-22
- task_id：`TASK-058`
- 类型：`Retrieval / Eval`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应任务：`TASK-058`
- 本会话唯一目标：完成 `TASK-058`，让 `ASK_QA` 正式拥有 retrieval-only benchmark runner，并在本地 provider 口径下拿到可复现、可讲的 retrieval baseline 数字。

### 1. 本次目标

- 为 `TASK-057` 的固定 `50` 条数据集落地 retrieval-only benchmark runner。
- 让 benchmark 在本地 embedding provider 未配置、模型不可用或向量索引未就绪时，能在 CLI preflight 阶段 fail-closed。
- 修复 `fts_only` 在中文自然语言 / 日期版本号 query 下的异常低召回，避免 retrieval baseline 被实现缺陷污染。

### 2. 本次完成内容

- 已在主线落地 retrieval benchmark runner：
  - [eval/benchmark/run_retrieval_benchmark.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/benchmark/run_retrieval_benchmark.py)
  - [backend/app/benchmark/ask_retrieval_benchmark.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_retrieval_benchmark.py)
  - [backend/app/benchmark/ask_retrieval_modes.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_retrieval_modes.py)
  - [backend/app/benchmark/ask_retrieval_metrics.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_retrieval_metrics.py)
- 已在主线落地 local-only preflight：
  - [backend/app/benchmark/ask_retrieval_preflight.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_retrieval_preflight.py)
  - benchmark 在 local provider / model / vector index 未就绪时会直接失败，不再产出半成品 artifact。
- 已确认 headline retrieval subset 固定为 `38` 条 case：
  - `single_hop + multi_hop + metadata_filter`
  - 排除 `tool_allowed` 与 `abstain_or_no_hit`
- 已修复 [backend/app/retrieval/sqlite_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_fts.py) 的 FTS 检索断口：
  - 长中文自然语言整句被错误当作硬性 `MATCH` 词项
  - 日期 / 版本号只作为 note path/title 标识时无法正确召回
  - hint rerank 在 SQL `LIMIT` 后执行，目标会先被截断
  - 版本 / 日期 hint 边界过宽，导致误 boost
  - identifier-only query（如 `2023-06-05`、`v6.2.5`）无法靠 path/title hint 命中
- 已得到当前 retrieval baseline 正式数字：
  - `fts_only`: `Recall@5=0.2368`, `Recall@10=0.2368`, `NDCG@10=0.2368`
  - `vector_only`: `Recall@5=0.5526`, `Recall@10=0.6842`, `NDCG@10=0.4612`
  - `hybrid_rrf`: `Recall@5=0.6579`, `Recall@10=0.7895`, `NDCG@10=0.5636`

### 3. 本次未完成内容

- 没有继续做剩余 `8` 个 `hybrid_rrf` miss case 的 failure taxonomy。
- 没有继续判断这些 residual miss 中，哪些还能靠 query rewrite 覆盖，哪些更像 chunking / heading boost / path prior 问题。
- 没有启动 `TASK-059` 的真实 provider answer benchmark。

### 4. 关键决策

- `TASK-058` retrieval baseline 保持 v1 scope：headline 只看 `Recall@5 / Recall@10 / NDCG@10`，不再把 `MRR / latency` 作为首版 headline 指标。
- benchmark 采用 `local-only` provider 口径，不允许静默 fallback 到 cloud。
- `fts_only` 问题按真实检索实现修复，而不是只对 benchmark 单独做 query rewrite 特判。
- 日期 / 版本号 query 改为 hint-aware reranking，并补 identifier-only query 支持。

### 5. 修改过的文件

- [eval/benchmark/run_retrieval_benchmark.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/benchmark/run_retrieval_benchmark.py)
- [backend/app/benchmark/ask_retrieval_benchmark.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_retrieval_benchmark.py)
- [backend/app/benchmark/ask_retrieval_modes.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_retrieval_modes.py)
- [backend/app/benchmark/ask_retrieval_metrics.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_retrieval_metrics.py)
- [backend/app/benchmark/ask_retrieval_preflight.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_retrieval_preflight.py)
- [backend/app/retrieval/sqlite_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_fts.py)
- [backend/tests/test_ask_retrieval_benchmark.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_retrieval_benchmark.py)
- [backend/tests/test_ask_retrieval_cli.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_retrieval_cli.py)
- [backend/tests/test_ask_retrieval_preflight.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_retrieval_preflight.py)
- [backend/tests/test_retrieval_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_retrieval_fts.py)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)

### 6. 验证与测试

- 跑了什么命令
  - `PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest backend.tests.test_retrieval_embeddings backend.tests.test_retrieval_vector backend.tests.test_ask_retrieval_modes backend.tests.test_ask_retrieval_preflight backend.tests.test_ask_retrieval_cli backend.tests.test_ask_retrieval_metrics backend.tests.test_ask_retrieval_benchmark -v`
  - `PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest backend.tests.test_retrieval_fts backend.tests.test_ask_retrieval_metrics backend.tests.test_ask_retrieval_benchmark -v`
  - `set -a; source backend/.env; set +a; ./.conda/knowledge-steward/bin/python eval/benchmark/run_retrieval_benchmark.py --output /tmp/task-058-local-benchmark-main-after-identifier-fix.json`
- 结果如何
  - retrieval benchmark / preflight 相关回归 `31/31` 通过。
  - FTS 修复后的 retrieval 相关回归 `22/22` 通过。
  - retrieval benchmark 在本地 `Ollama + bge-m3` 口径下跑通，并产出正式 baseline artifact。
- 哪些没法验证
  - 本次没有进入 `TASK-059`，因此没有 answer-level benchmark 或真实 provider ask 生成质量验证。
- 哪些只是静态修改
  - 本次 closeout 对 `TASK_QUEUE / CURRENT_STATE / SESSION_LOG` 的同步属于静态治理更新。

### 7. 范围偏移

- 中途为了让 benchmark 数字可信，额外修了 FTS 查询实现；这是 `TASK-058` 的有效伴随工作，不是新的 `medium`。
- 讨论过“剩余失败 case 能否靠 query rewrite 覆盖”，但没有继续扩出新的实现任务。

### 8. 未解决问题

- `hybrid_rrf` 仍有 `8` 个 miss case，retrieval layer 还不是最终形态。
- 当前还没有 bucket-level failure taxonomy，也还没有 query rewrite 覆盖率分析。
- `TASK-059` 尚未开始，仍缺真实 provider 的 answer-level benchmark。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果直接停在 `TASK-058`，只能证明 retrieval layer 有收益，不能证明最终 ask answer 更好。
- 技术债：当前 retrieval baseline 还没有 query bucket 聚合，剩余失败类型只能靠人工逐条分析。
- 假设：当前最优先的主线已经从“补 retrieval runner”切换为“补 answer benchmark”，而不是继续在 retrieval 层无限打磨。

### 10. 下一步最优先任务

- 默认进入 `TASK-059`，为 ask 主链路建立真实 provider 的 answer benchmark 与 runtime gate trade-off 评测。
- 若只做小尾项，可单独补一个 `small`：对剩余 `8` 个 `hybrid_rrf` miss 做 taxonomy，并判断 query rewrite 的实际覆盖面。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [eval/benchmark/ask_benchmark_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/benchmark/ask_benchmark_cases.json)
- [backend/app/benchmark/ask_retrieval_benchmark.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_retrieval_benchmark.py)
- [backend/app/retrieval/sqlite_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_fts.py)
- [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)

### 12. 当前最容易被追问的点

- 为什么 `fts_only` 从 `0` 提升到 `0.2368` 后仍然明显弱于 `vector_only`？
- `hybrid_rrf` 剩余 `8` 个 miss 的主因到底是 query rewrite、chunking、heading 粒度，还是 path/title prior 不够？
- 当前 retrieval baseline 数字是否已经足够支撑简历描述，还是必须等 `TASK-059` 的 answer-level 数字？

## [SES-20260419-01] 完成 `TASK-057` 的 50 条 ask benchmark 数据集并收口治理同步

- 日期：2026-04-19
- task_id：`TASK-057`
- 类型：`Eval`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应任务：`TASK-057`
- 本会话唯一目标：为 `ASK_QA` 完成固定 `50` 条 query 的正式人工审核 benchmark 数据集，并把治理控制面从“默认进入 `TASK-057`”切到“默认进入 `TASK-058`”。

### 1. 本次目标

- 在正式 dataset 中落满 `50` 条 approved ask benchmark case，而不是继续停留在空文件或临时 smoke 副本。
- 保持 bucket 分布满足 `20` 单跳、`10` 多跳、`8` metadata/filter、`6` abstain/no-hit、`6` tool_allowed。
- 用最小验证证明正式数据文件和 review 工具链仍然合法。

### 2. 本次完成内容

- 在 [eval/benchmark/ask_benchmark_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/benchmark/ask_benchmark_cases.json) 中完成了 `50` 条正式 approved case 落库，最终 bucket 分布为：
  - `single_hop=20`
  - `multi_hop=10`
  - `metadata_filter=8`
  - `abstain_or_no_hit=6`
  - `tool_allowed=6`
- 保持 [eval/benchmark/ask_benchmark_review_backlog.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/benchmark/ask_benchmark_review_backlog.json) 为空；本轮没有把任何 `revise / reject` 条目写入 backlog。
- 在 [backend/tests/test_ask_benchmark_dataset.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_benchmark_dataset.py) 中修正了一个过时断言：它之前强制正式 dataset 文件必须为空，现已改为检查“seeded dataset 文件形状合法且可被 loader 正常读取”。
- 在 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 与 [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md) 中同步 `TASK-057` 完成事实，并将默认下一任务切到 `TASK-058`。

### 3. 本次未完成内容

- 没有实现 retrieval-only runner、rank-based 指标聚合或 mode 对比；这些仍属于 `TASK-058`。
- 没有实现真实 provider answer benchmark、`generated_answer` 主链路对比或 runtime gate trade-off 聚合；这些仍属于 `TASK-059`。
- 没有把“纯回答生成效果”的独立 answer-generation benchmark 单独立项；当前仍以 retrieval-grounded ask benchmark 为主。

### 4. 关键决策

- 放弃把 generator 继续打磨成当前主路径，改为以人工 / 半人工方式直接从仓库内容反推候选并逐批 review；原因是当前目标是尽快拿到首版 `50` 条合格正式集，而不是先把大规模自动扩样能力打磨完整。
- query 统一按“self-contained、可检索、适合全 vault RAG”收敛，不接受 `这篇笔记`、`这段` 这类依赖隐式上下文的指代式问法。
- 当前数据集同时保留 retrieval truth、answer truth 与行为 truth；原因是这套 benchmark 不是纯召回集，而是面向 ask 链路的 grounded benchmark。
- 发现测试仍假设正式 dataset 为空后，没有绕过验证，而是把测试更新到与新 contract 一致；原因是这个断口会直接误导后续收尾判断。

### 5. 修改过的文件

- [eval/benchmark/ask_benchmark_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/benchmark/ask_benchmark_cases.json)
- [backend/tests/test_ask_benchmark_dataset.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_benchmark_dataset.py)
- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)

### 6. 验证与测试

- 跑了什么命令
  - `./.conda/knowledge-steward/bin/python eval/benchmark/manage_ask_benchmark.py validate`
  - `PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest backend.tests.test_ask_benchmark_dataset backend.tests.test_ask_benchmark_validation backend.tests.test_ask_benchmark_review`
- 结果如何
  - dataset / backlog 校验通过。
  - benchmark 相关 `59` 个 `unittest` 全部通过。
- 哪些没法验证
  - 本次没有运行 `TASK-058` 或 `TASK-059` 相关 runner，因为它们还未实现。
- 哪些只是静态修改
  - 正式 dataset JSON 写入、治理文档同步，以及一个 benchmark dataset 测试断言更新。

### 7. 范围偏移

- 会话中讨论过“这套数据更偏召回还是更偏生成评测”，但没有因此扩出新的 `medium`，也没有顺手开启 answer-generation 独立 benchmark。
- 候选生成器质量曾暴露出指代式 query 问题，但本会话没有继续投入 generator 打磨，而是回到人工 review 主路径；这属于同一 `TASK-057` 内的执行方式调整，不是新任务。

### 8. 未解决问题

- `TASK-058` 仍未把这 `50` 条 case 正式接入 retrieval-only runner，也还没有 `Recall@K / MRR / NDCG@10 / latency` 聚合输出。
- `TASK-059` 仍未把这 `50` 条 case 接到真实 provider 的 answer benchmark，也还没有 provider/model 维度的稳定结果文件。
- 当前 generator / candidate tooling 虽然存在，但还不能稳定直接产出高质量的 self-contained query；当前正式数据集主要靠人工 review 落库。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果 `TASK-058` 迟迟不做，这 `50` 条数据只能证明“数据层已就绪”，还不能证明 FTS / vector / hybrid 的检索收益。
- 技术债：candidate generator 仍可能产出依赖隐式上下文的 query，后续如果要继续扩样本，需要先补质量过滤或继续人工兜底。
- 假设：当前最有价值的下一步不是继续扩到超过 `50` 条，而是先用这套固定数据把 retrieval layer 和 answer layer 分开跑通。

### 10. 下一步最优先任务

- 默认进入 `TASK-058`，基于这 `50` 条固定数据集建立 retrieval-only runner 与 rank-based 指标面板。
- 随后进入 `TASK-059`，把 ask 真正接到真实 provider 的 answer benchmark 与 runtime gate trade-off 评测。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [eval/benchmark/ask_benchmark_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/benchmark/ask_benchmark_cases.json)
- [eval/benchmark/ask_benchmark_spec.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/benchmark/ask_benchmark_spec.md)
- [eval/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/README.md)
- [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
- [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)
- [backend/app/retrieval/hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/hybrid.py)

### 12. 当前最容易被追问的点

- 为什么这 `50` 条数据集不等于“answer generation benchmark 已完成”？
- 为什么当前阶段选择人工 review 主路径，而不是继续把 generator 打磨成自动扩样主路径？
- `tool_allowed` 和 `abstain_or_no_hit` 这两类 case 进入 `TASK-058` 后，retrieval 指标该怎么定义才不失真？

## [SES-20260418-02] 按双层评测方案重构 ask benchmark 主线任务定义

- 日期：2026-04-18
- task_id：`TASK-061`
- 类型：`Docs / Eval Governance`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应任务：`TASK-061`
- 本会话唯一目标：把 ask benchmark 主线从第一次登记时的“`TASK-057` 到 `TASK-060` 四段串行”重构为“`TASK-057` 到 `TASK-059` 三段主线 + `TASK-060` deferred”，并把 `TASK-059` 明确锁定为真实 provider 的 answer benchmark。

### 1. 本次目标

- 按刚确认的双层评测设计，重写 `TASK-057 / TASK-058 / TASK-059 / TASK-060` 的任务定义。
- 把 `CURRENT_STATE` 的默认下一任务链从 `TASK-057 -> TASK-058 -> TASK-059 -> TASK-060` 收敛为 `TASK-057 -> TASK-058 -> TASK-059`。
- 记录为什么 `TASK-059` 必须绑定真实 provider 与 ask 真实 `generated_answer` 路径。

### 2. 本次完成内容

- 在 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中新增 `TASK-061`，并重写 ask benchmark 主线定义：
  - `TASK-057`：固定 `50` 条 query 的数据集与样本协议
  - `TASK-058`：retrieval baseline 与 rank-based 指标面板
  - `TASK-059`：真实 provider 的 answer benchmark 与 runtime gate trade-off
  - `TASK-060`：改为 `deferred`，不再阻塞当前主线
- 在 [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md) 中补入 `TASK-061` 完成事实，更新默认下一任务、当前风险和建议先读文件。
- 删除了刚才那份未被采用的 superpowers spec 草稿，避免治理信息出现第二来源。
- 在本文件新增本次 governed session 记录，固化第二轮设计校准的原因与影响。

### 3. 本次未完成内容

- 没有实现 `TASK-057` 到 `TASK-059` 的任何 benchmark 代码。
- 没有修改 `eval/run_eval.py`、`backend/app/services/ask.py`、`backend/app/context/assembly.py` 或 `backend/app/quality/faithfulness.py` 的运行行为。
- 没有同步 [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 中仍引用旧四段 benchmark 主线的表述。

### 4. 关键决策

- 保留双层评测，而不是让所有 eval 都走真实 provider；原因是 regression 与 resume evidence 的职责不同。
- `TASK-059` 必须绑定真实 provider 与 ask 真实 `generated_answer` 路径；原因是当前 `provider_mode=none / mocked_cloud` 只能证明接线与降级，不足以证明生成质量。
- benchmark 首版固定 `50` 条 query、固定 canonical provider/model，并允许少量工具 query；原因是先要拿到单一且可讲的证据口径，而不是同时处理多 provider 波动。
- `TASK-060` 延后；原因是当前最关键的短板仍是“基础 benchmark 还没形成”，人工校准与报告导出不应继续阻塞第一阶段主线。

### 5. 修改过的文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [docs/superpowers/specs/2026-04-18-ask-resume-benchmark-design.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/superpowers/specs/2026-04-18-ask-resume-benchmark-design.md)（已删除）

### 6. 验证与测试

- 跑了什么命令
  - `rg -n "TASK-057|TASK-058|TASK-059|TASK-060|TASK-061|SES-20260418-02" docs/TASK_QUEUE.md docs/CURRENT_STATE.md docs/SESSION_LOG.md`
- 结果如何
  - 新的 `task_id` 与 `session_id` 已在三份治理文档中对齐出现；`TASK-060` 仅作为 deferred 保留，不再出现在默认下一任务主链中。
- 哪些没法验证
  - 本次是纯治理文档调整，没有运行 benchmark、后端或插件测试。
- 哪些只是静态修改
  - 本次全部改动均为任务定义、动态控制面与会话日志同步，不涉及代码行为变化。

### 7. 范围偏移

- 没有引入第二个 `medium` 实现任务。
- 没有顺手推进 `TASK-031 / TASK-032`，也没有提前开始 `TASK-057` 到 `TASK-059` 的实现。
- 没有保留刚才那份 superpowers spec；原因是你明确要求以 `project-session-governor` 的治理文档作为唯一落点。

### 8. 未解决问题

- `eval/run_eval.py` 目前仍只支持 `provider_mode=none / mocked_cloud`；真实 provider benchmark 的入口与 metadata 落盘仍待 `TASK-059` 实现。
- fixed `50` 条 query 数据集的文件落位、chunk locator helper 与 schema 校验脚本仍待 `TASK-057` 落地。
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 中仍可能残留旧的四段 benchmark 主线表述，当前继续作为 `tail_sync_item` 保留。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果后续迟迟不推进 `TASK-059`，你仍然拿不到基于真实 provider 的 answer 指标，简历证据问题不会真正解决。
- 技术债：治理文档已经明确两层评测，但 `eval` 代码与目录结构还没有正式拆层。
- 假设：当前最优先的不是人工校准或报告导出，而是先跑通固定 `50` 条 query、固定 canonical provider/model 的基础 benchmark。

### 10. 下一步最优先任务

- 默认进入 `TASK-057`，构建固定 `50` 条 query 的人工标注 benchmark 数据集与样本协议。
- 随后进入 `TASK-058`，建立 retrieval baseline 与 rank-based 指标面板。
- 再进入 `TASK-059`，建立真实 provider 的 answer benchmark 与 runtime gate trade-off 评测。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
- [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)
- [backend/app/retrieval/hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/hybrid.py)
- [backend/app/context/assembly.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/context/assembly.py)
- [backend/app/quality/faithfulness.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/quality/faithfulness.py)
- [backend/app/tools/registry.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/tools/registry.py)
- [sample_vault/](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/sample_vault)

### 12. 当前最容易被追问的点

- 为什么 `TASK-059` 必须接真实 provider，而不是继续沿用 `mocked_cloud`？
- 为什么 `TASK-060` 现在先 defer，而不是立刻做人工校准和报告导出？
- 为什么 benchmark 首版固定为单一 canonical provider/model，而不是多 provider 横向对比？

## [SES-20260418-01] 登记 ask benchmark 主线任务并重排动态控制面

- 日期：2026-04-18
- task_id：`TASK-056`
- 类型：`Docs / Eval Governance`
- 状态：`已完成`
- 验收结论：`完全满足`
- 对应任务：`TASK-056`
- 本会话唯一目标：把“当前 eval 更像 regression baseline，而不是 resume-grade benchmark”的诊断正式写入治理文档，并将后续主线拆成一组 ask-only benchmark `medium` 任务。

### 1. 本次目标

- 在 `TASK_QUEUE` 中登记一组新的 ask benchmark 任务，而不是继续口头依赖聊天历史。
- 把 `CURRENT_STATE` 的默认下一任务从 `TASK-031 / TASK-032` 切到 benchmark 主线。
- 在 `SESSION_LOG` 留下一份后续会话可直接接力的治理记录。

### 2. 本次完成内容

- 在 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 中新增 `TASK-056` 到 `TASK-060`：
  - `TASK-056`：本次任务登记与控制面对齐
  - `TASK-057`：ask benchmark 数据集与样本协议
  - `TASK-058`：retrieval baseline 与 rank-based 指标面板
  - `TASK-059`：answer ablation 与 runtime gate trade-off 评测
  - `TASK-060`：人工校准、bad case taxonomy 与报告导出
- 在 [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md) 中补入 `TASK-056` 完成事实、benchmark 主线风险，并将默认下一任务切到 `TASK-057`。
- 在本文件新增本次 governed session 记录，固化任务选择理由、范围边界与 tail sync 说明。

### 3. 本次未完成内容

- 没有实现 `TASK-057` 到 `TASK-060` 的任何 benchmark 代码。
- 没有修改 `eval/run_eval.py`、golden case、retrieval、assembly 或 runtime gate 实现。
- 没有同步 [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 中仍指向 `TASK-031 / TASK-032` 的所有 `Next Action` 文案。

### 4. 关键决策

- 优先登记 ask-only benchmark，而不是同时把 governance / digest 一起拉进来；原因是当前最大短板是 ask 主链路缺 baseline、缺 ablation、缺人工校准。
- 把 benchmark 主线放到 `TASK-031 / TASK-032` 之前；原因是当前用户目标是“拿到可写进简历的技术结果数字”，不是先补副作用恢复或 FTS 成本问题。
- 先更新动态控制面，不一次性全量修改稳定主文档；原因是本轮重点是任务治理，不是重写整份路线文档。

### 5. 修改过的文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)

### 6. 验证与测试

- 跑了什么命令
  - `rg -n "TASK-056|TASK-057|TASK-058|TASK-059|TASK-060|SES-20260418-01" docs/TASK_QUEUE.md docs/CURRENT_STATE.md docs/SESSION_LOG.md`
- 结果如何
  - 关键 `task_id` 与 `session_id` 已在三份治理文档中同时出现，未与现有编号冲突。
- 哪些没法验证
  - 本次是纯治理文档改动，没有运行 benchmark、后端或插件测试。
- 哪些只是静态修改
  - 本次全部改动均为任务治理与动态控制面对齐，不涉及代码行为变化。

### 7. 范围偏移

- 没有引入第二个 `medium` 实现任务。
- 没有顺手推进 `TASK-031 / TASK-032`，也没有提前开始 `TASK-057` 到 `TASK-060` 的实现。

### 8. 未解决问题

- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 中仍有多处 `Next Action = TASK-031 / TASK-032` 的旧口径，当前作为 `tail_sync_item` 保留。
- ask benchmark 的数据文件格式、目录落位与 review rubric 仍待 `TASK-057` / `TASK-060` 决定。
- 当前 benchmark 主线只切到 ask，governance / digest 的 resume-grade 评测后续是否另起 umbrella 仍未决定。

### 9. 新增风险 / 技术债 / 假设

- 风险：如果后续不尽快推进 `TASK-057`，这次优先级调整会再次退化成“只有诊断，没有执行”。
- 技术债：稳定主文档与动态控制面暂时存在优先级口径差异，后续需要 selective sync。
- 假设：当前最值得先做的不是更多功能，而是先把 ask-only benchmark 打穿，拿到可辩护的技术结果数字。

### 10. 下一步最优先任务

- 默认进入 `TASK-057`，为 `ASK_QA` 构建人工标注 benchmark 数据集与样本协议。
- 随后进入 `TASK-058` 和 `TASK-059`，分别补 retrieval baseline 与 answer ablation。
- benchmark 主线收口后，再回到 `TASK-031 / TASK-032`。

### 11. 下一次新会话应该先读哪些文件

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
- [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md)
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)
- [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
- [eval/golden/ask_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/ask_cases.json)
- [backend/app/retrieval/hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/hybrid.py)
- [backend/app/context/assembly.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/context/assembly.py)
- [backend/app/quality/faithfulness.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/quality/faithfulness.py)
- [sample_vault/](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/sample_vault)

### 12. 当前最容易被追问的点

- 为什么当前要把 benchmark 放到 `TASK-031 / TASK-032` 之前？
- 为什么 ask benchmark 要先独立切出来，而不是继续把 governance / digest 混在同一条主线里？
- 为什么当前 `23` 条 eval case 仍不足以支撑简历级结果表述？
