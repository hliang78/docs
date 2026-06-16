# 2026-06-13 SNMP Dashboard Tree And Recording Publish Boundaries Design

## 1. Goal

This spec hardens two boundaries that have been discussed repeatedly but are still not defined tightly enough for implementation:

1. the tree structure and ownership model for SNMP Grafana dashboards;
2. the operational boundary of the SNMP recording-rule publish channel.

The immediate purpose is not to add more capabilities. The purpose is to remove ambiguity so that:

- strategy semantics, dashboard layout, and published dashboard instances stop being treated as one mixed tree;
- recording-rule publish can be judged correctly as an existing but narrow channel, not an abstract future platform;
- later implementation can proceed with stable ownership, conflict, and persistence rules.

## 2. Current Reality

The current codebase already contains most of the raw pieces, but their roles are still blurred.

Already present:

- strategy-set contract resolution and effective-contract aggregation;
- panel capability preview by target;
- recording-rule preview, materialization dry-run, and publish endpoint;
- Grafana dashboard template storage and by-target template resolution;
- Grafana dashboard materialization dry-run;
- Grafana dashboard save, target binding, panel binding, and snapshot persistence.

Relevant current code:

- strategy-set and dashboard binding models:
  - [teleabs_strategy_set.go](/OneOPS/OneOps/app/platform/platform_model/teleabs_strategy_set.go:11)
- Grafana template model:
  - [snmp_grafana_dashboard_template.go](/OneOPS/OneOps/app/platform/platform_model/snmp_grafana_dashboard_template.go:8)
- frontend/DTO contract types:
  - [snmp-metric-contract.ts](/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts:48)
  - [snmp-metric-contract.ts](/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts:425)
- recording-rule publish implementation:
  - [metric_capability_contract_resolver.go](/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go:4006)
  - [metric_capability_contract_resolver.go](/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go:4479)

The main problem is not missing code. The problem is that the code still leaves too much room for conflicting mental models.

## 3. Scope

This spec defines:

- the canonical tree model for dashboard-related SNMP delivery;
- the stable connection points between strategy semantics, recording rules, and dashboards;
- ownership and persistence rules for dashboard instances;
- the current recording-rule publish channel and what can or cannot be assumed about its stability;
- the minimum implementation order.

This spec does not define:

- a new DashboardFamily database table;
- a generic multi-backend recording-rule publish framework;
- manual Grafana editor round-trip;
- multi-parent dashboard template inheritance;
- automatic dashboard-variant recommendation logic.

## 4. Canonical Tree Model

The system must be understood as three trees, not one.

### 4.1 Strategy Tree

Purpose: determine what semantic monitoring capability a target device has.

Canonical structure:

```text
StrategySet
  -> matched item_contracts[]
    -> strategy / parent-strategy chain
      -> effective_contract
        -> metric_groups[]
          -> fields[]
          -> panel_specs[]
```

Important semantics:

- `StrategySet` is the selection root.
- multiple matched items may contribute to a single `effective_contract`.
- `effective_contract` is the only semantic result consumed downstream.
- `panel_spec` belongs to the strategy tree, not the dashboard tree.

### 4.2 Dashboard Template Tree

Purpose: determine how semantic slots should be arranged into a dashboard layout.

Canonical structure:

```text
dashboard_variant
  -> template root
    -> child template
      -> child template
        -> resolved template_chain
```

Important semantics:

- `dashboard_variant` is the root category that selects one dashboard product type, for example `snmp.switch.operations`.
- each template node is one patch layer, not a final dashboard.
- `parent_key` forms single inheritance.
- for one target and one variant, resolution must produce exactly one template chain or fail.

### 4.3 Dashboard Instance Tree

Purpose: determine what has actually been generated and published for a specific target.

Canonical structure:

```text
owner_key(strategy_set_id, target_part, dashboard_variant)
  -> current materialized dashboard
    -> panel_bindings[]
  -> snapshots[]
```

Important semantics:

- this is the publication tree, not the template tree;
- only one current instance is allowed per owner key;
- overwrite creates snapshots, not parallel current instances.

## 5. Canonical Node Definitions

### 5.1 StrategySet

Role:

- selection root for semantic capability;
- not a dashboard-layout node;
- not the identity of a published dashboard instance by itself.

### 5.2 EffectiveContract

Role:

- single semantic truth for the resolved target under one strategy set;
- source for recording-rule preview/materialization;
- source for panel capability support;
- source for dashboard binding inputs.

### 5.3 DashboardVariant

Role:

- dashboard product/type key;
- first-class input to dashboard materialization;
- current replacement for an explicit DashboardFamily entity.

Current policy:

- `DashboardFamily` is not yet a first-class stored entity;
- `family` is treated as a naming convention prefix inside the variant;
- for example:
  - `snmp.switch.operations`
  - `snmp.switch.capacity`
  - `snmp.router.operations`

In this convention:

- family of `snmp.switch.operations` is `snmp.switch`;
- variant remains the full string `snmp.switch.operations`.

### 5.4 DashboardTemplate

Role:

- one layout patch node in a single-variant template tree;
- resolved only through target context and variant;
- never treated as a published dashboard instance.

### 5.5 PanelSpec

Role:

- strategy-tree slot definition;
- a semantic panel capability contract;
- not a Grafana panel object.

`panel_spec` must not be interpreted as:

- a dashboard layout node;
- a persisted panel instance;
- a direct Grafana JSON block.

### 5.6 PanelBinding

Role:

- final traceability record showing how one materialized dashboard panel was bound;
- stores the resolved `panel_key`, selected capabilities, metric keys, and record names;
- belongs to the instance tree.

### 5.7 Snapshot

Role:

- point-in-time archive of the previous published dashboard content before overwrite;
- belongs to the instance tree;
- not part of current resolution logic.

## 6. Connection Rules Between Trees

The stable primary connection key is `panel_key`.

Canonical binding path:

```text
template panel slot
  -> panel_key
  -> match effective_contract.panel_specs by panel_key
  -> expand to metric_keys / dimensions / capability_keys / record_names
  -> generate panel_binding
```

This implies the following rules:

1. dashboard templates consume `panel_key`, not raw metrics directly;
2. dashboard materialization reads from `effective_contract`, not individual strategy rows;
3. `panel_spec` remains the contract-layer slot definition;
4. `panel_binding` remains the instance-layer resolved result.

Forbidden patterns:

- template node directly references vendor-specific raw field names;
- template node directly references a specific strategy item;
- dashboard materialization bypasses `panel_key` and binds straight to arbitrary metric keys.

## 7. Dashboard Variant And Family Policy

For this implementation phase, `dashboard_variant` is first-class and `family` is derived.

Reason:

- current models already persist `dashboard_variant`;
- no current model persists `family` as a separate normalized entity;
- introducing a fourth logical tree now would increase scope without resolving the current ambiguity.

Policy:

- callers must treat `dashboard_variant` as required input for materialization/save;
- UI may present family-like grouping later by prefix;
- backend resolution and persistence are variant-scoped, not family-scoped.

## 8. Dashboard Instance Ownership

Canonical owner key:

```text
(strategy_set_id, target_part, dashboard_variant)
```

This owner key must define the current materialized dashboard instance.

Implications:

- `dashboard_code` is a publication result, not the root owner identity;
- `root_dashboard_code` is not the stable ownership concept for future implementation;
- overwrite operations must target the canonical owner key.

Required runtime rule:

- one owner key may have only one current dashboard instance.

## 9. Dashboard Resolution Algorithm

The algorithm must be fixed in this order:

1. resolve target context from `target_part`;
2. resolve strategy-set semantic matches;
3. build `effective_contract`;
4. resolve panel capability support;
5. resolve recording-rule preview/materialization inputs;
6. resolve dashboard template chain from `target + dashboard_variant`;
7. bind template slots to contract `panel_specs` through `panel_key`;
8. materialize dashboard JSON and panel bindings;
9. save instance, bindings, and snapshot if requested.

The algorithm must not:

- resolve dashboard layout before semantic contract resolution;
- infer template chain from individual metric groups alone;
- save a dashboard instance before successful binding resolution.

## 10. Dashboard Conflict Matrix

### 10.1 Template Resolution Conflict

Condition:

- one `target + dashboard_variant` matches multiple sibling template candidates without a deterministic winner.

Behavior:

- fail resolution;
- do not silently pick one.

### 10.2 Template Chain Panel-Key Conflict

Condition:

- the resolved chain produces duplicate panel slots for the same `panel_key`.

Behavior:

- fail materialization;
- this is a template design error.

### 10.3 Binding Ambiguity

Condition:

- a template slot cannot bind unambiguously to a single semantic slot.

Behavior:

- zero matches: mark as skipped/unsupported;
- multiple equivalent matches: fail unless a deterministic rule is explicitly added later.

### 10.4 Current Instance Conflict

Condition:

- save operation would create multiple current dashboard instances for the same owner key.

Behavior:

- replace current instance;
- snapshot previous content first when content differs.

### 10.5 No-Op Content Update

Condition:

- new dashboard content SHA matches current content SHA.

Behavior:

- allowed as no-op save/update;
- may skip unnecessary overwrite side effects.

## 11. Dashboard Persistence Rules

Save behavior must be treated as instance replacement, not append-only creation.

Required save-side actions:

1. save or update the current platform dashboard object;
2. save target binding for the owner key;
3. save current panel bindings;
4. save previous snapshot if content changes.

Current code is close to this already, but still partially keyed by `dashboard_code` and by `strategy_set_id + target_part` without variant in all replacement logic, for example:

- target binding replacement:
  - [metric_capability_contract_resolver.go](/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go:4760)
- panel binding replacement:
  - [metric_capability_contract_resolver.go](/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go:4788)

Implementation target:

- replacement and uniqueness must become variant-aware end to end.

## 12. Recording Rule Publish Channel: Current Status

The recording-rule path already has a real publication channel.

Existing current channel:

- by-target preview;
- materialization dry-run;
- publish endpoint;
- publish record persistence.

Relevant code:

- publish endpoint:
  - [teleabs.go](/OneOPS/OneOps/app/platform/api/teleabs.go:429)
- publish implementation:
  - [metric_capability_contract_resolver.go](/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go:4479)
- publish record model:
  - [snmp_recording_rule_publish_record.go](/OneOPS/OneOps/app/platform/platform_model/snmp_recording_rule_publish_record.go:9)

The current backend is not abstractly “publish anywhere”. It is concretely:

```text
vmalert_file
  -> read existing rule file
  -> replace configured managed group
  -> write file
  -> call reload URL
  -> persist publish record
```

That means the current path is a real but narrow channel.

## 13. Recording Rule Publish Stability Assessment

### 13.1 What Is Already Stable Enough To Count As Real

- there is an explicit API route;
- publish is not just a dry-run;
- a configured managed group isolates generated rules from unmanaged groups;
- reload is explicit and not skipped silently;
- publish records are persisted;
- tests cover publish behavior and failure cases.

Relevant test:

- [metric_capability_contract_resolver_test.go](/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go:4707)

### 13.2 What Is Not Yet Strong Enough To Treat As A General Stable Platform

1. only one backend is supported:
   - `vmalert_file`
2. owner boundary is still group-based, not strategy-set ownership aware;
3. reload failure is explicit but not rollback-safe;
4. current write path is not truly atomic rename-based replacement.

The last point is especially important:

- the design document described temp-file plus rename;
- the current implementation still truncates and rewrites the target file directly.

Current implementation:

- [writeRecordingRuleFileAtomically](/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go:4079)

So the function name says “atomically”, but the current write path is not yet a true atomic replace.

## 14. Recording Rule Publish Conflict Policy

This spec does not require the full future generic conflict platform, but it does require the following minimum policy:

### 14.1 Same Record Name, Same Expression

Policy:

- may be treated as deduplicable/equivalent.

### 14.2 Same Record Name, Different Expression

Policy:

- hard conflict;
- must fail publish or pre-publish validation.

### 14.3 Different Record Name, Same Expression

Policy:

- allowed for now;
- may be optimized later but does not block publish by itself.

### 14.4 Generated Rules Versus Unmanaged Rules

Policy:

- unmanaged groups remain intact;
- only the configured managed group is replaced.

This is already aligned with the current merge design:

- remove existing managed group from YAML;
- append regenerated managed group;
- keep unmanaged groups intact.

## 15. Minimum Required Hardening Before Calling Recording Publish “Stable”

Priority 1:

1. replace truncate-write with true temp-file plus rename behavior;
2. define clear owner semantics for generated rule content, not just group-name replacement;
3. formalize same-record conflict handling;
4. preserve explicit failed-reload state as a documented operational outcome.

Priority 2:

1. add stronger engine validation such as `promtool` or equivalent;
2. support additional publish backends;
3. design rollback path for post-write reload failure;
4. support stronger multi-node distribution semantics.

## 16. Minimum Implementation Slice For Dashboard Work

The first safe implementation slice for Grafana must be:

1. require explicit `dashboard_variant` on materialize/save;
2. make owner key variant-aware;
3. guarantee single resolved template chain;
4. enforce `panel_key` as the only semantic slot binding key;
5. make save/replace/snapshot semantics variant-aware.

This is intentionally smaller than “full dashboard platform”.

## 17. Recommended Rollout Order

Recommended order:

1. harden backend dashboard identity and owner key;
2. harden template resolution to single-chain deterministic behavior;
3. harden panel-binding persistence around owner key and variant;
4. harden recording-rule write behavior and conflict policy;
5. expose frontend dry-run/save flow after backend boundaries are stable.

This order avoids building frontend workflow on top of unstable ownership semantics.

## 18. Explicit Non-Goals For This Round

Not part of this round:

- new normalized DashboardFamily DB entity;
- family-based recommendation engine;
- manual dashboard editing round-trip into templates;
- generic plugin framework for all recording-rule backends;
- multi-parent dashboard template inheritance;
- cross-strategy-set sharing of one current dashboard instance.

## 19. Final Decision Summary

For this implementation round, the system must be treated as:

```text
StrategySet
  -> effective_contract
  -> panel_specs

dashboard_variant
  -> template_chain

(strategy_set_id, target_part, dashboard_variant)
  -> current materialized dashboard
  -> panel_bindings
  -> snapshots
```

And the recording-rule channel must be treated as:

```text
real publish channel
  but narrow and file-backend-specific
```

In short:

- `StrategySet` owns semantics;
- `template_chain` owns layout;
- instance owner key owns published dashboard state;
- recording-rule publish already exists, but still needs boundary hardening before it should be treated as a broadly stable platform capability.
