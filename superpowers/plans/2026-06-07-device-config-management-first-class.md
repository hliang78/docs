# Device Config Management First-Class Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote device configuration management from backup history metadata into a first-class version, change-detection, and redacted-diff capability.

**Architecture:** Build the MVP in three layers: backend config-version facts derived from existing `platform_device_config_backup`, backend redacted diff APIs, then frontend version history and diff drawer in Device V2 detail. Baseline, drift review, and config management center remain future phases; the MVP proves immutable versions, previous-version change detection, and governed historical diff.

**Tech Stack:** Go, Gin, GORM, MySQL-compatible platform models, Vue 3, TypeScript, Ant Design Vue.

---

## Scope

Implement MVP phases from `docs/superpowers/specs/2026-06-07-device-config-management-first-class-design.md`:

- Config versions.
- Hash-based change detection against previous successful version.
- Config change event for changed versions.
- Device config version list API.
- Redacted unified diff API.
- Device detail config management UI with version history and diff drawer.

Do not implement baseline, drift policy, review workflow, alerting, or a global config management center in this plan.

## File Map

Backend:

- Create `app/platform/platform_model/config_version.go` for `ConfigVersion`.
- Create `app/platform/platform_model/config_change_event.go` for `ConfigChangeEvent`.
- Modify `cmd/gen/mysql/gen.go` to include new models in generated MySQL model set.
- Create `app/platform/dto/config_management.go` for version and diff DTOs.
- Create `app/platform/service/impl/config_version_service.go` for version creation, previous-version lookup, and list.
- Create `app/platform/service/impl/config_diff_service.go` for redaction and unified diff generation.
- Modify `app/platform/service/impl/device_config_backup_projection.go` to project successful backup records into config versions.
- Modify `app/device/v2/api/device_v2.go` or related API wiring to inject config management services.
- Create or modify `app/device/v2/api/device_v2_config_management.go` for Device V2 endpoints.
- Modify `app/device/v2/router/device_v2.go` to add config-version routes.
- Extend tests in `app/platform/service/impl/device_config_backup_projection_test.go`.
- Add tests in `app/platform/service/impl/config_version_service_test.go`.
- Add tests in `app/platform/service/impl/config_diff_service_test.go`.
- Add API tests in `app/device/v2/api/device_v2_test.go`.
- Regenerate `cmd/wire_gen.go` only if constructor injection changes require it.

Frontend:

- Modify `src/api/device/device-v2.ts` to add config version and diff types/API helpers.
- Modify `src/views/device/DeviceV2ManagementGrouped.vue` to show version history and diff drawer.
- Add smoke script `scripts/device-config-management-smoke.ts` if needed for focused frontend validation.

Docs:

- Update `docs/superpowers/acceptance/` with final evidence after implementation.

---

### Task 1: Backend Models And DTOs

**Files:**
- Create: `app/platform/platform_model/config_version.go`
- Create: `app/platform/platform_model/config_change_event.go`
- Modify: `cmd/gen/mysql/gen.go`
- Create: `app/platform/dto/config_management.go`

- [ ] **Step 1: Add `ConfigVersion` model**

Create `app/platform/platform_model/config_version.go`:

```go
package platform_model

import "time"

type ConfigVersion struct {
	ID                 string    `gorm:"column:id;primaryKey;type:varchar(64)" json:"id"`
	TenantCode         string    `gorm:"column:tenant_code;type:varchar(64);index:idx_cfg_ver_tenant_device_time" json:"tenant_code,omitempty"`
	DeviceCode         string    `gorm:"column:device_code;type:varchar(128);index:idx_cfg_ver_tenant_device_time;index:idx_cfg_ver_device_hash" json:"device_code"`
	DeviceName         string    `gorm:"column:device_name;type:varchar(255)" json:"device_name,omitempty"`
	AppType            string    `gorm:"column:app_type;type:varchar(64)" json:"app_type,omitempty"`
	VendorFamily       string    `gorm:"column:vendor_family;type:varchar(128)" json:"vendor_family,omitempty"`
	AccessPlane        string    `gorm:"column:access_plane;type:varchar(64)" json:"access_plane,omitempty"`
	SourceType         string    `gorm:"column:source_type;type:varchar(64)" json:"source_type"`
	SourceTaskID       string    `gorm:"column:source_task_id;type:varchar(128);index" json:"source_task_id,omitempty"`
	SourceChildTaskID  string    `gorm:"column:source_child_task_id;type:varchar(128);index" json:"source_child_task_id,omitempty"`
	BackupRecordID     string    `gorm:"column:backup_record_id;type:varchar(64);uniqueIndex:idx_cfg_ver_backup_record" json:"backup_record_id,omitempty"`
	ArtifactName       string    `gorm:"column:artifact_name;type:varchar(512)" json:"artifact_name,omitempty"`
	ArtifactStorageKey string    `gorm:"column:artifact_storage_key;type:varchar(1024)" json:"artifact_storage_key,omitempty"`
	ArtifactSHA256     string    `gorm:"column:artifact_sha256;type:varchar(128)" json:"artifact_sha256,omitempty"`
	ArtifactSize       int64     `gorm:"column:artifact_size" json:"artifact_size,omitempty"`
	ConfigHash         string    `gorm:"column:config_hash;type:varchar(128);index:idx_cfg_ver_device_hash" json:"config_hash,omitempty"`
	BackupTime         time.Time `gorm:"column:backup_time;index:idx_cfg_ver_tenant_device_time" json:"backup_time"`
	VersionIndex        int       `gorm:"column:version_index" json:"version_index"`
	PreviousVersionID  string    `gorm:"column:previous_version_id;type:varchar(64);index" json:"previous_version_id,omitempty"`
	ChangeStatus       string    `gorm:"column:change_status;type:varchar(32);index" json:"change_status"`
	BaselineStatus     string    `gorm:"column:baseline_status;type:varchar(32);index" json:"baseline_status"`
	CreatedAt          time.Time `gorm:"column:created_at" json:"created_at"`
	UpdatedAt          time.Time `gorm:"column:updated_at" json:"updated_at"`
}

func (*ConfigVersion) TableName() string {
	return "platform_config_version"
}
```

- [ ] **Step 2: Add `ConfigChangeEvent` model**

Create `app/platform/platform_model/config_change_event.go`:

```go
package platform_model

import "time"

type ConfigChangeEvent struct {
	ID                 string    `gorm:"column:id;primaryKey;type:varchar(64)" json:"id"`
	TenantCode         string    `gorm:"column:tenant_code;type:varchar(64);index:idx_cfg_change_tenant_device_time" json:"tenant_code,omitempty"`
	DeviceCode         string    `gorm:"column:device_code;type:varchar(128);index:idx_cfg_change_tenant_device_time" json:"device_code"`
	VersionID          string    `gorm:"column:version_id;type:varchar(64);uniqueIndex:idx_cfg_change_version" json:"version_id"`
	PreviousVersionID  string    `gorm:"column:previous_version_id;type:varchar(64)" json:"previous_version_id,omitempty"`
	ConfigHash         string    `gorm:"column:config_hash;type:varchar(128)" json:"config_hash,omitempty"`
	PreviousConfigHash string    `gorm:"column:previous_config_hash;type:varchar(128)" json:"previous_config_hash,omitempty"`
	ChangeStatus       string    `gorm:"column:change_status;type:varchar(32)" json:"change_status"`
	Severity           string    `gorm:"column:severity;type:varchar(32)" json:"severity"`
	ReviewStatus       string    `gorm:"column:review_status;type:varchar(32);index" json:"review_status"`
	CreatedAt          time.Time `gorm:"column:created_at;index:idx_cfg_change_tenant_device_time" json:"created_at"`
	UpdatedAt          time.Time `gorm:"column:updated_at" json:"updated_at"`
}

func (*ConfigChangeEvent) TableName() string {
	return "platform_config_change_event"
}
```

- [ ] **Step 3: Register models for MySQL generation**

Modify `cmd/gen/mysql/gen.go` near the existing `platform_model.DeviceConfigBackup{}` entry:

```go
platform_model.DeviceConfigBackup{}, // 设备配置备份索引
platform_model.ConfigVersion{},      // 设备配置版本
platform_model.ConfigChangeEvent{},  // 设备配置变化事件
```

- [ ] **Step 4: Add DTOs**

Create `app/platform/dto/config_management.go`:

```go
package dto

import "time"

type ConfigVersionListResp struct {
	List     []ConfigVersionResp `json:"list"`
	Total    int64               `json:"total"`
	Page     int                 `json:"page"`
	PageSize int                 `json:"page_size"`
}

type ConfigVersionResp struct {
	ID                 string    `json:"id"`
	DeviceCode         string    `json:"device_code"`
	SourceTaskID       string    `json:"source_task_id,omitempty"`
	SourceChildTaskID  string    `json:"source_child_task_id,omitempty"`
	BackupRecordID     string    `json:"backup_record_id,omitempty"`
	VendorFamily       string    `json:"vendor_family,omitempty"`
	AccessPlane        string    `json:"access_plane,omitempty"`
	ArtifactName       string    `json:"artifact_name,omitempty"`
	ArtifactSHA256     string    `json:"artifact_sha256,omitempty"`
	ArtifactSize       int64     `json:"artifact_size,omitempty"`
	ConfigHash         string    `json:"config_hash,omitempty"`
	BackupTime         time.Time `json:"backup_time"`
	VersionIndex        int       `json:"version_index"`
	PreviousVersionID  string    `json:"previous_version_id,omitempty"`
	ChangeStatus       string    `json:"change_status"`
	BaselineStatus     string    `json:"baseline_status"`
	CreatedAt          time.Time `json:"created_at"`
	UpdatedAt          time.Time `json:"updated_at"`
}

type ConfigVersionDiffReq struct {
	BaseVersionID   string `json:"base_version_id"`
	TargetVersionID string `json:"target_version_id"`
	ContextLines    int    `json:"context_lines,omitempty"`
}

type ConfigVersionDiffResp struct {
	DeviceCode       string            `json:"device_code"`
	BaseVersionID    string            `json:"base_version_id"`
	TargetVersionID  string            `json:"target_version_id"`
	BaseConfigHash   string            `json:"base_config_hash,omitempty"`
	TargetConfigHash string            `json:"target_config_hash,omitempty"`
	Changed          bool              `json:"changed"`
	Summary          ConfigDiffSummary `json:"summary"`
	RedactionApplied bool              `json:"redaction_applied"`
	DiffFormat       string            `json:"diff_format"`
	DiffText         string            `json:"diff_text"`
	Warnings         []string          `json:"warnings,omitempty"`
}

type ConfigDiffSummary struct {
	AddedLines    int `json:"added_lines"`
	RemovedLines  int `json:"removed_lines"`
	ModifiedLines int `json:"modified_lines"`
}
```

- [ ] **Step 5: Commit**

```bash
git add app/platform/platform_model/config_version.go \
  app/platform/platform_model/config_change_event.go \
  app/platform/dto/config_management.go \
  cmd/gen/mysql/gen.go
git commit -m "feat: add config management models"
```

---

### Task 2: Config Version Service And Change Detection

**Files:**
- Create: `app/platform/service/impl/config_version_service.go`
- Test: `app/platform/service/impl/config_version_service_test.go`

- [ ] **Step 1: Write tests for first/no-change/changed statuses**

Create `app/platform/service/impl/config_version_service_test.go` with tests that create in-memory `platform_config_version` and `platform_config_change_event` tables, then call the service three times:

```go
func TestConfigVersionService_ProjectBackup_FirstNoChangeChanged(t *testing.T) {
	db := setupConfigVersionTestDB(t)
	svc := NewConfigVersionService(zap.NewNop(), types.DBTypeMySQL(db))
	first := configBackupFixture("backup-1", "SW001", "task-1", "hash-a", parseTime("2026-06-07T10:00:00Z"))
	v1, err := svc.ProjectBackup(context.Background(), first)
	if err != nil { t.Fatal(err) }
	if v1.ChangeStatus != "first_backup" || v1.VersionIndex != 1 || v1.PreviousVersionID != "" {
		t.Fatalf("unexpected first version: %#v", v1)
	}

	second := configBackupFixture("backup-2", "SW001", "task-2", "hash-a", parseTime("2026-06-07T11:00:00Z"))
	v2, err := svc.ProjectBackup(context.Background(), second)
	if err != nil { t.Fatal(err) }
	if v2.ChangeStatus != "no_change" || v2.VersionIndex != 2 || v2.PreviousVersionID != v1.ID {
		t.Fatalf("unexpected no-change version: %#v", v2)
	}

	third := configBackupFixture("backup-3", "SW001", "task-3", "hash-b", parseTime("2026-06-07T12:00:00Z"))
	v3, err := svc.ProjectBackup(context.Background(), third)
	if err != nil { t.Fatal(err) }
	if v3.ChangeStatus != "changed" || v3.VersionIndex != 3 || v3.PreviousVersionID != v2.ID {
		t.Fatalf("unexpected changed version: %#v", v3)
	}

	var events []platformModel.ConfigChangeEvent
	if err := db.Table((&platformModel.ConfigChangeEvent{}).TableName()).Find(&events).Error; err != nil {
		t.Fatal(err)
	}
	if len(events) != 1 || events[0].VersionID != v3.ID || events[0].ReviewStatus != "unreviewed" {
		t.Fatalf("unexpected change events: %#v", events)
	}
}
```

- [ ] **Step 2: Run tests and verify failure**

```bash
go test ./app/platform/service/impl -run TestConfigVersionService -count=1
```

Expected: fail because `NewConfigVersionService` does not exist.

- [ ] **Step 3: Implement service**

Create `app/platform/service/impl/config_version_service.go` with:

```go
type ConfigVersionService struct {
	Logger *zap.Logger
	DB     types.DBTypeMySQL
}

func NewConfigVersionService(logger *zap.Logger, db types.DBTypeMySQL) *ConfigVersionService {
	return &ConfigVersionService{Logger: logger, DB: db}
}

func (s *ConfigVersionService) ProjectBackup(ctx context.Context, backup platformModel.DeviceConfigBackup) (*platformModel.ConfigVersion, error) {
	// trim device_code; ignore non-success backup_status by returning nil, nil
	// find existing version by backup_record_id and return it if found
	// find previous version for tenant/device/access_plane ordered backup_time desc, created_at desc
	// derive version_index and change_status
	// insert ConfigVersion
	// insert ConfigChangeEvent only when change_status == "changed"
}
```

Use constants:

```go
const (
	configChangeFirstBackup   = "first_backup"
	configChangeNoChange      = "no_change"
	configChangeChanged       = "changed"
	configChangeCompareFailed = "compare_failed"
	configBaselineNoBaseline  = "no_baseline"
)
```

Idempotency rule: repeated projection for the same `backup_record_id` returns the existing version and does not duplicate change events.

- [ ] **Step 4: Implement list by device**

Add:

```go
func (s *ConfigVersionService) ListByDevice(ctx context.Context, deviceCode string, page, pageSize int) (*dto.ConfigVersionListResp, error)
```

It should mirror `DeviceConfigBackupService.ListByDevice`: tenant scoped, ordered by `backup_time desc, created_at desc`, capped at `page_size <= 200`.

- [ ] **Step 5: Run tests**

```bash
go test ./app/platform/service/impl -run TestConfigVersionService -count=1
```

Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add app/platform/service/impl/config_version_service.go app/platform/service/impl/config_version_service_test.go
git commit -m "feat: derive config versions from backups"
```

---

### Task 3: Projection Integration

**Files:**
- Modify: `app/platform/service/impl/device_config_backup_projection.go`
- Test: `app/platform/service/impl/device_config_backup_projection_test.go`

- [ ] **Step 1: Extend projection tests**

Add a test that creates `platform_device_config_backup`, `platform_config_version`, and `platform_config_change_event` tables, then calls `projectDeviceConfigBackupFromRuntimeOutput`. Assert one backup record and one config version exist.

```go
func TestProjectDeviceConfigBackupFromRuntimeOutput_CreatesConfigVersion(t *testing.T) {
	db := setupDeviceConfigBackupProjectionDB(t)
	createConfigVersionTestTables(t, db)
	output := `{"artifacts":[{"name":"network-config-backup-SW001.cfg","kind":"text","size":128,"sha256":"cfgsha","storage_key":"storage/SW001.cfg"},{"name":"network-config-backup-SW001.json","kind":"json","content_base64":"eyJkZXZpY2VfY29kZSI6IlNXMDAxIiwiY29uZmlnX2hhc2giOiJoYXNoMSJ9"}]}`
	if err := projectDeviceConfigBackupFromRuntimeOutput(context.Background(), db, "task-SW001", "controller-1", output, parseTime("2026-06-07T10:00:00Z")); err != nil {
		t.Fatal(err)
	}
	var versions []platformModel.ConfigVersion
	if err := db.Table((&platformModel.ConfigVersion{}).TableName()).Find(&versions).Error; err != nil {
		t.Fatal(err)
	}
	if len(versions) != 1 || versions[0].DeviceCode != "SW001" || versions[0].ChangeStatus != "first_backup" {
		t.Fatalf("unexpected versions: %#v", versions)
	}
}
```

- [ ] **Step 2: Run test and verify failure**

```bash
go test ./app/platform/service/impl -run TestProjectDeviceConfigBackupFromRuntimeOutput_CreatesConfigVersion -count=1
```

Expected: fail because projection does not call config version service.

- [ ] **Step 3: Update projection**

In `projectDeviceConfigBackupFromRuntimeOutput`, after backup record is created or updated, load the persisted `DeviceConfigBackup` row and call:

```go
versionSvc := NewConfigVersionService(nil, types.DBTypeMySQL(db))
if _, err := versionSvc.ProjectBackup(ctx, persistedBackup); err != nil {
	return err
}
```

Keep behavior idempotent when an existing backup row is updated.

- [ ] **Step 4: Run focused tests**

```bash
go test ./app/platform/service/impl -run 'Test(ProjectDeviceConfigBackupFromRuntimeOutput|ConfigVersionService)' -count=1
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add app/platform/service/impl/device_config_backup_projection.go app/platform/service/impl/device_config_backup_projection_test.go
git commit -m "feat: project config backups into versions"
```

---

### Task 4: Redacted Diff Service

**Files:**
- Create: `app/platform/service/impl/config_diff_service.go`
- Test: `app/platform/service/impl/config_diff_service_test.go`

- [ ] **Step 1: Write redaction and diff tests**

Create tests for:

- redacts password/token/private key lines before diff;
- compares two same-device versions;
- rejects cross-device versions.

Use an in-memory content provider so this task does not depend on object storage.

```go
func TestConfigDiffService_RedactsBeforeDiff(t *testing.T) {
	db := setupConfigVersionTestDB(t)
	base := insertConfigVersion(t, db, "base", "SW001", "storage/base.cfg", "hash-a")
	target := insertConfigVersion(t, db, "target", "SW001", "storage/target.cfg", "hash-b")
	content := map[string]string{
		"storage/base.cfg": "hostname SW001\nusername admin password oldsecret\n",
		"storage/target.cfg": "hostname SW001\nusername admin password newsecret\ninterface Vlan10\n",
	}
	svc := NewConfigDiffService(zap.NewNop(), types.DBTypeMySQL(db), MemoryConfigArtifactReader(content))
	resp, err := svc.DiffVersions(context.Background(), "SW001", base.ID, target.ID, 3)
	if err != nil { t.Fatal(err) }
	if !resp.Changed || !resp.RedactionApplied {
		t.Fatalf("expected changed redacted diff: %#v", resp)
	}
	if strings.Contains(resp.DiffText, "oldsecret") || strings.Contains(resp.DiffText, "newsecret") {
		t.Fatalf("diff leaked secret: %s", resp.DiffText)
	}
	if !strings.Contains(resp.DiffText, "interface Vlan10") {
		t.Fatalf("expected added interface line, got %s", resp.DiffText)
	}
}
```

- [ ] **Step 2: Implement service**

Create `ConfigArtifactReader` interface:

```go
type ConfigArtifactReader interface {
	ReadConfigArtifact(ctx context.Context, storageKey string) (string, error)
}
```

Add `ConfigDiffService`:

```go
type ConfigDiffService struct {
	Logger *zap.Logger
	DB     types.DBTypeMySQL
	Reader ConfigArtifactReader
}
```

Implement:

- version lookup by ID with tenant scope;
- same-device validation;
- artifact read by `ArtifactStorageKey`;
- redaction regexes for password, token, secret, private key, snmp community;
- unified diff generation with context lines;
- summary counts.

- [ ] **Step 3: Run tests**

```bash
go test ./app/platform/service/impl -run TestConfigDiffService -count=1
```

Expected: pass.

- [ ] **Step 4: Commit**

```bash
git add app/platform/service/impl/config_diff_service.go app/platform/service/impl/config_diff_service_test.go
git commit -m "feat: add redacted config diff service"
```

---

### Task 5: Device V2 Config Version APIs

**Files:**
- Modify: `app/device/v2/api/device_v2.go`
- Create: `app/device/v2/api/device_v2_config_management.go`
- Modify: `app/device/v2/router/device_v2.go`
- Test: `app/device/v2/api/device_v2_test.go`
- Modify: `cmd/wire_gen.go` if dependency injection requires it.

- [ ] **Step 1: Add API tests**

Add tests:

```go
func TestDeviceV2APIListConfigVersions(t *testing.T) {
	// seed two ConfigVersion rows for SW001 and one for SW002
	// GET /device/v2/SW001/config-versions?page=1&page_size=10
	// assert only SW001 versions returned, newest first
}

func TestDeviceV2APIDiffConfigVersionsRejectsCrossDevice(t *testing.T) {
	// seed base for SW001 and target for SW002
	// POST /device/v2/SW001/config-versions/diff
	// assert error response
}
```

- [ ] **Step 2: Implement API handlers**

Create `app/device/v2/api/device_v2_config_management.go`:

```go
func (a *DeviceV2API) ListConfigVersions(ctx *gin.Context) {
	code := strings.TrimSpace(ctx.Param("code"))
	page, pageSize := parsePageQuery(ctx)
	resp, err := a.ConfigVersionSrv.ListByDevice(ctx.Request.Context(), code, page, pageSize)
	if err != nil {
		response.FailWithMsg(err.Error(), ctx)
		return
	}
	response.OkWithData(resp, ctx)
}

func (a *DeviceV2API) DiffConfigVersions(ctx *gin.Context) {
	code := strings.TrimSpace(ctx.Param("code"))
	var req dto.ConfigVersionDiffReq
	if err := ctx.ShouldBindJSON(&req); err != nil {
		response.FailWithMsg(err.Error(), ctx)
		return
	}
	resp, err := a.ConfigDiffSrv.DiffVersions(ctx.Request.Context(), code, req.BaseVersionID, req.TargetVersionID, req.ContextLines)
	if err != nil {
		response.FailWithMsg(err.Error(), ctx)
		return
	}
	response.OkWithData(resp, ctx)
}
```

Add service fields to `DeviceV2API` following the existing `DeviceConfigBackupSrv` pattern.

- [ ] **Step 3: Add routes**

Modify `app/device/v2/router/device_v2.go` near `config-backups`:

```go
g.GET(":code/config-versions", deviceV2API.ListConfigVersions)
g.POST(":code/config-versions/diff", deviceV2API.DiffConfigVersions)
g.POST(":code/config-versions/:version_id/diff-previous", deviceV2API.DiffConfigVersionWithPrevious)
```

`diff-previous` may be deferred if arbitrary diff is already implemented; if deferred, do not add the route.

- [ ] **Step 4: Run API tests**

```bash
go test ./app/device/v2/api -run 'TestDeviceV2API(ListConfigVersions|DiffConfigVersions)' -count=1
```

Expected: pass.

- [ ] **Step 5: Run backend focused suite**

```bash
go test ./app/platform/service/impl -run 'Test(ConfigVersionService|ConfigDiffService|ProjectDeviceConfigBackupFromRuntimeOutput)' -count=1
go test ./app/device/v2/api -run 'TestDeviceV2API(ListConfigBackups|ListConfigVersions|DiffConfigVersions)' -count=1
```

Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add app/device/v2/api app/device/v2/router/device_v2.go cmd/wire_gen.go
git commit -m "feat: expose config version APIs"
```

---

### Task 6: Frontend API Types And Helpers

**Files:**
- Modify: `src/api/device/device-v2.ts`

- [ ] **Step 1: Add TypeScript interfaces**

In `src/api/device/device-v2.ts`, after `DeviceConfigBackupResp`, add:

```ts
export type ConfigChangeStatus = 'first_backup' | 'no_change' | 'changed' | 'compare_failed';
export type ConfigBaselineStatus = 'no_baseline' | 'matches_baseline' | 'drifted' | 'baseline_compare_failed';

export interface DeviceConfigVersionListResp {
  list: DeviceConfigVersionResp[];
  total: number;
  page: number;
  page_size: number;
}

export interface DeviceConfigVersionResp {
  id: string;
  device_code: string;
  source_task_id?: string;
  source_child_task_id?: string;
  backup_record_id?: string;
  vendor_family?: string;
  access_plane?: string;
  artifact_name?: string;
  artifact_sha256?: string;
  artifact_size?: number;
  config_hash?: string;
  backup_time: string;
  version_index: number;
  previous_version_id?: string;
  change_status: ConfigChangeStatus;
  baseline_status: ConfigBaselineStatus;
  created_at: string;
  updated_at: string;
}

export interface DeviceConfigVersionDiffReq {
  base_version_id: string;
  target_version_id: string;
  context_lines?: number;
}

export interface DeviceConfigVersionDiffResp {
  device_code: string;
  base_version_id: string;
  target_version_id: string;
  base_config_hash?: string;
  target_config_hash?: string;
  changed: boolean;
  summary: {
    added_lines: number;
    removed_lines: number;
    modified_lines: number;
  };
  redaction_applied: boolean;
  diff_format: 'unified';
  diff_text: string;
  warnings?: string[];
}
```

- [ ] **Step 2: Add API helpers**

Add:

```ts
export const listDeviceV2ConfigVersionsReq = async (
  code: string,
  params?: { page?: number; page_size?: number },
) => {
  return request<DeviceConfigVersionListResp>({
    url: `${BASE}/${encodeURIComponent(code)}/config-versions`,
    method: HTTP_GET,
    params: params ?? {},
  });
};

export const diffDeviceV2ConfigVersionsReq = async (code: string, data: DeviceConfigVersionDiffReq) => {
  return request<DeviceConfigVersionDiffResp>({
    url: `${BASE}/${encodeURIComponent(code)}/config-versions/diff`,
    method: HTTP_POST,
    data,
  });
};
```

- [ ] **Step 3: Run typecheck**

```bash
npm run typecheck
```

Expected: pass.

- [ ] **Step 4: Commit**

```bash
git add src/api/device/device-v2.ts
git commit -m "feat: add config version frontend api"
```

---

### Task 7: Device Detail Config Version UI

**Files:**
- Modify: `src/views/device/DeviceV2ManagementGrouped.vue`

- [ ] **Step 1: Add state and loaders**

Add state near existing `selectedDeviceConfigBackups` state:

```ts
const selectedDeviceConfigVersions = ref<DeviceConfigVersionResp[]>([]);
const selectedDeviceConfigVersionsTotal = ref(0);
const selectedDeviceConfigVersionsLoading = ref(false);
const selectedDeviceConfigVersionsError = ref('');
let selectedDeviceConfigVersionsRequestSeq = 0;
```

Add `loadSelectedDeviceConfigVersions(code: string)` mirroring `loadSelectedDeviceConfigBackups`, using `listDeviceV2ConfigVersionsReq(code, { page: 1, page_size: 10 })`.

- [ ] **Step 2: Load versions with device detail**

In `loadDeviceDetail`, after:

```ts
void loadSelectedDeviceConfigBackups(normalized);
```

add:

```ts
void loadSelectedDeviceConfigVersions(normalized);
```

Reset versions in `closeDetail()` and `resetSelectedDeviceConfigBackups()` equivalent.

- [ ] **Step 3: Add version columns and status formatting**

Add:

```ts
function configChangeStatusColor(status?: string) {
  const normalized = String(status || '').toLowerCase();
  if (normalized === 'changed') return 'warning';
  if (normalized === 'no_change') return 'success';
  if (normalized === 'first_backup') return 'processing';
  if (normalized === 'compare_failed') return 'error';
  return 'default';
}

function formatConfigChangeStatus(status?: string) {
  const normalized = String(status || '').toLowerCase();
  if (normalized === 'changed') return '有变化';
  if (normalized === 'no_change') return '无变化';
  if (normalized === 'first_backup') return '首次备份';
  if (normalized === 'compare_failed') return '对比失败';
  return status || '-';
}
```

Version columns:

```ts
const configVersionColumns = [
  { title: '版本', dataIndex: 'version_index', key: 'version_index', width: 80 },
  { title: '时间', dataIndex: 'backup_time', key: 'backup_time', width: 170 },
  { title: '变化', dataIndex: 'change_status', key: 'change_status', width: 100 },
  { title: '基线', dataIndex: 'baseline_status', key: 'baseline_status', width: 120 },
  { title: '访问平面', dataIndex: 'access_plane', key: 'access_plane', width: 100 },
  { title: '配置 Hash', dataIndex: 'config_hash', key: 'config_hash', width: 180 },
  { title: '产物', dataIndex: 'artifact_name', key: 'artifact_name', width: 220 },
  { title: '操作', key: 'action', width: 160, fixed: 'right' as const },
];
```

- [ ] **Step 4: Add version table UI**

In the config backup block, add a separate subsection titled `配置版本` before or after the existing `配置备份` table. Use a compact table and keep the existing backup table for provenance.

Row actions:

- `与上一版对比` when `previous_version_id` exists.
- `设为起点` and `设为目标` for arbitrary compare selection.

- [ ] **Step 5: Commit**

```bash
git add src/views/device/DeviceV2ManagementGrouped.vue
git commit -m "feat: show device config versions"
```

---

### Task 8: Frontend Diff Drawer

**Files:**
- Modify: `src/views/device/DeviceV2ManagementGrouped.vue`

- [ ] **Step 1: Add diff state**

```ts
const configDiffDrawer = reactive<{
  visible: boolean;
  loading: boolean;
  error: string;
  baseVersionId: string;
  targetVersionId: string;
  result: DeviceConfigVersionDiffResp | null;
}>({
  visible: false,
  loading: false,
  error: '',
  baseVersionId: '',
  targetVersionId: '',
  result: null,
});
```

- [ ] **Step 2: Add compare function**

```ts
async function openConfigVersionDiff(baseVersionId: string, targetVersionId: string) {
  const code = plainText(selectedDeviceCode.value);
  if (!code || !baseVersionId || !targetVersionId) return;
  configDiffDrawer.visible = true;
  configDiffDrawer.loading = true;
  configDiffDrawer.error = '';
  configDiffDrawer.result = null;
  configDiffDrawer.baseVersionId = baseVersionId;
  configDiffDrawer.targetVersionId = targetVersionId;
  try {
    configDiffDrawer.result = await diffDeviceV2ConfigVersionsReq(code, {
      base_version_id: baseVersionId,
      target_version_id: targetVersionId,
      context_lines: 3,
    });
  } catch (error) {
    configDiffDrawer.error = error instanceof Error ? error.message : '加载配置差异失败';
  } finally {
    configDiffDrawer.loading = false;
  }
}
```

- [ ] **Step 3: Add drawer UI**

Add an `a-drawer` near other detail drawers:

```vue
<a-drawer
  v-model:visible="configDiffDrawer.visible"
  title="配置差异"
  width="900px"
  placement="right"
  :destroy-on-close="true"
>
  <a-spin :spinning="configDiffDrawer.loading">
    <a-alert
      v-if="configDiffDrawer.error"
      type="error"
      show-icon
      :message="configDiffDrawer.error"
    />
    <template v-else-if="configDiffDrawer.result">
      <a-alert
        class="mb-3"
        type="warning"
        show-icon
        message="差异内容已脱敏"
        description="配置正文不会默认预览；这里只展示后端返回的受控 unified diff。"
      />
      <div class="config-diff-summary">
        <a-tag color="success">+{{ configDiffDrawer.result.summary.added_lines }}</a-tag>
        <a-tag color="error">-{{ configDiffDrawer.result.summary.removed_lines }}</a-tag>
        <a-tag color="processing">~{{ configDiffDrawer.result.summary.modified_lines }}</a-tag>
      </div>
      <pre class="config-diff-pre">{{ configDiffDrawer.result.diff_text || '无差异' }}</pre>
    </template>
  </a-spin>
</a-drawer>
```

- [ ] **Step 4: Add styles**

```css
.config-diff-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}
.config-diff-pre {
  max-height: 620px;
  overflow: auto;
  padding: 12px;
  border: 1px solid #eaecf0;
  border-radius: 6px;
  background: #0f172a;
  color: #e5e7eb;
  font-family: 'SFMono-Regular', 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre;
}
```

- [ ] **Step 5: Run frontend verification**

```bash
npm run typecheck
npm run build:force
```

Expected: both pass. Existing Vite large chunk warning may remain.

- [ ] **Step 6: Commit**

```bash
git add src/views/device/DeviceV2ManagementGrouped.vue
git commit -m "feat: compare device config versions"
```

---

### Task 9: Final Acceptance

**Files:**
- Create: `docs/superpowers/acceptance/2026-06-07-device-config-management-first-class-checklist.md`

- [ ] **Step 1: Run backend verification**

```bash
go test ./app/platform/service/impl -run 'Test(ConfigVersionService|ConfigDiffService|ProjectDeviceConfigBackupFromRuntimeOutput)' -count=1
go test ./app/device/v2/api -run 'TestDeviceV2API(ListConfigBackups|ListConfigVersions|DiffConfigVersions)' -count=1
```

Expected: pass.

- [ ] **Step 2: Run frontend verification**

```bash
npm run typecheck
npm run build:force
```

Expected: pass, except acceptable existing Vite large chunk warning.

- [ ] **Step 3: Run security grep**

```bash
git diff origin/main..HEAD -- src app | rg -n -i 'password|token|secret|private[_-]?key|community' || true
```

Expected: matches only redaction code, DTO field names, or test fixtures with redacted values. No real secret literals.

- [ ] **Step 4: Write acceptance checklist**

Create `docs/superpowers/acceptance/2026-06-07-device-config-management-first-class-checklist.md` with:

```markdown
# Device Config Management First-Class Acceptance

## Scope

- Config versions are first-class facts derived from successful device config backups.
- Change detection compares each new version with the previous successful version.
- Historical diff is returned only as redacted unified diff.

## Verification

- Backend focused tests: <command and result>
- Frontend typecheck/build: <command and result>
- Secret grep: <result>

## Remaining Risks

- Baseline/drift review is planned but not in MVP.
- Authenticated browser E2E requires a backend/auth fixture.
```

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/acceptance/2026-06-07-device-config-management-first-class-checklist.md
git commit -m "docs: record config management acceptance"
```

---

## Execution Notes

- Keep backend and frontend changes on their already established target branches:
  - Backend: `feature/device-v2-platform-core-optimization`
  - Frontend: `main`
  - Docs: `main`
- Do not expose raw config content in normal UI.
- Redact before diff generation, not after.
- Keep `platform_device_config_backup` as provenance; do not remove it.
- Treat `ConfigVersion` as the new source of truth for configuration versioning.

## Self-Review

- Spec coverage: MVP covers version facts, change detection, diff, frontend version history, and governed diff drawer. Baseline/drift/review center are explicitly deferred.
- Completeness scan: no unresolved filler terms remain in the plan.
- Type consistency: DTO names use `ConfigVersion*` in Go and `DeviceConfigVersion*` in frontend helpers; backend model uses `ConfigVersion`.
