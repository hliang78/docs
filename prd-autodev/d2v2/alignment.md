---
topic: d2v2
kind: full-stack
title: Device V2 运维入口迁移
createdAt: 2026-05-15T19:08:51+0800
program: true
---

# Alignment

## Program Decisions

- Proceed without another review because user explicitly requested planning and delegation.
- Task id: `d2v2`, chosen for short WeChat commands.
- Single OpenClaw task handles FE+BE because stories are ordered and bridge contract must precede FE implementation.
- User granted permission to modify old device-related frontend/backend code without further authorization, only when old behavior is preserved.
- No fallback, no degraded behavior, no mock, no intelligent inference. Missing contracts or fields must become visible blockers/errors.

## Batch Decisions

- Publish `batch-001` as `reviewed` immediately.
- Use `executionMode: dependency-chain`.
- First story creates/verifies backend bridge contract; later stories consume it.
- Delegate the full dependency chain to automation, not only the first turn. `d2v2` must keep scheduling eligible stories until all stories are done or a real blocker/approval boundary is reached.
