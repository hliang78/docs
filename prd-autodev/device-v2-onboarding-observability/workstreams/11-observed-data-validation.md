# Workstream 11 - Observed Data Validation

## Goal

Upgrade the closed configuration/readback onboarding loop into a data-plane validation loop. A device is not fully observed until its metrics can be queried from Prometheus and its relevant logs/traps can be queried from Loki, or the system records an exact blocker.

## Current Facts

- `batch-012` is closed for explicit batch onboarding, all-device collection validation, and first H3C/Comware device-side SNMP trap target configuration/readback.
- `oneops_test_tool` now exposes reusable observability query APIs:
  - `GET|POST /api/v1/observability/prometheus/query`
  - `GET|POST /api/v1/observability/prometheus/query_range`
  - `GET /api/v1/observability/prometheus/metrics`
  - `GET /api/v1/observability/loki/labels`
  - `GET|POST /api/v1/observability/loki/query_range`
- Live endpoints:
  - Prometheus: `http://192.168.0.164:9090`
  - Loki: `http://192.168.0.164:3100`
- Initial probe through `oneops_test_tool`:
  - Prometheus `up` returned `hit_count=1`.
  - Prometheus metric names include `ping_result_code` and `snmp_interface_ifOperStatus`.
  - Loki range query for `{__name=~"tail|syslog|snmp_trap"}` returned `hit_count=0`, `stream_count=0`, with upstream HTTP 200.
- Owner correction in `D2ON-056`:
  - Server local `tail` is the agent `inputs.tail` plugin chain: local log file -> grok parse -> `outputs.loki` -> controller -> Loki. File upload/download APIs are diagnostic aids, not the product success path.
  - Monitoring onboarding means triggering the network monitoring suite distribution/apply path. Device V2 collection/store evidence such as `persist_core` is readiness context and must not be treated as monitoring-suite dispatch proof.
  - Current OneOPS HTTP output and Loki output address configuration must be corrected before further data-plane conclusions.
- Handoff in `D2ON-057`:
  - Device V2 collection/store ingest currently does not automatically synchronize V1 and does not automatically push monitoring tasks.
  - The existing `sync-to-v1` API already defaults to monitor push and calls `DeviceStoreSrv.NotifyMonitorProbeByDeviceCodes`.
  - The next repair should attach that sync-and-push chain to explicit Device V2 monitoring onboarding.

## Requirements

- Metrics must be verified through Prometheus queries, not inferred from monitoring dispatch success.
- Monitoring onboarding must be evidenced as network monitoring suite dispatch/apply, not inferred from Device V2 collection/store readiness.
- Explicit Device V2 monitoring onboarding should call the existing sync-to-v1 plus monitor push chain and record that evidence separately from store readiness.
- Logs and traps must be verified through Loki range queries, not inferred from listener/target configuration success.
- Evidence must record:
  - backend endpoint
  - PromQL or LogQL summary
  - time window
  - hit count / stream count
  - selected device and reason
  - sample summary if present
  - exact blocker if no samples or labels do not match
- Store evidence should use separate observed-data actions:
  - `metric_observed`
  - `server_local_log_observed`
  - `server_syslog_observed`
  - `network_syslog_observed`
  - `snmp_trap_observed`
- No raw credential material and no large raw log payloads should be persisted.

## Non-Goals

- No alert firing, alert persistence, or RCA verification in this workstream.
- No broad fleet observed-data assertion.
- No all-vendor SNMP trap support.
- No long polling inside onboarding ensure; bounded query windows only.

## Acceptance Shape

- Prometheus and Loki query tooling is available from `oneops_test_tool`. Closed by `D2ON-049`.
- Prometheus metric validation produces success or exact blocker for selected ready devices.
- Loki validation covers server local logs, server syslog logs, network syslog logs, and network SNMP trap logs.
- Final readiness states exactly which data-plane categories are queryable and which remain pending/blocked.
