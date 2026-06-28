# OneOps Orchestration Runtime Foundation Design

## 1. Goal

Build the next lightweight MVP layer for the OneOps orchestration framework: a shared runtime foundation that adds reusable node execution support for:

- node-level logs
- structured error channels
- synchronous external calls
- asynchronous callback waiting and resume
- approval waiting and resume

This layer must stay lightweight, must fit the current `OneOps + dagengine` architecture, and must avoid prematurely turning the MVP into a generic workflow platform.

## 2. Scope

### Included

- shared runtime contract for orchestration nodes
- shared runtime middleware for logs, events, error normalization, timeout, and retry hooks
- runtime support for these node types:
  - `flow_step`
  - `agent_step`
  - `external_call_step`
  - `callback_wait_step`
  - `approval_wait_step`
- persistent suspend-and-resume model for callback and approval waits
- OneOps API-based resume entrypoints
- pre-registered external target resolution
- execution-level and node-level observability with concise logs and events

### Excluded

- queue-driven worker execution
- distributed scheduler redesign
- arbitrary template-defined code executors
- template-defined open outbound URLs
- advanced connector/plugin marketplace
- multi-stage approval engine
- full payload archival or full-text log platform

## 3. Design Principles

### 3.1 Lightweight MVP first

Only build shared runtime capabilities that are required to make node execution observable, resumable, and externally extensible.

### 3.2 Keep business semantics out of the kernel boundary

The runtime foundation should expose execution abstractions that could later move into `dagengine`, but OneOps-specific business concepts such as ticket routing, approval person resolution, credential governance, and target registration remain in OneOps.

### 3.3 Make waiting a first-class runtime concept

Callback and approval handling must not be simulated by in-memory blocking or ad hoc polling. Waiting must be explicit, persistent, and resumable.

### 3.4 Keep template semantics declarative

Templates describe orchestration intent and references. Platform-owned configuration such as external endpoints, approval policy details, and credential strategy are referenced, not embedded as large inline blobs.

### 3.5 Prefer stable common contracts over growing switch statements

Current MVP execution should evolve from a single gateway-style execution path into a registry-driven runtime model with clear contracts per node type.

## 4. Runtime Positioning

The current architecture remains:

- OneOps is the experience layer, integration layer, and persistence owner
- `dagengine/v2/engine` remains the execution kernel
- orchestration templates continue to compile into a `dagengine` process

The new runtime foundation sits between the compiled DAG nodes and business capability execution:

`ExecutionSrv -> compiler -> DagengineAdapter -> RuntimeRegistry -> NodeRuntime -> CapabilityGateway / OneOps services`

This keeps the primary execution path intact while allowing node behavior to expand without bloating `ExecutionSrv`, `DagengineAdapter`, or `CapabilityGateway`.

## 5. What Should Stay in OneOps vs. What Can Later Move to Dagengine

### Better suited to eventual `dagengine` ownership

These are execution-kernel concepts and should be designed as neutral contracts from day one:

- node runtime interface
- runtime registry
- node execution middleware lifecycle
- standard node execution input and output
- wait/resume instruction model
- timeout and retry semantics
- standard execution event model
- standard structured runtime error model

### Must stay in OneOps

These are business integration concerns and should not be pushed into `dagengine`:

- template bundle format and import rules
- external target registration and governance
- approval policy resolution
- credential and secret resolution
- alert, ticket, SOP, knowledge, and notification capability access
- OneOps API surface, RBAC, and operational views

## 6. State Model

### 6.1 Execution status

Execution instances should use a compact status model:

- `running`
- `waiting_callback`
- `waiting_approval`
- `completed`
- `failed`
- `escalated`
- `cancelled`

These statuses represent the whole execution's current top-level state.

### 6.2 Node status

Node status remains simpler and more reusable:

- `pending`
- `running`
- `waiting`
- `completed`
- `failed`
- `skipped`

Waiting-specific meaning is carried by runtime metadata rather than by exploding the node status enum.

### 6.3 Wait type

Waiting nodes distinguish their wait semantics through:

- `callback`
- `approval`

This keeps the state model compact and allows future wait modes such as timer-based waits without redesigning the entire execution state enum.

## 7. Node Runtime Model

### 7.1 Runtime registry

The runtime foundation should dispatch execution by node type rather than by a growing `switch` inside one gateway component.

The registry should support these first-pass runtime implementations:

- `flow_step`
- `agent_step`
- `external_call_step`
- `callback_wait_step`
- `approval_wait_step`

### 7.2 Neutral runtime interface

Each node runtime should implement one focused contract:

- receive normalized execution input
- execute its own node-specific behavior
- return a normalized execution result

This result must not directly mutate the full orchestration context or persistence model.

### 7.3 Standard execution input

The common runtime input should include at least:

- `execution_id`
- `node_id`
- `node_type`
- `attempt`
- `trace_id`
- `deadline`
- `context`
- `node_config`

This gives every runtime the same operational envelope.

### 7.4 Standard execution result

The common runtime result should include at least:

- `status`
- `context_patch`
- `logs`
- `events`
- `error`
- `suspend_instruction`

Important conventions:

- `context_patch` is incremental, not a full context overwrite
- `error` is structured, not plain string only
- `suspend_instruction` explicitly tells the runtime layer that this node should persist and wait rather than fail

## 8. Shared Runtime Middleware

The first-pass middleware layer should wrap every runtime execution and provide shared concerns in one place.

### 8.1 Responsibilities

- emit node lifecycle events
- attach trace and timing metadata
- collect concise node logs
- normalize errors
- enforce timeout policy
- invoke retry hooks
- recognize suspend instructions
- write execution status transitions consistently

### 8.2 Why middleware is required

Without this layer, each node type would independently invent:

- its own logging style
- its own timeout behavior
- its own failure representation
- its own waiting semantics

That would fragment the MVP immediately and make later kernel extraction much harder.

## 9. Observability Design

The chosen observability target for phase 1 is:

- execution-level status, error, and event visibility
- node-level status, error, event, and concise log visibility

### 9.1 Log model

The concise node log model should include:

- `execution_id`
- `node_id`
- `level`
- `message`
- `code`
- `details_json`
- `timestamp`

This is intentionally not a full payload archive. It should be enough for operational troubleshooting without prematurely committing to a heavy log platform.

### 9.2 Event model

The standard event model should at minimum support:

- `execution_started`
- `node_started`
- `node_completed`
- `node_failed`
- `node_waiting`
- `node_resumed`
- `execution_completed`
- `execution_failed`
- `execution_escalated`
- `execution_action_required`

These events drive audit trails, operational timelines, and later UI views.

## 10. Structured Error Channel

### 10.1 Standard error shape

Errors should be normalized into a shared runtime error contract with:

- `category`
- `code`
- `message`
- `retryable`
- `details`
- `external_ref`

### 10.2 Phase 1 categories

The first-pass categories should be:

- `validation_error`
- `runtime_error`
- `external_call_error`
- `timeout_error`
- `approval_error`
- `callback_error`
- `policy_error`

This allows OneOps to route retries, escalations, and operator diagnostics using explicit machine-readable semantics instead of string matching.

## 11. External Call Design

### 11.1 Security boundary

The first MVP must only allow calls to pre-registered external targets managed by OneOps. Templates must not directly embed arbitrary outbound URLs.

### 11.2 Runtime behavior

`external_call_step` should:

- resolve `target_ref` through a OneOps-owned target registry
- render a request using a referenced request template
- execute a synchronous HTTP call
- capture request/response summary data
- convert successful response data into `context_patch`
- convert failures into structured runtime errors

### 11.3 Non-goal for phase 1

Asynchronous external workflow should not be hidden inside `external_call_step`. Instead:

- use `external_call_step` to initiate
- use `callback_wait_step` to wait

This keeps the external interaction model explicit and debuggable.

## 12. Callback Wait Design

### 12.1 Runtime behavior

`callback_wait_step` should:

- create a persistent suspend record
- emit `node_waiting`
- move execution into `waiting_callback`
- stop forward execution

### 12.2 Resume model

Resume must be driven through OneOps APIs only in phase 1. The resume path should:

- validate the resume token or equivalent identity
- verify the suspend record is still active
- accept callback payload
- write resume result
- emit `node_resumed`
- continue execution from the waiting node onward

### 12.3 Current MVP callback decision

The current lightweight MVP makes one explicit resume choice:

- callback resume merges callback payload into execution context
- execution continues from the node after the wait node
- if continuation cannot be started, execution is marked `failed` rather than left in a stale waiting state

## 13. Approval Wait Design

### 13.1 Runtime behavior

`approval_wait_step` behaves as another wait node, not as a separate orchestration subsystem:

- create a persistent suspend record
- emit `node_waiting`
- move execution into `waiting_approval`
- stop forward execution

### 13.2 Resume model

Approval also resumes through OneOps APIs only in phase 1:

- approve
- reject
- comment
- operator identity capture

Approval decisions should resolve the suspend record and then either:

- continue execution
- fail the node
- route to `on_failure`
- escalate on timeout

### 13.3 Current MVP approval decision

The current lightweight MVP narrows approval behavior to one concrete choice so the loop stays small and testable:

- `approve` continues execution from the node after the wait node
- `reject` routes through the wait node's `on_failure`
- if `on_failure` resolves to a terminal token, execution closes in that terminal state
- if `on_failure` resolves to another step, execution continues from that step
- timeout handling routes through the wait node's `on_timeout`
- if `on_timeout` resolves to a terminal token, execution closes in that terminal state
- if `on_timeout` resolves to another step, execution continues from that step
- if the terminal token is `escalated`, runtime also emits a structured `execution_action_required` event so operations follow-up does not depend on string matching
- if approved continuation cannot be started, execution is marked `failed`

## 14. Suspend-and-Resume Persistence

### 14.1 Suspend record

The runtime foundation needs a dedicated suspend model rather than overloading execution events.

Minimum fields should include:

- `execution_id`
- `node_id`
- `wait_type`
- `resume_token`
- `status`
- `expires_at`
- `wait_payload_json`
- `resolved_at`
- `created_at`

### 14.2 Suspend status

Suspend record status should stay compact:

- `active`
- `resolved`
- `expired`
- `cancelled`

This persistence model is shared by callback waits and approval waits, with node-specific semantics living in `wait_payload_json` or equivalent typed config fields.

## 15. Template Model Extensions

The existing workflow model should remain small and only grow by necessary fields.

### 15.1 Supported node types

Workflow steps should now support:

- `flow_step`
- `agent_step`
- `external_call_step`
- `callback_wait_step`
- `approval_wait_step`

### 15.2 `external_call_step` fields

- `target_ref`
- `request_template_ref`
- `timeout_seconds`
- `retry_policy`

### 15.3 `callback_wait_step` fields

- `callback_ref`
- `resume_policy`
- `timeout_seconds`
- `on_timeout`

### 15.4 `approval_wait_step` fields

- `approval_policy_ref`
- `timeout_seconds`
- `on_timeout`

The use of referenced policy objects is intentional. Templates describe orchestration structure; OneOps manages platform-owned operational policy.

## 16. Proposed OneOps File Structure

The implementation should be decomposed into four groups inside `OneOps/app/orchestration`.

### 16.1 Runtime abstractions

- `runtime/registry.go`
- `runtime/types.go`
- `runtime/middleware.go`
- `runtime/errors.go`
- `runtime/events.go`

### 16.2 Node runtime implementations

- `runtime/flow_step.go`
- `runtime/agent_step.go`
- `runtime/external_call_step.go`
- `runtime/callback_wait_step.go`
- `runtime/approval_wait_step.go`

### 16.3 Suspend and resume handling

- `suspend/model.go`
- `suspend/store.go`
- `service/impl/resume.go`
- `api/resume.go`

### 16.4 Platform-owned integration

- `target_registry/model.go`
- `target_registry/registry.go`
- `service/impl/external_target.go`

## 17. Existing File Evolution

### `service/impl/execution.go`

Keep as the orchestration entrypoint and execution persistence coordinator, but remove growing node-specific behavior from it.

### `service/impl/dagengine_adapter.go`

Keep as the DAG execution bridge, but delegate node execution to the runtime registry rather than calling one generic execution gateway.

### `service/impl/capability_gateway.go`

Gradually narrow this component into a business capability access layer instead of a monolithic node executor.

## 18. Recommended Delivery Order

This work should be implemented in four lightweight phases.

### Phase 1: Runtime foundation

- standard input/output contracts
- runtime registry
- runtime middleware skeleton
- standard events
- standard structured errors
- concise node logs

### Phase 2: Wait and resume

- suspend model and store
- `callback_wait_step`
- `approval_wait_step`
- resume APIs
- execution status transitions for waiting and resumed states

### Phase 3: External calls

- external target registry
- synchronous HTTP runtime
- request/response summary logging
- timeout and retryable error mapping

### Phase 4: Migrate existing runtime path

- adapt `flow_step`
- adapt `agent_step`
- narrow `CapabilityGateway`
- route all node execution through runtime registry

## 19. Testing Strategy

The first-pass implementation should verify:

- node runtime registration and dispatch
- middleware event emission
- middleware log capture
- structured error normalization
- suspend record persistence
- callback resume path
- approval approve/reject path
- external call target resolution
- external call success/failure/timeout mapping
- execution resume after wait node completion

Testing should remain package-focused and small, following the current MVP approach already used for template loading, compiler behavior, and execution persistence.

## 20. Risks and Controls

### Risk: runtime abstraction becomes too heavy

Control:

- keep only one neutral runtime interface
- avoid generic plugin systems
- avoid queue and worker architecture in this phase

### Risk: business semantics leak into shared runtime contracts

Control:

- forbid OneOps-specific business fields in shared runtime interfaces
- keep approval and target registry lookups in OneOps-owned integration services

### Risk: wait/resume logic becomes fragmented

Control:

- one suspend model
- one resume API family
- one `node_waiting` / `node_resumed` event model

### Risk: external calls expand too quickly

Control:

- HTTP only
- synchronous only
- pre-registered targets only
- concise summaries only

## 21. Final Recommendation

The next MVP slice should not directly jump into a large external automation subsystem. It should first build a shared runtime foundation that makes node execution:

- observable
- structured
- resumable
- safe for controlled external interaction

This keeps the architecture aligned with the current `OneOps + dagengine` direction, prepares the right abstractions for future `dagengine` extraction, and still preserves the lightweight delivery principle required for the MVP.
