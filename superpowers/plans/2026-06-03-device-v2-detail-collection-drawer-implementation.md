# Device V2 Detail And Collection Drawer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve Device V2 device details and the collection result drawer so collected structured data is grouped clearly, while preserving current batch collection triggers, task retention, refresh, diagnostics, and DC2 detail jumps.

**Architecture:** Add focused mapping helpers for detail sections and collection result sections, then wire those helpers into `DeviceV2ManagementGrouped.vue`. Keep existing API calls and task persistence logic intact; this plan reorganizes presentation first and avoids backend contract changes unless missing fields are discovered.

**Tech Stack:** Vue 3 `<script setup>`, TypeScript, Ant Design Vue, existing Device V2 API helpers, `npm run typecheck:d2`, esbuild-powered smoke scripts.

---

## File Structure

- Create: `OneOPS-UI/src/views/device/device-v2-management/detail-section-model.ts`
  - Builds display sections for Device V2 details.
  - Separates common, server-specific, network-specific, access, location, and latest collection sections.
  - Contains no Vue state and no API calls.

- Create: `OneOPS-UI/src/views/device/device-v2-management/collection-result-model.ts`
  - Converts `DeviceV2StoreObservationItem[]`, `DeviceV2StoreRunItem[]`, and `DeviceV2StoreCollectionPlanItem[]` into grouped drawer sections.
  - Keeps field-level rows and raw evidence available.
  - Contains no Vue state and no API calls.

- Create: `OneOPS-UI/scripts/device-v2-detail-collection-model-smoke.ts`
  - Provides deterministic sample server and network devices.
  - Verifies server-only fields, network-only fields, and observation grouping.

- Modify: `OneOPS-UI/package.json`
  - Add `smoke:device-v2-detail-collection-model`.

- Modify: `OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue`
  - Import the new helpers.
  - Replace the small current detail fact grids with section-driven rendering.
  - Reorder collection drawer content so device result list and structured collected data appear before raw technical evidence.
  - Preserve existing functions: `openSelectedDeviceLastCollectionWorkbench`, `openDc2CollectionDetail`, `downloadCollectDiagnosticLogs`, `refreshCollectResult`, `startCollectResultAutoRefresh`, `restoreBatchWorkbenches`, `syncBatchCollectWorkbench`.

---

### Task 1: Add Pure Detail And Collection Models

**Files:**
- Create: `OneOPS-UI/src/views/device/device-v2-management/detail-section-model.ts`
- Create: `OneOPS-UI/src/views/device/device-v2-management/collection-result-model.ts`
- Create: `OneOPS-UI/scripts/device-v2-detail-collection-model-smoke.ts`
- Modify: `OneOPS-UI/package.json`

- [ ] **Step 1: Create the model directory**

Run:

```bash
mkdir -p OneOPS-UI/src/views/device/device-v2-management
```

Expected: directory exists.

- [ ] **Step 2: Add detail section model**

Create `OneOPS-UI/src/views/device/device-v2-management/detail-section-model.ts` with:

```ts
import type { DeviceV2Item, DeviceV2LastStoreCollectionDc2Resp } from '@/api/device/device-v2';
import { readAnyString, toAnyMap } from '@/views/device/device-v2-redesign/mappers';

export type DeviceV2DetailKind = 'server' | 'network' | 'generic';

export interface DeviceV2DetailField {
  key: string;
  label: string;
  value: string;
  source: 'device_v2' | 'attributes' | 'metadata' | 'labels' | 'latest_collection';
  secret?: boolean;
}

export interface DeviceV2DetailSection {
  key: string;
  title: string;
  fields: DeviceV2DetailField[];
}

function readLabel(record: DeviceV2Item | null | undefined, key: string) {
  return readAnyString(toAnyMap(record?.labels), key);
}

function readAttr(record: DeviceV2Item | null | undefined, ...keys: string[]) {
  const attrs = toAnyMap(record?.attributes);
  for (const key of keys) {
    const value = readAnyString(attrs, key);
    if (value) return value;
  }
  return '';
}

function readMeta(record: DeviceV2Item | null | undefined, ...keys: string[]) {
  const metadata = toAnyMap(record?.metadata);
  for (const key of keys) {
    const value = readAnyString(metadata, key);
    if (value) return value;
  }
  return '';
}

function field(
  key: string,
  label: string,
  value: string,
  source: DeviceV2DetailField['source'],
  opts?: { secret?: boolean },
): DeviceV2DetailField | null {
  const text = String(value || '').trim();
  if (!text || text === '-') return null;
  return { key, label, value: text, source, secret: opts?.secret };
}

function compact(fields: Array<DeviceV2DetailField | null>): DeviceV2DetailField[] {
  return fields.filter((item): item is DeviceV2DetailField => !!item);
}

export function classifyDeviceV2DetailKind(record?: DeviceV2Item | null): DeviceV2DetailKind {
  const attrs = toAnyMap(record?.attributes);
  const candidates = [
    record?.type,
    readAnyString(attrs, 'device_type'),
    readAnyString(attrs, 'target_kind'),
    readAnyString(attrs, 'catalog_name'),
    readAnyString(attrs, 'catalog_code'),
    readAnyString(attrs, 'platform_name'),
    readAnyString(attrs, 'platform_code'),
  ]
    .join(' ')
    .toLowerCase();
  if (/(switch|router|firewall|network|nvr|olt|onu|snmp|交换|路由|防火墙|网络)/i.test(candidates)) return 'network';
  if (/(server|linux|windows|vm|host|服务器|主机)/i.test(candidates)) return 'server';
  return 'generic';
}

export function buildDeviceV2DetailSections(
  record?: DeviceV2Item | null,
  latestCollection?: DeviceV2LastStoreCollectionDc2Resp | null,
): DeviceV2DetailSection[] {
  const attrs = toAnyMap(record?.attributes);
  const kind = classifyDeviceV2DetailKind(record);
  const sections: DeviceV2DetailSection[] = [];

  sections.push({
    key: 'identity',
    title: '基础身份',
    fields: compact([
      field('code', '设备编号', record?.code || '', 'device_v2'),
      field('name', '设备名称', record?.name || '', 'device_v2'),
      field('type', '设备类型', record?.type || readAttr(record, 'device_type', 'target_kind'), 'device_v2'),
      field('platform', '平台', readAttr(record, 'platform_name', 'platform_code') || record?.platform_code || '', 'attributes'),
      field('vendor', '厂商', readAttr(record, 'vendor', 'manufacturer'), 'attributes'),
      field('model', '型号', readAttr(record, 'model', 'model_name', 'hardware_model'), 'attributes'),
      field('serial_number', '序列号', readAttr(record, 'sn', 'serial_number', 'serialNumber'), 'attributes'),
      field('hostname', '主机名', readAttr(record, 'hostname', 'host_name'), 'attributes'),
      field('status', '设备状态', record?.status || '', 'device_v2'),
      field('updated_at', '最近更新时间', record?.updated_at || '', 'device_v2'),
    ]),
  });

  sections.push({
    key: 'location',
    title: '位置与归属',
    fields: compact([
      field('tenant', '租户', readAttr(record, 'tenant_name', 'tenant_code') || readLabel(record, 'tenant'), 'attributes'),
      field('region', '区域', record?.function_area || readAttr(record, 'region_name', 'region_code', 'region'), 'attributes'),
      field('site', '机房', readAttr(record, 'site_name', 'site_code', 'site'), 'attributes'),
      field('rack', '机架', readAttr(record, 'rack_name', 'rack_code', 'rack'), 'attributes'),
      field('security_zone', '安全区', readAttr(record, 'security_zone', 'zone', 'area'), 'attributes'),
      field('group_tags', '分组标签', Array.isArray(record?.group_tags) ? record.group_tags.join('，') : '', 'device_v2'),
    ]),
  });

  sections.push({
    key: 'access',
    title: '网络与访问',
    fields: compact([
      field('management_ip', '管理 IP', readAttr(record, 'management_ip', 'primary_ip', 'ip'), 'attributes'),
      field('in_band_ip', '带内地址', readAttr(record, 'in_band_ip'), 'attributes'),
      field('out_band_ip', '带外地址', readAttr(record, 'out_band_ip'), 'attributes'),
      field('access_protocol', '访问协议', readAttr(record, 'access_protocol', 'protocol', 'login_method'), 'attributes'),
      field('snmp_credential_ref', 'SNMP 凭证', readAttr(record, 'snmp_credential_ref'), 'attributes', { secret: true }),
      field('credential_ref_in_band', '带内凭证', readAttr(record, 'credential_ref_in_band'), 'attributes', { secret: true }),
      field('credential_ref_out_band', '带外凭证', readAttr(record, 'credential_ref_out_band'), 'attributes', { secret: true }),
      field('winrm_credential_ref', 'WinRM 凭证', readAttr(record, 'winrm_credential_ref'), 'attributes', { secret: true }),
    ]),
  });

  if (latestCollection?.found) {
    sections.push({
      key: 'latest_collection',
      title: '最近一次基础信息采集',
      fields: compact([
        field('dc2_run_id', 'DC2 采集记录', latestCollection.dc2_run_id || '', 'latest_collection'),
        field('target_id', '目标设备', latestCollection.target_id || '', 'latest_collection'),
        field('contract_key', '采集协议', latestCollection.contract_key || '', 'latest_collection'),
        field('task_id', '任务 ID', latestCollection.task_id || '', 'latest_collection'),
        field('store_run_id', '执行记录', latestCollection.store_run_id || '', 'latest_collection'),
      ]),
    });
  }

  if (kind === 'server') {
    sections.push({
      key: 'server_profile',
      title: '服务器信息',
      fields: compact([
        field('os_name', '操作系统', readAttr(record, 'os_name', 'os'), 'attributes'),
        field('os_version', 'OS 版本', readAttr(record, 'os_version', 'system_version'), 'attributes'),
        field('kernel_version', '内核版本', readAttr(record, 'kernel_version'), 'attributes'),
        field('cpu_model', 'CPU 型号', readAttr(record, 'cpu_model'), 'attributes'),
        field('cpu_cores', 'CPU 核数', readAttr(record, 'cpu_cores'), 'attributes'),
        field('memory_total', '内存容量', readAttr(record, 'memory_total', 'memory_total_bytes'), 'attributes'),
        field('disk_summary', '磁盘摘要', readAttr(record, 'disk_summary', 'filesystem_summary'), 'attributes'),
        field('virtualization', '虚拟化', readAttr(record, 'virtualization', 'hypervisor', 'host_machine'), 'attributes'),
      ]),
    });
  } else if (kind === 'network') {
    sections.push({
      key: 'network_profile',
      title: '网络设备信息',
      fields: compact([
        field('role', '设备角色', readAttr(record, 'role', 'device_role'), 'attributes'),
        field('firmware_version', '固件/软件版本', readAttr(record, 'firmware_version', 'software_version', 'system_version'), 'attributes'),
        field('sys_name', 'sysName', readAttr(record, 'sysName', 'sys_name'), 'attributes'),
        field('sys_descr', 'sysDescr', readAttr(record, 'sysDescr', 'sys_descr'), 'attributes'),
        field('sys_object_id', 'sysObjectID', readAttr(record, 'sysObjectID', 'sys_object_id'), 'attributes'),
        field('sys_location', 'sysLocation', readAttr(record, 'sysLocation', 'sys_location'), 'attributes'),
        field('sys_contact', 'sysContact', readAttr(record, 'sysContact', 'sys_contact'), 'attributes'),
        field('interface_count', '接口数量', readAttr(record, 'interface_count', 'if_count'), 'attributes'),
        field('interface_status', '接口状态摘要', readAttr(record, 'interface_status_summary'), 'attributes'),
      ]),
    });
  }

  sections.push({
    key: 'collection_hints',
    title: '采集结构化摘要',
    fields: compact([
      field('last_collection_at', '最近采集时间', readMeta(record, 'last_collection_at', 'collected_at'), 'metadata'),
      field('last_collection_status', '最近采集状态', readMeta(record, 'last_collection_status'), 'metadata'),
      field('runtime_evidence', '采集证据', readMeta(record, 'runtime_evidence'), 'metadata'),
    ]),
  });

  return sections.filter(section => section.fields.length > 0);
}
```

- [ ] **Step 3: Add collection result model**

Create `OneOPS-UI/src/views/device/device-v2-management/collection-result-model.ts` with:

```ts
import type {
  DeviceV2StoreCollectionPlanItem,
  DeviceV2StoreObservationItem,
  DeviceV2StoreRunItem,
} from '@/api/device/device-v2';
import { readAnyString, toAnyMap } from '@/views/device/device-v2-redesign/mappers';

export interface CollectionResultDeviceRow {
  key: string;
  deviceCode: string;
  status: string;
  stage: string;
  protocol: string;
  collectedAt: string;
  summary: string;
}

export interface CollectionStructuredField {
  key: string;
  label: string;
  value: string;
  status: string;
  sourceField: string;
}

export interface CollectionStructuredSection {
  key: string;
  title: string;
  fields: CollectionStructuredField[];
}

export interface CollectionPlanRow {
  key: string;
  action: string;
  capability: string;
  status: string;
  reason: string;
}

function statusText(value: unknown) {
  return readAnyString(value) || '-';
}

function valuePreview(value: unknown) {
  if (value == null) return '';
  if (typeof value === 'string') return value.trim();
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function observationText(item: DeviceV2StoreObservationItem) {
  const value = toAnyMap(item.value);
  return (
    readAnyString(value, 'display') ||
    readAnyString(value, 'value') ||
    readAnyString(value, 'text') ||
    valuePreview(item.value) ||
    valuePreview(item.raw)
  );
}

function sectionKeyForField(fieldKey: string, capability: string) {
  const key = `${fieldKey} ${capability}`.toLowerCase();
  if (/(sysname|sysdescr|sysobject|syslocation|syscontact|snmp|interface|iftable|ifname|ifdescr|port|mac|neighbor)/.test(key)) {
    return 'network';
  }
  if (/(cpu|memory|mem|disk|filesystem|os|kernel|host|hostname|system)/.test(key)) return 'server';
  if (/(ip|address|credential|access|protocol|plane)/.test(key)) return 'access';
  if (/(region|site|rack|tenant|location|zone|area)/.test(key)) return 'location';
  return 'identity';
}

const sectionTitles: Record<string, string> = {
  identity: '基础身份',
  access: '网络与访问',
  location: '位置与归属',
  server: '硬件与系统',
  network: '接口与协议证据',
};

export function buildCollectionResultDeviceRows(runs: DeviceV2StoreRunItem[]): CollectionResultDeviceRow[] {
  return runs.map(item => {
    const summary = toAnyMap(item.summary);
    return {
      key: item.run_id || readAnyString(item.device_code),
      deviceCode: readAnyString(item.device_code) || '-',
      status: readAnyString(item.display_status_label) || readAnyString(item.display_status) || readAnyString(item.status) || '-',
      stage: readAnyString(item.display_stage_label) || readAnyString(item.current_step) || '-',
      protocol: readAnyString(summary, 'contract_key') || readAnyString(summary, 'protocol') || '-',
      collectedAt: readAnyString(item.finished_at) || readAnyString(item.updated_at) || readAnyString(item.created_at) || '-',
      summary: readAnyString(item.display_summary) || readAnyString(summary, 'message') || '-',
    };
  });
}

export function buildCollectionStructuredSections(
  observations: DeviceV2StoreObservationItem[],
): CollectionStructuredSection[] {
  const groups = new Map<string, CollectionStructuredField[]>();
  observations.forEach(item => {
    const fieldKey = readAnyString(item.field_key);
    const capability = readAnyString(item.capability);
    const text = observationText(item);
    if (!fieldKey || !text) return;
    const groupKey = sectionKeyForField(fieldKey, capability);
    const fields = groups.get(groupKey) || [];
    fields.push({
      key: item.observation_id || `${fieldKey}:${fields.length}`,
      label: fieldKey,
      value: text,
      status: readAnyString(item.status) || '-',
      sourceField: fieldKey,
    });
    groups.set(groupKey, fields);
  });
  return Array.from(groups.entries()).map(([key, fields]) => ({
    key,
    title: sectionTitles[key] || key,
    fields,
  }));
}

export function buildCollectionPlanRows(plans: DeviceV2StoreCollectionPlanItem[]): CollectionPlanRow[] {
  return plans.map((item, index) => ({
    key: String(item.id ?? `${item.device_code || 'device'}:${index}`),
    action: readAnyString(item.action) || '-',
    capability: readAnyString(item.capability) || '-',
    status: readAnyString(item.status) || '-',
    reason: readAnyString(item.reason) || '-',
  }));
}
```

- [ ] **Step 4: Add smoke script**

Create `OneOPS-UI/scripts/device-v2-detail-collection-model-smoke.ts` with:

```ts
import assert from 'node:assert/strict';
import type { DeviceV2Item, DeviceV2StoreObservationItem } from '../src/api/device/device-v2';
import { buildDeviceV2DetailSections, classifyDeviceV2DetailKind } from '../src/views/device/device-v2-management/detail-section-model';
import { buildCollectionStructuredSections } from '../src/views/device/device-v2-management/collection-result-model';

const server: DeviceV2Item = {
  id: '1',
  code: 'srv-001',
  name: 'srv-001',
  type: 'server',
  platform_code: 'linux',
  status: 'active',
  attributes: {
    os_name: 'Linux',
    os_version: 'Ubuntu 22.04',
    cpu_cores: 16,
    memory_total: '64GB',
    in_band_ip: '10.0.0.10',
  },
};

const network: DeviceV2Item = {
  id: '2',
  code: 'sw-001',
  name: 'sw-001',
  type: 'switch',
  platform_code: 'network',
  status: 'active',
  attributes: {
    sysName: 'core-sw-001',
    sysDescr: 'Switch OS',
    sysObjectID: '1.3.6.1.4.1',
    snmp_credential_ref: 'cred-snmp',
  },
};

const observations: DeviceV2StoreObservationItem[] = [
  {
    observation_id: 'obs-1',
    field_key: 'sysName',
    capability: 'snmp',
    status: 'success',
    value: { value: 'core-sw-001' },
  },
  {
    observation_id: 'obs-2',
    field_key: 'cpu_cores',
    capability: 'ssh',
    status: 'success',
    value: { value: 16 },
  },
];

assert.equal(classifyDeviceV2DetailKind(server), 'server');
assert.equal(classifyDeviceV2DetailKind(network), 'network');

const serverSections = buildDeviceV2DetailSections(server, null);
assert.ok(serverSections.some(section => section.key === 'server_profile'));
assert.ok(!serverSections.some(section => section.key === 'network_profile'));

const networkSections = buildDeviceV2DetailSections(network, null);
assert.ok(networkSections.some(section => section.key === 'network_profile'));
assert.ok(!networkSections.some(section => section.key === 'server_profile'));

const structured = buildCollectionStructuredSections(observations);
assert.ok(structured.some(section => section.key === 'network'));
assert.ok(structured.some(section => section.key === 'server'));

console.log('device-v2-detail-collection-model smoke passed');
```

- [ ] **Step 5: Add smoke command**

In `OneOPS-UI/package.json`, add this script entry after `smoke:d2-ingest-buttons`:

```json
"smoke:device-v2-detail-collection-model": "npx esbuild scripts/device-v2-detail-collection-model-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/device-v2-detail-collection-model-smoke.mjs >/dev/null && node .tmp/device-v2-detail-collection-model-smoke.mjs"
```

Because it is not the last script entry, ensure JSON commas remain valid.

- [ ] **Step 6: Run smoke test**

Run:

```bash
cd OneOPS-UI
npm run smoke:device-v2-detail-collection-model
```

Expected:

```text
device-v2-detail-collection-model smoke passed
```

- [ ] **Step 7: Run D2 typecheck**

Run:

```bash
cd OneOPS-UI
npm run typecheck:d2
```

Expected: command exits with code `0`.

- [ ] **Step 8: Commit**

Run:

```bash
git add OneOPS-UI/package.json \
  OneOPS-UI/scripts/device-v2-detail-collection-model-smoke.ts \
  OneOPS-UI/src/views/device/device-v2-management/detail-section-model.ts \
  OneOPS-UI/src/views/device/device-v2-management/collection-result-model.ts
git commit -m "feat: add device v2 detail collection models"
```

Expected: commit created with only the four files above.

---

### Task 2: Wire Type-Aware Sections Into Device Detail Drawer

**Files:**
- Modify: `OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue`
- Test: `OneOPS-UI/scripts/device-v2-detail-collection-model-smoke.ts`

- [ ] **Step 1: Import detail model**

In `DeviceV2ManagementGrouped.vue`, add imports near the existing device imports:

```ts
import type { DeviceV2DetailSection } from '@/views/device/device-v2-management/detail-section-model';
import { buildDeviceV2DetailSections } from '@/views/device/device-v2-management/detail-section-model';
```

- [ ] **Step 2: Add computed section model**

Near the existing `selectedBaseFacts`, `selectedLocationFacts`, and `selectedTechnicalFacts` computed values, add:

```ts
const selectedDeviceDetailSections = computed<DeviceV2DetailSection[]>(() =>
  buildDeviceV2DetailSections(selectedDeviceRecord.value, selectedDeviceLastCollectionMeta.value),
);

function detailSectionSourceLabel(source: DeviceV2DetailSection['fields'][number]['source']) {
  if (source === 'latest_collection') return '最近采集';
  if (source === 'attributes') return '设备属性';
  if (source === 'metadata') return '运行数据';
  if (source === 'labels') return '标签';
  return '清册';
}
```

- [ ] **Step 3: Replace old detail fact blocks**

In the detail drawer template, replace the three blocks titled `基础信息`, `网络与位置`, and `技术信息`, plus the current `最近一次采集` block, with:

```vue
<section
  v-for="section in selectedDeviceDetailSections"
  :key="section.key"
  class="detail-block detail-block--structured"
>
  <div class="detail-block__title">{{ section.title }}</div>
  <div class="fact-grid fact-grid--structured">
    <div v-for="item in section.fields" :key="item.key" class="fact-grid__item">
      <span>
        {{ item.label }}
        <a-tag v-if="item.secret" size="small" color="blue">引用</a-tag>
      </span>
      <strong>{{ item.value }}</strong>
      <small class="fact-grid__source">{{ detailSectionSourceLabel(item.source) }}</small>
    </div>
  </div>

  <a-button
    v-if="section.key === 'latest_collection' && selectedDeviceLastCollectionMeta?.found"
    type="link"
    class="inline-link-button"
    @click="openSelectedDeviceLastCollectionWorkbench"
  >
    查看详细数据
  </a-button>
</section>

<section v-if="!selectedDeviceDetailSections.length" class="detail-block">
  <a-empty :image="false" description="当前设备暂无可展示的结构化详情" />
</section>
```

- [ ] **Step 4: Keep detail action block unchanged**

Confirm the `设备操作` block still contains:

```vue
<a-button block :loading="collecting" @click="openCollectConfirm([selectedDeviceView.code])">采集</a-button>
<a-button block type="primary" :loading="monitoring" @click="openMonitorConfirm([selectedDeviceView.code])">
  监控
</a-button>
```

Expected: device actions remain present and still open existing confirm flows.

- [ ] **Step 5: Add source hint styling**

In the `<style scoped>` section of `DeviceV2ManagementGrouped.vue`, add:

```less
.detail-block--structured {
  .fact-grid__item {
    min-height: 72px;
  }
}

.fact-grid__source {
  display: block;
  margin-top: 4px;
  color: #8c8c8c;
  font-size: 12px;
  font-weight: 400;
}
```

- [ ] **Step 6: Run verification**

Run:

```bash
cd OneOPS-UI
npm run smoke:device-v2-detail-collection-model
npm run typecheck:d2
```

Expected:

```text
device-v2-detail-collection-model smoke passed
```

and `typecheck:d2` exits with code `0`.

- [ ] **Step 7: Manual check**

Start dev server if one is not already running:

```bash
cd OneOPS-UI
npm run dev -- --host 127.0.0.1
```

Open:

```text
http://127.0.0.1:5173/#/device/device-v2-management
```

If Vite selects another port, keep the same hash route on the printed dev-server URL.

Check:

- Detail drawer shows multiple structured sections when fields exist.
- Server devices show `服务器信息` and do not show empty SNMP fields.
- Network devices show `网络设备信息` and do not show empty OS / CPU / memory fields.
- `查看详细数据` still jumps through `openSelectedDeviceLastCollectionWorkbench`.

- [ ] **Step 8: Commit**

Run:

```bash
git add OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue
git commit -m "feat: improve device v2 detail sections"
```

Expected: commit contains only `DeviceV2ManagementGrouped.vue`.

---

### Task 3: Reorder Collection Drawer Around Device Results And Structured Data

**Files:**
- Modify: `OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue`
- Test: `OneOPS-UI/scripts/device-v2-detail-collection-model-smoke.ts`

- [ ] **Step 1: Import collection model**

In `DeviceV2ManagementGrouped.vue`, add:

```ts
import type { CollectionResultDeviceRow, CollectionStructuredSection } from '@/views/device/device-v2-management/collection-result-model';
import {
  buildCollectionPlanRows,
  buildCollectionResultDeviceRows,
  buildCollectionStructuredSections,
} from '@/views/device/device-v2-management/collection-result-model';
```

- [ ] **Step 2: Add computed drawer models**

Near existing `collectResultObservationRows` and `collectResultPlanRows` computed values, add:

```ts
const collectResultDeviceRows = computed<CollectionResultDeviceRow[]>(() =>
  buildCollectionResultDeviceRows(collectResultRuns.value),
);

const collectResultStructuredSections = computed<CollectionStructuredSection[]>(() =>
  buildCollectionStructuredSections(collectResultObservations.value),
);

const collectResultStructuredEmptyMessage = computed(() =>
  collectResultPrimaryDeviceCode.value
    ? `${collectResultPrimaryDeviceCode.value} 暂无可分区展示的结构化采集字段`
    : '当前暂无可分区展示的结构化采集字段',
);
```

Do not delete the existing `collectResultObservationRows` computed value; it remains the field-level detail table.

- [ ] **Step 3: Move device results before technical evidence**

In the collection drawer template, place this block immediately after the status alerts and before `技术排障信息（供专业人员使用）`:

```vue
<div v-if="collectResultDeviceRows.length" class="detail-block">
  <div class="detail-block__title">设备采集结果</div>
  <a-table
    :data-source="collectResultDeviceRows"
    :pagination="false"
    :scroll="{ x: 860 }"
    row-key="key"
    size="small"
  >
    <a-table-column key="deviceCode" title="设备" data-index="deviceCode" width="160" />
    <a-table-column key="status" title="状态" data-index="status" width="120" />
    <a-table-column key="stage" title="阶段" data-index="stage" width="140" />
    <a-table-column key="protocol" title="协议" data-index="protocol" width="120" />
    <a-table-column key="collectedAt" title="采集时间" data-index="collectedAt" width="180" />
    <a-table-column key="summary" title="说明" data-index="summary" />
    <a-table-column v-if="collectResultIsBatch" key="action" title="操作" width="120">
      <template #default="{ record }">
        <a-button
          type="link"
          size="small"
          :disabled="!plainText(record.deviceCode)"
          @click="focusCollectResultDevice(record.deviceCode)"
        >
          {{ plainText(record.deviceCode) === collectResultPrimaryDeviceCode ? '当前查看' : '查看详情' }}
        </a-button>
      </template>
    </a-table-column>
  </a-table>
</div>
```

- [ ] **Step 4: Add structured collection result block**

Place this block after `设备采集结果` and before the old field-level observation table:

```vue
<div class="detail-block">
  <div class="detail-block__title">当前设备结构化采集结果</div>
  <template v-if="collectResultStructuredSections.length">
    <div class="collection-structured-grid">
      <article
        v-for="section in collectResultStructuredSections"
        :key="section.key"
        class="collection-structured-card"
      >
        <div class="collection-structured-card__title">{{ section.title }}</div>
        <div class="collection-structured-card__fields">
          <div v-for="item in section.fields" :key="item.key" class="collection-structured-field">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <a-tag :color="runtimeStatusColor(item.status)">{{ humanizeRuntimeText(item.status) }}</a-tag>
          </div>
        </div>
      </article>
    </div>
  </template>
  <a-empty v-else :image="false" :description="collectResultStructuredEmptyMessage" />
</div>
```

- [ ] **Step 5: Retitle existing observation table**

Change the existing detail block title from:

```vue
<div class="detail-block__title">{{ collectResultObservationTitle }}</div>
```

to:

```vue
<div class="detail-block__title">字段明细</div>
```

Keep the existing table columns and selected observation detail unchanged.

- [ ] **Step 6: Keep raw evidence and plan blocks**

Confirm these existing blocks still exist:

- `技术排障信息（供专业人员使用）`
- `最后一次 DC2 采集`
- selected observation detail with `标准化值` and `原始采集数据`
- `后续可采集数据`

Expected: no evidence block is removed.

- [ ] **Step 7: Add structured drawer styles**

In `<style scoped>`, add:

```less
.collection-structured-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.collection-structured-card {
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  padding: 12px;
  background: #fff;
}

.collection-structured-card__title {
  margin-bottom: 8px;
  font-weight: 600;
  color: #262626;
}

.collection-structured-card__fields {
  display: grid;
  gap: 8px;
}

.collection-structured-field {
  display: grid;
  grid-template-columns: minmax(80px, 0.8fr) minmax(0, 1.4fr) auto;
  gap: 8px;
  align-items: center;
}

.collection-structured-field span {
  color: #8c8c8c;
}

.collection-structured-field strong {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

- [ ] **Step 8: Run verification**

Run:

```bash
cd OneOPS-UI
npm run smoke:device-v2-detail-collection-model
npm run typecheck:d2
```

Expected: both commands pass.

- [ ] **Step 9: Manual check**

Use an existing or newly created collection task and verify:

- Batch collection still opens the result drawer.
- Manual refresh still works.
- Running tasks still auto-refresh.
- Device result list appears before raw technical evidence.
- Clicking `查看详情` switches the focused device and reloads observations.
- `下载当前设备排障日志` still works for the focused device.

- [ ] **Step 10: Commit**

Run:

```bash
git add OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue
git commit -m "feat: reorganize device v2 collection drawer"
```

Expected: commit contains only `DeviceV2ManagementGrouped.vue`.

---

### Task 4: Preserve And Verify Existing Collection Task Guarantees

**Files:**
- Modify: `OneOPS-UI/docs/device-v2-ui-autodev/CLOSURE_CHECKLIST.md`
- Modify: `OneOPS-UI/docs/device-v2-ui-autodev/COORDINATION.md` only if a field source is unclear
- Create: `docs/openclaw-autodev/evidence/d2-fe/DETAIL-COLLECTION-20260603/summary.md`

- [ ] **Step 1: Run deterministic checks**

Run:

```bash
cd OneOPS-UI
npm run smoke:device-v2-detail-collection-model
npm run typecheck:d2
```

Expected: both pass.

- [ ] **Step 2: Check preserved functions in source**

Run:

```bash
cd OneOPS-UI
rg -n "restoreBatchWorkbenches|syncBatchCollectWorkbench|downloadCollectDiagnosticLogs|openSelectedDeviceLastCollectionWorkbench|openDc2CollectionDetail|startCollectResultAutoRefresh|refreshCollectResult" src/views/device/DeviceV2ManagementGrouped.vue
```

Expected: each function name appears at least once.

- [ ] **Step 3: Write verification evidence**

Create `docs/openclaw-autodev/evidence/d2-fe/DETAIL-COLLECTION-20260603/summary.md` with:

```md
# Device V2 Detail And Collection Drawer Verification

## Scope

- Device detail is rendered from structured sections.
- Server and network devices use type-specific sections.
- Collection result drawer shows task overview, device result list, structured collected data, field details, and technical evidence.
- Batch collection triggers and batch task workbench behavior were not changed.

## Files

- `OneOPS-UI/src/views/device/device-v2-management/detail-section-model.ts`
- `OneOPS-UI/src/views/device/device-v2-management/collection-result-model.ts`
- `OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue`
- `OneOPS-UI/scripts/device-v2-detail-collection-model-smoke.ts`

## Validation

- `npm run smoke:device-v2-detail-collection-model`
- `npm run typecheck:d2`

## Preserved Behaviors

- Manual refresh remains available in the collection drawer.
- Running collection task auto-refresh remains available.
- Batch task restoration remains available through `restoreBatchWorkbenches`.
- Diagnostic log download remains available through `downloadCollectDiagnosticLogs`.
- Latest DC2 collection detail jump remains available through `openSelectedDeviceLastCollectionWorkbench` and `openDc2CollectionDetail`.

## Risk

No backend contract changes are included. If a field source is unclear, the implementation records the field question in `OneOPS-UI/docs/device-v2-ui-autodev/COORDINATION.md` instead of guessing.
```

- [ ] **Step 4: Document checklist result**

Append this line under the Device V2 management section in `OneOPS-UI/docs/device-v2-ui-autodev/CLOSURE_CHECKLIST.md`:

```md
- [x] 设备详情和采集结果抽屉已按结构化设备档案与采集证据中心重组；批量采集触发点、批量任务工作台、刷新后任务不丢、日志下载、最近一次 DC2 采集跳转均保留。Evidence: `../docs/openclaw-autodev/evidence/d2-fe/DETAIL-COLLECTION-20260603/summary.md`
```

- [ ] **Step 5: Record field contract gaps only if needed**

If implementation discovers that `sysDescr` is needed for the network-device section but the source is unclear, append this exact question to `OneOPS-UI/docs/device-v2-ui-autodev/COORDINATION.md` under `Questions`:

```md
- 2026-06-03 D2FE-DETAIL-COLLECTION-Q001: Device detail field `sysDescr` is needed for the network-device section, but current FE source audit cannot confirm whether it should come from Device V2 attributes, metadata, latest DC2 observation, or V1 relation. Please confirm source, enum/format, and missing-value behavior before production exposure.
```

For any other unclear field, write a separate concrete question with the exact field name and section name; do not use a generic template string.

- [ ] **Step 6: Run final D2 gate**

Run:

```bash
cd OneOPS-UI
npm run typecheck:d2
```

Expected: exits with code `0`.

- [ ] **Step 7: Commit docs**

Run:

```bash
git add OneOPS-UI/docs/device-v2-ui-autodev/CLOSURE_CHECKLIST.md \
  OneOPS-UI/docs/device-v2-ui-autodev/COORDINATION.md \
  docs/openclaw-autodev/evidence/d2-fe/DETAIL-COLLECTION-20260603/summary.md
git commit -m "docs: record device v2 detail collection verification"
```

Expected: commit contains documentation updates only. If `COORDINATION.md` was not changed, omit it from `git add`.

---

## Self-Review Notes

Spec coverage:

- Device detail as structured device archive: Task 1 and Task 2.
- Server/network type-specific display: Task 1 smoke test and Task 2 wiring.
- Keep recent collection jump: Task 2 Step 3 and Task 4 Step 2.
- Collection drawer result organization: Task 1 and Task 3.
- Preserve refresh, task retention, logs, raw data: Task 3 Step 6 and Task 4.
- Do not adjust batch collection trigger or task workbench: no task changes those areas.

Concrete-step review:

- All planned new files have concrete code.
- Verification commands and expected outputs are specified.
- Backend field uncertainty has a concrete `COORDINATION.md` question format.
