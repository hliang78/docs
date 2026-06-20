# OneOPS Canonical Fact Contract Design

## Purpose

This document freezes the first shared canonical fact contract for OneOPS upper-level applications.

The contract is intentionally based on the existing Device Collection 2 fact model instead of creating a parallel fact platform. L2 snapshot, IPAM, NetPath, topology, RCA, and future agent workflows should use this contract when they consume collected facts.

Parent tracking documents:

- `docs/superpowers/specs/2026-06-19-oneops-fact-application-foundation-design.md`
- `docs/superpowers/plans/2026-06-19-oneops-fact-application-foundation-master-plan.md`

## Current Scope

This phase only freezes the contract for facts that can support near-term application work.

In scope:

- core fact envelope
- fact identity rules
- initial fact type registry
- application consumption rules
- quality and provenance requirements
- known gaps that block IPAM and NetPath

Out of scope:

- replacing existing IPAM workflow tables
- building a generic graph database
- changing all existing consumers at once
- symbolic path analysis
- fuzzy automatic identity matching

## Existing Fact Envelope

Current canonical fact records already contain the right envelope shape.

Required fields:

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

Supporting tables:

```text
device_collection2_fact
device_collection2_fact_latest
device_collection2_fact_issue
```

Contract rule:

- `device_collection2_fact` is append-oriented observation history.
- `device_collection2_fact_latest` is the current latest projection by target, fact type, and identity.
- `device_collection2_fact_issue` records rows that could not safely become canonical facts.

## Required Envelope Semantics

### fact_type

`fact_type` names the normalized business fact, not the source dataset.

Examples:

- good: `interface_ip`
- good: `topology_neighbor`
- weak: `snmp_ip_addr_entry`
- weak: `cli_show_ip_route`

Source dataset names belong in `provenance.dataset_key`.

### target_id

`target_id` identifies the primary observed object for the fact. For network-device facts, this should normally be the device code or stable collection target id.

Contract rule:

- consumers must not assume `target_id` is globally unique without `fact_type` and `identity_key`
- tenant-aware queries must filter by explicit tenant scope or by a reviewed target set

### identity_key

`identity_key` is the stable deduplication key within:

```text
target_id + fact_type
```

It must be deterministic, trimmed, and based on normalized fields.

Contract rule:

- if identity cannot be built, the processor must emit an issue instead of an invalid accepted fact
- identity keys must not depend on row order
- identity keys must not depend on display names when stable ids are available

### fields

`fields` contains normalized application-facing values.

Contract rule:

- raw source field names should be mapped to normalized names
- fields required by applications must be documented per fact type
- raw unparsed blobs should be referenced through provenance or raw refs, not mixed into normalized fields unless explicitly named `raw`

### quality

Minimum shape:

```json
{
  "valid": true,
  "confidence": 0.9,
  "issues": []
}
```

Contract rule:

- application consumers should normally consume only `valid=true`
- low confidence facts are allowed but must remain visible to upper applications
- invalid rows should usually become issues, not accepted facts

### provenance

Minimum shape:

```json
{
  "contract_key": "...",
  "dataset_key": "...",
  "source_fields": ["..."],
  "processor_key": "...",
  "processor_version": "v1"
}
```

Contract rule:

- every canonical fact must identify the processor and source dataset
- `source_fields` should name the raw fields that produced normalized identity and application fields
- provenance must be sufficient for evidence drilldown

## Initial Fact Type Registry

### device_identity

Status: existing or partially existing.

Purpose:

- identify the device or collection target behind other facts
- support application display and target scoping

Expected normalized fields:

```text
device_code
device_name
hostname
management_ip
vendor
platform
model
os_version
serial_number
```

Identity rule:

```text
target_id
```

Primary consumers:

- topology
- NetPath
- RCA
- IPAM evidence

### interface

Status: existing.

Purpose:

- describe network interfaces and provide stable join keys for interface IP, MAC, topology, and route facts

Expected normalized fields:

```text
if_index
if_name
if_name_canonical
if_descr
mac
status
speed
admin_status
oper_status
```

Identity rule preference:

```text
target_id:if_index:<if_index>
target_id:if_name:<if_name_canonical>
```

Primary consumers:

- L2 snapshot
- IPAM
- NetPath
- topology

### interface_ip

Status: existing.

Purpose:

- bind IP addresses to device interfaces

Expected normalized fields:

```text
if_index
if_name
if_name_canonical
ip
prefix_len
netmask
cidr
vrf
addr_type
```

Identity rule preference:

```text
target_id:if_index:<if_index>:ip:<ip>
target_id:if_name:<if_name_canonical>:ip:<ip>
```

Primary consumers:

- IPAM fact projection
- NetPath snapshot provider
- topology interface details
- RCA context

### topology_neighbor

Status: existing.

Purpose:

- represent LLDP/CDP or equivalent neighbor observations

Expected normalized fields:

```text
local_if_index
local_if_name
local_if_name_canonical
protocol
collection_transport
remote_device
remote_if_name
remote_if_name_canonical
remote_chassis_id
remote_mac
remote_ip
remote_platform
remote_version
```

Identity rule:

```text
target_id:<local-interface-identity>:remote:<remote-identity>
```

Primary consumers:

- L2 snapshot
- topology
- NetPath link assembly

### mac_table_entry

Status: existing.

Purpose:

- represent learned forwarding database entries

Expected normalized fields:

```text
mac
vlan_id
if_index
if_name
if_name_canonical
entry_type
bridge_port
```

Identity rule:

```text
target_id + mac + optional vlan_id + optional bridge_port + optional local interface
```

Primary consumers:

- IPAM fact projection
- L2 diagnostics
- topology evidence

Naming note:

- current code emits `mac_table_entry`
- older product language may still say `mac_table`
- application contracts should treat `mac_table_entry` as the canonical fact type unless a migration explicitly renames it

### arp_entry

Status: existing but thin.

Purpose:

- bind IP to MAC as observed from ARP or neighbor cache

Expected normalized fields:

```text
ip
mac
if_index
if_name
if_name_canonical
vlan_id
entry_type
```

Identity rule preference:

```text
target_id + ip + mac + optional local interface
```

Known enrichment gaps:

- `vrf`
- `age`
- `state`
- source protocol detail
- L3/L2 resolution metadata

Primary consumers:

- IPAM fact projection
- duplicate IP and MAC drift audit
- RCA endpoint context

### route_table

Status: required gap.

Purpose:

- represent forwarding route entries for NetPath and future L3 topology

Required normalized fields:

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

Identity rule:

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

Primary consumers:

- NetPath snapshot provider
- L3 topology
- RCA path reasoning

### firewall_policy

Status: first-phase NetPath fact gap.

Purpose:

- expose policy evidence for NetPath, RCA, and change impact analysis
- prevent NetPath from returning confident allow decisions when required policy evidence is missing

Expected normalized fields:

```text
phase
rule_id
rule_name
action
source_zones
destination_zones
source_object_refs
destination_object_refs
service_object_refs
raw_cli
config_version_id
policy_source
```

Identity rule:

```text
target_id:phase:<phase>:rule:<rule_id-or-rule_name>
```

Primary consumers:

- NetPath policy evidence
- RCA
- firewall change impact

Related first-phase NetPath policy fact families:

- `security_zone_binding`
- `acl_rule`
- `nat_rule`
- `pbr_rule`
- `address_object`
- `service_object`
- `policy_parser_diagnostic`

Detailed first-phase contract:

- `docs/superpowers/specs/2026-06-20-oneops-netpath-policy-fact-foundation-design.md`

## Application Consumption Rules

### L2 Snapshot

L2 snapshot may consume:

- `interface`
- `topology_neighbor`
- `mac_table`
- `arp_entry`

It should publish:

- explicit snapshot code
- source batch codes or fact run ids
- readiness
- association summary
- association issues
- edge and device counts

### IPAM

IPAM may consume:

- `interface_ip`
- `mac_table`
- `arp_entry`
- existing `IPAMAgg` during migration

It should keep:

- planning records
- address pools
- reserved ranges
- request workflows
- allocation/reclaim state
- audit findings

Projection rule:

```text
canonical facts -> ipam_address_fact -> ipam audit findings
```

IPAM audit findings must keep enough source context to reach canonical facts.

### NetPath

NetPath may consume:

- `device_identity`
- `interface`
- `interface_ip`
- `topology_neighbor`
- `route_table`
- future firewall evidence facts

It should build:

- engine-ready immutable analysis snapshot
- path analysis run
- trace, hop, step, and diagnostic records

NetPath must not fake route tables when route facts are missing.

### RCA And Agent Workflows

RCA and agents should consume:

- application snapshots
- application projections
- canonical fact evidence

They should not consume raw collection rows directly unless acting as a diagnostic drilldown tool.

## Quality Gates

A fact processor is contract-compliant when:

- required identity fields are normalized before identity_key is built
- missing required identity fields create issues
- invalid IP, MAC, CIDR, route prefix, or interface identity creates issues
- accepted facts carry valid quality and provenance
- latest projection does not drop quality, provenance, or observed time

An application projection is contract-compliant when:

- source fact type is explicit
- source run or fact reference is preserved
- repeated projection is idempotent
- stale or low confidence source facts remain visible

## Phase 1 Deliverables

- Freeze this contract with implementation evidence from current code.
- Add a detailed implementation plan for missing tests and small contract hardening changes.
- Use this contract as the input to IPAM projection, route table fact, and NetPath snapshot provider plans.
