# IPAM Overview Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first IPAM overview dashboard page that displays address planning, lifecycle, request, fact, audit, and pool utilization statistics.

**Architecture:** Add one focused Vue page that consumes the already-created IPAM statistics API wrappers. Keep data transformation helpers inside the page for the first version, avoiding new global state or reusable abstractions until more IPAM pages exist.

**Tech Stack:** Vue 3 `<script setup>`, TypeScript, Ant Design Vue, existing `QueryForm` and table patterns, existing `src/api/ipam/ipam_statistics.ts` API contract.

---

## File Structure

- Create `OneOPS-UI/src/views/ipam/IPAMOverview.vue`
  - Owns the overview page layout, filters, API calls, KPI cards, distribution panels, and pool utilization table.
- Optionally modify `OneOPS-UI/src/router/index.ts` or static menu config only if there is an obvious existing static route for IPAM views.
  - If route/menu ownership is unclear, do not modify routing in this plan.
- Do not modify backend files.
- Do not modify unrelated AIOps, Alert, Netpath, or existing IPAM list pages.

## Task 1: Create IPAM overview page shell

**Files:**
- Create: `OneOPS-UI/src/views/ipam/IPAMOverview.vue`

- [ ] **Step 1: Create page component with filter state and layout skeleton**

Create `src/views/ipam/IPAMOverview.vue` with this structure:

```vue
<template>
  <div class="ipam-overview page-container">
    <query-form :query="handleQuery" :query-state="queryState">
      <template #item="scope">
        <a-col :md="8" :sm="24" :xs="24">
          <a-form-item label="租户" name="tenant_code">
            <a-input v-model:value="queryState.tenant_code" placeholder="请输入租户编码" allow-clear />
          </a-form-item>
        </a-col>
        <a-col :md="8" :sm="24" :xs="24">
          <a-form-item label="区域" name="region_code">
            <a-input v-model:value="queryState.region_code" placeholder="请输入区域编码" allow-clear />
          </a-form-item>
        </a-col>
        <a-col :md="8" :sm="24" :xs="24">
          <a-form-item label="安全区域" name="zone_code">
            <a-input v-model:value="queryState.zone_code" placeholder="请输入安全区域编码" allow-clear />
          </a-form-item>
        </a-col>
        <a-col v-show="scope.expand" :md="8" :sm="24" :xs="24">
          <a-form-item label="平台 VRF" name="platform_vrf_code">
            <a-input v-model:value="queryState.platform_vrf_code" placeholder="请输入平台 VRF 编码" allow-clear />
          </a-form-item>
        </a-col>
        <a-col v-show="scope.expand" :md="8" :sm="24" :xs="24">
          <a-form-item label="网段" name="prefix_code">
            <a-input v-model:value="queryState.prefix_code" placeholder="请输入网段编码" allow-clear />
          </a-form-item>
        </a-col>
        <a-col v-show="scope.expand" :md="8" :sm="24" :xs="24">
          <a-form-item label="地址池" name="pool_code">
            <a-input v-model:value="queryState.pool_code" placeholder="请输入地址池编码" allow-clear />
          </a-form-item>
        </a-col>
        <a-col v-show="scope.expand" :md="8" :sm="24" :xs="24">
          <a-form-item label="IP版本" name="ip_version">
            <a-select v-model:value="queryState.ip_version" placeholder="请选择IP版本" allow-clear>
              <a-select-option :value="4">IPv4</a-select-option>
              <a-select-option :value="6">IPv6</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
      </template>
    </query-form>

    <a-spin :spinning="loading">
      <div class="overview-section">
        <a-empty v-if="loadError" :description="loadError" />
        <template v-else>
          <div class="metric-grid"></div>
          <div class="distribution-grid"></div>
          <div class="pool-table-section"></div>
        </template>
      </div>
    </a-spin>
  </div>
</template>

<script lang="ts" setup>
import { message } from 'ant-design-vue';
import { computed, onMounted, reactive, ref } from 'vue';
import {
  ipamStatisticsAuditReq,
  ipamStatisticsLifecycleReq,
  ipamStatisticsOverviewReq,
  ipamStatisticsPoolsReq,
} from '@/api/ipam/ipam_statistics';
import {
  IPAMAuditStatisticsResp,
  IPAMPoolStatisticsItem,
  IPAMPoolStatisticsResp,
  IPAMStatisticsOverviewResp,
  IPAMStatisticsReq,
  IPAMLifecycleStatisticsResp,
} from '@/typings';

const loading = ref(false);
const loadError = ref('');
const overview = ref<IPAMStatisticsOverviewResp | null>(null);
const lifecycle = ref<IPAMLifecycleStatisticsResp | null>(null);
const audit = ref<IPAMAuditStatisticsResp | null>(null);
const poolStatistics = ref<IPAMPoolStatisticsResp | null>(null);

const queryState = reactive<IPAMStatisticsReq>({
  tenant_code: '',
  region_code: '',
  zone_code: '',
  business_unit_code: '',
  platform_vrf_code: '',
  vrf_code: '',
  prefix_code: '',
  pool_code: '',
  ip_version: 0,
  start_at: null,
  end_at: null,
});

const buildReq = (): IPAMStatisticsReq => ({
  ...queryState,
  ip_version: Number(queryState.ip_version || 0),
});

const handleQuery = async () => {
  await loadStatistics();
};

const loadStatistics = async () => {
  loading.value = true;
  loadError.value = '';
  const req = buildReq();
  try {
    const [overviewResp, lifecycleResp, auditResp, poolResp] = await Promise.all([
      ipamStatisticsOverviewReq(req),
      ipamStatisticsLifecycleReq(req),
      ipamStatisticsAuditReq(req),
      ipamStatisticsPoolsReq(req),
    ]);
    overview.value = overviewResp;
    lifecycle.value = lifecycleResp;
    audit.value = auditResp;
    poolStatistics.value = poolResp;
  } catch (error) {
    const text = error instanceof Error ? error.message : 'IPAM统计加载失败';
    loadError.value = text;
    message.error(text);
  } finally {
    loading.value = false;
  }
};

onMounted(loadStatistics);
</script>
```

- [ ] **Step 2: Verify shell compiles**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npm run typecheck
```

Expected: Typecheck passes, or fails only on unrelated dirty files not touched by this task. If it fails due to `IPAMOverview.vue`, fix before continuing.

- [ ] **Step 3: Commit shell**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
git add src/views/ipam/IPAMOverview.vue
git commit -m "feat(ipam): add overview dashboard shell"
```

## Task 2: Add KPI cards and distribution panels

**Files:**
- Modify: `OneOPS-UI/src/views/ipam/IPAMOverview.vue`

- [ ] **Step 1: Add helper functions and computed metrics**

Add these helpers inside `<script setup>`:

```ts
const formatNumber = (value?: number) => Number(value || 0).toLocaleString();
const formatPercent = (value?: number) => `${Math.round(Number(value || 0) * 100)}%`;

const submittedRequestCount = computed(() => overview.value?.submitted_request_count || 0);
const metricCards = computed(() => [
  { title: '地址池', value: overview.value?.total_pool_count || 0, tone: 'neutral' },
  { title: '已规划地址', value: overview.value?.planned_address_count || 0, tone: 'neutral' },
  { title: '地址利用率', value: formatPercent(overview.value?.utilization_ratio), tone: 'primary' },
  { title: '未解决稽核', value: overview.value?.unresolved_audit_finding_count || 0, tone: 'risk' },
  { title: '现网事实', value: overview.value?.observed_fact_count || 0, tone: 'neutral' },
  { title: '待处理申请', value: submittedRequestCount.value, tone: 'warning' },
]);

const lifecycleItems = computed(() => lifecycle.value?.lifecycle_status_counts || overview.value?.lifecycle_counts || []);
const requestItems = computed(() => overview.value?.request_status_counts || []);
const severityItems = computed(() => audit.value?.severity_counts || []);
const findingTypeItems = computed(() => audit.value?.finding_type_counts || []);
```

- [ ] **Step 2: Render KPI cards**

Replace `<div class="metric-grid"></div>` with:

```vue
<div class="metric-grid">
  <a-card v-for="card in metricCards" :key="card.title" class="metric-card" :class="`metric-card--${card.tone}`">
    <div class="metric-title">{{ card.title }}</div>
    <div class="metric-value">{{ typeof card.value === 'number' ? formatNumber(card.value) : card.value }}</div>
  </a-card>
</div>
```

- [ ] **Step 3: Render distribution panels**

Replace `<div class="distribution-grid"></div>` with:

```vue
<div class="distribution-grid">
  <a-card title="生命周期分布">
    <div v-if="lifecycleItems.length" class="distribution-list">
      <div v-for="item in lifecycleItems" :key="item.name" class="distribution-row">
        <span>{{ item.name }}</span>
        <strong>{{ formatNumber(item.count) }}</strong>
      </div>
    </div>
    <a-empty v-else description="暂无生命周期数据" />
  </a-card>

  <a-card title="申请状态">
    <div v-if="requestItems.length" class="distribution-list">
      <div v-for="item in requestItems" :key="item.name" class="distribution-row">
        <span>{{ item.name }}</span>
        <strong>{{ formatNumber(item.count) }}</strong>
      </div>
    </div>
    <a-empty v-else description="暂无申请数据" />
  </a-card>

  <a-card title="稽核风险">
    <div class="audit-summary">
      <span>未解决</span>
      <strong>{{ formatNumber(audit?.unresolved_count || overview?.unresolved_audit_finding_count || 0) }}</strong>
    </div>
    <div v-if="severityItems.length" class="distribution-list compact">
      <div v-for="item in severityItems" :key="item.name" class="distribution-row">
        <span>{{ item.name }}</span>
        <strong>{{ formatNumber(item.count) }}</strong>
      </div>
    </div>
    <a-empty v-else description="暂无稽核数据" />
  </a-card>
</div>
```

- [ ] **Step 4: Add styles for cards and panels**

Append:

```vue
<style scoped>
.ipam-overview { min-height: 100%; }
.overview-section { display: flex; flex-direction: column; gap: 16px; }
.metric-grid { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 12px; }
.metric-card { border-radius: 12px; }
.metric-title { color: rgba(0, 0, 0, 0.55); font-size: 13px; }
.metric-value { margin-top: 8px; font-size: 26px; font-weight: 700; line-height: 1.2; }
.metric-card--primary .metric-value { color: #1677ff; }
.metric-card--warning .metric-value { color: #faad14; }
.metric-card--risk .metric-value { color: #cf1322; }
.distribution-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
.distribution-list { display: flex; flex-direction: column; gap: 10px; }
.distribution-list.compact { margin-top: 12px; }
.distribution-row { display: flex; align-items: center; justify-content: space-between; }
.audit-summary { display: flex; align-items: baseline; justify-content: space-between; padding: 10px 12px; border-radius: 10px; background: #fff1f0; color: #cf1322; }
.audit-summary strong { font-size: 24px; }
@media (max-width: 1200px) { .metric-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); } .distribution-grid { grid-template-columns: 1fr; } }
@media (max-width: 640px) { .metric-grid { grid-template-columns: 1fr; } }
</style>
```

- [ ] **Step 5: Verify**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npm run typecheck
```

Expected: Pass.

- [ ] **Step 6: Commit**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
git add src/views/ipam/IPAMOverview.vue
git commit -m "feat(ipam): render overview dashboard metrics"
```

## Task 3: Add pool utilization table

**Files:**
- Modify: `OneOPS-UI/src/views/ipam/IPAMOverview.vue`

- [ ] **Step 1: Add pool table computed data and columns**

Add inside `<script setup>`:

```ts
const sortedPools = computed<IPAMPoolStatisticsItem[]>(() => {
  return [...(poolStatistics.value?.list || [])].sort((a, b) => b.utilization_ratio - a.utilization_ratio);
});

const poolColumns = [
  { title: '地址池', dataIndex: 'pool_code', width: 140 },
  { title: '名称', dataIndex: 'pool_name', width: 160 },
  { title: '网段', dataIndex: 'prefix_code', width: 160 },
  { title: '租户', dataIndex: 'tenant_code', width: 120 },
  { title: '区域', dataIndex: 'region_code', width: 120 },
  { title: '安全区域', dataIndex: 'zone_code', width: 120 },
  { title: '平台 VRF', dataIndex: 'platform_vrf_code', width: 140 },
  { title: '版本', dataIndex: 'ip_version', width: 80 },
  { title: '规划', dataIndex: 'planned_count', width: 100 },
  { title: '已分配', dataIndex: 'assigned_count', width: 100 },
  { title: '已保留', dataIndex: 'reserved_count', width: 100 },
  { title: '可用', dataIndex: 'available_count', width: 100 },
  { title: '利用率', dataIndex: 'utilization_ratio', width: 160 },
];

const getUtilizationStatus = (value: number) => {
  if (value >= 0.95) return 'exception';
  if (value >= 0.8) return 'active';
  return 'normal';
};
```

- [ ] **Step 2: Render table**

Replace `<div class="pool-table-section"></div>` with:

```vue
<a-card class="pool-table-section" title="地址池利用率">
  <a-table
    row-key="pool_code"
    :columns="poolColumns"
    :data-source="sortedPools"
    :pagination="{ pageSize: 10, showSizeChanger: true }"
    size="middle"
    :scroll="{ x: 1400 }"
  >
    <template #bodyCell="{ column, record }">
      <template v-if="column.dataIndex === 'ip_version'">IPv{{ record.ip_version || '-' }}</template>
      <template v-else-if="column.dataIndex === 'utilization_ratio'">
        <div class="utilization-cell">
          <a-progress
            :percent="Math.round((record.utilization_ratio || 0) * 100)"
            :status="getUtilizationStatus(record.utilization_ratio || 0)"
            size="small"
          />
        </div>
      </template>
    </template>
  </a-table>
</a-card>
```

- [ ] **Step 3: Add small table style**

Append inside existing style block:

```css
.pool-table-section { border-radius: 12px; }
.utilization-cell { min-width: 130px; }
```

- [ ] **Step 4: Verify**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npm run typecheck
```

Expected: Pass.

- [ ] **Step 5: Commit**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
git add src/views/ipam/IPAMOverview.vue
git commit -m "feat(ipam): add pool utilization table"
```

## Task 4: Optional route exposure and final verification

**Files:**
- Inspect: `OneOPS-UI/src/router/index.ts`
- Possibly modify: only if static IPAM routes are defined in a clear local file.

- [ ] **Step 1: Inspect routing ownership**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
rg "IPAgg|Mac|views/ipam|ipam" src/router src/static -n
```

Expected: Identify whether IPAM routes are static frontend routes or backend-driven menu resources.

- [ ] **Step 2: Decide route change**

If no clear static route is present, do not modify routing. Document that page file is ready for menu integration.

If a clear static route exists, add this route entry using existing route conventions:

```ts
{
  path: '/ipam/overview',
  name: 'IPAMOverview',
  component: () => import('@/views/ipam/IPAMOverview.vue'),
  meta: { title: 'IPAM总览' },
}
```

Only use this code if it matches the actual route file structure.

- [ ] **Step 3: Final verification**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npm run typecheck
```

Expected: Pass.

- [ ] **Step 4: Commit route if changed**

If route changed:

```bash
git add src/router/index.ts
git commit -m "feat(ipam): expose overview dashboard route"
```

If route did not change, no commit is needed.
