# Runtime Rules Reference

This is the compact runtime guardrail reference for OpenClaw autodev loops.

## Bounded Turn Rule

- one current story per worker turn;
- one bounded block per loop run by default;
- one compact final footer per turn;
- one deterministic handoff file after each turn.

## Truth Rule

The authoritative result is the latest ended worker trajectory with a valid
`LoopControl` footer.

Local files such as `last-report.txt`, `last-control`, `state.json`, and
`current-story.json` are projections that must reconcile back to that truth.

## Story Rule

- workers act only on the selected story;
- `DONE` closes the current story only;
- `CONTINUE` means the same story still needs another bounded turn;
- `BLOCKED` and `APPROVAL` keep the story selectable for repair/approval flow.

## Context Rule

- prefer current story, handoff, approval, and compact context docs;
- keep prompt budget bounded;
- truncate large context with an explicit marker;
- do not rely on broad workspace persona/identity context for business work.

## Verification Rule

- worker confidence is never enough for final completion;
- configured validation must run before `DONE`;
- controller verify should rerun on `DONE` for weaker workers;
- if controller verify disproves `DONE`, task truth must be rewritten to
  `controller-validation-failed`.

## Recovery Rule

- classify the blocker before retrying;
- use provider-check and cleanup only for automation/runtime classes;
- use repair agents for environment or tool blockers;
- after repeated failed recoveries, stop the smallest affected lane and preserve
  evidence/handoff.

## Approval Rule

Stop and ask before:

- writing outside allowed paths;
- deleting files;
- broad validation outside configured acceptance;
- adding/upgrading dependencies;
- changing production config, migrations, auth, tenant logic, credentials, or
  real external integrations;
- committing, pushing, merging, or deploying;
- continuing after repeated failed repairs.

## Evidence Rule

When code, docs, runtime, or remote actions matter, the task should leave
durable evidence that records:

- what claim is being made;
- which source produced that claim;
- what command or validation ran;
- what redaction boundary was applied;
- what residual risk remains.

See also:

- `docs/openclaw-autodev/reliability-model.md`
- `docs/openclaw-autodev/handoff-schema.json`
- `docs/openclaw-autodev/evidence-schema.json`
