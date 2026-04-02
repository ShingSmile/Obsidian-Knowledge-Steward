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
- 主文件从本次起只保留活跃 / 最近内容；更早的完成任务统一去 archive 查。

## Active Backlog

### TASK-047

- `task_id`: `TASK-047`
- `session_id`: `SES-20260329-02`
- `title`: 重构上下文装配层为多阶段质量控制管线
- `category`: `Retrieval`
- `priority`: `P1`
- `status`: `completed`
- `scope`: `medium`
- `goal`: 将当前上下文装配层从"去重 + 截断"升级为四阶段质量控制管线：相关性过滤（按 RRF 分数丢弃尾部噪声）→ 来源多样性控制（限制单篇笔记贡献上限，防止上下文被单一来源垄断）→ 结构化上下文增强（为每条 chunk 注入来源笔记标题、heading 路径、位置信息，使模型引用时能精确定位来源）→ 相关性加权 Token 预算分配（高分 chunk 保留全文，低分 chunk 截取摘要，替代当前的均匀截断）。装配结果输出 ContextBundle 并附带 assembly_metadata 记录每阶段的决策。
- `out_of_scope`:
  - 不引入外部 re-ranker 模型（cross-encoder 等），过滤基于 RRF 分数
  - 不改变混合检索层（RRF 融合逻辑不动）
  - 不改变 `AskWorkflowResult` 外层 contract
  - 不做 chunk 内容压缩或摘要生成（预算分配只做截取，不调模型）
- `acceptance_criteria`:
  - 相关性过滤：RRF 分数低于动态阈值（top-1 分数的一定比例）的 chunk 被丢弃，丢弃数量记入 assembly_metadata
  - 来源多样性：单篇笔记最多贡献 N 条 chunk（N 可配置，默认 2），超出部分按分数从低到高淘汰，淘汰记录写入 assembly_metadata
  - 结构化增强：每条 evidence_item 携带 source_note_title、heading_path、position_hint（如"第2节/共5节"），模型 prompt 中可直接引用这些字段
  - 预算分配：按 RRF 分数排序，高分 chunk 分配全文预算，低分 chunk 分配摘要预算（前 N 字符），总 Token 不超过可配置上限
  - ContextBundle 输出包含 evidence_items、source_notes（去重后来源列表）、assembly_metadata（各阶段过滤/调整统计）
  - 现有 ask 测试和 eval golden case 全部通过
- `depends_on`:
  - `TASK-042`
- `related_files`:
  - `backend/app/contracts/workflow.py`
  - `backend/app/context/assembly.py`
  - `backend/app/context/render.py`
  - `backend/app/services/ask.py`
  - `backend/tests/test_context_assembly.py`
  - `backend/tests/test_ask_workflow.py`
  - `eval/golden/ask_cases.json`
- `derived_tasks`:
  - `small: 为 assembly_metadata 增加结构化 trace 写入，便于在 Trace 回放中定位装配层丢弃了哪些 chunk`
  - `small: 评估是否需要对多样性控制中被淘汰的 chunk 做"备选池"保留，供 ReAct 二轮补查时优先召回`
  - `small: 为相关性过滤的阈值比例增加离线 eval case 覆盖，验证阈值变化对 ask 质量的影响`
- `notes`: 当前 `context/assembly.py` 原先只做 chunk_id 去重和字符数截断，面试时说"独立的上下文装配层"但追问细节会见底。`SES-20260329-02` 已完成四阶段升级：相关性过滤、来源多样性控制、结构化增强与加权预算分配均已落到 [backend/app/context/assembly.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/context/assembly.py)，`ContextBundle` 已补 `source_notes / assembly_metadata`，ask prompt 也已在 [backend/app/context/render.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/context/render.py) 中渲染 `source_note_title / position_hint`，citation 与 `retrieved_candidates` 继续只跟随 post-assembly 可见 evidence。验收期内已通过 `tests.test_context_assembly + tests.test_ask_workflow` 共 54 个 backend tests，以及 2 条 ask eval case。上面的 `derived_tasks` 继续保留为不阻塞收口的 `small` 尾项。

### TASK-045

- `task_id`: `TASK-045`
- `session_id`: `SES-20260329-01`
- `title`: 补齐受限写回的静态校验与工具覆盖，增强 LLM 输出可控性
- `category`: `Safety`
- `priority`: `P1`
- `status`: `completed`
- `scope`: `medium`
- `goal`: 在现有两种原子 patch 类型（merge_frontmatter、insert_under_heading）和五层工具调用防御的基础上，补齐三个维度：(1) 扩展读工具覆盖，增加 `get_note_outline` 和 `find_backlinks`，让模型在提出治理建议前能感知文档结构和引用关系；(2) 扩展写操作类型，增加 `replace_section` 和 `add_wikilink`，覆盖章节重写和知识图谱链接治理场景；(3) 补齐静态校验层，在现有 JSON Schema 校验之上增加内容长度阈值、目标路径白名单和危险模式检测。
- `out_of_scope`:
  - 不引入 `delete_note`、`full_rewrite`、`move_note` 等高风险操作
  - 不改变 Proposal 审批链路和审计日志结构
  - 不改变 Guardrail 降级策略
  - 不做插件侧 UI 改动
- `acceptance_criteria`:
  - `get_note_outline(path)` 返回目标笔记的标题树 + frontmatter 摘要，工具注册为只读，当前 scope 以 ASK 链路为准
  - `find_backlinks(path)` 返回经验证的 backlink 命中并在不满足完整性 / freshness 条件时 fail-closed，工具注册为只读，当前 scope 以 ASK 链路为准
  - `replace_section` patch 类型支持按 heading 定位并替换整段内容，before_hash 校验覆盖、审计日志记录与现有 patch 类型一致
  - `add_wikilink` patch 类型支持在指定 heading 下插入双向链接，限制为只能添加已存在的笔记路径
  - 静态校验层在 Proposal 提交时拦截：插入内容超过阈值（可配置，默认 2000 字符）、目标路径不在 vault 范围内、内容包含危险模式（脚本标签、删除指令等）
  - 现有工具和 patch 类型的行为不回退
  - 新增工具和 patch 类型有对应测试覆盖
- `depends_on`:
  - `TASK-042`
- `related_files`:
  - `backend/app/tools/registry.py`
  - `backend/app/guardrails/ask.py`
  - `backend/app/services/ingest_proposal.py`
  - `backend/app/services/proposal_validation.py`
  - `backend/app/contracts/workflow.py`
  - `plugin/src/writeback/applyProposalWriteback.ts`
  - `backend/app/indexing/store.py`
  - `backend/tests/test_tool_registry.py`
  - `backend/tests/test_proposal_validation.py`
- `derived_tasks`:
  - `small: 为 replace_section 增加 max_changed_lines 安全检查，防止模型一次替换过大段落`
  - `small: 将静态校验的阈值和白名单抽为配置文件，支持按 vault 自定义`
- `notes`: 当前系统只有两种 patch 类型和两个读工具，覆盖了最基础的治理场景。但随着 ingest proposal 逐渐成熟，模型缺乏文档结构感知（不知道标题树）和引用关系感知（不知道谁链接了这篇笔记），治理建议的质量会受限。写操作只有"在标题下插入"和"合并 frontmatter"，章节重写和链接管理这两个高频治理场景没有覆盖。静态校验目前只有 JSON Schema 层面的参数合法性检查，没有内容级的安全拦截。这三个维度是让"可控性"从最小可用推向面试可深挖的关键补齐。2026-03-28 已完成第一阶段落地：`get_note_outline`、fail-closed `find_backlinks`、ask verified-only tool reentry、插件侧 `replace_section / add_wikilink`、静态校验接线与相关测试均已合入本地 `main`。2026-03-29 已由 `SES-20260329-01` 收口最后缺口：[backend/app/services/proposal_validation.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/proposal_validation.py) 已把 `replace_section / add_wikilink` 纳入正式支持 op，并补齐 payload-specific validation、危险模式拦截与 `add_wikilink` 的“仅允许 vault 内已存在笔记”约束，因此本任务验收已满足。上面的 `derived_tasks` 继续保留为不阻塞收口的 `small` 尾项。

### TASK-046

- `task_id`: `TASK-046`
- `session_id`: `SES-20260401-01`
- `title`: 用 LangGraph 原生 conditional edges 重构 ask 链路为图级 ReAct 循环
- `category`: `Graph`
- `priority`: `P1`
- `status`: `completed`
- `scope`: `medium`
- `goal`: 将 ask 链路从当前的线性三节点图（prepare_ask → execute_ask → finalize_ask）重构为带条件边的图级 ReAct 循环：prepare_ask → llm_call → should_continue（条件边）→ tool_node / finalize_ask，其中 llm_call 与 tool_node 之间形成循环直到模型不再调用工具或达到最大轮次。ReAct 的每一步都是图上的独立节点，经过 SqliteSaver checkpoint，支持中途恢复。ingest / digest 链路保持静态线性编排不变。
- `out_of_scope`:
  - 不改变 ingest / digest 链路的编排范式
  - 不引入新的工具类型（工具扩展由 `TASK-045` 负责）
  - 不改变 `AskWorkflowResult` 外层 contract（除新增 `tool_call_rounds` 字段）
  - 不引入 LangGraph `create_react_agent` 预构建组件（保留自定义图结构的控制力）
- `acceptance_criteria`:
  - ask 图结构改为 `prepare_ask → llm_call → should_continue(conditional_edge) → tool_node | finalize_ask`，`llm_call ↔ tool_node` 形成图级循环
  - `should_continue` 条件边根据 LLM 输出是否包含 tool_calls 路由到 `tool_node`（继续循环）或 `finalize_ask`（结束）
  - `tool_node` 执行工具调用后返回 `llm_call`，形成完整 ReAct 循环
  - 最大轮次上限可配置（默认 3 轮），超过上限后条件边强制路由到 `finalize_ask`
  - 每轮 llm_call / tool_node 都经过 SqliteSaver checkpoint，循环中途中断可从上一轮恢复
  - 每轮工具调用经过现有五层防御体系校验，不绕过 guardrail
  - 每轮 llm_call / tool_call / tool_result 作为独立 trace 事件写入，支持按 thread_id 回放完整 ReAct 链路
  - `AskWorkflowResult` 新增 `tool_call_rounds: int` 字段记录实际工具调用轮次
  - 模型第一轮判断信息充分时（不调用工具），条件边直接路由到 finalize_ask，行为与当前单轮模式一致
  - 现有 ask 相关测试和 eval golden case 全部通过或等价迁移
- `depends_on`:
  - `TASK-042`
  - `TASK-044`
- `related_files`:
  - `backend/app/graphs/ask_graph.py`
  - `backend/app/graphs/runtime.py`
  - `backend/app/graphs/state.py`
  - `backend/app/contracts/workflow.py`
  - `backend/app/services/ask.py`
  - `backend/app/tools/registry.py`
  - `backend/app/guardrails/ask.py`
  - `backend/app/context/assembly.py`
  - `backend/app/observability/runtime_trace.py`
  - `backend/tests/test_ask_workflow.py`
  - `eval/golden/ask_cases.json`
- `derived_tasks`:
  - `small: 为 ReAct 循环增加 token 消耗累计统计，写入 trace 便于成本分析`
  - `small: 为多轮工具调用场景补充 eval golden case，覆盖"首轮不够、二轮补查后回答"的典型路径`
  - `small: 评估是否需要对 ReAct 循环中的中间 context 做增量去重，避免多轮查询结果重复`
- `notes`: 原设计是在 `execute_ask` 节点内部用 while 循环手写 ReAct——LangGraph 只看到一个黑盒函数，循环内部不经过 checkpoint，trace 也只记录一个事件。`SES-20260401-01` 已将 ask 收敛为 graph-only 执行模型：[backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py) 现使用 `prepare_ask -> llm_call -> tool_node -> finalize_ask` 的 conditional-edge 循环，[backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py) 被拆为初始装配、工具判定、工具执行与最终回答 helper，不再保留 `run_minimal_ask` 这条完整 ask 主入口，[backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py) 也已新增 `tool_call_rounds`。验收期内已通过 `tests.test_ask_workflow` 共 32 个 backend tests，以及 2 条 ask eval case。上面的 `derived_tasks` 继续保留为不阻塞收口的 `small` 尾项。

### TASK-048

- `task_id`: `TASK-048`
- `session_id`:
- `title`: 跨链路内容质量评估与 Runtime Faithfulness 治理 Umbrella
- `category`: `Eval`
- `priority`: `P1`
- `status`: `split_into_TASK-050_to_TASK-054`
- `scope`: `large`
- `goal`: 将原本单个 `medium` 里过于拥挤的“跨链路质量评估 + runtime gate”工作重新定义为 umbrella：保留统一目标与验收边界，但把执行切分为多个可独立推进、可单会话收口的 `medium`。整体目标仍是为 ask / ingest / digest 三条链路建立共享 faithfulness 底座、场景特定离线指标，以及可保守降级的 runtime 质量闸门。
- `out_of_scope`:
  - 不再把 umbrella 本身作为单个 `medium` 直接执行
  - 不在一个会话里同时完成共享底座、runtime gate、ask 四维度和 ingest / digest 全部评估
  - 不改变插件侧 UI
  - 不做 re-ranking（cross-encoder 精排为独立优化方向，不在本任务范围内）
- `acceptance_criteria`:
  - `TASK-050` 到 `TASK-054` 组合后，完整覆盖原任务的共享底座、runtime gate、ask 四维度评估、ingest / digest 场景指标与 golden 扩充
  - 每个拆分出的 `medium` 都能独立绑定 session、独立验证、独立收口
  - `TASK-033` 的 runtime groundedness 目标由新的拆分任务显式吸收，不再悬空
- `depends_on`:
  - `TASK-042`
  - `TASK-047`
- `related_files`:
  - `backend/app/services/ask.py`
  - `backend/app/services/ingest_proposal.py`
  - `backend/app/guardrails/ask.py`
  - `backend/app/context/assembly.py`
  - `backend/tests/test_ask_workflow.py`
  - `eval/run_eval.py`
  - `eval/golden/ask_cases.json`
  - `backend/tests/test_eval_runner.py`
- `derived_tasks`:
  - `medium: TASK-050 抽取共享 ask faithfulness 判定层并接通 ask runtime 启发式 gate（已完成）`
  - `medium: TASK-051 建立共享 claim 拆解 + NLI faithfulness core（已完成）`
  - `medium: TASK-052 用 embedding 相似度接通 ask / digest runtime faithfulness gate（已完成）`
  - `medium: TASK-053 完成 ask 离线四维度评估与 faithfulness golden 扩充`
  - `medium: TASK-054 完成 ingest / digest 场景评估指标与 golden 基线`
- `notes`: `SES-20260401-02` 实际实现后已经证明，这块工作把“共享语义底座、runtime 安全闸门、ask 四维度离线指标、ingest / digest 场景指标、golden 扩充”全部塞进一个 `medium` 会导致执行边界失真。因此从本次起保留 `TASK-048` 作为 umbrella，只负责定义总目标与拆分关系；真实执行改由 `TASK-050` 到 `TASK-054` 承担。`TASK-033` 也随之改为被 `TASK-050` / `TASK-052` 吸收。

### TASK-050

- `task_id`: `TASK-050`
- `session_id`: `SES-20260401-02`
- `title`: 抽取共享 ask faithfulness 判定层并接通 ask runtime 启发式 gate
- `category`: `Eval`
- `priority`: `P1`
- `status`: `completed`
- `scope`: `medium`
- `goal`: 把 ask 的 groundedness / faithfulness 启发式判断从离线 eval 脚本中抽成共享模块，在 ask runtime 主链路接入最保守的一层 `unsupported_claim -> retrieval_only` 降级，并让离线 eval 复用同一套判定逻辑，先消除“实现一份、评估一份”的分叉。
- `out_of_scope`:
  - 不引入 claim-NLI 或外部 LLM judge
  - 不把 runtime gate 升级为 embedding 相似度
  - 不扩展到 digest runtime gate
  - 不完成 ask 四维度或 ingest / digest 场景指标
- `acceptance_criteria`:
  - 新增共享 ask faithfulness snapshot 模块，runtime 与 offline eval 复用同一套判定逻辑
  - ask 对明显 `unsupported_claim` 的 generated answer 会稳定降级为 `retrieval_only`
  - 降级结果沿用现有 `AskWorkflowResult` contract，并写入 guardrail action
  - 受影响的 tests 与 eval golden case 全部通过
- `depends_on`:
  - `TASK-042`
  - `TASK-046`
  - `TASK-047`
- `related_files`:
  - `backend/app/quality/faithfulness.py`
  - `backend/app/guardrails/ask.py`
  - `backend/app/services/ask.py`
  - `eval/run_eval.py`
  - `backend/tests/test_ask_guardrails.py`
  - `backend/tests/test_ask_workflow.py`
  - `backend/tests/test_eval_runner.py`
  - `eval/golden/ask_cases.json`
- `derived_tasks`:
  - `small: 将 runtime faithfulness outcome 写入更结构化的 trace 字段，减少后续 gate 接线时的重复 glue code`
  - `small: 评估是否需要把 shared snapshot 拆成 ask 专属层与更通用的 claim-level helper`
- `notes`: 本任务对应 `TASK-048` 的第一刀，已在 `SES-20260401-02` 完成。当前实现仍是 term-overlap 风格的启发式快照，不是最终的 claim-NLI / embedding 方案；它的价值在于先把 ask runtime 安全降级与 offline eval 判定层收敛到同一个代码入口，为后续 `TASK-051` / `TASK-052` / `TASK-053` 铺底。

### TASK-051

- `task_id`: `TASK-051`
- `session_id`: `SES-20260401-03`
- `title`: 建立共享 claim 拆解 + NLI faithfulness core
- `category`: `Eval`
- `priority`: `P1`
- `status`: `completed`
- `scope`: `medium`
- `goal`: 把当前 ask 专属、启发式的 faithfulness snapshot 演进为可复用的 claim-level 语义底座：统一 claim 拆解、evidence 配对与 NLI 判定接口，让 ask / ingest / digest 在离线评估路径上能够共享一套 semantic faithfulness core。
- `out_of_scope`:
  - 不把外部 LLM judge 接入 runtime 主链路
  - 不在本任务内完成 ask / digest runtime gate 接线
  - 不在本任务内完成所有场景指标与 golden 扩充
- `acceptance_criteria`:
  - 提供共享 claim 拆解接口，能把中文回答 / rationale / digest 文本拆成原子声明列表
  - 提供统一 NLI 判定接口，对 `(claim, evidence)` 输出至少 `entailed / contradicted / neutral`
  - ask / ingest / digest 的离线评估都能调用同一套 core，而不是各自维护局部逻辑
  - 补齐最小测试，覆盖 entailed / contradicted / neutral 与中文短句边界
- `depends_on`:
  - `TASK-050`
- `related_files`:
  - `backend/app/quality/faithfulness.py`
  - `backend/app/quality/__init__.py`
  - `eval/run_eval.py`
  - `backend/tests/test_faithfulness.py`
  - `backend/tests/test_ask_guardrails.py`
  - `backend/tests/test_eval_runner.py`
  - `eval/golden/ask_cases.json`
  - `eval/golden/governance_cases.json`
  - `eval/golden/digest_cases.json`
- `derived_tasks`:
  - `small: 为 claim 拆解增加中文停用词 / allowlist，减少短句误拆`
  - `small: 为 NLI 判断增加 confidence threshold 与低置信度 trace`
- `notes`: `SES-20260401-03` 已完成本任务：[backend/app/quality/faithfulness.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/quality/faithfulness.py) 现已新增共享 claim-level faithfulness core，可把中文回答 / rationale / digest / proposal summary 拆成原子声明，并对 `(claim, evidence)` 输出 `entailed / contradicted / neutral` verdict；当 embedding provider 可用时，会复用现有 provider abstraction 走更强的 semantic backend，不可用时则保留 lexical / structured fallback。与此同时，[eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py) 已让 ask / governance / digest 共用同一套 core，governance / digest 的 faithfulness 不再直接退回 `context_recall` 充当替代指标。验收期内已通过 `tests.test_ask_guardrails + tests.test_faithfulness + tests.test_eval_runner` 共 15 个 backend tests，以及 4 条 targeted eval case。外部 LLM judge 与 runtime gate 接线继续保持 out-of-scope，留给 `TASK-052` / `TASK-053` / `TASK-054`。

### TASK-052

- `task_id`: `TASK-052`
- `session_id`: `SES-20260402-01`
- `title`: 用 embedding 相似度接通 ask / digest runtime faithfulness gate
- `category`: `Eval`
- `priority`: `P1`
- `status`: `completed`
- `scope`: `medium`
- `goal`: 把当前 ask runtime 的启发式降级逻辑升级为更稳定的 embedding/cosine 近似 gate，并把同类 runtime 质量闸门扩展到 digest 链路，形成“低延迟、可配置阈值、保守降级”的统一运行时策略。
- `out_of_scope`:
  - 不引入外部 LLM judge 作为 runtime 依赖
  - 不完成完整 ask 四维度离线评估
  - 不处理 ingest runtime gate
- `acceptance_criteria`:
  - ask generated answer 在生成后执行 embedding 相似度 gate，unsupported 比例超阈值时保守降级为 `retrieval_only`
  - digest 生成结果具备等价的 runtime quality outcome（如 `low_confidence` 或等价 contract / trace 字段）
  - 阈值、score 与 guardrail action 会写入结构化 trace 或等价运行时元数据
  - 已验证的 grounded case 不被大面积误伤
- `depends_on`:
  - `TASK-051`
- `related_files`:
  - `backend/app/quality/faithfulness.py`
  - `backend/app/services/ask.py`
  - `backend/app/guardrails/ask.py`
  - `backend/app/services/digest.py`
  - `backend/app/graphs/ask_graph.py`
  - `backend/app/graphs/digest_graph.py`
  - `backend/app/graphs/runtime.py`
  - `backend/app/contracts/workflow.py`
  - `backend/tests/test_faithfulness.py`
  - `backend/tests/test_ask_workflow.py`
  - `backend/tests/test_digest_workflow.py`
  - `backend/tests/test_workflow_invoke_contract.py`
  - `backend/tests/test_eval_runner.py`
- `derived_tasks`:
  - `small: 评估是否将 runtime faithfulness score 作为可选质量元数据暴露给插件侧`
  - `small: 为 digest 的低置信度文案增加更细粒度 reason code`
- `notes`: `SES-20260402-01` 已完成本任务： [backend/app/quality/faithfulness.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/quality/faithfulness.py) 新增了共享 `RuntimeFaithfulnessSignal` 归约层，在 claim-level semantic report 之上输出 `outcome / score / threshold / backend / reason / unsupported_claim_count`；[backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py) 与 [backend/app/guardrails/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/guardrails/ask.py) 已改为消费这套 shared runtime signal，对低分 generated answer 保守降级为 `retrieval_only`；[backend/app/services/digest.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/digest.py) 与 [backend/app/contracts/workflow.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/contracts/workflow.py) 也已为 digest 增加结构化 `runtime_faithfulness` outcome；[backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py) 与 [backend/app/graphs/digest_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/digest_graph.py) 会把 `score / threshold / outcome / backend` 落到 trace；[backend/app/graphs/runtime.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/runtime.py) 也已补齐 serializer allowlist，避免 completed checkpoint resume 因新 enum / model 产生 warning。验收期内已通过 `tests.test_ask_guardrails + tests.test_faithfulness + tests.test_ask_workflow + tests.test_digest_workflow + tests.test_workflow_invoke_contract + tests.test_eval_runner` 共 66 个 backend tests。 

### TASK-053

- `task_id`: `TASK-053`
- `session_id`:
- `title`: 完成 ask 离线四维度评估与 faithfulness golden 扩充
- `category`: `Eval`
- `priority`: `P1`
- `status`: `planned`
- `scope`: `medium`
- `goal`: 在共享 faithfulness core 之上，把 ask 离线评估补齐为可回归的四维度基线：Faithfulness、Answer Relevancy、Context Precision、Context Recall，并补足最小可持续维护的 ask golden 标注。
- `out_of_scope`:
  - 不处理 digest / ingest 场景指标
  - 不接 runtime gate
  - 不改变 ask 主链路 contract
- `acceptance_criteria`:
  - ask eval 输出 Faithfulness / Answer Relevancy / Context Precision / Context Recall 四个 0-1 分数
  - `eval/run_eval.py` 的 ask scenario overview 能稳定汇总四维度结果
  - ask 新增至少 5 条 faithfulness / evidence 标注 case，覆盖 grounded / unsupported / partial support 等路径
  - 现有 ask tests 与 golden case 不回退
- `depends_on`:
  - `TASK-051`
- `related_files`:
  - `backend/app/quality/faithfulness.py`
  - `eval/run_eval.py`
  - `eval/golden/ask_cases.json`
  - `backend/tests/test_eval_runner.py`
  - `backend/tests/test_ask_workflow.py`
- `derived_tasks`:
  - `small: 为 Context Recall 的 golden evidence 标注建立轻量标注规范`
  - `small: 评估是否需要为 answer relevancy 保留 deterministic fallback 算法`
- `notes`: `TASK-050` 只让 ask 拥有了共享的启发式 snapshot 与 runtime downgrade，还没有把 ask 离线质量评估做成真正的四维度回归面板。本任务负责把 ask 这一条链路先补完整。

### TASK-054

- `task_id`: `TASK-054`
- `session_id`:
- `title`: 完成 ingest / digest 场景评估指标与 golden 基线
- `category`: `Eval`
- `priority`: `P1`
- `status`: `planned`
- `scope`: `medium`
- `goal`: 在共享 faithfulness core 之上，为 ingest 与 digest 补齐各自的场景评估：ingest 关注 rationale 是否忠实且 patch 是否安全，digest 关注摘要是否忠实且覆盖关键事实，从而让跨链路 eval 不再只剩 ask 一条线。
- `out_of_scope`:
  - 不完成 ask 四维度评估
  - 不把 ingest / digest 的全部评估逻辑塞回 runtime
  - 不扩展新的插件交互
- `acceptance_criteria`:
  - ingest eval 输出 Rationale Faithfulness 与 Patch Safety
  - digest eval 输出 Faithfulness 与 Coverage
  - ingest / digest 至少各新增 3 条 golden case，覆盖成功、偏离与保守失败路径
  - governance / digest 场景 overview 能汇总新增指标
- `depends_on`:
  - `TASK-051`
- `related_files`:
  - `backend/app/services/ingest_proposal.py`
  - `backend/app/services/digest.py`
  - `eval/run_eval.py`
  - `eval/golden/governance_cases.json`
  - `eval/golden/digest_cases.json`
  - `eval/golden/resume_cases.json`
  - `backend/tests/test_eval_runner.py`
  - `backend/tests/test_digest_workflow.py`
- `derived_tasks`:
  - `small: 为 Patch Safety 的违规项输出整理更稳定的分类标签`
  - `small: 为 digest coverage 的关键事实抽取建立最小标注规范`
- `notes`: ask 之外的两条链路当前还没有真正的内容质量基线。本任务把 ingest / digest 的评估补齐，避免 `TASK-048` 拆分后只剩 ask 质量在进步、其他链路继续停留在合约级断言。

### TASK-049

- `task_id`: `TASK-049`
- `session_id`:
- `title`: 将工具调用从 prompt-based JSON 约定迁移到 Structured Tool Calling
- `category`: `Graph`
- `priority`: `P1`
- `status`: `planned`
- `scope`: `medium`
- `goal`: 将当前 ask 链路中 LLM 与工具的交互方式从"system prompt 文本描述 + 模型返回裸 JSON + 手动 json.loads 解析"迁移为 OpenAI Function Calling 协议：LLM 调用时通过 API `tools` 参数传入结构化工具定义，模型返回结构化 `tool_calls` 字段，由框架保证调用格式合法性。现有 ToolSpec 中的 `input_schema` 可直接映射为 `tools[].function.parameters`，迁移后移除 prompt 中的工具描述文本和手动 JSON 解析逻辑。
- `out_of_scope`:
  - 不改变工具注册表的 ToolSpec 数据结构（schema 定义复用）
  - 不改变五层工具调用防御体系（白名单、scope 隔离、只读强制、参数校验、guardrail 拦截）
  - 不引入新的工具类型（工具扩展由 `TASK-045` 负责）
  - 不改变 `AskWorkflowResult` 外层 contract
  - 不迁移 ingest / digest 链路（当前只有 ask 链路涉及工具调用）
- `acceptance_criteria`:
  - LLM 调用时通过 `tools` 参数传入工具定义，格式符合 OpenAI Function Calling 协议（`type: "function"`, `function.name`, `function.parameters`）
  - ToolSpec 的 `name`、`purpose`、`input_schema` 自动映射为 `tools` 参数，不需要手动维护两份 schema
  - 模型返回的 `tool_calls` 字段由响应解析逻辑提取，替代当前的 `json.loads(raw_text)` 手动解析
  - 移除 system prompt 中的工具描述文本和 JSON 格式约定
  - 移除 `_parse_tool_call_decision` 中的手动 JSON 解析和类型检查逻辑
  - ReAct 循环中的 tool_node 仍经过现有五层防御体系校验，工具执行路径不变
  - 对不支持 Function Calling 的 provider 保留 fallback（降级为当前 prompt-based 方式）
  - 现有 ask 测试和 eval golden case 全部通过
- `depends_on`:
  - `TASK-046`
- `related_files`:
  - `backend/app/services/ask.py`
  - `backend/app/tools/registry.py`
  - `backend/app/context/render.py`
  - `backend/app/graphs/ask_graph.py`
  - `backend/app/contracts/workflow.py`
  - `backend/tests/test_ask_workflow.py`
  - `backend/tests/test_tool_registry.py`
- `derived_tasks`:
  - `small: 评估是否为 ToolSpec 增加 description 字段，映射为 tools[].function.description 提升模型选择准确率`
  - `small: 为 Function Calling 的 token 消耗（tools 参数占用）增加 trace 记录，便于成本分析`
  - `small: 评估是否引入 parallel tool calls（模型一次返回多个 tool_calls），当前 ReAct 循环为单工具串行`
- `notes`: 当前 ask 链路的工具调用完全靠 prompt 约定——system prompt 用纯文本描述可用工具和 JSON 格式要求，模型返回纯文本 JSON，代码侧手动 `json.loads` 解析并做类型检查。这种方式有三个问题：(1) 模型可能返回格式不合法的 JSON，解析失败只能静默降级；(2) 工具描述在 prompt 中占用 token 但不受 API 级别的结构化保证；(3) 面试时说"Tool Calling"但实际没用 Function Calling 协议，追问会暴露。迁移后工具定义通过 API `tools` 参数传入，模型返回结构化 `tool_calls`，格式合法性由 API 层保证，prompt 更干净、解析更可靠。ToolSpec 中已有完整的 `input_schema`（JSON Schema 格式），可直接映射为 `tools[].function.parameters`，迁移成本低。需要注意的是部分 provider（如本地模型）可能不支持 Function Calling，因此保留 prompt-based fallback 作为降级路径。

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

### TASK-033

- `task_id`: `TASK-033`
- `session_id`:
- `title`: 在 ask 主链路接入保守 groundedness gate 与安全降级
- `category`: `Retrieval`
- `priority`: `P2`
- `status`: `absorbed_by_TASK-050_and_TASK-052`
- `scope`: `medium`
- `goal`: 在 `TASK-028` 已有最小 groundedness 离线评估的基础上，把最保守的一层 answer-citation semantic consistency 检查接入 ask runtime，对明显 `unsupported_claim` 的 generated answer 做安全降级。
- `out_of_scope`:
  - 不引入 LLM judge 或外部评测平台
  - 不改插件 ask UI
  - 不接入 hybrid retrieval、rerank 或更复杂的 query planner
- `acceptance_criteria`:
  - 对 citation 编号合法但 evidence 不支持的 generated answer，ask runtime 会稳定降级为 `retrieval_only` 或等价安全结果
  - 已验证的 grounded case 不会被大面积误伤
  - 不改变现有 `AskWorkflowResult` 外层 contract
  - 有最小测试与 eval case 覆盖成功 / 降级分支
- `depends_on`:
  - `TASK-028`
- `related_files`:
  - `backend/app/services/ask.py`
  - `backend/tests/test_ask_workflow.py`
  - `eval/run_eval.py`
  - `eval/golden/ask_cases.json`
  - `backend/tests/test_eval_runner.py`
- `derived_tasks`:
  - `small: 为 groundedness term extractor 增加停用词 / allowlist，减少中文短窗误报`
  - `small: 评估是否需要把 LLM judge 只作为人工抽样辅助，而不是主链路依赖`
- `notes`: `TASK-028` 已经证明 ask 存在“引用编号合法，但答案语义越界”的 bad case。该问题在 `SES-20260401-02` 中先由 `TASK-050` 以共享启发式 snapshot + `retrieval_only` 安全降级的方式落下第一刀，随后在 `SES-20260402-01` 由 `TASK-052` 以 shared semantic runtime gate + 结构化 runtime trace 的方式正式收口。因此本任务不再单独执行，拆分吸收到 `TASK-050` / `TASK-052`。

## Recent Completed

### TASK-044

- `task_id`: `TASK-044`
- `session_id`: `SES-20260327-01`
- `title`: 将 checkpoint 持久化迁移到 LangGraph SqliteSaver 并保留业务封装层
- `category`: `Graph`
- `priority`: `P1`
- `status`: `completed`
- `scope`: `medium`
- `goal`: 将当前自研的 checkpoint 持久化（裸写 SQLite `workflow_checkpoint` 表）迁移为基于 LangGraph 官方 `SqliteSaver` 的方案，让 state 序列化/反序列化和 thread_id 索引由框架承担，同时在上层保留字段级校验、幂等短路返回、状态机管理和 hydrate 字段覆盖等业务封装。
- `out_of_scope`:
  - 不引入条件边（`add_conditional_edges`），当前三条链路仍为线性拓扑
  - 不迁移 `workflow_checkpoint` 表中的审计/业务元数据字段，保持双表并行
  - 不改变 `WorkflowInvokeRequest/Response` 外层 contract
  - 不顺手重构 ingest 审批流程为 `interrupt_before` 模式（可作为 derived_task）
- `acceptance_criteria`:
  - `graph.compile(checkpointer=saver)` 替代当前无 checkpointer 的 compile
  - `graph.invoke(state, config={"configurable": {"thread_id": ...}})` 替代手动逐节点迭代
  - SqliteSaver 自动在每个节点执行后持久化 state
  - 业务封装层保留：`resume_match_fields` 校验、completed checkpoint 幂等短路、`checkpoint_status` 状态机（IN_PROGRESS/COMPLETED/FAILED）、hydrate 时 run_id/trace_events 覆盖
  - `workflow_checkpoint` 表保留业务元数据（checkpoint_status、last_completed_node、next_node_name），与 SqliteSaver 自有表并行工作
  - Pydantic model 的序列化/反序列化在 SqliteSaver 上下游正确衔接
  - fallback shim（`_CompiledStateGraph`）和 `LANGGRAPH_AVAILABLE` / `used_langgraph` 标记移除
  - 现有 checkpoint 相关测试全部通过或等价迁移
- `depends_on`:
  - `TASK-042`
- `related_files`:
  - `backend/app/graphs/runtime.py`
  - `backend/app/graphs/checkpoint.py`
  - `backend/app/graphs/ask_graph.py`
  - `backend/app/graphs/ingest_graph.py`
  - `backend/app/graphs/digest_graph.py`
  - `backend/tests/test_indexing_store.py`
  - `backend/tests/test_ask_workflow.py`
  - `backend/tests/test_ingest_workflow.py`
  - `backend/tests/test_digest_workflow.py`
- `derived_tasks`:
  - `small: 将 ingest 审批中断从手动编排改为 LangGraph interrupt_before 声明式配置`
  - `small: 清理 checkpoint.py 中不再需要的裸 SQL 写入函数，收敛为纯业务校验层`
- `notes`: 2026-03-27 的 `SES-20260327-01` 已完成 ask / ingest / digest 正常路径迁移：图执行改为 `graph.compile(checkpointer=SqliteSaver)` + `graph.invoke(... thread_id ...)`，LangGraph graph state 现写入 SQLite `checkpoints` / `writes`，而 `workflow_checkpoint` 继续保留 `checkpoint_status`、节点指针、last_run_id 与 completed short-circuit / waiting control-plane 这层业务元数据。会话内同时补齐了 serializer allowlist、移除了 `_CompiledStateGraph` / `LANGGRAPH_AVAILABLE` / `used_langgraph` / 旧线性 runner，并在 worktree 中提交为 `e214bd7` 后合并回 `main`。两个 `small` derived_tasks 继续保留：审批中断仍未切到 `interrupt_before`，`checkpoint.py` 的业务 SQL helper 也仍可继续收敛。

### TASK-043

- `task_id`: `TASK-043`
- `session_id`: `SES-20260323-02`
- `title`: 文档控制面分层与归档治理
- `category`: `Docs`
- `priority`: `P1`
- `status`: `completed`
- `scope`: `medium`
- `goal`: 将当前项目文档从“README / PROJECT_MASTER_PLAN / TASK_QUEUE / SESSION_LOG 同时承载动态控制面”的状态，收敛为“活跃控制面 + 稳定架构 + 历史归档”的分层结构，并为后续会话建立更低成本的默认读取入口。
- `out_of_scope`:
  - 不推进任何业务功能实现
  - 不重写历史会话结论或虚构已完成事实
  - 不借文档整理顺手重排 interview-first 的业务优先级
- `acceptance_criteria`:
  - 新增 `docs/CURRENT_STATE.md` 作为唯一动态控制面入口，承载当前阶段、最近完成、默认下一任务、当前风险与建议先读文件
  - `docs/PROJECT_MASTER_PLAN.md` 收缩到稳定架构、边界、风险与面试叙事，不再持续堆积高波动的“下一步”状态
  - `docs/SESSION_LOG.md` 与 `docs/TASK_QUEUE.md` 建立 archive 结构，主文件只保留活跃 / 最近内容
  - 主文档第 13 节面试问答库拆分到 `docs/INTERVIEW_PLAYBOOK.md`，版本变更记录拆分到 `docs/CHANGELOG.md`
  - 新会话默认读取顺序收敛为 `TASK_QUEUE -> CURRENT_STATE -> 最近相关 SESSION_LOG -> 相关代码`
- `depends_on`:
  - `TASK-042`
- `related_files`:
  - `docs/TASK_QUEUE.md`
  - `docs/SESSION_LOG.md`
  - `docs/PROJECT_MASTER_PLAN.md`
  - `README.md`
  - `docs/CURRENT_STATE.md`
  - `docs/INTERVIEW_PLAYBOOK.md`
  - `docs/CHANGELOG.md`
  - `docs/archive/`
- `derived_tasks`:
  - `small: 增加文档一致性检查脚本，校验 session_id 唯一、task 状态一致与 CURRENT_STATE 链接有效`
  - `small: 为 docs/archive 增加索引页，降低历史任务与历史会话的检索成本`
- `notes`: 2026-03-23 的 `SES-20260323-01` 只完成了任务登记、范围锁定与拆分目标确认；`SES-20260323-02` 完成了实体迁移：新增 [docs/CURRENT_STATE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CURRENT_STATE.md)、[docs/INTERVIEW_PLAYBOOK.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/INTERVIEW_PLAYBOOK.md)、[docs/CHANGELOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/CHANGELOG.md)，并将原有完整 [docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md) / [docs/SESSION_LOG.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/SESSION_LOG.md) 快照归档到 `docs/archive/`；同时收缩 [README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/README.md) 与 [docs/PROJECT_MASTER_PLAN.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/PROJECT_MASTER_PLAN.md) 的高波动控制面，使默认会话读取入口收敛到 `TASK_QUEUE -> CURRENT_STATE -> 最近相关 SESSION_LOG -> 相关代码`。由于 `SES-20260323-01` 已在历史日志中占用，本次完成会话使用 `SES-20260323-02`，避免复用旧 session_id。

## Recently Completed References

| task_id | session_id | 标题 | 说明 |
| --- | --- | --- | --- |
| `TASK-044` | `SES-20260327-01` | 将 checkpoint 持久化迁移到 LangGraph SqliteSaver 并保留业务封装层 | ask / ingest / digest 正常路径已迁到 `SqliteSaver(checkpoints/writes)`，`workflow_checkpoint` 保留业务元数据与 completed short-circuit |
| `TASK-042` | `SES-20260318-07` | 统一 ask / digest / ingest 的入口路由与共享 workflow contract | 仍是当前业务基线的最近完成项，详细条目已移到 archive |
| `TASK-041` | `SES-20260318-06` | 为受限 patch op 落地最小撤销 / 回滚能力 | 回滚主线已完成，post-rollback scoped ingest 仍留在 `small` |
| `TASK-040` | `SES-20260318-05` | 建立治理 vs 问答的分场景 benchmark | 当前 eval baseline 的最近完成项 |

## History

- 更早的完成任务、历史例外任务与全量字段详情，请查：
  [docs/archive/task_queue/TASK_QUEUE_20260323_pre_split.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/archive/task_queue/TASK_QUEUE_20260323_pre_split.md)
