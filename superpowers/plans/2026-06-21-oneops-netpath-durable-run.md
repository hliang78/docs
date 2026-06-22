# OneOPS NetPath Durable Run Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden OneOPS NetPath analysis runs into a minimal durable backend capability that stores successful and failed runs in MySQL/sqlite, reconstructs `GetAnalyzeRun` from DB records, and keeps synchronous request behavior unchanged.

**Architecture:** Reuse the existing `netpath_analysis_run` model and DB-backed service path instead of introducing a new task system. Extend the current record with a small set of structured request/result summary fields, make DB-backed services persist and read durable run state as the primary source, and keep full response reconstruction through `result_json`.

**Tech Stack:** Go, GORM, sqlite-backed Go tests, existing OneOPS NetPath service/API/model packages.

---

## File Structure

### Existing files to modify

- `OneOps/app/netpath/netpath_model/run.go`
  - Expand `NetPathAnalysisRun` with structured request and result-summary columns.
- `OneOps/app/netpath/service/impl/netpath.go`
  - Persist the new structured fields, reconstruct responses from DB records, and harden DB-backed read/write behavior.
- `OneOps/app/netpath/service/impl/netpath_test.go`
  - Add DB-first durable run tests for structured persistence, tenant isolation, failed-run persistence, and closed-DB failure.
- `OneOps/app/netpath/api/netpath_test.go`
  - Exercise the durable path through API handlers with a sqlite-backed service instance.
- `OneOps/initialize/mysql_test.go`
  - Keep AutoMigrate column coverage aligned with the expanded durable run schema.

### Optional release-alignment file

- `OneOps/migrations/add_netpath_analysis_run_durable_columns_20260621.sql`
  - Manual SQL companion for environments that do not rely on startup AutoMigrate.

## Task 1: Expand The Durable Run Schema

**Files:**
- Modify: `OneOps/app/netpath/netpath_model/run.go`
- Modify: `OneOps/initialize/mysql_test.go`
- Optional Create: `OneOps/migrations/add_netpath_analysis_run_durable_columns_20260621.sql`

- [ ] **Step 1: Write the failing AutoMigrate column test**

Add the new expected durable columns to `TestNetPathAnalysisRunAutoMigrateColumns` in `OneOps/initialize/mysql_test.go`:

```go
func TestNetPathAnalysisRunAutoMigrateColumns(t *testing.T) {
	db, err := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{})
	if err != nil {
		t.Fatalf("open sqlite failed: %v", err)
	}
	model := &netpathmodel.NetPathAnalysisRun{}
	if err = db.AutoMigrate(model); err != nil {
		t.Fatalf("automigrate netpath analysis run failed: %v", err)
	}

	table := model.TableName()
	for _, column := range []string{
		"code",
		"tenant_code",
		"snapshot_id",
		"status",
		"disposition",
		"src_ip",
		"dst_ip",
		"protocol",
		"src_port",
		"dst_port",
		"ingress_device_code",
		"ingress_interface",
		"ingress_vrf",
		"business_label",
		"device_codes_json",
		"snapshot_quality",
		"source_run_ids_json",
		"diagnostics_json",
		"summary",
		"request_json",
		"result_json",
		"error",
		"created_at",
		"updated_at",
	} {
		if !db.Migrator().HasColumn(table, column) {
			t.Fatalf("expected AutoMigrate to create %s.%s", table, column)
		}
	}
}
```

- [ ] **Step 2: Run the schema test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./initialize -run TestNetPathAnalysisRunAutoMigrateColumns -count=1
```

Expected: FAIL because the new durable columns do not exist on `NetPathAnalysisRun`.

- [ ] **Step 3: Add the structured durable columns to the run model**

Update `OneOps/app/netpath/netpath_model/run.go`:

```go
type NetPathAnalysisRun struct {
	ID                uint      `gorm:"primarykey" json:"id"`
	Code              string    `gorm:"column:code;uniqueIndex;size:64" json:"code"`
	TenantCode        string    `gorm:"column:tenant_code;size:64;index" json:"tenant_code"`
	SnapshotID        string    `gorm:"column:snapshot_id;size:128;index" json:"snapshot_id"`
	Status            string    `gorm:"column:status;size:32;index" json:"status"`
	Disposition       string    `gorm:"column:disposition;size:64;index" json:"disposition"`
	SrcIP             string    `gorm:"column:src_ip;size:64;index" json:"src_ip"`
	DstIP             string    `gorm:"column:dst_ip;size:64;index" json:"dst_ip"`
	Protocol          string    `gorm:"column:protocol;size:32;index" json:"protocol"`
	SrcPort           int       `gorm:"column:src_port" json:"src_port"`
	DstPort           int       `gorm:"column:dst_port" json:"dst_port"`
	IngressDeviceCode string    `gorm:"column:ingress_device_code;size:128;index" json:"ingress_device_code"`
	IngressInterface  string    `gorm:"column:ingress_interface;size:128" json:"ingress_interface"`
	IngressVRF        string    `gorm:"column:ingress_vrf;size:128;index" json:"ingress_vrf"`
	BusinessLabel     string    `gorm:"column:business_label;size:255" json:"business_label"`
	DeviceCodesJSON   string    `gorm:"column:device_codes_json;type:text" json:"device_codes_json"`
	SnapshotQuality   string    `gorm:"column:snapshot_quality;size:32;index" json:"snapshot_quality"`
	SourceRunIDsJSON  string    `gorm:"column:source_run_ids_json;type:text" json:"source_run_ids_json"`
	DiagnosticsJSON   string    `gorm:"column:diagnostics_json;type:longtext" json:"diagnostics_json"`
	Summary           string    `gorm:"column:summary;type:text" json:"summary"`
	RequestJSON       string    `gorm:"column:request_json;type:text" json:"request_json"`
	ResultJSON        string    `gorm:"column:result_json;type:longtext" json:"result_json"`
	Error             string    `gorm:"column:error;type:text" json:"error"`
	CreatedAt         time.Time `json:"created_at"`
	UpdatedAt         time.Time `json:"updated_at"`
}
```

- [ ] **Step 4: Add a companion migration SQL file**

Create `OneOps/migrations/add_netpath_analysis_run_durable_columns_20260621.sql`:

```sql
ALTER TABLE netpath_analysis_run ADD COLUMN src_ip varchar(64) NOT NULL DEFAULT '';
ALTER TABLE netpath_analysis_run ADD COLUMN dst_ip varchar(64) NOT NULL DEFAULT '';
ALTER TABLE netpath_analysis_run ADD COLUMN protocol varchar(32) NOT NULL DEFAULT '';
ALTER TABLE netpath_analysis_run ADD COLUMN src_port int NOT NULL DEFAULT 0;
ALTER TABLE netpath_analysis_run ADD COLUMN dst_port int NOT NULL DEFAULT 0;
ALTER TABLE netpath_analysis_run ADD COLUMN ingress_device_code varchar(128) NOT NULL DEFAULT '';
ALTER TABLE netpath_analysis_run ADD COLUMN ingress_interface varchar(128) NOT NULL DEFAULT '';
ALTER TABLE netpath_analysis_run ADD COLUMN ingress_vrf varchar(128) NOT NULL DEFAULT '';
ALTER TABLE netpath_analysis_run ADD COLUMN business_label varchar(255) NOT NULL DEFAULT '';
ALTER TABLE netpath_analysis_run ADD COLUMN device_codes_json text NOT NULL;
ALTER TABLE netpath_analysis_run ADD COLUMN snapshot_quality varchar(32) NOT NULL DEFAULT '';
ALTER TABLE netpath_analysis_run ADD COLUMN source_run_ids_json text NOT NULL;
ALTER TABLE netpath_analysis_run ADD COLUMN diagnostics_json longtext NOT NULL;
ALTER TABLE netpath_analysis_run ADD COLUMN summary text NOT NULL;
CREATE INDEX idx_netpath_analysis_run_src_ip ON netpath_analysis_run (src_ip);
CREATE INDEX idx_netpath_analysis_run_dst_ip ON netpath_analysis_run (dst_ip);
CREATE INDEX idx_netpath_analysis_run_protocol ON netpath_analysis_run (protocol);
CREATE INDEX idx_netpath_analysis_run_ingress_device_code ON netpath_analysis_run (ingress_device_code);
CREATE INDEX idx_netpath_analysis_run_ingress_vrf ON netpath_analysis_run (ingress_vrf);
CREATE INDEX idx_netpath_analysis_run_snapshot_quality ON netpath_analysis_run (snapshot_quality);
```

If the target MySQL flavor requires guarded DDL, replace the raw `ALTER TABLE` sequence with the repo’s preferred release pattern before execution.

- [ ] **Step 5: Run the schema test to verify it passes**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./initialize -run TestNetPathAnalysisRunAutoMigrateColumns -count=1
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL
git add OneOps/app/netpath/netpath_model/run.go OneOps/initialize/mysql_test.go OneOps/migrations/add_netpath_analysis_run_durable_columns_20260621.sql
git commit -m "feat: expand netpath durable run schema"
```

## Task 2: Persist Structured Durable Run Fields In The Service

**Files:**
- Modify: `OneOps/app/netpath/service/impl/netpath.go`
- Modify: `OneOps/app/netpath/service/impl/netpath_test.go`

- [ ] **Step 1: Write the first failing DB persistence test**

Add a structured-field assertion test near the existing persistence tests in `OneOps/app/netpath/service/impl/netpath_test.go`:

```go
func TestNetPathServicePersistsStructuredAnalyzeRunFieldsToDB(t *testing.T) {
	db := newNetPathTestDB(t)
	engine := &fakeAnalysisEngine{
		result: &netpathengine.AnalyzeResult{
			SnapshotID:  "analysis-structured-1",
			Disposition: "delivered_to_subnet",
			SourceRefs: netpathengine.SourceRefs{
				CollectionRunIDs: []string{"collect-1"},
				FactRunIDs:       []string{"fact-1", "fact-2"},
			},
			Flow: netpathengine.Flow{
				SrcIP:             "10.0.1.10",
				DstIP:             "10.0.2.20",
				Protocol:          "tcp",
				SrcPort:           12345,
				DstPort:           443,
				IngressDeviceCode: "r1",
				IngressInterface:  "ge0/0/1",
				IngressVRF:        "default",
				BusinessLabel:     "payments",
			},
			Traces: []netpathengine.Trace{{
				TraceID:     "trace-1",
				Disposition: "delivered_to_subnet",
			}},
			Diagnostics: []netpathengine.Diagnostic{{
				Severity: "warn",
				Code:     "partial_policy_visibility",
				Message:  "policy facts are incomplete",
			}},
		},
	}
	svc := NewNetPathService(db, WithAnalysisEngine(engine))

	created, err := svc.CreateAnalyzeRun(context.Background(), dto.AnalyzeRunCreateReq{
		TenantCode:        "tenant-a",
		SnapshotID:        "analysis-structured-1",
		SrcIP:             "10.0.1.10",
		DstIP:             "10.0.2.20",
		Protocol:          "tcp",
		SrcPort:           12345,
		DstPort:           443,
		IngressDeviceCode: "r1",
		IngressInterface:  "ge0/0/1",
		IngressVRF:        "default",
		DeviceCodes:       []string{"r1", "r2"},
		BusinessLabel:     "payments",
	})
	if err != nil {
		t.Fatalf("CreateAnalyzeRun returned error: %v", err)
	}

	var record netpathmodel.NetPathAnalysisRun
	if err := db.Where("code = ?", created.Code).First(&record).Error; err != nil {
		t.Fatalf("expected persisted run record: %v", err)
	}
	if record.SrcIP != "10.0.1.10" || record.DstIP != "10.0.2.20" || record.Protocol != "tcp" {
		t.Fatalf("unexpected persisted flow fields: %#v", record)
	}
	if record.IngressDeviceCode != "r1" || record.IngressInterface != "ge0/0/1" || record.IngressVRF != "default" {
		t.Fatalf("unexpected persisted ingress fields: %#v", record)
	}
	if record.BusinessLabel != "payments" || record.DstPort != 443 || record.SrcPort != 12345 {
		t.Fatalf("unexpected persisted request summary: %#v", record)
	}
	if record.SourceRunIDsJSON == "" || record.DiagnosticsJSON == "" {
		t.Fatalf("expected source run ids and diagnostics JSON, got %#v", record)
	}
}
```

- [ ] **Step 2: Run the service test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl -run TestNetPathServicePersistsStructuredAnalyzeRunFieldsToDB -count=1
```

Expected: FAIL because the record mapper does not yet fill the new structured columns.

- [ ] **Step 3: Add durable field extraction helpers and map them into the record**

Update `OneOps/app/netpath/service/impl/netpath.go` by expanding `analyzeRunRespToRecord` and adding small helpers:

```go
func analyzeRunRespToRecord(resp *dto.AnalyzeRunResp) (*netpathmodel.NetPathAnalysisRun, error) {
	if resp == nil {
		return nil, fmt.Errorf("analysis run response is nil")
	}
	requestJSON, err := marshalJSONString(resp.Request, "request_json")
	if err != nil {
		return nil, err
	}
	resultJSON := ""
	if resp.Result != nil {
		resultJSON, err = marshalJSONString(resp.Result, "result_json")
		if err != nil {
			return nil, err
		}
	}
	deviceCodesJSON, err := marshalJSONString(resp.Request.DeviceCodes, "device_codes_json")
	if err != nil {
		return nil, err
	}
	sourceRunIDsJSON, err := marshalJSONString(collectAnalyzeSourceRunIDs(resp.Result), "source_run_ids_json")
	if err != nil {
		return nil, err
	}
	diagnosticsJSON, err := marshalJSONString(collectAnalyzeRunDiagnostics(resp.Result), "diagnostics_json")
	if err != nil {
		return nil, err
	}
	createdAt := time.Unix(resp.CreatedAt, 0)
	if resp.CreatedAt == 0 {
		createdAt = time.Now()
	}
	updatedAt := time.Unix(resp.UpdatedAt, 0)
	if resp.UpdatedAt == 0 {
		updatedAt = createdAt
	}
	return &netpathmodel.NetPathAnalysisRun{
		Code:              resp.Code,
		TenantCode:        resp.TenantCode,
		SnapshotID:        resp.SnapshotID,
		Status:            resp.Status,
		Disposition:       resp.Disposition,
		SrcIP:             resp.Request.SrcIP,
		DstIP:             resp.Request.DstIP,
		Protocol:          resp.Request.Protocol,
		SrcPort:           resp.Request.SrcPort,
		DstPort:           resp.Request.DstPort,
		IngressDeviceCode: resp.Request.IngressDeviceCode,
		IngressInterface:  resp.Request.IngressInterface,
		IngressVRF:        resp.Request.IngressVRF,
		BusinessLabel:     resp.Request.BusinessLabel,
		DeviceCodesJSON:   deviceCodesJSON,
		SnapshotQuality:   summarizeAnalyzeSnapshotQuality(resp),
		SourceRunIDsJSON:  sourceRunIDsJSON,
		DiagnosticsJSON:   diagnosticsJSON,
		Summary:           summarizeAnalyzeRun(resp),
		RequestJSON:       requestJSON,
		ResultJSON:        resultJSON,
		Error:             resp.Error,
		CreatedAt:         createdAt,
		UpdatedAt:         updatedAt,
	}, nil
}

func collectAnalyzeSourceRunIDs(result *dto.AnalyzeResult) []string {
	if result == nil || result.SourceRefs == nil {
		return []string{}
	}
	seen := map[string]struct{}{}
	out := make([]string, 0, len(result.SourceRefs.CollectionRunIDs)+len(result.SourceRefs.FactRunIDs))
	for _, value := range append(append([]string{}, result.SourceRefs.CollectionRunIDs...), result.SourceRefs.FactRunIDs...) {
		value = strings.TrimSpace(value)
		if value == "" {
			continue
		}
		if _, ok := seen[value]; ok {
			continue
		}
		seen[value] = struct{}{}
		out = append(out, value)
	}
	sort.Strings(out)
	return out
}

func collectAnalyzeRunDiagnostics(result *dto.AnalyzeResult) []dto.AnalyzeDiagnostic {
	if result == nil {
		return []dto.AnalyzeDiagnostic{}
	}
	return cloneAnalyzeDiagnostics(result.Diagnostics)
}
```

- [ ] **Step 4: Rehydrate the new structured JSON columns on read**

Extend `analyzeRunRecordToResp` in `OneOps/app/netpath/service/impl/netpath.go` without changing the API shape:

```go
func analyzeRunRecordToResp(record *netpathmodel.NetPathAnalysisRun) (*dto.AnalyzeRunResp, error) {
	if record == nil {
		return nil, fmt.Errorf("analysis run record is nil")
	}
	resp := &dto.AnalyzeRunResp{
		Code:        record.Code,
		TenantCode:  record.TenantCode,
		SnapshotID:  record.SnapshotID,
		Status:      record.Status,
		Disposition: record.Disposition,
		Error:       record.Error,
		CreatedAt:   record.CreatedAt.Unix(),
		UpdatedAt:   record.UpdatedAt.Unix(),
	}
	if err := unmarshalJSONString(record.RequestJSON, &resp.Request, "request_json"); err != nil {
		return nil, err
	}
	if strings.TrimSpace(record.DeviceCodesJSON) != "" && len(resp.Request.DeviceCodes) == 0 {
		if err := unmarshalJSONString(record.DeviceCodesJSON, &resp.Request.DeviceCodes, "device_codes_json"); err != nil {
			return nil, err
		}
	}
	if strings.TrimSpace(record.ResultJSON) != "" {
		var result dto.AnalyzeResult
		if err := unmarshalJSONString(record.ResultJSON, &result, "result_json"); err != nil {
			return nil, err
		}
		hydrateAnalyzeResultEvidence(&result)
		hydrateAnalyzeResultGraph(&result)
		resp.Result = &result
	}
	return cloneAnalyzeRunResp(resp), nil
}
```

- [ ] **Step 5: Add a failing closed-DB write test**

Add this test to `OneOps/app/netpath/service/impl/netpath_test.go`:

```go
func TestNetPathServiceCreateAnalyzeRunFailsWhenDurableWriteFails(t *testing.T) {
	db := newNetPathTestDB(t)
	sqlDB, err := db.DB()
	if err != nil {
		t.Fatalf("db.DB failed: %v", err)
	}
	if err := sqlDB.Close(); err != nil {
		t.Fatalf("close sqlite db failed: %v", err)
	}

	svc := NewNetPathService(db)
	_, err = svc.CreateAnalyzeRun(context.Background(), dto.AnalyzeRunCreateReq{
		TenantCode:        "tenant-a",
		SrcIP:             "10.0.1.10",
		DstIP:             "10.0.2.20",
		IngressDeviceCode: "r1",
	})
	if err == nil {
		t.Fatal("expected durable write failure")
	}
}
```

- [ ] **Step 6: Run the service tests to verify they pass**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl -run 'TestNetPathService(PersistsStructuredAnalyzeRunFieldsToDB|CreateAnalyzeRunFailsWhenDurableWriteFails|PersistsAnalyzeRunToDB|PersistsFailedAnalyzeRunToDB|DBGetHonorsTenantScope)' -count=1
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL
git add OneOps/app/netpath/service/impl/netpath.go OneOps/app/netpath/service/impl/netpath_test.go
git commit -m "feat: persist structured netpath durable run fields"
```

## Task 3: Make DB-Backed Reads The Primary Source And Cover The API Path

**Files:**
- Modify: `OneOps/app/netpath/service/impl/netpath.go`
- Modify: `OneOps/app/netpath/api/netpath_test.go`

- [ ] **Step 1: Write the failing DB-primary read test**

Add this test to `OneOps/app/netpath/service/impl/netpath_test.go`:

```go
func TestNetPathServiceDBBackedGetDoesNotReadMemoryFallback(t *testing.T) {
	db := newNetPathTestDB(t)
	svc := NewNetPathService(db)

	run, err := svc.CreateAnalyzeRun(context.Background(), dto.AnalyzeRunCreateReq{
		TenantCode:        "tenant-a",
		SrcIP:             "10.0.1.10",
		DstIP:             "10.0.2.20",
		IngressDeviceCode: "r1",
	})
	if err != nil {
		t.Fatalf("CreateAnalyzeRun returned error: %v", err)
	}

	if err := db.Where("code = ?", run.Code).Delete(&netpathmodel.NetPathAnalysisRun{}).Error; err != nil {
		t.Fatalf("delete persisted run failed: %v", err)
	}

	_, err = svc.GetAnalyzeRun(context.Background(), "tenant-a", run.Code)
	if err == nil {
		t.Fatal("expected not found after deleting durable record")
	}
}
```

- [ ] **Step 2: Run the DB-primary read test to verify it fails if memory fallback leaks through**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl -run TestNetPathServiceDBBackedGetDoesNotReadMemoryFallback -count=1
```

Expected: PASS if the current DB-backed path is already primary. If it passes immediately, keep the test and proceed; it protects the durable contract from regressions.

- [ ] **Step 3: Add a durable API test that uses sqlite instead of a nil DB**

Extend `OneOps/app/netpath/api/netpath_test.go` with a DB-backed create/get round trip:

```go
func TestNetPathAPIAnalyzeRunUsesDurableStore(t *testing.T) {
	gin.SetMode(gin.TestMode)

	svc := impl.NewNetPathService(newNetPathAPITestDB(t), impl.WithTaskCreationService(apiFakeTaskCreationService{}))
	api := &NetPathAPI{
		Logger:     zap.NewNop(),
		NetPathSrv: svc,
	}

	router := gin.New()
	router.POST("/netpath/analysis-runs", api.CreateAnalyzeRun)
	router.GET("/netpath/analysis-runs/:code", api.GetAnalyzeRun)

	createRec := performNetPathAPIRequest(t, router, http.MethodPost, "/netpath/analysis-runs", dto.AnalyzeRunCreateReq{
		TenantCode:        "tenant-a",
		SrcIP:             "10.0.0.1",
		DstIP:             "10.0.0.2",
		Protocol:          "tcp",
		DstPort:           443,
		IngressDeviceCode: "leaf-1",
		DeviceCodes:       []string{"leaf-1", "leaf-2"},
	})
	if createRec.Code != http.StatusOK {
		t.Fatalf("expected create 200, got %d body=%s", createRec.Code, createRec.Body.String())
	}

	var createEnvelope netPathAPIEnvelope
	if err := json.Unmarshal(createRec.Body.Bytes(), &createEnvelope); err != nil {
		t.Fatalf("unmarshal create envelope failed: %v", err)
	}
	var created dto.AnalyzeRunResp
	if err := json.Unmarshal(createEnvelope.Data, &created); err != nil {
		t.Fatalf("unmarshal create payload failed: %v", err)
	}

	getRec := performNetPathAPIRequest(t, router, http.MethodGet, "/netpath/analysis-runs/"+created.Code+"?tenant_code=tenant-a", nil)
	if getRec.Code != http.StatusOK {
		t.Fatalf("expected get 200, got %d body=%s", getRec.Code, getRec.Body.String())
	}
}
```

Add the sqlite helper to the same file:

```go
func newNetPathAPITestDB(t *testing.T) *gorm.DB {
	t.Helper()
	db, err := gorm.Open(sqlite.Open("file:"+t.Name()+"?mode=memory&cache=shared"), &gorm.Config{})
	if err != nil {
		t.Fatalf("open sqlite failed: %v", err)
	}
	if err := db.AutoMigrate(&netpathmodel.NetPathAnalysisRun{}); err != nil {
		t.Fatalf("migrate api sqlite db failed: %v", err)
	}
	return db
}
```

- [ ] **Step 4: Run the API durable test**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/api -run TestNetPathAPIAnalyzeRunUsesDurableStore -count=1
```

Expected: PASS.

- [ ] **Step 5: Run the focused durable run suite**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl ./app/netpath/api ./initialize -run 'Test(NetPath(Service(PersistsStructuredAnalyzeRunFieldsToDB|CreateAnalyzeRunFailsWhenDurableWriteFails|PersistsAnalyzeRunToDB|PersistsFailedAnalyzeRunToDB|DBGetHonorsTenantScope|DBBackedGetDoesNotReadMemoryFallback)|APIAnalyzeRunUsesDurableStore)|NetPathAnalysisRunAutoMigrateColumns)' -count=1
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL
git add OneOps/app/netpath/service/impl/netpath.go OneOps/app/netpath/service/impl/netpath_test.go OneOps/app/netpath/api/netpath_test.go OneOps/initialize/mysql_test.go
git commit -m "test: harden netpath durable run persistence"
```

## Self-Review Notes

Spec coverage:

- Synchronous `CreateAnalyzeRun` preserved: Task 2.
- Durable successful and failed runs: Task 2.
- DB-backed `GetAnalyzeRun`: Task 3.
- Tenant-safe retrieval: existing coverage retained and rerun in Task 2.
- Structured fields plus full `result_json`: Tasks 1 and 2.

Placeholder scan:

- No `TBD` or deferred implementation placeholders remain.
- Commands and concrete code snippets are included for each code step.

Type consistency:

- Plan uses existing `NetPathAnalysisRun`, `AnalyzeRunResp`, and `AnalyzeRunCreateReq` names from the current codebase.
- New helper names introduced in Task 2 are reused consistently inside the same task.
