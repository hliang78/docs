# Task Assetization E2E Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first end-to-end task assetization lane using the Ansible network configuration backup asset while keeping the UI/API model extensible for Shell, Terraform, Tofu, and Terragrunt assets.

**Architecture:** Treat task assetization as a common contract model with runtime-specific blocks. Backend work first verifies the existing contract, precheck, device-results, and config-backups APIs. Frontend work then adds typed API helpers, device-level parent task results, device backup history, and a contract-aware task asset start flow.

**Tech Stack:** Go, Gin, GORM, Vue 3, TypeScript, Ant Design Vue, Vite, Playwright smoke checks, existing OneOps task center APIs.

---

## File Structure

### Backend Verification

- Read: `/OneOPS/OneOps/app/platform/dto/task_asset_precheck.go`
  - Responsibility: source of truth for Ansible task asset precheck response.
- Read: `/OneOPS/OneOps/app/platform/dto/task_device_result.go`
  - Responsibility: source of truth for parent task device result response.
- Read: `/OneOPS/OneOps/app/platform/dto/device_config_backup.go`
  - Responsibility: source of truth for device config backup history response.
- Read: `/OneOPS/OneOps/app/platform/api/task_api.go`
  - Responsibility: task device results, runtime artifacts, and platform device config backup endpoints.
- Read: `/OneOPS/OneOps/app/device/v2/api/device_v2_config_backup.go`
  - Responsibility: canonical device v2 config backup endpoint.

### Frontend API And Types

- Modify: `/OneOPS/OneOps-UI/src/typings/platform/task_template.ts`
  - Responsibility: expose common asset metadata fields on task templates.
- Modify: `/OneOPS/OneOps-UI/src/typings/platform/task.ts`
  - Responsibility: add task asset precheck and task device result TypeScript interfaces.
- Modify: `/OneOPS/OneOps-UI/src/api/platform/task.ts`
  - Responsibility: add request helpers for Ansible precheck and parent task device results.
- Modify: `/OneOPS/OneOps-UI/src/api/device/device-v2.ts`
  - Responsibility: add request helper and interfaces for device config backup history.

### Frontend Surfaces

- Modify: `/OneOPS/OneOps-UI/src/views/platform/TaskManagement.vue`
  - Responsibility: add device results tab to the existing task detail drawer and load `device-results`.
- Modify: `/OneOPS/OneOps-UI/src/views/device/DeviceV2ManagementGrouped.vue`
  - Responsibility: add config backup block to the existing device detail drawer.
- Modify: `/OneOPS/OneOps-UI/src/views/platform/TaskTemplateManagement.vue`
  - Responsibility: show task asset contract metadata and add a precheck-driven network backup start flow.
- Create: `/OneOPS/OneOps-UI/src/views/platform/task-asset-prefill.ts`
  - Responsibility: pass ready device codes from the task asset precheck drawer to the existing task creation modal.

### Verification Artifacts

- Create: `/OneOPS/docs/superpowers/acceptance/2026-06-06-task-assetization-e2e-checklist.md`
  - Responsibility: record backend, frontend, security, and E2E acceptance evidence for the first lane.

---

## Task 1: Verify Backend Asset APIs

**Files:**
- Read: `/OneOPS/OneOps/app/platform/dto/task_asset_precheck.go`
- Read: `/OneOPS/OneOps/app/platform/dto/task_device_result.go`
- Read: `/OneOPS/OneOps/app/platform/dto/device_config_backup.go`
- Read: `/OneOPS/OneOps/app/platform/api/task_api.go`
- Read: `/OneOPS/OneOps/app/device/v2/api/device_v2_config_backup.go`
- Test: `/OneOPS/OneOps/app/platform/api/task_api_test.go`
- Test: `/OneOPS/OneOps/app/device/v2/api/device_v2_test.go`
- Test: `/OneOPS/OneOps/app/platform/service/impl/task_asset_precheck_test.go`
- Test: `/OneOPS/OneOps/app/platform/service/impl/task_device_results_test.go`
- Test: `/OneOPS/OneOps/app/platform/service/impl/device_config_backup_projection_test.go`

- [ ] **Step 1: Confirm DTO response fields**

Run:

```bash
sed -n '1,120p' /OneOPS/OneOps/app/platform/dto/task_asset_precheck.go
sed -n '1,120p' /OneOPS/OneOps/app/platform/dto/task_device_result.go
sed -n '1,120p' /OneOPS/OneOps/app/platform/dto/device_config_backup.go
```

Expected fields:

```text
TaskAssetPrecheckResp: total, ready, blocked, warning, items.
TaskDeviceResultsResp: task_id, total_devices, executable_devices, blocked_devices, success_devices, failed_devices, archived_backups, failure_reasons, items.
DeviceConfigBackupListResp: list, total, page, page_size.
```

- [ ] **Step 2: Run focused backend tests**

Run from `/OneOPS/OneOps`:

```bash
go test ./app/platform/service/impl -run 'Test(TaskAssetPrecheck|TaskQueryServiceV2_GetTaskDeviceResults|DeviceConfigBackup)' -count=1
go test ./app/platform/api -run 'Test(TaskAssetPrecheckAPI|TestTaskAPI_GetTaskDeviceResults|TestTaskAPI_ListDeviceConfigBackups)' -count=1
go test ./app/device/v2/api -run TestDeviceV2APIListConfigBackups -count=1
```

Expected:

```text
All three go test commands exit 0.
```

- [ ] **Step 3: Record backend API readiness**

Append the following section to `/OneOPS/docs/superpowers/acceptance/2026-06-06-task-assetization-e2e-checklist.md`:

Run:

```bash
mkdir -p /OneOPS/docs/superpowers/acceptance
```

Then create or append:

```markdown
## Backend API Readiness

- [ ] `TaskAssetPrecheckResp` fields confirmed.
- [ ] `TaskDeviceResultsResp` fields confirmed.
- [ ] `DeviceConfigBackupListResp` fields confirmed.
- [ ] Focused service tests passed.
- [ ] Focused API tests passed.
```

- [ ] **Step 4: Commit acceptance checklist if created**

Run:

```bash
git -C /OneOPS/docs add superpowers/acceptance/2026-06-06-task-assetization-e2e-checklist.md
git -C /OneOPS/docs commit -m "docs: start task assetization acceptance checklist"
```

Expected:

```text
Commit succeeds if the checklist was newly created or changed.
```

---

## Task 2: Add Frontend Types And API Helpers

**Files:**
- Modify: `/OneOPS/OneOps-UI/src/typings/platform/task_template.ts`
- Modify: `/OneOPS/OneOps-UI/src/typings/platform/task.ts`
- Modify: `/OneOPS/OneOps-UI/src/api/platform/task.ts`
- Modify: `/OneOPS/OneOps-UI/src/api/device/device-v2.ts`

- [ ] **Step 1: Add asset metadata fields to task template types**

Modify `/OneOPS/OneOps-UI/src/typings/platform/task_template.ts` so `TaskTemplateResp`, `TaskTemplateCreateReq`, and `TaskTemplateUpdateReq` include:

```ts
  contract_json?: string;
  asset_category?: string;
  risk_level?: string;
  lifecycle_status?: string;
```

Expected insertion in each interface:

```ts
export interface TaskTemplateResp {
  id: string;
  name: string;
  description?: string;
  app_type?: string;
  variable_set_id?: string;
  playbook_path?: string;
  inventory_content?: string;
  inventory_grouping_selection_set_id?: string;
  repo_url?: string;
  repo_branch?: string;
  extra_vars_json?: string;
  parameter_specs?: ParameterSpecV2[];
  arguments?: string;
  run_on_agent?: boolean;
  agent_code?: string;
  runtime_contract_enabled?: boolean;
  runtime_data_scopes?: string[];
  runtime_api_base?: string;
  runtime_token_expires_seconds?: number;
  credential_ref?: string;
  contract_json?: string;
  asset_category?: string;
  risk_level?: string;
  lifecycle_status?: string;
  created_at: string;
  updated_at: string;
}
```

- [ ] **Step 2: Add task asset response types**

Add these interfaces to `/OneOPS/OneOps-UI/src/typings/platform/task.ts` after `CreateTaskResp`:

```ts
export type TaskAssetPrecheckStatus = 'ready' | 'blocked' | 'warning' | string;

export interface TaskAssetPrecheckReq {
  device_codes: string[];
  access_plane: 'in_band' | 'out_band' | string;
  credential_ref?: string;
}

export interface TaskAssetPrecheckResp {
  total: number;
  ready: number;
  blocked: number;
  warning: number;
  items: TaskAssetPrecheckItemResp[];
}

export interface TaskAssetPrecheckItemResp {
  device_code: string;
  status: TaskAssetPrecheckStatus;
  access_plane?: string;
  target_address?: string;
  vendor_family?: string;
  ansible_connection?: string;
  ansible_network_os?: string;
  credential_ref?: string;
  credential_source?: string;
  reason?: string;
}

export interface TaskDeviceResultsResp {
  task_id: string;
  total_devices: number;
  executable_devices: number;
  blocked_devices: number;
  success_devices: number;
  failed_devices: number;
  archived_backups: number;
  failure_reasons: Record<string, number>;
  items: TaskDeviceResultItemResp[];
}

export interface TaskDeviceResultItemResp {
  device_code: string;
  child_task_id?: string;
  status: string;
  backup_status?: string;
  archived: boolean;
  artifact_name?: string;
  artifact_storage_key?: string;
  artifact_sha256?: string;
  artifact_download_url?: string;
  config_hash?: string;
  vendor_family?: string;
  access_plane?: string;
  failure_reason?: string;
  backup_time?: string;
}
```

- [ ] **Step 3: Add platform task request helpers**

Modify imports in `/OneOPS/OneOps-UI/src/api/platform/task.ts` to include the new types:

```ts
  TaskAssetPrecheckReq,
  TaskAssetPrecheckResp,
  TaskDeviceResultsResp,
```

Add these helpers after `getTaskRuntimeOutputReq`:

```ts
export const precheckAnsibleTaskAssetReq = async (templateID: string, data: TaskAssetPrecheckReq) => {
  return request<TaskAssetPrecheckResp>({
    url: `/platform/task-assets/${encodeURIComponent(templateID)}/ansible/precheck`,
    method: HTTP_POST,
    data,
  });
};

export const getTaskDeviceResultsReq = async (taskID: string) => {
  return request<TaskDeviceResultsResp>({
    url: `${TASKS_BASE}/${encodeURIComponent(taskID)}/device-results`,
    method: HTTP_GET,
  });
};
```

- [ ] **Step 4: Add device config backup types and helper**

Add these interfaces near the other response interfaces in `/OneOPS/OneOps-UI/src/api/device/device-v2.ts`:

```ts
export interface DeviceConfigBackupListResp {
  list: DeviceConfigBackupResp[];
  total: number;
  page: number;
  page_size: number;
}

export interface DeviceConfigBackupResp {
  id: string;
  device_code: string;
  task_id: string;
  parent_task_id?: string;
  run_id?: string;
  controller_id?: string;
  vendor_family?: string;
  access_plane?: string;
  backup_status: string;
  backup_time: string;
  artifact_name?: string;
  artifact_storage_key?: string;
  artifact_size?: number;
  artifact_sha256?: string;
  config_hash?: string;
  summary_json?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}
```

Add this request helper near the existing `getDeviceV2Req` or other detail helpers:

```ts
export const listDeviceV2ConfigBackupsReq = async (
  code: string,
  params?: {
    page?: number;
    page_size?: number;
  },
) => {
  return request<DeviceConfigBackupListResp>({
    url: `${BASE}/${encodeURIComponent(code)}/config-backups`,
    method: HTTP_GET,
    params: params ?? {},
  });
};
```

- [ ] **Step 5: Run frontend typecheck**

Run from `/OneOPS/OneOps-UI`:

```bash
npm run typecheck
```

Expected:

```text
vue-tsc exits 0.
```

- [ ] **Step 6: Commit frontend API/type helpers**

Run:

```bash
git -C /OneOPS/OneOps-UI add \
  src/typings/platform/task_template.ts \
  src/typings/platform/task.ts \
  src/api/platform/task.ts \
  src/api/device/device-v2.ts
git -C /OneOPS/OneOps-UI commit -m "feat: add task assetization frontend api types"
```

Expected:

```text
Commit succeeds with only the four frontend type/API files staged.
```

---

## Task 3: Add Task Detail Device Results Tab

**Files:**
- Modify: `/OneOPS/OneOps-UI/src/views/platform/TaskManagement.vue`

- [ ] **Step 1: Import API and type**

Modify the import from `@/api/platform/task` to include:

```ts
  getTaskDeviceResultsReq,
```

Modify the import from `@/typings/platform/task` to include:

```ts
  TaskDeviceResultsResp,
  TaskDeviceResultItemResp,
```

- [ ] **Step 2: Add device results drawer state**

Extend the `logDrawer` reactive type and default object with:

```ts
  deviceResults: TaskDeviceResultsResp | null;
  deviceResultsLoading: boolean;
  deviceResultsError: string;
```

Default values:

```ts
  deviceResults: null,
  deviceResultsLoading: false,
  deviceResultsError: '',
```

Reset these fields in `openLogDrawer` with:

```ts
  logDrawer.deviceResults = null;
  logDrawer.deviceResultsLoading = false;
  logDrawer.deviceResultsError = '';
```

- [ ] **Step 3: Add loader**

Add this function near `loadRuntimeOutput`:

```ts
async function loadTaskDeviceResults(taskID: string) {
  logDrawer.deviceResults = null;
  logDrawer.deviceResultsError = '';
  logDrawer.deviceResultsLoading = true;
  try {
    logDrawer.deviceResults = await getTaskDeviceResultsReq(taskID);
  } catch (e) {
    const msg = e instanceof Error ? e.message : '加载设备结果失败';
    logDrawer.deviceResultsError = msg;
  } finally {
    logDrawer.deviceResultsLoading = false;
  }
}
```

- [ ] **Step 4: Wire tab change**

Modify `onDrawerTabChange`:

```ts
function onDrawerTabChange(key: string) {
  if (key === 'pipeline' && logDrawer.taskId) {
    loadPipeline(logDrawer.taskId);
  }
  if (key === 'runtime' && logDrawer.taskId) {
    loadRuntimeOutput(logDrawer.taskId);
  }
  if (key === 'device-results' && logDrawer.taskId) {
    loadTaskDeviceResults(logDrawer.taskId);
  }
}
```

- [ ] **Step 5: Add summary helpers**

Add these helpers near other formatting helpers:

```ts
function deviceResultStatusColor(status?: string) {
  const normalized = String(status || '').toLowerCase();
  if (normalized === 'success') return 'success';
  if (normalized === 'failed') return 'error';
  if (normalized === 'blocked') return 'warning';
  if (normalized === 'running' || normalized === 'pending') return 'processing';
  return 'default';
}

function formatDeviceResultStatus(status?: string) {
  const normalized = String(status || '').toLowerCase();
  if (normalized === 'success') return '成功';
  if (normalized === 'failed') return '失败';
  if (normalized === 'blocked') return '阻断';
  if (normalized === 'running') return '执行中';
  if (normalized === 'pending') return '待执行';
  return status || '-';
}

function deviceResultArtifactLabel(record: TaskDeviceResultItemResp) {
  return record.artifact_name || record.artifact_sha256 || record.artifact_storage_key || '-';
}
```

- [ ] **Step 6: Add device-results tab markup**

Add this `<a-tab-pane>` after the existing runtime tab and before the pipeline tab:

```vue
<a-tab-pane key="device-results" tab="设备结果">
  <div v-if="logDrawer.deviceResultsLoading" class="text-gray-500">加载中...</div>
  <div v-else-if="logDrawer.deviceResultsError" class="task-info-bar task-info-bar--error">
    {{ logDrawer.deviceResultsError }}
  </div>
  <template v-else-if="logDrawer.deviceResults">
    <div class="device-result-summary">
      <div class="device-result-summary__item">
        <span>总设备</span>
        <strong>{{ logDrawer.deviceResults.total_devices }}</strong>
      </div>
      <div class="device-result-summary__item">
        <span>可执行</span>
        <strong>{{ logDrawer.deviceResults.executable_devices }}</strong>
      </div>
      <div class="device-result-summary__item">
        <span>阻断</span>
        <strong>{{ logDrawer.deviceResults.blocked_devices }}</strong>
      </div>
      <div class="device-result-summary__item">
        <span>成功</span>
        <strong>{{ logDrawer.deviceResults.success_devices }}</strong>
      </div>
      <div class="device-result-summary__item">
        <span>失败</span>
        <strong>{{ logDrawer.deviceResults.failed_devices }}</strong>
      </div>
      <div class="device-result-summary__item">
        <span>已归档</span>
        <strong>{{ logDrawer.deviceResults.archived_backups }}</strong>
      </div>
    </div>

    <div v-if="Object.keys(logDrawer.deviceResults.failure_reasons || {}).length" class="runtime-section">
      <div class="runtime-section-title">失败原因分布</div>
      <a-space wrap>
        <a-tag
          v-for="(count, reason) in logDrawer.deviceResults.failure_reasons"
          :key="reason"
          color="error"
        >
          {{ reason }} × {{ count }}
        </a-tag>
      </a-space>
    </div>

    <a-table
      :columns="deviceResultColumns"
      :data-source="logDrawer.deviceResults.items"
      :row-key="(record: TaskDeviceResultItemResp) => record.device_code"
      size="small"
      :pagination="{ pageSize: 10 }"
      :scroll="{ x: 1100 }"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <a-tag :color="deviceResultStatusColor((record as TaskDeviceResultItemResp).status)">
            {{ formatDeviceResultStatus((record as TaskDeviceResultItemResp).status) }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'child_task_id'">
          <a
            v-if="(record as TaskDeviceResultItemResp).child_task_id"
            class="task-id-link"
            @click="openLogDrawer({ task_id: (record as TaskDeviceResultItemResp).child_task_id!, status: 'unknown' })"
          >
            {{ (record as TaskDeviceResultItemResp).child_task_id }}
          </a>
          <span v-else>-</span>
        </template>
        <template v-else-if="column.key === 'artifact'">
          <span :title="deviceResultArtifactLabel(record as TaskDeviceResultItemResp)">
            {{ deviceResultArtifactLabel(record as TaskDeviceResultItemResp) }}
          </span>
        </template>
        <template v-else-if="column.key === 'backup_time'">
          {{ (record as TaskDeviceResultItemResp).backup_time ? formatTime((record as TaskDeviceResultItemResp).backup_time!) : '-' }}
        </template>
        <template v-else-if="column.key === 'failure_reason'">
          <span class="text-danger">{{ (record as TaskDeviceResultItemResp).failure_reason || '-' }}</span>
        </template>
      </template>
    </a-table>
  </template>
  <div v-else class="text-gray-500">暂无设备维度结果。</div>
</a-tab-pane>
```

Add this column definition near other column definitions:

```ts
const deviceResultColumns = [
  { title: '设备', dataIndex: 'device_code', key: 'device_code', width: 140 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '子任务', dataIndex: 'child_task_id', key: 'child_task_id', width: 220 },
  { title: '访问平面', dataIndex: 'access_plane', key: 'access_plane', width: 100 },
  { title: '厂商族', dataIndex: 'vendor_family', key: 'vendor_family', width: 140 },
  { title: '产物', key: 'artifact', width: 240 },
  { title: '配置 Hash', dataIndex: 'config_hash', key: 'config_hash', width: 180 },
  { title: '备份时间', key: 'backup_time', width: 170 },
  { title: '失败原因', dataIndex: 'failure_reason', key: 'failure_reason', width: 260 },
];
```

- [ ] **Step 7: Add drawer tab styles**

Add CSS near the existing runtime/pipeline styles:

```css
.device-result-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(112px, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}

.device-result-summary__item {
  padding: 10px 12px;
  border: 1px solid #edf0f5;
  border-radius: 6px;
  background: #fafbfc;
}

.device-result-summary__item span {
  display: block;
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
}

.device-result-summary__item strong {
  display: block;
  color: rgba(0, 0, 0, 0.88);
  font-size: 20px;
  line-height: 1.2;
  margin-top: 4px;
}
```

- [ ] **Step 8: Run frontend verification**

Run from `/OneOPS/OneOps-UI`:

```bash
npm run typecheck
npm run build:force
```

Expected:

```text
Both commands exit 0.
```

- [ ] **Step 9: Commit task detail device results**

Run:

```bash
git -C /OneOPS/OneOps-UI add src/views/platform/TaskManagement.vue
git -C /OneOPS/OneOps-UI commit -m "feat: show task device results"
```

Expected:

```text
Commit succeeds with only TaskManagement.vue staged.
```

---

## Task 4: Add Device Config Backup History To Device Detail

**Files:**
- Modify: `/OneOPS/OneOps-UI/src/views/device/DeviceV2ManagementGrouped.vue`

- [ ] **Step 1: Import helper and types**

Modify imports from `@/api/device/device-v2` to include:

```ts
  listDeviceV2ConfigBackupsReq,
  type DeviceConfigBackupResp,
  type DeviceConfigBackupListResp,
```

- [ ] **Step 2: Add backup history state**

Add state near the existing detail drawer state:

```ts
const selectedDeviceConfigBackups = ref<DeviceConfigBackupResp[]>([]);
const selectedDeviceConfigBackupsTotal = ref(0);
const selectedDeviceConfigBackupsLoading = ref(false);
const selectedDeviceConfigBackupsError = ref('');
```

- [ ] **Step 3: Add backup history loader**

Add this function near `loadDeviceDetail`:

```ts
async function loadSelectedDeviceConfigBackups(code: string) {
  selectedDeviceConfigBackups.value = [];
  selectedDeviceConfigBackupsTotal.value = 0;
  selectedDeviceConfigBackupsError.value = '';
  selectedDeviceConfigBackupsLoading.value = true;
  try {
    const resp = await listDeviceV2ConfigBackupsReq(code, { page: 1, page_size: 10 });
    selectedDeviceConfigBackups.value = resp.list || [];
    selectedDeviceConfigBackupsTotal.value = resp.total || 0;
  } catch (error) {
    selectedDeviceConfigBackupsError.value =
      error instanceof Error ? error.message : '加载配置备份历史失败';
  } finally {
    selectedDeviceConfigBackupsLoading.value = false;
  }
}
```

- [ ] **Step 4: Load backups when device detail opens**

Modify the device selection path that calls `loadDeviceDetail(normalized, opts)` so it also calls:

```ts
await loadSelectedDeviceConfigBackups(normalized);
```

Reset backup state in `closeDetail`:

```ts
selectedDeviceConfigBackups.value = [];
selectedDeviceConfigBackupsTotal.value = 0;
selectedDeviceConfigBackupsError.value = '';
selectedDeviceConfigBackupsLoading.value = false;
```

- [ ] **Step 5: Add summary helpers**

Add:

```ts
const latestSelectedDeviceConfigBackup = computed(() => selectedDeviceConfigBackups.value[0] || null);

function configBackupStatusColor(status?: string) {
  const normalized = String(status || '').toLowerCase();
  if (normalized === 'success' || normalized === 'completed') return 'success';
  if (normalized === 'failed' || normalized === 'error') return 'error';
  if (normalized === 'running') return 'processing';
  return 'default';
}

function formatConfigBackupStatus(status?: string) {
  const normalized = String(status || '').toLowerCase();
  if (normalized === 'success' || normalized === 'completed') return '成功';
  if (normalized === 'failed' || normalized === 'error') return '失败';
  if (normalized === 'running') return '执行中';
  return status || '-';
}

function formatConfigBackupSize(size?: number) {
  if (!size || size <= 0) return '-';
  return formatBytes(size);
}
```

- [ ] **Step 6: Add config backup block to detail drawer**

Add this section after the structured detail sections and before device operations:

```vue
<section class="detail-block">
  <div class="detail-block__title">配置备份</div>
  <a-spin :spinning="selectedDeviceConfigBackupsLoading">
    <div v-if="selectedDeviceConfigBackupsError" class="task-info-bar task-info-bar--error">
      {{ selectedDeviceConfigBackupsError }}
    </div>
    <template v-else-if="latestSelectedDeviceConfigBackup">
      <div class="config-backup-summary">
        <div>
          <span>最近状态</span>
          <a-tag :color="configBackupStatusColor(latestSelectedDeviceConfigBackup.backup_status)">
            {{ formatConfigBackupStatus(latestSelectedDeviceConfigBackup.backup_status) }}
          </a-tag>
        </div>
        <div>
          <span>最近时间</span>
          <strong>{{ formatDisplayDateTime(latestSelectedDeviceConfigBackup.backup_time) }}</strong>
        </div>
        <div>
          <span>任务</span>
          <strong>{{ latestSelectedDeviceConfigBackup.task_id || '-' }}</strong>
        </div>
        <div>
          <span>配置 Hash</span>
          <strong>{{ latestSelectedDeviceConfigBackup.config_hash || '-' }}</strong>
        </div>
      </div>
      <a-table
        size="small"
        :columns="configBackupColumns"
        :data-source="selectedDeviceConfigBackups"
        :row-key="(record: DeviceConfigBackupResp) => record.id || `${record.task_id}-${record.backup_time}`"
        :pagination="false"
        :scroll="{ x: 900 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'backup_status'">
            <a-tag :color="configBackupStatusColor((record as DeviceConfigBackupResp).backup_status)">
              {{ formatConfigBackupStatus((record as DeviceConfigBackupResp).backup_status) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'backup_time'">
            {{ formatDisplayDateTime((record as DeviceConfigBackupResp).backup_time) }}
          </template>
          <template v-else-if="column.key === 'artifact_size'">
            {{ formatConfigBackupSize((record as DeviceConfigBackupResp).artifact_size) }}
          </template>
          <template v-else-if="column.key === 'error_message'">
            <span class="text-danger">{{ (record as DeviceConfigBackupResp).error_message || '-' }}</span>
          </template>
        </template>
      </a-table>
    </template>
    <a-empty v-else :image="false" description="当前设备暂无配置备份记录" />
  </a-spin>
</section>
```

Add columns near other table columns:

```ts
const configBackupColumns = [
  { title: '时间', dataIndex: 'backup_time', key: 'backup_time', width: 170 },
  { title: '状态', dataIndex: 'backup_status', key: 'backup_status', width: 90 },
  { title: '任务 ID', dataIndex: 'task_id', key: 'task_id', width: 220 },
  { title: '访问平面', dataIndex: 'access_plane', key: 'access_plane', width: 100 },
  { title: '厂商族', dataIndex: 'vendor_family', key: 'vendor_family', width: 120 },
  { title: '产物', dataIndex: 'artifact_name', key: 'artifact_name', width: 220 },
  { title: '大小', dataIndex: 'artifact_size', key: 'artifact_size', width: 90 },
  { title: '配置 Hash', dataIndex: 'config_hash', key: 'config_hash', width: 180 },
  { title: '错误', dataIndex: 'error_message', key: 'error_message', width: 220 },
];
```

- [ ] **Step 7: Add config backup styles**

Add:

```css
.config-backup-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}

.config-backup-summary > div {
  padding: 8px 10px;
  border: 1px solid #edf0f5;
  border-radius: 6px;
  background: #fafbfc;
}

.config-backup-summary span {
  display: block;
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
  margin-bottom: 4px;
}

.config-backup-summary strong {
  display: block;
  min-width: 0;
  overflow: hidden;
  color: rgba(0, 0, 0, 0.88);
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

- [ ] **Step 8: Run frontend verification**

Run from `/OneOPS/OneOps-UI`:

```bash
npm run typecheck
npm run build:force
```

Expected:

```text
Both commands exit 0.
```

- [ ] **Step 9: Commit device config backup history**

Run:

```bash
git -C /OneOPS/OneOps-UI add src/views/device/DeviceV2ManagementGrouped.vue
git -C /OneOPS/OneOps-UI commit -m "feat: show device config backup history"
```

Expected:

```text
Commit succeeds with only DeviceV2ManagementGrouped.vue staged.
```

---

## Task 5: Add Contract-Aware Asset Detail And Precheck Start Flow

**Files:**
- Modify: `/OneOPS/OneOps-UI/src/views/platform/TaskTemplateManagement.vue`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/TaskManagement.vue`
- Create: `/OneOPS/OneOps-UI/src/views/platform/task-asset-prefill.ts`

- [ ] **Step 1: Add asset detection helpers**

Add helpers near existing template display helpers:

```ts
function isAssetTemplate(record?: TaskTemplateResp | null) {
  return Boolean(
    record?.contract_json ||
      record?.asset_category ||
      record?.risk_level ||
      record?.lifecycle_status,
  );
}

function isNetworkConfigBackupAsset(record?: TaskTemplateResp | null) {
  const text = [
    record?.id,
    record?.name,
    record?.playbook_path,
    record?.asset_category,
    record?.contract_json,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();
  return record?.app_type === 'ansible' && text.includes('network-config-backup');
}

function parseTemplateContract(record?: TaskTemplateResp | null) {
  const raw = record?.contract_json?.trim();
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Record<string, unknown>;
  } catch {
    return null;
  }
}
```

Add this formatting helper if it does not already exist in `TaskTemplateManagement.vue`:

```ts
function jsonText(value: unknown) {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value ?? '');
  }
}
```

- [ ] **Step 2: Create task asset prefill bridge**

Create `/OneOPS/OneOps-UI/src/views/platform/task-asset-prefill.ts`:

```ts
export const TASK_ASSET_PREFILL_STORAGE_KEY = 'oneops.task.asset.prefill';
export const TASK_ASSET_PREFILL_QUERY_VALUE = 'task_asset_network_backup';

export interface TaskAssetPrefillPayload {
  source: 'task_asset';
  template_id: string;
  device_codes: string[];
  access_plane: 'in_band' | 'out_band';
  credential_ref?: string;
  created_at: number;
}

export interface BrowserLikeStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

function normalizeStringList(values: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const value of values) {
    const normalized = String(value || '').trim();
    if (!normalized || seen.has(normalized)) continue;
    seen.add(normalized);
    out.push(normalized);
  }
  return out;
}

export function writeTaskAssetPrefill(storage: BrowserLikeStorage, payload: TaskAssetPrefillPayload): void {
  storage.setItem(TASK_ASSET_PREFILL_STORAGE_KEY, JSON.stringify(payload));
}

export function readTaskAssetPrefill(storage: BrowserLikeStorage): TaskAssetPrefillPayload | null {
  const raw = storage.getItem(TASK_ASSET_PREFILL_STORAGE_KEY);
  storage.removeItem(TASK_ASSET_PREFILL_STORAGE_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<TaskAssetPrefillPayload>;
    const deviceCodes = normalizeStringList(Array.isArray(parsed.device_codes) ? parsed.device_codes : []);
    const templateID = String(parsed.template_id || '').trim();
    if (parsed.source !== 'task_asset' || !templateID || deviceCodes.length === 0) {
      return null;
    }
    return {
      source: 'task_asset',
      template_id: templateID,
      device_codes: deviceCodes,
      access_plane: parsed.access_plane === 'out_band' ? 'out_band' : 'in_band',
      credential_ref: String(parsed.credential_ref || '').trim() || undefined,
      created_at: Number(parsed.created_at || 0),
    };
  } catch {
    return null;
  }
}
```

- [ ] **Step 3: Teach TaskManagement to consume task asset prefill**

Modify `/OneOPS/OneOps-UI/src/views/platform/TaskManagement.vue`.

Add imports:

```ts
import {
  TASK_ASSET_PREFILL_QUERY_VALUE,
  readTaskAssetPrefill,
} from '@/views/platform/task-asset-prefill';
```

Modify `prefillCreateModalFromQuery` after the grouping prefill branch:

```ts
  if (prefillKey === TASK_ASSET_PREFILL_QUERY_VALUE && typeof window !== 'undefined') {
    const prefill = readTaskAssetPrefill(window.sessionStorage);
    if (prefill?.device_codes.length) {
      if (prefill.template_id) {
        await onTemplateSelect(prefill.template_id);
      }
      patchCreateForm({
        app_type: 'ansible',
        ansible_target_mode: 'devices',
        template_id: prefill.template_id || createModal.form.template_id,
        device_codes: prefill.device_codes,
        access_plane: prefill.access_plane,
        credential_ref: prefill.credential_ref || createModal.form.credential_ref,
        inventory_content: '',
        inventory_grouping_selection_set_id: undefined,
      });
      await loadDeviceOptions();
      message.success(`已从任务资产预检带入 ${prefill.device_codes.length} 台可执行设备`);
    } else {
      message.warning('未读取到任务资产预填数据，请返回任务资产重新发起');
    }
  }
```

- [ ] **Step 4: Add detail drawer state**

Add:

```ts
const assetDetail = reactive<{
  visible: boolean;
  record: TaskTemplateResp | null;
}>({
  visible: false,
  record: null,
});

function openAssetDetail(record: TaskTemplateResp) {
  assetDetail.record = record;
  assetDetail.visible = true;
}

function closeAssetDetail() {
  assetDetail.visible = false;
  assetDetail.record = null;
}
```

- [ ] **Step 5: Add asset detail action**

In the table action group, add before edit:

```vue
<a v-if="isAssetTemplate(record as TaskTemplateResp)" @click="openAssetDetail(record as TaskTemplateResp)">
  资产详情
</a>
```

- [ ] **Step 6: Add asset detail drawer**

Add after the table and before the existing form modal:

```vue
<a-drawer
  v-model:visible="assetDetail.visible"
  title="任务资产详情"
  width="720px"
  placement="right"
  destroy-on-close
  @close="closeAssetDetail"
>
  <template v-if="assetDetail.record">
    <a-descriptions bordered :column="1" size="small">
      <a-descriptions-item label="资产名称">{{ assetDetail.record.name }}</a-descriptions-item>
      <a-descriptions-item label="模板 ID">{{ assetDetail.record.id }}</a-descriptions-item>
      <a-descriptions-item label="Runtime">{{ assetDetail.record.app_type || '-' }}</a-descriptions-item>
      <a-descriptions-item label="资产分类">{{ assetDetail.record.asset_category || '-' }}</a-descriptions-item>
      <a-descriptions-item label="风险等级">{{ assetDetail.record.risk_level || '-' }}</a-descriptions-item>
      <a-descriptions-item label="生命周期">{{ assetDetail.record.lifecycle_status || '-' }}</a-descriptions-item>
      <a-descriptions-item label="入口">{{ assetDetail.record.playbook_path || '-' }}</a-descriptions-item>
      <a-descriptions-item label="仓库">
        {{ assetDetail.record.repo_url || '-' }} @ {{ assetDetail.record.repo_branch || '-' }}
      </a-descriptions-item>
      <a-descriptions-item label="凭据引用">{{ assetDetail.record.credential_ref || '设备绑定优先' }}</a-descriptions-item>
    </a-descriptions>
    <div class="asset-contract-block">
      <div class="asset-contract-block__title">运行契约</div>
      <pre>{{ jsonText(parseTemplateContract(assetDetail.record) || {}) }}</pre>
    </div>
    <a-space wrap>
      <a-button
        v-if="isNetworkConfigBackupAsset(assetDetail.record)"
        type="primary"
        @click="openNetworkBackupStart(assetDetail.record)"
      >
        发起备份
      </a-button>
      <a-button @click="assetDetail.record && openCreateTask(assetDetail.record)">创建任务</a-button>
      <a-button @click="assetDetail.record && openCreateSchedule(assetDetail.record)">新建定时</a-button>
    </a-space>
  </template>
</a-drawer>
```

- [ ] **Step 7: Add precheck start state**

Import `precheckAnsibleTaskAssetReq` from `@/api/platform/task`, `listDevicesReq` from `@/api/platform/device`, `type DeviceListItem` from `@/typings/platform/device`, and these types from `@/typings/platform/task`:

```ts
import type {
  TaskAssetPrecheckItemResp,
  TaskAssetPrecheckResp,
} from '@/typings/platform/task';
```

Import the prefill bridge:

```ts
import {
  TASK_ASSET_PREFILL_QUERY_VALUE,
  writeTaskAssetPrefill,
} from '@/views/platform/task-asset-prefill';
```

Add state:

```ts
const networkBackupStart = reactive<{
  visible: boolean;
  template: TaskTemplateResp | null;
  deviceCodes: string[];
  accessPlane: 'in_band' | 'out_band';
  credentialRef: string;
  precheck: TaskAssetPrecheckResp | null;
  precheckLoading: boolean;
  precheckStale: boolean;
}>({
  visible: false,
  template: null,
  deviceCodes: [],
  accessPlane: 'in_band',
  credentialRef: '',
  precheck: null,
  precheckLoading: false,
  precheckStale: false,
});

const assetDeviceOptions = ref<DeviceListItem[]>([]);
const assetDeviceOptionsLoading = ref(false);

function openNetworkBackupStart(record: TaskTemplateResp) {
  networkBackupStart.visible = true;
  networkBackupStart.template = record;
  networkBackupStart.deviceCodes = [];
  networkBackupStart.accessPlane = 'in_band';
  networkBackupStart.credentialRef = record.credential_ref || '';
  networkBackupStart.precheck = null;
  networkBackupStart.precheckLoading = false;
  networkBackupStart.precheckStale = false;
  loadAssetDeviceOptions();
}

function markNetworkBackupPrecheckStale() {
  if (networkBackupStart.precheck) networkBackupStart.precheckStale = true;
}
```

Add the device option loader:

```ts
async function loadAssetDeviceOptions() {
  assetDeviceOptionsLoading.value = true;
  try {
    const res = await listDevicesReq({ page: 1, pageSize: 500 });
    const payload = (res as { list?: DeviceListItem[]; data?: { list?: DeviceListItem[] } }) || {};
    assetDeviceOptions.value = Array.isArray(payload.list) ? payload.list : payload.data?.list || [];
  } catch {
    assetDeviceOptions.value = [];
    message.error('加载设备列表失败');
  } finally {
    assetDeviceOptionsLoading.value = false;
  }
}
```

- [ ] **Step 8: Add precheck action**

Add:

```ts
async function runNetworkBackupPrecheck() {
  if (!networkBackupStart.template) return;
  if (!networkBackupStart.deviceCodes.length) {
    message.warning('请先选择设备');
    return;
  }
  networkBackupStart.precheckLoading = true;
  try {
    networkBackupStart.precheck = await precheckAnsibleTaskAssetReq(networkBackupStart.template.id, {
      device_codes: networkBackupStart.deviceCodes,
      access_plane: networkBackupStart.accessPlane,
      credential_ref: networkBackupStart.credentialRef || undefined,
    });
    networkBackupStart.precheckStale = false;
  } catch (error) {
    message.error(error instanceof Error ? error.message : '设备预检失败');
  } finally {
    networkBackupStart.precheckLoading = false;
  }
}

const networkBackupReadyDeviceCodes = computed(() =>
  (networkBackupStart.precheck?.items || [])
    .filter(item => item.status === 'ready' || item.status === 'warning')
    .map(item => item.device_code),
);
```

Add the precheck table columns:

```ts
const assetPrecheckColumns = [
  { title: '设备', dataIndex: 'device_code', key: 'device_code', width: 140 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '访问平面', dataIndex: 'access_plane', key: 'access_plane', width: 100 },
  { title: '目标地址', dataIndex: 'target_address', key: 'target_address', width: 140 },
  { title: '厂商族', dataIndex: 'vendor_family', key: 'vendor_family', width: 130 },
  { title: '连接', dataIndex: 'ansible_connection', key: 'ansible_connection', width: 140 },
  { title: '凭据来源', dataIndex: 'credential_source', key: 'credential_source', width: 130 },
  { title: '原因', dataIndex: 'reason', key: 'reason', width: 260 },
];
```

Add the function that opens the existing task creation modal through route prefill:

```ts
function submitNetworkBackupReadyDevices() {
  if (!networkBackupStart.template) return;
  if (!networkBackupReadyDeviceCodes.value.length) {
    message.warning('当前没有可提交设备');
    return;
  }
  if (networkBackupStart.precheckStale) {
    message.warning('预检结果已过期，请重新预检');
    return;
  }
  if (typeof window !== 'undefined') {
    writeTaskAssetPrefill(window.sessionStorage, {
      source: 'task_asset',
      template_id: networkBackupStart.template.id,
      device_codes: networkBackupReadyDeviceCodes.value,
      access_plane: networkBackupStart.accessPlane,
      credential_ref: networkBackupStart.credentialRef || undefined,
      created_at: Date.now(),
    });
  }
  router.push({
    name: 'TaskManagement',
    query: {
      openCreate: '1',
      templateId: networkBackupStart.template.id,
      prefill: TASK_ASSET_PREFILL_QUERY_VALUE,
    },
  });
}
```

- [ ] **Step 9: Add start drawer markup**

Add:

```vue
<a-drawer
  v-model:visible="networkBackupStart.visible"
  title="发起网络配置备份"
  width="860px"
  placement="right"
  destroy-on-close
>
  <a-form layout="vertical">
    <a-form-item label="任务资产">
      <a-input :value="networkBackupStart.template?.name || '-'" disabled />
    </a-form-item>
    <a-form-item label="访问平面">
      <a-radio-group v-model:value="networkBackupStart.accessPlane" button-style="solid" @change="markNetworkBackupPrecheckStale">
        <a-radio-button value="in_band">带内</a-radio-button>
        <a-radio-button value="out_band">带外</a-radio-button>
      </a-radio-group>
    </a-form-item>
    <a-form-item label="兜底凭据">
      <a-select
        v-model:value="networkBackupStart.credentialRef"
        allow-clear
        placeholder="设备绑定优先，任务凭据作为兜底"
        @change="markNetworkBackupPrecheckStale"
      >
        <a-select-option v-for="c in credentialOptions" :key="c.code" :value="c.code">
          {{ c.name }} ({{ c.code }})
        </a-select-option>
      </a-select>
    </a-form-item>
    <a-form-item label="目标设备">
      <a-select
        v-model:value="networkBackupStart.deviceCodes"
        mode="multiple"
        show-search
        allow-clear
        placeholder="选择设备"
        :loading="assetDeviceOptionsLoading"
        @change="markNetworkBackupPrecheckStale"
      >
        <a-select-option v-for="device in assetDeviceOptions" :key="device.code" :value="device.code">
          {{ device.code }} · {{ device.ip || '-' }} · {{ device.function_area || '-' }}
        </a-select-option>
      </a-select>
    </a-form-item>
  </a-form>
  <a-space class="mb-3" wrap>
    <a-button type="primary" :loading="networkBackupStart.precheckLoading" @click="runNetworkBackupPrecheck">
      执行预检
    </a-button>
    <a-tag v-if="networkBackupStart.precheckStale" color="warning">预检已过期</a-tag>
  </a-space>
  <div v-if="networkBackupStart.precheck" class="asset-precheck-summary">
    <a-tag color="processing">总数 {{ networkBackupStart.precheck.total }}</a-tag>
    <a-tag color="success">可执行 {{ networkBackupStart.precheck.ready }}</a-tag>
    <a-tag color="warning">阻断 {{ networkBackupStart.precheck.blocked }}</a-tag>
    <a-tag color="gold">提醒 {{ networkBackupStart.precheck.warning }}</a-tag>
  </div>
  <a-table
    v-if="networkBackupStart.precheck"
    size="small"
    :columns="assetPrecheckColumns"
    :data-source="networkBackupStart.precheck.items"
    :row-key="(record: TaskAssetPrecheckItemResp) => record.device_code"
    :pagination="{ pageSize: 8 }"
    :scroll="{ x: 960 }"
  />
  <template #footer>
    <a-space>
      <a-button @click="networkBackupStart.visible = false">关闭</a-button>
      <a-button
        type="primary"
        :disabled="!networkBackupReadyDeviceCodes.length || networkBackupStart.precheckStale"
        @click="submitNetworkBackupReadyDevices"
      >
        提交可执行设备
      </a-button>
    </a-space>
  </template>
</a-drawer>
```

- [ ] **Step 10: Run frontend verification**

Run from `/OneOPS/OneOps-UI`:

```bash
npm run typecheck
npm run build:force
```

Expected:

```text
Both commands exit 0.
```

- [ ] **Step 11: Commit asset detail and precheck start flow**

Run:

```bash
git -C /OneOPS/OneOps-UI add \
  src/views/platform/TaskTemplateManagement.vue \
  src/views/platform/TaskManagement.vue \
  src/views/platform/task-asset-prefill.ts
git -C /OneOPS/OneOps-UI commit -m "feat: add task asset precheck start flow"
```

Expected:

```text
Commit succeeds with only TaskTemplateManagement.vue, TaskManagement.vue, and task-asset-prefill.ts staged.
```

---

## Task 6: End-To-End Acceptance And Security Review

**Files:**
- Modify: `/OneOPS/docs/superpowers/acceptance/2026-06-06-task-assetization-e2e-checklist.md`
- Read: `/OneOPS/docs/superpowers/specs/2026-06-06-task-assetization-e2e-acceptance-design.md`
- Read: `/OneOPS/docs/superpowers/ANSIBLE_TASK_ASSETIZATION_MVP_DESIGN_20260606.md`

- [ ] **Step 1: Run final backend verification**

Run from `/OneOPS/OneOps`:

```bash
go test ./app/platform/service/impl -run 'Test(TaskAssetPrecheck|TaskQueryServiceV2_GetTaskDeviceResults|DeviceConfigBackup|BuildChildExecutionEnvelopeForDevice|BuildTaskDeviceInventoryContent)' -count=1
go test ./app/platform/api -run 'Test(TaskAssetPrecheckAPI|TestTaskAPI_GetTaskDeviceResults|TestTaskAPI_ListDeviceConfigBackups|TestTaskAPI_.*RuntimeArtifact)' -count=1
go test ./app/device/v2/api -run TestDeviceV2APIListConfigBackups -count=1
```

Expected:

```text
All backend verification commands exit 0.
```

- [ ] **Step 2: Run final frontend verification**

Run from `/OneOPS/OneOps-UI`:

```bash
npm run typecheck
npm run build:force
```

Expected:

```text
Both frontend verification commands exit 0.
```

- [ ] **Step 3: Inspect secret leakage patterns**

Run:

```bash
rg -n "ansible_password|ansible_ssh_pass|ansible_become_password|private_key|token|auth_pass|password" \
  /OneOPS/OneOps-UI/src/views/platform/TaskManagement.vue \
  /OneOPS/OneOps-UI/src/views/platform/TaskTemplateManagement.vue \
  /OneOPS/OneOps-UI/src/views/device/DeviceV2ManagementGrouped.vue \
  /OneOPS/OneOps-UI/src/typings/platform/task.ts \
  /OneOPS/OneOps-UI/src/api/platform/task.ts \
  /OneOPS/OneOps-UI/src/api/device/device-v2.ts
```

Expected:

```text
No UI code renders resolved secret fields. Allowed matches are explanatory labels such as credential_ref or forbidden-field names inside documentation comments.
```

- [ ] **Step 4: Perform browser smoke**

Run the dev server from `/OneOPS/OneOps-UI`:

```bash
npm run dev
```

Then use Playwright or manual browser verification for:

```text
Task template list opens.
Network backup asset detail drawer opens.
Network backup precheck drawer opens.
Task detail drawer opens.
Device results tab renders empty, loading, or populated states without layout breakage.
Device detail drawer opens.
Config backup section renders empty, loading, or populated states without layout breakage.
```

Expected:

```text
No console error blocks page rendering.
Tables fit inside drawers at desktop width.
Sensitive cfg content is not previewed inline.
```

- [ ] **Step 5: Record acceptance evidence**

Append:

Run:

```bash
mkdir -p /OneOPS/docs/superpowers/acceptance
```

Then append:

```markdown
## E2E Acceptance Evidence

- [ ] Backend focused tests passed.
- [ ] Frontend typecheck passed.
- [ ] Frontend build passed.
- [ ] Secret leakage inspection completed.
- [ ] Task asset detail browser smoke completed.
- [ ] Task device results browser smoke completed.
- [ ] Device config backup browser smoke completed.

## Remaining Risks

- Artifact download permission behavior still requires a real permission-denied case if no fixture exists.
- First-lane implementation proves Ansible network backup; Shell and IaC lanes are framework-ready but not fully implemented.
```

- [ ] **Step 6: Commit acceptance evidence**

Run:

```bash
git -C /OneOPS/docs add superpowers/acceptance/2026-06-06-task-assetization-e2e-checklist.md
git -C /OneOPS/docs commit -m "docs: record task assetization e2e acceptance"
```

Expected:

```text
Commit succeeds if acceptance evidence changed.
```
