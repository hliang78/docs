# Config Management Collection Task Center Acceptance

Date: 2026-06-07

## Scope

- [x] 配置管理新增 `配置版本 / 采集任务` 工作模式。
- [x] 配置版本队列支持立即采集、采集当前筛选队列、重新采集失败资产。
- [x] 采集动作通过真实任务创建接口发起，不使用占位反馈。
- [x] 网络设备和服务器配置采集共用一套前端分组与任务创建 helper。
- [x] 一次性采集支持按资产类型和访问平面自动拆分任务。
- [x] 定时采集支持创建、启停、删除、查看最近运行。
- [x] 一次性采集历史只展示 `manual` / `retry` 且非定时任务的运行记录。
- [x] 成功创建采集任务后自动进入采集任务中心查看进度。
- [x] quick env 的 Gitea source repo bundle 已同步服务器配置采集模板。
- [x] 当前运行环境已重新导入变量组和任务模板，能查到服务器配置采集模板。

## User-Facing Flow Acceptance

- [x] 从配置版本队列选择资产，点击 `立即采集` 后创建采集任务并进入 `采集任务`。
- [x] 未选择资产时点击 `采集当前筛选队列`，需要确认当前筛选队列后才能提交。
- [x] 点击 `重新采集失败资产` 会对失败资产发起 retry 采集。
- [x] 单资产侧栏中的 `重试备份` / `重新采集` 走同一套真实任务创建链路。
- [x] 缺少网络或服务器采集模板时，页面显示真实跳过原因。
- [x] 接口未返回任务 ID 或创建失败时，不报假成功。
- [x] 创建定时采集后进入 `采集任务`，可查看定时任务列表。
- [x] 定时任务运行记录通过 `查看运行` 进入任务管理页。
- [x] 配置版本队列表格补充资产名称、IP、厂商型号、在线状态等常用信息。

## Backend Verification Evidence

- `go test ./app/platform/service/impl -run 'TestScheduledTaskRunner_RunOne' -count=1` -> exit 0.
- Added scheduled runner guard coverage for config collection:
  - forwards `project-network-config-management`
  - forwards `template_id`
  - forwards `device_codes`
  - forwards `access_plane`
  - preserves `triggered_by=scheduled`
  - records scheduled task run after task creation

## Frontend Verification Evidence

- `npm run typecheck` was run after Task 6 -> exit 0.
- Frontend worker ran `npm run typecheck` after implementing Task 7 -> reported exit 0.
- `npm run typecheck` was run again after Task 7 quality fixes -> exit 0.

## Quick Env Verification Evidence

- `git bundle verify /OneOPS/quick_env/init-configs/gitea/source-repo.bundle` -> exit 0.
- Bundle HEAD now points to `055e2191909f6fce27c8b803d9bd750120383c0d`, matching `source-repo` current `main`.
- `python3 /OneOPS/quick_env/scripts/validate_seed_templates.py` -> exit 0.
- `AUTH_TOKEN=abc123 /OneOPS/quick_env/init-configs/gitea/source-repo/templates/import-variable-sets.sh` -> exit 0.
- `AUTH_TOKEN=abc123 bash /OneOPS/quick_env/init-configs/gitea/source-repo/templates/import-to-oneops.sh` -> exit 0.
- API verification found:
  - `133cb2f9-6264-11f1-a18b-fa163e7745bf task-center-ansible-server-config-collection ansible ansible/server-config-collection/site.yml`

## Review Evidence

- Task 7 spec review: passed.
- Task 7 quality review found two issues and both were fixed:
  - queue dedupe now uses queue-level identity instead of only asset code.
  - one-time history excludes runs with `scheduled_task_id`.
- Task 7 quality re-review: passed.

## Deferred Scope

- Final sidebar menu placement for configuration management.
- Visual E2E with browser screenshots after the current dynamic frontend refresh.
- Full backend suite.
- Full frontend build.
- Policy design for scheduled task default cadence per asset group.
- Notification, ticket, and review workflow around detected config changes.
