# SNMP Definition-Layer Vs Runtime-Layer Closure Correction Plan

Date: 2026-06-14

## Goal

This plan corrects the current working direction for the SNMP dashboard-family effort.

The immediate objective is not to add more by-target runtime hardening.
The immediate objective is to restore the correct primary axis:

```text
definition-layer closure
vs
runtime-layer closure
```

The current codebase already contains meaningful runtime closure work:

- by-target panel support preview
- by-target recording rule preview
- by-target recording rule materialization
- explicit by-target recording rule publish
- flat by-target Grafana save / save+sync
- tree-pilot by-target dry-run / save / replay

That runtime work is real and should not be discarded.
But it must not be mistaken for completion of the dashboard-family business model.

This plan defines:

- the boundary between definition-layer and runtime-layer closure;
- the current deviation;
- the correction sequence;
- what work should temporarily stop.

The current simplified generation rule is now also captured in:

- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-class-baseline-generation-rule.md`

## Current Milestone

As of 2026-06-14:

- the current switch line is no longer the only baseline model;
- SNMP dashboard generation now has an explicit generic target-class floor:
  - `snmp.generic`
  - `switch.current`
  - `switch.routing_capable`
- the current active switch dashboard-tree family denominator can now be treated as closed;
- interface, system, hardware-detail, topology-evidence, and root-summary families all have an explicit current owner baseline;
- future routing families (`l3_route_table.*`, `routing_bgp.*`, `routing_ospf.*`) are now treated as a separate future-scope track, not part of the current closure denominator.
- dashboard generation and runtime monitoring are now treated as different stages:
  - generation decides what families exist in a class-level baseline;
  - runtime only decides what state those panels currently show.

## Boundary Diagram

The system should be understood as two connected but different closure loops.

### 1. Definition Layer

This layer exists before any target device is selected.

Canonical flow:

```text
StrategySet
  -> StrategyTree
    -> Dashboard Logical Tree
      -> DashboardFamily / DashboardVariant / Panel Ownership
```

This layer answers:

- what root dashboard exists for a strategy set;
- what strategy dashboards exist for strategy nodes;
- how parent/child strategy relationships map to parent/child dashboards;
- which panels belong to which strategy node;
- which parts are business hierarchy vs template inheritance.

Important rule:

- this layer must not depend on `target_part` as its primary identity.
- this layer must not use runtime data presence as a gate for whether a family exists.

### 2. Runtime Layer

This layer begins only after a concrete target is selected.

Canonical flow:

```text
(strategy_set_id, target_part)
  -> target-scoped contract resolution
  -> recording rule preview / materialization / publish
  -> dashboard instance materialization / save / sync
```

This layer answers:

- what concrete target is being rendered or published;
- what rule YAML is generated for that target;
- what dashboard instances are created or updated for that target;
- what publish / save status exists for that target.

Important rule:

- this layer may depend on `target_part`;
- but it must consume a prior definition-layer model instead of replacing it.
- it may affect panel state, but not baseline family existence.

### 3. Correct Connection Between The Two Layers

The intended relationship is:

```text
definition-layer model
  -> runtime-layer materialization
```

not:

```text
target-scoped runtime path
  -> becomes the definition model
```

and also not:

```text
runtime data presence
  -> decides whether a panel family exists
```

That inversion is the core deviation to correct.

## Current State Classification

Current project assets should be classified as follows.

### 1. Already In Definition Layer

- the long-path business intent in
  `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`
- the original dashboard-family design direction in
  `/OneOPS/docs/superpowers/specs/2026-06-10-snmp-metric-groups-dashboard-family-design.md`
- the strategy-tree to dashboard-tree mapping spec in
  `/OneOPS/docs/superpowers/specs/2026-06-13-strategy-tree-dashboard-tree-mapping-design.md`
- the current-mechanism issue analysis in
  `/OneOPS/docs/superpowers/specs/2026-06-13-strategy-dashboard-current-mechanism-issues.md`
- the tree pilot concept that preserves:
  - `root` dashboard node
  - `strategy` dashboard node
  - parent/child dashboard links

### 2. Already In Runtime Layer

- strict by-target panel support preview
- strict by-target recording rule preview
- strict by-target recording rule materialization dry-run
- explicit by-target recording rule publish lifecycle
- flat by-target dashboard save / save+sync
- by-target recording-rule readiness and version matching
- tree-pilot dry-run / save / save-summary replay

### 3. Current Structural Gap

There is still no fully explicit, first-class, target-independent definition model for:

- root dashboard definition;
- strategy dashboard definition;
- panel ownership per strategy node;
- the exact mapping from StrategyTree node to Dashboard Logical Tree node.

This means current runtime work still consumes either:

- flattened `effective_contract`, or
- a bounded pilot reconstruction of tree structure,

instead of a settled definition-layer source of truth.

## Current Deviation

The current deviation is not that runtime work exists.
The deviation is that runtime closure has become the operational center of gravity.

In practical terms, the recent work drifted toward:

```text
strategy_set_id + target_part
  -> publish correctness
  -> save correctness
  -> readiness correctness
```

This created three risks.

### 1. Runtime Closure Can Be Mistaken For Product Closure

The system may look “closed” because:

- rules can publish;
- dashboards can save;
- readiness can gate save actions.

But that still does not answer:

- what a root dashboard definition is;
- what a strategy dashboard definition is;
- how dashboard ownership follows strategy nodes.

### 2. `target_part` Can Start Driving The Wrong Layer

When more and more behavior is expressed as:

```text
strategy_set_id + target_part + dashboard_variant
```

the risk is that the runtime identity becomes the de facto business identity.

That is the opposite of the intended model.

The intended business identity should remain:

- `strategy_set_id` for root dashboard ownership;
- `strategy_id` for strategy dashboard ownership.

### 3. More Runtime Hardening Has Diminishing Value Right Now

Additional work such as:

- more readiness states,
- more save guards,
- more same-target protections,
- more pilot interaction polish,

can improve safety,
but they do not reduce the central business-model ambiguity.

## Correction Principle

The correction is not to remove runtime work.

The correction is:

1. freeze additional runtime closure expansion;
2. re-center on definition-layer closure;
3. treat runtime paths as consumers of the definition-layer model.

## Correction Plan

The next work should follow this order exactly.

### Step 1. Freeze New Runtime Hardening

Temporarily stop adding:

- new by-target readiness states;
- more flat save guards;
- more tree-pilot drawer micro-interactions;
- more publish/save sequencing UX;
- more target-scoped runtime polish.

Reason:

- these are no longer the highest-value unresolved questions.

### Step 2. Produce One Explicit Definition-Layer Model Note

Write one narrow design note that defines only:

- `StrategyTree`
- `Dashboard Logical Tree`
- `Template Tree`
- `Dashboard Instance Tree`
- `Recording Rule Runtime`

For each object, define:

- owner
- identity key
- whether it exists before target selection
- whether it may depend on `target_part`

This note should be definition-only.
It should not introduce API or DB details yet.

### Step 3. Lock The Ownership Table

Create one small ownership matrix:

```text
object -> owner -> identity -> target-scoped?
```

At minimum include:

- root dashboard definition
- strategy dashboard definition
- root dashboard instance
- strategy dashboard instance
- panel slot ownership
- recording rule publish record

The purpose is to stop `strategy_set_id + target_part + dashboard_variant` from being overused as the universal identity.

### Step 4. Reclassify Existing Endpoints

Take current APIs and classify them into:

- definition-layer endpoints
- runtime-layer endpoints
- mixed / transitional pilot endpoints

Expected outcome:

- by-target panel preview, recording-rule publish, readiness, and flat save remain runtime;
- dashboard-tree pilot stays explicitly transitional;
- no one mistakes them for the final definition model.

### Step 5. Decide The Next Primary Pilot

After the classification above, choose only one of these next steps:

1. definition-layer pilot:
   formalize root-dashboard / strategy-dashboard logical nodes first
2. transitional tree pilot hardening:
   continue evolving the current dashboard-tree pilot as the bridge

Recommended choice:

- choose `1` unless a blocked dependency requires the transitional tree pilot to continue.

## What Should Not Be Done Next

The following should not be the next primary task:

- more by-target publish readiness refinement
- more flat save-guard refinement
- more tree replay/batch UI polish
- more target-input behavior tuning
- more “formal closure” status wording adjustments

Those are now secondary.

## Completion Criteria For This Correction

This correction is successful when:

1. the team can clearly say whether a task belongs to definition-layer or runtime-layer closure;
2. `target_part` is no longer treated as the natural identity for definition-layer objects;
3. the next implementation task is chosen from the definition-layer gap first, not from residual runtime polish;
4. the current tree pilot is explicitly understood as a bridge, not as proof that dashboard-family modeling is finished.

## Immediate Next Action

Do not implement more runtime logic first.

The next concrete deliverable should be:

```text
one small definition-layer model note
+ one ownership matrix
```

Only after that should the next code implementation path be chosen.

## 2026-06-14 First-Cut Status

The first backend-only baseline-selection cut is now implemented in `/OneOPS/OneOps`:

- switch dashboard generation now has one explicit definition-layer selection step before builtin panel-definition fallback;
- the selection rule is narrow and currently only distinguishes:
  - `switch.current`
  - `switch.routing_capable`
- the trigger is matched strategy responsibility only:
  - `l3_route_table.*`
  - `routing_bgp.*`
  - `routing_ospf.*`
- topology evidence does not trigger routing-capable selection;
- runtime data presence is not consulted anywhere in this first cut.

Important boundary:

- this cut only introduces the selection path;
- it does **not** yet expand the routing-capable panel set;
- the routing-capable baseline currently reuses the current switch panel set until the dedicated routing baseline generation step is implemented.

## 2026-06-14 Routing Baseline Generation Status

The next generation cut is now also implemented in `/OneOPS/OneOps`:

- `switch.routing_capable` no longer reuses the current switch panel set unchanged;
- generation now adds these routing families into the routing-capable switch baseline:
  - `l3_route_table.ipv4_count`
  - `l3_route_table.ipv6_count`
  - `routing_bgp.neighbor_total`
  - `routing_bgp.established_total`
  - `routing_ospf.neighbor_total`
  - `routing_ospf.full_total`
- the current switch baseline still stays unchanged;
- baseline selection still happens before generation and still ignores runtime data presence.

Supporting implementation status:

- routing summary contract import now recognizes route-count, BGP, and OSPF count fields;
- Grafana expression generation now covers all six routing-capable baseline families;
- by-target materialization now renders those panels when matched strategy responsibility selects the routing-capable baseline.

## 2026-06-14 Resolution Boundary Status

The generation boundary is now explicit in backend responses too:

- flat materialization/save responses now carry one shared `Baseline` object;
- tree dry-run/save responses now carry the same `Baseline` object;
- tree save-summary-by-batch and recent save-batch list responses now carry the same `Baseline` object too;
- the object is intentionally short:
  - `class_baseline`
  - `variant_baseline`
  - `reason`

Current response contract meaning:

- `class_baseline` answers which class baseline generation chose;
- `variant_baseline` answers which variant baseline the request resolved under;
- `reason` answers why the current class baseline was chosen.

So baseline selection is no longer only an internal helper detail.
It is now part of the explicit generation resolution boundary.

Current/history parity rule:

- current tree preview/save and historical tree replay should describe the same generation choice with the same short `Baseline` language;
- save-batch history should therefore be interpreted as definition-layer replay, not as a separate runtime-only audit dialect.

## 2026-06-14 Internal Resolver Status

The next cleanup cut is also in place now:

- switch dashboard generation no longer has to let each caller hand-stitch `baseline selection + template resolution`;
- `/OneOPS/OneOps` now has one internal switch-generation resolver that returns:
  - class baseline
  - response `Baseline`
  - resolved template/panel set
- flat materialization already consumes that unified generation result directly.

Meaning:

- `Baseline` is not only an API response shape;
- it is now backed by one internal generation-resolution object instead of a growing set of loosely-coupled helper calls.

## 2026-06-14 Shared Materialization Entry Status

The next generation cleanup layer is also done:

- flat dry-run, flat save, tree dry-run, and tree save no longer need to reach generation by chaining through different public entrypoints;
- `/OneOPS/OneOps` now has one internal materialization resolver for switch dashboards;
- that shared resolver now owns:
  - target panel preview
  - target recording-rule preview
  - switch generation resolution
  - Grafana dashboard materialization
  - panel binding owner enrichment

Meaning:

- flat and tree generation now consume the same internal materialization path;
- follow-up work should extend that shared path, instead of reintroducing tree-only or flat-only assembly branches.

## 2026-06-14 Internal Generation Result Status

The next cleanup cut is also done:

- the shared materialization path no longer has to return a public dry-run DTO as its internal working type;
- `/OneOPS/OneOps` now has one internal switch-dashboard generation result object;
- that object carries the shared generation fields directly:
  - `Baseline`
  - target / item contracts / effective contract
  - support summary
  - recording preview
  - dashboard JSON
  - panel bindings
  - materialization summary

Meaning:

- public flat dry-run responses are now adapters over the internal generation result;
- tree planning helpers now consume that same internal result directly, instead of downgrading to a response DTO and then re-reading it.

## 2026-06-14 Generator Boundary Status

The next structural cut is now also done:

- the shared switch-dashboard generation logic is no longer only “a set of resolver methods in one file”;
- `/OneOPS/OneOps` now has a dedicated internal switch dashboard generator type;
- `MetricCapabilityContractResolver` keeps the public orchestration entrypoints, but the actual switch-dashboard generation flow now lives behind that internal generator boundary.

## 2026-06-14 Baseline Module Boundary Status

The next narrow closure cut is now done too:

- `/OneOPS/OneOps` now has a dedicated internal switch baseline module;
- `ClassBaseline`, `VariantBaseline`, baseline selection, strategy-ID baseline derivation, and baseline-aware template selection no longer live as scattered helper combinations across resolver and generator callers;
- routing responsibility detection stays definition-layer only and still ignores runtime `has_data / no_data / not_exposed` state.

Current split:

- resolver:
  - public API-facing orchestration
  - save / tree persistence flow
- switch baseline module:
  - routing responsibility detection
  - class baseline selection
  - response `Baseline` resolution
  - strategy-ID baseline derivation
  - baseline-aware template/panel-set resolution
- switch dashboard generator:
  - dashboard generation
  - binding owner enrichment

Meaning:

- baseline-rule changes should land in the baseline module first;
- dashboard-generation changes should land in the generator boundary first;
- resolver should continue shrinking toward orchestration instead of accumulating more generation logic.

## 2026-06-14 Service Boundary Status

The next cut is now done too:

- `/OneOPS/OneOps` now has a dedicated internal switch dashboard service type;
- flat dry-run, tree dry-run, and tree save pre-persistence assembly no longer each re-stitch generation pieces on their own;
- those entrypoints now consume one service boundary before save-specific persistence begins.

Current split:

- resolver:
  - public API-facing methods
  - save persistence
  - tree save persistence
- switch baseline module:
  - class baseline selection
  - response `Baseline` resolution
  - strategy-ID baseline derivation
  - baseline-aware template/panel-set resolution
- switch dashboard service:
  - shared dry-run assembly
  - shared tree dry-run assembly
  - shared tree generation assembly before persistence
- switch dashboard generator:
  - dashboard generation
  - binding owner enrichment

Meaning:

- the next structural work should extend the service boundary before touching public resolver methods directly;
- tree and flat generation assembly should keep converging inside the shared service path instead of growing separate pre-save branches again.

## 2026-06-14 Persistence Boundary Status

The current switch-dashboard backend closure batch is now aimed at one final internal split:

- public resolver methods should stop owning active save persistence flow;
- flat save and tree save should both run through a dedicated internal persistence service;
- baseline module, generator, shared assembly service, and persistence service should then form the current complete backend boundary for this line.

That execution batch is now tracked in:

- `/OneOPS/docs/superpowers/plans/2026-06-14-snmp-switch-dashboard-final-closure-batch.md`

## 2026-06-14 Baseline Module Status

The next closure phase is now also implemented:

- `ClassBaseline / VariantBaseline / baseline reason` no longer live partly in the large resolver and partly in generator callers;
- `/OneOPS/OneOps` now has one dedicated internal switch-baseline module;
- current baseline selection, routing-responsibility trigger, strategy-ID baseline derivation, and baseline-aware template selection now resolve through that module first.

The latest cleanup in the same batch also closed two real module blockers:

- `resolveForStrategyIDs(...)` no longer depends on template resolution side effects; it now resolves baseline-only state and cannot silently collapse because template loading failed;
- routing-capable template resolution now applies the routing delta even on DB-backed template paths, instead of dropping back to the current-switch DB template and losing the routing-capable identity.

## 2026-06-14 Next Long-Task Closure Target

The next closure batch is no longer "finish one more switch-only improvement".

It is now:

- generic SNMP target-class baseline model closure

Tracked in:

- `/OneOPS/docs/superpowers/plans/2026-06-14-snmp-generic-baseline-model-closure-plan.md`

That batch upgrades the current switch/routing-capable line into one generic SNMP model:

- `TargetClass`
- `ClassBaseline`
- `VariantBaseline`
- `PanelFamily`
- `PanelOwner`
- generic baseline-aware generation entry

The critical shift is:

- current switch baselines become explicit specializations under a generic SNMP model;
- non-switch SNMP targets must no longer silently inherit switch assumptions;
- future SNMP class expansion must extend the same generic model rather than create one class-specific mechanism at a time.

Current status after implementation:

- the generic SNMP target-class module is now the active baseline-resolution entry;
- current switch baselines are explicit specializations under that generic SNMP model;
- non-switch SNMP targets no longer have to fall through switch-only assumptions just to materialize a dashboard baseline.

Current split:

- resolver:
  - public API-facing methods
  - history/query orchestration
- switch baseline module:
  - class baseline selection
  - response `Baseline`
  - strategy-ID to baseline derivation
  - baseline-aware template resolution
- switch dashboard generator:
  - dashboard generation
  - binding owner enrichment
- switch dashboard service:
  - shared dry-run assembly
  - shared tree-generation assembly
- switch dashboard persistence service:
  - flat save persistence
  - tree save persistence

Meaning:

- the current switch-dashboard backend closure is no longer “resolver-centric”;
- future baseline work should land in the baseline module first instead of re-growing baseline rules in the large resolver or in per-caller helpers.
- the latest generic-baseline correctness gap is now closed too: when callers omit `dashboard_variant`, backend save/tree persistence follows the resolved `Baseline.VariantBaseline` (`snmp.generic.operations` for generic SNMP targets) instead of silently falling back to `snmp.switch.operations`.
- quick env now seeds the same class-level template floor too: `snmp.generic` is present as the generic SNMP template root, and `snmp.switch.routing_capable` is present as an additive switch delta template, so quick env no longer exposes only the legacy switch template family.
- quick env now also closes the last “real use” gap for current environments: `/OneOPS/quick_env/scripts/ensure_snmp_dashboard_instances.sh` logs into the live OneOPS API and persists real dashboard instances, instead of stopping at template seeding. Current switch instances are ensured idempotently, and the generic SNMP path (`server_oob_snmp -> snmp.generic.operations`) is now auto-saved for the live environment as soon as one successful OOB SNMP target exists.
- quick env now also carries a real routing-capable switch suite end to end: `zzzzzzzzzz-snmp-switch-routing-capable-strategy-set-bootstrap.sql` seeds an independent `snmp_switch_routing_capable` strategy set plus a Huawei VRP routing overlay leaf, and runtime ensure now auto-saves one live `switch.routing_capable` instance against `DVC2C4468B0B813`. This keeps the ordinary switch suite unchanged while making the routing-capable baseline truly usable in the current environment.
- shared persistence first cut is now active in backend save paths: flat SNMP dashboard save no longer persists one Grafana dashboard row per target when `class_baseline + variant_baseline + template_key` are the same. The saved dashboard identity is now shared and target bindings fan into it. Saved dashboard JSON is also scrubbed of target-specific title / UID / templating defaults so the persistent object no longer carries `SW-1`-style instance identity. Quick env runtime ensure now detects legacy per-target SNMP dashboard rows, drops the old unique `dashboard_code` target-binding constraint if it still exists, purges legacy variant-scoped duplicates, and rebuilds them through the shared save path.
- generation semantics are now aligned with the definition-layer rule too: SNMP dashboard generation no longer deletes panel families just because current runtime `supports` or recording-rule evidence are weak. When a class baseline says a panel family exists, the dashboard now keeps that panel and uses a harmless `no data` PromQL target when no live expression is currently derivable. This closes the “shared dashboard only shows 5 panels” regression and keeps class-level structure stable while runtime still decides only the current panel state.
- the next closure axis is now explicitly different from the earlier class-level shared flat dashboard path. See [2026-06-14-snmp-suite-strategy-dashboard-tree-design.md](/OneOPS/docs/superpowers/specs/2026-06-14-snmp-suite-strategy-dashboard-tree-design.md) and [2026-06-14-snmp-suite-strategy-dashboard-tree-closure-plan.md](/OneOPS/docs/superpowers/plans/2026-06-14-snmp-suite-strategy-dashboard-tree-closure-plan.md). The current product rule is now:
  - `dashboard selection = projection of strategy selection`
  - `monitoring suite -> root dashboard`
  - `matched strategy node -> strategy dashboard node`
  - `target -> binding to one dashboard tree`
- suite-root plus strategy-node dashboard tree generation is now the primary backend save path. Flat save remains available, but it is now just a compatibility projection of the saved root node from the dashboard tree. The business center of gravity is therefore no longer a single class-level switch dashboard row, but the suite root plus its strategy dashboard children.
- class baselines (`snmp.generic`, `switch.current`, `switch.routing_capable`) are now treated as generation floors only. They still determine reusable panel families, variants, and template floors, but they must not replace the matched strategy tree as the semantic selector.
- quick env runtime ensure is now aligned with that tree-first model. The switch path is considered healthy only when:
  - the suite root dashboard keeps explicit root-summary responsibility (`Device Identity`, `Overall Health`, `Active Alerts`);
  - at least one strategy dashboard under that root keeps explicit strategy-display responsibility (`Interface Utilization Top 10`, `Packets Per Second`, `OneOPS config evidence`).
  This replaces the older “shared switch must equal CE168 everywhere” assumption.
- the CE168 row remains intentionally visible, but only as a reference sample:
  - `OneOPS SNMP Switch Ops - CE16808-172-21-165-11`
  - it must not be treated as the canonical shared switch mother template;
  - it is now a quality/reference artifact for later overlay and layout work, while the canonical business model is the suite root plus strategy dashboard tree.
- 2026-06-14: the current product visibility path now also follows that tree-first logic more explicitly. The Grafana dashboard list uses `suite root / strategy / reference` semantics instead of only `root / child`, and `StrategySetDetailDrawer` now treats `Root + Strategy Dashboard Tree` as the formal semantic path. The old “Pilot 入口” wording is no longer the primary explanation; flat save remains visible only as the compatibility `root projection`.
- 2026-06-14: the Grafana dashboard list now also exposes a direct `查看策略树` action on `suite root` rows. That action opens the selected root's `strategy dashboard nodes` in a dedicated modal, so the product no longer requires users to infer tree semantics only from row indentation or from the strategy-set drawer. The current UI split is now explicit: the list page owns suite-root entry, and the tree modal/drawer owns strategy-dashboard visibility.
- 2026-06-14: the product path is now one step tighter too. SNMP suite-root rows can deep-link into `StrategyTemplate -> 策略集 -> StrategySetDetailDrawer`, and strategy-node rows forward `focusStrategyId` so the drawer can tell users which strategy dashboard node they came from. This keeps the suite-root list and the formal tree drawer on one navigation chain instead of leaving the modal as a dead-end visibility layer.
- 2026-06-14: the next closure axis is now explicitly the dashboard-regeneration problem, not more root/tree navigation work. See:
  - `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-strategy-effective-metrics-dashboard-derivation-design.md`
  - `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-strategy-effective-metrics-inventory.md`
  - `/OneOPS/docs/superpowers/plans/2026-06-14-snmp-strategy-dashboard-regeneration-plan.md`
  The frozen correction is:
  - start from each strategy's `effective_contract`
  - derive one strategy dashboard per strategy node
  - treat CE168 as a reference sample only
  - forbid direct reuse of hard-coded CE168 interface panels such as `100GE5/0`
- 2026-06-14: the first runtime-backed inventory is now exported too. `/OneOPS/quick_env/scripts/export_snmp_strategy_effective_metrics_inventory.py` logs into the live OneOPS API, pulls every SNMP strategy plus its `metric-contract`, and writes `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-strategy-effective-metrics-inventory.md`. The current environment result is decisive: 17 network-oriented SNMP strategies currently collapse into one identical effective metric signature (`l2_neighbors + l2_mac_table + l3_arp_table + l2_vlan_table + l2_stp_state + device_metrics.default`). That means dashboard differentiation still cannot honestly come from copying CE168 CPU/interface/optics sample panels unless the strategy contracts first grow those metrics explicitly.
- 2026-06-14: the next deterministic output exists now too. `/OneOPS/quick_env/scripts/export_snmp_strategy_dashboard_derivation_table.py` reads the same live API inventory and emits:
  - `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-strategy-dashboard-derivation-table.md`
  - `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-strategy-dashboard-derivation-table.json`
  The current derivation result is:
  - many current network strategies keep distinct strategy-dashboard node identity but legitimately share one `snmp.switch.topology-common` recipe;
  - firewall strategies already need distinct `firewall-common` nodes even though their current effective signature is still topology-shaped;
  - routing remains an explicit `routing-overlay`;
  - CE168 CPU/interface/optics content is still regenerate-only or forbidden carryover, not current semantic input.
- 2026-06-14: the derivation output is now also surfaced in the formal dashboard-tree product path instead of living only in scripts/docs. Current tree dry-run, tree save, and save-summary replay nodes all expose:
  - `recipe_key`
  - `panel_families`
  - `metric_group_keys`
  - `display_scope_summary`
  - `optional_overlay_families`
  - `ce168_handling_summary`
  and `StrategySetDetailDrawer` now renders those fields directly. That means “how this strategy node should regenerate its dashboard, and how CE168 may or may not influence it” is now visible in the same tree UI users already use for root/strategy dashboard semantics.
- 2026-06-14: the next formal artifact now exists too. `/OneOPS/quick_env/scripts/export_snmp_strategy_dashboard_node_definitions.py` converts the live derivation rows into machine-readable strategy dashboard node definitions and writes:
  - `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-strategy-dashboard-node-definitions.md`
  - `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-strategy-dashboard-node-definitions.json`
  The current rule is now explicit in code and assets:
  - one strategy row -> one strategy dashboard node definition;
  - `recipe_key` governs reusable generation logic only;
  - `panel_families` + `metric_group_keys` define current display responsibility;
  - CE168 influence must pass through `reusable_concepts / regenerate_panels / forbidden_carryovers`, never direct copying.
- 2026-06-14: dashboard-tree nodes now also expose one more concrete regeneration layer: `generated_panels`. This is the current recipe-projected panel-definition preview for each root/strategy node. It is not the final Grafana layout yet, but it is now the structured answer to “given this recipe and this node-local metric scope, which panel definitions would the node currently generate?”. `StrategySetDetailDrawer` renders that list directly, so users can now inspect:
  - node identity
  - node metric responsibility
  - CE168 reuse / regenerate / forbid rules
  - current generated panel definitions
  in one place.
- 2026-06-14: `snmp.switch.topology-common` no longer borrows `switch.current` flat dashboard definitions and filters them down. It now owns an explicit node-local recipe source for topology evidence tables and count cards (`l2_neighbors.summary`, `l2_mac_table.*`, `l3_arp_table.*`, `l2_vlan_table.*`, `l2_stp_state.*`). `snmp.firewall.current-common` has now also been split into its own node-local evidence recipe: it still reflects the same current mandatory families, but the generated panel source is firewall-specific (`firewall` section, firewall-local titles) instead of reusing switch topology titles or interface-heavy flat dashboard panels. This is the first real cut that separates strategy-node regeneration from the old flat switch dashboard source.
- 2026-06-14: `device_metrics.default` is no longer a raw fallback panel key in `generated_panels`. It now resolves into recipe-specific node-local panel definitions:
  - `snmp.switch.topology-common` -> `summary` section, `Node Device Metrics`
  - `snmp.firewall.current-common` -> `firewall` section, `Firewall Device Metrics`
  - `snmp.server.basic` -> `server` section, `Server Device Metrics`
  - `snmp.server.oob-common` -> `oob` section, `OOB Device Metrics`
  - `snmp.device.summary` -> `device` section, `Device Metrics Summary`
  This does not yet solve full summary/detail regeneration, but it removes one more placeholder layer and makes `device_metrics.default` an honest node-local content source.
