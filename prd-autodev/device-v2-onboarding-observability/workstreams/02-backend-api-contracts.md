---
topic: device-v2-onboarding-observability
kind: full-stack
title: Device V2 极简纳管设计
createdAt: 2026-05-15T20:57:53+0800
program: true
---

# Backend Evidence And API Contracts

## Purpose

定义最小后端契约：单台 ensure、action evidence、summary 推导和配置文件读取。

## Findings

- `device_v2_store_run.summary_json` 已可存储 map evidence。
- 现有 Device V2 API 可扩展 `:code/onboarding` 入口。

## Requirements

- `GET /device/v2/:code/onboarding` 返回 latest/provided run 的 onboarding evidence。
- `POST /device/v2/:code/onboarding/plan` 只生成 action list。
- `POST /device/v2/:code/onboarding/ensure` 执行单台 ensure。
- ensure 跳过 success，只执行 new/failed/unknown。

## Acceptance

- Evidence contract 中 action result 只使用 `success|failed|unknown|skipped`。
- Overall summary 由 action result 推导。
- 不新增 onboarding table。

## Validation

- Go unit tests for action merge and retry filtering.
- JSON contract snapshot.

## Candidate Stories

- BE-001: Add onboarding evidence helper.
- BE-002: Add plan/ensure/read API contract.
