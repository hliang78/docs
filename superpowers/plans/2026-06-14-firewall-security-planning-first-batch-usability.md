# Firewall Security Planning First-Batch Usability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the first batch of low-risk usability improvements for the firewall `SecurityPlanning` page without changing backend contracts or core workflow behavior.

**Architecture:** Keep the current page structure, state machine, and backend API usage unchanged. Extract the new copy and hint rules into a small planning-only helper module, wire those strings into `SecurityPlanning.vue` and `SecurityPlanningNodeBaselineTab.vue`, and verify the new behavior with a focused smoke script plus existing type checks.

**Tech Stack:** Vue 3 SFCs, Ant Design Vue, TypeScript, Vite, existing `esbuild`-based smoke scripts.

---

## File Structure

**Create:**

- `OneOPS-UI/src/views/firewall/components/planning/firewallPlanningUsabilityCopy.ts`
  - Pure helper module for first-batch copy and hint rules.
- `OneOPS-UI/scripts/firewall-security-planning-usability-smoke.ts`
  - Smoke coverage for helper output and source wiring.

**Modify:**

- `OneOPS-UI/package.json`
  - Add a dedicated `smoke:firewall-security-planning-usability` script.
- `OneOPS-UI/src/views/firewall/SecurityPlanning.vue`
  - Replace hard-coded node column titles for the five target status columns.
  - Route `continue` hint copy through the new helper.
  - Expose node-to-connection and workbench summary helper props to the child component.
- `OneOPS-UI/src/views/firewall/components/planning/SecurityPlanningNodeBaselineTab.vue`
  - Add explicit tooltips for `设为当前节点` and both `进入连接规划` entry points.
  - Render a compact current-workbench summary under the node header.

**Validation:**

- `cd OneOPS-UI && npm run smoke:firewall-security-planning-usability`
- `cd OneOPS-UI && npm run typecheck`

## Task 1: Add the first-batch copy helper and smoke harness

**Files:**

- Create: `OneOPS-UI/src/views/firewall/components/planning/firewallPlanningUsabilityCopy.ts`
- Create: `OneOPS-UI/scripts/firewall-security-planning-usability-smoke.ts`
- Modify: `OneOPS-UI/package.json`

- [ ] **Step 1: Write the failing smoke script and npm command**

Add the smoke script first so the repo has an executable red test before any feature code lands.

```ts
// OneOPS-UI/scripts/firewall-security-planning-usability-smoke.ts
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {
  buildConnectionPlanningEntryHint,
  buildCurrentNodeWorkbenchSummaryLines,
  buildFirewallContinueActionHint,
  firewallPlanningNodeColumnTitles,
} from '../src/views/firewall/components/planning/firewallPlanningUsabilityCopy';

const cwd = process.cwd();
const readSource = (relativePath: string) =>
  fs.readFileSync(path.resolve(cwd, relativePath), 'utf8');

assert.equal(firewallPlanningNodeColumnTitles.business_status, '总体阶段');
assert.equal(firewallPlanningNodeColumnTitles.pending_reason, '建议下一步');
assert.equal(firewallPlanningNodeColumnTitles.config_fact_snapshot_summary, '配置事实');
assert.equal(firewallPlanningNodeColumnTitles.readiness_check, '初检结果');
assert.equal(firewallPlanningNodeColumnTitles.edit_lock_status, '修改条件');

assert.match(
  buildFirewallContinueActionHint('zone-mapping'),
  /当前缺的是接口与安全区域对应关系/,
);
assert.match(
  buildConnectionPlanningEntryHint('workbench'),
  /当前问题已经超出单节点映射/,
);

const summaryLines = buildCurrentNodeWorkbenchSummaryLines({
  nodeName: 'FW-01',
  nextActionLabel: '补齐区域映射',
});
assert.deepEqual(summaryLines, [
  '当前正在处理：FW-01 的接口与安全区域对应关系。',
  '如果现有区域无法承接，再查看当前机房安全区域或进入连接规划。',
]);

const nodeBaselineSource = readSource(
  'src/views/firewall/components/planning/SecurityPlanningNodeBaselineTab.vue',
);
assert.match(nodeBaselineSource, /resolveConnectionPlanningEntryHint/);
assert.match(nodeBaselineSource, /resolveCurrentNodeWorkbenchSummary/);

const planningSource = readSource('src/views/firewall/SecurityPlanning.vue');
assert.match(planningSource, /firewallPlanningNodeColumnTitles/);
assert.match(planningSource, /buildFirewallContinueActionHint/);

console.log('firewall-security-planning-usability smoke passed');
```

```json
// OneOPS-UI/package.json
{
  "scripts": {
    "smoke:firewall-security-planning-usability": "npx esbuild scripts/firewall-security-planning-usability-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/firewall-security-planning-usability-smoke.mjs >/dev/null && node .tmp/firewall-security-planning-usability-smoke.mjs"
  }
}
```

- [ ] **Step 2: Run the smoke script to verify it fails**

Run:

```bash
cd OneOPS-UI && npm run smoke:firewall-security-planning-usability
```

Expected:

- `FAIL`
- Error similar to `Cannot find module '../src/views/firewall/components/planning/firewallPlanningUsabilityCopy'`

- [ ] **Step 3: Add the helper module with the smallest useful API**

Create the helper module with pure strings only. Do not move component logic into it yet.

```ts
// OneOPS-UI/src/views/firewall/components/planning/firewallPlanningUsabilityCopy.ts
export type FirewallPlanningNextActionKey =
  | 'config-access'
  | 'unlock'
  | 'readiness-check'
  | 'zone-mapping'
  | 'management-habit';

export const firewallPlanningNodeColumnTitles = {
  business_status: '总体阶段',
  pending_reason: '建议下一步',
  config_fact_snapshot_summary: '配置事实',
  readiness_check: '初检结果',
  edit_lock_status: '修改条件',
} as const;

export const buildFirewallContinueActionHint = (action: FirewallPlanningNextActionKey) => {
  switch (action) {
    case 'config-access':
      return '当前缺的是配置事实，请先完成配置接入。';
    case 'unlock':
      return '当前节点已锁定，如需继续修订，请先解锁。';
    case 'readiness-check':
      return '当前需要先做初检，确认配置事实和区域条件是否闭环。';
    case 'zone-mapping':
      return '当前缺的是接口与安全区域对应关系，请先补齐区域映射。';
    case 'management-habit':
    default:
      return '当前映射已基本闭环，下一步进入策略生成规则确认。';
  }
};

export const buildConnectionPlanningEntryHint = (source: 'list' | 'workbench') => {
  if (source === 'workbench') {
    return '当前问题已经超出单节点映射，适合去连接规划判断区域关系和连接关系。';
  }
  return '当单节点状态不足以解释问题时，可进入连接规划继续判断更高层的区域关系。';
};

export const buildCurrentNodeWorkbenchSummaryLines = (options: {
  nodeName?: string;
  nextActionLabel?: string;
}) => {
  const nodeName = String(options.nodeName || '当前节点').trim() || '当前节点';
  const nextActionLabel = String(options.nextActionLabel || '补齐区域映射').trim() || '补齐区域映射';
  return [
    `当前正在处理：${nodeName} 的接口与安全区域对应关系。`,
    nextActionLabel === '补齐区域映射'
      ? '如果现有区域无法承接，再查看当前机房安全区域或进入连接规划。'
      : `当前建议动作：${nextActionLabel}。`,
  ];
};
```

- [ ] **Step 4: Run the smoke script to verify it passes**

Run:

```bash
cd OneOPS-UI && npm run smoke:firewall-security-planning-usability
```

Expected:

- `PASS`
- Output contains `firewall-security-planning-usability smoke passed`

- [ ] **Step 5: Commit**

```bash
git add OneOPS-UI/package.json \
  OneOPS-UI/scripts/firewall-security-planning-usability-smoke.ts \
  OneOPS-UI/src/views/firewall/components/planning/firewallPlanningUsabilityCopy.ts
git commit -m "test: add firewall planning usability smoke harness"
```

## Task 2: Rewire the parent page copy and node-column titles

**Files:**

- Modify: `OneOPS-UI/src/views/firewall/SecurityPlanning.vue:1949-2042`
- Modify: `OneOPS-UI/src/views/firewall/SecurityPlanning.vue:2504-2520`
- Test: `OneOPS-UI/scripts/firewall-security-planning-usability-smoke.ts`

- [ ] **Step 1: Extend the smoke script so parent wiring must exist**

Update the smoke script assertions so it fails until the parent imports and uses the helper.

```ts
// append inside OneOPS-UI/scripts/firewall-security-planning-usability-smoke.ts
assert.match(
  planningSource,
  /title: firewallPlanningNodeColumnTitles\.business_status/,
);
assert.match(
  planningSource,
  /title: firewallPlanningNodeColumnTitles\.pending_reason/,
);
assert.match(
  planningSource,
  /return buildFirewallContinueActionHint\(resolveFirewallNodeNextAction\(record\)\)/,
);
```

- [ ] **Step 2: Run the smoke script to verify it fails**

Run:

```bash
cd OneOPS-UI && npm run smoke:firewall-security-planning-usability
```

Expected:

- `FAIL`
- Regex assertion failure pointing to missing helper wiring in `SecurityPlanning.vue`

- [ ] **Step 3: Update `SecurityPlanning.vue` to use the helper**

Add the helper import, swap the five column titles, and route the continue hint through the helper.

```ts
// import section in OneOPS-UI/src/views/firewall/SecurityPlanning.vue
import {
  buildConnectionPlanningEntryHint,
  buildCurrentNodeWorkbenchSummaryLines,
  buildFirewallContinueActionHint,
  firewallPlanningNodeColumnTitles,
} from './components/planning/firewallPlanningUsabilityCopy';
```

```ts
// replace inside resolveContinueNodeSetupHint in OneOPS-UI/src/views/firewall/SecurityPlanning.vue
const resolveContinueNodeSetupHint = (record: FirewallNode) => {
  return buildFirewallContinueActionHint(resolveFirewallNodeNextAction(record));
};

const resolveConnectionPlanningEntryHint = (_record: FirewallNode, source: 'list' | 'workbench') => {
  return buildConnectionPlanningEntryHint(source);
};

const resolveCurrentNodeWorkbenchSummary = (record: FirewallNode) => {
  return buildCurrentNodeWorkbenchSummaryLines({
    nodeName: record.name || record.code || record.id || '当前节点',
    nextActionLabel: resolveFirewallNodePendingReason(record).replace(/^下一步[：:]\s*/, ''),
  });
};
```

```ts
// replace the five target titles in firewallNodeColumns in OneOPS-UI/src/views/firewall/SecurityPlanning.vue
const firewallNodeColumns = [
  { title: '节点名称', dataIndex: 'name', key: 'name', width: 280, fixed: 'left' },
  { title: '节点编码', dataIndex: 'code', key: 'code', width: 150, ellipsis: true },
  { title: 'IP地址', dataIndex: 'ip', key: 'ip', width: 132 },
  { title: '防火墙平台', dataIndex: 'platform', key: 'platform', width: 116 },
  { title: 'VSYS/VRF', dataIndex: 'firewall_vsys_source', key: 'firewall_vsys_source', width: 220, ellipsis: true },
  { title: '关联机房', dataIndex: 'datacenter_name', key: 'datacenter_name', width: 140, ellipsis: true },
  { title: firewallPlanningNodeColumnTitles.business_status, dataIndex: 'business_status', key: 'business_status', width: 120 },
  { title: firewallPlanningNodeColumnTitles.pending_reason, dataIndex: 'pending_reason', key: 'pending_reason', width: 136 },
  { title: firewallPlanningNodeColumnTitles.config_fact_snapshot_summary, dataIndex: 'config_fact_snapshot_summary', key: 'config_fact_snapshot_summary', width: 120 },
  { title: '配置格式', dataIndex: 'config_text_format', key: 'config_text_format', width: 100, align: 'center' },
  { title: '配置更新时间', dataIndex: 'config_text_updated_at', key: 'config_text_updated_at', width: 172 },
  { title: firewallPlanningNodeColumnTitles.readiness_check, dataIndex: 'readiness_check', key: 'readiness_check', width: 190 },
  { title: firewallPlanningNodeColumnTitles.edit_lock_status, dataIndex: 'edit_lock_status', key: 'edit_lock_status', width: 190 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 172 },
  { title: '操作', key: 'action', width: 360, fixed: 'right' },
];
```

```vue
<!-- pass new props into SecurityPlanningNodeBaselineTab in OneOPS-UI/src/views/firewall/SecurityPlanning.vue -->
:resolve-connection-planning-entry-hint="resolveConnectionPlanningEntryHint"
:resolve-current-node-workbench-summary="resolveCurrentNodeWorkbenchSummary"
```

- [ ] **Step 4: Run the smoke script and typecheck**

Run:

```bash
cd OneOPS-UI && npm run smoke:firewall-security-planning-usability
cd OneOPS-UI && npm run typecheck
```

Expected:

- Smoke prints `firewall-security-planning-usability smoke passed`
- `typecheck` exits `0`

- [ ] **Step 5: Commit**

```bash
git add OneOPS-UI/src/views/firewall/SecurityPlanning.vue \
  OneOPS-UI/scripts/firewall-security-planning-usability-smoke.ts
git commit -m "feat: clarify firewall planning node-stage copy"
```

## Task 3: Add workbench summary and connection-planning hints in the child component

**Files:**

- Modify: `OneOPS-UI/src/views/firewall/components/planning/SecurityPlanningNodeBaselineTab.vue:164-290`
- Modify: `OneOPS-UI/src/views/firewall/components/planning/SecurityPlanningNodeBaselineTab.vue:399-580`
- Test: `OneOPS-UI/scripts/firewall-security-planning-usability-smoke.ts`

- [ ] **Step 1: Extend the smoke script so child rendering must exist**

Add assertions for the new props, tooltips, and summary loop before modifying the component.

```ts
// append inside OneOPS-UI/scripts/firewall-security-planning-usability-smoke.ts
assert.match(
  nodeBaselineSource,
  /resolveConnectionPlanningEntryHint: \(record: FirewallNode, source: 'list' \| 'workbench'\) => string/,
);
assert.match(
  nodeBaselineSource,
  /resolveCurrentNodeWorkbenchSummary: \(record: FirewallNode\) => string\[\]/,
);
assert.match(
  nodeBaselineSource,
  /<a-tooltip :title="resolveConnectionPlanningEntryHint\(\(record as FirewallNode\), 'list'\)">/,
);
assert.match(
  nodeBaselineSource,
  /<a-tooltip :title="resolveConnectionPlanningEntryHint\(selectedFirewallNode, 'workbench'\)">/,
);
assert.match(
  nodeBaselineSource,
  /v-for="summary in resolveCurrentNodeWorkbenchSummary\(selectedFirewallNode\)"/,
);
```

- [ ] **Step 2: Run the smoke script to verify it fails**

Run:

```bash
cd OneOPS-UI && npm run smoke:firewall-security-planning-usability
```

Expected:

- `FAIL`
- Regex assertion failure for missing child props or tooltip wiring

- [ ] **Step 3: Update `SecurityPlanningNodeBaselineTab.vue`**

Add the two new props, wrap both connection-planning entry points with tooltips, add a small current-workbench summary block, and add a short tooltip for `设为当前节点`.

```ts
// extend defineProps in OneOPS-UI/src/views/firewall/components/planning/SecurityPlanningNodeBaselineTab.vue
resolveConnectionPlanningEntryHint: (record: FirewallNode, source: 'list' | 'workbench') => string;
resolveCurrentNodeWorkbenchSummary: (record: FirewallNode) => string[];
```

```vue
<!-- row-level actions in OneOPS-UI/src/views/firewall/components/planning/SecurityPlanningNodeBaselineTab.vue -->
<a-tooltip title="切到当前节点办理视角，并滚动到下方区域映射工作台。">
  <a-button
    size="small"
    :disabled="selectedFirewallNode?.id === (record as FirewallNode).id"
    @click="handleSelectFirewallNode(record as FirewallNode)"
  >
    {{ selectedFirewallNode?.id === (record as FirewallNode).id ? '当前节点' : '设为当前节点' }}
  </a-button>
</a-tooltip>
```

```vue
<!-- more-menu connection-planning entry -->
<a-menu-item>
  <a-tooltip :title="resolveConnectionPlanningEntryHint((record as FirewallNode), 'list')">
    <a @click="openConnectionPlanning(record as FirewallNode)">进入连接规划</a>
  </a-tooltip>
</a-menu-item>
```

```vue
<!-- current node workbench header -->
<div style="color: #666; font-size: 12px">
  {{ resolveFirewallNodeManagementHabitSummary(selectedFirewallNode) }}
</div>
<div
  v-for="summary in resolveCurrentNodeWorkbenchSummary(selectedFirewallNode)"
  :key="summary"
  class="node-workbench-summary"
>
  {{ summary }}
</div>
```

```vue
<!-- current node workbench connection-planning button -->
<a-tooltip :title="resolveConnectionPlanningEntryHint(selectedFirewallNode, 'workbench')">
  <a-button @click="openConnectionPlanning(selectedFirewallNode)">进入连接规划</a-button>
</a-tooltip>
```

```less
/* style block in OneOPS-UI/src/views/firewall/components/planning/SecurityPlanningNodeBaselineTab.vue */
.node-workbench-summary {
  color: #64748b;
  font-size: 12px;
  line-height: 1.6;
}
```

- [ ] **Step 4: Run the smoke script and typecheck**

Run:

```bash
cd OneOPS-UI && npm run smoke:firewall-security-planning-usability
cd OneOPS-UI && npm run typecheck
```

Expected:

- Smoke prints `firewall-security-planning-usability smoke passed`
- `typecheck` exits `0`

- [ ] **Step 5: Commit**

```bash
git add OneOPS-UI/src/views/firewall/components/planning/SecurityPlanningNodeBaselineTab.vue \
  OneOPS-UI/scripts/firewall-security-planning-usability-smoke.ts
git commit -m "feat: add firewall planning workbench guidance"
```

## Task 4: Final verification and implementation evidence check

**Files:**

- Test: `OneOPS-UI/scripts/firewall-security-planning-usability-smoke.ts`
- Test: `OneOPS-UI/src/views/firewall/SecurityPlanning.vue`
- Test: `OneOPS-UI/src/views/firewall/components/planning/SecurityPlanningNodeBaselineTab.vue`

- [ ] **Step 1: Run the target smoke script one final time**

Run:

```bash
cd OneOPS-UI && npm run smoke:firewall-security-planning-usability
```

Expected:

- `PASS`
- Output contains `firewall-security-planning-usability smoke passed`

- [ ] **Step 2: Run the existing firewall planning smoke coverage**

Run:

```bash
cd OneOPS-UI && npm run smoke:firewall-mapping-unmatched
cd OneOPS-UI && npm run smoke:firewall-object-management
```

Expected:

- Both commands `PASS`
- No regressions in nearby firewall helper logic

- [ ] **Step 3: Run full frontend type checking**

Run:

```bash
cd OneOPS-UI && npm run typecheck
```

Expected:

- Exit code `0`
- No new TypeScript errors from prop additions or helper imports

- [ ] **Step 4: Review the changed UI areas in code before merge**

Confirm these exact surfaces changed and nothing larger:

```text
SecurityPlanning.vue:
- five node-table titles
- continue-action hint resolver
- two new props passed to SecurityPlanningNodeBaselineTab

SecurityPlanningNodeBaselineTab.vue:
- set-current tooltip
- connection-planning tooltips
- compact workbench summary
- small supporting style block
```

- [ ] **Step 5: Commit**

```bash
git add OneOPS-UI/package.json \
  OneOPS-UI/scripts/firewall-security-planning-usability-smoke.ts \
  OneOPS-UI/src/views/firewall/SecurityPlanning.vue \
  OneOPS-UI/src/views/firewall/components/planning/SecurityPlanningNodeBaselineTab.vue \
  OneOPS-UI/src/views/firewall/components/planning/firewallPlanningUsabilityCopy.ts
git commit -m "feat: improve firewall planning first-batch usability"
```

## Self-Review

### Spec coverage

- `F1-01` is covered by Task 2 column-title rewiring.
- `F1-02` is covered by Task 2 continue-action hint rewiring.
- `F1-03` is covered by Task 3 connection-planning tooltips.
- `F1-04` is covered by Task 3 workbench summary block.

No first-batch requirement is left without a task.

### Placeholder scan

- No `TODO`, `TBD`, or “implement later” placeholders remain.
- Each task names exact files, commands, and expected outputs.

### Type consistency

- Helper action type uses the same five action keys already present in `SecurityPlanning.vue`.
- Child props are added with explicit signatures that match the parent methods.
- Smoke script imports only the new pure helper module and reads SFCs as source text, matching existing repo smoke patterns.

