---
topic: obsflow-device-v2-ingest-update
kind: backend
title: obsflow 基于 Device V2 入库候选源更新
createdAt: 2026-05-19T07:49:09+0800
---

# Discovery

## Findings

- 当前 `obsflow` 候选源只读旧 `device` 表，并联表 `catalog/platform/device_model/manufacturer`，最终输出 `WorkflowCollectionCandidate` 的四个字段。
- workflow plan 后续只依赖该最小候选视图，不需要完整设备模型。
- Device V2 入库写入 `platform_devices_v2`，其中 `code`、`platform_code` 是表字段；`catalog/vendor/platform` 等事实可能在 `attributes_json`、`metadata_json` 或主数据 code 中。
- DC2 已有类似 Device V2 采集计划字段读取口径：优先从 attributes/metadata 中读取 `catalog/platform/manufacturer`，说明 obsflow 候选源也应遵循这一类字段事实。
- 迁移风险在于旧 `device` 与新 `platform_devices_v2` 会共存；候选应按 code 去重并优先使用 Device V2。

## Evidence

- `OneOPS/app/obsflow/adapters/device_collection_candidate_source.go`：原候选源从 `persistence.WorkflowCandidateDeviceRecord{}.TableName()` 即 `device` 读取。
- `OneOPS/app/obsflow/domain/workflow_collection_candidate.go`：候选结构只有 `DeviceCode/CatalogName/PlatformName/VendorName`。
- `OneOPS/app/obsflow/adapters/config_workflow_collection_support_policy.go`：后续策略用 vendor/platform/collection contract 判断 eligible device codes。
- `OneOPS/app/device/v2/model/device_v2.go`：Device V2 表名为 `platform_devices_v2`，JSON 字段为 `labels_json/attributes_json/metadata_json`。
- `OneOPS/app/device_collection2/service/impl/device_collection2_run.go`：Device V2 collection plan input 从 attributes/metadata 读取 catalog/platform/manufacturer。

## Open Questions

- 本轮是否进一步把 `manageable/access_points/function_area` 纳入 obsflow 候选筛选：暂不做，避免改变 workflow 调度语义。
