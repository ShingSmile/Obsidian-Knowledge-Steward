请使用 `$project-session-governor` 的 closeout 工作流，基于本次会话真实改动执行一次“会话收尾与项目文档同步”。

当前文档职责分层如下：
- `docs/TASK_QUEUE.md`：任务绑定与任务事实
- `docs/CURRENT_STATE.md`：唯一动态控制面
- `docs/SESSION_LOG.md`：近期会话记录
- `docs/archive/session_logs/`：历史会话归档
- `docs/PROJECT_MASTER_PLAN.md`：稳定架构、边界、风险、路线原则
- `README.md`：启动方式、目录导航、演示入口
- `docs/INTERVIEW_PLAYBOOK.md`：面试问答与叙事口径（如果存在）
- `docs/CHANGELOG.md`：版本与里程碑变更记录（如果存在）

要求：

1. 先判断本次会话属于 Level 1 / Level 2 / Level 3
2. 再生成可直接追加到 `docs/SESSION_LOG.md` 的交接摘要
3. 若 Level >= 2，再给出 `docs/TASK_QUEUE.md` 和 `docs/CURRENT_STATE.md` 的更新点
4. 若 Level = 3，再按实际影响给出稳定主文档更新点
5. 最后输出一个简短总结，说明：
   - 更新级别
   - 应更新文件
   - 当前任务状态是否变化
   - 是否新增派生任务
   - 是否需要新开下一会话
   - 当前代码、动态控制面与稳定主文档是否仍存在不一致
