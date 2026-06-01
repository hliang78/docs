# Discovery: Device / Monitoring / Logging / Topology

Status: draft for user confirmation.

## User Direction Captured

- Program decision: online quality gate.
- First focus: device / monitoring / logging / topology.
- Environment: existing OneOPS / OneOPS-UI dev services and test database are allowed.
- Evidence: combination evidence.
- Gate shape: 4 independent sub-gates, not one all-or-nothing gate.
- Test data: long-lived fixture data named with `ONEOPS_GATE_*`.
- Fixture source: prepared before automation from MySQL test DB `192.168.0.199:3306/zb_firewall_199`; secrets are injected outside PRD artifacts.
- Safety: no default prohibition because this is a test environment, but PRD should still classify test actions by risk level.

## Confirmed Sub-Gate Success Definitions

| Sub-Gate | User Definition Of Success |
|---|---|
| Device | For each device, use the maximum verifiable field set derived from collected evidence plus platform fields as the success basis. Different devices may have different verifiable fields; avoid one-size-fits-all required field lists. |
| Monitoring | Monitoring task is delivered, task governance works, Prometheus can return monitoring data, and labels attached to metric data are correct. |
| Topology | Topology generation is refactored around Device V2 onboarding data and collection method; topology can be generated, shown by frontend, and drilled down. |
| Logging | Log-forward can apply; a real device-side log event can be triggered; Loki receives and returns the correct log. |

## Device Onboarding Findings

### Frontend Surface

- Device V2 routes exist for management, redesigned management, schema design, import batches, and ingest pipeline:
  - `OneOPS-UI/src/router/utils.ts:406`
  - `OneOPS-UI/src/router/utils.ts:418`
  - `OneOPS-UI/src/router/utils.ts:430`
  - `OneOPS-UI/src/router/utils.ts:442`
  - `OneOPS-UI/src/router/utils.ts:454`
- The frontend API contract has strong response assertions for Device V2 list/item/task shapes:
  - `OneOPS-UI/src/api/device/device-v2.ts:67`
  - `OneOPS-UI/src/api/device/device-v2.ts:87`
  - `OneOPS-UI/src/api/device/device-v2.ts:101`

### Backend Surface

- Legacy device inventory routes exist under `/device/inventory`:
  - `OneOPS/app/device/router/device.go:8`
- Device V2 routes cover list, schema gate, sync from/to V1, store pipeline, import batches, interfaces, status, store readiness, last DC2 collection, network overview, CRUD:
  - `OneOPS/app/device/v2/router/device_v2.go:8`
- Device V2 has broad backend tests under `OneOPS/app/device/v2`.

### Existing Gate Candidates

- `npm run typecheck:d2`
- `npm run smoke:d2-real-operation`
- `npm run smoke:d2-ingest-buttons`
- `OneOPS/scripts/device_v2_minimal_onboard.sh`
- Backend packages:
  - `go test ./app/device/...`
  - `go test ./app/device/v2/...`
- DeviceCollection2 collection/fact paths:
  - `OneOPS/app/device_collection2/router/device_collection2.go:20`
  - `OneOPS/app/device_collection2/router/device_collection2.go:24`
  - `OneOPS/app/device_collection2/router/device_collection2.go:25`
  - `OneOPS/app/device_collection2/router/device_collection2.go:26`

### Evidence Candidate

Combination evidence should include:

- API: create/import/list/get/status/store-readiness responses.
- DC2: collect-standardize-process run, latest facts and fact issues.
- Browser: ingest/import lifecycle screenshots and console/network status from `d2-real-operation-smoke.cjs`.
- Backend: Go test output for Device V2 import/store/schema.
- Database/log: import batch and store task IDs if available.

### Key Field Coverage To Validate

User-confirmed baseline: field coverage starts from `docs/openclaw-autodev/D2_INGEST_BASE_FIELD_TABLE.md`, but success is not a fixed full-field checklist for every device. The first device gate should use the D2 table as the field universe, then derive a per-device maximum verifiable field set from collected evidence, platform fields, DC2 facts and device capability.

Initial field groups from the D2 base table:

- Identity: `code`, `biz_code`, `name`, `biz_name`, `sn`, `asset_number`, `hostname`.
- Platform/type: `platform`, `platform_code`, `platform_name`, `catalog`, `catalog_code`, `catalog_name`.
- Status/manageability: `status`, `manageable`, `manage_status`, `manageable_status`, `core_store_status`.
- Access and credentials: `in_band_ip`, `out_band_ip`, `credential_ref_in_band`, `credential_ref_out_band`, `snmp_credential_ref`, `winrm_credential_ref`, `credential_refs`, `access_points`.
- Location: `region_name`, `region_code`, `site_name`, `site_code`, `rack_name`, `rack_code`, `rack_position`, `location_node_code`.
- Hardware/classification: `device_kind`, `device_type`, `device_model`, `device_model_code`, `device_model_name`, `vendor`, `model`, `manufacturer_code`, `manufacturer_name`.
- System profile: `system_version`, `patch_version`, `firmware_version`, `kernel_version`, `os_name`, `os_version`, `architecture`, `cpu_arch`, `cpu_model`, `cpu_cores`, `cpu_sockets`, `memory_total`, `memory_total_bytes`, `memory_slots`, `hardware`.
- Labels/organization: `tenant_name`, `tenant_code`, `namespace`, `function_area`, `labels`, `group_tags`.
- Batch/trace and store/collection state: `batch_id`, `row_no`, `validate_status`, `apply_status`, `error_code`, `error_message`, `matched_by`, `locator_trace`, `conflict_candidates`, `run_id`, `current_step`, `collection_plan_source`, `next_collection_plan`, `collection_plan_snapshot`, `manageable_pending_reasons`.

DC2 fact processors then add collected/parsed correctness evidence:

- Device identity facts normalize `hostname`, `vendor`, `platform`, `model`, `serial_number`, `os_version`, `sys_object_id`, `management_ip`, etc.
- Interface facts normalize `if_index`, `if_name`, `admin_status`, `oper_status`, `mac`, `speed_bps`, `mtu`, etc.
- Topology neighbor facts normalize LLDP/CDP-style local/remote interface and remote identity hints.

### Device V2 -> DC2 Target Link

`DeviceCollection2` can resolve Device V2 records into collection targets. The resolver reads:

- target identity from Device V2 `code` / `id`;
- address from `in_band_ip`, `management_ip`, `address`, `snmp.address`;
- catalog/platform/manufacturer from Device V2 attributes/metadata;
- function area from attributes/metadata/labels;
- credential refs from in-band, WinRM and SNMP fields.

This is the most relevant current bridge for the device sub-gate and the topology refactor.

### Gaps / Questions

- Need query the prepared test DB for concrete `ONEOPS_GATE_*` fixture device records, tenant, IP, vendor and model.
- Need derive per-device maximum verifiable field sets from the D2 base field table plus actual collection evidence. Fields outside the per-device verifiable set must have reason classifications such as unsupported, no evidence, environment missing, or deferred.
- Need confirm whether DC2 collection will use real SNMP/SSH/WinRM against fixture devices or fixture/raw dataset injection for the first gate.

## Monitoring Findings

### Frontend Surface

- Monitoring task and metric asset pages are registered:
  - `OneOPS-UI/src/router/utils.ts:316`
  - `OneOPS-UI/src/router/utils.ts:328`
- Monitoring metric asset API uses `/api/v2/platform/monitoring` and supports metric assets, instances, observation, sync-observed, agent sync, task subjects, and backfill:
  - `OneOPS-UI/src/api/platform/monitoring-metric-asset.ts:20`
  - `OneOPS-UI/src/api/platform/monitoring-metric-asset.ts:33`
  - `OneOPS-UI/src/api/platform/monitoring-metric-asset.ts:49`
  - `OneOPS-UI/src/api/platform/monitoring-metric-asset.ts:58`
  - `OneOPS-UI/src/api/platform/monitoring-metric-asset.ts:88`

### Backend Surface

- Monitoring V2 router exposes target resolution, plan compile/apply, tasks, metric assets/instances, task subjects, graphs, credentials, and topology actions under `/api/v2/platform/monitoring`.
  - `OneOPS/app/platform/router/platform_v2.go:14`
  - `OneOPS/app/platform/router/platform_v2.go:37`
  - `OneOPS/app/platform/router/platform_v2.go:40`
  - `OneOPS/app/platform/router/platform_v2.go:53`
- Legacy monitor config routes also exist:
  - `OneOPS/app/monitor/router/monitor_config.go:8`

### Existing Gate Candidates

- `OneOPS/scripts/monitoring_v2_phase0_acceptance.sh`
- `OneOPS/scripts/monitoring_v2_jt01_e2e_bundle.sh`
- `OneOPS/scripts/monitoring_v2_release_gate_check.sh`
- `OneOPS/scripts/test_probe_monitoring_sync_e2e.sh`
- Frontend checks inside JT-01 bundle include eslint and vue-tsc over monitoring files.

### Evidence Candidate

Combination evidence should include:

- Script summary: `docs/evidence/monitoring-v2-*`.
- API: metric asset/instance list and sync-observed responses.
- Prometheus: direct query result for expected metric name + labels.
- Browser: monitoring task/metric asset page screenshot.
- Backend: focused Go tests around platform monitoring.

### Prometheus Evidence Path

Existing Prometheus query options:

- Common datasource service can execute instant and range PromQL queries.
- Dashboard service can query by labels and constructs selectors such as `metric_name{label="value"}`.

For the monitoring sub-gate, success should require:

- a task/projection exists for the fixture device;
- delivery/governance state is visible through monitoring task APIs;
- Prometheus query returns at least one sample in the gate window;
- required labels exist and match the fixture device according to the current "监控策略 / 通用标签附着" `attach_tags` configuration.

Current discovered label baselines:

- UI/API source: Teleabs strategy APIs under `/platform/metrics/teleabs`, where strategy parameters are stored as `parameters` or strategy-set item `default_params`.
- UI evidence source: "监控策略与 Teleabs 模板" -> "策略列表（绑定模板）" -> "通用标签附着" -> "配置参数" -> `attach_tags`.
- Code fallback source: `OneOPS/base_config_with_loki.txt` contains default `processors.attach.attach_tags`.
- Known code defaults: `ping` requires `tenant`, `ip_transform`, `device_name`, `hostname`; `snmp` requires `tenant`, `band_ip`, `hostname`, `device_name`; `snmp_interface` requires `tenant`, `band_ip`, `hostname`, `site`, `device_name`; `tail` requires `tenant`, `hostname`, `device_name`.
- User screenshot extends current strategy values for NVR and network metrics, including `oneops_nvr_camera_status`, `oneops_nvr_status`, `ping`, `snmp`, and `snmp_interface`. The gate should read the live strategy definition as the source of truth before asserting Prometheus labels.

### Gaps / Questions

- Need inspect existing `monitoring_v2_release_gate_check.sh` before deciding whether to reuse or wrap it.
- P0 metric set is confirmed as network-device `ping`, `snmp`, and `snmp_interface`.
- NVR metrics are deferred because no NVR test devices exist.
- Server SNMP is deferred until server-side configuration is prepared.
- Monitoring governance P0 is confirmed as delivery, status, retry/sync, Prometheus queryability and labels.
- drift/diff/repair is deferred until drift data is prepared.

## Logging Findings

### Frontend Surface

- Log forward, Grok profile, and Tail source routes are registered:
  - `OneOPS-UI/src/router/utils.ts:209`
  - `OneOPS-UI/src/router/utils.ts:232`
  - `OneOPS-UI/src/router/utils.ts:244`
- Log forward API supports plan CRUD, source binding, dry-run, preflight, apply, pause/resume/remove, Grok draft test, and Tail source profiles:
  - `OneOPS-UI/src/api/platform/log-forward.ts:26`
  - `OneOPS-UI/src/api/platform/log-forward.ts:28`
  - `OneOPS-UI/src/api/platform/log-forward.ts:72`
  - `OneOPS-UI/src/api/platform/log-forward.ts:80`
  - `OneOPS-UI/src/api/platform/log-forward.ts:87`
  - `OneOPS-UI/src/api/platform/log-forward.ts:94`
  - `OneOPS-UI/src/api/platform/log-forward.ts:176`

### Backend Surface

- Log forward routes are mounted under platform metrics/log-forward in platform router.
  - `OneOPS/app/platform/router/platform.go:381`
  - `OneOPS/app/platform/router/platform_bidi.go:359`

### Existing Gate Candidates

- `OneOPS/scripts/log_forward_tail_syslog_gate.sh`
- `OneOPS/scripts/log_forward_m1_e2e.sh`
- `OneOPS/scripts/test_log_api.sh`

### Evidence Candidate

Combination evidence should include:

- Unit/test summary from tail/syslog gate.
- API dry-run/preflight/apply response for a test plan.
- Device-side log trigger evidence.
- Loki query result containing the expected event and labels.
- Browser screenshot of log-forward plan and Tail source pages.
- Optional probe assertion when environment variables are supplied.

### Apply + Loki Evidence Path

`log_forward_m1_e2e.sh` already creates Grok profile, Tail source, local_file plan, binds source, runs dry-run, preflight and apply. It can also query generated monitoring tasks and optionally test remote_syslog apply.

Additional work needed for the confirmed success definition:

- Syslog path: build an SSH/netlink-based utility that enters config mode on a configured network device, runs a save command to emit deterministic syslog, then queries Loki for that event. Cisco uses `wr`; H3C and Huawei use `save`.
- Server tail path: create a deterministic log line on the target server watched by tail source paths `/var/log/messages` and `/var/log/syslog`, then query Loki for that event.
- Query Loki for that log line and validate expected labels.
- Attach both plan/apply evidence and Loki evidence to the same gate record.

### Gaps / Questions

- Need identify stable `ONEOPS_GATE_*` syslog network device and `ONEOPS_GATE_*` tail server fixture.
- Need define the expected syslog line format produced by Cisco `wr` and H3C/Huawei `save`.
- Need define the deterministic server log line format for `/var/log/messages` and `/var/log/syslog`.
- Need define required Loki labels. Existing dashboard Loki helper can query by `band_ip`, but log-forward gate likely needs the final label contract from the applied plan.

## Topology Findings

### Frontend Surface

- Topology API covers topology generation, coordinates, rack/interface/basic/runtime drill-down, snapshots, snapshot cable/interface preview/apply, overlay nodes/edges, and manual edges:
  - `OneOPS-UI/src/api/topology/topology.ts:19`
  - `OneOPS-UI/src/api/topology/topology.ts:41`
  - `OneOPS-UI/src/api/topology/topology.ts:80`
  - `OneOPS-UI/src/api/topology/topology.ts:95`
  - `OneOPS-UI/src/api/topology/topology.ts:105`
  - `OneOPS-UI/src/api/topology/topology.ts:137`
  - `OneOPS-UI/src/api/topology/topology.ts:239`
- L2 topology snapshots and workflows are exposed from data collection APIs:
  - `OneOPS-UI/src/api/data_collection/data_collection.ts:160`
  - `OneOPS-UI/src/api/data_collection/data_collection.ts:334`
  - `OneOPS-UI/src/api/data_collection/data_collection.ts:360`

### Backend Surface

- Traditional topology routes are mounted under `/topology`:
  - `OneOPS/app/topology/router/topology.go:8`
- Obsflow data collection routes expose collection runs, batches, processing runs, L2 topology snapshot workflows, publish/list/get snapshot:
  - `OneOPS/app/obsflow/router/data_collect_compat.go:32`

### Existing Gate Candidates

- Topology Go tests under `OneOPS/app/topology/service/...`.
- Obsflow tests under `OneOPS/app/obsflow/...`.
- `OneOPS/scripts/monitoring_v2_backfill_topology_snapshot.sh` has dry-run default for monitoring topology snapshot backfill.
- `OneOPS/scripts/import_topology_manual_edge_json.go`
- `OneOPS/scripts/import_topology_overlay_json.go`

### Evidence Candidate

Combination evidence should include:

- API: `/topology/:tenantCode` node/edge counts, drill-down responses.
- API: L2 topology snapshot workflow state and snapshot summary.
- Backend: topology + obsflow focused Go tests.
- Browser: topology page screenshot with node/edge counts when test data is present.

### Primary Topology Evidence Path

Confirmed direction: obsflow L2 topology snapshot is the primary evidence source; traditional `/topology` remains UI/display/drill-down validation.

Existing obsflow/DC2 topology building blocks:

- L2 snapshot workflow APIs exist for create/list/get/reconcile.
- obsflow tasks can output topology mount boundaries for neighbor links, device ports and ARP/MAC associations.
- DeviceCollection2 topology_neighbor facts normalize LLDP/CDP neighbor observations.
- DeviceCollection2 resolves targets from Device V2, so topology can be grounded in Device V2 onboarding data.
- Traditional topology already has a snapshot bridge path: `TopologySnapshotSrv` can resolve latest ready data_collection L2 snapshots and convert snapshot `edges` into topology nodes/edges. That means the first PRD story can validate and harden the bridge before asking for larger UI refactors.

Minimum success threshold:

- at least 2 `ONEOPS_GATE_*` network device fixtures;
- at least 1 L2 edge from obsflow/DC2 evidence;
- interface identity is present on both ends of the edge;
- `/topology` UI/API can display the graph;
- interface drill-down is required before final WS-01 Done. First story may mark it as `BLOCKED` when fixture interfaces are not ready.

### Gaps / Questions

- Need identify a stable tenant/test topology fixture and fixture tenant code.
- Need inspect UI drill-down path against snapshot-derived topology, because backend bridge evidence exists but frontend readiness still needs browser validation.

## Proposed Four Sub-Gates For Confirmation

### Gate D: Device Field Collection / Parse / Store

- Long-lived `ONEOPS_GATE_*` fixture devices exist in Device V2.
- DC2 run executes against the fixture device set.
- Latest facts contain expected identity/interface/topology fields.
- Device V2 read APIs show stored fields match expected values for each device's maximum verifiable field set.
- Browser evidence shows Device V2 pages can display the fixture.

### Gate M: Monitoring Task / Governance / Prometheus / Labels

- Monitoring task is generated and delivered for fixture device(s).
- Monitoring task governance state is visible and correct.
- Prometheus query returns expected metric samples.
- Required metric labels match the live "通用标签附着" `attach_tags` strategy configuration and fixture metadata.
- Browser evidence shows monitoring task/metric asset pages.

### Gate T: Device V2 + Collection -> obsflow L2 Snapshot -> Topology UI

- Device V2 data resolves into DC2 collection targets.
- Collection produces interface/neighbor facts.
- obsflow L2 snapshot workflow completes and produces snapshot summary.
- Traditional `/topology` or its refactored successor renders node/edge graph from the snapshot.
- Frontend can display at least 2 fixture devices, 1 edge, and can drill down to device/interface details.

### Gate L: Log Forward Apply -> Device Trigger -> Loki

- Log-forward plan is created/bound/preflighted/applied.
- Syslog fixture network device emits deterministic log line after apply.
- Tail fixture server emits deterministic log line after apply.
- Loki query returns the expected syslog and tail log lines within the gate window.
- Loki labels match expected device/source labels.
- Browser evidence shows log-forward plan and log dashboard/search result.

## Confirmation Needed

1. Query fixture inventory from the prepared test database and list actual `ONEOPS_GATE_*` device/server/tenant/IP/vendor/model rows.
2. Define expected syslog line patterns for Cisco `wr` and H3C/Huawei `save`.
3. Define expected tail test line patterns and whether the gate may write to `/var/log/messages` and `/var/log/syslog` directly or through a privileged helper.
4. Confirm whether browser evidence may use existing dev frontend/backend services or should be run against locally started services.
