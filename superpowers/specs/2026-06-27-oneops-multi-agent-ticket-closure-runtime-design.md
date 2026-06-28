# OneOps Multi-Agent Ticket Closure Runtime Design

## 1. Goal

Build the first real multi-agent orchestration closure loop for OneOps:

`alert -> analysis -> dispatch recommendation -> human approval -> execution tracking -> closure -> knowledge draft`

This design must use real agents, real persistence, real waiting/resume semantics, and real external actions. It must stay lightweight enough for MVP delivery and must preserve OneOps as the workflow and state owner.

## 2. Confirmed Product Decisions

The following product decisions are fixed for this MVP:

- orchestration mode is hybrid:
  - upper layer uses LLM-driven multi-agent reasoning
  - lower layer uses real OneOps, controller, and external system execution
- first closure loop is:
  - alert analysis
  - dispatch recommendation
  - human approval
  - execution tracking
  - closure
- only execution approval is manual
- OneOps alert, ticket system, and WeCom/DingTalk are in scope
- OneOps owns the primary ticket and primary workflow state
- first-pass agent roles are:
  - analysis agent
  - dispatch agent
  - tracking agent
  - knowledge agent
- multi-agent runtime is deployed as a separate runtime service
- interaction between OneOps and the agent runtime is fully asynchronous and persistent

## 3. Scope

### Included

- OneOps-owned orchestration template and execution flow for multi-agent closure
- separate agent runtime service for real agent execution
- persistent task submission from OneOps to the agent runtime
- persistent callback/event result delivery from the agent runtime back to OneOps
- approval wait and callback wait in the existing orchestration runtime
- OneOps observability for agent task progress and final outputs
- real integration points for:
  - primary OneOps ticket
  - external ticket synchronization
  - WeCom or DingTalk notification
- knowledge draft generation after closure

### Excluded

- arbitrary user-defined agent teams
- generic marketplace for agent tools
- free-form agent-to-agent social chat UI
- autonomous remediation changes on production systems
- multi-stage human approval engine
- automatic SOP publication without human review
- full distributed queue platform redesign

## 4. Design Principles

### 4.1 OneOps remains the workflow owner

OneOps owns:

- primary execution
- primary ticket
- approval
- status transitions
- timeout/escalation semantics
- audit trail

The agent runtime does not own the business process.

### 4.2 Agent runtime owns intelligence, not control

The agent runtime owns:

- agent session lifecycle
- LLM reasoning
- tool selection and invocation
- inter-agent coordination
- structured output production

It returns results and hints. It does not directly decide the final workflow route.

### 4.3 Waiting is explicit and persistent

Long-running agent work, approval, and external callback handling must use persisted waiting states. No in-memory blocking, no ad hoc polling loop inside request handlers, and no implicit hidden waits.

### 4.4 Structured outputs over free-form prose

Agents may produce natural language summaries, but the orchestration contract must be driven by structured payloads that OneOps can validate, store, route, and render.

### 4.5 MVP must close the loop, not build a platform first

The first release proves a real closure loop with four fixed agent roles. It does not try to become a generic agent operating system.

## 5. Target Architecture

The target architecture for MVP is:

`OneOps Alert/Event -> OneOps ExecutionSrv -> DagengineAdapter -> RuntimeRegistry -> agent_step/external_call_step/wait nodes -> Agent Runtime -> OneOps callback/resume -> Ticket/IM integrations -> Tracking -> Knowledge draft`

Responsibilities are split as follows.

### 5.1 OneOps

OneOps is responsible for:

- creating the primary ticket
- starting the orchestration execution
- deciding which step runs next
- storing execution and event history
- storing wait state and resume tokens
- collecting approval decisions
- applying escalation and timeout semantics
- exposing UI and API views

### 5.2 Agent Runtime

The agent runtime is responsible for:

- receiving a submitted agent task
- loading the correct agent role and prompt bundle
- reading task context and constraints
- invoking allowed tools
- coordinating sub-agents when needed
- producing a structured result
- posting a callback or event to OneOps

### 5.3 External Systems

External systems remain outside the workflow core:

- external ticket system
- WeCom or DingTalk
- schedule or skill registry
- knowledge base
- troubleshooting data sources

OneOps accesses them either directly through platform-managed integrations or through agent-runtime-managed tools, depending on the step.

## 6. Agent Roles

### 6.1 Analysis Agent

Inputs:

- alert payload
- device or service identity
- recent change summary
- recent related alerts
- topology or asset hints

Outputs:

- probable cause hypotheses
- impact assessment
- urgency or severity suggestion
- recommended handling strategy
- confidence and missing-information notes

### 6.2 Dispatch Agent

Inputs:

- analysis result
- ticket context
- staffing or skill metadata
- location, area, or resource constraints

Outputs:

- recommended assignee or team
- recommended notification targets
- dispatch rationale
- SLA or response urgency suggestion

### 6.3 Tracking Agent

Inputs:

- primary ticket state
- external ticket sync state
- execution history
- elapsed time and SLA thresholds

Outputs:

- tracking update summary
- follow-up recommendation
- escalation suggestion
- closure readiness assessment

### 6.4 Knowledge Agent

Inputs:

- final execution timeline
- key decision points
- human comments
- resolution summary

Outputs:

- draft knowledge entry
- draft SOP update suggestion
- reusable tags or similarity index keys

## 7. Orchestration Model

The first-pass workflow should be compiled from a normal orchestration template and use existing runtime node types plus one new business contract around agent tasks.

### 7.1 Recommended node chain

The minimal workflow chain is:

1. ingest alert and create primary ticket
2. submit analysis agent task
3. wait for agent callback
4. submit dispatch agent task
5. wait for agent callback
6. wait for human approval
7. sync or dispatch to external ticket and IM
8. submit tracking agent task
9. wait for callback or periodic follow-up signal
10. close primary ticket
11. submit knowledge agent task
12. wait for callback or mark draft pending
13. completed

### 7.2 Runtime mapping

The workflow uses these runtime types:

- `flow_step`
  - OneOps-owned deterministic business actions
- `agent_step`
  - submit a task to the agent runtime
- `callback_wait_step`
  - wait for async result from the agent runtime or external system
- `approval_wait_step`
  - wait for OneOps human approval
- `external_call_step`
  - reserved for controlled platform integration calls where needed

### 7.3 Agent step semantics

For this MVP, `agent_step` should not execute the full agent logic inside OneOps. It should:

- validate config
- create a persistent agent task submission
- emit execution events
- return a context patch with submitted task metadata

The actual persistent wait stays explicit in the following `callback_wait_step`, and the actual agent work happens in the separate agent runtime.

## 8. Task Protocol Between OneOps and Agent Runtime

### 8.1 OneOps -> Agent Runtime submit contract

Each submitted task should include:

- `task_id`
- `execution_id`
- `node_id`
- `ticket_id`
- `task_type`
- `agent_role`
- `input_context`
- `constraints`
- `allowed_tools`
- `callback_ref`
- `trace_id`

### 8.2 Task types

The first-pass `task_type` values are:

- `analyze_alert`
- `recommend_dispatch`
- `track_execution`
- `draft_knowledge`

### 8.3 Callback contract

Agent runtime callback to OneOps should include:

- `task_id`
- `execution_id`
- `node_id`
- `resume_token`
- `status`
- `result_type`
- `result_payload`
- `operator_action_required`
- `next_hint`
- `error`

### 8.4 Result status

The first-pass result statuses are:

- `succeeded`
- `failed`
- `waiting`
- `escalated`

`waiting` is allowed when the runtime itself needs a long subtask or a human/tool dependency and must continue later.

## 9. Persistent State Model

### 9.1 Execution-level state

Execution state remains compact:

- `running`
- `waiting_callback`
- `waiting_approval`
- `completed`
- `failed`
- `escalated`
- `cancelled`

### 9.2 Agent task state

Agent task state should be tracked separately from execution state:

- `submitted`
- `running`
- `waiting`
- `succeeded`
- `failed`
- `escalated`
- `cancelled`

This lets OneOps hold the business workflow state while still showing true agent progress.

### 9.3 Wait classes

This MVP uses three effective waiting classes:

- `waiting_agent`
  - the execution is waiting for an agent runtime callback
- `waiting_approval`
  - the execution is waiting for a human decision in OneOps
- `waiting_callback`
  - the execution is waiting for an external callback

In the existing execution status enum, `waiting_agent` should be represented through the persisted wait record and surfaced as `waiting_callback` with a more specific wait payload, rather than adding another top-level status immediately.

## 10. OneOps Data Ownership

OneOps should persist:

- execution rows
- execution context snapshots or patches
- execution logs
- execution events
- suspend records
- approval decisions
- agent task submission records
- agent callback audit records
- knowledge draft linkage to the ticket or execution

The agent runtime may keep its own task-local transcripts and tool traces, but OneOps must keep enough structured state to explain business flow decisions.

## 11. Approval and Closure Flow

### 11.1 Approval policy

Only one mandatory human gate exists in MVP:

- approve execution after dispatch recommendation and before formal execution or distribution

### 11.2 Approval outcomes

Approval outcomes map to:

- approve:
  - continue to external dispatch and tracking
- reject:
  - route through `on_failure` or `manual_review`
- timeout:
  - route through `on_timeout` or `escalated`

### 11.3 Closure conditions

The primary ticket closes only when:

- required dispatch actions are sent
- tracking stage marks execution complete or closure-ready
- no unresolved escalation remains
- final status has been persisted

Knowledge drafting may finish before or after final closure, but the closure event must record whether the knowledge draft is complete or still pending review.

## 12. Observability and UX

The execution observatory should remain the first operational surface for this MVP.

It should clearly show:

- which agent role is active or was last active
- whether the current wait is:
  - agent result
  - human approval
  - external callback
- latest structured agent output summary
- approval decision trail
- escalation or action-required events
- final knowledge-draft status

The UI does not need a generic multi-agent console in MVP. It needs a trustworthy operational view of the closure loop.

## 13. MVP Delivery Shape

The MVP should be delivered in four implementation slices:

### 13.1 Slice A: Agent task submission foundation

- extend `agent_step` from local stub execution into persisted async task submission
- define task protocol and callback contract
- add agent task persistence and observability

### 13.2 Slice B: Analysis and dispatch loop

- wire analysis agent and dispatch agent
- persist structured outputs
- route into approval wait

### 13.3 Slice C: Approval, external sync, and tracking loop

- OneOps approval UI
- external ticket and IM distribution
- tracking agent callback flow
- timeout and escalation handling

### 13.4 Slice D: Closure and knowledge draft

- closure decision
- knowledge agent task
- knowledge draft persistence and display

## 14. Non-Goals for MVP

The following are intentionally out of scope:

- arbitrary agent graphs defined by end users
- production auto-remediation without approval
- cross-tenant shared agent marketplace
- advanced prompt lab or agent authoring studio
- free-form agent memory platform
- generic event bus redesign

## 15. Key Risks and Mitigations

### 15.1 Risk: OneOps and agent runtime ownership blur together

Mitigation:

- keep OneOps as the sole workflow owner
- keep agent runtime outputs structured and advisory

### 15.2 Risk: Long-running agent work becomes invisible

Mitigation:

- persist agent task state separately
- surface it in execution observability

### 15.3 Risk: Callback semantics drift across agents and integrations

Mitigation:

- use one callback contract for all async agent completions
- map agent results through the same suspend/resume path already used by the orchestration runtime

### 15.4 Risk: MVP grows into a generic agent platform too early

Mitigation:

- keep four fixed agent roles
- keep one fixed closure loop
- postpone generalization until the first production-shaped loop is stable

## 16. Recommended Next Step

After this spec is approved, the implementation plan should be split into:

1. agent task submission and persistence foundation
2. agent runtime callback and resume contract
3. analysis + dispatch agent loop
4. approval + tracking + closure loop
5. knowledge draft loop
6. observability and operational UI
