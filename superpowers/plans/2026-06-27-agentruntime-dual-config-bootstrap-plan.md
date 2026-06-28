# AgentRuntime Dual-Source Config Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Nacos-first, local-file-fallback platform config bootstrap to `agentruntime` while preserving the current real local acceptance flow.

**Architecture:** Keep runtime-instance config in `RuntimeConfig` env parsing, but move platform-config source selection into `cmd/agentruntime` bootstrap helpers. Prefer explicit Nacos bootstrap when requested, otherwise fall back to local file, then fail clearly if no platform config source is available.

**Tech Stack:** Go, Viper, existing OneOps Nacos bootstrap conventions, GORM/MySQL, existing agentruntime worker bootstrap, shell script/runbook verification

---

## File Structure

### Existing files to modify

- `OneOps/cmd/agentruntime/main.go`
  - split platform-config loading into explicit bootstrap helpers and add dual-source precedence
- `OneOps/cmd/agentruntime/main_test.go`
  - cover Nacos/file selection and runtime bootstrap compatibility
- `OneOps/scripts/start_multi_agent_closure_stack.sh`
  - keep local fallback explicit and document the config source passed to `agentruntime`
- `OneOps/scripts/test_start_multi_agent_closure_stack.sh`
  - assert the helper script exports the config file env var in local mode
- `docs/runbooks/alert-to-ticket-dagengine-mvp.md`
  - explain Nacos-first / local-file-fallback behavior

### New files to create

- `OneOps/cmd/agentruntime/bootstrap_config.go`
  - isolate platform config source selection, local file loading, and Nacos intent detection
- `OneOps/cmd/agentruntime/bootstrap_config_test.go`
  - focused tests for source precedence and failure semantics

## Task 1: Extract Dual-Source Bootstrap Config Loader

**Files:**
- Create: `OneOps/cmd/agentruntime/bootstrap_config.go`
- Create: `OneOps/cmd/agentruntime/bootstrap_config_test.go`
- Test: `OneOps/cmd/agentruntime/bootstrap_config_test.go`

- [ ] **Step 1: Write the failing source-precedence tests**

```go
func TestResolvePlatformConfigSourcePrefersLocalFileWhenNacosModeDisabled(t *testing.T) {
	t.Setenv("ONEOPS_AGENT_RUNTIME_CONFIG_FILE", "/tmp/runtime-local.yaml")
	source, err := resolvePlatformConfigSource(func() bool { return false }, func(string) bool { return true })
	if err != nil {
		t.Fatalf("resolvePlatformConfigSource error: %v", err)
	}
	if source.Kind != platformConfigSourceFile {
		t.Fatalf("source kind = %q, want %q", source.Kind, platformConfigSourceFile)
	}
	if source.Path != "/tmp/runtime-local.yaml" {
		t.Fatalf("source path = %q, want %q", source.Path, "/tmp/runtime-local.yaml")
	}
}

func TestResolvePlatformConfigSourceRequiresNacosWhenExplicitlyEnabled(t *testing.T) {
	t.Setenv("ONEOPS_AGENT_RUNTIME_CONFIG_FILE", "/tmp/runtime-local.yaml")
	_, err := resolvePlatformConfigSource(func() bool { return true }, func(string) bool { return true })
	if err == nil {
		t.Fatal("resolvePlatformConfigSource error = nil, want nacos-required error until nacos loader is wired")
	}
}
```

- [ ] **Step 2: Run the config-loader tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./cmd/agentruntime -run 'TestResolvePlatformConfigSourcePrefersLocalFileWhenNacosModeDisabled|TestResolvePlatformConfigSourceRequiresNacosWhenExplicitlyEnabled' -count=1
```

Expected:

```text
FAIL ... undefined: resolvePlatformConfigSource
```

- [ ] **Step 3: Implement the minimal bootstrap config loader**

```go
package main

type platformConfigSourceKind string

const (
	platformConfigSourceNacos platformConfigSourceKind = "nacos"
	platformConfigSourceFile  platformConfigSourceKind = "file"
)

type platformConfigSource struct {
	Kind platformConfigSourceKind
	Path string
}

func resolvePlatformConfigSource(nacosEnabled func() bool, fileExists func(string) bool) (platformConfigSource, error) {
	if nacosEnabled() {
		return platformConfigSource{}, fmt.Errorf("agentruntime nacos bootstrap requested but not yet configured")
	}
	path := strings.TrimSpace(os.Getenv("ONEOPS_AGENT_RUNTIME_CONFIG_FILE"))
	if path != "" && fileExists(path) {
		return platformConfigSource{Kind: platformConfigSourceFile, Path: path}, nil
	}
	if fileExists(defaultAgentRuntimeConfigFile) {
		return platformConfigSource{Kind: platformConfigSourceFile, Path: defaultAgentRuntimeConfigFile}, nil
	}
	return platformConfigSource{}, fmt.Errorf("no platform config source available")
}
```

- [ ] **Step 4: Run the config-loader tests to verify they pass**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./cmd/agentruntime -run 'TestResolvePlatformConfigSourcePrefersLocalFileWhenNacosModeDisabled|TestResolvePlatformConfigSourceRequiresNacosWhenExplicitlyEnabled' -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/cmd/agentruntime	0.xxxs
```

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add cmd/agentruntime/bootstrap_config.go cmd/agentruntime/bootstrap_config_test.go
git commit -m "feat: add agentruntime dual-source config bootstrap loader"
```

## Task 2: Wire Dual-Source Loader Into `cmd/agentruntime`

**Files:**
- Modify: `OneOps/cmd/agentruntime/main.go`
- Modify: `OneOps/cmd/agentruntime/main_test.go`
- Test: `OneOps/cmd/agentruntime/main_test.go`

- [ ] **Step 1: Write the failing bootstrap integration tests**

```go
func TestLoadAgentRuntimePlatformConfigUsesLocalFileSource(t *testing.T) {
	configPath := writeAgentRuntimeConfigFixture(t)
	t.Setenv("ONEOPS_AGENT_RUNTIME_CONFIG_FILE", configPath)

	cfg, err := loadAgentRuntimePlatformConfig()
	if err != nil {
		t.Fatalf("loadAgentRuntimePlatformConfig error: %v", err)
	}
	if cfg.MySQL.DBName == "" {
		t.Fatal("mysql dbName = empty, want decoded config")
	}
}

func TestLoadAgentRuntimePlatformConfigFailsWhenNacosRequestedButUnavailable(t *testing.T) {
	t.Setenv("ONEOPS_AGENT_RUNTIME_USE_NACOS", "true")
	_, err := loadAgentRuntimePlatformConfig()
	if err == nil {
		t.Fatal("loadAgentRuntimePlatformConfig error = nil, want nacos bootstrap error")
	}
}
```

- [ ] **Step 2: Run the bootstrap integration tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./cmd/agentruntime -run 'TestLoadAgentRuntimePlatformConfigUsesLocalFileSource|TestLoadAgentRuntimePlatformConfigFailsWhenNacosRequestedButUnavailable' -count=1
```

Expected:

```text
FAIL ... unexpected source selection or missing helper fixture
```

- [ ] **Step 3: Implement source selection in `main.go`**

```go
func loadAgentRuntimePlatformConfig() (*config.Config, error) {
	source, err := resolvePlatformConfigSource(nacosBootstrapRequested, fileExists)
	if err != nil {
		return nil, err
	}
	switch source.Kind {
	case platformConfigSourceFile:
		return loadPlatformConfigFromFile(source.Path)
	case platformConfigSourceNacos:
		return nil, fmt.Errorf("agentruntime nacos bootstrap requested but not yet implemented")
	default:
		return nil, fmt.Errorf("unsupported platform config source %q", source.Kind)
	}
}
```

- [ ] **Step 4: Run the bootstrap integration tests to verify they pass**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./cmd/agentruntime -run 'TestLoadAgentRuntimePlatformConfigUsesLocalFileSource|TestLoadAgentRuntimePlatformConfigFailsWhenNacosRequestedButUnavailable|TestNewServerRuntimeBootstrapsPersistentWorkers' -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/cmd/agentruntime	0.xxxs
```

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add cmd/agentruntime/main.go cmd/agentruntime/main_test.go
git commit -m "feat: wire dual-source config bootstrap into agentruntime"
```

## Task 3: Add Explicit Nacos Intent And Safe Failure Semantics

**Files:**
- Create: `OneOps/cmd/agentruntime/bootstrap_config.go`
- Modify: `OneOps/cmd/agentruntime/bootstrap_config_test.go`
- Modify: `OneOps/cmd/agentruntime/main.go`
- Test: `OneOps/cmd/agentruntime/bootstrap_config_test.go`

- [ ] **Step 1: Write the failing explicit-intent tests**

```go
func TestNacosBootstrapRequestedByExplicitEnv(t *testing.T) {
	t.Setenv("ONEOPS_AGENT_RUNTIME_USE_NACOS", "true")
	if !nacosBootstrapRequested() {
		t.Fatal("nacosBootstrapRequested = false, want true")
	}
}

func TestResolvePlatformConfigSourceDoesNotSilentlyFallbackFromExplicitNacos(t *testing.T) {
	t.Setenv("ONEOPS_AGENT_RUNTIME_USE_NACOS", "true")
	t.Setenv("ONEOPS_AGENT_RUNTIME_CONFIG_FILE", "/tmp/runtime-local.yaml")
	_, err := resolvePlatformConfigSource(nacosBootstrapRequested, func(string) bool { return true })
	if err == nil {
		t.Fatal("resolvePlatformConfigSource error = nil, want explicit nacos failure")
	}
}
```

- [ ] **Step 2: Run the Nacos-intent tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./cmd/agentruntime -run 'TestNacosBootstrapRequestedByExplicitEnv|TestResolvePlatformConfigSourceDoesNotSilentlyFallbackFromExplicitNacos' -count=1
```

Expected:

```text
FAIL ... undefined: nacosBootstrapRequested
```

- [ ] **Step 3: Implement explicit Nacos intent detection**

```go
func nacosBootstrapRequested() bool {
	raw := strings.ToLower(strings.TrimSpace(os.Getenv("ONEOPS_AGENT_RUNTIME_USE_NACOS")))
	return raw == "1" || raw == "true" || raw == "yes" || raw == "on"
}
```

- [ ] **Step 4: Run the Nacos-intent tests to verify they pass**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./cmd/agentruntime -run 'TestNacosBootstrapRequestedByExplicitEnv|TestResolvePlatformConfigSourceDoesNotSilentlyFallbackFromExplicitNacos' -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/cmd/agentruntime	0.xxxs
```

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add cmd/agentruntime/bootstrap_config.go cmd/agentruntime/bootstrap_config_test.go cmd/agentruntime/main.go
git commit -m "feat: add explicit nacos bootstrap intent for agentruntime"
```

## Task 4: Align Local Script And Runbook With Dual-Source Bootstrap

**Files:**
- Modify: `OneOps/scripts/start_multi_agent_closure_stack.sh`
- Modify: `OneOps/scripts/test_start_multi_agent_closure_stack.sh`
- Modify: `docs/runbooks/alert-to-ticket-dagengine-mvp.md`
- Test: `OneOps/scripts/test_start_multi_agent_closure_stack.sh`

- [ ] **Step 1: Write the failing local-mode script assertion**

```bash
if [[ "${OUTPUT}" != *"ONEOPS_AGENT_RUNTIME_CONFIG_FILE="* ]]; then
  echo "expected output to contain ONEOPS_AGENT_RUNTIME_CONFIG_FILE"
  exit 1
fi
```

- [ ] **Step 2: Run the script smoke test to verify local-mode behavior**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL
bash OneOps/scripts/test_start_multi_agent_closure_stack.sh
```

Expected:

```text
FAIL local-mode config file export assertion
```

- [ ] **Step 3: Update script and runbook**

```bash
ONEOPS_AGENT_RUNTIME_CONFIG_FILE="${ONEOPS_AGENT_RUNTIME_CONFIG_FILE:-${ROOT_DIR}/local_config_test.yaml}"
```

Runbook text should state:

- local closure defaults to file bootstrap
- future production bootstrap can enable Nacos explicitly
- runtime env overrides still apply in both modes

- [ ] **Step 4: Run the script smoke test to verify it passes**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL
bash OneOps/scripts/test_start_multi_agent_closure_stack.sh
```

Expected:

```text
start_multi_agent_closure_stack_smoke=pass
```

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL
git add OneOps/scripts/start_multi_agent_closure_stack.sh OneOps/scripts/test_start_multi_agent_closure_stack.sh docs/runbooks/alert-to-ticket-dagengine-mvp.md
git commit -m "docs: align agentruntime local bootstrap with dual-source config"
```

## Task 5: Full Verification

**Files:**
- Test-only verification, no new files

- [ ] **Step 1: Run command-level regression**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./cmd/agentruntime ./app/agentruntime/... ./app/orchestration/service/impl ./cmd -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/cmd/agentruntime	...
ok  	github.com/netxops/OneOps/app/agentruntime/... 
ok  	github.com/netxops/OneOps/app/orchestration/service/impl	...
ok  	github.com/netxops/OneOps/cmd	...
```

- [ ] **Step 2: Run local acceptance**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
ONEOPS_API_BASE_URL=http://127.0.0.1:3001/api/v1 \
ONEOPS_UI_LOGIN_USERNAME=admin \
ONEOPS_UI_LOGIN_PASSWORD='admin@123' \
npm run acceptance:multi-agent-ticket-closure-real-api
```

Expected:

```text
Observatory URL: http://127.0.0.1:3001/#/platform/execution-observatory
Execution ID: ...
Evidence JSON: ...
Evidence Markdown: ...
```

- [ ] **Step 3: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL
git add OneOps/cmd/agentruntime OneOps/scripts docs/runbooks/alert-to-ticket-dagengine-mvp.md
git commit -m "feat: prepare agentruntime for nacos-first config bootstrap"
```

## Self-Review

### Spec coverage

- Nacos-first and local-file-fallback precedence: covered by Tasks 1-3
- env runtime overrides remain unchanged: covered by Tasks 2 and 4
- local compatibility preserved: covered by Task 4 and Task 5
- fail-fast semantics for missing platform config source: covered by Tasks 1 and 3

### Placeholder scan

- no `TODO` / `TBD` placeholders remain
- every task includes exact files, commands, and expected results
- local and future Nacos behavior are separated explicitly

### Type consistency

- `RuntimeConfig` remains the runtime env contract
- platform config source selection stays in `cmd/agentruntime`
- helper script remains local-file-first unless explicit Nacos bootstrap is requested
