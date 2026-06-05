# Ctrlhub Agent RunTask Sandbox Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run every ctrlhub agent `RunTask` command through a task-level sandbox, with systemd transient services enforcing CPU, memory, process-count, and runtime limits.

**Architecture:** Add `task_sandbox` config, introduce a `TaskSandboxRunner` interface, preserve the current direct executor as an explicit backend, and add a `SystemdTaskSandboxRunner` based on `systemd-run --wait --collect --pipe`. `AgentService` keeps building shell, Ansible, and Terraform commands as it does today, but delegates final execution and stop behavior to the sandbox runner.

**Tech Stack:** Go, systemd/systemd-run, zap, existing Bidi agent package, existing Go test suite.

---

## File Structure

- Modify `ctrlhub/controller/agent/pkg/config/config.go`: add YAML config struct and defaults for `task_sandbox`.
- Modify `ctrlhub/controller/agent/pkg/config/loader.go`: apply sandbox defaults and validate sandbox values.
- Modify `ctrlhub/controller/agent/pkg/config/loader_test.go`: cover defaults, YAML parsing, and validation.
- Modify `ctrlhub/controller/agent/cmd/agent/main.go`: map config package sandbox config into runtime `AgentConfig`.
- Modify `ctrlhub/controller/agent/cmd/agent/agent_service.go`: hold a `TaskSandboxRunner`, delegate command execution, and stop sandboxed tasks.
- Create `ctrlhub/controller/agent/cmd/agent/task_sandbox.go`: define request/result/types, direct runner, systemd runner, command construction, unit-name sanitization, and output streaming.
- Create `ctrlhub/controller/agent/cmd/agent/task_sandbox_test.go`: test unit names, command construction, direct runner, systemd runner command invocation, and stop behavior.
- Modify `ctrlhub/controller/agent/cmd/agent/agent_service_task_runner_test.go`: update tests to inject fake sandbox runner and prove command paths delegate to sandbox.
- Modify `ctrlhub/controller/agent/configs/agent.yaml`: add local default `task_sandbox` section with sandbox disabled.
- Modify `ctrlhub/controller/deploy/agent.yaml.template`: add production-oriented sandbox template values.
- Modify `ctrlhub/controller/deploy/agent.root.example.yaml` and `ctrlhub/controller/deploy/agent.unprivileged.example.yaml`: add example sandbox settings.
- Create `ctrlhub/scripts/agent_runtask_systemd_sandbox_smoke.sh`: gated smoke test for real systemd hosts.

---

### Task 1: Add `task_sandbox` Config

**Files:**
- Modify: `ctrlhub/controller/agent/pkg/config/config.go`
- Modify: `ctrlhub/controller/agent/pkg/config/loader.go`
- Test: `ctrlhub/controller/agent/pkg/config/loader_test.go`

- [ ] **Step 1: Write failing tests for defaults and YAML parsing**

Add these tests to `loader_test.go`:

```go
func TestLoadTaskSandboxDefaultsWhenOmitted(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "agent.yaml")
	if err := os.WriteFile(configPath, []byte(`
agent:
  code: "agent-001"
  workspace: "./workspace"
  log_level: "info"
  upload_dir: "./uploads"

protocol:
  enabled: true
  controller_address: "127.0.0.1:7073"
  collection_interval: 30
  heartbeat_interval: 30
  registration_interval: 60
  reconnect_interval: 5
  max_reconnect_attempts: -1
  site_id: "DefaultArea"
  tenant_id: "default"
  group_id: "default"

logging:
  directory: "./logs"
  file: "agent.log"
  max_size: "100MB"
  max_files: 10
  level: "info"
  stdout: false
`), 0o644); err != nil {
		t.Fatalf("write config: %v", err)
	}

	cfg, err := Load(configPath)
	if err != nil {
		t.Fatalf("load config: %v", err)
	}

	if cfg.TaskSandbox.Enabled {
		t.Fatalf("expected sandbox disabled by default")
	}
	if cfg.TaskSandbox.Backend != "direct" {
		t.Fatalf("backend default mismatch: %q", cfg.TaskSandbox.Backend)
	}
	if cfg.TaskSandbox.MemoryMax != "1G" || cfg.TaskSandbox.CPUQuota != "100%" || cfg.TaskSandbox.TasksMax != 256 || cfg.TaskSandbox.RuntimeMaxSec != 1800 || cfg.TaskSandbox.UnitPrefix != "oneops-task" {
		t.Fatalf("unexpected sandbox defaults: %#v", cfg.TaskSandbox)
	}
}

func TestLoadTaskSandboxParsesSystemdConfig(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "agent.yaml")
	if err := os.WriteFile(configPath, []byte(`
agent:
  code: "agent-001"
  workspace: "./workspace"
  log_level: "info"
  upload_dir: "./uploads"

protocol:
  enabled: true
  controller_address: "127.0.0.1:7073"
  collection_interval: 30
  heartbeat_interval: 30
  registration_interval: 60
  reconnect_interval: 5
  max_reconnect_attempts: -1
  site_id: "DefaultArea"
  tenant_id: "default"
  group_id: "default"

task_sandbox:
  enabled: true
  backend: systemd
  allow_legacy_fallback: false
  memory_max: 2G
  cpu_quota: 150%
  tasks_max: 128
  runtime_max_sec: 600
  unit_prefix: oneops-rt

logging:
  directory: "./logs"
  file: "agent.log"
  max_size: "100MB"
  max_files: 10
  level: "info"
  stdout: false
`), 0o644); err != nil {
		t.Fatalf("write config: %v", err)
	}

	cfg, err := Load(configPath)
	if err != nil {
		t.Fatalf("load config: %v", err)
	}

	if !cfg.TaskSandbox.Enabled || cfg.TaskSandbox.Backend != "systemd" || cfg.TaskSandbox.AllowLegacyFallback {
		t.Fatalf("unexpected sandbox switches: %#v", cfg.TaskSandbox)
	}
	if cfg.TaskSandbox.MemoryMax != "2G" || cfg.TaskSandbox.CPUQuota != "150%" || cfg.TaskSandbox.TasksMax != 128 || cfg.TaskSandbox.RuntimeMaxSec != 600 || cfg.TaskSandbox.UnitPrefix != "oneops-rt" {
		t.Fatalf("unexpected sandbox limits: %#v", cfg.TaskSandbox)
	}
}

func TestLoadTaskSandboxRejectsInvalidBackend(t *testing.T) {
	tmpDir := t.TempDir()
	configPath := filepath.Join(tmpDir, "agent.yaml")
	if err := os.WriteFile(configPath, []byte(`
agent:
  code: "agent-001"
  workspace: "./workspace"
  log_level: "info"
  upload_dir: "./uploads"

protocol:
  enabled: true
  controller_address: "127.0.0.1:7073"
  collection_interval: 30
  heartbeat_interval: 30
  registration_interval: 60
  reconnect_interval: 5
  max_reconnect_attempts: -1
  site_id: "DefaultArea"
  tenant_id: "default"
  group_id: "default"

task_sandbox:
  enabled: true
  backend: docker

logging:
  directory: "./logs"
  file: "agent.log"
  max_size: "100MB"
  max_files: 10
  level: "info"
  stdout: false
`), 0o644); err != nil {
		t.Fatalf("write config: %v", err)
	}

	_, err := Load(configPath)
	if err == nil || !strings.Contains(err.Error(), "task_sandbox.backend must be one of: direct|systemd") {
		t.Fatalf("expected backend validation error, got %v", err)
	}
}
```

Also add `strings` to the test imports.

- [ ] **Step 2: Run config tests to verify failure**

Run:

```bash
cd ctrlhub && go test ./controller/agent/pkg/config
```

Expected: FAIL because `Config.TaskSandbox` is undefined.

- [ ] **Step 3: Add config struct and defaults**

In `config.go`, add `TaskSandbox` to `Config`:

```go
type Config struct {
	Agent       AgentConfig       `yaml:"agent"`
	Metrics     MetricsConfig     `yaml:"metrics"`
	Logging     LoggingConfig     `yaml:"logging"`
	Protocol    ProtocolConfig    `yaml:"protocol"`
	TaskSandbox TaskSandboxConfig `yaml:"task_sandbox"`
}
```

Add the struct:

```go
type TaskSandboxConfig struct {
	Enabled             bool   `yaml:"enabled"`
	Backend             string `yaml:"backend"`
	AllowLegacyFallback bool   `yaml:"allow_legacy_fallback"`
	MemoryMax           string `yaml:"memory_max"`
	CPUQuota            string `yaml:"cpu_quota"`
	TasksMax            int    `yaml:"tasks_max"`
	RuntimeMaxSec       int    `yaml:"runtime_max_sec"`
	UnitPrefix          string `yaml:"unit_prefix"`
}
```

In `loader.go`, call defaults after YAML unmarshal and before path normalization:

```go
	applyDefaults(&cfg)

	if err := normalizePaths(&cfg, filepath.Dir(path)); err != nil {
```

Add these helpers:

```go
func applyDefaults(cfg *Config) {
	if strings.TrimSpace(cfg.TaskSandbox.Backend) == "" {
		cfg.TaskSandbox.Backend = "direct"
	}
	if strings.TrimSpace(cfg.TaskSandbox.MemoryMax) == "" {
		cfg.TaskSandbox.MemoryMax = "1G"
	}
	if strings.TrimSpace(cfg.TaskSandbox.CPUQuota) == "" {
		cfg.TaskSandbox.CPUQuota = "100%"
	}
	if cfg.TaskSandbox.TasksMax <= 0 {
		cfg.TaskSandbox.TasksMax = 256
	}
	if cfg.TaskSandbox.RuntimeMaxSec <= 0 {
		cfg.TaskSandbox.RuntimeMaxSec = 1800
	}
	if strings.TrimSpace(cfg.TaskSandbox.UnitPrefix) == "" {
		cfg.TaskSandbox.UnitPrefix = "oneops-task"
	}
	cfg.TaskSandbox.Backend = strings.ToLower(strings.TrimSpace(cfg.TaskSandbox.Backend))
	cfg.TaskSandbox.MemoryMax = strings.TrimSpace(cfg.TaskSandbox.MemoryMax)
	cfg.TaskSandbox.CPUQuota = strings.TrimSpace(cfg.TaskSandbox.CPUQuota)
	cfg.TaskSandbox.UnitPrefix = strings.TrimSpace(cfg.TaskSandbox.UnitPrefix)
}
```

In `validate`, add:

```go
	if err := validateTaskSandbox(cfg.TaskSandbox); err != nil {
		return err
	}
```

Add:

```go
func validateTaskSandbox(cfg TaskSandboxConfig) error {
	switch cfg.Backend {
	case "direct", "systemd":
	default:
		return fmt.Errorf("task_sandbox.backend must be one of: direct|systemd")
	}
	if strings.TrimSpace(cfg.MemoryMax) == "" {
		return fmt.Errorf("task_sandbox.memory_max is required")
	}
	if strings.TrimSpace(cfg.CPUQuota) == "" {
		return fmt.Errorf("task_sandbox.cpu_quota is required")
	}
	if cfg.TasksMax <= 0 {
		return fmt.Errorf("task_sandbox.tasks_max must be > 0")
	}
	if cfg.RuntimeMaxSec <= 0 {
		return fmt.Errorf("task_sandbox.runtime_max_sec must be > 0")
	}
	if strings.TrimSpace(cfg.UnitPrefix) == "" {
		return fmt.Errorf("task_sandbox.unit_prefix is required")
	}
	return nil
}
```

- [ ] **Step 4: Run config tests to verify pass**

Run:

```bash
cd ctrlhub && go test ./controller/agent/pkg/config
```

Expected: PASS.

- [ ] **Step 5: Commit config task**

Run:

```bash
git add ctrlhub/controller/agent/pkg/config/config.go ctrlhub/controller/agent/pkg/config/loader.go ctrlhub/controller/agent/pkg/config/loader_test.go
git commit -m "feat(agent): add task sandbox config"
```

---

### Task 2: Add Sandbox Types and Direct Runner

**Files:**
- Create: `ctrlhub/controller/agent/cmd/agent/task_sandbox.go`
- Test: `ctrlhub/controller/agent/cmd/agent/task_sandbox_test.go`

- [ ] **Step 1: Write failing tests for unit names and direct runner**

Create `task_sandbox_test.go`:

```go
package main

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestSanitizeSystemdUnitName(t *testing.T) {
	got := sanitizeSystemdUnitName("oneops-task", "task/with spaces:and.symbols")
	want := "oneops-task-task-with-spaces-and.symbols.service"
	if got != want {
		t.Fatalf("unit name mismatch: got %q want %q", got, want)
	}
}

func TestDirectTaskSandboxRunnerRunsCommandAndStreamsOutput(t *testing.T) {
	root := t.TempDir()
	bin := filepath.Join(root, "bin")
	if err := os.MkdirAll(bin, 0o755); err != nil {
		t.Fatalf("mkdir bin: %v", err)
	}
	script := filepath.Join(bin, "demo")
	if err := os.WriteFile(script, []byte("#!/bin/sh\necho stdout-line\necho stderr-line >&2\n"), 0o755); err != nil {
		t.Fatalf("write script: %v", err)
	}

	var logs []string
	runner := NewDirectTaskSandboxRunner()
	result, err := runner.Run(context.Background(), SandboxRunRequest{
		TaskID:  "task-1",
		WorkDir: root,
		Command: script,
		LogLine: func(stream, line string) {
			logs = append(logs, stream+":"+line)
		},
	})
	if err != nil {
		t.Fatalf("run command: %v", err)
	}
	if result.SandboxName != "direct" || result.Duration <= 0 {
		t.Fatalf("unexpected result: %#v", result)
	}
	joined := strings.Join(logs, "\n")
	if !strings.Contains(joined, "stdout:stdout-line") || !strings.Contains(joined, "stderr:stderr-line") {
		t.Fatalf("expected streamed stdout and stderr, got %q", joined)
	}
	if !strings.Contains(result.Output, "stdout-line") || !strings.Contains(result.Output, "stderr-line") {
		t.Fatalf("expected output summary, got %q", result.Output)
	}
}

func TestDirectTaskSandboxRunnerCancellation(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	_, err := NewDirectTaskSandboxRunner().Run(ctx, SandboxRunRequest{
		TaskID:  "task-cancelled",
		WorkDir: t.TempDir(),
		Command: "sh",
		Args:    []string{"-c", "sleep 10"},
	})
	if err == nil || !strings.Contains(err.Error(), "TASK_CANCELLED") {
		t.Fatalf("expected cancellation error, got %v", err)
	}
}

func TestSandboxRunResultDurationIsSet(t *testing.T) {
	start := time.Now()
	result := SandboxRunResult{StartedAt: start, FinishedAt: start.Add(time.Second)}
	if result.Duration != 0 {
		t.Fatalf("raw struct should not precompute duration: %#v", result)
	}
}
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd ctrlhub && go test ./controller/agent/cmd/agent -run 'Test(SanitizeSystemdUnitName|DirectTaskSandboxRunner|SandboxRunResultDuration)' -count=1
```

Expected: FAIL because sandbox types are undefined.

- [ ] **Step 3: Create sandbox types and direct runner**

Create `task_sandbox.go`:

```go
package main

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"io"
	"os/exec"
	"regexp"
	"strings"
	"sync"
	"time"

	controllerTasks "github.com/netxops/ctrlhub/controller/pkg/tasks"
)

const (
	taskSandboxErrUnavailable = "TASK_SANDBOX_UNAVAILABLE"
	taskSandboxErrStartFailed = "TASK_SANDBOX_START_FAILED"
	taskSandboxErrLimitHit    = "TASK_SANDBOX_LIMIT_HIT"
	taskSandboxErrCancelled   = "TASK_CANCELLED"
	taskSandboxErrCommand     = "TASK_COMMAND_FAILED"
)

type TaskSandboxConfig struct {
	Enabled             bool
	Backend             string
	AllowLegacyFallback bool
	MemoryMax           string
	CPUQuota            string
	TasksMax            int
	RuntimeMaxSec       int
	UnitPrefix          string
}

type SandboxRunRequest struct {
	TaskID    string
	ProjectID string
	WorkDir   string
	Command   string
	Args      []string
	Env       []string
	Config    TaskSandboxConfig
	LogLine   func(stream, line string)
}

type SandboxRunResult struct {
	Output      string
	SandboxName string
	StartedAt   time.Time
	FinishedAt  time.Time
	Duration    time.Duration
}

type TaskSandboxRunner interface {
	Run(ctx context.Context, req SandboxRunRequest) (SandboxRunResult, error)
	Stop(ctx context.Context, taskID string) error
}

type execCommandContextFunc func(ctx context.Context, name string, args ...string) *exec.Cmd

type DirectTaskSandboxRunner struct {
	commandContext execCommandContextFunc
}

func NewDirectTaskSandboxRunner() *DirectTaskSandboxRunner {
	return &DirectTaskSandboxRunner{commandContext: exec.CommandContext}
}

func (r *DirectTaskSandboxRunner) Run(ctx context.Context, req SandboxRunRequest) (SandboxRunResult, error) {
	startedAt := time.Now()
	if r.commandContext == nil {
		r.commandContext = exec.CommandContext
	}
	cmd := r.commandContext(ctx, req.Command, req.Args...)
	cmd.Dir = req.WorkDir
	cmd.Env = controllerTasks.BuildTaskCommandEnv(req.Env, nil, nil)
	output, err := runCommandAndStream(ctx, cmd, req.LogLine)
	finishedAt := time.Now()
	result := SandboxRunResult{
		Output:      output,
		SandboxName: "direct",
		StartedAt:   startedAt,
		FinishedAt:  finishedAt,
		Duration:    finishedAt.Sub(startedAt),
	}
	if err != nil {
		if errors.Is(ctx.Err(), context.Canceled) {
			return result, fmt.Errorf("%s: task cancelled", taskSandboxErrCancelled)
		}
		return result, fmt.Errorf("%s: %w", taskSandboxErrCommand, err)
	}
	return result, nil
}

func (r *DirectTaskSandboxRunner) Stop(ctx context.Context, taskID string) error {
	_ = ctx
	_ = taskID
	return nil
}

func runCommandAndStream(ctx context.Context, cmd *exec.Cmd, logLine func(stream, line string)) (string, error) {
	stdoutPipe, err := cmd.StdoutPipe()
	if err != nil {
		return "", err
	}
	stderrPipe, err := cmd.StderrPipe()
	if err != nil {
		return "", err
	}
	if err := cmd.Start(); err != nil {
		return "", err
	}
	var outputMu sync.Mutex
	var outputLines []string
	appendLine := func(line string) {
		line = strings.TrimSpace(line)
		if line == "" {
			return
		}
		outputMu.Lock()
		outputLines = append(outputLines, line)
		outputMu.Unlock()
	}
	consumePipe := func(r io.ReadCloser, stream string) {
		defer r.Close()
		scanner := bufio.NewScanner(r)
		scanner.Buffer(make([]byte, 0, 1024), 1024*1024)
		for scanner.Scan() {
			line := scanner.Text()
			appendLine(line)
			if logLine != nil {
				logLine(stream, line)
			}
		}
		if scanErr := scanner.Err(); scanErr != nil && !isIgnorablePipeReadErr(scanErr) {
			appendLine(scanErr.Error())
			if logLine != nil {
				logLine(stream, scanErr.Error())
			}
		}
	}
	var wg sync.WaitGroup
	wg.Add(2)
	go func() {
		defer wg.Done()
		consumePipe(stdoutPipe, "stdout")
	}()
	go func() {
		defer wg.Done()
		consumePipe(stderrPipe, "stderr")
	}()
	waitErr := cmd.Wait()
	wg.Wait()
	output := strings.TrimSpace(strings.Join(outputLines, "\n"))
	if waitErr != nil {
		if errors.Is(ctx.Err(), context.Canceled) {
			return output, fmt.Errorf("%s: task cancelled", taskSandboxErrCancelled)
		}
		return output, waitErr
	}
	return output, nil
}

var invalidSystemdUnitChar = regexp.MustCompile(`[^A-Za-z0-9_.-]+`)

func sanitizeSystemdUnitName(prefix, taskID string) string {
	prefix = strings.TrimSpace(prefix)
	if prefix == "" {
		prefix = "oneops-task"
	}
	taskID = strings.TrimSpace(taskID)
	if taskID == "" {
		taskID = "unknown"
	}
	clean := invalidSystemdUnitChar.ReplaceAllString(taskID, "-")
	clean = strings.Trim(clean, "-.")
	if clean == "" {
		clean = "unknown"
	}
	name := prefix + "-" + clean
	if len(name) > 200 {
		name = name[:200]
	}
	return name + ".service"
}
```

- [ ] **Step 4: Run sandbox tests to verify pass**

Run:

```bash
cd ctrlhub && go test ./controller/agent/cmd/agent -run 'Test(SanitizeSystemdUnitName|DirectTaskSandboxRunner|SandboxRunResultDuration)' -count=1
```

Expected: PASS.

- [ ] **Step 5: Commit sandbox base**

Run:

```bash
git add ctrlhub/controller/agent/cmd/agent/task_sandbox.go ctrlhub/controller/agent/cmd/agent/task_sandbox_test.go
git commit -m "feat(agent): add task sandbox runner base"
```

---

### Task 3: Add Systemd Runner Command Construction

**Files:**
- Modify: `ctrlhub/controller/agent/cmd/agent/task_sandbox.go`
- Test: `ctrlhub/controller/agent/cmd/agent/task_sandbox_test.go`

- [ ] **Step 1: Write failing systemd argument tests**

Append tests:

```go
func TestBuildSystemdRunArgsIncludesLimitsCwdEnvAndCommand(t *testing.T) {
	req := SandboxRunRequest{
		TaskID:  "task-1",
		WorkDir: "/tmp/work dir",
		Command: "/bin/sh",
		Args:    []string{"-c", "echo ok"},
		Env:     []string{"FOO=bar", "EMPTY="},
		Config: TaskSandboxConfig{
			MemoryMax:     "2G",
			CPUQuota:      "150%",
			TasksMax:      128,
			RuntimeMaxSec: 600,
			UnitPrefix:    "oneops-rt",
		},
	}
	args, unitName := buildSystemdRunArgs(req)
	joined := strings.Join(args, "\n")
	if unitName != "oneops-rt-task-1.service" {
		t.Fatalf("unit name mismatch: %q", unitName)
	}
	for _, want := range []string{
		"--unit=oneops-rt-task-1.service",
		"--wait",
		"--collect",
		"--pipe",
		"--property=MemoryMax=2G",
		"--property=CPUQuota=150%",
		"--property=TasksMax=128",
		"--property=RuntimeMaxSec=600",
		"--property=KillMode=control-group",
		"--property=WorkingDirectory=/tmp/work dir",
		"--setenv=FOO=bar",
		"--setenv=EMPTY=",
		"/bin/sh",
		"-c",
		"echo ok",
	} {
		if !strings.Contains(joined, want) {
			t.Fatalf("expected args to contain %q, got %#v", want, args)
		}
	}
}

func TestSystemdTaskSandboxRunnerStopUsesSystemctl(t *testing.T) {
	var gotName string
	var gotArgs []string
	runner := NewSystemdTaskSandboxRunner()
	runner.commandContext = func(ctx context.Context, name string, args ...string) *exec.Cmd {
		gotName = name
		gotArgs = append([]string(nil), args...)
		return exec.CommandContext(ctx, "true")
	}
	runner.registerUnit("task-1", "oneops-task-task-1.service")
	if err := runner.Stop(context.Background(), "task-1"); err != nil {
		t.Fatalf("stop: %v", err)
	}
	if gotName != "systemctl" || strings.Join(gotArgs, " ") != "stop oneops-task-task-1.service" {
		t.Fatalf("unexpected stop command: %s %#v", gotName, gotArgs)
	}
}

type unavailableSandboxRunner struct{}

func (unavailableSandboxRunner) Run(ctx context.Context, req SandboxRunRequest) (SandboxRunResult, error) {
	return SandboxRunResult{}, fmt.Errorf("%s: missing systemd-run", taskSandboxErrUnavailable)
}

func (unavailableSandboxRunner) Stop(ctx context.Context, taskID string) error {
	return nil
}

func TestFallbackTaskSandboxRunnerUsesDirectRunnerOnlyForUnavailablePrimary(t *testing.T) {
	root := t.TempDir()
	script := filepath.Join(root, "demo.sh")
	if err := os.WriteFile(script, []byte("#!/bin/sh\necho fallback-ok\n"), 0o755); err != nil {
		t.Fatalf("write script: %v", err)
	}
	runner := &FallbackTaskSandboxRunner{
		primary:  unavailableSandboxRunner{},
		fallback: NewDirectTaskSandboxRunner(),
	}
	result, err := runner.Run(context.Background(), SandboxRunRequest{
		TaskID:  "task-fallback",
		WorkDir: root,
		Command: script,
	})
	if err != nil {
		t.Fatalf("fallback run: %v", err)
	}
	if !strings.Contains(result.Output, "fallback-ok") || result.SandboxName != "direct" {
		t.Fatalf("unexpected fallback result: %#v", result)
	}
}
```

Add `os/exec` to test imports.

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd ctrlhub && go test ./controller/agent/cmd/agent -run 'Test(BuildSystemdRunArgs|SystemdTaskSandboxRunnerStop|FallbackTaskSandboxRunner)' -count=1
```

Expected: FAIL because systemd helpers are undefined.

- [ ] **Step 3: Implement systemd runner**

Append to `task_sandbox.go`:

```go
type SystemdTaskSandboxRunner struct {
	commandContext execCommandContextFunc
	mu             sync.Mutex
	taskUnits      map[string]string
}

type FallbackTaskSandboxRunner struct {
	primary  TaskSandboxRunner
	fallback TaskSandboxRunner
}

func (r *FallbackTaskSandboxRunner) Run(ctx context.Context, req SandboxRunRequest) (SandboxRunResult, error) {
	result, err := r.primary.Run(ctx, req)
	if err == nil {
		return result, nil
	}
	if strings.Contains(err.Error(), taskSandboxErrUnavailable) {
		return r.fallback.Run(ctx, req)
	}
	return result, err
}

func (r *FallbackTaskSandboxRunner) Stop(ctx context.Context, taskID string) error {
	if r.primary != nil {
		return r.primary.Stop(ctx, taskID)
	}
	return nil
}

func NewSystemdTaskSandboxRunner() *SystemdTaskSandboxRunner {
	return &SystemdTaskSandboxRunner{
		commandContext: exec.CommandContext,
		taskUnits:      make(map[string]string),
	}
}

func (r *SystemdTaskSandboxRunner) Run(ctx context.Context, req SandboxRunRequest) (SandboxRunResult, error) {
	if r.commandContext == nil {
		r.commandContext = exec.CommandContext
	}
	if _, err := exec.LookPath("systemd-run"); err != nil {
		return SandboxRunResult{}, fmt.Errorf("%s: systemd-run not found: %w", taskSandboxErrUnavailable, err)
	}
	args, unitName := buildSystemdRunArgs(req)
	r.registerUnit(req.TaskID, unitName)
	defer r.unregisterUnit(req.TaskID)

	startedAt := time.Now()
	cmd := r.commandContext(ctx, "systemd-run", args...)
	output, err := runCommandAndStream(ctx, cmd, req.LogLine)
	finishedAt := time.Now()
	result := SandboxRunResult{
		Output:      output,
		SandboxName: unitName,
		StartedAt:   startedAt,
		FinishedAt:  finishedAt,
		Duration:    finishedAt.Sub(startedAt),
	}
	if err != nil {
		if errors.Is(ctx.Err(), context.Canceled) {
			return result, fmt.Errorf("%s: task cancelled", taskSandboxErrCancelled)
		}
		if strings.Contains(output, "Result: timeout") || strings.Contains(output, "runtime-max") {
			return result, fmt.Errorf("%s: %w", taskSandboxErrLimitHit, err)
		}
		return result, fmt.Errorf("%s: %w", taskSandboxErrCommand, err)
	}
	return result, nil
}

func (r *SystemdTaskSandboxRunner) Stop(ctx context.Context, taskID string) error {
	r.mu.Lock()
	unitName := r.taskUnits[taskID]
	r.mu.Unlock()
	if strings.TrimSpace(unitName) == "" {
		return fmt.Errorf("task not running: %s", taskID)
	}
	if r.commandContext == nil {
		r.commandContext = exec.CommandContext
	}
	cmd := r.commandContext(ctx, "systemctl", "stop", unitName)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("systemctl stop %s failed: %s", unitName, strings.TrimSpace(string(out)))
	}
	return nil
}

func (r *SystemdTaskSandboxRunner) registerUnit(taskID, unitName string) {
	r.mu.Lock()
	defer r.mu.Unlock()
	if r.taskUnits == nil {
		r.taskUnits = make(map[string]string)
	}
	r.taskUnits[taskID] = unitName
}

func (r *SystemdTaskSandboxRunner) unregisterUnit(taskID string) {
	r.mu.Lock()
	defer r.mu.Unlock()
	delete(r.taskUnits, taskID)
}

func buildSystemdRunArgs(req SandboxRunRequest) ([]string, string) {
	cfg := req.Config
	unitName := sanitizeSystemdUnitName(cfg.UnitPrefix, req.TaskID)
	args := []string{
		"--unit=" + unitName,
		"--wait",
		"--collect",
		"--pipe",
		"--property=MemoryMax=" + cfg.MemoryMax,
		"--property=CPUQuota=" + cfg.CPUQuota,
		fmt.Sprintf("--property=TasksMax=%d", cfg.TasksMax),
		fmt.Sprintf("--property=RuntimeMaxSec=%d", cfg.RuntimeMaxSec),
		"--property=KillMode=control-group",
		"--property=WorkingDirectory=" + req.WorkDir,
	}
	for _, item := range req.Env {
		if strings.TrimSpace(item) == "" {
			continue
		}
		args = append(args, "--setenv="+item)
	}
	args = append(args, req.Command)
	args = append(args, req.Args...)
	return args, unitName
}
```

- [ ] **Step 4: Run systemd unit tests**

Run:

```bash
cd ctrlhub && go test ./controller/agent/cmd/agent -run 'Test(BuildSystemdRunArgs|SystemdTaskSandboxRunnerStop|FallbackTaskSandboxRunner)' -count=1
```

Expected: PASS.

- [ ] **Step 5: Commit systemd runner**

Run:

```bash
git add ctrlhub/controller/agent/cmd/agent/task_sandbox.go ctrlhub/controller/agent/cmd/agent/task_sandbox_test.go
git commit -m "feat(agent): add systemd task sandbox runner"
```

---

### Task 4: Wire Sandbox Runner Into AgentService

**Files:**
- Modify: `ctrlhub/controller/agent/cmd/agent/main.go`
- Modify: `ctrlhub/controller/agent/cmd/agent/agent_service.go`
- Modify: `ctrlhub/controller/agent/cmd/agent/agent_service_task_runner_test.go`
- Test: `ctrlhub/controller/agent/cmd/agent/agent_service_task_runner_test.go`

- [ ] **Step 1: Write fake runner and delegation test**

Add to `agent_service_task_runner_test.go`:

```go
type fakeTaskSandboxRunner struct {
	requests []SandboxRunRequest
	stopIDs  []string
	output   string
	err      error
}

func (f *fakeTaskSandboxRunner) Run(ctx context.Context, req SandboxRunRequest) (SandboxRunResult, error) {
	f.requests = append(f.requests, req)
	return SandboxRunResult{Output: f.output, SandboxName: "fake", StartedAt: time.Now(), FinishedAt: time.Now(), Duration: time.Millisecond}, f.err
}

func (f *fakeTaskSandboxRunner) Stop(ctx context.Context, taskID string) error {
	f.stopIDs = append(f.stopIDs, taskID)
	return f.err
}

func TestRunShellTaskDelegatesToSandboxRunner(t *testing.T) {
	root := t.TempDir()
	workDir := filepath.Join(root, "work")
	if err := os.MkdirAll(workDir, 0o755); err != nil {
		t.Fatalf("mkdir work dir: %v", err)
	}
	fake := &fakeTaskSandboxRunner{output: "ok"}
	as := &AgentService{logger: zap.NewNop(), taskSandboxRunner: fake}

	output, err := as.runShellTask(context.Background(), "task-1", "project-1", workDir, "", `["echo","hello"]`, nil)
	if err != nil {
		t.Fatalf("run shell: %v", err)
	}
	if output != "ok" {
		t.Fatalf("output mismatch: %q", output)
	}
	if len(fake.requests) != 1 {
		t.Fatalf("expected one sandbox request, got %d", len(fake.requests))
	}
	req := fake.requests[0]
	if req.TaskID != "task-1" || req.ProjectID != "project-1" || req.WorkDir != workDir || req.Command != "echo" || strings.Join(req.Args, " ") != "hello" {
		t.Fatalf("unexpected request: %#v", req)
	}
}
```

Add `time` to test imports.

- [ ] **Step 2: Run delegation test to verify failure**

Run:

```bash
cd ctrlhub && go test ./controller/agent/cmd/agent -run TestRunShellTaskDelegatesToSandboxRunner -count=1
```

Expected: FAIL because `AgentService.taskSandboxRunner` is undefined or direct execution still happens.

- [ ] **Step 3: Add runtime config to `AgentConfig` and config mapping**

In `main.go`, add to package-main `AgentConfig`:

```go
	TaskSandbox TaskSandboxConfig
```

In `buildBidiAgentConfig`, add:

```go
		TaskSandbox: TaskSandboxConfig{
			Enabled:             cfg.TaskSandbox.Enabled,
			Backend:             cfg.TaskSandbox.Backend,
			AllowLegacyFallback: cfg.TaskSandbox.AllowLegacyFallback,
			MemoryMax:           cfg.TaskSandbox.MemoryMax,
			CPUQuota:            cfg.TaskSandbox.CPUQuota,
			TasksMax:            cfg.TaskSandbox.TasksMax,
			RuntimeMaxSec:       cfg.TaskSandbox.RuntimeMaxSec,
			UnitPrefix:          cfg.TaskSandbox.UnitPrefix,
		},
```

- [ ] **Step 4: Add runner selection to AgentService**

In `AgentService`, add fields:

```go
	taskSandboxRunner TaskSandboxRunner
	taskSandboxConfig TaskSandboxConfig
```

In `NewAgentService`, initialize:

```go
		taskSandboxConfig: config.TaskSandbox,
```

Then after `agent := &AgentService{...}`, set:

```go
	agent.taskSandboxRunner = newTaskSandboxRunner(config.TaskSandbox)
```

Add helper to `task_sandbox.go`:

```go
func newTaskSandboxRunner(cfg TaskSandboxConfig) TaskSandboxRunner {
	if !cfg.Enabled || cfg.Backend == "direct" {
		return NewDirectTaskSandboxRunner()
	}
	if cfg.Backend == "systemd" {
		systemdRunner := NewSystemdTaskSandboxRunner()
		if cfg.AllowLegacyFallback {
			return &FallbackTaskSandboxRunner{
				primary:  systemdRunner,
				fallback: NewDirectTaskSandboxRunner(),
			}
		}
		return systemdRunner
	}
	return NewDirectTaskSandboxRunner()
}
```

- [ ] **Step 5: Delegate final command execution**

Replace body of `runCommandWithStreamingReportEnv` in `agent_service.go` with:

```go
func (as *AgentService) runCommandWithStreamingReportEnv(
	ctx context.Context, taskID, projectID, workDir string, env []string, executionProfile *controllerTasks.TaskExecutionProfile, name string, args ...string,
) (string, error) {
	startedAt := time.Now()
	as.reportTaskLifecycleLog(ctx, taskID, projectID, "INFO", "启动进程: command=%s arg_count=%d cwd=%s", filepath.Base(name), len(args), workDir)
	runner := as.taskSandboxRunner
	if runner == nil {
		runner = NewDirectTaskSandboxRunner()
	}
	result, err := runner.Run(ctx, SandboxRunRequest{
		TaskID:    taskID,
		ProjectID: projectID,
		WorkDir:   workDir,
		Command:   name,
		Args:      append([]string(nil), args...),
		Env:       controllerTasks.BuildTaskCommandEnv(env, nil, executionProfile),
		Config:    as.taskSandboxConfig,
		LogLine: func(stream, line string) {
			as.reportTaskLog(ctx, taskID, projectID, controllerTasks.InferTaskLogLevel(stream, line), line)
		},
	})
	if err != nil {
		as.reportTaskLifecycleLog(ctx, taskID, projectID, "ERROR", "进程退出失败: command=%s sandbox=%s duration=%s error=%v", filepath.Base(name), result.SandboxName, time.Since(startedAt).Round(time.Millisecond), err)
		return result.Output, err
	}
	as.reportTaskLifecycleLog(ctx, taskID, projectID, "INFO", "进程执行完成: command=%s sandbox=%s duration=%s", filepath.Base(name), result.SandboxName, time.Since(startedAt).Round(time.Millisecond))
	return result.Output, nil
}
```

Remove unused imports from `agent_service.go`: `bufio`, `io`, and `os/exec` if they are no longer used in that file. Keep `os/exec` if `prepareTaskWorkspace` still uses it for git.

- [ ] **Step 6: Run delegation test**

Run:

```bash
cd ctrlhub && go test ./controller/agent/cmd/agent -run TestRunShellTaskDelegatesToSandboxRunner -count=1
```

Expected: PASS.

- [ ] **Step 7: Run existing task runner tests**

Run:

```bash
cd ctrlhub && go test ./controller/agent/cmd/agent -run 'TestRun(TerraformFamilyTask|ShellTask)|TestHandleRunTask|TestPrepareTaskWorkspace' -count=1
```

Expected: PASS.

- [ ] **Step 8: Commit service wiring**

Run:

```bash
git add ctrlhub/controller/agent/cmd/agent/main.go ctrlhub/controller/agent/cmd/agent/agent_service.go ctrlhub/controller/agent/cmd/agent/task_sandbox.go ctrlhub/controller/agent/cmd/agent/agent_service_task_runner_test.go
git commit -m "feat(agent): route runtask execution through sandbox runner"
```

---

### Task 5: Stop Sandboxed Tasks

**Files:**
- Modify: `ctrlhub/controller/agent/cmd/agent/agent_service.go`
- Test: `ctrlhub/controller/agent/cmd/agent/agent_service_task_runner_test.go`

- [ ] **Step 1: Write failing StopTask test**

Add:

```go
func TestHandleStopTaskStopsSandboxRunnerAndCancelsContext(t *testing.T) {
	fake := &fakeTaskSandboxRunner{}
	as := &AgentService{
		logger:             zap.NewNop(),
		taskSandboxRunner:  fake,
		runningTaskCancels: make(map[string]context.CancelFunc),
	}
	ctx, cancel := context.WithCancel(context.Background())
	as.runningTaskCancels["task-1"] = cancel

	resp, err := as.handleStopTask(ctx, map[string]interface{}{"task_id": "task-1"})
	if err != nil {
		t.Fatalf("handle stop: %v", err)
	}
	if resp["code"] != 200 || resp["message"] != "stopping" {
		t.Fatalf("unexpected response: %#v", resp)
	}
	if len(fake.stopIDs) != 1 || fake.stopIDs[0] != "task-1" {
		t.Fatalf("expected sandbox stop, got %#v", fake.stopIDs)
	}
	select {
	case <-ctx.Done():
		t.Fatalf("parent context should not be cancelled")
	default:
	}
}
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
cd ctrlhub && go test ./controller/agent/cmd/agent -run TestHandleStopTaskStopsSandboxRunnerAndCancelsContext -count=1
```

Expected: FAIL because `handleStopTask` only cancels context.

- [ ] **Step 3: Update `handleStopTask`**

Modify the success path:

```go
	cancel()
	if as.taskSandboxRunner != nil {
		if err := as.taskSandboxRunner.Stop(context.Background(), taskID); err != nil {
			as.logger.Warn("停止任务 sandbox 失败", zap.String("task_id", taskID), zap.Error(err))
		}
	}
	return map[string]interface{}{
		"code":    200,
		"message": "stopping",
		"task_id": taskID,
	}, nil
```

- [ ] **Step 4: Run StopTask tests**

Run:

```bash
cd ctrlhub && go test ./controller/agent/cmd/agent -run 'TestHandleStopTask' -count=1
```

Expected: PASS.

- [ ] **Step 5: Commit stop behavior**

Run:

```bash
git add ctrlhub/controller/agent/cmd/agent/agent_service.go ctrlhub/controller/agent/cmd/agent/agent_service_task_runner_test.go
git commit -m "feat(agent): stop sandboxed runtask processes"
```

---

### Task 6: Config Files and Deployment Templates

**Files:**
- Modify: `ctrlhub/controller/agent/configs/agent.yaml`
- Modify: `ctrlhub/controller/deploy/agent.yaml.template`
- Modify: `ctrlhub/controller/deploy/agent.root.example.yaml`
- Modify: `ctrlhub/controller/deploy/agent.unprivileged.example.yaml`

- [ ] **Step 1: Update local agent config**

Add to `ctrlhub/controller/agent/configs/agent.yaml` after `protocol`:

```yaml
task_sandbox:
  enabled: false
  backend: direct
  allow_legacy_fallback: false
  memory_max: 1G
  cpu_quota: 100%
  tasks_max: 256
  runtime_max_sec: 1800
  unit_prefix: oneops-task
```

- [ ] **Step 2: Update deployment template**

Add to `ctrlhub/controller/deploy/agent.yaml.template` after `protocol`:

```yaml
task_sandbox:
  enabled: {{ .task_sandbox_enabled }}
  backend: "{{ .task_sandbox_backend }}"
  allow_legacy_fallback: {{ .task_sandbox_allow_legacy_fallback }}
  memory_max: "{{ .task_sandbox_memory_max }}"
  cpu_quota: "{{ .task_sandbox_cpu_quota }}"
  tasks_max: {{ .task_sandbox_tasks_max }}
  runtime_max_sec: {{ .task_sandbox_runtime_max_sec }}
  unit_prefix: "{{ .task_sandbox_unit_prefix }}"
```

- [ ] **Step 3: Update example configs**

Add to both example YAML files:

```yaml
task_sandbox:
  enabled: true
  backend: systemd
  allow_legacy_fallback: false
  memory_max: 1G
  cpu_quota: 100%
  tasks_max: 256
  runtime_max_sec: 1800
  unit_prefix: oneops-task
```

- [ ] **Step 4: Run config load tests**

Run:

```bash
cd ctrlhub && go test ./controller/agent/pkg/config
```

Expected: PASS.

- [ ] **Step 5: Commit templates**

Run:

```bash
git add ctrlhub/controller/agent/configs/agent.yaml ctrlhub/controller/deploy/agent.yaml.template ctrlhub/controller/deploy/agent.root.example.yaml ctrlhub/controller/deploy/agent.unprivileged.example.yaml
git commit -m "chore(agent): document task sandbox config"
```

---

### Task 7: Add Real Systemd Smoke Script

**Files:**
- Create: `ctrlhub/scripts/agent_runtask_systemd_sandbox_smoke.sh`

- [ ] **Step 1: Create smoke script**

Create:

```bash
#!/usr/bin/env bash
set -euo pipefail

if [[ "${ONEOPS_AGENT_SYSTEMD_SANDBOX_SMOKE:-}" != "1" ]]; then
  echo "skip: set ONEOPS_AGENT_SYSTEMD_SANDBOX_SMOKE=1 to run real systemd sandbox smoke"
  exit 0
fi

if ! command -v systemd-run >/dev/null 2>&1; then
  echo "systemd-run not found" >&2
  exit 1
fi

unit="oneops-task-smoke-$(date +%s)"
systemd-run \
  --unit="${unit}" \
  --wait \
  --collect \
  --pipe \
  --property=MemoryMax=128M \
  --property=CPUQuota=50% \
  --property=TasksMax=32 \
  --property=RuntimeMaxSec=10 \
  --property=KillMode=control-group \
  --property=WorkingDirectory=/tmp \
  /bin/sh -c 'echo oneops-systemd-sandbox-ok'

if systemctl list-units --all --no-legend "${unit}.service" | grep -q "${unit}.service"; then
  echo "unit still present after --collect: ${unit}.service" >&2
  exit 1
fi

echo "ok: systemd sandbox smoke passed"
```

- [ ] **Step 2: Make script executable**

Run:

```bash
chmod +x ctrlhub/scripts/agent_runtask_systemd_sandbox_smoke.sh
```

- [ ] **Step 3: Run skipped smoke**

Run:

```bash
ctrlhub/scripts/agent_runtask_systemd_sandbox_smoke.sh
```

Expected: PASS with skip message.

- [ ] **Step 4: Commit smoke script**

Run:

```bash
git add ctrlhub/scripts/agent_runtask_systemd_sandbox_smoke.sh
git commit -m "test(agent): add systemd sandbox smoke script"
```

---

### Task 8: Final Verification

**Files:**
- No new files.

- [ ] **Step 1: Run focused config tests**

Run:

```bash
cd ctrlhub && go test ./controller/agent/pkg/config
```

Expected: PASS.

- [ ] **Step 2: Run focused agent tests**

Run:

```bash
cd ctrlhub && go test ./controller/agent/cmd/agent -run 'Test(SanitizeSystemdUnitName|DirectTaskSandboxRunner|BuildSystemdRunArgs|SystemdTaskSandboxRunnerStop|FallbackTaskSandboxRunner|RunShellTaskDelegatesToSandboxRunner|HandleStopTask|RunTerraformFamilyTask|RunShellTask|HandleRunTask|PrepareTaskWorkspace)' -count=1
```

Expected: PASS.

- [ ] **Step 3: Run full agent package tests**

Run:

```bash
cd ctrlhub && go test ./controller/agent/cmd/agent ./controller/agent/pkg/config
```

Expected: PASS.

- [ ] **Step 4: Run skipped smoke script**

Run:

```bash
ctrlhub/scripts/agent_runtask_systemd_sandbox_smoke.sh
```

Expected: PASS with skip message unless `ONEOPS_AGENT_SYSTEMD_SANDBOX_SMOKE=1` is set.

- [ ] **Step 5: Inspect diff**

Run:

```bash
git diff --stat HEAD
git diff --check
```

Expected: `git diff --check` has no whitespace errors.

- [ ] **Step 6: Commit verification notes if any files changed**

If Task 8 required no edits, do not commit. If verification exposed a defect, return to the task that owns the edited file, apply the fix there, rerun that task's verification command, and use that task's commit command.

---

## Plan Self-Review

- Spec coverage: config, direct fallback, systemd transient service, resource limits, stop behavior, tests, deployment examples, and smoke verification are covered by Tasks 1-8.
- Scope: this plan isolates `RunTask` only. Telegraf plugin isolation, container backends, Controller policy redesign, and file RPC whitelisting remain outside this implementation.
- Type consistency: `TaskSandboxConfig`, `TaskSandboxRunner`, `SandboxRunRequest`, and `SandboxRunResult` are introduced before use. `AgentService.taskSandboxRunner` and `AgentService.taskSandboxConfig` are wired before tests depend on them.
