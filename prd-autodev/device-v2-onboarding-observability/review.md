# Logic Review

## Verdict

- `program-verdict`: **successful-product-closure-for-current-single-device-scope-and-batch-012-extension**.
- `high-quality-complete-now`: **yes**.
- `successful-product-result-now`: **yes** for the bounded Device V2 onboarding observability closure path.
- `previous-exact-blocker-now`: **resolved**. The old `runtime syslog contract is missing; configured dispatch details are recorded only` result is superseded by live server and network success evidence.
- `final-closure-stage-now`: **yes** for the manual Codex closure loop. Future work should open as new scope.
- `new-scope-now`: **closed-success** for `batch-012` explicit batch onboarding and first H3C/Comware device-side SNMP trap target delivery.
- `upgraded-scope-now`: **closed-with-exact-blockers** as `batch-013`: Prometheus metrics and server syslog are queryable; server local tail is blocked; network syslog and SNMP trap are no_samples after successful device-side readback.

## Current Closure Result

- `D2ON-039` proves server syslog forwarding through a managed `server_syslog_listener`.
- `D2ON-040` proves network syslog target configuration through a managed `network_syslog_listener`.
- `D2ON-041` proves the redesigned Device V2 page now makes server monitor mode explicit and passes `device_type` / `monitor_mode` to backend `plan` and `ensure`.
- The service-area syslog runbook records the listener-side setup path and the server/device forwarding script shape for future automation.
- `D2ON-043` and `D2ON-044` prove explicit-code batch onboarding API/UI support.
- `D2ON-045` proves the all-device collection validation gate: 17 total, 11 ready/success, 6 blocked/unready, 0 failed.
- `D2ON-046` and `D2ON-047` prove the H3C/Comware SNMP trap target profile and controller execution path, with `snmp_trap_target` action evidence kept separate from syslog `log_forward`.
- `D2ON-048` proves a bounded one-device ready H3C/Comware live probe: explicit batch ensure succeeded, `log_forward` succeeded, and `snmp_trap_target` succeeded with controller remote success, exit code `0`, and readback match.
- `D2ON-049` proves the query tooling prerequisite for the upgraded scope: Prometheus/Loki endpoints are reachable through `oneops_test_tool`, Prometheus `up` returns a hit, and Loki range query currently returns exact no-samples for the broad tail/syslog/trap selector.
- `D2ON-051` proves Prometheus metric data-plane queryability for the bounded ready H3C/Comware device `DVCD25E1C13D3C3` via `ping_result_code{url="172.32.2.14"}`. SNMP interface data for that exact IP remains a separate no-samples/label gap.
- `D2ON-052` proves server syslog data-plane queryability in Loki and records server local tail separately as an exact blocker: the collector tail task is converged/running with grok fallback and `name_override="tail"`, but no processed tail log line is queryable from the agent `inputs.tail` -> grok -> `outputs.loki` -> controller -> Loki chain.
- `D2ON-053` records network syslog observed-data as exact no-samples: `DVCD25E1C13D3C3` has successful H3C/Comware target configuration/readback to `192.168.100.6:514`, and Loki has generic syslog samples, but no stream or message matches `172.32.2.14` / `R11` in the bounded query window.
- `D2ON-054` records network SNMP trap observed-data as exact no-samples: `DVCD25E1C13D3C3` has successful trap target configuration/readback to `192.168.100.6:162`, but no `snmp_trap` stream or trap/SNMP syslog fallback sample is queryable in Loki.
- `D2ON-055` closes the observed-data readiness pass by listing all five categories separately and preserving exact blockers instead of reporting aggregate success.
- `D2ON-056` records owner corrections that govern the next repair scope: server local `tail` is the agent `inputs.tail` -> grok -> `outputs.loki` -> controller -> Loki path, not a file transfer path; monitoring onboarding is network monitoring suite dispatch/apply, not Device V2 collection/store ingest.
- `D2ON-057` records the manual code-analysis handoff: Device V2 collection/store ingest currently does not auto sync V1 or auto push monitoring tasks; explicit monitoring onboarding should call the existing `sync-to-v1` plus `DeviceStoreSrv.NotifyMonitorProbeByDeviceCodes` path.
- Future work should repair the observed-data blockers; it does not reopen the closed server/network syslog configuration path or the closed `batch-012` configuration/readback extension.

## Evidence

- server delivery source of truth: `docs/openclaw-autodev/evidence/d2on/D2ON-039.md`
- server machine-readable summary: `docs/openclaw-autodev/evidence/d2on/D2ON-039-server-delivery-success.json`
- network delivery source of truth: `docs/openclaw-autodev/evidence/d2on/D2ON-040.md`
- network machine-readable summary: `docs/openclaw-autodev/evidence/d2on/D2ON-040-network-delivery-success.json`
- server monitor-mode UI evidence: `docs/openclaw-autodev/evidence/d2on/D2ON-041.md`
- batch backend API evidence: `docs/openclaw-autodev/evidence/d2on/D2ON-043.md`
- batch frontend UI evidence: `docs/openclaw-autodev/evidence/d2on/D2ON-044.md`
- all-device collection gate evidence: `docs/openclaw-autodev/evidence/d2on/D2ON-045.md`
- all-device collection machine summary: `docs/openclaw-autodev/evidence/d2on/D2ON-045-all-device-store-validation.json`
- SNMP trap profile evidence: `docs/openclaw-autodev/evidence/d2on/D2ON-046.md`
- SNMP trap controller execution evidence: `docs/openclaw-autodev/evidence/d2on/D2ON-047.md`
- bounded batch/trap live probe evidence: `docs/openclaw-autodev/evidence/d2on/D2ON-048.md`
- observed query tooling evidence: `docs/openclaw-autodev/evidence/d2on/D2ON-049.md`
- Prometheus metric observed evidence: `docs/openclaw-autodev/evidence/d2on/D2ON-051.md`
- server log observed evidence: `docs/openclaw-autodev/evidence/d2on/D2ON-052.md`
- network syslog observed evidence: `docs/openclaw-autodev/evidence/d2on/D2ON-053.md`
- SNMP trap observed evidence: `docs/openclaw-autodev/evidence/d2on/D2ON-054.md`
- observed-data readiness closure: `docs/openclaw-autodev/evidence/d2on/D2ON-055.md`
- owner correction for onboarding semantics: `docs/openclaw-autodev/evidence/d2on/D2ON-056.md`
- monitoring onboarding sync-to-v1 handoff: `docs/openclaw-autodev/evidence/d2on/D2ON-057.md`
- observed-data workstream: `docs/prd-autodev/device-v2-onboarding-observability/workstreams/11-observed-data-validation.md`
- batch-013 story package: `docs/prd-autodev/device-v2-onboarding-observability/story-packages/batch-013.json`
- final readiness: `docs/prd-autodev/device-v2-onboarding-observability/evidence/final-readiness.md`
- service-area runbook: `docs/prd-autodev/device-v2-onboarding-observability/runbooks/service-area-syslog-config.md`

## Live Truth

- Server probe `DVC8B7374049C21`:
  - listener plan `fd5ee4f4-51fd-11f1-8781-a61f7c1de05a`
  - endpoint `192.168.100.6:514`
  - final `overall_status=success`
  - `log_forward.device_side_delivery_status=configured`
  - controller remote success with exit code `0`
- Network probe `DVCD25E1C13D3C3`:
  - detected profile `H3C / Comware`
  - listener plan `04f03968-5283-11f1-9041-a61f7c1de05a`
  - endpoint `192.168.100.6:514`
  - final `overall_status=success`
  - `log_forward.network_syslog_template=h3c_comware_info_center`
  - `log_forward.network_syslog_verify_match=true`
- Frontend probe:
  - local URL `http://127.0.0.1:3001/#/device/device-v2-management-redesign`
  - server device `DVC8B7374049C21` opens `选择服务器监控方式`
  - `Agent` / `SNMP` options render and `Agent` is selected by default
  - backend `plan` requires monitor mode for server and does not require it for network
- Batch-012 probe:
  - all-device collection gate task `entv2_1779094092855556000`
  - 17 explicit devices validated, 11 ready/success, 6 blocked/unready, 0 failed
  - bounded batch ensure used ready H3C/Comware device `DVCD25E1C13D3C3`
  - final batch summary `total=1`, `success=1`, `failed=0`, `unknown=0`, `blocked=0`
  - `snmp_trap_target.listener_service_type=snmp_trap_listener`
  - listener plan `4a7eb57e-5268-11f1-91aa-a61f7c1de05a`, endpoint `192.168.100.6:162`
  - `controller_remote_success=true`, `remote_exit_code=0`, `snmp_trap_verify_match=true`
- Batch-013 prerequisite:
  - `oneops_test_tool` exposes `/api/v1/observability/*`
  - Prometheus endpoint `http://192.168.0.164:9090`
  - Loki endpoint `http://192.168.0.164:3100`
  - Prometheus `up`: `upstream_status=200`, `hit_count=1`
  - Prometheus metric names: `hit_count=290`, includes `ping_result_code` and `snmp_interface_ifOperStatus`
  - `ping_result_code{url="172.32.2.14"}`: `upstream_status=200`, `hit_count=1`, sample labels `device_name=R11`, `ip_transform=172.32.2.14`
  - `snmp_interface_ifOperStatus{band_ip="172.32.2.14"}`: `upstream_status=200`, `hit_count=0`
  - Loki range query `{__name=~"tail|syslog|snmp_trap"}`: `upstream_status=200`, initial broad hit count was `0` before server syslog probe traffic
  - Loki control query `{__name="syslog"}` over 6h: `upstream_status=200`, `hit_count=2`, `stream_count=2`, both D2ON-052 server-side probes
  - Loki network syslog queries for `source="172.32.2.14"`, `hostname="R11"`, and message contains `172.32.2.14` / `R11` / `info-center`: `upstream_status=200`, `hit_count=0`, `stream_count=0`
  - Loki SNMP trap queries for `{__name="snmp_trap"}`, `{__name=~"snmp.*|.*trap.*"}`, and syslog messages containing `trap` / `SNMP`: `upstream_status=200`, `hit_count=0`, `stream_count=0`

## Guardrails

- Do not reopen the old `D2ON-030/D2ON-031` blocker as if it were still current.
- Do not claim broad fleet onboarding closure; `batch-012` only closes explicit-code batch mechanics, all-device collection validation, and one bounded ready-device trap delivery probe.
- Do not claim all-vendor SNMP trap target support or trap-packet arrival into Loki/Prometheus.
- Do not claim network syslog data-plane success from target readback; `D2ON-053` currently proves exact no-samples in Loki.
- Do not claim SNMP trap packet arrival from target readback; `D2ON-054` currently proves exact no-samples in Loki.
- Do not treat `monitor_controller_stage=persist_core` as monitoring onboarding completion. Monitoring onboarding is the network monitoring suite distribution/apply path; collection/store readiness is only prerequisite context.
- Do not treat Device V2 collection/store ingest as implicit V1 synchronization or implicit monitoring task push. The explicit monitoring onboarding action must invoke and evidence that sync-and-push chain.
- Do not treat remote file upload/download as the server-local-tail product mechanism. Tail success requires a Loki-queryable processed line from the agent tail/grok/Loki chain.
- Do not write raw credentials into evidence or runbooks.
- Preserve the distinction between service-area listener setup and device/server-side syslog forwarding automation.
- Treat any next expansion after `D2ON-048` as a new explicit owner scope.
- Do not treat the batch-013 exact blockers as queryable data-plane success; future repair should keep the five observed categories separate.
