# Config Version Compare Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `版本对比` prefill the diff drawer from selected configuration queue rows.

**Architecture:** Add a pure helper that converts selected config rows into a compare intent. The Vue page consumes the intent and either opens the existing manual picker or immediately calls the existing center diff API with the resolved version ids.

**Tech Stack:** Vue 3 script setup, TypeScript, esbuild smoke scripts.

---

### Task 1: Selected Row Compare Intent

**Files:**
- Create: `OneOps-UI/src/views/device/config-management/versionCompareHelpers.ts`
- Create: `OneOps-UI/scripts/config-management-version-compare-smoke.ts`
- Modify: `OneOps-UI/src/views/device/DeviceConfigManagement.vue`

- [ ] **Step 1: Write the failing smoke test**

Create `scripts/config-management-version-compare-smoke.ts` with assertions for one selected row, two selected rows, and fallback to manual picker.

- [ ] **Step 2: Verify RED**

Run:

```bash
npx esbuild scripts/config-management-version-compare-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/config-management-version-compare-smoke.mjs >/dev/null && node .tmp/config-management-version-compare-smoke.mjs
```

Expected: FAIL because `versionCompareHelpers.ts` does not exist yet.

- [ ] **Step 3: Implement helper and page wiring**

Add `resolveConfigVersionCompareIntent(selectedRows)` and update `openCustomDiffDrawer()` to use it before loading the global version list.

- [ ] **Step 4: Verify GREEN**

Run the same smoke command. Expected: PASS with `config management version compare smoke passed`.

- [ ] **Step 5: Run existing diff drawer smoke**

Run:

```bash
npm run smoke:config-management-version-compare
npm run smoke:device-config-management-diff-drawer
```

Expected: both commands pass.
