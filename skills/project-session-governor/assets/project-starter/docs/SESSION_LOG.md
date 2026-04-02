# Session Log

## 使用规则

- 本文件用于累计记录多个开发会话，必须持续追加，不允许每次覆盖重写。
- 每次会话都必须分配唯一会话 ID，格式统一为 `SES-YYYYMMDD-XX`。
- 新会话默认追加在文件顶部；旧会话只允许补充勘误，不允许重写结论。
- 所有新会话都必须先绑定 `docs/TASK_QUEUE.md` 中的一个任务项，再开始执行。

## 会话索引

| 会话 ID | 日期 | 主题 | 类型 | 状态 | 对应任务 |
| --- | --- | --- | --- | --- | --- |

---

## [{{SESSION_ID}}] {{SESSION_TITLE}}

- 日期：{{DATE}}
- task_id：`{{TASK_ID}}`
- 类型：`{{SESSION_TYPE}}`
- 状态：`{{STATUS}}`
- 验收结论：`{{ACCEPTANCE_RESULT}}`
- 对应任务：`{{TASK_ID}}`
- 本会话唯一目标：{{SESSION_GOAL}}

### 1. 本次目标

- {{GOAL_1}}

### 2. 本次完成内容

- {{DONE_1}}
- {{DONE_2}}

### 3. 本次未完成内容

- {{TODO_1}}

### 4. 关键决策

- {{DECISION_1}}

### 5. 修改过的文件

- `{{FILE_1}}`
- `{{FILE_2}}`

### 6. 验证与测试

- 跑了什么命令
  - `{{CMD_1}}`
- 结果如何
  - {{TEST_RESULT}}
- 哪些没法验证
  - {{UNVERIFIED}}
- 哪些只是静态修改
  - {{STATIC_ONLY}}

### 7. 范围偏移与原因

- {{SCOPE_SHIFT}}

### 8. 未解决问题

- {{OPEN_ISSUE_1}}

### 9. 新增风险 / 技术债 / 假设

- {{RISK_1}}

### 10. 下一步最优先任务

- `{{NEXT_TASK_ID}}`：{{NEXT_TASK_TITLE}}

### 11. 下一次新会话应该先读哪些文件

- `{{NEXT_FILE_1}}`
- `{{NEXT_FILE_2}}`

### 12. 当前最容易被追问的点

- {{INTERVIEW_POINT}}
