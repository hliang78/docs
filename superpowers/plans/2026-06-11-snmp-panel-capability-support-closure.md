# SNMP Panel Capability Support Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a narrow backend/frontend data contract that evaluates whether dashboard panel requirements are supported by a resolved SNMP metric contract.

**Architecture:** The backend resolver owns the canonical capability judgment from `contract.metric_groups[].fields[].capability_key`. Grafana/page code can later consume a stable `panel_key -> state` result without re-deriving vendor/platform-specific raw metric semantics. This plan does not generate Grafana dashboards, does not attach the result to pages, and does not expand metric standardization.

**Tech Stack:** Go service/API in `/OneOPS/OneOps`; TypeScript API/types in `/OneOPS/OneOps-UI`; TDD with focused Go resolver tests and existing frontend typecheck/smoke checks.

---

### Task 1: Backend Capability Support Resolver

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
- Modify: `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Test: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [x] **Step 1: Write the failing test**

Add `TestMetricCapabilityContractResolverResolvesPanelCapabilitySupport` covering:
- acceptable alternatives: CPU panel supports either `cpu_usage_direct` or `cpu_usage_from_idle`
- required capabilities: interface quality is partial when one required metric is missing
- config-driven fallback: custom panel becomes `config_driven` when `config_driven_query` is present
- unsupported: panel with missing capability and no fallback is `unsupported`

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverResolvesPanelCapabilitySupport -count=1
```

Expected: FAIL because the DTOs/methods do not exist yet.

- [x] **Step 3: Write minimal implementation**

Add DTOs:
- `SnmpPanelCapabilityRequirement`
- `SnmpPanelCapabilitySupport`
- `SnmpPanelCapabilitySupportRequest`
- `SnmpPanelCapabilitySupportResponse`

Add resolver interface methods:
- `ResolvePanelCapabilitySupport(contract, requirement)`
- `ResolvePanelCapabilitySupports(contract, requirements)`

Implement rules:
- Collect enabled fields from all enabled groups.
- A field is available by `capability_key` first, otherwise `metric_key`.
- If `acceptable_capabilities` has any available key, state is `supported` and selected contains the first available key in request order.
- Else if `required_capabilities` are all available, state is `supported` and selected contains all required keys.
- Else if some required keys are available, state is `partial`, selected contains available keys, missing contains unavailable keys.
- Else if `config_driven_query` is non-empty, state is `config_driven`.
- Else state is `unsupported`, missing contains requested acceptable or required keys.

- [x] **Step 4: Run test to verify it passes**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverResolvesPanelCapabilitySupport -count=1
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
POST /platform/metrics/teleabs/metric-contract/panel-support
```

Request body:

```json
{
  "contract": { "version": 1, "metric_groups": [] },
  "requirements": []
}
```

Response body:

```json
{
  "supports": []
}
```

- [x] **Step 2: Wire route in both routers**

Register the handler in both standard and bidi platform routers under the existing `teleabs` metrics namespace.

### Task 3: Frontend Typed API

**Files:**
- Modify: `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- Modify: `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`

- [x] **Step 1: Add request/response types**

Add:
- `SnmpPanelCapabilitySupportRequest`
- `SnmpPanelCapabilitySupportResponse`

- [x] **Step 2: Add API wrapper**

Add:

```ts
resolveSnmpPanelCapabilitySupport(body: SnmpPanelCapabilitySupportRequest)
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
