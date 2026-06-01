# OneOPS 根因定位测试数据集

本文档只提供当前主线所需的最小测试数据。

当前阶段说明：

- 代码侧基线已可执行并已跑通
- 真实数据执行当前延期，未来再做
- 历史验收模板、阶段边界等说明稿已删除，不再维护
- RCA 动画 demo 位于 `OneOps/static/rca-demo/index.html`
- 若 OneOps 服务已启动，可直接访问 `/static/rca-demo/index.html`
- RCA 最小场景编辑器位于 `OneOps/static/rca-scenario/index.html`
- 若 OneOps 服务已启动，可直接访问 `/static/rca-scenario/index.html`
- 场景编辑器使用前，可先执行 `bash OneOps/scripts/sync_rca_scenario_fixtures.sh`
- 该脚本会把 `app/platform/service/impl/testdata/scenarios/*.json` 同步到 `static/rca-scenario/fixtures/`
- 该脚本当前会先清理静态目录中的旧 `*.json`，避免源夹具删除后静态目录残留陈旧副本
- 场景编辑器导出的 JSON 可通过 `bash OneOps/scripts/import_rca_scenario_fixture.sh /abs/path/to/export.json` 导入到场景夹具目录
- 导入脚本会自动把文件写入 `app/platform/service/impl/testdata/scenarios/`，并继续同步到 `static/rca-scenario/fixtures/`
- 若要直接进入场景测试链，可执行 `bash OneOps/scripts/import_and_check_rca_scenario_fixture.sh /abs/path/to/export.json`

这些数据中，已经落成可执行平台无关夹具的部分位于：

- `OneOps/pkg/rca/testdata/direct_failed_edge.json`
- `OneOps/pkg/rca/testdata/ambiguous_shortest_path.json`
- `OneOps/pkg/rca/testdata/multi_path_common_bridge.json`
- `OneOps/pkg/rca/testdata/unique_bridge.json`
- `OneOps/pkg/rca/testdata/invalid_topology_contract.json`
- `OneOps/pkg/rca/testdata/layered/layered_path_edge_root_cause.json`
- `OneOps/pkg/rca/testdata/layered/layered_server_root_cause.json`
- `OneOps/pkg/rca/testdata/layered/layered_unable_to_conclude_yet.json`

对应的 OneOps 侧伪集成夹具位于：

- `OneOps/app/platform/service/impl/testdata/analyze_alerts_success_with_log.json`
- `OneOps/app/platform/service/impl/testdata/analyze_alerts_ambiguous_path.json`
- `OneOps/app/platform/service/impl/testdata/analyze_alerts_multi_path_common_bridge.json`
- `OneOps/app/platform/service/impl/testdata/analyze_alerts_invalid_topology.json`
- `OneOps/app/platform/service/impl/testdata/analyze_alerts_layered_path_edge_root_cause.json`
- `OneOps/app/platform/service/impl/testdata/analyze_alerts_layered_server_root_cause.json`
- `OneOps/app/platform/service/impl/testdata/analyze_alerts_layered_unable_to_conclude_yet.json`

当前新增的“场景构造主线”夹具位于：

- `OneOps/app/platform/service/impl/testdata/scenarios/path_edge_root_cause_minimal.json`
- `OneOps/app/platform/service/impl/testdata/scenarios/server_root_cause_minimal.json`
- `OneOps/app/platform/service/impl/testdata/scenarios/application_dependency_root_cause_minimal.json`
- `OneOps/app/platform/service/impl/testdata/scenarios/application_self_root_cause_minimal.json`
- `OneOps/app/platform/service/impl/testdata/scenarios/unable_to_conclude_minimal.json`
- `OneOps/app/platform/service/impl/testdata/scenarios/multi_path_common_blocked_edge.json`
- `OneOps/app/platform/service/impl/testdata/scenarios/multi_path_healthy_unable_to_conclude.json`

当前可直接执行的验收命令固定为：

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
GOCACHE=/tmp/go-build go test -run 'TestAnalyze(Connectivity|LayeredObservation)Fixtures' -v ./pkg/rca
GOCACHE=/tmp/go-build go test -run 'TestMonitoringRootCauseServiceAnalyzeAlertsFixtures' -v ./app/platform/service/impl
GOCACHE=/tmp/go-build go test -run 'TestMonitoringRootCauseScenario(Fixtures)?' -v ./app/platform/service/impl
GOCACHE=/tmp/go-build go test -run 'Test(MonitoringRootCauseAPIAnalyzeAlerts|AlertAlarmAPIAnalyzeRootCause)' -v ./app/platform/api ./app/alert/api
```

也可以直接执行：

```bash
bash /home/jacky/project/OneOPS-ALL/OneOps/scripts/run_rca_fixture_checks.sh
```

若是从场景编辑器新增夹具，建议固定流程为：

```bash
bash /home/jacky/project/OneOPS-ALL/OneOps/scripts/import_rca_scenario_fixture.sh /abs/path/to/export.json
GOCACHE=/tmp/go-build go test -run 'TestMonitoringRootCauseScenario(Fixtures)?' -v /home/jacky/project/OneOPS-ALL/OneOps/app/platform/service/impl
```

也可以直接缩成一条：

```bash
bash /home/jacky/project/OneOPS-ALL/OneOps/scripts/import_and_check_rca_scenario_fixture.sh /abs/path/to/export.json
```

执行顺序固定为：

1. 先跑 `pkg/rca` 平台无关机制夹具
2. 再跑 `platform/service/impl` OneOps 侧伪集成夹具
3. 最后跑 `platform/api` 与 `alert/api` 入口回归

若前一步失败，不进入下一步。

当前只覆盖五类场景：

1. 正常通过
2. 拓扑契约错误
3. 日志证据挂载
4. 两台失败设备之间存在多条最短路径且无公共桥接时，不强行输出桥接候选
5. 两台失败设备之间存在多条最短路径且有公共桥接边/点时，输出确定性候选

当前新增的一期分层夹具再覆盖三类场景：

1. 实际路径上的阻断边收敛
2. 承载服务器异常收敛
3. 路径与服务器都已排除，但当前阶段无法继续收敛

当前新增的场景构造夹具再覆盖五类前期场景：

1. 实际路径边阻断
2. 承载服务器异常
3. 应用依赖异常
4. 应用自身异常
5. 无法继续收敛

当前新增的中期第一版场景构造夹具再覆盖两类多路径场景：

1. 多路径下公共阻断边收敛
2. 多路径均健康但应用事实不足时保持 `unable_to_conclude_yet`

当前多路径场景表达边界固定为：

1. `active_path_edges` 记录的是已观测命中路径边的并集
2. `blocked_path_edges` 只用于表达“足以直接驱动当前 RCA 收敛的阻断边”
3. 当前还不能表达“仅部分分支阻断、但其他路径仍然可用”的细粒度路径组语义
4. 该类路径组语义当前只保留为未来边界，不进入现行夹具契约

不扩展到排序、置信度、历史因果分析。

### 当前夹具矩阵

| 夹具文件 | 层级 | 覆盖点 |
| --- | --- | --- |
| `OneOps/pkg/rca/testdata/direct_failed_edge.json` | 机制层 | 直接失败边 + 失败节点候选 |
| `OneOps/pkg/rca/testdata/unique_bridge.json` | 机制层 | 唯一最短路径桥接边/点候选 |
| `OneOps/pkg/rca/testdata/ambiguous_shortest_path.json` | 机制层 | 两台失败设备之间多路径歧义时不输出桥接候选 |
| `OneOps/pkg/rca/testdata/multi_path_common_bridge.json` | 机制层 | 两台失败设备之间多路径存在公共桥接边/点时输出确定性候选 |
| `OneOps/pkg/rca/testdata/invalid_topology_contract.json` | 机制层 | 拓扑契约错误直接报错 |
| `OneOps/pkg/rca/testdata/layered/layered_path_edge_root_cause.json` | 机制层 | 一期分层路径边阻断 |
| `OneOps/pkg/rca/testdata/layered/layered_server_root_cause.json` | 机制层 | 一期分层服务器异常 |
| `OneOps/pkg/rca/testdata/layered/layered_unable_to_conclude_yet.json` | 机制层 | 一期分层无法继续收敛 |
| `OneOps/app/platform/service/impl/testdata/analyze_alerts_success_with_log.json` | OneOps 伪集成层 | `AnalyzeAlerts` 主链路 + 日志证据挂载 |
| `OneOps/app/platform/service/impl/testdata/analyze_alerts_ambiguous_path.json` | OneOps 伪集成层 | 两台失败设备之间多路径歧义场景透传到 OneOps 输出 |
| `OneOps/app/platform/service/impl/testdata/analyze_alerts_multi_path_common_bridge.json` | OneOps 伪集成层 | 两台失败设备之间多路径公共桥接候选透传到 OneOps 输出 |
| `OneOps/app/platform/service/impl/testdata/analyze_alerts_invalid_topology.json` | OneOps 伪集成层 | 拓扑契约错误透传到 OneOps 适配链路 |
| `OneOps/app/platform/service/impl/testdata/analyze_alerts_layered_path_edge_root_cause.json` | OneOps 伪集成层 | 一期分层路径阻断从 `layered_input` 透传到 OneOps 输出 |
| `OneOps/app/platform/service/impl/testdata/analyze_alerts_layered_server_root_cause.json` | OneOps 伪集成层 | 一期分层服务器异常从 `layered_input` 透传到 OneOps 输出 |
| `OneOps/app/platform/service/impl/testdata/analyze_alerts_layered_unable_to_conclude_yet.json` | OneOps 伪集成层 | 一期分层无法继续收敛透传 `conclusion/reasons` |
| `OneOps/app/platform/service/impl/testdata/scenarios/path_edge_root_cause_minimal.json` | 场景构造层 | 场景 JSON 投影后收敛到路径边阻断 |
| `OneOps/app/platform/service/impl/testdata/scenarios/server_root_cause_minimal.json` | 场景构造层 | 场景 JSON 投影后收敛到服务器异常 |
| `OneOps/app/platform/service/impl/testdata/scenarios/application_dependency_root_cause_minimal.json` | 场景构造层 | 场景 JSON 投影后收敛到应用依赖异常 |
| `OneOps/app/platform/service/impl/testdata/scenarios/application_self_root_cause_minimal.json` | 场景构造层 | 场景 JSON 投影后收敛到应用自身异常 |
| `OneOps/app/platform/service/impl/testdata/scenarios/unable_to_conclude_minimal.json` | 场景构造层 | 场景 JSON 投影后收敛到无法继续收敛 |
| `OneOps/app/platform/service/impl/testdata/scenarios/multi_path_common_blocked_edge.json` | 场景构造层 | 多路径下公共阻断边收敛到 `path_edge_root_cause` |
| `OneOps/app/platform/service/impl/testdata/scenarios/multi_path_healthy_unable_to_conclude.json` | 场景构造层 | 多路径已知但路径健康时不强行收敛，保持 `unable_to_conclude_yet` |

---

## 1. 数据集 A：正常通过

### 1.1 租户

```json
{
  "tenant_code": "TENANT-A",
  "tenant_name": "Tenant A"
}
```

### 1.2 告警记录

用于 `alert/alarm/root-cause/analyze` 入口。

```json
[
  {
    "code": "alarm-a",
    "tenant_name": "Tenant A",
    "fired_at": "2026-03-23T10:00:00Z",
    "labels": {
      "device_code": "dev-a"
    }
  },
  {
    "code": "alarm-b",
    "tenant_name": "Tenant A",
    "fired_at": "2026-03-23T10:00:00Z",
    "labels": {
      "device_code": "dev-b"
    }
  }
]
```

### 1.3 统一拓扑输出

用于 `app/topology -> RCA` 主路径。

```json
{
  "nodes": [
    {
      "device_code": "dev-a",
      "device_name": "Device A",
      "device_type": "switch",
      "ip": "10.0.0.1"
    },
    {
      "device_code": "dev-b",
      "device_name": "Device B",
      "device_type": "switch",
      "ip": "10.0.0.2"
    }
  ],
  "edges": [
    {
      "a_device_code": "dev-a",
      "b_device_code": "dev-b",
      "a_device_name": "Device A",
      "b_device_name": "Device B",
      "a_interface_name": "Eth0/1",
      "b_interface_name": "Eth0/2",
      "a_interface_code": "if-a",
      "b_interface_code": "if-b",
      "status": "up",
      "bandwidth": "1000"
    }
  ],
  "coordinates": {
    "dev-a": {
      "x": 120,
      "y": 160
    },
    "dev-b": {
      "x": 320,
      "y": 160
    }
  }
}
```

### 1.4 告警入口请求

```json
{
  "request_id": "req-rca-a",
  "alert_codes": [
    "alarm-a",
    "alarm-b"
  ]
}
```

### 1.5 预期结果

```json
{
  "request_id": "req-rca-a",
  "tenant_code": "TENANT-A",
  "observed_at": "2026-03-23T10:00:00Z",
  "candidates": [
    {
      "object_type": "edge",
      "object_key": "dev-a:if-a|dev-b:if-b",
      "a_device_code": "dev-a",
      "b_device_code": "dev-b",
      "a_interface_code": "if-a",
      "b_interface_code": "if-b",
      "explains_devices": [
        "dev-a",
        "dev-b"
      ],
      "evidence_sources": [
        "alert",
        "topology"
      ],
      "assumptions": [
        "direct_failed_edge_only",
        "topology_input_normalized"
      ]
    },
    {
      "object_type": "node",
      "object_key": "dev-a",
      "device_code": "dev-a",
      "explains_devices": [
        "dev-a"
      ],
      "evidence_sources": [
        "alert",
        "topology"
      ],
      "assumptions": [
        "node_level_only",
        "topology_input_normalized"
      ]
    },
    {
      "object_type": "node",
      "object_key": "dev-b",
      "device_code": "dev-b",
      "explains_devices": [
        "dev-b"
      ],
      "evidence_sources": [
        "alert",
        "topology"
      ],
      "assumptions": [
        "node_level_only",
        "topology_input_normalized"
      ]
    }
  ]
}
```

---

## 2. 数据集 B：拓扑契约错误

这个数据集只用于验证 RCA 会直接报错。

### 2.1 错误拓扑

故意缺少 `b_interface_code`。

```json
{
  "nodes": [
    {
      "device_code": "dev-a"
    },
    {
      "device_code": "dev-b"
    }
  ],
  "edges": [
    {
      "a_device_code": "dev-a",
      "b_device_code": "dev-b",
      "a_interface_code": "if-a",
      "b_interface_code": ""
    }
  ],
  "coordinates": {}
}
```

### 2.2 预期错误

```text
topology contract is invalid: edge.a_interface_code and edge.b_interface_code are required
```

### 2.3 验收点

- RCA 不生成候选
- `platform` 入口透传该错误
- `alert` 入口也透传该错误

---

## 3. 数据集 C：日志证据挂载

### 3.1 基础拓扑

```json
{
  "nodes": [
    {
      "device_code": "dev-a"
    },
    {
      "device_code": "dev-b"
    }
  ],
  "edges": [
    {
      "a_device_code": "dev-a",
      "b_device_code": "dev-b",
      "a_interface_code": "if-a",
      "b_interface_code": "if-b"
    }
  ],
  "coordinates": {}
}
```

### 3.2 RCA 输入

```json
{
  "request_id": "req-rca-log",
  "tenant_code": "TENANT-A",
  "observed_at": "2026-03-23T10:00:00Z",
  "failed_device_codes": [
    "dev-a",
    "dev-b"
  ]
}
```

### 3.3 日志证据

只给 `dev-b`。

```json
{
  "tenant_code": "TENANT-A",
  "observed_at": "2026-03-23T10:00:00Z",
  "devices_with_log_evidence": [
    "dev-b"
  ]
}
```

### 3.4 预期结果

- `dev-b` 节点候选增加 `log`
- `dev-a:if-a|dev-b:if-b` 边候选增加 `log`
- `dev-a` 节点候选不增加 `log`

---

## 4. 使用方式

当前建议只按下面方式使用这三组数据：

1. 数据集 A 用于验证主路径能通
2. 数据集 B 用于验证错误暴露正确
3. 数据集 C 用于验证日志证据挂载正确

不要基于这份数据继续扩展排序、评分、历史因果相关测试。
