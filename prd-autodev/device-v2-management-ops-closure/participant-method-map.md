---
topic: device-v2-management-ops-closure
kind: full-stack
title: Device V2 采集与监控参与方与关键方法地图
createdAt: 2026-05-21T17:10:00+0800
---

# Device V2 采集与监控参与方与关键方法地图

## 1. 目的

这份文档回答一个比“错误文案怎么写”更基础的问题：

- 整条采集 / 继续纳管 / 监控推送链路里，到底有哪些真实参与方
- 每个参与方在代码里对应哪些关键方法
- 每个参与方最值得前端承接的关键信息点和错误锚点是什么

只有先把参与方和方法串清楚，前端后续的错误表达才能避免：

- 把上游问题误说成下游问题
- 把平台配置问题误说成设备连通性问题
- 把凭据解析问题误说成目标设备不可采

## 2. 参与方总览

| 参与方 | 角色 | 关键方法 / 文件 | 典型输出 | 前端最值得承接的信息点 |
| --- | --- | --- | --- | --- |
| 前端 `DeviceV2ManagementRedesign` | 发起动作、承接摘要与 evidence | [DeviceV2ManagementRedesign.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:4559) | task_id、summary、actions、toast | 当前阶段、优先核对项、证据锚点 |
| Device V2 API | 编排入口 | [device_v2.go](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2.go:607) | store task、task summary | task_id、current_stage、overall_status |
| Store Summary 摘要层 | 把运行态压成摘要 | [device_v2_store_minimal_api.go](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_store_minimal_api.go:539) | layers、process_result | decision.code、process_result.steps、collection_execution |
| DeviceV2 / DeviceV1 模型层 | 设备静态事实来源 | [device_v2_sync_to_v1.go](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_sync_to_v1.go:600) | attributes、metadata、device_v1_code | 当前保存的 credential_ref、catalog、platform |
| Vault / Credential Resolver | 解析凭据引用 | [device_collection2.go](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device_collection2/service/impl/device_collection2.go:1524) | username/password/community 等 | 凭据引用、usage、解析是否成功 |
| Controller | 探测与远程执行 | [device_collection2.go](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device_collection2/service/impl/device_collection2.go:647) | `/api/v1/device/detect`、remote run | route、controller_url、controller_stage、failure_detail |
| DC2 | 采集运行时 | [device_collection2_run.go](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device_collection2/service/impl/device_collection2_run.go:1249) | target、run_id、facts、issues | target_id、contract_key、snapshot_id、dc2_reason |
| DeviceStore / Monitoring Apply | 同步后推送监控 | [device_store_controller.go](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/service/impl/device_store_controller.go:2890) | apply strategy result | monitor_push_status、agent_errors、zero success |
| Teleabs / StrategyApply | 监控策略分发服务 | [device_store_controller.go](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/service/impl/device_store_controller.go:2997) | success/fail count | strategy dependency、output dependency、apply result |
| Agent / 运行面 | 最终执行监控任务 | 由 strategy push 结果间接体现 | runtime task / agent errors | agent_errors、是否 zero success |
| 目标设备 | 被探测、被采集、被远程配置 | controller 与 syslog/snmp remote run 的真实目标 | SSH / SNMP / WinRM 回包 | address、login method、device-side delivery blocker |

## 3. 主链路分解

### 3.1 采集链路

```text
前端 startStoreForSelection
-> startDeviceV2StorePipelineReq
-> DeviceV2API.StartStorePipeline
-> 设备属性转 DC2 target
-> Vault 解析 credential refs
-> Controller /api/v1/device/detect
-> DC2 collect / facts / observation
-> Store summary / process_result
-> 前端 loadStoreEvidence
```

### 3.2 继续纳管 / 监控推送链路

```text
前端 runOnboardingEnsure
-> DeviceV2API.EnsureOnboarding
-> ensureMonitoringDispatchOnboarding
-> syncOneDeviceV2ToV1
-> DeviceStore.NotifyMonitorProbeByDeviceCodes
-> StoreController.NotifyMonitorProbe
-> StrategyApplySrv.ApplyStrategyAndPush
-> Agent / runtime execute
-> onboarding actions / evidence
-> 前端 loadOnboardingEvidence
```

### 3.3 设备侧交付链路

```text
EnsureOnboarding
-> ensureLogOnboarding / ensureSNMPTrapTargetOnboarding
-> DeviceV2Srv.GetByCode
-> Vault 解析 SSH / SNMP 凭据
-> Controller remote run
-> device_side_delivery_status / blocker
```

## 4. 各参与方的关键方法与可定位信息

### 4.1 前端

关键方法：

- [runStoreStart](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:4521)
- [loadStoreEvidence](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:4363)
- [loadOnboardingEvidence](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:4568)
- [runOnboardingEnsure](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:4715)

前端当前职责应该是：

- 发起动作
- 承接后端结构化 summary / actions / evidence
- 把错误分层呈现，而不是重新判根因

前端最该展示的锚点：

- `task_id`
- `store_run_id`
- `dc2_run_id`
- `credential_ref_in_band`
- `controller_stage`
- `v1_sync_status`
- `monitor_push_status`

### 4.2 Device V2 API 编排层

关键方法：

- [StartStorePipeline](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2.go:607)
- [GetTaskSummary](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2.go:683)
- [EnsureOnboarding](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_onboarding_api.go:2181)

这一层的意义是：

- 决定当前是直接 HTTP fail，还是进入 task / summary / actions
- 把多个后端服务串起来

关键错误定位点：

- 请求有没有创建出 `task_id`
- 失败发生在“启动前 / 运行中 / 摘要构建 / onboarding actions 回写”

### 4.3 摘要层与 process_result

关键方法：

- [buildMinimalStoreTaskSummary](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_store_minimal_api.go:539)
- [classifyCollectDecision](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_store_minimal_api.go:810)
- [buildMinimalCollectionExecutionLayer](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_store_minimal_api.go:1012)

这一层不是原始执行层，而是二次整理层。

关键价值：

- 给前端稳定 `decision.code`
- 给前端稳定 `process_result.steps`
- 形成统一摘要层

关键风险：

- 容易把 `controller_detect_failed`
- 和 `未发起 DC2`
- 压成相似表象

前端应该特别留意：

- `decision.code`
- `process_result.steps[].error_code`
- `process_result.steps[].operator_message`
- `layers.collection_execution.device_collection2`

### 4.4 Device V2 设备属性层

关键方法：

- [deviceV2ToDC2Target](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device_collection2/service/impl/device_collection2_run.go:1249)

这是“正式链路到底从设备上拿了什么静态输入”的核心入口。

关键字段来源：

- `in_band_ip`
- `management_ip`
- `credential_ref_in_band`
- `credential_refs.in_band`
- `credential_refs.ssh`
- `snmp_credential_ref`
- `winrm_credential_ref`
- `function_area`

前端可承接的价值：

- 当前保存值来自哪里
- 当前显示值是 `static` 还是 `runtime`

### 4.5 Vault / Credential Resolver

关键方法：

- [resolveCredential](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device_collection2/service/impl/device_collection2.go:1524)
- server/syslog 交付中的 [ResolveReference](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_onboarding_api.go:1166)

这一层解决的不是“设备通不通”，而是：

- 凭据引用是否存在
- 凭据服务是否可用
- 解析出的凭据内容是否完整

真实错误样本：

- `credential resolver is required for ssh credential_ref ...`
- `resolve ssh credential_ref ... failed: ...`
- `credential resolution failed: ...`
- `resolved ssh credential is missing username`
- `resolved ssh credential is missing password/private_key`

前端最值得展示的锚点：

- `credential_ref_in_band`
- 当前动作的 usage：`ssh` / `snmp` / `winrm`
- 是否是 `credential_missing`、`credential_resolution_failed`、`resolved_but_incomplete`

### 4.6 Controller

关键方法：

- [DetectDevice](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device_collection2/service/impl/device_collection2.go:647)
- [postController](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device_collection2/service/impl/device_collection2.go:1536)

Controller 参与了两类动作：

- 设备探测：`POST /api/v1/device/detect`
- 设备侧远程交付：controller remote run

关键定位点：

- `controller_url`
- `X-Controller-ID`
- `X-Function-Area`
- route
- `controller_stage`

关键风险：

- 这是“平台到 controller”的远程调用失败
- 不应简单翻译成“目标设备不通”

### 4.7 DC2 运行层

关键方法：

- [deviceV2ToDC2Target](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device_collection2/service/impl/device_collection2_run.go:1249)
- `DetectDevice` payload 组装

DC2 层决定：

- 用哪个地址探测
- 用哪个凭据引用
- 用哪个 contract / collection profile

关键锚点：

- `target_id`
- `contract_key`
- `run_id`
- `snapshot_id`
- `reason`
- `failure_detail`

你当前那组最重要的真实样本，本质上就属于这一层：

- `credential_ref_in_band = vault_ssh_inband_root_admin@123_oneops_secrets`
- `controller_detect_failed`
- `SSH: no_data_collected`

### 4.8 sync-to-v1

关键方法：

- [syncOneDeviceV2ToV1](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_sync_to_v1.go:600)
- [classifySyncToV1Failure](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_sync_to_v1.go:464)

这一层关心的是：

- V2 设备能不能被同步成 V1 设备
- V1 code 是否生成
- 凭据绑定是否成功
- 接口同步是否完成

关键错误样本：

- `设备资料还不完整，暂时无法继续。`
- `设备已进入旧台账，但访问凭据未完成绑定。`
- `设备已进入旧台账，但接口信息同步未完成。`
- `sync-to-v1 未返回 device_v1_code`

### 4.9 Monitoring Push / Strategy Apply

关键方法：

- [NotifyMonitorProbeByDeviceCodes](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/service/impl/device_store_service.go:363)
- [StoreController.NotifyMonitorProbe](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/service/impl/device_store_controller.go:2890)
- [classifyMonitorPushFailure](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_sync_to_v1.go:499)

这一层不是 SSH 采集，而是：

- 按设备类型筛监控目标
- 校验策略依赖
- 校验监控凭据绑定
- 调 `StrategyApplySrv.ApplyStrategyAndPush`

关键错误样本：

- `strategy apply service not configured`
- `teleabs strategy service not configured`
- `no eligible devices for monitoring task push`
- `apply monitoring strategy failed: ...`
- `monitoring strategy push failed: success=0 fail=%d agent_errors=%v`
- `monitoring strategy push finished with zero success`

这层的核心定位价值是：

- 它是平台策略 / Agent / 输出依赖问题
- 不应被前端说成“设备本身不可采”

### 4.10 Agent / Runtime

当前这条链里，Agent 更多是通过 `ApplyStrategyAndPush` 结果间接暴露。

前端短期不一定拿得到完整 agent runtime，但至少应承接：

- `agent_errors`
- `success_count / fail_count`
- `zero success`

因为这已经足够区分：

- 平台推送已发起
- 但执行端没有成功实例

### 4.11 目标设备

目标设备是真正被探测、被采集、被远程执行配置的一端。

它的关键事实包括：

- `address / in_band_ip`
- `login method / protocol`
- SSH / SNMP / WinRM 是否拿到可识别数据

但目标设备不是所有失败的默认责任方。

只有在以下场景才应优先指向设备：

- 地址不存在
- 设备端返回明确认证失败
- 设备侧 remote run blocker 明确指出设备参数缺失

## 5. 前端错误承接应如何利用这张参与方地图

最重要的不是“多显示字段”，而是先判断问题属于谁：

1. `启动前参数 / API 失败`
归属：前端请求或编排入口

2. `凭据引用缺失 / Vault 解析失败 / 解析结果不完整`
归属：凭据层

3. `controller_url / detect route / remote run 失败`
归属：平台到 controller

4. `no_data_collected / facts 为空 / contract mismatch`
归属：DC2 运行层与目标访问条件

5. `sync-to-v1 未返回 V1 code / 凭据绑定失败 / 接口同步失败`
归属：同步层

6. `monitor push failed / zero success / agent_errors`
归属：监控策略与 Agent 执行层

7. `device_side_delivery_blocker`
归属：设备侧交付链路

也就是说，前端应该先展示：

- 当前失败属于哪一类参与方
- 当前停留在哪一个方法阶段
- 当前最值得核对的证据锚点

而不是只展示“动作失败”。

## 6. 本轮对前端最关键的结论

这轮分析后，可以明确 3 条结论：

1. `credential_ref_in_band` 问题不是前端猜测，而是正式链路中的真实参与方问题。
因为它确实参与了 `deviceV2ToDC2Target -> resolveCredential -> controller detect`。

2. `monitor push` 也不是一个单点失败。
它至少跨过 `sync-to-v1`、监控策略选择、凭据绑定筛选、strategy apply、agent runtime` 几层。

3. 前端后续做错误承接时，应该优先按“参与方 + 阶段”分层，而不是只按“采集 / 监控”两个大类分层。

