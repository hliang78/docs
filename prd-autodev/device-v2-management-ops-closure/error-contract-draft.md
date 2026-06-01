---
topic: device-v2-management-ops-closure
kind: full-stack
title: Device V2 错误字段协同契约草案
createdAt: 2026-05-21T14:38:00+0800
---

# Device V2 错误字段协同契约草案

## 1. 目的

这份文档把前面的研究再往实现前推一层，重点回答 4 个问题：

- 前端错误承接到底从哪些后端来源取值
- 同一类信息有多个来源时，前端优先信谁
- 没有稳定字段时，前端如何保守降级
- 哪些地方值得后端补一个最小结构化契约

本文默认服务于 [DeviceV2ManagementRedesign.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:1) 第一批实现。

## 2. 适用范围

第一批只覆盖两类主承接场景：

1. `store` 抽屉里的采集失败承接
2. 右侧详情里的单设备继续纳管 / 监控推送失败承接

不覆盖：

- 批量级全局结果页重做
- 历史任务列表重构
- 监控数据面验证页

## 3. 统一前端视图模型

前端第一批建议统一收敛成一个轻量视图模型：

```ts
type ErrorCoordinationViewModel = {
  process: 'collect' | 'onboarding' | 'sync_to_v1' | 'monitor_push'
  resultTitle: string
  stageLabel: string
  priorityChecks: string[]
  evidence: Array<{
    key: string
    label: string
    value: string
    source: 'runtime' | 'persisted' | 'static'
  }>
  operatorMessage?: string
  rawSources?: Record<string, unknown>
}
```

这里最重要的是 `source`：

- `runtime`: 本次执行证据
- `persisted`: 最近一次动作回写结果
- `static`: 设备静态保存值

前端必须把 `static` 和 `runtime` 区分开，避免把设备当前保存值误当成“本次正式链路实际使用值”。

## 4. 采集失败字段契约

## 4.1 结果层

### 目标

给出一句稳定、可读、不过度下结论的业务结果。

### 来源优先级

1. `task summary.process_result.headline`
2. `task summary.layers.core_store.headline`
3. `selectedStoreRun.display_summary`
4. 固定降级文案

### 降级规则

- 若存在 `failed` / `blocked` step，优先取 `process_result.headline`
- 如果摘要层只有“本次未发起 DC2 采集”，但运行态另有失败 evidence，不直接复用这句做主标题
- 最差降级为：
  - `本次采集未完成`

## 4.2 阶段层

### 目标

明确告诉用户卡在哪一段。

### 来源优先级

1. `process_result.steps` 中第一个 `status != success` 的 step
2. `selectedStoreRun.current_step`
3. `onboarding failed action evidence.controller_stage`
4. `layers.collection_execution.status`

### 映射规则

| 原始值 | 前端阶段文案 |
| --- | --- |
| `prepare` | `准备资料` |
| `pre_register` | `准备入库` |
| `collect` / `collection` / `dc2` | `执行采集` |
| `run_collection` + `controller_detect_failed` | `controller 探测` |
| `persist_result` | `写入结果` |
| 未知 | `采集处理中` |

### 额外规则

- 若 `decision.code = D2_STORE_CONTROLLER_DETECT_FAILED`，即使 step 名只是 `run_collection`，前端也应映射成 `controller 探测`
- 若 `device_collection2.status=failed`，优先显示 `执行采集`

## 4.3 优先核对项

### 来源优先级

1. 基于 `decision.code / process_result.error_code / device_collection2` 的前端规则映射
2. 后端未来若补 `next_check_items` 则直接使用
3. 保守通用降级

### 当前建议映射

| 条件 | 优先核对项 |
| --- | --- |
| `COLLECT_REQUIRED_FIELDS_MISSING` / `D2_STORE_SCHEMA_REQUIRED_MISSING` | `先补齐设备基础资料` |
| `D2_STORE_IDENTITY_REQUIRED` | `核对 hostname、SN、asset_number 等身份字段` |
| `D2_STORE_IDENTITY_CONFLICT` | `核对设备身份是否与现有记录冲突` |
| `D2_STORE_CREDENTIAL_MISSING` | `补充或绑定访问凭据` |
| `D2_STORE_CONTROLLER_DETECT_FAILED` | `优先核对正式链路使用的接入配置与凭据引用` |
| `device_collection2.failure_detail` 含 `no_data_collected` | `先核对凭据引用、登录方式和目标地址，再检查设备 SSH 连通性` |
| `D2_STORE_PERSISTENCE_FAILED` | `联系平台支持核对结果写入链路` |
| 其他 | `查看本次采集详情并核对当前阻断项` |

### 约束

- 前端不能把 `controller_detect_failed` 直接翻译成 `设备 SSH 不通`
- 前端只能说“优先核对项”，不能冒充最终根因

## 4.4 证据锚点

### 推荐展示顺序

1. `credential_ref_in_band`
2. `target_id`
3. `store_run_id`
4. `dc2_run_id`
5. `contract_key`
6. `dc2_reason`
7. `snapshot_id`
8. `route`

### 来源优先级

| 证据项 | 优先来源 | 降级来源 | source 标记 |
| --- | --- | --- | --- |
| `credential_ref_in_band` | `selectedStoreRun.summary.device_collection2.credential_ref_in_band` | 设备详情 `attributes.credential_ref_in_band / credential_refs.*` | `runtime` -> `static` |
| `target_id` | `selectedStoreRun.summary.device_collection2.target_id` | `last-store-collection-dc2.target_id` | `runtime` -> `persisted` |
| `store_run_id` | `selectedStoreRun.run_id` | `last-store-collection-dc2.store_run_id` | `runtime` -> `persisted` |
| `dc2_run_id` | `selectedStoreRun.summary.device_collection2.run_id` | `last-store-collection-dc2.dc2_run_id` | `runtime` -> `persisted` |
| `contract_key` | `selectedStoreRun.summary.device_collection2.contract_key` | `last-store-collection-dc2.contract_key` | `runtime` -> `persisted` |
| `dc2_reason` | `selectedStoreRun.summary.device_collection2.reason` | `onboarding action evidence.device_collection2.reason` | `runtime` |
| `snapshot_id` | `selectedStoreRun.summary.device_collection2.snapshot_id` | 无 | `runtime` |
| `route` | `selectedStoreRun.summary.device_collection2.route` | 固定推导文案 | `runtime` -> `static` |

### 降级规则

- 若某字段只来自设备静态详情，前端标签需显式带上 `当前保存值`
- 若 `dc2_run_id` 缺失，不得推断“本次未发起”
- `route` 若无运行态字段，最多展示 `controller detect route` 这种保守说明，不要伪造精确调用链

## 5. 继续纳管 / 监控失败字段契约

## 5.1 结果层

### 来源优先级

1. `onboarding failed_actions / blocked_actions` 聚合结果
2. `onboarding evidence.summary`
3. 设备回写 `process_result.headline`
4. 固定降级文案

### 聚合规则

- 若存在 `monitor_dispatch` failed，标题优先为：
  - `本次继续纳管未完成`
- 若 `monitor_dispatch` 成功但 `log_forward / snmp_trap_target` 失败：
  - `监控已触发，设备侧纳管仍未完成`
- 若只有 blocked action：
  - `本次继续纳管暂未完成`

## 5.2 阶段层

### 来源优先级

1. `failed_actions[0].action`
2. `blocked_actions[0].action`
3. `monitor_dispatch evidence.v1_sync_status / monitor_push_status`
4. 固定降级

### 建议映射

| action / evidence | 阶段文案 |
| --- | --- |
| `monitor_controller_stage` | `controller 结果复核` |
| `monitor_dispatch` + `v1_sync_status=failed` | `同步到 V1` |
| `monitor_dispatch` + `monitor_push_status=failed` | `监控推送` |
| `log_forward` | `日志纳管` |
| `snmp_trap_target` | `SNMP Trap 纳管` |
| 其他 | `继续纳管处理中` |

## 5.3 优先核对项

### 当前建议映射

| 条件 | 优先核对项 |
| --- | --- |
| `v1_sync_status=failed` | `优先核对 V1 同步是否成功生成目标设备` |
| `monitor_push_status=failed` | `优先核对监控推送服务、策略与凭据条件` |
| `monitor_push_status=skipped` 且 `v1_sync_status=skipped/failed` | `先处理 V1 同步或 readiness 阻断，再重试监控推送` |
| `listener_service_needed=true` | `核对 area listener / collector / plan 配置` |
| `device_side_delivery_required=true` | `继续完成设备侧日志或 Trap 交付配置` |
| `device_collection2.reason` 非空 | `先回看最新 controller / DC2 采集结果` |

## 5.4 证据锚点

### 推荐展示顺序

1. `store_run_id`
2. `task_id`
3. `controller_stage`
4. `device_v1_code`
5. `v1_sync_status`
6. `monitor_push_status`
7. `listener_service_type`
8. `function_area`

### 来源优先级

| 证据项 | 优先来源 | 降级来源 | source 标记 |
| --- | --- | --- | --- |
| `store_run_id` | `failed/blocked action evidence.store_run_id` | 设备回写 `process_result.steps[].context.store_run_id` | `runtime` -> `persisted` |
| `task_id` | `failed/blocked action evidence.task_id` | `onboarding response.task_id` | `runtime` |
| `controller_stage` | `failed/blocked action evidence.controller_stage` | 无 | `runtime` |
| `device_v1_code` | `monitor_dispatch evidence.device_v1_code` | 设备 `attributes.device_v1_code` | `runtime` -> `persisted` |
| `v1_sync_status` | `monitor_dispatch evidence.v1_sync_status` | 设备 `attributes.sync_to_v1_status` | `runtime` -> `persisted` |
| `monitor_push_status` | `monitor_dispatch evidence.monitor_push_status` | 设备 `attributes.monitor_push_status` | `runtime` -> `persisted` |
| `listener_service_type` | `log_forward / snmp_trap_target evidence.listener_service_type` | 无 | `runtime` |
| `function_area` | `failed action evidence.function_area` | 设备静态 `attributes.function_area` | `runtime` -> `static` |

## 6. 来源可信度规则

同一信息多处可读时，前端统一采用这条规则：

1. 本次动作直接返回的结构化 evidence
2. 本次任务关联的 run / summary
3. 最近一次已回写到设备 attrs/meta 的结果
4. 设备静态详情

前端不要反过来用静态详情覆盖运行态 evidence。

## 7. 当前前端实现建议

## 7.1 采集失败承接

前端组装 `store` 抽屉失败卡时，建议优先读取：

1. `selectedStoreSummary.process_result`
2. `selectedStoreSummary.layers`
3. `selectedStoreRun.summary.device_collection2`
4. `storeDc2Evidence`
5. `selectedDevice` 静态凭据引用

### 关键判断

- 若 `process_result.steps` 已有 `failed/blocked` step，失败卡直接以它为主
- 若 `layers.collection_execution.headline=本次未发起 DC2 采集`，但运行态 `device_collection2.status=failed/reason!=空`，以前端失败卡覆盖这层摘要

## 7.2 继续纳管承接

前端组装右侧详情结果块时，建议优先读取：

1. `onboardingFailedActions`
2. `onboardingBlockedActions`
3. `onboardingActions`
4. `onboardingEvidence`
5. 设备 attrs/meta 上最近回写的 `sync_to_v1_status / monitor_push_status / process_result`

### 关键判断

- 单设备继续纳管结果不再只依赖 toast
- controller-backed action 和 `monitor_dispatch` action 必须拆开理解
- `monitor_push_status=skipped` 不应显示成“监控推送失败”

## 8. 值得后端补的最小契约

不是所有问题都要后端先改，但有 3 处值得补最小结构：

### 8.1 采集链路补 `device_collection2` 运行态摘要

建议至少稳定这些字段：

- `credential_ref_in_band`
- `target_id`
- `contract_key`
- `reason`
- `failure_detail`
- `snapshot_id`
- `route`

### 8.2 避免把失败 DC2 稳定压成“未发起”

建议在 `collection_execution` 层补一个更明确的状态枚举，例如：

- `dc2_not_triggered`
- `dc2_failed_before_result`
- `dc2_executed`

### 8.3 继续纳管统一补 `stage / reason_code`

当前 action evidence 已经够用，但如果后端愿意再往前迈一步，最有价值的是稳定补：

- `stage`
- `reason_code`
- `next_check_items`

这样前端规则会简单很多。

## 9. 规划缺口

当前仍有几个尚未完全确定的点：

- `device_collection2.reason / failure_detail / snapshot_id / route` 在所有失败样本里是否稳定存在
- `store` 抽屉当前选中的 run 与最近一次 `dc2 evidence` 是否总能一一对齐
- 继续纳管返回里的 `failed_actions` 顺序是否稳定，是否需要前端自行排序

这些点不阻塞第一版前端实现，但会影响后续是否需要同步补后端契约。
