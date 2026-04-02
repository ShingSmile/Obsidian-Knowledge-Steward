# TASK_QUEUE

本文件是会话级任务的唯一队列来源。
所有新会话必须先绑定本文件中的一个任务项，再开始执行。

## Queue Rules

- 一个会话只能绑定一个 `scope=medium` 的任务项。
- `small` 任务只能作为当前任务的伴随改动或 `derived_tasks` 存在，不能单独开启一个新会话。
- `large` 任务必须先拆分为多个 `medium` 任务后才能开工。
- 会话结束后必须同步更新：
  - 本文件中的任务状态、`session_id`、备注和派生子任务
  - `docs/SESSION_LOG.md`
  - `docs/CURRENT_STATE.md`
- 若本次会话改变了架构、主路线、模块边界或稳定主文档事实，还必须同步更新相关稳定文档。

## Status Conventions

- `planned`
- `in_progress`
- `blocked`
- `completed`
- `cancelled`

## Scope Conventions

- `small`
- `medium`
- `large`

## Task Fields

- `task_id`
- `session_id`
- `title`
- `category`
- `priority`
- `status`
- `scope`
- `goal`
- `out_of_scope`
- `acceptance_criteria`
- `depends_on`
- `related_files`
- `derived_tasks`
- `notes`

## Active Tasks

### {{TASK_ID}}

- `task_id`: `{{TASK_ID}}`
- `session_id`:
- `title`: {{TASK_TITLE}}
- `category`: `{{TASK_CATEGORY}}`
- `priority`: `{{TASK_PRIORITY}}`
- `status`: `planned`
- `scope`: `medium`
- `goal`: {{TASK_GOAL}}
- `out_of_scope`:
  - {{OUT_OF_SCOPE_1}}
  - {{OUT_OF_SCOPE_2}}
- `acceptance_criteria`:
  - {{AC_1}}
  - {{AC_2}}
  - {{AC_3}}
- `depends_on`:
  - `{{DEPENDS_ON_1}}`
- `related_files`:
  - `{{FILE_1}}`
  - `{{FILE_2}}`
- `derived_tasks`: []
- `notes`: {{TASK_NOTES}}
