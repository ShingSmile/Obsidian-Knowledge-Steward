# INTERVIEW_PLAYBOOK

本文件承载项目的面试问答库与面试口径。

稳定架构、模块边界、ADR 与长期风险继续以 [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 为准。
当前动态状态、默认下一任务与最近完成，请先读 [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md)。

## 0. 面试输出角色设定

当输出任何与“面试相关”的内容时，默认切换到以下角色视角：

- 角色身份：就职于中国国内头部互联网大厂的资深大模型应用开发工程师兼高级面试官。
- 能力边界：熟悉 Prompt Engineering、RAG、Agent、LangChain、模型微调、部署与调用等应用层原理及工程落地痛点。
- 提问风格：一针见血、层层递进，优先深挖设计原因、替代方案、输入输出边界、极端失败场景、降级审计恢复和效果证明。

面试相关输出必须遵守以下要求：

1. 不要温和泛泛，不要只给概念定义。
2. 优先从工程落地、失败模式、边界条件、性能、稳定性、成本、可观测性、评估闭环等角度发问和分析。
3. 问题必须有层次：先验证候选人是否真的做过，再验证其是否理解原理，最后追问极端情况和 trade-off。
4. 回答建议不能只停留在“能说”，还要指出哪些回答会显得像没做过项目。
5. 如果发现项目描述中有玩具感、包装感、逻辑断层、评估缺失、系统边界模糊，要直接指出，不要美化。

默认深挖问题包括：

- 为什么这么设计。
- 为什么不选其他方案。
- 输入输出边界在哪里。
- 最容易失败的极端场景是什么。
- 如何做降级、审计与恢复。
- 如何证明这个方案真的有效。
- 如果线上出现脏数据、长尾 case、模型不稳定、上下文召回错误、工具调用失败，会发生什么。
- 如果这个项目拿到面试现场，最可能继续往哪里深挖。

## 1. 场景选择（5 题）

| 问题 | 回答思路 | 关键术语 | 最好举的例子 | 容易说错的点 |
| --- | --- | --- | --- | --- |
| 为什么选 Obsidian，而不是做通用 RAG | 强调知识治理的高频痛点：重复、冲突、孤立、复盘 | knowledge governance、Vault、wikilink | 新笔记写完后难以再被发现 | 不要把重点说成“因为我常用 Obsidian” |
| 这个项目解决的核心问题是什么 | 不是聊天，是持续治理个人知识资产 | lifecycle、governance、review loop | 一篇课程笔记写完后要补标签、回链和行动项 | 不要泛泛说“提升学习效率” |
| 为什么这不是普通 AI 助手 | 有状态工作流、审批写回、审计和 eval 才是核心 | stateful workflow、HITL、audit | 复盘工作流不是一个 prompt 就能替代 | 不要回到“它也能聊天” |
| 为什么这个场景适合面试 | 它需要架构、边界、评估和安全控制，不是 API 拼装 | architecture、trade-off、observability | 写回审批和中断恢复 | 不要只讲产品想法，不讲工程点 |
| 为什么要强调知识治理而不是问答 | 问答很容易同质化，治理才能体现系统设计价值 | governance vs QA | 自动发现孤立笔记并建议链接 | 不要贬低问答，而是说它是兜底链路 |

## 2. LangGraph / 工作流（8 题）

| 问题 | 回答思路 | 关键术语 | 最好举的例子 | 容易说错的点 |
| --- | --- | --- | --- | --- |
| 为什么这里必须用 LangGraph | 因为有审批、中断恢复、状态持久化和多入口工作流 | checkpoint、thread_id、interrupt | ingest workflow 在审批处暂停，再恢复写回 | 不要只说“因为它火” |
| 你说统一 workflow contract，到底统一了什么，为什么这不是简单抽 helper | 先把抽象边界说清：统一的是 ask / ingest / digest 的入口路由、shared execution contract、base workflow state、runtime trace hook 组装与响应装配，不是把三条业务 graph 硬揉成一个巨图；核心收益是新增 workflow 时不再复制 API / trace / checkpoint 样板 | workflow runtime、handler registry、shared execution contract、base state | `backend/app/main.py` 的 handler registry + `backend/app/graphs/runtime.py` 的 `WorkflowGraphExecution` | 不要回答成“代码更优雅了”或“就是把三个 if 抽出来”，这会显得没做过平台化收口 |
| 为什么当前没有继续把 `TASK-031` 到 `TASK-033` 排进第一批主线 | 要把“问题真实存在”和“当前必须先做”分开讲：这三项都是真缺口，但当前 interview-first 收口先看剩余 P0 是否闭合，以及哪三个 P1 最能提升质量闭环、恢复能力和系统设计叙事；如果 P0 还没收口就继续插更多优化，路线会再次发散 | scope control、P0 closure、priority reset | 先补 `writeback -> reindex`、hybrid retrieval、eval baseline，再回头做跨会话恢复 / 增量 FTS / runtime groundedness gate | 不要说成“这些不重要”或“以后再说”，要明确它们为什么被后移而不是被否定 |
| 为什么不是简单函数链 | 函数链难处理中断恢复和副作用幂等 | state machine、idempotency | 审批后恢复不能重复写回 | 不要把函数链说得一无是处，要说它不匹配需求 |
| 你怎么设计 state schema | 把持久化字段和临时字段分开，先服务审计和恢复 | persistent state、transient state | proposal / approval / writeback_result | 不要把所有大文本都塞进 state |
| interrupt 放在哪里最合适 | 放在独立审批节点，避免恢复时重复执行副作用 | pure control node | human_approval 独立于 apply_writeback | 不要把 interrupt 混在有写回的节点中 |
| 如何避免恢复执行的重复副作用 | proposal_id、before_hash、writeback_applied、审计校验 | idempotency key、resume protocol | 恢复前先查 patch 是否已应用 | 不要回答“重试就好了” |
| 你现在的 checkpoint 到底是节点级续跑还是线程级状态短路 | 先把当前恢复边界讲清：现在是 `thread_id + graph_name` 的 SQLite 快照恢复，completed checkpoint 直接短路返回，线性 graph 才支持按 `next_node_name` 继续；这满足最小恢复，但还不是完整 interrupt 平台 | workflow_checkpoint、thread-level resume、next_node_name | ask 命中 completed checkpoint 不再重复打模型，ingest 命中 completed checkpoint 不再重跑整库 | 不要把结果缓存包装成“任何节点都能无损续跑” |

## 3. 检索与索引（5 题）

| 问题 | 回答思路 | 关键术语 | 最好举的例子 | 容易说错的点 |
| --- | --- | --- | --- | --- |
| 为什么用 hybrid retrieval | Obsidian 语料同时需要关键词精确匹配和语义召回 | BM25、vector、fusion | 标题精确命中 + 正文语义相似 | 不要说成“行业都这么做” |
| 为什么 chunk 不能按 token 切 | 需要和 heading、frontmatter、回写位置对齐 | structural chunking、heading_path | 在 `Summary` 标题下插入链接建议 | 不要忽略写回定位需求 |
| metadata schema 为什么重要 | 检索过滤、治理规则和审计都依赖结构化字段 | tags、aliases、mtime、hash | 找最近一周无链接的概念笔记 | 不要把 metadata 只当展示字段 |
| rerank 的价值在哪里 | 提升前排质量，减少无关结果污染生成和 proposal | cross-encoder、top-k precision | 两条都相关时把真正核心 chunk 放前面 | 不要夸大 rerank，忽略延迟代价 |
| 如何处理 unresolved links | 既是检索信号，也是治理机会 | unresolved link、orphan detection | 当前笔记链接到了不存在的 note | 不要把它当纯错误噪音 |

## 4. HITL / 写回（9 题）

| 问题 | 回答思路 | 关键术语 | 最好举的例子 | 容易说错的点 |
| --- | --- | --- | --- | --- |
| 为什么写回必须审批 | 风险最大，必须在人类认可后执行 | high-risk action、approval gate | frontmatter 补标签和正文插链 | 不要回答“为了保险一点”这么弱 |
| 为什么 patch 要结构化 | 便于校验、diff、回滚和审计 | patch op、schema validation | `insert_under_heading`、`merge_frontmatter` | 不要让 patch 变成自由文本 |
| 为什么 proposal / audit 不能只挂在 checkpoint 里 | checkpoint 是恢复快照，不是业务事实主存储；proposal / audit 还要服务幂等查询、审批回放和写回审计 | source of truth、business store、append-only audit | proposal 生成后等待审批，恢复前先查 `proposal_id` 和 `writeback_applied` | 不要把 checkpoint 包装成万能数据库 |
| 为什么 resume 请求必须同时带 `thread_id` 和 `proposal_id` | `thread_id` 只能告诉你“这是哪条 workflow 事务”，但不能保证当前等待审批的就是哪一份 proposal；必须同时命中两层主键，才能避免把审批决策打到错误 proposal | workflow identity、business identity、resume control plane | 用户重复打开旧面板后重新点击 approve | 不要回答“带两个字段就是更安全”这么空，要说清 source of truth 和误命中风险 |
| 为什么插件执行写回而不是后端 | 插件更接近 Obsidian API 和用户交互边界 | execution boundary、Vault API | 审批后调用 `applyPatch` | 不要只说“实现方便” |
| 如何降低误删风险 | 默认只追加、不删用户原文，校验 before_hash | safe writeback、hash guard | 系统托管块替换而非整篇重写 | 不要承诺“绝不会错” |
| 如果用户拒绝 proposal 怎么办 | 记录拒绝原因、保留草稿、不写回 | rejection handling、audit | 用户觉得标签建议过度 | 不要把 reject 当异常 |
| 为什么同一审批决策的重复提交不能重复写审计 | 重放是分布式和前端超时里的常态；如果控制面阶段都不做幂等，后续真实写回时会直接放大成重复副作用 | idempotency、retry safety、append-only audit | 前端点了一次 approve 但请求超时又重发一次 | 不要回答“重复提交概率很低”，这会显得你没做过线上系统 |
| 如果插件本地写回成功了，但 `/workflows/resume` 记账失败怎么办 | 必须直说当前只做了“同一面板内允许重试 approve、避免重复落盘”的最小保护，控制面和副作用面还没有跨会话补偿；后续要补待同步入口或恢复任务，否则审计事实会落后于文件事实 | side-effect plane、control plane、reconciliation | Obsidian 已写进 frontmatter，但后端因网络抖动没记下 `writeback_result` | 不要把现在的内存态保护包装成完整恢复系统，这会显得你没有正视故障边界 |

## 5. 评估与 tracing（6 题）

| 问题 | 回答思路 | 关键术语 | 最好举的例子 | 容易说错的点 |
| --- | --- | --- | --- | --- |
| 为什么 tracing 是 P0，而不是锦上添花 | 没有 tracing，就无法解释延迟和失败来源 | node latency、token usage、evidence trail | rerank 让 P95 激增时的定位 | 不要只说“方便调试” |
| 为什么这次没有再单独新增一个 tracing P0 任务 | 关键不是否认 tracing，而是说明“基础 tracing 已达 interview-first 下限”：当前 ask / ingest / digest 已有节点级 JSONL + SQLite `run_trace`、错误落盘和检索上下文回溯；此时继续新建 tracing P0 只会抢占真正未闭合的 retrieval / eval 主线 | sufficiency threshold、observability baseline、scope control | 先把 hybrid retrieval 和 eval baseline 补齐，再决定是否继续做 LangSmith / dashboard | 不要回答“现在差不多够了”，这会显得你没有量化达线标准 |
| golden set 怎么构建 | 从真实样本抽样，按问答/治理/复盘分层 | golden dataset、scenario split | 30 条最小样本起步 | 不要一上来吹 1000 条样本 |
| 为什么 golden set 要混用真实 `sample_vault` 和 deterministic fixture | 真实样本负责检验系统没有脱离业务语料，fixture 负责稳定覆盖 citation 越界、empty index 这类高风险 bad case；只用一边都会失真 | corpus drift、deterministic bad case、regression stability | `sample_vault` 跑 retrieval fallback，fixture 跑 invalid citation downgrade | 不要回答成“只是为了写测试方便”，这会显得你没理解评估噪声和可复现性的 trade-off |
| 为什么 `TASK-039` 先做本地等价指标，而不是直接接 Ragas 或 LLM judge | 先讲约束：这轮目标是把 baseline 变成稳定可回归资产；再讲 trade-off：在线 judge 会把外部依赖、成本和波动引进主回归，反而削弱可重复性；最后讲路线：先用本地 `faithfulness / relevancy / context` 等价指标把 schema 与 case 覆盖立住，再在 `TASK-040` 里讨论是否值得引入更强 judge 做补充 | deterministic eval、judge variance、baseline contract | governance waiting proposal 和 hybrid ask 都先输出本地 `quality_metrics`，而不是每次联网问一个 judge | 不要回答成“以后再接就行”或“Ragas 太麻烦”，要明确说清为什么 baseline 优先级高于 judge 炫技 |
| 为什么 `TASK-040` 先切“问答 vs 治理”两套 benchmark，而不是直接做四套独立报告 | 先讲目标：这轮要服务 interview-first 叙事，优先回答“哪条主链路更稳、主要坏在哪”；再讲边界：`ask / governance / digest / resume_workflow` 仍保留在 `scenario_overview` 下，不是被抹平；最后讲 trade-off：如果一上来就做四套独立报告、markdown 导出和 dashboard，会把会话扩成评测平台而不是 benchmark 收口 | benchmark layering、scenario_overview、scope control | `question_answering` 负责讲引用与 groundedness 边界，`governance` 负责讲 proposal / digest / resume-writeback 的副作用与恢复边界 | 不要回答成“我觉得这样更好看”或“先随便分一下”，要明确说清分组是为决策服务，不是为了包装结果 |
| proposal 怎么评估 | 自动评 schema 和写回成功率，人工评合理性 | schema validity、approval rate | 标签建议命中率 | 不要只用主观体验 |
| 为什么审计日志和运行日志要分开 | 一个看过程，一个看副作用责任 | runtime log、audit log | 写回谁批准、改了什么 | 不要混为一个大 JSON |
| 指标变差你怎么排查 | 先看索引和检索，再看 rerank，再看 prompt | evidence-first debugging | recall 掉了先看 chunking | 不要第一反应怪模型 |

## 6. 成本 / 延迟 / 稳定性（5 题）

| 问题 | 回答思路 | 关键术语 | 最好举的例子 | 容易说错的点 |
| --- | --- | --- | --- | --- |
| 你怎么控制延迟 | 限制 top-k、可关闭 rerank、区分场景路由 | latency budget、feature flag | 问答链路默认关 rerank | 不要只说“加机器” |
| 你怎么控制成本 | 云模型首版按场景分层使用，并保留本地 fallback 和缓存空间 | model routing、cloud-primary、fallback | digest 用便宜云模型，proposal 用更稳模型，本地模型留作兜底基线 | 不要把“云优先”说成“成本不重要” |
| 如果模型波动很大怎么办 | 约束输出 schema、加 fallback、版本化 prompt | prompt versioning、fallback | proposal JSON 校验失败时降级 | 不要假设模型始终稳定 |
| 如何保证系统稳定性 | 从幂等、日志、健康检查和小步回滚入手 | health check、idempotency、retry policy | `/health` + 审计校验 | 不要只讲 try/except |
| 为什么不是一开始就做极致性能优化 | 当前瓶颈还未知，先打通闭环再用 tracing 找真瓶颈 | premature optimization | 先保正确性再调快 | 不要显得忽视性能 |

## 7. 技术选型取舍（5 题）

| 问题 | 回答思路 | 关键术语 | 最好举的例子 | 容易说错的点 |
| --- | --- | --- | --- | --- |
| 为什么后端选 Python | LangGraph、评估和数据处理生态更成熟 | FastAPI、LangGraph、offline eval | `run_eval.py` 和 graph 共用数据模型 | 不要只说“我更熟悉” |
| 为什么不是纯 TypeScript 全栈 | 可以做，但两周内 Python 对 graph 与 eval 更高效 | engineering trade-off | 插件 TS，后端 Python 职责清晰 | 不要说 TS 做不到 |
| 为什么用 SQLite | 本地优先、低依赖、好分发 | SQLite、FTS5、single-file DB | audit_log 和 note/chunk 表 | 不要忽视它的扩展性限制 |
| 为什么不是纯云托管服务 | 本地后端 + 云模型调用是边界更清晰的折中，既保留隐私和写回控制，也保留首版模型质量 | local backend、cloud model、privacy boundary | 索引和写回留本地，LLM 调用可走云 provider | 不要把“用云模型”说成“系统已经云化” |
| 为什么不做多 agent | 首版重点是确定性工作流和闭环，不是展示 agent 数量 | controlled workflow、scope control | 先把 ingest graph 打稳 | 不要显得害怕复杂性，要讲优先级 |

## 8. 本次代码改动新增追问点（12 题）

| 问题 | 回答思路 | 关键术语 | 最好举的例子 | 容易说错的点 |
| --- | --- | --- | --- | --- |
| 为什么现在选云优先，而不是一开始就本地优先 | 当前目标是尽快跑通可演示链路，云模型能减少本地调参与安装摩擦，本地保留为 fallback 和基线 | cloud-primary、local-compatible、delivery speed | 先用云模型打通 `ask`，后续在 M 系列 Mac 上补本地兜底 | 不要把这个决策说成“本地模型不重要” |
| 为什么不是让后端直接变成纯云服务 | 本地后端仍然掌握索引、协议、审计和写回边界，云只负责模型能力 | local backend、execution boundary、audit | `/health` 和未来 patch 执行都在本地边界内 | 不要混淆“云模型调用”和“云托管系统” |
| 为什么要参考 `ObsidianRAG`，但不直接 fork | 参考实现能加速验证通信和检索形态，但它是 chat-first，不符合治理优先和 HITL 写回主线 | reference repo、chat-first、workflow-first | 借鉴 `/ask/stream` 和插件探活，但不继承它的整体叙事 | 不要说成“别人代码不行”，重点是边界不匹配 |
| 为什么 `/health` 要返回 `sample_vault` 统计 | 这不是普通探活，而是最小 contract test，证明后端确实看到了真实语料并能做基础解析 | contract test、sample awareness、health semantics | 返回 205 篇笔记和模板分布，比单纯 `ok` 更能暴露问题 | 不要把 `/health` 做成重型业务接口 |
| 为什么在没有 frontmatter 的情况下先做模板推断 | 当前样本几乎没有 YAML，若等待结构化元数据齐全再开始，索引和复盘会被卡死；模板推断只是首版弱信号，不是唯一真相 | weak signal、template inference、generic fallback | `Task Planner / Summary` 和中文日记模板先帮助分流 daily note | 不要把模板推断讲成长期唯一方案 |
| 为什么 ask 先接在 `/workflows/invoke`，而不是直接新开 `/ask` | 这条决策的核心是先稳定统一 workflow contract，再逐步把 ask graph、trace 和恢复语义接进同一入口；`TASK-042` 已证明这条收口路线成立，如果一开始就拆第二套路由，协议更容易漂移 | scope control、contract-first、workflow entry | `ask_qa` 先走 `/workflows/invoke`，随后已在 `TASK-009` 中升级为 `ask_graph`，并在 `TASK-042` 中与 ingest / digest 共用同一入口控制面 | 不要回答成“懒得开新接口” |
| 为什么要把 retrieval fallback 和 model fallback 分开 | 两者代表完全不同的失败面：一个是召回条件过严，一个是模型能力不可用；如果混成一个字段，排障和用户认知都会失真 | fallback taxonomy、observability、trust boundary | filter 过严时 `retrieval_fallback_used=true`，无 provider 时 `model_fallback_used=true` | 不要把所有降级都说成“低置信” |
| 为什么这次先把语义级 groundedness 做在离线 eval，而不是直接接入线上拦截 | 先讲目标：本轮要先把“编号合法但语义越界”的 bad case 稳定暴露出来；再讲 trade-off：rule-based semantic bucket 还可能误报 / 漏报，如果直接接线上会污染用户答案体验；最后讲现状边界：现在已能在 `eval/run_eval.py` 里把 `unsupported_claim` 分桶出来，但 ask runtime 仍只基于 citation alignment 做保守兜底 | eval-first、runtime trust boundary、semantic grounding | deterministic fixture 中 answer 带合法 `[2]`，但 claim 出现“自动写回知识库”时会在离线结果中落成 `unsupported_claim` | 不要把“离线已能识别”包装成“线上已经 fully gated”，这会显得你没有理解误判成本和质量门控节奏 |
| 为什么要把 ask trace 同时写 JSONL 和 SQLite `run_trace` | 两者解决的是两个不同问题：JSONL 负责原始事件留存和人工抽样，SQLite 负责按 `run_id` / `thread_id` 的结构化查询；首版双写是为了补齐“可留存 + 可查询”，但不是最终最佳形态 | dual-write、local observability、queryability | `ask_runtime.jsonl` 用于看原始事件，`run_trace` 用于按一次 ask 查询三条节点记录 | 不要回答成“两个都写比较保险” |
| 为什么 `DAILY_DIGEST` 首版先做模板化摘要，而不是直接接模型 | 当前要先证明 digest graph、fallback、checkpoint 和 `source_notes` contract 是稳定的；如果一开始就绑到外部模型可用性上，会把“摘要质量问题”和“workflow 边界问题”混在一起 | contract-first、deterministic fallback、workflow boundary | 先基于 SQLite `note` 表产出 digest，再决定后续是否在 `build_digest` 节点接模型 | 不要回答成“模型太贵，所以先不用”，这会显得你没有把可验证性和协议稳定性讲清楚 |
| 你现在的 digest `source_notes` 是怎么选的，误判会发生什么 | 先讲 current rule：优先 recent `daily_note / summary_note`，再退回 recent generic；再讲风险：`note_type` / `template_family` 误判会让 digest 来源漂移；最后讲后续：补时间窗口、过滤输入或更稳的候选选择器 | source selection、heuristic routing、fallback window | `summary_note` 没被识别时，digest 会退回 generic note，但会打 `fallback_reason` | 不要把启发式选择说成“已经很准”，一旦被追问脏数据就会露底 |
| 为什么 `TASK-035` 先用 SQLite FTS 做 retrieval-backed analyze，而不是等向量和 hybrid 都补完后再一次性做 | 先讲工程边界：当前目标是把 `INGEST_STEWARD` 从“只看当前 note”推进到“至少能引用旧笔记证据”，而不是顺手把 `TASK-037`/`TASK-038` 一并做掉；再讲复用价值：现有 FTS、metadata filter、chunk schema 已经稳定可测，先把 evidence contract、self-match 排除和冷索引 fallback 收敛出来，后续再替换召回底座；最后讲风险控制：如果现在直接把治理判断绑死在未落地的向量 / hybrid 路径上，失败时你分不清是 analyze 逻辑错还是 retrieval 底座没好 | scope control、evidence contract、cold-index fallback | 当前先输出 `analysis_result`、`retrieval_queries` 和 `related_candidates`，后续再让 hybrid 替换召回输入而不是重写 proposal 审批链路 | 不要回答成“因为 FTS 实现简单”，这会暴露你没有定义任务边界，也没有理解为什么 evidence contract 要先于 retrieval fancy 化收敛 |
| 为什么 `TASK-037` 先把向量持久化继续放在 SQLite，而不是直接上 Chroma / FAISS / Qdrant | 先讲 scope control：本轮目标是补最小向量底座，不是顺手引入第二套基础设施；再讲连续性：`chunk_embedding` 与现有 `note/chunk` 生命周期、scoped ingest replace 语义和本地部署边界天然一致；最后讲 trade-off：当前方案是 MVP，优点是简单可测，缺点是全量扫描 JSON embedding，不适合大 Vault，所以 `TASK-038` 之后仍要评估 ANN 或独立向量库 | scope control、lifecycle consistency、deployment boundary、MVP trade-off | `backend/app/indexing/store.py` 中的 `chunk_embedding` 与 `backend/app/retrieval/sqlite_vector.py` 的最小余弦检索 | 不要回答成“因为这样实现最省事”，这会显得你没有意识到性能债和存储边界是设计选择，而不是偷懒 |
| 为什么插件侧 backend 自启不能把“子进程拉起来了”直接当成成功 | 先讲边界：本地进程拉起不等于后端真的 ready，端口绑定、依赖导入、reload watcher 和环境变量都可能在 spawn 之后失败；再讲控制面：当前必须用 `/health` 作为最小 readiness contract，只有命中后才推进到 `ready`；最后讲 trade-off：这仍不是完整 supervisor，只是最保守的一层启动控制 | readiness probe、false positive、control plane | 插件里 `starting` 只代表命令已发起，只有 `/health` 200 才切到 `ready` | 不要回答成“spawn 成功基本就够了”，这会直接暴露你没处理过本地进程假启动 |
| 为什么插件自启仍要求用户自己配置启动命令，而不是硬编码 conda 路径 | 先讲现实约束：repo 路径、shell、conda 初始化脚本、Obsidian 宿主进程环境都可能不同；再讲风险控制：当前先把“命令配置 + readiness probe + 失败降级”收敛成可回归边界，而不是做一个对你自己机器有效、对别的环境失效的假自动化；最后讲后续：如果要继续产品化，再补命令模板、预检或更稳的启动封装 | shell environment、path portability、progressive hardening | 当前设置页允许配置 `backendStartCommand` 和 `backendStartWorkingDirectory`，而不是假设所有机器都能直接 `conda activate` | 不要回答成“懒得做自动化”，要强调这是避免把环境假设硬编码进插件 |

## 9. 踩坑与复盘（5 题）

| 问题 | 回答思路 | 关键术语 | 最好举的例子 | 容易说错的点 |
| --- | --- | --- | --- | --- |
| 这个项目最可能踩的坑是什么 | 写回正确性和状态恢复一致性 | writeback safety、resume consistency | proposal 过期后还去写回 | 不要只说“调 API 很麻烦” |
| 你会先做什么，为什么 | 先做基线和协议，而不是先堆功能 | baseline、contract-first | 先有 `/health`、state schema、proposal schema | 不要上来就做 fancy UI |
| 如果时间只剩一半，你会砍什么 | 先砍花哨能力，保住问答、治理、审批写回和最小 eval | scope cut、demo-first | 砍掉复杂 GraphRAG、自动化 judge 和 dashboard | 不要说成“都很重要，一个都不能砍” |
| 如果两周做不完怎么办 | 保住主链路：ask、ingest、审批写回、最小 eval | scope cut、demo-first | 砍掉 OCR 和复杂 GraphRAG | 不要嘴硬说都能做完 |
| 你怎么证明自己是架构思考，不是拼库 | 强调边界、幂等、协议、评估、风险控制 | boundary、idempotency、ADR | 插件执行写回、后端生成 patch | 不要只列依赖名称 |
| 做完后你最想复盘什么 | 哪些设计过度、哪些不足、哪些需要用数据再验证 | postmortem、trade-off | rerank 是否真的值得长期保留 | 不要只复盘“时间不够” |
