# SNMP Static Strategy Dashboard Simplification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the SNMP switch dashboard path from target-materialized tree saving into a simpler static model where one strategy owns one dashboard, strategy-set root dashboards remain entry points, and runtime selection resolves root children by `device_model > platform > manufacturer > catalog > root`.

**Architecture:** Keep strategy-set root dashboard binding as the entry object, but persist strategy dashboards as normal `grafana_dashboard` rows with real `parent_id` and strategy-derived resource metadata. Reuse the existing runtime root-child branch selection code in `metric_strategy.go`, and make saved dashboards/backfilled dashboards conform to the shape that runtime matcher already expects.

**Tech Stack:** Go, GORM, SQLite test DB, existing OneOps platform/grafana services, Go command-line backfill utility.

---

### Task 1: Lock the expected static dashboard shape with tests

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- Test: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Write the failing persistence assertions**

Add assertions to `TestMetricCapabilityContractResolverSavesStrategySetGrafanaDashboardTreeByTarget` so saved `grafana_dashboard` rows must preserve parent linkage and strategy-derived resource fields:

```go
	var savedRootDashboard grafanaModel.GrafanaDashboard
	if err := db.Where("code = ?", result.Nodes[0].DashboardCode).First(&savedRootDashboard).Error; err != nil {
		t.Fatalf("load saved root dashboard: %v", err)
	}
	if strings.TrimSpace(savedRootDashboard.ParentID) != "" {
		t.Fatalf("expected root dashboard parent_id to stay empty, got %#v", savedRootDashboard)
	}

	var savedLeafDashboard grafanaModel.GrafanaDashboard
	if err := db.Where("code = ?", result.Nodes[2].DashboardCode).First(&savedLeafDashboard).Error; err != nil {
		t.Fatalf("load saved leaf dashboard: %v", err)
	}
	if strings.TrimSpace(savedLeafDashboard.ParentID) == "" {
		t.Fatalf("expected strategy dashboard parent_id to point at its root/parent dashboard, got %#v", savedLeafDashboard)
	}
	if strings.TrimSpace(savedLeafDashboard.CatalogID) != "SWITCH" {
		t.Fatalf("expected strategy dashboard catalog_id to follow strategy scope, got %#v", savedLeafDashboard)
	}
	if strings.TrimSpace(savedLeafDashboard.PlatformID) != "VRP" {
		t.Fatalf("expected strategy dashboard platform_id to follow strategy scope, got %#v", savedLeafDashboard)
	}
	if strings.TrimSpace(savedLeafDashboard.ManufacturerID) == "" {
		t.Fatalf("expected strategy dashboard manufacturer_id to be populated, got %#v", savedLeafDashboard)
	}
```

- [ ] **Step 2: Run the targeted test and verify it fails**

Run:

```bash
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverSavesStrategySetGrafanaDashboardTreeByTarget -count=1
```

Expected: FAIL because current save path writes empty `ParentID`, empty `ManufacturerID`, and empty `PlatformID`.

- [ ] **Step 3: Add a focused runtime matching regression test for root-child static dashboards**

Extend `/OneOPS/OneOps/app/platform/api/metric_strategy_device_dashboards_test.go` with a case that creates:
- one root dashboard bound to a strategy set,
- two child dashboards under that root,
- one child constrained by `manufacturer_id + platform_id`,
- one generic child constrained only by `catalog_id`.

Use assertions like:

```go
	if len(items) != 1 {
		t.Fatalf("expected one runtime-matched dashboard candidate, got %#v", items)
	}
	if items[0].DashboardCode != "GDBHUAWEIVRP" {
		t.Fatalf("expected runtime match to prefer the platform-specific child dashboard, got %#v", items[0])
	}
	if items[0].MatchedBy != "platform" {
		t.Fatalf("expected runtime dashboard match granularity to resolve to the platform branch, got %#v", items[0])
	}
```

- [ ] **Step 4: Run the targeted API test and verify it stays red or protected**

Run:

```bash
go test ./app/platform/api -run TestMetricStrategyAPIListDeviceBoundDashboardsByTargetPart_PrefersRuntimeChildDashboardMatch -count=1
```

Expected: PASS if existing matcher already honors static child dashboards, otherwise FAIL and reveal additional runtime gaps before implementation.

- [ ] **Step 5: Commit the red-state test changes**

```bash
git add /OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go /OneOPS/OneOps/app/platform/api/metric_strategy_device_dashboards_test.go
git commit -m "test: lock static snmp dashboard persistence shape"
```

### Task 2: Fix dashboard persistence to save static root-child metadata

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_persistence_service.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- Test: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Add helper logic to resolve strategy resource metadata from the owning strategy**

In `snmp_grafana_switch_dashboard_persistence_service.go`, add a small helper near the persistence methods:

```go
type snmpGrafanaDashboardResourceScope struct {
	ManufacturerID string
	CatalogID      string
	PlatformID     string
	DeviceModelIDs []string
}
```

and a resolver method that:
- returns catalog-only scope for root dashboards,
- returns full strategy-derived scope for strategy dashboards using `StrategySrv.Get(...)`.

- [ ] **Step 2: Run the persistence test to confirm it still fails before wiring**

Run:

```bash
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverSavesStrategySetGrafanaDashboardTreeByTarget -count=1
```

Expected: FAIL before the save logic is updated.

- [ ] **Step 3: Write the minimal save-path fix**

Update the save loop in `saveResolvedTreeGeneration(...)` to persist static parent/resource fields instead of blanking them:

```go
		if strings.TrimSpace(node.ParentNodeKey) != "" {
			if parent := nodeByKey[strings.TrimSpace(node.ParentNodeKey)]; parent != nil {
				dashboard.ParentID = strings.TrimSpace(parent.Dashboard.ID)
			}
		} else {
			dashboard.ParentID = ""
		}

		scope, err := s.resolveDashboardResourceScope(ctx, materialized, node)
		if err != nil {
			return nil, err
		}
		dashboard.ManufacturerID = strings.TrimSpace(scope.ManufacturerID)
		dashboard.DeviceModelIDs = append([]string(nil), scope.DeviceModelIDs...)
		dashboard.CatalogID = strings.TrimSpace(scope.CatalogID)
		dashboard.PlatformID = strings.TrimSpace(scope.PlatformID)
```

Make sure the root dashboard still remains generic enough to act as entry only.

- [ ] **Step 4: Run the persistence test and verify it passes**

Run:

```bash
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverSavesStrategySetGrafanaDashboardTreeByTarget -count=1
```

Expected: PASS with the saved root/strategy dashboards now carrying correct parent/resource metadata.

- [ ] **Step 5: Commit the persistence fix**

```bash
git add /OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_persistence_service.go /OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go
git commit -m "feat: persist static snmp strategy dashboard metadata"
```

### Task 3: Backfill existing dashboard rows into the static model

**Files:**
- Create: `/OneOPS/OneOps/cmd/snmp_dashboard_backfill/main.go`
- Modify: `/OneOPS/OneOps/go.mod`
- Test: `/OneOPS/OneOps/app/platform/api/metric_strategy_device_dashboards_test.go`

- [ ] **Step 1: Write a backfill-oriented regression test against the runtime selector**

Add a fixture in `metric_strategy_device_dashboards_test.go` that simulates:
- a root dashboard already bound to a strategy set,
- a strategy dashboard row under that root with filled `parent_id`, `manufacturer_id`, `catalog_id`, `platform_id`,
- no target-materialized tree dependency.

Assert that runtime selection uses only `grafana_dashboard` parent/metadata shape.

- [ ] **Step 2: Run the API regression and verify current behavior**

Run:

```bash
go test ./app/platform/api -run TestMetricStrategyAPIListDeviceBoundDashboardsByTargetPart_PrefersRuntimeChildDashboardMatch -count=1
```

Expected: PASS or reveal any remaining assumption that depends on target-materialized rows instead of static child dashboards.

- [ ] **Step 3: Create the backfill command**

Add `/OneOPS/OneOps/cmd/snmp_dashboard_backfill/main.go` that:
- loads MySQL config,
- loads strategy-set root bindings,
- loads strategy dashboards from existing target/tree rows,
- fills `parent_id` to the root dashboard,
- copies strategy `manufacturer_id/catalog_id/platform_id/device_model_ids` into `grafana_dashboard`,
- prints a compact summary of updated rows.

Use a main flow like:

```go
func main() {
	ctx := context.Background()
	if err := run(ctx); err != nil {
		log.Fatalf("snmp dashboard backfill failed: %v", err)
	}
}
```

Keep the first version intentionally simple:
- all strategy dashboards become direct children of the root,
- no recursive parent reconstruction yet.

- [ ] **Step 4: Run the command in dry-run or report mode against the current environment**

Run:

```bash
go run ./cmd/snmp_dashboard_backfill --dry-run
```

Expected: A readable count of root bindings found, strategy dashboards discovered, and rows that would be updated.

- [ ] **Step 5: Commit the backfill utility**

```bash
git add /OneOPS/OneOps/cmd/snmp_dashboard_backfill/main.go /OneOPS/OneOps/app/platform/api/metric_strategy_device_dashboards_test.go /OneOPS/OneOps/go.mod
git commit -m "feat: add snmp dashboard static backfill utility"
```

### Task 4: Verify end-to-end and record the migration path

**Files:**
- Modify: `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-network-strategy-generic-dashboard-panel-design.md`
- Modify: `/OneOPS/docs/superpowers/plans/2026-06-15-snmp-static-strategy-dashboard-simplification.md`

- [ ] **Step 1: Run focused backend verification**

Run:

```bash
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolverSavesStrategySetGrafanaDashboardTreeByTarget|TestMetricCapabilityContractResolverSavesStrategySetGrafanaDashboardTreeByTarget_GenericDefaultVariant' -count=1
go test ./app/platform/api -run 'TestMetricStrategyAPIListDeviceBoundDashboardsByTargetPart' -count=1
```

Expected: PASS for the focused persistence and runtime selection suite.

- [ ] **Step 2: Run the backfill command for real against the current database**

Run:

```bash
go run ./cmd/snmp_dashboard_backfill
```

Expected: Non-zero updated dashboard count, with strategy dashboards now attached to their root dashboards and populated with resource metadata.

- [ ] **Step 3: Record the simplified runtime contract in the spec**

Append a short “Implementation Contract” section to `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-network-strategy-generic-dashboard-panel-design.md` stating:
- root dashboard is strategy-set bound, not globally unique,
- one strategy = one static dashboard,
- runtime selection uses `device_model > platform > manufacturer > catalog > root`,
- no target-time dashboard generation is required for routing.

- [ ] **Step 4: Re-run the focused verification after doc update**

Run:

```bash
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverSavesStrategySetGrafanaDashboardTreeByTarget -count=1
go test ./app/platform/api -run TestMetricStrategyAPIListDeviceBoundDashboardsByTargetPart_PrefersRuntimeChildDashboardMatch -count=1
```

Expected: PASS; docs changes should not affect code paths.

- [ ] **Step 5: Commit the verified migration result**

```bash
git add /OneOPS/docs/superpowers/specs/2026-06-14-snmp-network-strategy-generic-dashboard-panel-design.md /OneOPS/docs/superpowers/plans/2026-06-15-snmp-static-strategy-dashboard-simplification.md
git commit -m "docs: record static snmp dashboard routing contract"
```

## Self-Review

- Spec coverage: The plan covers existing data repair, future save-path correctness, runtime root-child routing, and documentation of the simplified contract.
- Placeholder scan: No `TODO`/`TBD` markers remain; every task lists exact files and verification commands.
- Type consistency: The implementation centers on existing `grafana_dashboard`, `TeleabsStrategySetDashboardBinding`, and runtime branch matching types already used by the codebase.

Plan complete and saved to `docs/superpowers/plans/2026-06-15-snmp-static-strategy-dashboard-simplification.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration

2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Assuming Inline Execution for this session unless the user redirects.
