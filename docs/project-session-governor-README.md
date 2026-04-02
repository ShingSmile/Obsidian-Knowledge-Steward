# Project Session Governor README

## 1. 这是什么

`project-session-governor` 是一个通用的项目会话治理 skill，用来解决“多会话开发项目如何稳定接手、控 scope、做收尾同步”的问题。

它不负责替你写业务代码本身，而是负责约束和编排以下流程：

- 会话启动时如何读文档和代码
- 如何绑定唯一的 `medium` 任务
- 如何分配或检查 `session_id`
- 如何在执行中防止范围失控
- 如何在收尾时判断文档更新级别
- 如何把更新路由到正确的文档层

它适合：

- 正在开发中的项目
- 需要跨多个会话持续推进的项目
- 已经有或准备建立任务队列、当前状态、会话日志等治理文档的项目

它不适合：

- 一次性脚本
- 很小的临时仓库
- 纯 brainstorming、没有任务绑定的对话

## 2. skill 文件位置

当前仓库中的 skill 源文件位于：

- [skills/project-session-governor/SKILL.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/skills/project-session-governor/SKILL.md)
- [skills/project-session-governor/agents/openai.yaml](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/skills/project-session-governor/agents/openai.yaml)
- [skills/project-session-governor/assets/project-starter/README.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/skills/project-session-governor/assets/project-starter/README.md)
- [skills/project-session-governor/assets/prompts/start-prompt.template.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/skills/project-session-governor/assets/prompts/start-prompt.template.md)
- [skills/project-session-governor/assets/prompts/close-prompt.template.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/skills/project-session-governor/assets/prompts/close-prompt.template.md)
- [skills/project-session-governor/scripts/init_project_governance.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/skills/project-session-governor/scripts/init_project_governance.py)

说明：

- 现在 starter 文档骨架、提示词模板和初始化脚本都已经并入 skill 本身。
- 这个文件继续放在 `docs/` 下，作用是作为人读的总说明，而不是 machine-facing skill 资源。

## 3. skill 假定的文档分层

这个 skill 默认假设项目尽量接近以下文档职责：

- `docs/TASK_QUEUE.md`：任务绑定入口
- `docs/CURRENT_STATE.md`：唯一动态控制面
- `docs/SESSION_LOG.md`：近期会话交接
- `docs/archive/session_logs/`：历史会话归档
- `docs/PROJECT_MASTER_PLAN.md`：稳定架构、边界、风险、路线原则
- `README.md`：启动方式、目录导航、演示入口
- `docs/INTERVIEW_PLAYBOOK.md`：面试叙事与追问库，可选
- `docs/CHANGELOG.md`：版本与里程碑记录，可选

如果项目没有这些文件，skill 会进入降级模式：

- `minimal`：只用现有的少量治理文档工作
- `bootstrap`：明确指出治理文档缺失，先建议补最小骨架

## 4. 这个 skill 到底帮你做什么

### 4.0 用户只需要记住的三个入口

从实用性看，默认只需要记住三句话：

1. `Use $project-session-governor to bootstrap governance for this repo.`
2. `Use $project-session-governor to start a governed session in this repo.`
3. `Use $project-session-governor to close the current governed session.`

这三个入口分别对应：

- 初始化项目治理骨架
- 开始一次正式开发会话
- 结束一次正式开发会话

脚本是 skill 的内部工具，不是用户的主要入口。

### 4.1 启动阶段

它会按固定顺序读取上下文，而不是通读整个仓库历史：

1. `TASK_QUEUE`
2. `CURRENT_STATE`
3. 最近相关 `SESSION_LOG`
4. 按需读取 `PROJECT_MASTER_PLAN`
5. 按需读取 `README`
6. 按需读取 `INTERVIEW_PLAYBOOK`
7. 按需读取 `CHANGELOG`
8. 最相关的 3～5 个代码入口文件

然后输出结构化“会话启动分析”，包括：

- 阅读证据
- 会话绑定结果
- 当前项目状态理解
- 本会话边界
- 执行计划

### 4.2 执行阶段

它会持续约束：

- 一个会话只能做一个 `medium`
- 新发现的 `medium` 不能顺手继续做
- 代码和文档不一致时，先指出，再记 `tail_sync_item`
- 代码实现阶段不提前修改项目文档
- 绑定任务一旦完成且验证通过，应及时形成一个边界清晰的 git commit，不要让多个已完成任务长期堆在未提交工作区，尤其不要继续积压在 `main`

### 4.3 收尾阶段

它会把收尾分成三档：

- `Level 1`：只更新 `SESSION_LOG`
- `Level 2`：更新 `SESSION_LOG + TASK_QUEUE + CURRENT_STATE`
- `Level 3`：在 Level 2 基础上，按实际影响选择性更新稳定主文档

它不会要求“每次都全量更新所有文档”。

## 5. 推荐的新项目使用方式

面对一个全新项目，推荐按下面顺序使用。

### 5.1 先用 bootstrap 入口初始化最小骨架

推荐默认这样触发：

```text
Use $project-session-governor to bootstrap governance for this repo.
```

在 bootstrap 模式里，skill 应先收集或推断：

- 项目名
- 副标题
- 项目定位
- 2～4 条核心能力
- 是否启用 `INTERVIEW_PLAYBOOK`
- 是否启用 `CHANGELOG`
- 第一条 `TASK-001`

然后再决定是否内部调用 `scripts/init_project_governance.py` 来稳定生成 starter 文档骨架。

只有在你明确想绕过 skill、直接做确定性初始化时，才需要手工执行脚本。

### 5.2 再接入薄提示词

启动提示词只负责：

- 项目名称
- 副标题
- 项目定位
- 核心能力
- 项目级硬约束

结束提示词只负责：

- 触发收尾
- 要求按真实改动判断更新级别
- 要求生成结构化 handoff

不要再把完整治理逻辑继续硬编码进超长 prompt。

### 5.3 让 skill 承担流程

这个 skill 应该承接真正的流程编排：

- 读取顺序
- task binding
- `session_id` 规则
- 启动分析模板
- 执行期 guardrails
- 收尾 Level 1 / 2 / 3
- 文档更新路由

## 6. 怎么触发这个 skill

如果你的运行环境支持显式 skill 调用，推荐优先用这三个入口：

```text
Use $project-session-governor to bootstrap governance for this repo.
Use $project-session-governor to start a governed session in this repo.
Use $project-session-governor to close the current governed session.
```

如果你使用的是自定义启动提示词，则可以直接基于：

- [skills/project-session-governor/assets/prompts/start-prompt.template.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/skills/project-session-governor/assets/prompts/start-prompt.template.md)
- [skills/project-session-governor/assets/prompts/close-prompt.template.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/skills/project-session-governor/assets/prompts/close-prompt.template.md)

做项目级替换，而不需要再手工拼装整套提示词。

## 7. 和启动 / 结束提示词怎么配合

### 启动提示词负责什么

负责注入：

- 项目元信息
- 项目目标
- 核心能力
- 会话级硬约束

### skill 负责什么

负责执行：

- 读哪些文件
- 怎么挑 task
- 怎么分配 `session_id`
- 怎么输出“会话启动分析”
- 怎么做收尾判断

### 结束提示词负责什么

负责触发：

- closeout 模式
- 更新级别判断
- 交接摘要生成

## 8. 在新项目里迁移时需要替换什么

你通常只需要替换：

- 项目名称
- 副标题
- 项目定位
- 核心能力
- 项目自己的文档路径约定
- 是否启用 `INTERVIEW_PLAYBOOK`
- 是否启用 `CHANGELOG`

你不应该替换：

- 单会话单 `medium` 的规则
- `session_id` 的唯一性原则
- 启动分析的结构
- 收尾 Level 1 / 2 / 3 的分层思想

这些属于通用治理机制，不属于单项目特例。

## 9. 当前已知边界

这个 skill 当前仍有意保持保守边界：

- 只定义会话治理，不定义业务架构
- 不替代 coding / debugging / review 技能
- 不自动脑补项目事实；bootstrap 仍要先做项目信息 intake
- 不把全部项目特性吸进 skill 内部

这是刻意的。它的目标是稳定复用，而不是把任何项目都做成重型元框架。

## 10. 推荐的下一步

如果你接下来要真正跨项目复用它，最合理的下一步是：

1. 把这个 skill 安装到全局 `~/.codex/skills/`
2. 在一个新项目里试跑三条入口命令
3. 把启动/结束提示词进一步压缩为“薄提示词”
4. 在第 2 个项目里再验证一次它是否还足够通用
4. 在 1 到 2 个新项目里试跑，验证它是否还足够通用

## 11. 一句话总结

`project-session-governor` 不是用来替你开发功能的，而是用来确保你在一个正在开发中的项目里，始终知道：

- 现在该读什么
- 这次到底做什么
- 什么不能顺手做
- 收尾该更新哪些文档

它的真正价值是降低多会话开发中的上下文混乱和治理漂移。
