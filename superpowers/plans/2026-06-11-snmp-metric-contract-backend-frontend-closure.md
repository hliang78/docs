# SNMP Metric Contract Backend Frontend Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the SNMP metric capability contract available from the OneOps backend and have the existing frontend workspace prefer that backend answer without changing UI or expanding dashboard scope.

**Architecture:** Add a backend platform service resolver that reads existing Teleabs strategy parameters and returns the same semantic contract shape already used by the frontend. Add one thin Teleabs API endpoint for strategy contract resolution. On the frontend, add a typed API method and inject returned `metric_groups` into the existing workspace model, with local parsing remaining as fallback.

**Tech Stack:** Go backend under `/OneOPS/OneOps`, Gin routing, Wire provider sets, TypeScript/Vue frontend under `/OneOPS/OneOps-UI`, existing smoke scripts and `vue-tsc`.

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
- `/OneOPS/OneOps/boot/provider/service_groups.go`
- `/OneOPS/OneOps/cmd/wire_gen.go`

Allowed frontend files:

- `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`
- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/index.vue`
- `/OneOPS/OneOps-UI/scripts/snmp-workspace-view-smoke.ts`

Allowed docs:

- `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

Out of scope:

- no database schema changes,
- no strategy-set contract resolver yet,
- no Prometheus recording-rule generation or publishing,
- no Grafana dashboard JSON generation,
- no new Vue UI controls or layout changes,
- no standardization beyond the already agreed base SNMP contract,
- no backend parsing of legacy processor YAML such as `snmpIftableProcess`.

## Backend Contract

Add one endpoint:

```text
GET /platform/metrics/teleabs/strategies/:id/metric-contract
```

Response data shape:

```json
{
  "strategy_id": "strategy-1",
  "parent_strategy_id": "parent-1",
  "source": "backend_resolver",
  "contract": { "version": 1, "metric_groups": [] },
  "parent_contract": { "version": 1, "metric_groups": [] },
  "effective_contract": { "version": 1, "metric_groups": [] }
}
```

`contract` is the current strategy contract. `parent_contract` is present only when the strategy has a parent. `effective_contract` is a simple parent/child merge for preview and future consumers.

## Task 1: Backend DTO And Failing Resolver Test

**Files:**

- Create: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
- Create: `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
- Create: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [x] **Step 1: Add DTO structs**

Create Go DTOs matching the existing frontend JSON fields:

```go
package dto

type SnmpMetricContractEnvelope struct {
	Version      int                       `json:"version"`
	MetricGroups []SnmpMetricGroupContract `json:"metric_groups"`
}
```

Include group, field, raw source, transform rule, recording rule, panel spec, and response structs.

- [x] **Step 2: Add service interface**

Create:

```go
type IMetricCapabilityContractResolver interface {
	ResolveStrategyContract(ctx context.Context, strategyID string) (*dto.SnmpMetricContractResolution, error)
}
```

- [x] **Step 3: Write failing tests**

Tests must cover:

- `snmp_interface` table imports as `interface_basic`;
- `ifSpeed` becomes `if_speed_bps`;
- error/discard capabilities remain rate/pps;
- top-level `cpuIdle`, `memUsed`, `memTotal`, `memFree` imports as `system_basic`;
- unknown fields remain config-driven.

- [x] **Step 4: Run tests and verify RED**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolver -count=1
```

Expected: FAIL because resolver implementation does not exist.

## Task 2: Backend Resolver Implementation

**Files:**

- Create: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/boot/provider/service_groups.go`

- [x] **Step 1: Implement parameter-only parsing helpers**

Use existing Teleabs strategy parameters:

```text
metric_groups
passthrough_config
metric_manifest
```

If `metric_groups` exists and is non-empty, return it as explicit contract. Otherwise import from `passthrough_config`.

- [x] **Step 2: Implement SNMP table capability mapping**

Map current base interface fields only:

```text
ifDescr / ifName / ifAlias -> if_name
ifInOctets / ifHCInOctets -> if_in_rate
ifOutOctets / ifHCOutOctets -> if_out_rate
ifOperStatus -> if_oper_status
ifSpeed -> if_speed_bps
ifInErrors -> if_in_error_rate
ifOutErrors -> if_out_error_rate
ifInDiscards -> if_in_discard_rate
ifOutDiscards -> if_out_discard_rate
ifInNUcastPkts + ifInUcastPkts + ifInOctets + ifSpeed -> if_in_broadcast_ratio
ifOutNUcastPkts + ifOutUcastPkts + ifOutOctets + ifSpeed -> if_out_broadcast_ratio
```

Leave unstandardized table fields config-driven.

- [x] **Step 3: Implement system capability mapping**

Map current top-level fields only:

```text
cpuUsage -> cpu_usage_direct
cpuIdle -> cpu_usage_from_idle
memUsage -> memory_usage_direct
memUsed + memTotal -> memory_usage_used_total
memFree + memTotal -> memory_usage_free_total
```

Leave unknown top-level fields in `device_metrics` as config-driven.

- [x] **Step 4: Wire the service**

Add a provider set and include it in `ServicePlatformProviderSet`.

- [x] **Step 5: Run resolver tests and verify GREEN**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolver -count=1
```

Expected: PASS.

## Task 3: Backend API And Routing

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/api/teleabs.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform_bidi.go`

- [x] **Step 1: Inject resolver into TeleabsAPI**

Add:

```go
MetricContractResolver service.IMetricCapabilityContractResolver
```

- [x] **Step 2: Add handler**

Add `GetTeleabsStrategyMetricContract` that validates `:id`, calls the resolver, and returns `response.OkWithData`.

- [x] **Step 3: Add routes before `strategies/:id`**

Add:

```go
teleabsGroup.GET("strategies/:id/metric-contract", teleabsAPI.GetTeleabsStrategyMetricContract)
```

Place it before `teleabsGroup.GET("strategies/:id", ...)`.

- [x] **Step 4: Run backend compile check**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/api ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver|^$' -count=1
```

Expected: PASS.

## Task 4: Frontend API And Safe Consumption

**Files:**

- Modify: `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- Modify: `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/index.vue`
- Modify if useful: `/OneOPS/OneOps-UI/scripts/snmp-workspace-view-smoke.ts`

- [x] **Step 1: Add frontend response type**

Add `SnmpMetricContractResolution` matching backend JSON.

- [x] **Step 2: Add typed API method**

Add:

```ts
export const getTeleabsStrategyMetricContract = async (id: string) => request<SnmpMetricContractResolution>(...)
```

- [x] **Step 3: Prefer backend contract in SNMP workspace load**

In `openSnmpMetricGroupsFromStrategy`, after fetching strategy detail, call the new endpoint. If it returns non-empty `contract.metric_groups`, set:

```ts
strategyParams.metric_groups = resolution.contract.metric_groups
```

If it returns non-empty `parent_contract.metric_groups`, set parent record parameters similarly.

If the endpoint fails, do not block the page; continue with existing local parsing.

- [x] **Step 4: Run frontend checks**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-workspace-view
npm run typecheck
```

Expected: PASS.

## Task 5: Handoff Sync And Full Verification

**Files:**

- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [x] **Step 1: Document the backend/frontend closure**

Record:

```text
backend resolver endpoint exists
frontend prefers backend contract and falls back to local resolver
still no Prometheus publishing
still no Grafana JSON generation
strategy-set resolver still deferred
```

- [x] **Step 2: Run final verification**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolver -count=1
go test ./app/platform/api ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver|^$' -count=1

cd /OneOPS/OneOps-UI
npm run smoke:snmp-metric-contract
npm run smoke:snmp-profile-resolution
npm run smoke:snmp-workspace-view
npm run typecheck
```

Expected: all pass.
