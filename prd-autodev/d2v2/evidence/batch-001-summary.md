---
topic: d2v2
kind: full-stack
title: Device V2 运维入口迁移
createdAt: 2026-05-15T19:08:51+0800
program: true
---

# Batch 001 Evidence Summary

## Result

- Batch 001 validation completed for Device V2 operation entries.
- Backend validation passed: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS && go test ./app/device/v2/...`.
- Frontend validation passed: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run typecheck:d2`.
- Browser/CDP evidence confirms Device V2 row `更多` menu exposes `监控`, `WebShell`, `操作审计`, `日志`.
- Browser/CDP evidence confirms Device V2 detail `操作中心` exposes `监控`, `WebShell`, `操作审计`, `日志`.
- Browser/CDP evidence confirms `日志` opens a Loki-only placeholder with pending contract items and no old out-band log reuse copy.
- Old inventory regression smoke loaded `/#/device/inventory` and confirmed the existing resource table and monitoring/terminal/audit related surfaces remain visible.

## Evidence Files

- `docs/openclaw-autodev/evidence/d2v2/D2V2-001-bridge-contract.md`
- `docs/openclaw-autodev/evidence/d2v2/D2V2-002-frontend-v1-code-gate.md`
- `docs/openclaw-autodev/evidence/d2v2/D2V2-003-monitoring-webshell-entries.md`
- `docs/openclaw-autodev/evidence/d2v2/D2V2-004-operation-audit-entry.md`
- `docs/openclaw-autodev/evidence/d2v2/D2V2-005-loki-log-placeholder-entry.md`
- `docs/openclaw-autodev/evidence/d2v2/D2V2-006-device-v2-operations-evidence.md`
- `docs/openclaw-autodev/evidence/d2v2/D2V2-006-browser-check.json`
- `docs/openclaw-autodev/evidence/d2v2/D2V2-006-old-inventory-browser-check.json`

## Follow Ups

- Loki contract remains pending human confirmation: log type, label mapping, time range, permission, and API request/response contract.
- Full click-through validation for monitoring/WebShell/audit should use a synced V2 device with confirmed V1 code and record network/route details when available.
