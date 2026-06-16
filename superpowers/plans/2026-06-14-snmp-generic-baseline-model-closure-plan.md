# SNMP Generic Baseline Model Closure Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the next SNMP definition-layer gap by turning the current switch-only baseline path into one generic SNMP target-class baseline model, so every SNMP dashboard generation path goes through the same `TargetClass -> ClassBaseline -> VariantBaseline -> Owner -> Generation` contract.

**Architecture:** Keep the current switch and routing-capable switch behavior intact, but lift them into a generic SNMP class module. Introduce one generic SNMP baseline model that owns target-class selection, baseline selection, variant selection, owner rules, and baseline-aware template resolution. The existing switch-specific boundaries become implementations under that generic model rather than the model itself.

**Tech Stack:** Go backend in `/OneOPS/OneOps`, current SNMP/Grafana resolver/generator/service/persistence flow, focused service/API tests, docs in `/OneOPS/docs/superpowers`.

---

## Scope Lock

This is one long-task closure batch. It must finish the generic model, not add one more switch-only helper.

Allowed in this batch:

- introduce a generic SNMP target-class model;
- formalize `TargetClass`, `ClassBaseline`, `VariantBaseline`, `PanelFamily`, `PanelOwner`;
- keep current switch classes as explicit instances of the generic model;
- add one generic SNMP fallback baseline so non-switch SNMP targets are no longer forced into switch assumptions;
- move current owner/baseline/template selection behind the generic module;
- make flat dry-run, flat save, tree dry-run, tree save, and history replay consume the same generic model;
- update docs/handoff to declare the generic closure complete.

Not allowed in this batch:

- no runtime `has_data / no_data / not_exposed` redesign;
- no per-device dashboard branching;
- no new UI work;
- no attempt to fully model every future SNMP class family in one pass;
- no reopening current switch owner rules unless required by the generic model.

## Closure Target

After this batch, SNMP dashboard generation should be explainable as:

```text
SNMP target
  -> TargetClass
    -> ClassBaseline
      -> VariantBaseline
        -> PanelFamily set
          -> PanelOwner rules
            -> dashboard generation
```

And this must be true for:

- current switch targets;
- routing-capable switch targets;
- non-switch SNMP targets through an explicit generic SNMP baseline.

The key closure condition is:

- no SNMP dashboard generation path silently assumes “switch” as the only class;
- no caller assembles baseline/owner/template rules outside the generic module;
- runtime state does not gate baseline existence.

## File Structure

Backend expected to change:

- Create: `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_target_class_module.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_baseline_module.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_generator.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_service.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_persistence_service.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go`

Docs expected to change:

- Modify: `/OneOPS/docs/superpowers/plans/2026-06-14-snmp-definition-runtime-closure-correction.md`
- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`
- Modify: `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-definition-closure-summary.md`

Reference docs to keep open:

- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-class-baseline-generation-rule.md`
- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-routing-capable-switch-baseline.md`
- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-switch-baseline-selection-rule.md`
- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-routing-responsibility-mapping-table.md`
- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-current-panel-family-owner-decision-table.md`

## Canonical Decisions

These decisions are fixed for this batch:

- generation decides what families exist;
- runtime only decides panel state;
- current switch classes remain:
  - `switch.current`
  - `switch.routing_capable`
- add one generic baseline:
  - `snmp.generic`
- `snmp.generic` is a real class baseline, not an error bucket;
- current switch and routing-capable switch baselines become additive specializations over the generic SNMP baseline;
- routing responsibility stays narrow:
  - `l3_route_table.*`
  - `routing_bgp.*`
  - `routing_ospf.*`
- owner rules remain definition-layer rules, not runtime heuristics.

## Task 1: Freeze The Generic SNMP Class Contract With Failing Tests

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Add a failing test for generic SNMP class selection**

Add a test that resolves a non-switch SNMP target and expects:

- `TargetClass = snmp.generic`
- `ClassBaseline = snmp.generic`
- `VariantBaseline = snmp.generic.operations`

- [ ] **Step 2: Add a failing test for switch current class under the generic module**

Add a test that resolves the current Huawei S5735 switch path and expects:

- `TargetClass = switch`
- `ClassBaseline = switch.current`

- [ ] **Step 3: Add a failing test for routing-capable switch class under the generic module**

Add a test that resolves a routing-responsible strategy set and expects:

- `TargetClass = switch`
- `ClassBaseline = switch.routing_capable`

- [ ] **Step 4: Add a failing test for generic baseline history derivation**

Add a test that derives history baseline from strategy IDs and confirms:

- it stays baseline-only;
- it returns `snmp.generic` when strategy responsibility is not switch-scoped.

- [ ] **Step 5: Run focused tests to verify RED**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestSnmpGrafanaTargetClassModuleResolves(Generic|SwitchCurrent|SwitchRoutingCapable|BaselineForStrategyIDs)' -count=1
```

Expected: FAIL because the generic module does not exist yet.

## Task 2: Introduce The Generic SNMP Target-Class Module

**Files:**
- Create: `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_target_class_module.go`

- [ ] **Step 1: Add the generic class and baseline types**

Define short internal types:

- `snmpGrafanaTargetClass`
- `snmpGrafanaClassBaseline`
- `snmpGrafanaVariantBaseline`
- `snmpGrafanaTargetClassGeneration`

Required class constants:

- `snmp.generic`
- `switch`

Required baseline constants:

- `snmp.generic`
- `switch.current`
- `switch.routing_capable`

- [ ] **Step 2: Add one generic module entry**

Create:

- `newSnmpGrafanaTargetClassModule(...)`
- `resolve(...)`
- `resolveForStrategyIDs(...)`

Required result fields:

- `TargetClass`
- `ClassBaseline`
- `VariantBaseline`
- `Baseline`
- `Template`

- [ ] **Step 3: Add generic class selection**

The selector must use:

- target profile
- matched strategy responsibility

It must not use:

- runtime data presence
- push status
- current panel values

Rule:

- non-switch SNMP target -> `snmp.generic`
- switch target without routing responsibility -> `switch.current`
- switch target with routing responsibility -> `switch.routing_capable`

- [ ] **Step 4: Run focused tests to verify GREEN**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestSnmpGrafanaTargetClassModuleResolves(Generic|SwitchCurrent|SwitchRoutingCapable|BaselineForStrategyIDs)' -count=1
```

Expected: PASS

## Task 3: Turn Generic SNMP Baseline Into The Common Generation Floor

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_baseline_module.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Define the generic SNMP baseline**

Make `snmp.generic` own the minimum common SNMP families:

- `device.identity`
- `platform_config.*`
- `platform_alerts.*`
- `platform_events.*`

This baseline must be valid even when no switch-specific family exists.

- [ ] **Step 2: Make switch current baseline inherit from generic SNMP**

Keep current switch behavior unchanged, but express it as:

```text
snmp.generic
  + switch.current additions
```

- [ ] **Step 3: Make routing-capable switch baseline inherit from switch current**

Keep the current routing-capable delta:

- `l3_route_table.ipv4_count`
- `l3_route_table.ipv6_count`
- `routing_bgp.neighbor_total`
- `routing_bgp.established_total`
- `routing_ospf.neighbor_total`
- `routing_ospf.full_total`

But express it as:

```text
snmp.generic
  + switch.current
  + switch.routing_capable delta
```

- [ ] **Step 4: Add tests for generic baseline definitions**

Add tests that assert:

- generic baseline contains common SNMP families;
- switch current baseline still contains current switch families;
- routing-capable baseline still adds the six routing families.

- [ ] **Step 5: Run focused tests**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestSnmpGrafana(TargetClassModuleResolves.*|PanelDefinitionsForTargetAndBaseline_.*|SwitchDashboardGeneratorResolvesDashboardGeneration_Current)' -count=1
```

Expected: PASS

## Task 4: Unify Owner Rules Under The Generic Model

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Move owner rule entry to the generic module boundary**

Ensure generation consumes one owner rule entry from the generic target-class model instead of switch-specific scattered assumptions.

- [ ] **Step 2: Keep current owner decisions intact**

Preserve:

- generic/root families -> `root`
- current switch detail families -> `strategy`
- routing-capable routing families -> `strategy`

- [ ] **Step 3: Add tests for generic owner floor**

Add tests that verify:

- generic SNMP baseline families do not drift into strategy ownership;
- switch families still do not drift into root fallback;
- routing families stay strategy-owned under routing-capable baseline.

- [ ] **Step 4: Run focused tests**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestSnmpGrafanaBindingOwner|TestMetricCapabilityContractResolverPlansDashboardTree.*|TestSnmpGrafanaTargetClassModuleResolves.*' -count=1
```

Expected: PASS

## Task 5: Rewire Generator, Service, Persistence, And History To The Generic Module

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_generator.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_service.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_persistence_service.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go`

- [ ] **Step 1: Make generator consume the generic module**

Generator input must become:

- target class
- class baseline
- variant baseline
- baseline-aware template

It must no longer directly assume switch-specific baseline resolution as the only path.

- [ ] **Step 2: Make service and persistence consume the same generic generation result**

Flat dry-run, flat save, tree dry-run, tree save must all use the same generic model result.

- [ ] **Step 3: Make history replay consume the same generic baseline derivation**

`save-summary/by-batch` and `save-batches` must continue returning one unified `Baseline`, but that derivation must now come from the generic module.

- [ ] **Step 4: Add API tests**

Verify:

- flat materialize returns the same `Baseline` shape;
- tree dry-run returns the same `Baseline` shape;
- tree save summary/history returns the same `Baseline` shape;
- current switch and routing-capable switch still behave the same.

- [ ] **Step 5: Run focused backend and API tests**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestSnmpGrafanaTargetClassModuleResolves.*|TestSnmpGrafanaSwitchDashboard(ServiceResolves(DryRun|TreeDryRun)_Current|PersistenceServiceSaves(Dashboard|Tree)_Current)|TestMetricCapabilityContractResolver(ResolvesSnmpGrafanaSwitchDashboardGeneration_(Current|RoutingCapable)|MaterializesStrategySetGrafanaDashboardTreeByTarget|SavesStrategySetGrafanaDashboardByTarget|SavesStrategySetGrafanaDashboardTreeByTarget|GetsStrategySetGrafanaDashboardTreeSaveSummaryByBatch|ListsStrategySetGrafanaDashboardTreeSaveBatches)' -count=1
go test ./app/platform/api -run 'TestTeleabsAPI_(MaterializeStrategySetGrafanaDashboardByTarget_HTTP|MaterializeStrategySetGrafanaDashboardTreeByTarget_HTTP|SaveStrategySetGrafanaDashboardTreeByTarget_HTTP|GetStrategySetGrafanaDashboardTreeSaveSummaryByBatch_HTTP|ListStrategySetGrafanaDashboardTreeSaveBatches_HTTP)' -count=1
```

Expected: PASS

## Task 6: Close The Docs Against The New Generic Model

**Files:**
- Modify: `/OneOPS/docs/superpowers/plans/2026-06-14-snmp-definition-runtime-closure-correction.md`
- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`
- Modify: `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-definition-closure-summary.md`

- [ ] **Step 1: Update correction plan**

Add that the next closure is no longer “switch-only baseline closure”, but “generic SNMP target-class baseline closure”.

- [ ] **Step 2: Update handoff**

Record that:

- current switch line is now one specialization under the generic SNMP model;
- future SNMP classes must enter through the same target-class/baseline contract;
- runtime must still not gate baseline existence.

- [ ] **Step 3: Update summary page**

The summary page must explicitly say:

- generic SNMP class baseline exists;
- switch current and routing-capable are additive class baselines under the generic model;
- the remaining future work is class expansion, not another model correction.

- [ ] **Step 4: Run docs verification**

Run:

```bash
git -C /OneOPS/docs diff --check
```

Expected: no output

## Task 7: Final Closure Verification

**Files:**
- No new files

- [ ] **Step 1: Run the full focused backend closure suite**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestSnmpGrafanaTargetClassModuleResolves.*|TestSnmpGrafanaBindingOwner|TestSnmpGrafanaSwitchDashboard(GeneratorResolvesDashboardGeneration_Current|ServiceResolves(DryRun|TreeDryRun)_Current|PersistenceServiceSaves(Dashboard|Tree)_Current)|TestMetricCapabilityContractResolver(ResolvesSnmpGrafanaSwitchDashboardGeneration_(Current|RoutingCapable)|MaterializesStrategySetGrafanaDashboardTreeByTarget|SavesStrategySetGrafanaDashboardByTarget|SavesStrategySetGrafanaDashboardTreeByTarget|GetsStrategySetGrafanaDashboardTreeSaveSummaryByBatch|ListsStrategySetGrafanaDashboardTreeSaveBatches)|TestSnmpGrafanaPanelDefinitionsForTargetAndBaseline_RoutingCapableAddsRoutingFamilies' -count=1
```

Expected: PASS

- [ ] **Step 2: Run the focused API suite**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/api -run 'TestTeleabsAPI_(MaterializeStrategySetGrafanaDashboardByTarget_HTTP|MaterializeStrategySetGrafanaDashboardTreeByTarget_HTTP|SaveStrategySetGrafanaDashboardTreeByTarget_HTTP|GetStrategySetGrafanaDashboardTreeSaveSummaryByBatch_HTTP|ListStrategySetGrafanaDashboardTreeSaveBatches_HTTP)' -count=1
```

Expected: PASS

- [ ] **Step 3: Run diff checks**

Run:

```bash
git -C /OneOPS/OneOps diff --check
git -C /OneOPS/docs diff --check
```

Expected: no output

## Completion Standard

This long task is complete only when all of the following are true:

- every SNMP dashboard generation path resolves through one generic SNMP target-class module;
- switch current and routing-capable baselines are explicit class-baseline specializations, not the generic model itself;
- non-switch SNMP targets resolve through an explicit `snmp.generic` baseline instead of silently falling into switch assumptions;
- owner rules remain definition-layer rules and do not regress to runtime gating;
- flat generation, tree generation, save, and history replay all expose the same baseline language through the generic module;
- docs and handoff describe the generic SNMP model as the new closed baseline-generation contract.

## Final Notes

Do not split this batch into another sequence of tiny switch-only fixes.

If new work appears during implementation, accept it only if it helps satisfy the generic SNMP model closure target above.
If it is only runtime polish, defer it.
