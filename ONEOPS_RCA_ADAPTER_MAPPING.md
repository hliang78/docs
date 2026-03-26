# OneOps 到 RCA 契约的当前适配表

本文档只说明一件事：

- 当前 OneOps 数据如何映射到平台无关 RCA 最小契约

不讨论机制本体。

机制本体边界以：

- [RCA_PLATFORM_AGNOSTIC_MINIMAL_CONTRACT.md](/home/jacky/project/OneOPS-ALL/docs/RCA_PLATFORM_AGNOSTIC_MINIMAL_CONTRACT.md)

为准。

---

## 1. 映射原则

当前映射只遵守三条原则：

1. 先满足平台无关最小契约
2. 只做字段对应，不改机制语义
3. OneOps 字段可以调整，RCA 契约不跟着漂移

---

## 2. 图输入映射

当前图输入已经分成两条并行适配路径：

1. 旧 `AnalyzeConnectivity` 路径
2. 一期 `AnalyzeLayeredObservation` 路径

其中：

- 旧路径继续消费 `Graph`
- 一期新路径消费 `LayeredObservation`
- 两条路径共用 `app/topology` 的网络拓扑读取
- 只有当请求显式携带 `layered_input` 时，OneOps 才进入新路径

### 2.1 节点映射

| RCA 契约字段 | OneOps 当前字段 | 说明 |
| --- | --- | --- |
| `node.node_id` | `topology.nodes[].device_code` | 当前唯一必需字段 |
| `node.name` | `topology.nodes[].device_name` | 当前机制不依赖 |
| `node.type` | `topology.nodes[].device_type` | 当前机制不依赖 |
| `node.ip` | `topology.nodes[].ip` | 当前机制不依赖 |

### 2.2 边映射

| RCA 契约字段 | OneOps 当前字段 | 说明 |
| --- | --- | --- |
| `edge.a_node_id` | `topology.edges[].a_device_code` | 当前必需 |
| `edge.b_node_id` | `topology.edges[].b_device_code` | 当前必需 |
| `edge.a_endpoint_id` | `topology.edges[].a_interface_code` | 当前必需 |
| `edge.b_endpoint_id` | `topology.edges[].b_interface_code` | 当前必需 |
| `edge.a_endpoint_name` | `topology.edges[].a_interface_name` | 当前机制不依赖 |
| `edge.b_endpoint_name` | `topology.edges[].b_interface_name` | 当前机制不依赖 |
| `edge.status` | `topology.edges[].status` | 当前机制不依赖 |
| `edge.bandwidth` | `topology.edges[].bandwidth` | 当前机制不依赖 |

### 2.3 坐标映射

| RCA 契约字段 | OneOps 当前字段 | 说明 |
| --- | --- | --- |
| 不映射 | `topology.coordinates` | 当前不进入 RCA 主判定 |

### 2.4 一期分层节点类型映射

| RCA 契约字段 | OneOps 当前字段 | 说明 |
| --- | --- | --- |
| `nodes[].node_id` | `topology.nodes[].device_code` | 网络/服务器节点基础来源 |
| `nodes[].node_kind=network` | `topology.nodes[].device_type` 非 `server` | 当前按最小规则推断 |
| `nodes[].node_kind=server` | `topology.nodes[].device_type` 包含 `server` | 当前按最小规则推断 |
| `nodes[].node_kind=application` | `layered_input.extra_nodes[]` | 当前不从 `app/topology` 自动产出 |

当前说明：

- `application` 节点暂时只能由 OneOps 上层调用方显式补入 `layered_input`
- 当前不在适配层做应用对象发现与自动推断

### 2.5 一期分层边关系映射

| RCA 契约字段 | OneOps 当前字段 | 说明 |
| --- | --- | --- |
| `edges[].relation_kind=forwarding` | `topology.edges[]` | 当前网络拓扑边统一映射为转发边 |
| `edges[].relation_kind=hosting` | `layered_input.extra_edges[]` | 应用与服务器承载关系由调用方补入 |
| `edges[].relation_kind=dependency` | 暂不接入 | 第二轮才进入 |

当前说明：

- `dependency` 边当前保持冻结
- 一期只闭合 `forwarding + hosting`

---

## 3. 异常上下文映射

### 3.1 异常对象集合

| RCA 契约字段 | OneOps 当前字段 | 说明 |
| --- | --- | --- |
| `failed_node_ids[]` | `alert_alarm.labels.device_code` | 当前主路径从告警标签提取 |

当前兼容的标签键：

- `device_code`
- `deviceCode`
- `device_id`
- `deviceId`

当前建议长期收敛为：

- `device_code`

### 3.2 观测时间

| RCA 契约字段 | OneOps 当前字段 | 说明 |
| --- | --- | --- |
| `observed_at` | `alert_alarm.fired_at` | 优先使用 |
| `observed_at` | `alert_alarm.active_at` | `fired_at` 缺失时回退 |

### 3.3 追踪标识

| RCA 契约字段 | OneOps 当前字段 | 说明 |
| --- | --- | --- |
| `incident_id` | `request_id` | 当前只用于链路追踪 |

### 3.4 一期分层观测映射

| RCA 契约字段 | OneOps 当前字段 | 说明 |
| --- | --- | --- |
| `monitor_id` | `layered_input.monitor_node_id` | 当前监控源点 |
| `target_id` | `layered_input.target_node_id` | 当前分析目标 |
| `node_observations[]` | `layered_input.node_observations[]` | 当前节点 up/down 事实 |
| `active_path_edge_keys[]` | `layered_input.active_path_edges[]` | 当前实际监控路径 |
| `blocked_path_edge_keys[]` | `layered_input.blocked_path_edges[]` | 当前路径上已明确阻断的边 |

当前说明：

- 这些字段当前不由 OneOps 平台自动生成
- 现阶段只定义平台适配入口，不在平台层补推理

### 3.5 一期 `layered_input` 产出边界

当前必须固定一条边界：

- `layered_input` 不是 RCA 机制层生成的
- `layered_input` 也不是 `pkg/rca` 的责任
- 它必须由 OneOps 上游观测汇聚层产出后，再交给当前 RCA 适配入口

当前建议的一期产出顺序只允许是：

1. 先确定监控源点 `monitor_node_id`
2. 再确定分析目标 `target_node_id`
3. 再确定当前实际命中的路径 `active_path_edges`
4. 再确定路径上哪些边已经可明确判定阻断 `blocked_path_edges`
5. 再补节点 `up/down` 事实 `node_observations`
6. 最后补应用节点与 `hosting` 关系

当前明确不允许在 RCA 适配层承担：

1. 自动推导实际路径
2. 自动发现应用对象
3. 自动生成服务器承载关系
4. 自动把脏监控事实修补成完整输入

### 3.6 当前已知宿主与缺口

围绕第一轮输入，当前可以先固定这张判断表：

| `layered_input` 字段 | 当前最接近宿主 | 当前判断 |
| --- | --- | --- |
| `monitor_node_id` | remote 监控任务的实际执行 agent；`maintenance.monitor_probe` 只提供部署锚点 | 已有现实锚点，但还未统一成 RCA 监控源标识 |
| `target_node_id` | `device_code` / `application_v2.code` | 已有现实锚点，但还未统一为 RCA 目标标识 |
| `extra_nodes[].application` | `application/v2` | 已有宿主，但当前仍需上层显式补入 |
| `extra_edges[].hosting` | `application_v2.device_code` / `runs_on` | 已有现实锚点 |
| `node_observations[]` | 监控任务结果 | 当前没有统一 RCA 事实层 |
| `active_path_edges[]` | 暂无统一宿主 | 当前缺口 |
| `blocked_path_edges[]` | 暂无统一宿主 | 当前缺口 |

当前因此应固定两个判断：

1. `hosting` 不是第一轮的主要阻塞点
2. 真正的主要阻塞点是：
   - 路径事实
   - 阻断边事实
   - 统一的节点 up/down 事实

### 3.6.1 一期字段来源表

| `layered_input` 字段 | 现有最接近来源 | 当前状态 | 是否主阻塞点 |
| --- | --- | --- | --- |
| `monitor_node_id` | remote 监控任务的实际执行 agent；`maintenance.monitor_probe` 只提供部署锚点 | 已有现实锚点，但还未统一成 RCA 监控源标识 | 否 |
| `target_node_id` | `device_code` / `application_v2.code` | 已有现实锚点，但还未统一为 RCA 目标标识 | 否 |
| `extra_nodes[].application` | `application/v2` | 已有宿主，但当前仍需上层显式补入 | 否 |
| `extra_edges[].hosting` | `application_v2.device_code` / `runs_on` | 已有现实锚点 | 否 |
| `node_observations[]` | 监控任务结果 | 当前没有统一 RCA 事实层 | 是 |
| `active_path_edges[]` | 暂无统一宿主 | 当前缺口 | 是 |
| `blocked_path_edges[]` | 暂无统一宿主 | 当前缺口 | 是 |
| `log_evidence_node_ids[]` | 日志检索结果 | 当前已有布尔证据来源 | 否 |

这张表当前只用于一件事：

- 明确第一轮真实接入时，优先补哪几个字段的生产方

### 3.6.2 三个阻塞字段的最小生产契约

#### `node_observations[]`

当前最小字段固定为：

| 字段 | 要求 |
| --- | --- |
| `node_id` | 必须命中当前 RCA 节点集合 |
| `status` | 第一轮只允许 `up/down` |

当前只表达：

- 该节点在本次 `observed_at` 上被归一化成 `up` 或 `down`

当前不表达：

- `unknown`
- 分值
- 子健康项
- 时间序列

#### `active_path_edges[]`

当前最小字段固定为：

| 字段 | 要求 |
| --- | --- |
| `a_node_id` | 必须命中当前 RCA 节点集合 |
| `b_node_id` | 必须命中当前 RCA 节点集合 |

当前只表达：

- 这条转发边在本次观测里，确实命中了监控源到目标对象的实际路径

当前不表达：

- 路径顺序
- 多路径权重
- 置信度
- 路径推导过程

#### `blocked_path_edges[]`

当前最小字段也固定为：

| 字段 | 要求 |
| --- | --- |
| `a_node_id` | 必须命中当前 RCA 节点集合 |
| `b_node_id` | 必须命中当前 RCA 节点集合 |

当前必须满足一条约束：

- `blocked_path_edges[]` 必须是 `active_path_edges[]` 的子集

当前只表达：

- 该路径边已经被当前观测明确判定为阻断

当前不表达：

- 阻断原因分类
- 接口级底层指标
- 复杂故障画像

### 3.7 归一化层落点

基于当前宿主与缺口，`layered_input` 不应由现有适配入口直接硬编码拼装。

当前推荐落点固定为：

- `OneOps/app/platform/service`

当前推荐关系固定为：

1. `maintenance`
   - 继续提供探针部署点与探针配置事实
2. `application/v2`
   - 继续提供应用对象与 `runs_on` / `device_code` 事实
3. `platform/monitoring_v2`
   - 继续提供目标解析、任务投影、运行态快照事实
4. `app/topology`
   - 继续提供统一网络拓扑
5. 新的观测归一化层
   - 负责把以上事实收敛成 `layered_input`
6. `monitoring_root_cause_service.go`
   - 只消费归一化结果，不再自己拼装观测事实

当前最小代码落点也可先冻结为：

- `OneOps/app/platform/service/i_monitoring_root_cause_observation.go`

当前只定义一个最小接口：

```go
type IMonitoringRootCauseObservationNormalizer interface {
    BuildLayeredInput(ctx context.Context, req platformDTO.MonitoringRootCauseAnalyzeReq) (*platformDTO.MonitoringRootCauseLayeredAnalyzeInput, error)
}
```

这条接口当前只表达一个边界：

- `AnalyzeReq` 进入
- `layered_input` 出来
- 中间如何汇聚探针、应用、拓扑、运行态，不在这里展开

当前不建议让下面这些层直接负责 `layered_input`：

1. `pkg/rca`
2. `app/alert/api`
3. `monitoring_root_cause_service.go` 本体
4. 单独一个新的顶级 `rca` 业务模块

---

## 4. 日志证据映射

当前日志侧只需要映射一个结果：

- 某个设备编码在给定时间窗内是否存在日志证据

| RCA 契约字段 | OneOps 当前来源 | 说明 |
| --- | --- | --- |
| `node_ids_with_log_evidence[]` | 日志检索结果中的设备编码集合 | 旧路径只做布尔证据 |
| `log_evidence_node_ids[]` | `layered_input.log_evidence_node_ids` + `LogReader` 自动补充 | 新路径会在 service 中合并两者 |

当前不映射：

- 原始日志正文
- 日志严重级别
- 日志分类标签

---

## 5. 输出映射

### 5.1 候选对象

| RCA 契约字段 | OneOps 当前输出字段 | 说明 |
| --- | --- | --- |
| `candidate.object_type` | `object_type` | `node` 或 `edge` |
| `candidate.object_key` | `object_key` | 当前直接输出 |
| `candidate.node_id` | `device_code` | 节点候选 |
| `candidate.a_node_id` | `a_device_code` | 边候选 |
| `candidate.b_node_id` | `b_device_code` | 边候选 |
| `candidate.a_endpoint_id` | `a_interface_code` | 边候选 |
| `candidate.b_endpoint_id` | `b_interface_code` | 边候选 |

### 5.2 解释与证据

| RCA 契约字段 | OneOps 当前输出字段 | 说明 |
| --- | --- | --- |
| `candidate.explains_nodes[]` | `explains_devices[]` | 当前只是命名还未抽离 |
| `candidate.evidence_sources[]` | `evidence_sources[]` | 当前直接输出 |
| `candidate.assumptions[]` | `assumptions[]` | 当前直接输出，不改写 `unique_shortest_path_bridge` / `multi_path_common_bridge` 等机制前提 |

### 5.3 一期分层结论映射

| RCA 契约字段 | OneOps 当前输出字段 | 说明 |
| --- | --- | --- |
| `result.conclusion` | `conclusion` | 当前仅用于一期分层路径 |
| `result.reasons[]` | `reasons[]` | 当前仅用于 `unable_to_conclude_yet` 等明确原因 |

当前一期只允许三个结论值：

- `path_edge_root_cause`
- `server_root_cause`
- `unable_to_conclude_yet`

---

## 6. 当前适配边界结论

当前 OneOps 适配层的角色应固定为：

- 读取拓扑
- 读取告警
- 读取日志证据
- 做字段映射
- 调用 `pkg/rca` 中的平台无关 RCA 机制
- 返回 OneOps 风格结果

当前代码落点也应固定为：

- `OneOps/pkg/rca` 承担机制本体
- `OneOps/app/platform/api/monitoring_root_cause_adapter.go` 承担 platform API 请求归一化 helper
- `OneOps/app/platform/service/impl/monitoring_root_cause_service.go` 承担适配入口
- `OneOps/app/platform/service/impl/monitoring_root_cause_adapter.go` 承担 OneOps 字段映射 helper
- `OneOps/app/alert/api/alert_alarm_root_cause_adapter.go` 承担告警入口到 RCA 请求的归一化 helper

当前新增的一期分层输入落点固定为：

- `OneOps/app/platform/dto/monitoring_root_cause.go` 中的 `layered_input`
- `OneOps/app/platform/service/impl/monitoring_root_cause_service.go` 中的并行分支
- `OneOps/app/platform/service/impl/monitoring_root_cause_adapter.go` 中的 `LayeredObservation` 映射

当前 request / response 命名差异也应固定在这里收口：

- `platform/api` 中的请求 trimming 与基础归一化
- `failed_device_codes -> failed_node_ids`
- `layered_input.* -> LayeredObservation`
- `explains_nodes -> explains_devices`
- `node_id / a_node_id / b_node_id -> device_code / a_device_code / b_device_code`
- `alert/api` 中的 `alert_codes -> tenant_code / observed_at` 补齐逻辑

当前不应继续承担：

- 重新定义机制输入
- 修改机制判定语义
- 让平台字段直接替代机制契约

---

## 7. 后续收敛方向

后续若继续推进解耦，顺序固定为：

1. 先冻结这份适配表
2. 再继续收缩 OneOps DTO 在机制层中的残余痕迹
3. 最后把 OneOps 入口稳定为纯映射调用

当前阶段补充说明：

- 代码侧基线已冻结
- 真实数据执行当前延期
- 未来真实验收时，记录模板以 [ONEOPS_RCA_REAL_ACCEPTANCE_TEMPLATE.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_RCA_REAL_ACCEPTANCE_TEMPLATE.md) 为准
- 下一阶段开发边界以 [ONEOPS_RCA_NEXT_STAGE_BOUNDARY.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_RCA_NEXT_STAGE_BOUNDARY.md) 为准
