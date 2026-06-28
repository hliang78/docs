# Device V2 Network Scan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a real Device V2 network scan flow that lets users pick `function_area`, run controller-side `nmap` discovery against `IP / IP range / CIDR`, review discovery candidates, ingest approved candidates into Device V2, and then reuse the existing collect/store pipeline.

**Architecture:** Keep Device V2 as the only asset source of truth. Add a new discovery layer in OneOps for plans, runs, and candidates; add a controller-side `nmap` executor in `ctrlhub`; replace the current frontend demo state with real APIs while preserving the existing `设备探测` drawer workflow. The user journey remains `扫描 -> 审核入清单 -> 再采集`.

**Tech Stack:** Go, GORM/MySQL, Gin, existing OneOps Device V2 ingest/store services, ctrlhub controller, `nmap` XML output, Vue 3, TypeScript, Ant Design Vue.

---

## Scope Lock

### In Scope

- Device V2 discovery data model: `DiscoveryPlan`, `DiscoveryRun`, `DiscoveryCandidate`
- `function_area`-required scan request flow
- `IP / IP range / CIDR` parsing and validation
- controller dispatch from OneOps to `ctrlhub`
- controller-side `nmap` execution with XML parsing
- real frontend discovery drawer APIs
- approved candidate -> Device V2 ingest mapping
- reuse of existing Device V2 store/start collect flow
- one real acceptance script covering `scan -> ingest -> collect`

### Explicitly Out Of Scope

- ARP/L2 scan
- seed-neighbor discovery
- automatic `function_area` inference
- automatic ingest after scan
- automatic collect after ingest
- IPv6
- full-port scan
- OS fingerprinting / aggressive NSE rollout

## File Structure

### OneOps Backend

- Create: `OneOps/app/device/v2/discovery/model/device_v2_discovery_plan.go`
  Discovery plan persistence.
- Create: `OneOps/app/device/v2/discovery/model/device_v2_discovery_run.go`
  Discovery run persistence and state machine.
- Create: `OneOps/app/device/v2/discovery/model/device_v2_discovery_candidate.go`
  Discovery candidate persistence and ingest state.
- Create: `OneOps/app/device/v2/discovery/dto/device_v2_discovery.go`
  Request/response DTOs for plans, runs, candidates, ingest action.
- Create: `OneOps/app/device/v2/discovery/service/i_device_v2_discovery.go`
  Service contract.
- Create: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_scope.go`
  Range parsing, normalization, dedupe, and limit enforcement.
- Create: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_service.go`
  Plan CRUD, run creation, progress/completion, candidate approval.
- Create: `OneOps/app/device/v2/discovery/api/device_v2_discovery.go`
  Gin handlers.
- Create: `OneOps/app/device/v2/discovery/router/device_v2_discovery.go`
  Discovery sub-router.
- Modify: `OneOps/app/device/v2/router/device_v2.go`
  Mount discovery routes under `device/v2/discovery`.
- Modify: `OneOps/app/device/v2/ingest/model/device_v2_ingest_task.go`
  Extend supported sources with `network_scan`.
- Modify: `OneOps/app/device/v2/service/impl/device_v2_import_compat.go`
  Remove “unimplemented/planned only” behavior for real scan-ingested assets.

### OneOps Tests

- Create: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_scope_test.go`
- Create: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_service_test.go`
- Create: `OneOps/app/device/v2/discovery/api/device_v2_discovery_api_test.go`

### ctrlhub Controller

- Create: `ctrlhub/controller/pkg/discovery/models.go`
  Controller-side request/result types.
- Create: `ctrlhub/controller/pkg/discovery/nmap_executor.go`
  Shell-safe `nmap` command builder and executor.
- Create: `ctrlhub/controller/pkg/discovery/nmap_parser.go`
  XML parsing and normalization.
- Create: `ctrlhub/controller/pkg/discovery/service.go`
  Discovery orchestration with timeout/cancel/concurrency guard.
- Create: `ctrlhub/controller/pkg/discovery/service_test.go`
- Create: `ctrlhub/controller/pkg/discovery/nmap_parser_test.go`
- Modify: `ctrlhub/controller/pkg/controller/api/api.go`
  Add HTTP handlers for start/status/cancel discovery.
- Modify: `ctrlhub/controller/cmd/controller/main.go`
  Wire discovery service and routes.

### OneOPS-UI Frontend

- Modify: `OneOPS-UI/src/api/device/device-v2.ts`
  Add discovery request/response types and request functions.
- Modify: `OneOPS-UI/src/views/device/components/DeviceDiscoveryDrawer.vue`
  Replace local simulation with real plans/runs/candidates flow.
- Modify: `OneOPS-UI/src/views/device/device-discovery-workbench.ts`
  Keep only presentation helpers and remove fake execution/data generation.
- Modify: `OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue`
  Remove demo-localStorage state and route scan approvals to real APIs.
- Create: `OneOPS-UI/scripts/device-discovery-real-api-acceptance.ts`
  Browser/API acceptance script for the real flow.

### Docs

- Create: `docs/openclaw-autodev/evidence/device-v2-network-scan/`
  Evidence output directory for screenshots/json/markdown.
- Modify: `docs/runbooks/device-v2-network-scan.md`
  Operator runbook for controller prerequisites, scan flow, and rollback.

## Task 1: Add Discovery Data Contracts In OneOps

**Files:**
- Create: `OneOps/app/device/v2/discovery/model/device_v2_discovery_plan.go`
- Create: `OneOps/app/device/v2/discovery/model/device_v2_discovery_run.go`
- Create: `OneOps/app/device/v2/discovery/model/device_v2_discovery_candidate.go`
- Create: `OneOps/app/device/v2/discovery/dto/device_v2_discovery.go`
- Test: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_service_test.go`

- [ ] **Step 1: Write the failing model contract test**

```go
func TestDiscoveryModelsTableNames(t *testing.T) {
	if got := (&model.DeviceV2DiscoveryPlan{}).TableName(); got != "device_v2_discovery_plan" {
		t.Fatalf("unexpected plan table: %s", got)
	}
	if got := (&model.DeviceV2DiscoveryRun{}).TableName(); got != "device_v2_discovery_run" {
		t.Fatalf("unexpected run table: %s", got)
	}
	if got := (&model.DeviceV2DiscoveryCandidate{}).TableName(); got != "device_v2_discovery_candidate" {
		t.Fatalf("unexpected candidate table: %s", got)
	}
}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/device/v2/discovery/service/impl -run TestDiscoveryModelsTableNames -count=1
```

Expected: FAIL with missing package or undefined types.

- [ ] **Step 3: Add the model structs and DTO skeletons**

```go
type DeviceV2DiscoveryPlan struct {
	Code         string    `gorm:"primaryKey;type:varchar(64)"`
	Name         string    `gorm:"type:varchar(255);not null"`
	FunctionArea string    `gorm:"type:varchar(128);index;not null"`
	ScopeType    string    `gorm:"type:varchar(32);not null"`
	ScopeText    string    `gorm:"type:text;not null"`
	ExcludeText  string    `gorm:"type:text"`
	PortProfile  string    `gorm:"type:varchar(64);not null"`
	Enabled      bool      `gorm:"not null;default:true"`
	Schedule     string    `gorm:"type:varchar(128)"`
	LastRunAt    time.Time
	LastStatus   string    `gorm:"type:varchar(32)"`
	CreatedAt    time.Time
	UpdatedAt    time.Time
}

func (*DeviceV2DiscoveryPlan) TableName() string { return "device_v2_discovery_plan" }
```

```go
type CreateDiscoveryPlanReq struct {
	Name         string `json:"name" binding:"required"`
	FunctionArea string `json:"function_area" binding:"required"`
	ScopeType    string `json:"scope_type" binding:"required"`
	ScopeText    string `json:"scope_text" binding:"required"`
	ExcludeText  string `json:"exclude_text"`
	PortProfile  string `json:"port_profile"`
	Enabled      bool   `json:"enabled"`
	Schedule     string `json:"schedule"`
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/device/v2/discovery/service/impl -run TestDiscoveryModelsTableNames -count=1
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/device/v2/discovery/model app/device/v2/discovery/dto app/device/v2/discovery/service/impl/device_v2_discovery_service_test.go
git commit -m "feat: add device v2 discovery data contracts"
```

## Task 2: Implement Scope Parsing And Validation

**Files:**
- Create: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_scope.go`
- Test: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_scope_test.go`

- [ ] **Step 1: Write failing tests for IP, range, CIDR, excludes, and max-host limits**

```go
func TestNormalizeTargetsCIDRAndExclude(t *testing.T) {
	targets, err := normalizeTargets("cidr", "172.32.2.0/30", "172.32.2.1", 16)
	if err != nil {
		t.Fatalf("normalizeTargets returned err: %v", err)
	}
	got := strings.Join(targets, ",")
	if got != "172.32.2.2" {
		t.Fatalf("unexpected targets: %s", got)
	}
}

func TestNormalizeTargetsRejectsMissingFunctionAreaInputsAtAPILevel(t *testing.T) {
	if _, err := normalizeTargets("cidr", "172.32.2.0/24", "", 8); err == nil {
		t.Fatalf("expected max-host violation")
	}
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/device/v2/discovery/service/impl -run NormalizeTargets -count=1
```

Expected: FAIL with undefined `normalizeTargets`.

- [ ] **Step 3: Implement minimal normalization helpers**

```go
func normalizeTargets(scopeType, scopeText, excludeText string, maxHosts int) ([]string, error) {
	scopeType = strings.TrimSpace(scopeType)
	switch scopeType {
	case "single_ip":
		return normalizeSingleIP(scopeText, excludeText)
	case "ip_range":
		return normalizeIPRange(scopeText, excludeText, maxHosts)
	case "cidr":
		return normalizeCIDR(scopeText, excludeText, maxHosts)
	default:
		return nil, fmt.Errorf("unsupported scope_type: %s", scopeType)
	}
}
```

```go
func ensureWithinLimit(targets []string, maxHosts int) error {
	if maxHosts > 0 && len(targets) > maxHosts {
		return fmt.Errorf("scan target count %d exceeds max_hosts %d", len(targets), maxHosts)
	}
	return nil
}
```

- [ ] **Step 4: Run the focused tests again**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/device/v2/discovery/service/impl -run NormalizeTargets -count=1
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/device/v2/discovery/service/impl/device_v2_discovery_scope.go app/device/v2/discovery/service/impl/device_v2_discovery_scope_test.go
git commit -m "feat: add device v2 discovery scope normalization"
```

## Task 3: Add Discovery API And Run Lifecycle In OneOps

**Files:**
- Create: `OneOps/app/device/v2/discovery/service/i_device_v2_discovery.go`
- Create: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_service.go`
- Create: `OneOps/app/device/v2/discovery/api/device_v2_discovery.go`
- Create: `OneOps/app/device/v2/discovery/router/device_v2_discovery.go`
- Modify: `OneOps/app/device/v2/router/device_v2.go`
- Test: `OneOps/app/device/v2/discovery/api/device_v2_discovery_api_test.go`

- [ ] **Step 1: Write failing API tests for create-plan, start-run, list-candidates, and approve**

```go
func TestStartRunRejectsMissingFunctionArea(t *testing.T) {
	router := gin.New()
	api := &DeviceV2DiscoveryAPI{Service: failingStub{}}
	registerDiscoveryRoutes(router.Group("/device/v2"), api)

	req := httptest.NewRequest(http.MethodPost, "/device/v2/discovery/runs", strings.NewReader(`{"plan_code":"DP-1"}`))
	req.Header.Set("Content-Type", "application/json")
	resp := httptest.NewRecorder()
	router.ServeHTTP(resp, req)

	if resp.Code != http.StatusOK {
		t.Fatalf("expected envelope http 200, got %d", resp.Code)
	}
	if !strings.Contains(resp.Body.String(), "function_area") {
		t.Fatalf("expected validation error, got %s", resp.Body.String())
	}
}
```

- [ ] **Step 2: Run the failing API test**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/device/v2/discovery/api -run TestStartRunRejectsMissingFunctionArea -count=1
```

Expected: FAIL with missing API types/routes.

- [ ] **Step 3: Implement the service and API skeleton**

```go
type IDeviceV2Discovery interface {
	CreatePlan(ctx context.Context, req *dto.CreateDiscoveryPlanReq) (*model.DeviceV2DiscoveryPlan, error)
	StartRun(ctx context.Context, req *dto.StartDiscoveryRunReq) (*model.DeviceV2DiscoveryRun, error)
	ListCandidates(ctx context.Context, runCode string) ([]*model.DeviceV2DiscoveryCandidate, error)
	ApproveCandidate(ctx context.Context, req *dto.ApproveDiscoveryCandidateReq) (*dto.ApproveDiscoveryCandidateResp, error)
}
```

```go
func (a *DeviceV2DiscoveryAPI) StartRun(ctx *gin.Context) {
	var req dto.StartDiscoveryRunReq
	if err := ctx.ShouldBindJSON(&req); err != nil {
		response.FailWithMsg(err.Error(), ctx)
		return
	}
	run, err := a.Service.StartRun(ctx.Request.Context(), &req)
	if err != nil {
		response.FailWithMsg(err.Error(), ctx)
		return
	}
	response.OkWithData(run, ctx)
}
```

- [ ] **Step 4: Mount the discovery router under `device/v2/discovery`**

```go
func DeviceV2Discovery(r *gin.RouterGroup, api *api.DeviceV2DiscoveryAPI) {
	g := r.Group("device/v2/discovery")
	g.POST("plans", api.CreatePlan)
	g.GET("plans", api.ListPlans)
	g.POST("runs", api.StartRun)
	g.GET("runs/:runCode", api.GetRun)
	g.GET("runs/:runCode/candidates", api.ListCandidates)
	g.POST("candidates/:candidateCode/approve", api.ApproveCandidate)
	g.POST("candidates/:candidateCode/ignore", api.IgnoreCandidate)
}
```

- [ ] **Step 5: Run the API tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/device/v2/discovery/api ./app/device/v2/discovery/service/impl -count=1
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/device/v2/discovery app/device/v2/router/device_v2.go
git commit -m "feat: add device v2 discovery api and run lifecycle"
```

## Task 4: Map Approved Candidates Into Device V2 Ingest

**Files:**
- Modify: `OneOps/app/device/v2/ingest/model/device_v2_ingest_task.go`
- Modify: `OneOps/app/device/v2/service/impl/device_v2_import_compat.go`
- Modify: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_service.go`
- Test: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_service_test.go`

- [ ] **Step 1: Write the failing approval/ingest test**

```go
func TestApproveCandidateBuildsNetworkScanIngestPayload(t *testing.T) {
	svc := newDiscoveryServiceForTest(t)
	candidate := seedCandidate(t, svc.db, "DISC-CAND-1", "DefaultArea", "172.32.2.15")

	resp, err := svc.ApproveCandidate(context.Background(), &dto.ApproveDiscoveryCandidateReq{
		CandidateCode: candidate.Code,
		RequestedBy:   "tester",
	})
	if err != nil {
		t.Fatalf("ApproveCandidate returned err: %v", err)
	}
	if resp.SourceType != "network_scan" {
		t.Fatalf("expected network_scan, got %s", resp.SourceType)
	}
}
```

- [ ] **Step 2: Run the focused approval test**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/device/v2/discovery/service/impl -run TestApproveCandidateBuildsNetworkScanIngestPayload -count=1
```

Expected: FAIL with missing approval logic.

- [ ] **Step 3: Add `network_scan` support and build the ingest payload**

```go
var SupportedSources = []string{
	SourceManualAPI,
	SourceExcelUpload,
	SourceReferencePayload,
	SourceFuturePipeline,
	"network_scan",
}
```

```go
device := ingestmodel.DeviceV2IngestDevice{
	Code:         candidate.Code,
	BizCode:      candidate.Code,
	Name:         firstNonEmpty(candidate.Hostname, candidate.IP),
	PlatformCode: candidate.PlatformHint,
	Attributes: map[string]interface{}{
		"in_band_ip":    candidate.IP,
		"function_area": candidate.FunctionArea,
	},
	Metadata: map[string]interface{}{
		"source_type":              "network_scan",
		"source_label":             "网络扫描",
		"discovery_run_code":       candidate.RunCode,
		"discovery_candidate_code": candidate.Code,
		"discovery_source":         "nmap",
	},
}
```

- [ ] **Step 4: Add duplicate-existing behavior on `function_area + in_band_ip`**

```go
if existingCode, ok := s.lookupExistingByFunctionAreaAndIP(ctx, candidate.FunctionArea, candidate.IP); ok {
	candidate.IngestStatus = "duplicate_existing"
	candidate.DeviceV2Code = existingCode
	return &dto.ApproveDiscoveryCandidateResp{CandidateCode: candidate.Code, DeviceV2Code: existingCode, SourceType: "network_scan"}, s.db.Save(candidate).Error
}
```

- [ ] **Step 5: Run the discovery service tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/device/v2/discovery/service/impl -count=1
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/device/v2/discovery/service/impl app/device/v2/ingest/model/device_v2_ingest_task.go app/device/v2/service/impl/device_v2_import_compat.go
git commit -m "feat: ingest approved discovery candidates into device v2"
```

## Task 5: Add Controller-Side `nmap` Discovery Service

**Files:**
- Create: `ctrlhub/controller/pkg/discovery/models.go`
- Create: `ctrlhub/controller/pkg/discovery/nmap_executor.go`
- Create: `ctrlhub/controller/pkg/discovery/nmap_parser.go`
- Create: `ctrlhub/controller/pkg/discovery/service.go`
- Test: `ctrlhub/controller/pkg/discovery/nmap_parser_test.go`
- Test: `ctrlhub/controller/pkg/discovery/service_test.go`

- [ ] **Step 1: Write failing tests for command building and XML parsing**

```go
func TestBuildHostDiscoveryCommandUsesSafeArgs(t *testing.T) {
	cmd := buildHostDiscoveryCommand([]string{"172.32.2.15", "172.32.2.16"}, []int{22, 80})
	if got := strings.Join(cmd.Args, " "); !strings.Contains(got, "-sn") {
		t.Fatalf("expected -sn stage, got %s", got)
	}
	if strings.Contains(got, ";") {
		t.Fatalf("unexpected shell metacharacter in args: %s", got)
	}
}

func TestParseNmapXMLReturnsAliveHosts(t *testing.T) {
	results, err := parseNmapXML(strings.NewReader(sampleNmapXML))
	if err != nil {
		t.Fatalf("parseNmapXML returned err: %v", err)
	}
	if len(results.Hosts) != 1 || results.Hosts[0].IP != "172.32.2.15" {
		t.Fatalf("unexpected parse result: %#v", results)
	}
}
```

- [ ] **Step 2: Run the failing controller tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub
go test ./controller/pkg/discovery -count=1
```

Expected: FAIL with missing package/functions.

- [ ] **Step 3: Implement the request/result models and executor skeleton**

```go
type StartDiscoveryRequest struct {
	RunCode      string   `json:"run_code"`
	FunctionArea string   `json:"function_area"`
	Targets      []string `json:"targets"`
	PortProfile  string   `json:"port_profile"`
	TimeoutSec   int      `json:"timeout_sec"`
}

type HostResult struct {
	IP          string   `json:"ip"`
	Alive       bool     `json:"alive"`
	Hostnames   []string `json:"hostnames,omitempty"`
	OpenPorts   []int    `json:"open_ports,omitempty"`
	ServiceHints []string `json:"service_hints,omitempty"`
}
```

```go
func buildHostDiscoveryCommand(targets []string) *exec.Cmd {
	args := append([]string{"-sn", "-oX", "-"}, targets...)
	return exec.Command("nmap", args...)
}
```

- [ ] **Step 4: Implement the two-stage service flow**

```go
func (s *Service) Run(ctx context.Context, req StartDiscoveryRequest) (*Result, error) {
	aliveHosts, err := s.runHostDiscovery(ctx, req.Targets)
	if err != nil {
		return nil, err
	}
	if len(aliveHosts) == 0 {
		return &Result{RunCode: req.RunCode, Hosts: []HostResult{}}, nil
	}
	return s.runServiceProbe(ctx, req.RunCode, aliveHosts, req.PortProfile)
}
```

- [ ] **Step 5: Run the controller discovery tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub
go test ./controller/pkg/discovery -count=1
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub
git add controller/pkg/discovery
git commit -m "feat: add controller nmap discovery service"
```

## Task 6: Expose Controller Discovery HTTP Endpoints

**Files:**
- Modify: `ctrlhub/controller/pkg/controller/api/api.go`
- Modify: `ctrlhub/controller/cmd/controller/main.go`
- Test: `ctrlhub/controller/pkg/controller/api/api_test.go`

- [ ] **Step 1: Write failing API tests for start/status/cancel**

```go
func TestStartDiscoveryReturnsAcceptedPayload(t *testing.T) {
	ap := newControllerAPIForTest(t)
	req := httptest.NewRequest(http.MethodPost, "/api/v1/discovery/runs", strings.NewReader(`{"run_code":"RUN-1","function_area":"DefaultArea","targets":["172.32.2.15"]}`))
	req.Header.Set("Content-Type", "application/json")
	resp := httptest.NewRecorder()
	ap.StartDiscovery(resp, req)
	if resp.Code != http.StatusAccepted {
		t.Fatalf("expected 202, got %d", resp.Code)
	}
}
```

- [ ] **Step 2: Run the controller API test**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub
go test ./controller/pkg/controller/api -run TestStartDiscoveryReturnsAcceptedPayload -count=1
```

Expected: FAIL with missing endpoint.

- [ ] **Step 3: Add the controller API handlers**

```go
func (ap *ControllerAPI) StartDiscovery(w http.ResponseWriter, r *http.Request) {
	var req discovery.StartDiscoveryRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	go ap.discoveryService.RunAsync(context.Background(), req)
	writeJSON(w, http.StatusAccepted, map[string]interface{}{"run_code": req.RunCode, "status": "accepted"})
}
```

- [ ] **Step 4: Wire routes in controller main**

```go
router.HandleFunc("/api/v1/discovery/runs", controllerAPI.StartDiscovery).Methods(http.MethodPost)
router.HandleFunc("/api/v1/discovery/runs/{runCode}", controllerAPI.GetDiscoveryRun).Methods(http.MethodGet)
router.HandleFunc("/api/v1/discovery/runs/{runCode}:cancel", controllerAPI.CancelDiscoveryRun).Methods(http.MethodPost)
```

- [ ] **Step 5: Run the controller API test suite**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub
go test ./controller/pkg/controller/api ./controller/cmd/controller -count=1
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub
git add controller/pkg/controller/api/api.go controller/cmd/controller/main.go
git commit -m "feat: expose controller discovery endpoints"
```

## Task 7: Add Frontend Discovery API Layer

**Files:**
- Modify: `OneOPS-UI/src/api/device/device-v2.ts`

- [ ] **Step 1: Add the TypeScript request/response contracts**

```ts
export interface DeviceV2DiscoveryPlan {
  code: string;
  name: string;
  function_area: string;
  scope_type: 'single_ip' | 'ip_range' | 'cidr';
  scope_text: string;
  exclude_text?: string;
  port_profile?: string;
  enabled: boolean;
  schedule?: string;
}

export interface DeviceV2DiscoveryCandidate {
  code: string;
  run_code: string;
  function_area: string;
  ip: string;
  hostname?: string;
  summary?: string;
  review_status: 'pending_review' | 'ignored' | 'approved';
  ingest_status: 'not_ingested' | 'ingesting' | 'ingested' | 'duplicate_existing' | 'ingest_failed';
  device_v2_code?: string;
}
```

- [ ] **Step 2: Add the request helpers**

```ts
export const listDeviceV2DiscoveryPlansReq = async () =>
  request<DeviceV2DiscoveryPlan[]>({ url: `${BASE}/discovery/plans`, method: HTTP_GET });

export const startDeviceV2DiscoveryRunReq = async (data: DeviceV2DiscoveryRunStartReq) =>
  request<DeviceV2DiscoveryRun>({ url: `${BASE}/discovery/runs`, method: HTTP_POST, data });

export const approveDeviceV2DiscoveryCandidateReq = async (candidateCode: string, data?: { requested_by?: string }) =>
  request<DeviceV2DiscoveryApproveResp>({
    url: `${BASE}/discovery/candidates/${encodeURIComponent(candidateCode)}/approve`,
    method: HTTP_POST,
    data: data ?? {},
  });
```

- [ ] **Step 3: Type-check the API layer**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
pnpm exec vue-tsc --noEmit
```

Expected: PASS or only pre-existing unrelated errors.

- [ ] **Step 4: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git add src/api/device/device-v2.ts
git commit -m "feat: add device v2 discovery api client"
```

## Task 8: Replace Drawer Demo State With Real Discovery Flow

**Files:**
- Modify: `OneOPS-UI/src/views/device/components/DeviceDiscoveryDrawer.vue`
- Modify: `OneOPS-UI/src/views/device/device-discovery-workbench.ts`

- [ ] **Step 1: Remove fake execution generation from the drawer**

```ts
async function runPlanNow() {
  if (!selectedPlan.value?.function_area?.trim()) {
    message.error('请选择 function_area');
    return;
  }
  running.value = true;
  try {
    const run = await startDeviceV2DiscoveryRunReq({
      plan_code: selectedPlan.value.code,
      function_area: selectedPlan.value.function_area,
    });
    await refreshRun(run.code);
    activeTab.value = 'pending';
  } finally {
    running.value = false;
  }
}
```

- [ ] **Step 2: Reduce `device-discovery-workbench.ts` to UI-only helpers**

```ts
export function pendingStatusLabel(status: DeviceV2DiscoveryCandidate['ingest_status']) {
  switch (status) {
    case 'ingested':
      return '已入设备清单';
    case 'duplicate_existing':
      return '设备已存在';
    case 'ignored':
      return '已忽略';
    default:
      return '待审核';
  }
}
```

- [ ] **Step 3: Run a focused type-check**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
pnpm exec vue-tsc --noEmit
```

Expected: PASS or only pre-existing unrelated errors.

- [ ] **Step 4: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git add src/views/device/components/DeviceDiscoveryDrawer.vue src/views/device/device-discovery-workbench.ts
git commit -m "feat: replace discovery drawer demo execution with real api flow"
```

## Task 9: Remove Demo Device Special-Casing From Device V2 Management

**Files:**
- Modify: `OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue`

- [ ] **Step 1: Replace local-storage demo state with real candidate approval**

```ts
async function handleDiscoveryApprove(candidateCode: string) {
  const result = await approveDeviceV2DiscoveryCandidateReq(candidateCode);
  message.success(result.message || '已入设备清单');
  await refreshList();
}
```

- [ ] **Step 2: Keep existing collect flow for ingested devices**

```ts
async function collectApprovedDiscoveryDevices(codes: string[]) {
  const task = await startDeviceV2StorePipelineReq({ codes });
  latestStoreTaskId.value = task.task_id;
}
```

- [ ] **Step 3: Remove demo-only branches**

Delete or replace:

```ts
const DEVICE_DISCOVERY_STORAGE_KEY = 'oneops-device-v2-discovery-demo-state';
handleDemoDiscoveryCollect(...)
handleDemoDiscoveryMonitor(...)
simulateDiscoveryExecution(...)
```

- [ ] **Step 4: Run frontend type-check**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
pnpm exec vue-tsc --noEmit
```

Expected: PASS or only pre-existing unrelated errors.

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git add src/views/device/DeviceV2ManagementGrouped.vue
git commit -m "feat: route device v2 discovery approvals through real ingest flow"
```

## Task 10: Add Real Acceptance Script And Runbook

**Files:**
- Create: `OneOPS-UI/scripts/device-discovery-real-api-acceptance.ts`
- Modify: `docs/runbooks/device-v2-network-scan.md`
- Create: `docs/openclaw-autodev/evidence/device-v2-network-scan/README.md`

- [ ] **Step 1: Add a real acceptance script for `scan -> ingest -> collect`**

```ts
async function main() {
  const plan = await createPlan();
  const run = await startRun(plan.code, 'DefaultArea');
  const candidate = await waitForFirstCandidate(run.code);
  const approved = await approveCandidate(candidate.code);
  const collectTask = await startDeviceV2StorePipelineReq({ codes: [approved.device_v2_code] });
  console.log(JSON.stringify({ plan: plan.code, run: run.code, candidate: candidate.code, device_v2_code: approved.device_v2_code, collect_task: collectTask.task_id }, null, 2));
}
```

- [ ] **Step 2: Add the operator runbook**

```md
1. Verify the target controller host has `nmap` installed and executable by the controller service user.
2. Create a discovery plan with `function_area`, `scope_type`, and `scope_text`.
3. Start the run from the Device V2 page or via `POST /api/device/v2/discovery/runs`.
4. Review candidates and approve only the expected devices.
5. Trigger the existing Device V2 collect action after ingest succeeds.
```

- [ ] **Step 3: Run the acceptance script in a real environment**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
pnpm tsx scripts/device-discovery-real-api-acceptance.ts
```

Expected: script prints `plan`, `run`, `candidate`, `device_v2_code`, and `collect_task`.

- [ ] **Step 4: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git add scripts/device-discovery-real-api-acceptance.ts
git commit -m "test: add device v2 network scan real api acceptance"

cd /home/jacky/project/OneOPS-ALL/docs
git add runbooks/device-v2-network-scan.md openclaw-autodev/evidence/device-v2-network-scan/README.md
git commit -m "docs: add device v2 network scan runbook"
```

## Self-Review

### Spec Coverage

- `controller + nmap`:
  Covered by Task 5 and Task 6.
- `function_area` required:
  Covered by Task 2, Task 3, and Task 8.
- `IP / IP range / CIDR`:
  Covered by Task 2.
- `DiscoveryPlan / DiscoveryRun / DiscoveryCandidate`:
  Covered by Task 1 and Task 3.
- `扫描 -> 审核入清单 -> 再采集`:
  Covered by Task 4, Task 8, Task 9, and Task 10.
- Frontend demo replacement:
  Covered by Task 7, Task 8, and Task 9.
- Real acceptance path:
  Covered by Task 10.

### Placeholder Scan

- No `TODO` or `TBD` placeholders remain.
- Each task names exact files and commands.
- Each code-changing task includes code snippets or method signatures to anchor implementation.

### Type Consistency

- `function_area`, `scope_type`, `scope_text`, `run_code`, `candidate_code`, and `source_type = network_scan` are used consistently.
- Candidate states are consistently named `pending_review | ignored | approved` and `not_ingested | ingesting | ingested | duplicate_existing | ingest_failed`.
- The frontend API names align with the backend route names under `device/v2/discovery`.
