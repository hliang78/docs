# SNMP Dashboard Remaining Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the explicitly requested remaining SNMP switch dashboard closure items: multi-vendor validation, Grafana visual alignment, real SNMP data validation, and OneOps frontend entry integration.

**Architecture:** Keep the existing Huawei / VRP / S5735 closed loop as the reference path. Extend only the switch dashboard family contract so concrete vendor/model copies resolve inherited strategy and dashboard behavior, then verify the generated Grafana dashboard, real metric flow, and frontend open path from existing OneOps screens.

**Tech Stack:** Go/GORM service tests, quick_env MySQL seed SQL and shell smoke scripts, Grafana dashboard JSON, Prometheus-compatible metric queries, Vue 3 / TypeScript / Ant Design Vue frontend smoke scripts.

---

## Scope Boundary

Included in this closure:

- Multi-vendor switch validation for Huawei, H3C, Cisco, Maipu, and Fiberhome device families.
- Grafana visual tuning for the existing SNMP switch dashboard family only.
- Real SNMP metric data validation through the existing quick_env Telegraf to Prometheus/VictoriaMetrics path.
- OneOps frontend entry that opens the saved/synced Grafana dashboard from the existing strategy set or device context.

Excluded from this closure:

- New non-switch device domains.
- A custom Grafana plugin or iframe embedding framework.
- Rebuilding the OneOps frontend navigation model.
- Alert workflow redesign.
- Automated physical device onboarding beyond validating one configured target per vendor family.
- A full dashboard inheritance engine inside Grafana. Dashboard inheritance remains a OneOps materialization concern.

## Current Baseline

- Huawei / VRP / S5735 dashboard materialization, save-and-sync, panel binding, platform evidence, and Grafana API readback are already closed.
- `quick_env/start.sh` already replays the Huawei switch strategy seed and platform evidence seed.
- Existing smoke entry: `quick_env/scripts/smoke_snmp_switch_dashboard_save.sh`.
- Existing backend implementation: `OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`.
- Existing backend tests: `OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`.
- Existing frontend save/sync entry: `OneOPS-UI/src/views/platform/StrategyTemplate/StrategySetDetailDrawer.vue`.

## Closure Definition

This remaining work is closed only when all of these are true:

- Vendor matrix can materialize a switch dashboard for Huawei, H3C, Cisco, Maipu, and Fiberhome.
- Each concrete vendor/model path resolves inherited parent and ancestor strategy content before vendor-specific overrides.
- Generated Grafana dashboard preserves the screenshot-style operational layout: identity/status top band, instant health cards, interface and port map sections, resource/traffic curves, L2 evidence, platform evidence.
- Real SNMP metrics are visible through the Prometheus-compatible query API for at least one configured live target.
- OneOps frontend exposes an obvious "open Grafana" action after dashboard save/sync without requiring the operator to copy UID manually.

## File Structure

- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
  - Adds vendor matrix and visual dashboard contract tests.
- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
  - Minimal resolver/template changes required by failing tests.
- Modify: `quick_env/start.sh`
  - Replays all switch dashboard family seed files used by the closure matrix.
- Modify: `quick_env/tests/test_seed_template_guard.py`
  - Guards seed replay, vendor matrix, panel binding, visual contract, and smoke script drift.
- Create: `quick_env/docker-entrypoint-initdb.d/zzzzzzzzzz-cisco-snmp-network-strategy-bootstrap.sql`
  - Adds Cisco switch strategy family seed if no Cisco seed exists.
- Create: `quick_env/scripts/smoke_snmp_switch_dashboard_vendor_matrix.sh`
  - Runs dashboard save/sync smoke across the vendor matrix.
- Create: `quick_env/scripts/smoke_snmp_switch_metric_data.sh`
  - Verifies real SNMP metrics are queryable through the Prometheus-compatible endpoint.
- Modify: `quick_env/scripts/smoke_snmp_switch_dashboard_save.sh`
  - Adds optional vendor/target arguments while preserving current Huawei defaults.
- Modify: `OneOPS-UI/src/views/platform/StrategyTemplate/snmpStrategySetGrafanaDashboardSave.ts`
  - Normalizes saved dashboard URL/UID state for frontend entry.
- Modify: `OneOPS-UI/src/views/platform/StrategyTemplate/StrategySetDetailDrawer.vue`
  - Adds an "Open Grafana" action when a saved dashboard UID or URL exists.
- Create: `OneOPS-UI/scripts/snmp-strategy-set-grafana-dashboard-open-link-smoke.ts`
  - Unit-style smoke for URL state and open action behavior.
- Modify: `docs/superpowers/specs/2026-06-12-snmp-grafana-dashboard-screenshot-alignment-design.md`
  - Adds final visual contract and screenshot-to-Grafana mapping.
- Modify: `docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`
  - Adds remaining closure status and exact validation commands.

---

### Task 1: Lock Vendor Matrix And Seed Replay Contract

**Files:**
- Modify: `quick_env/tests/test_seed_template_guard.py`
- Modify: `quick_env/start.sh`
- Create if missing: `quick_env/docker-entrypoint-initdb.d/zzzzzzzzzz-cisco-snmp-network-strategy-bootstrap.sql`

- [ ] **Step 1: Write failing seed replay guard**

Add this test to `quick_env/tests/test_seed_template_guard.py`:

```python
def test_start_replays_all_snmp_switch_vendor_dashboard_seed_files():
    start_script = Path("quick_env/start.sh").read_text(encoding="utf-8")
    expected_seed_files = [
        "zzzzzzzzzz-huawei-snmp-network-strategy-bootstrap.sql",
        "zzzzzzzzzz-h3c-snmp-network-strategy-bootstrap.sql",
        "zzzzzzzzzz-maipu-snmp-network-strategy-bootstrap.sql",
        "zzzzzzzz-fiberhome-snmp-network-strategy-bootstrap.sql",
        "zzzzzzzzzz-cisco-snmp-network-strategy-bootstrap.sql",
        "zzzzzzzzzz-snmp-switch-platform-evidence-bootstrap.sql",
    ]

    for seed_file in expected_seed_files:
        assert seed_file in start_script
        assert Path("quick_env/docker-entrypoint-initdb.d", seed_file).exists()
```

- [ ] **Step 2: Run the guard and confirm it fails for Cisco or replay drift**

Run:

```bash
python3 quick_env/tests/test_seed_template_guard.py -v
```

Expected before implementation: fail if Cisco seed is missing or `start.sh` does not replay every expected vendor seed.

- [ ] **Step 3: Add Cisco seed with the same tree semantics**

Create `quick_env/docker-entrypoint-initdb.d/zzzzzzzzzz-cisco-snmp-network-strategy-bootstrap.sql` with these minimum records, using existing seed column names from the Huawei/H3C/Maipu files:

```sql
-- Cisco SNMP switch strategy seed.
-- Purpose: prove vendor/model concrete copies inherit the common switch dashboard family.

SET @now := NOW(3);
SET @strategy_set_code := 'SNMP_CISCO_SWITCH';
SET @parent_strategy_set_code := 'SNMP_SWITCH_BASE';
SET @device_vendor := 'Cisco';
SET @device_os := 'IOS';
SET @device_model := 'Catalyst';
SET @target_device_code := 'CISCO-SW-01';

-- Reuse the exact table/column shape used by existing SNMP strategy bootstrap files.
-- The implementation step must copy the insert/upsert pattern from:
-- quick_env/docker-entrypoint-initdb.d/zzzzzzzzzz-huawei-snmp-network-strategy-bootstrap.sql
-- and only change vendor/os/model/target identifiers above.
```

When implementing, replace the marker block with concrete `INSERT ... ON DUPLICATE KEY UPDATE` statements copied from the closest existing vendor seed. Keep IDs no longer than 36 characters.

- [ ] **Step 4: Replay all vendor seeds in `start.sh`**

In `sync_snmp_switch_dashboard_seed_records`, ensure this exact order appears:

```bash
replay_optional_seed "zzzzzzzzzz-huawei-snmp-network-strategy-bootstrap.sql"
replay_optional_seed "zzzzzzzzzz-h3c-snmp-network-strategy-bootstrap.sql"
replay_optional_seed "zzzzzzzzzz-maipu-snmp-network-strategy-bootstrap.sql"
replay_optional_seed "zzzzzzzz-fiberhome-snmp-network-strategy-bootstrap.sql"
replay_optional_seed "zzzzzzzzzz-cisco-snmp-network-strategy-bootstrap.sql"
replay_optional_seed "zzzzzzzzzz-snmp-switch-platform-evidence-bootstrap.sql"
```

- [ ] **Step 5: Verify guard passes**

Run:

```bash
python3 quick_env/tests/test_seed_template_guard.py -v
```

Expected: all seed guard tests pass.

---

### Task 2: Backend Multi-Vendor Dashboard Resolution Contract

**Files:**
- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- Modify if required: `OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`

- [ ] **Step 1: Add table-driven vendor matrix test**

Add this test near the existing Huawei S5735 dashboard closure test:

```go
func TestMetricCapabilityContractResolverMaterializesSwitchDashboardByVendorFamily(t *testing.T) {
    cases := []struct {
        name          string
        vendor        string
        os            string
        model         string
        targetCode    string
        expectedHints []string
    }{
        {
            name:       "Huawei VRP S5735",
            vendor:     "Huawei",
            os:         "VRP",
            model:      "S5735",
            targetCode: "AST20260603174801664",
            expectedHints: []string{
                "interface_utilization.top10",
                "l2_neighbors.summary",
                "platform_alerts.active",
            },
        },
        {
            name:       "H3C Comware switch",
            vendor:     "H3C",
            os:         "Comware",
            model:      "S5560X",
            targetCode: "H3C-SW-01",
            expectedHints: []string{
                "interface_utilization.top10",
                "l2_neighbors.summary",
                "platform_alerts.active",
            },
        },
        {
            name:       "Cisco IOS Catalyst",
            vendor:     "Cisco",
            os:         "IOS",
            model:      "Catalyst",
            targetCode: "CISCO-SW-01",
            expectedHints: []string{
                "interface_utilization.top10",
                "l2_neighbors.summary",
                "platform_alerts.active",
            },
        },
        {
            name:       "Maipu MyPower switch",
            vendor:     "Maipu",
            os:         "MyPower",
            model:      "S4300",
            targetCode: "MAIPU-SW-01",
            expectedHints: []string{
                "interface_utilization.top10",
                "l2_neighbors.summary",
                "platform_alerts.active",
            },
        },
        {
            name:       "Fiberhome Fengine switch",
            vendor:     "Fiberhome",
            os:         "Fengine",
            model:      "S5800",
            targetCode: "FIBERHOME-SW-01",
            expectedHints: []string{
                "interface_utilization.top10",
                "l2_neighbors.summary",
                "platform_alerts.active",
            },
        },
    }

    for _, tc := range cases {
        t.Run(tc.name, func(t *testing.T) {
            dashboard := materializeSwitchDashboardForTest(t, tc.vendor, tc.os, tc.model, tc.targetCode)

            if dashboard.UID == "" {
                t.Fatalf("dashboard UID is empty")
            }
            if !strings.Contains(dashboard.Title, tc.targetCode) {
                t.Fatalf("dashboard title %q does not include target %q", dashboard.Title, tc.targetCode)
            }

            payload, err := json.Marshal(dashboard)
            if err != nil {
                t.Fatalf("marshal dashboard: %v", err)
            }
            text := string(payload)
            for _, hint := range tc.expectedHints {
                if !strings.Contains(text, hint) {
                    t.Fatalf("dashboard for %s missing inherited panel hint %q", tc.name, hint)
                }
            }
        })
    }
}
```

If `materializeSwitchDashboardForTest` does not exist, extract it from the existing Huawei test instead of creating a second fixture path.

- [ ] **Step 2: Run the targeted test and confirm the real failure**

Run:

```bash
cd OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverMaterializesSwitchDashboardByVendorFamily -count=1
```

Expected before implementation: fail only for missing vendor seed/fixture/resolution support, not for unrelated package setup.

- [ ] **Step 3: Implement minimal resolver or fixture changes**

Keep the resolver behavior:

```text
concrete vendor/model strategy set
  -> inherits vendor strategy set
  -> inherits switch family strategy set
  -> inherits common SNMP metric groups
```

Dashboard selection rule:

```text
Use the concrete matched strategy set as the runtime target,
but materialize dashboard panels from the inherited strategy chain.
Vendor/model-specific panels may override parent panels by stable panel key.
```

Do not add Grafana-side dashboard inheritance in this task.

- [ ] **Step 4: Verify vendor matrix test passes**

Run:

```bash
cd OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverMaterializesSwitchDashboardByVendorFamily -count=1
```

Expected: PASS.

---

### Task 3: Grafana Visual Contract For Switch Dashboard

**Files:**
- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `docs/superpowers/specs/2026-06-12-snmp-grafana-dashboard-screenshot-alignment-design.md`

- [ ] **Step 1: Add visual layout contract test**

Add a test that asserts panel roles, not pixel-perfect rendering:

```go
func TestSwitchGrafanaDashboardUsesOpsScreenshotLayoutContract(t *testing.T) {
    dashboard := materializeSwitchDashboardForTest(t, "Huawei", "VRP", "S5735", "AST20260603174801664")
    payload, err := json.Marshal(dashboard)
    if err != nil {
        t.Fatalf("marshal dashboard: %v", err)
    }
    text := string(payload)

    expectedContracts := []string{
        "device_identity.header",
        "overall_health.instant",
        "availability.instant",
        "active_alerts.instant",
        "cpu_usage.timeseries",
        "memory_usage.timeseries",
        "temperature.instant",
        "interface_utilization.top10",
        "port_map.status",
        "traffic.throughput",
        "traffic.pps",
        "traffic.mix",
        "l2_neighbors.summary",
        "l2_mac_table.summary",
        "l3_arp_table.summary",
        "platform_alerts.active",
        "platform_events.recent",
        "platform_config.compliance",
    }

    for _, contract := range expectedContracts {
        if !strings.Contains(text, contract) {
            t.Fatalf("dashboard missing visual contract marker %q", contract)
        }
    }
}
```

- [ ] **Step 2: Run the visual contract test**

Run:

```bash
cd OneOps
go test ./app/platform/service/impl -run TestSwitchGrafanaDashboardUsesOpsScreenshotLayoutContract -count=1
```

Expected before implementation: fail for missing panel keys or role markers that are not yet encoded.

- [ ] **Step 3: Tune generated Grafana JSON only inside the switch dashboard generator**

Implementation rules:

- First row: identity/header and stat panels.
- Instant panels use `stat`, clear thresholds, and stable panel keys.
- Curves use `timeseries`.
- Interface utilization uses `table`.
- Port map uses `status-history` when supported by the existing Grafana JSON conventions; otherwise use a compact `table` with colored cell thresholds.
- Traffic mix uses `piechart` only if already supported by the Grafana version in quick_env; otherwise keep a table or time series fallback.
- Platform evidence panels must keep click-through values or labels that can be traced back to OneOps data.

Do not change datasource provisioning, Grafana auth, or global theme.

- [ ] **Step 4: Document screenshot mapping**

Append this section to `docs/superpowers/specs/2026-06-12-snmp-grafana-dashboard-screenshot-alignment-design.md`:

```markdown
## Final Visual Contract For Grafana Closure

The screenshot is treated as an operational information architecture reference, not a pixel-perfect design. Grafana must preserve:

- Top identity and instant state: device, vendor/model, location, uptime, last poll, health, availability, active alerts, CPU, memory, temperature, power/fan if present.
- Investigation center: top interfaces, port map, resource curves, traffic curves, and traffic mix.
- Network-layer evidence: L2 neighbors, MAC table, ARP table, VLAN/STP summaries when the strategy chain exposes those metric groups.
- Platform evidence: active alerts, recent events, config backup/compliance, and policy-generated links back to OneOps evidence.

Panel keys are the compatibility contract. Layout can be tuned, but panel keys must remain stable so strategy inheritance, panel binding, and frontend open actions continue to work.
```

- [ ] **Step 5: Verify visual contract test passes**

Run:

```bash
cd OneOps
go test ./app/platform/service/impl -run TestSwitchGrafanaDashboardUsesOpsScreenshotLayoutContract -count=1
```

Expected: PASS.

---

### Task 4: Vendor Matrix Save-And-Sync Smoke

**Files:**
- Modify: `quick_env/scripts/smoke_snmp_switch_dashboard_save.sh`
- Create: `quick_env/scripts/smoke_snmp_switch_dashboard_vendor_matrix.sh`
- Modify: `quick_env/tests/test_seed_template_guard.py`

- [ ] **Step 1: Make existing smoke accept target overrides**

In `quick_env/scripts/smoke_snmp_switch_dashboard_save.sh`, preserve current defaults and add:

```bash
SNMP_TARGET_DEVICE_CODE="${SNMP_TARGET_DEVICE_CODE:-AST20260603174801664}"
SNMP_TARGET_VENDOR="${SNMP_TARGET_VENDOR:-Huawei}"
SNMP_TARGET_OS="${SNMP_TARGET_OS:-VRP}"
SNMP_TARGET_MODEL="${SNMP_TARGET_MODEL:-S5735}"
```

Use these values in request payloads instead of hard-coded Huawei-only values.

- [ ] **Step 2: Create vendor matrix smoke script**

Create `quick_env/scripts/smoke_snmp_switch_dashboard_vendor_matrix.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SMOKE_SCRIPT="${ROOT_DIR}/quick_env/scripts/smoke_snmp_switch_dashboard_save.sh"

run_vendor() {
  local vendor="$1"
  local os="$2"
  local model="$3"
  local target="$4"

  echo "[vendor-matrix] ${vendor} ${os} ${model} target=${target}"
  SNMP_TARGET_VENDOR="${vendor}" \
  SNMP_TARGET_OS="${os}" \
  SNMP_TARGET_MODEL="${model}" \
  SNMP_TARGET_DEVICE_CODE="${target}" \
  "${SMOKE_SCRIPT}"
}

run_vendor "Huawei" "VRP" "S5735" "AST20260603174801664"
run_vendor "H3C" "Comware" "S5560X" "H3C-SW-01"
run_vendor "Cisco" "IOS" "Catalyst" "CISCO-SW-01"
run_vendor "Maipu" "MyPower" "S4300" "MAIPU-SW-01"
run_vendor "Fiberhome" "Fengine" "S5800" "FIBERHOME-SW-01"

echo "[vendor-matrix] all vendor dashboard save/sync checks passed"
```

- [ ] **Step 3: Add guard for matrix script**

Add this test to `quick_env/tests/test_seed_template_guard.py`:

```python
def test_snmp_switch_vendor_matrix_smoke_covers_required_families():
    script = Path("quick_env/scripts/smoke_snmp_switch_dashboard_vendor_matrix.sh").read_text(encoding="utf-8")
    for vendor in ["Huawei", "H3C", "Cisco", "Maipu", "Fiberhome"]:
        assert vendor in script
    for target in ["AST20260603174801664", "H3C-SW-01", "CISCO-SW-01", "MAIPU-SW-01", "FIBERHOME-SW-01"]:
        assert target in script
```

- [ ] **Step 4: Verify shell and guard**

Run:

```bash
bash -n quick_env/scripts/smoke_snmp_switch_dashboard_save.sh
bash -n quick_env/scripts/smoke_snmp_switch_dashboard_vendor_matrix.sh
python3 quick_env/tests/test_seed_template_guard.py -v
```

Expected: all pass.

- [ ] **Step 5: Run live vendor matrix smoke**

With quick_env services and OneOps API running:

```bash
SAVE_AND_SYNC=true \
ONEOPS_API_BASE_URL=http://127.0.0.1:8380/api/v1 \
ONEOPS_AUTH_TOKEN=abc123 \
MYSQL_PORT=3606 \
MYSQL_ROOT_PASSWORD='UniOPS@Passw0rd' \
GRAFANA_URL=http://127.0.0.1:3300 \
GRAFANA_USER=admin \
GRAFANA_PASSWORD=admin \
quick_env/scripts/smoke_snmp_switch_dashboard_vendor_matrix.sh
```

Expected: one dashboard save/sync success per vendor.

---

### Task 5: Real SNMP Metric Data Validation

**Files:**
- Create: `quick_env/scripts/smoke_snmp_switch_metric_data.sh`
- Modify: `quick_env/tests/test_seed_template_guard.py`
- Modify: `docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [ ] **Step 1: Create real metric smoke script**

Create `quick_env/scripts/smoke_snmp_switch_metric_data.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

PROMETHEUS_URL="${PROMETHEUS_URL:-http://127.0.0.1:8428}"
SNMP_TARGET_DEVICE_CODE="${SNMP_TARGET_DEVICE_CODE:-AST20260603174801664}"
TIME_WINDOW="${TIME_WINDOW:-30m}"

queries=(
  "snmp_cpu_usage{device_code=\"${SNMP_TARGET_DEVICE_CODE}\"}"
  "snmp_memory_usage{device_code=\"${SNMP_TARGET_DEVICE_CODE}\"}"
  "snmp_interface_ifInOctets{device_code=\"${SNMP_TARGET_DEVICE_CODE}\"}"
  "snmp_interface_ifOutOctets{device_code=\"${SNMP_TARGET_DEVICE_CODE}\"}"
)

if command -v jq >/dev/null 2>&1; then
  jq_filter='.data.result | length'
else
  jq_filter=''
fi

for query in "${queries[@]}"; do
  echo "[metric-data] query=${query}"
  encoded_query="$(python3 -c 'import sys, urllib.parse; print(urllib.parse.urlencode({"query": sys.argv[1]}))' "${query}")"
  response="$(curl -fsS "${PROMETHEUS_URL}/api/v1/query?${encoded_query}")"

  if [ -n "${jq_filter}" ]; then
    count="$(printf '%s' "${response}" | jq -r "${jq_filter}")"
    if [ "${count}" = "0" ]; then
      echo "[metric-data] no real SNMP data for query=${query} target=${SNMP_TARGET_DEVICE_CODE} window=${TIME_WINDOW}" >&2
      exit 2
    fi
  else
    if ! printf '%s' "${response}" | grep -q '"result":\['; then
      echo "[metric-data] invalid Prometheus response for query=${query}" >&2
      exit 2
    fi
    if printf '%s' "${response}" | grep -q '"result":\[\]'; then
      echo "[metric-data] no real SNMP data for query=${query} target=${SNMP_TARGET_DEVICE_CODE} window=${TIME_WINDOW}" >&2
      exit 2
    fi
  fi
done

echo "[metric-data] real SNMP metric data is available for target=${SNMP_TARGET_DEVICE_CODE}"
```

- [ ] **Step 2: Add guard for real metric queries**

Add this test to `quick_env/tests/test_seed_template_guard.py`:

```python
def test_real_snmp_metric_data_smoke_queries_dashboard_metrics():
    script = Path("quick_env/scripts/smoke_snmp_switch_metric_data.sh").read_text(encoding="utf-8")
    expected_queries = [
        "snmp_cpu_usage",
        "snmp_memory_usage",
        "snmp_interface_ifInOctets",
        "snmp_interface_ifOutOctets",
        "/api/v1/query",
    ]
    for query in expected_queries:
        assert query in script
```

- [ ] **Step 3: Verify shell and guard**

Run:

```bash
bash -n quick_env/scripts/smoke_snmp_switch_metric_data.sh
python3 quick_env/tests/test_seed_template_guard.py -v
```

Expected: PASS.

- [ ] **Step 4: Run against a live SNMP target**

After Telegraf has scraped a real device:

```bash
PROMETHEUS_URL=http://127.0.0.1:8428 \
SNMP_TARGET_DEVICE_CODE=AST20260603174801664 \
quick_env/scripts/smoke_snmp_switch_metric_data.sh
```

Expected: PASS. If it exits `2`, the dashboard code path may be correct but the real SNMP data loop is not closed yet.

---

### Task 6: Frontend Open Grafana Entry

**Files:**
- Modify: `OneOPS-UI/src/views/platform/StrategyTemplate/snmpStrategySetGrafanaDashboardSave.ts`
- Modify: `OneOPS-UI/src/views/platform/StrategyTemplate/StrategySetDetailDrawer.vue`
- Create: `OneOPS-UI/scripts/snmp-strategy-set-grafana-dashboard-open-link-smoke.ts`

- [ ] **Step 1: Add URL normalization smoke**

Create `OneOPS-UI/scripts/snmp-strategy-set-grafana-dashboard-open-link-smoke.ts`:

```ts
import assert from 'node:assert/strict'

function buildGrafanaDashboardUrl(baseUrl: string, uid: string): string {
  const cleanBase = baseUrl.replace(/\/+$/, '')
  return `${cleanBase}/d/${encodeURIComponent(uid)}`
}

assert.equal(
  buildGrafanaDashboardUrl('http://127.0.0.1:3300/', 'snmp-switch-abc'),
  'http://127.0.0.1:3300/d/snmp-switch-abc'
)

assert.equal(
  buildGrafanaDashboardUrl('http://grafana.local', 'snmp switch uid'),
  'http://grafana.local/d/snmp%20switch%20uid'
)

console.log('snmp grafana open link smoke passed')
```

- [ ] **Step 2: Add package script**

In `OneOPS-UI/package.json`, add:

```json
"smoke:snmp-strategy-set-grafana-dashboard-open-link": "npx esbuild scripts/snmp-strategy-set-grafana-dashboard-open-link-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/snmp-strategy-set-grafana-dashboard-open-link-smoke.mjs >/dev/null && node .tmp/snmp-strategy-set-grafana-dashboard-open-link-smoke.mjs"
```

- [ ] **Step 3: Normalize saved dashboard state**

In `OneOPS-UI/src/views/platform/StrategyTemplate/snmpStrategySetGrafanaDashboardSave.ts`, expose a small helper equivalent to:

```ts
export const buildGrafanaDashboardUrl = (baseUrl: string, uid: string): string => {
  const cleanBase = baseUrl.replace(/\/+$/, '')
  return `${cleanBase}/d/${encodeURIComponent(uid)}`
}
```

Use it when save/sync returns a dashboard UID but no full URL.

- [ ] **Step 4: Add visible open action in `StrategySetDetailDrawer.vue`**

Add an Ant Design Vue button near the existing save/sync controls:

```vue
<a-button
  v-if="grafanaDashboardSaveState.dashboardUrl"
  type="link"
  @click="openGrafanaDashboard"
>
  打开 Grafana
</a-button>
```

Add the method:

```ts
const openGrafanaDashboard = () => {
  const url = grafanaDashboardSaveState.dashboardUrl
  if (!url) return
  window.open(url, '_blank', 'noopener,noreferrer')
}
```

Keep this as an external open action. Do not embed Grafana in OneOps in this closure.

- [ ] **Step 5: Verify frontend smoke**

Run:

```bash
cd OneOPS-UI
npm run smoke:snmp-strategy-set-grafana-dashboard-open-link
npm run smoke:snmp-strategy-set-grafana-dashboard-save-action
```

Expected: both pass.

---

### Task 7: Handoff And Closure Evidence

**Files:**
- Modify: `docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [ ] **Step 1: Add remaining closure table**

Append:

```markdown
## Remaining SNMP Switch Dashboard Closure Matrix

| Item | Closure Evidence | Status |
| --- | --- | --- |
| Multi-vendor validation | `quick_env/scripts/smoke_snmp_switch_dashboard_vendor_matrix.sh` passes for Huawei, H3C, Cisco, Maipu, Fiberhome | Pending until live run passes |
| Visual experience tuning | `TestSwitchGrafanaDashboardUsesOpsScreenshotLayoutContract` passes and panel keys match screenshot-aligned contract | Pending until backend test passes |
| Real SNMP data validation | `quick_env/scripts/smoke_snmp_switch_metric_data.sh` returns non-empty query results for a live target | Pending until live SNMP target data exists |
| Frontend platform entry | `npm run smoke:snmp-strategy-set-grafana-dashboard-open-link` and save-action smoke pass | Pending until UI smoke passes |
```

- [ ] **Step 2: Add exact verification commands**

Append:

````markdown
### Remaining Closure Verification Commands

```bash
python3 quick_env/tests/test_seed_template_guard.py -v

cd OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolverMaterializesSwitchDashboardByVendorFamily|TestSwitchGrafanaDashboardUsesOpsScreenshotLayoutContract' -count=1

cd ../OneOPS-UI
npm run smoke:snmp-strategy-set-grafana-dashboard-open-link
npm run smoke:snmp-strategy-set-grafana-dashboard-save-action

cd ..
bash -n quick_env/scripts/smoke_snmp_switch_dashboard_vendor_matrix.sh
bash -n quick_env/scripts/smoke_snmp_switch_metric_data.sh
```

Live validation:

```bash
SAVE_AND_SYNC=true \
ONEOPS_API_BASE_URL=http://127.0.0.1:8380/api/v1 \
ONEOPS_AUTH_TOKEN=abc123 \
MYSQL_PORT=3606 \
MYSQL_ROOT_PASSWORD='UniOPS@Passw0rd' \
GRAFANA_URL=http://127.0.0.1:3300 \
GRAFANA_USER=admin \
GRAFANA_PASSWORD=admin \
quick_env/scripts/smoke_snmp_switch_dashboard_vendor_matrix.sh

PROMETHEUS_URL=http://127.0.0.1:8428 \
SNMP_TARGET_DEVICE_CODE=AST20260603174801664 \
quick_env/scripts/smoke_snmp_switch_metric_data.sh
```
````

- [ ] **Step 3: Verify Markdown and diff**

Run:

```bash
git diff --check -- \
  docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md \
  docs/superpowers/specs/2026-06-12-snmp-grafana-dashboard-screenshot-alignment-design.md \
  docs/superpowers/plans/2026-06-12-snmp-dashboard-remaining-closure-plan.md
```

Expected: no whitespace errors.

---

## Final Verification Gate

Run these before declaring the remaining closure complete:

```bash
python3 quick_env/tests/test_seed_template_guard.py -v
python3 quick_env/tests/test_validate_nacos_seed_runtime.py -v

cd OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolverMaterializesHuaweiS5735ClosedLoopDashboardByTarget|TestMetricCapabilityContractResolverMaterializesSwitchDashboardByVendorFamily|TestSwitchGrafanaDashboardUsesOpsScreenshotLayoutContract' -count=1

cd ../OneOPS-UI
npm run smoke:snmp-strategy-set-grafana-dashboard-open-link
npm run smoke:snmp-strategy-set-grafana-dashboard-save-action

cd ..
bash -n quick_env/scripts/smoke_snmp_switch_dashboard_save.sh
bash -n quick_env/scripts/smoke_snmp_switch_dashboard_vendor_matrix.sh
bash -n quick_env/scripts/smoke_snmp_switch_metric_data.sh
```

Live closure commands:

```bash
SAVE_AND_SYNC=true \
ONEOPS_API_BASE_URL=http://127.0.0.1:8380/api/v1 \
ONEOPS_AUTH_TOKEN=abc123 \
MYSQL_PORT=3606 \
MYSQL_ROOT_PASSWORD='UniOPS@Passw0rd' \
GRAFANA_URL=http://127.0.0.1:3300 \
GRAFANA_USER=admin \
GRAFANA_PASSWORD=admin \
quick_env/scripts/smoke_snmp_switch_dashboard_vendor_matrix.sh

PROMETHEUS_URL=http://127.0.0.1:8428 \
SNMP_TARGET_DEVICE_CODE=AST20260603174801664 \
quick_env/scripts/smoke_snmp_switch_metric_data.sh
```

The remaining closure is not complete until both live commands pass.
