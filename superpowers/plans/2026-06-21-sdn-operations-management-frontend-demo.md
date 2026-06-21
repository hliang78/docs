# SDN Operations Management Frontend Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing `设备管理 -> SDN控制器` page into a cluster-first SDN operations workbench with top summary and four task-oriented tabs.

**Architecture:** Keep the existing page, drawers, and request functions, then layer a workbench shell above them. Use real controller data when available, and curated fallback cluster/resource/alarm/config data for stable front-end demo behavior.

**Tech Stack:** Vue 3 `<script setup>`, TypeScript, Ant Design Vue, existing SDN controller APIs, source-based smoke validation.

---

### Task 1: Lock the SDN workbench structure with a failing smoke

**Files:**
- Create: `OneOPS-UI/scripts/sdn-ops-workbench-smoke.ts`
- Modify: `OneOPS-UI/package.json`
- Test: `OneOPS-UI/scripts/sdn-ops-workbench-smoke.ts`

- [ ] **Step 1: Write the failing smoke assertions**

```ts
assert(pageSource.includes('集群健康'), 'missing cluster summary metric');
assert(pageSource.includes('控制器集群'), 'missing cluster tab');
assert(pageSource.includes('SDN资源'), 'missing resource tab');
assert(pageSource.includes('配置下发'), 'missing config tab');
assert(pageSource.includes('网络告警'), 'missing alarm tab');
```

- [ ] **Step 2: Run smoke to verify it fails**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run smoke:sdn-ops-workbench`
Expected: FAIL because the new workbench labels are not in the page yet.

- [ ] **Step 3: Add the smoke command**

```json
"smoke:sdn-ops-workbench": "npx esbuild scripts/sdn-ops-workbench-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/sdn-ops-workbench-smoke.mjs >/dev/null && node .tmp/sdn-ops-workbench-smoke.mjs"
```

- [ ] **Step 4: Re-run and keep failure targeted**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run smoke:sdn-ops-workbench`
Expected: FAIL on missing workbench strings only.

### Task 2: Add the cluster-first shell and tabs

**Files:**
- Modify: `OneOPS-UI/src/views/device/SdnControllerManagement.vue`
- Test: `OneOPS-UI/scripts/sdn-ops-workbench-smoke.ts`

- [ ] **Step 1: Add derived workbench state**

```ts
const workbenchActiveTab = ref('cluster');
const clusterSummaryCards = computed(() => [...]);
const clusterNodeCards = computed(() => [...]);
const fallbackResourceRows = computed(() => [...]);
const fallbackAlarmRows = computed(() => [...]);
```

- [ ] **Step 2: Add top summary and node cards**

```vue
<section class="sdn-workbench-hero">
  <div v-for="card in clusterSummaryCards" :key="card.label" class="sdn-summary-card">...</div>
</section>
<section class="sdn-cluster-strip">
  <article v-for="node in clusterNodeCards" :key="node.id" class="sdn-node-card">...</article>
</section>
```

- [ ] **Step 3: Add the four tabs**

```vue
<a-tabs v-model:active-key="workbenchActiveTab">
  <a-tab-pane key="cluster" tab="控制器集群">...</a-tab-pane>
  <a-tab-pane key="resource" tab="SDN资源">...</a-tab-pane>
  <a-tab-pane key="config" tab="配置下发">...</a-tab-pane>
  <a-tab-pane key="alarm" tab="网络告警">...</a-tab-pane>
</a-tabs>
```

- [ ] **Step 4: Keep existing actions reusable inside the new shell**

```ts
function openClusterNodeAction(node: ClusterNodeCard, action: 'test' | 'sync' | 'diagnose') {
  const matched = controllerList.value.find(item => item.id === node.controllerId);
  if (!matched) return;
  if (action === 'test') testController(matched);
  if (action === 'sync') syncController(matched);
  if (action === 'diagnose') openDiagnoseDrawer(matched);
}
```

- [ ] **Step 5: Run smoke to verify it passes**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run smoke:sdn-ops-workbench`
Expected: PASS.

### Task 3: Verify the page remains usable

**Files:**
- Modify: `OneOPS-UI/src/views/device/SdnControllerManagement.vue`
- Test: `OneOPS-UI/scripts/sdn-ops-workbench-smoke.ts`

- [ ] **Step 1: Run scoped smoke**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run smoke:sdn-ops-workbench`
Expected: PASS.

- [ ] **Step 2: Run scoped typecheck evidence**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npx vue-tsc --noEmit --skipLibCheck`
Expected: either PASS or only the same unrelated pre-existing failures recorded before this task.

- [ ] **Step 3: Commit**

```bash
git -C /Users/huangliang/project/OneOPS-ALL/OneOPS-UI add package.json scripts/sdn-ops-workbench-smoke.ts src/views/device/SdnControllerManagement.vue
git -C /Users/huangliang/project/OneOPS-ALL/OneOPS-UI commit -m "feat: redesign sdn controller operations workbench"
```
