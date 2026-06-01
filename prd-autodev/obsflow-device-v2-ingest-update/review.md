---
topic: obsflow-device-v2-ingest-update
kind: backend
title: obsflow 基于 Device V2 入库候选源更新
createdAt: 2026-05-19T07:49:09+0800
---

# Logic Review

## P0 Blockers

- None found in current implementation.

## P1 Risks

- `obsflow` 当前只承接网络类 catalog：`switch/router/firewall`。如果后续希望把 server 或其他设备纳入 workflow，需要先扩展 `isWorkflowCollectionCandidateCatalog` 与对应 contract，而不是直接放开候选过滤。
- Device V2 候选读取依赖 `platform/catalog/manufacturer` 主数据表做 code->name 兜底。如果运行环境缺少这些主数据，候选仍可读出，但 vendor/platform 可能为空，进而在 support policy 阶段被排除。

## P2 Suggestions

- 保持 `obsflow` 候选结构最小化，只传 `device_code/catalog/platform/vendor`，避免把 Device V2 全量业务语义拖进 workflow 预检。
- 如果后续需要根据 `manageable/function_area/access_points` 限制候选，建议先在 PRD 中把“预检候选过滤”和“执行期目标过滤”分开，避免一次调整同时改变调度语义和执行语义。

## Validation

- `2026-05-20` 在 `/Users/huangliang/project/OneOPS-ALL/OneOPS` 执行 `go test ./app/obsflow/... -count=1`，全部通过。
- 补充了 `TestDeviceCollectionCandidateSourceListCandidatesResolvesDeviceV2PreparedFactsAndCodeRefs`，覆盖 Device V2 真实入库常见字段来源：
  - `prepare_result.prepared_facts.profile.catalog_code`
  - `platform_devices_v2.platform_code`
  - `attributes.manufacturer_code`
