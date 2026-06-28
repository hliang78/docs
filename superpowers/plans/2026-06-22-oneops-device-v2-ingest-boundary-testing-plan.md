# OneOPS Device V2 导入设备清单边界测试 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立 Device V2 导入设备清单的系统化边界测试体系，覆盖导入数据分类、提交结果合同，以及“提交成功后管理页必可见”的真实链路。

**Architecture:** 先抽出可复用的导入边界样例与分类判定辅助模块，用数据级 smoke 固化“必须拦截 / 仅登记 / 可采集”规则；再补一层提交合同 smoke，验证 handoff 结果与成功设备集合的一致性；最后用少量真实浏览器 E2E 回放高价值主线，证明“提交成功 -> handoff -> 管理页可见”的产品承诺成立。实现时遵循现有 `scripts/*smoke*` 风格，优先补测试，不先改页面行为，只有在测试逼出缺口时才最小补实现。

**Tech Stack:** TypeScript, Vue 3 composables, Node smoke scripts, existing Device V2 ingest API helpers, CDP/browser smoke scripts, docs subrepo plan/spec workflow

---

## 2026-06-23 Status Snapshot

### Current Smoke Coverage

- `smoke:d2-ingest-boundary-classification`
  Covers row/batch boundary classification for `must_block / registry_only / manageable`.
- `smoke:d2-ingest-draft-parser-boundary`
  Covers parser rejection paths including non-`xlsx`, missing headers, and duplicate mapped header conflicts.
- `smoke:d2-ingest-submit-summary-boundary`
  Covers submit gating drift between issue counts, blocked rows, and registry-only rows.
- `smoke:d2-ingest-submit-visibility-contract`
  Covers handoff scope fallback from `post_check.handoff` to `execution.device_results`, including count drift.
- `smoke:d2-ingest-success-handoff-contract`
  Covers success handoff page behavior when only `task_id + counts` are available.
- `smoke:d2-ingest-management-handoff-query`
  Covers ingest-page handoff query construction so `task_id` fallback is not masked by stale draft codes.
- `smoke:d2-ingest-submit-payload-contract`
  Covers payload mapping for SNMP-only, hybrid CLI/SNMP, out-band SNMP, and registry-only traceability.
- `smoke:d2-ingest-draft-roundtrip-contract`
  Covers `rowValuesToIngestDevice -> buildDraftValuesFromIngestDevice` round-trip for `credential_refs`, `access_points`, and traceability fields.
- `smoke:d2-ingest-structured-field-fallback`
  Covers malformed or wrong-shape `credential_refs/access_points` draft values so ingest falls back to discrete fields instead of silently losing manageable metadata.
- `smoke:d2-ingest-productized-flow`
  Covers compact ingest flow structure, redirect contract, and single visible success scope usage.
- `smoke:d2-ingest-visibility-e2e`
  Covers a real browser replay for `handoff -> management` visibility, including manageable-only, registry-only task fallback, mixed batches, and clear-filter recovery.
- `smoke:d2-ingest-real-api-acceptance-contract`
  Covers the candidate-selection contract for real-API acceptance, including explicit `require_handoff` enforcement and clear failure when the backend has no handoff-bearing task.
- `acceptance:d2-ingest-real-api`
  Covers one real backend ingest task payload, proving the frontend can still derive a visible management handoff scope from live `execution.device_results` even when `post_check.handoff` is absent; in `require_handoff` mode it now emits blocker evidence instead of silently falling back.
- `typecheck:d2`
  Guards the focused Device V2 TypeScript surface.

### High-Value Gaps Still Open

- Submit-page browser replay is still missing.
  The new E2E smoke starts from the success handoff route, so it proves visibility/navigation contracts but does not yet upload a sheet, execute submit, and observe a live backend-created success scope end-to-end.
- Backend acceptance coverage is still narrow.
  We now verify one real completed task, and the new strict acceptance gate shows that all 7 locally available completed tasks currently lack `post_check.handoff` while still exposing visible scope through `execution.device_results`. We still do not have acceptance coverage for tasks where both payload sections exist, drift, or disagree.
- No coverage yet for result-table UI rendering against mixed real payloads.
  The contract tests validate data helpers, but not whether the result cards/table render the fallback counts and success scope correctly under a mounted browser DOM.
- No persistence-layer verification for stored Device V2 records.
  We do not yet prove that `metadata.source`, `metadata.batch_id`, `metadata.d2la.original_code`, `attributes.access_points`, and `attributes.credential_refs` survive backend store/read cycles unchanged.
- No negative acceptance around malformed but still parseable structured fields.
  The new fallback smoke covers malformed draft values at the mapper layer, but we still do not verify backend-returned historical records with partially damaged nested attributes inside actual browser rendering.

### Recommended Next Moves

1. Produce or preserve at least one real task with `post_check.handoff`:
   until the backend emits such a task in this environment, the strict `require_handoff` acceptance will continue to fail and serves as an explicit blocker signal.
2. Add one store/read round-trip acceptance:
   submit a registry-only row with traceability + one hybrid manageable row, then re-fetch task/history payload and verify critical metadata/access fields survive unchanged.
3. Add one submit-page browser replay:
   upload manageable + registry-only mixed batch -> submit -> success handoff -> management page filter visible.

### Important Interpretation Notes

- The frontend is now intentionally biased toward `execution.device_results` when handoff lists or counts drift.
  This reduces visible product failures. The new real-API acceptance also shows the fallback is currently required across every locally available sampled completed task because `post_check.handoff` is missing entirely.
- The current suite is strong at catching frontend regression.
  It is not yet strong at proving end-to-end product truth across browser + API + persistence.

---

### Task 1: 建立导入边界样例库

**Files:**
- Create: `OneOPS-UI/scripts/d2-ingest-boundary-fixtures.ts`
- Test: `OneOPS-UI/scripts/d2-ingest-boundary-classification-smoke.ts`
- Reference: `OneOPS-UI/src/views/device/device-v2-import/field-config.ts`
- Reference: `OneOPS-UI/src/views/device/device-v2-import/draft-parser.ts`
- Reference: `OneOPS-UI/src/views/device/device-v2-import/draft-issues.ts`

- [ ] **Step 1: Write the failing test**

Create `OneOPS-UI/scripts/d2-ingest-boundary-classification-smoke.ts` with the first failing assertion that imports a fixture list that does not exist yet:

```ts
import assert from 'node:assert/strict';
import { ingestBoundaryFixtures } from './d2-ingest-boundary-fixtures';

assert.equal(Array.isArray(ingestBoundaryFixtures), true, 'fixture catalog should export an array');
assert.equal(ingestBoundaryFixtures.length >= 10, true, 'fixture catalog should include the first-round boundary set');
assert.equal(
  ingestBoundaryFixtures.some(item => item.id === 'mixed-batch-with-blocked-row'),
  true,
  'fixture catalog should include the blocked-row mixed batch',
);

console.log('d2 ingest boundary classification smoke passed');
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npx esbuild scripts/d2-ingest-boundary-classification-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-ingest-boundary-classification-smoke.mjs >/dev/null && node .tmp/d2-ingest-boundary-classification-smoke.mjs`

Expected: FAIL with a module resolution error because `scripts/d2-ingest-boundary-fixtures.ts` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create `OneOPS-UI/scripts/d2-ingest-boundary-fixtures.ts` with the first-round fixture catalog:

```ts
export type IngestBoundaryFixtureExpectation = 'must_block' | 'registry_only' | 'manageable';

export interface IngestBoundaryRowFixture {
  rowKey: string;
  rowNo: number;
  values: Record<string, unknown>;
  expected: IngestBoundaryFixtureExpectation;
}

export interface IngestBoundaryBatchFixture {
  id: string;
  title: string;
  rows: IngestBoundaryRowFixture[];
}

export const ingestBoundaryFixtures: IngestBoundaryBatchFixture[] = [
  {
    id: 'blank-row-blocked',
    title: '全空行必须拦截',
    rows: [{ rowKey: 'blank-1', rowNo: 2, values: {}, expected: 'must_block' }],
  },
  {
    id: 'invalid-ip-blocked',
    title: '非法管理 IP 必须拦截',
    rows: [
      {
        rowKey: 'ip-1',
        rowNo: 2,
        values: { biz_code: 'IP-BAD-1', in_band_ip: '999.1.1.1' },
        expected: 'must_block',
      },
    ],
  },
  {
    id: 'unrecognized-identity-blocked',
    title: '无法形成身份的记录必须拦截',
    rows: [{ rowKey: 'identity-1', rowNo: 2, values: { remark: 'only remark' }, expected: 'must_block' }],
  },
  {
    id: 'registry-only-basic-ledger',
    title: '基础台账字段允许仅登记',
    rows: [
      {
        rowKey: 'registry-1',
        rowNo: 2,
        values: { biz_code: 'REG-001', biz_name: '登记设备', site_name: '北艾数据中心' },
        expected: 'registry_only',
      },
    ],
  },
  {
    id: 'registry-only-ip-without-credential',
    title: '只有管理地址时仅允许登记',
    rows: [
      {
        rowKey: 'registry-2',
        rowNo: 2,
        values: { biz_code: 'REG-002', in_band_ip: '172.32.2.16' },
        expected: 'registry_only',
      },
    ],
  },
  {
    id: 'registry-only-legacy-remark',
    title: '历史 remark 字段合并后仍仅登记',
    rows: [
      {
        rowKey: 'registry-3',
        rowNo: 2,
        values: { biz_code: 'REG-003', remark: '归属类别=路由器; 虚拟区域=DefaultArea' },
        expected: 'registry_only',
      },
    ],
  },
  {
    id: 'manageable-ssh-plaintext',
    title: '带内账号密码满足可采集',
    rows: [
      {
        rowKey: 'manage-1',
        rowNo: 2,
        values: {
          biz_code: 'MNG-001',
          in_band_ip: '172.32.2.21',
          in_band_username: 'ops',
          in_band_password: 'secret',
        },
        expected: 'manageable',
      },
    ],
  },
  {
    id: 'manageable-snmp-v2c',
    title: 'SNMP community 满足可采集',
    rows: [
      {
        rowKey: 'manage-2',
        rowNo: 2,
        values: { biz_code: 'MNG-002', in_band_ip: '172.32.2.22', snmp_community: 'public' },
        expected: 'manageable',
      },
    ],
  },
  {
    id: 'mixed-batch-manageable-and-registry',
    title: '混合批次 A：2 条可采集 + 1 条仅登记',
    rows: [
      {
        rowKey: 'mix-a-1',
        rowNo: 2,
        values: { biz_code: 'MIX-A-1', in_band_ip: '172.32.2.31', in_band_username: 'ops', in_band_password: 'pw' },
        expected: 'manageable',
      },
      {
        rowKey: 'mix-a-2',
        rowNo: 3,
        values: { biz_code: 'MIX-A-2', in_band_ip: '172.32.2.32', snmp_community: 'public' },
        expected: 'manageable',
      },
      {
        rowKey: 'mix-a-3',
        rowNo: 4,
        values: { biz_code: 'MIX-A-3', biz_name: '登记设备 A3', site_name: '北艾数据中心' },
        expected: 'registry_only',
      },
    ],
  },
  {
    id: 'mixed-batch-with-blocked-row',
    title: '混合批次 B：1 条可采集 + 1 条仅登记 + 1 条拦截',
    rows: [
      {
        rowKey: 'mix-b-1',
        rowNo: 2,
        values: { biz_code: 'MIX-B-1', in_band_ip: '172.32.2.41', in_band_username: 'ops', in_band_password: 'pw' },
        expected: 'manageable',
      },
      {
        rowKey: 'mix-b-2',
        rowNo: 3,
        values: { biz_code: 'MIX-B-2', biz_name: '登记设备 B2', site_name: '北艾数据中心' },
        expected: 'registry_only',
      },
      {
        rowKey: 'mix-b-3',
        rowNo: 4,
        values: { biz_code: 'MIX-B-3', in_band_ip: '中文IP' },
        expected: 'must_block',
      },
    ],
  },
];
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npx esbuild scripts/d2-ingest-boundary-classification-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-ingest-boundary-classification-smoke.mjs >/dev/null && node .tmp/d2-ingest-boundary-classification-smoke.mjs`

Expected: PASS with `d2 ingest boundary classification smoke passed`

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git add scripts/d2-ingest-boundary-fixtures.ts scripts/d2-ingest-boundary-classification-smoke.ts
git commit -m "test: add ingest boundary fixture catalog"
```

### Task 2: 抽出导入边界分类辅助模块

**Files:**
- Create: `OneOPS-UI/src/views/device/device-v2-import/draft-boundary.ts`
- Modify: `OneOPS-UI/scripts/d2-ingest-boundary-classification-smoke.ts`
- Reference: `OneOPS-UI/src/views/device/device-v2-import/draft-issues.ts`
- Reference: `OneOPS-UI/src/views/device/device-v2-import/types.ts`

- [ ] **Step 1: Write the failing test**

Extend `OneOPS-UI/scripts/d2-ingest-boundary-classification-smoke.ts` to require a reusable classifier:

```ts
import assert from 'node:assert/strict';
import { ingestBoundaryFixtures } from './d2-ingest-boundary-fixtures';
import { classifyDraftBoundaryBatch, classifyDraftBoundaryRow } from '../src/views/device/device-v2-import/draft-boundary';

const blockedBatch = ingestBoundaryFixtures.find(item => item.id === 'invalid-ip-blocked');
if (!blockedBatch) throw new Error('invalid-ip-blocked fixture missing');

assert.equal(
  classifyDraftBoundaryRow({ row_key: 'x', row_no: 2, values: blockedBatch.rows[0].values }),
  'must_block',
  'invalid IP row should classify as must_block',
);

const mixedBatch = ingestBoundaryFixtures.find(item => item.id === 'mixed-batch-with-blocked-row');
if (!mixedBatch) throw new Error('mixed-batch-with-blocked-row fixture missing');

assert.deepEqual(classifyDraftBoundaryBatch(mixedBatch.rows.map(row => ({ row_key: row.rowKey, row_no: row.rowNo, values: row.values }))), {
  total: 3,
  mustBlock: 1,
  registryOnly: 1,
  manageable: 1,
  submittable: 2,
});

console.log('d2 ingest boundary classification smoke passed');
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npx esbuild scripts/d2-ingest-boundary-classification-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-ingest-boundary-classification-smoke.mjs >/dev/null && node .tmp/d2-ingest-boundary-classification-smoke.mjs`

Expected: FAIL because `src/views/device/device-v2-import/draft-boundary.ts` does not exist.

- [ ] **Step 3: Write minimal implementation**

Create `OneOPS-UI/src/views/device/device-v2-import/draft-boundary.ts`:

```ts
import { draftRowIssues, isDraftManageable } from './draft-issues';
import type { DraftRow } from './types';

export type DraftBoundaryClassification = 'must_block' | 'registry_only' | 'manageable';

export interface DraftBoundaryBatchSummary {
  total: number;
  mustBlock: number;
  registryOnly: number;
  manageable: number;
  submittable: number;
}

const ipv4Pattern = /^(25[0-5]|2[0-4]\d|1?\d?\d)(\.(25[0-5]|2[0-4]\d|1?\d?\d)){3}$/;

function isInvalidIP(value: string) {
  const normalized = String(value || '').trim();
  return !!normalized && !ipv4Pattern.test(normalized);
}

export function classifyDraftBoundaryRow(row: DraftRow): DraftBoundaryClassification {
  const duplicateIdentityMap = new Map<string, number>();
  const issues = draftRowIssues(row, duplicateIdentityMap);
  if (issues.length > 0) return 'must_block';

  const inBandIP = String(row.values.in_band_ip || '').trim();
  const outBandIP = String(row.values.out_band_ip || '').trim();
  if (isInvalidIP(inBandIP) || isInvalidIP(outBandIP)) {
    return 'must_block';
  }

  return isDraftManageable(row) ? 'manageable' : 'registry_only';
}

export function classifyDraftBoundaryBatch(rows: DraftRow[]): DraftBoundaryBatchSummary {
  return rows.reduce<DraftBoundaryBatchSummary>(
    (summary, row) => {
      summary.total += 1;
      const classification = classifyDraftBoundaryRow(row);
      if (classification === 'must_block') summary.mustBlock += 1;
      if (classification === 'registry_only') summary.registryOnly += 1;
      if (classification === 'manageable') summary.manageable += 1;
      if (classification !== 'must_block') summary.submittable += 1;
      return summary;
    },
    { total: 0, mustBlock: 0, registryOnly: 0, manageable: 0, submittable: 0 },
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npx esbuild scripts/d2-ingest-boundary-classification-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-ingest-boundary-classification-smoke.mjs >/dev/null && node .tmp/d2-ingest-boundary-classification-smoke.mjs`

Expected: PASS with `d2 ingest boundary classification smoke passed`

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git add src/views/device/device-v2-import/draft-boundary.ts scripts/d2-ingest-boundary-classification-smoke.ts
git commit -m "test: add draft boundary classifier"
```

### Task 3: 用样例库跑完整分类矩阵

**Files:**
- Modify: `OneOPS-UI/scripts/d2-ingest-boundary-classification-smoke.ts`
- Reference: `OneOPS-UI/scripts/d2-company-excel-import-smoke.ts`

- [ ] **Step 1: Write the failing test**

Replace the smoke body with a full matrix assertion:

```ts
import assert from 'node:assert/strict';
import { ingestBoundaryFixtures } from './d2-ingest-boundary-fixtures';
import { classifyDraftBoundaryBatch, classifyDraftBoundaryRow } from '../src/views/device/device-v2-import/draft-boundary';

for (const fixture of ingestBoundaryFixtures) {
  const rows = fixture.rows.map(row => ({ row_key: row.rowKey, row_no: row.rowNo, values: row.values }));
  for (let index = 0; index < fixture.rows.length; index += 1) {
    assert.equal(
      classifyDraftBoundaryRow(rows[index]),
      fixture.rows[index].expected,
      `${fixture.id} row ${fixture.rows[index].rowKey} should classify as ${fixture.rows[index].expected}`,
    );
  }
}

const mixedA = ingestBoundaryFixtures.find(item => item.id === 'mixed-batch-manageable-and-registry');
if (!mixedA) throw new Error('mixed-batch-manageable-and-registry fixture missing');
assert.deepEqual(
  classifyDraftBoundaryBatch(mixedA.rows.map(row => ({ row_key: row.rowKey, row_no: row.rowNo, values: row.values }))),
  { total: 3, mustBlock: 0, registryOnly: 1, manageable: 2, submittable: 3 },
  'mixed batch A summary should match the product rules',
);

const mixedB = ingestBoundaryFixtures.find(item => item.id === 'mixed-batch-with-blocked-row');
if (!mixedB) throw new Error('mixed-batch-with-blocked-row fixture missing');
assert.deepEqual(
  classifyDraftBoundaryBatch(mixedB.rows.map(row => ({ row_key: row.rowKey, row_no: row.rowNo, values: row.values }))),
  { total: 3, mustBlock: 1, registryOnly: 1, manageable: 1, submittable: 2 },
  'mixed batch B summary should exclude the blocked row from submittable totals',
);

console.log('d2 ingest boundary classification smoke passed');
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npx esbuild scripts/d2-ingest-boundary-classification-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-ingest-boundary-classification-smoke.mjs >/dev/null && node .tmp/d2-ingest-boundary-classification-smoke.mjs`

Expected: FAIL on at least one row until the classifier handles all first-round fixtures correctly.

- [ ] **Step 3: Write minimal implementation**

Update `OneOPS-UI/src/views/device/device-v2-import/draft-boundary.ts` so the classifier handles the first-round matrix without overfitting:

```ts
import { draftRowIssues, isDraftManageable } from './draft-issues';
import type { DraftRow } from './types';

export type DraftBoundaryClassification = 'must_block' | 'registry_only' | 'manageable';

export interface DraftBoundaryBatchSummary {
  total: number;
  mustBlock: number;
  registryOnly: number;
  manageable: number;
  submittable: number;
}

const ipv4Pattern = /^(25[0-5]|2[0-4]\d|1?\d?\d)(\.(25[0-5]|2[0-4]\d|1?\d?\d)){3}$/;

function hasInvalidDraftIP(row: DraftRow) {
  return ['in_band_ip', 'out_band_ip'].some(key => {
    const value = String(row.values[key] || '').trim();
    return !!value && !ipv4Pattern.test(value);
  });
}

function hasUnsupportedLoginMethod(row: DraftRow) {
  const loginMethod = String(row.values.login_method || '').trim().toLowerCase();
  return !!loginMethod && !['ssh', 'snmp', 'winrm', 'ipmi', 'redfish'].includes(loginMethod);
}

export function classifyDraftBoundaryRow(row: DraftRow): DraftBoundaryClassification {
  const duplicateIdentityMap = new Map<string, number>();
  if (draftRowIssues(row, duplicateIdentityMap).length > 0) return 'must_block';
  if (hasInvalidDraftIP(row)) return 'must_block';
  if (hasUnsupportedLoginMethod(row)) return 'must_block';
  return isDraftManageable(row) ? 'manageable' : 'registry_only';
}

export function classifyDraftBoundaryBatch(rows: DraftRow[]): DraftBoundaryBatchSummary {
  return rows.reduce<DraftBoundaryBatchSummary>(
    (summary, row) => {
      summary.total += 1;
      const classification = classifyDraftBoundaryRow(row);
      if (classification === 'must_block') summary.mustBlock += 1;
      if (classification === 'registry_only') summary.registryOnly += 1;
      if (classification === 'manageable') summary.manageable += 1;
      if (classification !== 'must_block') summary.submittable += 1;
      return summary;
    },
    { total: 0, mustBlock: 0, registryOnly: 0, manageable: 0, submittable: 0 },
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npx esbuild scripts/d2-ingest-boundary-classification-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-ingest-boundary-classification-smoke.mjs >/dev/null && node .tmp/d2-ingest-boundary-classification-smoke.mjs`

Expected: PASS with `d2 ingest boundary classification smoke passed`

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git add scripts/d2-ingest-boundary-classification-smoke.ts src/views/device/device-v2-import/draft-boundary.ts
git commit -m "test: cover ingest boundary classification matrix"
```

### Task 4: 让导入页复用分类辅助模块

**Files:**
- Modify: `OneOPS-UI/src/views/device/device-v2-import/useDeviceV2IngestDraft.ts`
- Modify: `OneOPS-UI/src/views/device/DeviceV2IngestPipelineRedesign.vue`
- Reference: `OneOPS-UI/src/views/device/device-v2-import/draft-boundary.ts`
- Test: `OneOPS-UI/scripts/d2-ingest-boundary-classification-smoke.ts`

- [ ] **Step 1: Write the failing test**

Add source assertions to `OneOPS-UI/scripts/d2-ingest-boundary-classification-smoke.ts`:

```ts
import { readFileSync } from 'node:fs';
// keep existing asserts above
const draftComposable = readFileSync('src/views/device/device-v2-import/useDeviceV2IngestDraft.ts', 'utf8');
const ingestPage = readFileSync('src/views/device/DeviceV2IngestPipelineRedesign.vue', 'utf8');

assert.match(
  draftComposable,
  /from '\.\/draft-boundary'/,
  'draft composable should reuse the shared draft boundary helper',
);
assert.match(
  ingestPage,
  /draftManageableCount|draftIssueCount/,
  'ingest page should continue to expose the summary counts after boundary helper integration',
);
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npx esbuild scripts/d2-ingest-boundary-classification-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-ingest-boundary-classification-smoke.mjs >/dev/null && node .tmp/d2-ingest-boundary-classification-smoke.mjs`

Expected: FAIL because `useDeviceV2IngestDraft.ts` does not yet import `./draft-boundary`.

- [ ] **Step 3: Write minimal implementation**

Update `OneOPS-UI/src/views/device/device-v2-import/useDeviceV2IngestDraft.ts` to import and expose the batch summary:

```ts
import { classifyDraftBoundaryBatch, classifyDraftBoundaryRow } from './draft-boundary';
```

Add these computed values near the existing counts:

```ts
  const draftBoundarySummary = computed(() => classifyDraftBoundaryBatch(draftRows.value));
  const draftManageableCount = computed(() => draftBoundarySummary.value.manageable);
  const draftBlockingCount = computed(() => draftBoundarySummary.value.mustBlock);
  const draftRegistryOnlyCount = computed(() => draftBoundarySummary.value.registryOnly);
```

Return the new values from the composable:

```ts
    draftBoundarySummary,
    draftBlockingCount,
    draftRegistryOnlyCount,
```

Keep `DeviceV2IngestPipelineRedesign.vue` using the existing summary cards; only update imports or destructuring if TypeScript requires it.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npx esbuild scripts/d2-ingest-boundary-classification-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-ingest-boundary-classification-smoke.mjs >/dev/null && node .tmp/d2-ingest-boundary-classification-smoke.mjs`

Expected: PASS with `d2 ingest boundary classification smoke passed`

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git add src/views/device/device-v2-import/useDeviceV2IngestDraft.ts src/views/device/DeviceV2IngestPipelineRedesign.vue scripts/d2-ingest-boundary-classification-smoke.ts
git commit -m "refactor: reuse draft boundary helper in ingest page"
```

### Task 5: 补提交合同 smoke 的首个失败断言

**Files:**
- Create: `OneOPS-UI/scripts/d2-ingest-submit-visibility-contract-smoke.ts`
- Reference: `OneOPS-UI/src/views/device/device-v2-ingest-flow-outcome.ts`
- Reference: `OneOPS-UI/src/api/device/device-v2.ts`
- Reference: `OneOPS-UI/scripts/d2-ingest-productized-flow-smoke.ts`

- [ ] **Step 1: Write the failing test**

Create `OneOPS-UI/scripts/d2-ingest-submit-visibility-contract-smoke.ts`:

```ts
import assert from 'node:assert/strict';
import { buildSubmitVisibilityContractCases } from '../src/views/device/device-v2-import/draft-submit-contract';

const cases = buildSubmitVisibilityContractCases();
assert.equal(Array.isArray(cases), true, 'submit visibility contract cases should export an array');
assert.equal(cases.length >= 4, true, 'submit visibility contract cases should include the first-round contract set');

console.log('d2 ingest submit visibility contract smoke passed');
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npx esbuild scripts/d2-ingest-submit-visibility-contract-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-ingest-submit-visibility-contract-smoke.mjs >/dev/null && node .tmp/d2-ingest-submit-visibility-contract-smoke.mjs`

Expected: FAIL because `src/views/device/device-v2-import/draft-submit-contract.ts` does not exist.

- [ ] **Step 3: Write minimal implementation**

Create `OneOPS-UI/src/views/device/device-v2-import/draft-submit-contract.ts`:

```ts
export interface SubmitVisibilityContractCase {
  id: string;
  taskID: string;
  outcomeStatus: 'success' | 'partial_success' | 'failed';
  successDeviceCodes: string[];
  manageableCount: number;
  registryOnlyCount: number;
}

export function buildSubmitVisibilityContractCases(): SubmitVisibilityContractCase[] {
  return [
    {
      id: 'manageable-only-batch',
      taskID: 'task-manageable-only',
      outcomeStatus: 'success',
      successDeviceCodes: ['MNG-001', 'MNG-002'],
      manageableCount: 2,
      registryOnlyCount: 0,
    },
    {
      id: 'registry-only-batch',
      taskID: 'task-registry-only',
      outcomeStatus: 'success',
      successDeviceCodes: ['REG-001', 'REG-002'],
      manageableCount: 0,
      registryOnlyCount: 2,
    },
    {
      id: 'mixed-manageable-and-registry',
      taskID: 'task-mixed-success',
      outcomeStatus: 'partial_success',
      successDeviceCodes: ['MIX-A-1', 'MIX-A-2', 'MIX-A-3'],
      manageableCount: 2,
      registryOnlyCount: 1,
    },
    {
      id: 'mixed-with-blocked-row',
      taskID: 'task-mixed-filtered',
      outcomeStatus: 'partial_success',
      successDeviceCodes: ['MIX-B-1', 'MIX-B-2'],
      manageableCount: 1,
      registryOnlyCount: 1,
    },
  ];
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npx esbuild scripts/d2-ingest-submit-visibility-contract-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-ingest-submit-visibility-contract-smoke.mjs >/dev/null && node .tmp/d2-ingest-submit-visibility-contract-smoke.mjs`

Expected: PASS with `d2 ingest submit visibility contract smoke passed`

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git add src/views/device/device-v2-import/draft-submit-contract.ts scripts/d2-ingest-submit-visibility-contract-smoke.ts
git commit -m "test: add ingest submit visibility contract cases"
```

### Task 6: 实现提交合同 smoke 的完整断言

**Files:**
- Modify: `OneOPS-UI/scripts/d2-ingest-submit-visibility-contract-smoke.ts`
- Reference: `OneOPS-UI/src/views/device/device-v2-ingest-flow-outcome.ts`
- Reference: `OneOPS-UI/src/views/device/device-v2-import/draft-submit-contract.ts`

- [ ] **Step 1: Write the failing test**

Replace the smoke body with full contract assertions:

```ts
import assert from 'node:assert/strict';
import { resolveIngestFlowOutcome } from '../src/views/device/device-v2-ingest-flow-outcome';
import { buildSubmitVisibilityContractCases } from '../src/views/device/device-v2-import/draft-submit-contract';

for (const testCase of buildSubmitVisibilityContractCases()) {
  const outcome = resolveIngestFlowOutcome({
    task_id: testCase.taskID,
    result: {
      post_check: {
        handoff: {
          status: testCase.outcomeStatus,
          success_device_codes: testCase.successDeviceCodes,
          manageable_count: testCase.manageableCount,
          registry_only_count: testCase.registryOnlyCount,
        },
      },
    },
  });

  assert.equal(outcome.taskID, testCase.taskID, `${testCase.id} should preserve task_id`);
  assert.equal(outcome.codes.length, testCase.successDeviceCodes.length, `${testCase.id} should preserve success_device_codes`);
  assert.equal(outcome.manageableCount + outcome.registryOnlyCount, outcome.codes.length, `${testCase.id} should keep handoff counts consistent with visible success devices`);
  assert.equal(outcome.canNavigateToManagement, true, `${testCase.id} should support management navigation`);
}

console.log('d2 ingest submit visibility contract smoke passed');
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npx esbuild scripts/d2-ingest-submit-visibility-contract-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-ingest-submit-visibility-contract-smoke.mjs >/dev/null && node .tmp/d2-ingest-submit-visibility-contract-smoke.mjs`

Expected: FAIL if any contract case or outcome mapping does not yet satisfy the counts rule.

- [ ] **Step 3: Write minimal implementation**

If the smoke fails, update `OneOPS-UI/src/views/device/device-v2-ingest-flow-outcome.ts` so counts and codes are normalized consistently:

```ts
const codes = Array.isArray(successDeviceCodes)
  ? successDeviceCodes.map(value => String(value || '').trim()).filter(Boolean)
  : [];
const manageableCount = Number(handoff.manageable_count || 0);
const registryOnlyCount = Number(handoff.registry_only_count || 0);
const normalizedTotal = codes.length;

return {
  status,
  codes,
  taskID,
  manageableCount: manageableCount || (status === 'success' ? normalizedTotal : manageableCount),
  registryOnlyCount,
  canNavigateToManagement: !!taskID && normalizedTotal > 0,
};
```

Keep the implementation minimal: only normalize what the smoke proves is missing.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npx esbuild scripts/d2-ingest-submit-visibility-contract-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-ingest-submit-visibility-contract-smoke.mjs >/dev/null && node .tmp/d2-ingest-submit-visibility-contract-smoke.mjs`

Expected: PASS with `d2 ingest submit visibility contract smoke passed`

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git add scripts/d2-ingest-submit-visibility-contract-smoke.ts src/views/device/device-v2-ingest-flow-outcome.ts src/views/device/device-v2-import/draft-submit-contract.ts
git commit -m "test: verify ingest submit visibility contract"
```

### Task 7: 把管理页可见性合同固化成脚本断言

**Files:**
- Modify: `OneOPS-UI/scripts/d2-ingest-submit-visibility-contract-smoke.ts`
- Reference: `OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue`
- Reference: `OneOPS-UI/src/api/device/device-v2.ts`

- [ ] **Step 1: Write the failing test**

Append source assertions to `OneOPS-UI/scripts/d2-ingest-submit-visibility-contract-smoke.ts`:

```ts
import { readFileSync } from 'node:fs';
// keep the existing contract asserts above
const managementPage = readFileSync('src/views/device/DeviceV2ManagementGrouped.vue', 'utf8');
const apiModule = readFileSync('src/api/device/device-v2.ts', 'utf8');

assert.match(
  managementPage,
  /task_id: handoffTaskId\.value/,
  'management page should support task_id-scoped visibility fallback for handoff traffic',
);
assert.match(
  apiModule,
  /if \(params\.task_id\) query\.set\('task_id', params\.task_id\);/,
  'device v2 list API helper should serialize task_id into the list query',
);
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npx esbuild scripts/d2-ingest-submit-visibility-contract-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-ingest-submit-visibility-contract-smoke.mjs >/dev/null && node .tmp/d2-ingest-submit-visibility-contract-smoke.mjs`

Expected: FAIL if either the management page or API helper no longer carries the `task_id` visibility contract.

- [ ] **Step 3: Write minimal implementation**

If the smoke fails, restore the task-scoped fallback exactly where the contract expects it:

In `OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue`, keep or restore:

```ts
  const handoffScopeParams =
    scopedCodes.length === 0 && handoffTaskId.value
      ? ({ task_id: handoffTaskId.value } satisfies Pick<DeviceV2ListReq, 'task_id'>)
      : {};
```

In `OneOPS-UI/src/api/device/device-v2.ts`, keep or restore:

```ts
  if (params.task_id) query.set('task_id', params.task_id);
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npx esbuild scripts/d2-ingest-submit-visibility-contract-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-ingest-submit-visibility-contract-smoke.mjs >/dev/null && node .tmp/d2-ingest-submit-visibility-contract-smoke.mjs`

Expected: PASS with `d2 ingest submit visibility contract smoke passed`

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git add scripts/d2-ingest-submit-visibility-contract-smoke.ts src/views/device/DeviceV2ManagementGrouped.vue src/api/device/device-v2.ts
git commit -m "test: enforce ingest visibility contract"
```

### Task 8: 新增真实端到端 smoke 骨架

**Files:**
- Create: `OneOPS-UI/scripts/d2-ingest-visibility-e2e-smoke.cjs`
- Modify: `OneOPS-UI/package.json`
- Reference: `OneOPS-UI/scripts/d2-ingest-buttons-smoke.cjs`
- Reference: `OneOPS-UI/scripts/d2-real-operation-smoke.cjs`

- [ ] **Step 1: Write the failing test**

Add the npm entry to `OneOPS-UI/package.json`:

```json
"smoke:d2-ingest-visibility-e2e": "node scripts/d2-ingest-visibility-e2e-smoke.cjs"
```

Create the script with an intentional failure:

```js
#!/usr/bin/env node
throw new Error('d2 ingest visibility e2e smoke not implemented');
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npm run smoke:d2-ingest-visibility-e2e`

Expected: FAIL with `d2 ingest visibility e2e smoke not implemented`

- [ ] **Step 3: Write minimal implementation**

Replace the skeleton with a contract-only smoke that proves the script is wired and documents the future browser flow:

```js
#!/usr/bin/env node
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const ingestSource = fs.readFileSync(path.join(__dirname, '..', 'src/views/device/DeviceV2IngestPipelineRedesign.vue'), 'utf8');
const handoffSource = fs.readFileSync(path.join(__dirname, '..', 'src/views/device/DeviceV2IngestSuccessHandoff.vue'), 'utf8');
const managementSource = fs.readFileSync(path.join(__dirname, '..', 'src/views/device/DeviceV2ManagementGrouped.vue'), 'utf8');

assert(ingestSource.includes('DeviceV2IngestSuccessHandoff'), 'ingest page should route to handoff on success');
assert(handoffSource.includes('task_id'), 'handoff page should carry task_id forward');
assert(managementSource.includes('handoffTaskId'), 'management page should consume handoff task visibility scope');

console.log('d2 ingest visibility e2e smoke passed (contract-only mode)');
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npm run smoke:d2-ingest-visibility-e2e`

Expected: PASS with `d2 ingest visibility e2e smoke passed (contract-only mode)`

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git add package.json scripts/d2-ingest-visibility-e2e-smoke.cjs
git commit -m "test: add ingest visibility e2e smoke scaffold"
```

### Task 9: 把首批三条真实主线写入 E2E smoke

**Files:**
- Modify: `OneOPS-UI/scripts/d2-ingest-visibility-e2e-smoke.cjs`
- Reference: `OneOPS-UI/scripts/d2-real-operation-smoke.cjs`
- Reference: `OneOPS-UI/scripts/d2-redesign-browser-smoke.cjs`
- Reference: `OneOPS-UI/scripts/d2-ingest-buttons-smoke.cjs`

- [ ] **Step 1: Write the failing test**

Replace the contract-only implementation with assertions for the three first-round scenarios:

```js
const scenarios = [
  { id: 'manageable-only', expected: { manageable: 1, registryOnly: 0 } },
  { id: 'registry-only', expected: { manageable: 0, registryOnly: 1 } },
  { id: 'mixed-manageable-and-registry', expected: { manageable: 2, registryOnly: 1 } },
];

for (const scenario of scenarios) {
  assert.fail(`browser scenario not implemented: ${scenario.id}`);
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npm run smoke:d2-ingest-visibility-e2e`

Expected: FAIL on `browser scenario not implemented`

- [ ] **Step 3: Write minimal implementation**

Implement the browser flow by adapting the waiting and evidence helpers from `d2-ingest-buttons-smoke.cjs` and `d2-real-operation-smoke.cjs`:

```js
async function runScenario(assertScenario) {
  // 1. Open the ingest page
  // 2. Seed the page with the scenario’s draft rows via the existing draft editor hooks or upload helper
  // 3. Wait for the page counters to show the expected manageable / registry-only counts
  // 4. Trigger submit
  // 5. Wait for the handoff page
  // 6. Verify handoff metrics
  // 7. Click through to management
  // 8. Verify all success codes appear in the management table or task-scoped result set
}

for (const scenario of scenarios) {
  await runScenario(scenario);
}
```

The implementation may stay in contract-only mode when required environment variables or a browser connection are missing, but it must still:

- report that it skipped real replay intentionally;
- keep the contract assertions from Task 8;
- fail if the code path needed for replay is missing.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npm run smoke:d2-ingest-visibility-e2e`

Expected: PASS in one of two modes:
- `d2 ingest visibility e2e smoke passed`
- or `d2 ingest visibility e2e smoke passed (contract-only mode)`

If a browser and target environment are configured, the preferred output is the full PASS mode with evidence files.

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git add scripts/d2-ingest-visibility-e2e-smoke.cjs
git commit -m "test: replay ingest visibility e2e scenarios"
```

### Task 10: 接线、验证、文档回写

**Files:**
- Modify: `OneOPS-UI/package.json`
- Modify: `docs/superpowers/specs/2026-06-22-oneops-device-v2-ingest-boundary-testing-design.md`
- Optionally Modify: `docs/superpowers/plans/2026-06-22-oneops-device-v2-ingest-boundary-testing-plan.md`
- Test: `OneOPS-UI/scripts/d2-ingest-boundary-classification-smoke.ts`
- Test: `OneOPS-UI/scripts/d2-ingest-submit-visibility-contract-smoke.ts`
- Test: `OneOPS-UI/scripts/d2-ingest-visibility-e2e-smoke.cjs`

- [ ] **Step 1: Write the failing test**

Add npm scripts for the two new TypeScript smokes if they are missing:

```json
"smoke:d2-ingest-boundary-classification": "npx esbuild scripts/d2-ingest-boundary-classification-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-ingest-boundary-classification-smoke.mjs >/dev/null && node .tmp/d2-ingest-boundary-classification-smoke.mjs",
"smoke:d2-ingest-submit-visibility-contract": "npx esbuild scripts/d2-ingest-submit-visibility-contract-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-ingest-submit-visibility-contract-smoke.mjs >/dev/null && node .tmp/d2-ingest-submit-visibility-contract-smoke.mjs"
```

Then run the three smoke commands in sequence:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
npm run smoke:d2-ingest-boundary-classification
npm run smoke:d2-ingest-submit-visibility-contract
npm run smoke:d2-ingest-visibility-e2e
```

Expected: FAIL until every script is wired into `package.json` and passing.

- [ ] **Step 2: Run test to verify it fails**

Run the three commands above exactly as written.

Expected: at least one command fails before the package wiring and final fixes are complete.

- [ ] **Step 3: Write minimal implementation**

Update `OneOPS-UI/package.json` with the final script wiring and add a short evidence note to the spec:

```md
## Validation Commands

- `npm run smoke:d2-ingest-boundary-classification`
- `npm run smoke:d2-ingest-submit-visibility-contract`
- `npm run smoke:d2-ingest-visibility-e2e`
```

Do not add new product behavior in this task. Only wire the verification entry points and document them.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
npm run smoke:d2-ingest-boundary-classification
npm run smoke:d2-ingest-submit-visibility-contract
npm run smoke:d2-ingest-visibility-e2e
npm run typecheck:d2
```

Expected:

- `d2 ingest boundary classification smoke passed`
- `d2 ingest submit visibility contract smoke passed`
- `d2 ingest visibility e2e smoke passed` or `d2 ingest visibility e2e smoke passed (contract-only mode)`
- `vue-tsc --noEmit -p tsconfig.d2.json --composite false` exits 0

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git add package.json scripts/d2-ingest-boundary-classification-smoke.ts scripts/d2-ingest-submit-visibility-contract-smoke.ts scripts/d2-ingest-visibility-e2e-smoke.cjs src/views/device/device-v2-import/draft-boundary.ts src/views/device/device-v2-import/draft-submit-contract.ts src/views/device/device-v2-import/useDeviceV2IngestDraft.ts src/views/device/device-v2-ingest-flow-outcome.ts src/views/device/DeviceV2IngestPipelineRedesign.vue src/views/device/DeviceV2ManagementGrouped.vue
git commit -m "test: add systematic ingest boundary coverage"
```

## Spec Coverage Check

- 分层处理规则：Task 1-4 将拦截 / 仅登记 / 可采集分类固化成可复用模块和 smoke。
- 提交合同：Task 5-7 通过合同样例和源码断言验证 handoff 结果、`task_id`、成功设备集合与管理页范围查询一致。
- 真实主线：Task 8-9 建立浏览器 E2E smoke，并回放纯可采集、纯仅登记、混合成功三条主线。
- 验证入口与文档：Task 10 把验证命令接入 `package.json`，并把命令写回 spec。

## Self-Review

- 本计划只覆盖一个子系统：Device V2 导入边界测试，不再拆成独立计划。
- 计划中没有使用模糊占空描述；每个代码步骤都给出目标文件和具体代码块。
- 所有后续任务都复用前面定义过的文件名、函数名和脚本名：
  - `draft-boundary.ts`
  - `d2-ingest-boundary-classification-smoke.ts`
  - `draft-submit-contract.ts`
  - `d2-ingest-submit-visibility-contract-smoke.ts`
  - `d2-ingest-visibility-e2e-smoke.cjs`
