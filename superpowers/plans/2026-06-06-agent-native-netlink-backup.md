# Agent Native Netlink Backup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an agent-native network configuration backup path that uses netlink as a Go library instead of requiring a separately deployed `netlink-backup` CLI.

**Architecture:** First extract the existing `netlink/cmd/netlink-backup` behavior into a reusable netlink package. Then add a new ctrlhub agent `app_type=network_config_backup` runner that calls the package, writes OneOPS runtime artifacts, and reuses the existing task credential and artifact upload flow.

**Tech Stack:** Go, ctrlhub agent RunTask, github.com/netxops/netlink, OneOPS runtime artifact manifest, existing task execution profile credential resolution.

---

## File Structure

- Create `netlink/backup/backup.go`: reusable backup request/result API and execution logic.
- Create `netlink/backup/backup_test.go`: offline tests for option normalization, default commands, mode config file mapping, and validation.
- Modify `netlink/cmd/netlink-backup/main.go`: keep CLI behavior, delegate execution to `backup.Execute`.
- Modify `ctrlhub/controller/pkg/tasks/types.go`: add `AppTypeNetworkConfigBackup`.
- Create `ctrlhub/controller/agent/cmd/agent/netlink_backup_runner.go`: parse task input, call netlink backup package, write artifacts and manifest.
- Create `ctrlhub/controller/agent/cmd/agent/netlink_backup_runner_test.go`: offline agent runner tests with a fake backup executor.
- Modify `ctrlhub/controller/agent/cmd/agent/agent_service.go`: route `app_type=network_config_backup` to the native runner.
- Modify `ctrlhub/go.mod` and `ctrlhub/go.sum`: bump `github.com/netxops/netlink` after the netlink package is tagged.

## Task 1: Extract netlink backup package

**Files:**
- Create: `netlink/backup/backup.go`
- Create: `netlink/backup/backup_test.go`
- Modify: `netlink/cmd/netlink-backup/main.go`

- [ ] **Step 1: Write package tests**

Create `netlink/backup/backup_test.go`:

```go
package backup

import "testing"

func TestNormalizeMode(t *testing.T) {
	tests := map[string]string{
		"huawei":        "huawei_vrp",
		"huawei-vrp":    "huawei_vrp",
		"vrp":           "huawei_vrp",
		"huawei_usg":    "huawei_usg",
		"h3c":           "h3c_comware",
		"comware":       "h3c_comware",
		"h3c_secpath":   "h3c_secpath",
		"secpath":       "h3c_secpath",
		"maipu":         "maipu_mypower",
		"maipu-mypower": "maipu_mypower",
	}
	for input, want := range tests {
		if got := NormalizeMode(input); got != want {
			t.Fatalf("NormalizeMode(%q)=%q, want %q", input, got, want)
		}
	}
}

func TestDefaultCommandForMode(t *testing.T) {
	tests := map[string]string{
		"huawei_vrp":   "display current-configuration",
		"huawei_usg":   "display current-configuration",
		"h3c_comware":  "display current-configuration",
		"h3c_secpath":  "display current-configuration",
		"maipu_mypower": "show run",
	}
	for mode, want := range tests {
		got, err := DefaultCommandForMode(mode)
		if err != nil {
			t.Fatalf("DefaultCommandForMode(%q) returned error: %v", mode, err)
		}
		if got != want {
			t.Fatalf("DefaultCommandForMode(%q)=%q, want %q", mode, got, want)
		}
	}
}

func TestResolveRequestDefaultsAuthPassToPassword(t *testing.T) {
	req := Request{
		Host:     "172.21.253.9",
		Username: "netmanager",
		Password: "login-pass",
		Mode:     "maipu",
	}
	got, err := ResolveRequest(req)
	if err != nil {
		t.Fatalf("ResolveRequest returned error: %v", err)
	}
	if got.Mode != "maipu_mypower" {
		t.Fatalf("mode=%q", got.Mode)
	}
	if got.Command != "show run" {
		t.Fatalf("command=%q", got.Command)
	}
	if got.AuthPass != "login-pass" {
		t.Fatalf("auth_pass=%q", got.AuthPass)
	}
	if got.Port != 22 || got.LoginTimeout != 30 || got.CommandTimeout != 180 || got.NoOutputTimeout != 15 {
		t.Fatalf("unexpected defaults: %#v", got)
	}
}

func TestResolveRequestRequiresCredential(t *testing.T) {
	_, err := ResolveRequest(Request{
		Host:     "172.21.253.9",
		Username: "netmanager",
		Mode:     "maipu",
	})
	if err == nil {
		t.Fatalf("expected credential validation error")
	}
}
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
cd /OneOPS/netlink
go test ./backup -count=1
```

Expected: FAIL because package `backup` and its exported types/functions do not exist yet.

- [ ] **Step 3: Implement package API**

Create `netlink/backup/backup.go` by moving the reusable logic out of `cmd/netlink-backup/main.go`. The public API should look like this:

```go
package backup

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/netxops/netlink/dispatch"
	"github.com/netxops/netlink/netdevice"
	"github.com/netxops/netlink/structs"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
	"gopkg.in/yaml.v2"
)

const (
	DefaultPort            = 22
	DefaultLoginTimeout    = 30
	DefaultCommandTimeout  = 180
	DefaultNoOutputTimeout = 15
)

type Request struct {
	Host            string
	Port            int
	Username        string
	Password        string
	PrivateKey      string
	AuthPass        string
	Mode            string
	Command         string
	Output          string
	ConfigDir       string
	LoginTimeout    int
	CommandTimeout  int
	NoOutputTimeout int
	Verbose         bool
}

type Result struct {
	Output         string
	Command        string
	Mode           string
	ModeConfigPath string
	HubConfigPath  string
	Size           int64
	Duration       time.Duration
}

type resolvedConfig struct {
	ModeConfigPath string
	HubConfigPath  string
	ModeConfig     *structs.ModeConfig
	HubConfig      *structs.HubConfig
}

func Execute(ctx context.Context, req Request, logger *zap.Logger) (*Result, error) {
	start := time.Now()
	resolved, err := ResolveRequest(req)
	if err != nil {
		return nil, err
	}
	cfg, err := LoadResolvedConfig(resolved)
	if err != nil {
		return nil, err
	}
	if logger == nil {
		logger, err = NewLogger(resolved.Verbose)
		if err != nil {
			return nil, err
		}
		defer logger.Sync() //nolint:errcheck
	}
	base := &dispatch.BaseInfo{
		Host:            resolved.Host,
		Port:            resolved.Port,
		Username:        resolved.Username,
		Password:        resolved.Password,
		PrivateKey:      resolved.PrivateKey,
		AuthPass:        resolved.AuthPass,
		IsPty:           true,
		DispatchTimeOut: resolved.LoginTimeout,
		DailTimeout:     resolved.LoginTimeout,
	}
	device, err := netdevice.NewBaseNetworkDevice(base, cfg.ModeConfig, cfg.HubConfig, logger)
	if err != nil {
		return nil, err
	}
	defer device.Close() //nolint:errcheck

	loginCtx, cancelLogin := device.BuildLoginCtx(resolved.NoOutputTimeout, resolved.LoginTimeout)
	if ctx != nil {
		var cancel context.CancelFunc
		loginCtx, cancel = context.WithCancel(loginCtx)
		go func() {
			select {
			case <-ctx.Done():
				cancel()
			case <-loginCtx.Done():
			}
		}()
		defer cancel()
	}
	if err := device.LoginAndInit(loginCtx); err != nil {
		cancelLogin()
		return nil, err
	}
	cancelLogin()

	commandCtx := context.WithValue(context.Background(), "noOutputTimeout", resolved.NoOutputTimeout)
	if ctx != nil {
		commandCtx = context.WithValue(ctx, "noOutputTimeout", resolved.NoOutputTimeout)
	}
	commandCtx, cancelCommand := context.WithTimeout(commandCtx, time.Duration(resolved.CommandTimeout)*time.Second)
	defer cancelCommand()

	output, err := device.ExecuteCommand(commandCtx, resolved.Command)
	if err != nil {
		return nil, err
	}
	if err := WriteOutput(resolved.Output, output); err != nil {
		return nil, err
	}
	return &Result{
		Output:         output,
		Command:        resolved.Command,
		Mode:           resolved.Mode,
		ModeConfigPath: cfg.ModeConfigPath,
		HubConfigPath:  cfg.HubConfigPath,
		Size:           int64(len([]byte(output))),
		Duration:       time.Since(start),
	}, nil
}
```

Move the helper functions from `cmd/netlink-backup/main.go` into this package and export the functions used by tests:

```go
func ResolveRequest(req Request) (Request, error)
func NormalizeMode(mode string) string
func DefaultCommandForMode(mode string) (string, error)
func ModeConfigFile(mode string) (string, error)
func LoadResolvedConfig(req Request) (*resolvedConfig, error)
func ResolveConfigDir(flagValue string) string
func WriteOutput(path, output string) error
func NewLogger(verbose bool) (*zap.Logger, error)
```

- [ ] **Step 4: Make CLI delegate to package**

Replace `netlink/cmd/netlink-backup/main.go` with a thin wrapper:

```go
package main

import (
	"context"
	"flag"
	"fmt"
	"os"

	"github.com/netxops/netlink/backup"
)

func main() {
	opts := parseFlags(os.Args[1:])
	if _, err := backup.Execute(context.Background(), opts, nil); err != nil {
		fmt.Fprintf(os.Stderr, "netlink-backup: %v\n", err)
		os.Exit(1)
	}
}

func parseFlags(args []string) backup.Request {
	fs := flag.NewFlagSet("netlink-backup", flag.ExitOnError)
	opts := backup.Request{}
	fs.StringVar(&opts.Host, "host", "", "target host or IP")
	fs.IntVar(&opts.Port, "port", backup.DefaultPort, "target SSH port")
	fs.StringVar(&opts.Username, "username", "", "login username")
	fs.StringVar(&opts.Password, "password", "", "login password; prefer NETLINK_BACKUP_PASSWORD")
	fs.StringVar(&opts.PrivateKey, "private-key", "", "private key content or path")
	fs.StringVar(&opts.AuthPass, "auth-pass", "", "enable/auth password; prefer NETLINK_BACKUP_AUTH_PASS")
	fs.StringVar(&opts.Mode, "mode", "", "device mode, for example huawei_vrp, h3c_comware, maipu_mypower")
	fs.StringVar(&opts.Command, "command", "", "backup command; defaults by mode")
	fs.StringVar(&opts.Output, "output", "", "output file path; stdout when empty")
	fs.StringVar(&opts.ConfigDir, "config-dir", "", "netlink configs directory")
	fs.IntVar(&opts.LoginTimeout, "login-timeout", backup.DefaultLoginTimeout, "login timeout seconds")
	fs.IntVar(&opts.CommandTimeout, "command-timeout", backup.DefaultCommandTimeout, "command timeout seconds")
	fs.IntVar(&opts.NoOutputTimeout, "no-output-timeout", backup.DefaultNoOutputTimeout, "no-output timeout seconds")
	fs.BoolVar(&opts.Verbose, "verbose", false, "enable debug logging")
	_ = fs.Parse(args)
	return opts
}
```

- [ ] **Step 5: Run netlink tests**

Run:

```bash
cd /OneOPS/netlink
gofmt -w backup/backup.go backup/backup_test.go cmd/netlink-backup/main.go
go test ./backup ./cmd/netlink-backup -count=1
go test ./netdevice ./dispatch -count=1
```

Expected: all tests pass.

- [ ] **Step 6: Commit and tag netlink**

Run:

```bash
cd /OneOPS/netlink
git status --short
git add backup/backup.go backup/backup_test.go cmd/netlink-backup/main.go
git commit -m "add reusable netlink backup package"
git tag v0.1.11
git push origin main
git push origin v0.1.11
```

Expected: commit and tag are pushed. If `v0.1.11` already exists, choose the next patch tag and use that exact tag in Task 3.

## Task 2: Add ctrlhub task type constant

**Files:**
- Modify: `ctrlhub/controller/pkg/tasks/types.go`
- Modify: `ctrlhub/controller/pkg/tasks/runner_test.go`

- [ ] **Step 1: Add failing test for app type identity**

Append this test to `ctrlhub/controller/pkg/tasks/runner_test.go`:

```go
func TestAppTypeNetworkConfigBackupConstant(t *testing.T) {
	if AppTypeNetworkConfigBackup != "network_config_backup" {
		t.Fatalf("unexpected network backup app type: %q", AppTypeNetworkConfigBackup)
	}
}
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
cd /OneOPS/ctrlhub
go test ./controller/pkg/tasks -run TestAppTypeNetworkConfigBackupConstant -count=1
```

Expected: FAIL because `AppTypeNetworkConfigBackup` is undefined.

- [ ] **Step 3: Add the constant**

Modify `ctrlhub/controller/pkg/tasks/types.go`:

```go
const (
	AppTypeAnsible             = "ansible"
	AppTypeShell               = "shell"
	AppTypeTerraform           = "terraform"
	AppTypeTofu                = "tofu"
	AppTypeTerragrunt          = "terragrunt"
	AppTypeNetworkConfigBackup = "network_config_backup"
)
```

- [ ] **Step 4: Run tests**

Run:

```bash
cd /OneOPS/ctrlhub
gofmt -w controller/pkg/tasks/types.go controller/pkg/tasks/runner_test.go
go test ./controller/pkg/tasks -count=1
```

Expected: PASS.

## Task 3: Add agent-native netlink backup runner

**Files:**
- Create: `ctrlhub/controller/agent/cmd/agent/netlink_backup_runner.go`
- Create: `ctrlhub/controller/agent/cmd/agent/netlink_backup_runner_test.go`
- Modify: `ctrlhub/go.mod`
- Modify: `ctrlhub/go.sum`

- [ ] **Step 1: Upgrade ctrlhub netlink dependency**

Use the tag from Task 1:

```bash
cd /OneOPS/ctrlhub
go get github.com/netxops/netlink@v0.1.11
go mod tidy
```

Expected: `go.mod` references the new netlink tag.

- [ ] **Step 2: Write runner tests with fake executor**

Create `ctrlhub/controller/agent/cmd/agent/netlink_backup_runner_test.go`:

```go
package main

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	controllerTasks "github.com/netxops/ctrlhub/controller/pkg/tasks"
	"github.com/netxops/netlink/backup"
)

func TestRunNativeNetlinkBackupWritesArtifacts(t *testing.T) {
	workDir := t.TempDir()
	env, err := buildTaskRuntimeContractEnv(workDir)
	if err != nil {
		t.Fatalf("build runtime env: %v", err)
	}
	runner := nativeNetlinkBackupRunner{
		exec: func(ctx context.Context, req backup.Request) (*backup.Result, error) {
			if req.Host != "172.21.253.9" {
				t.Fatalf("host=%q", req.Host)
			}
			if req.Username != "netmanager" {
				t.Fatalf("username=%q", req.Username)
			}
			if req.Password != "secret" {
				t.Fatalf("password not propagated")
			}
			if req.AuthPass != "enable-secret" {
				t.Fatalf("auth pass not propagated")
			}
			if req.Mode != "maipu" {
				t.Fatalf("mode=%q", req.Mode)
			}
			if req.Command != "show run" {
				t.Fatalf("command=%q", req.Command)
			}
			return &backup.Result{
				Output:  "hostname SH-HAP-ZJIDC-EXT-MSW-MAIPU-S4320-1\n",
				Command: req.Command,
				Mode:    "maipu_mypower",
				Size:    47,
			}, nil
		},
	}
	extraVars, _ := json.Marshal(map[string]interface{}{
		"target_host":            "172.21.253.9",
		"vendor_family":          "maipu",
		"network_backup_command": "show run",
		"network_backup_tag":     "native-test",
	})
	output, err := runner.run(context.Background(), nativeNetlinkBackupTask{
		TaskID:        "task-1",
		ControllerID:  "controller-1",
		WorkDir:       workDir,
		RuntimeEnv:    env,
		ExtraVarsJSON: string(extraVars),
		Credential: taskCredential{
			Username: "netmanager",
			Password: "secret",
			AuthPass: "enable-secret",
		},
	})
	if err != nil {
		t.Fatalf("run returned error: %v", err)
	}
	if output == "" {
		t.Fatalf("expected output summary")
	}
	manifestBytes, err := os.ReadFile(env["ONEOPS_ARTIFACT_MANIFEST"])
	if err != nil {
		t.Fatalf("read manifest: %v", err)
	}
	var manifest taskRuntimeArtifactManifest
	if err := json.Unmarshal(manifestBytes, &manifest); err != nil {
		t.Fatalf("unmarshal manifest: %v", err)
	}
	if len(manifest.Artifacts) != 2 {
		t.Fatalf("expected 2 artifacts, got %#v", manifest.Artifacts)
	}
	cfgPath := filepath.Join(env["ONEOPS_OUTPUT_DIR"], "network-config-backup-172-21-253-9.cfg")
	if _, err := os.Stat(cfgPath); err != nil {
		t.Fatalf("expected config artifact: %v", err)
	}
	if !manifest.Artifacts[0].Sensitive {
		t.Fatalf("config artifact must be sensitive")
	}
}

func TestRunNativeNetlinkBackupRequiresCredential(t *testing.T) {
	runner := nativeNetlinkBackupRunner{
		exec: func(ctx context.Context, req backup.Request) (*backup.Result, error) {
			t.Fatalf("executor should not be called")
			return nil, nil
		},
	}
	_, err := runner.run(context.Background(), nativeNetlinkBackupTask{
		ExtraVarsJSON: `{"target_host":"172.21.253.9","vendor_family":"maipu"}`,
		Credential:    taskCredential{},
	})
	if err == nil {
		t.Fatalf("expected credential error")
	}
}

func TestNativeNetlinkBackupTaskFromRunnableUsesExecutionProfileCredential(t *testing.T) {
	runnable := &controllerTasks.RunnableTask{
		TaskID:        "task-1",
		ControllerID:  "controller-1",
		ExtraVarsJSON: `{"target_host":"172.21.253.9","vendor_family":"maipu"}`,
		ExecutionProfile: &controllerTasks.TaskExecutionProfile{
			ResolvedCredential: &controllerTasks.TaskResolvedCredential{
				Username: "netmanager",
				Password: "secret",
				AuthPass: "enable-secret",
			},
		},
	}
	task := nativeNetlinkBackupTaskFromRunnable(runnable, "/tmp/work", map[string]string{"ONEOPS_OUTPUT_DIR": "/tmp/out"})
	if task.Credential.Username != "netmanager" || task.Credential.Password != "secret" || task.Credential.AuthPass != "enable-secret" {
		t.Fatalf("credential not resolved: %#v", task.Credential)
	}
}
```

- [ ] **Step 3: Run tests and verify they fail**

Run:

```bash
cd /OneOPS/ctrlhub
go test ./controller/agent/cmd/agent -run 'TestRunNativeNetlinkBackup|TestNativeNetlinkBackup' -count=1
```

Expected: FAIL because native runner types/functions do not exist.

- [ ] **Step 4: Implement runner**

Create `ctrlhub/controller/agent/cmd/agent/netlink_backup_runner.go`:

```go
package main

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	controllerTasks "github.com/netxops/ctrlhub/controller/pkg/tasks"
	"github.com/netxops/netlink/backup"
)

type nativeNetlinkBackupTask struct {
	TaskID        string
	ControllerID  string
	WorkDir       string
	RuntimeEnv    map[string]string
	ExtraVarsJSON string
	Arguments     string
	Credential    taskCredential
}

type nativeNetlinkBackupRunner struct {
	exec func(context.Context, backup.Request) (*backup.Result, error)
}

func nativeNetlinkBackupTaskFromRunnable(runnable *controllerTasks.RunnableTask, workDir string, runtimeEnv map[string]string) nativeNetlinkBackupTask {
	return nativeNetlinkBackupTask{
		TaskID:        runnable.TaskID,
		ControllerID:  runnable.ControllerID,
		WorkDir:       workDir,
		RuntimeEnv:    runtimeEnv,
		ExtraVarsJSON: runnable.ExtraVarsJSON,
		Arguments:     runnable.Arguments,
		Credential:    taskCredentialFromExecutionProfile(runnable.ExecutionProfile, runnable.Secret),
	}
}

func (r nativeNetlinkBackupRunner) run(ctx context.Context, task nativeNetlinkBackupTask) (string, error) {
	req, meta, err := buildNativeNetlinkBackupRequest(task)
	if err != nil {
		return "", err
	}
	exec := r.exec
	if exec == nil {
		exec = func(ctx context.Context, req backup.Request) (*backup.Result, error) {
			return backup.Execute(ctx, req, nil)
		}
	}
	result, err := exec(ctx, req)
	if err != nil {
		return "", err
	}
	if err := writeNativeNetlinkBackupArtifacts(task, req, result, meta); err != nil {
		return "", err
	}
	return fmt.Sprintf("netlink native backup completed: host=%s mode=%s command=%q bytes=%d", req.Host, result.Mode, result.Command, result.Size), nil
}
```

Add helper functions in the same file:

```go
func buildNativeNetlinkBackupRequest(task nativeNetlinkBackupTask) (backup.Request, map[string]interface{}, error)
func parseNativeNetlinkExtraVars(raw string) (map[string]interface{}, error)
func writeNativeNetlinkBackupArtifacts(task nativeNetlinkBackupTask, req backup.Request, result *backup.Result, meta map[string]interface{}) error
func nativeString(vars map[string]interface{}, keys ...string) string
func nativeInt(vars map[string]interface{}, key string, fallback int) int
func safeArtifactHost(host string) string
func writeJSONFile(path string, value interface{}, perm os.FileMode) error
```

`buildNativeNetlinkBackupRequest` must map:

- `target_host`, `host`, or `ansible_host` -> `backup.Request.Host`
- `target_port`, `port`, or `ansible_port` -> `backup.Request.Port`
- `vendor_family`, `netlink_mode`, or `mode` -> `backup.Request.Mode`
- `network_backup_command`, `netlink_command`, or `command` -> `backup.Request.Command`
- `netlink_config_dir` -> `backup.Request.ConfigDir`
- timeout fields to the matching request fields
- credential username/password/private key/auth pass from `task.Credential`

`writeNativeNetlinkBackupArtifacts` must write:

- config file under `ONEOPS_OUTPUT_DIR`
- summary JSON under `ONEOPS_OUTPUT_DIR`
- manifest JSON at `ONEOPS_ARTIFACT_MANIFEST`

- [ ] **Step 5: Run runner tests**

Run:

```bash
cd /OneOPS/ctrlhub
gofmt -w controller/agent/cmd/agent/netlink_backup_runner.go controller/agent/cmd/agent/netlink_backup_runner_test.go
go test ./controller/agent/cmd/agent -run 'TestRunNativeNetlinkBackup|TestNativeNetlinkBackup' -count=1
```

Expected: PASS.

## Task 4: Route RunTask to native runner

**Files:**
- Modify: `ctrlhub/controller/agent/cmd/agent/agent_service.go`
- Modify: `ctrlhub/controller/agent/cmd/agent/agent_service_task_runner_test.go`

- [ ] **Step 1: Add routing test**

Add a test in `agent_service_task_runner_test.go` that sends `app_type=network_config_backup` and verifies `ansible-playbook` is not required. Use the runner fake by adding an injectable field if needed:

```go
func TestHandleRunTask_NetworkConfigBackupDoesNotRequireAnsible(t *testing.T) {
	as := &AgentService{
		config: &AgentConfig{Workspace: t.TempDir()},
		nativeNetlinkBackupRunner: nativeNetlinkBackupRunner{
			exec: func(ctx context.Context, req backup.Request) (*backup.Result, error) {
				return &backup.Result{Output: "hostname test\n", Command: req.Command, Mode: "maipu_mypower", Size: 14}, nil
			},
		},
	}
	result, err := as.handleRunTask(context.Background(), map[string]interface{}{
		"task_id":         "task-1",
		"project_id":      "project-1",
		"controller_id":   "controller-1",
		"app_type":        controllerTasks.AppTypeNetworkConfigBackup,
		"extra_vars_json": `{"target_host":"172.21.253.9","vendor_family":"maipu","network_backup_command":"show run"}`,
		"execution_profile": &controllerTasks.TaskExecutionProfile{
			ResolvedCredential: &controllerTasks.TaskResolvedCredential{Username: "netmanager", Password: "secret"},
		},
	})
	if err != nil {
		t.Fatalf("handleRunTask returned error: %v", err)
	}
	if result["status"] != "success" {
		t.Fatalf("status=%v result=%#v", result["status"], result)
	}
}
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
cd /OneOPS/ctrlhub
go test ./controller/agent/cmd/agent -run TestHandleRunTask_NetworkConfigBackupDoesNotRequireAnsible -count=1
```

Expected: FAIL because routing/injection does not exist.

- [ ] **Step 3: Add service field and route**

Modify `AgentService`:

```go
nativeNetlinkBackupRunner nativeNetlinkBackupRunner
```

Initialize it in `NewAgentService`:

```go
nativeNetlinkBackupRunner: nativeNetlinkBackupRunner{},
```

Add a switch case in `handleRunTask`:

```go
case controllerTasks.AppTypeNetworkConfigBackup:
	runtimeEnv, envErr := buildTaskRuntimeContractEnv(workDir)
	if envErr != nil {
		err = envErr
		break
	}
	task := nativeNetlinkBackupTaskFromRunnable(runnable, workDir, runtimeEnv)
	output, err = as.nativeNetlinkBackupRunner.run(taskCtx, task)
```

The existing post-run `collectTaskRuntimeOutput(workDir)` should collect the artifacts written by the native runner.

- [ ] **Step 4: Run agent tests**

Run:

```bash
cd /OneOPS/ctrlhub
gofmt -w controller/agent/cmd/agent/agent_service.go controller/agent/cmd/agent/agent_service_task_runner_test.go
go test ./controller/agent/cmd/agent -run 'TestHandleRunTask_NetworkConfigBackup|TestRunNativeNetlinkBackup|TestNativeNetlinkBackup' -count=1
go test ./controller/agent/cmd/agent -run 'TestHandleRunTask_UsesExecutionProfileCredentialWithoutLegacySecretField|TestHandleRunTaskCollectsRuntimeOutputArtifacts' -count=1
```

Expected: PASS.

## Task 5: Full local verification and commit ctrlhub

**Files:**
- `ctrlhub/go.mod`
- `ctrlhub/go.sum`
- files changed in Tasks 2-4

- [ ] **Step 1: Run focused tests**

Run:

```bash
cd /OneOPS/ctrlhub
go test ./controller/pkg/tasks -count=1
go test ./controller/agent/cmd/agent -count=1
```

Expected: PASS.

- [ ] **Step 2: Build agent**

Run:

```bash
cd /OneOPS/ctrlhub/controller
make build-agent
```

Expected: `build/agent` is produced successfully.

- [ ] **Step 3: Commit and push**

Run:

```bash
cd /OneOPS/ctrlhub
git status --short
git add go.mod go.sum controller/pkg/tasks/types.go controller/pkg/tasks/runner_test.go controller/agent/cmd/agent/agent_service.go controller/agent/cmd/agent/agent_service_task_runner_test.go controller/agent/cmd/agent/netlink_backup_runner.go controller/agent/cmd/agent/netlink_backup_runner_test.go
git commit -m "add agent native netlink backup runner"
git push origin main
```

Expected: commit is pushed to `main`.

## Task 6: Acceptance test without repeated device login loops

**Files:**
- No source files required.

- [ ] **Step 1: Trigger one Maipu native backup task**

Create a payload equivalent to the previous Maipu task, but use:

```json
{
  "app_type": "network_config_backup",
  "extra_vars_json": {
    "target_host": "172.21.253.9",
    "vendor_family": "maipu",
    "network_backup_command": "show run",
    "network_backup_tag": "native-maipu-test",
    "netlink_no_log": true
  }
}
```

Use the existing credential reference and execution profile path. Do not put secrets in `extra_vars_json`.

- [ ] **Step 2: Poll task status**

Expected:

```text
status: success
artifact_count: 2
config artifact: sensitive=true
backup_engine: netlink-native
```

- [ ] **Step 3: Save diagnostic**

Save diagnostic to:

```text
/tmp/task-diagnostic-<task-id>.txt
```

Expected: diagnostic shows no Ansible invocation and no `netlink-backup` CLI requirement.

## Self-Review

- Spec coverage: package extraction, agent native runner, artifacts, credential handling, version/tag migration, and Maipu acceptance are covered.
- Placeholder scan: no task contains deferred placeholders; each task has concrete files, commands, and expected outcomes.
- Type consistency: `AppTypeNetworkConfigBackup`, `nativeNetlinkBackupRunner`, `nativeNetlinkBackupTask`, and `backup.Request` are used consistently across tasks.

