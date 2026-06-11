# SNMP Recording Rule Publish Lifecycle Design

## Goal

Move one step beyond materialization dry-run by publishing the already generated SNMP recording rule YAML into the runtime rule engine in a controlled, explicit, and auditable way.

This stage adds side effects, so the boundary is intentionally narrow:

```text
strategy_set_id + target_part
  -> existing by-target materialization dry-run
  -> publish planner
  -> managed rule-file merge
  -> local validation
  -> atomic file write
  -> explicit rule-engine reload
  -> publish record
```

It still does not generate Grafana dashboards and does not broaden metric standardization.

## Current Runtime Fact

The quick env runtime uses VictoriaMetrics plus `vmalert`, not native Prometheus `rule_files`.

Relevant quick env facts:

```text
quick_env/docker-compose.yml
  vmalert:
    -rule=/etc/vmalert/vmalert-rule.yml
    -datasource.url=http://victoria-metrics:9090
    -remoteWrite.url=http://victoria-metrics:9090
    -remoteRead.url=http://victoria-metrics:9090

quick_env/config/vmalert/vmalert-rule.yml
  mounted to /etc/vmalert/vmalert-rule.yml
```

VictoriaMetrics documentation states that `vmalert` supports Prometheus rule format, requires `-remoteWrite.url` for recording rules, and exposes `/-/reload` for hot configuration reload.

## Scope

In scope:

- backend publish DTOs;
- backend publisher config contract;
- file-based publisher for a single configured rule file;
- managed group merge into existing YAML;
- publish audit record;
- explicit reload call through configured URL and method;
- dry-run materialization reused as the only rule generator;
- backend HTTP publish endpoint;
- frontend typed API and smoke for request/response shape;
- quick env acceptance against the configured vmalert file and reload endpoint.

Out of scope:

- automatic publish after strategy set changes;
- automatic inventory-wide aggregation;
- Grafana dashboard JSON;
- Grafana page consumption;
- legacy YAML parsing;
- Prometheus Operator, Kubernetes ConfigMap, or object-storage rule publishing;
- new vendor/private metric standardization.

## Strict Inputs

Publish remains by-target because the current stable context resolver is by-target:

```json
{ "target_part": "DEVICE-CODE-OR-ID" }
```

No caller-provided manufacturer/platform/model/catalog/version is accepted.

The backend remains responsible for business semantic conversion:

```text
platform_devices_v2
  -> deviceidentity.ResolveMetadata(...)
  -> SnmpMetricStrategySetContractOptions
```

Frontend does not infer target metadata.

## Publisher Configuration

Publishing is disabled unless backend configuration explicitly provides the publisher settings.

Proposed config shape:

```yaml
snmp_recording_rule_publisher:
  enabled: true
  backend: vmalert_file
  rule_file_path: /OneOPS/quick_env/config/vmalert/vmalert-rule.yml
  managed_group_name: oneops_snmp_recording_rules
  reload_url: http://127.0.0.1:8880/-/reload
  reload_method: GET
  request_timeout_seconds: 10
```

Strict behavior:

- missing config fails the publish request;
- unsupported backend fails the publish request;
- empty `rule_file_path` fails the publish request;
- empty `managed_group_name` fails the publish request;
- empty `reload_url` or `reload_method` fails the publish request;
- reload is not skipped silently.

The config is explicit to avoid guessing whether the runtime is Prometheus, vmalert, or another compatible rule engine.

## Managed YAML Merge

The publisher must not overwrite the entire rule file with only OneOPS-generated rules.

Merge rule:

1. Parse the existing rule file into `groups[]`.
2. Remove groups whose `name` equals the configured `managed_group_name`.
3. Convert the materialized preview group to the configured managed group name.
4. Append the managed group to the end of `groups[]`.
5. Marshal the merged file.
6. Parse the merged YAML back and validate it.

Existing unmanaged groups remain intact and in their existing order.

The dry-run group name remains:

```text
oneops_snmp_recording_rules_preview
```

The published managed group name is configured, with quick env default:

```text
oneops_snmp_recording_rules
```

## Validation

Validation happens before any write:

- materialization dry-run must already be valid;
- existing rule file must parse;
- merged YAML must parse;
- exactly one managed group with the configured name must exist after merge;
- every managed rule must have non-empty `record` and `expr`;
- managed rule count must equal materialized rule count.

This stage uses local parse-back validation only. `promtool` or `vmalert -dryRun` can be added later as a separate validation enhancement.

## Write And Reload Lifecycle

The publish operation is synchronous and step-based:

```text
planned
  -> materialized
  -> merged
  -> validated
  -> written
  -> reloaded
```

Write sequence:

1. Read existing file.
2. Build merged YAML in memory.
3. Write merged YAML to a temporary file in the same directory.
4. Atomically rename temp file to `rule_file_path`.
5. Call configured reload endpoint.
6. Persist final status.

Failure states:

```text
failed_materialize
failed_merge
failed_validate
failed_write
failed_reload
```

If reload fails after a successful write, the publish record remains `failed_reload`. The file is not silently rolled back in this stage, because rollback requires another write and another reload and must be designed separately. The failure is explicit and visible.

## Publish Record

The backend should persist one publish record per request.

Proposed table:

```text
platform_snmp_recording_rule_publish_records
```

Fields:

```text
id
strategy_set_id
target_part
target_device_id
target_device_code
target_context_json
backend
rule_file_path
managed_group_name
rule_count
yaml_sha256
status
error_message
started_at
materialized_at
merged_at
validated_at
written_at
reloaded_at
created_at
updated_at
```

The record stores no credentials and no reload token.

## API Shape

Add one explicit publish endpoint:

```text
POST /platform/metrics/teleabs/strategy-sets/:id/metric-contract/recording-rules/publish/by-target
```

Request:

```json
{ "target_part": "DEVICE-CODE-OR-ID" }
```

Response:

```text
strategy_set_id
target
source
rule_group
rules[]
summary
yaml_sha256
publish
```

`publish`:

```text
publish_id
backend
rule_file_path
managed_group_name
rule_count
status
steps[]
error_message
```

## Conflict Policy

The publisher manages one configured group. It does not scan or rewrite unrelated groups.

Within the managed group:

- duplicate `record + expr` entries are deduplicated before writing;
- duplicate `record` with different `expr` fails validation.

This protects Grafana-facing standardized record names from ambiguous definitions.

Important limitation: publishing by a single target context is not the final inventory-wide solution. If future vendors require different expressions for the same standardized record, the next stage must design multi-context aggregation explicitly. This publish stage only makes the existing by-target chain operational.

## Quick Env Acceptance

Acceptance should prove:

1. H3C target publish creates a managed group with 12 rules.
2. Huawei target publish produces the same 12-record managed group in current quick env seed data.
3. Maipu target publish produces the same 12-record managed group in current quick env seed data.
4. Existing unmanaged `counts` group in `quick_env/config/vmalert/vmalert-rule.yml` remains present.
5. Configured reload endpoint is called and succeeds.
6. Publish record status is `reloaded`.

## Deferred

- rollback after reload failure;
- inventory-wide multi-context publishing;
- scheduled or automatic republish;
- object-storage or Kubernetes rule backends;
- Grafana dashboard JSON.

## References

- VictoriaMetrics vmalert documentation: https://docs.victoriametrics.com/victoriametrics/vmalert/
