---
topic: d2v2
kind: full-stack
title: Device V2 运维入口迁移
createdAt: 2026-05-15T19:08:51+0800
program: true
---

# 日志预留与证据验证

## Purpose

为 Loki 日志保留清晰入口和阻塞说明，同时完成首批运维入口的验证证据。

## Findings

- 用户明确说明 Loki 日志有很多类型，需要后续沟通。
- 旧带外日志不要迁移。

## Requirements

- 日志入口命名为 `日志`，不是 `带外日志`。
- 不发起 Loki 查询。
- 显示需要确认的契约项：日志类型、label、时间范围、权限、接口。
- 验证故事必须记录真实通过项和阻塞项。

## Acceptance

- 日志入口不误导用户为已可用。
- 首批证据可支持后续继续开发 Loki 查询。

## Validation

- Browser evidence.
- Typecheck and Go test evidence.

## Candidate Stories

- D2V2-005, D2V2-006
