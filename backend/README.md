# Backend Baseline

当前后端已完成以下基线能力：

- 固化核心协议模型
- 暴露最小 `/health` 探活接口
- 暴露 `/workflows/invoke`，其中 `ask_qa` 已返回最小引用式响应，其他 action 仍为占位
- 提供 SQLite schema 初始化与最小 ingest CLI
- 提供 SQLite FTS5 检索与最小 ask 服务

它还没有真正执行 LangGraph graph、hybrid retrieval、rerank、强约束 grounded answer 校验或审批写回。

## 推荐开发环境

当前唯一推荐的 Python 路线是工作区本地 conda prefix：`./.conda/knowledge-steward`。

```bash
conda env create --prefix ./.conda/knowledge-steward --file backend/environment.yml
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$PWD/.conda/knowledge-steward"
```

如果环境已存在，使用：

```bash
conda env update --prefix ./.conda/knowledge-steward --file backend/environment.yml --prune
```

`backend/.venv` 当前只视为历史残留，不再作为 README、验收或调试时的默认入口。

## 运行

```bash
cd backend
python -m app.main
```

## 初始化 SQLite schema

在进入 ingest 写库前，可先创建或迁移本地索引库：

```bash
cd backend
python -m app.indexing.store
```

如需落到其他数据库文件，可显式传入 `--db-path`，或设置 `KS_INDEX_DB_PATH`。

## 执行最小 ingest

当前已可将 `sample_vault/` 的 Markdown 全量写入 SQLite：

```bash
cd backend
python -m app.indexing.ingest
```

如需指定 Vault 或数据库路径，可显式传入 `--vault-path` 和 `--db-path`。

## 执行最小 FTS 检索

当前已可直接基于 SQLite FTS5 查询 top-k chunk candidate：

```bash
cd backend
python -m app.retrieval.sqlite_fts --query "总结" --limit 5
```

如需指定数据库路径，可显式传入 `--db-path`。

## 执行最小 ask 调用

当前已可通过 `/workflows/invoke` 的 `ask_qa` 返回最小 ask 结果：

```bash
curl -X POST http://127.0.0.1:8787/workflows/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "ask_qa",
    "user_query": "总结"
  }'
```

若模型不可用，返回体中的 `ask_result.mode` 会退回 `retrieval_only`；若没有命中候选片段，则返回 `no_hits`。

## 最小验证

后端启动后，在另一个终端执行：

```bash
curl http://127.0.0.1:8787/health
```

## 配置说明

- `backend/.env.example` 目前只提供变量清单，当前基线代码仍通过 shell 环境变量读取配置。
- `python -m app.main` 会使用 `KS_HOST` 和 `KS_PORT`，默认监听 `127.0.0.1:8787`。
