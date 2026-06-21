# Unified Monitoring Operations Frontend Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a front-end `统一监控运维` workbench page that turns the approved discovery-and-onboarding spec into a continuous operator journey.

**Architecture:** Add one new route and one new workbench view under `platform`, keep alert and topology pages unchanged, and drive the page with curated local discovery data plus router handoff to existing pages. The page stays self-contained so the demo remains stable even when backend discovery APIs are not available.

**Tech Stack:** Vue 3 `<script setup>`, TypeScript, Ant Design Vue, existing OneOPS router/menu system, simple source-based smoke scripts.

---

### Task 1: Lock the route and page contract

**Files:**
- Create: `OneOPS-UI/scripts/unified-monitoring-ops-smoke.ts`
- Modify: `OneOPS-UI/package.json`
- Test: `OneOPS-UI/scripts/unified-monitoring-ops-smoke.ts`

- [ ] **Step 1: Write the failing smoke script**

```ts
assert(routeSource.includes("name: 'UnifiedMonitoringOperations'"), 'missing UnifiedMonitoringOperations route');
assert(routeSource.includes("path: 'platform/unified-monitoring'"), 'missing unified monitoring route path');
assert(pageSource.includes('发起网段发现'), 'missing discovery entry');
assert(pageSource.includes('查看关联拓扑'), 'missing topology handoff');
```

- [ ] **Step 2: Run smoke to verify it fails**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run smoke:unified-monitoring-ops`
Expected: FAIL because route and page source do not exist yet.

- [ ] **Step 3: Add the smoke command**

```json
"smoke:unified-monitoring-ops": "npx esbuild scripts/unified-monitoring-ops-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/unified-monitoring-ops-smoke.mjs >/dev/null && node .tmp/unified-monitoring-ops-smoke.mjs"
```

- [ ] **Step 4: Re-run smoke and keep it failing for the right reason**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run smoke:unified-monitoring-ops`
Expected: FAIL on missing route or missing page source, not on script syntax.

### Task 2: Build the unified monitoring workbench

**Files:**
- Create: `OneOPS-UI/src/views/platform/UnifiedMonitoringOperations.vue`
- Create: `OneOPS-UI/src/views/platform/unified-monitoring-data.ts`
- Modify: `OneOPS-UI/src/router/utils.ts`
- Test: `OneOPS-UI/scripts/unified-monitoring-ops-smoke.ts`

- [ ] **Step 1: Add seeded operator data and UI helpers**

```ts
export type DiscoveryBlocker = '凭证缺失' | '疑似重复' | 'SNMP待验证' | '类型待识别' | '可直接入库';
export type DiscoverySource = '网段发现' | '邻居扩展';
export function buildUnifiedMonitoringSeedState() {
  return {
    activeMenu: 'device-discovery',
    discoveryTasks: [...],
    devices: [...],
  };
}
```

- [ ] **Step 2: Add the new route**

```ts
const unifiedMonitoringOperationsRoute: RouteRecordRaw = {
  path: 'platform/unified-monitoring',
  name: 'UnifiedMonitoringOperations',
  component: () => import('@/views/platform/UnifiedMonitoringOperations.vue'),
  meta: {
    title: '统一监控运维',
    requiresAuth: true,
    icon: 'DeploymentUnitOutlined',
  },
};
```

- [ ] **Step 3: Implement the workbench view**

```vue
<a-layout class="unified-monitoring-shell">
  <a-layout-sider width="208">...</a-layout-sider>
  <a-layout-content>
    <section v-if="activeMenu === 'device-discovery'">...</section>
  </a-layout-content>
</a-layout>
```

- [ ] **Step 4: Wire the core journey**

```ts
function handlePrimaryAction(device: DiscoveryDevice) {
  if (device.blocker === 'SNMP待验证' || device.blocker === '类型待识别') openProbeDrawer(device);
  else if (device.blocker === '凭证缺失') openCredentialDrawer(device);
  else if (device.blocker === '疑似重复') openDuplicateDrawer(device);
  else commitIngest(device.code);
}
```

- [ ] **Step 5: Run smoke to verify it passes**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run smoke:unified-monitoring-ops`
Expected: PASS.

### Task 3: Verify route integrity and page compile safety

**Files:**
- Modify: `OneOPS-UI/src/router/utils.ts`
- Modify: `OneOPS-UI/src/views/platform/UnifiedMonitoringOperations.vue`
- Test: `OneOPS-UI/package.json`

- [ ] **Step 1: Run scoped type safety**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npx vue-tsc --noEmit --skipLibCheck`
Expected: either PASS or only pre-existing unrelated failures already recorded before this task.

- [ ] **Step 2: Run route smoke again**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run smoke:unified-monitoring-ops`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git -C /Users/huangliang/project/OneOPS-ALL/OneOPS-UI add package.json scripts/unified-monitoring-ops-smoke.ts src/router/utils.ts src/views/platform/UnifiedMonitoringOperations.vue src/views/platform/unified-monitoring-data.ts
git -C /Users/huangliang/project/OneOPS-ALL/OneOPS-UI commit -m "feat: add unified monitoring operations workbench"
```
