# SNMP Recording Rule Preview Design

## Goal

Build the next data-logic stage after by-target panel capability preview:

```text
strategy_set_id + target_part
  -> backend target context
  -> effective SNMP metric contract
  -> base common recordable capabilities
  -> Prometheus recording rule preview
```

This stage returns Prometheus recording rule data only. It does not write rule files, reload Prometheus, materialize Grafana dashboards, or broaden vendor-specific standardization.

## Scope

In scope:

- backend DTOs for recording rule preview;
- backend resolver logic that turns `effective_contract` fields into Prometheus rule expressions;
- strict by-target endpoint for strategy-set recording rule preview;
- frontend typed API wrapper only;
- smoke/unit coverage for H3C, Huawei, and Maipu seed-backed contracts.

Out of scope:

- Prometheus rule persistence;
- Prometheus reload or publish lifecycle;
- Grafana dashboard JSON;
- Grafana page rendering;
- legacy SNMP processor YAML parsing;
- broad optical/power/fan/wireless/storage metric standardization.

## Rule Selection

The preview generator should not create records for every raw metric. It should generate records only when all conditions are true:

- the field has a non-empty `capability_key`, falling back to `metric_key` only when `capability_key` is empty;
- the capability is part of the backend default base panel requirement catalog;
- the field has `recordability = "recordable"`;
- `recording_rule.enabled` is not false;
- `recording_rule.record` is non-empty;
- `config_driven` is not true.

The base recording capability allowlist is derived from default panel requirements:

```text
interface_basic.traffic:
  if_in_rate
  if_out_rate

interface_basic.status:
  if_oper_status

interface_basic.speed:
  if_speed_bps

interface_basic.quality:
  if_in_error_rate
  if_out_error_rate
  if_in_discard_rate
  if_out_discard_rate

interface_basic.broadcast:
  if_in_broadcast_ratio
  if_out_broadcast_ratio

system_basic.cpu:
  cpu_usage_direct
  cpu_usage_from_idle

system_basic.memory:
  memory_usage_direct
  memory_usage_used_total
  memory_usage_free_total
```

If two fields produce the same record name with the same expression, the preview keeps one rule and records the duplicate as deduplicated. If the same record name produces different expressions, the preview returns an error. Silent conflict resolution is not allowed.

## Prometheus Metric Name Resolution

Each raw source input resolves to a Prometheus metric name as follows:

1. Use `raw_source.prometheus_name` or input `prometheus_name` when present.
2. Otherwise use `<measurement>_<field>`.
3. Sanitize only invalid Prometheus metric-name characters into `_`.

Examples:

```text
measurement=snmp_interface, field=ifInOctets -> snmp_interface_ifInOctets
measurement=snmp, field=cpuUsage -> snmp_cpuUsage
```

## Expression Rules

The preview generator supports only the transform types already present in the current SNMP metric contract.

### direct

For normal direct values:

```text
<raw_metric>
```

For utilization records ending in `:ratio`, direct percent inputs are normalized:

```text
<raw_metric> / 100
```

### rate

For packet/error/discard counters:

```text
rate(<raw_metric>[5m])
```

For octet traffic capabilities:

```text
rate(<raw_metric>[5m]) * 8
```

### enum_map

For the first preview stage, enum-map records pass through the raw value:

```text
<raw_metric>
```

The numeric-to-text status mapping remains a Grafana/display concern later.

### expression

Expression rules replace raw field names in `transform_rule.expression` with safe PromQL fragments.

Supported current expressions:

```text
100 - cpuIdle
memUsed / memTotal * 100
100 - memFree / memTotal * 100
rate(ifInNUcastPkts) / (rate(ifInNUcastPkts) + rate(ifInUcastPkts)) * rate(ifInOctets) * 8 / ifSpeed
rate(ifOutNUcastPkts) / (rate(ifOutNUcastPkts) + rate(ifOutUcastPkts)) * rate(ifOutOctets) * 8 / ifSpeed
```

Preview output should normalize utilization records to ratio:

```text
1 - snmp_cpuIdle / 100
snmp_memUsed / clamp_min(snmp_memTotal, 1)
1 - snmp_memFree / clamp_min(snmp_memTotal, 1)
```

Broadcast ratio records use `clamp_min` for denominators:

```text
(rate(snmp_interface_ifInNUcastPkts[5m]) / clamp_min(rate(snmp_interface_ifInNUcastPkts[5m]) + rate(snmp_interface_ifInUcastPkts[5m]), 1))
* ((rate(snmp_interface_ifInOctets[5m]) * 8) / clamp_min(snmp_interface_ifSpeed, 1))
```

The output expression can be one line; formatting is not semantically important.

## API Shape

Add a strict by-target preview endpoint:

```text
POST /platform/metrics/teleabs/strategy-sets/:id/metric-contract/recording-rules/preview/by-target
```

Request:

```json
{ "target_part": "DEVICE-CODE-OR-ID" }
```

No manufacturer, platform, model, version, context, or caller-provided requirements are accepted in this by-target path.

Response:

```text
strategy_set_id
target
source = backend_resolver
item_contracts[]
effective_contract
rule_group
rules[]
summary
```

`rule_group`:

```text
name
interval
rules[]
```

`rules[]`:

```text
record
expr
capability_key
metric_key
concept_key
unit
source
```

`source`:

```text
metric_group_key
raw_measurement
raw_fields[]
transform_type
```

`summary`:

```text
total
generated
deduplicated
skipped_not_base
skipped_not_recordable
skipped_config_driven
```

## Strict Behavior

The by-target recording rule preview must reuse the same strict target path as panel preview:

- empty strategy-set id returns an error;
- empty `target_part` returns an error;
- missing `platform_devices_v2` device returns an error;
- missing required target context returns an error;
- zero matched strategy-set item contracts returns an error;
- duplicate record name with conflicting expressions returns an error.

## Expected Seed Results

For the current quick env H3C/Huawei/Maipu seeds, the preview should generate the same base record set when all raw fields exist:

```text
oneops:if_in_rate:bps
oneops:if_out_rate:bps
oneops:if_oper_status
oneops:if_speed_bps
oneops:if_in_error_rate:pps
oneops:if_out_error_rate:pps
oneops:if_in_discard_rate:pps
oneops:if_out_discard_rate:pps
oneops:if_in_broadcast_ratio:ratio
oneops:if_out_broadcast_ratio:ratio
oneops:cpu_usage_direct:ratio
oneops:memory_usage_direct:ratio
```

If a future device supports `cpu_usage_from_idle` or memory used/free-total instead of direct utilization, it should generate only the supported variant records.

## Acceptance

The stage is closed when:

- backend unit tests prove expression generation for direct, rate, enum-map, memory expression, CPU idle expression, and broadcast ratio;
- backend resolver tests prove by-target preview returns rules for H3C/Huawei/Maipu sample devices;
- backend HTTP tests prove the endpoint accepts only `target_part` and returns strict errors;
- frontend API/types compile through a smoke script;
- handoff docs record the data flow and deferred publish/Grafana work.
