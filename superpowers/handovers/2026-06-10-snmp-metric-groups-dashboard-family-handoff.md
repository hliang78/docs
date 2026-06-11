# SNMP Metric Groups Dashboard Family Handoff

Date: 2026-06-11

## Current Objective

Continue the SNMP metric groups work as a semantic strategy editor, not as a generic SNMP raw-parameter editor.

The intended long path is still:

```text
StrategySet
  -> DashboardFamily
    -> DashboardVariant
      -> PanelSpec
        -> MetricGroup
          -> Strategy
            -> Metric / MetricAsset
```

The current phase still does **not** generate Grafana JSON. It must, however, make strategy-side data correct enough that a future phase can:

- generate dashboard variants,
- diff and update panels,
- trace `panel -> metric group -> strategy -> metric asset`,
- avoid reverse-parsing low-level SNMP raw config.

Primary docs:

- `/OneOPS/docs/superpowers/specs/2026-06-10-snmp-metric-groups-dashboard-family-design.md`
- `/OneOPS/docs/superpowers/plans/2026-06-10-snmp-metric-groups-dashboard-family.md`
- `/OneOPS/docs/superpowers/plans/2026-06-11-snmp-metric-capability-contract-strict-plan.md`

Frontend repo:

- `/OneOPS/OneOps-UI`

## User Direction That Must Stay Fixed

These constraints were clarified repeatedly by the user and should be treated as stable:

- Entry must come from `策略列表` on an existing SNMP strategy row.
- The page edits that strategy; it is not a standalone create surface.
- The real problem is data logic correctness, not more UI chrome.
- SNMP metric groups are meant to become:
  - a visual editor for SNMP strategy semantics,
  - and a future editor/input layer for Grafana panel contracts.
- We should not keep adding UI if the underlying data model is still conceptually wrong.

## Current Working Tree

Inside `/OneOPS/OneOps-UI`, there are uncommitted frontend changes in at least:

```text
package.json
scripts/snmp-metric-contract-smoke.ts
scripts/snmp-workspace-view-smoke.ts
src/views/platform/StrategyTemplate/TeleabsStrategyTab.vue
src/views/platform/StrategyTemplate/index.vue
src/views/platform/StrategyTemplate/plugin-forms/PluginFormSnmp.vue
src/views/platform/StrategyTemplate/plugin-forms/snmp/SnmpMetricGroupEditor.vue
src/views/platform/StrategyTemplate/plugin-forms/snmp/SnmpMetricGroupList.vue
src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricContract.ts
src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpWorkspaceView.ts
```

Do not revert unrelated user changes.

## What Has Already Been Implemented

### 1. Correct SNMP Entry Model

- SNMP strategy rows expose `指标分组` from the strategy list.
- The old standalone entry button was removed.
- The SNMP tab now expects a selected existing strategy row.

Key files:

- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/TeleabsStrategyTab.vue`
- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/index.vue`

### 2. Real Strategy Context Loading

The SNMP workspace now loads:

- selected strategy detail,
- parent strategy detail,
- manufacturer/platform/model/catalog context,
- template schema,
- current parameters for update instead of create.

Saving updates the selected strategy via `updateTeleabsStrategy`.

### 3. Parent/Child Effective Contract View

The page now computes:

```text
contract = current strategy contract or imported contract
parentContract = parent strategy contract or imported contract
effectiveContract = resolveEffectiveSnmpContract(parentContract, contract)
```

This part is important because it corrected one earlier page bug: child strategy pages must display **effective inherited groups**, not just the child diff.

### 4. Parent Warning Suppression For Inherited Child Pages

We removed the conceptually wrong inline warning that said a child page had a parent legacy inconsistency when the "missing" metrics were actually inherited.

Current behavior:

- root strategy pages may still surface raw legacy inconsistency,
- inherited child pages do not treat inherited raw gaps as local page errors.

### 5. Base Table OID Is Now Visible

One concrete UI gap was fixed:

- `group.source.base_oid` was already parsed,
- but was only used to enable the "加载 MIB 字段" button,
- and was not shown in the editor.

Now the editor displays `表 OID：...` directly.

### 6. Manifest-Only Metrics Are Now Backfilled Into Imported Groups

Another concrete visibility gap was fixed:

- if `metric_manifest` declared SNMP metrics that were not explicitly present as table fields in raw `passthrough_config`,
- they now still appear in the imported `fields` and default `panel_specs`.

This made the page "look more complete", but it did **not** solve the deeper semantic model issue described below.

### 7. First Metric Capability Contract Foundation Is Implemented

The first data-model pass now exists in the frontend contract resolver and has a backend authority entry point for strategy-level SNMP contracts.

Implemented scope:

- complete `snmp_interface` raw tables can import as `interface_basic`,
- `ifDescr / ifName / ifAlias` can become `if_name`,
- `ifHCInOctets / ifInOctets` can become `if_in_rate`,
- `ifHCOutOctets / ifOutOctets` can become `if_out_rate`,
- `ifOperStatus` can become `if_oper_status`,
- `ifSpeed` can become `if_speed_bps`,
- `ifInErrors` can become `if_in_error_rate`,
- `ifOutErrors` can become `if_out_error_rate`,
- `ifInDiscards` can become `if_in_discard_rate`,
- `ifOutDiscards` can become `if_out_discard_rate`,
- `ifInNUcastPkts + ifInUcastPkts + ifInOctets + ifSpeed` can become `if_in_broadcast_ratio`,
- `ifOutNUcastPkts + ifOutUcastPkts + ifOutOctets + ifSpeed` can become `if_out_broadcast_ratio`,
- real Telegraf-style `ifInOctets / ifOutOctets` interface metrics are covered, not only `ifHC*`,
- extra unstandardized fields in a standardized table remain `config_driven` instead of being dropped,
- top-level `cpuUsage` can become `cpu_usage_direct`,
- top-level `cpuIdle` can become `cpu_usage_from_idle`,
- top-level `memUsage` can become `memory_usage_direct`,
- top-level `memUsed + memTotal` can become `memory_usage_used_total`,
- top-level `memFree + memTotal` can become `memory_usage_free_total`,
- unknown top-level or table metrics remain `config_driven`,
- profile seeds now use `system_basic` capability naming instead of generic `system_health.cpu_usage / memory_usage`,
- a pure data resolver can evaluate panel capability support as `supported / partial / unsupported / config_driven`.

The contract fields can now carry:

- `concept_key`,
- `capability_key`,
- `raw_source`,
- `transform_rule`,
- `recording_rule`,
- `recordability`,
- `config_driven`.

Important limitation:

- `recording_rule` is metadata only.
- No Prometheus recording rule file is generated.
- No Prometheus reload/publish flow exists.
- No Grafana JSON is generated.
- No new UI has been added for these fields yet.
- Legacy SNMP process YAML such as `snmpIftableProcess` is not parsed by this resolver yet; the current resolver works from `passthrough_config`, `metric_manifest`, and explicit `metric_groups`.
- Existing Grafana panels still contain raw PromQL references such as `snmp_interface_ifInOctets`; this phase only validates the capability model that future Grafana work should consume.

### 8. Backend / Frontend Data Logic Closure Has Started

The backend now exposes a strategy-level SNMP metric contract resolver:

```text
GET /platform/metrics/teleabs/strategies/:id/metric-contract
GET /platform/metrics/teleabs/strategy-sets/:id/metric-contract
```

Current response shape:

```text
strategy_id
parent_strategy_id
source = backend_resolver
contract
parent_contract
effective_contract
```

Strategy-set response shape:

```text
strategy_set_id
source = backend_resolver
item_contracts[]
effective_contract
```

Strategy-set endpoint supports optional context query parameters:

```text
function_area
catalog_id
catalog_name
manufacturer_name
platform_name
device_model_name
system_version
```

Backend implementation files:

```text
/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go
/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go
/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go
/OneOPS/OneOps/app/platform/api/teleabs.go
```

Frontend implementation:

```text
/OneOPS/OneOps-UI/src/api/platform/teleabs.ts
/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/index.vue
```

Frontend behavior:

- when opening SNMP metric groups from a strategy row, the page requests the backend contract;
- if backend returns `contract.metric_groups`, those groups are injected into the existing `parameters.metric_groups` path;
- if backend returns `parent_contract.metric_groups`, parent parameters are injected the same way;
- if backend resolution fails, the existing local frontend resolver remains the fallback.
- frontend also has a typed API wrapper for strategy-set contract resolution, but no page consumes or displays it yet.

This creates a backend/frontend data logic loop without adding UI, Prometheus publishing, or Grafana JSON generation.

Strategy-set resolver behavior:

- resolves enabled strategy-set items only;
- item with `strategy_id` reuses the strategy-level resolver;
- item without `strategy_id` can parse `default_params`;
- aggregate `effective_contract` merges non-empty item contracts in `sort_order` order;
- when no context query is provided, the endpoint keeps the enabled-item aggregate behavior;
- when context query is provided, it reuses `StrategySetMatcher` semantics to select matching strategies by catalog, manufacturer, platform, model, version, fallback, priority, and sort order;
- no automatic device inventory lookup is performed yet; the caller must pass context values explicitly.

### 9. Strategy-Set Panel Capability Preview Is Now Data-Closed

The backend now exposes panel capability support as a data-layer answer, still without Grafana JSON generation.

Additional backend endpoints:

```text
GET  /platform/metrics/teleabs/metric-contract/panel-requirements/default
POST /platform/metrics/teleabs/metric-contract/panel-support
POST /platform/metrics/teleabs/strategy-sets/:id/metric-contract/panel-support
```

The default requirements endpoint returns the base common SNMP panel requirement catalog:

```text
interface_basic.traffic
interface_basic.status
interface_basic.speed
interface_basic.quality
interface_basic.broadcast
system_basic.cpu
system_basic.memory
```

The strategy-set panel preview endpoint now performs the full current data loop:

```text
strategy_set_id + optional context
  -> ResolveStrategySetContractWithOptions
  -> effective_contract
  -> default or caller-provided panel requirements
  -> supports[]
  -> support_summary
```

Request behavior:

- if `requirements` is omitted or empty, backend uses the default base panel requirement catalog;
- if `requirements` is provided, backend uses the caller-provided requirements;
- `context` is explicit and optional; there is still no automatic device inventory lookup.

Response shape:

```text
strategy_set_id
source
item_contracts[]
effective_contract
supports[]
support_summary
```

`supports[]` entries use:

```text
panel_key
state = supported | partial | unsupported | config_driven
selected_capability_keys[]
missing_capability_keys[]
```

`support_summary` contains:

```text
total
supported
partial
unsupported
config_driven
by_panel_key
```

Important semantics now aligned between backend and frontend:

- a field is available by `capability_key` first;
- if `capability_key` is empty, it falls back to `metric_key`;
- acceptable capabilities are evaluated before `config_driven_query`;
- `config_driven` is a fallback state, not an override when a standard capability is already available.

Frontend data logic has matching support:

```text
/OneOPS/OneOps-UI/src/api/platform/teleabs.ts
/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts
/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricContract.ts
```

Frontend now has:

- typed API wrappers for default panel requirements, panel support, strategy-set contract, and strategy-set panel preview;
- optional `requirements` in `SnmpStrategySetPanelCapabilityPreviewRequest`, matching backend fallback behavior;
- `summarizePanelCapabilitySupports(...)` for local/offline parity with backend `support_summary`;
- smoke coverage proving frontend local capability support uses the same `metric_key` fallback and config-driven fallback order as backend.

Still deferred:

- page-level consumption of target-based strategy-set contract resolution and panel preview,
- page-level consumption of strategy-set contract resolution and panel preview,
- Prometheus recording-rule generation and lifecycle,
- Grafana dashboard JSON materialization,
- backend parsing of legacy SNMP processor YAML,
- broad vendor/private metric standardization.

### 10. Target-Based Strategy-Set Panel Preview Is Strictly Closed

The backend now also has a strict by-target data path for real device context resolution, still without Grafana JSON generation.

Additional backend endpoint:

```text
POST /platform/metrics/teleabs/strategy-sets/:id/metric-contract/panel-support/by-target
```

Request:

```json
{ "target_part": "DEVICE-CODE-OR-ID" }
```

The endpoint performs the current real-device data loop:

```text
strategy_set_id + target_part
  -> platform_devices_v2
  -> deviceidentity.ResolveMetadata(...)
  -> SnmpMetricStrategySetContractOptions
  -> ResolveStrategySetContractWithOptions
  -> effective_contract
  -> backend default base panel requirements
  -> supports[]
  -> support_summary
```

Business semantics are converted in the backend resolver only:

- `platform_devices_v2.attributes_json` and `metadata_json` are merged;
- `deviceidentity.ResolveMetadata(...)` normalizes catalog, manufacturer, platform, model, and version semantics;
- the normalized result is mapped into `SnmpMetricStrategySetContractOptions`;
- frontend does not infer manufacturer, platform, model, catalog, or version.

Strict behavior:

- empty `target_part` returns an error;
- missing `platform_devices_v2` device returns an error;
- missing required target context returns an error;
- zero matched strategy-set item contracts returns an error;
- the by-target endpoint always uses backend default base panel requirements;
- no legacy inventory fallback, dashboard-binding fallback, caller-provided context fallback, or frontend target-context fallback is used.

Response shape:

```text
strategy_set_id
target
  target_part
  device_id
  device_code
  context
  metadata_source
source
item_contracts[]
effective_contract
supports[]
support_summary
```

Frontend typed API support exists in:

```text
/OneOPS/OneOps-UI/src/api/platform/teleabs.ts
/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts
```

### 11. Next Step: Real-Data Acceptance Before More UI

Before page-level consumption or Grafana work, validate the strict by-target loop with real devices.

Runbook:

```text
/OneOPS/docs/superpowers/testing/snmp-by-target-panel-preview-acceptance-2026-06-11.md
```

Acceptance should cover at least:

- one H3C / Comware device;
- one non-H3C device;
- one negative sample for missing target, missing context, or no matched strategy item.

For each sample, verify:

- `target.context` matches the real device metadata;
- `item_contracts[]` selects the expected strategy items;
- `effective_contract` exposes only supported capabilities;
- `support_summary.total` is `7`;
- each base panel state matches the selected contract.

Do not start page-level UI consumption until this real-data acceptance is recorded.

Local candidate discovery has found demo data for the first acceptance pass:

```text
strategy_set_id: 4284353d-1233-4022-ad18-871b3d8444c7
candidate targets:
  DVCF5A07C0AFFC9  H3C / Comware / S6900-54QF-F
  DVC7F2EED8EC1E0  H3C / Comware / S6520X-54QC-EI
  DVC2C4468B0B813  Huawei / VRP / CE6855HI
  DVCF21C6B43350C  Maipu / MyPower / S4320
```

Current blocker:

```text
The running local :8080 process returns 404 for the by-target route.
It appears to be an older running binary, not the freshly built backend with the new endpoint.
Acceptance is not marked passed until the updated backend process serves the route.
```

Direct resolver acceptance was run against the same demo MySQL data:

```text
real MySQL
  -> TeleabsStrategySrv
  -> TeleabsStrategySetSrv
  -> MetricCapabilityContractResolver.ResolveStrategySetTargetPanelCapabilityPreview(...)
```

Result summary:

```text
DVCF5A07C0AFFC9  H3C / Comware
  matched: 10000000-0000-4000-8000-000000000001
  support_summary: total=7 supported=0 partial=0 unsupported=6 config_driven=1
  decision: partial / data needs improvement

DVC7F2EED8EC1E0  H3C / Comware
  matched: 10000000-0000-4000-8000-000000000001
  support_summary: total=7 supported=0 partial=0 unsupported=6 config_driven=1
  decision: partial / data needs improvement

DVC2C4468B0B813  Huawei / VRP candidate
  resolved platform_name: HuaWei
  result: no matched metric contract items
  decision: expected strict failure, data normalization needs review

DVCF21C6B43350C  Maipu / MyPower
  matched: 50000000-0000-4000-8000-000000000001
  support_summary: total=7 supported=4 partial=0 unsupported=3 config_driven=0
  decision: partial pass
```

Negative strict checks:

```text
empty target -> target_part is required
missing target -> target device not found
```

Current acceptance conclusion:

- resolver-level core data logic is working;
- HTTP endpoint acceptance is still blocked by the running old process;
- real strategy data is not yet good enough for page-level consumption;
- next work should fix data/normalization issues before UI.

Follow-up data-logic fixes and re-acceptance:

```text
fixed:
  metadata_json now overrides attributes_json for non-empty target semantic fields;
  cpu_usage and memory_usage passthrough fields now map to direct standard capabilities.

re-acceptance:
  DVCF5A07C0AFFC9  H3C / Comware
    matched: 10000000-0000-4000-8000-000000000001
    support_summary: total=7 supported=2 partial=0 unsupported=4 config_driven=1
    CPU/Memory: supported
    interface basics: still unsupported

  DVC7F2EED8EC1E0  H3C / Comware
    matched: 10000000-0000-4000-8000-000000000001
    support_summary: total=7 supported=2 partial=0 unsupported=4 config_driven=1
    CPU/Memory: supported
    interface basics: still unsupported

  DVC2C4468B0B813  Huawei / VRP
    resolved platform_name: VRP
    matched: 20000000-0000-4000-8000-000000000001
    support_summary: total=7 supported=2 partial=0 unsupported=4 config_driven=1
    CPU/Memory: supported
    interface basics: still unsupported

  DVCF21C6B43350C  Maipu / MyPower
    matched: 50000000-0000-4000-8000-000000000001
    support_summary: total=7 supported=6 partial=0 unsupported=1 config_driven=0
    traffic/status/speed/quality/CPU/Memory: supported
    broadcast: unsupported
```

Updated acceptance conclusion:

- resolver-level by-target logic works against real demo data;
- metadata precedence and direct CPU/Memory usage mapping are fixed;
- H3C/Huawei selected strategies still need interface table fields before page-level consumption;
- broadcast remains unsupported where strategy data lacks broadcast inputs;
- HTTP endpoint acceptance still requires running the updated backend route.

API handler HTTP contract follow-up:

```text
added:
  app/platform/api/teleabs_metric_contract_http_test.go

verified route:
  POST /platform/metrics/teleabs/strategy-sets/:id/metric-contract/panel-support/by-target

covered:
  route id is passed as strategy_set_id;
  JSON body target_part is passed to the resolver;
  success response returns target.context and support_summary;
  empty target request is delegated to the strict resolver and returns target_part is required.

verification:
  go test ./app/platform/api -run 'TestTeleabsAPI_PreviewStrategySetPanelCapabilitySupportByTarget_HTTP' -count=1
```

Current boundary:

- handler-level HTTP contract is now closed by test;
- resolver-level by-target logic is already checked against real demo data;
- externally reachable process-level HTTP acceptance is still not claimed until an updated backend process can run without unrelated startup blockers.

Minimal HTTP process acceptance:

```text
process shape:
  Gin route
    -> TeleabsAPI.PreviewTeleabsStrategySetPanelCapabilitySupportByTarget
    -> MetricCapabilityContractResolver
    -> demo MySQL

route:
  POST /platform/metrics/teleabs/strategy-sets/:id/metric-contract/panel-support/by-target
```

Verified through curl against the temporary HTTP process:

```text
DVCF5A07C0AFFC9  H3C / Comware
  matched: 10000000-0000-4000-8000-000000000001
  support_summary: total=7 supported=2 partial=0 unsupported=4 config_driven=1
  CPU/Memory: supported
  interface basics: still unsupported except speed config_driven

DVC2C4468B0B813  Huawei / VRP
  matched: 20000000-0000-4000-8000-000000000001
  support_summary: total=7 supported=2 partial=0 unsupported=4 config_driven=1
  CPU/Memory: supported
  interface basics: still unsupported except speed config_driven

DVCF21C6B43350C  Maipu / MyPower
  matched: 50000000-0000-4000-8000-000000000001
  support_summary: total=7 supported=6 partial=0 unsupported=1 config_driven=0
  traffic/status/speed/quality/CPU/Memory: supported
  broadcast: unsupported

strict negatives:
  {} -> target_part is required
  DVC-NOT-EXIST -> target device not found
```

Updated boundary:

- endpoint path, JSON binding, handler call, resolver, real MySQL lookup, strategy-set matching, and support summary now work through a real HTTP process;
- this still does not claim full OneOps application startup acceptance;
- full application acceptance remains blocked by unrelated runtime dependencies.

Product router registration check:

```text
added:
  app/platform/router/teleabs_routes_consistency_test.go

verified:
  platform.go and platform_bidi.go expose the same Teleabs route set;
  both router definitions include:
    POST strategy-sets/:id/metric-contract/panel-support/by-target

verification:
  go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1
```

Current closed path:

```text
product router definition
  -> by-target HTTP handler
  -> MetricCapabilityContractResolver
  -> platform_devices_v2 target context
  -> strategy-set selector
  -> effective_contract
  -> default panel requirements
  -> supports[] + support_summary
```

Full OneOps application acceptance:

```text
startup:
  current backend code was started as a full OneOps application process;
  temporary full config was copied from the Nacos backup;
  only the HTTP port was changed to 18082 to avoid the existing 8080 process.

actual full-app route:
  POST /api/v1/platform/metrics/teleabs/strategy-sets/:id/metric-contract/panel-support/by-target

auth:
  X-Auth-Token is required on the full private route.

startup result:
  Redis connected;
  MongoDB connected;
  BootInit completed;
  HTTP server started on 18082.

non-blocking startup note:
  OneOps listener on :7070 reported address already in use,
  but this did not block the main HTTP endpoint acceptance.
```

Full-app HTTP acceptance results:

```text
DVCF5A07C0AFFC9  H3C / Comware
  matched: 10000000-0000-4000-8000-000000000001
  support_summary: total=7 supported=2 partial=0 unsupported=4 config_driven=1
  CPU/Memory: supported
  interface basics: still unsupported except speed config_driven

DVC2C4468B0B813  Huawei / VRP
  matched: 20000000-0000-4000-8000-000000000001
  support_summary: total=7 supported=2 partial=0 unsupported=4 config_driven=1
  CPU/Memory: supported
  interface basics: still unsupported except speed config_driven

DVCF21C6B43350C  Maipu / MyPower
  matched: 50000000-0000-4000-8000-000000000001
  support_summary: total=7 supported=6 partial=0 unsupported=1 config_driven=0
  traffic/status/speed/quality/CPU/Memory: supported
  broadcast: unsupported

strict negatives:
  {} -> target_part is required
  DVC-NOT-EXIST -> target device not found
```

Updated boundary:

- by-target data path is now closed through full OneOps HTTP routing;
- the previous 404 was caused by using the bare `/platform/...` path instead of the full-app `/api/v1/platform/...` path;
- this still does not include page-level frontend consumption or Grafana materialization.

### 12. Page-Level By-Target Panel Preview Consumption Is Now Wired

The first page-level consumption point is now the strategy-set detail drawer, still without Grafana JSON generation.

Frontend entry:

```text
/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/StrategySetDetailDrawer.vue
```

Frontend helper:

```text
/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/snmpStrategySetTargetPanelPreview.ts
```

Smoke coverage:

```text
/OneOPS/OneOps-UI/scripts/snmp-strategy-set-target-panel-preview-smoke.ts
npm run smoke:snmp-strategy-set-target-panel-preview

/OneOPS/OneOps-UI/scripts/snmp-strategy-set-target-panel-preview-browser-smoke.cjs
npm run smoke:snmp-strategy-set-target-panel-preview-browser
```

Current page data loop:

```text
strategy-set detail drawer
  -> operator inputs target device code or ID
  -> previewTeleabsStrategySetPanelCapabilitySupportByTarget(strategy_set_id, target_part)
  -> backend by-target resolver
  -> platform_devices_v2 metadata normalization
  -> strategy-set item matching
  -> effective_contract
  -> default base panel requirements
  -> supports[] + support_summary
  -> drawer displays target context, matched strategy IDs, summary, and panel states
```

Strict frontend boundary:

- frontend only trims `strategy_set_id` and `target_part`;
- frontend does not infer catalog, manufacturer, platform, model, version, or strategy match context;
- frontend does not provide caller-defined panel requirements on the by-target path;
- frontend does not generate Prometheus recording rules;
- frontend does not generate Grafana dashboard JSON.

Browser smoke coverage mounts the drawer through Vite, intercepts the by-target API response, submits a target device code, verifies the returned context and panel rows are visible, and checks the drawer stays inside both desktop and narrow mobile viewports.

The browser smoke also verifies the page interaction contract:

- empty target input shows `请输入目标设备编码或 ID` and does not call the by-target backend;
- valid target input calls the backend exactly once;
- request body is exactly `{ "target_part": "DVCF21C6B43350C" }` after trimming user input;
- request URL stays on `/strategy-sets/:id/metric-contract/panel-support/by-target`.
- backend strict errors are preserved in the drawer alert, for example `target device not found: DVC-NOT-EXIST`;
- the by-target frontend API wrapper reads the response envelope for this endpoint and throws backend `msg` when `code != 0`.

Responsive UI fix:

- `StrategySetDetailDrawer` uses `width="min(860px, 100vw)"`;
- this keeps the drawer full-size on desktop while preventing the right-side drawer from starting outside a 390px mobile viewport;
- no data contract, backend resolver, Grafana, or Prometheus recording-rule logic changed for this fix.

### 13. Real Page Acceptance Against Current Backend Code

The strategy-set detail drawer has now been accepted against a real current-code backend process, not only an intercepted browser smoke.

Acceptance environment:

```text
backend:
  current OneOps working tree
  /tmp/oneops-full-app-acceptance.yaml
  http://127.0.0.1:18082

frontend:
  Vite dev server with VITE_PROXY_TARGET=http://127.0.0.1:18082
  http://localhost:5174

script:
  /OneOPS/OneOps-UI/scripts/snmp-strategy-set-target-panel-preview-real-page-acceptance.cjs

command shape:
  ONEOPS_UI_REAL_BASE_URL=http://localhost:5174
  ONEOPS_UI_REAL_TOKEN=<login token>
  npm run smoke:snmp-strategy-set-target-panel-preview-real-page
```

The real-page script does not intercept the by-target API. It mounts the drawer, uses the product token supplied by the caller, submits target device codes, reads the real backend response through the Vite proxy, and verifies the drawer display.

Accepted targets:

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

Important environment note:

- the already-running local `:8080` process returned older by-target behavior, including Huawei no-match and CPU/Memory unsupported states;
- do not use the default `5173 -> 8080` path as evidence for this acceptance unless that backend process is restarted from the current code;
- the accepted real-page path for this run is `5174 -> 18082`.

This closes the current non-Grafana page-level data loop:

```text
real target input
  -> backend authoritative contract/support answer
  -> frontend typed API
  -> page-level preview display
```

## 2026-06-11 Multi-Agent Audit Result

Four read-only audits were run to check whether the current data model can become a stable end-to-end path. No files were changed by the audit agents.

### Backend Authority

The authoritative metric capability resolver should live in the OneOps backend platform service layer, not in the UI, controller, model structs, or only inside `StrategyApplyV2Srv`.

Recommended future location:

```text
/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go
/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go
```

That resolver should reuse existing strategy, strategy set, template, strategy chain, selector, `produces_metrics`, and `metric_manifest` logic, then expose one backend authoritative answer for:

```text
strategy / strategy set / device context
  -> effective metric capability contract
```

Important boundary: the backend resolver has started to become the source of truth for strategy-level SNMP contracts. The frontend resolver should now be treated as fallback/editor-local compatibility logic, not the final authority.

### Prometheus Recording Rule Publishing

Recording rules should not be generated or published by Teleabs or the controller agent.

Current real chain:

```text
OneOps strategy/template
  -> Teleabs generates Telegraf inputs
  -> OneOps injects outputs
  -> Bidi sends config bundle
  -> agent hot-replaces Telegraf collection task
  -> raw metrics arrive in Prometheus
```

Future recording rule publishing should be a separate OneOps backend capability:

```text
metric capability contract
  -> recording rule generator
  -> Prometheus rule group YAML
  -> validation
  -> publish/reload
  -> published/reload status
```

Current gap: there is no external Prometheus recording-rule lifecycle model yet. Existing reload logic is for OneOps alert-engine rules, not Prometheus server rule files.

### Grafana Materialization

Grafana currently stores and syncs dashboard JSON content. `PanelSpec` and capability contracts are not yet connected to Grafana JSON generation.

Future insertion point should be before dashboard sync to Grafana:

```text
DashboardVariant / PanelSpec
  -> selected capability / record / config-driven query
  -> materialized Grafana dashboard JSON
  -> syncToGrafana
```

Important boundary: do not start Grafana JSON generation until the backend authoritative capability resolver and Prometheus record lifecycle are designed.

### Real Panel / PromQL Alignment

Existing monitor panels confirm that the current base scope needs interface quality metrics now:

```text
errors
discards
broadcast traffic
CPU usage
memory usage
```

The audit also found data-model details that should be resolved before expanding UI. Current closure decision:

- Current error/discard panels use `idelta(...)`, but the standard capability contract keeps `*_rate` as canonical per-second rate with `pps` units. If Grafana needs legacy window-delta parity later, that belongs in Grafana materialization or a separately approved `*_delta` capability variant.
- `ifSpeed` is now a first-class base capability, `if_speed_bps`, while still exporting raw `ifSpeed` back to SNMP/Telegraf config.
- Interface utilization may need explicit capabilities, for example `if_in_utilization` and `if_out_utilization`, because existing broadcast PromQL already computes traffic divided by `ifSpeed`.
- `device_reachable` and `system_uptime` are useful common capabilities, but they should not be added to this phase unless the next strict plan explicitly includes them.
- Memory based on host-resources storage tables needs extra filtering semantics and should not be assumed equivalent to the simple top-level `memUsage / memUsed / memTotal` mappings.

## Current Phase Decision After Audit

The current data model is now available through backend strategy-level resolution, strategy-set-level resolution, and strategy-set panel capability preview. The frontend local resolver remains as fallback/editor-local compatibility logic while the backend authority matures.

The current safe order is now:

```text
1. Keep data closure focused on base common SNMP panels only.
2. Use backend resolver output as the authoritative answer for strategy/strategy-set/panel support previews.
3. Use the strict by-target endpoint when the caller has a real device/target.
4. Keep frontend local resolver behavior aligned with backend semantics for editor-local compatibility flows.
5. Next consume strategy-set and by-target panel previews at page level only if explicitly requested.
6. Then design Prometheus recording-rule lifecycle.
7. Then design Grafana materialization.
```

Do not start Prometheus publishing or Grafana JSON work until the backend contract resolver and panel support preview are accepted as stable enough for strategy-set/dashboard-family consumers.

The data-model closure pass has now resolved:

```text
resolved-now:
  - error/discard standard semantics remain rate/pps
  - ifSpeed is first-class base input/capability as if_speed_bps

still candidate only if explicitly approved:
  - interface utilization if needed by current panels

defer unless explicitly approved:
  - device_reachable
  - system_uptime
  - host-resources memory table normalization
  - vendor-private CPU/memory OID catalogs
```

## Verification Already Run

These backend commands were run from `/OneOPS/OneOps` after the latest data-logic closure changes:

```bash
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolver -count=1
go test ./app/platform/api ./app/platform/service/impl ./cmd -run 'TestMetricCapabilityContractResolver|^$' -count=1
```

Observed results:

- `app/platform/service/impl` resolver tests exited with code `0`;
- `app/platform/api`, `app/platform/service/impl`, and `cmd` compile/test checks exited with code `0`.

These frontend commands were run from `/OneOPS/OneOps-UI` after the latest changes:

```bash
npm run smoke:snmp-metric-contract
npm run smoke:snmp-workspace-view
npm run smoke:snmp-profile-resolution
npm run typecheck
```

Observed results:

- `snmp metric contract smoke passed`
- `snmp workspace view smoke passed`
- `snmp profile resolution smoke passed`
- `npm run typecheck` exited with code `0`

## The Most Important Handoff: Current Data Logic Understanding

This section matters more than the feature checklist.

### The Original Intended Data Logic

The design intends this:

```text
device context
  -> resolve strategy set
  -> resolve root dashboard family
  -> resolve child dashboard variant
  -> resolve effective strategies
  -> resolve semantic metric groups
  -> resolve stable panel specs
  -> later generate / diff / trace dashboard panels
```

At the strategy editor level, the intended semantic model is:

```text
SNMP profile semantic template
  + legacy raw SNMP facts
  + parent/child inheritance
  + user overrides
  = effective semantic metric contract
```

That semantic metric contract should use stable keys such as:

- `metric_group_key`
- `metric_key`
- `panel_key`

Examples from the design:

- `interface_basic`
- `if_name`
- `if_in_rate`
- `if_out_rate`
- `if_oper_status`
- `interface_basic.traffic`
- `interface_basic.status`

The profile is supposed to define the semantic shape.

### The Current Actual Runtime Data Logic

What the current implementation really does is:

```text
1. If parameters.metric_groups exists:
     use it as explicit contract

2. Else:
     import from passthrough_config + metric_manifest

3. For child pages:
     apply parent/child group inheritance on top

4. Use the result as the page contract
```

Important actual code path:

- `PluginFormSnmp.vue` computes `contract` from `resolveSnmpContractFromStrategyParameters(...)`
- `resolveSnmpContractFromStrategyParameters(...)` prefers explicit `metric_groups`
- otherwise it calls `importSnmpContractFromStrategyParameters(...)`

Current import behavior:

- top-level SNMP fields become `device_metrics`
- SNMP table name becomes `group_key`
- raw field names become `metric_key`
- manifest-only metrics are patched back into `fields`
- default `panel_specs` are generated from currently visible metrics

This means the current page contract is still fundamentally:

```text
legacy raw SNMP import
  -> pseudo contract
  -> inheritance
  -> page
```

not:

```text
profile semantic contract
  + raw fact mapping
  + inheritance
  -> page
```

## Strategy System And Dashboard System: Current Real Alignment Facts

These facts were confirmed from code and schema.

### Strategy Side

`TeleabsStrategySet`:

- contains strategy references,
- contains `dashboard_codes[] / dashboard_names[]`,
- persists root dashboard binding via `platform_teleabs_strategy_set_dashboard_binding`.

`TeleabsStrategy`:

- supports `parent_id`,
- supports `manufacturer_id / platform_id / device_model_ids / catalog_id / version_min / version_max`,
- currently stores the new semantic contract in `parameters.metric_groups`.

### Dashboard Side

`grafana_dashboard` already supports:

- `parent_id` for root/child variant structure,
- `manufacturer_id`,
- `platform_id`,
- `device_model_ids`,
- `catalog_id`.

So the dashboard system already has a natural shape for:

```text
DashboardFamily = root dashboard
DashboardVariant = child dashboard filtered by device profile
```

### Device-Bound Dashboard Lookup Already Exists

Frontend API already has `listDeviceBoundDashboardsReq(targetPart)` returning:

- `strategy_set_id`
- `root_dashboard_code`
- `dashboard_code`
- `is_child`
- `matched_by`
- `match_reason`

This proves the system already partially supports:

```text
device
  -> strategy_set
  -> root_dashboard
  -> matched child dashboard
```

## Current Misalignment Between The Two Systems

This is the main problem list.

### Problem 1: The Strategy Page Contract Is Still Raw-Oriented

Current example group:

- `snmp_interface`

But the semantic profile group is:

- `interface_basic`

That is a structural mismatch.

Effect:

- strategy-side group identity is unstable,
- dashboard-side `panel_key -> metric_group_key` cannot rely on a normalized semantic key,
- cross-vendor reuse becomes weak.

### Problem 2: Metric Keys Are Raw Field Names, Not Stable Semantic Metrics

Current imported keys can be:

- `ifInOctets`
- `ifOutErrors`
- `ifOperStatus`

But the semantic contract should eventually stabilize on keys like:

- `if_in_rate`
- `if_out_rate`
- `if_oper_status`

The dashboard layer wants semantic metrics, not raw SNMP table columns.

### Problem 3: Manifest-Only Backfill Improves Visibility But Not Meaning

The recent patch that backfills manifest-only metrics is useful for debugging and visibility, but those fields can still lack:

- OID,
- raw source mapping,
- calculation meaning,
- exportability.

So the page may now show "complete-looking" metrics while still lacking a real semantic contract.

### Problem 4: There Is No Formal Raw-To-Semantic Mapping Layer Yet

This is the biggest conceptual gap.

We still do **not** have an explicit layer that says:

```text
raw group snmp_interface
  -> semantic group interface_basic

raw field ifDescr
  -> semantic metric if_name

raw field ifInOctets / ifHCInOctets
  -> semantic metric if_in_rate

raw field ifOutOctets / ifHCOutOctets
  -> semantic metric if_out_rate

raw field ifOperStatus
  -> semantic metric if_oper_status
```

Without this layer:

- the strategy editor cannot become a semantic editor,
- the dashboard system cannot consume stable panel contracts,
- child overrides stay tied to raw import shape.

### Problem 5: Panel Specs Are Not Yet Real Dashboard Contracts

Current imported panel specs are mostly generated from available metrics.

They are useful for UI preview, but they are not yet the stable, profile-defined dashboard contract that future panel generation needs.

The design wants stable panel contracts such as:

- `interface_basic.traffic`
- `interface_basic.status`

Current import-time defaults are too shallow for long-term panel traceability.

### Problem 6: Parent/Child Inheritance Is Correctly Implemented At The Wrong Level

The inheritance machinery itself is reasonably correct:

- `inherit`
- `add`
- `override`
- `disable`

But it currently operates on the imported group layer.

That means child strategies inherit:

- `snmp_interface`

instead of inheriting:

- `interface_basic`

So even correct inheritance behavior can still be attached to the wrong conceptual model.

### Problem 7: Export Safety Guard Proves The Model Is Not Yet Closed

Current exportability rule:

- every enabled field must have an OID,
- otherwise the UI saves only `metric_groups`,
- and does not overwrite the real SNMP legacy raw config.

This is a good safety control.

But it also proves a deeper truth:

- the current page model is not yet a fully exportable strategy model,
- it is still partly an analysis/transition model.

## Current Risks

### Risk 1: Semantic Contract And Real SNMP Config Drift

If users edit `metric_groups` but many semantic fields have no OID/source mapping, then:

- the semantic contract changes,
- but the real collection config may not change.

This avoids destructive overwrites, but creates long-term drift risk between:

- strategy semantics,
- actual collection config,
- future dashboard assumptions.

### Risk 2: Dashboard Mapping May Freeze On Raw Keys

If we let current raw group names and raw field names propagate further into panel binding logic, then future dashboard generation may accidentally lock onto:

- `snmp_interface`
- `ifInOctets`
- `ifOperStatus`

instead of semantic keys.

That would make dashboard families much harder to normalize across vendors and templates.

### Risk 3: Child Strategy History May Become Migration Debt

If users start saving many child overrides against raw-import groups, then when we later introduce semantic group normalization, we will need migration logic from:

- raw imported child diffs

to:

- semantic child diffs

The longer this is delayed, the more painful it becomes.

### Risk 4: Strategy Matching And Dashboard Variant Matching May Diverge

Design explicitly requires both to use the same match context:

- manufacturer
- platform
- model
- catalog
- version

Current fields exist on both sides, but there is no single shared canonical matcher yet.

So this risk is real even if it has not exploded yet.

## Canonical Alignment Model Recommended For The Next AI

Treat these four layers as distinct:

```text
Layer 1: legacy collection facts
- passthrough_config
- metric_manifest

Layer 2: profile semantic template
- semantic metric groups
- semantic metric keys
- stable panel specs

Layer 3: effective editable semantic contract
- profile template
- raw fact mapping
- parent/child inheritance
- user overrides

Layer 4: exportable raw contract
- generate passthrough_config
- generate metric_manifest
- only when source mapping is complete
```

This model creates the bridge both systems need:

```text
strategy system
  -> effective semantic contract
  -> dashboard panel contract
  -> dashboard family / variant / panel binding
```

## Updated Decision: Limited Standardization, Not Full Standardization

After further analysis, the target should **not** be full metric standardization.

The stable direction is:

```text
limited base standardization
  + metric capability declarations
  + Prometheus recording rules for common reusable metrics
  + config-driven panels for vendor-specific or unstandardized metrics
```

This avoids forcing every vendor metric into one global semantic model.

### What Should Be Standardized First

Only standardize foundational, high-reuse metrics first:

```text
system_basic
  - cpu usage variants
  - memory usage variants
  - device status

interface_basic
  - interface name
  - interface inbound rate
  - interface outbound rate
  - interface operational status
  - interface inbound/outbound error rate
  - interface inbound/outbound discard rate
  - interface inbound/outbound broadcast traffic ratio
```

Specialized domains should remain config-driven until there is a clear reason to standardize them:

- optical modules,
- wireless,
- storage,
- power,
- fans,
- cards,
- vendor-private metrics,
- temporary project metrics.

Interface quality metrics are **not** deferred specialized metrics anymore. Error rate, discard rate, and broadcast traffic ratio are current base interface requirements.

### One Concept Can Have Multiple Standards

Do **not** force a concept such as CPU usage or memory usage into one single metric key.

Different devices may support different valid standards:

```text
cpu_usage_direct
  raw value is already CPU usage

cpu_usage_from_idle
  CPU usage is calculated as 100 - idle

cpu_usage_core_avg
  CPU usage is calculated from multiple CPU core values

cpu_usage_1m / cpu_usage_5m
  vendor already exposes rolling-window CPU usage values
```

Memory usage may also have multiple valid forms:

```text
memory_usage_direct
memory_usage_used_total
memory_usage_free_total
```

The strategy should declare what the device actually supports. If the raw data does not support a standard, do not fake it and do not force the panel to display it.

### Config-Driven Metrics Must Stay

For metrics that are not worth standardizing yet, keep a simplified config-driven path:

```text
raw metric / raw query
  -> display name
  -> unit
  -> panel type
  -> thresholds
  -> Grafana panel
```

These metrics can be displayed in Grafana, but they should not be treated as cross-vendor semantic contracts.

## Updated Real Data Flow With Prometheus Records

The preferred execution model is:

```text
device / SNMP agent
  -> device profile match
     manufacturer / platform / model / catalog / version
  -> StrategySet match
  -> SNMP Strategy chain
     root strategy + child overrides
  -> strategy semantic contract resolver
  -> effective metric capability contract
  -> SNMP collection config
  -> raw Prometheus metrics
  -> Prometheus recording rules for selected common capabilities
  -> standard Prometheus records
  -> Grafana standard panels
```

Vendor-specific or unstandardized metrics use a parallel path:

```text
raw Prometheus metrics
  -> config-driven query template
  -> Grafana config-driven panel
```

The responsibility split should be:

```text
Strategy/Profile
  defines raw source mapping, capability support, and transform rules

Prometheus recording rules
  execute selected standard calculations and produce reusable records

Grafana
  queries standard records for common panels
  uses config-driven queries for vendor-specific panels
```

So standardization is not performed inside Grafana. Grafana should consume either:

- standard records generated from strategy-defined rules,
- or explicit config-driven queries for non-standard panels.

### Example: CPU

```text
Vendor A:
  raw: cpuUsage
  capability: cpu_usage_direct
  record: oneops:cpu_usage_direct:ratio

Vendor B:
  raw: cpuIdle
  capability: cpu_usage_from_idle
  record: oneops:cpu_usage_from_idle:ratio

Vendor C:
  raw: cpuCoreUsage[]
  capability: cpu_usage_core_avg
  record: oneops:cpu_usage_core_avg:ratio
```

Grafana CPU panels should match one of the supported CPU usage capabilities instead of assuming one universal `cpu_usage` metric.

### Example: Memory

```text
Vendor A:
  raw: memUsage
  capability: memory_usage_direct

Vendor B:
  raw: memUsed + memTotal
  capability: memory_usage_used_total

Vendor C:
  raw: memFree + memTotal
  capability: memory_usage_free_total
```

Again, the device should expose only the capabilities it can actually support.

## Updated Grafana Meaning

From Grafana's perspective, the system becomes capability-driven:

```text
DashboardFamily
  defines common panel intent

DashboardVariant
  adapts panels by device profile and supported capabilities

PanelSpec
  declares acceptable capabilities or config-driven queries

Grafana panel
  queries the selected Prometheus record or raw/config-driven query
```

Grafana should not bind directly to vendor raw field names for common panels.

For common standardized panels:

```text
PanelSpec
  -> required/preferred capability
  -> selected Prometheus record
  -> Grafana query
```

For non-standard panels:

```text
PanelSpec
  -> config-driven query template
  -> Grafana query
```

This gives the dashboard system three panel classes:

```text
1. base standard panels
   CPU, memory, device status, interface traffic, interface status

2. future domain standard panels
   optical, power, fan, wireless, storage, etc. when they become worth standardizing

3. config-driven panels
   vendor-private, temporary, or project-specific metrics
```

## Updated Risks And Acceptability

### Risk: Recording Rule Count Can Grow

Different vendors and capability variants can produce many recording rules.

This is acceptable only if controlled:

- generate records for base common metrics first,
- avoid generating records for every raw metric,
- avoid high-cardinality labels,
- keep vendor-specific metrics config-driven by default.

### Risk: Prometheus Cost Increases

Recording rules create additional time series.

This is acceptable for high-reuse dashboard and alert metrics, but not for all metrics.

### Risk: Same Panel Title May Hide Different Calculation Semantics

A panel titled "CPU usage" may use:

- direct vendor value,
- `100 - idle`,
- average of CPU cores,
- a 1-minute or 5-minute vendor value.

This is acceptable only if the selected capability remains traceable from the panel back to:

```text
Panel
  -> selected capability
  -> Prometheus record
  -> recording rule
  -> raw metrics
  -> strategy mapping
```

### Risk: Strategy Changes Need Publication

Saving a strategy is not enough if it changes records.

The system should eventually distinguish:

```text
saved
published
Prometheus rule reloaded
record has data
Grafana panel available
```

### Risk: Config-Driven Panels Are Less Reusable

This is intentional. They are allowed for flexibility, but they should not be mistaken for stable cross-vendor contracts.

## Recommended Next Development Direction

Do **not** keep adding more raw-field visibility first, and do **not** pursue full standardization.

The first formal metric capability model for base SNMP metrics now has an initial implementation.

Implemented base interface mapping:

```text
snmp_interface
  -> interface_basic

ifDescr
  -> if_name

ifInOctets / ifHCInOctets
  -> if_in_rate

ifOutOctets / ifHCOutOctets
  -> if_out_rate

ifOperStatus
  -> if_oper_status

ifInErrors
  -> if_in_error_rate

ifOutErrors
  -> if_out_error_rate

ifInDiscards
  -> if_in_discard_rate

ifOutDiscards
  -> if_out_discard_rate

ifInNUcastPkts + ifInUcastPkts + ifInOctets + ifSpeed
  -> if_in_broadcast_ratio

ifOutNUcastPkts + ifOutUcastPkts + ifOutOctets + ifSpeed
  -> if_out_broadcast_ratio
```

Also add base system capability examples:

```text
cpuUsage
  -> cpu_usage_direct

cpuIdle
  -> cpu_usage_from_idle

memUsage
  -> memory_usage_direct

memUsed + memTotal
  -> memory_usage_used_total
```

Also implemented:

```text
memFree + memTotal
  -> memory_usage_free_total
```

The contract model carries:

- `metric_group_key`,
- `capability_key`,
- `concept_key`,
- `raw_source`,
- `transform_rule`,
- `recording_rule` metadata when a Prometheus record is generated,
- `exportability` / `recordability` status,
- config-driven fallback metadata for non-standard metrics.

Child inheritance should happen over semantic/capability groups, not raw import groups.

Dashboard impact preview should reason over:

```text
PanelSpec
  -> acceptable capabilities
  -> selected record or config-driven query
  -> support / unsupported / partial state
```

Before moving to UI or Grafana generation, review this data model against real SNMP strategies and confirm the first-pass capability keys and record names are acceptable.

### 14. Quick Env H3C/Huawei/Maipu SNMP Network Seeds Are Added

The data closure now includes quick env seed data for H3C, Huawei, and Maipu network SNMP strategies.

New quick env files:

```text
/OneOPS/quick_env/docker-entrypoint-initdb.d/zzzzzzzzzz-h3c-snmp-network-strategy-bootstrap.sql
/OneOPS/quick_env/docker-entrypoint-initdb.d/zzzzzzzzzz-huawei-snmp-network-strategy-bootstrap.sql
/OneOPS/quick_env/docker-entrypoint-initdb.d/zzzzzzzzzz-maipu-snmp-network-strategy-bootstrap.sql
/OneOPS/quick_env/scripts/sync_snmp_network_strategy_seed.sh
/OneOPS/quick_env/tests/test_snmp_network_strategy_seed.sh
/OneOPS/quick_env/tests/test_sync_snmp_network_strategy_seed.sh
```

Why the files use the later `zzzzzzzzzz-*` prefix:

- `zzzzzzzzz-current-mysql-seed-bootstrap.sql` still contains older H3C/Huawei/Maipu strategy rows;
- those older rows are CPU/memory-only and would overwrite earlier bootstrap files;
- the new H3C/Huawei/Maipu files intentionally run after the current snapshot seed;
- each file uses `ON DUPLICATE KEY UPDATE` and replaces `parameters_json`.

Seeded strategy ids:

```text
H3C    -> 10000000-0000-4000-8000-000000000001
Huawei -> 20000000-0000-4000-8000-000000000001
Maipu  -> 50000000-0000-4000-8000-000000000001
```

All three seeds now provide the same base capability shape:

```text
system_basic:
  cpu_usage
  memory_usage

interface_basic:
  ifDescr
  ifSpeed
  ifOperStatus
  ifInOctets
  ifOutOctets
  ifInErrors
  ifOutErrors
  ifInDiscards
  ifOutDiscards
  ifInUcastPkts
  ifOutUcastPkts
  ifInNUcastPkts
  ifOutNUcastPkts
```

Expected resolver impact:

- `system_basic.cpu` remains supported through `cpu_usage_direct`;
- `system_basic.memory` remains supported through `memory_usage_direct`;
- `interface_basic.traffic`, `interface_basic.status`, `interface_basic.speed`, and `interface_basic.quality` are resolvable from seed data;
- `interface_basic.broadcast` is resolvable when `ifInNUcastPkts/ifOutNUcastPkts` and unicast packet inputs are present;
- no frontend fallback or Grafana-specific data branch was added.

Verification run:

```text
bash tests/test_snmp_network_strategy_seed.sh
bash tests/test_sync_snmp_network_strategy_seed.sh
bash tests/test_runtime_helpers.sh && bash tests/test_snmp_network_strategy_seed.sh
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver|TestServerOOBSNMPSeed' -count=1
git diff --check
```

The running quick env instance `demo-core` was also updated in-place:

```text
target database: UniOPS
updated strategy ids:
  10000000-0000-4000-8000-000000000001
  20000000-0000-4000-8000-000000000001
  50000000-0000-4000-8000-000000000001
checked fields:
  manufacturer_id
  platform_id
  metric_manifest contains ifInOctets
  metric_manifest contains cpu_usage
  metric_manifest contains ifInNUcastPkts
  metric_manifest contains ifOutNUcastPkts
```

Repeatable runtime sync command:

```text
cd /OneOPS/quick_env
bash scripts/sync_snmp_network_strategy_seed.sh --instance demo-core
```

The sync script is intentionally narrow:

- it applies only the three late H3C/Huawei/Maipu SNMP network strategy seed files;
- it reads runtime settings from `quick_env/.runtime/<instance>/.env`;
- it uses the MySQL container's own `MYSQL_ROOT_PASSWORD` environment variable;
- it does not print or require the database password on the host;
- it does not export runtime data, rewrite the full bootstrap snapshot, or touch Grafana/Prometheus data.

Real page acceptance after seed sync:

```text
current backend: http://127.0.0.1:18082
frontend dev server: http://127.0.0.1:5174
script:
  ONEOPS_UI_REAL_BASE_URL=http://127.0.0.1:5174
  npm run smoke:snmp-strategy-set-target-panel-preview-real-page
```

The real page acceptance now also checks the frontend request body:

```text
POST .../panel-support/by-target
body = { "target_part": "<target>" }
```

No manufacturer, platform, model, version, or caller-provided context is sent by the page.
The backend by-target request DTO remains strict and only accepts `target_part`.

Observed support summaries:

```text
DVCF5A07C0AFFC9  H3C / Comware / S6900-54QF-F
  matched strategy: 10000000-0000-4000-8000-000000000001
  total=7 supported=7 partial=0 config_driven=0 unsupported=0

DVC2C4468B0B813  huawei / VRP / CE6855HI
  matched strategy: 20000000-0000-4000-8000-000000000001
  total=7 supported=7 partial=0 config_driven=0 unsupported=0

DVCF21C6B43350C  Maipu / MyPower / S4320
  matched strategy: 50000000-0000-4000-8000-000000000001
  total=7 supported=7 partial=0 config_driven=0 unsupported=0
```

Panel-level result:

- H3C, Huawei, and Maipu now support traffic, status, speed, quality, broadcast, CPU, and memory in the by-target preview.
- This remains a data-layer and preview-layer closure only; no Grafana JSON or Prometheus recording-rule lifecycle was added.

### 15. Recording Rule Preview Stage Has Started

The next stage now has a backend data-preview path for Prometheus recording rules. This is still preview only.

New backend endpoint:

```text
POST /platform/metrics/teleabs/strategy-sets/:id/metric-contract/recording-rules/preview/by-target
```

Request:

```json
{ "target_part": "DEVICE-CODE-OR-ID" }
```

The request remains strict:

- no manufacturer is accepted from the caller;
- no platform is accepted from the caller;
- no model/version/context is accepted from the caller;
- target semantics are still resolved by backend `platform_devices_v2` + `deviceidentity.ResolveMetadata(...)`.

Backend flow:

```text
strategy_set_id + target_part
  -> ResolveTargetContext
  -> ResolveStrategySetContractWithOptions
  -> effective_contract
  -> BuildRecordingRulePreview
  -> rule_group + rules + summary
```

Generated rules are selected only from base common recordable capabilities:

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

Implemented expression support:

```text
direct
rate
enum_map
expression:
  cpu_usage_from_idle
  memory_usage_used_total
  memory_usage_free_total
  if_in_broadcast_ratio
  if_out_broadcast_ratio
```

Frontend support is typed API only:

```text
/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts
/OneOPS/OneOps-UI/src/api/platform/teleabs.ts
/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-preview-smoke.ts
/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-preview-real-api-acceptance.cjs
```

Real API acceptance command:

```text
ONEOPS_API_BASE_URL=http://127.0.0.1:18082/api/v1
ONEOPS_API_TOKEN=<token>
npm run smoke:snmp-strategy-set-recording-rule-preview-real-api
```

Observed real API acceptance:

```text
DVCF5A07C0AFFC9  H3C / Comware
  matched strategy: 10000000-0000-4000-8000-000000000001
  generated records: 12/12

DVC2C4468B0B813  huawei / VRP
  matched strategy: 20000000-0000-4000-8000-000000000001
  generated records: 12/12

DVCF21C6B43350C  Maipu / MyPower
  matched strategy: 50000000-0000-4000-8000-000000000001
  generated records: 12/12
```

Generated record set:

```text
oneops:cpu_usage_direct:ratio
oneops:if_in_broadcast_ratio:ratio
oneops:if_in_discard_rate:pps
oneops:if_in_error_rate:pps
oneops:if_in_rate:bps
oneops:if_oper_status
oneops:if_out_broadcast_ratio:ratio
oneops:if_out_discard_rate:pps
oneops:if_out_error_rate:pps
oneops:if_out_rate:bps
oneops:if_speed_bps
oneops:memory_usage_direct:ratio
```

Quick env seeds currently provide explicit Prometheus raw names for system metrics:

```text
cpu_usage    -> snmp_cpu_usage
memory_usage -> snmp_memory_usage
```

Still deferred:

- Prometheus rule file write/publish;
- Prometheus reload;
- recording rule publish lifecycle;
- Grafana dashboard JSON;
- Grafana page consumption.

### 16. Recording Rule Materialization Dry-Run Is Now Data-Closed

The backend now converts by-target recording rule preview data into Prometheus-compatible rule YAML as a dry-run only.

Additional backend endpoint:

```text
POST /platform/metrics/teleabs/strategy-sets/:id/metric-contract/recording-rules/materialize/dry-run/by-target
```

Request:

```json
{ "target_part": "DEVICE-CODE-OR-ID" }
```

Current data loop:

```text
strategy_set_id + target_part
  -> ResolveStrategySetTargetRecordingRulePreview
  -> rule_group + rules + summary
  -> MaterializeRecordingRulePreviewYAML
  -> Prometheus rule-file YAML text
  -> parse-back validation
  -> materialization summary
```

Response shape:

```text
strategy_set_id
target
source
item_contracts[]
effective_contract
rule_group
rules[]
summary
yaml
materialization
```

`materialization` contains:

```text
format = prometheus_rule_file
dry_run = true
group_count
rule_count
yaml_bytes
valid
validation_errors[]
```

YAML shape:

```yaml
groups:
  - name: oneops_snmp_recording_rules_preview
    interval: 30s
    rules:
      - record: oneops:if_in_rate:bps
        expr: rate(snmp_interface_ifInOctets[5m]) * 8
```

Strict behavior:

- request body remains `target_part` only;
- no caller-provided context is accepted;
- target context still comes only from backend `platform_devices_v2` + `deviceidentity.ResolveMetadata(...)`;
- no frontend business-semantic inference is introduced;
- generated YAML is parsed back locally before being returned;
- invalid YAML or empty rule fields fail the request;
- no file is written;
- Prometheus is not reloaded.

Frontend support is typed API and smoke only:

```text
/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts
/OneOPS/OneOps-UI/src/api/platform/teleabs.ts
/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-materialization-dry-run-smoke.ts
/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-materialization-dry-run-real-api-acceptance.cjs
```

Real API acceptance command:

```text
ONEOPS_API_BASE_URL=http://127.0.0.1:18082/api/v1
ONEOPS_API_TOKEN=<token>
npm run smoke:snmp-strategy-set-recording-rule-materialization-dry-run-real-api
```

Observed real API acceptance:

```text
DVCF5A07C0AFFC9  H3C / Comware
  matched strategy: 10000000-0000-4000-8000-000000000001
  materialized rules: 12/12
  yaml bytes: 1615

DVC2C4468B0B813  huawei / VRP
  matched strategy: 20000000-0000-4000-8000-000000000001
  materialized rules: 12/12
  yaml bytes: 1615

DVCF21C6B43350C  Maipu / MyPower
  matched strategy: 50000000-0000-4000-8000-000000000001
  materialized rules: 12/12
  yaml bytes: 1615
```

Still deferred:

- Prometheus rule file write/publish;
- Prometheus reload;
- recording rule publish lifecycle and persisted state;
- Grafana dashboard JSON;
- Grafana page consumption;
- broad vendor/private metric standardization.

### 17. Recording Rule Publish Lifecycle Is Now Explicitly Closed

The backend now has an explicit by-target publish lifecycle for SNMP recording rules.

Design and plan:

```text
/OneOPS/docs/superpowers/specs/2026-06-11-snmp-recording-rule-publish-lifecycle-design.md
/OneOPS/docs/superpowers/plans/2026-06-11-snmp-recording-rule-publish-lifecycle.md
```

Current runtime fact:

```text
quick_env uses VictoriaMetrics + vmalert.
quick_env/config/vmalert/vmalert-rule.yml is mounted into vmalert as /etc/vmalert/vmalert-rule.yml.
vmalert is started with -remoteWrite.url, so recording rule results can be persisted.
```

Implemented publish flow:

```text
strategy_set_id + target_part
  -> ResolveStrategySetTargetRecordingRuleMaterializationDryRun
  -> managed rule-group merge
  -> local parse-back validation
  -> atomic file write
  -> configured vmalert reload endpoint
  -> publish record
```

Backend endpoint:

```text
POST /platform/metrics/teleabs/strategy-sets/:id/metric-contract/recording-rules/publish/by-target
```

Request:

```json
{ "target_part": "DEVICE-CODE-OR-ID" }
```

Publisher config:

```yaml
snmp_recording_rule_publisher:
  enabled: true
  backend: vmalert_file
  rule_file_path: /OneOPS/quick_env/config/vmalert/vmalert-rule.yml
  managed_group_name: oneops_snmp_recording_rules
  reload_url: http://127.0.0.1:8880/-/reload
  reload_method: GET
  request_timeout_seconds: 10
```

Implementation files:

```text
/OneOPS/OneOps/config/snmp_recording_rule_publisher.go
/OneOPS/OneOps/app/platform/platform_model/snmp_recording_rule_publish_record.go
/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go
/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go
/OneOPS/OneOps/app/platform/api/teleabs.go
/OneOPS/OneOps/app/platform/router/platform.go
/OneOPS/OneOps/app/platform/router/platform_bidi.go
/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts
/OneOPS/OneOps-UI/src/api/platform/teleabs.ts
/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-publish-smoke.ts
/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-publish-real-api-acceptance.cjs
```

Important runtime semantics:

- publish is explicit, not automatic;
- request body remains `target_part` only;
- frontend still does not infer manufacturer/platform/model/catalog/version;
- existing unmanaged rule groups are preserved;
- only the configured managed group is replaced;
- duplicate `record + expr` is deduplicated;
- duplicate `record` with different `expr` fails validation;
- reload is explicit and configured, not guessed;
- reload failure leaves status `failed_reload`;
- rollback is intentionally deferred.

Response shape:

```text
strategy_set_id
target
source
rule_group
rules[]
summary
yaml_sha256
publish
  publish_id
  backend
  rule_file_path
  managed_group_name
  rule_count
  status
  steps[]
  error_message
```

Real quick env acceptance has been verified with:

```bash
cd /OneOPS/OneOps-UI
ONEOPS_API_BASE_URL=http://127.0.0.1:18082/api/v1 \
ONEOPS_API_TOKEN="$(cat /tmp/oneops-ui-real-page-token-18082.txt)" \
npm run smoke:snmp-strategy-set-recording-rule-publish-real-api
```

Acceptance result:

```text
DVCF5A07C0AFFC9 -> status=reloaded, rule_count=12
DVC2C4468B0B813 -> status=reloaded, rule_count=12
DVCF21C6B43350C -> status=reloaded, rule_count=12
yaml_sha256=6ccbe0f8f240bf14313cbba20ac3baf74bfe86ddead0d6750c4c681daab7aeb6
```

After publishing, quick env rule file contains both:

```text
counts
oneops_snmp_recording_rules
```

The managed group contains 12 common OneOPS recording rules:

```text
oneops:cpu_usage_direct:ratio
oneops:memory_usage_direct:ratio
oneops:if_in_rate:bps
oneops:if_out_rate:bps
oneops:if_speed_bps
oneops:if_oper_status
oneops:if_in_error_rate:pps
oneops:if_out_error_rate:pps
oneops:if_in_discard_rate:pps
oneops:if_out_discard_rate:pps
oneops:if_in_broadcast_ratio:ratio
oneops:if_out_broadcast_ratio:ratio
```

Still deferred:

- automatic publish after strategy changes;
- inventory-wide aggregation;
- rollback after reload failure;
- Prometheus Operator or object-storage publishing backends;
- Grafana dashboard JSON;
- Grafana page consumption;
- broad vendor/private metric standardization.

## What The Next AI Should Verify Before Changing More UI

1. Keep the current scope fixed on the existing by-target page-level preview.
2. Re-run the focused frontend and backend verification commands before making claims.
3. Confirm the drawer calls only the by-target backend endpoint and does not infer device context locally.
4. Confirm real target samples still return expected `support_summary` and panel states.
5. Do not start Prometheus recording-rule publishing or Grafana dashboard JSON materialization in the same change.

## Important Files

Design / handoff:

- `/OneOPS/docs/superpowers/specs/2026-06-10-snmp-metric-groups-dashboard-family-design.md`
- `/OneOPS/docs/superpowers/specs/2026-06-11-snmp-recording-rule-preview-design.md`
- `/OneOPS/docs/superpowers/specs/2026-06-11-snmp-recording-rule-materialization-dry-run-design.md`
- `/OneOPS/docs/superpowers/specs/2026-06-11-snmp-recording-rule-publish-lifecycle-design.md`
- `/OneOPS/docs/superpowers/plans/2026-06-10-snmp-metric-groups-dashboard-family.md`
- `/OneOPS/docs/superpowers/plans/2026-06-11-snmp-metric-capability-contract-strict-plan.md`
- `/OneOPS/docs/superpowers/plans/2026-06-11-snmp-recording-rule-preview-closure.md`
- `/OneOPS/docs/superpowers/plans/2026-06-11-snmp-recording-rule-materialization-dry-run.md`
- `/OneOPS/docs/superpowers/plans/2026-06-11-snmp-recording-rule-publish-lifecycle.md`
- `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

Frontend contract / workbench:

- `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`
- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/StrategySetDetailDrawer.vue`
- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/snmpStrategySetTargetPanelPreview.ts`
- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricContract.ts`
- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMibProfiles.ts`
- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpWorkspaceView.ts`
- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/PluginFormSnmp.vue`
- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/SnmpMetricGroupEditor.vue`
- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/SnmpDashboardImpactPreview.vue`
- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/index.vue`

Backend alignment facts:

- `/OneOPS/OneOps/app/platform/platform_model/teleabs_strategy_set.go`
- `/OneOPS/OneOps/app/platform/dto/teleabs_strategy_set.go`
- `/OneOPS/OneOps/app/grafana/grafana_model/dashboard.go`
- `/OneOPS/OneOps/app/grafana/dto/dashboard.go`
- `/OneOPS/OneOps-UI/src/api/platform/metric-strategy.ts`

Verification scripts:

- `/OneOPS/OneOps-UI/scripts/snmp-metric-contract-smoke.ts`
- `/OneOPS/OneOps-UI/scripts/snmp-workspace-view-smoke.ts`
- `/OneOPS/OneOps-UI/scripts/snmp-profile-resolution-smoke.ts`
- `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-target-panel-preview-smoke.ts`
- `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-target-panel-preview-browser-smoke.cjs`
- `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-preview-smoke.ts`
- `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-preview-real-api-acceptance.cjs`
- `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-materialization-dry-run-smoke.ts`
- `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-materialization-dry-run-real-api-acceptance.cjs`
- `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-publish-smoke.ts`
- `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-publish-real-api-acceptance.cjs`

## Suggested First Prompt For The Next AI

```text
请阅读 /OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md，
以及 /OneOPS/docs/superpowers/plans/2026-06-11-snmp-recording-rule-publish-lifecycle.md。
当前 SNMP recording rule preview、materialization dry-run、显式 by-target publish lifecycle 已完成数据闭环。
不要扩展 Grafana、legacy YAML 解析、自动全量设备聚合、rollback 或新的厂商专项标准化。
先验证：
1. 现有 by-target 面板能力预检仍然通过；
2. quick_env H3C/Huawei/Maipu seed 仍然提供完整基础能力；
3. by-target recording rule preview 仍然生成 12/12 条记录；
4. by-target materialization dry-run 请求体只能是 target_part；
5. by-target publish 请求体只能是 target_part，发布后只替换 configured managed group；
6. 下一阶段如果继续，只能在已完成的发布闭环之后推进，仍然不要直接扩展 Grafana。
```

## Repository Notes

- `/OneOPS` is not a git repo.
- `/OneOPS/OneOps-UI` is the frontend git repo.
- The handoff doc itself lives outside the frontend repo.
- Do not revert unrelated frontend changes.
- Commit only inside `/OneOPS/OneOps-UI` if explicitly asked.

## New AI Handoff Summary For Next Session

### Current State

The SNMP common metric data loop is now closed up to explicit recording-rule publish in quick env.

Completed stages:

```text
SNMP strategy metric contract
  -> strategy-set effective contract
  -> target-based device context resolution
  -> panel capability support preview
  -> recording rule preview
  -> recording rule YAML materialization dry-run
  -> explicit by-target recording rule publish
  -> quick_env vmalert reload
```

The current implementation deliberately stops before Grafana.

### Real Publish Fact

Recording rules have been published to the current quick env runtime, not to production.

Runtime target:

```text
/OneOPS/quick_env/config/vmalert/vmalert-rule.yml
```

Rule engine:

```text
quick_env vmalert
```

Managed group:

```text
oneops_snmp_recording_rules
```

Published common rules:

```text
oneops:cpu_usage_direct:ratio
oneops:memory_usage_direct:ratio
oneops:if_in_rate:bps
oneops:if_out_rate:bps
oneops:if_speed_bps
oneops:if_oper_status
oneops:if_in_error_rate:pps
oneops:if_out_error_rate:pps
oneops:if_in_discard_rate:pps
oneops:if_out_discard_rate:pps
oneops:if_in_broadcast_ratio:ratio
oneops:if_out_broadcast_ratio:ratio
```

Acceptance result from real API:

```text
DVCF5A07C0AFFC9 -> status=reloaded, rule_count=12
DVC2C4468B0B813 -> status=reloaded, rule_count=12
DVCF21C6B43350C -> status=reloaded, rule_count=12
yaml_sha256=6ccbe0f8f240bf14313cbba20ac3baf74bfe86ddead0d6750c4c681daab7aeb6
```

### Publish Boundary

Publish is explicit only.

The publish endpoint is:

```text
POST /platform/metrics/teleabs/strategy-sets/:id/metric-contract/recording-rules/publish/by-target
```

Request body:

```json
{ "target_part": "DEVICE-CODE-OR-ID" }
```

The frontend must not infer manufacturer, platform, model, catalog, or version. The backend resolves those semantics from `platform_devices_v2` through `deviceidentity.ResolveMetadata(...)`.

The publisher only replaces the configured managed group. Existing unmanaged groups in the rule file must be preserved.

### Important Constraints For The Next AI

Do not expand scope unless the user explicitly changes direction.

Do not add:

- Grafana dashboard JSON generation;
- Grafana page consumption;
- automatic publish on strategy or device changes;
- inventory-wide aggregation;
- rollback after reload failure;
- legacy SNMP processor YAML parsing;
- Prometheus Operator or object-storage publisher;
- broad vendor/private metric standardization.

Do not introduce frontend fallback logic for device metadata. If a target cannot be resolved, the backend should return an error.

### Suggested Next Step

The best next implementation step is page-level consumption of the existing recording-rule loop in `StrategySetDetailDrawer.vue`.

Minimal page scope:

```text
strategy-set detail drawer
  -> user enters target_part
  -> panel capability preview
  -> recording rule preview
  -> materialization dry-run YAML
  -> explicit publish
  -> show publish status and steps
```

This should reuse the existing typed API wrappers:

```text
previewTeleabsStrategySetRecordingRulesByTarget(...)
materializeTeleabsStrategySetRecordingRulesByTarget(...)
publishTeleabsStrategySetRecordingRulesByTarget(...)
```

Do not make the page publish automatically. The publish action must remain a visible, explicit user action.

### Recommended Verification Before Continuing

Backend:

```bash
cd /OneOPS/OneOps
go test ./config -run '^$' -count=1
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*RecordingRule|TestMetricCapabilityContractResolver.*Publish' -count=1
go test ./app/platform/api -run 'TestTeleabsAPI_.*RecordingRulesByTarget|TestTeleabsAPI_PublishStrategySetRecordingRulesByTarget' -count=1
go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1
go test ./cmd -run '^$' -count=1
```

Frontend:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-strategy-set-recording-rule-materialization-dry-run
npm run smoke:snmp-strategy-set-recording-rule-publish
```

Quick env seed:

```bash
cd /OneOPS/quick_env
bash tests/test_sync_snmp_network_strategy_seed.sh
bash tests/test_snmp_network_strategy_seed.sh
```

Diff hygiene:

```bash
git -C /OneOPS/OneOps diff --check
git -C /OneOPS/OneOps-UI diff --check
git -C /OneOPS/quick_env diff --check
git -C /OneOPS/docs diff --check
```

### Cleanup Reminder

If a backend process is started for real API acceptance, stop it before handing off again.

Also remove generated profile files:

```bash
rm -f /OneOPS/OneOps/cpu.prof /OneOPS/OneOps/mem.prof
```
