# NetPath DC2 Snapshot Builder Design

Date: 2026-06-18

## Purpose

This design defines the first OneOPS integration step after the standalone `oneops-netpath` MVP: build a NetPath snapshot from DC2 latest facts.

The goal is to reuse DC2 as the upstream collection and fact-normalization system, while keeping path analysis independent and deterministic.

## Scope

This phase builds a `Snapshot Builder MVP` inside OneOPS.

In scope:

- Read valid latest DC2 facts from `device_collection2_fact_latest`.
- Convert supported fact types into an engine-friendly snapshot model.
- Expose the builder through the existing NetPath service preview path.
- Return snapshot counts and diagnostics so operators can see whether DC2 has enough data to run meaningful path analysis.
- Keep the builder isolated from the standalone `oneops-netpath` repository for now by using local OneOPS DTOs or internal snapshot structs.

Out of scope:

- Running the real `oneops-netpath` engine from OneOPS.
- Persisting full snapshot versions.
- Building route tables from DC2 facts unless a route fact already exists.
- ACL, NAT, PBR, firewall policy, security policy evaluation.
- Probe orchestration.
- UI work.
- Router/Wire integration beyond what is needed for isolated service tests.

## Current Code Context

DC2 already provides the relevant storage and service surface:

- `app/device_collection2/model/fact.go`
  - `FactRecord`
  - `FactLatestRecord`
  - table `device_collection2_fact_latest`
- `app/device_collection2/fact/types.go`
  - `CanonicalFact`
  - `FactQuality`
  - `FactProvenance`
- `app/device_collection2/fact/interface_processor.go`
  - fact type `interface`
- `app/device_collection2/fact/interface_ip_processor.go`
  - fact type `interface_ip`
- `app/device_collection2/fact/topology_processor.go`
  - fact type `topology_neighbor`
- `app/device_collection2/service/i_device_collection2.go`
  - `ListLatestFacts(ctx, targetID, factType, validOnly, limit)`

OneOPS NetPath already has a thin service/API shell:

- `app/netpath/dto/netpath.go`
- `app/netpath/service/i_netpath.go`
- `app/netpath/service/impl/netpath.go`
- `app/netpath/api/netpath.go`

The current `PreviewSnapshot` response is still metadata-only. This phase replaces that placeholder with DC2-backed counts and diagnostics.

## Architecture

The Builder sits between DC2 fact storage and the NetPath service:

```text
device_collection2_fact_latest
  -> DC2 latest fact reader
  -> NetPath Snapshot Builder
  -> SnapshotSummary / SnapshotPreviewResp
  -> later Engine Runner
```

It should not call production devices. It should not parse raw CLI. DC2 has already done collection and normalization.

## Data Flow

1. User calls `PreviewSnapshot` with `tenant_code` and optional `device_codes`.
2. NetPath service asks the builder for a DC2 latest snapshot preview.
3. Builder loads valid latest DC2 facts.
4. Builder groups facts by `target_id`.
5. Builder creates device entries from target IDs and fact presence.
6. Builder attaches interface facts.
7. Builder attaches interface IP facts to matching interfaces.
8. Builder derives links from topology neighbor facts when both local and remote sides can be resolved.
9. Builder emits diagnostics for missing or incomplete data.
10. NetPath service returns `SnapshotPreviewResp`.

## Supported DC2 Fact Mapping

### interface

Source:

- `FactLatestRecord.FactType == "interface"`
- `Fields.if_index`
- `Fields.if_name`
- `Fields.if_name_canonical`
- `Fields.if_descr`
- `Fields.admin_status`
- `Fields.oper_status`

Target:

- NetPath device interface.

Mapping:

```text
target_id                 -> device_code candidate
identity_key              -> interface_code
if_name_canonical/name    -> interface_name
oper_status/admin_status  -> status
```

The MVP should prefer `if_name_canonical`, then `if_name`, then `identity_key` for display name.

### interface_ip

Source:

- `FactLatestRecord.FactType == "interface_ip"`
- `Fields.if_index`
- `Fields.if_name`
- `Fields.if_name_canonical`
- `Fields.ip`
- `Fields.prefix_len`
- `Fields.cidr`
- `Fields.vrf`

Target:

- `Interface.IPv4Addresses`
- `Interface.VRF`

Mapping:

```text
cidr                         -> ipv4_addresses entry
ip + prefix_len              -> ipv4_addresses entry if cidr missing
vrf                          -> interface vrf
if_index/if_name_canonical   -> interface join key
```

If an `interface_ip` fact has no matching `interface` fact, the builder should create an inferred interface with a warning diagnostic rather than dropping the address.

### topology_neighbor

Source:

- `FactLatestRecord.FactType == "topology_neighbor"`
- local interface fields from `copyLocalInterfaceFields`
- `Fields.remote_device`
- `Fields.remote_if_name`
- `Fields.remote_if_name_canonical`
- `Fields.remote_ip`
- `Fields.remote_mac`
- `Fields.protocol`

Target:

- Snapshot link.

Mapping:

```text
target_id                         -> local device
local if_name/if_name_canonical   -> local interface
remote_device                     -> remote device candidate
remote_if_name_canonical/name     -> remote interface candidate
protocol                          -> link source
```

The MVP should only create a link when both endpoint device and interface identifiers are present. If remote side cannot be resolved, emit a diagnostic rather than inventing a link.

## Snapshot Summary Model

The MVP does not need to persist full snapshot JSON yet. It should still use an internal summary model so tests can inspect builder output without depending only on counts.

Recommended internal package:

```text
app/netpath/snapshot
```

Recommended types:

```go
type BuildRequest struct {
    TenantCode  string
    DeviceCodes []string
}

type Snapshot struct {
    SnapshotID  string
    TenantCode  string
    Devices     []Device
    Links       []Link
    Diagnostics []Diagnostic
}

type Device struct {
    DeviceCode string
    Interfaces []Interface
}

type Interface struct {
    InterfaceCode string
    InterfaceName string
    VRF           string
    IPv4Addresses []string
    Status        string
}

type Link struct {
    ADeviceCode string
    AInterface  string
    BDeviceCode string
    BInterface  string
    Source      string
}

type Diagnostic struct {
    Severity string
    Code     string
    Message  string
    Refs     []string
}
```

This model mirrors the standalone engine shape closely enough for a future engine adapter, but avoids importing `oneops-netpath` into OneOPS during this phase.

## Fact Reader Boundary

The builder should depend on an interface rather than directly depending on `DeviceCollection2Srv`.

Recommended interface:

```go
type LatestFactReader interface {
    ListLatestFacts(ctx context.Context, targetID string, factType string, validOnly bool, limit int) ([]dc2dto.FactRecordResp, error)
}
```

The production service can pass DC2 service later. Unit tests can use a fake reader.

The MVP should call:

```text
ListLatestFacts(ctx, "", "interface", true, limit)
ListLatestFacts(ctx, "", "interface_ip", true, limit)
ListLatestFacts(ctx, "", "topology_neighbor", true, limit)
```

Device filtering should happen in the builder after reading facts. This keeps the reader interface aligned with the existing DC2 service.

## Service Integration

`NetPathService` should accept an optional snapshot builder dependency.

Recommended constructor expansion:

```go
func NewNetPathService(db *gorm.DB, options ...Option) *NetPathService
```

Recommended option:

```go
func WithSnapshotBuilder(builder SnapshotBuilder) Option
```

Where:

```go
type SnapshotBuilder interface {
    BuildPreview(ctx context.Context, req snapshot.BuildRequest) (*snapshot.Snapshot, error)
}
```

When no builder is configured, keep the current metadata-only fallback. This preserves existing tests and lets router/Wire work come later.

`PreviewSnapshot` behavior:

- Validate `tenant_code`.
- If no builder exists, return current preview fallback with warning.
- If builder exists, return:
  - `snapshot_id`
  - `tenant_code`
  - device count
  - link count
  - warning messages from diagnostics

## Diagnostics

The builder should return diagnostics instead of failing when data is incomplete.

Recommended diagnostic codes:

- `dc2_facts_empty`: no latest facts found for supported types.
- `interface_ip_without_interface`: IP fact could not join to an interface fact.
- `topology_remote_unresolved`: topology neighbor could not be converted into a link.
- `route_table_missing`: no route facts are available in this MVP.

Hard errors should be reserved for infrastructure failures, such as DC2 reader/database errors.

## Testing Strategy

Unit tests should use fake latest fact reader data and assert the internal snapshot structure.

Required tests:

1. Builds devices and interfaces from `interface` facts.
2. Attaches IPv4 CIDRs and VRF from `interface_ip` facts.
3. Creates links from resolvable `topology_neighbor` facts.
4. Emits `interface_ip_without_interface` for orphan IP facts.
5. Emits `topology_remote_unresolved` for unresolved neighbor facts.
6. `NetPathService.PreviewSnapshot` returns DC2-backed device/link counts when a builder is configured.
7. Existing metadata fallback behavior still works when no builder is configured.

## Future Phases

After this snapshot builder MVP:

1. Add route table DC2 contracts/facts and map them into route tables.
2. Persist snapshot versions in OneOPS.
3. Add Engine Runner to call `oneops-netpath`.
4. Add Probe Orchestrator after analysis runs.
5. Add ACL/NAT/PBR/firewall evaluator inputs.
6. Add UI path visualization and policy drill-down.

## Acceptance Criteria

This phase is complete when:

- OneOPS has an isolated `app/netpath/snapshot` builder package.
- The builder consumes DC2 latest fact DTOs through an interface.
- `PreviewSnapshot` can return real device/link counts from DC2 facts in tests.
- Incomplete DC2 data produces diagnostics/warnings, not crashes.
- No OneOPS production router/Wire coupling is required to test the feature.
- No direct dependency from OneOPS service tests to the standalone `oneops-netpath` repository is introduced.
