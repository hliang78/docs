# OneOps Redfish Hard-Cut Design

**Date:** 2026-06-25

**Status:** Draft for review

## Goal

Replace the existing Dell-branded `oneops_idrac_exporter` path with a single generic `oneops_redfish` path across agent, Teleabs, and OneOps so that:

- the agent exposes `[[inputs.oneops_redfish]]` instead of `[[inputs.oneops_idrac_exporter]]`
- emitted metrics use the `oneops_redfish_*` prefix instead of `idrac_*`
- OneOps can render and distribute Redfish OOB monitoring tasks through a first-class `oneops_redfish` Teleabs template, similar to the existing `oneops_ipmi` path

This is a hard cut. We will not preserve `oneops_idrac_exporter` as a runtime alias and we will not preserve `idrac_*` metric names.

## Current State

### Agent

- The custom Redfish collector exists only as `oneops_idrac_exporter`.
- The package directory, Go package name, input registration name, sample config, preview helper, and tests all use the iDRAC-specific naming.
- The collector still emits `idrac_*` metrics through its internal metrics prefix.

### Teleabs

- There is a generic `redfish-passthrough` template for the stock Telegraf `redfish` input.
- There is no custom `oneops_redfish` template that targets the agent-native collector.

### OneOps

- The Redfish OOB strategy set currently points to `redfish-passthrough`.
- Plugin semantics, target extraction, and credential usage are wired for `redfish`, not for `oneops_redfish`.
- The final rendered TOML for the Redfish OOB path is `[[inputs.redfish]]`, not `[[inputs.oneops_redfish]]`.

## Product Decision

We will treat the existing custom collector as a generic OneOps-native Redfish collector rather than a Dell-specific collector.

### Naming decision

- Plugin name: `oneops_redfish`
- Teleabs template id: `oneops-redfish-basic`
- Teleabs plugin type: `oneops_redfish`
- Metric prefix: `oneops_redfish`
- Resulting measurements: `oneops_redfish_*`

### Non-goals

- No backward-compatible alias for `oneops_idrac_exporter`
- No dual-write period for `idrac_*` and `oneops_redfish_*`
- No attempt to rename the built-in stock Telegraf `redfish` plugin

## Architecture

The implementation has four coordinated layers:

1. Agent plugin rename
2. Teleabs template introduction
3. OneOps rendering semantics and target extraction
4. OneOps Redfish OOB seed/default strategy switch

The core idea is to preserve the collector behavior and transport model while changing the public contract end-to-end from iDRAC branding to generic Redfish branding.

## Design Details

### 1. Agent Plugin Hard-Cut Rename

The agent-side plugin is the source of truth for the new name.

#### Required changes

- Rename directory `ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_idrac_exporter` to `.../oneops_redfish`
- Rename package declarations from `oneops_idrac_exporter` to `oneops_redfish`
- Update imports in:
  - `ctrlhub/controller/agent/cmd/agent/main.go`
  - `ctrlhub/controller/pkg/controller/config/telegraf_plugin_validator.go`
  - `ctrlhub/controller/test/idrac_preview_server.go`
  - any internal imports under the renamed package tree
- Change the registered Telegraf input name from `oneops_idrac_exporter` to `oneops_redfish`
- Change sample config header to `[[inputs.oneops_redfish]]`

#### Metric contract changes

- Replace the current metrics prefix `idrac` with `oneops_redfish`
- Any logic or tests that parse or assert names such as `idrac_system_power_on` must be updated to the new `oneops_redfish_*` form
- Prometheus-text-to-Telegraf conversion and split helpers must continue to derive measurement and field names correctly after the prefix change

#### Internal code boundaries

The collector may still contain Dell-specific endpoint handling internally where needed for vendor compatibility, but that internal knowledge must not leak into:

- package name
- plugin registration name
- generated measurement names
- sample config
- preview utility naming

### 2. Teleabs OneOps-Redfish Template

We will add a first-class Teleabs template that mirrors the role played by `oneops-ipmi-basic`.

#### Template contract

- File location:
  - `teleabs/teleabs-templates/categories/infrastructure/server/oob/oneops_redfish_basic.json`
- Template id:
  - `oneops-redfish-basic`
- Plugin type:
  - `oneops_redfish`
- Collection scope:
  - `remote`
- Target kind:
  - `ip`

#### Parameter model

The template should follow the current Redfish OOB path closely enough that OneOps can reuse its existing Redfish device semantics:

- `address`
- `username`
- `password`
- `collectors`
- `timeout`
- `interval`
- any additional safe technical knobs already supported by the custom collector

The shape should stay minimal. We should not expose every internal collector detail unless it is already part of the stable operational contract.

#### Output contract

The rendered TOML must produce:

```toml
[[inputs.oneops_redfish]]
```

The template `produces_metrics` list must be updated to reflect `oneops_redfish_*` measurement names rather than `idrac_*` or stock `redfish_*` names.

### 3. OneOps Rendering and Distribution Semantics

OneOps must recognize `oneops_redfish` as a first-class plugin type for remote OOB generation.

#### Semantics registration

In the monitoring-task semantics layer:

- add plugin semantics for `oneops_redfish`
- credential usage must be `TelegrafRedfish`
- default port must be `443`
- default collection type must be `redfish`
- default collection scope must be `remote`
- default target kind must be `ip`

#### Target extraction

In Teleabs/OneOps config generation:

- add target extraction for `oneops_redfish`
- address formatting should use the existing Redfish URL logic rather than IPMI endpoint formatting
- rendered target data should land in the template field expected by `oneops-redfish-basic`

#### Produces/capability bookkeeping

Update any code that reasons about template output or collection capability so that `oneops_redfish` is treated as the custom Redfish collector path rather than falling back to stock `redfish`.

The final downlink contract for the OOB Redfish path should be:

- OneOps strategy references `oneops-redfish-basic`
- generator resolves Redfish address and credentials
- emitted task TOML contains `[[inputs.oneops_redfish]]`

### 4. OneOps OOB Redfish Default Strategy Switch

The built-in Redfish OOB strategy set must stop pointing at `redfish-passthrough` and start pointing at the custom template.

#### Seed change

Update the Redfish OOB seed so that:

- strategy set remains `server_oob_redfish`
- strategy id remains `server_oob_redfish_strategy`
- template id changes from `redfish-passthrough` to `oneops-redfish-basic`

#### Result

After the seed switch, the out-of-band Redfish quick-apply and auto-apply path should produce OneOps-native Redfish tasks by default.

## Migration Impact

This is intentionally breaking for old names.

### Expected breaking changes

- old TOML snippets using `[[inputs.oneops_idrac_exporter]]` stop working after the rename
- old tests or dashboards expecting `idrac_*` measurements must be updated
- preview tooling and developer scripts that import or reference the old package name must be updated

### Why we accept the break

- the old name is now misleading for product scope
- dual naming would create a permanent maintenance split across agent, Teleabs, and OneOps
- the user explicitly chose not to preserve the old name

## Testing Strategy

### Agent tests

- plugin registration test must expose `oneops_redfish`
- sample config test must use `[[inputs.oneops_redfish]]`
- metrics-prefix and split-name tests must assert `oneops_redfish_*`
- any preview-server or validator tests must compile with the renamed package path

### Teleabs tests

- template loading must find `oneops-redfish-basic`
- stable render tests must render `[[inputs.oneops_redfish]]`
- `produces_metrics` assertions must verify the `oneops_redfish_*` contract

### OneOps tests

- plugin semantics tests must recognize `oneops_redfish`
- target extraction tests must resolve Redfish OOB addresses for `oneops_redfish`
- config generation tests must render `[[inputs.oneops_redfish]]`
- Redfish seed tests must assert that `server_oob_redfish` references `oneops-redfish-basic`
- quick-apply / OOB resolver tests must continue to bind `redfish_outband` credentials and port `443`

## Risks and Mitigations

### Risk: hidden references to old names

The old name appears in imports, helper tools, sample configs, and tests. A shallow rename will miss some of them.

Mitigation:

- use repository-wide search for `oneops_idrac_exporter`
- use repository-wide search for `idrac_`
- use repository-wide search for `[[inputs.oneops_idrac_exporter]]`

### Risk: metric-manifest drift between template and collector

If the collector emits one set of names and Teleabs advertises another set, downstream strategy behavior and attach configuration become misleading.

Mitigation:

- update Teleabs `produces_metrics` from the collector contract rather than inventing names
- add direct assertions in tests for critical measurement names

### Risk: OneOps still routes Redfish tasks to stock `redfish`

If the seed or semantics layer is only partially updated, the UI may still create old-style tasks.

Mitigation:

- seed test must assert `oneops-redfish-basic`
- config-generation test must assert final TOML contains `[[inputs.oneops_redfish]]`

## Acceptance Criteria

The change is complete when all of the following are true:

- there is no remaining runtime registration for `oneops_idrac_exporter`
- agent capability lists expose `oneops_redfish`
- the collector emits `oneops_redfish_*` metrics
- Teleabs loads and renders `oneops-redfish-basic`
- OneOps semantics and target extraction recognize `oneops_redfish`
- `server_oob_redfish` defaults to `oneops-redfish-basic`
- OneOps-generated Redfish OOB tasks render `[[inputs.oneops_redfish]]`

## Open Questions Resolved

- Preserve old name? No.
- Preserve `idrac_*` metrics? No.
- Include OneOps rendering and distribution in scope? Yes.
- Treat the custom collector as generic Redfish rather than Dell-only? Yes.
