# Device Discovery Drawer Frontend Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有设备清单页新增 `设备探测` 抽屉，基于当前数据库中已加载的设备数据生成探测计划、执行记录和待入库设备，并把结果回流到设备清单继续做采集与监控。

**Architecture:** 保持 `DeviceV2ManagementGrouped.vue` 作为主页面容器，新增一个独立的 `DeviceDiscoveryDrawer` 子组件承载交互，并新增一个纯前端数据模块负责从当前设备数据派生探测计划与结果。主页面只负责入口、状态挂接和回流，不改动现有采集/监控流程。

**Tech Stack:** Vue 3 `<script setup>`, TypeScript, Ant Design Vue, existing device-v2 page state, source-based smoke script.

---

### Task 1: 锁定入口与抽屉契约

**Files:**
- Create: `OneOPS-UI/scripts/device-discovery-drawer-smoke.ts`
- Modify: `OneOPS-UI/package.json`
- Test: `OneOPS-UI/scripts/device-discovery-drawer-smoke.ts`

- [ ] **Step 1: 写失败的 smoke 断言**

```ts
assert(pageSource.includes('设备探测'), 'missing discovery entry button');
assert(pageSource.includes('DeviceDiscoveryDrawer'), 'missing discovery drawer component');
assert(drawerSource.includes('计划详情'), 'missing discovery detail tab');
assert(drawerSource.includes('待入库设备'), 'missing pending inventory tab');
```

- [ ] **Step 2: 运行 smoke，确认按预期失败**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run smoke:device-discovery-drawer`
Expected: FAIL，因为入口和组件都还不存在。

- [ ] **Step 3: 在 package.json 注册 smoke 命令**

```json
"smoke:device-discovery-drawer": "npx esbuild scripts/device-discovery-drawer-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/device-discovery-drawer-smoke.mjs >/dev/null && node .tmp/device-discovery-drawer-smoke.mjs"
```

### Task 2: 抽离探测状态与派生数据

**Files:**
- Create: `OneOPS-UI/src/views/device/device-discovery-workbench.ts`
- Test: `OneOPS-UI/scripts/device-discovery-drawer-smoke.ts`

- [ ] **Step 1: 定义计划、执行记录、待入库设备类型**

```ts
export type DiscoveryPlanType = 'subnet' | 'seed';
export type DiscoveryExecutionStatus = 'idle' | 'queued' | 'probing' | 'identifying' | 'completed';

export interface DiscoveryPlanRecord {
  id: string;
  type: DiscoveryPlanType;
  name: string;
  region: string;
  enabled: boolean;
  subnetTargets: string[];
  seedDeviceCodes: string[];
  snmpProfile: string;
  schedule: string;
  lastRunAt: string;
  lastDiscoveredCount: number;
}
```

- [ ] **Step 2: 基于当前设备数据生成默认计划与候选结果**

```ts
export function buildDiscoveryWorkbench(devices: DeviceV2Item[]) {
  return {
    plans: buildDefaultPlans(devices),
    executionHistory: [],
    pendingDevices: [],
  };
}
```

- [ ] **Step 3: 提供执行模拟与回流方法**

```ts
export function simulateDiscoveryExecution(plan: DiscoveryPlanRecord, devices: DeviceV2Item[]) {
  return {
    historyRecord: ...,
    pendingDevices: ...,
  };
}
```

### Task 3: 新建设备探测抽屉组件

**Files:**
- Create: `OneOPS-UI/src/views/device/components/DeviceDiscoveryDrawer.vue`
- Test: `OneOPS-UI/scripts/device-discovery-drawer-smoke.ts`

- [ ] **Step 1: 先写出抽屉骨架**

```vue
<a-drawer :open="open" title="设备探测" width="1120" placement="right">
  <div class="device-discovery">
    <aside class="device-discovery__plans">...</aside>
    <section class="device-discovery__detail">...</section>
  </div>
</a-drawer>
```

- [ ] **Step 2: 完成右侧摘要卡与页签**

```vue
<a-tabs v-model:activeKey="activeTab">
  <a-tab-pane key="detail" tab="计划详情" />
  <a-tab-pane key="history" tab="执行记录" />
  <a-tab-pane key="pending" tab="待入库设备" />
</a-tabs>
```

- [ ] **Step 3: 补齐计划编辑与立即执行按钮**

```vue
<a-button type="primary" :loading="running" @click="handleRunNow">立即执行</a-button>
<a-button @click="handleSavePlan">保存计划</a-button>
```

- [ ] **Step 4: 在待入库页签中提供入清单动作**

```vue
<a-button size="small" type="primary" @click="emit('ingest-pending-device', record.id)">入设备清单</a-button>
```

### Task 4: 在设备清单页接入入口与结果回流

**Files:**
- Modify: `OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue`
- Modify: `OneOPS-UI/src/views/device/components/DeviceDiscoveryDrawer.vue`
- Modify: `OneOPS-UI/src/views/device/device-discovery-workbench.ts`
- Test: `OneOPS-UI/scripts/device-discovery-drawer-smoke.ts`

- [ ] **Step 1: 增加入口按钮与打开状态**

```vue
<a-button @click="discoveryDrawerOpen = true">设备探测</a-button>
```

- [ ] **Step 2: 把 sourceDevices 传给抽屉**

```vue
<DeviceDiscoveryDrawer
  v-model:open="discoveryDrawerOpen"
  :devices="sourceDevices"
  :existing-codes="allRows.map(row => row.code)"
  @ingest-pending-device="ingestDiscoveredDevice"
/>
```

- [ ] **Step 3: 将新发现设备合并到设备清单数据源**

```ts
const discoveredInventoryDevices = ref<DeviceV2Item[]>([]);
const sourceDevicesForList = computed(() => [...discoveredInventoryDevices.value, ...sourceDevices.value]);
```

- [ ] **Step 4: 用新的合并数据源替换列表映射**

```ts
const allRows = computed(() => sourceDevicesForList.value.map(mapDeviceRow));
```

- [ ] **Step 5: 调整摘要文案，体现探测来源**

```ts
const discoveredCount = discoveredInventoryDevices.value.length;
```

### Task 5: 验证与收口

**Files:**
- Modify: `OneOPS-UI/package.json`
- Modify: `OneOPS-UI/scripts/device-discovery-drawer-smoke.ts`
- Test: `OneOPS-UI/scripts/device-discovery-drawer-smoke.ts`

- [ ] **Step 1: 跑新的 smoke**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run smoke:device-discovery-drawer`
Expected: PASS

- [ ] **Step 2: 跑既有设备清单相关 smoke**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run smoke:unified-monitoring-ops`
Expected: PASS

- [ ] **Step 3: 做 scoped type check**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npx vue-tsc --noEmit --skipLibCheck 2>&1 | rg "DeviceV2ManagementGrouped|DeviceDiscoveryDrawer|device-discovery-workbench|device-discovery-drawer-smoke"`
Expected: no output for touched files
