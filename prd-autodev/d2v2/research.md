---
topic: d2v2
kind: full-stack
title: Device V2 运维入口迁移
createdAt: 2026-05-15T19:08:51+0800
program: true
---

# Research

## 当前真实代码事实

- Device V2 重构页的行级操作位于 `OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue`，当前有 `详情`、`真实采集`、`编辑` 和 `更多`；`更多`内只有补充资料、采集验证、删除设备。
- Device V2 详情侧栏当前展示资产、身份/平台/来源、状态分层、访问点/凭据、系统/硬件摘要、来源与变更、采集与监控、操作中心，但没有监控、WebShell、操作审计、日志入口。
- 旧设备页 `OneOPS-UI/src/views/device/Inventory.vue` 已有：
  - SSH/TELNET 控制台入口，跳转 `TerminalFull`，query 为 `hostCode`、`protocol`、`hostname`。
  - Grafana 监控 tab，根据设备类别选择 switch/server dashboard，变量分别为 `Switch` 或 `server`。
  - 安全审计 tab，调用 `sshRecordPageReq`，按 `instance_code` 查询，支持回放和下载。
  - GPU tab 与带外日志 tab，本项目不迁移。
- 前端 Device V2 API 已有 `syncDeviceV2ToV1Req`，调用 `POST /device/v2/sync-to-v1`，请求字段为 `codes` 与 `monitor_push`。
- 后端 `OneOPS/app/device/v2/api/device_v2_sync_to_v1.go` 已实现批量同步：
  - 若已有 `device_v1_code` 且 V1 存在则跳过创建。
  - 若创建或匹配到 V1，会把 `device_v1_code`、`legacy_device_code`、`sync_to_v1_status`、`sync_to_v1_at` 回填到 V2 attributes/metadata。
  - 同步成功后可调用 `NotifyMonitorProbeByDeviceCodes` 推送监控任务。
- 现有后端同步缺少面向前端单设备入口的“桥接状态”契约；前端如果只读 attributes，需要重复解析和猜测字段。

## 候选实现方向

- 后端增加一个显式旧能力桥接状态/确保接口，返回 `device_v1_code`、`synced`、`sync_to_v1_status`、`missing_required_fields`，并复用现有同步逻辑。
- 前端增加单设备 `ensureLegacyDevice` gate：若没有 V1 code，不打开旧能力；调用同步/状态接口后只使用返回的 V1 code。
- 监控、WebShell、操作审计都基于 V1 设备 code 调用旧实现。旧页面可以被抽取轻量 helper 或复用同一接口，但旧页面行为不得变化。
- 日志入口只显示“待确认 Loki 日志类型/查询契约”，不做默认查询，不做空数据假装成功。

## AI 推导建议

- 优先让后端暴露显式桥接状态，减少前端从 attributes/metadata 私自推断。
- 若后端实现发现现有 sync-to-v1 已足够，可仍补测试和文档，但前端必须集中封装 V1 code gate，不能在多个按钮内散落解析逻辑。
- 行级 `更多` 和右侧详情 `操作中心` 都应提供入口，避免用户必须先进入旧清册页。

## 规划缺口

- Loki 日志的类型、label、时间范围、接口路径、是否复用现有 dashboard/log 模块尚未确认。
- 旧监控 dashboard code 的来源目前在旧页面 `getDashboardUrls()`，自动化需要决定是抽取共享 helper，还是局部复用旧 API 查询。
