# MENTOR_PROGRESS

> 用途：为跨会话继续“项目面试辅导”提供最小但完整的接力信息。只写当前进度、下一步断点和用户薄弱点，不写冗余过程。

## 2026-03-23 最新断点（新会话先看这里）

- 当前最新状态：
  - Step 1：项目宏观认知与术语对齐，已完成
  - Step 2：核心架构与技术栈剖析，已完成
  - Step 3：模块 A-H 首轮源码级精读，已完成
  - Step 4：各模块首轮高频面试追问，已完成
  - 全项目总复盘首轮串讲，已完成
  - 方案 B 增量迭代，已完成并合并到 `main`
- 方案 B 已完成的内容：
  - 新增显式 `Context Assembly`
  - 新增轻量只读 `Tool Registry`
  - `ASK_QA` 接入受控 tool calling
  - `INGEST_STEWARD / DAILY_DIGEST` 复用 context assembly
  - 新增 ask runtime `guardrail`
  - 完成对应测试与 eval 回归
- 当前仓库状态：
  - `main` 已落在方案 B 合并结果
  - 合并后主工作区已验证通过：
    - backend `104` 个测试通过
    - offline eval `21/21` 通过
- 当前最适合进入的辅导阶段：
  - 不再继续讲“方案 B 要不要做”
  - 直接转为“方案 B 做完后怎么讲给面试官听”
  - 或者只回读方案 B 最关键的增量源码链路
- 当前会话恢复后的最新确认：
  - 用户当前并不掌握方案 B 的具体内容，不能直接进入“背 60-90 秒表达”
  - 需要先补一轮最小心智模型：方案 B 解决什么问题、插在 ask 主链路的什么位置、边界在哪里
  - 本轮已补读：
    - `backend/app/services/ask.py`
    - `backend/app/context/assembly.py`
    - `backend/app/tools/registry.py`
    - `backend/app/guardrails/ask.py`
  - 用户已能用自己的话回答：
    - 方案 B 的核心不是让模型更自由
    - 而是让问答链路更可控
    - 控制点落在上下文、工具使用和最终结果检验
    - 检索之后还需要 `context assembly`，因为检索结果还要继续提纯，才能形成更干净、可控的 context
  - 用户开始继续追问：
    - 为什么预算不够时不能随机截断
    - 当前代码里的 `context assembly` 到底怎样做去重、裁剪和过滤
  - 用户已能回答当前 `context assembly` 的核心 trade-off：
    - 不能完全保证最相关的 chunk 一定会进入最终上下文
  - 用户当前在优先级判断上出现的新偏差：
    - 能意识到 `context assembly` 对噪声过滤的重要性
    - 但容易把“数据放大后的首要升级点”直接回答成 `context assembly`
    - 还需要继续压实：召回问题是上游问题，`assembly` 只能整理已召回证据，不能补回漏召回证据
  - 用户已能回答当前 `context assembly` 的直接价值：
    - 保证检索到的上下文更干净、可控地进入模型输入
  - 用户已能对白名单工具边界给出第一反应：
    - 需要让模型能力可控
    - 防止超过边界造成危险行为
  - 用户当前在工具边界上暴露的新疑问：
    - 容易把“当前不开放给治理/复盘 workflow”理解成“这些 workflow 完全用不上工具”
    - 下一小步需要纠正为：不是绝对用不上，而是当前版本不让模型在高风险链路里自主决定调工具
  - 用户已能给出“tool calling 不等于开放式 ReAct”的第一层答案：
    - 当前没有根据 tool calling 结果继续自主思考并反复调用工具
  - 用户已能明确判断当前 `ASK_QA` 的范式定位：
    - `workflow-first` 的 `tool-augmented QA`
    - 不是开放式 ReAct
    - 也不是典型 Plan-and-Execute
  - 用户本轮主动切换到更具体的问题：
    - 想先弄清当前到底实现了哪些工具
    - 想知道工具是如何被选择、校验、执行、以及结果如何回流 prompt
  - 用户在理解工具价值时出现新的合理质疑：
    - 觉得当前这 3 个工具对 `ASK_QA` 的直接作用不明显
    - 需要明确区分“当前真实增益最大的工具”与“更多在搭能力边界/未来扩展口的工具”
  - 用户进一步追问到工具价值的核心前提：
    - 对 `chunk / snippet / excerpt` 的区别还不清楚
    - 需要明确：检索命中的是 chunk，但候选对象里同时保留 full chunk text 与 snippet
    - 需要进一步说明当前 `load_note_excerpt` 的真实边界：它读取的是受限笔记片段，不是按 chunk 精准扩窗
- 下一步推荐顺序：
  1. 先用白话讲清“为什么要做方案 B”
  2. 再练 60 到 90 秒的“方案 B 增量价值”表达
  3. 再精读这条增量主链路：
     - `backend/app/services/ask.py`
     - `backend/app/context/assembly.py`
     - `backend/app/tools/registry.py`
     - `backend/app/guardrails/ask.py`
  4. 然后进入综合面试模拟
- 用户当前最需要加强的点：
  - 容易把“workflow-first agent system”讲成“只是个 workflow”
  - 容易把 `retrieval / context assembly / tool result / guardrail` 混成一层
  - 容易只讲功能新增，漏掉安全边界和 trade-off
  - 容易把“有 tool calling”误讲成“开放式 ReAct agent”
  - 当前对方案 B 的代码主链路还没有建立“问题 -> 方案 -> 边界”的最小心智模型
  - 下一小步要重点压实：
    - `retrieval` 负责“找证据”
    - `context assembly` 负责“整理证据”
    - 继续细化 `context assembly` 的具体控制动作：去重、预算裁剪、可疑内容过滤、统一证据打包
    - 重点解释当前实现是“按已有检索顺序做保守裁剪”，不是随机截断，也不是复杂重排优化
    - 继续把 trade-off 讲完整：稳定性、可解释性、实现复杂度 与 最优召回之间的取舍
    - 继续纠偏：当问题变成“找不准 / 找不全 / 找太慢”时，优先升级 `retrieval`；当问题变成“召回后上下文太脏 / 太长 / 太危险”时，再优先升级 `assembly`
    - 继续强化 `assembly` 的完整价值：不只是“提纯文本”，还包括统一证据格式、承接 tool result、把安全检查前移到模型生成前
    - 继续压实 `Tool Registry` 的具体边界：
      - workflow 白名单
      - 只读限制
      - 参数 schema 校验
      - 路径范围限制
      - tool result 是否允许回流上下文
    - 继续解释为什么当前只对 `ASK_QA` 开放工具：
      - `ASK_QA` 风险最低
      - `INGEST_STEWARD / DAILY_DIGEST` 已有 proposal / approval / writeback 主语义
      - 高风险链路优先收紧模型自由度，而不是扩权
    - 继续把 `tool calling != ReAct` 讲完整：
      - 当前 ask 是固定主链路
      - 最多一次受控工具决策与执行
      - 没有开放式 think-act-observe 循环
    - 先补完当前工具实现全景：
      - 已实现的 3 个工具分别做什么
      - 模型如何做一次受控工具决策
      - registry 如何校验
      - 哪些 tool result 可以回流上下文
    - 继续诚实评估当前工具价值：
      - `load_note_excerpt` 是当前最有实际 QA 价值的工具
      - `search_notes` / `list_pending_approvals` 在现版本里更多是边界能力与控制面示例，直接增益有限
    - 继续讲清 `chunk / snippet / excerpt`：
      - chunk 是索引和检索的基本单位
      - snippet 更像展示用摘要
      - excerpt 是工具侧额外读取的受限原文片段
    - 工具讲完后再进入 `guardrail`
- 阅读说明：
  - 下方大段模块记录主要是历史辅导过程，供回看用
  - 新会话恢复时，优先以本节为准

## 当前总进度

- 当前已完成：
  - Step 1：项目宏观认知与术语对齐
  - Step 2：核心架构与技术栈剖析
  - Step 3：先完成了模块拆分与阅读顺序设计
  - Step 3：模块 A 已完成源码级精读
  - Step 4：模块 A 的面试追问与高分回答已完成并写入 `docs/INTERVIEW_PREP_ESSENCE.md`
  - Step 3：模块 B 已完成源码级精读与核心结论沉淀
  - Step 4：模块 B 的两道面试追问与高分回答已完成并写入 `docs/INTERVIEW_PREP_ESSENCE.md`
  - Step 3：模块 C 已完成源码级精读与总收束
  - Step 4：模块 C 的面试追问与高分回答已完成并写入 `docs/INTERVIEW_PREP_ESSENCE.md`
  - Step 3：模块 D 已完成首轮源码级精读与 3 道高频追问
  - Step 3：模块 E 已完成首轮源码级精读、4 道高频追问与收束
  - Step 4：模块 E 的高频追问与参考回答已写入 `docs/INTERVIEW_PREP_ESSENCE.md`
  - Step 3：模块 F 已完成首轮源码级精读与核心结论沉淀
  - Step 4：模块 F 的 2 道场景题已完成并写入 `docs/INTERVIEW_PREP_ESSENCE.md`
  - Step 3：模块 F 的 `before_hash / after_hash / rollback` 补课与最终收束已完成
  - Step 3：模块 F 的 `audit vs checkpoint` 补充概念已完成，模块 F 已真正收尾
  - Step 3：模块 G 已完成首轮源码级精读与场景题收束
  - Step 3：模块 H 已完成首轮源码级精读与场景题收束
  - 当前模块级代码精读（A-H）已完成一轮
- 截至本轮更新的最新断点：
  - 已完成“全项目总复盘”首轮串讲
  - 当前不再继续拆新模块，除非用户点名回看某个模块
  - 下一步默认进入“综合面试模拟”
  - 综合模拟优先串法已固定为：
    - 定位
    - 架构
    - 检索
    - workflow
    - proposal / writeback
    - 插件 runtime
    - 观测与评估
  - 用户当前最需要加强的，不是继续记零散术语，而是把以下控制面边界讲顺：
    - `trace`
    - `checkpoint`
    - `audit_log`
    - `writeback_result`
  - 面试表达上的主要薄弱点：
    - 容易把“系统能跑”讲成“系统可靠”
    - 容易只讲功能流程，漏掉幂等、事实对账、降级与恢复边界
    - 容易把 `citation`、`trace`、`audit` 这类控制面概念混讲
- 当前正在进行：
  - 当前阶段已从“模块级精读”切换到“全项目总复盘准备”
  - 下一会话的第一目标不是继续拆新模块，而是：
    - 做 2 分钟全项目总串讲
    - 进入综合面试模拟
  - 下一会话开始后，优先动作：
    - 先承认模块 A-H 已全部完成首轮精读
    - 不再回到模块级扫盲，除非用户点名要复盘某个模块
    - 直接把项目主线串成：定位 -> 架构 -> 检索 -> workflow -> proposal/writeback -> 插件 runtime -> 观测评估
  - 模块 G：插件 UI 与后端运行时控制已完成首轮源码级精读与面试题收束
  - 已完成模块 G 的基础术语补课规划，准备先补 `插件 / 本地后端 / 探活(/health) / readiness / auto-start`
  - 已完成 `plugin/src/main.ts` 首轮精读：明确了插件入口负责 registerView、注册命令、调度 backend runtime 与把真实/演示 proposal 注入面板
  - 已针对用户困惑回退到更白话的解释：明确 `main.ts = 总调度台`、`runtime.ts = 后端管家`、`KnowledgeStewardView.ts = 右侧面板`、`settings.ts = 设置页`
  - 下一小步只讲 `main.ts` 的 `onload()` 启动顺序，避免一次塞入过多函数名
  - 用户已能说出 `onload()` 的核心职责是“把后续需要的东西先装配好”，不是自己完成业务处理
  - 当前已进入 `main.ts` 的单函数精读阶段，下一小步讲 `pingBackend()` 这条最短链路：`打开面板 -> 询问后端状态 -> 更新面板 -> 弹通知`
  - 用户已能说出 `pingBackend()` 不只是弹通知，还要把后端状态同步给面板，因为插件 UI 也需要持有这份状态
  - 已补读 `plugin/src/backend/runtime.ts` 全文件，下一小步聚焦解释 `BackendRuntimeSnapshot`：它是共享状态记录，不是一次性检查结果
  - 用户已能说出 `snapshot` 是“系统持续维护的一份共享状态记录”，并主动联想到观察者模式；下一步可进入 `subscribe/updateSnapshot` 的订阅-通知机制
  - 用户已明确表示“共享状态 + 观察者模式”这一层已经理解，无需继续深讲；下一步转入 backend runtime 的状态机语义：`checking / starting / ready / unavailable / failed`
  - 用户已能初步回答“为什么不能只做 available / unavailable 二态”，知道需要更细粒度状态控制；下一步需要把答案从抽象的“更细粒度控制”落到 UI、错误分流和用户动作指引
  - 当前已进入 `startBackend()` 精读：用户需要重点掌握 4 个控制点
    - 用 `startPromise` 防止重复启动
    - 启动前先做一次 `refreshStatus()`，避免后端其实已 ready 还重复拉进程
    - 未配置启动命令时直接返回 `unavailable`，不盲目 spawn
    - 真正启动后仍要等待 `/health`，只有命中 health 才算 ready
  - 用户已能清楚区分：
    - `startPromise` 防的是“本轮启动中的重复点击/重复触发”
    - `refreshStatus()` 防的是“后端其实已经 ready，却又多拉一个进程”
  - 下一小步进入 `launchAndWaitUntilHealthy()`：重点讲清 `spawn != ready`、进程提前退出为什么记为 `failed`、以及轮询 `/health` 的 readiness 语义
  - 已补读 `KnowledgeStewardView.ts` 中 backend runtime 相关 UI：
    - `onOpen()` 订阅 runtime 状态并触发首轮 `refreshStatus()`
    - `renderBackendRuntimeSection()` 根据状态机控制按钮启用/禁用和状态卡片展示
    - `renderHealthSection()` 只在 `health` 可用时展示后端详情
    - `handleStartBackend()` 负责把 runtime 启动结果翻译成用户可理解的 Notice
  - 用户已能说出 UI 展示 `last_error / recent_output / tracked_pid` 的价值在于排障和解释“为什么启动失败”，而不是只给一个红绿灯
  - 已完成 `settings.ts` 首轮精读：用户已理解配置化的目的在于承接本地环境差异和运行策略，而不是“图方便”
  - 已按用户要求把模块 G 的串讲总结补进 `docs/INTERVIEW_PREP_ESSENCE.md`
  - 已明确模块 G 在面试中的定位：不是最高频核心算法模块，但属于工程化加分项
  - 已按用户要求给出模块 G 的场景题并写入 `docs/INTERVIEW_PREP_ESSENCE.md`
  - 下一步进入模块 H：观测与评估闭环
  - 模块 H 仍未正式开始源码级精读
  - 用户当前明确表示“观测 / 评估都不懂”，需要按零基础顺序重讲
  - 模块 H 的讲解顺序已收敛为：
    - 先用白话讲清 `观测(tracing/trace)` 和 `评估(eval)` 的区别
    - 再精读 `backend/app/observability/runtime_trace.py`
    - 最后精读 `eval/run_eval.py`
  - 当前第一小步不是直接讲代码细节，而是先建立一句话心智模型：
    - 观测 = 看系统这次是“怎么跑的”
    - 评估 = 看系统这次“跑得好不好”
  - 用户已能用自己的话复述：
    - 观测 = 运行过程中经历的事件
    - 评估 = 对最终结果做指标评测，例如忠实度、回答相关度
  - 下一小步进入模块 H 的第一段源码：
    - `backend/app/observability/runtime_trace.py`
    - 先讲“为什么同时写 JSONL 和 SQLite `run_trace`”
  - 用户已能回答：
    - JSONL 更适合当前运行排障
    - SQLite `run_trace` 更适合后续聚合查询
  - 下一小步继续精读 `runtime_trace.py`：
    - 讲清 trace event 的身份字段：`run_id / thread_id / graph_name / node_name / event_type`
  - 用户已能回答：
    - `thread_id` = 同一条业务事务/流程线程
    - `run_id` = 这条线程的一次具体执行尝试
  - 下一小步继续精读 `runtime_trace.py`：
    - 讲清为什么 `compose_trace_hooks()` 要吞掉单个 sink 的异常，避免观测拖垮主链路
  - 用户已能回答：
    - 如果 trace sink 长期静默失败，主业务出问题时会缺少 trace，排障会明显变难
  - 下一小步继续追问：
    - 为什么即使有“排障困难”的风险，trace sink 失败仍然不能反向打崩主业务链路
  - 用户已能回答：
    - 主业务优先级更高，观测数据属于辅助链路
  - 下一小步继续精读 `runtime_trace.py`：
    - 讲清 `_normalize_trace_event()` 和 `_build_trace_id()` 在做什么
  - 用户已能回答：
    - trace 事件不能原样乱写，必须先收敛成稳定的结构化数据，否则后续难以查询、提取和复用
  - 下一小步继续精读 `runtime_trace.py`：
    - 讲清 `normalize -> details_json -> trace_id` 这条落库前链路
  - 用户已能回答：
    - `trace_id` 不能只靠 `run_id + node_name`
    - 因为同一节点在同一次 run 里也可能出现重试或不同事件细节，需要靠 `timestamp / details_json` 区分
  - 下一小步继续精读 `runtime_trace.py`：
    - 讲清 `_build_trace_id()` 当前解决的是“最小幂等去重”，不是完整事件版本治理
  - 用户已能回答：
    - 如果要看“这一次具体执行卡在哪一步”，更适合按 `run_id` 查询
  - 下一小步继续精读 `runtime_trace.py`：
    - 讲清 `run_id` 查询与 `thread_id` 查询分别服务什么排障目标
  - 已完成 `runtime_trace.py` 第一轮关键概念：
    - 观测 vs 评估
    - JSONL vs SQLite `run_trace`
    - `thread_id` vs `run_id`
    - best-effort trace sink
    - `normalize -> trace_id`
    - `run_id` 查询 vs `thread_id` 查询
  - 下一小步切入 `eval/run_eval.py`：
    - 先补 `golden set` / `fixture` / `离线回归` 三个基础概念
    - 再讲 `run_case()` 主链路
  - 用户已能回答：
    - `golden set` = 一批带预期设定的固定样本
    - `fixture` = 为回归稳定执行准备的可重复运行环境
  - 下一小步继续精读 `eval/run_eval.py`：
    - 讲清 `run_case()` 的主链路：建 fixture -> 固化 settings -> 跑 entrypoint -> 生成 snapshot -> 断言 expected
  - 用户已能回答：
    - `build_eval_settings()` 要强制覆盖 provider 配置，是为了防止本机环境差异污染 case 结果
  - 下一小步继续精读 `eval/run_eval.py`：
    - 讲清为什么 eval 要刻意 mock provider / embedding，而不是追求“每次都连真实外部服务”
  - 用户已能回答：
    - 离线 eval 倾向 mock 外部模型，是为了去掉外部模型输出波动和联网不确定性对结果的污染
  - 下一小步继续精读 `eval/run_eval.py`：
    - 讲清为什么 `run_eval.py` 不直接比原始响应文本，而是先构造结构化 snapshot 再断言
  - 用户已能回答：
    - eval 不能只看最终文本结果，还要看系统行为是否稳定合理
  - 下一小步继续精读 `eval/run_eval.py`：
    - 纠正并强化为：snapshot 不只是看“过程”，而是同时收敛输出 contract、fallback 信号和持久化副作用事实
    - 下一问聚焦 `resume`：为什么要把 `checkpoint / audit_log / writeback_result` 一起拉进 snapshot
  - 用户当前在 `resume` 场景里卡住的核心点已明确：
    - 还分不清 `checkpoint / audit_log / writeback_result` 分别是什么
    - 还分不清“接口 contract”与“持久化副作用事实”的边界
  - 下一小步先做概念补课，再继续 `run_eval.py`
  - 用户已能初步复述：
    - `checkpoint` 记录当前运行状态
    - `audit_log` 记录发生过什么事件
  - 下一小步继续纠正并压实：
    - `checkpoint` 更准确是“线程当前停在哪个状态、恢复时该从哪里接着跑”
    - `audit_log` 更准确是“这次审批/写回到底发生了什么、谁做的、结果如何”
  - 用户已能继续理解：
    - `trace` = 运行过程观测
    - `audit_log` = 高风险事实账本
    - 高风险链路要先核事实，再补过程
  - 模块 H 已完成首轮源码级精读与 2 道高频面试题
  - 用户已确认当前没有下一个模块
  - 下一步已切换为：
    - 全项目总复盘
    - 或综合面试模拟
    - 接着追问为什么 `resume` eval 不能只看接口返回成功
  - 用户已能回答：
    - `resume` 返回成功不等于系统真的成功
    - 因为 checkpoint 状态流转、审批日志和写回结果这些关键事实也可能没对齐
  - 下一小步继续模块 H：
    - 用这道题收束 `resume snapshot` 的必要性
    - 然后进入 `quality_metrics / groundedness` 这条评估指标线
  - 当前已切入模块 H 的指标层：
    - 下一小步只补 `groundedness / faithfulness / relevancy / context_precision / context_recall` 的白话含义
    - 再落回 `run_eval.py` 当前是怎么近似实现的
  - 用户当前追问已切到两个非常关键的面试点：
    - 这些指标在大厂项目里到底会不会真的用
    - 当前仓库里这些指标具体怎么计算
  - 下一小步回答顺序已收敛为：
    - 先讲“概念会用，但名字和实现未必一模一样”
    - 再逐个解释当前仓库的最小近似计算方式
  - 用户已明确表示：
    - 当前已经理解这几个评估指标
    - 不需要继续做手算 case 练习
  - 下一小步直接进入模块 H 的面试题拷问与高分回答模板
  - 已进入模块 H 面试题 1：
    - 主题是“为什么 `resume` 返回成功不等于系统真的成功”
  - 用户当前作答状态：
    - 已能想到先查 `trace`、`checkpoint`、`audit_log`
    - 但仍会把 `trace` 放在高风险恢复链路的第一优先级
    - 还需要继续纠正：
      - 第一优先级应先核对持久化事实一致性
      - `trace` 主要用于补充定位，不是最终真相来源
      - 还缺少对 `writeback_result` 对账和后续补观测 / 补 eval 的回答
  - 下一小步：
    - 给出模块 H 面试题 1 的满分回答模板
    - 然后再决定是否进入题 2
  - 用户当前新增卡点已明确：
    - 分不清 `trace / checkpoint / audit_log / eval snapshot` 四者的层级关系
  - 下一小步先补清四者边界，再继续模块 H 面试题
  - 用户当前追问进一步收敛为：
    - `trace` 和 `audit_log` 的区分点到底在哪
  - 下一小步先用“黑匣子 vs 凭证账本”讲清两者差异，再回到模块 H 面试题
  - 用户已能给出第一层直觉：
    - `trace` 像流水账
    - `audit_log` 指向高风险点的记录
  - 下一小步继续纠正：
    - `audit_log` 不是“审查”，而是“审计凭证 / 事实账本”
    - 再追问为什么 `resume` 出问题时应优先看 `audit_log`
  - 用户已能回答：
    - 高风险链路里应先看事实是否符合预期，再回头看运行过程
  - 下一小步：
    - 把这句收束成“事实优先于过程”的高分表达
    - 然后进入模块 H 面试题 2
  - 已进入模块 H 面试题 2：
    - 主题是“trace sink 静默失败一周但主业务仍正常时，如何做发现和治理”
  - 用户当前状态：
    - 对“观测断流的发现机制 / 告警机制 / 治理机制”还没有成体系答案
  - 下一小步：
    - 给出模块 H 面试题 2 的满分回答模板
    - 观察用户是否能复述“发现 -> 暴露 -> 治理”三段式
  - 用户已能回答：
    - trace sink 不能只吞异常
    - 因为长期断流会带来隐患，需要在不影响主业务的前提下告警并治理
  - 模块 H 当前已基本完成首轮收束：
    - 观测 vs 评估
    - runtime trace 设计取舍
    - golden eval / fixture / snapshot
    - `resume` 高风险链路为什么要对账持久化事实
    - 两道模块 H 高频面试题
  - 下一步可二选一：
    - 先对模块 H 做 30 秒串讲收束
    - 或直接进入下一个模块 / 总复盘

## 已拆解模块

### 模块 A：统一入口与协议控制面

- 重点文件：
  - `backend/app/main.py`
  - `backend/app/contracts/workflow.py`
- 已完成内容：
  - 讲清了统一 `/workflows/invoke` 的原因
  - 讲清了 handler registry、统一 response、`thread_id/run_id` 控制面语义
  - 完成了关于 “为什么统一入口” 和 “统一 envelope + action-specific payload” 的面试追问

### 模块 B：工作流运行时与状态管理

- 重点文件：
  - `backend/app/graphs/runtime.py`
  - `backend/app/graphs/checkpoint.py`
  - `backend/app/graphs/state.py`
- 已完成内容：
  - 讲清了 `StewardState` 是共享状态容器
  - 讲清了 checkpoint 的保存、加载、序列化/反序列化逻辑
  - 讲清了 completed checkpoint short-circuit、checkpoint hit/miss、scope mismatch、best-effort save/load 的设计意图
  - 用户已回答“为什么恢复时保留 `thread_id`、重置 `run_id`”这道追问
  - 用户已回答“为什么 checkpoint 只存必要字段，而不是全量落盘”这道追问
  - 已将模块 B 结论和两道题的高分回答模板写入 `docs/INTERVIEW_PREP_ESSENCE.md`
- 未完成内容：
  - 模块 B 已收尾
  - 下一步进入模块 C：三条业务工作流

## 新会话开始后要立刻做什么

### 1. 先进入模块 G：插件 UI 与后端运行时控制

当前断点问题：

> 模块 F 已真正收尾。用户现在已能说出：
> - `before_hash` 是 proposal 生成时的文件指纹
> - mismatch 后要区分“patch 已落地”还是“proposal 已过期”
> - 当前之所以能做 `already applied` 检查，是因为 patch op 受限且效果可确定性核查
> - `after_hash` 负责把 rollback 锁定在“proposal 写回后的精确状态”
> - rollback 必须命中精确 `after_hash`，否则会有覆盖用户后续修改的风险
> - 模块 F 的最终收束是：这一层不是让模型自由改笔记，而是在做高风险副作用治理
> 下一步按顺序继续：
> - 模块 G：插件 UI 与后端运行时控制
> - 模块 H：观测与评估闭环

要求：
- 如需复习，优先阅读 `backend/app/services/ingest_proposal.py`
- 再读 `backend/app/services/resume_workflow.py`、`backend/app/services/rollback_workflow.py`
- 最后结合插件侧 `plugin/src/writeback/` 与 `plugin/src/views/KnowledgeStewardView.ts` 追问写回安全边界与同步失败补偿
- 当前模块 G 的讲解顺序已确定为：
  - 先补后端 runtime 控制相关基础概念
  - 再读插件入口 `plugin/src/main.ts`
  - 再读运行时控制核心 `plugin/src/backend/runtime.ts`
  - 最后读 UI 与配置层 `plugin/src/views/KnowledgeStewardView.ts`、`plugin/src/settings.ts`

### 2. 模块 C 已完成，无需回看

- 只有当用户主动要求复盘 graph 编排边界时，才回看：
  - `backend/app/graphs/ask_graph.py`
  - `backend/app/graphs/ingest_graph.py`
  - `backend/app/graphs/digest_graph.py`

### 模块 C：三条业务工作流

- 已完成内容：
  - `ask_graph`：已讲清最小线性三节点、graph 与 service 边界、共享 runtime 语义
  - `ingest_graph`：已讲清线性索引主干、proposal / waiting 控制分支、proposal 与 waiting checkpoint 原子落盘
  - `digest_graph`：已讲清线性 digest 主干、proposal 作为“结果写回外壳”的轻审批分支、与 `ingest_graph` 的差异
  - 用户已回答“为什么不把 `human_approval` 直接塞进线性三节点里”这道追问，已经能说出“并不是每次都有高风险行为需要 approval，正常治理应走简单主流程”
  - 用户已回答 `daily_note / summary_note` 的含义，已经能说出“这是解析阶段打的类型标签，优先用于提高 digest 输入质量；缺失时再退回通用笔记”
- 下一步：
  - 模块 C 已收尾

### 模块 E：检索与问答生成

- 重点文件：
  - `backend/app/retrieval/sqlite_fts.py`
  - `backend/app/retrieval/sqlite_vector.py`
  - `backend/app/retrieval/hybrid.py`
  - `backend/app/services/ask.py`
  - `backend/app/contracts/workflow.py`
- 已完成内容：
  - 讲清了 `RetrievedChunkCandidate / RetrievalSearchResponse / AskWorkflowResult` 这三层协议分别承载什么
  - 讲清了 ask 主链路：query 进入 hybrid retrieval，随后构造 citation，再尝试 grounded answer，最后做 citation 编号对齐校验
  - 讲清了 ask 的三种结果模式：`generated_answer / retrieval_only / no_hits`
  - 讲清了两类不同降级：
    - `retrieval_fallback_used`：过滤条件过严，检索放宽
    - `model_fallback_used`：模型不可用，或生成答案 citation 编号失配
  - 讲清了 hybrid 的关键取舍：
    - 先用 RRF 融合 FTS 和向量，不直接混原始分数
    - filter fallback 在 hybrid 总入口统一处理
    - 向量分支 disabled / index_not_ready 不伪装成普通 no-hit
  - 已完成模块 E 的基础概念补课：
    - `query` 和 `metadata filter` 的职责分离
    - `retrieval_only` 和 `no_hits` 的区别
    - 当前前端对 `retrieval_filter` 主要停留在协议层，默认 ask 更接近全库检索
  - 已完成模块 E 的 4 道高频追问：
    - 为什么 `retrieval_fallback` 和 `model_fallback` 不能混成一个字段
    - 为什么 citation 失配时要直接降级成 `retrieval_only`
    - 规模放大 100 倍时最先炸哪一层
    - 为什么“有 citation”仍然不等于 grounded
  - 已完成模块 E 的首轮收束
- 下一步：
  - 模块 E 已收尾

### 模块 F：治理 proposal、审批恢复与写回安全

- 重点文件：
  - `backend/app/services/ingest_proposal.py`
  - `backend/app/services/resume_workflow.py`
  - `backend/app/services/rollback_workflow.py`
  - `backend/app/graphs/ingest_graph.py`
  - `plugin/src/writeback/applyProposalWriteback.ts`
  - `plugin/src/views/KnowledgeStewardView.ts`
- 已完成内容：
  - 讲清了模块 F 不是“生成建议”，而是“把建议变成可审批、可写回、可回滚、可审计的受控副作用链路”
  - 讲清了三层边界：
    - proposal 事实层
    - resume / rollback 控制面
    - 插件本地副作用面
  - 讲清了主调用链：
    - `ingest_graph` 执行 scoped ingest
    - `ingest_proposal.py` 基于 note 结构信号 + related retrieve 生成 proposal
    - proposal 与 waiting checkpoint 在同一个 SQLite 事务里原子落盘
    - 插件本地先执行受限 writeback，再把真实 `writeback_result` 回传 `/workflows/resume`
    - `resume_workflow.py` 负责校验 `thread_id + proposal_id + checkpoint + writeback_result` 的一致性，并同事务写 audit + completed checkpoint
    - 如需撤销，插件先基于本地快照 rollback，再调用 `/workflows/rollback` 记 rollback 审计
  - 讲清了为什么写回必须由插件执行而不是后端直接改 Vault：
    - 插件掌握当前 Vault 上下文、真实文件 hash 和本地 rollback 快照
    - 后端只负责 workflow 控制面和业务事实，不应越权直改用户本地文件
  - 讲清了 `before_hash` 与 rollback 的安全边界：
    - `before_hash` 本质是乐观并发锁 / stale proposal 防线
    - rollback 只有在当前文件仍命中精确 `after_hash` 时才允许恢复，避免覆盖用户后续手改
  - 已将模块 F 的首轮核心结论写入 `docs/INTERVIEW_PREP_ESSENCE.md`
- 下一步：
  - 进入模块 F 的 2 道场景题，等待用户作答后补高分回答模板

## 用户当前暴露出的知识薄弱点

### 术语与控制面概念

- 一开始对以下概念不熟：
  - LangGraph / 有状态工作流
  - HITL
  - Checkpoint / Thread ID / 恢复机制
- 当前状态：
  - 已能大致理解，但仍需要结合代码不断巩固

### 接口与架构设计

- 对“为什么统一 `/workflows/invoke`、而不是拆 3 个独立 endpoint”最初没有清晰概念
- 对“控制面统一 vs 业务逻辑统一”的区别刚建立
- `runtime contract` 已补过一轮，当前已能理解它是“共享运行协议”，但后续还要继续巩固为什么这里选择半显式 contract，而不是强抽象基类
- 已按用户要求在 `docs/INTERVIEW_PREP_ESSENCE.md` 中新增显式小节：`runtime contract` 是什么
- 对 `envelope` / `payload` 一开始完全不理解，后已解释：
  - `envelope` = 统一外层协议壳
  - `payload` = 业务结果内容
- 后续仍需反复追问 API 演进与解耦问题

### 状态与执行语义

- `thread_id` / `run_id` 的职责边界已经能说出主干，但还不够细，尤其容易把“业务连续性”和“执行可观测性”混在一起
- 下一轮继续巩固“恢复语义 vs 观测语义分离”

### 模块 H 新暴露出的基础概念薄弱点

- 当前对 `观测`、`tracing`、`评估`、`golden set`、`benchmark` 都没有稳定概念
- 最适合的讲解方式是：
  - 先讲“过程数据 vs 结果数据”
  - 再讲“为什么不能只看 demo、也不能只看最终答案”
  - 最后再落到 `runtime_trace.py` 和 `run_eval.py` 的具体代码
- 模块 H 开场应避免直接堆指标名和 schema 字段，先建立“排障”和“验收”两种不同目标
- 当前用户已经建立第一层区别：
  - 观测偏“过程”
  - 评估偏“结果”
- 后续还需要继续纠正：
  - 评估不只看“最终回答文本”，也会评估检索、proposal、resume / writeback 等链路结果
  - 观测也不是“把所有东西无脑全记下来”，而是记录对排障有价值的结构化事件
- 用户已经建立第二层直觉：
  - `JSONL` = 更像原始流水账
  - `SQLite run_trace` = 更像可检索台账
- 用户已经建立第三层直觉：
  - `thread_id` 偏业务连续性
  - `run_id` 偏单次执行可观测性
- 用户已经开始建立第四层直觉：
  - trace 断流的直接后果不是“业务立刻坏掉”，而是“出了问题后更难定位”
  - 后续还要继续补“观测故障不应升级为业务故障”这层工程取舍
- 用户已经开始建立第五层直觉：
  - 业务结果优先于观测补充数据
  - 但后续仍要继续巩固“辅助链路不等于可以长期失控”这层治理意识
- 用户已经开始建立第六层直觉：
  - 观测数据要想可用，前提是字段稳定、可序列化、可查询
  - “原样全收”不等于“更完整”，很多时候只会让后续聚合和分析更差
- 用户已经开始建立第七层直觉：
  - 同一 `run_id` 下的同一节点也可能出现多次事件
  - 事件 identity 不能过粗，否则容易把不同尝试或不同细节误合并
- 用户已经开始建立第八层直觉：
  - `run_id` 更适合查看某一次具体执行
  - `thread_id` 更适合查看同一业务线程在多次执行/恢复中的演进
- 用户即将进入模块 H 第二半，预计会继续暴露以下基础薄弱点：
  - `golden set` 容易被误解成“标准答案全文”
  - `fixture` 容易被误解成“真实线上数据”
  - `eval` 容易被误解成“只看最终分数，不看 contract / fallback / 持久化事实”
- 用户已经建立第一层修正：
  - `golden set` 不是全文标准答案，而是固定 case 集
  - `fixture` 不是线上环境，而是可重复的本地评估环境
- 用户已经建立第二层修正：
  - eval 追求的是结果可重复、可比较
  - 不能让本机 provider / 环境变量把同一 case 跑成两套答案
- 用户已经建立第三层修正：
  - 外部模型和外部服务属于高噪声依赖
  - 离线回归更适合把验证焦点压在 contract、分支和降级行为上
- 用户已经开始建立第四层直觉：
  - eval 不能只比回答文本
  - 但还需要继续纠正：snapshot 关注的不只是“运行过程”，而是“结构化输出 + 副作用事实”是否符合预期
- 用户当前新的基础薄弱点：
  - 在 `resume` 链路里，容易把 API 返回字段、checkpoint 状态、audit 审计和 writeback 执行结果混成一层
  - 需要先建立：
    - contract = 接口约定的数据结构
    - persisted fact = 调用后真正落到库里的事实
- 当前这层已经开始建立第一版区分：
  - `checkpoint` 偏线程状态与恢复语义
  - `audit_log` 偏事件留痕与审计语义
- 用户已经建立第二版区分：
  - HTTP / contract 成功只代表表面返回
  - 真正成功还要看持久化副作用事实是否落对
- 用户接下来大概率会在指标层暴露的薄弱点：
  - 容易把 `groundedness` 和 `faithfulness` 当成一个词
  - 容易把 `context_precision` 和 `context_recall` 混掉
  - 容易把“项目里的近似实现”误当成通用标准定义
- 当前新的薄弱点已经显性化：
  - 对“业界常用概念”和“当前仓库近似实现”之间的差别还没有完全建立
- 当前该薄弱点已完成一轮补课：
  - 用户已能接受“业界常见评估维度”和“当前仓库 interview-first 近似实现”是两层东西
- 当前模块 H 新暴露出的答题薄弱点：
  - 在高风险恢复链路里，容易先看 trace，而不是先看 persisted facts
  - 还需要继续巩固“checkpoint / audit_log / writeback_result 三份事实对账优先于 trace”
- 当前新增的基础概念薄弱点：
  - 容易把“所有记录下来的东西”都统称成 trace
  - 需要明确：
    - trace = 运行时过程观测
    - checkpoint = 恢复状态
    - audit_log = 审计事实
    - snapshot = eval 时临时拼装出的断言视图
- 当前最需要继续巩固的一刀：
  - trace 不是 source of truth
  - audit_log 更接近高风险副作用链路的事实凭证
- 当前这层已建立第一版类比：
  - `trace` = 黑匣子 / 流水账
  - `audit_log` = 审计凭证 / 事实账本
- 当前这层已建立第二版答题直觉：
  - 高风险链路排查顺序应是“先核事实，再补过程”
- 当前模块 H 新暴露出的答题薄弱点：
  - 对“best-effort 观测不拖垮主业务”已经理解
  - 但还不会继续往下回答“那怎么发现断流、怎么治理断流”

### 模块 G 新暴露出的基础概念薄弱点

- 对插件为什么要管理本地 backend runtime 没有直觉，容易把它误解成“只是 UI 上多了一个启动按钮”
- 对 `/health` 探活、`readiness`、`process started` 三者的区别还不清楚
- 对 `auto-start` 的角色还不清楚：它是可用性增强，不是系统正确性的前提
- 对插件入口 `main.ts` 的职责边界需要继续巩固：它主要做装配与调度，不承载 runtime 状态机细节
- 当前最需要的讲解方式是“按单个函数、单个时序”讲，不适合直接堆函数名和抽象分层术语
- 当前用户已开始建立“入口层负责装配，不负责重业务逻辑”的边界感，后续可继续用单函数讲解方式巩固
- 用户已经能理解“后端状态既服务提示也服务界面展示”，下一步可以引入“统一状态快照”的概念，但仍需保持白话解释
- 对“状态快照”还需要继续降维：用户目前能接受“共享状态”，但还未完全建立“为什么不能每次都现查现用”的工程直觉
- 用户对设计模式有直觉，已经开始主动把代码映射到“观察者模式”；后续可以顺势讲“谁订阅、谁发通知、谁消费状态”

### checkpoint 设计取舍

- 已能理解“checkpoint 是为了恢复，不是为了录像”
- 但对“最小充分字段集”和 `required_terminal_fields` 这种工程兜底还不够敏感

### graph 编排理解

- 还需要继续巩固“graph 负责编排，service 负责业务细节”这条边界
- 容易把“拆成三个节点”误解成“只是形式化拆文件”，后续要反复追问为什么 prepare/finalize 有价值
- 对 `ask_graph` 这题已经能回答主干，但还需要把“统一 runtime 语义”和“后续可扩展性”讲得更完整
- 对 `ingest_graph` 已能说出“不是每次都需要 human approval”，但还需要继续加强：
  - 低风险主流程 vs 高风险控制分支的状态边界
  - proposal 语义与 ingest 基础成功语义分离
  - proposal 与 waiting checkpoint 原子落盘的一致性价值
- 对 `digest_graph` 预计会继续暴露的薄弱点：
  - 容易忽略 fallback 设计背后的可用性 trade-off
  - 容易把“结果写回型 proposal”和“内容诊断型 proposal”混为一谈
  - `daily_note / summary_note / generic_note` 这类 note_type 现已补过一轮，但还需要结合 parser 代码继续巩固

### 模块 D 预计考点

- 需要开始巩固“够用解析 vs 过度工程”的取舍
- 后续大概率会在“为什么整 note replace chunk 而不是局部 diff 更新”上被追问
- 用户已主动追问“是不是改一篇 note 就替换它的所有 chunk，为什么不做更细粒度替换”，说明已经开始进入正确的工程取舍层
- 下一轮重点转到“为什么 scoped ingest 仍然全量重建 FTS，以及这带来的性能/一致性 trade-off”
- 模块 D 当前已完成首轮高频追问，后续如回看可再补“embedding provider 故障为什么不回滚主索引”
- 用户刚暴露出对 `Markdown AST / heading / wikilink / task / frontmatter` 这些解析基础术语不熟，需要先补 parser 的最低前置概念
- 用户现在已经能把“够用解析”和 AST 联系起来，但还需要继续纠正：
  - 不是简单把它当成“AST 子集”就结束
  - 更关键的是理解这是有意识的工程取舍：当前没有走完整 AST 路线，而是先抓高价值结构信号
  - 当前已能说出“项目只需要部分高价值信息，而不是完整语法信息”，后续要再补上复杂度、收益和演进顺序这三层
- 用户刚暴露出对 `scoped ingest`、`FTS / chunk_fts` 还不熟，需要先补“局部同步”和“全文检索索引表”这两个概念，再继续回答 FTS 重建取舍

### 模块 E 预计考点

- 大概率会混淆：
  - `retrieval fallback`
  - `model fallback`
  - `vector disabled`
  - `no_hits`
- 用户刚暴露出对以下基础概念还不够稳：
  - “结构化过滤条件”不是 BM25/FTS 本身，而是附加在检索上的 metadata 条件
  - “放宽条件后再做纯检索”不是切到向量检索，而是先去掉这些 metadata filter，再走原本的 retrieval 主链路
  - `retrieval_only` 的含义是“不返回模型生成结论，只返回检索证据及引用”
- 这一轮已补过一轮，当前可以继续进入面试追问，不必再停留在概念扫盲
- 用户在模块 E 的第 1 道题里已经能抓到“失败链路分离”和“可诊断性”主干，但还需要继续强化：
  - 不能只停在“这是两个步骤”
  - 要能继续说出“不同优化动作、不同告警面、不同用户提示、不同可信度解释”
- 用户在模块 E 的第 2 道题里已经能抓到“citation 失配 = 可能幻觉”这层，但还需要继续强化：
  - 当前系统为什么选择“直接不放生成答案”，而不是“继续展示并附低置信标签”
  - ask 的可信边界本质上是“结论必须回指到当前证据集合”
- 用户在“规模放大 100 倍先炸哪层”这道题里已经能判断：
  - 最先出硬瓶颈的是当前 vector retrieval implementation
  - RRF 和 groundedness 更偏质量上限问题
- 用户接下来大概率会在以下点上被追问：
  - 为什么 RRF 只是阶段性方案
  - 为什么 Python 侧全量向量扫描不适合大规模
  - 为什么“有 citation”仍可能不 grounded
- 容易把“citation 编号对齐校验”误认为“已经完成语义级 groundedness”
- 这一轮已补过“编号层 vs 语义层”的差异，后续可以继续进入模块 E 收束，不必再回到最基础概念
- 模块 E 当前已完成首轮收束，后续如回看，重点复盘：
  - fallback taxonomy
  - citation alignment vs groundedness
  - vector retrieval 的规模化瓶颈
- 容易把 hybrid 回答成“行业标准组合拳”，但讲不清为什么这里先用 RRF、而不是直接做线性加权或 rerank
- 容易忽略 contract 价值：
  - ask 并不是直接返回一段字符串
  - 中间显式保留了 candidate、citation、fallback reason 和 provider/model 信息，便于调试、审计和评估

### 模块 F 预计考点

- 大概率会混淆：
  - proposal store
  - checkpoint store
  - audit log
  - 插件本地 writeback / rollback
- 接下来重点观察用户是否能真正讲清：
  - 为什么 `thread_id` 和 `proposal_id` 两层身份都必须带
  - 为什么 proposal 与 waiting checkpoint 必须原子落盘
  - 为什么写回必须在插件本地执行，而不是后端直接改 Vault
  - 为什么 `before_hash` 只是最小并发锁，不等于完整事务
  - 为什么 rollback 故意只支持当前插件会话内的本地快照恢复
- 当前已完成的纠偏：
  - 用户一开始容易把“有 proposal”直接等同于“流程已经进入 waiting”，现已纠正为“业务事实 vs 流程事实”
  - 用户刚补清了 `resume`、`pending inbox`、重复审批控制、`patch_ops` 的基础含义
  - 用户对“副作用面已成功、控制面未记账”的双面一致性问题已补过一轮，当前已能说出：
    - 当前实现只是同会话内 retry sync
    - 不是完整跨会话补偿
    - 生产上要引入 outbox / idempotency / reconciliation
  - 用户已经补清 `before_hash`：
    - 何时生成
    - 何时校验
    - 为什么 mismatch 时还要区分“已应用过”与“陈旧 proposal”
    - 为什么受限 patch 比自由 diff 更容易做 `already applied` 检查
  - 用户已经补清 `after_hash / rollback`：
    - 需要把 `before_hash` 和 `after_hash` 放回同一条时间线理解
    - rollback 拒绝的本质是“避免覆盖写回后用户又做的新修改”
- 如果用户回答里只停在“更安全”“避免出错”这类空话，下一轮要继续往下压：
  - source of truth 分层
  - 控制面与副作用面分离
  - 双面一致性失败后的补偿设计
  - 保守拒绝优于危险自动修复

## 文档状态

- `docs/INTERVIEW_PREP_ESSENCE.md` 当前已是最新状态，已经覆盖：
  - Step 1 结论
  - Step 2 结论
  - Step 3 模块拆分计划
  - 模块 A 精读结论与追问题库
  - 模块 B 精读结论与追问题库
  - 模块 C 的 `ask_graph` 首轮精读结论与追问题库
  - 模块 C 的 `ingest_graph` 首轮精读结论与追问题库
  - 模块 C 的 `digest_graph` 首轮精读结论与追问题库
  - 模块 C 的总收束结论
  - 模块 D 的首轮主链路结论与 1 道追问题库
  - 模块 D 的第 2 / 第 3 道追问题库
  - 模块 D 的首轮收束结论
  - 模块 E 的首轮主链路结论
  - 模块 E 的 4 道追问题库、规模化瓶颈回答与首轮收束
  - 模块 F 的首轮主链路结论与安全边界总结
  - 模块 F 的两道场景题与参考回答
  - 方案 B 的增量设计、实现边界、面试表达与验证结果
- 新会话中不要重复回顾全部旧内容，优先：
  1. 读本文件
  2. 读 `docs/INTERVIEW_PREP_ESSENCE.md`
  3. 优先读取本文件顶部“2026-03-23 最新断点”
  4. 先讲方案 B 的面试表达或回读方案 B 增量主链路
