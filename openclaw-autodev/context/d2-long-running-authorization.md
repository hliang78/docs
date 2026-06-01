# D2 Long-Running Authorization

This authorization remains effective for the D2 sustained-development loops until D2 is completed or the operator explicitly revokes it through Weixin.

## Authorized FE Write Scope

`d2-fe` workers may modify D2-related frontend code under:

- `src/views/device/**`
- `src/api/device/**`
- `src/router/**` when the route is D2/device related
- `docs/device-v2-ui-autodev/**`
- `/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/evidence/d2-fe/**`
- `/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/shared-d2.md`

`d2-fe` must not modify `OneOPS/**`.

## Authorized BE Write Scope

`d2-be` workers may modify D2/device-related backend code under:

- `app/device/**`
- `docs/device-v2-ui-autodev/**`
- `/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/evidence/d2-be/**`
- `/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/shared-d2.md`

`d2-be` must not modify `OneOPS-UI/**`.

## Non-Negotiable Behavior Guard

Existing old-code behavior must not change unless the operator gives a new explicit approval.

Allowed old-code changes are limited to behavior-preserving refactors, extraction into smaller helpers, tests, type/interface tightening that preserves runtime behavior, deterministic validation, no-op-by-default integration points, and explicit D2 redesign wiring that keeps legacy behavior unchanged.

Forbidden without a new explicit approval:

- route, menu, navigation, or permission behavior changes outside the D2/device scope
- existing API request/response schema or semantic changes
- existing persistence/write behavior changes
- default config changes
- feature enablement, production route switching, or replacing old entrypoints with redesign entrypoints
- fallback branches, mock data, pseudo-success, swallowed errors, or silent defaults
- dependency changes, migrations, destructive operations, commit, or push

If a useful D2 step requires changing old-code behavior, the worker must stop with `LoopControl: APPROVAL` or `LoopControl: BLOCKED` and describe the required behavior change.

## Required Validation

Any `d2-fe` turn touching old frontend code must run or explicitly block on:

- `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run typecheck:d2`
- `/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-d2-runtime.sh ensure-backend`
- `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run smoke:d2-redesign-browser` when visible D2 behavior changes

Any `d2-be` turn touching old backend code must run or explicitly block on:

- `cd /Users/huangliang/project/OneOPS-ALL/OneOPS && go test ./app/device/...`
- `cd /Users/huangliang/project/OneOPS-ALL/OneOPS && go test ./app/device/v2/...`

Targeted regression evidence must prove existing old-code behavior remains unchanged for the affected D2/device path.
