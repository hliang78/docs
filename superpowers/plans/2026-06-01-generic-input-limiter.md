# Generic Input Limiter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current SNMP-only gather throttling with a generic class-based input limiter that supports both `network_device_poll` and `remote_probe` while preserving backward compatibility for existing SNMP config.

**Architecture:** Keep the per-input runner model unchanged and replace the current `SNMP only` acquire path with a `classify input -> normalize target key -> acquire class/global + class/target tokens` flow. The first rollout should support `snmp-passthrough` / `snmp-basic` as `network_device_poll`, `ping-basic` as `remote_probe`, and map legacy `snmp_*` YAML settings into the new structure when `input_limits` is absent.

**Tech Stack:** Go, Telegraf input runners, YAML config, `go test`, Markdown docs

---

## File Structure

- Modify: `ctrlhub/controller/agent/pkg/ops/metrics/input_limits.go`
  Purpose: replace SNMP-specialized limiter logic with class-based limiter state, classification, and target-key normalization.

- Modify: `ctrlhub/controller/agent/pkg/ops/metrics/input_runner.go`
  Purpose: expand `SchedulerOptions` with generic limiter specs while keeping existing scheduling controls intact.

- Modify: `ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector.go`
  Purpose: construct the new limiter from `SchedulerOptions.InputLimits` and keep runner gather execution unchanged apart from the new limiter config.

- Modify: `ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector_input_runner_test.go`
  Purpose: add failing regression coverage for `ping-basic`, cross-template grouping, and class-pool isolation.

- Modify: `ctrlhub/controller/agent/pkg/config/config.go`
  Purpose: add generic YAML schema for `input_limits` while keeping legacy `snmp_*` fields.

- Modify: `ctrlhub/controller/agent/cmd/agent/main.go`
  Purpose: translate config into `metrics.InputLimitSpec` and implement legacy-SNMP-to-generic compatibility mapping.

- Modify: `ctrlhub/controller/agent/configs/agent.yaml`
- Modify: `ctrlhub/controller/agent/configs/agent_164.yaml`
- Modify: `ctrlhub/controller/agent/configs/agent.debug.yaml`
  Purpose: show the new generic `input_limits` structure in runtime config.

- Modify: `docs/superpowers/testing/zb-agent-telegraf-scale-refactor-notes.md`
  Purpose: record that throttling is no longer SNMP-only and phase-one generic classes include `network_device_poll` and `remote_probe`.

### Task 1: Add Failing Generic Limiter Tests

**Files:**
- Modify: `ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector_input_runner_test.go`
- Test: `ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector_input_runner_test.go`

- [ ] **Step 1: Add a helper for generic limiter test setup**

```go
func applyTestInputLimits(collector *TelegrafInputCollector, specs ...InputLimitSpec) {
	collector.scheduler = SchedulerOptions{
		Interval:    time.Hour,
		InputLimits: append([]InputLimitSpec(nil), specs...),
	}
	collector.limits = newInputLimits(specs)
}
```

- [ ] **Step 2: Write the failing `ping-basic` same-target serialization test**

```go
func TestInputLimit_RemoteProbeSameTargetWithDifferentHashSuffixWaitsBehindTargetLimit(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	firstStarted := make(chan struct{})
	firstRelease := make(chan struct{})
	secondStarted := make(chan struct{})
	secondRelease := make(chan struct{})

	collector := newRunnerTestCollector(t, ctx, time.Hour)
	applyTestInputLimits(collector, InputLimitSpec{
		Class:       string(InputLimitClassRemoteProbe),
		GlobalLimit: 8,
		TargetLimit: 1,
	})
	if err := collector.ReplaceAllInputs(map[string]telegraf.Input{
		"collect_agent-001_ping-basic_DEV20260401000043_hashaaaa": &collectorBlockThenSleepInput{started: firstStarted, release: firstRelease},
		"collect_agent-001_ping-basic_DEV20260401000043_hashbbbb": &collectorBlockThenSleepInput{started: secondStarted, release: secondRelease},
	}); err != nil {
		t.Fatalf("ReplaceAllInputs failed: %v", err)
	}
	if err := collector.Start(ctx); err != nil {
		t.Fatalf("Start failed: %v", err)
	}
	defer func() {
		close(firstRelease)
		close(secondRelease)
		_ = collector.Stop()
	}()

	select {
	case <-firstStarted:
	case <-secondStarted:
	case <-time.After(2 * time.Second):
		t.Fatal("timed out waiting for one ping-basic gather to start")
	}

	select {
	case <-firstStarted:
		select {
		case <-secondStarted:
			t.Fatal("expected second same-target ping-basic input to wait behind target limit")
		case <-time.After(120 * time.Millisecond):
		}
	case <-secondStarted:
		select {
		case <-firstStarted:
			t.Fatal("expected second same-target ping-basic input to wait behind target limit")
		case <-time.After(120 * time.Millisecond):
		}
	}
}
```

- [ ] **Step 3: Write the failing `ping-basic` different-target concurrency test**

```go
func TestInputLimit_RemoteProbeDifferentTargetsCanRunConcurrently(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	firstStarted := make(chan struct{})
	firstRelease := make(chan struct{})
	secondStarted := make(chan struct{})
	secondRelease := make(chan struct{})

	collector := newRunnerTestCollector(t, ctx, time.Hour)
	applyTestInputLimits(collector, InputLimitSpec{
		Class:       string(InputLimitClassRemoteProbe),
		GlobalLimit: 8,
		TargetLimit: 1,
	})
	if err := collector.ReplaceAllInputs(map[string]telegraf.Input{
		"collect_agent-001_ping-basic_172_32_2_14_161_hashaaaa": &collectorBlockThenSleepInput{started: firstStarted, release: firstRelease},
		"collect_agent-001_ping-basic_172_32_2_15_161_hashbbbb": &collectorBlockThenSleepInput{started: secondStarted, release: secondRelease},
	}); err != nil {
		t.Fatalf("ReplaceAllInputs failed: %v", err)
	}
	if err := collector.Start(ctx); err != nil {
		t.Fatalf("Start failed: %v", err)
	}
	defer func() {
		close(firstRelease)
		close(secondRelease)
		_ = collector.Stop()
	}()

	select {
	case <-firstStarted:
	case <-time.After(2 * time.Second):
		t.Fatal("timed out waiting for first ping-basic gather")
	}
	select {
	case <-secondStarted:
	case <-time.After(2 * time.Second):
		t.Fatal("expected different-target ping-basic input to start concurrently")
	}
}
```

- [ ] **Step 4: Write the failing cross-class isolation test**

```go
func TestInputLimit_DifferentClassesDoNotShareGlobalPools(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	snmpStarted := make(chan struct{})
	snmpRelease := make(chan struct{})
	pingStarted := make(chan struct{})
	pingRelease := make(chan struct{})

	collector := newRunnerTestCollector(t, ctx, time.Hour)
	applyTestInputLimits(
		collector,
		InputLimitSpec{Class: string(InputLimitClassNetworkDevicePoll), GlobalLimit: 1, TargetLimit: 1},
		InputLimitSpec{Class: string(InputLimitClassRemoteProbe), GlobalLimit: 1, TargetLimit: 1},
	)
	if err := collector.ReplaceAllInputs(map[string]telegraf.Input{
		"collect_agent-001_snmp-basic_DEV20260401000043_hashaaaa": &collectorBlockThenSleepInput{started: snmpStarted, release: snmpRelease},
		"collect_agent-001_ping-basic_DEV20260401000043_hashbbbb": &collectorBlockThenSleepInput{started: pingStarted, release: pingRelease},
	}); err != nil {
		t.Fatalf("ReplaceAllInputs failed: %v", err)
	}
	if err := collector.Start(ctx); err != nil {
		t.Fatalf("Start failed: %v", err)
	}
	defer func() {
		close(snmpRelease)
		close(pingRelease)
		_ = collector.Stop()
	}()

	select {
	case <-snmpStarted:
	case <-time.After(2 * time.Second):
		t.Fatal("timed out waiting for snmp-basic gather")
	}
	select {
	case <-pingStarted:
	case <-time.After(2 * time.Second):
		t.Fatal("expected ping-basic gather to use an independent class pool")
	}
}
```

- [ ] **Step 5: Run the focused tests to confirm red**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent
go test ./pkg/ops/metrics -run 'TestInputLimit_(RemoteProbeSameTargetWithDifferentHashSuffixWaitsBehindTargetLimit|RemoteProbeDifferentTargetsCanRunConcurrently|DifferentClassesDoNotShareGlobalPools)' -count=1 -timeout 30s
```

Expected:
- red is required. Because `InputLimitSpec`, `InputLimitClass*`, and `SchedulerOptions.InputLimits` do not exist until Task 2, a compile-red caused by those missing generic limiter symbols is acceptable at this stage.
- once the file compiles, at least one failure must still be caused by missing `ping-basic` class handling or shared-pool assumptions.

- [ ] **Step 6: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL
git add ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector_input_runner_test.go
git commit -m "test: add failing generic input limiter coverage"
```

### Task 2: Add Generic Config And Compatibility Mapping

**Files:**
- Modify: `ctrlhub/controller/agent/pkg/config/config.go`
- Modify: `ctrlhub/controller/agent/cmd/agent/main.go`
- Modify: `ctrlhub/controller/agent/pkg/ops/metrics/input_runner.go`
- Test: `ctrlhub/controller/agent/pkg/config/config.go`

- [ ] **Step 1: Add generic config schema in `config.go`**

```go
type InputLimitConfig struct {
	Class       string `yaml:"class"`
	GlobalLimit int    `yaml:"global_limit"`
	TargetLimit int    `yaml:"target_limit"`
}

type TelegrafInputsConfig struct {
	Enabled            []string               `yaml:"enabled"`
	Configs            map[string]interface{} `yaml:"configs"`
	Interval           time.Duration          `yaml:"interval"`
	CollectionJitter   time.Duration          `yaml:"collection_jitter"`
	CollectionOffset   time.Duration          `yaml:"collection_offset"`
	SNMPGlobalLimit    int                    `yaml:"snmp_global_limit"`
	SNMPPerDeviceLimit int                    `yaml:"snmp_per_device_limit"`
	InputLimits        []InputLimitConfig     `yaml:"input_limits"`
}
```

- [ ] **Step 2: Add generic scheduler types in `input_runner.go`**

```go
type InputLimitClass string

const (
	InputLimitClassUnlimited         InputLimitClass = ""
	InputLimitClassNetworkDevicePoll InputLimitClass = "network_device_poll"
	InputLimitClassRemoteProbe       InputLimitClass = "remote_probe"
)

type InputLimitSpec struct {
	Class       InputLimitClass
	GlobalLimit int
	TargetLimit int
}

type SchedulerOptions struct {
	Interval           time.Duration
	CollectionJitter   time.Duration
	CollectionOffset   time.Duration
	SNMPGlobalLimit    int
	SNMPPerDeviceLimit int
	InputLimits        []InputLimitSpec
}
```

- [ ] **Step 3: Add compatibility builder in `main.go`**

```go
func buildTelegrafInputLimitSpecs(cfg config.TelegrafInputsConfig) []metrics.InputLimitSpec {
	if len(cfg.InputLimits) > 0 {
		specs := make([]metrics.InputLimitSpec, 0, len(cfg.InputLimits))
		for _, item := range cfg.InputLimits {
			specs = append(specs, metrics.InputLimitSpec{
				Class:       metrics.InputLimitClass(strings.TrimSpace(item.Class)),
				GlobalLimit: item.GlobalLimit,
				TargetLimit: item.TargetLimit,
			})
		}
		return specs
	}
	if cfg.SNMPGlobalLimit <= 0 && cfg.SNMPPerDeviceLimit <= 0 {
		return nil
	}
	return []metrics.InputLimitSpec{{
		Class:       metrics.InputLimitClassNetworkDevicePoll,
		GlobalLimit: cfg.SNMPGlobalLimit,
		TargetLimit: cfg.SNMPPerDeviceLimit,
	}}
}
```

- [ ] **Step 4: Wire the compatibility builder into collector startup**

```go
	a.telegrafScheduler = metrics.SchedulerOptions{
		Interval:           cfg.Protocol.TelegrafInputs.Interval,
		CollectionJitter:   cfg.Protocol.TelegrafInputs.CollectionJitter,
		CollectionOffset:   cfg.Protocol.TelegrafInputs.CollectionOffset,
		SNMPGlobalLimit:    cfg.Protocol.TelegrafInputs.SNMPGlobalLimit,
		SNMPPerDeviceLimit: cfg.Protocol.TelegrafInputs.SNMPPerDeviceLimit,
		InputLimits:        buildTelegrafInputLimitSpecs(cfg.Protocol.TelegrafInputs),
	}
```

- [ ] **Step 5: Run package tests covering config wiring**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent
go test ./pkg/config ./cmd/agent -count=1 -timeout 30s
```

Expected:
- PASS

- [ ] **Step 6: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL
git add ctrlhub/controller/agent/pkg/config/config.go ctrlhub/controller/agent/cmd/agent/main.go ctrlhub/controller/agent/pkg/ops/metrics/input_runner.go
git commit -m "feat: add generic input limiter config mapping"
```

### Task 3: Refactor Limiter Core To Class-Based Acquire

**Files:**
- Modify: `ctrlhub/controller/agent/pkg/ops/metrics/input_limits.go`
- Modify: `ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector.go`
- Modify: `ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector_input_runner_test.go`
- Test: `ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector_input_runner_test.go`

- [ ] **Step 1: Replace the constructor and limiter state**

```go
type inputLimitState struct {
	global    chan struct{}
	perTarget sync.Map
	targetN   int
}

type inputLimits struct {
	byClass map[InputLimitClass]*inputLimitState
}

func newInputLimits(specs []InputLimitSpec) *inputLimits {
	limits := &inputLimits{byClass: map[InputLimitClass]*inputLimitState{}}
	for _, spec := range specs {
		class := spec.Class
		if class == InputLimitClassUnlimited {
			continue
		}
		state := &inputLimitState{targetN: spec.TargetLimit}
		if spec.GlobalLimit > 0 {
			state.global = make(chan struct{}, spec.GlobalLimit)
		}
		limits.byClass[class] = state
	}
	return limits
}

func (s *inputLimitState) targetSemaphore(key string) chan struct{} {
	sem, _ := s.perTarget.LoadOrStore(key, make(chan struct{}, s.targetN))
	return sem.(chan struct{})
}
```

- [ ] **Step 2: Add classification and generic target parsing**

```go
func classifyInput(name string) InputLimitClass {
	lower := strings.ToLower(strings.TrimSpace(name))
	switch {
	case strings.Contains(lower, "snmp-passthrough"),
		strings.Contains(lower, "snmp_passthrough"),
		strings.Contains(lower, "snmp-basic"):
		return InputLimitClassNetworkDevicePoll
	case strings.Contains(lower, "ping-basic"):
		return InputLimitClassRemoteProbe
	default:
		return InputLimitClassUnlimited
	}
}

func parseTargetKey(name string, class InputLimitClass) string {
	switch class {
	case InputLimitClassNetworkDevicePoll:
		return extractTargetPartAfterMarkers(name, []string{
			"snmp-passthrough_",
			"snmp_passthrough_",
			"snmp-basic_",
		}, true)
	case InputLimitClassRemoteProbe:
		return extractTargetPartAfterMarkers(name, []string{
			"ping-basic_",
		}, false)
	default:
		return ""
	}
}
```

- [ ] **Step 3: Add class-aware acquire logic**

```go
func (l *inputLimits) Acquire(name string) func() {
	if l == nil {
		return func() {}
	}
	class := classifyInput(name)
	if class == InputLimitClassUnlimited {
		return func() {}
	}
	state := l.byClass[class]
	if state == nil {
		return func() {}
	}

	globalRelease := acquireToken(state.global)
	targetRelease := func() {}
	if key := parseTargetKey(name, class); key != "" && state.targetN > 0 {
		targetRelease = acquireToken(state.targetSemaphore(key))
	}
	return func() {
		targetRelease()
		globalRelease()
	}
}
```

- [ ] **Step 4: Add reusable marker-based target parsing helpers**

```go
func extractTargetPartAfterMarkers(name string, markers []string, collapseIPv4Port bool) string {
	lowerName := strings.ToLower(strings.TrimSpace(name))
	for _, marker := range markers {
		if idx := strings.Index(lowerName, marker); idx >= 0 {
			target := strings.Trim(name[idx+len(marker):], "_ ")
			if target == "" {
				return ""
			}
			parts := strings.Split(target, "_")
			if len(parts) > 1 && looksLikeHashToken(parts[len(parts)-1]) {
				parts = parts[:len(parts)-1]
			}
			if collapseIPv4Port && len(parts) >= 5 && isIPv4WithPortParts(parts[len(parts)-5:]) {
				return strings.Join(parts[len(parts)-5:len(parts)-1], "_")
			}
			return strings.Join(parts, "_")
		}
	}
	return ""
}
```

- [ ] **Step 5: Update collector construction to use generic specs**

```go
collector := &TelegrafInputCollector{
	// existing fields...
	scheduler: scheduler,
	limits:    newInputLimits(scheduler.InputLimits),
}
```

- [ ] **Step 6: Run focused limiter tests to verify green**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent
go test ./pkg/ops/metrics -run 'Test(InputLimit_|SNMPLimit_)' -count=1 -timeout 30s
```

Expected:
- PASS
- existing `SNMPLimit_` tests still pass
- new `InputLimit_` tests pass

- [ ] **Step 7: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL
git add ctrlhub/controller/agent/pkg/ops/metrics/input_limits.go ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector.go ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector_input_runner_test.go
git commit -m "feat: generalize input limiter by class"
```

### Task 4: Update Runtime Config Samples, Notes, And Full Verification

**Files:**
- Modify: `ctrlhub/controller/agent/configs/agent.yaml`
- Modify: `ctrlhub/controller/agent/configs/agent_164.yaml`
- Modify: `ctrlhub/controller/agent/configs/agent.debug.yaml`
- Modify: `docs/superpowers/testing/zb-agent-telegraf-scale-refactor-notes.md`
- Test: full package test command

- [ ] **Step 1: Replace active sample config with generic `input_limits`**

```yaml
protocol:
  telegraf_inputs:
    interval: 60s
    collection_jitter: 0s
    collection_offset: 0s
    input_limits:
      - class: network_device_poll
        global_limit: 32
        target_limit: 1
      - class: remote_probe
        global_limit: 128
        target_limit: 2
```

- [ ] **Step 2: Update refactor notes to describe phase-one classes**

```markdown
- 通用 limiter 第一阶段已覆盖两类真实远端采集：
  - `network_device_poll`：`snmp-passthrough` / `snmp_passthrough` / `snmp-basic`
  - `remote_probe`：`ping-basic`
- 旧 `snmp_global_limit` / `snmp_per_device_limit` 仍兼容，但当 `input_limits` 已配置时，以新结构为准。
```

- [ ] **Step 3: Run full verification**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent
go test ./pkg/ops/metrics ./pkg/config ./cmd/agent ./app -count=1 -timeout 120s
```

Expected:
- PASS across all four packages

- [ ] **Step 4: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL
git add ctrlhub/controller/agent/configs/agent.yaml ctrlhub/controller/agent/configs/agent_164.yaml ctrlhub/controller/agent/configs/agent.debug.yaml docs/superpowers/testing/zb-agent-telegraf-scale-refactor-notes.md
git commit -m "docs: describe generic input limiter rollout"
```
