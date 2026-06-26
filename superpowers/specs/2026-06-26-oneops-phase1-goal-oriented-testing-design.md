# OneOPS Phase 1 Goal-Oriented Testing Design

## Goal

Build a Phase 1 testing strategy that is driven by customer delivery confidence rather than module-level completeness.

Phase 1 should prove that OneOPS can support more real devices with evidence, and that the platform behaves predictably across:

- device collection
- monitoring push
- firewall configuration parsing
- policy generation
- policy query
- topology generation
- automation script execution

The key design constraint is that testing must be based on real-device samples, deliberate data combinations, and weak-link analysis.

## Core Position

Phase 1 is not a broad "test more features" effort.

Phase 1 is a targeted verification program that answers:

1. Which real devices are actually supported?
2. Which capability chains are verified on those devices?
3. Which data variations and protocol differences break the chains?
4. Which weak links most threaten customer delivery confidence?
5. Which unsupported or partial cases already have clear operational boundaries?

## Testing Unit

The primary testing unit is not a module or an API.

The primary testing unit for Phase 1 is:

`real device family + protocol path + capability chain + data combination + expected boundary`

Example units:

- Huawei switch + SNMP + ingest -> collect -> monitor + normal inventory payload + supported
- H3C switch + SSH + collect -> parse -> topology + missing interface metadata + partial support with boundary
- Firewall family + SSH/API + config parse -> policy query -> policy generation + version-drift config sample + weak-link investigation
- Linux server + SSH + collect -> monitor push -> automation script + timeout/retry payload + resilience validation

## Phase 1 Strategy

### 1. Real-Device Sample Set First

Phase 1 starts by selecting a finite but representative real-device sample set.

Each sample should be chosen because it represents one or more of:

- important customer device family
- protocol path already in active use
- high-risk adaptation area
- known parsing drift or unstable behavior
- future expansion anchor for similar devices

The Phase 1 sample set should be organized by:

- network devices
- server devices
- firewall devices

For each sample, record:

- vendor
- model family
- OS or firmware version band
- protocol(s)
- target capability chains
- current support status
- current evidence location
- known unknowns

### 2. Data Combination Library

Each real-device sample must be tested through deliberate data combinations, not only a single happy path.

Phase 1 combinations should include at least:

- normal success payload
- missing field payload
- dirty or inconsistent payload
- version-drift payload
- protocol-return variant
- timeout or retry condition
- partial-result condition
- large-volume condition where applicable

The purpose is to verify how the platform behaves when the shape of reality changes.

### 3. Weak-Link-Driven Test Design

Phase 1 test design should not distribute effort evenly.

The first priority is to identify and attack weak links that most threaten delivery certainty.

Typical weak-link categories:

- data acquisition fragility
- parser drift across device variants
- mapping and normalization ambiguity
- monitoring task distribution and push consistency
- firewall configuration structure variance
- policy generation precheck and rule composition correctness
- policy query and compare result correctness
- topology relation inference instability
- automation script compatibility across device differences
- error explanation and boundary visibility

For each weak link, define:

- why it is risky
- what real-device sample exposes it
- what data combinations pressure it
- what evidence proves it is stable
- what boundary is acceptable if it is not yet fully supported

### 4. Chain-Level Verification

A device is not counted as supported because one step succeeds once.

Phase 1 verifies support at the capability-chain level.

Each chain should be tested as a sequence with truth checks between stages.

Examples:

- ingest -> collect -> monitor
- collect -> parse -> read model
- config parse -> policy query -> policy generation
- topology source -> relation build -> topology render
- automation task issue -> execution -> result collection

Each chain should explicitly identify:

- source truth
- transformed truth
- runtime truth
- operator-visible truth

### 5. Boundary as Deliverable

Unsupported or partial cases are acceptable only if the boundary is explicit.

Phase 1 therefore treats boundary definition as part of the test output.

For each real-device chain, the outcome must be one of:

- supported with evidence
- partially supported with clear boundary
- unsupported with explicit reason
- unknown and queued for targeted validation

## Execution Model

### PR Core

Use PR core only for the highest-risk paths that protect current customer-facing certainty.

Phase 1 PR core should favor:

- fast fixture-backed chain checks
- parser and precheck contract checks
- read-model and operator-signal checks
- any weak-link regression already turned into stable smoke or fixture coverage

### Nightly

Nightly is where Phase 1 expands breadth.

Nightly should carry:

- wider real-device replay coverage
- more data combinations
- heavier multi-step scenario checks
- expanded weak-link regression packs

### Manual / Real-World

Manual and real-world verification should validate the highest-value device samples and refresh confidence where offline fixtures may drift away from field reality.

## Deliverables

Phase 1 should produce these concrete artifacts:

1. real-device sample register
2. data-combination scenario library
3. weak-link register with priority
4. capability-chain coverage matrix
5. PR core targeted regression set
6. nightly expanded regression set
7. boundary ledger for unsupported and partial support cases
8. evidence-backed validation snapshots for major chains

## Acceptance Criteria

Phase 1 is successful when:

1. testing work is clearly organized around real devices, not only around code modules
2. every priority device sample has named capability chains and evidence state
3. every priority chain has deliberate data-combination coverage
4. weak links are explicitly ranked and attached to targeted tests
5. support, partial support, and unsupported boundaries are all visible
6. the team can explain customer-facing certainty with evidence instead of intuition

## Immediate Next Step

The next document and execution step after this design should be a Phase 1 operating plan that lists:

- the first real-device sample set
- the first weak-link list
- the first chain-by-chain test packs
- which items belong in PR core, nightly, and real-world verification
