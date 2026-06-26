# OneOPS Phase 1 Goal-Oriented Testing Plan

> **For agentic workers:** Use this plan to drive the first operational testing wave under the approved Phase 1 goal-oriented testing design.

**Goal:** turn the Phase 1 design into a concrete operating baseline built around real-device samples, weak-link analysis, and targeted data-combination testing.

**Architecture:** the work starts from customer-facing delivery certainty, then flows through three artifacts in order: real-device sample register, weak-link register, and chain-level targeted test packs. PR core, nightly, and real-world verification are fed from those artifacts rather than invented independently.

**Tech Stack:** shared docs in `docs`, backend validation assets in `OneOPS`, frontend smoke and fixture assets in `OneOPS-UI`, existing envtest and replay harnesses where available.

---

## Phase 1 Operating Sequence

### Task 1: Build the Real-Device Sample Register

**Outcome:** a shared register of the first real devices that define Phase 1.

- [ ] Create the first sample register covering:
  - network devices
  - server devices
  - firewall devices
- [ ] For each sample, record:
  - vendor
  - model family
  - version band
  - protocol path
  - target capability chains
  - current support state
  - evidence source
  - known uncertainty
- [ ] Prefer devices that represent:
  - active customer usage
  - protocol differences
  - known instability
  - future expansion anchors

### Task 2: Build the Weak-Link Register

**Outcome:** a prioritized list of the failure-prone links most threatening delivery certainty.

- [ ] Identify the first weak-link set across:
  - collection
  - monitoring push
  - firewall configuration parsing
  - policy generation
  - policy query
  - topology generation
  - automation script execution
- [ ] For each weak link, record:
  - risk description
  - affected device samples
  - affected chain
  - likely failure signals
  - target evidence needed
  - acceptable boundary if not fully solved in Phase 1
- [ ] Rank each weak link as:
  - P0 delivery blocker
  - P1 high-risk instability
  - P2 important but not first-wave critical

### Task 3: Build the Data-Combination Scenario Library

**Outcome:** reusable targeted scenario packs instead of one-path smoke checks.

- [ ] For each priority real-device chain, define combinations for:
  - normal success
  - missing field
  - dirty data
  - version drift
  - protocol-return variant
  - timeout or retry
  - partial result
  - large-volume case where relevant
- [ ] Attach each combination to:
  - a real-device sample
  - a weak link
  - an expected outcome
  - a boundary explanation

### Task 4: Build Chain-Level Test Packs

**Outcome:** targeted test packs aligned to real delivery paths.

- [ ] Create first-wave chain packs for:
  - ingest -> collect -> monitor
  - collect -> parse -> read model
  - config parse -> policy query -> policy generation
  - topology source -> relation build -> topology render
  - automation task issue -> execution -> result collection
- [ ] For each pack, define:
  - source truth
  - transformed truth
  - runtime truth
  - operator-visible truth
  - success evidence
  - failure boundary evidence

### Task 5: Map Tests Into PR Core, Nightly, And Real-World Layers

**Outcome:** execution layering follows risk and evidence value.

- [ ] Put only the highest-certainty, highest-value targeted checks into PR core.
- [ ] Put broader replay, larger combination sets, and heavier scenario packs into nightly.
- [ ] Reserve highest-value real-device validation for real-world verification and milestone checks.
- [ ] For every test pack, mark exactly one primary execution layer and optional secondary layer.

### Task 6: Establish the Boundary Ledger

**Outcome:** unsupported or partial support becomes explicit delivery knowledge.

- [ ] For each device sample and capability chain, record one of:
  - supported with evidence
  - partially supported with boundary
  - unsupported with explicit reason
  - unknown and scheduled
- [ ] Make the ledger visible to:
  - testing decisions
  - release decisions
  - customer-facing expectation setting

### Task 7: Produce the Phase 1 Validation Snapshot

**Outcome:** a customer-facing confidence snapshot grounded in evidence.

- [ ] Summarize which device families have first-wave evidence.
- [ ] Summarize which chains are green, partial, blocked, or unknown.
- [ ] Summarize which weak links remain open.
- [ ] Summarize which boundaries are already clear enough for controlled delivery.

## Phase 1 Completion Standard

Phase 1 should be considered operationally established when all of the following are true:

- the first real-device sample register exists and is shared
- the first weak-link register exists and is prioritized
- the first data-combination scenario library exists
- the first chain-level test packs exist
- PR core and nightly both draw from those artifacts
- the boundary ledger is being updated as a first-class output
- the team can explain support certainty by device family and capability chain
