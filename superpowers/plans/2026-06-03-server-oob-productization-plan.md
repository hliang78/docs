# Server OOB Productization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden server OOB monitoring so the accepted scalar OOB SNMP path becomes configurable, plane-labeled, visible, and regression-tested without mixing with in-band server monitoring.

**Architecture:** Keep OOB as an access plane, not a device type. The same `access_points + credential_refs` model feeds strategy matching, target normalization, credential resolution, task rendering, and display grouping. OOB SNMP remains a separate strategy set from in-band SNMP.

**Tech Stack:** Go, GORM/MySQL seed SQL, Teleabs strategy rendering, Device V2 ingest, Monitoring V2 StrategyApply, controller/agent Telegraf task delivery, jq/curl/mysql for longest-chain validation.

**Status:** Deferred backlog. Do not execute this plan until `/OneOPS/docs/superpowers/specs/2026-06-02-server-oob-plane-support.md` section `17. Current Phase Completion Audit` is closed.

---

## File Map

- Modify: `/OneOPS/OneOps/migrations/seed_server_oob_snmp_strategy_set.sql`
  - Make the seed safe for production rollout by allowing disabled-by-default behavior.

- Modify: `/OneOPS/OneOps/app/platform/service/impl/strategy_apply_rendering_v2.go`
  - Ensure OOB SNMP target metadata carries stable metric tags before rendering.

- Modify: `/OneOPS/OneOps/app/platform/service/impl/monitoring_task_v3_target_resolver_registry.go`
  - Keep OOB target metadata canonical in one place.

- Modify: `/OneOPS/OneOps/app/platform/service/impl/monitoring_task_v3_target_metadata.go`
  - Keep address resolution plane-aware and avoid in-band fallback for OOB requests.

- Modify: `/OneOPS/OneOps/app/platform/service/impl/strategy_apply_v2_test.go`
  - Add regression tests for plane labels and endpoint identity.

- Modify: `/OneOPS/OneOps/app/device/service/impl/device_store_controller_test.go`
  - Add regression tests for strategy set claim coexistence.

- Modify: `/OneOPS/OneOps/app/device/service/impl/device_store_controller.go`
  - Keep strategy-set credential requirements plane-aware.

- Modify: `/OneOPS/OneOps/app/platform/service/impl/monitoring_task_v3_services_test.go`
  - Add target resolver and metadata tests for explicit OOB SNMP selection.

- Create: `/OneOPS/OneOps/migrations/seed_server_oob_snmp_inventory_strategy_set.sql`
  - Add a disabled inventory suite for validated ENTITY-MIB or vendor-specific hardware metrics.

- Modify: `/OneOPS/docs/superpowers/specs/2026-06-02-server-oob-plane-support.md`
  - Record implementation status and acceptance results for each productization task.

---

## Task 1: Make OOB SNMP Seed Rollout-Safe

**Files:**
- Modify: `/OneOPS/OneOps/migrations/seed_server_oob_snmp_strategy_set.sql`

- [ ] **Step 1: Change the seed to default disabled**

Replace the strategy set `VALUES` section fields:

```sql
  'DefaultArea',
  0,
  0,
```

This means:

```text
function_area = DefaultArea
auto_apply_on_store = false
enabled = false
```

- [ ] **Step 2: Add a pilot enable block at the bottom**

Append this optional block:

```sql
-- Pilot enablement command:
-- UPDATE `platform_teleabs_strategy_set`
-- SET `enabled` = 1,
--     `auto_apply_on_store` = 1,
--     `updated_at` = NOW(3)
-- WHERE `id` = 'server_oob_snmp';
```

- [ ] **Step 3: Verify seed syntax**

Run:

```bash
docker exec -i demo-core-mysql sh -lc 'MYSQL_PWD="UniOPS@Passw0rd" mysql -uUniOPS UniOPS' < /OneOPS/OneOps/migrations/seed_server_oob_snmp_strategy_set.sql
```

Expected:

```text
command exits 0
server_oob_snmp exists
server_oob_snmp enabled=0
server_oob_snmp auto_apply_on_store=0
```

- [ ] **Step 4: Verify DB state**

Run:

```bash
docker exec demo-core-mysql sh -lc "MYSQL_PWD='UniOPS@Passw0rd' mysql -uUniOPS UniOPS -e \"select id, enabled, auto_apply_on_store from platform_teleabs_strategy_set where id='server_oob_snmp'\""
```

Expected row:

```text
server_oob_snmp  0  0
```

## Task 2: Add Explicit OOB Metric Labels

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/monitoring_task_v3_target_resolver_registry.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/strategy_apply_rendering_v2.go`
- Test: `/OneOPS/OneOps/app/platform/service/impl/strategy_apply_v2_test.go`

- [ ] **Step 1: Write failing test**

Add this test to `strategy_apply_v2_test.go`:

```go
func TestStrategyApplyV2Srv_ApplyStrategyAndPush_ServerOOBStrategySetRendersPlaneTags(t *testing.T) {
	tplProvider := &fakeTemplateProvider{
		templates: map[string]*dto.TeleabsTemplateDetail{
			"snmp-passthrough": {
				ID:              "snmp-passthrough",
				PluginType:      "snmp",
				CollectionScope: "remote",
				TargetKind:      "device",
			},
		},
	}
	generator := NewTelegrafConfigGeneratorWithDepsImpl(TelegrafConfigGeneratorDeps{
		Logger:      zap.NewNop(),
		TplProvider: tplProvider,
	})
	resolver := &fakeCredentialResolverForMonitoringV2{
		refResp: &credentialDTO.ResolveResponse{
			CredentialCode: "cred-oob-snmp",
			Credentials:    map[string]interface{}{"community": "oob-public"},
		},
	}
	transfer := &fakeStrategyInheritanceTransferCaller{}
	device := service.TelegrafDeviceSpec{
		ID:      "DVC-OOB-LABEL-1",
		Name:    "server-oob-label-1",
		Address: "192.168.10.11",
		Port:    161,
		Metadata: map[string]interface{}{
			"in_band_ip":  "192.168.10.11",
			"out_band_ip": "10.10.10.11",
			"credential_refs": map[string]interface{}{
				"out_band:snmp": "cred-oob-snmp",
			},
			"access_points": []map[string]interface{}{
				{
					"plane":          "out_band",
					"protocol":       "snmp",
					"ip":             "10.10.10.11",
					"port":           161,
					"credential_ref": "cred-oob-snmp",
				},
			},
		},
	}
	s := &StrategyApplyV2Srv{
		Logger:                     zap.NewNop(),
		CollectionTaskDistribution: &fakeCollectionTaskDistribution{echoDevices: true},
		TelegrafConfigGenerator:    generator,
		TeleabsTemplateProvider:    tplProvider,
		TeleabsStrategySetSrv: &fakeMetricStrategyApplySetSrv{set: &dto.TeleabsStrategySetDto{
			ID:             "server_oob_snmp",
			Mode:           dto.StrategySetModeStrategySelector,
			CollectionMode: dto.StrategySetCollectionModeRemote,
			Enabled:        true,
			Items: []dto.TeleabsStrategySetItemDto{
				{
					ID:                "server_oob_snmp_item",
					StrategyID:        "server_oob_snmp_strategy",
					TeleabsTemplateID: "snmp-passthrough",
					Enabled:           true,
				},
			},
		}},
		StrategyApplyV2RecordStore:  newFakeStrategyApplyRecordStoreV2(),
		CredentialResolver:          resolver,
		TransferConfigToAgentCaller: transfer,
		TaskGenerator:               &fakeRuntimeRemoveTaskGenerator{controllerID: "controller-a"},
		AgentTopologySrv:            NewInMemoryAgentTopologyService(),
	}

	resp, err := s.ApplyStrategyAndPush(context.Background(), &service.ApplyStrategyAndPushInput{
		StrategySetID: "server_oob_snmp",
		Devices:       []service.TelegrafDeviceSpec{device},
		OutputPolicy:  constants.OutputPolicyInheritExisting,
	})

	require.NoError(t, err)
	require.Equal(t, 1, resp.SuccessCount)
	require.Len(t, transfer.bundles, 1)
	config := applyConfigFromBundle(t, transfer.bundles[0])
	require.Contains(t, config, `agents = ["udp://10.10.10.11:161"]`)
	require.Contains(t, config, `access_plane = "out_band"`)
	require.Contains(t, config, `plane = "out_band"`)
	require.Contains(t, config, `protocol = "snmp"`)
	require.Contains(t, config, `monitoring_profile = "server_oob_snmp"`)
	require.Contains(t, config, `strategy_set_id = "server_oob_snmp"`)
}
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestStrategyApplyV2Srv_ApplyStrategyAndPush_ServerOOBStrategySetRendersPlaneTags -count=1
```

Expected:

```text
FAIL because the rendered config does not contain one or more OOB labels
```

- [ ] **Step 3: Add canonical OOB label metadata**

Update `monitoringV2ApplyOutBandSNMPTargetMetadata` in `monitoring_task_v3_target_resolver_registry.go` so it sets:

```go
metadata["access_plane"] = "out_band"
metadata["plane"] = "out_band"
metadata["selected_access_plane"] = "out_band"
metadata["protocol"] = "snmp"
metadata["selected_protocol"] = "snmp"
metadata["selected_credential_key"] = "out_band:snmp"
metadata["credential_binding"] = "snmp_outband"
metadata["monitoring_profile"] = "server_oob_snmp"
metadata["strategy_set_id"] = "server_oob_snmp"
metadata["oob_protocol"] = "snmp"
```

- [ ] **Step 4: Ensure rendered tags include labels**

If the generator only copies selected metadata keys, add the OOB label keys to the allowed metadata-to-tag path used by SNMP rendering.

The rendered TOML must include:

```toml
[inputs.snmp.tags]
  access_plane = "out_band"
  plane = "out_band"
  protocol = "snmp"
  monitoring_profile = "server_oob_snmp"
  strategy_set_id = "server_oob_snmp"
```

- [ ] **Step 5: Run test and verify pass**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestStrategyApplyV2Srv_ApplyStrategyAndPush_ServerOOBStrategySetRendersPlaneTags -count=1
```

Expected:

```text
PASS
```

## Task 3: Lock In In-Band + OOB Coexistence

**Files:**
- Modify: `/OneOPS/OneOps/app/device/service/impl/device_store_controller_test.go`
- Modify: `/OneOPS/OneOps/app/device/service/impl/device_store_controller.go`

- [ ] **Step 1: Add claim-key regression test**

Add a test that proves the same device can be claimed twice when the strategy sets represent different planes:

```go
func TestMonitoringStrategySetClaimKeySeparatesInBandAndOutBandSNMP(t *testing.T) {
	inBand := &platformDTO.TeleabsStrategySetDto{ID: "server_snmp_inband", Name: "服务器带内SNMP监控套件"}
	outBand := &platformDTO.TeleabsStrategySetDto{ID: "server_oob_snmp", Name: "服务器带外SNMP监控套件"}

	inKey := monitoringStrategySetClaimKey("DEV-1", inBand)
	outKey := monitoringStrategySetClaimKey("DEV-1", outBand)

	if inKey == outKey {
		t.Fatalf("expected different claim keys for in-band and OOB SNMP, got %q", inKey)
	}
	if !strings.Contains(outKey, "out_band") || !strings.Contains(outKey, "snmp") {
		t.Fatalf("expected OOB claim key to include plane/protocol, got %q", outKey)
	}
}
```

- [ ] **Step 2: Run test and verify behavior**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/device/service/impl -run TestMonitoringStrategySetClaimKeySeparatesInBandAndOutBandSNMP -count=1
```

Expected:

```text
PASS if claim key is already plane-aware
FAIL if claim key only uses device code
```

- [ ] **Step 3: Fix claim key if needed**

Update `monitoringStrategySetClaimKey` so OOB SNMP appends:

```go
return strings.TrimSpace(deviceCode) + "|out_band|snmp"
```

For ordinary strategy sets, keep the existing behavior.

- [ ] **Step 4: Run package tests**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/device/service/impl
```

Expected:

```text
PASS
```

## Task 4: Add Monitoring Task Visibility For Access Plane

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/strategy_apply_record_store_v2.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/strategy_apply_task_model_v2.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/strategy_apply_v2_test.go`

- [ ] **Step 1: Add record test**

Add a test that applies `server_oob_snmp` and asserts the persisted record can be traced to the OOB plane.

Expected persisted fields:

```text
strategy_set_id = server_oob_snmp
strategy_id = server_oob_snmp_strategy
target_part = 10_10_10_11_161
template_id = snmp-passthrough
config_snapshot contains access_plane = "out_band"
```

- [ ] **Step 2: Run test**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run ServerOOBStrategySetUsesOutBandTargetAndCredential -count=1
```

Expected:

```text
PASS after Task 2 labels are rendered
```

- [ ] **Step 3: Expose plane in task list response**

If the task-list API currently only exposes raw `config_snapshot`, add derived fields:

```text
access_plane
protocol
strategy_set_id
target_address
```

Derive them from:

```text
strategy_set_id
target_part
config_snapshot tags
```

No secret fields should be returned.

## Task 5: Add Disabled OOB Inventory Strategy Seed

**Files:**
- Create: `/OneOPS/OneOps/migrations/seed_server_oob_snmp_inventory_strategy_set.sql`

- [ ] **Step 1: Create disabled inventory seed**

Create a seed with:

```sql
INSERT INTO `platform_teleabs_strategy` (
  `id`, `created_at`, `updated_at`, `deleted_at`,
  `name`, `description`, `scope_type`, `scope_id`,
  `teleabs_template_id`, `parameters_json`,
  `parent_id`, `manufacturer_id`, `device_model_id`,
  `catalog_id`, `platform_id`, `version_min`, `version_max`,
  `device_model_ids`, `tenant_code`
) VALUES (
  'server_oob_snmp_inventory_strategy',
  NOW(3), NOW(3), NULL,
  '服务器带外SNMP硬件库存策略',
  'Disabled-by-default OOB SNMP inventory strategy for validated ENTITY-MIB or vendor hardware tables.',
  'global',
  '',
  'snmp-passthrough',
  JSON_OBJECT(
    'version', 2,
    'community', 'public',
    'interval', '300s',
    'timeout', '5s',
    'retries', 3,
    'passthrough_config',
    '  [[inputs.snmp.field]]
    name = "sysDescr"
    oid = ".1.3.6.1.2.1.1.1.0"'
  ),
  '', '', '',
  'CATL20231020003',
  '', '', '',
  NULL,
  NULL
) ON DUPLICATE KEY UPDATE
  `updated_at` = VALUES(`updated_at`),
  `deleted_at` = NULL,
  `name` = VALUES(`name`),
  `description` = VALUES(`description`),
  `teleabs_template_id` = VALUES(`teleabs_template_id`),
  `parameters_json` = VALUES(`parameters_json`);
```

Add a disabled strategy set:

```sql
INSERT INTO `platform_teleabs_strategy_set` (
  `id`, `created_at`, `updated_at`, `deleted_at`,
  `name`, `description`, `mode`, `catalog`, `collection_mode`,
  `function_area`, `auto_apply_on_store`, `enabled`, `output_ids`,
  `attach_processor_strategy_id`, `strategy_items`, `catalogs`, `tenant_code`
) VALUES (
  'server_oob_snmp_inventory',
  NOW(3), NOW(3), NULL,
  '服务器带外SNMP硬件库存套件',
  'Disabled-by-default inventory suite for server OOB SNMP hardware and firmware facts.',
  'strategy_selector',
  'CATL20231020003',
  'remote',
  'DefaultArea',
  0,
  0,
  JSON_ARRAY('8ec4cae8-0fb0-11f1-b426-0050569b3ce3'),
  '934f0d58-5caa-44ae-933a-ccac288b5f2c',
  JSON_ARRAY(JSON_OBJECT(
    'id', 'server_oob_snmp_inventory_item',
    'strategy_id', 'server_oob_snmp_inventory_strategy',
    'sort_order', 1,
    'priority', 100,
    'enabled', TRUE,
    'is_fallback', FALSE
  )),
  JSON_ARRAY('CATL20231020003'),
  NULL
) ON DUPLICATE KEY UPDATE
  `updated_at` = VALUES(`updated_at`),
  `deleted_at` = NULL,
  `enabled` = VALUES(`enabled`),
  `auto_apply_on_store` = VALUES(`auto_apply_on_store`),
  `strategy_items` = VALUES(`strategy_items`);
```

- [ ] **Step 2: Verify seed**

Run:

```bash
docker exec -i demo-core-mysql sh -lc 'MYSQL_PWD="UniOPS@Passw0rd" mysql -uUniOPS UniOPS' < /OneOPS/OneOps/migrations/seed_server_oob_snmp_inventory_strategy_set.sql
```

Expected:

```text
command exits 0
server_oob_snmp_inventory exists
enabled = 0
auto_apply_on_store = 0
```

## Task 6: Redfish/IPMI Parser Compatibility Tests

**Files:**
- Modify: `/OneOPS/OneOps/scripts/device_v2_ingest_prepare_from_excel_test.go`
- Modify: `/OneOPS/OneOps/scripts/device_v2_ingest_prepare_from_excel.go`

- [ ] **Step 1: Add test for future OOB protocols**

Add a test that verifies non-SNMP OOB credential refs are preserved in `credential_refs` and do not create an SNMP access point:

```go
func TestTransformRowsPreservesFutureOutBandProtocolRefs(t *testing.T) {
	row := sourceRow{
		DeviceName: "server-redfish-1",
		Catalog:    "SERVER",
		InBandIP:   "192.168.10.20",
		OutBandIP:  "10.10.10.20",
		ExtraAttributes: map[string]string{
			"credential_refs": `{"out_band:redfish":"cred-redfish","out_band:ipmi":"cred-ipmi"}`,
		},
	}

	rows, _, err := transformRows([]sourceRow{row}, "kv/data/device-v2-ingest", "inband", "snmp_outband")
	if err != nil {
		t.Fatalf("transformRows failed: %v", err)
	}
	if len(rows) != 1 {
		t.Fatalf("expected one transformed row, got %d", len(rows))
	}
	refs := parseJSONMap(t, rows[0].Attributes["credential_refs"])
	if refs["out_band:redfish"] != "cred-redfish" || refs["out_band:ipmi"] != "cred-ipmi" {
		t.Fatalf("expected future OOB refs preserved, got %+v", refs)
	}
	points := parseJSONArray(t, rows[0].Attributes["access_points"])
	for _, point := range points {
		if point["protocol"] == "redfish" || point["protocol"] == "ipmi" {
			t.Fatalf("redfish/ipmi access point should wait for explicit protocol support, got %+v", point)
		}
	}
}
```

- [ ] **Step 2: Run test**

Run:

```bash
cd /OneOPS/OneOps/scripts
go test -run TestTransformRowsPreservesFutureOutBandProtocolRefs ./device_v2_ingest_prepare_from_excel.go ./device_v2_ingest_prepare_from_excel_test.go
```

Expected:

```text
PASS if refs are already preserved
FAIL if extra credential_refs are overwritten
```

- [ ] **Step 3: Preserve unknown credential_refs if needed**

If the test fails, change merge logic so unknown `credential_refs` keys are copied through unchanged unless a normalized explicit field overwrites the same key.

## Task 7: Longest-Chain Revalidation

**Files:**
- Modify: `/OneOPS/docs/superpowers/specs/2026-06-02-server-oob-plane-support.md`

- [ ] **Step 1: Enable pilot OOB suite**

Run:

```bash
docker exec demo-core-mysql sh -lc "MYSQL_PWD='UniOPS@Passw0rd' mysql -uUniOPS UniOPS -e \"update platform_teleabs_strategy_set set enabled=1, auto_apply_on_store=1, updated_at=now(3) where id='server_oob_snmp'\""
```

Expected:

```text
server_oob_snmp enabled for pilot validation
```

- [ ] **Step 2: Trigger sync-to-v1 with monitor push**

Run:

```bash
TOKEN=$(curl -sS -X POST http://127.0.0.1:8080/api/v1/access/login \
  -H 'Content-Type: application/json' \
  -d '{"login_type":0,"account":"admin","password":"admin@123"}' | jq -r '.data.token')

curl -sS -X POST 'http://127.0.0.1:8080/api/v1/device/v2/sync-to-v1?monitor_push=true' \
  -H "X-Auth-Token: $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"codes":["DVC94FA66E51531"],"monitor_push":true}' | jq '.data.monitor_push_status'
```

Expected:

```text
"success"
```

- [ ] **Step 3: Verify strategy apply record**

Run:

```bash
docker exec demo-core-mysql sh -lc "MYSQL_PWD='UniOPS@Passw0rd' mysql -uUniOPS UniOPS -e \"select strategy_set_id,strategy_id,task_id,target_part from platform_strategy_apply_record where task_id='collect_agent-001_snmp-passthrough_172_21_160_1_161'\""
```

Expected:

```text
strategy_set_id = server_oob_snmp
strategy_id = server_oob_snmp_strategy
target_part = 172_21_160_1_161
```

- [ ] **Step 4: Verify agent task file**

Run:

```bash
jq '.tasks[] | select(.task_id=="collect_agent-001_snmp-passthrough_172_21_160_1_161") | {task_id, enabled, has_oob_agent:(.config|contains("udp://172.21.160.1:161")), has_inband_agent:(.config|contains("udp://172.21.144.1:161"))}' /home/sy_cmsr/app/agent/data/telegraf_tasks/tasks.json
```

Expected:

```json
{
  "task_id": "collect_agent-001_snmp-passthrough_172_21_160_1_161",
  "enabled": true,
  "has_oob_agent": true,
  "has_inband_agent": false
}
```

- [ ] **Step 5: Update spec acceptance section**

Append a new dated acceptance note to `/OneOPS/docs/superpowers/specs/2026-06-02-server-oob-plane-support.md` with:

```text
date
device_v2_code
strategy_set_id
task_id
agent task enabled
metric labels present
remaining risks
```

---

## Completion Criteria

The next phase is complete when:

```text
server_oob_snmp seed is safe for non-pilot environments
OOB SNMP rendered metrics carry plane labels
in-band and OOB strategy sets can coexist for one server
OOB task visibility includes strategy_set_id and access plane
OOB inventory suite exists only as disabled-by-default seed
Redfish/IPMI refs are preserved without being misclassified as SNMP
longest-chain validation still passes for DVC94FA66E51531
```
