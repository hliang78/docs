# SNMP Strategy Set Panel Support Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a narrow data-layer preview that resolves a strategy set with optional device context, then evaluates panel capability requirements against the resolved effective SNMP metric contract.

**Architecture:** The resolver composes two existing responsibilities: strategy-set metric contract resolution and panel capability support resolution. The API returns the selected item contracts, effective contract, and panel support states in one response, so later Grafana/page code can consume a stable preview without duplicating selection or capability logic. This plan does not generate Grafana dashboard JSON, does not attach UI pages, and does not expand metric standardization.

**Tech Stack:** Go service/API in `/OneOPS/OneOps`; TypeScript API/types in `/OneOPS/OneOps-UI`; TDD with focused Go resolver tests plus existing frontend smoke/typecheck.

---

### Task 1: Backend Strategy Set Panel Preview Resolver

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
- Modify: `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Test: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [x] **Step 1: Write the failing test**

Add `TestMetricCapabilityContractResolverPreviewsStrategySetPanelCapabilitySupport` covering:
- a strategy set with context selects the matching vendor/platform strategy
- the response keeps `strategy_set_id`, `item_contracts`, and `effective_contract`
- CPU acceptable alternatives resolve to `supported`
- interface error requirements resolve to `partial` when the selected contract lacks one required metric

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverPreviewsStrategySetPanelCapabilitySupport -count=1
```

Expected: FAIL because preview DTOs/methods do not exist yet.

- [x] **Step 3: Write minimal implementation**

Add DTOs:
- `SnmpStrategySetPanelCapabilityPreviewRequest`
- `SnmpStrategySetPanelCapabilityPreviewResponse`

Add resolver interface method:
- `ResolveStrategySetPanelCapabilityPreview(ctx, strategySetID, request)`

Implementation:
- call `ResolveStrategySetContractWithOptions(ctx, strategySetID, request.Context)`
- call `ResolvePanelCapabilitySupports(resolution.EffectiveContract, request.Requirements)`
- return strategy set ID, source, item contracts, effective contract, and supports

- [x] **Step 4: Run test to verify it passes**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverPreviewsStrategySetPanelCapabilitySupport -count=1
```

Expected: PASS.

### Task 2: Backend API Endpoint

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform_bidi.go`

- [x] **Step 1: Add a narrow POST handler**

Add:

```text
POST /platform/metrics/teleabs/strategy-sets/:id/metric-contract/panel-support
```

Request body:

```json
{
  "context": {
    "manufacturer_name": "H3C",
    "platform_name": "Comware",
    "device_model_name": "S6520",
    "system_version": "7.1"
  },
  "requirements": []
}
```

Response body:

```json
{
  "strategy_set_id": "set-1",
  "source": "backend_resolver",
  "item_contracts": [],
  "effective_contract": { "version": 1, "metric_groups": [] },
  "supports": []
}
```

- [x] **Step 2: Wire route in both routers**

Register the handler in both standard and bidi platform routers under the existing `teleabs/strategy-sets/:id` namespace.

### Task 3: Frontend Typed API

**Files:**
- Modify: `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- Modify: `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`

- [x] **Step 1: Add request/response types**

Add:
- `SnmpStrategySetPanelCapabilityPreviewRequest`
- `SnmpStrategySetPanelCapabilityPreviewResponse`

- [x] **Step 2: Add API wrapper**

Add:

```ts
previewTeleabsStrategySetPanelCapabilitySupport(id, body)
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
