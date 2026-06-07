# Grouped Asset Selector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable platform grouped asset selector and wire it into configuration management collection task creation.

**Architecture:** Reuse the existing platform grouping APIs, schema view helpers, `GroupingConfigSidebar`, and `GroupingResultBody`. Add one focused selector state composable, one full-screen drawer component, and a small configuration-management adapter that turns grouped device selections into existing collection rows. The selector returns temporary selection results only; task envelope creation remains in configuration management.

**Tech Stack:** Vue 3 `<script setup>`, TypeScript, Ant Design Vue, existing OneOps platform grouping APIs, esbuild smoke tests.

---

## File Structure

- Create `OneOps-UI/src/views/platform/composables/groupedAssetSelectorTypes.ts`: shared selector result and option types.
- Create `OneOps-UI/src/views/platform/composables/useGroupedAssetSelectorState.ts`: entity type setup, schema loading, grouping execution, selection and exclusion state.
- Create `OneOps-UI/src/views/platform/components/GroupedAssetSelector.vue`: full-screen drawer with three-column workbench and confirm event.
- Modify `OneOps-UI/src/views/platform/components/GroupingConfigSidebar.vue`: allow selector mode copy, hide persistent grouping links, and render a single entity context when only one type is allowed.
- Modify `OneOps-UI/src/views/platform/components/GroupingResultBody.vue`: add optional selected-result keyword filter and per-row exclusion action column.
- Modify `OneOps-UI/src/views/device/config-management/collectionTaskHelpers.ts`: add a pure mapper from grouped device entities to `ConfigManagementAssetResp`.
- Modify `OneOps-UI/src/views/device/DeviceConfigManagement.vue`: add `按分组选择资产` action, selector drawer, grouped-source state, and reuse existing collection task creation.
- Create `OneOps-UI/scripts/grouped-asset-selector-state-smoke.ts`: validates result derivation with exclusions and type switching behavior.
- Modify `OneOps-UI/scripts/config-management-collection-task-helpers-smoke.ts`: validates grouped device entity mapping.
- Modify `OneOps-UI/package.json`: add `smoke:grouped-asset-selector` script.

## Task 1: Selector Types And State Smoke

**Files:**
- Create: `OneOps-UI/src/views/platform/composables/groupedAssetSelectorTypes.ts`
- Create: `OneOps-UI/scripts/grouped-asset-selector-state-smoke.ts`
- Modify: `OneOps-UI/package.json`

- [ ] **Step 1: Add selector shared types**

Create `OneOps-UI/src/views/platform/composables/groupedAssetSelectorTypes.ts`:

```ts
import type { EntityHierarchicalGroupingReq, EntityType } from '@/typings/platform/entity-grouping';

export type GroupedAssetSelectorEntityType = Extract<EntityType, 'device' | 'application' | 'nvr'>;

export interface GroupingFieldOption {
  source: 'attribute' | 'metadata' | 'label';
  key: string;
  label: string;
  description?: string;
  valueType?: 'string' | 'number' | 'boolean' | 'enum';
}

export interface GroupedAssetSelectionResult {
  entity_type: GroupedAssetSelectorEntityType;
  entity_ids: string[];
  raw_selected_entity_ids: string[];
  excluded_entity_ids: string[];
  entities: Record<string, unknown>[];
  grouping_payload: EntityHierarchicalGroupingReq;
  selected_group_keys: string[];
  total: number;
}

export function normalizeSelectorEntityTypes(
  values: GroupedAssetSelectorEntityType[] | undefined,
): GroupedAssetSelectorEntityType[] {
  const allowed = new Set<GroupedAssetSelectorEntityType>(['device', 'application', 'nvr']);
  const seen = new Set<GroupedAssetSelectorEntityType>();
  const out: GroupedAssetSelectorEntityType[] = [];
  for (const value of values?.length ? values : ['device']) {
    if (!allowed.has(value) || seen.has(value)) continue;
    seen.add(value);
    out.push(value);
  }
  return out.length ? out : ['device'];
}

export function buildGroupedAssetSelectionResult(params: {
  entityType: GroupedAssetSelectorEntityType;
  entities: Record<string, unknown>[];
  rawEntityIds: string[];
  excludedEntityIds: string[];
  groupingPayload: EntityHierarchicalGroupingReq;
  selectedGroupKeys: string[];
  entityKey: (entity: Record<string, unknown>) => string;
}): GroupedAssetSelectionResult {
  const excluded = new Set(params.excludedEntityIds.map(item => String(item || '').trim()).filter(Boolean));
  const finalEntities: Record<string, unknown>[] = [];
  const finalIDs: string[] = [];
  const seen = new Set<string>();

  for (const entity of params.entities) {
    const id = params.entityKey(entity);
    if (!id || excluded.has(id) || seen.has(id)) continue;
    seen.add(id);
    finalIDs.push(id);
    finalEntities.push(entity);
  }

  return {
    entity_type: params.entityType,
    entity_ids: finalIDs,
    raw_selected_entity_ids: Array.from(new Set(params.rawEntityIds.filter(Boolean))),
    excluded_entity_ids: Array.from(excluded),
    entities: finalEntities,
    grouping_payload: params.groupingPayload,
    selected_group_keys: [...params.selectedGroupKeys],
    total: finalIDs.length,
  };
}
```

- [ ] **Step 2: Add smoke test**

Create `OneOps-UI/scripts/grouped-asset-selector-state-smoke.ts`:

```ts
import assert from 'node:assert/strict';

import {
  buildGroupedAssetSelectionResult,
  normalizeSelectorEntityTypes,
} from '../src/views/platform/composables/groupedAssetSelectorTypes';

assert.deepEqual(normalizeSelectorEntityTypes(['device', 'device', 'nvr']), ['device', 'nvr']);
assert.deepEqual(normalizeSelectorEntityTypes([]), ['device']);
assert.deepEqual(normalizeSelectorEntityTypes(undefined), ['device']);

const result = buildGroupedAssetSelectionResult({
  entityType: 'device',
  entities: [
    { code: 'SW001', name: '核心交换机-01' },
    { code: 'SW002', name: '核心交换机-02' },
    { code: 'SW002', name: '重复资产' },
  ],
  rawEntityIds: ['SW001', 'SW002', 'SW002'],
  excludedEntityIds: ['SW002'],
  groupingPayload: {
    entity_type: 'device',
    device_source: 'device_v2',
    levels: [{ source: 'attribute', key: 'catalog_name' }],
  },
  selectedGroupKeys: ['group-switch'],
  entityKey: entity => String(entity.code || ''),
});

assert.equal(result.total, 1);
assert.deepEqual(result.entity_ids, ['SW001']);
assert.deepEqual(result.raw_selected_entity_ids, ['SW001', 'SW002']);
assert.deepEqual(result.excluded_entity_ids, ['SW002']);
assert.equal(result.entities[0].name, '核心交换机-01');
assert.equal(result.grouping_payload.levels[0].key, 'catalog_name');

console.log('grouped asset selector state smoke passed');
```

- [ ] **Step 3: Add npm script**

Modify `OneOps-UI/package.json` `scripts`:

```json
"smoke:grouped-asset-selector": "npx esbuild scripts/grouped-asset-selector-state-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/grouped-asset-selector-state-smoke.mjs >/dev/null && node .tmp/grouped-asset-selector-state-smoke.mjs"
```

- [ ] **Step 4: Run smoke test**

Run:

```bash
cd OneOps-UI && npm run smoke:grouped-asset-selector
```

Expected:

```text
grouped asset selector state smoke passed
```

## Task 2: Selector State Composable

**Files:**
- Create: `OneOps-UI/src/views/platform/composables/useGroupedAssetSelectorState.ts`
- Test: `OneOps-UI/scripts/grouped-asset-selector-state-smoke.ts`

- [ ] **Step 1: Create composable skeleton**

Create `OneOps-UI/src/views/platform/composables/useGroupedAssetSelectorState.ts` with imports, default level helpers, entity key, schema loading, and profile setup copied from the existing grouping page:

```ts
import { computed, onMounted, ref, watch } from 'vue';
import { message } from 'ant-design-vue';
import { getDeviceV2SchemaCurrentReq, type DeviceV2SchemaResp } from '@/api/device/device-v2';
import { getApplicationV2SchemaCurrentReq, type ApplicationV2SchemaResp } from '@/api/application/application-v2';
import { getEntityGroupingCapabilities, groupEntitiesHierarchical } from '@/api/platform/entity-grouping';
import type {
  EntityFilterClause,
  EntityGroupingCapabilitiesResp,
  EntityGroupingCapability,
  EntityHierarchicalGroupingReq,
  EntityHierarchicalGroupingResp,
  LevelSpec,
} from '@/typings/platform/entity-grouping';
import {
  buildGroupedAssetSelectionResult,
  normalizeSelectorEntityTypes,
  type GroupedAssetSelectionResult,
  type GroupedAssetSelectorEntityType,
} from '@/views/platform/composables/groupedAssetSelectorTypes';
import {
  buildTypedFilterClauses,
  createEntityGroupingProfiles,
  useEntityGroupingProfiles,
  type FilterField,
} from '@/views/platform/composables/useEntityGroupingProfiles';
import { useEntityGroupingSchemaViews } from '@/views/platform/composables/useEntityGroupingSchemaViews';
import { useHierarchicalGroupingSelection } from '@/views/platform/composables/useHierarchicalGroupingSelection';
import { defaultBusinessGroupingLevels } from '@/views/platform/composables/groupingFieldDisplay';

const DEVICE_SOURCE = 'device_v2' as const;
const DEFAULT_DIMENSION_SOURCES: NonNullable<EntityGroupingCapability['supported_dimension_sources']> = [
  'attribute',
  'label',
  'metadata',
];
const APPLICATION_BUILTIN_ATTRIBUTE_KEYS = new Set([
  'id',
  'name',
  'type',
  'address',
  'port',
  'device_id',
  'group_id',
  'group_name',
]);
```

- [ ] **Step 2: Implement exported `useGroupedAssetSelectorState`**

Add the exported composable:

```ts
export function useGroupedAssetSelectorState(params: {
  allowedEntityTypes?: GroupedAssetSelectorEntityType[];
  defaultEntityType?: GroupedAssetSelectorEntityType;
}) {
  const allowedEntityTypes = computed(() => normalizeSelectorEntityTypes(params.allowedEntityTypes));
  const initialType = allowedEntityTypes.value.includes(params.defaultEntityType || 'device')
    ? params.defaultEntityType || 'device'
    : allowedEntityTypes.value[0];

  const entityType = ref<GroupedAssetSelectorEntityType>(initialType);
  const groupingCapabilities = ref<EntityGroupingCapabilitiesResp | null>(null);
  const deviceSchema = ref<DeviceV2SchemaResp | null>(null);
  const applicationSchema = ref<ApplicationV2SchemaResp | null>(null);
  const hierarchicalLevelSpecs = ref<LevelSpec[]>([]);
  const hierarchicalLoading = ref(false);
  const hierarchicalResult = ref<EntityHierarchicalGroupingResp | null>(null);
  const hierarchicalCheckedKeys = ref<string[]>([]);
  const selectedTreeKeys = ref<string[]>([]);
  const treeExpandedKeys = ref<string[]>([]);
  const preGroupFilterOpen = ref<string[]>([]);
  const preGroupDeviceFilters = ref<Record<string, string>>({});
  const preGroupAppFilters = ref<Record<string, string>>({});
  const preGroupNvrFilters = ref<Record<string, string>>({
    name: '',
    code: '',
    tenant: '',
    function_area: '',
    status: '',
    protocol_type: '',
  });
  const excludedEntityIds = ref<string[]>([]);

  function entityKey(e: Record<string, unknown>): string {
    const key = (e.code || e.id || e.name || e.address) as string | undefined;
    return key || JSON.stringify(e);
  }

  return {
    entityType,
    allowedEntityTypes,
    groupingCapabilities,
    hierarchicalLevelSpecs,
    hierarchicalLoading,
    hierarchicalResult,
    hierarchicalCheckedKeys,
    selectedTreeKeys,
    treeExpandedKeys,
    preGroupFilterOpen,
    excludedEntityIds,
    entityKey,
  };
}
```

- [ ] **Step 3: Complete schema views, profiles, grouping execution, and result building**

Extend the composable with the same logic as `DeviceGroupManagement.vue` for:

```ts
const {
  nvrAttributeKeys,
  nvrFilterFields,
  nvrEntityColumns,
  deviceFilterFields,
  applicationFilterFields,
  deviceLabelKeySuggestions,
  applicationLabelKeySuggestions,
  deviceAttributeKeyOptions,
  applicationAttributeKeyOptions,
  deviceNewLevelSpec,
  applicationNewLevelSpec,
  nvrNewLevelSpec,
  deviceEntityColumns,
  applicationEntityColumns,
  devicePostFilterFields,
  applicationPostFilterFields,
} = useEntityGroupingSchemaViews({ deviceSchema, applicationSchema });
```

and return:

```ts
return {
  entityType,
  entityOptions,
  allowedEntityTypes,
  showEntityTypeSwitch,
  supportedDimensionSources,
  deviceSourceHint,
  hierarchicalLevelSpecs,
  hierarchicalLoading,
  hierarchicalResult,
  hierarchicalCheckedKeys,
  selectedTreeKeys,
  treeExpandedKeys,
  preGroupFilterOpen,
  entityLabel,
  entityUnit,
  currentPreGroupFilterFields,
  currentPreGroupFilters,
  labelKeySuggestions,
  attributeKeyOptions,
  entityColumns,
  allTreeKeys,
  hierarchicalTreeData,
  checkedNodeEntities,
  effectiveSelectedEntities,
  effectiveOperationCount,
  excludedEntityIds,
  entityKey,
  addHierarchicalLevel,
  removeHierarchicalLevel,
  performHierarchicalGrouping,
  removeSelectedEntity,
  clearSelection,
  buildSelectionResult,
  initialize,
};
```

`effectiveSelectedEntities` filters `checkedNodeEntities` through `excludedEntityIds`. `buildSelectionResult()` calls `buildGroupedAssetSelectionResult`. `performHierarchicalGrouping()` validates levels, calls `groupEntitiesHierarchical`, expands the result, and clears exclusions.

- [ ] **Step 4: Run typecheck and smoke**

Run:

```bash
cd OneOps-UI && npm run smoke:grouped-asset-selector && npm run typecheck
```

Expected: smoke passes; typecheck completes without errors caused by the new files.

## Task 3: Selector Component And Existing Grouping Components

**Files:**
- Create: `OneOps-UI/src/views/platform/components/GroupedAssetSelector.vue`
- Modify: `OneOps-UI/src/views/platform/components/GroupingConfigSidebar.vue`
- Modify: `OneOps-UI/src/views/platform/components/GroupingResultBody.vue`

- [ ] **Step 1: Add optional props to `GroupingConfigSidebar.vue`**

Add props:

```ts
title?: string;
subtitle?: string;
showFooterLinks?: boolean;
showEntityTypeSwitch?: boolean;
```

Render `title || '通用分组'`, `subtitle || '按层级对设备或应用分组，勾选节点后应用策略或保存为选择集。'`. Only render the object tabs when `showEntityTypeSwitch !== false`; otherwise show the current entity label in a disabled context block. Only render footer links when `showFooterLinks !== false`.

- [ ] **Step 2: Add exclusion support to `GroupingResultBody.vue`**

Add props:

```ts
selectedKeyword?: string;
showRemoveAction?: boolean;
```

Add emits:

```ts
(e: 'remove-entity', entity: Record<string, unknown>): void;
```

When `showRemoveAction` is true, append an action column:

```ts
{
  title: '操作',
  key: 'selectorAction',
  fixed: 'right',
  width: 80,
}
```

In `bodyCell`, render a small link button that emits `remove-entity`.

- [ ] **Step 3: Create `GroupedAssetSelector.vue`**

Create a full-screen drawer component with this public contract:

```ts
const props = withDefaults(
  defineProps<{
    open: boolean;
    allowedEntityTypes?: GroupedAssetSelectorEntityType[];
    defaultEntityType?: GroupedAssetSelectorEntityType;
    title?: string;
    confirmText?: string;
  }>(),
  {
    title: '按分组选择资产',
    confirmText: '确认选择',
  },
);

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void;
  (e: 'confirm', value: GroupedAssetSelectionResult): void;
}>();
```

Use `GroupingConfigSidebar` in the left column and `GroupingResultBody` in the middle/right work area. Add selected keyword search above the result detail, selected count in the footer, and disable confirm when total is zero.

- [ ] **Step 4: Run smoke and typecheck**

Run:

```bash
cd OneOps-UI && npm run smoke:grouped-asset-selector && npm run typecheck
```

Expected: no TypeScript errors in selector component or modified grouping components.

## Task 4: Configuration Management Mapper

**Files:**
- Modify: `OneOps-UI/src/views/device/config-management/collectionTaskHelpers.ts`
- Modify: `OneOps-UI/scripts/config-management-collection-task-helpers-smoke.ts`

- [ ] **Step 1: Add mapper function**

Add to `collectionTaskHelpers.ts`:

```ts
export const configCollectionRowsFromGroupedDeviceEntities = (
  entities: Record<string, unknown>[],
): ConfigManagementAssetResp[] =>
  entities
    .map(entity => {
      const code = String(entity.code || entity.device_code || entity.asset_code || entity.id || '').trim();
      if (!code) return null;
      const attributes = (entity.attributes || {}) as Record<string, unknown>;
      const metadata = (entity.metadata || {}) as Record<string, unknown>;
      const plane = String(
        entity.access_plane || entity.collection_plane || attributes.access_plane || metadata.access_plane || '',
      ).toLowerCase();
      return {
        asset_type: String(entity.asset_type || attributes.asset_type || metadata.asset_type || 'network_device'),
        asset_code: code,
        asset_name: String(entity.name || entity.device_name || entity.asset_name || ''),
        device_code: code,
        device_name: String(entity.name || entity.device_name || ''),
        management_ip: String(
          entity.management_ip || entity.ip || entity.address || attributes.management_ip || attributes.ip || '',
        ),
        vendor: String(entity.vendor || attributes.vendor || attributes.manufacturer_name || ''),
        model: String(entity.model || attributes.model || attributes.device_model_name || ''),
        access_plane: plane === 'out_band' ? 'out_band' : 'in_band',
        collection_plane: plane === 'out_band' ? 'out_band' : 'in_band',
        config_scope: 'network_running_config',
      } as ConfigManagementAssetResp;
    })
    .filter((row): row is ConfigManagementAssetResp => !!row);
```

- [ ] **Step 2: Extend smoke test**

Add assertions to `config-management-collection-task-helpers-smoke.ts`:

```ts
import { configCollectionRowsFromGroupedDeviceEntities } from '../src/views/device/config-management/collectionTaskHelpers';

const mappedRows = configCollectionRowsFromGroupedDeviceEntities([
  {
    code: 'SW001',
    name: '核心交换机-01',
    ip: '10.1.1.1',
    attributes: { manufacturer_name: 'H3C', device_model_name: 'S6520', access_plane: 'out_band' },
  },
  { code: '' },
]);

assert.equal(mappedRows.length, 1);
assert.equal(mappedRows[0].device_code, 'SW001');
assert.equal(mappedRows[0].asset_name, '核心交换机-01');
assert.equal(mappedRows[0].management_ip, '10.1.1.1');
assert.equal(mappedRows[0].vendor, 'H3C');
assert.equal(mappedRows[0].model, 'S6520');
assert.equal(mappedRows[0].access_plane, 'out_band');
```

- [ ] **Step 3: Run collection helper smoke**

Run:

```bash
cd OneOps-UI && npm run smoke:config-management-collection-task-helpers
```

Expected:

```text
config management collection task helpers smoke passed
```

## Task 5: Configuration Management Integration

**Files:**
- Modify: `OneOps-UI/src/views/device/DeviceConfigManagement.vue`

- [ ] **Step 1: Import selector and mapper**

Add imports:

```ts
import GroupedAssetSelector from '@/views/platform/components/GroupedAssetSelector.vue';
import type { GroupedAssetSelectionResult } from '@/views/platform/composables/groupedAssetSelectorTypes';
import {
  buildConfigCollectionTaskEnvelope,
  buildConfigScheduledTaskRequest,
  configCollectionAssetTypeLabel,
  configCollectionRowsFromGroupedDeviceEntities,
  groupConfigCollectionRows,
  resolveConfigCollectionTemplate,
} from './config-management/collectionTaskHelpers';
```

- [ ] **Step 2: Add grouped selection state**

Add state near `collectionDrawer`:

```ts
type CollectionTargetSource = 'selected' | 'filtered' | 'grouped';

const groupedAssetSelectorVisible = ref(false);
const groupedCollectionRows = ref<ConfigRow[]>([]);
const collectionTargetSource = ref<CollectionTargetSource>('selected');
```

- [ ] **Step 3: Update collection target computed values**

Replace `isCollectionDrawerUsingSelectedRows` and `collectionTargetRows` with:

```ts
const isCollectionDrawerUsingSelectedRows = computed(() => collectionTargetSource.value === 'selected');
const isCollectionDrawerUsingFilteredRows = computed(() => collectionTargetSource.value === 'filtered');
const isCollectionDrawerUsingGroupedRows = computed(() => collectionTargetSource.value === 'grouped');

const collectionTargetRows = computed(() => {
  if (isCollectionDrawerUsingGroupedRows.value) return groupedCollectionRows.value;
  if (isCollectionDrawerUsingSelectedRows.value) return selectedRows.value;
  return filteredRows.value;
});
```

Update labels so grouped selections show `分组选择资产`.

- [ ] **Step 4: Add selector action to task toolbar and drawer**

Add buttons:

```vue
<a-button @click="openGroupedAssetSelector">
  按分组选择资产
</a-button>
```

Add the selector component below the collection drawer:

```vue
<GroupedAssetSelector
  v-model:open="groupedAssetSelectorVisible"
  :allowed-entity-types="['device']"
  default-entity-type="device"
  title="选择配置采集资产"
  confirm-text="加入采集任务"
  @confirm="handleGroupedAssetSelectionConfirm"
/>
```

- [ ] **Step 5: Add handlers**

Add methods:

```ts
function openGroupedAssetSelector() {
  groupedAssetSelectorVisible.value = true;
}

function handleGroupedAssetSelectionConfirm(result: GroupedAssetSelectionResult) {
  if (result.entity_type !== 'device') {
    message.warning('配置采集当前仅支持设备资产');
    return;
  }
  const mappedRows = configCollectionRowsFromGroupedDeviceEntities(result.entities).map(configRowFromAsset);
  if (!mappedRows.length) {
    message.warning('分组选择结果中没有可采集设备');
    return;
  }
  groupedCollectionRows.value = mappedRows;
  collectionTargetSource.value = 'grouped';
  collectionDrawer.selectedOnly = false;
  collectionDrawer.confirmFilteredQueue = true;
  groupedAssetSelectorVisible.value = false;
  openCollectionTaskDrawer(collectionDrawer.mode || 'manual', false);
  message.success(`已从分组选择带入 ${mappedRows.length} 个资产`);
}
```

Update `openCollectionTaskDrawer(mode, selectedOnly)` so it sets `collectionTargetSource`:

```ts
collectionTargetSource.value = selectedOnly && selectedRows.value.length > 0 ? 'selected' : 'filtered';
```

Do not clear `groupedCollectionRows` unless the source changes away from grouped.

- [ ] **Step 6: Run typecheck and smoke tests**

Run:

```bash
cd OneOps-UI && npm run smoke:grouped-asset-selector && npm run smoke:config-management-collection-task-helpers && npm run typecheck
```

Expected: both smokes pass; typecheck passes or only reports pre-existing unrelated errors.

## Task 6: Manual UI Verification

**Files:**
- Verify: `OneOps-UI/src/views/platform/components/GroupedAssetSelector.vue`
- Verify: `OneOps-UI/src/views/device/DeviceConfigManagement.vue`

- [ ] **Step 1: Start dev server**

Run:

```bash
cd OneOps-UI && npm run dev -- --host 0.0.0.0
```

Expected: Vite reports a local URL.

- [ ] **Step 2: Exercise selector flow**

Open the configuration management page, switch to `采集任务`, click `按分组选择资产`, run a simple device grouping, select a group, confirm, and verify the collection drawer shows `分组选择资产` with a non-zero asset count.

- [ ] **Step 3: Check layout**

Verify the drawer uses the three-column workbench, the grouping level dropdown shows readable labels such as `设备类别名称` and `平台名称`, and selected asset removal updates the right-column count without forcing the tree state to change.

- [ ] **Step 4: Stop dev server**

Stop the Vite session with `Ctrl-C`.

## Self-Review

- Spec coverage: The plan implements temporary grouped selection, readable field labels, full-screen three-column layout, single entity type confirmation, exclusion semantics, and configuration management integration.
- Placeholder scan: No deferred implementation markers are present.
- Type consistency: The result type is `GroupedAssetSelectionResult`; configuration management handler consumes that type and maps only `device` selections into existing collection rows.
