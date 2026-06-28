# OneOps AgentRuntime First Production Design

## 1. Goal

Upgrade the current `agentruntime` from an in-memory demo executor into a first-production runtime suitable for initial real-world deployment.

This version must:

- support real multi-agent task execution behind OneOps orchestration
- persist agent tasks before execution
- recover unfinished tasks after process restart
- separate task execution from callback delivery
- support explicit service-to-service authentication
- remain lightweight enough to ship without Redis, Kafka, or a full distributed queue platform

This version does not target high availability or horizontal scale as the primary objective. It targets safe first production rollout.

## 2. Scope

### Included

- persistent `agentruntime` task storage in MySQL
- worker-based execution instead of request-scoped goroutines
- persisted callback retry and recovery semantics
- production-ready task status machine
- service-to-service callback authentication
- configuration model for runtime URLs, retry policy, and timing
- minimal operational visibility for runtime health and task state

### Excluded

- Redis queue
- Kafka or MQ redesign
- multi-instance active-active worker coordination beyond DB claim semantics
- generic plugin marketplace for agent roles
- user-defined arbitrary agent teams
- advanced human intervention console for runtime internals

## 3. Current State

Today the runtime behavior is:

1. OneOps sends a task to `POST /api/agentruntime/tasks`
2. the runtime validates input
3. it immediately launches a goroutine in memory
4. the goroutine executes the role handler
5. it posts a callback directly to OneOps

This is sufficient for MVP demo and closed-loop validation, but it is not sufficient for first production use because:

- accepted tasks are not durable before execution
- in-flight tasks are lost on process restart
- callback failure is logged but not persisted as a recoverable state
- execution and callback are coupled into one volatile worker path
- operator observability is limited to logs

## 4. Design Principles

### 4.1 OneOps remains workflow owner

OneOps still owns:

- orchestration control flow
- wait and resume semantics
- approval
- escalation and timeout routing
- business execution status

`agentruntime` only owns agent task execution lifecycle.

### 4.2 Persist before execute

No accepted task may depend on request memory for survival. Once `Submit` returns success, the task must already exist in durable storage.

### 4.3 Execution and callback are separate phases

Producing an agent result and delivering that result back to OneOps are different failure domains. They must be represented separately in state.

### 4.4 Recovery is explicit

Restart recovery is not best-effort logging. The runtime must have deterministic rules for reclaiming stale work and replaying pending callbacks.

### 4.5 Lightweight over overbuilt

The first production version must favor:

- one MySQL task table
- one execution worker loop
- one callback retry loop

over queue platform expansion.

## 5. Target Architecture

### 5.1 Submission path

The new request path becomes:

`OneOps -> POST /api/agentruntime/tasks -> validate -> insert task row -> return accepted`

The HTTP handler does not execute the task directly.

### 5.2 Execution path

The execution path becomes:

`execution worker -> claim submitted task -> mark running -> execute role -> persist result -> mark callback_pending`

### 5.3 Callback path

The callback path becomes:

`callback worker -> load callback_pending/callback_retry task -> POST callback to OneOps -> mark completed or callback_retry`

### 5.4 Recovery path

On startup the runtime performs lightweight recovery scans:

- stale `claimed` tasks are returned to `submitted`
- stale `running` tasks are either failed or re-queued according to policy
- `callback_pending` and `callback_retry` tasks are retried

## 6. Runtime Components

### 6.1 Submit API

Responsibilities:

- validate request
- reject malformed or unsupported task type
- write a new task record
- return success only after durable insert

Non-responsibilities:

- do not run the role inline
- do not callback OneOps directly

### 6.2 Task Repository

Responsibilities:

- insert task rows
- claim tasks atomically
- update status and result fields
- list retryable tasks
- recover stale tasks

This repository becomes the state backbone of the runtime.

### 6.3 Execution Worker

Responsibilities:

- poll for executable tasks
- atomically claim a task
- execute the role handler
- persist normalized execution result
- move the task to callback-ready state

### 6.4 Callback Worker

Responsibilities:

- poll callback-ready tasks
- send callback to OneOps
- update callback attempt metadata
- mark task complete on success
- move task to retry or dead state on failure

### 6.5 Role Executor Layer

The existing role handlers remain usable, but they must sit behind a more explicit executor contract.

The runtime should treat a role handler as an execution dependency, not as the task lifecycle owner.

## 7. Task State Machine

The first production state set is:

- `submitted`
- `claimed`
- `running`
- `callback_pending`
- `completed`
- `failed`
- `callback_retry`
- `dead`

### 7.1 State semantics

#### `submitted`

Task is durably stored and available for execution workers.

#### `claimed`

Task has been atomically reserved by a worker but not yet fully entered the execution body. This state prevents duplicate start by concurrent workers.

#### `running`

Task execution is in progress.

#### `callback_pending`

Execution produced a result and persisted it successfully. Callback delivery has not yet succeeded.

#### `completed`

Callback to OneOps succeeded and the task is fully closed.

#### `failed`

Task execution itself failed and should not be retried further under current policy.

#### `callback_retry`

Execution is complete, but callback delivery failed and should be retried later.

#### `dead`

Task exceeded retry or recovery policy and now requires operator inspection.

### 7.2 Allowed transition outline

- `submitted -> claimed`
- `claimed -> running`
- `claimed -> submitted` when claim expires or worker dies early
- `running -> callback_pending`
- `running -> failed`
- `callback_pending -> completed`
- `callback_pending -> callback_retry`
- `callback_retry -> completed`
- `callback_retry -> callback_retry`
- `callback_retry -> dead`

## 8. Claiming and Idempotency

### 8.1 Why `claimed` is required

The runtime must protect against duplicate execution when multiple worker loops or restart races observe the same `submitted` task.

The claim operation must be a conditional database update:

- only rows in `submitted` may be claimed
- the worker writes claim metadata
- only the winner proceeds

### 8.2 Claim metadata

Each task should track enough information to identify ownership and expiry:

- `claimed_by`
- `claimed_at`
- `claim_expires_at`

This allows stale-claim recovery after crash or shutdown.

## 9. Persistence Model

### 9.1 Required main table

The first production design requires a durable task table, e.g. `agentruntime_tasks`.

It should store:

- task identity
- orchestration identity
- node and task type
- task input payload
- role/catalog metadata
- execution status
- result payload
- callback status and attempt count
- claim metadata
- timestamps
- last error summary

### 9.2 Optional future tables

The following are useful but not required for first delivery:

- `agentruntime_task_attempts`
- `agentruntime_task_events`

For first production rollout, these may be deferred if the main task table plus logs provide enough operational visibility.

## 10. Callback Delivery Model

### 10.1 Separate persistence boundary

The runtime must persist execution success before attempting callback delivery.

If callback delivery fails, the task must remain recoverable without recomputing the agent result.

### 10.2 Retry policy

Callback retry should be bounded and configurable:

- fixed or simple interval retry is sufficient for first production
- retry count is persisted on the task row
- after max retry the task moves to `dead`

### 10.3 Payload contract

The callback payload continues to use structured result fields already validated in the MVP path:

- `agent_task_id`
- `agent_task_status`
- `agent_result_type`
- `agent_result`
- `operator_required`
- `agent_next_hint`

## 11. Restart Recovery

On runtime startup, recovery must inspect unfinished tasks.

### 11.1 Recover stale claims

Tasks stuck in `claimed` beyond the claim timeout return to `submitted`.

### 11.2 Recover stale running tasks

For the first production version, tasks stuck in `running` beyond run timeout should default to `failed` with explicit error attribution unless a proven safe re-run rule exists.

This is safer than silently replaying a possibly non-idempotent role execution.

### 11.3 Recover pending callbacks

Tasks in `callback_pending` and `callback_retry` re-enter the callback retry loop automatically.

## 12. Authentication Model

### 12.1 Submission path

OneOps to `agentruntime` may remain an internal trusted call in the short term, but should still be driven by explicit configuration and deploy boundary controls.

### 12.2 Callback path

`agentruntime -> OneOps` callback must use a dedicated service token, not a developer-only `debugToken` as the long-term model.

First production rollout may temporarily use a configured token that OneOps accepts through the existing auth path, but the configuration must be treated as service credentials, not user credentials.

### 12.3 Follow-up direction

Later improvement may move to:

- service identity token rotation
- HMAC signatures
- mTLS

These are not required to ship the first production version.

## 13. Configuration Model

The runtime and OneOps should move from script-only env wiring toward formal configuration ownership.

### 13.1 OneOps-side config

At minimum:

- `agent_runtime_submit_url`

### 13.2 AgentRuntime-side config

At minimum:

- `callback_url`
- `callback_auth_token`
- `worker_poll_interval`
- `claim_timeout`
- `run_timeout`
- `callback_retry_interval`
- `callback_max_retry`

### 13.3 Migration approach

For first production rollout:

- application config should become the primary source
- environment variables remain supported as fallback
- deployment scripts may still inject env values where needed

This allows gradual migration into Nacos-backed configuration without blocking release.

## 14. Operational Requirements

First production rollout must expose enough operating surface to support troubleshooting.

### 14.1 Health

- process liveness
- readiness after worker initialization

### 14.2 Metrics

At minimum:

- task counts by state
- task execution failures
- callback failures
- retry counts
- dead task count

### 14.3 Logging

Every task log path should include:

- task id
- execution id
- node id
- task type
- current state

### 14.4 Queryability

Operators need a way to identify:

- stuck tasks
- callback retry tasks
- dead tasks

This may initially be DB-backed and admin-facing rather than a full custom UI.

## 15. Delivery Boundary

The first production release is considered complete when all of the following are true:

- accepted tasks are durably stored before execution
- runtime restart does not lose unfinished tasks
- callback failures are recoverable without recomputing successful agent work
- task states are queryable and diagnosable
- service-to-service callback auth is explicit and configurable
- OneOps real orchestration loop still completes using the persistent runtime

## 16. Recommended Implementation Order

1. add persistent task table and repository
2. refactor submit API to write tasks instead of launching goroutines
3. add execution worker with DB claim semantics
4. add callback retry worker
5. add startup recovery logic
6. formalize config loading for runtime and OneOps
7. replace temporary callback auth usage with service credential config
8. add health, metrics, and operational query surface

## 17. Recommended Approach

Use:

- MySQL task table
- local execution worker
- local callback retry worker
- explicit service token config

Do not introduce Redis or Kafka in this phase.

This keeps the first production version aligned with the existing codebase, minimizes moving parts, and solves the primary production risks without expanding platform scope.
