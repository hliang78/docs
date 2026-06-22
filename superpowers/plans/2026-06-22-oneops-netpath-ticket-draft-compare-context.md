# OneOPS NetPath Ticket Draft Compare Context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend NetPath ticket draft with optional baseline compare context while preserving current ticket owner/action/evidence semantics and carrying compare-aware metadata into task creation.

**Architecture:** Reuse workflow handoff as the single producer of durable run-compare context, then let ticket draft consume and reshape that context into a ticket-oriented `compare_context`. Thread the same optional `baseline_run_code` through ticket-draft and task-create entrypoints so downstream task metadata can carry stable delta signals without duplicating compare orchestration.

**Tech Stack:** Go, GORM, sqlite-backed Go tests, existing OneOPS NetPath DTO/API/router/service packages.

---

## File Structure

### Existing files to modify

- `OneOps/app/netpath/dto/netpath.go`
  - Add ticket-draft compare request/response DTO surface and optional task-create baseline input.
- `OneOps/app/netpath/service/i_netpath.go`
  - Extend ticket-draft service signature with optional baseline compare input.
- `OneOps/app/netpath/service/impl/netpath.go`
  - Thread baseline compare into ticket draft, map workflow compare context, tune summary/action wording, and add compare-aware task metadata.
- `OneOps/app/netpath/service/impl/netpath_test.go`
  - Add ticket-draft compare-context, degradation, and task metadata tests.
- `OneOps/app/netpath/api/netpath.go`
  - Bind `baseline_run_code` for ticket-draft query and pass task-create baseline input through unchanged body binding.
- `OneOps/app/netpath/api/netpath_test.go`
  - Add API payload-shape and end-to-end ticket-draft/task-create compare-context coverage.

## Task 1: Add Ticket Draft Compare DTO Surface

**Files:**
- Modify: `OneOps/app/netpath/dto/netpath.go`
- Modify: `OneOps/app/netpath/api/netpath_test.go`

- [ ] **Step 1: Write the failing DTO shape test**

Add a compile-focused test near `TestNetPathAPIWorkflowHandoffCompareContextPayloadShape` in `OneOps/app/netpath/api/netpath_test.go`:

```go
func TestNetPathAPITicketDraftCompareContextPayloadShape(t *testing.T) {
	_ = dto.AnalyzeTicketDraftReq{
		TenantCode:      "tenant-a",
		BaselineRunCode: "run-baseline",
	}

	_ = dto.AnalyzeTicketCompareContext{
		BaselineRunCode:    "run-baseline",
		BaselineSnapshotID: "snapshot-base",
		TargetRunCode:      "run-target",
		TargetSnapshotID:   "snapshot-followup",
		DeltaStatus:        "risk_changed",
		DeltaSummary:       "disposition changed; blocker +1/-0",
		DispositionChanged: true,
		AddedBlockers:      []dto.AnalyzeDiagnostic{{Code: "acl_block"}},
		RemovedBlockers:    []dto.AnalyzeDiagnostic{{Code: "legacy_block"}},
		AddedHops:          []dto.AnalyzeCompareHop{{Sequence: 2, DeviceCode: "fw-b"}},
		RemovedHops:        []dto.AnalyzeCompareHop{{Sequence: 2, DeviceCode: "fw-a"}},
	}

	_ = dto.AnalyzeTicketDraftResp{
		AnalyzeRunCode: "run-target",
		TenantCode:     "tenant-a",
		CompareContext: &dto.AnalyzeTicketCompareContext{
			DeltaStatus: "review_recommended",
		},
	}

	_ = dto.AnalyzeTaskCreateReq{
		TenantCode:      "tenant-a",
		BaselineRunCode: "run-baseline",
	}
}
```

- [ ] **Step 2: Run the focused API test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/api -run TestNetPathAPITicketDraftCompareContextPayloadShape -count=1
```

Expected: FAIL with undefined `AnalyzeTicketDraftReq`, undefined `AnalyzeTicketCompareContext`, unknown field `CompareContext`, and unknown field `BaselineRunCode` on `AnalyzeTaskCreateReq`.

- [ ] **Step 3: Add the ticket-draft DTOs**

Update `OneOps/app/netpath/dto/netpath.go`:

```go
type AnalyzeTicketDraftReq struct {
	TenantCode      string `json:"tenant_code" form:"tenant_code"`
	BaselineRunCode string `json:"baseline_run_code,omitempty" form:"baseline_run_code"`
}

type AnalyzeTicketCompareContext struct {
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

type AnalyzeTicketDraftResp struct {
	AnalyzeRunCode  string                      `json:"analyze_run_code"`
	TenantCode      string                      `json:"tenant_code"`
	SnapshotID      string                      `json:"snapshot_id"`
	Status          string                      `json:"status"`
	Summary         string                      `json:"summary"`
	SuggestedOwner  string                      `json:"suggested_owner"`
	SuggestedAction string                      `json:"suggested_action,omitempty"`
	Flow            AnalyzeFlow                 `json:"flow"`
	Disposition     string                      `json:"disposition,omitempty"`
	PathSummary     *AnalyzeTicketPathSummary   `json:"path_summary,omitempty"`
	Blockers        []AnalyzeDiagnostic         `json:"blockers,omitempty"`
	CompareContext  *AnalyzeTicketCompareContext `json:"compare_context,omitempty"`
	Evidence        []AnalyzeTicketEvidence     `json:"evidence,omitempty"`
	ProbeExecution  *AnalyzeProbeExecutionResp  `json:"probe_execution,omitempty"`
	Links           []AnalyzeTicketLink         `json:"links,omitempty"`
}

type AnalyzeTaskCreateReq struct {
	TenantCode      string                      `json:"tenant_code"`
	BaselineRunCode string                      `json:"baseline_run_code,omitempty"`
	Scope           AnalyzeTaskCreateScope      `json:"scope"`
	Script          AnalyzeTaskCreateScript     `json:"script"`
	Target          AnalyzeTaskCreateTarget     `json:"target"`
	Repository      AnalyzeTaskCreateRepository `json:"repository"`
	Params          AnalyzeTaskCreateParams     `json:"params"`
	Runtime         AnalyzeTaskCreateRuntime    `json:"runtime"`
	Credential      AnalyzeTaskCreateCredential `json:"credential"`
}
```

- [ ] **Step 4: Re-run the focused API test**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/api -run TestNetPathAPITicketDraftCompareContextPayloadShape -count=1
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/netpath/dto/netpath.go app/netpath/api/netpath_test.go
git commit -m "feat: add ticket draft compare dto surface"
```

## Task 2: Extend Ticket Draft Service And Compare-Aware Task Metadata

**Files:**
- Modify: `OneOps/app/netpath/service/i_netpath.go`
- Modify: `OneOps/app/netpath/service/impl/netpath.go`
- Modify: `OneOps/app/netpath/service/impl/netpath_test.go`

- [ ] **Step 1: Write the failing service tests**

Add the following tests near `TestNetPathServiceGetAnalyzeRunTicketDraft` in `OneOps/app/netpath/service/impl/netpath_test.go`:

```go
func TestNetPathServiceGetAnalyzeRunTicketDraftWithoutBaselineLeavesCompareContextEmpty(t *testing.T) {
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

	draft, err := svc.GetAnalyzeRunTicketDraft(context.Background(), "tenant-a", run.Code, "")
	if err != nil {
		t.Fatalf("GetAnalyzeRunTicketDraft returned error: %v", err)
	}
	if draft.CompareContext != nil {
		t.Fatalf("expected nil compare context without baseline, got %#v", draft.CompareContext)
	}
}

func TestNetPathServiceGetAnalyzeRunTicketDraftWithBaselineCompareContext(t *testing.T) {
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

	draft, err := svc.GetAnalyzeRunTicketDraft(context.Background(), "tenant-a", target.Code, baseline.Code)
	if err != nil {
		t.Fatalf("GetAnalyzeRunTicketDraft returned error: %v", err)
	}
	if draft.CompareContext == nil || draft.CompareContext.DeltaStatus != "risk_changed" {
		t.Fatalf("expected risk_changed compare context, got %#v", draft)
	}
	if !strings.Contains(draft.Summary, "baseline") && !strings.Contains(draft.Summary, "delta") {
		t.Fatalf("expected compare-aware summary, got %#v", draft.Summary)
	}
	if strings.TrimSpace(draft.SuggestedOwner) == "" {
		t.Fatalf("expected suggested owner to remain populated, got %#v", draft)
	}
}

func TestNetPathServiceGetAnalyzeRunTicketDraftBaselineCompareUnavailableDegradesGracefully(t *testing.T) {
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

	draft, err := svc.GetAnalyzeRunTicketDraft(context.Background(), "tenant-a", target.Code, "run-missing")
	if err != nil {
		t.Fatalf("GetAnalyzeRunTicketDraft returned error: %v", err)
	}
	if draft.CompareContext == nil || draft.CompareContext.DeltaStatus != "review_recommended" {
		t.Fatalf("expected review_recommended compare degradation, got %#v", draft)
	}
}

func TestNetPathServiceCreateAnalyzeRunTaskWithBaselineCarriesCompareMetadata(t *testing.T) {
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
	taskCreator := &fakeTaskCreationService{resp: &platformDTO.CreateTaskResp{TaskID: "task-compare-001"}}
	svc := NewNetPathService(db, WithAnalysisEngine(engine), WithTaskCreationService(taskCreator))

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

	_, err = svc.CreateAnalyzeRunTask(context.Background(), target.Code, dto.AnalyzeTaskCreateReq{
		TenantCode:      "tenant-a",
		BaselineRunCode: baseline.Code,
		Scope: dto.AnalyzeTaskCreateScope{ProjectID: "project-a", FunctionArea: "ops-network"},
		Script: dto.AnalyzeTaskCreateScript{AppType: "ansible", EntryPoint: "playbooks/netpath-diagnostic.yml"},
		Target: dto.AnalyzeTaskCreateTarget{DeviceCodes: []string{"leaf-1"}, InventoryContent: "leaf-1 ansible_host=10.0.1.10"},
		Repository: dto.AnalyzeTaskCreateRepository{RepoURL: "https://git.example.com/netops/diag.git", RepoBranch: "main"},
		Runtime: dto.AnalyzeTaskCreateRuntime{RunOnAgent: true, AgentCode: "agent-001"},
		Credential: dto.AnalyzeTaskCreateCredential{Ref: "cred://netpath/demo"},
	})
	if err != nil {
		t.Fatalf("CreateAnalyzeRunTask returned error: %v", err)
	}

	var extraVars map[string]interface{}
	if err := json.Unmarshal([]byte(taskCreator.envelope.Params.ExtraVarsJSON), &extraVars); err != nil {
		t.Fatalf("expected valid extra vars json, got %v", err)
	}
	metaRaw := extraVars["oneops_netpath"].(map[string]interface{})
	if metaRaw["baseline_run_code"] != baseline.Code || metaRaw["delta_status"] != "risk_changed" {
		t.Fatalf("expected compare-aware task metadata, got %#v", metaRaw)
	}
}
```

- [ ] **Step 2: Run the focused service tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl -run 'TestNetPathService(GetAnalyzeRunTicketDraftWithoutBaselineLeavesCompareContextEmpty|GetAnalyzeRunTicketDraftWithBaselineCompareContext|GetAnalyzeRunTicketDraftBaselineCompareUnavailableDegradesGracefully|CreateAnalyzeRunTaskWithBaselineCarriesCompareMetadata)' -count=1
```

Expected: FAIL because `GetAnalyzeRunTicketDraft` does not yet accept a baseline run code, no ticket compare context is emitted, and task-create cannot yet forward baseline compare metadata.

- [ ] **Step 3: Extend the ticket-draft service signature**

Update `OneOps/app/netpath/service/i_netpath.go`:

```go
GetAnalyzeRunTicketDraft(ctx context.Context, tenantCode string, code string, baselineRunCode string) (*dto.AnalyzeTicketDraftResp, error)
```

Update internal call sites in `OneOps/app/netpath/service/impl/netpath.go` so:

```go
draft, err := s.GetAnalyzeRunTicketDraft(ctx, tenantCode, code, strings.TrimSpace(req.BaselineRunCode))
```

and any existing compare-free calls pass `""`.

- [ ] **Step 4: Extend ticket-draft service behavior**

Update `OneOps/app/netpath/service/impl/netpath.go` so `GetAnalyzeRunTicketDraft(...)`:

```go
func (s *NetPathService) GetAnalyzeRunTicketDraft(ctx context.Context, tenantCode string, code string, baselineRunCode string) (*dto.AnalyzeTicketDraftResp, error) {
	handoff, err := s.GetAnalyzeRunWorkflowHandoff(ctx, tenantCode, code, baselineRunCode)
	if err != nil {
		return nil, err
	}
	run, err := s.GetAnalyzeRun(ctx, tenantCode, code)
	if err != nil {
		return nil, err
	}
	probeExecution, err := s.GetAnalyzeRunProbeExecution(ctx, tenantCode, code)
	if err != nil {
		return nil, err
	}
	return buildAnalyzeTicketDraft(run, handoff, probeExecution), nil
}
```

Then extend `buildAnalyzeTicketDraft(...)` to map handoff compare context:

```go
func buildAnalyzeTicketDraft(run *dto.AnalyzeRunResp, handoff *dto.AnalyzeWorkflowHandoffResp, probeExecution *dto.AnalyzeProbeExecutionResp) *dto.AnalyzeTicketDraftResp {
	// existing draft construction...
	if handoff != nil && handoff.CompareContext != nil {
		draft.CompareContext = buildAnalyzeTicketCompareContext(handoff.CompareContext)
	}
	draft.SuggestedAction = buildAnalyzeTicketSuggestedAction(draft.SuggestedOwner, draft.CompareContext)
	draft.Summary = buildAnalyzeTicketSummary(draft)
	draft.Links = buildAnalyzeTicketLinks(run, draft)
	return draft
}
```

- [ ] **Step 5: Add compare-context helpers and tune summary/action/links**

Add helpers in `OneOps/app/netpath/service/impl/netpath.go`:

```go
func buildAnalyzeTicketCompareContext(ctx *dto.AnalyzeWorkflowCompareContext) *dto.AnalyzeTicketCompareContext
func compareDiagnosticCodes(diagnostics []dto.AnalyzeDiagnostic) []string
func compareHopDevices(hops []dto.AnalyzeCompareHop) []string
```

Recommended action tuning:

```go
func buildAnalyzeTicketSuggestedAction(owner string, compareCtx *dto.AnalyzeTicketCompareContext) string {
	base := existingTicketSuggestedAction(owner)
	if compareCtx == nil {
		return base
	}
	switch strings.TrimSpace(compareCtx.DeltaStatus) {
	case "risk_changed":
		return "请先复核基线差异、阻断变化和设备路径变化，再执行后续处置。" + base
	case "review_recommended":
		return "建议先复核当前结果相对基线的变化，再决定是否执行后续动作。" + base
	default:
		return base
	}
}
```

Summary tuning:

```go
func buildAnalyzeTicketSummary(draft *dto.AnalyzeTicketDraftResp) string {
	base := existingTicketSummary(draft)
	if draft == nil || draft.CompareContext == nil {
		return base
	}
	switch strings.TrimSpace(draft.CompareContext.DeltaStatus) {
	case "context_only":
		return fmt.Sprintf("%s / compare=%s", base, draft.CompareContext.DeltaSummary)
	case "review_recommended", "risk_changed":
		return fmt.Sprintf("%s / baseline_delta=%s", base, draft.CompareContext.DeltaSummary)
	default:
		return base
	}
}
```

Link tuning:

```go
if draft.CompareContext != nil && strings.TrimSpace(draft.CompareContext.BaselineRunCode) != "" {
	links = append(links,
		dto.AnalyzeTicketLink{
			Kind:   "workflow_handoff_compare",
			Label:  "Workflow Handoff Compare",
			Target: fmt.Sprintf("/api/netpath/analysis-runs/%s/workflow-handoff?tenant_code=%s&baseline_run_code=%s", run.Code, run.TenantCode, draft.CompareContext.BaselineRunCode),
		},
		dto.AnalyzeTicketLink{
			Kind:   "run_compare",
			Label:  "Run Compare",
			Target: fmt.Sprintf("/api/netpath/analysis-runs/%s/compare?tenant_code=%s&target_run_code=%s", draft.CompareContext.BaselineRunCode, run.TenantCode, run.Code),
		},
	)
}
```

- [ ] **Step 6: Extend task metadata with compare-aware fields**

Update `buildAnalyzeTaskMetadata(...)` in `OneOps/app/netpath/service/impl/netpath.go`:

```go
if draft != nil && draft.CompareContext != nil {
	metadata["baseline_run_code"] = strings.TrimSpace(draft.CompareContext.BaselineRunCode)
	metadata["baseline_snapshot_id"] = strings.TrimSpace(draft.CompareContext.BaselineSnapshotID)
	metadata["target_run_code"] = strings.TrimSpace(draft.CompareContext.TargetRunCode)
	metadata["target_snapshot_id"] = strings.TrimSpace(draft.CompareContext.TargetSnapshotID)
	metadata["delta_status"] = strings.TrimSpace(draft.CompareContext.DeltaStatus)
	metadata["delta_summary"] = strings.TrimSpace(draft.CompareContext.DeltaSummary)
	metadata["disposition_changed"] = draft.CompareContext.DispositionChanged
	metadata["added_blocker_codes"] = compareDiagnosticCodes(draft.CompareContext.AddedBlockers)
	metadata["removed_blocker_codes"] = compareDiagnosticCodes(draft.CompareContext.RemovedBlockers)
	metadata["added_hop_devices"] = compareHopDevices(draft.CompareContext.AddedHops)
	metadata["removed_hop_devices"] = compareHopDevices(draft.CompareContext.RemovedHops)
}
```

- [ ] **Step 7: Re-run the focused service tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl -run 'TestNetPathService(GetAnalyzeRunTicketDraftWithoutBaselineLeavesCompareContextEmpty|GetAnalyzeRunTicketDraftWithBaselineCompareContext|GetAnalyzeRunTicketDraftBaselineCompareUnavailableDegradesGracefully|CreateAnalyzeRunTaskWithBaselineCarriesCompareMetadata|GetAnalyzeRunTicketDraft)' -count=1
```

Expected: PASS.

- [ ] **Step 8: Run the broader ticket/task verification**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/service/impl -run 'TestNetPathService(GetAnalyzeRunTicketDraft|CreateAnalyzeRunTask|GetAnalyzeRunWorkflowHandoff)' -count=1
```

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/netpath/service/i_netpath.go app/netpath/service/impl/netpath.go app/netpath/service/impl/netpath_test.go
git commit -m "feat: add ticket draft compare context"
```

## Task 3: Bind API Baseline Input And Add End-To-End Coverage

**Files:**
- Modify: `OneOps/app/netpath/api/netpath.go`
- Modify: `OneOps/app/netpath/api/netpath_test.go`

- [ ] **Step 1: Write the failing API tests**

Add new API-level tests near the existing ticket-draft and task-create coverage in `OneOps/app/netpath/api/netpath_test.go`:

```go
func TestNetPathAPITicketDraftWithBaselineCompareContext(t *testing.T) {
	// create baseline snapshot/run
	// create target snapshot/run
	// GET /netpath/analysis-runs/:code/ticket-draft?tenant_code=tenant-a&baseline_run_code=<baseline>
	// assert compare_context.delta_status == "risk_changed"
	// assert suggested_action mentions baseline review
}

func TestNetPathAPICreateAnalyzeRunTaskWithBaselineCarriesCompareMetadata(t *testing.T) {
	// create baseline + target runs
	// POST /netpath/analysis-runs/:code/task-create with baseline_run_code in JSON body
	// assert task create succeeds
	// assert returned fake task envelope extra vars include baseline_run_code + delta_status
}
```

- [ ] **Step 2: Run the focused API tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/api -run 'TestNetPathAPI(TicketDraftWithBaselineCompareContext|CreateAnalyzeRunTaskWithBaselineCarriesCompareMetadata)' -count=1
```

Expected: FAIL because ticket-draft API does not yet bind `baseline_run_code` and task-create does not yet flow compare metadata through the request body.

- [ ] **Step 3: Bind ticket-draft baseline input in the API layer**

Update `OneOps/app/netpath/api/netpath.go`:

```go
func (a *NetPathAPI) GetAnalyzeRunTicketDraft(ctx *gin.Context) {
	code := strings.TrimSpace(ctx.Param("code"))
	var req dto.AnalyzeTicketDraftReq
	if err := ctx.ShouldBindQuery(&req); err != nil {
		response.FailWithMsg(err.Error(), ctx)
		a.warn("GetAnalyzeRunTicketDraft bind query error", zap.Error(err))
		return
	}

	resp, err := a.NetPathSrv.GetAnalyzeRunTicketDraft(ctx, strings.TrimSpace(req.TenantCode), code, strings.TrimSpace(req.BaselineRunCode))
	if err != nil {
		response.FailWithMsg(err.Error(), ctx)
		a.warn("GetAnalyzeRunTicketDraft service error",
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

- [ ] **Step 4: Implement the end-to-end API assertions**

In `OneOps/app/netpath/api/netpath_test.go`, add concrete assertions matching the service behavior:

```go
if ticketDraft.CompareContext == nil || ticketDraft.CompareContext.DeltaStatus != "risk_changed" {
	t.Fatalf("expected risk_changed compare context, got %#v", ticketDraft)
}
if !strings.Contains(ticketDraft.SuggestedAction, "基线") {
	t.Fatalf("expected compare-aware suggested action, got %#v", ticketDraft.SuggestedAction)
}
if metaRaw["baseline_run_code"] != baseline.Code || metaRaw["delta_status"] != "risk_changed" {
	t.Fatalf("expected compare-aware task metadata, got %#v", metaRaw)
}
```

- [ ] **Step 5: Re-run the focused API tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/api -run 'TestNetPathAPI(TicketDraftWithBaselineCompareContext|CreateAnalyzeRunTaskWithBaselineCarriesCompareMetadata)' -count=1
```

Expected: PASS.

- [ ] **Step 6: Run the full NetPath verification**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/... -count=1
```

Expected: PASS across API, DTO, router, runtime, and service packages.

- [ ] **Step 7: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/netpath/api/netpath.go app/netpath/api/netpath_test.go
git commit -m "feat: add ticket draft baseline compare context"
```
