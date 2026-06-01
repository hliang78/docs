# OpenClaw Autodev Stories

Story files are the Ralph-style work queue for OpenClaw agent-loop.

- Each loop reads one current story per worker turn.
- The worker should only work on the selected story.
- The controller updates story status from the final `LoopControl` footer.
- `done` stories are skipped; `open`, `in_progress`, `blocked`, and `approval`
  stories remain selectable so retry/approval can continue from the same unit.

Status values:

- `open`: ready for a worker.
- `in_progress`: work started and may continue.
- `blocked`: tool/runtime/project blocker needs repair or retry.
- `approval`: human approval required.
- `done`: complete and no longer selected.

