# OneOPS NetPath Monitor Probe Draft Compare Context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend NetPath monitor probe draft with optional baseline compare context while preserving current probe item mapping and keeping maintenance payload generation backward-compatible.

**Architecture:** Reuse workflow handoff as the single producer of durable run-compare context, then let monitor-probe-draft consume that context through an optional `baseline_run_code`. Add a small compare-aware layer to the existing draft builder so the response exposes structured `compare_context` and human-readable compare guidance through `summary` and item `notes`, without changing the downstream `maintenance/monitor_probe` payload contract.

**Tech Stack:** Go, GORM, sqlite-backed Go tests, existing OneOPS NetPath DTO/API/router/service packages.

---

## File Structure

### Existing files to modify

- `OneOps/app/netpath/dto/netpath.go`
  - Add monitor-probe draft request DTO and response compare-context field.
- `OneOps/app/netpath/service/i_netpath.go`
  - Extend the monitor-probe-draft service signature with optional baseline compare input.
- `OneOps/app/netpath/service/impl/netpath.go`
  - Thread baseline compare through workflow handoff, attach compare context to the probe draft, and tune summary and notes by compare delta.
- `OneOps/app/netpath/service/impl/netpath_test.go`
  - Add service coverage for compare-context attach, graceful degradation, and compare-aware notes.
- `OneOps/app/netpath/api/netpath.go`
  - Bind `baseline_run_code` from the monitor-probe-draft query string.
- `OneOps/app/netpath/api/netpath_test.go`
  - Add API payload-shape and end-to-end compare-context coverage.
- `OneOps/app/netpath/adapter/oneopsnetpath/monitor_probe_draft_test.go`
  - Add regression coverage showing compare-only fields do not affect maintenance payload generation.

## Task 1: Add Monitor Probe Draft Compare DTO Surface

**Files:**
- Modify: `OneOps/app/netpath/dto/netpath.go`
- Modify: `OneOps/app/netpath/api/netpath_test.go`

- [ ] **Step 1: Write the failing DTO shape test**

Add a compile-focused test near the other DTO surface tests in `OneOps/app/netpath/api/netpath_test.go`:

```go
func TestNetPathAPIMonitorProbeDraftCompareContextPayloadShape(t *testing.T) {
	_ = dto.AnalyzeMonitorProbeDraftReq{
		TenantCode:      "tenant-a",
		BaselineRunCode: "run-baseline",
	}

	_ = dto.AnalyzeMonitorProbeDraftResp{
		AnalyzeRunCode: "run-target",
		TenantCode:     "tenant-a",
		CompareContext: &dto.AnalyzeWorkflowCompareContext{
			BaselineRunCode:    "run-baseline",
			BaselineSnapshotID: "snapshot-base",
			TargetRunCode:      "run-target",
			TargetSnapshotID:   "snapshot-followup",
			DeltaStatus:        "review_recommended",
			DeltaSummary:       "hop delta detected",
		},
	}
}
```

- [ ] **Step 2: Run the focused API test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/api -run TestNetPathAPIMonitorProbeDraftCompareContextPayloadShape -count=1
```

Expected: FAIL with `undefined: dto.AnalyzeMonitorProbeDraftReq` and `unknown field CompareContext`.

- [ ] **Step 3: Add the monitor-probe draft DTO surface**

Update `OneOps/app/netpath/dto/netpath.go`:

```go
type AnalyzeMonitorProbeDraftReq struct {
	TenantCode      string `json:"tenant_code" form:"tenant_code"`
	BaselineRunCode string `json:"baseline_run_code,omitempty" form:"baseline_run_code"`
}

type AnalyzeMonitorProbeDraftResp struct {
	AnalyzeRunCode        string                         `json:"analyze_run_code"`
	TenantCode            string                         `json:"tenant_code"`
	SnapshotID            string                         `json:"snapshot_id"`
	ProbePlanCode         string                         `json:"probe_plan_code,omitempty"`
	Status                string                         `json:"status"`
	Summary               string                         `json:"summary"`
	ProbeType             string                         `json:"probe_type"`
	RequiredPlaceholders  []string                       `json:"required_placeholders,omitempty"`
	SupportedItems        []AnalyzeMonitorProbeDraftItem `json:"supported_items,omitempty"`
	UnsupportedDirections []string                       `json:"unsupported_directions,omitempty"`
	CompareContext        *AnalyzeWorkflowCompareContext `json:"compare_context,omitempty"`
	PushInfo              *AnalyzeMonitorProbePushInfo   `json:"push_info,omitempty"`
}
```

- [ ] **Step 4: Re-run the focused API test**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/api -run TestNetPathAPIMonitorProbeDraftCompareContextPayloadShape -count=1
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/netpath/dto/netpath.go app/netpath/api/netpath_test.go
git commit -m "feat: add monitor probe draft compare dto surface"
```

## Task 2: Thread Baseline Compare Through API And Service

**Files:**
- Modify: `OneOps/app/netpath/service/i_netpath.go`
- Modify: `OneOps/app/netpath/api/netpath.go`
- Modify: `OneOps/app/netpath/service/impl/netpath.go`
- Modify: `OneOps/app/netpath/service/impl/netpath_test.go`
- Modify: `OneOps/app/netpath/api/netpath_test.go`

- [ ] **Step 1: Write the failing service tests**

Add the following tests near `TestNetPathServiceGetAnalyzeRunMonitorProbeDraft` in `OneOps/app/netpath/service/impl/netpath_test.go`:

```go
func TestNetPathServiceGetAnalyzeRunMonitorProbeDraftWithoutBaselineLeavesCompareContextEmpty(t *testing.T) {
	db := newNetPathTestDB(t)
	seedDurableSnapshotForTest(t, db, "tenant-a", "analysis-monitor-probe-plain", "leaf-1")
	engine := &fakeAnalysisEngine{
		result: &netpathengine.AnalyzeResult{
			SnapshotID:  "analysis-monitor-probe-plain",
			Disposition: "delivered_to_subnet",
			Flow: netpathengine.Flow{
				SrcIP:             "10.0.1.10",
				DstIP:             "10.0.2.20",
				IngressDeviceCode: "leaf-1",
			},
			Traces: []netpathengine.Trace{{
				TraceID:     "trace-1",
				Disposition: "delivered_to_subnet",
				Hops: []netpathengine.Hop{{Sequence: 1, DeviceCode: "leaf-1"}},
			}},
		},
	}
	svc := NewNetPathService(db, WithAnalysisEngine(engine))
	run, err := svc.CreateAnalyzeRun(context.Background(), dto.AnalyzeRunCreateReq{
		TenantCode:        "tenant-a",
		SnapshotID:        "analysis-monitor-probe-plain",
		SrcIP:             "10.0.1.10",
		DstIP:             "10.0.2.20",
		IngressDeviceCode: "leaf-1",
	})
	if err != nil {
		t.Fatalf("CreateAnalyzeRun returned error: %v", err)
	}
	if _, err = svc.BuildAnalyzeRunProbePlan(context.Background(), run.Code, dto.AnalyzeProbePlanBuildReq{TenantCode: "tenant-a"}); err != nil {
		t.Fatalf("BuildAnalyzeRunProbePlan returned error: %v", err)
	}

	draft, err := svc.GetAnalyzeRunMonitorProbeDraft(context.Background(), "tenant-a", run.Code, "")
	if err != nil {
		t.Fatalf("GetAnalyzeRunMonitorProbeDraft returned error: %v", err)
	}
	if draft.CompareContext != nil {
		t.Fatalf("expected nil compare context without baseline, got %#v", draft.CompareContext)
	}
}

func TestNetPathServiceGetAnalyzeRunMonitorProbeDraftWithBaselineCompareContext(t *testing.T) {
	db := newNetPathTestDB(t)
	seedDurableSnapshotForTest(t, db, "tenant-a", "snapshot-probe-base", "leaf-1")
	seedDurableSnapshotForTest(t, db, "tenant-a", "snapshot-probe-target", "leaf-1")
	engine := &fakeAnalysisEngine{
		result: &netpathengine.AnalyzeResult{
			SnapshotID:  "snapshot-probe-base",
			Disposition: "blocked_acl",
			Flow: netpathengine.Flow{
				SrcIP:             "10.0.1.10",
				DstIP:             "10.0.2.20",
				IngressDeviceCode: "leaf-1",
			},
			Traces: []netpathengine.Trace{{
				TraceID:     "trace-1",
				Disposition: "blocked_acl",
				Hops: []netpathengine.Hop{{Sequence: 1, DeviceCode: "leaf-1"}, {Sequence: 2, DeviceCode: "fw-a"}},
			}},
			Diagnostics: []netpathengine.Diagnostic{{
				Severity: "warn",
				Code:     "acl_block",
				Message:  "security policy blocked the flow",
			}},
		},
	}
	svc := NewNetPathService(db, WithAnalysisEngine(engine))

	baseline, err := svc.CreateAnalyzeRun(context.Background(), dto.AnalyzeRunCreateReq{
		TenantCode:        "tenant-a",
		SnapshotID:        "snapshot-probe-base",
		SrcIP:             "10.0.1.10",
		DstIP:             "10.0.2.20",
		IngressDeviceCode: "leaf-1",
	})
	if err != nil {
		t.Fatalf("CreateAnalyzeRun baseline failed: %v", err)
	}

	engine.result = &netpathengine.AnalyzeResult{
		SnapshotID:  "snapshot-probe-target",
		Disposition: "delivered_to_subnet",
		Flow: netpathengine.Flow{
			SrcIP:             "10.0.1.10",
			DstIP:             "10.0.2.20",
			IngressDeviceCode: "leaf-1",
		},
		Traces: []netpathengine.Trace{{
			TraceID:     "trace-1",
			Disposition: "delivered_to_subnet",
			Hops: []netpathengine.Hop{{Sequence: 1, DeviceCode: "leaf-1"}, {Sequence: 2, DeviceCode: "fw-b"}},
		}},
	}
	target, err := svc.CreateAnalyzeRun(context.Background(), dto.AnalyzeRunCreateReq{
		TenantCode:        "tenant-a",
		SnapshotID:        "snapshot-probe-target",
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

	draft, err := svc.GetAnalyzeRunMonitorProbeDraft(context.Background(), "tenant-a", target.Code, baseline.Code)
	if err != nil {
		t.Fatalf("GetAnalyzeRunMonitorProbeDraft returned error: %v", err)
	}
	if draft.CompareContext == nil || draft.CompareContext.DeltaStatus != "risk_changed" {
		t.Fatalf("expected risk_changed compare context, got %#v", draft)
	}
	if !strings.Contains(draft.Summary, "人工复核") {
		t.Fatalf("expected compare-aware review summary, got %q", draft.Summary)
	}
	if len(draft.SupportedItems) == 0 || len(draft.SupportedItems[0].Notes) == 0 {
		t.Fatalf("expected compare-aware notes, got %#v", draft.SupportedItems)
	}
}

func TestNetPathServiceGetAnalyzeRunMonitorProbeDraftBaselineCompareUnavailableDegradesGracefully(t *testing.T) {
	db := newNetPathTestDB(t)
	seedDurableSnapshotForTest(t, db, "tenant-a", "snapshot-probe-degraded", "leaf-1")
	engine := &fakeAnalysisEngine{
		result: &netpathengine.AnalyzeResult{
			SnapshotID:  "snapshot-probe-degraded",
			Disposition: "delivered_to_subnet",
			Flow: netpathengine.Flow{
				SrcIP:             "10.0.1.10",
				DstIP:             "10.0.2.20",
				IngressDeviceCode: "leaf-1",
			},
			Traces: []netpathengine.Trace{{
				TraceID:     "trace-1",
				Disposition: "delivered_to_subnet",
				Hops: []netpathengine.Hop{{Sequence: 1, DeviceCode: "leaf-1"}},
			}},
		},
	}
	svc := NewNetPathService(db, WithAnalysisEngine(engine))
	target, err := svc.CreateAnalyzeRun(context.Background(), dto.AnalyzeRunCreateReq{
		TenantCode:        "tenant-a",
		SnapshotID:        "snapshot-probe-degraded",
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

	draft, err := svc.GetAnalyzeRunMonitorProbeDraft(context.Background(), "tenant-a", target.Code, "missing-baseline")
	if err != nil {
		t.Fatalf("GetAnalyzeRunMonitorProbeDraft returned error: %v", err)
	}
	if draft.CompareContext == nil || draft.CompareContext.DeltaStatus != "review_recommended" {
		t.Fatalf("expected degraded compare context, got %#v", draft)
	}
	if !strings.Contains(draft.CompareContext.DeltaSummary, "baseline compare unavailable") {
		t.Fatalf("expected degraded delta summary, got %#v", draft.CompareContext)
	}
	if !strings.Contains(draft.Summary, "人工复核") {
		t.Fatalf("expected degraded summary to recommend review, got %q", draft.Summary)
	}
}
```

- [ ] **Step 2: Run the focused service tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl -run 'TestNetPathServiceGetAnalyzeRunMonitorProbeDraft(WithoutBaselineLeavesCompareContextEmpty|WithBaselineCompareContext|BaselineCompareUnavailableDegradesGracefully)$' -count=1
```

Expected: FAIL because `GetAnalyzeRunMonitorProbeDraft` does not accept `baselineRunCode`, `AnalyzeMonitorProbeDraftResp` has no `CompareContext`, and compare-aware summary/notes are not implemented.

- [ ] **Step 3: Extend the service signature and API binding**

Update `OneOps/app/netpath/service/i_netpath.go`:

```go
GetAnalyzeRunMonitorProbeDraft(ctx context.Context, tenantCode string, code string, baselineRunCode string) (*dto.AnalyzeMonitorProbeDraftResp, error)
```

Update `OneOps/app/netpath/api/netpath.go`:

```go
func (a *NetPathAPI) GetAnalyzeRunMonitorProbeDraft(ctx *gin.Context) {
	code := strings.TrimSpace(ctx.Param("code"))
	var req dto.AnalyzeMonitorProbeDraftReq
	if err := ctx.ShouldBindQuery(&req); err != nil {
		response.FailWithMsg(err.Error(), ctx)
		a.warn("GetAnalyzeRunMonitorProbeDraft bind query error", zap.Error(err))
		return
	}

	resp, err := a.NetPathSrv.GetAnalyzeRunMonitorProbeDraft(
		ctx,
		strings.TrimSpace(req.TenantCode),
		code,
		strings.TrimSpace(req.BaselineRunCode),
	)
	if err != nil {
		response.FailWithMsg(err.Error(), ctx)
		a.warn(
			"GetAnalyzeRunMonitorProbeDraft service error",
			zap.String("tenant_code", strings.TrimSpace(req.TenantCode)),
			zap.String("code", code),
			zap.String("baseline_run_code", strings.TrimSpace(req.BaselineRunCode)),
			zap.Error(err),
		)
		return
	}

	response.OkWithData(resp, ctx)
}
```

- [ ] **Step 4: Implement minimal compare threading in the service**

Update `OneOps/app/netpath/service/impl/netpath.go`:

```go
func (s *NetPathService) GetAnalyzeRunMonitorProbeDraft(ctx context.Context, tenantCode string, code string, baselineRunCode string) (*dto.AnalyzeMonitorProbeDraftResp, error) {
	handoff, err := s.GetAnalyzeRunWorkflowHandoff(ctx, tenantCode, code, baselineRunCode)
	if err != nil {
		return nil, err
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
	return buildAnalyzeMonitorProbeDraft(handoff, plan), nil
}
```

- [ ] **Step 5: Re-run the focused service tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl -run 'TestNetPathServiceGetAnalyzeRunMonitorProbeDraft(WithoutBaselineLeavesCompareContextEmpty|WithBaselineCompareContext|BaselineCompareUnavailableDegradesGracefully)$' -count=1
```

Expected: FAIL moves forward, now showing missing compare-context attach and missing compare-aware summary/notes behavior rather than signature or compile errors.

- [ ] **Step 6: Add the failing API test for baseline query passthrough**

Add the following test near the existing monitor-probe API coverage in `OneOps/app/netpath/api/netpath_test.go`:

```go
func TestNetPathAPIMonitorProbeDraftWithBaselineCompareContext(t *testing.T) {
	db := newNetPathTestDB(t)
	seedDurableSnapshotForTest(t, db, "tenant-a", "snapshot-api-probe-base", "leaf-1")
	seedDurableSnapshotForTest(t, db, "tenant-a", "snapshot-api-probe-target", "leaf-1")
	engine := &fakeAnalysisEngine{
		result: &netpathengine.AnalyzeResult{
			SnapshotID:  "snapshot-api-probe-base",
			Disposition: "blocked_acl",
			Flow: netpathengine.Flow{
				SrcIP:             "10.0.0.1",
				DstIP:             "10.0.0.2",
				IngressDeviceCode: "leaf-1",
			},
			Traces: []netpathengine.Trace{{TraceID: "trace-1", Disposition: "blocked_acl", Hops: []netpathengine.Hop{{Sequence: 1, DeviceCode: "leaf-1"}, {Sequence: 2, DeviceCode: "fw-a"}}}},
			Diagnostics: []netpathengine.Diagnostic{{Severity: "warn", Code: "acl_block", Message: "security policy blocked the flow"}},
		},
	}
	svc := serviceimpl.NewNetPathService(db, serviceimpl.WithAnalysisEngine(engine))
	api := NewNetPathAPI(svc)

	router := gin.New()
	router.POST("/netpath/analysis-runs", api.CreateAnalyzeRun)
	router.POST("/netpath/analysis-runs/:code/probe-plan", api.BuildAnalyzeRunProbePlan)
	router.GET("/netpath/analysis-runs/:code/monitor-probe-draft", api.GetAnalyzeRunMonitorProbeDraft)

	baseRec := performNetPathAPIRequest(t, router, http.MethodPost, "/netpath/analysis-runs", dto.AnalyzeRunCreateReq{
		TenantCode:        "tenant-a",
		SnapshotID:        "snapshot-api-probe-base",
		SrcIP:             "10.0.0.1",
		DstIP:             "10.0.0.2",
		IngressDeviceCode: "leaf-1",
	})
	if baseRec.Code != http.StatusOK {
		t.Fatalf("expected baseline create 200, got %d body=%s", baseRec.Code, baseRec.Body.String())
	}
	var baseline dto.AnalyzeRunResp
	if err := json.Unmarshal(decodeNetPathAPIEnvelope(t, baseRec).Data, &baseline); err != nil {
		t.Fatalf("unmarshal baseline response failed: %v body=%s", err, baseRec.Body.String())
	}

	engine.result = &netpathengine.AnalyzeResult{
		SnapshotID:  "snapshot-api-probe-target",
		Disposition: "delivered_to_subnet",
		Flow: netpathengine.Flow{
			SrcIP:             "10.0.0.1",
			DstIP:             "10.0.0.2",
			IngressDeviceCode: "leaf-1",
		},
		Traces: []netpathengine.Trace{{TraceID: "trace-1", Disposition: "delivered_to_subnet", Hops: []netpathengine.Hop{{Sequence: 1, DeviceCode: "leaf-1"}, {Sequence: 2, DeviceCode: "fw-b"}}}},
	}
	targetRec := performNetPathAPIRequest(t, router, http.MethodPost, "/netpath/analysis-runs", dto.AnalyzeRunCreateReq{
		TenantCode:        "tenant-a",
		SnapshotID:        "snapshot-api-probe-target",
		SrcIP:             "10.0.0.1",
		DstIP:             "10.0.0.2",
		IngressDeviceCode: "leaf-1",
	})
	if targetRec.Code != http.StatusOK {
		t.Fatalf("expected target create 200, got %d body=%s", targetRec.Code, targetRec.Body.String())
	}
	var target dto.AnalyzeRunResp
	if err := json.Unmarshal(decodeNetPathAPIEnvelope(t, targetRec).Data, &target); err != nil {
		t.Fatalf("unmarshal target response failed: %v body=%s", err, targetRec.Body.String())
	}

	planRec := performNetPathAPIRequest(t, router, http.MethodPost, "/netpath/analysis-runs/"+target.Code+"/probe-plan", dto.AnalyzeProbePlanBuildReq{
		TenantCode: "tenant-a",
	})
	if planRec.Code != http.StatusOK {
		t.Fatalf("expected probe-plan 200, got %d body=%s", planRec.Code, planRec.Body.String())
	}

	rec := performNetPathAPIRequest(
		t,
		router,
		http.MethodGet,
		"/netpath/analysis-runs/"+target.Code+"/monitor-probe-draft?tenant_code=tenant-a&baseline_run_code="+baseline.Code,
		nil,
	)
	if rec.Code != http.StatusOK {
		t.Fatalf("expected status 200 from monitor probe draft, got %d body=%s", rec.Code, rec.Body.String())
	}
	var draft dto.AnalyzeMonitorProbeDraftResp
	if err := json.Unmarshal(decodeNetPathAPIEnvelope(t, rec).Data, &draft); err != nil {
		t.Fatalf("unmarshal monitor probe draft response failed: %v body=%s", err, rec.Body.String())
	}
	if draft.CompareContext == nil || draft.CompareContext.BaselineRunCode != baseline.Code {
		t.Fatalf("expected compare context in response, got %#v", draft)
	}
}
```

- [ ] **Step 7: Run the focused API test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/api -run TestNetPathAPIMonitorProbeDraftWithBaselineCompareContext -count=1
```

Expected: FAIL until compare context is attached into the monitor-probe draft response.

- [ ] **Step 8: Commit the API/service threading checkpoint**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/netpath/service/i_netpath.go app/netpath/api/netpath.go app/netpath/service/impl/netpath.go app/netpath/service/impl/netpath_test.go app/netpath/api/netpath_test.go
git commit -m "feat: thread baseline compare into monitor probe draft"
```

## Task 3: Add Compare-Aware Summary And Item Notes

**Files:**
- Modify: `OneOps/app/netpath/service/impl/netpath.go`
- Modify: `OneOps/app/netpath/service/impl/netpath_test.go`
- Modify: `OneOps/app/netpath/api/netpath_test.go`

- [ ] **Step 1: Add the failing note-detail assertions**

Tighten `TestNetPathServiceGetAnalyzeRunMonitorProbeDraftWithBaselineCompareContext` and `TestNetPathServiceGetAnalyzeRunMonitorProbeDraftBaselineCompareUnavailableDegradesGracefully` in `OneOps/app/netpath/service/impl/netpath_test.go` with these assertions:

```go
if !strings.Contains(draft.SupportedItems[0].Notes[len(draft.SupportedItems[0].Notes)-1], "人工复核") {
	t.Fatalf("expected trailing compare-review note, got %#v", draft.SupportedItems[0].Notes)
}
if draft.CompareContext.TargetRunCode != target.Code {
	t.Fatalf("expected target run code in compare context, got %#v", draft.CompareContext)
}
```

Add one positive backward-compatibility assertion to `TestNetPathServiceGetAnalyzeRunMonitorProbeDraft`:

```go
if draft.CompareContext != nil {
	t.Fatalf("expected nil compare context for existing no-baseline flow, got %#v", draft.CompareContext)
}
```

- [ ] **Step 2: Run the focused service tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl -run 'TestNetPathServiceGetAnalyzeRunMonitorProbeDraft(|WithoutBaselineLeavesCompareContextEmpty|WithBaselineCompareContext|BaselineCompareUnavailableDegradesGracefully)$' -count=1
```

Expected: FAIL because summary and item notes still reflect current-plan-only logic.

- [ ] **Step 3: Implement compare-aware draft composition**

Update `OneOps/app/netpath/service/impl/netpath.go` by extending `buildAnalyzeMonitorProbeDraft` and adding helper functions:

```go
func buildAnalyzeMonitorProbeDraft(handoff *dto.AnalyzeWorkflowHandoffResp, plan *dto.AnalyzeProbePlanResp) *dto.AnalyzeMonitorProbeDraftResp {
	resp := &dto.AnalyzeMonitorProbeDraftResp{
		AnalyzeRunCode: handoff.AnalyzeRunCode,
		TenantCode:     handoff.TenantCode,
		SnapshotID:     handoff.SnapshotID,
		ProbePlanCode:  handoff.ProbePlanCode,
		Status:         handoff.Status,
		ProbeType:      "Telegraf",
		CompareContext: cloneAnalyzeWorkflowCompareContext(handoff.CompareContext),
		RequiredPlaceholders: []string{
			"monitor_probe.code",
			"monitor_probe.host_code",
			"monitor_probe.settings[].code",
			"monitor_probe.settings[].file_path",
			"monitor_probe.settings[].setting_tag_mapping[].tag_code",
		},
		PushInfo: &dto.AnalyzeMonitorProbePushInfo{},
	}
	if plan == nil {
		resp.Summary = deriveAnalyzeMonitorProbeDraftSummary(handoff, false)
		return resp
	}
	resp.PushInfo.Code = "pending_monitor_probe_code"
	for _, item := range plan.Items {
		if item.Action != "ping" {
			resp.UnsupportedDirections = appendIfMissingString(resp.UnsupportedDirections, item.Direction)
			continue
		}
		resp.SupportedItems = append(resp.SupportedItems, dto.AnalyzeMonitorProbeDraftItem{
			Direction:     item.Direction,
			ProbeMode:     "Ping",
			TargetIP:      item.TargetIP,
			GatewayIP:     item.GatewayIP,
			DeviceCode:    item.DeviceCode,
			InterfaceName: item.InterfaceName,
			FilePathHint:  fmt.Sprintf("/etc/oneops/netpath/%s-%s.conf", handoff.AnalyzeRunCode, item.Direction),
			TagCodeHints: []string{
				"pending_tenant_scope_tag",
				fmt.Sprintf("pending_device_scope_%s", strings.ToLower(firstNonEmptyString(item.DeviceCode, handoff.Flow.IngressDeviceCode))),
			},
			Notes: buildAnalyzeMonitorProbeDraftItemNotes(item, handoff.CompareContext),
		})
		resp.PushInfo.SettingCodes = append(resp.PushInfo.SettingCodes, fmt.Sprintf("pending_setting_%s", strings.ToLower(item.Direction)))
	}
	resp.Summary = deriveAnalyzeMonitorProbeDraftSummary(handoff, len(resp.SupportedItems) > 0)
	return resp
}

func deriveAnalyzeMonitorProbeDraftSummary(handoff *dto.AnalyzeWorkflowHandoffResp, hasSupportedItems bool) string {
	if handoff != nil && handoff.CompareContext != nil {
		switch strings.ToLower(strings.TrimSpace(handoff.CompareContext.DeltaStatus)) {
		case "risk_changed":
			return "当前路径与 baseline 相比存在风险变化；monitor_probe 草案仅供参考，建议人工复核后再下发。"
		case "review_recommended":
			return "当前路径与 baseline 存在差异；建议先人工复核 tag、target 和 probe 范围，再决定是否下发。"
		case "context_only":
			if hasSupportedItems {
				return "已生成可映射到 maintenance/monitor_probe 的 ping 草案；存在 baseline 对比上下文，建议下发前复核映射。"
			}
		}
	}
	if handoff != nil && handoff.Status == "manual_review" {
		return "当前 handoff 仍需人工复核；monitor_probe 草案仅可作为映射参考，不建议直接下发。"
	}
	return "已生成可映射到 maintenance/monitor_probe 的 ping 草案；仍需补齐 host_code、tag 映射和 setting code。"
}

func buildAnalyzeMonitorProbeDraftItemNotes(item dto.AnalyzeProbePlanItem, compare *dto.AnalyzeWorkflowCompareContext) []string {
	notes := make([]string, 0)
	if strings.Contains(item.Direction, "gateway") {
		notes = append(notes, "该方向依赖 gateway 目标，请确认 tag 范围能覆盖对应探测源。")
	}
	if item.DeviceCode != "" {
		notes = append(notes, fmt.Sprintf("建议将 tag 映射到设备 %s 的探测域。", item.DeviceCode))
	}
	if item.InterfaceName != "" {
		notes = append(notes, fmt.Sprintf("接口线索：%s。", item.InterfaceName))
	}
	if compare != nil {
		switch strings.ToLower(strings.TrimSpace(compare.DeltaStatus)) {
		case "context_only":
			notes = append(notes, "存在 baseline 对比上下文，建议最终下发前复核 host、tag 与 target 映射。")
		case "review_recommended":
			notes = append(notes, "baseline 对比显示路径或快照上下文有变化，建议人工复核后再下发该方向配置。")
		case "risk_changed":
			notes = append(notes, "baseline 对比显示阻断或 disposition 已变化，未完成人工复核前不建议直接下发该方向配置。")
		}
	}
	return notes
}
```

- [ ] **Step 4: Re-run the focused service tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl -run 'TestNetPathServiceGetAnalyzeRunMonitorProbeDraft(|WithoutBaselineLeavesCompareContextEmpty|WithBaselineCompareContext|BaselineCompareUnavailableDegradesGracefully)$' -count=1
```

Expected: PASS.

- [ ] **Step 5: Re-run the focused API test**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/api -run TestNetPathAPIMonitorProbeDraftWithBaselineCompareContext -count=1
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/netpath/service/impl/netpath.go app/netpath/service/impl/netpath_test.go app/netpath/api/netpath_test.go
git commit -m "feat: add compare context to monitor probe draft"
```

## Task 4: Prove Adapter Backward Compatibility And Run Broader Verification

**Files:**
- Modify: `OneOps/app/netpath/adapter/oneopsnetpath/monitor_probe_draft_test.go`

- [ ] **Step 1: Write the adapter regression test**

Add this test to `OneOps/app/netpath/adapter/oneopsnetpath/monitor_probe_draft_test.go`:

```go
func TestBuildMonitorProbeDraftPayloadIgnoresCompareContext(t *testing.T) {
	payload, err := BuildMonitorProbeDraftPayload(&netpathDTO.AnalyzeMonitorProbeDraftResp{
		AnalyzeRunCode: "run-1",
		Summary:        "compare-aware summary",
		CompareContext: &netpathDTO.AnalyzeWorkflowCompareContext{
			BaselineRunCode: "run-0",
			DeltaStatus:     "risk_changed",
			DeltaSummary:    "disposition changed",
		},
		SupportedItems: []netpathDTO.AnalyzeMonitorProbeDraftItem{{
			Direction:    "src_to_dst_ping",
			TargetIP:     "10.0.0.2",
			FilePathHint: "/etc/oneops/netpath/run-1-src_to_dst_ping.conf",
			TagCodeHints: []string{"tag-a"},
		}},
	}, MonitorProbeDraftBuildOptions{
		ProbeCode: "NETPATH_PROBE",
		ProbeName: "NetPath Probe",
		HostCode:  "host-a",
	})
	if err != nil {
		t.Fatalf("BuildMonitorProbeDraftPayload returned error: %v", err)
	}
	if payload.ProbeReq == nil || payload.ProbeReq.Description != "compare-aware summary" {
		t.Fatalf("expected payload description to still use draft summary, got %#v", payload)
	}
	if payload.PushInfo == nil || payload.PushInfo.Code != "NETPATH_PROBE" {
		t.Fatalf("expected push info to remain unchanged, got %#v", payload.PushInfo)
	}
}
```

- [ ] **Step 2: Run the focused adapter test**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/adapter/oneopsnetpath -run TestBuildMonitorProbeDraftPayloadIgnoresCompareContext -count=1
```

Expected: PASS.

- [ ] **Step 3: Run the targeted NetPath verification suite**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl -run 'TestNetPathServiceGetAnalyzeRunMonitorProbeDraft(|WithoutBaselineLeavesCompareContextEmpty|WithBaselineCompareContext|BaselineCompareUnavailableDegradesGracefully)$' -count=1
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/api -run 'TestNetPathAPIMonitorProbeDraft(CompareContextPayloadShape|WithBaselineCompareContext)$' -count=1
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/adapter/oneopsnetpath -run 'TestBuildMonitorProbeDraftPayload(|UsesOverrides|ValidatesRequiredFields|IgnoresCompareContext)$' -count=1
```

Expected: all PASS.

- [ ] **Step 4: Run the broader NetPath package verification**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/... -count=1
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/netpath/adapter/oneopsnetpath/monitor_probe_draft_test.go
git commit -m "test: cover monitor probe draft compare compatibility"
```
