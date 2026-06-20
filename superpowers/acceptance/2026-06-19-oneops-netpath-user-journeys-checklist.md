# OneOPS NetPath User Journeys Acceptance Checklist

Date: 2026-06-19

Source spec:

- `docs/superpowers/specs/2026-06-19-oneops-netpath-user-journeys-acceptance-design.md`

## Acceptance Rule

Mark an item complete only when the behavior is visible through OneOPS UI, API, stored data, logs, or tests. A backend-only capability without observable evidence is not accepted.

## Journey 1: Collect And Normalize Network Configuration

- [ ] User can start or schedule a collection task for a selected tenant, site, group, or device set.
- [ ] Collection task shows per-device status.
- [ ] Raw configuration or raw source reference is retained.
- [ ] Parsed interface facts are stored with source references.
- [ ] Parsed LLDP or topology link facts are stored with source references.
- [ ] Parsed VRF and route table facts are stored with source references.
- [ ] Parsed ACL, NAT, and security policy facts are stored or explicitly marked as unsupported with diagnostics.
- [ ] Parse errors show device, source section, parser reason, and confidence impact.

## Journey 2: Build A Network Analysis Snapshot

- [ ] User can build or select a snapshot from collection and config sources.
- [ ] Snapshot has stable `snapshot_id`, tenant, generated time, and source references.
- [ ] Snapshot quality summary shows device, link, route, policy, NAT, and diagnostic counts.
- [ ] Snapshot diagnostics identify missing routes, orphan links, duplicate interfaces, unknown peers, missing zones, or unresolved policy objects.
- [ ] Diagnostics distinguish blocking errors from warnings.
- [ ] Analysis run stores the exact snapshot used.

## Journey 3: Submit A Business Flow

- [ ] User can enter source IP, destination IP, protocol, ports, and optional business label.
- [ ] User can choose a snapshot or use the latest validated snapshot.
- [ ] System validates invalid IPs, missing destination, unsupported protocol, and ambiguous ingress.
- [ ] System resolves or asks for ingress device, interface, and VRF.
- [ ] Analysis run stores original input, normalized flow, snapshot ID, status, error message, and timestamps.
- [ ] Engine failures are stored as failed runs with readable errors.
- [ ] Same flow can be rerun against another snapshot as a separate run.

## Journey 4: Produce Explainable Trace

- [ ] Result includes terminal disposition.
- [ ] Result includes ordered hops with device, ingress interface, egress interface, zone, VRF, and sequence.
- [ ] Result includes per-hop steps for route lookup and available policy, NAT, ACL, neighbor, or diagnostic phases.
- [ ] Route hits include matched object, raw reference, and explanation when available.
- [ ] Policy hits include matched object, raw reference, and explanation when available.
- [ ] Unsupported phases produce diagnostics instead of silent allow decisions.
- [ ] Trace confidence reflects missing topology or unsupported policy parsing.

## Journey 5: Show Interactive Path View

- [ ] Path result page renders source, destination, devices, links, arrows, and terminal state.
- [ ] Device types are visually distinct.
- [ ] Selected path is highlighted.
- [ ] Unrelated topology is deemphasized or hidden.
- [ ] User can zoom and pan.
- [ ] User can select devices and links.
- [ ] Blocking or uncertain points are visually distinct.
- [ ] User can switch traces when multiple traces exist.

## Journey 6: Drill Into Device Evidence

- [ ] User can click a path device, hop, step, route hit, or policy hit.
- [ ] Evidence panel opens in the current flow context.
- [ ] Evidence panel shows matched route entries relevant to the flow.
- [ ] Evidence panel shows ACL, security policy, NAT, PBR, zones, interfaces, or object details when available.
- [ ] Evidence panel supports structured fields and raw config references.
- [ ] Each evidence item links back to the trace step that used it.
- [ ] Missing evidence is shown as a diagnostic with a reason.

## Journey 7: Locate Policy Blockers

- [ ] Denied or blocked result highlights blocker device.
- [ ] Blocker includes direction, interface or zone, policy phase, and rule reference when known.
- [ ] Explicit deny, implicit deny, unsupported policy, and missing policy data are distinguishable.
- [ ] Ordered policy steps remain visible when permit and deny decisions occur in sequence.
- [ ] User can copy or attach policy evidence to a ticket.

## Journey 8: Locate Route Or Topology Problems

- [ ] No-route result shows the device and VRF where route lookup failed.
- [ ] Null route is distinct from no route.
- [ ] Loop result shows repeated device and VRF state.
- [ ] Neighbor unreachable result explains missing topology, missing peer, or unresolved out interface.
- [ ] User can inspect route table evidence for the failing hop.
- [ ] User can inspect LLDP or topology peer evidence for the failing hop.

## Journey 9: Run Connectivity Probes

- [ ] Path analysis completion creates or enables a linked probe plan.
- [ ] Probe plan includes source-to-destination ping.
- [ ] Probe plan includes source-to-source-gateway ping.
- [ ] Probe plan includes source-to-destination-gateway ping.
- [ ] Probe plan includes destination-to-destination-gateway ping.
- [ ] Probe plan includes source-to-destination traceroute.
- [ ] Each probe item stores type, source, destination, executor, status, command, result, and error.
- [ ] Probe failures are shown separately from simulated trace disposition.
- [ ] UI can display source IP, destination IP, executor, command, latency, packet loss, hop output, error output, and timestamps.
- [ ] Traceroute can be compared with simulated hops when correlation data exists.

## Journey 10: Validate Before Or After Change

- [ ] User can save or reuse a flow for repeated analysis.
- [ ] User can rerun the same flow against a different snapshot.
- [ ] Result comparison shows disposition changed or unchanged.
- [ ] Path comparison identifies added, removed, or changed hops.
- [ ] Evidence comparison identifies changed route or policy hits when available.
- [ ] Before and after results can be referenced from a change or incident record.

## Journey 11: Create Ticket And Close Loop

- [ ] User can create a ticket or diagnostic record from a path result.
- [ ] Ticket payload includes run ID, snapshot ID, source, destination, protocol, port, disposition, path summary, blocker, evidence, and probe results.
- [ ] Ticket summary suggests likely owner: routing, firewall, topology, collection, or application edge.
- [ ] Ticket evidence links back to path view, device evidence, raw config references, and probe details.
- [ ] Re-analysis can be linked to the original ticket.
- [ ] Closure can include before and after disposition.

## MVP Release Gate

- [ ] At least one collection-to-snapshot path works with visible diagnostics.
- [ ] At least one source-to-destination flow creates a persisted analysis run.
- [ ] At least one route-aware trace includes hops, steps, and final disposition.
- [ ] At least one interactive path view supports route evidence drilldown.
- [ ] At least one post-analysis probe plan runs ping and traceroute items.
- [ ] Unsupported policy, PBR, NAT, or vendor parsing gaps appear as diagnostics.
- [ ] No path is marked allowed when required policy data is missing.

## Rejection Gate

Reject the release if any item below is true:

- [ ] Analysis result cannot be traced back to snapshot and collection source.
- [ ] UI shows only pass or fail without hops and evidence.
- [ ] Policy or topology gaps are silently ignored.
- [ ] Path direction is ambiguous.
- [ ] Probe results overwrite or confuse simulated trace results.
- [ ] Ticket payload lacks enough evidence for another team to act.
- [ ] Same flow cannot be rerun after configuration changes.
