# Skill Mechanism Design (TASK-063 ~ TASK-067)

**Tasks:** `TASK-063`, `TASK-064`, `TASK-065`, `TASK-066`, `TASK-067`

**Session Origin:** `SES-20260426-01`

**Status:** approved-design — implementation pending

> **后续会话使用说明：**
> 这份 spec 把 TASK-063 ~ TASK-067 当成一个相互依赖的整体来设计。每个任务的 `related_files` 都会指向本文件。
> 启动新会话时按 `project-session-governor` 的“开始会话”流程读完 `TASK_QUEUE` / `CURRENT_STATE` / 最近 `SESSION_LOG` 后，再读这份 spec 中与当前 task 编号对应的 section。**不要把 5 个任务合并成一个会话**：每个 task 仍只能由一个 medium 会话承担。

---

## 1. Problem

ask 链路已经走通了 ReAct 循环 + Structured Tool Calling（`TASK-046`、`TASK-049`），但其它两条链路上的“治理决策”和“周期复盘决策”都还是硬编码：

- `INGEST_STEWARD` 在 [backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py) 里把 governance finding 的发现规则写在 Python 函数里（缺 frontmatter、缺出入链等），无法按需扩展、也无法复用 LLM 的判断能力。
- `DAILY_DIGEST` 现在只是一个 retrieval-summarize 形式的最简实现，没有“今天到底要复盘什么、按什么角度复盘”的可控制面。
- 没有任何机制可以让 LLM 在接到一类治理 / 复盘任务时，**按需加载**对应的“做法说明书”（例如“怎么处理结构性缺失”“怎么做近 7 天复盘”）。

我们需要一个轻量的 **skill mechanism**：把这些“做法说明书”从代码里抽出来，变成可枚举、可索引、可按需加载、可被 LLM 在 ReAct 循环里调用的资源。

类比 Claude Code 的 skill：每个 skill = 一段 markdown + frontmatter，描述“在什么场景下、以什么步骤、调什么工具完成什么目标”。我们要做的是同构的、面向后端 LLM workflow 的版本。

## 2. Goals

- 把 `INGEST_STEWARD` / `DAILY_DIGEST` 链路的“治理 / 复盘做法”从硬编码迁移成可枚举的 skill。
- 一条 workflow 可以根据当前请求**选择 0 ~ N 条 skill** 同时执行，每条 skill 独立产出 finding，最后由一个 summary node 汇总 LLM-level governance report。
- skill 必须能按需加载（lazy load），避免每次都把所有 skill 内容塞进 prompt。
- skill 必须支持调用受白名单约束的 read-only 工具，并复用 ask 链路已有的 ReAct 执行机制。
- 现有 ask 链路 ReAct 循环代码必须被抽出为 `LLMWithToolsRunner` 通用层，让 `skill_apply` 与 `ask_graph` 共享一份执行实现。
- 现有 INGEST_STEWARD 硬编码 finding 必须迁移到 skill 体系下，不再保留两份治理来源。

## 3. Non-Goals

- 不实现“用户在 Vault 里自定义 skill markdown 文件”的加载入口（v1 只做内置 skill）。
- 不实现 skill 在生产路径上的并发执行（v1 串行执行多条 skill）。
- 不实现 skill 的运行时热更新（v1 在进程启动时静态加载）。
- 不在 v1 引入对外部 LLM judge / scorer 的调用；skill 的产出由当前已有的 faithfulness / approval 流程承接。
- 不修改 ask 链路的对外 contract（`AskWorkflowResult` 的 schema 在 v1 不变）。
- 不在本 spec 内重写 `DAILY_DIGEST` 的整体形态；v2 仅把“复盘内容由谁决定”这件事从硬编码搬到 skill 上。
- 不实现 skill 的“触发计划”逻辑（间隔几天触发、定时调度等都由另一层组件负责，与 skill 本身无关）。

## 4. Approaches Considered

1. **直接把 governance 规则写成更多 Python 函数 + 配置文件**
   优点：实现成本最低；缺点：完全没有 LLM 介入空间，且“两条笔记是否相关”这种判断本质上需要 LLM。

2. **把每条 skill 当成独立 LangGraph subgraph 注册**
   优点：和现有 graph 形态一致；缺点：v1 只用得到 ReAct 循环，subgraph 抽象成本与收益不匹配，迁移阻力大。

3. **共享 `LLMWithToolsRunner`，每条 skill 用 frontmatter + markdown body 描述 + 一个 skill_apply 节点统一执行（推荐）**
   - skill 是数据：`name / version / scope / required_inputs / allowed_tools / instruction`。
   - 节点是行为：`skill_apply` 在 ingest / digest 图里执行选中的 skill 列表。
   - runner 是机制：`LLMWithToolsRunner` 抽出 ask 现有的 ReAct 循环，被 ask graph 与 skill_apply 复用。
   - 优点：把“执行机制”“决策载体”“执行宿主”三者分开；ask 链路不被破坏，governance / digest 链路得到与 ask 同构的 LLM + tools 能力；后续要加“用户自定义 skill”只需在加载层做扩展。

**推荐方案 3。**

## 5. Architecture

```
                 +-----------------------+
ask_graph -----> | LLMWithToolsRunner    | <----- skill_apply node (ingest / digest)
                 | (shared ReAct loop)   |
                 +-----------+-----------+
                             |
                             v
                 +-----------------------+
                 | ToolRegistry          |
                 | (existing whitelist)  |
                 +-----------------------+

ingest_graph: ... -> skill_select -> skill_apply -> governance_summary -> proposal -> ...
digest_graph: ... -> skill_select -> skill_apply -> digest_summary -> ...

builtin_skills/
  structural_governance/
    skill.md        # frontmatter + instruction
  content_redundancy/
    skill.md
  weekly_review/
    skill.md
  ...
```

### 5.1 Skill 数据结构（v1）

frontmatter 字段（最小集）：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `name` | yes | 全局唯一标识，例如 `structural_governance` |
| `version` | yes | 语义化版本号，写进 trace 与 finding，便于回溯 |
| `description` | yes | 1 ~ 2 句话，用于让 selector LLM 决定是否加载本 skill |
| `applicable_workflows` | yes | `[ingest_steward]` / `[daily_digest]` / 其它 |
| `required_inputs` | yes | 例如 `["target_notes", "vault_root"]`；missing 时 selector 拒绝该 skill |
| `allowed_tools` | yes | 该 skill 允许调用的工具白名单（v1 子集，v2 全启用） |
| `max_tool_rounds` | no | 控制单条 skill 的 ReAct 上限，默认 3 |

markdown body：

- 自然语言描述「在什么场景下做什么」「用什么工具」「输出 finding 的格式」。
- 严格要求模型只输出 `findings: list[GovernanceFinding]`（沿用既有 `GovernanceFinding` schema），保证后续 proposal builder 可以直接消费。

### 5.2 Skill Selection（v1 简化版）

- v1 不引入“selector LLM”：由调用方（例如插件或 ingest 入口）显式传入要执行的 skill name 列表。
- v2 引入 `skill_select` 节点：用一个轻量 LLM 调用，根据 description + 当前 request 决定加载哪些 skill；同样需要落 trace。

### 5.3 Skill Apply（核心节点）

`skill_apply` 节点的职责：

1. 顺序遍历选中的 skill。
2. 对每条 skill：
   - 把 frontmatter + body + workflow 传入的 `required_inputs` 拼成 system prompt。
   - 把 `allowed_tools` 解析为一个**临时受限 ToolRegistry view**，传给 `LLMWithToolsRunner`。
   - 调用 runner 跑一次完整 ReAct 循环（受 `max_tool_rounds` 上限保护）。
   - 把 runner 返回的结构化结果落为 `SkillExecutionResult`。
3. 累积每条 skill 的 raw findings；不在本节点做合并 / 去重 / LLM 二次筛。

### 5.4 Governance Summary（merge 阶段）

新增 `governance_summary` 节点（ingest 链路）/ `digest_summary` 节点（digest 链路）：

- **预处理 (S1)**：在节点内部对 raw findings 跑一次 deterministic dedup（基于 `evidence_path` + `finding_type` 组合 key），保留所有原始项作为 `raw_findings`。
- **LLM 二次筛 (S3)**：调用一次 LLM 生成 `governance_report_markdown`，要求模型对去重后的 findings 给出：
  - 每条 finding 的 keep / drop 判断与原因；
  - 推荐的 proposal 优先级；
  - 如果 LLM 失败 / 超时 / JSON 解析失败，fail-soft：保留 raw findings 做兜底，并在 trace 标 `summary_status=failed`。
- 最终 artifact 同时保留 `raw_findings`（供审计 / 复盘）和 `governance_report_markdown`（供 UI 展示）。
- proposal builder 仍只消费 raw findings 的 keep 集合，不在本任务内绕过既有 HITL 流程。

## 6. Task Breakdown

5 个 medium 任务，按依赖串行；ordering：063 → 064 → 065 → 066 → 067。

### TASK-063 — 抽取 LLMWithToolsRunner 通用 ReAct 层（基础）

**Why first:** 这是后续 4 个任务的执行底座；不先抽出来，skill_apply 就得自己复制一份 ask 的 ReAct 代码，迁移阻力会被推到所有下游任务。

**In scope**

- 在 `backend/app/runtime/` 下新增 `llm_with_tools_runner.py`，承载 `LLMWithToolsRunner`。
- 把 [backend/app/graphs/ask_graph.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/graphs/ask_graph.py) 与 [backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py) 中现有的 ReAct 循环代码**等价迁移**到 runner（不修改对外行为，不改 contract，不改 prompt）。
- runner 至少暴露：`run(prompt, tools, max_rounds, trace_hook) -> RunnerResult`。
- 单元测试覆盖：`tool_call_rounds` 终止条件、tool error fallback、max_rounds 上限、guardrail 透传。
- 在 ask 端切回到使用 runner 的实现，保证既有 `tests.test_ask_workflow` 全绿。

**Out of scope**

- 不引入 skill 概念。
- 不改 ask 的对外 schema。
- 不引入 streaming。

**Acceptance**

- ask 链路的 backend 测试套件不回归。
- runner 提供独立单元测试，覆盖至少 4 个分支：normal exit、no tool call、tool error fallback、max rounds reached。
- runner 暴露的 trace 字段足以让下游 skill_apply 写入 `skill_name / skill_version / decisions`。

**Acceptance criteria for trace fields (来自原 TASK-068 trace 部分):**

- runner 的 `RunnerResult` 必须支持 caller 注入额外 trace 元数据（即 caller 能往 trace 上挂 `skill_name / skill_version / decisions`），不要求本任务真的写入 skill 字段，但必须验证 hook 入口存在。

---

### TASK-064 — 引入 skill 数据结构 + 内置 demo skill + skill_apply 节点骨架

**Why second:** 把数据结构和宿主节点先立起来，后面的 v1 / v2 可以直接挂在这条骨架上。

**In scope**

- 新增模块 `backend/app/skills/`：
  - `skill_spec.py`：`SkillSpec` Pydantic model（按 §5.1 字段）。
  - `loader.py`：从 `backend/app/skills/builtin/` 目录加载 markdown + frontmatter，启动时全部加载到内存 `SKILL_REGISTRY`。
  - `registry.py`：暴露 `get_skill(name)` / `get_skills_for_workflow(action)`。
- 新增 1 条 demo skill `frontmatter_completeness`：只检查目标 note 是否缺少 frontmatter，便于把链路跑通。本任务**只**实现这一条 skill，不要求覆盖 governance 既有规则。
- 在 `backend/app/graphs/ingest_graph.py` 增加 `skill_apply` 节点（仅作为 governance proposal 之前的可选节点；本任务允许显式从入口绕过，方便回归既有路径）。
- skill_apply 内部使用 TASK-063 的 runner 调用 LLM；本任务暂不开放工具白名单，所有 tool 调用直接被 reject（v2 才开放）。
- runner 的 trace 必须落 `skill_name / skill_version / selected_skills / per_skill_status`（本字段实现来自原 TASK-068 trace 部分）。
- 单元测试：skill loader、registry lookup、skill_apply 节点的成功 / 失败 / fail-soft 分支。

**Out of scope**

- 不实现 governance summary 节点。
- 不迁移现有 INGEST_STEWARD 硬编码 finding。
- 不放开 skill 的 tool 调用。

**Acceptance**

- demo skill 能在 ingest 链路里被调用并写入一条 `frontmatter_missing` finding（沿用既有 `GovernanceFinding` schema）。
- ingest 链路既有测试不回归。

---

### TASK-065 — 三条内置 governance / review skill + governance_summary 节点（v1 全量）

**Why third:** v1 上线第一个完整闭环；这一任务结束后，链路就具备了「多 skill 并行 → 去重 → LLM 二次筛 → 报告 + raw findings 双产出」的完整形态。

**In scope**

- 新增 3 条内置 skill（无需调工具）：
  - `structural_governance`（结构性缺失：缺 frontmatter、缺出入链；本任务的“出入链缺失”仅基于显式存在 link 字段判断，不做相关性推断）。
  - `content_leftover_tasks`（识别笔记里遗留的 `[ ]` task / TODO）。
  - `weekly_review_summary`（按传入的 note 列表生成本周复盘要点）。
- 在 `backend/app/graphs/ingest_graph.py` 加 `governance_summary` 节点，按 §5.4 实现 dedup + LLM summary，输出：
  - `raw_findings: list[GovernanceFinding]`
  - `governance_report_markdown: str`
  - `summary_status: ok | failed | skipped`
- 在 `backend/app/graphs/digest_graph.py` 加 `digest_summary` 节点，初版直接复用 governance_summary 的实现（只是工作流标签不同）。
- artifact / response 增加上述新字段；插件层不在本任务做 UI 集成（v2 之后再做）。
- proposal builder 在本任务内**只消费 raw findings**，不依赖 markdown 报告；保证既有 HITL 链路可以平稳过渡。

**Out of scope**

- 不放开 skill 的 tool 调用。
- 不迁移现有 INGEST_STEWARD 硬编码 finding（在 TASK-067 完成）。
- 不重构 digest 的整体形态；本任务只插入 summary 节点。

**Acceptance**

- 新增 backend 测试覆盖：3 条 skill 的最小快照 + summary 节点的 ok / failed / skipped 三个分支。
- ingest / digest 链路既有测试不回归。

---

### TASK-066 — 放开 skill 的工具调用 + 引入 1 条 tool-using skill

**Why fourth:** v1 验证了无工具的 skill 闭环；v2 才把 skill 真正变成「LLM + tools 的最小 agent」。

**In scope**

- 在 `SkillSpec.allowed_tools` 上落地工具白名单解析，传入 `LLMWithToolsRunner` 时构造 scoped tool registry view（**不**修改全局 `TOOL_REGISTRY`）。
- 新增 1 条 tool-using skill：`related_notes_linker`
  - 输入：候选笔记列表、目标笔记。
  - 工具白名单：复用 ask 已有的 `search_notes` + `load_note_excerpt`，外加本任务新增的 `search_related_notes`（基于 hybrid retrieval，输入是笔记内容片段）。
  - 输出 finding：`finding_type=missing_inbound_link`，附带 evidence chunk 引用。
- 复用 TASK-063 的 `max_tool_rounds`，避免 skill 进入死循环。
- `governance_summary` 增加对带 evidence_chunk 的 finding 的展示规范（在 markdown 报告里附 anchor）。
- 单元测试覆盖：scoped registry 拒绝越权工具、tool-using skill 在 max_rounds 内正常收敛、finding payload 结构。

**Out of scope**

- 不开启用户自定义 skill 入口。
- 不引入 skill selector LLM；调用方仍显式传入 skill name 列表。
- 不调整既有 ask 工具的 schema。

**Acceptance**

- `related_notes_linker` 在 sample_vault 上能产出至少 1 条 `missing_inbound_link` finding。
- 不允许的工具调用被 runner 拒绝并落 trace。
- backend 测试不回归。

---

### TASK-067 — 迁移 INGEST_STEWARD 现有硬编码 governance + benchmark 覆盖

**Why last:** 必须等 v2 工具白名单与 summary 节点落地后，才能让既有规则真正退役而不丢能力。

**In scope**

- 把 [backend/app/services/ingest_proposal.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ingest_proposal.py) 中现有的硬编码 governance finding 等价迁移到 skill 体系：
  - 缺 frontmatter / 缺标题 / 缺出入链 / 遗留任务等，全部改由 `structural_governance` + `content_leftover_tasks` + `related_notes_linker` 输出。
  - 旧函数保留对外签名但内部委托给 skill；待回归确认稳定后再做 deprecation。
- 在 [eval/benchmark/ask_benchmark_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/benchmark/ask_benchmark_cases.json) 的同级目录新增 `governance_skill_benchmark_cases.json`（小样本即可，5 ~ 10 条），覆盖每条 skill 至少一条正例 + 一条反例。本字段实现来自原 TASK-068 eval 部分。
- 在 `backend/tests/` 下补一组测试，确认旧硬编码 governance 用例迁移后产出等价的 raw findings。
- 更新 `docs/PROJECT_MASTER_PLAN.md` 中关于 INGEST_STEWARD governance 来源的描述。

**Out of scope**

- 不顺手重写 proposal validator。
- 不顺手扩 benchmark runner 的指标维度（仅落 dataset，不强制接 CI）。

**Acceptance**

- 旧硬编码 governance 路径的所有既有 backend 测试通过（行为等价）。
- 新增 governance skill benchmark 数据集 schema 校验通过。
- ingest / digest 端到端冒烟在 sample_vault 上稳定输出 raw_findings + governance_report_markdown。

## 7. Cross-Cutting Concerns

### 7.1 Trace

- 每条 skill 执行写入：`skill_name / skill_version / status / tool_rounds / tool_calls / latency_ms`。
- summary 节点写入：`summary_status / kept_findings / dropped_findings / report_chars`。
- ask 链路 trace 字段不变（向后兼容）。

### 7.2 Failure handling

- skill_apply 单条失败不影响其它 skill；记录 `per_skill_status` 后继续。
- summary 节点失败时降级为 `summary_status=failed` + 保留 raw findings；不阻塞 proposal 流程。
- runner 出错的语义与 ask 现有语义一致（不为 skill 改特例）。

### 7.3 Cost guardrails

- 每条 skill 默认 `max_tool_rounds=3`；可在 frontmatter 内单独覆写。
- summary 节点的 LLM 调用走与 ask 相同的 provider 选择层，便于 cost 统计；本 spec 不规定 model，由后续配置项决定。

## 8. Open Questions（不阻塞 v1）

- skill description 是否需要双语？（中 / 英 prompt 一致性 vs. 维护成本）
- 多 skill 是否要支持并发执行？（v1 串行；只有当链路总延迟成为问题时才考虑）
- 是否引入用户自定义 skill 加载入口？（v1 不支持；如果未来引入，需要安全审计：路径白名单、prompt injection 防御、tool 白名单严格继承）

## 9. 跨会话执行手册

- TASK-063 启动会话先读：本 spec §5.3 + §6.TASK-063 + ask_graph / ask service 现有 ReAct 实现。
- TASK-064 启动会话先读：本 spec §5.1 + §5.3 + §6.TASK-064 + TASK-063 产出的 runner 文件。
- TASK-065 启动会话先读：本 spec §5.4 + §6.TASK-065 + 既有 `GovernanceFinding` schema + ingest_graph / digest_graph。
- TASK-066 启动会话先读：本 spec §5.3 + §6.TASK-066 + ToolSpec 白名单、ask_tools.py 中 `search_notes` / `load_note_excerpt` 实现。
- TASK-067 启动会话先读：本 spec §6.TASK-067 + ingest_proposal.py 旧 governance 函数 + 既有 ingest 测试。
- 任何一个会话发现本 spec 与最终代码不一致时，优先在 SESSION_LOG 标 `tail_sync_item`，不要静默修改本 spec；spec 更新走单独的 docs-only 小任务。
