# IPAM MVP Launch Long Task Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the IPAM MVP from prototype screens to a coherent launchable workflow centered on address planning, allocation, release/reclaim, and audit.

**Architecture:** Treat existing `Prefix` as the authoritative subnet master data. Treat IPAM planning nodes as planning structure, address pools as allocatable ranges, IP address records as lifecycle resources, and request/audit records as workflow objects. Planning objects do not own approval state; only requests, IP lifecycle, and audit findings have workflow-like status.

**Tech Stack:** Vue 3, Ant Design Vue, OneOPS Go APIs, MySQL-backed IPAM models, existing smoke journey automation.

---

## Unified Product Decisions

- Address planning scheme and node are configuration/baseline data, not workflow data.
- IP allocation and release/reclaim are workflow data.
- Existing `Prefix` remains the subnet source of truth.
- `AddressPlanningNode` expresses hierarchy and intent; it must not silently replace `Prefix`.
- `AddressPool.prefix_code` must eventually point to a real Prefix, not only a planning node code.
- `releasing` is a meaningful IP lifecycle state and must remain.
- `reclaimed` should not be emphasized as a long-lived current state in the UI; the target state after reclaim is `available`.
- MVP request state should be user-facing as `submitted`, `completed`, `rejected`, `canceled`; `draft` and `approved` are internal or future states.
- MVP audit finding state should be user-facing as `open` and `resolved`; `acknowledged` and `ignored` can remain backend-compatible but should not lead the MVP UI.

## Field Lifecycle Baseline

### Planning scheme

- Keep: `code`, `name`, `root_cidr`, `description`.
- Hide or default: `owner_type`, `owner_code`.
- Remove from user-facing flow: `status`.

### Planning node

- Keep: `code`, `scheme_code`, `parent_code`, `name`, `cidr`, `region_code`, `site_code`, `business_unit_code`, `environment`, `security_zone_id`, `purpose`, `description`.
- Display-only: `level`.
- Remove from user-facing flow: `status`.

### Address pool

- Keep: `code`, `name`, `prefix_code`, `prefix_cidr`, `start_ip`, `end_ip`, `tenant_code`, `platform_vrf_code`, `security_zone_id`, `site_code`, `purpose`, `capacity_threshold`, `description`.
- Simplify: `allocation_policy` defaults to `first_available`.
- Keep as operational availability, not workflow: `status`.

### Reserved range

- Keep: `code`, `pool_code`, `prefix_code`, `prefix_cidr`, `start_ip`, `end_ip`, `reason`, `allow_special_allocation`, `description`.
- Lifecycle: existence means effective; deletion removes the reservation constraint.

### IP request

- Keep: `request_type`, `requester`, `owner_type`, `owner_code`, `tenant_code`, `site_code`, `security_zone_id`, `platform_vrf_code`, `pool_code`, `quantity`, `preferred_ip`, `allow_special_allocation`, `purpose`, `business_system`, `description`.
- MVP visible states: `submitted`, `completed`, `rejected`, `canceled`.
- Internal/future states: `draft`, `approved`.

### IP address lifecycle

- MVP visible states: `available`, `reserved`, `assigned`, `releasing`, `conflict`, `unknown`.
- Business rule: `releasing` blocks reallocation.
- Target after confirmed reclaim: `available`.

### Observed fact

- Keep as observation data, not workflow: `address`, `source_type`, `observed_status`, `device_*`, `mac_*`, `vrf_code`, `pool_code`, `prefix_code`, `security_zone_id`, `confidence`, `first_seen_at`, `last_seen_at`, `raw_data`.

### Audit finding

- Keep: `finding_type`, `severity`, `status`, `address`, `ip_address_code`, `prefix_code`, `pool_code`, `security_zone_id`, `device_code`, `device_interface_code`, `mac_code`, `suggested_action`, `first_detected_at`, `last_detected_at`.
- MVP visible states: `open`, `resolved`.

## Implementation Track

### Track 1: Frontend vocabulary and status cleanup

- [x] Remove planning scheme/node status fields from creation drawers.
- [x] Remove planning node status column from overview table.
- [x] Stop displaying planning status labels as workflow states.
- [x] Simplify request status copy in allocation/reclaim pages.
- [x] Adjust smoke to assert no planning draft status is shown.

### Track 2: Prefix and planning-node fusion

- [x] Audit current `AddressPool.prefix_code` behavior when creating a pool from planning node.
- [x] Add a clear UI label that distinguishes `规划节点` from `Prefix`.
- [x] Avoid silently storing a planning-node code as `prefix_code` once Prefix binding is available.
- [x] Decide and implement one MVP path: bind existing Prefix master data from the address-pool drawer, with clear guidance when Prefix data is missing.

### Track 3: Address pool and reserved range guardrails

- [x] Keep allocation policy fixed to `first_available` in MVP UI.
- [ ] Keep address pool status as operational enabled/disabled only.
- [x] Ensure reserved ranges block automatic allocation unless special allocation is allowed.
- [ ] Keep manual security-zone input until authoritative source is finalized.

### Track 4: Allocation request closure

- [x] Keep create request as immediate `submitted`.
- [x] Keep approve-and-allocate as completing the request.
- [x] Hide `draft` and `approved` as primary user-facing states.
- [x] Preserve allocated address display in request table.

### Track 5: Release and reclaim closure

- [x] Treat release as a business transition into `releasing`.
- [x] Treat reclaim confirmation as return to `available`.
- [ ] Avoid presenting `reclaimed` as a stable current state unless backend still returns it.
- [x] Add smoke coverage for release/reclaim page affordances.

### Track 6: Audit closure

- [ ] Keep manual fact upsert as MVP/testing entry.
- [ ] Keep generate finding and resolve finding as audit loop.
- [x] Prefer `open/resolved` in MVP UI.
- [x] Keep other audit statuses backend-compatible but lower priority.

## Acceptance Journeys

- Journey A: Planner creates a planning scheme and planning nodes without seeing planning approval states.
- Journey B: Planner creates an address pool and reserved range from planned address space.
- Journey C: Requester submits an IP allocation request and operator completes allocation.
- Journey D: Operator releases and reclaims an assigned IP with `releasing` treated as meaningful.
- Journey E: Operator records or receives observed facts, generates audit findings, and resolves them.
- Journey F: Operator uses statistics to understand pool utilization, lifecycle distribution, pending requests, and unresolved audit risk.

## Unified Long-Task Operating Mode

From this point forward, IPAM MVP work is handled as one continuous launch task
instead of multiple disconnected phases. The execution order is driven by the
operator journey, and each code change should strengthen at least one journey
checkpoint:

1. Planning baseline is understandable and has no approval-flow noise.
2. Prefix master data is clearly the source of truth for address-pool subnets.
3. Address pools and reserved ranges expose allocatable inventory safely.
4. Allocation request is operable from submit to completed result.
5. Release and reclaim preserve business meaning: release enters a blocked
   transition, reclaim confirmation returns the address to available inventory.
6. Observed facts and audit findings form a small closed loop from discovery to
   resolution.

The implementation principle is: planning scheme/node are planning baseline;
Prefix, address pool, IP address, request, release/reclaim, and audit finding
are operating objects. Journey smoke remains the shared acceptance mechanism.
