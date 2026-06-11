# SNMP Recording Rule Materialization Dry-Run Design

## Goal

Move one step beyond recording rule preview by rendering the preview result into Prometheus-compatible rule YAML, while still avoiding any runtime publication side effect.

The target flow is:

```text
strategy_set_id + target_part
  -> target context
  -> effective_contract
  -> recording rule preview
  -> Prometheus rule YAML dry-run
  -> validation summary
```

This stage is intentionally a dry-run. It returns YAML text and validation metadata only.

## Scope

In scope:

- backend DTOs for rule YAML dry-run;
- pure materializer that converts `SnmpRecordingRulePreviewGroup` into Prometheus rule-file YAML;
- backend by-target dry-run endpoint;
- frontend typed API wrapper and smoke script;
- real API acceptance for H3C, Huawei, and Maipu targets.

Out of scope:

- writing files to Prometheus rule directories;
- Prometheus reload;
- publish/saved/reloaded lifecycle state;
- Grafana dashboard JSON;
- Grafana page consumption;
- new vendor or domain metric standardization.

## YAML Shape

The materialized YAML must follow Prometheus rule-file structure:

```yaml
groups:
  - name: oneops_snmp_recording_rules_preview
    interval: 30s
    rules:
      - record: oneops:if_in_rate:bps
        expr: rate(snmp_interface_ifInOctets[5m]) * 8
```

The materializer should preserve rule order from the preview response. The existing preview builder already sorts records by record name, so the YAML output remains stable.

## Validation

Dry-run validation should be deterministic and local:

1. Build YAML from the preview rule group.
2. Parse the generated YAML back into a Prometheus rule-file DTO.
3. Verify exactly one group exists.
4. Verify group name and interval are non-empty.
5. Verify every rule has non-empty `record` and `expr`.
6. Verify parsed rule count equals preview rule count.

This does not call `promtool` and does not contact Prometheus. `promtool` can be introduced later as a separate validation enhancement.

## API Shape

Add a strict by-target dry-run endpoint:

```text
POST /platform/metrics/teleabs/strategy-sets/:id/metric-contract/recording-rules/materialize/dry-run/by-target
```

Request:

```json
{ "target_part": "DEVICE-CODE-OR-ID" }
```

No caller-provided context is accepted.

Response:

```text
strategy_set_id
target
source
item_contracts[]
effective_contract
rule_group
rules[]
summary
yaml
materialization
```

`materialization`:

```text
format = prometheus_rule_file
dry_run = true
group_count
rule_count
yaml_bytes
valid
validation_errors[]
```

## Strict Behavior

The dry-run endpoint must reuse the same strict by-target resolver path as recording rule preview:

- empty strategy-set id returns an error;
- empty `target_part` returns an error;
- missing device returns an error;
- missing target context returns an error;
- zero matched strategy-set item contracts returns an error;
- preview conflict errors still fail the request;
- invalid materialized YAML fails the request.

## Acceptance

The stage is closed when:

- backend unit tests prove rule groups render to valid YAML;
- backend by-target dry-run tests prove the response contains YAML and materialization metadata;
- backend HTTP tests prove the endpoint accepts only `target_part`;
- frontend typed smoke proves request/response shape;
- real API acceptance proves H3C, Huawei, and Maipu produce valid YAML with 12 rules each;
- handoff records that this is still dry-run only.
