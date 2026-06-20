# OneOPS NetPath User Journeys Acceptance Design

Date: 2026-06-19

## Purpose

This document turns the OneOPS NetPath product goals into user journeys that can be used as acceptance standards for design, implementation, demos, tests, and delivery reviews.

The journeys are not a feature checklist copied from the requirement text. They describe the operational path a user follows from network data collection to path analysis, visualization, diagnosis, probing, and ticket closure.

## Acceptance North Star

OneOPS NetPath is acceptable when an operator can answer these questions from inside OneOPS:

1. Which network data was collected, parsed, and used for this analysis?
2. What path would this business flow take from source to destination?
3. Which devices, interfaces, VRFs, zones, routes, policies, and transformations affected that path?
4. Where is the traffic allowed, denied, dropped, blackholed, missing route information, or uncertain?
5. What did active ping and traceroute probes observe compared with the simulated path?
6. What evidence should be attached to a ticket or change workflow?

## Personas

### Network Operator

Uses OneOPS to troubleshoot routing, topology, device, and interface problems. Cares about path continuity, route lookup, next-hop resolution, LLDP topology, and device health.

### Security Operator

Uses OneOPS to troubleshoot firewall, ACL, NAT, and security policy behavior. Cares about rule hits, object expansion, zones, policy phases, and deny or permit decisions.

### Application Operator

Uses OneOPS to validate business access from a source application or subnet to a destination service. Cares about whether access works and who should fix it when it does not.

### Platform Administrator

Maintains collection jobs, config versions, snapshot quality, task execution, permissions, and analysis reliability.

## Journey Map

```text
Collect configs and state
  -> Parse and normalize facts
  -> Build analysis snapshot
  -> Submit business flow
  -> Simulate forwarding path
  -> Render interactive path view
  -> Drill into route and policy evidence
  -> Run active probes
  -> Create ticket or change evidence
  -> Re-run and compare after remediation
```

## Journey 1: Collect And Normalize Network Configuration

### User Goal

The user wants OneOPS to ingest current network device configuration and operational data so later path analysis is based on known source data.

### Trigger

A platform administrator or network operator starts a collection task for a tenant, site, device group, or selected devices.

### User Steps

1. User selects the collection scope.
2. User starts or schedules the collection task.
3. OneOPS collects device configuration and state facts.
4. OneOPS parses LLDP, interfaces, VRFs, route tables, PBR, ACL, NAT, security policies, zones, address objects, and service objects when available.
5. OneOPS stores raw configuration, parsed facts, collection task metadata, and parse diagnostics.
6. User reviews device-level success, failure, and unsupported-data summaries.

### Acceptance Criteria

- The collection task exposes per-device status: pending, running, succeeded, failed, or partially parsed.
- Raw configuration is retained or linked for audit.
- Parsed facts are stored with device identity, tenant, collection run, and config version references.
- LLDP, interface, route, ACL, NAT, and security policy facts have separate structured records or equivalent typed fact groups.
- Parse failures show device, source section, parser reason, and whether path analysis can continue with degraded confidence.

### MVP Boundary

MVP must support at least interfaces, LLDP links, VRFs, route tables, and a minimal policy fact model. PBR, NAT, and vendor-specific firewall policy expansion may start as partial facts with explicit diagnostics.

## Journey 2: Build A Network Analysis Snapshot

### User Goal

The user wants a stable, versioned snapshot that can be used repeatedly for path analysis and evidence review.

### Trigger

A collection run completes, or a user selects a known set of config versions and topology data.

### User Steps

1. User selects or accepts a collection run as the snapshot source.
2. OneOPS builds a `Snapshot` from devices, interfaces, links, VRFs, route tables, policy facts, NAT facts, and diagnostics.
3. OneOPS validates snapshot completeness.
4. OneOPS records snapshot metadata and source references.
5. User opens the snapshot quality summary.

### Acceptance Criteria

- Snapshot has a stable `snapshot_id`, tenant, generated time, source config versions, topology snapshot, and collection runs.
- Snapshot quality summary shows device count, link count, route count, policy count, NAT count, and diagnostics count.
- Missing route tables, orphan links, duplicate interfaces, unknown peers, missing zones, and unresolved policy objects are visible diagnostics.
- Snapshot diagnostics distinguish blocking errors from warnings.
- A path analysis run records exactly which snapshot was used.

### MVP Boundary

MVP must build an engine-ready snapshot for route and topology analysis. Firewall and NAT facts may be included as diagnostic or policy stubs until the engine supports full evaluation.

## Journey 3: Submit A Business Flow For Path Analysis

### User Goal

The user wants to know whether a concrete business flow can reach its destination and what path it takes.

### Trigger

An application access test, incident, change validation, or troubleshooting request.

### User Steps

1. User enters source IP, destination IP, protocol, source port, destination port, and optional business label.
2. User selects tenant, network domain, or snapshot.
3. OneOPS resolves or asks for ingress device, interface, and VRF when they cannot be inferred.
4. User starts the analysis.
5. OneOPS records an analysis run and sends an `AnalyzeRequest` to the analysis engine.
6. User sees status transition from queued to running to succeeded or failed.

### Acceptance Criteria

- Required input validation catches invalid IPs, missing destination, unsupported protocol, and ambiguous ingress.
- User can choose a snapshot or use the latest validated snapshot.
- The analysis run stores original input, normalized flow, snapshot ID, status, error message, and timestamps.
- Engine errors are stored as failed runs instead of disappearing into logs.
- Re-running the same flow against a different snapshot creates a separate comparable run.

### MVP Boundary

MVP uses concrete single-flow analysis only. Range-based reachability, bulk matrix queries, and symbolic search are later work.

## Journey 4: Simulate Packet Forwarding And Produce Explainable Trace

### User Goal

The user wants OneOPS to explain the forwarding behavior, not only return pass or fail.

### Trigger

The analysis engine receives a valid snapshot and flow.

### System Steps

1. Engine starts at ingress device and VRF.
2. Engine evaluates ingress steps that are available in the snapshot.
3. Engine performs route lookup and next-hop or out-interface resolution.
4. Engine follows topology links to the next device.
5. Engine repeats until delivery, exit, deny, no route, null route, loop, neighbor unreachable, or insufficient information.
6. Engine returns `Trace -> Hop -> Step -> Disposition`.

### Acceptance Criteria

- Result includes ordered hops with device code, ingress interface, egress interface, zone, VRF, and sequence.
- Each hop includes route lookup, policy, NAT, ACL, neighbor, or diagnostic steps when known.
- Terminal disposition is explicit: delivered, accepted, denied, no route, null routed, loop, neighbor unreachable, insufficient info, or engine error.
- Policy and route hits include `matched_object`, raw reference, and message when available.
- Trace confidence reflects degraded inputs, such as missing topology or unsupported policy parsing.

### MVP Boundary

MVP must explain route lookup and topology traversal. Policy, ACL, PBR, and NAT evaluation can be phased in, but unsupported phases must appear as diagnostics rather than silent omissions.

## Journey 5: View Interactive End-To-End Path

### User Goal

The user wants a visual path that makes source, destination, direction, devices, and blockers clear at a glance.

### Trigger

A path analysis run succeeds or returns a partial trace with diagnostics.

### User Steps

1. User opens the path result page.
2. OneOPS renders the selected trace over a topology view.
3. User sees source, destination, flow direction arrows, devices, links, and terminal disposition.
4. User zooms, pans, highlights the path, and filters unrelated topology.
5. User identifies the device or link where the path stops or changes state.

### Acceptance Criteria

- Device types use distinct visual encoding for router, switch, firewall, load balancer, cloud gateway, endpoint, and unknown device.
- Flow direction is shown with arrows.
- The selected path is highlighted while unrelated topology is visually deemphasized.
- Terminal state is visible on the graph and in a summary panel.
- Users can zoom, pan, select devices, select links, and switch traces when multiple traces exist.
- Blocking or uncertain points are visually distinct from normal forwarding hops.

### MVP Boundary

MVP may render only the selected trace plus immediate neighboring context. Full global topology exploration can remain a broader topology module concern.

## Journey 6: Drill Into Device Evidence On The Current Path

### User Goal

The user wants to click any path device and see only the configuration evidence relevant to the current flow.

### Trigger

User clicks a device node, hop, step, route hit, or policy hit in the path result.

### User Steps

1. User selects a device in the path.
2. OneOPS opens a contextual evidence panel.
3. OneOPS shows matched route entries, ACL rules, security policies, NAT rules, PBR rules, zones, interfaces, and object details that affected this flow.
4. User switches between structured fields and raw config references.
5. User copies or attaches the evidence to a ticket.

### Acceptance Criteria

- Evidence is filtered by the current flow and path context, not dumped as the full device configuration.
- Route evidence includes destination prefix, next hop, out interface, protocol, metric or preference, and raw reference.
- Policy evidence includes rule name or ID, action, source, destination, service, zone, object expansion status, and raw reference.
- NAT evidence includes original and translated source or destination fields when known.
- Each evidence item links back to the trace step that used it.
- Missing evidence is shown as a diagnostic with a clear reason.

### MVP Boundary

MVP must support route evidence and basic policy/ACL evidence stubs with diagnostics. Full object-group expansion can be staged by vendor and platform.

## Journey 7: Locate Policy Blockers

### User Goal

The user wants to quickly determine whether a firewall, ACL, or security rule is blocking the flow.

### Trigger

The trace disposition is denied, dropped, or insufficient because of policy uncertainty.

### User Steps

1. User opens a denied or blocked path result.
2. OneOPS highlights the blocker device and policy phase.
3. User clicks the blocker.
4. OneOPS shows the matching deny rule, implicit deny, unsupported rule, or uncertain policy phase.
5. User reviews source, destination, service, zone, and object references.
6. User creates a firewall change or troubleshooting ticket with attached evidence.

### Acceptance Criteria

- Blocker location includes device, direction, interface or zone, policy phase, and rule reference when known.
- Explicit deny, implicit deny, unsupported policy, and missing policy data are distinguishable.
- If a permit rule is hit before a later deny, both steps are visible in order.
- Evidence can be attached to a ticket or copied as a diagnostic summary.

### MVP Boundary

MVP must identify policy-related blockers when policy facts are available. Where policy evaluation is unsupported, the system must report `insufficient_info` rather than claiming traffic is allowed.

## Journey 8: Locate Route Or Topology Problems

### User Goal

The user wants to understand route and topology failures without logging into every device.

### Trigger

The trace disposition is no route, null routed, loop, neighbor unreachable, or insufficient topology.

### User Steps

1. User opens the failed path.
2. OneOPS highlights the failing hop.
3. User opens the route and topology evidence for that hop.
4. OneOPS shows the relevant route table, selected longest-prefix match, next hop, out interface, and LLDP or topology peer.
5. User determines whether the problem is route missing, route wrong, null route, loop, missing LLDP, down interface, or unresolved next hop.

### Acceptance Criteria

- Route lookup explains matched or missing prefix.
- Null route is distinct from no route.
- Loop detection shows repeated device and VRF state.
- Neighbor unreachable explains whether the issue is missing topology, missing peer, or unresolved out interface.
- The user can see the route and topology evidence used by the engine.

### MVP Boundary

MVP must support no route, null route, directly connected delivery, topology next-hop traversal, loop, and neighbor unreachable dispositions.

## Journey 9: Run Connectivity Probes After Path Analysis

### User Goal

The user wants simulated path analysis and real network probing in one view.

### Trigger

A path analysis run reaches a final or partial disposition.

### User Steps

1. OneOPS generates a probe plan for the completed path analysis.
2. OneOPS triggers probes through the available executor.
3. System runs:
   - source to destination ping
   - source to source gateway ping
   - source to destination gateway ping
   - destination to destination gateway ping
   - source to destination traceroute
4. User sees probe status and results.
5. User hovers over or selects a probe route in the path view.
6. OneOPS shows source IP, destination IP, executor, command, latency, packet loss, hop output, error output, and timestamps.

### Acceptance Criteria

- Probe plan is linked to a path analysis run.
- Each probe item has type, source, destination, executor, status, command, result, and error fields.
- Probe failures do not invalidate the simulated trace; they are shown as separate observations.
- Traceroute results can be compared with simulated hops when device IPs can be correlated.
- The UI distinguishes simulated path, active probe route, and probe failure.

### MVP Boundary

MVP may execute probes through known source and destination executors only. Gateway inference may start with explicit gateway fields or best-effort inference with diagnostics.

## Journey 10: Validate Access Before Or After A Change

### User Goal

The user wants to simulate business access before a change and confirm it after remediation.

### Trigger

A planned application release, firewall change, routing change, or incident remediation.

### User Steps

1. User runs path analysis against the current or selected snapshot.
2. User reviews expected path and disposition.
3. User attaches result to a change or incident ticket.
4. After configuration changes, OneOPS collects new configuration.
5. User reruns the same flow against the new snapshot.
6. OneOPS compares old and new path, disposition, blockers, and probe results.

### Acceptance Criteria

- A saved flow can be rerun against another snapshot.
- Result comparison shows disposition changed or unchanged.
- Path comparison identifies added, removed, or changed hops.
- Evidence comparison identifies changed route or policy hits when available.
- Ticket or change record can reference both before and after results.

### MVP Boundary

MVP can start with manual rerun and side-by-side metadata. Automated diff of every hop and policy object can be phased in.

## Journey 11: Create Ticket And Close The Loop

### User Goal

The user wants diagnosis evidence to become actionable work, not remain a standalone analysis page.

### Trigger

The analysis identifies a blocker, uncertainty, route problem, probe failure, or change validation gap.

### User Steps

1. User creates a ticket from the path result.
2. OneOPS pre-fills source, destination, protocol, port, snapshot ID, disposition, path summary, blocker, key evidence, and probe results.
3. User assigns the ticket to network, firewall, platform, or application team.
4. Resolver changes configuration or requests more data.
5. OneOPS reruns analysis after new collection or on demand.
6. User closes the ticket when path and probe evidence confirm recovery.

### Acceptance Criteria

- Ticket payload includes run ID and source snapshot ID.
- Ticket summary identifies likely owner based on blocker type: routing, firewall, topology, collection, or application edge.
- Ticket evidence links back to path view, device evidence, raw config references, and probe details.
- Re-analysis can be linked to the original ticket.
- Closure can include before and after dispositions.

### MVP Boundary

MVP can create an internal OneOPS work item or structured diagnostic record before integrating with external ITSM.

## Cross-Journey Acceptance Matrix

| Capability | Must Be Visible To User | Must Be Stored | MVP Required |
| --- | --- | --- | --- |
| Collection status | per-device result | collection run, raw config ref, parse diagnostics | yes |
| Parsed facts | device/interface/route/policy summaries | typed facts with source refs | yes |
| Snapshot | quality summary | immutable snapshot source refs | yes |
| Flow input | normalized flow | request and run status | yes |
| Trace | path summary and graph | traces, hops, steps, disposition | yes |
| Route evidence | matched/missing route | route hit step and raw ref | yes |
| Policy evidence | permit/deny/unknown | policy hit step and raw ref | partial |
| NAT evidence | translation details | transformation step | later or partial |
| Probe | ping/traceroute result | probe plan and result | yes |
| Ticket | diagnosis payload | linked run, evidence, status | partial |

## MVP Acceptance Slice

The first shippable MVP should be judged by these five end-to-end journeys:

1. Collect configs and build a snapshot with visible diagnostics.
2. Submit a concrete source-to-destination flow and create an analysis run.
3. Produce a route-aware trace with hops, steps, and disposition.
4. Render the path and allow device-level evidence drilldown.
5. Generate and display post-analysis ping and traceroute probes.

This MVP can be accepted even if vendor-specific firewall rule evaluation and NAT transformation are partial, provided those gaps are explicit diagnostics and do not result in false allow decisions.

## Non-Acceptance Conditions

The capability should not be accepted if any of these are true:

- Analysis results cannot be traced back to a snapshot and collection source.
- The system shows a pass/fail result without explaining hops and evidence.
- Policy or topology gaps are silently ignored.
- UI path direction is ambiguous.
- Probe results overwrite or confuse simulated path results.
- Tickets cannot carry enough evidence for another team to act.
- Re-running after a config change cannot be compared with the original run.

## Relationship To Existing Designs

This document is the journey and acceptance layer above:

- `2026-06-18-oneops-netpath-platform-design.md`
- `2026-06-18-netpath-dc2-snapshot-builder-design.md`
- `2026-06-18-netpath-engine-runner-design.md`
- `2026-06-19-oneops-netpath-engine-port-design.md`
- `2026-06-19-oneops-netpath-sdk-adapter-design.md`

The existing designs define data models and integration seams. This document defines what a user must be able to accomplish for the capability to be considered complete.
