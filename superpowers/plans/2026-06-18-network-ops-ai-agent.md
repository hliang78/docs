# Network Operations AI Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an alert-detail "AI analysis" MVP that uses local Ollama, real log evidence, existing OneOPS AIOps/RCA patterns, and safe `show` command suggestions to produce an evidence-cited diagnosis report.

**Architecture:** Extend the existing `app/aiops` backend instead of creating a parallel service. The first backend slice adds report DTOs, log evidence parsing, show-command guarding, and a diagnosis endpoint; the frontend slice adds an alert-row AI analysis action and a read-only diagnosis drawer. The MVP does not execute show commands.

**Tech Stack:** Go, Gin, existing OneOPS `app/aiops` and `app/llm` modules, Vue 3, TypeScript, Ant Design Vue, existing `requestEnvelope` helper, local Ollama through the existing LLM provider registry.

---

## File Structure

Backend files:

- Create: `OneOPS/app/aiops/dto/diagnosis.go`
  - Owns alert-diagnosis request, report, evidence, citation, and validation DTOs.
- Create: `OneOPS/app/aiops/dto/diagnosis_test.go`
  - Tests report validation and request validation.
- Create: `OneOPS/app/aiops/service/impl/log_evidence.go`
  - Parses staged real log text into normalized evidence with source line references.
- Create: `OneOPS/app/aiops/service/impl/log_evidence_test.go`
  - Tests timestamp/device/interface extraction and source line preservation.
- Create: `OneOPS/app/aiops/service/impl/show_guard.go`
  - Validates suggested `show` commands and rejects side-effect commands.
- Create: `OneOPS/app/aiops/service/impl/show_guard_test.go`
  - Tests allowed and blocked command patterns.
- Create: `OneOPS/app/aiops/service/impl/diagnosis_generator.go`
  - Builds the local-Ollama prompt, calls the existing LLM service, parses strict JSON diagnosis reports, and validates them.
- Create: `OneOPS/app/aiops/service/impl/diagnosis_generator_test.go`
  - Tests strict JSON parsing, invalid JSON rejection, and prompt constraints.
- Modify: `OneOPS/app/aiops/service/service.go`
  - Adds `AlertDiagnosisGenerator` service interface.
- Modify: `OneOPS/app/aiops/api/aiops.go`
  - Adds `AnalyzeAlertDiagnosis` API handler.
- Modify: `OneOPS/app/aiops/api/aiops_test.go`
  - Tests the new handler with a fake diagnosis generator.
- Modify: `OneOPS/app/aiops/router/aiops.go`
  - Adds `POST /api/v1/aiops/alerts:diagnose`.
- Modify: `OneOPS/app/aiops/service/impl/module.go`
  - Wires the new diagnosis generator into the existing Wire provider set.

Frontend files:

- Modify: `OneOPS-UI/src/api/aiops.ts`
  - Adds `diagnoseAIOpsAlertReq`.
- Modify: `OneOPS-UI/src/typings/aiops.ts`
  - Adds alert diagnosis request/report types.
- Create: `OneOPS-UI/src/views/alert/AlarmAIDiagnosisDrawer.vue`
  - Read-only diagnosis report drawer.
- Create: `OneOPS-UI/src/views/alert/alarm_ai_diagnosis.ts`
  - Builds an AI diagnosis request from an alert row.
- Modify: `OneOPS-UI/src/views/alert/Alarm.vue`
  - Adds row action and drawer integration.
- Create: `OneOPS-UI/scripts/alert-ai-diagnosis-smoke.ts`
  - Tests the request builder and report guards.
- Modify: `OneOPS-UI/package.json`
  - Adds `smoke:alert-ai-diagnosis`.

Validation commands:

- `cd OneOPS && go test ./app/aiops/...`
- `cd OneOPS-UI && yarn smoke:alert-ai-diagnosis`
- `cd OneOPS-UI && yarn typecheck`

Commit/checkpoint convention:

```bash
if test -d .git; then
  git status --short
  git add <changed-files>
  git commit -m "<message>"
else
  echo "No git repository in /Users/huangliang/project/OneOPS-ALL; record checkpoint in final response."
fi
```

---

### Task 1: Backend Diagnosis DTO And Validation

**Files:**

- Create: `OneOPS/app/aiops/dto/diagnosis.go`
- Create: `OneOPS/app/aiops/dto/diagnosis_test.go`

- [ ] **Step 1: Write the failing DTO validation tests**

Create `OneOPS/app/aiops/dto/diagnosis_test.go`:

```go
package dto

import "testing"

func TestValidateAlertDiagnosisReqRequiresAlertID(t *testing.T) {
	req := AlertDiagnosisReq{
		TenantID:   "TENANT-A",
		ObservedAt: "2026-06-18T10:00:00Z",
		Target:     ObjectRef{Type: TargetTypeDevice, ID: "SW-001"},
	}
	if err := ValidateAlertDiagnosisReq(req); err == nil {
		t.Fatalf("expected alert_id validation error")
	}
}

func TestValidateDiagnosisReportRequiresCitedFacts(t *testing.T) {
	report := ValidDiagnosisReportForTest()
	report.Facts[0].Citations = nil
	if err := ValidateDiagnosisReport(report); err == nil {
		t.Fatalf("expected missing citation validation error")
	}
}

func TestValidateDiagnosisReportAcceptsSafeShowSuggestion(t *testing.T) {
	report := ValidDiagnosisReportForTest()
	if err := ValidateDiagnosisReport(report); err != nil {
		t.Fatalf("expected valid report, got %v", err)
	}
}

func ValidDiagnosisReportForTest() DiagnosisReport {
	return DiagnosisReport{
		ReportID: "report-001",
		AlertID:  "alert-001",
		Status:   DiagnosisStatusCompleted,
		Summary:  "Gi1/0/24 多次 down/up。",
		Facts: []DiagnosisStatement{{
			Text:      "日志显示 Gi1/0/24 多次 link down/up。",
			Citations: []string{"uploaded_log:network.log:10-12"},
		}},
		RootCauseCandidates: []DiagnosisCandidate{{
			Candidate:  "物理链路或光模块异常",
			Source:     "logs",
			Confidence: "medium",
			Evidence:   []string{"log-1"},
			Why:        "日志呈现接口 flap 模式。",
		}},
		TroubleshootingSteps: []DiagnosisStep{{
			Risk:             DiagnosisRiskReadOnly,
			Action:           "检查接口计数器和物理状态",
			SuggestedShow:    "show interface Gi1/0/24",
			RequiresApproval: true,
		}},
		Recommendations: []DiagnosisRecommendation{{
			Risk: DiagnosisRiskManualReview,
			Text: "若 CRC 持续增长，建议人工检查光模块和尾纤。",
		}},
		MissingEvidence: []string{"缺少对端设备日志"},
		Citations: []DiagnosisCitation{{
			ID:     "log-1",
			Type:   "log",
			Source: "uploaded_log",
			Ref:    "network.log:10-12",
		}},
	}
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
cd OneOPS && go test ./app/aiops/dto -run 'TestValidate(AlertDiagnosisReq|DiagnosisReport)' -v
```

Expected: FAIL because `AlertDiagnosisReq`, `DiagnosisReport`, and validation functions do not exist.

- [ ] **Step 3: Add diagnosis DTOs and validators**

Create `OneOPS/app/aiops/dto/diagnosis.go`:

```go
package dto

import (
	"fmt"
	"strings"
)

const (
	DiagnosisStatusCompleted = "completed"
	DiagnosisStatusPartial   = "partial"
	DiagnosisStatusFailed    = "failed"

	DiagnosisRiskReadOnly     = "read_only"
	DiagnosisRiskManualReview = "manual_review"
)

type DiagnosisTimeWindow struct {
	From string `json:"from,omitempty"`
	To   string `json:"to,omitempty"`
}

type AlertDiagnosisOptions struct {
	IncludeLogs      bool `json:"include_logs"`
	IncludeRCA       bool `json:"include_rca"`
	IncludeKnowledge bool `json:"include_knowledge"`
	AllowShowPlan    bool `json:"allow_show_plan"`
}

type AlertDiagnosisReq struct {
	RequestID  string                `json:"request_id,omitempty"`
	AlertID    string                `json:"alert_id"`
	TenantID   string                `json:"tenant_id"`
	ObservedAt string                `json:"observed_at"`
	Target     ObjectRef             `json:"target"`
	Question   string                `json:"question,omitempty"`
	TimeWindow DiagnosisTimeWindow   `json:"time_window,omitempty"`
	Options    AlertDiagnosisOptions `json:"options"`
	Metadata   map[string]string     `json:"metadata,omitempty"`
}

type NormalizedEvidence struct {
	ID         string            `json:"id"`
	Kind       string            `json:"kind"`
	Source     string            `json:"source"`
	ObservedAt string            `json:"observed_at,omitempty"`
	DeviceRef  string            `json:"device_ref,omitempty"`
	Summary    string            `json:"summary"`
	RawRef     string            `json:"raw_ref,omitempty"`
	Confidence int               `json:"confidence,omitempty"`
	Attributes map[string]string `json:"attributes,omitempty"`
}

type DiagnosisStatement struct {
	Text      string   `json:"text"`
	Citations []string `json:"citations"`
}

type DiagnosisCandidate struct {
	Candidate  string   `json:"candidate"`
	Source     string   `json:"source"`
	Confidence string   `json:"confidence"`
	Evidence   []string `json:"evidence"`
	Why        string   `json:"why"`
}

type DiagnosisStep struct {
	Risk             string `json:"risk"`
	Action           string `json:"action"`
	SuggestedShow    string `json:"suggested_show,omitempty"`
	RequiresApproval bool   `json:"requires_approval"`
}

type DiagnosisRecommendation struct {
	Risk string `json:"risk"`
	Text string `json:"text"`
}

type DiagnosisCitation struct {
	ID     string `json:"id"`
	Type   string `json:"type"`
	Source string `json:"source"`
	Ref    string `json:"ref"`
}

type DiagnosisReport struct {
	ReportID              string                    `json:"report_id,omitempty"`
	AlertID               string                    `json:"alert_id"`
	Status                string                    `json:"status"`
	Summary               string                    `json:"summary"`
	Facts                 []DiagnosisStatement      `json:"facts"`
	RootCauseCandidates   []DiagnosisCandidate      `json:"root_cause_candidates,omitempty"`
	TroubleshootingSteps  []DiagnosisStep           `json:"troubleshooting_steps,omitempty"`
	Recommendations       []DiagnosisRecommendation `json:"recommendations,omitempty"`
	MissingEvidence        []string                  `json:"missing_evidence,omitempty"`
	Citations              []DiagnosisCitation       `json:"citations"`
}

type AlertDiagnosisResp struct {
	Request  AlertDiagnosisReq `json:"request"`
	Evidence []NormalizedEvidence `json:"evidence"`
	Report   DiagnosisReport   `json:"report"`
}

func ValidateAlertDiagnosisReq(req AlertDiagnosisReq) error {
	if strings.TrimSpace(req.AlertID) == "" {
		return fmt.Errorf("alert_id is required")
	}
	if strings.TrimSpace(req.TenantID) == "" {
		return fmt.Errorf("tenant_id is required")
	}
	if strings.TrimSpace(req.ObservedAt) == "" {
		return fmt.Errorf("observed_at is required")
	}
	if err := ValidateObjectRef(req.Target, "target"); err != nil {
		return err
	}
	if strings.TrimSpace(req.Target.Type) != TargetTypeDevice {
		return fmt.Errorf("target.type %q is not supported in aiops diagnosis mvp", req.Target.Type)
	}
	return nil
}

func ValidateDiagnosisReport(report DiagnosisReport) error {
	if strings.TrimSpace(report.AlertID) == "" {
		return fmt.Errorf("report.alert_id is required")
	}
	switch strings.TrimSpace(report.Status) {
	case DiagnosisStatusCompleted, DiagnosisStatusPartial, DiagnosisStatusFailed:
	default:
		return fmt.Errorf("report.status %q is not supported", report.Status)
	}
	if strings.TrimSpace(report.Summary) == "" {
		return fmt.Errorf("report.summary is required")
	}
	if len(report.Facts) == 0 {
		return fmt.Errorf("report.facts is required")
	}
	for index, fact := range report.Facts {
		if strings.TrimSpace(fact.Text) == "" {
			return fmt.Errorf("report.facts[%d].text is required", index)
		}
		if len(normalizedStrings(fact.Citations)) == 0 {
			return fmt.Errorf("report.facts[%d].citations is required", index)
		}
	}
	for index, step := range report.TroubleshootingSteps {
		if strings.TrimSpace(step.Action) == "" {
			return fmt.Errorf("report.troubleshooting_steps[%d].action is required", index)
		}
		switch strings.TrimSpace(step.Risk) {
		case DiagnosisRiskReadOnly, DiagnosisRiskManualReview:
		default:
			return fmt.Errorf("report.troubleshooting_steps[%d].risk %q is not supported", index, step.Risk)
		}
	}
	if len(report.Citations) == 0 {
		return fmt.Errorf("report.citations is required")
	}
	for index, citation := range report.Citations {
		if strings.TrimSpace(citation.ID) == "" || strings.TrimSpace(citation.Source) == "" || strings.TrimSpace(citation.Ref) == "" {
			return fmt.Errorf("report.citations[%d] must include id, source, and ref", index)
		}
	}
	return nil
}
```

- [ ] **Step 4: Run the DTO tests**

Run:

```bash
cd OneOPS && go test ./app/aiops/dto -run 'TestValidate(AlertDiagnosisReq|DiagnosisReport)' -v
```

Expected: PASS.

- [ ] **Step 5: Checkpoint**

Run:

```bash
if test -d .git; then
  git add OneOPS/app/aiops/dto/diagnosis.go OneOPS/app/aiops/dto/diagnosis_test.go
  git commit -m "feat(aiops): add diagnosis report contract"
else
  echo "No git repository; checkpoint Task 1 complete."
fi
```

---

### Task 2: Real Log Evidence Parser

**Files:**

- Create: `OneOPS/app/aiops/service/impl/log_evidence.go`
- Create: `OneOPS/app/aiops/service/impl/log_evidence_test.go`

- [ ] **Step 1: Write failing parser tests**

Create `OneOPS/app/aiops/service/impl/log_evidence_test.go`:

```go
package impl

import (
	"strings"
	"testing"
)

func TestParseUploadedLogEvidencePreservesLineReferences(t *testing.T) {
	input := strings.Join([]string{
		"Jun 18 10:02:01 SW-001 %%LINK/3/UPDOWN: Interface Gi1/0/24, changed state to down",
		"Jun 18 10:02:08 SW-001 %%LINK/3/UPDOWN: Interface Gi1/0/24, changed state to up",
	}, "\n")
	items := ParseUploadedLogEvidence("network.log", input, UploadedLogParseOptions{DefaultObservedAt: "2026-06-18T10:00:00Z"})
	if len(items) != 2 {
		t.Fatalf("expected two evidence items, got %d", len(items))
	}
	if items[0].RawRef != "network.log:1" {
		t.Fatalf("expected line reference, got %q", items[0].RawRef)
	}
	if items[0].DeviceRef != "SW-001" {
		t.Fatalf("expected device SW-001, got %q", items[0].DeviceRef)
	}
	if got := items[0].Attributes["interface"]; got != "Gi1/0/24" {
		t.Fatalf("expected interface extraction, got %q", got)
	}
}

func TestParseUploadedLogEvidenceSkipsBlankLines(t *testing.T) {
	items := ParseUploadedLogEvidence("network.log", "\n\nmessage only\n", UploadedLogParseOptions{})
	if len(items) != 1 {
		t.Fatalf("expected one item, got %d", len(items))
	}
	if items[0].Summary != "message only" {
		t.Fatalf("unexpected summary %q", items[0].Summary)
	}
}
```

- [ ] **Step 2: Run the parser tests to verify failure**

Run:

```bash
cd OneOPS && go test ./app/aiops/service/impl -run TestParseUploadedLogEvidence -v
```

Expected: FAIL because parser symbols do not exist.

- [ ] **Step 3: Implement parser**

Create `OneOPS/app/aiops/service/impl/log_evidence.go`:

```go
package impl

import (
	"crypto/sha1"
	"fmt"
	"regexp"
	"strings"

	aiopsDTO "github.com/netxops/OneOps/app/aiops/dto"
)

type UploadedLogParseOptions struct {
	DefaultObservedAt string
}

var (
	logDevicePattern    = regexp.MustCompile(`\b([A-Za-z][A-Za-z0-9_.-]{1,63})\b`)
	logInterfacePattern = regexp.MustCompile(`(?i)\b(?:interface|if|port)\s+([A-Za-z]+[0-9][A-Za-z0-9/._:-]*)`)
)

func ParseUploadedLogEvidence(fileName string, content string, opts UploadedLogParseOptions) []aiopsDTO.NormalizedEvidence {
	source := strings.TrimSpace(fileName)
	if source == "" {
		source = "uploaded.log"
	}
	lines := strings.Split(content, "\n")
	out := make([]aiopsDTO.NormalizedEvidence, 0, len(lines))
	for index, rawLine := range lines {
		line := strings.TrimSpace(rawLine)
		if line == "" {
			continue
		}
		rawRef := fmt.Sprintf("%s:%d", source, index+1)
		attrs := map[string]string{}
		if iface := extractLogInterface(line); iface != "" {
			attrs["interface"] = iface
		}
		out = append(out, aiopsDTO.NormalizedEvidence{
			ID:         stableEvidenceID(rawRef, line),
			Kind:       "log",
			Source:     "uploaded_log",
			ObservedAt: strings.TrimSpace(opts.DefaultObservedAt),
			DeviceRef:  extractLogDevice(line),
			Summary:    line,
			RawRef:     rawRef,
			Confidence: 60,
			Attributes: attrs,
		})
	}
	return out
}

func stableEvidenceID(rawRef string, summary string) string {
	sum := sha1.Sum([]byte(rawRef + "\n" + summary))
	return fmt.Sprintf("log-%x", sum[:6])
}

func extractLogInterface(line string) string {
	matches := logInterfacePattern.FindStringSubmatch(line)
	if len(matches) == 2 {
		return strings.TrimSpace(matches[1])
	}
	return ""
}

func extractLogDevice(line string) string {
	fields := strings.Fields(line)
	for _, field := range fields {
		cleaned := strings.Trim(field, "[]:,")
		if strings.Contains(cleaned, "-") && logDevicePattern.MatchString(cleaned) {
			return cleaned
		}
	}
	return ""
}
```

- [ ] **Step 4: Run parser tests**

Run:

```bash
cd OneOPS && go test ./app/aiops/service/impl -run TestParseUploadedLogEvidence -v
```

Expected: PASS.

- [ ] **Step 5: Checkpoint**

Run:

```bash
if test -d .git; then
  git add OneOPS/app/aiops/service/impl/log_evidence.go OneOPS/app/aiops/service/impl/log_evidence_test.go
  git commit -m "feat(aiops): parse uploaded log evidence"
else
  echo "No git repository; checkpoint Task 2 complete."
fi
```

---

### Task 3: Show Command Guard

**Files:**

- Create: `OneOPS/app/aiops/service/impl/show_guard.go`
- Create: `OneOPS/app/aiops/service/impl/show_guard_test.go`

- [ ] **Step 1: Write failing show guard tests**

Create `OneOPS/app/aiops/service/impl/show_guard_test.go`:

```go
package impl

import "testing"

func TestValidateShowCommandAllowsOnlyShow(t *testing.T) {
	if err := ValidateShowCommand("show interface Gi1/0/24"); err != nil {
		t.Fatalf("expected show command to pass, got %v", err)
	}
}

func TestValidateShowCommandRejectsSideEffects(t *testing.T) {
	blocked := []string{
		"configure terminal",
		"clear counters",
		"reload",
		"copy running-config startup-config",
		"show interface Gi1/0/24 ; reload",
	}
	for _, cmd := range blocked {
		if err := ValidateShowCommand(cmd); err == nil {
			t.Fatalf("expected command %q to be blocked", cmd)
		}
	}
}
```

- [ ] **Step 2: Run show guard tests to verify failure**

Run:

```bash
cd OneOPS && go test ./app/aiops/service/impl -run TestValidateShowCommand -v
```

Expected: FAIL because `ValidateShowCommand` does not exist.

- [ ] **Step 3: Implement the guard**

Create `OneOPS/app/aiops/service/impl/show_guard.go`:

```go
package impl

import (
	"fmt"
	"strings"
)

var blockedCommandTokens = []string{
	"configure",
	"conf t",
	"set ",
	"delete",
	"clear",
	"reload",
	"reset",
	"write",
	"copy",
	"commit",
	"save",
	";",
	"&&",
	"||",
	"| bash",
	"| sh",
}

func ValidateShowCommand(command string) error {
	normalized := strings.TrimSpace(strings.ToLower(command))
	if normalized == "" {
		return fmt.Errorf("show command is required")
	}
	if !strings.HasPrefix(normalized, "show ") {
		return fmt.Errorf("only show commands are allowed")
	}
	for _, token := range blockedCommandTokens {
		if strings.Contains(normalized, token) {
			return fmt.Errorf("command contains blocked token %q", token)
		}
	}
	return nil
}
```

- [ ] **Step 4: Run show guard tests**

Run:

```bash
cd OneOPS && go test ./app/aiops/service/impl -run TestValidateShowCommand -v
```

Expected: PASS.

- [ ] **Step 5: Checkpoint**

Run:

```bash
if test -d .git; then
  git add OneOPS/app/aiops/service/impl/show_guard.go OneOPS/app/aiops/service/impl/show_guard_test.go
  git commit -m "feat(aiops): guard show command suggestions"
else
  echo "No git repository; checkpoint Task 3 complete."
fi
```

---

### Task 4: Local Ollama Diagnosis Generator

**Files:**

- Create: `OneOPS/app/aiops/service/impl/diagnosis_generator.go`
- Create: `OneOPS/app/aiops/service/impl/diagnosis_generator_test.go`
- Modify: `OneOPS/app/aiops/service/service.go`
- Modify: `OneOPS/app/aiops/service/impl/module.go`

- [ ] **Step 1: Add service interface**

Modify `OneOPS/app/aiops/service/service.go` by appending:

```go
type AlertDiagnosisGenerator interface {
	GenerateAlertDiagnosis(ctx context.Context, req AlertDiagnosisGenerateReq) (*dto.AlertDiagnosisResp, error)
}

type AlertDiagnosisGenerateReq struct {
	Request  dto.AlertDiagnosisReq
	Evidence []dto.NormalizedEvidence
	RCA      dto.RCAAnalysisResult
}
```

- [ ] **Step 2: Write failing generator tests**

Create `OneOPS/app/aiops/service/impl/diagnosis_generator_test.go`:

```go
package impl

import (
	"context"
	"strings"
	"testing"

	aiopsDTO "github.com/netxops/OneOps/app/aiops/dto"
	aiopsService "github.com/netxops/OneOps/app/aiops/service"
	llmDTO "github.com/netxops/OneOps/app/llm/dto"
)

func TestDiagnosisGeneratorRejectsNonJSON(t *testing.T) {
	gen := NewLLMDiagnosisGenerator(&fakeLLMChatService{resp: &llmDTO.ChatCompletionResponse{Content: "not json"}}, "", "")
	_, err := gen.GenerateAlertDiagnosis(context.Background(), validDiagnosisGenerateReq())
	if err == nil {
		t.Fatalf("expected non-json response to fail")
	}
}

func TestDiagnosisGeneratorAcceptsStrictReportJSON(t *testing.T) {
	gen := NewLLMDiagnosisGenerator(&fakeLLMChatService{resp: &llmDTO.ChatCompletionResponse{Content: `{
		"alert_id":"alert-001",
		"status":"completed",
		"summary":"Gi1/0/24 多次 down/up。",
		"facts":[{"text":"日志显示接口 flap。","citations":["uploaded_log:network.log:1"]}],
		"root_cause_candidates":[{"candidate":"物理链路异常","source":"logs","confidence":"medium","evidence":["log-1"],"why":"日志出现 down/up。"}],
		"troubleshooting_steps":[{"risk":"read_only","action":"检查接口状态","suggested_show":"show interface Gi1/0/24","requires_approval":true}],
		"recommendations":[{"risk":"manual_review","text":"人工检查光模块和尾纤。"}],
		"missing_evidence":["缺少对端日志"],
		"citations":[{"id":"log-1","type":"log","source":"uploaded_log","ref":"network.log:1"}]
	}`}}, "", "")
	resp, err := gen.GenerateAlertDiagnosis(context.Background(), validDiagnosisGenerateReq())
	if err != nil {
		t.Fatalf("expected valid diagnosis, got %v", err)
	}
	if resp.Report.AlertID != "alert-001" {
		t.Fatalf("unexpected alert id %q", resp.Report.AlertID)
	}
}

func TestDiagnosisGeneratorPromptContainsSafetyRules(t *testing.T) {
	fake := &fakeLLMChatService{resp: &llmDTO.ChatCompletionResponse{Content: `{
		"alert_id":"alert-001",
		"status":"completed",
		"summary":"summary",
		"facts":[{"text":"fact","citations":["uploaded_log:network.log:1"]}],
		"citations":[{"id":"log-1","type":"log","source":"uploaded_log","ref":"network.log:1"}]
	}`}}
	gen := NewLLMDiagnosisGenerator(fake, "local-ollama", "qwen2.5")
	_, err := gen.GenerateAlertDiagnosis(context.Background(), validDiagnosisGenerateReq())
	if err != nil {
		t.Fatalf("expected valid diagnosis, got %v", err)
	}
	if fake.lastChatReq == nil {
		t.Fatalf("expected chat request")
	}
	system := fake.lastChatReq.Messages[0].Content
	if !strings.Contains(system, "不能输出配置命令") || !strings.Contains(system, "必须区分事实、推断、建议和缺口") {
		t.Fatalf("system prompt missing safety rules: %s", system)
	}
}

func validDiagnosisGenerateReq() aiopsService.AlertDiagnosisGenerateReq {
	return aiopsService.AlertDiagnosisGenerateReq{
		Request: aiopsDTO.AlertDiagnosisReq{
			AlertID:    "alert-001",
			TenantID:   "TENANT-A",
			ObservedAt: "2026-06-18T10:00:00Z",
			Target:     aiopsDTO.ObjectRef{Type: aiopsDTO.TargetTypeDevice, ID: "SW-001"},
		},
		Evidence: []aiopsDTO.NormalizedEvidence{{
			ID:      "log-1",
			Kind:    "log",
			Source:  "uploaded_log",
			Summary: "Gi1/0/24 changed state to down",
			RawRef:  "network.log:1",
		}},
		RCA: aiopsDTO.RCAAnalysisResult{Conclusion: "rca completed"},
	}
}
```

- [ ] **Step 3: Run generator tests to verify failure**

Run:

```bash
cd OneOPS && go test ./app/aiops/service/impl -run TestDiagnosisGenerator -v
```

Expected: FAIL because the generator does not exist.

- [ ] **Step 4: Implement generator**

Create `OneOPS/app/aiops/service/impl/diagnosis_generator.go`:

```go
package impl

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	aiopsDTO "github.com/netxops/OneOps/app/aiops/dto"
	aiopsService "github.com/netxops/OneOps/app/aiops/service"
	llmDTO "github.com/netxops/OneOps/app/llm/dto"
)

var _ aiopsService.AlertDiagnosisGenerator = (*LLMDiagnosisGenerator)(nil)

type LLMDiagnosisGenerator struct {
	LLMSrv    aiopsLLMChatService
	Provider  string
	Model     string
	MaxTokens *int
}

func NewLLMDiagnosisGenerator(llmSrv aiopsLLMChatService, provider string, model string) *LLMDiagnosisGenerator {
	return &LLMDiagnosisGenerator{
		LLMSrv:   llmSrv,
		Provider: strings.TrimSpace(provider),
		Model:    strings.TrimSpace(model),
	}
}

func (g *LLMDiagnosisGenerator) GenerateAlertDiagnosis(ctx context.Context, req aiopsService.AlertDiagnosisGenerateReq) (*aiopsDTO.AlertDiagnosisResp, error) {
	if g == nil || g.LLMSrv == nil {
		return nil, fmt.Errorf("aiops diagnosis generator is not configured")
	}
	if err := aiopsDTO.ValidateAlertDiagnosisReq(req.Request); err != nil {
		return nil, err
	}
	systemPrompt := aiopsDiagnosisSystemPrompt()
	userPrompt, err := buildDiagnosisUserPrompt(req)
	if err != nil {
		return nil, err
	}
	resp, err := g.LLMSrv.Chat(ctx, &llmDTO.ChatCompletionRequest{
		Provider:  strings.TrimSpace(g.Provider),
		Model:     strings.TrimSpace(g.Model),
		MaxTokens: g.MaxTokens,
		Messages: []llmDTO.ChatMessage{
			{Role: "system", Content: systemPrompt},
			{Role: "user", Content: userPrompt},
		},
		Metadata: map[string]string{
			"module":   "aiops",
			"scene":    "alert_diagnosis",
			"alert_id": strings.TrimSpace(req.Request.AlertID),
		},
	})
	if err != nil {
		return nil, err
	}
	if resp == nil || strings.TrimSpace(resp.Content) == "" {
		return nil, fmt.Errorf("aiops diagnosis generator received empty response")
	}
	var report aiopsDTO.DiagnosisReport
	if err := json.Unmarshal([]byte(strings.TrimSpace(resp.Content)), &report); err != nil {
		return nil, fmt.Errorf("parse aiops diagnosis report json: %w", err)
	}
	if strings.TrimSpace(report.AlertID) == "" {
		report.AlertID = req.Request.AlertID
	}
	if err := aiopsDTO.ValidateDiagnosisReport(report); err != nil {
		return nil, err
	}
	for _, step := range report.TroubleshootingSteps {
		if strings.TrimSpace(step.SuggestedShow) != "" {
			if err := ValidateShowCommand(step.SuggestedShow); err != nil {
				return nil, fmt.Errorf("validate suggested_show %q: %w", step.SuggestedShow, err)
			}
		}
	}
	return &aiopsDTO.AlertDiagnosisResp{
		Request:  req.Request,
		Evidence: append([]aiopsDTO.NormalizedEvidence{}, req.Evidence...),
		Report:   report,
	}, nil
}

func buildDiagnosisUserPrompt(req aiopsService.AlertDiagnosisGenerateReq) (string, error) {
	payload := struct {
		Request  aiopsDTO.AlertDiagnosisReq    `json:"request"`
		Evidence []aiopsDTO.NormalizedEvidence `json:"evidence"`
		RCA      aiopsDTO.RCAAnalysisResult    `json:"rca"`
	}{
		Request:  req.Request,
		Evidence: req.Evidence,
		RCA:      req.RCA,
	}
	body, err := json.MarshalIndent(payload, "", "  ")
	if err != nil {
		return "", err
	}
	return "请基于以下 OneOPS 告警、日志证据和 RCA 输入生成诊断报告，只能输出 JSON。\n\n" + string(body), nil
}

func aiopsDiagnosisSystemPrompt() string {
	return strings.TrimSpace(`你是 OneOPS 网络运维诊断助手。
你只能基于平台提供的 request、evidence、rca 输出诊断报告。
不能输出配置命令、修复命令、clear/reload/reset/write/copy/commit/save 等有副作用命令。
如果需要设备命令，只能建议 show 开头的只读命令，并且 requires_approval 必须为 true。
必须区分事实、推断、建议和缺口；事实必须带 citations。
禁止编造日志、拓扑、指标、show 输出或执行结果。
禁止输出 Markdown、代码块、解释性前后缀。
必须直接输出一个 JSON 对象，字段包括：
{
  "report_id": "可选字符串",
  "alert_id": "告警 ID",
  "status": "completed|partial|failed",
  "summary": "一句话摘要",
  "facts": [{"text": "事实", "citations": ["source:ref"]}],
  "root_cause_candidates": [{"candidate": "候选", "source": "logs|rca|knowledge", "confidence": "low|medium|high", "evidence": ["证据 ID"], "why": "依据"}],
  "troubleshooting_steps": [{"risk": "read_only|manual_review", "action": "步骤", "suggested_show": "show ...", "requires_approval": true}],
  "recommendations": [{"risk": "manual_review", "text": "建议"}],
  "missing_evidence": ["缺失证据"],
  "citations": [{"id": "证据 ID", "type": "log|rca|knowledge|show", "source": "来源", "ref": "引用"}]
}`)
}
```

- [ ] **Step 5: Run generator tests**

Run:

```bash
cd OneOPS && go test ./app/aiops/service/impl -run TestDiagnosisGenerator -v
```

Expected: PASS.

- [ ] **Step 6: Wire the generator**

Modify `OneOPS/app/aiops/service/impl/module.go` by adding:

```go
func ProvideAIOpsDiagnosisGenerator(llmSrv llmService.ILLMService) *LLMDiagnosisGenerator {
	return NewLLMDiagnosisGenerator(llmSrv, "", "")
}
```

Add these entries to `AIOpsModuleSet` after `ProvideAIOpsLLMPlanGenerator`:

```go
ProvideAIOpsDiagnosisGenerator,
wire.Bind(new(aiopsService.AlertDiagnosisGenerator), new(*LLMDiagnosisGenerator)),
```

- [ ] **Step 7: Run AIOps service tests**

Run:

```bash
cd OneOPS && go test ./app/aiops/service/...
```

Expected: PASS.

- [ ] **Step 8: Checkpoint**

Run:

```bash
if test -d .git; then
  git add OneOPS/app/aiops/service/service.go OneOPS/app/aiops/service/impl/diagnosis_generator.go OneOPS/app/aiops/service/impl/diagnosis_generator_test.go OneOPS/app/aiops/service/impl/module.go
  git commit -m "feat(aiops): generate alert diagnosis reports"
else
  echo "No git repository; checkpoint Task 4 complete."
fi
```

---

### Task 5: Backend API Endpoint

**Files:**

- Modify: `OneOPS/app/aiops/api/aiops.go`
- Modify: `OneOPS/app/aiops/api/aiops_test.go`
- Modify: `OneOPS/app/aiops/router/aiops.go`

- [ ] **Step 1: Add fake generator and handler tests**

Append to `OneOPS/app/aiops/api/aiops_test.go`:

```go
type fakeAlertDiagnosisGenerator struct {
	resp *aiopsDTO.AlertDiagnosisResp
	err  error
}

func (f *fakeAlertDiagnosisGenerator) GenerateAlertDiagnosis(context.Context, aiopsService.AlertDiagnosisGenerateReq) (*aiopsDTO.AlertDiagnosisResp, error) {
	return f.resp, f.err
}

func TestAIOpsAPI_AnalyzeAlertDiagnosis(t *testing.T) {
	report := aiopsDTO.DiagnosisReport{
		AlertID: "alert-001",
		Status:  aiopsDTO.DiagnosisStatusCompleted,
		Summary: "Gi1/0/24 多次 down/up。",
		Facts: []aiopsDTO.DiagnosisStatement{{
			Text:      "日志显示接口 flap。",
			Citations: []string{"uploaded_log:network.log:1"},
		}},
		Citations: []aiopsDTO.DiagnosisCitation{{
			ID:     "log-1",
			Type:   "log",
			Source: "uploaded_log",
			Ref:    "network.log:1",
		}},
	}
	api := newAIOpsAPIForTest()
	api.AlertDiagnosisGenerator = &fakeAlertDiagnosisGenerator{
		resp: &aiopsDTO.AlertDiagnosisResp{
			Request: aiopsDTO.AlertDiagnosisReq{
				AlertID:    "alert-001",
				TenantID:   "TENANT-A",
				ObservedAt: "2026-06-18T10:00:00Z",
				Target:     aiopsDTO.ObjectRef{Type: aiopsDTO.TargetTypeDevice, ID: "SW-001"},
			},
			Report: report,
		},
	}
	body := `{"alert_id":"alert-001","tenant_id":"TENANT-A","observed_at":"2026-06-18T10:00:00Z","target":{"type":"device","id":"SW-001"},"options":{"include_logs":true,"include_rca":true,"allow_show_plan":true}}`
	ctx, recorder := newAIOpsTestContext(t, http.MethodPost, "/aiops/alerts:diagnose", body)

	api.AnalyzeAlertDiagnosis(ctx)

	var resp struct {
		Code int                        `json:"code"`
		Msg  string                     `json:"msg"`
		Data aiopsDTO.AlertDiagnosisResp `json:"data"`
	}
	if err := json.Unmarshal(recorder.Body.Bytes(), &resp); err != nil {
		t.Fatalf("unmarshal response failed: %v body=%s", err, recorder.Body.String())
	}
	if resp.Code != 0 {
		t.Fatalf("expected code=0, got=%d msg=%s", resp.Code, resp.Msg)
	}
	if resp.Data.Report.AlertID != "alert-001" {
		t.Fatalf("unexpected report %+v", resp.Data.Report)
	}
}
```

- [ ] **Step 2: Run handler test to verify failure**

Run:

```bash
cd OneOPS && go test ./app/aiops/api -run TestAIOpsAPI_AnalyzeAlertDiagnosis -v
```

Expected: FAIL because `AlertDiagnosisGenerator` field and handler do not exist.

- [ ] **Step 3: Add handler field and method**

Modify `AIOpsAPI` in `OneOPS/app/aiops/api/aiops.go` to add:

```go
AlertDiagnosisGenerator aiopsService.AlertDiagnosisGenerator
```

Add this method to `OneOPS/app/aiops/api/aiops.go`:

```go
func (a *AIOpsAPI) AnalyzeAlertDiagnosis(ctx *gin.Context) {
	if a == nil || a.AlertDiagnosisGenerator == nil {
		response.FailWithMsg("aiops alert diagnosis generator 未初始化", ctx)
		return
	}
	var req aiopsDTO.AlertDiagnosisReq
	if err := ctx.ShouldBindJSON(&req); err != nil {
		response.FailWithMsg("请求参数错误: "+err.Error(), ctx)
		return
	}
	if err := aiopsDTO.ValidateAlertDiagnosisReq(req); err != nil {
		response.FailWithMsg(err.Error(), ctx)
		return
	}
	var evidence []aiopsDTO.NormalizedEvidence
	if rawLog := strings.TrimSpace(req.Metadata["uploaded_log_sample"]); rawLog != "" {
		evidence = impl.ParseUploadedLogEvidence("uploaded-log-sample.log", rawLog, impl.UploadedLogParseOptions{
			DefaultObservedAt: strings.TrimSpace(req.ObservedAt),
		})
	}
	resp, err := a.AlertDiagnosisGenerator.GenerateAlertDiagnosis(ctx.Request.Context(), aiopsService.AlertDiagnosisGenerateReq{
		Request:  req,
		Evidence: evidence,
		RCA:      aiopsDTO.RCAAnalysisResult{Conclusion: "rca_not_connected_in_alert_diagnosis_mvp"},
	})
	if err != nil {
		if a.Logger != nil {
			a.Logger.Error("AIOps alert diagnosis failed", zap.Error(err))
		}
		response.FailWithMsg(err.Error(), ctx)
		return
	}
	response.OkWithData(resp, ctx)
}
```

Also add import:

```go
impl "github.com/netxops/OneOps/app/aiops/service/impl"
```

- [ ] **Step 4: Add route**

Modify `OneOPS/app/aiops/router/aiops.go`:

```go
group.POST("alerts:diagnose", aiopsAPI.AnalyzeAlertDiagnosis)
```

Place it near the existing `incidents:analyze` route.

- [ ] **Step 5: Run handler test**

Run:

```bash
cd OneOPS && go test ./app/aiops/api -run TestAIOpsAPI_AnalyzeAlertDiagnosis -v
```

Expected: PASS.

- [ ] **Step 6: Run backend AIOps tests**

Run:

```bash
cd OneOPS && go test ./app/aiops/...
```

Expected: PASS.

- [ ] **Step 7: Checkpoint**

Run:

```bash
if test -d .git; then
  git add OneOPS/app/aiops/api/aiops.go OneOPS/app/aiops/api/aiops_test.go OneOPS/app/aiops/router/aiops.go
  git commit -m "feat(aiops): expose alert diagnosis endpoint"
else
  echo "No git repository; checkpoint Task 5 complete."
fi
```

---

### Task 6: Frontend API Types And Request Builder

**Files:**

- Modify: `OneOPS-UI/src/typings/aiops.ts`
- Modify: `OneOPS-UI/src/api/aiops.ts`
- Create: `OneOPS-UI/src/views/alert/alarm_ai_diagnosis.ts`
- Create: `OneOPS-UI/scripts/alert-ai-diagnosis-smoke.ts`
- Modify: `OneOPS-UI/package.json`

- [ ] **Step 1: Add smoke test for request builder**

Create `OneOPS-UI/scripts/alert-ai-diagnosis-smoke.ts`:

```ts
import assert from 'node:assert/strict';
import { buildAlertAIDiagnosisRequest } from '../src/views/alert/alarm_ai_diagnosis';
import type { AlertAlarmResp } from '../src/typings';

function makeAlarm(overrides: Partial<AlertAlarmResp>): AlertAlarmResp {
  return {
    code: 'alert-001',
    value: 1,
    state: 'firing',
    confirmed_by: '',
    rule_code: '',
    rule: {} as AlertAlarmResp['rule'],
    datasource_code: '',
    datasource: {} as AlertAlarmResp['datasource'],
    datasource_type: 'prometheus',
    expr_snapshot: '',
    fired_at: '2026-06-18T10:00:00Z',
    confirmed_at: '',
    confirmed_before: '',
    resolved_at: '',
    summary: '接口 Gi1/0/24 flap',
    active_at: '',
    last_sent_at: '',
    valid_until: '',
    alarm_duration: 3,
    keep_firing_since: '',
    description: '',
    annotations: {},
    labels: { tenant_code: 'TENANT-A', device_code: 'SW-001' },
    sample_ts: '',
    sample_line: '',
    sample_stream: {},
    ...overrides,
  };
}

const result = buildAlertAIDiagnosisRequest(makeAlarm({}));
assert.equal(result.ok, true);
if (!result.ok) {
  throw new Error('expected valid request');
}
assert.equal(result.req.alert_id, 'alert-001');
assert.equal(result.req.tenant_id, 'TENANT-A');
assert.equal(result.req.target.id, 'SW-001');
assert.equal(result.req.options.include_logs, true);
console.log('Alert AI diagnosis smoke passed');
```

- [ ] **Step 2: Add npm script**

Modify `OneOPS-UI/package.json` scripts:

```json
"smoke:alert-ai-diagnosis": "npx esbuild scripts/alert-ai-diagnosis-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/alert-ai-diagnosis-smoke.mjs >/dev/null && node .tmp/alert-ai-diagnosis-smoke.mjs"
```

- [ ] **Step 3: Run smoke test to verify failure**

Run:

```bash
cd OneOPS-UI && yarn smoke:alert-ai-diagnosis
```

Expected: FAIL because `alarm_ai_diagnosis.ts` does not exist.

- [ ] **Step 4: Add frontend typings**

Append to `OneOPS-UI/src/typings/aiops.ts`:

```ts
export interface AIOpsDiagnosisTimeWindow {
  from?: string;
  to?: string;
}

export interface AIOpsAlertDiagnosisReq {
  request_id?: string;
  alert_id: string;
  tenant_id: string;
  observed_at: string;
  target: AIOpsObjectRef;
  question?: string;
  time_window?: AIOpsDiagnosisTimeWindow;
  options: {
    include_logs: boolean;
    include_rca: boolean;
    include_knowledge: boolean;
    allow_show_plan: boolean;
  };
  metadata?: Record<string, string>;
}

export interface AIOpsNormalizedEvidence {
  id: string;
  kind: string;
  source: string;
  observed_at?: string;
  device_ref?: string;
  summary: string;
  raw_ref?: string;
  confidence?: number;
  attributes?: Record<string, string>;
}

export interface AIOpsDiagnosisReport {
  report_id?: string;
  alert_id: string;
  status: 'completed' | 'partial' | 'failed';
  summary: string;
  facts: Array<{ text: string; citations: string[] }>;
  root_cause_candidates?: Array<{
    candidate: string;
    source: string;
    confidence: string;
    evidence: string[];
    why: string;
  }>;
  troubleshooting_steps?: Array<{
    risk: 'read_only' | 'manual_review';
    action: string;
    suggested_show?: string;
    requires_approval: boolean;
  }>;
  recommendations?: Array<{ risk: 'manual_review'; text: string }>;
  missing_evidence?: string[];
  citations: Array<{ id: string; type: string; source: string; ref: string }>;
}

export interface AIOpsAlertDiagnosisResp {
  request: AIOpsAlertDiagnosisReq;
  evidence: AIOpsNormalizedEvidence[];
  report: AIOpsDiagnosisReport;
}
```

- [ ] **Step 5: Add API wrapper**

Modify `OneOPS-UI/src/api/aiops.ts` imports to include:

```ts
AIOpsAlertDiagnosisReq,
AIOpsAlertDiagnosisResp,
```

Add:

```ts
export const diagnoseAIOpsAlertReq = async (data: AIOpsAlertDiagnosisReq) => {
  const resp = await requestEnvelope<AIOpsAlertDiagnosisResp>({
    url: '/aiops/alerts:diagnose',
    method: HTTP_POST,
    data,
    silentError: true,
  });
  return assertAIOpsEnvelope(resp, 'AIOps 告警 AI 分析');
};
```

- [ ] **Step 6: Add request builder**

Create `OneOPS-UI/src/views/alert/alarm_ai_diagnosis.ts`:

```ts
import dayjs from 'dayjs';
import type { AlertAlarmResp } from '@/typings';
import type { AIOpsAlertDiagnosisReq } from '@/typings/aiops';
import { resolveAlarmTenantCode } from './alarm_rca';

export type AlertAIDiagnosisBuildResult =
  | { ok: true; req: AIOpsAlertDiagnosisReq }
  | { ok: false; reason: 'missing_alert_id' | 'missing_tenant' | 'missing_target' | 'missing_observed_at' };

const resolveTargetDeviceCode = (record: AlertAlarmResp) => {
  const candidates = [
    record?.rca_identity?.target_id,
    record?.labels?.device_code,
    record?.labels?.deviceCode,
    record?.labels?.instance,
    record?.annotations?.device_code,
    record?.annotations?.deviceCode,
  ];
  return candidates.map(value => String(value || '').trim()).find(Boolean) || '';
};

export const buildAlertAIDiagnosisRequest = (record: AlertAlarmResp): AlertAIDiagnosisBuildResult => {
  const alertID = String(record?.code || '').trim();
  if (!alertID) {
    return { ok: false, reason: 'missing_alert_id' };
  }
  const tenantID = resolveAlarmTenantCode(record);
  if (!tenantID) {
    return { ok: false, reason: 'missing_tenant' };
  }
  const targetID = resolveTargetDeviceCode(record);
  if (!targetID) {
    return { ok: false, reason: 'missing_target' };
  }
  const observedAt = String(record?.fired_at || record?.active_at || '').trim();
  if (!observedAt) {
    return { ok: false, reason: 'missing_observed_at' };
  }
  const observed = dayjs(observedAt);
  return {
    ok: true,
    req: {
      request_id: `alert-ai-${Date.now()}`,
      alert_id: alertID,
      tenant_id: tenantID,
      observed_at: observedAt,
      target: {
        type: 'device',
        id: targetID,
        name: String(record?.labels?.device_name || record?.annotations?.device_name || targetID),
      },
      question: String(record?.summary || record?.description || '请分析该告警可能原因和排查步骤。'),
      time_window: {
        from: observed.subtract(2, 'hour').toISOString(),
        to: observed.add(30, 'minute').toISOString(),
      },
      options: {
        include_logs: true,
        include_rca: true,
        include_knowledge: true,
        allow_show_plan: true,
      },
      metadata: {
        datasource_type: String(record?.datasource_type || ''),
        rule_code: String(record?.rule_code || ''),
        summary: String(record?.summary || ''),
      },
    },
  };
};
```

- [ ] **Step 7: Run smoke test**

Run:

```bash
cd OneOPS-UI && yarn smoke:alert-ai-diagnosis
```

Expected: PASS.

- [ ] **Step 8: Checkpoint**

Run:

```bash
if test -d .git; then
  git add OneOPS-UI/src/typings/aiops.ts OneOPS-UI/src/api/aiops.ts OneOPS-UI/src/views/alert/alarm_ai_diagnosis.ts OneOPS-UI/scripts/alert-ai-diagnosis-smoke.ts OneOPS-UI/package.json
  git commit -m "feat(aiops): add alert diagnosis frontend contract"
else
  echo "No git repository; checkpoint Task 6 complete."
fi
```

---

### Task 7: Alert Diagnosis Drawer UI

**Files:**

- Create: `OneOPS-UI/src/views/alert/AlarmAIDiagnosisDrawer.vue`
- Modify: `OneOPS-UI/src/views/alert/Alarm.vue`

- [ ] **Step 1: Create drawer component**

Create `OneOPS-UI/src/views/alert/AlarmAIDiagnosisDrawer.vue`:

```vue
<template>
  <a-drawer :open="open" title="AI 分析" width="720px" placement="right" @close="$emit('close')">
    <a-spin :spinning="loading">
      <a-alert v-if="error" type="error" show-icon :message="error" style="margin-bottom: 12px" />
      <a-empty v-if="!loading && !error && !report" description="尚未生成 AI 分析" />
      <section v-if="report" class="alert-ai-diagnosis">
        <a-alert :message="report.summary" type="info" show-icon style="margin-bottom: 12px" />

        <a-card size="small" title="事实" class="alert-ai-diagnosis__card">
          <a-list :data-source="report.facts" size="small">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta :description="item.citations.join(', ')">
                  <template #title>{{ item.text }}</template>
                </a-list-item-meta>
              </a-list-item>
            </template>
          </a-list>
        </a-card>

        <a-card size="small" title="根因候选" class="alert-ai-diagnosis__card">
          <a-list :data-source="report.root_cause_candidates || []" size="small">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta :description="item.why">
                  <template #title>
                    <a-space wrap>
                      <span>{{ item.candidate }}</span>
                      <a-tag>{{ item.confidence }}</a-tag>
                    </a-space>
                  </template>
                </a-list-item-meta>
              </a-list-item>
            </template>
          </a-list>
          <a-empty v-if="!report.root_cause_candidates?.length" description="暂无候选" />
        </a-card>

        <a-card size="small" title="排查步骤" class="alert-ai-diagnosis__card">
          <a-list :data-source="report.troubleshooting_steps || []" size="small">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta>
                  <template #title>
                    <a-space wrap>
                      <span>{{ item.action }}</span>
                      <a-tag color="green">{{ item.risk }}</a-tag>
                    </a-space>
                  </template>
                  <template #description>
                    <span v-if="item.suggested_show">建议只读命令：{{ item.suggested_show }}</span>
                  </template>
                </a-list-item-meta>
              </a-list-item>
            </template>
          </a-list>
        </a-card>

        <a-card size="small" title="缺失证据" class="alert-ai-diagnosis__card">
          <a-tag v-for="item in report.missing_evidence || []" :key="item" color="orange">{{ item }}</a-tag>
          <a-empty v-if="!report.missing_evidence?.length" description="暂无缺失证据" />
        </a-card>
      </section>
    </a-spin>
  </a-drawer>
</template>

<script setup lang="ts">
import type { AIOpsDiagnosisReport } from '@/typings/aiops';

defineProps<{
  open: boolean;
  loading: boolean;
  error: string;
  report?: AIOpsDiagnosisReport | null;
}>();

defineEmits<{ close: [] }>();
</script>

<style scoped>
.alert-ai-diagnosis {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.alert-ai-diagnosis__card {
  border-radius: 6px;
}
</style>
```

- [ ] **Step 2: Integrate in Alarm.vue imports**

Add imports in `OneOPS-UI/src/views/alert/Alarm.vue`:

```ts
import AlarmAIDiagnosisDrawer from './AlarmAIDiagnosisDrawer.vue';
import { buildAlertAIDiagnosisRequest } from './alarm_ai_diagnosis';
import { diagnoseAIOpsAlertReq } from '@/api/aiops';
import type { AIOpsDiagnosisReport } from '@/typings/aiops';
```

- [ ] **Step 3: Add drawer state**

Inside `<script setup>` in `Alarm.vue`, add:

```ts
const aiDiagnosisPanel = reactive<{
  visible: boolean;
  loading: boolean;
  error: string;
  report: AIOpsDiagnosisReport | null;
}>({
  visible: false,
  loading: false,
  error: '',
  report: null,
});

const analyzeAlertWithAI = async (record: AlertAlarmResp) => {
  const built = buildAlertAIDiagnosisRequest(record);
  if (!built.ok) {
    message.warning(`无法发起 AI 分析：${built.reason}`);
    return;
  }
  aiDiagnosisPanel.visible = true;
  aiDiagnosisPanel.loading = true;
  aiDiagnosisPanel.error = '';
  aiDiagnosisPanel.report = null;
  try {
    const resp = await diagnoseAIOpsAlertReq(built.req);
    aiDiagnosisPanel.report = resp.report;
  } catch (err) {
    aiDiagnosisPanel.error = err instanceof Error ? err.message : String(err);
  } finally {
    aiDiagnosisPanel.loading = false;
  }
};
```

- [ ] **Step 4: Add row action**

In the action column template, change:

```vue
<a-space>
  <a @click="openAlarmDetail(record as AlertAlarmResp)">详情</a>
  <a @click="() => analyzeRootCauseV2(record as AlertAlarmResp)">故障定位</a>
</a-space>
```

to:

```vue
<a-space>
  <a @click="openAlarmDetail(record as AlertAlarmResp)">详情</a>
  <a @click="() => analyzeRootCauseV2(record as AlertAlarmResp)">故障定位</a>
  <a @click="() => analyzeAlertWithAI(record as AlertAlarmResp)">AI 分析</a>
</a-space>
```

- [ ] **Step 5: Add drawer to template**

Near the existing RCA modal/drawer blocks in `Alarm.vue`, add:

```vue
<alarm-a-i-diagnosis-drawer
  :open="aiDiagnosisPanel.visible"
  :loading="aiDiagnosisPanel.loading"
  :error="aiDiagnosisPanel.error"
  :report="aiDiagnosisPanel.report"
  @close="aiDiagnosisPanel.visible = false"
/>
```

- [ ] **Step 6: Run frontend typecheck**

Run:

```bash
cd OneOPS-UI && yarn typecheck
```

Expected: PASS.

- [ ] **Step 7: Checkpoint**

Run:

```bash
if test -d .git; then
  git add OneOPS-UI/src/views/alert/Alarm.vue OneOPS-UI/src/views/alert/AlarmAIDiagnosisDrawer.vue
  git commit -m "feat(alert): add AI diagnosis drawer"
else
  echo "No git repository; checkpoint Task 7 complete."
fi
```

---

### Task 8: Final Regression And Documentation Update

**Files:**

- Modify: `docs/superpowers/specs/2026-06-18-network-ops-ai-agent-design.md`

- [ ] **Step 1: Run backend validation**

Run:

```bash
cd OneOPS && go test ./app/aiops/...
```

Expected: PASS.

- [ ] **Step 2: Run frontend smoke**

Run:

```bash
cd OneOPS-UI && yarn smoke:alert-ai-diagnosis
```

Expected: PASS and output includes `Alert AI diagnosis smoke passed`.

- [ ] **Step 3: Run frontend typecheck**

Run:

```bash
cd OneOPS-UI && yarn typecheck
```

Expected: PASS.

- [ ] **Step 4: Update the design note with implementation status**

Append to `docs/superpowers/specs/2026-06-18-network-ops-ai-agent-design.md`:

```markdown

## Implementation Status

- MVP implementation slice completed: alert-detail AI analysis request/report contract, uploaded log evidence parser, show command guard, local Ollama report generator, backend diagnosis endpoint, and frontend read-only drawer.
- Show command execution remains disabled; the MVP only suggests approved read-only `show` commands.
- RCA connection inside the alert diagnosis endpoint remains conservative and uses a placeholder conclusion until the next slice connects full `rca3` context assembly.
```

- [ ] **Step 5: Checkpoint**

Run:

```bash
if test -d .git; then
  git add docs/superpowers/specs/2026-06-18-network-ops-ai-agent-design.md
  git commit -m "docs(aiops): record MVP implementation status"
else
  echo "No git repository; checkpoint Task 8 complete."
fi
```

---

## Self-Review

Spec coverage:

- Alert detail entry is covered by Tasks 6 and 7.
- Local Ollama report generation is covered by Task 4.
- Real log evidence is covered by Task 2.
- RCA boundary is preserved by Task 5 using a conservative placeholder until full `rca3` assembly is connected in a later plan.
- Show-only boundary is covered by Task 3 and Task 4 validation.
- Evidence-cited report schema is covered by Task 1.
- UI rendering and error handling are covered by Task 7.
- Regression commands are covered by Task 8.

Deferred follow-up plan:

- Connect alert diagnosis endpoint to full `rca3`/MonitoringRootCauseV2 context assembly.
- Replace `uploaded_log_sample` metadata transport with a real log evidence source or file upload workflow.
- Add persistent audit storage for `AlertDiagnosisResp`, separate from existing remediation-plan audit if needed.
- Add local document ingestion and hybrid retrieval after the first real-log golden scenario is stable.
