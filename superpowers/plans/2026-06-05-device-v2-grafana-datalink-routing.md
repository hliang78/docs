# Device V2 Grafana DataLink Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Route OneOPS Unified Dashboard device DataLinks to Device V2 management and preserve Grafana-origin filtering behavior.

**Architecture:** Add a small pure TypeScript query resolver for Grafana route parameters, then let `DeviceV2ManagementGrouped.vue` apply the resolved query rows before loading the list. Keep `${oneops_origin}` as the dashboard origin contract and update the Unified Dashboard seed links away from legacy `device/inventory`.

**Tech Stack:** Vue 3, TypeScript, Ant Design Vue, Grafana dashboard JSON stored in SQL seed, Node/esbuild smoke tests.

---

### Task 1: Grafana Query Resolver

**Files:**
- Create: `OneOps-UI/src/views/device/device-v2-management/grafana-route-query.ts`
- Create: `OneOps-UI/scripts/device-v2-grafana-route-query-smoke.ts`

- [x] Write a smoke test covering `code`, `ip_address`, `name`, `keyword`, and `connectivity`.
- [x] Implement the resolver as a pure function returning `directCode`, structured query rows, and connectivity mode.
- [x] Run the smoke test and confirm it passes.

### Task 2: Device V2 Page Wiring

**Files:**
- Modify: `OneOps-UI/src/views/device/DeviceV2ManagementGrouped.vue`

- [x] Import the resolver.
- [x] Apply resolved query rows during `onMounted` before `loadDevices()`.
- [x] For `connectivity`, reuse the existing dashboard Prometheus proxy to fetch interrupted/normal device names, then filter by name.

### Task 3: Dashboard Seed Links

**Files:**
- Modify: `quick_env/docker-entrypoint-initdb.d/zzz-grafana-dashboard-bootstrap.sql`

- [x] Replace legacy Device V1 inventory links in OneOPS Unified Dashboard with `#/device/device-v2-management`.
- [x] Prefer `keyword` for alert target values unless the dashboard field is proven to be a Device V2 code.
- [x] Keep alert, tenant, and rule links unchanged unless they are device links.

### Task 4: Verification

**Files:**
- Test: `OneOps-UI/scripts/device-v2-grafana-route-query-smoke.ts`
- Test: `OneOps-UI/src/views/device/DeviceV2ManagementGrouped.vue`

- [x] Run the new smoke test.
- [x] Run `npm run typecheck:d2`.
- [x] Inspect git status and note pre-existing unrelated changes.
