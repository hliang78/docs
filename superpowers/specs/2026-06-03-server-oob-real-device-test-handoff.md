# Server OOB SNMP Real Device Test Handoff

Date: 2026-06-03

## 2026-06-03 15:05 CST Full-Device Coverage Update

This section records the follow-up full-device execution after the earlier
server and DVC65 focused retest.

Scope:

```text
platform_devices_v2 total = 49
execution mode = one async store task per device
reason = batch store is serial enough that slow controller raw calls can hold later devices
task map artifact = /tmp/per_device_store_tasks.tsv
```

Note:

```text
An earlier all-49 batch task entv2_1780469198770640401 remained running because
its serial execution was held by a slow controller raw collection call.
There is no confirmed Device V2 store cancel endpoint in the current router.
The full-coverage result below is based on the later one-device-per-task run.
```

Store result:

```text
success / ready / persist_core        22
blocked / device_collection2          19
blocked / rules                        8
missing run                            0
running after final poll               0
```

All 49 devices created a `device_v2_store_run`, so every current V2 device was
covered by a real store pipeline attempt. The 22 successful devices carried
prepared `catalog_code` and `platform_code` in their run summaries.

The 27 blocked devices failed before monitor-ready state:

```text
19 blocked at device_collection2 with device_collection2_required / target_detect_failed
8 blocked at rules with incomplete prepared profile/catalog facts
```

Full sync-to-v1 + monitor push:

```text
POST /api/v1/device/v2/sync-to-v1?monitor_push=true
payload codes = all 49 platform_devices_v2 codes

total = 49
failed = 27
created = 8
skipped/refreshed = 14
monitor_push_status = success
```

Interpretation:

```text
22 store-ready devices reached sync-to-v1 / monitor push
27 blocked devices returned structured "device profile incomplete" failures
monitor push succeeded for the eligible device set
```

Agent-side redacted verification:

```text
agent task file = /home/sy_cmsr/app/agent/data/telegraf_tasks/tasks.json

total tasks = 38
ping tasks = 22
snmp tasks = 14
processor/output shared tasks = 2

expected ping tasks for 22 successful devices = 22
missing expected ping tasks = 0

snmp v2c tasks with community = 13
snmp v3 tasks with auth_password = 1
snmp tasks using public community = 0
```

No secret material was copied into this handoff; the agent-side evidence only
records boolean credential presence and public-community checks.

Fresh reconcile:

```text
POST /api/v2/platform/monitoring/tasks:reconcile
scope.agent_code = agent-001
scope.pull_from_agent = true
scope.write_back = true

platform_count = 38
runtime_task_count = 38
runtime_config_missing = 0
runtime_graph_buildable = true
drift_count = 0
```

Artifacts:

```text
/tmp/per_device_store_tasks.tsv
/tmp/per_device_store_results.tsv
/tmp/per_device_store_status_matrix.tsv
/tmp/per_device_success_prepared_codes.tsv
/tmp/all_devices_sync_monitor_response.json
/tmp/all_agent_tasks_redacted.json
/tmp/reconcile_all_devices_response.json
/tmp/final_store_summary_counts.tsv
/tmp/final_sync_summary.json
/tmp/final_reconcile_summary.json
```

## Scope

This handoff records the current live-environment test status for server OOB SNMP collection and monitoring push.

The goal is not to mark the whole chain as closed. The current result is:

```text
server OOB SNMP gate: mostly verified on one reachable OOB device
server in-band SNMP guard: verified for no in-band SNMP credential
network default fallback excluding SERVER: verified
network SNMP monitoring push: code-level gate bug fixed; live retest still required
```

## 2026-06-03 14:40 CST Live Retest Update

This section supersedes the earlier "live retest still required" notes below.

### Code fix applied during retest

Server store was blocked by an internal summary inconsistency:

```text
candidate_engine.resolved_ref_codes.platform_code/catalog_code were present
prepared_facts.profile.platform_code/catalog_code were empty
schema gate only consumed prepared_facts, so server runs ended schema_required_missing
```

Fix:

```text
app/entity/v2/service/impl/device_v2_store_runtime.go
  backfill prepared_facts.profile.*_code from candidate_engine.resolved_ref_codes
  before applying prepared facts to store candidates
  before schema gate evaluation
```

Tests:

```bash
go test ./app/entity/v2/service/impl -run 'Test(BuildMinimalDeviceV2StoreGateBackfillsResolvedRefCodesFromCandidateEngine|StartPipeline_DeviceV2StoreRuntime_ReappliesCandidateEngineAfterDC2Facts|ApplyMinimalDeviceV2CandidateEngineResolvedRefs_WritesPreparedFactCodes)' -count=1
```

Result: passed.

### Server real-device store result

Task:

```text
entv2_1780468102038360396
```

Final task status:

```text
overall_status=success
current_stage=done
message=device_v2 pipeline finished: total=3 success=3 created=0 next_manage=3 manage_submitted=3
```

Store runs:

```text
DVC04A63FD6E3C4  success  core_store=success  manageable=ready  platform_code=PLT20231020001  catalog_code=CATL20231020003
DVC94FA66E51531  success  core_store=success  manageable=ready  platform_code=PLT20231020001  catalog_code=CATL20231020003
DVCE0CD921DAA5F  success  core_store=success  manageable=ready  platform_code=PLT20231020001  catalog_code=CATL20231020003
```

DC2 sidecar result:

```text
all three store runs had device_collection2.status=partial / reason=run_partial
DVC94FA66E51531 OOB SNMP probe status=success
DVC04A63FD6E3C4 OOB SNMP probe status=failed
DVCE0CD921DAA5F OOB SNMP probe status=failed
```

This means the longest store chain verified:

```text
V2 task -> prepare -> DC2 real-device detect/collect -> candidate engine ref code materialization
-> schema gate -> core store -> manage submitted
```

The previous `schema_required_missing:platform_code/catalog_code` blocker is fixed for the real server devices.

### Server sync-to-v1 and monitoring push

Final call:

```text
/api/v1/device/v2/sync-to-v1?monitor_push=true
task_id=entv2_1780468102038360396
```

Result:

```text
total=3
failed=0
monitor_push=true
monitor_push_status=success

DVC04A63FD6E3C4 -> DEV20260603000004
DVC94FA66E51531 -> DEV20260603000001
DVCE0CD921DAA5F -> DEV20260603000003
```

Credential binding evidence from sync response:

```text
all three server devices refreshed existing V1 rows
all three reported in-band management + out-band management + out-band SNMP SecretHub bindings
```

### Agent-side task and credential verification

Agent task file:

```text
/home/sy_cmsr/app/agent/data/telegraf_tasks/tasks.json
```

Redacted server task evidence:

```text
collect_agent-001_ping-basic_172_21_148_236_161  enabled=true  plugin=ping
collect_agent-001_ping-basic_172_21_144_1_161    enabled=true  plugin=ping
collect_agent-001_ping-basic_172_21_144_76_161   enabled=true  plugin=ping

collect_agent-001_snmp-passthrough_172_21_160_1_161
  enabled=true
  plugin=snmp
  access_plane=out_band
  credential_binding=snmp_outband
  has_community=true
  has_public=false
```

Interpretation:

```text
DVC94FA66E51531 has real OOB SNMP success and got the server_oob_snmp task.
DVC04A63FD6E3C4 and DVCE0CD921DAA5F had OOB SNMP probe failure, so they did not get OOB SNMP tasks.
All three have ping tasks.
No secret value was copied into this handoff; only boolean credential checks are recorded.
```

### Network real-device retest

Root cause found for DVC65:

```text
network strategy set 4284353d-1233-4022-ad18-871b3d8444c7 selects leaf strategies
DVC65F6466753AB is FIREWALL + H3C SecPath
existing H3C SNMP leaf only matched Comware, so DVC65 only received ping
```

Data/config fix:

```text
inserted SNMP leaf strategy:
id=4c902a48-5f12-11f1-a9bb-0242ac14000c
name=H3C SecPath 防火墙 SNMP监控策略
parent_id=baf7bb34-86b7-45f8-8e28-2afce170966a
template=snmp-passthrough
catalog=FIREWALL
platform=SecPath
```

Backup artifact:

```text
/tmp/platform_teleabs_strategy_snmp_before_secpath.sql
```

DVC65 quick apply after fix:

```text
success_count=2
fail_count=0
selected SNMP task=collect_agent-001_snmp-passthrough_172_21_166_35_161
selected ping task=collect_agent-001_ping-basic_172_21_166_35_161
```

Agent-side DVC65 evidence:

```text
collect_agent-001_snmp-passthrough_172_21_166_35_161
  enabled=true
  plugin=snmp
  has_community=true
  has_public=false

collect_agent-001_ping-basic_172_21_166_35_161
  enabled=true
  plugin=ping
```

DB apply record:

```text
task_id=collect_agent-001_snmp-passthrough_172_21_166_35_161
strategy_id=4c902a48-5f12-11f1-a9bb-0242ac14000c
template_id=snmp-passthrough
device_count=1
applied_at=2026-06-03 14:06:15.124
```

### Reconcile

Final reconcile after server store, monitor push, and DVC65 recheck:

```text
platform_count=22
runtime_task_count=22
runtime_config_missing=0
drift_count=0
```

Artifacts:

```text
/tmp/server_store_retry_after_code_fix.json
/tmp/server_sync_monitor_push_final_after_store_success.json
/tmp/reconcile_final_after_server_store_success.json
/tmp/server_agent_tasks_redacted_after_code_fix.json
/tmp/reconcile_after_dvc65_secpath_snmp.json
```

## Fix Update

The previously suspicious network SNMP symptom was rechecked at code level.

Root cause:

```text
SNMP probe gate was applied to every SNMP strategy set.
Network SNMP strategies were therefore treated like server SNMP strategies.
Network devices usually do not carry server-style in_band_snmp_probe_status.
The network SNMP strategy was skipped, and stale SNMP tasks could be removed.
```

Fix:

```text
network SNMP strategy set:
  requires SNMP credential availability
  does not require server SNMP probe status

server in-band SNMP strategy set:
  requires in-band SNMP credential
  requires in_band_snmp_probe_status=success

server OOB SNMP strategy set:
  requires out_band_ip
  requires out_band:snmp / snmp_outband credential
  requires out_band_snmp_probe_status=success
```

Code touched:

```text
OneOps/app/device/service/impl/device_store_controller.go
OneOps/app/device/service/impl/device_store_controller_test.go
OneOps/app/platform/service/impl/strategy_apply_v2_test.go
```

Tests added or verified:

```text
TestTryNotifyMonitorProbeByStrategySelectorSets_NetworkSNMPDoesNotRequireProbe
TestTryNotifyMonitorProbeByStrategySelectorSets_SkipsInBandSNMPWhenProbeMissing
TestStrategyApplyV2Srv_EnrichDevicesCredentialsForPlugin_UsesInBandSNMPRef
```

Verification commands:

```bash
go test ./app/device/service/impl -run 'TestTryNotifyMonitorProbeByStrategySelectorSets_NetworkSNMPDoesNotRequireProbe|TestTryNotifyMonitorProbeByStrategySelectorSets_SkipsInBandSNMPWhenProbeMissing' -count=1

go test ./app/device/service/impl -run 'TestMonitoringDefaultNetworkFallback|TestMonitoringFilterDefaultNetworkFallback|TestMonitoringFilter|TestMonitoringStrategySelectorGroupRequiresOOBSNMP|TestMonitoringCredentialBindingRequirementsForStrategySet|TestDeviceV2HasAnyCredentialBinding|TestTryNotifyMonitorProbeByStrategySelectorSets|TestNotifyMonitorProbe_StrategySelectorAutoApply|TestEnrichMonitoringApplyDevicesFromCredentialSources' -count=1

go test ./app/platform/service/impl -run 'TestStrategyApplyV2Srv_EnrichDevicesCredentialsForPlugin_UsesInBandSNMPRef|TestStrategyApplyV2Srv_EnrichDevicesCredentialsForPlugin_UsesSNMPOutbandForOOBTarget|TestStrategyApplyV2Srv_ApplyStrategyAndPush_ServerOOBStrategySetUsesOutBandTargetAndCredential' -count=1
```

All three commands passed. `git diff --check` also passed.

Live retest is still required because the running OneOps process may need restart before the fixed gate takes effect.

## SNMP v3 Credential Impact

Code-level conclusion:

```text
SNMP v3 credentials should not block monitoring task push by themselves.
The strategy apply path resolves credential_refs.snmp / credential_refs.out_band:snmp by usage.
The SNMP renderer recognizes v3 USM fields and renders version=3.
The renderer does not require community when v3 USM fields are present.
```

Required v3 material:

```text
sec_name
sec_level
auth_protocol + auth_password when sec_level is authNoPriv/authPriv
priv_protocol + priv_password when sec_level is authPriv
context_name optional
```

Important distinction:

```text
community_non_empty=false in logs does not mean SNMP v3 credential is missing.
For v3, check credential_keys for sec_name/sec_level/auth_protocol/auth_password/priv_protocol/priv_password.
Final TOML should contain version = 3 and must not fall back to community = "public".
```

Tests verified:

```bash
go test ./app/platform/service/impl -run 'TestStrategyApplyV2Srv_ApplyStrategyAndPush_SNMPV3CredentialRefRendersTransferAndRedactedRecord|TestStrategyApplyV2Srv_ApplyStrategyAndPush_SNMPV3CredentialRefSecurityLevelsRenderTransferConfig|TestGenerateFromStrategy_SNMPV3CredentialsRenderFinalTOML|TestMetricStrategyTargetResolverCredentialsFromTargetConfig_KeepsSNMPV3USMFields|TestMonitoringV2WizardService_ApplyPlan_InjectsResolvedSNMPV3DeviceCredentials|TestMonitoringV2TaskProjection_ListRuntimeViewIncludesSNMPV3GatherHealth' -count=1

go test ./app/device_collection2/service/impl -run 'TestDeviceV2ToDC2TargetReadsInlineSNMPV3USMAccess|TestCollectSNMPV3USMResolvesCredentialRefBeforeController|TestCollectSNMPV3USMSecurityLevelsResolveCredentialRefBeforeController' -count=1
```

Both commands passed.

Risk to watch:

```text
Old Device V1 community compatibility APIs are community-oriented.
If a future/live path resolves SNMP through GetDeviceCommunity* or CommunityResp only, SNMP v3 may fail or be treated as missing community.
The preferred monitoring path should use credential_refs + CredentialResolver, not legacy community-only lookup.
```

Live acceptance check for v3:

```text
agent task config contains version = 3
agent task config contains sec_name and expected auth/priv fields
agent task config does not contain community = "public"
agent task is not skipped only because community_non_empty=false
```

## Forced OOB SNMP v3 Push Check

Device used:

```text
DVC6BD96FBD0403
OOB address: 172.31.11.106
strategy_set_id: server_oob_snmp
template_id: snmp-passthrough
credential binding: snmp_outband / out_band:snmp
```

Bug found during force-push:

```text
The pushed task rendered as SNMP v2 with community=public.
The device credential was actually SNMP v3 USM.
```

Root causes:

```text
snmp_v3_usm had no default Vault field mapping, so v3 fields were dropped.
explicit credential_ref resolution could return empty credentials and then fall back to default SNMP material.
```

Fix:

```text
defaultVaultFieldMapping(snmp_v3_usm) now maps version/sec_name/sec_level/auth/priv/context fields.
explicit credential_ref resolution now fails closed when the ref cannot produce usable credentials.
```

Live result after OneOps/controller restart and force-push:

```text
success_count=1
agent=agent-001
task_id=collect_agent-001_snmp-passthrough_DVC6BD96FBD0403
address=udp://172.31.11.106:161
version=3
credential_binding=snmp_outband
monitoring_profile=server_oob_snmp
access_plane=out_band
community=public not present
```

This credential is `authNoPriv`, so the valid task has auth fields but no priv fields:

```text
sec_name present
sec_level present
auth_protocol present
auth_password present
priv_protocol absent
priv_password absent
```

Stale cleanup:

```text
Removed old bad task:
collect_agent-001_snmp-passthrough_172_31_11_106_161

Current agent task file has only one matching task for 172.31.11.106 / DVC6BD96FBD0403.
The remaining task is SNMP v3 and has no public community fallback.
```

## Environment

```text
OneOps API: http://127.0.0.1:8080
Auth header: X-Auth-Token: <debug token>
Agent task file: /home/sy_cmsr/app/agent/data/telegraf_tasks/tasks.json
Device list artifact: /tmp/device_v2_list.json
Store task artifact: /tmp/oob_sample_task_runs.json
Sync artifact: /tmp/oob_sample_sync_push.json
Strategy set artifact: /tmp/teleabs_strategy_set_4284353d.json
Strategy list artifact: /tmp/teleabs_strategies.json
```

Do not paste database passwords or SNMP community strings into future notes.

## Routes

Teleabs strategy APIs are under:

```text
/api/v1/platform/metrics/teleabs/strategy-sets
/api/v1/platform/metrics/teleabs/strategies
```

The path below returned 404 and should not be used:

```text
/api/v1/platform/teleabs/strategy-sets
```

## Sample Devices

Network samples:

```text
DVCEFB68A85655D  SWITCH    172.21.165.17
DVC65F6466753AB  FIREWALL  172.21.166.35
DVCF250553DECB7  ROUTER    172.21.165.4
```

Server/OOB samples:

```text
DVC94FA66E51531  SERVER     in-band=172.21.144.1    oob=172.21.160.1
DVCE0CD921DAA5F  device_v2  in-band=172.21.144.76   oob=172.21.162.16
DVC04A63FD6E3C4  device_v2  in-band=172.21.148.236  oob=172.21.164.1
```

## Commands Used

Start store/collection:

```bash
curl -sS -X POST -H 'X-Auth-Token: <debug token>' -H 'Content-Type: application/json' \
  -d '{"codes":["DVCEFB68A85655D","DVC65F6466753AB","DVCF250553DECB7","DVC94FA66E51531","DVCE0CD921DAA5F","DVC04A63FD6E3C4"],"options":{"async":true,"device_collection2":{"enabled":true,"store_pipeline_probe_enabled":true}}}' \
  'http://127.0.0.1:8080/api/v1/device/v2/store/start'
```

Store task id:

```text
entv2_1780460064915931816
```

Sync to v1 and push monitoring:

```bash
curl -sS -X POST -H 'X-Auth-Token: <debug token>' -H 'Content-Type: application/json' \
  -d '{"codes":["DVCEFB68A85655D","DVC65F6466753AB","DVCF250553DECB7","DVC94FA66E51531","DVCE0CD921DAA5F","DVC04A63FD6E3C4"],"monitor_push":true}' \
  'http://127.0.0.1:8080/api/v1/device/v2/sync-to-v1?monitor_push=true'
```

Inspect agent tasks:

```bash
jq -r '
  def has($s): (.config|contains($s));
  .tasks[]
  | [.task_id,
     (if has("server_oob_snmp") then "server_oob_snmp"
      elif has("SNMP网络监控策略") then "network_snmp"
      elif (.task_id|contains("snmp-passthrough")) then "snmp"
      elif (.task_id|contains("ping-basic")) then "ping"
      else "other" end),
     (if has("credential_binding = \"snmp_outband\"") then "snmp_outband"
      elif has("credential_binding = \"snmp\"") then "snmp_inband"
      else "no_binding_tag" end)]
  | @tsv' /home/sy_cmsr/app/agent/data/telegraf_tasks/tasks.json
```

## Store Result

Observed store run status:

```text
DVCEFB68A85655D  success  persist_core
DVC65F6466753AB  success  persist_core
DVCF250553DECB7  success  persist_core
DVC94FA66E51531  blocked  rules
DVCE0CD921DAA5F  success  persist_core
DVC04A63FD6E3C4  success  persist_core
```

Important: `DVC94FA66E51531` has reachable OOB SNMP and did receive OOB monitoring, but its store run still ended `blocked/rules`. Next tester should inspect the specific rule blocker before calling server onboarding closed.

## Sync Result

The 6-device sync-to-v1 call returned:

```text
total=6
created=3
skipped=3
failed=0
monitor_push=true
monitor_push_status=success
```

Credential binding summary from the sync response:

```text
network devices: in-band mgmt + in-band SNMP
DVC94FA66E51531: in-band mgmt + out-band mgmt + out-band SNMP
DVCE0CD921DAA5F: in-band mgmt + out-band mgmt + out-band SNMP
DVC04A63FD6E3C4: in-band mgmt + out-band mgmt + out-band SNMP
```

## Agent Task Result

Current agent tasks include:

```text
server OOB SNMP:
collect_agent-001_snmp-passthrough_172_21_160_1_161
  monitoring_profile=server_oob_snmp
  credential_binding=snmp_outband
  access_plane=out_band
  source_address=172.21.160.1

server in-band SNMP:
no task for 172.21.144.1
no task for 172.21.144.76
no task for 172.21.148.236

unverified/unreachable OOB SNMP:
no task for 172.21.162.16
no task for 172.21.164.1

network samples:
ping tasks exist for 172.21.165.17, 172.21.166.35, 172.21.165.4
SNMP tasks for these three sample IPs are not present after the latest push
```

This matches the intended server guard:

```text
in-band SNMP is pushed only when in-band SNMP credential and in-band SNMP probe are both present
OOB SNMP is pushed only when OOB SNMP credential and OOB SNMP probe success are both present
```

## Strategy Set State

Current strategy sets:

```text
server_oob_snmp                         服务器带外SNMP监控套件  enabled=true auto_apply_on_store=true
43e00e73-8cb5-4636-b6a2-216a67a32084   服务器远程监控套件      enabled=true auto_apply_on_store=true
4284353d-1233-4022-ad18-871b3d8444c7   网络监控套件          enabled=true auto_apply_on_store=true
bef148ff-2c60-4f39-b0ca-468b315788e8   NVR监控套件           enabled=true
```

`网络监控套件` currently contains two enabled items:

```text
SNMP网络监控策略  template=snmp-passthrough  plugin=snmp
ICMP探活          template=ping-basic        plugin=ping
```

So the network set is not simply "ping only".

## Findings

1. SERVER is no longer picked by the default network fallback.

2. `DVC94FA66E51531` correctly received an OOB SNMP task on `172.21.160.1` using `snmp_outband`; its in-band IP `172.21.144.1` did not receive SNMP.

3. OOB candidates without successful OOB SNMP probe did not receive OOB SNMP tasks.

4. Server in-band SNMP strategy was skipped when only OOB SNMP exists. Logs show `monitoring apply skip: credential binding missing` for the server in-band SNMP strategy.

5. Network SNMP push needs live retest after restarting OneOps with the gate fix. The code-level credential bridge has a unit test for `credential_refs.snmp -> SNMP render credential`, so the previous "credential propagation suspicious" hypothesis is no longer the leading explanation.

6. There are stale or unrelated current SNMP tasks for other network IPs:

```text
collect_agent-001_snmp-passthrough_172_21_253_9_161
collect_agent-001_snmp-passthrough_172_31_131_51_161
```

They do not prove the latest sample network push is healthy.

## Inventory Snapshot

From `/tmp/device_v2_list.json`:

```text
FIREWALL  3
ROUTER    1
SERVER    1
SWITCH    8
device_v2 36
```

Many `device_v2` rows have `in_band:ssh + out_band:snmp` but do not yet have resolved `catalog_name=SERVER` in the list projection. Future all-device testing should not assume all OOB devices are already classified as SERVER.

## Next Test Plan

1. Restart OneOps so the fixed monitoring gate is active.

2. Re-run the 3 network samples and confirm all three have `snmp-passthrough` tasks with non-empty SNMP credentials.

3. Re-run `DVC94FA66E51531` and confirm only `172.21.160.1` has `server_oob_snmp`.

4. Pick 3 more OOB devices from the generic `device_v2` group and run store with probe enabled. Expected result:

```text
probe success -> server_oob_snmp task can be pushed after SERVER classification
probe failure -> no OOB SNMP monitoring task
```

5. If a network SNMP task renders but the agent cannot execute it, check for a separate agent-side dependency issue. Earlier logs showed `snmptranslate` missing in at least one run; that is separate from the monitoring gate bug.

6. Only after the above passes, run full current inventory in batches of 5 to 10 devices. Keep before/after snapshots of `tasks.json`.

## Code Areas To Inspect Next

Likely relevant files:

```text
app/device/service/impl/device_store_controller.go
app/platform/service/impl/monitoring_task_v3_target_credentials.go
app/platform/service/impl/monitoring_task_v3_target_metadata.go
app/platform/service/impl/monitoring_task_v3_api_target_resolver.go
app/platform/service/impl/strategy_apply_transfer_v2.go
app/platform/service/impl/telegraf_config_generator_impl.go
```

If live retest still fails, look specifically for the path:

```text
Device V2 attributes.credential_refs.snmp
  -> sync-to-v1 credential source bridge
  -> monitoring apply target credentials
  -> SNMP strategy render credentials.community
```

Do not weaken the server guard while fixing network SNMP. The desired rule remains:

```text
network devices: default network set can push SNMP after successful collection and SNMP credential availability
servers: SNMP push requires explicit server strategy set plus plane-specific SNMP probe success
```
