# Device V2 Frontend CRUD Testing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add repeatable frontend tests for Device V2 add, update, and delete behavior around `/device/device-v2-management`.

**Architecture:** Use Playwright under the existing `OneOps/scripts/platform2_multi_agent_test` harness. Seed and clean deterministic Device V2 records through authenticated backend API calls using the UI login token, then exercise the actual Device V2 management UI for edit and delete; treat creation as two layers because the current management page does not expose a direct create form and routes users through the import page.

**Tech Stack:** Vue 3, Ant Design Vue, Playwright, TypeScript, OneOps Device V2 API.

---

## Scope And Product Reality

- Primary page under test: `OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue`.
- Route under test: `/#/device/device-v2-management`.
- API client under test: `OneOPS-UI/src/api/device/device-v2.ts`.
- Backend route contract: `GET /api/v1/device/v2/list`, `GET /api/v1/device/v2/:code`, `PUT /api/v1/device/v2/:code`, `DELETE /api/v1/device/v2/:code`.
- Direct create API exists as `POST /api/v1/device/v2`, but the frontend API marks it deprecated and the backend router says the current pages should prefer the import page.
- Current management page exposes `设备导入`, `编辑`, and `批量删除`, but it does not expose a direct `新增设备` modal.

## Test Strategy

- P0 CRUD management safety:
  - Seed one deterministic Device V2 record through API setup.
  - Open the management UI and prove the seeded record is visible.
  - Edit the record through the UI `操作 -> 编辑` modal.
  - Assert the UI sends `PUT /device/v2/:code` and the saved value appears after reload.
  - Delete the record through UI row selection and `批量删除`.
  - Assert the UI sends `DELETE /device/v2/:code`, clears selection, reloads, and the record disappears.
- P0 add-entry contract:
  - Open the management UI and click `设备导入`.
  - Assert navigation reaches `/#/device/device-v2-ingest-pipeline-redesign`.
  - Assert there is no misleading direct create entry on the management page.
- P1 import creation flow:
  - Cover real frontend "新增" through `DeviceV2IngestPipelineRedesign.vue` in a separate spec once the import page's stable controls and minimal valid payload are confirmed.

## File Structure

- Create: `OneOps/scripts/platform2_multi_agent_test/shared/device_v2_api.ts`
  - Small authenticated Playwright API helpers for deterministic Device V2 seed, read, delete, and cleanup.
- Create: `OneOps/scripts/platform2_multi_agent_test/agents/device_v2_frontend_crud.spec.ts`
  - Playwright UI tests for Device V2 management add-entry, edit, and delete.
- Modify: `OneOps/scripts/platform2_multi_agent_test/package.json`
  - Add a targeted `test:device-v2:crud` script.

## Test Data Contract

- Code prefix: `E2E_D2_CRUD_`.
- Runtime code: `E2E_D2_CRUD_${Date.now()}`.
- Initial record:

```json
{
  "code": "E2E_D2_CRUD_<timestamp>",
  "name": "E2E Device V2 CRUD Seed",
  "platform_code": "linux",
  "status": "active",
  "labels": {
    "e2e": "device-v2-crud"
  },
  "attributes": {
    "platform_code": "linux",
    "catalog_code": "server",
    "site_code": "E2E_SITE",
    "rack_code": "E2E_RACK",
    "in_band_ip": "192.0.2.10"
  },
  "metadata": {
    "e2e_run": "device-v2-frontend-crud"
  },
  "group_tags": ["e2e", "crud"]
}
```

- Updated record assertions:
  - Name becomes `E2E Device V2 CRUD Updated`.
  - Label `e2e=device-v2-crud` remains present.
  - GET `/device/v2/:code` returns the updated name after UI save.
  - If `updated_at` is present before and after save, the value changes, following the persistence-check lesson from `docs/knowledge/oneops-teleabs-strategy-set-switch-update-lessons-2026-06-04.md`.

## Tasks

### Task 1: Add Device V2 API Test Helpers

**Files:**
- Create: `OneOps/scripts/platform2_multi_agent_test/shared/device_v2_api.ts`

- [x] Create the helper file with typed API envelopes and cleanup helpers.

```ts
import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';
import { API_BASE_URL } from './frontend_task_execution_real';

type ApiEnvelope<T> = {
  code?: number;
  msg?: string;
  data?: T;
};

export type DeviceV2Seed = {
  code: string;
  name: string;
  platform_code: string;
  status: string;
  labels: Record<string, string>;
  attributes: Record<string, unknown>;
  metadata: Record<string, unknown>;
  group_tags: string[];
};

export type DeviceV2Item = DeviceV2Seed & {
  id?: string;
  updated_at?: string;
};

export function buildDeviceV2CrudSeed(code: string): DeviceV2Seed {
  return {
    code,
    name: 'E2E Device V2 CRUD Seed',
    platform_code: 'linux',
    status: 'active',
    labels: { e2e: 'device-v2-crud' },
    attributes: {
      platform_code: 'linux',
      catalog_code: 'server',
      site_code: 'E2E_SITE',
      rack_code: 'E2E_RACK',
      in_band_ip: '192.0.2.10',
    },
    metadata: { e2e_run: 'device-v2-frontend-crud' },
    group_tags: ['e2e', 'crud'],
  };
}

async function deviceV2ApiRequest<T>(
  page: Page,
  token: string,
  method: 'GET' | 'POST' | 'DELETE',
  apiPath: string,
  body?: unknown,
): Promise<ApiEnvelope<T> | null> {
  const resp = await page.request.fetch(`${API_BASE_URL}${apiPath}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-Auth-Token': token,
    },
    data: body,
  });
  if (resp.status() === 404) return null;
  expect(resp.ok(), `${method} ${apiPath}`).toBeTruthy();
  return (await resp.json()) as ApiEnvelope<T>;
}

export async function getDeviceV2(page: Page, token: string, code: string): Promise<DeviceV2Item | null> {
  const body = await deviceV2ApiRequest<DeviceV2Item>(page, token, 'GET', `/device/v2/${encodeURIComponent(code)}`);
  if (!body) return null;
  if (body.code !== 0) return null;
  return body.data ?? null;
}

export async function ensureDeviceV2(page: Page, token: string, seed: DeviceV2Seed): Promise<DeviceV2Item> {
  const existing = await getDeviceV2(page, token, seed.code);
  if (existing) {
    await deleteDeviceV2IfExists(page, token, seed.code);
  }
  const body = await deviceV2ApiRequest<DeviceV2Item>(page, token, 'POST', '/device/v2?base_ref_mode=warn', seed);
  expect(body, `POST Device V2 ${seed.code} should return an API envelope`).toBeTruthy();
  expect(body.code, body.msg || 'create Device V2 should return code=0').toBe(0);
  expect(body.data?.code).toBe(seed.code);
  return body.data as DeviceV2Item;
}

export async function deleteDeviceV2IfExists(page: Page, token: string, code: string): Promise<void> {
  const existing = await getDeviceV2(page, token, code);
  if (!existing) return;
  const body = await deviceV2ApiRequest<DeviceV2Item>(page, token, 'DELETE', `/device/v2/${encodeURIComponent(code)}`);
  if (body) {
    expect(body.code, body.msg || 'delete Device V2 should return code=0').toBe(0);
  }
}
```

- [x] Run TypeScript compilation for the new Playwright files.

Run:

```bash
cd OneOps/scripts/platform2_multi_agent_test
npx tsc --noEmit --target ES2022 --module NodeNext --moduleResolution NodeNext --lib ES2022,DOM --types node,@playwright/test agents/device_v2_frontend_crud.spec.ts shared/device_v2_api.ts shared/playwright_login.ts shared/frontend_task_execution_real.ts
```

Expected: PASS.

### Task 2: Add Management Page Add-Entry Test

**Files:**
- Create: `OneOps/scripts/platform2_multi_agent_test/agents/device_v2_frontend_crud.spec.ts`

- [x] Add the first test case that verifies the current add entry routes to the import page.

```ts
import { test, expect } from '@playwright/test';
import { playwrightLogin } from '../shared/playwright_login';

test.describe('Device V2 frontend CRUD', () => {
  test('management page exposes import as the current add entry', async ({ page }) => {
    await playwrightLogin(page);
    await page.goto('/#/device/device-v2-management');
    await expect(page.getByRole('heading', { name: '设备清单' })).toBeVisible({ timeout: 60000 });

    await expect(page.getByRole('button', { name: '设备导入' })).toBeVisible();
    await expect(page.getByRole('button', { name: /新增设备|创建设备/ })).toHaveCount(0);

    await page.getByRole('button', { name: '设备导入' }).click();
    await expect(page).toHaveURL(/device-v2-ingest-pipeline-redesign/);
  });
});
```

- [x] Run only this test.

Run:

```bash
cd OneOps/scripts/platform2_multi_agent_test
ONEOPS_UI_URL=http://127.0.0.1:3001 ONEOPS_API_URL=http://127.0.0.1:8280/api/v1 npx playwright test agents/device_v2_frontend_crud.spec.ts -g 'add entry'
```

Expected: PASS when UI and backend are running.

### Task 3: Add UI Update Test

**Files:**
- Modify: `OneOps/scripts/platform2_multi_agent_test/agents/device_v2_frontend_crud.spec.ts`

- [x] Extend imports and add deterministic seed setup.

```ts
import { test, expect } from '@playwright/test';
import { playwrightLogin } from '../shared/playwright_login';
import { getAuthToken } from '../shared/frontend_task_execution_real';
import {
  buildDeviceV2CrudSeed,
  deleteDeviceV2IfExists,
  ensureDeviceV2,
  getDeviceV2,
} from '../shared/device_v2_api';
```

- [x] Add the update test.

```ts
test('edits a seeded Device V2 record through the management UI', async ({ page }) => {
  const code = `E2E_D2_CRUD_${Date.now()}`;
  await playwrightLogin(page);
  const token = await getAuthToken(page);
  await ensureDeviceV2(page, token, buildDeviceV2CrudSeed(code));
  const beforeUpdate = await getDeviceV2(page, token, code);
  expect(beforeUpdate?.name).toBe('E2E Device V2 CRUD Seed');

  try {
    await page.goto(`/#/device/device-v2-management?codes=${encodeURIComponent(code)}`);
    await expect(page.getByText(code)).toBeVisible({ timeout: 60000 });

    const row = page.locator('tr').filter({ hasText: code }).first();
    await row.getByRole('button', { name: '操作' }).click();
    await page.getByRole('menuitem', { name: '编辑' }).click();

    const dialog = page.getByRole('dialog', { name: '编辑设备' });
    await expect(dialog).toBeVisible();
    await dialog.getByLabel('设备名称').fill('E2E Device V2 CRUD Updated');

    const updateResponse = page.waitForResponse(
      (resp) =>
        resp.url().includes(`/api/v1/device/v2/${encodeURIComponent(code)}`) &&
        resp.request().method() === 'PUT',
    );
    await dialog.getByRole('button', { name: /^保存/ }).click();
    const resp = await updateResponse;
    expect(resp.ok()).toBeTruthy();

    await expect(page.getByText('E2E Device V2 CRUD Updated')).toBeVisible({ timeout: 60000 });
    const saved = await getDeviceV2(page, token, code);
    expect(saved?.name).toBe('E2E Device V2 CRUD Updated');
    expect(saved?.labels?.e2e).toBe('device-v2-crud');
    if (beforeUpdate?.updated_at && saved?.updated_at) {
      expect(saved.updated_at).not.toBe(beforeUpdate.updated_at);
    }
  } finally {
    await deleteDeviceV2IfExists(page, token, code);
  }
});
```

- [x] Run the update test.

Run:

```bash
cd OneOps/scripts/platform2_multi_agent_test
ONEOPS_UI_URL=http://127.0.0.1:3001 ONEOPS_API_URL=http://127.0.0.1:8280/api/v1 npx playwright test agents/device_v2_frontend_crud.spec.ts -g 'edits a seeded'
```

Expected: PASS; the test observes `PUT /api/v1/device/v2/<code>` and verifies the saved name through GET.

### Task 4: Add UI Delete Test

**Files:**
- Modify: `OneOps/scripts/platform2_multi_agent_test/agents/device_v2_frontend_crud.spec.ts`

- [x] Add the delete test.

```ts
test('deletes a seeded Device V2 record through batch delete UI', async ({ page }) => {
  const code = `E2E_D2_CRUD_${Date.now()}`;
  await playwrightLogin(page);
  const token = await getAuthToken(page);
  await ensureDeviceV2(page, token, buildDeviceV2CrudSeed(code));

  try {
    await page.goto(`/#/device/device-v2-management?codes=${encodeURIComponent(code)}`);
    await expect(page.getByText(code)).toBeVisible({ timeout: 60000 });

    const row = page.locator('tr').filter({ hasText: code }).first();
    await row.locator('input[type="checkbox"]').check({ force: true });
    await expect(page.getByRole('button', { name: '批量删除' })).toBeEnabled();
    await page.getByRole('button', { name: '批量删除' }).click();

    const deleteResponse = page.waitForResponse(
      (resp) =>
        resp.url().includes(`/api/v1/device/v2/${encodeURIComponent(code)}`) &&
        resp.request().method() === 'DELETE',
    );
    await page.getByRole('button', { name: '确认删除' }).click();
    const resp = await deleteResponse;
    expect(resp.ok()).toBeTruthy();

    await expect(page.getByText(code)).toHaveCount(0, { timeout: 60000 });
    const deleted = await getDeviceV2(page, token, code);
    expect(deleted).toBeNull();
  } finally {
    await deleteDeviceV2IfExists(page, token, code);
  }
});
```

- [x] Run the delete test.

Run:

```bash
cd OneOps/scripts/platform2_multi_agent_test
ONEOPS_UI_URL=http://127.0.0.1:3001 ONEOPS_API_URL=http://127.0.0.1:8280/api/v1 npx playwright test agents/device_v2_frontend_crud.spec.ts -g 'deletes a seeded'
```

Expected: PASS; the test observes `DELETE /api/v1/device/v2/<code>` and GET returns null or a non-zero envelope.

### Task 5: Add Package Script

**Files:**
- Modify: `OneOps/scripts/platform2_multi_agent_test/package.json`

- [x] Add the targeted script.

```json
"test:device-v2:crud": "playwright test agents/device_v2_frontend_crud.spec.ts"
```

- [x] Run the script.

Run:

```bash
cd OneOps/scripts/platform2_multi_agent_test
ONEOPS_UI_URL=http://127.0.0.1:3001 ONEOPS_API_URL=http://127.0.0.1:8280/api/v1 npm run test:device-v2:crud
```

Expected: PASS for all four tests.

### Task 6: Verification Matrix

**Files:**
- Verify only.

- [x] Frontend typecheck.

Run:

```bash
cd OneOPS-UI
npm run typecheck:d2
```

Expected: PASS.

- [x] Device V2 backend API and service regression.

Run:

```bash
cd OneOps
go test ./app/device/v2/api ./app/device/v2/service/impl -run 'TestDeviceV2|TestDeviceV2Srv' -count=1
```

Expected: PASS.

- [x] Full Device V2 backend regression after fixing the rack/site import expectation.

Run:

```bash
cd OneOps
go test ./app/device/v2/... -count=1
```

Expected: PASS.

- [x] Playwright CRUD regression.

Run:

```bash
cd OneOps/scripts/platform2_multi_agent_test
ONEOPS_UI_URL=http://127.0.0.1:3001 ONEOPS_API_URL=http://127.0.0.1:8280/api/v1 npm run test:device-v2:crud
```

Expected: PASS.

- [x] Platform integration regression focused on Device V2/monitoring/strategy touchpoints.

Run:

```bash
cd OneOps
go test ./app/platform/... -run 'Test.*(DeviceV2|EntityGrouping|DeploymentBidi|MonitoringTaskV3|Teleabs|Strategy)' -count=1
```

Expected: PASS.

## Manual Acceptance Checklist

- [x] `设备导入` opens the import route and the management page has no stale direct-create button.
- [x] Seeded record appears on `/#/device/device-v2-management?codes=<code>`.
- [x] `操作 -> 编辑` opens `编辑设备`.
- [x] Saving updates the record through `PUT /api/v1/device/v2/<code>`.
- [x] Required-field validation prevents saving if platform, device category, site, or rack are empty.
- [x] Batch delete confirmation displays Device V2 impact text.
- [x] Confirming delete calls `DELETE /api/v1/device/v2/<code>`.
- [x] Deleted record no longer appears after the table reloads.
- [x] Cleanup leaves no `E2E_D2_CRUD_` records.

## Execution Notes

- Local backend for this run was listening on `http://127.0.0.1:8280`; Vite on `http://127.0.0.1:3001` was already proxying to that backend.
- Playwright Chromium was installed with `npx playwright install chromium` because the local runner cache was missing.
- Ant Design Vue inserts spacing in short Chinese button text, so the update test matches `/操\s*作/`, `/编\s*辑/`, and `/保\s*存/`.
- The CRUD spec now has 4 tests: add/import entry, edit save, required-field save block, and batch delete.
- The previous `TestPageImportE2E_ApplyFailsWhenRackSiteHierarchyConflicts` expectation was stale. Import validation now resolves rack/site together and blocks the row during validation, so the test was renamed to `TestPageImportE2E_ValidateFailsWhenRackSiteHierarchyConflicts`.

## Self-Review

- Spec coverage: add-entry, update, required-field blocking, delete, deterministic setup, cleanup, API assertions, and UI assertions are covered.
- Placeholder scan: no forbidden placeholder tokens, no unresolved file paths, no vague testing steps.
- Type consistency: helpers use `DeviceV2Seed` and `DeviceV2Item`; tests import the same helper names used in Task 1.
