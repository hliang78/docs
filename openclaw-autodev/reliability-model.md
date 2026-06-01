# OpenClaw Autodev Reliability Model

This note defines the current reliability direction for the Weixin router,
agent loop, and repair agent. It is intentionally small: the goal is to make
the existing Bash control plane safer before any larger rewrite.

## Layers

- Weixin router: parse one deterministic command and classify it as read,
  change, repair, or danger.
- Agent loop: own task scheduling, worker prompt creation, bounded turn
  execution, state transitions, and handoff.
- Repair agent: own one-shot repair lifecycle for runtime/contract/evidence
  blockers. It must not continue business stories unless explicitly told.
- State manager: provide derived status, progress, story selection, cleanup,
  and event recording.

## State Sources

The completed worker session trajectory is the result source of truth. When an
ended OpenClaw trajectory contains a valid `LoopControl` footer, every local
state file below is only a projection cache and must be overwritten from that
trajectory:

1. `~/.openclaw/agents/<agent>/sessions/<session>.trajectory.jsonl`
2. `state/<task>/last-report.txt`
3. `state/<task>/last-control`
4. `state/<task>/state.json`
5. `state/<task>/current-story.json` and `stories/*.json`

`progress.json` is only active-turn telemetry. `handoff.md` is only cross-turn
context. `state/events.jsonl` is only the append-only audit trail.

Status commands should be derived views. They should not require humans to
reconcile contradictory files.

Core source ownership:

| Fact | Source of truth | Projection/cache only |
| --- | --- | --- |
| Final worker result | ended OpenClaw trajectory `LoopControl` | `last-report.txt`, `last-control`, `state.json`, story status |
| Story intent and boundaries | `docs/openclaw-autodev/stories/*.json` | prompt text, handoff text, worker memory |
| Current executable story | scheduler selection from story queue | `current-story.json` |
| Lane enabled/disabled | `state/<task>/enabled` | monitor/status text |
| Daemon liveness | process table | `supervisor.pid`, `state.json.pid` |
| Lock validity | lock owner pid plus process table | lock directory presence |
| BLOCK routing | `BLOCKER_POLICIES` and `recovery-decision` | prose docs, reports, router text |
| Repair lifecycle state | run pid, run log, closed marker, append-only events | `repair/<id>/status` |
| Provider health | provider probe output | blocker ticket text |
| Audit trail | `state/events.jsonl` | derived status/report files |

`work-detail.txt` is a derived diagnostic view. It must display only data that
comes from a current source of truth:

- runtime truth from the process table, enabled file, and live lock owner pid;
- active trajectory facts from the trajectory file;
- last authoritative result from an ended trajectory with a valid `LoopControl`.

It must not display raw `state.json`, `progress.json`, `handoff.md`, or
`last-report.txt` cache content. Those files may be used internally to find
paths, but inaccurate or stale cache data must not appear in detail output.

`monitor` task lines follow the same rule. They should not print separate
`Truth <group>:` rows. Group/business truth is folded into the corresponding
task lines. They should display only:

- `run` from process-table-backed runtime facts plus lock/model-slot ownership;
- `queue` from `scheduler-decision`, which is derived from enabled state, live
  daemon/lock, blocker state, and selectable story queue;
- `enabled` from the lane enabled file;
- `daemon` and `lock` from process-table-backed runtime truth;
- `active` from the current trajectory;
- `result` from the latest ended trajectory with a valid `LoopControl`.

They must not display raw `state.status`, `last-control`, `last-report`, raw
file size, or handoff text as facts.

`run` uses these meanings:

| Value | Meaning |
| --- | --- |
| `Working` | live daemon plus valid task lock |
| `Queued` | live daemon plus valid task lock, but the model slot is held by another live task |
| `DaemonIdle` | live daemon with no valid task lock |
| `Idle` | no live daemon; scheduler says wait or start is possible |
| `Blocked` | latest authoritative control/blocker requires manual/repair route |
| `ApprovalRequired` | business authorization is required |
| `Disabled` | lane enabled file says disabled |

`任务进度` / `openclaw-task-progress.mjs` follows the same contract:

- story counts and blocked/open/done distribution come from `stories/*.json`;
- runnable next story comes from `scheduler-decision`, not priority-only sorting
  or `current-story.json`;
- runtime lines come from the same monitor truth fields;
- provider probes, raw progress telemetry, handoff, and cached loop status are
  hidden unless a command explicitly asks for those diagnostics.

`status` and `daemon-report` are also derived views:

- `status` reuses the same task-line format as `monitor`; it must not show
  `LastReport`, raw `Status`, or raw `Control` from projection files.
- `daemon-report` is limited to supervisor facts: adopted pid, supervisor pid,
  live daemon roots, duplicates, lock owner, scheduler decision, business truth,
  and latest authoritative result.
- `daemon-report` JSON must not include `status`, `control`, `stateAgeMinutes`,
  or `reportAgeMinutes` fields for task rows.

## Events

Every externally visible state-changing command should append one compact
event:

```json
{"ts":"2026-05-14T19:00:00.000+08:00","target":"d2-fe","type":"router.command","source":"weixin-router","payload":{"class":"change","command":"retry"}}
```

Events are not the state store. They are the audit trail for debugging why the
state changed.

## Command Classes

- `read`: status, progress, detail, handoff, prompt preview, help, repair list.
- `change`: enable, disable, retry, approve, pool sync/start/stop, resident
  lifecycle.
- `repair`: repair start, stop, close.
- `danger`: cleanup, broad stop all, destructive future operations.

Router smoke tests must use `read` commands only unless the test explicitly
sets a mutation allowance.

## Reliability Rules

- A runner is successful only when shell rc and structured output agree.
- `status=timeout` or `stopReason=rpc` is blocked even if shell rc is zero.
- Exit codes `124` and `143` before useful work are controller/runtime exits,
  not business story results. If `progress.json` classifies `124` as
  `PromptStuck` or `ToolStuck`, the report must name that classification
  instead of using `Ticket: unknown`. `143` is classified under the same
  automation runtime route so story text cannot misclassify it as business
  authorization or optimization.
- `running` without a live pid is `stale`, not running.
- Repair agents are one-shot. They may leave evidence, but must not become
  business workers.
- `close` must make the lifecycle visible as `closed`.
- Prompt inputs must be budgeted. Large rules/context must be truncated with an
  explicit marker.

## PromptStuck / 124 / 143 Recovery

`PromptStuck` means the prompt was submitted but no model progress arrived
inside the configured stuck window. `ToolStuck` means a tool call did not
produce a result and no child process is alive. `openclaw-agent-exit-143`
means the worker process exited before useful business work completed. All
three are automation runtime blockers unless detail/report evidence proves a
more specific environment or business cause.

Standard recovery order:

1. Inspect the live detail:

   ```bash
   /Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh detail <task>
   ```

2. Run a provider probe:

   ```bash
   /Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh provider-check <task>
   ```

3. If the probe or detail shows stale runtime state, clean only the affected
   task loop/runtime state, then retry:

   ```bash
   /Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh cleanup <task>
   /Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh retry <task> "model/session health restored"
   ```

   Target-scoped cleanup must not purge global OpenClaw sessions or delete loop
   agents. Use `FULL_OPENCLAW_CLEANUP=1 ... cleanup all` only for an explicit
   global maintenance window.

4. If the failure is environment, test data, contract, or tool behavior rather
   than model/session health, start a repair agent instead of repeatedly retrying
   the business loop:

   ```bash
   /Users/huangliang/project/OneOPS-ALL/scripts/openclaw-repair-agent.sh start <task> "<concrete blocker>"
   ```

After two failed repair/retry attempts for the same blocker, stop and ask for a
human decision. Do not continue the story by broadening scope privately.

`retry` is guarded by the recovery gate:

- it may release a blocked lane only when the blocker class allows retry;
- repeated `automation.model_runtime` exits such as `124`/`143` are counted from
  the current story events;
- after two matching runtime exits, `retry` returns `RecoveryStopped`, disables
  only the affected task, and keeps the story blocked.

The gate is intentionally small and has no separate ticket store:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-state-manager.mjs recovery-decision <task>
```

Automatic recovery is available through:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh auto-recover <task>
```

It only performs the bounded safe path:

- `automation.model_runtime`: `provider-check`; if OK, target-scoped cleanup and
  one gated retry.
- `automation.health_check`: target-scoped cleanup and one gated retry.
- repeated runtime failures at the gate return `RecoveryStopped` and disable
  only the affected task/lane.
- business authorization, unknown blockers, and business repair blockers are
  reported but not automatically modified.

## Blocker Classes

Every `BLOCKED` or `APPROVAL` state should be classified before it is retried.
Use:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh blocker <task-or-group>
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh blocker-policy
```

Weixin equivalent:

```text
PF3 阻塞分类
D2BE 阻塞分类
D2FE 阻塞分类
CT 阻塞分类
```

Classes:

| Class | Owner | Correct Route | Stop Policy |
| --- | --- | --- | --- |
| `automation.model_runtime` | automation framework | provider-check -> cleanup stale session/model-slot -> retry | after two failed recoveries, stop only this task and keep story blocked |
| `automation.controller_or_story` | automation framework | fix controller or story metadata; validate story queue | disable only affected task until metadata validates |
| `automation.health_check` | automation framework | repair CT/framework health | keep CT blocked; do not stop product loops solely because CT failed |
| `environment.runtime` | environment repair | start repair agent for local runtime, dependency, fixture, DB, or tool blocker | after two failed repairs, stop only affected task/lane |
| `business.authorization` | business authorization | ask for the smallest explicit approval/decision | if rejected or unavailable, stop only affected story lane |
| `business.optimization` | business implementation | adjust story contract when stale, or run focused business repair | after two failed focused repairs or unsafe story adjustment, stop only affected story lane |
| `unknown.blocked` | human triage | classify before retry | do not broaden scope; stop only affected task if classification cannot be established |

Business blockers are split intentionally:

- `business.authorization`: the agent is not allowed to decide privately. This
  includes production behavior changes, tenant/auth/deploy boundaries, secret
  exposure, destructive operations, route switches, migrations, commit/push,
  ownership transfer, external integrations, or any explicit approval question.
- `business.optimization`: the work is inside an approved product area, but the
  code, contract, mapping, validation, UX, or story contract needs adjustment.
  If the story itself is stale or too narrow, update `scope`, `acceptance`,
  `validation`, `allowedPaths`, `lanes`, or `dependsOn` first, then continue.

For every class, the final fallback is minimal stopping: stop the smallest
affected task or lane, preserve handoff/evidence, and leave unrelated loops
running.

The policy table is executable source of truth, not prose. Add new ticket
patterns to `BLOCKER_POLICIES` in `scripts/openclaw-state-manager.mjs`, then
verify with:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-state-manager.mjs blocker-policy-json
/Users/huangliang/project/OneOPS-ALL/scripts/test-openclaw-blocker-routing.sh
```

## State Reconciliation

The controller must not allow split-brain task state. These files are reconciled
as one state model before `status`, `detail`, `scheduler-decision`, and
`blocker` classification:

- `docs/openclaw-autodev/state/<task>/last-control`
- `docs/openclaw-autodev/state/<task>/state.json`
- `docs/openclaw-autodev/state/<task>/current-story.json`
- `docs/openclaw-autodev/stories/*.json` story status and `laneStatus`

Use:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh reconcile <task-or-group>
```

Rules:

- If the latest ended worker trajectory has a valid `LoopControl` footer, it is
  authoritative. Reconciliation projects that footer to `last-report.txt`,
  `last-control`, `state.json`, and story status. No other state file can vote
  against it.
- If the current story lane is `blocked`, the task is reconciled to
  `LoopControl: BLOCKED` and `state.status=Blocked`.
- If the current story lane is `approval`, `approval_required`, or
  `needs_approval`, the task is reconciled to `LoopControl: APPROVAL` and
  `state.status=ApprovalRequired`.
- If the task still says `BLOCKED` / `APPROVAL` but the current story is
  completed by a later `DONE` report, the task is reconciled back to
  `LoopControl: DONE` and `state.status=Idle`.
- If `current-story.json` points to a story that no longer exists, or to a
  completed non-repeat story, it is removed so the scheduler cannot keep using
  stale active-story context.
- Repeat stories, such as CT health checks, may return to `open` after a `DONE`
  turn without being treated as split state.

Weixin equivalents are `PF3 状态收敛`, `D2FE 状态收敛`, `D2BE 状态收敛`, and
`CT 状态收敛`. Normal `状态`, `现场`, and `阻塞分类` paths also reconcile
automatically.

## Truth Status

Progress percentages are not enough to declare business completion. The trusted
status model separates runtime, queue, and business state:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh truth-status <task-or-group>
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-state-manager.mjs truth-json <task-or-group>
```

Fields:

| Field | Meaning |
| --- | --- |
| `RuntimeState` | daemon/loop execution state such as `Idle`, `DaemonIdle`, `Working`, `Blocked` |
| `QueueState` | story queue state such as `Complete`, `HasOpenStories`, `Blocked`, `MissingStoryFile` |
| `BusinessState` | business interpretation such as `Complete`, `InProgress`, `ContinuationSuggested` |
| `Accuracy` | `Verified`, `Conflict`, or `Stale` |
| `RequiredAction` | smallest next action before retrying or declaring completion |

Conflict examples:

- story queue is complete, but the latest report `Next` says to continue a
  business chain or next phase;
- loop says `DONE`, but current story/lane is still blocked or approval;
- queue has open stories, but all relevant lanes are disabled;
- duplicate daemon processes exist for the same task.

When `Accuracy=Conflict`, status/progress output must not claim final business
completion. It should say what is verified and what decision is required, for
example: add the next story, or add/mark an explicit closure story. The monitor
keeps one aggregate `TruthAccuracy` line and folds each task/group truth summary
into the matching task line as `story`, `biz`, `accuracy`, optional `block`, and
optional `need`.

## Daemon Supervision

Daemon ownership is part of the state model, not a side effect of shell
processes.

- A task may have at most one `openclaw-agent-loop.sh run-daemon <task>` process
  at a time.
- `docs/openclaw-autodev/state/<task>/supervisor.pid` is the adopted daemon pid.
  If it is stale but exactly one matching daemon is alive, cleanup adopts that
  daemon and rewrites `supervisor.pid`.
- If multiple matching daemons are alive, cleanup keeps one, terminates the
  duplicates, and records the kept pid.
- For repeat loops with `CONTINUE_AFTER_DONE=1`, `LoopControl: DONE` means the
  last block finished, not that the daemon should be ignored. The daemon remains
  schedulable and must prevent resident from starting a duplicate.
- For non-repeat loops, `DONE` plus a live daemon keeps `supervisor.pid` until
  the process exits; cleanup must not remove the supervisor first, because that
  lets resident start a parallel daemon.
- Shell wrapper parent/child processes for one daemon count as one daemon root;
  only independent roots are duplicates.
- Resident pool must call cleanup before scheduling and then trust
  `scheduler-decision`; it must not start a daemon if a live daemon is already
  adopted.

Operational commands:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh status <task>
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh cleanup <task-or-all>
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh reconcile <task-or-group>
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh daemon-report <task-or-group>
```

The daemon supervisor report is written to:

```text
docs/openclaw-autodev/state/daemon-supervisor/report.txt
docs/openclaw-autodev/state/daemon-supervisor/state.json
```

It includes resident status, pool status, adopted daemon pid, live daemon pids,
duplicates, lock owner, and current scheduler decision.

Cleanup scope is intentionally asymmetric:

- `cleanup <task>` is narrow. It runs local state/duplicate cleanup only for the
  target and skips global OpenClaw session purge and loop-agent deletion.
- `cleanup all`, `cleanup pool`, or `FULL_OPENCLAW_CLEANUP=1 cleanup <target>`
  may perform global OpenClaw maintenance. Use this only when no business lane
  is mid-turn, or when the intended outcome is a full supervisor reset.
- If a cleanup creates `openclaw-agent-exit-143`, classify it as
  `automation.model_runtime`, run `provider-check`, and retry only the affected
  lane. Do not convert it into business authorization/optimization.

## Repair Lifecycle Events

Every repair agent must produce append-only lifecycle events through
`scripts/openclaw-state-manager.mjs append-event`:

| Event | Meaning |
| --- | --- |
| `repair.submitted` | operator created a one-shot repair agent |
| `repair.started` | repair runner started and wrote pid/status |
| `repair.finished` | repair runner exited cleanly with OpenClaw `status=ok` |
| `repair.blocked` | repair runner failed or OpenClaw did not return `status=ok` |
| `repair.restart-prevented` | launchd tried to restart an already completed one-shot repair |
| `repair.stopped` | operator stopped an active repair |
| `repair.stop-noop` | operator stop found no live repair pid |
| `repair.closed` | temporary repair agent was deleted; evidence retained |

Repair context must include target status, blocker classification, daemon
supervisor report, detail, handoff, and stories. Repair does not enable or retry
the business loop by itself; it records a precise retry/close/blocker next step.

## Near-Term P0

- Add append-only events through the state manager.
- Log router command class before execution.
- Log loop state transitions via the central `write_state` path.
- Move the remaining router command classes into append-only events.
- Add daemon duplicate cleanup events in addition to the supervisor report.
- Keep expanding the blocker policy table until `unknown.blocked` trends toward
  zero instead of accumulating as exceptions.
- Keep compatibility with existing Weixin commands.
