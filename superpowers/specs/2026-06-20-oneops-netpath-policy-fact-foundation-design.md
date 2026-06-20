# OneOPS NetPath Policy Fact Foundation Design

Date: 2026-06-20

## Purpose

This design expands the first NetPath fact phase from route-only collection into a complete path-analysis fact foundation.

The first phase must include routing, firewall, ACL, NAT, PBR, zone, and policy-object facts. The engine may evaluate these families in stages, but the collection and snapshot contracts must not postpone them. If a path depends on policy semantics and the required facts are missing or untrusted, NetPath must not return a confident allowed result.

Parent documents:

- `docs/superpowers/specs/2026-06-19-oneops-fact-application-foundation-design.md`
- `docs/superpowers/specs/2026-06-19-oneops-canonical-fact-contract-design.md`
- `docs/superpowers/specs/2026-06-19-oneops-netpath-snapshot-provider-design.md`
- `docs/superpowers/plans/2026-06-19-oneops-netpath-master-roadmap.md`
- `docs/superpowers/acceptance/2026-06-19-oneops-netpath-user-journeys-checklist.md`

## Current Code Facts

### DC2 Canonical Facts

Device Collection 2 already has the right canonical envelope:

```text
fact_type
target_id
identity_key
fields
quality
provenance
valid
confidence
observed_at
latest projection
issue rows
```

Existing or planned NetPath-relevant fact processors include:

- `device_identity`
- `interface`
- `interface_ip`
- `topology_neighbor`
- `mac_table_entry`
- `arp_entry`
- `server_route`
- `route_table` in the route-table phase work

The provider-side NetPath assembler already expects:

- `device_identity`
- `interface`
- `interface_ip`
- `topology_neighbor`
- `route_table`
- `server_route`

### Firewall Config Snapshot

`OneOPS/app/firewall/service/impl/config_fact_snapshot.go` already models a firewall config snapshot with:

- `facts.interfaces`
- `facts.zones`
- `facts.routes`
- diagnostics for policy and NAT parsing counts
- config health, vendor confidence, and manual-review state

The current snapshot structure is useful but too thin for NetPath policy reasoning because it only counts policy and NAT items. It does not yet expose normalized ACL, NAT, PBR, security policy, or object rows as first-class path facts.

### Firewall Business Models

The firewall module already owns planning and business-policy models that should be reused as supporting facts:

- `firewall_security_zone`
- `firewall_network_segment`
- `firewall_zone_mapping`
- `firewall_zone_security_rule`

These are not raw device config facts. They are planning or business-governance facts. NetPath should consume them as policy context, not confuse them with parsed device config.

### Engine Boundary

`oneops-netpath` currently evaluates route and topology traversal only. Its own roadmap explicitly lists firewall policy, ACL, NAT, and PBR as future pluggable evaluator work.

That boundary remains valid. This design changes the first-phase fact scope, not the engine coupling rule.

## Design Decision

First-phase NetPath facts must include both:

1. forwarding facts required to find candidate paths;
2. policy facts required to decide whether a candidate path can be trusted.

Evaluation may be incremental:

- route lookup can be fully evaluated first;
- policy, ACL, NAT, and PBR may initially appear as evidence and diagnostics;
- missing required policy facts must block or degrade confidence instead of silently allowing traffic.

The platform rule is:

```text
If a hop crosses a firewall or policy-controlled boundary and the relevant ACL/NAT/PBR/security-policy facts are missing, unsupported, stale, or low confidence, NetPath must not report a confident allowed path.
```

## First-Phase Fact Registry

### device_identity

Role:

- identify every device in the analysis scope.

Required for NetPath:

- all device types.

Important fields:

```text
device_code
hostname
management_ip
vendor
platform
model
device_type
```

Missing behavior:

- missing device identity for a requested scope device blocks snapshot readiness.

### interface

Role:

- provide per-device interface join anchors for IP, route, topology, zone, and policy binding.

Important fields:

```text
if_index
if_name
if_name_canonical
admin_status
oper_status
mac
speed
vrf
zone
```

Missing behavior:

- route out-interface cannot be resolved: degraded.
- ingress interface cannot be resolved when required by the flow: blocked.

### interface_ip

Role:

- bind device interfaces to L3 addresses and VRFs.

Important fields:

```text
if_index
if_name_canonical
ip
cidr
prefix_len
vrf
addr_type
```

Missing behavior:

- destination subnet delivery cannot be proven without interface or route evidence.

### topology_neighbor

Role:

- resolve hop-to-hop adjacency.

Important fields:

```text
local_if_index
local_if_name_canonical
remote_device
remote_if_name_canonical
remote_ip
remote_chassis_id
protocol
```

Missing behavior:

- missing peer for selected route out-interface degrades or blocks depending on whether the route is terminal connected delivery.

### route_table

Role:

- model network-device forwarding routes.

Important fields:

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

Identity:

```text
<target_id>:route:vrf:<vrf>:dest:<destination>:nh:<next_hop_or_direct_or_null>:out:<out_interface_or_none>
```

Missing behavior:

- missing route table for ingress device and VRF blocks the analysis snapshot.
- missing route table on a later hop blocks if traversal reaches that device.

### security_zone_binding

Role:

- bind interfaces, prefixes, VRFs, or firewall config zones to OneOPS security zones.

Sources:

- parsed firewall config snapshot `facts.zones`
- parsed interface zone values
- `firewall_zone_mapping`
- `firewall_security_zone`
- `firewall_network_segment`

Important fields:

```text
zone_id
zone_code
zone_name
zone_type
zone_role
tenant_code
vrf
interface_name
interface_ip
prefix
config_zone
mapping_source
```

Identity:

```text
<target_id>:zone_binding:<zone_or_prefix_or_interface_key>
```

Issue codes:

```text
zone_missing
zone_unmapped
interface_zone_conflict
prefix_zone_conflict
tenant_zone_conflict
```

Missing behavior:

- missing zone on a firewall policy hop degrades.
- missing zone when policy rules use zones blocks policy decision.

### acl_rule

Role:

- represent ingress, egress, or interface ACL behavior.

Sources:

- parsed firewall or network device config
- future DC2 CLI config parsers
- imported normalized rule sets

Important fields:

```text
acl_name
rule_id
sequence
direction
interface_name
vrf
action
protocol
source_objects
destination_objects
source_cidrs
destination_cidrs
source_ports
destination_ports
log
enabled
raw_cli
config_version_id
```

Identity:

```text
<target_id>:acl:<acl_name>:dir:<direction>:seq:<sequence_or_rule_id>
```

Issue codes:

```text
missing_rule_id
invalid_action
unresolved_address_object
unresolved_service_object
unsupported_acl_syntax
shadowed_rule_unclassified
```

Missing behavior:

- if an interface or zone declares an ACL and ACL facts are missing, the path is blocked for confident allow.

### firewall_policy

Role:

- represent zone-to-zone or global security policy decisions.

Sources:

- parsed firewall config snapshot
- firewall policy validation or generated policy artifacts
- business-side `firewall_zone_security_rule` as planning context

Important fields:

```text
phase
rule_id
rule_name
sequence
action
source_zones
destination_zones
source_object_refs
destination_object_refs
service_object_refs
source_cidrs
destination_cidrs
protocols
ports
schedule
enabled
log
raw_cli
config_version_id
policy_source
```

Identity:

```text
<target_id>:policy:<phase>:seq:<sequence_or_rule_id>
```

Issue codes:

```text
missing_rule_id
invalid_action
unresolved_zone
unresolved_address_object
unresolved_service_object
unsupported_policy_syntax
implicit_deny_only
```

Missing behavior:

- missing policy facts on a firewall hop blocks confident allow.
- explicit deny should eventually produce a denied disposition.
- before evaluators exist, matched or potentially relevant policy evidence must appear in diagnostics or evidence stubs.

### nat_rule

Role:

- represent source NAT, destination NAT, static NAT, dynamic NAT, and VIP transformations.

Sources:

- parsed firewall config snapshot
- firewall network segment `segment_type` for planning context
- future DC2 config parsers

Important fields:

```text
nat_type
phase
rule_id
sequence
action
source_zones
destination_zones
original_source
original_destination
original_service
translated_source
translated_destination
translated_service
pool_refs
enabled
raw_cli
config_version_id
```

Identity:

```text
<target_id>:nat:<phase>:seq:<sequence_or_rule_id>
```

Issue codes:

```text
missing_rule_id
invalid_nat_type
unresolved_nat_pool
unresolved_address_object
unresolved_service_object
unsupported_nat_syntax
ambiguous_translation
```

Missing behavior:

- missing NAT facts on a NAT-capable firewall hop blocks confident allow when the flow crosses a NAT domain or when diagnostics say NAT parsing was skipped.
- known NAT unsupported syntax should be a blocking diagnostic for flows that may match it.

### pbr_rule

Role:

- represent policy-based routing that can override route-table next-hop selection.

Sources:

- parsed firewall or router config
- future DC2 config parsers

Important fields:

```text
pbr_name
rule_id
sequence
vrf
interface_name
source_objects
destination_objects
source_cidrs
destination_cidrs
protocols
ports
action
next_hop_ip
out_interface
set_vrf
enabled
raw_cli
config_version_id
```

Identity:

```text
<target_id>:pbr:<pbr_name_or_vrf>:seq:<sequence_or_rule_id>
```

Issue codes:

```text
missing_rule_id
invalid_next_hop
invalid_set_vrf
unresolved_match_object
unsupported_pbr_syntax
```

Missing behavior:

- if a device has PBR configured but PBR facts are missing, route lookup alone is insufficient for confident allow.

### address_object

Role:

- normalize host, subnet, range, FQDN, group member, and VIP address objects used by policy, ACL, NAT, and PBR.

Important fields:

```text
object_id
object_name
object_type
cidr
ip
range_start
range_end
fqdn
members
zone
raw_cli
config_version_id
```

Identity:

```text
<target_id>:addr_obj:<object_name_or_id>
```

Issue codes:

```text
invalid_cidr
invalid_ip_range
recursive_group
missing_member
unsupported_object_type
```

Missing behavior:

- unresolved objects block policy/NAT/PBR decisions that reference them.

### service_object

Role:

- normalize protocol and port objects used by policy and ACL rules.

Important fields:

```text
object_id
object_name
protocol
ports
port_ranges
icmp_type
members
raw_cli
config_version_id
```

Identity:

```text
<target_id>:svc_obj:<object_name_or_id>
```

Issue codes:

```text
invalid_protocol
invalid_port
recursive_group
missing_member
unsupported_service_type
```

Missing behavior:

- unresolved service objects block policy decisions that reference them.

### policy_parser_diagnostic

Role:

- make unsupported or skipped policy/NAT/PBR parsing visible as first-class evidence.

Sources:

- firewall config snapshot diagnostics
- DC2 fact issues
- vendor parser output

Important fields:

```text
diagnostic_code
severity
phase
parser_key
vendor
platform
config_section
line_number
message
raw_excerpt_ref
confidence_impact
```

Identity:

```text
<target_id>:policy_diag:<phase>:<diagnostic_code>:<line_or_hash>
```

Missing behavior:

- high-severity parser diagnostics block confident allow for affected phases.

## Device-Type Collection Definitions

### Network Router Or Switch

Required forwarding facts:

- `device_identity`
- `interface`
- `interface_ip`
- `topology_neighbor`
- `route_table`

Optional but useful:

- `mac_table_entry`
- `arp_entry`
- `acl_rule`
- `pbr_rule`
- `address_object`
- `service_object`

Blocking gaps:

- missing ingress route table
- PBR configured but not parsed
- interface ACL configured but ACL facts missing

### Firewall

Required forwarding and policy facts:

- `device_identity`
- `firewall_interface` or `interface`
- `interface_ip`
- `security_zone_binding`
- `route_table` or firewall snapshot routes
- `firewall_policy`
- `nat_rule`
- `address_object`
- `service_object`
- `policy_parser_diagnostic`

Optional but useful:

- `acl_rule`
- `pbr_rule`
- `topology_neighbor`
- `mac_table_entry`
- `arp_entry`

Blocking gaps:

- missing firewall route table for a reached VRF
- missing zone binding when policies are zone-based
- skipped policy parsing for a vendor/platform in scope
- skipped NAT parsing when NAT may apply
- unresolved address or service objects referenced by candidate rules

### Server

Required endpoint facts:

- `device_identity`
- `interface`
- `interface_ip`
- `server_route`

Optional:

- local firewall facts if collected later
- service listening facts if future application-edge diagnosis needs them

Blocking gaps:

- missing source endpoint interface when the flow starts at a server and ingress cannot be resolved.

## Snapshot Assembly Contract

The NetPath analysis snapshot should assemble from these source groups:

```text
DC2 latest facts
  device_identity
  interface
  interface_ip
  topology_neighbor
  route_table
  server_route
  acl_rule
  nat_rule
  pbr_rule
  address_object
  service_object
  policy_parser_diagnostic

Firewall config snapshots
  interfaces
  zones
  routes
  parsed policies
  parsed NAT
  parser diagnostics

Firewall business models
  firewall_security_zone
  firewall_network_segment
  firewall_zone_mapping
  firewall_zone_security_rule
```

Assembly outputs:

- devices
- interfaces with VRF and zone
- links
- route tables
- policy evidence
- NAT evidence
- PBR evidence
- object indexes
- diagnostics
- source references
- snapshot quality

The assembler must keep source references:

```text
fact_id
run_id
contract_key
dataset_key
processor_key
config_version_id
firewall_node_id
raw excerpt reference
```

## Quality Gate

### Ready

A snapshot can be `ready` only when:

- tenant and explicit device scope are present;
- every requested device has identity;
- ingress device and VRF have a route table;
- candidate firewall hops have zone bindings;
- policy/NAT/PBR parser diagnostics do not indicate skipped high-impact parsing for the candidate path;
- required object references can be resolved.

### Degraded

A snapshot is `degraded` when:

- topology peer resolution is incomplete but route evidence still explains the hop;
- optional MAC or ARP facts are missing;
- policy facts exist but some low-confidence non-candidate rules could not be normalized;
- a non-null route has an unresolved out-interface and the engine can still produce a useful diagnostic.

### Blocked

A snapshot is `blocked` when:

- ingress route table is missing;
- reached firewall device lacks required policy facts;
- NAT may apply and NAT facts were skipped or unsupported;
- PBR may override routing and PBR facts are unavailable;
- ACL or policy references unresolved address or service objects needed for a candidate decision;
- parser diagnostics are high severity for a phase needed by the flow;
- tenant or device scope is missing.

## Engine Evaluation Staging

Stage 1 evaluation:

- route lookup
- topology traversal
- null route and no-route disposition
- policy/NAT/PBR/ACL facts included as evidence and confidence gates

Stage 2 evaluation:

- interface ACL evaluator
- zone policy evaluator
- explicit deny and implicit deny dispositions

Stage 3 evaluation:

- NAT transformation evaluator
- PBR next-hop override evaluator
- object expansion and rule shadowing diagnostics

Stage 4 evaluation:

- vendor-specific advanced features such as virtual systems, rulebase inheritance, address-book hierarchy, service groups, application objects, and schedule matching.

## Implementation Entry Points

Recommended first implementation slice:

1. Integrate or verify `route_table` canonical facts in the main OneOPS worktree.
2. Extend the canonical fact contract with the policy fact registry in this document.
3. Extend `AnalysisSnapshot` to carry:
   - ACL evidence
   - NAT evidence
   - PBR evidence
   - address and service object indexes
   - parser diagnostics
4. Add provider tests where a firewall hop with missing policy facts becomes blocked.
5. Extend firewall config snapshot output to expose normalized policy and NAT rows, not only counts.
6. Add a first vendor fixture for H3C SecPath or Huawei USG, because existing firewall online collection already has command defaults for those platforms.

## Non-Goals

This phase does not require:

- full vendor coverage;
- real-time device collection against production firewalls;
- UI path rendering;
- ticket creation;
- complete NAT/PBR evaluator behavior in the engine;
- replacing existing firewall business models.

## Acceptance Tests

Minimum first-phase acceptance:

- route facts assemble into route tables with source references;
- firewall zone bindings assemble into interface zones;
- a firewall hop with policy parsing skipped becomes blocked;
- a firewall hop with NAT parsing skipped becomes blocked when NAT may apply;
- unresolved address or service objects block policy decisions;
- unsupported policy syntax is visible as a diagnostic;
- no path is marked confidently allowed when required policy facts are missing.

## Open Decisions

1. Whether parsed policy/NAT/PBR facts should be stored first in DC2 latest facts, firewall config snapshot rows, or both.
2. Whether business planning rules such as `firewall_zone_security_rule` should become canonical facts or stay as an application context reader.
3. Which vendor gets the first end-to-end parser fixture: H3C SecPath, Huawei USG, Fortinet, Cisco ASA, or Juniper SRX.
4. Whether the first policy evaluator should model interface ACLs or zone security policy first.
