# OneOps IPMI SEL Dual Output Design

Date: 2026-06-25

## Summary

This design extends `inputs.oneops_ipmi` so a single plugin instance can:

- collect IPMI metrics for Prometheus-style outputs
- collect SEL event logs for Loki
- incrementally ship only newly appeared SEL events
- persist per-target SEL cursors on local agent disk so collection resumes after agent or Telegraf restart
- attach stable Loki-friendly labels to SEL logs
- perform high-confidence structured parsing for decodable PCIe and CXL related SEL events without dropping unparsed events

The design explicitly forbids cross-stream leakage:

- logs must not be sent to Prometheus outputs
- metrics must not be sent to Loki outputs

The first phase targets host-level SEL observability only. It does not attempt GPU-card-level SEL attachment, arbitrary OEM SEL deep parsing, or historical SEL replay.

## Problem

Current `oneops_ipmi` behavior supports metrics only:

- SDR sensor readings are converted to metric measurements such as temperature, power, voltage, current, and generic sensor values.
- `sel` collector exposes SEL capacity metrics.
- `sel_events` collector summarizes SEL events into counts and latest timestamps.

Current behavior does not support:

- emitting each SEL event as a log record
- sending a single `oneops_ipmi` task to both a metrics destination and a logs destination
- incremental SEL delivery with durable restart-safe cursors
- strict routing guarantees that prevent metrics from reaching Loki and logs from reaching Prometheus

## Goals

- Keep a single `inputs.oneops_ipmi` instance per target.
- Support simultaneous metric collection and SEL log collection.
- Send metrics and logs to two different outputs from the same task.
- Incrementally send only newly appeared SEL events.
- Persist SEL cursors locally so restart resumes from the last confirmed position.
- Use explicit whitelist routing so stream separation is deterministic.
- Attach low-cardinality SEL labels that make Loki querying and alert routing practical.
- Parse only clearly recognizable PCIe and CXL style SEL payloads into structured fields and labels.
- Preserve backward compatibility for existing `oneops_ipmi` tasks that do not enable SEL log collection.

## Non-Goals

- Parsing arbitrary vendor OEM SEL payloads into rich structured domain fields in phase 1.
- Replaying historical SEL data on first start.
- Shipping runtime logs such as connection failures or privilege errors to Loki.
- Solving GPU-card-level attachment for SEL logs in phase 1.
- Replacing the existing `sel` and `sel_events` metric collectors.
- Promoting high-cardinality identifiers such as BDF or record ID to broad Loki labels by default.

## Confirmed Requirements

- One `oneops_ipmi` instance must support both metrics and logs.
- SEL logs sent to Loki include only SEL event data.
- Logs must not be sent to Prometheus outputs.
- Metrics must not be sent to Loki outputs.
- SEL logs are sent incrementally only.
- SEL cursor state must survive agent or Telegraf restart.
- Cursor state may be stored on local agent disk.
- Loki should receive only SEL event logs plus their attached labels.
- Parsing failures must fall back to generic SEL logs instead of dropping events.

## Approaches Considered

### Approach A: Single `oneops_ipmi` instance with direct dual output

The plugin emits both metric measurements and a dedicated SEL log measurement. Output routing is enforced with explicit `namepass` whitelists.

Pros:

- matches the desired single-task user experience
- reuses one IPMI connection model and one target definition
- keeps SEL log semantics inside the IPMI plugin where SEL context already exists
- avoids an extra local file hop

Cons:

- the plugin becomes responsible for both metric and log emission
- cursor durability and incremental logic must be implemented in the plugin

Recommendation: choose this approach.

### Approach B: Single `oneops_ipmi` instance writes local SEL files, `inputs.tail` ships to Loki

The plugin converts SEL events into local files. `inputs.tail` and `outputs.loki` send those files onward.

Pros:

- uses an established text log shipping pattern
- Loki sees natural file-based logs

Cons:

- introduces a second ingestion hop and more moving parts
- adds file rotation and tail state complexity
- weakens the single-plugin mental model

Recommendation: do not use for phase 1.

### Approach C: Single `oneops_ipmi` instance emits everything as generic metrics and relies on output filters

The plugin emits SEL events without a dedicated log measurement and relies on tags or downstream output rules to infer what is a log.

Pros:

- appears minimal at first glance

Cons:

- semantics are ambiguous
- stream separation is fragile
- later dashboards and alerts become harder to reason about

Recommendation: reject.

## Chosen Design

Use a single `inputs.oneops_ipmi` instance that emits:

- metric measurements for existing IPMI metric workflows
- a dedicated SEL log measurement named `ipmi_sel_event_log`

Attach both a metrics output and a Loki output to the same task, but enforce stream separation through explicit measurement whitelists on each output.

## Architecture

### Data Paths

Metric path:

1. `inputs.oneops_ipmi` runs standard collectors such as `ipmi`, `dcmi`, `bmc`, `chassis`, `sel`, and `sel_events`
2. the plugin emits standard metric measurements
3. metrics outputs include only whitelisted metric measurements

SEL log path:

1. `inputs.oneops_ipmi` runs a new `sel_logs` collector
2. the collector reads current SEL entries from the BMC
3. the collector computes the incremental delta using a per-target persisted cursor
4. each newly observed SEL entry becomes one `ipmi_sel_event_log` measurement
5. the collector enriches the entry with stable labels and optional parsed PCIe or CXL fields when a high-confidence decoder matches
6. the Loki output includes only `ipmi_sel_event_log`

### Stream Separation

Routing is whitelist based, not inference based.

Metrics outputs must use `namepass` limited to metric measurements only.

Loki output must use:

```toml
namepass = ["ipmi_sel_event_log"]
```

Any new measurement introduced in the future is not routed anywhere until it is explicitly added to an output whitelist.

## Plugin Interface Changes

### New Collector

Add a new collector:

- `sel_logs`

Existing collectors remain:

- `ipmi`
- `dcmi`
- `bmc`
- `bmc_watchdog`
- `chassis`
- `sel`
- `sel_events`
- `sm_lan_mode`

### New Configuration

Add the following `inputs.oneops_ipmi` configuration keys:

- `sel_log_state_dir`
  - required when `sel_logs` is enabled
  - local directory for persistent cursor files
- `sel_log_bootstrap`
  - default: `latest`
  - phase 1 supports only baseline-at-latest behavior
- `sel_log_max_entries_per_scrape`
  - caps one scrape's incremental send volume
- `sel_log_include_raw`
  - default: `false`
  - include raw event bytes when available
- `sel_log_min_severity`
  - optional severity filter
- `sel_log_measurement`
  - default: `ipmi_sel_event_log`
  - mainly for explicitness; phase 1 standardizes on the default value

### SEL Log Measurement Shape

Measurement:

- `ipmi_sel_event_log`

Base tags:

- `server`
- `severity`
- `sensor_type`
- `sensor_number`
- `generator_id`
- `event_direction`
- `event_type`

Additional SEL routing tags:

- `sel_kind`
  - default `generic`
  - parsed events may emit values such as `pcie` or `cxl`
- `sel_decoder`
  - default `generic`
  - parsed events may emit values such as `ami_pcie`, `intel_pcie`, or `cxl`
- `pci_error_type`
  - present only when a parser can classify the PCIe or CXL error family

Fields:

- `message`
- `record_id`
- `event_timestamp`
- `raw_hex` when enabled
- `entity_id` when available
- `entity_instance` when available
- `decode_note` when a parser matched and wants to describe the heuristic
- `pci_bdf` when a parser matched
- `pci_bus` when a parser matched
- `pci_device` when a parser matched
- `pci_function` when a parser matched

Label policy:

- Loki labels come from tags only.
- `sel_kind`, `sel_decoder`, `severity`, `sensor_type`, `event_type`, and `event_direction` are intentionally low-cardinality and safe for labels.
- `record_id` remains available on the event as a field for deduplication and debugging, but it should not be promoted to a Loki label in phase 1.
- `pci_bdf`, `pci_bus`, `pci_device`, and `pci_function` remain fields, not labels, to avoid stream explosion on large GPU fleets.

### SEL Parsing Scope

Phase 1 parsing is conservative.

Included:

- AMI BIOS PCIe style event-data payloads with recognizable BDF encoding
- Intel PCIe or AER style payloads with recognizable BDF encoding
- CXL style payloads that clearly encode component class, severity, and BDF

Excluded:

- arbitrary OEM payload families
- speculative decoding when the payload shape is ambiguous
- GPU card attachment inference beyond the BDF carried by the SEL payload itself

The collector must follow a no-loss fallback:

- if parsing succeeds, emit the generic SEL event plus structured parsed fields and tags
- if parsing does not match, emit the generic SEL event unchanged
- if parsing errors internally, log locally for operator troubleshooting but still emit the generic SEL event

The log body should be centered on `message`. Loki labels come from tags.

## SEL Cursor Model

### Cursor Key

Phase 1 cursor identity is derived from:

- normalized target `server`
- collector name `sel_logs`

If later multi-tenant or task collision is observed for the same BMC, the key can be extended with tenant or task identity without changing the collection model.

### Cursor State

Each cursor record stores at least:

- `last_record_id`
- `last_timestamp`
- `last_seen_at`
- `bmc_identity`

`bmc_identity` is a lightweight fingerprint derived from stable BMC facts and target identity so target replacement or unexpected reset can be detected.

### Bootstrap Behavior

On first start:

- read current SEL
- establish the latest known cursor baseline
- do not replay historical SEL records

This is the explicit phase 1 behavior.

### Normal Incremental Behavior

On each scrape:

1. read current SEL entries
2. select only entries newer than the stored cursor
3. emit one `ipmi_sel_event_log` measurement per new entry
4. persist the advanced cursor only after the batch has been accepted into the Telegraf pipeline

### Restart Behavior

On restart:

- load local cursor state
- resume incremental send from the stored position
- do not rebuild baseline unless cursor state is missing or invalid

### SEL Reset or Target Change

If the collector detects:

- maximum current record ID is lower than `last_record_id`, or
- `bmc_identity` no longer matches

then it treats the situation as SEL reset or target replacement:

- do not replay old history
- rebuild the latest baseline
- emit a metric signal such as `ipmi_sel_cursor_reset_total` or equivalent operational signal

## Failure Handling

### IPMI Read Failure

- do not advance the cursor
- mark the collector failed in normal plugin health metrics
- resume from the same cursor on the next successful run

### Cursor Read or Write Failure

- treat SEL log delivery as unavailable
- do not emit new SEL log entries for that scrape
- do not advance cursor state

This avoids sending logs that cannot be durably tracked.

### Downstream Output Failure

The design target is at-least-once delivery, not exactly-once.

If the downstream pipeline fails after events are emitted but before cursor advancement is durably confirmed, the next scrape may repeat a small suffix of events. This is acceptable in phase 1 and preferred over silent loss.

### SEL Parse Failure

- never drop the SEL event because parsing failed
- keep `sel_kind=generic` and `sel_decoder=generic`
- omit parsed PCIe or CXL fields when confidence is insufficient

## Idempotency and Delivery Semantics

The system provides at-least-once semantics for SEL logs.

Expected behavior:

- normal path sends each event once
- crash windows may cause bounded duplicates
- duplicates can be recognized by `server + record_id`

The design explicitly prioritizes:

- no metric/log cross-routing
- no silent SEL loss
- bounded, explainable duplication over data loss

## Platform Changes

### Template Produces

Relevant `oneops_ipmi` templates should explicitly declare:

```json
["metrics", "logs"]
```

This enables both output categories to be selected for the same task.

`produces` controls eligibility only. It does not define final routing behavior.

### Output Routing

Metrics outputs:

- use explicit `namepass` for metric measurements only
- exclude `ipmi_sel_event_log`

Loki outputs:

- use `namepass = ["ipmi_sel_event_log"]`

No output should rely on plugin-type inference or default `namepass` values for this workflow.

### Compatibility

Tasks that do not enable `sel_logs` remain unchanged.

Existing `sel` and `sel_events` collectors continue to emit only metrics and continue to support existing dashboards and alerts.

## Testing Strategy

### Unit Tests

- config validation for `sel_logs`
- bootstrap at latest baseline
- incremental send when new record IDs appear
- restart resume from persisted cursor
- reset detection when record IDs roll back
- high-confidence parser coverage for AMI PCIe, Intel PCIe or AER, and CXL payloads
- unparsed payload fallback coverage
- Loki tag and field shape coverage for parsed and generic events
- whitelist measurement routing assumptions

### Integration Tests

- generated TOML includes both metrics and Loki outputs when the template produces both streams
- metrics output `namepass` excludes `ipmi_sel_event_log`
- Loki output `namepass` includes only `ipmi_sel_event_log`

### Regression Tests

- no behavior change when `sel_logs` is not configured
- existing `sel` and `sel_events` metrics continue to work

## Phase 1 Scope

Included:

- single `oneops_ipmi` task with dual outputs
- new `sel_logs` collector
- local persistent SEL cursor state
- strict whitelist routing
- host-level Loki search and alerting for SEL logs
- conservative structured parsing for decodable PCIe and CXL SEL events
- Loki labels suitable for downstream routing and alert grouping

Excluded:

- GPU-card-level SEL attachment
- arbitrary OEM SEL deep structured parsing
- initial historical replay
- non-SEL runtime logs to Loki
- cross-agent shared cursor storage

## Open Operational Notes

- The plugin should prefer simple, inspectable JSON state files for cursor persistence in phase 1.
- One file per target is preferred over a shared monolithic state file for easier debugging.
- A bounded per-scrape entry cap is required so a burst of new SEL records does not overwhelm Loki or block the scrape loop for too long.
- The parser should prefer explicit decoder tables and simple byte extraction over broad heuristic guesswork so operational behavior stays explainable.

## Rollout Plan

1. extend `inputs.oneops_ipmi` with `sel_logs` and local cursor persistence
2. add tests for bootstrap, incremental delivery, restart recovery, reset detection, and structured PCIe or CXL SEL parsing
3. attach stable Loki tags and structured parsed fields to `ipmi_sel_event_log`
4. productize a `oneops_ipmi` template variant that declares both `metrics` and `logs`
5. configure separate metrics and Loki outputs with explicit `namepass` whitelists
6. validate end-to-end on a MEGARAC SP-X target with real SEL generation

## Acceptance Criteria

- A single `oneops_ipmi` task can emit both metrics and SEL logs.
- `ipmi_sel_event_log` is sent only to Loki.
- existing IPMI metric measurements are sent only to metrics outputs.
- first startup does not replay historical SEL records.
- new SEL records appear incrementally in Loki.
- parsed PCIe or CXL SEL events expose stable routing labels and structured BDF fields in Loki.
- undecodable SEL events still appear in Loki as generic SEL logs.
- restart resumes from the stored cursor rather than rebuilding from scratch.
- SEL reset or target replacement rebuilds baseline without replaying stale history.
