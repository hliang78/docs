---
topic: device-v2-onboarding-observability
kind: full-stack
title: Device V2 极简纳管设计
createdAt: 2026-05-15T20:57:53+0800
program: true
---

# Monitoring And Log Ensure Flows

## Purpose

定义监控纳管和日志纳管的最小可执行路径。

## Findings

- 监控任务下发机制已有。
- syslog listener 已有流程。
- SNMP trap 缺 teleabs 模板。

## Requirements

- 网络设备监控：下发监控任务成功即成功。
- 网络设备日志：首期优先 syslog，确保区域 syslog listener，再远程配置 target 并保存。
- 服务器监控：用户选择 agent / SNMP。
- 服务器日志：有 agent 优先 agent，无 agent 生成 SSH 配置计划。

## Acceptance

- 每类路径都产出 action result。
- 远程失败不污染整体状态，只记录 failed/unknown。
- SNMP trap 缺口以 unsupported/template_required action 表达。

## Validation

- Fake monitor dispatch service.
- Fake remote runner for timeout and save failure.

## Candidate Stories

- BE-003: Implement monitoring ensure adapter.
- BE-004: Implement log plan builder.
