# OneOPS NetPath SDK Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dormant, build-tagged OneOPS adapter that can call the standalone `oneops-netpath/pkg/netpath` SDK during local opt-in verification.

**Architecture:** The adapter lives under `OneOPS/app/netpath/adapter/oneopsnetpath` and implements the OneOPS-owned `app/netpath/engine.AnalysisEngine` port. Default builds compile only a package doc file; SDK integration files are guarded by `//go:build oneops_netpath_sdk`, so OneOPS does not need a committed `oneops-netpath` dependency yet.

**Tech Stack:** Go build tags, OneOPS `app/netpath/engine`, standalone `github.com/netxops/oneops-netpath/pkg/netpath`, local `go.work` for optional tagged verification.

---

## File Structure

- Create `OneOPS/app/netpath/adapter/oneopsnetpath/doc.go`
  - Default package documentation.
  - No build tag.
  - Must not import `github.com/netxops/oneops-netpath/pkg/netpath`.
- Create `OneOPS/app/netpath/adapter/oneopsnetpath/adapter_sdk.go`
  - Build tag `oneops_netpath_sdk`.
  - Defines `SnapshotProvider`, `Adapter`, `New`, `Analyze`, and mapping helpers.
  - Imports the standalone SDK only inside this tagged file.
- Create `OneOPS/app/netpath/adapter/oneopsnetpath/adapter_sdk_test.go`
  - Build tag `oneops_netpath_sdk`.
  - Uses an in-memory `SnapshotProvider`.
  - Verifies request mapping, provider errors, SDK errors, response mapping, deep copy behavior, and primary trace disposition aggregation.

## Task 1: Add Dormant Adapter Package

**Files:**
- Create: `OneOPS/app/netpath/adapter/oneopsnetpath/doc.go`

- [ ] **Step 1: Add the default package documentation**

Create `OneOPS/app/netpath/adapter/oneopsnetpath/doc.go` with exactly this package-level behavior:

```go
// Package oneopsnetpath contains the optional OneOPS adapter for the standalone
// oneops-netpath SDK.
//
// The SDK implementation is compiled only when the oneops_netpath_sdk build tag
// is enabled. Normal OneOPS builds keep this package as documentation-only so
// the application does not require a committed oneops-netpath module dependency
// or a developer-local replace directive.
package oneopsnetpath
```

- [ ] **Step 2: Verify the package builds without the SDK tag**

Run from `/Users/huangliang/project/OneOPS-ALL/OneOPS`:

```bash
go test -count=1 ./app/netpath/adapter/oneopsnetpath
```

Expected: PASS with no dependency lookup for `github.com/netxops/oneops-netpath`.

## Task 2: Add Tagged SDK Adapter Implementation

**Files:**
- Create: `OneOPS/app/netpath/adapter/oneopsnetpath/adapter_sdk.go`

- [ ] **Step 1: Write the SDK-tagged implementation**

Create `OneOPS/app/netpath/adapter/oneopsnetpath/adapter_sdk.go`:

```go
//go:build oneops_netpath_sdk

package oneopsnetpath

import (
	"context"
	"errors"
	"fmt"
	"strings"

	netpathengine "github.com/netxops/OneOps/app/netpath/engine"
	netpath "github.com/netxops/oneops-netpath/pkg/netpath"
)

var errMissingSnapshotProvider = errors.New("oneopsnetpath snapshot provider is required")

type SnapshotProvider interface {
	GetSnapshot(ctx context.Context, req netpathengine.AnalyzeRequest) (netpath.Snapshot, error)
}

type Adapter struct {
	provider SnapshotProvider
}

func New(provider SnapshotProvider) netpathengine.AnalysisEngine {
	return &Adapter{provider: provider}
}

func (a *Adapter) Analyze(ctx context.Context, req netpathengine.AnalyzeRequest) (*netpathengine.AnalyzeResult, error) {
	if a == nil || a.provider == nil {
		return nil, errMissingSnapshotProvider
	}

	snapshot, err := a.provider.GetSnapshot(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("oneopsnetpath load snapshot: %w", err)
	}
	if strings.TrimSpace(snapshot.SnapshotID) == "" {
		return nil, errors.New("oneopsnetpath snapshot provider returned snapshot without snapshot_id")
	}

	resp, err := netpath.Analyze(netpath.AnalyzeRequest{
		Snapshot: snapshot,
		Flow:     toSDKFlow(req),
	})
	if err != nil {
		return nil, fmt.Errorf("oneopsnetpath analyze: %w", err)
	}

	result, err := toEngineAnalyzeResult(resp)
	if err != nil {
		return nil, err
	}
	return result, nil
}

func toSDKFlow(req netpathengine.AnalyzeRequest) netpath.Flow {
	return netpath.Flow{
		SrcIP:             req.SrcIP,
		DstIP:             req.DstIP,
		Protocol:          req.Protocol,
		SrcPort:           req.SrcPort,
		DstPort:           req.DstPort,
		IngressDeviceCode: req.IngressDeviceCode,
		IngressInterface:  req.IngressInterface,
		IngressVRF:        req.IngressVRF,
		BusinessLabel:     req.BusinessLabel,
	}
}

func toEngineAnalyzeResult(resp netpath.AnalyzeResponse) (*netpathengine.AnalyzeResult, error) {
	if len(resp.Traces) == 0 {
		return nil, errors.New("oneopsnetpath returned no traces")
	}
	disposition := strings.TrimSpace(resp.Traces[0].Disposition)
	if disposition == "" {
		return nil, errors.New("oneopsnetpath returned empty primary disposition")
	}

	return &netpathengine.AnalyzeResult{
		SnapshotID:  resp.SnapshotID,
		Flow:        toEngineFlow(resp.Flow),
		Disposition: disposition,
		Traces:      toEngineTraces(resp.Traces),
		Diagnostics: toEngineDiagnostics(resp.Diagnostics),
	}, nil
}

func toEngineFlow(flow netpath.Flow) netpathengine.Flow {
	return netpathengine.Flow{
		SrcIP:             flow.SrcIP,
		DstIP:             flow.DstIP,
		Protocol:          flow.Protocol,
		SrcPort:           flow.SrcPort,
		DstPort:           flow.DstPort,
		IngressDeviceCode: flow.IngressDeviceCode,
		IngressInterface:  flow.IngressInterface,
		IngressVRF:        flow.IngressVRF,
		BusinessLabel:     flow.BusinessLabel,
	}
}

func toEngineTraces(traces []netpath.Trace) []netpathengine.Trace {
	if len(traces) == 0 {
		return nil
	}
	mapped := make([]netpathengine.Trace, 0, len(traces))
	for _, trace := range traces {
		mapped = append(mapped, netpathengine.Trace{
			TraceID:     trace.TraceID,
			Disposition: trace.Disposition,
			Hops:        toEngineHops(trace.Hops),
			Diagnostics: toEngineDiagnostics(trace.Diagnostics),
			Confidence:  trace.Confidence,
		})
	}
	return mapped
}

func toEngineHops(hops []netpath.Hop) []netpathengine.Hop {
	if len(hops) == 0 {
		return nil
	}
	mapped := make([]netpathengine.Hop, 0, len(hops))
	for _, hop := range hops {
		mapped = append(mapped, netpathengine.Hop{
			Sequence:     hop.Sequence,
			DeviceCode:   hop.DeviceCode,
			InInterface:  hop.InInterface,
			OutInterface: hop.OutInterface,
			InZone:       hop.InZone,
			OutZone:      hop.OutZone,
			VRF:          hop.VRF,
			Steps:        toEngineSteps(hop.Steps),
		})
	}
	return mapped
}

func toEngineSteps(steps []netpath.Step) []netpathengine.Step {
	if len(steps) == 0 {
		return nil
	}
	mapped := make([]netpathengine.Step, 0, len(steps))
	for _, step := range steps {
		mapped = append(mapped, netpathengine.Step{
			Type:          step.Type,
			Action:        step.Action,
			MatchedObject: step.MatchedObject,
			RawRef:        step.RawRef,
			Message:       step.Message,
			Details:       cloneStringMap(step.Details),
		})
	}
	return mapped
}

func toEngineDiagnostics(diagnostics []netpath.Diagnostic) []netpathengine.Diagnostic {
	if len(diagnostics) == 0 {
		return nil
	}
	mapped := make([]netpathengine.Diagnostic, 0, len(diagnostics))
	for _, diagnostic := range diagnostics {
		mapped = append(mapped, netpathengine.Diagnostic{
			Severity: diagnostic.Severity,
			Code:     diagnostic.Code,
			Message:  diagnostic.Message,
			Refs:     cloneStringSlice(diagnostic.Refs),
		})
	}
	return mapped
}

func cloneStringMap(values map[string]string) map[string]string {
	if len(values) == 0 {
		return nil
	}
	cloned := make(map[string]string, len(values))
	for key, value := range values {
		cloned[key] = value
	}
	return cloned
}

func cloneStringSlice(values []string) []string {
	if len(values) == 0 {
		return nil
	}
	cloned := make([]string, len(values))
	copy(cloned, values)
	return cloned
}
```

- [ ] **Step 2: Verify default build still ignores the tagged file**

Run from `/Users/huangliang/project/OneOPS-ALL/OneOPS`:

```bash
go test -count=1 ./app/netpath/adapter/oneopsnetpath
```

Expected: PASS. If this command tries to resolve `github.com/netxops/oneops-netpath`, the build tag is wrong.

## Task 3: Add Tagged Adapter Tests

**Files:**
- Create: `OneOPS/app/netpath/adapter/oneopsnetpath/adapter_sdk_test.go`

- [ ] **Step 1: Write SDK-tagged tests**

Create `OneOPS/app/netpath/adapter/oneopsnetpath/adapter_sdk_test.go`:

```go
//go:build oneops_netpath_sdk

package oneopsnetpath

import (
	"context"
	"errors"
	"strings"
	"testing"

	netpathengine "github.com/netxops/OneOps/app/netpath/engine"
	netpath "github.com/netxops/oneops-netpath/pkg/netpath"
)

type fakeSnapshotProvider struct {
	snapshot netpath.Snapshot
	err      error
	calls    int
	seenReq  netpathengine.AnalyzeRequest
}

func (p *fakeSnapshotProvider) GetSnapshot(_ context.Context, req netpathengine.AnalyzeRequest) (netpath.Snapshot, error) {
	p.calls++
	p.seenReq = req
	if p.err != nil {
		return netpath.Snapshot{}, p.err
	}
	return p.snapshot, nil
}

func TestAnalyzeMapsSuccessfulTrace(t *testing.T) {
	provider := &fakeSnapshotProvider{snapshot: deliveredSnapshot()}
	adapter := New(provider)
	req := netpathengine.AnalyzeRequest{
		TenantCode:        "tenant-a",
		SnapshotID:        "snap-1",
		SrcIP:             "10.0.1.10",
		DstIP:             "10.0.2.20",
		Protocol:          "tcp",
		SrcPort:           32100,
		DstPort:           443,
		IngressDeviceCode: "r1",
		IngressInterface:  "ge-0/0/0",
		IngressVRF:        "default",
		BusinessLabel:     "crm-api",
	}

	result, err := adapter.Analyze(context.Background(), req)
	if err != nil {
		t.Fatalf("Analyze returned error: %v", err)
	}

	if provider.calls != 1 {
		t.Fatalf("expected provider to be called once, got %d", provider.calls)
	}
	if provider.seenReq != req {
		t.Fatalf("expected provider to receive original request\nwant: %#v\ngot:  %#v", req, provider.seenReq)
	}
	if result.SnapshotID != "snap-1" {
		t.Fatalf("expected snapshot id snap-1, got %q", result.SnapshotID)
	}
	if result.Flow.SrcIP != req.SrcIP || result.Flow.DstIP != req.DstIP || result.Flow.Protocol != req.Protocol {
		t.Fatalf("flow was not mapped from request: %#v", result.Flow)
	}
	if result.Flow.SrcPort != req.SrcPort || result.Flow.DstPort != req.DstPort {
		t.Fatalf("flow ports were not mapped from request: %#v", result.Flow)
	}
	if result.Flow.IngressDeviceCode != req.IngressDeviceCode || result.Flow.IngressInterface != req.IngressInterface || result.Flow.IngressVRF != req.IngressVRF {
		t.Fatalf("flow ingress fields were not mapped from request: %#v", result.Flow)
	}
	if result.Flow.BusinessLabel != req.BusinessLabel {
		t.Fatalf("business label was not mapped from request: %#v", result.Flow)
	}
	if result.Disposition != netpath.DispositionDeliveredToSubnet {
		t.Fatalf("expected run disposition %q, got %q", netpath.DispositionDeliveredToSubnet, result.Disposition)
	}
	if len(result.Traces) != 1 {
		t.Fatalf("expected one trace, got %d", len(result.Traces))
	}
	trace := result.Traces[0]
	if trace.TraceID == "" || trace.Disposition != netpath.DispositionDeliveredToSubnet || trace.Confidence == "" {
		t.Fatalf("unexpected trace mapping: %#v", trace)
	}
	if len(trace.Hops) != 2 {
		t.Fatalf("expected two hops, got %d", len(trace.Hops))
	}
	if trace.Hops[0].DeviceCode != "r1" || trace.Hops[1].DeviceCode != "r2" {
		t.Fatalf("unexpected hop devices: %#v", trace.Hops)
	}
	if len(trace.Hops[0].Steps) == 0 {
		t.Fatal("expected mapped route steps on first hop")
	}
	finalStep := trace.Hops[len(trace.Hops)-1].Steps[len(trace.Hops[len(trace.Hops)-1].Steps)-1]
	if finalStep.Type != "final_disposition" || finalStep.Action != netpath.DispositionDeliveredToSubnet {
		t.Fatalf("unexpected final step: %#v", finalStep)
	}
}

func TestAnalyzeRequiresProvider(t *testing.T) {
	_, err := New(nil).Analyze(context.Background(), netpathengine.AnalyzeRequest{})
	if !errors.Is(err, errMissingSnapshotProvider) {
		t.Fatalf("expected missing provider error, got %v", err)
	}

	var adapter *Adapter
	_, err = adapter.Analyze(context.Background(), netpathengine.AnalyzeRequest{})
	if !errors.Is(err, errMissingSnapshotProvider) {
		t.Fatalf("expected missing provider error for nil receiver, got %v", err)
	}
}

func TestAnalyzePropagatesProviderError(t *testing.T) {
	providerErr := errors.New("snapshot store unavailable")
	adapter := New(&fakeSnapshotProvider{err: providerErr})

	_, err := adapter.Analyze(context.Background(), validRequest())
	if !errors.Is(err, providerErr) {
		t.Fatalf("expected provider error wrapping, got %v", err)
	}
	if !strings.Contains(err.Error(), "load snapshot") {
		t.Fatalf("expected load snapshot context, got %v", err)
	}
}

func TestAnalyzeRejectsSnapshotWithoutID(t *testing.T) {
	snapshot := deliveredSnapshot()
	snapshot.SnapshotID = ""
	adapter := New(&fakeSnapshotProvider{snapshot: snapshot})

	_, err := adapter.Analyze(context.Background(), validRequest())
	if err == nil || !strings.Contains(err.Error(), "snapshot_id") {
		t.Fatalf("expected snapshot_id error, got %v", err)
	}
}

func TestAnalyzePropagatesSDKValidationError(t *testing.T) {
	adapter := New(&fakeSnapshotProvider{snapshot: deliveredSnapshot()})
	req := validRequest()
	req.SrcIP = "not-an-ip"

	_, err := adapter.Analyze(context.Background(), req)
	if err == nil || !strings.Contains(err.Error(), "oneopsnetpath analyze") {
		t.Fatalf("expected SDK validation wrapper, got %v", err)
	}
}

func TestToEngineAnalyzeResultRejectsEmptyTraceSet(t *testing.T) {
	_, err := toEngineAnalyzeResult(netpath.AnalyzeResponse{SnapshotID: "snap-1"})
	if err == nil || !strings.Contains(err.Error(), "no traces") {
		t.Fatalf("expected no traces error, got %v", err)
	}
}

func TestToEngineAnalyzeResultRejectsEmptyPrimaryDisposition(t *testing.T) {
	_, err := toEngineAnalyzeResult(netpath.AnalyzeResponse{
		SnapshotID: "snap-1",
		Traces:    []netpath.Trace{{TraceID: "trace-1"}},
	})
	if err == nil || !strings.Contains(err.Error(), "empty primary disposition") {
		t.Fatalf("expected empty primary disposition error, got %v", err)
	}
}

func TestToEngineAnalyzeResultDeepCopiesDetailsAndRefs(t *testing.T) {
	resp := netpath.AnalyzeResponse{
		SnapshotID: "snap-1",
		Flow:      netpath.Flow{SrcIP: "10.0.1.10", DstIP: "10.0.2.20", IngressDeviceCode: "r1"},
		Traces: []netpath.Trace{{
			TraceID:     "trace-1",
			Disposition: netpath.DispositionNoRoute,
			Hops: []netpath.Hop{{
				Sequence:   1,
				DeviceCode: "r1",
				Steps: []netpath.Step{{
					Type:    "route_lookup",
					Action:  "miss",
					Details: map[string]string{"destination": "10.0.2.20"},
				}},
			}},
			Diagnostics: []netpath.Diagnostic{{
				Severity: "warning",
				Code:     "route.miss",
				Message:  "no route",
				Refs:     []string{"r1/default"},
			}},
		}},
		Diagnostics: []netpath.Diagnostic{{
			Severity: "info",
			Code:     "snapshot.used",
			Message:  "snapshot loaded",
			Refs:     []string{"snap-1"},
		}},
	}

	result, err := toEngineAnalyzeResult(resp)
	if err != nil {
		t.Fatalf("toEngineAnalyzeResult returned error: %v", err)
	}

	resp.Traces[0].Hops[0].Steps[0].Details["destination"] = "changed"
	resp.Traces[0].Diagnostics[0].Refs[0] = "changed"
	resp.Diagnostics[0].Refs[0] = "changed"

	if got := result.Traces[0].Hops[0].Steps[0].Details["destination"]; got != "10.0.2.20" {
		t.Fatalf("expected step details to be deep copied, got %q", got)
	}
	if got := result.Traces[0].Diagnostics[0].Refs[0]; got != "r1/default" {
		t.Fatalf("expected trace diagnostic refs to be deep copied, got %q", got)
	}
	if got := result.Diagnostics[0].Refs[0]; got != "snap-1" {
		t.Fatalf("expected result diagnostic refs to be deep copied, got %q", got)
	}
}

func validRequest() netpathengine.AnalyzeRequest {
	return netpathengine.AnalyzeRequest{
		SrcIP:             "10.0.1.10",
		DstIP:             "10.0.2.20",
		Protocol:          "tcp",
		DstPort:           443,
		IngressDeviceCode: "r1",
		IngressVRF:        "default",
	}
}

func deliveredSnapshot() netpath.Snapshot {
	return netpath.Snapshot{
		SnapshotID: "snap-1",
		TenantCode: "tenant-a",
		Devices: []netpath.Device{
			{
				DeviceCode: "r1",
				DeviceName: "edge-r1",
				DeviceType: "router",
				Interfaces: []netpath.Interface{
					{InterfaceName: "ge-0/0/0", VRF: "default", IPv4Addresses: []string{"10.0.1.1/24"}, Status: "up"},
					{InterfaceName: "ge-0/0/1", VRF: "default", IPv4Addresses: []string{"192.0.2.1/30"}, Status: "up"},
				},
				RouteTables: []netpath.RouteTable{{
					VRF: "default",
					Routes: []netpath.Route{{
						Destination:  "10.0.2.0/24",
						NextHopIP:    "192.0.2.2",
						OutInterface: "ge-0/0/1",
						Protocol:     "static",
					}},
				}},
			},
			{
				DeviceCode: "r2",
				DeviceName: "app-r2",
				DeviceType: "router",
				Interfaces: []netpath.Interface{
					{InterfaceName: "ge-0/0/0", VRF: "default", IPv4Addresses: []string{"192.0.2.2/30"}, Status: "up"},
					{InterfaceName: "ge-0/0/1", VRF: "default", IPv4Addresses: []string{"10.0.2.1/24"}, Status: "up"},
				},
				RouteTables: []netpath.RouteTable{{
					VRF: "default",
					Routes: []netpath.Route{{
						Destination:  "10.0.2.0/24",
						OutInterface: "ge-0/0/1",
						Protocol:     "connected",
					}},
				}},
			},
		},
		Links: []netpath.Link{{
			ADeviceCode: "r1",
			AInterface:  "ge-0/0/1",
			BDeviceCode: "r2",
			BInterface:  "ge-0/0/0",
			Source:      "test",
		}},
	}
}
```

- [ ] **Step 2: Verify default build still ignores SDK tests**

Run from `/Users/huangliang/project/OneOPS-ALL/OneOPS`:

```bash
go test -count=1 ./app/netpath/adapter/oneopsnetpath
```

Expected: PASS with no SDK tests compiled.

- [ ] **Step 3: Verify tagged tests with a temporary local workspace**

Run:

```bash
tmpwork="$(mktemp -d)"
cd "$tmpwork"
go work init /Users/huangliang/project/OneOPS-ALL/OneOPS /Users/huangliang/project/OneOPS-ALL/oneops-netpath
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
GOWORK="$tmpwork/go.work" go test -tags oneops_netpath_sdk -count=1 ./app/netpath/adapter/oneopsnetpath
```

Expected: PASS. The temporary `go.work` lives outside the repository and must not be committed.

## Task 4: Run NetPath Boundary Verification

**Files:**
- No source changes unless verification exposes a real adapter bug.

- [ ] **Step 1: Run default NetPath test set**

Run from `/Users/huangliang/project/OneOPS-ALL/OneOPS`:

```bash
go test -count=1 ./app/netpath/adapter/oneopsnetpath ./app/netpath/engine ./app/netpath/service/impl
```

Expected: PASS.

Run:

```bash
go test -count=1 ./app/netpath/snapshot ./app/netpath/dto ./app/netpath/engine ./app/netpath/service ./app/netpath/service/impl ./app/netpath/api ./app/netpath/adapter/oneopsnetpath
```

Expected: PASS.

- [ ] **Step 2: Confirm dependency boundary**

Run from `/Users/huangliang/project/OneOPS-ALL/OneOPS`:

```bash
git diff -- go.mod go.sum
```

Expected: no output.

Run:

```bash
rg -n "replace github.com/netxops/oneops-netpath" go.mod
```

Expected: no output and exit code 1 is acceptable.

Run:

```bash
rg -n "github.com/netxops/oneops-netpath" app/netpath
```

Expected: matches only `app/netpath/adapter/oneopsnetpath/adapter_sdk.go` and `app/netpath/adapter/oneopsnetpath/adapter_sdk_test.go`.

- [ ] **Step 3: Inspect git status and stage only adapter files**

Run:

```bash
git status --short
```

Expected: existing unrelated dirty files may remain. Stage only:

```bash
git add app/netpath/adapter/oneopsnetpath/doc.go app/netpath/adapter/oneopsnetpath/adapter_sdk.go app/netpath/adapter/oneopsnetpath/adapter_sdk_test.go
```

- [ ] **Step 4: Commit the adapter scaffold**

Run:

```bash
git commit -m "feat: scaffold netpath sdk adapter"
```

Expected: commit contains only files under `app/netpath/adapter/oneopsnetpath`.

## Self-Review Checklist

- The adapter source is dormant unless `oneops_netpath_sdk` is set.
- The default package file imports no standalone SDK dependency.
- The tagged implementation maps request, flow, traces, hops, steps, diagnostics, details, and top-level disposition.
- The adapter requires a `SnapshotProvider` and does not call the current DC2 preview `SnapshotBuilder`.
- The tests use an engine-ready `netpath.Snapshot` with route tables and topology links.
- No `go.mod`, `go.sum`, `go.work`, or `replace` change is required.
