# OneOPS Route Table Canonical Fact Phase 4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add production `route_table` canonical facts for network devices so NetPath can build engine-ready snapshots from real DC2 latest facts instead of route-less previews and synthetic-only fixtures.

**Architecture:** Keep route data in the shared Device Collection 2 canonical fact layer, not in a NetPath-only model. Add one network-device `route_table` processor, one built-in collection contract for a real CLI route dataset, and service/provider tests that prove the resulting facts persist, surface through latest-fact reads, and assemble into NetPath snapshots with correct diagnostics.

**Tech Stack:** Go, GORM, existing `OneOPS/app/device_collection2` fact processors and contract bootstrap, existing `OneOPS/app/netpath/snapshot/provider`, existing `OneOPS/app/netpath/snapshot` preview builder, MySQL-backed latest fact tables, superpowers docs.

---

## Scope

This is Phase 4 of the fact-application foundation plan, not NetPath UI or full analysis-run wiring.

In scope:

- freeze the `route_table` canonical fact schema and identity rule
- add processor tests before implementation
- implement and register the processor in DC2
- add at least one built-in network-device dataset contract
- persist invalid route rows as fact issues instead of accepted facts
- review latest-fact tenant/scope implications before NetPath consumes production data
- validate NetPath provider fixtures against DC2-shaped `route_table` facts

Out of scope:

- UI changes
- live device collection
- route backfill or migration jobs
- global tenant-model redesign for all DC2 fact tables
- full NetPath run persistence and API workflow
- firewall/NAT/PBR fact families

## Canonical Fact Contract

Fact type:

```text
route_table
```

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

Field rules:

- `vrf`: required in normalized output, default to `default` when source data is blank.
- `destination`: required CIDR/prefix string; invalid prefixes become issues.
- `next_hop_ip`: optional for connected and null routes; required when the source route is recursive or next-hop based.
- `out_interface`: normalized interface name when present; blank is allowed only when the route is genuinely null/discard or the source route is next-hop-only and the phase explicitly accepts that shape.
- `protocol`: normalized lowercase routing source such as `connected`, `static`, `ospf`, `bgp`.
- `metric`: optional integer.
- `preference`: optional integer.
- `null_route`: boolean; true for `null0` / discard / blackhole routes.
- `raw`: preserved source route text or source-row summary for drilldown.

Identity key to freeze in this phase:

```text
<target_id>:route:vrf:<vrf>:dest:<destination>:nh:<next_hop_or_direct_or_null>:out:<out_interface_or_none>
```

Examples:

```text
r1:route:vrf:default:dest:10.0.2.0/24:nh:192.0.2.2:out:ge0/1
r1:route:vrf:default:dest:10.0.3.0/24:nh:direct:out:ge0/2
r1:route:vrf:default:dest:203.0.113.0/24:nh:null:out:null0
```

Reason for this freeze:

- it stays deterministic within `target_id + fact_type`
- it distinguishes direct and null routes without overloading empty `next_hop_ip`
- it matches the current DC2 style of explicit identity fragments better than a bare positional string
- it is easy for NetPath fixtures and issue diagnostics to read

## Files

Likely implementation files and exact code areas to touch:

- `OneOPS/app/device_collection2/fact/route_table_processor.go`
  - new processor following the patterns in `server_processor.go`, `interface_ip_processor.go`, and `topology_processor.go`
- `OneOPS/app/device_collection2/fact/registry.go`
  - `NewDefaultRegistry()` must register the new processor
- `OneOPS/app/device_collection2/service/impl/device_collection2.go`
  - `ProcessFacts()`
  - `persistFacts()`
  - `upsertLatestFacts()`
  - `ListLatestFacts()`
- `OneOPS/app/device_collection2/service/i_device_collection2.go`
  - current latest-fact query surface to review for scope changes
- `OneOPS/app/device_collection2/api/device_collection2.go`
  - `ListLatestFacts()` query surface if scope parameters change
- `OneOPS/app/device_collection2/service/impl/device_collection2_network_contract_bootstrap.go`
  - `builtinNetworkCLIContracts()`
  - vendor dataset helper additions for route collection
- `OneOPS/app/device_collection2/service/impl/device_collection2_test.go`
  - service-level `ProcessFacts` and persistence tests
- `OneOPS/app/netpath/snapshot/provider/facts.go`
  - existing `FactTypeRouteTable` contract helpers
- `OneOPS/app/netpath/snapshot/provider/assembler.go`
  - `addRouteTables()`
- `OneOPS/app/netpath/snapshot/provider/assembler_test.go`
  - DC2-shaped route fixture validation
- `OneOPS/app/netpath/snapshot/provider/validator.go`
  - `validateRoutes()`
  - `deviceHasRouteTable()`
- `OneOPS/app/netpath/snapshot/provider/validator_test.go`
  - route quality and blocked/degraded expectations
- `OneOPS/app/netpath/snapshot/builder.go`
  - current preview-only latest-fact usage and tenant gap reference point
- `OneOPS/app/netpath/snapshot/builder_test.go`
  - guardrail tests for route-table gap and scope expectations
- `docs/superpowers/specs/2026-06-19-oneops-canonical-fact-contract-design.md`
  - update the route identity rule to this exact frozen form
- `docs/superpowers/specs/2026-06-19-oneops-canonical-fact-inventory.md`
  - record the implemented dataset, issue codes, and tenant/scope decision

## Task 1: Freeze The Route Table Schema And Identity Rule

Purpose:

- remove the current disagreement between the contract design and inventory wording before code lands

- [x] **Step 1: Reconcile the route identity format in docs**

Update:

```text
docs/superpowers/specs/2026-06-19-oneops-canonical-fact-contract-design.md
docs/superpowers/specs/2026-06-19-oneops-canonical-fact-inventory.md
```

Expected:

```text
Both docs use the same identity key:
<target_id>:route:vrf:<vrf>:dest:<destination>:nh:<next_hop_or_direct_or_null>:out:<out_interface_or_none>
```

- [x] **Step 2: Freeze accepted issue codes for route normalization**

Document these issue codes in the contract/inventory update:

```text
missing_required_field
invalid_prefix
invalid_ip
invalid_metric
invalid_preference
```

If implementation needs one extra route-specific code, add it deliberately and document why.

- [x] **Step 3: Confirm NetPath field expectations still match**

Read:

```bash
rg -n 'FactTypeRouteTable|next_hop_ip|out_interface|null_route|preference|metric' OneOPS/app/netpath/snapshot/provider
```

Expected:

```text
provider/facts.go, assembler.go, and validator.go already expect the route_table field family and should not require a parallel route schema
```

Implementation note:

```text
Design and inventory now use:
<target_id>:route:vrf:<vrf>:dest:<destination>:nh:<next_hop_or_direct_or_null>:out:<out_interface_or_none>

Issue codes frozen:
missing_required_field, invalid_prefix, invalid_ip, invalid_metric, invalid_preference.
Provider field expectations already match vrf/destination/next_hop_ip/out_interface/protocol/metric/preference/null_route/raw.
```

## Task 2: Write Processor And Persistence Tests First

Purpose:

- establish the route-table contract at the DC2 service boundary before adding the processor

- [x] **Step 1: Add happy-path route normalization tests**

Add tests in:

```text
OneOPS/app/device_collection2/service/impl/device_collection2_test.go
```

Cover at least:

```text
static route with next_hop_ip + out_interface
connected route with direct next hop semantics
null/discard route with null_route=true
vrf defaulting when source vrf is blank
protocol lowercase normalization
metric/preference integer normalization
identity_key exact match to the frozen format
provenance.processor_key = processor.route_table.v1
```

- [x] **Step 2: Add invalid route tests**

In the same file, add cases for:

```text
invalid destination prefix
invalid next_hop_ip
missing destination
non-integer metric/preference when source provides garbage
```

Expected assertions:

```text
no accepted route_table fact for the bad row
FactIssue created with stable issue_code
issue row keeps target_id, dataset_key, row_index, and processor_key
```

- [x] **Step 3: Add persistence and latest-projection tests**

Still in:

```text
OneOPS/app/device_collection2/service/impl/device_collection2_test.go
```

Add a persisted test that:

```text
calls ProcessFacts with Persist=true
asserts valid route facts write to device_collection2_fact and device_collection2_fact_latest
asserts invalid rows write to device_collection2_fact_issue only
asserts a later duplicate identity updates the latest row while leaving history queryable
```

- [x] **Step 4: Run red tests**

Run:

```bash
cd OneOPS
go test ./app/device_collection2/service/impl -run 'TestProcessFacts.*Route|Test.*Latest.*Route|Test.*Route.*Issue' -count=1
```

Expected:

```text
FAIL because no route_table processor is registered yet
```

Implementation note:

```text
Added service-level route tests in device_collection2_test.go.
Observed red failure: processor_not_found before NewRouteTableProcessor registration.
```

## Task 3: Implement And Register The Route Table Processor

Purpose:

- add the missing network-device route canonicalizer without disturbing existing `server_route`

- [x] **Step 1: Create the processor**

Create:

```text
OneOPS/app/device_collection2/fact/route_table_processor.go
```

Implementation expectations:

```text
Accept network-device route dataset keys only
Normalize vrf, destination, next_hop_ip, out_interface, protocol, metric, preference, null_route, raw
Emit route_table facts with FactQuality.Valid=true for accepted rows
Emit FactIssue instead of accepted facts for invalid rows
Use baseProvenance() and uniqueStrings(sourceFields)
```

- [x] **Step 2: Keep server and network routes separate**

Do not repurpose:

```text
OneOPS/app/device_collection2/fact/server_processor.go
```

The existing `ServerRouteProcessor` should remain the home for `linux_default_route` and `windows_default_route`. This phase adds a sibling processor for network-device routing tables, not a merged route abstraction.

- [x] **Step 3: Register the processor**

Modify:

```text
OneOPS/app/device_collection2/fact/registry.go
```

Expected:

```text
NewDefaultRegistry() includes NewRouteTableProcessor() in the default chain
```

- [x] **Step 4: Add focused processor unit tests if service tests are too coarse**

If the service-level tests do not give enough debugging signal, add targeted tests under:

```text
OneOPS/app/device_collection2/fact/
```

Suggested file:

```text
OneOPS/app/device_collection2/fact/route_table_processor_test.go
```

- [x] **Step 5: Run DC2 route tests**

Run:

```bash
cd OneOPS
go test ./app/device_collection2/fact ./app/device_collection2/service/impl -run 'Test.*Route' -count=1
```

Expected:

```text
ok
```

Implementation note:

```text
Added app/device_collection2/fact/route_table_processor.go and registered it in registry.go.
ServerRouteProcessor remains unchanged.
Service tests cover static, direct, null, invalid, fractional metric/preference, persistence/latest/history behavior.
Focused service tests were enough; no separate fact package test was added.
```

## Task 4: Add One Built-In Network Device Route Dataset Contract

Purpose:

- ensure route_table facts can come from a real built-in collection contract rather than hand-built API payloads only

- [x] **Step 1: Choose one MVP device contract**

Recommended first contract:

```text
h3c_comware
h3c_secpath
```

Reason:

```text
these already have built-in interface and LLDP datasets in device_collection2_network_contract_bootstrap.go, so route collection can extend the same contract family cleanly
```

- [x] **Step 2: Add a bootstrap test first**

Add or extend tests in:

```text
OneOPS/app/device_collection2/service/impl/device_collection2_test.go
```

Assert:

```text
builtinNetworkCLIContracts() includes a route dataset for the chosen contract family
dataset key maps to route_table processor-compatible fields
raw commands and field mapping are not empty
```

- [x] **Step 3: Add the dataset helper**

Modify:

```text
OneOPS/app/device_collection2/service/impl/device_collection2_network_contract_bootstrap.go
```

Implementation expectations:

```text
one dataset helper dedicated to route-table collection
textfsm or equivalent standardizer that yields destination, next_hop_ip, out_interface, protocol, metric, preference, optional vrf/raw
dataset key chosen to match the new processor Accepts() list
```

- [x] **Step 4: Run bootstrap-focused tests**

Run:

```bash
cd OneOPS
go test ./app/device_collection2/service/impl -run 'Test.*Builtin.*Route|Test.*Contract.*Route' -count=1
```

Expected:

```text
ok
```

Implementation note:

```text
Added h3CComwareRouteTableDataset() with dataset key cli_route_table.
Attached it to h3c_comware and h3c_secpath builtin network CLI contracts.
Added bootstrap and TextFSM parse tests for public route and NULL0 route samples.
```

## Task 5: Harden Invalid Route Issue Handling

Purpose:

- make broken route rows visible and queryable without poisoning latest facts

- [x] **Step 1: Prove invalid rows persist only as issues**

Extend the persisted service test so it verifies:

```text
device_collection2_fact_issue contains one row per invalid route input
device_collection2_fact_latest has no row for rejected identities
issue context preserves the offending value when useful
```

- [x] **Step 2: Verify issue reporting aligns with current DC2 run summaries**

Read and test around:

```text
OneOPS/app/device_collection2/service/impl/device_collection2_run.go
```

Expected:

```text
route-table fact issues contribute to existing fact_issue run reporting without custom summary plumbing
```

- [x] **Step 3: Keep validator responsibility separate**

Rule to preserve in implementation:

```text
processor rejects impossible source rows
NetPath validator handles assembled-snapshot consistency such as unresolved out_interface or missing ingress route tables
```

This prevents the processor from silently passing malformed prefixes downstream and also prevents the validator from becoming a source-row parser.

Implementation note:

```text
TestLatestRouteTableFactsPersistHistoryAndIssues verifies invalid route rows persist as fact issues, preserve offending context value, and do not create latest facts.
TestListRunDevicesReturnsStandardDiagnostics now seeds a route_table invalid_prefix fact issue and verifies run-device issue summary grouping keeps dataset_key, processor_key, issue_code, and count.
Validator tests continue to cover assembled-route consistency separately: malformed destination blocks, unresolved non-null out_interface degrades, null routes can omit out_interface.
```

## Task 6: Resolve Latest Fact Tenant And Scope Guardrails

Purpose:

- keep Phase 4 honest about the current multi-tenant gap before NetPath starts consuming production route facts

Current code facts:

```text
IDeviceCollection2.ListLatestFacts() has no tenant parameter
DeviceCollection2API.ListLatestFacts() exposes no tenant query
DeviceCollection2Srv.ListLatestFacts() filters only by target_id, fact_type, valid_only, limit
netpath/snapshot/builder.go currently reads latest facts with target_id=""
netpath service and provider already require tenant_code in their own request layer
```

- [x] **Step 1: Decide the minimum safe scope rule for this phase**

Recommended rule:

```text
do not add tenant_code to the latest-table primary key in this phase
do not allow production NetPath route consumption to rely on unscoped ListLatestFacts("", fact_type, ...)
require either explicit target_id filtering or a reviewed target set resolved outside the latest table
```

If the team wants tenant-aware latest facts at the DC2 service layer now, treat that as a deliberate sub-scope expansion and document the migration risk separately.

- [x] **Step 2: Add guardrail tests**

Add tests in one or both of:

```text
OneOPS/app/device_collection2/service/impl/device_collection2_test.go
OneOPS/app/netpath/snapshot/builder_test.go
```

Assert at least one of these outcomes:

```text
unscoped latest-fact reads remain documented as preview-only
production provider path requires explicit device scope
future tenant-aware reader interface is named and covered by a failing or skipped contract test
```

- [x] **Step 3: Decide whether the interface changes in this phase**

Review:

```text
OneOPS/app/device_collection2/service/i_device_collection2.go
OneOPS/app/device_collection2/api/device_collection2.go
OneOPS/app/device_collection2/service/impl/device_collection2.go
```

Recommended outcome:

```text
keep the public DC2 latest-fact API unchanged for Phase 4
add scope enforcement in the NetPath-facing reader/provider seam instead of broadening the DC2 API mid-phase
```

Implementation note:

```text
Decision: keep IDeviceCollection2.ListLatestFacts(ctx, target_id, fact_type, valid_only, limit) and DeviceCollection2API.ListLatestFacts unchanged in Phase 4.
Guardrails: app/netpath/snapshot/builder_test.go asserts preview BuildPreview still performs unscoped latest-fact reads and therefore remains preview-only; app/device_collection2/service/impl/device_collection2_test.go keeps TestListLatestFactsTenantScopeNotImplemented skipped as the explicit production blocker.
Residual gap: production NetPath/IPAM/L2 snapshot consumption must add a tenant-aware or explicit-target reader seam before using unscoped latest facts.
```

## Task 7: Validate NetPath Provider Fixtures Against Real DC2 Route Facts

Purpose:

- prove the new route_table facts actually unblock NetPath snapshot assembly instead of only passing DC2-side tests

- [x] **Step 1: Add a DC2-shaped route fixture test**

Extend:

```text
OneOPS/app/netpath/snapshot/provider/assembler_test.go
```

Cover:

```text
route_table facts assembled from DC2 fields into AnalysisRouteTable
RouteSourceRef preserved from FactID
mixed route families: static, connected, null route
server_route remains a separate fallback path and does not replace route_table
```

- [x] **Step 2: Add validator expectations**

Extend:

```text
OneOPS/app/netpath/snapshot/provider/validator_test.go
```

Assert:

```text
valid route_table snapshot -> ready
missing ingress VRF route table -> blocked
unresolved out_interface on a non-null route -> degraded
invalid destination should never arrive from processor tests, but validator still blocks malformed assembled routes defensively
```

- [x] **Step 3: Review preview builder behavior**

Check:

```text
OneOPS/app/netpath/snapshot/builder.go
OneOPS/app/netpath/snapshot/builder_test.go
```

Expected direction:

```text
preview builder may continue reporting route_table_missing until the production provider path replaces it
do not claim NetPath is fully unblocked until provider fixture validation passes with route_table facts
```

- [x] **Step 4: Run NetPath snapshot tests**

Run:

```bash
cd OneOPS
go test ./app/netpath/snapshot/provider ./app/netpath/snapshot -run 'Test.*Route|Test.*Validator|Test.*Preview' -count=1
```

Expected:

```text
ok
```

Implementation note:

```text
app/netpath/snapshot/provider/assembler_test.go now uses DC2 canonical route_table identities for static, connected/direct, and null route facts and asserts RouteSourceRef is preserved from FactID.
The null route fixture preserves H3C-style standardized next_hop_ip=0.0.0.0 while using identity nh:null.
Existing validator tests cover ready, degraded unresolved out_interface, blocked malformed destination, missing ingress route table, and null route without out_interface.
Preview builder remains preview-only and still reports route_table_missing.
Verification run:
/usr/local/go/bin/go test ./app/netpath/snapshot/provider ./app/netpath/snapshot -run 'Test.*Route|Test.*Validator|Test.*Preview|TestAssemblerBuildsEngineReadyRouteTopologySnapshot' -count=1
```

## Task 8: Final Verification And Handoff

Purpose:

- leave a clean execution boundary for the next agent

- [x] **Step 1: Run focused DC2 and NetPath verification**

Run:

```bash
cd OneOPS
go test ./app/device_collection2/fact ./app/device_collection2/service/impl ./app/netpath/snapshot/provider ./app/netpath/snapshot -count=1
```

Expected:

```text
ok
```

- [x] **Step 2: Check boundary assumptions**

Run:

```bash
cd OneOPS
rg -n 'route_table|processor.route_table|ListLatestFacts\\(' app/device_collection2 app/netpath
```

Expected:

```text
route_table shows up in processor, registry, contract bootstrap, service tests, and provider tests
latest-fact scope expectations are explicit rather than hidden
```

- [x] **Step 3: Update foundation and roadmap status docs only after verification**

Likely docs to update after implementation succeeds:

```text
docs/superpowers/specs/2026-06-19-oneops-canonical-fact-contract-design.md
docs/superpowers/specs/2026-06-19-oneops-canonical-fact-inventory.md
docs/superpowers/plans/2026-06-19-oneops-fact-application-foundation-master-plan.md
docs/superpowers/plans/2026-06-19-oneops-netpath-master-roadmap.md
```

Do this in a separate final docs pass so concurrent documentation edits are easier to reconcile.

Implementation note:

```text
Final verification after code review fixes:
/usr/local/go/bin/go test ./app/device_collection2/fact ./app/device_collection2/service/impl ./app/netpath/snapshot/provider ./app/netpath/snapshot -count=1

Boundary check:
rg -n 'route_table|processor.route_table|ListLatestFacts\(' app/device_collection2 app/netpath

Docs updated:
docs/superpowers/plans/2026-06-19-oneops-fact-application-foundation-master-plan.md
docs/superpowers/specs/2026-06-19-oneops-canonical-fact-inventory.md
docs/superpowers/plans/2026-06-19-oneops-netpath-master-roadmap.md
```

## Definition Of Done

- `route_table` is a registered DC2 canonical fact type for network devices.
- Required fields and identity key are frozen and documented consistently.
- At least one built-in network-device contract can standardize route rows into processor-ready fields.
- Invalid route rows become `device_collection2_fact_issue` records, not accepted latest facts.
- Latest fact behavior for route_table is covered by persistence tests.
- Tenant/scope risk is explicitly addressed for the production NetPath consumption path.
- NetPath provider tests pass using DC2-shaped `route_table` facts.
- Preview-only route gaps are not misrepresented as production readiness.
