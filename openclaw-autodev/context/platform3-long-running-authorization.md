# Platform3 Long-Running Authorization

This authorization remains effective for the Platform3 sustained-development loop until PF3 is completed or the operator explicitly revokes it through Weixin.

## Authorized Write Scope

PF3 workers may modify:

- `app/platform/**`
- `app/platform3/**`
- `docs/platform3/**`
- `/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/evidence/platform3/**`

## Non-Negotiable Behavior Guard

Current `app/platform` behavior must not change.

Allowed `app/platform` changes are limited to behavior-preserving wiring, no-op-by-default integration points, tests, instrumentation, equivalent refactors, and explicitly safe shadow/compare-only Platform3 hooks.

Forbidden without a new explicit approval:

- route or API behavior changes
- request/response schema or semantic changes
- permission/auth behavior changes
- persistence/write behavior changes
- default config changes
- production feature enablement
- live canary, live adapter, ownership transfer, or rollback execution
- commit, push, dependency changes, migrations, destructive operations

If a useful PF3 step requires changing existing `app/platform` behavior, the worker must stop with `LoopControl: APPROVAL` or `LoopControl: BLOCKED` and describe the required behavior change.

## Required Validation

Any turn touching `app/platform/**` must run or explicitly block on:

- `cd /Users/huangliang/project/OneOPS-ALL/OneOPS && go test ./app/platform/...`
- `cd /Users/huangliang/project/OneOPS-ALL/OneOPS && go test ./app/platform3/...`

Targeted regression tests must prove legacy Monitoring V2 behavior is unchanged when Platform3 is disabled, shadow-only, or failing.
