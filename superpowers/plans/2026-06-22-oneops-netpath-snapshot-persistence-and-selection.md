# OneOPS NetPath Snapshot Persistence And Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add durable NetPath snapshot persistence, explicit snapshot create/get APIs, snapshot-first analysis-run behavior, and store-first SDK snapshot resolution.

**Architecture:** Introduce a OneOPS-owned `netpath_snapshot` table that stores the internal `AnalysisSnapshot` as `snapshot_json` plus structured summary fields. Build snapshots from latest facts through a service-owned builder, let `CreateAnalyzeRun` reuse or auto-create persisted snapshots, and make the SDK-backed runtime load stored snapshots by `snapshot_id` before rebuilding from latest facts.

**Tech Stack:** Go, GORM, sqlite-backed Go tests, existing OneOPS NetPath service/API/runtime packages, current NetPath snapshot assembler/validator, MySQL companion migration.

---

## File Structure

### New files

- `OneOps/app/netpath/netpath_model/snapshot.go`
  - Durable snapshot model for `netpath_snapshot`.
- `OneOps/migrations/add_netpath_snapshot_20260622.sql`
  - Companion SQL for environments not relying on startup AutoMigrate.

### Existing files to modify

- `OneOps/initialize/mysql_test.go`
  - AutoMigrate coverage for the new snapshot model and migration compatibility guard.
- `OneOps/app/netpath/dto/netpath.go`
  - Snapshot create/get request and response DTOs, including debug view payload.
- `OneOps/app/netpath/service/i_netpath.go`
  - Public snapshot service methods.
- `OneOps/app/netpath/api/netpath.go`
  - HTTP handlers for create/get snapshot.
- `OneOps/app/netpath/router/netpath.go`
  - Snapshot routes.
- `OneOps/app/netpath/service/impl/netpath.go`
  - Snapshot persistence helpers, snapshot-first `CreateAnalyzeRun`, and run/snapshot linkage.
- `OneOps/app/netpath/service/impl/module.go`
  - DI wiring for snapshot creation dependencies.
- `OneOps/app/netpath/runtime/runtime.go`
  - Runtime dependency surface for snapshot lookup/create.
- `OneOps/app/netpath/runtime/sdk_enabled.go`
  - Store-first snapshot resolution before latest-fact assembly fallback.
- `OneOps/app/netpath/api/netpath_test.go`
  - Snapshot API tests plus run integration coverage.
- `OneOps/app/netpath/service/impl/netpath_test.go`
  - Snapshot service tests, blocked fail-closed run tests, and persisted-snapshot reuse tests.
- `OneOps/app/netpath/runtime/runtime_sdk_test.go`
  - SDK provider tests for stored snapshot lookup and blocked snapshot rejection.

## Task 1: Add The Durable Snapshot Schema

**Files:**
- Create: `OneOps/app/netpath/netpath_model/snapshot.go`
- Modify: `OneOps/initialize/mysql_test.go`
- Create: `OneOps/migrations/add_netpath_snapshot_20260622.sql`

- [ ] **Step 1: Write the failing schema test**

Add a new test in `OneOps/initialize/mysql_test.go`:

```go
func TestNetPathSnapshotAutoMigrateColumns(t *testing.T) {
	db, err := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{})
	if err != nil {
		t.Fatalf("open sqlite failed: %v", err)
	}
	model := &netpathmodel.NetPathSnapshot{}
	if err = db.AutoMigrate(model); err != nil {
		t.Fatalf("automigrate netpath snapshot failed: %v", err)
	}

	table := model.TableName()
	for _, column := range []string{
		"code",
		"tenant_code",
		"quality",
		"device_codes_json",
		"ingress_device_code",
		"ingress_vrf",
		"source_run_ids_json",
		"diagnostics_json",
		"summary",
		"snapshot_json",
		"created_at",
		"updated_at",
	} {
		if !db.Migrator().HasColumn(table, column) {
			t.Fatalf("expected AutoMigrate to create %s.%s", table, column)
		}
	}

	for _, index := range []string{
		"idx_netpath_snapshot_tenant_code",
		"idx_netpath_snapshot_quality",
		"idx_netpath_snapshot_ingress_device_code",
	} {
		if !db.Migrator().HasIndex(table, index) {
			t.Fatalf("expected AutoMigrate to create index %s on %s", index, table)
		}
	}
}
```

- [ ] **Step 2: Run the schema test and confirm it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./initialize -run TestNetPathSnapshotAutoMigrateColumns -count=1
```

Expected: FAIL because `NetPathSnapshot` does not exist yet.

- [ ] **Step 3: Add the snapshot model**

Create `OneOps/app/netpath/netpath_model/snapshot.go`:

```go
package netpath_model

import "time"

type NetPathSnapshot struct {
	ID                uint      `gorm:"primarykey" json:"id"`
	Code              string    `gorm:"column:code;uniqueIndex;size:64" json:"code"`
	TenantCode        string    `gorm:"column:tenant_code;size:64;index:idx_netpath_snapshot_tenant_code" json:"tenant_code"`
	Quality           string    `gorm:"column:quality;size:32;index:idx_netpath_snapshot_quality" json:"quality"`
	DeviceCodesJSON   string    `gorm:"column:device_codes_json;type:text" json:"device_codes_json"`
	IngressDeviceCode string    `gorm:"column:ingress_device_code;size:128;index:idx_netpath_snapshot_ingress_device_code" json:"ingress_device_code"`
	IngressVRF        string    `gorm:"column:ingress_vrf;size:128" json:"ingress_vrf"`
	SourceRunIDsJSON  string    `gorm:"column:source_run_ids_json;type:text" json:"source_run_ids_json"`
	DiagnosticsJSON   string    `gorm:"column:diagnostics_json;type:longtext" json:"diagnostics_json"`
	Summary           string    `gorm:"column:summary;type:text" json:"summary"`
	SnapshotJSON      string    `gorm:"column:snapshot_json;type:longtext" json:"snapshot_json"`
	CreatedAt         time.Time `json:"created_at"`
	UpdatedAt         time.Time `json:"updated_at"`
}

func (*NetPathSnapshot) TableName() string {
	return "netpath_snapshot"
}
```

- [ ] **Step 4: Add the companion migration**

Create `OneOps/migrations/add_netpath_snapshot_20260622.sql`:

```sql
CREATE TABLE IF NOT EXISTS `netpath_snapshot` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `code` varchar(64) NOT NULL,
  `tenant_code` varchar(64) NOT NULL DEFAULT '',
  `quality` varchar(32) NOT NULL DEFAULT '',
  `device_codes_json` text NOT NULL,
  `ingress_device_code` varchar(128) NOT NULL DEFAULT '',
  `ingress_vrf` varchar(128) NOT NULL DEFAULT '',
  `source_run_ids_json` text NOT NULL,
  `diagnostics_json` longtext NOT NULL,
  `summary` text NOT NULL,
  `snapshot_json` longtext NOT NULL,
  `created_at` datetime(3) NULL,
  `updated_at` datetime(3) NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_netpath_snapshot_code` (`code`),
  KEY `idx_netpath_snapshot_tenant_code` (`tenant_code`),
  KEY `idx_netpath_snapshot_quality` (`quality`),
  KEY `idx_netpath_snapshot_ingress_device_code` (`ingress_device_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
```

- [ ] **Step 5: Re-run the schema test**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./initialize -run 'TestNetPathSnapshotAutoMigrateColumns|TestNetPathAnalysisRunAutoMigrateColumns' -count=1
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/netpath/netpath_model/snapshot.go initialize/mysql_test.go migrations/add_netpath_snapshot_20260622.sql
git commit -m "feat: add netpath snapshot schema"
```

## Task 2: Add Snapshot DTOs, Service Methods, And HTTP APIs

**Files:**
- Modify: `OneOps/app/netpath/dto/netpath.go`
- Modify: `OneOps/app/netpath/service/i_netpath.go`
- Modify: `OneOps/app/netpath/api/netpath.go`
- Modify: `OneOps/app/netpath/router/netpath.go`
- Modify: `OneOps/app/netpath/service/impl/netpath.go`
- Modify: `OneOps/app/netpath/service/impl/netpath_test.go`
- Modify: `OneOps/app/netpath/api/netpath_test.go`

- [ ] **Step 1: Write the first failing snapshot service tests**

Add service tests in `OneOps/app/netpath/service/impl/netpath_test.go`:

```go
func TestNetPathServiceCreateAndGetSnapshotSummary(t *testing.T) {
	db := newNetPathTestDB(t)
	svc := NewNetPathService(db, WithAnalysisSnapshotBuilder(&fakeAnalysisSnapshotBuilder{
		snapshot: provider.AnalysisSnapshot{
			SnapshotID:  "nps-ready-1",
			TenantCode:  "tenant-a",
			Quality:     provider.SnapshotQualityReady,
			Diagnostics: []provider.AnalysisDiagnostic{{Severity: provider.SeverityInfo, Code: "ok", Message: "ready"}},
			SourceVersions: provider.SourceRefs{
				CollectionRunIDs: []string{"collect-1"},
				FactRunIDs:       []string{"fact-1"},
			},
		},
		summary: "2 devices | route ready",
	}))

	created, err := svc.CreateSnapshot(context.Background(), dto.SnapshotCreateReq{
		TenantCode:        "tenant-a",
		DeviceCodes:       []string{"r1", "r2"},
		IngressDeviceCode: "r1",
		IngressVRF:        "default",
	})
	if err != nil {
		t.Fatalf("CreateSnapshot returned error: %v", err)
	}
	if created.Quality != "ready" || created.Summary == "" {
		t.Fatalf("unexpected snapshot summary: %#v", created)
	}

	got, err := svc.GetSnapshot(context.Background(), "tenant-a", created.Code, false)
	if err != nil {
		t.Fatalf("GetSnapshot returned error: %v", err)
	}
	if got.Code != created.Code || got.DebugSnapshot != nil {
		t.Fatalf("unexpected snapshot fetch result: %#v", got)
	}
}

func TestNetPathServiceGetSnapshotDebugIncludesPayload(t *testing.T) {
	db := newNetPathTestDB(t)
	svc := NewNetPathService(db, WithAnalysisSnapshotBuilder(&fakeAnalysisSnapshotBuilder{
		snapshot: provider.AnalysisSnapshot{
			SnapshotID: "nps-debug-1",
			TenantCode: "tenant-a",
			Quality:    provider.SnapshotQualityDegraded,
		},
		summary: "debug snapshot",
	}))

	created, err := svc.CreateSnapshot(context.Background(), dto.SnapshotCreateReq{
		TenantCode:  "tenant-a",
		DeviceCodes: []string{"r1"},
	})
	if err != nil {
		t.Fatalf("CreateSnapshot returned error: %v", err)
	}

	got, err := svc.GetSnapshot(context.Background(), "tenant-a", created.Code, true)
	if err != nil {
		t.Fatalf("GetSnapshot debug returned error: %v", err)
	}
	if got.DebugSnapshot == nil {
		t.Fatalf("expected debug snapshot payload, got %#v", got)
	}
}
```

- [ ] **Step 2: Run the snapshot service tests and confirm they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl -run 'TestNetPathService(CreateAndGetSnapshotSummary|GetSnapshotDebugIncludesPayload)$' -count=1
```

Expected: FAIL because the snapshot DTOs/service methods/builders do not exist yet.

- [ ] **Step 3: Add snapshot DTOs and service interface methods**

Update `OneOps/app/netpath/dto/netpath.go`:

```go
type SnapshotCreateReq struct {
	TenantCode        string   `json:"tenant_code"`
	DeviceCodes       []string `json:"device_codes,omitempty"`
	IngressDeviceCode string   `json:"ingress_device_code,omitempty"`
	IngressVRF        string   `json:"ingress_vrf,omitempty"`
}

type SnapshotResp struct {
	Code              string              `json:"code"`
	TenantCode        string              `json:"tenant_code"`
	Quality           string              `json:"quality"`
	Summary           string              `json:"summary,omitempty"`
	DeviceCodes       []string            `json:"device_codes,omitempty"`
	IngressDeviceCode string              `json:"ingress_device_code,omitempty"`
	IngressVRF        string              `json:"ingress_vrf,omitempty"`
	SourceRunIDs      []string            `json:"source_run_ids,omitempty"`
	Diagnostics       []AnalyzeDiagnostic `json:"diagnostics,omitempty"`
	DebugSnapshot     map[string]any      `json:"debug_snapshot,omitempty"`
	CreatedAt         int64               `json:"created_at,omitempty"`
	UpdatedAt         int64               `json:"updated_at,omitempty"`
}
```

Update `OneOps/app/netpath/service/i_netpath.go`:

```go
	CreateSnapshot(ctx context.Context, req dto.SnapshotCreateReq) (*dto.SnapshotResp, error)
	GetSnapshot(ctx context.Context, tenantCode string, code string, debug bool) (*dto.SnapshotResp, error)
```

- [ ] **Step 4: Add API handlers and routes**

Update `OneOps/app/netpath/api/netpath.go`:

```go
func (a *NetPathAPI) CreateSnapshot(ctx *gin.Context) {
	var req dto.SnapshotCreateReq
	if err := ctx.ShouldBindJSON(&req); err != nil {
		response.FailWithMsg(err.Error(), ctx)
		a.warn("CreateSnapshot bind error", zap.Error(err))
		return
	}
	resp, err := a.NetPathSrv.CreateSnapshot(ctx, req)
	if err != nil {
		response.FailWithMsg(err.Error(), ctx)
		a.warn("CreateSnapshot service error", zap.Error(err))
		return
	}
	response.OkWithData(resp, ctx)
}

func (a *NetPathAPI) GetSnapshot(ctx *gin.Context) {
	code := strings.TrimSpace(ctx.Param("code"))
	tenantCode := strings.TrimSpace(ctx.Query("tenant_code"))
	debug := strings.EqualFold(strings.TrimSpace(ctx.Query("view")), "debug")
	resp, err := a.NetPathSrv.GetSnapshot(ctx, tenantCode, code, debug)
	if err != nil {
		response.FailWithMsg(err.Error(), ctx)
		a.warn("GetSnapshot service error", zap.String("tenant_code", tenantCode), zap.String("code", code), zap.Error(err))
		return
	}
	response.OkWithData(resp, ctx)
}
```

Update `OneOps/app/netpath/router/netpath.go`:

```go
	g.POST("snapshots", netPathAPI.CreateSnapshot)
	g.GET("snapshots/:code", netPathAPI.GetSnapshot)
```

- [ ] **Step 5: Implement snapshot persistence in the service**

Add a builder seam near the existing options in `OneOps/app/netpath/service/impl/netpath.go`:

```go
type AnalysisSnapshotBuilder interface {
	BuildSnapshot(ctx context.Context, req dto.SnapshotCreateReq) (*provider.AnalysisSnapshot, string, error)
}

func WithAnalysisSnapshotBuilder(builder AnalysisSnapshotBuilder) Option {
	return func(s *NetPathService) {
		s.analysisSnapshotBuilder = builder
	}
}
```

Add the new field:

```go
	analysisSnapshotBuilder AnalysisSnapshotBuilder
```

Add service methods and minimal helpers:

```go
func (s *NetPathService) CreateSnapshot(ctx context.Context, req dto.SnapshotCreateReq) (*dto.SnapshotResp, error) {
	req = normalizeSnapshotCreateReq(req)
	if req.TenantCode == "" {
		return nil, fmt.Errorf("tenant_code is required")
	}
	if len(req.DeviceCodes) == 0 {
		return nil, fmt.Errorf("device_codes is required")
	}
	if s.analysisSnapshotBuilder == nil {
		return nil, fmt.Errorf("netpath snapshot builder is not configured")
	}
	snap, summary, err := s.analysisSnapshotBuilder.BuildSnapshot(ctx, req)
	if err != nil {
		return nil, err
	}
	record, err := analysisSnapshotToRecord(req, snap, summary)
	if err != nil {
		return nil, err
	}
	if err := s.db.Create(record).Error; err != nil {
		return nil, fmt.Errorf("create netpath snapshot: %w", err)
	}
	return snapshotRecordToResp(record, false)
}

func (s *NetPathService) GetSnapshot(ctx context.Context, tenantCode string, code string, debug bool) (*dto.SnapshotResp, error) {
	var record netpathmodel.NetPathSnapshot
	if err := s.db.WithContext(ctx).
		Where("tenant_code = ? AND code = ?", strings.TrimSpace(tenantCode), strings.TrimSpace(code)).
		First(&record).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, fmt.Errorf("netpath snapshot not found")
		}
		return nil, fmt.Errorf("query netpath snapshot: %w", err)
	}
	return snapshotRecordToResp(&record, debug)
}
```

- [ ] **Step 6: Add API tests**

Add `OneOps/app/netpath/api/netpath_test.go` coverage:

```go
func TestNetPathAPICreateAndGetSnapshot(t *testing.T) {
	db := newNetPathAPITestDB(t)
	svc := impl.NewNetPathService(db, impl.WithAnalysisSnapshotBuilder(&fakeAnalysisSnapshotBuilder{
		snapshot: provider.AnalysisSnapshot{
			SnapshotID: "nps-api-1",
			TenantCode: "tenant-a",
			Quality:    provider.SnapshotQualityReady,
		},
		summary: "api snapshot",
	}))
	router := newNetPathTestRouter(t, svc)

	createBody := `{"tenant_code":"tenant-a","device_codes":["r1"],"ingress_device_code":"r1"}`
	createRec := performAPIRequest(t, router, http.MethodPost, "/netpath/snapshots", createBody)
	assertOK(t, createRec)

	var created response.Response
	if err := json.Unmarshal(createRec.Body.Bytes(), &created); err != nil {
		t.Fatalf("unmarshal create snapshot response: %v", err)
	}

	code := gjson.GetBytes(createRec.Body.Bytes(), "data.code").String()
	getRec := performAPIRequest(t, router, http.MethodGet, "/netpath/snapshots/"+code+"?tenant_code=tenant-a&view=debug", "")
	assertOK(t, getRec)
	if !gjson.GetBytes(getRec.Body.Bytes(), "data.debug_snapshot").Exists() {
		t.Fatalf("expected debug snapshot payload, got %s", getRec.Body.String())
	}
}
```

- [ ] **Step 7: Re-run focused snapshot tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl ./app/netpath/api -run 'TestNetPathService(CreateAndGetSnapshotSummary|GetSnapshotDebugIncludesPayload)$|TestNetPathAPICreateAndGetSnapshot' -count=1
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/netpath/dto/netpath.go app/netpath/service/i_netpath.go app/netpath/api/netpath.go app/netpath/router/netpath.go app/netpath/service/impl/netpath.go app/netpath/service/impl/netpath_test.go app/netpath/api/netpath_test.go
git commit -m "feat: add netpath snapshot persistence api"
```

## Task 3: Connect Snapshot Creation To Latest Facts And Quality Validation

**Files:**
- Modify: `OneOps/app/netpath/service/impl/netpath.go`
- Modify: `OneOps/app/netpath/service/impl/module.go`
- Modify: `OneOps/app/netpath/service/impl/netpath_test.go`

- [ ] **Step 1: Write failing service tests for ready, degraded, and blocked snapshots**

Add tests:

```go
func TestNetPathServiceCreateSnapshotPersistsDegradedQuality(t *testing.T) {
	db := newNetPathTestDB(t)
	svc := NewNetPathService(db, WithAnalysisSnapshotBuilder(&fakeAnalysisSnapshotBuilder{
		snapshot: provider.AnalysisSnapshot{
			SnapshotID: "nps-degraded-1",
			TenantCode: "tenant-a",
			Quality:    provider.SnapshotQualityDegraded,
			Diagnostics: []provider.AnalysisDiagnostic{{
				Severity: provider.SeverityWarn,
				Code:     "route_partial",
				Message:  "partial route visibility",
			}},
		},
		summary: "partial route visibility",
	}))
	created, err := svc.CreateSnapshot(context.Background(), dto.SnapshotCreateReq{
		TenantCode:  "tenant-a",
		DeviceCodes: []string{"r1"},
	})
	if err != nil {
		t.Fatalf("CreateSnapshot returned error: %v", err)
	}
	if created.Quality != "degraded" || len(created.Diagnostics) != 1 {
		t.Fatalf("expected degraded snapshot with diagnostics, got %#v", created)
	}
}

func TestNetPathServiceCreateSnapshotPersistsBlockedQuality(t *testing.T) {
	db := newNetPathTestDB(t)
	svc := NewNetPathService(db, WithAnalysisSnapshotBuilder(&fakeAnalysisSnapshotBuilder{
		snapshot: provider.AnalysisSnapshot{
			SnapshotID: "nps-blocked-1",
			TenantCode: "tenant-a",
			Quality:    provider.SnapshotQualityBlocked,
			Diagnostics: []provider.AnalysisDiagnostic{{
				Severity: provider.SeverityError,
				Code:     "route_missing",
				Message:  "route table missing",
			}},
		},
		summary: "blocked snapshot",
	}))
	created, err := svc.CreateSnapshot(context.Background(), dto.SnapshotCreateReq{
		TenantCode:  "tenant-a",
		DeviceCodes: []string{"r1"},
	})
	if err != nil {
		t.Fatalf("CreateSnapshot returned error: %v", err)
	}
	if created.Quality != "blocked" {
		t.Fatalf("expected blocked snapshot, got %#v", created)
	}
}
```

- [ ] **Step 2: Run the quality tests and verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl -run 'TestNetPathServiceCreateSnapshotPersists(DegradedQuality|BlockedQuality)$' -count=1
```

Expected: FAIL until diagnostics/quality persistence is wired through record<->DTO helpers correctly.

- [ ] **Step 3: Implement a real default latest-fact-backed snapshot builder**

Add a concrete builder in `OneOps/app/netpath/service/impl/netpath.go`:

```go
type latestFactAnalysisSnapshotBuilder struct {
	reader     snapshot.LatestFactReader
	authorizer netpathruntime.DeviceScopeAuthorizer
	assembler  *provider.Assembler
	validator  *provider.Validator
}

func newLatestFactAnalysisSnapshotBuilder(reader snapshot.LatestFactReader, authorizer netpathruntime.DeviceScopeAuthorizer) AnalysisSnapshotBuilder {
	if reader == nil || authorizer == nil {
		return nil
	}
	return &latestFactAnalysisSnapshotBuilder{
		reader:     reader,
		authorizer: authorizer,
		assembler:  provider.NewAssembler(),
		validator:  provider.NewValidator(),
	}
}
```

Implement `BuildSnapshot` using the same fact set currently read in the SDK provider:

```go
func (b *latestFactAnalysisSnapshotBuilder) BuildSnapshot(ctx context.Context, req dto.SnapshotCreateReq) (*provider.AnalysisSnapshot, string, error) {
	if err := b.authorizer.AuthorizeDeviceScope(ctx, req.TenantCode, req.DeviceCodes); err != nil {
		return nil, "", fmt.Errorf("authorize netpath snapshot scope: %w", err)
	}
	facts, err := readAnalysisFactSet(ctx, b.reader, req.DeviceCodes)
	if err != nil {
		return nil, "", err
	}
	snap, err := b.assembler.Assemble(ctx, provider.AssembleRequest{
		TenantCode:  req.TenantCode,
		SnapshotID:  nextSnapshotCode(),
		GeneratedAt: time.Now().UTC(),
		Facts:       facts,
	})
	if err != nil {
		return nil, "", fmt.Errorf("assemble analysis snapshot: %w", err)
	}
	snap.Quality = b.validator.Validate(snap, provider.ValidateRequest{
		IngressDeviceCode: req.IngressDeviceCode,
		IngressVRF:        req.IngressVRF,
	})
	return snap, summarizeAnalysisSnapshot(snap), nil
}
```

- [ ] **Step 4: Wire the default builder in module setup**

Update `OneOps/app/netpath/service/impl/module.go`:

```go
	if builder := newLatestFactAnalysisSnapshotBuilder(reader, authorizer); builder != nil {
		options = append(options, WithAnalysisSnapshotBuilder(builder))
	}
```

- [ ] **Step 5: Re-run focused quality tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl -run 'TestNetPathService(CreateSnapshotPersistsDegradedQuality|CreateSnapshotPersistsBlockedQuality|CreateAndGetSnapshotSummary|GetSnapshotDebugIncludesPayload)$' -count=1
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/netpath/service/impl/netpath.go app/netpath/service/impl/module.go app/netpath/service/impl/netpath_test.go
git commit -m "feat: build netpath snapshots from latest facts"
```

## Task 4: Switch Analysis Runs And SDK Runtime To Snapshot-First

**Files:**
- Modify: `OneOps/app/netpath/service/impl/netpath.go`
- Modify: `OneOps/app/netpath/service/impl/netpath_test.go`
- Modify: `OneOps/app/netpath/runtime/runtime.go`
- Modify: `OneOps/app/netpath/runtime/sdk_enabled.go`
- Modify: `OneOps/app/netpath/runtime/runtime_sdk_test.go`
- Modify: `OneOps/app/netpath/api/netpath_test.go`

- [ ] **Step 1: Write failing run tests for persisted snapshot reuse**

Add tests in `OneOps/app/netpath/service/impl/netpath_test.go`:

```go
func TestNetPathServiceCreateAnalyzeRunCreatesSnapshotWhenSnapshotIDMissing(t *testing.T) {
	db := newNetPathTestDB(t)
	engine := &fakeAnalysisEngine{
		result: &netpathengine.AnalyzeResult{
			SnapshotID:  "nps-auto-1",
			Disposition: "delivered_to_subnet",
			Flow: netpathengine.Flow{
				SrcIP:             "10.0.0.1",
				DstIP:             "10.0.0.2",
				IngressDeviceCode: "r1",
			},
		},
	}
	svc := NewNetPathService(db,
		WithAnalysisEngine(engine),
		WithAnalysisSnapshotBuilder(&fakeAnalysisSnapshotBuilder{
			snapshot: provider.AnalysisSnapshot{
				SnapshotID: "nps-auto-1",
				TenantCode: "tenant-a",
				Quality:    provider.SnapshotQualityReady,
			},
			summary: "auto snapshot",
		}),
	)

	created, err := svc.CreateAnalyzeRun(context.Background(), dto.AnalyzeRunCreateReq{
		TenantCode:        "tenant-a",
		DeviceCodes:       []string{"r1"},
		SrcIP:             "10.0.0.1",
		DstIP:             "10.0.0.2",
		IngressDeviceCode: "r1",
	})
	if err != nil {
		t.Fatalf("CreateAnalyzeRun returned error: %v", err)
	}
	if created.SnapshotID != "nps-auto-1" {
		t.Fatalf("expected stored snapshot id, got %#v", created)
	}
}

func TestNetPathServiceCreateAnalyzeRunFailsClosedForBlockedSnapshot(t *testing.T) {
	db := newNetPathTestDB(t)
	svc := NewNetPathService(db,
		WithAnalysisEngine(&fakeAnalysisEngine{}),
		WithAnalysisSnapshotBuilder(&fakeAnalysisSnapshotBuilder{
			snapshot: provider.AnalysisSnapshot{
				SnapshotID: "nps-blocked-run-1",
				TenantCode: "tenant-a",
				Quality:    provider.SnapshotQualityBlocked,
			},
			summary: "blocked snapshot",
		}),
	)

	_, err := svc.CreateAnalyzeRun(context.Background(), dto.AnalyzeRunCreateReq{
		TenantCode:        "tenant-a",
		DeviceCodes:       []string{"r1"},
		SrcIP:             "10.0.0.1",
		DstIP:             "10.0.0.2",
		IngressDeviceCode: "r1",
	})
	if err == nil || !strings.Contains(err.Error(), "blocked") {
		t.Fatalf("expected blocked snapshot error, got %v", err)
	}
}
```

- [ ] **Step 2: Run the run tests and verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl -run 'TestNetPathServiceCreateAnalyzeRun(CreatesSnapshotWhenSnapshotIDMissing|FailsClosedForBlockedSnapshot)$' -count=1
```

Expected: FAIL because `CreateAnalyzeRun` still uses fake preview snapshot IDs and does not enforce snapshot-first blocked behavior.

- [ ] **Step 3: Make `CreateAnalyzeRun` snapshot-first**

Update `OneOps/app/netpath/service/impl/netpath.go` to:

```go
func (s *NetPathService) CreateAnalyzeRun(ctx context.Context, req dto.AnalyzeRunCreateReq) (*dto.AnalyzeRunResp, error) {
	req = normalizeAnalyzeRunCreateReq(req)
	if req.TenantCode == "" {
		return nil, fmt.Errorf("tenant_code is required")
	}
	if req.SrcIP == "" || req.DstIP == "" || req.IngressDeviceCode == "" {
		return nil, fmt.Errorf("src_ip, dst_ip, and ingress_device_code are required")
	}

	snapshotResp, err := s.ensureSnapshotForAnalyzeRun(ctx, req)
	if err != nil {
		return nil, err
	}
	req.SnapshotID = snapshotResp.Code
	if snapshotResp.Quality == string(provider.SnapshotQualityBlocked) {
		failed := s.buildBlockedSnapshotRun(req, snapshotResp)
		_, storeErr := s.storeAnalyzeRun(ctx, failed)
		if storeErr != nil {
			return nil, storeErr
		}
		return nil, fmt.Errorf("analysis snapshot quality is blocked")
	}

	resp := s.buildAnalyzeRunResp(ctx, req)
	return s.storeAnalyzeRun(ctx, resp)
}
```

- [ ] **Step 4: Add runtime snapshot-store dependencies and store-first SDK lookup**

Update `OneOps/app/netpath/runtime/runtime.go`:

```go
type SnapshotLookup interface {
	GetSnapshot(ctx context.Context, tenantCode string, code string, debug bool) (*dto.SnapshotResp, error)
}

type SnapshotCreator interface {
	CreateSnapshot(ctx context.Context, req dto.SnapshotCreateReq) (*dto.SnapshotResp, error)
}

type Dependencies struct {
	SnapshotReader        snapshot.LatestFactReader
	DeviceScopeAuthorizer DeviceScopeAuthorizer
	SnapshotLookup        SnapshotLookup
	SnapshotCreator       SnapshotCreator
}
```

Update `OneOps/app/netpath/runtime/sdk_enabled.go`:

```go
func (p *ProviderBackedSDKSnapshotProvider) GetSnapshot(ctx context.Context, req netpathengine.AnalyzeRequest) (netpath.Snapshot, error) {
	stored, err := p.resolveStoredSnapshot(ctx, req)
	if err != nil {
		return netpath.Snapshot{}, err
	}
	if stored.Quality == string(provider.SnapshotQualityBlocked) {
		return netpath.Snapshot{}, fmt.Errorf("analysis snapshot quality is blocked")
	}
	return toSDKSnapshotFromStored(stored), nil
}
```

Resolution rules:

- if `req.SnapshotID` is set, lookup persisted snapshot by tenant/code;
- if `req.SnapshotID` is empty, call `SnapshotCreator.CreateSnapshot`;
- only fall back to direct latest-fact assembly if you intentionally preserve a temporary compatibility path, and guard it with a test plus comment.

- [ ] **Step 5: Add runtime tests**

Add `OneOps/app/netpath/runtime/runtime_sdk_test.go` tests:

```go
func TestProviderBackedSDKSnapshotProviderUsesStoredSnapshotWhenSnapshotIDProvided(t *testing.T) {
	// fake lookup returns a stored ready snapshot
	// fake latest fact reader counts calls
	// assert GetSnapshot succeeds and latest fact reader call count stays zero
}

func TestProviderBackedSDKSnapshotProviderRejectsBlockedStoredSnapshot(t *testing.T) {
	// fake lookup returns blocked snapshot
	// assert error contains "blocked"
}
```

- [ ] **Step 6: Re-run focused run/runtime/api tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl ./app/netpath/runtime ./app/netpath/api -run 'TestNetPathServiceCreateAnalyzeRun(CreatesSnapshotWhenSnapshotIDMissing|FailsClosedForBlockedSnapshot)$|TestProviderBackedSDKSnapshotProvider(UsesStoredSnapshotWhenSnapshotIDProvided|RejectsBlockedStoredSnapshot)$|TestNetPathAPICreateAndGetSnapshot|TestNetPathAPIDurableCreateAndGetAnalyzeRun' -count=1
```

Expected: PASS.

- [ ] **Step 7: Run final cross-package verification**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./initialize ./app/netpath/service/impl ./app/netpath/api ./app/netpath/runtime -count=1
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/netpath/service/impl/netpath.go app/netpath/service/impl/netpath_test.go app/netpath/runtime/runtime.go app/netpath/runtime/sdk_enabled.go app/netpath/runtime/runtime_sdk_test.go app/netpath/api/netpath_test.go
git commit -m "feat: make netpath analysis snapshot-first"
```

## Self-Review

Spec coverage check:

- Durable snapshot model: covered by Task 1.
- Snapshot create/get APIs: covered by Task 2.
- Latest-fact-backed snapshot creation: covered by Task 3.
- Snapshot-first analysis runs and runtime lookup: covered by Task 4.

Placeholder scan:

- No `TBD`, `TODO`, or “similar to previous task” references remain.

Type consistency check:

- Snapshot request/response names are consistently `SnapshotCreateReq` and `SnapshotResp`.
- Public service methods are consistently `CreateSnapshot` and `GetSnapshot`.
- Runtime dependency names are consistently `SnapshotLookup` and `SnapshotCreator`.
