# SNMP Strategy Set Contract Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add strategy-set-level SNMP metric contract resolution without expanding into target matching, Grafana JSON, Prometheus rules, or UI work.

**Architecture:** Reuse the existing backend strategy-level metric contract resolver. A strategy set resolution returns per-item contracts and an aggregate effective contract by merging non-empty SNMP contracts in item order. Frontend only receives a typed API wrapper for this backend data; no page consumes or displays it yet.

**Tech Stack:** Go backend under `/OneOPS/OneOps`, Gin routing, Wire provider sets, TypeScript frontend API under `/OneOPS/OneOps-UI`.

---

## Scope Lock

Allowed backend files:

- `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
- `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
- `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- `/OneOPS/OneOps/app/platform/api/teleabs.go`
- `/OneOPS/OneOps/app/platform/router/platform.go`
- `/OneOPS/OneOps/app/platform/router/platform_bidi.go`
- `/OneOPS/OneOps/cmd/wire_gen.go`

Allowed frontend files:

- `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`

Allowed docs:

- `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

Out of scope:

- no strategy target/device matching,
- no dashboard/Grafana materialization,
- no Prometheus recording-rule publishing,
- no new UI consumption,
- no persistence/schema changes,
- no processor YAML parsing,
- no new metric standardization.

## Backend Contract

Add one endpoint:

```text
GET /platform/metrics/teleabs/strategy-sets/:id/metric-contract
```

Response data shape:

```json
{
  "strategy_set_id": "set-1",
  "source": "backend_resolver",
  "item_contracts": [
    {
      "strategy_set_item_id": "item-1",
      "strategy_id": "strategy-1",
      "teleabs_template_id": "snmp",
      "sort_order": 1,
      "priority": 10,
      "enabled": true,
      "contract": { "version": 1, "metric_groups": [] }
    }
  ],
  "effective_contract": { "version": 1, "metric_groups": [] }
}
```

Only enabled items with non-empty contracts should contribute to `effective_contract`.

## Task 1: Add Failing Strategy-Set Resolver Test

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
- Modify: `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [x] **Step 1: Add DTO shape for strategy-set resolution**

Add:

```go
type SnmpMetricStrategySetContractResolution struct { ... }
type SnmpMetricStrategySetItemContract struct { ... }
```

- [x] **Step 2: Add interface method**

Add:

```go
ResolveStrategySetContract(ctx context.Context, strategySetID string) (*dto.SnmpMetricStrategySetContractResolution, error)
```

- [x] **Step 3: Write failing test**

The test should create a fake strategy set with two enabled items:

- one SNMP interface strategy,
- one SNMP system strategy.

Expected:

- `item_contracts` length is `2`;
- aggregate `effective_contract.metric_groups` contains `interface_basic` and `system_basic`;
- disabled items do not contribute.

- [x] **Step 4: Run focused test and verify RED**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverResolvesStrategySet -count=1
```

Expected: FAIL because strategy-set resolver implementation is missing.

## Task 2: Implement Strategy-Set Resolver

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/cmd/wire_gen.go`

- [x] **Step 1: Inject `ITeleabsStrategySet` into resolver**

Extend constructor and Wire generated initialization so resolver has both strategy and strategy-set services.

- [x] **Step 2: Resolve item contracts**

For each enabled item:

- if `StrategyID` is present, resolve the referenced strategy contract;
- else if `DefaultParams` is present, parse it as a standalone contract;
- skip empty contracts.

- [x] **Step 3: Aggregate effective contract**

Merge non-empty item contracts in `SortOrder` order. Later groups with the same `group_key` override earlier groups.

- [x] **Step 4: Run focused test and verify GREEN**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolver -count=1
```

Expected: PASS.

## Task 3: Add API Route And Frontend Wrapper

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/api/teleabs.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform_bidi.go`
- Modify: `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- Modify: `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`

- [x] **Step 1: Add TeleabsAPI handler**

Add `GetTeleabsStrategySetMetricContract`.

- [x] **Step 2: Add routes before `strategy-sets/:id`**

Add:

```go
teleabsGroup.GET("strategy-sets/:id/metric-contract", teleabsAPI.GetTeleabsStrategySetMetricContract)
```

- [x] **Step 3: Add frontend types and API method**

Add `SnmpMetricStrategySetContractResolution` and `getTeleabsStrategySetMetricContract`.

- [x] **Step 4: Run compile/type checks**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/api ./app/platform/service/impl ./cmd -run 'TestMetricCapabilityContractResolver|^$' -count=1

cd /OneOPS/OneOps-UI
npm run typecheck
```

Expected: PASS.

## Task 4: Handoff Sync And Final Verification

**Files:**

- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [x] **Step 1: Document strategy-set closure**

Record:

```text
strategy-set metric-contract endpoint exists
it aggregates enabled item contracts only
no target matching yet
no Grafana/Prometheus work yet
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
