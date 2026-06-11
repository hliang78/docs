# SNMP Metric Groups And Dashboard Family Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the SNMP strategy editor foundation that stores metric groups and panel specs while preserving future Grafana dashboard-family integration.

**Architecture:** Keep this phase frontend-focused and backward-compatible by storing the new contract in existing strategy `parameters.metric_groups`. Add typed contract helpers, an SNMP-specific form, MIB profile loading, inheritance states, and a dashboard impact preview. Do not generate Grafana JSON in this phase.

**Tech Stack:** Vue 3 `<script setup>`, TypeScript, Ant Design Vue, existing OneOps API wrappers, esbuild smoke scripts.

---

## File Structure

- Create `OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
  - Owns the serializable metric group, field, panel, profile, and impact preview types.
- Create `OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricContract.ts`
  - Pure helpers for normalization, default contract creation, inheritance resolution, stable key validation, and display summaries.
- Create `OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMibProfiles.ts`
  - Small frontend seed profile registry for H3C Comware, Huawei VRP, Cisco IOS, and generic SNMP. This is isolated so a future backend-backed profile endpoint can replace it without changing the SNMP editor contract.
- Create `OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/SnmpMetricGroupList.vue`
  - Left-side group navigation and action state controls.
- Create `OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/SnmpMetricGroupEditor.vue`
  - Main group editor for fields, roles, units, data shape, and panel specs.
- Create `OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/SnmpDashboardImpactPreview.vue`
  - Right-side strategy set and dashboard family impact preview.
- Create `OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/SnmpAdvancedSettings.vue`
  - Collapsed low-frequency SNMP parameters using existing schema/model values.
- Modify `OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/PluginFormSnmp.vue`
  - Replace the generic parameter-only form with the SNMP workspace.
- Modify `OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/PluginFormByType.vue`
  - Pass optional strategy context through to plugin forms.
- Modify `OneOps-UI/src/views/platform/StrategyTemplate/StrategyFormModal.vue`
  - Pass root strategy context to `PluginFormByType`.
- Modify `OneOps-UI/src/views/platform/StrategyTemplate/SubStrategyFormModal.vue`
  - Pass child strategy context, including parent strategy and device profile, to `PluginFormByType`.
- Modify `OneOps-UI/src/views/platform/StrategyTemplate/StrategySetFormModal.vue`
  - Pass empty strategy context to keep template-bundle parameter editing compatible.
- Create `OneOps-UI/scripts/snmp-metric-contract-smoke.ts`
  - Smoke tests pure contract behavior without a browser.
- Create `OneOps-UI/scripts/snmp-profile-resolution-smoke.ts`
  - Smoke tests vendor/platform/model profile resolution and default group generation.
- Modify `OneOps-UI/package.json`
  - Add two smoke scripts.

### Task 1: Contract Types

**Files:**
- Create: `OneOps-UI/src/typings/platform/snmp-metric-contract.ts`

- [x] **Step 1: Create SNMP contract type definitions**

Use this complete file:

```ts
export type SnmpMetricGroupAction = 'inherit' | 'add' | 'override' | 'disable';
export type SnmpMetricFieldRole = 'dimension' | 'metric';
export type SnmpMetricValueType = 'string' | 'number' | 'boolean' | 'enum';
export type SnmpMetricCalculation = 'raw' | 'delta' | 'rate' | 'enum_map';
export type SnmpMetricDataShape = 'single' | 'timeseries' | 'table' | 'category' | 'topn' | 'table_timeseries';
export type SnmpPanelVisualType = 'stat' | 'gauge' | 'timeseries' | 'table' | 'pie' | 'bar' | 'topn';

export interface SnmpMetricSourceRef {
  manufacturer_id?: string;
  manufacturer_name?: string;
  platform_id?: string;
  platform_name?: string;
  device_model_ids?: string[];
  device_model_name?: string;
  mib_profile_key?: string;
  base_oid?: string;
}

export interface SnmpMetricFieldContract {
  metric_key: string;
  name: string;
  role: SnmpMetricFieldRole;
  oid?: string;
  unit?: string;
  value_type?: SnmpMetricValueType;
  calculation?: SnmpMetricCalculation;
  visual_hint?: SnmpPanelVisualType;
  enabled?: boolean;
}

export interface SnmpPanelSpecContract {
  panel_key: string;
  title: string;
  visual_type: SnmpPanelVisualType;
  metrics: string[];
  dimensions?: string[];
  unit?: string;
  layout_hint?: 'wide' | 'normal' | 'compact';
  enabled?: boolean;
}

export interface SnmpMetricGroupContract {
  group_key: string;
  name: string;
  entity: 'device' | 'interface' | 'sensor' | 'module' | 'custom';
  action: SnmpMetricGroupAction;
  data_shape: SnmpMetricDataShape;
  source?: SnmpMetricSourceRef;
  fields: SnmpMetricFieldContract[];
  panel_specs: SnmpPanelSpecContract[];
  enabled?: boolean;
}

export interface SnmpMetricContractEnvelope {
  version: 1;
  metric_groups: SnmpMetricGroupContract[];
}

export interface SnmpStrategyContext {
  strategy_id?: string;
  parent_strategy_id?: string;
  parent_parameters?: Record<string, unknown>;
  manufacturer_id?: string;
  manufacturer_name?: string;
  platform_id?: string;
  platform_name?: string;
  device_model_ids?: string[];
  device_model_name?: string;
  catalog_id?: string;
  catalog_name?: string;
  version_min?: string;
  version_max?: string;
}

export interface SnmpMibProfileGroupSeed {
  group_key: string;
  name: string;
  entity: SnmpMetricGroupContract['entity'];
  data_shape: SnmpMetricDataShape;
  base_oid?: string;
  fields: SnmpMetricFieldContract[];
  panel_specs: SnmpPanelSpecContract[];
}

export interface SnmpMibProfile {
  key: string;
  name: string;
  manufacturer_names: string[];
  platform_names: string[];
  model_keywords?: string[];
  groups: SnmpMibProfileGroupSeed[];
}

export interface SnmpDashboardImpactItem {
  strategy_set_id: string;
  strategy_set_name: string;
  root_dashboard_code?: string;
  root_dashboard_name?: string;
}
```

- [x] **Step 2: Run typecheck for the new standalone type file**

Run: `cd /OneOPS/OneOps-UI && npm run typecheck`

Expected: Existing project typecheck runs. If unrelated existing type errors appear, record them and continue after confirming the new file has no syntax errors.

### Task 2: Contract Helpers

**Files:**
- Create: `OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricContract.ts`
- Test: `OneOps-UI/scripts/snmp-metric-contract-smoke.ts`
- Modify: `OneOps-UI/package.json`

- [x] **Step 1: Add pure contract helpers**

Create `snmpMetricContract.ts`:

```ts
import type {
  SnmpMetricContractEnvelope,
  SnmpMetricFieldContract,
  SnmpMetricGroupContract,
  SnmpPanelSpecContract,
} from '@/typings/platform/snmp-metric-contract';

export const SNMP_METRIC_GROUPS_PARAM = 'metric_groups';

export function emptySnmpContract(): SnmpMetricContractEnvelope {
  return { version: 1, metric_groups: [] };
}

export function readSnmpContract(model: Record<string, unknown>): SnmpMetricContractEnvelope {
  const raw = model[SNMP_METRIC_GROUPS_PARAM];
  if (!raw || typeof raw !== 'object') return emptySnmpContract();
  const candidate = raw as Partial<SnmpMetricContractEnvelope>;
  return {
    version: 1,
    metric_groups: Array.isArray(candidate.metric_groups) ? candidate.metric_groups.map(normalizeMetricGroup) : [],
  };
}

export function writeSnmpContract(
  model: Record<string, unknown>,
  contract: SnmpMetricContractEnvelope,
): Record<string, unknown> {
  return {
    ...model,
    [SNMP_METRIC_GROUPS_PARAM]: {
      version: 1,
      metric_groups: contract.metric_groups.map(normalizeMetricGroup),
    },
  };
}

export function normalizeMetricGroup(group: SnmpMetricGroupContract): SnmpMetricGroupContract {
  return {
    ...group,
    action: group.action || 'inherit',
    enabled: group.enabled !== false,
    fields: Array.isArray(group.fields) ? group.fields.map(normalizeMetricField) : [],
    panel_specs: Array.isArray(group.panel_specs) ? group.panel_specs.map(normalizePanelSpec) : [],
  };
}

export function normalizeMetricField(field: SnmpMetricFieldContract): SnmpMetricFieldContract {
  return {
    ...field,
    metric_key: String(field.metric_key || '').trim(),
    name: String(field.name || field.metric_key || '').trim(),
    role: field.role === 'dimension' ? 'dimension' : 'metric',
    enabled: field.enabled !== false,
    value_type: field.value_type || (field.role === 'dimension' ? 'string' : 'number'),
    calculation: field.calculation || 'raw',
  };
}

export function normalizePanelSpec(panel: SnmpPanelSpecContract): SnmpPanelSpecContract {
  return {
    ...panel,
    panel_key: String(panel.panel_key || '').trim(),
    title: String(panel.title || panel.panel_key || '').trim(),
    visual_type: panel.visual_type || 'timeseries',
    metrics: Array.isArray(panel.metrics) ? panel.metrics.map(v => String(v).trim()).filter(Boolean) : [],
    dimensions: Array.isArray(panel.dimensions) ? panel.dimensions.map(v => String(v).trim()).filter(Boolean) : [],
    enabled: panel.enabled !== false,
  };
}

export function validateSnmpContract(contract: SnmpMetricContractEnvelope): string[] {
  const errors: string[] = [];
  const groupKeys = new Set<string>();
  contract.metric_groups.forEach(group => {
    if (!group.group_key) errors.push('指标分组缺少 group_key');
    if (groupKeys.has(group.group_key)) errors.push(`指标分组 key 重复: ${group.group_key}`);
    groupKeys.add(group.group_key);

    const metricKeys = new Set<string>();
    group.fields.forEach(field => {
      if (!field.metric_key) errors.push(`指标分组 ${group.group_key} 存在空 metric_key`);
      if (metricKeys.has(field.metric_key)) errors.push(`指标分组 ${group.group_key} 指标 key 重复: ${field.metric_key}`);
      metricKeys.add(field.metric_key);
    });

    const panelKeys = new Set<string>();
    group.panel_specs.forEach(panel => {
      if (!panel.panel_key) errors.push(`指标分组 ${group.group_key} 存在空 panel_key`);
      if (panelKeys.has(panel.panel_key)) errors.push(`指标分组 ${group.group_key} 面板 key 重复: ${panel.panel_key}`);
      panelKeys.add(panel.panel_key);
      panel.metrics.forEach(metric => {
        if (!metricKeys.has(metric)) errors.push(`面板 ${panel.panel_key} 引用了不存在的指标: ${metric}`);
      });
    });
  });
  return errors;
}

export function upsertMetricGroup(
  contract: SnmpMetricContractEnvelope,
  group: SnmpMetricGroupContract,
): SnmpMetricContractEnvelope {
  const normalized = normalizeMetricGroup(group);
  const next = contract.metric_groups.filter(item => item.group_key !== normalized.group_key);
  next.push(normalized);
  return { version: 1, metric_groups: next };
}

export function removeMetricGroup(contract: SnmpMetricContractEnvelope, groupKey: string): SnmpMetricContractEnvelope {
  return { version: 1, metric_groups: contract.metric_groups.filter(item => item.group_key !== groupKey) };
}

export function describeGroupAction(action: SnmpMetricGroupContract['action']): string {
  if (action === 'add') return '新增';
  if (action === 'override') return '覆盖';
  if (action === 'disable') return '禁用';
  return '继承';
}
```

- [x] **Step 2: Add smoke test for helpers**

Create `OneOps-UI/scripts/snmp-metric-contract-smoke.ts`:

```ts
import assert from 'node:assert/strict';
import {
  emptySnmpContract,
  readSnmpContract,
  upsertMetricGroup,
  validateSnmpContract,
  writeSnmpContract,
} from '../src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricContract';

const base = emptySnmpContract();
const withGroup = upsertMetricGroup(base, {
  group_key: 'interface_basic',
  name: '接口基础指标',
  entity: 'interface',
  action: 'add',
  data_shape: 'table_timeseries',
  fields: [
    { metric_key: 'if_name', name: '接口名称', role: 'dimension' },
    { metric_key: 'if_in_rate', name: '入方向流量', role: 'metric', unit: 'bps', calculation: 'rate' },
  ],
  panel_specs: [
    {
      panel_key: 'interface_basic.traffic',
      title: '接口流量',
      visual_type: 'timeseries',
      metrics: ['if_in_rate'],
      dimensions: ['if_name'],
      unit: 'bps',
    },
  ],
});

assert.equal(withGroup.metric_groups.length, 1);
assert.deepEqual(validateSnmpContract(withGroup), []);

const model = writeSnmpContract({ interval: '60s' }, withGroup);
const restored = readSnmpContract(model);

assert.equal(restored.metric_groups[0].group_key, 'interface_basic');
assert.equal(restored.metric_groups[0].fields[0].value_type, 'string');
assert.equal(restored.metric_groups[0].fields[1].calculation, 'rate');

const invalid = upsertMetricGroup(base, {
  group_key: 'broken',
  name: '坏分组',
  entity: 'custom',
  action: 'add',
  data_shape: 'timeseries',
  fields: [{ metric_key: 'only_dimension', name: '维度', role: 'dimension' }],
  panel_specs: [{ panel_key: 'broken.panel', title: '坏面板', visual_type: 'timeseries', metrics: ['missing'] }],
});

assert.match(validateSnmpContract(invalid).join('\n'), /引用了不存在的指标/);
console.log('snmp metric contract smoke passed');
```

- [x] **Step 3: Add smoke script command**

Add this script to `OneOps-UI/package.json` under `scripts`:

```json
"smoke:snmp-metric-contract": "npx esbuild scripts/snmp-metric-contract-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/snmp-metric-contract-smoke.mjs >/dev/null && node .tmp/snmp-metric-contract-smoke.mjs"
```

- [x] **Step 4: Run smoke test**

Run: `cd /OneOPS/OneOps-UI && npm run smoke:snmp-metric-contract`

Expected: `snmp metric contract smoke passed`

### Task 3: MIB Profile Registry

**Files:**
- Create: `OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMibProfiles.ts`
- Test: `OneOps-UI/scripts/snmp-profile-resolution-smoke.ts`
- Modify: `OneOps-UI/package.json`

- [x] **Step 1: Add frontend MIB profile seeds**

Create `snmpMibProfiles.ts`:

```ts
import type {
  SnmpMibProfile,
  SnmpMibProfileGroupSeed,
  SnmpStrategyContext,
} from '@/typings/platform/snmp-metric-contract';

const interfaceBasicGroup: SnmpMibProfileGroupSeed = {
  group_key: 'interface_basic',
  name: '接口基础指标',
  entity: 'interface',
  data_shape: 'table_timeseries',
  base_oid: '.1.3.6.1.2.1.2.2.1',
  fields: [
    { metric_key: 'if_name', name: '接口名称', role: 'dimension', value_type: 'string' },
    { metric_key: 'if_in_rate', name: '入方向流量', role: 'metric', unit: 'bps', calculation: 'rate', visual_hint: 'timeseries' },
    { metric_key: 'if_out_rate', name: '出方向流量', role: 'metric', unit: 'bps', calculation: 'rate', visual_hint: 'timeseries' },
    { metric_key: 'if_oper_status', name: '运行状态', role: 'metric', value_type: 'enum', calculation: 'enum_map', visual_hint: 'table' },
  ],
  panel_specs: [
    { panel_key: 'interface_basic.traffic', title: '接口流量', visual_type: 'timeseries', metrics: ['if_in_rate', 'if_out_rate'], dimensions: ['if_name'], unit: 'bps', layout_hint: 'wide' },
    { panel_key: 'interface_basic.status', title: '接口状态', visual_type: 'table', metrics: ['if_oper_status'], dimensions: ['if_name'], layout_hint: 'normal' },
  ],
};

const systemHealthGroup: SnmpMibProfileGroupSeed = {
  group_key: 'system_health',
  name: '系统健康',
  entity: 'device',
  data_shape: 'timeseries',
  fields: [
    { metric_key: 'cpu_usage', name: 'CPU 利用率', role: 'metric', unit: '%', value_type: 'number', visual_hint: 'timeseries' },
    { metric_key: 'memory_usage', name: '内存利用率', role: 'metric', unit: '%', value_type: 'number', visual_hint: 'timeseries' },
    { metric_key: 'temperature', name: '温度', role: 'metric', unit: 'celsius', value_type: 'number', visual_hint: 'timeseries' },
  ],
  panel_specs: [
    { panel_key: 'system_health.utilization', title: 'CPU / 内存', visual_type: 'timeseries', metrics: ['cpu_usage', 'memory_usage'], unit: '%' },
    { panel_key: 'system_health.temperature', title: '温度', visual_type: 'timeseries', metrics: ['temperature'], unit: 'celsius' },
  ],
};

export const SNMP_MIB_PROFILES: SnmpMibProfile[] = [
  {
    key: 'h3c_comware',
    name: 'H3C / Comware 指标库',
    manufacturer_names: ['h3c', '新华三'],
    platform_names: ['comware'],
    groups: [interfaceBasicGroup, systemHealthGroup],
  },
  {
    key: 'huawei_vrp',
    name: 'Huawei / VRP 指标库',
    manufacturer_names: ['huawei', '华为'],
    platform_names: ['vrp'],
    groups: [interfaceBasicGroup, systemHealthGroup],
  },
  {
    key: 'cisco_ios',
    name: 'Cisco / IOS 指标库',
    manufacturer_names: ['cisco', '思科'],
    platform_names: ['ios'],
    groups: [interfaceBasicGroup, systemHealthGroup],
  },
  {
    key: 'generic_snmp',
    name: '通用 SNMP 指标库',
    manufacturer_names: [],
    platform_names: [],
    groups: [interfaceBasicGroup],
  },
];

function normalizeText(value?: string): string {
  return String(value || '').trim().toLowerCase();
}

function matchesAny(value: string, choices: string[]): boolean {
  if (!value || choices.length === 0) return false;
  return choices.map(normalizeText).includes(value);
}

export function resolveSnmpMibProfile(context: SnmpStrategyContext): SnmpMibProfile {
  const manufacturer = normalizeText(context.manufacturer_name || context.manufacturer_id);
  const platform = normalizeText(context.platform_name || context.platform_id);
  const model = normalizeText(context.device_model_name);

  const matched = SNMP_MIB_PROFILES.find(profile => {
    const manufacturerMatched = matchesAny(manufacturer, profile.manufacturer_names);
    const platformMatched = matchesAny(platform, profile.platform_names);
    const modelMatched =
      !profile.model_keywords?.length || profile.model_keywords.some(keyword => model.includes(normalizeText(keyword)));
    return manufacturerMatched && platformMatched && modelMatched;
  });

  return matched || SNMP_MIB_PROFILES[SNMP_MIB_PROFILES.length - 1];
}
```

- [x] **Step 2: Add profile smoke test**

Create `OneOps-UI/scripts/snmp-profile-resolution-smoke.ts`:

```ts
import assert from 'node:assert/strict';
import { resolveSnmpMibProfile } from '../src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMibProfiles';

assert.equal(resolveSnmpMibProfile({ manufacturer_name: 'H3C', platform_name: 'Comware' }).key, 'h3c_comware');
assert.equal(resolveSnmpMibProfile({ manufacturer_name: '华为', platform_name: 'VRP' }).key, 'huawei_vrp');
assert.equal(resolveSnmpMibProfile({ manufacturer_name: 'Cisco', platform_name: 'IOS' }).key, 'cisco_ios');
assert.equal(resolveSnmpMibProfile({ manufacturer_name: 'Unknown', platform_name: 'Unknown' }).key, 'generic_snmp');
console.log('snmp profile resolution smoke passed');
```

- [x] **Step 3: Add smoke script command**

Add this script to `OneOps-UI/package.json`:

```json
"smoke:snmp-profile-resolution": "npx esbuild scripts/snmp-profile-resolution-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/snmp-profile-resolution-smoke.mjs >/dev/null && node .tmp/snmp-profile-resolution-smoke.mjs"
```

- [x] **Step 4: Run profile smoke test**

Run: `cd /OneOPS/OneOps-UI && npm run smoke:snmp-profile-resolution`

Expected: `snmp profile resolution smoke passed`

### Task 4: Strategy Context Plumbing

**Files:**
- Modify: `OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/PluginFormByType.vue`
- Modify: `OneOps-UI/src/views/platform/StrategyTemplate/StrategyFormModal.vue`
- Modify: `OneOps-UI/src/views/platform/StrategyTemplate/SubStrategyFormModal.vue`
- Modify: `OneOps-UI/src/views/platform/StrategyTemplate/StrategySetFormModal.vue`

- [x] **Step 1: Add `strategyContext` prop to `PluginFormByType.vue`**

Add import:

```ts
import type { SnmpStrategyContext } from '@/typings/platform/snmp-metric-contract';
```

Extend props:

```ts
strategyContext?: SnmpStrategyContext;
```

Add to `bindProps` plugin branch:

```ts
strategyContext: props.strategyContext,
```

- [x] **Step 2: Pass root strategy context from `StrategyFormModal.vue`**

Import:

```ts
import type { SnmpStrategyContext } from '@/typings/platform/snmp-metric-contract';
```

Add computed:

```ts
const snmpStrategyContext = computed<SnmpStrategyContext>(() => ({
  strategy_id: form.id,
  parent_parameters: undefined,
}));
```

Pass to `PluginFormByType`:

```vue
:strategy-context="snmpStrategyContext"
```

- [x] **Step 3: Pass child strategy context from `SubStrategyFormModal.vue`**

Import:

```ts
import type { SnmpStrategyContext } from '@/typings/platform/snmp-metric-contract';
```

Add helper:

```ts
function optionLabelByValue(options: SelectOption[], value?: string): string | undefined {
  return options.find(item => item.value === value)?.label;
}
```

Add computed:

```ts
const snmpStrategyContext = computed<SnmpStrategyContext>(() => ({
  strategy_id: form.id,
  parent_strategy_id: props.parentRecord?.id,
  parent_parameters: props.parentRecord?.parameters,
  manufacturer_id: form.manufacturer_id,
  manufacturer_name: optionLabelByValue(manufacturerOptions.value, form.manufacturer_id),
  platform_id: form.platform_id,
  platform_name: optionLabelByValue(platformOptions.value, form.platform_id),
  device_model_ids: form.device_model_ids,
  device_model_name: form.device_model_ids
    .map(id => optionLabelByValue(deviceModelOptions.value, id))
    .filter(Boolean)
    .join(', '),
  catalog_id: props.parentRecord?.catalog_id,
  catalog_name: props.parentRecord?.catalog_name,
  version_min: form.version_min,
  version_max: form.version_max,
}));
```

Pass to `PluginFormByType`:

```vue
:strategy-context="snmpStrategyContext"
```

- [x] **Step 4: Keep strategy set template parameter editing compatible**

In `StrategySetFormModal.vue`, pass an empty context:

```vue
:strategy-context="{}"
```

- [x] **Step 5: Run frontend typecheck**

Run: `cd /OneOPS/OneOps-UI && npm run typecheck`

Expected: Typecheck reaches project checking. Fix any context prop typing errors introduced by this task.

### Task 5: SNMP Group List Component

**Files:**
- Create: `OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/SnmpMetricGroupList.vue`

- [x] **Step 1: Create group list component**

Use this file:

```vue
<template>
  <div class="snmp-group-list">
    <div class="snmp-group-list__title">指标分组</div>
    <a-space direction="vertical" class="snmp-group-list__items" :size="8">
      <a-button
        v-for="group in groups"
        :key="group.group_key"
        class="snmp-group-list__item"
        :type="group.group_key === activeKey ? 'primary' : 'default'"
        block
        @click="emit('select', group.group_key)"
      >
        <span>{{ group.name }}</span>
        <a-tag :color="actionColor(group.action)">{{ describeGroupAction(group.action) }}</a-tag>
      </a-button>
    </a-space>
    <a-button block type="dashed" class="snmp-group-list__add" @click="emit('add-custom')">新增自定义分组</a-button>
  </div>
</template>

<script lang="ts" setup>
import type { SnmpMetricGroupContract } from '@/typings/platform/snmp-metric-contract';
import { describeGroupAction } from './snmpMetricContract';

defineProps<{
  groups: SnmpMetricGroupContract[];
  activeKey?: string;
}>();

const emit = defineEmits<{
  (e: 'select', groupKey: string): void;
  (e: 'add-custom'): void;
}>();

function actionColor(action: SnmpMetricGroupContract['action']) {
  if (action === 'add') return 'blue';
  if (action === 'override') return 'orange';
  if (action === 'disable') return 'red';
  return 'green';
}
</script>

<style lang="less" scoped>
.snmp-group-list {
  &__title {
    margin-bottom: 8px;
    color: #475569;
    font-size: 12px;
    font-weight: 600;
  }

  &__items {
    width: 100%;
  }

  &__item {
    display: flex;
    height: auto;
    min-height: 34px;
    align-items: center;
    justify-content: space-between;
    text-align: left;
    white-space: normal;
  }

  &__add {
    margin-top: 10px;
  }
}
</style>
```

- [x] **Step 2: Run typecheck**

Run: `cd /OneOPS/OneOps-UI && npm run typecheck`

Expected: No errors from `SnmpMetricGroupList.vue`.

### Task 6: SNMP Metric Group Editor

**Files:**
- Create: `OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/SnmpMetricGroupEditor.vue`

- [x] **Step 1: Create group editor component**

Create a component that edits one group and emits a full replacement group. Use Ant Design Vue table rows for fields and panel specs.

Key template shape:

```vue
<template>
  <div v-if="group" class="snmp-group-editor">
    <div class="snmp-group-editor__header">
      <div>
        <div class="snmp-group-editor__eyebrow">当前指标分组</div>
        <h3>{{ draft.name }}</h3>
        <div class="snmp-group-editor__key">分组标识：{{ draft.group_key }}</div>
      </div>
      <a-select v-model:value="draft.action" style="width: 110px" @change="commit">
        <a-select-option value="inherit">继承</a-select-option>
        <a-select-option value="add">新增</a-select-option>
        <a-select-option value="override">覆盖</a-select-option>
        <a-select-option value="disable">禁用</a-select-option>
      </a-select>
    </div>

    <a-divider />

    <a-table :columns="fieldColumns" :data-source="draft.fields" :pagination="false" size="small" row-key="metric_key">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'enabled'">
          <a-checkbox v-model:checked="record.enabled" @change="commit" />
        </template>
        <template v-else-if="column.key === 'role'">
          <a-select v-model:value="record.role" size="small" style="width: 88px" @change="commit">
            <a-select-option value="dimension">维度</a-select-option>
            <a-select-option value="metric">指标</a-select-option>
          </a-select>
        </template>
        <template v-else-if="column.key === 'unit'">
          <a-input v-model:value="record.unit" size="small" @change="commit" />
        </template>
      </template>
    </a-table>

    <a-divider />

    <div class="snmp-group-editor__subhead">面板契约</div>
    <a-list :data-source="draft.panel_specs" size="small">
      <template #renderItem="{ item }">
        <a-list-item>
          <a-list-item-meta :title="item.title" :description="`${item.panel_key} · ${item.visual_type}`" />
          <a-tag>{{ item.metrics.join(', ') }}</a-tag>
        </a-list-item>
      </template>
    </a-list>
  </div>
  <a-empty v-else description="请选择指标分组" />
</template>
```

Key script:

```ts
import { reactive, watch } from 'vue';
import type { SnmpMetricGroupContract } from '@/typings/platform/snmp-metric-contract';
import { normalizeMetricGroup } from './snmpMetricContract';

const props = defineProps<{ group?: SnmpMetricGroupContract }>();
const emit = defineEmits<{ (e: 'update:group', value: SnmpMetricGroupContract): void }>();

const draft = reactive<SnmpMetricGroupContract>({
  group_key: '',
  name: '',
  entity: 'custom',
  action: 'inherit',
  data_shape: 'timeseries',
  fields: [],
  panel_specs: [],
});

watch(
  () => props.group,
  value => {
    Object.assign(draft, value ? normalizeMetricGroup(value) : normalizeMetricGroup({
      group_key: '',
      name: '',
      entity: 'custom',
      action: 'inherit',
      data_shape: 'timeseries',
      fields: [],
      panel_specs: [],
    }));
  },
  { immediate: true, deep: true },
);

const fieldColumns = [
  { title: '', key: 'enabled', width: 46 },
  { title: '字段', dataIndex: 'name', key: 'name' },
  { title: '指标标识', dataIndex: 'metric_key', key: 'metric_key' },
  { title: '角色', key: 'role', width: 100 },
  { title: '单位', key: 'unit', width: 120 },
];

function commit() {
  emit('update:group', normalizeMetricGroup(draft));
}
```

- [x] **Step 2: Add scoped styles**

Use:

```less
.snmp-group-editor {
  &__header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
  }

  &__eyebrow,
  &__subhead {
    color: #475569;
    font-size: 12px;
    font-weight: 600;
  }

  h3 {
    margin: 2px 0 4px;
  }

  &__key {
    color: #64748b;
    font-size: 12px;
  }
}
```

- [x] **Step 3: Run typecheck**

Run: `cd /OneOPS/OneOps-UI && npm run typecheck`

Expected: No errors from `SnmpMetricGroupEditor.vue`.

### Task 7: Dashboard Impact Preview

**Files:**
- Create: `OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/SnmpDashboardImpactPreview.vue`

- [x] **Step 1: Create impact preview component**

Use this component:

```vue
<template>
  <div class="snmp-impact">
    <div class="snmp-impact__title">策略集影响</div>
    <a-alert
      v-if="!strategyId"
      type="info"
      show-icon
      message="保存策略后可查看策略集与仪表盘族影响。"
      class="snmp-impact__alert"
    />
    <template v-else>
      <a-spin :spinning="loading">
        <a-empty v-if="!items.length" description="暂无引用该策略的策略集" />
        <a-list v-else :data-source="items" size="small">
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta
                :title="item.strategy_set_name"
                :description="item.root_dashboard_name || item.root_dashboard_code || '未绑定根仪表盘'"
              />
            </a-list-item>
          </template>
        </a-list>
      </a-spin>
      <a-divider />
      <div class="snmp-impact__title">分组到面板</div>
      <a-list :data-source="groups" size="small">
        <template #renderItem="{ item }">
          <a-list-item>
            <a-list-item-meta :title="item.name" :description="item.panel_specs.map(panel => panel.title).join(' / ')" />
            <a-tag>{{ item.panel_specs.length }} 个面板</a-tag>
          </a-list-item>
        </template>
      </a-list>
    </template>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue';
import { listTeleabsStrategySets } from '@/api/platform/teleabs';
import type { TeleabsStrategySetDto } from '@/typings/platform/teleabs';
import type { SnmpDashboardImpactItem, SnmpMetricGroupContract } from '@/typings/platform/snmp-metric-contract';

const props = defineProps<{
  strategyId?: string;
  groups: SnmpMetricGroupContract[];
}>();

const loading = ref(false);
const items = ref<SnmpDashboardImpactItem[]>([]);

watch(
  () => props.strategyId,
  async strategyId => {
    if (!strategyId) {
      items.value = [];
      return;
    }
    loading.value = true;
    try {
      const sets = await listTeleabsStrategySets();
      const list = Array.isArray(sets) ? sets : [];
      items.value = list
        .filter((set: TeleabsStrategySetDto) => (set.items || []).some(item => item.strategy_id === strategyId))
        .map((set: TeleabsStrategySetDto) => ({
          strategy_set_id: set.id,
          strategy_set_name: set.name,
          root_dashboard_code: set.dashboard_codes?.[0],
          root_dashboard_name: set.dashboard_names?.[0],
        }));
    } finally {
      loading.value = false;
    }
  },
  { immediate: true },
);
</script>

<style lang="less" scoped>
.snmp-impact {
  &__title {
    margin-bottom: 8px;
    color: #475569;
    font-size: 12px;
    font-weight: 600;
  }

  &__alert {
    margin-bottom: 12px;
  }
}
</style>
```

- [x] **Step 2: Run typecheck**

Run: `cd /OneOPS/OneOps-UI && npm run typecheck`

Expected: No errors from impact preview.

### Task 8: Advanced SNMP Settings

**Files:**
- Create: `OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/SnmpAdvancedSettings.vue`

- [x] **Step 1: Create advanced settings wrapper**

The component should reuse `PluginFormBase` but filter only low-frequency SNMP parameter names.

Use:

```vue
<template>
  <a-collapse ghost>
    <a-collapse-panel key="advanced" header="高级设置">
      <PluginFormBase
        plugin-type="snmp"
        :param-schema="advancedSchema"
        :model="model"
        :compact="compact"
        :enable-grouping="false"
        @update:model="emit('update:model', $event)"
      />
    </a-collapse-panel>
  </a-collapse>
</template>

<script lang="ts" setup>
import { computed } from 'vue';
import type { TeleabsTemplateParam } from '@/typings/platform/teleabs';
import PluginFormBase from '../PluginFormBase.vue';

const ADVANCED_PARAM_NAMES = new Set([
  'version',
  'community',
  'timeout',
  'retries',
  'interval',
  'sec_name',
  'auth_protocol',
  'auth_password',
  'sec_level',
  'context_name',
  'priv_protocol',
  'priv_password',
]);

const props = defineProps<{
  paramSchema: TeleabsTemplateParam[];
  model: Record<string, unknown>;
  compact?: boolean;
}>();

const emit = defineEmits<{ (e: 'update:model', value: Record<string, unknown>): void }>();

const advancedSchema = computed(() => props.paramSchema.filter(param => ADVANCED_PARAM_NAMES.has(param.name)));
</script>
```

- [x] **Step 2: Run typecheck**

Run: `cd /OneOPS/OneOps-UI && npm run typecheck`

Expected: No errors from advanced settings.

### Task 9: SNMP Workspace Form

**Files:**
- Modify: `OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/PluginFormSnmp.vue`

- [x] **Step 1: Replace generic SNMP form with workspace layout**

Use this structure:

```vue
<template>
  <div class="snmp-form">
    <div class="snmp-form__left">
      <div class="snmp-form__section">
        <div class="snmp-form__label">策略上下文</div>
        <a-descriptions :column="1" size="small" bordered>
          <a-descriptions-item label="父策略">{{ strategyContext?.parent_strategy_id || '-' }}</a-descriptions-item>
          <a-descriptions-item label="厂商">{{ strategyContext?.manufacturer_name || strategyContext?.manufacturer_id || '-' }}</a-descriptions-item>
          <a-descriptions-item label="平台">{{ strategyContext?.platform_name || strategyContext?.platform_id || '-' }}</a-descriptions-item>
          <a-descriptions-item label="型号">{{ strategyContext?.device_model_name || '-' }}</a-descriptions-item>
        </a-descriptions>
      </div>
      <div class="snmp-form__section">
        <div class="snmp-form__label">指标库</div>
        <a-alert type="success" :message="profile.name" show-icon />
      </div>
      <SnmpMetricGroupList
        :groups="contract.metric_groups"
        :active-key="activeGroupKey"
        @select="activeGroupKey = $event"
        @add-custom="addCustomGroup"
      />
      <SnmpAdvancedSettings
        :param-schema="paramSchema"
        :model="model"
        :compact="compact"
        @update:model="emit('update:model', $event)"
      />
    </div>

    <div class="snmp-form__center">
      <SnmpMetricGroupEditor :group="activeGroup" @update:group="handleGroupUpdate" />
    </div>

    <div class="snmp-form__right">
      <SnmpDashboardImpactPreview :strategy-id="strategyContext?.strategy_id" :groups="contract.metric_groups" />
      <a-divider />
      <a-alert
        v-if="validationErrors.length"
        type="warning"
        show-icon
        :message="`存在 ${validationErrors.length} 个契约问题`"
        :description="validationErrors.join('；')"
      />
      <a-alert v-else type="success" show-icon message="指标分组契约有效" />
    </div>
  </div>
</template>
```

Use this script structure:

```ts
import { computed, ref, watch } from 'vue';
import type { TeleabsTemplateParam } from '@/typings/platform/teleabs';
import type { SnmpMetricGroupContract, SnmpStrategyContext } from '@/typings/platform/snmp-metric-contract';
import SnmpAdvancedSettings from './snmp/SnmpAdvancedSettings.vue';
import SnmpDashboardImpactPreview from './snmp/SnmpDashboardImpactPreview.vue';
import SnmpMetricGroupEditor from './snmp/SnmpMetricGroupEditor.vue';
import SnmpMetricGroupList from './snmp/SnmpMetricGroupList.vue';
import {
  readSnmpContract,
  upsertMetricGroup,
  validateSnmpContract,
  writeSnmpContract,
} from './snmp/snmpMetricContract';
import { resolveSnmpMibProfile } from './snmp/snmpMibProfiles';

const props = defineProps<{
  paramSchema: TeleabsTemplateParam[];
  model: Record<string, unknown>;
  compact?: boolean;
  enableGrouping?: boolean;
  strategyContext?: SnmpStrategyContext;
}>();

const emit = defineEmits<{ (e: 'update:model', value: Record<string, unknown>): void }>();

const activeGroupKey = ref('');
const profile = computed(() => resolveSnmpMibProfile(props.strategyContext || {}));
const contract = computed(() => readSnmpContract(props.model));
const validationErrors = computed(() => validateSnmpContract(contract.value));
const activeGroup = computed(() => contract.value.metric_groups.find(group => group.group_key === activeGroupKey.value));

watch(
  () => [profile.value.key, contract.value.metric_groups.length] as const,
  () => {
    if (contract.value.metric_groups.length === 0) {
      const seeded = profile.value.groups.reduce((current, group) => {
        return upsertMetricGroup(current, { ...group, action: 'inherit', source: { mib_profile_key: profile.value.key } });
      }, contract.value);
      emit('update:model', writeSnmpContract(props.model, seeded));
      activeGroupKey.value = seeded.metric_groups[0]?.group_key || '';
      return;
    }
    if (!activeGroupKey.value || !contract.value.metric_groups.some(group => group.group_key === activeGroupKey.value)) {
      activeGroupKey.value = contract.value.metric_groups[0]?.group_key || '';
    }
  },
  { immediate: true },
);

function handleGroupUpdate(group: SnmpMetricGroupContract) {
  emit('update:model', writeSnmpContract(props.model, upsertMetricGroup(contract.value, group)));
}

function addCustomGroup() {
  const index = contract.value.metric_groups.filter(group => group.group_key.startsWith('custom_')).length + 1;
  const group: SnmpMetricGroupContract = {
    group_key: `custom_${index}`,
    name: `自定义指标分组 ${index}`,
    entity: 'custom',
    action: 'add',
    data_shape: 'timeseries',
    fields: [],
    panel_specs: [],
  };
  activeGroupKey.value = group.group_key;
  emit('update:model', writeSnmpContract(props.model, upsertMetricGroup(contract.value, group)));
}
```

- [x] **Step 2: Add responsive scoped styles**

Use:

```less
.snmp-form {
  display: grid;
  grid-template-columns: 300px minmax(560px, 1fr) 300px;
  gap: 16px;

  &__left,
  &__center,
  &__right {
    min-width: 0;
  }

  &__section {
    margin-bottom: 16px;
  }

  &__label {
    margin-bottom: 8px;
    color: #475569;
    font-size: 12px;
    font-weight: 600;
  }
}

@media (max-width: 1280px) {
  .snmp-form {
    grid-template-columns: 280px minmax(520px, 1fr);

    &__right {
      grid-column: 1 / -1;
    }
  }
}
```

- [x] **Step 3: Run typecheck**

Run: `cd /OneOPS/OneOps-UI && npm run typecheck`

Expected: No errors from `PluginFormSnmp.vue` or new SNMP child components.

### Task 10: MIB Field Loading Hook

**Files:**
- Modify: `OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/SnmpMetricGroupEditor.vue`
- Modify: `OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/PluginFormSnmp.vue`

- [x] **Step 1: Pass active profile base OID to editor**

In `PluginFormSnmp.vue`, compute:

```ts
const activeSeedGroup = computed(() => profile.value.groups.find(group => group.group_key === activeGroupKey.value));
```

Pass:

```vue
:base-oid="activeSeedGroup?.base_oid"
```

- [x] **Step 2: Add MIB field loader to editor**

In `SnmpMetricGroupEditor.vue`, import:

```ts
import { listDeviceCollection2MIBFieldsReq } from '@/api/device/device-collection2';
import type { DeviceCollection2MIBField } from '@/api/device/device-collection2';
```

Add prop:

```ts
baseOid?: string;
```

Add state and function:

```ts
const mibLoading = ref(false);
const mibFields = ref<DeviceCollection2MIBField[]>([]);

async function loadMibFields() {
  if (!props.baseOid) return;
  mibLoading.value = true;
  try {
    mibFields.value = await listDeviceCollection2MIBFieldsReq({ base_oid: props.baseOid });
  } finally {
    mibLoading.value = false;
  }
}
```

Add button near the header:

```vue
<a-button :loading="mibLoading" :disabled="!baseOid" @click="loadMibFields">加载 MIB 字段</a-button>
```

Add below the existing table:

```vue
<a-alert
  v-if="mibFields.length"
  type="info"
  show-icon
  :message="`已加载 ${mibFields.length} 个 MIB 字段，可用于自定义分组补充。`"
/>
```

- [x] **Step 3: Run typecheck**

Run: `cd /OneOPS/OneOps-UI && npm run typecheck`

Expected: No errors from MIB API usage.

### Task 11: Final Verification

**Files:**
- Verify all files modified above.

- [x] **Step 1: Run smoke tests**

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

- [x] **Step 2: Run typecheck**

Run: `cd /OneOPS/OneOps-UI && npm run typecheck`

Expected: No new TypeScript errors from this feature. If existing unrelated project errors block completion, record exact errors and the files that caused them.

- [ ] **Step 3: Manual browser check**

Run: `cd /OneOPS/OneOps-UI && npm run dev -- --host 0.0.0.0 --port 3002`

Open the strategy template SNMP strategy form and verify:

- SNMP form shows three workspace areas.
- Vendor/profile alert resolves H3C/Comware, Huawei/VRP, Cisco/IOS, or generic SNMP.
- Metric group list shows inherit/add/override/disable tags.
- Selecting a group updates the editor.
- Changing a group action updates `parameters.metric_groups`.
- Custom group button creates `custom_1`.
- Dashboard impact panel shows saved-strategy message when no strategy id is available.
- Advanced settings are collapsed and do not dominate the page.

- [x] **Step 4: Commit implementation changes**

Because `/OneOPS` is a multi-repo workspace, commit only inside `OneOps-UI` when implementation changes are complete:

```bash
cd /OneOPS/OneOps-UI
git status --short
git add src/typings/platform/snmp-metric-contract.ts \
  src/views/platform/StrategyTemplate/plugin-forms/PluginFormByType.vue \
  src/views/platform/StrategyTemplate/plugin-forms/PluginFormSnmp.vue \
  src/views/platform/StrategyTemplate/plugin-forms/snmp \
  src/views/platform/StrategyTemplate/StrategyFormModal.vue \
  src/views/platform/StrategyTemplate/SubStrategyFormModal.vue \
  src/views/platform/StrategyTemplate/StrategySetFormModal.vue \
  scripts/snmp-metric-contract-smoke.ts \
  scripts/snmp-profile-resolution-smoke.ts \
  package.json
git commit -m "feat: add snmp metric group contract editor"
```

Expected: commit succeeds with only the files listed above.

## Self-Review

Spec coverage:

- SNMP-specific strategy form is covered by Tasks 5 through 9.
- Vendor/profile-driven MIB simplification is covered by Tasks 3 and 10.
- Metric group and panel spec contract persistence is covered by Tasks 1, 2, and 9.
- Parent/child strategy context is covered by Task 4.
- Strategy set and dashboard family impact preview is covered by Task 7.
- Grafana JSON generation remains out of scope; only panel specs and impact preview are created.

Placeholder scan:

- No task contains placeholder markers or unspecified implementation steps.

Type consistency:

- Contract type names use the `Snmp*` prefix consistently.
- Stored parameter key is `metric_groups`.
- Stable identities are `group_key`, `metric_key`, and `panel_key`.
