# Adaptation Notes

## 1. 什么时候适合直接用这套 starter

适合：

- 需要跨多个会话持续推进的项目
- 需要任务绑定、会话日志、动态控制面的项目
- 希望后续做 prompt 模板和 skill 化复用的项目

不适合：

- 一次性实验仓库
- 没有持续 handoff 需求的小项目

## 2. 哪些字段必须替换

至少应替换：

- `{{PROJECT_NAME}}`
- `{{PROJECT_SUBTITLE}}`
- `{{PROJECT_POSITIONING}}`
- `{{CAPABILITY_*}}`
- `{{OWNER}}`
- 第一条 `{{TASK_ID}}` 与对应 goal

## 3. 哪些机制不要轻易改

不建议一上来就改：

- 单会话单 `medium`
- `session_id` 唯一性规则
- `CURRENT_STATE` 作为唯一动态控制面
- Level 1 / 2 / 3 收尾分层

这些是治理结构本身，不是项目特例。

## 4. 提示词如何使用

- `assets/prompts/start-prompt.template.md`：适合启动新会话时注入项目元信息
- `assets/prompts/close-prompt.template.md`：适合显式触发收尾与文档同步

如果运行环境已经能稳定显式调用 `$project-session-governor`，提示词可以进一步变薄。
