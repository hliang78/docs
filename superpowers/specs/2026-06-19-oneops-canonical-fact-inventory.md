# OneOPS Canonical Fact Inventory

## Purpose

This inventory records the current code-backed state of canonical facts, obsflow snapshots, IPAM fact projection readiness, and NetPath snapshot gaps.

It supports:

- `docs/superpowers/specs/2026-06-19-oneops-canonical-fact-contract-design.md`
- `docs/superpowers/plans/2026-06-19-oneops-canonical-fact-contract-phase1.md`

## Inventory Status

Status: in progress.

Collection method:

- gpt-5.4 explorer: Device Collection 2 facts
- gpt-5.4 explorer: Obsflow snapshot contracts
- gpt-5.4 explorer: IPAM facts and audit
- gpt-5.4 explorer: NetPath snapshot provider and route gaps

## Summary

Current working conclusion:

- DC2 fact model is the right shared envelope.
- Obsflow is the strongest existing batch and snapshot mainline.
- IPAM has enough application workflow to become the first fact projection consumer.
- NetPath is blocked primarily by route table fact availability and durable platform integration.

## Device Collection 2 Fact Inventory

Status: explorer-backed inventory recorded.

Known current files:

- `OneOPS/app/device_collection2/model/fact.go`
- `OneOPS/app/device_collection2/fact/types.go`
- `OneOPS/app/device_collection2/fact/registry.go`
- `OneOPS/app/device_collection2/fact/device_identity_processor.go`
- `OneOPS/app/device_collection2/fact/interface_processor.go`
- `OneOPS/app/device_collection2/fact/interface_ip_processor.go`
- `OneOPS/app/device_collection2/fact/physical_entity_processor.go`
- `OneOPS/app/device_collection2/fact/server_processor.go`
- `OneOPS/app/device_collection2/fact/topology_processor.go`
- `OneOPS/app/device_collection2/api/device_collection2.go`
- `OneOPS/app/device_collection2/router/device_collection2.go`
- `OneOPS/app/device_collection2/service/impl/device_collection2.go`
- `OneOPS/app/netpath/snapshot/provider/facts.go`
- `OneOPS/app/netpath/snapshot/provider/assembler.go`

### Current Fact Model

In-memory shape:

```text
StandardRow -> CanonicalFact
```

`CanonicalFact` currently carries:

```text
fact_type
target_id
identity_key
fields
quality
provenance
observed_at
```

`FactQuality` carries:

```text
valid
confidence
issues
```

`FactProvenance` carries:

```text
contract_key
dataset_key
source_fields
processor_key
processor_version
```

Persistence tables:

```text
device_collection2_fact
device_collection2_fact_latest
device_collection2_fact_issue
```

Stored fact rows include ids/run/target/fact_type/identity_key, `valid`, `confidence`, `observed_at`, timestamps, and JSON blobs for fields, quality, and provenance.

Latest facts are upserted by:

```text
target_id + fact_type + identity_key
```

References:

- `OneOPS/app/device_collection2/fact/types.go`
- `OneOPS/app/device_collection2/model/fact.go`
- `OneOPS/app/device_collection2/service/impl/device_collection2.go`

### Current Processor Registry

Current registry wires 9 processors.

#### device_identity

Processor:

```text
processor.device_identity.v1
```

Fact type:

```text
device_identity
```

Accepted datasets include device identity, sysinfo, version, CLI version, SNMP system, Linux OS release, Ubuntu/CentOS release, and Windows OS-style datasets.

Identity rule:

```text
serial_number:<serial>
<target_id>:device_identity
management_ip:<ip>
hostname:<hostname>
```

Reference:

- `OneOPS/app/device_collection2/fact/device_identity_processor.go`

#### interface

Processor:

```text
processor.interface.v1
```

Fact type:

```text
interface
```

Accepted datasets include interface, if table, SNMP if table, high speed, LLDP local port entry, CLI interface brief, Linux interfaces, and Windows network adapter datasets.

Identity rule:

```text
<target_id>:if_index:<if_index>
<target_id>:if_name:<if_name_canonical>
```

Reference:

- `OneOPS/app/device_collection2/fact/interface_processor.go`

#### interface_ip

Processor:

```text
processor.interface_ip.v1
```

Fact type:

```text
interface_ip
```

Accepted datasets include interface IP, IP addressing, SNMP IP addressing, SNMP IP address entry, Linux interface IP, and Windows network IP address.

Identity rule:

```text
interface anchor + ip
```

Reference:

- `OneOPS/app/device_collection2/fact/interface_ip_processor.go`

#### physical_entity

Processor:

```text
processor.physical_entity.v1
```

Fact types:

```text
physical_entity
device_identity
```

The processor may synthesize `device_identity`.

Identity rule:

```text
<target_id>:ent_index:<ent_index>
<target_id>:physical:<fallback>
```

Reference:

- `OneOPS/app/device_collection2/fact/physical_entity_processor.go`

#### server_cpu

Processor:

```text
processor.server_cpu.v1
```

Fact type:

```text
server_cpu
```

Identity rule:

```text
processor_id
cpu_model + row_index
row_index
```

Reference:

- `OneOPS/app/device_collection2/fact/server_processor.go`

#### server_route

Processor:

```text
processor.server_route.v1
```

Fact type:

```text
server_route
```

Accepted datasets:

```text
linux_default_route
windows_default_route
```

Identity rule:

```text
<target_id>:route:<destination/gateway/if_index/if_name parts>
```

Important: this is not a generic network-device route table.

Reference:

- `OneOPS/app/device_collection2/fact/server_processor.go`

#### topology_neighbor

Processor:

```text
processor.topology_neighbor.v1
```

Fact type:

```text
topology_neighbor
```

Accepted datasets include explicit LLDP/CDP dataset keys and heuristic dataset-name matching for topology-like datasets.

Identity rule:

```text
local interface anchor + first remote hint
```

Remote hints include remote device, remote MAC, remote IP, remote chassis id, and remote interface fields.

Reference:

- `OneOPS/app/device_collection2/fact/topology_processor.go`

#### mac_table_entry

Processor:

```text
processor.mac_table.v1
```

Fact type:

```text
mac_table_entry
```

Accepted datasets include MAC table, FDB, bridge MAC, SNMP FDB table, CLI MAC table, MAC address table, and dot1d FDB.

Identity rule:

```text
target + mac + optional vlan
```

Important naming gap:

- the design contract previously called this `mac_table`
- current code emits `mac_table_entry`
- product-facing `mac_table` should be treated as an alias, not the stored canonical fact type

Latest compatibility note:

- pre-hardening latest rows may have identities that also include `bridge_port` or local interface
- hardening cleanup removes stale legacy-shape `mac_table_entry` rows from `device_collection2_fact_latest`
- history rows in `device_collection2_fact` are retained for evidence

Reference:

- `OneOPS/app/device_collection2/fact/topology_processor.go`

#### arp_entry

Processor:

```text
processor.arp.v1
```

Fact type:

```text
arp_entry
```

Accepted datasets:

```text
arp
arp_table
ip_net_to_media
snmp_arp_table
cli_arp
snmp_arp
```

Identity rule:

```text
target + ip + mac + optional local interface
```

Current weakness:

- schema is thin
- no VRF
- no age
- no state
- no source protocol detail
- no L3/L2 resolution metadata

Reference:

- `OneOPS/app/device_collection2/fact/topology_processor.go`

### Quality And Provenance

`ProcessFacts` wraps rows, calls exactly one matching processor, and optionally persists facts and issues.

Provenance is uniform and minimal via `baseProvenance()`:

```text
contract_key
dataset_key
source_fields
processor_key
processor_version
```

Quality is processor-local:

- `device_identity`, `physical_entity`, and `server_cpu` add more meaningful confidence or issue hints
- many other processors hardcode `Valid:true`, fixed confidence, and empty issue lists

Bad normalization commonly creates `FactIssue` rows and skips accepted facts rather than storing invalid facts.

Gaps:

- provenance does not carry vendor/platform even though `StandardRow` has them
- no raw source row or payload fingerprint
- no cross-row conflict scoring before latest upsert
- latest projection is overwrite-by-key
- only the first matching processor runs per dataset

### API And Service Entry Points

Routes:

```text
POST /process-facts
GET /facts
GET /facts/latest
GET /fact-issues
```

Relevant service methods:

```text
ProcessFacts
ListFacts
ListLatestFacts
ListFactIssues
```

References:

- `OneOPS/app/device_collection2/router/device_collection2.go`
- `OneOPS/app/device_collection2/api/device_collection2.go`
- `OneOPS/app/device_collection2/service/impl/device_collection2.go`

### Upper-Application Gaps

Strong enough today:

- identity/interface/IP/topology/MAC/ARP
- light server facts

Still not strong enough:

- generic `route_table` fact exists in the Phase 4 worktree, but is not integrated into production runs yet
- firewall/security fact family is absent
- `arp_entry` needs VRF/status/age/source enrichment for IPAM and RCA
- `mac_table_entry` naming must be reconciled with application contract terminology

NetPath already expects a distinct `route_table` fact type and consumes:

```text
destination
next_hop_ip
out_interface
protocol
metric
preference
null_route
raw
```

References:

- `OneOPS/app/netpath/snapshot/provider/facts.go`
- `OneOPS/app/netpath/snapshot/provider/assembler.go`
- `OneOPS/app/netpath/snapshot/builder.go`

## Obsflow Snapshot Inventory

Status: explorer-backed inventory recorded.

Known current files:

- `OneOPS/app/obsflow/domain/types.go`
- `OneOPS/app/obsflow/app/kernel_service.go`
- `OneOPS/app/obsflow/tasks/device_ports/task.go`
- `OneOPS/app/obsflow/tasks/neighbor_links/task.go`
- `OneOPS/app/obsflow/tasks/arp_mac/task.go`
- `OneOPS/app/obsflow/adapters/data_collection_processing_run_store.go`
- `OneOPS/app/obsflow/adapters/data_collection_collection_query_store.go`
- `OneOPS/app/obsflow/adapters/data_collection_snapshot_store.go`
- `OneOPS/app/obsflow/bridge/snapshot_apply_api.go`
- `OneOPS/app/obsflow/app/snapshot_query_service.go`
- `OneOPS/app/obsflow/domain/collection_observation_contract.go`
- `OneOPS/app/obsflow/task/association.go`
- `OneOPS/app/obsflow/api/task_alias.go`

### Current Mainline Contract

`CollectionRun` is the execution-side record. It carries collection name, device and result counts, linked batch id/code/state, and downstream `ProcessingReadiness`.

`ObservationBatch` is the processing handoff unit. It repeats run linkage, tenant, schema/targets, observation counts, and its own `ProcessingReadiness`.

`KernelService.Process` consumes batch codes, not collection runs. It rebuilds:

```text
PrimaryBatch + all batches + flattened observations
```

Then it:

1. validates the task contract,
2. starts `processing_run` as `running/not_ready`,
3. runs the registered task,
4. saves a snapshot,
5. marks the run `completed/<task readiness>`.

On task failure or snapshot-write failure, the run is marked `failed/not_ready`.

Primary-batch semantics are important: the first normalized batch becomes `BatchCode`; all normalized codes remain in `BatchCodes`.

References:

- `OneOPS/app/obsflow/domain/types.go`
- `OneOPS/app/obsflow/app/kernel_service.go`
- `OneOPS/app/obsflow/adapters/data_collection_processing_run_store.go`
- `OneOPS/app/obsflow/api/task_alias.go`

### Snapshot Fields Produced By Current L2 Tasks

Common payload envelope across current L2 tasks:

```text
snapshot_kind
snapshot_scope
topology_mount_boundary
device_codes
processed_devices
collections_used
observation_collections
association_status
association_summary
association_issues
```

`device_ports` adds:

```text
total_observations
total_observation_rows
base_row_count
ip_row_count
speed_row_count
ports[]
```

Each `ports[]` item includes:

```text
device_code
interface_index
interface_name
interface_mac
interface_state
phy_protocol
ip_addresses
ip_masks
speed_high_mbps
association_state
```

`neighbor_links` adds:

```text
total_observations
total_observation_rows
edge_count
observed_edge_count
edges[]
```

Each `edges[]` item includes collection name, source/target device name/code, source/target interface code/name, and source/target port.

`arp_mac` adds:

```text
input_mode
has_arp_batch
has_mac_batch
arp_record_count
mac_record_count
binding_count
interconnect exclusion counters
bindings[]
orphan_macs[]
```

References:

- `OneOPS/app/obsflow/tasks/device_ports/task.go`
- `OneOPS/app/obsflow/tasks/neighbor_links/task.go`
- `OneOPS/app/obsflow/tasks/arp_mac/task.go`

### Readiness And State Semantics

Batch-level readiness is stricter than state:

```text
ProcessingReadiness = ready only when State == "ready" and observationCount > 0
```

Processing runs start as:

```text
running / not_ready
```

The kernel marks them completed only after snapshot persistence succeeds.

Important gap:

- current L2 tasks can return `Readiness="ready"` and `SnapshotState="ready"` even when `association_status` is `partial` or `blocked`
- `association_status` is informational, not a publish/apply gate
- `neighbor_links` can treat existing observations with zero rows as a ready empty snapshot

References:

- `OneOPS/app/obsflow/domain/collection_observation_contract.go`
- `OneOPS/app/obsflow/adapters/data_collection_collection_query_store.go`
- `OneOPS/app/obsflow/app/kernel_service.go`
- `OneOPS/app/obsflow/task/association.go`

### Apply Behavior

`ApplyL2TopologySnapshot` requires `snapshot_code`, loads the snapshot, and rejects snapshots whose `Readiness != "ready"`.

Apply dispatch currently supports only:

- `device_ports`
- `arp_mac`
- `neighbor_links`

Legacy task aliases such as `L2nodeMapServer` are normalized before dispatch.

Safeguards:

- apply rejects non-ready snapshots
- each apply path rehydrates typed structures from `snapshot.Data`
- `neighbor_links` requires `device_codes` to exist and be string-like

Gap:

- apply checks readiness only, while snapshot publishing checks processing run completion and readiness
- partial apply result reporting exists for `device_ports`, but not equivalently for all apply paths

References:

- `OneOPS/app/obsflow/bridge/snapshot_apply_api.go`
- `OneOPS/app/obsflow/app/snapshot_query_service.go`

### Reuse Gaps For Non-L2 Applications

Current snapshot semantics are usable but not yet a reusable platform contract.

Gaps:

- no typed, versioned snapshot envelope
- task-specific payloads are stored as `map[string]interface{}`
- domain `Snapshot.Summary` string is effectively less portable than the stored JSON payload
- stored task names may prefer legacy aliases from `processing_run`
- `ready` can coexist with `association_status=blocked`
- apply dispatch is hardcoded, not registry-driven
- snapshot lookup tolerates historical state values `completed`, `ready`, and `success`

Conclusion:

```text
Obsflow has a workable batch-to-snapshot spine, but reusable snapshot semantics remain convention-driven.
```

## IPAM Fact And Audit Inventory

Status: explorer-backed inventory recorded.

Known current files:

- `OneOPS/app/ipam/ipam_model/ip_address.go`
- `OneOPS/app/ipam/ipam_model/ip_address_fact.go`
- `OneOPS/app/ipam/ipam_model/ip_address_audit_finding.go`
- `OneOPS/app/ipam/service/impl/ip_address_fact.go`
- `OneOPS/app/ipam/service/impl/ip_address_audit_finding.go`
- `OneOPS/app/ipam/service/impl/ipam_statistics.go`
- `OneOPS-UI/src/views/ipam/IPFactAuditFlow.vue`
- `OneOPS-UI/src/typings/ipam/ip_address_fact.ts`
- `OneOPS-UI/src/typings/ipam/ip_address_audit_finding.ts`

### Current Observed Fact Fields

`IPAddressFact` stores first-class columns for:

```text
ip_address
ip_version
device_code
device_name
interface_code
interface_name
mac_code
mac_address
platform_vrf_code
device_local_vrf_code
security_zone_id
source
first_seen_at
last_seen_at
confidence
raw_ref
```

The API contract also carries:

```text
prefix_code
pool_code
tenant_code
observed_status
raw_data
```

Those values are not columns. They are packed into `RawRef`.

References:

- `OneOPS/app/ipam/ipam_model/ip_address_fact.go`
- `OneOPS/app/ipam/dto/ip_address_fact.go`
- `OneOPS/app/ipam/service/impl/ip_address_fact.go`

### Upsert Identity

Current fact upsert matches on:

```text
ip_address
source_type
device_code
device_interface_code
vrf_code
```

These do not participate in uniqueness:

```text
code
prefix_code
pool_code
tenant_code
observed_status
mac_code
mac_address
security_zone_id
raw_data
```

On update:

- `RawRef` is replaced wholesale
- names, seen times, and confidence are refreshed
- MAC and security zone update only when non-empty

Important risk:

- omitted prefix/pool/tenant/status/raw fields are cleared from `RawRef` rather than merged

Reference:

- `OneOPS/app/ipam/service/impl/ip_address_fact.go`

### Audit Finding Generation Rules

From one fact, backend can generate:

```text
unplanned
ambiguous_planned_match
stale_planned
owner_mismatch
mac_mismatch
duplicate_observation
```

Rules:

- `unplanned`: no planned `IPAddress` matches address plus optional VRF and prefix context
- `ambiguous_planned_match`: more than one planned match exists
- `stale_planned`: observed status is inactive/down/off/unreachable while planned state still has active intent
- `owner_mismatch`: planned owner/interface code differs from observed device/interface code
- `mac_mismatch`: planned and observed MAC codes are both non-empty and differ
- `duplicate_observation`: active/reachable/up/on observed fact has more than one active fact for the same IP and VRF

Open, acknowledged, and ignored findings are deduped by:

```text
finding_type
ip
prefix
observed_device
observed_interface
observed_mac
```

Resolved findings allow a new record later.

Reference:

- `OneOPS/app/ipam/service/impl/ip_address_audit_finding.go`

### Source Metadata Preservation

Preserved as columns:

```text
source type
device/interface codes and names
MAC code/address
platform VRF
security zone
seen times
confidence
```

Preserved only inside opaque `RawRef`:

```text
prefix_code
pool_code
tenant_code
observed_status
raw_data
```

Lost or weakened:

- no structured provenance beyond short `raw_data`
- no collector, job, run, batch, or canonical fact id fields
- later upserts overwrite prior `RawRef`
- `device_local_vrf_code` exists in the model but current upsert path does not set it
- tenant/prefix/pool/status filtering requires post-read `RawRef` parsing
- manual UI does not expose prefix, tenant, device code, interface code, MAC code, or raw data

### UI And Backend Status Mismatch

Current UI status options include:

```text
online
offline
unknown
```

Backend audit status checks recognize:

```text
active
up
reachable
on
inactive
down
off
unreachable
```

Impact:

- manual UI facts may not trigger `duplicate_observation`
- manual UI facts may not trigger `stale_planned`
- manual UI facts cannot meaningfully trigger owner or MAC mismatch when codes are blank

References:

- `OneOPS-UI/src/views/ipam/IPFactAuditFlow.vue`
- `OneOPS/app/ipam/service/impl/ip_address_audit_finding.go`

### Projection Boundary

IPAM should keep owning workflow and planning state:

- `IPAddress.status`
- `IPAddress.lifecycle_status`
- `IPAddress.pool_code`
- `IPAddress.request_code`
- `IPAddress.owner_*`
- `IPAddress.security_zone_id`
- `IPAddressRequest.status`
- `AddressPool`
- `ReservedRange`

Canonical facts should describe what was observed.

Recommended projection:

```text
canonical facts -> IPAM observed fact/reconciliation model -> IPAM audit findings
```

Projection must not overwrite lifecycle, request approval, pool membership, or reserved range policy unless a user-visible IPAM workflow acts on a finding.

References:

- `OneOPS/app/ipam/ipam_model/ip_address.go`
- `OneOPS/app/ipam/ipam_model/ip_address_request.go`
- `OneOPS/app/ipam/ipam_model/address_pool.go`
- `OneOPS/app/ipam/ipam_model/reserved_range.go`
- `OneOPS/app/ipam/service/impl/ipam_statistics.go`

## NetPath Snapshot Gap Inventory

Status: explorer-backed inventory recorded.

Known current files:

- `OneOPS/app/netpath/api/netpath.go`
- `OneOPS/app/netpath/service/impl/netpath.go`
- `OneOPS/app/netpath/engine/engine.go`
- `OneOPS/app/netpath/netpath_model/run.go`
- `OneOPS/app/netpath/service/impl/netpath.go`
- `OneOPS/app/netpath/snapshot/builder.go`
- `OneOPS/app/netpath/snapshot/provider/types.go`
- `OneOPS/app/netpath/snapshot/provider/facts.go`
- `OneOPS/app/netpath/snapshot/provider/assembler.go`
- `OneOPS/app/netpath/snapshot/provider/validator.go`
- `OneOPS/app/netpath/adapter/oneopsnetpath/adapter_sdk.go`
- `oneops-netpath/pkg/netpath/netpath.go`
- `oneops-netpath/internal/model/types.go`
- `oneops-netpath/internal/model/validation.go`
- `oneops-netpath/internal/engine/engine.go`
- `docs/superpowers/plans/2026-06-19-oneops-netpath-master-roadmap.md`
- `docs/superpowers/plans/2026-06-19-oneops-netpath-route-table-phase3.md`

### Current OneOPS NetPath Status

Service/API skeleton exists:

- `NetPathAPI` exposes preview, create run, and get run handlers
- `NetPathService` validates DTOs and maps requests into the engine port

Preview behavior:

- if no builder is injected, preview is metadata-only
- if a builder is injected, preview returns counts and warnings

Analyze behavior:

- if no engine is injected, runs are stored with `engine_pending`
- fallback result contains synthetic trace data

Persistence status:

- runs are stored in an in-memory `map[string]*dto.AnalyzeRunResp`
- `netpath_model.NetPathAnalysisRun` exists but is not used by the service yet

Engine adapter status:

- OneOPS engine port exists and is intentionally minimal
- SDK adapter exists behind build tag `oneops_netpath_sdk`
- adapter requires a `SnapshotProvider.GetSnapshot(...)` returning `pkg/netpath.Snapshot`
- no concrete production SnapshotProvider retrieval path is wired yet

Provider status:

- internal `AnalysisSnapshot` types exist
- fact helpers exist
- in-memory assembler exists
- validator exists
- no concrete reader/provider pulls real DC2 latest facts into `FactSet`
- no mapper from `AnalysisSnapshot` to `pkg/netpath.Snapshot`
- assembler/validator are not wired into `NetPathService` or adapter path

### oneops-netpath Engine Snapshot Contract

Minimal validation requires:

```text
snapshot.snapshot_id
snapshot.devices[]
flow.ingress_device_code
flow.src_ip
flow.dst_ip
```

Actual traversal consumes:

```text
devices[].device_code
devices[].route_tables[].vrf
devices[].route_tables[].routes[]
routes[].destination
routes[].next_hop_ip
routes[].out_interface
routes[].preference
routes[].metric
routes[].null_route
routes[].raw
interfaces[].vrf
interfaces[].interface_name
interfaces[].interface_code
interfaces[].ipv4_addresses
interfaces[].peer_*
links[]
```

Model gap:

- SDK model has tenant/source/device metadata fields that route/topology engine does not meaningfully use today
- OneOPS provider model has `FactRunIDs` and per-route `RouteSourceRef`
- SDK `Snapshot` and `Route` do not yet preserve those provenance fields cleanly

### Current Builder And Provider Capabilities

Preview builder consumes DC2 latest facts:

```text
interface
interface_ip
topology_neighbor
```

It builds:

```text
devices
interfaces
links
diagnostics
```

It can infer interfaces for orphan IP facts.

Hard gap:

```text
route_table_missing
```

The preview builder explicitly does not build route tables.

Provider assembler can assemble internal `AnalysisSnapshot` from in-memory facts:

```text
device_identity
interface
interface_ip
topology_neighbor
route_table
server_route
```

The validator classifies snapshot quality and can block snapshots when the ingress device or VRF has no route table.

### Tenant Scope Gap

Tenant scoping is not enforced in current DC2 latest-fact reads.

Observed issues:

- preview builder passes empty `targetID` into `ListLatestFacts`
- `tenant_code` is not part of the current DC2 latest fact query surface
- `tenant_code` is not part of the latest table key

Tracked blocker test:

```text
OneOPS/app/device_collection2/service/impl/device_collection2_test.go
TestListLatestFactsTenantScopeNotImplemented
```

Current mitigation in the NetPath worktree:

```text
OneOPS/app/netpath/snapshot/provider/latest_fact_provider.go
```

The provider-side seam requires `tenant_code` and explicit `device_codes`, then reads DC2 latest facts per target/fact type. It does not use `target_id=""`.

Caller contract:

```text
Callers must resolve tenant-authorized device_codes before invoking the NetPath latest-fact provider.
The provider validates that tenant_code and device_codes are present, but it does not infer authorization from DC2 latest facts.
```

Residual gap:

```text
The caller must still resolve tenant-authorized device_codes before invoking the seam.
DC2 latest facts themselves are still not tenant-keyed.
```

### route_table Canonical Fact Status

Required fields:

```text
vrf
destination
next_hop_ip
out_interface
protocol
metric
preference
null_route
raw
```

Required identity key from existing NetPath route-table phase plan:

```text
<target_id>:route:vrf:<vrf>:dest:<destination>:nh:<next_hop_or_direct_or_null>:out:<out_interface_or_none>
```

Accepted normalization issue codes:

```text
missing_required_field
invalid_prefix
invalid_ip
invalid_metric
invalid_preference
```

Implemented in the Phase 4 worktree:

- `processor.route_table.v1` accepts `route_table`, `routing_table`, `ip_route`, `ip_routing_table`, `cli_route_table`, `cli_ip_route`, and `display_ip_routing_table`.
- H3C Comware/SecPath built-in CLI contracts include `cli_route_table` using `display ip routing-table`.
- Processor tests cover static, direct/connected with a populated source next hop, null routes, invalid prefix/IP, invalid metric/preference, and persistence/latest/history behavior.
- NetPath provider tests assemble DC2-shaped `route_table` facts for static, direct, and null routes while preserving `RouteSourceRef`.

Why this still blocks production NetPath:

- preview builder remains preview-only and still reports `route_table_missing`
- provider validator blocks missing ingress route tables
- engine returns `no_route` when current device/VRF has no route table
- production NetPath now has a first provider-side tenant-safe latest-fact seam, but still needs tenant-authorized device scope resolution before invoking it

Conclusion:

```text
NetPath's main data blocker is no longer the absence of a route_table canonical fact or the absence of a scoped reader seam; the remaining blockers are tenant-authorized device scope resolution and wiring the SnapshotProvider path into durable NetPath runs.
```

## Consolidated Gaps

### Contract Gaps

- Fact registry is not yet a first-class document or test target.
- Tenant-safe production consumers must use scoped reader seams; DC2 latest facts remain not tenant-keyed.
- Route table facts must be integrated from the Phase 4 worktree before NetPath can fully converge.
- ARP facts exist, but need VRF/status/age/source enrichment before IPAM and RCA can fully rely on them.
- `mac_table_entry` naming must be reconciled with product-facing `mac_table` language.

### Application Gaps

- IPAM facts need a projection path from canonical facts.
- L2 snapshot fields need stable consumer-facing documentation.
- NetPath needs Phase 4 route facts integrated, tenant-authorized device scope resolution, provider quality gates wired into persistent runs, and router/frontend integration.
- NetPath provider has a tenant-safe latest-fact seam, but production analysis still needs to call it from the durable run path.

## Next Update

Next actions:

- create the focused hardening implementation plan
- create IPAM fact projection phase plan
- integrate the route table canonical fact worktree
- wire NetPath durable runs through the tenant-safe latest-fact provider seam
- design equivalent tenant-safe fact consumption for IPAM/L2 snapshot production paths
- update the master board as implementation phases land
