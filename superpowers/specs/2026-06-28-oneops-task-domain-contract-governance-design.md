# OneOps Task Domain Contract Governance Design

## 1. Goal

Define the next mainline platform step after the runtime foundation and role-pack governance work:

- promote `task_domain` from a loose string into a platform-owned contract object
- make templates switch behavior mainly through `流程 + agent 策略 + 任务域`
- ensure different task domains can reuse the same runtime and agent contract layer without hidden assumptions

This design is the bridge from the current M1 closure-oriented mainline into M2 template-driven multi-domain reuse.

## 2. Current Baseline

The current codebase already has meaningful platform assets and should not be treated as throwaway MVP work.

### 2.1 Runtime foundation already exists

The orchestration runtime now has:

- typed step model and template normalization
- runtime registry and middleware
- `flow_step`, `agent_step`, `external_call_step`, `callback_wait_step`, and `approval_wait_step`
- persistent suspend and resume support
- execution graph, logs, events, and observability APIs

### 2.2 Agent strategy governance is partially platformized

The agent strategy layer now has:

- `role_ref`
- `role_pack_ref`
- `strategy_ref`
- strategy-driven inheritance for:
  - `timeout_seconds`
  - `callback_max_retry`
  - `approval_required`
- runtime submission validation and role-pack-aware routing

### 2.3 Durable agentruntime is already production-shaped

`agentruntime` now has:

- durable task persistence
- worker claim and recovery
- callback retry
- restart safety
- Nacos-backed bootstrap
- role and role-pack aware execution

## 3. Problem Statement

The platform is no longer blocked on basic runtime mechanics. The weakest layer is now `任务域`.

Today `task_domain` is still mostly:

- a string in templates
- a routing hint for runtime policy
- a label carried into task submission

That is not enough for platform reuse.

Without a first-class task-domain contract, the system still has these risks:

- templates from different domains can accidentally rely on hidden context assumptions
- role packs can be bound to domains only informally
- input and output expectations are not platform-governed
- switching templates still means partially switching implicit code expectations
- domain-level success, failure, escalation, and takeover semantics remain underspecified

## 4. Why This Is The Right Next Step

The current platform already has:

- enough flow control to express domain workflows
- enough agent policy to route and govern agent-like execution
- enough durable runtime to run asynchronous production-shaped work

The missing piece is what makes the platform truly reusable:

- a stable task-domain contract layer that sits between templates and role-pack execution

This is what turns:

- "a closure workflow with some agent steps"

into:

- "a platform where multiple domains can share the same runtime and agent contract layer"

## 5. Design Principles

### 5.1 Domains are platform objects, not labels

`task_domain` should be resolved from a registry-backed definition rather than treated as free-form text.

### 5.2 Contracts should be explicit at submit time

If a template, role pack, or execution context violates a domain contract, the platform should fail before agent work starts.

### 5.3 Domains should own business I/O expectations

The runtime remains generic, but domain contracts should define:

- required inputs
- expected outputs
- allowed outcome shapes
- operator takeover semantics

### 5.4 Role packs and domains must be governed together

Role packs should not merely carry their own metadata. They must be checked against the domain they are serving.

### 5.5 Keep the system lightweight

This step should not introduce a generic ontology system or a complex schema platform. MVP governance should be concise, typed, and testable.

## 6. Target Model

The next stable contract stack should become:

- `流程`
  - step order, branching, waiting, resume, timeout routing
- `agent 策略`
  - role pack, tool policy, runtime policy, approval and retry behavior
- `任务域`
  - business object, input contract, output contract, allowed role packs, outcome semantics

At runtime the path should read conceptually as:

`template -> normalized step -> domain contract + role pack policy -> agent task submission -> agentruntime validation -> role execution`

## 7. Task Domain Registry

### 7.1 Required domain definition fields

Each platform-owned task domain definition should minimally include:

- `ref`
- `name`
- `description`
- `required_context_keys`
- `optional_context_keys`
- `result_type`
- `required_result_payload_keys`
- `allowed_role_packs`
- `default_timeout_seconds`
- `default_callback_max_retry`
- `approval_required`
- `allowed_terminal_states`

### 7.2 Why these fields are enough for MVP

These fields are enough to govern:

- whether a template is valid for a domain
- whether a role pack is allowed in that domain
- whether runtime policy has safe defaults
- whether role output is acceptable for that domain

They avoid prematurely adding:

- full JSON-schema engines
- nested domain inheritance systems
- dynamic workflow synthesis

## 8. Template Changes

Templates should continue to describe intent declaratively, but with clearer domain semantics.

### 8.1 Workflow layer

Workflow steps still define:

- transitions
- wait points
- node actions

### 8.2 Agent strategy layer

Agent strategy continues to define:

- role pack reference
- tool and retry policy
- approval requirement
- strategy-level defaults

### 8.3 Task domain layer

Task domain references should define:

- which domain the step belongs to
- which domain input contract applies
- which output binding contract the step must satisfy

For MVP, this should stay reference-based rather than embedding large contract blobs inline.

## 9. Validation Model

Validation should happen at three points.

### 9.1 Template load time

Fail if:

- domain reference is missing
- role pack is not allowed for the referenced domain
- required domain bindings are absent

### 9.2 Orchestration submit time

Fail if:

- required domain context keys are missing
- the effective runtime policy conflicts with domain policy constraints

### 9.3 Agentruntime execution time

Fail if:

- submitted task does not satisfy the resolved domain contract
- role output does not satisfy domain result requirements

## 10. Outcome Semantics

The domain layer should formalize what terminal outcomes mean in business terms.

For MVP, each domain should explicitly declare which terminal states are allowed, such as:

- `completed`
- `failed`
- `rejected`
- `timed_out`
- `escalated`
- `action_required`

This is important because `escalated` in a closure domain may mean operator follow-up, while `escalated` in an operation-assist domain may mean mandatory senior review.

## 11. Initial Domain Set

MVP should define at least these platform-owned domains:

- `ticket_closure`
- `incident_analysis`
- `operation_assist`

These map to the domains already hinted at in existing template fixtures and allow M2 to prove real reuse rather than theoretical reuse.

## 12. Expected Platform Gain

After this step:

- changing template will more reliably change task behavior without runtime rewrites
- different domains can share the same durable runtime
- role packs can be governed against business-domain boundaries
- domain-level observability and operator expectations become clearer

This is the point where the platform starts to become "one platform, many task domains" rather than "one workflow with reusable helpers."

## 13. Out Of Scope

This step does not include:

- full autonomous multi-agent society behavior
- planner-created arbitrary subgraphs
- marketplace-level agent/plugin packaging
- large schema authoring UI
- advanced policy DSLs

Those can come later. The immediate purpose is to make template-driven multi-domain execution safe, testable, and platform-owned.

## 14. Recommended Next Implementation Slice

The next implementation slice should focus on:

1. introducing `TaskDomainDefinition` and `TaskDomainRegistry`
2. validating template domain references against the registry
3. validating role-pack/domain compatibility at load and submit time
4. carrying domain contract metadata through agent task submission
5. validating domain result expectations in `agentruntime`

This is the smallest slice that materially advances the mainline without overexpanding scope.
