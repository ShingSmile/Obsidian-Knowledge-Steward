# Eval Baseline

当前目录用于存放：

- `golden/`：golden set 样本
- `results/`：每次评估输出

当前已落地的是“interview-first P0 baseline”，而不是先凑满固定 30 条样本再开始回归。

当前 baseline 的关键事实：

- golden set 已扩到 18 条 case
- 结果文件当前为 `schema_version=1.2`
- 每条 case 会输出最小 `quality_metrics`
- 全局结果会聚合 `metric_overview`
- 样本继续混合真实 `sample_vault` 回归与 deterministic fixture bad case

当前真实覆盖面包括：

- ask：retrieval-only、metadata filter fallback、hybrid retrieval、编号越界、合法 grounded answer、semantic overclaim 的 `unsupported_claim`
- governance / proposal：`INGEST_STEWARD` waiting proposal、no-proposal fallback、retrieval-backed analysis evidence
- digest / proposal：structured digest、empty-index fallback、waiting proposal
- resume / writeback：reject、writeback success、writeback failure

执行入口为 [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)，每次运行会向 `results/` 落一份带时间戳的 JSON 结果文件。

当前最小指标包括：

- `faithfulness`
- `relevancy`
- `context_precision`
- `context_recall`

当前 baseline 仍然刻意限制在“本地、可解释、可重复”的范围内：

- 不依赖在线 judge 或外部评测平台
- 不把本轮扩成分场景 benchmark 或 dashboard
- 不把离线指标直接接进 ask runtime gate

后续如需继续扩样本，优先补齐：

- `TASK-040`：把当前结果正式切成治理 vs 问答的分场景 benchmark
- 新增 workflow 的高风险 bad case
- groundedness 规则最容易误判的中文样本
- 写回 / 恢复 / scoped ingest 相关回归，而不是先机械追求样本条数
