---
topic: device-v2-management-ops-closure
kind: full-stack
title: Device V2 错误字段协同表与类型矩阵
createdAt: 2026-05-21T13:02:00+0800
---

# Device V2 错误字段协同表与类型矩阵

## 1. 目的

这份文档把“错误分层协同模型”落到更可执行的一层：

- 哪些错误类型是当前第一页必须承接的
- 每类错误前端应该展示哪几层
- 这些层分别来自哪些后端字段
- 字段不存在时，前端怎么降级

目标不是穷举全量异常，而是先覆盖本轮最关键的高价值链路：

1. `store/start` 后的采集失败
2. 单设备 `onboarding ensure` 后的继续纳管 / 监控失败

## 2. 统一展示层

所有错误类型都按同一套层级展示：

1. `结果`
2. `阶段`
3. `优先核对项`
4. `证据锚点`
5. `原始返回`

其中：

- `结果` 和 `阶段` 必须有
- `优先核对项` 能给则给，不能伪造
- `证据锚点` 优先展示稳定字段
- `原始返回` 永远默认收起

## 3. 采集链路错误类型矩阵

### T1. 缺少前置资料

场景：

- `D2_STORE_SCHEMA_REQUIRED_MISSING`
- `COLLECT_REQUIRED_FIELDS_MISSING`

结果层：

- `本次采集未完成`

阶段层：

- `准备资料`

优先核对项：

- `先补齐设备基础资料`

证据锚点来源：

- `process_result.steps[].details.missing_fields`
- `store_gate.missing_required_fields`

前端降级规则：

- 若明细字段为空，只展示 `请先补齐基础资料`

### T2. 缺少身份字段 / 身份冲突

场景：

- `D2_STORE_IDENTITY_REQUIRED`
- `D2_STORE_IDENTITY_CONFLICT`

结果层：

- `本次采集未完成`

阶段层：

- `准备资料` 或 `写入结果`

优先核对项：

- `核对 hostname / SN / asset_number 等身份锚点`

证据锚点来源：

- `decision.code`
- `decision.message`
- `process_result.steps[].error_code`

前端降级规则：

- 若没有字段级明细，至少保留 `设备身份信息不足` 或 `设备身份与现有记录冲突`

### T3. 接入目标未就绪

场景：

- `D2_STORE_TARGET_NOT_READY`
- `D2_STORE_ACCESS_NOT_READY`

结果层：

- `本次采集未完成`

阶段层：

- `准备资料` 或 `执行采集`

优先核对项：

- `核对接入目标地址、访问路径与控制器可达性`

证据锚点来源：

- `decision.code`
- `collection_plan_snapshot`
- 设备详情静态 `in_band_ip / out_band_ip`

前端降级规则：

- 若没有链路证据，则回退展示设备当前静态接入点信息

### T4. 缺少凭据

场景：

- `D2_STORE_CREDENTIAL_MISSING`

结果层：

- `本次采集未完成`

阶段层：

- `执行采集`

优先核对项：

- `补充或绑定访问凭据`

证据锚点来源：

- `decision.code`
- 设备静态 `credential_ref_in_band`
- 设备静态 `credential_refs.*`

前端降级规则：

- 若运行态凭据字段不存在，可明确标注“以下为设备当前保存凭据引用”

### T5. controller 探测失败，但用户不可被误导成“设备不可采”

场景：

- `D2_STORE_CONTROLLER_DETECT_FAILED`
- `controller_detect_failed`
- `no_data_collected`

结果层：

- `本次采集未完成`

阶段层：

- `controller 探测`

优先核对项：

- `优先核对正式链路使用的接入配置与凭据引用`
- `再核对目标地址、登录方式与设备实际能力是否匹配`

证据锚点来源：

- `decision.code`
- `decision.message`
- `device_collection2.reason`
- `device_collection2.failure_detail`
- `device_collection2.credential_ref_in_band`
- `onboarding action evidence.device_collection2`

前端降级规则：

- 如果只有 `D2_STORE_CONTROLLER_DETECT_FAILED`，不要翻译成 `设备 SSH 不通`
- 统一回退成：
  - `controller 未通过当前正式链路配置拿到可识别数据，请优先核对接入配置`

### T6. DC2 执行失败，但当前层被压成“未发起”

场景：

- `device_collection2.status=failed`
- 无 `run_id / facts / observation_count`

结果层：

- `本次采集未完成`

阶段层：

- `执行采集`

优先核对项：

- `核对本次 DC2 执行结果与 controller 返回`

证据锚点来源：

- `run_summary.device_collection2`
- `task.result.device_runs[].device_collection2`
- `onboarding action evidence.device_collection2`

前端降级规则：

- 若 `layers.collection_execution` 仍显示 `未发起 DC2`，以前端补充说明覆盖：
  - `后端未确认本次 DC2 成功执行；请继续核对下方失败证据`

### T7. 持久化失败

场景：

- `D2_STORE_PERSISTENCE_FAILED`

结果层：

- `本次采集未完成`

阶段层：

- `写入结果`

优先核对项：

- `联系平台支持核对结果写入链路`

证据锚点来源：

- `decision.code`
- `decision.message`
- `process_result.steps[].operator_message`

前端降级规则：

- 若缺少明细，保留平台侧失败，不误导用户去查设备

## 4. 继续纳管 / 监控链路错误类型矩阵

### O1. 继续纳管 controller-backed 失败

场景：

- `monitor_controller_stage`
- `status != success`

结果层：

- `本次继续纳管未完成`

阶段层：

- 取 `onboarding action evidence.controller_stage`

优先核对项：

- 若 evidence 中含 `device_collection2`，沿用采集链路优先核对项
- 否则基于 `reason / error_detail / message` 生成通用核对项

证据锚点来源：

- `actions[].evidence.task_id`
- `actions[].evidence.store_run_id`
- `actions[].evidence.controller_stage`
- `actions[].evidence.device_collection2`
- `actions[].evidence.decision`

前端降级规则：

- 若 action 存在但 evidence 不全，至少展示：
  - `controller 阶段`
  - `动作标签`
  - `reason`

### O2. sync-to-v1 失败

场景：

- 批量或单设备继续纳管中，V1 同步未成功

结果层：

- `本次继续纳管未完成`

阶段层：

- `同步到 V1`

优先核对项：

- `优先核对 V1 同步结果与目标设备映射`

证据锚点来源：

- `sync-to-v1 batch item`
- `monitor_push_status / monitor_push_error`
- `onboarding action reason`

前端降级规则：

- 若无法拿到设备级 item，只展示 `同步到 V1 未完成`

### O3. monitor push 失败

场景：

- `monitor_push_status=failed`
- `monitor_push_error` 存在

结果层：

- `本次监控推送未完成`

阶段层：

- `监控推送`

优先核对项：

- `核对监控推送任务与目标监控系统状态`

证据锚点来源：

- `monitor_push_status`
- `monitor_push_error`
- `sync-to-v1 batch item`

前端降级规则：

- 若只有状态没有错误，回退为 `监控推送未成功，请核对推送结果`

## 5. 字段协同表

| 展示层 | 优先字段 | 当前主要来源 | 无字段时降级 |
| --- | --- | --- | --- |
| 结果 | `process_result.overall_status` / onboarding action status | `task summary` / `onboarding evidence` | 用流程默认失败标题 |
| 阶段 | `process_result.steps[].step` / `controller_stage` | `task summary` / `actions[].evidence` | 用动作类型映射阶段 |
| 优先核对项 | `next_action` / `reason_code` / `message` / `next_check_items` | `process_result` / `decision` / `action evidence` | 用通用保守文案 |
| 证据锚点 | `credential_ref_in_band` / `snapshot_id` / `store_run_id` / `dc2_run_id` / `route` | `device_collection2` / `action evidence` / 设备静态字段 | 明确标记“当前只展示设备静态值” |
| 原始返回 | `storeSummary` / `storeDc2Evidence` / `onboardingEvidence.raw` | 现有接口 | 不做额外降级，保持只读展开 |

## 6. 前端固定降级原则

1. 没有稳定字段时，不猜最终根因。
2. 没有运行态凭据值时，不冒充“本次实际使用值”。
3. 没有阶段字段时，至少保留动作大类阶段。
4. 没有结构化优先核对项时，用保守提示，不把设备本身判死。
5. 原始返回永远不替代主承接区。

## 7. 后端补字段优先级建议

如果后端愿意补小范围稳定字段，优先级建议如下：

1. `stage`
2. `reason_code`
3. `next_check_items`
4. `evidence.credential_ref_in_band`
5. `evidence.snapshot_id`
6. `evidence.route`

原因：

- 前三项决定前端能否稳定做分层承接
- 后三项决定用户是否会被误导到错误排查方向

## 8. 与实现的关系

前端实现时，建议先做两块：

1. `store` 抽屉的采集失败承接卡
2. 单设备 `继续纳管` 的结果承接卡

这两块都应直接引用本矩阵，而不是在组件里散落 hardcode 规则。
