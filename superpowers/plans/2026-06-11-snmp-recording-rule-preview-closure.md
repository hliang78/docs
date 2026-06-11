# SNMP Recording Rule Preview Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a strict backend/frontend data preview that turns by-target SNMP strategy-set contracts into Prometheus recording rule previews, without publishing rules or generating Grafana JSON.

**Architecture:** Reuse the existing by-target strategy-set contract resolver, then pass the effective contract through a new pure recording-rule preview builder. The builder emits Prometheus rule-group-shaped data for base common recordable capabilities only, using existing `recording_rule`, `raw_source`, and `transform_rule` metadata. Frontend work is limited to typed API access and smoke coverage.

**Tech Stack:** Go DTO/service/API/router tests in `/OneOPS/OneOps`; TypeScript API/types smoke in `/OneOPS/OneOps-UI`; docs in `/OneOPS/docs`; TDD with focused unit and HTTP tests.

---

## Scope Lock

This plan only implements:

```text
strategy_set_id + target_part
  -> ResolveStrategySetContractWithOptions(...)
  -> effective_contract
  -> base recordable capability allowlist
  -> recording rule preview response
```

Strict non-goals:

- no Prometheus rule file write;
- no Prometheus reload;
- no publish/saved/reloaded lifecycle table;
- no Grafana dashboard JSON;
- no Grafana page changes;
- no legacy YAML parser;
- no additional vendor-specific standardization beyond the existing base capability contract.

The by-target request body remains strict:

```json
{ "target_part": "DEVICE-CODE-OR-ID" }
```

No caller-provided context, manufacturer, platform, model, version, or requirements are accepted in this path.

---

## File Structure

Backend DTO and service interface:

- Modify `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
  - Add recording rule preview DTOs.
- Modify `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
  - Add by-target recording rule preview method.

Backend implementation:

- Modify `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
  - Add pure rule preview builder helpers.
  - Add by-target resolver method.
- Modify `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
  - Add expression/rule selection tests.
  - Add by-target preview resolver tests.

Backend API/router:

- Modify `/OneOPS/OneOps/app/platform/api/teleabs.go`
  - Add HTTP handler.
- Modify `/OneOPS/OneOps/app/platform/router/platform.go`
  - Register route.
- Modify `/OneOPS/OneOps/app/platform/router/platform_bidi.go`
  - Register route.
- Modify `/OneOPS/OneOps/app/platform/router/teleabs_routes_consistency_test.go`
  - Assert normal and bidi route lists stay aligned.
- Modify `/OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go`
  - Add HTTP acceptance tests.

Frontend:

- Modify `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
  - Add recording rule preview types.
- Modify `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`
  - Add typed API wrapper.
- Create `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-preview-smoke.ts`
  - Assert typed request body remains `{ target_part }`.
- Modify `/OneOPS/OneOps-UI/package.json`
  - Add smoke script.

Docs:

- Modify `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`
  - Add recording rule preview stage notes and deferred publish/Grafana items.

---

### Task 1: Backend DTO Contract

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`

- [ ] **Step 1: Write DTO compile check**

Run before editing to capture current state:

```bash
cd /OneOPS/OneOps
go test ./app/platform/dto -run '^$' -count=1
```

Expected: package compiles or reports no test files.

- [ ] **Step 2: Add recording rule preview DTOs**

Add these types after `SnmpStrategySetTargetPanelCapabilityPreviewResponse`:

```go
type SnmpRecordingRuleSource struct {
	MetricGroupKey string   `json:"metric_group_key,omitempty"`
	RawMeasurement string   `json:"raw_measurement,omitempty"`
	RawFields      []string `json:"raw_fields,omitempty"`
	TransformType  string   `json:"transform_type,omitempty"`
}

type SnmpRecordingRulePreviewRule struct {
	Record        string                  `json:"record"`
	Expr          string                  `json:"expr"`
	CapabilityKey string                  `json:"capability_key"`
	MetricKey     string                  `json:"metric_key"`
	ConceptKey    string                  `json:"concept_key,omitempty"`
	Unit          string                  `json:"unit,omitempty"`
	Source        SnmpRecordingRuleSource `json:"source"`
}

type SnmpRecordingRulePreviewGroup struct {
	Name     string                         `json:"name"`
	Interval string                         `json:"interval"`
	Rules    []SnmpRecordingRulePreviewRule `json:"rules"`
}

type SnmpRecordingRulePreviewSummary struct {
	Total                int `json:"total"`
	Generated            int `json:"generated"`
	Deduplicated         int `json:"deduplicated"`
	SkippedNotBase       int `json:"skipped_not_base"`
	SkippedNotRecordable int `json:"skipped_not_recordable"`
	SkippedConfigDriven  int `json:"skipped_config_driven"`
}

type SnmpStrategySetTargetRecordingRulePreviewRequest struct {
	TargetPart string `json:"target_part"`
}

type SnmpStrategySetTargetRecordingRulePreviewResponse struct {
	StrategySetID     string                              `json:"strategy_set_id"`
	Target            SnmpMetricResolvedTargetContext     `json:"target"`
	Source            string                              `json:"source"`
	ItemContracts     []SnmpMetricStrategySetItemContract `json:"item_contracts"`
	EffectiveContract SnmpMetricContractEnvelope          `json:"effective_contract"`
	RuleGroup         SnmpRecordingRulePreviewGroup       `json:"rule_group"`
	Rules             []SnmpRecordingRulePreviewRule      `json:"rules"`
	Summary           SnmpRecordingRulePreviewSummary     `json:"summary"`
}
```

- [ ] **Step 3: Run compile check**

```bash
cd /OneOPS/OneOps
go test ./app/platform/dto -run '^$' -count=1
```

Expected: package compiles.

---

### Task 2: Pure Recording Rule Builder

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Write failing test for base rule generation**

Add a test that builds a contract with:

- `ifInOctets` as `if_in_rate`;
- `ifOutOctets` as `if_out_rate`;
- `ifOperStatus` as `if_oper_status`;
- `ifSpeed` as `if_speed_bps`;
- `cpuUsage` as `cpu_usage_direct`;
- `memUsage` as `memory_usage_direct`;
- one config-driven field.

Assert generated records:

```text
oneops:if_in_rate:bps       rate(snmp_interface_ifInOctets[5m]) * 8
oneops:if_out_rate:bps      rate(snmp_interface_ifOutOctets[5m]) * 8
oneops:if_oper_status       snmp_interface_ifOperStatus
oneops:if_speed_bps         snmp_interface_ifSpeed
oneops:cpu_usage_direct:ratio     snmp_cpuUsage / 100
oneops:memory_usage_direct:ratio  snmp_memUsage / 100
```

Assert the config-driven field increments `skipped_config_driven`.

- [ ] **Step 2: Run the failing test**

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverBuildsRecordingRulePreview -count=1
```

Expected: FAIL because the builder does not exist.

- [ ] **Step 3: Implement builder entry point**

Add:

```go
func (r *MetricCapabilityContractResolver) BuildRecordingRulePreview(contract dto.SnmpMetricContractEnvelope) (dto.SnmpRecordingRulePreviewGroup, dto.SnmpRecordingRulePreviewSummary, error)
```

Use:

```text
group.name = "oneops_snmp_recording_rules_preview"
group.interval = "30s"
```

The method should:

- derive the base capability allowlist from `DefaultPanelCapabilityRequirements`;
- scan every group and field in `contract.MetricGroups`;
- skip config-driven fields;
- skip fields outside the base allowlist;
- skip fields without `recordability = "recordable"` or without enabled `recording_rule.record`;
- build expressions from `raw_source` and `transform_rule`;
- deduplicate same record/same expr;
- return an error on same record/different expr;
- sort rules by record name for stable output.

- [ ] **Step 4: Run the test**

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverBuildsRecordingRulePreview -count=1
```

Expected: PASS.

---

### Task 3: Expression Coverage

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`

- [ ] **Step 1: Write failing expression tests**

Add tests for:

```text
cpu_usage_from_idle:
  oneops:cpu_usage_from_idle:ratio
  1 - snmp_cpuIdle / 100

memory_usage_used_total:
  oneops:memory_usage_used_total:ratio
  snmp_memUsed / clamp_min(snmp_memTotal, 1)

memory_usage_free_total:
  oneops:memory_usage_free_total:ratio
  1 - snmp_memFree / clamp_min(snmp_memTotal, 1)

if_in_error_rate:
  oneops:if_in_error_rate:pps
  rate(snmp_interface_ifInErrors[5m])

if_in_broadcast_ratio:
  oneops:if_in_broadcast_ratio:ratio
  contains rate(snmp_interface_ifInNUcastPkts[5m])
  contains clamp_min(rate(snmp_interface_ifInNUcastPkts[5m]) + rate(snmp_interface_ifInUcastPkts[5m]), 1)
  contains clamp_min(snmp_interface_ifSpeed, 1)
```

- [ ] **Step 2: Run failing expression tests**

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverBuildsRecordingRuleExpressions -count=1
```

Expected: FAIL until expressions are implemented.

- [ ] **Step 3: Implement expression helpers**

Add helpers with focused names:

```go
func snmpRecordingRulePromMetricName(measurement, field, explicit string) string
func snmpRecordingRuleExpr(field dto.SnmpMetricFieldContract) (string, error)
func snmpRecordingRuleRateExpr(metric string, capabilityKey string) string
func snmpRecordingRuleExpressionExpr(field dto.SnmpMetricFieldContract, inputs map[string]string) (string, error)
```

Implement only current transform types:

```text
direct
rate
enum_map
expression
```

Unknown transform type returns an error.

- [ ] **Step 4: Run expression tests**

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverBuildsRecordingRuleExpressions -count=1
```

Expected: PASS.

---

### Task 4: Strict By-Target Resolver Method

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Add interface method**

Add:

```go
ResolveStrategySetTargetRecordingRulePreview(ctx context.Context, strategySetID string, request dto.SnmpStrategySetTargetRecordingRulePreviewRequest) (*dto.SnmpStrategySetTargetRecordingRulePreviewResponse, error)
```

- [ ] **Step 2: Write failing resolver test**

Create a test mirroring the existing by-target panel preview test. It should assert:

- target context is resolved through `platform_devices_v2`;
- selected item contract count is non-zero;
- generated rules include `oneops:if_in_rate:bps`, `oneops:if_out_rate:bps`, `oneops:cpu_usage_direct:ratio`, and `oneops:memory_usage_direct:ratio`;
- empty `target_part` fails;
- zero matched item contracts fails.

- [ ] **Step 3: Run failing resolver test**

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverPreviewsStrategySetRecordingRulesByTarget -count=1
```

Expected: FAIL until resolver method exists.

- [ ] **Step 4: Implement resolver method**

Implementation flow:

```text
validate strategySetID
ResolveTargetContext(ctx, request.TargetPart)
ResolveStrategySetContractWithOptions(ctx, strategySetID, target.Context)
error if resolution nil
error if item_contracts empty
BuildRecordingRulePreview(resolution.EffectiveContract)
return response with target, contracts, rule_group, rules, summary
```

- [ ] **Step 5: Run resolver test**

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverPreviewsStrategySetRecordingRulesByTarget -count=1
```

Expected: PASS.

---

### Task 5: Backend HTTP Route

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/api/teleabs.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform_bidi.go`
- Modify: `/OneOPS/OneOps/app/platform/router/teleabs_routes_consistency_test.go`
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go`

- [ ] **Step 1: Write failing HTTP tests**

Add tests for:

```text
POST /platform/metrics/teleabs/strategy-sets/set-1/metric-contract/recording-rules/preview/by-target
body: {"target_part":"SW-1"}
```

Assert:

- handler calls resolver with strategy set `set-1` and target `SW-1`;
- response contains `rule_group.rules`;
- empty body returns an error from resolver;
- request body has no context fields in the expected fixture.

- [ ] **Step 2: Run failing HTTP tests**

```bash
cd /OneOPS/OneOps
go test ./app/platform/api -run TestTeleabsAPI_PreviewStrategySetRecordingRulesByTarget -count=1
```

Expected: FAIL until handler is implemented.

- [ ] **Step 3: Implement handler and routes**

Add handler:

```go
func (a *TeleabsAPI) PreviewTeleabsStrategySetRecordingRulesByTarget(ctx *gin.Context)
```

Register route in both routers:

```text
POST strategy-sets/:id/metric-contract/recording-rules/preview/by-target
```

Update route consistency test with the new route.

- [ ] **Step 4: Run HTTP and route tests**

```bash
cd /OneOPS/OneOps
go test ./app/platform/api -run TestTeleabsAPI_PreviewStrategySetRecordingRulesByTarget -count=1
go test ./app/platform/router -run TestTeleabsRoutesConsistency -count=1
```

Expected: PASS.

---

### Task 6: Frontend Types And API Wrapper

**Files:**

- Modify: `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- Modify: `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`
- Create: `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-preview-smoke.ts`
- Modify: `/OneOPS/OneOps-UI/package.json`

- [ ] **Step 1: Write failing smoke**

Create smoke script that imports the API wrapper with a fake request layer or tests request body construction through the exported function shape used in this repo. The key assertion is:

```ts
assert.deepEqual(requestBody, { target_part: 'DVCF21C6B43350C' });
```

Also assert response types can hold:

```text
rule_group.name
rules[0].record
rules[0].expr
summary.generated
```

- [ ] **Step 2: Add package script**

Add:

```json
"smoke:snmp-strategy-set-recording-rule-preview": "npx esbuild scripts/snmp-strategy-set-recording-rule-preview-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/snmp-strategy-set-recording-rule-preview-smoke.mjs >/dev/null && node .tmp/snmp-strategy-set-recording-rule-preview-smoke.mjs"
```

- [ ] **Step 3: Run failing smoke**

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-strategy-set-recording-rule-preview
```

Expected: FAIL until types/API wrapper exist.

- [ ] **Step 4: Add frontend types and API wrapper**

Types should mirror backend JSON:

```ts
export interface SnmpRecordingRulePreviewRule { ... }
export interface SnmpRecordingRulePreviewGroup { ... }
export interface SnmpRecordingRulePreviewSummary { ... }
export interface SnmpStrategySetTargetRecordingRulePreviewRequest { target_part: string }
export interface SnmpStrategySetTargetRecordingRulePreviewResponse { ... }
```

API wrapper:

```ts
export const previewTeleabsStrategySetRecordingRulesByTarget = async (
  id: string,
  body: SnmpStrategySetTargetRecordingRulePreviewRequest,
) => request<SnmpStrategySetTargetRecordingRulePreviewResponse>({
  url: `/platform/metrics/teleabs/strategy-sets/${encodeURIComponent(id)}/metric-contract/recording-rules/preview/by-target`,
  method: 'post',
  data: body,
});
```

- [ ] **Step 5: Run frontend smoke**

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-strategy-set-recording-rule-preview
```

Expected: PASS.

---

### Task 7: Quick Env Seed Acceptance Script

**Files:**

- Create: `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-preview-real-api-acceptance.cjs`
- Modify: `/OneOPS/OneOps-UI/package.json`

- [ ] **Step 1: Write real API acceptance script**

Script inputs:

```text
ONEOPS_API_BASE_URL default http://127.0.0.1:18082/api/v1
ONEOPS_API_TOKEN required
ONEOPS_STRATEGY_SET_ID default 4284353d-1233-4022-ad18-871b3d8444c7
```

Cases:

```text
DVCF5A07C0AFFC9 -> H3C -> expect 12 generated records
DVC2C4468B0B813 -> Huawei -> expect 12 generated records
DVCF21C6B43350C -> Maipu -> expect 12 generated records
```

Expected records:

```text
oneops:if_in_rate:bps
oneops:if_out_rate:bps
oneops:if_oper_status
oneops:if_speed_bps
oneops:if_in_error_rate:pps
oneops:if_out_error_rate:pps
oneops:if_in_discard_rate:pps
oneops:if_out_discard_rate:pps
oneops:if_in_broadcast_ratio:ratio
oneops:if_out_broadcast_ratio:ratio
oneops:cpu_usage_direct:ratio
oneops:memory_usage_direct:ratio
```

The script should assert request body is exactly `{ target_part }`.

- [ ] **Step 2: Add package script**

```json
"smoke:snmp-strategy-set-recording-rule-preview-real-api": "node scripts/snmp-strategy-set-recording-rule-preview-real-api-acceptance.cjs"
```

- [ ] **Step 3: Run only when current backend is serving the new route**

```bash
cd /OneOPS/OneOps-UI
ONEOPS_API_BASE_URL=http://127.0.0.1:18082/api/v1 \
ONEOPS_API_TOKEN="$(cat /tmp/oneops-ui-real-page-token-18082.txt)" \
npm run smoke:snmp-strategy-set-recording-rule-preview-real-api
```

Expected: PASS for all three targets.

Do not mark this acceptance passed if the route returns 404 from an old backend binary.

---

### Task 8: Focused Verification And Handoff

**Files:**

- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [ ] **Step 1: Run focused backend tests**

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*RecordingRule|TestMetricCapabilityContractResolverPreviewsStrategySetRecordingRulesByTarget' -count=1
go test ./app/platform/api -run TestTeleabsAPI_PreviewStrategySetRecordingRulesByTarget -count=1
go test ./app/platform/router -run TestTeleabsRoutesConsistency -count=1
```

Expected: PASS.

- [ ] **Step 2: Run focused frontend smoke**

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-strategy-set-recording-rule-preview
```

Expected: PASS.

- [ ] **Step 3: Run seed sync checks**

```bash
cd /OneOPS/quick_env
bash tests/test_sync_snmp_network_strategy_seed.sh
bash tests/test_snmp_network_strategy_seed.sh
```

Expected: PASS.

- [ ] **Step 4: Run diff checks**

```bash
git -C /OneOPS/OneOps diff --check
git -C /OneOPS/OneOps-UI diff --check
git -C /OneOPS/quick_env diff --check
git -C /OneOPS/docs diff --check
```

Expected: no output.

- [ ] **Step 5: Update handoff**

Add:

- new endpoint;
- request/response shape;
- rule selection semantics;
- generated record list for H3C/Huawei/Maipu;
- explicit deferred items: publish lifecycle, Prometheus reload, Grafana dashboard JSON.

---

## Final Acceptance

The phase is complete only when these commands pass:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*RecordingRule|TestMetricCapabilityContractResolverPreviewsStrategySetRecordingRulesByTarget' -count=1
go test ./app/platform/api -run TestTeleabsAPI_PreviewStrategySetRecordingRulesByTarget -count=1
go test ./app/platform/router -run TestTeleabsRoutesConsistency -count=1

cd /OneOPS/OneOps-UI
npm run smoke:snmp-strategy-set-recording-rule-preview

cd /OneOPS/quick_env
bash tests/test_sync_snmp_network_strategy_seed.sh
bash tests/test_snmp_network_strategy_seed.sh

git -C /OneOPS/OneOps diff --check
git -C /OneOPS/OneOps-UI diff --check
git -C /OneOPS/quick_env diff --check
git -C /OneOPS/docs diff --check
```

Optional real API acceptance can run after the current backend binary is serving the new route:

```bash
cd /OneOPS/OneOps-UI
ONEOPS_API_BASE_URL=http://127.0.0.1:18082/api/v1 \
ONEOPS_API_TOKEN="$(cat /tmp/oneops-ui-real-page-token-18082.txt)" \
npm run smoke:snmp-strategy-set-recording-rule-preview-real-api
```
