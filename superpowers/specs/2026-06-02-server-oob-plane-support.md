# Server OOB Plane Support

## 1. Core Statements

OOB is not a device type.

OOB is another access plane of a server.

In-band represents the OS and service-side access plane.

Out-of-band represents the BMC or management-controller access plane.

Device v2 should model OOB once, then let ingestion and monitoring reuse the same model.

The shared model is `access_points + credential_refs`.

The standard OOB SNMP expression is:

```json
{
  "out_band_ip": "10.1.1.5",
  "access_points": [
    {
      "plane": "out_band",
      "protocol": "snmp",
      "ip": "10.1.1.5",
      "port": 161,
      "credential_ref": "cred-oob-snmp"
    }
  ],
  "credential_refs": {
    "out_band:snmp": "cred-oob-snmp"
  }
}
```

`out_band_ip` is only an address.

`out_band:snmp` is the credential binding that makes OOB SNMP actionable.

Without `out_band_ip`, there is no OOB target address.

Without `out_band:snmp`, there is no OOB SNMP credential.

## 2. Field Semantics

`snmp_credential_ref` is the old generic SNMP field.

`snmp_credential_ref` should remain compatible with current in-band SNMP behavior.

When a row has `out_band_ip` but no `in_band_ip`, `snmp_credential_ref` may be conservatively interpreted as OOB SNMP.

When a row has both `in_band_ip` and `out_band_ip`, OOB SNMP must be explicit.

Explicit OOB SNMP means `credential_refs.out_band:snmp`.

`credential_ref_out_band` is not the same as `out_band:snmp`.

`credential_ref_out_band` means generic OOB credential, usually CLI-like access.

`out_band:snmp` means SNMP access on the OOB plane.

Future protocols should reuse the same model:

```text
out_band:redfish
out_band:ipmi
out_band:snmp
```

## 3. Ingestion Flow

Device v2 ingestion does not directly collect SNMP.

Device v2 ingestion only writes the target material.

The actual SNMP request is executed by DC2/controller.

The OOB SNMP ingestion flow is:

```text
device v2 attributes
  -> normalize access_points and credential_refs
  -> build DC2 target
  -> select out_band_ip
  -> bind out_band:snmp
  -> controller detect
  -> DC2 RunManual
  -> controller executes SNMP
  -> DC2 writes facts
  -> device v2 store merges facts
```

Controller reachability is required.

Controller must be able to reach `out_band_ip`.

Controller must support SNMP execution.

Controller must be able to resolve and use the OOB SNMP credential.

OOB SNMP is not a way to bypass controller.

OOB SNMP is a way to give controller a different target plane.

## 4. Ingestion Gate

Do not loosen the existing server Linux or Windows gate.

`server_linux` requires in-band CLI material.

`server_windows` requires WinRM or compatible in-band material.

OOB SNMP should not satisfy the Linux SSH gate.

OOB SNMP should not satisfy the Windows WinRM gate.

Use a separate OOB contract:

```text
server_oob_snmp
```

`server_oob_snmp` requires:

```text
out_band_ip
out_band:snmp or equivalent SNMP material
```

`server_oob_snmp` should not require SSH.

`server_oob_snmp` should not require WinRM.

If OOB address is missing, the gate reason should be OOB-address-specific.

If OOB SNMP credential is missing, the gate reason should be OOB-credential-specific.

Recommended reasons:

```text
target_missing_oob_address
target_missing_oob_snmp_credential
```

## 5. Collection Contract

Do not reuse the full network-device SNMP contract for server OOB.

Server OOB SNMP should start with a lightweight contract.

Recommended initial datasets:

```text
snmp_sys_descr
snmp_entPhysicalEntry
```

Recommended logical dataset names:

```text
oob_snmp_identity
oob_snmp_ent_physical
oob_snmp_firmware
oob_snmp_health
```

`snmp_entPhysicalEntry` can help enrich:

```text
serial number
manufacturer
model
firmware revision
hardware revision
software revision
physical component inventory
```

Do not write OOB `ifTable` into server OS interface baseline.

Do not treat BMC network ports as OS network interfaces.

Do not merge OOB IP data into server business IP facts.

OOB data belongs to hardware, firmware, BMC, and chassis-health dimensions.

## 6. Target Selection

If a server has usable in-band CLI or WinRM credentials, prefer in-band collection.

In-band collection has higher fact value for OS identity, CPU, memory, disk, interfaces, routes, and OS software.

If a server has no usable in-band CLI or WinRM credentials but has OOB SNMP, select OOB SNMP.

Selection logic:

```text
if SERVER and has in-band CLI/WinRM:
    use in-band server contract
else if SERVER and has out_band_ip + out_band:snmp:
    use server_oob_snmp
else:
    remain not ready or fail with precise gate reason
```

The store summary should record the selected target.

Recommended summary fields:

```text
selected_access_plane
selected_protocol
selected_address
selected_credential_key
```

Example:

```json
{
  "selected_access_plane": "out_band",
  "selected_protocol": "snmp",
  "selected_address": "10.1.1.5",
  "selected_credential_key": "out_band:snmp"
}
```

These fields are for troubleshooting.

They answer which plane was used, which protocol was used, and which credential binding was selected.

## 7. Monitoring Strategy

Monitoring should use a separate OOB strategy set.

Do not silently extend the existing in-band server SNMP strategy.

In-band SNMP and OOB SNMP have different addresses.

In-band SNMP and OOB SNMP have different credential bindings.

In-band SNMP and OOB SNMP have different metric meanings.

Recommended strategy sets:

```text
server_basic
server_os_linux
server_os_windows
server_snmp_inband
server_oob_snmp
server_oob_redfish
server_oob_ipmi
```

`server_snmp_inband` should use:

```text
address = in_band_ip
credential = snmp or in_band:snmp
```

`server_oob_snmp` should use:

```text
address = out_band_ip
credential = snmp_outband or out_band:snmp
```

Do not let `snmp` and `snmp_outband` fall back to each other.

`snmp` means in-band SNMP.

`snmp_outband` means OOB SNMP.

The monitoring gate must be plane-aware.

In-band monitoring checks in-band credentials.

OOB monitoring checks OOB credentials.

## 8. Strategy And Strategy Set Relationship

A strategy set decides which devices should receive monitoring.

A strategy decides what monitoring task should be generated.

The strategy set is the container.

The strategy is the concrete collection action.

The simple relationship is:

```text
strategy set = device matching + auto-apply policy + output policy + strategy grouping
strategy     = one monitoring template or one collection action
```

For server OOB SNMP, the recommended model is:

```text
server_oob_snmp strategy set
  match:
    catalog = SERVER
    out_band_ip exists
    credential_refs.out_band:snmp exists
  auto_apply_on_store:
    true
  output:
    prometheus/http push/current monitoring output
  strategies:
    oob_snmp_identity
    oob_snmp_hardware_health
    oob_snmp_firmware
    oob_snmp_power_thermal
```

The strategy set answers:

```text
which servers should get OOB monitoring
```

The strategy answers:

```text
which OOB metric family should be collected
```

The in-band strategy set should remain separate:

```text
server_snmp_inband strategy set
  match:
    catalog = SERVER
    in_band_ip exists
    snmp or in_band:snmp exists
  strategies:
    server_snmp_basic
```

The OOB strategy set should be separate:

```text
server_oob_snmp strategy set
  match:
    catalog = SERVER
    out_band_ip exists
    out_band:snmp exists
  strategies:
    server_oob_snmp_basic
```

A single server may need both:

```text
same SERVER
  -> server_snmp_inband  -> in-band SNMP task
  -> server_oob_snmp     -> OOB SNMP task
```

This is conceptually valid.

The current auto-apply implementation must be checked carefully.

If auto-apply claims a device only by `device_code`, the first matched strategy set may block later strategy sets.

That behavior is safe for competing strategy sets.

That behavior is not enough for in-band and OOB coexistence.

For OOB support, auto-apply claim should be plane-aware.

Recommended claim key:

```text
device_code + access_plane + protocol
```

Example:

```text
DEV-1|in_band|snmp
DEV-1|out_band|snmp
```

This allows one server to receive both in-band SNMP and OOB SNMP in the same push run.

Alternative short-term workaround:

```text
put in-band and OOB strategy groups into one strategy set
```

The long-term recommendation is:

```text
keep strategy sets separate
make auto-apply claim plane-aware
```

OOB strategy metadata should be explicit:

```json
{
  "monitoring_profile": "server_oob_snmp",
  "access_plane": "out_band",
  "protocol": "snmp",
  "credential_binding": "snmp_outband"
}
```

Do not infer OOB only from the word `snmp`.

Do not infer OOB only from server catalog.

OOB requires an explicit plane signal.

## 9. Monitoring Data Display

Strategy sets should be separate.

Device display should be merged.

The server page should show one server, not two devices.

Metrics should carry plane labels.

Recommended labels:

```text
device_code
plane = out_band
protocol = snmp
source = bmc
```

Display groups should separate OS and OOB health.

Recommended page sections:

```text
Server overview
In-band status
Out-of-band status
OS monitoring
OOB monitoring
Hardware health
BMC health
Power
Fan
Temperature
Firmware
```

OOB metrics can affect:

```text
hardware health
BMC health
power health
fan health
temperature health
firmware visibility
OOB reachability
```

OOB metrics should not affect:

```text
OS interface health
OS IP inventory
business network baseline
OS CPU metrics
OS memory metrics
OS disk metrics
```

The display rule is:

```text
strategy sets are separate
metric storage is plane-labeled
device detail page is merged
health dimensions are separated
```

## 10. Failure Boundaries

If controller is unavailable, OOB SNMP collection cannot run.

If controller cannot reach `out_band_ip`, OOB SNMP collection fails.

If controller detect says SNMP is unavailable, OOB SNMP datasets should be filtered.

If `server_oob_snmp` contract is missing, OOB SNMP collection cannot run.

If MIB tree is required but missing, OOB SNMP standardization cannot run.

If OOB SNMP returns interface tables, those records must not be merged into server OS interface baseline.

Gate failures should be precise.

Transport failures should be visible.

Target selection should be visible.

Credential binding should be visible by key, not by secret.

## 11. Implementation Order

Recommended order:

```text
1. Normalize OOB model
2. Build OOB SNMP DC2 target
3. Add server_oob_snmp contract and gate
4. Add monitoring snmp_outband binding
5. Add server_oob_snmp monitoring strategy set
6. Make monitoring auto-apply claim plane-aware
7. Add OOB-specific health and firmware datasets
8. Add display grouping for OOB health
```

Do not start by changing display.

Do not start by loosening gates.

Start by making the access plane explicit.

Then make collection and monitoring consume that explicit model.

## 12. One-Line Summary

Server OOB support means modeling `out_band + protocol + credential_ref` as a first-class access plane, then letting ingestion and monitoring use that plane through separate contracts, separate gates, and separate display dimensions.

## 13. Longest-Chain Acceptance

Longest-chain acceptance should validate the full path, not only Device V2 attributes.

The chain is:

```text
Excel import
  -> Device V2 attributes
  -> V1 bridge sync
  -> monitor push
  -> strategy set selection
  -> target resolution
  -> credential resolution
  -> controller dispatch
  -> agent task/config
  -> Telegraf input target
```

The server test device is:

```text
device_v2_code = DVC94FA66E51531
in_band_ip = 172.21.144.1
out_band_ip = 172.21.160.1
in_band credential = credential_refs.in_band:ssh
out_band credential = credential_refs.out_band:snmp
```

The Device V2 precondition must be:

```text
credential_ref_out_band is empty
snmp_credential_ref is empty unless explicitly in-band
credential_refs.out_band:snmp exists
credential_refs.out_band:ssh does not exist
access_points has in_band ssh
access_points has out_band snmp
```

The V1 bridge precondition is:

```text
GET /api/v1/device/v2/{code}/v1-bridge
```

If the bridge is missing, the longest chain starts with:

```text
POST /api/v1/device/v2/sync-to-v1?monitor_push=true
```

with body:

```json
{
  "codes": ["DVC94FA66E51531"],
  "monitor_push": true
}
```

Monitoring acceptance should prove these facts:

```text
1. monitor_push_status becomes success
2. a monitoring task exists for the device or its V1 bridge code
3. the OOB SNMP task address is 172.21.160.1
4. the OOB SNMP task port is 161
5. the credential usage resolves to out_band:snmp / snmp_outband
6. the task carries plane=out_band and protocol=snmp metadata
7. the agent-side config contains udp://172.21.160.1:161 or equivalent SNMP agent address
8. the in-band SSH task, if present, remains separate from the OOB SNMP task
```

Failure interpretation:

```text
missing V1 bridge -> sync-to-v1 issue, not OOB model issue
missing strategy set -> monitoring strategy configuration issue
missing agent -> agent selection or capability issue
missing OOB address in task -> target resolver issue
missing OOB credential in task -> credential resolver issue
agent config absent after successful push -> controller/agent dispatch issue
```

Do not accept the chain based only on Device V2 fields.

Device V2 fields are only the first checkpoint.

## 14. 2026-06-03 Longest-Chain Negative Finding

Test input:

```text
source file = /OneOPS/OneOps/scripts/test_data2.xlsx
device_v2_code = DVC94FA66E51531
device_v1_code = DEV20260603000001
in_band_ip = 172.21.144.1
out_band_ip = 172.21.160.1
out_band:snmp credential_ref = ingest_snmp_975BF891C80C
agent = agent-001
controller = quickenv-demo-core-defaultarea-10-0-110-251
```

Environment fix needed for acceptance:

```text
agent protocol.controller_address must point to controller bidi address 127.0.0.1:7073
127.0.0.1:7273 caused agent offline and monitor push dispatch failure
```

Invalid test path:

```text
the current platform has no independent server_oob_snmp monitoring suite
the observed OOB task was produced by appending an OOB target into the existing in-band server SNMP strategy group
this is not an acceptable longest-chain test
```

Reason:

```text
OOB target must not be delivered by an in-band strategy set
OOB strategy set ownership must stay separate from in-band strategy set ownership
OOB enable/disable, task identity, display grouping, and alarm ownership must be controlled independently
existing server in-band SNMP monitoring must not implicitly create OOB SNMP monitoring
```

Current positive checkpoints:

```text
device import carries out_band_ip
device import carries access_points[plane=out_band, protocol=snmp]
device import carries credential_refs.out_band:snmp
sync-to-v1 can carry OOB SNMP credential material
target resolver can render an OOB SNMP address when explicitly requested by OOB metadata
credential resolver can map OOB SNMP target to snmp_outband
```

Required missing piece:

```text
add an independent server_oob_snmp strategy set
the strategy set should be catalog=SERVER
the strategy set should be auto_apply_on_store=true only when the environment wants OOB SNMP monitoring
the strategy set should select only devices that have out_band_ip + out_band:snmp
the strategy set should render target address from out_band_ip / OOB SNMP access point
the strategy set should resolve credential usage as snmp_outband
```

Correct acceptance path:

```text
1. confirm server_oob_snmp strategy set exists
2. confirm normal server in-band strategy set does not include OOB targets
3. import DVC94FA66E51531 with in-band SSH and OOB SNMP
4. sync-to-v1 succeeds
5. monitor push applies the in-band server strategy set to in-band targets only
6. monitor push applies the server_oob_snmp strategy set to OOB SNMP targets only
7. agent receives a task with udp://172.21.160.1:161 from the OOB strategy set
8. task metadata carries plane=out_band and protocol=snmp
9. task credential usage is snmp_outband / out_band:snmp
```

Interpretation:

```text
the previous longest-chain result is invalid
it proved that the renderer can technically collect OOB SNMP
it did not prove that the product supports OOB monitoring correctly
the next implementation step is a real server_oob_snmp monitoring suite, not target injection into the in-band suite
```

## 15. Server OOB SNMP Monitoring Suite

Implementation artifact:

```text
/OneOPS/OneOps/migrations/seed_server_oob_snmp_strategy_set.sql
```

New strategy:

```text
id = server_oob_snmp_strategy
name = 服务器带外SNMP监控策略
template = snmp-passthrough
catalog_id = CATL20231020003
scope = global
```

Collection scope:

```text
collect sysDescr
collect sysName as tag
collect sysUpTime
do not collect ENTITY-MIB entPhysicalTable in the first suite seed
do not collect ifTable
do not write OOB interfaces into server business interface facts
```

Reason:

```text
ENTITY-MIB table probing must be validated per OOB vendor/model before entering the default suite
an invalid table root can make the whole SNMP input fail at agent init time
the first OOB suite should prove target selection, credential binding, dispatch, and scalar reachability first
hardware inventory tables should be added as a separate OOB inventory strategy after OID validation
```

New strategy set:

```text
id = server_oob_snmp
name = 服务器带外SNMP监控套件
mode = strategy_selector
catalog = CATL20231020003
collection_mode = remote
function_area = DefaultArea
auto_apply_on_store = false by default
enabled = false by default
strategy_items = [server_oob_snmp_strategy]
attach_processor_strategy_id = 934f0d58-5caa-44ae-933a-ccac288b5f2c
output_ids = [8ec4cae8-0fb0-11f1-b426-0050569b3ce3]
```

Production default:

```text
server_oob_snmp exists
server_oob_snmp.enabled = false
server_oob_snmp.auto_apply_on_store = false
```

Pilot enablement:

```text
server_oob_snmp.enabled = true
server_oob_snmp.auto_apply_on_store = true
```

Gate rule:

```text
server_oob_snmp strategy set requires snmp_outband
ordinary snmp is not enough for this strategy set
devices with only in-band SNMP must not enter the OOB SNMP push path
```

Dispatch rule:

```text
服务器远程监控套件:
  owns in-band server monitoring
  must not append OOB targets

服务器带外SNMP监控套件:
  owns OOB SNMP monitoring
  target address = out_band_ip / OOB SNMP access point
  credential usage = snmp_outband / out_band:snmp
```

StrategyApplyV2 propagation rule:

```text
strategy_set_id=server_oob_snmp must be visible before agent selection
OOB target normalization happens before credential resolution and TOML rendering
task identity is endpoint-based when OOB target metadata marks explicit endpoint ownership
expected task address = udp://out_band_ip:161
expected credential resolver usage = snmp_outband
```

## 16. 2026-06-03 Longest-Chain Acceptance

Test target:

```text
device_v2_code = DVC94FA66E51531
device_v1_code = DEV20260603000001
in_band_ip = 172.21.144.1
out_band_ip = 172.21.160.1
agent = agent-001
controller = quickenv-demo-core-defaultarea-10-0-110-251
```

Accepted checkpoints:

```text
sync-to-v1 monitor_push_status = success
server_oob_snmp strategy set was applied independently
OOB task_id = collect_agent-001_snmp-passthrough_172_21_160_1_161
OOB config agent = udp://172.21.160.1:161
OOB credential usage = snmp_outband
OOB strategy_set_id = server_oob_snmp
OOB strategy_id = server_oob_snmp_strategy
agent accepted bundle status = applied
agent task file contains OOB task and enabled=true
agent metric debug dump contains sysDescr/sysUpTime from agent_host=172.21.160.1
```

Separation checkpoints:

```text
existing in-band SNMP task remains owned by the original server strategy set
in-band task_id = collect_agent-001_snmp-passthrough_172_21_144_1_161
in-band config agent = udp://172.21.144.1:161
OOB task does not contain the in-band address
in-band task does not contain the OOB address
OOB task does not contain ENTITY-MIB table
OOB task does not contain ifTable
```

Residual observation:

```text
the legacy in-band server SNMP task still times out against 172.21.144.1 in this environment
that is independent from OOB support
the accepted OOB path proves agent-side OOB SNMP task delivery and scalar collection
```

## 17. Current Phase Completion Audit

This section freezes the current phase.

Do not add new productization work until these items are reviewed.

Current phase scope:

```text
Excel import can carry in-band and OOB access material
Device V2 can persist OOB SNMP as an access plane
V1 bridge can preserve OOB SNMP credential binding
DC2/store can choose OOB SNMP for OOB-only server collection
monitor push can create an independent server_oob_snmp task
agent can receive and run the OOB SNMP scalar task
```

Completion status:

```text
Excel / import fields:
  status = implemented
  evidence = test_data2.xlsx transformed into credential_refs.out_band:snmp and access_points out_band/snmp
  remaining = broader regression on mixed in-band SNMP + OOB SNMP rows

Device V2 attribute model:
  status = implemented
  evidence = out_band_ip, access_points, credential_refs.out_band:snmp persisted
  remaining = ensure future out_band:redfish and out_band:ipmi are preserved without SNMP assumptions

V1 bridge / credential sync:
  status = implemented
  evidence = sync-to-v1 bound 带外 SNMP using ingest_snmp_975BF891C80C
  remaining = verify v2/v3 variants across more rows

DC2 ingress target selection:
  status = implemented with unit evidence
  evidence = server_oob_snmp target selection tests pass; OOB-only target uses out_band_ip and out_band:snmp
  remaining = longest-chain DC2 fact merge for a real OOB-only imported server still needs runtime validation

Monitoring strategy set:
  status = implemented with production-safe default
  evidence = server_oob_snmp strategy set exists and is separate from in-band server strategy set
  remaining = pilot environments must explicitly enable it when OOB monitoring validation is desired

Monitoring push:
  status = accepted for scalar OOB SNMP with final TOML tag evidence
  evidence = monitor_push_status=success and task collect_agent-001_snmp-passthrough_172_21_160_1_161
  remaining = agent-side downloaded task should be sampled again after enabling the tagged build

Agent-side task and data:
  status = accepted for scalar OOB SNMP
  evidence = agent tasks.json contains udp://172.21.160.1:161 and metric debug dump contains sysDescr/sysUpTime
  remaining = in-band task still times out in this environment, but that is separate from OOB
```

Current phase is not fully closed until:

```text
1. Run focused regression tests for Excel, Device V2, V1 bridge, DC2 target selection, and monitoring push.
   status = done for focused packages listed below
2. Record which tests are blocked by environment or pre-existing package failures.
   status = no focused package failures recorded in this audit
3. Confirm whether server_oob_snmp should stay enabled in this pilot DB or be reset to disabled after validation.
   status = decided; production seed defaults to disabled, pilot environments may explicitly enable it
4. Confirm whether OOB-only server creation is accepted as device_v2 creation without OS facts.
   status = accepted; OOB-only server can create device_v2 without OS facts
5. Confirm no OOB SNMP interface/table data is written into server OS interface facts.
   status = unit evidence added for hardware facts; runtime OOB-only merge still needs validation
```

2026-06-03 focused regression audit:

```text
Excel transform OOB tests:
  command = go test -run 'OutBand|OOB|SNMP' ./device_v2_ingest_prepare_from_excel.go ./device_v2_ingest_prepare_from_excel_test.go
  result = PASS

Device V2 service OOB tests:
  command = go test ./app/device/v2/service/impl -run 'OutBand|OOB|SNMP' -count=1
  result = PASS

Device V2 API / V1 bridge credential tests:
  command = go test ./app/device/v2/api -run 'OutBand|OOB|SNMP|CredentialRefs|SyncToV1' -count=1
  result = PASS

Device V2 ingest service OOB tests:
  command = go test ./app/device/v2/ingest/service/impl -run 'OutBand|OOB|SNMP' -count=1
  result = PASS

Device V2 ingest API OOB tests:
  command = go test ./app/device/v2/ingest/api -run 'OutBand|OOB|SNMP' -count=1
  result = PASS

DC2 target selection tests:
  command = go test ./app/entity/v2/service/impl -run 'TestDeviceV2DC2TargetPrefersOutBandSNMPForServer|TestDeviceV2DC2StoreSidecarReportsOutBandSNMPSelection|TestDeviceV2DC2StoreSidecarReportsMissingOutBandSNMPCredential' -count=1
  result = PASS

OOB-only collectable projection test:
  command = go test ./app/device/v2/service/impl -run 'TestEntityToDeviceV2ProjectionTreatsOutBandSNMPAsCollectable|OutBandSNMP' -count=1
  result = PASS

Excel ingest OOB manageability test:
  command = go test ./app/device/v2/ingest/api -run 'TestDeviceV2IngestAPI_UploadExcelTaskTreatsOutBandSNMPAccessModelAsManageable' -count=1
  result = PASS

DC2 OOB selection and sidecar tests:
  command = go test ./app/entity/v2/service/impl -run 'TestDeviceV2DC2StoreSidecarReportsOutBandSNMPSelection|TestDeviceV2DC2TargetTreatsOOBOnlyLegacySNMPRefAsOutBand|TestDeviceV2DC2TargetPrefersOutBandSNMPForServer' -count=1
  result = PASS

Server OOB SNMP contract and fact isolation tests:
  command = go test ./app/device_collection2/service/impl -run 'TestBuiltinServerOOBSNMPContract|TestProcessFactsNormalizesCommonMIBEntPhysicalRows|TestProcessFactsNormalizesCommonMIBInterfaceRows|TestProcessFactsNormalizesInterfaceRows' -count=1
  result = PASS

OOB hardware facts do not build interface resources:
  command = go test ./app/entity/v2/service/impl -run 'TestDeviceV2DC2OOBSNMPHardwareFactsDoNotBuildInterfaceResources|TestDeviceV2DC2FactsBuildInterfaceMirrorResources|TestDeviceV2DC2StoreSidecarReportsOutBandSNMPSelection' -count=1
  result = PASS

Device service monitoring OOB gate tests:
  command = go test ./app/device/service/impl -run 'OutBand|OOB|SNMP|StrategySetClaim|CredentialBindingRequirements' -count=1
  result = PASS

Platform StrategyApply OOB tests:
  command = go test ./app/platform/service/impl -run 'OutBand|OOB|SNMPOutband|server_oob_snmp|ServerOOB' -count=1
  result = PASS

Server OOB SNMP seed default guard:
  command = go test ./app/platform/service/impl -run 'TestServerOOBSNMPSeedDefaultsToPresentDisabled' -count=1
  result = PASS

OOB render target label contract:
  command = go test ./app/platform/service/impl -run 'TestStrategyApplyV2Srv_ApplyStrategyAndPush_ServerOOBStrategySetUsesOutBandTargetAndCredential|TestMonitoringTaskV3NormalizeAndLogRenderTargets_ServerOOBSNMPStrategyUsesOutBandAddress' -count=1
  result = PASS

OOB final TOML metric tag contract:
  command = go test ./app/platform/service/impl -run 'TestGenerateFromStrategy_ServerOOBSNMPRendersPlaneTagsInFinalTOML' -count=1
  result = PASS
  evidence = final [inputs.snmp.tags] contains access_plane=out_band, protocol=snmp, monitoring_profile=server_oob_snmp, credential_binding=snmp_outband, source_address=<out_band_ip>

OOB strategy-set final TOML metric tag contract:
  command = go test ./app/platform/service/impl -run 'TestGenerateFromStrategySet/server_oob_snmp_策略集最终TOML包含OOB标签' -count=1
  result = PASS
  evidence = server_oob_snmp strategy set renders final [inputs.snmp.tags] with access_plane/protocol/monitoring_profile/credential_binding/source_address
```

2026-06-03 runtime revalidation:

```text
agent-001 status = online
agent function_area = DefaultArea
agent controller = quickenv-demo-core-defaultarea-10-0-110-251
monitor_push_status = success
device_v2_code = DVC94FA66E51531
device_v1_code = DEV20260603000001
```

Runtime task evidence:

```text
OOB task:
  strategy_set_id = server_oob_snmp
  strategy_id = server_oob_snmp_strategy
  task_id = collect_agent-001_snmp-passthrough_172_21_160_1_161
  target_part = 172_21_160_1_161
  config contains udp://172.21.160.1:161
  agent task enabled = true
  config contains sysDescr/sysName/sysUpTime
  config does not contain in-band address 172.21.144.1
  config does not contain ENTITY-MIB table
  config does not contain ifTable

In-band task:
  strategy_set_id = 43e00e73-8cb5-4636-b6a2-216a67a32084
  task_id = collect_agent-001_snmp-passthrough_172_21_144_1_161
  target_part = 172_21_144_1_161
  config contains udp://172.21.144.1:161
  config does not contain OOB address 172.21.160.1
```

Still not closed:

```text
OOB DC2 fact merge for a real OOB-only server still needs longest-chain runtime validation.
OOB ifTable isolation now has unit evidence:
  server_oob_snmp contract excludes snmp_if_table.
  OOB hardware facts from snmp_sys_descr and snmp_entPhysicalEntry do not build interface/ip/mac/neighbor/arp resources.
  Runtime monitoring task also excludes ifTable.
server_oob_snmp production seed now defaults to enabled=0 and auto_apply_on_store=0.
Pilot DBs may keep enabled=1 and auto_apply_on_store=1 when OOB monitoring validation is desired.
OOB render targets now carry access_plane, protocol, monitoring_profile, credential_binding, and source_address.
Final generated TOML now carries the same OOB tags under [inputs.snmp.tags].
Agent-side downloaded task still needs runtime sampling after the tagged build is deployed.
```

Current phase should not include:

```text
UI display implementation
alarm policy implementation
Redfish/IPMI implementation
ENTITY-MIB inventory rollout
additional production rollout workflow changes
```

Those belong to deferred backlog.

## 18. Deferred Productization Follow-Up

The accepted chain proves the platform can deliver OOB SNMP monitoring.

It does not mean OOB support is fully productized.

Productization still needs these boundaries:

```text
strategy-set enablement
environment-specific defaults
metric display grouping
alarm ownership
inventory dataset maturity
Redfish/IPMI extensibility
regression tests for in-band + OOB coexistence
```

Do not treat `server_oob_snmp` as a hidden extension of the existing server SNMP suite.

Treat it as an independently managed monitoring capability.

The default rollout posture should be:

```text
lab / pilot environment:
  server_oob_snmp enabled

production environment without OOB monitoring readiness:
  server_oob_snmp present but disabled

production environment with OOB monitoring readiness:
  server_oob_snmp enabled by explicit configuration
```

The reason is simple:

```text
OOB SNMP reachability and credential conventions differ by environment
some environments use SNMP v2
some environments use SNMP v3
some future environments will use Redfish or IPMI
```

## 19. Strategy Set Enablement Model

`server_oob_snmp` should support three states:

```text
absent:
  platform version does not provide OOB monitoring

present_disabled:
  strategy set exists but auto_apply_on_store=false or enabled=false

present_enabled:
  strategy set exists and can auto-apply to eligible servers
```

Recommended control fields:

```text
enabled
auto_apply_on_store
function_area
catalog
strategy_items
output_ids
attach_processor_strategy_id
```

Optional future environment flag:

```text
ONEOPS_MONITORING_SERVER_OOB_SNMP_ENABLED
```

Optional future behavior:

```text
if ONEOPS_MONITORING_SERVER_OOB_SNMP_ENABLED=true:
    seed server_oob_snmp as enabled=true, auto_apply_on_store=true
else:
    seed server_oob_snmp as enabled=false, auto_apply_on_store=false
```

The current seed is production-safe by default.

Pilot environments can explicitly enable the strategy set after applying the seed.

## 20. Monitoring Matching Rule

The OOB strategy set should only match a server when all required OOB material exists.

Required target material:

```text
catalog = SERVER
out_band_ip is non-empty
access_points contains plane=out_band and protocol=snmp
credential_refs.out_band:snmp is non-empty
```

Acceptable credential aliases:

```text
credential_refs.out_band:snmp
credential_refs.snmp_outband
```

Do not accept these as OOB SNMP when both in-band and OOB are present:

```text
snmp_credential_ref
credential_refs.snmp
credential_refs.in_band:snmp
credential_ref_out_band
```

Reason:

```text
snmp_credential_ref may be legacy in-band SNMP
credential_ref_out_band may be CLI or generic BMC credential
OOB SNMP must be explicit to avoid credential leakage across planes
```

The in-band strategy set and OOB strategy set may both match the same server.

That is valid only when the claim key is plane-aware.

Correct claim examples:

```text
DEV20260603000001|in_band|snmp
DEV20260603000001|out_band|snmp
```

Incorrect claim example:

```text
DEV20260603000001
```

The incorrect claim blocks coexistence.

## 21. Metric Label Contract

OOB metrics must be identifiable after they reach storage.

Minimum labels:

```text
device_id
device_name
plane = out_band
protocol = snmp
strategy_set_id = server_oob_snmp
source_address = out_band_ip
```

Recommended labels:

```text
access_plane = out_band
monitoring_profile = server_oob_snmp
credential_binding = snmp_outband
oob_protocol = snmp
```

Current scalar OOB task already proves target address and collection.

The next improvement is to add stable plane labels into emitted metrics.

Without plane labels, UI and alert rules cannot reliably distinguish:

```text
server OS SNMP from in-band
server BMC SNMP from OOB
network device SNMP
```

Plane labels should be added at render time, not inferred later from IP ranges.

## 22. Display Model

Device identity remains one server.

Monitoring views should separate planes.

Recommended UI grouping:

```text
Server
  Overview
  In-band
    reachability
    OS metrics
    OS SNMP metrics
  Out-of-band
    OOB reachability
    BMC identity
    BMC uptime
    hardware health
    firmware
    power / fan / temperature
```

OOB scalar metrics should initially display as:

```text
OOB SNMP reachable
BMC sysName
BMC sysDescr
BMC uptime
last successful OOB SNMP collection time
```

Do not show OOB SNMP scalar metrics as OS CPU, OS memory, or OS disk metrics.

Do not merge BMC `sysName` into server hostname automatically.

Do not merge OOB address into business IP.

## 23. Alarm Ownership

OOB alarms should have separate ownership from in-band alarms.

Recommended alarm categories:

```text
server_oob_unreachable
server_oob_snmp_auth_failed
server_oob_snmp_timeout
server_oob_bmc_uptime_reset
server_oob_hardware_health_warning
server_oob_hardware_health_critical
```

Do not reuse generic server OS alarms for OOB faults.

Example:

```text
in-band SNMP timeout:
  category = server_inband_snmp_timeout
  target = in_band_ip

OOB SNMP timeout:
  category = server_oob_snmp_timeout
  target = out_band_ip
```

This separation matters because the response teams can differ.

OS unreachable and BMC unreachable are different incidents.

## 24. OOB Inventory Strategy Roadmap

The first accepted OOB suite collects scalar identity only.

That is intentional.

The next inventory strategy should be separate:

```text
strategy_id = server_oob_snmp_inventory_strategy
strategy_set_id = server_oob_snmp_inventory
template = snmp-passthrough
purpose = OOB hardware and firmware inventory
```

Candidate datasets:

```text
ENTITY-MIB entPhysicalTable
vendor-specific sensor table
vendor-specific power table
vendor-specific fan table
vendor-specific temperature table
```

Before enabling by default, validate:

```text
OID table root is accepted by Telegraf
table has bounded cardinality
table fields have stable names
metrics carry plane=out_band
parser does not write OOB rows into OS interface baseline
parser handles missing table without failing the whole task
```

ENTITY-MIB validation should start with:

```text
.1.3.6.1.2.1.47.1.1.1.1
```

Do not use a table root that makes Telegraf fail input initialization.

An invalid table root is worse than a missing metric.

It stops the whole SNMP task.

## 25. Redfish And IPMI Extension

SNMP is one OOB protocol.

The model should not become SNMP-only.

Future OOB protocols should use the same access-plane shape:

```json
{
  "access_points": [
    {
      "plane": "out_band",
      "protocol": "redfish",
      "ip": "10.1.1.5",
      "port": 443,
      "credential_ref": "cred-oob-redfish"
    },
    {
      "plane": "out_band",
      "protocol": "ipmi",
      "ip": "10.1.1.5",
      "port": 623,
      "credential_ref": "cred-oob-ipmi"
    }
  ],
  "credential_refs": {
    "out_band:redfish": "cred-oob-redfish",
    "out_band:ipmi": "cred-oob-ipmi"
  }
}
```

Strategy set examples:

```text
server_oob_redfish
server_oob_ipmi
server_oob_snmp
```

Agent selection should depend on:

```text
protocol
required capability
function_area
target reachability
```

Examples:

```text
out_band:snmp    -> requires teleabs_template:snmp
out_band:redfish -> requires redfish/http capability
out_band:ipmi    -> requires ipmi capability
```

Credential selection should depend on:

```text
out_band:<protocol>
```

Never resolve Redfish or IPMI credentials through `snmp_outband`.

## 26. Regression Matrix

Required regression cases:

```text
1. server with only in-band SSH
   expected: device can import; no OOB SNMP task

2. server with in-band SSH + OOB SNMP
   expected: in-band task and OOB SNMP task both exist

3. server with only OOB SNMP
   expected: device v2 can exist; server_oob_snmp can monitor; Linux/Windows in-band gate remains unsatisfied

4. server with out_band_ip but no out_band:snmp
   expected: no OOB SNMP task; precise gate reason

5. server with in-band SNMP only
   expected: in-band SNMP task only; no OOB SNMP task

6. server with in-band SNMP + OOB SNMP
   expected: two SNMP tasks with different addresses and different credential usages

7. server with OOB Redfish only
   expected: no OOB SNMP task; future Redfish strategy set may match

8. network device with SNMP
   expected: no server_oob_snmp match
```

Minimum verification commands:

```text
go test ./app/platform/service/impl
go test ./app/device/service/impl
go test ./app/entity/v2/service/impl -run 'OutBand|OOB|SNMP'
go test -run 'OutBand|OOB|SNMP' ./scripts/device_v2_ingest_prepare_from_excel.go ./scripts/device_v2_ingest_prepare_from_excel_test.go
```

Longest-chain verification should include:

```text
database strategy_apply_record
agent tasks.json
agent apply logs
agent metric debug dump
```

Do not accept API success alone.

## 27. Remaining Decisions

Open decisions:

```text
Should OOB scalar metrics share the existing SNMP measurement name or use a separate measurement?
Which labels are mandatory for OOB metric display?
Should OOB alarms be enabled with the first scalar suite?
Which vendor-specific OOB SNMP tables should be supported first?
Should Redfish be prioritized before deeper SNMP inventory?
```

Recommended near-term decisions:

```text
keep server_oob_snmp disabled by default in production
enable server_oob_snmp only in pilot or explicitly prepared environments
add plane labels before building UI display rules
keep scalar OOB SNMP and inventory OOB SNMP as separate strategies
define alarm ownership after metric labels are stable
prototype Redfish as a parallel OOB protocol, not as a replacement for SNMP
```

## 28. Deferred Productization Backlog

This is a deferred backlog.

It is not the active current-phase task list.

When the current phase is closed, the next phase should focus on product hardening, not adding more MIBs first.

Recommended tasks:

```text
1. Add explicit plane labels to OOB SNMP rendered metrics
2. Add matcher tests for in-band + OOB coexistence
3. Add API/DB visibility for strategy_set_id and access_plane on monitoring tasks
4. Add UI grouping contract for OOB monitoring
5. Add separate server_oob_snmp_inventory strategy after ENTITY-MIB validation
6. Add Redfish/IPMI access-point parser compatibility tests
7. Optionally add environment-flag based seed enablement for pilot automation
```

Do not proceed to hardware inventory until:

```text
the OOB scalar suite remains stable across at least one full monitor push cycle
agent-side task config is stable after repeated sync-to-v1 monitor_push
metric labels are plane-aware
display does not confuse OOB SNMP with OS SNMP
```

## 29. Deferred Productization Plan File

The deferred implementation plan is:

```text
/OneOPS/docs/superpowers/plans/2026-06-03-server-oob-productization-plan.md
```

This file is not active until the current phase completion audit is resolved.

The plan focuses on:

```text
rollout-safe OOB SNMP seed
explicit OOB metric labels
in-band and OOB coexistence regression tests
monitoring task visibility for access plane
disabled OOB inventory strategy seed
Redfish/IPMI parser compatibility tests
longest-chain revalidation
```

The plan should be executed after reviewing whether `server_oob_snmp` should remain enabled in the current pilot environment or become disabled by default for production rollout.
