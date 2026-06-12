# SNMP Grafana Dashboard Materialization Dry-Run Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate SNMP Grafana dashboard JSON as a strict by-target dry-run, without writing dashboard rows or syncing to Grafana.

**Architecture:** Reuse the existing by-target panel support and recording-rule preview data. Add a pure dashboard materializer in the metric capability resolver that emits Grafana-compatible JSON, validation metadata, and panel binding previews. Expose backend and frontend typed dry-run APIs only.

**Tech Stack:** Go service/API/router in `OneOps`; TypeScript API/types smoke in `OneOPS-UI`; existing `encoding/json`, `crypto/sha256`, Gin route tests, and esbuild smoke scripts.

---

## Scope Lock

This plan only implements:

```text
strategy_set_id + target_part
  -> ResolveStrategySetTargetPanelCapabilityPreview
  -> ResolveStrategySetTargetRecordingRulePreview
  -> materialize Grafana dashboard JSON
  -> validate generated JSON locally
  -> return dry-run response
```

Strict non-goals:

- no `grafana_dashboard` create or update;
- no `syncToGrafana`;
- no dashboard diff;
- no persistent panel binding table;
- no automatic publish;
- no inventory-wide generation;
- no new metric standardization.

The request body remains:

```json
{ "target_part": "DEVICE-CODE-OR-ID" }
```

---

## File Structure

Backend DTO and interface:

- Modify `OneOps/app/platform/dto/snmp_metric_contract.go`
  - Add Grafana dashboard dry-run DTOs.
- Modify `OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
  - Add by-target dry-run resolver method.

Backend implementation:

- Modify `OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
  - Add pure Grafana dashboard materializer and validation helpers.
  - Add by-target dry-run resolver method.
- Modify `OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
  - Add materializer and by-target resolver tests.

Backend API/router:

- Modify `OneOps/app/platform/api/teleabs.go`
  - Add HTTP handler.
- Modify `OneOps/app/platform/router/platform.go`
  - Register route.
- Modify `OneOps/app/platform/router/platform_bidi.go`
  - Register route.
- Modify `OneOps/app/platform/router/teleabs_routes_consistency_test.go`
  - Add required route.
- Modify `OneOps/app/platform/api/teleabs_metric_contract_http_test.go`
  - Add HTTP tests.

Frontend:

- Modify `OneOPS-UI/src/typings/platform/snmp-metric-contract.ts`
  - Add dry-run request/response types.
- Modify `OneOPS-UI/src/api/platform/teleabs.ts`
  - Add typed API wrapper.
- Create `OneOPS-UI/scripts/snmp-strategy-set-grafana-dashboard-materialization-dry-run-smoke.ts`
  - Assert request body is only `{ target_part }` and response shape contains JSON, bindings, and materialization metadata.
- Modify `OneOPS-UI/package.json`
  - Add smoke script.

Docs:

- Modify `docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`
  - Add the dry-run Grafana stage notes after the recording-rule publish section.

---

### Task 1: Backend DTO Contract

**Files:**

- Modify: `OneOps/app/platform/dto/snmp_metric_contract.go`

- [ ] **Step 1: Write the DTO compile test command**

Run:

```bash
cd OneOps
go test ./app/platform/dto -run '^$' -count=1
```

Expected: PASS before and after DTO changes.

- [ ] **Step 2: Add Grafana dry-run DTOs**

Add after `SnmpStrategySetTargetRecordingRulePublishResponse`:

```go
type SnmpGrafanaDashboardMaterializationSummary struct {
	Format           string   `json:"format"`
	DryRun           bool     `json:"dry_run"`
	PanelCount       int      `json:"panel_count"`
	BindingCount     int      `json:"binding_count"`
	JSONBytes        int      `json:"json_bytes"`
	Valid            bool     `json:"valid"`
	ValidationErrors []string `json:"validation_errors"`
}

type SnmpGrafanaPanelBindingPreview struct {
	PanelKey               string   `json:"panel_key"`
	PanelID                int      `json:"panel_id"`
	Title                  string   `json:"title"`
	StrategySetID          string   `json:"strategy_set_id"`
	StrategyIDs            []string `json:"strategy_ids"`
	MetricGroupKey         string   `json:"metric_group_key,omitempty"`
	MetricKeys             []string `json:"metric_keys"`
	SelectedCapabilityKeys []string `json:"selected_capability_keys"`
	RecordNames            []string `json:"record_names"`
	ManagedState           string   `json:"managed_state"`
	ContentHash            string   `json:"content_hash"`
}

type SnmpStrategySetTargetGrafanaDashboardMaterializationDryRunRequest struct {
	TargetPart string `json:"target_part"`
}

type SnmpStrategySetTargetGrafanaDashboardMaterializationDryRunResponse struct {
	StrategySetID         string                                      `json:"strategy_set_id"`
	Target                SnmpMetricResolvedTargetContext             `json:"target"`
	Source                string                                      `json:"source"`
	ItemContracts         []SnmpMetricStrategySetItemContract         `json:"item_contracts"`
	EffectiveContract     SnmpMetricContractEnvelope                  `json:"effective_contract"`
	Supports              []SnmpPanelCapabilitySupport                `json:"supports"`
	SupportSummary        SnmpPanelCapabilitySupportSummary           `json:"support_summary"`
	RuleGroup             SnmpRecordingRulePreviewGroup               `json:"rule_group"`
	Rules                 []SnmpRecordingRulePreviewRule              `json:"rules"`
	RecordingRuleSummary  SnmpRecordingRulePreviewSummary             `json:"recording_rule_summary"`
	Dashboard             map[string]interface{}                      `json:"dashboard"`
	DashboardJSON         string                                      `json:"dashboard_json"`
	PanelBindings         []SnmpGrafanaPanelBindingPreview            `json:"panel_bindings"`
	Materialization       SnmpGrafanaDashboardMaterializationSummary  `json:"materialization"`
}
```

- [ ] **Step 3: Run compile check**

Run:

```bash
cd OneOps
go test ./app/platform/dto -run '^$' -count=1
```

Expected: PASS.

### Task 2: Pure Grafana Materializer

**Files:**

- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Write failing materializer test**

Add `TestMetricCapabilityContractResolverMaterializesGrafanaDashboardJSON` using a target context, all default panel supports as supported, and recording rules for CPU, memory, interface traffic, status, speed, quality, and broadcast.

Assert:

- dashboard title contains the device code;
- materialization format is `grafana_dashboard_json`;
- dry-run is true;
- at least seven panels are generated;
- panel count equals binding count;
- dashboard JSON contains `oneops:if_in_rate:bps`;
- every binding has `managed_state = preview` and a content hash.

- [ ] **Step 2: Run failing test**

Run:

```bash
cd OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverMaterializesGrafanaDashboardJSON -count=1
```

Expected: FAIL because the materializer does not exist.

- [ ] **Step 3: Implement materializer helpers**

Add helpers with these responsibilities:

- `MaterializeGrafanaDashboardDryRun(...)` builds the dashboard map, serialized JSON, bindings, and summary.
- `snmpGrafanaPanelDefinitions()` maps the seven base panel keys to titles, visual types, record names, and metric group keys.
- `snmpGrafanaPanelType(...)` maps `timeseries`, `stat`, `gauge`, and `table` to Grafana panel types.
- `validateMaterializedGrafanaDashboardJSON(...)` parses and validates generated JSON and binding count.
- `snmpGrafanaPanelHash(...)` hashes each generated panel JSON.

- [ ] **Step 4: Run materializer test**

Run:

```bash
cd OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverMaterializesGrafanaDashboardJSON -count=1
```

Expected: PASS.

### Task 3: By-Target Resolver

**Files:**

- Modify: `OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Add interface method**

```go
ResolveStrategySetTargetGrafanaDashboardMaterializationDryRun(ctx context.Context, strategySetID string, request dto.SnmpStrategySetTargetGrafanaDashboardMaterializationDryRunRequest) (*dto.SnmpStrategySetTargetGrafanaDashboardMaterializationDryRunResponse, error)
```

- [ ] **Step 2: Write failing by-target resolver test**

Add `TestMetricCapabilityContractResolverMaterializesStrategySetGrafanaDashboardByTarget`.

Assert:

- target context is H3C/Comware;
- response has panel support summary total `7`;
- response has recording rule summary generated `12`;
- dashboard JSON contains the target device code;
- panel bindings include `interface_basic.traffic`;
- empty target fails with `target_part is required`.

- [ ] **Step 3: Run failing resolver test**

Run:

```bash
cd OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverMaterializesStrategySetGrafanaDashboardByTarget -count=1
```

Expected: FAIL because the resolver method does not exist.

- [ ] **Step 4: Implement resolver method**

Implementation:

- call `ResolveStrategySetTargetPanelCapabilityPreview`;
- call `ResolveStrategySetTargetRecordingRulePreview`;
- pass target, strategy set id, item contracts, supports, and rules into the pure materializer;
- return the dry-run response;
- do not call any Grafana service and do not write database rows.

- [ ] **Step 5: Run resolver test**

Run:

```bash
cd OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverMaterializesStrategySetGrafanaDashboardByTarget -count=1
```

Expected: PASS.

### Task 4: Backend HTTP Route

**Files:**

- Modify: `OneOps/app/platform/api/teleabs.go`
- Modify: `OneOps/app/platform/api/teleabs_metric_contract_http_test.go`
- Modify: `OneOps/app/platform/router/platform.go`
- Modify: `OneOps/app/platform/router/platform_bidi.go`
- Modify: `OneOps/app/platform/router/teleabs_routes_consistency_test.go`

- [ ] **Step 1: Write failing HTTP handler test**

Add `TestTeleabsAPI_MaterializeStrategySetGrafanaDashboardByTarget_HTTP`.

Assert:

- route id is passed as `strategy_set_id`;
- request body `target_part` is passed unchanged after JSON bind;
- success response includes `target.context`, `dashboard_json`, and `materialization`;
- empty body delegates to strict resolver and returns `target_part is required`.

- [ ] **Step 2: Run failing HTTP test**

Run:

```bash
cd OneOps
go test ./app/platform/api -run TestTeleabsAPI_MaterializeStrategySetGrafanaDashboardByTarget_HTTP -count=1
```

Expected: FAIL because the handler route is missing.

- [ ] **Step 3: Add handler and routes**

Route path:

```text
POST strategy-sets/:id/metric-contract/grafana/dashboards/materialize/dry-run/by-target
```

Add the same route to `platform.go` and `platform_bidi.go`.

- [ ] **Step 4: Update router consistency test**

Add the new route string to the required Teleabs route set.

- [ ] **Step 5: Run HTTP and route tests**

Run:

```bash
cd OneOps
go test ./app/platform/api -run TestTeleabsAPI_MaterializeStrategySetGrafanaDashboardByTarget_HTTP -count=1
go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1
```

Expected: PASS.

### Task 5: Frontend Types And API Smoke

**Files:**

- Modify: `OneOPS-UI/src/typings/platform/snmp-metric-contract.ts`
- Modify: `OneOPS-UI/src/api/platform/teleabs.ts`
- Create: `OneOPS-UI/scripts/snmp-strategy-set-grafana-dashboard-materialization-dry-run-smoke.ts`
- Modify: `OneOPS-UI/package.json`

- [ ] **Step 1: Add frontend types**

Mirror the backend dry-run DTOs in TypeScript.

- [ ] **Step 2: Add API wrapper**

Add:

```ts
export const materializeTeleabsStrategySetGrafanaDashboardByTarget = async (
  id: string,
  body: SnmpStrategySetTargetGrafanaDashboardMaterializationDryRunRequest,
) => {
  const resp = await requestEnvelope<SnmpStrategySetTargetGrafanaDashboardMaterializationDryRunResponse>({
    url: `${BASE}/strategy-sets/${encodeURIComponent(
      id,
    )}/metric-contract/grafana/dashboards/materialize/dry-run/by-target`,
    method: HTTP_POST,
    data: body,
    silentError: true,
  });
  if (!resp || resp.code !== 0) {
    throw new Error(resp?.msg || 'Grafana dashboard dry-run 生成失败');
  }
  return resp.data;
};
```

- [ ] **Step 3: Add smoke test**

The smoke script stubs `requestEnvelope`, calls the wrapper, and asserts:

- URL contains `/grafana/dashboards/materialize/dry-run/by-target`;
- body is exactly `{ target_part: 'DVCF21C6B43350C' }`;
- returned response contains `dashboard_json`, `panel_bindings`, and valid materialization metadata;
- backend `code != 0` throws backend `msg`.

- [ ] **Step 4: Add npm script**

Add:

```json
"smoke:snmp-strategy-set-grafana-dashboard-materialization-dry-run": "tsx scripts/snmp-strategy-set-grafana-dashboard-materialization-dry-run-smoke.ts"
```

- [ ] **Step 5: Run frontend smoke and typecheck**

Run:

```bash
cd OneOPS-UI
npm run smoke:snmp-strategy-set-grafana-dashboard-materialization-dry-run
npm run typecheck
```

Expected: PASS.

### Task 6: Handoff Update And Verification

**Files:**

- Modify: `docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [ ] **Step 1: Add handoff section**

Add a new section after recording-rule publish lifecycle:

```text
SNMP Grafana dashboard materialization dry-run is now opened.
It returns dashboard JSON and panel binding previews only.
It does not write grafana_dashboard and does not call syncToGrafana.
The request body remains target_part only.
```

- [ ] **Step 2: Run backend focused checks**

Run:

```bash
cd OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*GrafanaDashboard|TestMetricCapabilityContractResolver.*RecordingRule|TestMetricCapabilityContractResolver.*Publish' -count=1
go test ./app/platform/api -run 'TestTeleabsAPI_.*GrafanaDashboard|TestTeleabsAPI_.*RecordingRulesByTarget|TestTeleabsAPI_PublishStrategySetRecordingRulesByTarget' -count=1
go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1
go test ./cmd -run '^$' -count=1
```

Expected: PASS.

- [ ] **Step 3: Run frontend focused checks**

Run:

```bash
cd OneOPS-UI
npm run smoke:snmp-strategy-set-grafana-dashboard-materialization-dry-run
npm run smoke:snmp-strategy-set-recording-rule-publish
npm run typecheck
```

Expected: PASS.

- [ ] **Step 4: Run diff hygiene**

Run:

```bash
git -C OneOps diff --check
git -C OneOPS-UI diff --check
git -C quick_env diff --check
git -C docs diff --check
```

Expected: no whitespace errors.

