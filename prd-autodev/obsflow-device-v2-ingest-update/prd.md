---
topic: obsflow-device-v2-ingest-update
kind: backend
title: obsflow 基于 Device V2 入库候选源更新
createdAt: 2026-05-19T07:49:09+0800
---

# PRD

## 背景

`obsflow` 的 workflow 预检需要先知道哪些设备可参与 collection。目前候选源只读旧 `device` 表。Device V2 入库完成后，设备事实进入 `platform_devices_v2`，导致新入库的 V2 设备无法自然进入 obsflow 候选范围。

## 目标

- `obsflow` 能识别 Device V2 入库写入的网络设备候选。
- 相同 code 同时存在 V2 与旧表时，以 V2 候选事实为准。
- 保留旧 `device` 表补位，降低迁移期影响。
- 保持 obsflow 最小模型边界，只传递 `device_code/catalog/platform/vendor`。

## 非目标

- 不修改 Device V2 入库写库流程。
- 不修改 DC2 执行、collection contract、前端 UI。
- 不创建 OpenClaw 自动化故事或任务。
- 不在本轮引入 `manageable/access_points/function_area` 过滤。

## 当前真实代码事实

- `OneOPS/app/obsflow/domain/workflow_collection_candidate.go` 定义候选最小结构。
- `OneOPS/app/obsflow/adapters/device_collection_candidate_source.go` 原先只从旧 `device` 表读取候选。
- `OneOPS/app/device/v2/model/device_v2.go` 的 Device V2 表名是 `platform_devices_v2`，动态事实在 `attributes_json`、`metadata_json`。
- `OneOPS/app/obsflow/adapters/config_workflow_collection_support_policy.go` 后续只消费 candidate 的 vendor/platform/catalog 语义。

## 需求

- 当 `platform_devices_v2` 存在时，读取 Device V2 rows 并解析：
  - code：优先 `platform_devices_v2.code`
  - catalog：`attributes.catalog_name/catalog`、`metadata.catalog_name/catalog`、`metadata.prepare_result.prepared_facts.profile.catalog_name`，以及 `catalog_code` 主数据兜底
  - platform：attributes/metadata/platform 主字段，`platform_code` 主数据兜底
  - vendor：attributes/metadata/manufacturer/manufacturer_name/vendor 主字段，`manufacturer_code` 主数据兜底
- 候选仍只保留 `switch/router/firewall`。
- 读取旧 `device` 候选作为补位；按 code 去重，V2 优先。
- 无任何候选时保持原错误语义：`警告：无设备执行`。

## 验收

- V2 入库设备可作为 obsflow 候选返回。
- V2 与旧表 code 冲突时只返回一条，且字段取 V2。
- 旧表-only 场景继续通过。
- 非网络 catalog 继续被过滤。

## 验证

- `go test ./app/obsflow/adapters -run TestDeviceCollectionCandidateSource -count=1`

## OpenClaw Story Package

本次按用户要求在当前 Codex 会话内实现，不生成或发布 OpenClaw story package。
