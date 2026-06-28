# OneOps Redfish Hard-Cut Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `oneops_idrac_exporter` with `oneops_redfish` end-to-end, including agent plugin naming, emitted metric names, Teleabs template support, and OneOps task rendering/distribution.

**Architecture:** The work is split into five slices: rename the agent plugin/package and metric prefix, introduce a first-class `oneops_redfish` Teleabs template, wire OneOps rendering semantics to the new plugin type, switch the Redfish OOB default strategy to the new template, and verify the rendered TOML/downlink contract. This is a hard cut with no alias for `oneops_idrac_exporter` and no dual-write for `idrac_*`.

**Tech Stack:** Go, Telegraf input plugins, Teleabs JSON templates, OneOps monitoring-task pipeline, SQL seed migrations, Go tests.

---

### Task 1: Rename The Agent Plugin Package And Registration

**Files:**
- Rename: `ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_idrac_exporter` -> `ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_redfish`
- Modify: `ctrlhub/controller/agent/cmd/agent/main.go`
- Modify: `ctrlhub/controller/pkg/controller/config/telegraf_plugin_validator.go`
- Rename/Modify: `ctrlhub/controller/test/idrac_preview_server.go` -> `ctrlhub/controller/test/redfish_preview_server.go`
- Test: `ctrlhub/controller/agent/cmd/agent/oob_plugin_capability_test.go`

- [ ] **Step 1: Write the failing registration test update**

Update `ctrlhub/controller/agent/cmd/agent/oob_plugin_capability_test.go` so the expected capability list contains `oneops_redfish` and does not contain `oneops_idrac_exporter`.

```go
for _, want := range []string{"ipmi_sensor", "redfish", "oneops_ipmi", "oneops_ipmi_exporter", "oneops_redfish"} {
    // existing assertion shape
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `go test ./controller/agent/cmd/agent -run TestOOBPluginCapabilities -count=1`

Expected: FAIL because the agent still imports/registers `oneops_idrac_exporter`.

- [ ] **Step 3: Rename the package and update imports**

Make these code changes:

```go
// ctrlhub/controller/agent/cmd/agent/main.go
_ "github.com/netxops/ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_redfish"
```

```go
// ctrlhub/controller/pkg/controller/config/telegraf_plugin_validator.go
_ "github.com/netxops/ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_redfish"
```

```go
// ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_redfish/oneops_redfish.go
package oneops_redfish

func init() {
    inputs.Add("oneops_redfish", func() telegraf.Input {
        return &OneOpsRedfish{ /* existing defaults */ }
    })
}
```

- [ ] **Step 4: Update the preview utility naming**

Rename the preview helper file and imports so it no longer exposes iDRAC branding:

```go
// ctrlhub/controller/test/redfish_preview_server.go
oneopsredfish "github.com/netxops/ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_redfish"
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `go test ./controller/agent/cmd/agent -run TestOOBPluginCapabilities -count=1`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git -C ctrlhub add controller/agent/cmd/agent/main.go \
  controller/pkg/controller/config/telegraf_plugin_validator.go \
  controller/test/redfish_preview_server.go \
  controller/agent/pkg/telegraf/plugins/inputs/oneops_redfish
git -C ctrlhub commit -m "feat: rename custom redfish agent plugin"
```

### Task 2: Switch Emitted Metrics From `idrac_*` To `oneops_redfish_*`

**Files:**
- Modify: `ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_redfish/oneops_redfish.go`
- Modify: `ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_redfish/internal/config/config.go`
- Modify: `ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_redfish/sample.conf`
- Modify/Test: `ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_redfish/oneops_redfish_test.go`

- [ ] **Step 1: Write the failing metric-prefix test**

Update the plugin unit test so it expects the renamed prefix:

```go
measurement, field := splitMetricName("oneops_redfish_system_power_on")
if measurement != "oneops_redfish_system_power" || field != "on" {
    t.Fatalf("unexpected split result: measurement=%s field=%s", measurement, field)
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `go test ./controller/agent/pkg/telegraf/plugins/inputs/oneops_redfish -run TestSplitMetricName -count=1`

Expected: FAIL because the plugin still emits or parses `idrac_*`.

- [ ] **Step 3: Update the metrics prefix and sample config**

Change the internal defaults:

```go
// internal/config/config.go
MetricsPrefix: "oneops_redfish",
```

```go
// oneops_redfish.go
cfg.MetricsPrefix = "oneops_redfish"
```

```toml
[[inputs.oneops_redfish]]
  timeout = "30s"
  event_max_age = "168h"
  event_severity = "warning"
  collectors = ["system", "sensors", "power", "storage", "memory", "network", "processors", "manager", "events", "extra"]
  servers = ["root:calvin@https(192.168.10.206:443)"]
```

- [ ] **Step 4: Run focused plugin tests**

Run: `go test ./controller/agent/pkg/telegraf/plugins/inputs/oneops_redfish -count=1`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C ctrlhub add controller/agent/pkg/telegraf/plugins/inputs/oneops_redfish
git -C ctrlhub commit -m "feat: rename custom redfish metric prefix"
```

### Task 3: Add A First-Class `oneops-redfish-basic` Teleabs Template

**Files:**
- Create: `teleabs/teleabs-templates/categories/infrastructure/server/oob/oneops_redfish_basic.json`
- Modify: `teleabs/teleabs-templates/config/template-registry.json`
- Modify/Test: `teleabs/stable_template_render_test.go`
- Modify/Test: `teleabs/template_system_test.go`

- [ ] **Step 1: Write the failing Teleabs render test**

Add or update a stable-render test that expects `plugin_type = "oneops_redfish"` to render `[[inputs.oneops_redfish]]`.

```go
{
    name:       "oneops_redfish",
    templateID: "oneops-redfish-basic",
    pluginType: "oneops_redfish",
    wantContains: []string{
        "[[inputs.oneops_redfish]]",
        `timeout = "30s"`,
    },
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `go test . -run 'TestStableTemplateRender|TestTemplateFileSystemIntegration_OneOpsAndProcessorTemplates' -count=1`

Expected: FAIL because the template does not exist yet.

- [ ] **Step 3: Add the new template and registry entry**

Create `oneops_redfish_basic.json` with the new contract:

```json
{
  "id": "oneops-redfish-basic",
  "plugin_type": "oneops_redfish",
  "layer": "basic",
  "collection_scope": "remote",
  "target_kind": "ip",
  "target_extraction": {
    "param_key": "address",
    "override_key": "address",
    "address_parser": "url",
    "value_format": "redfish_url",
    "require_host": true
  },
  "template": "[[inputs.oneops_redfish]]\n  address = \"{{.address}}\"\n  username = \"{{.username}}\"\n  password = \"{{.password}}\"\n  collectors = {{.collectors | toTomlArray}}\n  timeout = \"{{.timeout | default \"30s\"}}\"\n  interval = \"{{.interval | default \"60s\"}}\""
}
```

Add `produces_metrics` entries that use `oneops_redfish_*`.

- [ ] **Step 4: Run Teleabs package tests**

Run: `go test . -count=1`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C teleabs add teleabs-templates/categories/infrastructure/server/oob/oneops_redfish_basic.json \
  teleabs-templates/config/template-registry.json \
  stable_template_render_test.go template_system_test.go
git -C teleabs commit -m "feat: add oneops redfish teleabs template"
```

### Task 4: Wire OneOps Rendering Semantics And Target Extraction For `oneops_redfish`

**Files:**
- Modify: `OneOps/app/platform/service/impl/monitoring_task_v3_apply_semantics.go`
- Modify/Test: `OneOps/app/platform/service/impl/monitoring_task_v3_apply_semantics_test.go`
- Modify: `OneOps/app/platform/service/impl/monitoring_task_v3_target_resolver_registry.go`
- Modify: `OneOps/app/platform/service/impl/telegraf_config_generator_impl.go`
- Modify/Test: `OneOps/app/platform/service/impl/telegraf_config_generator_impl_test.go`
- Modify/Test: `OneOps/app/platform/service/impl/teleabs_template_provider_exec_test.go`
- Modify: `OneOps/app/platform/service/impl/teleabs_template_produces.go`

- [ ] **Step 1: Write the failing OneOps semantics test**

Extend the semantics test tables so `oneops_redfish` is recognized as remote Redfish:

```go
{"oneops_redfish", constants.CredentialUsageTelegrafRedfish, 443, constants.CollectionTypeRedfish},
```

- [ ] **Step 2: Run the semantics test to verify it fails**

Run: `go test ./app/platform/service/impl -run 'TestMonitoringV2ApplySemantics|TestMonitoringV2CredentialUsage' -count=1`

Expected: FAIL because `oneops_redfish` is not yet registered.

- [ ] **Step 3: Register plugin semantics and target extraction**

Make the minimal logic changes:

```go
// monitoring_task_v3_apply_semantics.go
register(monitoringV2PluginSemantics{
    CredentialUsage:        constants.CredentialUsageTelegrafRedfish,
    DefaultPort:            443,
    DefaultCollectionType:  constants.CollectionTypeRedfish,
    DefaultCollectionScope: constants.CollectionScopeRemote,
    DefaultTargetKind:      constants.TargetKindIP,
}, "redfish", "oneops_redfish")
```

```go
// telegraf_config_generator_impl.go
case "redfish", "oneops_redfish":
    return &dto.TeleabsTemplateTargetExtraction{
        ParamKey: "address", OverrideKey: "address",
        AddressParser: "url", ValueFormat: "redfish_url", RequireHost: true,
    }
```

Update any template-provider/produces bookkeeping so `oneops_redfish` is recognized as a producer.

- [ ] **Step 4: Add the config-generation regression test**

Add an assertion that the generated TOML contains the custom plugin name:

```go
require.Contains(t, toml, "[[inputs.oneops_redfish]]")
require.NotContains(t, toml, "[[inputs.oneops_idrac_exporter]]")
```

- [ ] **Step 5: Run focused OneOps tests**

Run: `go test ./app/platform/service/impl -run 'TestMonitoringV2ApplySemantics|TestMonitoringV2CredentialUsage|TestTelegrafConfigGenerator' -count=1`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git -C OneOps add app/platform/service/impl/monitoring_task_v3_apply_semantics.go \
  app/platform/service/impl/monitoring_task_v3_apply_semantics_test.go \
  app/platform/service/impl/monitoring_task_v3_target_resolver_registry.go \
  app/platform/service/impl/telegraf_config_generator_impl.go \
  app/platform/service/impl/telegraf_config_generator_impl_test.go \
  app/platform/service/impl/teleabs_template_provider_exec_test.go \
  app/platform/service/impl/teleabs_template_produces.go
git -C OneOps commit -m "feat: wire oneops redfish rendering semantics"
```

### Task 5: Switch The Redfish OOB Seed And Downlink Contract

**Files:**
- Modify: `OneOps/migrations/seed_server_oob_redfish_strategy_set.sql`
- Modify/Test: `OneOps/app/platform/service/impl/server_oob_redfish_seed_test.go`
- Modify/Test: `OneOps/app/platform/service/impl/metric_strategy_quick_apply_service_test.go`
- Modify/Test: `OneOps/app/platform/service/impl/monitoring_task_v3_services_test.go`
- Modify/Test: `OneOps/app/platform/api/metric_strategy_quick_apply_test.go`

- [ ] **Step 1: Write the failing seed assertion**

Change the seed test to expect `oneops-redfish-basic` instead of `redfish-passthrough`.

```go
for _, needle := range []string{
    "server_oob_redfish_strategy",
    "server_oob_redfish",
    "oneops-redfish-basic",
} {
    // existing assertion shape
}
```

- [ ] **Step 2: Run the seed test to verify it fails**

Run: `go test ./app/platform/service/impl -run TestServerOOBRedfishSeed -count=1`

Expected: FAIL because the SQL seed still points to `redfish-passthrough`.

- [ ] **Step 3: Update the seed and downstream expectations**

Modify the SQL seed so the strategy references the new template id:

```sql
-- seed_server_oob_redfish_strategy_set.sql
teleabs_template_id = 'oneops-redfish-basic'
```

Update quick-apply and service tests so the final rendered task is validated as:

```go
require.Contains(t, toml, "[[inputs.oneops_redfish]]")
```

- [ ] **Step 4: Run focused Redfish OOB tests**

Run: `go test ./app/platform/service/impl -run 'TestServerOOBRedfishSeed|TestMetricStrategyQuickApply|TestMonitoringTaskV3Services' -count=1`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C OneOps add migrations/seed_server_oob_redfish_strategy_set.sql \
  app/platform/service/impl/server_oob_redfish_seed_test.go \
  app/platform/service/impl/metric_strategy_quick_apply_service_test.go \
  app/platform/service/impl/monitoring_task_v3_services_test.go \
  app/platform/api/metric_strategy_quick_apply_test.go
git -C OneOps commit -m "feat: switch redfish oob seed to oneops redfish"
```

### Task 6: End-To-End Verification

**Files:**
- Verify only; no code changes required unless failures expose gaps.

- [ ] **Step 1: Run agent verification**

Run: `go test ./controller/agent/cmd/agent ./controller/agent/pkg/telegraf/plugins/inputs/oneops_redfish -count=1`

Expected: PASS

- [ ] **Step 2: Run Teleabs verification**

Run: `go test . -count=1`

Working directory: `teleabs`

Expected: PASS

- [ ] **Step 3: Run OneOps focused verification**

Run: `go test ./app/platform/service/impl ./app/platform/api -run 'Redfish|oneops_redfish|TelegrafConfigGenerator|ApplySemantics' -count=1`

Working directory: `OneOps`

Expected: PASS

- [ ] **Step 4: Spot-check final contracts**

Verify by search:

```bash
rg -n "oneops_idrac_exporter|\\[\\[inputs\\.oneops_idrac_exporter\\]\\]|idrac_" ctrlhub OneOps teleabs
```

Expected: no runtime references remain except intentionally updated historical docs/tests if any are explicitly accepted.

- [ ] **Step 5: Final commit or squash note**

```bash
git -C ctrlhub log --oneline -3
git -C teleabs log --oneline -3
git -C OneOps log --oneline -3
```

If all verification passes, prepare the branch/PR summary with:

- agent plugin rename complete
- Teleabs `oneops-redfish-basic` active
- OneOps `server_oob_redfish` now renders `[[inputs.oneops_redfish]]`
