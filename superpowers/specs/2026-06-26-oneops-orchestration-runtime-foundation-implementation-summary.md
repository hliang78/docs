# OneOps Orchestration Runtime Foundation Implementation Summary

## Goal

This implementation closes the lightweight MVP loop for the orchestration runtime foundation described in:

- `docs/superpowers/specs/2026-06-26-oneops-orchestration-runtime-foundation-design.md`
- `docs/superpowers/plans/2026-06-26-oneops-orchestration-runtime-foundation-implementation-plan.md`

The delivered runtime keeps `OneOps` as the persistence and integration owner, keeps `dagengine` as the execution kernel, and adds a thin runtime layer between compiled DAG nodes and capability execution.

## Delivered Scope

### 1. Shared runtime foundation

Implemented under `OneOps/app/orchestration/runtime`:

- neutral runtime contracts
- runtime registry
- middleware for node lifecycle events and error normalization
- concise execution log model
- structured event model

### 2. Persistent wait and resume

Implemented persistent wait state and resume entrypoints:

- `SuspendRecord`
- waiting-aware fields on `TemplateExecution`
- `ExecutionLog`
- structured `ExecutionEvent`
- callback and approval resume APIs

Waiting is explicit, durable, and resumable. It is no longer simulated through in-memory blocking.

### 3. External call runtime

Implemented the controlled external call slice:

- platform-managed `ExternalTarget`
- target registry resolution
- `external_call_step` runtime
- template and compiler support for external/wait node fields

Templates reference platform-owned targets instead of embedding arbitrary outbound URLs.

### 4. Existing runtime path migrated to runtime registry

The execution path now runs through:

`ExecutionSrv -> compiler -> DagengineAdapter -> RuntimeRegistry -> NodeRuntime -> CapabilityGateway`

The following node types are registered in the runtime path:

- `flow_step`
- `agent_step`
- `external_call_step`
- `callback_wait_step`
- `approval_wait_step`

### 5. Resume-to-continuation closed loop

The MVP loop now supports:

- start execution
- enter `waiting_callback` or `waiting_approval`
- persist suspend record and execution snapshot
- resolve through resume API
- continue execution from the node after the wait node
- finish in a terminal status

Current MVP decisions:

- callback resume merges callback payload into execution context, then continues execution
- approval `approve` continues execution
- approval `reject` routes through the wait node's `on_failure`
- wait timeout handling routes through the wait node's `on_timeout`
- when a wait-node terminal target resolves to `escalated`, runtime persists structured `terminal_outcome` context and emits `execution_action_required`
- orchestration now exposes read-side event outlets for both per-execution event history and aggregated action-required items
- if resume unblocks the wait record but continuation cannot be started, execution is marked `failed`

## Current Runtime Semantics

### Execution statuses

Current top-level execution states used by this MVP:

- `completed`
- `failed`
- `waiting_callback`
- `waiting_approval`

### Suspend record statuses

Suspend records use compact shared persistence statuses:

- `active`
- `resolved`

Business outcomes such as approval `approve` and `reject` are returned through resume response payloads and audit details rather than by expanding suspend record state.

## Important Files

Primary implementation areas:

- `OneOps/app/orchestration/runtime/`
- `OneOps/app/orchestration/service/impl/dagengine_adapter.go`
- `OneOps/app/orchestration/service/impl/execution.go`
- `OneOps/app/orchestration/service/impl/resume.go`
- `OneOps/app/orchestration/service/impl/capability_gateway.go`
- `OneOps/app/orchestration/template/`
- `OneOps/app/orchestration/compiler/`
- `OneOps/app/orchestration/target_registry/`
- `OneOps/app/orchestration/orchestration_model/`

Operator-facing documentation:

- `docs/runbooks/alert-to-ticket-dagengine-mvp.md`

## Verification Run

The implementation was verified with these commands:

```bash
go test ./app/orchestration/service/impl -run 'TestResumeService_(ResumeCallbackContinuesExecutionToCompletion|ResumeCallbackMarksExecutionFailedWhenContinuationCannotStart|ApproveContinuesExecutionToCompletion|RejectMarksExecutionFailed|ResolveCallbackResume|ResumeCallbackPersistsAuditLog|ApproveSuspendedExecution|RejectSuspendedExecution)$' -count=1
go test -parallel 1 ./app/orchestration/runtime ./app/orchestration/service/impl -count=1
go test ./app/orchestration/... ./app/alert_engine/... ./boot/provider ./initialize -count=1
```

## Explicitly Deferred

These are intentionally not part of the current MVP:

- queue or worker based resume execution
- distributed recovery or scheduler redesign
- richer approval policy execution
- execution replay from persisted per-node state

## Handoff Note

If a next phase is opened, the cleanest follow-up slice is:

1. route approval reject through `on_failure`
2. implement timeout-driven `on_timeout`
3. decide whether resumed execution should remain inline or move behind a worker boundary
