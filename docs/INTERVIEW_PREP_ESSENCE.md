# INTERVIEW_PREP_ESSENCE

> 用途：只保留后续面试复习最有用的结论。当前版本先沉淀 Step 1，后续继续增量维护。

## Step 1：项目宏观认知与术语对齐

### 1. 项目一句话定位

问题：这个项目本质上是什么？

思路：不要把它讲成“Obsidian 聊天助手”，要讲成“知识治理系统”。

方案：`Obsidian Knowledge Steward` 是一个面向个人学习场景的知识治理 Agent 系统。它围绕新笔记治理、每日复盘、可解释问答、人工审批写回、审计与评估闭环，构建了一个有状态、可恢复、可审计的 LangGraph 工作流，而不是一个黑盒聊天机器人。

项目代码落地：
- 文档结论：主文档明确有三条主链路 `INGEST_STEWARD`、`DAILY_DIGEST`、`ASK_QA`
- 文档结论：当前强调“治理优先，问答兜底”
- 待代码复核：Step 2 再从入口和依赖确认当前实现是否完全对齐该叙事

### 2. 核心业务流

问题：这个 Agent 到底能干什么？输入和输出分别是什么？

思路：按“输入 -> 中间处理 -> 输出”讲，面试官最容易听懂。

方案：

1. 新笔记治理流
- 输入：当前笔记路径、笔记内容、相关上下文
- 处理：解析 Markdown -> 检索相关旧笔记 -> 分析重复/冲突/孤立 -> 生成 proposal -> 人工审批 -> 受限写回 -> 审计与重建索引
- 输出：结构化治理建议、patch plan、审批结果、审计记录

2. 每日复盘流
- 输入：一个时间窗口内的近期笔记集合
- 处理：聚合近期笔记 -> 提取主题/开放问题/行动项 -> 生成 digest proposal -> 人工审批 -> 写回复盘 note
- 输出：复盘草稿、行动项、审计记录

3. 问答兜底流
- 输入：用户问题
- 处理：解析 query -> metadata 过滤 -> hybrid retrieval -> 可选 rerank -> 基于引用生成答案
- 输出：带引用的答案、来源 chunk、置信提示

项目代码落地：
- 文档结论：后端统一入口是 `/workflows/invoke`
- 文档结论：当前三条 workflow 已统一到 ask / ingest / digest 共享 contract
- 文档结论：审批恢复、rollback、pending approvals 已有独立控制面

### 3. 为什么它不是普通 RAG

问题：为什么这个项目值得讲，而不是“又一个 RAG Demo”？

思路：抓住“状态、审批、写回、安全、评估”这几个关键词。

方案：
- 普通 RAG 主要解决“能不能查到信息”
- 这个项目还要解决“知识库会不会越来越乱、能不能安全修改、出了问题能不能追责和恢复”
- 所以它多了 workflow、checkpoint、HITL、writeback、audit log、eval/tracing

项目代码落地：
- 文档结论：当前已经接通最小 `DAILY_DIGEST -> approval -> local writeback -> audit/checkpoint` 闭环
- 文档结论：当前 ask 链路强调 citation 对齐和 groundedness 离线评估

### 4. Step 1 必会术语

#### 术语 1：LangGraph / 有状态工作流
- 大白话：不是让模型自己随便想下一步，而是把流程拆成多个固定节点，每一步都能看见、能暂停、能恢复。
- 为什么这里需要它：因为这个项目有审批节点，用户可能今天看 proposal，明天才点通过，这不是一次 API 调用能优雅处理的。
- 面试一句话：这个项目不是单轮 prompt，而是多节点、有状态、可中断的工作流，所以选 LangGraph 而不是单个 ReAct Agent。

#### 术语 2：RAG / Hybrid Retrieval
- 大白话：先去知识库里“找资料”，再拿找到的资料去回答，而不是让模型只靠自己记忆乱答。
- Hybrid 的意思：既看关键词匹配，也看语义相似度，两条路一起召回，稳定性更高。
- 为什么这里需要它：Obsidian 笔记里既有术语、标题、标签，也有语义相近但措辞不同的内容，只做向量检索或者只做 BM25 都不稳。

#### 术语 3：Embedding / 向量检索
- 大白话：把一句话变成一串数字坐标，让“意思相近”的文本在空间里更靠近。
- 为什么这里需要它：用户写笔记时说法不统一，关键词可能对不上，但语义还是相关。
- 例子：一篇写“上下文窗口优化”，另一篇写“长文本裁剪”，词不一样，但意思接近，向量检索更容易把它们召回到一起。

#### 术语 4：HITL（Human in the Loop）
- 大白话：模型先提建议，人最后拍板。
- 为什么这里需要它：因为一旦写回 Obsidian Vault，改错内容比答错一句话危险得多。
- 面试一句话：所有高风险写操作都要卡在危险之前，而不是改坏之后再补救。

#### 术语 5：Checkpoint / Thread ID / 恢复
- 大白话：给工作流存档。做到一半停住了，之后能从上次进度接着跑。
- 为什么这里需要它：审批、失败重试、rollback、审计都依赖“上次跑到哪里”的状态记录。
- 面试一句话：这相当于给 Agent 工作流加了事务感和可回放能力。

### 5. Step 1 可直接背的 30 秒表达

问题：面试官问“你这个项目是做什么的”，怎么快速回答？

思路：用“场景 + 核心问题 + 技术抓手 + 安全机制”四段式。

方案：

这个项目叫 `Obsidian Knowledge Steward`，它不是一个单纯的 Obsidian 聊天助手，而是一个面向个人学习场景的知识治理 Agent。它主要解决的是笔记越写越多之后出现的重复、冲突、孤立和复盘困难问题。技术上我把它拆成三条 LangGraph 工作流：新笔记治理、每日复盘和问答兜底；其中问答只是辅助，主线是治理。因为它涉及真实写回用户笔记，所以我专门加了人工审批、checkpoint、audit log 和 eval/tracing，重点不是“模型多聪明”，而是“系统可控、可恢复、可审计”。

### 6. 当前不要乱吹的点

- 不要说它已经是完整的生产级多 Agent 系统；当前主线更准确是三条 workflow
- 不要说 ask 也已经 fully proposal 化；文档里明确 ask proposal 还没接上
- 不要说它已经解决大规模 Vault 的性能问题；当前 SQLite + MVP 向量检索更偏 interview-first 可运行版本
- 不要把初版指南里的设想全部当成现状；后续必须以代码和主计划为准

### 7. 三个最容易卡壳的控制面概念

问题：`LangGraph`、`HITL`、`Checkpoint / Thread ID / 恢复` 到底分别是什么？

思路：把它们拆成“流程编排”“人工卡点”“状态存档”三件事。

方案：

- `LangGraph / 有状态工作流`
  - 本质：把一个复杂任务拆成多个固定节点，按状态和条件决定下一步做什么
  - 关键价值：不是只知道“当前做什么”，还知道“之前做到哪一步了”
  - 项目例子：新笔记治理不是一次 LLM 调用，而是 `解析 -> 检索 -> 分析 -> proposal -> 审批 -> 写回 -> 审计`

- `HITL`
  - 本质：把最危险的一步交给人拍板
  - 关键价值：模型可以提建议，但不能直接越权改用户笔记
  - 项目例子：proposal 出来后先停住，插件展示 diff 和风险提示，只有用户点 approve 才继续

- `Checkpoint / Thread ID / 恢复`
  - 本质：给 workflow 存档，并用一个 ID 标识这次流程实例
  - `thread_id` 更像“这次任务的会话编号”
  - `checkpoint` 更像“这个编号在某个时刻的状态快照”
  - `恢复` 就是带着 `thread_id` 回来，从上次停住的 checkpoint 接着执行
  - 项目例子：用户今天看到 proposal 没批，明天还能继续批，而不是从头重新生成一遍

项目代码落地：
- 文档结论：当前已有 `workflow_checkpoint`
- 文档结论：当前已有 `thread_id` 恢复协议
- 文档结论：`/workflows/resume` 已作为审批恢复入口

面试一句话：
- LangGraph 负责“怎么流转”
- HITL 负责“哪里必须让人介入”
- Checkpoint / Thread ID / 恢复负责“停了以后怎么接着跑”

## Step 2：核心架构与技术栈剖析

### 1. 项目地图

问题：这个仓库按层怎么分？

思路：按“插件层、后端层、数据层、评估层、文档层”来讲最清楚。

方案：
- `plugin/`：Obsidian 插件层，负责命令入口、面板 UI、审批交互、本地后端启动控制、受限写回
- `backend/`：Python 后端，负责 FastAPI API、LangGraph 工作流、检索、索引、checkpoint、resume、rollback
- `data/`：本地运行数据，包含 SQLite、trace
- `eval/`：golden case 和离线评测
- `docs/`：主计划、任务队列、会话演进记录
- `sample_vault/`：示例知识库语料

项目代码落地：
- 代码事实：[backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py) 是后端入口
- 代码事实：[plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts) 是插件入口

### 2. 当前技术栈

问题：项目具体用了什么技术？

思路：只讲代码里真实出现的依赖，不把文档设想混进来。

方案：
- 后端：Python 3.12 + FastAPI + Uvicorn + Pydantic + LangGraph
- 插件：TypeScript + Obsidian Plugin API + esbuild
- 检索存储：SQLite + FTS5 + SQLite 内的 embedding 持久化
- 模型调用：自封装 openai-compatible / local provider HTTP 调用，不依赖 LangChain/LlamaIndex SDK

项目代码落地：
- 代码事实：[backend/pyproject.toml](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/pyproject.toml#L11) 只有 `fastapi`、`uvicorn`、`pydantic`、`langgraph`
- 代码事实：[plugin/package.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/package.json#L6) 是 Obsidian 插件构建与测试脚本
- 代码事实：[backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L39) 与 [backend/app/retrieval/embeddings.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/embeddings.py#L151) 使用原生 HTTP 请求封装模型与 embedding 调用

### 3. Agent 范式判断

问题：它是单 Agent 还是多 Agent？是 ReAct 还是 Plan-and-Execute？

思路：先按代码事实排除，再给出准确叫法。

方案：
- 不是多 Agent。当前没有 supervisor、agent 间分工、消息传递或并行子 agent
- 也不是经典 ReAct。模型没有“自己想下一步做什么、再调用工具、再观察”的循环
- 更准确的说法是：`单系统、多工作流（workflow-first）的有状态 Agent 应用`
- 三条主链路分别是 `ask_graph`、`ingest_graph`、`digest_graph`，都是显式节点编排

项目代码落地：
- 代码事实：[backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py#L91) 统一注册并分发三条 workflow
- 代码事实：[backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py#L114) 只有 `prepare -> execute -> finalize`
- 代码事实：[backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py#L163) 也是固定线性节点
- 代码事实：[backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py#L203) 明确是 checkpointed linear graph

### 4. 为什么这样选型

问题：为什么这里不用 LangChain/LlamaIndex，也不做 ReAct？

思路：围绕“可控性、安全性、面试可解释性”回答。

方案：
- 选 LangGraph：因为项目核心不是聊天，而是长流程、有状态、可恢复、可审批
- 不选 ReAct：因为写回笔记是高风险动作，不能让模型自由决定何时调工具、何时改内容
- 不重度依赖 LangChain/LlamaIndex：因为当前流程并不复杂，自己维护状态、协议、fallback 更直接，也更利于讲清工程边界
- 选 FastAPI + Pydantic：接口协议清晰，适合本地后端控制面
- 选 SQLite：本地优先、部署轻、两周内能落地，但扩展性一般

面试一句话：
- 这个项目更像“状态机驱动的工作流 Agent”，而不是“让大模型自由发挥的智能体”
- 我优先要的是可控、可审计、可恢复，而不是抽象层越高越好

### 5. 当前 trade-off

- 收益：结构清楚、状态显式、安全边界清楚、面试时容易讲
- 代价：很多能力要手写，抽象没有高层框架省事
- 风险：当前 workflow 还比较线性，后面如果分支和节点暴增，维护成本会上升

## Step 3：模块级代码精读阅读计划

### 1. 为什么先做模块拆分

问题：为什么不直接从入口一路读下去？

思路：源码阅读如果没有模块边界，最后会变成“看了很多文件，但讲不清系统”。

方案：
- 先拆模块，再逐个精读
- 每个模块只回答 4 个问题：它负责什么、核心输入输出是什么、为什么这样设计、放大 10 倍/100 倍后的瓶颈是什么
- 每次精读只读一个模块，读完就停，顺手做面试追问

### 2. Step 3 的推荐模块划分

#### 模块 A：统一入口与协议控制面
- 负责什么：把插件请求变成后端统一 workflow 调用，并统一响应、状态、协议
- 重点文件：
  - [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
  - [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py)
- 为什么先读：这是全项目主入口，不先搞懂这里，后面读 graph 和 service 会失去方向
- 面试高频追问：
  - 为什么要统一 `/workflows/invoke`
  - 为什么协议要先于业务细节固定

#### 模块 B：工作流运行时与状态管理
- 负责什么：封装共享 state、trace hook、checkpoint、resume 机制
- 重点文件：
  - [backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py)
  - [backend/app/graphs/checkpoint.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/checkpoint.py)
  - [backend/app/graphs/state.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/state.py)
- 为什么重要：这是 LangGraph / checkpoint / thread_id 最核心的代码承载点
- 面试高频追问：
  - checkpoint 怎么防重复执行
  - thread_id 和 run_id 为什么都要有

#### 模块 C：三条业务工作流
- 负责什么：把 ask / ingest / digest 组织成显式 graph
- 重点文件：
  - [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)
  - [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)
  - [backend/app/graphs/digest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/digest_graph.py)
- 为什么单独成块：这里最能体现“项目不是聊天壳，而是 workflow-first”
- 面试高频追问：
  - 为什么 ask / ingest / digest 要拆三条 graph
  - 为什么当前是线性 graph，不是更复杂的条件路由

#### 模块 D：文档解析与索引构建
- 负责什么：把 Obsidian Markdown 变成 note / chunk 结构，并落到 SQLite
- 重点文件：
  - [backend/app/indexing/parser.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/parser.py)
  - [backend/app/indexing/models.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/models.py)
  - [backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py)
  - [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py)
- 面试高频追问：
  - chunk 为什么这样切
  - SQLite schema 为什么这么设计
  - 数据量放大后 ingest 的瓶颈在哪里

#### 模块 E：检索与问答生成
- 负责什么：FTS、向量检索、hybrid 融合、最小 ask 响应
- 重点文件：
  - [backend/app/retrieval/sqlite_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_fts.py)
  - [backend/app/retrieval/sqlite_vector.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_vector.py)
  - [backend/app/retrieval/hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/hybrid.py)
  - [backend/app/retrieval/embeddings.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/embeddings.py)
  - [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)
- 面试高频追问：
  - 为什么 hybrid 比单路径稳
  - citation 对齐是怎么兜底的
  - provider 挂了怎么降级

#### 模块 F：治理 proposal、审批恢复与写回安全
- 负责什么：生成 proposal、等待审批、恢复执行、本地受限 patch 写回、rollback
- 重点文件：
  - [backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py)
  - [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py)
  - [backend/app/services/rollback_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/rollback_workflow.py)
  - [plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts)
  - [plugin/src/writeback/helpers.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/helpers.ts)
- 面试高频追问：
  - 为什么 patch 要插件执行而不是后端直接改文件
  - before_hash 怎么防并发覆盖
  - rollback 的边界在哪里

#### 模块 G：插件 UI 与后端运行时控制
- 负责什么：面板、命令、pending inbox、后端探活与自启
- 重点文件：
  - [plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts)
  - [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)
  - [plugin/src/api/client.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/api/client.ts)
  - [plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts)
- 面试高频追问：
  - 为什么插件不直接做全部逻辑
  - readiness 为什么要看 `/health` 而不是只看子进程存在

#### 模块 H：观测与评估闭环
- 负责什么：runtime trace、golden eval、benchmark 输出
- 重点文件：
  - [backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py)
  - [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
  - [eval/golden](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden)
- 面试高频追问：
  - 你怎么证明系统有效
  - tracing 和 logging 的区别是什么

### 3. 推荐阅读顺序

1. 模块 A：统一入口与协议控制面
2. 模块 B：工作流运行时与状态管理
3. 模块 C：三条业务工作流
4. 模块 D：文档解析与索引构建
5. 模块 E：检索与问答生成
6. 模块 F：治理 proposal、审批恢复与写回安全
7. 模块 G：插件 UI 与后端运行时控制
8. 模块 H：观测与评估闭环

原因：
- 先看控制面，再看业务流
- 先看“怎么串起来”，再看“每一段怎么实现”
- 这样后面每个模块都能放回主链路里讲，而不是碎片化背代码

### 4. 模块 A 精读结论：统一入口与协议控制面

问题：为什么先读 `main.py` 和 `workflow.py`？

思路：这两个文件决定了“系统接什么请求、返回什么结果、三条 workflow 如何统一调度”。

方案：
- [backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py) 是后端控制面入口
- [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py) 是全系统协议中心
- 两者一起把“接口层”和“领域模型层”钉死，后面的 graph、service、plugin 都要围着它们转

项目代码落地：
- 代码事实：`WorkflowAction` 只定义了三种动作 `ask_qa / ingest_steward / daily_digest`
- 代码事实：`/workflows/invoke` 是统一入口，内部通过 handler registry 分发到三条 workflow
- 代码事实：`/workflows/resume`、`/workflows/rollback`、`/workflows/pending-approvals` 把审批恢复、撤销、待办查询独立成控制面
- 代码事实：响应统一包含 `run_id / thread_id / action_type / status / message / approval_required`

主链路大白话：
- 插件或客户端发一个 `WorkflowInvokeRequest`
- 后端先检查参数是否合法
- 然后生成 `thread_id` 和 `run_id`
- 再根据 `action_type` 找到对应 handler
- handler 调 ask / ingest / digest 的 graph
- graph 执行完后，不直接裸返回，而是先转成统一 outcome，再拼成统一 response

为什么这样设计：
- 如果不统一入口，三条 workflow 很容易各写各的 API，最后插件端协议会越来越乱
- 如果不统一 response，前端就要针对 ask / ingest / digest 分别写兼容逻辑
- 如果不把 proposal / approval / rollback 也定义成协议对象，后面 HITL 很难稳定扩展

模块亮点：
- 用 handler registry 收口 workflow 分发，而不是在 API 层写一堆 if-else
- 在 API 层统一生成 `thread_id` 和 `run_id`，避免 graph 内外 ID 断裂
- `Proposal`、`ApprovalDecision`、`WritebackResult`、`AuditEvent` 这些协议对象把高风险动作结构化了，后面才有审计、恢复、回滚的基础

规模扩大时的瓶颈：
- 不是数据量瓶颈，而是“协议复杂度膨胀”
- 如果后面 workflow 类型翻倍，`WorkflowInvokeResponse` 这种大一统模型会越来越胖
- 更合理的重构方向是：保留统一 envelope，业务 payload 再按 action_type 拆子模型，或者引入更清晰的 response discriminator

面试一句话：
- 模块 A 本质上是整个系统的 API 控制面和协议中枢，它把三条业务 workflow 收口成统一入口、统一状态语义和统一响应格式，保证插件层不用理解后端内部细节

### 5. 模块 A 高频追问题库

#### 问题 1：为什么要把 ask / ingest / digest 统一收口到 `/workflows/invoke`，而不是一开始就做 3 个独立 endpoint？

参考回答：
- 我统一的是控制面，不是业务算法本身
- 这三条链路虽然中间逻辑不同，但入口层共享一套很强的公共语义：`action_type`、`thread_id`、`run_id`、`status`、`approval_required`，后续还可能进入 `resume`、`rollback`、`audit`
- 统一入口可以让插件只维护一套调用协议和状态处理逻辑，而不是分别适配 3 套 API
- 真正不同的业务逻辑并没有被硬揉在一起，而是通过 handler registry 分发到不同 graph
- 当前 workflow 数量不多，统一入口的收益大于拆分成本

更进一步追问：
- 什么情况下你会把统一入口拆掉？

进一步回答：
- 当控制面不再统一时，我会考虑拆
- 具体信号包括：不同 workflow 的鉴权方式不同、SLA 和超时策略明显不同、请求响应模型差异大到需要大量 if-else、前端已经不得不按 action 写很多分支、某些 workflow 需要独立部署或独立扩缩容
- 这时候继续强行共用一个入口，会让控制面从“统一”变成“耦合”
- 我的拆法通常不是一步拆成完全无关的 10 个接口，而是先按域拆，例如问答类、治理类、审批类，再看是否进一步细分

这题考察的本质：
- 你有没有区分“控制面统一”和“业务逻辑统一”
- 你能不能从接口设计、前后端协作、演进成本三个角度回答 trade-off

#### 问题 2：如果 workflow 从 3 条扩到 10 条，继续共用一个 `WorkflowInvokeResponse` 会有什么问题？你会怎么改？

参考回答：
- 最大问题不是功能不够，而是协议会膨胀
- 如果所有 action 都往同一个 response 模型里塞字段，会出现大量可空字段、类型边界变弱、一个 action 改协议牵连其他 action
- 更合理的做法是保留统一 envelope，再拆 action-specific payload
- `envelope` 指外层统一壳，主要放公共控制字段，如 `run_id`、`thread_id`、`action_type`、`status`、`message`
- `payload` 指真正随 action 变化的业务内容，如 `ask_result`、`ingest_result`、`digest_result`
- 这样可以做到“外壳统一，里子分开”；只有当不同 workflow 的权限模型、SLA、部署边界都明显不同，才进一步拆独立 endpoint

更进一步追问：
- 什么信号说明“协议已经该拆了”？

进一步回答：
- 第一，大量字段长期只对个别 action 有意义，response 里充满可空字段
- 第二，前后端都开始出现大量 `if action_type == ...` 的分支逻辑
- 第三，一个 action 改协议会连带改动其他 action 的校验、测试和类型定义
- 第四，团队已经无法靠一个统一模型清楚表达边界，新人读协议也会困惑
- 第五，不同 action 开始有不同的版本节奏、权限模型、性能目标
- 出现这些信号后，就说明“统一 envelope”还可以保留，但 payload 和 endpoint 应该进一步拆分

这题考察的本质：
- 你是否理解 API 演进中的可扩展性问题
- 你能否提出渐进式重构，而不是只会“全统一”或“全拆分”两种极端方案

### 6. 模块 B 精读结论：工作流运行时与状态管理

问题：模块 B 到底负责什么？

思路：把它理解成“workflow 的操作系统”。

方案：
- [backend/app/graphs/state.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/state.py) 定义共享状态容器 `StewardState`
- [backend/app/graphs/checkpoint.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/checkpoint.py) 负责状态序列化、反序列化和 SQLite 持久化
- [backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py) 负责执行 graph、保存 checkpoint、恢复 checkpoint、写 trace

主链路大白话：
- 先基于请求构造一份基础 state
- graph 每跑完一个 step，就把当前业务状态保存成 checkpoint
- 如果下次带 `resume_from_checkpoint=true` 进来，就按 `thread_id + graph_name` 找上次存档
- 如果 checkpoint 已经是 completed 且结果完整，就直接短路返回
- 如果是 waiting / in_progress，就从正确节点继续
- 如果 scope 变了或 checkpoint 不可信，就记一次 miss，然后重新跑

为什么这样设计：
- `StewardState` 统一了 ask / ingest / digest 的最小公共状态，避免每条 graph 各造一套上下文
- checkpoint 只持久化恢复真正需要的字段，不存 trace 和临时 prompt 上下文，避免恢复语义和观测语义耦死
- 恢复时保留 `thread_id`、重置 `run_id`，表示“还是同一次业务事务，但这是一次新的执行”
- checkpoint 保存失败只记错误，不阻断主链路，说明它是增强能力，不是强依赖

模块亮点：
- `runtime.py` 里显式区分 checkpoint hit / miss / completed short-circuit
- `resume_match_fields` 机制可以避免 scoped ingest 因范围变化而误复用旧 checkpoint
- trace sink 和 checkpoint save 都采用 best-effort，不让观测与恢复反向拖垮业务

规模扩大时的瓶颈：
- `StewardState` 会越来越胖，后续需要更细的分层或按 graph 拆子状态
- SQLite checkpoint 在并发 thread 很多时会有写入压力
- 当前 linear graph runner 适合 interview-first，后续分支复杂后会增加恢复语义复杂度

面试一句话：
- 模块 B 解决的是“workflow 跑到一半怎么记住、怎么恢复、怎么避免重复跑和串错上下文”，它是整个系统有状态能力的底座

### 7. 模块 B 高频追问题库

#### 问题 1：为什么恢复时要保留 `thread_id`，但重新生成 `run_id`？

参考回答：
- `thread_id` 表示同一次业务事务，比如同一个治理流程或同一个审批线程
- `run_id` 表示一次具体执行尝试
- 恢复时如果把旧 `run_id` 也原样带回来，新的 trace、日志、审计就会和历史执行混在一起
- 所以恢复语义应该是“延续同一个 thread，但开启一轮新的 run”
- 更完整地说：`thread_id` 保证业务连续性，`run_id` 保证执行可观测性
- 同一个 `thread_id` 下可以有多次 run，这样才能区分首次执行、恢复执行、失败重试分别发生了什么

项目代码落地：
- 代码事实：[backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py#L399) 的 `_hydrate_state_from_checkpoint()` 明确保留当前 `thread_id`
- 代码事实：[backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py#L400) 同时把 `run_id` 重置为本次新执行生成的值
- 代码事实：[backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py#L402) 恢复时还会清空 `trace_events`
- 这说明系统恢复的是业务状态，不是把历史执行记录整包复制回来

更进一步追问：
- 如果恢复时 `run_id` 不重置，会有什么具体问题？

进一步回答：
- trace 会混淆，无法区分第一次执行和恢复执行
- 审计和排障时会看不清到底哪一轮真正调用了模型或写了 checkpoint
- 某些基于 `run_id` 的幂等、指标聚合、错误定位都会失真
- 如果后面要做 run 级别的延迟、失败率、成本统计，也会因为历史执行和当前执行混在一起而污染数据

这题考察的本质：
- 你是否真正理解 `thread_id` 和 `run_id` 的职责边界

#### 问题 2：为什么 checkpoint 只存部分字段，而不是把整个 state 全量落盘？

参考回答：
- 因为 checkpoint 的目标是恢复业务状态，不是做全量运行录像
- 如果把 trace、临时 prompt 上下文、甚至大块原文都塞进去，状态会又大又乱，还会把恢复语义和观测语义耦在一起
- 当前实现只持久化恢复真正需要的结构化字段，比如 action、query、proposal、ask_result、writeback_result、errors 等
- 这样做的 trade-off 是：恢复更干净、状态更稳定、存储更可控，但代价是字段设计要更谨慎，必须明确哪些字段是恢复必需的

项目代码落地：
- 代码事实：[backend/app/graphs/checkpoint.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/checkpoint.py#L51) 用 `PERSISTED_STATE_FIELDS` 显式白名单控制 checkpoint 落盘字段
- 代码事实：[backend/app/graphs/checkpoint.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/checkpoint.py#L79) 注释直接说明不把 trace、临时 prompt 上下文、大块原文塞进 checkpoint，避免恢复语义和观测语义耦死
- 代码事实：[backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py#L260) 对 completed checkpoint 还会做 `required_terminal_fields` 校验，不满足就 fresh start，而不是盲目复用

更进一步追问：
- 那如果少存了字段，恢复不了怎么办？

进一步回答：
- 所以设计 checkpoint 时要先区分“恢复必需字段”和“临时字段”
- 当前项目还加了 `required_terminal_fields` 校验；如果 completed checkpoint 缺少必要结果，不会盲目复用，而是记错误后 fresh start
- 这说明 checkpoint 设计不是“越全越安全”，而是“围绕恢复目标做最小充分集”

这题考察的本质：
- 你是否理解 checkpoint 不是“存得越多越好”，而是“为恢复目标服务”

## Step 3：模块 C 精读（一）`ask_graph`

### 1. 模块定位

问题：`ask_graph` 在三条 graph 里负责什么？

思路：把它讲成“最纯粹的问答工作流”，不要和审批写回混在一起。

方案：
- `ask_graph` 是三条工作流里最简单的一条
- 它负责把一次问答请求组织成固定三段：准备上下文、执行问答、收尾记 trace
- 它不涉及 proposal、审批、写回，所以最适合拿来理解模块 C 的基础骨架

项目代码落地：
- 代码事实：[backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py#L33) 的 `invoke_ask_graph()` 是 ask 链路入口
- 代码事实：[backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py#L47) 通过共享的 `invoke_checkpointed_linear_graph()` 执行
- 代码事实：[backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py#L54) 强制要求最终状态里必须有 `ask_result`

### 2. 主执行链路

问题：一次 ask 请求从进入 graph 到返回结果，中间发生了什么？

思路：按 `invoke -> state -> prepare -> execute -> finalize -> result check` 六步讲。

方案：
1. `invoke_ask_graph()` 先构造 `initial_state`
2. 然后组装 runtime trace hook
3. 再调用统一的 checkpointed linear graph runner
4. graph 内部按顺序跑 `prepare_ask -> execute_ask -> finalize_ask`
5. 跑完后检查 `ask_result` 是否存在
6. 最后把共享执行信息和 ask 专属结果合成 `AskGraphExecution`

项目代码落地：
- 代码事实：[backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py#L82) 的 `build_initial_ask_state()` 在基础 state 上额外初始化了 `retrieved_chunks`
- 代码事实：[backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py#L114) 把 ask workflow 显式固定为三个节点
- 代码事实：[backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py#L58) 如果没有 `ask_result` 会直接抛错，避免 graph “看起来跑完了，但结果是空的”

### 3. 三个节点分别做什么

问题：`prepare_ask / execute_ask / finalize_ask` 各自的职责边界是什么？

思路：要强调“准备、业务执行、收尾观测”三层分工。

方案：
- `prepare_ask`
  - 负责记录最小 trace 元信息
  - 设置 `approval_required=False`
  - 构造临时 prompt 上下文
- `execute_ask`
  - 真正调用 [ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py) 的 `run_minimal_ask()`
  - 把问答结果写回 state
  - 把召回候选也以 `retrieved_chunks` 形式挂回 state，供下游统一消费
- `finalize_ask`
  - 不再改业务结果
  - 只补最后一个 trace 事件，标记 ask 工作流正常结束

项目代码落地：
- 代码事实：[backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py#L147) `prepare_ask` 故意不把原始 query 全量写入 trace，只记录长度和 filter 摘要
- 代码事实：[backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py#L175) `execute_ask` 把 state 重新包装成 `WorkflowInvokeRequest` 再调用 service
- 代码事实：[backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py#L202) `execute_ask` 返回 `ask_result + retrieved_chunks + trace_events`
- 代码事实：[backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py#L212) `finalize_ask` 只做收尾 trace，不碰核心业务字段

### 4. 为什么这样设计

问题：为什么 ask 也要用 graph，而不是直接在 API 层调一个 service 就返回？

思路：不能只回答“为了统一”，要讲出运行时协议、trace、checkpoint 的收益。

方案：
- 第一，统一 ask / ingest / digest 的 runtime 语义，后续 resume、trace、response envelope 都能复用
- 第二，先把 ask 主链路拆成显式节点，后面如果要插 rerank、groundedness gate、query rewrite，会更好演进
- 第三，prepare 和 finalize 把“观测逻辑”和“业务逻辑”分开，避免所有事情都堆进 `run_minimal_ask()`

项目代码落地：
- 代码事实：[backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py#L98) 通过 `StateGraph` 显式定义节点和边
- 代码事实：[backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L48) 真正的检索和生成仍在 service 层，说明 graph 负责编排，不负责吞掉所有业务细节
- 代码事实：[backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L77) service 层还做了 citation 编号校验，保证模型输出和证据集合没有明显脱钩

### 5. 模块亮点与瓶颈

亮点：
- 把 ask 主链路压缩成最清楚的三段式，面试时很好讲
- trace 里只记 query 长度，不记原文，这是一个很像真实工程的隐私与观测权衡
- graph 层只做编排，service 层处理 retrieval 和 answer generation，边界清楚

规模扩大时的瓶颈：
- 如果后续加 query rewrite、rerank、groundedness 校验、答案后处理，线性节点会继续膨胀
- 当前 `execute_ask` 把整个 ask service 当成一个黑盒节点，后续若要更细粒度排障，可能要把它继续拆节点
- `retrieved_chunks` 整体挂回 state，在候选很多时会让状态体积变大

面试一句话：
- `ask_graph` 本质上是一个最小可恢复的问答工作流：prepare 负责准备上下文和最小观测，execute 调检索加生成服务，finalize 负责收尾；它不是为了炫技上 graph，而是为了和其他 workflow 共享同一套运行时语义。

### 6. `ask_graph` 高频追问题库

#### 问题 1：为什么要拆成 `prepare_ask -> execute_ask -> finalize_ask`，而不是直接在 API 层调一次 `run_minimal_ask()`？

参考回答：
- 因为 `run_minimal_ask()` 只应该负责问答业务本身，不应该同时吞掉工作流编排、trace、checkpoint 语义
- `prepare_ask` 负责准备运行上下文和最小观测数据
- `execute_ask` 负责真正的 retrieval + generation
- `finalize_ask` 负责收尾 trace 和工作流结束语义
- 这样拆分后，graph 层负责“怎么跑”，service 层负责“具体干什么”，边界会更清楚

项目代码落地：
- 代码事实：[backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py#L135) `prepare_ask` 只写最小 trace 和临时上下文
- 代码事实：[backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py#L169) `execute_ask` 才真正调用 `run_minimal_ask()`
- 代码事实：[backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py#L212) `finalize_ask` 只做收尾 trace

更进一步追问：
- 如果以后要在 ask 链路里新增 rerank、query rewrite、groundedness gate，你会把它们放在哪一层？

进一步回答：
- 我会优先把它们建成新的 graph 节点，而不是继续把逻辑塞进 `run_minimal_ask()`
- 因为这些步骤都属于可编排、可观测、可单独失败处理的流程节点
- 只有真正强耦合的检索或生成细节，才继续留在 service 内部

这题考察的本质：
- 你是否真的理解“graph 负责编排，service 负责业务细节”

## Step 3：模块 C 精读（二）`ingest_graph`

### 1. 模块定位

问题：`ingest_graph` 在三条 graph 里负责什么？

思路：把它讲成“索引同步主干 + 审批控制分支”的治理工作流。

方案：
- `ingest_graph` 的基础职责是把目标笔记或整个 vault 同步进 SQLite 索引
- 当请求只是普通同步时，它走最小线性主干
- 当请求显式要求 `approval_mode=proposal` 时，它会在同步完成后额外生成治理 proposal，并把 thread 停在 `waiting_for_approval`

项目代码落地：
- 代码事实：[backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py#L48) 的 `invoke_ingest_graph()` 先判断是否需要走审批 proposal 分支
- 代码事实：[backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py#L76) 普通路径复用统一的 `invoke_checkpointed_linear_graph()`
- 代码事实：[backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py#L69) 只有 `require_approval + approval_mode=proposal` 才会进入 `_invoke_ingest_graph_with_approval()`

### 2. 主干三节点分别做什么

问题：为什么主干仍然保持 `prepare -> execute -> finalize`？

思路：要区分“低风险索引同步主流程”和“高风险写回审批控制流”。

方案：
- `prepare_ingest`
  - 规范化 scope，记录本次是 `scoped_notes` 还是 `full_vault`
  - 初始化最小 trace 和临时上下文
- `execute_ingest`
  - 真正调用 ingest pipeline，把笔记写入索引库
  - 返回扫描量、创建量、更新量、chunk 数等结构化结果
- `finalize_ingest`
  - 不再碰 ingest 业务结果
  - 只补收尾 trace，标记工作流正常结束

项目代码落地：
- 代码事实：[backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py#L184) `prepare_ingest` 只做范围归一化和 trace 初始化
- 代码事实：[backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py#L218) `execute_ingest` 真正调用 `ingest_vault()`
- 代码事实：[backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py#L268) `finalize_ingest` 只做收尾 trace

### 3. 为什么要额外接审批分支

问题：既然主干已经能跑完，为什么还要再接一条 proposal / waiting 分支？

思路：答案不能只停在“有的场景需要审批”，还要讲出控制面隔离和状态语义。

方案：
- 第一，不是每次 ingest 都有高风险动作。普通索引同步本身是低风险后台动作，不应该被审批流拖慢
- 第二，proposal 是“治理建议”和“潜在写回”的控制面，它不等于 ingest 本身的基础成功语义
- 第三，如果把 `human_approval` 硬塞进主干线性图，会让所有 ingest 都被迫理解 proposal、pending 状态和 resume 语义，低风险路径会被高风险控制面污染
- 第四，现在的做法是：先让 ingest 主干把基础事实跑出来，再按需叠加治理分析、proposal 落盘和 `waiting_for_approval` checkpoint，这样状态边界更清楚

项目代码落地：
- 代码事实：[backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py#L290) 审批路径先复用 `prepare_ingest` 和 `execute_ingest`
- 代码事实：[backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py#L309) 然后才调用 `build_scoped_ingest_approval_proposal()`
- 代码事实：[backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py#L324) 如果没有 proposal，就回到普通完成语义，直接 `finalize + completed checkpoint`
- 代码事实：[backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py#L362) proposal 和 waiting checkpoint 必须原子落盘，避免插件拿到 proposal 但 thread 还不在 waiting 状态

### 4. proposal 分支到底额外做了什么

问题：审批分支不是“多一个 if”而已，它到底新增了哪些职责？

思路：要拆成“分析、提案、持久化等待态”三件事。

方案：
- 先基于 scoped note 做 retrieval-backed analyze，补齐 `analysis_result` 和 `analysis_issues`
- 再构造 `Proposal`，里面包含 summary、risk_level、evidence、patch_ops、before_hash
- 最后把 `proposal` 和 `waiting_for_approval` checkpoint 原子落盘，交给插件审批面板与 `/workflows/resume`

项目代码落地：
- 代码事实：[backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py#L62) `build_scoped_ingest_approval_proposal()` 只覆盖单 note scoped ingest
- 代码事实：[backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py#L167) 会先做 related retrieve，再汇总 governance findings
- 代码事实：[backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py#L227) 生成的 proposal 同时包含 frontmatter merge 和 review section insert 两类 patch op

### 5. 模块亮点与瓶颈

亮点：
- 把“索引同步”和“治理审批”解耦，避免每次 ingest 都被高风险控制面绑架
- proposal 分支先复用主干结果，再叠加分析和等待态，说明它不是平行重做一遍业务
- `proposal + waiting checkpoint` 原子落盘，这是真实工程里很重要的一类一致性保护

规模扩大时的瓶颈：
- 当前 proposal 只支持单 note scoped ingest，多 note 合并会立刻变成跨 note 冲突裁决问题
- `execute_ingest` 仍是一个大黑盒，后续若要做更细粒度失败恢复，可能还要再拆索引节点
- 现在的治理分析主要基于最小 related retrieve，数据量扩大后，召回质量和分析耗时都会成为瓶颈

面试一句话：
- `ingest_graph` 不是把审批硬塞进索引流程，而是保留低风险线性主干，再按需叠加 proposal / waiting 控制分支。这样既守住普通 ingest 的简单性，也给高风险写回留出了清晰的暂停与恢复边界。

### 6. `ingest_graph` 高频追问题库

#### 问题 1：为什么不把 `human_approval` 直接塞进线性三节点里，而是保留线性主干，再额外走 proposal / waiting 分支？

参考回答：
- 因为 ingest 的基础成功语义是“索引同步完成”，而不是“proposal 一定产生”
- 不是每次 ingest 都有高风险写回动作，如果把审批硬塞进主干，就会让所有低风险同步都背上 proposal、pending、resume 的复杂状态
- 当前做法是先跑通低风险主干，再按需叠加治理分析和审批等待态，这样控制面边界更清楚
- 同时 proposal 和 waiting checkpoint 采用原子落盘，避免出现“前端拿到 proposal，但后端 thread 还没进入 waiting”这种状态不一致

项目代码落地：
- 代码事实：[backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py#L69) 只有审批模式才进入 proposal 分支
- 代码事实：[backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py#L324) proposal 构建失败或不适用时，仍然可以回到普通 completed 语义
- 代码事实：[backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py#L364) proposal 与 waiting checkpoint 在同一个事务里落盘

更进一步追问：
- 如果未来 `ingest_graph` 要支持批量多 note proposal，你会优先扩 proposal builder，还是先重构 graph 节点边界？

进一步回答：
- 我会先重构 graph 节点边界，再扩 proposal builder
- 因为多 note proposal 不只是 patch 变多，而是会引入跨 note 的冲突裁决、证据聚合、审批展示和失败恢复语义
- 如果 graph 仍然把所有复杂度塞进一个 proposal builder，后续会很难观测、测试和恢复

这题考察的本质：
- 你是否真的理解“低风险主流程”和“高风险控制分支”应该解耦

## Step 3：模块 C 精读（三）`digest_graph`

### 1. 模块定位

问题：`digest_graph` 在三条 graph 里负责什么？

思路：把它讲成“基于已索引笔记生成复盘结果，再按需包一层审批 proposal”的工作流。

方案：
- `digest_graph` 的基础职责是从已索引笔记里挑选 source notes，生成一份最小 `digest_result`
- 它的主干仍是低风险线性流程：准备上下文、构建 digest、收尾 trace
- 当请求显式要求审批时，它不会像 `ingest_graph` 那样再做一轮 retrieval-backed analyze，而是直接把已有 `digest_result` 包装成 proposal，并进入 `waiting_for_approval`

项目代码落地：
- 代码事实：[backend/app/graphs/digest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/digest_graph.py#L40) `invoke_digest_graph()` 与 `ingest_graph` 一样，先判断是否进入审批 proposal 分支
- 代码事实：[backend/app/graphs/digest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/digest_graph.py#L67) 普通路径仍复用统一的 `invoke_checkpointed_linear_graph()`
- 代码事实：[backend/app/graphs/digest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/digest_graph.py#L104) 当前 digest 不支持 note 级 scope，只处理整个 indexed vault

### 2. 主干三节点分别做什么

问题：`digest_graph` 的线性主干是什么？

思路：强调“先产出稳定结果，再决定是否需要审批写回”。

方案：
- `prepare_digest`
  - 记录当前 digest 范围是 `indexed_vault`
  - 初始化 trace 和临时上下文
- `build_digest`
  - 真正调用 `run_minimal_digest()`，从索引库里挑 source notes，生成模板化复盘结果
  - 如果当前没有合适笔记，会走 fallback，而不是直接让 workflow 崩掉
- `finalize_digest`
  - 只补收尾 trace，不再修改 digest 业务结果

项目代码落地：
- 代码事实：[backend/app/graphs/digest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/digest_graph.py#L160) `prepare_digest` 只做 trace 初始化和上下文准备
- 代码事实：[backend/app/graphs/digest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/digest_graph.py#L189) `build_digest` 真正调用 `run_minimal_digest()`
- 代码事实：[backend/app/services/digest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/digest.py#L25) `run_minimal_digest()` 会从索引中选 source notes，并构造 `digest_markdown`

### 3. 为什么它的审批分支比 `ingest_graph` 轻

问题：为什么 `digest_graph` 进入 proposal 分支后，没有像 `ingest_graph` 那样先做 retrieval-backed analyze？

思路：核心是两者的“风险来源”不同。

方案：
- `ingest_graph` 的 proposal 目标是“治理一篇具体笔记”，风险来自重复、孤立、缺 frontmatter、缺双链等结构问题，所以 proposal 前必须先做分析和证据聚合
- `digest_graph` 的 proposal 目标更直接：把已经生成好的 digest 文本写进一篇已有笔记
- 也就是说，digest 的高风险点主要在“写回动作本身”，而不是“是否存在复杂治理诊断”
- 所以它的审批分支更像给现有 `digest_result` 包一层受限写回外壳，而不是再引入一套 analyze 阶段

项目代码落地：
- 代码事实：[backend/app/graphs/digest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/digest_graph.py#L257) proposal 直接基于已有 `digest_result` 构建
- 代码事实：[backend/app/services/digest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/digest.py#L54) `build_digest_approval_proposal()` 只做 target note 选择、patch op 组装和 safety check
- 代码事实：[backend/app/services/digest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/digest.py#L88) 当前 proposal 明确被限制成“已有笔记上的 frontmatter merge + digest 文本插入”

### 4. 它和 `ingest_graph` 最关键的差异

问题：`digest_graph` 和 `ingest_graph` 长得很像，面试里怎么讲出差异？

思路：从“主干产物”和“审批前复杂度”两个维度对比。

方案：
- 相同点：
  - 都保留低风险线性主干
  - 都只在审批模式下叠加 proposal / waiting 分支
  - 都要求 `proposal + waiting checkpoint` 原子落盘
- 不同点：
  - `ingest_graph` 主干产物是索引同步结果，proposal 前要额外做治理分析
  - `digest_graph` 主干产物已经是可展示的 digest 结果，proposal 只是把这个结果转成受限写回动作
  - `ingest_graph` 更像“先诊断，再提案”；`digest_graph` 更像“先产出结果，再决定是否写回”

项目代码落地：
- 代码事实：[backend/app/graphs/digest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/digest_graph.py#L292) 与 [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py#L362) 一样，proposal 和 waiting checkpoint 都在同一事务里落盘
- 代码事实：[backend/app/services/digest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/digest.py#L58) digest proposal 的 patch op 只有两类：frontmatter merge 和插入 digest 文本
- 代码事实：[backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py#L167) ingest proposal 则先做 related retrieve 和 finding 汇总

### 5. 模块亮点与瓶颈

亮点：
- 先把 `digest_result` 作为稳定中间产物钉死，再按需叠加审批写回，边界清楚
- 即使没有合适 source notes，也先走 fallback，而不是让 workflow 整体失效
- proposal 写回边界被限制得很保守，方便和现有受限 patch op 体系复用

规模扩大时的瓶颈：
- 当前 digest 还是模板化摘要，不是真正的主题聚类和开放环抽取
- 现在只支持整库 digest，不支持时间窗口或 note scope
- source note 选择和 target note 选择规则都比较简单，后续容易被面试官追问质量和污染风险

面试一句话：
- `digest_graph` 的设计重点不是“复杂分析”，而是“先得到稳定 digest 结果，再决定要不要把它安全写回”。所以它的审批分支更轻，更像给结果加一层可审批、可恢复的写回外壳。

### 6. `digest_graph` 高频追问题库

#### 问题 1：为什么 `digest_graph` 里即使开启审批模式，也不需要像 `ingest_graph` 一样先做 retrieval-backed analyze？

参考回答：
- 因为两者的风险来源不同
- `ingest_graph` 面对的是单篇笔记治理，proposal 前必须先判断有没有重复、孤立、结构缺陷等治理问题
- `digest_graph` 的主干已经产出了 `digest_result`，审批阶段主要只是决定“要不要把这段结果写回某篇已有笔记”
- 所以它不需要额外插入一套治理分析链路，而是直接把现有结果包装成 proposal，并用 safety check 和人工审批兜底

项目代码落地：
- 代码事实：[backend/app/graphs/digest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/digest_graph.py#L257) 直接用 `digest_result` 构建 proposal
- 代码事实：[backend/app/services/digest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/digest.py#L63) target note 和 patch op 都在 proposal builder 里直接确定
- 代码事实：[backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py#L167) `ingest_graph` 则必须先做 related retrieve 和 finding 收敛

这题考察的本质：
- 你能不能分清“内容诊断型 proposal”和“结果写回型 proposal”

#### 问题 2：如果当前索引里暂时没有 `daily_note / summary_note`，为什么 `digest_graph` 不直接失败，而是 fallback 到最近更新的通用笔记？

参考回答：
- 因为 `daily_note / summary_note` 是解析阶段给现有笔记打的 `note_type` 标签，不是 Agent 新建的特殊对象
- `digest_graph` 优先选这两类笔记，是因为它们更接近“复盘素材”，用来生成 digest 语义更稳
- 但如果索引里暂时没有这两类笔记，直接失败会让 workflow 可用性太差，所以系统退回最近更新的 `generic_note`
- 这是一种明确的 trade-off：优先保证“有结果可用”，代价是这次 digest 的复盘语义可能没那么纯，质量会下降
- 更好的生产化做法是把这种 fallback 明确打标、暴露到 trace 和结果里，而不是悄悄降级

项目代码落地：
- 代码事实：[backend/app/indexing/parser.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/parser.py#L38) 解析器会把现有笔记识别为 `daily_note / summary_note / generic_note`
- 代码事实：[backend/app/services/digest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/digest.py#L22) digest 默认优先消费 `daily_note` 和 `summary_note`
- 代码事实：[backend/app/services/digest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/digest.py#L119) 如果优选类型不够，会补充最近更新的通用笔记
- 代码事实：[backend/app/services/digest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/digest.py#L273) 退回通用笔记时，会在 digest 文本里明确写出 fallback 说明

### 7. 模块 C 总收束

问题：三条 graph 放在一起，面试里应该怎么总结？

思路：用“共性 + 差异”两段式。

方案：
- 共性：
  - 三条 graph 都复用了统一 runtime contract
  - 都保留 `prepare -> execute/build -> finalize` 这种低风险线性主干
  - 都把 trace、checkpoint、thread_id/run_id 语义收进统一工作流控制面
- 差异：
  - `ask_graph` 是最小问答流，没有 proposal 和写回
  - `ingest_graph` 是内容治理流，审批前要先做分析和提案
  - `digest_graph` 是结果写回流，先产出 digest，再按需给结果包 proposal 外壳

面试一句话：
- 这三个 graph 不是三个风格完全不同的系统，而是在同一套 workflow runtime 上，分别承载“问答、治理、复盘”三类业务；区别主要在高风险控制分支的复杂度不同。

### 8. 补充概念：`runtime contract` 是什么

问题：这里反复提到的 `runtime contract` 到底是什么？

思路：把它翻译成“workflow 运行时的公共协议”，不要讲成抽象空话。

方案：
- `runtime contract` 不是业务规则，而是三条 workflow 在运行时共同遵守的一套控制面约定
- 它主要回答四件事：
  - graph 开始前，公共 state 至少长什么样
  - trace 事件怎么记录、写到哪里
  - checkpoint / resume 按什么语义恢复
  - graph 跑完后，如何统一包装成 execution 结果
- 所以它更像“共享运行协议”，解决的是“怎么统一执行、观测、恢复和返回”，不是“具体业务结果长什么样”

项目代码落地：
- 代码事实：[backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py#L113) `build_base_workflow_state()` 统一了初始 state
- 代码事实：[backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py#L138) `build_workflow_runtime_trace_hook()` 统一了 trace sink
- 代码事实：[backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py#L151) `build_workflow_graph_execution()` 统一了执行结果包装
- 代码事实：[backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py#L203) `invoke_checkpointed_linear_graph()` 统一了 checkpoint / resume / completed short-circuit 语义

面试一句话：
- `runtime contract` 就是 workflow 的共享运行协议，统一的是执行控制面，不是业务结果本身。

### 9. 补充概念：为什么 `runtime contract` 没做成更强约束的抽象基类

问题：既然三条 graph 都要遵守统一 runtime contract，为什么这里没直接上抽象基类强约束？

思路：从 Python 工程现实、当前复杂度和演进成本三点回答。

方案：
- 第一，这个项目当前共享的是“运行时骨架”，不是完整业务接口；真正统一的是 base state、trace hook、checkpoint runner、execution envelope，而不是所有 graph 都有完全相同的方法签名
- 第二，Python 这里更适合用“共享函数 + 共享 dataclass + 约定式接入”，因为 ask / ingest / digest 虽然共用控制面，但业务结果字段明显不同
- 第三，如果过早上强抽象基类，很容易把还没稳定的变化点锁死，后面每多一种 workflow 都得先和抽象搏斗
- 所以当前是半显式 contract：公共运行语义集中在 `runtime.py`，各 graph 主动按统一方式接线；这样既能复用，又保留了业务侧演进空间

项目代码落地：
- 代码事实：[backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py#L113) 共享 `build_base_workflow_state()`
- 代码事实：[backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py#L138) 共享 `build_workflow_runtime_trace_hook()`
- 代码事实：[backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py#L151) 共享 `build_workflow_graph_execution()`
- 代码事实：[backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py#L203) 共享 `invoke_checkpointed_linear_graph()`

面试一句话：
- 这里不是没有 contract，而是故意没把它做成过硬的继承体系；因为当前更需要统一运行语义，而不是提前把所有 workflow 的业务形态抽象成一个僵硬父类。

## Step 3：模块 D 精读（一）文档解析与索引构建

### 0. 术语补课：模块 D 里的基础解析概念

问题：`Markdown AST`、`heading`、`wikilink`、`task`、`frontmatter` 分别是什么？

思路：先用 Obsidian 用户视角解释，再落到 parser 为什么只抓这些信号。

方案：
- `heading`
  - 就是 Markdown 里的标题，比如 `# 一级标题`、`## 二级标题`
  - 作用：帮助系统按章节切分内容，形成更稳定的 chunk 边界
- `wikilink`
  - 就是 Obsidian 常见的 `[[笔记名]]` 内链
  - 作用：反映一篇笔记和其他笔记的显式关联
- `task`
  - 就是 `- [ ] 待办` 或 `- [x] 已完成` 这样的任务项
  - 作用：帮助系统识别行动项、任务密度和复盘价值
- `frontmatter`
  - 就是 Markdown 文件最上面的 `---` 包起来那段元数据，比如标签、别名、状态
  - 作用：给后续治理状态和筛选规则留结构化落点
- `Markdown AST`
  - AST 是“抽象语法树”
  - 大白话：不是把文件当普通文本硬扫，而是把整篇 Markdown 解析成一棵语法结构树，知道哪里是标题、列表、表格、代码块、引用块，它们之间怎么嵌套
  - 它更强，但也更复杂
- `scoped ingest`
  - 意思是“只同步指定的一篇或几篇笔记”
  - 对应的反义词是 `full_vault ingest`，也就是整库同步
  - 作用：写回成功后、局部改动后，只刷新受影响的 note，而不是每次都重扫整个 vault
- `FTS`
  - 是 `Full-Text Search`，全文检索
  - 在这个项目里主要指 SQLite 的 `FTS5` 虚表，也就是 [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py) 里的 `chunk_fts`
  - 大白话：它像一张专门给搜索准备的“倒排索引表”，不是主数据表本身
- `整张 FTS`
  - 不是指“一篇笔记的全文”
  - 而是指整个 `chunk_fts` 全文索引表统一重建
- 两者区别
  - “够用解析”可以理解成只抽 AST 里当前业务最关心的那部分结构信号
  - 但它不等于“已经有完整 AST，只是少用一点”，而是压根没有走完整语法树建模这条更重的路线
  - 当前项目是有意识地只抓 heading / wikilink / task / frontmatter 这些高价值信号，优先支撑检索、digest 和治理

面试一句话：
- 模块 D 当前先抓对检索和治理最有价值的结构信号，而不是一开始就上完整 Markdown AST 解析器。

### 1. 模块定位

问题：模块 D 到底负责什么？

思路：按“解析 -> 结构化 -> 入库”三段讲。

方案：
- [`parser.py`](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/parser.py) 负责把 Markdown 读成结构化 `ParsedNote`
- [`ingest.py`](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py) 负责遍历 vault、调用 parser、驱动写库
- [`store.py`](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py) 负责把 note/chunk/fts/embedding 这些结构稳定落进 SQLite

面试一句话：
- 模块 D 是知识库底座，解决“原始 Markdown 怎么变成后续可检索、可治理、可评估的数据事实”。

### 2. 主调用链

问题：一篇 Markdown 从文件到索引，中间经过了什么？

思路：按函数调用链讲最清楚。

方案：
1. `ingest_vault()` 先决定这轮 ingest 是全库还是 scoped note
2. 对每篇 note 调 `parse_markdown_note()`
3. 用 `build_note_record()` 和 `build_chunk_records()` 把解析结果转成数据库记录
4. 用 `sync_note_and_chunks()` 做单 note 事务写入
5. 可选同步 embedding
6. 最后统一重建 `chunk_fts`

项目代码落地：
- 代码事实：[backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py#L84) `ingest_vault()` 是主入口
- 代码事实：[backend/app/indexing/parser.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/parser.py#L56) `parse_markdown_note()` 产出 `ParsedNote`
- 代码事实：[backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py#L582) `build_note_record()` 和 [backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py#L605) `build_chunk_records()` 负责映射成落库对象
- 代码事实：[backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py#L822) `sync_note_and_chunks()` 负责 note 级幂等写入

### 3. `parser.py` 为什么先做“够用解析”

问题：为什么 parser 没一开始就上复杂 Markdown AST？

思路：核心是 MVP 边界和目标信号。

方案：
- 当前项目最需要的不是完美还原 Markdown 语法，而是先抽出对治理和检索最有价值的信号
- 所以 parser 先抓：
  - heading
  - wikilink
  - task
  - frontmatter 是否存在
  - note_type / template_family / daily_note_date
- 这些信号已经足够支撑后续 ask、digest、ingest proposal 的大部分基础能力

项目代码落地：
- 代码事实：[backend/app/indexing/parser.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/parser.py#L10) 到 [backend/app/indexing/parser.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/parser.py#L14) 只定义了几类核心正则
- 代码事实：[backend/app/indexing/parser.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/parser.py#L38) `_infer_note_type()` 会识别 `daily_note / summary_note / generic_note`
- 代码事实：[backend/app/indexing/parser.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/parser.py#L72) `flush_chunk()` 用 heading 边界切 chunk

### 4. `store.py` 的核心设计

问题：为什么写库不是做复杂 diff，而是按 note 整体替换 chunk？

思路：先讲幂等性，再讲复杂度控制。

方案：
- note 表存的是一篇笔记的整体事实：路径、标题、类型、mtime、frontmatter 状态、任务数、出链
- chunk 表存的是切分后的检索单元
- 当前策略是“单 note 事务 + 整 note replace”
- 原因是这样最容易守住幂等边界：标题重排、段落改写、chunk 数量变化时，旧 chunk 不会残留脏数据

项目代码落地：
- 代码事实：[backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py#L660) `upsert_note()` 先更新 note 事实
- 代码事实：[backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py#L718) `replace_chunks_for_note()` 先删旧 chunk，再插新 chunk
- 代码事实：[backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py#L822) `sync_note_and_chunks()` 用单 note 事务收口

### 5. 模块亮点与瓶颈

亮点：
- parser 只抓高价值结构信号，MVP 很克制
- ingest 顺序显式排序，保证测试、trace、审计统计稳定
- embedding 被设计成“可选增强链路”，provider 不可用时不拖垮主索引
- FTS 统一重建，先守住“写库完成 = 检索可用”的一致性边界

规模扩大时的瓶颈：
- regex parser 对复杂表格、代码块、嵌套列表的语义理解有限
- 全量重建 FTS 在大 vault 上会越来越慢
- 单 note replace 简单稳定，但更新量很大时写放大会明显增加

### 6. 模块 D 高频追问题库

#### 问题 1：为什么 parser 没有一开始就做特别复杂的 Markdown AST，而是先做够用的 heading / wikilink / task / frontmatter 解析？

参考回答：
- 因为当前项目最重要的是尽快抽出治理和检索最有用的结构信号，而不是完整复刻 Markdown 渲染语义
- heading、wikilink、task、frontmatter、note_type 已经足够支撑 chunk 切分、类型判断、digest 输入选择、governance finding 和后续检索
- 如果一开始就上复杂 AST，开发成本和调试成本都会显著上升，但短期业务收益不一定匹配
- 所以首版选择“够用解析”，先把知识库底座跑稳，后续再按 bad case 逐步补复杂语法支持
- 面试作答压缩版：
  - 当前项目只需要部分高价值结构信息，而不是完整语法信息；因此首版先做够用解析，用更低复杂度支撑检索、digest 和治理，等 bad case 暴露后再考虑升级到更重的 AST 路线

#### 问题 2：为什么这里写库采用“按单篇 note 整体替换 chunk”，而不是做更细粒度的局部 diff 更新？

参考回答：
- 是的，当前实现的意思就是：当一篇 note 重新 ingest 时，会先重新解析出这篇 note 的完整 chunk 列表，然后把数据库里属于这篇 note 的旧 chunk 全删掉，再插入这次新的 chunk 结果
- 这样做的核心原因不是性能最优，而是幂等边界最清楚
- 因为标题重排、段落改写、heading 层级变化、chunk 数量变化时，旧 chunk 很容易残留成脏数据；如果一开始就做最小 diff，需要先解决“怎样稳定识别新旧 chunk 是同一个语义单元”这个更难的问题
- 当前 chunk_id 里带有路径、heading_path、起止行号，这些字段一旦变化，做局部 diff 的稳定性就会明显下降
- 所以首版先用“单 note 事务 + 整 note replace”守住正确性，再接受一定写放大

项目代码落地：
- 代码事实：[backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py#L718) `replace_chunks_for_note()` 会先统计旧 chunk 数，再删除这篇 note 的所有 chunk
- 代码事实：[backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py#L735) 然后批量插入这次新的 chunk 记录
- 代码事实：[backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py#L822) `sync_note_and_chunks()` 用单 note 事务收口整个替换过程
- 代码事实：[backend/app/indexing/parser.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/parser.py#L78) chunk_id 当前和 `path + heading_path + start_line + end_line` 绑定，不是天然适合做稳定 diff 的长期 ID

面试作答压缩版：
- 当前不是不知道 chunk 级 diff 更省写，而是优先选择更稳的幂等边界。首版先保证一篇 note 重跑后数据库状态一定正确，没有旧 chunk 残留；等数据规模上来，再考虑引入稳定 chunk identity、增量 FTS 和更细粒度更新。
- 用户回答修正版：
  - 更细粒度 diff 稳定性更差，需要更复杂的 chunk 身份管理和更新规则；首版优先选择 `整 note replace chunk`，用更简单的实现守住正确性、幂等性和无脏数据残留。

#### 问题 3：为什么即使当前是 scoped ingest，这里也仍然统一重建整张 FTS，而不是只更新受影响的部分？

参考回答：
- 因为当前项目优先守的是“一次 ingest 完成后，全文检索一定和主库一致”这个一致性边界
- 如果一开始就做局部 FTS 增量同步，需要额外解决删除、改名、chunk 重排、异常中断后的漂移恢复问题
- 现在的实现虽然更重，但边界最清楚：主库写完，再统一重建 FTS，就能保证 `note/chunk` 和 `chunk_fts` 不会长期不一致
- 这也是典型的 MVP 取舍：先用更重但更稳的全量重建换正确性，后面再在大数据量场景下优化成增量同步

项目代码落地：
- 代码事实：[backend/app/indexing/ingest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/ingest.py#L140) 即使 scoped ingest，当前也统一调用 `rebuild_chunk_fts_index()`
- 代码事实：[backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py#L853) `rebuild_chunk_fts_index()` 会先清空 `chunk_fts`，再按最新主表全量重建
- 用户追问版理解：
  - `scoped ingest` 明明只改了几篇 note，为什么还要把整张 `chunk_fts` 都重建？
  - 答案是：当前项目优先保证 `note/chunk` 主表和 `chunk_fts` 搜索索引绝不漂移；如果一开始就做局部增量更新，还要额外解决删除、改名、chunk 重排和异常中断后的恢复问题，复杂度更高
- 面试作答压缩版：
  - 当前不是不想做 FTS 增量更新，而是先用“全量重建”守住最清晰的一致性边界：一轮 ingest 结束后，搜索索引一定和主库一致。代价是性能更重，但首版更稳。
- 用户回答修正版：
  - 局部增量更新面对很多细粒度改动时复杂度太高；重建整张 FTS 虽然更重，但能持续保证索引表和主表一致。

### 7. 模块 D 首轮收束

问题：模块 D 这一轮最应该带走的结论是什么？

思路：把“正确性优先”讲透。

方案：
- parser 首版只做“够用解析”，先抽最有业务价值的结构信号
- ingest 以稳定顺序驱动“解析 -> 结构化 -> 写库”
- store 以“单 note 事务 + 整 note replace”守住幂等边界
- FTS 以“整表重建”守住主库与搜索索引的一致性边界
- embedding 被放在主索引之后，作为可降级增强链路

面试一句话：
- 模块 D 的核心不是把 Markdown 解析得多完美，而是先用最稳的方式把知识库底座做正确，再逐步优化性能和增量能力。

项目代码落地：
- 代码事实：[backend/app/indexing/parser.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/parser.py#L10) 到 [backend/app/indexing/parser.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/parser.py#L14) 只覆盖了当前最关键的结构信号
- 代码事实：[backend/app/indexing/parser.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/parser.py#L95) 到 [backend/app/indexing/parser.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/parser.py#L119) chunk 切分也围绕 heading 边界展开

## Step 3：模块 E 精读（一）检索与问答生成

### 1. 模块定位

问题：模块 E 到底负责什么？

思路：按“召回事实 -> 组织证据 -> 生成回答 -> 守住可信边界”四段讲。

方案：
- `sqlite_fts.py` 负责关键词 / 全文检索
- `sqlite_vector.py` 负责语义检索
- `hybrid.py` 负责把两路候选融合成统一 candidate 集合
- `ask.py` 负责把 candidate 变成 citation，再尝试生成带引用答案，并在失败时安全降级

面试一句话：
- 模块 E 的本质不是“让模型回答问题”，而是把索引里的事实稳妥地转成“可引用、可降级、可审计”的答案。

### 2. 主执行链路

问题：一个 `ask_qa` 请求从 query 到 answer，中间到底经过了什么？

思路：按主函数调用顺序讲最稳。

方案：
1. `run_minimal_ask()` 先校验 query 非空
2. 调 `search_hybrid_chunks_in_db()` 拿统一 candidate
3. 用 `_build_citations()` 把 candidate 映射成引用
4. 没有 candidate 就直接返回 `no_hits`
5. 有 candidate 就调用 `_try_generate_grounded_answer()`
6. 如果模型返回了答案，再用 `_validate_generated_answer_citations()` 做编号对齐校验
7. 校验通过返回 `generated_answer`
8. 校验失败或 provider 不可用，则降级为 `retrieval_only`

项目代码落地：
- 代码事实：[backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L39) `run_minimal_ask()` 是 ask 主入口
- 代码事实：[backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L48) 到 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L55) 先走 hybrid retrieval
- 代码事实：[backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L129) 到 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L166) 把 candidate 转成 citation 或 retrieval-only 文本
- 代码事实：[backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L169) 到 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L192) 做 citation 编号校验

### 3. 为什么它不是普通 RAG

问题：为什么不能只说“这里做了 hybrid RAG”？

思路：关键不是有没有检索，而是有没有把失败面定义清楚。

方案：
- 普通 RAG 往往是“检索几段文本 -> 拼 prompt -> 返回答案”
- 这个项目额外做了四层工程控制：
  - 有统一 candidate contract
  - 有 `generated_answer / retrieval_only / no_hits` 三种显式模式
  - 有 `retrieval_fallback` 和 `model_fallback` 两类不同降级面
  - 有 citation 编号对齐校验，防止模型输出“看起来像引用、其实已经漂移”的答案

项目代码落地：
- 协议事实：[backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py#L145) `RetrievedChunkCandidate` 保留路径、标题、行号、分数、原文
- 协议事实：[backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py#L181) `RetrievalSearchResponse` 显式保留 fallback / disabled / provider 信息
- 协议事实：[backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py#L193) `AskWorkflowResult` 显式保留结果模式和降级原因

面试一句话：
- 这个 ask 链路不是“把 RAG 接上模型”就结束，而是把召回、生成和失败边界都收敛进统一协议，确保回答既能引用证据，也能在异常时可解释地降级。

### 4. hybrid retrieval 的关键取舍

问题：为什么这里先用 RRF，而不是直接把 FTS 分数和 cosine 分数相加？

思路：先讲量纲问题，再讲 scope control。

方案：
- FTS 的 BM25 分数和向量 cosine 分数不在一个量纲上
- 如果一开始就硬做线性加权，很容易把系统变成调参实验
- 所以当前先用 rank-based 的 RRF 融合，把 hybrid 做成稳健底座
- 同时，metadata filter fallback 放在 hybrid 总入口统一处理，避免 FTS 和 vector 各自放宽条件，最后拼出一组“来源条件不一致”的候选

项目代码落地：
- 代码事实：[backend/app/retrieval/hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/hybrid.py#L55) 到 [backend/app/retrieval/hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/hybrid.py#L73) 统一处理 filter fallback
- 代码事实：[backend/app/retrieval/hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/hybrid.py#L114) 到 [backend/app/retrieval/hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/hybrid.py#L145) 同时调 FTS 和 vector
- 代码事实：[backend/app/retrieval/hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/hybrid.py#L186) 到 [backend/app/retrieval/hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/hybrid.py#L215) 用 RRF 融合和排序

### 5. 模块亮点与瓶颈

亮点：
- 把检索、生成、引用、降级拆成清晰的可观测阶段
- 把 filter fallback 收敛到 hybrid 总入口，避免多路检索条件漂移
- 把向量 provider 不可用、索引未就绪、真的没召回区分开，而不是都伪装成 no-hit

规模扩大时的瓶颈：
- `sqlite_vector.py` 当前是读出候选 embedding 后做 Python 侧余弦排序，大 Vault 下会先遇到延迟和内存压力
- 目前只有 citation 编号对齐校验，还没有真正的线上语义 groundedness gate
- ask 当前只取 top-4 candidate，在长问题或跨主题问题下可能不够

### 6. 模块 E 高频追问题库

#### 问题 1：为什么 `retrieval_fallback` 和 `model_fallback` 不能混成一个“低置信回答”字段？

参考回答：
- 因为它们代表的是两种完全不同的失败面
- `retrieval_fallback` 说明问题在召回层，典型是 metadata filter 太严，系统为了避免空结果而放宽了检索条件
- `model_fallback` 说明召回层已经有证据，但模型不可用，或者模型返回的答案在 citation 编号层面不可信
- 如果把两者混成一个字段，上游就分不清到底是“没召回准”还是“模型没生成稳”，后续调参、告警和用户提示都会失真
- 在真实工程里，这两类问题的优化方向也不同：
  - retrieval 问题要调 filter、top-k、fusion、索引
  - model 问题要调 provider、prompt、超时、校验和降级策略

面试作答压缩版：
- `retrieval_fallback` 和 `model_fallback` 对应两条不同失败链路：前者是召回条件过严，后者是生成层不可用或不可信。把它们拆开，才能让排障、监控和用户提示都保持真实。

用户回答提炼：
- 用户已经抓到核心主干：这是两种不同失败原因，必须拆开才能保证问题可诊断性。

用户回答修正版：
- 这两个 fallback 必须拆开，因为它们代表的是两条完全不同的失败链路。`retrieval_fallback` 说明问题发生在召回阶段，通常是 filter 太严或检索边界设置不合适；`model_fallback` 说明证据已经召回到了，但模型不可用，或者模型输出的答案在引用校验上不可信。如果把两者都压成一个“低置信回答”，上游就无法判断到底该调 retrieval 还是调 generation，监控、告警、用户提示和后续优化方向都会失真。在当前项目里，这个区分直接落在 `AskWorkflowResult` 的 `retrieval_fallback_used` 和 `model_fallback_used` 两组字段上，[backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L96) 到 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L125) 以及 [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py#L193) 都体现了这种拆分。

#### 问题 2：如果模型返回了一段“看起来像正确答案”的文本，但没有带引用，或者引用了超出候选范围的编号，为什么系统要直接降级成 `retrieval_only`，而不是原样返回并提示“低置信”？

参考回答：
- 因为当前项目把“答案必须可追溯到证据”当成 ask 链路的可信边界，而不是一个可选增强项
- 如果模型没带引用，或者引用编号已经越界，就说明这段答案和当前证据集合已经脱钩了
- 这时即使文本看起来通顺，也不能证明它真的是由当前候选支撑出来的，很可能已经发生了幻觉、偷换概念或证据漂移
- 在这种场景下，把答案原样返回再附一句“低置信”是不够的，因为用户通常会先看自然语言结论，而不是先审查系统提示
- 所以当前项目宁可保守，只返回 `retrieval_only` 的证据列表，也不把不可信的生成结论继续往下游传

用户回答提炼：
- 用户已经抓到主干：没有有效证据支撑时，模型可能产生幻觉，因此直接降级为 `retrieval_only` 更可靠

用户回答修正版：
- 这里直接降级成 `retrieval_only`，核心不是“模型回答得不够漂亮”，而是它已经越过了当前 ask 链路的可信边界。当前项目要求所有关键结论都必须能回指到当前候选证据；如果模型没有带引用，或者引用编号超出了候选范围，就说明答案和证据集合已经脱钩了。此时哪怕文本看起来像对的，也可能是幻觉、过度概括或编号漂移。如果仍把这段自然语言答案原样返回，再附一个“低置信”提示，用户通常还是会先相信结论本身，风险比直接返回证据更高。所以系统选择更保守的策略：一旦 citation 校验失败，就降级成 `retrieval_only`，只返回可核查的检索证据，不让不可信的生成结论进入最终响应。代码上这一点落在 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L77) 到 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L110) 和 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L169) 到 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L192)。

### 7. 模块 E 补充概念：`query`、`metadata filter`、`retrieval_only`、`no_hits`

问题：这几个基础概念最容易混在哪里？

思路：先把“搜什么”和“在哪搜”拆开，再把“有证据但不生成”和“根本没证据”拆开。

方案：
- `query` = 检索内容
  - 例子：`embedding`
- `metadata filter` = 检索边界
  - 例子：最近 7 天、只看 `daily_note`
- 当前项目里，`metadata filter` 不是从自然语言 query 自动解析出来的，而是请求里的独立结构化字段
- `retrieval_only` = 检索到了证据，但模型不可用或生成答案不可信，因此只返回证据和引用
- `no_hits` = 连可支撑回答的候选证据都没找到

项目代码落地：
- 协议事实：[backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py#L263) `WorkflowInvokeRequest` 里 `user_query` 和 `retrieval_filter` 是两个并列字段
- 协议事实：[plugin/src/contracts.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/contracts.ts#L199) 插件请求类型也保留了 `retrieval_filter`
- 代码事实：[backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L59) 没有 candidate 时返回 `no_hits`
- 代码事实：[backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L96) 与 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L112) 生成失败或 citation 校验失败时返回 `retrieval_only`

面试一句话：
- `query` 决定“搜什么”，`metadata filter` 决定“在哪搜”；`retrieval_only` 是“有证据但不信模型”，`no_hits` 是“连证据都没有”。

### 8. 模块 E 的真实工程瓶颈

问题：这条 ask 链路现在为什么“能演示”，但还不算真正的大规模稳定方案？

思路：分别看 fusion、vector 检索实现、groundedness 三层。

方案：
- 瓶颈 1：RRF 是稳妥基线，但不是最终最优融合
  - 当前先用 RRF，而不是线性加权或 rerank，本质是为了避开 BM25 和 cosine 分数量纲不一致的问题
  - 好处是简单、稳、可回归
  - 代价是：它只看排序，不看真实分值强弱；后续遇到复杂 query 时，精排能力有限
- 瓶颈 2：`sqlite_vector.py` 当前是 Python 侧全量扫描
  - 现在会把匹配 provider/model 的 embedding 从 SQLite 读出来，再在 Python 里逐条算 cosine
  - 小 vault 可以，大 vault 会先遇到延迟和内存压力
  - 所以后续如果 chunk 数上去，通常要换 ANN / 独立向量库 / 原生向量索引，而不是继续全扫 JSON
- 瓶颈 3：citation 编号校验不等于 groundedness
  - 当前只校验“有没有引用、编号有没有越界”
  - 这能拦住最明显的坏答案，但拦不住“编号合法、结论仍然过度概括”的情况
  - 所以后续还需要真正的语义级 groundedness gate

项目代码落地：
- 代码事实：[backend/app/retrieval/hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/hybrid.py#L186) 到 [backend/app/retrieval/hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/hybrid.py#L215) 当前只做 rank-based RRF
- 代码事实：[backend/app/retrieval/sqlite_vector.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_vector.py#L154) 到 [backend/app/retrieval/sqlite_vector.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_vector.py#L240) 当前是把 embedding 读出后在 Python 中逐条算相似度
- 代码事实：[backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L169) 到 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L192) 当前 citation 校验只覆盖编号层

面试一句话：
- 模块 E 当前已经把“可引用回答”做出来了，但 fusion 还偏保守、vector 检索还偏重、groundedness 还停留在编号校验，这三点都是大厂面试里会继续深挖的真实瓶颈。

#### 问题 3：如果 `sample_vault` 扩大 100 倍，chunk 从 1 千变成 10 万，模块 E 里最先炸的会是哪一层？

参考回答：
- 如果只看“最先出现硬性能瓶颈”的层，通常会先炸向量检索这层，也就是当前 `sqlite_vector.py` 的 Python 侧全量扫描
- 因为当前实现会把匹配 provider/model 的 embedding 从 SQLite 读出来，再逐条计算 cosine，相当于每次查询都在做近似全表扫描
- 当 chunk 数从 1 千涨到 10 万时，这一层会最先表现为延迟抬升、内存压力增大、并发吞吐下降
- 相比之下，RRF 和 groundedness 更像“质量债”：
  - RRF 先影响排序上限和复杂 query 的精排能力
  - groundedness 先影响答案可信度上限
- 但如果面试官强调的是“第一处会把系统拖慢甚至拖挂的地方”，答案通常应优先落在向量检索实现

用户回答提炼：
- 用户已经抓到主干：最先炸的是第 2 层，因为数据量飙升会先把计算压力和性能问题暴露出来，而第 1、3 层更偏质量上限问题

用户回答修正版：
- 如果规模直接放大 100 倍，我认为最先出硬瓶颈的是向量检索层，而不是 RRF 或 citation 校验。因为当前 `sqlite_vector.py` 的实现是把 SQLite 里的 embedding 读出来后在 Python 里逐条算 cosine，这种方式在 1 千级 chunk 还能接受，但到了 10 万级很容易先出现查询延迟升高、内存占用上升和并发吞吐下降。RRF 和 groundedness 当然也有问题，但它们更像质量上限和可信度上限，会先影响“答得好不好、稳不稳”，而向量全量扫描更容易先影响“系统还能不能扛住”。所以如果问‘最先炸哪层’，我会优先回答 vector retrieval implementation。代码可以落到 [backend/app/retrieval/sqlite_vector.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_vector.py#L154) 到 [backend/app/retrieval/sqlite_vector.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_vector.py#L240)。

#### 问题 4：如果一个答案带了合法的 `[1][2]` 引用编号，而且编号都没有越界，为什么你仍然不能说这个答案一定 grounded？

参考回答：
- 因为 citation 编号合法，只能说明“答案引用了当前候选集合里的某几条证据”，不能说明“答案里的每一句结论都被这些证据严格支持”
- 模型仍然可能出现几类语义级问题：
  - 过度概括：证据只支持局部结论，模型却说成普遍结论
  - 偷换因果：证据只是并列事实，模型却总结成因果关系
  - 补充新信息：模型带出了证据里没有明确写出的判断
  - 拼接漂移：分别引用了 `[1]` 和 `[2]`，但中间推出了证据并未明确支持的综合结论
- 所以“citation 合法”只说明编号层没坏，不等于 answer 真正 grounded
- 当前项目在 runtime 里只做了 citation 编号校验，还没有真正的语义级 groundedness gate

用户回答提炼：
- 用户已经抓到核心：当前没有验证“每一句话是否都有证据支撑”

用户回答修正版：
- 对，当前最大的问题是：citation 编号合法，只说明形式上引用没漂移，并不代表答案里的每一句话都真的被证据支持。模型可能引用了 `[1][2]`，但仍然会过度概括、补充证据里没有的新判断，或者把并列事实讲成因果关系。所以编号层校验只能解决“有没有引用、引用有没有越界”，不能证明答案已经 grounded。当前项目里 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L169) 到 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L192) 做的就是编号层校验，还没有上线语义级 groundedness gate。这也是为什么模块 E 里“citation alignment”已经完成，但 groundedness 仍然是后续工程缺口。

### 9. 模块 E 首轮收束

问题：模块 E 这一轮最应该带走的结论是什么？

思路：把“可引用回答”和“可信边界”一起讲透。

方案：
- ask 主链路不是“检索几段文本喂给模型”这么简单，而是：
  - 先做 hybrid retrieval
  - 再把 candidate 映射成 citation
  - 然后尝试 grounded answer
  - 最后用 citation alignment 守住最基本的可信边界
- 当前项目把 ask 结果显式分成：
  - `generated_answer`
  - `retrieval_only`
  - `no_hits`
- 同时把两类失败面拆开：
  - `retrieval_fallback` 代表召回条件过严
  - `model_fallback` 代表生成层不可用或不可信
- 当前实现的优势是边界清楚、可降级、可审计、可评估
- 当前实现的缺口是：
  - RRF 还是保守融合
  - `sqlite_vector` 还是 Python 侧全量扫描
  - citation 编号校验还不等于真正 grounded

面试一句话：
- 模块 E 的核心价值不是“把问题答出来”，而是把索引事实稳定转成“可引用、可降级、可诊断”的答案；当前已经守住了编号级可信边界，但语义级 groundedness 和大规模检索性能还没有完全收口。

项目代码落地：
- 代码事实：[backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L39) `run_minimal_ask()` 统一收口 ask 主流程
- 代码事实：[backend/app/retrieval/hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/hybrid.py#L30) 到 [backend/app/retrieval/hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/hybrid.py#L145) 负责 hybrid candidate 检索与 filter fallback
- 代码事实：[backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L169) 到 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py#L192) 当前只完成 citation 编号层校验
- 协议事实：[backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py#L181) 到 [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py#L204) 明确保留了 candidate、citation、fallback 和 provider/model 信息

## Step 3：模块 F：治理 proposal、审批恢复与写回安全

### 1. 模块 F 一句话定位

问题：这一层本质上在解决什么？

思路：不要讲成“生成一份建议”，而要讲成“把建议变成受控副作用”。

方案：
- 模块 F 解决的是：模型或规则已经给出了治理建议后，系统怎么把它安全地推进到真实笔记文件里，同时保证可审批、可恢复、可回滚、可审计。
- 它其实拆成三层：
  - `proposal` 事实层：生成什么 patch、风险多高、证据是什么
  - `resume / rollback` 控制面：用户批准或撤销后，后端如何记账和更新 workflow 状态
  - 插件本地副作用面：真正改 Vault 文件、校验 hash、保存本地 rollback 快照

项目代码落地：
- 代码事实：[backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py) 负责生成单 note scoped ingest proposal
- 代码事实：[backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py) 负责审批恢复、记 audit、推进 checkpoint
- 代码事实：[plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts) 负责插件本地真实写回与本地 rollback

### 2. 主调用链

问题：这一模块从 proposal 到写回，链路到底怎么走？

思路：按“生成建议 -> 等审批 -> 本地执行 -> 后端记账 -> 必要时回滚”来背。

方案：
1. `INGEST_STEWARD` 走 scoped ingest 且请求 `approval_mode=proposal` 时，`ingest_graph` 在完成索引后调用 proposal builder。
2. [backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py) 先解析目标 note，再做最小 related retrieve，收集 duplicate / orphan / missing_frontmatter 等 finding，最后产出 `Proposal + analysis_result`。
3. [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py) 把 `proposal` 和 `waiting_for_approval checkpoint` 放在同一个 SQLite 事务里原子落盘。
4. 插件审批面板拿到 proposal 后，先在本地执行受限 patch；只有本地写回真的成功了，才把 `writeback_result` 连同 `thread_id / proposal_id / approval_decision` 回传到 `/workflows/resume`。
5. [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py) 校验 proposal、checkpoint、decision 和 writeback 结果是否一致，然后把 append-only `audit_log` 和 completed checkpoint 同事务写入。
6. 如果本地已经写回成功，后端再 best-effort 做一次 scoped ingest 刷新；如果需要撤销，则插件先基于本地快照 rollback，再调 `/workflows/rollback` 记 rollback 审计。

项目代码落地：
- 代码事实：[backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py#L354) 到 [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py#L375) 显式保证 proposal 和 waiting checkpoint 原子落盘
- 代码事实：[plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts#L804) 到 [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts#L832) 先执行本地写回，再调用 `/workflows/resume`
- 代码事实：[backend/app/services/rollback_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/rollback_workflow.py) 负责 rollback 记账与 checkpoint 更新

### 3. 为什么 proposal builder 先保守，再谈智能

问题：为什么这里没有直接上“大而全的 LLM patch planner”？

思路：先看边界，再看能力。

方案：
- 当前 `build_scoped_ingest_approval_proposal()` 明确只支持“单 note scoped ingest”，因为一旦变成多 note proposal，就会立刻扩成跨 note 冲突裁决和多文件事务问题。
- 它先抓几类高价值治理信号：
  - 当前 note 自身的结构问题，比如缺 frontmatter、没 wikilink、task 太多、note_type 不稳定
  - related retrieve 命中的外部证据，比如 duplicate hint、orphan hint
- 最终 patch 也故意限制成两类：
  - `merge_frontmatter`
  - `insert_under_heading`
- 这不是能力不够，而是首版先把“安全可执行 patch contract”收口，再谈更自由的 diff。

项目代码落地：
- 代码事实：[backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py#L72) 到 [backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py#L84) 明确拒绝多 note proposal
- 代码事实：[backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py#L214) 到 [backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py#L244) 当前只生成两种受限 patch op

### 4. 为什么写回必须由插件执行，而不是后端直接改 Vault

问题：这是模块 F 最核心的架构 trade-off，面试里很容易被追问。

思路：把“控制面”和“副作用面”分开。

方案：
- 后端负责：
  - proposal / audit / checkpoint 这些业务事实
  - 审批恢复协议和一致性校验
- 插件负责：
  - 当前 Vault 内文件定位
  - 路径必须在 Vault 根内
  - 真实文件 hash 校验
  - 本地写回前快照与 rollback
- 这么拆的核心原因是：后端不应该越权直接修改用户本地知识库。插件才拥有“当前 Obsidian Vault 上下文 + 当前文件真实状态 + 本地快照回滚能力”。

项目代码落地：
- 代码事实：[plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts#L239) 与 [plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts#L272) 这段解析绝对路径并拒绝 Vault 外目标
- 代码事实：[plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts#L58) 与 [plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts#L82) 这段会校验 `before_hash`
- 代码事实：[backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py#L166) 到 [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py#L178) 只在后端记录审计和状态，不直接写文件

面试一句话：
- 后端是 workflow 控制面和业务事实源，插件是本地副作用执行器；这能把“能不能改”与“怎么记账”分开，避免后端越权直改用户 Vault。

### 5. `before_hash` 和 rollback 在守什么边界

问题：这两个机制看上去只是 hash 字段，真正价值是什么？

思路：把它理解成“乐观并发锁 + 保守撤销门槛”。

方案：
- `before_hash` 的作用：
  - 防止用户加载了旧 proposal 后，文件已经变了还继续套 patch
  - 如果 hash 不一致，但 patch 实际已经应用过，插件会走“already applied”判断，避免重复写
- rollback 的作用：
  - 只允许撤销“当前插件会话亲手执行的那次写回”
  - 只有当当前文件还精确等于 `after_hash` 时才允许整文恢复
  - 一旦用户后面又手改过文件，宁可拒绝 rollback，也不覆盖用户新修改
- 这就是典型的“宁可保守失败，也不做危险自动修复”。

项目代码落地：
- 代码事实：[plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts#L112) 与 [plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts#L159) 这段要求 rollback 必须命中精确 `after_hash`
- 代码事实：[backend/app/services/rollback_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/rollback_workflow.py#L121) 到 [backend/app/services/rollback_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/rollback_workflow.py#L139) rollback 失败也写 audit，但只有成功 rollback 才回写 checkpoint

### 5.1 模块 F 补充概念：`before_hash` 到底是什么

问题：`before_hash` 为什么老被强调，它本质上在干什么？

思路：把它理解成“proposal 生成那一刻，这篇 note 的文件指纹”。

方案：
- 在 proposal 生成时，后端会对目标 note 的当前文件内容做一次 SHA-256，生成 `proposal.safety_checks.before_hash`
- 这个 hash 不是为了检索，也不是为了审计展示，而是为了后续写回时判断：
  - “你现在准备改的，还是不是当初生成 proposal 时看到的那份文件？”
- 插件真正写回前会重新计算当前文件 hash：
  - 如果和 `before_hash` 一样，说明文件没漂，可以按 proposal 执行 patch
  - 如果不一样，不代表一定失败，还要再判断一次 proposal patch 是否其实已经落地过
    - 如果已经落地过，就按“already applied”处理，避免重复写
    - 如果没有落地过，就拒绝写回，避免旧 proposal 覆盖用户后来修改的新内容
- 写回成功后，插件还会把 `before_hash / after_hash` 一起回传给后端，后端在 `/workflows/resume` 中再校验 `writeback_result.before_hash` 是否仍然和 proposal 里的 `before_hash` 一致

面试一句话：
- `before_hash` 是 proposal 生成时那份目标文件的指纹，用来防止 stale proposal 覆盖新内容；它本质上是最小乐观并发锁，不是完整事务系统。

用户最容易混淆的点：
- 不要把 `before_hash` 理解成“只要 mismatch 就一定失败”
- 更准确地说：
  - mismatch 先说明“文件状态变了”
  - 但还要进一步区分：是“别人后来改了文件”，还是“这份 proposal 其实已经应用过了”

问题：那系统怎么判断“proposal 其实已经应用过了”？

方案：
- 插件不会靠“猜”来判断，而是逐条检查当前文件里是否已经包含 proposal 对应的 patch 效果：
  - 对 `merge_frontmatter`
    - 检查当前 frontmatter 是否已经包含 proposal 想写入的字段和值
  - 对 `insert_under_heading`
    - 检查目标 heading 下是否已经包含 proposal 想插入的那段内容
- 只有当所有 patch op 都命中时，才把这份 proposal 视为“already applied”
- 这意味着当前实现判断的是“补丁效果是否已存在”，而不是“这次写回是不是由本次请求亲手执行”

面试一句话：
- 当前项目判断 `already applied`，本质上是做 patch effect detection：检查目标 frontmatter 和目标 section 里是否已经包含 proposal 要施加的结果，而不是只看一个 hash 或时间戳。

用户回答提炼：
- 当前项目的写动作是受限且结构化的，所以 patch 效果可检查；如果将来变成任意自由 diff，落地结果不再稳定可判，`already applied` 核查会难很多。

用户回答修正版：
- 当前项目之所以能做 `already applied` 检查，本质上是因为写动作被限制成少数几种结构化 patch op，比如 frontmatter merge 和 heading 下插入内容，这些效果都能被插件确定性检查。如果未来支持任意自由 diff，模型生成的改动会更开放，等价表达和局部重排也会变多，系统就很难再用简单规则判断“这份 proposal 是否已经落地”，核查成本和误判风险都会明显上升。

### 5.2 模块 F 补充概念：`after_hash` 和 rollback 是什么关系

问题：`before_hash` 已经能防 stale proposal 了，那 `after_hash` 和 rollback 又各自负责什么？

思路：把三者放到一条时间线上记。

方案：
- `before_hash`
  - 含义：proposal 生成时，原始文件的指纹
  - 作用：写回前确认“现在准备改的文件，还是不是当初看到的那份”
- `after_hash`
  - 含义：proposal 写回成功后，修改后文件的指纹
  - 作用：给 rollback 提供“写回后的精确落点”
- rollback
  - 含义：如果要撤销刚才那次本地写回，插件必须先确认当前文件还停留在那次写回后的精确状态
  - 只有当前文件 hash 仍然等于 `after_hash`，才允许把文件恢复回 `before_markdown`

大白话时间线：
1. 生成 proposal 时记录 `before_hash`
2. 本地写回成功后记录 `after_hash`
3. 之后如果要 rollback：
   - 先看当前文件 hash 是否还是 `after_hash`
   - 如果是，说明用户没再改过，可以安全恢复
   - 如果不是，说明文件在写回后又被改过，rollback 必须拒绝，避免把用户后来手改的内容覆盖掉

面试一句话：
- `before_hash` 负责“写之前别覆盖新内容”，`after_hash` 负责“撤销时别误删后续修改”；两者一前一后，共同把写回和回滚的安全边界钉住。

用户回答提炼：
- `before_hash` 确保 proposal 批准后写回的目标仍是当初那份文件；`after_hash` 确保 rollback 要恢复的，仍是 proposal 写回后的那份文件，没有再被后续修改。

用户回答修正版：
- `before_hash` 用来保证 proposal 审核通过后，真正要写回的仍然是 proposal 生成时看到的那份文件，避免旧 proposal 覆盖新内容；`after_hash` 用来保证 rollback 作用的仍然是那次 proposal 写回后的精确文件状态，如果写回后用户又改过内容，rollback 就必须拒绝，避免把后续修改覆盖掉。

### 10. 模块 F 最终收束

问题：模块 F 这一轮最应该带走的结论是什么？

思路：把 proposal、写回、恢复、回滚四件事收成一个闭环。

方案：
- 模块 F 的核心价值，不是“让模型自动改笔记”，而是把高风险写操作变成一个可控闭环：
  - proposal 先把“建议改什么”结构化
  - resume 再把“审批后如何继续流程”控制住
  - 插件本地执行受限 patch，守住本地副作用边界
  - rollback 在必要时只做保守撤销，不覆盖用户后续修改
- 这一模块最重要的工程设计有 4 个：
  - proposal 与 waiting checkpoint 原子落盘，避免业务事实和流程事实分叉
  - 写回必须由插件执行，而不是后端越权直改 Vault
  - `before_hash` 防 stale proposal 覆盖新内容
  - `after_hash` + rollback 防撤销时误删写回后的后续修改
- 当前方案的强项是：边界清楚、风险可控、可审计、可恢复
- 当前方案的限制是：仍然是受限 patch、单 note、最小补偿，不是完整生产级写回平台

面试一句话：
- 模块 F 本质上是在做“高风险副作用治理”：不是追求模型能改得多自由，而是优先保证 proposal、审批、写回、回滚这条链路可控、可恢复、可审计。

30 秒背诵版：
- 在这个项目里，模型不会直接改用户笔记。后端先生成带 evidence、patch_ops 和 safety_checks 的 proposal，并把 proposal 和 waiting checkpoint 原子落盘；用户审批后，由插件在本地执行受限写回，利用 `before_hash` 防止旧 proposal 覆盖新内容，再把真实 `writeback_result` 回传后端记 audit 和 checkpoint。如果需要撤销，再利用 `after_hash` 确认文件还停留在那次写回后的精确状态，只有满足条件才允许 rollback。所以这一层的重点不是“让 Agent 更自由”，而是把高风险副作用做成可控闭环。

### 11. 模块 F 补充概念：`audit` 到底是什么，和 `checkpoint` 有什么区别

问题：回传后端“记 audit”到底在记什么？它和 checkpoint 不是一回事吗？

方案：
- `checkpoint`
  - 本质：当前 workflow 运行到哪里的状态快照
  - 作用：为了恢复和续跑
  - 更像“现在系统停在哪一格”
- `audit`
  - 本质：已经发生过什么事实的 append-only 记录
  - 作用：为了审计、追责、排障、补偿和回放
  - 更像“这一路上到底发生过哪些关键事件”
- 在模块 F 里，audit 主要会记：
  - 哪个 `thread_id / proposal_id / run_id`
  - 审批结果是什么
  - 写回是否成功，`before_hash / after_hash` 是什么
  - rollback 是否尝试过、是否成功
  - 目标 note 是哪篇
- 为什么需要它：
  - checkpoint 只告诉你“现在状态”
  - audit 才告诉你“过程里发生过什么”
  - 比如 rollback 失败时，checkpoint 可能不更新，但 audit 仍然要留痕，因为“失败尝试过一次”本身就是重要事实

面试一句话：
- checkpoint 是恢复快照，audit 是事实日志；一个回答“现在停在哪”，一个回答“之前发生过什么”。

用户回答提炼：
- rollback 失败属于已经发生过的动作事实，所以要写 audit；但失败不代表当前流程状态必须变化，因此不一定要更新 checkpoint。

用户回答修正版：
- rollback 失败本身就是一条已经发生过的关键动作事实，所以必须写进 audit，方便后续排障、审计和补偿；但它不一定改变当前 workflow 的恢复状态，因此不一定要更新 checkpoint。换句话说，audit 记录的是历史事实，checkpoint 记录的是当前状态快照。

项目代码落地：
- 代码事实：[backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py#L76) 到 [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py#L87) 定义了 `AuditEvent`
- 代码事实：[backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py#L166) 到 [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py#L178) 在同一事务里同时写 audit 和 completed checkpoint
- 代码事实：[backend/app/services/rollback_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/rollback_workflow.py#L133) 到 [backend/app/services/rollback_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/rollback_workflow.py#L155) rollback 失败也写 audit，但只有成功 rollback 才更新 checkpoint

项目代码落地：
- 代码事实：[plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts#L96) 到 [plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts#L113) 写回成功后会把 `after_hash` 写进 `writeback_result`
- 代码事实：[plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts#L131) 到 [plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts#L139) rollback 前先校验当前 hash 是否仍等于 `expectedAfterHash`
- 代码事实：[backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py#L301) 到 [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py#L305) 后端要求成功写回的 `writeback_result` 必须带 `after_hash`
- 代码事实：[backend/app/services/rollback_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/rollback_workflow.py#L88) 到 [backend/app/services/rollback_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/rollback_workflow.py#L92) 后端 rollback 会拿正向写回结果和这次 rollback 结果做一致性校验

项目代码落地：
- 代码事实：[backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py#L671) 在 proposal 生成时计算 `before_hash`
- 代码事实：[plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts#L68) 到 [plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts#L90) 写回前比较当前 hash 和 `expectedBeforeHash`
- 代码事实：[plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts#L70) 到 [plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts#L81) mismatch 后还会检查 proposal 是否已实际应用
- 代码事实：[plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts#L219) 到 [plugin/src/writeback/applyProposalWriteback.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/applyProposalWriteback.ts#L244) `isProposalAlreadyApplied()` 会逐条检查 patch 效果
- 代码事实：[plugin/src/writeback/helpers.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/helpers.ts#L148) 到 [plugin/src/writeback/helpers.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/helpers.ts#L157) `frontmatterContainsPatch()` 用来检查 frontmatter 效果
- 代码事实：[plugin/src/writeback/helpers.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/helpers.ts#L99) 到 [plugin/src/writeback/helpers.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/writeback/helpers.ts#L115) `sectionContainsInsertedContent()` 用来检查插入内容是否已存在
- 代码事实：[backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py#L317) 到 [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py#L324) 后端会再次校验回传的 `before_hash`

### 6. 当前模块 F 的 trade-off

问题：这一版为什么说“安全边界清楚”，但还不算完整生产级方案？

思路：同时讲优点和欠账。

方案：
- 当前优点：
  - proposal / checkpoint / audit 分层清楚
  - proposal 与 waiting checkpoint 原子落盘
  - 本地写回先执行，再回传真实结果
  - rollback 保守，不会覆盖用户后续修改
- 当前欠账：
  - 只支持单 note proposal
  - 只支持两类受限 patch op
  - 不支持 partial apply
  - rollback 只覆盖当前插件会话内的本地快照，不能跨会话恢复
  - 后端和插件之间仍然存在“本地副作用已成功、后端同步失败”的双面一致性补偿问题，只是先做了最小重试保护

面试一句话：
- 模块 F 当前不是“万能写回引擎”，而是一个受限但边界清楚的 HITL 写回闭环：先保证安全和可审计，再逐步扩表达能力。

### 7. 模块 F 面试题 1：为什么 proposal 与 waiting checkpoint 必须原子落盘？

问题：为什么不能先把 proposal 返回给前端，再异步补 waiting checkpoint？

思路：把 `proposal` 和 `checkpoint` 分别看成“业务事实”和“流程事实”。

方案：
- `proposal` 是业务事实：
  - 记录“建议改什么、证据是什么、风险多高、允许执行哪些 patch”
- `waiting checkpoint` 是流程事实：
  - 记录“这条 workflow thread 现在已经停在审批节点，只能走 `/workflows/resume` 继续”
- 如果两者不原子落盘，就会出现分叉状态：
  - 前端已经拿到了 proposal
  - 但后端线程其实还没进入 `waiting_for_approval`
  - 这会直接影响三个控制点：
    - `resume`：找不到这条 thread 正在等待审批的状态
    - `pending inbox`：待审批收件箱里可能看不到这条 proposal
    - 重复审批控制：系统无法基于完整 waiting 状态判断这是不是同一份已处理或待处理 proposal
- 所以这里必须把“proposal 持久化”和“checkpoint 切到 waiting”放进同一个事务，避免前端和后端看到两套不同世界。

面试一句话：
- `proposal` 是业务事实，`waiting checkpoint` 是流程事实；两者必须同事务提交，否则 `resume`、pending inbox 和重复审批控制都会失配。

用户修正版：
- `proposal` 是业务事实，而 `waiting checkpoint` 是流程事实，两者必须保持一致，并在一个原子事务里提交；否则就会出现前端已经看到 proposal，但后端并不承认这条 workflow 正在 waiting 的分叉状态，后续 `resume`、pending inbox 和重复审批控制都会错乱。

项目代码落地：
- 代码事实：[backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py#L354) 到 [backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py#L375) 用一个 SQLite 事务同时保存 proposal record 和 waiting checkpoint

### 8. 模块 F 补充基础概念：`resume`、`pending inbox`、重复审批控制、`patch_ops`

问题：这几个词在这一模块里分别指什么？

方案：
- `resume`
  - 不是重新生成 proposal，而是让已经停在审批节点的 workflow 继续往下走
  - 当前项目里对应 `POST /workflows/resume`
- `pending inbox`
  - 就是“待审批收件箱”
  - 当前项目里对应 `GET /workflows/pending-approvals`
- 重复审批控制
  - 防止同一份 proposal 被重复 approve，或者 approve 后又被旧面板二次改判
  - 后端通过 completed checkpoint + decision 一致性校验做幂等/冲突控制
  - 前端通过冻结已提交 proposal 上下文，避免陈旧面板重复提交
- `patch_ops`
  - 不是整篇重写 Markdown，而是受限、结构化的白名单写操作清单
  - 当前主要是 `merge_frontmatter` 与 `insert_under_heading`

面试一句话：
- `proposal` 说的是“建议改什么”，`patch_ops` 说的是“允许怎么改”；`resume` 负责继续流程，`pending inbox` 负责找回待审批项，重复审批控制负责守住幂等和状态边界。

### 9. 模块 F 面试题 2：如果插件本地写回已经成功，但 `/workflows/resume` 因网络失败没记账，当前怎么兜底？生产上还要补什么？

问题：这是典型的“副作用面已经成功，控制面还没记账”的双面一致性问题，怎么回答才像做过系统的人？

思路：先分清“当前最小保护”与“长期生产补偿”。

方案：
- 当前代码的最小兜底：
  - 插件本地写回先执行
  - 如果写回已经成功，但 `/workflows/resume` 调用失败，插件不会再次执行同一批 patch
  - 它会把这次已经成功的本地写回结果暂存在面板内存里，提示用户“Retry Approve to sync audit state”
  - 用户再次点 Approve 时，插件直接复用上次的 `writeback_result` 回传后端，只重试“同步审计和 checkpoint”这一步，不重复改文件
- 这为什么还不够：
  - 当前保护只在“同一个插件会话 / 同一个面板上下文”内成立
  - 如果 Obsidian 重启、面板关闭、前端状态丢失，这个“本地已经写回但后端没记账”的事实就不再有稳定的持久化补偿入口
  - 所以它只是最小防重试，不是完整的跨会话恢复系统
- 生产上应该再补的机制：
  - 本地持久化 outbox / 待同步队列：把 `thread_id / proposal_id / before_hash / after_hash / applied_patch_ops` 落本地磁盘，而不是只放面板内存
  - 后端幂等记账：`/workflows/resume` 接受稳定 idempotency key，重复上报同一写回事实时只做幂等确认，不重复推进状态
  - 启动后 reconciliation：插件或后端能扫描“本地已写回、后端未记账”的待同步项并自动补记
  - 明确的 pending sync inbox：把“文件事实已变、审计事实未补齐”的异常态显式暴露给用户，而不是藏在临时错误提示里

面试一句话：
- 当前方案只解决“不要重复写文件”，还没有彻底解决“跨会话怎么补记审计”；生产上要靠本地 outbox、后端幂等记账和 reconciliation 把副作用面与控制面重新对齐。

用户当前应掌握的高分回答模板：
- 场景：插件先在本地把 proposal 写进了 Vault，但随后 `/workflows/resume` 因网络失败，没有把 audit 和 completed checkpoint 记到后端。
- 风险：如果这时简单重试整个流程，就可能把同一批 patch 再执行一次，造成重复写入；如果什么都不做，又会出现“文件事实已经变化，但后端状态还停在 waiting”的分叉。
- 设计：当前项目的最小保护是在插件侧保留已经成功的 `writeback_result`，允许用户重试 Approve 时只同步后端审计，不重复执行本地 patch。
- trade-off：这个设计能先守住“不重复写文件”，但状态只保存在当前面板内存里，跨会话补偿还不完整。
- 在本项目中的落地：`KnowledgeStewardView.submitDecision()` 在本地写回成功但 resume 失败时，会保留 `pendingWritebackExecution` 并提示 `Retry Approve to sync audit state`；下一次提交时直接复用这次 `writeback_result`，不再重新落盘。真正要做成生产级，还要再加本地 outbox、后端幂等 key 和启动后 reconciliation。

用户回答提炼：
- 当前方案解决了“单会话内重试只同步状态、不重复写文件”，但还没有解决跨会话场景下的补偿。

用户回答修正版：
- 当前方案本质上只解决了同一插件会话内的最小补偿问题：如果本地写回已经成功，重试时只同步后端状态，不会重复写文件。但它没有解决跨会话恢复，因为这些待同步事实还只保存在面板内存里。一旦插件重启或上下文丢失，就还需要更完整的 outbox、幂等记账和 reconciliation 机制来补偿。

项目代码落地：
- 代码事实：[plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts#L839) 到 [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts#L848) 本地写回成功但 resume 失败时会保留 `pendingWritebackExecution`
- 代码事实：[plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts#L820) 到 [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts#L823) 重试 approve 时优先复用 `pendingWritebackExecution`

## Step 3：模块 G：插件 UI 与后端运行时控制（第一轮）

> 当前状态：本节只沉淀已经讲过的第一轮基础结论，后续继续精读 `startBackend()`、`KnowledgeStewardView` 和设置页后再增量补充。

### 1. 模块 G 的一句话定位

问题：模块 G 本质上在解决什么？

思路：不要把它讲成“插件多了个面板和按钮”，要讲成“插件侧可用性控制面”。

方案：
- 模块 G 的核心不是业务问答，也不是写回逻辑，而是插件如何确认“本地后端现在能不能用、为什么不能用、下一步该让用户做什么”。
- 它本质上在做三件事：
  - 后端状态探测
  - 后端启动控制
  - 状态同步到 UI

面试一句话：
- 这一层是插件侧的 backend control plane，目的是把“后端是否可用”从临时感觉变成可展示、可排障、可驱动用户动作的显式状态。

项目代码落地：
- 代码事实：[plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts) 负责插件入口装配
- 代码事实：[plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts) 负责维护后端状态与启动逻辑
- 代码事实：[plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts) 负责消费状态并展示到面板
- 代码事实：[plugin/src/settings.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/settings.ts) 负责配置 backend URL、启动命令、超时和 auto-start

### 2. 模块 G 的四个角色

问题：这几个文件分别在干什么？

思路：先用白话建立角色分工，不要一上来陷进函数细节。

方案：
- `main.ts`
  - 插件总调度台
  - 负责把面板、命令、设置页和后端状态管理接起来
- `runtime.ts`
  - 后端管家
  - 负责记录“后端当前状态”、执行探活、尝试启动、记录最近错误和输出
- `KnowledgeStewardView.ts`
  - 右侧面板
  - 负责把后端状态、待审批项和审批交互展示给用户
- `settings.ts`
  - 设置页
  - 负责让用户配置后端地址、启动命令、工作目录和超时策略

项目代码落地：
- 代码事实：[plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts#L21) 定义插件主类 `KnowledgeStewardPlugin`
- 代码事实：[plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L41) 定义 `KnowledgeStewardBackendRuntime`
- 代码事实：[plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts#L31) 定义面板 `KnowledgeStewardView`
- 代码事实：[plugin/src/settings.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/settings.ts#L5) 定义 `KnowledgeStewardSettings`

### 3. 当前已讲清的入口函数：`onload()`

问题：`main.ts` 里的 `onload()` 在做什么？

思路：把它讲成“插件启动时的开机装配流程”，而不是业务主逻辑。

方案：
- `onload()` 当前做 5 件事：
  - 读取设置
  - 注册右侧面板
  - 注册命令
  - 注册设置页
  - 按配置决定是否尝试处理后端
- 它的核心职责不是处理业务，而是把后续要用到的能力装配好。

面试一句话：
- 插件入口层负责初始化和接线，不直接承载复杂业务，这样入口不会演变成又管 UI、又管状态、又管副作用的大文件。

项目代码落地：
- 代码事实：[plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts#L28) `onload()` 先调用 `loadSettings()`
- 代码事实：[plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts#L31) 到 [plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts#L38) 注册 `KnowledgeStewardView`
- 代码事实：[plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts#L40) 到 [plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts#L86) 注册打开面板、检查后端、启动后端等命令
- 代码事实：[plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts#L88) 注册设置页
- 代码事实：[plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts#L89) 调用 `backendRuntime.maybeAutoStartBackend()`

### 4. 当前已讲清的一条最短链路：`pingBackend()`

问题：从用户点击“检查后端”到界面拿到结果，中间发生了什么？

思路：用最短链路建立“命令 -> 状态 -> UI”的基本感觉。

方案：
- `pingBackend()` 的主链路是：
  - 打开/激活面板
  - 询问后端当前状态
  - 把状态同步给面板
  - 再用 Notice 告诉用户结果
- 所以它不是只弹一个提示，而是让“后端状态”同时进入 UI 的持续状态和用户的即时反馈。

面试一句话：
- 后端状态不是一次性提示，而是插件界面也要持续消费的共享状态；Notice 只是通知，面板状态才是系统当前事实。

项目代码落地：
- 代码事实：[plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts#L140) 到 [plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts#L153) `pingBackend()` 先 `activateView()`，再 `refreshStatus()`，随后 `setBackendStatus(snapshot)` 并弹出 Notice

### 5. 为什么这里要维护 `snapshot`

问题：为什么不每次临时检查一下后端状态就行了？

思路：把“后端可用性”讲成一个过程，而不是一个瞬时布尔值。

方案：
- 当前项目里，`snapshot` 更像“后端状态卡片”，不是一次性消息。
- 因为后端启动是过程型状态：
  - 可能先 `checking`
  - 再 `starting`
  - 最后 `ready`
  - 也可能走到 `failed`
- 如果没有统一 `snapshot`：
  - Notice 和面板可能各看到一套结果
  - 启动中的状态没地方保存
  - 最近错误、PID、最近输出会丢失
  - 每个按钮都可能各自查一遍，控制面会变乱

面试一句话：
- backend availability 是过程型状态，不是一拍脑袋的布尔值，所以这里用统一 `snapshot` 保存状态、错误、时间戳和最近输出，再让 UI 订阅它。

项目代码落地：
- 代码事实：[plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L19) 定义 `BackendRuntimeSnapshot`
- 代码事实：[plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L44) 运行时类内部持有 `snapshot`
- 代码事实：[plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L73) `getSnapshot()` 对外提供当前状态

### 6. 当前已讲清的模式：轻量观察者模式

问题：这里是不是观察者模式？

方案：
- 可以这么理解，但更准确地说是“共享状态记录 + 轻量观察者模式”。
- `runtime.ts` 维护 `snapshot`
- `KnowledgeStewardView` 订阅 `snapshot`
- `snapshot` 一更新，就把新状态通知给所有 listener

面试一句话：
- 这里没有上很重的状态框架，而是手写了最小订阅-通知机制，让 UI 跟着统一状态源变化。

项目代码落地：
- 代码事实：[plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L65) `subscribe()` 会把当前状态和后续更新发给 listener
- 代码事实：[plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L404) `updateSnapshot()` 会更新状态并通知 listeners
- 代码事实：[plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts#L68) 面板打开时订阅 backend runtime

### 7. 当前已讲清的状态机骨架

问题：为什么不能只做 `available / unavailable` 二态？

思路：后端控制面关心的不是“亮不亮灯”，而是“现在处在哪个阶段、下一步允许什么动作”。

方案：
- 当前 runtime 把状态拆成：
  - `checking`
  - `starting`
  - `ready`
  - `unavailable`
  - `failed`
- 这样拆的价值是：
  - UI 可以做不同展示和按钮禁用逻辑
  - 错误语义更清楚：没开、未配置、启动炸了，不是一回事
  - 用户动作更明确：什么时候该点 Start，什么时候只能等，什么时候该去排查启动命令

面试一句话：
- 我没有把 backend 状态压成二态，因为可用性是过程型控制问题；不同阶段对应不同的错误解释、UI 展示和用户动作。

项目代码落地：
- 代码事实：[plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L12) 定义 `BackendRuntimeStatus`

### 8. 当前模块 G 的第一轮收束

问题：到目前为止，模块 G 最值得记住的结论是什么？

方案：
- 模块 G 不是“插件 UI 杂项”
- 它是在插件侧做一个最小 backend control plane
- `main.ts` 负责装配和调度
- `runtime.ts` 负责维护共享状态与启动/探活状态机
- `view.ts` 负责订阅并展示这份状态
- 这一层的重点是可用性、排障和用户动作引导，不是大模型能力本身

面试一句话：
- 这一层看起来不像 Agent 核心，但它决定了系统是不是一个“能稳定跑的产品”，而不只是“后端能单独跑通的 demo”。

### 9. 当前已讲清的启动控制函数：`startBackend()`

问题：点击“Start backend”后，这个函数到底在控制什么？

思路：它不是“立刻起进程”的薄封装，而是一个带保护条件的启动总控。

方案：
- `startBackend()` 当前做了 4 层保护：
  - 如果已经有一次启动在进行，直接复用同一份 `startPromise`，避免重复启动
  - 先做一次 `refreshStatus()`，如果后端已经 `ready`，就直接返回，不再多拉一个进程
  - 如果用户根本没配置启动命令，就直接给出 `unavailable` 和明确提示，不盲目 `spawn`
  - 真正进入启动时，也不是“进程拉起来就算成功”，而是继续等待 `/health`，只有 health 命中才算 `ready`
- 这说明这里控制的不是“有没有调用 start 命令”，而是“怎样安全地尝试启动，并把状态机推进到正确阶段”。

面试一句话：
- `startBackend()` 的重点不是启动动作本身，而是防重复、先探活、配置兜底和 readiness 校验；它要避免把一次启动按钮变成重复拉进程或伪成功的来源。

项目代码落地：
- 代码事实：[plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L107) 到 [plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L110) 用 `startPromise` 复用同一次启动
- 代码事实：[plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L112) 到 [plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L115) 启动前先探活，已 `ready` 就直接返回
- 代码事实：[plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L117) 到 [plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L130) 未配置启动命令时显式返回 `unavailable`
- 代码事实：[plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L132) 到 [plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L136) 真正启动逻辑委托给 `launchAndWaitUntilHealthy()`

### 10. 补充概念：为什么“进程启动了”不等于“后端 ready”

问题：为什么这里不把 `spawn` 成功直接当成启动成功？

方案：
- 因为 `spawn` 成功只能说明“进程被拉起来了”
- 但后端可能还没监听端口、还没完成初始化，甚至可能刚启动就退出
- 所以代码会继续轮询 `/health`
  - 命中 `/health` 才推进到 `ready`
  - 启动中命不中 `/health` 就保持 `starting`
  - 超时或进程提前退出就转成 `failed`

面试一句话：
- readiness 的定义应该建立在“服务真的能接请求”上，而不是“进程看起来被拉起来了”。

项目代码落地：
- 代码事实：[plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L233) 到 [plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L271) 拉起进程后进入 `waitUntilHealthy()`
- 代码事实：[plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L343) 到 [plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L355) 只有命中 `/health` 才设置为 `ready`
- 代码事实：[plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L374) 到 [plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L384) 启动超时会显式标记为 `failed`
- 代码事实：[plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L305) 到 [plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L315) 如果进程在 ready 前退出，会显式标记为 `failed`

### 11. 当前已讲清的启动内层时序：`launchAndWaitUntilHealthy()`

问题：真正开始启动后，内部时序是怎么跑的？

思路：把它讲成“启动尝试 + 监听进程 + 等待健康检查”的三段式，而不是一坨进程代码。

方案：
- 如果已经有一个被插件跟踪的子进程还活着，就不再重复拉起，只把状态标成 `starting`，然后继续等 `/health`
- 如果还没有活着的子进程，就先把状态切到 `starting`
- 然后执行 `spawnCommand(...)` 真正拉起后端进程
- 拉起后马上记录 `pid`，并监听 `stdout/stderr/error/exit`
- 之后进入 `waitUntilHealthy()` 循环：
  - 命中 `/health` 就转 `ready`
  - 命不中就继续保持 `starting`
  - 超时则转 `failed`
  - 如果进程在 ready 前就退出，也直接转 `failed`

面试一句话：
- 这一层把“发起启动”“跟踪进程”“确认 ready”拆开了，避免把 `spawn` 成功误当成服务可用。

项目代码落地：
- 代码事实：[plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L219) 到 [plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L230) 如果已有活着的 tracked child，就不重复拉起
- 代码事实：[plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L233) 到 [plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L251) 真正执行启动命令
- 代码事实：[plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L264) 到 [plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L271) 保存 `activeChild` 并进入 `waitUntilHealthy()`
- 代码事实：[plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L274) 到 [plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L331) 监听子进程输出、错误和退出事件
- 代码事实：[plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L334) 到 [plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L385) 循环等待 `/health` 变成 ready

### 12. 当前已讲清的 UI 消费层：`KnowledgeStewardView` 如何展示 backend runtime

问题：runtime 状态机到了 UI 层，用户到底能看到什么？

思路：强调 view 是状态消费者，不是状态生产者。

方案：
- `onOpen()` 打开面板时会做两件事：
  - 订阅 backend runtime 的 `snapshot`
  - 触发一次初始 `refreshStatus()`
- `renderBackendRuntimeSection()` 负责展示控制面：
  - `Check backend` 在 `checking` 时禁用
  - `Start backend` 在 `starting`、`ready` 或未配置启动命令时禁用
  - 面板会显示当前状态、状态说明、是否配置启动命令、是否开启 auto-start、PID、最近检查时间、最近启动时间、最近 ready 时间、最近错误和最近输出
- `renderHealthSection()` 只在 `health` 真存在时展示版本、模型策略和 sample vault 指标；否则明确提示用户去检查或启动后端
- `handleStartBackend()` 不自己管理状态机，只负责调用 runtime 并把结果翻译成 Notice

面试一句话：
- `KnowledgeStewardView` 是 backend control plane 的可视化层：消费统一状态源，并把不同 runtime 状态翻译成按钮可用性、状态卡片和排障信息。

项目代码落地：
- 代码事实：[plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts#L75) 到 [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts#L85) `onOpen()` 订阅 runtime 并触发 `refreshStatus()`
- 代码事实：[plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts#L185) 到 [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts#L301) `renderBackendRuntimeSection()` 展示状态卡、错误与最近输出
- 代码事实：[plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts#L303) 到 [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts#L328) `renderHealthSection()` 只在 `health` 存在时展示细节
- 代码事实：[plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts#L330) 到 [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts#L341) `handleStartBackend()` 只是把 runtime 结果翻译成 Notice

### 13. 当前已讲清的配置层：为什么 `settings.ts` 不能写死

问题：为什么启动参数不直接写在代码里，而要暴露到设置页？

思路：把“配置”讲成“环境差异 + 控制策略”，不要只说“方便”。

方案：
- 因为这个插件运行在用户本地，每个人的环境都可能不同：
  - backend URL 可能不同
  - 启动命令可能不同
  - 工作目录可能不同
  - 启动所需时间可能不同
- 所以 `settings.ts` 把以下内容显式开放给用户配置：
  - `backendUrl`
  - `requestTimeoutMs`
  - `backendStartCommand`
  - `backendStartWorkingDirectory`
  - `backendStartupTimeoutMs`
  - `backendHealthCheckIntervalMs`
  - `autoStartBackendOnLoad`
- 这些不是“业务参数”，而是插件侧 backend control plane 的运行策略。
- 如果写死在代码里，会有三个问题：
  - 换环境就得改代码
  - 无法针对慢机器/快机器调整启动超时和轮询间隔
  - 用户无法选择“手动启动”还是“插件自动启动”

面试一句话：
- 这一层配置化的目的不是图省事，而是把环境差异和运行策略从代码里抽出来，让插件在不同本地机器上都能工作，同时保持控制面可调。

项目代码落地：
- 代码事实：[plugin/src/settings.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/settings.ts#L5) 到 [plugin/src/settings.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/settings.ts#L12) 定义 `KnowledgeStewardSettings` 与默认值
- 代码事实：[plugin/src/settings.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/settings.ts#L14) 到 [plugin/src/settings.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/settings.ts#L121) 设置页显式暴露 backend URL、启动命令、工作目录、timeout、poll interval 和 auto-start

### 14. 模块 G 五句话串讲

问题：如果面试官让你用 30-45 秒串起模块 G，该怎么说？

方案：
1. 模块 G 本质上不是普通插件 UI，而是插件侧的 backend control plane。
2. `main.ts` 只负责装配和调度，把面板、命令、设置页和 backend runtime 接起来。
3. `runtime.ts` 维护统一 `snapshot`，并把后端状态拆成 `checking / starting / ready / unavailable / failed`，避免把可用性问题压成一个模糊红绿灯。
4. `KnowledgeStewardView.ts` 订阅这份状态，把它翻译成按钮启用/禁用、状态卡片、错误提示和最近输出，所以用户不但知道“坏了”，还知道“为什么坏、下一步该做什么”。
5. `settings.ts` 把 URL、启动命令、工作目录、超时和 auto-start 配置化，是为了适配不同本地环境和运行策略，而不是把这些环境差异硬编码进插件。

面试一句话：
- 模块 G 解决的是“插件如何稳定管理本地后端可用性”，让系统从“后端能单独跑的 demo”进化成“用户能在插件里看见状态、触发动作、并完成排障的产品”。

### 15. 模块 G 两道高频场景题

#### 题 1：后端进程已经拉起来了，但 `/health` 一直不通，随后进程自己退出，你怎么设计状态和 UI？

高分思路：
- 状态流转应是 `starting -> failed`，而不是直接吞成 `unavailable`
- 因为这是“一次明确的启动失败”，不是普通不可用
- UI 要显示 `last_error`、`last_exit_code`、`recent_output`，帮助用户定位是端口、依赖还是启动命令问题
- `starting` 期间要禁用重复启动，失败后允许重试

项目代码落地：
- 代码事实：[plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L305) 到 [plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts#L315) ready 前退出会显式标成 `failed`
- 代码事实：[plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts#L283) 到 [plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts#L299) UI 会展示错误和最近输出

#### 题 2：不同用户机器启动速度差异很大，为什么不能把启动超时、轮询间隔、启动命令都写死？

高分思路：
- 因为这些不是业务规则，而是环境差异和运行策略
- 写死会导致换机器就改代码，慢机器频繁误报失败，快机器又浪费等待时间
- 正确做法是把 `backendStartCommand`、`backendStartupTimeoutMs`、`backendHealthCheckIntervalMs`、`autoStartBackendOnLoad` 配置化
- 这样 runtime 逻辑保持稳定，不同环境只改配置

项目代码落地：
- 代码事实：[plugin/src/settings.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/settings.ts#L5) 到 [plugin/src/settings.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/settings.ts#L12) 定义了运行配置
- 代码事实：[plugin/src/settings.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/settings.ts#L54) 到 [plugin/src/settings.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/settings.ts#L120) 设置页暴露了启动命令、工作目录、超时、轮询和 auto-start

## Step 3：模块 H：观测与评估闭环（第一轮）

### 1. 先把两个最容易混的概念拆开

问题：`观测` 和 `评估` 到底有什么区别？

思路：先分“过程证据”和“结果验收”，不要一上来就堆指标名。

方案：
- `观测` 更偏过程证据：系统这次怎么跑的，经过了哪些节点，在哪一步出问题。
- `评估` 更偏结果验收：系统最后产出的答案、proposal、resume 结果到底好不好。
- 更工程化一点说：
  - 观测负责排障
  - 评估负责验收

项目代码落地：
- 代码事实：[backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py) 负责记录 runtime trace
- 代码事实：[eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py) 负责跑离线 golden set 回归

面试一句话：
- 我把“过程观测”和“结果评估”拆开做：前者回答系统怎么跑，后者回答系统跑得好不好。

### 2. `runtime_trace.py` 第一层职责：把运行过程落盘

问题：这个文件最核心在做什么？

思路：不要把它讲成“指标计算器”，它本质是过程记录器。

方案：
- `build_jsonl_trace_hook()`：把 trace event 追加写入 JSONL，更像原始流水账，适合当前排障。
- `build_sqlite_trace_hook()`：把 trace event 写入 SQLite `run_trace` 表，更像结构化台账，适合后续聚合查询。
- `compose_trace_hooks()`：把多个 sink 组合起来，并对单个 sink 失败做 best-effort 隔离，避免观测反向拖垮主链路。

项目代码落地：
- 代码事实：[backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py#L43) 到 [backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py#L55) 提供 JSONL / SQLite hook 构造器
- 代码事实：[backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py#L58) 到 [backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py#L73) 组合多个 hook，并逐个吞掉单 sink 异常
- 代码事实：[backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py#L76) 到 [backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py#L118) 分别落地 JSONL 追加写入与 SQLite `run_trace` 写入

面试一句话：
- JSONL 负责保留原始事件，SQLite 负责结构化查询；两者服务的是排障和查询两类不同需求。

### 3. trace 事件为什么必须带身份字段

问题：为什么 trace 不能只写一句文本日志，而要显式记录 `run_id / thread_id / graph_name / node_name`？

思路：把它讲成“可定位身份”，不要只说“方便排查”。

方案：
- `thread_id` 表示同一条业务流程线程，解决“这是谁的持续上下文”。
- `run_id` 表示这条线程的一次具体执行尝试，解决“这是第几次跑、是不是恢复后的新尝试”。
- `graph_name` 和 `node_name` 负责把问题定位到具体 workflow 和节点，而不是只停在“系统报错了”。
- 如果没有这组身份字段，trace 很容易退化成不可检索、不可聚合、不可复盘的普通日志文本。

项目代码落地：
- 代码事实：[backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py) 顶部 `PersistedRunTraceEvent` 明确把 `run_id / thread_id / graph_name / node_name / event_type / action_type / timestamp / details` 作为持久化事件的核心字段
- 代码事实：[backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py#L179) 到 [backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py#L199) `_build_sqlite_trace_record()` 会先规范化事件，再基于这些字段生成稳定 `trace_id`

面试一句话：
- `thread_id` 保证业务连续性，`run_id` 保证单次执行可观测性；trace 不是写日记，而是在给运行过程建立可定位身份。

### 4. 为什么单个 trace sink 失败要 best-effort 吞掉

问题：既然 trace 很重要，为什么 `compose_trace_hooks()` 里单个 sink 失败时不直接报错？

思路：把它讲成“观测故障不能升级为业务故障”。

方案：
- trace 属于观测补充链路，不是 ask / ingest / digest 的主业务结果本身。
- 如果因为 SQLite 或 JSONL trace 写失败，就把主 workflow 一起打崩，相当于让观测系统变成新的单点。
- 所以当前实现选择 best-effort：
  - 能写就写
  - 某个 sink 坏了就降级到其他 sink 或直接放过
  - 不反向拖垮主链路
- 但代价是：trace 可能静默断流，后续排障和统计会变难。
- 所以后续必须补：
  - trace health check
  - 断流发现
  - 告警或失败计数

项目代码落地：
- 代码事实：[backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py#L58) 到 [backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py#L73) `compose_trace_hooks()` 会逐个执行 hook，并吞掉单个 sink 的异常

面试一句话：
- 观测系统不能成为业务系统的新单点，所以 trace sink 失败时我选择 best-effort 降级；但这不代表问题消失了，后续还要补断流监控和告警。

### 5. 为什么 trace 写失败不能直接打崩主业务

问题：既然 trace 断流会让排障变难，为什么这里还是不能让 trace 写失败直接打崩 ask / ingest / digest？

思路：把它讲成“主链路优先级高于辅助链路”。

方案：
- 主业务链路的职责是给用户返回 ask、digest、resume 等结果。
- trace 写入只是观测补充链路，它很重要，但不是用户请求的主结果本身。
- 如果因为 trace 写失败就让主 workflow 失败，相当于让辅助链路反客为主，放大故障影响面。
- 所以正确取舍是：
  - 业务结果优先
  - 观测 best-effort
  - 同时再补断流发现，而不是把两者绑定成同生共死

面试一句话：
- 主链路负责交付业务结果，观测链路负责补充过程证据；前者优先级更高，所以观测失败不能直接升级成业务失败。

### 6. 为什么 trace 事件要先 normalize，再生成 `trace_id`

问题：为什么 `_normalize_trace_event()` 不直接跳过，而要在落库前先清洗字段？

思路：把它讲成“先保证结构稳定，再谈持久化和查询”。

方案：
- 如果 event 原样乱写，字段可能缺失、类型可能漂移、`details` 还可能不可 JSON 序列化。
- 这样一来：
  - SQLite 落库会不稳定
  - 后续聚合查询会变脆
  - 同类事件无法稳定比较
- 所以当前实现先做三件事：
  - 强制校验核心身份字段不能为空
  - 把 `details` 收敛成可 JSON 序列化的结构
  - 再基于规范化后的字段和 `details_json` 生成稳定 `trace_id`
- 这相当于把 trace 事件从“临时日志对象”变成“可持久化事实记录”。

项目代码落地：
- 代码事实：[backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py#L220) 到 [backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py#L248) `_normalize_trace_event()` 会校验必填字段，并把异常形态的 `details` 兜底成结构化字典
- 代码事实：[backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py#L252) 到 [backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py#L274) `_build_trace_id()` 基于规范化字段拼接 raw key，再生成稳定哈希 ID

面试一句话：
- trace 想真正可查、可聚合、可去重，就不能原样乱存；要先把事件规范化，再给它一个稳定身份。

### 7. 为什么 `trace_id` 还要带 `timestamp` 和 `details_json`

问题：为什么 `trace_id` 不能只用 `run_id + node_name`，而还要把 `timestamp` 和 `details_json` 放进去？

思路：把它讲成“避免 identity 过粗”。

方案：
- 同一条 `run_id` 里的同一 `node_name`，也可能出现多次事件：
  - 重试
  - 不同 `event_type`
  - 不同细节 payload
- 如果 identity 过粗，很容易把本来不同的事件误合并。
- 所以当前实现把 `timestamp` 和 `details_json` 也纳入 hash key，让事件 identity 更细，先兜住“重复落同一条事件”这类最小幂等问题。
- 但这也意味着它还不是完整的事件版本治理：
  - 如果事件结构将来大改
  - 或同一语义事件时间戳变化
  - 当前 `trace_id` 方案仍可能需要同步演进

面试一句话：
- 当前 `trace_id` 解决的是最小幂等去重，避免 identity 过粗把不同事件误合并；它不是完整的事件版本治理方案。

### 8. `run_id` 查询和 `thread_id` 查询分别看什么

问题：查 trace 时，什么时候按 `run_id`，什么时候按 `thread_id`？

思路：把它拆成“单次执行视角”和“业务线程视角”。

方案：
- 按 `run_id` 查：
  - 适合看“这一次具体执行发生了什么”
  - 例如：这次 ask 为什么失败、卡在哪个 node、是不是某次重试才成功
- 按 `thread_id` 查：
  - 适合看“同一条业务线程的历史演进”
  - 例如：第一次运行停在 waiting_for_approval，后面 resume 后又发生了什么
- 所以两者不是替代关系，而是两个观察切面：
  - `run_id` 偏单次执行
  - `thread_id` 偏跨执行连续性

项目代码落地：
- 代码事实：[backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py#L121) 到 [backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py#L173) `query_run_trace_events()` 强制要求至少带一个 `run_id` 或 `thread_id`

面试一句话：
- `run_id` 让我看清某一次执行，`thread_id` 让我看清同一条业务线程跨多次执行的连续轨迹。

### 9. `eval/run_eval.py` 第一层定位：固定回归考卷，不是临时 demo

问题：`golden set` 到底是什么？为什么不能只靠 demo 证明系统可用？

思路：把它讲成“固定考卷 + 固定判分规则”。

方案：
- `golden set` 不是“标准答案全文集合”，而是一组固定样本：
  - 给定输入
  - 给定运行设置
  - 给定预期 contract / 指标 / fallback
- `eval/run_eval.py` 的职责不是临时试试看，而是每次都按同一批样本重复执行，检查系统有没有退化。
- 所以它本质上是：
  - 固定考卷
  - 固定运行环境
  - 固定判分规则

项目代码落地：
- 代码事实：[eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L95) `load_golden_cases()` 会从 `eval/golden/*.json` 读取固定 case
- 代码事实：[eval/golden/ask_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/golden/ask_cases.json) 中每个 case 都显式写了 `request / setup / expected`
- 代码事实：[eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L473) `run_case()` 会对单个 case 建 fixture、跑 entrypoint、生成 snapshot、做断言并返回 passed / failed

面试一句话：
- demo 只能证明“这一刻看起来能跑”，golden eval 才能证明“同一批关键场景没有回归”。

### 10. `golden set` 和 `fixture` 分别是什么

问题：这两个词在 `run_eval.py` 里分别扮演什么角色？

思路：把它们拆成“考卷”和“考场”。

方案：
- `golden set` = 固定 case 集
  - 定义了要测什么
  - 包含 `request / setup / expected`
- `fixture` = 可重复运行环境
  - 定义了在什么本地条件下跑
  - 例如临时 vault、临时 SQLite、临时 trace 路径、mock provider / embedding
- 所以可以把它们记成：
  - `golden set` 是考卷
  - `fixture` 是考场

项目代码落地：
- 代码事实：[eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L95) `load_golden_cases()` 负责加载 fixed case
- 代码事实：[eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L108) `build_fixture()` 负责构造不同 fixture

面试一句话：
- golden set 决定“测什么”，fixture 决定“在什么可重复环境下测”。

### 11. 为什么 `build_eval_settings()` 要压住 provider 配置

问题：为什么 `run_eval.py` 里要故意覆盖 provider 配置，而不是直接用机器当前环境？

思路：把它讲成“保护可重复性”。

方案：
- 同一批 golden case 的目标是可重复、可比较。
- 如果直接吃本机环境变量，可能出现：
  - 某台机器能连云模型
  - 某台机器没有 key
  - 某台机器模型名不同
- 这样同一批 case 会跑出两套结果，eval 就不再是稳定回归，而变成环境赌博。
- 所以 `build_eval_settings()` 会显式覆盖 provider 配置：
  - 需要无 provider 时就强制清空
  - 需要 mocked cloud 时就注入固定假配置

项目代码落地：
- 代码事实：[eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L328) 到 [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L377) `build_eval_settings()` 会根据 `provider_mode` 覆盖 chat / embedding provider 相关配置

面试一句话：
- eval 的第一原则不是“尽量像线上”，而是“同一 case 在不同机器上仍然得到可比较结果”。

### 12. 为什么离线 eval 经常 mock 外部模型和 embedding

问题：既然项目真实依赖模型，为什么 `run_eval.py` 里反而大量 mock provider / embedding？

思路：把它讲成“先去掉外部噪声，再验证内部 contract”。

方案：
- 外部模型和外部服务有天然不稳定性：
  - 网络波动
  - 模型版本变化
  - 供应商返回波动
  - 本地 key / 配置差异
- 如果把这些不确定性直接混进离线回归，同一个 case 今天和明天可能都不一样，结果就不可比较。
- 所以离线 eval 更适合：
  - mock 外部 provider
  - mock embedding
  - 把验证焦点压在内部 contract、fallback、状态流转和持久化事实上

项目代码落地：
- 代码事实：[eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L379) 到 [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L449) `_install_embedding_profile_mocks()` 会注入固定 embedding 返回
- 代码事实：[eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L542) 到 [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L561) `run_case_entrypoint()` 会对 ask 的 provider 返回做 mock，避免把离线回归绑定到真实联网可用性

面试一句话：
- 离线 eval 的重点不是考外部模型当天发挥，而是稳定验证系统自己的协议、降级和状态语义。

### 13. 为什么 `run_eval.py` 要先构造 snapshot，再做断言

问题：为什么不能只比最终回答文本，而要先做 `build_invoke_snapshot()`、`build_resume_snapshot()` 这类结构化快照？

思路：把它讲成“验证的不只是文本，而是整条 contract 和副作用事实”。

方案：
- 系统输出不只是一个 answer string。
- 真正需要验证的还有：
  - `http_status`
  - `workflow_status`
  - `approval_required`
  - `fallback` 信号
  - citation / proposal 结构
  - `checkpoint / audit_log / writeback_result` 这些持久化副作用事实
- 所以 `snapshot` 的作用是把一次运行结果收敛成“可稳定比较的结构化事实视图”，而不是只盯着最终文本。
- 这让 eval 能同时检查：
  - 返回 contract 对不对
  - 降级分支对不对
  - 高风险链路有没有把副作用事实正确落库

项目代码落地：
- 代码事实：[eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L577) 到 [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L679) `build_invoke_snapshot()` 会把 ask / ingest / analysis / digest / proposal 收敛成结构化输出
- 代码事实：[eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L682) 到 [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L723) `build_resume_snapshot()` 会额外把 `checkpoint` 和 `audit_log` 拉进快照

面试一句话：
- snapshot 不是为了“看日志”，而是为了把返回结果、降级行为和持久化副作用统一收敛成可断言的结构化事实。

### 14. `resume` 里什么是 contract，什么是 persisted fact

问题：为什么 `build_resume_snapshot()` 不只看接口返回，还要额外把 `checkpoint` 和 `audit_log` 查出来？

思路：先分清“接口约定”和“落库事实”。

方案：
- `contract`
  - 指 API 输入输出约定的数据结构
  - 例如 `approval_decision`、`writeback_result`、HTTP 返回里的 `message / run_id / thread_id`
- `persisted fact`
  - 指这次调用之后，数据库里真正留下的事实
  - 例如：
    - `checkpoint`：workflow 当前状态快照，表示线程是否还在 waiting、是否已 completed
    - `audit_log`：append-only 审计记录，表示谁批准了什么、写回是否成功、前后 hash 是什么
- `writeback_result`
  - 它本身首先是 contract 里的一个结构，表示插件本地写回执行得怎么样
  - 但当它被写进 checkpoint / audit_log 后，又会成为 persisted fact 的一部分
- 所以 `build_resume_snapshot()` 要同时校验：
  - 表面返回值对不对
  - 线程状态是否真的从 waiting 变成 completed
  - 审计事实是否真的落库

项目代码落地：
- 代码事实：[backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py#L62) 到 [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py#L80) 定义了 `ApprovalDecision`、`WritebackResult` 和 `AuditEvent`
- 代码事实：[backend/app/graphs/checkpoint.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/checkpoint.py#L29) 到 [backend/app/graphs/checkpoint.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/checkpoint.py#L42) 定义了 checkpoint 状态
- 代码事实：[backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py#L168) 到 [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py#L184) 在同一事务里同时写 audit 和 completed checkpoint

面试一句话：
- `resume` 不能只验证接口回了什么，还要验证线程状态和审计事实是否真的落库；否则只是在测表面 contract，没有测高风险副作用链路。

### 15. `checkpoint` 和 `audit_log` 的一句话区别

问题：这两个都落库了，到底分别记录什么？

思路：一个看“现在停在哪”，一个看“之前发生了什么”。

方案：
- `checkpoint`
  - 记录 workflow 线程当前状态
  - 核心问题是：现在停在哪一阶段、恢复时该从哪里继续
- `audit_log`
  - 记录已经发生过的审批 / 写回事件
  - 核心问题是：谁做了什么、结果怎样、前后 hash 和错误是什么

面试一句话：
- checkpoint 面向恢复，audit_log 面向审计；前者回答“现在在哪”，后者回答“发生过什么”。

### 16. 为什么 `resume` 返回成功不等于系统真的成功

问题：为什么高风险链路不能只看 HTTP 200 或接口返回 message？

思路：把“表面 contract”与“持久化副作用事实”分开。

方案：
- 接口返回成功，只能说明表面 contract 看起来对。
- 但在 `resume` 这种高风险链路里，真正要验证的是：
  - checkpoint 是否真的从 waiting 变成 completed
  - audit_log 是否真的追加了一条审计记录
  - writeback_result 是否和前两者保持一致
- 如果接口回了成功，但这些持久化事实没落对，本质上仍是假成功。

面试一句话：
- 在高风险链路里，HTTP 成功只代表“说自己成功了”，而 checkpoint / audit / writeback 三份事实一致，才代表系统真的成功了。

### 17. 模块 H 必会的 5 个评估词

问题：`groundedness / faithfulness / relevancy / context_precision / context_recall` 分别是什么意思？

思路：先讲白话，再说明当前仓库里是怎么做“最小近似实现”的。

方案：
- `groundedness`
  - 问的是：答案里的说法有没有被引用证据真正支撑
  - 在当前仓库里，主要体现在 ask 的 `ask_groundedness` 分桶：`grounded / unsupported_claim / citation_missing / citation_invalid`
- `faithfulness`
  - 问的是：结果是否忠于证据
  - 当前 ask 场景优先复用 `ask_groundedness` 分桶；非 ask 场景退回到“关键支持上下文是否覆盖”的可解释基线
- `relevancy`
  - 问的是：输出有没有回答题目、有没有命中预期要点
  - 当前实现用 expected 里的输出提示词去匹配最终组合文本
- `context_precision`
  - 问的是：你拿出来的上下文里，有多少是真的应该拿的
  - 当前实现看实际上下文路径里，有多少命中了参考路径
- `context_recall`
  - 问的是：应该拿到的关键上下文，你到底拿全了没有
  - 当前实现看参考路径里，有多少被实际上下文覆盖到了

项目代码落地：
- 代码事实：[eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L987) 到 [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L1049) `build_quality_metrics_snapshot()` 会统一生成这 4 个质量指标
- 代码事实：[eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L727) 到 [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L803) `build_ask_groundedness_snapshot()` 会先对 ask 做 groundedness 分桶

面试一句话：
- 这套指标不是为了凑术语，而是分别回答：答得真不真、答得像不像题、证据拿得准不准、证据拿得全不全。

### 18. 大厂项目会不会真用这些指标

问题：`faithfulness / relevancy / context_precision / context_recall / groundedness` 这些词，大厂项目里会不会真的用？

思路：区分“概念层常见”和“命名层未必完全一致”。

方案：
- 会用这些评估维度，但名字未必完全一样。
- 在真实大厂项目里，通常会同时看 4 层指标：
  - 检索层：Recall@K、Precision@K、Hit Rate、NDCG
  - 生成层：groundedness / faithfulness / hallucination rate / answer relevance
  - 业务层：任务成功率、审批通过率、写回成功率、用户采纳率
  - 运行层：延迟、失败率、token 成本、fallback 比例
- 所以当前仓库这些词不是“教材摆设”，而是把真实项目常见评估维度做成了 interview-first 的最小版。

面试一句话：
- 大厂项目会看这些评估维度，但往往会按自己业务重命名、重加权，未必直接照搬开源框架字段名。

### 19. 当前仓库里这几个指标是怎么近似计算的

问题：这套指标在当前代码里到底怎么算？

思路：要明确这是“最小近似实现”，不是通用学术标准。

方案：
- `groundedness`
  - 只在 ask 场景里先做一层 rule-based 分桶
  - 做法：
    - 先检查答案有没有 citation marker
    - 再检查 citation 编号是否越界
    - 再把答案文本和 cited evidence 文本里的 term 做对比
    - 有明显越界 term 就分到 `unsupported_claim`
- `faithfulness`
  - ask 场景优先复用 `ask_groundedness`
    - `grounded / not_generated_answer` 记为 `1.0`
    - `unsupported_claim / citation_missing / citation_invalid` 记为 `0.0`
  - 非 ask 场景不强行做复杂 judge，而是退回 `context_recall` 作为可解释基线
- `relevancy`
  - 从 expected 里提取输出提示词
  - 再去实际输出文本里数命中了多少
  - 命中数 / 提示词总数 = 当前最小 relevancy 分数
- `context_precision`
  - 看“实际拿出来的上下文路径”里，有多少命中了参考路径
  - 公式近似为：
    - 命中的实际上下文数 / 实际上下文总数
- `context_recall`
  - 看“参考路径”里，有多少被实际上下文覆盖到
  - 公式近似为：
    - 命中的参考上下文数 / 参考上下文总数

项目代码落地：
- 代码事实：[eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L727) 到 [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L803) `build_ask_groundedness_snapshot()` 负责 ask groundedness 分桶
- 代码事实：[eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L804) 到 [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L854) 用 term extractor 找 unsupported terms
- 代码事实：[eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L987) 到 [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L1049) `build_quality_metrics_snapshot()` 统一计算 4 个质量指标
- 代码事实：[eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L1141) 到 [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py#L1160) `_compute_faithfulness_score()` 定义了当前项目的 faithfulness 近似逻辑

面试一句话：
- 当前仓库不是在追求“学术最优指标实现”，而是在用一套可解释、可重复、可回归的近似评估，把 retrieval、answer 和高风险 workflow 的退化先暴露出来。

### 20. 模块 H 高频场景题 1

问题：`resume_workflow` 接口返回 `HTTP 200`，但用户反馈 proposal 明明批过了，面板里却像没处理过一样。你怎么排查？

高分思路：
- 第一优先级不是先看 trace，而是先核对持久化事实：
  - `checkpoint` 是否还停在 `waiting_for_approval`
  - `audit_log` 是否新增了对应审批记录
  - `writeback_result` 是否和前两者一致
- 如果这三份事实不一致，说明是高风险恢复链路的状态分叉，不是单纯展示问题。
- `trace` 这时主要用于补充定位“卡在哪个节点、哪次 run 出的问题”，不是最终真相来源。
- 后续要补两类兜底：
  - 观测：对 `resume` 的 checkpoint / audit / writeback 三份事实增加更明确的 run 级对账字段和失败告警
  - 评估：在离线 eval 里同时断言 HTTP 返回、checkpoint、audit_log、writeback_result，避免只测表面成功

满分回答模板：

场景：
- `resume` 是高风险链路，因为它不只是回一个响应，还会改变 workflow 状态并写入审计事实。

风险：
- 最大风险不是接口报错，而是“接口说成功了，但 checkpoint / audit / writeback 三份事实分叉”，形成假成功。

设计：
- 排查顺序我会先查持久化事实，再查 trace。
- 第一步查 checkpoint：
  - 看 thread 是否从 `waiting_for_approval` 正确流转到 `completed`
- 第二步查 audit_log：
  - 看是否真的追加了审批 / 写回记录
- 第三步查 writeback_result：
  - 看 applied、before_hash、after_hash、error 是否与前两者对齐
- 第四步再查 trace：
  - 只用来补充定位 run_id、node_name、失败阶段和时间线

trade-off：
- 我不会把 trace 当唯一依据，因为 trace 是 best-effort，可能断流；checkpoint 和 audit_log 才是恢复链路的持久化事实源。

在本项目中的具体落地：
- [backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py) 当前已经把 append-only audit 和 completed checkpoint 放在同一 SQLite 事务里
- [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py) 的 `build_resume_snapshot()` 也不只看 HTTP 返回，而会额外拉出 checkpoint 和 audit_log 一起断言

面试一句话：
- 高风险恢复链路里，先对账持久化事实，再用 trace 补定位；不能把 best-effort 观测当成最终真相来源。

### 21. `trace` 和 `audit_log` 到底怎么区分

问题：它们看起来都在“记事情”，差别到底在哪？

思路：一个是黑匣子，一个是审计凭证。

方案：
- `trace`
  - 记录运行过程事件
  - 关心：哪次 `run_id`、哪个 `graph/node`、什么 `event_type`、什么时间发生
  - 用途：排障、性能定位、时间线回放
  - 特点：best-effort，允许单 sink 失败时降级
- `audit_log`
  - 记录高风险业务事实
  - 关心：谁批准了什么 proposal、写回是否成功、`before_hash / after_hash`、错误是什么
  - 用途：审计、追责、核对副作用是否真正落地
  - 特点：append-only，更接近 source of truth

项目代码落地：
- 代码事实：[backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py) 里的 trace 事件核心字段是 `run_id / thread_id / graph_name / node_name / event_type / timestamp / details`
- 代码事实：[backend/app/indexing/store.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/indexing/store.py#L1200) 注释直接强调 `audit_log` 必须 append-only，避免恢复或重放时把旧审批结果覆盖掉

面试一句话：
- trace 负责告诉我“系统怎么跑的”，audit_log 负责告诉我“高风险动作到底有没有真实发生”。

补充纠偏：
- `audit_log` 不是“审查流程本身”，而是“审计凭证 / 事实账本”
- 更白话地记：
  - `trace` = 黑匣子 / 流水账
  - `audit_log` = 审计凭证 / 高风险事实账本

高分补充：
- 高风险链路排查时，要先核事实，再补过程
- 因为：
  - 事实层回答“到底有没有真的发生”
  - 过程层回答“它是怎么发生的”
  - 如果事实本身都没对齐，就不能只靠过程观测判断系统成功

### 22. 模块 H 高频场景题 2

问题：SQLite trace sink 连续静默失败一周，但 ask / ingest / digest 主业务都还能正常返回。你怎么设计发现和治理机制？

高分思路：
- 先接受一个事实：best-effort 吞异常是对的，但不能停在“吞了就算了”。
- 回答要分三层：
  - 发现机制
  - 暴露 / 告警机制
  - 治理机制

满分回答模板：

场景：
- trace sink 断流时，业务表面仍正常，所以最危险的是“长期静默失效”。

风险：
- 排障时没有过程证据
- latency / failure / fallback 趋势统计失真
- 团队误以为系统健康，直到出事故才发现黑匣子早就停了

设计：
- 发现机制：
  - 为每个 sink 维护成功写入时间、连续失败次数、最近错误
  - 定期对比“最近业务 run 是否存在”与“最近 trace 是否持续写入”
  - 如果业务有 run、trace 长时间无新增，就判定为断流嫌疑
- 暴露 / 告警机制：
  - `/health` 或调试面板暴露 trace sink 健康状态
  - 在日志 / 指标里输出 sink failure counter、last_success_at、last_error
  - 连续失败超过阈值后发 Notice、写 error log 或进入 health degraded
- 治理机制：
  - 保留 best-effort，不让观测拖垮主业务
  - 但要补文件轮转、SQLite 写入失败计数、定期自检
  - 必要时允许 sink 自动降级，比如 SQLite 坏了先只保留 JSONL
  - 再配一条离线回归或 smoke test，验证 trace path 真的能写

trade-off：
- 我不会因为 trace 失败直接打崩主业务，但也不会只吞异常装没事；正确做法是“业务优先 + 断流可见 + 失败可治理”。

在本项目中的具体落地：
- [backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py) 当前已经做了单 sink best-effort 隔离
- 但主计划和会话记录里也明确把 trace 断流发现、文件治理和更强健康检查列为后续缺口

面试一句话：
- best-effort 只是第一步，真正成熟的做法是让观测故障不拖垮业务，同时让断流能被及时发现、暴露和治理。

### 23. 模块 H 30 秒串讲收束

问题：如果面试官让你用 30-45 秒讲清“观测与评估闭环”，怎么答？

方案：
1. 模块 H 本质上解决的不是“模型答得聪不聪明”，而是“系统出了问题时能不能定位、改完之后能不能验证没有回归”。
2. 在观测侧，我把运行过程和高风险事实拆开：`trace` 负责记录 `run_id / node / event_type` 这类过程事件，`checkpoint` 负责恢复状态，`audit_log` 负责高风险动作的审计凭证。
3. 在评估侧，我没有只靠 demo，而是用 `eval/run_eval.py` 跑固定 `golden set`，通过 `fixture` 固定环境、用 `snapshot` 同时断言返回 contract 和持久化副作用事实。
4. 指标上，我重点看 `groundedness / faithfulness / relevancy / context precision / context recall`，但当前实现是 interview-first 的可解释近似版，不会乱吹成通用最优 judge。
5. 工程取舍上，我允许 trace sink best-effort 失败不拖垮主业务，但必须补健康暴露、失败计数和断流治理，避免系统进入“业务还活着、观测却失明”的假健康状态。

面试一句话：
- 模块 H 的核心价值是：让系统既能被看见，也能被验证；前者解决排障，后者解决回归。

### 24. 全项目 2 分钟总复盘

问题：如果面试官让你不按模块背，而是 2 分钟讲完整个项目，应该怎么串？

思路：不要变成“念文件树”，而要按业务目标和系统责任边界来讲。

方案：
1. 这个项目不是普通 Obsidian 聊天助手，而是一个面向个人学习场景的知识治理系统。它要解决的核心问题不是“能不能问答”，而是笔记持续积累后出现的重复、冲突、孤立、复盘困难和高风险写回失控。
2. 整体架构上，我把系统拆成插件层和本地后端两层。插件层负责命令入口、审批面板、最终写回和本地后端运行时控制；后端负责 FastAPI 接口、LangGraph 工作流、检索索引、proposal 生成、checkpoint、audit 和 eval。
3. 在能力主线上，系统有三条 workflow：`ASK_QA` 负责可解释问答兜底，`INGEST_STEWARD` 负责新笔记治理，`DAILY_DIGEST` 负责周期复盘。它更接近单系统、多工作流的有状态 Agent，而不是多 Agent，也不是经典 ReAct。
4. 在检索层，我先做 SQLite FTS5，再补最小向量检索，最后用 RRF 做 hybrid retrieval。原因是 Obsidian 笔记既有关键词、标题、标签，也有语义改写，只走 BM25 或只走向量都不稳。当前没急着上 rerank，是因为首版先把可运行、可解释、可评估的底座打稳。
5. 在高风险链路上，我没有让模型直接改 Vault，而是让后端只生成结构化 `proposal + patch_ops`，进入 `waiting_for_approval` 后由插件做人审和受限写回。这样才能把控制面和副作用面分开，并通过 `before_hash / after_hash / rollback / audit_log` 做最小安全边界。
6. 在工程化闭环上，我补了 `thread_id + checkpoint` 做恢复，补了 `trace` 看运行过程，补了 `audit_log` 记高风险事实，补了 `eval/run_eval.py` 跑 golden set 和 benchmark。这样我在面试里讲的重点就不是“模型很聪明”，而是“系统可控、可恢复、可审计、可验证”。

项目代码落地：
- 后端入口：[backend/app/main.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/main.py)
- 三条 workflow：[backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py)、[backend/app/graphs/ingest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ingest_graph.py)、[backend/app/graphs/digest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/digest_graph.py)
- 检索底座：[backend/app/retrieval/sqlite_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_fts.py)、[backend/app/retrieval/sqlite_vector.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_vector.py)、[backend/app/retrieval/hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/hybrid.py)
- 审批恢复与写回对账：[backend/app/services/resume_workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/resume_workflow.py)
- 插件控制面：[plugin/src/main.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/main.ts)、[plugin/src/views/KnowledgeStewardView.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/views/KnowledgeStewardView.ts)、[plugin/src/backend/runtime.ts](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/plugin/src/backend/runtime.ts)
- 观测与评估：[backend/app/observability/runtime_trace.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/observability/runtime_trace.py)、[eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)

面试一句话：
- 我做的不是“把 LLM 接进 Obsidian”，而是把 LLM 钉进一个有状态、可审批、可恢复、可评估的知识治理工作流系统。
