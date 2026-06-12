# SNMP Grafana Dashboard Materialization Dry-Run Design

Date: 2026-06-11

## Goal

Open the Grafana materialization path for SNMP common panels without writing dashboard rows or syncing to Grafana.

The target flow is:

```text
strategy_set_id + target_part
  -> target context
  -> effective SNMP metric contract
  -> panel capability support
  -> recording rule preview
  -> Grafana dashboard JSON dry-run
  -> panel binding preview
```

This is the first Grafana-facing stage after the recording-rule publish loop. It returns generated JSON, summary data, and trace bindings only.

## Scope

In scope:

- backend DTOs for dashboard materialization dry-run;
- a pure Grafana dashboard JSON materializer for base common SNMP panels;
- strict by-target backend endpoint;
- frontend typed API wrapper and smoke script;
- focused tests proving no caller-provided device context is accepted.

Out of scope:

- writing or updating `grafana_dashboard`;
- calling `syncToGrafana`;
- diffing existing dashboards;
- panel binding persistence;
- automatic publication after strategy changes;
- inventory-wide generation;
- new vendor/private metric standardization.

## API Shape

Add a strict by-target endpoint:

```text
POST /platform/metrics/teleabs/strategy-sets/:id/metric-contract/grafana/dashboards/materialize/dry-run/by-target
```

Request:

```json
{ "target_part": "DEVICE-CODE-OR-ID" }
```

No manufacturer, platform, model, catalog, version, dashboard code, or caller-defined panel requirements are accepted.

Response:

```text
strategy_set_id
target
source
item_contracts[]
effective_contract
supports[]
support_summary
rule_group
rules[]
recording_rule_summary
dashboard
panel_bindings[]
materialization
```

`dashboard` is a JSON object suitable for Grafana import. The backend also returns `dashboard_json` as the canonical serialized text used for size/hash validation.

`materialization` contains:

```text
format = grafana_dashboard_json
dry_run = true
panel_count
binding_count
json_bytes
valid
validation_errors[]
```

## Dashboard Shape

The dry-run dashboard should be intentionally small and stable:

- `title`: `OneOPS SNMP <device_code>`
- `timezone`: `browser`
- `schemaVersion`: a fixed Grafana-compatible integer
- `panels`: generated only for supported or config-driven base panels

Base panel keys:

```text
interface_basic.traffic
interface_basic.status
interface_basic.speed
interface_basic.quality
interface_basic.broadcast
system_basic.cpu
system_basic.memory
```

The initial materializer uses recording-rule records where they exist:

- CPU: `oneops:cpu_usage_direct:ratio` or another supported CPU record
- memory: `oneops:memory_usage_direct:ratio` or another supported memory record
- interface traffic: `oneops:if_in_rate:bps`, `oneops:if_out_rate:bps`
- interface status: `oneops:if_oper_status`
- speed: `oneops:if_speed_bps`
- quality: error and discard rate records
- broadcast: broadcast ratio records

Unsupported panels are not rendered into `dashboard.panels`. Their support state is still present in `supports[]`.

## Panel Binding Preview

Each rendered panel returns a trace binding:

```text
panel_key
panel_id
title
strategy_set_id
strategy_ids[]
metric_group_key
metric_keys[]
selected_capability_keys[]
record_names[]
managed_state = preview
content_hash
```

The binding is not persisted in this phase. It proves future dashboard diff/sync can trace:

```text
panel -> metric group -> strategy -> capability/record
```

## Validation

Validation is local and deterministic:

1. generated JSON parses back into a map;
2. title is non-empty;
3. panel count equals binding count;
4. every panel has a positive numeric id;
5. every panel has a non-empty title;
6. every rendered panel has at least one target expression;
7. every binding has `panel_key`, `panel_id`, `strategy_set_id`, and `content_hash`.

This does not contact Grafana and does not call existing dashboard create/update/sync code.

## Error Behavior

The endpoint reuses the strict by-target resolver behavior:

- empty strategy-set id returns an error;
- empty `target_part` returns an error;
- missing target device returns an error;
- missing required target context returns an error;
- zero matched strategy-set item contracts returns an error;
- recording-rule conflicts fail the request;
- invalid generated JSON fails the request.

## Acceptance

- backend unit tests prove materialization creates valid JSON and panel bindings from the existing H3C-style test contract;
- backend HTTP tests prove route id and request body are passed to the resolver;
- router consistency test includes the new route in both product and Bidi routers;
- frontend smoke proves the wrapper sends only `{ target_part }` and reads `dashboard_json`, `panel_bindings`, and `materialization`;
- existing recording-rule publish tests continue to pass.

