# OneOPS NetPath SnapshotProvider Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the OneOPS internal analysis snapshot model, reader ports, assembler, and quality gate needed for future engine-ready `netpath.Snapshot` generation.

**Architecture:** This phase creates `app/netpath/snapshot/provider` as an analysis-focused package separate from the existing preview builder. The package uses OneOPS-owned structs and injected reader data, so default OneOPS builds remain independent from `oneops-netpath`; the build-tagged SDK mapper/provider is intentionally left for a later Phase 2E plan.

**Tech Stack:** Go, OneOPS `app/netpath/snapshot/provider`, DC2 fact response DTOs, table-driven tests, no `oneops-netpath` import, no `go.mod` or `go.sum` changes.

---

## Scope

In scope:

- Create internal `AnalysisSnapshot` model.
- Define reader input contracts around DC2 latest facts and optional supplemental sources.
- Assemble devices, interfaces, links, route tables, and diagnostics from in-memory facts.
- Support fact types:
  - `device_identity`
  - `interface`
  - `interface_ip`
  - `topology_neighbor`
  - proposed `route_table`
  - existing `server_route`
- Classify snapshot quality as `ready`, `degraded`, or `blocked`.
- Add unit tests for ready, degraded, and blocked cases.

Out of scope:

- Importing `github.com/netxops/oneops-netpath`.
- Wiring the build-tagged SDK adapter.
- Changing `go.mod` or `go.sum`.
- Creating or committing `go.work`.
- Adding production DI / Wire changes.
- Implementing route collection contracts.
- Implementing ACL/NAT/PBR/security policy evaluation.
- UI, probe, or ticket work.

## File Structure

Create:

```text
OneOPS/app/netpath/snapshot/provider/types.go
OneOPS/app/netpath/snapshot/provider/facts.go
OneOPS/app/netpath/snapshot/provider/assembler.go
OneOPS/app/netpath/snapshot/provider/validator.go
OneOPS/app/netpath/snapshot/provider/assembler_test.go
OneOPS/app/netpath/snapshot/provider/validator_test.go
```

Responsibilities:

- `types.go`: public internal package model, diagnostics, source refs, quality state.
- `facts.go`: fact input helpers and field conversion helpers.
- `assembler.go`: converts facts into `AnalysisSnapshot`.
- `validator.go`: validates and classifies snapshots for analysis readiness.
- `assembler_test.go`: table tests for facts-to-snapshot assembly.
- `validator_test.go`: table tests for ready/degraded/blocked quality gates.

## Task 1: Analysis Snapshot Model

**Files:**
- Create: `OneOPS/app/netpath/snapshot/provider/types.go`
- Test: `OneOPS/app/netpath/snapshot/provider/validator_test.go`

- [ ] **Step 1: Create the model file**

Create `OneOPS/app/netpath/snapshot/provider/types.go` with these exported types:

```go
package provider

import "time"

type SnapshotQuality string

const (
	SnapshotQualityReady    SnapshotQuality = "ready"
	SnapshotQualityDegraded SnapshotQuality = "degraded"
	SnapshotQualityBlocked  SnapshotQuality = "blocked"
)

type Severity string

const (
	SeverityInfo  Severity = "info"
	SeverityWarn  Severity = "warn"
	SeverityError Severity = "error"
)

type AnalysisSnapshot struct {
	SnapshotID     string
	TenantCode     string
	GeneratedAt    time.Time
	SourceVersions SourceRefs
	Devices        []AnalysisDevice
	Links          []AnalysisLink
	Diagnostics    []AnalysisDiagnostic
	Quality        SnapshotQuality
}

type SourceRefs struct {
	ConfigVersionIDs []string
	TopologySnapshotID string
	CollectionRunIDs   []string
	FactRunIDs       []string
}

type AnalysisDevice struct {
	DeviceCode       string
	DeviceName       string
	DeviceType       string
	Vendor           string
	Model            string
	ManagementIP     string
	VRFs             []AnalysisVRF
	Interfaces       []AnalysisInterface
	RouteTables      []AnalysisRouteTable
	PolicyEvidence   []AnalysisPolicyEvidence
	FirewallModelRef string
	Metadata         map[string]string
}

type AnalysisVRF struct {
	Name string
}

type AnalysisInterface struct {
	InterfaceCode     string
	InterfaceName     string
	VRF               string
	Zone              string
	IPv4Addresses     []string
	Status            string
	PeerDeviceCode    string
	PeerInterfaceName string
	PeerInterfaceCode string
	Source            string
}

type AnalysisLink struct {
	ADeviceCode string
	AInterfaceName string
	BDeviceCode string
	BInterfaceName string
	Source      string
	Description string
}

type AnalysisRouteTable struct {
	VRF    string
	Routes []AnalysisRoute
}

type AnalysisRoute struct {
	Destination  string
	NextHopIP    string
	OutInterfaceName string
	Protocol     string
	Metric       int
	Preference   int
	NullRoute    bool
	Raw          string
	RouteSourceRef string
}

type AnalysisPolicyEvidence struct {
	Phase            string
	RuleID           string
	RuleName         string
	Action           string
	SourceZones      []string
	DestinationZones []string
	SourceObjectRefs []string
	DestinationObjectRefs []string
	ServiceObjectRefs []string
	RawCLI           string
	ConfigVersionID  string
	EvidenceSourceRef string
}

type AnalysisDiagnostic struct {
	Severity Severity
	Code     string
	Message  string
	Refs     []string
}
```

- [ ] **Step 2: Add compile test for quality constants**

Create `OneOPS/app/netpath/snapshot/provider/validator_test.go` with this first test:

```go
package provider

import "testing"

func TestSnapshotQualityConstants(t *testing.T) {
	if SnapshotQualityReady != "ready" {
		t.Fatalf("unexpected ready quality: %q", SnapshotQualityReady)
	}
	if SnapshotQualityDegraded != "degraded" {
		t.Fatalf("unexpected degraded quality: %q", SnapshotQualityDegraded)
	}
	if SnapshotQualityBlocked != "blocked" {
		t.Fatalf("unexpected blocked quality: %q", SnapshotQualityBlocked)
	}
}
```

- [ ] **Step 3: Run the package test**

Run from `/Users/huangliang/project/OneOPS-ALL/OneOPS`:

```bash
go test -count=1 ./app/netpath/snapshot/provider
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add app/netpath/snapshot/provider/types.go app/netpath/snapshot/provider/validator_test.go
git commit -m "feat: add netpath analysis snapshot model"
```

## Task 2: Fact Input Helpers

**Files:**
- Create: `OneOPS/app/netpath/snapshot/provider/facts.go`
- Modify: `OneOPS/app/netpath/snapshot/provider/assembler_test.go`

- [ ] **Step 1: Add fact helper file**

Create `OneOPS/app/netpath/snapshot/provider/facts.go`:

```go
package provider

import (
	"fmt"
	"strconv"
	"strings"

	dc2dto "github.com/netxops/OneOps/app/device_collection2/dto"
)

const (
	FactTypeDeviceIdentity   = "device_identity"
	FactTypeInterface        = "interface"
	FactTypeInterfaceIP      = "interface_ip"
	FactTypeTopologyNeighbor = "topology_neighbor"
	FactTypeRouteTable       = "route_table"
	FactTypeServerRoute      = "server_route"
	DefaultVRF               = "default"
)

type FactSet struct {
	DeviceIdentity   []dc2dto.FactRecordResp
	Interfaces       []dc2dto.FactRecordResp
	InterfaceIPs     []dc2dto.FactRecordResp
	TopologyNeighbor []dc2dto.FactRecordResp
	RouteTables      []dc2dto.FactRecordResp
	ServerRoutes     []dc2dto.FactRecordResp
}

func normalizeVRF(value string) string {
	value = strings.TrimSpace(value)
	if value == "" {
		return DefaultVRF
	}
	return value
}

func stringField(fields map[string]interface{}, key string) string {
	if fields == nil {
		return ""
	}
	value, ok := fields[key]
	if !ok || value == nil {
		return ""
	}
	switch typed := value.(type) {
	case string:
		return strings.TrimSpace(typed)
	case fmt.Stringer:
		return strings.TrimSpace(typed.String())
	default:
		return strings.TrimSpace(fmt.Sprint(typed))
	}
}

func intField(fields map[string]interface{}, key string) int {
	text := intFieldString(fields, key)
	if text == "" {
		return 0
	}
	parsed, _ := strconv.Atoi(text)
	return parsed
}

func intFieldString(fields map[string]interface{}, key string) string {
	if fields == nil {
		return ""
	}
	value, ok := fields[key]
	if !ok || value == nil {
		return ""
	}
	switch typed := value.(type) {
	case int:
		return strconv.Itoa(typed)
	case int64:
		return strconv.FormatInt(typed, 10)
	case float64:
		if math.Trunc(typed) != typed {
			return ""
		}
		return strconv.FormatInt(int64(typed), 10)
	case string:
		if parsed, err := strconv.ParseFloat(strings.TrimSpace(typed), 64); err == nil && math.Trunc(parsed) == parsed {
			return strconv.FormatInt(int64(parsed), 10)
		}
	default:
		if parsed, err := strconv.ParseFloat(strings.TrimSpace(fmt.Sprint(typed)), 64); err == nil && math.Trunc(parsed) == parsed {
			return strconv.FormatInt(int64(parsed), 10)
		}
	}
	return ""
}

func boolField(fields map[string]interface{}, key string) bool {
	if fields == nil {
		return false
	}
	value, ok := fields[key]
	if !ok || value == nil {
		return false
	}
	switch typed := value.(type) {
	case bool:
		return typed
	case string:
		parsed, _ := strconv.ParseBool(strings.TrimSpace(typed))
		return parsed
	default:
		parsed, _ := strconv.ParseBool(strings.TrimSpace(fmt.Sprint(typed)))
		return parsed
	}
}

func interfaceName(fields map[string]interface{}, fallback string) string {
	if value := stringField(fields, "if_name_canonical"); value != "" {
		return value
	}
	if value := stringField(fields, "if_name"); value != "" {
		return value
	}
	return strings.TrimSpace(fallback)
}

func statusField(fields map[string]interface{}) string {
	if value := stringField(fields, "oper_status"); value != "" {
		return value
	}
	return stringField(fields, "admin_status")
}

func cidrField(fields map[string]interface{}) string {
	if value := stringField(fields, "cidr"); value != "" {
		return value
	}
	ip := stringField(fields, "ip")
	prefix := intFieldString(fields, "prefix_len")
	if ip == "" || prefix == "" {
		return ""
	}
	return ip + "/" + prefix
}

func interfaceJoinKeys(identityKey string, fields map[string]interface{}) []string {
	keys := make([]string, 0, 4)
	add := func(value string) {
		value = strings.TrimSpace(value)
		if value == "" {
			return
		}
		for _, existing := range keys {
			if existing == value {
				return
			}
		}
		keys = append(keys, value)
	}

	add(interfaceJoinKey(identityKey, fields))
	if value := intFieldString(fields, "if_index"); value != "" {
		add("if_index:" + normalizeIdentityString(value))
	}
	if value := stringField(fields, "if_name_canonical"); value != "" {
		normalized := normalizeIdentityString(value)
		add("if_name_canonical:" + normalized)
		add("if_name:" + normalized)
	}
	if value := stringField(fields, "if_name"); value != "" {
		add("if_name:" + normalizeIdentityString(value))
	}
	if value := strings.TrimSpace(identityKey); value != "" {
		add("identity:" + normalizeIdentityString(value))
	}
	return keys
}

func interfaceJoinKey(identityKey string, fields map[string]interface{}) string {
	if value := intFieldString(fields, "if_index"); value != "" {
		return "if_index:" + normalizeIdentityString(value)
	}
	if value := stringField(fields, "if_name_canonical"); value != "" {
		return "if_name_canonical:" + normalizeIdentityString(value)
	}
	if value := stringField(fields, "if_name"); value != "" {
		return "if_name:" + normalizeIdentityString(value)
	}
	if value := strings.TrimSpace(identityKey); value != "" {
		return "identity:" + normalizeIdentityString(value)
	}
	return ""
}

func normalizeIdentityString(value string) string {
	return strings.ToLower(strings.TrimSpace(value))
}
```

- [ ] **Step 2: Add helper tests**

Create `OneOPS/app/netpath/snapshot/provider/assembler_test.go` with:

```go
package provider

import "testing"

func TestFactHelpersNormalizeFields(t *testing.T) {
	fields := map[string]interface{}{
		"if_name":           "GigabitEthernet0/0",
		"if_name_canonical": "ge0/0",
		"if_index":          float64(7),
		"metric":            "20",
		"null_route":        "true",
	}

	if got := interfaceName(fields, "fallback"); got != "ge0/0" {
		t.Fatalf("expected canonical interface name, got %q", got)
	}
	if got := intField(fields, "metric"); got != 20 {
		t.Fatalf("expected metric 20, got %d", got)
	}
	if got := boolField(fields, "null_route"); !got {
		t.Fatal("expected null_route to parse true")
	}
	if got := statusField(map[string]interface{}{"admin_status": "up", "oper_status": "down"}); got != "down" {
		t.Fatalf("expected oper_status to win, got %q", got)
	}
	if got := cidrField(map[string]interface{}{"ip": "10.0.12.1", "prefix_len": float64(30)}); got != "10.0.12.1/30" {
		t.Fatalf("expected synthesized cidr, got %q", got)
	}
	if got := cidrField(map[string]interface{}{"cidr": "192.0.2.1/32", "ip": "192.0.2.1", "prefix_len": float64(24)}); got != "192.0.2.1/32" {
		t.Fatalf("expected explicit cidr to win, got %q", got)
	}
	keys := interfaceJoinKeys("r1:if_index:7", fields)
	assertContainsString(t, keys, "identity:r1:if_index:7")
	assertContainsString(t, keys, "if_name_canonical:ge0/0")
	assertContainsString(t, keys, "if_name:ge0/0")
	assertContainsString(t, keys, "if_name:gigabitethernet0/0")
	assertContainsString(t, keys, "if_index:7")
	if got := cidrField(map[string]interface{}{"ip": "10.0.12.1", "prefix_len": float64(30.5)}); got != "" {
		t.Fatalf("expected non-integral prefix_len to be rejected, got %q", got)
	}
}

func assertContainsString(t *testing.T, values []string, want string) {
	t.Helper()
	for _, value := range values {
		if value == want {
			return
		}
	}
	t.Fatalf("expected %#v to contain %q", values, want)
}
```

- [ ] **Step 3: Run tests**

```bash
go test -count=1 ./app/netpath/snapshot/provider
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add app/netpath/snapshot/provider/facts.go app/netpath/snapshot/provider/assembler_test.go
git commit -m "feat: add netpath snapshot fact helpers"
```

## Task 3: Assembler For Devices, Interfaces, Links, And Routes

**Files:**
- Create: `OneOPS/app/netpath/snapshot/provider/assembler.go`
- Modify: `OneOPS/app/netpath/snapshot/provider/assembler_test.go`

- [ ] **Step 1: Add assembler API and implementation**

Create `OneOPS/app/netpath/snapshot/provider/assembler.go` with:

```go
package provider

import (
	"context"
	"sort"
	"strings"
	"time"

	dc2dto "github.com/netxops/OneOps/app/device_collection2/dto"
)

type AssembleRequest struct {
	TenantCode  string
	SnapshotID  string
	GeneratedAt time.Time
	Facts       FactSet
}

type Assembler struct{}

func NewAssembler() *Assembler {
	return &Assembler{}
}

func (a *Assembler) Assemble(ctx context.Context, req AssembleRequest) (*AnalysisSnapshot, error) {
	_ = ctx
	state := newAssembleState(req)
	state.addDeviceIdentity(req.Facts.DeviceIdentity)
	state.addInterfaces(req.Facts.Interfaces)
	state.addInterfaceIPs(req.Facts.InterfaceIPs)
	state.addTopology(req.Facts.TopologyNeighbor)
	state.addRouteTables(req.Facts.RouteTables)
	state.addServerRoutes(req.Facts.ServerRoutes)
	return state.snapshot(), nil
}

type assembleState struct {
	req         AssembleRequest
	devices     map[string]*deviceState
	links       []AnalysisLink
	linkIndex   map[string]struct{}
	diagnostics []AnalysisDiagnostic
	diagIndex   map[string]struct{}
	factRunIDs  map[string]struct{}
}

type deviceState struct {
	device     AnalysisDevice
	joinIndex  map[string]string
	interfaces map[string]*AnalysisInterface
	routesByVRF map[string][]AnalysisRoute
	vrfs       map[string]struct{}
}

func newAssembleState(req AssembleRequest) *assembleState {
	return &assembleState{
		req:        req,
		devices:    make(map[string]*deviceState),
		linkIndex:  make(map[string]struct{}),
		diagIndex:  make(map[string]struct{}),
		factRunIDs: make(map[string]struct{}),
	}
}

func (s *assembleState) addDeviceIdentity(facts []dc2dto.FactRecordResp) {
	for _, fact := range facts {
		device := s.ensureDevice(fact.TargetID)
		device.device.DeviceName = firstNonEmpty(stringField(fact.Fields, "hostname"), device.device.DeviceName)
		device.device.Vendor = firstNonEmpty(stringField(fact.Fields, "vendor"), device.device.Vendor)
		device.device.Model = firstNonEmpty(stringField(fact.Fields, "model"), stringField(fact.Fields, "product_name"), device.device.Model)
		device.device.ManagementIP = firstNonEmpty(stringField(fact.Fields, "management_ip"), device.device.ManagementIP)
		device.device.DeviceType = firstNonEmpty(stringField(fact.Fields, "platform"), device.device.DeviceType)
		s.recordRunID(fact)
	}
}

func (s *assembleState) addInterfaces(facts []dc2dto.FactRecordResp) {
	for _, fact := range facts {
		device := s.ensureDevice(fact.TargetID)
		iface := s.ensureInterface(device, fact.IdentityKey, fact.Fields)
		iface.InterfaceName = firstNonEmpty(interfaceName(fact.Fields, fact.IdentityKey), iface.InterfaceName)
		iface.Status = firstNonEmpty(stringField(fact.Fields, "oper_status"), stringField(fact.Fields, "admin_status"), iface.Status)
		iface.Source = firstNonEmpty("dc2:"+FactTypeInterface, iface.Source)
		for _, key := range interfaceJoinKeys(fact.IdentityKey, fact.Fields) {
			device.joinIndex[key] = iface.InterfaceCode
		}
		s.recordRunID(fact)
	}
}

func (s *assembleState) addInterfaceIPs(facts []dc2dto.FactRecordResp) {
	for _, fact := range facts {
		device := s.ensureDevice(fact.TargetID)
		iface, found := s.findInterface(device, fact.IdentityKey, fact.Fields)
		if !found {
			iface = s.ensureInterface(device, fact.IdentityKey, fact.Fields)
			s.addDiagnostic(SeverityWarn, "interface_ip_without_interface", "interface_ip fact could not be joined to an interface fact; inferred interface created", []string{fact.TargetID, fact.IdentityKey})
		}
		iface.InterfaceName = firstNonEmpty(interfaceName(fact.Fields, fact.IdentityKey), iface.InterfaceName)
		iface.VRF = normalizeVRF(firstNonEmpty(stringField(fact.Fields, "vrf"), iface.VRF))
		if cidr := stringField(fact.Fields, "cidr"); cidr != "" {
			iface.IPv4Addresses = appendUnique(iface.IPv4Addresses, cidr)
		}
		iface.Source = firstNonEmpty(iface.Source, "dc2:"+FactTypeInterfaceIP)
		device.vrfs[iface.VRF] = struct{}{}
		for _, key := range interfaceJoinKeys(fact.IdentityKey, fact.Fields) {
			device.joinIndex[key] = iface.InterfaceCode
		}
		s.recordRunID(fact)
	}
}

func (s *assembleState) addTopology(facts []dc2dto.FactRecordResp) {
	for _, fact := range facts {
		localDevice := s.devices[strings.TrimSpace(fact.TargetID)]
		if localDevice == nil {
			s.addDiagnostic(SeverityWarn, "topology_local_device_missing", "topology neighbor local device is missing", []string{fact.TargetID, fact.IdentityKey})
			continue
		}
		localInterface, found := s.findInterface(localDevice, fact.IdentityKey, fact.Fields)
		if !found {
			s.addDiagnostic(SeverityWarn, "topology_local_interface_missing", "topology neighbor local interface is missing", []string{fact.TargetID, fact.IdentityKey})
			continue
		}
		remoteDeviceCode := strings.TrimSpace(stringField(fact.Fields, "remote_device"))
		remoteInterfaceName := firstNonEmpty(stringField(fact.Fields, "remote_if_name_canonical"), stringField(fact.Fields, "remote_if_name"))
		remoteDevice := s.devices[remoteDeviceCode]
		if remoteDevice == nil || remoteInterfaceName == "" {
			s.addDiagnostic(SeverityWarn, "topology_remote_unresolved", "topology neighbor remote endpoint could not be resolved", []string{fact.TargetID, fact.IdentityKey})
			continue
		}
		remoteInterface, found := s.findInterfaceByName(remoteDevice, remoteInterfaceName)
		if !found {
			s.addDiagnostic(SeverityWarn, "topology_remote_interface_missing", "topology neighbor remote interface is missing", []string{fact.TargetID, fact.IdentityKey})
			continue
		}
		s.addLink(AnalysisLink{
			ADeviceCode: localDevice.device.DeviceCode,
			AInterfaceName:  localInterface.InterfaceName,
			BDeviceCode: remoteDevice.device.DeviceCode,
			BInterfaceName:  remoteInterface.InterfaceName,
			Source:      firstNonEmpty(stringField(fact.Fields, "protocol"), "dc2"),
		})
		s.recordRunID(fact)
	}
}

func (s *assembleState) addRouteTables(facts []dc2dto.FactRecordResp) {
	for _, fact := range facts {
		device := s.ensureDevice(fact.TargetID)
		vrf := normalizeVRF(stringField(fact.Fields, "vrf"))
		route := AnalysisRoute{
			Destination:  stringField(fact.Fields, "destination"),
			NextHopIP:    stringField(fact.Fields, "next_hop_ip"),
			OutInterfaceName: stringField(fact.Fields, "out_interface"),
			Protocol:     stringField(fact.Fields, "protocol"),
			Metric:       intField(fact.Fields, "metric"),
			Preference:   intField(fact.Fields, "preference"),
			NullRoute:    boolField(fact.Fields, "null_route"),
			Raw:          stringField(fact.Fields, "raw"),
			RouteSourceRef:    fact.FactID,
		}
		device.routesByVRF[vrf] = append(device.routesByVRF[vrf], route)
		device.vrfs[vrf] = struct{}{}
		s.recordRunID(fact)
	}
}

func (s *assembleState) addServerRoutes(facts []dc2dto.FactRecordResp) {
	for _, fact := range facts {
		device := s.ensureDevice(fact.TargetID)
		vrf := normalizeVRF(stringField(fact.Fields, "vrf"))
		outInterface := firstNonEmpty(stringField(fact.Fields, "out_interface"), stringField(fact.Fields, "if_name"), stringField(fact.Fields, "if_name_canonical"))
		route := AnalysisRoute{
			Destination:  stringField(fact.Fields, "destination"),
			NextHopIP:    firstNonEmpty(stringField(fact.Fields, "next_hop_ip"), stringField(fact.Fields, "gateway")),
			OutInterfaceName: outInterface,
			Protocol:     firstNonEmpty(stringField(fact.Fields, "protocol"), "server_route"),
			Metric:       firstNonEmptyInt(intField(fact.Fields, "metric"), intField(fact.Fields, "route_metric")),
			Preference:   intField(fact.Fields, "preference"),
			NullRoute:    boolField(fact.Fields, "null_route"),
			Raw:          stringField(fact.Fields, "raw"),
			RouteSourceRef:    fact.FactID,
		}
		device.routesByVRF[vrf] = append(device.routesByVRF[vrf], route)
		device.vrfs[vrf] = struct{}{}
		s.recordRunID(fact)
	}
}
```

Add the supporting methods in the same file:

```go
func (s *assembleState) ensureDevice(code string) *deviceState {
	code = strings.TrimSpace(code)
	device := s.devices[code]
	if device != nil {
		return device
	}
	device = &deviceState{
		device: AnalysisDevice{
			DeviceCode: code,
			DeviceType: "unknown",
			Metadata:   map[string]string{},
		},
		joinIndex:  make(map[string]string),
		interfaces: make(map[string]*AnalysisInterface),
		routesByVRF: make(map[string][]AnalysisRoute),
		vrfs:       make(map[string]struct{}),
	}
	s.devices[code] = device
	return device
}

func (s *assembleState) ensureInterface(device *deviceState, identityKey string, fields map[string]interface{}) *AnalysisInterface {
	code := strings.TrimSpace(identityKey)
	if code == "" {
		code = interfaceName(fields, "interface")
	}
	iface := device.interfaces[code]
	if iface != nil {
		return iface
	}
	iface = &AnalysisInterface{
		InterfaceCode: code,
		InterfaceName: interfaceName(fields, code),
		VRF:           normalizeVRF(stringField(fields, "vrf")),
	}
	device.interfaces[code] = iface
	for _, key := range interfaceJoinKeys(identityKey, fields) {
		device.joinIndex[key] = code
	}
	device.vrfs[iface.VRF] = struct{}{}
	return iface
}

func (s *assembleState) findInterface(device *deviceState, identityKey string, fields map[string]interface{}) (*AnalysisInterface, bool) {
	for _, key := range interfaceJoinKeys(identityKey, fields) {
		if code := device.joinIndex[key]; code != "" {
			if iface := device.interfaces[code]; iface != nil {
				return iface, true
			}
		}
	}
	return nil, false
}

func (s *assembleState) findInterfaceByName(device *deviceState, name string) (*AnalysisInterface, bool) {
	name = strings.TrimSpace(name)
	for _, iface := range device.interfaces {
		if iface.InterfaceName == name || iface.InterfaceCode == name {
			return iface, true
		}
	}
	return nil, false
}

func (s *assembleState) addLink(link AnalysisLink) {
	if link.ADeviceCode > link.BDeviceCode || (link.ADeviceCode == link.BDeviceCode && link.AInterfaceName > link.BInterfaceName) {
		link = AnalysisLink{
			ADeviceCode: link.BDeviceCode,
			AInterfaceName:  link.BInterfaceName,
			BDeviceCode: link.ADeviceCode,
			BInterfaceName:  link.AInterfaceName,
			Source:      link.Source,
			Description: link.Description,
		}
	}
	key := strings.Join([]string{link.ADeviceCode, link.AInterfaceName, link.BDeviceCode, link.BInterfaceName}, "|")
	if _, ok := s.linkIndex[key]; ok {
		return
	}
	s.linkIndex[key] = struct{}{}
	s.links = append(s.links, link)
}

func (s *assembleState) snapshot() *AnalysisSnapshot {
	devices := make([]AnalysisDevice, 0, len(s.devices))
	for _, state := range s.devices {
		device := state.device
		device.Interfaces = sortedInterfaces(state.interfaces)
		device.RouteTables = sortedRouteTables(state.routesByVRF)
		device.VRFs = sortedVRFs(state.vrfs)
		devices = append(devices, device)
	}
	sort.Slice(devices, func(i, j int) bool { return devices[i].DeviceCode < devices[j].DeviceCode })
	sort.Slice(s.links, func(i, j int) bool {
		left := strings.Join([]string{s.links[i].ADeviceCode, s.links[i].AInterfaceName, s.links[i].BDeviceCode, s.links[i].BInterfaceName}, "|")
		right := strings.Join([]string{s.links[j].ADeviceCode, s.links[j].AInterfaceName, s.links[j].BDeviceCode, s.links[j].BInterfaceName}, "|")
		return left < right
	})
	sort.Slice(s.diagnostics, func(i, j int) bool {
		left := strings.Join([]string{string(s.diagnostics[i].Severity), s.diagnostics[i].Code, strings.Join(s.diagnostics[i].Refs, "|")}, "|")
		right := strings.Join([]string{string(s.diagnostics[j].Severity), s.diagnostics[j].Code, strings.Join(s.diagnostics[j].Refs, "|")}, "|")
		return left < right
	})
	snapshotID := strings.TrimSpace(s.req.SnapshotID)
	if snapshotID == "" {
		snapshotID = "analysis-snapshot:" + strings.TrimSpace(s.req.TenantCode)
	}
	generatedAt := s.req.GeneratedAt
	if generatedAt.IsZero() {
		generatedAt = time.Now().UTC()
	}
	return &AnalysisSnapshot{
		SnapshotID:  snapshotID,
		TenantCode:  strings.TrimSpace(s.req.TenantCode),
		GeneratedAt: generatedAt,
		SourceVersions: SourceRefs{
			FactRunIDs: sortedStringSet(s.factRunIDs),
		},
		Devices:     devices,
		Links:       append([]AnalysisLink(nil), s.links...),
		Diagnostics: append([]AnalysisDiagnostic(nil), s.diagnostics...),
	}
}
```

Add the remaining helper functions in the same file:

```go
func sortedInterfaces(values map[string]*AnalysisInterface) []AnalysisInterface {
	out := make([]AnalysisInterface, 0, len(values))
	for _, value := range values {
		copied := *value
		copied.IPv4Addresses = append([]string(nil), value.IPv4Addresses...)
		sort.Strings(copied.IPv4Addresses)
		out = append(out, copied)
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].InterfaceName != out[j].InterfaceName {
			return out[i].InterfaceName < out[j].InterfaceName
		}
		return out[i].InterfaceCode < out[j].InterfaceCode
	})
	return out
}

func sortedRouteTables(values map[string][]AnalysisRoute) []AnalysisRouteTable {
	out := make([]AnalysisRouteTable, 0, len(values))
	for vrf, routes := range values {
		copied := append([]AnalysisRoute(nil), routes...)
		sort.SliceStable(copied, func(i, j int) bool {
			if copied[i].Destination != copied[j].Destination {
				return copied[i].Destination < copied[j].Destination
			}
			if copied[i].Preference != copied[j].Preference {
				return copied[i].Preference < copied[j].Preference
			}
			return copied[i].Metric < copied[j].Metric
		})
		out = append(out, AnalysisRouteTable{VRF: vrf, Routes: copied})
	}
	sort.Slice(out, func(i, j int) bool { return out[i].VRF < out[j].VRF })
	return out
}

func sortedVRFs(values map[string]struct{}) []AnalysisVRF {
	names := sortedStringSet(values)
	out := make([]AnalysisVRF, 0, len(names))
	for _, name := range names {
		out = append(out, AnalysisVRF{Name: name})
	}
	return out
}

func sortedStringSet(values map[string]struct{}) []string {
	out := make([]string, 0, len(values))
	for value := range values {
		if strings.TrimSpace(value) != "" {
			out = append(out, value)
		}
	}
	sort.Strings(out)
	return out
}

func (s *assembleState) addDiagnostic(severity Severity, code string, message string, refs []string) {
	key := strings.Join(append([]string{string(severity), code, message}, refs...), "|")
	if _, ok := s.diagIndex[key]; ok {
		return
	}
	s.diagIndex[key] = struct{}{}
	s.diagnostics = append(s.diagnostics, AnalysisDiagnostic{
		Severity: severity,
		Code:     code,
		Message:  message,
		Refs:     append([]string(nil), refs...),
	})
}

func (s *assembleState) recordRunID(fact dc2dto.FactRecordResp) {
	if strings.TrimSpace(fact.RunID) != "" {
		s.factRunIDs[strings.TrimSpace(fact.RunID)] = struct{}{}
	}
}

func firstNonEmpty(values ...string) string {
	for _, value := range values {
		if strings.TrimSpace(value) != "" {
			return strings.TrimSpace(value)
		}
	}
	return ""
}

func firstNonEmptyInt(values ...int) int {
	for _, value := range values {
		if value != 0 {
			return value
		}
	}
	return 0
}

func appendUnique(values []string, value string) []string {
	value = strings.TrimSpace(value)
	if value == "" {
		return values
	}
	for _, existing := range values {
		if existing == value {
			return values
		}
	}
	return append(values, value)
}
```

- [ ] **Step 2: Add ready assembly test**

Append this to `OneOPS/app/netpath/snapshot/provider/assembler_test.go`:

```go
func TestAssemblerBuildsEngineReadyRouteTopologySnapshot(t *testing.T) {
	assembler := NewAssembler()
	snap, err := assembler.Assemble(context.Background(), AssembleRequest{
		TenantCode:  "tenant-a",
		SnapshotID:  "snap-a",
		GeneratedAt: time.Date(2026, 6, 19, 1, 0, 0, 0, time.UTC),
		Facts: FactSet{
			DeviceIdentity: []dc2dto.FactRecordResp{
				fact("fact-id-r1", "run-1", "r1", FactTypeDeviceIdentity, "r1", map[string]interface{}{"hostname": "edge-r1", "vendor": "h3c", "model": "s6850", "management_ip": "192.0.2.10"}),
				fact("fact-id-r2", "run-1", "r2", FactTypeDeviceIdentity, "r2", map[string]interface{}{"hostname": "app-r2", "vendor": "h3c", "model": "s6850", "management_ip": "192.0.2.11"}),
			},
			Interfaces: []dc2dto.FactRecordResp{
				fact("fact-if-r1-1", "run-1", "r1", FactTypeInterface, "r1:if_index:1", map[string]interface{}{"if_index": float64(1), "if_name_canonical": "ge0/0", "oper_status": "up"}),
				fact("fact-if-r1-2", "run-1", "r1", FactTypeInterface, "r1:if_index:2", map[string]interface{}{"if_index": float64(2), "if_name_canonical": "ge0/1", "oper_status": "up"}),
				fact("fact-if-r2-1", "run-1", "r2", FactTypeInterface, "r2:if_index:1", map[string]interface{}{"if_index": float64(1), "if_name_canonical": "ge0/0", "oper_status": "up"}),
				fact("fact-if-r2-2", "run-1", "r2", FactTypeInterface, "r2:if_index:2", map[string]interface{}{"if_index": float64(2), "if_name_canonical": "ge0/1", "oper_status": "up"}),
			},
			InterfaceIPs: []dc2dto.FactRecordResp{
				fact("fact-ip-r1-1", "run-1", "r1", FactTypeInterfaceIP, "r1:if_index:1:ip:10.0.1.1", map[string]interface{}{"if_index": float64(1), "cidr": "10.0.1.1/24", "vrf": "default"}),
				fact("fact-ip-r1-2", "run-1", "r1", FactTypeInterfaceIP, "r1:if_index:2:ip:192.0.2.1", map[string]interface{}{"if_index": float64(2), "cidr": "192.0.2.1/30", "vrf": "default"}),
				fact("fact-ip-r2-1", "run-1", "r2", FactTypeInterfaceIP, "r2:if_index:1:ip:192.0.2.2", map[string]interface{}{"if_index": float64(1), "cidr": "192.0.2.2/30", "vrf": "default"}),
				fact("fact-ip-r2-2", "run-1", "r2", FactTypeInterfaceIP, "r2:if_index:2:ip:10.0.2.1", map[string]interface{}{"if_index": float64(2), "cidr": "10.0.2.1/24", "vrf": "default"}),
			},
			TopologyNeighbor: []dc2dto.FactRecordResp{
				fact("fact-link-r1-r2", "run-1", "r1", FactTypeTopologyNeighbor, "r1:if_index:2:neighbor:r2", map[string]interface{}{"if_index": float64(2), "remote_device": "r2", "remote_if_name_canonical": "ge0/0", "protocol": "lldp"}),
			},
			RouteTables: []dc2dto.FactRecordResp{
				fact("fact-route-r1", "run-1", "r1", FactTypeRouteTable, "r1:route:10.0.2.0/24", map[string]interface{}{"vrf": "default", "destination": "10.0.2.0/24", "next_hop_ip": "192.0.2.2", "out_interface": "ge0/1", "protocol": "static", "metric": float64(10), "preference": float64(60), "raw": "ip route 10.0.2.0/24 192.0.2.2"}),
				fact("fact-route-r2", "run-1", "r2", FactTypeRouteTable, "r2:route:10.0.2.0/24", map[string]interface{}{"vrf": "default", "destination": "10.0.2.0/24", "out_interface": "ge0/1", "protocol": "connected", "raw": "C 10.0.2.0/24 is directly connected"}),
			},
		},
	})
	if err != nil {
		t.Fatalf("Assemble returned error: %v", err)
	}
	if snap.SnapshotID != "snap-a" || snap.TenantCode != "tenant-a" {
		t.Fatalf("unexpected snapshot identity: %#v", snap)
	}
	if len(snap.Devices) != 2 {
		t.Fatalf("expected 2 devices, got %#v", snap.Devices)
	}
	r1 := findAnalysisDevice(t, snap, "r1")
	if r1.DeviceName != "edge-r1" || r1.Vendor != "h3c" || r1.ManagementIP != "192.0.2.10" {
		t.Fatalf("unexpected r1 identity: %#v", r1)
	}
	if len(r1.Interfaces) != 2 {
		t.Fatalf("expected r1 interfaces, got %#v", r1.Interfaces)
	}
	if len(r1.RouteTables) != 1 || len(r1.RouteTables[0].Routes) != 1 {
		t.Fatalf("expected r1 route table, got %#v", r1.RouteTables)
	}
	route := r1.RouteTables[0].Routes[0]
	if route.Destination != "10.0.2.0/24" || route.NextHopIP != "192.0.2.2" || route.OutInterfaceName != "ge0/1" || route.Metric != 10 || route.Preference != 60 {
		t.Fatalf("unexpected route: %#v", route)
	}
	if len(snap.Links) != 1 || snap.Links[0].ADeviceCode != "r1" || snap.Links[0].BDeviceCode != "r2" {
		t.Fatalf("unexpected links: %#v", snap.Links)
	}
	if len(snap.Diagnostics) != 0 {
		t.Fatalf("expected no diagnostics, got %#v", snap.Diagnostics)
	}
}
```

Add imports and helpers to the same test file:

```go
import (
	"context"
	"testing"
	"time"

	dc2dto "github.com/netxops/OneOps/app/device_collection2/dto"
)

func fact(factID, runID, targetID, factType, identityKey string, fields map[string]interface{}) dc2dto.FactRecordResp {
	return dc2dto.FactRecordResp{
		FactID:      factID,
		RunID:       runID,
		TargetID:    targetID,
		FactType:    factType,
		IdentityKey: identityKey,
		Fields:      fields,
		Valid:       true,
	}
}

func findAnalysisDevice(t *testing.T, snap *AnalysisSnapshot, code string) AnalysisDevice {
	t.Helper()
	for _, device := range snap.Devices {
		if device.DeviceCode == code {
			return device
		}
	}
	t.Fatalf("device %s not found in %#v", code, snap.Devices)
	return AnalysisDevice{}
}
```

When adding imports, merge with the existing `testing` import from Task 2 so the file has one import block.

- [ ] **Step 3: Add degraded assembly test**

Append this test:

```go
func TestAssemblerEmitsDiagnosticsForOrphanInterfaceIPAndUnresolvedTopology(t *testing.T) {
	assembler := NewAssembler()
	snap, err := assembler.Assemble(context.Background(), AssembleRequest{
		TenantCode: "tenant-a",
		Facts: FactSet{
			InterfaceIPs: []dc2dto.FactRecordResp{
				fact("fact-ip-orphan", "run-1", "r1", FactTypeInterfaceIP, "r1:if_name:loop0:ip:192.0.2.1", map[string]interface{}{"if_name_canonical": "loop0", "cidr": "192.0.2.1/32"}),
			},
			TopologyNeighbor: []dc2dto.FactRecordResp{
				fact("fact-link-bad", "run-1", "r1", FactTypeTopologyNeighbor, "r1:if_name:loop0:neighbor:r9", map[string]interface{}{"if_name_canonical": "loop0", "remote_device": "r9", "remote_if_name_canonical": "ge0/9", "protocol": "lldp"}),
			},
		},
	})
	if err != nil {
		t.Fatalf("Assemble returned error: %v", err)
	}
	if !hasAnalysisDiagnostic(snap, "interface_ip_without_interface") {
		t.Fatalf("expected interface_ip_without_interface diagnostic, got %#v", snap.Diagnostics)
	}
	if !hasAnalysisDiagnostic(snap, "topology_remote_unresolved") {
		t.Fatalf("expected topology_remote_unresolved diagnostic, got %#v", snap.Diagnostics)
	}
}

func hasAnalysisDiagnostic(snap *AnalysisSnapshot, code string) bool {
	for _, diagnostic := range snap.Diagnostics {
		if diagnostic.Code == code {
			return true
		}
	}
	return false
}
```

- [ ] **Step 4: Run tests**

```bash
go test -count=1 ./app/netpath/snapshot/provider
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/netpath/snapshot/provider/assembler.go app/netpath/snapshot/provider/assembler_test.go
git commit -m "feat: assemble netpath analysis snapshots"
```

## Task 4: Snapshot Quality Gate

**Files:**
- Create: `OneOPS/app/netpath/snapshot/provider/validator.go`
- Modify: `OneOPS/app/netpath/snapshot/provider/validator_test.go`

- [ ] **Step 1: Add validator implementation**

Create `OneOPS/app/netpath/snapshot/provider/validator.go`:

```go
package provider

import (
	"fmt"
	"net/netip"
	"strings"
)

type ValidateRequest struct {
	IngressDeviceCode string
	IngressVRF        string
}

type Validator struct{}

func NewValidator() *Validator {
	return &Validator{}
}

func (v *Validator) Validate(snapshot *AnalysisSnapshot, req ValidateRequest) SnapshotQuality {
	if snapshot == nil {
		return SnapshotQualityBlocked
	}
	snapshot.Diagnostics = append([]AnalysisDiagnostic(nil), snapshot.Diagnostics...)
	if strings.TrimSpace(snapshot.TenantCode) == "" {
		addValidationDiagnostic(snapshot, SeverityError, "tenant_scope_missing", "tenant_code is required for analysis snapshots", nil)
	}
	if len(snapshot.Devices) == 0 {
		addValidationDiagnostic(snapshot, SeverityError, "snapshot_devices_empty", "analysis snapshot must contain at least one device", nil)
	}

	deviceIndex := make(map[string]AnalysisDevice, len(snapshot.Devices))
	for _, device := range snapshot.Devices {
		if strings.TrimSpace(device.DeviceCode) == "" {
			addValidationDiagnostic(snapshot, SeverityError, "device_code_missing", "device code is required", nil)
			continue
		}
		if _, exists := deviceIndex[device.DeviceCode]; exists {
			addValidationDiagnostic(snapshot, SeverityError, "device_code_duplicate", "device code is duplicated", []string{device.DeviceCode})
		}
		deviceIndex[device.DeviceCode] = device
		validateRoutes(snapshot, device)
	}

	ingressCode := strings.TrimSpace(req.IngressDeviceCode)
	if ingressCode == "" {
		addValidationDiagnostic(snapshot, SeverityError, "ingress_device_missing", "ingress device is required for analysis", nil)
	} else if _, ok := deviceIndex[ingressCode]; !ok {
		addValidationDiagnostic(snapshot, SeverityError, "ingress_device_not_found", "ingress device is not present in analysis snapshot", []string{ingressCode})
	}

	if ingressDevice, ok := deviceIndex[ingressCode]; ok {
		vrf := normalizeVRF(req.IngressVRF)
		if !deviceHasRouteTable(ingressDevice, vrf) {
			addValidationDiagnostic(snapshot, SeverityError, "ingress_route_table_missing", "route table is missing for ingress device and vrf", []string{ingressCode, vrf})
		}
	}

	if hasSeverity(snapshot.Diagnostics, SeverityError) {
		snapshot.Quality = SnapshotQualityBlocked
		return snapshot.Quality
	}
	if hasSeverity(snapshot.Diagnostics, SeverityWarn) {
		snapshot.Quality = SnapshotQualityDegraded
		return snapshot.Quality
	}
	snapshot.Quality = SnapshotQualityReady
	return snapshot.Quality
}

func validateRoutes(snapshot *AnalysisSnapshot, device AnalysisDevice) {
	for _, table := range device.RouteTables {
		vrf := normalizeVRF(table.VRF)
		interfaceNames := interfacesByVRF(device.Interfaces, vrf)
		for _, route := range table.Routes {
			refs := []string{device.DeviceCode, vrf, route.Destination}
			if strings.TrimSpace(route.Destination) == "" {
				addValidationDiagnostic(snapshot, SeverityError, "route_destination_missing", "route destination is required", refs)
			} else if _, err := netip.ParsePrefix(route.Destination); err != nil {
				addValidationDiagnostic(snapshot, SeverityError, "route_destination_invalid", fmt.Sprintf("route destination is invalid: %v", err), refs)
			}
			if !route.NullRoute && strings.TrimSpace(route.OutInterfaceName) == "" {
				addValidationDiagnostic(snapshot, SeverityWarn, "route_out_interface_missing", "non-null route is missing out interface", refs)
				continue
			}
			if !route.NullRoute && strings.TrimSpace(route.OutInterfaceName) != "" {
				if _, ok := interfaceNames[route.OutInterfaceName]; !ok {
					addValidationDiagnostic(snapshot, SeverityWarn, "route_out_interface_unresolved", "route out interface does not match an interface in the same vrf", append(refs, route.OutInterfaceName))
				}
			}
		}
	}
}

func interfacesByVRF(interfaces []AnalysisInterface, vrf string) map[string]struct{} {
	out := make(map[string]struct{})
	for _, iface := range interfaces {
		if normalizeVRF(iface.VRF) != vrf {
			continue
		}
		if strings.TrimSpace(iface.InterfaceName) != "" {
			out[iface.InterfaceName] = struct{}{}
		}
		if strings.TrimSpace(iface.InterfaceCode) != "" {
			out[iface.InterfaceCode] = struct{}{}
		}
	}
	return out
}

func deviceHasRouteTable(device AnalysisDevice, vrf string) bool {
	for _, table := range device.RouteTables {
		if normalizeVRF(table.VRF) == vrf {
			return true
		}
	}
	return false
}

func addValidationDiagnostic(snapshot *AnalysisSnapshot, severity Severity, code string, message string, refs []string) {
	for _, diagnostic := range snapshot.Diagnostics {
		if diagnostic.Severity == severity && diagnostic.Code == code && strings.Join(diagnostic.Refs, "|") == strings.Join(refs, "|") {
			return
		}
	}
	snapshot.Diagnostics = append(snapshot.Diagnostics, AnalysisDiagnostic{
		Severity: severity,
		Code:     code,
		Message:  message,
		Refs:     append([]string(nil), refs...),
	})
}

func hasSeverity(diagnostics []AnalysisDiagnostic, severity Severity) bool {
	for _, diagnostic := range diagnostics {
		if diagnostic.Severity == severity {
			return true
		}
	}
	return false
}
```

- [ ] **Step 2: Add validator tests**

Append to `OneOPS/app/netpath/snapshot/provider/validator_test.go`:

```go
func TestValidatorClassifiesReadySnapshot(t *testing.T) {
	snap := readySnapshotForValidation()
	quality := NewValidator().Validate(snap, ValidateRequest{IngressDeviceCode: "r1", IngressVRF: "default"})
	if quality != SnapshotQualityReady {
		t.Fatalf("expected ready, got %q diagnostics=%#v", quality, snap.Diagnostics)
	}
	if snap.Quality != SnapshotQualityReady {
		t.Fatalf("expected snapshot quality ready, got %q", snap.Quality)
	}
}

func TestValidatorClassifiesDegradedSnapshot(t *testing.T) {
	snap := readySnapshotForValidation()
	snap.Devices[0].RouteTables[0].Routes[0].OutInterfaceName = "missing0"
	quality := NewValidator().Validate(snap, ValidateRequest{IngressDeviceCode: "r1", IngressVRF: "default"})
	if quality != SnapshotQualityDegraded {
		t.Fatalf("expected degraded, got %q diagnostics=%#v", quality, snap.Diagnostics)
	}
	if !hasAnalysisDiagnostic(snap, "route_out_interface_unresolved") {
		t.Fatalf("expected route_out_interface_unresolved diagnostic, got %#v", snap.Diagnostics)
	}
}

func TestValidatorClassifiesBlockedSnapshot(t *testing.T) {
	snap := readySnapshotForValidation()
	snap.Devices[0].RouteTables[0].Routes[0].Destination = "not-a-prefix"
	quality := NewValidator().Validate(snap, ValidateRequest{IngressDeviceCode: "r1", IngressVRF: "default"})
	if quality != SnapshotQualityBlocked {
		t.Fatalf("expected blocked, got %q diagnostics=%#v", quality, snap.Diagnostics)
	}
	if !hasAnalysisDiagnostic(snap, "route_destination_invalid") {
		t.Fatalf("expected route_destination_invalid diagnostic, got %#v", snap.Diagnostics)
	}
}

func TestValidatorBlocksMissingIngressRouteTable(t *testing.T) {
	snap := readySnapshotForValidation()
	quality := NewValidator().Validate(snap, ValidateRequest{IngressDeviceCode: "r1", IngressVRF: "blue"})
	if quality != SnapshotQualityBlocked {
		t.Fatalf("expected blocked, got %q diagnostics=%#v", quality, snap.Diagnostics)
	}
	if !hasAnalysisDiagnostic(snap, "ingress_route_table_missing") {
		t.Fatalf("expected ingress_route_table_missing diagnostic, got %#v", snap.Diagnostics)
	}
}

func readySnapshotForValidation() *AnalysisSnapshot {
	return &AnalysisSnapshot{
		SnapshotID: "snap-ready",
		TenantCode: "tenant-a",
		Devices: []AnalysisDevice{{
			DeviceCode: "r1",
			Interfaces: []AnalysisInterface{{
				InterfaceCode: "if-1",
				InterfaceName: "ge0/0",
				VRF: "default",
			}},
			RouteTables: []AnalysisRouteTable{{
				VRF: "default",
				Routes: []AnalysisRoute{{
					Destination: "10.0.2.0/24",
					OutInterfaceName: "ge0/0",
					Protocol: "static",
				}},
			}},
		}},
	}
}
```

- [ ] **Step 3: Run tests**

```bash
go test -count=1 ./app/netpath/snapshot/provider
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add app/netpath/snapshot/provider/validator.go app/netpath/snapshot/provider/validator_test.go
git commit -m "feat: validate netpath analysis snapshots"
```

## Task 5: Boundary Verification

**Files:**
- No source changes unless verification exposes a real bug.

- [ ] **Step 1: Run provider package tests**

```bash
go test -count=1 ./app/netpath/snapshot/provider
```

Expected: PASS.

- [ ] **Step 2: Run existing netpath package tests**

```bash
go test -count=1 ./app/netpath/snapshot ./app/netpath/dto ./app/netpath/engine ./app/netpath/service ./app/netpath/service/impl ./app/netpath/api ./app/netpath/adapter/oneopsnetpath ./app/netpath/snapshot/provider
```

Expected: PASS.

- [ ] **Step 3: Confirm dependency boundary**

```bash
git diff -- go.mod go.sum
```

Expected: no output.

```bash
rg -n "github.com/netxops/oneops-netpath" app/netpath/snapshot/provider app/netpath/snapshot go.mod
```

Expected: no output and exit code 1 is acceptable.

- [ ] **Step 4: Confirm committed files**

```bash
git log --oneline -4
```

Expected: recent commits include:

```text
feat: add netpath analysis snapshot model
feat: add netpath snapshot fact helpers
feat: assemble netpath analysis snapshots
feat: validate netpath analysis snapshots
```

## Execution Notes

- Existing unrelated dirty files in OneOPS must be ignored.
- Stage only files under `app/netpath/snapshot/provider`.
- Do not modify the existing preview builder in `app/netpath/snapshot` during this phase.
- Do not wire the provider into production service or adapter during this phase.
- If the assembler test import block conflicts with the helper test import, merge imports manually and run `gofmt`.
- If any test reveals mismatch with real `dc2dto.FactRecordResp` field names, inspect `app/device_collection2/dto/device_collection2.go` and update the plan implementation consistently.
