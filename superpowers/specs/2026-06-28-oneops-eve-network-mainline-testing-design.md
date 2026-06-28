# OneOps EVE Network Mainline Testing Design

Date: 2026-06-28

## Purpose

Define the first stable OneOps-centered way to use the current EVE environment as a long-lived real-device testing factory.

This design is not about building a one-off lab. It is about turning EVE into a repeatable baseline that can continuously expose weak points in OneOps and drive improvements across collection, monitoring, and topology.

## User Original Goal

The user's testing target can be summarized as follows:

1. OneOps has accumulated a large amount of AI-assisted feature code, and that code now needs systematic sorting, testing, and validation.
2. Device collection and monitoring delivery need to be hardened so that device coverage keeps increasing, and every unsupported boundary is explicit.
3. Platform performance needs testing under large-scale data, large-scale queries, many agents, many monitoring tasks, many monitored targets, and large monitoring data volumes.
4. The immediate first phase should focus on testing, not broad feature expansion.
5. The testing method should be systematic, scenario-driven, and based on real devices and real topology combinations, not a few smoke scripts.

The user further clarified the first mainline direction:

1. Start from the network-device mainline.
2. Validate in the order: collection, then monitoring, then topology.
3. Expand support to more device types over time.
4. Use the EVE environment primarily to expose weak parts of OneOps and improve the platform.
5. Build topology with one device class and multiple devices first, including addressing and wiring rules.
6. The topology should include no fewer than 4 business network devices, 2 business servers, and 1 independent observation server.
7. Business servers must connect to switches.
8. The observation server should deploy `controller + agent`, and it should reuse the management plane rather than create a separate observation network.

## Scope

In scope for this design:

1. Define the first standard EVE scenario from the OneOps point of view.
2. Fix the topology structure for the first network-device mainline test.
3. Fix device ID rules, address allocation rules, and port-role rules.
4. Fix the validation order for collection, monitoring, and topology.
5. Fix a standard evidence receipt model so every run produces reusable improvement evidence.

Out of scope for this design:

1. Full platform performance pressure model for hundreds or thousands of devices.
2. A mixed first scenario containing routers, switches, firewalls, and all server classes at once.
3. Full automatic lab provisioning in this round.
4. Full firewall strategy generation and policy-query validation in this first mainline.
5. CI or automation orchestration implementation in this document.

## Approaches Considered

### 1. Single-device baseline first

Pros:

1. Simplest to control.
2. Fastest to isolate raw compatibility issues.

Cons:

1. Too weak for topology validation.
2. Too weak for exposing multi-device collection and monitoring weaknesses.
3. Cannot represent the user's real target.

This approach is useful as a prerequisite, but it is insufficient as the first OneOps mainline.

### 2. Network-device mainline with layered topology

Pros:

1. Best fit for the user's current priorities: collection, monitoring, topology.
2. Can expose weak points across interface facts, neighbor facts, route facts, task delivery, and topology inference in one shared scenario.
3. Scales naturally to more device types later.

Cons:

1. More design work up front.
2. Requires strict addressing and wiring conventions.

Recommendation:

Use this approach.

### 3. Fully mixed realistic environment from day one

Pros:

1. Looks closer to customer production environments.

Cons:

1. Failures become much harder to attribute.
2. Early weak-point analysis becomes noisy.
3. Slows the first feedback cycle.

This approach should be deferred until the network-device mainline is stable.

## Recommended Design

Use EVE as a OneOps real-device regression factory, with the first standard mainline fixed as a layered network scenario:

1. Management plane
2. Access plane
3. Routing plane

The observation server is not a separate network plane. It reuses the management plane so the first scenario stays small, stable, and easier to diagnose.

The first mainline should be built around:

1. 1 management gateway switch
2. 2 access switches
3. 4 business routing devices
4. 2 business servers
5. 1 observation server with `controller + agent`

This creates the first reusable OneOps-standard environment for finding problems in:

1. device adaptation
2. fact collection
3. monitor task delivery
4. agent execution
5. result return
6. topology inference

## Standard Scenario Architecture

### 1. Management plane

All device management interfaces and the observation server connect to the existing management gateway model and follow the `MGT` management rule.

Goal:

1. Keep management reachability stable.
2. Keep OneOps login and task-entry paths stable.
3. Avoid mixing management and business forwarding facts.

### 2. Access plane

Two access switches host the business servers and the access-facing interfaces of routing devices.

Goal:

1. Validate server access relationships.
2. Validate switch interface facts.
3. Validate L2/L3 fact stitching.

### 3. Routing plane

Four routing devices form the business interconnect.

Goal:

1. Validate interface collection.
2. Validate neighbor collection.
3. Validate route collection.
4. Validate OSPF-based topology inference.

## Topology Skeleton

The first standard scenario should follow this logical structure:

1. `GW` connects to `pnet0`.
2. `GW` connects to `ACC1` and `ACC2` for management reachability.
3. `GW` connects to the management interfaces of `R1`, `R2`, `R3`, `R4`, `S1`, `S2`, and `OBS`.
4. `ACC1` connects to `S1`, `R1`, and `R2`.
5. `ACC2` connects to `S2`, `R3`, and `R4`.
6. `R1`, `R2`, `R3`, and `R4` are fully interconnected at Layer 3.
7. `OBS` reaches all test targets through the management plane.

## Device Roles

### 1. Management gateway switch

Purpose:

1. Provide the unified management gateway.
2. Provide access toward `pnet0`.
3. Provide a stable management entry for all nodes.

### 2. Access switches

Purpose:

1. Carry business server access.
2. Provide switch-side facts for later collection and topology checks.
3. Separate access relationships from routing-plane relationships.

### 3. Business routing devices

Purpose:

1. Carry the main collection, monitoring, and topology test load.
2. Participate in dynamic routing.
3. Expose OneOps weak points under multi-device, multi-link conditions.

### 4. Business servers

Purpose:

1. Act as business endpoints.
2. Validate access-side relationships and business reachability context.
3. Serve as reference points when checking topology output against real design.

### 5. Observation server

Purpose:

1. Deploy `controller + agent`.
2. Verify OneOps task delivery and execution chains.
3. Help separate device-side failures from OneOps-side failures.

## Device ID Rule

The first standard scenario should be ID-driven.

Recommended device IDs:

1. `GW = 1`
2. `ACC1 = 10`
3. `ACC2 = 20`
4. `R1 = 31`
5. `R2 = 32`
6. `R3 = 33`
7. `R4 = 34`
8. `S1 = 61`
9. `S2 = 62`
10. `OBS = 71`

Design principle:

1. Device role is visible from the ID band.
2. IP addresses, hostnames, and later templates can all derive from the same ID.
3. The scheme stays stable when more devices are added later.

## Address Planning Rule

### 1. Management addresses

Management network:

`172.32.2.0/24`

Management gateway:

`172.32.2.254`

Rule:

The last octet of every management IP equals the device ID.

Examples:

1. `GW = 172.32.2.1`
2. `ACC1 = 172.32.2.10`
3. `ACC2 = 172.32.2.20`
4. `R1 = 172.32.2.31`
5. `R2 = 172.32.2.32`
6. `R3 = 172.32.2.33`
7. `R4 = 172.32.2.34`
8. `S1 = 172.32.2.61`
9. `S2 = 172.32.2.62`
10. `OBS = 172.32.2.71`

### 2. L3 interconnect addresses

Use `172.32.64.0/24` and above for routing-device interconnects.

Rule:

1. Each interconnect gets its own subnet.
2. Each side uses its device ID as the last octet.

Recommended first-round layout:

1. `R1 <-> R2`
   - `R1 = 172.32.64.31/24`
   - `R2 = 172.32.64.32/24`
2. `R1 <-> R3`
   - `R1 = 172.32.65.31/24`
   - `R3 = 172.32.65.33/24`
3. `R1 <-> R4`
   - `R1 = 172.32.66.31/24`
   - `R4 = 172.32.66.34/24`
4. `R2 <-> R3`
   - `R2 = 172.32.67.32/24`
   - `R3 = 172.32.67.33/24`
5. `R2 <-> R4`
   - `R2 = 172.32.68.32/24`
   - `R4 = 172.32.68.34/24`
6. `R3 <-> R4`
   - `R3 = 172.32.69.33/24`
   - `R4 = 172.32.69.34/24`

### 3. Business server addresses

Business server subnets should stay separate from the management network.

Rule:

1. Server IP last octet equals the server ID.
2. The gateway in each business subnet ends with `.254`.

Recommended first-round layout:

1. `S1`
   - subnet: `172.32.101.0/24`
   - IP: `172.32.101.61/24`
   - gateway: `172.32.101.254`
2. `S2`
   - subnet: `172.32.102.0/24`
   - IP: `172.32.102.62/24`
   - gateway: `172.32.102.254`

## Routing Topology Rule

The first routing-plane scenario should use full mesh between the four routing devices.

That means six L3 links:

1. `R1-R2`
2. `R1-R3`
3. `R1-R4`
4. `R2-R3`
5. `R2-R4`
6. `R3-R4`

Why this is recommended:

1. Collection complexity rises quickly, which helps expose missing interface, neighbor, and route facts.
2. Monitoring complexity rises quickly, which helps expose task-delivery and execution weaknesses.
3. Topology complexity rises quickly, which helps expose wrong-edge, missing-edge, and duplicate-edge problems.

## Interface and Wiring Rules

### 1. Common rules

1. The last interface of every business network device is reserved for management.
2. Management traffic and business traffic must not share the same interface.
3. Servers use one management-facing interface and one business-facing interface.
4. Access switches carry server access and routing-device access relationships.
5. Routing devices carry the main L3 mesh.

### 2. First-round port allocation

`GW`:

1. one port to `pnet0`
2. one port to `ACC1`
3. one port to `ACC2`
4. one port each to `R1`, `R2`, `R3`, `R4`
5. one port each to `S1`, `S2`, `OBS`

`ACC1`:

1. one port to `GW`
2. one port to `S1`
3. one port to `R1`
4. one port to `R2`

`ACC2`:

1. one port to `GW`
2. one port to `S2`
3. one port to `R3`
4. one port to `R4`

`R1`:

1. one access-facing port to `ACC1`
2. one port to `R2`
3. one port to `R3`
4. one port to `R4`
5. the last port to `GW` for management

`R2`:

1. one access-facing port to `ACC1`
2. one port to `R1`
3. one port to `R3`
4. one port to `R4`
5. the last port to `GW` for management

`R3`:

1. one access-facing port to `ACC2`
2. one port to `R1`
3. one port to `R2`
4. one port to `R4`
5. the last port to `GW` for management

`R4`:

1. one access-facing port to `ACC2`
2. one port to `R1`
3. one port to `R2`
4. one port to `R3`
5. the last port to `GW` for management

`S1`:

1. one management port to `GW`
2. one business port to `ACC1`

`S2`:

1. one management port to `GW`
2. one business port to `ACC2`

`OBS`:

1. one management port to `GW`

## Validation Order

The first mainline must validate in this order:

1. collection
2. monitoring
3. topology

This order is mandatory because topology is only meaningful when underlying collection facts are already trusted.

### 1. Collection first

The first phase should prove that OneOps can stably collect:

1. device identity
2. management reachability
3. interface inventory
4. interface state
5. neighbor facts
6. routing facts
7. server asset facts

Weak points to expose:

1. vendor adaptation gaps
2. inconsistent data modeling
3. unstable task execution
4. unclear unsupported boundaries

### 2. Monitoring second

Monitoring should only start once collection facts are stable enough.

Monitoring evidence must include four layers:

1. platform planning evidence
2. platform task evidence
3. agent runtime evidence
4. target result evidence

Weak points to expose:

1. task-delivery gaps
2. protocol-chain gaps
3. concurrency-chain gaps
4. unclear failure-state expression

### 3. Topology third

Topology validation should compare OneOps output against the actual EVE design, not just whether a graph exists.

Weak points to expose:

1. interface relationship gaps
2. adjacency inference gaps
3. L2/L3 stitching gaps
4. poor topology error explainability

## Standard Evidence Receipt

Every run of the first standard scenario should produce the same evidence structure.

### 1. Scenario definition

Record:

1. topology version
2. device list
3. device IDs
4. addressing plan
5. wiring plan
6. management and business interface role mapping

### 2. Initialization status

Record:

1. whether each device matches its standard initialization template
2. login baseline
3. management address
4. routing protocol state
5. interface-up state
6. server business addressing
7. observation server readiness

### 3. Collection receipt

Record per device:

1. onboarding result
2. identity collection result
3. interface collection result
4. neighbor collection result
5. route collection result
6. missing fields
7. explicit unsupported boundaries

### 4. Monitoring receipt

Record per task:

1. platform plan created or not
2. platform task delivered or not
3. agent executed or not
4. target returned valid data or not

### 5. Topology receipt

Record:

1. whether server-to-switch access relationships are correct
2. whether router-to-router relationships are correct
3. whether management facts were incorrectly mixed into business topology
4. whether missing, duplicate, or wrong edges exist

### 6. Weak-point analysis

Every run must state:

1. what weak points were exposed
2. whether the weak point belongs to device adaptation, task chain, data model, or topology inference
3. severity
4. customer-impact assessment

### 7. Fix recommendation

Every weak point should map to an action such as:

1. add device adaptation
2. add field mapping
3. strengthen task or agent tracing
4. improve topology inference rules
5. improve failure-state expression

### 8. Regression conclusion

Each run must end with one clear conclusion:

1. ready for next stage
2. fix required before continuing
3. boundary sample only, not a stable capability yet

## Why This Improves OneOps

This design changes the role of EVE from "a place where devices can boot" to "a factory that continuously produces OneOps improvement evidence."

Its main value is:

1. OneOps support becomes evidence-based instead of claim-based.
2. Collection, monitoring, and topology are validated in one shared real-device scenario.
3. Weak points become attributable rather than vague.
4. More device types can later be added onto the same test grammar.
5. Every future code change can be brought back to the same baseline for regression.

## Implementation Boundary For The Next Step

This design intentionally stops before implementation details such as:

1. exact EVE API orchestration code
2. exact OneOps task definitions
3. CI scheduling
4. large-scale performance replay

The next step after this design should be a written execution plan that breaks the work into:

1. standard topology construction
2. first collection baseline run
3. first monitoring baseline run
4. first topology baseline run
5. weak-point analysis and remediation loop
