---
topic: d2v2
kind: full-stack
title: Device V2 运维入口迁移
createdAt: 2026-05-15T19:08:51+0800
program: true
---

# Test Matrix

| Area | Surface/API | Scenario | Role/Data | Expected | Evidence | Lane | Priority | Status |
|---|---|---|---|---|---|---|---|---|
| FE | `/#/device/device-v2-management-redesign` | Row `更多` shows 监控/WebShell/操作审计/日志 | admin/admin@123, synced V2 device | Entries visible and disabled/blocked only with explicit reason | Browser screenshot + console/network notes | d2v2 | P0 | reviewed |
| FE/BE | V1 bridge gate | V2 device has no `device_v1_code` | selected row code | Sync/status call returns V1 code or explicit missing fields | API response + UI message | d2v2 | P0 | reviewed |
| FE | WebShell | User clicks SSH/TELNET entry | synced V1 code | Opens `TerminalFull` with V1 `hostCode`, protocol, hostname | Browser URL evidence | d2v2 | P0 | reviewed |
| FE | 监控 | User opens monitoring entry | synced V1 code + V1 detail | Reuses old Grafana dashboard logic and variables | Network/Grafana iframe evidence or exact blocker | d2v2 | P0 | reviewed |
| FE | 操作审计 | User opens audit entry | synced V1 code | Uses `/terminal/record` `instance_code` V1 code; replay/download remain old implementation | Network evidence + table state | d2v2 | P0 | reviewed |
| FE | 日志 | User opens log entry | any selected device | Shows Loki contract pending, no query made | Browser evidence | d2v2 | P1 | reviewed |
| Regression | Old inventory page | Open old device detail | existing V1 device | Existing summary, monitor, console, audit behavior unchanged | Browser smoke or focused code evidence | d2v2 | P0 | reviewed |
