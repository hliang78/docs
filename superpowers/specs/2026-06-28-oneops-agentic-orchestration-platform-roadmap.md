# OneOps Agentic Orchestration Platform Roadmap

## 1. Positioning

The target is not a single-purpose alert-closure demo and not an unconstrained autonomous agent society.

The target is a production-oriented **OneOps Agentic Orchestration Platform**:

- One stable runtime foundation
- One stable agent contract layer
- Many task domains driven by templates
- Controlled autonomy with human takeover

The platform must support:

- changing workflow by template
- changing agent strategy by template and configuration
- changing task domain by template

This means the long-term system is not defined by one business scenario. The first scenario is only the first validation path.

## 2. Core Goal

Build a platform where:

- the runtime remains stable
- agent behavior is controlled by explicit contracts and policy
- different tasks are delivered by switching templates rather than rewriting core code
- operators can always observe, intervene, resume, reject, escalate, and audit execution

## 3. Anti-Toy Constraints

To avoid spending large effort on something with little real-world value, every stage must satisfy all of the following:

### 3.1 Real input

The platform must consume real production-style inputs such as:

- real alerts
- real tickets
- real approvals
- real callbacks
- real knowledge references

Long-term reliance on mock-only entrypoints is not acceptable.

### 3.2 Real output

The platform must produce real effects such as:

- creating or updating tickets
- progressing execution state
- triggering approval or callback handling
- generating actionable knowledge drafts
- emitting real operator-facing action-required events

### 3.3 Human takeover

Any agent failure, timeout, rejection, or escalation must be visible and recoverable by people through the platform.

### 3.4 Operability

Operators must be able to answer:

- what ran
- what is waiting
- what failed
- why it failed
- what was auto-decided
- who took over
- how execution was resumed

If a capability does not improve one of these four dimensions, it should not be prioritized.

## 4. Platform Architecture

The platform should be understood as three layers.

### 4.1 Runtime kernel

This layer is stable and scenario-agnostic.

It includes:

- durable execution and task persistence
- callback wait and approval wait
- suspend and resume
- execution and node events
- node logs
- timeout and retry behavior
- recovery and restart behavior
- action-required escalation handling

This layer should change slowly and only when the platform itself grows.

### 4.2 Agent contract layer

This layer defines how agent-like work is executed safely and predictably.

It includes:

- agent catalog
- allowed tools and tool policy
- input and output contracts
- task result typing
- next-hint semantics
- failure semantics
- escalation semantics
- autonomy guardrails

This layer should evolve into the stable control plane for all agent behaviors.

### 4.3 Template domain layer

This layer defines task-domain workflows.

Examples:

- alert-to-ticket closure
- RCA / diagnosis
- inspection and SOP execution
- change preparation
- rollback confirmation
- dispatch coordination

This is where most task variation should live.

## 5. Recommended Strategy

The recommended strategy is:

- first prove one real production-style mainline
- then prove template-driven multi-domain reuse
- then add controlled autonomy

This avoids two common failure modes:

- overbuilding autonomy before production control exists
- overfitting the platform to one alert-closure demo

## 6. Milestone M1

### 6.1 Name

**Platformized Closure Mainline**

### 6.2 Objective

Deliver one real, production-meaningful task mainline:

`alert -> ticket -> multi-agent coordination -> approval / callback -> closure trace`

### 6.3 What M1 proves

M1 proves:

- the platform can run a real end-to-end business path
- the runtime is durable and observable
- waits and resumes are first-class
- agents can participate without becoming a black box
- operators can take over at any point that matters

### 6.4 Scope

M1 should include:

- durable agentruntime workers
- persistent callback and approval wait handling
- one primary multi-agent closure template
- one stable minimum agent contract
- observatory and detail debugging views
- operator actions for approve, reject, callback resume, escalation follow-up
- production-style local or pre-production acceptance path

### 6.5 Completion standard

M1 is complete only when:

- one real closure template can run repeatedly
- results are durable and observable
- failures do not become black boxes
- operator intervention is usable
- the chain is meaningful enough for a real pilot

## 7. Milestone M2

### 7.1 Name

**Template-Driven Multi-Domain Platform**

### 7.2 Objective

Prove that the system is a platform rather than a single workflow product.

### 7.3 What M2 proves

M2 proves:

- different task domains can share the same runtime
- templates can change workflow, strategy, and domain
- agent catalog and tool policy materially affect behavior
- new domains mostly require template and configuration work, not deep runtime rewrites

### 7.4 Scope

M2 should validate at least three kinds of template domains:

- closure domain
- diagnosis / RCA domain
- operation / inspection / change-assist domain

M2 should also strengthen:

- agent catalog semantics
- tool capability boundaries
- template domain typing
- domain-level acceptance criteria

### 7.5 Completion standard

M2 is complete only when:

- at least two or three task domains execute on the same platform
- runtime and contract reuse are real, not theoretical
- agent catalog affects policy and outcomes
- adding a new domain is primarily a template/config operation

## 8. Milestone M3

### 8.1 Name

**Controlled Autonomy**

### 8.2 Objective

Increase useful agent autonomy without losing production control.

### 8.3 What M3 proves

M3 proves:

- agents can decompose within template-defined boundaries
- multiple agents can collaborate through structured handoff objects
- autonomy is budgeted, explainable, and interruptible
- autonomy failure returns safely to human-controlled paths

### 8.4 Scope

M3 should include:

- bounded task decomposition
- structured multi-agent coordination artifacts
- autonomy guardrails
- explanation and reasoning trace visibility
- mandatory escalation or approval for high-risk decisions

### 8.5 Completion standard

M3 is complete only when:

- at least one template supports bounded subtask decomposition
- autonomous behavior remains observable and controllable
- operators can understand why an agent took a path
- rollback to human-managed continuation is safe

## 9. What Must Not Happen

The roadmap should explicitly reject these failure patterns:

- building many scenario-specific branches into core runtime
- introducing free-form autonomy before guardrails exist
- using template count as the success metric
- optimizing for demos over operability
- hiding failure details behind agent mystique
- treating UI polish as a substitute for runtime truth

## 10. Near-Term Prioritization

The current recommended order is:

1. finish M1 as the first production-meaningful mainline
2. reframe all new work through the M2 platform lens
3. defer stronger autonomy to M3 until M1 and M2 controls are stable

This means current work should be judged against a simple question:

`Does this strengthen the production closure mainline or the future template-driven platform boundary?`

If the answer is no, it should likely wait.

## 11. Acceptance Framework

Every proposed feature after this roadmap should be tagged with:

- milestone: `M1`, `M2`, or `M3`
- layer: `runtime kernel`, `agent contract`, or `template domain`
- business impact: what real input and output it improves
- control impact: how it improves visibility, takeover, or auditability

This keeps execution aligned with platform goals rather than feature drift.

## 12. Final Definition Of Success

Success is not:

- “we built a multi-agent demo”
- “we added many nodes”
- “we can show a fancy execution graph”

Success is:

- one stable runtime foundation
- one reusable agent contract model
- many task domains delivered by templates
- controlled autonomy with human takeover
- a path from pilot to production that operators can trust
