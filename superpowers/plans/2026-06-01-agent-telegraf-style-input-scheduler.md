# Agent Telegraf-Style Input Scheduler Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the OneOps agent collector from a global serial input sweep into a Telegraf-style per-input scheduler with bounded SNMP concurrency, so thousands of monitoring tasks no longer share one blocking gather queue.

## Current Status

- Implemented on `2026-06-01` in `ctrlhub/controller/agent/pkg/ops/metrics`:
  - per-input runner registry
  - diff-based `ReplaceAllInputs()`
  - Telegraf-style overrun skip behavior
  - bounded SNMP global / per-device concurrency
  - scheduler config wiring in agent YAML + startup path
- Verified in code with:
  - `go test ./pkg/ops/metrics ./pkg/config ./cmd/agent ./app -count=1 -timeout 120s`
- Verified in real runtime with:
  - `REAL-077` in [zb-device-v2-e2e-master-outline.md](/home/jacky/project/OneOPS-ALL/docs/superpowers/testing/zb-device-v2-e2e-master-outline.md)
  - evidence shows `DVCE1EE3F7D394C` replay converging directly to `ping/snmp=running` even after restoring `41` persisted agent tasks
- Remaining worthwhile follow-up is no longer “remove the global queue” but larger-scale runtime validation and, if needed, a separate batching/sharding plan.

**Architecture:** Replace the current single `collectLoop() -> gatherMetricsSnapshot()` model with an input-runner registry: each input owns its own ticker, immediate-trigger channel, and overrun protection, while processors/outputs remain shared. Add Telegraf-like scheduling controls (`collection_jitter`, `collection_offset`) plus explicit SNMP concurrency limits so we gain Telegraf’s isolation benefits without letting thousands of SNMP goroutines stampede devices or outputs. This plan intentionally does **not** batch multiple OneOps tasks into one SNMP input instance yet; that is a higher-risk semantic change and should be a separate follow-up after the scheduler refactor is stable.

**Tech Stack:** Go, existing Telegraf input/output plugins, `go test`, existing runtime APIs, YAML config, Markdown docs, Git

---

## File Structure

- Create: `ctrlhub/controller/agent/pkg/ops/metrics/input_runner.go`
  Purpose: own the Telegraf-style per-input gather loop, immediate trigger path, overrun skip handling, and generation-aware status writes.

- Create: `ctrlhub/controller/agent/pkg/ops/metrics/input_limits.go`
  Purpose: centralize optional global/per-device concurrency limiting for expensive inputs, especially SNMP.

- Create: `ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector_input_runner_test.go`
  Purpose: focused tests for independent input runners, overrun skip semantics, changed-input restart behavior, and backlog fairness.

- Modify: `ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector.go`
  Purpose: remove the global serial gather scheduler, manage runner lifecycle, wire new limits/options into the collector, and preserve processors/outputs/status APIs.

- Modify: `ctrlhub/controller/agent/pkg/config/config.go`
  Purpose: expose scheduler and SNMP limit settings through YAML config.

- Modify: `ctrlhub/controller/agent/cmd/agent/main.go`
  Purpose: translate config into collector options and keep agent startup/restore behavior aligned with the new scheduler.

- Modify: `ctrlhub/controller/agent/configs/agent.yaml`
- Modify: `ctrlhub/controller/agent/configs/agent_164.yaml`
- Modify: `ctrlhub/controller/agent/configs/agent.debug.yaml`
  Purpose: declare safe defaults and debug overrides for the new scheduler controls.

- Modify: `docs/superpowers/testing/zb-device-v2-e2e-ai-handoff.md`
- Modify: `docs/superpowers/testing/zb-device-v2-e2e-overlooked-factors.md`
- Modify: `docs/superpowers/testing/zb-device-v2-e2e-master-outline.md`
  Purpose: capture new findings, rollout evidence, and residual scaling caveats after each implementation slice.

## Reference Material

- Telegraf configuration docs: `interval`, `metric_buffer_limit`, `collection_jitter`, `collection_offset`, `flush_jitter`
  Link: <https://docs.influxdata.com/telegraf/v1/configuration/>

- Telegraf SNMP input docs: one `[[inputs.snmp]]` can target multiple `agents`
  Link: <https://docs.influxdata.com/telegraf/v1/input-plugins/snmp/>

- Telegraf agent source: per-input `gatherLoop()` and `gatherOnce()` overrun skip model
  Link: <https://raw.githubusercontent.com/influxdata/telegraf/master/agent/agent.go>

- Telegraf SNMP source: one SNMP input gathers multiple agents concurrently
  Link: <https://raw.githubusercontent.com/influxdata/telegraf/master/plugins/inputs/snmp/snmp.go>

## Scope Guard

- In scope:
  - replace the current global serial input scheduler
  - keep runtime status freshness under large task counts
  - bound SNMP concurrency so per-input goroutines do not turn into an unbounded stampede
  - keep existing OneOps task identity, persistence, and runtime APIs compatible

- Out of scope for this plan:
  - merging many OneOps monitor tasks into one synthetic SNMP input with shared `agents`
  - changing monitor-push payload format or controller task model
  - redesigning output buffering or Prometheus registration semantics

---

### Task 1: Add Failing Scheduler Isolation Tests

**Files:**
- Create: `ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector_input_runner_test.go`
- Reuse: `ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector_input_status_test.go`
- Test: `ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector_input_runner_test.go`

- [ ] **Step 1: Write the failing independent-runner tests**

```go
func TestInputRunners_DoNotBlockUnrelatedInputs(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	slowStarted := make(chan struct{})
	slowRelease := make(chan struct{})
	collector := newRunnerTestCollector(t, ctx, 50*time.Millisecond)
	if err := collector.ReplaceAllInputs(map[string]telegraf.Input{
		"task-slow_inputs.snmp": &collectorBlockThenSleepInput{started: slowStarted, release: slowRelease},
		"task-fast_inputs.ping": collectorEmittingInput{measurement: "ping", field: "latency_ms", value: 1},
	}); err != nil {
		t.Fatalf("ReplaceAllInputs failed: %v", err)
	}
	if err := collector.Start(ctx); err != nil {
		t.Fatalf("Start failed: %v", err)
	}
	defer collector.Stop()

	<-slowStarted
	if _, ok := findInputStatusWithin(collector, "task-fast_inputs.ping", 150*time.Millisecond); !ok {
		t.Fatalf("expected fast input to gather while slow input still blocked")
	}
	close(slowRelease)
}

func TestInputRunner_SkipsTickWhenPreviousGatherStillRunning(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	collector := newRunnerTestCollector(t, ctx, 40*time.Millisecond)
	input := &collectorBlockThenSleepInput{subsequentSleep: 120 * time.Millisecond}
	if err := collector.ReplaceAllInputs(map[string]telegraf.Input{
		"task-overrun_inputs.snmp": input,
	}); err != nil {
		t.Fatalf("ReplaceAllInputs failed: %v", err)
	}
	if err := collector.Start(ctx); err != nil {
		t.Fatalf("Start failed: %v", err)
	}
	defer collector.Stop()

	time.Sleep(250 * time.Millisecond)

	if got := atomic.LoadInt32(&input.calls); got > 3 {
		t.Fatalf("expected skip-on-overrun behavior, got %d gathers", got)
	}
}

func TestReplaceAllInputs_OnlyRestartsChangedRunner(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	collector := newRunnerTestCollector(t, ctx, time.Hour)
	stable := &collectorCountingInput{}
	changed := &collectorCountingInput{}
	if err := collector.ReplaceAllInputs(map[string]telegraf.Input{
		"task-stable_inputs.ping": stable,
		"task-changed_inputs.snmp": changed,
	}); err != nil {
		t.Fatalf("initial replace failed: %v", err)
	}
	if err := collector.Start(ctx); err != nil {
		t.Fatalf("Start failed: %v", err)
	}
	defer collector.Stop()

	waitForInputStatus(t, collector, "task-stable_inputs.ping", 2*time.Second)
	waitForInputStatus(t, collector, "task-changed_inputs.snmp", 2*time.Second)

	stableCalls := atomic.LoadInt32(&stable.calls)
	if err := collector.ReplaceAllInputs(map[string]telegraf.Input{
		"task-stable_inputs.ping": stable,
		"task-changed_inputs.snmp": &collectorCountingInput{},
	}); err != nil {
		t.Fatalf("replace failed: %v", err)
	}

	time.Sleep(150 * time.Millisecond)
	if got := atomic.LoadInt32(&stable.calls); got != stableCalls {
		t.Fatalf("expected unchanged runner to stay alive without forced restart, before=%d after=%d", stableCalls, got)
	}
}
```

- [ ] **Step 2: Run the new tests to verify the current scheduler fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent
go test ./pkg/ops/metrics -run 'TestInputRunners_(DoNotBlockUnrelatedInputs|SkipsTickWhenPreviousGatherStillRunning)|TestReplaceAllInputs_OnlyRestartsChangedRunner' -count=1
```

Expected:
- At least one failure caused by the current global serial sweep.
- It is acceptable if the file does not compile yet because `newRunnerTestCollector` or runner symbols are not defined.

- [ ] **Step 3: Add minimal runner-test fixtures**

```go
type collectorCountingInput struct {
	calls int32
}

func (*collectorCountingInput) SampleConfig() string { return "" }

func (i *collectorCountingInput) Gather(acc telegraf.Accumulator) error {
	atomic.AddInt32(&i.calls, 1)
	acc.AddFields("ping", map[string]interface{}{"value": 1}, map[string]string{"source": "count"})
	return nil
}

func newRunnerTestCollector(t *testing.T, ctx context.Context, interval time.Duration) *TelegrafInputCollector {
	t.Helper()
	return &TelegrafInputCollector{
		logger:          zap.NewNop(),
		registry:        prometheus.NewRegistry(),
		inputs:          map[string]telegraf.Input{},
		metricsCh:       make(chan telegraf.Metric, 128),
		ctx:             ctx,
		cancel:          func() {},
		interval:        interval,
		systemMetrics:   &domain.SystemMetrics{},
		promMetrics:     map[string]prometheus.Collector{},
		metricCounters:  map[string]int64{},
		metricLabelNames: map[string][]string{},
		inputStatus:     map[string]*InputGatherStatus{},
		observedMetrics: map[string]map[string]ObservedMetric{},
		processors:      make(models.RunningProcessors, 0),
	}
}
```

- [ ] **Step 4: Re-run the focused tests and confirm they still fail for behavioral reasons**

Run:

```bash
go test ./pkg/ops/metrics -run 'TestInputRunners_(DoNotBlockUnrelatedInputs|SkipsTickWhenPreviousGatherStillRunning)|TestReplaceAllInputs_OnlyRestartsChangedRunner' -count=1
```

Expected:
- Tests compile.
- Failures now reflect scheduler behavior, not missing symbols.

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL
git add ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector_input_runner_test.go
git commit -m "test: add failing tests for telegraf-style input runners"
```

### Task 2: Introduce Per-Input Runner Infrastructure

**Files:**
- Create: `ctrlhub/controller/agent/pkg/ops/metrics/input_runner.go`
- Modify: `ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector.go`
- Test: `ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector_input_runner_test.go`

- [ ] **Step 1: Add the runner types**

```go
type inputRunner struct {
	name       string
	input      telegraf.Input
	interval   time.Duration
	jitter     time.Duration
	offset     time.Duration
	generation uint64

	triggerNowCh chan struct{}
	stopCh       chan struct{}
	doneCh       chan struct{}

	running atomic.Bool
	logger  *zap.Logger
}

type schedulerOptions struct {
	interval         time.Duration
	collectionJitter time.Duration
	collectionOffset time.Duration
	snmpGlobalLimit  int
	snmpPerDevice    int
}
```

- [ ] **Step 2: Add runner lifecycle methods with Telegraf-style overrun behavior**

```go
func (r *inputRunner) loop(ctx context.Context, run func(time.Time) error, onSlow func(), onSkip func()) {
	ticker := time.NewTicker(r.interval)
	defer ticker.Stop()
	defer close(r.doneCh)

	if delay := r.initialDelay(); delay > 0 {
		timer := time.NewTimer(delay)
		select {
		case <-timer.C:
		case <-ctx.Done():
			timer.Stop()
			return
		case <-r.stopCh:
			timer.Stop()
			return
		}
	}

	r.runOnce(run, onSlow)

	for {
		select {
		case <-ctx.Done():
			return
		case <-r.stopCh:
			return
		case <-ticker.C:
			if !r.runOnceIfIdle(run, onSlow) {
				onSkip()
			}
		case <-r.triggerNowCh:
			r.runOnceIfIdle(run, onSlow)
		}
	}
}
```

- [ ] **Step 3: Add runner registry fields to the collector and wire startup**

```go
type TelegrafInputCollector struct {
	// existing fields...
	runners   map[string]*inputRunner
	runnersMu sync.RWMutex
	scheduler schedulerOptions
	limits    *inputLimits
}

func NewTelegrafInputCollector(...) (*TelegrafInputCollector, error) {
	collector := &TelegrafInputCollector{
		// existing fields...
		runners:   make(map[string]*inputRunner),
		scheduler: opts,
		limits:    newInputLimits(opts.snmpGlobalLimit, opts.snmpPerDevice),
	}
	return collector, nil
}
```

- [ ] **Step 4: Replace `collectLoop()` with runner startup**

```go
func (c *TelegrafInputCollector) Start(ctx context.Context) error {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.running {
		return nil
	}
	c.ctx, c.cancel = context.WithCancel(ctx)
	c.running = true

	c.wg.Add(1)
	go c.processMetrics(c.ctx)

	for name, input := range c.inputs {
		c.startRunnerLocked(name, input, atomic.LoadUint64(&c.inputStatusGeneration))
	}
	return nil
}
```

- [ ] **Step 5: Run the focused runner tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent
go test ./pkg/ops/metrics -run 'TestInputRunners_(DoNotBlockUnrelatedInputs|SkipsTickWhenPreviousGatherStillRunning)|TestReplaceAllInputs_OnlyRestartsChangedRunner' -count=1
```

Expected:
- `TestInputRunners_DoNotBlockUnrelatedInputs` passes.
- `TestInputRunner_SkipsTickWhenPreviousGatherStillRunning` may still fail until config/skip counters are finished in Task 4.

- [ ] **Step 6: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL
git add ctrlhub/controller/agent/pkg/ops/metrics/input_runner.go ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector.go ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector_input_runner_test.go
git commit -m "refactor: add per-input runner infrastructure"
```

### Task 3: Make ReplaceAllInputs Diff-Based Instead Of Global Wipe

**Files:**
- Modify: `ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector.go`
- Test: `ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector_input_runner_test.go`

- [ ] **Step 1: Add failing tests for status preservation and changed-runner restart**

```go
func TestReplaceAllInputs_PreservesStatusForUnchangedRunner(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	stable := &collectorCountingInput{}
	changed := &collectorCountingInput{}
	collector := newRunnerTestCollector(t, ctx, time.Hour)
	require.NoError(t, collector.ReplaceAllInputs(map[string]telegraf.Input{
		"task-stable_inputs.ping": stable,
		"task-changed_inputs.snmp": changed,
	}))
	require.NoError(t, collector.Start(ctx))
	defer collector.Stop()

	waitForInputStatus(t, collector, "task-stable_inputs.ping", 2*time.Second)
	stableBefore := waitForInputStatus(t, collector, "task-stable_inputs.ping", 50*time.Millisecond)

	require.NoError(t, collector.ReplaceAllInputs(map[string]telegraf.Input{
		"task-stable_inputs.ping": stable,
		"task-changed_inputs.snmp": &collectorCountingInput{},
	}))

	stableAfter := waitForInputStatus(t, collector, "task-stable_inputs.ping", 50*time.Millisecond)
	if stableAfter.LastGatherAt.IsZero() || !stableAfter.LastGatherAt.Equal(stableBefore.LastGatherAt) {
		t.Fatalf("expected unchanged runner status to survive replace, before=%+v after=%+v", stableBefore, stableAfter)
	}
}
```

- [ ] **Step 2: Implement runner diffing in `ReplaceAllInputs()`**

```go
func (c *TelegrafInputCollector) ReplaceAllInputs(newInputs map[string]telegraf.Input) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	oldInputs := c.inputs
	c.inputs = cloneInputs(newInputs)
	changed, removed, unchanged := diffInputs(oldInputs, c.inputs)

	for _, name := range removed {
		c.stopRunnerLocked(name)
		c.deleteInputStatusLocked(name)
	}
	for _, name := range changed {
		c.stopRunnerLocked(name)
		c.deleteInputStatusLocked(name)
		c.startRunnerLocked(name, c.inputs[name], atomic.AddUint64(&c.inputStatusGeneration, 1))
	}
	for _, name := range unchanged {
		c.keepRunnerLocked(name, c.inputs[name])
	}
	return nil
}
```

- [ ] **Step 3: Delete the old global priority queue fields after diff-based restart is stable**

```go
// Remove from TelegrafInputCollector:
// - gatherNowCh
// - priorityGatherCh
// - pendingPriorityInputs
// - pendingPriorityOrder
//
// Remove helper methods:
// - triggerImmediateGather
// - triggerPriorityGather
// - mergePendingPriorityInputNamesLocked
// - clearPendingPriorityInputs
```

- [ ] **Step 4: Run the status/replace tests**

Run:

```bash
go test ./pkg/ops/metrics -run 'TestReplaceAllInputs_(OnlyRestartsChangedRunner|PreservesStatusForUnchangedRunner|KeepsEarlierUpdatedInputPrioritizedAcrossLaterUnrelatedReplace|PrioritizesCurrentBurstAheadOfOlderPendingBacklog)' -count=1
```

Expected:
- Existing priority/backlog tests should be deleted or rewritten because the old queue no longer exists.
- Replacement semantics should now be validated by the runner-diff tests instead.

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL
git add ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector.go ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector_input_runner_test.go ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector_input_status_test.go
git commit -m "refactor: make input replacement diff-based"
```

### Task 4: Add Telegraf-Style Overrun Skip, Jitter, And Offset Config

**Files:**
- Modify: `ctrlhub/controller/agent/pkg/config/config.go`
- Modify: `ctrlhub/controller/agent/cmd/agent/main.go`
- Modify: `ctrlhub/controller/agent/pkg/ops/metrics/input_runner.go`
- Modify: `ctrlhub/controller/agent/configs/agent.yaml`
- Modify: `ctrlhub/controller/agent/configs/agent_164.yaml`
- Modify: `ctrlhub/controller/agent/configs/agent.debug.yaml`
- Test: `ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector_input_runner_test.go`

- [ ] **Step 1: Extend YAML config with scheduler knobs**

```go
type TelegrafInputsConfig struct {
	Enabled           []string               `yaml:"enabled"`
	Configs           map[string]interface{} `yaml:"configs"`
	Interval          time.Duration          `yaml:"interval"`
	CollectionJitter  time.Duration          `yaml:"collection_jitter"`
	CollectionOffset  time.Duration          `yaml:"collection_offset"`
	SNMPGlobalLimit   int                    `yaml:"snmp_global_limit"`
	SNMPPerDeviceLimit int                   `yaml:"snmp_per_device_limit"`
}
```

- [ ] **Step 2: Pass the new scheduler options into the collector**

```go
opts := metrics.SchedulerOptions{
	Interval:           cfg.Protocol.TelegrafInputs.Interval,
	CollectionJitter:   cfg.Protocol.TelegrafInputs.CollectionJitter,
	CollectionOffset:   cfg.Protocol.TelegrafInputs.CollectionOffset,
	SNMPGlobalLimit:    cfg.Protocol.TelegrafInputs.SNMPGlobalLimit,
	SNMPPerDeviceLimit: cfg.Protocol.TelegrafInputs.SNMPPerDeviceLimit,
}
telegrafCollector, err := metrics.NewTelegrafInputCollector(logger, []string{defaultTelegrafInput}, defaultTelegrafInterval, nil, opts)
```

- [ ] **Step 3: Add defaults in YAML**

```yaml
protocol:
  telegraf_inputs:
    interval: 60s
    collection_jitter: 3s
    collection_offset: 0s
    snmp_global_limit: 128
    snmp_per_device_limit: 1
```

- [ ] **Step 4: Implement Telegraf-style skip logging**

```go
func (r *inputRunner) runOnceIfIdle(run func(time.Time) error, onSlow func(), onSkip func()) bool {
	if !r.running.CompareAndSwap(false, true) {
		return false
	}
	go func() {
		defer r.running.Store(false)
		if err := run(time.Now()); err != nil {
			r.logger.Warn("input gather failed", zap.String("name", r.name), zap.Error(err))
		}
	}()
	return true
}
```

- [ ] **Step 5: Run the overrun/jitter tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent
go test ./pkg/ops/metrics -run 'TestInputRunners_(SkipsTickWhenPreviousGatherStillRunning|DoNotBlockUnrelatedInputs)' -count=1
```

Expected:
- Overrun test passes.
- Collector logs should show skip warnings rather than spawning overlapping gathers.

- [ ] **Step 6: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL
git add ctrlhub/controller/agent/pkg/config/config.go ctrlhub/controller/agent/cmd/agent/main.go ctrlhub/controller/agent/pkg/ops/metrics/input_runner.go ctrlhub/controller/agent/configs/agent.yaml ctrlhub/controller/agent/configs/agent_164.yaml ctrlhub/controller/agent/configs/agent.debug.yaml
git commit -m "feat: add telegraf-style scheduler config and overrun skip"
```

### Task 5: Add Bounded SNMP Concurrency

**Files:**
- Create: `ctrlhub/controller/agent/pkg/ops/metrics/input_limits.go`
- Modify: `ctrlhub/controller/agent/pkg/ops/metrics/input_runner.go`
- Modify: `ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector_input_runner_test.go`
- Test: `ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector_input_runner_test.go`

- [ ] **Step 1: Write the failing SNMP limit tests**

```go
func TestSNMPLimit_GlobalLimitQueuesExcessWorkers(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	collector := newRunnerTestCollector(t, ctx, time.Hour)
	collector.scheduler.snmpGlobalLimit = 1
	collector.limits = newInputLimits(1, 1)

	first := &collectorBlockThenSleepInput{started: make(chan struct{}), release: make(chan struct{})}
	second := &collectorBlockThenSleepInput{started: make(chan struct{}), release: make(chan struct{})}

	require.NoError(t, collector.ReplaceAllInputs(map[string]telegraf.Input{
		"collect_agent-001_snmp-passthrough_10_0_0_1_161": first,
		"collect_agent-001_snmp-passthrough_10_0_0_2_161": second,
	}))
	require.NoError(t, collector.Start(ctx))
	defer collector.Stop()

	<-first.started
	if _, ok := findInputStatusWithin(collector, "collect_agent-001_snmp-passthrough_10_0_0_2_161", 120*time.Millisecond); ok {
		t.Fatalf("expected second SNMP input to wait behind global limit")
	}
	close(first.release)
}
```

- [ ] **Step 2: Add the limiter implementation**

```go
type inputLimits struct {
	snmpGlobal chan struct{}
	perDevice  sync.Map // map[string]chan struct{}
	perDeviceN int
}

func (l *inputLimits) Acquire(name string) func() {
	if !isSNMPInputName(name) {
		return func() {}
	}
	deviceKey := parseDeviceKey(name)
	globalRelease := acquireToken(l.snmpGlobal)
	deviceRelease := acquireToken(l.deviceSemaphore(deviceKey))
	return func() {
		deviceRelease()
		globalRelease()
	}
}
```

- [ ] **Step 3: Wrap runner gather execution with limits**

```go
release := c.limits.Acquire(name)
defer release()
err := gatherInputSafe(input, acc)
```

- [ ] **Step 4: Run the SNMP limit tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent
go test ./pkg/ops/metrics -run 'TestSNMPLimit_' -count=1
```

Expected:
- Global limit test passes.
- Add a per-device variant if the global-only version passes too easily.

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL
git add ctrlhub/controller/agent/pkg/ops/metrics/input_limits.go ctrlhub/controller/agent/pkg/ops/metrics/input_runner.go ctrlhub/controller/agent/pkg/ops/metrics/telegraf_collector_input_runner_test.go
git commit -m "feat: add bounded snmp concurrency limits"
```

### Task 6: Validate Real Runtime Behavior And Update Docs

**Files:**
- Modify: `docs/superpowers/testing/zb-device-v2-e2e-master-outline.md`
- Modify: `docs/superpowers/testing/zb-device-v2-e2e-ai-handoff.md`
- Modify: `docs/superpowers/testing/zb-device-v2-e2e-overlooked-factors.md`
- Test: real runtime replay plus package tests

- [ ] **Step 1: Run the full package tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent
go test ./pkg/ops/metrics -count=1
```

Expected:
- PASS.

- [ ] **Step 2: Restart the agent and run a real replay**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent/cmd/agent
go run . -config ../../configs/agent.yaml
```

In another shell:

```bash
TOKEN=$(curl -s http://127.0.0.1:8280/api/v1/access/login \
  -H 'Content-Type: application/json' \
  -d '{"account":"admin","password":"admin@123"}' | jq -r '.data.token')

curl -s -X POST 'http://127.0.0.1:8280/api/v1/device/v2/store/start' \
  -H "X-Auth-Token: $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"codes":["DVCE1EE3F7D394C"],"options":{"async":false}}'
```

- [ ] **Step 3: Verify fresh runtime windows**

Run:

```bash
curl -s -H "X-Auth-Token: $TOKEN" \
  'http://127.0.0.1:8280/api/v2/platform/monitoring/tasks/agent-001:collect_agent-001_ping-basic_172_32_2_15_161/runtime'

curl -s -H "X-Auth-Token: $TOKEN" \
  'http://127.0.0.1:8280/api/v2/platform/monitoring/tasks/agent-001:collect_agent-001_snmp-passthrough_172_32_2_15_161/runtime'
```

Expected:
- `ping` and `snmp` both converge with fresh `last_updated`.
- `snmp` start delay should be close to its own gather duration plus limited queueing, not dozens of seconds from unrelated backlog.

- [ ] **Step 4: Update the runtime docs**

```markdown
- Record:
  - task id
  - apply timestamp
  - ping/snmp runtime timestamps
  - whether old backlog still existed
  - whether global/per-device limits changed queueing
- Add one new REAL-### row only after there is real evidence, not for speculative design.
```

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL
git add docs/superpowers/testing/zb-device-v2-e2e-master-outline.md docs/superpowers/testing/zb-device-v2-e2e-ai-handoff.md docs/superpowers/testing/zb-device-v2-e2e-overlooked-factors.md
git commit -m "docs: record telegraf-style scheduler validation"
```

---

## Risks To Watch During Execution

- Removing `collectLoop()` too early can break startup gathers; only delete it after runner tests pass.
- Per-input goroutines without SNMP limits can replace one giant queue with a network storm; add limits before claiming the refactor is safe for scale.
- Preserving unchanged runners means `ReplaceAllInputs()` can no longer clear every status map entry blindly; status deletion must become per-input.
- Existing priority-queue tests from `REAL-075/076` will become obsolete once the global queue disappears; replace them with runner-diff tests instead of force-fitting old assertions.
- Telegraf supports multiple agents in one SNMP input, but this plan deliberately keeps OneOps’ current one-task-per-input contract. Do not silently batch tasks in this refactor.

## Definition Of Done

- `ctrlhub/controller/agent/pkg/ops/metrics` no longer uses one global serial gather sweep for all inputs.
- Each input can gather independently and a slow input only delays itself.
- Overrunning inputs skip scheduled re-entry instead of overlapping or blocking unrelated inputs.
- SNMP concurrency is explicitly bounded globally and per device.
- Real replay evidence shows target device `ping/snmp` fresh-runtime convergence no longer waits behind unrelated backlog.
- Docs capture the new model, new config knobs, and residual out-of-scope follow-up work.

## Follow-Up Plan (Separate Scope)

After this scheduler refactor is stable, create a second plan for:
- collapsing multiple OneOps SNMP tasks into shared multi-agent or multi-table collectors where semantics allow,
- reusing one SNMP walk for several metrics,
- sharding large monitor fleets across multiple agents by policy instead of by accident.
