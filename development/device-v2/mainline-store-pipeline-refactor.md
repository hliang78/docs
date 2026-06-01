# Device V2 主线采集入库改造设计

| 项目 | 内容 |
| --- | --- |
| 文档状态 | `active-design-draft` |
| 创建日期 | 2026-05-28 |
| 适用范围 | Device V2 store pipeline、远程采集、解析处理、同步 V1、监控推送 |
| 决策来源 | 2026-05-28 ZB 入库接线沟通与当前代码梳理 |

## 0. 当前推进状态

- 已抽出可复用 pipeline options 入口：`DefaultDeviceV2PipelineOptions` 与 `NormalizeDeviceV2PipelineOptions`，HTTP 与后续内部入口可以共用同一套默认值/校验。
- 已把 `StartStorePipeline` 拆成可内部调用的 `StartDeviceV2StorePipeline`，ZB 不需要模拟 HTTP 即可启动 Device V2 pipeline。
- 已把 `SyncToV1` 拆成可内部调用的 `RunSyncToV1`，并保留 HTTP handler 作为薄入口。
- 已修正 sync-to-v1 新建 V1 设备时的 `DeviceCode` 贯穿：新建设备请求会使用 Device V2 `Code`，回填查重也优先按 code 查找。
- 已新增 Device V2 `manage` runtime 接线：`EntityV2Srv` 在 device_v2/manage 阶段通过 `DeviceV2ManageRuntimeRunner` 调用 Device V2 内部 runner，执行 sync-to-v1 与 monitor push，并写入 `manage_device_runs/manage_summary`。
- ZB 后台编排已改为只启动 Device V2 pipeline；sync-to-v1/monitor push 由 pipeline manage 阶段完成，回调从 pipeline 结果读取端到端明细。
- `manage` runtime 的单设备 run 与 summary 构造已先收口到私有 typed struct，落入 pipeline result 前再转成 `map[string]interface{}`，为后续统一结果模型做铺垫。

## 1. 目标

Device V2 的主线入库必须表达完整闭环：

```text
pre_register -> prepare -> store -> manage
```

其中完整业务语义为：

```text
设备源数据准备 -> 远程采集准备 -> 采集/解析/核心入库 -> 同步 V1/推送监控
```

当前代码已经具备 `prepare`、`store`、`manage` 的 device_v2 主线接线：`store` 阶段接入 `DeviceCollection2Srv`，`manage` 阶段通过 Device V2 runner 执行 sync-to-v1 和 monitor push。后续改造重点转为服务化拆分、结果模型治理与 store runtime 瘦身。

## 2. 当前代码事实

| 能力 | 当前入口 | 现状 |
| --- | --- | --- |
| Pipeline 启动 | `EntityV2Srv.StartPipeline` | 默认模板 `pre_register-prepare-store-manage` |
| Prepare runtime | `runMinimalDeviceV2PrepareRuntime` | 已按 device_v2 特化 |
| Store runtime | `runMinimalDeviceV2StoreRuntime` | 已按 device_v2 特化，并接入 DeviceCollection2 |
| Manage stage | `DeviceV2ManageRuntimeRunner` | device_v2 专用 manage runtime 已接入 |
| Sync to V1 | `DeviceV2API.RunSyncToV1` | 已可被 HTTP、ZB、pipeline manage 复用，后续再服务化 |
| Monitor push | `DeviceStoreSrv.NotifyMonitorProbeByDeviceCodes` | 由 manage runtime 经 `RunSyncToV1` 调用 |
| Pipeline options | `NormalizeDeviceV2PipelineOptions` | HTTP 与内部入口共用 |

## 3. 已确认主线语义

- Device V2 主线包含远程采集、解析处理、同步 V1、推送监控任务的全过程。
- `manage` 阶段必须承载 sync-to-v1 和 monitor push 的结果，而不是只推进 entity 状态。
- 成功/失败必须支持设备粒度的部分成功。
- 监控推送结果必须纳入最终状态和外部回调。
- `DeviceCode` 必须贯穿 Device V2 和 Device V1。

## 4. 目标架构

### 4.1 Pipeline 分层

```text
EntityV2Srv.StartPipeline
  pre_register
    ensure source entity
  prepare
    runDeviceV2PrepareRuntime
  store
    runDeviceV2StoreRuntime
  manage
    runDeviceV2ManageRuntime
```

`runDeviceV2ManageRuntime` 是本轮新增重点。

### 4.2 Manage runtime 职责

`runDeviceV2ManageRuntime` 应负责：

- 读取 store 阶段产生的 `NextManageIDs`。
- 对可管理设备执行 sync-to-v1。
- 对 sync 成功设备执行 monitor push。
- 持久化每台设备的 `sync_to_v1_status`、`monitor_push_status`。
- 生成 `manage_device_runs` 与 `manage_summary`。
- 将 sync/monitor 的失败纳入 pipeline overall status。

### 4.3 Sync-to-v1 服务化

当前 sync-to-v1 已从 HTTP handler 抽出为 `RunSyncToV1`，可被 pipeline/ZB 内部调用。后续仍建议继续抽成独立 service，降低 API 层承载的业务逻辑：

```text
DeviceV2SyncToV1Service
  SyncBatch(ctx, req) -> resp
  SyncOne(ctx, code, options) -> item
  PushMonitor(ctx, syncResult) -> monitorResult
  PersistResult(ctx, result)
```

API 层只保留请求绑定、响应输出和权限边界。

### 4.4 Pipeline options 统一

所有入口必须共用同一套 options 默认化逻辑：

- HTTP API `device/v2/store/start`
- HTTP API `device/v2/store/retry`
- ZB 后台入库编排
- 后续内部任务重试

该逻辑应从 API 私有方法迁到可复用 helper/service，避免 ZB 直接调用 `EntityV2Srv.StartPipeline` 时绕过 DeviceCollection2 生产配置。

## 5. 状态模型

目标 pipeline 状态需要能表达以下终态：

| 状态 | 含义 |
| --- | --- |
| `prepare_failed` | prepare 阶段无可继续设备或关键准备失败 |
| `store_blocked` | store 阶段被规则、schema、DC2 或凭据阻断 |
| `store_success_manage_pending` | 核心入库成功，但尚未执行 manage |
| `sync_to_v1_failed` | sync-to-v1 失败 |
| `monitor_push_failed` | 监控推送失败 |
| `done_success` | 入库、同步、监控均成功 |
| `done_partial` | 批量任务部分设备成功、部分失败 |

现有 `success/partial/failed/blocked` 可继续作为外层状态，但 `result` 中必须保留更具体的阶段原因。

## 6. 改造拆分

### Phase 1: 基础抽取

- 抽出 `DeviceV2PipelineOptionBuilder`。
- 让 API 和内部调用共用 options 默认化。
- 保持现有 API 行为不变。

### Phase 2: Sync-to-v1 内部可复用与后续服务化

- 已从 `DeviceV2API.SyncToV1` 抽出内部方法 `RunSyncToV1`。
- 保持 API 响应结构兼容。
- 已修正新建 V1 设备时 `DeviceCode` 贯穿规则。
- 后续再把 `RunSyncToV1` 下沉为 service。

### Phase 3: Manage runtime

- 已在 entity pipeline 中新增 device_v2 manage runtime 接线。
- manage runtime 调用 `RunSyncToV1`，覆盖 sync-to-v1 与 monitor push。
- manage runtime 已写入 `manage_summary` 和每设备 `manage_device_runs`。

### Phase 4: 结果模型治理

- 已为 manage runtime 内部结果引入 typed struct，并在最终落库前转 `map[string]interface{}`。
- 已为 store runtime 批量 summary 引入 typed struct，稳定 `total/success/partial/failed/blocked/manual_pending/next_manage/observations/runtime_target` 字段。
- 已为 prepare runtime 批量 summary 引入 typed struct，稳定 `total/success/failed/prepared/runtime_target/prepare_request` 字段。
- 已为 prepare/store 单设备 run 的初始字段引入 typed builder，稳定基础字段与 legacy profile enrich 初始化。
- 后续继续将 prepare/store 单设备 run 的后续阶段状态变更收口为 typed 方法。
- 最终落库时再转 `map[string]interface{}`。
- 统一 callback、task summary、run summary 的字段命名。
- ZB callback 已临时在 map summary 中对齐 `status/v2_store_status/sync_to_v1_status/monitor_push_status`，后续 typed result 应复用这组字段。

### Phase 5: Store runtime 瘦身

- 拆分 `runMinimalDeviceV2StoreForDevice`。
- 将 DC2 采集、facts 回读、规则评估、core persist、extension persist、interface mirror 拆成独立函数或组件。

## 7. 验收重点

- API 启动 store pipeline 的行为保持兼容。
- 非 HTTP 入口启动 pipeline 时，DeviceCollection2 options 与 API 一致。
- Pipeline `manage` 阶段真实执行 sync-to-v1 和 monitor push。
- Device V2 code 与 Device V1 code 在 ZB 场景中保持一致。
- 批量任务按设备粒度产出结果，单台失败不阻断其他设备。
- 监控推送失败会体现在最终状态和回调明细中。

## 8. 闭环收尾状态

- 主链路已闭环：`prepare -> store -> manage(sync-to-v1 + monitor push)`。
- 内部复用入口已闭环：`StartDeviceV2StorePipeline`、`RunSyncToV1`、`RunDeviceV2ManageRuntime`。
- 结果模型治理已先完成批量 summary 与单设备 run 初始字段的 typed 收口；prepare/store 单设备后续状态变更仍可继续拆小步治理。
- 已知未闭环项不在 Device V2 主线接线内：ZB 采集配置渲染测试按人工要求暂不修复。
