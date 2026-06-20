# OneOPS Fact Application Foundation Design

## Purpose

OneOPS currently has many requirements that start from collected facts and grow into upper-level applications, including L2 topology snapshot, IPAM address management, NetPath analysis, RCA, topology visualization, and future network operations agents.

This design records the shared foundation needed to keep those applications from each inventing its own fact model, identity rules, snapshot semantics, and quality language.

The guiding product position is:

```text
OneOPS = collected fact production line + fact governance layer + upper-level network applications
```

## Current Code Facts

These are observed facts from the current repository, not future assumptions.

### Obsflow Mainline Exists

Relevant code:

- `OneOPS/app/obsflow/domain/types.go`
- `OneOPS/app/obsflow/persistence/models.go`
- `OneOPS/app/obsflow/app/kernel_service.go`
- `OneOPS/app/obsflow/bridge/snapshot_apply_api.go`
- `OneOPS/app/obsflow/router/data_collect_compat.go`
- `OneOPS-UI/src/views/data_collection/CollectionRuns.vue`
- `OneOPS-UI/src/views/data_collection/ProcessingRuns.vue`
- `OneOPS-UI/src/views/data_collection/L2Snapshots.vue`

Current chain:

```text
collection_run
  -> observation_batch
  -> processing_run
  -> l2_topology_snapshot
  -> optional apply
```

The obsflow kernel already separates old HTTP/task aliases from the internal processing model. It validates batch inputs, starts a processing run, executes a registered task, saves a snapshot, and only then marks the run complete.

Current supported processing areas include:

- `DevicePorts`
- `L2nodeMapServer`
- `ArpMac` related apply path

### Device Collection 2 Canonical Facts Exist

Relevant code:

- `OneOPS/app/device_collection2/model/fact.go`
- `OneOPS/app/device_collection2/fact/types.go`
- `OneOPS/app/device_collection2/fact/interface_processor.go`
- `OneOPS/app/device_collection2/fact/interface_ip_processor.go`
- `OneOPS/app/device_collection2/fact/topology_processor.go`
- `OneOPS/app/device_collection2/api/device_collection2.go`

Current fact shape includes:

- `fact_type`
- `target_id`
- `identity_key`
- `fields`
- `quality`
- `provenance`
- `valid`
- `confidence`
- `observed_at`
- latest projection table
- issue table

Existing or partially implemented canonical fact processors include:

- `interface`
- `interface_ip`
- `topology_neighbor`
- `mac_table`
- device identity and server facts

This is the strongest candidate for the shared fact layer.

### IPAM Application Skeleton Is Substantial

Relevant code:

- `OneOPS/app/ipam/ipam_model/ip_address.go`
- `OneOPS/app/ipam/ipam_model/ip_address_fact.go`
- `OneOPS/app/ipam/ipam_model/ip_address_audit_finding.go`
- `OneOPS/app/ipam/service/impl/ip_address_request.go`
- `OneOPS/app/ipam/service/impl/ip_address_fact.go`
- `OneOPS/app/ipam/service/impl/ip_address_audit_finding.go`
- `OneOPS/app/ipam/service/impl/ipam_statistics.go`
- `OneOPS-UI/src/views/ipam/IPAMOverview.vue`
- `OneOPS-UI/src/views/ipam/IPAllocationFlow.vue`
- `OneOPS-UI/src/views/ipam/IPReclaimFlow.vue`
- `OneOPS-UI/src/views/ipam/IPFactAuditFlow.vue`

Current IPAM capabilities include:

- planned address records
- pools
- reserved ranges
- request, allocation, release, and reclaim flows
- observed IP facts
- audit findings
- statistics
- frontend work areas for overview, allocation, reclaim, and fact audit

Current risk: `ipam_address_fact` is useful as an application-facing fact index, but it is not yet clearly defined as a projection from shared canonical facts.

### NetPath Has Engine And Platform Skeleton

Relevant code:

- `oneops-netpath/pkg/netpath/netpath.go`
- `oneops-netpath/internal/engine/engine.go`
- `OneOPS/app/netpath/service/impl/netpath.go`
- `OneOPS/app/netpath/snapshot/builder.go`
- `OneOPS/app/netpath/snapshot/provider/types.go`
- `OneOPS/app/netpath/adapter/oneopsnetpath/adapter_sdk.go`

Current status:

- standalone deterministic path engine exists
- OneOPS has a service/API shape and engine port
- build-tagged SDK adapter exists
- DC2 preview snapshot builder exists

Current gaps:

- default OneOPS router registration is not yet complete
- service runs are in-memory by default
- route table canonical facts are not yet available as a production input
- analysis snapshot provider needs route, topology, interface, and policy evidence before it is engine-ready

### Topology Already Reads L2 Snapshot As A Source

Relevant code:

- `OneOPS/app/topology/service/impl/snapshot.go`
- `OneOPS/app/topology/service/impl/topology.go`
- `OneOPS/app/topology/api/topology.go`

Current topology service can read latest ready task snapshots and merge snapshot data with legacy topology, overlays, manual edges, and coordinates.

This makes L2 snapshot a real application bridge, not only a data table.

## Core Problem

The platform has enough raw data and enough application demand, but the applications are beginning to define facts independently.

If this continues, the same business entity will be represented differently across modules:

- device identity in Device V2, collection target, topology node, NetPath device, and IPAM observed device
- interface identity in DC2 facts, topology edges, IPAM facts, and NetPath links
- IP identity in IPAM records, interface facts, MAC/ARP tables, and path flows
- topology edge identity in L2 snapshot, manual edges, current topology UI, and NetPath links
- route identity in future route facts, NetPath route tables, and firewall config snapshots

The repeated failure mode will be:

- unknown source batch
- unknown freshness
- unknown confidence
- unknown publish state
- unknown entity identity
- unknown whether a result is fact, inference, projection, or application decision

## Design Direction

### Layer 1: Collection Layer

Sources:

- device collection 2
- obsflow collection run
- agent and Ansible tasks
- configuration backup
- firewall config parsing
- manual overlays and imports

Rule: this layer produces raw rows and raw payload references. It should not decide application semantics.

### Layer 2: Canonical Fact Layer

Shared canonical facts should live around the DC2 fact model.

Minimum common fact contract:

```text
fact_type
target_id
identity_key
fields
quality.valid
quality.confidence
quality.issues
provenance.contract_key
provenance.dataset_key
provenance.processor_key
provenance.source_fields
observed_at
run_id
latest projection
```

Initial shared fact types:

- `device_identity`
- `interface`
- `interface_ip`
- `topology_neighbor`
- `mac_table`
- `arp_entry`
- `route_table`
- `firewall_interface`
- `firewall_route`
- `firewall_policy`

### Layer 3: Snapshot And Projection Layer

Applications should not read random raw facts directly unless they are a fact browser. They should read one of:

- canonical latest facts
- explicitly selected observation batch
- processing run result
- published snapshot
- application projection generated from canonical facts

Examples:

- L2 topology reads `topology_neighbor` and publishes `l2_topology_snapshot`
- IPAM reads `interface_ip`, `mac_table`, and `arp_entry`, then updates `ipam_address_fact`
- NetPath reads `interface`, `interface_ip`, `topology_neighbor`, `route_table`, and firewall evidence to build an analysis snapshot

### Layer 4: Application Layer

Upper-level applications remain product-specific:

- L2 snapshot
- IPAM
- NetPath
- RCA
- topology visualization
- alert diagnosis
- network ops AI agent

Rule: product-specific state is allowed, but source facts, freshness, quality, and snapshot references must remain visible.

## Application Alignment

### L2 Snapshot

Role:

- reference implementation of the shared mainline
- proves batch, processing, snapshot, readiness, and apply semantics

Do next:

- keep tightening snapshot contracts for DevicePorts, L2nodeMapServer, and ArpMac
- make topology UI prefer ready snapshots with clear source and readiness display
- document every snapshot field that another application can consume

### IPAM

Role:

- first strong business application consuming facts
- planning and audit domain for addresses

Do next:

- define `ipam_address_fact` as a projection from canonical facts, not an unrelated fact model
- add a repeatable projection job from `interface_ip`, `mac_table`, and `arp_entry`
- keep request/allocation/reclaim workflow in IPAM
- keep audit findings application-specific, but keep source fact references

### NetPath

Role:

- analysis application over engine-ready snapshots
- higher-value reasoning layer after route facts are available

Do next:

- finish `route_table` canonical fact schema and processor
- build production snapshot provider from canonical facts
- persist analysis runs and trace results
- register router and add frontend only after backend run persistence is real

## Non-Goals

This foundation should not become a new generic data lake or graph platform in the first phase.

Out of scope for the first implementation wave:

- universal graph database migration
- broad symbolic reachability
- automatic fuzzy identity matching
- multi-domain cloud/application dependency model
- replacing existing IPAM workflow models
- replacing current topology UI

## Open Decisions

1. Whether `ipam_address_fact` remains a table owned by IPAM or becomes a thin projection table with source canonical fact refs.
2. Whether route facts enter through DC2 contracts first or a temporary import endpoint first.
3. Whether snapshot publication should get a generic table beyond `l2_topology_snapshot`, or whether each application keeps a typed snapshot table until reuse pressure is real.
4. How tenant scoping should be encoded in DC2 latest fact queries.
5. Which application gets the first full source-fact drilldown UI: IPAM audit or NetPath evidence.

## Success Criteria

The foundation is working when OneOPS can answer these questions for any upper-level result:

- which collection run produced the source facts
- which observation batch or latest fact set was consumed
- which processing run created the result
- whether the result is ready, degraded, blocked, or failed
- which canonical entity identities were used
- which facts were omitted and why
- which application projection or snapshot currently exposes the result

