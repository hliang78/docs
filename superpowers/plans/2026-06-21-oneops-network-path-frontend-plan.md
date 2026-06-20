# OneOPS 网络路径前端实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有 `NetPathMvp` 单页研发工作台拆分为正式的 `网络路径` 查询页与 `路径详情` 页，在真实拓扑上展示路径、节点证据、连通性验证与后续处理。

**Architecture:** 保留现有 `topology/netpath` 路由作为兼容入口，但把页面实现改为新的查询页壳；新增详情页与 4 个共享组件，把 `NetPathMvp.vue` 中的查询、拓扑投影、设备证据、Probe/Ticket/Task 能力拆到可复用的 `network-path` 子目录下。真实拓扑继续复用 `Topology.vue` 与 `topologyGenerateReq`，路径投影继续复用 `netpath-graph.ts`。

**Tech Stack:** Vue 3 + TypeScript + Ant Design Vue + Vue Router + 现有 NetPath/Topology API + esbuild smoke scripts

---

## File Structure

### New files

- `OneOPS-UI/src/views/topology/NetworkPathIndex.vue`
- `OneOPS-UI/src/views/topology/NetworkPathDetail.vue`
- `OneOPS-UI/src/views/topology/network-path/PathQueryForm.vue`
- `OneOPS-UI/src/views/topology/network-path/PathResultTable.vue`
- `OneOPS-UI/src/views/topology/network-path/PathTopologyView.vue`
- `OneOPS-UI/src/views/topology/network-path/PathDiagnosticPanel.vue`
- `OneOPS-UI/src/views/topology/network-path/useNetworkPathIndex.ts`
- `OneOPS-UI/src/views/topology/network-path/useNetworkPathDetail.ts`
- `OneOPS-UI/src/views/topology/network-path/copy.ts`
- `OneOPS-UI/src/views/topology/network-path/mappers.ts`
- `OneOPS-UI/scripts/network-path-route-smoke.ts`
- `OneOPS-UI/scripts/network-path-page-smoke.ts`

### Modified files

- `OneOPS-UI/src/router/utils.ts`
- `OneOPS-UI/src/views/topology/NetPathMvp.vue`
- `OneOPS-UI/src/views/topology/netpath-evidence-helpers.ts`
- `OneOPS-UI/package.json`
- `docs/superpowers/specs/2026-06-21-oneops-network-path-design.md` (only if implementation reveals a spec mismatch)

### Existing files reused as-is

- `OneOPS-UI/src/components/Topology/Topology.vue`
- `OneOPS-UI/src/views/topology/netpath-graph.ts`
- `OneOPS-UI/src/api/netpath/netpath.ts`
- `OneOPS-UI/src/api/topology/topology.ts`
- `OneOPS-UI/src/typings/netpath/netpath.ts`
- `OneOPS-UI/src/typings/topology/topology.ts`

---

### Task 1: Split the Route Shell and Shared View State

**Files:**
- Create: `OneOPS-UI/src/views/topology/NetworkPathIndex.vue`
- Create: `OneOPS-UI/src/views/topology/NetworkPathDetail.vue`
- Create: `OneOPS-UI/src/views/topology/network-path/useNetworkPathIndex.ts`
- Create: `OneOPS-UI/src/views/topology/network-path/useNetworkPathDetail.ts`
- Create: `OneOPS-UI/src/views/topology/network-path/copy.ts`
- Modify: `OneOPS-UI/src/router/utils.ts`
- Modify: `OneOPS-UI/src/views/topology/NetPathMvp.vue`
- Test: `OneOPS-UI/scripts/network-path-route-smoke.ts`

- [ ] **Step 1: Write the failing route smoke test**

```ts
// OneOPS-UI/scripts/network-path-route-smoke.ts
import { readFileSync } from 'node:fs';

const router = readFileSync('src/router/utils.ts', 'utf8');

if (!router.includes("path: 'topology/netpath'")) {
  throw new Error('missing network path index route');
}

if (!router.includes("path: 'topology/netpath/detail'")) {
  throw new Error('missing network path detail route');
}

if (!router.includes("title: '网络路径'")) {
  throw new Error('network path route title not updated');
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd OneOPS-UI && node scripts/network-path-route-smoke.ts`
Expected: FAIL with missing detail route and missing renamed title.

- [ ] **Step 3: Add the route shell and copy module**

```ts
// OneOPS-UI/src/views/topology/network-path/copy.ts
export const NETWORK_PATH_COPY = {
  indexTitle: '网络路径',
  indexSubtitle: '面向网络运维的访问路径查询与故障定位，统一查看路径、转发证据与连通性验证。',
  detailTitle: '路径详情',
  emptyQuery: '选择源节点和目的节点后，系统将计算访问路径并加载关联证据。',
} as const;
```

```ts
// OneOPS-UI/src/views/topology/network-path/useNetworkPathIndex.ts
import { computed, ref } from 'vue';

export function useNetworkPathIndex() {
  const sourceNode = ref('debian');
  const targetNode = ref('ubuntu');
  const purpose = ref<'troubleshoot' | 'daily'>('troubleshoot');
  const lastRunCode = ref('');

  const querySummary = computed(() =>
    sourceNode.value && targetNode.value ? `${sourceNode.value} -> ${targetNode.value}` : '',
  );

  return {
    sourceNode,
    targetNode,
    purpose,
    lastRunCode,
    querySummary,
  };
}
```

```ts
// OneOPS-UI/src/views/topology/network-path/useNetworkPathDetail.ts
import { computed, ref } from 'vue';

export function useNetworkPathDetail() {
  const selectedTraceId = ref('');
  const selectedDeviceCode = ref('');
  const activeTab = ref<'summary' | 'evidence' | 'connectivity' | 'actions'>('summary');

  const hasSelection = computed(() => Boolean(selectedDeviceCode.value));

  return {
    selectedTraceId,
    selectedDeviceCode,
    activeTab,
    hasSelection,
  };
}
```

```vue
<!-- OneOPS-UI/src/views/topology/NetworkPathIndex.vue -->
<template>
  <div class="network-path-index-page">
    <a-page-header :title="NETWORK_PATH_COPY.indexTitle" :sub-title="NETWORK_PATH_COPY.indexSubtitle" />
  </div>
</template>

<script setup lang="ts">
import { NETWORK_PATH_COPY } from './network-path/copy';
</script>
```

```vue
<!-- OneOPS-UI/src/views/topology/NetworkPathDetail.vue -->
<template>
  <div class="network-path-detail-page">
    <a-page-header :title="NETWORK_PATH_COPY.detailTitle" />
  </div>
</template>

<script setup lang="ts">
import { NETWORK_PATH_COPY } from './network-path/copy';
</script>
```

- [ ] **Step 4: Wire router entries and compatibility wrapper**

```ts
// OneOPS-UI/src/router/utils.ts
const networkPathIndexRoute: RouteRecordRaw = {
  path: 'topology/netpath',
  name: 'NetworkPathIndex',
  component: () => import('@/views/topology/NetworkPathIndex.vue'),
  meta: {
    title: '网络路径',
    requiresAuth: true,
    hideInMenu: true,
  },
};

const networkPathDetailRoute: RouteRecordRaw = {
  path: 'topology/netpath/detail',
  name: 'NetworkPathDetail',
  component: () => import('@/views/topology/NetworkPathDetail.vue'),
  meta: {
    title: '路径详情',
    requiresAuth: true,
    hideInMenu: true,
  },
};
```

```vue
<!-- OneOPS-UI/src/views/topology/NetPathMvp.vue -->
<template>
  <NetworkPathIndex />
</template>

<script setup lang="ts">
import NetworkPathIndex from './NetworkPathIndex.vue';
</script>
```

- [ ] **Step 5: Run the route smoke test**

Run: `cd OneOPS-UI && node scripts/network-path-route-smoke.ts`
Expected: PASS with no output.

- [ ] **Step 6: Commit**

```bash
git -C OneOPS-UI add \
  src/router/utils.ts \
  src/views/topology/NetPathMvp.vue \
  src/views/topology/NetworkPathIndex.vue \
  src/views/topology/NetworkPathDetail.vue \
  src/views/topology/network-path/useNetworkPathIndex.ts \
  src/views/topology/network-path/useNetworkPathDetail.ts \
  src/views/topology/network-path/copy.ts \
  scripts/network-path-route-smoke.ts
git -C OneOPS-UI commit -m "feat: split network path route shell"
```

---

### Task 2: Build the Query Page and Result Table

**Files:**
- Create: `OneOPS-UI/src/views/topology/network-path/PathQueryForm.vue`
- Create: `OneOPS-UI/src/views/topology/network-path/PathResultTable.vue`
- Create: `OneOPS-UI/src/views/topology/network-path/mappers.ts`
- Modify: `OneOPS-UI/src/views/topology/NetworkPathIndex.vue`
- Modify: `OneOPS-UI/src/views/topology/network-path/useNetworkPathIndex.ts`
- Test: `OneOPS-UI/scripts/network-path-page-smoke.ts`

- [ ] **Step 1: Write the failing page smoke test**

```ts
// OneOPS-UI/scripts/network-path-page-smoke.ts
import { readFileSync } from 'node:fs';

const source = readFileSync('src/views/topology/NetworkPathIndex.vue', 'utf8');

for (const signal of ['网络路径', '开始分析', '查询结果', '主路径', '查看详情']) {
  if (!source.includes(signal)) {
    throw new Error(`missing query-page signal: ${signal}`);
  }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd OneOPS-UI && node scripts/network-path-page-smoke.ts`
Expected: FAIL because the index page only has a header.

- [ ] **Step 3: Add result mappers and query components**

```ts
// OneOPS-UI/src/views/topology/network-path/mappers.ts
import type { NetPathAnalyzeRunResp, NetPathAnalyzeTrace } from '@/typings/netpath/netpath';

export type NetworkPathResultRow = {
  key: string;
  conclusion: string;
  path: string;
  hopCount: number;
  keyNode: string;
  connectivitySummary: string;
  updatedAtText: string;
  runCode: string;
  traceId: string;
};

export function buildNetworkPathRows(run: NetPathAnalyzeRunResp | null): NetworkPathResultRow[] {
  if (!run?.result?.traces?.length) {
    return [];
  }
  return run.result.traces.map((trace: NetPathAnalyzeTrace) => ({
    key: `${run.code}-${trace.trace_id}`,
    conclusion: trace.disposition || '待复核',
    path: trace.hops.map(item => item.device_code).join(' -> '),
    hopCount: trace.hops.length,
    keyNode: trace.hops[trace.hops.length - 1]?.device_code || '-',
    connectivitySummary: '待加载连通性结果',
    updatedAtText: String(run.updated_at || ''),
    runCode: run.code,
    traceId: trace.trace_id,
  }));
}
```

```vue
<!-- OneOPS-UI/src/views/topology/network-path/PathQueryForm.vue -->
<template>
  <a-card title="发起查询" size="small">
    <a-form layout="vertical">
      <div class="network-path-query-grid">
        <a-form-item label="源节点"><a-input v-model:value="sourceNode" /></a-form-item>
        <a-form-item label="目的节点"><a-input v-model:value="targetNode" /></a-form-item>
        <a-form-item label="协议"><a-select v-model:value="protocol" :options="protocolOptions" /></a-form-item>
        <a-form-item label="目的端口"><a-input-number v-model:value="dstPort" :min="1" :max="65535" /></a-form-item>
        <a-form-item label="入口设备"><a-input v-model:value="ingressDeviceCode" /></a-form-item>
      </div>
      <a-space>
        <a-button type="primary" @click="$emit('submit')">开始分析</a-button>
        <a-button @click="$emit('reset')">重置条件</a-button>
      </a-space>
    </a-form>
  </a-card>
</template>
```

```vue
<!-- OneOPS-UI/src/views/topology/network-path/PathResultTable.vue -->
<template>
  <a-card title="查询结果" size="small">
    <a-table :columns="columns" :data-source="rows" :pagination="false" row-key="key">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'action'">
          <a-button type="link" @click="$emit('detail', record)">查看详情</a-button>
        </template>
      </template>
    </a-table>
  </a-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { NetworkPathResultRow } from './mappers';

const props = defineProps<{ rows: NetworkPathResultRow[] }>();

const columns = computed(() => [
  { title: '结论', dataIndex: 'conclusion', key: 'conclusion' },
  { title: '主路径', dataIndex: 'path', key: 'path' },
  { title: '跳数', dataIndex: 'hopCount', key: 'hopCount' },
  { title: '关键节点', dataIndex: 'keyNode', key: 'keyNode' },
  { title: '连通性概况', dataIndex: 'connectivitySummary', key: 'connectivitySummary' },
  { title: '更新时间', dataIndex: 'updatedAtText', key: 'updatedAtText' },
  { title: '操作', key: 'action' },
]);
</script>
```

- [ ] **Step 4: Wire the index page to existing create/list APIs**

```ts
// OneOPS-UI/src/views/topology/network-path/useNetworkPathIndex.ts
import { createNetPathAnalyzeRunReq, getNetPathAnalyzeRunListReq } from '@/api/netpath/netpath';
import { buildNetworkPathRows } from './mappers';

async function submitAnalyze() {
  const run = await createNetPathAnalyzeRunReq({
    tenant_code: tenantCode.value,
    src_ip: srcIp.value,
    dst_ip: dstIp.value,
    protocol: protocol.value,
    dst_port: dstPort.value,
    ingress_device_code: ingressDeviceCode.value,
  });
  latestRun.value = run;
  rows.value = buildNetworkPathRows(run);
}
```

```vue
<!-- OneOPS-UI/src/views/topology/NetworkPathIndex.vue -->
<template>
  <div class="network-path-index-page">
    <a-page-header :title="NETWORK_PATH_COPY.indexTitle" :sub-title="NETWORK_PATH_COPY.indexSubtitle" />
    <PathQueryForm v-bind="formBindings" @submit="submitAnalyze" @reset="resetForm" />
    <a-alert v-if="summaryText" type="info" show-icon :message="summaryText" />
    <PathResultTable :rows="rows" @detail="openDetail" />
  </div>
</template>
```

- [ ] **Step 5: Run the page smoke test**

Run: `cd OneOPS-UI && node scripts/network-path-page-smoke.ts`
Expected: PASS with no output.

- [ ] **Step 6: Commit**

```bash
git -C OneOPS-UI add \
  src/views/topology/NetworkPathIndex.vue \
  src/views/topology/network-path/PathQueryForm.vue \
  src/views/topology/network-path/PathResultTable.vue \
  src/views/topology/network-path/mappers.ts \
  src/views/topology/network-path/useNetworkPathIndex.ts \
  scripts/network-path-page-smoke.ts
git -C OneOPS-UI commit -m "feat: add network path query page"
```

---

### Task 3: Build the Detail Page and Path Topology View

**Files:**
- Create: `OneOPS-UI/src/views/topology/network-path/PathTopologyView.vue`
- Modify: `OneOPS-UI/src/views/topology/NetworkPathDetail.vue`
- Modify: `OneOPS-UI/src/views/topology/network-path/useNetworkPathDetail.ts`
- Test: `OneOPS-UI/scripts/network-path-page-smoke.ts`

- [ ] **Step 1: Extend the failing smoke test with detail-page signals**

```ts
const detail = readFileSync('src/views/topology/NetworkPathDetail.vue', 'utf8');

for (const signal of ['路径详情', '路径视图', '路径摘要', '节点证据']) {
  if (!detail.includes(signal)) {
    throw new Error(`missing detail-page signal: ${signal}`);
  }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd OneOPS-UI && node scripts/network-path-page-smoke.ts`
Expected: FAIL because the detail page only has a header.

- [ ] **Step 3: Add the topology view wrapper**

```vue
<!-- OneOPS-UI/src/views/topology/network-path/PathTopologyView.vue -->
<template>
  <a-card title="路径视图" size="small">
    <a-empty v-if="!topologyData?.nodes?.length" description="当前租户暂无可投影拓扑" />
    <Topology
      v-else
      :data="topologyData"
      :highlight-node-ids="highlightNodeIds"
      :highlight-edge-ids="highlightEdgeIds"
      :dimmed-node-ids="dimmedNodeIds"
      :dimmed-edge-ids="dimmedEdgeIds"
      @node-clicked="$emit('node-clicked', $event)"
    />
  </a-card>
</template>
```

- [ ] **Step 4: Load topology and projected trace on the detail page**

```ts
// OneOPS-UI/src/views/topology/network-path/useNetworkPathDetail.ts
import { topologyGenerateReq } from '@/api/topology/topology';
import { getNetPathAnalyzeRunReq } from '@/api/netpath/netpath';
import { projectNetPathGraphTraceToTopology, projectNetPathTraceToTopology } from '../netpath-graph';

async function loadDetail(code: string, tenantCode: string) {
  const [run, topology] = await Promise.all([
    getNetPathAnalyzeRunReq({ code, tenant_code: tenantCode }),
    topologyGenerateReq(tenantCode),
  ]);
  activeRun.value = run;
  topologyData.value = topology;
}
```

```vue
<!-- OneOPS-UI/src/views/topology/NetworkPathDetail.vue -->
<template>
  <div class="network-path-detail-page">
    <a-page-header :title="NETWORK_PATH_COPY.detailTitle" />
    <a-row :gutter="16">
      <a-col :span="16">
        <PathTopologyView
          :topology-data="topologyData"
          :highlight-node-ids="traceProjection.highlightNodeIds"
          :highlight-edge-ids="traceProjection.highlightEdgeIds"
          :dimmed-node-ids="dimmedNodeIds"
          :dimmed-edge-ids="dimmedEdgeIds"
          @node-clicked="handleNodeClicked"
        />
      </a-col>
      <a-col :span="8">
        <a-card title="路径摘要" size="small" />
      </a-col>
    </a-row>
  </div>
</template>
```

- [ ] **Step 5: Run the detail smoke test**

Run: `cd OneOPS-UI && node scripts/network-path-page-smoke.ts`
Expected: PASS with no output.

- [ ] **Step 6: Commit**

```bash
git -C OneOPS-UI add \
  src/views/topology/NetworkPathDetail.vue \
  src/views/topology/network-path/PathTopologyView.vue \
  src/views/topology/network-path/useNetworkPathDetail.ts \
  scripts/network-path-page-smoke.ts
git -C OneOPS-UI commit -m "feat: add network path detail topology view"
```

---

### Task 4: Build the Diagnostic Panel and Reuse Device Evidence / Probe Data

**Files:**
- Create: `OneOPS-UI/src/views/topology/network-path/PathDiagnosticPanel.vue`
- Modify: `OneOPS-UI/src/views/topology/netpath-evidence-helpers.ts`
- Modify: `OneOPS-UI/src/views/topology/NetworkPathDetail.vue`
- Modify: `OneOPS-UI/src/views/topology/network-path/useNetworkPathDetail.ts`
- Test: `OneOPS-UI/scripts/network-path-page-smoke.ts`

- [ ] **Step 1: Extend smoke coverage for diagnostic tabs**

```ts
for (const signal of ['节点证据', '连通性验证', '后续处理', '创建验证任务']) {
  if (!detail.includes(signal)) {
    throw new Error(`missing diagnostic signal: ${signal}`);
  }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd OneOPS-UI && node scripts/network-path-page-smoke.ts`
Expected: FAIL because the detail page lacks the diagnostic tabs.

- [ ] **Step 3: Rename evidence section titles to product copy**

```ts
// OneOPS-UI/src/views/topology/netpath-evidence-helpers.ts
const buildSection = (title: string, key: string, items?: unknown[]) =>
  items && items.length ? { key, title, items } : null;

const SECTION_TITLE_MAP: Record<string, string> = {
  route_lookups: '路由证据',
  forward_peers: '邻接证据',
  policy_steps: '策略证据',
  nat_steps: 'NAT 证据',
  pbr_steps: 'PBR 证据',
};
```

- [ ] **Step 4: Add the diagnostic panel component**

```vue
<!-- OneOPS-UI/src/views/topology/network-path/PathDiagnosticPanel.vue -->
<template>
  <a-card size="small">
    <a-tabs v-model:activeKey="activeTab">
      <a-tab-pane key="summary" tab="路径摘要" />
      <a-tab-pane key="evidence" tab="节点证据" />
      <a-tab-pane key="connectivity" tab="连通性验证" />
      <a-tab-pane key="actions" tab="后续处理" />
    </a-tabs>
    <a-alert v-if="selectedDeviceCode" type="info" :message="`${selectedDeviceCode} 位于当前路径中，可查看关联证据。`" />
    <a-button v-if="activeTab === 'actions'" type="primary">创建验证任务</a-button>
  </a-card>
</template>
```

- [ ] **Step 5: Reuse existing APIs for evidence and probe state**

```ts
// OneOPS-UI/src/views/topology/network-path/useNetworkPathDetail.ts
import {
  getNetPathAnalyzeRunDeviceEvidenceReq,
  getNetPathAnalyzeProbeExecutionReq,
  getNetPathAnalyzeWorkflowHandoffReq,
} from '@/api/netpath/netpath';

async function loadDeviceEvidence(deviceCode: string) {
  if (!activeRun.value) return;
  deviceEvidence.value = await getNetPathAnalyzeRunDeviceEvidenceReq({
    tenant_code: activeRun.value.tenant_code,
    code: activeRun.value.code,
    device_code: deviceCode,
  });
}
```

- [ ] **Step 6: Run the diagnostic smoke test**

Run: `cd OneOPS-UI && node scripts/network-path-page-smoke.ts`
Expected: PASS with no output.

- [ ] **Step 7: Commit**

```bash
git -C OneOPS-UI add \
  src/views/topology/NetworkPathDetail.vue \
  src/views/topology/network-path/PathDiagnosticPanel.vue \
  src/views/topology/network-path/useNetworkPathDetail.ts \
  src/views/topology/netpath-evidence-helpers.ts \
  scripts/network-path-page-smoke.ts
git -C OneOPS-UI commit -m "feat: add network path diagnostic panel"
```

---

### Task 5: Polish Product Copy, Replace Internal Terms, and Verify Build

**Files:**
- Modify: `OneOPS-UI/src/views/topology/NetworkPathIndex.vue`
- Modify: `OneOPS-UI/src/views/topology/NetworkPathDetail.vue`
- Modify: `OneOPS-UI/src/views/topology/network-path/copy.ts`
- Modify: `OneOPS-UI/src/router/utils.ts`
- Modify: `OneOPS-UI/package.json`
- Test: `OneOPS-UI/scripts/network-path-route-smoke.ts`
- Test: `OneOPS-UI/scripts/network-path-page-smoke.ts`

- [ ] **Step 1: Add a failing copy scan**

```bash
cd OneOPS-UI
rg -n "NetPath|MVP|工作台|demo|handoff|draft" \
  src/views/topology/NetworkPathIndex.vue \
  src/views/topology/NetworkPathDetail.vue \
  src/views/topology/network-path \
  src/router/utils.ts
```

Expected: FAIL with one or more old terms still present.

- [ ] **Step 2: Replace internal copy with product copy**

```ts
// OneOPS-UI/src/views/topology/network-path/copy.ts
export const NETWORK_PATH_COPY = {
  indexTitle: '网络路径',
  indexSubtitle: '面向网络运维的访问路径查询与故障定位，统一查看路径、转发证据与连通性验证。',
  detailTitle: '路径详情',
  resultSummaryReachable: '已识别 1 条主路径，当前访问可达。',
  resultSummaryAbnormal: '已识别 1 条主路径，存在异常证据，建议查看路径详情。',
} as const;
```

```json
// OneOPS-UI/package.json
{
  "scripts": {
    "smoke:network-path-route": "node scripts/network-path-route-smoke.ts",
    "smoke:network-path-page": "node scripts/network-path-page-smoke.ts"
  }
}
```

- [ ] **Step 3: Run smoke tests and build verification**

Run: `cd OneOPS-UI && npm run smoke:network-path-route && npm run smoke:network-path-page && npm run typecheck && npm run build`
Expected:
- route smoke: PASS
- page smoke: PASS
- `vue-tsc` exits 0
- `vite build` completes successfully

- [ ] **Step 4: Commit**

```bash
git -C OneOPS-UI add \
  src/views/topology/NetworkPathIndex.vue \
  src/views/topology/NetworkPathDetail.vue \
  src/views/topology/network-path/copy.ts \
  src/router/utils.ts \
  package.json \
  scripts/network-path-route-smoke.ts \
  scripts/network-path-page-smoke.ts
git -C OneOPS-UI commit -m "feat: polish network path product copy"
```

---

## Self-Review

### Spec coverage

- Query entry under `拓扑中心 / 网络路径`: covered by Tasks 1 and 2.
- Split query page and detail page: covered by Tasks 1 through 3.
- Real topology projection with current nodes like `debian -> R10 -> SW69 -> RT12 -> ubuntu`: covered by Task 3.
- Node evidence, connectivity validation, and follow-up actions in one detail page: covered by Task 4.
- Product copy with no `NetPath` / `MVP` / `工作台` / `demo`: covered by Task 5.

### Placeholder scan

- No `TODO`, `TBD`, or “implement later” placeholders remain.
- Each task lists exact files and concrete commands.
- Each code step includes literal file content or literal command text.

### Type consistency

- Route page names are consistently `NetworkPathIndex` and `NetworkPathDetail`.
- Shared copy module is consistently `NETWORK_PATH_COPY`.
- Shared detail tabs are consistently `summary`, `evidence`, `connectivity`, `actions`.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-21-oneops-network-path-frontend-plan.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
