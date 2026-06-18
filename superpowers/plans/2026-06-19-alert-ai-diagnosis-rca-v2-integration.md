# Alert AI Diagnosis RCA V2 Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the OneOPS alert detail "AI 分析" loop by feeding the current alert-page RCA V2 result into AIOps diagnosis evidence and rendering the result clearly in the frontend drawer.

**Architecture:** `AIOpsAPI.AnalyzeAlertDiagnosis` injects `alertService.IAlertAlarmRootCauseV2App`, maps the AIOps alert request into `AlertAlarmAnalyzeRootCauseV2Req`, converts `MonitoringRootCauseV2AnalyzeResp` into `RCAAnalysisResult` plus normalized evidence, then passes log evidence and RCA evidence into the existing Ollama diagnosis generator. The frontend keeps the same entry point but displays RCA/log/status evidence explicitly so the user can tell whether RCA V2 completed or degraded.

**Tech Stack:** Go, Gin, Wire, existing OneOPS alert/platform DTOs, Vue 3, TypeScript, Ant Design Vue, local Ollama-backed AIOps diagnosis generator.

---

## File Structure

- Create `OneOPS/app/aiops/service/impl/alert_rca_v2_adapter.go`: pure helper functions for request mapping, RCA V2 result conversion, RCA evidence conversion, and degradation evidence.
- Create `OneOPS/app/aiops/service/impl/alert_rca_v2_adapter_test.go`: focused unit tests for all adapter behavior.
- Modify `OneOPS/app/aiops/api/aiops.go`: inject `alertService.IAlertAlarmRootCauseV2App`, call RCA V2, merge RCA evidence with log evidence, and degrade on RCA failure.
- Modify `OneOPS/app/aiops/api/aiops_test.go`: handler-level tests for RCA success, RCA error degradation, and missing target degradation.
- Modify `OneOPS/cmd/wire_gen.go`: pass the existing `alertAlarmRootCauseV2App` into `AIOpsAPI`.
- Modify `OneOPS-UI/src/typings/aiops.ts`: add explicit frontend evidence grouping types used by the drawer smoke.
- Modify `OneOPS-UI/src/views/alert/AlarmAIDiagnosisDrawer.vue`: display normalized evidence grouped as RCA, logs, and status.
- Modify `OneOPS-UI/scripts/alert-ai-diagnosis-smoke.ts`: assert request builder still produces the fields RCA V2 needs.
- Create `OneOPS-UI/scripts/alert-ai-diagnosis-drawer-smoke.ts`: smoke-test report grouping logic with RCA candidate/path/attachment/status and log evidence.
- Modify `OneOPS-UI/package.json`: add `smoke:alert-ai-diagnosis-drawer`.
- Create `OneOPS/scripts/aiops_alert_diagnosis_long_chain_smoke.go`: local harness for handler -> RCA stub -> evidence -> generator path.

## Data Model

Use these constants in adapter code:

```go
const (
	alertRCAConclusionCompleted   = "monitoring_root_cause_v2_completed"
	alertRCAConclusionUnavailable = "monitoring_root_cause_v2_unavailable"

	alertRCAEvidenceTypeCandidate  = "rca_candidate"
	alertRCAEvidenceTypeAnalysis    = "rca_analysis"
	alertRCAEvidenceTypePath        = "rca_path"
	alertRCAEvidenceTypeAttachment  = "rca_attachment"
	alertRCAEvidenceTypeStatus      = "rca_status"
	alertRCAEvidenceSource          = "monitoring_root_cause_v2"
)
```

All generated RCA evidence IDs must be stable and citation-safe:

```text
rca:v2:candidate:<object_type>:<object_id>
rca:v2:analysis:<scope-or-index>
rca:v2:path:<path_set_id>:<path_id>
rca:v2:attachment:<attachment_id-or-hash>
rca:v2:status:unavailable
```

## Task 1: Backend RCA V2 Adapter

**Files:**
- Create: `OneOPS/app/aiops/service/impl/alert_rca_v2_adapter.go`
- Create: `OneOPS/app/aiops/service/impl/alert_rca_v2_adapter_test.go`

- [ ] **Step 1: Write failing adapter tests**

Add tests that build a representative `MonitoringRootCauseV2AnalyzeResp` and assert conversion behavior:

```go
func TestBuildAlertRootCauseV2Request(t *testing.T) {
	req, ok, unavailable := BuildAlertRootCauseV2Request(aiopsDTO.AlertDiagnosisReq{
		RequestID:  "req-1",
		AlertID:    "alarm-1",
		TenantID:   "tenant-a",
		ObservedAt: "2026-06-18T10:00:00Z",
		Target: aiopsDTO.ObjectRef{
			Type: aiopsDTO.TargetTypeDevice,
			ID:   "device-1",
		},
		Metadata: map[string]string{"monitor_id": "monitor-a"},
	})
	if !ok {
		t.Fatalf("expected RCA request to be buildable: %+v", unavailable)
	}
	if req.RequestID != "req-1" || req.TenantCode != "tenant-a" || req.CurrentAlertCode != "alarm-1" {
		t.Fatalf("unexpected mapped request: %+v", req)
	}
	if req.TargetID != "device-1" || req.MonitorID != "monitor-a" {
		t.Fatalf("unexpected RCA target/monitor: %+v", req)
	}
}

func TestBuildAlertRootCauseV2RequestMissingTargetDegrades(t *testing.T) {
	_, ok, unavailable := BuildAlertRootCauseV2Request(aiopsDTO.AlertDiagnosisReq{
		RequestID:  "req-1",
		AlertID:    "alarm-1",
		TenantID:   "tenant-a",
		ObservedAt: "2026-06-18T10:00:00Z",
		Target:     aiopsDTO.ObjectRef{Type: aiopsDTO.TargetTypeDevice},
	})
	if ok {
		t.Fatalf("expected missing target to skip RCA")
	}
	if unavailable.RCA.Conclusion != alertRCAConclusionUnavailable {
		t.Fatalf("expected unavailable RCA, got %+v", unavailable.RCA)
	}
	if len(unavailable.Evidence) != 1 || unavailable.Evidence[0].ID != "rca:v2:status:unavailable" {
		t.Fatalf("expected unavailable status evidence, got %+v", unavailable.Evidence)
	}
}

func TestConvertMonitoringRootCauseV2AnalyzeResp(t *testing.T) {
	resp := sampleMonitoringRootCauseV2AnalyzeResp()
	rca, evidence := ConvertMonitoringRootCauseV2AnalyzeResp(resp)
	if rca.Conclusion != alertRCAConclusionCompleted {
		t.Fatalf("expected completed RCA, got %+v", rca)
	}
	if len(rca.Candidates) != 1 {
		t.Fatalf("expected one final candidate, got %+v", rca.Candidates)
	}
	if rca.Candidates[0].ObjectRef.Type != "node" || rca.Candidates[0].ObjectRef.ID != "device-1" {
		t.Fatalf("unexpected candidate object ref: %+v", rca.Candidates[0])
	}
	assertEvidenceID(t, evidence, "rca:v2:candidate:node:device-1")
	assertEvidenceID(t, evidence, "rca:v2:analysis:physical")
	assertEvidenceID(t, evidence, "rca:v2:path:monitor-to-device:path-1")
	assertEvidenceID(t, evidence, "rca:v2:attachment:att-1")
}

func TestUnavailableMonitoringRootCauseV2(t *testing.T) {
	result := UnavailableMonitoringRootCauseV2("topology path not found")
	if result.RCA.Conclusion != alertRCAConclusionUnavailable {
		t.Fatalf("expected unavailable conclusion, got %+v", result.RCA)
	}
	if !strings.Contains(result.RCA.Reasons[0], "topology path not found") {
		t.Fatalf("expected reason to include RCA error, got %+v", result.RCA.Reasons)
	}
	if len(result.Evidence) != 1 || result.Evidence[0].Type != alertRCAEvidenceTypeStatus {
		t.Fatalf("expected one status evidence, got %+v", result.Evidence)
	}
}
```

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/aiops/service/impl -run 'Test(BuildAlertRootCauseV2Request|ConvertMonitoringRootCauseV2AnalyzeResp|UnavailableMonitoringRootCauseV2)' -count=1
```

Expected: FAIL because adapter functions do not exist.

- [ ] **Step 2: Implement adapter helpers**

Create `alert_rca_v2_adapter.go` with these exported functions:

```go
type AlertRootCauseV2UnavailableResult struct {
	RCA      aiopsDTO.RCAAnalysisResult
	Evidence []aiopsDTO.NormalizedEvidence
}

func BuildAlertRootCauseV2Request(req aiopsDTO.AlertDiagnosisReq) (alertDTO.AlertAlarmAnalyzeRootCauseV2Req, bool, AlertRootCauseV2UnavailableResult)
func ConvertMonitoringRootCauseV2AnalyzeResp(resp *platformDTO.MonitoringRootCauseV2AnalyzeResp) (aiopsDTO.RCAAnalysisResult, []aiopsDTO.NormalizedEvidence)
func UnavailableMonitoringRootCauseV2(reason string) AlertRootCauseV2UnavailableResult
```

Implementation rules:

- Trim all request strings.
- Map `tenant_id` to `tenant_code`.
- Use `metadata["monitor_id"]` only when non-empty.
- If target id is empty, return `ok=false` and `UnavailableMonitoringRootCauseV2("target.id is required for monitoring_root_cause_v2")`.
- If response is nil, return unavailable result from `ConvertMonitoringRootCauseV2AnalyzeResp`.
- Use `sha1` or `fnv` only for missing attachment IDs. Never use random IDs.
- Use compact evidence summaries. Include object type/id, role, score, reasons, path hop count, attachment category/type/source/summary.

- [ ] **Step 3: Run adapter tests**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/aiops/service/impl -run 'Test(BuildAlertRootCauseV2Request|ConvertMonitoringRootCauseV2AnalyzeResp|UnavailableMonitoringRootCauseV2)' -count=1
```

Expected: PASS.

- [ ] **Step 4: Commit adapter**

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
git add app/aiops/service/impl/alert_rca_v2_adapter.go app/aiops/service/impl/alert_rca_v2_adapter_test.go
git commit -m "feat(aiops): convert alert RCA V2 into diagnosis evidence"
```

## Task 2: AIOps Handler RCA Integration

**Files:**
- Modify: `OneOPS/app/aiops/api/aiops.go`
- Modify: `OneOPS/app/aiops/api/aiops_test.go`

- [ ] **Step 1: Write failing handler tests**

Add a fake RCA app in `aiops_test.go`:

```go
type fakeAlertRootCauseV2App struct {
	lastReq alertDTO.AlertAlarmAnalyzeRootCauseV2Req
	resp    *platformDTO.MonitoringRootCauseV2AnalyzeResp
	err     error
	calls   int
}

func (f *fakeAlertRootCauseV2App) Analyze(ctx context.Context, req alertDTO.AlertAlarmAnalyzeRootCauseV2Req) (*platformDTO.MonitoringRootCauseV2AnalyzeResp, error) {
	f.calls++
	f.lastReq = req
	if f.err != nil {
		return nil, f.err
	}
	return f.resp, nil
}
```

Add tests:

```go
func TestAIOpsAPIAnalyzeAlertDiagnosisUsesAlertRCAv2(t *testing.T) {
	fakeGenerator := &fakeAlertDiagnosisGenerator{}
	fakeRCA := &fakeAlertRootCauseV2App{resp: sampleAIOpsMonitoringRootCauseV2AnalyzeResp()}
	api := &AIOpsAPI{
		Logger:                  zap.NewNop(),
		AlertDiagnosisGenerator: fakeGenerator,
		AlertRootCauseV2App:     fakeRCA,
	}
	reqBody := marshalAlertDiagnosisReqWithLog(t, map[string]string{"monitor_id": "monitor-a"})
	ctx, recorder := newAIOpsTestContext(t, http.MethodPost, "/aiops/alerts:diagnose", reqBody)

	api.AnalyzeAlertDiagnosis(ctx)

	assertAIOpsOK(t, recorder)
	if fakeRCA.calls != 1 {
		t.Fatalf("expected RCA V2 called once, got %d", fakeRCA.calls)
	}
	if fakeRCA.lastReq.CurrentAlertCode != "alert-001" || fakeRCA.lastReq.TargetID != "SW-001" {
		t.Fatalf("unexpected RCA V2 request: %+v", fakeRCA.lastReq)
	}
	if fakeGenerator.lastReq.RCA.Conclusion != "monitoring_root_cause_v2_completed" {
		t.Fatalf("expected completed RCA passed to generator, got %+v", fakeGenerator.lastReq.RCA)
	}
	if !hasEvidencePrefix(fakeGenerator.lastReq.Evidence, "rca:v2:candidate:") {
		t.Fatalf("expected RCA candidate evidence, got %+v", fakeGenerator.lastReq.Evidence)
	}
	if !hasEvidencePrefix(fakeGenerator.lastReq.Evidence, "network.log:1#") {
		t.Fatalf("expected uploaded log evidence to remain, got %+v", fakeGenerator.lastReq.Evidence)
	}
}

func TestAIOpsAPIAnalyzeAlertDiagnosisDegradesWhenRCAv2Fails(t *testing.T) {
	fakeGenerator := &fakeAlertDiagnosisGenerator{}
	fakeRCA := &fakeAlertRootCauseV2App{err: fmt.Errorf("path not found")}
	api := &AIOpsAPI{
		Logger:                  zap.NewNop(),
		AlertDiagnosisGenerator: fakeGenerator,
		AlertRootCauseV2App:     fakeRCA,
	}
	reqBody := marshalAlertDiagnosisReqWithLog(t, nil)
	ctx, recorder := newAIOpsTestContext(t, http.MethodPost, "/aiops/alerts:diagnose", reqBody)

	api.AnalyzeAlertDiagnosis(ctx)

	assertAIOpsOK(t, recorder)
	if fakeGenerator.lastReq.RCA.Conclusion != "monitoring_root_cause_v2_unavailable" {
		t.Fatalf("expected unavailable RCA, got %+v", fakeGenerator.lastReq.RCA)
	}
	if !hasEvidenceID(fakeGenerator.lastReq.Evidence, "rca:v2:status:unavailable") {
		t.Fatalf("expected unavailable RCA status evidence, got %+v", fakeGenerator.lastReq.Evidence)
	}
}
```

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/aiops/api -run 'TestAIOpsAPIAnalyzeAlertDiagnosis(UsesAlertRCAv2|DegradesWhenRCAv2Fails)' -count=1
```

Expected: FAIL because `AIOpsAPI` has no `AlertRootCauseV2App` field and handler still uses the temporary RCA sentinel.

- [ ] **Step 2: Implement handler integration**

In `aiops.go`:

- Import alert service:

```go
alertService "github.com/netxops/OneOps/app/alert/service"
```

- Add the field:

```go
AlertRootCauseV2App alertService.IAlertAlarmRootCauseV2App
```

- Replace the temporary RCA sentinel block with:

```go
rcaResult := aiopsImpl.UnavailableMonitoringRootCauseV2("alert RCA V2 app is not initialized")
if a.AlertRootCauseV2App != nil {
	rcaReq, ok, unavailable := aiopsImpl.BuildAlertRootCauseV2Request(req)
	if ok {
		rcaResp, rcaErr := a.AlertRootCauseV2App.Analyze(ctx.Request.Context(), rcaReq)
		if rcaErr != nil {
			if a.Logger != nil {
				a.Logger.Warn("AIOps alert RCA V2 unavailable", zap.Error(rcaErr))
			}
			rcaResult = aiopsImpl.UnavailableMonitoringRootCauseV2(rcaErr.Error())
		} else {
			rca, rcaEvidence := aiopsImpl.ConvertMonitoringRootCauseV2AnalyzeResp(rcaResp)
			rcaResult = aiopsImpl.AlertRootCauseV2UnavailableResult{
				RCA:      rca,
				Evidence: rcaEvidence,
			}
		}
	} else {
		rcaResult = unavailable
	}
}
evidence = append(evidence, rcaResult.Evidence...)
```

Then pass `RCA: rcaResult.RCA` to the generator.

- [ ] **Step 3: Run handler tests**

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/aiops/api -run 'TestAIOpsAPIAnalyzeAlertDiagnosis|TestAIOpsAPI_AnalyzeAlertDiagnosis' -count=1
```

Expected: PASS.

- [ ] **Step 4: Commit handler integration**

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
git add app/aiops/api/aiops.go app/aiops/api/aiops_test.go
git commit -m "feat(aiops): attach RCA V2 to alert diagnosis"
```

## Task 3: Wire AIOps API Dependency

**Files:**
- Modify: `OneOPS/cmd/wire_gen.go`

- [ ] **Step 1: Write or run the compile check that fails before wiring**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./cmd -run '^$' -count=1
```

Expected before wiring: FAIL or compile evidence showing the new `AIOpsAPI.AlertRootCauseV2App` field is unset in generated wiring.

- [ ] **Step 2: Wire the existing app**

Find the `AIOpsAPI` struct literal in `cmd/wire_gen.go` and set:

```go
AlertRootCauseV2App: alertAlarmRootCauseV2App,
```

Use the existing local variable already produced by the alert RCA V2 provider set. Do not instantiate another RCA service.

- [ ] **Step 3: Run compile check**

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./cmd -run '^$' -count=1
```

Expected: PASS.

- [ ] **Step 4: Commit wiring**

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
git add cmd/wire_gen.go
git commit -m "chore(aiops): wire alert RCA V2 app"
```

## Task 4: Frontend RCA Evidence Closure

**Files:**
- Modify: `OneOPS-UI/src/views/alert/AlarmAIDiagnosisDrawer.vue`
- Modify: `OneOPS-UI/src/typings/aiops.ts`
- Create: `OneOPS-UI/scripts/alert-ai-diagnosis-drawer-smoke.ts`
- Modify: `OneOPS-UI/package.json`

- [ ] **Step 1: Write failing frontend drawer smoke**

Create a small pure function export from the drawer script section or from a new helper section:

```ts
export function groupAIOpsDiagnosisEvidence(report?: AIOpsDiagnosisReport | null) {
  const evidence = report?.normalized_evidence || [];
  return {
    rca: evidence.filter(item => String(item.type || '').startsWith('rca_') && item.type !== 'rca_status'),
    logs: evidence.filter(item => item.type === 'uploaded_log'),
    status: evidence.filter(item => item.type === 'rca_status'),
    other: evidence.filter(item => {
      const type = String(item.type || '');
      return type !== 'uploaded_log' && type !== 'rca_status' && !type.startsWith('rca_');
    }),
  };
}
```

The smoke script should import the function and assert:

```ts
const groups = groupAIOpsDiagnosisEvidence(report);
assertEqual(groups.rca.length, 3, 'RCA candidate/path/attachment evidence should group together');
assertEqual(groups.logs.length, 1, 'uploaded log evidence should remain separate');
assertEqual(groups.status.length, 1, 'RCA unavailable status should be visible');
```

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
yarn tsx scripts/alert-ai-diagnosis-drawer-smoke.ts
```

Expected: FAIL because the grouping helper and smoke script do not exist.

- [ ] **Step 2: Add grouped evidence UI**

Update `AlarmAIDiagnosisDrawer.vue` to show a new "证据" section before "引用".

Display groups:

- "RCA V2" for `rca_candidate`, `rca_analysis`, `rca_path`, `rca_attachment`.
- "日志" for `uploaded_log`.
- "状态" for `rca_status`.
- "其他" for remaining evidence types.

Each evidence item must show:

- `summary`
- `id`
- `source`
- `occurred_at` when present

Keep the drawer read-only. Do not add execute buttons.

- [ ] **Step 3: Add package script**

In `package.json`, add:

```json
"smoke:alert-ai-diagnosis-drawer": "tsx scripts/alert-ai-diagnosis-drawer-smoke.ts"
```

- [ ] **Step 4: Run frontend smoke**

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
yarn smoke:alert-ai-diagnosis
yarn smoke:alert-ai-diagnosis-drawer
```

Expected: PASS.

- [ ] **Step 5: Run frontend typecheck**

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npm run typecheck
```

Expected: PASS or only known unrelated pre-existing failures. If unrelated failures appear, record exact file names and run a narrower `vue-tsc`/`tsc` command that covers `src/views/alert`, `src/typings/aiops.ts`, and the new smoke script.

- [ ] **Step 6: Commit frontend closure**

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
git add src/views/alert/AlarmAIDiagnosisDrawer.vue src/typings/aiops.ts scripts/alert-ai-diagnosis-drawer-smoke.ts package.json
git commit -m "feat(alert): show AI diagnosis evidence groups"
```

## Task 5: Longest-Chain Smoke

**Files:**
- Modify or create: `OneOPS/scripts/aiops_alert_diagnosis_long_chain_smoke.go`
- Modify: `memory/2026-06-19.md`

- [ ] **Step 1: Build the controllable backend smoke harness**

Create a Go script that constructs:

- `AIOpsAPI`
- fake `AlertRootCauseV2App` returning one candidate, one analysis, one path, one attachment
- fake or real `AlertDiagnosisGenerator`

Use the real generator only when local Ollama provider config is available without DB boot. If not, use a fake generator that validates the evidence set it receives and returns a report citing both one RCA evidence ID and one uploaded log evidence ID.

The script must print:

```text
LONG_CHAIN_SMOKE_PASSED
rca_status: monitoring_root_cause_v2_completed
rca_evidence: <count>
log_evidence: <count>
frontend_builder: passed
drawer_grouping: passed
```

- [ ] **Step 2: Run backend and frontend checks**

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/aiops/... -count=1
go test ./cmd -run '^$' -count=1
go run ./scripts/aiops_alert_diagnosis_long_chain_smoke.go

cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
yarn smoke:alert-ai-diagnosis
yarn smoke:alert-ai-diagnosis-drawer
npm run typecheck
```

Expected:

- Go tests PASS.
- Wire compile check PASS.
- Long-chain smoke prints `LONG_CHAIN_SMOKE_PASSED`.
- Frontend smoke scripts PASS.
- Typecheck PASS or exact unrelated existing failures are documented.

- [ ] **Step 3: Record uncovered nodes**

Append a short section to `memory/2026-06-19.md`:

```md
### Alert AI RCA V2 Longest-Chain Smoke

- Passed: frontend request builder -> AIOps handler -> AlertAlarmRootCauseV2App stub -> RCA normalized evidence -> uploaded log evidence -> diagnosis report -> drawer grouping.
- Not covered: authenticated live browser click, DB-backed provider config, real Loki retrieval, private knowledge/RAG, device command execution, audit persistence.
```

- [ ] **Step 4: Commit smoke evidence**

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
git add scripts/aiops_alert_diagnosis_long_chain_smoke.go
git commit -m "test(aiops): add alert diagnosis RCA V2 smoke"

cd /Users/huangliang/project/OneOPS-ALL
git -C docs status --short
```

If `memory/2026-06-19.md` is not in a git repo, leave it uncommitted as workspace memory.

## Final Verification

Run all scoped verification commands:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/aiops/... -count=1
go test ./cmd -run '^$' -count=1
go run ./scripts/aiops_alert_diagnosis_long_chain_smoke.go

cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
yarn smoke:alert-ai-diagnosis
yarn smoke:alert-ai-diagnosis-drawer
npm run typecheck
```

Final response must include:

- 当前基于的数据模型: `AlertDiagnosisReq`, `AlertAlarmAnalyzeRootCauseV2Req`, `MonitoringRootCauseV2AnalyzeResp`, `RCAAnalysisResult`, `NormalizedEvidence`, `AIOpsDiagnosisReport`.
- 完成了什么: backend RCA V2 integration, evidence conversion, frontend evidence grouping, smoke.
- 验证结果: exact commands and pass/fail status.
- 当前风险/缺口: list uncovered nodes.
- 下一步: live browser/authenticated smoke or private knowledge/RAG, depending on user priority.

## Self-Review

- Spec coverage: covered request mapping, RCA conversion, evidence conversion, failure degradation, show-only safety preservation, frontend read-only display, longest-chain smoke, and uncovered nodes.
- Completeness scan: no `TBD`, no undefined future work instructions, no empty edge-case language.
- Type consistency: uses existing `AlertDiagnosisReq`, `AlertAlarmAnalyzeRootCauseV2Req`, `MonitoringRootCauseV2AnalyzeResp`, `RCAAnalysisResult`, `NormalizedEvidence`, and `AIOpsDiagnosisReport` names.
