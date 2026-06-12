# SNMP Dashboard Save And Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an explicit SNMP strategy-set by-target API that saves the generated switch Grafana dashboard and syncs the saved dashboard to live Grafana.

**Architecture:** Keep `save/by-target` as platform persistence only. Add `save-and-sync/by-target` in the Teleabs API layer: it calls the existing resolver save method, then reuses the existing Grafana dashboard service `BatchSync([dashboard_code])`. Return the same materialized payload with `synced=true` only when batch sync succeeds.

**Tech Stack:** Go API/service tests in `OneOps`, existing Grafana dashboard service, TypeScript API typings in `OneOPS-UI`, quick_env shell smoke.

---

### Task 1: Backend API Contract

**Files:**
- Modify: `OneOps/app/platform/dto/snmp_metric_contract.go`
- Modify: `OneOps/app/platform/api/teleabs.go`
- Modify: `OneOps/app/platform/api/teleabs_metric_contract_http_test.go`
- Modify: `OneOps/app/platform/router/platform.go`
- Modify: `OneOps/app/platform/router/platform_bidi.go`
- Modify: `OneOps/app/platform/router/teleabs_route_consistency_test.go`

- [ ] **Step 1: Write failing API test**

Add `TestTeleabsAPI_SaveAndSyncStrategySetGrafanaDashboardByTarget_HTTP` that posts:

```text
/platform/metrics/teleabs/strategy-sets/set-1/metric-contract/grafana/dashboards/save-and-sync/by-target
```

The fake resolver returns a saved dashboard response with `dashboard_code=GDBSNMP123`, `synced=false`. The fake Grafana sync service records the code and returns success. The test expects response `code=0`, `saved=true`, `synced=true`, and the fake sync call list equals `["GDBSNMP123"]`.

- [ ] **Step 2: Run API test red**

```bash
cd OneOps
go test ./app/platform/api -run TestTeleabsAPI_SaveAndSyncStrategySetGrafanaDashboardByTarget_HTTP -count=1
```

Expected: fail because route/handler/fake dependency is missing.

- [ ] **Step 3: Implement handler**

Add `SaveAndSyncTeleabsStrategySetGrafanaDashboardByTarget`. It must:

1. parse the same request body as `save/by-target`;
2. call `MetricContractResolver.ResolveStrategySetTargetGrafanaDashboardSaveByTarget`;
3. fail if `dashboard_code` is empty;
4. call `GrafanaDashboardSrv.BatchSync([]string{dashboard_code}, ctx)`;
5. return `synced=true` only if `Success == 1 && Failed == 0`;
6. keep `save/by-target` unchanged.

- [ ] **Step 4: Add routes**

Register:

```text
strategy-sets/:id/metric-contract/grafana/dashboards/save-and-sync/by-target
```

in both platform and bidi route files.

- [ ] **Step 5: Run API/router tests green**

```bash
cd OneOps
go test ./app/platform/api -run 'TestTeleabsAPI_.*GrafanaDashboard' -count=1
go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1
```

### Task 2: Frontend API Types

**Files:**
- Modify: `OneOPS-UI/src/typings/platform/snmp-metric-contract.ts`
- Modify: `OneOPS-UI/src/api/platform/teleabs.ts`
- Modify: `OneOPS-UI/scripts/snmp-strategy-set-grafana-dashboard-materialization-dry-run-smoke.ts`

- [ ] **Step 1: Write failing smoke assertion**

Assert the TypeScript API source contains:

```text
/metric-contract/grafana/dashboards/save-and-sync/by-target
saveAndSyncTeleabsStrategySetGrafanaDashboardByTarget
```

- [ ] **Step 2: Run smoke red**

```bash
cd OneOPS-UI
npm run smoke:snmp-strategy-set-grafana-dashboard-materialization-dry-run
```

Expected: fail because the helper is absent.

- [ ] **Step 3: Add request helper**

Export `saveAndSyncTeleabsStrategySetGrafanaDashboardByTarget(id, data)` using the same response type as save.

- [ ] **Step 4: Run smoke green**

```bash
cd OneOPS-UI
npm run smoke:snmp-strategy-set-grafana-dashboard-materialization-dry-run
```

### Task 3: Quick Env Live Sync Smoke

**Files:**
- Modify: `quick_env/scripts/smoke_snmp_switch_dashboard_save.sh`
- Modify: `quick_env/tests/test_seed_template_guard.py`
- Modify: `quick_env/README.md`

- [ ] **Step 1: Write failing guard**

Require the quick_env smoke script to contain `SAVE_AND_SYNC`, `save-and-sync/by-target`, and a Grafana API readback check for the synced UID.

- [ ] **Step 2: Run guard red**

```bash
python3 quick_env/tests/test_seed_template_guard.py -v -k save_and_sync
```

- [ ] **Step 3: Extend smoke script**

Add `SAVE_AND_SYNC=true` mode. In sync mode, call `save-and-sync/by-target`, assert `synced=true`, and query Grafana `/api/dashboards/uid/<uid>` through `GRAFANA_URL=http://127.0.0.1:3300` with `GRAFANA_USER=admin`, `GRAFANA_PASSWORD=admin`.

- [ ] **Step 4: Run real smoke**

```bash
SAVE_AND_SYNC=true quick_env/scripts/smoke_snmp_switch_dashboard_save.sh
```

Expected: HTTP 200, `synced=true`, dashboard row count 1, binding row count 1, Grafana API readback title matches.

### Task 4: Documentation And Verification

**Files:**
- Modify: `docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [ ] **Step 1: Document the new closure**

Append the endpoint, smoke command, verified Grafana UID/title, and remaining gaps.

- [ ] **Step 2: Full verification**

```bash
cd OneOps
go test ./app/platform/api -run 'TestTeleabsAPI_.*GrafanaDashboard|TestTeleabsAPI_.*RecordingRule' -count=1
go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1

cd ../OneOPS-UI
npm run smoke:snmp-strategy-set-grafana-dashboard-materialization-dry-run

cd ..
python3 quick_env/tests/test_seed_template_guard.py -v
bash -n quick_env/scripts/smoke_snmp_switch_dashboard_save.sh
git -C OneOps diff --check
git -C OneOPS-UI diff --check
git -C quick_env diff --check
git -C docs diff --check
```
