# SNMP Metric Groups Dashboard Family Handoff

Date: 2026-06-11

## Current Objective

Continue the SNMP metric groups work as a semantic strategy editor, not as a generic SNMP raw-parameter editor.

## 2026-06-12 Progress Update

The strategy/dashboard inheritance baseline is now fixed:

- strategy runtime matches concrete copies, but metric contracts must resolve the full `parent_id` chain from root to leaf;
- SNMP metric contract resolution now needs to align with strategy apply parameter merging, especially for append/merge parameters such as `passthrough_config` and `metric_manifest`;
- dashboard trees are OneOps-side template/spec inheritance; Grafana receives independent materialized dashboard JSON.

The demo2 switch dashboard loop was validated after reparenting existing vendor/platform copies under their vendor-generic strategy:

```text
target: AST20260603174801664
matched strategy: 20000000-0000-4000-8000-000000000005
matched context: Huawei / VRP / S5735
support summary: 10 supported / 0 unsupported / 0 config_driven
saved panel bindings: 20
dashboard uid: snmp-switch-ast20260603174801-d01c0e303c
```

This confirms that a concrete Huawei S5735 copy can inherit interface, CPU, memory, fan, and power capabilities from ancestors while keeping model-specific temperature OIDs locally.

Dashboard template inheritance has also started at the pure resolver layer:

- `snmpGrafanaDashboardTemplate` applies ordered `snmpGrafanaPanelPatch` entries;
- supported patch actions are `add`, `override`, `hide`, and `move`;
- `before_panel_key` / `after_panel_key` style ordering is represented by patch anchors;
- explicit grid zero overrides are supported through pointer layout fields, so children can move panels to `x=0` without losing intent;
- the current static switch panel catalog is now treated as the root template and resolved through this same template-chain function before Grafana JSON materialization.

The materializer now consumes that chain for concrete target contexts. For `Huawei / VRP / S5735`, dry-run/save resolves:

```text
snmp.switch.root
snmp.switch.huawei.vrp
snmp.switch.huawei.vrp.s5735
```

The dry-run materialization summary exposes both `dashboard_template_key` and `dashboard_template_chain`, and the inherited panel overrides are reflected in Grafana JSON plus panel bindings.

A first persistent model now exists:

```text
platform_snmp_grafana_dashboard_template
OneOps/migrations/add_snmp_grafana_dashboard_template.sql
```

It stores `template_key`, `parent_key`, switch dashboard variant, optional target match fields, `sort_order`, `enabled`, and `patches_json`. The by-target materializer attempts to load the most specific matching DB template chain first, then falls back to the built-in switch templates when the table is absent or empty.

Quick env now has a late bootstrap seed:

```text
quick_env/docker-entrypoint-initdb.d/zzzzzzzzzz-snmp-grafana-dashboard-template-bootstrap.sql
```

The seed creates the table when needed and upserts:

```text
snmp.switch.root
snmp.switch.huawei.vrp
snmp.switch.huawei.vrp.s5735
```

The root template carries the current 20 switch-operation panel recipes. The Huawei/VRP child overrides CPU title and hides the inherited memory stat panel. The S5735 child overrides the device identity title. This closes the quick-env data anchor.

A first read-only management/diagnostic API now exposes the template tree and concrete target resolution:

```text
GET  /platform/metrics/teleabs/metric-contract/grafana/dashboard-templates
POST /platform/metrics/teleabs/metric-contract/grafana/dashboard-templates/resolve/by-target
```

The list endpoint reports either persisted DB templates or built-in fallback templates, including `template_key`, `parent_key`, match fields, patch count, and enabled state. The resolve endpoint accepts either `target_part` or a direct target context and returns the selected template key, full template chain, effective panel count, and effective panel keys. This is intentionally diagnostic/read-only; template edit API and UI are still pending.

The first write-side template management API is now also available:

```text
POST /platform/metrics/teleabs/metric-contract/grafana/dashboard-templates
```

This endpoint upserts one template node by `template_key`. It writes the OneOps-side template tree only; it does not materialize dashboard JSON, save a `grafana_dashboard` row, or sync to Grafana. Request fields cover parent key, dashboard variant, target match fields, sort order, enabled state, and `patches_json`. The backend validates that the parent exists, the node does not parent itself, and `patches_json` parses as the same `snmpGrafanaPanelPatch` array consumed by the materializer.

Frontend typed support and the first drawer entry are now connected:

- `OneOPS-UI/src/typings/platform/snmp-metric-contract.ts` defines template list, resolve, and upsert request/response types;
- `OneOPS-UI/src/api/platform/teleabs.ts` exposes `listSnmpGrafanaDashboardTemplates`, `resolveSnmpGrafanaDashboardTemplateByTarget`, and `upsertSnmpGrafanaDashboardTemplate`;
- `StrategySetDetailDrawer` now adds `加载模板树` and `解析模板链` actions beside the existing target panel preview and dashboard save/sync actions;
- `snmpGrafanaDashboardTemplateManagement.ts` keeps the reusable state helper for a future full edit UI.

This gives operators an immediate read/diagnostic surface from a real target input.

The drawer now also includes the first lightweight template-node editor:

- selecting `编辑模板` copies the row into an editable draft;
- the draft can edit template key, parent key, vendor/platform/model match fields, sort order, enabled state, and raw `patches_json`;
- `patches_json` must be an array JSON before `保存模板` calls the upsert API;
- save refreshes the template list so the updated node can be resolved again against the same target input.
- list and upsert responses now include the node's actual `patches_json`, so editing an existing node does not silently reset inherited overrides to `[]`;
- the internal patch structs now marshal with stable snake_case JSON keys such as `panel_key`, `before_panel_key`, `grid_x`, and `definition`, preserving the same format used by quick-env seed SQL and frontend raw editing.
- the management list now calls the backend with `include_disabled=true`, so a disabled template node remains visible and can be re-enabled. Runtime template resolution and dashboard materialization still use enabled templates only, so disabled nodes are not accidentally applied to generated Grafana dashboards.
- the strategy-set Grafana save summary now surfaces the materializer's `dashboard_template_key` and `dashboard_template_chain`, so an operator can see which concrete dashboard template copy was applied during save or save-and-sync without opening raw JSON.

This is intentionally a raw patch JSON editor, not a visual panel/patch builder. It manages the OneOps template tree only and still does not materialize, persist, or sync a Grafana dashboard.

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
- Real runtime matching usually lands on a concrete strategy copy. That copy must inherit parent and grandparent strategy capabilities; metric groups, recording rules, and Grafana materialization must consume the merged effective strategy, not only the leaf row.
- Dashboard families may be tree-shaped inside OneOps, but Grafana should receive an independent materialized dashboard JSON. Grafana folders and library panels can help organization/reuse, but they should not be treated as full dashboard inheritance.

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
contract_source
read_issues[]
effective_issues[]
save_mode_hint
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

Additional current semantics now implemented:

- backend `contract_source` distinguishes at least:
  - `explicit_contract`
  - `legacy_import`
  - `backend_resolver`
- backend `read_issues[]` surfaces compatibility-read or malformed explicit-contract shape problems instead of hiding them;
- backend `effective_issues[]` currently exposes degraded-save reasons such as missing OID;
- backend `save_mode_hint` distinguishes `full_sync` vs `contract_only`;
- frontend workspace now shows whether it is in:
  - backend authority mode,
  - or frontend fallback mode;
- frontend workspace also shows backend read issues explicitly instead of treating backend and fallback paths as identical.

This creates a backend/frontend data logic loop without adding UI, Prometheus publishing, or Grafana JSON generation.

Strategy-set resolver behavior:

- resolves enabled strategy-set items only;
- item with `strategy_id` reuses the strategy-level resolver;
- item without `strategy_id` can parse `default_params`;
- aggregate `effective_contract` merges non-empty item contracts in `sort_order` order;
- when no context query is provided, the endpoint keeps the enabled-item aggregate behavior;
- when context query is provided, it reuses `StrategySetMatcher` semantics to select matching strategies by catalog, manufacturer, platform, model, version, fallback, priority, and sort order;
- no automatic device inventory lookup is performed yet; the caller must pass context values explicitly.

### 8A. First-Round Contract Boundary Hardening Is Partially Landed

The current SNMP metric refactor has moved beyond "initial capability foundation" and already hardened several contract boundaries.

Frontend modules now split responsibilities more clearly:

```text
/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricContractWire.ts
/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricLegacyCodec.ts
/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricValidation.ts
```

What is already true now:

- canonical explicit persistence shape is fixed to:
  - `metric_groups: { version: 1, metric_groups: [...] }`
- frontend and backend both compatibility-read legacy bare-array explicit contract shapes;
- compatibility-read and malformed-shape cases now produce structured issues instead of silently collapsing to empty contract;
- frontend save behavior now exposes:
  - `full_sync`
  - `contract_only`
- frontend strict validation now separates:
  - `errors`
  - `warnings`
  - `degradations`
- explicit-contract reads now surface draft-only defaulting as warnings when fields such as `action`, `role`, `value_type`, `calculation`, or `visual_type` are missing;
- explicit-contract writes no longer silently invent those missing semantic defaults at persistence time;
- legacy `passthrough_config` / `metric_manifest` parsing, import, export, and exportability checks are no longer all embedded directly inside one monolithic contract file.

Important current boundary:

- read path may still normalize draft/editor data so the page remains usable;
- write path now tries to preserve missing semantic fields rather than silently writing invented defaults;
- therefore "editor convenience defaults" and "persisted contract truth" are no longer the same thing.

Focused current verification that has already been run in this state:

- frontend:
  - `npm run smoke:snmp-metric-contract`
  - `npm run smoke:snmp-metric-contract-wire`
  - `npm run smoke:snmp-workspace-view`
- backend:
  - `go test ./app/platform/service/impl -run 'TestReadExplicitSnmpMetricContract|TestMetricCapabilityContractResolverSurfacesStrategyContractMetadata|TestMetricCapabilityContractResolverResolvesStrategyContractFromFullParentChain' -count=1`

Historical limitation at this stage of the refactor:

- `npm run typecheck` had not yet returned within the waiting window at this point in time. That later got resolved during the OID online-test slice; see the later verification notes where `npm run typecheck` is confirmed passing.

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

### 18. Grafana Dashboard Materialization Dry-Run Is Now Opened

The first Grafana-facing stage is now a strict by-target dry-run only.

New backend endpoint:

```text
POST /platform/metrics/teleabs/strategy-sets/:id/metric-contract/grafana/dashboards/materialize/dry-run/by-target
```

Request:

```json
{ "target_part": "DEVICE-CODE-OR-ID" }
```

Current dry-run flow:

```text
strategy_set_id + target_part
  -> by-target panel capability preview
  -> by-target recording rule preview
  -> pure Grafana dashboard JSON materializer
  -> local JSON validation
  -> panel binding preview
```

Response includes:

```text
strategy_set_id
target
source
item_contracts[]
effective_contract
supports[]
support_summary
rule_group
rules[]
recording_rule_summary
dashboard
dashboard_json
panel_bindings[]
materialization
```

`materialization` contains:

```text
format = grafana_dashboard_json
dry_run = true
panel_count
binding_count
json_bytes
valid
validation_errors[]
```

Strict boundary:

- request body remains `target_part` only;
- no frontend manufacturer/platform/model/catalog/version inference is introduced;
- no `grafana_dashboard` row is created or updated;
- no `syncToGrafana` call is made;
- no dashboard diff is computed;
- no panel binding is persisted;
- unsupported panels are left out of generated `dashboard.panels` but remain visible in `supports[]`.

The generated panel binding preview carries:

```text
panel_key
panel_id
title
strategy_set_id
strategy_ids[]
metric_group_key
metric_keys[]
selected_capability_keys[]
record_names[]
managed_state = preview
content_hash
```

Implemented files:

```text
/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go
/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go
/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go
/OneOPS/OneOps/app/platform/api/teleabs.go
/OneOPS/OneOps/app/platform/router/platform.go
/OneOPS/OneOps/app/platform/router/platform_bidi.go
/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts
/OneOPS/OneOps-UI/src/api/platform/teleabs.ts
/OneOPS/OneOps-UI/scripts/snmp-strategy-set-grafana-dashboard-materialization-dry-run-smoke.ts
```

Focused verification:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolverMaterializesGrafanaDashboardJSON|TestMetricCapabilityContractResolverMaterializesStrategySetGrafanaDashboardByTarget' -count=1
go test ./app/platform/api -run TestTeleabsAPI_MaterializeStrategySetGrafanaDashboardByTarget_HTTP -count=1
go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1

cd /OneOPS/OneOps-UI
npm run smoke:snmp-strategy-set-grafana-dashboard-materialization-dry-run
```

Still deferred:

- writing generated JSON to `grafana_dashboard`;
- syncing generated JSON to Grafana;
- dashboard diff and rollback;
- persisted panel binding table;
- page-level Grafana materialization controls;
- automatic generation after strategy or recording-rule publish.

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

Additional hardening that is now landed for the Grafana path:

```text
Grafana dry-run/save
  -> explicit dashboard_variant request
  -> variant-aware current-instance ownership at application logic level
  -> deterministic template ambiguity failure
  -> variant-aware target binding / panel binding persistence
```

Canonical current dashboard owner key should now be treated as:

```text
strategy_set_id + target_part + dashboard_variant
```

Current implementation-level meaning:

- `StrategySet` still owns semantic capability resolution;
- dashboard templates still resolve as a single inheritance chain per variant;
- saved dashboard instances are now intended to be variant-aware, not just target-aware;
- `panel_key` remains the stable bridge from contract-side panel semantics to materialized dashboard panel bindings.

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

The current publish channel is real but still narrow:

```text
backend = vmalert_file
managed group replacement
rule file write
reload endpoint call
publish record persistence
```

The write path now uses temp-file replacement semantics instead of direct truncate-in-place overwrite.

The `save-and-sync` Grafana path now also persists the target-binding state transition after external sync succeeds:

- API `save-and-sync` no longer only flips the response body to `Enabled`;
- backend now explicitly updates `platform_teleabs_strategy_set_dashboard_target_binding.dashboard_state`;
- owner lookup remains variant-aware: `strategy_set_id + target_part + dashboard_variant`.

The older Grafana materialization tests that still hard-coded the pre-expansion default panel-requirement count (`21`) have now been reconciled with the current catalog-driven behavior:

- broader support/materialization tests now follow `DefaultPanelCapabilityRequirements()` instead of pinning the old count;
- the minimal H3C materialization fixture now asserts the currently rendered throughput panel instead of the older utilization-only assumption;
- this closes the previously known “21 vs 33” test drift for the targeted resolver suite.

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

Do not regress these newly hardened boundaries:

- do not remove explicit `dashboard_variant` from Grafana dry-run/save request paths;
- do not collapse dashboard ownership back to `strategy_set_id + target_part` only;
- do not silently choose one dashboard template when multiple same-priority candidates match;
- do not revert recording-rule file replacement back to truncate-write semantics.

Do not introduce frontend fallback logic for device metadata. If a target cannot be resolved, the backend should return an error.

### 20. Strategy-Set Detail Drawer Now Consumes The Recording-Rule Loop

The minimal page-level consumption for by-target recording rules is now wired into `StrategySetDetailDrawer.vue`.

Within the existing target preview block, the drawer now exposes three explicit actions:

```text
preview rules
materialize YAML
publish rules
```

The same `target_part` input is reused across:

```text
panel capability preview
recording rule preview
recording rule YAML materialization dry-run
explicit recording rule publish
```

The drawer now renders:

- recording-rule summary cards;
- a rule table;
- materialized YAML;
- publish steps / backend / managed-group status.

This page-level integration reuses the existing typed frontend wrappers:

```text
previewTeleabsStrategySetRecordingRulesByTarget(...)
materializeTeleabsStrategySetRecordingRulesByTarget(...)
publishTeleabsStrategySetRecordingRulesByTarget(...)
```

The publish action remains explicit and user-triggered; no automatic publish behavior was added.

New frontend files added for this page-level closure:

- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/snmpStrategySetRecordingRuleState.ts`
- `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-state-smoke.ts`
- `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-drawer-smoke.ts`

Additional verification completed for this page layer:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-strategy-set-recording-rule-drawer
npm run smoke:snmp-strategy-set-recording-rule-state
npm run smoke:snmp-strategy-set-recording-rule-preview
npm run smoke:snmp-strategy-set-recording-rule-materialization-dry-run
npm run smoke:snmp-strategy-set-recording-rule-publish
git diff --check
```

The next most natural product-facing step is no longer recording-rule page consumption.
It is the SNMP metric-group workflow itself:

```text
select group
fill OID
test OID inline
repair failures
save strategy
```

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

## 2026-06-12 Update: Grafana Switch Dashboard Direction Is Now Open

The earlier boundary said not to expand Grafana. That boundary has changed by explicit user direction.

New direction:

```text
SNMP Grafana materialization should continue,
but the screenshot-inspired dashboard style is primarily for network switches.
```

The screenshot should be treated as a switch operations dashboard variant, not a universal SNMP dashboard template.

New spec:

```text
docs/superpowers/specs/2026-06-12-snmp-grafana-dashboard-screenshot-alignment-design.md
```

New implementation plan:

```text
docs/superpowers/plans/2026-06-12-snmp-grafana-screenshot-style-materializer.md
```

Current accepted product/design interpretation:

```text
variant: snmp.switch.operations
primary target: network switch
primary principle: integrate with the existing strategy set / strategy / capability-contract data logic
primary workflow:
  identify device
  -> decide urgency
  -> locate saturated/faulty port
  -> inspect trend/correlation
  -> collect evidence for ownership and next action
```

The switch variant should prioritize:

- device identity and data freshness;
- health KPI strip;
- CPU and memory current values plus trends;
- interface utilization top-N;
- port status map or status-history;
- throughput trend;
- interface quality hotspot table;
- broadcast/non-unicast ratio where supported;
- optional hardware health later when sensor capabilities are modeled.

The most important point is not visual similarity. The dashboard must be materialized from the already implemented data logic:

```text
target_part
  -> platform_devices_v2
  -> deviceidentity.ResolveMetadata(...)
  -> StrategySetMatcher
  -> matched TeleabsStrategySet items
  -> TeleabsStrategy parent/child/effective contract
  -> supports[] / support_summary
  -> recording rule preview rules[]
  -> switch panel catalog
  -> dashboard_json + panel_bindings[]
```

Do not create a standalone dashboard template that bypasses:

- target context normalization;
- strategy-set selector logic;
- strategy parent/child inheritance;
- effective SNMP metric capability contract;
- panel capability support;
- recording-rule preview;
- panel binding traceability.

Do not force this layout onto:

- servers;
- BMC/OOB devices;
- generic SNMP devices;
- routers/firewalls/load balancers without a dedicated variant decision.

Those should use future variants or a smaller capability-driven fallback.

Quick sample already produced in demo2 Grafana:

```text
http://127.0.0.1:3300/d/oneops-snmp-screenshot-style-sample/oneops-snmp-screenshot-style-sample
```

Sample facts:

- datasource: `VictoriaMetrics`;
- dashboard uid: `oneops-snmp-screenshot-style-sample`;
- panel count: `19`;
- panel types: `text`, `stat`, `timeseries`, `table`, `status-history`, `piechart`;
- data is simulated VictoriaMetrics sample data, not real SNMP collection.

Next implementation should follow:

```text
docs/superpowers/plans/2026-06-12-snmp-grafana-screenshot-style-materializer.md
```

Boundary for next implementation:

- keep strict by-target dry-run route;
- add switch variant metadata and section-aware panel catalog;
- do not persist dashboards;
- do not call `syncToGrafana`;
- do not add real alert/event/compliance joins in this pass;
- do not implement a custom Canvas port map in this pass.

## 2026-06-12 Implementation Update: Switch Dashboard Dry-Run Materializer

The switch dashboard direction has now moved from design/sample into the backend dry-run materializer.

Implemented behavior:

- the by-target Grafana dry-run still uses the existing authoritative chain: target metadata, StrategySet matching, effective contract, panel support preview, and recording-rule preview;
- dashboard variant is fixed to `snmp.switch.operations` for this pass;
- panels are rendered from a switch panel catalog only when the required capability keys and recording rules are available;
- unsupported panels are omitted and reported in `materialization.skipped_panel_keys`;
- rendered panels are reported in `materialization.rendered_panel_keys`;
- panel bindings now carry `dashboard_variant`, `section_key`, `display_intent`, `visual_type`, and `render_policy`;
- the identity panel is always rendered from target context and carries no metric/record binding;
- metric panels keep strategy-set, strategy id, metric group, capability, and record-name traceability.

Current switch dry-run panel catalog includes:

- `device.identity`;
- `system_basic.cpu.stat`;
- `system_basic.memory.stat`;
- `interface_basic.traffic_mix`;
- `interface_basic.port_up_count`;
- `interface_basic.port_down_count`;
- `interface_basic.error_port_count`;
- `interface_basic.discard_port_count`;
- `interface_basic.utilization`;
- `interface_basic.port_state`;
- `system_basic.cpu_memory.trend`;
- `interface_basic.throughput`;
- `interface_basic.quality_hotspots`;
- `interface_basic.broadcast`.

Important boundaries still hold:

- no `grafana_dashboard` persistence;
- no `syncToGrafana`;
- no dashboard diff;
- no automatic publish;
- no real alert/event/compliance/routing joins;
- no custom Canvas port-map plugin.

Verification run:

```bash
cd OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*GrafanaDashboard|TestMetricCapabilityContractResolver.*RecordingRule' -count=1
go test ./app/platform/api -run 'TestTeleabsAPI_.*GrafanaDashboard' -count=1
go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1
go test ./cmd -run '^$' -count=1

cd ../OneOPS-UI
npm run smoke:snmp-strategy-set-grafana-dashboard-materialization-dry-run
npm run typecheck
```

## 2026-06-12 Quick Env Verification: Real Switch Target Imported To Grafana

The local quick env was restarted with the latest OneOps code and the by-target dry-run was verified against a real loaded Device V2 switch target:

- OneOps API: `http://127.0.0.1:8380`;
- Grafana: `http://127.0.0.1:3300`;
- datasource: `VictoriaMetrics`, uid `victoriametrics`;
- strategy set: `4284353d-1233-4022-ad18-871b3d8444c7`;
- target: `AST20260603174801664`;
- target context: `SWITCH / H3C / Comware / S5735 / 7.1`;
- metadata source: `platform_devices_v2`.

Dry-run result:

- `dashboard_variant`: `snmp.switch.operations`;
- `panel_count`: `9`;
- `binding_count`: `9`;
- rendered panel keys:
  - `device.identity`;
  - `system_basic.cpu.stat`;
  - `system_basic.memory.stat`;
  - `interface_basic.traffic_mix`;
  - `interface_basic.port_up_count`;
  - `interface_basic.port_down_count`;
  - `interface_basic.error_port_count`;
  - `interface_basic.discard_port_count`;
  - `interface_basic.utilization`;
  - `interface_basic.port_state`;
  - `system_basic.cpu_memory.trend`;
  - `interface_basic.throughput`;
  - `interface_basic.quality_hotspots`;
  - `interface_basic.broadcast`.

Grafana import result:

```text
http://127.0.0.1:3300/d/snmp-switch-ast3174801664/oneops-snmp-switch-ops-ast20260603174801664
```

Imported dashboard facts:

- uid: `snmp-switch-ast3174801664`;
- title: `OneOPS SNMP Switch Ops - AST20260603174801664`;
- panel count read back from Grafana API: `9`;
- panel types: `text`, `stat`, `table`, `status-history`, `timeseries`.

## 2026-06-12 Update: Dashboard Save Closure And Quick Env Target Context Fix

The Grafana switch dashboard closure now has a real persistence path, not only dry-run/import testing.

New save endpoint:

```text
POST /platform/metrics/teleabs/strategy-sets/:id/metric-contract/grafana/dashboards/save/by-target
```

Current behavior:

- resolves target context from `platform_devices_v2`;
- matches the strategy set through the existing strategy-set matcher;
- resolves inherited/effective SNMP capability contracts;
- materializes Grafana dashboard JSON through the backend resolver;
- upserts `grafana_dashboard` with a stable dashboard uid/code;
- upserts `platform_teleabs_strategy_set_dashboard_binding`;
- does not call `syncToGrafana`.

Quick env had a concrete closure gap: the existing Device V2 seed row for target `AST20260603174801664` existed, but did not contain enough normalized context for the by-target resolver. The missing fields were:

- `manufacturer_name`;
- `platform_name`;
- `system_version`.

Because `ResolveTargetContext` requires the normalized target profile, the real save API previously failed with:

```text
target context missing required fields: manufacturer_name, platform_name, system_version
```

This is now fixed in `quick_env/start.sh`.

New quick env startup sync:

```text
sync_snmp_switch_device_context_records
```

It runs before optional data loading and idempotently patches/inserts the SNMP switch demo target into:

- `UniOPS`;
- `zb_firewall`;
- `zb_firewall_122`.

Current normalized demo target context:

```text
target: AST20260603174801664
catalog: SWITCH / CATL20231020001
manufacturer: Huawei
platform: VRP / PLT20231020016
model: S5735 / TYP20240628000003
system_version: V200R021C10
function_area: DefaultArea
```

The current running quick env database was also patched in-place, so the save endpoint now succeeds against port `8380`.

Verified real save result:

```text
strategy_set_id: 4284353d-1233-4022-ad18-871b3d8444c7
target: AST20260603174801664
dashboard_code: GDBSNMP3E6A64DC49CDE413A4C27D84
dashboard_uid: snmp-switch-ast20260603174801-d01c0e303c
dashboard_title: OneOPS SNMP Switch Ops - AST20260603174801664
grafana_dashboard.state: Disabled
platform_teleabs_strategy_set_dashboard_binding rows: 1
```

Idempotency was verified by calling the save endpoint twice:

```text
grafana_dashboard rows for uid: 1
strategy-set dashboard binding rows: 1
```

This closes the first platform-side persistence loop:

```text
quick env seed target
  -> platform_devices_v2 normalized target context
  -> strategy set
  -> metric capability contract
  -> dashboard materialization
  -> grafana_dashboard
  -> strategy-set dashboard binding
```

Remaining closure gaps:

- the saved dashboard is still `Disabled` and not synced to Grafana automatically;
- there is still no diff/preview/rollback lifecycle for persisted dashboards;
- the dashboard binding is currently at strategy-set level, not variant/profile/target level;
- alert/event/compliance/routing data from the screenshot is not yet backed by real joined platform data;
- hardware health panels require modeled sensor/fan/PSU capability contracts before they should be generated;
- the frontend still needs a deliberate action surface for "dry-run -> save -> later sync/import".

Verification commands used for this update:

```bash
cd quick_env
python3 tests/test_seed_template_guard.py -v -k snmp_switch_device_context

cd ../OneOps
go run main.go

curl -H 'Content-Type: application/json' \
  -H 'X-Auth-Token: abc123' \
  -X POST \
  http://127.0.0.1:8380/api/v1/platform/metrics/teleabs/strategy-sets/4284353d-1233-4022-ad18-871b3d8444c7/metric-contract/grafana/dashboards/save/by-target \
  -d '{"target_part":"AST20260603174801664"}'
```

Important data note:

- Grafana layout and PromQL bindings are imported;
- the current VictoriaMetrics query for `oneops:cpu_usage_direct:ratio` returned `0` series during this verification;
- this means quick env still needs recording-rule publication and/or real SNMP sample ingestion before the dashboard shows live curves instead of empty panels.

Follow-up implementation note:

- A real quick-env mismatch was found where support preview selected representative keys such as `if_in_error_rate` and `if_in_broadcast_ratio`, while recording-rule preview had both in/out records.
- The materializer was adjusted so a switch panel capability may be satisfied by either support-selected capability keys or existing recording-rule records.
- This keeps panel rendering aligned with the existing StrategySet/support/recording-rule chain instead of requiring support preview to list every derived record key.

## 2026-06-12 Quick Env Update: Switch Dashboard Now Has Sample Series

To make the imported switch operations dashboard immediately visible in Grafana, synthetic VictoriaMetrics sample series were loaded into the current quick env runtime.

Dashboard URL:

```text
http://127.0.0.1:3300/d/snmp-switch-ast3174801664/oneops-snmp-switch-ops-ast20260603174801664
```

Sample import facts:

- VictoriaMetrics host port: `9390`;
- Grafana datasource uid: `victoriametrics`;
- sample file generated at: `/tmp/oneops-snmp-switch-ops-sample.prom`;
- imported line count: `5002`;
- import endpoint: `POST http://127.0.0.1:9390/api/v1/import/prometheus`;
- import result: HTTP `204`.

Verified query results:

```bash
curl -sS --get 'http://127.0.0.1:9390/api/v1/query' \
  --data-urlencode 'query=oneops:cpu_usage_direct:ratio'
```

- result count: `1`;
- sample metric labels: `device_code="AST20260603174801664"`, `device_name="H3C-S5735-Demo"`, `agent_host="192.168.106.68"`.

```bash
curl -sS --get 'http://127.0.0.1:9390/api/v1/query' \
  --data-urlencode 'query=topk(10, max by (ifDescr, ifAlias) (oneops:if_in_rate:bps / oneops:if_speed_bps))'
```

- result count: `8`;
- sample interface labels: `ifDescr="GigabitEthernet1/0/8"`, `ifAlias="access-8"`.

Grafana datasource proxy was also verified:

```bash
curl -sS --get 'http://127.0.0.1:3300/api/datasources/proxy/uid/victoriametrics/api/v1/query' \
  --data-urlencode 'query=oneops:cpu_usage_direct:ratio' \
  -u admin:admin
```

- result count: `1`.

Important boundary:

- this is synthetic quick-env data for visual/dashboard smoke only;
- it does not prove live SNMP collection, Telegraf ingestion, or vmalert recording-rule evaluation;
- the dashboard itself is still imported manually from the dry-run output and is not persisted through `grafana_dashboard` or synced through `syncToGrafana`.

## 2026-06-12 Quick Env Update: Traffic Mix Pie Panel Added

The switch operations dry-run materializer now includes a composition panel:

- panel key: `interface_basic.traffic_mix`;
- title: `Traffic Mix`;
- Grafana type: `piechart`;
- display intent: `composition`;
- required capabilities: `if_in_broadcast_ratio`, `if_out_broadcast_ratio`;
- data source: existing recording-rule records, not new raw SNMP fields.

The panel intentionally stays inside the current data logic:

```text
StrategySet/Strategy passthrough
  -> capability support
  -> recording-rule preview
  -> oneops:if_in_broadcast_ratio:ratio
  -> oneops:if_out_broadcast_ratio:ratio
  -> Grafana piechart targets
```

It renders two slices:

- `Broadcast / Non-Unicast`: average of inbound/outbound broadcast or non-unicast ratio;
- `Other Traffic`: `1 - Broadcast / Non-Unicast`.

Real quick env dry-run result after restarting OneOps on `8380`:

- `panel_count`: `10`;
- `binding_count`: `10`;
- rendered panel keys include `interface_basic.traffic_mix`;
- panel types include `piechart`, `stat`, `status-history`, `table`, `text`, and `timeseries`.

Grafana was overwritten on the same UID:

```text
http://127.0.0.1:3300/d/snmp-switch-ast3174801664/oneops-snmp-switch-ops-ast20260603174801664
```

Grafana API readback:

- uid: `snmp-switch-ast3174801664`;
- version: `2`;
- panel count: `10`;
- panel titles now include `Traffic Mix`.

Synthetic sample data was shifted to the current time and re-imported:

- shifted file: `/tmp/oneops-snmp-switch-ops-sample-current.prom`;
- imported line count: `5002`;
- import result: HTTP `204`.

Verified query results:

```bash
curl -sS --get 'http://127.0.0.1:9390/api/v1/query' \
  --data-urlencode 'query=clamp_min(clamp_max(avg((oneops:if_in_broadcast_ratio:ratio + oneops:if_out_broadcast_ratio:ratio) / 2), 1), 0)'
```

- result count: `1`;
- sample value: approximately `0.0307`.

```bash
curl -sS --get 'http://127.0.0.1:9390/api/v1/query' \
  --data-urlencode 'query=clamp_min(1 - (clamp_min(clamp_max(avg((oneops:if_in_broadcast_ratio:ratio + oneops:if_out_broadcast_ratio:ratio) / 2), 1), 0)), 0)'
```

- result count: `1`;
- sample value: approximately `0.9693`.

The same broadcast/non-unicast query also returns `1` result through Grafana datasource proxy.

Important boundary:

- this is a useful visual approximation of the screenshot's traffic-mix donut;
- true unicast/broadcast/multicast split still needs dedicated packet-ratio capabilities before it can be represented literally;
- no new dashboard persistence, `syncToGrafana`, or automatic publication was added.

## 2026-06-12 Quick Env Update: Port Up/Down KPI Panels Added

The switch operations dry-run materializer now includes two immediate port-state KPI panels:

- `interface_basic.port_up_count`
  - title: `Ports Up`;
  - Grafana type: `stat`;
  - capability: `if_oper_status`;
  - expression: `count(oneops:if_oper_status == 1) or vector(0)`.
- `interface_basic.port_down_count`
  - title: `Ports Down`;
  - Grafana type: `stat`;
  - capability: `if_oper_status`;
  - expression: `count(oneops:if_oper_status != 1) or vector(0)`.

Why this belongs in the switch variant:

- network operators check interface availability before reading detailed traffic curves;
- it uses the same `if_oper_status` recording rule as the existing port state map;
- it adds a fast top-row triage signal without adding new SNMP fields, raw PromQL shortcuts, or a vendor-specific branch.

Real quick env dry-run result after restarting OneOps on `8380`:

- `panel_count`: `12`;
- `binding_count`: `12`;
- rendered panel keys include `interface_basic.port_up_count` and `interface_basic.port_down_count`;
- panel titles include `Ports Up` and `Ports Down`.

Grafana was overwritten on the same UID:

```text
http://127.0.0.1:3300/d/snmp-switch-ast3174801664/oneops-snmp-switch-ops-ast20260603174801664
```

Grafana API readback:

- uid: `snmp-switch-ast3174801664`;
- version: `3`;
- panel count: `12`;
- panel types: `piechart`, `stat`, `status-history`, `table`, `text`, `timeseries`.

Synthetic sample data was shifted to the current time and re-imported:

- shifted file: `/tmp/oneops-snmp-switch-ops-sample-current.prom`;
- imported line count: `5002`;
- import result: HTTP `204`.

Verified query results:

```bash
curl -sS --get 'http://127.0.0.1:9390/api/v1/query' \
  --data-urlencode 'query=count(oneops:if_oper_status == 1) or vector(0)'
```

- result count: `1`;
- sample value: `7`.

```bash
curl -sS --get 'http://127.0.0.1:9390/api/v1/query' \
  --data-urlencode 'query=count(oneops:if_oper_status != 1) or vector(0)'
```

- result count: `1`;
- sample value: `1`.

The `Ports Up` expression also returns `1` result through Grafana datasource proxy.

Important boundary:

- `Ports Down` currently means non-up `ifOperStatus`, not only administratively down;
- a future panel can split `down/testing/dormant/notPresent/lowerLayerDown` if the product needs richer IF-MIB state semantics;
- dashboard persistence and Grafana sync remain outside this dry-run-only phase.

## 2026-06-12 Quick Env Update: Error/Discard Port KPI Panels Added

The switch operations dry-run materializer now includes two immediate interface-quality KPI panels:

- `interface_basic.error_port_count`
  - title: `Error Ports`;
  - Grafana type: `stat`;
  - capabilities: `if_in_error_rate`, `if_out_error_rate`;
  - expression: `count(max by (ifDescr, ifAlias) (oneops:if_in_error_rate:pps + oneops:if_out_error_rate:pps) > 0) or vector(0)`.
- `interface_basic.discard_port_count`
  - title: `Discard Ports`;
  - Grafana type: `stat`;
  - capabilities: `if_in_discard_rate`, `if_out_discard_rate`;
  - expression: `count(max by (ifDescr, ifAlias) (oneops:if_in_discard_rate:pps + oneops:if_out_discard_rate:pps) > 0) or vector(0)`.

Why this belongs in the switch variant:

- operators need a top-level quality signal before opening the detailed hotspot table;
- the panels reuse existing recording rules and capability gating;
- no new raw SNMP inputs, dashboard-side vendor matching, or alert/event joins were added.

Real quick env dry-run result after restarting OneOps on `8380`:

- `panel_count`: `14`;
- `binding_count`: `14`;
- rendered panel keys include `interface_basic.error_port_count` and `interface_basic.discard_port_count`;
- panel titles include `Error Ports` and `Discard Ports`.

Grafana was overwritten on the same UID:

```text
http://127.0.0.1:3300/d/snmp-switch-ast3174801664/oneops-snmp-switch-ops-ast20260603174801664
```

Grafana API readback:

- uid: `snmp-switch-ast3174801664`;
- version: `4`;
- panel count: `14`;
- panel types: `piechart`, `stat`, `status-history`, `table`, `text`, `timeseries`.

Verified query results:

```bash
curl -sS --get 'http://127.0.0.1:9390/api/v1/query' \
  --data-urlencode 'query=count(max by (ifDescr, ifAlias) (oneops:if_in_error_rate:pps + oneops:if_out_error_rate:pps) > 0) or vector(0)'
```

- result count: `1`;
- sample value: `0`.

```bash
curl -sS --get 'http://127.0.0.1:9390/api/v1/query' \
  --data-urlencode 'query=count(max by (ifDescr, ifAlias) (oneops:if_in_discard_rate:pps + oneops:if_out_discard_rate:pps) > 0) or vector(0)'
```

- result count: `1`;
- sample value: `0`.

The `Error Ports` expression also returns `1` result through Grafana datasource proxy.

Important boundary:

- these are quality indicators, not alert records;
- thresholding is panel-local for visualization only and does not create alert policy;
- future alert/event panels should join a real alert model instead of inferring alerts from these stat panels.

## 2026-06-12 Quick Env Update: Grafana PromQL Is Now Target-Scoped

The switch operations dry-run materializer now scopes Grafana PromQL to the resolved target device.

Why this matters:

- the dry-run API is by target, so the generated dashboard must not aggregate all devices that share the same recording-rule names;
- without label scoping, a multi-switch VictoriaMetrics dataset would mix CPU, memory, traffic, status, quality, and broadcast series across devices;
- this fix keeps dashboard materialization aligned with the existing strict target-resolution chain.

Implementation behavior:

- Grafana expressions now wrap each recording-rule record with `device_code="<resolved device code>"`;
- fallback target identity is `DeviceCode`, then `TargetPart`, then `DeviceID`;
- panel bindings still retain original recording-rule names such as `oneops:if_in_rate:bps`;
- only dashboard query expressions are scoped.

Example before:

```text
topk(10, max by (ifDescr, ifAlias) (oneops:if_in_rate:bps / oneops:if_speed_bps))
```

Example after:

```text
topk(10, max by (ifDescr, ifAlias) (oneops:if_in_rate:bps{device_code="AST20260603174801664"} / oneops:if_speed_bps{device_code="AST20260603174801664"}))
```

Real quick env dry-run result after restarting OneOps on `8380`:

- `panel_count`: `14`;
- `binding_count`: `14`;
- first generated expression: `oneops:cpu_usage_direct:ratio{device_code="AST20260603174801664"}`;
- dashboard JSON contains `device_code="AST20260603174801664"`;
- dashboard JSON no longer contains the unscoped utilization expression `oneops:if_in_rate:bps / oneops:if_speed_bps`.

Grafana was overwritten on the same UID:

```text
http://127.0.0.1:3300/d/snmp-switch-ast3174801664/oneops-snmp-switch-ops-ast20260603174801664
```

Grafana API readback:

- uid: `snmp-switch-ast3174801664`;
- version: `5`;
- panel count: `14`;
- first expression: `oneops:cpu_usage_direct:ratio{device_code="AST20260603174801664"}`.

Synthetic sample data was shifted to the current time and re-imported:

- shifted file: `/tmp/oneops-snmp-switch-ops-sample-current.prom`;
- imported line count: `5002`;
- import result: HTTP `204`.

Verified scoped query results:

```bash
curl -sS --get 'http://127.0.0.1:9390/api/v1/query' \
  --data-urlencode 'query=oneops:cpu_usage_direct:ratio{device_code="AST20260603174801664"}'
```

- result count: `1`.

```bash
curl -sS --get 'http://127.0.0.1:9390/api/v1/query' \
  --data-urlencode 'query=topk(10, max by (ifDescr, ifAlias) (oneops:if_in_rate:bps{device_code="AST20260603174801664"} / oneops:if_speed_bps{device_code="AST20260603174801664"}))'
```

- result count: `8`.

The scoped interface-utilization query also returns `8` results through Grafana datasource proxy.

Important boundary:

- this assumes collected/recorded series carry a stable `device_code` label;
- if future pipelines use another canonical device label, the materializer should centralize the label key rather than hard-code panel-specific filters;
- this change still does not persist dashboards or call `syncToGrafana`.

## 2026-06-12 Quick Env Update: Device Scope Uses Grafana Variable

The switch operations dry-run materializer now expresses device scoping through a Grafana dashboard variable instead of hard-coding the target device code in every query.

Why this matters:

- the dashboard remains single-target by default, but the filter is centralized;
- future save/sync/import flows can override or inspect one variable instead of rewriting every PromQL expression;
- generated panel expressions are easier to diff and less noisy.

Generated dashboard variable:

```json
{
  "name": "device_code",
  "type": "constant",
  "label": "Device Code",
  "query": "AST20260603174801664",
  "current": {
    "text": "AST20260603174801664",
    "value": "AST20260603174801664"
  },
  "hide": 2
}
```

Example query:

```text
oneops:cpu_usage_direct:ratio{device_code="$device_code"}
```

Real quick env dry-run result after restarting OneOps on `8380`:

- `panel_count`: `14`;
- `binding_count`: `14`;
- variable `device_code` exists with current value `AST20260603174801664`;
- first generated expression: `oneops:cpu_usage_direct:ratio{device_code="$device_code"}`;
- dashboard JSON contains `device_code="$device_code"`;
- dashboard JSON no longer hard-codes `device_code="AST20260603174801664"` inside query expressions.

Grafana was overwritten on the same UID:

```text
http://127.0.0.1:3300/d/snmp-switch-ast3174801664/oneops-snmp-switch-ops-ast20260603174801664
```

Grafana API readback:

- uid: `snmp-switch-ast3174801664`;
- version: `6`;
- panel count: `14`;
- variable `device_code` current value: `AST20260603174801664`;
- first expression: `oneops:cpu_usage_direct:ratio{device_code="$device_code"}`.

Synthetic sample data was shifted to the current time and re-imported:

- shifted file: `/tmp/oneops-snmp-switch-ops-sample-current.prom`;
- imported line count: `5002`;
- import result: HTTP `204`.

Verified query results after substituting the variable value:

```bash
curl -sS --get 'http://127.0.0.1:9390/api/v1/query' \
  --data-urlencode 'query=oneops:cpu_usage_direct:ratio{device_code="AST20260603174801664"}'
```

- result count: `1`.

The scoped interface-utilization query also returns `8` results through Grafana datasource proxy.

Important boundary:

- `device_code` is currently a hidden constant because this dashboard is generated by strict by-target dry-run;
- a future multi-device or reusable dashboard variant can expose a query/custom variable, but that should be a separate variant decision;
- this change still does not persist dashboards or call `syncToGrafana`.

## 2026-06-12 Quick Env Update: Datasource Variable Added To Generated Dashboard

The switch operations dry-run materializer now emits Grafana datasource references directly in the generated dashboard JSON.

Why this matters:

- previous quick-env imports needed a jq step that injected `datasource: {type:"prometheus", uid:"victoriametrics"}` into each target;
- that import-only patch would not exist when the dashboard is later persisted through `grafana_dashboard` or synced through `syncToGrafana`;
- generated dashboard JSON should be self-contained enough for Grafana import.

Generated datasource variable:

```json
{
  "name": "datasource",
  "type": "datasource",
  "label": "Datasource",
  "query": "prometheus",
  "current": {
    "text": "Prometheus",
    "value": "Prometheus"
  }
}
```

Generated panel and target datasource reference:

```json
{
  "type": "prometheus",
  "uid": "${datasource}"
}
```

Real quick env dry-run result after restarting OneOps on `8380`:

- `panel_count`: `14`;
- `binding_count`: `14`;
- variables: `datasource`, `device_code`;
- first panel datasource: `{type:"prometheus", uid:"${datasource}"}`;
- first target datasource: `{type:"prometheus", uid:"${datasource}"}`;
- first expression remains `oneops:cpu_usage_direct:ratio{device_code="$device_code"}`.

Grafana was overwritten on the same UID using the generated dashboard JSON without target datasource injection:

```text
http://127.0.0.1:3300/d/snmp-switch-ast3174801664/oneops-snmp-switch-ops-ast20260603174801664
```

Grafana API readback:

- uid: `snmp-switch-ast3174801664`;
- version: `7`;
- panel count: `14`;
- variables: `datasource`, `device_code`;
- first panel datasource: `{type:"prometheus", uid:"${datasource}"}`;
- first target datasource: `{type:"prometheus", uid:"${datasource}"}`.

Synthetic sample data was shifted to the current time and re-imported:

- shifted file: `/tmp/oneops-snmp-switch-ops-sample-current.prom`;
- imported line count: `5002`;
- import result: HTTP `204`.

Verified query results:

- `oneops:cpu_usage_direct:ratio{device_code="AST20260603174801664"}` returns `1` result from VictoriaMetrics;
- scoped interface utilization returns `8` results through Grafana datasource proxy.

Important boundary:

- the datasource variable follows existing OneOps Grafana template style and queries `prometheus`;
- quick env resolves this to the VictoriaMetrics datasource because it is Prometheus-compatible;
- this still does not persist dashboards or call `syncToGrafana`.

## 2026-06-12 Quick Env Update: Stable Dashboard UID And Switch Title

The switch operations dry-run materializer now emits a stable Grafana dashboard identity directly in the generated dashboard JSON.

Generated dashboard fields:

```json
{
  "uid": "snmp-switch-ast20260603174801-d01c0e303c",
  "title": "OneOPS SNMP Switch Ops - AST20260603174801664",
  "id": null
}
```

Why this matters:

- previous quick-env imports still patched `uid`, `title`, and `id` in the import payload;
- future `grafana_dashboard` persistence and `syncToGrafana` need a stable dashboard identity from the materializer itself;
- the generated UID is short enough for Grafana and includes a hash suffix to avoid collisions.

Real quick env dry-run result after restarting OneOps on `8380`:

- `uid`: `snmp-switch-ast20260603174801-d01c0e303c`;
- `title`: `OneOPS SNMP Switch Ops - AST20260603174801664`;
- `id`: `null`;
- `panel_count`: `14`;
- `binding_count`: `14`.

Grafana import note:

- the old manually imported dashboard UID `snmp-switch-ast3174801664` had the same title, so Grafana kept updating that existing dashboard;
- the old manual dashboard was deleted from quick env Grafana;
- the generated dashboard JSON was then imported without patching `uid`, `title`, datasource, or targets.

Current Grafana URL:

```text
http://127.0.0.1:3300/d/snmp-switch-ast20260603174801-d01c0e303c/oneops-snmp-switch-ops-ast20260603174801664
```

Grafana API readback:

- uid: `snmp-switch-ast20260603174801-d01c0e303c`;
- title: `OneOPS SNMP Switch Ops - AST20260603174801664`;
- version: `1`;
- panel count: `14`;
- variables: `datasource`, `device_code`;
- first expression: `oneops:cpu_usage_direct:ratio{device_code="$device_code"}`.

Synthetic sample data was shifted to the current time and re-imported:

- shifted file: `/tmp/oneops-snmp-switch-ops-sample-current.prom`;
- imported line count: `5002`;
- import result: HTTP `204`.

Verified query results:

- `oneops:cpu_usage_direct:ratio{device_code="AST20260603174801664"}` returns `1` result from VictoriaMetrics;
- scoped interface utilization returns `8` results through Grafana datasource proxy.

Important boundary:

- this still does not create or update a `grafana_dashboard` database row;
- the current Grafana import remains a quick-env visual verification step;
- the next persistence step should use this generated `uid`, title, variables, datasource references, panel bindings, and content hashes instead of reconstructing them elsewhere.

## 2026-06-12 Update: Platform Dashboard Persistence And Strategy Set Binding

The generated switch operations dashboard can now be saved back into the OneOps platform data model, not only dry-run generated or manually imported into Grafana.

New backend API:

```text
POST /platform/metrics/teleabs/strategy-sets/:id/metric-contract/grafana/dashboards/save/by-target
```

Request:

```json
{
  "target_part": "AST20260603174801664"
}
```

Save behavior:

- reuses the same strategy set target resolution, panel capability preview, recording rule preview, and Grafana dashboard materializer as the dry-run endpoint;
- generates a stable Grafana `uid` from the target device code;
- generates a stable platform dashboard `code` from that `uid`;
- upserts one `grafana_dashboard` row with `state = Disabled`;
- writes `platform_teleabs_strategy_set_dashboard_binding` so the strategy set points to this dashboard code;
- replaces an older binding for the same strategy set, so repeated saves are idempotent;
- does not call `syncToGrafana` and does not mutate the live Grafana instance.

Response adds these platform persistence fields on top of the existing dry-run payload:

```json
{
  "dashboard_code": "GDBSNMP...",
  "dashboard_uid": "snmp-switch-...",
  "dashboard_name": "OneOPS SNMP Switch Ops - ...",
  "dashboard_state": "Disabled",
  "saved": true,
  "synced": false
}
```

Why this closes an important loop:

- the screenshot-style dashboard remains derived from metric groups, panel capability requirements, recording rules, and strategy set target matching;
- the generated dashboard is now visible to platform dashboard management through `grafana_dashboard`;
- strategy set details can discover the dashboard through the existing strategy set dashboard binding table;
- enabling/syncing to Grafana stays an explicit later operation instead of being hidden inside materialization.

Frontend touch points:

- `OneOPS-UI/src/typings/platform/snmp-metric-contract.ts` now has save request/response types;
- `OneOPS-UI/src/api/platform/teleabs.ts` now exposes `saveTeleabsStrategySetGrafanaDashboardByTarget`;
- the smoke script checks both dry-run and save endpoint contracts.

Remaining closure gaps after this step:

1. Add a UI action in the strategy set or device dashboard workflow to call `saveTeleabsStrategySetGrafanaDashboardByTarget`, then surface the returned `dashboard_code`, `uid`, saved state, and binding status.
2. Decide the explicit sync path: either reuse existing dashboard enable/toggle flow or add a controlled “保存并同步到 Grafana” action that uses the persisted row and existing Grafana sync service.
3. Persist panel-level binding metadata if the platform needs first-class traceability from dashboard panel to metric group, capability, strategy, and recording rule. For now this traceability is returned by the materializer and embedded in the response, but not stored in a dedicated table.
4. Add quick-env smoke coverage that calls the new save endpoint against the real seed strategy set and confirms one `grafana_dashboard` row plus one strategy set binding.
5. After live sync is wired, verify the saved row can be enabled/synced and produces the same Grafana URL currently proven by manual quick-env import.

Quick env verification note:

- unauthenticated call reaches the HTTP layer but is rejected with `未登录或非法请求`;
- with `X-Auth-Token: abc123`, the new save endpoint reaches business logic;
- current quick env target `AST20260603174801664` is rejected before save because target context resolution reports missing `manufacturer_name`, `platform_name`, and `system_version`;
- this means the next quick-env closure is not the save API itself, but ensuring the seed/device context used by `by-target` materialization is fully loaded before save/publish/sync flows run.

## 2026-06-12 Update: Quick Env Dashboard Save Smoke Is Added

The previous remaining gap "add quick-env smoke coverage for the save endpoint" is now closed.

New script:

```text
quick_env/scripts/smoke_snmp_switch_dashboard_save.sh
```

It calls the real by-target dashboard save endpoint and then checks MySQL:

```text
POST /api/v1/platform/metrics/teleabs/strategy-sets/4284353d-1233-4022-ad18-871b3d8444c7/metric-contract/grafana/dashboards/save/by-target
target_part = AST20260603174801664
```

Assertions:

- HTTP response is `200`;
- response `code` is `0`;
- response contains `dashboard_code` and `dashboard_uid`;
- `grafana_dashboard` has exactly 1 row for that uid/code;
- `platform_teleabs_strategy_set_dashboard_binding` has exactly 1 row for that strategy set/dashboard code.

Default runtime assumptions:

```text
OneOps API: http://127.0.0.1:8380/api/v1
Auth token: abc123
MySQL: 127.0.0.1:3606
Database: UniOPS
```

Real quick env verification result:

```text
dashboard save smoke passed
HTTP_CODE=200
dashboard_code=GDBSNMP3E6A64DC49CDE413A4C27D84
dashboard_uid=snmp-switch-ast20260603174801-d01c0e303c
dashboard_count=1
binding_count=1
```

Guard coverage:

```text
quick_env/tests/test_seed_template_guard.py
  test_snmp_switch_dashboard_save_smoke_covers_real_quick_env_loop
```

Updated remaining closure gaps:

1. Add a UI action in the strategy set or device dashboard workflow to call `saveTeleabsStrategySetGrafanaDashboardByTarget`, then surface the returned `dashboard_code`, `uid`, saved state, and binding status.
2. Decide the explicit sync path: either reuse existing dashboard enable/toggle flow or add a controlled "保存并同步到 Grafana" action that uses the persisted row and existing Grafana sync service.
3. Persist panel-level binding metadata if the platform needs first-class traceability from dashboard panel to metric group, capability, strategy, and recording rule.
4. After live sync is wired, verify the saved row can be enabled/synced and produces the same Grafana URL currently proven by manual quick-env import.

## 2026-06-12 Update: Save-And-Sync To Live Grafana Is Added

The explicit sync path is now implemented as a separate SNMP by-target API. The existing `save/by-target` endpoint remains platform persistence only.

New backend endpoint:

```text
POST /platform/metrics/teleabs/strategy-sets/:id/metric-contract/grafana/dashboards/save-and-sync/by-target
```

Behavior:

- calls the existing by-target save resolver;
- persists/upserts `grafana_dashboard`;
- persists/upserts `platform_teleabs_strategy_set_dashboard_binding`;
- calls the existing Grafana dashboard batch sync service with the saved `dashboard_code`;
- returns the same dashboard materialization payload with `synced=true` and `dashboard_state=Enabled` only when Grafana sync reports one success and zero failures.

Frontend API helper:

```text
saveAndSyncTeleabsStrategySetGrafanaDashboardByTarget
```

Quick env smoke now supports both modes:

```bash
quick_env/scripts/smoke_snmp_switch_dashboard_save.sh
SAVE_AND_SYNC=true quick_env/scripts/smoke_snmp_switch_dashboard_save.sh
```

The sync mode calls `save-and-sync/by-target` and then reads back:

```text
GET http://127.0.0.1:3300/api/dashboards/uid/<dashboard_uid>
```

Real quick env verification result:

```text
dashboard save smoke passed
HTTP_CODE=200
dashboard_code=GDBSNMP3E6A64DC49CDE413A4C27D84
dashboard_uid=snmp-switch-ast20260603174801-d01c0e303c
synced=true
dashboard_count=1
binding_count=1
grafana_title=OneOPS SNMP Switch Ops - AST20260603174801664
```

Important implementation note:

- `cmd/wire_gen.go` was updated so the existing `GrafanaDashboardSrv` is injected into `TeleabsAPI`;
- without this generated wiring update, the handler compiles in isolated tests but the real API returns `Grafana 仪表盘同步服务未初始化`.

Remaining closure gaps after this step:

1. Add a UI action in the strategy set or device dashboard workflow to call save or save-and-sync and surface the returned dashboard code, uid, state, and sync status.
2. Persist panel-level binding metadata if first-class traceability from panel to metric group/capability/strategy/recording rule is required.
3. Decide whether the strategy-set dashboard binding must become variant/profile/target aware instead of one dashboard per strategy set.
4. Add dashboard diff/rollback before replacing an already-synced dashboard in higher-risk environments.

## 2026-06-12 Update: Strategy Set Drawer Can Save And Sync Dashboard

The first frontend action surface is now wired into the existing strategy-set detail drawer.

Location:

```text
OneOPS-UI/src/views/platform/StrategyTemplate/StrategySetDetailDrawer.vue
```

Behavior:

- the existing target device input remains the shared target source;
- `预检面板能力` still calls the by-target panel capability preview;
- `保存到平台` calls `saveTeleabsStrategySetGrafanaDashboardByTarget`;
- `保存并同步` calls `saveAndSyncTeleabsStrategySetGrafanaDashboardByTarget`;
- the drawer displays the returned dashboard code, UID, platform state, and sync status.

New frontend state helper:

```text
OneOPS-UI/src/views/platform/StrategyTemplate/snmpStrategySetGrafanaDashboardSave.ts
```

It keeps the UI behavior testable outside the SFC:

- validates strategy set id and target part;
- separates save loading from sync loading;
- stores the last result;
- exposes summary items for `dashboard_code`, `dashboard_uid`, `dashboard_state`, and `synced`.

New frontend smoke:

```bash
cd OneOPS-UI
npm run smoke:snmp-strategy-set-grafana-dashboard-save-action
```

Verification:

```text
snmp strategy-set grafana dashboard save action smoke passed
npm run typecheck passed
```

Remaining closure gaps after this step:

1. Decide whether the strategy-set dashboard binding must become variant/profile/target aware instead of one dashboard per strategy set.
2. Add dashboard diff/rollback before replacing an already-synced dashboard in higher-risk environments.
3. Add browser-level acceptance coverage for the drawer action once a stable quick-env frontend page flow is available.

## 2026-06-12 Update: Dashboard Panel Bindings Are Persisted

The dashboard save path now persists panel-level trace metadata in addition to the dashboard row and strategy-set dashboard binding.

New table/model:

```text
platform_teleabs_strategy_set_dashboard_panel_binding
OneOps/app/platform/platform_model/teleabs_strategy_set.go
OneOps/migrations/add_teleabs_strategy_set_dashboard_panel_binding.sql
```

Stored per panel:

- strategy set id, dashboard code, dashboard uid, target part, device code;
- panel key, panel id, title, section key, display intent, visual type, render policy;
- metric group key;
- strategy ids JSON;
- metric keys JSON;
- selected capability keys JSON;
- recording rule names JSON;
- managed state and content hash.

Save behavior:

- `save/by-target` and `save-and-sync/by-target` both materialize the dashboard first;
- the resolver saves the dashboard as `Disabled`;
- the resolver refreshes `platform_teleabs_strategy_set_dashboard_binding`;
- the resolver then deletes old panel bindings for the same dashboard or the same strategy set + target and inserts the current materialized panel bindings;
- the response now includes `panel_bindings_saved` and `panel_binding_count`.

Frontend behavior:

- `SnmpStrategySetTargetGrafanaDashboardSaveByTargetResponse` includes `panel_bindings_saved` and `panel_binding_count`;
- the strategy-set detail drawer summary now displays `面板追踪` with the persisted binding count.

Quick env smoke now verifies the full loop:

```bash
SAVE_AND_SYNC=true quick_env/scripts/smoke_snmp_switch_dashboard_save.sh
```

Real quick env verification result:

```text
dashboard save smoke passed
HTTP_CODE=200
dashboard_code=GDBSNMP3E6A64DC49CDE413A4C27D84
dashboard_uid=snmp-switch-ast20260603174801-d01c0e303c
synced=true
dashboard_count=1
binding_count=1
panel_binding_count=2
grafana_title=OneOPS SNMP Switch Ops - AST20260603174801664
```

Sample persisted panel trace from the running quick env:

```text
device.identity            panel_id=1 metric_group_key=                 record_names=[]
system_basic.cpu.stat      panel_id=2 metric_group_key=system_basic     record_names=["oneops:cpu_usage_direct:ratio"]
```

Verification:

```text
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*GrafanaDashboard|TestMetricCapabilityContractResolver.*RecordingRule' -count=1
go test ./app/platform/api -run 'TestTeleabsAPI_.*GrafanaDashboard|TestTeleabsAPI_.*RecordingRule' -count=1
go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1
go test ./initialize -run 'TestModelsIncludes|Test.*Teleabs' -count=1
go test ./cmd -run '^$' -count=1
npm run smoke:snmp-strategy-set-grafana-dashboard-save-action
npm run smoke:snmp-strategy-set-grafana-dashboard-materialization-dry-run
npm run typecheck
bash -n quick_env/scripts/smoke_snmp_switch_dashboard_save.sh
python3 quick_env/tests/test_seed_template_guard.py -v
SAVE_AND_SYNC=true quick_env/scripts/smoke_snmp_switch_dashboard_save.sh
```

Remaining closure gaps after this step:

1. Add dashboard diff/rollback before replacing an already-synced dashboard in higher-risk environments. Closed in the following "Dashboard Replacement Snapshots" step.
2. Add browser-level acceptance coverage for the drawer action once a stable quick-env frontend page flow is available.

## 2026-06-12 Update: Target-Aware Dashboard Bindings

The generated SNMP dashboard path now keeps target-aware dashboard bindings, so saving a second target for the same strategy set no longer erases the traceability for the first target.

New table/model:

```text
platform_teleabs_strategy_set_dashboard_target_binding
OneOps/app/platform/platform_model/teleabs_strategy_set.go
OneOps/migrations/add_teleabs_strategy_set_dashboard_target_binding.sql
```

Compatibility rule:

- `platform_teleabs_strategy_set_dashboard_binding` is still kept as the existing compatibility/current binding table;
- generated dashboards also write `platform_teleabs_strategy_set_dashboard_target_binding`;
- the target-aware table is keyed by `strategy_set_id + target_part` and `dashboard_code`;
- panel bindings are now refreshed by `dashboard_code` or `strategy_set_id + target_part`, not by the whole strategy set.

Response/API surface:

- `save/by-target` and `save-and-sync/by-target` now include `target_binding_saved`;
- the frontend response type includes `target_binding_saved`;
- the strategy-set detail drawer summary shows `目标绑定`.

Regression covered:

- saving `SW-1` and then `SW-2` under the same strategy set keeps two rows in `platform_teleabs_strategy_set_dashboard_target_binding`;
- saving `SW-2` no longer deletes `SW-1` panel bindings.

Real quick env verification result:

```text
dashboard save smoke passed
HTTP_CODE=200
dashboard_code=GDBSNMP3E6A64DC49CDE413A4C27D84
dashboard_uid=snmp-switch-ast20260603174801-d01c0e303c
synced=true
dashboard_count=1
binding_count=1
target_binding_count=1
panel_binding_count=2
grafana_title=OneOPS SNMP Switch Ops - AST20260603174801664
```

Sample target-aware binding row from the running quick env:

```text
strategy_set_id=4284353d-1233-4022-ad18-871b3d8444c7
target_part=AST20260603174801664
dashboard_code=GDBSNMP3E6A64DC49CDE413A4C27D84
dashboard_uid=snmp-switch-ast20260603174801-d01c0e303c
panel_binding_count=2
```

Verification:

```text
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*GrafanaDashboard|TestMetricCapabilityContractResolver.*RecordingRule' -count=1
go test ./app/platform/api -run 'TestTeleabsAPI_.*GrafanaDashboard|TestTeleabsAPI_.*RecordingRule' -count=1
go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1
go test ./initialize -run 'TestModelsIncludes|Test.*Teleabs' -count=1
go test ./cmd -run '^$' -count=1
npm run smoke:snmp-strategy-set-grafana-dashboard-save-action
npm run smoke:snmp-strategy-set-grafana-dashboard-materialization-dry-run
npm run typecheck
bash -n quick_env/scripts/smoke_snmp_switch_dashboard_save.sh
python3 quick_env/tests/test_seed_template_guard.py -v
SAVE_AND_SYNC=true quick_env/scripts/smoke_snmp_switch_dashboard_save.sh
```

Remaining closure gaps after this step:

1. Add dashboard diff/rollback before replacing an already-synced dashboard in higher-risk environments. Closed in the following "Dashboard Replacement Snapshots" step.
2. Add browser-level acceptance coverage for the drawer action once a stable quick-env frontend page flow is available.

## 2026-06-12 Update: Dashboard Replacement Snapshots

The generated SNMP dashboard save path now records a lightweight replacement snapshot before overwriting an existing platform dashboard whose content differs from the newly materialized dashboard JSON.

New table/model:

```text
platform_teleabs_strategy_set_dashboard_snapshot
OneOps/app/platform/platform_model/teleabs_strategy_set.go
OneOps/migrations/add_teleabs_strategy_set_dashboard_snapshot.sql
```

Replacement behavior:

- first save of a generated dashboard does not create a snapshot;
- idempotent save with the same dashboard JSON does not create a snapshot;
- if an existing `grafana_dashboard.content` SHA differs from the newly generated SHA, the previous content, UID, state, target, previous SHA, and new SHA are persisted before overwrite;
- snapshots are scoped by `strategy_set_id`, `dashboard_code`, and target context, so they can be used as rollback/diff evidence for a specific generated dashboard.

Response/API surface:

- `save/by-target` and `save-and-sync/by-target` now include `dashboard_sha256`;
- replacement saves also include `previous_dashboard_snapshot_saved`, `previous_dashboard_snapshot_id`, and `previous_dashboard_sha256`;
- the frontend response type includes these fields;
- the strategy-set detail drawer summary shows the dashboard content SHA prefix and whether an overwrite snapshot was created;
- the quick-env smoke requires `dashboard_sha256` and validates the snapshot id when a replacement snapshot is reported.

Regression covered:

- first save returns a generated dashboard SHA and no snapshot;
- repeated same-content save creates zero snapshot rows;
- overwriting a manually changed existing dashboard creates one snapshot row with the old content hash, old UID/state, and target part;
- API tests verify hash/snapshot fields are preserved through save and save-and-sync responses.

Real quick env verification result:

```text
dashboard save smoke passed
HTTP_CODE=200
dashboard_code=GDBSNMP3E6A64DC49CDE413A4C27D84
dashboard_uid=snmp-switch-ast20260603174801-d01c0e303c
dashboard_sha256=81a202d4cd012e53b50c62a16ae1d631335dd4079a4490d9735bc6d6212b79ab
synced=true
dashboard_count=1
binding_count=1
target_binding_count=1
panel_binding_count=2
grafana_title=OneOPS SNMP Switch Ops - AST20260603174801664
```

Verification:

```text
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*GrafanaDashboard|TestMetricCapabilityContractResolver.*RecordingRule' -count=1
go test ./app/platform/api -run 'TestTeleabsAPI_.*GrafanaDashboard|TestTeleabsAPI_.*RecordingRule' -count=1
go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1
go test ./initialize -run 'TestModelsIncludes|Test.*Teleabs' -count=1
go test ./cmd -run '^$' -count=1
npm run smoke:snmp-strategy-set-grafana-dashboard-save-action
npm run smoke:snmp-strategy-set-grafana-dashboard-materialization-dry-run
npm run typecheck
bash -n quick_env/scripts/smoke_snmp_switch_dashboard_save.sh
python3 quick_env/tests/test_seed_template_guard.py -v
SAVE_AND_SYNC=true quick_env/scripts/smoke_snmp_switch_dashboard_save.sh
```

Remaining closure gap after this step:

1. Add browser-level acceptance coverage for the drawer action once a stable quick-env frontend page flow is available.

## 2026-06-12 Update: Browser-Level Save-And-Sync Acceptance

The strategy-set drawer now has a repeatable browser-level acceptance script for the SNMP Grafana dashboard save-and-sync action.

New command:

```text
cd OneOPS-UI
ONEOPS_UI_REAL_BASE_URL=http://127.0.0.1:3001 npm run smoke:snmp-strategy-set-grafana-dashboard-save-real-page
```

The script uses a real browser session through Chrome DevTools Protocol and validates the full page action:

- mounts `StrategySetDetailDrawer` in a Vite-served fixture page;
- seeds `X-Auth-Token` into browser local storage;
- fills target `AST20260603174801664`;
- clicks the real `保存并同步` button;
- verifies the browser request body for `/metric-contract/grafana/dashboards/save-and-sync/by-target`;
- verifies the backend response has `saved=true`, `synced=true`, `dashboard_state=Enabled`, a 64-char `dashboard_sha256`, target binding, and panel bindings;
- verifies the drawer summary shows `同步=是`, `目标绑定=已保存`, content SHA prefix, and panel trace count;
- reads back the dashboard from Grafana via `/api/dashboards/uid/:uid`;
- writes a screenshot under `OneOPS-UI/.tmp/`.

Real quick env browser verification result:

```text
ok=true
base_url=http://127.0.0.1:3001
target_part=AST20260603174801664
strategy_set_id=4284353d-1233-4022-ad18-871b3d8444c7
dashboard_code=GDBSNMP3E6A64DC49CDE413A4C27D84
dashboard_uid=snmp-switch-ast20260603174801-d01c0e303c
dashboard_sha256=81a202d4cd012e53b50c62a16ae1d631335dd4079a4490d9735bc6d6212b79ab
panel_binding_count=2
grafana_title=OneOPS SNMP Switch Ops - AST20260603174801664
screenshot=OneOPS-UI/.tmp/snmp-grafana-dashboard-save-real-page-1781227948734.png
```

Verification:

```text
npm run smoke:snmp-strategy-set-grafana-dashboard-save-action
ONEOPS_UI_REAL_BASE_URL=http://127.0.0.1:3001 npm run smoke:snmp-strategy-set-grafana-dashboard-save-real-page
```

Core closure status after this step:

- platform strategy set to SNMP metric contract resolution: closed;
- recording rule and dashboard materialization: closed;
- platform save, target binding, panel binding, replacement snapshot: closed;
- quick-env seed/runtime smoke: closed;
- browser drawer save-and-sync action and Grafana readback: closed.

Remaining enhancements, not core closure blockers:

1. Improve generated Grafana dashboard visual density and switch-ops layout against the screenshot alignment spec.
2. Add multi-vendor browser acceptance cases beyond the current quick-env switch target.
3. Add a human-facing rollback UI/API over the saved dashboard snapshots.

## 2026-06-12 Update: Switch Health Strip Visual Enhancement

The generated switch dashboard now moves closer to the screenshot's first-screen operator model by adding a compact health command strip.

New generated panels:

```text
device.overall_health
device.active_alerts
```

Behavior:

- `Overall Health` is a derived stat panel that turns the existing metric logic into a 0/1 health signal;
- `Active Alerts` is a derived stat panel that counts active warning signals from CPU, memory, down ports, and interface error sources;
- both panels are still generated from recording-rule-backed capabilities, not from hardcoded vendor assumptions;
- the first metric row now prioritizes health and alert triage before CPU, memory, and port state;
- existing traceability continues through `panel_bindings[]`, including section, display intent, capability keys, metric keys, and record names.

Real quick env result after this visual enhancement:

```text
dashboard save smoke passed
HTTP_CODE=200
dashboard_code=GDBSNMP3E6A64DC49CDE413A4C27D84
dashboard_uid=snmp-switch-ast20260603174801-d01c0e303c
dashboard_sha256=166182f0b9290319d5cd9a0eef59a23d0b9a791387b013d419f854a30c49f276
synced=true
dashboard_count=1
binding_count=1
target_binding_count=1
panel_binding_count=2
previous_snapshot_id=f116f289-65ff-11f1-b681-cc15310828f2
grafana_title=OneOPS SNMP Switch Ops - AST20260603174801664
```

Browser acceptance result:

```text
ok=true
base_url=http://127.0.0.1:3001
target_part=AST20260603174801664
strategy_set_id=4284353d-1233-4022-ad18-871b3d8444c7
dashboard_code=GDBSNMP3E6A64DC49CDE413A4C27D84
dashboard_uid=snmp-switch-ast20260603174801-d01c0e303c
dashboard_sha256=166182f0b9290319d5cd9a0eef59a23d0b9a791387b013d419f854a30c49f276
panel_binding_count=2
grafana_title=OneOPS SNMP Switch Ops - AST20260603174801664
screenshot=OneOPS-UI/.tmp/snmp-grafana-dashboard-save-real-page-1781228546441.png
```

Verification:

```text
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverMaterializesScreenshotStyleGrafanaDashboard -count=1
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*GrafanaDashboard|TestMetricCapabilityContractResolver.*RecordingRule' -count=1
go test ./app/platform/api -run 'TestTeleabsAPI_.*GrafanaDashboard|TestTeleabsAPI_.*RecordingRule' -count=1
npm run smoke:snmp-strategy-set-grafana-dashboard-materialization-dry-run
npm run smoke:snmp-strategy-set-grafana-dashboard-save-action
bash -n quick_env/scripts/smoke_snmp_switch_dashboard_save.sh
python3 quick_env/tests/test_seed_template_guard.py -v
SAVE_AND_SYNC=true quick_env/scripts/smoke_snmp_switch_dashboard_save.sh
ONEOPS_UI_REAL_BASE_URL=http://127.0.0.1:3001 npm run smoke:snmp-strategy-set-grafana-dashboard-save-real-page
```

Remaining enhancements:

1. Add richer switch-ops sections for hardware health, layer-2/routing summaries, and event/config evidence when matching metric groups exist.
2. Add multi-vendor browser acceptance cases beyond the current quick-env switch target.
3. Add a human-facing rollback UI/API over the saved dashboard snapshots.

## 2026-06-12 Update: Hardware Temperature Capability Closure

The first hardware-health metric is now wired through the same strategy-set and recording-rule path as interface and system metrics.

New standard capability:

```text
device_temperature_celsius
```

New generated panels:

```text
device_metrics.temperature.stat
device_metrics.temperature.trend
```

Behavior:

- SNMP passthrough fields named `temperature`, `temp`, `deviceTemperature`, or `hwTemperature` are normalized into the recordable `device_temperature_celsius` capability;
- the generated recording rule is `oneops:device_temperature:celsius`;
- `Temperature Now` renders as an instant stat with green/orange/red thresholds;
- `Temperature Trend` renders as a time series for incident-window correlation;
- unknown device metrics still remain config-driven and are not forced into switch hardware panels;
- target dashboard materialization now proves the path: strategy set -> effective contract -> recording rule preview -> Grafana panel -> panel binding.

Verification:

```text
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver(ImportsInterfaceAndSystemCapabilities|DefaultPanelRequirements|BuildsRecordingRuleExpressions|MaterializesScreenshotStyleGrafanaDashboard|SkipsUnsupportedSwitchPanels)' -count=1
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*GrafanaDashboard|TestMetricCapabilityContractResolver.*RecordingRule|TestMetricCapabilityContractResolver.*PanelCapability|TestMetricCapabilityContractResolverImportsInterfaceAndSystemCapabilities' -count=1
go test ./app/platform/api -run 'TestTeleabsAPI_.*GrafanaDashboard|TestTeleabsAPI_.*RecordingRule|TestTeleabsAPI_.*PanelCapability' -count=1
```

Quick-env seed follow-up:

- H3C, Huawei, and Maipu SNMP network strategy bootstrap SQL now include `temperature` in `metric_manifest`;
- their passthrough SNMP configs now include `[[inputs.snmp.field]] name = "temperature"`;
- this lets `quick_env/start.sh` load seed data that can actually produce the temperature recording rule and Grafana panels.

Seed verification:

```text
bash quick_env/tests/test_snmp_network_strategy_seed.sh
python3 quick_env/tests/test_seed_template_guard.py -v
bash -n quick_env/scripts/smoke_snmp_switch_dashboard_save.sh
```

Runtime quick-env verification on `demo2`:

```text
bash quick_env/scripts/sync_snmp_network_strategy_seed.sh --instance demo2
```

The running UniOPS database was verified to contain the temperature manifest and passthrough field for all three seeded SNMP strategies:

```text
H3C通用SNMP网络监控策略     1  1
Huawei通用SNMP网络监控策略  1  1
迈普通用SNMP网络监控策略    1  1
```

Real save-and-sync smoke after starting the local OneOps backend:

```text
dashboard save smoke passed
HTTP_CODE=200
dashboard_code=GDBSNMP3E6A64DC49CDE413A4C27D84
dashboard_uid=snmp-switch-ast20260603174801-d01c0e303c
dashboard_sha256=5837794966048d1453f2322b032def41cac321b577883e4a28d5a4be6734fc91
synced=true
dashboard_count=1
binding_count=1
target_binding_count=1
panel_binding_count=4
previous_snapshot_id=f2834df3-6601-11f1-88a8-cc15310828f2
grafana_title=OneOPS SNMP Switch Ops - AST20260603174801664
```

Database verification confirmed the saved dashboard content and panel bindings contain:

```text
Temperature Now
Temperature Trend
oneops:device_temperature:celsius
device_metrics.temperature.stat
device_metrics.temperature.trend
```

## 2026-06-12 Update: Hardware Status Capability Closure

Hardware status panels now follow the same optional capability model as temperature.

New standard capabilities:

```text
device_fan_status
device_power_status
device_transceiver_status
device_module_status
```

New generated panels:

```text
device_metrics.fan_status.stat
device_metrics.power_status.stat
device_metrics.transceiver_status.stat
device_metrics.module_status.stat
```

Behavior:

- passthrough fields such as `fanStatus`, `powerStatus`, `transceiverStatus`, and `moduleStatus` are normalized into recordable device health capabilities;
- generated recording rules use `oneops:device_fan_status`, `oneops:device_power_status`, `oneops:device_transceiver_status`, and `oneops:device_module_status`;
- status panels render only when the effective strategy contract exposes the capability or the recording-rule preview provides the record;
- the active-alert and overall-health strip treats non-`1` hardware status as an alert signal;
- unsupported hardware panels are still skipped, so switch dashboards do not invent fan, PSU, optical, or module health when a strategy cannot provide those fields.

Verification:

```text
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver(ImportsInterfaceAndSystemCapabilities|DefaultPanelRequirements|BuildsRecordingRuleExpressions|MaterializesScreenshotStyleGrafanaDashboard|SkipsUnsupportedSwitchPanels|MaterializesHuaweiS5735DashboardFromTemplateChain)' -count=1
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*GrafanaDashboard|TestMetricCapabilityContractResolver.*RecordingRule|TestMetricCapabilityContractResolver.*PanelCapability|TestMetricCapabilityContractResolverImportsInterfaceAndSystemCapabilities' -count=1
go test ./app/platform/api -run 'TestTeleabsAPI_.*GrafanaDashboard|TestTeleabsAPI_.*RecordingRule|TestTeleabsAPI_.*PanelCapability' -count=1
npm run smoke:snmp-strategy-set-grafana-dashboard-materialization-dry-run
npm run smoke:snmp-strategy-set-grafana-dashboard-save-action
```

## 2026-06-12 Update: L2 Neighbor Evidence Panel Closure

The first Layer-2 neighbor metric contract is now connected into the Grafana materializer as a narrow evidence-table path.

Metric group:

```text
l2_neighbors
```

Generated panel:

```text
l2_neighbors.summary
```

Behavior:

- LLDP-style passthrough tables such as `snmp_lldp_neighbors` / `LLDP-MIB::lldpRemTable` are normalized into a table-shaped contract;
- stable fields include `local_port`, `neighbor_port`, `neighbor_name`, `neighbor_chassis_id`, and `neighbor_management_ip`;
- unknown extra neighbor fields remain config-driven dimensions;
- the group remains `table` / non-recordable because LLDP neighbor evidence is dimensional topology data, not a time-series recording-rule metric;
- `l2_neighbors.summary` renders only when the effective capability support exposes `l2_neighbor_identity`;
- the panel uses an evidence-table render policy and queries the raw LLDP measurement family with `__name__=~"snmp_lldp_neighbors.*"` scoped by `device_code`;
- panel bindings keep `metric_group_key=l2_neighbors`, stable metric keys, and `selected_capability_keys=["l2_neighbor_identity"]`;
- `record_names` is intentionally empty for this panel, so it does not pretend to be backed by Prometheus recording rules.

Verification:

```text
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverImportsLldpNeighborContract -count=1
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver(DefaultPanelRequirements|MaterializesL2NeighborEvidencePanel)' -count=1
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver(ImportsLldpNeighborContract|DefaultPanelRequirements|ResolvesPanelCapabilitySupport|PreviewsStrategySetPanelCapabilitySupportWithDefaultRequirements|PreviewsStrategySetPanelCapabilitySupportByTarget|MaterializesL2NeighborEvidencePanel|MaterializesL2NeighborDashboardByTarget|MaterializesScreenshotStyleGrafanaDashboard|MaterializesHuaweiS5735DashboardFromTemplateChain|MaterializesStrategySetGrafanaDashboardByTarget|SavesStrategySetGrafanaDashboardByTarget)' -count=1
go test ./app/platform/api -run 'TestTeleabsAPI_.*GrafanaDashboard|TestTeleabsAPI_.*PanelCapability' -count=1
python3 quick_env/tests/test_seed_template_guard.py -v
python3 quick_env/tests/test_validate_nacos_seed_runtime.py -v
```

Remaining closure gaps:

1. MAC, ARP, VLAN, and STP still need their own metric-group contracts and evidence-panel bindings; they are not included in the LLDP closure above.
2. Event/config evidence is still outside the SNMP metric contract and needs a separate binding model or a clear bridge from existing config/compliance tables.
3. Multi-vendor real/browser acceptance still needs more targets beyond the current quick-env switch path.

## 2026-06-12 Update: MAC Address Table Evidence Panel Closure

The first MAC forwarding table contract now follows the same narrow evidence-table closure as LLDP.

Metric group:

```text
l2_mac_table
```

Generated panel:

```text
l2_mac_table.summary
```

Behavior:

- BRIDGE-MIB / Q-BRIDGE-MIB passthrough tables such as `snmp_mac_table` / `BRIDGE-MIB::dot1dTpFdbTable` are normalized into a table-shaped contract;
- stable fields include `mac_address`, `bridge_port`, `mac_status`, and `vlan_id`;
- fields remain dimensional and `not_recordable`, because the operator question is "where is this MAC learned now?" rather than "what is the averaged value?";
- `l2_mac_table.summary` renders only when the effective capability support exposes `l2_mac_identity`;
- the panel uses the existing evidence-table render policy and queries the raw MAC table measurement family with `__name__=~"snmp_mac_table.*"` scoped by `device_code`;
- panel bindings keep `metric_group_key=l2_mac_table`, stable metric keys, and `selected_capability_keys=["l2_mac_identity"]`;
- `record_names` is intentionally empty for this panel.

Verification:

```text
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver(ImportsMacTableContract|DefaultPanelRequirements|MaterializesMacTableDashboardByTarget)' -count=1
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver(ImportsLldpNeighborContract|ImportsMacTableContract|DefaultPanelRequirements|ResolvesPanelCapabilitySupport|PreviewsStrategySetPanelCapabilitySupportWithDefaultRequirements|PreviewsStrategySetPanelCapabilitySupportByTarget|MaterializesL2NeighborEvidencePanel|MaterializesL2NeighborDashboardByTarget|MaterializesMacTableDashboardByTarget|MaterializesScreenshotStyleGrafanaDashboard|MaterializesHuaweiS5735DashboardFromTemplateChain|MaterializesStrategySetGrafanaDashboardByTarget|SavesStrategySetGrafanaDashboardByTarget)' -count=1
```

Remaining closure gaps after this update:

1. ARP, VLAN, and STP still need their own metric-group contracts and evidence-panel bindings.
2. Event/config evidence is still outside the SNMP metric contract and needs a separate binding model or a clear bridge from existing config/compliance tables.
3. Multi-vendor real/browser acceptance still needs more targets beyond the current quick-env switch path.

## 2026-06-12 Update: ARP Table Evidence Panel Closure

The first ARP table contract is now connected into the same evidence-table path.

Metric group:

```text
l3_arp_table
```

Generated panel:

```text
l3_arp_table.summary
```

Behavior:

- IP-MIB passthrough tables such as `snmp_arp_table` / `IP-MIB::ipNetToMediaTable` are normalized into a table-shaped contract;
- stable fields include `ip_address`, `mac_address`, `if_index`, and `arp_type`;
- fields remain dimensional and `not_recordable`, because the operator question is "which MAC owns this IP on which interface now?" rather than a trend;
- `l3_arp_table.summary` renders only when the effective capability support exposes `l3_arp_identity`;
- the panel uses the evidence-table render policy and queries the raw ARP table measurement family with `__name__=~"snmp_arp_table.*"` scoped by `device_code`;
- panel bindings keep `metric_group_key=l3_arp_table`, stable metric keys, and `selected_capability_keys=["l3_arp_identity"]`;
- `record_names` is intentionally empty for this panel.

Verification:

```text
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver(ImportsArpTableContract|DefaultPanelRequirements|MaterializesArpTableDashboardByTarget)' -count=1
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver(ImportsLldpNeighborContract|ImportsMacTableContract|ImportsArpTableContract|DefaultPanelRequirements|ResolvesPanelCapabilitySupport|PreviewsStrategySetPanelCapabilitySupportWithDefaultRequirements|PreviewsStrategySetPanelCapabilitySupportByTarget|MaterializesL2NeighborEvidencePanel|MaterializesL2NeighborDashboardByTarget|MaterializesMacTableDashboardByTarget|MaterializesArpTableDashboardByTarget|MaterializesScreenshotStyleGrafanaDashboard|MaterializesHuaweiS5735DashboardFromTemplateChain|MaterializesStrategySetGrafanaDashboardByTarget|SavesStrategySetGrafanaDashboardByTarget)' -count=1
```

Remaining closure gaps after this update:

1. VLAN and STP still need their own metric-group contracts and evidence-panel bindings.
2. Event/config evidence is still outside the SNMP metric contract and needs a separate binding model or a clear bridge from existing config/compliance tables.
3. Multi-vendor real/browser acceptance still needs more targets beyond the current quick-env switch path.

## 2026-06-12 Update: VLAN Table Evidence Panel Closure

The first VLAN table contract is now connected into the evidence-table path.

Metric group:

```text
l2_vlan_table
```

Generated panel:

```text
l2_vlan_table.summary
```

Behavior:

- Q-BRIDGE-MIB passthrough tables such as `snmp_vlan_table` / `Q-BRIDGE-MIB::dot1qVlanStaticTable` are normalized into a table-shaped contract;
- stable fields include `vlan_id`, `vlan_name`, `vlan_status`, and `vlan_type`;
- fields remain dimensional and `not_recordable`, because the operator question is "which VLANs exist and what is their current state?" rather than a trend;
- `l2_vlan_table.summary` renders only when the effective capability support exposes `l2_vlan_identity`;
- the panel uses the evidence-table render policy and queries the raw VLAN table measurement family with `__name__=~"snmp_vlan_table.*"` scoped by `device_code`;
- panel bindings keep `metric_group_key=l2_vlan_table`, stable metric keys, and `selected_capability_keys=["l2_vlan_identity"]`;
- `record_names` is intentionally empty for this panel.

Verification:

```text
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver(ImportsVlanTableContract|DefaultPanelRequirements|MaterializesVlanTableDashboardByTarget)' -count=1
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver(ImportsLldpNeighborContract|ImportsMacTableContract|ImportsArpTableContract|ImportsVlanTableContract|DefaultPanelRequirements|ResolvesPanelCapabilitySupport|PreviewsStrategySetPanelCapabilitySupportWithDefaultRequirements|PreviewsStrategySetPanelCapabilitySupportByTarget|MaterializesL2NeighborEvidencePanel|MaterializesL2NeighborDashboardByTarget|MaterializesMacTableDashboardByTarget|MaterializesArpTableDashboardByTarget|MaterializesVlanTableDashboardByTarget|MaterializesScreenshotStyleGrafanaDashboard|MaterializesHuaweiS5735DashboardFromTemplateChain|MaterializesStrategySetGrafanaDashboardByTarget|SavesStrategySetGrafanaDashboardByTarget)' -count=1
```

Remaining closure gaps after this update:

1. STP still needs its own metric-group contract and evidence-panel binding.
2. Event/config evidence is still outside the SNMP metric contract and needs a separate binding model or a clear bridge from existing config/compliance tables.
3. Multi-vendor real/browser acceptance still needs more targets beyond the current quick-env switch path.

## 2026-06-12 Update: STP State Evidence Panel Closure

The first STP state contract is now connected into the evidence-table path.

Metric group:

```text
l2_stp_state
```

Generated panel:

```text
l2_stp_state.summary
```

Behavior:

- BRIDGE-MIB passthrough tables such as `snmp_stp_state` / `BRIDGE-MIB::dot1dStpPortTable` are normalized into a table-shaped contract;
- stable fields include `stp_port`, `stp_state`, `stp_enable`, `stp_path_cost`, and `stp_designated_bridge`;
- fields remain dimensional and `not_recordable`, because the operator question is "which ports are participating in STP and what is their current state?" rather than a trend;
- `l2_stp_state.summary` renders only when the effective capability support exposes `l2_stp_identity`;
- the panel uses the evidence-table render policy and queries the raw STP table measurement family with `__name__=~"snmp_stp_state.*"` scoped by `device_code`;
- panel bindings keep `metric_group_key=l2_stp_state`, stable metric keys, and `selected_capability_keys=["l2_stp_identity"]`;
- `record_names` is intentionally empty for this panel.

Verification:

```text
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver(ImportsStpStateContract|DefaultPanelRequirements|MaterializesStpStateDashboardByTarget)' -count=1
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver(ImportsLldpNeighborContract|ImportsMacTableContract|ImportsArpTableContract|ImportsVlanTableContract|ImportsStpStateContract|DefaultPanelRequirements|ResolvesPanelCapabilitySupport|PreviewsStrategySetPanelCapabilitySupportWithDefaultRequirements|PreviewsStrategySetPanelCapabilitySupportByTarget|MaterializesL2NeighborEvidencePanel|MaterializesL2NeighborDashboardByTarget|MaterializesMacTableDashboardByTarget|MaterializesArpTableDashboardByTarget|MaterializesVlanTableDashboardByTarget|MaterializesStpStateDashboardByTarget|MaterializesScreenshotStyleGrafanaDashboard|MaterializesHuaweiS5735DashboardFromTemplateChain|MaterializesStrategySetGrafanaDashboardByTarget|SavesStrategySetGrafanaDashboardByTarget|.*RecordingRule)' -count=1
```

Remaining closure gaps after this update:

1. Event/config evidence is still outside the SNMP metric contract and needs a separate binding model or a clear bridge from existing config/compliance tables.
2. Multi-vendor real/browser acceptance still needs more targets beyond the current quick-env switch path.

## 2026-06-12 Update: Config/Compliance Platform Evidence Link Closure

Configuration backup and compliance evidence now have a platform bridge into the generated switch dashboard.

Generated panels:

```text
platform_config.backup
platform_config.compliance
```

Behavior:

- these panels are not SNMP metric groups and do not generate recording rules;
- target panel preview enriches the default SNMP support list with platform capabilities only when the target has matching OneOPS platform rows;
- `platform_config.backup` is supported by existing backup/version evidence from tables such as `platform_device_config_backup` and `platform_config_version`;
- `platform_config.compliance` is supported by baseline/compliance evidence from tables such as `platform_config_baseline_evaluation` or a populated `platform_config_version.baseline_status`;
- Grafana renders these as `platform_evidence_link` text panels, pointing the operator back to OneOPS config evidence instead of pretending the data is Prometheus time-series data;
- panel bindings keep `metric_group_key=platform_config_backup` or `metric_group_key=platform_config_compliance`, stable platform evidence keys, and selected capabilities;
- `record_names` is intentionally empty for both panels.

Verification:

```text
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver(DefaultPanelRequirements|AddsPlatformConfigEvidenceSupportByTarget|MaterializesPlatformConfigEvidencePanelsByTarget)' -count=1
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver(ImportsInterfaceAndSystemCapabilities|ImportsLldpNeighborContract|ImportsMacTableContract|ImportsArpTableContract|ImportsVlanTableContract|ImportsStpStateContract|DefaultPanelRequirements|AddsPlatformConfigEvidenceSupportByTarget|MaterializesPlatformConfigEvidencePanelsByTarget|.*PanelCapability|.*GrafanaDashboard|MaterializesL2NeighborEvidencePanel|MaterializesL2NeighborDashboardByTarget|MaterializesMacTableDashboardByTarget|MaterializesArpTableDashboardByTarget|MaterializesVlanTableDashboardByTarget|MaterializesStpStateDashboardByTarget|.*RecordingRule)' -count=1
```

Remaining closure gaps after this update:

1. Active alert and recent event evidence still need a platform source bridge.
2. Multi-vendor real/browser acceptance still needs more targets beyond the current quick-env switch path.

## 2026-06-12 Update: Alert/Event Platform Evidence Link Closure

Active alerts and recent events now have a platform bridge into the generated switch dashboard.

Generated panels:

```text
platform_alerts.active
platform_events.recent
```

Behavior:

- these panels are not SNMP metric groups and do not generate recording rules;
- target panel preview enriches the default SNMP support list with platform capabilities only when the target has matching OneOPS platform rows;
- `platform_alerts.active` is supported by active alert evidence from `alert_alarm`;
- `platform_events.recent` is supported by recent platform events from sources such as `deployment_event_log`, `platform_config_change_event`, or `device_v2_change_event`;
- Grafana renders these as `platform_evidence_link` text panels, pointing the operator back to OneOPS alert/event evidence instead of pretending the data is Prometheus time-series data;
- panel bindings keep `metric_group_key=platform_active_alerts` or `metric_group_key=platform_recent_events`, stable platform evidence keys, and selected capabilities;
- `record_names` is intentionally empty for both panels.

Verification:

```text
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver(DefaultPanelRequirements|AddsPlatformAlertEventEvidenceSupportByTarget|MaterializesPlatformAlertEventEvidencePanelsByTarget)' -count=1
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver(ImportsInterfaceAndSystemCapabilities|ImportsLldpNeighborContract|ImportsMacTableContract|ImportsArpTableContract|ImportsVlanTableContract|ImportsStpStateContract|DefaultPanelRequirements|AddsPlatformConfigEvidenceSupportByTarget|MaterializesPlatformConfigEvidencePanelsByTarget|AddsPlatformAlertEventEvidenceSupportByTarget|MaterializesPlatformAlertEventEvidencePanelsByTarget|.*PanelCapability|.*GrafanaDashboard|MaterializesL2NeighborEvidencePanel|MaterializesL2NeighborDashboardByTarget|MaterializesMacTableDashboardByTarget|MaterializesArpTableDashboardByTarget|MaterializesVlanTableDashboardByTarget|MaterializesStpStateDashboardByTarget|.*RecordingRule)' -count=1
```

Remaining closure gaps after this update:

1. Multi-vendor real/browser acceptance still needs more targets beyond the current quick-env switch path.

## 2026-06-12 Update: Huawei/S5735 Closed-Loop Acceptance Scaffold

The local acceptance path now matches the intended production model for a concrete switch target:

```text
target = Huawei / VRP / S5735
strategy set item = generic switch SNMP strategy
selected strategy = concrete Huawei S5735 child strategy
effective contract = generic switch parent + Huawei VRP parent + Huawei S5735 child
dashboard template = snmp.switch.root -> snmp.switch.huawei.vrp -> snmp.switch.huawei.vrp.s5735
```

What this verifies:

- a concrete target first resolves to the best leaf strategy, not to every matching sibling strategy;
- the leaf strategy inherits parent and grandparent `passthrough_config` blocks before contract import;
- the effective contract renders recording-rule panels, L2 evidence-table panels, and platform evidence-link panels in the same dashboard;
- `l2_neighbors.summary`, `l2_mac_table.summary`, `l3_arp_table.summary`, `l2_vlan_table.summary`, and `l2_stp_state.summary` all keep `render_policy=evidence_table`;
- `platform_config.backup`, `platform_config.compliance`, `platform_alerts.active`, and `platform_events.recent` all keep `render_policy=platform_evidence_link`;
- recording-rule panels inherited from the parent contract still render beside evidence panels;
- Huawei/S5735 dashboard template inheritance is materialized into one concrete Grafana dashboard JSON.

Verification:

```text
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverMaterializesHuaweiS5735ClosedLoopDashboardByTarget -count=1
```

Current closure boundary:

1. Backend materialization, panel capability trace, strategy inheritance, dashboard template inheritance, evidence-table panels, and platform evidence-link panels are covered by automated tests.
2. quick_env can still save/sync the generated dashboard, but its seed does not yet contain stable L2/platform evidence rows for a hard smoke assertion of every closed-loop panel.
3. Remaining real acceptance is therefore limited to quick_env seed enrichment plus Grafana browser readback/sample-data verification for the Huawei/S5735 target.

## 2026-06-12 Update: quick_env SNMP Switch Seed Replay Closure

quick_env startup now replays the SNMP switch closed-loop seed records for existing environments, not only for first-time MySQL initialization.

Closed scope for this step:

- `start.sh` now runs `sync_snmp_switch_dashboard_seed_records` after `sync_snmp_switch_device_context_records` and before optional external data loading;
- the replayed seed files are `zzzzzzzzzz-huawei-snmp-network-strategy-bootstrap.sql` and `zzzzzzzzzz-snmp-switch-platform-evidence-bootstrap.sql`;
- the Huawei SNMP strategy seed includes the switch evidence-table measurements needed by the screenshot-style dashboard: `snmp_lldp_neighbors`, `snmp_mac_table`, `snmp_arp_table`, `snmp_vlan_table`, and `snmp_stp_state`;
- the platform evidence seed supplies the quick-env switch rows needed by config backup, compliance, active alert, and recent event link panels;
- `smoke_snmp_switch_dashboard_save.sh` now asserts all closed-loop panel binding keys, including the five L2 evidence panels and four platform evidence-link panels.

Verification:

```text
bash -n quick_env/start.sh quick_env/scripts/smoke_snmp_switch_dashboard_save.sh
python3 quick_env/tests/test_seed_template_guard.py -v
docker exec -i demo2-mysql mysql -uroot -pUniOPS@Passw0rd -D UniOPS < quick_env/docker-entrypoint-initdb.d/zzzzzzzzzz-huawei-snmp-network-strategy-bootstrap.sql
docker exec -i demo2-mysql mysql -uroot -pUniOPS@Passw0rd -D UniOPS < quick_env/docker-entrypoint-initdb.d/zzzzzzzzzz-snmp-switch-platform-evidence-bootstrap.sql
```

Live demo2 MySQL replay notes:

- `UniOPS.platform_device_config_backup`, `platform_config_version`, `platform_config_baseline_evaluation`, `alert_alarm`, and `deployment_event_log` each returned evidence for `AST20260603174801664`;
- the platform evidence seed keeps all inserted primary keys within the current `varchar(36)` schema limit;
- `alert_alarm` insertion handles schema drift by checking `information_schema.COLUMNS` and including `datasource_type='prometheus'` only when that column exists.
- `alert_rule` insertion handles schema drift by checking `information_schema.COLUMNS` and including `expr='snmp_cpu_usage{device_code="AST20260603174801664"} > 80'` only when that column exists.

Current closure boundary:

1. Backend inheritance/materialization and quick_env seed replay are now covered by automated tests.
2. Current demo2 has MySQL and Grafana running, and the seed replay has been verified against live MySQL.
3. OneOps API was started from source with `go run main.go --config ../quick_env/.runtime/demo2/init-configs/nacos/cipher-aes-start-config.yaml`, listening on `:8380` with Bidi on `:7370`.
4. `SAVE_AND_SYNC=true quick_env/scripts/smoke_snmp_switch_dashboard_save.sh` passed against live OneOps + Grafana.

Live Grafana readback:

```text
dashboard_code=GDBSNMP3E6A64DC49CDE413A4C27D84
dashboard_uid=snmp-switch-ast20260603174801-d01c0e303c
grafana_title=OneOPS SNMP Switch Ops - AST20260603174801664
panel_binding_count=28
grafana_url=http://127.0.0.1:3300/d/snmp-switch-ast20260603174801-d01c0e303c
```

The smoke asserts these closed-loop panel keys:

```text
l2_neighbors.summary
l2_mac_table.summary
l3_arp_table.summary
l2_vlan_table.summary
l2_stp_state.summary
platform_config.backup
platform_config.compliance
platform_alerts.active
platform_events.recent
```

Closed-loop status:

1. Huawei / VRP / S5735 concrete target matching is covered.
2. Strategy parent/child inheritance is covered.
3. Dashboard template inheritance is covered.
4. quick_env seed replay is covered.
5. OneOps DB save, panel binding persistence, target binding persistence, Grafana sync, and Grafana UID readback are covered.

Remaining scope is no longer part of this switch closed loop: multi-vendor browser acceptance and visual tuning can proceed as separate follow-up work.

## 2026-06-12 Update: Remaining SNMP Switch Dashboard Closure Boundary

The next closure is intentionally limited to the four items explicitly requested after Huawei/S5735 closed-loop acceptance:

| Item | Closure Evidence | Status |
| --- | --- | --- |
| Multi-vendor validation | `quick_env/scripts/smoke_snmp_switch_dashboard_vendor_matrix.sh` passes for Huawei, H3C, Cisco, Maipu, and Fiberhome | Pending implementation and live run |
| Visual experience tuning | `TestSwitchGrafanaDashboardUsesOpsScreenshotLayoutContract` passes and panel keys match the screenshot-aligned information contract | Pending implementation |
| Real SNMP data validation | `quick_env/scripts/smoke_snmp_switch_metric_data.sh` returns non-empty Prometheus-compatible query results for a live target | Pending real SNMP metric flow |
| Frontend platform entry | `npm run smoke:snmp-strategy-set-grafana-dashboard-open-link` and the existing save-action smoke pass | Pending implementation |

Scope guard:

- keep the work inside the SNMP switch dashboard family;
- keep strategy and dashboard inheritance in OneOPS materialization, not in Grafana runtime;
- do not add a custom Grafana plugin, iframe embedding framework, new alert workflow, or non-switch device dashboard family;
- treat real SNMP data validation as a live-environment gate, not as a synthetic seed substitute.

Verification commands for this remaining closure:

```text
python3 quick_env/tests/test_seed_template_guard.py -v
python3 quick_env/tests/test_validate_nacos_seed_runtime.py -v

cd OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolverMaterializesHuaweiS5735ClosedLoopDashboardByTarget|TestMetricCapabilityContractResolverMaterializesSwitchDashboardByVendorFamily|TestSwitchGrafanaDashboardUsesOpsScreenshotLayoutContract' -count=1

cd ../OneOPS-UI
npm run smoke:snmp-strategy-set-grafana-dashboard-open-link
npm run smoke:snmp-strategy-set-grafana-dashboard-save-action

cd ..
bash -n quick_env/scripts/smoke_snmp_switch_dashboard_save.sh
bash -n quick_env/scripts/smoke_snmp_switch_dashboard_vendor_matrix.sh
bash -n quick_env/scripts/smoke_snmp_switch_metric_data.sh
```

Live validation remains required before marking the remaining closure complete:

```text
SAVE_AND_SYNC=true \
ONEOPS_API_BASE_URL=http://127.0.0.1:8380/api/v1 \
ONEOPS_AUTH_TOKEN=abc123 \
MYSQL_PORT=3606 \
MYSQL_ROOT_PASSWORD='UniOPS@Passw0rd' \
GRAFANA_URL=http://127.0.0.1:3300 \
GRAFANA_USER=admin \
GRAFANA_PASSWORD=admin \
quick_env/scripts/smoke_snmp_switch_dashboard_vendor_matrix.sh

PROMETHEUS_URL=http://127.0.0.1:8428 \
SNMP_TARGET_DEVICE_CODE=AST20260603174801664 \
quick_env/scripts/smoke_snmp_switch_metric_data.sh
```

### 10. SNMP OID Online Test Is Now Wired End-to-End

The SNMP metric-group editor now supports real-target OID online testing without leaving the strategy page.

Backend additions:

- dedicated endpoint: `POST /platform/metrics/teleabs/strategies/:id/snmp-metric/oid-test/by-target`
- resolver path: strategy scoped request -> target context resolution -> SNMP probe target resolution -> `collectsnmp.RealWalker`
- field mode and group mode both return thin per-field results:
  - `success`
  - `failed`
  - `value_kind`
  - `sample_value`
  - `message`
  - `tested_at`

Frontend additions:

- `PluginFormSnmp.vue` now carries a lightweight `target_part` input for OID testing
- the OID test entry was then moved from the left-side info column into the main editor lane, so users now see `target_part + 待测试提示` immediately above the active group editor
- the OID task bar was then tightened again so the main editor lane now emphasizes only `target_part + compact readiness state`; the earlier long guidance copy was removed, and `测试本组待测项` remains a current-group header action rather than a page-level action
- `SnmpMetricGroupEditor.vue` now exposes:
  - field-level `测试`
  - group-level `测试本组待测项`
  - inline `未测 / 测试中 / 通过 / 失败` status
- changing `target_part` clears prior OID test state
- editing an OID marks that field back to `未测`
- group test focuses the first failed field
- save still remains available; the page now only adds a small `待测试 N` hint
- the tightened task-bar pass was re-verified with `smoke:snmp-oid-online-test-page`, `smoke:snmp-oid-online-test-editor`, `smoke:snmp-workspace-view`, and a fresh `npm run typecheck`
- explicit-contract draft-default warnings are now aggregated by group and issue type, so legacy contracts no longer dump dozens of near-duplicate `缺少 value_type/calculation` lines into the right-side alert area
- the explicit-contract alert headline is now summary-first as well: it highlights affected groups and issue categories before showing detailed messages, instead of foregrounding a large raw issue count

New frontend file added for this slice:

- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpOidOnlineTestState.ts`

Focused verification completed for this closure:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*Oid.*Test' -count=1
go test ./app/platform/api -run 'TestTeleabsAPI_TestStrategySnmpOidByTarget_.*' -count=1
go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1

cd /OneOPS/OneOps-UI
npm run smoke:snmp-oid-online-test-state
npm run smoke:snmp-oid-online-test-editor
npm run smoke:snmp-oid-online-test-page
```

Additional broad checks also completed after the initial closure:

```bash
cd /OneOPS/OneOps
go test ./app/platform/api -run 'TestTeleabsAPI_.*Snmp.*Oid.*Test|TestTeleabsAPI_.*RecordingRulesByTarget|TestTeleabsAPI_.*Grafana.*' -count=1

cd /OneOPS/OneOps-UI
npm run smoke:snmp-metric-contract
npm run smoke:snmp-workspace-view
```

Typecheck status:

- `npm run typecheck` is now confirmed passing for this slice.
- During investigation, the OID-related `vue-tsc` issues were traced to:
  - missing `oid` in the new smoke mock result shape
  - persistence normalizer casts in `snmpMetricContract.ts`
  - missing union-type imports after tightening those casts

### 11. Strategy Tree To Dashboard Tree Analysis Is Now Written Down

The next architectural problem is no longer OID testing.
It is the mismatch between the Teleabs strategy tree and the current Grafana dashboard generation unit.

Current product intent:

```text
策略集 -> 根仪表盘
策略 -> 具体仪表盘
策略父子关系 -> 仪表盘父子关系
target_part -> 这棵仪表盘树的目标实例
```

Current implementation reality:

```text
strategy_set_id + target_part + dashboard_variant
  -> one dashboard instance
```

This means the current mechanism is still fundamentally flat.

The key findings have now been written into three docs:

1. target model / mapping spec:
   - `/OneOPS/docs/superpowers/specs/2026-06-13-strategy-tree-dashboard-tree-mapping-design.md`
2. current mechanism issue list:
   - `/OneOPS/docs/superpowers/specs/2026-06-13-strategy-dashboard-current-mechanism-issues.md`
3. minimal pilot implementation plan:
   - `/OneOPS/docs/superpowers/plans/2026-06-13-strategy-dashboard-tree-pilot.md`

Core architectural conclusion:

- the current resolver flattens matched strategy items into one `effective_contract` too early for dashboard-node ownership;
- template inheritance (`SnmpGrafanaDashboardTemplate.parent_key`) is a layout tree, not the business dashboard tree;
- current target binding / panel binding / snapshot persistence are variant-scoped and target-scoped, but not strategy-node-scoped;
- current automatic generation naturally tends toward “one strategy set, one oversized dashboard per variant”.

Recommended implementation direction was:

```text
strategy tree
-> dashboard logical tree
-> target-scoped dashboard instance tree
```

Minimum pilot expected by the new plan was:

- one root dashboard owned by `strategy_set`
- one strategy dashboard per matched strategy node
- explicit parent/child dashboard relationships in persistence
- keep the old flat path available while piloting the new tree path

### 12. Strategy Dashboard Tree Pilot Is Now Implemented In Backend

The minimal backend-only pilot from:

- `/OneOPS/docs/superpowers/plans/2026-06-13-strategy-dashboard-tree-pilot.md`

is now landed.

New routes:

```text
POST /platform/metrics/teleabs/strategy-sets/:id/metric-contract/grafana/dashboard-tree/materialize/dry-run/by-target
POST /platform/metrics/teleabs/strategy-sets/:id/metric-contract/grafana/dashboard-tree/save/by-target
```

Current pilot behavior:

- tree dry-run reuses the existing target-scoped flat Grafana materialization result;
- the backend now expands the selected strategy item back into a visible strategy tree by re-introducing ancestor strategy nodes that are declared in the same strategy set;
- one `root` dashboard node is created for the strategy set;
- one `strategy` dashboard node is created per relevant strategy node in the pilot tree;
- parent/child relationships are persisted through:
  - `dashboard_role`
  - `owner_strategy_id`
  - `parent_dashboard_code`
  - `root_dashboard_code`
  on target-binding, panel-binding, and snapshot rows;
- the old flat Grafana dry-run/save path is still kept for compatibility.

Current ownership split is intentionally conservative:

- root keeps identity / platform-style overview panels;
- strategy nodes now prefer stronger strategy evidence before falling back to `metric_group_key`:
  - if panel-level strategy ownership is specific, use it;
  - if `strategy_ids` is still broad/set-wide, derive ownership from selected capability keys;
  - only then fall back to the old `metric_group_key` heuristic;
- target materialization still currently resolves one matched strategy item in the real `strategy_selector` path,
  but the helper path now prunes ancestor matches and keeps the deepest matching strategy id when capability-derived ownership becomes multi-strategy again in future flows;
- tree dry-run/save responses now also expand `item_contracts` to include the matched leaf plus same-set ancestors,
  but this expansion is response-context only for now; it does not change the current panel planning path or flat target materialization behavior;
- tree dry-run/save responses now also carry `matched_strategy_ids`,
  so callers can distinguish:
  - the real leaf match used by current target resolution;
  - the ancestor-expanded `item_contracts` shown for tree context;
- strategy ownership is restored structurally, but panel ownership is still not the final dashboard-family model.

Focused verification completed for this pilot:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*DashboardTree.*' -count=1
go test ./app/platform/api -run 'TestTeleabsAPI_.*DashboardTree.*' -count=1
go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1
```

Current boundary after this pilot:

- backend tree dry-run/save routes now exist;
- root/strategy dashboard split now exists in persistence metadata;
- parent/child dashboard instance links now exist in the pilot save path;
- old flat `grafana/dashboards/*` routes are still unchanged;
- no frontend dashboard-tree UI exists yet;
- no full dashboard-family normalization or panel-ownership perfection is claimed yet.

### 13. Frontend Dashboard Tree Pilot Now Covers Dry-Run And Save

The Strategy Set detail drawer now has a minimal frontend pilot for the new tree path.

Files added or updated:

- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/StrategySetDetailDrawer.vue`
- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/snmpStrategySetDashboardTreeState.ts`
- `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`
- `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-dashboard-tree-state-smoke.ts`
- `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-dashboard-tree-drawer-smoke.ts`

Current frontend pilot behavior:

- reuses the existing `target_part` input in `StrategySetDetailDrawer`;
- keeps the old flat Grafana save buttons unchanged;
- adds `预览仪表盘树` for tree dry-run;
- adds `保存仪表盘树` for tree save;
- shows a read-only node table with:
  - `node_key`
  - `role`
  - `owner_strategy_id`
  - `parent_node_key`
  - `dashboard_code`
  - `save_status` on tree-save results
    - `created`
    - `reused_updated`
    - `reused_unchanged`
  - `dashboard_content_changed` on reused nodes
  - `panel_bindings_changed` on reused nodes
  - `save_batch_id` on tree-save responses
  - `parent_dashboard_code`
  - `root_dashboard_code`
  - `panel_binding_count`
- shows a compact save summary after tree save:
  - whether save succeeded
  - saved node count
  - created node count
  - reused-updated node count
  - reused-unchanged node count
  - dashboard-content changed count
  - panel-bindings changed count
  - `save_batch_id`
  - dashboard variant
- adds `回看本次保存批次` in `StrategySetDetailDrawer`, which calls a new read-only backend endpoint to reload the persisted node-level audit rows for the current `save_batch_id`
- adds `加载最近保存批次` in `StrategySetDetailDrawer`, which calls a new read-only backend endpoint to list recent save batches for the current `(strategy_set_id, target_part, dashboard_variant)` and then lets the user click `回看`
- tree save now best-effort auto-refreshes `recentSaveBatches` after a successful save, so users usually do not need to click `加载最近保存批次` immediately after saving
- the recent save-batch table now marks the latest saved batch with `当前批次`, making the auto-refreshed batch list easier to read after save
- the recent save-batch table now also marks the batch currently being replayed in the tree table with `正在回看`, so “latest saved” and “currently viewed” are no longer conflated
- the recent save-batch table now makes the replay action state-aware: the row currently being replayed shows `已回看` and disables the replay button instead of offering a redundant `回看`
- the tree title area now echoes the current replay context as `当前正在查看: <save_batch_id>`, so users can tell what historical batch is rendered without scanning the recent-batch table
- the tree title area now also provides `返回当前树`, which restores the latest in-memory save result and clears replay mode without making another backend call
- frontend now uses the same node table for both live save responses and persisted batch-summary replay, instead of introducing a second audit-only view

State handling now separates preview and save concerns:

- `loading` continues to represent tree dry-run;
- `saveLoading` represents tree save;
- `result` holds the current visible tree payload;
- `saveResult` holds the explicit save response;
- `loadSaveSummary(strategySetId, saveBatchId)` reloads persisted node-level audit rows from the append-only save-summary table and repopulates `result`
- `loadRecentSaveBatches(strategySetId, targetPart)` loads recent save-batch summaries into `recentSaveBatches`
- `save(strategySetId, targetPart)` now also tries to refresh `recentSaveBatches` after a successful save; if that follow-up reload fails, the save itself still remains successful
- `currentSaveBatchId` is derived from `saveResult.save_batch_id` and is used only for frontend batch-row highlighting
- `currentViewedBatchId` is set only by `loadSaveSummary(...)` and cleared by preview/save/reset flows; it is used only for frontend “正在回看” row highlighting
- replay button enablement is now derived from `currentViewedBatchId`; no backend state or persisted flag was added for this interaction
- `showCurrentSavedTree()` restores `result` from `saveResult` and clears `currentViewedBatchId`; it is a frontend-only view switch, not a new backend query

Current backend pilot behavior additionally includes:

- `GET /platform/metrics/teleabs/strategy-sets/:id/metric-contract/grafana/dashboard-tree/save-summary/by-batch/:save_batch_id`
- `GET /platform/metrics/teleabs/strategy-sets/:id/metric-contract/grafana/dashboard-tree/save-batches?target_part=...&dashboard_variant=...&limit=...`
- resolver method `GetStrategySetGrafanaDashboardTreeSaveSummaryByBatch`
- resolver method `ListStrategySetGrafanaDashboardTreeSaveBatches`
- persisted rows in `platform_teleabs_strategy_set_dashboard_save_summary` are reconstructed back into:
  - `node_key`
  - `parent_node_key`
  - `parent_dashboard_code`
  - `root_dashboard_code`
  - `save_status`
  - `dashboard_content_changed`
  - `panel_bindings_changed`
- recent batches are aggregated from the same append-only table into:
  - `save_batch_id`
  - `matched_strategy_ids`
  - `node_count`
  - `created_count`
  - `updated_count`
  - `unchanged_count`
  - `content_changed_count`
  - `bindings_changed_count`
  - `created_at`
- `reset()` clears both preview and save state.

Focused verification completed for this frontend slice:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-strategy-set-dashboard-tree-state
npm run smoke:snmp-strategy-set-dashboard-tree-drawer
npm run smoke:snmp-strategy-set-recording-rule-drawer
npm run smoke:snmp-strategy-set-grafana-dashboard-save-action
npm run typecheck
git diff --check
```

Current boundary after this frontend pilot:

- the new tree backend path is now minimally consumable from UI;
- users can preview and save the tree path without replacing the old flat path;
- tree save now returns node-level `save_status` (`created` / `reused_updated` / `reused_unchanged`) for minimal visibility;
- tree save also returns two reused-node change signals:
  - `dashboard_content_changed`
  - `panel_bindings_changed`
- tree save now also persists append-only node save audit rows in:
  - `platform_teleabs_strategy_set_dashboard_save_summary`
  grouped by `save_batch_id`
- the drawer header now makes view mode explicit:
  - `当前树视图`
  - `历史回看视图`
  and history replay still supports `返回当前树` without a new request
- the tree summary itself now also carries:
  - `叶子命中策略`
  - `视图模式`
  - `结果来源`
  so screenshots / copied results stay self-explanatory even when the header scrolls away
- `叶子命中策略` is now accurate in history replay too, because save-summary/by-batch also returns `matched_strategy_ids`
  instead of relying on frontend in-memory fallback only;
- recent save batch browsing can now also distinguish the leaf matched strategy without opening a batch first,
  because the batch list itself carries `matched_strategy_ids`;
- the tree view is still read-only;
- there is still no frontend editing of node ownership or hierarchy;
- this frontend pilot loop should now be treated as closed;
- backend ownership refinement has started, but this is still a bounded pilot refinement rather than full dashboard-family normalization;
- tree planner now uses `matched_strategy_ids` only as a narrow leaf tie-breaker
  when a panel binding declares the whole strategy chain in `strategy_ids`
  and `selected_capability_keys` do not provide a more specific ownership signal;
- for reused tree nodes, `panel_bindings_changed` is now emitted as a deterministic boolean
  even when the previous owned binding set was empty, so save/replay consumers no longer
  need to treat `nil` as a separate “unchanged but unknown” state;
- the frontend drawer now makes the rollout boundary explicit:
  tree actions are labeled as a `Pilot 入口`, and the drawer states that this path
  validates strategy-tree -> dashboard-tree mapping without replacing the existing flat save path;
- the drawer copy now also names `保存到平台 / 保存并同步` as the default formal entry,
  so the rollout contrast is explicit in both directions rather than only labeling the tree path as experimental;
- the action button row itself now visually groups the two routes with
  `Pilot 入口` and `默认正式入口` tags, so the rollout split is visible even before reading the helper copy;
- tree pilot actions now stay disabled until a target device code / ID is entered,
  which removes the last easy path to empty-target preview/save/batch-list errors from the drawer UI;
- the frontend drawer now also supports a real rollout gate via
  `VITE_ENABLE_SNMP_DASHBOARD_TREE_PILOT !== 'false'`:
  when disabled, tree-pilot actions and tree result rendering disappear, while the flat formal path remains visible;
- the flat formal path now also guards its biggest sequencing gap:
  if the current target does not have a successful in-session recording-rule publish result,
  `保存到平台 / 保存并同步` first shows a warning confirmation instead of silently proceeding;
- the drawer now also exposes one explicit current-session formal-closure panel for the default path:
  it shows `监控策略 -> Recording Rule -> 仪表盘` stage/readiness status for the current target,
  makes the next recommended action explicit,
  and now treats rule-publish readiness as backend-derived while keeping the rest of the chain session-scoped;
- the backend now also exposes a strict by-target recording-rule readiness read path backed by
  `platform_snmp_recording_rule_publish_records`, so the formal drawer and flat save guard
  no longer depend only on in-session publish memory after a refresh;
- readiness semantics are intentionally narrow:
  it reports the latest attempt status for `strategy_set_id + target_part`,
  but `ready=true` means there is at least one successful publish record for that same target;
- readiness is now also version-aware against the current by-target materialized YAML:
  the backend returns `current_yaml_sha256` and `version_matched`,
  the formal-closure panel treats backend readiness as truly save-ready only when
  `ready=true && version_matched=true`,
  and a stale successful publish now surfaces as `版本不一致 / 当前规则已变更，请重新发布规则`
  instead of being treated as dashboard-save ready;
- the flat save guard is now also aligned with that stronger semantics:
  `无成功发布记录` still stays a warning-level confirm,
  but `ready=true && version_matched=false` becomes a hard stop that requires re-publishing rules first
  before `保存到平台 / 保存并同步` can proceed;
- after a successful `发布规则`, the drawer now also re-queries backend readiness for the same target,
  so a stale `version_matched=false` state is cleared automatically once the new rule publish succeeds,
  instead of waiting for a later manual reload or save-click refresh;
- that post-publish readiness refresh is now also same-target scoped:
  if the operator changes the target input while the publish request is still in flight,
  the drawer does not overwrite the current target’s readiness with the older publish target result;
- after a current tree save succeeds, the drawer now also shows an explicit info alert that
  this save is still for pilot validation / audit and does not replace the default flat save+sync workflow;
- clicking `保存仪表盘树` now requires an explicit confirmation dialog that repeats the same pilot-only boundary,
  so the user sees the rollout guard before the write action rather than only after the save returns;
- while the drawer is in `历史回看视图`, `保存仪表盘树` is now disabled and relabeled to `返回当前树后保存`,
  so history replay can no longer be mistaken for an editable/saveable working context;
- the next logical step should move back to larger-scope work such as backend ownership refinement, tree-editing design, or rollout strategy, rather than more micro-UX iteration here.

### 14. Definition-Layer Vs Runtime-Layer Correction Is Now Explicit

One important correction has now been written down:

- `/OneOPS/docs/superpowers/plans/2026-06-14-snmp-definition-runtime-closure-correction.md`
- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-definition-layer-model-note.md`
- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-strategy-dashboard-panel-ownership-mapping-note.md`
- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-current-panel-family-owner-decision-table.md`
- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-tree-pilot-gap-map.md`
- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-short-name-baseline.md`
- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-definition-closure-summary.md`
- `/OneOPS/docs/superpowers/plans/2026-06-14-snmp-panel-slot-owner-first-cut.md`

The key clarification is that recent work closed a meaningful runtime loop:

```text
strategy_set_id + target_part
  -> recording rule preview / materialize / publish
  -> dashboard save / save+sync / readiness
```

but that runtime loop must not be mistaken for completion of the dashboard-family business model.

The corrected boundary is:

```text
definition layer:
StrategySet -> StrategyTree -> Dashboard Logical Tree

runtime layer:
(strategy_set_id, target_part) -> recording rules / dashboard instance materialization
```

Current correction direction after this note:

- stop prioritizing more by-target runtime hardening as the main line;
- treat current tree pilot as a transitional bridge, not as full definition-model completion;
- shift the next primary task back to definition-layer closure:
  - object identities
  - ownership matrix
  - mapping from strategy node to dashboard logical node
- the first concrete implementation line under that correction is now
  `PanelSlot ownership first cut`:
  add short explicit `OwnerKind` / `OwnerKey` to panel bindings,
  then let tree planning consume those fields before runtime heuristics.
- the first cut is now partially implemented in code:
  - `SnmpGrafanaPanelBindingPreview` now carries short explicit owner fields
    `owner_kind` and `owner_key`;
  - by-target Grafana dashboard materialization now assigns:
    - root/evidence/navigation style bindings -> `owner_kind=root`, `owner_key=strategy_set_id`
    - single-strategy bindings -> `owner_kind=strategy`, `owner_key=strategy_id`
    - ambiguous bindings -> unresolved empty owner rather than root fallback;
  - dashboard-tree planning now consumes explicit owner first,
    then falls back to existing strategy/capability/group heuristics.
  - current tree dry-run/save node previews now also expose `slot_owners`
    such as `root:set-1`, `strategy:huawei-s5735-switch`, or `unowned`,
    so the UI can distinguish `node owner` from `slot owner` without opening full binding detail.
  - current tree dry-run/save node previews now also expose `unowned_slot_count`;
    current materialized trees return a real count,
    while historical save-summary replay still leaves that field empty rather than faking `0`.
  - current tree dry-run/save node previews now also expose `unowned_families`,
    using short panel-family labels such as `interface_basic.port_state` or `system_basic.cpu`
    so unresolved slot clusters can be read directly without opening full binding detail;
    historical save-summary replay still leaves that field empty rather than inventing a family list.
  - the frontend tree pilot now also turns `unowned_slot_count > 0` into an explicit warning,
    instead of leaving it only as one table number;
    current wording is kept narrow and definition-layer focused.
  - the frontend tree pilot summary/warning now also aggregates `unowned_families`
    across the current tree result,
    so operators can tell whether unresolved ownership is mainly concentrated in
    `interface_basic.port_state`, `system_basic.cpu`, or another short family label
    without scanning each node row first.
  - nodes with `unowned_slot_count > 0` now also show a direct `待归属` tag in the tree table,
    so operators can spot unresolved nodes without scanning the numeric column first.
  - owner resolution is now also slightly stricter on the backend:
    if one slot’s candidate owners are only a parent/child chain,
    owner selection now prefers the deepest strategy owner instead of leaving the slot `unowned`.
  - for strategy-owned families that may render without a populated `selected_capability_keys`
    (currently validated on `interface_basic.port_state*` and `system_basic.cpu_memory.trend`),
    binding planning now also falls back to definition-layer `capability_keys`
    before giving up and widening to the whole strategy tree;
    this is the current first concrete step that turns two real families
    from heuristic-heavy/unowned-prone into explicit strategy-owned bindings.
  - dashboard-tree binding strategy resolution now also consumes that same
    `capability_keys` fallback,
    so the tree planner itself no longer depends only on `selected_capability_keys`
    when narrowing strategy-owned slots for those families.
  - two root-summary families are now also made explicit in the root-owner rule:
    `device.overall_health` and `device.active_alerts`
    no longer drift into strategy ownership just because their capability set overlaps
    with one concrete child strategy; this matches the current definition-layer note
    that cross-strategy total-health / alerts summaries belong to the root node.
  - the earlier `capability_keys` fallback is now also locked by stronger regression coverage
    on strategy-local hardware detail panels:
    `device_metrics.temperature.sensors`,
    `device_metrics.fan_status.components`,
    `device_metrics.power_status.components`,
    `device_metrics.transceiver.rx_top4`,
    `device_metrics.transceiver.rx_last4`
    are all now explicitly asserted to stay strategy-owned in by-target materialization.
  - `routing_l2.summary` is now also treated as an explicit root-summary family,
    rather than drifting into child strategy ownership from its underlying
    `l2_mac_table` evidence source;
    the current interpretation is that this compact “Routing & Layer 2” rollup
    behaves like a cross-strategy overview block on the root dashboard.

The new definition-layer model note now makes one narrow thing explicit:

- which objects are definition-layer objects;
- which objects are runtime-layer objects;
- who owns each object;
- whether each object is allowed to depend on `target_part`.

That note should now be treated as the immediate prerequisite before any more tree-pilot or by-target runtime polishing.

The new panel-ownership mapping note then narrows the next missing design question further:

- how one `strategy node` maps to one `dashboard logical node`;
- how root dashboard ownership differs from strategy dashboard ownership;
- how `panel slot ownership` must be decided before runtime materialization rather than inferred late from target-scoped results.

The new current panel-family owner decision table then makes the first practical ownership baseline explicit:

- current detailed families such as `interface_basic.*` and `system_basic.*` default to `strategy_id` ownership;
- current overview / navigation / platform-evidence style panels default to `strategy_set_id` ownership;
- root should no longer be treated as the generic fallback owner just because runtime heuristics are weak.

The new tree-pilot gap map then makes the current bridge state easier to read with shorter names:

- `RootNode`
- `StrategyNode`
- `NodeOwner`
- `LeafMatch`
- `SaveBatch`

and clarifies which pilot fields already align with the definition model versus which fields are still runtime evidence or audit-only artifacts.

The new short-name baseline then freezes the preferred naming direction:

- short object names first
- one name for one meaning
- runtime evidence and logical ownership must not share the same short name

So follow-up discussion should prefer names like:

- `RootNode`
- `StrategyNode`
- `NodeOwner`
- `LeafMatch`
- `SaveBatch`

instead of continuing to expand long mixed-layer phrases.

The new definition-closure summary page is now the shortest re-entry point for this corrected direction:

- boundary
- core objects
- owner split
- current pilot gap

Anyone resuming this line should read that one-page summary first, then drill into the narrower notes only if needed.

There is now also one new batch-oriented execution note:

- [2026-06-14-snmp-family-closure-matrix.md](/OneOPS/docs/superpowers/plans/2026-06-14-snmp-family-closure-matrix.md)

That note is important because it changes the execution unit from:

- one helper / one patch / one family at a time

to:

- one family group at a time

Current recommendation is to use that matrix as the remaining closure denominator:

- `closed`
- `partial`
- `open`

and drive the remaining work by moving family rows to `closed`,
instead of continuing to measure progress patch-by-patch.
- 2026-06-14: family-closure execution has switched from micro-patches to the batch matrix in [2026-06-14-snmp-family-closure-matrix.md](/OneOPS/docs/superpowers/plans/2026-06-14-snmp-family-closure-matrix.md). Topology evidence families (`l2_neighbors.summary`, `l2_mac_table.*`, `l3_arp_table.*`, `l2_vlan_table.*`, `l2_stp_state.*`) are now frozen as `strategy`-owned in both the decision notes and regression tests. Current routing families (`l3_route_table.*`, `routing_bgp.*`, `routing_ospf.*`) are now explicitly treated as future scope, not part of the current switch dashboard-tree closure denominator, because they belong to a possible future routing-capable class or variant baseline rather than the current switch baseline. This means the current active family denominator can now be treated as closed, and any future routing inclusion should start as a separate batch instead of re-opening the current closure work.
- 2026-06-14: the next line is now formalized in [2026-06-14-snmp-routing-family-activation-batch.md](/OneOPS/docs/superpowers/plans/2026-06-14-snmp-routing-family-activation-batch.md). That plan no longer uses runtime data presence as a gate for baseline family existence. The rule is now simpler: generation decides what families exist in a class/variant baseline, runtime only decides the current panel state. Routing therefore re-enters closure only when a routing-capable class or variant baseline is intentionally defined.
- 2026-06-14: the simplified rule is now written down in [2026-06-14-snmp-class-baseline-generation-rule.md](/OneOPS/docs/superpowers/specs/2026-06-14-snmp-class-baseline-generation-rule.md). Use its short split going forward: `ClassBaseline` decides what families exist, `VariantBaseline` decides which view includes them, and `PanelState` only describes runtime state (`has_data / no_data / not_exposed`). Do not re-introduce runtime-gated baseline logic when discussing routing or any future family.
- 2026-06-14: the next class-level step is now captured in [2026-06-14-snmp-routing-capable-switch-baseline.md](/OneOPS/docs/superpowers/specs/2026-06-14-snmp-routing-capable-switch-baseline.md). That note defines the first routing-capable switch baseline as an additive class baseline over the current switch baseline, keeps routing families strategy-owned by default, and explicitly avoids per-device branching or runtime-gated baseline existence.
- 2026-06-14: baseline selection is now captured in [2026-06-14-snmp-switch-baseline-selection-rule.md](/OneOPS/docs/superpowers/specs/2026-06-14-snmp-switch-baseline-selection-rule.md). The current rule is: baseline follows class intent plus matched strategy responsibility. In practice, OneOPS should choose `routing-capable switch baseline` only when the matched strategy side actually carries routing responsibility (`l3_route_table.*`, `routing_bgp.*`, `routing_ospf.*`), not because one target currently has routing data.
- 2026-06-14: the routing trigger itself is now narrowed in [2026-06-14-snmp-routing-responsibility-mapping-table.md](/OneOPS/docs/superpowers/specs/2026-06-14-snmp-routing-responsibility-mapping-table.md). Only `l3_route_table.*`, `routing_bgp.*`, and `routing_ospf.*` count as routing responsibility for baseline selection. Topology evidence (`l2_neighbors.*`, `l2_mac_table.*`, `l3_arp_table.*`, `l2_vlan_table.*`, `l2_stp_state.*`) stays outside that trigger and should not accidentally promote an ordinary switch into the routing-capable baseline.
- 2026-06-14: the first backend-only baseline-selection cut is now implemented. In `/OneOPS/OneOps`, switch dashboard generation has one explicit definition-layer selection step before builtin panel-definition fallback. The current helper only distinguishes `switch.current` and `switch.routing_capable`, uses matched strategy responsibility as the trigger, and deliberately ignores runtime data presence. This cut is intentionally narrow: routing-capable selection is now wired into the generation path, but it still reuses the current switch panel set until the dedicated routing baseline panel expansion is implemented.
- 2026-06-14: the next generation cut is now implemented too. `switch.routing_capable` no longer reuses the current switch panel set unchanged; it now adds six routing families at generation time: `l3_route_table.ipv4_count`, `l3_route_table.ipv6_count`, `routing_bgp.neighbor_total`, `routing_bgp.established_total`, `routing_ospf.neighbor_total`, and `routing_ospf.full_total`. The current switch baseline remains unchanged, and runtime data presence still does not participate in baseline existence or selection. Supporting backend work also landed in the same batch: routing summary contract import now recognizes route-count, BGP, and OSPF count fields, and Grafana expression generation now covers all six routing-capable baseline families.
- 2026-06-14: baseline selection is no longer only internal helper logic. Flat materialization/save responses and tree dry-run/save responses now all carry the same short `Baseline` object: `class_baseline`, `variant_baseline`, `reason`. This is the current explicit generation-resolution boundary for switch dashboards, and it should be preferred over adding more ad-hoc booleans or hidden helper-only branches.
- 2026-06-14: that same `Baseline` object now also propagates into tree save history. `save-summary/by-batch` and recent `save-batches` responses derive and return the same `class_baseline / variant_baseline / reason`, so current tree results and historical tree replay now speak one definition-layer language instead of splitting into “current generation” vs “history audit” dialects.
- 2026-06-14: baseline resolution is also no longer assembled ad hoc inside each generation caller. `/OneOPS/OneOps` now has one internal switch-generation resolver that returns `class baseline + response Baseline + resolved template/panel set` together, and flat materialization already consumes that unified result directly. If this line continues, prefer extending that resolver boundary instead of reintroducing scattered helper combinations.
- 2026-06-14: the next structural closure cut is now in place too. `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_baseline_module.go` is the new internal baseline boundary for switch dashboards. `ClassBaseline`, `VariantBaseline`, routing-responsibility detection, baseline selection, strategy-ID baseline derivation, and baseline-aware template selection now live there instead of being split between resolver helpers and generator callers. Keep runtime gating out of that module.
- 2026-06-14: generation is now also unified one layer lower. `/OneOPS/OneOps` has one internal switch-dashboard materialization resolver, and flat dry-run/save plus tree dry-run/save now all consume that same internal path instead of tree reaching generation by bouncing through separate public assembly steps. If more work lands here, keep extending the shared materialization path rather than creating tree-only or flat-only generation branches.
- 2026-06-14: that shared materialization path now also has its own internal generation result object. Flat dry-run is now just a DTO adapter over the internal result, and tree planning helpers consume the same internal result directly. This means `Baseline + preview summaries + dashboard JSON + bindings + materialization` now travel together inside one shared generation shape before any public response mapping happens.
- 2026-06-14: the shared switch-dashboard generation logic is now also behind a dedicated internal generator type, not just a growing set of resolver methods. `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_generator.go` now consumes the baseline module and owns dashboard generation plus binding-owner enrichment, while `MetricCapabilityContractResolver` keeps the public orchestration entrypoints. If this line continues, prefer extending that generator boundary instead of pushing more switch-generation detail back into the top-level resolver.
- 2026-06-14: there is now also a dedicated internal switch dashboard service boundary above the generator. `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_service.go` now owns shared flat dry-run assembly, shared tree dry-run assembly, and the shared tree-generation bundle used before tree-save persistence starts. `MetricCapabilityContractResolver` still owns public API methods and persistence, but it no longer has to re-stitch generation pieces separately for flat dry-run, tree dry-run, and tree save. The active assembly split is now `resolver -> baseline module -> generator -> service`.
- 2026-06-14: the active save path now also runs through a dedicated internal persistence boundary. `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_persistence_service.go` now owns flat save persistence and tree save persistence orchestration, while `MetricCapabilityContractResolver` keeps only the public save entrypoints. The active split for the current switch-dashboard backend line is now `resolver -> baseline module -> generator -> service -> persistence service`, and future work should extend those internal boundaries instead of re-growing resolver-owned save flow assembly.
- 2026-06-14: the baseline side is now closed one layer further too. `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_baseline_module.go` now owns `ClassBaseline / VariantBaseline / reason`, routing-responsibility detection, strategy-ID baseline derivation, and baseline-aware template selection. The active internal split for the current switch-dashboard backend line is now `resolver -> baseline module -> generator/service/persistence`, so future baseline work should extend that module instead of re-scattering baseline rules into resolver helpers or per-caller branches.
- 2026-06-14: two baseline-module correctness gaps were also closed in the same batch. `resolveForStrategyIDs(...)` is now baseline-only instead of being coupled to template resolution success, and routing-capable selection now preserves its routing-capable template identity even when the current switch template came from DB-backed resolution. That keeps history/audit baseline derivation and generation-time baseline-aware template selection on the same definition-layer semantics.
- 2026-06-14: the next closure target is now explicitly broader than the current switch line. See [2026-06-14-snmp-generic-baseline-model-closure-plan.md](/OneOPS/docs/superpowers/plans/2026-06-14-snmp-generic-baseline-model-closure-plan.md). The goal of that batch is to lift the current `switch.current / switch.routing_capable` path into one generic SNMP target-class model, add an explicit `snmp.generic` baseline for non-switch SNMP targets, and require all future SNMP dashboard generation to enter through the same `TargetClass -> ClassBaseline -> VariantBaseline -> Owner -> Generation` contract.
- 2026-06-14: that generic SNMP target-class closure is now also implemented on the backend. `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_target_class_module.go` is the active generic entry for baseline resolution. `snmp.generic` now exists as an explicit non-switch SNMP baseline, while `switch.current` and `switch.routing_capable` are additive specializations under the same model. Current dashboard generation/history paths therefore no longer need to assume that every SNMP target is fundamentally switch-shaped before a baseline can be chosen.
- 2026-06-14: the last generic-baseline save/tree correctness gap is now closed too. When backend callers omit `dashboard_variant`, flat save and tree save now persist the resolved `Baseline.VariantBaseline` instead of falling back to the switch default. In practice that means generic SNMP targets now consistently save/replay under `snmp.generic.operations`, while HTTP save/tree endpoints still keep their existing explicit-variant contract.
- 2026-06-14: quick env now seeds the same SNMP dashboard baseline family explicitly. `zzzzzzzzzz-snmp-grafana-dashboard-template-bootstrap.sql` now includes `snmp.generic` as the generic SNMP template root and `snmp.switch.routing_capable` as the routing-capable switch delta template, so seeded template resolution no longer stops at the legacy switch-only family.
- 2026-06-14: quick env no longer stops at SNMP template seeding. `/OneOPS/quick_env/scripts/ensure_snmp_dashboard_instances.sh` is now wired into `quick_env/start.sh`, so current environments auto-save real SNMP dashboard instances after startup. The live path now guarantees: existing switch targets keep `snmp.switch.operations`, and once a successful OOB SNMP server target exists, `server_oob_snmp` will persist a real `snmp.generic.operations` dashboard instance without manual demo-only steps.
- 2026-06-14: quick env now also closes the live routing-capable gap. `/OneOPS/quick_env/docker-entrypoint-initdb.d/zzzzzzzzzz-snmp-switch-routing-capable-strategy-set-bootstrap.sql` seeds an independent `snmp_switch_routing_capable` suite with a Huawei VRP routing overlay leaf that carries explicit routing responsibility, and `/OneOPS/quick_env/scripts/ensure_snmp_dashboard_instances.sh` now persists one real `switch.routing_capable` dashboard instance for `DVC2C4468B0B813`. In the current environment this means the dashboard list now has all three real SNMP classes in use: ordinary switch, generic SNMP, and routing-capable switch.
- 2026-06-14: shared dashboard persistence is now the intended SNMP save model. Flat SNMP save no longer treats target identity as the primary dashboard identity when `class_baseline + variant_baseline + template_key` are unchanged; instead it saves one shared dashboard object and fans multiple targets into target-binding rows. The persistence layer now rewrites saved dashboard `uid/title` to class-level identity and clears target-specific templating defaults from stored JSON. Quick env runtime ensure also drops the legacy unique `uk_strategy_target_dashboard_code` constraint if present, purges legacy per-target SNMP dashboard rows for a variant, and rebuilds them through the shared save path.
- 2026-06-14: class-level generation now keeps panel families even when live runtime `supports` or rule evidence are weak. The materializer no longer drops SNMP panels by support-gate; instead it keeps baseline-owned panels and fills missing live queries with a harmless `no data` PromQL target. This is the current fix for the poor shared `OneOPS SNMP Switch Ops` result: the saved shared switch dashboard now preserves the CE168-derived operations structure instead of collapsing to a 5-panel runtime-only subset.
- 2026-06-14: the current closure target is no longer “one class-level shared flat switch dashboard”. See [2026-06-14-snmp-suite-strategy-dashboard-tree-design.md](/OneOPS/docs/superpowers/specs/2026-06-14-snmp-suite-strategy-dashboard-tree-design.md) and [2026-06-14-snmp-suite-strategy-dashboard-tree-closure-plan.md](/OneOPS/docs/superpowers/plans/2026-06-14-snmp-suite-strategy-dashboard-tree-closure-plan.md). The active rule is now:
  - `dashboard selection = projection of strategy selection`
  - `monitoring suite -> root dashboard`
  - `matched strategy node -> strategy dashboard node`
  - `target -> binding to one dashboard tree`
- 2026-06-14: suite-root plus strategy-node dashboard tree save is now the primary backend path. Flat save still exists, but it is only a compatibility projection of the saved root node. Current switch/generic/routing-capable rows therefore describe suite roots, while the full business model lives in the saved dashboard tree and its strategy child nodes.
- 2026-06-14: class baselines (`snmp.generic`, `switch.current`, `switch.routing_capable`) are now generation floors, not independent business selectors. They still shape reusable panel-family floors and layout/template reuse, but they must not replace matched strategy selection.
- 2026-06-14: quick env runtime ensure is now tree-first too. The switch path is healthy only when the suite root keeps explicit root-summary responsibility (`Device Identity`, `Overall Health`, `Active Alerts`) and at least one strategy dashboard under that root keeps explicit strategy-display responsibility (`Interface Utilization Top 10`, `Packets Per Second`, `OneOPS config evidence`).
- 2026-06-14: the CE168 row remains intentionally visible:
  - `OneOPS SNMP Switch Ops - CE16808-172-21-165-11`
  but it is now reference-only. It should be treated as a quality sample and future overlay/layout input, not as the canonical mother template for the shared switch business model.
- 2026-06-14: product visibility is now nudged toward the same model. The Grafana dashboard list no longer needs to explain SNMP rows only as generic “根/子仪表盘”; current UI semantics are `suite root / strategy / reference`, and the strategy-set drawer now presents `Root + Strategy Dashboard Tree` as the formal path while flat save remains the compatibility `root projection`.
- 2026-06-14: the Grafana dashboard list now carries one more explicit suite-root affordance: `查看策略树`. Root rows can now open a dedicated modal that lists their `strategy dashboard nodes`, which makes the user path match the current business rule more directly:
  - list page -> `suite root`
  - tree modal / strategy-set drawer -> `strategy dashboards`
  This is a UI-only visibility step; it does not change backend generation or persistence semantics.
- 2026-06-14: that visibility step is now also connected to the formal strategy-set drawer path. The suite-root strategy-tree modal can deep-link to `StrategyTemplate` and auto-open `StrategySetDetailDrawer` for the bound strategy set, while forwarding `focusStrategyId` from a clicked strategy-dashboard row. The drawer now exposes that focus context inside the dashboard-tree section, so the product path is no longer “list -> modal -> stop”; it is now “list -> modal -> formal tree drawer”.
- 2026-06-14: the next dashboard batch must not start from CE168 layout copying. The fixed entry is now:
  - per-strategy `effective_contract`
  - per-strategy dashboard derivation
  - CE168 decomposition into reusable concept / regenerate / overlay-only / forbidden hard-coded sample
  See:
  - `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-strategy-effective-metrics-dashboard-derivation-design.md`
  - `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-strategy-effective-metrics-inventory.md`
  - `/OneOPS/docs/superpowers/plans/2026-06-14-snmp-strategy-dashboard-regeneration-plan.md`
  This is the current correction to preserve:
  - every current SNMP strategy row needs its own strategy dashboard node;
  - CE168 is a quality reference sample only;
  - hard-coded interface panels and vendor-specific literal titles must not be copied directly into shared generation.
- 2026-06-14: the first runtime-backed effective-metrics inventory now exists too. `/OneOPS/quick_env/scripts/export_snmp_strategy_effective_metrics_inventory.py` exports it from the live OneOPS API into `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-strategy-effective-metrics-inventory.md`. The current runtime result is important: 17 network-oriented SNMP strategies currently share one identical effective metric signature, so the next dashboard regeneration batch must treat CE168 as layout/reference inspiration only and regenerate topology/routing/hardware nodes from actual strategy metrics instead of copying vendor- or interface-specific sample panels.
- 2026-06-14: the next output after the live inventory is now exported too. `/OneOPS/quick_env/scripts/export_snmp_strategy_dashboard_derivation_table.py` produces:
  - `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-strategy-dashboard-derivation-table.md`
  - `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-strategy-dashboard-derivation-table.json`
  This derivation table is the current machine-readable rule for regeneration:
  - keep one strategy dashboard node per strategy row;
  - allow same-signature strategies to share one recipe;
  - keep firewall/routing/server node identity explicit even when current metrics are sparse;
  - treat CE168 panel content only as reusable concept / regenerate-only reference / forbidden carryover, never as direct mother-template content.
- 2026-06-14: those regeneration semantics are now exposed in the formal dashboard-tree UI too. Tree dry-run, tree save, and save-summary replay nodes all carry `recipe_key`, `panel_families`, `metric_group_keys`, `display_scope_summary`, `optional_overlay_families`, and `ce168_handling_summary`, and `StrategySetDetailDrawer` renders them directly. The tree UI is therefore now the current place to read both:
  - root/strategy dashboard semantics; and
  - per-strategy dashboard regeneration intent.
- 2026-06-14: the machine-readable node-definition layer now exists as well. `/OneOPS/quick_env/scripts/export_snmp_strategy_dashboard_node_definitions.py` exports:
  - `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-strategy-dashboard-node-definitions.md`
  - `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-strategy-dashboard-node-definitions.json`
  This is the current artifact to consume before real Grafana regeneration:
  - one strategy row keeps one node definition;
  - `recipe_key` is reusable generation logic only;
  - `panel_families` + `metric_group_keys` define node-local metric responsibility;
  - `ce168_reusable_concepts`, `ce168_regenerate_panels`, and `ce168_forbidden_carryovers` are the only legal CE168 inputs.
- 2026-06-14: formal tree nodes now also surface `generated_panels`. This is the recipe-projected panel-definition preview for each root/strategy node. It still stops before final Grafana layout composition, but it gives the current structured answer to:
  - “which panel definitions does this strategy dashboard node currently generate?”
  This list is rendered directly in `StrategySetDetailDrawer`, alongside recipe, metric scope, and CE168 handling fields.
- 2026-06-14: `snmp.switch.topology-common` is now backed by its own node-local panel-definition source instead of filtering `switch.current`. The topology recipe explicitly owns the evidence-table and count-card set for `l2_neighbors`, `l2_mac_table`, `l3_arp_table`, `l2_vlan_table`, and `l2_stp_state`. `snmp.firewall.current-common` has now been split again into its own node-local recipe source: current mandatory families are still the same, but the generated panel source is firewall-local (`firewall` section and firewall-specific titles) instead of inheriting switch topology titles or flat switch interface/hardware panels.
- 2026-06-14: `device_metrics.default` no longer shows up as a raw fallback panel key in node regeneration previews. It now resolves into recipe-specific node-local panel definitions across recipes:
  - topology -> `Node Device Metrics`
  - firewall -> `Firewall Device Metrics`
  - server basic -> `Server Device Metrics`
  - server OOB -> `OOB Device Metrics`
  - device summary -> `Device Metrics Summary`
  This is still only the first step toward richer summary/detail regeneration, but it removes one more placeholder layer from the tree-first dashboard path.
