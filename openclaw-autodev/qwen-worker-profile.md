# Qwen Worker Harness Profile

Use this profile when a loop runs a local small-step worker such as
`ollama/qwen3.6:latest`.

## Intent

This profile does not improve the base model. It improves effective behavior in
the OpenClaw automation environment by tightening task scope, shrinking noisy
context, constraining patch shape, and forcing external verification.

## Recommended Config

```bash
HARNESS_PROFILE="qwen-worker"
HARNESS_CONTRACT_DOC="/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/qwen-worker-profile.md"
PATCH_MAX_FILES="3"
CONTROLLER_VERIFY_ON_DONE="1"
CONTROLLER_VERIFY_COMMAND="<same as validation command or stricter>"
AGENT_MODEL="ollama/qwen3.6:latest"
THINKING="off"
```

Minimal example loop config:

```text
docs/openclaw-autodev/qwen-worker-loop.conf.example
```

Notes:

- `ollama/qwen3.6:latest` is the currently verified working path in this repo.
- The direct `qwen/qwen3.6:latest` provider path currently returns `HTTP 404`
  and should not be used for sustained loop work until the provider mapping is
  fixed.
- `thinking=off` is required for the current Ollama-backed qwen3.6 model path.

## Contract

### Task Harness

- One turn should complete one bounded story only.
- If the active ticket is bigger than one safe turn, the worker should stop with
  `CONTINUE`, `BLOCKED`, or `APPROVAL` instead of expanding scope privately.
- `DONE` closes the current story when its acceptance is met, even if another
  story is queued next.
- `CONTINUE` means the same current story still needs another bounded turn; it
  should not be used as shorthand for "move on to the next story".

### Context Harness

- Start from current story, handoff, approval, and compact context docs.
- Use `rg` before opening source files.
- Read targeted snippets, not whole modules, unless validation forces a wider
  read.
- When `ProjectRoot` points at a copied workspace, stay inside that workspace
  copy for reads and writes instead of jumping to same-named repo source paths.

### Tool Harness

- Preferred order: locate, read, plan, edit, verify, summarize.
- Remote or shell failures must be surfaced as evidence, not silently bypassed.

### Patch Harness

- Identify target file list before editing.
- Keep the diff small and story-local.
- Run verification before claiming the patch is complete.
- After one failed repair retry, stop and hand the failure back to the
  controller.

### Verifier Harness

- Trust tests, type checks, and explicit runtime probes over the model's own
  confidence.
- `DONE` is valid only when configured validation ran and its result is captured
  in the footer.
- The controller should rerun verification on `DONE` and downgrade false-positive
  completions to `BLOCKED`.
- If the previous handoff ticket is `controller-validation-failed`, the next
  turn should read the controller verify evidence first and treat it as the
  recovery starting point, not as optional context.

## Pilot Evidence

The initial isolated pilot for this profile is stored under:

```text
docs/openclaw-autodev/evidence/qwen-harness-pilot/20260516-154642/
```

That pilot verified the working `ollama/qwen3.6:latest` path on a small patch
task and showed that the qwen worker can succeed when scope, writes, and
verification are tightly bounded.
