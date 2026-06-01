---
topic: obsflow-device-v2-ingest-update
kind: backend
title: obsflow 基于 Device V2 入库候选源更新
createdAt: 2026-05-19T07:49:09+0800
---

# Question Round 001

## Purpose

Enrich the rough input before PRD or automation.

## Questions

1. What exact page, module, API, or workflow should this focus on first?
2. What outcome would make you say this is successful?
3. What must not change?
4. What are you most worried might go wrong?
5. Which users, roles, data, or environment should be treated as primary?
6. What evidence would convince you the work is really done?

## Answers

- 重点模块：`obsflow` workflow 预检候选源，即 `DeviceCollectionCandidateSource`。
- 成功标准：Device V2 入库后写入 `platform_devices_v2` 的网络设备，能被 `obsflow` 识别为 workflow 候选。
- 不应改变：Device V2 入库主流程、DC2 执行逻辑、前端页面，以及旧 `device` 表在迁移期的兼容补位作用。
- 主要风险：把完整 Device V2 业务模型耦合进 `obsflow`，或让 server 等非网络类设备误入当前 workflow。
- 主要数据环境：当前 OneOPS 后端，主数据表与 `platform_devices_v2` 共存的迁移期环境。
- 完成证据：代码实现、针对 Device V2 候选来源的测试覆盖，以及 `go test ./app/obsflow/... -count=1` 通过。

## Context Brief

### Goal

让 `obsflow` 的 workflow 采集预检候选设备能够承接 Device V2 入库后的设备清册。

### Boundaries

- 不通过 OpenClaw 自动化发布故事，不创建/启动任何 loop。
- 本次在当前 Codex 会话内直接实现。
- 范围限定为 obsflow 预检候选源，不改变 Device V2 入库写库流程、DC2 执行逻辑、前端页面或 collection contract 配置。

### Focus

- `OneOPS/app/obsflow/adapters/device_collection_candidate_source.go`
- `OneOPS/app/obsflow/adapters/device_collection_candidate_source_test.go`
- 候选设备最小字段：`device_code`、`catalog_name`、`platform_name`、`vendor_name`

### Concerns

- 不能把完整 Device V2 业务模型拖进 obsflow，保持最小候选视图。
- 相同设备 code 同时存在 V2 和旧表时，应以 V2 口径为准。
- 非网络设备如 server 不应因为 Device V2 入库进入拓扑类 workflow。

### Open Questions

- 后续是否需要把 `manageable/function_area/access_points` 纳入候选过滤：本轮暂不纳入。
