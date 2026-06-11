# SNMP Recording Rule Materialization Dry-Run Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert SNMP recording rule preview results into Prometheus-compatible rule YAML in a dry-run endpoint, without writing files, reloading Prometheus, or generating Grafana JSON.

**Architecture:** Reuse the existing by-target recording rule preview resolver. Add a pure YAML materializer that renders `SnmpRecordingRulePreviewGroup` into Prometheus rule-file YAML and validates it by parsing it back. Expose one strict by-target dry-run endpoint and frontend typed API support only.

**Tech Stack:** Go service/API/router in `/OneOPS/OneOps`, using existing `gopkg.in/yaml.v3`; TypeScript API/types smoke in `/OneOPS/OneOps-UI`; quick env real API acceptance for H3C/Huawei/Maipu.

---

## Scope Lock

This plan only implements:

```text
strategy_set_id + target_part
  -> ResolveStrategySetTargetRecordingRulePreview
  -> materialize Prometheus rule YAML
  -> validate generated YAML locally
  -> return dry-run response
```

Strict non-goals:

- no Prometheus file write;
- no Prometheus reload;
- no publish lifecycle persistence;
- no Grafana dashboard JSON;
- no Grafana UI page;
- no new metric standardization.

The request body remains:

```json
{ "target_part": "DEVICE-CODE-OR-ID" }
```

---

## File Structure

Backend DTO and service interface:

- Modify `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
  - Add materialization DTOs.
- Modify `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
  - Add by-target dry-run materialization resolver method.

Backend implementation:

- Modify `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
  - Add Prometheus YAML materializer and validator helpers.
  - Add by-target dry-run resolver method.
- Modify `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
  - Add materializer unit tests.
  - Add by-target dry-run resolver tests.

Backend API/router:

- Modify `/OneOPS/OneOps/app/platform/api/teleabs.go`
  - Add HTTP handler.
- Modify `/OneOPS/OneOps/app/platform/router/platform.go`
  - Register route.
- Modify `/OneOPS/OneOps/app/platform/router/platform_bidi.go`
  - Register route.
- Modify `/OneOPS/OneOps/app/platform/router/teleabs_routes_consistency_test.go`
  - Add required route.
- Modify `/OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go`
  - Add HTTP tests.

Frontend:

- Modify `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
  - Add materialization dry-run types.
- Modify `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`
  - Add typed API wrapper.
- Create `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-materialization-dry-run-smoke.ts`
  - Assert request body is only `{ target_part }` and response shape holds YAML.
- Create `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-materialization-dry-run-real-api-acceptance.cjs`
  - Assert real H3C/Huawei/Maipu API output.
- Modify `/OneOPS/OneOps-UI/package.json`
  - Add both smoke scripts.

Docs:

- Modify `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`
  - Add dry-run materialization stage notes.

---

### Task 1: Backend DTO Contract

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`

- [ ] **Step 1: Add materialization DTOs**

Add after `SnmpStrategySetTargetRecordingRulePreviewResponse`:

```go
type SnmpPrometheusRuleFile struct {
	Groups []SnmpPrometheusRuleGroup `json:"groups" yaml:"groups"`
}

type SnmpPrometheusRuleGroup struct {
	Name     string                       `json:"name" yaml:"name"`
	Interval string                       `json:"interval,omitempty" yaml:"interval,omitempty"`
	Rules    []SnmpPrometheusRuleFileRule `json:"rules" yaml:"rules"`
}

type SnmpPrometheusRuleFileRule struct {
	Record string `json:"record" yaml:"record"`
	Expr   string `json:"expr" yaml:"expr"`
}

type SnmpRecordingRuleMaterializationSummary struct {
	Format           string   `json:"format"`
	DryRun           bool     `json:"dry_run"`
	GroupCount       int      `json:"group_count"`
	RuleCount        int      `json:"rule_count"`
	YAMLBytes        int      `json:"yaml_bytes"`
	Valid            bool     `json:"valid"`
	ValidationErrors []string `json:"validation_errors"`
}

type SnmpStrategySetTargetRecordingRuleMaterializationDryRunRequest struct {
	TargetPart string `json:"target_part"`
}

type SnmpStrategySetTargetRecordingRuleMaterializationDryRunResponse struct {
	StrategySetID     string                                  `json:"strategy_set_id"`
	Target            SnmpMetricResolvedTargetContext         `json:"target"`
	Source            string                                  `json:"source"`
	ItemContracts     []SnmpMetricStrategySetItemContract     `json:"item_contracts"`
	EffectiveContract SnmpMetricContractEnvelope              `json:"effective_contract"`
	RuleGroup         SnmpRecordingRulePreviewGroup           `json:"rule_group"`
	Rules             []SnmpRecordingRulePreviewRule          `json:"rules"`
	Summary           SnmpRecordingRulePreviewSummary         `json:"summary"`
	YAML              string                                  `json:"yaml"`
	Materialization   SnmpRecordingRuleMaterializationSummary `json:"materialization"`
}
```

- [ ] **Step 2: Run compile check**

```bash
cd /OneOPS/OneOps
go test ./app/platform/dto -run '^$' -count=1
```

Expected: PASS.

---

### Task 2: Pure YAML Materializer

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Write failing materializer test**

Add `TestMetricCapabilityContractResolverMaterializesRecordingRulePreviewYAML`.

Input rule group:

```go
dto.SnmpRecordingRulePreviewGroup{
	Name: "oneops_snmp_recording_rules_preview",
	Interval: "30s",
	Rules: []dto.SnmpRecordingRulePreviewRule{
		{Record: "oneops:if_in_rate:bps", Expr: "rate(snmp_interface_ifInOctets[5m]) * 8"},
		{Record: "oneops:cpu_usage_direct:ratio", Expr: "snmp_cpu_usage / 100"},
	},
}
```

Assert:

- YAML contains `groups:`;
- YAML contains `name: oneops_snmp_recording_rules_preview`;
- YAML contains both records;
- materialization summary has `format = prometheus_rule_file`;
- `dry_run = true`;
- `group_count = 1`;
- `rule_count = 2`;
- `valid = true`;
- `validation_errors` is empty.

- [ ] **Step 2: Run failing test**

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverMaterializesRecordingRulePreviewYAML -count=1
```

Expected: FAIL because materializer does not exist.

- [ ] **Step 3: Implement materializer**

Add:

```go
func (r *MetricCapabilityContractResolver) MaterializeRecordingRulePreviewYAML(group dto.SnmpRecordingRulePreviewGroup) (string, dto.SnmpRecordingRuleMaterializationSummary, error)
```

Implementation:

- create `dto.SnmpPrometheusRuleFile{Groups: []dto.SnmpPrometheusRuleGroup{...}}`;
- copy `record` and `expr` only;
- marshal with `gopkg.in/yaml.v3`;
- parse back into `dto.SnmpPrometheusRuleFile`;
- validate one group, non-empty group name, non-empty record/expr, count equality;
- return error when invalid.

- [ ] **Step 4: Run materializer test**

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverMaterializesRecordingRulePreviewYAML -count=1
```

Expected: PASS.

---

### Task 3: By-Target Dry-Run Resolver

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Add interface method**

```go
ResolveStrategySetTargetRecordingRuleMaterializationDryRun(ctx context.Context, strategySetID string, request dto.SnmpStrategySetTargetRecordingRuleMaterializationDryRunRequest) (*dto.SnmpStrategySetTargetRecordingRuleMaterializationDryRunResponse, error)
```

- [ ] **Step 2: Write failing resolver test**

Add `TestMetricCapabilityContractResolverMaterializesStrategySetRecordingRulesByTarget`.

Use the existing target-device fixture and `recordingRulePreviewPassthroughConfigForTest()`.

Assert:

- target context is H3C/Comware;
- `rules` contains `oneops:if_in_rate:bps`;
- `yaml` contains `groups:`;
- `materialization.valid = true`;
- `materialization.rule_count = len(rules)`;
- empty target fails with `target_part is required`.

- [ ] **Step 3: Implement resolver method**

Flow:

```text
ResolveStrategySetTargetRecordingRulePreview(...)
MaterializeRecordingRulePreviewYAML(preview.RuleGroup)
return dry-run response
```

- [ ] **Step 4: Run resolver test**

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolverMaterializesRecordingRulePreviewYAML|TestMetricCapabilityContractResolverMaterializesStrategySetRecordingRulesByTarget' -count=1
```

Expected: PASS.

---

### Task 4: Backend HTTP Route

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/api/teleabs.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform_bidi.go`
- Modify: `/OneOPS/OneOps/app/platform/router/teleabs_routes_consistency_test.go`
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go`

- [ ] **Step 1: Write failing HTTP tests**

Add `TestTeleabsAPI_MaterializeStrategySetRecordingRulesByTarget_HTTP`.

Path:

```text
POST /platform/metrics/teleabs/strategy-sets/set-1/metric-contract/recording-rules/materialize/dry-run/by-target
```

Body:

```json
{ "target_part": "SW-1" }
```

Assert:

- resolver receives `set-1` and `SW-1`;
- response data includes `yaml`;
- response data includes `materialization.valid = true`;
- empty target returns strict error from resolver.

- [ ] **Step 2: Implement handler and route**

Handler:

```go
func (a *TeleabsAPI) MaterializeTeleabsStrategySetRecordingRulesByTarget(ctx *gin.Context)
```

Route in both routers:

```text
POST strategy-sets/:id/metric-contract/recording-rules/materialize/dry-run/by-target
```

- [ ] **Step 3: Run HTTP and route tests**

```bash
cd /OneOPS/OneOps
go test ./app/platform/api -run TestTeleabsAPI_MaterializeStrategySetRecordingRulesByTarget -count=1
go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1
```

Expected: PASS.

---

### Task 5: Frontend Types And Smoke

**Files:**

- Modify: `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- Modify: `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`
- Create: `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-materialization-dry-run-smoke.ts`
- Modify: `/OneOPS/OneOps-UI/package.json`

- [ ] **Step 1: Add frontend types and wrapper**

Add TypeScript interfaces matching backend DTOs.

Wrapper:

```ts
export const materializeTeleabsStrategySetRecordingRulesByTarget = async (
  id: string,
  body: SnmpStrategySetTargetRecordingRuleMaterializationDryRunRequest,
) => { ... }
```

URL:

```text
/platform/metrics/teleabs/strategy-sets/:id/metric-contract/recording-rules/materialize/dry-run/by-target
```

- [ ] **Step 2: Add smoke script**

Assert:

- request body keys equal `["target_part"]`;
- response type can hold `yaml`;
- response type can hold `materialization.valid`.

- [ ] **Step 3: Run smoke**

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-strategy-set-recording-rule-materialization-dry-run
```

Expected: PASS.

---

### Task 6: Real API Acceptance

**Files:**

- Create: `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-materialization-dry-run-real-api-acceptance.cjs`
- Modify: `/OneOPS/OneOps-UI/package.json`

- [ ] **Step 1: Add real API acceptance script**

Use:

```text
ONEOPS_API_BASE_URL default http://127.0.0.1:18082/api/v1
ONEOPS_API_TOKEN required
ONEOPS_STRATEGY_SET_ID default 4284353d-1233-4022-ad18-871b3d8444c7
```

Cases:

```text
DVCF5A07C0AFFC9
DVC2C4468B0B813
DVCF21C6B43350C
```

Assert for each:

- `materialization.valid = true`;
- `materialization.rule_count = 12`;
- YAML contains `groups:`;
- YAML contains all 12 known record names;
- request body is exactly `{ target_part }`.

- [ ] **Step 2: Add package script**

```json
"smoke:snmp-strategy-set-recording-rule-materialization-dry-run-real-api": "node scripts/snmp-strategy-set-recording-rule-materialization-dry-run-real-api-acceptance.cjs"
```

- [ ] **Step 3: Run only with current backend**

```bash
cd /OneOPS/OneOps-UI
ONEOPS_API_BASE_URL=http://127.0.0.1:18082/api/v1 \
ONEOPS_API_TOKEN="$(cat /tmp/oneops-ui-real-page-token-18082.txt)" \
npm run smoke:snmp-strategy-set-recording-rule-materialization-dry-run-real-api
```

Expected: PASS.

---

### Task 7: Handoff And Verification

**Files:**

- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [ ] **Step 1: Update handoff**

Add:

- endpoint path;
- request/response shape;
- YAML example;
- real API acceptance results;
- explicit deferred items: file write, reload, lifecycle, Grafana.

- [ ] **Step 2: Run focused verification**

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*RecordingRule|TestMetricCapabilityContractResolverMaterializes' -count=1
go test ./app/platform/api -run 'TestTeleabsAPI_.*RecordingRulesByTarget' -count=1
go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1

cd /OneOPS/OneOps-UI
npm run smoke:snmp-strategy-set-recording-rule-preview
npm run smoke:snmp-strategy-set-recording-rule-materialization-dry-run

cd /OneOPS/quick_env
bash tests/test_sync_snmp_network_strategy_seed.sh
bash tests/test_snmp_network_strategy_seed.sh

git -C /OneOPS/OneOps diff --check
git -C /OneOPS/OneOps-UI diff --check
git -C /OneOPS/quick_env diff --check
git -C /OneOPS/docs diff --check
```

Expected: PASS / no output.
