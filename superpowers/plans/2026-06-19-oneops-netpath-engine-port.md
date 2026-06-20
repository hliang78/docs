# OneOPS NetPath Engine Port Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move OneOPS NetPath's `AnalysisEngine` contract out of `service/impl` into a stable `app/netpath/engine` port package with independent request/result types and without changing runtime behavior.

**Architecture:** `app/netpath/engine` owns the engine port interface and domain-shaped request/result structs. `app/netpath/service/impl` continues to orchestrate analysis runs and keeps `WithAnalysisEngine`, but it now depends on `engine.AnalysisEngine` and maps between service DTOs and engine port types. This slice intentionally avoids `go.mod`, SDK adapter, `go.work`, and DC2 route-fact changes.

**Tech Stack:** Go 1.25.5, existing OneOPS NetPath DTOs, standard `testing`, existing service option pattern.

---

## File Structure

`/Users/huangliang/project/OneOPS-ALL/OneOPS/app/netpath/engine/engine.go`

- New port package.
- Defines `AnalysisEngine` interface and engine request/result types.
- Imports only `context`.

`/Users/huangliang/project/OneOPS-ALL/OneOPS/app/netpath/service/impl/netpath.go`

- Removes local `AnalysisEngine` interface.
- Imports `app/netpath/engine`.
- Changes `analysisEngine` field and `WithAnalysisEngine` parameter to `engine.AnalysisEngine`.
- Adds DTO-to-engine and engine-to-DTO mapper helpers.
- Keeps all analysis run behavior unchanged.

`/Users/huangliang/project/OneOPS-ALL/OneOPS/app/netpath/service/impl/netpath_test.go`

- Adds compile-time assertion that `fakeAnalysisEngine` implements `engine.AnalysisEngine`.
- Keeps all behavior tests passing.

No `go.mod`, `go.sum`, `app/netpath/snapshot`, API DTO, router, wire, or DC2 files are changed.

---

### Task 1: Extract Engine Port

**Files:**
- Create: `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/netpath/engine/engine.go`
- Modify: `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/netpath/service/impl/netpath.go`
- Modify: `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/netpath/service/impl/netpath_test.go`

- [ ] **Step 1: Write the port package**

Create `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/netpath/engine/engine.go`:

```go
package engine

import "context"

type AnalysisEngine interface {
	Analyze(ctx context.Context, req AnalyzeRequest) (*AnalyzeResult, error)
}

type AnalyzeRequest struct {
	TenantCode        string
	SnapshotID        string
	SrcIP             string
	DstIP             string
	Protocol          string
	SrcPort           int
	DstPort           int
	IngressDeviceCode string
	IngressInterface  string
	IngressVRF        string
	BusinessLabel     string
}

type AnalyzeResult struct {
	SnapshotID  string
	Flow        Flow
	Disposition string
	Traces      []Trace
	Diagnostics []Diagnostic
}

type Flow struct {
	SrcIP             string
	DstIP             string
	Protocol          string
	SrcPort           int
	DstPort           int
	IngressDeviceCode string
	IngressInterface  string
	IngressVRF        string
	BusinessLabel     string
}

type Trace struct {
	TraceID     string
	Disposition string
	Hops        []Hop
	Diagnostics []Diagnostic
	Confidence  string
}

type Hop struct {
	Sequence     int
	DeviceCode   string
	InInterface  string
	OutInterface string
	InZone       string
	OutZone      string
	VRF          string
	Steps        []Step
}

type Step struct {
	Type          string
	Action        string
	MatchedObject string
	RawRef        string
	Message       string
	Details       map[string]string
}

type Diagnostic struct {
	Severity string
	Code     string
	Message  string
	Refs     []string
}
```

- [ ] **Step 2: Update the service implementation to use the port**

In `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/netpath/service/impl/netpath.go`, add the import:

```go
netpathengine "github.com/netxops/OneOps/app/netpath/engine"
```

Change the service field from:

```go
analysisEngine  AnalysisEngine
```

to:

```go
analysisEngine  netpathengine.AnalysisEngine
```

Delete the local interface:

```go
type AnalysisEngine interface {
	Analyze(ctx context.Context, req dto.AnalyzeRunCreateReq) (*dto.AnalyzeResult, string, error)
}
```

Change `WithAnalysisEngine` from:

```go
func WithAnalysisEngine(engine AnalysisEngine) Option {
	return func(s *NetPathService) {
		s.analysisEngine = engine
	}
}
```

to:

```go
func WithAnalysisEngine(engine netpathengine.AnalysisEngine) Option {
	return func(s *NetPathService) {
		s.analysisEngine = engine
	}
}
```

Update the engine call in `buildAnalyzeRunResp` to:

```go
result, err := s.analysisEngine.Analyze(ctx, toEngineAnalyzeRequest(req))
```

Use only `strings.TrimSpace(result.Disposition)` as the run-level disposition. If the trimmed value is empty, store a failed run with `Disposition: "engine_error"` and `Error: "analysis engine returned empty disposition"`.

Add mapper helpers:

```go
func toEngineAnalyzeRequest(req dto.AnalyzeRunCreateReq) netpathengine.AnalyzeRequest
func toDTOAnalyzeResult(result *netpathengine.AnalyzeResult) *dto.AnalyzeResult
```

The result mapper must deep-copy slices and `Step.Details` maps so later engine-side mutations cannot change stored run results.

- [ ] **Step 3: Add a compile-time test assertion**

In `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/netpath/service/impl/netpath_test.go`, add this import:

```go
netpathengine "github.com/netxops/OneOps/app/netpath/engine"
```

After `fakeAnalysisEngine.Analyze`, add:

```go
var _ netpathengine.AnalysisEngine = (*fakeAnalysisEngine)(nil)
```

Update `fakeAnalysisEngine` to store and return engine port types:

```go
type fakeAnalysisEngine struct {
	result *netpathengine.AnalyzeResult
	err    error
	req    netpathengine.AnalyzeRequest
}

func (f *fakeAnalysisEngine) Analyze(ctx context.Context, req netpathengine.AnalyzeRequest) (*netpathengine.AnalyzeResult, error) {
	_ = ctx
	f.req = req
	return f.result, f.err
}
```

Update tests so engine success uses `netpathengine.AnalyzeResult.Disposition` as the only run-level disposition source. The empty-disposition test should fail even when a trace disposition is present.

- [ ] **Step 4: Format and run targeted tests**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
gofmt -w app/netpath/engine/engine.go app/netpath/service/impl/netpath.go app/netpath/service/impl/netpath_test.go
go test -count=1 ./app/netpath/engine ./app/netpath/service/impl
```

Expected: both packages pass. `app/netpath/engine` may report `[no test files]`.

- [ ] **Step 5: Run NetPath regression tests**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test -count=1 ./app/netpath/snapshot ./app/netpath/dto ./app/netpath/engine ./app/netpath/service ./app/netpath/service/impl ./app/netpath/api
go test -race -count=1 ./app/netpath/service/impl
```

Expected: all listed packages pass; `app/netpath/service` and `app/netpath/engine` may have no test files.

- [ ] **Step 6: Verify dependency boundaries**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
git diff -- go.mod go.sum
rg -n "oneops-netpath|github.com/netxops/oneops-netpath|replace github.com/netxops/oneops-netpath" app/netpath go.mod
```

Expected:

- `git diff -- go.mod go.sum` prints no diff.
- `rg` does not find an active OneOPS import or dependency on `oneops-netpath`; matches inside documentation are outside this command scope and are irrelevant.

- [ ] **Step 7: Commit**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
git add app/netpath/engine/engine.go app/netpath/service/impl/netpath.go app/netpath/service/impl/netpath_test.go
git commit -m "refactor: extract netpath analysis engine port"
```

Expected: commit created. Do not stage unrelated dirty files outside `app/netpath`.

---

## Self-Review

Spec coverage:

- `AnalysisEngine` is no longer private to `service/impl`: Task 1 steps 1-2.
- `NetPathService` depends on `app/netpath/engine.AnalysisEngine`: Task 1 step 2.
- Engine port does not import API DTOs: Task 1 step 1.
- Service owns DTO mapping and run-level disposition comes from `engine.AnalyzeResult.Disposition`: Task 1 steps 2-3.
- Existing behavior remains unchanged: Task 1 steps 4-5.
- No `oneops-netpath` dependency or `replace`: Task 1 step 6.
- No DC2 preview or route-fact changes: file structure and task scope exclude those files.

Placeholder scan:

- No placeholders remain. Every step has exact files, code snippets, commands, and expected results.

Type consistency:

- The interface signature is:
  `Analyze(ctx context.Context, req engine.AnalyzeRequest) (*engine.AnalyzeResult, error)`.
- `WithAnalysisEngine` keeps its name and option behavior, changing only the imported interface type.
