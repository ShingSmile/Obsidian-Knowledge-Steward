# Obsidian Knowledge Steward

基于 LangGraph 的个人学习知识治理与复盘 Agent。

## 项目介绍

Obsidian Knowledge Steward 是一个面向 Obsidian 的知识治理系统，不是普通聊天问答插件。它关注的是“新笔记进入 Vault 之后如何被治理、复盘、追踪、审批写回和审计”，问答只是兜底链路，不是系统主叙事。

稳定能力边界包括：

- 新笔记治理
- 每日 / 周期复盘
- 问答兜底
- Human-in-the-loop 审批写回
- tracing / eval / 审计日志

## 文档导航

- [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)：任务绑定与验收入口
- [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md)：唯一动态控制面
- [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md)：最近相关会话与交接记录
- [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md)：稳定架构、模块边界、ADR、长期风险
- [docs/INTERVIEW_PLAYBOOK.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/INTERVIEW_PLAYBOOK.md)：面试叙事与追问口径
- [docs/CHANGELOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CHANGELOG.md)：版本与里程碑记录

新会话默认读取顺序：

1. [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
2. [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md)
3. [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md) 中最近相关记录
4. [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 与相关代码入口

## 运行方式

### 后端

唯一推荐环境仍是 workspace-local conda prefix：

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

最小健康检查：

```bash
curl http://127.0.0.1:8787/health
```

### 插件

```bash
cd plugin
npm install
npm run dev
```

推荐顺序仍然是先启动后端并确认 `/health` 正常，再启动插件 dev 模式。

若希望由插件拉起本地后端，需要在插件设置中显式配置：

- `Backend start command`
- `Backend working directory`
- `Backend startup timeout (ms)`
- `Backend health poll interval (ms)`
- `Auto-start backend on plugin load`

## 演示入口

### Obsidian 插件命令

- `Knowledge Steward: Open panel`
- `Knowledge Steward: Ping backend`
- `Knowledge Steward: Start backend`
- `Knowledge Steward: Refresh pending approvals`
- `Knowledge Steward: Load daily digest approval`
- `Knowledge Steward: Open approval demo`

### Ask Demo

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

### Ingest Proposal Demo

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

### Daily Digest Proposal Demo

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

### Pending Approvals Demo

```bash
curl http://127.0.0.1:8787/workflows/pending-approvals
```

### 离线 Eval

```bash
./.conda/knowledge-steward/bin/python eval/run_eval.py
```

如需只跑某条 case，可显式过滤：

```bash
./.conda/knowledge-steward/bin/python eval/run_eval.py \
  --case-id ask_sample_retrieval_only_daily_notes
```
