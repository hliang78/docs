# SNMP Interface Panel Data Model Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the current data-model gap for existing interface Grafana panels without expanding into backend, Prometheus publishing, Grafana JSON generation, or broader metric standardization.

**Architecture:** Keep this as a frontend contract-model closure pass. `ifSpeed` becomes a first-class base interface capability because current broadcast and utilization-style queries depend on it. Error/discard capabilities remain per-second rate capabilities in this standard contract; legacy `idelta(...)` Grafana panels are documented as current-query behavior, not as the canonical capability model.

**Tech Stack:** TypeScript, Vue 3 frontend repo `/OneOPS/OneOps-UI`, smoke scripts bundled with esbuild, `vue-tsc` typecheck.

---

## Scope Lock

Allowed files for this plan:

- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricContract.ts`
- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMibProfiles.ts`
- `/OneOPS/OneOps-UI/scripts/snmp-metric-contract-smoke.ts`
- `/OneOPS/OneOps-UI/scripts/snmp-profile-resolution-smoke.ts`
- `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

Out of scope:

- no Vue UI changes,
- no backend resolver implementation,
- no Prometheus recording-rule publishing,
- no Grafana dashboard JSON generation,
- no `device_reachable`,
- no `system_uptime`,
- no host-resources memory table normalization,
- no vendor-private CPU/memory OID catalog,
- no new error/discard `delta` capabilities in this pass.

## Canonical Decisions For This Pass

Use these exact decisions while implementing:

```text
ifSpeed
  -> if_speed_bps
  concept_key: interface_speed
  capability_key: if_speed_bps
  raw_source.field: ifSpeed
  transform_rule.type: direct
  unit: bps
  recording_rule.record: oneops:if_speed_bps
```

```text
ifInErrors / ifOutErrors / ifInDiscards / ifOutDiscards
  -> keep existing *_rate capability keys
  transform_rule.type: rate
  unit: pps
  meaning: canonical per-second rate
```

Do not add `*_delta` keys now. If Grafana needs legacy `idelta(...)` parity later, it should be handled by the Grafana materialization layer or by a separate explicitly approved capability variant.

## Task 1: Add Failing Smoke Coverage For `if_speed_bps`

**Files:**

- Modify: `/OneOPS/OneOps-UI/scripts/snmp-metric-contract-smoke.ts`

- [x] **Step 1: Update the Telegraf-native interface field expectation**

Change the expected interface field list so `ifSpeed` is no longer config-driven. The expected row must be:

```typescript
['if_speed_bps', 'if_speed_bps', 'ifSpeed', false],
```

It should appear before the quality capabilities:

```typescript
[
  ['index', undefined, undefined, undefined],
  ['if_name', 'if_name', 'ifDescr', false],
  ['if_in_rate', 'if_in_rate', 'ifInOctets', false],
  ['if_out_rate', 'if_out_rate', 'ifOutOctets', false],
  ['if_oper_status', 'if_oper_status', 'ifOperStatus', false],
  ['if_speed_bps', 'if_speed_bps', 'ifSpeed', false],
  ['if_in_error_rate', 'if_in_error_rate', 'ifInErrors', false],
  ['if_out_error_rate', 'if_out_error_rate', 'ifOutErrors', false],
  ['if_in_discard_rate', 'if_in_discard_rate', 'ifInDiscards', false],
  ['if_out_discard_rate', 'if_out_discard_rate', 'ifOutDiscards', false],
  ['if_in_broadcast_ratio', 'if_in_broadcast_ratio', undefined, false],
  ['if_out_broadcast_ratio', 'if_out_broadcast_ratio', undefined, false],
  ['ifInUcastPkts', undefined, 'ifInUcastPkts', true],
  ['ifOutUcastPkts', undefined, 'ifOutUcastPkts', true],
  ['ifInNUcastPkts', undefined, 'ifInNUcastPkts', true],
  ['ifOutNUcastPkts', undefined, 'ifOutNUcastPkts', true],
]
```

- [x] **Step 2: Add metadata assertion for `if_speed_bps`**

Add an assertion that finds `if_speed_bps` and checks:

```typescript
assert.deepEqual(
  [
    speedCapability?.concept_key,
    speedCapability?.capability_key,
    speedCapability?.raw_source?.field,
    speedCapability?.transform_rule?.type,
    speedCapability?.recording_rule?.record,
    speedCapability?.unit,
  ],
  ['interface_speed', 'if_speed_bps', 'ifSpeed', 'direct', 'oneops:if_speed_bps', 'bps'],
);
```

- [x] **Step 3: Keep the default panel expectation unchanged**

Keep this assertion:

```typescript
assert.equal(
  telegrafNativeInterfaceContract.metric_groups[0].panel_specs.some(panel => panel.metrics.includes('ifSpeed')),
  false,
);
```

Then add:

```typescript
assert.equal(
  telegrafNativeInterfaceContract.metric_groups[0].panel_specs.some(panel => panel.metrics.includes('if_speed_bps')),
  false,
);
```

`if_speed_bps` is a base input/capability, not a standalone default panel.

- [x] **Step 4: Run focused smoke and verify RED**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-metric-contract
```

Expected: FAIL because `ifSpeed` still imports as config-driven.

## Task 2: Implement `if_speed_bps`

**Files:**

- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricContract.ts`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMibProfiles.ts`
- Modify if needed: `/OneOPS/OneOps-UI/scripts/snmp-profile-resolution-smoke.ts`

- [x] **Step 1: Treat `ifSpeed` as a standard interface raw field**

In `buildInterfaceBasicGroup`, include `speedField` in `standardRawFields` so it is not emitted again as a config-driven raw metric.

- [x] **Step 2: Add the capability field**

In the main `fields` list, insert this capability after `if_oper_status` and before quality fields:

```typescript
...(speedField
  ? [
      createInterfaceCapabilityField(
        speedField,
        'if_speed_bps',
        '接口速率',
        'interface_speed',
        'if_speed_bps',
        'direct',
        {
          unit: 'bps',
          value_type: 'number',
          visual_hint: 'table',
          recording_rule: { record: 'oneops:if_speed_bps', enabled: true },
        },
      ),
    ]
  : []),
```

Do not add `if_speed_bps` to default panel specs in this pass.

- [x] **Step 3: Add the profile seed field**

In `snmpMibProfiles.ts`, add the same semantic field after `if_oper_status`:

```typescript
{
  metric_key: 'if_speed_bps',
  name: '接口速率',
  role: 'metric',
  unit: 'bps',
  value_type: 'number',
  visual_hint: 'table',
  concept_key: 'interface_speed',
  capability_key: 'if_speed_bps',
  transform_rule: { type: 'direct' },
  recording_rule: { record: 'oneops:if_speed_bps', enabled: true },
  recordability: 'recordable',
}
```

- [x] **Step 4: Update profile smoke if it asserts the interface field order**

If `/OneOPS/OneOps-UI/scripts/snmp-profile-resolution-smoke.ts` lists interface field keys, insert `if_speed_bps` after `if_oper_status`.

- [x] **Step 5: Run focused smoke and verify GREEN**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-metric-contract
npm run smoke:snmp-profile-resolution
```

Expected:

```text
snmp metric contract smoke passed
snmp profile resolution smoke passed
```

## Task 3: Document The Closure Decision

**Files:**

- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [x] **Step 1: Update implemented scope**

Add:

```text
ifSpeed can become if_speed_bps
```

Near the existing `interface_basic` implemented list.

- [x] **Step 2: Update the audit decision section**

Record:

```text
ifSpeed is now first-class base capability metadata.
Error/discard standard capability remains rate/pps.
Legacy idelta panels are a Grafana materialization concern or future delta variant, not part of this pass.
```

## Required Verification Before Completion

Run from `/OneOPS/OneOps-UI`:

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
