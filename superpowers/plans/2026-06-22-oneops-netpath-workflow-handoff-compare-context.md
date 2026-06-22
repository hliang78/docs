# OneOPS NetPath Workflow Handoff Compare Context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend NetPath workflow handoff with optional baseline compare context while preserving the current run as the source of truth for readiness and core blockers.

**Architecture:** Add a small `compare_context` structure to the workflow handoff DTO, extend the workflow handoff service/API path with an optional `baseline_run_code`, and map existing run-compare results into a lightweight delta model that can tune recommendation priority without rewriting the current handoff gate logic.

**Tech Stack:** Go, GORM, sqlite-backed Go tests, existing OneOPS NetPath DTO/API/router/service packages.

---

## File Structure

### Existing files to modify

- `OneOps/app/netpath/dto/netpath.go`
  - Add workflow handoff compare-context DTOs.
- `OneOps/app/netpath/service/i_netpath.go`
  - Extend the workflow handoff service method signature with optional baseline compare input.
- `OneOps/app/netpath/api/netpath.go`
  - Bind `baseline_run_code` from the workflow handoff query string.
- `OneOps/app/netpath/api/netpath_test.go`
  - Add workflow handoff API coverage for compare-context behavior.
- `OneOps/app/netpath/service/impl/netpath.go`
  - Load optional baseline compare results, map them to `compare_context`, and lightly tune integration ordering/mode.
- `OneOps/app/netpath/service/impl/netpath_test.go`
  - Add service-level compare-context, degradation, and recommendation-priority tests.

## Task 1: Add Workflow Handoff Compare DTO Surface

**Files:**
- Modify: `OneOps/app/netpath/dto/netpath.go`
- Modify: `OneOps/app/netpath/api/netpath_test.go`

- [ ] **Step 1: Write the failing DTO shape test**

Add a compile-focused test near `TestNetPathAPICompareSnapshotsPayloadShape` in `OneOps/app/netpath/api/netpath_test.go`:

```go
func TestNetPathAPIWorkflowHandoffCompareContextPayloadShape(t *testing.T) {
	_ = dto.AnalyzeWorkflowHandoffReq{
		TenantCode:      "tenant-a",
		BaselineRunCode: "run-baseline",
	}

	_ = dto.AnalyzeWorkflowCompareContext{
		BaselineRunCode:     "run-baseline",
		BaselineSnapshotID:  "snapshot-base",
		TargetRunCode:       "run-target",
		TargetSnapshotID:    "snapshot-followup",
		DeltaStatus:         "risk_changed",
		DeltaSummary:        "blocker delta +1/-0",
		DispositionChanged:  true,
		AddedBlockers:       []dto.AnalyzeDiagnostic{{Code: "acl_block"}},
		RemovedBlockers:     []dto.AnalyzeDiagnostic{{Code: "legacy_block"}},
		AddedHops:           []dto.AnalyzeCompareHop{{Sequence: 2, DeviceCode: "fw-1"}},
		RemovedHops:         []dto.AnalyzeCompareHop{{Sequence: 2, DeviceCode: "fw-a"}},
	}

	_ = dto.AnalyzeWorkflowHandoffResp{
		AnalyzeRunCode: "run-target",
		TenantCode:     "tenant-a",
		CompareContext: &dto.AnalyzeWorkflowCompareContext{
			DeltaStatus: "review_recommended",
		},
	}
}
```

- [ ] **Step 2: Run the focused API test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/api -run TestNetPathAPIWorkflowHandoffCompareContextPayloadShape -count=1
```

Expected: FAIL with `undefined: dto.AnalyzeWorkflowHandoffReq`, `undefined: dto.AnalyzeWorkflowCompareContext`, and `unknown field CompareContext`.

- [ ] **Step 3: Add the workflow handoff DTOs**

Update `OneOps/app/netpath/dto/netpath.go`:

```go
type AnalyzeWorkflowHandoffReq struct {
	TenantCode      string `json:"tenant_code" form:"tenant_code"`
	BaselineRunCode string `json:"baseline_run_code,omitempty" form:"baseline_run_code"`
}

type AnalyzeWorkflowCompareContext struct {
	BaselineRunCode    string              `json:"baseline_run_code,omitempty"`
	BaselineSnapshotID string              `json:"baseline_snapshot_id,omitempty"`
	TargetRunCode      string              `json:"target_run_code,omitempty"`
	TargetSnapshotID   string              `json:"target_snapshot_id,omitempty"`
	DeltaStatus        string              `json:"delta_status,omitempty"`
	DeltaSummary       string              `json:"delta_summary,omitempty"`
	DispositionChanged bool                `json:"disposition_changed,omitempty"`
	AddedBlockers      []AnalyzeDiagnostic `json:"added_blockers,omitempty"`
	RemovedBlockers    []AnalyzeDiagnostic `json:"removed_blockers,omitempty"`
	AddedHops          []AnalyzeCompareHop `json:"added_hops,omitempty"`
	RemovedHops        []AnalyzeCompareHop `json:"removed_hops,omitempty"`
}

type AnalyzeWorkflowHandoffResp struct {
	AnalyzeRunCode          string                         `json:"analyze_run_code"`
	TenantCode              string                         `json:"tenant_code"`
	SnapshotID              string                         `json:"snapshot_id"`
	AnalyzeRunStatus        string                         `json:"analyze_run_status"`
	AnalyzeRunDisposition   string                         `json:"analyze_run_disposition,omitempty"`
	ProbePlanCode           string                         `json:"probe_plan_code,omitempty"`
	ProbePlanStatus         string                         `json:"probe_plan_status,omitempty"`
	Ready                   bool                           `json:"ready"`
	Status                  string                         `json:"status"`
	Summary                 string                         `json:"summary"`
	Flow                    AnalyzeFlow                    `json:"flow"`
	Devices                 []AnalyzeWorkflowDevice        `json:"devices,omitempty"`
	Blockers                []AnalyzeDiagnostic            `json:"blockers,omitempty"`
	CompareContext          *AnalyzeWorkflowCompareContext `json:"compare_context,omitempty"`
	RecommendedIntegrations []AnalyzeWorkflowIntegrationHint `json:"recommended_integrations,omitempty"`
}
```

- [ ] **Step 4: Re-run the focused API test**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/api -run TestNetPathAPIWorkflowHandoffCompareContextPayloadShape -count=1
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/netpath/dto/netpath.go app/netpath/api/netpath_test.go
git commit -m "feat: add workflow handoff compare dto surface"
```

## Task 2: Extend Workflow Handoff Service For Optional Baseline Compare

**Files:**
- Modify: `OneOps/app/netpath/service/i_netpath.go`
- Modify: `OneOps/app/netpath/service/impl/netpath.go`
- Modify: `OneOps/app/netpath/service/impl/netpath_test.go`

- [ ] **Step 1: Write the failing service tests**

Add the following tests near the existing workflow handoff tests in `OneOps/app/netpath/service/impl/netpath_test.go`:

```go
func TestNetPathServiceGetAnalyzeRunWorkflowHandoffWithoutBaselineLeavesCompareContextEmpty(t *testing.T) {
	svc := newDurableAnalyzeRunTestService(t)
	run, err := svc.CreateAnalyzeRun(context.Background(), dto.AnalyzeRunCreateReq{
		TenantCode:        "tenant-a",
		SrcIP:             "10.0.1.10",
		DstIP:             "10.0.2.20",
		IngressDeviceCode: "leaf-1",
	})
	if err != nil {
		t.Fatalf("CreateAnalyzeRun returned error: %v", err)
	}

	handoff, err := svc.GetAnalyzeRunWorkflowHandoff(context.Background(), "tenant-a", run.Code, "")
	if err != nil {
		t.Fatalf("GetAnalyzeRunWorkflowHandoff returned error: %v", err)
	}
	if handoff.CompareContext != nil {
		t.Fatalf("expected nil compare context without baseline, got %#v", handoff.CompareContext)
	}
}

func TestNetPathServiceGetAnalyzeRunWorkflowHandoffWithBaselineCompareContext(t *testing.T) {
	db := newNetPathTestDB(t)
	seedDurableSnapshotForTest(t, db, "tenant-a", "snapshot-base", "leaf-1")
	seedDurableSnapshotForTest(t, db, "tenant-a", "snapshot-followup", "leaf-1")
	engine := &fakeAnalysisEngine{
		result: &netpathengine.AnalyzeResult{
			SnapshotID:  "snapshot-base",
			Disposition: "blocked_acl",
			Flow: netpathengine.Flow{SrcIP: "10.0.1.10", DstIP: "10.0.2.20", IngressDeviceCode: "leaf-1"},
			Traces: []netpathengine.Trace{{TraceID: "trace-1", Disposition: "blocked_acl", Hops: []netpathengine.Hop{{Sequence: 1, DeviceCode: "leaf-1"}, {Sequence: 2, DeviceCode: "fw-a"}}}},
			Diagnostics: []netpathengine.Diagnostic{{Severity: "warn", Code: "acl_block", Message: "security policy blocked the flow"}},
		},
	}
	svc := NewNetPathService(db, WithAnalysisEngine(engine))

	baseline, err := svc.CreateAnalyzeRun(context.Background(), dto.AnalyzeRunCreateReq{
		TenantCode:        "tenant-a",
		SnapshotID:        "snapshot-base",
		SrcIP:             "10.0.1.10",
		DstIP:             "10.0.2.20",
		IngressDeviceCode: "leaf-1",
	})
	if err != nil {
		t.Fatalf("CreateAnalyzeRun baseline failed: %v", err)
	}

	engine.result = &netpathengine.AnalyzeResult{
		SnapshotID:  "snapshot-followup",
		Disposition: "delivered_to_subnet",
		Flow: netpathengine.Flow{SrcIP: "10.0.1.10", DstIP: "10.0.2.20", IngressDeviceCode: "leaf-1"},
		Traces: []netpathengine.Trace{{TraceID: "trace-1", Disposition: "delivered_to_subnet", Hops: []netpathengine.Hop{{Sequence: 1, DeviceCode: "leaf-1"}, {Sequence: 2, DeviceCode: "fw-b"}}}},
		Diagnostics: []netpathengine.Diagnostic{{Severity: "warn", Code: "needs_validation", Message: "follow-up validation required"}},
	}
	target, err := svc.CreateAnalyzeRun(context.Background(), dto.AnalyzeRunCreateReq{
		TenantCode:        "tenant-a",
		SnapshotID:        "snapshot-followup",
		SrcIP:             "10.0.1.10",
		DstIP:             "10.0.2.20",
		IngressDeviceCode: "leaf-1",
	})
	if err != nil {
		t.Fatalf("CreateAnalyzeRun target failed: %v", err)
	}
	if _, err = svc.BuildAnalyzeRunProbePlan(context.Background(), target.Code, dto.AnalyzeProbePlanBuildReq{TenantCode: "tenant-a"}); err != nil {
		t.Fatalf("BuildAnalyzeRunProbePlan returned error: %v", err)
	}

	handoff, err := svc.GetAnalyzeRunWorkflowHandoff(context.Background(), "tenant-a", target.Code, baseline.Code)
	if err != nil {
		t.Fatalf("GetAnalyzeRunWorkflowHandoff returned error: %v", err)
	}
	if handoff.CompareContext == nil {
		t.Fatalf("expected compare context, got %#v", handoff)
	}
	if handoff.CompareContext.DeltaStatus != "risk_changed" {
		t.Fatalf("expected risk_changed delta status, got %#v", handoff.CompareContext)
	}
	if !handoff.CompareContext.DispositionChanged || len(handoff.CompareContext.AddedBlockers) != 1 {
		t.Fatalf("expected blocker/disposition delta, got %#v", handoff.CompareContext)
	}
	if len(handoff.RecommendedIntegrations) == 0 || handoff.RecommendedIntegrations[0].Kind != "manual_review" {
		t.Fatalf("expected manual_review to be prioritized, got %#v", handoff.RecommendedIntegrations)
	}
}

func TestNetPathServiceGetAnalyzeRunWorkflowHandoffBaselineCompareUnavailableDegradesGracefully(t *testing.T) {
	db := newNetPathTestDB(t)
	seedDurableSnapshotForTest(t, db, "tenant-a", "snapshot-target", "leaf-1")
	engine := &fakeAnalysisEngine{
		result: &netpathengine.AnalyzeResult{
			SnapshotID:  "snapshot-target",
			Disposition: "delivered_to_subnet",
			Flow: netpathengine.Flow{SrcIP: "10.0.1.10", DstIP: "10.0.2.20", IngressDeviceCode: "leaf-1"},
			Traces: []netpathengine.Trace{{TraceID: "trace-1", Disposition: "delivered_to_subnet", Hops: []netpathengine.Hop{{Sequence: 1, DeviceCode: "leaf-1"}}}},
		},
	}
	svc := NewNetPathService(db, WithAnalysisEngine(engine))
	target, err := svc.CreateAnalyzeRun(context.Background(), dto.AnalyzeRunCreateReq{
		TenantCode:        "tenant-a",
		SnapshotID:        "snapshot-target",
		SrcIP:             "10.0.1.10",
		DstIP:             "10.0.2.20",
		IngressDeviceCode: "leaf-1",
	})
	if err != nil {
		t.Fatalf("CreateAnalyzeRun target failed: %v", err)
	}
	if _, err = svc.BuildAnalyzeRunProbePlan(context.Background(), target.Code, dto.AnalyzeProbePlanBuildReq{TenantCode: "tenant-a"}); err != nil {
		t.Fatalf("BuildAnalyzeRunProbePlan returned error: %v", err)
	}

	handoff, err := svc.GetAnalyzeRunWorkflowHandoff(context.Background(), "tenant-a", target.Code, "missing-baseline")
	if err != nil {
		t.Fatalf("GetAnalyzeRunWorkflowHandoff returned error: %v", err)
	}
	if handoff.CompareContext == nil || handoff.CompareContext.DeltaStatus != "review_recommended" {
		t.Fatalf("expected degraded compare context, got %#v", handoff.CompareContext)
	}
	if handoff.Ready != true {
		t.Fatalf("expected current run readiness to remain true, got %#v", handoff)
	}
}
```

- [ ] **Step 2: Run the focused service tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl -run 'TestNetPathServiceGetAnalyzeRunWorkflowHandoff(WithoutBaselineLeavesCompareContextEmpty|WithBaselineCompareContext|BaselineCompareUnavailableDegradesGracefully)' -count=1
```

Expected: FAIL because `GetAnalyzeRunWorkflowHandoff` does not yet accept a baseline run code or emit compare context.

- [ ] **Step 3: Extend the service interface**

Update `OneOps/app/netpath/service/i_netpath.go`:

```go
type INetPathService interface {
	// ...
	GetAnalyzeRunWorkflowHandoff(ctx context.Context, tenantCode string, code string, baselineRunCode string) (*dto.AnalyzeWorkflowHandoffResp, error)
	// ...
}
```

- [ ] **Step 4: Extend workflow handoff service behavior**

Update `OneOps/app/netpath/service/impl/netpath.go`:

```go
func (s *NetPathService) GetAnalyzeRunWorkflowHandoff(ctx context.Context, tenantCode string, code string, baselineRunCode string) (*dto.AnalyzeWorkflowHandoffResp, error) {
	tenantCode = strings.TrimSpace(tenantCode)
	code = strings.TrimSpace(code)
	baselineRunCode = strings.TrimSpace(baselineRunCode)
	if tenantCode == "" {
		return nil, fmt.Errorf("tenant_code is required")
	}
	if code == "" {
		return nil, fmt.Errorf("code is required")
	}

	run, err := s.GetAnalyzeRun(ctx, tenantCode, code)
	if err != nil {
		return nil, err
	}
	plan, err := s.lookupAnalyzeRunProbePlan(ctx, tenantCode, code)
	if err != nil {
		return nil, err
	}
	if plan == nil {
		plan = buildAnalyzeProbePlanResp(run)
	}

	handoff := buildAnalyzeWorkflowHandoff(run, plan)
	if baselineRunCode == "" {
		return handoff, nil
	}

	compare, err := s.CompareAnalyzeRuns(ctx, tenantCode, baselineRunCode, code)
	if err != nil {
		handoff.CompareContext = buildUnavailableWorkflowCompareContext(baselineRunCode, run, err)
		handoff.RecommendedIntegrations = buildAnalyzeWorkflowIntegrations(handoff, plan)
		return handoff, nil
	}

	handoff.CompareContext = buildAnalyzeWorkflowCompareContext(compare)
	handoff.RecommendedIntegrations = buildAnalyzeWorkflowIntegrations(handoff, plan)
	return handoff, nil
}
```

Add helpers in the same file:

```go
func buildAnalyzeWorkflowCompareContext(compare *dto.AnalyzeRunCompareResp) *dto.AnalyzeWorkflowCompareContext {
	if compare == nil {
		return nil
	}
	ctx := &dto.AnalyzeWorkflowCompareContext{
		BaselineRunCode:    compare.BaselineRunCode,
		BaselineSnapshotID: compare.BaselineSnapshotID,
		TargetRunCode:      compare.TargetRunCode,
		TargetSnapshotID:   compare.TargetSnapshotID,
		DeltaSummary:       compare.Summary,
		DispositionChanged: compare.DispositionChanged,
		AddedBlockers:      cloneAnalyzeDiagnostics(compare.AddedBlockers),
		RemovedBlockers:    cloneAnalyzeDiagnostics(compare.RemovedBlockers),
		AddedHops:          cloneAnalyzeCompareHops(compare.AddedHops),
		RemovedHops:        cloneAnalyzeCompareHops(compare.RemovedHops),
	}
	switch {
	case compare.DispositionChanged || len(compare.AddedBlockers) > 0:
		ctx.DeltaStatus = "risk_changed"
	case len(compare.AddedHops) > 0 || len(compare.RemovedHops) > 0 || len(compare.RemovedBlockers) > 0:
		ctx.DeltaStatus = "review_recommended"
	case strings.TrimSpace(compare.Summary) != "":
		ctx.DeltaStatus = "context_only"
	default:
		ctx.DeltaStatus = "none"
	}
	return ctx
}

func buildUnavailableWorkflowCompareContext(baselineRunCode string, run *dto.AnalyzeRunResp, err error) *dto.AnalyzeWorkflowCompareContext {
	return &dto.AnalyzeWorkflowCompareContext{
		BaselineRunCode: baselineRunCode,
		TargetRunCode:   safeAnalyzeRunCode(run),
		TargetSnapshotID: func() string {
			if run == nil {
				return ""
			}
			return run.SnapshotID
		}(),
		DeltaStatus:  "review_recommended",
		DeltaSummary: fmt.Sprintf("baseline compare unavailable: %v", err),
	}
}

func safeAnalyzeRunCode(run *dto.AnalyzeRunResp) string {
	if run == nil {
		return ""
	}
	return run.Code
}

func cloneAnalyzeCompareHops(in []dto.AnalyzeCompareHop) []dto.AnalyzeCompareHop {
	if len(in) == 0 {
		return nil
	}
	out := make([]dto.AnalyzeCompareHop, len(in))
	copy(out, in)
	return out
}
```

Update `buildAnalyzeWorkflowIntegrations` in the same file so compare context lightly adjusts recommendation priority:

```go
func buildAnalyzeWorkflowIntegrations(handoff *dto.AnalyzeWorkflowHandoffResp, plan *dto.AnalyzeProbePlanResp) []dto.AnalyzeWorkflowIntegrationHint {
	// existing hint building stays in place
	hints := existingWorkflowHints(handoff, plan)
	if handoff == nil || handoff.CompareContext == nil {
		return hints
	}

	switch strings.TrimSpace(handoff.CompareContext.DeltaStatus) {
	case "review_recommended":
		hints = prioritizeManualReviewHint(hints, false)
	case "risk_changed":
		hints = prioritizeManualReviewHint(hints, true)
	}
	return hints
}
```

Refactor the current body into a small helper so the behavior stays clear:

```go
func existingWorkflowHints(handoff *dto.AnalyzeWorkflowHandoffResp, plan *dto.AnalyzeProbePlanResp) []dto.AnalyzeWorkflowIntegrationHint {
	// move the current body of buildAnalyzeWorkflowIntegrations here unchanged
}

func prioritizeManualReviewHint(hints []dto.AnalyzeWorkflowIntegrationHint, conditionalAutomation bool) []dto.AnalyzeWorkflowIntegrationHint {
	if len(hints) == 0 {
		return hints
	}
	reordered := make([]dto.AnalyzeWorkflowIntegrationHint, 0, len(hints))
	manual := make([]dto.AnalyzeWorkflowIntegrationHint, 0, 1)
	others := make([]dto.AnalyzeWorkflowIntegrationHint, 0, len(hints))
	for _, hint := range hints {
		item := hint
		if conditionalAutomation && item.Kind != "manual_review" && item.Mode == "recommended" {
			item.Mode = "conditional"
		}
		if item.Kind == "manual_review" {
			manual = append(manual, item)
			continue
		}
		others = append(others, item)
	}
	reordered = append(reordered, manual...)
	reordered = append(reordered, others...)
	return reordered
}
```

- [ ] **Step 5: Re-run the focused service tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl -run 'TestNetPathServiceGetAnalyzeRunWorkflowHandoff(WithoutBaselineLeavesCompareContextEmpty|WithBaselineCompareContext|BaselineCompareUnavailableDegradesGracefully|ForReadyRun)' -count=1
```

Expected: PASS.

- [ ] **Step 6: Run the broader workflow service tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl -run 'TestNetPathServiceGetAnalyzeRunWorkflowHandoff|TestNetPathServiceGetAnalyzeRunMonitorProbeDraft|TestNetPathServiceGetAnalyzeRunTicketDraft' -count=1
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/netpath/service/i_netpath.go app/netpath/service/impl/netpath.go app/netpath/service/impl/netpath_test.go
git commit -m "feat: add workflow handoff compare context"
```

## Task 3: Bind Baseline Query In The API And Verify End-To-End Payloads

**Files:**
- Modify: `OneOps/app/netpath/api/netpath.go`
- Modify: `OneOps/app/netpath/api/netpath_test.go`

- [ ] **Step 1: Write the failing API test**

Add a new API-level test in `OneOps/app/netpath/api/netpath_test.go` near the existing workflow handoff tests:

```go
func TestNetPathAPIWorkflowHandoffWithBaselineCompareContext(t *testing.T) {
	gin.SetMode(gin.TestMode)

	seedSvc, db, builder := newNetPathAPIAnalyzeRunService(t)
	builder.snapshot = provider.AnalysisSnapshot{
		SnapshotID: "snapshot-base",
		TenantCode: "tenant-a",
		Quality:    provider.SnapshotQualityReady,
		Devices:    []provider.AnalysisDevice{{DeviceCode: "leaf-1"}},
	}
	builder.summary = "baseline snapshot"
	baselineSnapshot, err := seedSvc.CreateSnapshot(context.Background(), dto.SnapshotCreateReq{
		TenantCode:        "tenant-a",
		DeviceCodes:       []string{"leaf-1"},
		IngressDeviceCode: "leaf-1",
	})
	if err != nil {
		t.Fatalf("CreateSnapshot baseline failed: %v", err)
	}

	engine := &apiFakeAnalysisEngine{
		result: &netpathengine.AnalyzeResult{
			SnapshotID:  baselineSnapshot.Code,
			Disposition: "blocked_acl",
			Flow:        netpathengine.Flow{SrcIP: "10.0.1.10", DstIP: "10.0.2.20", IngressDeviceCode: "leaf-1"},
			Traces: []netpathengine.Trace{{TraceID: "trace-1", Disposition: "blocked_acl", Hops: []netpathengine.Hop{{Sequence: 1, DeviceCode: "leaf-1"}, {Sequence: 2, DeviceCode: "fw-a"}}}},
			Diagnostics: []netpathengine.Diagnostic{{Severity: "warn", Code: "acl_block", Message: "security policy blocked the flow"}},
		},
	}
	svc := impl.NewNetPathService(db, impl.WithAnalysisSnapshotBuilder(builder), impl.WithAnalysisEngine(engine))
	baselineRun, err := svc.CreateAnalyzeRun(context.Background(), dto.AnalyzeRunCreateReq{
		TenantCode:        "tenant-a",
		SnapshotID:        baselineSnapshot.Code,
		SrcIP:             "10.0.1.10",
		DstIP:             "10.0.2.20",
		IngressDeviceCode: "leaf-1",
	})
	if err != nil {
		t.Fatalf("CreateAnalyzeRun baseline failed: %v", err)
	}

	builder.snapshot = provider.AnalysisSnapshot{
		SnapshotID: "snapshot-followup",
		TenantCode: "tenant-a",
		Quality:    provider.SnapshotQualityReady,
		Devices:    []provider.AnalysisDevice{{DeviceCode: "leaf-1"}},
	}
	builder.summary = "followup snapshot"
	followupSnapshot, err := svc.CreateSnapshot(context.Background(), dto.SnapshotCreateReq{
		TenantCode:        "tenant-a",
		DeviceCodes:       []string{"leaf-1"},
		IngressDeviceCode: "leaf-1",
	})
	if err != nil {
		t.Fatalf("CreateSnapshot followup failed: %v", err)
	}

	engine.result = &netpathengine.AnalyzeResult{
		SnapshotID:  followupSnapshot.Code,
		Disposition: "delivered_to_subnet",
		Flow:        netpathengine.Flow{SrcIP: "10.0.1.10", DstIP: "10.0.2.20", IngressDeviceCode: "leaf-1"},
		Traces: []netpathengine.Trace{{TraceID: "trace-1", Disposition: "delivered_to_subnet", Hops: []netpathengine.Hop{{Sequence: 1, DeviceCode: "leaf-1"}, {Sequence: 2, DeviceCode: "fw-b"}}}},
		Diagnostics: []netpathengine.Diagnostic{{Severity: "warn", Code: "needs_validation", Message: "follow-up validation required"}},
	}
	targetRun, err := svc.CreateAnalyzeRun(context.Background(), dto.AnalyzeRunCreateReq{
		TenantCode:        "tenant-a",
		SnapshotID:        followupSnapshot.Code,
		SrcIP:             "10.0.1.10",
		DstIP:             "10.0.2.20",
		IngressDeviceCode: "leaf-1",
	})
	if err != nil {
		t.Fatalf("CreateAnalyzeRun target failed: %v", err)
	}
	if _, err = svc.BuildAnalyzeRunProbePlan(context.Background(), targetRun.Code, dto.AnalyzeProbePlanBuildReq{TenantCode: "tenant-a"}); err != nil {
		t.Fatalf("BuildAnalyzeRunProbePlan returned error: %v", err)
	}

	api := &NetPathAPI{Logger: zap.NewNop(), NetPathSrv: svc}
	router := gin.New()
	router.GET("/netpath/analysis-runs/:code/workflow-handoff", api.GetAnalyzeRunWorkflowHandoff)

	rec := performNetPathAPIRequest(t, router, http.MethodGet, "/netpath/analysis-runs/"+targetRun.Code+"/workflow-handoff?tenant_code=tenant-a&baseline_run_code="+baselineRun.Code, nil)
	if rec.Code != http.StatusOK {
		t.Fatalf("expected status 200, got %d body=%s", rec.Code, rec.Body.String())
	}

	var handoff dto.AnalyzeWorkflowHandoffResp
	if err := json.Unmarshal(decodeNetPathAPIEnvelope(t, rec).Data, &handoff); err != nil {
		t.Fatalf("unmarshal workflow handoff response failed: %v body=%s", err, rec.Body.String())
	}
	if handoff.CompareContext == nil || handoff.CompareContext.DeltaStatus != "risk_changed" {
		t.Fatalf("expected compare context risk_changed, got %#v", handoff.CompareContext)
	}
	if len(handoff.RecommendedIntegrations) == 0 || handoff.RecommendedIntegrations[0].Kind != "manual_review" {
		t.Fatalf("expected manual review to be prioritized, got %#v", handoff.RecommendedIntegrations)
	}
}
```

- [ ] **Step 2: Run the focused API test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/api -run TestNetPathAPIWorkflowHandoffWithBaselineCompareContext -count=1
```

Expected: FAIL because the API handler does not yet bind or pass `baseline_run_code`.

- [ ] **Step 3: Bind the baseline query parameter in the API**

Update `OneOps/app/netpath/api/netpath.go`:

```go
func (a *NetPathAPI) GetAnalyzeRunWorkflowHandoff(ctx *gin.Context) {
	code := strings.TrimSpace(ctx.Param("code"))
	var req dto.AnalyzeWorkflowHandoffReq
	if err := ctx.ShouldBindQuery(&req); err != nil {
		response.FailWithMsg(err.Error(), ctx)
		a.warn("GetAnalyzeRunWorkflowHandoff bind query error", zap.Error(err))
		return
	}

	resp, err := a.NetPathSrv.GetAnalyzeRunWorkflowHandoff(ctx, strings.TrimSpace(req.TenantCode), code, strings.TrimSpace(req.BaselineRunCode))
	if err != nil {
		response.FailWithMsg(err.Error(), ctx)
		a.warn("GetAnalyzeRunWorkflowHandoff service error",
			zap.String("tenant_code", req.TenantCode),
			zap.String("code", code),
			zap.String("baseline_run_code", req.BaselineRunCode),
			zap.Error(err),
		)
		return
	}

	response.OkWithData(resp, ctx)
}
```

- [ ] **Step 4: Re-run the focused API test**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/api -run TestNetPathAPIWorkflowHandoffWithBaselineCompareContext -count=1
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
git add app/netpath/api/netpath.go app/netpath/api/netpath_test.go
git commit -m "feat: add workflow handoff baseline compare context"
```
