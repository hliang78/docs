# AgentRuntime Auto Nacos Bootstrap Design

## Goal

Simplify `agentruntime` startup so platform-config source selection is driven by repository/bootstrap configuration instead of a dedicated mode environment variable.

The new behavior should be:

- if `nacos_config.yaml` is present, `agentruntime` uses Nacos bootstrap
- if `nacos_config.yaml` is absent, `agentruntime` falls back to local file bootstrap
- local MVP acceptance must keep working without extra production-only setup

This design changes only platform-config bootstrap. Runtime instance config loaded from `RuntimeConfig` environment variables remains unchanged in this phase.

## Current Problem

Today `agentruntime` uses `ONEOPS_AGENT_RUNTIME_USE_NACOS` to decide whether to enter Nacos mode. This has two problems:

- startup intent is split across multiple environment variables, which makes production launch harder to reason about
- the repository already has a standard Nacos bootstrap convention based on `nacos_config.yaml`, so `agentruntime` is introducing a separate switch instead of reusing the platform contract

## Decision

Replace explicit mode selection by automatic source detection:

1. detect `nacos_config.yaml`
2. if present, choose Nacos as the platform-config source
3. if absent, choose local file bootstrap

The existence of `nacos_config.yaml` is treated as explicit operator intent. Once detected, bootstrap must stay on the Nacos path and fail fast on any Nacos bootstrap error. It must not silently fall back to local file loading.

## Source Selection Rules

`agentruntime` chooses platform-config source in this order:

1. if `nacos_config.yaml` exists in the working directory, use Nacos
2. otherwise, if `ONEOPS_AGENT_RUNTIME_CONFIG_FILE` is explicitly set, use that file and require it to exist
3. otherwise, if `local_config_test.yaml` exists, use that file
4. otherwise, fail startup with a clear no-source error

This preserves current local behavior while removing the dedicated Nacos mode environment variable.

## Nacos Bootstrap Rules

When `nacos_config.yaml` is present, `agentruntime` reuses the existing OneOps bootstrap conventions:

- bootstrap file: `nacos_config.yaml`
- bootstrap loader: existing logic aligned with `initialize/nacos.go`
- Nacos group: `BootStartConfig.Nacos.ClientConfig.Group`
- Nacos dataId: `cipher-aes-start-config`
- remote content: platform root YAML that decodes into `config.Config`

The Nacos load flow is:

1. load and parse `nacos_config.yaml`
2. initialize `BootStartConfig`
3. create Nacos config client
4. fetch `cipher-aes-start-config`
5. decode returned YAML into `config.Config`
6. continue opening DB and runtime bootstrap

This phase is startup-only bootstrap. It does not include runtime watch, hot reload, or dynamic refresh.

## Code Structure

The change stays inside `OneOps/cmd/agentruntime` bootstrap helpers.

Responsibilities are split as follows:

- `resolvePlatformConfigSource()`
  decides whether source is `nacos` or `file`
- `loadPlatformConfigFromSource()`
  loads raw platform config according to the chosen source
- `decodePlatformConfig()`
  decodes YAML text into `config.Config`

`main.go` remains thin and should only:

- load runtime env config
- load platform config
- open DB
- create runtime
- start HTTP server

The runtime, service, orchestration, and worker layers are not responsible for source selection.

## Failure Semantics

Failure behavior must be explicit and stable.

If `nacos_config.yaml` exists:

- `agentruntime` must attempt Nacos bootstrap
- any bootstrap error fails startup immediately
- no fallback to local file is allowed

If `nacos_config.yaml` does not exist:

- explicit `ONEOPS_AGENT_RUNTIME_CONFIG_FILE` must exist or startup fails
- otherwise `local_config_test.yaml` may be used as local fallback
- if no file source exists, startup fails clearly

This prevents ambiguous launches where production intent accidentally degrades into local mode.

## Script and Runbook Expectations

`start_multi_agent_closure_stack.sh` should no longer export or document `ONEOPS_AGENT_RUNTIME_USE_NACOS`.

Local helper behavior remains:

- default to file bootstrap through `local_config_test.yaml`
- keep `ONEOPS_AGENT_RUNTIME_CONFIG_FILE` visible for local overrides
- keep submit URL and callback env wiring unchanged

Runbook text should explain:

- local acceptance usually runs without `nacos_config.yaml`
- production-style bootstrap is enabled by placing `nacos_config.yaml`
- if Nacos bootstrap is selected, startup fails fast on any Nacos bootstrap error

## Testing Strategy

Validation should cover four levels.

### 1. Source selection unit tests

Cover:

- `nacos_config.yaml` present -> choose `nacos`
- no `nacos_config.yaml` -> file path logic still works
- explicit file path missing -> hard error
- default local fallback still works

### 2. Bootstrap loader tests

Cover:

- Nacos loader success path returns decoded `config.Config`
- Nacos client/bootstrap errors fail startup path
- no Nacos-to-file silent fallback when `nacos_config.yaml` exists

### 3. Command-level regression

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./cmd/agentruntime ./app/agentruntime/... ./app/orchestration/service/impl ./cmd -count=1
```

### 4. Real acceptance

Keep the real local loop:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
./scripts/start_multi_agent_closure_stack.sh start
```

Then:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
ONEOPS_API_BASE_URL=http://127.0.0.1:3001/api/v1 \
ONEOPS_UI_LOGIN_USERNAME=admin \
ONEOPS_UI_LOGIN_PASSWORD='admin@123' \
npm run acceptance:multi-agent-ticket-closure-real-api
```

This confirms that local file fallback still supports the current MVP closure path.

## Non-Goals

This phase does not include:

- Nacos watch or hot reload
- changing runtime env-based listener/callback settings
- splitting out a separate agentruntime-specific Nacos dataId
- refactoring runtime/service internals unrelated to bootstrap

## Recommended Outcome

Adopt auto-detected Nacos bootstrap with local file fallback.

This keeps startup simple for production, preserves the current local acceptance loop, and aligns `agentruntime` with the platform's existing Nacos bootstrap conventions instead of introducing a parallel mode toggle.
