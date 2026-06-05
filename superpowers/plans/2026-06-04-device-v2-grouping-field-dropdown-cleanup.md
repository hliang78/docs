# Device V2 Grouping Field Dropdown Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce noise and duplicates in the Device V2 management page's grouping field dropdown.

**Architecture:** Keep the change local to `DeviceV2ManagementGrouped.vue` by filtering schema-derived grouping attribute candidates through a small allowlist and alias identity map. Verify with Playwright against the real page: open grouping editor, inspect the attribute dropdown, and assert common grouping fields remain while high-cardinality/rare fields disappear.

**Tech Stack:** Vue 3, Ant Design Vue, Playwright, TypeScript.

---

## Task 1: Add Failing E2E Coverage

**Files:**
- Create: `OneOps/scripts/platform2_multi_agent_test/agents/device_v2_grouping_fields.spec.ts`
- Modify: `OneOps/scripts/platform2_multi_agent_test/package.json`

- [x] Open `/device/device-v2-management`, enter grouping edit mode, open the first attribute dropdown.
- [x] Assert common grouping fields remain: 区域, 机房, 机架.
- [x] Assert noisy fields are absent: 设备名称, 序列号, 描述.
- [x] Assert alias duplicates are not simultaneously visible for 区域.
- [x] Run the spec before implementation and verify it fails on the current unfiltered dropdown.

## Task 2: Implement Dropdown Cleanup

**Files:**
- Modify: `OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue`

- [x] Add a grouping field allowlist keyed by canonical attribute identity.
- [x] Filter `groupingAttributeOptions` through the allowlist, while preserving currently saved/edited non-allowlisted keys so existing configs remain editable.
- [x] Keep existing alias dedupe behavior.
- [x] Ensure `defaultLevelsFromSchema` still prefers region/site/rack.

## Task 3: Verification

**Files:**
- Verify only.

- [x] Run `npm run test:device-v2:grouping-fields`.
- [x] Run `npm run typecheck:d2`.
- [x] Run existing Device V2 frontend CRUD/flexible search smoke specs if time allows.

## Self-Review

- Scope is only the grouping editor field dropdown.
- Labels and metadata source pickers remain available through “改用其他来源”.
- No backend API changes are required.
