---
topic: d2v2
kind: full-stack
title: Device V2 运维入口迁移
createdAt: 2026-05-15T19:08:51+0800
program: true
---

# Program Context Brief

## Goal

在 Device V2 清册中，为单台设备提供 `监控`、`WebShell`、`操作审计` 和后续 `日志` 的统一入口。实现原则是：V2 先同步/绑定到 V1，之后这些能力完全调用旧设备实现或旧接口，不复制业务逻辑，不改变旧页面行为。

## Scope

- Device V2 清册重构页：`OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue`
- Device V2 API 封装：`OneOPS-UI/src/api/device/device-v2.ts`
- 旧设备详情可复用能力：`OneOPS-UI/src/views/device/Inventory.vue`
- 终端审计 API：`OneOPS-UI/src/api/terminal/ssh_record.ts`
- Grafana 旧监控组件/API：`OneOPS-UI/src/components/GrafanaDashboard/GrafanaDashboard.vue`、`OneOPS-UI/src/api/grafana/dashboard.ts`
- Device V2 后端同步桥：`OneOPS/app/device/v2/api/device_v2_sync_to_v1.go`、`OneOPS/app/device/v2/router/device_v2.go`、`OneOPS/app/device/v2/dto/device_v2.go`

## Boundaries

- 不实现 Loki 日志查询，仅保留入口、禁用态或明确阻塞态。
- 不迁移 GPU 信息。
- 不迁移旧带外日志。
- 不为缺失字段创建兜底、降级分支或智能推断。
- 不改变旧 `/#/device/inventory` 的现有操作、布局、接口语义。
- 不添加依赖、不写迁移、不改生产配置、不提交/推送。

## Priority Focus

第一批开发按依赖链执行：后端桥接契约 -> 前端 V1 code gate -> 监控/WebShell/操作审计入口 -> 日志占位 -> 验证证据。

## Background

旧设备详情页已经提供监控、SSH/TELNET 控制台、安全审计、变更记录、GPU 和带外日志。用户要求 V2 清册只迁移监控、日志、WebShell、操作审计，其中日志来自 Loki 且类型待确认，GPU 和带外日志不要迁移。现有后端已有批量 `sync-to-v1` 能力，并会回填 `device_v1_code` / `legacy_device_code`。

## Concerns

- 若前端拿 V2 code 直接访问旧终端/审计/监控接口，会造成数据错位或空数据。
- 若同步失败但 UI 继续打开旧能力，会掩盖真实数据问题。
- 若抽取旧代码组件时改动旧页面，容易引入回归。
- 旧监控变量依赖设备名称和类型，V2 必须使用同步后的 V1 设备实体事实。

## Open Questions

- Loki 日志的设备 label、日志类型、时间范围、权限和查询接口仍需用户确认，因此本批只做入口和阻塞说明。
