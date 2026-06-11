# SNMP Metric Capability Contract Strict Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the minimal SNMP metric capability contract for base common metrics without expanding into UI polish, Grafana JSON generation, backend publishing, or full metric standardization.

**Architecture:** Keep standardization in the SNMP strategy contract resolver. Strategy/Profile defines raw source mapping, transform rules, and record metadata; Prometheus recording rules are represented as metadata only in this phase; Grafana-facing logic consumes capability support state later. Unknown or vendor-specific metrics remain config-driven.

**Tech Stack:** TypeScript, Vue 3 frontend repo `/OneOPS/OneOps-UI`, smoke scripts bundled with esbuild, `vue-tsc` typecheck.

**Execution Status:** The original frontend-only data model scope in this plan has been implemented and verified. Do not silently append backend, Prometheus publisher, Grafana JSON, or extra metric domains to this plan. Any further implementation needs a new strict plan or an explicit addendum approved by the user.

---

## Scope Lock

This plan must be followed in order. Do not add UI features, backend APIs, Grafana JSON generation, Prometheus rule publishing, asset model changes, or broad refactors while executing this plan.

Allowed files for this plan:

- `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricContract.ts`
- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMibProfiles.ts`
- `/OneOPS/OneOps-UI/scripts/snmp-metric-contract-smoke.ts`
- `/OneOPS/OneOps-UI/scripts/snmp-profile-resolution-smoke.ts`
- `/OneOPS/OneOps-UI/scripts/snmp-workspace-view-smoke.ts`
- `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

Stop and ask before touching any other file.

Out of scope:

- no new Vue UI controls,
- no Grafana dashboard JSON generation,
- no backend persistence schema changes,
- no Prometheus rule publishing/reload integration,
- no standardization of optical, fan, power, wireless, storage, or vendor-private metrics,
- no migration of existing saved child strategy diffs,
- no commit unless explicitly requested by the user.

## Current Baseline

Already completed before this plan:

- `interface_basic` capability import exists for complete `snmp_interface` raw tables.
- Interface capabilities include `if_name`, `if_in_rate`, `if_out_rate`, `if_oper_status`.
- Interface quality capabilities are now current base requirements:
  - `if_in_error_rate`,
  - `if_out_error_rate`,
  - `if_in_discard_rate`,
  - `if_out_discard_rate`,
  - `if_in_broadcast_ratio`,
  - `if_out_broadcast_ratio`.
- Interface capabilities carry `concept_key`, `capability_key`, `raw_source`, `transform_rule`, `recording_rule`, `recordability`, and `config_driven`.
- Unknown or unstandardized raw metrics can remain `config_driven`.
- Verified commands previously passed:
  - `npm run smoke:snmp-metric-contract`
  - `npm run smoke:snmp-profile-resolution`
  - `npm run smoke:snmp-workspace-view`
  - `npm run typecheck`

## Milestone 1: Add `system_basic` Capability Contract

**Purpose:** Add CPU and memory capability mapping for top-level SNMP fields only.

**Allowed behavior:**

- `cpuUsage` -> `cpu_usage_direct`
- `cpuIdle` -> `cpu_usage_from_idle`
- `memUsage` -> `memory_usage_direct`
- `memUsed + memTotal` -> `memory_usage_used_total`
- `memFree + memTotal` -> `memory_usage_free_total`
- unknown top-level metrics remain `config_driven`

**Not allowed:**

- no CPU core table aggregation yet,
- no 1m/5m CPU rolling-window variants yet,
- no vendor-specific OID catalog,
- no UI display changes.

### Task 1.1: Write Failing Smoke Coverage For `system_basic`

**Files:**

- Modify: `/OneOPS/OneOps-UI/scripts/snmp-metric-contract-smoke.ts`

- [x] **Step 1: Add a direct CPU/memory import assertion**

Add a smoke block that imports top-level fields:

```text
cpuUsage
memUsage
temperature
```

Expected contract:

```text
metric_groups:
  - system_basic
  - device_metrics or equivalent config-driven group for temperature

system_basic fields:
  cpu_usage_direct
    concept_key: cpu_usage
    capability_key: cpu_usage_direct
    raw_source.field: cpuUsage
    transform_rule.type: direct
    recording_rule.record: oneops:cpu_usage_direct:ratio

  memory_usage_direct
    concept_key: memory_usage
    capability_key: memory_usage_direct
    raw_source.field: memUsage
    transform_rule.type: direct
    recording_rule.record: oneops:memory_usage_direct:ratio

temperature:
  config_driven: true
```

- [x] **Step 2: Add expression CPU/memory import assertion**

Add a smoke block that imports top-level fields:

```text
cpuIdle
memUsed
memTotal
memFree
```

Expected `system_basic` fields:

```text
cpu_usage_from_idle
  concept_key: cpu_usage
  transform_rule.type: expression
  transform_rule.expression: 100 - cpuIdle
  raw_source.fields: [cpuIdle]
  recording_rule.record: oneops:cpu_usage_from_idle:ratio

memory_usage_used_total
  concept_key: memory_usage
  transform_rule.type: expression
  transform_rule.expression: memUsed / memTotal * 100
  raw_source.fields: [memUsed, memTotal]
  recording_rule.record: oneops:memory_usage_used_total:ratio

memory_usage_free_total
  concept_key: memory_usage
  transform_rule.type: expression
  transform_rule.expression: 100 - memFree / memTotal * 100
  raw_source.fields: [memFree, memTotal]
  recording_rule.record: oneops:memory_usage_free_total:ratio
```

- [x] **Step 3: Run the smoke and verify RED**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-metric-contract
```

Expected: FAIL because `system_basic` capability mapping does not exist yet.

### Task 1.2: Implement Minimal `system_basic` Mapping

**Files:**

- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricContract.ts`

- [x] **Step 1: Add helper functions only inside `snmpMetricContract.ts`**

Add focused helpers near existing capability helpers:

```text
canBuildSystemBasicGroup(fields)
buildSystemBasicGroup(fields, context)
createSystemCapabilityField(...)
```

Do not create a new file in this milestone.

- [x] **Step 2: Build `system_basic` only from top-level SNMP fields**

The import path should:

```text
top-level passthrough_config fields
  -> recognized CPU/memory capability fields
  -> system_basic group

unrecognized top-level fields
  -> existing config-driven group
```

- [x] **Step 3: Preserve raw export**

When exporting a semantic field, use:

```text
field.raw_source.field
field.raw_source.oid
```

Do not export semantic names such as `cpu_usage_from_idle` as raw SNMP field names.

- [x] **Step 4: Run the smoke and verify GREEN**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-metric-contract
```

Expected: PASS.

## Milestone 2: Align Profile Seeds To Capability Naming

**Purpose:** Prevent profile-defined system metrics from drifting back to single generic `cpu_usage` / `memory_usage` keys.

### Task 2.1: Update Profile Seeds Conservatively

**Files:**

- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMibProfiles.ts`
- Modify if needed: `/OneOPS/OneOps-UI/scripts/snmp-profile-resolution-smoke.ts`

- [x] **Step 1: Change `system_health` naming only if tests require it**

Preferred target:

```text
system_basic
  cpu_usage_direct
  cpu_usage_from_idle
  memory_usage_direct
  memory_usage_used_total
  memory_usage_free_total
```

If changing this breaks existing profile reload behavior, stop and adjust only after adding a failing smoke assertion.

- [x] **Step 2: Keep profile changes metadata-only**

Do not add vendor-specific OID mapping here.

- [x] **Step 3: Run profile smoke**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-profile-resolution
```

Expected: PASS.

## Milestone 3: Add Pure Data Panel Capability Support State

**Purpose:** Give later UI/Grafana work a stable data function without building UI now.

### Task 3.1: Add Support-State Resolver

**Files:**

- Modify: `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricContract.ts`
- Modify: `/OneOPS/OneOps-UI/scripts/snmp-metric-contract-smoke.ts`

- [x] **Step 1: Define support states**

Use only these states:

```text
supported
partial
unsupported
config_driven
```

- [x] **Step 2: Add a pure resolver**

Add a function with this shape:

```text
resolvePanelCapabilitySupport(contract, panelRequirement)
```

It should choose from already-declared capabilities. It must not inspect raw SNMP config directly.

- [x] **Step 3: Add smoke coverage**

Smoke cases:

```text
CPU panel accepts [cpu_usage_direct, cpu_usage_from_idle]
contract has cpu_usage_from_idle
result: supported, selected cpu_usage_from_idle

Memory panel accepts [memory_usage_direct, memory_usage_used_total]
contract has no memory capability
result: unsupported

Vendor custom panel uses config-driven query
result: config_driven
```

- [x] **Step 4: Run focused verification**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-metric-contract
```

Expected: PASS.

## Milestone 4: Documentation Sync

**Purpose:** Keep the handoff accurate so later work does not reopen settled decisions.

### Task 4.1: Update Handoff With Actual Implementation State

**Files:**

- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [x] **Step 1: Add completed implementation notes**

Record:

```text
interface_basic capability mapping
interface quality capability mapping
system_basic capability mapping
config-driven fallback
recording_rule metadata only, not published
panel capability support resolver if Milestone 3 is complete
```

- [x] **Step 2: Preserve out-of-scope reminders**

Keep explicit warnings:

```text
no full standardization
no UI-first expansion
no Grafana JSON generation in this phase
no Prometheus rule publishing in this phase
```

## Required Verification Before Any Completion Claim

Run all commands from `/OneOPS/OneOps-UI`:

```bash
npm run smoke:snmp-metric-contract
npm run smoke:snmp-profile-resolution
npm run smoke:snmp-workspace-view
npm run typecheck
```

Expected:

```text
snmp metric contract smoke passed
snmp profile resolution smoke passed
snmp workspace view smoke passed
typecheck exits 0
```

Do not claim completion if any command fails or does not finish.

## Strict Stop Rules

Stop and ask the user before proceeding if:

- a task requires changing Vue UI components,
- a task requires backend API/schema changes,
- a task requires creating actual Prometheus recording rule files,
- a task requires generating Grafana dashboard JSON,
- a task requires standardizing a non-base metric domain,
- a task requires modifying files outside the allowed list.

## Audit Addendum: Next Data-Model Gate

The 2026-06-11 read-only audit found that the current contract is a valid first pass, but a small closure gate is required before backend/Grafana work.

Allowed next-gate topics, if the user approves a follow-up plan:

- Decide whether error/discard capabilities represent per-second rate, window delta, or separate variants.
- Promote `ifSpeed` from config-driven raw field to a first-class base input/capability if current panels depend on it.
- Add explicit interface utilization capabilities only if needed for current Grafana panel parity.

Deferred unless explicitly approved:

- `device_reachable`,
- `system_uptime`,
- host-resources memory table normalization,
- vendor-private CPU/memory OID catalogs,
- backend authoritative resolver implementation,
- Prometheus recording-rule generation/publishing,
- Grafana dashboard JSON materialization.
