# NetPath Engine Runner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `oneops-netpath` reusable through a public Go SDK and make OneOPS NetPath analysis runs able to use an injected real/fake analysis engine while preserving the current `engine_pending` fallback.

**Architecture:** The standalone `oneops-netpath` module remains the canonical forwarding engine and exposes `pkg/netpath` as its public API. OneOPS adds an `AnalysisEngine` service seam and uses it only when configured; this phase does not add a local module `replace` or make DC2 preview snapshots pretend to be full analysis snapshots.

**Tech Stack:** Go 1.22 module for `github.com/netxops/oneops-netpath`; Go 1.25.5 OneOPS service package; standard `testing`; existing `dto` and `Option` patterns.

---

## File Structure

`/Users/huangliang/project/OneOPS-ALL/oneops-netpath/pkg/netpath/netpath.go`

- New public SDK package.
- Re-exports stable model types from `internal/model`.
- Wraps `internal/engine.Analyze`.

`/Users/huangliang/project/OneOPS-ALL/oneops-netpath/pkg/netpath/netpath_test.go`

- Proves callers can construct snapshots and call `Analyze` without importing `internal`.

`/Users/huangliang/project/OneOPS-ALL/OneOPS/app/netpath/service/impl/netpath.go`

- Adds `AnalysisEngine` interface.
- Adds `WithAnalysisEngine`.
- Uses injected engine in `CreateAnalyzeRun`.
- Preserves fallback result when no engine is configured.
- Converts engine errors into failed analysis runs that are stored and retrievable.

`/Users/huangliang/project/OneOPS-ALL/OneOPS/app/netpath/service/impl/netpath_test.go`

- Adds fake engine tests for configured success, configured failure, fallback compatibility, and mutation isolation.

No `OneOPS/go.mod` change in this phase.

---

### Task 1: Public SDK Boundary In oneops-netpath

**Files:**
- Create: `/Users/huangliang/project/OneOPS-ALL/oneops-netpath/pkg/netpath/netpath.go`
- Create: `/Users/huangliang/project/OneOPS-ALL/oneops-netpath/pkg/netpath/netpath_test.go`

- [ ] **Step 1: Write the public SDK test**

Create `/Users/huangliang/project/OneOPS-ALL/oneops-netpath/pkg/netpath/netpath_test.go`:

```go
package netpath

import "testing"

func TestAnalyzeUsesPublicTypes(t *testing.T) {
	req := AnalyzeRequest{
		Snapshot: Snapshot{
			SnapshotID: "sdk-simple",
			TenantCode: "demo",
			Devices: []Device{
				{
					DeviceCode: "r1",
					DeviceType: "router",
					VRFs: []VRF{
						{Name: "default"},
					},
					Interfaces: []Interface{
						{
							InterfaceName: "eth0",
							VRF: "default",
							IPv4Addresses: []string{"10.0.2.1/24"},
						},
					},
					RouteTables: []RouteTable{
						{
							VRF: "default",
							Routes: []Route{
								{
									Destination: "10.0.2.0/24",
									OutInterface: "eth0",
									Protocol: "connected",
									Raw: "C 10.0.2.0/24 is directly connected, eth0",
								},
							},
						},
					},
				},
			},
			SourceVersions: &SourceRefs{
				ConfigVersionIDs: []string{"cfg-1"},
			},
		},
		Flow: Flow{
			SrcIP: "10.0.1.10",
			DstIP: "10.0.2.20",
			Protocol: "tcp",
			DstPort: 443,
			IngressDeviceCode: "r1",
			IngressVRF: "default",
		},
		Options: &Options{MaxHops: 8},
	}

	resp, err := Analyze(req)
	if err != nil {
		t.Fatalf("Analyze returned error: %v", err)
	}
	if resp.SnapshotID != "sdk-simple" {
		t.Fatalf("expected snapshot id sdk-simple, got %q", resp.SnapshotID)
	}
	if len(resp.Traces) != 1 {
		t.Fatalf("expected one trace, got %d", len(resp.Traces))
	}
	if resp.Traces[0].Disposition != DispositionDeliveredToSubnet {
		t.Fatalf("expected disposition %q, got %q", DispositionDeliveredToSubnet, resp.Traces[0].Disposition)
	}
}
```

- [ ] **Step 2: Run the SDK test and verify it fails**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/oneops-netpath
go test ./pkg/netpath
```

Expected: fail because package `pkg/netpath` has no implementation yet.

- [ ] **Step 3: Add the public SDK wrapper**

Create `/Users/huangliang/project/OneOPS-ALL/oneops-netpath/pkg/netpath/netpath.go`:

```go
package netpath

import (
	"github.com/netxops/oneops-netpath/internal/engine"
	"github.com/netxops/oneops-netpath/internal/model"
)

type Snapshot = model.Snapshot
type SourceRefs = model.SourceRefs
type Device = model.Device
type VRF = model.VRF
type Interface = model.Interface
type Link = model.Link
type RouteTable = model.RouteTable
type Route = model.Route
type Flow = model.Flow
type AnalyzeRequest = model.AnalyzeRequest
type Options = model.Options
type AnalyzeResponse = model.AnalyzeResponse
type Trace = model.Trace
type Hop = model.Hop
type Step = model.Step
type Diagnostic = model.Diagnostic

const (
	DispositionAccepted = model.DispositionAccepted
	DispositionDeliveredToSubnet = model.DispositionDeliveredToSubnet
	DispositionExitsNetwork = model.DispositionExitsNetwork
	DispositionDeniedIn = model.DispositionDeniedIn
	DispositionDeniedOut = model.DispositionDeniedOut
	DispositionNoRoute = model.DispositionNoRoute
	DispositionNullRouted = model.DispositionNullRouted
	DispositionLoop = model.DispositionLoop
	DispositionNeighborUnreachable = model.DispositionNeighborUnreachable
	DispositionInsufficientInfo = model.DispositionInsufficientInfo
	DispositionEngineError = model.DispositionEngineError
)

func Analyze(req AnalyzeRequest) (AnalyzeResponse, error) {
	return engine.Analyze(req)
}
```

Run `gofmt` on both new files.

- [ ] **Step 4: Run oneops-netpath tests**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/oneops-netpath
go test -count=1 ./...
```

Expected: pass.

- [ ] **Step 5: Commit Task 1**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/oneops-netpath
git add pkg/netpath/netpath.go pkg/netpath/netpath_test.go
git commit -m "feat: expose netpath public sdk"
```

Expected: commit created in `oneops-netpath`.

---

### Task 2: OneOPS AnalysisEngine Seam

**Files:**
- Modify: `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/netpath/service/impl/netpath.go`
- Modify: `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/netpath/service/impl/netpath_test.go`

- [ ] **Step 1: Add fake engine tests**

In `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/netpath/service/impl/netpath_test.go`, add this fake after `fakeSnapshotBuilder`:

```go
type fakeAnalysisEngine struct {
	result *dto.AnalyzeResult
	disposition string
	err error
	req dto.AnalyzeRunCreateReq
}

func (f *fakeAnalysisEngine) Analyze(ctx context.Context, req dto.AnalyzeRunCreateReq) (*dto.AnalyzeResult, string, error) {
	_ = ctx
	f.req = req
	return f.result, f.disposition, f.err
}
```

Add these tests near the existing create-run tests:

```go
func TestNetPathServiceCreateAnalyzeRunUsesConfiguredEngine(t *testing.T) {
	engine := &fakeAnalysisEngine{
		disposition: "delivered_to_subnet",
		result: &dto.AnalyzeResult{
			SnapshotID: "analysis-1",
			Flow: dto.AnalyzeFlow{
				SrcIP: "10.0.1.10",
				DstIP: "10.0.2.20",
				Protocol: "tcp",
				DstPort: 443,
				IngressDeviceCode: "r1",
				IngressVRF: "default",
			},
			Traces: []dto.AnalyzeTrace{
				{
					TraceID: "trace-1",
					Disposition: "delivered_to_subnet",
					Hops: []dto.AnalyzeHop{
						{
							Sequence: 1,
							DeviceCode: "r1",
							OutInterface: "eth0",
							VRF: "default",
							Steps: []dto.AnalyzeStep{
								{
									Type: "route_lookup",
									Action: "matched",
									MatchedObject: "10.0.2.0/24",
								},
							},
						},
					},
				},
			},
		},
	}
	svc := NewNetPathService(nil, WithAnalysisEngine(engine))

	created, err := svc.CreateAnalyzeRun(context.Background(), dto.AnalyzeRunCreateReq{
		TenantCode: " demo ",
		SnapshotID: " analysis-1 ",
		SrcIP: " 10.0.1.10 ",
		DstIP: " 10.0.2.20 ",
		Protocol: " tcp ",
		DstPort: 443,
		IngressDeviceCode: " r1 ",
		IngressVRF: " default ",
	})
	if err != nil {
		t.Fatalf("CreateAnalyzeRun returned error: %v", err)
	}
	if created.Status != "completed" {
		t.Fatalf("expected status completed, got %q", created.Status)
	}
	if created.Disposition != "delivered_to_subnet" {
		t.Fatalf("expected run disposition delivered_to_subnet, got %q", created.Disposition)
	}
	if created.Result == nil || len(created.Result.Traces) != 1 {
		t.Fatalf("expected one engine trace, got %#v", created.Result)
	}
	if created.Result.Traces[0].Disposition != "delivered_to_subnet" {
		t.Fatalf("expected trace disposition delivered_to_subnet, got %q", created.Result.Traces[0].Disposition)
	}
	if engine.req.TenantCode != "demo" || engine.req.SnapshotID != "analysis-1" {
		t.Fatalf("expected normalized engine request, got %#v", engine.req)
	}

	got, err := svc.GetAnalyzeRun(context.Background(), created.Code)
	if err != nil {
		t.Fatalf("GetAnalyzeRun returned error: %v", err)
	}
	if got.Disposition != "delivered_to_subnet" {
		t.Fatalf("expected stored disposition delivered_to_subnet, got %q", got.Disposition)
	}
}

func TestNetPathServiceCreateAnalyzeRunStoresEngineError(t *testing.T) {
	engine := &fakeAnalysisEngine{err: fmt.Errorf("snapshot provider failed")}
	svc := NewNetPathService(nil, WithAnalysisEngine(engine))

	created, err := svc.CreateAnalyzeRun(context.Background(), dto.AnalyzeRunCreateReq{
		TenantCode: "demo",
		SrcIP: "10.0.1.10",
		DstIP: "10.0.2.20",
		IngressDeviceCode: "r1",
	})
	if err != nil {
		t.Fatalf("CreateAnalyzeRun should store failed run instead of returning error, got %v", err)
	}
	if created.Status != "failed" {
		t.Fatalf("expected status failed, got %q", created.Status)
	}
	if created.Disposition != "engine_error" {
		t.Fatalf("expected disposition engine_error, got %q", created.Disposition)
	}
	if created.Error != "snapshot provider failed" {
		t.Fatalf("expected engine error message, got %q", created.Error)
	}
	if created.Result != nil {
		t.Fatalf("expected nil result for failed engine run, got %#v", created.Result)
	}

	got, err := svc.GetAnalyzeRun(context.Background(), created.Code)
	if err != nil {
		t.Fatalf("GetAnalyzeRun returned error: %v", err)
	}
	if got.Status != "failed" || got.Error != "snapshot provider failed" {
		t.Fatalf("expected stored failed run, got %#v", got)
	}
}
```

- [ ] **Step 2: Run the targeted OneOPS service test and verify it fails**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test -count=1 ./app/netpath/service/impl
```

Expected: fail because `WithAnalysisEngine` and `AnalysisEngine` do not exist.

- [ ] **Step 3: Add the analysis engine interface and option**

In `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/netpath/service/impl/netpath.go`, update the service type and options:

```go
type NetPathService struct {
	db              *gorm.DB
	mutex           sync.RWMutex
	runs            map[string]*dto.AnalyzeRunResp
	snapshotBuilder SnapshotBuilder
	analysisEngine  AnalysisEngine
}

type AnalysisEngine interface {
	Analyze(ctx context.Context, req dto.AnalyzeRunCreateReq) (*dto.AnalyzeResult, string, error)
}

func WithAnalysisEngine(engine AnalysisEngine) Option {
	return func(s *NetPathService) {
		s.analysisEngine = engine
	}
}
```

- [ ] **Step 4: Refactor CreateAnalyzeRun through helper builders**

Keep the existing validation and snapshot defaulting. Replace the inline preview-result construction with two helpers:

```go
func (s *NetPathService) CreateAnalyzeRun(ctx context.Context, req dto.AnalyzeRunCreateReq) (*dto.AnalyzeRunResp, error) {
	req = normalizeAnalyzeRunCreateReq(req)
	if req.TenantCode == "" {
		return nil, fmt.Errorf("tenant_code is required")
	}
	if req.SrcIP == "" {
		return nil, fmt.Errorf("src_ip is required")
	}
	if req.DstIP == "" {
		return nil, fmt.Errorf("dst_ip is required")
	}
	if req.IngressDeviceCode == "" {
		return nil, fmt.Errorf("ingress_device_code is required")
	}
	if req.SnapshotID == "" {
		req.SnapshotID = "preview-" + req.TenantCode
	}

	resp := s.buildAnalyzeRunResp(ctx, req)
	return s.storeAnalyzeRun(resp), nil
}

func (s *NetPathService) buildAnalyzeRunResp(ctx context.Context, req dto.AnalyzeRunCreateReq) *dto.AnalyzeRunResp {
	now := time.Now().Unix()
	resp := &dto.AnalyzeRunResp{
		TenantCode: req.TenantCode,
		SnapshotID: req.SnapshotID,
		Status: "completed",
		Request: req,
		CreatedAt: now,
		UpdatedAt: now,
	}

	if s.analysisEngine != nil {
		result, disposition, err := s.analysisEngine.Analyze(ctx, req)
		if err != nil {
			resp.Status = "failed"
			resp.Disposition = "engine_error"
			resp.Error = err.Error()
			return resp
		}
		resp.Result = cloneAnalyzeResult(result)
		resp.Disposition = normalizeRunDisposition(disposition, result)
		return resp
	}

	resp.Result = buildPendingAnalyzeResult(req)
	resp.Disposition = "engine_pending"
	return resp
}
```

Move the old preview result construction into:

```go
func buildPendingAnalyzeResult(req dto.AnalyzeRunCreateReq) *dto.AnalyzeResult {
	return &dto.AnalyzeResult{
		SnapshotID: req.SnapshotID,
		Flow: dto.AnalyzeFlow{
			SrcIP: req.SrcIP,
			DstIP: req.DstIP,
			Protocol: req.Protocol,
			SrcPort: req.SrcPort,
			DstPort: req.DstPort,
			IngressDeviceCode: req.IngressDeviceCode,
			IngressInterface: req.IngressInterface,
			IngressVRF: req.IngressVRF,
			BusinessLabel: req.BusinessLabel,
		},
		Traces: []dto.AnalyzeTrace{
			{
				TraceID: "trace-1",
				Disposition: "engine_pending",
				Hops: []dto.AnalyzeHop{
					{
						Sequence: 1,
						DeviceCode: req.IngressDeviceCode,
						VRF: req.IngressVRF,
						Steps: []dto.AnalyzeStep{
							{
								Type: "engine",
								Message: "pending external engine wiring",
								Details: map[string]string{"engine": "pending"},
							},
						},
					},
				},
				Diagnostics: []dto.AnalyzeDiagnostic{
					{
						Severity: "info",
						Code: "engine_not_wired",
						Message: "OneOPS service contract is ready; external engine wiring follows in the next task",
					},
				},
			},
		},
		Diagnostics: []dto.AnalyzeDiagnostic{
			{
				Severity: "info",
				Code: "result_preview_only",
				Message: "MVP result generated from request metadata only",
			},
		},
	}
}
```

Add deterministic run disposition normalization:

```go
func normalizeRunDisposition(disposition string, result *dto.AnalyzeResult) string {
	disposition = strings.TrimSpace(disposition)
	if disposition != "" {
		return disposition
	}
	if result != nil && len(result.Traces) > 0 {
		return strings.TrimSpace(result.Traces[0].Disposition)
	}
	return "engine_error"
}
```

Add a storage helper:

```go
func (s *NetPathService) storeAnalyzeRun(resp *dto.AnalyzeRunResp) *dto.AnalyzeRunResp {
	s.mutex.Lock()
	defer s.mutex.Unlock()
	for {
		resp.Code = nextAnalyzeRunCode()
		if _, exists := s.runs[resp.Code]; exists {
			continue
		}
		stored := cloneAnalyzeRunResp(resp)
		s.runs[resp.Code] = stored
		return cloneAnalyzeRunResp(stored)
	}
}
```

- [ ] **Step 5: Run OneOPS service tests**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test -count=1 ./app/netpath/service/impl
```

Expected: pass.

- [ ] **Step 6: Run OneOPS netpath targeted tests**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test -count=1 ./app/netpath/snapshot ./app/netpath/dto ./app/netpath/service ./app/netpath/service/impl ./app/netpath/api
go test -race -count=1 ./app/netpath/service/impl
```

Expected: pass.

- [ ] **Step 7: Commit Task 2**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
git add app/netpath/service/impl/netpath.go app/netpath/service/impl/netpath_test.go
git commit -m "feat: add netpath analysis engine seam"
```

Expected: commit created in OneOPS. Do not stage unrelated dirty files outside `app/netpath`.

---

## Self-Review

Spec coverage:

- Public SDK boundary: Task 1.
- OneOPS AnalysisEngine injection: Task 2.
- Fallback compatibility: Task 2 tests keep existing behavior.
- Engine errors stored as failed runs: Task 2 tests.
- No local module replace: file structure and scope explicitly exclude `go.mod`.
- DC2 route facts remain separate: no task modifies snapshot builder route facts.

Placeholder scan:

- No placeholder task remains. All implementation steps include exact files, code, commands, and expected outcomes.

Type consistency:

- `AnalysisEngine.Analyze(ctx context.Context, req dto.AnalyzeRunCreateReq) (*dto.AnalyzeResult, string, error)` is used consistently in design, tests, and implementation.
- `normalizeRunDisposition` uses explicit disposition first, then primary trace disposition, then `engine_error`.
