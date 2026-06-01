---
topic: obsflow-device-v2-ingest-update
kind: backend
title: obsflow 基于 Device V2 入库候选源更新
createdAt: 2026-05-19T07:49:09+0800
---

# Context Brief

## Goal

让 `obsflow` 的 workflow 采集预检候选设备能够承接 Device V2 入库后的设备清册。Device V2 入库写入 `platform_devices_v2` 后，网络类设备应进入 obsflow 的 collection plan 判断，不再只依赖旧 `device` 表。

## Boundaries

- 本次不通过 OpenClaw 自动化发布故事，不创建/启动任何 loop。
- 本次在当前 Codex 会话内直接实现。
- 范围限定为 obsflow 预检候选源，不改变 Device V2 入库写库流程、DC2 执行逻辑、前端页面或 collection contract 配置。
- 保留旧 `device` 表候选作为迁移期补位，避免未迁移资产从 workflow 中消失。

## Focus

- `OneOPS/app/obsflow/adapters/device_collection_candidate_source.go`
- `OneOPS/app/obsflow/adapters/device_collection_candidate_source_test.go`
- 候选设备最小字段：`device_code`、`catalog_name`、`platform_name`、`vendor_name`

## Background

`obsflow` 的 workflow plan 会调用 `DeviceCollectionCandidateSource.ListCandidates`，再由 `ConfigWorkflowCollectionSupportPolicy` 根据配置判断每个 collection 是否有可执行设备。原实现只从旧 `device` 表联表 `catalog/platform/device_model/manufacturer` 取候选。Device V2 入库当前主表是 `platform_devices_v2`，字段事实主要在 `attributes_json`、`metadata_json` 与 `platform_code` 中。

## Concerns

- 不能把完整 Device V2 业务模型拖进 obsflow，保持 obsflow 的最小候选视图。
- Device V2 字段可能来自 attributes、metadata 或主数据 code，需要兼容多来源。
- 相同设备 code 同时存在 V2 和旧表时，应以 V2 口径为准。
- 非网络设备如 server 不应因为 Device V2 入库进入拓扑类 workflow。

## Open Questions

- 后续是否需要将 Device V2 的 `function_area`、`manageable`、`access_points` 一并纳入 obsflow 候选过滤，目前未纳入本次范围。
