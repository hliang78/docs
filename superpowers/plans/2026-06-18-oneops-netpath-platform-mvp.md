# OneOPS NetPath Platform MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working slice of `oneops-netpath` and OneOPS integration: load a snapshot, simulate a concrete flow across route/topology data, persist a run in OneOPS, and expose a read-only result.

**Architecture:** `oneops-netpath` is an independent Go engine that accepts snapshot JSON and returns Batfish-style `Trace -> Hop -> Step -> Disposition` output. OneOPS owns snapshot construction, run persistence, API exposure, and future UI/probe/ticket workflows. nodemap is treated as a future firewall behavior plugin; this MVP adds the adapter boundary and model mapping but does not import ctrlhub packages yet.

**Tech Stack:** Go 1.22+, standard library `net/netip`, `encoding/json`, `net/http`; OneOPS Go/Gin/GORM patterns; TypeScript/Vue integration is planned as a follow-up after backend result shape stabilizes.

---

## Current Data Model Basis

This plan is based on the following model chain:

```text
OneOPS ConfigVersion/Topology/Device
  -> NetPath Snapshot
  -> Flow
  -> Engine traversal
  -> Trace
  -> Hop
  -> Step
  -> Disposition
```

The nodemap mapping for later firewall enrichment is:

```text
nodemap policy.Intent        -> netpath Flow
nodemap api.Node             -> netpath Device
nodemap api.Port             -> netpath Interface
nodemap FirewallProcess      -> netpath Hop evaluator
nodemap INPUT_NAT            -> netpath Step(pre_routing_nat)
nodemap INPUT_POLICY         -> netpath Step(security_policy)
nodemap OUTPUT_POLICY        -> netpath Step(egress_acl or security_policy)
nodemap OUTPUT_NAT           -> netpath Step(post_routing_nat)
nodemap WarningInfo          -> netpath Diagnostic
nodemap matched CLI/rule     -> netpath PolicyHit raw_ref/matched_object
```

## File Structure

### oneops-netpath

Create or modify these files in `/Users/huangliang/project/OneOPS-ALL/oneops-netpath`:

- `go.mod`: module definition.
- `cmd/netpathctl/main.go`: CLI entry point for local snapshot analysis.
- `internal/model/types.go`: core DTOs used by CLI/API/tests.
- `internal/model/validation.go`: input validation for snapshots and flows.
- `internal/routing/table.go`: route table parsing and longest-prefix match.
- `internal/topology/graph.go`: link lookup and next-hop device resolution.
- `internal/engine/engine.go`: packet traversal and trace construction.
- `internal/engine/disposition.go`: terminal disposition helpers.
- `internal/adapters/oneops/snapshot.go`: OneOPS snapshot normalization boundary.
- `testdata/simple-path.snapshot.json`: a passing route/topology fixture.
- `testdata/no-route.snapshot.json`: no-route fixture.
- `testdata/loop.snapshot.json`: loop fixture.
- `internal/routing/table_test.go`: routing unit tests.
- `internal/topology/graph_test.go`: topology unit tests.
- `internal/engine/engine_test.go`: end-to-end engine tests.

### OneOPS

Create or modify these files in `/Users/huangliang/project/OneOPS-ALL/OneOPS`:

- `app/netpath/dto/netpath.go`: OneOPS API DTOs mirroring engine request/result shape.
- `app/netpath/netpath_model/run.go`: MVP run persistence model.
- `app/netpath/service/i_netpath.go`: service interface.
- `app/netpath/service/impl/netpath.go`: service implementation using in-process fixture mode first.
- `app/netpath/api/netpath.go`: Gin API handlers.
- `app/netpath/router/netpath.go`: route registration.
- `initialize/routers.go`: add netpath router once service wiring is prepared.

The OneOPS wiring task is intentionally last because the project uses Wire and existing dependency assembly. The first OneOPS backend task can be implemented and tested as isolated service/API tests before full router integration.

## Task 1: oneops-netpath Module And Core Models

**Files:**
- Create: `/Users/huangliang/project/OneOPS-ALL/oneops-netpath/go.mod`
- Create: `/Users/huangliang/project/OneOPS-ALL/oneops-netpath/internal/model/types.go`
- Create: `/Users/huangliang/project/OneOPS-ALL/oneops-netpath/internal/model/validation.go`

- [ ] **Step 1: Initialize the Go module file**

Create `go.mod` with:

```go
module github.com/netxops/oneops-netpath

go 1.22
```

- [ ] **Step 2: Define the core model types**

Create `internal/model/types.go` with:

```go
package model

type Snapshot struct {
	SnapshotID     string       `json:"snapshot_id"`
	TenantCode     string       `json:"tenant_code"`
	GeneratedAt    string       `json:"generated_at,omitempty"`
	SourceVersions SourceRefs   `json:"source_versions,omitempty"`
	Devices        []Device     `json:"devices"`
	Links          []Link       `json:"links"`
	Diagnostics    []Diagnostic `json:"diagnostics,omitempty"`
}

type SourceRefs struct {
	ConfigVersionIDs []string `json:"config_version_ids,omitempty"`
	TopologySnapshot string   `json:"topology_snapshot,omitempty"`
	CollectionRuns   []string `json:"collection_runs,omitempty"`
}

type Device struct {
	DeviceCode       string            `json:"device_code"`
	DeviceName       string            `json:"device_name,omitempty"`
	DeviceType       string            `json:"device_type"`
	Vendor           string            `json:"vendor,omitempty"`
	Model            string            `json:"model,omitempty"`
	ManagementIP     string            `json:"management_ip,omitempty"`
	VRFs             []VRF             `json:"vrfs,omitempty"`
	Interfaces       []Interface       `json:"interfaces,omitempty"`
	RouteTables      []RouteTable      `json:"route_tables,omitempty"`
	FirewallModelRef string            `json:"firewall_model_ref,omitempty"`
	Metadata         map[string]string `json:"metadata,omitempty"`
}

type VRF struct {
	Name string `json:"name"`
}

type Interface struct {
	InterfaceCode   string   `json:"interface_code,omitempty"`
	InterfaceName   string   `json:"interface_name"`
	VRF             string   `json:"vrf,omitempty"`
	Zone            string   `json:"zone,omitempty"`
	IPv4Addresses   []string `json:"ipv4_addresses,omitempty"`
	Status          string   `json:"status,omitempty"`
	PeerDeviceCode  string   `json:"peer_device_code,omitempty"`
	PeerInterface   string   `json:"peer_interface,omitempty"`
	PeerInterfaceID string   `json:"peer_interface_code,omitempty"`
	Source          string   `json:"source,omitempty"`
}

type Link struct {
	ADeviceCode  string `json:"a_device_code"`
	AInterface   string `json:"a_interface"`
	BDeviceCode  string `json:"b_device_code"`
	BInterface   string `json:"b_interface"`
	Source       string `json:"source,omitempty"`
	Description  string `json:"description,omitempty"`
}

type RouteTable struct {
	VRF    string  `json:"vrf"`
	Routes []Route `json:"routes"`
}

type Route struct {
	Destination string `json:"destination"`
	NextHopIP   string `json:"next_hop_ip,omitempty"`
	OutInterface string `json:"out_interface,omitempty"`
	Protocol    string `json:"protocol,omitempty"`
	Metric      int    `json:"metric,omitempty"`
	Preference  int    `json:"preference,omitempty"`
	NullRoute   bool   `json:"null_route,omitempty"`
	Raw         string `json:"raw,omitempty"`
}

type Flow struct {
	SrcIP               string `json:"src_ip"`
	DstIP               string `json:"dst_ip"`
	Protocol            string `json:"protocol,omitempty"`
	SrcPort             int    `json:"src_port,omitempty"`
	DstPort             int    `json:"dst_port,omitempty"`
	IngressDeviceCode   string `json:"ingress_device_code"`
	IngressInterface    string `json:"ingress_interface,omitempty"`
	IngressVRF          string `json:"ingress_vrf,omitempty"`
	BusinessLabel       string `json:"business_label,omitempty"`
}

type AnalyzeRequest struct {
	Snapshot Snapshot `json:"snapshot"`
	Flow     Flow     `json:"flow"`
	Options  Options  `json:"options,omitempty"`
}

type Options struct {
	MaxHops   int `json:"max_hops,omitempty"`
	MaxTraces int `json:"max_traces,omitempty"`
}

type AnalyzeResponse struct {
	SnapshotID  string       `json:"snapshot_id"`
	Flow        Flow         `json:"flow"`
	Traces      []Trace      `json:"traces"`
	Diagnostics []Diagnostic `json:"diagnostics,omitempty"`
}

type Trace struct {
	TraceID     string       `json:"trace_id"`
	Disposition string       `json:"disposition"`
	Hops        []Hop        `json:"hops"`
	Diagnostics []Diagnostic `json:"diagnostics,omitempty"`
	Confidence  string       `json:"confidence,omitempty"`
}

type Hop struct {
	Sequence     int    `json:"sequence"`
	DeviceCode   string `json:"device_code"`
	InInterface  string `json:"in_interface,omitempty"`
	OutInterface string `json:"out_interface,omitempty"`
	InZone       string `json:"in_zone,omitempty"`
	OutZone      string `json:"out_zone,omitempty"`
	VRF          string `json:"vrf,omitempty"`
	Steps        []Step `json:"steps"`
}

type Step struct {
	Type          string            `json:"type"`
	Action        string            `json:"action,omitempty"`
	MatchedObject string            `json:"matched_object,omitempty"`
	RawRef        string            `json:"raw_ref,omitempty"`
	Message       string            `json:"message,omitempty"`
	Details       map[string]string `json:"details,omitempty"`
}

type Diagnostic struct {
	Severity string   `json:"severity"`
	Code     string   `json:"code"`
	Message  string   `json:"message"`
	Refs     []string `json:"refs,omitempty"`
}

const (
	DispositionAccepted            = "accepted"
	DispositionDeliveredToSubnet   = "delivered_to_subnet"
	DispositionExitsNetwork        = "exits_network"
	DispositionDeniedIn            = "denied_in"
	DispositionDeniedOut           = "denied_out"
	DispositionNoRoute             = "no_route"
	DispositionNullRouted          = "null_routed"
	DispositionLoop                = "loop"
	DispositionNeighborUnreachable = "neighbor_unreachable"
	DispositionInsufficientInfo    = "insufficient_info"
	DispositionEngineError         = "engine_error"
)
```

- [ ] **Step 3: Define validation helpers**

Create `internal/model/validation.go` with:

```go
package model

import (
	"fmt"
	"net/netip"
	"strings"
)

func ValidateAnalyzeRequest(req AnalyzeRequest) error {
	if strings.TrimSpace(req.Snapshot.SnapshotID) == "" {
		return fmt.Errorf("snapshot_id is required")
	}
	if len(req.Snapshot.Devices) == 0 {
		return fmt.Errorf("snapshot.devices must contain at least one device")
	}
	if strings.TrimSpace(req.Flow.IngressDeviceCode) == "" {
		return fmt.Errorf("flow.ingress_device_code is required")
	}
	if _, err := netip.ParseAddr(req.Flow.SrcIP); err != nil {
		return fmt.Errorf("flow.src_ip is invalid: %w", err)
	}
	if _, err := netip.ParseAddr(req.Flow.DstIP); err != nil {
		return fmt.Errorf("flow.dst_ip is invalid: %w", err)
	}
	return nil
}

func DefaultOptions(opts Options) Options {
	if opts.MaxHops <= 0 {
		opts.MaxHops = 64
	}
	if opts.MaxTraces <= 0 {
		opts.MaxTraces = 16
	}
	return opts
}
```

- [ ] **Step 4: Run formatting and tests**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/oneops-netpath
go test ./...
```

Expected: pass with no packages beyond model or with `?` no test files.

- [ ] **Step 5: Commit**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/oneops-netpath
git add go.mod internal/model
git commit -m "feat: define netpath core models"
```

## Task 2: Route Table Longest-Prefix Match

**Files:**
- Create: `/Users/huangliang/project/OneOPS-ALL/oneops-netpath/internal/routing/table.go`
- Create: `/Users/huangliang/project/OneOPS-ALL/oneops-netpath/internal/routing/table_test.go`

- [ ] **Step 1: Write route lookup tests**

Create `internal/routing/table_test.go` with:

```go
package routing

import (
	"testing"

	"github.com/netxops/oneops-netpath/internal/model"
)

func TestLookupUsesLongestPrefix(t *testing.T) {
	table, err := NewTable("default", []model.Route{
		{Destination: "0.0.0.0/0", NextHopIP: "10.0.0.1", OutInterface: "eth0", Protocol: "static"},
		{Destination: "10.20.0.0/16", NextHopIP: "10.0.0.2", OutInterface: "eth1", Protocol: "ospf"},
		{Destination: "10.20.30.0/24", NextHopIP: "10.0.0.3", OutInterface: "eth2", Protocol: "static"},
	})
	if err != nil {
		t.Fatalf("NewTable returned error: %v", err)
	}

	match, ok := table.Lookup("10.20.30.40")
	if !ok {
		t.Fatal("expected route match")
	}
	if match.Route.NextHopIP != "10.0.0.3" {
		t.Fatalf("expected longest prefix next-hop 10.0.0.3, got %q", match.Route.NextHopIP)
	}
	if match.Prefix.String() != "10.20.30.0/24" {
		t.Fatalf("expected /24 prefix, got %s", match.Prefix)
	}
}

func TestLookupReturnsNoMatchWhenNoDefault(t *testing.T) {
	table, err := NewTable("default", []model.Route{
		{Destination: "192.168.0.0/16", NextHopIP: "10.0.0.1", OutInterface: "eth0"},
	})
	if err != nil {
		t.Fatalf("NewTable returned error: %v", err)
	}

	_, ok := table.Lookup("10.1.1.1")
	if ok {
		t.Fatal("expected no route")
	}
}

func TestLookupReturnsNullRoute(t *testing.T) {
	table, err := NewTable("default", []model.Route{
		{Destination: "10.10.0.0/16", NullRoute: true, Protocol: "static"},
	})
	if err != nil {
		t.Fatalf("NewTable returned error: %v", err)
	}

	match, ok := table.Lookup("10.10.1.1")
	if !ok {
		t.Fatal("expected null route match")
	}
	if !match.Route.NullRoute {
		t.Fatal("expected null route flag")
	}
}

func TestNewTableRejectsInvalidPrefix(t *testing.T) {
	_, err := NewTable("default", []model.Route{{Destination: "bad-prefix"}})
	if err == nil {
		t.Fatal("expected invalid prefix error")
	}
}
```

- [ ] **Step 2: Run test and confirm failure**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/oneops-netpath
go test ./internal/routing
```

Expected: fail because `NewTable` is undefined.

- [ ] **Step 3: Implement route table**

Create `internal/routing/table.go` with:

```go
package routing

import (
	"fmt"
	"net/netip"
	"sort"

	"github.com/netxops/oneops-netpath/internal/model"
)

type Entry struct {
	Prefix netip.Prefix
	Route  model.Route
}

type Match struct {
	Prefix netip.Prefix
	Route  model.Route
}

type Table struct {
	VRF     string
	entries []Entry
}

func NewTable(vrf string, routes []model.Route) (*Table, error) {
	entries := make([]Entry, 0, len(routes))
	for _, route := range routes {
		prefix, err := netip.ParsePrefix(route.Destination)
		if err != nil {
			return nil, fmt.Errorf("parse route destination %q: %w", route.Destination, err)
		}
		entries = append(entries, Entry{Prefix: prefix.Masked(), Route: route})
	}
	sort.SliceStable(entries, func(i, j int) bool {
		return entries[i].Prefix.Bits() > entries[j].Prefix.Bits()
	})
	return &Table{VRF: vrf, entries: entries}, nil
}

func (t *Table) Lookup(ipText string) (Match, bool) {
	ip, err := netip.ParseAddr(ipText)
	if err != nil {
		return Match{}, false
	}
	for _, entry := range t.entries {
		if entry.Prefix.Contains(ip) {
			return Match{Prefix: entry.Prefix, Route: entry.Route}, true
		}
	}
	return Match{}, false
}
```

- [ ] **Step 4: Run route tests**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/oneops-netpath
go test ./internal/routing
```

Expected: pass.

- [ ] **Step 5: Commit**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/oneops-netpath
git add internal/routing
git commit -m "feat: add longest-prefix route lookup"
```

## Task 3: Topology Next-Hop Resolution

**Files:**
- Create: `/Users/huangliang/project/OneOPS-ALL/oneops-netpath/internal/topology/graph.go`
- Create: `/Users/huangliang/project/OneOPS-ALL/oneops-netpath/internal/topology/graph_test.go`

- [ ] **Step 1: Write topology graph tests**

Create `internal/topology/graph_test.go` with:

```go
package topology

import (
	"testing"

	"github.com/netxops/oneops-netpath/internal/model"
)

func TestPeerByInterfaceFindsLinkPeer(t *testing.T) {
	graph := NewGraph([]model.Link{{
		ADeviceCode: "r1",
		AInterface: "eth0",
		BDeviceCode: "r2",
		BInterface: "eth1",
		Source:      "lldp",
	}})

	peer, ok := graph.PeerByInterface("r1", "eth0")
	if !ok {
		t.Fatal("expected peer")
	}
	if peer.DeviceCode != "r2" || peer.Interface != "eth1" {
		t.Fatalf("unexpected peer: %#v", peer)
	}
}

func TestPeerByInterfaceIsBidirectional(t *testing.T) {
	graph := NewGraph([]model.Link{{
		ADeviceCode: "r1",
		AInterface: "eth0",
		BDeviceCode: "r2",
		BInterface: "eth1",
	}})

	peer, ok := graph.PeerByInterface("r2", "eth1")
	if !ok {
		t.Fatal("expected reverse peer")
	}
	if peer.DeviceCode != "r1" || peer.Interface != "eth0" {
		t.Fatalf("unexpected reverse peer: %#v", peer)
	}
}

func TestPeerByInterfaceReturnsFalseForMissingLink(t *testing.T) {
	graph := NewGraph(nil)
	_, ok := graph.PeerByInterface("r1", "eth0")
	if ok {
		t.Fatal("expected no peer")
	}
}
```

- [ ] **Step 2: Run test and confirm failure**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/oneops-netpath
go test ./internal/topology
```

Expected: fail because `NewGraph` is undefined.

- [ ] **Step 3: Implement topology graph**

Create `internal/topology/graph.go` with:

```go
package topology

import "github.com/netxops/oneops-netpath/internal/model"

type Peer struct {
	DeviceCode string
	Interface  string
	Source     string
}

type Graph struct {
	peers map[string]Peer
}

func NewGraph(links []model.Link) *Graph {
	g := &Graph{peers: make(map[string]Peer, len(links)*2)}
	for _, link := range links {
		aKey := key(link.ADeviceCode, link.AInterface)
		bKey := key(link.BDeviceCode, link.BInterface)
		g.peers[aKey] = Peer{DeviceCode: link.BDeviceCode, Interface: link.BInterface, Source: link.Source}
		g.peers[bKey] = Peer{DeviceCode: link.ADeviceCode, Interface: link.AInterface, Source: link.Source}
	}
	return g
}

func (g *Graph) PeerByInterface(deviceCode, interfaceName string) (Peer, bool) {
	peer, ok := g.peers[key(deviceCode, interfaceName)]
	return peer, ok
}

func key(deviceCode, interfaceName string) string {
	return deviceCode + "|" + interfaceName
}
```

- [ ] **Step 4: Run topology tests**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/oneops-netpath
go test ./internal/topology
```

Expected: pass.

- [ ] **Step 5: Commit**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/oneops-netpath
git add internal/topology
git commit -m "feat: add topology peer resolution"
```

## Task 4: Engine Traversal MVP

**Files:**
- Create: `/Users/huangliang/project/OneOPS-ALL/oneops-netpath/internal/engine/engine.go`
- Create: `/Users/huangliang/project/OneOPS-ALL/oneops-netpath/internal/engine/disposition.go`
- Create: `/Users/huangliang/project/OneOPS-ALL/oneops-netpath/internal/engine/engine_test.go`
- Create: `/Users/huangliang/project/OneOPS-ALL/oneops-netpath/testdata/simple-path.snapshot.json`
- Create: `/Users/huangliang/project/OneOPS-ALL/oneops-netpath/testdata/no-route.snapshot.json`
- Create: `/Users/huangliang/project/OneOPS-ALL/oneops-netpath/testdata/loop.snapshot.json`

- [ ] **Step 1: Add engine tests**

Create `internal/engine/engine_test.go` with:

```go
package engine

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/netxops/oneops-netpath/internal/model"
)

func loadRequest(t *testing.T, name string, flow model.Flow) model.AnalyzeRequest {
	t.Helper()
	data, err := os.ReadFile(filepath.Join("..", "..", "testdata", name))
	if err != nil {
		t.Fatalf("read fixture: %v", err)
	}
	var snapshot model.Snapshot
	if err := json.Unmarshal(data, &snapshot); err != nil {
		t.Fatalf("unmarshal fixture: %v", err)
	}
	return model.AnalyzeRequest{Snapshot: snapshot, Flow: flow}
}

func TestAnalyzeSimplePathAccepted(t *testing.T) {
	req := loadRequest(t, "simple-path.snapshot.json", model.Flow{
		SrcIP:             "10.0.1.10",
		DstIP:             "10.0.2.20",
		Protocol:          "tcp",
		DstPort:           443,
		IngressDeviceCode: "r1",
		IngressVRF:        "default",
	})

	resp, err := Analyze(req)
	if err != nil {
		t.Fatalf("Analyze returned error: %v", err)
	}
	if len(resp.Traces) != 1 {
		t.Fatalf("expected one trace, got %d", len(resp.Traces))
	}
	trace := resp.Traces[0]
	if trace.Disposition != model.DispositionDeliveredToSubnet {
		t.Fatalf("expected delivered_to_subnet, got %s", trace.Disposition)
	}
	if len(trace.Hops) != 2 {
		t.Fatalf("expected two hops, got %d", len(trace.Hops))
	}
	if trace.Hops[0].DeviceCode != "r1" || trace.Hops[1].DeviceCode != "r2" {
		t.Fatalf("unexpected hop devices: %#v", trace.Hops)
	}
}

func TestAnalyzeNoRoute(t *testing.T) {
	req := loadRequest(t, "no-route.snapshot.json", model.Flow{
		SrcIP:             "10.0.1.10",
		DstIP:             "203.0.113.20",
		IngressDeviceCode: "r1",
		IngressVRF:        "default",
	})

	resp, err := Analyze(req)
	if err != nil {
		t.Fatalf("Analyze returned error: %v", err)
	}
	if got := resp.Traces[0].Disposition; got != model.DispositionNoRoute {
		t.Fatalf("expected no_route, got %s", got)
	}
}

func TestAnalyzeLoop(t *testing.T) {
	req := loadRequest(t, "loop.snapshot.json", model.Flow{
		SrcIP:             "10.0.1.10",
		DstIP:             "10.99.0.1",
		IngressDeviceCode: "r1",
		IngressVRF:        "default",
	})

	resp, err := Analyze(req)
	if err != nil {
		t.Fatalf("Analyze returned error: %v", err)
	}
	if got := resp.Traces[0].Disposition; got != model.DispositionLoop {
		t.Fatalf("expected loop, got %s", got)
	}
}
```

- [ ] **Step 2: Add snapshot fixtures**

Create `testdata/simple-path.snapshot.json` with:

```json
{
  "snapshot_id": "simple-path",
  "tenant_code": "demo",
  "devices": [
    {
      "device_code": "r1",
      "device_type": "router",
      "vrfs": [{"name": "default"}],
      "interfaces": [{"interface_name": "eth0", "vrf": "default", "ipv4_addresses": ["10.0.12.1/30"]}],
      "route_tables": [{
        "vrf": "default",
        "routes": [{"destination": "10.0.2.0/24", "next_hop_ip": "10.0.12.2", "out_interface": "eth0", "protocol": "static"}]
      }]
    },
    {
      "device_code": "r2",
      "device_type": "router",
      "vrfs": [{"name": "default"}],
      "interfaces": [{"interface_name": "eth1", "vrf": "default", "ipv4_addresses": ["10.0.12.2/30"]}, {"interface_name": "eth2", "vrf": "default", "ipv4_addresses": ["10.0.2.1/24"]}],
      "route_tables": [{
        "vrf": "default",
        "routes": [{"destination": "10.0.2.0/24", "out_interface": "eth2", "protocol": "connected"}]
      }]
    }
  ],
  "links": [{"a_device_code": "r1", "a_interface": "eth0", "b_device_code": "r2", "b_interface": "eth1", "source": "lldp"}]
}
```

Create `testdata/no-route.snapshot.json` with:

```json
{
  "snapshot_id": "no-route",
  "tenant_code": "demo",
  "devices": [
    {
      "device_code": "r1",
      "device_type": "router",
      "vrfs": [{"name": "default"}],
      "interfaces": [{"interface_name": "eth0", "vrf": "default", "ipv4_addresses": ["10.0.1.1/24"]}],
      "route_tables": [{"vrf": "default", "routes": [{"destination": "10.0.1.0/24", "out_interface": "eth0", "protocol": "connected"}]}]
    }
  ],
  "links": []
}
```

Create `testdata/loop.snapshot.json` with:

```json
{
  "snapshot_id": "loop",
  "tenant_code": "demo",
  "devices": [
    {
      "device_code": "r1",
      "device_type": "router",
      "vrfs": [{"name": "default"}],
      "interfaces": [{"interface_name": "eth0", "vrf": "default", "ipv4_addresses": ["10.0.12.1/30"]}],
      "route_tables": [{"vrf": "default", "routes": [{"destination": "10.99.0.0/16", "next_hop_ip": "10.0.12.2", "out_interface": "eth0", "protocol": "static"}]}]
    },
    {
      "device_code": "r2",
      "device_type": "router",
      "vrfs": [{"name": "default"}],
      "interfaces": [{"interface_name": "eth1", "vrf": "default", "ipv4_addresses": ["10.0.12.2/30"]}],
      "route_tables": [{"vrf": "default", "routes": [{"destination": "10.99.0.0/16", "next_hop_ip": "10.0.12.1", "out_interface": "eth1", "protocol": "static"}]}]
    }
  ],
  "links": [{"a_device_code": "r1", "a_interface": "eth0", "b_device_code": "r2", "b_interface": "eth1", "source": "lldp"}]
}
```

- [ ] **Step 3: Run test and confirm failure**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/oneops-netpath
go test ./internal/engine
```

Expected: fail because `Analyze` is undefined.

- [ ] **Step 4: Implement disposition helper**

Create `internal/engine/disposition.go` with:

```go
package engine

import "github.com/netxops/oneops-netpath/internal/model"

func terminalTrace(flow model.Flow, disposition string, hops []model.Hop, message string) model.Trace {
	trace := model.Trace{
		TraceID:     "trace-1",
		Disposition: disposition,
		Hops:        hops,
		Confidence:  "medium",
	}
	if message != "" {
		trace.Diagnostics = append(trace.Diagnostics, model.Diagnostic{
			Severity: "info",
			Code:     disposition,
			Message:  message,
		})
	}
	return trace
}
```

- [ ] **Step 5: Implement traversal engine**

Create `internal/engine/engine.go` with:

```go
package engine

import (
	"fmt"
	"net/netip"

	"github.com/netxops/oneops-netpath/internal/model"
	"github.com/netxops/oneops-netpath/internal/routing"
	"github.com/netxops/oneops-netpath/internal/topology"
)

func Analyze(req model.AnalyzeRequest) (model.AnalyzeResponse, error) {
	if err := model.ValidateAnalyzeRequest(req); err != nil {
		return model.AnalyzeResponse{}, err
	}
	opts := model.DefaultOptions(req.Options)
	index, err := buildIndex(req.Snapshot)
	if err != nil {
		return model.AnalyzeResponse{}, err
	}
	trace := traverse(req.Flow, index, opts)
	return model.AnalyzeResponse{
		SnapshotID:  req.Snapshot.SnapshotID,
		Flow:        req.Flow,
		Traces:      []model.Trace{trace},
		Diagnostics: req.Snapshot.Diagnostics,
	}, nil
}

type snapshotIndex struct {
	devices map[string]model.Device
	tables  map[string]*routing.Table
	graph   *topology.Graph
}

func buildIndex(snapshot model.Snapshot) (*snapshotIndex, error) {
	idx := &snapshotIndex{
		devices: make(map[string]model.Device, len(snapshot.Devices)),
		tables:  make(map[string]*routing.Table, len(snapshot.Devices)),
		graph:   topology.NewGraph(snapshot.Links),
	}
	for _, device := range snapshot.Devices {
		idx.devices[device.DeviceCode] = device
		for _, rt := range device.RouteTables {
			table, err := routing.NewTable(rt.VRF, rt.Routes)
			if err != nil {
				return nil, fmt.Errorf("device %s vrf %s: %w", device.DeviceCode, rt.VRF, err)
			}
			idx.tables[tableKey(device.DeviceCode, rt.VRF)] = table
		}
	}
	return idx, nil
}

func traverse(flow model.Flow, idx *snapshotIndex, opts model.Options) model.Trace {
	currentDevice := flow.IngressDeviceCode
	currentVRF := flow.IngressVRF
	if currentVRF == "" {
		currentVRF = "default"
	}
	visited := map[string]bool{}
	hops := make([]model.Hop, 0, opts.MaxHops)

	for sequence := 1; sequence <= opts.MaxHops; sequence++ {
		device, ok := idx.devices[currentDevice]
		if !ok {
			return terminalTrace(flow, model.DispositionInsufficientInfo, hops, "current device is missing from snapshot")
		}
		visitKey := currentDevice + "|" + currentVRF + "|" + flow.DstIP
		if visited[visitKey] {
			return terminalTrace(flow, model.DispositionLoop, hops, "packet returned to a previously visited device and vrf")
		}
		visited[visitKey] = true

		hop := model.Hop{
			Sequence:   sequence,
			DeviceCode: currentDevice,
			VRF:        currentVRF,
			Steps: []model.Step{{
				Type:    "enter_interface",
				Action:  "entered",
				Message: "packet entered device",
			}},
		}

		if deviceOwnsDestination(device, currentVRF, flow.DstIP) {
			hop.Steps = append(hop.Steps, model.Step{
				Type:    "final_disposition",
				Action:  model.DispositionDeliveredToSubnet,
				Message: "destination is on a connected interface of this device",
			})
			hops = append(hops, hop)
			return terminalTrace(flow, model.DispositionDeliveredToSubnet, hops, "")
		}

		table := idx.tables[tableKey(currentDevice, currentVRF)]
		if table == nil {
			hop.Steps = append(hop.Steps, model.Step{
				Type:    "route_lookup",
				Action:  "missing_table",
				Message: "no route table for device and vrf",
			})
			hops = append(hops, hop)
			return terminalTrace(flow, model.DispositionNoRoute, hops, "no route table for current device and vrf")
		}
		match, ok := table.Lookup(flow.DstIP)
		if !ok {
			hop.Steps = append(hop.Steps, model.Step{
				Type:    "route_lookup",
				Action:  "no_match",
				Message: "no route matched destination",
			})
			hops = append(hops, hop)
			return terminalTrace(flow, model.DispositionNoRoute, hops, "no route matched destination")
		}
		hop.OutInterface = match.Route.OutInterface
		hop.Steps = append(hop.Steps, model.Step{
			Type:          "route_lookup",
			Action:        "matched",
			MatchedObject: match.Prefix.String(),
			RawRef:        match.Route.Raw,
			Message:       "route selected by longest-prefix match",
		})
		if match.Route.NullRoute {
			hops = append(hops, hop)
			return terminalTrace(flow, model.DispositionNullRouted, hops, "matched route is a null route")
		}
		if match.Route.OutInterface == "" {
			hops = append(hops, hop)
			return terminalTrace(flow, model.DispositionInsufficientInfo, hops, "matched route has no output interface")
		}
		peer, ok := idx.graph.PeerByInterface(currentDevice, match.Route.OutInterface)
		if !ok {
			if routeDeliversToSubnet(device, currentVRF, match.Route.OutInterface, flow.DstIP) {
				hops = append(hops, hop)
				return terminalTrace(flow, model.DispositionDeliveredToSubnet, hops, "route exits to directly connected destination subnet")
			}
			hops = append(hops, hop)
			return terminalTrace(flow, model.DispositionNeighborUnreachable, hops, "no topology peer for selected output interface")
		}
		hop.Steps = append(hop.Steps, model.Step{
			Type:    "exit_interface",
			Action:  "forwarded",
			Message: "packet forwarded to topology peer",
			Details: map[string]string{
				"peer_device_code": peer.DeviceCode,
				"peer_interface":   peer.Interface,
			},
		})
		hops = append(hops, hop)
		currentDevice = peer.DeviceCode
	}
	return terminalTrace(flow, model.DispositionLoop, hops, "maximum hop count reached before terminal disposition")
}

func tableKey(deviceCode, vrf string) string {
	if vrf == "" {
		vrf = "default"
	}
	return deviceCode + "|" + vrf
}

func deviceOwnsDestination(device model.Device, vrf, dstIP string) bool {
	return routeDeliversToSubnet(device, vrf, "", dstIP)
}

func routeDeliversToSubnet(device model.Device, vrf, outInterface, dstIP string) bool {
	dst, err := netip.ParseAddr(dstIP)
	if err != nil {
		return false
	}
	for _, iface := range device.Interfaces {
		if vrf != "" && iface.VRF != "" && iface.VRF != vrf {
			continue
		}
		if outInterface != "" && iface.InterfaceName != outInterface && iface.InterfaceCode != outInterface {
			continue
		}
		for _, cidr := range iface.IPv4Addresses {
			prefix, err := netip.ParsePrefix(cidr)
			if err == nil && prefix.Contains(dst) {
				return true
			}
		}
	}
	return false
}
```

- [ ] **Step 6: Run engine tests**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/oneops-netpath
go test ./internal/engine
```

Expected: pass.

- [ ] **Step 7: Run all engine repository tests**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/oneops-netpath
go test ./...
```

Expected: pass.

- [ ] **Step 8: Commit**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/oneops-netpath
git add internal/engine testdata
git commit -m "feat: add basic netpath traversal engine"
```

## Task 5: CLI Analyze Command

**Files:**
- Create: `/Users/huangliang/project/OneOPS-ALL/oneops-netpath/cmd/netpathctl/main.go`

- [ ] **Step 1: Add CLI command**

Create `cmd/netpathctl/main.go` with:

```go
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"

	"github.com/netxops/oneops-netpath/internal/engine"
	"github.com/netxops/oneops-netpath/internal/model"
)

func main() {
	snapshotPath := flag.String("snapshot", "", "path to snapshot JSON")
	srcIP := flag.String("src-ip", "", "source IP")
	dstIP := flag.String("dst-ip", "", "destination IP")
	protocol := flag.String("protocol", "tcp", "protocol")
	dstPort := flag.Int("dst-port", 0, "destination port")
	ingressDevice := flag.String("ingress-device", "", "ingress device code")
	ingressVRF := flag.String("ingress-vrf", "default", "ingress VRF")
	flag.Parse()

	if *snapshotPath == "" || *srcIP == "" || *dstIP == "" || *ingressDevice == "" {
		fmt.Fprintln(os.Stderr, "required flags: -snapshot -src-ip -dst-ip -ingress-device")
		os.Exit(2)
	}

	data, err := os.ReadFile(*snapshotPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "read snapshot: %v\n", err)
		os.Exit(1)
	}
	var snapshot model.Snapshot
	if err := json.Unmarshal(data, &snapshot); err != nil {
		fmt.Fprintf(os.Stderr, "parse snapshot: %v\n", err)
		os.Exit(1)
	}
	resp, err := engine.Analyze(model.AnalyzeRequest{
		Snapshot: snapshot,
		Flow: model.Flow{
			SrcIP:             *srcIP,
			DstIP:             *dstIP,
			Protocol:          *protocol,
			DstPort:           *dstPort,
			IngressDeviceCode: *ingressDevice,
			IngressVRF:        *ingressVRF,
		},
	})
	if err != nil {
		fmt.Fprintf(os.Stderr, "analyze: %v\n", err)
		os.Exit(1)
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	if err := enc.Encode(resp); err != nil {
		fmt.Fprintf(os.Stderr, "write response: %v\n", err)
		os.Exit(1)
	}
}
```

- [ ] **Step 2: Run CLI against passing fixture**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/oneops-netpath
go run ./cmd/netpathctl \
  -snapshot testdata/simple-path.snapshot.json \
  -src-ip 10.0.1.10 \
  -dst-ip 10.0.2.20 \
  -protocol tcp \
  -dst-port 443 \
  -ingress-device r1
```

Expected: JSON output contains `"disposition": "delivered_to_subnet"` and two hops.

- [ ] **Step 3: Run all tests**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/oneops-netpath
go test ./...
```

Expected: pass.

- [ ] **Step 4: Commit**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/oneops-netpath
git add cmd/netpathctl
git commit -m "feat: add netpath analysis cli"
```

## Task 6: OneOPS NetPath DTO And Isolated Service Contract

**Files:**
- Create: `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/netpath/dto/netpath.go`
- Create: `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/netpath/service/i_netpath.go`

- [ ] **Step 1: Add DTOs**

Create `app/netpath/dto/netpath.go` with:

```go
package dto

type SnapshotPreviewReq struct {
	TenantCode string   `json:"tenant_code"`
	DeviceCodes []string `json:"device_codes,omitempty"`
}

type SnapshotPreviewResp struct {
	SnapshotID string   `json:"snapshot_id"`
	TenantCode string   `json:"tenant_code"`
	Devices    int      `json:"devices"`
	Links      int      `json:"links"`
	Warnings   []string `json:"warnings,omitempty"`
}

type AnalyzeRunCreateReq struct {
	TenantCode          string `json:"tenant_code"`
	SnapshotID          string `json:"snapshot_id,omitempty"`
	SrcIP               string `json:"src_ip"`
	DstIP               string `json:"dst_ip"`
	Protocol            string `json:"protocol,omitempty"`
	SrcPort             int    `json:"src_port,omitempty"`
	DstPort             int    `json:"dst_port,omitempty"`
	IngressDeviceCode   string `json:"ingress_device_code"`
	IngressInterface    string `json:"ingress_interface,omitempty"`
	IngressVRF          string `json:"ingress_vrf,omitempty"`
	BusinessLabel       string `json:"business_label,omitempty"`
}

type AnalyzeRunResp struct {
	Code        string                 `json:"code"`
	TenantCode  string                 `json:"tenant_code"`
	SnapshotID  string                 `json:"snapshot_id"`
	Status      string                 `json:"status"`
	Disposition string                 `json:"disposition,omitempty"`
	Request     AnalyzeRunCreateReq    `json:"request"`
	Result      map[string]interface{} `json:"result,omitempty"`
	Error       string                 `json:"error,omitempty"`
	CreatedAt   int64                  `json:"created_at,omitempty"`
	UpdatedAt   int64                  `json:"updated_at,omitempty"`
}
```

- [ ] **Step 2: Add service interface**

Create `app/netpath/service/i_netpath.go` with:

```go
package service

import (
	"context"

	"github.com/netxops/OneOps/app/netpath/dto"
)

type INetPathService interface {
	PreviewSnapshot(ctx context.Context, req dto.SnapshotPreviewReq) (*dto.SnapshotPreviewResp, error)
	CreateAnalyzeRun(ctx context.Context, req dto.AnalyzeRunCreateReq) (*dto.AnalyzeRunResp, error)
	GetAnalyzeRun(ctx context.Context, code string) (*dto.AnalyzeRunResp, error)
}
```

- [ ] **Step 3: Run package compile**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/netpath/dto ./app/netpath/service
```

Expected: pass.

- [ ] **Step 4: Commit**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
git add app/netpath/dto app/netpath/service
git commit -m "feat: add netpath service contract"
```

## Task 7: OneOPS NetPath MVP Service With JSON Result Storage

**Files:**
- Create: `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/netpath/netpath_model/run.go`
- Create: `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/netpath/service/impl/netpath.go`
- Create: `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/netpath/service/impl/netpath_test.go`

- [ ] **Step 1: Add service tests**

Create `app/netpath/service/impl/netpath_test.go` with:

```go
package impl

import (
	"context"
	"testing"

	"github.com/netxops/OneOps/app/netpath/dto"
)

func TestNetPathServicePreviewSnapshotUsesRequestTenant(t *testing.T) {
	s := NewNetPathService(nil)
	resp, err := s.PreviewSnapshot(context.Background(), dto.SnapshotPreviewReq{TenantCode: "demo"})
	if err != nil {
		t.Fatalf("PreviewSnapshot returned error: %v", err)
	}
	if resp.TenantCode != "demo" {
		t.Fatalf("expected tenant demo, got %s", resp.TenantCode)
	}
	if resp.SnapshotID == "" {
		t.Fatal("expected snapshot id")
	}
}

func TestNetPathServiceCreateAndGetRun(t *testing.T) {
	s := NewNetPathService(nil)
	created, err := s.CreateAnalyzeRun(context.Background(), dto.AnalyzeRunCreateReq{
		TenantCode:        "demo",
		SrcIP:             "10.0.1.10",
		DstIP:             "10.0.2.20",
		Protocol:          "tcp",
		DstPort:           443,
		IngressDeviceCode: "r1",
		IngressVRF:        "default",
	})
	if err != nil {
		t.Fatalf("CreateAnalyzeRun returned error: %v", err)
	}
	if created.Code == "" {
		t.Fatal("expected run code")
	}
	if created.Status != "completed" {
		t.Fatalf("expected completed, got %s", created.Status)
	}

	got, err := s.GetAnalyzeRun(context.Background(), created.Code)
	if err != nil {
		t.Fatalf("GetAnalyzeRun returned error: %v", err)
	}
	if got.Code != created.Code {
		t.Fatalf("expected code %s, got %s", created.Code, got.Code)
	}
}
```

- [ ] **Step 2: Run test and confirm failure**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/netpath/service/impl
```

Expected: fail because `NewNetPathService` is undefined.

- [ ] **Step 3: Add persistence model**

Create `app/netpath/netpath_model/run.go` with:

```go
package netpath_model

import "time"

type NetPathAnalysisRun struct {
	ID          uint      `gorm:"primarykey" json:"id"`
	Code        string    `gorm:"column:code;uniqueIndex;size:64" json:"code"`
	TenantCode  string    `gorm:"column:tenant_code;size:64;index" json:"tenant_code"`
	SnapshotID  string    `gorm:"column:snapshot_id;size:128;index" json:"snapshot_id"`
	Status      string    `gorm:"column:status;size:32;index" json:"status"`
	Disposition string    `gorm:"column:disposition;size:64;index" json:"disposition"`
	RequestJSON string    `gorm:"column:request_json;type:text" json:"request_json"`
	ResultJSON  string    `gorm:"column:result_json;type:longtext" json:"result_json"`
	Error       string    `gorm:"column:error;type:text" json:"error"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

func (NetPathAnalysisRun) TableName() string {
	return "netpath_analysis_run"
}
```

- [ ] **Step 4: Implement in-memory MVP service**

Create `app/netpath/service/impl/netpath.go` with:

```go
package impl

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/netxops/OneOps/app/netpath/dto"
	"gorm.io/gorm"
)

type NetPathService struct {
	db    *gorm.DB
	mutex sync.RWMutex
	runs  map[string]*dto.AnalyzeRunResp
}

func NewNetPathService(db *gorm.DB) *NetPathService {
	return &NetPathService{db: db, runs: make(map[string]*dto.AnalyzeRunResp)}
}

func (s *NetPathService) PreviewSnapshot(ctx context.Context, req dto.SnapshotPreviewReq) (*dto.SnapshotPreviewResp, error) {
	if req.TenantCode == "" {
		return nil, fmt.Errorf("tenant_code is required")
	}
	return &dto.SnapshotPreviewResp{
		SnapshotID: "preview-" + req.TenantCode,
		TenantCode: req.TenantCode,
		Devices:    len(req.DeviceCodes),
		Links:      0,
		Warnings:   []string{"MVP preview uses request metadata only until snapshot builder is implemented"},
	}, nil
}

func (s *NetPathService) CreateAnalyzeRun(ctx context.Context, req dto.AnalyzeRunCreateReq) (*dto.AnalyzeRunResp, error) {
	if req.TenantCode == "" {
		return nil, fmt.Errorf("tenant_code is required")
	}
	if req.SrcIP == "" || req.DstIP == "" || req.IngressDeviceCode == "" {
		return nil, fmt.Errorf("src_ip, dst_ip, and ingress_device_code are required")
	}
	now := time.Now().Unix()
	code := fmt.Sprintf("npr-%d", time.Now().UnixNano())
	if req.SnapshotID == "" {
		req.SnapshotID = "preview-" + req.TenantCode
	}
	result := map[string]interface{}{
		"snapshot_id": req.SnapshotID,
		"flow": map[string]interface{}{
			"src_ip":              req.SrcIP,
			"dst_ip":              req.DstIP,
			"protocol":            req.Protocol,
			"src_port":            req.SrcPort,
			"dst_port":            req.DstPort,
			"ingress_device_code": req.IngressDeviceCode,
			"ingress_vrf":         req.IngressVRF,
		},
		"traces": []map[string]interface{}{
			{
				"trace_id":    "trace-1",
				"disposition": "engine_pending",
				"hops":        []interface{}{},
				"diagnostics": []map[string]string{{"severity": "info", "code": "engine_not_wired", "message": "OneOPS service contract is ready; external engine wiring follows in the next task"}},
			},
		},
	}
	encoded, err := json.Marshal(result)
	if err != nil {
		return nil, err
	}
	var decoded map[string]interface{}
	if err := json.Unmarshal(encoded, &decoded); err != nil {
		return nil, err
	}
	resp := &dto.AnalyzeRunResp{
		Code:        code,
		TenantCode:  req.TenantCode,
		SnapshotID:  req.SnapshotID,
		Status:      "completed",
		Disposition: "engine_pending",
		Request:     req,
		Result:      decoded,
		CreatedAt:   now,
		UpdatedAt:   now,
	}
	s.mutex.Lock()
	s.runs[code] = resp
	s.mutex.Unlock()
	return resp, nil
}

func (s *NetPathService) GetAnalyzeRun(ctx context.Context, code string) (*dto.AnalyzeRunResp, error) {
	s.mutex.RLock()
	defer s.mutex.RUnlock()
	run, ok := s.runs[code]
	if !ok {
		return nil, fmt.Errorf("netpath analysis run not found: %s", code)
	}
	return run, nil
}
```

- [ ] **Step 5: Run service tests**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/netpath/service/impl
```

Expected: pass.

- [ ] **Step 6: Commit**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
git add app/netpath/netpath_model app/netpath/service/impl
git commit -m "feat: add netpath mvp service"
```

## Task 8: OneOPS NetPath API Handlers

**Files:**
- Create: `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/netpath/api/netpath.go`
- Create: `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/netpath/api/netpath_test.go`

- [ ] **Step 1: Add API handler test**

Create `app/netpath/api/netpath_test.go` with:

```go
package api

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/netxops/OneOps/app/netpath/dto"
	"github.com/netxops/OneOps/app/netpath/service/impl"
)

func TestNetPathAPICreateAnalyzeRun(t *testing.T) {
	gin.SetMode(gin.TestMode)
	api := &NetPathAPI{NetPathSrv: impl.NewNetPathService(nil)}
	r := gin.New()
	r.POST("/netpath/analysis-runs", api.CreateAnalyzeRun)

	body, _ := json.Marshal(dto.AnalyzeRunCreateReq{
		TenantCode:        "demo",
		SrcIP:             "10.0.1.10",
		DstIP:             "10.0.2.20",
		IngressDeviceCode: "r1",
	})
	req := httptest.NewRequest(http.MethodPost, "/netpath/analysis-runs", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected status 200, got %d body=%s", w.Code, w.Body.String())
	}
	if !bytes.Contains(w.Body.Bytes(), []byte("engine_pending")) {
		t.Fatalf("expected engine_pending in response, got %s", w.Body.String())
	}
}
```

- [ ] **Step 2: Run test and confirm failure**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/netpath/api
```

Expected: fail because `NetPathAPI` is undefined.

- [ ] **Step 3: Implement API handlers**

Create `app/netpath/api/netpath.go` with:

```go
package api

import (
	"github.com/gin-gonic/gin"
	"github.com/netxops/OneOps/app/netpath/dto"
	"github.com/netxops/OneOps/app/netpath/service"
	"github.com/netxops/OneOps/pkg/bind"
	"github.com/netxops/OneOps/pkg/response"
	"go.uber.org/zap"
)

type NetPathAPI struct {
	Logger     *zap.Logger
	NetPathSrv service.INetPathService
}

func (a *NetPathAPI) PreviewSnapshot(ctx *gin.Context) {
	var req dto.SnapshotPreviewReq
	if ok := bind.JSON(&req, ctx); !ok {
		return
	}
	resp, err := a.NetPathSrv.PreviewSnapshot(ctx, req)
	if err != nil {
		response.FailWithMsg(err.Error(), ctx)
		return
	}
	response.OkWithData(resp, ctx)
}

func (a *NetPathAPI) CreateAnalyzeRun(ctx *gin.Context) {
	var req dto.AnalyzeRunCreateReq
	if ok := bind.JSON(&req, ctx); !ok {
		return
	}
	resp, err := a.NetPathSrv.CreateAnalyzeRun(ctx, req)
	if err != nil {
		response.FailWithMsg(err.Error(), ctx)
		return
	}
	response.OkWithData(resp, ctx)
}

func (a *NetPathAPI) GetAnalyzeRun(ctx *gin.Context) {
	code := ctx.Param("code")
	resp, err := a.NetPathSrv.GetAnalyzeRun(ctx, code)
	if err != nil {
		response.FailWithMsg(err.Error(), ctx)
		return
	}
	response.OkWithData(resp, ctx)
}
```

- [ ] **Step 4: Run API tests**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/netpath/api
```

Expected: pass.

- [ ] **Step 5: Commit**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
git add app/netpath/api
git commit -m "feat: add netpath api handlers"
```

## Task 9: Document The nodemap Adapter Boundary

**Files:**
- Create: `/Users/huangliang/project/OneOPS-ALL/oneops-netpath/docs/nodemap-adapter.md`
- Modify: `/Users/huangliang/project/OneOPS-ALL/oneops-netpath/README.md`

- [ ] **Step 1: Add nodemap adapter document**

Create `docs/nodemap-adapter.md` with:

```markdown
# nodemap Adapter Boundary

`oneops-netpath` extends the packet traversal idea from nodemap, but does not directly import the full ctrlhub/controller tree in the MVP.

## Mapping

| nodemap concept | netpath concept | Notes |
| --- | --- | --- |
| `policy.Intent` | `model.Flow` | Concrete source, destination, service, and optional NAT intent. |
| `api.Node` | `model.Device` | Snapshot-owned device identity. |
| `api.Port` | `model.Interface` | Interface, VRF, zone, and addressing. |
| `FirewallProcess` | Hop evaluator | Produces device-internal steps. |
| `INPUT_NAT` | `pre_routing_nat` step | Destination or input-side NAT. |
| `INPUT_POLICY` | `security_policy` step | Main firewall allow/deny decision. |
| `OUTPUT_POLICY` | `egress_acl` or `security_policy` step | Vendor-specific output policy. |
| `OUTPUT_NAT` | `post_routing_nat` step | Source or output-side NAT. |
| `WarningInfo` | `Diagnostic` | Unsupported syntax, skipped rules, ambiguous order. |

## MVP Rule

The MVP snapshot may carry firewall data as JSON, but the first engine implementation only routes across topology and reports where a firewall behavior plugin would be invoked.

## P1 Rule

P1 introduces a small compatibility model derived from ctrlhub firewall v2 semantic structures:

- policy order
- NAT stage
- zones
- address selectors
- service selectors
- diagnostics
- raw CLI references

The adapter must return explainable steps and never silently treat unsupported rules as permits.
```

- [ ] **Step 2: Update README**

Replace `README.md` content with:

```markdown
# oneops-netpath

`oneops-netpath` is the independent Go packet journey engine for OneOPS.

It evaluates a concrete business flow against a prepared snapshot and returns:

- trace
- hops
- steps
- route matches
- future firewall/NAT policy hits
- final disposition

The project references Batfish concepts such as Flow, FIB, Trace, Hop, Step, and Disposition, while keeping the MVP small and Go-native.

## MVP

The MVP supports:

- JSON snapshot input
- static, connected, default, and null routes
- longest-prefix match
- topology peer traversal
- no-route, loop, neighbor-unreachable, and delivered-to-subnet dispositions
- CLI execution through `cmd/netpathctl`

## OneOPS Integration

OneOPS owns snapshot generation, run persistence, UI, probing, and ticket workflow.

## nodemap

nodemap firewall traverse/runtime is treated as the future firewall behavior plugin source. See `docs/nodemap-adapter.md`.
```

- [ ] **Step 3: Commit**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/oneops-netpath
git add README.md docs/nodemap-adapter.md
git commit -m "docs: document nodemap adapter boundary"
```

## Verification Before Completion

Run these commands after all tasks in this MVP batch:

```bash
cd /Users/huangliang/project/OneOPS-ALL/oneops-netpath
go test ./...
go run ./cmd/netpathctl -snapshot testdata/simple-path.snapshot.json -src-ip 10.0.1.10 -dst-ip 10.0.2.20 -protocol tcp -dst-port 443 -ingress-device r1
```

Expected:

- `go test ./...` passes.
- CLI output includes `"disposition": "delivered_to_subnet"`.

Then run OneOPS isolated checks:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/netpath/dto ./app/netpath/service ./app/netpath/service/impl ./app/netpath/api
```

Expected:

- all packages pass.

## Deferred Work

These items are not part of this MVP implementation plan:

- Full OneOPS Wire/router integration.
- OneOPS-UI page.
- External `netpathd` HTTP client.
- Snapshot builder from real config version tables.
- Firewall semantic evaluator.
- Probe Orchestrator execution.
- Ticket creation.

They should become the next implementation plan after this MVP proves the core model and trace shape.

## Self-Review Notes

Spec coverage:

- `oneops-netpath` independent engine: covered by Tasks 1 to 5.
- Core data model: covered by Task 1.
- route/topology traversal: covered by Tasks 2 to 4.
- OneOPS thin integration: covered by Tasks 6 to 8.
- nodemap mapping: covered by Task 9.
- Probe Orchestrator: intentionally deferred because it depends on stable path result persistence.

Type consistency:

- The plan consistently uses `Snapshot`, `Flow`, `AnalyzeRequest`, `AnalyzeResponse`, `Trace`, `Hop`, and `Step`.
- OneOPS DTOs intentionally mirror but do not import `oneops-netpath` packages.

Execution rule:

- Complete tasks in order.
- Commit after each task.
- Do not start router/Wire/UI work until the MVP service and engine tests pass.
