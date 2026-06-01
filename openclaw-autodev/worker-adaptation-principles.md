# OpenClaw Worker Adaptation Principles

This note defines the macro adaptation model for weak-mindset workers.

The goal is not to make every worker equally smart. The goal is to compile
work into a narrow, verifiable execution lane that a weaker worker can finish
without privately inventing scope, facts, permissions, or success criteria.

## What Qwen Covered

The current `qwen-worker` adaptation proved these points:

- provider/model compatibility must be explicit;
- noisy workspace identity/bootstrap context can derail a weak worker;
- one story, one bounded turn, one small patch, and one targeted validation are
  much more reliable than broad backlog work;
- worker-reported `DONE` is not trustworthy without controller-side verify;
- controller recovery evidence must be injected into the next turn when verify
  disproves the worker result.

These lessons are real, but they mainly cover the local code-patch worker lane.

## What A Full Adaptation Model Must Cover

Weak-worker adaptation must also cover lanes that the Qwen harness did not
exercise fully:

- validation-only workers;
- browser/UI verification workers;
- code-to-doc fact extraction workers;
- read-only DB/API discovery workers;
- remote read-only workers;
- remote apply workers with explicit approval;
- multi-lane join/handoff workers;
- evidence synthesis and coordination workers.

## Core Principle

Every weak worker must operate inside a compiled execution pack, not a raw
project prompt.

That execution pack must answer six questions before the worker starts:

1. What kind of task is this?
2. Why is this worker allowed to take it?
3. What is the current source of truth?
4. What actions and writes are allowed?
5. How will success be externally verified?
6. What is the exact recovery route if the worker is wrong or stuck?

## Adaptation Pipeline

### 1. Task Classification

Before scheduling, classify the story into one primary task kind:

- `code_patch`
- `product_implementation`
- `validation_only`
- `browser_verification`
- `doc_fact_extraction`
- `readonly_discovery`
- `remote_readonly`
- `remote_apply`
- `coordination_only`

Do not dispatch one story that mixes multiple primary task kinds unless the
story contract explicitly says it is a coordinated multi-lane story.

### 2. Worker Capability Match

Each worker profile must describe:

- supported task kinds;
- supported environments;
- context tolerance;
- tool reliability assumptions;
- allowed side-effect level;
- patch breadth limits;
- verification dependence;
- recovery dependence;
- multi-story and multi-lane tolerance.

A worker must not receive a story outside its declared capability envelope.

### 3. Story Compilation

Each story must be compiled into an execution pack that includes:

- current story contract;
- source-of-truth files;
- must-read context;
- forbidden-read context;
- allowed writes;
- allowed actions;
- denied actions;
- required validation;
- output contract;
- evidence contract;
- recovery contract.

The worker should never need to infer these rules from broad prose scattered
across many files.

### 4. Environment Gating

Environment ownership is a first-class adaptation layer, not a footnote.

The execution pack must state:

- whether a precheck is required;
- whether the worker may restart or take over runtime processes;
- whether secrets are injected at runtime;
- whether DB/API/browser/remote targets are approved;
- whether the task runs in a copied workspace or the product workspace.

If precheck truth is missing, the worker should block early instead of
misclassifying environment failure as product failure.

### 5. Side-Effect Gating

`ALLOWED_WRITES` is necessary but not sufficient.

Weak workers also need an action capability whitelist:

- browser login allowed or not;
- backend restart allowed or not;
- DB/API read-only access allowed or not;
- remote read-only access allowed or not;
- remote apply allowed or not;
- delete/cleanup allowed or not;
- commit/push/merge/deploy allowed or not.

Action permissions should come from explicit approval profiles, not from worker
interpretation of vague prose.

### 6. Verification And Reconciliation

External verification must dominate worker confidence.

Verification should be layered:

- syntax/type/unit level;
- story-targeted validation level;
- end-to-end behavior level;
- real-operation/real-environment level when the story requires it.

After every turn, controller truth must reconcile:

- worker footer;
- controller verify result;
- story state;
- handoff state;
- task state;
- blocker classification.

No local cache or stale report may override authoritative truth.

### 7. Recovery

Recovery is not "retry until lucky".

Recovery must state:

- blocker class;
- smallest next route;
- whether retry is allowed;
- whether repair is required;
- whether approval is required;
- whether the lane must stop after repeated failure.

Weak workers should receive the last failed verify evidence as their recovery
starting point when the controller disproves a previous `DONE`.

## Required Contracts

A complete weak-worker system should maintain these contracts:

- worker capability profile;
- story execution pack;
- approval profile;
- handoff schema;
- evidence schema;
- blocker classification policy;
- reconciliation policy;
- benchmark suite for each worker/task lane.

## Non-Negotiable Rules

- Do not let the worker define the task kind privately.
- Do not let the worker expand the source of truth privately.
- Do not let the worker invent permissions privately.
- Do not let the worker self-certify `DONE`.
- Do not let retries replace blocker classification.
- Do not let broad workspace identity/persona files dominate task context.
- Do not let one story silently spill into another story.
- Do not let real-environment success be simulated by screenshots, HTTP 200,
  mock outputs, or unverified assumptions.

## Existing Repository Mapping

Current repository pieces already implement part of this model:

- loop config runtime boundaries: `docs/openclaw-autodev/loops/*.conf`
- story queue boundaries: `docs/openclaw-autodev/stories/*.json`
- runtime contract: `docs/openclaw-autodev/runtime-template.md`
- reliability and recovery: `docs/openclaw-autodev/reliability-model.md`
- approval action envelopes: `docs/openclaw-autodev/approval-profiles.json`
- Qwen local-patch harness contract: `docs/openclaw-autodev/qwen-worker-profile.md`

The remaining gap is to make these contracts explicit and reusable across
worker classes instead of leaving them implied in per-task prose.
