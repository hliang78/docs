# Strict Worker Harness Profile

Use this profile when a loop runs a bounded worker that needs a compiled
execution pack, tighter scope, and stronger controller-side verification than
the default prompt provides.

This profile is model-agnostic. It can back local models, cloud models, and
OpenAI-compatible gateways, including operator-routed endpoints such as a
cc-switch path.

## Intent

This profile does not make the base model smarter. It makes weaker or cheaper
workers more reliable in the OpenClaw automation environment by shrinking noisy
context, constraining patch shape, and forcing external verification.

## Recommended Config

```bash
HARNESS_PROFILE="strict-worker"
HARNESS_CONTRACT_DOC="/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/strict-worker-profile.md"
PATCH_MAX_FILES="3"
CONTROLLER_VERIFY_ON_DONE="1"
CONTROLLER_VERIFY_COMMAND="<same as validation command or stricter>"
AGENT_MODEL="<provider/model>"
THINKING="<off|minimal|low>"
```

Notes:

- `qwen-worker` is kept as a compatibility alias for older loop configs, but
  new loops should prefer `strict-worker`.
- Runtime-only model credentials should come from environment-backed OpenClaw
  provider config or external secret files, not repository files.
- Export `OPENCLAW_AGENT_MODEL` / `PROVIDER_PROBE_MODEL` before starting a loop
  when you want to switch models without editing the loop config.

## Contract

### Task Harness

- One turn should complete one bounded story only.
- If the active ticket is bigger than one safe turn, the worker should stop
  with `CONTINUE`, `BLOCKED`, or `APPROVAL` instead of expanding scope
  privately.
- `DONE` closes the current story when its acceptance is met, even if another
  story is queued next.
- `CONTINUE` means the same current story still needs another bounded turn; it
  should not be used as shorthand for "move on to the next story".

### Context Harness

- Start from current story, handoff, approval, and compact context docs.
- Follow the execution pack read-budget rules first. When the pack already
  names the exact files, read those directly instead of starting with broad
  shell search.
- Read targeted snippets, not whole modules, unless validation forces a wider
  read.
- When `ProjectRoot` points at a copied workspace, stay inside that workspace
  copy for reads and writes instead of jumping to same-named repo source paths.

### Tool Harness

- Preferred order: locate, read, plan, edit, verify, summarize.
- Prefer direct read/edit/browser tools over shell exec for search, grep, jq,
  or file inspection when the execution pack or loop rules say shell policy is
  tight.
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
- `DONE` is valid when the validation owner named by the execution pack ran.
  If the pack delegates heavy validation to controller verify on `DONE`, the
  worker should capture the pre-validation evidence it can actually observe and
  leave the full test/typecheck run to the controller.
- The controller should rerun verification on `DONE` and downgrade
  false-positive completions to `BLOCKED`.
- If the previous handoff ticket is `controller-validation-failed`, the next
  turn should read the controller verify evidence first and treat it as the
  recovery starting point, not as optional context.
