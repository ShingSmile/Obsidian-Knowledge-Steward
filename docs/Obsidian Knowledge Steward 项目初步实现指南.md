# Obsidian Knowledge Steward 项目初步实现指南

## 执行摘要

本报告给出一个两周内可落地的“**Obsidian Knowledge Steward（基于 LangGraph 的个人学习知识治理与复盘 Agent）**”的工程化实现指南，目标不是做一个“能聊天的 Obsidian RAG”，而是做一个**可审计、可中断、可恢复、可评估**的“知识治理工作流系统”。LangGraph 的核心价值在于：它是**低级别编排**框架，擅长构建**有状态、长流程**的智能体工作流，并通过**checkpointer（检查点持久化）**在每个 super-step 保存状态快照，利用 thread（线程）实现会话记忆、人类在环、时间旅行调试与容错执行等能力。citeturn0search0turn0search15

两周冲刺的现实策略是：**fork/参考现成插件壳 + 复用现成 RAG 后端 + 你在其上“硬插”知识治理工作流（HITL + 写回审计 + Eval/Tracing）**。推荐的“最省时间且可讲故事”基线组合如下：

- **后端基线（强推荐）**：ObsidianRAG（Python backend + Obsidian 插件），它已具备“本地后端 + 插件 UI + SSE 流式 + 混合检索（Vector+BM25）+ CrossEncoder rerank + GraphRAG（wikilinks 扩展上下文）”等你最费时的骨架能力，且明确使用 LangGraph。citeturn6view0turn7view0turn11view0  
- **插件工程化基线（可补强）**：cbelling/obsidian-agent 的工程特性很“面试友好”（缓存、退避重试、限流、优雅降级、LangSmith 可选、测试覆盖等），可借鉴其 `src/checkpoint`、`src/vault`、`src/state` 等模块组织方式，但它偏聊天助手，需要你把“对话中心”改成“工作流中心”。citeturn3view0turn15view0  
- **LangGraph 官方范式参考**：`langchain-ai/langgraph-example` 强调一键启动生产级 HTTP microservice、内置持久化，并提到 API 设计受 OpenAI assistants API 启发；它适合作为你讲“生产化接口与持久化”的引用点与结构参考。citeturn16view0  

两周内的**成功定义**建议采用“硬指标 + 软指标”组合：硬指标覆盖检索召回/精确、写回错误率、P50/P95 延迟、成本；软指标覆盖人类在环可用性、可观测性完备度、可复现演示脚本完备度（demo 一键跑通）。评估层建议用 Ragas 的 Faithfulness、Answer Relevancy、Context Precision、Context Recall 等指标构建最小回归；这些指标在 Ragas 文档中给出了定义与计算方法（例如 Faithfulness 衡量回答的声明能否被检索上下文支持）。citeturn17search1turn0search14turn17search2turn17search0  

最后，本报告明确列出你未提供的关键工程约束（如 vault 规模、是否允许外网、可用模型预算等），在未指定前提下提供“默认可落地假设”和相应降级策略，避免方案在面试时被一问就崩。

## 项目目标与成功指标

### 未指定的关键假设与约束

下表是本方案依赖但你未提供的信息。面试时你必须显式说明这些假设，否则面试官会直接质疑 KPI 与方案合理性。

| 关键变量 | 目前状态 | 对设计的影响 | 建议默认假设（可调整） |
|---|---|---|---|
| Obsidian vault 笔记数量、总字数、附件规模 | 未指定 | 决定索引耗时、分块策略、缓存策略、分页与限流阈值 | 1k–10k 笔记；文本为主，附件少量 |
| 是否允许外网（调用云模型/云 Embedding/云 Reranker） | 未指定 | 决定模型路由与成本、隐私、可用性 | 默认“本地优先”，云模型可选 |
| 可用 GPU / CPU / 内存 | 未指定 | 决定 reranker 可用性、向量库与并发策略 | 默认无 GPU；rerank 可降级 |
| 模型预算（每次请求可用 token/成本） | 未指定 | 决定是否做多轮重试、是否做长上下文总结 | 设定月度预算上限（例如 <$X）并做路由 |
| 笔记命名/标签规范程度（是否混乱） | 未指定 | 决定 metadata 清洗与规则层强度 | 默认“中等混乱”，需规则+LLM 联合 |
| 是否接受后端常驻服务（FastAPI/本地 daemon） | 未指定 | 决定插件-后端通讯模式与部署脚本 | 默认常驻（localhost），插件可自启后端citeturn12view0turn7view0 |

### 项目目标

“Knowledge Steward”的目标不是回答问题，而是**持续治理你的学习资产**：将碎片笔记结构化、消除重复与冲突、补齐链接与标签、抽取行动项与复习计划，并以**人类在环**方式在关键写回动作前暂停审查，确保“可控且可追溯”。

目标可拆成三层闭环：

1) **知识资产盘点闭环**：新/改笔记 → 解析结构/元数据 → 召回相关旧笔记 → 检测冲突/重复/孤立 → 生成治理建议 → 人工审批 → 写回并审计。  
2) **学习复盘闭环**：近 1–7 天笔记 → 聚类主题 → 抽取“未解决问题/开放环” → 生成复习任务/卡片 → 人工确认 → 写入复盘笔记与任务清单。  
3) **问答兜底闭环**：当用户确实要问“我以前写过什么”，提供可解释的 RAG + 引用来源；但这不是主叙事。

LangGraph 的设计契合点在于：通过 checkpointer 持久化每一步图状态，使你能实现“暂停-审查-恢复”的 HITL，以及长流程容错。citeturn0search0turn0search12  

### 成功指标（KPI）与量化目标

建议 KPI 分为：检索质量、生成忠实度、写回安全、性能成本、稳定性与可观测性。

| KPI 类别 | 指标定义 | 量化目标（两周冲刺可达版本） | 说明/依据 |
|---|---|---|---|
| 检索质量 | Context Recall（召回率） | ≥ 0.80（Top-K=12） | Ragas 将 Context Recall 定义为 0–1，衡量相关信息是否被检索到，偏向“不漏重要结果”。citeturn17search0turn17search4 |
| 检索质量 | Context Precision（精确率/排序质量） | ≥ 0.60（Top-K=12） | Ragas 的 Context Precision 用于评估相关 chunk 是否排在前面。citeturn17search2turn17search6 |
| 生成可靠性 | Faithfulness（忠实度） | ≥ 0.85 | Ragas 定义 Faithfulness 为回答声明被上下文支持的比例（0–1）。citeturn17search1 |
| 生成相关性 | Answer Relevancy | ≥ 0.80 | Ragas 定义 Answer Relevancy 用于衡量回答与问题意图对齐程度（0–1）。citeturn0search14 |
| 写回安全 | 写回错误率 | ≤ 0.5%（以“审批通过后仍产生错误改动”为口径） | 你要把风险压到“几乎不出错”，靠 HITL + diff 预览 + 规则校验兜底。HITL 能力在 LangGraph 中通常通过 interrupt 配合 checkpointer 实现。citeturn0search12turn0search0 |
| 写回安全 | 不安全写回拦截率 | ≥ 99%（以规则/策略检测出危险操作为口径） | 如“删除大段内容”“跨文件批量覆盖”“破坏 frontmatter 格式”等必须被拦截并强制人工确认。 |
| 性能 | 端到端延迟（问答兜底） | P50 ≤ 2.5s；P95 ≤ 8s（本地模型/本地索引） | ObsidianRAG 已有 `/ask/stream` SSE 流式模式与 process_time 字段，可作为你基线测量点。citeturn7view0turn12view0 |
| 成本 | 平均每次请求成本 | 本地模式≈0；云模式：提供公式与上限（如 ≤ ¥0.05/次） | 预算未指定时，至少要给出“可计算公式 + 预算上限 + 路由策略”。 |
| 稳定性 | 工作流成功率 | ≥ 99%（不含人工拒绝） | 节点重试建议用 LangGraph RetryPolicy（指数退避、最大尝试次数等）。citeturn0search11 |
| 可观测性 | Tracing 覆盖率 | ≥ 90% 的图节点都有 span（latency/token/错误） | LangSmith 明确支持对 LangGraph（Python/JS）进行追踪。citeturn0search1turn0search9 |

## 关键用户场景与两周内 MVP 清单

### 高频场景与用例

Obsidian 的“高频”不在问答，而在“日常持续写入 + 结构逐渐腐化”。因此场景设计必须覆盖“新内容入库、旧内容治理、周期性复盘、行动项管理、检索问答兜底”。

建议至少覆盖以下 7 个高频场景（满足你要求的 ≥5）：

| 场景 | 触发方式 | 用户痛点 | Steward 的输出 | 风险点/必须 HITL？ |
|---|---|---|---|---|
| 新笔记入库治理 | 保存/修改笔记后自动触发；或命令手动触发 | 笔记写完就扔，后续找不到，结构混乱 | 自动补 tags、补链接、生成摘要区块、抽取 TODO、建议合并或拆分 | 高：涉及写回，必须 HITL |
| 课程/论文笔记去重与合并 | 手动批量选笔记触发 | 同一概念写多份，版本漂移 | 检测重复主题、生成合并方案、保留来源引用 | 高：必须 HITL（防误删） |
| 概念冲突检测 | 新笔记/复盘触发 | 旧笔记 A 写“结论1”，新笔记 B 写“结论2”冲突 | 输出冲突对照表 + 溯源引用 + 建议标注“版本/时间/条件” | 中：建议 HITL |
| 孤立笔记治理 | 每日/每周巡检 | 笔记无链接无标签，成为“知识黑洞” | 推荐 3–8 个可链接目标；建议分类文件夹/标签 | 低：可先只建议不写回 |
| 每日学习复盘 | 每晚固定触发 | 学完就忘，不形成复习闭环 | 生成“今日要点/未解问题/明日计划/复习卡片草稿” | 中：写回复盘笔记建议 HITL |
| “开放环”追踪（未解决问题） | 复盘时自动；或问答触发 | 问题散落在笔记里，无法收敛 | 提取问题清单，关联来源笔记与最后出现时间，生成待办 | 中：写回任务列表建议 HITL |
| 问答兜底 | Chat 提问 | 快速回忆“我在哪写过？” | 透明引用、来源链接、相关性分数；必要时 GraphRAG 扩展上下文 | 低：无需写回 |

这些场景中的“链接治理”之所以重要，是因为 Obsidian 内部链接（Wiki 链接 `[[...]]` 或 Markdown 链接）是其知识网络基础，并且重命名文件时 Obsidian 会自动更新指向该文件的内部链接，天然适合做“知识图结构”。citeturn13search0 同时 Obsidian 支持链接到标题（`#`）与块（`#^block-id`），使你能把“引用粒度”从文件级降到块级，这是你做高质量检索与审计的关键。citeturn13search0

### MVP 功能清单与优先级

两周冲刺必须用“P0 必做 / P1 加分 / P2 野心”分层，避免被工程细节拖死。

| 优先级 | 两周内必须完成（P0） | 可选加分项（P1） | 野心项（P2，不建议两周强做） |
|---|---|---|---|
| 产品形态 | Obsidian 插件侧栏 View + 命令面板入口 + 设置页 | 多视图：复盘面板、冲突面板、孤立笔记面板 | 跨端同步/移动端深度适配 |
| 后端服务 | 本地 Python 后端（FastAPI/CLI），插件可自启/探活 | 多进程/守护进程，崩溃自动拉起 | 分布式部署、多设备共享索引 |
| 工作流 | LangGraph DAG：ingest → analyze → propose → HITL → writeback → audit | 多入口统一图（ask/digest/ingest 三类） | 多 Agent supervisor（深度协作） |
| 检索 | 向量检索 + BM25 混合检索 + metadata 过滤 | reranker（BGE reranker）精排 | 图数据库 + GraphRAG 全局推理 |
| 写回安全 | diff 预览 + 人工审批（interrupt）+ 审计日志 | 自动回滚/撤销（基于 patch 反应用） | 自动合并冲突（git-like 三方合并） |
| 可观测性 | 基础 tracing：节点耗时/错误/检索内容记录 | LangSmith 全链路 trace | 线上 A/B、漂移检测 |
| Eval | Golden set（≥50 条）+ Ragas 指标 + 每日回归脚本 | 分场景基准（治理 vs 问答） | 自动生成/难例挖掘/对抗评测 |

你可以直接参考 ObsidianRAG 的“插件 + 后端”结构：插件通过 localhost HTTP 调后端，并支持 `/ask/stream` 的 SSE 事件流（包含 `retrieve_complete`、`token`、`answer` 等事件），这给你节省大量 UI/流式工程时间。citeturn7view0turn12view0

## 系统架构设计

### 组件图与数据流

下面给出一个“本地优先、两周可落地”的架构：插件负责 UI、Vault 读写与审批；后端负责索引、检索、LangGraph 工作流与评估；共享存储以 SQLite/Chroma（或你选择的向量库）为主。

```mermaid
flowchart TB
  subgraph Obsidian_App[Obsidian 桌面端 (Electron)]
    UI[Knowledge Steward Side Panel\n(复盘/治理/聊天兜底)]
    Plugin[Obsidian 插件(Typescript)\nVault IO + HITL UI + 应用写回]
    Vault[Vault 文件系统\n.md + 附件]
    Meta[MetadataCache\nlinks/tags/headings/blocks]
    UI --> Plugin
    Plugin <--> Vault
    Plugin <--> Meta
  end

  subgraph Local_Backend[本地后端 (Python)]
    API[FastAPI/HTTP + SSE\n/ask /ingest /digest /preview /apply]
    Graph[LangGraph 工作流引擎\nStateGraph + Checkpointer]
    Router[模型路由/策略\n(便宜模型 vs 重模型)]
    Retriever[检索层\nHybrid(BM25+Vector)+Rerank]
    Eval[Eval/回归\nRagas + golden set]
    Obs[Tracing/日志\nLangSmith(可选)+本地JSONL]
    API --> Graph
    Graph --> Router
    Graph --> Retriever
    Graph --> Obs
    Graph --> Eval
  end

  subgraph Storage[本地存储]
    CP[LangGraph Checkpoints\nSQLite Saver]
    DB[元数据/审计库\nSQLite]
    VS[向量库\nChroma/FAISS/LanceDB]
    FTS[BM25/全文索引\nSQLite FTS5 或专用引擎]
    Cache[语义缓存\nRedisSemanticCache(可选)]
  end

  Plugin <--> API
  Graph <--> CP
  Retriever <--> VS
  Retriever <--> FTS
  Graph <--> DB
  Router <--> Cache
```

关键依据与设计动机：

- **LangGraph 持久化**：当你编译图并指定 checkpointer 时，会在图执行每个 super-step 保存状态快照，并按 thread 组织；这为“中断-恢复、人类在环、容错执行”提供基础设施。citeturn0search0turn0search12  
- **HITL 的工程落点**：LangGraph 的 `interrupt()` 与 `Command(resume=...)` 用于将图暂停并在后续恢复（并要求配置 checkpointer）。citeturn0search12turn0search0  
- **Obsidian 写回能力**：插件侧可以使用 `Vault.read()`/`Vault.modify()` 修改文件内容，或用 `FileManager.processFrontMatter()` 原子读改存 frontmatter。citeturn14search15turn14search1turn14search0turn14search13  
- **混合检索必要性**：混合检索的核心思想是融合向量检索与 keyword/BM25 搜索并可配置权重；Weaviate 文档对这种融合给出清晰定义，你可以用同样思路在本地实现（并非必须用 Weaviate）。citeturn13search3turn13search7  
- **reranker 的位置**：FlagEmbedding 明确建议使用 cross-encoder reranker（如 bge-reranker）对 embedding 检索返回的 top-k 文档进行重排序，以提升相关性。citeturn1search3  

### 存储设计与 metadata schema

两周内建议“一个 SQLite + 一个向量库”解决 80% 问题：SQLite 存 metadata、审计、索引状态与（可选）FTS；向量库存 chunk embedding。

**核心表/集合建议：**

| 实体 | 关键字段 | 索引建议 | 用途 |
|---|---|---|---|
| notes | note_id（hash(path)）、path、title、mtime、ctime、tags、aliases、out_links、in_links_count | `path` 唯一；`mtime`；`tags` | 增量索引、过滤与治理决策 |
| chunks | chunk_id、note_id、parent_id、chunk_type、heading_path、block_id、start/end、text、tokens、embedding_id | `note_id`；`chunk_type`；`heading_path` | parent-child 检索、粒度控制 |
| fts_chunks（可选） | chunk_id、text、path、tags（冗余） | SQLite FTS5 | BM25 召回 |
| graph_edges（可选 P1） | src_note_id、dst_note_id、edge_type（wikilink/mention） | src/dst | GraphRAG/链接治理 |
| audit_log | event_id、timestamp、thread_id、note_id、proposal、decision、applied_patch、hash_before/after、actor | timestamp；note_id | 审计与可回放 |

**metadata 采集来源建议：**

- Obsidian 的 `MetadataCache` 会缓存 markdown 文件的元数据（frontmatter、headings、links、tags、blocks 等），它能让你避免每次都重新解析文件。citeturn1search1turn14search8turn13search10  
- `MetadataCache.unresolvedLinks` 明确给出“未解析链接”的映射结构，可用于治理“空链接/缺失笔记”的修复建议。citeturn13search2  

### 模型路由、语义缓存与降本策略

在“未指定预算”的情况下，你至少要把路由策略写成**可配置**，并用指标解释为何这么做。

- 路由输入：任务类型（ingest/digest/ask）、风险等级（是否写回）、上下文规模（token/字符数）、是否命中语义缓存。  
- 路由输出：LLM（大/小）、是否启用 rerank、是否启用 GraphRAG 扩展、最大输出 token、温度等。

**语义缓存建议（P1 加分）**：Redis 与 LangChain 的集成文档明确提到可以用 Redis 做 vector search、semantic caching、对话记忆等；同时 `langchain-redis` README 也明确包含 semantic caching 能力。citeturn2search2turn2search18turn2search6  
两周内你可先实现“简化版语义缓存”（SQLite 存 embedding + 响应），再扩展到 RedisSemanticCache。

## LangGraph 工作流设计

### 总体工作流思路

你应避免“一个 ReAct agent 乱跑”，而采用**确定性的状态机/DAG**。建议把入口统一为 `action_type`，通过条件路由进入不同子流程：`ASK_QA`（问答兜底）、`INGEST_STEWARD`（新笔记治理）、`DAILY_DIGEST`（复盘）。

LangGraph 的持久化能力强调：在配置 checkpointer 后，图会保存每步 checkpoint，并以 thread_id 管理；这使你可以在工作流中断后恢复，适用于 HITL。citeturn0search0turn2search13  

下面给一个“单图多入口”的示意（你可以用 LangGraph 的 conditional edges 实现）：

```mermaid
flowchart TD
  START((START))
  route[route_intent\n(识别 action_type/风险)]
  START --> route

  route -->|ASK_QA| qa_retrieve[qa_retrieve\nHybrid+Rerank]
  qa_retrieve --> qa_generate[qa_generate\n基于引用生成]
  qa_generate --> END((END))

  route -->|INGEST_STEWARD| load_note[load_note\n读取/解析目标笔记]
  load_note --> related_retrieve[related_retrieve\n按标签/链接/时间过滤+检索]
  related_retrieve --> analyze[analyze_consistency\n重复/冲突/孤立检测]
  analyze --> propose[propose_changes\n产生结构化变更提案]
  propose --> hitl{human_approval\ninterrupt}
  hitl -->|approve| writeback[apply_patch\n写回(插件侧执行)]
  hitl -->|reject| archive[archive_proposal\n记录拒绝原因]
  writeback --> reindex[reindex_incremental\n更新索引状态]
  archive --> END
  reindex --> END

  route -->|DAILY_DIGEST| collect[collect_recent_notes]
  collect --> cluster[cluster_topics]
  cluster --> plan[plan_review_tasks\n复习/开放环]
  plan --> hitl2{human_approval\ninterrupt}
  hitl2 -->|approve| write_digest[write_digest_note]
  hitl2 -->|reject| END
  write_digest --> END
```

### Node/Edge 详细设计（输入输出、条件路由、checkpoint、异常处理）

你在面试里必须能清晰说出：每个 Node 的输入输出边界是什么；失败如何重试；哪里 checkpoint；哪里降级。

下表给出 P0 必做节点（可按你实现进一步细化）：

| Node | 输入（state 关键字段） | 输出 | 条件路由/Edge 逻辑 | checkpoint/HITL | 异常处理与降级 |
|---|---|---|---|---|---|
| route_intent | user_request、active_file(optional) | action_type、risk_level、thread_id | 规则+轻量分类：写回类→高风险 | checkpoint 自动由 checkpointer 保存citeturn0search0 | 分类失败→默认 ASK_QA（最低风险） |
| load_note | note_path / active_file_id | note_text、note_meta（tags/links/headings） | 进入治理链路 | — | 读取失败：用 Vault.cachedRead 或 fallback 读取；插件侧提示citeturn14search15 |
| related_retrieve | note_text、meta_filters | retrieved_chunks（带来源与分数） | Hybrid 检索后进入 analyze | — | rerank 不可用→跳过；GraphRAG 不可用→跳过 |
| analyze_consistency | note、retrieved | issues（duplicates/conflicts/orphans）、evidence | issues 为空→仅轻量建议或直接 END | — | LLM 超时→降级为规则检测（如相似度阈值） |
| propose_changes | issues + evidence | proposal（结构化 patch） | 进入 HITL | — | JSON 解析失败→强制重新生成/自修复解析 |
| human_approval | proposal | Command(resume)/decision | approve → apply_patch；reject → archive | **interrupt 必须放在节点开头或专用节点**，且需要 checkpointer；恢复通过 Command resume。citeturn0search12turn0search0 | 若 UI 未响应→提供“导出 proposal JSON”离线审批 |
| apply_patch | approved_proposal | applied_result、hash_after | 成功→reindex；失败→rollback/记录错误 | 建议在写回前后记录 hash | 写回失败→不重试破坏性操作；仅提示并保留草案 |
| reindex_incremental | changed_note_ids | index_state_updated | END | — | 索引失败→标记 dirty，后台重建 |
| archive_proposal | proposal + reject_reason | audit_log_written | END | — | 写日志失败→降级写 local JSONL |

**节点重试（重要加分项）**：LangGraph 的节点可以配置 `RetryPolicy`，包含 initial_interval、backoff_factor、max_attempts 等，并且对部分异常（如 httpx 5xx）才重试；这非常适合你处理模型 API 抖动、网络问题等。citeturn0search11

### LangGraph 持久化与 checkpointer 选型

两周内优先选 SQLite：因为它部署简单、无需额外服务。

- `langgraph-checkpoint-sqlite` 在 PyPI 明确是 LangGraph checkpoint saver 的 SQLite 实现。citeturn2search0  
- 如果未来要多并发/更强一致性，可迁移到 Postgres checkpointer；LangGraph 操作指南介绍了 `langgraph-checkpoint-postgres` 的用法，并强调使用 LangGraph API 时可无需手动实现 checkpointer（但你现在是自建后端）。citeturn2search1  

## 检索与索引实现细节、HITL 设计、可观测与 Eval、两周计划与面试叙事

### 检索与索引实现细节

#### Chunking 策略（必须“像 Obsidian”，而不是像 PDF）

Obsidian 的结构强、语法明确：标题层级、块、列表、代码块、表格、frontmatter。你应该按这些“自然边界”切分，以便 metadata filter 和写回对齐。

推荐 P0 分块策略（两周可做）：

1) **Frontmatter 单独成块（chunk_type=frontmatter）**：因为治理最常改它（tags/aliases/status）。Obsidian API 允许通过 `FileManager.processFrontMatter()` 原子改写。citeturn14search0turn14search13  
2) **按 Heading 切块（chunk_type=section）**：每个 heading 形成一个 parent；其下段落/列表为 child。Obsidian 帮助文档也强调可链接到标题（`#`），你可以把 `heading_path` 写入 metadata，支持“引用到标题级”的检索。citeturn13search0  
3) **代码块单独成块（chunk_type=code）**：代码检索高度依赖关键字与符号，混合检索在此最有效。  
4) **表格单独成块（chunk_type=table）**：表格可先保留 markdown 原文，同时提取“表头+每行摘要”做附加字段（便于 BM25）。  
5) **块引用/块 ID（可选 P1）**：Obsidian 支持块链接 `#^`，说明“块”为一等公民；你可在 chunk metadata 保存 block_id 以支持更细粒度引用。citeturn13search0  

#### Parent-child（两周内建议做，性价比高）

Parent-child 的价值：**子块用于检索精度，父块用于上下文完整性**。LangChain 文档的 ParentDocumentRetriever 明确描述了“先检索小块，再返回其父文档/更大块”的机制，解决“小块 embedding 精准但语境不够 vs 大块语境够但 embedding 失真”的矛盾。citeturn1search2

你完全可以用同理念自研（不一定要直接用 LangChain Retriever）：在向量库里存 child chunk embedding，在 SQLite 里维护 `child -> parent_id` 映射，最后返回 parent text。

#### 表格/代码块/图片处理（两周现实版）

- 表格：保留 markdown 表格原文；额外生成 “flattened text”（把表头和每行拼成句子）放入 BM25 索引。  
- 代码块：保留原文；并提取 `language`、关键 import、函数名作为 metadata。  
- 图片：两周内不要做 OCR（高风险高工时）。只做：解析 `![[image.png]]` 或 markdown image 链接，记录为 “附件引用”；可在回答中提示“此处引用了图片，暂不解析”。Obsidian 内部链接语法也覆盖附件链接（包括需带扩展名的情况）。citeturn13search0  

#### BM25 + 向量混合 + reranker

- 混合检索的定义：融合 vector search 与 keyword（BM25/BM25F）检索结果，并可配置融合方法与权重。citeturn13search3turn13search7  
- ObsidianRAG 已经提供了“Hybrid search（Vector + BM25）+ CrossEncoder reranking”的实现方向，并在配置中暴露 `BM25_WEIGHT`、`VECTOR_WEIGHT`、`RERANKER_MODEL`、`RERANKER_TOP_N` 等参数，这对你两周内快速复现与改造非常关键。citeturn7view0turn6view0  
- FlagEmbedding 明确发布了 bge-reranker 系列 cross-encoder，并建议用于对 embedding 检索返回的 top-k 文档重排。citeturn1search3  

### Human-in-the-loop 交互设计（卡点、UI/UX 最小实现、审批流程、审计日志）

#### 卡点策略（你要“卡在危险之前”）

HITL 不是装饰，而是你整个项目“工业级感”的来源。推荐两个强制卡点：

1) **写回前卡点（强制）**：任何会修改 vault 的操作（frontmatter、插入链接、删除段落、重命名文件）必须 `interrupt()`，输出可审查的 proposal（含证据引用与 diff）。LangGraph 文档明确：在图中使用 interrupt 需要指定 checkpointer；恢复通过 invoke/stream 等配合 Command 原语；同时提醒 interrupt 会在恢复时重新运行整个节点，因此最好放在节点开头或独立节点。citeturn0search12turn0search0  
2) **批量操作前卡点（强制）**：如“合并多篇笔记”“批量补标签”“全库巡检自动修复”。

#### UI/UX 最小实现建议（两周能做）

你不需要做漂亮 UI，但必须做到“可用、可审计”。

最小 UI 组件清单：

- **Proposal 面板**：显示  
  - 变更摘要（例如：新增 3 个 tags、插入 5 条 wikilinks、生成 1 段摘要）  
  - 证据引用（从哪些 notes/sections 来）  
  - diff 预览（before/after）  
- **三个按钮**：Approve / Reject / Edit（Edit 可先做“导出 JSON，用户手改再 resume”）  
- **审计记录入口**：最近 20 条治理记录（时间、文件、动作、结果）

写回实现建议：

- frontmatter：用 `FileManager.processFrontMatter()` 原子修改（避免竞态与破坏 YAML）。citeturn14search0turn14search13  
- 正文：用 `Vault.modify()` 覆盖写入；或用 `Vault.process()` 基于当前内容做 callback 修改（更适合 patch 应用）。citeturn14search1turn14search11  

审计日志建议至少包含：thread_id、note_id/path、proposal JSON、decision（approve/reject）、applied_patch、hash_before/after、耗时、模型与版本、召回的 chunk_ids。

### 可观测性与 Eval

#### Tracing 指标体系（你要能“拿数据说话”）

两周内建议实现两层观测：

1) **LangSmith（可选但强加分）**：官方文档明确 LangSmith 与 LangGraph（Python/JS）可无缝集成，用于 tracing。citeturn0search1turn0search9  
2) **本地 JSONL trace（必做）**：每次 run 输出一条 trace（graph_start → node_enter/exit → graph_end），包含节点耗时、token、检索条目、写回动作。

你可以参考 ObsidianRAG `qa_agent.py` 中的 GraphTracer 思路：记录节点 enter/exit、耗时与事件，并打印执行摘要；这非常适合你两周内快速补齐“自研 tracing”。citeturn11view0

#### Golden set 设计（最小但有效）

建议至少 50–100 条样本，按三类分层：问答兜底（30%）、治理建议（40%）、复盘生成（30%）。样本结构建议包含：

- `user_input`  
- `reference`（参考答案/参考产物：比如应生成哪些 tags/links/summary）  
- `reference_context_ids`（可选：你手标的关键 chunk_id 集合，用于 IDBasedContextRecall）citeturn17search0  
- `risk_level`（写回类为 high）  
- `expected_action_type`

指标建议：

- 检索：Context Recall / Context Precision（Ragas）。citeturn17search0turn17search2  
- 生成：Faithfulness、Answer Relevancy。citeturn17search1turn0search14  

### 工程实现计划（两周冲刺日程表、风险与应对）

#### 两周冲刺日程表（以 10 个工作日拆分）

假设从你开始动手算起 10 个工作日（两周），给出“每天必须有可演示增量”的节奏。

| Day | 里程碑产物 | 当日任务 | 风险点与兜底 |
|---|---|---|---|
| D1 | 跑通基线（插件+后端） | fork ObsidianRAG；按 README 启动后端/插件；确认 SSE 流式与索引生成 | 环境坑：Ollama/依赖；兜底：先 CLI ask 跑通citeturn7view0turn12view0 |
| D2 | 新增“治理入口命令” | 插件增加命令：对当前笔记执行 steward；后端新增 `/ingest` | API 设计不稳：先写 mock 返回 |
| D3 | 建立索引 schema | SQLite notes/chunks/audit 表；实现增量索引状态（mtime） | 数据迁移：先 drop&rebuild |
| D4 | Chunking v1 | 按 frontmatter/heading/代码块/表格分块；写入向量库+FTS | 解析 bug：保留原文 fallback |
| D5 | Hybrid retrieve v1 | BM25 + vector 并行召回；融合（权重/rrf）；输出来源与分数 | BM25 实现慢：先用 SQLite FTS5 |
| D6 | Rerank 接入（可降级） | 接入 bge-reranker（可选开关）；失败则跳过 | 模型太慢：限制 top_n=6 citeturn1search3turn7view0 |
| D7 | LangGraph ingest workflow | route→load_note→retrieve→analyze→propose；接入 checkpointer（sqlite） | checkpointer 兼容：优先用 langgraph-checkpoint-sqliteciteturn2search0turn0search0 |
| D8 | HITL + diff 预览 | interrupt 卡点；插件展示 proposal/diff；approve→apply | 写回风险：先只写草稿文件；再写正文 |
| D9 | 复盘 workflow | collect_recent→cluster→plan→HITL→write_digest | 聚类难：先规则分组（tag/文件夹/时间） |
| D10 | Eval+Tracing+Demo脚本 | golden set（≥50）；Ragas 指标跑通；录屏脚本/README | 指标跑不通：先只做检索指标，再补生成指标 |

### 风险清单与缓解措施

| 风险 | 触发条件 | 后果 | 缓解策略 |
|---|---|---|---|
| 索引耗时过长 | vault 很大（>10k 文件） | 初次体验差 | 分页/分批索引；增量索引；界面显示进度（SSE status）citeturn7view0 |
| reranker 太慢 | 无 GPU、cross-encoder 推理慢 | 延迟爆炸 | 限制 rerank top_n；可配置关闭；失败跳过citeturn1search3turn7view0 |
| 写回误伤 | patch 生成错误或并发改动 | 用户数据损坏（致命） | 强制 HITL；写回前后 hash；优先写草稿；Frontmatter 用 processFrontMatter 原子改写citeturn0search12turn14search0turn14search13 |
| interrupt 恢复语义踩坑 | interrupt 节点放在中间且有副作用 | 恢复时重复执行副作用 | 按文档建议把 interrupt 放在节点开头或独立节点；副作用写回放在 interrupt 之后citeturn0search12 |
| GitHub 拉取/依赖问题 | 国内网络/限流 | 无法复现 | 使用 PyPI 安装后端包；或使用镜像；保留 vendor 方案（requirements lock）citeturn5search3turn2search0 |
| Eval 设计虚 | golden set 太少或不真实 | 面试被质疑“自嗨” | 用真实笔记抽样；分场景；用 Ragas 指标做回归并在 README 展示趋势citeturn17search1turn17search2turn17search0 |

### 简历/面试讲述要点与“血泪史”复盘模板

#### 面试叙事主线（建议背熟）

你应把项目讲成：**“把一个不可控的 LLM 工具，钉进一个可控的知识治理工作流”**。关键关键词必须出现：DAG/状态机、checkpoints、interrupt/HITL、审计日志、混合检索+rerank、可观测+评估闭环、降级策略。

可直接用这个“可复述结构”：

1) **问题定义**：Obsidian 笔记随着时间推移结构腐化，真正痛点不是问答，而是治理（重复/冲突/孤立/开放环/复盘）。  
2) **系统拆解**：将治理拆成 ingest→retrieve→analyze→propose→HITL→writeback→audit 的 SOP。  
3) **LangGraph 价值**：用 checkpointer 持久化每一步状态（thread_id），用 interrupt 实现暂停审查与恢复；这比黑盒 ReAct 更可控。citeturn0search0turn0search12  
4) **检索深水区**：混合检索 + rerank；同时利用 Obsidian 的链接结构做 GraphRAG 扩展上下文；引用来源可点击。citeturn6view0turn1search3turn13search0  
5) **安全与审计**：写回前必须人工审批；frontmatter 用原子方法改写；每次写回记录 before/after hash 与 proposal。citeturn14search0turn14search1  
6) **评估闭环**：golden set + Ragas 指标（Faithfulness/Context Recall/Precision 等）做回归。citeturn17search1turn17search0turn17search2  

#### “血泪史”复盘模板（你要在 README/面试里讲得出来）

你可以按以下结构写 3–5 个真实坑（每个坑 5–10 行），非常加分：

- 现象：XXX（例：reranker 开启后 P95 从 6s 变 25s）  
- 初始假设：我以为是模型慢 / 网络慢  
- 定位方法：用 tracing 看节点耗时；发现瓶颈在 rerank top_k=30  
- 解决策略：限制 top_n=6、可配置开关、无 GPU 自动降级  
- 结果：P95 降回 8s，Context Precision 提升 0.12  
- 教训：cross-encoder 必须受控；“质量-延迟”要用数据权衡  
（reranker 的定位与价值可引用 FlagEmbedding 对 reranker 的建议；tracing 可引用 LangSmith-LangGraph 集成。）citeturn1search3turn0search1  

### 推荐可复用开源仓库与应参考/ fork 的模块

你要求“按优先级列表，给出关键理由与需改动点”，这里给出直接可执行的建议。

| 优先级 | 仓库 | 为什么值得用 | 建议 fork/参考的具体模块 | 你必须做的关键改动 |
|---|---|---|---|---|
| P0 | Vasallo94/ObsidianRAG | 已有“插件+Python后端+LangGraph+混合检索+rerank+GraphRAG+SSE”，两周复现最快；配置中暴露混合权重、reranker 模型等；并且后端提供 `/ask/stream` 与状态事件。citeturn6view0turn7view0turn12view0turn11view0 | `backend/obsidianrag/core/qa_agent.py`（LangGraph 图、检索与 GraphRAG 思路）；`backend/obsidianrag/core/*`；`plugin/src`（SSE UI 与后端管理）citeturn9view0turn12view0turn11view0 | 从“问答”升级到“治理”：新增 ingest/digest 工作流、HITL、写回 patch、审计与 Eval；把治理作为主入口 |
| P1 | cbelling/obsidian-agent | 工程韧性特性齐全：LangGraph checkpoint 持久对话、缓存、指数退避重试、限流、优雅降级、LangSmith 可选、测试覆盖等；目录结构清晰。citeturn3view0turn15view0 | `src/checkpoint`、`src/vault`、`src/state`、`src/utils`（缓存/错误/工具封装）；`ChatView.ts`（UI 组织）citeturn15view0turn3view0 | 把“聊天中心”改成“工作流中心”：UI 增加 Proposal/Diff 面板；工具从“搜索读文件”升级为“生成治理提案+审批写回” |
| P1 | langchain-ai/langgraph-example | 官方示例强调：一键启动生产级 HTTP microservice、内置持久化；适合你讲“生产化接口 + 内置 checkpoint”。citeturn16view0 | `my_agent/`、`langgraph.json`、服务化接口组织 | 用其借鉴 API 形态，但不必完全迁移到 Cloud |
| P1 | obsidianmd/obsidian-sample-plugin | 高星 Obsidian 插件模板（约 4k stars），提供基础开发/构建/设置页/发布流程范式，适合你快速扩展插件 UI。citeturn4view0 | `src/`（命令、设置页、modal/view） | 用它规范你的插件工程（lint/build），并融入你的 Side Panel 与命令入口 |
| P1 | obsidianmd/obsidian-api + 官方 TS API 文档 | 提供 Vault/MetadataCache/FileManager 等正式 API 定义与文档，是你写回/读取/元数据引用的权威依据。citeturn1search1turn14search0turn14search15turn13search2 | `Vault.read/modify/process`、`FileManager.processFrontMatter`、`MetadataCache.getFileCache/unresolvedLinks`citeturn14search15turn14search1turn14search0turn13search2 | 把写回全部基于官方 API，避免“读写文件系统路径”的不稳定性 |
| P2 | FlagEmbedding | 官方建议 bge-reranker 用于重排 top-k，提升相关性，是你“检索深水区”的关键拼图。citeturn1search3 | reranker 接入与模型选择 | 做成可配置、可关闭、可降级，否则延迟会毁掉体验 |

### 主要参考链接（便于你写 README “References”）

以下均为官方文档/仓库或其权威镜像，建议你在项目 README 中以“References”列出（本报告用引文形式呈现）：

- LangGraph 持久化（checkpoints/threads/StateSnapshot）citeturn0search0  
- LangGraph 人类在环（interrupt/Command/resume，且需 checkpointer）citeturn0search12  
- LangGraph 节点重试 RetryPolicyciteturn0search11  
- LangSmith 追踪 LangGraph（Python/JS）citeturn0search1turn0search9  
- Ragas 指标：Faithfulness / Context Recall / Context Precision / Answer Relevancyciteturn17search1turn17search0turn17search2turn0search14  
- Obsidian 内部链接语法（含标题/块链接）citeturn13search0  
- Obsidian TS API：Vault/MetadataCache/FileManager.processFrontMatterciteturn14search11turn14search0turn13search2  
- ObsidianRAG（LangGraph + Hybrid + rerank + GraphRAG + SSE）citeturn6view0turn7view0turn11view0turn12view0  

## 关键节点代码片段示例（Python/asyncio + LangGraph 伪代码）

下面给出你要求的 4 类关键节点（retrieve、rerank、human_approval、write_back）的可执行风格伪代码。注意：代码结构是“可落地”的，但你需要按实际库（Chroma/SQLite/FlagEmbedding/HTTP client）补齐细节。

### retrieve 节点（混合检索 + metadata filter + 融合）

```python
import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

@dataclass
class RetrievedChunk:
    chunk_id: str
    note_path: str
    text: str
    score: float
    source: str            # "bm25" | "vector" | "fused"
    metadata: Dict[str, Any]

def rrf_fuse(
    bm25: List[RetrievedChunk],
    vec: List[RetrievedChunk],
    k: int = 60,
    weight_bm25: float = 0.4,
    weight_vec: float = 0.6,
    top_n: int = 12,
) -> List[RetrievedChunk]:
    """Reciprocal Rank Fusion-ish: 用排名融合，适合两周内实现且稳定。"""
    rank: Dict[str, float] = {}
    meta: Dict[str, RetrievedChunk] = {}

    for i, c in enumerate(bm25):
        rank[c.chunk_id] = rank.get(c.chunk_id, 0.0) + weight_bm25 * (1.0 / (k + i + 1))
        meta[c.chunk_id] = c

    for i, c in enumerate(vec):
        rank[c.chunk_id] = rank.get(c.chunk_id, 0.0) + weight_vec * (1.0 / (k + i + 1))
        meta.setdefault(c.chunk_id, c)

    fused = sorted(rank.items(), key=lambda x: x[1], reverse=True)[:top_n]
    out = []
    for cid, s in fused:
        c = meta[cid]
        out.append(RetrievedChunk(
            chunk_id=cid,
            note_path=c.note_path,
            text=c.text,
            score=float(s),
            source="fused",
            metadata={**c.metadata, "fused_score": float(s)},
        ))
    return out

async def retrieve_hybrid(
    query: str,
    filters: Dict[str, Any],
    bm25_store,
    vector_store,
    topk_bm25: int = 20,
    topk_vec: int = 20,
) -> List[RetrievedChunk]:
    # 并行召回
    bm25_task = asyncio.to_thread(bm25_store.search, query, filters, topk_bm25)
    vec_task = asyncio.to_thread(vector_store.search, query, filters, topk_vec)
    bm25_res, vec_res = await asyncio.gather(bm25_task, vec_task)

    # bm25_res / vec_res: List[RetrievedChunk]
    fused = rrf_fuse(bm25_res, vec_res)
    return fused
```

（混合检索作为“向量 + BM25 并行 + 融合”的思想与可配置权重，在 Weaviate 文档中有明确描述；你可以引用它证明你不是拍脑袋。citeturn13search3turn13search7）

### rerank 节点（cross-encoder 精排，可降级）

```python
from typing import Callable

async def rerank_cross_encoder(
    query: str,
    chunks: List[RetrievedChunk],
    reranker: Optional[Callable[[str, str], float]],
    top_n: int = 6
) -> List[RetrievedChunk]:
    """
    reranker(query, doc_text)->score
    如果 reranker 不可用（无 GPU/模型缺失），直接返回原排序。
    """
    if reranker is None:
        return chunks

    cand = chunks[:max(top_n, len(chunks))]
    # 并行打分（注意：真实 cross-encoder 往往应 batch）
    async def score_one(c: RetrievedChunk) -> Tuple[str, float]:
        s = await asyncio.to_thread(reranker, query, c.text)
        return (c.chunk_id, float(s))

    scores = await asyncio.gather(*[score_one(c) for c in cand])
    score_map = dict(scores)

    out = []
    for c in cand:
        out.append(RetrievedChunk(
            **{**c.__dict__, "score": score_map.get(c.chunk_id, c.score)},
        ))
    out.sort(key=lambda x: x.score, reverse=True)
    return out
```

（为何要做 rerank：FlagEmbedding 明确建议用 bge-reranker 这类 cross-encoder 对 embedding 检索的 top-k 文档重排，提升相关性；你应在 README/面试中引用此依据。citeturn1search3）

### human_approval 节点（interrupt + resume）

```python
from typing import Literal, TypedDict
from langgraph.types import interrupt, Command

class StewardState(TypedDict, total=False):
    thread_id: str
    proposal: dict
    approval: dict
    next_step: str

def human_approval_node(state: StewardState) -> Command[Literal["apply_patch", "archive_proposal"]]:
    """
    高风险操作：写回前必须人工审批。
    interrupt() 会让图返回 __interrupt__，等待外部用 Command(resume=...) 恢复。
    """
    proposal = state["proposal"]

    decision = interrupt({
        "type": "WRITEBACK_APPROVAL",
        "proposal": proposal,
        "instructions": "请审查变更：Approve/Reject 或编辑后继续。",
    })

    # decision 由 UI/外部恢复时提供
    if decision.get("approved") is True:
        return Command(
            goto="apply_patch",
            update={"approval": decision, "next_step": "apply_patch"},
        )
    return Command(
        goto="archive_proposal",
        update={"approval": decision, "next_step": "archive_proposal"},
    )
```

（interrupt 的注意事项：LangGraph 文档强调使用 interrupt 需要指定 checkpointer；并提示恢复不会“从中断点继续执行该节点中断之后的那一行”，而是重新运行使用 interrupt 的整个节点，因此通常应把 interrupt 放在节点开头或专用节点。citeturn0search12turn0search0）

### write_back 节点（生成 patch + 插件侧执行写回）

两周内强烈建议：后端**只生成 patch**，不直接改 vault；写回由插件用 Obsidian 官方 API 执行（更安全、更可控、更贴合 HITL）。

```python
import hashlib
from typing import List, Dict, Any, TypedDict

class PatchOp(TypedDict):
    op: str               # "frontmatter_set" | "insert_text" | "replace_range" | "append_block"
    target_path: str
    payload: Dict[str, Any]

class WriteBackResult(TypedDict):
    patch: List[PatchOp]
    before_hash: str
    after_hash: str

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

async def build_writeback_patch(state, vault_reader) -> WriteBackResult:
    """
    vault_reader: 后端用于读取当前文件内容（或由插件传入）
    """
    path = state["proposal"]["target_note_path"]
    current = await vault_reader.read_text(path)
    before = sha256_text(current)

    patch: List[PatchOp] = state["proposal"]["patch_ops"]  # 结构化 patch
    # 注意：此处不应用 patch，只生成可审计计划
    # after_hash 可在插件执行后回传真实值；这里先占位
    return {"patch": patch, "before_hash": before, "after_hash": ""}
```

插件侧执行写回时，frontmatter 用 `FileManager.processFrontMatter()`，正文用 `Vault.modify()` 或 `Vault.process()`；这些能力在 Obsidian 官方 TS API 文档中明确给出。citeturn14search0turn14search1turn14search11turn14search15

（可选补强：把 `before_hash` 与插件执行后的 `after_hash` 一并写入 audit_log，形成“可证明”的写回链路。）

---

以上实现指南刻意把“Obsidian 方向”从“问答玩具”拔高成“可控的知识治理系统”，并用 LangGraph 的持久化、interrupt/HITL、重试策略，以及 Ragas 的评估指标与 LangSmith tracing 形成工业级闭环。其核心价值在于：你可以在两周内交付一个可复现、可演示、可讲清楚“为什么这样设计”的项目，而不是一个“API 拼图聊天框”。