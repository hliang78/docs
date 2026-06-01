---
topic: device-v2-management-ops-closure
kind: full-stack
title: Device V2 采集与监控错误可定位化研究
createdAt: 2026-05-21T12:35:00+0800
---

# Device V2 采集与监控错误可定位化研究

> 注：
> 当前是否把这套能力命名为“诊断”仍未最终确认。
> 本文里的“可定位化”应理解为“帮助前后端和运维对齐错误阶段、优先核对项与证据锚点”，而不是要求前端直接判定最终根因。

## 1. 研究目标

这份文档专项回答一个更窄的问题：

- 当前 `DeviceV2ManagementRedesign.vue` 在采集 / 继续纳管失败时，到底已经拿到了哪些后端证据
- 哪些证据被前端压平了，导致用户只能看到笼统失败
- 如果要把错误提示升级成“可定位表达”，第一批最合理的前后端协同边界在哪里

这份文档不讨论新增设备，也不重做整页信息架构，只聚焦：

- `store/start` 后的采集失败承接
- `onboarding ensure` 后的继续纳管 / 监控失败承接

后端全过程级的失败面拆解，另见：

- [backend-process-failure-map.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/device-v2-management-ops-closure/backend-process-failure-map.md)

## 2. 当前真实代码事实

### 2.1 Frontend 真实现状

当前目标页已经是：

- [DeviceV2ManagementRedesign.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:1)

采集链路这页已经接入：

- `getDeviceV2StoreTaskReq`
- `getDeviceV2StoreTaskSummaryReq`
- `listDeviceV2StoreRunsReq`
- `listDeviceV2StoreCollectionPlansReq`
- `getDeviceV2LastStoreCollectionDc2Req`

代码证据：

- [loadStoreEvidence](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:3876)

但当前页对采集失败的主承接仍有两个问题：

1. `store` 抽屉主视图优先读 `layers` / `process_result` 的压平结果，用户默认看到的是结论型摘要，不是诊断型摘要。
2. 原始 `summary` 与 `storeDc2Evidence` 虽然能在“原始返回 / JSON（排障用）”里看到，但没有被前置为第一层可定位线索。

代码证据：

- 采集抽屉主结构：[DeviceV2ManagementRedesign.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:636)
- 原始返回面板：[DeviceV2ManagementRedesign.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:894)

继续纳管 / 监控链路这页也已经接入了结构化 evidence：

- `getDeviceV2OnboardingEvidenceReq`
- `planDeviceV2OnboardingReq`
- `ensureDeviceV2OnboardingReq`

代码证据：

- [loadOnboardingEvidence](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:4066)
- [runOnboardingEnsure](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:4215)

但单设备继续纳管当前只把结构化 evidence 用在：

- 成功 / 失败 toast
- 内存态缓存

并没有在页面里渲染成稳定的错误诊断区块。

代码证据：

- `onboardingEvidence / onboardingActions / onboardingBlockedActions / onboardingFailedActions` 被写入状态，但没有模板消费：
  - [state 定义](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:1612)
  - [runOnboardingEnsure](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:4232)

### 2.2 Backend 真实现状

后端 `task summary` 已经把采集结果整理成：

- `layers.core_store`
- `layers.collection_execution`
- `layers.collection_gap`
- `process_result.steps`

代码证据：

- [buildMinimalStoreRunProcessResult](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_store_minimal_api.go:612)

但 `collection_execution` 当前只把 `device_collection2` 压成了“是否执行过 DC2”的一层抽象：

- `run_id / status / facts / observation_count` 命中即视为已执行
- 否则统一落成：
  - `headline = 本次未发起 DC2 采集`
  - `message = 当前没有发现本次 DC2 采集执行记录`

代码证据：

- [buildMinimalCollectionExecutionLayer](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_store_minimal_api.go:1014)

这意味着：

- 只要 `device_collection2` report 里没有 `run_id / facts / observation_count`
- 即使 report 里可能已经有 `failed / reason / failure_detail`
- 前端主层看到的仍然会更接近“没发起”而不是“发起了但失败了”

同时，`process_result.run_collection` 的失败文案也还是通用分流：

- `D2_STORE_CONTROLLER_DETECT_FAILED` -> “设备探测失败，请检查连通性和账号后重试”
- `D2_STORE_RUNTIME_FAILED / D2_STORE_DC2_REQUIRED_FAILED` -> “采集执行失败，请联系运维处理”

代码证据：

- [classifyCollectDecision](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_store_minimal_api.go:802)

继续纳管 / 监控这条链路，后端其实已经把更丰富的 evidence 放进 action 里了：

- `controller_stage`
- `store_run_status`
- `core_store_status`
- `manageable_status`
- `device_collection2`
- `decision`
- `store_summary`

代码证据：

- [buildControllerBackedMonitoringAction](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_onboarding_api.go:406)
- [formatOnboardingAction](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_onboarding_api.go:294)

但前端当前只把 controller 类 action 简化成：

- `controller 阶段 <stage>，store=<status> · core=<status> · manageable=<status>`

代码证据：

- [onboardingActionMessageText](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:2913)

这层简化没有继续展开 `action.evidence.device_collection2`，所以 `controller-backed` 动作里已经存在的 DC2 失败证据不会自然暴露出来。

### 2.3 设备侧已保存的凭据引用，前端其实能读到

当前详情侧栏已经能展示设备当前保存的：

- `attributes.credential_ref_in_band`
- `attributes.credential_refs.*`

代码证据：

- 凭证引用展示区：[DeviceV2ManagementRedesign.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:342)
- 行数据组装：[DeviceV2ManagementRedesign.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:2110)

但这块只在“设备静态详情”里展示，没有与“本次失败到底用了什么接入凭据引用”建立关联。

### 2.4 `last-store-collection-dc2` 目前只够做入口，不够做诊断

当前 `GET /device/v2/:code/last-store-collection-dc2` 只返回：

- `task_id`
- `store_run_id`
- `dc2_run_id`
- `target_id`
- `contract_key`

代码证据：

- [DeviceV2LastStoreCollectionDc2Resp](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/api/device/device-v2.ts:363)
- [GetLastStoreCollectionDC2](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_store_minimal_api.go:412)

所以它今天更适合“查看最后一次采集详细数据”的入口判断，不够支撑“为什么失败”的首层诊断。

## 3. 已确认的运行态事实

以下不是代码静态推导，而是你已明确确认的运行态事实，应视为本轮 PRD 的输入前提：

- 设备 `DVC631D6B2EB0FB` 本身不是“不能采集”。
- 直接按明文 `root / Admin@123` 调 controller 探测可以成功。
- controller 能识别：
  - `manufacturer = server`
  - `platform = base_linux`
  - `supported_collect_methods = [\"sshCommand\"]`
- 但走正式 `store/start` 链路时，同一台设备在 `device_collection2` 阶段被挡住。
- 被挡住时的 run summary 里出现过：
  - `credential_ref_in_band = vault_ssh_inband_root_admin@123_oneops_secrets`
  - `controller_detect_failed`
  - `SSH: no_data_collected`

这组事实意味着：

- 更准确的问题定义不是“设备 SSH 不通”
- 而是“正式链路里使用的凭据引用内容，与手工验证成功时的凭据不一致或解析结果异常”

## 4. 候选文档内容

### 4.1 问题定义

当前前端最大的问题不是“提示太少”，而是把多类失败压成了同一种表象：

- 表象：`controller 未能完成设备类型探测` / `no data collected` / `本次未发起 DC2 采集`
- 真实根因之一：正式链路使用的 `credential_ref_in_band` 对应内容异常

这会把用户引导去怀疑：

- 设备 SSH
- 网络
- SNMP
- 采集画像

而不是优先怀疑：

- Vault / credential_ref 内容

### 4.2 第一批协同模型至少要补的 3 层信息

#### 层 1：显示本次正式链路实际使用的接入信息摘要

优先展示：

- `带内凭据引用`
- `目标地址 / target_id`
- `contract_key`

推荐文案：

- `本次正式链路带内凭据引用：vault_ssh_inband_root_admin@123_oneops_secrets`

若后端没有返回“本次实际使用值”，则前端要显式降级：

- `当前页面仅能读取设备已保存的凭据引用，后端未回传本次正式链路实际使用值`

#### 层 2：对 `controller_detect_failed + no_data_collected` 做专门分流

不再直接归并成“检查连通性和账号”。

推荐表达方向：

- `控制器已发起本次探测，但未通过当前凭据引用拿到可识别数据；请优先核对凭据引用内容，再检查设备 SSH 连通性。`

#### 层 3：把 evidence 锚点前置成“可复制 / 可对照”的诊断项

优先项：

- `snapshot_id`
- `dc2_reason`
- `route = POST /api/v1/device/detect`
- `store_run_id`
- `dc2_run_id`

这些信息今天可能藏在原始 JSON、run summary 或 action evidence 里，但不该只存在于“排障用原始返回”里。

### 4.3 监控 / 继续纳管链路也要同步升级

单设备 `继续纳管` 当前已经拿到了 `actions / blocked_actions / failed_actions / unknown_actions`，但页面只 toast。

第一批应该把这部分变成“稳定可复核区块”，至少展示：

- 当前 controller 阶段
- 当前失败动作
- 首条关键 reason
- 如果失败来自 `device_collection2`，继续展开显示 DC2 诊断锚点

## 5. AI 推导建议

## 5.1 推荐方向

推荐走：

- `方向 B：前端优先落地 + 小范围补后端协同字段`

理由：

- 只做前端不够，因为 `last-store-collection-dc2` 当前拿不到失败原因和凭据引用。
- 一步做到完整运行态比对成本太高，容易把本轮从“错误可定位化”膨胀成“控制器 / Vault 调试平台”。
- 小范围后端补充一个稳定的错误协同结构，就能明显提升前端表达质量。

### 5.2 Direction A：纯前端版本

可立即落地：

- 在 `store` 抽屉主视图中增加“失败定位”卡片
- 从 `storeSummary.task.result.device_runs[0].device_collection2`、`storeSummary.run_summary`、`storeSummary.layers` 尝试抽取：
  - `reason`
  - `failure_detail`
  - `credential_ref_in_band`
  - `snapshot_id`
- 在单设备继续纳管结果中，把 `onboardingEvidence / actions` 渲染出来，而不是只 toast

限制：

- 是否能稳定拿到“本次正式链路实际使用的 credential_ref”取决于后端当前 summary 的真实字段路径
- 如果字段路径不稳定，前端只能做“尽量读取 + 明确降级”

### 5.3 Direction B：前端 + 小范围后端契约补充

建议新增一个稳定的协同块，优先挂在 `device_collection2` report 或 `layers.collection_execution.details` 下，例如：

```json
{
  "diagnostics": {
    "used_credential_ref_in_band": "vault_ssh_xxx",
    "dc2_reason": "controller_detect_failed",
    "dc2_message": "SSH: no_data_collected",
    "snapshot_id": "snap-xxx",
    "detect_route": "POST /api/v1/device/detect",
    "failure_class": "credential_ref_suspect"
  }
}
```

这样前端就不需要猜测字段路径，也能在失败卡片里稳定承接。

### 5.4 Direction C：完整对比“手工验证 vs 正式链路”

这会进一步要求：

- 后端记录手工验证结果
- 前端展示“双轨对照”

这方向诊断能力最强，但超出本轮页面专项范围，不建议第一批直接纳入。

## 6. 规划缺口

### 6.1 当前还缺少的确认

1. 运行态里 `credential_ref_in_band / snapshot_id / dc2_reason` 在 `store summary` 的稳定字段路径是什么。
2. 当前是否允许后端在 `last-store-collection-dc2` 或 `task summary` 增补专门的协同结构。
3. 单设备继续纳管结果是放：
   - 右侧详情
   - `store` 抽屉
   - 还是单独的小抽屉

### 6.2 当前最准确的候选结论

在没有进一步深挖 Vault 运行态前，本轮页面应优先收敛到这句产品结论：

- `这台设备能采；当前失败更应优先核对正式采集链路使用的 Vault 凭据引用内容，而不是先认定设备 SSH 本身不可用。`

这个结论不要求前端直接判定 Vault 配置是否错误，但要求前端把用户带到更接近真实根因的排查方向。
