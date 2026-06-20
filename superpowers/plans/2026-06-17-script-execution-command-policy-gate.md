# Script Execution Command Policy Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a P0 platform-side command policy gate that blocks high-risk commands in `Script Studio` test runs and in `Script Studio` publish-to-template flow before risky content can enter the template-governed `Task Center` path.

**Architecture:** Add a dedicated `ScriptExecutionPolicyGate` service with a config-aware rule provider, lightweight shell/Python/Ansible content extraction, and shared `allow/deny` decisions. Wire the gate into `ScriptStudioSrv` before task execution test runs and before Script Studio publishes draft content into a task template, because `platform_task_template` in this branch stores repository metadata and entrypoint but not raw script content.

**Tech Stack:** Go, Wire DI, existing `config.Config` platform config, Gorm/sqlite tests, Go `regexp`, YAML parsing for Ansible playbooks.

---

## File Structure

### New files

- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/i_script_execution_policy.go`
  - New service interface and DTOs for command policy evaluation.
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_provider.go`
  - Config-driven rule loading and merge logic.
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_rules.go`
  - Built-in default high-risk rules.
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_gate.go`
  - Main gate implementation, shell/Python/Ansible extraction, matching, and error shape.
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_gate_test.go`
  - Unit tests for rule matching, config overrides, and content extraction.

### Modified files

- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/config/config.go`
  - Extend `PlatformConfig` with script execution policy config fields.
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_studio.go`
  - Inject and invoke the gate before task-execution runs and publish runs.
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_studio_test_run_test.go`
  - Extend test harness and add integration coverage for denied test runs and denied publish runs.
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/boot/provider/service_groups.go`
  - Register the new gate/provider set in platform service wiring.

### Existing helper files to reuse

- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/managed_label_descriptor.go`
  - Reference pattern for config-backed service with built-in fallback.
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_studio_test_run_test.go`
  - Existing sqlite-based Script Studio harness and fake repository/workspace/template services.

---

### Task 1: Define the command policy service contract and wire set

**Files:**
- Create: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/i_script_execution_policy.go`
- Modify: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/boot/provider/service_groups.go`
- Test: none

- [ ] **Step 1: Add the new service interface and DTO definitions**

Create `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/i_script_execution_policy.go`:

```go
package service

import "context"

type ScriptExecutionPolicyCheckReq struct {
	Source     string
	AppType    string
	EntryPoint string
	Content    string
}

type ScriptExecutionPolicyDecision struct {
	Allowed         bool
	RuleID          string
	Severity        string
	Description     string
	MatchedFragment string
	RemediationHint string
}

type IScriptExecutionPolicyGate interface {
	Check(ctx context.Context, req *ScriptExecutionPolicyCheckReq) (*ScriptExecutionPolicyDecision, error)
}
```

- [ ] **Step 2: Register the provider set hook**

Modify `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/boot/provider/service_groups.go` near the platform service registrations:

```go
platformSrv.ManagedLabelDescriptorSet,
platformSrv.ScriptExecutionPolicyGateSet,
```

- [ ] **Step 3: Run a compile-only provider check**

Run: `go test ./boot/provider/... -run TestDoesNotExist`

Expected: compile progresses to the missing implementation symbols for the new gate.

- [ ] **Step 4: Commit**

```bash
git add \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/i_script_execution_policy.go \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/boot/provider/service_groups.go
git commit -m "feat: define script execution policy gate contract"
```

### Task 2: Extend platform config for command policy rules

**Files:**
- Modify: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/config/config.go`
- Test: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_gate_test.go`

- [ ] **Step 1: Write the failing config override test**

Create `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_gate_test.go` with:

```go
package impl

import (
	"testing"

	"github.com/netxops/OneOps/config"
	"go.uber.org/zap"
)

func ptrBool(v bool) *bool { return &v }

func TestScriptExecutionPolicyProvider_ConfigOverrideDisablesBuiltinRule(t *testing.T) {
	cfg := &config.Config{}
	cfg.Platform.ScriptExecutionPolicy.Enabled = ptrBool(true)
	cfg.Platform.ScriptExecutionPolicy.Rules = []config.ScriptExecutionPolicyRuleConfig{
		{RuleID: "shell.shutdown", Enabled: ptrBool(false)},
	}

	provider := newScriptExecutionPolicyRuleProvider(zap.NewNop(), cfg)
	rules := provider.ListRules()
	for _, rule := range rules {
		if rule.RuleID == "shell.shutdown" && rule.Enabled {
			t.Fatalf("expected shell.shutdown to be disabled by config override")
		}
	}
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `go test ./app/platform/service/impl -run TestScriptExecutionPolicyProvider_ConfigOverrideDisablesBuiltinRule -count=1`

Expected: FAIL because config types and provider do not exist yet.

- [ ] **Step 3: Add config structs**

Modify `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/config/config.go` near `PlatformConfig`:

```go
type ScriptExecutionPolicyConfig struct {
	Enabled *bool                             `yaml:"enabled" mapstructure:"enabled"`
	Rules   []ScriptExecutionPolicyRuleConfig `yaml:"rules" mapstructure:"rules"`
}

type ScriptExecutionPolicyRuleConfig struct {
	RuleID          string   `yaml:"rule_id" mapstructure:"rule_id"`
	Enabled         *bool    `yaml:"enabled" mapstructure:"enabled"`
	Severity        string   `yaml:"severity" mapstructure:"severity"`
	MatchType       string   `yaml:"match_type" mapstructure:"match_type"`
	Pattern         string   `yaml:"pattern" mapstructure:"pattern"`
	AppliesTo       []string `yaml:"applies_to" mapstructure:"applies_to"`
	Description     string   `yaml:"description" mapstructure:"description"`
	RemediationHint string   `yaml:"remediation_hint" mapstructure:"remediation_hint"`
}
```

Extend `PlatformConfig`:

```go
ScriptExecutionPolicy ScriptExecutionPolicyConfig `yaml:"script_execution_policy" mapstructure:"script_execution_policy"`
```

- [ ] **Step 4: Re-run the focused test**

Run: `go test ./app/platform/service/impl -run TestScriptExecutionPolicyProvider_ConfigOverrideDisablesBuiltinRule -count=1`

Expected: still FAIL because the provider implementation is not added yet, but config types compile.

- [ ] **Step 5: Commit**

```bash
git add \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/config/config.go \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_gate_test.go
git commit -m "feat: add script execution policy config model"
```

### Task 3: Implement built-in rules and config-aware provider

**Files:**
- Create: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_rules.go`
- Create: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_provider.go`
- Test: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_gate_test.go`

- [ ] **Step 1: Add provider tests for built-ins and custom appends**

Append to `script_execution_policy_gate_test.go`:

```go
func TestScriptExecutionPolicyProvider_LoadsBuiltinRules(t *testing.T) {
	provider := newScriptExecutionPolicyRuleProvider(zap.NewNop(), &config.Config{})
	if got := len(provider.ListRules()); got == 0 {
		t.Fatalf("expected builtin rules, got %d", got)
	}
}

func TestScriptExecutionPolicyProvider_AppendsCustomRule(t *testing.T) {
	cfg := &config.Config{}
	cfg.Platform.ScriptExecutionPolicy.Rules = []config.ScriptExecutionPolicyRuleConfig{
		{
			RuleID:    "custom.killall",
			Enabled:   ptrBool(true),
			MatchType: "keyword",
			Pattern:   "killall",
			AppliesTo: []string{"shell"},
		},
	}
	provider := newScriptExecutionPolicyRuleProvider(zap.NewNop(), cfg)
	found := false
	for _, rule := range provider.ListRules() {
		if rule.RuleID == "custom.killall" {
			found = true
		}
	}
	if !found {
		t.Fatalf("expected custom rule to be appended")
	}
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `go test ./app/platform/service/impl -run 'TestScriptExecutionPolicyProvider_' -count=1`

Expected: FAIL because provider and builtin rules are missing.

- [ ] **Step 3: Add built-in default rules**

Create `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_rules.go`:

```go
package impl

var defaultScriptExecutionPolicyRules = []scriptExecutionPolicyRule{
	{RuleID: "shell.rm_rf_root", Enabled: true, Severity: "critical", MatchType: "regex", Pattern: `(?i)\brm\s+-rf\s+/(?:\s|$)`, AppliesTo: []string{"shell", "bash", "sh"}, Description: "禁止删除根目录或全局递归删除命令", RemediationHint: "请改用受控路径和显式文件清单，不允许全局递归删除"},
	{RuleID: "shell.shutdown", Enabled: true, Severity: "critical", MatchType: "regex", Pattern: `(?i)\bshutdown\b`, AppliesTo: []string{"shell", "bash", "sh", "python", "ansible"}, Description: "禁止关机命令", RemediationHint: "请移除会导致主机下线的命令"},
	{RuleID: "shell.reboot", Enabled: true, Severity: "critical", MatchType: "regex", Pattern: `(?i)\breboot\b`, AppliesTo: []string{"shell", "bash", "sh", "python", "ansible"}, Description: "禁止重启命令", RemediationHint: "请移除会导致主机重启的命令"},
	{RuleID: "shell.mkfs", Enabled: true, Severity: "critical", MatchType: "regex", Pattern: `(?i)\bmkfs(?:\.[a-z0-9]+)?\b`, AppliesTo: []string{"shell", "bash", "sh", "python", "ansible"}, Description: "禁止格式化文件系统命令", RemediationHint: "请移除磁盘格式化命令"},
	{RuleID: "shell.userdel", Enabled: true, Severity: "critical", MatchType: "regex", Pattern: `(?i)\buserdel\b`, AppliesTo: []string{"shell", "bash", "sh", "python", "ansible"}, Description: "禁止删除系统账号命令", RemediationHint: "请移除用户删除命令"},
	{RuleID: "shell.passwd", Enabled: true, Severity: "critical", MatchType: "regex", Pattern: `(?i)\b(?:passwd|chpasswd)\b`, AppliesTo: []string{"shell", "bash", "sh", "python", "ansible"}, Description: "禁止修改账号口令命令", RemediationHint: "请移除口令修改命令"},
	{RuleID: "shell.iptables_flush", Enabled: true, Severity: "critical", MatchType: "regex", Pattern: `(?i)\biptables\b.*(?:-F|--flush)\b`, AppliesTo: []string{"shell", "bash", "sh", "python", "ansible"}, Description: "禁止清空 iptables 规则", RemediationHint: "请改用受控的防火墙变更流程"},
}
```

- [ ] **Step 4: Add the config-aware provider**

Create `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_provider.go`:

```go
package impl

import (
	"strings"

	"github.com/google/wire"
	"github.com/netxops/OneOps/app/platform/service"
	"github.com/netxops/OneOps/config"
	"go.uber.org/zap"
)

var ScriptExecutionPolicyGateSet = wire.NewSet(
	NewScriptExecutionPolicyGate,
	wire.Bind(new(service.IScriptExecutionPolicyGate), new(*ScriptExecutionPolicyGate)),
)

type scriptExecutionPolicyRule struct {
	RuleID          string
	Enabled         bool
	Severity        string
	MatchType       string
	Pattern         string
	AppliesTo       []string
	Description     string
	RemediationHint string
}

type scriptExecutionPolicyRuleProvider struct {
	logger *zap.Logger
	cfg    *config.Config
}

func newScriptExecutionPolicyRuleProvider(logger *zap.Logger, cfg *config.Config) *scriptExecutionPolicyRuleProvider {
	return &scriptExecutionPolicyRuleProvider{logger: logger, cfg: cfg}
}

func (p *scriptExecutionPolicyRuleProvider) Enabled() bool {
	if p == nil || p.cfg == nil || p.cfg.Platform.ScriptExecutionPolicy.Enabled == nil {
		return true
	}
	return *p.cfg.Platform.ScriptExecutionPolicy.Enabled
}

func (p *scriptExecutionPolicyRuleProvider) ListRules() []scriptExecutionPolicyRule {
	base := append([]scriptExecutionPolicyRule(nil), defaultScriptExecutionPolicyRules...)
	index := map[string]int{}
	for i, rule := range base {
		index[rule.RuleID] = i
	}
	if p == nil || p.cfg == nil {
		return base
	}
	for _, override := range p.cfg.Platform.ScriptExecutionPolicy.Rules {
		id := strings.TrimSpace(override.RuleID)
		if id == "" {
			continue
		}
		if pos, ok := index[id]; ok {
			applyScriptExecutionPolicyOverride(&base[pos], override)
			continue
		}
		base = append(base, buildScriptExecutionPolicyRuleFromConfig(override))
	}
	return base
}
```

Also implement:

```go
func applyScriptExecutionPolicyOverride(dst *scriptExecutionPolicyRule, src config.ScriptExecutionPolicyRuleConfig) {
	if dst == nil {
		return
	}
	if src.Enabled != nil {
		dst.Enabled = *src.Enabled
	}
	if strings.TrimSpace(src.Severity) != "" {
		dst.Severity = strings.TrimSpace(src.Severity)
	}
	if strings.TrimSpace(src.MatchType) != "" {
		dst.MatchType = strings.TrimSpace(src.MatchType)
	}
	if strings.TrimSpace(src.Pattern) != "" {
		dst.Pattern = strings.TrimSpace(src.Pattern)
	}
	if len(src.AppliesTo) > 0 {
		dst.AppliesTo = append([]string(nil), src.AppliesTo...)
	}
	if strings.TrimSpace(src.Description) != "" {
		dst.Description = strings.TrimSpace(src.Description)
	}
	if strings.TrimSpace(src.RemediationHint) != "" {
		dst.RemediationHint = strings.TrimSpace(src.RemediationHint)
	}
}

func buildScriptExecutionPolicyRuleFromConfig(src config.ScriptExecutionPolicyRuleConfig) scriptExecutionPolicyRule {
	rule := scriptExecutionPolicyRule{
		RuleID:          strings.TrimSpace(src.RuleID),
		Enabled:         true,
		Severity:        strings.TrimSpace(src.Severity),
		MatchType:       strings.TrimSpace(src.MatchType),
		Pattern:         strings.TrimSpace(src.Pattern),
		AppliesTo:       append([]string(nil), src.AppliesTo...),
		Description:     strings.TrimSpace(src.Description),
		RemediationHint: strings.TrimSpace(src.RemediationHint),
	}
	if src.Enabled != nil {
		rule.Enabled = *src.Enabled
	}
	return rule
}
```

- [ ] **Step 5: Re-run provider tests**

Run: `go test ./app/platform/service/impl -run 'TestScriptExecutionPolicyProvider_' -count=1`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_rules.go \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_provider.go \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_gate_test.go
git commit -m "feat: add script execution policy rules and provider"
```

### Task 4: Implement gate matching for shell and Python content

**Files:**
- Create: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_gate.go`
- Test: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_gate_test.go`

- [ ] **Step 1: Add failing shell and Python tests**

Append to `script_execution_policy_gate_test.go`:

```go
func newScriptExecutionPolicyGateForTest(t *testing.T, cfg *config.Config) *ScriptExecutionPolicyGate {
	t.Helper()
	if cfg == nil {
		cfg = &config.Config{}
	}
	return NewScriptExecutionPolicyGate(zap.NewNop(), cfg)
}

func TestScriptExecutionPolicyGate_DeniesShellCommand(t *testing.T) {
	gate := newScriptExecutionPolicyGateForTest(t, nil)
	decision, err := gate.Check(context.Background(), &service.ScriptExecutionPolicyCheckReq{
		Source:  "script_studio",
		AppType: "shell",
		Content: "echo ok\nshutdown now\n",
	})
	if err != nil {
		t.Fatalf("check failed: %v", err)
	}
	if decision == nil || decision.Allowed {
		t.Fatalf("expected deny decision, got %#v", decision)
	}
}

func TestScriptExecutionPolicyGate_IgnoresCommentedShellLine(t *testing.T) {
	gate := newScriptExecutionPolicyGateForTest(t, nil)
	decision, err := gate.Check(context.Background(), &service.ScriptExecutionPolicyCheckReq{
		AppType: "shell",
		Content: "# shutdown now\necho ok\n",
	})
	if err != nil {
		t.Fatalf("check failed: %v", err)
	}
	if decision == nil || !decision.Allowed {
		t.Fatalf("expected allow decision, got %#v", decision)
	}
}

func TestScriptExecutionPolicyGate_DeniesPythonSubprocessCommand(t *testing.T) {
	gate := newScriptExecutionPolicyGateForTest(t, nil)
	decision, err := gate.Check(context.Background(), &service.ScriptExecutionPolicyCheckReq{
		AppType: "python",
		Content: "import subprocess\nsubprocess.run(\"reboot\", shell=True)\n",
	})
	if err != nil {
		t.Fatalf("check failed: %v", err)
	}
	if decision == nil || decision.Allowed {
		t.Fatalf("expected deny decision, got %#v", decision)
	}
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `go test ./app/platform/service/impl -run 'TestScriptExecutionPolicyGate_(DeniesShellCommand|IgnoresCommentedShellLine|DeniesPythonSubprocessCommand)' -count=1`

Expected: FAIL because the gate implementation does not exist.

- [ ] **Step 3: Implement the gate**

Create `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_gate.go`:

```go
package impl

import (
	"context"
	"fmt"
	"regexp"
	"strings"

	"github.com/netxops/OneOps/app/platform/service"
	"github.com/netxops/OneOps/config"
	"go.uber.org/zap"
)

type ScriptExecutionPolicyGate struct {
	logger   *zap.Logger
	provider *scriptExecutionPolicyRuleProvider
}

func NewScriptExecutionPolicyGate(logger *zap.Logger, cfg *config.Config) *ScriptExecutionPolicyGate {
	return &ScriptExecutionPolicyGate{
		logger:   logger,
		provider: newScriptExecutionPolicyRuleProvider(logger, cfg),
	}
}

func (g *ScriptExecutionPolicyGate) Check(ctx context.Context, req *service.ScriptExecutionPolicyCheckReq) (*service.ScriptExecutionPolicyDecision, error) {
	_ = ctx
	if req == nil || g == nil || g.provider == nil || !g.provider.Enabled() {
		return &service.ScriptExecutionPolicyDecision{Allowed: true}, nil
	}
	content := strings.TrimSpace(req.Content)
	if content == "" {
		return &service.ScriptExecutionPolicyDecision{Allowed: true}, nil
	}
	appType := normalizeScriptExecutionPolicyAppType(req.AppType, req.EntryPoint)
	candidates := extractScriptExecutionPolicyCandidates(appType, content)
	for _, rule := range g.provider.ListRules() {
		if !rule.Enabled || !scriptExecutionPolicyAppliesTo(rule, appType) {
			continue
		}
		for _, candidate := range candidates {
			matched, fragment, err := matchScriptExecutionPolicyRule(rule, candidate)
			if err != nil {
				return nil, err
			}
			if matched {
				return &service.ScriptExecutionPolicyDecision{
					Allowed:         false,
					RuleID:          rule.RuleID,
					Severity:        rule.Severity,
					Description:     rule.Description,
					MatchedFragment: truncateScriptExecutionPolicyFragment(fragment),
					RemediationHint: rule.RemediationHint,
				}, nil
			}
		}
	}
	return &service.ScriptExecutionPolicyDecision{Allowed: true}, nil
}
```

Implement helpers:

- `normalizeScriptExecutionPolicyAppType(appType, entryPoint string) string`
- `extractScriptExecutionPolicyCandidates(appType, content string) []string`
- `extractShellCandidates(content string) []string`
- `extractPythonCandidates(content string) []string`
- `scriptExecutionPolicyAppliesTo(rule scriptExecutionPolicyRule, appType string) bool`
- `matchScriptExecutionPolicyRule(rule scriptExecutionPolicyRule, candidate string) (bool, string, error)`
- `truncateScriptExecutionPolicyFragment(fragment string) string`

Shell extraction rules:

```go
for _, line := range strings.Split(content, "\n") {
	line = strings.TrimSpace(line)
	if line == "" || strings.HasPrefix(line, "#") {
		continue
	}
	out = append(out, line)
}
```

Python extraction rules:

```go
markers := []string{"os.system", "subprocess.run", "subprocess.Popen"}
```

- [ ] **Step 4: Re-run focused tests**

Run: `go test ./app/platform/service/impl -run 'TestScriptExecutionPolicyGate_(DeniesShellCommand|IgnoresCommentedShellLine|DeniesPythonSubprocessCommand)' -count=1`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_gate.go \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_gate_test.go
git commit -m "feat: implement shell and python command policy gate"
```

### Task 5: Add Ansible command extraction support

**Files:**
- Modify: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_gate.go`
- Test: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_gate_test.go`

- [ ] **Step 1: Add failing Ansible tests**

Append to `script_execution_policy_gate_test.go`:

```go
func TestScriptExecutionPolicyGate_DeniesAnsibleShellTask(t *testing.T) {
	gate := newScriptExecutionPolicyGateForTest(t, nil)
	content := "---\n- hosts: all\n  tasks:\n    - name: reboot host\n      shell: reboot\n"
	decision, err := gate.Check(context.Background(), &service.ScriptExecutionPolicyCheckReq{
		AppType:    "ansible",
		EntryPoint: "playbook.yml",
		Content:    content,
	})
	if err != nil {
		t.Fatalf("check failed: %v", err)
	}
	if decision == nil || decision.Allowed {
		t.Fatalf("expected deny decision, got %#v", decision)
	}
}

func TestScriptExecutionPolicyGate_AllowsAnsibleServiceModuleInP0(t *testing.T) {
	gate := newScriptExecutionPolicyGateForTest(t, nil)
	content := "---\n- hosts: all\n  tasks:\n    - name: restart service\n      service:\n        name: nginx\n        state: restarted\n"
	decision, err := gate.Check(context.Background(), &service.ScriptExecutionPolicyCheckReq{
		AppType: "ansible",
		Content: content,
	})
	if err != nil {
		t.Fatalf("check failed: %v", err)
	}
	if decision == nil || !decision.Allowed {
		t.Fatalf("expected allow decision, got %#v", decision)
	}
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `go test ./app/platform/service/impl -run 'TestScriptExecutionPolicyGate_(DeniesAnsibleShellTask|AllowsAnsibleServiceModuleInP0)' -count=1`

Expected: FAIL because ansible extraction is not implemented.

- [ ] **Step 3: Implement minimal Ansible extraction**

Extend `script_execution_policy_gate.go`:

```go
import "gopkg.in/yaml.v3"

func extractAnsibleCandidates(content string) []string {
	var docs []map[string]interface{}
	if err := yaml.Unmarshal([]byte(content), &docs); err != nil {
		return extractShellCandidates(content)
	}
	out := make([]string, 0)
	for _, play := range docs {
		for _, section := range []string{"tasks", "pre_tasks", "post_tasks", "handlers"} {
			items, ok := play[section].([]interface{})
			if !ok {
				continue
			}
			for _, item := range items {
				task, ok := item.(map[string]interface{})
				if !ok {
					continue
				}
				for _, key := range []string{"shell", "command", "raw", "script"} {
					if value, ok := task[key]; ok {
						out = append(out, fmt.Sprint(value))
					}
				}
			}
		}
	}
	return out
}
```

In `extractScriptExecutionPolicyCandidates`, route `ansible` to `extractAnsibleCandidates`.

- [ ] **Step 4: Re-run focused tests**

Run: `go test ./app/platform/service/impl -run 'TestScriptExecutionPolicyGate_(DeniesAnsibleShellTask|AllowsAnsibleServiceModuleInP0)' -count=1`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_gate.go \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_gate_test.go
git commit -m "feat: add ansible command policy extraction"
```

### Task 6: Integrate the gate into Script Studio execution test runs

**Files:**
- Modify: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_studio.go`
- Modify: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_studio_test_run_test.go`
- Test: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_studio_test_run_test.go`

- [ ] **Step 1: Add a failing Script Studio test**

Append to `script_studio_test_run_test.go`:

```go
func TestCreateTestRun_DeniesHighRiskCommandPolicy(t *testing.T) {
	srv := newScriptStudioTestSrv(t)
	srv.CommandPolicyGate = newScriptExecutionPolicyGateForTest(t, nil)
	srv.RepositoryStore = &fakeScriptStudioRepositoryStore{
		repository: &dto.RepositoryResp{
			ID:         "repo-1",
			RepoURL:    "https://example.com/demo.git",
			RepoBranch: "main",
		},
	}
	srv.WorkspaceManager = &fakeScriptStudioWorkspaceManager{
		response: &service.ScriptStudioWorkspaceMaterializeResp{
			Branch:            "script-studio/test/draft-1",
			BaseBranch:        "main",
			ValidationSummary: "bash -n passed",
		},
	}
	srv.TaskProfileSrv = &fakeScriptStudioTaskExecutionProfileResolver{
		profile: &dto.TaskExecutionProfile{CredentialRef: "cred-1"},
	}
	draft := createScriptStudioDraftForTest(t, srv, "scripts/check.sh", "shell", "#!/usr/bin/env bash\nshutdown now\n")

	_, err := srv.CreateTestRun(context.Background(), draft.ID, &dto.ScriptStudioTestRunCreateReq{
		Mode:          "task_execution",
		ProjectID:     "project-a",
		FunctionArea:  "ops",
		RepositoryID:  "repo-1",
		CredentialRef: "device-cred-1",
	})
	if err == nil {
		t.Fatalf("expected command policy error")
	}
	if !strings.Contains(err.Error(), "高风险命令策略") {
		t.Fatalf("expected command policy message, got %v", err)
	}
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `go test ./app/platform/service/impl -run TestCreateTestRun_DeniesHighRiskCommandPolicy -count=1`

Expected: FAIL because `ScriptStudioSrv` has no command policy dependency and no check.

- [ ] **Step 3: Inject the gate and apply the check**

Modify `ScriptStudioSrv`:

```go
type ScriptStudioSrv struct {
	Logger            *zap.Logger
	DB                types.DBTypeMySQL
	LLMProvider       service.IScriptStudioLLMProvider
	WorkspaceManager  service.IScriptStudioWorkspaceManager
	TaskCreationSrvV2 service.ITaskCreationServiceV2
	TaskQuerySrvV2    service.ITaskQueryServiceV2
	TaskProfileSrv    service.ITaskExecutionProfileResolver
	RepositoryStore   service.IRepositoryStore
	TaskTemplateSrvV2 service.ITaskTemplateServiceV2
	CommandPolicyGate service.IScriptExecutionPolicyGate
	schemaOnce        sync.Once
	schemaErr         error
}
```

Update `NewScriptStudioSrv` signature and assignment:

```go
func NewScriptStudioSrv(
	logger *zap.Logger,
	db types.DBTypeMySQL,
	llmProvider service.IScriptStudioLLMProvider,
	workspaceManager service.IScriptStudioWorkspaceManager,
	taskCreationSrvV2 service.ITaskCreationServiceV2,
	taskQuerySrvV2 service.ITaskQueryServiceV2,
	taskProfileSrv service.ITaskExecutionProfileResolver,
	repositoryStore service.IRepositoryStore,
	taskTemplateSrvV2 service.ITaskTemplateServiceV2,
	commandPolicyGate service.IScriptExecutionPolicyGate,
) *ScriptStudioSrv
```

Add helper:

```go
func (s *ScriptStudioSrv) enforceScriptStudioCommandPolicyForDraft(ctx context.Context, source string, draft *dto.ScriptStudioDraftResp, appType, entryPoint string) error {
	if s == nil || s.CommandPolicyGate == nil || draft == nil {
		return nil
	}
	decision, err := s.CommandPolicyGate.Check(ctx, &service.ScriptExecutionPolicyCheckReq{
		Source:     source,
		AppType:    appType,
		EntryPoint: entryPoint,
		Content:    draft.Content,
	})
	if err != nil {
		return err
	}
	if decision != nil && !decision.Allowed {
		return fmt.Errorf("脚本命中高风险命令策略，已阻止执行: %s (%s)", decision.Description, decision.RuleID)
	}
	return nil
}
```

Call it at the top of `createScriptStudioTaskExecutionRun`:

```go
if err := s.enforceScriptStudioCommandPolicyForDraft(ctx, "script_studio", draft, draft.Language, chooseNonEmpty(draft.EntryPoint, draft.FilePath)); err != nil {
	return nil, err
}
```

Update `newScriptStudioTestSrv` to initialize `CommandPolicyGate`:

```go
CommandPolicyGate: NewScriptExecutionPolicyGate(zap.NewNop(), &config.Config{}),
```

- [ ] **Step 4: Re-run the focused test**

Run: `go test ./app/platform/service/impl -run TestCreateTestRun_DeniesHighRiskCommandPolicy -count=1`

Expected: PASS.

- [ ] **Step 5: Run the broader Script Studio subset**

Run: `go test ./app/platform/service/impl -run 'Test(ScriptStudioCreateTestRunUsesLocalValidation|CreateTestRun_DeniesHighRiskCommandPolicy)' -count=1`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_studio.go \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_studio_test_run_test.go
git commit -m "feat: enforce command policy in script studio test runs"
```

### Task 7: Integrate the gate into Script Studio publish-to-template flow

**Files:**
- Modify: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_studio.go`
- Modify: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_studio_test_run_test.go`
- Test: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_studio_test_run_test.go`

- [ ] **Step 1: Add failing publish-run tests**

Append to `script_studio_test_run_test.go`:

```go
func TestCreatePublishRun_DeniesHighRiskCommandPolicy(t *testing.T) {
	srv := newScriptStudioTestSrv(t)
	srv.CommandPolicyGate = newScriptExecutionPolicyGateForTest(t, nil)
	srv.RepositoryStore = &fakeScriptStudioRepositoryStore{
		repository: &dto.RepositoryResp{
			ID:         "repo-1",
			RepoURL:    "https://example.com/demo.git",
			RepoBranch: "main",
		},
	}
	srv.WorkspaceManager = &fakeScriptStudioWorkspaceManager{
		response: &service.ScriptStudioWorkspaceMaterializeResp{
			Branch:            "main",
			BaseBranch:        "main",
			CommitSHA:         "abc123",
			ValidationSummary: "published",
		},
	}
	srv.TaskTemplateSrvV2 = &fakeScriptStudioTaskTemplateService{
		createResp: &dto.TaskTemplateResp{ID: "tpl-001", Name: "template-1"},
	}
	draft := createScriptStudioDraftForTest(t, srv, "scripts/check.sh", "shell", "#!/usr/bin/env bash\nshutdown now\n")

	_, err := srv.CreatePublishRun(context.Background(), draft.ID, &dto.ScriptStudioPublishRunCreateReq{
		RepositoryID:   "repo-1",
		TemplateName:   "shell-danger-template",
		CreateTemplate: true,
	})
	if err == nil {
		t.Fatalf("expected command policy error")
	}
	if !strings.Contains(err.Error(), "高风险命令策略") {
		t.Fatalf("expected command policy message, got %v", err)
	}
}

func TestCreatePublishRun_AllowsSafeContent(t *testing.T) {
	srv := newScriptStudioTestSrv(t)
	srv.CommandPolicyGate = newScriptExecutionPolicyGateForTest(t, nil)
	srv.RepositoryStore = &fakeScriptStudioRepositoryStore{
		repository: &dto.RepositoryResp{
			ID:         "repo-1",
			RepoURL:    "https://example.com/demo.git",
			RepoBranch: "main",
		},
	}
	srv.WorkspaceManager = &fakeScriptStudioWorkspaceManager{
		response: &service.ScriptStudioWorkspaceMaterializeResp{
			Branch:            "main",
			BaseBranch:        "main",
			CommitSHA:         "abc123",
			ValidationSummary: "published",
		},
	}
	srv.TaskTemplateSrvV2 = &fakeScriptStudioTaskTemplateService{
		createResp: &dto.TaskTemplateResp{ID: "tpl-001", Name: "template-1"},
	}
	draft := createScriptStudioDraftForTest(t, srv, "scripts/check.sh", "shell", "#!/usr/bin/env bash\necho ok\n")

	run, err := srv.CreatePublishRun(context.Background(), draft.ID, &dto.ScriptStudioPublishRunCreateReq{
		RepositoryID:   "repo-1",
		TemplateName:   "shell-safe-template",
		CreateTemplate: true,
	})
	if err != nil {
		t.Fatalf("expected safe publish run, got %v", err)
	}
	if run == nil || run.TemplateID != "tpl-001" {
		t.Fatalf("expected published template id, got %#v", run)
	}
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `go test ./app/platform/service/impl -run 'TestCreatePublishRun_(DeniesHighRiskCommandPolicy|AllowsSafeContent)' -count=1`

Expected: FAIL because publish flow has no command policy check yet.

- [ ] **Step 3: Apply the gate in `CreatePublishRun`**

In `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_studio.go`, add before `WorkspaceManager.MaterializeDraft`:

```go
if err := s.enforceScriptStudioCommandPolicyForDraft(
	ctx,
	"script_studio_publish",
	draft,
	chooseNonEmpty(draft.Language, session.ScriptType),
	chooseNonEmpty(draft.EntryPoint, draft.FilePath, session.TargetFilePath),
); err != nil {
	return nil, err
}
```

- [ ] **Step 4: Re-run the publish tests**

Run: `go test ./app/platform/service/impl -run 'TestCreatePublishRun_(DeniesHighRiskCommandPolicy|AllowsSafeContent)' -count=1`

Expected: PASS.

- [ ] **Step 5: Run the broader publish subset**

Run: `go test ./app/platform/service/impl -run 'TestScriptStudio(PublishRun|TaskExecutionRejects)' -count=1`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_studio.go \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_studio_test_run_test.go
git commit -m "feat: enforce command policy in script studio publish flow"
```

### Task 8: Add config-disable and error-shape coverage

**Files:**
- Modify: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_gate_test.go`
- Modify: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_studio_test_run_test.go`
- Test: both files

- [ ] **Step 1: Add failing disable-switch and error-shape tests**

Append to `script_execution_policy_gate_test.go`:

```go
func TestScriptExecutionPolicyGate_DisabledByConfigAllowsRiskyCommand(t *testing.T) {
	cfg := &config.Config{}
	cfg.Platform.ScriptExecutionPolicy.Enabled = ptrBool(false)
	gate := newScriptExecutionPolicyGateForTest(t, cfg)
	decision, err := gate.Check(context.Background(), &service.ScriptExecutionPolicyCheckReq{
		AppType: "shell",
		Content: "shutdown now",
	})
	if err != nil {
		t.Fatalf("check failed: %v", err)
	}
	if decision == nil || !decision.Allowed {
		t.Fatalf("expected allow decision when disabled, got %#v", decision)
	}
}
```

Tighten the earlier Script Studio deny tests to also assert `shell.shutdown` appears in the error string.

- [ ] **Step 2: Run tests to verify they fail if logic is incomplete**

Run: `go test ./app/platform/service/impl -run 'TestScriptExecutionPolicyGate_DisabledByConfigAllowsRiskyCommand|TestCreateTestRun_DeniesHighRiskCommandPolicy|TestCreatePublishRun_DeniesHighRiskCommandPolicy' -count=1`

Expected: FAIL if disable logic or error formatting is incomplete.

- [ ] **Step 3: Adjust the implementation**

Ensure:

```go
if decision != nil && !decision.Allowed {
	return fmt.Errorf("脚本命中高风险命令策略，已阻止执行: %s (%s)", decision.Description, decision.RuleID)
}
```

And `Enabled()` returns `true` only when the config switch is unset or explicitly enabled.

- [ ] **Step 4: Re-run the focused tests**

Run: `go test ./app/platform/service/impl -run 'TestScriptExecutionPolicyGate_DisabledByConfigAllowsRiskyCommand|TestCreateTestRun_DeniesHighRiskCommandPolicy|TestCreatePublishRun_DeniesHighRiskCommandPolicy' -count=1`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_execution_policy_gate_test.go \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/script_studio_test_run_test.go
git commit -m "test: cover command policy disable switch and error details"
```

### Task 9: Run full targeted verification

**Files:**
- Modify: none
- Test: `app/platform/service/impl/...`, `boot/provider/...`

- [ ] **Step 1: Run the focused platform service test subset**

Run:

```bash
go test ./app/platform/service/impl -run 'Test(ScriptExecutionPolicyGate|CreateTestRun|CreatePublishRun|ScriptStudioCreateTestRunUsesLocalValidation)' -count=1
```

Expected: PASS.

- [ ] **Step 2: Run provider/wiring tests**

Run:

```bash
go test ./boot/provider/... -count=1
```

Expected: PASS.

- [ ] **Step 3: Run one broader package command**

Run:

```bash
go test ./app/platform/service/impl/... -count=1
```

Expected: PASS or, if there are existing unrelated branch failures, record the exact failing tests and confirm all new command-policy tests still pass.

- [ ] **Step 4: Commit final verification checkpoint**

```bash
git add -A
git commit -m "chore: verify script execution command policy gate"
```

---

## Self-Review

### Spec coverage

- Platform-only `Script Studio / Task Center` scope: covered by Tasks 6 and 7, with the codebase reality that `Task Center` coverage enters through Script Studio publish-to-template because `platform_task_template` does not store raw script content.
- Blacklist-first P0 gate: covered by Tasks 2-5.
- Config extensibility with built-in fallback: covered by Tasks 2, 3, and 8.
- Direct deny behavior: covered by Tasks 4, 6, and 7.
- No `remote/run` integration: intentionally excluded from tasks.

### Placeholder scan

- Removed the earlier template-validation placeholder by aligning template-path enforcement with the actual publish-to-template flow that still has access to `draft.Content`.
- Every code-changing step names exact files, code snippets, and test commands.

### Type consistency

- Service name is consistently `IScriptExecutionPolicyGate`.
- Request type is consistently `ScriptExecutionPolicyCheckReq`.
- Config type is consistently `ScriptExecutionPolicyConfig`.
