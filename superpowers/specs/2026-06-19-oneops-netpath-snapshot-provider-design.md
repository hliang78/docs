# OneOPS NetPath SnapshotProvider Design

Date: 2026-06-19

## Purpose

This design defines how OneOPS should build an engine-ready `netpath.Snapshot` from collected OneOPS data and provide it to the optional `oneops-netpath` SDK adapter.

The key distinction is:

- `app/netpath/snapshot.Builder` today is a DC2 preview builder.
- `SnapshotProvider` for analysis must return a complete engine-ready snapshot with route tables.

The preview builder can remain useful for operator visibility, but it must not be treated as a valid analysis snapshot until route tables and validation gates are added.

## Current Facts From Code Review

### Existing OneOPS Sources

DC2 latest facts are the best primary source for normalized collection facts:

- `app/device_collection2/service/i_device_collection2.go`
  - `ListLatestFacts(ctx, targetID, factType, validOnly, limit)`
- `app/device_collection2/model/fact.go`
  - `FactLatestRecord`
  - key fields: `target_id`, `fact_type`, `identity_key`, `fields`, `valid`, `confidence`, `observed_at`, `provenance`
- `app/device_collection2/fact/interface_processor.go`
  - fact type `interface`
  - key fields: `if_index`, `if_name`, `if_name_canonical`, `admin_status`, `oper_status`, `mac`, `speed_bps`, `mtu`, `if_type`
- `app/device_collection2/fact/interface_ip_processor.go`
  - fact type `interface_ip`
  - key fields: `ip`, `prefix_len`, `cidr`, `netmask`, `vrf`, `addr_type`
- `app/device_collection2/fact/topology_processor.go`
  - fact type `topology_neighbor`
  - key fields: local interface identity, `remote_device`, `remote_if_name`, `remote_if_name_canonical`, `remote_ip`, `remote_mac`, `remote_chassis_id`, `protocol`
- `app/device_collection2/fact/device_identity_processor.go`
  - fact type `device_identity`
  - key fields: `hostname`, `vendor`, `platform`, `model`, `serial_number`, `management_ip`, `os_version`

Supplementary sources:

- Device master data:
  - `app/device/device_model/device.go`
  - `app/device/device_model/device_interface.go`
  - `app/device/device_model/device_cable.go`
- Topology snapshot data:
  - `app/topology/service/impl/snapshot.go`
- Firewall config facts:
  - `app/firewall/service/impl/config_fact_snapshot.go`
  - `FirewallConfigSnapshot.facts.interfaces`
  - `FirewallConfigSnapshot.facts.routes`
  - `FirewallConfigSnapshot.facts.zones`
- Firewall policy overview:
  - `app/firewall/dto/firewall_node.go`
  - `FirewallNodeManagementLatestPolicyOverviewResp`
  - `FirewallNodeManagementLatestPolicyItem`

### Current Preview Builder

`app/netpath/snapshot.Builder` currently:

- reads DC2 latest `interface`, `interface_ip`, and `topology_neighbor` facts;
- joins interface IPs to interfaces;
- creates inferred interfaces for orphan IP facts;
- builds links from resolved topology neighbor facts;
- deduplicates bidirectional links;
- emits stable sorted devices, links, and diagnostics;
- always emits `route_table_missing` when devices exist.

It does not:

- read route tables;
- build route tables;
- expose policy, ACL, PBR, NAT, zones, or firewall evidence;
- persist full snapshot versions;
- use `tenant_code` as a real DC2 query boundary;
- feed the analysis engine.

### oneops-netpath Engine Requirements

The public SDK uses `netpath.Snapshot`, a type alias for the internal model.

Hard validation:

- `snapshot.snapshot_id` is required.
- `snapshot.devices` must be non-empty.
- `flow.ingress_device_code` is required.
- `flow.src_ip` and `flow.dst_ip` must be valid IP addresses.
- every `route.destination` must parse as an IP prefix.

Current traversal actually depends on:

- `Flow.DstIP`
- `Flow.IngressDeviceCode`
- `Flow.IngressVRF`
- `Flow.IngressInterface` for display on first hop only
- `Device.DeviceCode`
- `Device.Interfaces`
- `Interface.InterfaceName`
- `Interface.InterfaceCode`
- `Interface.VRF`
- `Interface.IPv4Addresses`
- `Interface.PeerDeviceCode`
- `Interface.PeerInterfaceName`
- `Interface.PeerInterfaceCode`
- `RouteTable.VRF`
- `Route.Destination`
- `Route.NextHopIP`
- `Route.OutInterfaceName`
- `Route.Preference`
- `Route.Metric`
- `Route.NullRoute`
- `Route.Raw`
- `Link.ADeviceCode`
- `Link.AInterfaceName`
- `Link.BDeviceCode`
- `Link.BInterfaceName`

Current traversal can produce:

- `delivered_to_subnet`
- `no_route`
- `null_routed`
- `loop`
- `neighbor_unreachable`
- `insufficient_info`

It does not yet truly evaluate firewall policy, ACL, NAT, or PBR. Those phases must appear as diagnostics or evidence stubs until the engine supports them.

## Recommended Architecture

```text
DC2 latest facts
  + Device/Interface/Cable services
  + Topology snapshot service
  + Firewall config fact reader
        |
        v
NetPath Snapshot Fact Reader Ports
        |
        v
Analysis Snapshot Assembler
        |
        v
Snapshot Validator / Quality Gate
        |
        v
Snapshot Store / SnapshotProvider
        |
        v
oneopsnetpath SDK Adapter
        |
        v
oneops-netpath Analyze
```

The design has four layers:

1. **Fact reader ports**
   - read normalized facts through service interfaces;
   - do not read database tables directly.
2. **Analysis snapshot assembler**
   - converts facts into a full `netpath.Snapshot`;
   - handles joins, canonical names, route tables, links, and diagnostics.
3. **Snapshot store / provider**
   - stores or caches generated snapshots by `snapshot_id`;
   - implements the adapter-facing `SnapshotProvider`.
4. **SDK adapter**
   - already exists as build-tagged source;
   - calls provider and maps SDK results back into OneOPS engine result.

## Alternatives Considered

### Alternative A: Extend The Current Preview Builder Into The Engine Provider

This is the smallest code movement, because `app/netpath/snapshot.Builder` already reads DC2 interface, interface IP, and topology facts.

It is not recommended as the primary design because the preview builder is intentionally incomplete. It always emits `route_table_missing`, has a fixed latest fact limit, does not enforce tenant scope, and returns a preview model rather than an engine-ready model. Turning it directly into the provider would blur operator preview and analysis execution, increasing the chance that a metadata preview is accidentally treated as a valid analysis snapshot.

The preview builder can still share helper logic with the future assembler after a deliberate refactor.

### Alternative B: Let The SDK Adapter Read DC2 And Build Snapshots Inline

This keeps the integration surface small at first, because the adapter could call DC2, build a `netpath.Snapshot`, and immediately call `netpath.Analyze`.

It is not recommended because the adapter is already build-tagged and should remain a thin engine bridge. Putting DC2 reading and snapshot assembly inside it would make default builds harder to reason about, mix platform data access with SDK mapping, and make snapshot quality hard to inspect or persist independently.

### Alternative C: Add A Separate Analysis Snapshot Provider Layer

This is the recommended approach.

It keeps concerns separated:

- preview builder remains a preview and diagnostics tool;
- analysis assembler owns engine-ready snapshot construction;
- provider owns snapshot selection, quality gating, and retrieval;
- SDK adapter owns only SDK invocation and result mapping.

This also matches the user journeys: collection and snapshot quality must be visible before analysis, and analysis results must be traceable back to immutable source data.

## Recommended Package Boundary

Create a new analysis-focused package rather than overloading preview builder:

```text
app/netpath/snapshot/provider
```

Recommended files:

```text
app/netpath/snapshot/provider/types.go
app/netpath/snapshot/provider/reader.go
app/netpath/snapshot/provider/assembler.go
app/netpath/snapshot/provider/validator.go
app/netpath/snapshot/provider/provider.go
```

The existing `app/netpath/snapshot` package can remain preview-focused until it is intentionally refactored.

## Provider Contract

The build-tagged SDK adapter currently expects:

```go
type SnapshotProvider interface {
	GetSnapshot(ctx context.Context, req engine.AnalyzeRequest) (netpath.Snapshot, error)
}
```

The OneOPS provider should implement this contract in the tagged adapter integration slice.

Internally, the provider should not depend on `oneops-netpath` unless compiled with `oneops_netpath_sdk`. The non-tagged analysis snapshot package should use OneOPS-owned snapshot structs that mirror the SDK shape, then the tagged provider mapper can convert to `netpath.Snapshot`.

## Analysis Snapshot Model

OneOPS should introduce an internal analysis snapshot model that is richer than preview:

```go
type AnalysisSnapshot struct {
	SnapshotID     string
	TenantCode     string
	GeneratedAt    time.Time
	SourceVersions SourceRefs
	Devices        []AnalysisDevice
	Links          []AnalysisLink
	Diagnostics    []AnalysisDiagnostic
}

type SourceRefs struct {
	ConfigVersionIDs []string
	TopologySnapshotID string
	CollectionRunIDs   []string
	FactRunIDs       []string
}

type AnalysisDevice struct {
	DeviceCode       string
	DeviceName       string
	DeviceType       string
	Vendor           string
	Model            string
	ManagementIP     string
	VRFs             []AnalysisVRF
	Interfaces       []AnalysisInterface
	RouteTables      []AnalysisRouteTable
	PolicyEvidence   []AnalysisPolicyEvidence
	FirewallModelRef string
	Metadata         map[string]string
}

type AnalysisInterface struct {
	InterfaceCode     string
	InterfaceName     string
	VRF               string
	Zone              string
	IPv4Addresses     []string
	Status            string
	PeerDeviceCode    string
	PeerInterfaceName string
	PeerInterfaceCode string
	Source            string
}

type AnalysisRouteTable struct {
	VRF    string
	Routes []AnalysisRoute
}

type AnalysisRoute struct {
	Destination  string
	NextHopIP    string
	OutInterfaceName string
	Protocol     string
	Metric       int
	Preference   int
	NullRoute    bool
	Raw          string
	RouteSourceRef string
}
```

Policy evidence is stored in OneOPS even before engine evaluation:

```go
type AnalysisPolicyEvidence struct {
	Phase           string
	RuleID          string
	RuleName        string
	Action          string
	SourceZones     []string
	DestinationZones []string
	SourceObjectRefs []string
	DestinationObjectRefs []string
	ServiceObjectRefs []string
	RawCLI          string
	ConfigVersionID string
	EvidenceSourceRef string
}
```

This model gives OneOPS enough structure for drilldown and diagnostics without claiming that the engine has evaluated every policy phase.

## Source Mapping

### Device Identity

Primary source:

- DC2 `device_identity`

Fallback source:

- Device master data from device service.

Mapping:

```text
target_id            -> device_code
hostname             -> device_name
vendor               -> vendor
platform/os_name     -> device_type candidate or metadata
model/product_name   -> model
management_ip        -> management_ip
```

Diagnostics:

- missing device identity
- conflicting hostname or management IP
- target not in tenant scope

### Interfaces

Primary source:

- DC2 `interface`
- DC2 `interface_ip`

Fallback source:

- device interface service.

Mapping:

```text
identity_key / if_index / if_name_canonical -> interface_code join key
if_name_canonical or if_name                 -> interface_name
oper_status/admin_status                     -> status
interface_ip.cidr                            -> ipv4_addresses
interface_ip.vrf                             -> vrf
```

Rules:

- prefer canonical interface name for `InterfaceName`;
- keep original interface code when available;
- create inferred interfaces for orphan `interface_ip`, but emit diagnostics;
- normalize empty VRF to `default` when building engine-ready snapshots.

Diagnostics:

- interface IP without interface
- duplicate interface join key
- invalid CIDR
- interface VRF mismatch

### Links

Primary source:

- DC2 `topology_neighbor`

Fallback sources:

- topology snapshot service;
- device cable service;
- interface peer hints.

Mapping:

```text
target_id                         -> local device
local if_name_canonical/if_index  -> local interface
remote_device                     -> remote device candidate
remote_if_name_canonical/name     -> remote interface candidate
protocol                          -> link source
```

Rules:

- create a link only when both device endpoints and interface endpoints resolve;
- canonicalize bidirectional duplicates;
- if endpoint resolution is partial, emit a diagnostic and optionally fill `PeerDeviceCode` hints only when safe.

Diagnostics:

- remote device unresolved
- remote interface unresolved
- duplicate link endpoint
- topology conflict between DC2 and topology snapshot

### Route Tables

Primary future source:

- DC2 `route_table` facts for network devices.

Existing partial sources:

- DC2 `server_route`;
- firewall config fact snapshot routes.

Required route fact schema:

```text
fact_type: route_table
identity_key: <device>:vrf:<vrf>:destination:<prefix>:next_hop:<next-hop>:out:<interface>
fields:
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

Mapping:

```text
target_id       -> device_code
fields.vrf      -> route_table.vrf
destination     -> route.destination
next_hop_ip     -> route.next_hop_ip
out_interface   -> route.out_interface
protocol        -> route.protocol
metric          -> route.metric
preference      -> route.preference
null_route      -> route.null_route
raw             -> route.raw
```

Validation:

- `destination` must parse as an IP prefix.
- non-null routes should have `out_interface`.
- `out_interface` should uniquely match an interface in the same VRF.
- if `next_hop_ip` is present, a peer interface should have the exact next-hop IP when topology continuation is expected.

Diagnostics:

- route table missing
- route destination invalid
- route out interface missing
- route out interface unresolved
- duplicate route table for device and VRF
- next hop cannot be proven from topology

### Firewall Routes And Zones

Firewall config fact snapshot can immediately enrich snapshots for firewall nodes:

```text
facts.interfaces[].name   -> interface_name
facts.interfaces[].ips    -> ipv4_addresses
facts.interfaces[].zone   -> zone
facts.interfaces[].vrf    -> vrf
facts.routes[]            -> route table entries
facts.zones[]             -> zone/interface relationship
```

Rules:

- firewall route facts can be used as route tables when the node identity matches a OneOPS device code;
- firewall zone/interface mapping should populate `Interface.Zone`;
- policy overview should be stored as evidence, not evaluated as allow or deny until the engine supports policy phases.

Diagnostics:

- firewall node cannot map to device code
- route interface cannot map to interface
- zone references unknown interface
- policy evidence available but not evaluated

### Policy, ACL, NAT, PBR

MVP source status:

- firewall policy overview exists for firewall domain;
- generic DC2 ACL/NAT/PBR facts do not yet exist;
- oneops-netpath engine does not yet evaluate these phases.

Design rule:

- store policy, ACL, NAT, and PBR as evidence and diagnostics;
- never convert unsupported policy phases into an allowed disposition;
- when a flow crosses a device where policy facts are required but unevaluated, set snapshot diagnostic and trace confidence risk once the engine supports confidence propagation.

Recommended future fact types:

```text
acl_rule
security_policy_rule
nat_rule
pbr_rule
address_object
service_object
zone
```

## Snapshot Quality Gate

The provider must classify snapshots before analysis:

### Ready

Requirements:

- at least one device;
- target ingress device exists;
- route table exists for ingress device and requested VRF;
- all route destinations parse;
- route out interfaces can be resolved where needed.

Ready snapshots can be sent to the SDK adapter.

### Degraded

Examples:

- some devices lack route tables;
- some topology neighbors are unresolved;
- firewall policies exist but are not evaluated;
- next-hop proof is incomplete for non-primary routes.

Degraded snapshots can be analyzed, but diagnostics must be persisted and surfaced.

### Blocked

Examples:

- no devices;
- ingress device missing;
- all route tables missing;
- route table destination invalid in a way that would make SDK return error;
- tenant scope cannot be enforced.

Blocked snapshots should not be sent to the SDK adapter unless the user explicitly runs a diagnostic-only preview.

## SnapshotProvider Flow

```text
GetSnapshot(ctx, AnalyzeRequest)
  -> resolve tenant and snapshot selection
  -> if snapshot_id exists in snapshot store:
       load persisted analysis snapshot
     else:
       build latest analysis snapshot from facts
  -> validate quality gate
  -> map OneOPS analysis snapshot to netpath.Snapshot under build tag
  -> return snapshot or error
```

## Snapshot Identity

Do not use `dc2-preview-<tenant>` for analysis snapshots.

Recommended generated ID:

```text
netpath-snapshot:<tenant>:<source-hash>:<generated-at>
```

The `source-hash` should include:

- collection run IDs;
- topology snapshot ID;
- config version IDs;
- fact latest observed timestamps or fact IDs.

This allows the same source data to generate a stable snapshot identity, while still supporting explicit rebuilds.

## Reader Ports

Recommended OneOPS-owned interfaces:

```go
type LatestFactReader interface {
	ListLatestFacts(ctx context.Context, targetID string, factType string, validOnly bool, limit int) ([]dc2dto.FactRecordResp, error)
}

type DeviceInventoryReader interface {
	FindDevices(ctx context.Context, tenantCode string, deviceCodes []string) ([]DeviceInventoryItem, error)
}

type TopologyReader interface {
	GetSnapshotLinks(ctx context.Context, tenantCode string, snapshotID string) ([]TopologyLinkItem, error)
}

type FirewallFactReader interface {
	GetConfigFactSnapshot(ctx context.Context, deviceCode string) (*FirewallConfigFactSnapshot, error)
	GetPolicyOverview(ctx context.Context, deviceCode string) (*FirewallPolicyOverview, error)
}
```

Implementation should adapt existing service interfaces. It should not import service `impl` packages or read GORM tables directly.

## Relationship To SDK Adapter

The current SDK adapter is build-tagged:

```text
app/netpath/adapter/oneopsnetpath
```

It expects a provider that returns `netpath.Snapshot`.

Recommended next integration slice:

1. implement OneOPS internal `AnalysisSnapshot` assembler without importing `oneops-netpath`;
2. add a tagged mapper from `AnalysisSnapshot` to `netpath.Snapshot`;
3. implement `SnapshotProvider.GetSnapshot` using assembled or persisted snapshots;
4. wire adapter only in local or explicitly enabled builds.

This preserves default OneOPS builds until `oneops-netpath` has a stable module dependency strategy.

## MVP Scope

In scope for the next implementation plan:

- define internal analysis snapshot structs;
- define reader interfaces;
- assemble devices, interfaces, links, and route tables from injected facts;
- support DC2 `interface`, `interface_ip`, `topology_neighbor`, and proposed `route_table` facts;
- support existing `server_route` as a route source;
- support firewall config snapshot routes through a reader stub;
- validate route destinations and out-interface joins;
- produce quality diagnostics;
- add tests for ready, degraded, and blocked snapshots.

Out of scope for the next implementation plan:

- production DI wiring to the build-tagged SDK adapter;
- adding `oneops-netpath` to `go.mod`;
- committing `go.work`;
- full firewall policy evaluation;
- NAT transformation evaluation;
- PBR evaluation;
- topology UI changes;
- probe orchestration changes.

## Acceptance Criteria

- Provider design keeps preview builder and engine-ready assembler separate.
- Route tables are mandatory for meaningful analysis.
- Missing route data results in diagnostics or blocked status, not fake routes.
- Tenant scoping is explicit; if it cannot be enforced, the snapshot is blocked.
- Snapshot diagnostics preserve source references.
- Interface identifiers are normalized consistently across route, interface, and link mapping.
- Unsupported policy/NAT/PBR phases are stored as evidence or diagnostics, not evaluated as pass.
- Default OneOPS builds remain independent of `oneops-netpath`.

## Main Risks

- No generic network-device route table facts exist yet.
- Tenant filtering is not enforced by current preview builder.
- Large tenants can exceed current `latestFactLimit`.
- LLDP remote device names may not match OneOPS device codes.
- Firewall route and policy facts live behind firewall service implementation details.
- `next_hop_ip` in the engine is strict; incomplete peer interface IP data can turn otherwise valid paths into `insufficient_info`.
- Duplicate device codes, VRF route tables, or link endpoints are currently last-write-wins in the engine, so provider-side validation must catch them first.
