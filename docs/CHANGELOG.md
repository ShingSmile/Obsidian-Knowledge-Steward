# CHANGELOG

本文件承载项目版本变更记录。

稳定架构、模块边界、ADR 与长期设计说明继续以 [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 为准。

| 版本 | 日期 | 变更人 | 变更内容 |
| --- | --- | --- | --- |
| v0.2.51 | 2026-03-28 | qingfeng Qi | 推进 `TASK-045` 第一阶段：为 ask 新增 `get_note_outline`、fail-closed `find_backlinks` 与 verified-only tool reentry，在插件侧落地 `replace_section / add_wikilink`、补 proposal 静态校验接线与相关回归测试，并将实现合入本地 `main`；同时撤回会话中临时引入的 `docs/` 忽略策略，恢复治理文档的正常版本化路径。当前 `TASK-045` 仍未完全收口，剩余缺口是 proposal persistence validator 对新 patch op 的正式支持。 |
| v0.2.50 | 2026-03-27 | qingfeng Qi | 完成 `TASK-044`：将 ask / ingest / digest 正常路径的 checkpoint 持久化迁移到 LangGraph `SqliteSaver`，让 graph state 落到 SQLite `checkpoints` / `writes`，同时保留 `workflow_checkpoint` 的业务元数据 / 恢复策略层；补齐 serializer allowlist、warning-free completed resume 回归、`checkpoints` 表落盘测试，移除 `_CompiledStateGraph` / `LANGGRAPH_AVAILABLE` / `used_langgraph` / 旧线性 runner，并将实现提交 `e214bd7` 合并回 `main`。 |
| v0.2.49 | 2026-03-23 | qingfeng Qi | 完成 `TASK-043`：新增 [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md)，拆出 [docs/INTERVIEW_PLAYBOOK.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/INTERVIEW_PLAYBOOK.md) 与本文件，进一步将 README 收敛到“项目介绍 / 运行方式 / 演示入口 / 文档导航”，把主文档顶部高波动控制面移出，并将会话历史按月归档到 [docs/archive/session_logs/SESSION_LOG_2026-03.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/archive/session_logs/SESSION_LOG_2026-03.md)。 |
| v0.2.48 | 2026-03-23 | qingfeng Qi | 登记 `TASK-043`：将文档控制面分层与归档治理正式纳入任务队列，并确认后续拆分目标包含 `docs/CURRENT_STATE.md`、`docs/INTERVIEW_PLAYBOOK.md`、`docs/CHANGELOG.md` 与 archive 结构；本次仅完成任务登记与范围锁定，尚未执行实际迁移。 |
| v0.2.47 | 2026-03-18 | qingfeng Qi | 完成 `TASK-042`：统一 ask / digest / ingest 的入口路由与共享 workflow contract，在 `backend/app/graphs/runtime.py` 中新增共享 `WorkflowGraphExecution` / 基础 state / runtime trace hook 组装，并让 `backend/app/main.py` 的 `/workflows/invoke` 改为 handler registry + 统一 outcome/response builder；同时把主线路线从“下一步执行 `TASK-042`”更新为“interview-first 保留主线已收口，若继续开发默认回到 `TASK-031` 到 `TASK-033`”。 |
| v0.2.46 | 2026-03-18 | qingfeng Qi | 完成 `TASK-041`：为当前受限 patch op 落地最小 rollback，新增插件本地 `LocalRollbackContext` 快照、`POST /workflows/rollback`、rollback 审计记账与 checkpoint 持久化，并把主线路线从 `TASK-041` 前移到 `TASK-042`。 |
| v0.2.45 | 2026-03-18 | qingfeng Qi | 完成 `TASK-040`：将离线 eval 从全局 `metric_overview` 升级为 `question_answering / governance` 两套分场景 benchmark，新增 `schema_version=1.3`、`benchmark_overview`、场景级 `core_metrics` 与最小 `failure_type_breakdown`，并把主线路线从 `TASK-040` 前移到 `TASK-041`。 |
| v0.2.44 | 2026-03-18 | qingfeng Qi | 完成 `TASK-039`：将离线 eval 升级到 interview-first P0 基线，把 golden set 从 13 条扩到 18 条，新增 governance suite、`schema_version=1.2`、最小 `quality_metrics` 与 `metric_overview`，并把主线路线从“剩余最后一个 P0”前移到 `TASK-040`。 |
| v0.2.43 | 2026-03-18 | qingfeng Qi | 完成 `TASK-038`：新增 `backend/app/retrieval/hybrid.py`，用 RRF 融合 FTS 与 `sqlite_vector` 并接入 ask / `INGEST_STEWARD` 的 related retrieve，同时同步修正主文档与 README 中仍把 hybrid retrieval 写成“未开始”或把 `TASK-038` 视为“下一步待做”的过时事实。 |
| v0.2.42 | 2026-03-18 | qingfeng Qi | 完成 `TASK-037`：为 chunk 索引补最小 embedding 写入与 `sqlite_vector` 检索入口，在 SQLite schema 中新增 `chunk_embedding` 持久化、provider 不可用 / 向量索引未就绪禁用语义，并同步修正主文档与 README 中仍把 `TASK-037` 视为“下一步待做”或把检索底座写成“只有 FTS”的过时事实。 |
| v0.2.41 | 2026-03-18 | qingfeng Qi | 完成 `TASK-036`：为插件补齐 backend runtime 控制，支持用户提供启动命令后的最小本地自启、`/health` readiness probe、启动状态展示与失败降级提示，并同步修正主文档与 README 中仍把 `TASK-036` 视为“下一步待做”或仍按手工分终端启动描述插件能力的过时事实。 |
| v0.2.40 | 2026-03-18 | qingfeng Qi | 完成 `TASK-035`：让 `INGEST_STEWARD` 在单 note scoped proposal 路径上接入基于 SQLite FTS 的 retrieval-backed analyze，新增结构化 `analysis_result`、跨 note evidence 与 target-note self-match 排除，并同步修正主文档与 README 中仍把 `TASK-035` 视为“下一步待做”或把治理分析写成设计态 hybrid/LLM 的过时描述。 |
| v0.2.39 | 2026-03-17 | qingfeng Qi | 完成 `TASK-030`：让 `/workflows/resume` 在 successful writeback 后自动触发 scoped ingest，并通过结构化 `post_writeback_sync` 返回刷新成功 / 失败结果，同时同步修正主文档与 README 中仍把 `TASK-030` 视为“下一步待做”的过时描述。 |
| v0.2.38 | 2026-03-17 | qingfeng Qi | 继续补全 `TASK-034` 的面试叙事同步：在原主文档问答库中新增“为什么当前不继续推进 `TASK-031` 到 `TASK-033`”与“为什么基础 tracing 不再单独立 P0”两条关键追问，防止路线回正后面试口径仍停留在旧优先级。 |
| v0.2.37 | 2026-03-17 | qingfeng Qi | 补全 `TASK-034` 的文档收尾：修正文内仍残留的旧 `Next Action` 路线，明确“基础 tracing 已达 interview-first P0 下限”，并同步补记 `SES-20260317-05` 的路线校正结论。 |
| v0.2.36 | 2026-03-17 | qingfeng Qi | 完成 `TASK-034`：根据《初步实现指南》的 interview-first MVP 重新校正优先级，把后续主线收敛为“剩余 P0 全部补齐，再只做前三个 P1”，新增 `TASK-035` 到 `TASK-042`，并将 `TASK-031` 到 `TASK-033` 后移。 |
| v0.2.35 | 2026-03-17 | qingfeng Qi | 完成 `TASK-029`：基于真实代码状态新增 `TASK-030` 到 `TASK-033`，把后续主线收敛为 post-writeback scoped ingest 同步、写回后跨会话恢复、scoped ingest 增量 FTS 同步与 ask runtime groundedness gate，并同步修正主文档、README 与 `eval/README.md` 中仍指向 `TASK-029` 或旧 eval 计划的过时描述。 |
| v0.2.34 | 2026-03-17 | qingfeng Qi | 完成 `TASK-028`：在 `eval/run_eval.py` 中新增 ask `ask_groundedness` / `unsupported_claim` 离线分桶、deterministic semantic overclaim bad case 与 eval runner 断言，补齐“编号合法但语义越界”的最小回归基线，并将主线路线从 `TASK-028` 前移到 `TASK-029`。 |
| v0.2.33 | 2026-03-17 | qingfeng Qi | 完成 `TASK-027`：新增 `backend/app/services/ingest_proposal.py`，让 `INGEST_STEWARD` 在显式 proposal 模式下为单 note scoped ingest 产出首条规则驱动治理 proposal，补齐 waiting checkpoint 原子落盘、pending inbox 兼容、no-proposal fallback 与 waiting thread 恢复边界，并将主线路线从 `TASK-027` 前移到 `TASK-028`。 |
| v0.2.32 | 2026-03-17 | qingfeng Qi | 完成 `TASK-026`：让 `INGEST_STEWARD` 支持 `note_path / note_paths` scoped note ingest，补齐 vault 内路径校验、scope-aware checkpoint resume miss 与 scoped/full-vault 消息分流，并将主线路线从 `TASK-026` 前移到 `TASK-027`。 |
| v0.2.31 | 2026-03-16 | qingfeng Qi | 完成 `TASK-025`：新增 `GET /workflows/pending-approvals`、基于 `workflow_checkpoint.waiting_for_approval + proposal` 的 pending proposal 查询 helper，以及插件侧最小待审批收件箱与 stale proposal 提示，并将主线路线从 `TASK-025` 前移到 `TASK-026`。 |
| v0.2.30 | 2026-03-16 | qingfeng Qi | 完成 `TASK-024`：在 `eval/run_eval.py` 中新增 `resume` entrypoint、deterministic waiting proposal fixture 与 checkpoint / `audit_log` 断言，补齐 `resume_workflow + writeback_result` 的最小离线回归，并将主线路线从 `TASK-024` 前移到 `TASK-025`。 |
| v0.2.29 | 2026-03-16 | qingfeng Qi | 完成 `TASK-023` 的队列治理收尾：基于真实代码状态新增 `TASK-024` 到 `TASK-028`，把后续主线收敛为 `writeback/resume` 离线回归、待审批收件箱、scoped ingest、`INGEST_STEWARD` proposal 化与 ask 语义级 groundedness eval，并同步修正主文档中仍指向 `TASK-023` 的过时 `Next Action`。 |
| v0.2.28 | 2026-03-15 | qingfeng Qi | 新增 `eval/run_eval.py`、ask / digest 两套最小 golden case 与 `backend/tests/test_eval_runner.py`，让项目具备可重复执行、可落结果文件的最小离线回归基线，并同步修正主文档 / README 中“eval 仍是目录空壳”的过时描述。 |
| v0.2.27 | 2026-03-15 | qingfeng Qi | 在 `backend/app/services/ask.py` 中为 `generated_answer` 增加程序级 citation 对齐校验：缺引用、越界编号或与当前候选集合编号不对齐时自动降级为 `retrieval_only`，并补齐 ask bad case 测试与主文档 / README 同步。 |
| v0.2.26 | 2026-03-15 | qingfeng Qi | 新增 `plugin/src/writeback/applyProposalWriteback.ts` 与 `plugin/src/writeback/helpers.ts`，让插件在 approval 通过后可执行 `merge_frontmatter` / `insert_under_heading` 两类受限写回、校验 `before_hash` 并产出真实 `writeback_result`；同时扩展 `backend/app/services/resume_workflow.py` 接收并持久化该结果，补齐 resume 测试、插件纯函数测试、TS 类型检查与 README / 主文档同步。 |
| v0.2.25 | 2026-03-15 | qingfeng Qi | 让 `backend/app/graphs/digest_graph.py` 在显式 proposal 模式下真实产出 `proposal + waiting_for_approval checkpoint`，并通过 `plugin/src/main.ts` 中的 `Load daily digest approval` 命令把 `thread_id / proposal / proposal_id` 真实注入审批面板；同时补齐 waiting proposal 测试与 README / 主文档同步。 |
| v0.2.24 | 2026-03-15 | qingfeng Qi | 在 `plugin/src/views/KnowledgeStewardView.ts` 中落地插件审批面板与最小 diff 预览骨架，支持 reviewer/comment、approve/reject 与后端异常展示；同时在 `plugin/src/main.ts` 中增加本地 demo proposal 入口，在 `plugin/src/api/client.ts` 中补齐 error detail / timeout 映射，并通过 `npm run build` 完成插件构建验证。 |
| v0.2.23 | 2026-03-14 | qingfeng Qi | 新增 `POST /workflows/resume` 与 `backend/app/services/resume_workflow.py`，把 `thread_id / proposal_id / approval_decision` 的审批恢复控制面接到 SQLite `workflow_checkpoint`、`proposal` 与 append-only `audit_log`；同时将 `workflow_checkpoint` schema 升到 `v6` 支持 `waiting_for_approval`，并补齐插件 resume contract 与恢复测试。 |
| v0.2.22 | 2026-03-14 | qingfeng Qi | 在 `backend/app/indexing/store.py` 中把 schema 升到 `v5`，新增 `proposal`、`proposal_evidence`、`patch_op` 与 append-only `audit_log` 表，并补最小 proposal / audit 持久化 helper 与测试，关闭主文档中“proposal schema / audit_log 尚未开始”的状态漂移。 |
| v0.2.21 | 2026-03-14 | qingfeng Qi | 新增 `backend/app/services/digest.py` 与 `backend/app/graphs/digest_graph.py`，让 `/workflows/invoke` 的 `daily_digest` 返回最小结构化 `digest_result`、`source_notes` 和安全 fallback，同时把 digest 纳入现有 JSONL + SQLite `run_trace` 与 SQLite `workflow_checkpoint` 语义。 |
| v0.2.20 | 2026-03-14 | qingfeng Qi | 新增 `backend/app/graphs/checkpoint.py`、SQLite `workflow_checkpoint` 表与 ask / ingest 共用的 checkpoint runner，让 `/workflows/invoke` 支持基于显式 `thread_id` 的最小恢复协议，并同步修正主文档中“checkpoint 尚未开始”的状态漂移。 |
| v0.2.19 | 2026-03-14 | qingfeng Qi | 新增 `backend/app/graphs/ingest_graph.py` 与共享 `backend/app/graphs/runtime.py`，让 `/workflows/invoke` 的 `INGEST_STEWARD` 进入最小 ingest graph、返回结构化 `ingest_result`，并复用 JSONL + SQLite `run_trace` 的多 graph 最小 runtime trace。 |
| v0.2.18 | 2026-03-14 | qingfeng Qi | 继续将主计划拆解到 `docs/TASK_QUEUE.md`：新增 `TASK-013` 到 `TASK-021`，把 Phase 3/4/5 的下一批可执行工作显式登记进队列，并将主文档的下一步动作收敛到 `TASK-013`。 |
| v0.2.17 | 2026-03-14 | qingfeng Qi | 在 `backend/app/indexing/store.py` 与 `backend/app/observability/runtime_trace.py` 中落地 SQLite `run_trace` 聚合表、最小查询 helper 与 CLI，并让 ask graph 默认双写 JSONL + SQLite trace。 |
| v0.2.16 | 2026-03-14 | qingfeng Qi | 新增 `backend/app/observability/runtime_trace.py` 与 ask runtime trace JSONL 持久化骨架，让 ask graph 默认写出本地 JSONL trace，并在写盘失败时保持 ask 主链路可降级继续执行。 |
| v0.2.15 | 2026-03-14 | qingfeng Qi | 新增 `backend/app/graphs/ask_graph.py`，让 `/workflows/invoke` 的 `ask_qa` 先进入最小 ask graph，再统一 `thread_id` / `run_id` 与内存态 trace event；同时补齐 `langgraph` 依赖声明与相关测试。 |
| v0.2.14 | 2026-03-14 | qingfeng Qi | 在 `backend/app/services/ask.py` 与 `backend/app/main.py` 中落地最小 ask 引用式返回链路，让 `/workflows/invoke` 的 `ask_qa` 支持真实 `ask_result`、citation 和 retrieval/model 双层 fallback，并同步修正文档中“最小 ask 尚未开始”的状态漂移。 |
| v0.2.13 | 2026-03-14 | qingfeng Qi | 在 `backend/app/contracts/workflow.py` 与 `backend/app/retrieval/sqlite_fts.py` 中新增 metadata filter、标准 candidate 输出与 filter fallback，并修正主文档中“检索层仍未实现”的状态漂移。 |
| v0.2.12 | 2026-03-14 | qingfeng Qi | 新增 `backend/app/retrieval/sqlite_fts.py`，落地 SQLite FTS5 虚表、top-k chunk candidate 查询与 snippet 输出，并让 ingest 在写库后统一重建 FTS 索引。 |
| v0.2.11 | 2026-03-14 | qingfeng Qi | 新增 `backend/app/indexing/ingest.py` 与 note 级 replace/upsert 事务，跑通 `sample_vault/` 全量写库、重复执行幂等覆盖和 ingest 测试。 |
| v0.2.10 | 2026-03-12 | qingfeng Qi | 新增 `backend/app/indexing/store.py`，落地 `note/chunk` SQLite schema、最小迁移入口与 schema 对齐测试，并修正主计划中“schema 尚未开始”的状态漂移。 |
| v0.2.9 | 2026-03-12 | qingfeng Qi | 在“后续维护规则”中新增代码实现与中文注释要求，明确后续代码开发需补充必要的中文注释。 |
| v0.2.8 | 2026-03-12 | qingfeng Qi | 完成 `python -m app.main` 与 `/health` 的真实运行验证，关闭 `TASK-003`，并同步修正 `sample_vault` 任务统计与运行状态描述。 |
| v0.2.7 | 2026-03-12 | qingfeng Qi | 在原主文档“面试问答库”章节前新增统一角色设定，明确后续所有面试相关输出必须使用大厂资深大模型应用工程师兼高级面试官视角。 |
| v0.2.6 | 2026-03-12 | qingfeng Qi | 新增 `backend/environment.yml` 与 `python -m app.main` 统一后端启动入口，将 README 收敛到工作区本地 conda prefix，并补记本次未完成的非沙箱运行验证限制。 |
| v0.2.5 | 2026-03-12 | qingfeng Qi | 将主文档中的会话级任务明细迁移到 `docs/TASK_QUEUE.md`，使 `PROJECT_MASTER_PLAN.md` 保持架构主文档定位，并把所有会话任务绑定规则统一改为引用独立任务队列。 |
| v0.2.4 | 2026-03-11 | qingfeng Qi | 引入会话级执行规则：新增 `docs/SESSION_LOG.md` 的唯一会话 ID 规范，并在主文档中按“一个会话一个中等粒度问题”拆分近期实现任务。 |
| v0.2.3 | 2026-03-11 | qingfeng Qi | 继续做增量同步：修正“当前事实边界”仍按空仓描述的问题，补充环境漂移与云 provider 风险，更新 Phase 状态、图层/评估层实现状态，并新增本次代码改动带来的面试追问点。 |
| v0.2.2 | 2026-03-11 | qingfeng Qi | 基于本次代码改动同步主文档：修正“已有码骨架却仍标注未实现”的不一致，更新开发阶段、模块状态、路线图状态、风险、ADR 与面试问答。 |
| v0.2.1 | 2026-03-11 | qingfeng Qi | 新增首版 Markdown 解析器与样例笔记分类器，已能从 `sample_vault/` 推断 `daily_note / summary_note`、标题路径、任务数与 wikilink。 |
| v0.2.0 | 2026-03-11 | qingfeng Qi | 新增仓库基线代码：`backend/`、`plugin/`、`eval/`、`README.md`、核心协议模型与 `/health` 探活接口；引入 `references/ObsidianRAG/` 作为只读参考实现。 |
| v0.1.1 | 2026-03-11 | qingfeng Qi | 锁定双端架构与模型路线，纳入 `sample_vault/` 的真实样本统计，并调整首版索引、复盘与评估优先级。 |
| v0.1.0 | 2026-03-11 | qingfeng Qi | 基于当前空仓现状与《Obsidian Knowledge Steward 项目初步实现指南》创建项目主文档，并补齐目录事实、自检修正、Gap Analysis、路线图、ADR、风险与面试问答库。 |
