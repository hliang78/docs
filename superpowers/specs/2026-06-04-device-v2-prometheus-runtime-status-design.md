# Device V2 Prometheus Runtime Status Design

## Goal

Device V2 设备页面需要把 Prometheus 感知到的设备真实运行状态纳入状态展示，同时保持监控任务覆盖状态、入库流程状态各自独立。页面不应再用历史 `monitor_push_status=success` 推断设备仍处于“监控已下发”，也不应把监控任务删除误解成设备真实离线。

## Current Facts

- 真实运行状态来自监控感知模块。
- `DeviceStatusPerceptionSrv` 查询 Prometheus 指标 `ping_result_code`。
- `ping_result_code=0` 映射为 `PowerON`，`1` 映射为 `PowerOFF`，`2` 映射为 `DeviceUnKnow`。
- 感知模块通过 `DeviceSrv.UpdateStatus` 写回 V1 `device.status`。
- Device V2 页面当前的“状态”列主要展示 `operational_status`，其中混入了入库流程、监控下发、agent 运行态等含义。
- `monitor_push_status` 是一次监控下发动作的历史结果，不代表当前仍存在有效监控任务。
- 当前是否存在监控任务，应以 `platform_monitoring_task_subject` 和由它汇总出的 `runtime_health.monitor_task_count` 为准。

## Status Layers

设备页状态拆成三层，每层含义独立。

### 1. Device Runtime Status

表示设备真实运行状态，也就是设备是否在线、是否可达。

数据来源：

- V1 `device.status`
- 由 Prometheus `ping_result_code` 感知后写回

建议状态：

| Code | Label | Source |
| --- | --- | --- |
| `power_on` | 运行中 | `device.status=PowerON` |
| `power_off` | 离线 | `device.status=PowerOFF` |
| `unknown` | 未知 | `device.status=DeviceUnKnow` 或空值 |

展示原则：

- 作为设备列表中的主状态。
- 不被监控下发成功、任务删除、入库成功覆盖。
- 如果 Prometheus 暂无数据，应显示“未知”，不要推断为离线。

### 2. Monitoring Coverage Status

表示当前设备是否已经被纳入监控任务，以及 agent 任务运行态是否正常。

数据来源：

- `platform_monitoring_task_subject`
- `runtime_health.monitor_task_count`
- `runtime_health.status`
- 当前任务的 projection/runtime 结果

建议状态：

| Code | Label | Meaning |
| --- | --- | --- |
| `monitor_not_bound` | 监控未下发 | 没有当前任务绑定 |
| `monitor_bound_pending_runtime` | 监控已下发，等待运行态确认 | 有任务绑定，但 agent 运行态尚未完整回传 |
| `monitor_runtime_healthy` | 监控运行正常 | 有任务绑定，运行态健康 |
| `monitor_runtime_degraded` | 监控运行异常 | 有任务绑定，存在失败、漂移或运行态异常 |
| `monitor_push_failed` | 监控下发失败 | 最近一次下发失败 |

展示原则：

- 作为真实运行状态下方的副状态。
- `monitor_push_status=success` 只能作为最近一次动作证据，不能单独决定“监控已下发”。
- 删除监控任务后，只要 `platform_monitoring_task_subject` 不存在，就应回到 `monitor_not_bound`。
- SNMP、IPMI、Redfish 不需要在页面状态模型里特殊分支；它们都是监控覆盖状态下的任务类型。

### 3. Store And Workflow Status

表示设备采集、入库、同步 V1、探测等流程状态。

数据来源：

- `process_result`
- `sync_to_v1_status`
- 入库/采集任务过程结果

建议状态：

| Code | Label | Meaning |
| --- | --- | --- |
| `collecting` | 采集中 | 正在采集或入库 |
| `store_ready` | 已入库 | 已具备 V1 同步结果 |
| `detect_failed` | 探测失败 | 控制器或现场探测失败 |
| `store_failed` | 入库失败 | 入库过程失败 |
| `sync_failed` | 同步失败 | sync-to-v1 失败 |

展示原则：

- 作为流程提示，不替代真实运行状态。
- 阻断型流程异常可以高亮展示，但仍保留真实运行状态。
- “已入库”不等价于“监控已下发”。

## UI Layout

设备列表建议将原“状态”列改为复合状态单元：

```text
运行中
监控已下发，等待运行态确认
已入库
```

当存在流程异常时：

```text
未知
监控未下发
探测失败：控制器无法连通
```

字段优先级：

1. 第一行固定展示真实运行状态。
2. 第二行展示监控覆盖状态。
3. 第三行仅在流程状态有异常、阻断或正在执行时展示。

颜色建议：

| Layer | Good | Warning | Error | Neutral |
| --- | --- | --- | --- | --- |
| Runtime | PowerON 绿色 | Unknown 灰/蓝 | PowerOFF 红 | - |
| Monitoring | Healthy 绿色 | Pending 蓝 | Failed/Degraded 红 | Not bound 灰 |
| Workflow | Ready 蓝 | Collecting 蓝 | Failed/Blocked 红 | Empty hidden |

详情页状态区建议使用更面向运维的文案：

```text
真实运行状态：运行中
来源：PING探测
最近感知：2026-06-04 20:30:00

监控状态：监控已下发，待确认
任务数：3
插件：带内SNMP / 带外SNMP / IPMI / Redfish

流程状态：已入库
同步状态：created
```

其中“PING探测”是页面展示文案，底层仍来自 Prometheus `ping_result_code` 感知结果。插件展示应使用任务目标和插件类型共同归一化：SNMP 需要区分带内 SNMP、带外 SNMP；IPMI、Redfish 归入带外管理协议。

## Backend Contract

建议 Device V2 API 输出三个独立字段：

```json
{
  "runtime_status": {
    "code": "power_on",
    "label": "运行中",
    "tone": "green",
    "source": "connectivity_check",
    "source_label": "PING探测",
    "observed_at": "2026-06-04T20:30:00+08:00"
  },
  "monitoring_status": {
    "code": "monitor_bound_pending_runtime",
    "label": "监控已下发，等待运行态确认",
    "tone": "blue",
    "task_count": 3,
    "healthy_task_count": 0,
    "failing_task_count": 0
  },
  "workflow_status": {
    "code": "store_ready",
    "label": "已入库",
    "tone": "blue",
    "summary": "设备已具备 V1 同步结果"
  }
}
```

兼容策略：

- 短期保留 `operational_status`，但它应逐步退化为 `workflow_status` 的兼容别名。
- 前端优先读取新字段；旧字段仅作为接口未升级时的兜底。
- 不再让 `operational_status=runtime_healthy/runtime_degraded` 同时承担监控覆盖和真实设备运行状态。

## Data Flow

```text
Prometheus ping_result_code
  -> DeviceStatusPerceptionSrv.Perception
  -> DeviceStatusPerceptionSrv.Compare
  -> DeviceStatusPerceptionSrv.ProcessCompareResult
  -> DeviceSrv.UpdateStatus
  -> V1 device.status
  -> Device V2 list/detail runtime_status
```

```text
Device V2 monitor push
  -> platform_monitoring_task
  -> platform_monitoring_task_subject
  -> projection/runtime health summary
  -> Device V2 list/detail monitoring_status
```

```text
Device V2 collect/store/sync
  -> process_result / sync_to_v1_status
  -> Device V2 list/detail workflow_status
```

## Filtering

设备页筛选也按三层拆分：

- `runtime_status`: 运行中、离线、未知。
- `monitoring_status`: 未下发、已下发待确认、运行正常、运行异常、下发失败。
- `workflow_status`: 采集中、已入库、探测失败、入库失败、同步失败。

旧的 `monitor_status` 筛选继续兼容，但语义应调整为“当前是否存在监控任务绑定”，不能再包含历史 `monitor_push_status=success`。

## Edge Cases

- 监控任务删除：`monitoring_status=monitor_not_bound`，真实运行状态保持 `device.status` 当前值。
- Prometheus 暂无该设备数据：`runtime_status=unknown`，不影响监控覆盖状态。
- 监控下发成功但 agent 未回传：`monitoring_status=monitor_bound_pending_runtime`。
- 监控任务运行异常：`monitoring_status=monitor_runtime_degraded`，真实运行状态仍由 Prometheus ping 决定。
- 入库失败但 Prometheus 仍能感知：真实运行状态照常展示，流程状态展示入库失败。
- SNMP/IPMI/Redfish 任一任务存在：都计入 monitoring coverage，插件类型作为详情信息，不改变状态层级。

## Implementation Scope

第一阶段：

- 后端保持真实运行状态写回链路不变。
- Device V2 API 增加 `runtime_status`、`monitoring_status`、`workflow_status`。
- 旧 `operational_status` 继续输出，但不再混合真实运行状态。
- 前端设备列表把“状态”列改为三层展示。
- 监控任务删除后，设备页立即回到“监控未下发”，但真实运行状态不变。

第二阶段：

- 详情页、筛选器、高级搜索同步使用三层状态。
- 废弃旧的 `monitor_push_status` 页面兜底逻辑。
- 将运行态时间、指标来源、任务类型展示到详情抽屉。
- 详情页插件列表按 `带内SNMP / 带外SNMP / IPMI / Redfish` 这类用户可理解名称展示。

第三阶段：

- 为 IPMI、Redfish 探测补充 monitoring coverage 的前置发现能力。
- 监控覆盖状态保留统一模型，不为插件类型增加特殊状态。

## Tests

后端测试：

- `ping_result_code=0` 写回 PowerON 后，Device V2 `runtime_status=power_on`。
- 删除 `platform_monitoring_task_subject` 后，即使 `monitor_push_status=success`，`monitoring_status=monitor_not_bound`。
- 有 task subject 但无 runtime projection 时，`monitoring_status=monitor_bound_pending_runtime`。
- runtime health degraded 时，`monitoring_status=monitor_runtime_degraded`，不覆盖 `runtime_status`。

前端测试：

- 设备列表同时展示真实运行状态、监控覆盖状态、流程状态。
- 删除监控任务后，页面不再显示“监控已下发”。
- PowerON + 监控未下发时，展示“运行中 / 监控未下发”。
- PowerOFF + 监控运行正常时，展示“离线 / 监控运行正常”，不互相覆盖。

## Non-Goals

- 不改变 Prometheus 指标采集规则。
- 不改变 `DeviceSrv.UpdateStatus` 的真实运行状态写回逻辑。
- 不要求本阶段验证指标最终进入 Prometheus。
- 不为 SNMP/IPMI/Redfish 做不同的页面状态分支。
