# OneOPS NetPath Platform Design

Date: 2026-06-18

## Purpose

OneOPS should add a network path analysis capability that can explain how business traffic moves through the current network, where it is allowed, translated, denied, dropped, or becomes uncertain.

The work is split into two cooperating products:

1. `oneops-netpath`: an independent Go analysis engine.
2. OneOPS platform integration: collection, snapshot generation, result persistence, topology visualization, probing, and ticket workflow.

This design intentionally references Batfish concepts, but does not clone Batfish. Batfish is used as an architecture reference for snapshots, flows, FIB lookup, traceroute-style hop/step output, dispositions, and packet transformations. The MVP avoids symbolic analysis, BDD reachability, dynamic routing convergence, and a broad question framework.

## Product Boundary

### oneops-netpath

`oneops-netpath` owns deterministic packet simulation over a prepared network snapshot.

It accepts a snapshot and a concrete business flow, then returns one or more traces. Each trace contains ordered hops, per-hop steps, matched routes, transformations, policy hits, diagnostics, and a final disposition.

It does not connect to the OneOPS database, call production devices, manage credentials, create tickets, or render UI.

### OneOPS

OneOPS owns the operational workflow around the engine.

It builds snapshots from existing assets, configuration versions, topology, collection task outputs, firewall data, and optional manual overlays. It starts path analysis runs, persists results, displays interactive path views, triggers probes, and connects blockers to firewall/configuration/ticket workflows.

OneOPS remains the source of truth for asset identity, configuration versions, task execution, topology coordinates, device detail, and user-facing audit.

## Referenced Current Capabilities

OneOPS already has foundations that should be reused:

- Config version lifecycle and config management APIs.
- Device V2 asset identity, vendor, model, management IP, and task entry points.
- Topology nodes, edges, snapshots, overlays, manual edges, Cytoscape UI.
- L3 nodemap policy query DTOs and firewall object relation display.
- Firewall policy validation and firewall planning modules.
- ctrlhub/controller firewall v2 semantic/runtime model.
- Task center and agent/Ansible collection mechanisms.

Batfish reference concepts:

- `Flow`: concrete packet header and start location.
- `Fib`: longest-prefix lookup over forwarding entries.
- `Trace`, `Hop`, `Step`: explainable per-hop forwarding path.
- `FlowDisposition`: accepted, no route, denied, loop, null route, insufficient info.
- `Transformation`: NAT or packet header mutation.
- `traceroute` question: concrete flow path debugging rather than exhaustive symbolic reachability.

## Core Data Model

### Snapshot

A snapshot is the immutable input to `oneops-netpath`.

Required fields:

- `snapshot_id`
- `tenant_code`
- `generated_at`
- `source_versions`: config versions, topology snapshot, collection run codes
- `devices`
- `links`
- `diagnostics`

Snapshot generation belongs to OneOPS. Snapshot evaluation belongs to `oneops-netpath`.

### Device

Device fields:

- `device_code`
- `device_name`
- `device_type`: router, switch, firewall, load_balancer, server, virtual
- `vendor`
- `model`
- `management_ip`
- `vrfs`
- `interfaces`
- `route_tables`
- `acl_sets`
- `pbr_policies`
- `firewall_model_ref`
- `metadata`

MVP requires routers, switches, and firewalls. Servers may be represented as endpoint stubs when they do not have full routing data.

### Interface

Interface fields:

- `interface_code`
- `interface_name`
- `vrf`
- `zone`
- `ipv4_addresses`
- `status`
- `peer_device_code`
- `peer_interface_code`
- `source`: lldp, cdp, manual, topology_snapshot, config

### Route

Route fields:

- `vrf`
- `destination`
- `next_hop_ip`
- `out_interface`
- `protocol`: connected, static, ospf, bgp, unknown
- `metric`
- `preference`
- `null_route`
- `raw`

MVP treats collected route tables as already converged forwarding facts. Dynamic routing protocol convergence is out of scope.

### Flow

Flow fields:

- `src_ip`
- `dst_ip`
- `protocol`
- `src_port`
- `dst_port`
- `ingress_device_code`
- `ingress_interface_code`
- `ingress_vrf`
- `business_label`

Flow is concrete. Range-based reachability and symbolic flow search are later work.

### Trace

Trace fields:

- `trace_id`
- `flow`
- `disposition`
- `hops`
- `diagnostics`
- `confidence`

Dispositions:

- `accepted`
- `delivered_to_subnet`
- `exits_network`
- `denied_in`
- `denied_out`
- `no_route`
- `null_routed`
- `loop`
- `neighbor_unreachable`
- `insufficient_info`
- `engine_error`

### Hop

Hop fields:

- `sequence`
- `device_code`
- `in_interface`
- `out_interface`
- `in_zone`
- `out_zone`
- `vrf`
- `steps`

### Step

Step types:

- `enter_interface`
- `ingress_acl`
- `pre_routing_nat`
- `pbr`
- `route_lookup`
- `security_policy`
- `post_routing_nat`
- `egress_acl`
- `exit_interface`
- `neighbor_resolution`
- `final_disposition`
- `diagnostic`

Every step should carry `action`, `matched_object`, `raw_ref`, and `message` when available.

### PolicyHit

Policy hit fields:

- `device_code`
- `phase`: ingress_acl, security_policy, egress_acl, pre_routing_nat, post_routing_nat, pbr
- `rule_name`
- `rule_id`
- `action`
- `source`
- `destination`
- `service`
- `raw_cli`
- `config_version_id`
- `line_numbers`

### ProbePlan And ProbeResult

Probe execution is platform-owned, not engine-owned.

`ProbePlan` fields:

- `path_analysis_run_id`
- `items`

Probe item fields:

- `probe_type`
- `executor_type`
- `executor_id`
- `src_ip`
- `dst_ip`
- `preferred_command`
- `fallback_commands`
- `reason`

Probe types:

- `source_to_destination_ping`
- `source_to_source_gateway_ping`
- `source_to_destination_gateway_ping`
- `destination_to_destination_gateway_ping`
- `source_to_destination_traceroute`

`ProbeResult` fields:

- `probe_type`
- `executor_type`
- `executor_id`
- `status`
- `latency_ms`
- `packet_loss`
- `hops`
- `raw_output`
- `started_at`
- `finished_at`
- `diagnostics`

MVP supports Linux agent execution. Network device CLI, firewall CLI, and Windows execution are P1.

## oneops-netpath Architecture

### Packages

Recommended structure:

```text
cmd/netpathctl
cmd/netpathd
internal/model
internal/snapshot
internal/topology
internal/routing
internal/policy
internal/firewall
internal/engine
internal/explain
internal/adapters/oneops
internal/adapters/ctrlhub
api
testdata
```

### Engine Flow

The engine evaluates a flow as:

1. Resolve start device, ingress VRF, and optional ingress interface.
2. Enter hop.
3. Apply ingress ACL if present.
4. Apply pre-routing NAT if the device has firewall semantics.
5. Apply PBR if present.
6. Perform route lookup by longest-prefix match.
7. Apply security policy and egress ACL when applicable.
8. Apply post-routing NAT when applicable.
9. Resolve next device through topology/link/IP ownership.
10. Detect loop using `(device, vrf, ingress interface, flow headers)`.
11. Continue until accepted, exits network, no route, denied, loop, or insufficient information.

MVP may initially evaluate firewall policy before or after route lookup according to each firewall adapter's declared pipeline. The trace must expose the chosen phase order.

### Firewall Integration

`oneops-netpath` should not duplicate all ctrlhub firewall v2 logic.

The preferred initial approach is an adapter boundary:

- OneOPS snapshot includes firewall semantic model JSON, or
- `oneops-netpath` imports a small, copied compatibility model derived from ctrlhub v2 semantic structures.

The adapter must preserve:

- policy order
- NAT stage
- zones
- address/service object references
- diagnostics and skipped runtime rules
- raw CLI references where possible

Direct dependency on the whole ctrlhub/controller tree is not recommended for MVP because it would make the independent engine heavy and hard to version.

## OneOPS Platform Architecture

### Backend Modules

New backend module:

```text
OneOPS/app/netpath
```

Suggested subpackages:

```text
api
dto
model
service
service/impl
router
adapter
```

Responsibilities:

- Build snapshot payloads from OneOPS data.
- Call `oneops-netpath` through HTTP or local CLI in development mode.
- Persist path analysis runs and results.
- Generate probe plans after analysis.
- Trigger probe tasks through task center or agent execution.
- Join result details with config versions, firewall modules, and topology metadata.

### Backend Data Objects

Recommended persistent entities:

- `netpath_snapshot`
- `netpath_analysis_run`
- `netpath_trace`
- `netpath_hop`
- `netpath_step`
- `netpath_policy_hit`
- `netpath_probe_plan`
- `netpath_probe_result`

MVP can store `trace_json` and `probe_json` first, with selected indexed fields:

- run code
- tenant
- src IP
- dst IP
- protocol
- dst port
- disposition
- blocker device
- blocker phase
- snapshot id
- created by
- created at

Normalize hop/step tables in P1 once query needs are proven.

### Backend APIs

MVP APIs:

```text
POST /netpath/snapshots/preview
POST /netpath/snapshots
POST /netpath/analysis-runs
GET  /netpath/analysis-runs
GET  /netpath/analysis-runs/:code
POST /netpath/analysis-runs/:code/probes
GET  /netpath/analysis-runs/:code/probes
```

P1 APIs:

```text
GET /netpath/analysis-runs/:code/topology
GET /netpath/analysis-runs/:code/hops/:hop_id/config-context
POST /netpath/analysis-runs/:code/tickets
POST /netpath/analysis-runs/:code/recalculate
```

### Frontend

New page:

```text
OneOPS-UI/src/views/netpath/NetPathAnalysis.vue
```

Recommended UI areas:

1. Query panel: source, destination, protocol, port, start device, VRF, snapshot.
2. Result summary: disposition, confidence, blocker, elapsed time, snapshot versions.
3. Topology path view: reuse existing Cytoscape topology component with path overlay support.
4. Hop list: ordered device/interface/policy/NAT steps.
5. Detail drawer: route, ACL, NAT, firewall policy, raw config, diagnostics.
6. Probe panel: ping/traceroute plan and execution results.
7. History list: previous analyses and filters.

The current topology component should be extended through props rather than forked:

- `highlightNodes`
- `highlightEdges`
- `directedEdges`
- `pathEdgeStates`
- `nodeBadges`
- `edgeBadges`

## Probe Orchestrator Design

Probe Orchestrator starts only after a path analysis run reaches a terminal state.

It should never execute arbitrary user-provided shell. It generates commands from safe templates.

Executor selection order:

1. Managed source host agent.
2. Source gateway or same-subnet network device.
3. Managed destination host agent for destination-side probes.
4. Destination gateway device.
5. Controller-local fallback, marked as non-source-representative.

MVP command templates:

Linux:

```text
ping -c 4 -W 2 <target>
traceroute -n -w 2 -q 1 <target>
tracepath -n <target>
```

Probe results must be labeled as observation evidence, not truth. ICMP and traceroute may be filtered even when business TCP/UDP is allowed.

## Phased Roadmap

### MVP

Scope:

- Standalone `oneops-netpath` Go skeleton.
- Snapshot JSON schema.
- Static/connected/default route lookup.
- Basic topology next-hop resolution.
- Loop/no-route/neighbor-missing dispositions.
- Trace/Hop/Step JSON output.
- Minimal OneOPS backend netpath module with snapshot preview and run creation.
- Store result JSON.
- No production probing by default.

Acceptance:

- A small test snapshot can produce an explainable path.
- A no-route case returns `no_route` with matched context.
- A loop case returns `loop`.
- OneOPS can call the engine and retrieve the stored run detail.

### P1

Scope:

- Firewall policy/NAT adapter from ctrlhub v2 semantic model.
- Path topology visualization in OneOPS UI.
- Hop detail drawer.
- Linux agent probe execution.
- Config version linkage.
- Selected vendor coverage: choose two first, such as SecPath and USG, or Forti and SecPath.

Acceptance:

- A path through a firewall shows pre-NAT, security policy, post-NAT, and final verdict.
- UI highlights the path and blocker.
- Probe results are visible beside the simulated path.

### P2

Scope:

- Network device CLI probes.
- Windows probes.
- Batch business flow analysis.
- Ticket creation from blocker.
- Change-before/after analysis using two snapshots.
- Confidence scoring and unsupported syntax risk rollup.

Acceptance:

- Operators can compare simulated and observed paths.
- A policy blocker can create or link a firewall ticket.
- Snapshot diff can show changed path or changed blocker.

## Risks

- Vendor configuration parsing is uneven. Unsupported syntax must be visible.
- NAT can change the next-hop lookup target. Trace must preserve pre/post NAT flow state.
- Topology may be incomplete. Missing neighbor resolution must not be hidden.
- Probe results may not match business connectivity because ICMP/traceroute behavior differs from TCP/UDP.
- Large ECMP path sets can explode. MVP should cap trace count and expose truncation.
- Directly importing ctrlhub packages into `oneops-netpath` may couple release cycles too tightly.

## Reporting Format For Long Execution

Every implementation turn should end with this compact status block:

```text
【本轮状态】
基于的数据模型：
- <this turn's models/contracts>

完成的工作：
- <files/features/tests completed>

验证：
- <commands and result>

下一步：
- <one next action>
```

This keeps the long-running work reviewable and allows the owner to correct the direction before the implementation drifts.

## Open Decisions

1. First supported firewall vendors for P1.
2. Whether OneOPS calls `oneops-netpath` over HTTP only, or allows local CLI mode for quick env.
3. Whether MVP stores only trace JSON or creates normalized hop/step tables immediately.
4. Whether the first probe executor is an existing Agent task template or a new lightweight probe task type.

## Recommendation

Proceed with the independent-engine architecture.

Start with `oneops-netpath` MVP and a thin OneOPS integration. Keep the first engine snapshot JSON small and explicit. Add firewall and probe integration only after trace/routing/topology basics are stable.
