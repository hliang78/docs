# OneOps AgentRuntime Dual-Source Config Bootstrap Design

## 1. Goal

Promote `agentruntime` from a locally bootstrapped runtime into a more production-shaped service by supporting dual-source platform configuration:

- prefer the same Nacos-backed startup configuration model already used by `OneOps`
- fall back to a local config file for local development and acceptance
- keep runtime-instance overrides in environment variables

This phase is intentionally narrow. It does not redesign worker behavior, orchestration logic, or runtime observability.

## 2. Scope

### Included

- `agentruntime` platform config loading with precedence:
  - Nacos startup config
  - local config file
  - explicit startup error
- continued env-based runtime overrides for:
  - listen address
  - callback URL
  - callback auth token
  - runtime timing and retry settings
- script and runbook alignment with the new bootstrap behavior
- tests for source precedence and local compatibility

### Excluded

- health probe endpoints
- metrics and dashboards
- auth model redesign
- Nacos write-back or dynamic hot reload
- generic config abstraction across every OneOps sidecar command

## 3. Current State

Today `agentruntime` can run real workers and pass real acceptance, but its platform bootstrap is still effectively local-file driven:

- runtime configuration comes from env via `RuntimeConfig`
- MySQL and other platform config are loaded from `ONEOPS_AGENT_RUNTIME_CONFIG_FILE`
- local helper scripts default to `local_config_test.yaml`

This is good enough for local closure, but not ideal for production-shaped deployment because it leaves `agentruntime` outside the main platform config path.

## 4. Desired Bootstrap Model

The target precedence is:

1. Nacos-backed startup config, when explicit Nacos startup conditions are available
2. local config file, when Nacos bootstrap is not requested
3. explicit startup failure when neither source is available

This applies only to platform/base configuration such as:

- MySQL DSN inputs
- debug token
- OneOps config-backed submit URL and related platform settings

Runtime-instance overrides remain env-driven and continue to sit above platform config for per-process deployment concerns.

## 5. Config Boundary

### 5.1 Platform config

Platform config is the shared baseline and should come from Nacos or local file:

- `mysql`
- `system.debug`
- `debugToken`
- future `agentruntime` platform-level config sections if needed

This keeps `agentruntime` aligned with the same operational source of truth as the main `OneOps` service.

### 5.2 Runtime config

Runtime config remains env-driven because it is instance-scoped rather than platform-scoped:

- `ONEOPS_AGENT_RUNTIME_LISTEN_ADDR`
- `ONEOPS_ORCHESTRATION_CALLBACK_URL`
- `ONEOPS_ORCHESTRATION_CALLBACK_AUTH_TOKEN`
- worker interval and retry env vars

This split avoids pushing pod- or process-specific deployment details into shared platform config.

## 6. Bootstrap Flow

The desired `cmd/agentruntime` startup flow becomes:

1. load `RuntimeConfig` from env
2. resolve platform config source:
   - if Nacos startup bootstrap is explicitly requested, load via the same Nacos config path used by `OneOps`
   - else if `ONEOPS_AGENT_RUNTIME_CONFIG_FILE` is present or a local default exists, load local YAML
   - else fail with a clear error
3. open MySQL from the resolved platform config
4. migrate `agentruntime_tasks`
5. construct repository, roles, callback client, and workers
6. start worker loops
7. expose submit API

## 7. Integration Strategy

This phase should reuse existing `OneOps` config-loading behavior where practical instead of introducing a brand-new config dialect.

The safest approach is:

- keep `RuntimeConfig` in `app/agentruntime/service`
- move platform-config source selection into a focused bootstrap helper under `cmd/agentruntime`
- reuse existing parsing conventions for local YAML and Nacos-started config content

This preserves the current runtime/service boundaries while avoiding leakage of Nacos bootstrap logic into task execution code.

## 8. Local Compatibility

The local multi-agent closure flow must continue to work without requiring Nacos.

That means:

- helper script still defaults to `local_config_test.yaml`
- real API acceptance remains runnable from the current developer machine flow
- local operators can still override the config file path explicitly

Nacos support is additive, not disruptive.

## 9. Failure Semantics

Startup must fail fast with operator-readable messages when:

- runtime env config is invalid
- Nacos bootstrap was requested but could not load config
- local config file path was requested but unreadable
- no valid platform config source exists
- MySQL connection cannot be established

Failure must be explicit. Silent fallback from broken Nacos to an unintended local file is not acceptable when Nacos mode was intentionally selected.

## 10. Testing Strategy

This phase should prove three behaviors:

1. source precedence
   - Nacos path wins when explicitly enabled
   - local file is used when Nacos mode is not enabled
2. bootstrap viability
   - `newServerRuntime` can still stand up workers with a real DB handle
3. local tooling compatibility
   - helper script exports the expected config file env var

Real acceptance remains the final confidence check, because the point of this phase is not theoretical correctness but preserving the real alert-to-ticket closure loop.

## 11. Success Criteria

This phase is complete when:

- `agentruntime` can bootstrap from Nacos-backed platform config
- local file fallback still works unchanged for local acceptance
- env runtime overrides still work
- helper script and runbook document the new behavior clearly
- existing real acceptance still passes
