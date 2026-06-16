# SNMP OID Online Test UI Tightening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refine the existing SNMP OID online-test page flow so the main editor lane naturally drives `target_part -> field test -> group test -> save`, with less visual competition from explanatory copy and side information.

**Architecture:** Keep the existing OID online-test backend and state model unchanged. This slice is a UI-only tightening pass inside the current SNMP editor components: compress the page-level task bar, keep field-level `测试` as the strongest local action, keep group-level `测试本组待测项` in the group header, and further de-emphasize left/right non-local information without introducing new pages or new workflows.

**Tech Stack:** Vue 3 + TypeScript in `/OneOPS/OneOps-UI`, existing Ant Design Vue components, SNMP editor components under `src/views/platform/StrategyTemplate/plugin-forms/snmp`, smoke scripts under `/OneOPS/OneOps-UI/scripts`, and docs under `/OneOPS/docs/superpowers`.

---

## Scope Lock

Allowed in this slice:

- tighten the page-level task bar in `PluginFormSnmp.vue`;
- reorder or restyle current group header actions in `SnmpMetricGroupEditor.vue`;
- reduce long guidance text in favor of short readiness labels;
- de-emphasize left/right information that competes with the OID edit-and-test loop;
- add or update smoke coverage for the tightened layout.

Not allowed in this slice:

- no backend changes;
- no changes to OID test request/response semantics;
- no new page, drawer, or modal;
- no full redesign of left/right side panels;
- no new recording-rule or Grafana workflow changes.

## File Structure

Frontend expected to change:

- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/PluginFormSnmp.vue`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/SnmpMetricGroupEditor.vue`
- Modify: `/OneOPS/OneOps-UI/scripts/snmp-oid-online-test-page-smoke.ts`
- Modify: `/OneOPS/OneOps-UI/scripts/snmp-oid-online-test-editor-smoke.ts`

Docs expected to change:

- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

## Canonical Decisions

These decisions are fixed for this plan:

- page-level task bar contains only `target_part`, one short readiness state, and the page-level save action;
- field-level `测试` remains the strongest local action;
- group-level `测试本组待测项` stays in the current group header, not the page-level task bar;
- readiness copy is compact: `先输入目标设备`, `待测试 N`, `当前分组已就绪`;
- left/right contextual information remains available but must not visually outrank the active editor lane.

## Task 1: Freeze The Refined UI Contract With Smokes

**Files:**

- Modify: `/OneOPS/OneOps-UI/scripts/snmp-oid-online-test-page-smoke.ts`
- Modify: `/OneOPS/OneOps-UI/scripts/snmp-oid-online-test-editor-smoke.ts`

- [ ] **Step 1: Add failing page-smoke assertions for the compact task bar**

Extend `snmp-oid-online-test-page-smoke.ts` so it verifies:

- `PluginFormSnmp.vue` no longer relies on long two-sentence task-hint copy;
- the page task bar exposes compact readiness labels;
- the page task bar does not include `测试本组待测项`.

Target assertions:

```ts
assert.ok(formSource.includes('先输入目标设备'));
assert.ok(formSource.includes('当前分组已就绪'));
assert.ok(!formSource.includes('填 OID 后先测试，再继续保存策略'));
assert.ok(!taskbarSource.includes('测试本组待测项'));
```

- [ ] **Step 2: Add failing editor-smoke assertions for group-header action order**

Extend `snmp-oid-online-test-editor-smoke.ts` so it verifies:

- the group header still owns `测试本组待测项`;
- the action appears alongside `新增字段` and `加载 MIB 字段`;
- field-level `测试` still exists inside the OID cell.

Target assertions:

```ts
assert.ok(editorSource.includes('新增字段'));
assert.ok(editorSource.includes('加载 MIB 字段'));
assert.ok(editorSource.includes('测试本组待测项'));
assert.ok(editorSource.includes("column.key === 'oid'"));
assert.ok(editorSource.includes('>\\n              测试\\n            </a-button>'));
```

- [ ] **Step 3: Run the focused smokes to verify RED**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-oid-online-test-page
npm run smoke:snmp-oid-online-test-editor
```

Expected: RED until the task bar copy/layout and group-header emphasis are tightened.

## Task 2: Tighten The Page-Level Task Bar

**Files:**

- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/PluginFormSnmp.vue`
- Modify: `/OneOPS/OneOps-UI/scripts/snmp-oid-online-test-page-smoke.ts`

- [ ] **Step 1: Replace long task-hint copy with compact readiness state**

In `PluginFormSnmp.vue`, replace the current long guidance copy with a compact computed state that renders exactly one of:

```ts
const oidTaskbarStatus = computed(() => {
  if (!targetPartForOidTest.value) return '先输入目标设备';
  return oidUntestedSummary.value || '当前分组已就绪';
});
```

Use that status in the task bar instead of the current sentence-style hint.

- [ ] **Step 2: Keep the task bar focused on target, status, and save context**

Adjust the task bar markup so the top bar presents:

- `target_part` input
- compact readiness tag
- existing page-level save context only

The task bar should not render group-scoped actions.

Target structure:

```vue
<div class="snmp-form__taskbar">
  <div class="snmp-form__taskactions">
    <a-input ... />
    <a-tag>{{ oidTaskbarStatus }}</a-tag>
  </div>
</div>
```

- [ ] **Step 3: Keep OID test errors compact and local**

Retain the page-level `oidOnlineTestError` alert only as a short warning line under the task bar.
Do not move field failures into a larger page-level explanation block.

- [ ] **Step 4: Run focused frontend verification for the task bar**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-oid-online-test-page
npm run smoke:snmp-workspace-view
npm run typecheck
```

Expected: PASS.

## Task 3: Keep Group-Level Actions Local To The Active Group

**Files:**

- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/SnmpMetricGroupEditor.vue`
- Modify: `/OneOPS/OneOps-UI/scripts/snmp-oid-online-test-editor-smoke.ts`

- [ ] **Step 1: Make the group header the local action bar**

In `SnmpMetricGroupEditor.vue`, preserve the header action cluster and keep this order:

```vue
<a-button :disabled="isDisabledGroup" @click="addBlankField">新增字段</a-button>
<a-button :loading="mibLoading" :disabled="!baseOid || isDisabledGroup" @click="loadMibFields">
  加载 MIB 字段
</a-button>
<a-button :loading="oidTestState?.loading.value" :disabled="!canRunGroupOidTest" @click="testGroupFields">
  测试本组待测项
</a-button>
```

The batch-test button stays here and does not move back to the page-level bar.

- [ ] **Step 2: Preserve field-level `测试` as the strongest local action**

Keep the OID cell structure stable:

```vue
<div class="snmp-group-editor__oid-cell">
  <a-input ... />
  <a-button
    size="small"
    :loading="fieldTestStatus(record.metric_key) === 'testing'"
    :disabled="!canRunOidTests"
    @click="testSingleField(record)"
  >
    测试
  </a-button>
  <a-tag :color="fieldTestMeta(record.metric_key).color">{{ fieldTestMeta(record.metric_key).label }}</a-tag>
</div>
```

Do not replace this with a more distant or more global action.

- [ ] **Step 3: Run focused editor verification**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-oid-online-test-editor
npm run smoke:snmp-oid-online-test-page
npm run typecheck
```

Expected: PASS.

## Task 4: De-Emphasize Non-Local Information Without Removing It

**Files:**

- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/PluginFormSnmp.vue`
- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [ ] **Step 1: Reduce left-column context density on first screen**

In `PluginFormSnmp.vue`, keep the left column but make the first screen favor:

- current strategy
- parent strategy
- inheritance state

Manufacturer, platform, and model should remain available, but the layout should not visually make them the page’s first priority.

- [ ] **Step 2: Keep right-column alerts secondary to the editor lane**

Do not remove the right-column alerts or dashboard preview.
Instead, keep their order and styling secondary so the active group editor remains the dominant workflow area.

Concrete guardrail:

- no new large warning block above the editor;
- no movement of dashboard preview into the center lane;
- no expansion of contract-source copy near the task bar.

- [ ] **Step 3: Update handoff with the tightened UI rule**

Add a short note to the handoff stating that the OID online-test entry has been further tightened so the page-level bar now emphasizes only `target_part`, compact readiness state, and save context, while batch test remains a current-group action.

- [ ] **Step 4: Run final verification and diff hygiene**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-oid-online-test-page
npm run smoke:snmp-oid-online-test-editor
npm run smoke:snmp-workspace-view
npm run typecheck
git -C /OneOPS/OneOps-UI diff --check
git -C /OneOPS/docs diff --check
```

Expected: PASS.

## Self-Review

Spec coverage:

- page-level task-bar tightening is covered in Task 2;
- field-vs-group action hierarchy is covered in Task 3;
- information de-emphasis is covered in Task 4;
- smoke expectations are covered in Task 1 plus per-task verification.

Placeholder scan:

- no `TODO` / `TBD` placeholders remain;
- every verification step includes exact commands.

Type consistency:

- keeps existing names such as `targetPartForOidTest`, `oidUntestedSummary`, `testGroupFields`, `testSingleField`, and `fieldTestStatus` rather than inventing parallel APIs.
