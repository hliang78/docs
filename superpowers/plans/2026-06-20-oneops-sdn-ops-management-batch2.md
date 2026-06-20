# OneOPS SDN Ops Management Batch 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:dispatching-parallel-agents to implement the independent workstreams. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the first SDN resource workbench into an operational loop covering diagnostics, alarms, enhanced resource filtering, and guarded configuration plans.

**Architecture:** OneOPS remains vendor-neutral and calls CtrlHub for controller-specific actions. CtrlHub owns ACI/Huawei/H3C API behavior. Configuration execution stays disabled until approval, audit, and rollback are designed and accepted.

**Tech Stack:** Go, GORM, Gin, OneOPS service/API/router patterns, Vue 3, TypeScript, Ant Design Vue, CtrlHub Go SDN adapters.

---

## Current Baseline

- CtrlHub has `/api/v1/sdn/snapshot` and `/api/v1/sdn/diagnose`.
- CtrlHub has normalized `Alarm`/`AlarmResponse` types and ACI `faultInst` mapping tests.
- OneOPS has SDN controller CRUD, test, sync, latest snapshot, history, resource projection, and snapshot diff.
- OneOPS has `SDNConfigPlanService` for draft/dry-run with live execution disabled.
- OneOPS-UI has `src/views/device/SdnControllerManagement.vue` with controller list, sync/test, resource workbench, snapshot history, and diff.

## Safety Rules

- OneOPS must not add vendor-specific ACI/Huawei/H3C clients.
- OneOPS must not persist or echo SDN controller passwords.
- Real SDN configuration apply remains disabled.
- Do not revert unrelated dirty files in `OneOPS`, `OneOPS-UI`, `ctrlhub`, or `docs`.
- Ask before any live write to APIC/Huawei/H3C.

## Parallel Workstreams

### W5: CtrlHub SDN Alarm Collection API

**Repo:** `/Users/huangliang/project/OneOPS-ALL/ctrlhub`

- [ ] Add `AlarmRequest` and `AlarmAdapter` in `controller/pkg/sdn`.
- [ ] Add registry method `NewAlarmAdapter(provider)`.
- [ ] Implement ACI `CollectAlarms(ctx, endpoint, options)` using `/api/node/class/faultInst.json`.
- [ ] Add `ControllerAPI.SDNAlarms` for `POST /api/v1/sdn/alarms`.
- [ ] Register the route beside snapshot/diagnose.
- [ ] Add focused tests for registry, ACI alarm collection, and API response.
- [ ] Verify:

```bash
go test ./controller/pkg/sdn ./controller/pkg/sdn/aci ./controller/pkg/sdn/adapters ./controller/pkg/controller/api -run 'Test.*Alarm|TestSDNAlarms|TestNewAlarmAdapter' -count=1
```

### W6: OneOPS Diagnostics And Alarms Backend

**Repo:** `/Users/huangliang/project/OneOPS-ALL/OneOPS`

- [ ] Add diagnostic and alarm DTOs to `app/platform/dto/sdn_controller.go`.
- [ ] Add `Diagnose(ctx,id)` and `ListAlarms(ctx,id)` to `ISDNControllerStore`.
- [ ] Reuse SDN controller config and Secret service to call CtrlHub `/api/v1/sdn/diagnose` and `/api/v1/sdn/alarms`.
- [ ] Add `POST /sdn/controllers/:id/diagnose`.
- [ ] Add `POST /sdn/controllers/:id/alarms`.
- [ ] Add httptest-backed service tests for success and CtrlHub readable failure messages.
- [ ] Verify:

```bash
go test ./app/platform/service/impl ./app/platform/api ./app/platform/router -run 'TestSDN.*Diagnose|TestSDN.*Alarm|TestSdn.*Diagnose|TestSdn.*Alarm|TestSDNController' -count=1
```

### W7: OneOPS SDN Config Plan API

**Repo:** `/Users/huangliang/project/OneOPS-ALL/OneOPS`

- [ ] Add service interface for `SDNConfigPlanService`.
- [ ] Add API handlers for create draft, dry-run, and execute-disabled.
- [ ] Add routes under `/sdn/config-plans`.
- [ ] Wire service/API sets without non-SDN provider churn.
- [ ] Add tests for create, dry-run, and disabled execute behavior.
- [ ] Verify:

```bash
go test ./app/platform/service/impl ./app/platform/api ./app/platform/router -run 'TestSDNConfigPlan|TestSdnConfigPlan' -count=1
go test ./app/platform/api ./app/platform/router -count=1
```

### W8: OneOPS-UI SDN Ops Workbench

**Repo:** `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI`

- [ ] Add TypeScript API wrappers and types for diagnostics, alarms, and config plans.
- [ ] Add resource filters for tenant, VRF, and network.
- [ ] Add diagnostics drawer/modal to show stage checks.
- [ ] Add alarms drawer/table to show severity, status, resource, code, and message.
- [ ] Add guarded config-plan drawer supporting draft and dry-run; live execute must remain visibly disabled or return the backend disabled message.
- [ ] Extend or add smoke coverage for new helper behavior.
- [ ] Verify:

```bash
npx prettier --check src/views/device/SdnControllerManagement.vue src/api/platform/sdn-controller.ts src/typings/platform/sdn-controller.ts scripts/sdn-resource-workbench-smoke.ts package.json
npm run smoke:sdn-resource-workbench
```

## Batch 2 Acceptance

- CtrlHub can collect ACI alarms through a normalized `/api/v1/sdn/alarms` contract.
- OneOPS can request diagnostics and alarms through CtrlHub without vendor-specific logic.
- OneOPS exposes config plan draft/dry-run API but still blocks real execution.
- OneOPS-UI lets an operator inspect resources, run diagnostics, inspect alarms, and prepare dry-run plans from the SDN controller page.
- All focused tests above pass after integration.
