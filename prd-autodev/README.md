# PRD Autodev To OpenClaw Handoff

This folder is the product-side staging area before work enters the OpenClaw
automation queue. A PRD story package is not ready just because it is useful to
read. It is ready only when an OpenClaw worker can safely select one story and
finish one narrow turn inside the target loop rules.

## Program Ownership

Each PRD topic must own exactly one product/program concern. Do not use one PRD
folder to drive unrelated automation tasks.

Current important topic boundaries:

- `oneops-poc-concern-autotest`: serves the `poc-ct` exploration-driven PoC
  testing loop only.
- `oneops-engineering-docs-standardization`: serves the `dev-docs` engineering
  documentation governance loop only.

## Required Flow

1. Capture the original request in the topic folder.
2. Produce discovery, alignment, PRD, and test/evidence expectations as files.
3. Split the PRD into a reviewed story package under
   `docs/prd-autodev/<topic>/story-packages/`.
4. Audit the package against the target OpenClaw loop before publishing:

```bash
scripts/prd-openclaw-sync.mjs <topic> <task-group> --dry-run
```

5. Fix any story audit errors or coarse warnings before `--publish-reviewed`.
6. Publish only reviewed packages:

```bash
scripts/prd-openclaw-sync.mjs <topic> <task-group> --publish-reviewed
```

## Story Readiness Rules

Each story must be one worker turn, not a mini project. Use the active
OpenClaw loop config as the contract:

- `lanes` must match real loop IDs from `docs/openclaw-autodev/loops/*.conf`.
- `allowedPaths` must be covered by that lane's `ALLOWED_WRITES`.
- `validation` must fit the lane's `VALIDATION_COMMAND` or name a precise
  evidence-only check.
- `acceptance` must describe observable outcomes, not broad intent.
- `dependsOn` must model real ordering. If order matters, use
  `executionMode: "dependency-chain"` and wire every later story to the exact
  prior story.
- Multi-lane stories need explicit handoff/coordination. Prefer separate FE and
  BE stories unless both lanes are genuinely required for the same evidence
  gate.
- Evidence output must be named. A worker should know which `summary.md`,
  report, JSON, screenshot, or matrix row it is expected to create or update.

## PRD vs Execution Boundary

Keep PRD at the program and batch level. PRD owns the large objective, round
goal, release/readiness gate, and whether the next batch should exist at all.
OpenClaw execution owns the small operational path: retries, repair,
authorization, environment preconditions, and bounded reruns inside the current
goal.

Do not create a new PRD batch just because execution hit one of these:

- local runtime or tooling blockers such as Chrome, DevTools, gateway token,
  login/session, missing fixture, missing credential, or broken harness
- a bounded approval/authorization question that can be answered without
  changing the larger program scope
- a single closing probe whose only job is "validate once more or record the
  blocker"

Those belong to execution-side `BLOCKED` / `APPROVAL` / repair handling first.
Only return to PRD when the evidence proves the large goal, scope, acceptance,
sequencing, or next batch decision itself must change.

Exception: when the program is already in its final closure stage, PRD may send
down one small validation/testing task whose direct purpose is to decide
`close` / `continue` / `stop`. Even then, keep an efficiency check:

- prefer folding the check into the current execution or repair batch when that
  is equally clear
- use a standalone tiny PRD batch only when it is the fastest clean way to make
  the final readiness decision
- do not keep spawning repeated single-probe batches for environment recovery,
  login/session repair, or other execution-side preconditions

## Anti-Coarse Checklist

Before setting a package to `"status": "reviewed"`, check every story:

- Can one worker understand it without rereading the whole PRD?
- Can it complete in the loop's `MAX_TURNS=1` and time budget?
- Does it touch one page, API, harness, evidence file, or contract seam?
- Are non-goals explicit enough to prevent wandering?
- Are write paths narrow enough that the worker cannot edit unrelated modules?
- Is the validation command or evidence review deterministic?
- If the story blocks, will the `BLOCKED` question be specific enough for a
  human to answer?
- Is this really batch-level product progress, rather than one environment check
  or repair gate that should stay in the execution lane?
- If this is a final-stage tiny validation task, is it truly the most efficient
  way to make the close/continue/stop decision?

If the answer is no, split the story. The package should contain more small
stories with dependencies, not fewer broad stories.

## Current Sync Guard

`scripts/prd-openclaw-sync.mjs` now writes a `Story Quality Audit` section to
`docs/prd-autodev/<topic>/evidence/automation-sync.md`. Blocking audit errors
prevent `--publish-reviewed`; warnings are review prompts for story slicing and
evidence clarity.

## Multi-Round Cycle Controller

For programs that should keep looping through:

```text
reviewed batch -> OpenClaw execution -> evidence -> next batch planning
```

use:

```bash
node scripts/prd-program-cycle.mjs <topic> <task-group> --publish-reviewed
```

What it does:

- refreshes `automation-sync.json` through `scripts/prd-openclaw-sync.mjs`
- checks whether the current reviewed batch is still running, blocked, or done
- when a reviewed batch is fully done, writes a planning brief under
  `docs/prd-autodev/<topic>/evidence/cycle-briefs/`
- optionally triggers a planner command exactly once per completed batch
- persists cycle state in `docs/prd-autodev/<topic>/evidence/cycle-state.json`

Topic-local control file:

```json
{
  "enabled": true,
  "taskGroup": "d2on",
  "publishReviewed": true,
  "plannerCommand": "/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh start d2on-prd",
  "storyFile": "/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/stories/d2on.json",
  "stopFile": "/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/device-v2-onboarding-observability/STOP"
}
```

Planner contract:

- read the generated planning brief and completed batch evidence
- either draft/promote the next batch, or close the program by updating
  `final-readiness.md`
- do not solve runtime/environment/authorization blockers that the execution
  lane can repair or escalate directly
- if the program should stop without continuing, write the configured stop file
