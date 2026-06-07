# Config Management Collection Task Center Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make configuration management able to create, execute, schedule, and manage configuration collection tasks for network devices and servers.

**Architecture:** Configuration versions remain the immutable facts. Collection tasks become the producer workflow owned by configuration management. Phase 1 reuses existing platform task, scheduled task, task template, and config version APIs, then Phase 2 can introduce `platform_config_collection_plan` if we need a persistent policy object with richer governance.

**Tech Stack:** Vue 3, Ant Design Vue, TypeScript, Go, GORM, MySQL, existing OneOPS platform task APIs, existing scheduled task APIs, existing config version APIs.

---

## Product Positioning

Configuration management should not be only a result viewer. It owns three first-class work objects:

- **Configuration versions:** immutable collected content, hash, baseline, diff, download, redacted view.
- **Collection tasks:** manual and scheduled jobs that produce configuration versions.
- **Collection scope:** asset type, asset range, access plane, collection template, credential source, runtime agent, and collection frequency.

The first implementation should keep the workflow concrete:

1. Operator enters configuration management.
2. Operator chooses network devices or servers.
3. Operator creates a one-time collection or scheduled collection.
4. System creates platform task or scheduled task using the correct template.
5. Operator sees task status and failed targets.
6. Successful runtime output is projected into config versions.
7. Operator views, downloads, compares, and sets baseline.

## Phase Split

### Phase 1: Task Center Inside Config Management

Use existing APIs and avoid a new backend table.

- Manual collection uses `POST /api/v1/platform/tasks`.
- Scheduled collection uses `POST /api/v1/platform/scheduled-tasks`.
- Scheduled task management uses existing list, enable, disable, update, delete, and recent-run APIs.
- One-time task history uses `GET /api/v1/platform/tasks?project_id=...&template_id=...`.
- Configuration page identifies config-management tasks by project id, template id, and extra vars marker.

This phase is enough for the operator to create and manage real backup jobs.

### Phase 2: First-Class Collection Plan

Add `platform_config_collection_plan` only after Phase 1 proves the shape.

Use it when we need:

- named policy ownership independent from `platform_scheduled_task`;
- target selectors that are not just explicit device codes;
- retention, baseline rules, and failure handling;
- plan audit and approval.

Phase 2 is not required to make the current workflow usable.

## File Structure

### Frontend

- Modify: `/OneOPS/OneOps-UI/src/views/device/DeviceConfigManagement.vue`
  - Add page-level mode between configuration versions and collection tasks.
  - Add task creation drawer.
  - Add collection task list and scheduled task list panels.
  - Keep current version queue behavior.

- Create: `/OneOPS/OneOps-UI/src/views/device/config-management/collectionTaskHelpers.ts`
  - Resolve network and server templates.
  - Build one-time `ExecutionEnvelopeV2`.
  - Build scheduled task request.
  - Group assets by asset type and access plane.
  - Produce user-facing labels.

- Create: `/OneOPS/OneOps-UI/src/views/device/config-management/collectionTaskHelpers.test.ts`
  - Unit test template resolution, grouping, task request shape, scheduled request shape.

- Modify: `/OneOPS/OneOps-UI/src/api/platform/scheduled_task.ts`
  - Keep existing calls.
  - Add no new backend dependency unless pagination or filtering is missing in practice.

- Modify: `/OneOPS/OneOps-UI/src/typings/platform/scheduled_task.ts`
  - Add local UI-only extension type if needed. Do not change backend contract unless backend changes.

### Backend

Phase 1 backend changes should be minimal.

- Modify only if needed: `/OneOPS/OneOps/app/platform/service/impl/scheduled_task_v2.go`
  - Ensure config collection scheduled tasks keep `device_codes`, `access_plane`, `run_on_agent`, `agent_code`, and `credential_ref`.

- Modify only if needed: `/OneOPS/OneOps/app/platform/service/impl/scheduled_task_runner.go`
  - Ensure scheduled config tasks create execution envelopes with `scheduled_task_id` and `triggered_by=scheduled`.

- Modify only if needed: `/OneOPS/OneOps/app/platform/api/task_api.go`
  - If one-time task list cannot be filtered enough, add query support for `triggered_by` or `project_id_prefix`.

- No new migration in Phase 1.

### Docs And Quick Env

- Modify: `/OneOPS/docs/superpowers/specs/2026-06-07-device-config-management-first-class-design.md`
  - Add collection task center section.
  - Document manual and scheduled collection workflows.

- Verify and modify as needed:
  - `/OneOPS/OneOps/quick_env/init-configs/gitea/source-repo/templates/task-template-catalog.json`
  - `/OneOPS/OneOps/quick_env/init-configs/gitea/source-repo/templates/variable-set-catalog.json`
  - `/OneOPS/OneOps/quick_env/init-configs/gitea/source-repo/ansible/server-config-collection/site.yml`

Quick env must keep both templates available:

- network config collection template: native netlink or Ansible network backup.
- server config collection template: `task-center-ansible-server-config-collection`.

## Data Markers

Use predictable values so the UI can filter tasks without a new table.

### Project IDs

```text
project-network-config-management
project-server-config-management
```

### Extra Vars Marker

For manual and scheduled config collection tasks, include:

```json
{
  "config_management": true,
  "config_asset_type": "network_device",
  "config_scope": "network_running_config",
  "collection_reason": "manual"
}
```

For server collection:

```json
{
  "config_management": true,
  "config_asset_type": "server",
  "config_scope": "server_system_snapshot",
  "collection_reason": "manual"
}
```

### Display Labels

Use user-facing labels only:

- `network_device` -> `网络设备`
- `server` -> `服务器`
- `in_band` -> `带内`
- `out_band` -> `带外`
- `first_backup` -> `首次采集`
- `no_change` -> `无变化`
- `changed` -> `有变化`
- `no_baseline` -> `未设基线`
- `matches_baseline` -> `符合基线`
- `drifted` -> `偏离基线`

Avoid labels such as `no_baseline`, `network_cli`, `server_system_snapshot` in the main UI.

## Task 1: Document The Collection Task Center

**Files:**
- Modify: `/OneOPS/docs/superpowers/specs/2026-06-07-device-config-management-first-class-design.md`

- [ ] **Step 1: Add a section named `Configuration Collection Task Center`**

Add this content after `Phase 1 Daily Operations`:

```markdown
## Configuration Collection Task Center

Configuration management owns the collection task lifecycle.

The task center covers:

- one-time collection for selected assets;
- scheduled collection for network devices and servers;
- task status and recent run review;
- failed target recollection;
- transition from task result to configuration version.

The first implementation reuses platform task and scheduled task APIs. Config management marks its tasks with project ids `project-network-config-management` and `project-server-config-management`, plus `config_management=true` in `extra_vars_json`.

The operator workflow is:

1. Select assets from the configuration version queue or task composer.
2. Choose collection mode: run once or schedule.
3. Confirm asset type, access plane, template, agent, and credential source.
4. Create the task.
5. Review task status and failed targets.
6. Open generated configuration versions from the same page.
```

- [ ] **Step 2: Run a doc sanity check**

Run:

```bash
rg -n "Configuration Collection Task Center|project-network-config-management|project-server-config-management" docs/superpowers/specs/2026-06-07-device-config-management-first-class-design.md
```

Expected: the new section and both project ids are found.

## Task 2: Add Collection Task Helper Module

**Files:**
- Create: `/OneOPS/OneOps-UI/src/views/device/config-management/collectionTaskHelpers.ts`
- Test: `/OneOPS/OneOps-UI/src/views/device/config-management/collectionTaskHelpers.test.ts`

- [ ] **Step 1: Create helper types**

Create `collectionTaskHelpers.ts` with these exported types:

```ts
import type { ConfigManagementAssetResp } from '@/api/device/device-v2';
import type { ExecutionEnvelopeV2 } from '@/typings/platform/task';
import type { CreateScheduledTaskReq } from '@/typings/platform/scheduled_task';
import type { TaskTemplateResp } from '@/typings/platform/task_template';

export type ConfigCollectionAssetType = 'network_device' | 'server';

export interface ConfigCollectionGroup {
  assetType: ConfigCollectionAssetType;
  accessPlane: 'in_band' | 'out_band';
  rows: ConfigManagementAssetResp[];
}

export interface ConfigCollectionBuildOptions {
  template: TaskTemplateResp;
  rows: ConfigManagementAssetResp[];
  assetType: ConfigCollectionAssetType;
  accessPlane: 'in_band' | 'out_band';
  reason: 'manual' | 'scheduled' | 'retry';
  cronExpr?: string;
}
```

- [ ] **Step 2: Add label helpers**

Add:

```ts
export const configCollectionProjectID = (assetType: ConfigCollectionAssetType) =>
  assetType === 'server' ? 'project-server-config-management' : 'project-network-config-management';

export const configCollectionScope = (assetType: ConfigCollectionAssetType) =>
  assetType === 'server' ? 'server_system_snapshot' : 'network_running_config';

export const configCollectionAssetTypeLabel = (assetType: ConfigCollectionAssetType) =>
  assetType === 'server' ? '服务器' : '网络设备';
```

- [ ] **Step 3: Add template resolution**

Add functions that prefer exact app types before fuzzy name matching:

```ts
const templateText = (template: TaskTemplateResp) =>
  [
    template.id,
    template.name,
    template.app_type,
    template.asset_category,
    template.playbook_path,
    template.description,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();

export const isNetworkConfigTemplate = (template: TaskTemplateResp) => {
  const appType = String(template.app_type || '').toLowerCase();
  if (appType === 'network_config_backup') return true;
  const text = templateText(template);
  return text.includes('network-config-backup') || text.includes('network_config_backup');
};

export const isServerConfigTemplate = (template: TaskTemplateResp) => {
  const appType = String(template.app_type || '').toLowerCase();
  if (appType === 'server_config_collection') return true;
  const text = templateText(template);
  return text.includes('server-config-collection') || text.includes('server_config_collection');
};

export const resolveConfigCollectionTemplate = (
  templates: TaskTemplateResp[],
  assetType: ConfigCollectionAssetType,
) => {
  const matcher = assetType === 'server' ? isServerConfigTemplate : isNetworkConfigTemplate;
  const candidates = templates.filter(matcher);
  return candidates.sort((a, b) => templatePriority(b, assetType) - templatePriority(a, assetType))[0];
};

const templatePriority = (template: TaskTemplateResp, assetType: ConfigCollectionAssetType) => {
  const appType = String(template.app_type || '').toLowerCase();
  const text = templateText(template);
  let score = 0;
  if (assetType === 'server' && appType === 'server_config_collection') score += 100;
  if (assetType === 'network_device' && appType === 'network_config_backup') score += 100;
  if (text.includes('native-network-config-backup-netlink')) score += 20;
  if (text.includes('server-config-collection')) score += 20;
  if (template.run_on_agent) score += 5;
  return score;
};
```

- [ ] **Step 4: Add asset grouping**

Add:

```ts
export const normalizeCollectionAssetType = (row: ConfigManagementAssetResp): ConfigCollectionAssetType => {
  const assetType = String(row.asset_type || '').toLowerCase();
  if (assetType === 'server') return 'server';
  return 'network_device';
};

export const normalizeAccessPlane = (row: ConfigManagementAssetResp): 'in_band' | 'out_band' => {
  const plane = String(row.collection_plane || row.access_plane || '').toLowerCase();
  return plane === 'out_band' ? 'out_band' : 'in_band';
};

export const groupConfigCollectionRows = (rows: ConfigManagementAssetResp[]): ConfigCollectionGroup[] => {
  const map = new Map<string, ConfigCollectionGroup>();
  rows.forEach(row => {
    const assetType = normalizeCollectionAssetType(row);
    const accessPlane = normalizeAccessPlane(row);
    const key = `${assetType}:${accessPlane}`;
    const current = map.get(key) || { assetType, accessPlane, rows: [] };
    current.rows.push(row);
    map.set(key, current);
  });
  return Array.from(map.values());
};
```

- [ ] **Step 5: Add request builders**

Add:

```ts
const uniqueCodes = (rows: ConfigManagementAssetResp[]) =>
  Array.from(
    new Set(
      rows
        .map(row => row.device_code || row.asset_code)
        .map(code => String(code || '').trim())
        .filter(Boolean),
    ),
  );

const configExtraVars = (assetType: ConfigCollectionAssetType, reason: 'manual' | 'scheduled' | 'retry') =>
  JSON.stringify({
    config_management: true,
    config_asset_type: assetType,
    config_scope: configCollectionScope(assetType),
    collection_reason: reason,
  });

export const buildConfigCollectionTaskEnvelope = (options: ConfigCollectionBuildOptions): ExecutionEnvelopeV2 => ({
  source: 'config_management_ui',
  scope: {
    project_id: configCollectionProjectID(options.assetType),
    function_area: 'DefaultArea',
    template_id: options.template.id,
    triggered_by: options.reason === 'retry' ? 'retry' : 'manual',
  },
  script: {
    app_type: options.template.app_type || (options.assetType === 'server' ? 'ansible' : 'network_config_backup'),
  },
  target: {
    device_codes: uniqueCodes(options.rows),
    access_plane: options.accessPlane,
  },
  params: {
    variable_set_id: options.template.variable_set_id,
    extra_vars_json: configExtraVars(options.assetType, options.reason),
  },
  runtime: {
    run_on_agent: options.template.run_on_agent !== false,
    agent_code: options.template.agent_code || 'agent-001',
  },
  credential: options.template.credential_ref ? { ref: options.template.credential_ref } : undefined,
});

export const buildConfigScheduledTaskRequest = (options: ConfigCollectionBuildOptions): CreateScheduledTaskReq => ({
  name: `${configCollectionAssetTypeLabel(options.assetType)}配置采集 ${options.accessPlane === 'out_band' ? '带外' : '带内'}`,
  template_id: options.template.id,
  project_id: configCollectionProjectID(options.assetType),
  function_area: 'DefaultArea',
  cron_expr: options.cronExpr || '0 0 2 * * *',
  enabled: true,
  variable_set_id: options.template.variable_set_id,
  device_codes: uniqueCodes(options.rows),
  access_plane: options.accessPlane,
  extra_vars_json: configExtraVars(options.assetType, 'scheduled'),
  run_on_agent: options.template.run_on_agent !== false,
  agent_code: options.template.agent_code || 'agent-001',
  credential_ref: options.template.credential_ref,
  ansible_target_mode: 'devices',
});
```

- [ ] **Step 6: Add helper tests**

Create tests that cover:

```ts
import {
  buildConfigCollectionTaskEnvelope,
  buildConfigScheduledTaskRequest,
  groupConfigCollectionRows,
  resolveConfigCollectionTemplate,
} from './collectionTaskHelpers';

describe('collectionTaskHelpers', () => {
  it('groups rows by asset type and access plane', () => {
    const groups = groupConfigCollectionRows([
      { asset_code: 'DVC1', asset_type: 'network_device', collection_plane: 'in_band' } as any,
      { asset_code: 'SRV1', asset_type: 'server', collection_plane: 'in_band' } as any,
      { asset_code: 'DVC2', asset_type: 'network_device', collection_plane: 'out_band' } as any,
    ]);

    expect(groups.map(group => `${group.assetType}:${group.accessPlane}`).sort()).toEqual([
      'network_device:in_band',
      'network_device:out_band',
      'server:in_band',
    ]);
  });

  it('prefers native network backup template', () => {
    const template = resolveConfigCollectionTemplate(
      [
        { id: 'ansible', name: 'network-config-backup', app_type: 'ansible' } as any,
        { id: 'native', name: 'task-center-native-network-config-backup-netlink', app_type: 'network_config_backup' } as any,
      ],
      'network_device',
    );

    expect(template?.id).toBe('native');
  });

  it('builds one-time server collection task envelope', () => {
    const envelope = buildConfigCollectionTaskEnvelope({
      template: { id: 'server-template', app_type: 'server_config_collection', run_on_agent: true, agent_code: 'agent-001' } as any,
      rows: [{ asset_code: 'SRV1', asset_type: 'server' } as any],
      assetType: 'server',
      accessPlane: 'in_band',
      reason: 'manual',
    });

    expect(envelope.scope?.project_id).toBe('project-server-config-management');
    expect(envelope.target?.device_codes).toEqual(['SRV1']);
    expect(envelope.params?.extra_vars_json).toContain('"config_management":true');
  });

  it('builds scheduled network collection request', () => {
    const req = buildConfigScheduledTaskRequest({
      template: { id: 'network-template', app_type: 'network_config_backup', run_on_agent: true } as any,
      rows: [{ asset_code: 'DVC1', asset_type: 'network_device' } as any],
      assetType: 'network_device',
      accessPlane: 'out_band',
      reason: 'scheduled',
      cronExpr: '0 0 3 * * *',
    });

    expect(req.project_id).toBe('project-network-config-management');
    expect(req.device_codes).toEqual(['DVC1']);
    expect(req.access_plane).toBe('out_band');
    expect(req.cron_expr).toBe('0 0 3 * * *');
  });
});
```

- [ ] **Step 7: Run frontend unit or type verification**

Run whichever test command exists in `package.json`. At minimum:

```bash
cd /OneOPS/OneOps-UI
npm run typecheck
```

Expected: typecheck passes.

## Task 3: Add Collection Task Mode To Config Management Page

**Files:**
- Modify: `/OneOPS/OneOps-UI/src/views/device/DeviceConfigManagement.vue`

- [ ] **Step 1: Add mode state**

In `<script setup>`, add:

```ts
type ConfigManagementMode = 'versions' | 'tasks';

const configManagementMode = ref<ConfigManagementMode>('versions');
```

- [ ] **Step 2: Add top segmented control**

Near the page header actions, add:

```vue
<a-segmented
  v-model:value="configManagementMode"
  :options="[
    { label: '配置版本', value: 'versions' },
    { label: '采集任务', value: 'tasks' },
  ]"
/>
```

- [ ] **Step 3: Wrap the existing version queue**

Wrap existing summary and version queue sections:

```vue
<template v-if="configManagementMode === 'versions'">
  <!-- existing summary, version queue, operation rail -->
</template>
```

- [ ] **Step 4: Add task mode shell**

Add:

```vue
<template v-else>
  <section class="config-management-main">
    <div class="config-management-main__head">
      <div>
        <h3>采集任务</h3>
      </div>
      <div class="config-management-main__tools">
        <a-button @click="loadConfigCollectionTasks">刷新</a-button>
        <a-button type="primary" @click="openCollectionTaskDrawer('manual')">新建采集</a-button>
        <a-button @click="openCollectionTaskDrawer('scheduled')">新建定时采集</a-button>
      </div>
    </div>
  </section>
</template>
```

- [ ] **Step 5: Keep copy action-oriented**

Do not add paragraphs explaining the feature. Use labels, counts, filters, and buttons:

- `采集任务`
- `新建采集`
- `新建定时采集`
- `失败任务`
- `最近运行`
- `启用`
- `禁用`

## Task 4: Implement One-Time Collection From Config Management

**Files:**
- Modify: `/OneOPS/OneOps-UI/src/views/device/DeviceConfigManagement.vue`
- Use: `/OneOPS/OneOps-UI/src/views/device/config-management/collectionTaskHelpers.ts`

- [ ] **Step 1: Import helpers**

Add:

```ts
import {
  buildConfigCollectionTaskEnvelope,
  groupConfigCollectionRows,
  resolveConfigCollectionTemplate,
} from './config-management/collectionTaskHelpers';
```

- [ ] **Step 2: Add drawer state**

Add:

```ts
const collectionDrawer = reactive({
  visible: false,
  mode: 'manual' as 'manual' | 'scheduled',
  selectedOnly: true,
  accessPlane: 'in_band' as 'in_band' | 'out_band',
  cronExpr: '0 0 2 * * *',
  loading: false,
});
```

- [ ] **Step 3: Add open function**

Add:

```ts
const openCollectionTaskDrawer = (mode: 'manual' | 'scheduled') => {
  collectionDrawer.mode = mode;
  collectionDrawer.visible = true;
};
```

- [ ] **Step 4: Add manual submit**

Add:

```ts
const submitManualCollection = async () => {
  const rows = selectedRows.value.length > 0 ? selectedRows.value : filteredRows.value;
  const groups = groupConfigCollectionRows(rows);
  if (groups.length === 0) {
    message.warning('请选择要采集的资产');
    return;
  }

  collectionDrawer.loading = true;
  try {
    await ensureConfigTaskTemplates();
    const created: string[] = [];
    const skipped: string[] = [];

    for (const group of groups) {
      const template = resolveConfigCollectionTemplate(taskTemplates.value, group.assetType);
      if (!template) {
        skipped.push(group.assetType === 'server' ? '服务器' : '网络设备');
        continue;
      }
      const resp = await createTaskReq(
        buildConfigCollectionTaskEnvelope({
          template,
          rows: group.rows,
          assetType: group.assetType,
          accessPlane: group.accessPlane,
          reason: 'manual',
        }),
      );
      if (resp?.task_id) created.push(resp.task_id);
    }

    if (created.length > 0) message.success(`已创建 ${created.length} 个采集任务`);
    if (skipped.length > 0) message.warning(`缺少${skipped.join('、')}采集模板`);
    collectionDrawer.visible = false;
    await loadConfigCollectionTasks();
  } finally {
    collectionDrawer.loading = false;
  }
};
```

- [ ] **Step 5: Verify selected and filtered row behavior**

Manual test:

1. Select one network device row.
2. Click `新建采集`.
3. Submit.
4. Confirm a platform task is created with project id `project-network-config-management`.
5. Select one server row.
6. Submit.
7. Confirm a platform task is created with project id `project-server-config-management`.

## Task 5: Implement Scheduled Collection Management

**Files:**
- Modify: `/OneOPS/OneOps-UI/src/views/device/DeviceConfigManagement.vue`
- Use: `/OneOPS/OneOps-UI/src/api/platform/scheduled_task.ts`
- Use: `/OneOPS/OneOps-UI/src/views/device/config-management/collectionTaskHelpers.ts`

- [ ] **Step 1: Import scheduled APIs**

Add:

```ts
import {
  createScheduledTaskReq,
  deleteScheduledTaskReq,
  disableScheduledTaskReq,
  enableScheduledTaskReq,
  listScheduledTasksReq,
  listScheduledTaskTasksReq,
} from '@/api/platform/scheduled_task';
```

- [ ] **Step 2: Add state**

Add:

```ts
const collectionScheduledTasks = ref<ScheduledTaskResp[]>([]);
const collectionScheduledTasksLoading = ref(false);
const collectionRecentRuns = reactive({
  visible: false,
  name: '',
  taskIds: [] as string[],
  loading: false,
});
```

- [ ] **Step 3: Load config scheduled tasks**

Add:

```ts
const loadConfigCollectionScheduledTasks = async () => {
  collectionScheduledTasksLoading.value = true;
  try {
    const [networkResp, serverResp] = await Promise.all([
      listScheduledTasksReq({ project_id: 'project-network-config-management', page: 1, page_size: 100 }),
      listScheduledTasksReq({ project_id: 'project-server-config-management', page: 1, page_size: 100 }),
    ]);
    collectionScheduledTasks.value = [...(networkResp?.list || []), ...(serverResp?.list || [])];
  } finally {
    collectionScheduledTasksLoading.value = false;
  }
};
```

- [ ] **Step 4: Add scheduled submit**

Use `buildConfigScheduledTaskRequest` and `createScheduledTaskReq`. The submit path must:

- require at least one target row;
- require a cron expression;
- create one scheduled task per asset type and access plane group;
- refresh the scheduled task list.

- [ ] **Step 5: Add list actions**

For each scheduled task row:

- `最近运行` calls `listScheduledTaskTasksReq`.
- `启用` calls `enableScheduledTaskReq`.
- `禁用` calls `disableScheduledTaskReq`.
- `删除` calls `deleteScheduledTaskReq`.

- [ ] **Step 6: Verify**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run typecheck
```

Manual test:

1. Create a scheduled network collection.
2. Confirm it appears in config management task mode.
3. Disable it.
4. Enable it.
5. Open recent runs.
6. Delete it.

## Task 6: Show One-Time Collection Task History

**Files:**
- Modify: `/OneOPS/OneOps-UI/src/views/device/DeviceConfigManagement.vue`
- Use: `/OneOPS/OneOps-UI/src/api/platform/task.ts`

- [ ] **Step 1: Import task list API**

Add:

```ts
import { listTaskOverviewsReq } from '@/api/platform/task';
```

- [ ] **Step 2: Add state**

Add:

```ts
const collectionTaskRuns = ref<TaskOverviewResp[]>([]);
const collectionTaskRunsLoading = ref(false);
```

- [ ] **Step 3: Load one-time runs**

Add:

```ts
const loadConfigCollectionTaskRuns = async () => {
  collectionTaskRunsLoading.value = true;
  try {
    const [networkResp, serverResp] = await Promise.all([
      listTaskOverviewsReq({ project_id: 'project-network-config-management', page: 1, pageSize: 20 }),
      listTaskOverviewsReq({ project_id: 'project-server-config-management', page: 1, pageSize: 20 }),
    ]);
    collectionTaskRuns.value = [...(networkResp?.list || []), ...(serverResp?.list || [])];
  } finally {
    collectionTaskRunsLoading.value = false;
  }
};
```

- [ ] **Step 4: Add run list UI**

Columns:

- task id;
- asset type from project id;
- status;
- target count;
- access plane;
- start time;
- end time;
- actions: `查看日志`, `查看结果`, `停止`.

Use existing task detail route if available; otherwise link to `#/platform/tasks?task_id=<task_id>`.

- [ ] **Step 5: Add refresh aggregator**

Add:

```ts
const loadConfigCollectionTasks = async () => {
  await Promise.all([loadConfigCollectionTaskRuns(), loadConfigCollectionScheduledTasks()]);
};
```

Call it when entering task mode and after creating tasks.

## Task 7: Keep Version Queue Connected To Task Center

**Files:**
- Modify: `/OneOPS/OneOps-UI/src/views/device/DeviceConfigManagement.vue`

- [ ] **Step 1: Rename isolated actions**

Rename UI labels:

- `立即采集` stays.
- `处理采集失败` becomes `重新采集失败资产`.
- `新建定时采集` appears in task mode.

- [ ] **Step 2: Make row action produce tasks**

Existing row-level collection should call the same helper path as task center manual collection. Do not keep duplicate request construction.

- [ ] **Step 3: Make failure queue action produce tasks**

`重新采集失败资产` should:

- filter rows where `last_backup_status !== 'success'` or work status is failed;
- group rows by asset type and access plane;
- create one task per group;
- show created task ids.

- [ ] **Step 4: After task creation**

After any collection task is created:

- refresh task mode data;
- keep the user on version mode if the action came from version queue;
- show a link-like button `查看采集任务` that switches to task mode.

## Task 8: Backend Guardrails For Scheduled Config Tasks

**Files:**
- Modify only if verification fails: `/OneOPS/OneOps/app/platform/service/impl/scheduled_task_v2.go`
- Modify only if verification fails: `/OneOPS/OneOps/app/platform/service/impl/scheduled_task_runner.go`
- Test: `/OneOPS/OneOps/app/platform/service/impl/scheduled_task_runner_test.go`

- [ ] **Step 1: Verify scheduled task request persists key fields**

Run backend tests:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestScheduledTaskRunner|TestScheduledTaskServiceV2' -count=1
```

Expected: tests pass.

- [ ] **Step 2: Add a test if config fields are lost**

If `device_codes`, `access_plane`, `run_on_agent`, `agent_code`, or `credential_ref` are lost, add a test in `scheduled_task_runner_test.go`:

```go
func TestScheduledTaskRunner_RunOne_ConfigManagementScheduledTaskPreservesTargets(t *testing.T) {
	store := &fakeScheduledTaskServiceV2{}
	creator := &fakeTaskCreationServiceV2{}
	runner := NewScheduledTaskRunner(zap.NewNop(), store, creator, nil)
	sched := &dto.ScheduledTaskResp{
		ID:           "sched-config-1",
		Name:         "网络设备配置采集 带内",
		TemplateID:   "tpl-network",
		ProjectID:    "project-network-config-management",
		FunctionArea: "DefaultArea",
		CronExpr:     "0 0 2 * * *",
		Enabled:      true,
		DeviceCodes:  []string{"DVC1", "DVC2"},
		AccessPlane:  "in_band",
		RunOnAgent:   true,
		AgentCode:    "agent-001",
	}

	runner.runOne(context.Background(), sched)

	if creator.lastEnvelope == nil {
		t.Fatalf("expected envelope")
	}
	if got := creator.lastEnvelope.Scope.ProjectID; got != "project-network-config-management" {
		t.Fatalf("project_id = %q", got)
	}
	if got := creator.lastEnvelope.Scope.ScheduledTaskID; got != "sched-config-1" {
		t.Fatalf("scheduled_task_id = %q", got)
	}
	if got := creator.lastEnvelope.Target.AccessPlane; got != "in_band" {
		t.Fatalf("access_plane = %q", got)
	}
	if got := creator.lastEnvelope.Runtime.AgentCode; got != "agent-001" {
		t.Fatalf("agent_code = %q", got)
	}
	if got := creator.lastEnvelope.Target.DeviceCodes; !reflect.DeepEqual(got, []string{"DVC1", "DVC2"}) {
		t.Fatalf("device_codes = %#v", got)
	}
}
```

- [ ] **Step 3: Implement minimal backend fix only if the test fails**

Keep fixes scoped to scheduled task persistence or envelope conversion.

## Task 9: Quick Env Synchronization

**Files:**
- Verify and modify as needed:
  - `/OneOPS/OneOps/quick_env/init-configs/gitea/source-repo/templates/task-template-catalog.json`
  - `/OneOPS/OneOps/quick_env/init-configs/gitea/source-repo/templates/variable-set-catalog.json`
  - `/OneOPS/OneOps/quick_env/init-configs/gitea/source-repo/ansible/server-config-collection/site.yml`

- [ ] **Step 1: Locate quick env files**

Run:

```bash
cd /OneOPS/OneOps
rg -n "server-config-collection|network-config-backup|native-network-config-backup-netlink" quick_env scripts app -g '*.json' -g '*.yml' -g '*.yaml' -g '*.sql'
```

Expected: both server and network collection templates appear in quick env seed data.

- [ ] **Step 2: Add missing server template seed if needed**

If missing, add the same template that exists in the live environment:

- name: `task-center-ansible-server-config-collection`
- app type: `server_config_collection`
- playbook path: `ansible/server-config-collection/site.yml`
- run on agent: `true`
- agent code: `agent-001`

- [ ] **Step 3: Add missing network template seed if needed**

If missing, add:

- name: `task-center-native-network-config-backup-netlink`
- app type: `network_config_backup`
- run on agent: `true`
- agent code: `agent-001`

- [ ] **Step 4: Verify seed consistency**

Run the quick env seed validation command used by the repo. If no dedicated validation exists, run:

```bash
cd /OneOPS/OneOps
rg -n "task-center-ansible-server-config-collection|task-center-native-network-config-backup-netlink" quick_env scripts app
```

Expected: both names appear in quick env seed paths.

## Task 10: Acceptance And Verification

**Files:**
- Create: `/OneOPS/docs/superpowers/acceptance/2026-06-07-config-management-collection-task-center-checklist.md`

- [ ] **Step 1: Create acceptance checklist**

Checklist content:

```markdown
# Config Management Collection Task Center Acceptance

Date: 2026-06-07

## Manual Collection

- [ ] Select one network device and create one-time collection.
- [ ] Select one server and create one-time collection.
- [ ] Confirm created tasks use config management project ids.
- [ ] Confirm task status is visible in configuration management.
- [ ] Confirm successful collection creates a config version.

## Scheduled Collection

- [ ] Create scheduled network collection.
- [ ] Create scheduled server collection.
- [ ] Enable and disable a scheduled collection.
- [ ] Open recent runs.
- [ ] Delete a scheduled collection.

## Version Loop

- [ ] View generated configuration.
- [ ] Download generated configuration.
- [ ] Compare current and previous versions.
- [ ] Compare arbitrary versions across assets.
- [ ] Set a single baseline.
- [ ] Batch set baselines.

## Failure Loop

- [ ] Trigger recollection for failed assets.
- [ ] Confirm failed asset recollection creates a new task.
- [ ] Confirm skipped groups show a human-readable reason.

## Copy And UI

- [ ] Main UI does not expose raw enum labels.
- [ ] Explanatory text is limited to blocking conditions.
- [ ] Task actions have verb-object labels.
- [ ] Layout does not shift when filters or modes change.
```

- [ ] **Step 2: Run frontend verification**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run typecheck
```

Expected: typecheck passes.

- [ ] **Step 3: Run backend verification**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestScheduledTaskRunner|TestTaskCreationServiceV2_CreateTask_ServerConfigCollectionUsesServerSSHInventoryForHuaweiServer|TestTaskCreationServiceV2_CreateTask_ServerConfigCollectionRejectsNetworkDeviceTargets' -count=1
```

Expected: tests pass.

- [ ] **Step 4: Browser acceptance**

Use the existing frontend at `http://127.0.0.1:3001` or the current dynamically served frontend. Do not start a separate frontend server unless the user explicitly asks.

Verify:

1. Login as `admin/admin@123`.
2. Open configuration management.
3. Switch to `采集任务`.
4. Create a one-time network collection.
5. Create a one-time server collection.
6. Create a scheduled collection.
7. Enable, disable, and delete the scheduled collection.
8. Confirm generated versions appear after successful runtime output projection.

## Self-Review

- Spec coverage: the plan covers task creation, scheduled task management, one-time task history, failure recollection, version loop linkage, server and network support, quick env synchronization, and acceptance.
- Placeholder scan: no task uses unresolved placeholder implementation. Phase 2 is explicitly out of Phase 1 implementation scope.
- Type consistency: `ConfigCollectionAssetType`, project ids, scope names, and helper function names are consistent across tasks.

## Execution Recommendation

Start with Phase 1. The highest-value implementation order is:

1. Task 2 helper module.
2. Task 3 page mode.
3. Task 4 one-time collection.
4. Task 5 scheduled collection management.
5. Task 6 task history.
6. Task 7 connect version queue actions.
7. Task 9 quick env verification.
8. Task 10 acceptance.

Do not add `platform_config_collection_plan` until the first version of the task center has been used in the browser and the operator workflow proves stable.
