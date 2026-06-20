# OneOPS NetPath Route Table Phase3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add DC2 route table collection normalization so OneOPS can build engine-ready route tables from real network-device facts.

**Architecture:** Implement a DC2 `route_table` processor that converts standardized CLI rows into canonical route facts. Register it in the existing fact processor registry, add tests through `ProcessFacts`, then verify SnapshotProvider consumes the same field shape. Keep `oneops-netpath` out of default OneOPS dependencies.

**Tech Stack:** Go, OneOPS `app/device_collection2/fact`, DC2 `ProcessFacts`, built-in network CLI contracts, OneOPS `app/netpath/snapshot/provider`, table-driven tests.

---

## Scope

This phase follows `docs/superpowers/specs/2026-06-19-oneops-fact-application-foundation-design.md`.

Layer placement:

```text
Collection layer: network CLI route command output
Canonical fact layer: DC2 route_table facts
Snapshot/projection layer: NetPath AnalysisSnapshot
Application layer: future NetPath analysis runs, evidence, UI, probes, tickets
```

Rules:

- `route_table` belongs to the shared canonical fact layer, not a NetPath-only model.
- SnapshotProvider may consume `route_table`, but it must preserve source fact references and quality diagnostics.
- A temporary import endpoint is out of scope unless the user explicitly approves it.
- Tenant scoping remains a known open decision; this phase does not solve global tenant latest-fact semantics.

In scope:

- Add canonical route table fact schema.
- Add route table fact processor.
- Register processor in DC2 default registry.
- Add tests for route normalization and invalid rows.
- Add one minimal built-in network CLI dataset contract for route table rows.
- Add SnapshotProvider integration test that uses DC2-produced `route_table` fact shape.
- Keep provenance visible through existing DC2 `FactProvenance`, `RunID`, and latest fact shape.

Out of scope:

- Live SSH/SNMP collection against real devices.
- Data migrations or backfills.
- Default build dependency on `oneops-netpath`.
- Temporary route import APIs.
- Generic snapshot publication table changes.
- Firewall ACL, NAT, PBR, or security policy evaluation.
- UI or probe work.

## Consent Gates For This Phase

Proceed without asking for:

- New processor files under `app/device_collection2/fact`.
- Registry updates.
- Unit tests and contract bootstrap tests.
- Minimal built-in route dataset for one MVP network CLI shape.

Stop and ask before:

- Adding more than one vendor-specific route parser family.
- Adding migrations or backfills.
- Touching production wiring outside DC2 bootstrap and SnapshotProvider tests.
- Adding new third-party dependencies.
- Running commands against live network devices.
- Adding temporary import endpoints.
- Changing tenant scoping behavior for DC2 latest fact queries.

## Route Table Canonical Fact Schema

Fact type:

```text
route_table
```

Canonical fields:

```text
vrf              string, default "default"
destination      string, IP prefix such as "10.0.2.0/24" or "0.0.0.0/0"
next_hop_ip      string, normalized IP, optional for connected/null routes
out_interface    string, canonical interface name when possible
protocol         string, lower-case route protocol such as static, connected, ospf, bgp
metric           int, optional
preference       int, optional
null_route       bool, true for discard/null routes
raw              string, optional raw route line or raw reference text
```

Identity key format:

```text
<target_id>:route:<vrf>:<destination>:<next_hop_or_direct>:<out_interface_or_null>
```

Examples:

```text
r1:route:default:10.0.2.0/24:192.0.2.2:gigabitethernet0/1
r1:route:default:10.0.3.0/24:direct:gigabitethernet0/2
r1:route:default:203.0.113.0/24:null:null0
```

## File Structure

Create:

```text
OneOPS/app/device_collection2/fact/route_table_processor.go
```

Modify:

```text
OneOPS/app/device_collection2/fact/registry.go
OneOPS/app/device_collection2/service/impl/device_collection2_test.go
OneOPS/app/device_collection2/service/impl/device_collection2_network_contract_bootstrap.go
OneOPS/app/netpath/snapshot/provider/assembler_test.go
```

Responsibilities:

- `route_table_processor.go`: normalize route rows into `route_table` canonical facts.
- `registry.go`: include `NewRouteTableProcessor()` in `NewDefaultRegistry()`.
- `device_collection2_test.go`: prove `ProcessFacts` emits route facts and issues.
- `device_collection2_network_contract_bootstrap.go`: add one route table dataset to the MVP network CLI contract.
- `assembler_test.go`: prove SnapshotProvider consumes DC2 route fact shape.

## Task 1: Route Table Processor Tests

**Files:**

- Modify: `OneOPS/app/device_collection2/service/impl/device_collection2_test.go`

- [ ] **Step 1: Add a happy-path route table test**

Append this test near the existing `TestProcessFactsNormalizesWindowsDefaultRouteRows` and topology tests:

```go
func TestProcessFactsNormalizesNetworkRouteTableRows(t *testing.T) {
	srv := NewDeviceCollection2Srv(nil, nil, nil, nil)
	resp, err := srv.ProcessFacts(context.Background(), dto.ProcessFactsReq{
		Contract:   testFactContract("route_table"),
		DatasetKey: "route_table",
		TargetID:   "R1",
		Rows: []map[string]interface{}{
			{
				"vrf":           " default ",
				"destination":   "10.0.2.0/24",
				"next_hop_ip":   "C0000202",
				"out_interface": "GigabitEthernet0/1",
				"protocol":      "Static",
				"metric":        "10",
				"preference":    "60",
				"raw":           "S 10.0.2.0/24 [60/10] via 192.0.2.2, GigabitEthernet0/1",
			},
			{
				"destination":   "10.0.3.0/24",
				"out_interface": "GigabitEthernet0/2",
				"protocol":      "Connected",
			},
			{
				"destination":   "203.0.113.0/24",
				"out_interface": "NULL0",
				"protocol":      "Static",
				"null_route":    "true",
			},
		},
	})
	if err != nil {
		t.Fatalf("process route table facts failed: %v", err)
	}
	if len(resp.Issues) != 0 || len(resp.Facts) != 3 {
		t.Fatalf("unexpected route table result: facts=%#v issues=%#v", resp.Facts, resp.Issues)
	}
	first := resp.Facts[0]
	if first.FactType != "route_table" || first.TargetID != "R1" {
		t.Fatalf("unexpected route fact identity: %#v", first)
	}
	if first.Fields["vrf"] != "default" || first.Fields["destination"] != "10.0.2.0/24" {
		t.Fatalf("route destination fields were not normalized: %#v", first.Fields)
	}
	if first.Fields["next_hop_ip"] != "192.0.2.2" || first.Fields["out_interface"] != "gigabitethernet0/1" {
		t.Fatalf("route next hop or interface was not normalized: %#v", first.Fields)
	}
	if first.Fields["protocol"] != "static" || first.Fields["metric"] != 10 || first.Fields["preference"] != 60 {
		t.Fatalf("route protocol or metrics were not normalized: %#v", first.Fields)
	}
	if resp.Facts[1].Fields["protocol"] != "connected" || resp.Facts[1].Fields["vrf"] != "default" {
		t.Fatalf("connected route was not normalized: %#v", resp.Facts[1].Fields)
	}
	if resp.Facts[2].Fields["null_route"] != true || resp.Facts[2].Fields["out_interface"] != "null0" {
		t.Fatalf("null route was not normalized: %#v", resp.Facts[2].Fields)
	}
}
```

- [ ] **Step 2: Add invalid route tests**

Append this test:

```go
func TestProcessFactsRouteTableReportsInvalidRows(t *testing.T) {
	srv := NewDeviceCollection2Srv(nil, nil, nil, nil)
	resp, err := srv.ProcessFacts(context.Background(), dto.ProcessFactsReq{
		Contract:   testFactContract("route_table"),
		DatasetKey: "route_table",
		TargetID:   "R1",
		Rows: []map[string]interface{}{
			{
				"destination": "not-a-prefix",
				"next_hop_ip": "192.0.2.2",
			},
			{
				"destination": "10.0.2.0/24",
				"next_hop_ip": "not-an-ip",
			},
			{
				"next_hop_ip": "192.0.2.2",
			},
		},
	})
	if err != nil {
		t.Fatalf("process invalid route rows failed: %v", err)
	}
	if len(resp.Facts) != 0 || len(resp.Issues) != 3 {
		t.Fatalf("expected invalid route rows to produce issues only, facts=%#v issues=%#v", resp.Facts, resp.Issues)
	}
	assertIssueCode(t, resp.Issues, "invalid_prefix")
	assertIssueCode(t, resp.Issues, "invalid_ip")
	assertIssueCode(t, resp.Issues, "missing_required_field")
}

func assertIssueCode(t *testing.T, issues []fact.FactIssue, code string) {
	t.Helper()
	for _, issue := range issues {
		if issue.IssueCode == code {
			return
		}
	}
	t.Fatalf("expected issue code %s in %#v", code, issues)
}
```

If `assertIssueCode` conflicts with an existing helper, reuse the existing helper and keep one implementation.

- [ ] **Step 3: Run the red test**

Run:

```bash
go test -count=1 ./app/device_collection2/service/impl -run 'TestProcessFacts(NormalizesNetworkRouteTableRows|RouteTableReportsInvalidRows)' -v
```

Expected:

```text
processor_not_found
```

or failing assertions showing no `route_table` processor exists.

## Task 2: Route Table Processor Implementation

**Files:**

- Create: `OneOPS/app/device_collection2/fact/route_table_processor.go`
- Modify: `OneOPS/app/device_collection2/fact/registry.go`

- [ ] **Step 1: Create route table processor**

Create `OneOPS/app/device_collection2/fact/route_table_processor.go`:

```go
package fact

import (
	"context"
	"fmt"
	"net/netip"
	"strings"
)

type RouteTableProcessor struct{}

func NewRouteTableProcessor() *RouteTableProcessor { return &RouteTableProcessor{} }

func (p *RouteTableProcessor) ProcessorKey() string     { return "processor.route_table.v1" }
func (p *RouteTableProcessor) ProcessorVersion() string { return "v1" }

func (p *RouteTableProcessor) Accepts(datasetKey string) bool {
	return datasetKeyIn(datasetKey, "route_table", "cli_route_table", "h3c_route_table", "huawei_route_table")
}

func (p *RouteTableProcessor) Process(ctx context.Context, rows []StandardRow) ([]CanonicalFact, []FactIssue, error) {
	_ = ctx
	facts := make([]CanonicalFact, 0, len(rows))
	issues := make([]FactIssue, 0)
	for _, row := range rows {
		fields := map[string]interface{}{}
		sourceFields := make([]string, 0)

		vrf, vrfSource := FirstText(row.Fields, "vrf", "vpn_instance")
		if strings.TrimSpace(vrf) == "" {
			vrf = "default"
		}
		fields["vrf"] = strings.TrimSpace(vrf)
		if vrfSource != "" {
			sourceFields = append(sourceFields, vrfSource)
		}

		destination, destinationSource := FirstText(row.Fields, "destination", "prefix", "network")
		destination = strings.TrimSpace(destination)
		if destination == "" {
			issues = append(issues, issue(row, p, "missing_required_field", "route_table fact requires destination", nil))
			continue
		}
		if _, err := netip.ParsePrefix(destination); err != nil {
			issues = append(issues, issue(row, p, "invalid_prefix", "route destination cannot be normalized", map[string]interface{}{"value": destination}))
			continue
		}
		fields["destination"] = destination
		sourceFields = append(sourceFields, destinationSource)

		if rawNextHop, source := FirstText(row.Fields, "next_hop_ip", "next_hop", "gateway"); rawNextHop != "" {
			sourceFields = append(sourceFields, source)
			if nextHop, ok := NormalizeIP(rawNextHop); ok {
				fields["next_hop_ip"] = nextHop
			} else {
				issues = append(issues, issue(row, p, "invalid_ip", "route next hop cannot be normalized", map[string]interface{}{"value": rawNextHop}))
				continue
			}
		}

		if rawInterface, source := FirstText(row.Fields, "out_interface", "interface", "if_name"); rawInterface != "" {
			sourceFields = append(sourceFields, source)
			if canonical, ok := NormalizeInterfaceName(rawInterface); ok {
				fields["out_interface"] = canonical
			} else {
				fields["out_interface"] = strings.ToLower(strings.TrimSpace(rawInterface))
			}
		}

		if protocol, source := FirstText(row.Fields, "protocol", "route_protocol"); protocol != "" {
			fields["protocol"] = strings.ToLower(strings.TrimSpace(protocol))
			sourceFields = append(sourceFields, source)
		}
		copyRouteIntField(fields, row.Fields, &sourceFields, "metric", "metric", "cost")
		copyRouteIntField(fields, row.Fields, &sourceFields, "preference", "preference", "distance", "admin_distance")
		if nullRoute, source, ok := routeBoolField(row.Fields, "null_route", "discard", "blackhole"); ok {
			fields["null_route"] = nullRoute
			sourceFields = append(sourceFields, source)
		} else if outInterface := strings.ToLower(StringValue(fields["out_interface"])); outInterface == "null0" || outInterface == "null" || outInterface == "discard" {
			fields["null_route"] = true
		}
		copyTextField(fields, row.Fields, &sourceFields, "raw", "raw", "raw_line")

		identity := routeTableIdentity(row.TargetID, fields)
		if identity == "" {
			issues = append(issues, issue(row, p, "missing_required_field", "route_table fact requires target_id and destination", nil))
			continue
		}
		facts = append(facts, CanonicalFact{
			FactType:    "route_table",
			TargetID:    row.TargetID,
			IdentityKey: identity,
			Fields:      fields,
			Quality:     FactQuality{Valid: true, Confidence: 0.86, Issues: []string{}},
			Provenance:  baseProvenance(row, p, uniqueStrings(sourceFields)),
			ObservedAt:  row.ObservedAt,
		})
	}
	return facts, issues, nil
}

func routeTableIdentity(targetID string, fields map[string]interface{}) string {
	targetID = strings.TrimSpace(targetID)
	destination := strings.TrimSpace(StringValue(fields["destination"]))
	if targetID == "" || destination == "" {
		return ""
	}
	vrf := strings.TrimSpace(StringValue(fields["vrf"]))
	if vrf == "" {
		vrf = "default"
	}
	nextHop := strings.TrimSpace(StringValue(fields["next_hop_ip"]))
	if nextHop == "" {
		if StringValue(fields["null_route"]) == "true" {
			nextHop = "null"
		} else {
			nextHop = "direct"
		}
	}
	outInterface := strings.TrimSpace(StringValue(fields["out_interface"]))
	if outInterface == "" {
		outInterface = "none"
	}
	return fmt.Sprintf("%s:route:%s:%s:%s:%s", targetID, strings.ToLower(vrf), destination, strings.ToLower(nextHop), strings.ToLower(outInterface))
}

func copyRouteIntField(out map[string]interface{}, in map[string]interface{}, sourceFields *[]string, outKey string, sourceKeys ...string) {
	for _, key := range sourceKeys {
		value, ok := in[key]
		if !ok {
			continue
		}
		parsed, ok := ToInt(value)
		if !ok {
			continue
		}
		out[outKey] = parsed
		*sourceFields = append(*sourceFields, key)
		return
	}
}

func routeBoolField(fields map[string]interface{}, keys ...string) (bool, string, bool) {
	for _, key := range keys {
		value, ok := fields[key]
		if !ok {
			continue
		}
		switch typed := value.(type) {
		case bool:
			return typed, key, true
		case string:
			text := strings.TrimSpace(strings.ToLower(typed))
			switch text {
			case "true", "yes", "y", "1", "null0", "null", "discard", "blackhole":
				return true, key, true
			case "false", "no", "n", "0":
				return false, key, true
			}
		default:
			text := strings.TrimSpace(strings.ToLower(fmt.Sprint(typed)))
			if text == "1" {
				return true, key, true
			}
			if text == "0" {
				return false, key, true
			}
		}
	}
	return false, "", false
}
```

- [ ] **Step 2: Register processor**

Modify `OneOPS/app/device_collection2/fact/registry.go` in `NewDefaultRegistry()`:

```go
func NewDefaultRegistry() *Registry {
	return NewRegistry(
		NewDeviceIdentityProcessor(),
		NewInterfaceProcessor(),
		NewInterfaceIPProcessor(),
		NewRouteTableProcessor(),
		NewServerCPUProcessor(),
		NewServerRouteProcessor(),
		NewPhysicalEntityProcessor(),
		NewNeighborProcessor(),
		NewMACTableProcessor(),
		NewARPProcessor(),
	)
}
```

- [ ] **Step 3: Run route processor tests**

Run:

```bash
go test -count=1 ./app/device_collection2/service/impl -run 'TestProcessFacts(NormalizesNetworkRouteTableRows|RouteTableReportsInvalidRows)' -v
```

Expected:

```text
PASS
```

- [ ] **Step 4: Commit**

Run:

```bash
git add app/device_collection2/fact/route_table_processor.go app/device_collection2/fact/registry.go app/device_collection2/service/impl/device_collection2_test.go
git commit -m "feat: normalize network route table facts"
```

## Task 3: Built-In Route Dataset Contract

**Files:**

- Modify: `OneOPS/app/device_collection2/service/impl/device_collection2_network_contract_bootstrap.go`
- Modify: `OneOPS/app/device_collection2/service/impl/device_collection2_test.go`

- [ ] **Step 1: Add contract test**

Add a test near existing built-in network contract tests:

```go
func TestBuiltinNetworkCLIContractsIncludeRouteTableDataset(t *testing.T) {
	contracts := builtinNetworkCLIContracts()
	found := false
	for _, contract := range contracts {
		if contract.Key != "h3c_comware" && contract.Key != "h3c_secpath" {
			continue
		}
		for _, dataset := range contract.Datasets {
			if dataset.Key == "route_table" {
				found = true
				if len(dataset.Raw.Commands) == 0 {
					t.Fatalf("route_table dataset must define commands: %#v", dataset)
				}
				if len(dataset.Fields) == 0 {
					t.Fatalf("route_table dataset must define fields: %#v", dataset)
				}
			}
		}
	}
	if !found {
		t.Fatal("expected h3c network CLI contracts to include route_table dataset")
	}
}
```

- [ ] **Step 2: Run red contract test**

Run:

```bash
go test -count=1 ./app/device_collection2/service/impl -run TestBuiltinNetworkCLIContractsIncludeRouteTableDataset -v
```

Expected:

```text
FAIL: expected h3c network CLI contracts to include route_table dataset
```

- [ ] **Step 3: Add H3C route table dataset**

In `device_collection2_network_contract_bootstrap.go`, add `h3CComwareRouteTableDataset()` and include it in `h3c_comware` and `h3c_secpath` datasets:

```go
func h3CComwareRouteTableDataset() definition.Dataset {
	return definition.Dataset{
		Key:      "route_table",
		Protocol: "cli",
		Raw: definition.Raw{
			Commands:   []string{"display ip routing-table"},
			TimeoutSec: 30,
		},
		Standardizer: definition.Standardizer{
			Type:       "textfsm",
			SourcePath: "stdout",
			TextFSMTemplate: "Value PROTOCOL (\\S+)\\n" +
				"Value DESTINATION (\\d+\\.\\d+\\.\\d+\\.\\d+/\\d+)\\n" +
				"Value PREFERENCE (\\d+)\\n" +
				"Value METRIC (\\d+)\\n" +
				"Value NEXT_HOP (\\d+\\.\\d+\\.\\d+\\.\\d+|0\\.0\\.0\\.0)\\n" +
				"Value INTERFACE (\\S+)\\n\\n" +
				"Start\\n" +
				"  ^${PROTOCOL}\\s+${DESTINATION}\\s+\\S+\\s+${PREFERENCE}\\s+${METRIC}\\s+${NEXT_HOP}\\s+${INTERFACE} -> Record\\n",
		},
		Fields: []definition.Field{
			{Key: "protocol", SourceKey: "PROTOCOL"},
			{Key: "destination", SourceKey: "DESTINATION", Required: true},
			{Key: "preference", SourceKey: "PREFERENCE"},
			{Key: "metric", SourceKey: "METRIC"},
			{Key: "next_hop_ip", SourceKey: "NEXT_HOP"},
			{Key: "out_interface", SourceKey: "INTERFACE"},
		},
	}
}
```

Add to H3C contract datasets:

```go
h3CComwareRouteTableDataset(),
```

- [ ] **Step 4: Run contract tests**

Run:

```bash
go test -count=1 ./app/device_collection2/service/impl -run TestBuiltinNetworkCLIContractsIncludeRouteTableDataset -v
```

Expected:

```text
PASS
```

- [ ] **Step 5: Commit**

Run:

```bash
git add app/device_collection2/service/impl/device_collection2_network_contract_bootstrap.go app/device_collection2/service/impl/device_collection2_test.go
git commit -m "feat: add network route table collection contract"
```

## Task 4: SnapshotProvider Route Fact Integration Test

**Files:**

- Modify: `OneOPS/app/netpath/snapshot/provider/assembler_test.go`

- [ ] **Step 1: Add DC2-shaped route fact test**

Append this test:

```go
func TestAssemblerConsumesRouteTableFactsFromDC2Shape(t *testing.T) {
	assembler := NewAssembler()
	snap, err := assembler.Assemble(context.Background(), AssembleRequest{
		TenantCode: "tenant-a",
		Facts: FactSet{
			Interfaces: []dc2dto.FactRecordResp{
				fact("fact-if-r1-1", "run-1", "r1", FactTypeInterface, "r1:if_index:1", map[string]interface{}{"if_index": float64(1), "if_name_canonical": "gigabitethernet0/1"}),
			},
			RouteTables: []dc2dto.FactRecordResp{
				fact("fact-route-r1", "run-route", "r1", FactTypeRouteTable, "r1:route:default:10.0.2.0/24:192.0.2.2:gigabitethernet0/1", map[string]interface{}{
					"vrf":           "default",
					"destination":   "10.0.2.0/24",
					"next_hop_ip":   "192.0.2.2",
					"out_interface": "gigabitethernet0/1",
					"protocol":      "static",
					"metric":        float64(10),
					"preference":    float64(60),
					"raw":           "S 10.0.2.0/24 via 192.0.2.2",
				}),
			},
		},
	})
	if err != nil {
		t.Fatalf("Assemble returned error: %v", err)
	}
	r1 := findAnalysisDevice(t, snap, "r1")
	if len(r1.RouteTables) != 1 || len(r1.RouteTables[0].Routes) != 1 {
		t.Fatalf("expected one route table route, got %#v", r1.RouteTables)
	}
	route := r1.RouteTables[0].Routes[0]
	if route.Destination != "10.0.2.0/24" || route.NextHopIP != "192.0.2.2" || route.OutInterfaceName != "gigabitethernet0/1" || route.Protocol != "static" {
		t.Fatalf("unexpected assembled route: %#v", route)
	}
	if route.RouteSourceRef != "fact-route-r1" {
		t.Fatalf("expected route source ref, got %#v", route)
	}
}
```

- [ ] **Step 2: Run provider tests**

Run:

```bash
go test -count=1 ./app/netpath/snapshot/provider
```

Expected:

```text
PASS
```

- [ ] **Step 3: Commit**

Run:

```bash
git add app/netpath/snapshot/provider/assembler_test.go
git commit -m "test: cover dc2 route table snapshot assembly"
```

## Task 5: Phase Verification

**Files:**

- No source changes unless verification reveals a real bug.

- [ ] **Step 1: Run DC2 focused tests**

Run:

```bash
go test -count=1 ./app/device_collection2/fact ./app/device_collection2/service/impl -run 'TestProcessFacts(NormalizesNetworkRouteTableRows|RouteTableReportsInvalidRows)|TestBuiltinNetworkCLIContractsIncludeRouteTableDataset'
```

Expected:

```text
PASS
```

- [ ] **Step 2: Run SnapshotProvider tests**

Run:

```bash
go test -count=1 ./app/netpath/snapshot/provider
```

Expected:

```text
PASS
```

- [ ] **Step 3: Run netpath package tests**

Run:

```bash
go test -count=1 ./app/netpath/snapshot ./app/netpath/dto ./app/netpath/engine ./app/netpath/service ./app/netpath/service/impl ./app/netpath/api ./app/netpath/adapter/oneopsnetpath ./app/netpath/snapshot/provider
```

Expected:

```text
PASS
```

- [ ] **Step 4: Confirm dependency boundary**

Run:

```bash
git diff -- go.mod go.sum
rg -n "github.com/netxops/oneops-netpath" app/device_collection2 app/netpath/snapshot/provider app/netpath/snapshot go.mod
```

Expected:

```text
No go.mod/go.sum diff.
No oneops-netpath import in default snapshot/provider or DC2 packages.
```

- [ ] **Step 5: Update roadmap**

Modify `docs/superpowers/plans/2026-06-19-oneops-netpath-master-roadmap.md`:

```text
Phase 3 status: complete.
Phase 4 status: next active phase.
```

- [ ] **Step 6: Commit docs update**

Run:

```bash
git add docs/superpowers/plans/2026-06-19-oneops-netpath-master-roadmap.md
git commit -m "docs: mark route table phase complete"
```

Only run this commit if docs are tracked in the current repository context. If the root docs are outside the active OneOPS git repository, leave the docs file updated but uncommitted and report that explicitly.

## Self-Review Checklist

- [ ] Tests are written before implementation for each code behavior.
- [ ] No `oneops-netpath` import is introduced into default OneOPS packages.
- [ ] No `go.mod` or `go.sum` change is introduced.
- [ ] Route table facts include source provenance through existing DC2 fact infrastructure.
- [ ] Invalid route rows produce issues instead of fake route facts.
- [ ] SnapshotProvider consumes the same field shape emitted by DC2.
- [ ] Live device collection is not executed in this phase.
