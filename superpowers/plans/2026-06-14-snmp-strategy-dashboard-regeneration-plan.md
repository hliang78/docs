# 2026-06-14 SNMP Strategy Dashboard Regeneration Plan

## 1. Goal

Execute the dashboard recovery work in the correct order:

```text
effective strategy metrics
  -> strategy dashboard derivation
  -> CE168 reference decomposition
  -> regenerated dashboard tree
```

This plan explicitly forbids starting with direct CE168 copying.

## 2. Non-Goals

This batch does not:

- copy CE168 as the shared mother template;
- keep hard-coded interface panels such as `100GE5/0`;
- reintroduce flat class-level dashboard generation as the business center;
- make runtime data presence decide dashboard existence.

## 3. Inputs

Authoritative inputs for this batch:

- strategy selection result
- effective strategy contracts
- strategy tree / suite root mapping
- CE168 reference dashboard as sample only

Relevant current assets:

- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-suite-strategy-dashboard-tree-design.md`
- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-strategy-effective-metrics-dashboard-derivation-design.md`
- `/OneOPS/docs/superpowers/specs/2026-06-12-ce168-entity-semantic-cpu-memory-design.md`
- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricContract.ts`
- `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`

## 4. Deliverables

This batch should produce four concrete deliverables.

### Deliverable A

Per-strategy effective metric inventory.

### Deliverable B

Per-strategy dashboard derivation table.

### Deliverable C

CE168 panel decomposition table:

- reusable concept
- regenerate
- overlay-only sample
- forbidden hard-coded sample

### Deliverable D

Regenerated SNMP strategy dashboards:

- one suite root
- one strategy dashboard per strategy node
- node-local metric responsibility

## 5. Execution Order

### Step 1: Extract Effective Metrics Per Strategy

For each current SNMP strategy row in scope:

- resolve parent contract
- resolve child contract
- compute `effective_contract`
- flatten:
  - `metric_groups`
  - `fields`
  - `capability_keys`
  - `panel_specs`

Expected output:

```text
strategy
  -> effective metric groups
  -> effective capabilities
  -> effective panel specs
```

This step must complete before any dashboard regeneration.

### Step 2: Classify Dashboard Role Per Strategy

For each strategy, classify:

- switch common
- switch hardware overlay
- switch routing overlay
- firewall
- vendor-specific overlay
- generic SNMP fallback

Expected output:

- node role
- mandatory panel families
- optional overlay families

### Step 3: Decompose CE168 Reference

Take the CE168 sample dashboard and classify each panel into:

- reusable concept
- regenerate from current strategy metrics
- overlay-only reference
- forbidden hard-coded carryover

Examples that must be marked forbidden:

- `100GE5/0`
- `100GE6/0`
- `40GE7/0`
- `10GE8/0`

Examples that must be marked regenerate:

- `Huawei VRP Control Plane CPU`
- `Interface Utilization Top 10`
- `Traffic Throughput`
- `Packets Per Second`
- `Temperature Sensors`
- `Top 4 by Rx Power`

### Step 4: Define Strategy Dashboard Spec Per Strategy

For each strategy, produce a concrete node spec:

- dashboard node key
- node role
- metric groups
- panel families
- metric scope summary
- overlay dependencies

This is the first place where actual dashboard node content is allowed to become concrete.

### Step 5: Regenerate Dashboard Tree

Regenerate:

- one root dashboard
- one strategy dashboard per current SNMP strategy
- parent/child relationships matching the strategy tree

Important rule:

- root dashboard keeps suite-level summary
- strategy dashboards own their explicit metric-display responsibility
- no target-specific hard-coded panel identity is allowed into the logical tree

### Step 6: Apply UI And Seed Updates

After regenerated strategy dashboards exist:

- update quick env seeds
- update shared/reference rules
- keep CE168 visible as reference
- update tree-first visibility checks to validate regenerated strategy dashboards instead of CE168 parity

## 6. Current Strategy Scope

The first execution scope should include the SNMP rows currently visible in the strategy list:

- `H3C通用SNMP网络监控策略`
- `Huawei通用SNMP网络监控策略`
- `SNMP网络监控策略 (副本)`
- `Cisco generic SNMP network monitoring strategy`
- `思科网络设备监控 (副本)`
- `锐捷网络设备监控 (副本)`
- `H3C SecPath 防火墙 SNMP监控策略`
- `迈普通用SNMP网络监控策略`
- `烽火通用SNMP网络监控策略`

The first batch may still prioritize switch-oriented strategies before firewall/fallback refinement,
but all of these rows must have an explicit dashboard derivation result.

## 7. Verification

This batch is only complete when all of the following are true:

1. every in-scope SNMP strategy has an explicit effective-metric inventory;
2. every in-scope SNMP strategy has a strategy dashboard derivation result;
3. CE168 is decomposed and no forbidden hard-coded panel is still reused in shared generation;
4. strategy dashboard generation no longer depends on copying CE168 titles/ports directly;
5. suite root and strategy dashboard tree remain the primary business model.

## 8. Immediate Next Coding Batch

The first coding batch after this plan should do exactly this:

1. add/export an effective-metric inventory view per strategy;
2. add a machine-readable dashboard-derivation table per strategy;
3. encode CE168 decomposition rules into tests/fixtures;
4. only then start regenerating dashboard node definitions.
