# SNMP Strategy Set Contract Context Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional device-context selection to the strategy-set SNMP metric contract resolver while keeping the default aggregate behavior unchanged.

**Architecture:** Reuse the existing `StrategySetMatcher` scoring semantics for strategy selector sets. The strategy-set metric-contract endpoint accepts optional context query parameters; when no context is provided it keeps aggregating all enabled item contracts, and when context is provided it only aggregates matched strategies. Frontend receives typed query parameters only; no page UI consumes this yet.

**Tech Stack:** Go backend under `/OneOPS/OneOps`, Gin routing, TypeScript frontend API under `/OneOPS/OneOps-UI`.

---

## Scope Lock

Allowed backend files:

- `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
- `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
- `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- `/OneOPS/OneOps/app/platform/api/teleabs.go`

Allowed frontend files:

- `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`

Allowed docs:

- `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

Out of scope:

- no Grafana JSON generation,
- no Prometheus recording-rule lifecycle,
- no UI controls or page consumption,
- no database schema changes,
- no new metric standardization,
- no processor YAML parsing.

## Context Query Contract

The existing endpoint remains:

```text
GET /platform/metrics/teleabs/strategy-sets/:id/metric-contract
```

Optional query parameters:

```text
function_area
catalog_id
catalog_name
manufacturer_name
platform_name
device_model_name
system_version
```

When none of these are provided, behavior remains the current enabled-item aggregate.

When at least one is provided, the resolver should select matching strategy-selector items using the same matching rules as `StrategySetMatcher`: catalog, manufacturer, platform, model, version, fallback, priority, and sort order.

## Task 1: Add Failing Context Selection Test

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
- Modify: `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [x] **Step 1: Add option DTO**

Add:

```go
type SnmpMetricStrategySetContractOptions struct {
	FunctionArea     string `json:"function_area,omitempty"`
	CatalogID        string `json:"catalog_id,omitempty"`
	CatalogName      string `json:"catalog_name,omitempty"`
	ManufacturerName string `json:"manufacturer_name,omitempty"`
	PlatformName     string `json:"platform_name,omitempty"`
	DeviceModelName  string `json:"device_model_name,omitempty"`
	SystemVersion    string `json:"system_version,omitempty"`
}
```

- [x] **Step 2: Add interface method**

Add:

```go
ResolveStrategySetContractWithOptions(ctx context.Context, strategySetID string, opts dto.SnmpMetricStrategySetContractOptions) (*dto.SnmpMetricStrategySetContractResolution, error)
```

Keep existing `ResolveStrategySetContract(ctx, strategySetID)` as a no-options wrapper.

- [x] **Step 3: Write failing test**

Add a test where a strategy set has:

- a generic interface strategy,
- an H3C/Comware/S6520 child strategy,
- a Huawei strategy.

Call `ResolveStrategySetContractWithOptions` with:

```go
ManufacturerName: "H3C"
PlatformName: "Comware"
DeviceModelName: "S6520"
CatalogName: "network"
```

Expected:

- only the H3C strategy contributes to `item_contracts`;
- `effective_contract.metric_groups` contains `interface_basic`;
- Huawei and generic strategies do not contribute when a more specific same-family candidate wins.

- [x] **Step 4: Run focused test and verify RED**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverResolvesStrategySetWithContext -count=1
```

Expected: FAIL because option-based resolver is missing.

## Task 2: Implement Context Selection

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`

- [x] **Step 1: Add no-options wrapper**

Make existing `ResolveStrategySetContract` call `ResolveStrategySetContractWithOptions` with empty options.

- [x] **Step 2: Detect whether options are empty**

If all option fields are blank, keep current enabled-item aggregate behavior.

- [x] **Step 3: Use `StrategySetMatcher` for context selection**

Build a one-device `service.TelegrafDeviceSpec` with metadata from options and call:

```go
matcher := NewStrategySetMatcher(r.StrategySetSrv, r.StrategySrv)
selection, err := matcher.ResolveDevices(ctx, strategySetID, []service.TelegrafDeviceSpec{device})
```

Use `selection.Groups[].StrategyID` as the selected strategy IDs.

- [x] **Step 4: Aggregate selected strategy contracts only**

Build `item_contracts` from selected strategy IDs and merge their effective contracts in deterministic order.

- [x] **Step 5: Run focused tests and verify GREEN**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolver -count=1
```

Expected: PASS.

## Task 3: API Query Params And Frontend Typing

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/api/teleabs.go`
- Modify: `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`

- [x] **Step 1: Parse query params in API**

`GetTeleabsStrategySetMetricContract` should pass query params into `ResolveStrategySetContractWithOptions`.

- [x] **Step 2: Add frontend API params type**

Allow `getTeleabsStrategySetMetricContract(id, params?)` with the same optional context fields.

- [x] **Step 3: Run compile checks**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/api ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver|^$' -count=1

cd /OneOPS/OneOps-UI
npm run typecheck
```

Expected: PASS.

## Task 4: Handoff Sync And Final Verification

**Files:**

- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [x] **Step 1: Document optional context selection**

Record:

```text
strategy-set metric-contract supports optional context query
empty context keeps aggregate enabled-item behavior
context mode reuses StrategySetMatcher semantics
no UI/Grafana/Prometheus scope added
```

- [x] **Step 2: Run final verification**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolver -count=1
go test ./app/platform/api ./app/platform/service/impl ./cmd -run 'TestMetricCapabilityContractResolver|^$' -count=1

cd /OneOPS/OneOps-UI
npm run smoke:snmp-metric-contract
npm run smoke:snmp-profile-resolution
npm run smoke:snmp-workspace-view
npm run typecheck
```

Expected: all pass.
