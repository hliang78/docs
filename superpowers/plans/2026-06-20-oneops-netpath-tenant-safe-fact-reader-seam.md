# OneOPS NetPath Tenant-Safe Fact Reader Seam Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a small NetPath provider seam that consumes DC2 latest facts only with explicit tenant and device scope, so production NetPath paths do not rely on unscoped `ListLatestFacts("", fact_type, ...)` reads.

**Architecture:** Keep the existing DC2 public latest-fact API unchanged in this phase. Add a NetPath-side provider adapter under `app/netpath/snapshot/provider` that requires `tenant_code` and explicit `device_codes`, reads each supported fact type per device, assembles an `AnalysisSnapshot`, and runs the existing validator. Leave `app/netpath/snapshot/builder.go` as preview-only.

**Tech Stack:** Go, existing DC2 `FactRecordResp`, existing NetPath snapshot provider `Assembler` and `Validator`, existing Go tests.

---

## Scope

In scope:

- fail closed when `tenant_code` is blank
- fail closed when explicit `device_codes` are missing
- avoid every unscoped latest-fact read in this provider
- read latest facts per target and fact type
- assemble and validate the result using existing provider components
- keep preview builder behavior unchanged and documented as preview-only

Out of scope:

- changing `IDeviceCollection2.ListLatestFacts`
- adding tenant columns to latest fact tables
- resolving tenant-owned device scope from RBAC or policy scope
- wiring the provider into durable NetPath runs
- mapping `AnalysisSnapshot` into the external `oneops-netpath` SDK model

## Caller Contract

The seam is tenant-safe only when the caller supplies an already authorized device scope:

```text
tenant_code must identify the request tenant
device_codes must be resolved before calling the provider
device_codes must contain only devices that the tenant is authorized to analyze
the provider does not infer tenant membership from DC2 latest facts
the provider does not filter by tenant inside ListLatestFacts because that API is not tenant-keyed yet
```

For Phase 5, NetPath should accept explicit device codes only. A future tenant/device scope resolver may expand policies, topology neighborhoods, or application groups, but that resolver must sit before `LatestFactSnapshotProvider.Build(...)`.

## Files

- Create: `OneOPS/app/netpath/snapshot/provider/latest_fact_provider.go`
- Create: `OneOPS/app/netpath/snapshot/provider/latest_fact_provider_test.go`
- Modify: `docs/superpowers/specs/2026-06-19-oneops-canonical-fact-inventory.md`
- Modify: `docs/superpowers/plans/2026-06-19-oneops-netpath-master-roadmap.md`

## Task 1: Add Failing Provider Seam Tests

- [x] **Step 1: Add a fake latest fact reader and scope rejection tests**

Create `OneOPS/app/netpath/snapshot/provider/latest_fact_provider_test.go` with tests:

```go
func TestLatestFactSnapshotProviderRequiresTenantAndDeviceScope(t *testing.T)
```

Expected behavior:

```text
nil provider or nil reader returns error containing "latest fact reader is required"
blank tenant_code returns error containing "tenant_code is required"
blank or all-empty device_codes returns error containing "device_codes are required"
reader is not called on either failure
```

- [x] **Step 2: Add scoped read and assembly test**

In the same file add:

```go
func TestLatestFactSnapshotProviderReadsLatestFactsPerDeviceAndFactType(t *testing.T)
```

Expected behavior:

```text
request tenant_code is trimmed
device_codes are trimmed and de-duplicated
reader is called with target_id set to each device code, never empty
reader is called for device_identity, interface, interface_ip, topology_neighbor, route_table, server_route
assembled snapshot contains only requested devices
route_table facts are assembled into AnalysisRouteTable
validator quality is ready when ingress route table is present
```

- [x] **Step 3: Run red tests**

Run:

```bash
cd /Users/huangliang/.config/superpowers/worktrees/OneOPS/codex/fact-contract-hardening-phase1
/usr/local/go/bin/go test ./app/netpath/snapshot/provider -run 'TestLatestFactSnapshotProvider' -count=1
```

Expected:

```text
FAIL because NewLatestFactSnapshotProvider and request types do not exist
```

Observed:

```text
FAIL with undefined: NewLatestFactSnapshotProvider and undefined: LatestFactSnapshotRequest
```

## Task 2: Implement Minimal Provider Seam

- [x] **Step 1: Add provider request and reader types**

Create `OneOPS/app/netpath/snapshot/provider/latest_fact_provider.go` with:

```go
type LatestFactReader interface {
    ListLatestFacts(ctx context.Context, targetID string, factType string, validOnly bool, limit int) ([]dc2dto.FactRecordResp, error)
}

type LatestFactSnapshotRequest struct {
    TenantCode        string
    SnapshotID        string
    DeviceCodes       []string
    IngressDeviceCode string
    IngressVRF        string
    GeneratedAt       time.Time
}
```

- [x] **Step 2: Add constructor and build method**

Expected method:

```go
func NewLatestFactSnapshotProvider(reader LatestFactReader) *LatestFactSnapshotProvider
func (p *LatestFactSnapshotProvider) Build(ctx context.Context, req LatestFactSnapshotRequest) (*AnalysisSnapshot, error)
```

Behavior:

```text
return error if reader is nil
trim tenant_code and require non-empty
trim/dedupe device_codes and require non-empty
for each device and fact type, call ListLatestFacts(ctx, device, fact_type, true, 1000)
assemble the FactSet with NewAssembler()
validate with NewValidator() and request ingress fields
```

- [x] **Step 3: Run provider seam tests**

Run:

```bash
/usr/local/go/bin/go test ./app/netpath/snapshot/provider -run 'TestLatestFactSnapshotProvider' -count=1
```

Expected:

```text
ok
```

Observed:

```text
/usr/local/go/bin/go test ./app/netpath/snapshot/provider -run 'TestLatestFactSnapshotProvider' -count=1
ok
```

Review follow-up:

```text
TestLatestFactSnapshotProviderRequiresTenantAndDeviceScope now also covers nil provider and nil reader fail-closed paths.
```

## Task 3: Verify Existing Preview Boundary Still Holds

- [x] **Step 1: Run existing preview builder tests**

Run:

```bash
/usr/local/go/bin/go test ./app/netpath/snapshot ./app/netpath/snapshot/provider -count=1
```

Expected:

```text
ok
```

- [x] **Step 2: Confirm preview still performs preview-only reads**

Run:

```bash
rg -n 'ListLatestFacts\\(ctx, "",' app/netpath/snapshot/builder.go
```

Expected:

```text
builder.go still contains unscoped reads and remains preview-only; production seam is in provider/latest_fact_provider.go
```

Observed:

```text
/usr/local/go/bin/go test ./app/netpath/snapshot ./app/netpath/snapshot/provider -count=1
ok

rg -n 'ListLatestFacts\(ctx, "",' app/netpath/snapshot/builder.go
shows only preview builder reads for interface, interface_ip, and topology_neighbor.
```

## Task 4: Update Status Docs

- [x] **Step 1: Update inventory**

Modify `docs/superpowers/specs/2026-06-19-oneops-canonical-fact-inventory.md` to record:

```text
NetPath now has a provider-side tenant-safe latest-fact reader seam.
Residual gap: caller still must resolve tenant-authorized device_codes before invoking the seam.
```

- [x] **Step 2: Update NetPath roadmap**

Modify `docs/superpowers/plans/2026-06-19-oneops-netpath-master-roadmap.md` to record:

```text
Phase 2/3 provider work includes a tenant-safe latest-fact seam.
Preview builder remains preview-only.
Durable run wiring remains pending.
```

- [x] **Step 3: Record caller authorization contract**

Documented that callers must pre-resolve tenant-authorized `device_codes` before invoking `LatestFactSnapshotProvider.Build(...)`. The provider enforces non-empty tenant/scope and scoped reads, but does not infer authorization from DC2 latest facts.

## Task 5: Add Service Error Propagation Guardrail

- [x] **Step 1: Add strict scope propagation test**

Added:

```go
func TestNetPathServicePreviewSnapshotPropagatesStrictScopeError(t *testing.T)
```

Expected behavior:

```text
when an injected strict builder/provider rejects missing device scope with "device_codes are required",
PreviewSnapshot returns that exact error and does not fall back to metadata-only preview.
```

- [x] **Step 2: Run focused service test**

Run:

```bash
/usr/local/go/bin/go test ./app/netpath/service/impl -run 'TestNetPathServicePreviewSnapshotPropagatesStrictScopeError|TestNetPathServicePreviewSnapshotPropagatesBuilderError' -count=1
```

Observed:

```text
ok
```

## Task 6: Carry Explicit Device Scope Into Durable Analyze Requests

- [x] **Step 1: Add failing service contract test**

Extended:

```go
func TestNetPathServiceCreateAnalyzeRunUsesConfiguredEngine(t *testing.T)
```

Expected behavior:

```text
AnalyzeRunCreateReq accepts device_codes
device_codes are trimmed, de-duplicated, and order-preserving
engine.AnalyzeRequest receives the normalized device scope
```

Observed red test:

```text
unknown field DeviceCodes in dto.AnalyzeRunCreateReq
engine.req.DeviceCodes undefined
```

- [x] **Step 2: Add request and engine fields**

Implemented:

```text
dto.AnalyzeRunCreateReq.DeviceCodes []string `json:"device_codes,omitempty"`
engine.AnalyzeRequest.DeviceCodes []string
NetPathService.normalizeAnalyzeRunCreateReq trims and de-duplicates device codes
toEngineAnalyzeRequest copies device codes into the engine request
```

- [x] **Step 3: Add mutation isolation guardrail**

Extended:

```go
func TestNetPathServiceRunResponsesAreMutationIsolated(t *testing.T)
```

Expected behavior:

```text
mutating a returned AnalyzeRunResp.Request.DeviceCodes slice must not mutate the stored run
```

- [x] **Step 4: Run focused service tests**

Run:

```bash
/usr/local/go/bin/go test ./app/netpath/service/impl -run 'TestNetPathServiceCreateAnalyzeRunUsesConfiguredEngine|TestNetPathServiceRunResponsesAreMutationIsolated' -count=1
/usr/local/go/bin/go test ./app/netpath/service/impl -count=1
```

Observed:

```text
ok
ok
```

- [x] **Step 5: Address review follow-up on preview/analyze scope normalization**

Independent review noted that preview builder requests previously used `trim + drop empty` while durable analyze requests used `trim + drop empty + de-duplicate`. The service now uses the same order-preserving normalization before invoking a configured preview builder/provider and before invoking the analysis engine.

The metadata-only preview fallback still preserves the original input device count because that path is a legacy placeholder count, not a scoped provider call.

Run:

```bash
/usr/local/go/bin/go test ./app/netpath/service/impl -run 'TestNetPathServicePreviewSnapshotUsesConfiguredBuilder|TestNetPathServiceCreateAnalyzeRunUsesConfiguredEngine|TestNetPathServicePreviewSnapshotFallbackPreservesOriginalDeviceCount' -count=1
```

Observed:

```text
ok
```

Residual gap:

```text
Durable analysis requests can now carry explicit device scope to the engine port.
The next gap is wiring a provider-backed engine or adapter that converts that scope into LatestFactSnapshotProvider.Build(...), then maps AnalysisSnapshot into the selected analysis engine snapshot model.
```

## Task 7: Add Build-Tagged Provider-Backed SDK Snapshot Provider

- [x] **Step 1: Add failing tagged adapter tests**

Created:

```go
//go:build oneops_netpath_sdk
func TestProviderSnapshotProviderMapsScopedAnalysisSnapshot(t *testing.T)
func TestProviderSnapshotProviderPropagatesSourceErrors(t *testing.T)
func TestProviderSnapshotProviderRejectsBlockedAnalysisSnapshot(t *testing.T)
```

Expected behavior:

```text
engine.AnalyzeRequest device_codes are copied into LatestFactSnapshotRequest
AnalysisSnapshot maps to oneops-netpath/pkg/netpath.Snapshot
GeneratedAt uses RFC3339
SourceVersions maps config/topology/collection refs
devices/interfaces/routes/links/diagnostics are deep copied
blocked analysis snapshots fail closed before SDK analysis
source provider errors are wrapped and preserved
```

Observed red test:

```text
undefined: NewProviderSnapshotProvider
undefined: errBlockedAnalysisSnapshot
```

- [x] **Step 2: Implement tagged provider adapter**

Added:

```text
app/netpath/adapter/oneopsnetpath/provider_sdk.go
```

Implemented:

```text
AnalysisSnapshotProvider interface
NewProviderSnapshotProvider(...)
ProviderSnapshotProvider.GetSnapshot(...)
AnalysisSnapshot -> netpath.Snapshot mapper
blocked snapshot quality guard
```

The implementation is guarded by `//go:build oneops_netpath_sdk`, so default OneOPS builds still do not require `github.com/netxops/oneops-netpath`.

- [x] **Step 3: Fix tagged adapter request comparison after DeviceCodes**

`engine.AnalyzeRequest` now contains `[]string`, so the existing tagged adapter test can no longer compare request structs with `!=`. The test now uses `reflect.DeepEqual`.

- [x] **Step 4: Verify tagged and default adapter paths**

Run with a temporary local workspace:

```bash
tmpwork="$(mktemp -d)"
cd "$tmpwork"
/usr/local/go/bin/go work init \
  /Users/huangliang/.config/superpowers/worktrees/OneOPS/codex/fact-contract-hardening-phase1 \
  /Users/huangliang/project/OneOPS-ALL/oneops-netpath
cd /Users/huangliang/.config/superpowers/worktrees/OneOPS/codex/fact-contract-hardening-phase1
GOWORK="$tmpwork/go.work" /usr/local/go/bin/go test -tags oneops_netpath_sdk -count=1 ./app/netpath/adapter/oneopsnetpath
```

Observed:

```text
ok
```

Run default build:

```bash
/usr/local/go/bin/go test -count=1 ./app/netpath/adapter/oneopsnetpath ./app/netpath/engine ./app/netpath/service/impl
```

Observed:

```text
? github.com/netxops/OneOps/app/netpath/adapter/oneopsnetpath [no test files]
? github.com/netxops/OneOps/app/netpath/engine [no test files]
ok github.com/netxops/OneOps/app/netpath/service/impl
```

- [x] **Step 5: Add tagged scoped latest-fact to SDK engine smoke**

Added:

```go
func TestProviderBackedAdapterAnalyzesScopedLatestFacts(t *testing.T)
```

The test uses fake DC2 latest facts and the real chain:

```text
fake LatestFactReader
-> snapshot/provider.NewLatestFactSnapshotProvider(...)
-> oneopsnetpath.NewProviderSnapshotProvider(...)
-> oneopsnetpath.New(...)
-> SDK Analyze(...)
```

Expected behavior:

```text
duplicate/blank device_codes are normalized to r1,r2
latest fact reads are always scoped by target_id
route/interface/topology facts assemble into an SDK-ready snapshot
the SDK engine returns delivered_to_subnet
```

Observed:

```text
GOWORK="$tmpwork/go.work" /usr/local/go/bin/go test -tags oneops_netpath_sdk -count=1 ./app/netpath/adapter/oneopsnetpath
ok
```

- [x] **Step 6: Record tagged dependency boundary and degraded quality policy**

Independent review noted that direct tagged tests fail without local module wiring:

```bash
/usr/local/go/bin/go test -tags oneops_netpath_sdk ./app/netpath/adapter/oneopsnetpath
```

This is expected for the current dependency strategy. OneOPS intentionally does not add `github.com/netxops/oneops-netpath` to default `go.mod`; tagged SDK verification must use a temporary `go.work` that includes both modules.

Added:

```go
func TestProviderSnapshotProviderAllowsDegradedAnalysisSnapshot(t *testing.T)
```

Policy:

```text
blocked AnalysisSnapshot => fail closed before SDK Analyze
degraded AnalysisSnapshot => pass through with warning diagnostics
ready AnalysisSnapshot => pass through
```

Run:

```bash
tmpwork="$(mktemp -d)"
cd "$tmpwork"
/usr/local/go/bin/go work init \
  /Users/huangliang/.config/superpowers/worktrees/OneOPS/codex/fact-contract-hardening-phase1 \
  /Users/huangliang/project/OneOPS-ALL/oneops-netpath
cd /Users/huangliang/.config/superpowers/worktrees/OneOPS/codex/fact-contract-hardening-phase1
GOWORK="$tmpwork/go.work" /usr/local/go/bin/go test -tags oneops_netpath_sdk -count=1 ./app/netpath/...
```

Observed:

```text
ok github.com/netxops/OneOps/app/netpath/adapter/oneopsnetpath
ok github.com/netxops/OneOps/app/netpath/api
ok github.com/netxops/OneOps/app/netpath/dto
?  github.com/netxops/OneOps/app/netpath/engine [no test files]
?  github.com/netxops/OneOps/app/netpath/netpath_model [no test files]
?  github.com/netxops/OneOps/app/netpath/service [no test files]
ok github.com/netxops/OneOps/app/netpath/service/impl
ok github.com/netxops/OneOps/app/netpath/snapshot
ok github.com/netxops/OneOps/app/netpath/snapshot/provider
```

Residual gap:

```text
The build-tagged adapter can now convert a scoped AnalysisSnapshot into the SDK snapshot provider contract.
Production service construction still needs explicit dependency wiring to instantiate LatestFactSnapshotProvider + NewProviderSnapshotProvider + oneopsnetpath.New(...) behind the build tag or runtime configuration.
```

## Final Verification

Run:

```bash
cd /Users/huangliang/.config/superpowers/worktrees/OneOPS/codex/fact-contract-hardening-phase1
/usr/local/go/bin/go test ./app/device_collection2/fact ./app/device_collection2/service/impl ./app/netpath/snapshot/provider ./app/netpath/snapshot ./app/netpath/service/impl -count=1
git diff --check
```

Expected:

```text
all tests pass
no whitespace errors
```
