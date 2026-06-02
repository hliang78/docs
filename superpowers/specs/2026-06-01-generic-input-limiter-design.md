# Generic Input Limiter Design

## 1. Background

The agent collector has already been refactored from one global serial sweep into per-input runners.

That refactor solved the first-order problem: one slow input no longer blocks unrelated inputs.

However, the current throttling layer is still SNMP-specific:

- config only exposes `snmp_global_limit` and `snmp_per_device_limit`
- runtime limiter only knows how to classify SNMP-like input names
- target-key extraction is hard-coded around current SNMP task naming patterns

This is good enough for the first production fix, but it does not generalize to other remote or high-cost polling inputs such as `ping-basic`, or future `http` / database style probes.

## 2. Problem Statement

Per-input runners remove one queue, but they also make it easier to create many concurrent gathers.

That is safe only for cheap or isolated inputs.

It is unsafe for inputs that share one of these bottlenecks:

- the same remote device
- the same remote service endpoint
- the same database instance
- the same local heavy resource budget

If we keep solving this one protocol at a time, the code will accumulate:

- `snmp_*` rules
- `ping_*` rules
- `http_*` rules
- more protocol-specific config and parsing branches

That path does not scale.

## 3. Design Goals

### 3.1 Primary goals

- generalize the limiter from `SNMP only` to `input class + target key`
- keep the existing per-input runner architecture
- preserve current SNMP behavior and compatibility
- add first-class support for `ping-basic` as another remote polling class
- keep rollout risk low by limiting first-scope classes

### 3.2 Secondary goals

- make it easy to add more input classes later without rewriting the limiter core
- keep config migration incremental
- keep runtime behavior observable and testable

## 4. Non-Goals

This design does not include:

- batching multiple OneOps tasks into one shared SNMP input
- changing task identity format
- redesigning output-side flow control
- implementing weighted fair scheduling across all classes
- onboarding every future template in the first rollout

## 5. Current Naming Evidence

The current repo and runtime notes already show real task names that matter for concurrency grouping:

- `collect_agent-001_snmp-passthrough_172_32_2_14_161`
- `collect_agent-001_snmp-basic_DEV20260401000043`
- `collect_agent-001_ping-basic_172_32_2_14_161`

This means:

- grouping cannot stay tied to one template name
- grouping should keep using the stable `target part` embedded in task IDs
- `ping-basic` should be treated as a real remote polling workload, not as an unlimited input by default

## 6. Proposed Model

### 6.1 Core abstraction

Replace the current SNMP-specialized limiter shape:

- `isSNMPInputName(name)`
- `parseSNMPDeviceKey(name)`
- `Acquire(name)`

with a generic flow:

- `classifyInput(name) -> InputLimitClass`
- `parseTargetKey(name, class) -> string`
- `Acquire(class, targetKey)`

### 6.2 First-scope classes

First rollout should be intentionally small:

1. `network_device_poll`
   - covers `snmp-passthrough`
   - covers `snmp_passthrough`
   - covers `snmp-basic`
   - intended for remote device polling with higher latency / device contention risk

2. `remote_probe`
   - covers `ping-basic`
   - intended for lightweight remote endpoint checks

3. `unlimited`
   - default fallback for everything else in phase one

### 6.3 Limits per class

Each class should support:

- `global_limit`
  - maximum concurrent gathers for the class across the whole agent

- `target_limit`
  - maximum concurrent gathers for the same normalized target within the class

This preserves the same two-level protection already proven useful for SNMP.

## 7. Target Key Strategy

### 7.1 General rule

For remote polling tasks, the limiter should prefer the `target part` embedded in task naming, because that is already the stable logical identity used by the platform.

Examples:

- `172_32_2_14_161`
- `DEV20260401000043`

### 7.2 Normalization rules

The first rollout should normalize:

- strip trailing hash suffixes when present
- keep stable target identity across template variants
- collapse `ipv4_port` style names to device identity when class policy requires it

For `network_device_poll`, target normalization should stay effectively the same as today, just generalized to more than one template family.

For `remote_probe`, the default target key should be the normalized target part after `ping-basic_`.

### 7.3 Why class-aware keys matter

Two tasks may share the same target identifier but should not always share one limiter bucket.

Example:

- `snmp-basic_DEV...`
- `ping-basic_DEV...`

These should usually share neither the same global pool nor the same target semaphore, because their cost profile is different.

So the limiter key must be:

- class-aware
- target-aware

not just `target string only`.

## 8. Config Design

### 8.1 New config structure

Add a generic config shape under `telegraf_inputs`:

```yaml
input_limits:
  - class: network_device_poll
    global_limit: 64
    target_limit: 1
  - class: remote_probe
    global_limit: 128
    target_limit: 2
```

### 8.2 Compatibility with existing config

Keep these fields for backward compatibility:

- `snmp_global_limit`
- `snmp_per_device_limit`

Migration rule:

- if `input_limits` is configured, it wins
- otherwise map old SNMP config into `network_device_poll`

This keeps existing runtime behavior stable while allowing new deployments to use the generic structure.

## 9. Runtime Design

### 9.1 Limiter structure

The limiter core should become class-based rather than protocol-specific.

Conceptually:

- one optional global semaphore per class
- one `target key -> semaphore` map per class

This can still live inside the existing `input_limits.go`; it just needs to stop assuming `snmp` is the only limited class.

### 9.2 Collector integration

The runner flow should stay unchanged except for the acquire path:

- runner decides to gather
- collector resolves `class + target key`
- limiter acquires class/global and class/target tokens
- gather runs
- limiter releases tokens

No change is needed to runner lifecycle, restart semantics, or status generation logic.

## 10. Rollout Scope

### 10.1 Phase one

Implement:

- generic limiter core
- config compatibility layer
- class coverage for `network_device_poll`
- class coverage for `remote_probe`
- tests for `snmp-*` and `ping-basic`

### 10.2 Deferred follow-up

Leave for later:

- database polling classes
- generic `http` remote checks if and when real task names are confirmed
- weighted or cost-based scheduling
- cross-class shared resource budgeting

## 11. Test Strategy

### 11.1 New regression tests

Add focused tests for:

1. `ping-basic` same target, different hash suffix
   - should respect `remote_probe.target_limit`

2. `ping-basic` different targets
   - should not block each other when capacity exists

3. `snmp-basic` and `snmp-passthrough`
   - should both map into `network_device_poll`

4. `snmp-*` and `ping-basic`
   - should use different class pools so lightweight probes are not accidentally serialized behind heavy device polling

### 11.2 Verification expectations

Required package verification after implementation:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent
go test ./pkg/ops/metrics ./pkg/config ./cmd/agent ./app -count=1 -timeout 120s
```

## 12. Risks

### 12.1 Under-classifying inputs

If an input that should be limited falls into `unlimited`, we can still create concurrency bursts.

Mitigation:

- keep first rollout small but explicit
- add tests from real task naming evidence

### 12.2 Over-classifying lightweight inputs

If we put too many cheap probes into one low-cap pool, we reintroduce artificial queueing.

Mitigation:

- give `remote_probe` its own larger pool
- do not force `ping` into the SNMP pool

### 12.3 Config confusion

Running both legacy SNMP fields and new generic fields can confuse operators.

Mitigation:

- document precedence clearly
- log which limiter config path is active at startup

## 13. Recommendation

Implement the generic limiter now, but keep the first rollout intentionally narrow:

- `network_device_poll`
- `remote_probe`
- legacy SNMP compatibility

That gives the current scheduler refactor a reusable concurrency-governance layer without prematurely expanding to every possible input type.
