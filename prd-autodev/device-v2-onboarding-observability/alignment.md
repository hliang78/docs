---
topic: device-v2-onboarding-observability
kind: full-stack
title: Device V2 极简纳管设计
status: draft
---

# Alignment

## 页面观察

- 访问 `http://127.0.0.1:3001/#/device/device-v2-management-redesign` 成功，页面显示 118 台设备和最近 5 条导入任务。
- 当前按钮仍叫“批量采集验证”，单行菜单仍有“采集验证”。新方案应避免把远程纳管做成批量按钮。
- 单行“真实采集”能跳转到 DC2 生产采集测试页，并展示 run evidence、facts、issues、persisted 计数。
- 采集证据样例：`DVC8B7374049C21` 的 `last-store-collection-dc2` 返回 `task_id=entv2_1778840314183543000`、`store_run_id=dvsr_5875cfa67fad8f9c12f539e1605d380bad330249`、`dc2_run_id=dc2s_5875cfa67fad8f9c12f539e1605d380bad330249`。

截图证据：

- `evidence/device-v2-management-redesign-20260515.png`
- `evidence/device-v2-production-test-20260515.png`

## 当前真实代码事实

| Area | Fact |
|---|---|
| FE action | `OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:196` 批量按钮触发 `startStoreForSelection`，文案为“批量采集验证”。 |
| FE row actions | `OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:249` 有“真实采集”，`:257` 有单设备“采集验证”，`:261` 的“日志”目前是 placeholder。 |
| FE DC2 evidence | `OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:2996` 根据 `last-store-collection-dc2` 跳转 DC2 生产采集页，并携带 store task/run id。 |
| FE store start | `OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:3036` 调用 `startDeviceV2StorePipelineReq` 或 `retryDeviceV2StorePipelineReq`。 |
| BE store run model | `OneOPS/app/device/v2/model/device_v2_store_run.go` 已有 `SummaryJSON`，适合承载 onboarding evidence。 |
| BE store runtime | `OneOPS/app/entity/v2/service/impl/device_v2_store_runtime.go:181` 运行 Device V2 store runtime，汇总 success/partial/failed/blocked 和 `NextManageIDs`。 |
| BE V1 sync | `OneOPS/app/device/v2/api/device_v2_sync_to_v1.go:146` `SyncToV1` 已声明“同步到旧 Device V1 台账，并在成功后触发监控任务推送”。 |
| BE monitor push | `OneOPS/app/device/v2/api/device_v2_sync_to_v1.go:201` 成功同步后调用 `DeviceStoreSrv.NotifyMonitorProbeByDeviceCodes`。 |
| Platform monitoring | `OneOPS/app/platform/router/platform_v2.go:19` 到 `:44` 已有 plans apply、tasks action、metric instances observe/sync API。 |
| Agent log/trap capability | `ctrlhub/controller/pkg/controller/config/plugin_mapping_config.yaml` 已映射 `log_collection -> inputs.tail`、`snmp_trap -> inputs.snmp_trap`、`outputs.loki`。 |

## 候选设计内容

### 当前真实代码事实

- 入库和采集证据已有基础。
- 监控下发可复用现有机制。
- `summary_json` 可避免新建 onboarding 表。
- syslog listener 有基础，但 SNMP trap 仍需 teleabs 模板。

### 候选文档内容

- PRD 使用“手动继续纳管 + ensure action + evidence”。
- Program plan 拆成 FE 单台入口、BE evidence contract、监控 ensure、日志 ensure/config、远程模板、回归证据。
- Test matrix 覆盖单台 UI、重试 failed/unknown、区域配置、syslog target 模板、SSH timeout、SNMP trap 缺口。
- 新增一个独立的区域监听服务管理页，作为 Device V2 onboarding 之外的日常运维入口。
- 该页面复用现有 `app/platform` 日志转发发布链路，但页面语义从“日志转发计划”提升为“区域 syslog/snmp trap 接入服务管理”。
- `syslog` 页面模型首期拆成两种表单语义：
  - `服务器 syslog 监听`
  - `网络设备 syslog 监听`
- 两类 syslog 首期仅表单/默认值差异，不额外拆后端投递模型。
- `snmp trap` 首期纳入独立页面，但范围先收敛在 listener 管理。

### AI 推导建议

- 不把远程访问拆成多个状态，而把每次远程尝试记录为 action result。
- 整体纳管摘要由 action result 推导，不单独维护复杂生命周期。
- 配置文件先承载 FunctionArea 基础服务，待稳定后再升级一级模型。
- 新页面可优先以“包装现有 `remote_syslog` / `log_forward_plan` 模型”的方式交付，减少首期改造面。

### 规划缺口

- 配置文件路径与 schema。
- 各厂商 syslog target 保存命令模板。
- 服务器 SNMP 与 SSH 日志转发模板。
- SNMP trap teleabs 模板。

## 对齐建议

建议把“独立 syslog/snmp trap 管理页”视为当前 program 的新增场景增量，而不是塞回单台 `继续纳管` 入口内部。实现上优先复用现有 `remote_syslog` / `log_forward_plan` 下发链路，再补一轮 PRD 增量与小批次 stories。
