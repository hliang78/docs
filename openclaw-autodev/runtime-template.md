# {{MODULE_NAME}} OpenClaw Autodev Runtime

Task ID: `{{TASK_ID}}`

This file defines the runtime contract for OpenClaw direct-mode autonomous
development of `{{MODULE_NAME}}`.

## Mode

Current mode: L1 autonomous development, manual merge.

Operational driver: explicit agent-loop controller.

OpenClaw cron is not the continuation mechanism for sustained development.
Cron may be used separately for independent periodic tasks, but development
progress must be driven by a controller that submits bounded direct agent turns
and reads a `LoopControl` footer.

## Reporting Cadence

The normal cadence is one WeChat report per bounded loop block.

During the block, the loop should continue autonomous development without
asking for routine approval. It may send or return an approval question only
when an explicit approval boundary or hard blocker is reached.

When multiple autonomous tasks share the same WeChat conversation, every normal
report and every approval question must include `Task: {{TASK_ID}}` so the
human can tell which development loop is speaking.

## Immediate Start

A human WeChat command such as `启动 {{TASK_ID}}` must start the explicit
agent-loop controller immediately. Do not perform long-running development
inside a passive direct chat turn.

The only sustained-development entry point is:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh start {{TASK_ID}}
```

If the task is not listed, add a config file under
`docs/openclaw-autodev/loops/` and update the task groups in
`scripts/openclaw-agent-loop.sh`.

## Per-block Budget

Each loop block must observe these limits:

- Work for one bounded block, then report once.
- Keep only one active ticket at a time.
- A ticket may advance through multiple development sections in the same block:
  intake, design, implementation, test, repair, evidence, and review.
- Prefer the oldest unfinished `Risk: Low` ticket with explicit `AllowedPaths`.
- If the active ticket is completed, validated, and recorded before the block
  budget is exhausted, the loop may pick the next eligible low-risk ticket.
- If the git worktree is dirty, inspect existing in-scope changes first and
  either finish/verify that work or report the blocker. Do not start unrelated
  new work on top of unknown changes.
- Run at most two automatic repair loops after a failing validation.
- Stop near the end of the block and produce the required report.
- Do not keep retrying network or toolchain failures. Report the environment
  blocker with the exact command and key output.

## Backlog Continuation

When the current next-step section in the checklist is fully implemented,
autonomous development must continue by turning the remaining checklist into
small, reviewable backlog tickets.

Continuation order:

1. Update checklist status and evidence for the completed next-step tickets.
2. Re-read the checklist and find remaining `[ ]` or `[~]` items.
3. Split the next unfinished closure item into one or more small backlog tickets.
4. Add the tickets to the backlog with `Status`, `Risk`, `AllowedPaths`, `Goal`,
   `Acceptance`, and expected tests.
5. Only implement tickets that are `Risk: Low`, have explicit `AllowedPaths`,
   stay within allowed writes, and can be validated with `{{VALIDATION_COMMAND}}`.

Do not silently promote high-risk checklist items into autonomous work. Items
involving production writes, DB/migrations, real external integrations,
credentials, tenant/auth semantics, feature flags, canaries, or ownership
transfer require an approval question first.

## Strict Closure

The checklist is the primary project state machine. Every autonomous block must
update it when a checklist item changes state:

- `[ ]` means not started.
- `[~]` means started but not closed.
- `[x]` means implemented, validated, and evidenced.

Do not mark an item `[x]` unless code/docs/evidence are updated and the
configured validation command has passed or the item is docs-only with its
explicit acceptance satisfied.

When every checklist item is `[x]`, autonomous development must stop creating
new scope. The final blocks should perform strict closure only:

1. Run the configured validation command.
2. Verify backlog entries are Done or intentionally out of scope.
3. Verify every completed item has evidence or a clear docs-only acceptance.
4. Produce a final closure report with validation results, remaining manual
   approval gates, residual risks, and recommended human review points.
5. Ask through WeChat before moving beyond closure into production replacement,
   commit mode, ownership transfer, merge, push, or deployment.

## Allowed Writes

Autonomous blocks may write only these paths:

```text
{{MODULE_PATH}}/**
{{DOCS_PATH}}/**
{{EVIDENCE_PATH}}/**
```

## Approval Required

Stop and ask through WeChat before doing any of the following:

- Modify files outside the allowed write paths.
- Delete files.
- Run broad validation outside the configured acceptance command.
- Add or upgrade third-party dependencies.
- Touch production configuration, migrations, credentials, auth, tenant logic,
  or real external integrations.
- Commit, push, merge, or open a pull request.
- Continue after two failed repair attempts.

## Validation

The default acceptance command is:

```bash
{{VALIDATION_COMMAND}}
```

## Required Output

Every direct agent turn must end with this machine-readable footer:

```text
LoopControl: CONTINUE|DONE|BLOCKED|APPROVAL
Task:
Status:
Ticket:
Changed:
Tests:
Next:
```

WeChat reports must stay short:

- At most 8 lines.
- Fit on one phone screen.
- Do not include long logs, diffs, stack traces, or full file lists.
- If many files changed, summarize by directory and mention only the key files.
- For tests, include only the command and pass/fail/blocker key line.

When code or docs changed, also create or update a ledger entry under:

```text
{{EVIDENCE_PATH}}/<ticket-id>/summary.md
```

## Token And Context Discipline

- Use lightweight context and read only the files needed for the selected ticket.
- Prefer docs and evidence files over long session memory.
- Avoid repeatedly printing large diffs or full test logs.
- Keep WeChat reports short; include only the failing command and key lines when
  blocked. Put detailed evidence in files, not in WeChat.
