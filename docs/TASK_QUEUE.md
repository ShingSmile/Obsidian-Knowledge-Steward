# TASK_QUEUE

本文件是会话级任务的唯一队列来源。
所有新会话必须先绑定本文件中的一个任务项，再开始执行。

## Queue Rules

- 一个会话只能绑定一个 `scope=medium` 的任务项。
- `small` 任务只能作为当前任务的伴随改动或 `derived_tasks` 存在，不能单独开启一个新会话。
- `large` 任务必须先拆分为多个 `medium` 任务后才能开工。
- 会话结束后必须同步更新本文件与 [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)。
- 新会话默认读取顺序为：
  1. [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
  2. [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md)
  3. [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md) 中最近相关记录
  4. 相关代码入口文件

## Archive

- 2026-03-23 拆分前的完整任务队列快照已归档到：
  [docs/archive/task_queue/TASK_QUEUE_20260323_pre_split.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/archive/task_queue/TASK_QUEUE_20260323_pre_split.md)
- 2026-04-24 从主文件移出的旧完成 / 吸收任务块归档到：
  [docs/archive/task_queue/TASK_QUEUE_20260424_pruned_from_active.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/archive/task_queue/TASK_QUEUE_20260424_pruned_from_active.md)
- 主文件从本次起只保留活跃 / 最近内容；更早的完成任务统一去 archive 查。

## Active Backlog

### TASK-056

- `task_id`: `TASK-056`
- `session_id`: `SES-20260418-01`
- `title`: 登记 ask benchmark 主线任务并重排动态控制面
- `category`: `Docs`
- `priority`: `P1`
- `status`: `completed`
- `scope`: `medium`
- `goal`: 基于 2026-04-18 的评测校准结论，把当前“golden regression baseline”正式升级为一条新的治理主线：登记 `TASK-057` 到 `TASK-060` 四个 ask-only benchmark `medium`，并把 `CURRENT_STATE` 的默认下一任务从 `TASK-031 / TASK-032` 切到 benchmark 主线，避免后续会话继续沿旧优先级推进。
- `out_of_scope`:
  - 不实现 benchmark 数据集、指标、runner 或报告导出
  - 不修改后端 / 插件业务逻辑
  - 不重写已完成任务的验收事实
  - 不一次性同步 `PROJECT_MASTER_PLAN.md` 中所有遗留的 `Next Action` 文案
- `acceptance_criteria`:
  - `TASK-057` 到 `TASK-060` 以标准 queue 格式登记到 `TASK_QUEUE`
  - `CURRENT_STATE` 的默认下一任务切到 `TASK-057`
  - `SESSION_LOG` 记录本次任务登记会话、关键决策和 tail sync 项
  - benchmark 主线与旧的 `TASK-031 / TASK-032` 优先级关系被明确说明，不再依赖聊天历史
- `depends_on`:
  - `TASK-053`
  - `TASK-054`
- `related_files`:
  - `docs/TASK_QUEUE.md`
  - `docs/CURRENT_STATE.md`
  - `docs/SESSION_LOG.md`
  - `docs/INTERVIEW_PREP_ESSENCE.md`
  - `docs/MENTOR_PROGRESS.md`
- `derived_tasks`:
  - `small: 视后续路线是否稳定，选择性同步 PROJECT_MASTER_PLAN 中仍指向 TASK-031 / TASK-032 的 Next Action 段落`
- `notes`: 本任务是一个纯治理会话，不对应代码实现。触发原因是用户明确指出：当前离线 eval 与测试通过只能证明“系统没回退”和“代码能跑”，不足以支撑项目成熟度与技术选型有效性判断。基于这轮校准，后续主线先聚焦 ask-only resume-grade benchmark，而不是继续沿 `TASK-031 / TASK-032` 推进。

### TASK-061

- `task_id`: `TASK-061`
- `session_id`: `SES-20260418-02`
- `title`: 按双层评测方案重构 ask benchmark 主线任务定义
- `category`: `Docs`
- `priority`: `P1`
- `status`: `completed`
- `scope`: `medium`
- `goal`: 基于 2026-04-18 的第二轮设计校准，把 ask benchmark 主线从“`TASK-057` 到 `TASK-060` 四段串行”重构为“双层评测、三段主线”：`TASK-057` 固定为 `50` 条数据集与样本协议，`TASK-058` 固定为 retrieval baseline，`TASK-059` 固定为真实 provider 的 answer benchmark，并将 `TASK-060` 从当前主线移出、改为 deferred。
- `out_of_scope`:
  - 不实现 benchmark runner、真实 provider 接线或任何后端逻辑
  - 不修改 `eval/run_eval.py`、`backend/app/services/ask.py` 的运行行为
  - 不同步整个 `PROJECT_MASTER_PLAN.md`
  - 不新增 superpowers spec / plan 文档作为第二治理来源
- `acceptance_criteria`:
  - `TASK-057` 明确为固定 `50` 条 query 的 ask benchmark 数据集任务，并补齐新的样本字段约束
  - `TASK-059` 明确要求真实 provider、canonical provider/model 口径，以及 ask 真走 `generated_answer` 路径
  - `TASK-060` 改为 `deferred`，且不再出现在 `CURRENT_STATE` 的默认下一任务链中
  - `CURRENT_STATE` 与 `SESSION_LOG` 完整记录这次主线重排与设计原因
  - 刚产生的多余 spec 草稿被移除，避免治理信息出现第二来源
- `depends_on`:
  - `TASK-056`
- `related_files`:
  - `docs/TASK_QUEUE.md`
  - `docs/CURRENT_STATE.md`
  - `docs/SESSION_LOG.md`
  - `eval/run_eval.py`
  - `backend/app/services/ask.py`
- `derived_tasks`:
  - `small: 当 canonical provider / model 最终锁定后，在 eval/README 中补运行前置条件与环境变量约束`
  - `small: 当路线再次稳定后，选择性同步 PROJECT_MASTER_PLAN 中仍引用旧四段 benchmark 主线的表述`
- `notes`: 用户明确收窄了 benchmark 设计边界：需要同时保留低成本的 regression layer 和可写进简历的 resume-grade benchmark layer；后者必须在固定 `50` 条 query、固定 canonical provider/model 的前提下，让 ask 真走 `generated_answer` 路径，而不是继续依赖 `provider_mode=none / mocked_cloud` 的接线型指标。基于这次校准，`TASK-060` 不再作为第一阶段阻塞项。

### TASK-057

- `task_id`: `TASK-057`
- `session_id`: `SES-20260419-01`
- `title`: 为 `ASK_QA` 构建人工标注 benchmark 数据集与样本协议
- `category`: `Eval`
- `priority`: `P1`
- `status`: `completed`
- `scope`: `medium`
- `goal`: 为双层评测中的 `resume-grade ask benchmark` 建立一套独立于现有 regression golden case 的固定 `50` 条 query 数据集：以真实 query 为主，显式标注 bucket、相关 note/chunk、expected facts、forbidden claims、tool allowance 与 generate/abstain expectation，使 retrieval 与 answer 评测不再依赖 path suffix / output hint 的临时断言。
- `out_of_scope`:
  - 不实现 retrieval baseline 与 answer ablation runner
  - 不扩展 governance / digest benchmark
  - 不引入 rerank、外部 judge 或 dashboard
  - 不直接修改 ask 主链路逻辑
- `acceptance_criteria`:
  - 新增独立于 `eval/golden/ask_cases.json` 的 ask benchmark 数据文件与 schema 说明
  - 固定 `50` 条 query 样本，其中来自真实 `sample_vault` 场景的不少于 `40` 条
  - 首版 bucket 分布满足：`20` 条单跳事实问答、`10` 条多跳问答、`8` 条 metadata / tag / 日期过滤、`6` 条应拒答或 `no-hit`、`6` 条允许触发工具的 query
  - 每条样本至少标注：`case_id / bucket / user_query / expected_relevant_paths / expected_relevant_chunk_locators / expected_facts / forbidden_claims / allow_tool / expected_tool_names / allow_retrieval_only / should_generate_answer`
  - 有最小校验脚本或测试保证 schema 合法、path 可解析、chunk locator 可回指
- `depends_on`:
  - `TASK-053`
- `related_files`:
  - `eval/benchmark/ask_benchmark_cases.json`
  - `eval/benchmark/ask_benchmark_review_backlog.json`
  - `eval/benchmark/ask_benchmark_spec.md`
  - `eval/benchmark/manage_ask_benchmark.py`
  - `eval/README.md`
  - `eval/run_eval.py`
  - `sample_vault/`
  - `backend/tests/test_ask_benchmark_dataset.py`
  - `backend/tests/test_ask_benchmark_validation.py`
  - `backend/tests/test_ask_benchmark_review.py`
- `derived_tasks`:
  - `small: 为 benchmark 样本增加 bucket 分布统计，防止后续持续偏向单一 query 类型`
  - `small: 为 chunk locator 补最小导出 helper，减少人工标注时反复查库成本`
- `notes`: 当前 ask 结果里的 `answer_relevancy / context_precision / context_recall` 很大程度仍建立在 output hints 与 reference path coverage 之上，适合 regression，不足以回答“检索是否真变好”或“答案是否真更对”。这条任务的目标是先把 regression layer 与 resume-grade benchmark layer 在数据层物理分开，后续 `TASK-058` 与 `TASK-059` 才有统一且可讲的地基。`SES-20260419-01` 已完成首版 `50` 条正式 benchmark case 落库，bucket 分布满足 `20 / 10 / 8 / 6 / 6`，`ask_benchmark_review_backlog.json` 当前为空，`manage_ask_benchmark.py validate` 与三组 benchmark 相关 `unittest` 已通过。

### TASK-058

- `task_id`: `TASK-058`
- `session_id`: `SES-20260422-01`
- `title`: 为 `ASK_QA` 补 retrieval baseline 与 rank-based 指标面板
- `category`: `Retrieval`
- `priority`: `P1`
- `status`: `completed`
- `scope`: `medium`
- `goal`: 作为双层评测中的 retrieval layer，基于 `TASK-057` 的固定 `50` 条 query 数据集，把 ask benchmark 正式拆出 retrieval-only runner，先在 headline 子集 `38` 条 case 上建立 `fts_only / vector_only / hybrid_rrf` 三种 retrieval baseline，并以严格 locator 命中口径输出 `Recall@5 / Recall@10 / NDCG@10`，同时补齐 local-only preflight，使 retrieval benchmark 在本地 provider / model / index 未就绪时 fail-closed。
- `out_of_scope`:
  - 不评测生成答案质量
  - 不实现 rerank
  - 不扩展到 governance / digest
  - 不改 ask prompt、assembly 或 runtime gate 逻辑
- `acceptance_criteria`:
  - retrieval benchmark runner 能在统一 query 集上切换 `fts_only / vector_only / hybrid_rrf` 三种 retrieval mode
  - headline 只统计 `single_hop / multi_hop / metadata_filter` 且 `allow_tool=false` 的 `38` 条 case
  - 结果文件输出 query 级 `retrieved_candidates / matched_locator_ranks / hit_flags`，并聚合 `Recall@5 / Recall@10 / NDCG@10`
  - benchmark CLI 在本地 provider / model / vector index 未就绪时，于 preflight 阶段直接失败且不写半成品 artifact
  - 有最小测试覆盖指标计算、mode routing、preflight gating 与 FTS query normalization / hint-aware reranking 回归
- `depends_on`:
  - `TASK-057`
- `related_files`:
  - `eval/benchmark/run_retrieval_benchmark.py`
  - `backend/app/benchmark/ask_retrieval_benchmark.py`
  - `backend/app/benchmark/ask_retrieval_modes.py`
  - `backend/app/benchmark/ask_retrieval_metrics.py`
  - `backend/app/benchmark/ask_retrieval_preflight.py`
  - `backend/app/retrieval/sqlite_fts.py`
  - `backend/app/retrieval/sqlite_vector.py`
  - `backend/app/retrieval/hybrid.py`
  - `backend/tests/test_ask_retrieval_benchmark.py`
  - `backend/tests/test_ask_retrieval_cli.py`
  - `backend/tests/test_ask_retrieval_preflight.py`
  - `backend/tests/test_retrieval_fts.py`
  - `backend/tests/test_retrieval_vector.py`
  - `eval/benchmark/ask_benchmark_cases.json`
- `derived_tasks`:
  - `small: 为 retrieval benchmark 结果增加 query bucket 级聚合，识别哪类问题最吃 hybrid`
  - `small: 对当前 residual hybrid misses 做 failure taxonomy，并判断 query rewrite / chunking / path prior 的实际覆盖面`
- `notes`: `SES-20260422-01` 已完成本任务并合并到 `main`。当前 retrieval benchmark 已能在本地 provider 口径下稳定跑出正式 baseline；同时 [backend/app/retrieval/sqlite_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_fts.py) 已修复中文自然语言、日期 / 版本号 hint、pre-limit truncation 与 identifier-only query 的 FTS 命中问题。当前 headline baseline 为：`fts_only Recall@10=0.2368 / NDCG@10=0.2368`，`vector_only Recall@10=0.6842 / NDCG@10=0.4612`，`hybrid_rrf Recall@10=0.7895 / NDCG@10=0.5636`。这说明 retrieval layer 已经可以独立回答“vector / hybrid 是否真有收益”，当前主线应进入 `TASK-059`，而不是继续把 `TASK-058` 视作未完成 `medium`。

### TASK-059

- `task_id`: `TASK-059`
- `session_id`: `SES-20260424-02`
- `title`: 为 `ASK_QA` 建立真实 provider 的 answer benchmark 与 runtime gate trade-off 评测
- `category`: `Eval`
- `priority`: `P1`
- `status`: `completed`
- `scope`: `medium`
- `goal`: 在 `TASK-057 / TASK-058` 的固定 `50` 条 query 集与 retrieval baseline 之上，为 ask 主链路建立默认手动触发的真实 provider answer benchmark：固定 canonical provider / model 口径，让 ask 真走 `generated_answer` 路径，并比较 `hybrid`、`hybrid + context assembly`、`hybrid + context assembly + runtime faithfulness gate` 三种变体的质量收益与代价。
- `out_of_scope`:
  - 不实现 rerank
  - 不扩展到 governance / digest
  - 不接入在线 judge 平台
  - 不做多 provider / 多 model 横向对比
  - 不把真实 provider benchmark 接进日常 CI
- `acceptance_criteria`:
  - benchmark runner 提供独立于 regression run 的真实 provider ask benchmark 入口，并支持显式开关：`context_assembly_on_off` 与 `runtime_faithfulness_gate_on_off`
  - 同一批 query 上能稳定比较 `hybrid`、`hybrid + assembly`、`hybrid + assembly + gate`
  - 结果文件至少记录：`dataset_version / provider_name / model_name / prompt_version / run_timestamp / git_commit / vault_fixture_id / latency_ms / ask_result_mode / guardrail_reason`
  - 聚合输出至少包括：`faithfulness / answer_correctness / unsupported_claim_rate / generated_answer_rate / retrieval_only_rate / P50 latency / P95 latency`
  - 对允许触发工具的子集，额外输出至少：`tool_trigger_rate / expected_tool_hit_rate / tool_case_answer_correctness`
  - 有最小测试覆盖 benchmark 配置 gating、结果聚合与元数据落盘；真实 provider run 本身保持手动触发
- `depends_on`:
  - `TASK-057`
  - `TASK-058`
  - `TASK-052`
  - `TASK-049`
- `related_files`:
  - `eval/benchmark/run_answer_benchmark.py`
  - `eval/benchmark/ask_answer_benchmark_smoke_cases.json`
  - `backend/app/benchmark/ask_answer_benchmark.py`
  - `backend/app/benchmark/ask_answer_benchmark_scoring.py`
  - `backend/app/benchmark/ask_answer_benchmark_preflight.py`
  - `backend/app/benchmark/ask_answer_benchmark_variants.py`
  - `eval/README.md`
  - `backend/app/services/ask.py`
  - `backend/app/context/assembly.py`
  - `backend/app/quality/faithfulness.py`
  - `backend/app/tools/registry.py`
  - `backend/app/retrieval/sqlite_fts.py`
  - `backend/tests/test_ask_answer_benchmark.py`
  - `backend/tests/test_ask_answer_benchmark_scoring.py`
  - `backend/tests/test_ask_answer_benchmark_preflight.py`
  - `backend/tests/test_ask_answer_benchmark_cli.py`
  - `backend/tests/test_ask_workflow.py`
  - `backend/tests/test_faithfulness.py`
  - `backend/tests/test_retrieval_fts.py`
- `derived_tasks`:
  - `small: 为 answer ablation 结果补 token / cost 统计字段，便于后续写 trade-off 结论`
  - `small: 在成本可控时显式触发 full 50-case answer benchmark，并将结果与 smoke artifact 分开归档`
- `notes`: `SES-20260424-02` 已完成本任务的 v1 工程目标：新增独立 answer benchmark CLI，固定 `10` 条 smoke subset 与三种 variant（`hybrid` / `hybrid_assembly` / `hybrid_assembly_gate`），接真实 OpenAI-compatible provider 与 canonical model `qwen3.6-flash-2026-04-16`，让 ask 真走 `generated_answer` 路径，并输出 provider / model / prompt_version / git_commit / latency / mode / guardrail 等 artifact metadata。最终 smoke artifact 为 `/tmp/task-059-answer-benchmark-smoke-final-20260424.json`，`run_status=passed`，`selected_case_count=10`，三个 variant 的 `generated_answer_rate=1.0`、`retrieval_only_rate=0`、`unsupported_claim_rate=0`；规则 `answer_correctness` 分别为 `hybrid=0.65`、`hybrid_assembly=0.45`、`hybrid_assembly_gate=0.45`。这些数字只能说明 v1 runner 与真实 provider 链路已跑通，不能作为最终质量结论：当前规则正确性评分仍依赖字符串命中，可能误伤语义正确回答；runtime faithfulness gate 在本次 smoke 中也没有产生有效拦截。该评测解释缺口已拆为 `TASK-062` 的 LLM-as-judge semantic correctness 任务。

### TASK-062

- `task_id`: `TASK-062`
- `session_id`:
- `title`: 为 ask answer benchmark 接入 LLM-as-judge 语义正确性评分
- `category`: `Eval`
- `priority`: `P1`
- `status`: `planned`
- `scope`: `medium`
- `goal`: 在真实 provider answer benchmark 的 deterministic rule score 旁边新增可选 LLM-as-judge 语义正确性评分，让 benchmark 能区分“语义答对但字符串未连续命中”和“确实答错 / 漏答 / 编造”。最终 artifact 同时保留 `rule_correctness` 与 `judge_correctness`，用 rule score 做低成本 smoke / drift protection，用 judge score 作为分析装配层、检索策略与 runtime gate 改进价值的主要质量信号。
- `out_of_scope`:
  - 不把 LLM judge 接入 ask runtime 主链路或用户请求路径
  - 不删除现有规则判分，rule score 继续服务 CI smoke 与可重复基线
  - 不把 judge 扩展到 ingest / digest 场景
  - 不在本任务内调优检索、context assembly 或 runtime faithfulness gate
  - 不强制 full benchmark 每次都调用 judge；必须保留成本可控的显式开关
- `acceptance_criteria`:
  - 新增 judge prompt 与 prompt version，输入至少包含 `user_query`、`expected_facts`、`forbidden_claims`、`answer_text` 和可见 citations / snippets
  - judge 返回结构化 JSON，字段至少包含 `verdict: correct|partial|incorrect`、`matched_facts`、`missed_facts`、`unsupported_claims`、`reason`
  - benchmark artifact 同时输出规则判分与 judge 判分，variant aggregate 同时汇总 `rule_answer_correctness` 和 `judge_answer_correctness`
  - judge provider / model 可配置，并默认与生成模型解耦；本地无 key 或显式关闭 judge 时 benchmark 仍可只跑 rule score
  - judge JSON 解析失败、超时或 provider 不可用时 fail-soft，记录 `judge_status` 和原因，不覆盖 rule score
  - smoke 模式支持小样本 judge 验证；full 模式支持显式开关，避免无意产生高成本调用
  - 至少补齐 scoring / artifact / CLI / preflight 的单元测试，覆盖 judge 成功、partial、unsupported、parse failure 和 disabled 分支
  - 用 3～5 条既有 smoke case 人工抽样校准 judge 输出，确认它能修正规则判分的明显误伤
- `depends_on`:
  - `TASK-059`
- `related_files`:
  - `backend/app/benchmark/ask_answer_benchmark.py`
  - `backend/app/benchmark/ask_answer_benchmark_scoring.py`
  - `backend/app/benchmark/ask_answer_benchmark_preflight.py`
  - `backend/app/benchmark/ask_answer_benchmark_variants.py`
  - `eval/benchmark/run_answer_benchmark.py`
  - `eval/benchmark/ask_benchmark_cases.json`
  - `backend/tests/test_ask_answer_benchmark.py`
  - `backend/tests/test_ask_answer_benchmark_scoring.py`
  - `backend/tests/test_ask_answer_benchmark_preflight.py`
  - `backend/tests/test_ask_answer_benchmark_cli.py`
- `derived_tasks`:
  - `small: 建立 10 条以内的人审校准集，用于比较 rule score 与 judge score 的偏差`
  - `small: 对比 qwen-max / qwen-flash / deepseek judge 在同一 artifact 上的一致性和成本`
  - `small: 为 judge reason 增加稳定分类标签，便于后续定位装配层、检索层或模型生成层问题`
- `notes`: 旧 `TASK-060` 是 2026-04-18 设计中的人工校准 / 报告导出任务，后续已被 `TASK-061` 移出当前主线，本轮按用户判断从 active queue 删除。当前更紧迫的缺口是 answer benchmark 的 `answer_correctness` 仍主要依赖 normalized substring match，可能把语义正确但表述不连续的回答判错，也会污染 `hybrid`、`hybrid_assembly` 与 runtime gate 的对比解释。因此本任务使用新编号 `TASK-062`，避免复用已出现过的 `TASK-060` 语义。

### TASK-031

- `task_id`: `TASK-031`
- `session_id`:
- `title`: 为本地写回成功但 `/workflows/resume` 失败补跨会话恢复入口
- `category`: `Plugin`
- `priority`: `P2`
- `status`: `planned`
- `scope`: `medium`
- `goal`: 在插件已经能保留 `pendingWritebackResult` 的前提下，把“本地写回已成功但后端审计 / checkpoint 记账失败”的恢复入口从面板内存态提升为跨会话可恢复控制面。
- `out_of_scope`:
  - 不做后台自动重试或常驻同步守护进程
  - 不做自动回滚本地写回
  - 不处理多设备或多 Vault 间的冲突合并
- `acceptance_criteria`:
  - 本地写回成功但 resume 失败后，插件能持久化一条可恢复的待同步记录
  - 重启插件或重新打开面板后，用户仍可对这条记录执行“只同步后端审计 / checkpoint，不重复写回”
  - 后端会对 stale / mismatched proposal 做安全拒绝，避免错误补记
  - 有最小测试或构建验证覆盖持久化恢复与重复写回防护分支
- `depends_on`:
  - `TASK-019`
  - `TASK-030`
- `related_files`:
  - `plugin/src/views/KnowledgeStewardView.ts`
  - `plugin/src/main.ts`
  - `plugin/src/contracts.ts`
  - `plugin/src/writeback/applyProposalWriteback.ts`
  - `backend/app/services/resume_workflow.py`
  - `backend/app/main.py`
  - `backend/tests/test_resume_workflow.py`
- `derived_tasks`:
  - `small: 为跨会话待同步记录增加过期清理或“已同步”自动收口，避免本地恢复列表长期堆积`
- `notes`: 当前实现只在面板内存里保留 `pendingWritebackResult`；一旦插件重启或上下文丢失，用户就失去“只补后端记账、不重复执行 patch”的恢复入口。这个问题直接关系到审计可信度和副作用幂等，已经不适合继续放在 `small` 里。2026-03-17 在 `TASK-034` 中重新对齐《初步实现指南》后，本任务被明确后移：它不属于当前要先补齐的剩余 P0，也不属于当前只保留的前三个 P1，因此优先级降到 `P2`，待 guide-first MVP 首版收口后再推进。

### TASK-032

- `task_id`: `TASK-032`
- `session_id`:
- `title`: 为 scoped ingest 落地增量 FTS 同步策略
- `category`: `Retrieval`
- `priority`: `P2`
- `status`: `planned`
- `scope`: `medium`
- `goal`: 让 scoped ingest 不再每次都整库重建 `chunk_fts`，把 note 级同步真正收敛为“局部写库 + 局部 FTS 刷新”的可持续路径。
- `out_of_scope`:
  - 不接入向量索引或 hybrid retrieval
  - 不做完整性能 dashboard
  - 不顺手实现写回后自动触发 scoped ingest
- `acceptance_criteria`:
  - scoped ingest 只重建或刷新受影响 note / chunk 的 FTS 文档，而不是整库重建
  - 全量 ingest 入口仍保持可用，且不会因增量策略回退
  - FTS 查询在新增、替换和删除 chunk 后仍保持一致
  - 有最小测试覆盖 scoped ingest 下的 FTS 命中与旧文档清理
- `depends_on`:
  - `TASK-026`
- `related_files`:
  - `backend/app/indexing/store.py`
  - `backend/app/indexing/ingest.py`
  - `backend/app/retrieval/sqlite_fts.py`
  - `backend/tests/test_indexing_ingest.py`
  - `backend/tests/test_retrieval_fts.py`
- `derived_tasks`:
  - `small: 为 \`python -m app.indexing.ingest\` 增加 scoped 参数，便于脱离 API 复现增量 ingest`
  - `small: 为 scoped ingest 记录最小 FTS 刷新耗时，便于后续判断是否还需更细粒度优化`
- `notes`: `TASK-026` 虽然让 scoped ingest 真正可用了，但当前 `backend/app/indexing/ingest.py` 仍在任何 scoped note 更新后整库执行 `rebuild_chunk_fts_index(connection)`。在 scoped ingest 即将被写回链路复用的前提下，这已经不是单纯的“成本评估”问题，而是决定 scoped ingest 是否值得持续作为主路径使用的结构性问题。2026-03-17 在 `TASK-034` 中重新审视《初步实现指南》后，本任务被后移：当前 interview-first P0 先补向量检索、hybrid retrieval 和 eval baseline，更细的 FTS 增量同步留到之后处理。

### TASK-063

- `task_id`: `TASK-063`
- `session_id`:
- `title`: 抽取 `LLMWithToolsRunner` 通用 ReAct 层并切换 ask 链路使用 runner
- `category`: `Backend`
- `priority`: `P1`
- `status`: `planned`
- `scope`: `medium`
- `goal`: 把 [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py) 与 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py) 中既有的 ReAct 循环代码等价迁移为独立的 `LLMWithToolsRunner` 通用层，作为后续 skill 机制（`TASK-064` ~ `TASK-067`）的执行底座。本任务不改 ask 对外行为，不改 prompt，不改 contract；只把执行机制抽出来，让 skill_apply 和 ask 可以共享一份 ReAct 实现。
- `out_of_scope`:
  - 不引入 skill 概念或 skill 数据结构
  - 不修改 ask 对外 schema 或 prompt
  - 不引入 streaming
  - 不顺手重构既有 guardrail / faithfulness 链路
- `acceptance_criteria`:
  - 新增 `backend/app/runtime/llm_with_tools_runner.py`（或等价位置），承载 `LLMWithToolsRunner`
  - ask 链路切回到使用 runner 的实现，`tests.test_ask_workflow` 全套不回归
  - runner 提供独立单元测试，覆盖至少 4 个分支：normal exit、no tool call、tool error fallback、max rounds reached
  - runner 暴露的 trace hook 必须支持 caller 注入额外元数据（为下游 skill_apply 的 `skill_name / skill_version / decisions` 字段预留入口）
- `depends_on`:
  - `TASK-049`
  - `TASK-046`
- `related_files`:
  - `backend/app/graphs/ask_graph.py`
  - `backend/app/services/ask.py`
  - `backend/app/runtime/llm_with_tools_runner.py`
  - `backend/tests/test_ask_workflow.py`
  - `docs/superpowers/specs/2026-04-26-skill-mechanism-design.md`
- `derived_tasks`:
- `notes`: 这是 `2026-04-26 skill mechanism design` 的第 1 步，不抽 runner 后续 4 个任务都得自己复制一份 ReAct 代码，迁移阻力会扩散。spec 完整说明见 [docs/superpowers/specs/2026-04-26-skill-mechanism-design.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/superpowers/specs/2026-04-26-skill-mechanism-design.md) §5.3 与 §6.TASK-063；新会话先按 `project-session-governor` 流程读 governance 文档，再读 spec 中本 task 的 section。

### TASK-064

- `task_id`: `TASK-064`
- `session_id`:
- `title`: 引入 skill 数据结构、内置 demo skill 与 ingest `skill_apply` 节点骨架
- `category`: `Backend`
- `priority`: `P1`
- `status`: `planned`
- `scope`: `medium`
- `goal`: 在 `TASK-063` 抽出的 runner 之上，建立 skill 机制最小骨架：定义 `SkillSpec` 数据结构与 builtin skill loader / registry，新增 1 条无工具的 demo skill `frontmatter_completeness`，并在 [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py) 增加 `skill_apply` 节点把 demo skill 跑通，同时让 runner trace 输出 `skill_name / skill_version / selected_skills / per_skill_status`。本任务只做最小闭环，不放开工具调用，不迁移既有 governance 规则。
- `out_of_scope`:
  - 不引入 governance summary / dedup / LLM 二次筛
  - 不迁移既有 INGEST_STEWARD 硬编码 finding（在 `TASK-067` 完成）
  - 不放开 skill 的 tool 调用（`SkillSpec.allowed_tools` 在本任务内强制为空，runner 拒绝任何 tool 调用并落 trace）
  - 不实现 skill selector LLM；调用方显式传入 skill name 列表
  - 不实现用户自定义 skill 加载入口
- `acceptance_criteria`:
  - 新增 `backend/app/skills/` 模块，至少包含 `skill_spec.py` / `loader.py` / `registry.py`
  - `backend/app/skills/builtin/frontmatter_completeness/skill.md` 含完整 frontmatter（按 spec §5.1 字段）与 instruction body
  - 在 ingest 链路新增 `skill_apply` 节点，调用 runner 执行 demo skill，并写入 `frontmatter_missing` 类型 `GovernanceFinding`
  - runner 的 trace 必须包含 `skill_name / skill_version / selected_skills / per_skill_status`
  - 单元测试覆盖：skill loader、registry lookup、skill_apply 节点的成功 / 失败 / fail-soft 分支
  - ingest 链路既有测试不回归
- `depends_on`:
  - `TASK-063`
- `related_files`:
  - `backend/app/skills/skill_spec.py`
  - `backend/app/skills/loader.py`
  - `backend/app/skills/registry.py`
  - `backend/app/skills/builtin/frontmatter_completeness/skill.md`
  - `backend/app/graphs/ingest_graph.py`
  - `backend/app/contracts/workflow.py`
  - `backend/app/services/ingest_proposal.py`
  - `backend/tests/test_ingest_workflow.py`
  - `docs/superpowers/specs/2026-04-26-skill-mechanism-design.md`
- `derived_tasks`:
- `notes`: 这是 `2026-04-26 skill mechanism design` 的第 2 步。trace 字段（来自原拟 `TASK-068` 的 trace 部分）已并入本任务，避免单独留 small。spec 完整说明见 [docs/superpowers/specs/2026-04-26-skill-mechanism-design.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/superpowers/specs/2026-04-26-skill-mechanism-design.md) §5.1 / §5.3 与 §6.TASK-064。

### TASK-065

- `task_id`: `TASK-065`
- `session_id`:
- `title`: 落地 v1 全量：3 条无工具 governance / review skill + governance_summary / digest_summary 节点
- `category`: `Backend`
- `priority`: `P1`
- `status`: `planned`
- `scope`: `medium`
- `goal`: 在 `TASK-064` 的骨架之上完成 v1 完整闭环：新增 3 条无工具内置 skill（`structural_governance` / `content_leftover_tasks` / `weekly_review_summary`），在 ingest 链路加 `governance_summary` 节点、digest 链路加 `digest_summary` 节点，按 spec §5.4 实现「dedup → LLM 二次筛 → raw_findings + governance_report_markdown 双产出」，并保证 LLM summary 失败时 fail-soft 不阻塞 proposal 流程。
- `out_of_scope`:
  - 不放开 skill 的 tool 调用（`TASK-066` 完成）
  - 不迁移既有 INGEST_STEWARD 硬编码 finding（`TASK-067` 完成）
  - 不重构 digest 整体形态；本任务只插入 summary 节点
  - 不在插件层做 UI 集成
  - 不引入外部 LLM judge / scorer
- `acceptance_criteria`:
  - 新增 `backend/app/skills/builtin/structural_governance/skill.md`、`content_leftover_tasks/skill.md`、`weekly_review_summary/skill.md`，每条 skill 都有最小快照测试
  - ingest 链路新增 `governance_summary` 节点，输出 `raw_findings: list[GovernanceFinding]`、`governance_report_markdown: str`、`summary_status: ok|failed|skipped`
  - digest 链路新增 `digest_summary` 节点，复用 governance summary 实现（仅工作流标签不同）
  - LLM summary 失败、超时或 JSON 解析失败时 fail-soft，保留 raw findings 并标 `summary_status=failed`
  - `structural_governance` 仅基于显式存在 link 字段判断出入链缺失，不做相关性推断
  - proposal builder 仍只消费 raw findings 的 keep 集合，HITL 链路不被绕过
  - 单元测试覆盖：3 条 skill 的最小快照 + summary 节点的 ok / failed / skipped 三个分支
  - ingest / digest 链路既有测试不回归
- `depends_on`:
  - `TASK-064`
- `related_files`:
  - `backend/app/skills/builtin/structural_governance/skill.md`
  - `backend/app/skills/builtin/content_leftover_tasks/skill.md`
  - `backend/app/skills/builtin/weekly_review_summary/skill.md`
  - `backend/app/graphs/ingest_graph.py`
  - `backend/app/graphs/digest_graph.py`
  - `backend/app/services/ingest_proposal.py`
  - `backend/app/services/digest.py`
  - `backend/app/contracts/workflow.py`
  - `backend/tests/test_ingest_workflow.py`
  - `backend/tests/test_digest_workflow.py`
  - `docs/superpowers/specs/2026-04-26-skill-mechanism-design.md`
- `derived_tasks`:
- `notes`: 这是 `2026-04-26 skill mechanism design` 的第 3 步，本任务结束后 v1 闭环完成。spec 完整说明见 [docs/superpowers/specs/2026-04-26-skill-mechanism-design.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/superpowers/specs/2026-04-26-skill-mechanism-design.md) §5.4 与 §6.TASK-065。

### TASK-066

- `task_id`: `TASK-066`
- `session_id`:
- `title`: 放开 skill 的工具调用，落地 1 条 tool-using skill `related_notes_linker`
- `category`: `Backend`
- `priority`: `P1`
- `status`: `planned`
- `scope`: `medium`
- `goal`: 把 skill 从「LLM-only」升级为「LLM + 受限工具」，按 `SkillSpec.allowed_tools` 落地工具白名单，复用 ask 既有的 `search_notes` / `load_note_excerpt`，并新增一个 `search_related_notes` 工具（基于 hybrid retrieval，输入是笔记内容片段），让 `related_notes_linker` 能基于检索结果产出带 evidence 的 `missing_inbound_link` finding。
- `out_of_scope`:
  - 不引入用户自定义 skill 加载入口
  - 不引入 skill selector LLM；调用方仍显式传入 skill name 列表
  - 不修改既有 ask 工具的 schema
  - 不重构 hybrid retrieval 的对外接口
- `acceptance_criteria`:
  - `SkillSpec.allowed_tools` 在 runner 调用前被解析为 scoped tool registry view，**不**修改全局 `TOOL_REGISTRY`
  - 越权工具调用被 runner 拒绝并落 trace
  - 新增 `search_related_notes` 工具按 ask 既有 ToolSpec 风格定义，read_only 为 True
  - 新增 `backend/app/skills/builtin/related_notes_linker/skill.md`，allowed_tools 至少包含 `search_notes` / `load_note_excerpt` / `search_related_notes`
  - `related_notes_linker` 在 sample_vault 上能产出至少 1 条 `missing_inbound_link` finding，并附带 evidence chunk 引用
  - `governance_summary` 增加对带 evidence_chunk 的 finding 的 markdown 锚点展示规范
  - 单元测试覆盖：scoped registry 拒绝越权工具、tool-using skill 在 max_rounds 内正常收敛、finding payload 结构、`search_related_notes` 工具
  - backend 测试不回归
- `depends_on`:
  - `TASK-065`
- `related_files`:
  - `backend/app/skills/registry.py`
  - `backend/app/skills/builtin/related_notes_linker/skill.md`
  - `backend/app/tools/registry.py`
  - `backend/app/tools/ask_tools.py`
  - `backend/app/retrieval/hybrid.py`
  - `backend/app/runtime/llm_with_tools_runner.py`
  - `backend/app/graphs/ingest_graph.py`
  - `backend/tests/test_ingest_workflow.py`
  - `backend/tests/test_ask_tools.py`
  - `docs/superpowers/specs/2026-04-26-skill-mechanism-design.md`
- `derived_tasks`:
- `notes`: 这是 `2026-04-26 skill mechanism design` 的第 4 步。spec 完整说明见 [docs/superpowers/specs/2026-04-26-skill-mechanism-design.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/superpowers/specs/2026-04-26-skill-mechanism-design.md) §5.3 与 §6.TASK-066。

### TASK-067

- `task_id`: `TASK-067`
- `session_id`:
- `title`: 迁移 INGEST_STEWARD 现有硬编码 governance 到 skill 体系并补 governance skill benchmark
- `category`: `Backend`
- `priority`: `P1`
- `status`: `planned`
- `scope`: `medium`
- `goal`: 把 [backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py) 中现有的硬编码 governance finding（缺 frontmatter / 缺标题 / 缺出入链 / 遗留任务等）等价迁移到 `structural_governance` + `content_leftover_tasks` + `related_notes_linker` 三条 skill；同时新增 `governance_skill_benchmark_cases.json`（5 ~ 10 条 case）作为 governance skill 的最小回归数据集，确保 skill 化之后行为不退化。
- `out_of_scope`:
  - 不顺手重写 proposal validator
  - 不顺手扩 benchmark runner 的指标维度（仅落 dataset，不强制接 CI）
  - 不删除旧函数对外签名（保留为薄壳委托给 skill，待回归稳定后再做单独 deprecation 任务）
- `acceptance_criteria`:
  - 旧硬编码 governance 路径的所有既有 backend 测试通过（行为等价）
  - 新增 `eval/benchmark/governance_skill_benchmark_cases.json`，含 5 ~ 10 条 case，覆盖每条 skill 至少一条正例 + 一条反例
  - 新增 schema 校验测试，确保 benchmark dataset 结构稳定
  - ingest / digest 端到端冒烟在 sample_vault 上稳定输出 `raw_findings` + `governance_report_markdown`
  - `docs/PROJECT_MASTER_PLAN.md` 中关于 INGEST_STEWARD governance 来源的描述被更新
- `depends_on`:
  - `TASK-066`
- `related_files`:
  - `backend/app/services/ingest_proposal.py`
  - `backend/app/skills/builtin/structural_governance/skill.md`
  - `backend/app/skills/builtin/content_leftover_tasks/skill.md`
  - `backend/app/skills/builtin/related_notes_linker/skill.md`
  - `backend/app/graphs/ingest_graph.py`
  - `eval/benchmark/governance_skill_benchmark_cases.json`
  - `backend/tests/test_ingest_proposal.py`
  - `backend/tests/test_governance_skill_benchmark.py`
  - `docs/PROJECT_MASTER_PLAN.md`
  - `docs/superpowers/specs/2026-04-26-skill-mechanism-design.md`
- `derived_tasks`:
  - `small: 待 governance skill 在真实 vault 上稳定运行后，单独开任务做旧 ingest_proposal 函数的 deprecation 与签名清理`
- `notes`: 这是 `2026-04-26 skill mechanism design` 的第 5 步，也是 v2 完成后的收口任务。benchmark dataset 字段（来自原拟 `TASK-068` 的 eval 部分）已并入本任务。spec 完整说明见 [docs/superpowers/specs/2026-04-26-skill-mechanism-design.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/superpowers/specs/2026-04-26-skill-mechanism-design.md) §6.TASK-067。
