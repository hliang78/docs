# SNMP Switch Dashboard Bottom Extension Panels Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add three new bottom-row panels for `接口流量`、`接口丢包`、`接口广播` to `OneOPS SNMP Switch Ops` and all `OneOPS SNMP Switch Ops/*` dashboards without changing the existing 22-panel CE168-derived layout.

**Architecture:** Reuse the existing current-switch shared skeleton and append the new panels through the dedicated additional-panel hook so all shared root and strategy child dashboards inherit the same additive band. Reuse existing interface recording rules and panel rendering helpers so the feature expands dashboard capability without introducing a second metrics path.

**Tech Stack:** Go backend in `/OneOPS/OneOps`, Grafana dashboard materialization helpers in `metric_capability_contract_resolver.go`, package tests in `metric_capability_contract_resolver_test.go`, spec in `/OneOPS/docs/superpowers/specs`.

---

## File Map

- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
  - Append the three bottom-extension panel definitions to the current switch shared skeleton.
  - Add panel-expression, legend, and visual-contract support for the new panel keys.
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
  - Add regression tests for panel presence, grid positions, query wiring, and unchanged legacy panel positions.

## Task 1: Lock the additive layout with failing tests

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Write the failing test**

Add tests that assert:
- `snmpGrafanaSwitchCurrentPanelDefinitions()` includes `interface_basic.traffic_summary`, `interface_basic.discard_summary`, and `interface_basic.broadcast_summary`.
- Their grids are `(0,26,8,6)`, `(8,26,8,6)`, and `(16,26,8,6)`.
- Existing panels `interface_basic.throughput`, `interface_basic.packet_rate`, and `interface_basic.discard_port_count` keep their current coordinates.
- Materialized current switch dashboards still expose the old upper/health-cluster panels and now also expose the new bottom band.

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
go test ./OneOps/app/platform/service/impl -run 'Test(SnmpGrafanaSwitchCurrentPanelDefinitionsAppendBottomExtensionBand|SnmpGrafanaSwitchCurrentSharedTemplateKeepsExistingLayoutAndAddsBottomExtensionBand)$' -count=1
```

Expected:
```text
--- FAIL: TestSnmpGrafanaSwitchCurrentPanelDefinitionsAppendBottomExtensionBand
--- FAIL: TestSnmpGrafanaSwitchCurrentSharedTemplateKeepsExistingLayoutAndAddsBottomExtensionBand
```

## Task 2: Add the new bottom-extension panel definitions

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`

- [ ] **Step 1: Implement the additional panel hook**

Return three `snmpGrafanaPanelDefinition` entries from `snmpGrafanaSwitchCurrentAdditionalPanelDefinitions()`:
- `interface_basic.traffic_summary`
- `interface_basic.discard_summary`
- `interface_basic.broadcast_summary`

Each definition must:
- use `DashboardVariant: snmpGrafanaSwitchDashboardVariant`;
- preserve the current layout by only occupying `y=26` and below;
- reuse `interface_basic` metric group capabilities.

- [ ] **Step 2: Append the additional panels to the current skeleton**

Update `snmpGrafanaSwitchCurrentPanelDefinitions()` so it returns the existing 22-panel slice plus `snmpGrafanaSwitchCurrentAdditionalPanelDefinitions()`.

- [ ] **Step 3: Add minimal render wiring**

Extend the current switch render helpers so the new panels:
- produce timeseries targets for traffic and discard summaries;
- produce pie/stat-composition targets for the broadcast summary using existing broadcast packet capabilities;
- expose stable legends.

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
go test ./OneOps/app/platform/service/impl -run 'Test(SnmpGrafanaSwitchCurrentPanelDefinitionsAppendBottomExtensionBand|SnmpGrafanaSwitchCurrentSharedTemplateKeepsExistingLayoutAndAddsBottomExtensionBand)$' -count=1
```

Expected:
```text
ok  	github.com/netxops/OneOps/app/platform/service/impl	0.xxxs
```

## Task 3: Verify no regression to the existing switch shared skeleton

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Run focused switch dashboard verification**

Run:
```bash
go test ./OneOps/app/platform/service/impl -run 'Test(SnmpGrafanaGenericPanelDefinitionsUseCurrentOpsLayoutSkeleton|SnmpGrafanaSwitchBaselineModuleResolvesCurrent|SwitchGrafanaDashboardUsesOpsScreenshotLayoutContract|SnmpGrafanaPanelDefinitionsForTargetAndBaseline_GenericUsesSharedOpsSkeleton|SnmpGrafanaSwitchCurrentPanelDefinitionsAppendBottomExtensionBand|SnmpGrafanaSwitchCurrentSharedTemplateKeepsExistingLayoutAndAddsBottomExtensionBand)$' -count=1
```

Expected:
```text
ok  	github.com/netxops/OneOps/app/platform/service/impl	0.xxxs
```

- [ ] **Step 2: Re-read the spec and verify behavior matches**

Check the implementation against:
- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-network-strategy-generic-dashboard-panel-design.md`

Confirm:
- no existing panel moved;
- new panels are additive;
- all switch shared dashboards inherit the same bottom band.
