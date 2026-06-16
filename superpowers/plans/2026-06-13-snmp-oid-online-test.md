# SNMP OID Online Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a real-target SNMP OID online test loop to the existing SNMP metric-group page so users can edit an OID, test it inline against a target device, fix failures, and then save the strategy without leaving the page.

**Architecture:** Keep this slice narrow and page-oriented. Add one dedicated backend by-target OID test endpoint instead of exposing `template-debug-v2` pipeline/node concepts in the SNMP strategy editor. On the frontend, add a small target input plus field-level and group-level test actions, store test state locally by `group_key + metric_key + target_part`, and surface results inline near each OID row.

**Tech Stack:** Go backend in `/OneOPS/OneOps`, Vue 3 + TypeScript frontend in `/OneOPS/OneOps-UI`, existing Teleabs platform HTTP patterns, SNMP metric-group editor components, smoke scripts under `/OneOPS/OneOps-UI/scripts`, and docs under `/OneOPS/docs/superpowers`.

## Implementation Status

This plan is now implemented.

Confirmed completion in the current workspace includes:

- backend by-target OID test API, DTOs, routing, and resolver coverage;
- frontend `target_part` input, field-level `测试`, group-level `测试本组待测项`, and inline test state;
- page-level smoke coverage for `target_part -> field test -> group test -> retarget invalidation`;
- `npm run typecheck` confirmed passing after fixing the OID-slice type regressions.

---

## Scope Lock

Allowed in this slice:

- add one dedicated strategy-scoped by-target OID test endpoint;
- support field-mode and group-mode OID tests;
- add `target_part` input to the SNMP metric-group page;
- add field-level `测试` and group-level `测试本组待测项` actions;
- add inline field status: `未测 / 测试中 / 通过 / 失败`;
- auto-focus the first failed field after a batch test;
- keep `保存策略` available while showing a short `待测试 N` style hint.

Not allowed in this slice:

- no reuse of the full `template-debug-v2` UX;
- no strategy-wide test-all-groups action;
- no OID auto-suggestion or auto-fix;
- no long-term test history;
- no recording-rule or Grafana auto-publish after test;
- no right-side large alert/dashboard for OID test results.

## File Structure

Backend expected to change:

- Modify: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs.go`
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform_bidi.go`
- Modify: `/OneOPS/OneOps/app/platform/router/teleabs_routes_consistency_test.go`
- Modify: `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

Frontend expected to change:

- Modify: `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- Modify: `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/PluginFormSnmp.vue`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/SnmpMetricGroupEditor.vue`
- Create: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpOidOnlineTestState.ts`
- Create: `/OneOPS/OneOps-UI/scripts/snmp-oid-online-test-state-smoke.ts`
- Create: `/OneOPS/OneOps-UI/scripts/snmp-oid-online-test-editor-smoke.ts`
- Modify: `/OneOPS/OneOps-UI/package.json`

Docs expected to change:

- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

## Canonical Decisions

These decisions are fixed for this plan:

- OID online test is executed against a real target resolved from `target_part`;
- the strategy page uses a dedicated endpoint and must not expose pipeline/node debug abstractions;
- request modes are only `field` and `group`;
- field-level test is the primary local action after OID edits;
- editing an OID resets that field to `untested`;
- changing `target_part` invalidates existing test results;
- save remains allowed even when untested fields exist.

## Task 1: Freeze The New Behavior With Failing Tests And Smokes

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- Create: `/OneOPS/OneOps-UI/scripts/snmp-oid-online-test-state-smoke.ts`
- Create: `/OneOPS/OneOps-UI/scripts/snmp-oid-online-test-editor-smoke.ts`
- Modify: `/OneOPS/OneOps-UI/package.json`

- [x] **Step 1: Add failing backend DTO/API tests for field-mode and group-mode OID test**

Add HTTP tests for:

- field-mode success request binding;
- missing `target_part` rejected;
- missing `oid` rejected for field mode;
- group-mode mixed success/failure response shape.

Target request examples:

```go
req := httptest.NewRequest(
	http.MethodPost,
	"/platform/metrics/teleabs/strategies/strategy-1/snmp-metric/oid-test/by-target",
	strings.NewReader(`{"target_part":"SW-1","group_key":"interface_basic","metric_key":"if_in_rate","oid":".1.3.6.1.2.1.31.1.1.1.6","mode":"field"}`),
)
```

```go
req := httptest.NewRequest(
	http.MethodPost,
	"/platform/metrics/teleabs/strategies/strategy-1/snmp-metric/oid-test/by-target",
	strings.NewReader(`{"target_part":"SW-1","group_key":"interface_basic","mode":"group","fields":[{"metric_key":"if_in_rate","oid":".1.3.6.1.2.1.31.1.1.1.6"}]}`),
)
```

- [x] **Step 2: Add failing resolver tests for result semantics**

Add resolver tests for:

- field-mode returns one `success` result with `value_kind`;
- field-mode returns one `failed` result when target cannot be resolved;
- group-mode returns per-field results without discarding sibling successes.

Target result shape:

```go
if resp.Results[0].MetricKey != "if_in_rate" || resp.Results[0].Status != "success" {
	t.Fatalf("expected success result for if_in_rate, got %#v", resp.Results)
}
```

- [x] **Step 3: Add failing frontend smoke for new state module**

Create `snmp-oid-online-test-state-smoke.ts` that asserts:

- field edit reset behavior maps to `untested`;
- field-mode request sends `target_part`, `group_key`, `metric_key`, `oid`, `mode: "field"`;
- group-mode request sends `fields[]` with `mode: "group"`;
- changing target clears previous result state.

Expected assertions:

```ts
assert.equal(state.fieldStates.value['interface_basic::if_in_rate::SW-1']?.status, 'success');
state.setTargetPart('SW-2');
assert.equal(Object.keys(state.fieldStates.value).length, 0);
```

- [x] **Step 4: Add failing frontend smoke for editor wiring**

Create `snmp-oid-online-test-editor-smoke.ts` that source-checks:

- `PluginFormSnmp.vue` contains target input binding;
- `SnmpMetricGroupEditor.vue` contains `测试` and `测试本组待测项`;
- editor renders field status and failure message hooks;
- package script exists.

Expected assertions:

```ts
assert.ok(editorSource.includes('测试本组待测项'));
assert.ok(editorSource.includes('fieldTestStatus'));
assert.ok(formSource.includes('targetPartForOidTest'));
```

- [x] **Step 5: Run the focused tests to verify RED**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/api -run 'TestTeleabsAPI_.*Snmp.*Oid.*Test' -count=1
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*Oid.*Test' -count=1
```

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-oid-online-test-state
npm run smoke:snmp-oid-online-test-editor
```

Expected: RED until the backend endpoint and frontend state/UI are implemented.

## Task 2: Implement Backend By-Target OID Test Endpoint

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform_bidi.go`
- Modify: `/OneOPS/OneOps/app/platform/router/teleabs_routes_consistency_test.go`
- Modify: `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [x] **Step 1: Add request/response DTOs**

In `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`, add:

```go
type SnmpOidOnlineTestFieldInput struct {
	MetricKey string `json:"metric_key"`
	OID       string `json:"oid"`
}

type SnmpOidOnlineTestByTargetRequest struct {
	TargetPart string                    `json:"target_part"`
	GroupKey   string                    `json:"group_key"`
	MetricKey  string                    `json:"metric_key,omitempty"`
	BaseOID    string                    `json:"base_oid,omitempty"`
	OID        string                    `json:"oid,omitempty"`
	Mode       string                    `json:"mode"`
	Fields     []SnmpOidOnlineTestFieldInput `json:"fields,omitempty"`
}

type SnmpOidOnlineTestResult struct {
	MetricKey   string `json:"metric_key"`
	Status      string `json:"status"`
	ValueKind   string `json:"value_kind"`
	SampleValue string `json:"sample_value,omitempty"`
	Message     string `json:"message,omitempty"`
	TestedAt    string `json:"tested_at"`
}

type SnmpOidOnlineTestByTargetResponse struct {
	StrategyID string                  `json:"strategy_id"`
	TargetPart string                  `json:"target_part"`
	GroupKey   string                  `json:"group_key"`
	Results    []SnmpOidOnlineTestResult `json:"results"`
}
```

- [x] **Step 2: Add resolver interface and failing implementation stub**

In `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`, add:

```go
ResolveStrategyOidOnlineTestByTarget(
	ctx context.Context,
	strategyID string,
	req dto.SnmpOidOnlineTestByTargetRequest,
) (*dto.SnmpOidOnlineTestByTargetResponse, error)
```

In the implementation file, add a minimal stub that validates request shape first.

- [x] **Step 3: Implement API handler and route**

In `teleabs.go`, add handler:

```go
func (a *TeleabsAPI) ResolveStrategyOidOnlineTestByTarget(ctx *gin.Context) {
	strategyID := strings.TrimSpace(ctx.Param("id"))
	var body dto.SnmpOidOnlineTestByTargetRequest
	if err := ctx.ShouldBindJSON(&body); err != nil {
		response.FailWithMessage("请求参数无效", ctx)
		return
	}
	// validate strategyID, target_part, mode, oid/fields
	// call resolver
}
```

Wire route in both router files under `/platform/metrics/teleabs/strategies/:id/...`.

- [x] **Step 4: Implement minimal real-target semantics**

Inside the resolver implementation:

- resolve `target_part` using the same target-context path already used in strategy-set by-target flows;
- reject empty or unresolved target;
- for `field` mode, produce exactly one result;
- for `group` mode, iterate through requested `fields`;
- return per-field results even when some fail;
- do not mutate strategy/config state.

Minimum behavior is acceptable for this slice if lower-level SNMP test internals are thin, but the response contract must be stable.

Representative loop:

```go
results := make([]dto.SnmpOidOnlineTestResult, 0, len(req.Fields))
for _, field := range req.Fields {
	result := dto.SnmpOidOnlineTestResult{
		MetricKey: field.MetricKey,
		Status:    "failed",
		ValueKind: "error",
		TestedAt:  time.Now().Format(time.RFC3339),
	}
	// resolve/test here
	results = append(results, result)
}
```

- [x] **Step 5: Run backend tests to verify GREEN**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/api -run 'TestTeleabsAPI_.*Snmp.*Oid.*Test' -count=1
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*Oid.*Test' -count=1
go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1
```

Expected: PASS.

- [x] **Step 6: Commit backend slice**

```bash
cd /OneOPS/OneOps
git add app/platform/dto/snmp_metric_contract.go \
  app/platform/api/teleabs.go \
  app/platform/api/teleabs_metric_contract_http_test.go \
  app/platform/router/platform.go \
  app/platform/router/platform_bidi.go \
  app/platform/router/teleabs_routes_consistency_test.go \
  app/platform/service/i_metric_capability_contract_resolver.go \
  app/platform/service/impl/metric_capability_contract_resolver.go \
  app/platform/service/impl/metric_capability_contract_resolver_test.go
git commit -m "feat: add snmp oid online test endpoint"
```

## Task 3: Add Frontend API Wrapper And Local OID Test State

**Files:**

- Modify: `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- Modify: `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`
- Create: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpOidOnlineTestState.ts`
- Create: `/OneOPS/OneOps-UI/scripts/snmp-oid-online-test-state-smoke.ts`
- Modify: `/OneOPS/OneOps-UI/package.json`

- [x] **Step 1: Add TS request/response types**

In `snmp-metric-contract.ts`, add:

```ts
export interface SnmpOidOnlineTestFieldInput {
  metric_key: string;
  oid: string;
}

export interface SnmpOidOnlineTestByTargetRequest {
  target_part: string;
  group_key: string;
  metric_key?: string;
  base_oid?: string;
  oid?: string;
  mode: 'field' | 'group';
  fields?: SnmpOidOnlineTestFieldInput[];
}

export interface SnmpOidOnlineTestResult {
  metric_key: string;
  status: 'success' | 'failed';
  value_kind: 'scalar' | 'table' | 'empty' | 'error';
  sample_value?: string;
  message?: string;
  tested_at: string;
}

export interface SnmpOidOnlineTestByTargetResponse {
  strategy_id: string;
  target_part: string;
  group_key: string;
  results: SnmpOidOnlineTestResult[];
}
```

- [x] **Step 2: Add frontend API wrapper**

In `src/api/platform/teleabs.ts`, add:

```ts
export const testTeleabsStrategySnmpOidByTarget = async (
  strategyId: string,
  data: SnmpOidOnlineTestByTargetRequest,
) => {
  return requestEnvelope<SnmpOidOnlineTestByTargetResponse>({
    url: `/platform/metrics/teleabs/strategies/${encodeURIComponent(strategyId)}/snmp-metric/oid-test/by-target`,
    method: HTTP_POST,
    data,
    silentSuccess: true,
    silentError: true,
  });
};
```

- [x] **Step 3: Build local state helper**

Create `snmpOidOnlineTestState.ts` with:

- `targetPart`
- `fieldStates`
- `setTargetPart()`
- `markFieldEdited()`
- `testField()`
- `testGroupUntested()`
- `untestedCountForGroup()`
- `firstFailedMetricKey`

State key shape:

```ts
const stateKey = `${groupKey}::${metricKey}::${targetPart}`;
```

Field state shape:

```ts
interface SnmpOidFieldTestState {
  status: 'untested' | 'testing' | 'success' | 'failed';
  message: string;
  valueKind?: string;
  sampleValue?: string;
  testedAt?: string;
}
```

- [x] **Step 4: Run smoke to verify GREEN**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-oid-online-test-state
```

Expected: PASS.

- [x] **Step 5: Commit frontend state slice**

```bash
cd /OneOPS/OneOps-UI
git add src/typings/platform/snmp-metric-contract.ts \
  src/api/platform/teleabs.ts \
  src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpOidOnlineTestState.ts \
  scripts/snmp-oid-online-test-state-smoke.ts \
  package.json
git commit -m "feat: add snmp oid online test state"
```

## Task 4: Wire The SNMP Editor UX And Verify End-To-End Page Behavior

**Files:**

- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/PluginFormSnmp.vue`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/SnmpMetricGroupEditor.vue`
- Create: `/OneOPS/OneOps-UI/scripts/snmp-oid-online-test-editor-smoke.ts`
- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [x] **Step 1: Add page-level target input to PluginFormSnmp**

Near the strategy context area, add:

```vue
<a-input
  v-model:value="targetPartForOidTest"
  placeholder="输入目标设备编码或 ID"
  allow-clear
/>
```

Expose `targetPartForOidTest` and pass it to the group editor.

- [x] **Step 2: Add field-level and group-level test controls to SnmpMetricGroupEditor**

Add in the header:

```vue
<a-button
  :disabled="!draft.fields.some(field => oidTestState.isUntested(draft.group_key, field.metric_key))"
  @click="testCurrentGroupUntested"
>
  测试本组待测项
</a-button>
```

Add in the OID cell:

```vue
<a-space>
  <a-input v-model:value="record.oid" size="small" :disabled="isDisabledGroup" @change="handleOidChange(record)" />
  <a-button size="small" :loading="fieldTestStatus(record.metric_key).status === 'testing'" @click="testSingleField(record)">
    测试
  </a-button>
</a-space>
```

Render inline status and message below/next to the row.

- [x] **Step 3: Reset state on OID edit and focus first failed field after batch**

When `oid` changes:

```ts
function handleOidChange(field: Record<string, any>) {
  oidTestState.markFieldEdited(draft.group_key, String(field.metric_key || ''));
  commitFieldEdit();
}
```

After group batch test:

```ts
await oidTestState.testGroupUntested(...);
await nextTick();
focusFirstFailedField();
```

Focus can be implemented with a simple `ref` map keyed by `metric_key`.

- [x] **Step 4: Add short page-level save hint**

In `PluginFormSnmp.vue`, expose a small summary such as:

```ts
const oidUntestedSummary = computed(() => {
  const count = oidTestState.untestedCountForContract(contract.value.metric_groups);
  return count > 0 ? `待测试 ${count}` : '';
});
```

Show it as a small note, not a blocking alert.

- [x] **Step 5: Run frontend smokes and diff hygiene**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-oid-online-test-state
npm run smoke:snmp-oid-online-test-editor
git diff --check
```

Expected: PASS.

- [x] **Step 6: Update handoff and commit UI slice**

Add a handoff note describing:

- dedicated by-target OID test endpoint exists;
- SNMP metric-group page now supports inline OID testing;
- save remains available with `待测试 N` hint.

Commit:

```bash
cd /OneOPS
git -C OneOps-UI add src/views/platform/StrategyTemplate/plugin-forms/PluginFormSnmp.vue \
  src/views/platform/StrategyTemplate/plugin-forms/snmp/SnmpMetricGroupEditor.vue \
  scripts/snmp-oid-online-test-editor-smoke.ts
git -C docs add docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md
git -C OneOps-UI commit -m "feat: add inline snmp oid online test ui"
```

## Final Verification

- [x] **Step 1: Run backend verification**

```bash
cd /OneOPS/OneOps
go test ./app/platform/api -run 'TestTeleabsAPI_.*Snmp.*Oid.*Test' -count=1
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*Oid.*Test' -count=1
go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1
```

- [x] **Step 2: Run frontend verification**

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-oid-online-test-state
npm run smoke:snmp-oid-online-test-editor
```

- [x] **Step 3: Run diff hygiene**

```bash
git -C /OneOPS/OneOps diff --check
git -C /OneOPS/OneOps-UI diff --check
git -C /OneOPS/docs diff --check
```

- [x] **Step 4: Record any unverified items honestly**

Historical note: during mid-implementation this step was left explicitly unverified while `npm run typecheck` was still timing out in the waiting window. That status was later resolved; the final OID slice now has `npm run typecheck` confirmed passing.
