# OneOPS DC2 Minimal Contract And Dataset Design

## Purpose

This design freezes the first minimal `Device Collection 2` contract and dataset registry that upper-level OneOPS applications may depend on directly.

The goal is not to define every future canonical fact. The goal is to stop NetPath and IPAM from each depending on slightly different assumptions about:

- which canonical facts are already stable enough to consume
- which fields are required versus optional
- which gaps should degrade a result versus block it
- which provenance and quality fields must always survive into application snapshots or projections

This document is intentionally small. It covers only the dataset families that are already high-value and close to real consumption.

Parent documents:

- `docs/superpowers/specs/2026-06-19-oneops-fact-application-foundation-design.md`
- `docs/superpowers/specs/2026-06-19-oneops-canonical-fact-contract-design.md`
- `docs/superpowers/specs/2026-06-20-oneops-netpath-policy-fact-foundation-design.md`
- `docs/superpowers/2026-06-21-post-2026-06-18-analysis.md`

## Scope

In scope:

- first minimal shared dataset registry
- dataset-level required fields
- identity and dedup rules
- minimum quality and provenance requirements
- versioning rules for application-safe consumption
- consumer mapping for NetPath and IPAM

Out of scope:

- full policy fact registry
- complete firewall fact families
- every possible DC2 dataset
- changing the base canonical fact envelope
- replacing application-local tables such as `ipam_address_fact`

## Design Decision

Freeze the shared layer in two pieces:

1. a common canonical fact envelope that every accepted dataset instance must satisfy
2. a minimal dataset registry for the five highest-value fact families:
   - `route_table`
   - `interface_ip`
   - `arp_entry`
   - `mac_table_entry`
   - `topology_neighbor`

Applications may treat only these five families as phase-one application-safe datasets.

Everything else stays in one of these states:

- experimental
- consumer-specific
- not yet frozen

This is the boundary rule:

```text
If a dataset family is not frozen here, upper-level applications may read it only behind an application-specific seam and must not treat it as a stable shared contract.
```

## Common Canonical Fact Contract

Every dataset in this document inherits the existing canonical fact envelope:

```text
fact_id
run_id
target_id
fact_type
identity_key
fields
quality
provenance
valid
confidence
observed_at
created_at
updated_at
```

### Envelope Requirements

Required for application-safe consumption:

- `fact_type`
- `target_id`
- `identity_key`
- `fields`
- `quality.valid`
- `quality.confidence`
- `quality.issues`
- `provenance.contract_key`
- `provenance.dataset_key`
- `provenance.processor_key`
- `provenance.processor_version`
- `provenance.source_fields`
- `observed_at`

Required behavior:

- rows with no stable identity must become `FactIssue`, not accepted facts
- application consumers should default to `valid=true`
- `dataset_key` describes source collection shape, not business fact meaning
- `fact_type` describes business meaning, not raw source command name
- provenance must be rich enough for evidence drilldown

### Version Boundary

This document introduces a practical version rule for application-safe datasets:

- breaking field or identity changes require a new `processor_version`
- if the meaning of a required normalized field changes, the old and new shapes must not share the same effective contract silently
- applications must assume that:
  - `processor_version` tracks normalization shape
  - `dataset_key` tracks raw-source lineage
  - `fact_type` tracks business semantic family

Phase-one platform rule:

```text
Applications may rely on fact_type + required fields + identity rule only when processor_version changes on breaking normalization updates.
```

## Minimal Dataset Registry

### 1. route_table

Purpose:

- represent forwarding routes needed by NetPath and future L3 reasoning

Required fields:

```text
vrf
destination
out_interface
protocol
metric
preference
null_route
```

Normalization note:

- `next_hop_ip` is required for non-direct, non-null routes
- direct or connected routes may omit `next_hop_ip` if the route semantics are explicit

Optional but recommended:

```text
raw
route_type
source_protocol_detail
```

Identity rule:

```text
<target_id>:route:vrf:<vrf>:dest:<destination>:nh:<next_hop_or_direct_or_null>:out:<out_interface_or_none>
```

Quality rule:

- `valid=false` when destination prefix cannot be normalized
- `confidence` must be reduced when route source is partial or interface binding is unresolved
- issue codes should include:
  - `missing_required_field`
  - `invalid_prefix`
  - `invalid_ip`
  - `invalid_metric`
  - `invalid_preference`

Provenance rule:

- `dataset_key` must name the route-collection dataset
- `source_fields` must include the raw route prefix, next hop, and out-interface source fields

Blocking gaps:

- ingress device route table missing
- reached hop route table missing
- route cannot be normalized for the candidate VRF

Primary consumers:

- NetPath snapshot assembly

### 2. interface_ip

Purpose:

- bind L3 addresses to device interfaces

Required fields:

```text
ip
cidr
prefix_len
vrf
addr_type
```

Join-anchor rule:

- at least one stable interface anchor is required:
  - `if_index`
  - `if_name_canonical`

Optional but recommended:

```text
if_name
netmask
scope
primary
```

Identity rule:

```text
target_id:if_index:<if_index>:ip:<ip>
target_id:if_name:<if_name_canonical>:ip:<ip>
```

Quality rule:

- `valid=false` when IP or prefix cannot be normalized
- `confidence` should be reduced if interface join anchors are incomplete
- issue codes should include:
  - `invalid_ip`
  - `invalid_prefix`
  - `missing_interface_identity`

Provenance rule:

- `source_fields` must include raw interface name or index plus raw IP and mask fields

Blocking gaps:

- source or ingress interface cannot be resolved for a path flow

Primary consumers:

- NetPath
- IPAM projection

### 3. arp_entry

Purpose:

- represent observed IP-to-MAC resolution from ARP or neighbor cache

Required fields:

```text
ip
mac
```

Join-anchor rule:

- interface context should include at least one of:
  - `if_name_canonical`
  - `if_index`

Recommended enrichment:

```text
if_index
vlan_id
vrf
entry_type
age
state
```

Identity rule:

```text
target_id:ip:<ip>:mac:<mac>:if:<if_name_canonical_or_none>
```

Quality rule:

- `valid=false` when IP or MAC is malformed
- `confidence` should be reduced when interface context is missing
- issue codes should include:
  - `invalid_ip`
  - `invalid_mac`
  - `missing_required_field`

Provenance rule:

- `source_fields` must include raw IP, MAC, and interface origin fields

Blocking gaps:

- none for phase-one NetPath

Degraded gaps:

- missing interface join anchor
- missing `vrf`
- missing freshness detail such as `age` or `state`

Primary consumers:

- IPAM projection
- endpoint evidence

### 4. mac_table_entry

Purpose:

- represent learned forwarding database entries

Naming rule:

- `mac_table_entry` is the canonical shared fact type
- older references to `mac_table` should be treated as legacy product language, not a separate shared contract

Required fields:

```text
mac
entry_type
```

Join-anchor rule:

- local switching context should include at least one of:
  - `if_name_canonical`
  - `if_index`
  - `bridge_port`

Recommended enrichment:

```text
if_index
vlan_id
bridge_port
```

Identity rule:

```text
target_id:mac:<mac>:vlan:<vlan_or_none>:if:<if_name_canonical_or_none>:bridge:<bridge_port_or_none>
```

Quality rule:

- `valid=false` when MAC is malformed
- `confidence` should be reduced when VLAN or interface anchors are missing
- issue codes should include:
  - `invalid_mac`
  - `missing_required_field`

Provenance rule:

- `source_fields` must include raw MAC, local interface, and VLAN source fields when present

Blocking gaps:

- none for phase-one NetPath

Degraded gaps:

- missing local interface anchor
- missing VLAN context

Primary consumers:

- IPAM projection
- topology evidence

### 5. topology_neighbor

Purpose:

- represent LLDP/CDP or equivalent adjacency observations

Required fields:

```text
local_if_name_canonical
protocol
remote_device
```

Recommended enrichment:

```text
local_if_index
remote_if_name_canonical
remote_ip
remote_chassis_id
remote_platform
collection_transport
```

Identity rule:

```text
target_id:<local-interface-identity>:remote:<remote-identity>
```

Quality rule:

- `valid=false` when local interface identity is missing or remote endpoint identity is empty
- `confidence` should be reduced when only weak remote identity is available
- issue codes should include:
  - `missing_local_interface`
  - `missing_remote_identity`
  - `ambiguous_remote_identity`

Provenance rule:

- `source_fields` must include local interface fields and the raw remote identity inputs used to build the normalized remote endpoint

Blocking gaps:

- none by itself

Degraded gaps:

- selected route out-interface has no trusted neighbor match
- remote side has weak identity only

Primary consumers:

- NetPath link assembly
- topology

## Application Consumption Mapping

### NetPath

NetPath may treat these datasets as phase-one shared inputs:

- `route_table`
- `interface_ip`
- `topology_neighbor`

NetPath may treat these as supporting evidence, not path-readiness anchors:

- `arp_entry`
- `mac_table_entry`

NetPath readiness rule:

- `route_table` is required
- `interface_ip` is required when ingress, endpoint, or delivery resolution depends on interface addressing
- `topology_neighbor` may degrade or block depending on whether the route can still be explained without peer confirmation
- `arp_entry` and `mac_table_entry` must not silently upgrade a blocked path into ready

### IPAM

IPAM may treat these datasets as phase-one shared inputs:

- `interface_ip`
- `arp_entry`
- `mac_table_entry`

IPAM may use `topology_neighbor` only as context, not as a first-phase allocation or audit dependency.

IPAM projection rule:

- `interface_ip` is the base address anchor
- `arp_entry` adds observed IP-to-MAC context
- `mac_table_entry` adds switching evidence and duplicate-MAC or drift context
- missing ARP or MAC evidence must not block projection of a valid `interface_ip`

Implementation note:

- `mac_table_entry` is frozen as a shared fact family, but the IPAM `ProjectCanonicalLatest` API keeps its default fact list narrow in phase one.
- Operators may still request `mac_table_entry` explicitly for validation or future projection work.
- This keeps the shared contract ahead of the default projection workflow without pretending that MAC-only records already produce first-class IPAM address facts.

## Dataset State Model

Each canonical fact family should be labeled in one of these states:

- `frozen`: safe for shared application consumption
- `experimental`: present in code or design, but not yet stable as a cross-application contract
- `consumer_specific`: valid only behind one application seam

Phase-one state assignment:

| fact_type | state | note |
| --- | --- | --- |
| `route_table` | `frozen` | required for NetPath route reasoning |
| `interface_ip` | `frozen` | required by both NetPath and IPAM |
| `arp_entry` | `frozen` | shared observational evidence for IPAM and endpoint context |
| `mac_table_entry` | `frozen` | shared switching evidence |
| `topology_neighbor` | `frozen` | shared adjacency anchor |
| policy fact families | `experimental` | not frozen by this document |
| application-local projections | `consumer_specific` | remain owned by each app |

## Non-Goals

This design does not:

- freeze ACL, NAT, PBR, zone, or firewall object facts
- define every dataset-specific SQL schema change
- require every application to migrate immediately
- replace snapshot-specific quality gates with dataset-only rules

## Acceptance Criteria

This design is accepted when:

1. NetPath and IPAM can both reference the same five frozen fact families without redefining their minimum fields in separate documents.
2. A reviewer can answer, for each of the five families:
   - what the dataset means
   - which fields are required
   - how identity is built
   - which gaps block versus degrade
   - which provenance must survive
3. Future dataset additions can be labeled `experimental` first, instead of being treated as shared contracts by default.

## Follow-Up

Immediate next steps after this document:

1. verify actual processor outputs in the main OneOPS worktree against the five frozen dataset definitions
2. patch mismatches in `route_table`, `arp_entry`, and `mac_table_entry` processors or DTOs where required fields or provenance are still thin
3. add a small shared registry or documentation index that lists each fact family with its state label
4. freeze the first policy fact subset separately after NetPath chooses the minimum evaluator/evidence lane

## Conclusion

The important move here is not “define more facts.” The important move is to define a small set of facts that applications may depend on without guessing.

For this phase, OneOPS should treat:

- `route_table`
- `interface_ip`
- `arp_entry`
- `mac_table_entry`
- `topology_neighbor`

as the first minimal DC2 shared contract surface.
