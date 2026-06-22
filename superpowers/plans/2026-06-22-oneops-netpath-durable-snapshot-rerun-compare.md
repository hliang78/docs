# OneOPS NetPath Durable Snapshot Rerun And Compare Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tighten NetPath rerun and run-compare onto durable snapshot semantics, and add a snapshot-to-snapshot compare API over stored `netpath_snapshot` records.

**Architecture:** Extend the existing NetPath DTO/service/API surface instead of introducing a new subsystem. Reuse durable `GetSnapshot` lookups to fail closed on non-durable references, enrich run-compare responses with snapshot summary context, and add a lightweight snapshot-compare endpoint that diffs persisted snapshot metadata without re-running analysis.

**Tech Stack:** Go, GORM, sqlite-backed Go tests, existing OneOPS NetPath DTO/API/router/service packages.

---

## File Structure

### Existing files to modify

- `OneOps/app/netpath/dto/netpath.go`
  - Add snapshot summary and snapshot-compare DTOs used by service and API layers.
- `OneOps/app/netpath/service/i_netpath.go`
  - Expose the snapshot-compare service method on the public NetPath interface.
- `OneOps/app/netpath/service/impl/netpath.go`
  - Tighten `RerunAnalyzeRun`, harden `CompareAnalyzeRuns`, add `CompareSnapshots`, and add snapshot summary/diff helpers.
- `OneOps/app/netpath/service/impl/netpath_test.go`
  - Add service-level fail-closed and snapshot-compare coverage.
- `OneOps/app/netpath/api/netpath.go`
  - Add the `CompareSnapshots` handler.
- `OneOps/app/netpath/api/netpath_test.go`
  - Exercise snapshot-compare and enriched run-compare payloads through HTTP handlers.
- `OneOps/app/netpath/router/netpath.go`
  - Register the snapshot-compare route.
- `OneOps/app/netpath/router/netpath_test.go`
  - Verify the new route is wired.

## Task 1: Add Snapshot Compare DTOs And Service Interface

**Files:**
- Modify: `OneOps/app/netpath/dto/netpath.go`
- Modify: `OneOps/app/netpath/service/i_netpath.go`

- [ ] **Step 1: Write the failing DTO/service interface test**

Add a compile-focused DTO usage test in `OneOps/app/netpath/api/netpath_test.go` near the existing handler tests:

```go
func TestNetPathAPICompareSnapshotsPayloadShape(t *testing.T) {
	_ = dto.AnalyzeRunCompareResp{
		BaselineSnapshot: &dto.SnapshotCompareSummary{
			Code:         "snapshot-base",
			Quality:      "ready",
			Summary:      "baseline",
			DeviceCodes:  []string{"leaf-1"},
			SourceRunIDs: []string{"collect-1", "fact-1"},
		},
		TargetSnapshot: &dto.SnapshotCompareSummary{
			Code:         "snapshot-followup",
			Quality:      "degraded",
			Summary:      "target",
			DeviceCodes:  []string{"leaf-1", "fw-1"},
			SourceRunIDs: []string{"collect-2"},
		},
	}

	_ = dto.SnapshotCompareReq{
		TenantCode:         "tenant-a",
		BaselineSnapshotID: "snapshot-base",
		TargetSnapshotID:   "snapshot-followup",
	}

	_ = dto.SnapshotCompareResp{
		TenantCode:         "tenant-a",
		BaselineSnapshotID: "snapshot-base",
		TargetSnapshotID:   "snapshot-followup",
		QualityChanged:     true,
	}
}
```

- [ ] **Step 2: Run the focused API test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/api -run TestNetPathAPICompareSnapshotsPayloadShape -count=1
```

Expected: FAIL with `undefined: dto.SnapshotCompareSummary`, `undefined: dto.SnapshotCompareReq`, and `undefined: dto.SnapshotCompareResp`.

- [ ] **Step 3: Add the DTOs**

Update `OneOps/app/netpath/dto/netpath.go` by extending `AnalyzeRunCompareResp` and adding the new compare types:

```go
type AnalyzeRunCompareResp struct {
	BaselineRunCode     string                    `json:"baseline_run_code"`
	TargetRunCode       string                    `json:"target_run_code"`
	TenantCode          string                    `json:"tenant_code"`
	BaselineSnapshotID  string                    `json:"baseline_snapshot_id,omitempty"`
	TargetSnapshotID    string                    `json:"target_snapshot_id,omitempty"`
	BaselineSnapshot    *SnapshotCompareSummary   `json:"baseline_snapshot,omitempty"`
	TargetSnapshot      *SnapshotCompareSummary   `json:"target_snapshot,omitempty"`
	BaselineDisposition string                    `json:"baseline_disposition,omitempty"`
	TargetDisposition   string                    `json:"target_disposition,omitempty"`
	DispositionChanged  bool                      `json:"disposition_changed,omitempty"`
	BaselineHops        []AnalyzeCompareHop       `json:"baseline_hops,omitempty"`
	TargetHops          []AnalyzeCompareHop       `json:"target_hops,omitempty"`
	AddedHops           []AnalyzeCompareHop       `json:"added_hops,omitempty"`
	RemovedHops         []AnalyzeCompareHop       `json:"removed_hops,omitempty"`
	BaselineBlockers    []AnalyzeDiagnostic       `json:"baseline_blockers,omitempty"`
	TargetBlockers      []AnalyzeDiagnostic       `json:"target_blockers,omitempty"`
	AddedBlockers       []AnalyzeDiagnostic       `json:"added_blockers,omitempty"`
	RemovedBlockers     []AnalyzeDiagnostic       `json:"removed_blockers,omitempty"`
	BaselinePathSummary *AnalyzeTicketPathSummary `json:"baseline_path_summary,omitempty"`
	TargetPathSummary   *AnalyzeTicketPathSummary `json:"target_path_summary,omitempty"`
	Summary             string                    `json:"summary,omitempty"`
}

type SnapshotCompareSummary struct {
	Code         string   `json:"code"`
	Quality      string   `json:"quality,omitempty"`
	Summary      string   `json:"summary,omitempty"`
	DeviceCodes  []string `json:"device_codes,omitempty"`
	SourceRunIDs []string `json:"source_run_ids,omitempty"`
}

type SnapshotCompareReq struct {
	TenantCode         string `json:"tenant_code" form:"tenant_code"`
	BaselineSnapshotID string `json:"baseline_snapshot_id" form:"baseline_snapshot_id"`
	TargetSnapshotID   string `json:"target_snapshot_id" form:"target_snapshot_id"`
}

type SnapshotCompareResp struct {
	TenantCode            string              `json:"tenant_code"`
	BaselineSnapshotID    string              `json:"baseline_snapshot_id"`
	TargetSnapshotID      string              `json:"target_snapshot_id"`
	BaselineQuality       string              `json:"baseline_quality,omitempty"`
	TargetQuality         string              `json:"target_quality,omitempty"`
	QualityChanged        bool                `json:"quality_changed,omitempty"`
	BaselineSummary       string              `json:"baseline_summary,omitempty"`
	TargetSummary         string              `json:"target_summary,omitempty"`
	BaselineDeviceCodes   []string            `json:"baseline_device_codes,omitempty"`
	TargetDeviceCodes     []string            `json:"target_device_codes,omitempty"`
	AddedDeviceCodes      []string            `json:"added_device_codes,omitempty"`
	RemovedDeviceCodes    []string            `json:"removed_device_codes,omitempty"`
	BaselineDiagnostics   []AnalyzeDiagnostic `json:"baseline_diagnostics,omitempty"`
	TargetDiagnostics     []AnalyzeDiagnostic `json:"target_diagnostics,omitempty"`
	AddedDiagnostics      []AnalyzeDiagnostic `json:"added_diagnostics,omitempty"`
	RemovedDiagnostics    []AnalyzeDiagnostic `json:"removed_diagnostics,omitempty"`
	BaselineSourceRunIDs  []string            `json:"baseline_source_run_ids,omitempty"`
	TargetSourceRunIDs    []string            `json:"target_source_run_ids,omitempty"`
	Summary               string              `json:"summary,omitempty"`
}
```

- [ ] **Step 4: Add the service interface method**

Update `OneOps/app/netpath/service/i_netpath.go`:

```go
type INetPathService interface {
	PreviewSnapshot(ctx context.Context, req dto.SnapshotPreviewReq) (*dto.SnapshotPreviewResp, error)
	CreateSnapshot(ctx context.Context, req dto.SnapshotCreateReq) (*dto.SnapshotResp, error)
	GetSnapshot(ctx context.Context, tenantCode string, code string, debug bool) (*dto.SnapshotResp, error)
	CreateAnalyzeRun(ctx context.Context, req dto.AnalyzeRunCreateReq) (*dto.AnalyzeRunResp, error)
	RerunAnalyzeRun(ctx context.Context, code string, req dto.AnalyzeRunRerunReq) (*dto.AnalyzeRunRerunResp, error)
	ListAnalyzeRuns(ctx context.Context, req dto.AnalyzeRunListReq) (*dto.AnalyzeRunListResp, error)
	GetAnalyzeRun(ctx context.Context, tenantCode string, code string) (*dto.AnalyzeRunResp, error)
	CompareAnalyzeRuns(ctx context.Context, tenantCode string, code string, targetRunCode string) (*dto.AnalyzeRunCompareResp, error)
	CompareSnapshots(ctx context.Context, req dto.SnapshotCompareReq) (*dto.SnapshotCompareResp, error)
	GetAnalyzeRunDeviceEvidence(ctx context.Context, tenantCode string, code string, deviceCode string) (*dto.AnalyzeRunDeviceEvidenceResp, error)
	// ...
}
```

- [ ] **Step 5: Re-run the focused API test**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/api -run TestNetPathAPICompareSnapshotsPayloadShape -count=1
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/netpath/dto/netpath.go app/netpath/service/i_netpath.go app/netpath/api/netpath_test.go
git commit -m "feat: add netpath snapshot compare dto surface"
```

## Task 2: Tighten Rerun And Run Compare To Durable Snapshot Semantics

**Files:**
- Modify: `OneOps/app/netpath/service/impl/netpath.go`
- Modify: `OneOps/app/netpath/service/impl/netpath_test.go`

- [ ] **Step 1: Write the failing service tests**

Add the following tests in `OneOps/app/netpath/service/impl/netpath_test.go` near `TestNetPathServiceRerunAndCompareAnalyzeRun`:

```go
func TestNetPathServiceRerunAnalyzeRunRejectsPreviewSnapshotReference(t *testing.T) {
	svc, _ := newSeededAnalyzeRunTestService(t, "tenant-a", "snapshot-base", "leaf-1")

	run := &dto.AnalyzeRunResp{
		Code:       "run-preview",
		TenantCode: "tenant-a",
		SnapshotID: "snapshot-base",
		Status:     "completed",
		Request: dto.AnalyzeRunCreateReq{
			TenantCode:        "tenant-a",
			SnapshotID:        "snapshot-base",
			SrcIP:             "10.0.1.10",
			DstIP:             "10.0.2.20",
			Protocol:          "tcp",
			DstPort:           443,
			IngressDeviceCode: "leaf-1",
		},
	}
	if err := persistAnalyzeRunForTest(svc.db, run); err != nil {
		t.Fatalf("persist baseline run failed: %v", err)
	}

	_, err := svc.RerunAnalyzeRun(context.Background(), "run-preview", dto.AnalyzeRunRerunReq{
		TenantCode: "tenant-a",
		SnapshotID: "preview-tenant-a",
	})
	if err == nil || !strings.Contains(err.Error(), "non-durable") {
		t.Fatalf("expected non-durable snapshot error, got %v", err)
	}
}

func TestNetPathServiceCompareAnalyzeRunsIncludesSnapshotSummaries(t *testing.T) {
	db := newNetPathTestDB(t)
	seedDurableSnapshotForTest(t, db, "tenant-a", "snapshot-base", "leaf-1")
	seedDurableSnapshotForTest(t, db, "tenant-a", "snapshot-followup", "leaf-1", "fw-1")
	svc := NewNetPathService(db)

	baseline := &dto.AnalyzeRunResp{
		Code:        "run-base",
		TenantCode:  "tenant-a",
		SnapshotID:  "snapshot-base",
		Status:      "completed",
		Disposition: "blocked_acl",
		Request: dto.AnalyzeRunCreateReq{TenantCode: "tenant-a", SnapshotID: "snapshot-base", SrcIP: "10.0.1.10", DstIP: "10.0.2.20", IngressDeviceCode: "leaf-1"},
		Result: &dto.AnalyzeResult{SnapshotID: "snapshot-base", Flow: dto.AnalyzeFlow{SrcIP: "10.0.1.10", DstIP: "10.0.2.20"}, Traces: []dto.AnalyzeTrace{{Disposition: "blocked_acl", Hops: []dto.AnalyzeHop{{Sequence: 1, DeviceCode: "leaf-1"}}}}},
	}
	target := &dto.AnalyzeRunResp{
		Code:        "run-target",
		TenantCode:  "tenant-a",
		SnapshotID:  "snapshot-followup",
		Status:      "completed",
		Disposition: "delivered_to_subnet",
		Request: dto.AnalyzeRunCreateReq{TenantCode: "tenant-a", SnapshotID: "snapshot-followup", SrcIP: "10.0.1.10", DstIP: "10.0.2.20", IngressDeviceCode: "leaf-1"},
		Result: &dto.AnalyzeResult{SnapshotID: "snapshot-followup", Flow: dto.AnalyzeFlow{SrcIP: "10.0.1.10", DstIP: "10.0.2.20"}, Traces: []dto.AnalyzeTrace{{Disposition: "delivered_to_subnet", Hops: []dto.AnalyzeHop{{Sequence: 1, DeviceCode: "leaf-1"}, {Sequence: 2, DeviceCode: "fw-1"}}}}},
	}
	if err := persistAnalyzeRunForTest(db, baseline); err != nil {
		t.Fatalf("persist baseline run failed: %v", err)
	}
	if err := persistAnalyzeRunForTest(db, target); err != nil {
		t.Fatalf("persist target run failed: %v", err)
	}

	resp, err := svc.CompareAnalyzeRuns(context.Background(), "tenant-a", "run-base", "run-target")
	if err != nil {
		t.Fatalf("CompareAnalyzeRuns returned error: %v", err)
	}
	if resp.BaselineSnapshot == nil || resp.TargetSnapshot == nil {
		t.Fatalf("expected snapshot summaries, got %#v", resp)
	}
	if resp.BaselineSnapshot.Code != "snapshot-base" || resp.TargetSnapshot.Code != "snapshot-followup" {
		t.Fatalf("unexpected snapshot summary codes: %#v", resp)
	}
}

func TestNetPathServiceCompareAnalyzeRunsRejectsMissingDurableSnapshot(t *testing.T) {
	db := newNetPathTestDB(t)
	svc := NewNetPathService(db)

	baseline := &dto.AnalyzeRunResp{
		Code:        "run-legacy",
		TenantCode:  "tenant-a",
		SnapshotID:  "preview-tenant-a",
		Status:      "completed",
		Disposition: "blocked_acl",
		Request: dto.AnalyzeRunCreateReq{TenantCode: "tenant-a", SnapshotID: "preview-tenant-a", SrcIP: "10.0.1.10", DstIP: "10.0.2.20", IngressDeviceCode: "leaf-1"},
		Result:      &dto.AnalyzeResult{SnapshotID: "preview-tenant-a", Flow: dto.AnalyzeFlow{SrcIP: "10.0.1.10", DstIP: "10.0.2.20"}},
	}
	target := &dto.AnalyzeRunResp{
		Code:        "run-target",
		TenantCode:  "tenant-a",
		SnapshotID:  "snapshot-followup",
		Status:      "completed",
		Disposition: "delivered_to_subnet",
		Request: dto.AnalyzeRunCreateReq{TenantCode: "tenant-a", SnapshotID: "snapshot-followup", SrcIP: "10.0.1.10", DstIP: "10.0.2.20", IngressDeviceCode: "leaf-1"},
		Result:      &dto.AnalyzeResult{SnapshotID: "snapshot-followup", Flow: dto.AnalyzeFlow{SrcIP: "10.0.1.10", DstIP: "10.0.2.20"}},
	}
	seedDurableSnapshotForTest(t, db, "tenant-a", "snapshot-followup", "leaf-1")
	if err := persistAnalyzeRunForTest(db, baseline); err != nil {
		t.Fatalf("persist baseline run failed: %v", err)
	}
	if err := persistAnalyzeRunForTest(db, target); err != nil {
		t.Fatalf("persist target run failed: %v", err)
	}

	_, err := svc.CompareAnalyzeRuns(context.Background(), "tenant-a", "run-legacy", "run-target")
	if err == nil || !strings.Contains(err.Error(), "non-durable snapshot") {
		t.Fatalf("expected non-durable snapshot error, got %v", err)
	}
}
```

- [ ] **Step 2: Run the focused service tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl -run 'TestNetPathService(RerunAnalyzeRunRejectsPreviewSnapshotReference|CompareAnalyzeRunsIncludesSnapshotSummaries|CompareAnalyzeRunsRejectsMissingDurableSnapshot)' -count=1
```

Expected: FAIL because rerun does not yet reject preview snapshot IDs and run compare does not yet load or return snapshot summaries.

- [ ] **Step 3: Tighten rerun and run compare in the service**

Update `OneOps/app/netpath/service/impl/netpath.go`:

```go
func (s *NetPathService) RerunAnalyzeRun(ctx context.Context, code string, req dto.AnalyzeRunRerunReq) (*dto.AnalyzeRunRerunResp, error) {
	req = normalizeAnalyzeRunRerunReq(req)
	code = strings.TrimSpace(code)
	if req.TenantCode == "" {
		return nil, fmt.Errorf("tenant_code is required")
	}
	if code == "" {
		return nil, fmt.Errorf("code is required")
	}
	if req.SnapshotID == "" {
		return nil, fmt.Errorf("snapshot_id is required")
	}

	baseline, err := s.GetAnalyzeRun(ctx, req.TenantCode, code)
	if err != nil {
		return nil, err
	}
	targetSnapshot, err := s.requireDurableSnapshotForCompare(ctx, req.TenantCode, req.SnapshotID)
	if err != nil {
		return nil, err
	}
	if strings.EqualFold(targetSnapshot.Quality, string(provider.SnapshotQualityBlocked)) {
		return nil, fmt.Errorf("analysis snapshot %s quality is blocked", targetSnapshot.Code)
	}

	rerunReq := baseline.Request
	rerunReq.TenantCode = baseline.TenantCode
	rerunReq.SnapshotID = targetSnapshot.Code

	rerun, err := s.CreateAnalyzeRun(ctx, rerunReq)
	if err != nil {
		return nil, err
	}
	return &dto.AnalyzeRunRerunResp{
		BaselineRunCode: baseline.Code,
		TenantCode:      rerun.TenantCode,
		SnapshotID:      rerun.SnapshotID,
		AnalyzeRun:      rerun,
		CompareAPI:      fmt.Sprintf("/api/netpath/analysis-runs/%s/compare?tenant_code=%s&target_run_code=%s", baseline.Code, baseline.TenantCode, rerun.Code),
	}, nil
}

func (s *NetPathService) CompareAnalyzeRuns(ctx context.Context, tenantCode string, code string, targetRunCode string) (*dto.AnalyzeRunCompareResp, error) {
	tenantCode = strings.TrimSpace(tenantCode)
	code = strings.TrimSpace(code)
	targetRunCode = strings.TrimSpace(targetRunCode)
	if tenantCode == "" {
		return nil, fmt.Errorf("tenant_code is required")
	}
	if code == "" {
		return nil, fmt.Errorf("code is required")
	}
	if targetRunCode == "" {
		return nil, fmt.Errorf("target_run_code is required")
	}

	baseline, err := s.GetAnalyzeRun(ctx, tenantCode, code)
	if err != nil {
		return nil, err
	}
	target, err := s.GetAnalyzeRun(ctx, tenantCode, targetRunCode)
	if err != nil {
		return nil, err
	}
	baselineSnapshot, err := s.requireDurableSnapshotForCompare(ctx, tenantCode, baseline.SnapshotID)
	if err != nil {
		return nil, err
	}
	targetSnapshot, err := s.requireDurableSnapshotForCompare(ctx, tenantCode, target.SnapshotID)
	if err != nil {
		return nil, err
	}

	baselineHops := buildAnalyzeCompareHops(baseline)
	targetHops := buildAnalyzeCompareHops(target)
	baselineBlockers := collectAnalyzeRunBlockers(baseline)
	targetBlockers := collectAnalyzeRunBlockers(target)
	addedHops, removedHops := diffAnalyzeCompareHops(baselineHops, targetHops)
	addedBlockers, removedBlockers := diffAnalyzeDiagnostics(baselineBlockers, targetBlockers)

	resp := &dto.AnalyzeRunCompareResp{
		BaselineRunCode:     baseline.Code,
		TargetRunCode:       target.Code,
		TenantCode:          tenantCode,
		BaselineSnapshotID:  baseline.SnapshotID,
		TargetSnapshotID:    target.SnapshotID,
		BaselineSnapshot:    snapshotRespToCompareSummary(baselineSnapshot),
		TargetSnapshot:      snapshotRespToCompareSummary(targetSnapshot),
		BaselineDisposition: baseline.Disposition,
		TargetDisposition:   target.Disposition,
		DispositionChanged:  baseline.Disposition != target.Disposition,
		BaselineHops:        baselineHops,
		TargetHops:          targetHops,
		AddedHops:           addedHops,
		RemovedHops:         removedHops,
		BaselineBlockers:    baselineBlockers,
		TargetBlockers:      targetBlockers,
		AddedBlockers:       addedBlockers,
		RemovedBlockers:     removedBlockers,
		BaselinePathSummary: buildAnalyzeComparePathSummary(baseline),
		TargetPathSummary:   buildAnalyzeComparePathSummary(target),
	}
	resp.Summary = buildAnalyzeRunCompareSummary(resp)
	return resp, nil
}
```

Add the helpers nearby in the same file:

```go
func (s *NetPathService) requireDurableSnapshotForCompare(ctx context.Context, tenantCode string, snapshotID string) (*dto.SnapshotResp, error) {
	snapshotID = strings.TrimSpace(snapshotID)
	if snapshotID == "" {
		return nil, fmt.Errorf("snapshot_id is required")
	}
	if strings.HasPrefix(snapshotID, "preview-") {
		return nil, fmt.Errorf("run references non-durable snapshot: %s", snapshotID)
	}
	snap, err := s.GetSnapshot(ctx, tenantCode, snapshotID, false)
	if err != nil {
		if strings.Contains(err.Error(), "not found") {
			return nil, fmt.Errorf("run references non-durable snapshot: %s", snapshotID)
		}
		return nil, err
	}
	return snap, nil
}

func snapshotRespToCompareSummary(resp *dto.SnapshotResp) *dto.SnapshotCompareSummary {
	if resp == nil {
		return nil
	}
	return &dto.SnapshotCompareSummary{
		Code:         resp.Code,
		Quality:      resp.Quality,
		Summary:      resp.Summary,
		DeviceCodes:  append([]string(nil), resp.DeviceCodes...),
		SourceRunIDs: append([]string(nil), resp.SourceRunIDs...),
	}
}
```

- [ ] **Step 4: Re-run the focused service tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl -run 'TestNetPathService(RerunAnalyzeRunRejectsPreviewSnapshotReference|CompareAnalyzeRunsIncludesSnapshotSummaries|CompareAnalyzeRunsRejectsMissingDurableSnapshot|RerunAndCompareAnalyzeRun)' -count=1
```

Expected: PASS.

- [ ] **Step 5: Run the broader NetPath service tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl -count=1
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/netpath/service/impl/netpath.go app/netpath/service/impl/netpath_test.go
git commit -m "fix: harden netpath durable rerun compare semantics"
```

## Task 3: Add Snapshot Compare Service, API, Router, And HTTP Tests

**Files:**
- Modify: `OneOps/app/netpath/service/impl/netpath.go`
- Modify: `OneOps/app/netpath/service/impl/netpath_test.go`
- Modify: `OneOps/app/netpath/api/netpath.go`
- Modify: `OneOps/app/netpath/api/netpath_test.go`
- Modify: `OneOps/app/netpath/router/netpath.go`
- Modify: `OneOps/app/netpath/router/netpath_test.go`

- [ ] **Step 1: Write the failing snapshot compare service and API tests**

Add service tests in `OneOps/app/netpath/service/impl/netpath_test.go`:

```go
func TestNetPathServiceCompareSnapshots(t *testing.T) {
	db := newNetPathTestDB(t)
	seedDurableSnapshotForTest(t, db, "tenant-a", "snapshot-base", "leaf-1")
	seedDurableSnapshotForTest(t, db, "tenant-a", "snapshot-followup", "leaf-1", "fw-1")
	svc := NewNetPathService(db)

	resp, err := svc.CompareSnapshots(context.Background(), dto.SnapshotCompareReq{
		TenantCode:         "tenant-a",
		BaselineSnapshotID: "snapshot-base",
		TargetSnapshotID:   "snapshot-followup",
	})
	if err != nil {
		t.Fatalf("CompareSnapshots returned error: %v", err)
	}
	if resp.BaselineSnapshotID != "snapshot-base" || resp.TargetSnapshotID != "snapshot-followup" {
		t.Fatalf("unexpected snapshot ids: %#v", resp)
	}
	if len(resp.AddedDeviceCodes) != 1 || resp.AddedDeviceCodes[0] != "fw-1" {
		t.Fatalf("expected added device fw-1, got %#v", resp)
	}
}

func TestNetPathServiceCompareSnapshotsHonorsTenantIsolation(t *testing.T) {
	db := newNetPathTestDB(t)
	seedDurableSnapshotForTest(t, db, "tenant-b", "snapshot-b", "leaf-9")
	svc := NewNetPathService(db)

	_, err := svc.CompareSnapshots(context.Background(), dto.SnapshotCompareReq{
		TenantCode:         "tenant-a",
		BaselineSnapshotID: "snapshot-b",
		TargetSnapshotID:   "snapshot-b",
	})
	if err == nil || !strings.Contains(err.Error(), "not found") {
		t.Fatalf("expected tenant-scoped not found, got %v", err)
	}
}
```

Add API coverage in `OneOps/app/netpath/api/netpath_test.go`:

```go
t.Run("compare snapshots returns typed payload", func(t *testing.T) {
	svc, _, _ := newNetPathAPIAnalyzeRunService(t)
	api := &NetPathAPI{Logger: zap.NewNop(), NetPathSrv: svc}
	router := gin.New()
	router.GET("/netpath/snapshots/compare", api.CompareSnapshots)

	rec := performNetPathAPIRequest(t, router, http.MethodGet, "/netpath/snapshots/compare?tenant_code=tenant-a&baseline_snapshot_id=snapshot-base&target_snapshot_id=snapshot-followup", nil)
	if rec.Code != http.StatusOK {
		t.Fatalf("expected status 200, got %d body=%s", rec.Code, rec.Body.String())
	}

	envelope := decodeNetPathAPIEnvelope(t, rec)
	var resp dto.SnapshotCompareResp
	if err := json.Unmarshal(envelope.Data, &resp); err != nil {
		t.Fatalf("unmarshal snapshot compare response failed: %v body=%s", err, rec.Body.String())
	}
	if resp.BaselineSnapshotID == "" || resp.TargetSnapshotID == "" {
		t.Fatalf("expected snapshot compare ids, got %#v", resp)
	}
})
```

Add the route registration check in `OneOps/app/netpath/router/netpath_test.go`:

```go
rec = httptest.NewRecorder()
req = httptest.NewRequest(http.MethodGet, "/api/netpath/snapshots/compare?tenant_code=tenant-a&baseline_snapshot_id=snapshot-base&target_snapshot_id=snapshot-followup", nil)
engine.ServeHTTP(rec, req)

if rec.Code != http.StatusOK {
	t.Fatalf("expected registered snapshot compare route status 200, got %d body=%s", rec.Code, rec.Body.String())
}
```

- [ ] **Step 2: Run the focused service/API/router tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl ./app/netpath/api ./app/netpath/router -run 'TestNetPathServiceCompareSnapshots|TestNetPathServiceCompareSnapshotsHonorsTenantIsolation|TestNetPathAPIHandlers|TestNetPathRegistersAnalysisRoutes' -count=1
```

Expected: FAIL because `CompareSnapshots` handler/service/route do not exist yet.

- [ ] **Step 3: Implement snapshot compare service and HTTP surface**

Update `OneOps/app/netpath/service/impl/netpath.go`:

```go
func (s *NetPathService) CompareSnapshots(ctx context.Context, req dto.SnapshotCompareReq) (*dto.SnapshotCompareResp, error) {
	req.TenantCode = strings.TrimSpace(req.TenantCode)
	req.BaselineSnapshotID = strings.TrimSpace(req.BaselineSnapshotID)
	req.TargetSnapshotID = strings.TrimSpace(req.TargetSnapshotID)
	if req.TenantCode == "" {
		return nil, fmt.Errorf("tenant_code is required")
	}
	if req.BaselineSnapshotID == "" {
		return nil, fmt.Errorf("baseline_snapshot_id is required")
	}
	if req.TargetSnapshotID == "" {
		return nil, fmt.Errorf("target_snapshot_id is required")
	}

	baseline, err := s.GetSnapshot(ctx, req.TenantCode, req.BaselineSnapshotID, false)
	if err != nil {
		return nil, err
	}
	target, err := s.GetSnapshot(ctx, req.TenantCode, req.TargetSnapshotID, false)
	if err != nil {
		return nil, err
	}

	addedDeviceCodes, removedDeviceCodes := diffStringSets(baseline.DeviceCodes, target.DeviceCodes)
	addedDiagnostics, removedDiagnostics := diffAnalyzeDiagnostics(baseline.Diagnostics, target.Diagnostics)
	addedSourceRunIDs, removedSourceRunIDs := diffStringSets(baseline.SourceRunIDs, target.SourceRunIDs)

	resp := &dto.SnapshotCompareResp{
		TenantCode:           req.TenantCode,
		BaselineSnapshotID:   baseline.Code,
		TargetSnapshotID:     target.Code,
		BaselineQuality:      baseline.Quality,
		TargetQuality:        target.Quality,
		QualityChanged:       baseline.Quality != target.Quality,
		BaselineSummary:      baseline.Summary,
		TargetSummary:        target.Summary,
		BaselineDeviceCodes:  append([]string(nil), baseline.DeviceCodes...),
		TargetDeviceCodes:    append([]string(nil), target.DeviceCodes...),
		AddedDeviceCodes:     addedDeviceCodes,
		RemovedDeviceCodes:   removedDeviceCodes,
		BaselineDiagnostics:  append([]dto.AnalyzeDiagnostic(nil), baseline.Diagnostics...),
		TargetDiagnostics:    append([]dto.AnalyzeDiagnostic(nil), target.Diagnostics...),
		AddedDiagnostics:     addedDiagnostics,
		RemovedDiagnostics:   removedDiagnostics,
		BaselineSourceRunIDs: append([]string(nil), baseline.SourceRunIDs...),
		TargetSourceRunIDs:   append([]string(nil), target.SourceRunIDs...),
	}
	resp.Summary = buildSnapshotCompareSummary(resp)
	_ = addedSourceRunIDs
	_ = removedSourceRunIDs
	return resp, nil
}

func diffStringSets(baseline []string, target []string) ([]string, []string) {
	baselineIndex := make(map[string]struct{}, len(baseline))
	targetIndex := make(map[string]struct{}, len(target))
	for _, item := range baseline {
		text := strings.TrimSpace(item)
		if text != "" {
			baselineIndex[text] = struct{}{}
		}
	}
	for _, item := range target {
		text := strings.TrimSpace(item)
		if text != "" {
			targetIndex[text] = struct{}{}
		}
	}
	added := make([]string, 0)
	removed := make([]string, 0)
	for item := range targetIndex {
		if _, ok := baselineIndex[item]; !ok {
			added = append(added, item)
		}
	}
	for item := range baselineIndex {
		if _, ok := targetIndex[item]; !ok {
			removed = append(removed, item)
		}
	}
	sort.Strings(added)
	sort.Strings(removed)
	return added, removed
}

func buildSnapshotCompareSummary(resp *dto.SnapshotCompareResp) string {
	if resp == nil {
		return ""
	}
	parts := []string{
		fmt.Sprintf("baseline=%s", resp.BaselineSnapshotID),
		fmt.Sprintf("target=%s", resp.TargetSnapshotID),
	}
	if resp.QualityChanged {
		parts = append(parts, fmt.Sprintf("quality %s -> %s", resp.BaselineQuality, resp.TargetQuality))
	}
	if len(resp.AddedDeviceCodes) > 0 {
		parts = append(parts, fmt.Sprintf("added devices=%d", len(resp.AddedDeviceCodes)))
	}
	if len(resp.RemovedDeviceCodes) > 0 {
		parts = append(parts, fmt.Sprintf("removed devices=%d", len(resp.RemovedDeviceCodes)))
	}
	return strings.Join(parts, " | ")
}
```

Update `OneOps/app/netpath/api/netpath.go`:

```go
func (a *NetPathAPI) CompareSnapshots(ctx *gin.Context) {
	var req dto.SnapshotCompareReq
	if err := ctx.ShouldBindQuery(&req); err != nil {
		response.FailWithMsg(err.Error(), ctx)
		a.warn("CompareSnapshots bind error", zap.Error(err))
		return
	}

	resp, err := a.NetPathSrv.CompareSnapshots(ctx, req)
	if err != nil {
		response.FailWithMsg(err.Error(), ctx)
		a.warn("CompareSnapshots service error", zap.String("tenant_code", req.TenantCode), zap.String("baseline_snapshot_id", req.BaselineSnapshotID), zap.String("target_snapshot_id", req.TargetSnapshotID), zap.Error(err))
		return
	}

	response.OkWithData(resp, ctx)
}
```

Update `OneOps/app/netpath/router/netpath.go`:

```go
g.GET("snapshots/compare", netPathAPI.CompareSnapshots)
```

- [ ] **Step 4: Re-run the focused service/API/router tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl ./app/netpath/api ./app/netpath/router -run 'TestNetPathServiceCompareSnapshots|TestNetPathServiceCompareSnapshotsHonorsTenantIsolation|TestNetPathAPIHandlers|TestNetPathRegistersAnalysisRoutes' -count=1
```

Expected: PASS.

- [ ] **Step 5: Run the full NetPath verification suite**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/... -count=1
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/netpath/service/impl/netpath.go app/netpath/service/impl/netpath_test.go app/netpath/api/netpath.go app/netpath/api/netpath_test.go app/netpath/router/netpath.go app/netpath/router/netpath_test.go
git commit -m "feat: add netpath durable snapshot compare"
```
