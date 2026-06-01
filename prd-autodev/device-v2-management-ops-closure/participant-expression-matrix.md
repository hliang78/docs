---
topic: device-v2-management-ops-closure
kind: full-stack
title: Device V2 参与方到前端错误承接矩阵
createdAt: 2026-05-21T17:28:00+0800
---

# Device V2 参与方到前端错误承接矩阵

## 1. 目的

这份文档把 [participant-method-map.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/device-v2-management-ops-closure/participant-method-map.md) 继续压到前端实现层。

重点不是再讲一遍流程，而是回答：

- 当错误属于某个参与方时，前端应该怎么归类
- 该参与方最关键的字段是什么
- 应该如何提示用户，不误导排查方向
- 哪些文案可以说，哪些文案不能说

## 2. 统一承接原则

前端先做 4 个判断：

1. `属于哪个参与方`
2. `停留在哪个方法阶段`
3. `优先核对项是什么`
4. `有哪些证据锚点`

然后再决定 `结果标题` 和 `补充说明`。

前端不要先做的事：

- 先猜最终根因
- 先把问题归咎给目标设备
- 先把所有失败都翻译成“检查连通性”

## 3. 参与方承接矩阵

### P1. 前端 / API 编排入口

归属场景：

- `store/start` 直接 HTTP fail
- `get task summary` 直接失败
- `get onboarding evidence` 直接失败
- `ensure onboarding` 直接失败

关键方法：

- [runStoreStart](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:4521)
- [loadStoreEvidence](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:4363)
- [loadOnboardingEvidence](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:4568)
- [runOnboardingEnsure](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:4715)

关键字段：

- `task_id`
- HTTP error message
- `request_id`

前端结果标题建议：

- `这次操作暂时没有成功发起`

前端补充说明建议：

- `平台未返回可继续复核的任务结果，请先核对本次请求是否成功进入后台处理。`

优先核对项：

- 请求参数是否合法
- 是否生成 `task_id`
- 是否是 summary/actions 读取失败

不能直接说：

- `设备不可采`
- `监控推送失败`

### P2. Store Summary / 摘要层

归属场景：

- `decision.code` 已生成
- `process_result.steps` 已生成
- 但运行态细节被压平

关键方法：

- [classifyCollectDecision](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_store_minimal_api.go:810)
- [buildMinimalCollectionExecutionLayer](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_store_minimal_api.go:1012)

关键字段：

- `decision.code`
- `decision.category`
- `process_result.steps[].error_code`
- `process_result.steps[].operator_message`
- `layers.collection_execution.device_collection2`

前端结果标题建议：

- `本次采集未完成`

前端补充说明建议：

- `当前摘要层已确认采集未完成，但具体原因需要继续结合运行态证据查看。`

优先核对项：

- `D2_STORE_*` 属于哪一类
- `process_result` 的首个 problem step
- 是否出现“未发起 DC2”与运行态失败并存

不能直接说：

- `摘要里写未发起，所以本次一定没走到 DC2`

### P3. DeviceV2 静态属性层

归属场景：

- 前端只能读到设备当前保存的地址、功能域、凭据引用
- 但无法证明这就是本次正式链路实际成功使用值

关键方法：

- [deviceV2ToDC2Target](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device_collection2/service/impl/device_collection2_run.go:1249)

关键字段：

- `in_band_ip`
- `management_ip`
- `function_area`
- `credential_ref_in_band`
- `credential_refs.*`
- `snmp_credential_ref`
- `winrm_credential_ref`

前端结果标题建议：

- 不单独作为失败标题

前端补充说明建议：

- `以下为设备当前保存的接入信息，若后端未回传本次运行态值，请勿直接视为本次正式链路实际使用值。`

优先核对项：

- 地址是否为空
- 功能域是否为空
- 是否存在保存值与运行态 evidence 不一致

不能直接说：

- `当前保存的 credential_ref_in_band 就等于本次运行态使用值`

### P4. Vault / Credential Resolver

归属场景：

- 凭据引用缺失
- Vault/secret 解析失败
- 解析出的凭据内容不完整

关键方法：

- [resolveCredential](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device_collection2/service/impl/device_collection2.go:1524)
- [ResolveReference in onboarding remote delivery](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_onboarding_api.go:1166)

真实错误样本：

- `credential resolver is required for ssh credential_ref ...`
- `resolve ssh credential_ref ... failed: ...`
- `credential resolution failed: ...`
- `resolved ssh credential is missing username`
- `resolved ssh credential is missing password/private_key`

关键字段：

- `credential_ref_in_band`
- protocol / usage: `ssh` / `snmp` / `winrm`
- `device_side_delivery_blocker`

前端结果标题建议：

- `当前接入凭据条件未满足`

前端补充说明建议：

- `平台已找到凭据引用线索，但当前更值得优先核对凭据引用内容或解析结果，而不是先判断目标设备不可访问。`

优先核对项：

- 凭据引用是否为空
- Vault 解析是否报错
- 解析结果是否缺 `username`
- 解析结果是否缺 `password/private_key`

不能直接说：

- `SSH 不通`
- `设备登录失败`

除非后端明确返回了设备侧认证失败。

### P5. Controller

归属场景：

- `/api/v1/device/detect` 调用失败
- controller remote run 失败
- `controller_stage` 失败

关键方法：

- [DetectDevice -> postController](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device_collection2/service/impl/device_collection2.go:647)
- [postController](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device_collection2/service/impl/device_collection2.go:1536)

关键字段：

- `route`
- `controller_url`
- `controller_stage`
- `failure_detail`
- `reason`

前端结果标题建议：

- `控制器阶段未完成`

前端补充说明建议：

- `平台已进入控制器调用阶段，但控制器未返回可继续推进的有效结果。`

优先核对项：

- controller URL / function area 是否匹配
- detect route 是否正确
- controller 返回是不可用、超时还是业务失败

不能直接说：

- `目标设备不可达`

因为 controller 自身不可用、路由错误、鉴权错误都可能长得很像。

### P6. DC2 运行层

归属场景：

- `device_collection2.status=failed`
- `controller_detect_failed`
- `no_data_collected`
- contract / snapshot / target evidence 已出现

关键方法：

- [deviceV2ToDC2Target](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device_collection2/service/impl/device_collection2_run.go:1249)

关键字段：

- `target_id`
- `contract_key`
- `run_id`
- `reason`
- `failure_detail`
- `snapshot_id`
- `credential_ref_in_band`

前端结果标题建议：

- `本次采集未完成`

前端补充说明建议：

- `正式采集链路已进入 DC2 / controller 阶段，但当前没有拿到足够的可识别数据。`

优先核对项：

- `credential_ref_in_band`
- `target_id`
- `contract_key`
- `dc2_reason`
- `no_data_collected` 是否出现

更精确的推荐提示：

- `先核对凭据引用、登录方式和目标地址，再检查设备 SSH 连通性`

不能直接说：

- `本次没有发起 DC2`

除非运行态和摘要层都明确没有执行痕迹。

### P7. sync-to-v1

归属场景：

- V1 创建失败
- `device_v1_code` 未返回
- 凭据绑定失败
- 接口同步失败

关键方法：

- [syncOneDeviceV2ToV1](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_sync_to_v1.go:600)
- [classifySyncToV1Failure](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_sync_to_v1.go:464)

关键字段：

- `device_v1_code`
- `v1_sync_status`
- `v1_sync_message`
- `process_result.steps[].details.raw_message`

前端结果标题建议：

- `同步到 V1 未完成`

前端补充说明建议：

- `当前问题发生在旧设备台账同步阶段，监控推送可能尚未真正开始。`

优先核对项：

- 是否生成 `device_v1_code`
- 是否是凭据绑定失败
- 是否是接口同步失败

不能直接说：

- `监控推送失败`

如果上游 `sync-to-v1` 根本没过。

### P8. Monitoring Push / Strategy Apply

归属场景：

- `monitor_push_status=failed`
- `apply monitoring strategy failed`
- `no eligible devices`
- `zero success`

关键方法：

- [NotifyMonitorProbeByDeviceCodes](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/service/impl/device_store_service.go:363)
- [StoreController.NotifyMonitorProbe](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/service/impl/device_store_controller.go:2890)
- [classifyMonitorPushFailure](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_sync_to_v1.go:499)

真实错误样本：

- `strategy apply service not configured`
- `teleabs strategy service not configured`
- `no eligible devices for monitoring task push`
- `apply monitoring strategy failed: ...`
- `monitoring strategy push failed: success=0 fail=1 agent_errors=...`
- `monitoring strategy push finished with zero success`

关键字段：

- `monitor_push_status`
- `monitor_push_error`
- `monitor_push_device_codes`
- `agent_errors`

前端结果标题建议：

- `监控推送未完成`

前端补充说明建议：

- `当前问题发生在平台监控策略推送阶段，可能涉及策略、输出依赖、凭据绑定或 Agent 执行结果。`

优先核对项：

- 是否有符合条件的设备
- 监控策略与输出依赖是否齐全
- 是否存在 `agent_errors`
- 是否 `zero success`

不能直接说：

- `目标设备不支持监控`

除非后端明确给出的是设备类型不满足，而不是平台策略失败。

### P9. Agent / Runtime

归属场景：

- 推送已发起
- 但没有成功实例
- `agent_errors` 已存在

关键方法：

- 当前多通过 `ApplyStrategyAndPush` 结果间接暴露

关键字段：

- `agent_errors`
- `success_count`
- `fail_count`

前端结果标题建议：

- `监控任务已下发，但执行端未成功落地`

前端补充说明建议：

- `平台已发起推送，但当前没有成功执行实例，需要继续核对 Agent 执行侧结果。`

优先核对项：

- `agent_errors`
- `zero success`
- runtime task 是否存在

不能直接说：

- `平台未推送`

如果 evidence 已明确出现 push 尝试。

### P10. 目标设备

归属场景：

- 地址为空
- 设备侧认证失败
- syslog/snmp remote run blocker 明确指向设备端参数或回包问题

关键字段：

- `address`
- `remote_host`
- `login_method`
- `device_side_delivery_blocker`

前端结果标题建议：

- `目标设备侧条件未满足`

前端补充说明建议：

- `当前问题已定位到目标设备接入或设备侧交付条件。`

优先核对项：

- 地址是否为空
- 登录方式是否匹配
- 设备侧交付 blocker 具体内容

前端只能在这些条件满足时，才优先指向设备。

## 4. 当前最应该优先承接的高价值组合

### 4.1 `Vault + Controller + DC2`

这是你当前这个问题最贴近的组合。

典型链路：

```text
deviceV2ToDC2Target
-> resolveCredential
-> /api/v1/device/detect
-> controller_detect_failed
-> no_data_collected
```

前端应表现为：

- 参与方：`凭据 / 控制器 / 采集运行态`
- 阶段：`controller 探测`
- 优先核对项：
  - `正式链路凭据引用`
  - `目标地址`
  - `登录方式`
- 证据锚点：
  - `credential_ref_in_band`
  - `target_id`
  - `dc2_reason`
  - `snapshot_id`
  - `route`

### 4.2 `sync-to-v1 + monitor push`

这是继续纳管最容易被混淆的一组。

前端应先区分：

- 是 `sync-to-v1` 没过
- 还是 `monitor push` 自己失败

不能统一说成：

- `监控下发失败`

### 4.3 `monitor push + agent runtime`

这组必须和“设备不可采”剥离。

前端应优先表述成：

- 平台监控推送阶段未完成
- 已尝试推送但执行端没有成功实例

## 5. 对前端实现的直接约束

基于这张矩阵，`DeviceV2ManagementRedesign.vue` 后续应至少满足：

1. 每条主承接卡都能标出 `参与方`
2. `参与方` 与 `阶段` 不能混为一谈
3. `credential_ref_in_band` 一类字段必须带来源标签
4. `sync-to-v1` 与 `monitor push` 必须拆开
5. `agent_errors / zero success` 不能再被折叠成“监控失败”一句话
6. 主说明文案要先给出 `参与方语境`，再附上后端原始返回，避免用户第一眼只看到脱离责任面的技术句子

## 6. 一句收敛结论

后续前端最稳的错误表达模型，不应该只是：

- `结果`
- `阶段`
- `优先核对项`
- `证据锚点`

而应该升级成：

- `结果`
- `参与方`
- `阶段 / 方法`
- `优先核对项`
- `证据锚点`
- `原始返回`
