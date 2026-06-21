# OneOPS NetPath Frontend MVP Phase 6 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a first usable `OneOPS-UI` NetPath page that can submit an analysis run, render the returned result, and open device evidence drilldown.

**Architecture:** Reuse the existing OneOPS dynamic-route shell, existing `Topology` graph component, and existing drawer/table/form patterns. Do not invent a new graph foundation. First land the NetPath API/types contract, then build a page shell, then render result summary and evidence drawer, and only then project traces onto the topology canvas.

**Tech Stack:** Vue 3, TypeScript, Ant Design Vue, existing `request.ts` API client, existing `Topology` component, OneOPS NetPath backend DTOs and APIs.

---

## File Structure

### New files

- `OneOPS-UI/src/typings/netpath/netpath.ts`
  - NetPath request/response typings mirrored from `OneOPS/app/netpath/dto/netpath.go`.
- `OneOPS-UI/src/api/netpath/netpath.ts`
  - Frontend API wrapper for NetPath preview/create/get/evidence calls.
- `OneOPS-UI/src/views/topology/NetPathMvp.vue`
  - First operator-facing NetPath page shell with form, result summary, trace list, and evidence drawer.
- `OneOPS-UI/src/views/topology/netpath-graph.ts`
  - Pure helper that maps NetPath traces/evidence into a graph-friendly highlight model consumable by the existing topology canvas.
- `OneOPS-UI/scripts/netpath-mvp-smoke.ts`
  - Lightweight smoke script importing the page/helper/api module so we can catch obvious wiring regressions outside the browser.

### Modified files

- `OneOPS-UI/src/typings/index.ts`
  - Re-export NetPath typings.
- `OneOPS-UI/src/router/utils.ts`
  - Add a hidden route entry for the NetPath MVP page so it can be opened without waiting for a visible menu rollout.
- `OneOPS-UI/package.json`
  - Add a smoke command for the new `netpath-mvp-smoke.ts` script.
- `OneOPS/static/mysql_init2.sql`
  - Optional follow-up if we want a visible menu entry instead of hidden-route-only access.
- `OneOPS/scripts/sql/output.sql`
  - Optional follow-up to keep menu seed output aligned with `mysql_init2.sql`.

## Task 1: Land Frontend NetPath Contract

**Files:**
- Create: `OneOPS-UI/src/typings/netpath/netpath.ts`
- Create: `OneOPS-UI/src/api/netpath/netpath.ts`
- Modify: `OneOPS-UI/src/typings/index.ts`
- Test: `OneOPS-UI/scripts/netpath-mvp-smoke.ts`

- [ ] **Step 1: Add a failing smoke import script**

Create `OneOPS-UI/scripts/netpath-mvp-smoke.ts` that imports the planned API functions and typings names before they exist yet:

```ts
import type {
  AnalyzeRunCreateReq,
  AnalyzeRunResp,
  AnalyzeRunDeviceEvidenceResp,
  SnapshotPreviewReq,
  SnapshotPreviewResp,
} from '../src/typings/netpath/netpath';
import {
  createNetPathAnalyzeRunReq,
  getNetPathAnalyzeRunReq,
  getNetPathAnalyzeRunDeviceEvidenceReq,
  previewNetPathSnapshotReq,
} from '../src/api/netpath/netpath';

void [
  createNetPathAnalyzeRunReq,
  getNetPathAnalyzeRunReq,
  getNetPathAnalyzeRunDeviceEvidenceReq,
  previewNetPathSnapshotReq,
] satisfies unknown[];

type _Smoke =
  | AnalyzeRunCreateReq
  | AnalyzeRunResp
  | AnalyzeRunDeviceEvidenceResp
  | SnapshotPreviewReq
  | SnapshotPreviewResp;

console.log('netpath-mvp-smoke:ok');
```

- [ ] **Step 2: Run the smoke build and verify it fails**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npx esbuild scripts/netpath-mvp-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/netpath-mvp-smoke.mjs
```

Expected: fail because `src/typings/netpath/netpath.ts` and `src/api/netpath/netpath.ts` do not exist yet.

- [ ] **Step 3: Add NetPath typings**

Create `OneOPS-UI/src/typings/netpath/netpath.ts` with the first MVP surface mirrored from `OneOPS/app/netpath/dto/netpath.go`:

```ts
export interface SnapshotPreviewReq {
  tenant_code: string;
  device_codes?: string[];
}

export interface SnapshotPreviewResp {
  snapshot_id: string;
  tenant_code: string;
  devices: number;
  links: number;
  warnings?: string[];
}

export interface AnalyzeRunCreateReq {
  tenant_code: string;
  snapshot_id?: string;
  src_ip: string;
  dst_ip: string;
  protocol?: string;
  src_port?: number;
  dst_port?: number;
  ingress_device_code: string;
  ingress_interface?: string;
  ingress_vrf?: string;
  device_codes?: string[];
  business_label?: string;
}

export interface AnalyzeDiagnostic {
  severity: string;
  code: string;
  message: string;
  refs?: string[];
}

export interface AnalyzeStep {
  type: string;
  action?: string;
  matched_object?: string;
  raw_ref?: string;
  message?: string;
  details?: Record<string, string>;
}

export interface AnalyzeHop {
  sequence: number;
  device_code: string;
  in_interface?: string;
  out_interface?: string;
  in_zone?: string;
  out_zone?: string;
  vrf?: string;
  steps: AnalyzeStep[];
}

export interface AnalyzeTrace {
  trace_id: string;
  disposition: string;
  hops: AnalyzeHop[];
  diagnostics?: AnalyzeDiagnostic[];
  confidence?: string;
}

export interface AnalyzeSourceRefs {
  config_version_ids?: string[];
  topology_snapshot_id?: string;
  collection_run_ids?: string[];
  fact_run_ids?: string[];
}

export interface AnalyzeFlow {
  src_ip: string;
  dst_ip: string;
  protocol?: string;
  src_port?: number;
  dst_port?: number;
  ingress_device_code: string;
  ingress_interface?: string;
  ingress_vrf?: string;
  business_label?: string;
}

export interface AnalyzeRouteLookupDrilldownEvidence {
  action?: string;
  prefix?: string;
  next_hop_ip?: string;
  out_interface?: string;
  route_source_ref?: string;
  raw_ref?: string;
  message?: string;
}

export interface AnalyzeForwardPeerDrilldownEvidence {
  action?: string;
  peer_device_code?: string;
  peer_interface?: string;
  topology_source?: string;
  topology_source_ref?: string;
  message?: string;
}

export interface AnalyzePolicyDrilldownEvidence {
  action?: string;
  matched_object?: string;
  policy_source_ref?: string;
  raw_ref?: string;
  message?: string;
  details?: Record<string, string>;
}

export interface AnalyzeNATDrilldownEvidence {
  action?: string;
  matched_object?: string;
  nat_source_ref?: string;
  raw_ref?: string;
  message?: string;
  details?: Record<string, string>;
}

export interface AnalyzePBRDrilldownEvidence {
  action?: string;
  matched_object?: string;
  pbr_source_ref?: string;
  raw_ref?: string;
  message?: string;
  details?: Record<string, string>;
}

export interface AnalyzePathDeviceDrilldownEvidence {
  trace_id?: string;
  trace_disposition?: string;
  sequence: number;
  device_code: string;
  in_interface?: string;
  out_interface?: string;
  vrf?: string;
  route_lookups?: AnalyzeRouteLookupDrilldownEvidence[];
  forward_peers?: AnalyzeForwardPeerDrilldownEvidence[];
  policy_steps?: AnalyzePolicyDrilldownEvidence[];
  nat_steps?: AnalyzeNATDrilldownEvidence[];
  pbr_steps?: AnalyzePBRDrilldownEvidence[];
}

export interface AnalyzeRunDeviceEvidenceResp {
  code: string;
  tenant_code: string;
  snapshot_id: string;
  device_code: string;
  source_refs?: AnalyzeSourceRefs;
  occurrences: AnalyzePathDeviceDrilldownEvidence[];
  diagnostics?: AnalyzeDiagnostic[];
}

export interface AnalyzePathDeviceEvidence {
  trace_id?: string;
  trace_disposition?: string;
  sequence: number;
  device_code: string;
  in_interface?: string;
  out_interface?: string;
  vrf?: string;
}

export interface AnalyzeEvidenceSummary {
  devices?: AnalyzePathDeviceEvidence[];
}

export interface AnalyzeResult {
  snapshot_id: string;
  source_refs?: AnalyzeSourceRefs;
  evidence_summary?: AnalyzeEvidenceSummary;
  flow: AnalyzeFlow;
  traces: AnalyzeTrace[];
  diagnostics?: AnalyzeDiagnostic[];
}

export interface AnalyzeRunResp {
  code: string;
  tenant_code: string;
  snapshot_id: string;
  status: string;
  disposition?: string;
  request: AnalyzeRunCreateReq;
  result?: AnalyzeResult;
  error?: string;
  created_at?: number;
  updated_at?: number;
}
```

- [ ] **Step 4: Add NetPath API wrapper**

Create `OneOPS-UI/src/api/netpath/netpath.ts`:

```ts
import request, { HTTP_GET, HTTP_POST } from '@/utils/request';
import type {
  AnalyzeRunCreateReq,
  AnalyzeRunDeviceEvidenceResp,
  AnalyzeRunResp,
  SnapshotPreviewReq,
  SnapshotPreviewResp,
} from '@/typings/netpath/netpath';

const BASE = '/netpath';

export const previewNetPathSnapshotReq = async (data: SnapshotPreviewReq) => {
  return request<SnapshotPreviewResp>({
    url: `${BASE}/snapshots:preview`,
    method: HTTP_POST,
    data,
  });
};

export const createNetPathAnalyzeRunReq = async (data: AnalyzeRunCreateReq) => {
  return request<AnalyzeRunResp>({
    url: `${BASE}/analysis-runs`,
    method: HTTP_POST,
    data,
  });
};

export const getNetPathAnalyzeRunReq = async (tenantCode: string, code: string) => {
  return request<AnalyzeRunResp>({
    url: `${BASE}/analysis-runs/${encodeURIComponent(code)}?tenant_code=${encodeURIComponent(tenantCode)}`,
    method: HTTP_GET,
  });
};

export const getNetPathAnalyzeRunDeviceEvidenceReq = async (
  tenantCode: string,
  code: string,
  deviceCode: string,
) => {
  return request<AnalyzeRunDeviceEvidenceResp>({
    url:
      `${BASE}/analysis-runs/${encodeURIComponent(code)}/devices/${encodeURIComponent(deviceCode)}/evidence` +
      `?tenant_code=${encodeURIComponent(tenantCode)}`,
    method: HTTP_GET,
  });
};
```

- [ ] **Step 5: Re-export the new typings**

Add to `OneOPS-UI/src/typings/index.ts`:

```ts
export * from './netpath/netpath';
```

- [ ] **Step 6: Run smoke and typecheck**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npx esbuild scripts/netpath-mvp-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/netpath-mvp-smoke.mjs
node .tmp/netpath-mvp-smoke.mjs
npm run typecheck
```

Expected: smoke prints `netpath-mvp-smoke:ok`; typecheck passes.

## Task 2: Add NetPath MVP Route And Page Shell

**Files:**
- Create: `OneOPS-UI/src/views/topology/NetPathMvp.vue`
- Modify: `OneOPS-UI/src/router/utils.ts`
- Test: `OneOPS-UI/scripts/netpath-mvp-smoke.ts`

- [ ] **Step 1: Add a failing route smoke import**

Extend `OneOPS-UI/scripts/netpath-mvp-smoke.ts` to import the page shell:

```ts
import '../src/views/topology/NetPathMvp.vue';
```

- [ ] **Step 2: Run smoke and verify it fails**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npx esbuild scripts/netpath-mvp-smoke.ts --bundle --platform=node --format=esm --loader:.vue=text --outfile=.tmp/netpath-mvp-smoke.mjs
```

Expected: fail because `NetPathMvp.vue` does not exist yet.

- [ ] **Step 3: Add hidden route entry**

In `OneOPS-UI/src/router/utils.ts`, add a hidden route near the other manually-added hidden pages:

```ts
const netPathMvpRoute: RouteRecordRaw = {
  path: 'topology/netpath-mvp',
  name: 'NetPathMvp',
  component: () => import('@/views/topology/NetPathMvp.vue'),
  meta: {
    title: 'NetPath 路径分析',
    requiresAuth: true,
    hideInMenu: true,
  },
};
```

Also append it to the list of manually registered child routes alongside the existing hidden platform routes.

- [ ] **Step 4: Add page shell**

Create `OneOPS-UI/src/views/topology/NetPathMvp.vue` with a minimal shell:

```vue
<template>
  <div class="page-container">
    <a-card title="NetPath 路径分析">
      <a-empty description="NetPath MVP shell" />
    </a-card>
  </div>
</template>
```

- [ ] **Step 5: Re-run smoke and typecheck**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npx esbuild scripts/netpath-mvp-smoke.ts --bundle --platform=node --format=esm --loader:.vue=text --outfile=.tmp/netpath-mvp-smoke.mjs
npm run typecheck
```

Expected: page shell resolves and typecheck passes.

## Task 3: Build Run Form And Result Summary

**Files:**
- Modify: `OneOPS-UI/src/views/topology/NetPathMvp.vue`
- Test: `OneOPS-UI/scripts/netpath-mvp-smoke.ts`

- [ ] **Step 1: Add a failing page-state smoke assertion**

Update the smoke script to import the page module and assert the file text includes the expected markers:

```ts
import netPathPage from '../src/views/topology/NetPathMvp.vue';

if (!String(netPathPage).includes('NetPath 路径分析')) {
  throw new Error('netpath page title missing');
}
```

Expected: fail once the placeholder shell is replaced but the form/result markers are still missing.

- [ ] **Step 2: Add the form and submit path**

Expand `NetPathMvp.vue` to include:

```vue
<a-form :model="formState" layout="vertical">
  <a-row :gutter="16">
    <a-col :span="8"><a-form-item label="租户"><a-input v-model:value="formState.tenant_code" /></a-form-item></a-col>
    <a-col :span="8"><a-form-item label="源 IP"><a-input v-model:value="formState.src_ip" /></a-form-item></a-col>
    <a-col :span="8"><a-form-item label="目的 IP"><a-input v-model:value="formState.dst_ip" /></a-form-item></a-col>
    <a-col :span="8"><a-form-item label="协议"><a-input v-model:value="formState.protocol" /></a-form-item></a-col>
    <a-col :span="8"><a-form-item label="入口设备"><a-input v-model:value="formState.ingress_device_code" /></a-form-item></a-col>
    <a-col :span="8"><a-form-item label="设备范围"><a-select v-model:value="formState.device_codes" mode="tags" /></a-form-item></a-col>
  </a-row>
  <a-space>
    <a-button type="primary" :loading="submitting" @click="handleSubmit">开始分析</a-button>
    <a-button @click="handlePreview">快照预检</a-button>
  </a-space>
</a-form>
```

Also add script state that calls:
- `previewNetPathSnapshotReq`
- `createNetPathAnalyzeRunReq`
- `getNetPathAnalyzeRunReq`

and stores:
- `previewResp`
- `runResp`
- `selectedTraceId`

- [ ] **Step 3: Add result summary blocks**

Add result presentation for:
- run code and status;
- primary disposition;
- diagnostics list;
- trace list;
- hop list inside the selected trace.

Render at least:

```vue
<a-alert v-if="runResp?.error" type="error" :message="runResp.error" show-icon />
<a-descriptions v-if="runResp" bordered :column="2">
  <a-descriptions-item label="Run Code">{{ runResp.code }}</a-descriptions-item>
  <a-descriptions-item label="Disposition">{{ runResp.disposition || runResp.result?.traces?.[0]?.disposition }}</a-descriptions-item>
  <a-descriptions-item label="Snapshot">{{ runResp.snapshot_id }}</a-descriptions-item>
  <a-descriptions-item label="Status">{{ runResp.status }}</a-descriptions-item>
</a-descriptions>
```

- [ ] **Step 4: Run smoke and typecheck**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npx esbuild scripts/netpath-mvp-smoke.ts --bundle --platform=node --format=esm --loader:.vue=text --outfile=.tmp/netpath-mvp-smoke.mjs
node .tmp/netpath-mvp-smoke.mjs
npm run typecheck
```

Expected: smoke passes; typecheck passes.

## Task 4: Add Device Evidence Drawer

**Files:**
- Modify: `OneOPS-UI/src/views/topology/NetPathMvp.vue`
- Test: `OneOPS-UI/scripts/netpath-mvp-smoke.ts`

- [ ] **Step 1: Add a failing device-evidence marker to smoke**

Update the smoke script to require `device evidence` drawer markers in the page text.

- [ ] **Step 2: Add hop click and evidence fetch**

In `NetPathMvp.vue`, add:
- `selectedDeviceCode`
- `evidenceDrawerOpen`
- `deviceEvidenceLoading`
- `deviceEvidenceResp`

and on hop/device click call:

```ts
deviceEvidenceResp.value = await getNetPathAnalyzeRunDeviceEvidenceReq(
  formState.tenant_code,
  runResp.value.code,
  deviceCode,
);
```

- [ ] **Step 3: Add evidence drawer UI**

Render an `a-drawer` showing:
- run/snapshot/device summary;
- `occurrences`;
- route lookups;
- forward peers;
- policy steps;
- nat steps;
- pbr steps;
- diagnostics.

Do not try to pretty-print every nested field yet. A clean list view is enough for MVP.

- [ ] **Step 4: Run smoke and typecheck**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npx esbuild scripts/netpath-mvp-smoke.ts --bundle --platform=node --format=esm --loader:.vue=text --outfile=.tmp/netpath-mvp-smoke.mjs
node .tmp/netpath-mvp-smoke.mjs
npm run typecheck
```

Expected: evidence markers present and typecheck passes.

## Task 5: Reuse Topology Component For Trace Highlight

**Files:**
- Create: `OneOPS-UI/src/views/topology/netpath-graph.ts`
- Modify: `OneOPS-UI/src/views/topology/NetPathMvp.vue`
- Test: `OneOPS-UI/scripts/netpath-mvp-smoke.ts`

- [ ] **Step 1: Add a failing helper import**

Update the smoke script to import `src/views/topology/netpath-graph.ts`.

- [ ] **Step 2: Add the graph projection helper**

Create `OneOPS-UI/src/views/topology/netpath-graph.ts` with a pure helper that derives at least:

```ts
import type { AnalyzeRunResp } from '@/typings/netpath/netpath';

export interface NetPathGraphHighlight {
  nodeCodes: string[];
  edgePairs: Array<{ from: string; to: string }>;
}

export const buildNetPathGraphHighlight = (run?: AnalyzeRunResp | null, traceId?: string): NetPathGraphHighlight => {
  const trace = run?.result?.traces?.find(item => item.trace_id === traceId) || run?.result?.traces?.[0];
  if (!trace) return { nodeCodes: [], edgePairs: [] };
  const nodeCodes = trace.hops.map(hop => hop.device_code).filter(Boolean);
  const edgePairs = trace.hops.slice(1).map((hop, index) => ({
    from: trace.hops[index].device_code,
    to: hop.device_code,
  }));
  return { nodeCodes, edgePairs };
};
```

- [ ] **Step 3: Reuse existing topology canvas**

In `NetPathMvp.vue`:
- load tenant topology using `topologyGenerateReq`;
- derive `highlightNodeIds` from matching `device_code`;
- optionally derive `highlightEdgeIds` by matching consecutive device pairs against topology edges;
- render the existing `Topology` component below the run summary.

Do not block MVP on perfect edge matching. Node highlighting is the required first win.

- [ ] **Step 4: Run smoke and typecheck**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npx esbuild scripts/netpath-mvp-smoke.ts --bundle --platform=node --format=esm --loader:.vue=text --outfile=.tmp/netpath-mvp-smoke.mjs
node .tmp/netpath-mvp-smoke.mjs
npm run typecheck
```

Expected: helper imports cleanly and page typechecks with the topology component wired.

## Task 6: Optional Productization Follow-Up

**Files:**
- Modify: `OneOPS/static/mysql_init2.sql`
- Modify: `OneOPS/scripts/sql/output.sql`
- Optional backend follow-up: `OneOPS/app/netpath/api`, `OneOPS/app/netpath/service`, `OneOPS/app/netpath/router`

- [ ] **Step 1: Decide whether the MVP should be hidden-route-only or menu-visible**

If hidden-route-only is acceptable, skip SQL menu changes for the first pass.

- [ ] **Step 2: If menu-visible, add a seeded menu item**

Add a menu record that points to:

```text
../views/topology/NetPathMvp.vue
```

under the topology or dashboard menu branch.

- [ ] **Step 3: Decide whether run history is required**

If users must reopen past NetPath runs from the page, plan a backend follow-up for:
- `list netpath analysis runs by tenant`
- optional filtering by disposition/status/date

Do not block the first MVP page on this API.

## Plan Self-Review

- Spec coverage: this plan covers Phase 6A and 6B completely, and lands the first thin slice of Phase 6C.
- Placeholder scan: no TODO/TBD placeholders remain in the execution steps.
- Type consistency: API/types/page/helper names are consistent across the plan and match the intended NetPath naming surface.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-20-oneops-netpath-frontend-mvp-phase6.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints
