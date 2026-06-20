# NetPath DC2 Snapshot Builder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first OneOPS Snapshot Builder slice that converts DC2 latest facts into a NetPath snapshot preview.

**Architecture:** Add an isolated `app/netpath/snapshot` package that consumes DC2 latest fact DTOs through a small reader interface, builds a local snapshot summary, and returns diagnostics for incomplete data. Wire that builder into `NetPathService.PreviewSnapshot` through an optional constructor dependency while preserving the existing metadata-only fallback.

**Tech Stack:** Go, GORM only as existing service dependency, DC2 DTOs, existing OneOPS service/API tests, no direct import of standalone `oneops-netpath`.

---

## Data Model Basis

```text
device_collection2_fact_latest
  -> dto.FactRecordResp
  -> app/netpath/snapshot.Builder
  -> snapshot.Snapshot
  -> dto.SnapshotPreviewResp
```

Supported fact types in this phase:

- `interface`
- `interface_ip`
- `topology_neighbor`

Explicitly not included:

- Route tables
- ACL/NAT/PBR/firewall policy
- Engine Runner
- Probe Orchestrator
- UI
- Router/Wire integration

## File Structure

Modify or create these files in `/Users/huangliang/project/OneOPS-ALL/OneOPS`:

- Create: `app/netpath/snapshot/types.go`
- Create: `app/netpath/snapshot/builder.go`
- Create: `app/netpath/snapshot/builder_test.go`
- Modify: `app/netpath/service/impl/netpath.go`
- Modify: `app/netpath/service/impl/netpath_test.go`

Do not modify:

- `app/device_collection2` production code
- `app/netpath/api`
- router/Wire files
- standalone `/Users/huangliang/project/OneOPS-ALL/oneops-netpath`

## Task 1: Snapshot Builder Package

**Files:**
- Create: `app/netpath/snapshot/types.go`
- Create: `app/netpath/snapshot/builder.go`
- Create: `app/netpath/snapshot/builder_test.go`

- [ ] **Step 1: Write failing builder tests**

Create `app/netpath/snapshot/builder_test.go` with tests that use a fake reader:

```go
package snapshot

import (
	"context"
	"testing"

	dc2dto "github.com/netxops/OneOps/app/device_collection2/dto"
)

type fakeLatestFactReader struct {
	byType map[string][]dc2dto.FactRecordResp
}

func (f fakeLatestFactReader) ListLatestFacts(ctx context.Context, targetID string, factType string, validOnly bool, limit int) ([]dc2dto.FactRecordResp, error) {
	_ = ctx
	_ = targetID
	_ = validOnly
	_ = limit
	return append([]dc2dto.FactRecordResp(nil), f.byType[factType]...), nil
}

func TestBuilderBuildsDevicesInterfacesIPsAndLinks(t *testing.T) {
	builder := NewBuilder(fakeLatestFactReader{byType: map[string][]dc2dto.FactRecordResp{
		"interface": {
			{
				TargetID: "r1", FactType: "interface", IdentityKey: "r1:if_index:1", Valid: true,
				Fields: map[string]interface{}{"if_index": float64(1), "if_name": "GigabitEthernet0/0", "if_name_canonical": "ge0/0", "oper_status": "up"},
			},
			{
				TargetID: "r2", FactType: "interface", IdentityKey: "r2:if_index:2", Valid: true,
				Fields: map[string]interface{}{"if_index": float64(2), "if_name_canonical": "ge0/1", "oper_status": "up"},
			},
		},
		"interface_ip": {
			{
				TargetID: "r1", FactType: "interface_ip", IdentityKey: "r1:if_index:1:ip:10.0.12.1", Valid: true,
				Fields: map[string]interface{}{"if_index": float64(1), "cidr": "10.0.12.1/30", "vrf": "default"},
			},
			{
				TargetID: "r2", FactType: "interface_ip", IdentityKey: "r2:if_index:2:ip:10.0.12.2", Valid: true,
				Fields: map[string]interface{}{"if_index": float64(2), "ip": "10.0.12.2", "prefix_len": float64(30), "vrf": "default"},
			},
		},
		"topology_neighbor": {
			{
				TargetID: "r1", FactType: "topology_neighbor", IdentityKey: "r1:if_index:1:neighbor:r2", Valid: true,
				Fields: map[string]interface{}{"if_index": float64(1), "remote_device": "r2", "remote_if_name_canonical": "ge0/1", "protocol": "lldp"},
			},
		},
	}})

	snap, err := builder.BuildPreview(context.Background(), BuildRequest{TenantCode: "tenant-a"})
	if err != nil {
		t.Fatalf("BuildPreview returned error: %v", err)
	}
	if snap.SnapshotID != "dc2-preview-tenant-a" {
		t.Fatalf("unexpected snapshot id %q", snap.SnapshotID)
	}
	if len(snap.Devices) != 2 {
		t.Fatalf("expected 2 devices, got %d", len(snap.Devices))
	}
	r1 := findDevice(t, snap, "r1")
	if len(r1.Interfaces) != 1 {
		t.Fatalf("expected r1 interface, got %#v", r1.Interfaces)
	}
	if r1.Interfaces[0].InterfaceName != "ge0/0" {
		t.Fatalf("expected canonical interface name ge0/0, got %q", r1.Interfaces[0].InterfaceName)
	}
	if len(r1.Interfaces[0].IPv4Addresses) != 1 || r1.Interfaces[0].IPv4Addresses[0] != "10.0.12.1/30" {
		t.Fatalf("unexpected r1 addresses: %#v", r1.Interfaces[0].IPv4Addresses)
	}
	if len(snap.Links) != 1 {
		t.Fatalf("expected one link, got %#v", snap.Links)
	}
	if snap.Links[0].ADeviceCode != "r1" || snap.Links[0].BDeviceCode != "r2" || snap.Links[0].Source != "lldp" {
		t.Fatalf("unexpected link: %#v", snap.Links[0])
	}
}

func TestBuilderCreatesInferredInterfaceForOrphanIP(t *testing.T) {
	builder := NewBuilder(fakeLatestFactReader{byType: map[string][]dc2dto.FactRecordResp{
		"interface_ip": {
			{
				TargetID: "r1", FactType: "interface_ip", IdentityKey: "r1:if_name:loop0:ip:192.0.2.1", Valid: true,
				Fields: map[string]interface{}{"if_name_canonical": "loop0", "cidr": "192.0.2.1/32"},
			},
		},
	}})

	snap, err := builder.BuildPreview(context.Background(), BuildRequest{TenantCode: "tenant-a"})
	if err != nil {
		t.Fatalf("BuildPreview returned error: %v", err)
	}
	r1 := findDevice(t, snap, "r1")
	if len(r1.Interfaces) != 1 || r1.Interfaces[0].InterfaceName != "loop0" {
		t.Fatalf("expected inferred loop0 interface, got %#v", r1.Interfaces)
	}
	if !hasDiagnostic(snap, "interface_ip_without_interface") {
		t.Fatalf("expected interface_ip_without_interface diagnostic, got %#v", snap.Diagnostics)
	}
}

func TestBuilderEmitsDiagnosticForUnresolvedTopology(t *testing.T) {
	builder := NewBuilder(fakeLatestFactReader{byType: map[string][]dc2dto.FactRecordResp{
		"interface": {
			{
				TargetID: "r1", FactType: "interface", IdentityKey: "r1:if_name:ge0/0", Valid: true,
				Fields: map[string]interface{}{"if_name_canonical": "ge0/0"},
			},
		},
		"topology_neighbor": {
			{
				TargetID: "r1", FactType: "topology_neighbor", IdentityKey: "bad-neighbor", Valid: true,
				Fields: map[string]interface{}{"if_name_canonical": "ge0/0", "remote_device": "r9", "remote_if_name_canonical": "ge0/9"},
			},
		},
	}})

	snap, err := builder.BuildPreview(context.Background(), BuildRequest{TenantCode: "tenant-a"})
	if err != nil {
		t.Fatalf("BuildPreview returned error: %v", err)
	}
	if len(snap.Links) != 0 {
		t.Fatalf("expected no links, got %#v", snap.Links)
	}
	if !hasDiagnostic(snap, "topology_remote_unresolved") {
		t.Fatalf("expected topology_remote_unresolved diagnostic, got %#v", snap.Diagnostics)
	}
}

func TestBuilderFiltersDeviceCodes(t *testing.T) {
	builder := NewBuilder(fakeLatestFactReader{byType: map[string][]dc2dto.FactRecordResp{
		"interface": {
			{TargetID: "r1", FactType: "interface", IdentityKey: "r1:if_name:ge0/0", Valid: true, Fields: map[string]interface{}{"if_name_canonical": "ge0/0"}},
			{TargetID: "r2", FactType: "interface", IdentityKey: "r2:if_name:ge0/1", Valid: true, Fields: map[string]interface{}{"if_name_canonical": "ge0/1"}},
		},
	}})

	snap, err := builder.BuildPreview(context.Background(), BuildRequest{TenantCode: "tenant-a", DeviceCodes: []string{"r2"}})
	if err != nil {
		t.Fatalf("BuildPreview returned error: %v", err)
	}
	if len(snap.Devices) != 1 || snap.Devices[0].DeviceCode != "r2" {
		t.Fatalf("expected only r2, got %#v", snap.Devices)
	}
}
```

Include small local helpers in the test file:

```go
func findDevice(t *testing.T, snap *Snapshot, code string) Device {
	t.Helper()
	for _, device := range snap.Devices {
		if device.DeviceCode == code {
			return device
		}
	}
	t.Fatalf("device %s not found in %#v", code, snap.Devices)
	return Device{}
}

func hasDiagnostic(snap *Snapshot, code string) bool {
	for _, diagnostic := range snap.Diagnostics {
		if diagnostic.Code == code {
			return true
		}
	}
	return false
}
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
go test ./app/netpath/snapshot
```

Expected: FAIL because package/types do not exist yet.

- [ ] **Step 3: Add snapshot types**

Create `app/netpath/snapshot/types.go`:

```go
package snapshot

type BuildRequest struct {
	TenantCode  string
	DeviceCodes []string
}

type Snapshot struct {
	SnapshotID   string
	TenantCode   string
	Devices      []Device
	Links        []Link
	Diagnostics  []Diagnostic
}

type Device struct {
	DeviceCode string
	Interfaces []Interface
}

type Interface struct {
	InterfaceCode  string
	InterfaceName  string
	VRF            string
	IPv4Addresses  []string
	Status         string
}

type Link struct {
	ADeviceCode string
	AInterface  string
	BDeviceCode string
	BInterface  string
	Source      string
}

type Diagnostic struct {
	Severity string
	Code     string
	Message  string
	Refs     []string
}
```

- [ ] **Step 4: Implement builder**

Create `app/netpath/snapshot/builder.go` with:

```go
package snapshot

import (
	"context"
	"fmt"
	"sort"
	"strconv"
	"strings"

	dc2dto "github.com/netxops/OneOps/app/device_collection2/dto"
)

const latestFactLimit = 1000

type LatestFactReader interface {
	ListLatestFacts(ctx context.Context, targetID string, factType string, validOnly bool, limit int) ([]dc2dto.FactRecordResp, error)
}

type Builder struct {
	reader LatestFactReader
}

func NewBuilder(reader LatestFactReader) *Builder {
	return &Builder{reader: reader}
}

func (b *Builder) BuildPreview(ctx context.Context, req BuildRequest) (*Snapshot, error) {
	tenant := strings.TrimSpace(req.TenantCode)
	if tenant == "" {
		return nil, fmt.Errorf("tenant_code is required")
	}
	if b == nil || b.reader == nil {
		return nil, fmt.Errorf("dc2 latest fact reader is required")
	}

	deviceFilter := makeDeviceFilter(req.DeviceCodes)
	interfaceFacts, err := b.reader.ListLatestFacts(ctx, "", "interface", true, latestFactLimit)
	if err != nil {
		return nil, err
	}
	interfaceIPFacts, err := b.reader.ListLatestFacts(ctx, "", "interface_ip", true, latestFactLimit)
	if err != nil {
		return nil, err
	}
	topologyFacts, err := b.reader.ListLatestFacts(ctx, "", "topology_neighbor", true, latestFactLimit)
	if err != nil {
		return nil, err
	}

	state := newBuildState(tenant, deviceFilter)
	state.addInterfaces(interfaceFacts)
	state.addInterfaceIPs(interfaceIPFacts)
	state.addTopology(topologyFacts)
	return state.snapshot(), nil
}
```

Implement private helpers in the same file:

- `buildState`
- `deviceState`
- `interfaceKey`
- `addInterfaces`
- `addInterfaceIPs`
- `addTopology`
- `snapshot`
- `makeDeviceFilter`
- `factAllowed`
- `stringField`
- `intFieldString`
- `interfaceJoinKey`
- `interfaceName`
- `statusField`
- `cidrField`
- `dedupeAppend`

Implementation rules:

- Use `TargetID` as `DeviceCode`.
- Use `identity_key` as fallback `InterfaceCode`.
- Join interface and interface_ip by `if_index` first, then `if_name_canonical`, then `if_name`, then identity key.
- Prefer `if_name_canonical`, then `if_name`, then `identity_key` for `InterfaceName`.
- For IPs, prefer `cidr`; otherwise build `ip/prefix_len`.
- If an IP fact cannot join an interface, create an inferred interface and add diagnostic `interface_ip_without_interface`.
- Only create topology links when local interface and remote device/interface exist in the built snapshot.
- Add diagnostic `topology_remote_unresolved` when topology fact cannot become a link.
- Add diagnostic `dc2_facts_empty` if all three fact lists are empty.
- Add diagnostic `route_table_missing` whenever devices exist, because routes are out of this MVP.
- Sort devices, interfaces, links, and diagnostics deterministically for test stability.

- [ ] **Step 5: Run snapshot tests**

Run:

```bash
go test ./app/netpath/snapshot
```

Expected: PASS.

- [ ] **Step 6: Commit Task 1**

Run:

```bash
git add app/netpath/snapshot
git commit -m "feat: build netpath snapshots from dc2 facts"
```

## Task 2: NetPath Service Preview Integration

**Files:**
- Modify: `app/netpath/service/impl/netpath.go`
- Modify: `app/netpath/service/impl/netpath_test.go`

- [ ] **Step 1: Add failing service test for builder-backed preview**

Append a test in `app/netpath/service/impl/netpath_test.go`:

```go
type fakeSnapshotBuilder struct {
	snapshot *snapshot.Snapshot
	err      error
	req      snapshot.BuildRequest
}

func (f *fakeSnapshotBuilder) BuildPreview(ctx context.Context, req snapshot.BuildRequest) (*snapshot.Snapshot, error) {
	_ = ctx
	f.req = req
	return f.snapshot, f.err
}

func TestNetPathServicePreviewSnapshotUsesConfiguredBuilder(t *testing.T) {
	builder := &fakeSnapshotBuilder{snapshot: &snapshot.Snapshot{
		SnapshotID: "dc2-preview-demo",
		TenantCode: "demo",
		Devices: []snapshot.Device{
			{DeviceCode: "r1"},
			{DeviceCode: "r2"},
		},
		Links: []snapshot.Link{
			{ADeviceCode: "r1", AInterface: "ge0/0", BDeviceCode: "r2", BInterface: "ge0/1", Source: "lldp"},
		},
		Diagnostics: []snapshot.Diagnostic{
			{Severity: "warn", Code: "route_table_missing", Message: "route tables are not available in snapshot builder MVP"},
		},
	}}
	svc := NewNetPathService(nil, WithSnapshotBuilder(builder))

	resp, err := svc.PreviewSnapshot(context.Background(), dto.SnapshotPreviewReq{
		TenantCode:  " demo ",
		DeviceCodes: []string{" r1 ", "r2"},
	})
	if err != nil {
		t.Fatalf("PreviewSnapshot returned error: %v", err)
	}
	if resp.SnapshotID != "dc2-preview-demo" {
		t.Fatalf("expected builder snapshot id, got %q", resp.SnapshotID)
	}
	if resp.Devices != 2 || resp.Links != 1 {
		t.Fatalf("unexpected counts devices=%d links=%d", resp.Devices, resp.Links)
	}
	if len(resp.Warnings) != 1 || resp.Warnings[0] != "route tables are not available in snapshot builder MVP" {
		t.Fatalf("unexpected warnings: %#v", resp.Warnings)
	}
	if builder.req.TenantCode != "demo" {
		t.Fatalf("expected trimmed tenant in builder req, got %q", builder.req.TenantCode)
	}
	if len(builder.req.DeviceCodes) != 2 || builder.req.DeviceCodes[0] != "r1" || builder.req.DeviceCodes[1] != "r2" {
		t.Fatalf("expected trimmed device codes, got %#v", builder.req.DeviceCodes)
	}
}
```

Add imports:

```go
	"github.com/netxops/OneOps/app/netpath/snapshot"
```

- [ ] **Step 2: Run service tests and verify failure**

Run:

```bash
go test ./app/netpath/service/impl
```

Expected: FAIL because `WithSnapshotBuilder` does not exist.

- [ ] **Step 3: Add optional builder dependency**

Modify `app/netpath/service/impl/netpath.go`:

```go
import "github.com/netxops/OneOps/app/netpath/snapshot"
```

Add:

```go
type SnapshotBuilder interface {
	BuildPreview(ctx context.Context, req snapshot.BuildRequest) (*snapshot.Snapshot, error)
}

type Option func(*NetPathService)

func WithSnapshotBuilder(builder SnapshotBuilder) Option {
	return func(s *NetPathService) {
		s.snapshotBuilder = builder
	}
}
```

Update `NetPathService`:

```go
type NetPathService struct {
	db              *gorm.DB
	mutex           sync.RWMutex
	runs            map[string]*dto.AnalyzeRunResp
	snapshotBuilder SnapshotBuilder
}
```

Update constructor:

```go
func NewNetPathService(db *gorm.DB, options ...Option) *NetPathService {
	s := &NetPathService{
		db:   db,
		runs: make(map[string]*dto.AnalyzeRunResp),
	}
	for _, option := range options {
		if option != nil {
			option(s)
		}
	}
	return s
}
```

- [ ] **Step 4: Route PreviewSnapshot through builder when configured**

Modify `PreviewSnapshot`:

```go
func (s *NetPathService) PreviewSnapshot(ctx context.Context, req dto.SnapshotPreviewReq) (*dto.SnapshotPreviewResp, error) {
	req.TenantCode = strings.TrimSpace(req.TenantCode)
	req.DeviceCodes = trimNonEmptyStrings(req.DeviceCodes)
	if req.TenantCode == "" {
		return nil, fmt.Errorf("tenant_code is required")
	}

	if s.snapshotBuilder != nil {
		snap, err := s.snapshotBuilder.BuildPreview(ctx, snapshot.BuildRequest{
			TenantCode:  req.TenantCode,
			DeviceCodes: req.DeviceCodes,
		})
		if err != nil {
			return nil, err
		}
		return &dto.SnapshotPreviewResp{
			SnapshotID: snap.SnapshotID,
			TenantCode: snap.TenantCode,
			Devices:    len(snap.Devices),
			Links:      len(snap.Links),
			Warnings:   snapshotWarnings(snap.Diagnostics),
		}, nil
	}

	return &dto.SnapshotPreviewResp{
		SnapshotID: "preview-" + req.TenantCode,
		TenantCode: req.TenantCode,
		Devices:    len(req.DeviceCodes),
		Links:      0,
		Warnings: []string{
			"MVP preview uses request metadata only until snapshot builder is implemented",
		},
	}, nil
}
```

Add helpers:

```go
func trimNonEmptyStrings(values []string) []string {
	out := make([]string, 0, len(values))
	for _, value := range values {
		value = strings.TrimSpace(value)
		if value != "" {
			out = append(out, value)
		}
	}
	return out
}

func snapshotWarnings(diagnostics []snapshot.Diagnostic) []string {
	warnings := make([]string, 0, len(diagnostics))
	for _, diagnostic := range diagnostics {
		if diagnostic.Severity == "warn" || diagnostic.Severity == "error" {
			if diagnostic.Message != "" {
				warnings = append(warnings, diagnostic.Message)
			} else if diagnostic.Code != "" {
				warnings = append(warnings, diagnostic.Code)
			}
		}
	}
	return warnings
}
```

- [ ] **Step 5: Run service tests**

Run:

```bash
go test ./app/netpath/service/impl
```

Expected: PASS.

- [ ] **Step 6: Run combined netpath tests**

Run:

```bash
go test ./app/netpath/snapshot ./app/netpath/dto ./app/netpath/service ./app/netpath/service/impl ./app/netpath/api
```

Expected: PASS.

- [ ] **Step 7: Commit Task 2**

Run:

```bash
git add app/netpath/service/impl/netpath.go app/netpath/service/impl/netpath_test.go
git commit -m "feat: use dc2 snapshot builder in netpath preview"
```

## Task 3: Verification And Review

**Files:**
- No code changes expected.

- [ ] **Step 1: Run final OneOPS netpath verification**

Run:

```bash
go test -count=1 ./app/netpath/snapshot ./app/netpath/dto ./app/netpath/service ./app/netpath/service/impl ./app/netpath/api
```

Expected: PASS.

- [ ] **Step 2: Confirm unrelated dirty files are untouched**

Run:

```bash
git status --short
git diff --name-only HEAD~2..HEAD
```

Expected:

- NetPath commits only touch `app/netpath/snapshot` and `app/netpath/service/impl`.
- Existing unrelated dirty files under `app/aiops`, `app/ipam`, `app/llm`, and `cmd/wire_gen.go` may still be present and must not be reverted.

- [ ] **Step 3: Request subagent reviews**

Run a spec compliance review:

- Confirms this plan implements approved方案 A.
- Confirms no engine runner/probe/UI/router/Wire scope creep.
- Confirms builder consumes DC2 facts via interface.

Run a quality review:

- Checks deterministic output.
- Checks field coercion from `map[string]interface{}`.
- Checks diagnostics behavior.
- Checks service fallback compatibility.

- [ ] **Step 4: Fix review findings if needed**

If review returns Critical or Important findings, fix them in a follow-up commit and rerun:

```bash
go test -count=1 ./app/netpath/snapshot ./app/netpath/dto ./app/netpath/service ./app/netpath/service/impl ./app/netpath/api
```

Expected: PASS.
