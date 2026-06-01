# ZB 入库接入 Device V2 主线设计

| 项目 | 内容 |
| --- | --- |
| 文档状态 | `active-design-draft` |
| 创建日期 | 2026-05-28 |
| 适用范围 | `ZbCallSrv.Store`、ZB 外部回调、Device V2 pipeline 接线 |
| 决策来源 | 2026-05-28 用户确认的关键决策 |

## 0. 当前推进状态

- 已将 `ZbCallSrv.Store` 主路径切到 Device V2：同步阶段只做前置校验并返回受理/失败；后台异步执行凭据引用 materialize、Device V2 seed/upsert、v2 pipeline，最后调用 `notifyExternalSystem`。
- 已从 `Store` 主路径移除 `RegisterDeviceInventory` 写入与 `DeviceStoreSrv.StoreDevices` 调用。
- 已补充 ZB 前置校验：`AttributionType/DeviceCode/DeviceName/SiteCode/RackCode`，服务器带内 SSH 必填，网络设备 SNMP community 必填且 SSH 可选但必须成对。
- 已把 ZB 明文凭据落到 legacy Secret/Community 并在 Device V2 上只保存 `credential_ref_in_band/snmp_credential_ref/credential_refs`。
- Device V2 pipeline `manage` 阶段已承载 sync-to-v1 与 monitor push；ZB 不再在 pipeline 外重复编排同步/监控。
- ZB callback summary 对外保持原 v1 字段 `device_code/device_name/store/msg`；内部汇总会从 pipeline `manage_device_runs` 读取 `status/sync_to_v1_status/device_v1_code/monitor_push_status`，并从 `device_runs` 兜底读取 `v2_store_status` 与阻断原因。
- 前置校验或后台 seed 阶段失败的设备也会进入最终 callback summary；整批都前置失败时仍会异步回调。
- `notifyExternalSystem` 已识别 Device V2 pipeline summary；新路径不再清理旧 `RegisterDeviceInventory`，旧 v1 兼容路径仍保留清理。
- 已补充 targeted tests 覆盖 ZB 凭据规则、Device V2 seed 不保存明文字段、`Store()` 同步返回老 step 契约、pipeline success/partial 映射，以及 callback summary 对外只下发 `device_code/device_name/store/msg`。

## 1. 目标

将 ZB 入库从 device v1 预入库/采集入库切换到 device v2 主线：

```text
ZB Store -> 前置校验 -> Device V2 seed/upsert -> Device V2 pipeline -> sync-to-v1 -> monitor push -> notifyExternalSystem
```

本次目标是彻底绕开 v1 预入库和 v1 采集入库：

- 不写 `RegisterDeviceInventory`。
- 不调用 v1 `DeviceStoreSrv.StoreDevices`。
- 不再通过 v1 request callback 触发 ZB 回调。
- 只在 device v2 完成后同步到 device v1，并推送监控。

## 2. 已确认决策

| 编号 | 决策 |
| --- | --- |
| D-001 | `ZbCallSrv.Store` 保持异步。 |
| D-002 | Device V2 入库包含远程采集、解析处理、同步 V1、推送监控全过程。 |
| D-003 | `DeviceCode` 必须贯穿 Device V2 和 Device V1。 |
| D-004 | V1 已存在时，允许 V2 更新并同步刷新 V1；ZB call API 层可另做存在性判断。 |
| D-005 | `site_code`、`rack_code` 是 ZB 必填，且解析不到真实记录时前置失败。 |
| D-006 | `platform_code`、`catalog_code` 不由 ZB 必填，后续通过采集判断。 |
| D-007 | `AttributionType` 只用于前置规则判断，不参与后续采集分类。 |
| D-008 | SSH/SNMP 凭据按引用落 V2，不在 V2 设备属性中保存明文。 |
| D-009 | 监控推送结果纳入最终回调。 |
| D-010 | 批量任务采用部分成功策略。 |
| D-011 | 彻底绕开 v1 预入库/采集入库。 |

## 3. ZB 前置校验

### 3.1 公共必填

- `DeviceCode`
- `DeviceName`
- `AttributionType`
- `SiteCode`
- `RackCode`

### 3.2 服务器设备

当 `AttributionType == 主机设备`：

- 必须有 `InBandIP`。
- 必须有 `InBandUsername`。
- 必须有 `InBandPassword`。

### 3.3 网络设备

当 `AttributionType == 网络设备`：

- 必须有 `InBandIP`。
- 必须有 `InBandCommunity`。
- SSH 可选。
- 如果传 SSH，则 `InBandUsername` 与 `InBandPassword` 必须同时存在。

### 3.4 基础引用

- `SiteCode` 必须能解析到 site。
- `RackCode` 必须能解析到 rack。
- 解析失败直接作为该设备前置失败，不进入 pipeline。

## 4. 字段落点

| ZB 字段 | Device V2 落点 | 说明 |
| --- | --- | --- |
| `DeviceCode` | `code`、`biz_code` | 必须贯穿 V2/V1 |
| `DeviceName` | `name`、`biz_name` | 设备显示名 |
| `AttributionType` | metadata 审计字段 | 只用于前置校验分支 |
| `SiteCode` | `site_code` | 前置解析必需 |
| `RackCode` | `rack_code` | 前置解析必需 |
| `InBandIP` | `in_band_ip`、access point | 采集入口 |
| `InBandUsername/InBandPassword` | SSH credential ref | 明文只用于创建/更新凭据 |
| `InBandCommunity` | SNMP credential ref | 明文只用于创建/更新凭据 |
| `FunctionArea` | `function_area` | 空值默认 `DefaultArea` |

## 5. 凭据策略

ZB 输入中的明文凭据只作为 materialize 输入：

- 服务器 SSH 创建或更新带内管理 Secret。
- 网络 SNMP 创建或更新带内 SNMP Community。
- 网络 SSH 可选，传入时创建或更新带内管理 Secret。

Device V2 只保存：

- `credential_ref_in_band`
- `snmp_credential_ref`
- `credential_refs`
- access point 上的 `credential_ref`

不保存：

- 明文 SSH 密码。
- 明文 SNMP community。

推荐使用稳定 ref 命名，避免重试产生重复凭据：

```text
zb-{device_code}-inband
zb-{device_code}-snmp-inband
```

最终命名需受现有 Secret/Community code 长度限制约束。

## 6. 异步编排

`ZbCallSrv.Store` 同步阶段：

1. 对每台设备做前置校验。
2. 返回每台设备的受理/前置失败 `StepProcessInfo`。
3. 对前置通过的设备启动后台编排。

后台编排阶段：

1. materialize 凭据。
2. upsert Device V2 source。
3. 启动 Device V2 pipeline。
4. pipeline `manage` 阶段执行 sync-to-v1 与 monitor push。
5. 从 pipeline result 汇总每台设备的端到端结果，并合并前置/seed 失败设备。
6. 调用 `notifyExternalSystem`。

如果没有任何设备进入 pipeline，则直接以异步方式回调前置/seed 失败 summary。

## 7. 回调语义

`notifyExternalSystem` 必须在完整链路结束后调用：

```text
Device V2 pipeline done -> sync-to-v1 done -> monitor push done -> callback
```

对外 callback summary 按设备保持原字段：

- `device_code`
- `device_name`
- `store`
- `msg`

对外兼容规则：

- `store`、`msg` 继续作为外部系统主要消费字段，避免 ZB 侧重构。
- `store=success` 只表示该设备端到端状态为成功；其他状态映射为 `store=failed`，具体原因放在 `msg`。
- `status`、`message` 与 v2 专用字段只保留在内部汇总/日志中，不默认下发给外部系统。

状态归因优先级：

1. `manage_device_runs.status`：覆盖 sync-to-v1 与 monitor push 的最终单设备状态。
2. `device_runs.status`：设备未进入 manage 时，使用基础入库/采集阶段状态。
3. 前置/seed 失败 summary：设备未进入 pipeline 时标记 `failed`，下游阶段标记 `skipped`。
4. `sync_to_v1` 直接响应：兼容非 pipeline 内部复用场景。
5. pipeline `overall_status` 或后台异常：兜底标记整链路状态。

顶层 `success` 仅表示整批全部端到端成功。部分成功时顶层 `success=false`，设备明细中体现成功设备。

### 7.1 同步返回兼容样例

`Store()` 同步返回仍保持原 `StepProcessInfo` 语义，只表示同步受理/前置失败，不表示 Device V2 最终入库成功：

```json
[
  {
    "device_code": "DVC-001",
    "device_name": "leaf-001",
    "step": "成功保存基础信息阶段",
    "step_key": "SuccessSaveBuildDeviceInStep",
    "process_status": true,
    "process_err_msg": ""
  },
  {
    "device_code": "DVC-002",
    "device_name": "leaf-002",
    "step": "基础信息入库阶段",
    "step_key": "BaseStep",
    "process_status": false,
    "process_err_msg": "site_code[SITE-X]不存在"
  }
]
```

### 7.2 最终回调兼容样例

Device V2 内部会保留 `status/v2_task_id/v2_store_status/sync_to_v1_status/monitor_push_status` 等明细用于归因，但传给外部系统的 callback payload 仍只下发原 summary 字段：

```json
{
  "request_id": "REQ-20260528-001",
  "success": true,
  "summary": [
    {
      "device_code": "DVC-001",
      "device_name": "leaf-001",
      "store": "success"
    }
  ],
  "timestamp": 1779984000
}
```

部分成功时仍保持同一 payload 形态：

```json
{
  "request_id": "REQ-20260528-002",
  "success": false,
  "summary": [
    {
      "device_code": "DVC-001",
      "device_name": "leaf-001",
      "store": "success"
    },
    {
      "device_code": "DVC-002",
      "device_name": "leaf-002",
      "store": "failed",
      "msg": "monitor push failed"
    },
    {
      "device_code": "DVC-003",
      "device_name": "leaf-003",
      "store": "failed",
      "msg": "site_code[SITE-X]不存在"
    }
  ],
  "timestamp": 1779984000,
  "msg": "ZB device_v2 入库存在1台设备前置/seed处理失败; pipeline: device_v2 pipeline partial: monitor push failed"
}
```

### 7.3 外部契约边界

- 入参字段会随 Device V2 前置要求调整：`AttributionType/DeviceCode/DeviceName/site_code/rack_code` 必填，服务器 SSH 密码必填，网络 SNMP community 必填。
- 同步返回字段名、`step/step_key/process_status/process_err_msg` 语义保持原样。
- callback 顶层字段 `request_id/success/summary/timestamp/msg` 保持原样。
- callback `summary` 对外只承诺 `device_code/device_name/store/msg`，不要求外部系统理解 Device V2 内部阶段字段。
- `success=false` 不等价于整批失败；外部系统应继续按每台设备的 `store` 判断设备级结果。

## 8. 验收清单

- `Store()` 不写 `RegisterDeviceInventory`，不调用 v1 `DeviceStoreSrv.StoreDevices`。
- 前置失败设备同步返回 `BaseStep` 失败，并进入最终 callback summary。
- 前置通过设备同步返回 `SuccessSaveBuildDeviceInStep` 成功，后台异步进入 Device V2 pipeline。
- Device V2 pipeline 的 `manage` 阶段必须执行 sync-to-v1 与 monitor push。
- monitor push 失败时，该设备 callback `store=failed`，成功设备仍 `store=success`。
- callback summary 不下发 `device_v2_code/task_id/status/v2_store_status/sync_to_v1_status/monitor_push_status` 等内部字段。
- Device V2 新路径不触发旧 `RegisterDeviceInventory` 清理；旧 v1 兼容路径保留清理。
- 已知配置渲染相关失败测试不纳入本轮修复范围，避免和当前主线混在一起。

## 9. 需要同步调整的旧逻辑

- `ZbCallSrv.Store` 不再检查 v1 存在后直接跳过。
- `ZbCallSrv.Store` 不再写 v1 `RegisterDeviceInventory`。
- `ZbCallSrv.Store` 不再注册 v1 `DeviceStoreSrv` callback。
- `notifyExternalSystem` 仅在旧 v1 兼容 summary 下清理 `RegisterDeviceInventory`；Device V2 pipeline summary 跳过该清理。
- `StoreCallback` 对非 200 响应目前只记录日志不返回错误，后续需纳入回调可靠性治理。

## 10. 推进拆分

### Phase 1: Device V2 主线基础改造

- 抽 pipeline options builder。
- 抽 sync-to-v1 内部复用入口，后续继续服务化。
- 修正 DeviceCode 贯穿 V1 创建。
- 新增 device_v2 manage runtime。

### Phase 2: ZB v2 编排服务

- 新增 ZB v2 前置校验。
- 新增 ZB payload 到 Device V2 seed 的 mapper。
- 新增凭据 materializer。
- 新增后台 orchestration，并改为由 pipeline manage stage 承载 sync/monitor。

### Phase 3: 回调与状态

- 已构造端到端 callback summary，并补齐每设备 `status/v2_task_id/v2_store_status`。
- 新路径中的 v1 inventory cleanup 已跳过，旧路径保留兼容清理。
- 已覆盖 manage 部分成功、store 阶段阻断、后台异常等结果；monitor push 失败通过 manage run 体现为单设备 `partial`。

### Phase 4: 测试

- 前置校验单测。
- mapper 单测。
- options builder 单测。
- sync-to-v1 service 单测。
- ZB Store 异步受理与 callback summary 单测。
- ZB 外部契约兼容单测：同步返回保持 `BaseStep/SuccessSaveBuildDeviceInStep`，callback summary 保持 `device_code/device_name/store/msg`。
- ZB pipeline success/partial 单测：seed 成功后模拟 v2 pipeline 成功、前置失败 + pipeline 成功 + monitor failed 的批量部分成功，外部 callback 仍保持老格式。

## 11. 闭环收尾状态

### 11.1 已闭环

- ZB 入库主路径已切到 Device V2，不再调用 v1 预入库/采集入库。
- Device V2 pipeline `manage` 阶段已覆盖 sync-to-v1 与 monitor push。
- ZB callback 已在 Device V2 完整链路结束后触发。
- 外部 callback payload 保持 legacy 结构，成功设备不会携带批次级 partial 错误 `msg`。
- 前置失败、seed 失败、store blocked、sync-to-v1 failed、monitor push failed、pipeline partial 均可落入设备级 `store/msg`。
- Device V2 新路径不触发旧 `RegisterDeviceInventory` 清理。

### 11.2 主线验收命令

```bash
go test ./app/entity/v2/service/impl -count=1
go test ./app/device/v2/api ./app/device/v2/service/impl -count=1
go test ./app/external_request/service/impl ./app/external_request/service/zb ./cmd -count=1
go test ./app/external_request/api -run '^$' -count=1
go test ./app/external_request/service/zb/impl -run 'TestValidateZbDeviceV2CredentialInputs|TestBuildZbDeviceV2SeedPayloadUsesCredentialRefsOnly|TestZbNotifySummaryUsesDeviceV2Pipeline|TestZbLegacyStoreCallbackSummaryStripsDeviceV2Fields|TestNotifyExternalSystemKeepsLegacySummaryContract|TestZbStoreKeepsLegacyStepContract|TestZbStorePipeline|TestZbDeviceV2' -count=1
go test ./app/external_request/service/zb/impl -run '^$' -count=1
```

### 11.3 已知未闭环项

- `go test ./app/external_request/service/zb/impl -count=1` 仍会触发既有配置渲染测试失败，本轮按人工要求暂不修复。
- `go test ./app/external_request/api -count=1` 中配置渲染相关 API 测试仍不纳入本轮主线验收。
- `StoreCallback` 的重试/可靠性治理仍是后续专项，不影响本轮 Device V2 主路径接线。
