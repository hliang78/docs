# OneOps Orchestration Action-Required Records Design

## 1. Purpose

The current orchestration runtime can already emit `execution_action_required` events when a wait path reaches an `escalated` terminal outcome.

That is enough for observability, but not enough for real operator takeover.

Today the system can answer:

- an execution required human follow-up
- why it required follow-up
- which execution and node produced the escalation

But it still cannot reliably answer:

- who has claimed the follow-up
- whether it is still pending
- whether it was resolved
- what resolution was applied
- how to reopen or continue operational tracking

This design adds a first-class **action-required record model** owned by OneOps so operator takeover becomes a real platform capability rather than a derived event view.

## 2. Goal

Build the smallest production-meaningful operator takeover model for orchestration:

- action-required items are persisted as first-class records
- runtime still emits audit events
- operators can list, claim, resolve, and inspect current follow-up items
- execution observability uses the action-required record as the live state source

This is an M1/M1.5 capability, not a full generic work management system.

## 3. Non-Goals

This design does **not** attempt to build:

- a full ticket workflow engine
- SLA timers, escalation ladders, or reminders
- a generic approval center
- assignment rules or load-balancing
- a universal operations workbench
- multi-step human collaboration flows
- notification fan-out logic

Those may come later, but are intentionally excluded now to avoid turning the orchestration platform into a side project.

## 4. Design Principles

### 4.1 Events remain audit artifacts

`execution_action_required` remains useful and should continue to exist in execution timelines.

It is the audit/event layer.

It should not remain the only source of current operator state.

### 4.2 Records become the live state layer

The new action-required record becomes the source of truth for:

- current pending items
- claim status
- resolution status
- operator notes

### 4.3 One record per operational follow-up

When the runtime decides a node has reached an operator-follow-up state, OneOps should create one persisted record for that operational follow-up.

The platform should not recompute “current pending items” by rescanning raw events each time.

### 4.4 Keep the first version narrow

This version should only support the lifecycle needed now:

- create
- list
- claim
- resolve
- inspect

Anything beyond that should be explicitly deferred.

## 5. Runtime Position

The execution path remains:

`ExecutionSrv -> compiler -> DagengineAdapter -> ResumeSrv / runtime continuation`

The new action-required persistence is inserted inside the terminal escalation path owned by OneOps:

`resume / timeout / reject path -> terminal outcome = escalated -> emit execution event + persist action-required record`

This keeps:

- dagengine as execution kernel
- orchestration runtime as control plane
- OneOps as persistence owner

## 6. Data Model

### 6.1 New table

Add a new table:

- `orchestration_action_required_records`

### 6.2 Core identity fields

- `id`
- `execution_id`
- `node_id`
- `node_type`
- `source_event_id`

These fields tie the record back to the runtime event and execution context.

### 6.3 Business context fields

- `template_code`
- `environment`
- `alert_code`
- `ticket_code`

These are denormalized for fast operator lookup and UI rendering.

### 6.4 Action semantics fields

- `action_type`
  - example: `operator_intervention`
- `action_key`
  - example: `escalate`
- `route_field`
  - `on_failure` or `on_timeout`
- `terminal_status`
  - normally `escalated`
- `reason`

These preserve why the record exists.

### 6.5 Operator lifecycle fields

- `status`
  - `pending`
  - `claimed`
  - `resolved`
  - `cancelled`
- `claimed_by`
- `claimed_at`
- `resolved_by`
- `resolved_at`
- `resolution_code`
- `resolution_note`

### 6.6 Payload fields

- `payload_json`

This stores the source action-required payload for future compatibility without forcing schema expansion for every new detail.

### 6.7 Timestamps

- `created_at`
- `updated_at`

## 7. Record Lifecycle

### 7.1 Creation

When runtime reaches an `escalated` terminal outcome and emits `execution_action_required`, OneOps also persists one new action-required record.

Initial state:

- `status = pending`
- `claimed_* = empty`
- `resolved_* = empty`

### 7.2 Claim

An operator can claim a pending record.

Result:

- `status = claimed`
- `claimed_by` set
- `claimed_at` set

Claim should also be allowed as a takeover refresh for the same operator if already claimed by that operator.

### 7.3 Resolve

An operator can resolve a pending or claimed record.

Result:

- `status = resolved`
- `resolved_by` set
- `resolved_at` set
- `resolution_code` set
- `resolution_note` optionally set

Resolving the record does **not** automatically mutate the execution state retroactively.

Execution remains the runtime truth.

The action-required record only tracks the human operational follow-up lifecycle.

### 7.4 Cancel

`cancelled` is reserved for system-side invalidation or future workflows.

The first implementation does not need a public cancel action.

## 8. API Design

### 8.1 List action-required records

Reuse the existing list surface conceptually:

- `GET /orchestration/executions/action-required`

But change its backing source from raw event scan to action-required records.

The response should include:

- record id
- execution id
- node id / node type
- template / environment
- alert / ticket
- action key / reason
- route field / terminal status
- current record status
- claim metadata
- created / updated timestamps

### 8.2 Claim action-required record

Add:

- `POST /orchestration/executions/action-required/:id/claim`

Request body:

- `operator`
- optional `note`

Behavior:

- pending -> claimed
- claimed by same operator -> idempotent success
- claimed by different operator -> conflict
- resolved/cancelled -> reject

### 8.3 Resolve action-required record

Add:

- `POST /orchestration/executions/action-required/:id/resolve`

Request body:

- `operator`
- `resolution_code`
- optional `resolution_note`

Behavior:

- pending -> resolved
- claimed -> resolved
- resolved -> idempotent or reject based on current code path policy

For MVP, idempotent success is acceptable if the same resolution is repeated.

### 8.4 Single-record detail

Optional but recommended:

- `GET /orchestration/executions/action-required/:id`

This is useful for UI deep-linking and operator detail panels.

If we want to stay lighter, the first UI can operate from list data only.

## 9. Runtime Integration

### 9.1 ResumeSrv integration point

The action-required record should be created in the same path that currently:

- persists terminal escalated outcome
- emits `execution_action_required`

That keeps creation atomic relative to orchestration-owned runtime handling.

### 9.2 Failure behavior

If the action-required record cannot be created but the execution has already reached an escalated terminal state, the failure must be logged loudly.

Preferred first-pass behavior:

- fail the same transaction if creation is part of the same persistence unit
- do not silently drop the record

The system should bias toward consistency between:

- escalated execution state
- emitted action-required event
- persisted action-required record

## 10. Read Path Changes

### 10.1 Observatory list

The observatory `Action Required` tab should read the new record model instead of reconstructing items from events.

### 10.2 Execution detail page

The execution detail debugger should show:

- whether a live action-required record exists
- record status
- claimed by
- resolution note if resolved

### 10.3 Summary

Execution summary’s `action_required` count should count open action-required records, not only raw event presence.

For the first pass:

- count `pending + claimed`
- exclude `resolved + cancelled`

## 11. Concurrency and Idempotency

### 11.1 Create path

Creation should avoid duplicate active records for the same source event.

The simplest first-pass method:

- unique index on `source_event_id`

### 11.2 Claim path

Claim should be conditional on current status.

Expected optimistic transition:

- update where `id = ? and status = 'pending'`

### 11.3 Resolve path

Resolve should also be conditional on current status.

Expected optimistic transition:

- update where `status in ('pending', 'claimed')`

## 12. Migration Strategy

### 12.1 No backfill required for MVP

This capability can start from new runtime-generated records only.

Historical action-required events do not need immediate backfill into records.

### 12.2 Existing event API compatibility

Existing consumers expecting action-required list data should still receive equivalent or better fields.

That means:

- preserve route/reason/action semantics in list responses
- add lifecycle fields without removing current core fields

## 13. UI Scope

### 13.1 Included now

- list current action-required records
- show status `pending/claimed/resolved`
- claim action
- resolve action
- reflect state in execution detail

### 13.2 Excluded now

- bulk operations
- advanced filtering UI beyond current page patterns
- separate operations workbench
- reminder/escalation UX

## 14. Testing Strategy

### 14.1 Backend

Add tests for:

- escalated runtime path creates both event and record
- list API returns records with live status
- claim transition success
- claim conflict
- resolve transition success
- resolved items excluded from open summary counts

### 14.2 UI

Add smoke/assertion coverage for:

- action-required list status rendering
- claim/resolve action presence
- execution detail shows live record state

## 15. Acceptance Criteria

This design is complete when:

- an escalated execution creates a persisted action-required record
- operators can list pending items from the platform
- an operator can claim and resolve an item through real APIs
- the observatory and detail page reflect live operator state
- the platform no longer relies on raw events alone to represent current operational follow-up

## 16. Recommended Implementation Order

1. Add new record model and migration
2. Persist record during escalated terminal handling
3. Switch list/read APIs to record-backed reads
4. Add claim/resolve APIs
5. Update observatory and detail page
6. Add verification and runbook updates

## 17. Why This Is The Right Next Step

This design keeps the platform on the mainline:

- runtime remains stable
- OneOps stays the persistence and experience owner
- operator takeover becomes real
- the system gets more production-meaningful without over-expanding scope

It is small enough for MVP discipline, but meaningful enough to avoid toy behavior.
