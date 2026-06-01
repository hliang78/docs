---
topic: device-v2-onboarding-observability
kind: full-stack
title: Device V2 极简纳管设计
createdAt: 2026-05-15T20:57:53+0800
program: true
---

# Frontend Continue Onboarding

## Purpose

把 Device V2 管理页从“采集验证”语义收敛为单台“继续纳管”，并只展示监控纳管、日志纳管两个结果。

## Findings

- 当前页面已有单行“真实采集”“采集验证”“日志”入口。
- 当前批量按钮可触发 store start，但首期继续纳管不做批量远程配置。

## Requirements

- 单台行操作增加或重命名为 `继续纳管`。
- 服务器设备点击后可选择监控方式：agent / SNMP。
- 批量选择时只允许生成计划或逐台查看，不触发并发远程执行。
- 详情展示 action evidence，而不是复杂阶段状态。

## Acceptance

- 用户能看到监控纳管、日志纳管两个摘要。
- 再次点击只表达重试 failed/unknown。
- 日志入口优先展示日志纳管计划/结果。

## Validation

- Browser screenshot.
- Request payload includes single device code and optional monitoring mode.

## Candidate Stories

- FE-001: Add single-device continue onboarding action.
- FE-002: Render onboarding action evidence in detail drawer.
