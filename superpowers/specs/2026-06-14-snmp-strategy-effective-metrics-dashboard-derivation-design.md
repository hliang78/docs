# 2026-06-14 SNMP Strategy Effective Metrics To Dashboard Derivation Design

## 1. Goal

This spec defines the correct way to turn SNMP strategies into dashboards after the earlier
`suite root + strategy dashboard tree` direction has been fixed.

The key correction is:

```text
strategy dashboard
!= copied device sample dashboard
```

The intended derivation is:

```text
matched strategy tree
  -> effective metric responsibility per strategy node
  -> dashboard tree
  -> node-local panel families
  -> layout / profile overlays
```

not:

```text
CE168 sample dashboard
  -> remove a few device strings
  -> shared switch dashboard
```

## 2. Problem Statement

The current line has two different assets mixed together:

1. a **semantic strategy model**
2. a **high-quality device sample dashboard**

The semantic model is correct input for dashboard generation.
The device sample is only a useful reference.

The current danger is:

- CE168 quality is attractive enough that it is easy to treat it as the canonical mother template;
- but CE168 contains device-specific layout and port-level assumptions;
- once those assumptions are frozen into the shared path, the business model drifts away from
  `suite root + strategy dashboard tree`.

This spec prevents that drift.

## 3. Scope

This spec defines:

- how to compute the final metric responsibility of each strategy;
- how strategy dashboards should be derived from those effective metrics;
- how CE168 should be decomposed into reusable concepts versus non-reusable hard-coded sample content;
- what kinds of dashboards should exist for the current SNMP strategy list.

This spec does not define:

- final Grafana JSON for every strategy;
- final DB migrations;
- final frontend tree navigation details;
- exact visual polish rules.

## 4. Core Rule

The first-class derivation must be:

```text
strategy selection
  -> effective strategy metrics
  -> strategy dashboard selection
```

The second-class reference is:

```text
CE168 sample
  -> panel/layout inspiration only
```

Important rule:

- CE168 can influence **how** a strategy dashboard is rendered.
- CE168 must not define **what** a strategy dashboard semantically is.

## 5. Effective Metrics Are The Only Valid Input

For each strategy node, the dashboard derivation must start from the final effective metric contract,
not from raw sample dashboards and not from only the local child diff.

### 5.1 Existing Effective-Contract Rule

The current SNMP contract model already has the right conceptual primitive:

```text
parent_contract + child_contract
  -> effective_contract
```

Frontend helper:

- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricContract.ts`
- `resolveEffectiveSnmpContract(...)`

Backend response shape:

- `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
- `effective_contract`
- `item_contracts`

This must become the starting point for strategy dashboards.

### 5.2 Effective Metric Extraction

For one strategy node, the derivation input should be:

```text
effective_contract.metric_groups[]
  -> fields[]
  -> panel_specs[]
  -> capability_keys
  -> concept_keys
```

That means each strategy dashboard should be computed from:

1. **effective metric groups**
2. **effective field capabilities**
3. **effective panel specs**
4. **effective concept coverage**

### 5.3 What “Final Metrics” Means

For the current closure work, “final metrics” means:

- inherited metric groups from parent strategy;
- child-local added groups;
- child-local overridden groups;
- child-local disabled groups removed from display responsibility;
- resulting panel specs after inheritance and override are applied.

Important rule:

- do not derive dashboards from raw `passthrough_config` directly;
- do not derive dashboards from local child parameters only;
- always derive from the effective strategy-level semantic contract.

## 6. Every Strategy Needs Its Own Dashboard

For the current strategy list, each concrete SNMP strategy row should map to one strategy dashboard node.

Examples from the current environment include:

- `H3C通用SNMP网络监控策略`
- `Huawei通用SNMP网络监控策略`
- `SNMP网络监控策略 (副本)`
- `Cisco generic SNMP network monitoring strategy`
- `思科网络设备监控 (副本)`
- `锐捷网络设备监控 (副本)`
- `H3C SecPath 防火墙 SNMP监控策略`
- `迈普通用SNMP网络监控策略`
- `烽火通用SNMP网络监控策略`

Important rule:

- these are not all one flat switch dashboard;
- these are different strategy dashboard nodes under one suite-root family;
- target binding chooses which strategy node tree a target sees through the matched strategy selection.

## 7. Strategy Dashboard Derivation Layers

Each strategy dashboard should be derived in four layers.

### 7.1 Layer A: Semantic Metric Responsibility

The strategy dashboard must first answer:

- which metric groups does this strategy own?
- which concept families does it cover?
- which panel families are mandatory?
- which panels are summary versus detail?

This layer is semantic and comes entirely from the effective contract.

### 7.2 Layer B: Dashboard Node Role

Each strategy dashboard node must then be classified into a role such as:

- `root-summary`
- `system`
- `interface`
- `hardware`
- `topology`
- `routing`
- `platform-evidence`

This role should come from effective metric groups and panel families,
not from CE168 screen position.

### 7.3 Layer C: Profile Overlay

After semantic role is known, platform/model profile overlays can refine:

- titles
- optional hardware sections
- routing additions
- vendor/platform naming
- visibility of hardware-rich detail panels

Examples:

- `Huawei VRP`
- `Cisco Nexus`
- `H3C Comware`
- `Ruijie`
- `Firewall`

Important rule:

- profile overlay is allowed to refine a strategy dashboard;
- profile overlay must not replace the strategy dashboard identity.

### 7.4 Layer D: Visual/Layout Reference

Only after Layers A/B/C are fixed should the system reuse dashboard sample ideas.

This is where CE168 belongs:

- layout inspiration
- section density
- panel title style
- hotspot ranking patterns
- hardware summary patterns

## 8. CE168 Must Be Decomposed, Not Copied

CE168 should be treated as:

```text
switch sample
= common switch concepts
+ Huawei/chassis/optical overlays
+ device-specific hard-coded samples
```

### 8.1 Reusable Concepts From CE168

These are reusable as concepts, but not necessarily with the same literal title/query/layout:

- device identity
- overall health
- active alerts
- CPU summary
- memory summary
- interface utilization hotspot ranking
- traffic throughput trend
- packet-rate trend
- layer-2 / switching summary
- hardware health summaries

### 8.2 Reusable But Must Be Regenerated

These can inspire strategy dashboards, but must be regenerated from effective metrics and profile rules:

- `Huawei VRP Control Plane CPU`
- `Huawei VRP Control Plane Memory`
- `Interface Utilization Top 10`
- `Traffic Throughput`
- `Packets Per Second`
- `Temperature Sensors`
- `Fans`
- `Power Supplies`
- `Top 4 by Rx Power`
- `Last 4 by Rx Power`

Important rule:

- keep the semantic intent;
- regenerate title, query, dimensions, and node placement from strategy responsibility and profile capability.

### 8.3 Forbidden To Reuse Directly

These must never be copied into the shared derivation path:

- `100GE5/0`
- `100GE6/0`
- `40GE7/0`
- `10GE8/0`
- any port-specific hard-coded interface tiles
- any panel whose identity depends on one exact CE168 port naming scheme

Important rule:

- interface-level panels must always be generated from current effective interface metrics;
- interface names must come from current target/runtime series labels, not from a device sample title list.

## 9. Strategy-Tree To Dashboard-Tree Mapping

The dashboard tree should follow the strategy tree at the business level.

Canonical mapping:

```text
Monitoring Suite
  -> Root Dashboard
    -> Strategy Dashboard
      -> child Strategy Dashboard
```

Within one strategy dashboard node, panel families should still be grouped by semantic sections:

```text
Strategy Dashboard
  -> summary section
  -> interface section
  -> system section
  -> hardware section
  -> topology section
  -> routing section
```

Important rule:

- tree identity comes from strategies;
- panel sections come from effective metric roles;
- layout comes last.

## 10. First-Cut Strategy Families For The Current SNMP Set

For the current screenshot-driven strategy list, the first-cut dashboard intent should look like this.

### 10.1 Generic Network Switch Strategies

Examples:

- `H3C通用SNMP网络监控策略`
- `Huawei通用SNMP网络监控策略`
- `Cisco generic SNMP network monitoring strategy`
- `锐捷网络设备监控 (副本)`
- `迈普通用SNMP网络监控策略`
- `烽火通用SNMP网络监控策略`

Expected dashboard shape:

- one switch strategy dashboard each;
- common sections:
  - identity / health / alerts
  - CPU / memory
  - interface hotspot
  - traffic
  - switching / topology summary
- optional overlays:
  - hardware
  - optical
  - routing

### 10.2 Firewall Strategy

Example:

- `H3C SecPath 防火墙 SNMP监控策略`

Expected dashboard shape:

- separate firewall strategy dashboard;
- must not inherit switch interface-heavy layout blindly;
- root summary may still be shared, but node-local dashboard should bias toward:
  - system
  - sessions / throughput if available later
  - interface summary only where semantically justified.

### 10.3 “副本” Strategies

Examples:

- `SNMP网络监控策略 (副本)`
- `思科网络设备监控 (副本)`
- vendor-specific or model-specific copy strategies

Expected rule:

- if effective metrics are semantically equal, they may reuse the same layout/profile recipe;
- but they still remain distinct strategy dashboard nodes in the tree;
- if the effective metrics differ, they must not be flattened into one dashboard node.

## 11. What Must Be Implemented Next

The next implementation batch should not start by editing Grafana panel coordinates.

It should start with three deterministic outputs.

### 11.1 Output A: Effective Metrics Inventory Per Strategy

For each current SNMP strategy:

- strategy id / name
- parent strategy
- effective metric groups
- effective capability keys
- effective panel specs

### 11.2 Output B: Dashboard Derivation Table

For each strategy:

- dashboard node role
- mandatory panel families
- optional overlay families
- forbidden hard-coded CE168 carryovers

### 11.3 Output C: CE168 Reference Decomposition Table

For each CE168 panel:

- reusable concept
- regenerate from effective metrics
- keep only as profile overlay sample
- forbidden hard-coded sample

## 12. Frozen Rules

Freeze these rules for follow-up work:

1. dashboard derivation starts from `effective_contract`, not from sample dashboards.
2. every strategy row needs its own strategy dashboard node.
3. CE168 is a reference sample, not the canonical mother template.
4. hard-coded interface-specific CE168 panels must not enter shared generation.
5. vendor/platform/model overlays may refine layout, but must not replace strategy-node identity.
6. dashboard tree identity follows strategy tree identity.
