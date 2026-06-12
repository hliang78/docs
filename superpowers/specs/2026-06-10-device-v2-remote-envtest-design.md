# Device V2 Remote Environment Test Pack Design

Date: 2026-06-10

## Objective

为 Device V2 / ZB 入库链路设计一套**仓库内独立目录、弱依赖主代码、Python CLI 形态**的半自动测试包，用于：

1. 在指定远端独立环境中执行真实设备与真实链路测试。
2. 覆盖输入解释、采集入库、监控推送、监控任务落地、末端运行态验证。
3. 在大版本更新后作为标准回归包重复执行。
4. 输出机器可消费的结构化结果和人工可读的验收报告。

这套测试包不是单元测试替代品，也不是 CI 内部 stub 测试。它的定位是：

- **真实环境回归验收包**
- **版本升级后的链路验证包**
- **输入组合解释器稳定性验证包**

## Why This Package Exists

当前最容易反复出错的不是单个函数，而是整条链路上的“输入解释 -> 主入库 -> 监控推送 -> 任务状态 -> 末端运行态”一致性。

仅靠仓内单测无法回答下面这些问题：

1. 同一接入意图的不同写法，在真实环境里是否被解释成相同结果。
2. 冲突写法时，系统最终到底采用了哪个输入。
3. `monitor_push_status=success` 是否对应真实监控任务存在。
4. 任务是否在 Agent 真实落地、可对账、可观测。
5. OOB 或 monitor-only 场景下，没有真实目标时应如何给出可验收结论。

因此需要一套环境驱动、证据沉淀型的测试包。

## Design Principles

### 1. 真实环境优先

默认面向远端独立环境，不以 mock 成功为目标。

### 2. 输入组合优先

优先验证输入解释器，而不是只验证两三条最长路径。

### 3. 证据优先

每个结论都要能回落到 artifact：

- 原始请求
- `external_request_log`
- `entity_pipeline_task`
- 监控任务查询结果
- Agent / Prometheus / Loki 查询结果

### 4. 验收与运行态分层

平台侧编排成功，不必然等于末端数据成功。

### 5. 环境配置驱动

同一组标准 case 应可通过环境配置映射到不同远端环境。

## Package Shape

测试包放在仓库内独立目录，弱依赖主代码：

```text
tools/device_v2_envtest/
  README.md
  pyproject.toml
  configs/
    env.example.yaml
    suites/
      baseline.yaml
      full-regression.yaml
  cases/
    ic_01_linux_ssh.yaml
    ic_06_network_snmp.yaml
    ic_07_monitor_only.yaml
    ic_08_oob_ipmi.yaml
    ic_09_oob_redfish.yaml
    ic_12_legacy_vs_structured_conflict.yaml
  device_v2_envtest/
    cli.py
    runner.py
    models.py
    case_loader.py
    artifacts.py
    reporters/
      json_report.py
      markdown_report.py
      html_report.py
    probes/
      oneops_api.py
      mysql_probe.py
      monitoring_task_api.py
      agent_probe.py
      prometheus_probe.py
      loki_probe.py
```

## Runtime Capabilities

第一版测试包默认支持：

1. **OneOps API**
   - 发起 ZB / Device V2 请求
   - 轮询结果接口
2. **MySQL**
   - 查询 `external_request_log`
   - 查询 `entity_pipeline_task`
   - 查询必要的辅助表
3. **监控任务查询接口**
   - 验证任务是否真实生成
   - 验证任务状态是否可见、可对账
4. **Agent / Prometheus / Loki**
   - 验证任务是否落地到 Agent
   - 验证指标或日志是否可查询

## Output Model

每次执行同时生成两种输出：

1. **结构化 JSON**
   - 用于机器比较、历史比对、二次加工
2. **Markdown / HTML**
   - 用于人工验收、发群、留档

同时保存逐 case artifact：

```text
artifacts/<run_id>/<case_id>/
  request.json
  response.json
  request_log.json
  pipeline_task.json
  monitoring_tasks.json
  agent_probe.json
  prometheus_probe.json
  loki_probe.json
  final_case_result.json
```

## Execution Flow

每条 case 的执行流程固定成：

1. 根据 case 模板 + 环境配置生成请求 payload。
2. 调用 OneOps / ZB 入口发起请求。
3. 轮询 `external_request_log`，确认请求被接收。
4. 轮询 `entity_pipeline_task`，抽取 `device_runs` / `manage_device_runs`。
5. 查询监控任务接口，确认任务是否生成、是否可见、是否可对账。
6. 查询 Agent 任务状态，确认任务是否真实落地。
7. 可选查询 Prometheus / Loki，确认末端数据是否出现。
8. 汇总 case 结果，写入 artifact。
9. 汇总 suite 结果，生成 JSON / Markdown / HTML 报告。

## Case Model

测试包采用“内置标准 case + 环境配置映射”的双层模式。

### Built-in Standard Cases

测试包内置标准输入组合 case，例如：

- `IC-01` Linux SSH 基准
- `IC-06` Network SNMP 基准
- `IC-07` monitor-only 无 SSH
- `IC-08` OOB IPMI
- `IC-09` OOB Redfish
- `IC-12` legacy vs structured 冲突

### Environment Mapping

环境配置负责把 case 所需的设备、地址、凭据、Agent、末端查询信息映射到当前远端环境。

例如：

```yaml
devices:
  linux_ssh_01:
    device_code: AST-LINUX-01
    in_band_ip: 192.168.10.11
    ssh_credential_ref: cred-linux-01

  oob_ipmi_shadow_01:
    device_code: AST-OOB-01
    out_band_ip: 192.168.30.99
    ipmi_credential_ref: cred-ipmi-shadow
    runtime_expectation: expected_runtime_error
```

## Acceptance Model

这是本测试包最关键的语义设计。

### Four-Layer Evaluation

每条 case 按 4 层给结论：

1. **解释层**
   - 输入是否被解释成预期的 plane / protocol / credential source
2. **动作层**
   - 采集、主入库、监控推送是否执行
3. **落地层**
   - 监控任务是否真实存在、可见、可对账
4. **末端运行层**
   - Agent 执行是否成功
   - Prometheus / Loki 是否出现末端数据

### Result States

第一版不要只给 `pass/fail`，而是给更细粒度结论：

- `pass`
- `fail`
- `pass_with_expected_runtime_error`
- `blocked`
- `inconclusive`

### Expected Runtime Error Rule

对于**故意没有真实目标**的演练型 case，如果系统已经做到：

1. 输入被正确解释为 `out_band:ipmi` 或 `out_band:redfish`
2. 主入库成功
3. 监控任务成功下发
4. 监控任务在 Agent 真实存在
5. 后续因目标不存在、不可达、证书不通等原因在 Agent 侧报错

则这条 case 应判定为：

```text
platform acceptance = pass
runtime acceptance = expected error
final result = pass_with_expected_runtime_error
```

也就是说：

- 它是**可验收的**
- 不能算版本回归失败
- 报告里必须显式标注“预期运行态错误”

这条规则适用于：

1. OOB 无真实 IPMI / Redfish 目标
2. monitor-only 演练对象故意不可达
3. 为验证任务下发与 Agent 运行态而故意配置的 shadow target
4. 其它“没有真实目标，但希望验证平台编排链路”的演练型 case

## Verification Semantics

### Platform Acceptance Pass

满足下面条件即可认为平台侧通过：

1. 输入解释正确
2. 主入库成功或按预期成功进入 accepted / manage 阶段
3. 监控推送按预期执行
4. 监控任务真实生成
5. Agent 上能看到对应任务

### Runtime Acceptance Pass

在平台侧通过基础上，再满足：

1. Agent 任务状态健康
2. Prometheus 指标可见，或
3. Loki 日志 / trap 可见

### Runtime Acceptance Expected Error

以下情形不作为版本失败：

1. OOB 无真实目标
2. monitor-only 演练对象不可达，但平台编排链路正确
3. 故意构造缺失目标或不可执行输入，用于验证任务下发和运行态报错路径

## Report Semantics

报告中每条 case 至少给出：

1. `expected_interpretation`
2. `actual_interpretation`
3. `platform_acceptance`
4. `runtime_acceptance`
5. `final_result`
6. `reason`
7. `evidence_links`

示例：

```json
{
  "case_id": "IC-08",
  "platform_acceptance": "pass",
  "runtime_acceptance": "expected_error",
  "final_result": "pass_with_expected_runtime_error",
  "reason": "task reached agent and failed only because no real OOB target exists in this environment"
}
```

## Initial Suite

第一版 suite 固定为 6 条高价值 case：

1. `IC-01` Linux SSH 基准
2. `IC-06` Network SNMP 基准
3. `IC-07` monitor-only 无 SSH
4. `IC-08` OOB IPMI
5. `IC-09` OOB Redfish
6. `IC-12` legacy vs structured 冲突

理由：

1. 覆盖 in-band / out-band
2. 覆盖 ssh / snmp / ipmi / redfish
3. 覆盖 monitor-only
4. 覆盖 legacy / structured 冲突
5. 覆盖“真实成功”和“可验收的预期运行态错误”

## Non-Goals

第一版不追求：

1. 覆盖全部输入组合全排列
2. 替代现有单元测试或 E2E 测试
3. 自动化处理所有环境前置准备
4. 内建设备发现、凭据下发、Agent 部署
5. 处理全部 syslog / trap / 日志纳管动作

## Recommended Next Step

在这个设计获批后，下一步只做两件事：

1. 搭一个**最小可运行 Python CLI 脚手架**
2. 先实现：
   - 环境配置加载
   - case 模板加载
   - OneOps API 调用
   - MySQL 查询
   - JSON / Markdown 输出

Agent / Prometheus / Loki probe 可以在最小骨架跑通后补进第二步。
