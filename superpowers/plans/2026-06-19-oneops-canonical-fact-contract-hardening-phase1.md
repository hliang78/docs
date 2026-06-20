# OneOPS Canonical Fact Contract Hardening Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the smallest contract hardening changes needed so existing DC2 canonical facts can safely support IPAM, L2 snapshot, NetPath, topology, and RCA planning work.

**Architecture:** Keep Device Collection 2 as the canonical fact envelope. Do not introduce a new fact platform. Add targeted tests, naming decisions, and query-scope checks around existing processors and APIs before larger application projections begin.

**Tech Stack:** Go, GORM, existing `OneOPS/app/device_collection2` fact processors, existing `OneOPS/app/netpath/snapshot/provider`, superpowers documentation.

---

## Scope

This plan is Phase 1 hardening only.

In scope:

- processor contract tests
- fact type naming decision for `mac_table_entry`
- ARP enrichment gap documentation
- route table gap test scaffolding
- provenance and latest projection behavior checks
- tenant/scope risk tests or documented blockers

Out of scope:

- implementing IPAM projection
- implementing route table collection
- wiring NetPath production provider
- changing IPAM workflow state
- frontend changes

## Files

Likely implementation files:

- `OneOPS/app/device_collection2/fact/*_test.go`
- `OneOPS/app/device_collection2/fact/topology_processor.go`
- `OneOPS/app/device_collection2/fact/registry.go`
- `OneOPS/app/device_collection2/service/impl/device_collection2_test.go`
- `OneOPS/app/device_collection2/service/impl/device_collection2.go`
- `OneOPS/app/netpath/snapshot/provider/*_test.go`
- `docs/superpowers/specs/2026-06-19-oneops-canonical-fact-contract-design.md`
- `docs/superpowers/specs/2026-06-19-oneops-canonical-fact-inventory.md`

## Task 1: Freeze Fact Type Naming For MAC Facts

Purpose:

- Remove ambiguity between product language `mac_table` and current emitted fact type `mac_table_entry`.

- [x] **Step 1: Confirm current emitted fact type**

Read:

```bash
rg -n 'FactType:.*mac|mac_table_entry|processor.mac_table' OneOPS/app/device_collection2/fact
```

Expected:

```text
topology_processor.go shows processor.mac_table.v1 and emitted fact type mac_table_entry
```

- [x] **Step 2: Add or update processor test**

Add a test in:

```text
OneOPS/app/device_collection2/fact/topology_processor_test.go
```

The test should assert:

```text
dataset mac_table produces fact_type mac_table_entry
identity key includes target, mac, and vlan when present
provenance.processor_key is processor.mac_table.v1
```

- [x] **Step 3: Update contract docs if implementation keeps current name**

Update:

```text
docs/superpowers/specs/2026-06-19-oneops-canonical-fact-contract-design.md
```

Expected:

```text
mac_table_entry is documented as canonical, with mac_table treated as product language alias only.
```

- [x] **Step 4: Run targeted tests**

Run:

```bash
cd OneOPS
go test ./app/device_collection2/fact -run 'Test.*MAC|Test.*Mac|Test.*mac' -count=1
```

Expected:

```text
ok .../app/device_collection2/fact
```

Implementation note:

```text
Added TestMACTableProcessorContracts_FactTypeIdentityAndProvenance.
Added TestMACTableProcessorContracts_IdentityFallsBackToTargetAndMACWithoutVLAN.
mac_table_entry identity is now target + mac + optional vlan.
Added TestProcessFactsPersistsMACTableFanInHistoryAndLatest to lock the fan-in behavior:
history keeps both rows; latest keeps one row from the later input.
Added TestProcessFactsCleansStaleLegacyMACTableLatestKeys and latest cleanup:
old latest identities with bridge_port/local-interface suffixes are removed when a canonical row for the same target/MAC/VLAN is upserted.
Rows for different target, different MAC, or different VLAN are retained.
History rows are not deleted.
```

## Task 2: Harden ARP Fact Contract Tests

Purpose:

- Confirm ARP facts exist and record the remaining enrichment gap without blocking current consumers.

- [x] **Step 1: Add ARP processor contract test**

Add a test in:

```text
OneOPS/app/device_collection2/fact/topology_processor_test.go
```

The test should assert:

```text
dataset snmp_arp emits arp_entry
valid ip and mac are normalized
identity key includes target, ip, mac, and optional interface
invalid ip or mac creates FactIssue
```

- [x] **Step 2: Document current missing enrichment fields**

Update:

```text
docs/superpowers/specs/2026-06-19-oneops-canonical-fact-inventory.md
```

Expected:

```text
arp_entry exists but lacks vrf, age, state, source protocol detail, and resolution metadata.
```

- [x] **Step 3: Run targeted tests**

Run:

```bash
cd OneOPS
go test ./app/device_collection2/fact -run 'Test.*ARP|Test.*Arp|Test.*arp' -count=1
```

Expected:

```text
ok .../app/device_collection2/fact
```

Implementation note:

```text
Added TestARPProcessorContracts_EmitsNormalizedEntryAndIssuesInvalidRows.
Invalid-row assertions are keyed by RowIndex and IssueCode, not issue slice order.
The same test covers ARP identity without local interface:
target + ip + mac.
```

## Task 3: Add Provenance And Quality Contract Tests

Purpose:

- Ensure accepted facts preserve the minimum evidence fields required by upper applications.

- [x] **Step 1: Add table-driven tests for representative processors**

Add or extend tests in:

```text
OneOPS/app/device_collection2/fact/*_test.go
```

Representatives:

```text
device_identity
interface
interface_ip
topology_neighbor
mac_table_entry
arp_entry
```

Each test should assert:

```text
quality.valid is true for accepted facts
quality.confidence is greater than 0
provenance.contract_key matches StandardRow.ContractKey
provenance.dataset_key matches StandardRow.DatasetKey
provenance.processor_key is non-empty
provenance.processor_version is non-empty
provenance.source_fields is non-empty when a source field contributes to identity or application fields
```

- [x] **Step 2: Run fact tests**

Run:

```bash
cd OneOPS
go test ./app/device_collection2/fact -count=1
```

Expected:

```text
ok .../app/device_collection2/fact
```

Implementation note:

```text
Added TestRepresentativeProcessorsPopulateProvenanceAndQualityContract.
```

## Task 4: Verify Latest Projection Preserves Evidence Fields

Purpose:

- Ensure latest facts remain useful for IPAM and NetPath evidence drilldown.

- [x] **Step 1: Add service-level latest projection test**

Add or extend tests in:

```text
OneOPS/app/device_collection2/service/impl/device_collection2_test.go
```

The test should:

```text
call ProcessFacts with persist enabled
query ListLatestFacts for the target and fact type
assert fields, quality, provenance, valid, confidence, and observed_at are preserved
```

- [x] **Step 2: Verify overwrite behavior is explicit**

Add a second fact with the same:

```text
target_id + fact_type + identity_key
```

Assert:

```text
latest row updates to the newer fact
history row remains queryable from device_collection2_fact
```

- [x] **Step 3: Run service tests**

Run:

```bash
cd OneOPS
go test ./app/device_collection2/service/impl -run 'Test.*Fact|Test.*Latest' -count=1
```

Expected:

```text
ok .../app/device_collection2/service/impl
```

Implementation note:

```text
Added TestProcessFactsLatestPreservesEvidenceAndHistoryOnOverwrite.
```

## Task 5: Record Tenant Scope Blocker For Latest Facts

Purpose:

- Make the tenant risk visible before NetPath or IPAM projection rely on unscoped latest facts.

- [x] **Step 1: Add a focused failing or skipped test if current API cannot express tenant scope**

Candidate file:

```text
OneOPS/app/device_collection2/service/impl/device_collection2_test.go
```

If tenant scoping cannot be represented today, add a skipped test with a clear message:

```go
t.Skip("tenant-scoped latest fact query is not implemented; required before production NetPath/IPAM projection")
```

The skipped test should describe:

```text
given facts from two tenants
when querying latest facts for tenant A
then tenant B facts must not appear
```

- [x] **Step 2: Link blocker in docs**

Update:

```text
docs/superpowers/specs/2026-06-19-oneops-canonical-fact-inventory.md
```

Expected:

```text
Tenant scope gap links to the skipped or failing test name.
```

Implementation note:

```text
Added skipped blocker test TestListLatestFactsTenantScopeNotImplemented.
Linked it from oneops-canonical-fact-inventory.md.
```

## Task 6: Create Follow-Up Phase Links

Purpose:

- Keep the master plan connected to the next implementation plans.

- [x] **Step 1: Update master board**

Update:

```text
docs/superpowers/plans/2026-06-19-oneops-fact-application-foundation-master-plan.md
```

Expected:

```text
Phase 1 references this hardening plan.
Phase 2 references IPAM projection plan.
Phase 4 references route_table canonical fact plan.
```

- [x] **Step 2: Run documentation checks**

Run:

```bash
PATTERN='TB[D]|TO[DO]|implement la''ter|fill in de''tails'
rg -n "$PATTERN" \
  docs/superpowers/specs/2026-06-19-oneops-canonical-fact-contract-design.md \
  docs/superpowers/specs/2026-06-19-oneops-canonical-fact-inventory.md \
  docs/superpowers/plans/2026-06-19-oneops-canonical-fact-contract-phase1.md \
  docs/superpowers/plans/2026-06-19-oneops-canonical-fact-contract-hardening-phase1.md \
  docs/superpowers/plans/2026-06-19-oneops-fact-application-foundation-master-plan.md
```

Expected:

```text
no output
```

## Completion Criteria

Phase 1 hardening is complete when:

- current processor identity behavior is covered by tests
- quality and provenance are covered for representative processors
- latest projection evidence preservation is tested
- tenant scope blocker is either tested or explicitly skipped with a tracked reason
- master plan links to Phase 2 and Phase 4 plans
