# Device V2 Discovery Credential Probe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a two-stage Device V2 discovery flow where users first run controller-based network scanning, then batch-probe selected candidates with temporary SSH and SNMP credential pools, manually confirm ambiguous successes, and ingest devices with bound credential refs for downstream collection.

**Architecture:** Keep network discovery and credential validation separate. OneOps owns plans, runs, candidates, probe persistence, credential resolution, and final binding decisions. Controller owns real network-side protocol probing through a new `DeviceDiscovery.ProbeCredentials` RPC. Frontend extends the existing discovery drawer and candidate list instead of creating a parallel workflow.

**Tech Stack:** Go, GORM/MySQL, Gin, existing Device V2 discovery module, existing credential resolver interfaces, controller RPC handlers, native Go SSH client, native Go SNMP client, Vue 3, Ant Design Vue, TypeScript, smoke scripts.

---

## Scope Lock

### In Scope

- Add persistent backend models for credential probe runs and probe results.
- Extend discovery candidates with probe summary and final selected credential fields.
- Add OneOps API endpoints to start probe runs, inspect probe results, and save final credential selections.
- Add a new controller RPC to probe SSH and SNMP credentials against discovered candidates.
- Extend the discovery frontend with batch probe initiation, per-candidate result display, and manual credential selection.
- Extend ingest approval so final confirmed SSH and SNMP credential refs are written into Device V2 fields used by downstream collection.

### Out Of Scope

- Auto-selecting a final credential when multiple credentials succeed for the same protocol.
- Blocking ingest when probe results are missing or all probes fail.
- Adding out-of-band protocols such as IPMI or Redfish in this phase.
- Building persistent `function_area` default credential pools.
- Replacing the current full collection pipeline.

## Files To Touch

### OneOps Backend

- Modify: `OneOps/app/device/v2/discovery/dto/device_v2_discovery.go`
- Modify: `OneOps/app/device/v2/discovery/model/device_v2_discovery_candidate.go`
- Create: `OneOps/app/device/v2/discovery/model/device_v2_discovery_probe_run.go`
- Create: `OneOps/app/device/v2/discovery/model/device_v2_discovery_probe_result.go`
- Modify: `OneOps/app/device/v2/discovery/service/i_device_v2_discovery.go`
- Modify: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_service.go`
- Create: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_probe_aggregate.go`
- Modify: `OneOps/app/device/v2/discovery/api/device_v2_discovery.go`
- Modify: `OneOps/app/device/v2/discovery/router/device_v2_discovery.go`
- Modify: `OneOps/app/device/v2/router/device_v2.go`
- Modify: `OneOps/initialize/mysql.go`
- Modify: `OneOps/initialize/mysql_test.go`
- Test: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_service_test.go`
- Test: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_execute_test.go`
- Create: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_probe_test.go`
- Modify: `OneOps/app/device/v2/discovery/api/device_v2_discovery_api_test.go`

### Controller

- Modify: `ctrlhub/controller/cmd/controller/device_discovery_rpc.go`
- Create: `ctrlhub/controller/cmd/controller/device_discovery_probe_rpc_test.go`
- Modify: `ctrlhub/controller/cmd/controller/main.go`

### Frontend

- Modify: `OneOPS-UI/src/api/device/device-v2.ts`
- Modify: `OneOPS-UI/src/views/device/device-discovery-workbench.ts`
- Modify: `OneOPS-UI/src/views/device/components/DeviceDiscoveryDrawer.vue`
- Create: `OneOPS-UI/src/views/device/components/DeviceDiscoveryProbeModal.vue`
- Modify: `OneOPS-UI/scripts/device-discovery-drawer-smoke.ts`

### Docs

- Modify: `docs/superpowers/specs/2026-06-29-device-v2-discovery-credential-probe-design.md`
- Create: `docs/superpowers/plans/2026-06-29-device-v2-discovery-credential-probe-implementation-plan.md`

## Task 1: Add Discovery Probe Persistence Models

**Files:**
- Modify: `OneOps/app/device/v2/discovery/model/device_v2_discovery_candidate.go`
- Create: `OneOps/app/device/v2/discovery/model/device_v2_discovery_probe_run.go`
- Create: `OneOps/app/device/v2/discovery/model/device_v2_discovery_probe_result.go`
- Modify: `OneOps/initialize/mysql.go`
- Modify: `OneOps/initialize/mysql_test.go`
- Test: `OneOps/initialize/mysql_test.go`

- [ ] **Step 1: Write the failing migration coverage test**

Add a startup migration assertion for the new probe tables in `OneOps/initialize/mysql_test.go`:

```go
func TestModelsIncludesDeviceV2DiscoveryProbeTables(t *testing.T) {
	tables := map[string]bool{}
	for _, model := range Models() {
		named, ok := model.(interface{ TableName() string })
		if ok {
			tables[named.TableName()] = true
		}
	}
	for _, table := range []string{
		(&discoverymodel.DeviceV2DiscoveryProbeRun{}).TableName(),
		(&discoverymodel.DeviceV2DiscoveryProbeResult{}).TableName(),
	} {
		if !tables[table] {
			t.Fatalf("expected startup AutoMigrate models to include %s", table)
		}
	}
}
```

- [ ] **Step 2: Run the migration coverage test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
env GOCACHE=/tmp/oneops-go-build-cache GOFLAGS=-mod=readonly go test ./initialize -run 'TestModelsIncludesDeviceV2DiscoveryProbeTables' -count=1
```

Expected:

```text
FAIL: expected startup AutoMigrate models to include device_v2_discovery_probe_run
```

- [ ] **Step 3: Add the new models and candidate summary fields**

Create `OneOps/app/device/v2/discovery/model/device_v2_discovery_probe_run.go`:

```go
package model

import "time"

type DeviceV2DiscoveryProbeRun struct {
	ID                    uint64    `json:"id" gorm:"primaryKey;autoIncrement"`
	Code                  string    `json:"code" gorm:"type:varchar(64);uniqueIndex;not null"`
	DiscoveryRunCode      string    `json:"discovery_run_code" gorm:"type:varchar(64);index;not null"`
	FunctionArea          string    `json:"function_area" gorm:"type:varchar(128);index;not null"`
	Status                string    `json:"status" gorm:"type:varchar(32);index;not null;default:pending"`
	SelectedCandidateCodes []string `json:"selected_candidate_codes" gorm:"type:json;serializer:json"`
	SelectedProtocols     []string  `json:"selected_protocols" gorm:"type:json;serializer:json"`
	SelectedCredentialRefs map[string][]string `json:"selected_credential_refs" gorm:"type:json;serializer:json"`
	Options               map[string]interface{} `json:"options" gorm:"type:json;serializer:json"`
	ErrorMessage          string    `json:"error_message" gorm:"type:text"`
	StartedAt             *time.Time `json:"started_at"`
	CompletedAt           *time.Time `json:"completed_at"`
	CreatedAt             time.Time `json:"created_at"`
	UpdatedAt             time.Time `json:"updated_at"`
}

func (*DeviceV2DiscoveryProbeRun) TableName() string { return "device_v2_discovery_probe_run" }
```

Create `OneOps/app/device/v2/discovery/model/device_v2_discovery_probe_result.go`:

```go
package model

import "time"

type DeviceV2DiscoveryProbeResult struct {
	ID            uint64                 `json:"id" gorm:"primaryKey;autoIncrement"`
	Code          string                 `json:"code" gorm:"type:varchar(64);uniqueIndex;not null"`
	ProbeRunCode  string                 `json:"probe_run_code" gorm:"type:varchar(64);index;not null"`
	CandidateCode string                 `json:"candidate_code" gorm:"type:varchar(64);index;not null"`
	Protocol      string                 `json:"protocol" gorm:"type:varchar(32);index;not null"`
	CredentialRef string                 `json:"credential_ref" gorm:"type:varchar(128);index;not null"`
	ProbeStatus   string                 `json:"probe_status" gorm:"type:varchar(32);index;not null"`
	Detail        string                 `json:"detail" gorm:"type:text"`
	LatencyMS     int                    `json:"latency_ms" gorm:"not null;default:0"`
	Summary       map[string]interface{} `json:"summary" gorm:"type:json;serializer:json"`
	ObservedAt    time.Time              `json:"observed_at" gorm:"autoCreateTime"`
	CreatedAt     time.Time              `json:"created_at"`
	UpdatedAt     time.Time              `json:"updated_at"`
}

func (*DeviceV2DiscoveryProbeResult) TableName() string { return "device_v2_discovery_probe_result" }
```

Extend `OneOps/app/device/v2/discovery/model/device_v2_discovery_candidate.go` with:

```go
	SSHProbeStatus          string                 `json:"ssh_probe_status" gorm:"type:varchar(32);index;not null;default:untested"`
	SNMPProbeStatus         string                 `json:"snmp_probe_status" gorm:"type:varchar(32);index;not null;default:untested"`
	SSHSuccessCount         int                    `json:"ssh_success_count" gorm:"not null;default:0"`
	SNMPSuccessCount        int                    `json:"snmp_success_count" gorm:"not null;default:0"`
	SelectedSSHCredentialRef string                `json:"selected_ssh_credential_ref" gorm:"type:varchar(128);index"`
	SelectedSNMPCredentialRef string               `json:"selected_snmp_credential_ref" gorm:"type:varchar(128);index"`
	ProbeSummary            map[string]interface{} `json:"probe_summary" gorm:"type:json;serializer:json"`
```

Register the new models in `OneOps/initialize/mysql.go`:

```go
device_v2_discovery_model.DeviceV2DiscoveryProbeRun{},
device_v2_discovery_model.DeviceV2DiscoveryProbeResult{},
```

- [ ] **Step 4: Run the migration coverage test to verify it passes**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
env GOCACHE=/tmp/oneops-go-build-cache GOFLAGS=-mod=readonly go test ./initialize -run 'TestModelsIncludesDeviceV2DiscoveryProbeTables|TestModelsIncludesDeviceV2DiscoveryTables' -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/initialize
```

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/device/v2/discovery/model/device_v2_discovery_candidate.go \
  app/device/v2/discovery/model/device_v2_discovery_probe_run.go \
  app/device/v2/discovery/model/device_v2_discovery_probe_result.go \
  initialize/mysql.go initialize/mysql_test.go
git commit -m "feat: add discovery credential probe models"
```

## Task 2: Add Backend DTOs And Service Contract For Probe Runs

**Files:**
- Modify: `OneOps/app/device/v2/discovery/dto/device_v2_discovery.go`
- Modify: `OneOps/app/device/v2/discovery/service/i_device_v2_discovery.go`
- Create: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_probe_test.go`

- [ ] **Step 1: Write the failing service-level DTO contract test**

Create `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_probe_test.go` with:

```go
func TestStartProbeRunRequiresCandidatesAndCredentialRefs(t *testing.T) {
	svc := &DeviceV2DiscoveryService{}
	_, err := svc.StartProbeRun(context.Background(), &dto.DeviceV2DiscoveryProbeRunStartReq{
		DiscoveryRunCode: "DR-001",
		FunctionArea:     "fa-a",
		CandidateCodes:   []string{},
		Protocols:        []string{"ssh", "snmp"},
	})
	if err == nil || !strings.Contains(err.Error(), "candidate_codes is required") {
		t.Fatalf("expected candidate_codes validation error, got %v", err)
	}
}
```

- [ ] **Step 2: Run the focused probe validation test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
env GOCACHE=/tmp/oneops-go-build-cache GOFLAGS=-mod=readonly go test ./app/device/v2/discovery/service/impl -run 'TestStartProbeRunRequiresCandidatesAndCredentialRefs' -count=1
```

Expected:

```text
FAIL: svc.StartProbeRun undefined
```

- [ ] **Step 3: Add DTOs and service interface methods**

Extend `OneOps/app/device/v2/discovery/dto/device_v2_discovery.go` with:

```go
type DeviceV2DiscoveryProbeRunStartReq struct {
	DiscoveryRunCode string              `json:"discovery_run_code"`
	FunctionArea     string              `json:"function_area"`
	CandidateCodes   []string            `json:"candidate_codes"`
	Protocols        []string            `json:"protocols"`
	SSHCredentialRefs []string           `json:"ssh_credential_refs"`
	SNMPCredentialRefs []string          `json:"snmp_credential_refs"`
	OnlyDiscoveredPorts *bool            `json:"only_discovered_ports,omitempty"`
}

type DeviceV2DiscoveryProbeRunResp struct {
	Code             string `json:"code"`
	DiscoveryRunCode string `json:"discovery_run_code"`
	FunctionArea     string `json:"function_area"`
	Status           string `json:"status"`
}

type DeviceV2DiscoveryProbeResultResp struct {
	CandidateCode string                 `json:"candidate_code"`
	Protocol      string                 `json:"protocol"`
	CredentialRef string                 `json:"credential_ref"`
	ProbeStatus   string                 `json:"probe_status"`
	Detail        string                 `json:"detail"`
	LatencyMS     int                    `json:"latency_ms"`
	Summary       map[string]interface{} `json:"summary,omitempty"`
}

type DeviceV2DiscoveryCredentialSelectionReq struct {
	SelectedSSHCredentialRef  string `json:"selected_ssh_credential_ref"`
	SelectedSNMPCredentialRef string `json:"selected_snmp_credential_ref"`
}
```

Extend `OneOps/app/device/v2/discovery/service/i_device_v2_discovery.go` with:

```go
	StartProbeRun(ctx context.Context, req *dto.DeviceV2DiscoveryProbeRunStartReq) (*model.DeviceV2DiscoveryProbeRun, error)
	ListProbeResults(ctx context.Context, candidateCode string) ([]*model.DeviceV2DiscoveryProbeResult, error)
	SaveCredentialSelection(ctx context.Context, candidateCode string, req *dto.DeviceV2DiscoveryCredentialSelectionReq) (*model.DeviceV2DiscoveryCandidate, error)
```

- [ ] **Step 4: Run the focused probe validation test to verify it now fails for business validation**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
env GOCACHE=/tmp/oneops-go-build-cache GOFLAGS=-mod=readonly go test ./app/device/v2/discovery/service/impl -run 'TestStartProbeRunRequiresCandidatesAndCredentialRefs' -count=1
```

Expected:

```text
FAIL: expected candidate_codes validation error, got <actual validation error or nil if implementation missing>
```

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/device/v2/discovery/dto/device_v2_discovery.go \
  app/device/v2/discovery/service/i_device_v2_discovery.go \
  app/device/v2/discovery/service/impl/device_v2_discovery_probe_test.go
git commit -m "feat: add discovery probe DTO contracts"
```

## Task 3: Implement Backend Probe Run Lifecycle And Aggregation

**Files:**
- Modify: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_service.go`
- Create: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_probe_aggregate.go`
- Create: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_probe_test.go`
- Test: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_probe_test.go`

- [ ] **Step 1: Expand the failing probe test to cover summary aggregation**

Add to `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_probe_test.go`:

```go
func TestApplyProbeResultsMarksAmbiguousAndSelectedRefs(t *testing.T) {
	candidate := &model.DeviceV2DiscoveryCandidate{Code: "DC-001"}
	results := []*model.DeviceV2DiscoveryProbeResult{
		{CandidateCode: "DC-001", Protocol: "ssh", CredentialRef: "cred-ssh-a", ProbeStatus: "success"},
		{CandidateCode: "DC-001", Protocol: "ssh", CredentialRef: "cred-ssh-b", ProbeStatus: "success"},
		{CandidateCode: "DC-001", Protocol: "snmp", CredentialRef: "cred-snmp-a", ProbeStatus: "success"},
	}
	applyProbeSummary(candidate, results)
	if candidate.SSHProbeStatus != "ambiguous" || candidate.SSHSuccessCount != 2 {
		t.Fatalf("expected ambiguous ssh summary, got %+v", candidate)
	}
	if candidate.SNMPProbeStatus != "success" || candidate.SelectedSNMPCredentialRef != "cred-snmp-a" {
		t.Fatalf("expected unique snmp selection, got %+v", candidate)
	}
}
```

- [ ] **Step 2: Run the focused aggregation test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
env GOCACHE=/tmp/oneops-go-build-cache GOFLAGS=-mod=readonly go test ./app/device/v2/discovery/service/impl -run 'TestApplyProbeResultsMarksAmbiguousAndSelectedRefs' -count=1
```

Expected:

```text
FAIL: undefined: applyProbeSummary
```

- [ ] **Step 3: Implement probe persistence, RPC dispatch, and aggregation**

Add `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_probe_aggregate.go`:

```go
package impl

import discoverymodel "github.com/netxops/OneOps/app/device/v2/discovery/model"

func applyProbeSummary(candidate *discoverymodel.DeviceV2DiscoveryCandidate, results []*discoverymodel.DeviceV2DiscoveryProbeResult) {
	if candidate == nil {
		return
	}
	var sshRefs []string
	var snmpRefs []string
	for _, result := range results {
		if result == nil || result.ProbeStatus != "success" {
			continue
		}
		switch result.Protocol {
		case "ssh":
			sshRefs = append(sshRefs, result.CredentialRef)
		case "snmp":
			snmpRefs = append(snmpRefs, result.CredentialRef)
		}
	}
	candidate.SSHSuccessCount = len(sshRefs)
	candidate.SNMPSuccessCount = len(snmpRefs)
	candidate.SSHProbeStatus, candidate.SelectedSSHCredentialRef = summarizeProbeRefs(sshRefs)
	candidate.SNMPProbeStatus, candidate.SelectedSNMPCredentialRef = summarizeProbeRefs(snmpRefs)
}

func summarizeProbeRefs(refs []string) (string, string) {
	switch len(refs) {
	case 0:
		return "failed", ""
	case 1:
		return "success", refs[0]
	default:
		return "ambiguous", ""
	}
}
```

In `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_service.go`, add:

```go
func (s *DeviceV2DiscoveryService) StartProbeRun(ctx context.Context, req *dto.DeviceV2DiscoveryProbeRunStartReq) (*model.DeviceV2DiscoveryProbeRun, error) {
	if req == nil {
		return nil, fmt.Errorf("probe request is required")
	}
	if len(req.CandidateCodes) == 0 {
		return nil, fmt.Errorf("candidate_codes is required")
	}
	run := &model.DeviceV2DiscoveryProbeRun{
		Code:                   generateDiscoveryCode("DPR"),
		DiscoveryRunCode:       strings.TrimSpace(req.DiscoveryRunCode),
		FunctionArea:           strings.TrimSpace(req.FunctionArea),
		Status:                 DeviceV2DiscoveryRunStatusPending,
		SelectedCandidateCodes: append([]string(nil), req.CandidateCodes...),
		SelectedProtocols:      append([]string(nil), req.Protocols...),
	}
	if err := s.db(ctx).Create(run).Error; err != nil {
		return nil, err
	}
	return run, nil
}
```

Also add helper methods to:

- resolve selected credential refs through the existing credential resolver
- call the controller RPC
- persist `DeviceV2DiscoveryProbeResult` rows
- aggregate per-candidate probe summary back onto `device_v2_discovery_candidate`

- [ ] **Step 4: Run the focused backend probe tests to verify they pass**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
env GOCACHE=/tmp/oneops-go-build-cache GOFLAGS=-mod=readonly go test ./app/device/v2/discovery/service/impl -run 'TestStartProbeRunRequiresCandidatesAndCredentialRefs|TestApplyProbeResultsMarksAmbiguousAndSelectedRefs' -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/app/device/v2/discovery/service/impl
```

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/device/v2/discovery/service/impl/device_v2_discovery_service.go \
  app/device/v2/discovery/service/impl/device_v2_discovery_probe_aggregate.go \
  app/device/v2/discovery/service/impl/device_v2_discovery_probe_test.go
git commit -m "feat: implement discovery probe lifecycle"
```

## Task 4: Add Controller Credential Probe RPC

**Files:**
- Modify: `ctrlhub/controller/cmd/controller/device_discovery_rpc.go`
- Create: `ctrlhub/controller/cmd/controller/device_discovery_probe_rpc_test.go`
- Modify: `ctrlhub/controller/cmd/controller/main.go`

- [ ] **Step 1: Write the failing controller probe RPC test**

Create `ctrlhub/controller/cmd/controller/device_discovery_probe_rpc_test.go`:

```go
func TestHandleDeviceDiscoveryProbeCredentialsReturnsSuccessPerProtocol(t *testing.T) {
	cs := &ControllerService{}
	resp, err := cs.handleDeviceDiscoveryProbeCredentials(context.Background(), map[string]interface{}{
		"probe_run_code": "DPR-001",
		"function_area":  "fa-a",
		"candidates": []map[string]interface{}{
			{"candidate_code": "DC-001", "ip": "127.0.0.1", "open_ports": []int{22, 161}},
		},
		"protocols": []string{"ssh", "snmp"},
	})
	if err != nil {
		t.Fatalf("unexpected err: %v", err)
	}
	if resp == nil {
		t.Fatal("expected non-nil response")
	}
}
```

- [ ] **Step 2: Run the controller probe RPC test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub
go test ./controller/cmd/controller -run 'TestHandleDeviceDiscoveryProbeCredentialsReturnsSuccessPerProtocol' -count=1
```

Expected:

```text
FAIL: cs.handleDeviceDiscoveryProbeCredentials undefined
```

- [ ] **Step 3: Implement the new controller RPC and register it**

Extend `ctrlhub/controller/cmd/controller/device_discovery_rpc.go` with request and response structs:

```go
type deviceDiscoveryProbeRequest struct {
	ProbeRunCode    string                               `json:"probe_run_code"`
	FunctionArea    string                               `json:"function_area"`
	Candidates      []deviceDiscoveryProbeCandidateEntry `json:"candidates"`
	Protocols       []string                             `json:"protocols"`
	SSHCredentials  []deviceDiscoverySSHCredential       `json:"ssh_credentials"`
	SNMPCredentials []deviceDiscoverySNMPCredential      `json:"snmp_credentials"`
	Options         deviceDiscoveryProbeOptions          `json:"options"`
}
```

Add the RPC handler skeleton:

```go
func (cs *ControllerService) handleDeviceDiscoveryProbeCredentials(ctx context.Context, params interface{}) (interface{}, error) {
	pm := paramsToMap(params)
	req, err := decodeDeviceDiscoveryProbeRequest(pm)
	if err != nil {
		return deviceDiscoveryProbeResponse{Status: deviceDiscoveryScanFailed, ErrorMessage: err.Error()}, nil
	}
	results := make([]deviceDiscoveryProbeResultEntry, 0)
	for _, candidate := range req.Candidates {
		results = append(results, probeCandidateProtocols(ctx, candidate, req)...)
	}
	return deviceDiscoveryProbeResponse{
		ControllerID: cs.discoveryControllerID(),
		Status:       deviceDiscoveryScanCompleted,
		Results:      results,
	}, nil
}
```

Register it in `ctrlhub/controller/cmd/controller/main.go`:

```go
oneOpsCommunicator.RegisterRPCHandler("DeviceDiscovery.ProbeCredentials", cs.handleDeviceDiscoveryProbeCredentials)
```

Add phase-1 protocol helpers in the same file:

- `probeCandidateSSHCredential`
- `probeCandidateSNMPCredential`
- `probeCandidateProtocols`

Use native Go SSH and SNMP libraries rather than shelling out.

- [ ] **Step 4: Run the controller probe RPC test to verify it passes**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub
go test ./controller/cmd/controller -run 'TestHandleDeviceDiscoveryProbeCredentialsReturnsSuccessPerProtocol|TestHandleDeviceDiscoveryScan' -count=1
```

Expected:

```text
ok  	github.com/netxops/ctrlhub/controller/cmd/controller
```

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub
git add controller/cmd/controller/device_discovery_rpc.go \
  controller/cmd/controller/device_discovery_probe_rpc_test.go \
  controller/cmd/controller/main.go
git commit -m "feat: add discovery credential probe rpc"
```

## Task 5: Expose Probe APIs In OneOps And Wire Controller Calls

**Files:**
- Modify: `OneOps/app/device/v2/discovery/api/device_v2_discovery.go`
- Modify: `OneOps/app/device/v2/discovery/router/device_v2_discovery.go`
- Modify: `OneOps/app/device/v2/router/device_v2.go`
- Modify: `OneOps/app/device/v2/discovery/api/device_v2_discovery_api_test.go`

- [ ] **Step 1: Write the failing API test for starting a probe run**

Add to `OneOps/app/device/v2/discovery/api/device_v2_discovery_api_test.go`:

```go
func TestStartProbeRunCallsServiceAndReturnsProbeRun(t *testing.T) {
	// mirror the existing execute-run API test style and expect HTTP 200 with probe run code
}
```

- [ ] **Step 2: Run the focused API test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
env GOCACHE=/tmp/oneops-go-build-cache GOFLAGS=-mod=readonly go test ./app/device/v2/discovery/api -run 'TestStartProbeRunCallsServiceAndReturnsProbeRun' -count=1
```

Expected:

```text
FAIL: missing API route or method
```

- [ ] **Step 3: Add API handlers and routes**

In `OneOps/app/device/v2/discovery/api/device_v2_discovery.go`, add:

```go
func (api *DeviceV2DiscoveryAPI) StartProbeRun(c *gin.Context) {
	var req dto.DeviceV2DiscoveryProbeRunStartReq
	if err := c.ShouldBindJSON(&req); err != nil {
		common.FailWithMessage(err.Error(), c)
		return
	}
	run, err := api.Service.StartProbeRun(c.Request.Context(), &req)
	if err != nil {
		common.FailWithMessage(err.Error(), c)
		return
	}
	common.OkWithData(run, c)
}
```

Add list/save routes in `OneOps/app/device/v2/discovery/router/device_v2_discovery.go`:

```go
g.POST("probe-runs", api.StartProbeRun)
g.GET("candidates/:candidateCode/probe-results", api.ListCandidateProbeResults)
g.POST("candidates/:candidateCode/credential-selection", api.SaveCandidateCredentialSelection)
```

Ensure `OneOps/app/device/v2/router/device_v2.go` still constructs the discovery service with controller caller support.

- [ ] **Step 4: Run the focused API test to verify it passes**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
env GOCACHE=/tmp/oneops-go-build-cache GOFLAGS=-mod=readonly go test ./app/device/v2/discovery/api -run 'TestStartProbeRunCallsServiceAndReturnsProbeRun|TestExecuteRunCallsControllerAndReturnsUpdatedRun' -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/app/device/v2/discovery/api
```

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/device/v2/discovery/api/device_v2_discovery.go \
  app/device/v2/discovery/router/device_v2_discovery.go \
  app/device/v2/router/device_v2.go \
  app/device/v2/discovery/api/device_v2_discovery_api_test.go
git commit -m "feat: expose discovery probe APIs"
```

## Task 6: Extend Ingest To Consume Final Credential Selection

**Files:**
- Modify: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_service.go`
- Test: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_execute_test.go`

- [ ] **Step 1: Write the failing ingest propagation test**

Add a focused test:

```go
func TestApproveCandidateUsesSelectedProbeCredentialRefs(t *testing.T) {
	// create a candidate with SelectedSSHCredentialRef and SelectedSNMPCredentialRef
	// approve it
	// assert generated ingest payload includes credential_ref_in_band and snmp_credential_ref
}
```

- [ ] **Step 2: Run the focused ingest propagation test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
env GOCACHE=/tmp/oneops-go-build-cache GOFLAGS=-mod=readonly go test ./app/device/v2/discovery/service/impl -run 'TestApproveCandidateUsesSelectedProbeCredentialRefs' -count=1
```

Expected:

```text
FAIL: expected credential_ref_in_band to be copied from selected probe credential
```

- [ ] **Step 3: Update ingest mapping to carry selected refs**

In the candidate-to-ingest path inside `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_service.go`, add:

```go
if strings.TrimSpace(candidate.SelectedSSHCredentialRef) != "" {
	attrs["credential_ref_in_band"] = strings.TrimSpace(candidate.SelectedSSHCredentialRef)
}
if strings.TrimSpace(candidate.SelectedSNMPCredentialRef) != "" {
	attrs["snmp_credential_ref"] = strings.TrimSpace(candidate.SelectedSNMPCredentialRef)
}
```

Preserve existing de-duplication and existing-device skip behavior.

- [ ] **Step 4: Run the focused ingest propagation test to verify it passes**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
env GOCACHE=/tmp/oneops-go-build-cache GOFLAGS=-mod=readonly go test ./app/device/v2/discovery/service/impl -run 'TestApproveCandidateUsesSelectedProbeCredentialRefs|TestDiscoveryServiceExecuteRun' -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/app/device/v2/discovery/service/impl
```

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/device/v2/discovery/service/impl/device_v2_discovery_service.go \
  app/device/v2/discovery/service/impl/device_v2_discovery_execute_test.go
git commit -m "feat: bind probe-selected credentials during ingest"
```

## Task 7: Extend Discovery Frontend For Probe Runs And Manual Selection

**Files:**
- Modify: `OneOPS-UI/src/api/device/device-v2.ts`
- Modify: `OneOPS-UI/src/views/device/device-discovery-workbench.ts`
- Modify: `OneOPS-UI/src/views/device/components/DeviceDiscoveryDrawer.vue`
- Create: `OneOPS-UI/src/views/device/components/DeviceDiscoveryProbeModal.vue`
- Modify: `OneOPS-UI/scripts/device-discovery-drawer-smoke.ts`

- [ ] **Step 1: Add the failing frontend smoke expectation**

In `OneOPS-UI/scripts/device-discovery-drawer-smoke.ts`, add an expectation that the drawer renders a probe entrypoint:

```ts
await expect(page.getByRole('button', { name: '凭证探测' })).toBeVisible();
```

- [ ] **Step 2: Run the frontend smoke script to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
npm run smoke:device-discovery-drawer
```

Expected:

```text
Error: expected button "凭证探测" to be visible
```

- [ ] **Step 3: Add probe API types and UI workflow**

Extend `OneOPS-UI/src/api/device/device-v2.ts` with:

```ts
export interface DeviceV2DiscoveryProbeRunStartReq {
  discovery_run_code: string;
  function_area: string;
  candidate_codes: string[];
  protocols: string[];
  ssh_credential_refs: string[];
  snmp_credential_refs: string[];
  only_discovered_ports?: boolean;
}

export const startDeviceV2DiscoveryProbeRunReq = (data: DeviceV2DiscoveryProbeRunStartReq) =>
  request.post('/device/v2/discovery/probe-runs', data);
```

Extend `OneOPS-UI/src/views/device/device-discovery-workbench.ts` records with:

```ts
  sshProbeStatus?: string;
  snmpProbeStatus?: string;
  sshSuccessCount?: number;
  snmpSuccessCount?: number;
  selectedSSHCredentialRef?: string;
  selectedSNMPCredentialRef?: string;
```

Create `OneOPS-UI/src/views/device/components/DeviceDiscoveryProbeModal.vue` with props:

```ts
defineProps<{
  open: boolean;
  candidateCodes: string[];
  functionArea: string;
}>();
```

Update `OneOPS-UI/src/views/device/components/DeviceDiscoveryDrawer.vue` to:

- add row selection on pending candidates
- add a `凭证探测` button
- show SSH/SNMP probe summary columns
- open the modal
- refresh candidate data after a successful probe run

- [ ] **Step 4: Run the frontend smoke script to verify it passes**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
npm run smoke:device-discovery-drawer
```

Expected:

```text
device discovery drawer smoke passed
```

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git add src/api/device/device-v2.ts \
  src/views/device/device-discovery-workbench.ts \
  src/views/device/components/DeviceDiscoveryDrawer.vue \
  src/views/device/components/DeviceDiscoveryProbeModal.vue \
  scripts/device-discovery-drawer-smoke.ts
git commit -m "feat: add discovery credential probe ui"
```

## Task 8: Add Candidate Credential Selection UI And Save Path

**Files:**
- Modify: `OneOPS-UI/src/views/device/components/DeviceDiscoveryDrawer.vue`
- Modify: `OneOPS-UI/src/api/device/device-v2.ts`
- Modify: `OneOPS-UI/scripts/device-discovery-drawer-smoke.ts`

- [ ] **Step 1: Add the failing manual selection smoke expectation**

Add a smoke expectation that ambiguous probe results render a manual selection affordance:

```ts
await expect(page.getByText('待确认(2)')).toBeVisible();
```

- [ ] **Step 2: Run the smoke script to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
npm run smoke:device-discovery-drawer
```

Expected:

```text
Error: expected text "待确认(2)" to be visible
```

- [ ] **Step 3: Implement final credential selection save flow**

Extend `OneOPS-UI/src/api/device/device-v2.ts`:

```ts
export interface DeviceV2DiscoveryCredentialSelectionReq {
  selected_ssh_credential_ref?: string;
  selected_snmp_credential_ref?: string;
}

export const saveDeviceV2DiscoveryCredentialSelectionReq = (
  candidateCode: string,
  data: DeviceV2DiscoveryCredentialSelectionReq,
) => request.post(`/device/v2/discovery/candidates/${candidateCode}/credential-selection`, data);
```

Update `OneOPS-UI/src/views/device/components/DeviceDiscoveryDrawer.vue` to:

- render selected refs when unique
- render `待确认(n)` when ambiguous
- open a confirmation dialog before ingest when a protocol has multiple successful refs
- call `saveDeviceV2DiscoveryCredentialSelectionReq` before approve/ingest when the user chooses a final binding

- [ ] **Step 4: Run the smoke script to verify it passes**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
npm run smoke:device-discovery-drawer
```

Expected:

```text
device discovery drawer smoke passed
```

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git add src/views/device/components/DeviceDiscoveryDrawer.vue \
  src/api/device/device-v2.ts \
  scripts/device-discovery-drawer-smoke.ts
git commit -m "feat: add manual credential selection before ingest"
```

## Task 9: Run End-To-End Verification

**Files:**
- Evidence: local command output
- Optional helper: `OneOps/scripts/device_v2_discovery_execute_smoke.sh`

- [ ] **Step 1: Run focused OneOps discovery tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
env GOCACHE=/tmp/oneops-go-build-cache GOFLAGS=-mod=readonly go test ./app/device/v2/discovery/... ./initialize -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/app/device/v2/discovery/api
ok  	github.com/netxops/OneOps/app/device/v2/discovery/service/impl
ok  	github.com/netxops/OneOps/initialize
```

- [ ] **Step 2: Run focused controller tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub
go test ./controller/cmd/controller -run 'TestHandleDeviceDiscoveryScan|TestHandleDeviceDiscoveryProbeCredentialsReturnsSuccessPerProtocol' -count=1
```

Expected:

```text
ok  	github.com/netxops/ctrlhub/controller/cmd/controller
```

- [ ] **Step 3: Run frontend smoke verification**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
npm run smoke:device-discovery-drawer
```

Expected:

```text
device discovery drawer smoke passed
```

- [ ] **Step 4: Run a real backend discovery + probe flow if local stack is available**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
./scripts/device_v2_discovery_execute_smoke.sh
```

Expected:

```text
Discovery plan created
Discovery run executed
Probe run created
Candidates listed with probe summaries
```

- [ ] **Step 5: Commit any final verification-only updates**

```bash
cd /home/jacky/project/OneOPS-ALL
git status --short
```

Expected:

```text
working tree clean or only intentional evidence/doc changes remain
```

## Spec Coverage Check

- Stage 1 `controller + nmap` discovery remains intact: covered by Task 4 regression coverage and Task 5 API wiring.
- Stage 2 temporary credential pool probe run: covered by Tasks 2, 3, 4, 5, and 7.
- Devices always ingestible even if probes fail: covered by Task 6, which only maps selected refs when present and does not add ingest blockers.
- SSH and SNMP successes retained independently: covered by Tasks 1 and 3.
- Multiple successes require manual confirmation: covered by Tasks 3 and 8.
- Final bindings flow into downstream collection fields: covered by Task 6.

## Placeholder Scan

- No `TBD`, `TODO`, or “implement later” markers remain.
- All tasks list exact files and commands.
- Every code-changing task includes concrete snippets or method signatures to add.

## Type Consistency Check

- Probe run DTO names use `DeviceV2DiscoveryProbeRunStartReq`, `DeviceV2DiscoveryProbeRunResp`, and `DeviceV2DiscoveryProbeResultResp` consistently.
- Candidate summary fields use `SelectedSSHCredentialRef` and `SelectedSNMPCredentialRef` consistently across backend and frontend.
- Controller RPC name is consistently `DeviceDiscovery.ProbeCredentials`.
