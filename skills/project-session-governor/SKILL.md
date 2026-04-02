---
name: project-session-governor
description: Use when taking over an in-progress software project with task, status, or session docs and you need to bind one medium task, control execution scope, or perform structured session closeout.
---

# 项目会话治理器

## 概述

这个 skill 用于“正在开发中的项目”，前提是项目需要跨多个会话持续推进，并依赖仓库内的治理文档，而不是只靠聊天历史维持上下文。

它主要解决五件事：

1. 用最少但足够的上下文启动会话
2. 绑定唯一一个 `medium` 任务
3. 在执行过程中防止 scope 漂移
4. 在收尾时判断正确的文档同步级别
5. 在新项目里快速初始化 starter 文档骨架、提示词模板和治理流程

不要把它用于：

- 一次性脚本
- 很小的临时仓库
- 纯 brainstorming、没有任务绑定的对话

内置资源：

- starter 文档骨架：`assets/project-starter/`
- 提示词模板：`assets/prompts/`
- 初始化脚本：`scripts/init_project_governance.py`
- 适配说明：`references/adaptation-notes.md`

## 三个入口命令

默认通过以下三条用户入口命令使用本 skill：

1. `Use $project-session-governor to bootstrap governance for this repo.`
2. `Use $project-session-governor to start a governed session in this repo.`
3. `Use $project-session-governor to close the current governed session.`

把这三条理解成一个 skill 的三种模式，而不是三个独立 skill。

默认原则：

- 用户调用 skill
- skill 自己决定现在该读文档、做 intake，还是内部调用初始化脚本
- 不要求用户自己记脚本路径

## 期望的文档结构

优先适配以下结构：

- `docs/TASK_QUEUE.md`：任务事实来源
- `docs/CURRENT_STATE.md`：唯一动态控制面
- `docs/SESSION_LOG.md`：近期会话证据
- `docs/archive/session_logs/`：历史会话归档
- `docs/PROJECT_MASTER_PLAN.md`：稳定架构、边界、风险、路线原则
- `README.md`：启动方式、目录导航、演示入口
- `docs/INTERVIEW_PLAYBOOK.md`：可选的面试叙事文档
- `docs/CHANGELOG.md`：可选的版本历史文档

如果这些文件不完整，不要假装还能按 full profile 正常运行。应降级到 `minimal` 或 `bootstrap`，并明确指出缺了什么。

## 三种运行档位

### 完整档 `Full`

当以下文件都存在时，使用完整工作流：

- `docs/TASK_QUEUE.md`
- `docs/CURRENT_STATE.md`
- `docs/SESSION_LOG.md`

### 降级档 `Minimal`

当只有部分治理文档存在时，使用降级工作流。

规则：

- 任务事实优先看 `TASK_QUEUE`
- 当前状态优先看 `CURRENT_STATE`
- 近期执行事实优先看最近相关 `SESSION_LOG`
- 明确指出缺失的治理文档

### 引导档 `Bootstrap`

当项目还没有任务/会话治理骨架时，使用 bootstrap 模式。

在 bootstrap 模式下：

- 不要假装正常会话已经可以开始
- 先建议建立最小治理文档骨架
- 先做项目信息 intake
- 若需要稳定落盘 starter 文件，可把 `scripts/init_project_governance.py` 当成内部 helper 来用

### Bootstrap 信息采集

在生成 starter 文档前，先收集或推断以下字段：

- 项目名称
- 副标题
- 项目定位
- 2～4 条核心能力
- 如有必要，项目 owner / maintainer
- 是否需要 `INTERVIEW_PLAYBOOK`
- 是否需要 `CHANGELOG`
- 第一条可执行的 `TASK-001`

只有当这些字段无法从用户请求或仓库现状中安全推断时，才补问。

## 开始会话

当用户要求你继续开发、接手仓库或开始新一轮实现会话时，进入这个模式。

### 读取顺序

除非用户另有要求，按以下顺序读取：

1. `docs/TASK_QUEUE.md`
2. `docs/CURRENT_STATE.md`
3. `docs/SESSION_LOG.md` 中最相关的最近一条记录
4. 只有在需要时，再读取 `docs/archive/session_logs/` 对应归档
5. 只有任务涉及架构、路线、边界或风险时，再读 `docs/PROJECT_MASTER_PLAN.md`
6. 只有启动、导航、演示方式相关时，再读 `README.md`
7. 只有面试输出相关时，再读 `docs/INTERVIEW_PLAYBOOK.md`
8. 只有里程碑或版本同步相关时，再读 `docs/CHANGELOG.md`
9. 最后读取最相关的 3～5 个代码入口文件

不要默认通读整个会话日志或全部归档。

### 任务选择

按以下优先级选择本会话任务：

1. 用户显式指定的任务或目标
2. `docs/TASK_QUEUE.md` 中最合适的可执行 `medium`
3. `docs/CURRENT_STATE.md` 中的默认下一任务
4. 最近相关 `SESSION_LOG` 中仍未完成的下一步
5. `docs/PROJECT_MASTER_PLAN.md` 中相关的稳定路线约束

如果多个任务都看起来合理，必须说明：

- 为什么选当前这个
- 为什么另外几个现在不做

### 会话 ID

`session_id` 必须遵循：

- `SES-YYYYMMDD-XX`

分配前必须检查：

- `docs/TASK_QUEUE.md`
- `docs/SESSION_LOG.md`
- 若存在，再检查 `docs/archive/session_logs/`

规则：

- 如果当前 task 已预分配 `session_id`，优先使用
- 否则使用当天未占用的下一个顺序号
- 绝不复用已存在的 `session_id`

### 启动阶段必须输出

在开始实现前，必须输出一份结构化“会话启动分析”，包含：

1. 阅读证据
2. 会话绑定结果
3. 当前项目状态理解
4. 本会话边界
5. 执行计划

至少要写明：

- 已读取文件
- 每个文件的一句话结论
- 选定的 `task_id`
- 选定的 `session_id`
- 本会话唯一目标
- 明确的 out-of-scope
- 3～5 个关键代码入口文件
- 当前代码/文档是否不一致
- 当前动态控制面是否不一致

## 执行期守卫

在执行过程中使用这个模式。

### 核心规则

- 一个会话只能拥有一个 `medium` 任务
- `small` 伴随改动只允许服务当前绑定任务
- 如果执行过程中出现新的 `medium`，必须停止扩张并建议拆分
- 不得把未验证的推测写成已完成事实
- 在用户显式要求收尾前，代码实现阶段不要提前改项目文档
- 当绑定任务已经完成且验证通过时，应尽快形成一个只包含该任务相关改动的 git commit；不要把多个已完成任务长期堆在未提交工作区里，尤其不要继续积压在 `main`

### 代码与文档不一致

如果代码与文档不一致：

1. 先明确指出不一致点
2. 说明当前哪一层文档应被视为该事实的主来源
3. 记录一个 `tail_sync_item`
4. 如果继续执行是安全的，再继续
5. 不要在中途静默改文档

### 事实优先级

当不同文档冲突时，默认优先级如下：

1. `docs/TASK_QUEUE.md`：任务事实
2. `docs/CURRENT_STATE.md`：当前动态状态
3. 最近相关 `docs/SESSION_LOG.md`：近期执行事实
4. `docs/PROJECT_MASTER_PLAN.md`：稳定架构事实
5. `README.md`：onboarding 事实

不要让 README 或旧主文档里的“下一步”覆盖当前 task 状态。

## 会话收尾

当用户要求收尾、交接或文档同步时，进入这个模式。

### 更新级别

#### Level 1

只更新：

- `docs/SESSION_LOG.md`

适用场景：

- 主要是阅读、调试、验证或局部小修
- 没有任务状态变化
- 没有新的 `derived_tasks`
- 没有 `CURRENT_STATE` 变化
- 没有稳定主文档事实变化

#### Level 2

更新：

- `docs/SESSION_LOG.md`
- `docs/TASK_QUEUE.md`
- `docs/CURRENT_STATE.md`

适用场景：

- task 状态发生变化
- 新增了 `derived_tasks`
- task 的 notes 或 related files 变化
- 默认下一任务变化
- 当前阶段或活动风险变化
- 执行事实变化，但架构未变化

#### Level 3

先完成 Level 2，再按实际影响选择性更新：

- `docs/PROJECT_MASTER_PLAN.md`
- `README.md`
- `docs/INTERVIEW_PLAYBOOK.md`
- `docs/CHANGELOG.md`

适用场景：

- 架构变化
- 技术路线变化
- 模块边界变化
- onboarding / 启动方式变化
- 面试叙事变化
- 需要记录里程碑或版本
- 稳定主文档与当前代码事实不一致

不要一进入 Level 3 就把所有稳定文档都顺手更新，必须按影响路由。

### 收尾阶段必须输出

必须按以下顺序输出：

1. 更新级别判断
2. 可直接追加到 `docs/SESSION_LOG.md` 的 handoff 摘要
3. 如果 Level >= 2，给出 `docs/TASK_QUEUE.md` 和 `docs/CURRENT_STATE.md` 的更新点
4. 如果 Level = 3，给出受影响稳定文档的更新点
5. 最后给一个简短摘要，至少包括：
   - 更新级别
   - 需要更新的文件
   - 当前任务状态是否变化
   - 是否新增 `derived_tasks`
   - 是否需要新开会话
   - 当前代码、动态控制面、稳定主文档是否仍不一致

### 交接摘要必填字段

`SESSION_LOG` 的交接摘要至少覆盖：

1. 本次目标
2. 本次完成内容
3. 本次未完成内容
4. 关键决策
5. 修改过的文件
6. 验证与测试
7. 范围偏移
8. 未解决问题
9. 新增风险 / 技术债 / 假设
10. 下一步最优先任务
11. 下一次新会话先读哪些文件
12. 当前最容易被追问的点

## 引导式治理初始化

当仓库还不支持结构化会话治理时，进入这个模式。

至少建议创建：

- `README.md`
- `docs/TASK_QUEUE.md`
- `docs/CURRENT_STATE.md`
- `docs/SESSION_LOG.md`
- `docs/PROJECT_MASTER_PLAN.md`

可选后补：

- `docs/INTERVIEW_PLAYBOOK.md`
- `docs/CHANGELOG.md`
- `docs/archive/`

在 bootstrap 模式下，不要声称“正常 task 绑定会话已经可以开始”。

如果用户要求你快速初始化一个新项目：

1. 读取 `references/adaptation-notes.md`
2. 做 bootstrap intake
3. 仅在需要稳定落盘时，把 `scripts/init_project_governance.py` 当作内部 deterministic helper 使用
4. 从 `assets/project-starter/` 初始化 starter 文档骨架
5. 告诉用户可复用的启动提示词模板在 `assets/prompts/start-prompt.template.md`
6. 告诉用户可复用的结束提示词模板在 `assets/prompts/close-prompt.template.md`

## 常见错误

- 每次都通读整个 `SESSION_LOG`
- 把 `docs/PROJECT_MASTER_PLAN.md` 当成动态控制面
- 让 README 承担当前下一任务
- 在 task binding 前直接开始实现
- 中途顺手推进第二个 `medium`
- 收尾时不做影响路由，直接全量更新文档
- 用归档日志覆盖当前任务事实
- 复用已有 `session_id`

## 失败处理

### 缺少关键文档

如果治理文档缺失：

- 明确说出缺了哪些
- 降级到 `minimal` 或 `bootstrap`
- 说明哪些判断因此无法可靠完成

### 任务不明确

如果正确 task 不明确：

- 列出候选项
- 选一个并解释原因
- 说明其他候选项为什么暂不选择

### 文档冲突

如果治理文档互相冲突：

- 明确冲突点
- 按优先级处理
- 把它写成一个待收尾同步项

### 收尾级别难判断

如果更新级别不确定：

- 默认选更高一级
- 但必须解释原因

## 提示词边界

这个 skill 应承载工作流本身。项目级提示词只负责提供：

- 项目名称
- 副标题
- 项目定位
- 核心能力
- 项目级硬约束

不要在项目级提示词里重复写本 skill 已经定义好的治理流程。

从用户入口看，应优先使用前面的三条入口命令，而不是告诉用户去手工执行脚本。

若需要可复用的提示词壳，请使用：

- `assets/prompts/start-prompt.template.md`
- `assets/prompts/close-prompt.template.md`

## 成功标准

如果这个 skill 是有效的，它应能稳定帮助 agent：

- 不通读无关历史也能启动会话
- 稳定绑定一个 `medium` 任务
- 防止 scope 漂移
- 显式指出代码/文档不一致
- 正确判断收尾级别
- 把文档更新路由到正确层级
