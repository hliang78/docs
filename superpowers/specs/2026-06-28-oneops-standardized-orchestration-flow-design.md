# OneOps Standardized Orchestration Flow Design

## 1. Goal

Upgrade OneOps orchestration from a field-oriented MVP template model into a standardized flow contract that keeps the current runtime node kinds but replaces ad hoc step fields with a unified process structure.

The target is not a brand new workflow engine and not a generic low-code platform. The target is a production-oriented orchestration core where:

- templates express flow intent in one stable shape
- the compiler only accepts normalized step contracts
- runtime execution uses one common node contract
- multi-agent orchestration can switch task templates without rewriting the execution core

This design explicitly assumes the current phase does not need backward compatibility with old template syntax.

## 2. Scope

### Included

- hard switch from flat workflow step fields to standardized step structure
- unified template flow contract built around:
  - `kind`
  - `inputs`
  - `policy`
  - `transitions`
  - `outputs`
- normalized internal step model used by compiler and runtime
- compiler refactor to consume only normalized steps
- runtime contract refactor so all node runtimes execute through one common interface
- explicit transition semantics for:
  - success
  - failure
  - timeout
  - reject
- explicit terminal tokens for:
  - `completed`
  - `failed`
  - `escalated`
  - `rejected`
  - `timed_out`
- first-class support for current node kinds:
  - `flow_step`
  - `agent_step`
  - `external_call_step`
  - `callback_wait_step`
  - `approval_wait_step`

### Excluded

- backward compatibility loader for legacy flat workflow fields
- visual orchestration editor
- fully autonomous agent society
- dynamic template-authored code execution
- generic marketplace of arbitrary runtime plugins
- replacing dagengine as execution kernel
- redesigning agentruntime task execution model in this phase

## 3. Design Principles

### 3.1 Standardize shape before expanding capability

The priority is to make every orchestration step look structurally the same before adding more step kinds or richer task domains.

### 3.2 No dual syntax path

The system should not accept both old flat fields and new structured fields. Maintaining both would slow down convergence, complicate tests, and pollute compiler logic.

### 3.3 Keep current node kinds, upgrade their contracts

This phase keeps the existing runtime categories so the rewrite stays bounded. The change is in how they are described and executed, not in inventing a new taxonomy.

### 3.4 Separate node execution from flow routing

Node runtimes should report execution outcome. Template transitions decide where the process goes next. This avoids mixing business routing with node-local mechanics.

### 3.5 Keep OneOps as orchestration owner

OneOps remains the owner of:

- template loading
- flow validation
- execution persistence
- approval records
- callback resume handling
- capability integrations

`dagengine` remains the execution kernel and `agentruntime` remains the agent task execution service.

## 4. Current Problem

The current orchestration MVP already proves the mainline:

- OneOps compiles template bundles into dagengine processes
- runtime registry dispatches node execution
- agentruntime can execute durable agent tasks and callback into OneOps
- waits and approvals are persistent and resumable

The weak point is the template and runtime contract shape.

Current steps are still expressed through scattered fields such as:

- `action`
- `next`
- `on_failure`
- `on_timeout`
- `agent_catalog_name`
- `allowed_tools`
- `target_ref`
- `callback_ref`
- `resume_policy`
- `approval_policy_ref`

This creates several problems:

- template semantics are hard to read
- compiler logic grows by checking many optional flat fields
- node runtime contracts are more implicit than explicit
- adding a new task domain risks more field growth instead of stable composition

## 5. Target Template Model

### 5.1 Standard workflow step shape

Every workflow step should follow one stable structure:

```yaml
steps:
  - key: analysis_submit
    kind: agent_step
    inputs:
      from_context:
        alert_code: alert.code
        ticket_code: ticket.code
    policy:
      action: analyze_alert
      agent:
        catalog: closure_agents
        allowed_tools:
          - knowledge_base
      timeout: 10m
    transitions:
      on_success: analysis_wait
      on_failure: failed
      on_timeout: escalated
    outputs:
      result_key: analysis
```

All current and future steps must be modeled through these same top-level sections:

- `key`
- `kind`
- `inputs`
- `policy`
- `transitions`
- `outputs`

### 5.2 Step sections

#### `key`

Unique identifier for the step inside one workflow.

#### `kind`

One of the supported runtime kinds:

- `flow_step`
- `agent_step`
- `external_call_step`
- `callback_wait_step`
- `approval_wait_step`

#### `inputs`

Declares what the step consumes. It should support at least:

- `from_context`
- `static`

`from_context` maps step-local names to execution context paths.
`static` provides literal values owned by the template.

Example:

```yaml
inputs:
  from_context:
    ticket_code: ticket.code
  static:
    severity: high
```

#### `policy`

Describes how the step executes. This is where kind-specific execution behavior lives.

Examples:

- `policy.action`
- `policy.timeout`
- `policy.agent.catalog`
- `policy.agent.allowed_tools`
- `policy.external.target_ref`
- `policy.external.request_template_ref`
- `policy.resume.token_context_key`
- `policy.approval.policy_ref`

#### `transitions`

Defines flow routing after runtime outcome. It is the only place where next-step semantics are described.

Supported route keys in this phase:

- `on_success`
- `on_failure`
- `on_timeout`
- `on_reject`

Each transition target must be either:

- another step key
- a terminal token

#### `outputs`

Declares what execution result gets written back into context.

Phase 1 requires only lightweight output mapping, not a full transformation language. It should support at least:

- `result_key`
- optional named result path bindings

Example:

```yaml
outputs:
  result_key: dispatch
```

## 6. Kind-Specific Policy Requirements

The flow model is unified, but each `kind` still has minimum required policy fields.

### 6.1 `flow_step`

Required:

- `policy.action`

Optional:

- `policy.timeout`

Allowed transitions:

- `on_success`
- `on_failure`
- `on_timeout`

### 6.2 `agent_step`

Required:

- `policy.action`
- `policy.agent.catalog`

Optional:

- `policy.agent.allowed_tools`
- `policy.timeout`

Allowed transitions:

- `on_success`
- `on_failure`
- `on_timeout`

### 6.3 `external_call_step`

Required:

- `policy.action`
- `policy.external.target_ref`
- `policy.external.request_template_ref`

Optional:

- `policy.timeout`
- `policy.external.callback_ref`

Allowed transitions:

- `on_success`
- `on_failure`
- `on_timeout`

### 6.4 `callback_wait_step`

Required:

- `policy.resume.token_context_key`

Optional:

- `policy.timeout`

Allowed transitions:

- `on_success`
- `on_failure`
- `on_timeout`

### 6.5 `approval_wait_step`

Required:

- `policy.approval.policy_ref`

Optional:

- `policy.timeout`

Allowed transitions:

- `on_success`
- `on_reject`
- `on_timeout`

## 7. Internal Normalized Model

The loader should decode YAML into structured template DTOs, then normalize into one internal contract used everywhere downstream.

Recommended internal structure:

```go
type NormalizedStep struct {
    Key         string
    Kind        string
    Inputs      StepInputs
    Policy      StepPolicy
    Transitions StepTransitions
    Outputs     StepOutputs
}
```

### 7.1 Responsibility split

#### Loader

Responsibilities:

- read YAML files
- parse schema
- perform basic structural validation

It should not contain business routing logic or runtime-specific branching.

#### Normalizer

Responsibilities:

- convert parsed template data into `NormalizedStep`
- validate kind-specific required fields
- validate transition legality
- validate context-key references that can be checked statically

#### Compiler

Responsibilities:

- consume only normalized steps
- produce dagengine nodes and node configs
- remain unaware of legacy template syntax

## 8. Compiler Design

### 8.1 Hard cut compiler behavior

`CompileBundle` should no longer derive node config from a loose collection of flat step fields.

Instead:

1. load template bundle
2. normalize workflow steps
3. compile normalized steps into:
   - `NodeType`
   - `NodeConfig`
   - dependencies

### 8.2 Compiler output shape

The compiler still targets the current dagengine process shape:

- `Nodes`
- `NodeTypes`
- `NodeConfigs`

But `NodeConfig` should now be generated from the standard contract, not directly from raw template fields.

### 8.3 Terminal tokens

The compiler must recognize these terminal tokens:

- `completed`
- `failed`
- `escalated`
- `rejected`
- `timed_out`

Terminal tokens are flow-level end states, not step keys.

## 9. Runtime Contract

### 9.1 Common runtime interface

All node runtimes should execute through one common interface:

```go
type NodeRuntime interface {
    Kind() string
    Run(ctx context.Context, in NodeRuntimeInput) (NodeRuntimeResult, error)
}
```

### 9.2 Common runtime input

Recommended shape:

```go
type NodeRuntimeInput struct {
    ExecutionID string
    NodeKey     string
    Context     map[string]interface{}
    Step        NormalizedStep
}
```

Properties:

- the runtime receives the normalized step, not raw node config trivia
- the runtime sees execution context and current step only
- the runtime should not need to understand template file structure

### 9.3 Common runtime result

Recommended shape:

```go
type NodeRuntimeResult struct {
    Outcome       string
    ContextPatch  map[string]interface{}
    WaitState     *WaitState
    ActionState   *ActionState
    TerminalState string
    Events        []RuntimeEvent
}
```

Semantics:

- `Outcome` is one of:
  - `success`
  - `wait`
  - `failure`
- `ContextPatch` is incremental only
- `WaitState` describes persistent waits
- `ActionState` describes durable action metadata
- `TerminalState` is used only when the flow ends immediately
- `Events` carry structured runtime audit events

### 9.4 Why this matters

Without this contract, the runtime layer will keep leaking implementation details into:

- `ExecutionSrv`
- `DagengineAdapter`
- node-specific switch logic

The goal is that these components coordinate execution, but do not encode per-kind business semantics.

## 10. Transition Semantics

### 10.1 Separate outcome from routing

Runtime outcome and flow routing must stay separate.

Runtime outcome answers:

- did the step succeed
- did it wait
- did it fail

Flow routing answers:

- where does the process go next

### 10.2 Runtime outcome values

In this phase, runtime outcome values are:

- `success`
- `wait`
- `failure`

### 10.3 Transition keys

Transitions use these route keys:

- `on_success`
- `on_failure`
- `on_timeout`
- `on_reject`

### 10.4 Routing rules

- runtime `success` routes through `on_success`
- runtime `failure` routes through `on_failure` unless the failure is timeout-driven
- timeout-driven failure routes through `on_timeout`
- explicit approval rejection routes through `on_reject`
- runtime `wait` does not route immediately; it persists wait state and pauses execution

### 10.5 Why `on_reject` must not collapse into `on_failure`

Approval rejection is an operational business branch, not a technical execution failure.

Collapsing rejection into failure would:

- hide intent in templates
- make audit and UI semantics weaker
- confuse escalation and rejection handling

## 11. Terminal State Model

The standardized terminal tokens for this phase are:

- `completed`
- `failed`
- `escalated`
- `rejected`
- `timed_out`

### 11.1 Meanings

#### `completed`

The process reached a successful business end state.

#### `failed`

The process ended due to unrecoverable execution failure.

#### `escalated`

The process exited to explicit manual or operations takeover.

This is not merely a synonym for failure. It represents an operational handoff boundary and should be preserved distinctly for future runbooks, alerts, and UI treatment.

#### `rejected`

The process ended because a required approval was rejected.

#### `timed_out`

The process ended because the flow exhausted a timeout path and intentionally terminated instead of routing elsewhere.

## 12. Runtime Positioning

The high-level architecture remains:

`ExecutionSrv -> compiler -> DagengineAdapter -> RuntimeRegistry -> NodeRuntime -> CapabilityGateway / OneOps services / agentruntime`

### 12.1 ExecutionSrv

Owns:

- execution lifecycle
- persistence orchestration
- status changes
- high-level resume coordination

Must not own:

- per-kind execution behavior
- template field branching

### 12.2 DagengineAdapter

Owns:

- dispatch between dagengine nodes and runtime registry

Must not own:

- business semantics of node kinds
- ad hoc step-specific switch sprawl

### 12.3 RuntimeRegistry

Owns:

- mapping `kind -> NodeRuntime`

### 12.4 NodeRuntime implementations

Own:

- kind-specific execution
- kind-specific wait creation
- kind-specific action metadata

Must return standardized results rather than mutating orchestration persistence directly in arbitrary ways.

## 13. Template File Shape

This phase does not require changing the bundle layout itself.

The bundle still uses:

- `manifest.yaml`
- `workflow.yaml`
- `agents.yaml`

The change is inside `workflow.yaml`, where the old flat step format is removed and replaced with the standardized step structure.

This keeps import and packaging stable while changing the contract that matters most.

## 14. Mainline Migration Strategy

Because compatibility is out of scope, migration should be explicit and fast.

### 14.1 Rewrite official templates first

Start with:

- `multi_agent_ticket_closure`
- other first-party testdata templates that block compiler tests

### 14.2 Refactor compiler and runtime immediately after

Do not keep a half-state where templates are rewritten but runtime still assumes loose config fields.

### 14.3 Keep one production mainline green

The required proof path for this phase is the real multi-agent closure mainline:

- submit agent tasks
- persist wait state
- resume callbacks
- approval wait
- reject route
- timeout route
- completion and escalation paths

## 15. Testing Strategy

### 15.1 Loader and normalizer tests

Add focused tests for:

- valid standardized steps per kind
- missing required policy fields
- invalid transitions
- invalid terminal token usage
- invalid mixed semantics such as `approval_wait_step` without approval policy

### 15.2 Compiler tests

Add tests for:

- normalized step compilation
- transition target validation
- terminal token handling
- node config generation from standard structure

### 15.3 Runtime tests

Add or refactor tests so every node kind validates:

- `NodeRuntimeInput` consumption
- `NodeRuntimeResult` production
- `ContextPatch` semantics
- `WaitState` semantics where relevant
- transition routing expectations

### 15.4 Mainline acceptance

The mandatory end-to-end acceptance remains the real stack:

- OneOps
- agentruntime
- Nacos-backed config
- real callback/resume behavior
- execution observability

The closure template should be the first certified standardized-flow template.

## 16. Risks

### 16.1 Template rewrite blast radius

Removing compatibility means every active template must move. This is acceptable only if the number of active orchestration templates is still small and controlled.

### 16.2 Runtime half-refactor risk

If the compiler standardizes but runtimes still depend on loose config assumptions, the codebase will become more confusing, not less. Compiler and runtime contract changes must land together.

### 16.3 Over-design risk

The standard structure should remain compact. This phase does not need a rich expression language, embedded scripting, or general transformation DSL.

## 17. Recommended Implementation Order

### Phase 1: Standardized template contract

- redefine workflow step schema
- update template loader
- add normalizer
- rewrite official templates

### Phase 2: Compiler hard cut

- refactor compiler to consume normalized steps only
- regenerate node config from standard sections
- remove legacy flat-field assumptions

### Phase 3: Runtime contract unification

- define common runtime input and result
- migrate runtimes to consume normalized steps
- shrink adapter logic to dispatch-only behavior

### Phase 4: Mainline certification

- validate multi-agent closure end to end
- validate reject to `on_reject`
- validate timeout to `on_timeout`
- validate `escalated` as distinct operational terminal state

## 18. Decision Summary

The design decisions for this phase are:

- keep current node kinds
- do not keep old template syntax
- move all steps to one standard structure
- normalize before compile
- make runtime contract explicit
- separate outcome from routing
- preserve `escalated` and `rejected` as distinct flow terminal states
- certify the multi-agent closure path first before expanding to additional task domains
