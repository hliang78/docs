# OneOPS RCA 场景 JSON 最小契约

本文档只定义用于 RCA 前期与中期测试的数据构造契约。

约束固定：

1. 围绕核心主线，不泛化，不衍生
2. 不冗余，不降级，不兜底，不智能
3. 主线闭环前，不做过度细节设计

本文档不是页面协议设计，也不是未来通用拓扑平台协议。
本文档只服务当前这条主线：

1. 构造测试场景
2. 生成 Prometheus 指标
3. 生成 Monitoring Map 最小事实
4. 压成 RCA layered input
5. 验证 RCA 输出

---

## 1. 契约目标

当前场景 JSON 只解决三件事：

1. 描述节点与关系
2. 描述当前观测事实
3. 描述预期 RCA 结论

因此，场景 JSON 必须能稳定投影成以下三类输出：

1. Prometheus 指标事实
2. Monitoring Map 事实
3. `pkg/rca` 可消费的 layered observation

---

## 2. 最小顶层结构

建议固定为：

```json
{
  "scenario_id": "scenario-path-edge-001",
  "scenario_name": "network path blocked before server",
  "tenant_code": "TENANT-A",
  "observed_at": "2026-03-24T10:00:00Z",
  "monitor_source": {},
  "nodes": [],
  "edges": [],
  "tags": [],
  "target_bindings": [],
  "node_observations": [],
  "observed_paths": [],
  "expected_rca": {}
}
```

当前只允许这些顶层块。

不增加：

1. UI 样式字段
2. 页面布局字段
3. 智能生成参数
4. 与主线无关的扩展元数据

当前装载规则固定为：

1. 场景 JSON 按严格模式解析
2. 未声明字段直接报错
3. `observed_path_groups` 等未来字段当前不允许混入

---

## 3. monitor_source

`monitor_source` 表示本次场景的观测起点。

最小结构：

```json
{
  "source_id": "src-agent-a",
  "agent_code": "agent-a",
  "device_code": "sw-core-a"
}
```

字段说明：

1. `source_id`
   - Monitoring Map `sources[].source_id`
2. `agent_code`
   - Monitoring Map `sources[].agent_code`
3. `device_code`
   - 对应 RCA `monitor_id`
   - 表示该监控源挂载在哪个节点上

当前只支持单监控源场景。

---

## 4. nodes

`nodes` 描述 RCA 图中的节点，不区分“设备对象”和“RCA 节点对象”两套模型，当前统一成一套。

最小结构：

```json
[
  {
    "node_id": "sw-core-a",
    "node_kind": "network",
    "node_name": "Core Switch A",
    "ip": "10.0.0.1"
  },
  {
    "node_id": "srv-app-a",
    "node_kind": "server",
    "node_name": "App Server A",
    "ip": "10.0.1.10"
  },
  {
    "node_id": "app-order",
    "node_kind": "application",
    "node_name": "Order Service"
  }
]
```

字段说明：

1. `node_id`
   - RCA 节点唯一标识
   - 后续直接映射到 layered `nodes[].node_id`
2. `node_kind`
   - 只允许：
   - `network`
   - `server`
   - `application`
3. `node_name`
   - 当前只用于页面显示和测试可读性
4. `ip`
   - 当前只作为设备基础信息保留

当前不拆：

1. 设备库存模型
2. 拓扑节点模型
3. RCA 节点模型

当前三者合一，先服务主线闭环。

---

## 5. edges

`edges` 描述节点之间的关系边。

最小结构：

```json
[
  {
    "a_node_id": "sw-core-a",
    "b_node_id": "sw-access-a",
    "relation_kind": "forwarding"
  },
  {
    "a_node_id": "srv-app-a",
    "b_node_id": "sw-access-a",
    "relation_kind": "forwarding"
  },
  {
    "a_node_id": "app-order",
    "b_node_id": "srv-app-a",
    "relation_kind": "hosting"
  },
  {
    "a_node_id": "app-order",
    "b_node_id": "app-inventory",
    "relation_kind": "dependency"
  }
]
```

字段说明：

1. `a_node_id`
2. `b_node_id`
3. `relation_kind`
   - 只允许：
   - `forwarding`
   - `hosting`
   - `dependency`

映射关系固定为：

1. `forwarding`
   - 对应网络转发路径边
2. `hosting`
   - 对应应用部署在服务器上
3. `dependency`
   - 对应应用依赖应用

当前不再额外保留另一套 relation_kind 命名空间。

---

## 6. tags

`tags` 用于对齐 OneOps 当前“标签附着”模式。

最小结构：

```json
[
  {
    "tag_key": "device_code",
    "tag_value": "srv-app-a",
    "attach_to_kind": "node",
    "attach_to_id": "srv-app-a"
  },
  {
    "tag_key": "app_code",
    "tag_value": "app-order",
    "attach_to_kind": "node",
    "attach_to_id": "app-order"
  }
]
```

字段说明：

1. `tag_key`
2. `tag_value`
3. `attach_to_kind`
   - 当前只允许：
   - `node`
   - `target`
4. `attach_to_id`

当前标签契约只做两件事：

1. 支持发生器生成 Prometheus label
2. 支持监控目标绑定

不做标签继承、标签模板、标签规则引擎。

---

## 7. target_bindings

`target_bindings` 用于表示“哪些对象是本次监控目标，以及它如何映射到 Monitoring Map target”。

最小结构：

```json
[
  {
    "target_id": "srv-app-a",
    "target_kind": "server",
    "node_id": "srv-app-a",
    "labels": {
      "device_code": "srv-app-a"
    }
  },
  {
    "target_id": "app-order",
    "target_kind": "application",
    "node_id": "app-order",
    "labels": {
      "app_code": "app-order"
    }
  }
]
```

字段说明：

1. `target_id`
   - Monitoring Map `targets[].target_id`
2. `target_kind`
   - Monitoring Map `targets[].target_kind`
   - 当前只允许：
   - `network`
   - `server`
   - `application`
3. `node_id`
   - 绑定到 RCA 节点
4. `labels`
   - Prometheus 发生器输出时附着的目标标签

---

## 8. node_observations

`node_observations` 表示节点观测事实。

最小结构：

```json
[
  {
    "node_id": "sw-core-a",
    "status": "up"
  },
  {
    "node_id": "srv-app-a",
    "status": "down"
  }
]
```

字段说明：

1. `node_id`
2. `status`
   - 只允许：
   - `up`
   - `down`

映射固定为：

1. Prometheus 侧由 `ping_result_code` 等指标生成
2. Monitoring Root Cause 归一化后进入 `node_observations`
3. RCA 最终消费的是 layered `node_observations`

当前场景 JSON 允许直接写入该事实，方便前期和中期测试。

---

## 9. observed_paths

`observed_paths` 表示当前已经知道的路径事实。

最小结构：

```json
[
  {
    "target_id": "srv-app-a",
    "target_kind": "server",
    "active_path_edges": [
      {
        "a_node_id": "sw-core-a",
        "b_node_id": "sw-access-a"
      },
      {
        "a_node_id": "sw-access-a",
        "b_node_id": "srv-app-a"
      }
    ],
    "blocked_path_edges": [
      {
        "a_node_id": "sw-access-a",
        "b_node_id": "srv-app-a"
      }
    ]
  }
]
```

字段说明：

1. `target_id`
2. `target_kind`
3. `active_path_edges`
4. `blocked_path_edges`

语义固定为：

1. `active_path_edges`
   - 表示本次场景认为“实际监控路径中被命中的路径边集合”
   - 不是全部拓扑边
   - 不是“只要 target up 就自动补齐”的拓扑推定边
   - 若当前只有 `monitor_source -> target` 的节点观测，而没有 L2/L3 转发路径证据，则不能把中间拓扑边直接写进这里
   - 若存在多路径，则这里记录的是“所有已观测命中路径边的并集”
   - 不强行压成单路径
2. `blocked_path_edges`
   - 表示本次场景认为“实际监控路径中已知阻断的边集合”
   - 必须属于 `active_path_edges` 的子集
   - 因此，如果某条边还不能被证明属于 `active_path_edges`，也不能直接写入 `blocked_path_edges`

当前额外边界：

1. 扁平 `blocked_path_edges` 只适合表达“这些阻断边足以直接驱动本次 RCA 收敛”
2. 它当前不能表达“多路径里只有部分分支阻断，但仍有其他分支存活”的细粒度路径组语义
3. 若未来需要表达这类场景，应单独增加路径组模型，而不是继续往当前扁平字段里塞隐含语义

### 9.1 未来路径组语义的预留边界

当前只保留边界，不启用字段。

只有同时满足以下条件，才允许引入未来路径组模型：

1. 已出现必须表达“部分分支阻断、其他分支仍存活”的稳定测试场景
2. 当前扁平 `blocked_path_edges` 已无法无歧义表达该场景
3. 引入路径组后仍然只服务当前 RCA 主线，不扩成通用路径编排模型

若未来真的引入，最小目标也只允许是：

1. 表达一组实际被命中的路径分支
2. 表达每组分支各自的 blocked / healthy 状态
3. 让 RCA 能区分“全部路径都断”与“只有部分路径断”

当前明确不做：

1. 在现有 `observed_paths` 上继续叠加隐含语义
2. 设计通用图查询 DSL
3. 设计路径权重、优先级、负载分担模型
4. 设计跨时间窗口的路径漂移分析

当前前期测试允许手工直接写入。
中期测试再逐步替换为从 `L2NodeMap`、`ArpTable`、L2/L3 forwarding reader 生成。

当前还需要明确区分两类模板语义：

1. 机制层模板
   - 允许直接写入“已预解析好的路径事实”
2. 当前平台采集模板
   - 只能写当前采集链条已经真实拿到的路径事实
   - 不能把纯拓扑边伪装成 `active_path_edges`

---

## 10. expected_rca

`expected_rca` 用于定义测试验收预期。

最小结构：

```json
{
  "target_id": "app-order",
  "conclusion": "server_root_cause",
  "candidate_object_keys": [
    "node:srv-app-a"
  ],
  "must_include_reasons": [
    "target_application_hosted_on_down_server"
  ]
}
```

字段说明：

1. `target_id`
   - 本次验收目标
2. `conclusion`
   - 只允许：
   - `path_edge_root_cause`
   - `server_root_cause`
   - `application_dependency_root_cause`
   - `application_self_root_cause`
   - `unable_to_conclude_yet`
3. `candidate_object_keys`
   - 允许为空
   - 用于校验主候选对象
4. `must_include_reasons`
   - 允许为空
   - 用于校验关键原因字段

---

## 11. 与现有代码的固定映射

### 11.1 到 Monitoring Map DTO 的映射

固定映射为：

1. `monitor_source`
   - `sources[]`
2. `target_bindings`
   - `targets[]`
3. `edges`
   - 按关系类型映射到 `relations[]`
4. `observed_paths`
   - 直接映射到 `observed_paths[]`

### 11.2 到 layered observation 的映射

固定映射为：

1. `monitor_source.device_code`
   - `monitor_id`
2. `expected_rca.target_id` 或场景指定 target
   - `target_id`
3. `observed_at`
   - `observed_at`
4. `nodes`
   - `nodes`
5. `edges`
   - `edges`
6. `node_observations`
   - `node_observations`
7. `observed_paths.active_path_edges`
   - `active_path_edge_keys`
8. `observed_paths.blocked_path_edges`
   - `blocked_path_edge_keys`

注意：

1. layered contract 里路径用的是 edge key
2. 场景 JSON 里路径先保持可读的边结构
3. 在投影阶段统一转换成 edge key

---

## 12. 当前固定校验规则

场景导入时必须校验：

1. `monitor_source.device_code` 必须存在于 `nodes`
2. `expected_rca.target_id` 必须存在于 `nodes`
3. `node_kind` 必须合法
4. `relation_kind` 必须合法
5. `node_observations.node_id` 必须存在于 `nodes`
6. `observed_paths.target_id` 必须存在于 `target_bindings`
7. `blocked_path_edges` 必须是对应 `active_path_edges` 子集
8. `expected_rca.conclusion` 必须合法

当前不做模糊修复，不做自动补全，不做推测容错。

---

## 13. 一个完整最小例子

```json
{
  "scenario_id": "scenario-server-root-cause-001",
  "scenario_name": "application down because hosted server is down",
  "tenant_code": "TENANT-A",
  "observed_at": "2026-03-24T10:00:00Z",
  "monitor_source": {
    "source_id": "src-agent-a",
    "agent_code": "agent-a",
    "device_code": "sw-core-a"
  },
  "nodes": [
    {
      "node_id": "sw-core-a",
      "node_kind": "network",
      "node_name": "Core Switch A",
      "ip": "10.0.0.1"
    },
    {
      "node_id": "srv-app-a",
      "node_kind": "server",
      "node_name": "App Server A",
      "ip": "10.0.1.10"
    },
    {
      "node_id": "app-order",
      "node_kind": "application",
      "node_name": "Order Service"
    }
  ],
  "edges": [
    {
      "a_node_id": "sw-core-a",
      "b_node_id": "srv-app-a",
      "relation_kind": "forwarding"
    },
    {
      "a_node_id": "app-order",
      "b_node_id": "srv-app-a",
      "relation_kind": "hosting"
    }
  ],
  "tags": [
    {
      "tag_key": "device_code",
      "tag_value": "srv-app-a",
      "attach_to_kind": "target",
      "attach_to_id": "srv-app-a"
    }
  ],
  "target_bindings": [
    {
      "target_id": "srv-app-a",
      "target_kind": "server",
      "node_id": "srv-app-a",
      "labels": {
        "device_code": "srv-app-a"
      }
    },
    {
      "target_id": "app-order",
      "target_kind": "application",
      "node_id": "app-order",
      "labels": {
        "app_code": "app-order"
      }
    }
  ],
  "node_observations": [
    {
      "node_id": "sw-core-a",
      "status": "up"
    },
    {
      "node_id": "srv-app-a",
      "status": "down"
    }
  ],
  "observed_paths": [
    {
      "target_id": "srv-app-a",
      "target_kind": "server",
      "active_path_edges": [
        {
          "a_node_id": "sw-core-a",
          "b_node_id": "srv-app-a"
        }
      ],
      "blocked_path_edges": []
    }
  ],
  "expected_rca": {
    "target_id": "app-order",
    "conclusion": "server_root_cause",
    "candidate_object_keys": [
      "node:srv-app-a"
    ],
    "must_include_reasons": [
      "target_application_hosted_on_down_server"
    ]
  }
}
```

---

## 14. 下一步只允许做的事

这份契约落定后，下一步只允许沿这个顺序推进：

1. 先写场景 JSON 到 layered input 的投影器
2. 再写场景 JSON 到 Prometheus 指标的发生器
3. 再补一组前期与中期标准场景
4. 最后再做页面编辑器

不允许先做重页面，再反推数据模型。
