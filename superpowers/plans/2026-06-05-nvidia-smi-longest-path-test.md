# Nvidia SMI Longest Path Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Telegraf `nvidia_smi` support so OneOps can expose a Teleabs NVIDIA SMI template, compile/apply a platform monitoring task, push it to ctrlhub agent, and verify on the agent that the task is correct and fails gathering through a deterministic missing `nvidia-smi` binary.

**Architecture:** Teleabs owns the embedded `nvidia-smi-basic` template and render contract, ctrlhub agent owns Telegraf plugin registration and agent task execution, and OneOps consumes Teleabs `v0.0.26` to make the template visible to strategy/apply flows. The longest-path test uses platform compile/apply plus agent runtime query; Prometheus is deliberately out of scope.

**Tech Stack:** Go, Telegraf `github.com/influxdata/telegraf v1.37.0`, Teleabs embedded templates, ctrlhub bidi agent, OneOps Monitoring V2 APIs, Git tag `v0.0.26`.

---

## File Structure

- Create `/OneOPS/teleabs/nvidia_smi_render_test.go`: locks Teleabs embedded template loading, metadata, and rendered TOML for `nvidia-smi-basic`.
- Create `/OneOPS/teleabs/teleabs-templates/categories/infrastructure/system/nvidia_smi/nvidia_smi_basic.json`: Teleabs basic local/system NVIDIA SMI template.
- Modify `/OneOPS/ctrlhub/controller/agent/cmd/agent/main.go`: blank import Telegraf `inputs/nvidia_smi` and add `nvidia_smi` to `SupportedTelegrafPluginsForTeleabs`.
- Create `/OneOPS/ctrlhub/controller/agent/cmd/agent/nvidia_smi_plugin_test.go`: verifies the production agent package registers and advertises `nvidia_smi`.
- Modify `/OneOPS/ctrlhub/controller/agent/app/telegraf_task_manager_test.go`: verifies the agent task manager stores the exact NVIDIA SMI task data and produces a gather error with `/tmp/oneops-nvidia-smi-missing`.
- Modify `/OneOPS/OneOps/go.mod`: update `github.com/netxops/teleabs` from the existing version to `v0.0.26`, preserving unrelated user edits already present in the file.
- Modify `/OneOPS/OneOps/go.sum`: update module checksums caused by `go get github.com/netxops/teleabs@v0.0.26`, preserving unrelated user edits already present in the file.
- Modify `/OneOPS/OneOps/app/platform/service/impl/teleabs_template_provider_exec_test.go`: adds an embedded-template provider test proving OneOps can see `nvidia-smi-basic`.

## Task 1: Teleabs Red Test For NVIDIA SMI Template

**Files:**
- Create: `/OneOPS/teleabs/nvidia_smi_render_test.go`

- [ ] **Step 1: Write the failing Teleabs render test**

Add this file:

```go
package teleabs

import (
	"strings"
	"testing"
)

func TestNvidiaSMIBasicTemplateRendersBinPathTimeoutAndInterval(t *testing.T) {
	registry := NewTemplateRegistry("")
	defer registry.Close()
	if err := registry.LoadTemplates(); err != nil {
		t.Fatalf("LoadTemplates failed: %v", err)
	}

	tpl := registry.GetTemplateByID("nvidia-smi-basic")
	if tpl == nil {
		t.Fatalf("expected nvidia-smi-basic template to be embedded")
	}
	if tpl.PluginType != "nvidia_smi" {
		t.Fatalf("expected plugin type nvidia_smi, got %s", tpl.PluginType)
	}
	if tpl.CollectionScope != "local" {
		t.Fatalf("expected collection_scope local, got %s", tpl.CollectionScope)
	}
	if tpl.TargetKind != "system" {
		t.Fatalf("expected target_kind system, got %s", tpl.TargetKind)
	}

	generator := NewConfigGenerator(registry)
	task := &MonitoringTask{
		ID:   "task-nvidia-smi",
		Name: "NVIDIA SMI longest path probe",
		Targets: []MonitoringTarget{
			{
				ID:   "local-system",
				Name: "local system",
				Type: "server",
				Plugins: []PluginConfig{
					{
						TemplateID: "nvidia-smi-basic",
						PluginType: "nvidia_smi",
						Layer:      BasicAbstraction,
						Config: map[string]interface{}{
							"bin_path": "/tmp/oneops-nvidia-smi-missing",
							"timeout":  "1s",
							"interval": "10s",
						},
					},
				},
			},
		},
	}

	cfg, err := generator.GenerateTelegrafConfig(task)
	if err != nil {
		t.Fatalf("GenerateTelegrafConfig failed: %v", err)
	}
	toml := generator.ExportToTOML(cfg)

	for _, want := range []string{
		"[[inputs.nvidia_smi]]",
		`bin_path = "/tmp/oneops-nvidia-smi-missing"`,
		`timeout = "1s"`,
		`interval = "10s"`,
	} {
		if !strings.Contains(toml, want) {
			t.Fatalf("expected TOML to contain %q, got:\n%s", want, toml)
		}
	}
}
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
cd /OneOPS/teleabs
go test . -run TestNvidiaSMIBasicTemplateRendersBinPathTimeoutAndInterval -count=1
```

Expected: FAIL with `expected nvidia-smi-basic template to be embedded`.

## Task 2: Add Teleabs NVIDIA SMI Template

**Files:**
- Create: `/OneOPS/teleabs/teleabs-templates/categories/infrastructure/system/nvidia_smi/nvidia_smi_basic.json`
- Test: `/OneOPS/teleabs/nvidia_smi_render_test.go`

- [ ] **Step 1: Add the embedded template JSON**

Create `/OneOPS/teleabs/teleabs-templates/categories/infrastructure/system/nvidia_smi/nvidia_smi_basic.json` with this content:

```json
{
  "complexity_level": "low",
  "created_at": "2026-06-05T00:00:00Z",
  "description": "NVIDIA GPU 基础监控，基于 Telegraf nvidia_smi 插件采集本机 GPU 利用率、显存、功耗、温度和驱动信息",
  "id": "nvidia-smi-basic",
  "is_active": true,
  "layer": "basic",
  "name": "NVIDIA SMI 基础监控",
  "parameters": [
    {
      "name": "bin_path",
      "type": "string",
      "required": false,
      "default_value": "/usr/bin/nvidia-smi",
      "description": "nvidia-smi 可执行文件路径；最长链路测试可设置为 /tmp/oneops-nvidia-smi-missing 以稳定触发采集失败",
      "source": "technical"
    },
    {
      "name": "timeout",
      "type": "string",
      "required": false,
      "default_value": "5s",
      "description": "GPU 查询超时时间",
      "validation": "pattern:^\\d+(ns|us|ms|s|m|h)$",
      "source": "technical"
    },
    {
      "name": "interval",
      "type": "string",
      "required": false,
      "default_value": "60s",
      "description": "数据收集间隔",
      "validation": "pattern:^\\d+(ns|us|ms|s|m|h)$",
      "source": "technical"
    }
  ],
  "plugin_type": "nvidia_smi",
  "template": "# Generated by Teleabs Template Engine v1.0\n# Template: nvidia_smi_basic v1.0.0\n\n[[inputs.nvidia_smi]]\n  ## Optional path to nvidia-smi binary\n  bin_path = \"{{.bin_path | default \"/usr/bin/nvidia-smi\"}}\"\n  ## Optional timeout for GPU polling\n  timeout = \"{{.timeout | default \"5s\"}}\"\n  ## Collection interval\n  interval = \"{{.interval | default \"60s\"}}\"",
  "updated_at": "2026-06-05T00:00:00Z",
  "validation_rules": [
    {
      "name": "timeout_format_validation",
      "condition": "timeout matches ^\\d+(ns|us|ms|s|m|h)$",
      "error_message": "timeout 格式无效，应为时间间隔如 5s、1m",
      "severity": "error"
    },
    {
      "name": "interval_format_validation",
      "condition": "interval matches ^\\d+(ns|us|ms|s|m|h)$",
      "error_message": "interval 格式无效，应为时间间隔如 60s、5m",
      "severity": "error"
    }
  ],
  "version": "1.0.0",
  "collection_scope": "local",
  "target_kind": "system",
  "produces_metrics": [
    {
      "measurement": "nvidia_smi",
      "field": "utilization_gpu",
      "prometheus_name": "nvidia_smi_utilization_gpu"
    },
    {
      "measurement": "nvidia_smi",
      "field": "utilization_memory",
      "prometheus_name": "nvidia_smi_utilization_memory"
    },
    {
      "measurement": "nvidia_smi",
      "field": "temperature_gpu",
      "prometheus_name": "nvidia_smi_temperature_gpu"
    },
    {
      "measurement": "nvidia_smi",
      "field": "memory_used",
      "prometheus_name": "nvidia_smi_memory_used"
    },
    {
      "measurement": "nvidia_smi",
      "field": "memory_total",
      "prometheus_name": "nvidia_smi_memory_total"
    },
    {
      "measurement": "nvidia_smi",
      "field": "memory_free",
      "prometheus_name": "nvidia_smi_memory_free"
    },
    {
      "measurement": "nvidia_smi",
      "field": "power_draw",
      "prometheus_name": "nvidia_smi_power_draw"
    },
    {
      "measurement": "nvidia_smi",
      "field": "driver_version",
      "prometheus_name": "nvidia_smi_driver_version"
    },
    {
      "measurement": "nvidia_smi",
      "field": "cuda_version",
      "prometheus_name": "nvidia_smi_cuda_version"
    }
  ]
}
```

- [ ] **Step 2: Run the focused Teleabs test**

Run:

```bash
cd /OneOPS/teleabs
go test . -run TestNvidiaSMIBasicTemplateRendersBinPathTimeoutAndInterval -count=1
```

Expected: PASS.

- [ ] **Step 3: Run Teleabs package tests**

Run:

```bash
cd /OneOPS/teleabs
go test ./... -count=1
```

Expected: PASS.

## Task 3: Commit, Tag, And Push Teleabs v0.0.26

**Files:**
- Commit: `/OneOPS/teleabs/nvidia_smi_render_test.go`
- Commit: `/OneOPS/teleabs/teleabs-templates/categories/infrastructure/system/nvidia_smi/nvidia_smi_basic.json`

- [ ] **Step 1: Confirm remote tag is free**

Run:

```bash
cd /OneOPS/teleabs
git ls-remote --tags origin refs/tags/v0.0.26
```

Expected: no output. If output exists for `refs/tags/v0.0.26`, stop because the requested tag already exists remotely.

- [ ] **Step 2: Commit Teleabs changes**

Run:

```bash
cd /OneOPS/teleabs
git status --short
git add nvidia_smi_render_test.go teleabs-templates/categories/infrastructure/system/nvidia_smi/nvidia_smi_basic.json
git commit -m "feat: add nvidia smi teleabs template"
```

Expected: a commit is created on Teleabs `main` with only the NVIDIA SMI test and template.

- [ ] **Step 3: Tag and push**

Run:

```bash
cd /OneOPS/teleabs
git tag v0.0.26
git push origin main
git push origin v0.0.26
git ls-remote --tags origin refs/tags/v0.0.26
```

Expected: final command prints a line ending in `refs/tags/v0.0.26`.

## Task 4: ctrlhub Agent Registers And Executes NVIDIA SMI

**Files:**
- Create: `/OneOPS/ctrlhub/controller/agent/cmd/agent/nvidia_smi_plugin_test.go`
- Modify: `/OneOPS/ctrlhub/controller/agent/cmd/agent/main.go`
- Modify: `/OneOPS/ctrlhub/controller/agent/app/telegraf_task_manager_test.go`

- [ ] **Step 1: Write failing production-registration tests**

Create `/OneOPS/ctrlhub/controller/agent/cmd/agent/nvidia_smi_plugin_test.go`:

```go
package main

import (
	"strings"
	"testing"

	telegrafconfig "github.com/influxdata/telegraf/config"
)

func TestSupportedTelegrafPluginsForTeleabsIncludesNvidiaSMI(t *testing.T) {
	for _, plugin := range SupportedTelegrafPluginsForTeleabs {
		if plugin == "nvidia_smi" {
			return
		}
	}
	t.Fatalf("expected SupportedTelegrafPluginsForTeleabs to include nvidia_smi, got %#v", SupportedTelegrafPluginsForTeleabs)
}

func TestAgentProductionPackageParsesNvidiaSMIInput(t *testing.T) {
	cfg := telegrafconfig.NewConfig()
	err := cfg.LoadConfigData([]byte(strings.Join([]string{
		"[[inputs.nvidia_smi]]",
		`  bin_path = "/tmp/oneops-nvidia-smi-missing"`,
		`  timeout = "1s"`,
		`  interval = "10s"`,
	}, "\n")), "nvidia_smi_test.conf")
	if err != nil {
		t.Fatalf("expected production agent package to register nvidia_smi input: %v", err)
	}
	if len(cfg.Inputs) != 1 {
		t.Fatalf("expected one parsed input, got %d", len(cfg.Inputs))
	}
}
```

- [ ] **Step 2: Run production-registration tests and verify failure**

Run:

```bash
cd /OneOPS/ctrlhub
go test ./controller/agent/cmd/agent -run 'TestSupportedTelegrafPluginsForTeleabsIncludesNvidiaSMI|TestAgentProductionPackageParsesNvidiaSMIInput' -count=1
```

Expected: FAIL. One assertion should report missing `nvidia_smi`, and config parsing should fail before the blank import is added.

- [ ] **Step 3: Register NVIDIA SMI in agent main package**

In `/OneOPS/ctrlhub/controller/agent/cmd/agent/main.go`, add the Telegraf input import near the other input plugin blank imports:

```go
	_ "github.com/influxdata/telegraf/plugins/inputs/nvidia_smi"
```

Update `SupportedTelegrafPluginsForTeleabs` so the list contains `nvidia_smi`; keep the list sorted by the nearby Telegraf plugin grouping:

```go
var SupportedTelegrafPluginsForTeleabs = []string{
	"cloudwatch", "cpu", "ctrlx_datalayer", "disk", "docker", "exec", "http", "jolokia2_agent", "kafka_consumer",
	"mem", "mysql", "net", "net_response", "nginx", "nvidia_smi", "oneops_nvr_status", "opcua", "opcua_listener", "ping", "postgresql",
	"procstat", "prometheus", "rabbitmq", "redis", "redfish", "ipmi_sensor", "snmp", "snmp_trap", "sqlserver", "statsd", "syslog", "system", "tail", "vsphere",
}
```

- [ ] **Step 4: Run production-registration tests and verify pass**

Run:

```bash
cd /OneOPS/ctrlhub
go test ./controller/agent/cmd/agent -run 'TestSupportedTelegrafPluginsForTeleabsIncludesNvidiaSMI|TestAgentProductionPackageParsesNvidiaSMIInput' -count=1
```

Expected: PASS.

- [ ] **Step 5: Write agent task-manager test for task data and deterministic gather failure**

In `/OneOPS/ctrlhub/controller/agent/app/telegraf_task_manager_test.go`, add the blank test import with the other input plugins:

```go
	_ "github.com/influxdata/telegraf/plugins/inputs/nvidia_smi"
```

Add this test near `TestApplyTask_WithRedfishConfigStoresTask`:

```go
func TestApplyTask_WithNvidiaSMIConfigStoresTaskAndGatherFails(t *testing.T) {
	logger := zap.NewNop()
	collector, err := metrics.NewTelegrafInputCollector(
		logger,
		[]string{"nvidia_smi"},
		5*time.Second,
		nil,
	)
	if err != nil {
		t.Fatalf("create collector failed: %v", err)
	}
	defer collector.Stop()

	manager := NewTelegrafTaskManager(logger, collector, "")
	tomlConfig := `
[[inputs.nvidia_smi]]
  bin_path = "/tmp/oneops-nvidia-smi-missing"
  timeout = "1s"
  interval = "10s"
`
	if err := manager.ApplyTask("task-nvidia-smi", tomlConfig, "v1", nil); err != nil {
		t.Fatalf("ApplyTask failed: %v", err)
	}

	info, ok := manager.GetTask("task-nvidia-smi")
	if !ok {
		t.Fatalf("expected GetTask found=true")
	}
	if !reflect.DeepEqual(info.PluginsInput, []string{"nvidia_smi"}) {
		t.Fatalf("unexpected input plugins: %#v", info.PluginsInput)
	}
	if !strings.Contains(info.Config, `[[inputs.nvidia_smi]]`) ||
		!strings.Contains(info.Config, `bin_path = "/tmp/oneops-nvidia-smi-missing"`) ||
		!strings.Contains(info.Config, `timeout = "1s"`) ||
		!strings.Contains(info.Config, `interval = "10s"`) {
		t.Fatalf("stored task config missing expected nvidia_smi data:\n%s", info.Config)
	}

	manager.mu.RLock()
	state := manager.tasks["task-nvidia-smi"]
	manager.mu.RUnlock()
	if state == nil || len(state.Inputs) == 0 {
		t.Fatalf("expected stored nvidia_smi input state")
	}
	var inputErr error
	for _, input := range state.Inputs {
		inputErr = input.Gather(nil)
		break
	}
	if inputErr == nil {
		t.Fatalf("expected nvidia_smi gather to fail for missing bin_path")
	}
}
```

- [ ] **Step 6: Run focused task-manager test**

Run:

```bash
cd /OneOPS/ctrlhub
go test ./controller/agent/app -run TestApplyTask_WithNvidiaSMIConfigStoresTaskAndGatherFails -count=1
```

Expected: PASS, and the test confirms task data correctness plus execution failure without Prometheus.

- [ ] **Step 7: Run ctrlhub agent package tests**

Run:

```bash
cd /OneOPS/ctrlhub
go test ./controller/agent/cmd/agent ./controller/agent/app -count=1
```

Expected: PASS.

- [ ] **Step 8: Commit ctrlhub changes**

Run:

```bash
cd /OneOPS/ctrlhub
git status --short
git add controller/agent/cmd/agent/main.go controller/agent/cmd/agent/nvidia_smi_plugin_test.go controller/agent/app/telegraf_task_manager_test.go
git commit -m "feat: register nvidia smi telegraf input"
```

Expected: a ctrlhub commit containing only NVIDIA SMI registration and tests.

## Task 5: OneOps Consumes Teleabs v0.0.26 And Exposes Template

**Files:**
- Modify: `/OneOPS/OneOps/go.mod`
- Modify: `/OneOPS/OneOps/go.sum`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/teleabs_template_provider_exec_test.go`

- [ ] **Step 1: Write failing OneOps provider test**

Append this test to `/OneOPS/OneOps/app/platform/service/impl/teleabs_template_provider_exec_test.go`:

```go
func TestTeleabsTemplateProvider_NvidiaSMIBasicVisibleInStrategyUI(t *testing.T) {
	provider := NewTeleabsTemplateProvider(zap.NewNop(), &config.Config{})

	tpl, err := provider.GetTemplateByID(context.Background(), "nvidia-smi-basic")
	if err != nil {
		t.Fatalf("GetTemplateByID failed: %v", err)
	}
	if tpl == nil {
		t.Fatalf("expected nvidia-smi-basic template")
	}
	if tpl.PluginType != "nvidia_smi" {
		t.Fatalf("expected plugin type nvidia_smi, got %s", tpl.PluginType)
	}
	if tpl.CollectionScope != "local" {
		t.Fatalf("expected collection scope local, got %s", tpl.CollectionScope)
	}
	if tpl.TargetKind != "system" {
		t.Fatalf("expected target kind system, got %s", tpl.TargetKind)
	}

	requiredParams := map[string]bool{
		"bin_path": false,
		"timeout":  false,
		"interval": false,
	}
	for _, param := range tpl.Parameters {
		if _, ok := requiredParams[param.Name]; ok {
			requiredParams[param.Name] = true
		}
	}
	for name, seen := range requiredParams {
		if !seen {
			t.Fatalf("expected parameter %s to be visible in strategy UI template", name)
		}
	}
}
```

- [ ] **Step 2: Run provider test and verify failure before dependency update**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestTeleabsTemplateProvider_NvidiaSMIBasicVisibleInStrategyUI -count=1
```

Expected: FAIL because the current OneOps Teleabs module does not yet contain `nvidia-smi-basic`.

- [ ] **Step 3: Update OneOps Teleabs dependency to v0.0.26**

Run:

```bash
cd /OneOPS/OneOps
go get github.com/netxops/teleabs@v0.0.26
```

Expected: `/OneOPS/OneOps/go.mod` contains:

```go
github.com/netxops/teleabs v0.0.26
```

Also inspect the diff so pre-existing user edits in `go.mod` and `go.sum` remain intact:

```bash
cd /OneOPS/OneOps
git diff -- go.mod go.sum
```

- [ ] **Step 4: Run provider test and verify pass**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestTeleabsTemplateProvider_NvidiaSMIBasicVisibleInStrategyUI -count=1
```

Expected: PASS.

- [ ] **Step 5: Run focused OneOps strategy/template tests**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestTeleabsTemplateProvider_ExecPassthrough|TestTeleabsTemplateProvider_NvidiaSMIBasicVisibleInStrategyUI|TestStrategyApply' -count=1
```

Expected: PASS, or known unrelated failures must be recorded with the exact failing test names and error messages.

## Task 6: Longest-Path Runtime Verification Without Prometheus

**Files:**
- No required code changes after Tasks 1-5.
- Optional artifact: `/OneOPS/artifacts/probe-results/nvidia-smi-longest-path-20260605.md`

- [ ] **Step 1: Rebuild or restart the ctrlhub agent with the new import**

Use the local deployment method already used for the test environment. The important invariant is that the running agent binary includes `/OneOPS/ctrlhub/controller/agent/cmd/agent/main.go` after the `nvidia_smi` blank import.

Verify capability registration through logs or controller capability output. The agent capability list must contain:

```text
nvidia_smi
```

- [ ] **Step 2: Compile a platform plan with NVIDIA SMI template**

Set shell variables for the live OneOps endpoint and a real agent already connected to ctrlhub:

```bash
export ONEOPS_BASE_URL="http://127.0.0.1:8080"
export TENANT_ID="tenant-a"
export AGENT_CODE="agent-with-ctrlhub-connection"
export ENTITY_ID="nvidia-smi-longest-path-local"
```

Run:

```bash
curl -sS -X POST "$ONEOPS_BASE_URL/api/v2/platform/monitoring/plans:compile" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT_ID" \
  -d '{
    "selection_spec": {
      "source_type": "manual",
      "entity_type": "device",
      "selector": {
        "entity_id": "'"$ENTITY_ID"'"
      }
    },
    "resolved_targets": [
      {
        "target_uid": "device:'"$ENTITY_ID"'",
        "entity_type": "device",
        "entity_id": "'"$ENTITY_ID"'",
        "agent_code": "'"$AGENT_CODE"'",
        "metadata": {
          "agent_code": "'"$AGENT_CODE"'",
          "collection_scope": "local",
          "target_kind": "system"
        }
      }
    ],
    "strategy_intent": {
      "template_id": "nvidia-smi-basic",
      "plugin_type": "nvidia_smi",
      "target_kind": "system",
      "params": {
        "bin_path": "/tmp/oneops-nvidia-smi-missing",
        "timeout": "1s",
        "interval": "10s"
      }
    }
  }' | tee /tmp/oneops-nvidia-smi-compile.json
```

Expected: response data contains a non-empty `plan_id` and no error code.

- [ ] **Step 3: Apply the plan and sync runtime snapshot**

Extract the `plan_id` and apply it:

```bash
export PLAN_ID="$(jq -r '.data.plan_id // .plan_id' /tmp/oneops-nvidia-smi-compile.json)"
curl -sS -X POST "$ONEOPS_BASE_URL/api/v2/platform/monitoring/plans/$PLAN_ID:apply" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT_ID" \
  -d '{
    "request_id": "nvidia-smi-longest-path-20260605",
    "apply_options": {
      "sync_agent_snapshot": true
    }
  }' | tee /tmp/oneops-nvidia-smi-apply.json
```

Expected: response data contains a non-empty `apply_id` and at least one task operation for `$AGENT_CODE`.

- [ ] **Step 4: Identify runtime task ID and projection ID**

Run:

```bash
export TASK_ID="$(jq -r --arg agent "$AGENT_CODE" '.data.task_operations[]? | select((.agent_code // .AgentCode) == $agent) | (.task_id // .TaskID)' /tmp/oneops-nvidia-smi-apply.json | head -n 1)"
export PROJECTION_ID="$AGENT_CODE:$TASK_ID"
printf 'TASK_ID=%s\nPROJECTION_ID=%s\n' "$TASK_ID" "$PROJECTION_ID"
```

Expected: `TASK_ID` is non-empty. For a local/system task it should include `template_nvidia-smi-basic` or otherwise be associated with the `nvidia-smi-basic` template in the apply response.

- [ ] **Step 5: Query runtime until the agent reports task data and failure**

Run this loop:

```bash
for i in $(seq 1 12); do
  curl -sS "$ONEOPS_BASE_URL/api/v2/platform/monitoring/tasks/$PROJECTION_ID/runtime" \
    -H "X-Tenant-ID: $TENANT_ID" | tee /tmp/oneops-nvidia-smi-runtime.json
  status="$(jq -r '.data.status // .status // empty' /tmp/oneops-nvidia-smi-runtime.json)"
  found="$(jq -r '.data.found // .found // empty' /tmp/oneops-nvidia-smi-runtime.json)"
  inputs="$(jq -r '(.data.plugins_input // .plugins_input // []) | join(",")' /tmp/oneops-nvidia-smi-runtime.json)"
  message="$(jq -r '.data.message // .message // empty' /tmp/oneops-nvidia-smi-runtime.json)"
  printf 'attempt=%s found=%s status=%s inputs=%s message=%s\n' "$i" "$found" "$status" "$inputs" "$message"
  if [ "$found" = "true" ] && [ "$status" = "failed" ] && printf '%s' "$inputs" | grep -q 'nvidia_smi'; then
    break
  fi
  sleep 10
done
```

Expected final runtime response:

```text
found=true
plugins_input contains nvidia_smi
status=failed
message mentions missing /tmp/oneops-nvidia-smi-missing or nvidia-smi lookup failure
inputs contains a task-prefixed nvidia_smi input with ok=false
```

- [ ] **Step 6: Confirm task data correctness on agent**

Use either the platform runtime response or direct ctrlhub controller call available in the environment. The agent task must contain these exact values:

```toml
[[inputs.nvidia_smi]]
  bin_path = "/tmp/oneops-nvidia-smi-missing"
  timeout = "1s"
  interval = "10s"
```

Also confirm `plugins_input` is:

```json
["nvidia_smi"]
```

- [ ] **Step 7: Record probe result**

Create `/OneOPS/artifacts/probe-results/nvidia-smi-longest-path-20260605.md` containing:

````markdown
# NVIDIA SMI Longest Path Probe - 2026-06-05

## Scope

- Platform compile/apply: verified
- ctrlhub push to agent: verified
- Agent task data: verified
- Agent gather failure: verified
- Prometheus validation: skipped by design

## Runtime Evidence

- agent_code:
- task_id:
- projection_id:
- plugins_input: ["nvidia_smi"]
- status: failed
- failure message:
- config excerpt:

```toml
[[inputs.nvidia_smi]]
  bin_path = "/tmp/oneops-nvidia-smi-missing"
  timeout = "1s"
  interval = "10s"
```
````

## Task 7: Final Verification And Change Accounting

**Files:**
- Inspect all touched files across Teleabs, ctrlhub, OneOps, and docs.

- [ ] **Step 1: Run final focused test commands**

Run:

```bash
cd /OneOPS/teleabs
go test . -run TestNvidiaSMIBasicTemplateRendersBinPathTimeoutAndInterval -count=1
```

Run:

```bash
cd /OneOPS/ctrlhub
go test ./controller/agent/cmd/agent ./controller/agent/app -run 'TestSupportedTelegrafPluginsForTeleabsIncludesNvidiaSMI|TestAgentProductionPackageParsesNvidiaSMIInput|TestApplyTask_WithNvidiaSMIConfigStoresTaskAndGatherFails' -count=1
```

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestTeleabsTemplateProvider_NvidiaSMIBasicVisibleInStrategyUI -count=1
```

Expected: all focused tests PASS.

- [ ] **Step 2: Inspect git status in each repo**

Run:

```bash
git -C /OneOPS/teleabs status --short
git -C /OneOPS/ctrlhub status --short
git -C /OneOPS/OneOps status --short
git -C /OneOPS/docs status --short
```

Expected:

- Teleabs has no uncommitted NVIDIA SMI changes after pushing `v0.0.26`.
- ctrlhub has no uncommitted NVIDIA SMI changes after its commit, unless the user wants it left uncommitted.
- OneOps may remain dirty because it had pre-existing user edits; the final report must list only our changes to `go.mod`, `go.sum`, and the provider test.
- docs may contain unrelated existing changes; only this plan and the earlier NVIDIA SMI spec should be attributed to this work.

- [ ] **Step 3: Report final outcome**

Final report must include:

- Teleabs commit hash and remote tag `v0.0.26`.
- ctrlhub commit hash, or a note that ctrlhub changes are left uncommitted.
- OneOps `github.com/netxops/teleabs v0.0.26` confirmation.
- Focused test command results.
- Longest-path runtime result: `found=true`, `plugins_input=["nvidia_smi"]`, `status=failed`, and the failure message.
- A clear note that Prometheus validation was not performed by request.
