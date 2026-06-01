# PRD Convergence Notes

Status: ready for user review before OpenClaw story publication.

## What Is Now Stable

- The program goal is OneOps online quality gates, not customer PoC execution.
- All 7 workstreams have first-round P0/P1 scope decisions.
- Evidence must be combination evidence and stored under this PRD program's `evidence/`.
- The final evidence system must produce fixed Chinese summaries, matrix updates, readiness summary and machine-readable JSON.

## Recommended First Cut

Start with batch-001: WS-01 Device Field Gate Baseline Preparation.

This is intentionally narrower than the full WS-01 scope. It should establish:

- actual `ONEOPS_GATE_*` fixture inventory from the test DB;
- per-device maximum verifiable field manifests derived from `D2_INGEST_BASE_FIELD_TABLE.md`, collected evidence and platform fields;
- Device V2 / DC2 / UI evidence paths;
- first fixed Chinese evidence summary and machine-readable status JSON.

## Why This First

Device fixture integrity is the dependency underneath:

- monitoring target and label validation;
- syslog/tail source attribution;
- topology node/interface/edge validation;
- alert trigger object identity;
- credential/automation target selection;
- firewall policy object lookup and audit correlation.

## OpenClaw Boundary

The user confirmed these publishing preconditions on 2026-05-14:

- batch-001 scope;
- DB credential injection method;
- evidence write location;
- whether `test-matrix.md` can be updated by the story.

Batch-001 is now reviewed and ready to publish on explicit instruction.

## Remaining Details By Category

Execution-blocking before batch-001:

- None for PRD handoff. Runtime execution still requires DB password to be provided by environment or local secret.

Story-internal exploration:

- Fixture field expectation manifest.
- Evidence summary template.
- Batch status JSON schema.
- Device V2 / DC2 evidence command map.

Deferred beyond batch-001:

- Monitoring/log/topology execution.
- Agent lifecycle execution.
- Alert device shutdown trigger.
- Credential write/remote execution.
- Real LLM automation.
- Firewall policy query and CLI config generation.
