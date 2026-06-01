# Worker Profile Mapping

This note maps current OpenClaw loops to recommended worker capability
profiles.

The purpose is to stop treating all loops as if they were the same kind of
worker job.

## Stable Mappings

### `qwen-realcode-smoke` and `qwen-complex-*`

Recommended profile:

- `qwen-local-patch-worker`

Why:

- copied workspace;
- one bounded story;
- tiny patch width;
- controller verify on `DONE`;
- recovery from `controller-validation-failed`.

### `ct`

Recommended profile:

- `shell-validation-worker`

Why:

- validation-only lane;
- shell turn instead of model turn;
- evidence and issue writing only;
- no product implementation responsibility.

### `dev-docs`

Recommended profile:

- `doc-fact-draft-worker`

Why:

- output is a candidate document, not product code;
- correctness depends on fact extraction discipline, template discipline, and
  explicit `[待确认]` boundaries;
- failure mode is fact/speculation mixing, not patch drift.

## Split Mappings

These loops currently mix multiple task kinds and should be interpreted as
orchestrator lanes, not single worker capability lanes.

### `d2-fe`

The current loop mixes:

- `product_implementation`
- `browser_verification`
- coordination/evidence update

Recommended split:

- `product-implementation-worker` for code changes;
- `browser-verification-worker` for real browser evidence;
- shared coordination remains outside direct product editing.

### `d2-be`

The current loop mixes:

- `product_implementation`
- `readonly_discovery`
- contract/evidence synthesis

Recommended split:

- `product-implementation-worker`;
- `readonly-discovery-worker`;
- optional `coordination-only` lane for FE-facing contract summaries.

### `d2on`

The current loop is the clearest overloaded example. It mixes:

- `product_implementation`
- `browser_verification`
- `readonly_discovery`
- `remote_readonly`
- future `remote_apply`
- development-document updates

This should not be treated as one weak-worker lane.

Recommended split:

- `product-implementation-worker`
- `browser-verification-worker`
- `readonly-discovery-worker`
- `remote-apply-worker`
- `doc-fact-draft-worker`

The top-level `d2on` loop can remain as orchestration, but stories should be
compiled into one of those narrower lanes before dispatch.

## Adaptation Guidance

If a loop needs more than one primary task kind, do not solve it by making the
worker prompt longer.

Instead:

1. classify the current story by task kind;
2. select a capability profile that matches that task kind;
3. compile a story execution pack for that profile;
4. keep the orchestration lane responsible for handoff, join, and truth
   reconciliation.
