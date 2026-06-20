# OneOPS Canonical Fact Contract Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze and verify the first OneOPS canonical fact contract so upper-level applications can safely consume Device Collection 2 facts.

**Architecture:** Keep the existing DC2 fact model as the shared envelope. Add documentation, inventory, and focused tests before changing application consumers. Treat missing fact types such as `arp_entry` and `route_table` as explicit gaps rather than implicit future behavior.

**Tech Stack:** Go, GORM, MySQL models, existing `OneOPS/app/device_collection2` processors and APIs, superpowers documentation.

---

## Phase Status

Status: in progress.

Controller:

- main Codex thread coordinates.
- gpt-5.4 explorer agents inspect independent domains.
- implementation changes should wait until this inventory is complete.

## Source Documents

- `docs/superpowers/specs/2026-06-19-oneops-fact-application-foundation-design.md`
- `docs/superpowers/plans/2026-06-19-oneops-fact-application-foundation-master-plan.md`
- `docs/superpowers/specs/2026-06-19-oneops-canonical-fact-contract-design.md`

## Workstreams

### Workstream A: DC2 Fact Inventory

Owner mode: explorer, then implementation plan.

- [x] Dispatch gpt-5.4 explorer for DC2 fact model and processors.
- [x] Record existing fact types, processor keys, accepted dataset keys, identity rules, quality, and provenance behavior.
- [x] Mark missing or weak fact types.
- [ ] Decide the smallest test additions needed to enforce the contract.

### Workstream B: Obsflow Snapshot Contract Inventory

Owner mode: explorer, then implementation plan.

- [x] Dispatch gpt-5.4 explorer for obsflow batch, processing, snapshot, and apply semantics.
- [x] Record current snapshot fields produced by L2 tasks.
- [x] Record readiness and state semantics.
- [x] Identify which snapshot semantics can be reused by IPAM and NetPath.

### Workstream C: IPAM Projection Inventory

Owner mode: explorer, then implementation plan.

- [x] Dispatch gpt-5.4 explorer for IPAM fact, audit, request, and statistics code.
- [x] Record current `ipam_address_fact` identity and metadata behavior.
- [x] Identify exactly which source metadata is missing for canonical projection.
- [x] Propose the smallest IPAM projection phase plan.

### Workstream D: NetPath Snapshot Gap Inventory

Owner mode: explorer, then implementation plan.

- [x] Dispatch gpt-5.4 explorer for NetPath engine, service, provider, and route fact gaps.
- [x] Record route table requirements and provider gaps.
- [x] Identify what can be planned before route collection exists.
- [x] Propose the smallest route table canonical fact phase plan.

## Expected Phase 1 Outputs

- [ ] Update `docs/superpowers/specs/2026-06-19-oneops-canonical-fact-contract-design.md` with explorer-backed exact code facts.
- [x] Add `docs/superpowers/specs/2026-06-19-oneops-canonical-fact-inventory.md`.
- [x] Add follow-up implementation plan for contract tests and hardening.
- [ ] Update the master tracking board in `docs/superpowers/plans/2026-06-19-oneops-fact-application-foundation-master-plan.md`.

## Validation

Documentation validation:

```bash
PATTERN='TB[D]|TO[DO]|implement la''ter|fill in de''tails'
rg -n "$PATTERN" \
  docs/superpowers/specs/2026-06-19-oneops-canonical-fact-contract-design.md \
  docs/superpowers/plans/2026-06-19-oneops-canonical-fact-contract-phase1.md
```

Expected:

```text
no output
```

Code validation for future hardening:

```bash
cd OneOPS
go test ./app/device_collection2/fact ./app/device_collection2/service/impl
```

Expected:

```text
ok .../app/device_collection2/fact
ok .../app/device_collection2/service/impl
```

## Next Phase Entry Criteria

Phase 2 IPAM fact projection can start when:

- canonical `interface_ip`, `mac_table`, and planned `arp_entry` contracts are clear;
- IPAM source metadata gaps are recorded;
- projection idempotency requirements are written.

Phase 4 route table canonical fact can start when:

- `route_table` required fields and identity key are accepted;
- invalid route handling is specified;
- NetPath provider requirements are linked to the route fact contract.

## Follow-Up Plans

- `docs/superpowers/plans/2026-06-19-oneops-canonical-fact-contract-hardening-phase1.md`
- `docs/superpowers/plans/2026-06-19-oneops-ipam-fact-projection-phase2.md`
- `docs/superpowers/plans/2026-06-19-oneops-route-table-canonical-fact-phase4.md`
