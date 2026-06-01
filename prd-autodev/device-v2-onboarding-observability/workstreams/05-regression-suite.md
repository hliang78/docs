---
topic: device-v2-onboarding-observability
kind: full-stack
title: Device V2 极简纳管设计
createdAt: 2026-05-15T20:57:53+0800
program: true
---

# Regression Suite

## Purpose

用小测试覆盖极简纳管设计的稳定性边界。

## Requirements

- JSON config schema validation.
- Onboarding action evidence contract test.
- Retry failed/unknown only.
- Browser evidence for single-device UI.
- Fake remote runner for timeout, command failure, save failure.

## Acceptance

- 测试覆盖单台成功、部分失败、重试、unsupported SNMP trap。
- 不依赖真实远程设备。

## Validation

- `jq empty` for story packages and config samples.
- Go unit tests for backend helpers.
- Browser screenshot for UI.

## Candidate Stories

- CT-001: Add contract test matrix.
- CT-002: Add fake remote runner regression cases.
