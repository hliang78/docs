# OneOps EVE Network Mainline Testing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the approved OneOps EVE network-mainline testing design into a reusable execution baseline with standard scenario docs, addressing and port maps, execution runbooks, and first-wave evidence receipt templates for collection, monitoring, and topology.

**Architecture:** The implementation is docs-first and evidence-first. It starts by freezing the first standard `4+2+1` network scenario, then adds operator-facing runbooks and fixed receipt templates so later EVE runs produce comparable evidence instead of one-off notes. The deliverable is a shared testing framework inside `docs/testing`, not product-code changes in this round.

**Tech Stack:** Markdown docs, existing `docs/testing` baseline, EVE-NG operational conventions, OneOps controller/agent deployment assumptions, shell verification commands, `git -C docs`

---

## File Structure

Create or modify these files:

- Create: `docs/testing/phase1-network-mainline-standard-scenario.md`
  - The canonical first-wave scenario definition from the OneOps point of view.
- Create: `docs/testing/phase1-network-mainline-addressing-and-port-map.md`
  - The frozen ID, addressing, subnet, and link-to-interface allocation map.
- Create: `docs/testing/phase1-network-mainline-execution-runbook.md`
  - Step-by-step runbook for topology build, initialization checks, and ordered validation flow.
- Create: `docs/testing/phase1-network-mainline-collection-receipt-v1.md`
  - First standard collection evidence receipt for the mainline scenario.
- Create: `docs/testing/phase1-network-mainline-monitoring-receipt-v1.md`
  - First standard monitoring evidence receipt using the existing four-layer evidence model.
- Create: `docs/testing/phase1-network-mainline-topology-receipt-v1.md`
  - First topology evidence receipt that compares platform output against EVE truth.
- Create: `docs/testing/phase1-network-mainline-weak-point-register.md`
  - One place to classify findings into adaptation, task-chain, data-model, and topology-inference weaknesses.
- Modify: `docs/testing/phase1-first-batch-executable-checklist.md`
  - Add the network-mainline scenario as the next concrete execution pack.
- Modify: `docs/testing/README.md`
  - Link the new mainline scenario docs and receipts so the testing doc set stays discoverable.

Notes:

1. This plan intentionally stays inside `docs` because the next immediate need is a stable testing operating baseline, not product implementation.
2. Existing device standard-operation manuals remain the source of truth for per-device initialization. The new docs should reference them rather than duplicate vendor-specific commands everywhere.
3. The first execution pack should remain focused on `collection -> monitoring -> topology`; do not expand this plan to firewall policy generation or performance-scale replay.

### Task 1: Freeze the first standard network-mainline scenario

**Files:**
- Create: `docs/testing/phase1-network-mainline-standard-scenario.md`
- Create: `docs/testing/phase1-network-mainline-addressing-and-port-map.md`

- [ ] **Step 1: Verify the target files do not already exist**

```bash
test ! -f docs/testing/phase1-network-mainline-standard-scenario.md
test ! -f docs/testing/phase1-network-mainline-addressing-and-port-map.md
```

Expected: both commands exit `0`.

- [ ] **Step 2: Capture the existing upstream references that the new scenario must align to**

Run:

```bash
rg -n "phase1-real-device-test-matrix|eve-ng-current-environment-preparation-summary|phase1-a1-minimal-monitoring-task-evidence|testing-objective-basis" docs/testing docs/superpowers/testing/platform-testing-baseline
```

Expected: matches from the existing matrix, environment summary, monitoring evidence rule, and testing objective basis so the new scenario doc can point upward instead of restating the whole baseline.

- [ ] **Step 3: Write the standard-scenario document with the fixed first-wave structure**

Create `docs/testing/phase1-network-mainline-standard-scenario.md` with sections like:

```markdown
# 第一阶段网络设备主线标准场景

更新时间：2026-06-28
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份文档把 OneOps 第一条网络设备主线场景固定下来：

1. 不少于 `4` 台业务网络设备
2. `2` 台业务服务器
3. `1` 台观测服务器
4. 统一走管理平面
5. 验证顺序固定为 `采集 -> 监控 -> 拓扑`

## 2. 场景骨架

1. 管理网关交换机：统一承接管理网
2. 两台接入交换机：承接服务器与业务设备接入
3. 四台业务路由设备：组成全互联三层平面
4. 两台业务服务器：分别接入两台接入交换机
5. 一台观测服务器：部署 `controller + agent`
```

Also create `docs/testing/phase1-network-mainline-addressing-and-port-map.md` with:

```markdown
# 第一阶段网络设备主线地址与端口分配

## 1. 设备 ID

1. `GW = 1`
2. `ACC1 = 10`
3. `ACC2 = 20`
4. `R1 = 31`
5. `R2 = 32`
6. `R3 = 33`
7. `R4 = 34`
8. `S1 = 61`
9. `S2 = 62`
10. `OBS = 71`

## 2. 管理地址

1. `GW = 172.32.2.1`
2. `ACC1 = 172.32.2.10`
3. `ACC2 = 172.32.2.20`
4. `R1 = 172.32.2.31`
5. `R2 = 172.32.2.32`
6. `R3 = 172.32.2.33`
7. `R4 = 172.32.2.34`
8. `S1 = 172.32.2.61`
9. `S2 = 172.32.2.62`
10. `OBS = 172.32.2.71`
```

- [ ] **Step 4: Verify the new docs contain the fixed scenario anchors**

Run:

```bash
rg -n "4\\+2\\+1|采集 -> 监控 -> 拓扑|GW = 1|OBS = 71|172.32.2.254|172.32.69.34" docs/testing/phase1-network-mainline-standard-scenario.md docs/testing/phase1-network-mainline-addressing-and-port-map.md
```

Expected: hits for the scenario size, validation order, ID anchors, management gateway, and the final L3 mesh subnet.

- [ ] **Step 5: Commit the frozen scenario baseline**

```bash
git -C docs add testing/phase1-network-mainline-standard-scenario.md testing/phase1-network-mainline-addressing-and-port-map.md
git -C docs commit -m "docs: add phase1 network mainline scenario baseline"
```

### Task 2: Add the operator runbook for topology construction and ordered validation

**Files:**
- Create: `docs/testing/phase1-network-mainline-execution-runbook.md`

- [ ] **Step 1: Verify there is no existing runbook with the same name**

```bash
test ! -f docs/testing/phase1-network-mainline-execution-runbook.md
```

Expected: exit `0`.

- [ ] **Step 2: Collect the source docs that the runbook must cross-reference**

Run:

```bash
rg -n "拓扑生命周期|bridge|pnet0|管理网关|标准操作手册" docs/testing/README.md docs/testing/eve-ng-topology-lifecycle-validation.md docs/testing/eve-ng-bridge-pnet0-boundary-template.md docs/testing/eve-ng-mgt-gateway-topology-standard.md docs/testing/eve-ng-huawei-ar-router-standard-operation.md docs/testing/eve-ng-h3c-vsr-router-standard-operation.md docs/testing/eve-ng-linux-server-standard-operation.md
```

Expected: matches for topology lifecycle, bridge/pnet0 boundary, management gateway standard, and per-device operation manuals.

- [ ] **Step 3: Write the execution runbook with a strict phase order**

Create `docs/testing/phase1-network-mainline-execution-runbook.md` with sections like:

```markdown
# 第一阶段网络设备主线执行手册

## 1. 执行前提

1. Cisco 管理网关可复用
2. Huawei AR 与 H3C VSR 标准模板已可登录
3. 业务服务器模板已可登录
4. `OBS` 已准备好部署 `controller + agent`

## 2. 执行顺序

1. 建拓扑
2. 设备初始化复核
3. 管理平面连通性验证
4. 业务平面地址与 OSPF 配置
5. 采集基线
6. 监控基线
7. 拓扑基线
8. 关闭设备并清理拓扑

## 3. 退出原则

1. 采集不过，不进入监控
2. 监控不过，不进入拓扑
3. 每阶段都必须产出回执
```

Include an explicit cleanup section that says all devices must be shut down and the topology removed after the run.

- [ ] **Step 4: Verify the runbook encodes the mandatory order and cleanup rule**

Run:

```bash
rg -n "采集不过，不进入监控|监控不过，不进入拓扑|关闭设备并清理拓扑|controller \\+ agent" docs/testing/phase1-network-mainline-execution-runbook.md
```

Expected: one match for each gate and cleanup requirement.

- [ ] **Step 5: Commit the runbook**

```bash
git -C docs add testing/phase1-network-mainline-execution-runbook.md
git -C docs commit -m "docs: add phase1 network mainline execution runbook"
```

### Task 3: Create the first collection baseline receipt

**Files:**
- Create: `docs/testing/phase1-network-mainline-collection-receipt-v1.md`

- [ ] **Step 1: Verify the collection receipt file is absent before creation**

```bash
test ! -f docs/testing/phase1-network-mainline-collection-receipt-v1.md
```

Expected: exit `0`.

- [ ] **Step 2: Re-read the existing collection and A1 evidence docs so the receipt inherits their language**

Run:

```bash
rg -n "身份信息|接口|邻居|路由|边界|A1|最小监控任务" docs/testing/phase1-a1-single-device-baseline-receipt-v1.md docs/testing/phase1-a1-per-device-standard-receipts.md docs/testing/phase1-a1-minimal-monitoring-task-evidence.md docs/testing/phase1-real-device-test-matrix.md
```

Expected: matches for identity, interface, neighbor, route, and explicit boundary wording.

- [ ] **Step 3: Write the collection receipt template with device-by-device facts**

Create `docs/testing/phase1-network-mainline-collection-receipt-v1.md` with sections like:

```markdown
# 第一阶段网络设备主线采集回执 V1

## 1. 场景定义

1. 拓扑版本
2. 设备清单
3. 地址版本
4. 端口分配版本

## 2. 逐设备采集结果

| 设备 | 管理可达 | 身份信息 | 接口 | 邻居 | 路由 | 当前结论 |
| --- | --- | --- | --- | --- | --- | --- |
| ACC1 | 未验证 | 未验证 | 未验证 | 不适用 | 未验证 | 未执行 |
| R1 | 未验证 | 未验证 | 未验证 | 未验证 | 未验证 | 未执行 |
```

Add a final section named `薄弱点分析` that splits findings into:

1. 设备适配问题
2. 数据建模问题
3. 任务执行问题
4. 明确支持边界

- [ ] **Step 4: Verify the receipt includes all required fact classes**

Run:

```bash
rg -n "身份信息|接口|邻居|路由|薄弱点分析|明确支持边界" docs/testing/phase1-network-mainline-collection-receipt-v1.md
```

Expected: one or more matches for each required collection fact class and the weak-point section.

- [ ] **Step 5: Commit the collection receipt template**

```bash
git -C docs add testing/phase1-network-mainline-collection-receipt-v1.md
git -C docs commit -m "docs: add phase1 network mainline collection receipt"
```

### Task 4: Create the first monitoring and topology receipts plus the weak-point register

**Files:**
- Create: `docs/testing/phase1-network-mainline-monitoring-receipt-v1.md`
- Create: `docs/testing/phase1-network-mainline-topology-receipt-v1.md`
- Create: `docs/testing/phase1-network-mainline-weak-point-register.md`

- [ ] **Step 1: Verify the three files are absent before creation**

```bash
test ! -f docs/testing/phase1-network-mainline-monitoring-receipt-v1.md
test ! -f docs/testing/phase1-network-mainline-topology-receipt-v1.md
test ! -f docs/testing/phase1-network-mainline-weak-point-register.md
```

Expected: all commands exit `0`.

- [ ] **Step 2: Pull the existing monitoring evidence rule and topology expectations**

Run:

```bash
rg -n "平台计划层|平台任务层|Agent 运行层|目标结果层|漏边|重边|错边|管理平面" docs/testing/phase1-a1-minimal-monitoring-task-evidence.md docs/testing/eve-ng-first-scenario-bridge-boundary-pnet0-runbook.md docs/testing/phase1-real-device-test-matrix.md
```

Expected: matches for the four monitoring layers and topology-error vocabulary.

- [ ] **Step 3: Write the monitoring receipt, topology receipt, and weak-point register**

Create `docs/testing/phase1-network-mainline-monitoring-receipt-v1.md` with a four-layer table:

```markdown
| 任务对象 | 平台计划层 | 平台任务层 | Agent 运行层 | 目标结果层 | 当前结论 |
| --- | --- | --- | --- | --- | --- |
| R1 接口监控 | 未验证 | 未验证 | 未验证 | 未验证 | 未执行 |
```

Create `docs/testing/phase1-network-mainline-topology-receipt-v1.md` with checks for:

```markdown
1. 交换机与服务器接入关系是否正确
2. 路由器之间全互联关系是否正确
3. 管理平面是否被错误混入业务拓扑
4. 是否存在漏边、重边、错边
```

Create `docs/testing/phase1-network-mainline-weak-point-register.md` with a table like:

```markdown
| 编号 | 链路 | 问题类型 | 现象 | 影响 | 当前判断 | 下一步动作 |
| --- | --- | --- | --- | --- | --- | --- |
| W-001 | 采集链 | 设备适配 | 未记录 | 未评估 | 未分类 | 补录首条真实问题 |
```

- [ ] **Step 4: Verify all three docs contain the expected anchors**

Run:

```bash
rg -n "平台计划层|Agent 运行层|目标结果层|漏边|重边|错边|W-001|下一步动作" docs/testing/phase1-network-mainline-monitoring-receipt-v1.md docs/testing/phase1-network-mainline-topology-receipt-v1.md docs/testing/phase1-network-mainline-weak-point-register.md
```

Expected: matches for the monitoring evidence layers, topology error vocabulary, and weak-point tracking fields.

- [ ] **Step 5: Commit the receipts and register**

```bash
git -C docs add testing/phase1-network-mainline-monitoring-receipt-v1.md testing/phase1-network-mainline-topology-receipt-v1.md testing/phase1-network-mainline-weak-point-register.md
git -C docs commit -m "docs: add phase1 network mainline evidence receipts"
```

### Task 5: Wire the new mainline docs into the testing index and execution checklist

**Files:**
- Modify: `docs/testing/README.md`
- Modify: `docs/testing/phase1-first-batch-executable-checklist.md`

- [ ] **Step 1: Write the failing discoverability check**

Run:

```bash
! rg -n "phase1-network-mainline-standard-scenario|phase1-network-mainline-execution-runbook|phase1-network-mainline-collection-receipt-v1" docs/testing/README.md docs/testing/phase1-first-batch-executable-checklist.md
```

Expected: exit `0` because the new files should not be indexed yet.

- [ ] **Step 2: Open the relevant insertion points before editing**

Run:

```bash
sed -n '1,220p' docs/testing/README.md
sed -n '1,220p' docs/testing/phase1-first-batch-executable-checklist.md
```

Expected: visible sections where the new network-mainline docs can be inserted without renumbering errors or duplicated narrative.

- [ ] **Step 3: Update the index and checklist to surface the new mainline path**

Add entries to `docs/testing/README.md` similar to:

```markdown
37. [第一阶段网络设备主线标准场景](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-network-mainline-standard-scenario.md)
    把第一条 `4+2+1` 网络设备主线场景固定下来，作为后续采集、监控、拓扑联合验证的统一入口。
38. [第一阶段网络设备主线地址与端口分配](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-network-mainline-addressing-and-port-map.md)
    固定设备 ID、地址规划、业务网关与管理口/业务口角色分配，避免每轮重复设计。
39. [第一阶段网络设备主线执行手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-network-mainline-execution-runbook.md)
    规定建拓扑、采集、监控、拓扑、清理的执行顺序与退出原则。
```

Update `docs/testing/phase1-first-batch-executable-checklist.md` by adding a new `B3` section that explicitly says the next execution priority is the first network-mainline `4+2+1` scenario.

- [ ] **Step 4: Verify the docs are now discoverable**

Run:

```bash
rg -n "phase1-network-mainline-standard-scenario|phase1-network-mainline-execution-runbook|phase1-network-mainline-collection-receipt-v1|4\\+2\\+1" docs/testing/README.md docs/testing/phase1-first-batch-executable-checklist.md
```

Expected: matches in both the main testing index and the executable checklist.

- [ ] **Step 5: Commit the index updates**

```bash
git -C docs add testing/README.md testing/phase1-first-batch-executable-checklist.md
git -C docs commit -m "docs: index phase1 network mainline testing path"
```

## Self-Review Checklist

Before executing this plan, the implementing agent should confirm:

1. Every artifact in the approved design is represented by at least one task in this plan.
2. The first-wave scope stays on `collection -> monitoring -> topology`.
3. No task silently expands into policy-generation, firewall-chain, or large-scale performance work.
4. The new docs reference existing device-standard manuals instead of cloning vendor-specific content.
5. The new docs always distinguish management-plane facts from business-plane facts.

## Completion Standard

This plan should be considered complete when all of the following are true:

1. The first standard network-mainline scenario is documented and frozen.
2. The addressing and port-allocation map is documented and frozen.
3. The operator runbook exists with a strict execution order and cleanup rule.
4. Collection, monitoring, and topology all have their own first-wave receipt templates.
5. A weak-point register exists for findings from the mainline scenario.
6. The testing index and first-batch executable checklist both surface this new mainline path.
