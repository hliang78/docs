---
topic: device-v2-onboarding-observability
kind: full-stack
title: Device V2 极简纳管设计
createdAt: 2026-05-15T20:57:53+0800
program: true
---

# Remote Access, Permissions, And Errors

## Purpose

限制远程访问风险，避免把连接细节变成复杂状态。

## Findings

- 远程访问可能慢、失败、半成功。
- 网络设备配置需要保存。

## Requirements

- 所有远程动作以 ensure contract 表达。
- 远程 runner 设置短 timeout。
- 保存配置是网络设备 syslog target 模板的一部分。
- error 归一为 `failed` 或 `unknown`，并带 `retryable`。
- 首期只支持单台远程执行。

## Acceptance

- SSH timeout 可重试。
- 保存失败不会标记 success。
- 已 success action 不重复执行。

## Validation

- Template tests for inspect/apply/save/verify.
- Retry filtering tests.

## Candidate Stories

- PLATFORM3-001: Define remote ensure template contract.
- PLATFORM3-002: Add network syslog target template skeleton.
