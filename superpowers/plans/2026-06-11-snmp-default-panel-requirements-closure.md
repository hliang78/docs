# SNMP Default Panel Requirements Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide a canonical default list of base SNMP panel capability requirements and make strategy-set panel previews use it when callers do not pass custom requirements.

**Architecture:** The backend owns the default base panel requirement catalog. The existing strategy-set preview composes context matching, effective metric contract resolution, and panel support evaluation; this step adds a default input so callers can complete the data loop with only `strategy_set_id + context`. This plan does not generate Grafana dashboard JSON, does not attach UI pages, and does not expand metric standardization beyond base common panels.

**Tech Stack:** Go service/API in `/OneOPS/OneOps`; TypeScript API/types in `/OneOPS/OneOps-UI`; TDD with focused Go resolver tests and existing frontend smoke/typecheck.

---

### Task 1: Backend Default Panel Requirements

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
- Modify: `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Test: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [x] **Step 1: Write failing tests**

Add tests covering:
- default requirements contain the base common panels in stable order:
  - `interface_basic.traffic`
  - `interface_basic.status`
  - `interface_basic.speed`
  - `interface_basic.quality`
  - `interface_basic.broadcast`
  - `system_basic.cpu`
  - `system_basic.memory`
- strategy-set panel preview uses default requirements when request `requirements` is empty

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver(DefaultPanelRequirements|PreviewsStrategySetPanelCapabilitySupportWithDefaultRequirements)' -count=1
```

Expected: FAIL because default requirement methods/DTOs do not exist yet.

- [x] **Step 3: Write minimal implementation**

Add DTO:
- `SnmpPanelCapabilityRequirementCatalogResponse`

Add resolver interface method:
- `DefaultPanelCapabilityRequirements() []dto.SnmpPanelCapabilityRequirement`

Implement default requirements:
- traffic requires `if_in_rate`, `if_out_rate`
- status requires `if_oper_status`
- speed accepts `if_speed_bps` and can fall back to `config_driven_query: "ifSpeed"`
- quality accepts any current quality/error/discard capability and can be partial when requirements are specified by callers
- broadcast accepts `if_in_broadcast_ratio` or `if_out_broadcast_ratio`
- CPU accepts `cpu_usage_direct` or `cpu_usage_from_idle`
- memory accepts `memory_usage_direct`, `memory_usage_used_total`, or `memory_usage_free_total`

Update preview resolver:
- if `request.Requirements` is empty, use `DefaultPanelCapabilityRequirements()`

- [x] **Step 4: Run tests to verify they pass**

Run the same focused test command. Expected: PASS.

### Task 2: Backend API Endpoint

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform_bidi.go`

- [x] **Step 1: Add a narrow GET handler**

Add:

```text
GET /platform/metrics/teleabs/metric-contract/panel-requirements/default
```

Response body:

```json
{
  "requirements": []
}
```

- [x] **Step 2: Wire route in both routers**

Register the handler in both standard and bidi platform routers under the existing `teleabs` metrics namespace.

### Task 3: Frontend Typed API

**Files:**
- Modify: `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- Modify: `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`

- [x] **Step 1: Add response type**

Add:
- `SnmpPanelCapabilityRequirementCatalogResponse`

- [x] **Step 2: Add API wrapper**

Add:

```ts
getDefaultSnmpPanelCapabilityRequirements()
```

This wrapper is intentionally not consumed by pages in this plan.

### Task 4: Verification

**Files:**
- No new production files.

- [x] **Step 1: Backend focused tests**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolver -count=1
```

- [x] **Step 2: Backend compile checks**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/api ./app/platform/service/impl ./cmd -run 'TestMetricCapabilityContractResolver|^$' -count=1
```

- [x] **Step 3: Frontend checks**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-metric-contract
npm run typecheck
```

Expected: all commands exit with code 0.
