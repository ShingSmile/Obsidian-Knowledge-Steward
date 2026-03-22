# Obsidian Knowledge Steward

基于 LangGraph 的个人学习知识治理与复盘 Agent。

当前仓库状态已经从“只有设计文档的空仓”推进到“有主文档、有示例 Vault、有插件/后端基线骨架”的阶段，但还没有完成完整功能实现。当前最重要的目标不是堆功能，而是先稳定以下基线：

- Obsidian 插件与本地后端的双端架构
- 云模型优先、本地模型兼容的 provider 抽象
- 可扩展的工作流状态、proposal、patch、audit 协议
- 基于 `sample_vault/` 的首版索引、复盘和评估样本

## 当前优先级提醒

虽然具体实现与验收仍以 [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 和当前代码事实为准，但项目的 interview-first north star 仍然对齐 [Obsidian Knowledge Steward 项目初步实现指南.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/Obsidian%20Knowledge%20Steward%20项目初步实现指南.md)。`TASK-040`、`TASK-041`、`TASK-042` 已完成，因此当前剩余 P0 与保留 P1 都已清空；若继续推进 medium，默认回到已后移的 `TASK-031`、`TASK-032`、`TASK-033`。其他优化项继续后移。

## 当前目录

```text
.
├── backend/          # FastAPI + contracts + graph state baseline
├── docs/             # 项目主文档（single source of truth）
├── eval/             # golden set 与评估结果目录
├── plugin/           # Obsidian plugin baseline
├── sample_vault/     # 示例 Vault
└── data/             # 本地运行时数据目录
```

## 当前已落地的基线

- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)
- `backend/app/main.py` 已提供 `/health`、`/workflows/invoke`、`/workflows/resume`、`/workflows/rollback` 与 `GET /workflows/pending-approvals`；其中 `/workflows/invoke` 已通过 handler registry + 统一 invoker / outcome / response builder 收敛 ask / ingest / digest 三条入口
- `backend/app/contracts/workflow.py` 固化核心协议模型
- `backend/app/graphs/state.py` 固化首版状态 schema
- `backend/app/graphs/runtime.py` 已提供共享 `WorkflowGraphExecution`、基础 workflow state、runtime trace hook 与 checkpoint 执行上下文组装，ask / ingest / digest wrapper 统一复用这套 runtime contract
- `backend/app/indexing/store.py` 与 `backend/app/indexing/ingest.py` 已可初始化 SQLite schema，并支持 `sample_vault/` 全量 ingest、scoped note ingest 与 `chunk_embedding` 的 best-effort 写入
- `backend/app/retrieval/sqlite_fts.py` 已可基于 SQLite FTS5 返回带 metadata filter / fallback 的标准 chunk candidate
- `backend/app/retrieval/embeddings.py` 与 `backend/app/retrieval/sqlite_vector.py` 已补最小 embedding provider 路由、SQLite `chunk_embedding` 持久化后的向量检索入口，以及 provider 不可用 / 索引未就绪时的显式禁用语义
- `backend/app/retrieval/hybrid.py` 已用 RRF 融合 FTS 与向量检索，统一 metadata filter fallback、重复 chunk 去重与 `hybrid_rrf` candidate 输出；向量分支不可用时会稳定退回现有 FTS 路径
- `backend/app/services/ask.py` 已可复用 hybrid candidate，在 `/workflows/invoke` 的 `ask_qa` 中返回最小引用式响应，并在模型不可用、缺少引用编号或引用越界时退回 `retrieval_only`
- `backend/app/graphs/ask_graph.py` 已让 ask 从普通 API 分支升级为最小 graph 入口，并贯通 `thread_id` / `run_id` 与 runtime trace event
- `backend/app/graphs/ingest_graph.py` 与 `backend/app/services/ingest_proposal.py` 已让 `ingest_steward` 进入最小 graph 入口，支持 `note_path / note_paths` scoped sync，并可在显式 proposal 模式下为单 note scoped ingest 产出 retrieval-backed `analysis_result`、基于 hybrid related retrieve 的跨 note evidence、真实 `proposal + waiting_for_approval checkpoint`
- `backend/app/graphs/digest_graph.py` 已让 `daily_digest` 返回结构化 `digest_result`，并可在显式 proposal 模式下产出真实 `proposal + waiting_for_approval checkpoint`
- `backend/app/observability/runtime_trace.py` 已让 ask / ingest / digest graph 默认把 runtime trace 同时写入 `data/traces/ask_runtime.jsonl` 与 SQLite `run_trace`，并支持按 `run_id` / `thread_id` 做最小查询
- `backend/app/graphs/checkpoint.py` 与 `backend/app/indexing/store.py` 已支持 SQLite `workflow_checkpoint`，ask / ingest / digest 可通过显式 `thread_id` + `resume_from_checkpoint` 做最小恢复，`DAILY_DIGEST` 与 `INGEST_STEWARD` 的 waiting thread 则通过 `/workflows/resume` 继续推进
- `backend/app/main.py` 与 `backend/app/services/resume_workflow.py` 已提供 `/workflows/resume`，可消费 `thread_id / proposal_id / approval_decision / writeback_result` 做最小审批恢复，并在成功写回后自动触发 scoped ingest、通过 `post_writeback_sync` 返回刷新成功 / 失败结果，同时把写回事实记入 checkpoint 与审计日志；`GET /workflows/pending-approvals` 也已可返回最小待审批收件箱列表
- `backend/app/services/rollback_workflow.py` 与 `backend/app/main.py` 已提供 `/workflows/rollback`，可把 rollback 成功 / 失败结果写入 append-only `audit_log`，并仅在成功 rollback 时把 `rollback_result` 持久化到 completed checkpoint
- `plugin/src/main.ts` 现已提供最小插件入口、设置、后端探活 / 启动控制、真实 `DAILY_DIGEST` proposal 加载命令、待审批收件箱刷新命令与本地 demo fallback 命令
- `plugin/src/views/KnowledgeStewardView.ts` 已接通待审批收件箱，并把审批通过流程改成“先本地执行受限写回，再把 `writeback_result` 回传 `/workflows/resume`”；当前面板除 post-writeback scoped reindex 结果外，也会展示 Backend Runtime 的启动中 / 已就绪 / 启动失败状态、最近错误和最近输出
- `plugin/src/writeback/applyProposalWriteback.ts` 与 `plugin/src/writeback/helpers.ts` 已支持 `merge_frontmatter` / `insert_under_heading` 两类受限 patch op，并在写回前校验 `before_hash`；若当前写回是由本插件会话真实执行，插件还能基于 `LocalRollbackContext` 提供最小 rollback 入口
- `eval/run_eval.py` 已把离线 golden eval 升级到 `schema_version=1.3`，当前 18 条 case 已覆盖 ask / governance / digest / resume-writeback 四类核心场景，并输出最小 `quality_metrics`、全局 `metric_overview`、`question_answering / governance` 两套 `benchmark_overview`、场景级 `core_metrics` 与最小 `failure_type_breakdown`
- `sample_vault/` 已纳入首版设计，当前检测到 205 篇 Markdown 笔记

## 启动计划

### 后端（唯一推荐环境：workspace-local conda prefix）

```bash
conda env create --prefix ./.conda/knowledge-steward --file backend/environment.yml
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$PWD/.conda/knowledge-steward"
cd backend
python -m app.main
```

若环境已存在，改为：

```bash
conda env update --prefix ./.conda/knowledge-steward --file backend/environment.yml --prune
```

最小验证命令（另一个终端执行）：

```bash
curl http://127.0.0.1:8787/health
```

`python -m app.main` 会读取 `KS_HOST` / `KS_PORT`。`backend/.venv` 当前仅保留为历史痕迹，不再作为推荐开发环境或验收标准。

### 插件

```bash
cd plugin
npm install
npm run dev
```

推荐顺序仍然是先启动后端并确认 `/health` 正常，再启动插件 dev 模式；但插件现在也支持在设置页配置 backend 启动命令后，从 Obsidian 内执行最小启动控制。

若希望让插件一键拉起本地后端，可在插件设置中配置：

- `Backend start command`：实际启动命令，建议使用绝对路径或明确的 shell 命令链
- `Backend working directory`：可选工作目录；如果命令本身已处理 `cd`，可留空
- `Backend startup timeout (ms)` / `Backend health poll interval (ms)`：控制等待 `/health` ready 的时限和轮询频率
- `Auto-start backend on plugin load`：若开启，插件加载时会自动尝试启动

当前实现仍依赖用户提供可执行启动命令，不会替你自动安装依赖或推断 conda / shell 环境。

将 `plugin/` 产物作为 Obsidian 开发插件载入后，可使用：

- `Knowledge Steward: Open panel`
- `Knowledge Steward: Ping backend`
- `Knowledge Steward: Start backend`
- `Knowledge Steward: Refresh pending approvals`
- `Knowledge Steward: Load daily digest approval`
- `Knowledge Steward: Open approval demo`

## 执行最小 FTS 检索

在完成 ingest 后，当前已可直接对 SQLite 索引做最小全文查询：

```bash
cd backend
python -m app.retrieval.sqlite_fts --query "总结" --limit 5
```

如需指定数据库路径，可显式传入 `--db-path`。

## 执行最小向量检索

在完成至少一次带可用 embedding provider 的 ingest 后，当前已可对 `chunk_embedding` 执行最小向量检索：

```bash
cd backend
python -m app.retrieval.sqlite_vector --query "总结" --limit 5
```

如当前 embedding provider 不可用，返回会显式标记 `disabled=true` 与 `disabled_reason=no_available_embedding_provider`；如当前 provider/model 下还没有任何向量数据，则会返回 `vector_index_not_ready`，而不是伪装成普通 no-hit。

## 执行 scoped ingest

后端启动后，当前已可通过 `/workflows/invoke` 只同步指定 note，而不是每次都整库 ingest：

```bash
curl -X POST http://127.0.0.1:8787/workflows/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "ingest_steward",
    "note_paths": [
      "日常/2023-11-06_星期一.md",
      "日常/2023-07/v6.3.0迭代总结.md"
    ]
  }'
```

`note_path` 和 `note_paths` 都支持 vault 内相对路径；后端会拒绝 vault 外路径、缺失文件和非 Markdown 文件。当前 scoped ingest 之后仍统一重建 FTS，以优先保证检索一致性。

## 触发真实 ingest 审批 proposal

后端启动并完成 ingest 后，当前已可通过显式 proposal 模式让单 note scoped ingest 产出真实治理 proposal：

```bash
curl -X POST http://127.0.0.1:8787/workflows/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "ingest_steward",
    "note_path": "日常/2023-11-06_星期一.md",
    "require_approval": true,
    "metadata": {
      "approval_mode": "proposal"
    }
  }'
```

若当前 note 命中首版规则驱动治理信号，返回体会包含：

- `status=waiting_for_approval`
- `thread_id`
- `proposal`
- 同步生成的 `ingest_result`

若当前 note 命中 proposal 路径，返回体会在 `proposal` 之外额外给出 `analysis_result`，其中包含最小 `retrieval_queries`、`related_candidates` 与结构化 finding。当前这条治理链路已经从“只看当前 note 的 parser 结构信号”推进到“单 note scoped ingest + 统一 hybrid related retrieve（FTS + vector，向量不可用时退回 FTS）+ 保守的 `orphan_hint / duplicate_hint` + 现有受限 patch op”边界内；同时 target note 自身会被显式排除，避免 related evidence 变成自证循环。

如果当前索引里还没有旧笔记上下文，例如 fresh DB 或冷索引下只做了单 note scoped ingest，后端会安全 fallback 到普通 completed scoped ingest 或 no-proposal message，而不是硬造跨 note evidence。

## 执行最小 ask 调用

后端启动并完成 ingest 后，当前已可通过 `/workflows/invoke` 触发最小 ask 链路：

```bash
curl -X POST http://127.0.0.1:8787/workflows/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "ask_qa",
    "user_query": "总结",
    "retrieval_filter": {
      "note_types": ["daily_note"]
    }
  }'
```

返回体中的 `ask_result` 会包含 `answer`、`citations`、`retrieved_candidates` 以及 retrieval / model fallback 信号；若模型答案缺少 `[n]` 引用或编号超出当前候选范围，后端会自动降级为 `retrieval_only`。

每次 ask 执行还会默认向 `data/traces/ask_runtime.jsonl` 追加 JSONL runtime trace，并同步聚合到 SQLite `run_trace`；如需调整 JSONL 路径，可设置 `KS_ASK_RUNTIME_TRACE_PATH`。

## 查询最小 ask trace

完成一次 ask 调用后，当前已可按 `run_id` 或 `thread_id` 查询 SQLite 聚合 trace：

```bash
cd backend
python -m app.observability.runtime_trace --run-id "run_xxx"
```

如需按 `thread_id` 查询，可改用 `--thread-id`。

## 触发真实 digest 审批 proposal

后端启动并完成 ingest 后，当前已可通过 `DAILY_DIGEST` 触发真实 `proposal + waiting_for_approval`：

```bash
curl -X POST http://127.0.0.1:8787/workflows/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "daily_digest",
    "require_approval": true,
    "metadata": {
      "approval_mode": "proposal"
    }
  }'
```

若命中 proposal 路径，返回体会包含：

- `status=waiting_for_approval`
- `thread_id`
- `proposal`
- 同步生成的 `digest_result`

审批决策可继续调用 `/workflows/resume`；当前插件也可通过 `Knowledge Steward: Load daily digest approval` 直接把这份真实 proposal 注入审批面板，并在 approve 时先执行本地受限写回，再把 `writeback_result` 回传后端统一落审计与 checkpoint。

## 查询待审批收件箱

当前已可通过后端查询最小 pending proposal inbox：

```bash
curl http://127.0.0.1:8787/workflows/pending-approvals
```

返回体中的 `items` 会包含 `thread_id`、`proposal_id`、`summary`、`target_note_path`、`risk_level` 与完整 `proposal`。插件侧边栏也已支持 `Refresh pending approvals`，可把真实 waiting proposal 加载回现有审批面板。

## 运行最小离线 eval

当前已可执行最小 golden set 回归：

```bash
./.conda/knowledge-steward/bin/python eval/run_eval.py
```

如需只跑某条 case，可显式过滤：

```bash
./.conda/knowledge-steward/bin/python eval/run_eval.py \
  --case-id ask_sample_retrieval_only_daily_notes
```

执行完成后会在 `eval/results/` 下生成带时间戳的 JSON 结果文件。当前 baseline 已扩到 18 条样本，同时包含：

- 基于真实 `sample_vault` 的 ask / digest 回归
- 基于 deterministic fixture 的 governance waiting / no-proposal fallback、citation 越界、`no_hits`、合法 grounded answer、semantic overclaim 的 `unsupported_claim` 分桶，以及 `resume_workflow` 的 reject / writeback success / writeback failure 等 bad case
- 每条 case 的最小 `faithfulness`、`relevancy`、`context_precision`、`context_recall`，以及全局 `metric_overview`、`question_answering / governance` 两套 `benchmark_overview`、场景级 `core_metrics` 与最小 `failure_type_breakdown`

## 当前未完成

- 更完整的 LangGraph graph 编排（当前已落地 ask_graph、ingest_graph、digest_graph、最小 SQLite checkpoint 恢复，以及 `DAILY_DIGEST` 与 `INGEST_STEWARD` 的首条真实 approval proposal 路径）
- rerank、更强的线上语义级 groundedness gate / answer-citation consistency 校验，以及 hybrid 的 branch 调试快照 / 向量 coverage 观测
- 多 workflow proposal 化与“本地写回成功但后端记账失败”的跨会话恢复入口
- rollback 成功后的 scoped ingest 刷新、历史 writeback 的跨会话可执行 rollback 与 rollback diff 预览
- 插件 ask UI、更完整 tracing 治理、更大规模 golden set、宿主级写回回归和 richer eval 指标

当前后续主线已在 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) 收敛为新的 interview-first MVP 路线：`TASK-030`、`TASK-034`、`TASK-035`、`TASK-036`、`TASK-037`、`TASK-038`、`TASK-039`、`TASK-040`、`TASK-041`、`TASK-042` 已完成，interview-first 保留主线已收口。若继续推进 medium，默认回到 `TASK-031`、`TASK-032`、`TASK-033`；pending inbox freshness、CLI scoped parity、新笔记治理 proposal 的风险分级 / patch 模板收敛、rollback diff 预览、post-rollback scoped ingest、groundedness 停用词 / allowlist 收敛继续后移。

这些内容的设计与路线图已经写入主文档，后续代码必须同步维护文档。
