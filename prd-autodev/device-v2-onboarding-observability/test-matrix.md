---
topic: device-v2-onboarding-observability
kind: full-stack
title: Device V2 极简纳管设计
status: draft
---

# Test Matrix

| Flow | Entry | Expected Evidence | Validation |
|---|---|---|---|
| Continue onboarding UI | Device V2 row action | Single-device action, no batch remote execution | Browser screenshot + no batch API call |
| Redesign browser validation | Local `DeviceV2ManagementRedesign` target | Continue-onboarding uses onboarding APIs and renders action evidence, or a durable blocker is recorded | Browser/devtools evidence summary + readiness/review update |
| Monitoring mode choice | Server device continue | user chooses `agent` or `snmp` | UI state + request payload |
| Action result contract | onboarding ensure response | `summary_json.onboarding.actions[]` with result/changed/retryable | Go contract test |
| Retry failed only | second ensure click | skip success, retry failed/unknown | Unit test with seeded summary |
| Network syslog listener | FunctionArea config | syslog service resolved to agent_code/ip/port | config schema test |
| Network syslog target | remote template | inspect/apply/save/verify commands selected by vendor/platform | template unit test |
| Monitoring dispatch | existing monitor mechanism | action `monitoring.dispatch=success|failed|unknown` | fake service test |
| Real single-device execute evidence | continue-onboarding ensure path | one controller-backed monitor/log execution result or exact stage blocker is preserved durably | bounded execution evidence + focused contract validation |
| Exact closure-stage blocker truth gate | same single-device `plan -> ensure -> GET /onboarding` path | exact `ensure` blocker plus same-flow controller tuple is preserved without paraphrasing it as success | durable evidence read-back (`D2ON-024` / `D2ON-025`) + readiness/review update |
| Repaired single-device rerun | same path after config-source repair | normal `ensure` payload plus rerun tuple, or an exact remaining contract blocker, is preserved durably | bounded rerun evidence + focused contract/type gates |
| Remaining `log_forward` repair rerun | same single-device `plan -> ensure -> GET /onboarding` path after `D2ON-027` | `log_forward` no longer returns `config_source_required=true` while the controller-backed tuple stays honest, or a smaller exact blocker is preserved durably | bounded rerun evidence (`D2ON-029` / `D2ON-030`) + readiness verdict (`D2ON-031`) |
| Area listener quick-create workflow | `#/platform/area-listener-services` header buttons + card `新增` entries | each quick-create entry opens the correct preset, can save a usable listener plan, and the row becomes visible/editable/releasable in the table | browser verification + targeted UI/typecheck evidence |
| Real syslog listener publish | area listener page release modal for `server_syslog_listener` / `network_syslog_listener` | `dry-run / preflight / apply / remove` return concrete collector-side publish results instead of wrapper-only placeholder semantics | focused Go tests + live release evidence |
| Real SNMP trap listener publish | area listener page release modal for `snmp_trap_listener` | collector-side trap listener publish adapter exists and no longer closes only with adapter-gap honesty; still no device-side trap target | focused Go tests + live release evidence |
| Server log strategy | linux system default | only existing files selected, missing files ignored | strategy unit test |
| SSH timeout | remote access failure | action result `unknown` or `failed`, retryable true | fake remote runner test |
| SNMP trap unsupported profile | network trap plan for unknown vendor/platform | records exact unsupported-profile blocker instead of success | contract test `D2ON-046` / `D2ON-047` |
| Batch onboarding plan | selected Device V2 codes | per-device plan entries plus aggregate counts; no implicit filter execution | API contract test + `D2ON-043` |
| Batch onboarding ensure | two explicit selected devices | sequential per-device ensure results; one blocked device does not hide another success | API contract test + bounded live probe `D2ON-048` |
| Batch onboarding UI | multi-select `继续纳管` | guarded confirmation and per-device result rendering; server monitor-mode policy explicit | UI implementation evidence `D2ON-044` + typecheck |
| All-device collection validation gate | explicit list of every current Device V2 code | one store/start task records 17 total, 11 ready success, 6 per-device blocked/unready; unreachable devices are not global failures | live task summary/runs evidence `D2ON-045` |
| Device-side SNMP trap target profile | H3C/Comware command/profile layer | commands configure trap host, enable traps, save config, and verify readback with no controller execution claim | Go tests + `D2ON-046` |
| Device-side SNMP trap target execution | network device with managed `snmp_trap_listener` | controller remote run configures trap host, saves config, verifies readback, and records `snmp_trap_target` evidence separately from syslog | Go tests `D2ON-047` + live H3C/Comware probe `D2ON-048` |
| Unsupported SNMP trap target profile | unknown network vendor/platform | exact blocker with trap action status blocked, no success paraphrase | unit test `D2ON-047` |
| Observability query tooling | `oneops_test_tool` local APIs | Prometheus/Loki query responses include endpoint, upstream status, result type, hit count, and stream count | `go test ./cmd/oneops_test_tool` + live tool checks `D2ON-049` |
| Prometheus metric observed | selected ready device | device metrics can be queried in Prometheus, or exact no-samples/label blocker is recorded | `GET|POST /api/v1/observability/prometheus/query(_range)` + `D2ON-051` |
| Server local log observed | bounded server device local log path | server local/tail logs can be queried in Loki, or exact no-samples/task blocker is recorded | `POST /api/v1/observability/loki/query_range` + `D2ON-052` |
| Server syslog observed | bounded server syslog listener path | server syslog samples can be queried in Loki separately from local logs | `POST /api/v1/observability/loki/query_range` + `D2ON-052` |
| Network syslog observed | ready H3C/Comware network device | network syslog samples can be queried in Loki, or exact no-samples/label blocker is recorded | `POST /api/v1/observability/loki/query_range` + `D2ON-053` |
| SNMP trap observed | ready H3C/Comware trap target path | network SNMP trap samples can be queried in Loki, or exact no-samples/generation blocker is recorded | `POST /api/v1/observability/loki/query_range` + `D2ON-054` |
