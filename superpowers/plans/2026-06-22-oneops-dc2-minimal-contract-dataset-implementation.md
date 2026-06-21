# OneOPS DC2 Minimal Contract Dataset Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align `OneOps` DC2 processors and first-phase consumers with the frozen minimal shared dataset contract for `route_table`, `interface_ip`, `arp_entry`, `mac_table_entry`, and `topology_neighbor`.

**Architecture:** Codify a small frozen-fact registry in `device_collection2/fact`, then harden dataset processors so their normalized fields, provenance, and quality semantics match the spec. Keep NetPath and IPAM aligned by reusing the shared fact-family definitions and adding consumer-facing tests before changing any default behavior.

**Tech Stack:** Go, existing `device_collection2` fact processors, NetPath snapshot/provider code, IPAM canonical projection API/service tests, Markdown docs in nested `docs/` repo.

---

## File Structure

### Shared contract registry

- Create: `OneOps/app/device_collection2/fact/frozen_registry.go`
- Create: `OneOps/app/device_collection2/fact/frozen_registry_test.go`
- Responsibility:
  - define the five first-phase frozen fact types in one place
  - expose helpers that NetPath and IPAM can reuse instead of open-coding string lists
  - label unsupported families as outside the shared frozen surface

### DC2 processor hardening

- Modify: `OneOps/app/device_collection2/fact/route_policy_processor.go`
- Modify: `OneOps/app/device_collection2/fact/interface_ip_processor.go`
- Modify: `OneOps/app/device_collection2/fact/topology_processor.go`
- Modify: `OneOps/app/device_collection2/fact/route_policy_processor_test.go`
- Modify: `OneOps/app/device_collection2/service/impl/device_collection2_test.go`
- Responsibility:
  - match the spec for required fields, join-anchor rules, direct-route behavior, confidence lowering, and provenance completeness
  - bump processor provenance versions when normalized contract semantics change

### Consumer alignment

- Modify: `OneOps/app/netpath/snapshot/provider/facts.go`
- Modify: `OneOps/app/netpath/snapshot/builder_test.go`
- Modify: `OneOps/app/ipam/api/ip_address_fact.go`
- Modify: `OneOps/app/ipam/api/ip_address_fact_test.go`
- Modify: `OneOps/app/ipam/service/impl/ip_address_fact_test.go`
- Responsibility:
  - make consumer code use the shared frozen registry helpers where practical
  - verify IPAM default projection behavior versus explicit `fact_type` requests
  - verify NetPath still treats `route_table/interface_ip/topology_neighbor` as readiness anchors and `arp_entry/mac_table_entry` as supporting evidence

### Docs follow-up

- Modify: `docs/superpowers/specs/2026-06-22-oneops-dc2-minimal-contract-dataset-design.md`
- Responsibility:
  - record any implementation-driven clarifications discovered during code alignment
  - keep the spec and implementation plan in sync

## Task 1: Add Shared Frozen Fact Registry

**Files:**
- Create: `OneOps/app/device_collection2/fact/frozen_registry.go`
- Test: `OneOps/app/device_collection2/fact/frozen_registry_test.go`
- Modify: `OneOps/app/netpath/snapshot/provider/facts.go`

- [ ] **Step 1: Write the failing registry test**

```go
package fact

import "testing"

func TestFrozenFactTypesPhaseOne(t *testing.T) {
	got := FrozenFactTypes()
	want := []string{
		FactTypeRouteTable,
		FactTypeInterfaceIP,
		FactTypeARPEntry,
		FactTypeMACTableEntry,
		FactTypeTopologyNeighbor,
	}
	if len(got) != len(want) {
		t.Fatalf("unexpected frozen fact count: got=%v want=%v", got, want)
	}
	for i := range want {
		if got[i] != want[i] {
			t.Fatalf("unexpected frozen fact order: got=%v want=%v", got, want)
		}
	}
	if !IsFrozenFactType(FactTypeRouteTable) {
		t.Fatal("expected route_table to be frozen")
	}
	if IsFrozenFactType("firewall_policy") {
		t.Fatal("did not expect firewall_policy to be frozen")
	}
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `go test ./app/device_collection2/fact -run TestFrozenFactTypesPhaseOne -count=1`

Expected: FAIL with errors such as `undefined: FrozenFactTypes` and `undefined: FactTypeRouteTable`.

- [ ] **Step 3: Add the minimal shared registry**

```go
package fact

import "strings"

const (
	FactTypeRouteTable       = "route_table"
	FactTypeInterfaceIP      = "interface_ip"
	FactTypeARPEntry         = "arp_entry"
	FactTypeMACTableEntry    = "mac_table_entry"
	FactTypeTopologyNeighbor = "topology_neighbor"
)

var frozenFactTypes = []string{
	FactTypeRouteTable,
	FactTypeInterfaceIP,
	FactTypeARPEntry,
	FactTypeMACTableEntry,
	FactTypeTopologyNeighbor,
}

func FrozenFactTypes() []string {
	out := make([]string, len(frozenFactTypes))
	copy(out, frozenFactTypes)
	return out
}

func IsFrozenFactType(factType string) bool {
	for _, item := range frozenFactTypes {
		if item == strings.TrimSpace(factType) {
			return true
		}
	}
	return false
}
```

Update `OneOps/app/netpath/snapshot/provider/facts.go` to reuse these constants instead of duplicating the three shared fact-type strings:

```go
import fact "github.com/netxops/OneOps/app/device_collection2/fact"

const (
	FactTypeDeviceIdentity   = "device_identity"
	FactTypeInterface        = "interface"
	FactTypeInterfaceIP      = fact.FactTypeInterfaceIP
	FactTypeTopologyNeighbor = fact.FactTypeTopologyNeighbor
	FactTypeRouteTable       = fact.FactTypeRouteTable
```

- [ ] **Step 4: Run tests to verify it passes**

Run: `go test ./app/device_collection2/fact ./app/netpath/snapshot/provider -run 'TestFrozenFactTypesPhaseOne|TestNormalizeRouteDestinationValue' -count=1`

Expected: PASS for the new registry test and no compilation errors in NetPath provider.

- [ ] **Step 5: Commit**

```bash
git -C OneOps add \
  app/device_collection2/fact/frozen_registry.go \
  app/device_collection2/fact/frozen_registry_test.go \
  app/netpath/snapshot/provider/facts.go
git -C OneOps commit -m "feat: add frozen dc2 fact registry"
```

## Task 2: Harden `route_table` Processor To Match The Frozen Contract

**Files:**
- Modify: `OneOps/app/device_collection2/fact/route_policy_processor.go`
- Modify: `OneOps/app/device_collection2/fact/route_policy_processor_test.go`
- Modify: `OneOps/app/device_collection2/service/impl/device_collection2_test.go`

- [ ] **Step 1: Add failing direct-route and provenance tests**

Append focused tests to `OneOps/app/device_collection2/fact/route_policy_processor_test.go`:

```go
func TestRouteTableProcessorAcceptsDirectRouteWithoutNextHop(t *testing.T) {
	registry := NewDefaultRegistry()
	rows := []StandardRow{{
		ContractKey: "common_mib",
		DatasetKey:  "snmp_ipRouteTable",
		TargetID:    "r1",
		Fields: map[string]interface{}{
			"destination":   "10.0.10.0",
			"netmask":       "255.255.255.0",
			"if_index":      "9",
			"out_interface": "Vlan10",
			"route_type":    "3",
			"protocol":      "direct",
			"metric":        "0",
			"preference":    "0",
		},
		ObservedAt: time.Unix(100, 0),
	}}

	facts, issues, err := registry.Process(context.Background(), "snmp_ipRouteTable", rows)
	if err != nil {
		t.Fatalf("process direct route facts failed: %v", err)
	}
	if len(issues) != 0 || len(facts) != 1 {
		t.Fatalf("unexpected direct route result: facts=%#v issues=%#v", facts, issues)
	}
	if got := facts[0].IdentityKey; got != "r1:route:default:10.0.10.0/24:direct:9" {
		t.Fatalf("unexpected direct route identity: %s", got)
	}
	if got := facts[0].Provenance.ProcessorVersion; got != "v2" {
		t.Fatalf("expected processor version bump, got %#v", facts[0].Provenance)
	}
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `go test ./app/device_collection2/fact -run 'TestRouteTableProcessor(AcceptsDirectRouteWithoutNextHop|NormalizesSNMPIPRouteRows)' -count=1`

Expected: FAIL because the current identity builder expects next-hop semantics that do not distinguish direct routes cleanly and current provenance still reports `v1`.

- [ ] **Step 3: Patch `route_table` normalization and versioning**

Update `OneOps/app/device_collection2/fact/route_policy_processor.go`:

```go
func (p *RouteTableProcessor) ProcessorKey() string     { return "processor.route_table.v2" }
func (p *RouteTableProcessor) ProcessorVersion() string { return "v2" }

// After route_type / protocol / null_route normalization:
if fields["null_route"] == nil {
	fields["null_route"] = false
}

// Require destination plus one forwarding anchor:
// - next_hop_ip for transit routes
// - out_interface or if_index for direct / connected / null routes
identity := routeTableIdentity(row.TargetID, fields)
if identity == "" {
	issues = append(issues, issue(row, p, "missing_required_field", "route_table fact requires destination plus next hop or direct forwarding anchor", nil))
	continue
}
```

Adjust the identity helper so direct or connected routes can emit `direct` when `next_hop_ip` is absent but interface context exists:

```go
func routeTableIdentity(targetID string, fields map[string]interface{}) string {
	dest := identityValue(fields["destination"])
	if dest == "" {
		return ""
	}

	vrf := identityValue(fields["vrf"])
	if vrf == "" {
		vrf = "default"
	}

	nh := identityValue(fields["next_hop_ip"])
	if nh == "" {
		routeType := strings.ToLower(identityValue(fields["route_type"]))
		protocol := strings.ToLower(identityValue(fields["protocol"]))
		nullRoute := strings.EqualFold(identityValue(fields["null_route"]), "true")
		if nullRoute || routeType == "direct" || routeType == "connected" || protocol == "direct" || protocol == "connected" {
			nh = "direct"
		}
	}

	out := ""
	if value := identityValue(fields["if_index"]); value != "" {
		out = value
	} else if value := identityValue(fields["out_interface"]); value != "" {
		out = value
	}

	if nh == "" && out == "" {
		return ""
	}
	if nh == "" {
		nh = "none"
	}
	if out == "" {
		out = "none"
	}

	return fmt.Sprintf("%s:route:%s:%s:%s:%s", strings.TrimSpace(targetID), vrf, dest, nh, out)
}
```

Also add an explicit import in `route_policy_processor.go` if needed:

```go
import (
	"context"
	"fmt"
	"net"
	"strings"
)
```

This replaces the old implicit “next hop or interface” assumption with a deterministic identity that still works for direct/null routes.

- [ ] **Step 4: Run tests to verify it passes**

Run: `go test ./app/device_collection2/fact ./app/device_collection2/service/impl -run 'TestRouteTableProcessor|TestProcessFactsNormalizesWindowsDefaultRouteRows' -count=1`

Expected: PASS and existing service-level route tests still normalize legacy route inputs.

- [ ] **Step 5: Commit**

```bash
git -C OneOps add \
  app/device_collection2/fact/route_policy_processor.go \
  app/device_collection2/fact/route_policy_processor_test.go \
  app/device_collection2/service/impl/device_collection2_test.go
git -C OneOps commit -m "fix: harden route table frozen contract"
```

## Task 3: Harden `interface_ip`, `arp_entry`, And `mac_table_entry` Join-Anchor Rules

**Files:**
- Modify: `OneOps/app/device_collection2/fact/interface_ip_processor.go`
- Modify: `OneOps/app/device_collection2/fact/topology_processor.go`
- Modify: `OneOps/app/device_collection2/service/impl/device_collection2_test.go`
- Modify: `OneOps/app/ipam/service/impl/ip_address_fact_test.go`

- [ ] **Step 1: Add failing processor contract tests**

Add focused service-level tests in `OneOps/app/device_collection2/service/impl/device_collection2_test.go`:

```go
func TestProcessFactsRejectsInterfaceIPWithoutJoinAnchor(t *testing.T) {
	srv := NewDeviceCollection2Srv(nil, nil, nil, nil)
	resp, err := srv.ProcessFacts(context.Background(), dto.ProcessFactsReq{
		Contract:   testFactContract("interface_ip"),
		DatasetKey: "interface_ip",
		TargetID:   "SW-001",
		Rows: []map[string]interface{}{
			{"ip": "10.0.0.1", "prefix_len": "24"},
		},
	})
	if err != nil {
		t.Fatalf("process interface_ip facts failed: %v", err)
	}
	if len(resp.Facts) != 0 {
		t.Fatalf("expected missing join anchor to reject fact, got %#v", resp.Facts)
	}
	if len(resp.Issues) != 1 || resp.Issues[0].IssueCode != "missing_interface_identity" {
		t.Fatalf("unexpected issues: %#v", resp.Issues)
	}
}

func TestProcessFactsLowersARPConfidenceWithoutInterfaceAnchor(t *testing.T) {
	srv := NewDeviceCollection2Srv(nil, nil, nil, nil)
	resp, err := srv.ProcessFacts(context.Background(), dto.ProcessFactsReq{
		Contract:   testFactContract("arp_table"),
		DatasetKey: "arp_table",
		TargetID:   "SW-001",
		Rows: []map[string]interface{}{
			{"ip": "10.1.2.10", "mac": "001122AABBCC"},
		},
	})
	if err != nil {
		t.Fatalf("process arp facts failed: %v", err)
	}
	if len(resp.Facts) != 1 {
		t.Fatalf("expected degraded arp fact, got %#v", resp)
	}
	if resp.Facts[0].Quality.Confidence >= 0.9 {
		t.Fatalf("expected degraded confidence, got %#v", resp.Facts[0].Quality)
	}
	if len(resp.Facts[0].Quality.Issues) == 0 {
		t.Fatalf("expected quality issues for missing interface anchor, got %#v", resp.Facts[0].Quality)
	}
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `go test ./app/device_collection2/service/impl -run 'TestProcessFacts(RejectsInterfaceIPWithoutJoinAnchor|LowersARPConfidenceWithoutInterfaceAnchor)' -count=1`

Expected: FAIL because the current processors either reject with a generic code or keep confidence fixed at `0.9`.

- [ ] **Step 3: Patch join-anchor semantics and processor versions**

Update `OneOps/app/device_collection2/fact/interface_ip_processor.go`:

```go
func (p *InterfaceIPProcessor) ProcessorKey() string     { return "processor.interface_ip.v2" }
func (p *InterfaceIPProcessor) ProcessorVersion() string { return "v2" }

if identity == "" {
	issues = append(issues, issue(row, p, "missing_interface_identity", "interface_ip fact requires interface identity", nil))
	continue
}
```

Update `OneOps/app/device_collection2/fact/topology_processor.go` for ARP and MAC:

```go
func (p *MACTableProcessor) ProcessorKey() string     { return "processor.mac_table.v2" }
func (p *MACTableProcessor) ProcessorVersion() string { return "v2" }

quality := FactQuality{Valid: true, Confidence: 0.9, Issues: []string{}}
if localInterfaceIdentityPart(fields) == "" && identityValue(fields["bridge_port"]) == "" {
	quality.Confidence = 0.6
	quality.Issues = append(quality.Issues, "missing_interface_identity")
}
```

```go
func (p *ARPProcessor) ProcessorKey() string     { return "processor.arp.v2" }
func (p *ARPProcessor) ProcessorVersion() string { return "v2" }

quality := FactQuality{Valid: true, Confidence: 0.9, Issues: []string{}}
if localInterfaceIdentityPart(fields) == "" {
	quality.Confidence = 0.6
	quality.Issues = append(quality.Issues, "missing_interface_identity")
}
```

Also update IPAM provenance assertions in `OneOps/app/ipam/service/impl/ip_address_fact_test.go` from `processor.interface_ip.v1` to `processor.interface_ip.v2` where the test models the new frozen contract shape.

- [ ] **Step 4: Run tests to verify it passes**

Run: `go test ./app/device_collection2/service/impl ./app/ipam/service/impl -run 'TestProcessFacts|TestProjectCanonical|TestProjectDC2FactRecordPreservesLatestFactProvenance' -count=1`

Expected: PASS with updated processor keys/versions and lowered-confidence degraded facts where anchors are missing.

- [ ] **Step 5: Commit**

```bash
git -C OneOps add \
  app/device_collection2/fact/interface_ip_processor.go \
  app/device_collection2/fact/topology_processor.go \
  app/device_collection2/service/impl/device_collection2_test.go \
  app/ipam/service/impl/ip_address_fact_test.go
git -C OneOps commit -m "fix: align dc2 join-anchor contract semantics"
```

## Task 4: Align NetPath And IPAM Consumer Behavior With The Frozen Registry

**Files:**
- Modify: `OneOps/app/netpath/snapshot/builder_test.go`
- Modify: `OneOps/app/ipam/api/ip_address_fact.go`
- Modify: `OneOps/app/ipam/api/ip_address_fact_test.go`

- [ ] **Step 1: Add failing consumer-behavior tests**

Add a focused IPAM API test in `OneOps/app/ipam/api/ip_address_fact_test.go`:

```go
func TestCanonicalLatestProjectionFactTypesDefaultsStayNarrow(t *testing.T) {
	got := canonicalLatestProjectionFactTypes("")
	want := []string{"interface_ip", "arp_entry"}
	if len(got) != len(want) {
		t.Fatalf("unexpected default fact types: got=%v want=%v", got, want)
	}
	for i := range want {
		if got[i] != want[i] {
			t.Fatalf("unexpected default fact types: got=%v want=%v", got, want)
		}
	}
}

func TestCanonicalLatestProjectionFactTypesAcceptsExplicitFrozenMACFact(t *testing.T) {
	got := canonicalLatestProjectionFactTypes(" mac_table_entry ")
	if len(got) != 1 || got[0] != "mac_table_entry" {
		t.Fatalf("expected explicit frozen MAC fact type, got %#v", got)
	}
}
```

Add a NetPath builder regression test in `OneOps/app/netpath/snapshot/builder_test.go`:

```go
func TestBuildDC2SnapshotTreatsARPAndMACAsSupportingEvidenceOnly(t *testing.T) {
	reader := &fakeLatestFactReader{
		facts: map[string][]dc2dto.FactRecordResp{
			"arp_entry": {{TargetID: "r1", FactType: "arp_entry", IdentityKey: "r1:ip:10.0.0.1:mac:00:11:22:aa:bb:cc", Valid: true}},
			"mac_table_entry": {{TargetID: "r1", FactType: "mac_table_entry", IdentityKey: "r1:mac:00:11:22:aa:bb:cc", Valid: true}},
		},
	}
	builder := NewDC2LatestSnapshotBuilder(reader)
	snap, err := builder.Build(context.Background(), BuildRequest{DeviceCodes: []string{"r1"}})
	if err != nil {
		t.Fatalf("build snapshot failed: %v", err)
	}
	if !hasDiagnostic(snap, "route_table_missing") {
		t.Fatalf("expected route_table_missing when readiness anchors are absent, got %#v", snap.Diagnostics)
	}
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `go test ./app/ipam/api ./app/netpath/snapshot -run 'TestCanonicalLatestProjectionFactTypes|TestBuildDC2SnapshotTreatsARPAndMACAsSupportingEvidenceOnly' -count=1`

Expected: FAIL because the NetPath builder test is new and current API tests do not yet document the explicit frozen MAC behavior.

- [ ] **Step 3: Patch consumer alignment without widening defaults**

Keep IPAM default projection narrow for now, but document and test explicit frozen fact selection:

```go
import fact "github.com/netxops/OneOps/app/device_collection2/fact"

func canonicalLatestProjectionFactTypes(factType string) []string {
	factType = strings.TrimSpace(factType)
	if factType != "" {
		return []string{factType}
	}
	// Keep defaults narrow until mac_table_entry projection produces first-class IPAM value
	// instead of mostly skipped records.
	return []string{fact.FactTypeInterfaceIP, fact.FactTypeARPEntry}
}
```

In NetPath tests, explicitly assert that `arp_entry` and `mac_table_entry` do not satisfy readiness anchors by themselves. No production NetPath code change is required unless the new test reveals an unexpected upgrade path.

- [ ] **Step 4: Run tests to verify it passes**

Run: `go test ./app/ipam/api ./app/netpath/snapshot -run 'TestCanonicalLatestProjectionFactTypes|TestBuildDC2SnapshotTreatsARPAndMACAsSupportingEvidenceOnly' -count=1`

Expected: PASS and current default projection behavior remains intentionally narrow.

- [ ] **Step 5: Commit**

```bash
git -C OneOps add \
  app/ipam/api/ip_address_fact.go \
  app/ipam/api/ip_address_fact_test.go \
  app/netpath/snapshot/builder_test.go
git -C OneOps commit -m "test: document frozen fact consumer boundaries"
```

## Task 5: Update Spec With Implementation Clarifications And Run Focused Verification

**Files:**
- Modify: `docs/superpowers/specs/2026-06-22-oneops-dc2-minimal-contract-dataset-design.md`

- [ ] **Step 1: Add a short implementation note to the spec**

Append a note under `Application Consumption Mapping`:

```md
Implementation note:

- `mac_table_entry` is frozen as a shared fact family, but the IPAM `ProjectCanonicalLatest` API keeps its default fact list narrow in phase one.
- Operators may still request `mac_table_entry` explicitly for validation or future projection work.
- This keeps the shared contract ahead of the default projection workflow without pretending that MAC-only records already produce first-class IPAM address facts.
```

- [ ] **Step 2: Run doc self-check**

Run: `rg -n "TODO|TBD|implement later|fill in details" docs/superpowers/specs/2026-06-22-oneops-dc2-minimal-contract-dataset-design.md`

Expected: no output

- [ ] **Step 3: Run the final focused Go verification**

Run: `go test ./app/device_collection2/fact ./app/device_collection2/service/impl ./app/netpath/snapshot ./app/netpath/snapshot/provider ./app/ipam/api ./app/ipam/service/impl -count=1`

Expected: PASS

- [ ] **Step 4: Capture nested-repo doc commit**

```bash
git -C docs add \
  superpowers/specs/2026-06-22-oneops-dc2-minimal-contract-dataset-design.md \
  superpowers/plans/2026-06-22-oneops-dc2-minimal-contract-dataset-implementation.md
git -C docs commit -m "docs: plan dc2 minimal contract implementation"
```

- [ ] **Step 5: Record implementation branch status**

```bash
git -C OneOps status --short
git -C docs status --short
```

Expected:
- `OneOps` shows a clean tree after the code commits above
- `docs` shows a clean tree after the doc commit above

## Self-Review

### Spec coverage

- Frozen shared registry: covered by Task 1.
- `route_table` direct-route and provenance/version semantics: covered by Task 2.
- `interface_ip`, `arp_entry`, and `mac_table_entry` join-anchor and confidence semantics: covered by Task 3.
- NetPath versus IPAM consumer boundaries: covered by Task 4.
- Spec clarification and final verification: covered by Task 5.

No spec sections are intentionally left without an implementation task.

### Placeholder scan

- No `TODO`, `TBD`, or “similar to task N” placeholders remain.
- Every code-changing step names exact files, code direction, and test commands.

### Type consistency

- Shared fact type constants are introduced once in `device_collection2/fact/frozen_registry.go`.
- Processor version bumps are explicitly paired with provenance expectation updates in IPAM tests.
- Consumer tests distinguish shared frozen availability from default API behavior, so the plan does not accidentally require IPAM to treat all frozen facts as default projection inputs.
