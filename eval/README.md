# Eval Baseline

当前目录用于存放：

- `golden/`：golden set 样本
- `results/`：每次评估输出

其中 `eval/golden/` 仍然是回归层，负责固定的 eval 回归样本；`eval/benchmark/` 是新的 benchmark 数据层，负责维护可增量扩展的 ask benchmark 数据集和 review backlog。

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

## Ask Benchmark Dataset Workflow

`eval/benchmark/` 目录下的 operator 入口是：

```bash
/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/.conda/knowledge-steward/bin/python eval/benchmark/manage_ask_benchmark.py validate
```

生成候选批次：

```bash
/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/.conda/knowledge-steward/bin/python eval/benchmark/manage_ask_benchmark.py generate-batch --count 5 --output /tmp/ask_batch.json
```

应用 review 结果：

```bash
/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/.conda/knowledge-steward/bin/python eval/benchmark/manage_ask_benchmark.py apply-review --batch /tmp/ask_batch.json --review /tmp/ask_review.json
```

`apply-review` 支持 partial review 文件：只会处理 `--review` 中出现的 case，其余 batch 条目会被跳过，并在成功输出里显式报告 skipped 数量。

路径覆盖参数 `--dataset`、`--backlog`、`--vault-root` 都可用于临时副本或 smoke test，不会强制写入正式文件。

后续如需继续扩样本，优先补齐：

- `TASK-040`：把当前结果正式切成治理 vs 问答的分场景 benchmark
- 新增 workflow 的高风险 bad case
- groundedness 规则最容易误判的中文样本
- 写回 / 恢复 / scoped ingest 相关回归，而不是先机械追求样本条数
