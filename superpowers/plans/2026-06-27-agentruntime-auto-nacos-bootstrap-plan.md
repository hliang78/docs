# AgentRuntime Auto Nacos Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the dedicated `ONEOPS_AGENT_RUNTIME_USE_NACOS` mode switch and let `agentruntime` automatically choose Nacos bootstrap when `nacos_config.yaml` exists, while preserving local file fallback for the current real MVP loop.

**Architecture:** Keep platform-config bootstrap inside `OneOps/cmd/agentruntime`. Split source detection, raw content loading, and YAML decoding into focused helpers. Reuse the existing OneOps Nacos bootstrap convention (`nacos_config.yaml` -> `BootStartConfig` -> `cipher-aes-start-config`) and keep runtime/service layers unchanged.

**Tech Stack:** Go, Viper, existing OneOps Nacos bootstrap helpers, GORM/MySQL, bash helper scripts, real API acceptance in OneOPS-UI

---

## File Structure

### Existing files to modify

- `OneOps/cmd/agentruntime/bootstrap_config.go`
  - replace env-controlled Nacos intent with auto-detected source selection
  - add Nacos raw-config loading helpers and shared YAML decode helper
- `OneOps/cmd/agentruntime/bootstrap_config_test.go`
  - update source-selection tests for `nacos_config.yaml` auto-detection
  - add fail-fast tests that forbid silent fallback from detected Nacos mode
- `OneOps/cmd/agentruntime/main.go`
  - load platform config through the new source/content/decode helpers
- `OneOps/cmd/agentruntime/main_test.go`
  - keep runtime bootstrap coverage and add integration coverage for auto-detected Nacos/local file behavior
- `OneOps/scripts/start_multi_agent_closure_stack.sh`
  - remove `ONEOPS_AGENT_RUNTIME_USE_NACOS`
  - keep local file fallback wiring only
- `OneOps/scripts/test_start_multi_agent_closure_stack.sh`
  - remove Nacos mode env assertions
  - keep local startup smoke assertions
- `docs/runbooks/alert-to-ticket-dagengine-mvp.md`
  - document auto-detected Nacos bootstrap and local fallback behavior

### Existing files to read for reference

- `OneOps/initialize/nacos.go`
  - existing bootstrap of `BootStartConfig` and Nacos config client
- `OneOps/app/common/nacos/service/nacos.go`
  - current `DefaultConfigFile`, `BootStartConfig`, and `cipher-aes-start-config` read convention
- `OneOps/config/nacos.go`
  - shape of `nacos_config.yaml`

## Task 1: Convert Source Selection To Auto-Detected Nacos

**Files:**
- Modify: `OneOps/cmd/agentruntime/bootstrap_config.go`
- Modify: `OneOps/cmd/agentruntime/bootstrap_config_test.go`
- Test: `OneOps/cmd/agentruntime/bootstrap_config_test.go`

- [ ] **Step 1: Write the failing source-detection tests**

Add these tests to `OneOps/cmd/agentruntime/bootstrap_config_test.go`:

```go
func TestResolvePlatformConfigSourcePrefersNacosConfigFileWhenPresent(t *testing.T) {
	source, err := resolvePlatformConfigSource(
		func(string) bool { return true },
		func(string) bool { return false },
	)
	if err != nil {
		t.Fatalf("resolvePlatformConfigSource error: %v", err)
	}
	if source.Kind != platformConfigSourceNacos {
		t.Fatalf("source kind = %q, want %q", source.Kind, platformConfigSourceNacos)
	}
}

func TestResolvePlatformConfigSourceDoesNotFallbackWhenExplicitEnvFileMissing(t *testing.T) {
	t.Setenv("ONEOPS_AGENT_RUNTIME_CONFIG_FILE", "/tmp/missing-runtime-local.yaml")

	_, err := resolvePlatformConfigSource(
		func(string) bool { return false },
		func(path string) bool { return path == defaultAgentRuntimeConfigFile },
	)
	if err == nil {
		t.Fatal("resolvePlatformConfigSource error = nil, want explicit env file missing error")
	}
}
```

- [ ] **Step 2: Run the source-detection tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./cmd/agentruntime -run 'TestResolvePlatformConfigSourcePrefersNacosConfigFileWhenPresent|TestResolvePlatformConfigSourceDoesNotFallbackWhenExplicitEnvFileMissing' -count=1
```

Expected:

```text
FAIL ... too many arguments in call to resolvePlatformConfigSource
```

- [ ] **Step 3: Implement minimal auto-detected source selection**

Update `OneOps/cmd/agentruntime/bootstrap_config.go` so source detection is file-driven instead of env-driven:

```go
const nacosBootstrapConfigFile = "nacos_config.yaml"

func resolvePlatformConfigSource(
	fileExists func(string) bool,
	defaultFileExists func(string) bool,
) (platformConfigSource, error) {
	if fileExists(nacosBootstrapConfigFile) {
		return platformConfigSource{Kind: platformConfigSourceNacos, Path: nacosBootstrapConfigFile}, nil
	}

	configFile := strings.TrimSpace(os.Getenv("ONEOPS_AGENT_RUNTIME_CONFIG_FILE"))
	if configFile != "" {
		if !fileExists(configFile) {
			return platformConfigSource{}, fmt.Errorf("configured agentruntime platform config file not found: %s", configFile)
		}
		return platformConfigSource{Kind: platformConfigSourceFile, Path: configFile}, nil
	}

	if defaultFileExists(defaultAgentRuntimeConfigFile) {
		return platformConfigSource{Kind: platformConfigSourceFile, Path: defaultAgentRuntimeConfigFile}, nil
	}

	return platformConfigSource{}, fmt.Errorf("no platform config source available")
}
```

- [ ] **Step 4: Run the source-detection test group to verify it passes**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./cmd/agentruntime -run 'TestResolvePlatformConfigSource' -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/cmd/agentruntime	0.xxxs
```

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add cmd/agentruntime/bootstrap_config.go cmd/agentruntime/bootstrap_config_test.go
git commit -m "feat: auto-detect agentruntime nacos bootstrap"
```

## Task 2: Add Real Nacos Platform Config Loading

**Files:**
- Modify: `OneOps/cmd/agentruntime/bootstrap_config.go`
- Modify: `OneOps/cmd/agentruntime/bootstrap_config_test.go`
- Modify: `OneOps/cmd/agentruntime/main.go`
- Test: `OneOps/cmd/agentruntime/bootstrap_config_test.go`

- [ ] **Step 1: Write the failing Nacos bootstrap tests**

Add these tests to `OneOps/cmd/agentruntime/bootstrap_config_test.go`:

```go
func TestLoadPlatformConfigFromSourceLoadsNacosContent(t *testing.T) {
	source := platformConfigSource{Kind: platformConfigSourceNacos, Path: nacosBootstrapConfigFile}

	cfg, err := loadPlatformConfigFromSource(
		source,
		func(string) ([]byte, error) {
			return []byte("nacos:\n  clientConfig:\n    group: DEFAULT_GROUP\n"), nil
		},
		func([]byte) (string, error) {
			return "mysql:\n  host: 127.0.0.1\n  port: 3306\n  dbName: agentruntime_test\n  username: root\n  password: root\nsystem:\n  debug: false\n", nil
		},
	)
	if err != nil {
		t.Fatalf("loadPlatformConfigFromSource error: %v", err)
	}
	if cfg.MySQL.DBName != "agentruntime_test" {
		t.Fatalf("mysql dbName = %q, want %q", cfg.MySQL.DBName, "agentruntime_test")
	}
}

func TestLoadPlatformConfigFromSourceFailsFastWhenNacosBootstrapFails(t *testing.T) {
	source := platformConfigSource{Kind: platformConfigSourceNacos, Path: nacosBootstrapConfigFile}

	_, err := loadPlatformConfigFromSource(
		source,
		func(string) ([]byte, error) { return nil, fmt.Errorf("read bootstrap failed") },
		func([]byte) (string, error) { return "", nil },
	)
	if err == nil {
		t.Fatal("loadPlatformConfigFromSource error = nil, want nacos bootstrap error")
	}
}
```

- [ ] **Step 2: Run the Nacos bootstrap tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./cmd/agentruntime -run 'TestLoadPlatformConfigFromSourceLoadsNacosContent|TestLoadPlatformConfigFromSourceFailsFastWhenNacosBootstrapFails' -count=1
```

Expected:

```text
FAIL ... undefined: loadPlatformConfigFromSource
```

- [ ] **Step 3: Implement shared decode and Nacos loader helpers**

Add these helpers to `OneOps/cmd/agentruntime/bootstrap_config.go`:

```go
func loadPlatformConfigFromSource(
	source platformConfigSource,
	readFile func(string) ([]byte, error),
	loadNacosConfig func([]byte) (string, error),
) (*config.Config, error) {
	switch source.Kind {
	case platformConfigSourceFile:
		content, err := readFile(source.Path)
		if err != nil {
			return nil, fmt.Errorf("read config file %s: %w", source.Path, err)
		}
		return decodePlatformConfig(content, source.Path)
	case platformConfigSourceNacos:
		bootstrapContent, err := readFile(source.Path)
		if err != nil {
			return nil, fmt.Errorf("read nacos bootstrap file %s: %w", source.Path, err)
		}
		content, err := loadNacosConfig(bootstrapContent)
		if err != nil {
			return nil, fmt.Errorf("load platform config from nacos: %w", err)
		}
		return decodePlatformConfig([]byte(content), "nacos://cipher-aes-start-config")
	default:
		return nil, fmt.Errorf("unsupported platform config source %q", source.Kind)
	}
}

func decodePlatformConfig(content []byte, source string) (*config.Config, error) {
	v := viper.New()
	v.SetConfigType("yaml")
	if err := v.ReadConfig(strings.NewReader(os.ExpandEnv(string(content)))); err != nil {
		return nil, fmt.Errorf("parse config source %s: %w", source, err)
	}
	conf := new(config.Config)
	if err := v.Unmarshal(conf); err != nil {
		return nil, fmt.Errorf("unmarshal config source %s: %w", source, err)
	}
	return conf, nil
}
```

Also add a real Nacos content loader that reuses `initialize/nacos.go` and `app/common/nacos/service/nacos.go` conventions:

```go
func loadPlatformConfigContentFromNacos(bootstrapContent []byte) (string, error) {
	v := viper.New()
	v.SetConfigType("yaml")
	if err := v.ReadConfig(bytes.NewReader(bootstrapContent)); err != nil {
		return "", fmt.Errorf("parse nacos bootstrap config: %w", err)
	}

	var nacosConf config.NacosConfig
	if err := v.Unmarshal(&nacosConf); err != nil {
		return "", fmt.Errorf("unmarshal nacos bootstrap config: %w", err)
	}

	nacosSvc.BootStartConfig = &nacosConf
	client := initialize.InitNacosConfigClient()
	content, err := (&nacosSvc.NacosClient{ConfigClient: client}).GetConfig()
	if err != nil {
		return "", err
	}
	return content, nil
}
```

- [ ] **Step 4: Route `main.go` through the shared source loader**

Replace the current platform config bootstrap in `OneOps/cmd/agentruntime/main.go` with:

```go
func loadAgentRuntimePlatformConfig() (*config.Config, error) {
	source, err := resolvePlatformConfigSource(fileExists, fileExists)
	if err != nil {
		return nil, err
	}
	return loadPlatformConfigFromSource(source, os.ReadFile, loadPlatformConfigContentFromNacos)
}
```

- [ ] **Step 5: Run bootstrap tests to verify they pass**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./cmd/agentruntime -run 'TestLoadPlatformConfigFromSource|TestResolvePlatformConfigSource' -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/cmd/agentruntime	0.xxxs
```

- [ ] **Step 6: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add cmd/agentruntime/bootstrap_config.go cmd/agentruntime/bootstrap_config_test.go cmd/agentruntime/main.go
git commit -m "feat: load agentruntime platform config from nacos bootstrap"
```

## Task 3: Update Integration Tests For Auto-Detected Bootstrap

**Files:**
- Modify: `OneOps/cmd/agentruntime/main_test.go`
- Test: `OneOps/cmd/agentruntime/main_test.go`

- [ ] **Step 1: Write the failing integration tests**

Add these tests to `OneOps/cmd/agentruntime/main_test.go`:

```go
func TestLoadAgentRuntimePlatformConfigUsesLocalFileSourceWhenNacosBootstrapMissing(t *testing.T) {
	configPath := writeAgentRuntimeConfigFixture(t)
	t.Setenv("ONEOPS_AGENT_RUNTIME_CONFIG_FILE", configPath)

	cfg, err := loadAgentRuntimePlatformConfig()
	if err != nil {
		t.Fatalf("loadAgentRuntimePlatformConfig error: %v", err)
	}
	if cfg.MySQL.DBName != "agentruntime_test" {
		t.Fatalf("mysql dbName = %q, want %q", cfg.MySQL.DBName, "agentruntime_test")
	}
}

func TestLoadAgentRuntimePlatformConfigFailsFastWhenNacosBootstrapPresentButUnreadable(t *testing.T) {
	tempDir := t.TempDir()
	if err := os.WriteFile(filepath.Join(tempDir, nacosBootstrapConfigFile), []byte("not: [valid"), 0o600); err != nil {
		t.Fatalf("write nacos bootstrap file failed: %v", err)
	}

	oldWD, err := os.Getwd()
	if err != nil {
		t.Fatalf("getwd failed: %v", err)
	}
	defer func() { _ = os.Chdir(oldWD) }()
	if err := os.Chdir(tempDir); err != nil {
		t.Fatalf("chdir failed: %v", err)
	}

	_, err = loadAgentRuntimePlatformConfig()
	if err == nil {
		t.Fatal("loadAgentRuntimePlatformConfig error = nil, want nacos bootstrap error")
	}
}
```

- [ ] **Step 2: Run the integration tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./cmd/agentruntime -run 'TestLoadAgentRuntimePlatformConfigUsesLocalFileSourceWhenNacosBootstrapMissing|TestLoadAgentRuntimePlatformConfigFailsFastWhenNacosBootstrapPresentButUnreadable' -count=1
```

Expected:

```text
FAIL ... old nacos env-based expectations no longer match
```

- [ ] **Step 3: Remove obsolete env-driven expectations and keep runtime bootstrap coverage**

Keep:

- `TestNewServerRuntimeReturnsErrorUntilPersistenceBootstrapIsWired`
- `TestNewServerRuntimeBootstrapsPersistentWorkers`

Replace any old `ONEOPS_AGENT_RUNTIME_USE_NACOS` expectations with the two tests above and the existing local-file fixture helper.

- [ ] **Step 4: Run the integration test group to verify it passes**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./cmd/agentruntime -run 'TestLoadAgentRuntimePlatformConfig|TestNewServerRuntime' -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/cmd/agentruntime	0.xxxs
```

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add cmd/agentruntime/main_test.go
git commit -m "test: cover auto bootstrap behavior in agentruntime main"
```

## Task 4: Remove The Nacos Mode Env From Local Tooling And Docs

**Files:**
- Modify: `OneOps/scripts/start_multi_agent_closure_stack.sh`
- Modify: `OneOps/scripts/test_start_multi_agent_closure_stack.sh`
- Modify: `docs/runbooks/alert-to-ticket-dagengine-mvp.md`
- Test: `OneOps/scripts/test_start_multi_agent_closure_stack.sh`

- [ ] **Step 1: Write the failing script assertions**

Update `OneOps/scripts/test_start_multi_agent_closure_stack.sh` so it asserts that local startup output does not depend on `ONEOPS_AGENT_RUNTIME_USE_NACOS`:

```bash
if [[ "${OUTPUT}" == *"ONEOPS_AGENT_RUNTIME_USE_NACOS="* ]]; then
  echo "did not expect output to contain ONEOPS_AGENT_RUNTIME_USE_NACOS" >&2
  exit 1
fi
```

- [ ] **Step 2: Run the script smoke test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
bash scripts/test_start_multi_agent_closure_stack.sh
```

Expected:

```text
did not expect output to contain ONEOPS_AGENT_RUNTIME_USE_NACOS
```

- [ ] **Step 3: Remove the obsolete env from script and docs**

Apply these changes:

```bash
# start_multi_agent_closure_stack.sh
# remove:
# ONEOPS_AGENT_RUNTIME_USE_NACOS="${ONEOPS_AGENT_RUNTIME_USE_NACOS:-false}"
#
# remove from print_config
# remove from start_agentruntime command export
```

Runbook text should explicitly say:

- local helper mode normally runs without `nacos_config.yaml`
- placing `nacos_config.yaml` enables production-style Nacos bootstrap automatically
- if `nacos_config.yaml` exists, bootstrap errors fail startup instead of falling back to `local_config_test.yaml`

- [ ] **Step 4: Run the script smoke test to verify it passes**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
bash scripts/test_start_multi_agent_closure_stack.sh
```

Expected:

```text
start_multi_agent_closure_stack_smoke=pass
```

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL
git add OneOps/scripts/start_multi_agent_closure_stack.sh OneOps/scripts/test_start_multi_agent_closure_stack.sh docs/runbooks/alert-to-ticket-dagengine-mvp.md
git commit -m "docs: simplify agentruntime bootstrap startup"
```

## Task 5: Full Regression And Real Acceptance

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

- [ ] **Step 2: Restart the local stack with simplified startup**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
./scripts/start_multi_agent_closure_stack.sh restart
```

Expected:

```text
agentruntime_ready=yes port=18080
oneops_ready=yes port=8380
execution_observatory_url=http://127.0.0.1:3001/#/platform/execution-observatory
```

- [ ] **Step 3: Run real API acceptance**

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

- [ ] **Step 4: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL
git add OneOps/cmd/agentruntime OneOps/scripts docs/runbooks/alert-to-ticket-dagengine-mvp.md
git commit -m "feat: auto-detect agentruntime nacos bootstrap"
```
