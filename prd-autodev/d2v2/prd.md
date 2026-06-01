---
topic: d2v2
kind: full-stack
title: Device V2 运维入口迁移
createdAt: 2026-05-15T19:08:51+0800
program: true
---

# Program PRD

## Summary

Device V2 清册需要围绕单台设备补齐运维入口：监控、WebShell、操作审计，以及后续 Loki 日志入口。实现必须以 Device V2 同步到 Device V1 为前置，旧能力完全调用旧实现。GPU 和旧带外日志不迁移。

## Current Facts

- 旧设备页已有监控、SSH/TELNET、操作审计、GPU、带外日志。
- 新 Device V2 重构页目前只有资料维护、采集验证、删除、真实采集等操作。
- 后端已有 `POST /device/v2/sync-to-v1`，成功后回填 `device_v1_code` 和 `legacy_device_code`。
- 前端尚无集中 V1 code gate，也没有 V2 运维入口。

## Requirements

1. Backend bridge
   - Provide or verify a single-device bridge contract for V2 to V1 operation use.
   - Return explicit V1 code or explicit missing-field/sync error.
   - Do not silently succeed with empty values.

2. Frontend gate
   - Centralize V1 code resolution before old-operation buttons run.
   - Use only confirmed V1 code for terminal, monitoring, and audit.
   - Block with visible reason when sync/status fails.

3. Operation entries
   - Add `监控`、`WebShell`、`操作审计`、`日志` to row `更多` and selected device operation center where appropriate.
   - WebShell opens old terminal path.
   - Monitoring reuses old Grafana dashboard path and variables.
   - Audit reuses old `/terminal/record` list/replay/download behavior.
   - Log entry states Loki contract is pending and does not query.

4. Old behavior
   - Existing `/#/device/inventory` behavior must not change.
   - Any helper extraction from old code must preserve old API and visual behavior.

## Non-Goals

- GPU migration.
- Old out-of-band log migration.
- Loki query implementation.
- Dependency changes, migrations, production configuration, commit, push, deploy.

## Validation

- `cd /Users/huangliang/project/OneOPS-ALL/OneOPS && go test ./app/device/v2/...`
- `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run typecheck:d2`
- Browser validation on `http://127.0.0.1:3001/#/device/device-v2-management-redesign` with `admin/admin@123`.
- Evidence under `docs/openclaw-autodev/evidence/d2v2/<story-id>/summary.md`.

## OpenClaw Story Package

See `story-packages/batch-001.json`.
