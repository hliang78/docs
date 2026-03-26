# RCA 平台无关最小输入输出契约

本文档只定义**根因定位机制本体**的最小输入输出。

这份契约与 OneOps 无关。

OneOps 在这里的角色只有一个：

- 把平台内的拓扑、告警、日志映射成这份契约

不讨论：

- 排序
- 置信度
- 历史因果分析
- 变更关联建模

---

## 1. 目标

当前机制只解决一个问题：

- 给定一份图结构、一次异常时间窗、一个异常对象集合，输出可解释当前异常的候选根因对象

这里的异常对象集合当前按失败节点集合处理。
因此桥接判定始终是围绕任意两台失败设备之间的最短路径关系展开。

当前输出的是：

- 节点候选
- 直接故障边候选
- 唯一最短路径桥接边/点候选
- 多路径公共桥接边/点候选

---

## 2. 最小输入

当前机制最小输入只分三部分：

1. 图快照
2. 异常上下文
3. 可选日志证据

### 2.1 图快照

```json
{
  "nodes": [
    {
      "node_id": "node-a"
    },
    {
      "node_id": "node-b"
    }
  ],
  "edges": [
    {
      "a_node_id": "node-a",
      "b_node_id": "node-b",
      "a_endpoint_id": "port-a",
      "b_endpoint_id": "port-b"
    }
  ]
}
```

当前长期必需字段只有：

- `node.node_id`
- `edge.a_node_id`
- `edge.b_node_id`
- `edge.a_endpoint_id`
- `edge.b_endpoint_id`

当前不作为机制必需字段：

- 节点名称
- 节点类型
- 边状态
- 边带宽
- 坐标
- 平台内部主键

### 2.2 异常上下文

```json
{
  "incident_id": "incident-1",
  "observed_at": "2026-03-23T10:00:00Z",
  "failed_node_ids": [
    "node-a",
    "node-b"
  ]
}
```

当前长期必需字段只有：

- `observed_at`
- `failed_node_ids`

`incident_id` 可选，只用于追踪。

### 2.3 可选日志证据

```json
{
  "observed_at": "2026-03-23T10:00:00Z",
  "node_ids_with_log_evidence": [
    "node-b"
  ]
}
```

当前日志只需要回答一个问题：

- 某个节点在当前观测时间窗内是否存在日志证据

当前不要求日志本体进入机制。

---

## 3. 最小输出

```json
{
  "incident_id": "incident-1",
  "observed_at": "2026-03-23T10:00:00Z",
  "candidates": [
    {
      "object_type": "edge",
      "object_key": "node-a:port-a|node-b:port-b",
      "a_node_id": "node-a",
      "b_node_id": "node-b",
      "a_endpoint_id": "port-a",
      "b_endpoint_id": "port-b",
      "explains_nodes": [
        "node-a",
        "node-b"
      ],
      "evidence_sources": [
        "alert",
        "topology"
      ],
      "assumptions": [
        "direct_failed_edge_only",
        "topology_input_normalized"
      ]
    }
  ]
}
```

每个候选最少包含：

- 候选对象类型
- 候选对象键
- 该候选解释了哪些异常对象
- 该候选依赖了哪些证据
- 该候选依赖了哪些前提

---

## 4. 机制约束

当前机制必须满足以下约束：

1. 若图输入不满足最小契约，直接报错
2. 若异常对象不在图中，允许跳过该对象
3. 若图为空，不报错，但返回空候选
4. 日志当前只作为附加证据，不改变候选类型
5. 任意两台失败设备之间若存在多条最短路径且没有公共桥接边/点，不强行给出桥接候选

这里还要补一条现实前提：

- 真实网络中，多路径通常是常态，不是例外

因此当前机制不能把“树形拓扑、唯一路径”当作默认输入假设。

---

## 5. OneOps 映射方式

OneOps 只负责把平台数据映射到这份契约。

当前映射关系应固定为：

| 平台无关字段 | OneOps 当前来源 |
| --- | --- |
| `node.node_id` | `topology.nodes[].device_code` |
| `edge.a_node_id` | `topology.edges[].a_device_code` |
| `edge.b_node_id` | `topology.edges[].b_device_code` |
| `edge.a_endpoint_id` | `topology.edges[].a_interface_code` |
| `edge.b_endpoint_id` | `topology.edges[].b_interface_code` |
| `failed_node_ids[]` | 告警标签中的 `device_code` |
| `observed_at` | 告警 `fired_at` / `active_at` |
| `node_ids_with_log_evidence[]` | 日志侧时间窗内存在证据的设备编码集合 |

这里的关键要求只有一个：

- 映射层可以替换，但机制契约不能跟着平台字段漂移

---

## 6. 当前结论

对当前需求，边界应固定为：

- 先定义并验证这份平台无关契约
- 再由 OneOps 负责映射
- OneOps 当前 `platform` / `topology` / `alert` 相关代码只视为适配实现，不视为机制本体
