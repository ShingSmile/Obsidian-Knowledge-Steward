你现在接手的是一个正在开发中的项目，不是从零开始。

项目名称：
{{PROJECT_NAME}}

副标题：
{{PROJECT_SUBTITLE}}

项目定位：
{{PROJECT_POSITIONING}}

核心能力包括：
- {{CAPABILITY_1}}
- {{CAPABILITY_2}}
- {{CAPABILITY_3}}
- {{CAPABILITY_4}}

当前文档职责分层如下：
- `docs/TASK_QUEUE.md`：会话任务绑定入口
- `docs/CURRENT_STATE.md`：唯一动态控制面
- `docs/SESSION_LOG.md`：近期会话证据与交接
- `docs/archive/session_logs/`：历史会话归档
- `docs/PROJECT_MASTER_PLAN.md`：稳定架构、边界、风险、路线原则
- `README.md`：启动方式、目录导航、演示入口
- `docs/INTERVIEW_PLAYBOOK.md`：面试问答与叙事口径（如果存在）
- `docs/CHANGELOG.md`：版本与里程碑记录（如果存在）

你必须严格遵守以下规则：

1. 以代码和文档为准，不要脑补未实现功能。
2. 不要把废弃方案当成当前方案。
3. 本会话只能解决一个 `scope=medium` 的任务。
4. 本会话必须绑定 `docs/TASK_QUEUE.md` 中的一个任务项。
5. 允许为了完成本会话唯一目标而进行必要的伴随改动，但不允许借此推进新的 `medium` 功能。
6. 若发现未登记的轻量派生子任务，可建议补入 `derived_tasks` 并继续。
7. 若发现新的 `medium` 或更大任务，必须先停止扩张，提出拆分与登记建议。
8. 若发现代码与文档不一致，先指出不一致，再继续实现。
9. 在我显式发送“执行会话收尾与项目文档同步”之前，不要提前修改项目文档。

请使用 `$project-session-governor` 的工作流来：

1. 锁定本会话任务
2. 分配或确认 `session_id`
3. 输出“会话启动分析”
4. 在分析完成前不要直接编码
