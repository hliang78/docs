# Config Management Center API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the frontend's per-device temporary aggregation with backend-owned config management overview and latest asset list APIs.

**Architecture:** Keep the current Device V2 development entry and existing config version tables. Add config-management center DTOs and service methods that aggregate latest network-device config versions and latest backup failures from backend data. Expose temporary Device V2-scoped routes now, while keeping DTO and service names generic enough for a future standalone config-management router.

**Tech Stack:** Go, Gin, GORM, existing OneOps platform service pattern, Vue 3, TypeScript, Ant Design Vue.

---

### Task 1: Backend DTO And Service Contract

**Files:**
- Modify: `app/platform/dto/config_management.go`
- Modify: `app/platform/service/i_config_management.go`

- [x] **Step 1: Add DTOs**

Add `ConfigManagementOverviewResp`, `ConfigManagementAssetListReq`, `ConfigManagementAssetListResp`, and `ConfigManagementAssetResp`. The asset row should include `asset_type`, `asset_code`, `asset_name`, `config_scope`, `collector_type`, `collection_plane`, device compatibility fields, version fields, backup status fields, and `work_status`.

- [x] **Step 2: Extend service interface**

Add these methods to `IConfigVersionService`:

```go
GetCenterOverview(ctx context.Context) (*dto.ConfigManagementOverviewResp, error)
ListCenterAssets(ctx context.Context, req dto.ConfigManagementAssetListReq) (*dto.ConfigManagementAssetListResp, error)
```

- [x] **Step 3: Run API compile tests**

Run:

```bash
go test ./app/device/v2/api ./app/platform/service/impl
```

Expected: compile errors until implementation is added.

### Task 2: Backend Aggregation Service

**Files:**
- Modify: `app/platform/service/impl/config_version_service.go`
- Modify: `app/platform/service/impl/config_version_service_test.go`

- [x] **Step 1: Add failing service tests**

Add tests that insert config versions and device backup records, then assert:

- overview counts changed-today, unreviewed changes, no-baseline assets, failed backups, stale assets, and covered assets;
- asset list deduplicates to the latest version per device;
- failed latest backups without a config version appear as retryable work rows.

- [x] **Step 2: Implement aggregation helpers**

Use tenant-scoped queries. Read recent rows ordered by `device_code asc, backup_time desc, created_at desc`, deduplicate in Go, and cap query size to avoid unbounded scans.

- [x] **Step 3: Run service tests**

Run:

```bash
go test ./app/platform/service/impl -run 'TestConfigVersionService_(CenterOverview|ListCenterAssets)' -count=1
```

Expected: pass.

### Task 3: Device V2 Development Routes

**Files:**
- Modify: `app/device/v2/api/device_v2_config_management.go`
- Modify: `app/device/v2/api/device_v2_test.go`
- Modify: `app/device/v2/router/device_v2.go`

- [x] **Step 1: Add API tests**

Add tests for:

- `GET /device/v2/config-management/overview`
- `GET /device/v2/config-management/assets?page=1&page_size=20&status=changed`

- [x] **Step 2: Implement API methods**

Methods should validate service presence, parse pagination and status query, call `ConfigVersionSrv`, and return existing OneOps response envelopes.

- [x] **Step 3: Register routes before `:code` routes**

Add routes before parameterized `:code` routes:

```go
g.GET("config-management/overview", deviceV2API.GetConfigManagementOverview)
g.GET("config-management/assets", deviceV2API.ListConfigManagementAssets)
```

- [x] **Step 4: Run API tests**

Run:

```bash
go test ./app/device/v2/api -run 'TestDeviceV2API(ConfigManagementOverview|ListConfigManagementAssets)' -count=1
```

Expected: pass.

### Task 4: Frontend API Adapter

**Files:**
- Modify: `src/api/device/device-v2.ts`

- [x] **Step 1: Add TypeScript types**

Add config management overview and asset list response interfaces matching backend JSON.

- [x] **Step 2: Add request helpers**

Add:

```ts
export const getDeviceV2ConfigManagementOverviewReq = async () => request<ConfigManagementOverviewResp>({ ... });
export const listDeviceV2ConfigManagementAssetsReq = async (params?: ConfigManagementAssetListReq) => request<ConfigManagementAssetListResp>({ ... });
```

- [x] **Step 3: Run typecheck**

Run:

```bash
npm run typecheck:d2
```

Expected: fail until the page is updated.

### Task 5: Frontend Page Uses Center API

**Files:**
- Modify: `src/views/device/DeviceConfigManagement.vue`

- [x] **Step 1: Replace per-device aggregation**

Remove calls to `listDeviceV2Req`, `listDeviceV2ConfigBackupsReq`, and `listDeviceV2ConfigVersionsReq`. Load overview and asset rows from the new backend APIs.

- [x] **Step 2: Make cards actionable**

Clicking cards should update the table status filter: changed today, changed, no baseline, failed backup, stale, all covered.

- [x] **Step 3: Update copy**

Remove "temporary aggregation" wording. Keep the page as an operational workbench: discover, filter, inspect, retry/view task.

- [x] **Step 4: Run typecheck**

Run:

```bash
npm run typecheck:d2
```

Expected: pass.

### Task 6: Verification And Git

**Files:**
- Backend repo: `/OneOPS/OneOps`
- Frontend repo: `/OneOPS/OneOps-UI`
- Docs repo: `/OneOPS/docs`

- [x] **Step 1: Run backend verification**

Run:

```bash
go test ./app/platform/service/impl -run 'TestConfigVersionService|TestConfigDiffService|TestDeviceConfigBackupProjection' -count=1
go test ./app/device/v2/api -run 'TestDeviceV2API(ListConfigVersions|DiffConfigVersions|ConfigManagementOverview|ListConfigManagementAssets)' -count=1
go test ./app/platform/service ./app/platform/dto ./initialize
```

Expected: pass.

Note: `go test ./app/platform/service/impl ./app/device/v2/api ./initialize` was also run. `app/device/v2/api` and `initialize` passed, while the full `app/platform/service/impl` package failed in pre-existing unrelated deployment and Script Studio tests with missing SQLite tables and read-only SQLite writes. Config-management scoped tests passed.

- [x] **Step 2: Run frontend verification**

Run:

```bash
npm run typecheck:d2
```

Expected: pass.

- [x] **Step 3: Commit and push**

Commit backend to `feature/device-v2-platform-core-optimization`, frontend and docs to `main`, then push each clean worktree.
