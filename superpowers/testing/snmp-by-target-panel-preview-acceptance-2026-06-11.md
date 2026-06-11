# SNMP By-Target Panel Preview Real-Data Acceptance

This runbook validates the strict by-target data loop with real devices. It does not include Grafana, Prometheus recording rules, page-level UI consumption, fallback lookup, or broader metric standardization.

## Goal

Verify that a real device target can produce a trustworthy backend answer:

```text
strategy_set_id + target_part
  -> platform_devices_v2
  -> resolved target context
  -> matched strategy-set item contracts
  -> effective_contract
  -> base panel supports
  -> support_summary
```

## Required Samples

Prepare at least three samples before accepting the closure:

| Sample | Purpose | Expected Result |
| --- | --- | --- |
| H3C / Comware device | Validate normal vendor/platform/model/version matching | `supported` or intentional `partial` panels |
| Non-H3C device | Validate another vendor/platform path | matched item contracts are vendor-appropriate |
| Negative sample | Validate strict failure behavior | clear error for missing target/context/match |

For each sample, record:

```text
strategy_set_id:
target_part:
expected_catalog:
expected_manufacturer:
expected_platform:
expected_model:
expected_version:
expected_strategy_ids:
```

## Request

```bash
curl -sS -X POST \
  "$ONEOPS_BASE_URL/platform/metrics/teleabs/strategy-sets/$STRATEGY_SET_ID/metric-contract/panel-support/by-target" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ONEOPS_TOKEN" \
  -d '{"target_part":"'"$TARGET_PART"'"}'
```

The endpoint accepts only:

```json
{ "target_part": "DEVICE-CODE-OR-ID" }
```

Do not pass explicit context or requirements in this path.

## Acceptance Checks

### 1. Target Context

Check `data.target.context`:

```text
catalog_name
manufacturer_name
platform_name
device_model_name
system_version
```

Pass criteria:

- all required fields are present;
- values match the real device;
- `metadata_source` is `platform_devices_v2`;
- frontend did not infer or rewrite these values.

Fail criteria:

- missing required field;
- vendor/platform/model/version value is wrong;
- response succeeds for an invalid or missing target.

### 2. Strategy Matching

Check:

```text
data.item_contracts[]
```

Pass criteria:

- expected strategy IDs are selected;
- unrelated vendor/platform/model strategies are not selected;
- zero selected items is returned as an error, not an empty success.

Fail criteria:

- generic strategy hides a missing vendor strategy;
- wrong vendor strategy is selected;
- empty `item_contracts[]` is treated as success.

### 3. Effective Contract

Check:

```text
data.effective_contract.metric_groups[]
```

Pass criteria:

- common interface groups appear when supported by the selected strategy;
- CPU and Memory appear using one of the supported standards for that vendor;
- unsupported capabilities remain absent instead of being invented.

Base panel capability keys currently expected by the backend requirements:

```text
if_in_rate
if_out_rate
if_oper_status
if_speed_bps
if_in_error_rate
if_out_error_rate
if_in_discard_rate
if_out_discard_rate
if_in_broadcast_ratio
if_out_broadcast_ratio
cpu_usage_direct
cpu_usage_from_idle
memory_usage_direct
memory_usage_used_total
memory_usage_free_total
```

### 4. Panel Support Summary

Check:

```text
data.supports[]
data.support_summary
```

Expected panel keys:

```text
interface_basic.traffic
interface_basic.status
interface_basic.speed
interface_basic.quality
interface_basic.broadcast
system_basic.cpu
system_basic.memory
```

State meaning:

| State | Meaning |
| --- | --- |
| `supported` | required or acceptable capability is present |
| `partial` | some required capabilities are present, but some are missing |
| `unsupported` | no usable standard capability is present |
| `config_driven` | standard capability is absent, but config-driven query is explicitly allowed |

Pass criteria:

- `support_summary.total` is `7`;
- each panel state matches the actual selected contract;
- `partial` is used for incomplete required capability sets;
- `unsupported` is used when no approved capability exists.

## Negative Tests

Run these deliberately:

| Case | Request | Expected |
| --- | --- | --- |
| Empty target | `{"target_part":""}` | error containing `target_part is required` |
| Missing device | unknown target | error containing `target device not found` |
| Incomplete metadata | target missing required context | error containing missing field names |
| No matched strategy | valid target with no matching item | error containing `no matched metric contract items` |

## Acceptance Record Template

```text
sample_name:
strategy_set_id:
target_part:

target_context:
  catalog_name:
  manufacturer_name:
  platform_name:
  device_model_name:
  system_version:

matched_strategy_ids:

support_summary:
  total:
  supported:
  partial:
  unsupported:
  config_driven:

panel_states:
  interface_basic.traffic:
  interface_basic.status:
  interface_basic.speed:
  interface_basic.quality:
  interface_basic.broadcast:
  system_basic.cpu:
  system_basic.memory:

decision: pass / fail
notes:
```

## 2026-06-11 Local Candidate Discovery

Local read-only discovery found usable candidate data in the demo MySQL container.

Counts:

```text
platform_devices_v2: 51
platform_teleabs_strategy_set: 9
platform_teleabs_strategy_set_item: 14
platform_teleabs_strategy: 40
```

Primary strategy-set candidate:

```text
strategy_set_id: 4284353d-1233-4022-ad18-871b3d8444c7
name: 网络监控套件
mode: strategy_selector
enabled: true
catalogs: CATL20231020001, CATL20231020002, CATL20231020004, CATL20231020010
```

Candidate target samples:

```text
H3C / Comware:
  target_part: DVCF5A07C0AFFC9
  catalog_name: SWITCH
  manufacturer_name: H3C
  platform_name: Comware
  device_model_name: S6900-54QF-F
  system_version: 7.1.070 Release 2910

H3C / Comware:
  target_part: DVC7F2EED8EC1E0
  catalog_name: SWITCH
  manufacturer_name: H3C
  platform_name: Comware
  device_model_name: S6520X-54QC-EI
  system_version: 7.1.070 Release 6326

Huawei / VRP:
  target_part: DVC2C4468B0B813
  catalog_name: SWITCH
  manufacturer_name: huawei / HuaWei
  platform_name: VRP
  device_model_name: CE6855HI
  system_version: Version 8.180 V200R005C10SPC800

Maipu / MyPower:
  target_part: DVCF21C6B43350C
  catalog_name: SWITCH
  manufacturer_name: Maipu
  platform_name: MyPower
  device_model_name: S4320
  system_version: 9.5.0.3
```

Strategy candidates observed for these samples include:

```text
10000000-0000-4000-8000-000000000001  H3C网络设备监控 (副本)        H3C / Comware
20000000-0000-4000-8000-000000000001  华为网络设备监控 (副本)       Huawei / VRP
50000000-0000-4000-8000-000000000001  迈普通用SNMP网络监控策略      Maipu / MyPower
```

Current execution blocker:

```text
The running local :8080 OneOps process returns 404 for the new by-target route,
which indicates it is not the freshly built binary that contains the endpoint.
Do not record acceptance as passed until the updated backend process is running
and the endpoint response is captured.
```

## 2026-06-11 Direct Resolver Acceptance Result

Because the local `:8080` process was not serving the new route, a direct backend resolver acceptance was run against the same demo MySQL data.

Execution path:

```text
real MySQL
  -> TeleabsStrategySrv
  -> TeleabsStrategySetSrv
  -> MetricCapabilityContractResolver.ResolveStrategySetTargetPanelCapabilityPreview(...)
```

This validates the core data logic, but it is not yet HTTP endpoint acceptance.

### Positive / Partial Samples

```text
sample: H3C / Comware / S6900-54QF-F
target_part: DVCF5A07C0AFFC9
matched_strategy_ids:
  10000000-0000-4000-8000-000000000001
support_summary:
  total: 7
  supported: 0
  partial: 0
  unsupported: 6
  config_driven: 1
panel_states:
  interface_basic.traffic: unsupported
  interface_basic.status: unsupported
  interface_basic.speed: config_driven
  interface_basic.quality: unsupported
  interface_basic.broadcast: unsupported
  system_basic.cpu: unsupported
  system_basic.memory: unsupported
decision: partial / data needs improvement
notes: strategy matching works, but the selected H3C strategy only contains CPU and Memory raw fields in passthrough_config and does not expose enough base capability contract fields.
```

```text
sample: H3C / Comware / S6520X-54QC-EI
target_part: DVC7F2EED8EC1E0
matched_strategy_ids:
  10000000-0000-4000-8000-000000000001
support_summary:
  total: 7
  supported: 0
  partial: 0
  unsupported: 6
  config_driven: 1
panel_states:
  interface_basic.traffic: unsupported
  interface_basic.status: unsupported
  interface_basic.speed: config_driven
  interface_basic.quality: unsupported
  interface_basic.broadcast: unsupported
  system_basic.cpu: unsupported
  system_basic.memory: unsupported
decision: partial / data needs improvement
notes: same behavior as the first H3C sample.
```

```text
sample: Maipu / MyPower / S4320
target_part: DVCF21C6B43350C
matched_strategy_ids:
  50000000-0000-4000-8000-000000000001
support_summary:
  total: 7
  supported: 4
  partial: 0
  unsupported: 3
  config_driven: 0
panel_states:
  interface_basic.traffic: supported
  interface_basic.status: supported
  interface_basic.speed: supported
  interface_basic.quality: supported
  interface_basic.broadcast: unsupported
  system_basic.cpu: unsupported
  system_basic.memory: unsupported
decision: partial pass
notes: strategy matching works and interface basics are mostly covered. CPU and Memory are still unsupported by the current capability mapping, even though the raw strategy has cpu_usage and memory fields.
```

### Negative Samples

```text
sample: Huawei / VRP / CE6855HI
target_part: DVC2C4468B0B813
resolved_context:
  manufacturer_name: huawei
  platform_name: HuaWei
  device_model_name: CE6855HI
  system_version: Version 8.180 V200R005C10SPC800
result: error
error: strategy set has no matched metric contract items for target: DVC2C4468B0B813
decision: expected strict failure, but data normalization needs review
notes: strategy candidates expect Huawei / VRP, while the resolved target context produced platform_name=HuaWei from Device V2 metadata merge order.
```

```text
sample: empty target
target_part:
result: error
error: target_part is required
decision: pass
```

```text
sample: missing target
target_part: DVC-NOT-EXIST
result: error
error: target device not found: DVC-NOT-EXIST
decision: pass
```

### Findings

The strict by-target data logic is operational at resolver level:

- target context can be resolved from `platform_devices_v2`;
- H3C and Maipu samples select the expected vendor/platform strategies;
- missing target and no-match cases return strict errors;
- `support_summary.total` is `7` when a strategy is matched.

The real data is not yet good enough to proceed to page-level consumption:

- H3C strategies match but do not expose the expected base interface capabilities;
- Maipu exposes interface basics but not CPU/Memory standard capabilities;
- Huawei target metadata resolves `platform_name` as `HuaWei` instead of `VRP`, causing no matched strategy item;
- direct resolver acceptance passed only as a core-logic check, not as HTTP endpoint acceptance.

## 2026-06-11 Direct Resolver Re-Acceptance After Data-Logic Fixes

Two data-logic fixes were applied and re-tested at resolver level:

```text
1. Device V2 metadata semantics:
   metadata_json now overrides attributes_json for non-empty semantic fields.

2. Direct system usage fields:
   cpu_usage and memory_usage are now mapped to:
     cpu_usage_direct
     memory_usage_direct
```

Re-acceptance result:

```text
sample: H3C / Comware / S6900-54QF-F
target_part: DVCF5A07C0AFFC9
matched_strategy_ids:
  10000000-0000-4000-8000-000000000001
support_summary:
  total: 7
  supported: 2
  partial: 0
  unsupported: 4
  config_driven: 1
panel_states:
  interface_basic.traffic: unsupported
  interface_basic.status: unsupported
  interface_basic.speed: config_driven
  interface_basic.quality: unsupported
  interface_basic.broadcast: unsupported
  system_basic.cpu: supported
  system_basic.memory: supported
decision: partial pass
notes: CPU/Memory are now standard supported. Interface basics remain unsupported because the selected H3C strategy does not include interface table fields.
```

```text
sample: H3C / Comware / S6520X-54QC-EI
target_part: DVC7F2EED8EC1E0
matched_strategy_ids:
  10000000-0000-4000-8000-000000000001
support_summary:
  total: 7
  supported: 2
  partial: 0
  unsupported: 4
  config_driven: 1
panel_states:
  interface_basic.traffic: unsupported
  interface_basic.status: unsupported
  interface_basic.speed: config_driven
  interface_basic.quality: unsupported
  interface_basic.broadcast: unsupported
  system_basic.cpu: supported
  system_basic.memory: supported
decision: partial pass
notes: same behavior as the first H3C sample.
```

```text
sample: Huawei / VRP / CE6855HI
target_part: DVC2C4468B0B813
resolved_context:
  manufacturer_name: huawei
  platform_name: VRP
  device_model_name: CE6855HI
  system_version: Version 8.180 V200R005C10SPC800
matched_strategy_ids:
  20000000-0000-4000-8000-000000000001
support_summary:
  total: 7
  supported: 2
  partial: 0
  unsupported: 4
  config_driven: 1
panel_states:
  interface_basic.traffic: unsupported
  interface_basic.status: unsupported
  interface_basic.speed: config_driven
  interface_basic.quality: unsupported
  interface_basic.broadcast: unsupported
  system_basic.cpu: supported
  system_basic.memory: supported
decision: partial pass
notes: target metadata normalization now allows Huawei / VRP strategy matching.
```

```text
sample: Maipu / MyPower / S4320
target_part: DVCF21C6B43350C
matched_strategy_ids:
  50000000-0000-4000-8000-000000000001
support_summary:
  total: 7
  supported: 6
  partial: 0
  unsupported: 1
  config_driven: 0
panel_states:
  interface_basic.traffic: supported
  interface_basic.status: supported
  interface_basic.speed: supported
  interface_basic.quality: supported
  interface_basic.broadcast: unsupported
  system_basic.cpu: supported
  system_basic.memory: supported
decision: pass for current base scope except broadcast
notes: broadcast remains unsupported because the selected strategy does not expose the required broadcast capability inputs.
```

Strict negative checks are unchanged:

```text
empty target -> target_part is required
missing target -> target device not found
```

Updated conclusion:

- resolver-level by-target data logic is working against real demo data;
- Huawei matching is fixed by metadata precedence;
- direct CPU/Memory usage is fixed for snake_case fields;
- H3C still lacks interface table capabilities in the selected strategy data;
- broadcast remains unsupported where raw strategy data lacks broadcast inputs;
- HTTP endpoint acceptance is still blocked by the running old process / full app startup dependencies.

## 2026-06-11 API Handler HTTP Contract Check

A focused Gin `httptest` check was added for the by-target endpoint:

```text
POST /platform/metrics/teleabs/strategy-sets/:id/metric-contract/panel-support/by-target
```

Verified behavior:

```text
success request:
  route id: set-1
  body target_part: SW-1
  handler calls ResolveStrategySetTargetPanelCapabilityPreview(set-1, SW-1)
  response envelope code: 0
  response includes target.context and support_summary

strict empty-target request:
  body: {}
  handler still delegates to the strict resolver
  resolver error: target_part is required
  response envelope code: -1
```

Verification command:

```text
go test ./app/platform/api -run 'TestTeleabsAPI_PreviewStrategySetPanelCapabilitySupportByTarget_HTTP' -count=1
```

Result:

```text
ok github.com/netxops/OneOps/app/platform/api
```

Boundary:

- this closes the API handler/route contract in test;
- resolver-level real-data acceptance is already covered above;
- externally reachable process-level HTTP acceptance is still not claimed, because full app startup is blocked by unrelated runtime dependencies.

## 2026-06-11 Minimal HTTP Process Acceptance

To separate the endpoint from unrelated full-application boot dependencies, a temporary minimal HTTP process was started with only:

```text
Gin route
  -> TeleabsAPI.PreviewTeleabsStrategySetPanelCapabilitySupportByTarget
  -> MetricCapabilityContractResolver
  -> demo MySQL
```

The route under test was the same product endpoint path:

```text
POST /platform/metrics/teleabs/strategy-sets/:id/metric-contract/panel-support/by-target
```

Success samples:

```text
DVCF5A07C0AFFC9
  matched_strategy_ids:
    10000000-0000-4000-8000-000000000001
  support_summary:
    total=7 supported=2 partial=0 unsupported=4 config_driven=1
  panel_states:
    interface_basic.traffic: unsupported
    interface_basic.status: unsupported
    interface_basic.speed: config_driven
    interface_basic.quality: unsupported
    interface_basic.broadcast: unsupported
    system_basic.cpu: supported
    system_basic.memory: supported

DVC2C4468B0B813
  matched_strategy_ids:
    20000000-0000-4000-8000-000000000001
  support_summary:
    total=7 supported=2 partial=0 unsupported=4 config_driven=1
  panel_states:
    interface_basic.traffic: unsupported
    interface_basic.status: unsupported
    interface_basic.speed: config_driven
    interface_basic.quality: unsupported
    interface_basic.broadcast: unsupported
    system_basic.cpu: supported
    system_basic.memory: supported

DVCF21C6B43350C
  matched_strategy_ids:
    50000000-0000-4000-8000-000000000001
  support_summary:
    total=7 supported=6 partial=0 unsupported=1 config_driven=0
  panel_states:
    interface_basic.traffic: supported
    interface_basic.status: supported
    interface_basic.speed: supported
    interface_basic.quality: supported
    interface_basic.broadcast: unsupported
    system_basic.cpu: supported
    system_basic.memory: supported
```

Strict negative samples:

```text
{} -> code=-1, msg="target_part is required"
{"target_part":"DVC-NOT-EXIST"} -> code=-1, msg="target device not found: DVC-NOT-EXIST"
```

Current conclusion:

- endpoint path, handler binding, resolver call, real MySQL lookup, strategy-set matching, contract generation, and support summary work through a real HTTP process;
- this is not a full OneOps application startup acceptance;
- full app acceptance remains blocked by unrelated Redis/MinIO/Mongo/BootInit startup dependencies.

## 2026-06-11 Product Router Registration Check

The by-target route is also covered at product router definition level.

Added test:

```text
app/platform/router/teleabs_routes_consistency_test.go
```

Verified:

```text
platform.go and platform_bidi.go expose the same Teleabs route set;
the required by-target route exists in both router definitions:

POST strategy-sets/:id/metric-contract/panel-support/by-target
```

Verification command:

```text
go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1
```

Result:

```text
ok github.com/netxops/OneOps/app/platform/router
```

## 2026-06-11 Full OneOps Application Acceptance

The current OneOps backend code was started as a full application process with a temporary full config copied from the Nacos backup and only the HTTP port changed to avoid the existing `8080` process.

Important runtime facts:

```text
startup config:
  /tmp/oneops-full-app-acceptance.yaml

HTTP port:
  18082

actual product path:
  /api/v1/platform/metrics/teleabs/strategy-sets/:id/metric-contract/panel-support/by-target

auth:
  X-Auth-Token is required for private routes.
```

Startup result:

```text
Redis connected
MongoDB connected
BootInit completed
HTTP server started on 18082
```

Observed non-blocking startup note:

```text
OneOps listener on :7070 reported address already in use,
but this did not block the main HTTP server or this endpoint acceptance.
```

Successful full-application HTTP samples:

```text
DVCF5A07C0AFFC9
  manufacturer/platform: H3C / Comware
  matched_strategy_ids:
    10000000-0000-4000-8000-000000000001
  support_summary:
    total=7 supported=2 partial=0 unsupported=4 config_driven=1
  panel_states:
    interface_basic.traffic: unsupported
    interface_basic.status: unsupported
    interface_basic.speed: config_driven
    interface_basic.quality: unsupported
    interface_basic.broadcast: unsupported
    system_basic.cpu: supported
    system_basic.memory: supported

DVC2C4468B0B813
  manufacturer/platform: huawei / VRP
  matched_strategy_ids:
    20000000-0000-4000-8000-000000000001
  support_summary:
    total=7 supported=2 partial=0 unsupported=4 config_driven=1
  panel_states:
    interface_basic.traffic: unsupported
    interface_basic.status: unsupported
    interface_basic.speed: config_driven
    interface_basic.quality: unsupported
    interface_basic.broadcast: unsupported
    system_basic.cpu: supported
    system_basic.memory: supported

DVCF21C6B43350C
  manufacturer/platform: Maipu / MyPower
  matched_strategy_ids:
    50000000-0000-4000-8000-000000000001
  support_summary:
    total=7 supported=6 partial=0 unsupported=1 config_driven=0
  panel_states:
    interface_basic.traffic: supported
    interface_basic.status: supported
    interface_basic.speed: supported
    interface_basic.quality: supported
    interface_basic.broadcast: unsupported
    system_basic.cpu: supported
    system_basic.memory: supported
```

Strict negative samples:

```text
{} -> code=-1, msg="target_part is required"
{"target_part":"DVC-NOT-EXIST"} -> code=-1, msg="target device not found: DVC-NOT-EXIST"
```

Updated conclusion:

- full OneOps application startup-level HTTP acceptance is now complete for the by-target data path;
- the actual full-app request path includes `/api/v1/`;
- authentication is required on the full product route;
- the previous 404 came from using the bare platform path against the full app;
- Grafana behavior was not included in this acceptance.

## 2026-06-11 Frontend Page-Level Consumption Smoke

The first frontend page-level consumer is the strategy-set detail drawer.

Files:

```text
/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/StrategySetDetailDrawer.vue
/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/snmpStrategySetTargetPanelPreview.ts
/OneOPS/OneOps-UI/scripts/snmp-strategy-set-target-panel-preview-smoke.ts
/OneOPS/OneOps-UI/scripts/snmp-strategy-set-target-panel-preview-browser-smoke.cjs
```

The smoke verifies the page state helper behavior:

```text
strategy_set_id + target_part
  -> trim user input
  -> call previewTeleabsStrategySetPanelCapabilitySupportByTarget(...)
  -> expose target context
  -> expose support_summary as summary items
  -> expose supports[] as panel rows
  -> reset preview state when requested
  -> reject empty target input before calling backend
```

Verification:

```text
npm run smoke:snmp-strategy-set-target-panel-preview
npm run smoke:snmp-strategy-set-target-panel-preview-browser
```

The browser smoke mounts the drawer through the running Vite dev server, intercepts the by-target backend request, submits a target device code, verifies the target context and panel rows render, and checks that the drawer remains inside both desktop and narrow mobile viewports.

It also verifies the frontend request boundary:

- empty input does not call the by-target backend;
- valid input calls the backend exactly once;
- the sent request body is exactly `{ "target_part": "DVCF21C6B43350C" }` after trimming;
- no frontend manufacturer/platform/model/catalog/version context is sent.

It verifies strict backend error display:

- when the by-target backend returns `code=-1` with `msg="target device not found: DVC-NOT-EXIST"`, the drawer alert shows that backend message;
- the by-target frontend API wrapper uses the response envelope for this endpoint so strict backend errors are not collapsed into a generic failure.

Responsive acceptance note:

```text
StrategySetDetailDrawer width = min(860px, 100vw)
```

This keeps the right-side drawer visible on a 390px mobile viewport without changing the data contract.

Frontend boundary:

- the drawer sends only `strategy_set_id` and `target_part`;
- the drawer does not infer manufacturer, platform, model, catalog, version, or strategy matches;
- the drawer does not generate Grafana dashboard JSON;
- the drawer does not generate Prometheus recording rules.

## 2026-06-11 Real Frontend Page Acceptance Against Current Backend

The first real page-level acceptance was run with the current OneOps backend code, not the already-running local `:8080` process.

Environment:

```text
backend:
  current OneOps working tree
  /tmp/oneops-full-app-acceptance.yaml
  http://127.0.0.1:18082

frontend:
  VITE_PROXY_TARGET=http://127.0.0.1:18082
  http://localhost:5174

script:
  /OneOPS/OneOps-UI/scripts/snmp-strategy-set-target-panel-preview-real-page-acceptance.cjs
```

Command shape:

```text
ONEOPS_UI_REAL_BASE_URL=http://localhost:5174 \
ONEOPS_UI_REAL_TOKEN=<login token> \
npm run smoke:snmp-strategy-set-target-panel-preview-real-page
```

The script does not intercept `/api/v1`. It mounts `StrategySetDetailDrawer`, stores the supplied product token in local storage, submits target device codes, waits for the real by-target backend response, and verifies that the drawer displays the same context, matched strategy, support summary, and panel states.

Accepted results:

```text
DVCF5A07C0AFFC9
  context: H3C / Comware / S6900-54QF-F
  matched_strategy_id: 10000000-0000-4000-8000-000000000001
  support_summary: total=7 supported=2 partial=0 unsupported=4 config_driven=1
  panel_states:
    interface_basic.traffic: unsupported
    interface_basic.status: unsupported
    interface_basic.speed: config_driven
    interface_basic.quality: unsupported
    interface_basic.broadcast: unsupported
    system_basic.cpu: supported
    system_basic.memory: supported

DVC2C4468B0B813
  context: huawei / VRP / CE6855HI
  matched_strategy_id: 20000000-0000-4000-8000-000000000001
  support_summary: total=7 supported=2 partial=0 unsupported=4 config_driven=1
  panel_states:
    interface_basic.traffic: unsupported
    interface_basic.status: unsupported
    interface_basic.speed: config_driven
    interface_basic.quality: unsupported
    interface_basic.broadcast: unsupported
    system_basic.cpu: supported
    system_basic.memory: supported

DVCF21C6B43350C
  context: Maipu / MyPower / S4320
  matched_strategy_id: 50000000-0000-4000-8000-000000000001
  support_summary: total=7 supported=6 partial=0 unsupported=1 config_driven=0
  panel_states:
    interface_basic.traffic: supported
    interface_basic.status: supported
    interface_basic.speed: supported
    interface_basic.quality: supported
    interface_basic.broadcast: unsupported
    system_basic.cpu: supported
    system_basic.memory: supported
```

Environment note:

- the existing `:8080` process was observed to return older by-target behavior;
- default `5173 -> 8080` should not be used as current-code page acceptance evidence unless that backend process is restarted;
- current-code page acceptance evidence for this run is `5174 -> 18082`.

## Stop Conditions

Stop before further page-level UI expansion if any of these are true:

- required context is often missing in `platform_devices_v2`;
- strategy-set item matching selects unexpected vendor/platform strategies;
- CPU or Memory support states do not match the actual vendor data model;
- error/discard/broadcast support differs from the selected strategy contract;
- operators cannot explain why a panel is `partial` or `unsupported`.
