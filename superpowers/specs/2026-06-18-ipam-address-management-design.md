# OneOPS IPAM Address Management Design

## Purpose

This design extends OneOPS IPAM around address management as the primary goal. It covers the bid requirement for enterprise-wide IP address planning, address statistics, automatic collection and audit, and IP request/reclaim workflows.

Topology visualization is explicitly out of this phase. IP current-network topology and IP end-to-end topology will be handled when the topology module is extended. This phase only prepares the data relationships that topology can later consume.

## Scope

### In Scope

- Enterprise-wide IP address planning.
- Address space hierarchy: aggregate, prefix/subnet, address pool, reserved range, IP address.
- IP address lifecycle management.
- IP address statistics by tenant, platform VRF, security zone, prefix, address pool, and status.
- IP request, reservation, allocation, release, reclaim, and audit trail.
- Automatic collection of observed IP facts from existing device/interface/MAC/IPAM aggregate data sources.
- Audit between planned IPAM data and observed network facts.
- Security zone association for address planning.
- Compatibility with existing platform VRF semantics.
- Lightweight context for device-local VRF and connectivity domain, only to clarify address boundaries and future network fact reconciliation.

### Out of Scope

- IP current-network topology diagram.
- IP end-to-end topology diagram.
- Full VPN orchestration.
- Full VRF management or route-target policy analysis.
- DNS/DHCP automation beyond interface and data-field reservation.
- Full workflow engine implementation if OneOPS already has a separate workflow module; this design defines the IPAM-side states and integration points.

## Requirement Mapping

### Enterprise-Wide IP Address Planning

OneOPS should support hierarchical address planning:

- Global or enterprise-level address blocks.
- Site/datacenter/tenant/security-zone address pools.
- Prefix/subnet planning.
- Reserved ranges for gateways, network devices, VIPs, NAT, DHCP excluded ranges, and future use.
- Single IP address records with lifecycle and ownership.

### IP Address Statistics

OneOPS should provide statistics across these dimensions:

- Enterprise-wide.
- Tenant.
- Platform VRF.
- Security zone.
- Site/datacenter.
- Prefix/subnet.
- Address pool.
- Status: available, reserved, assigned, releasing, reclaimed, conflict, unknown.
- Observed state: seen in network, not seen, stale, unmanaged.

### Automatic Collection and Audit

OneOPS should collect observed facts from existing and future sources:

- Device interface IP data.
- MAC and ARP-related data.
- Existing `IPAMAgg` data.
- Firewall zone mapping data.
- Future device configuration collection.

Audit should identify:

- Unregistered usage: observed IP has no IPAM record.
- Duplicate usage: same IP appears on more than one resource within the same effective boundary.
- Out-of-range usage: observed IP is outside the planned prefix or address pool.
- Planned but unused: assigned IP has not been observed for a configured period.
- Security-zone mismatch: interface/firewall zone and IPAM prefix zone disagree.
- MAC/interface drift: IP binding changed from the planned resource.
- Stale fact: observed record has not been refreshed within the configured window.

### IP Request and Reclaim Process

OneOPS should support:

- IP request by business/system/user.
- Pool selection by tenant, security zone, platform VRF, site/datacenter, and purpose.
- Automatic allocation from a valid pool.
- Manual address selection with strict validation.
- Reservation before final assignment.
- Binding to device/interface/MAC/application/owner.
- Release request.
- Reclaim with optional cooling period.
- Operation audit for every state transition.

## Existing Context

Current OneOPS already has these relevant pieces:

- `IPAddress`: address, MAC, prefix, platform VRF, tenant, status, description, device interface code.
- `Mac`: MAC records.
- `Prefix`: CIDR-like subnet with tenant and platform VRF.
- `Vrf`: existing platform VRF, currently tenant-oriented and idealized.
- `IPAMAgg`: aggregate view that connects IP, MAC, port, device, peer port, and peer device.
- `SecurityZone` and `NetworkSegment`: firewall planning objects. `NetworkSegment` already carries `cidr`, `gateway`, `vlan_id`, `prefix_code`, `vrf_code`, and `site_code`.

The design should reuse these concepts and avoid creating a parallel security-zone or VRF universe.

## Core Principle

IP address management is the center.

Tenant, platform VRF, connectivity domain, security zone, device interface, MAC, and device-local VRF are all context dimensions around addresses. They help define ownership, conflict boundaries, planning scope, and observed network facts, but they are not the main product scope of this phase.

## Conceptual Structure

```text
                     +--------------------------+
                     | Planning Context         |
                     | Tenant / Site / DC       |
                     | Platform VRF             |
                     | SecurityZone             |
                     +------------+-------------+
                                  |
                                  v
+--------------------+   +----------------------+   +--------------------+
| Network Fact        |   | IPAM Core            |   | Resource Fact       |
| DeviceLocalVRF      |-->| Prefix / Subnet      |<--| Device              |
| ConnectivityDomain  |   | AddressPool          |   | Interface           |
| VPN / RD / RT       |   | ReservedRange        |   | MAC                 |
+--------------------+   | IPAddress            |   | IPAMAgg             |
                         +----------+-----------+   | Firewall Mapping   |
                                    |               +--------------------+
                                    v
                         +----------------------+
                         | Address Capabilities |
                         | Lifecycle            |
                         | Allocation/Reclaim   |
                         | Audit/Statistics     |
                         +----------------------+
```

## Address Planning Workflow

```text
Demand input
  -> Address space planning
  -> Prefix and pool assignment
  -> IP request and allocation
  -> Implementation binding
  -> Collection and audit
  -> Capacity review and reclaim
  -> Back to planning
```

### Step 1: Demand Input

The requester provides:

- Business system or project.
- Tenant.
- Site/datacenter.
- Security zone.
- Purpose: server, network device, management, VIP, NAT, application, reserved, other.
- Required quantity or CIDR size.
- Expected usage period.
- Connectivity requirement.
- Optional preferred platform VRF or address pool.

### Step 2: Address Space Planning

Network planners create or select:

- Enterprise-level address block.
- Tenant/site/security-zone pool.
- Prefix/subnet.
- Reserved ranges.
- Gateway/DNS/VLAN metadata.
- Utilization threshold.

### Step 3: Prefix and Pool Assignment

OneOPS validates:

- CIDR syntax.
- Prefix is within the parent address block.
- Prefix does not overlap in the same effective boundary.
- Pool is within prefix.
- Reserved range is within prefix or pool.
- Gateway is within prefix and not allocatable as normal IP.
- Security zone and network segment relationship is consistent.

### Step 4: IP Request and Allocation

OneOPS supports two allocation modes:

- Automatic allocation: choose the next available address from a matching pool.
- Manual allocation: validate the requested address before reserving or assigning it.

Allocation checks:

- Address is syntactically valid.
- Address belongs to the chosen prefix or pool.
- Address is not in reserved range unless the request purpose allows it.
- Address is not already assigned in the same effective boundary.
- Address is not observed as occupied by a different resource.
- Address matches security zone constraints.

### Step 5: Implementation Binding

An allocated address can be bound to:

- Device.
- Device interface.
- MAC.
- Application or service.
- Owner or request record.

The binding should be visible in address detail and in aggregate queries.

### Step 6: Collection and Audit

Collection writes observed facts into an IP fact layer. The audit job compares facts with planned IPAM records and generates audit findings.

Audit findings should be actionable and include:

- Finding type.
- Severity.
- IP address.
- Planned prefix/pool/security zone.
- Observed device/interface/MAC.
- Suggested action.
- First seen and last seen time.
- Current status: open, acknowledged, ignored, resolved.

### Step 7: Capacity Review and Reclaim

Capacity review should calculate:

- Total usable addresses.
- Assigned addresses.
- Reserved addresses.
- Reclaiming addresses.
- Available addresses.
- Observed unmanaged addresses.
- Utilization percentage.
- Threshold status.

Reclaim flow:

```text
Release request
  -> Validate current binding
  -> Mark releasing
  -> Confirm not observed or wait for cooling period
  -> Remove binding
  -> Mark available
  -> Write audit event
```

## Proposed Domain Model

### AddressAggregate

Represents a large enterprise-level address block.

Suggested fields:

- `code`
- `name`
- `cidr`
- `ip_version`
- `description`
- `tenant_code` optional
- `site_code` optional
- `status`

This can be introduced later if current `Prefix` is sufficient for phase one. If not implemented immediately, reserve the concept in API and UI naming.

### Prefix

Existing `Prefix` remains the primary subnet model.

Additional recommended fields or associations:

- `security_zone_id` or relation through existing `NetworkSegment.PrefixCode`.
- `address_purpose`
- `gateway`
- `dns_servers`
- `vlan_id`
- `site_code`
- `capacity_threshold`
- `connectivity_domain_code` optional.

Existing `VrfCode` remains platform VRF.

### AddressPool

Represents a subset of a prefix from which addresses can be allocated.

Suggested fields:

- `code`
- `name`
- `prefix_code`
- `start_ip`
- `end_ip`
- `purpose`
- `tenant_code`
- `platform_vrf_code`
- `security_zone_id`
- `site_code`
- `allocation_policy`
- `capacity_threshold`
- `status`

### ReservedRange

Represents non-normal-allocatable addresses.

Suggested fields:

- `code`
- `prefix_code`
- `pool_code` optional
- `start_ip`
- `end_ip`
- `reason`
- `allow_special_allocation`
- `description`

### IPAddress

Existing `IPAddress` remains the main address record.

Recommended semantic additions:

- Keep existing `Status` if it means observed online/offline, but introduce a separate lifecycle field for IPAM status.
- Add lifecycle: `available`, `reserved`, `assigned`, `releasing`, `reclaimed`, `conflict`, `unknown`.
- Add `pool_code` optional.
- Add `request_code` optional.
- Add `owner_type` and `owner_code` optional.
- Add `security_zone_id` optional override.
- Add `last_seen_at` optional.
- Add `source`: manual, import, discovered, workflow.

If a single `Status` must be kept for compatibility, do not overload it. Add a new `LifecycleStatus` for IPAM lifecycle.

### IPAddressRequest

Represents IP request and reclaim process data.

Suggested fields:

- `code`
- `request_type`: allocate, reserve, release, reclaim.
- `requester`
- `tenant_code`
- `site_code`
- `security_zone_id`
- `platform_vrf_code`
- `pool_code`
- `quantity`
- `preferred_ip`
- `purpose`
- `business_system`
- `status`
- `approved_by`
- `approved_at`
- `completed_at`
- `description`

### IPAddressAudit

Records operation history.

Suggested fields:

- `code`
- `ip_address_code`
- `request_code` optional
- `action`
- `before_value`
- `after_value`
- `operator`
- `source`
- `created_at`
- `description`

### IPAddressFact

Represents observed current-network facts.

Suggested fields:

- `code`
- `ip_address`
- `ip_version`
- `device_code`
- `device_name`
- `interface_code`
- `interface_name`
- `mac_code`
- `mac_address`
- `platform_vrf_code` optional
- `device_local_vrf_code` optional
- `security_zone_id` optional
- `source`
- `first_seen_at`
- `last_seen_at`
- `confidence`
- `raw_ref`

### IPAddressAuditFinding

Represents audit result between planned data and observed facts.

Suggested fields:

- `code`
- `finding_type`
- `severity`
- `ip_address`
- `ip_address_code` optional
- `prefix_code` optional
- `pool_code` optional
- `security_zone_id` optional
- `observed_device_code` optional
- `observed_interface_code` optional
- `observed_mac_code` optional
- `status`
- `suggested_action`
- `first_detected_at`
- `last_detected_at`

## VRF, VPN, and Connectivity Semantics

Existing platform `VRF` remains unchanged.

It continues to serve the current OneOPS planning model and existing prefix/IP relationships. The design does not reinterpret it as a real device-local VRF.

### DeviceLocalVRF

Device-local VRF is a future or lightweight supporting concept:

- Unique by `device_code + local_vrf_name`.
- Stores observed device configuration facts.
- Can include `rd`, `import_rt`, `export_rt`, `source`, `last_seen_at`.

### ConnectivityDomain / VPN

Connectivity domain is a supporting boundary concept:

- Represents a real cross-device reachable domain.
- Can correspond to MPLS L3VPN, EVPN EVI, IPsec/SD-WAN VPN, or manually defined domain.
- Multiple device-local VRFs may map to one connectivity domain.

Phase one should not become a VPN/VRF management project. These concepts are only used to avoid wrong address-boundary assumptions and to prepare for future collection and topology.

## Security Zone Association

OneOPS should reuse existing firewall security-zone models:

- `firewall_security_zone`
- `firewall_network_segment`
- `firewall_zone_mapping`
- `firewall_zone_security_rule`

Recommended association:

- Prefix or address pool associates to security zone.
- IP address inherits security zone from its prefix or pool.
- IP address may override security zone only for special cases such as VIP, NAT, or temporary exception.
- Overrides must be audited.

This supports:

- Querying available addresses by security zone.
- Validating requests against zone-specific pools.
- Auditing firewall interface zone and IPAM prefix zone consistency.
- Supporting future security-policy planning.

## Statistics

Statistics should support these dimensions:

- Enterprise-wide.
- Tenant.
- Platform VRF.
- Security zone.
- Site/datacenter.
- Prefix.
- Address pool.
- Purpose.
- Lifecycle status.
- Observed status.

Key metrics:

- Total addresses.
- Usable addresses.
- Reserved addresses.
- Assigned addresses.
- Releasing addresses.
- Available addresses.
- Observed unmanaged addresses.
- Conflict count.
- Utilization percentage.
- Days since last seen.

## APIs

Exact routes should follow existing OneOPS conventions. Conceptually:

### Planning APIs

- Create/list/update/delete address pools.
- Create/list/update/delete reserved ranges.
- Bind prefix or pool to security zone.
- Query available addresses in a pool.

### Request APIs

- Create IP allocation request.
- Approve or reject request.
- Allocate automatically.
- Allocate manually.
- Release IP.
- Reclaim IP.

### Audit APIs

- Import or sync observed facts.
- Run audit for prefix, pool, security zone, tenant, or enterprise-wide address space.
- List audit findings.
- Acknowledge, ignore, or resolve finding.

### Statistics APIs

- Summary by tenant.
- Summary by platform VRF.
- Summary by security zone.
- Summary by prefix or address pool.
- Capacity threshold list.

## Validation Rules

Address planning validation:

- CIDR must be valid.
- Pool range must be inside prefix.
- Reserved range must be inside prefix or pool.
- Gateway must be inside prefix.
- Prefix cannot duplicate an existing prefix in the same platform VRF unless explicitly allowed as parent/child.
- Prefix overlap should be flagged when it crosses the same effective boundary.

Allocation validation:

- IP must belong to selected pool.
- IP must not be reserved unless request purpose allows special allocation.
- IP must not already be assigned in the same effective boundary.
- IP must not be observed as used by another resource.
- Requested security zone must match pool/prefix security zone.

Reclaim validation:

- IP must be assigned or reserved.
- Active bindings must be removed or explicitly transferred.
- If the IP is still observed in the network, reclaim should require forced override or remain in releasing state.

## Topology Preparation

This phase does not implement topology diagrams.

It should prepare data that future topology can consume:

- IP to interface.
- Interface to device.
- IP to MAC.
- Prefix to security zone.
- Prefix to platform VRF.
- Optional IP/prefix to connectivity domain.
- Observed fact source and timestamp.

Future topology expansion can use these relationships for:

- IP current-network topology.
- IP end-to-end topology.
- Path visualization through security zones and devices.

## Rollout Strategy

### Phase 1: Address Planning Foundation

- Add address pool and reserved range.
- Add lifecycle status separate from online/offline status.
- Associate prefix/pool with security zone.
- Add basic statistics.

### Phase 2: Request and Reclaim Workflow

- Add request model and APIs.
- Implement automatic allocation.
- Implement release and reclaim states.
- Add audit trail.

### Phase 3: Collection and Audit

- Add observed IP fact model.
- Sync facts from existing `IPAMAgg`, device interface, MAC, and firewall mapping data.
- Generate audit findings.
- Add audit finding operations.

### Phase 4: Topology-Ready Data Contract

- Stabilize relationship contract for topology module.
- Expose query APIs for IP/interface/device/MAC/security-zone relationships.
- Leave diagram rendering to topology expansion.

## Success Criteria

- A planner can create address pools and reserved ranges under enterprise/site/tenant/security-zone contexts.
- A requester can apply for an IP, and OneOPS can allocate a valid available address.
- A released IP can be reclaimed with audit history.
- An operator can see address utilization by tenant, platform VRF, security zone, prefix, and pool.
- OneOPS can compare observed facts against planned records and produce audit findings.
- Existing platform VRF behavior remains compatible.
- Existing security-zone data is reused instead of duplicated.
- Topology diagrams remain out of phase-one implementation but have sufficient relationship data prepared.

## Open Decisions

- Whether `AddressAggregate` is implemented as a new table in phase one or represented by parent prefixes.
- Whether existing `IPAddress.Status` continues to represent observed online/offline state while a new `LifecycleStatus` represents IPAM lifecycle.
- Which existing workflow module, if any, should own approval mechanics for IP request and reclaim.
- Whether security zone association is stored directly on `Prefix`/`AddressPool`, or primarily through existing `firewall_network_segment.prefix_code`.
