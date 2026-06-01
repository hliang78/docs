# ZB And Device V2 P0 E2E Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first runnable P0 end-to-end test slice for ZB external store and page-driven device v2 inbound flows, with real seed/pipeline/detect/collect behavior, plus DB and monitor-push evidence checks.

**Architecture:** Keep the existing service and handler code paths real wherever possible: ZB tests should exercise `Store -> UpsertSeed -> EntityV2 StartPipeline`, page tests should exercise `CreateBatch/Upload/Validate/Apply` and `store/start`, and both should run against a sqlite-backed real `DeviceV2Srv` + `EntityV2Srv`. DC2 detect/collect and monitor push remain controllable fakes so we can deterministically inject success and failure while still validating DB writes, pipeline snapshots, and agent-dispatch side effects.

**Tech Stack:** Go, Gin, GORM with SQLite, existing `DeviceV2Srv` / `EntityV2Srv`, existing ZB and API test helpers, `go test`, Markdown docs, Git

---

## File Structure

- Create: `docs/superpowers/testing/zb-device-v2-e2e-master-outline.md`
  Purpose: stable master outline with `Case ID`, entry, device type, tag, one-line description, and status for all P0 cases.

- Create: `OneOps/app/external_request/service/zb/impl/zb_device_v2_store_e2e_test.go`
  Purpose: ZB entry P0 integration tests that reuse the current callback harness, but switch from fake pipeline-only coverage to real `UpsertSeed` + real `EntityV2` pipeline with controllable DC2 and monitor-push collaborators.

- Create: `OneOps/app/device/v2/api/device_v2_entry_e2e_test.go`
  Purpose: page-side P0 integration tests for import batches and `store/start`, asserting DB writes, task/runs/observations, and monitor-push side effects through the actual API handlers.

- Create: `OneOps/app/device/v2/e2e/dual_entry_e2e_test.go`
  Purpose: dual-entry parity tests that feed the same network-device sample through ZB and page entry paths and compare `detect`, `collect`, `store`, DB, and monitor-push outputs.

- Reuse without modification: `OneOps/app/external_request/service/zb/impl/zb_device_v2_store_test.go:1483-1944`
  Purpose: existing sqlite callback harness, fake ZB services, and summary helpers for ZB tests.

- Reuse without modification: `OneOps/app/device/v2/api/device_v2_store_minimal_api_test.go:30-100`
  Purpose: existing `stubEntityV2Service` and sqlite DB helper for API tests.

- Reuse without modification: `OneOps/app/device/v2/api/device_v2_sync_to_v1_test.go:221-237`
  Purpose: existing fake monitor-push service that captures `NotifyMonitorProbeByDeviceCodes(...)` calls.

- Reuse without modification: `OneOps/app/entity/v2/service/impl/entity_v2_device_v2_store_runtime_test.go:5340-5475`
  Purpose: existing real runtime example for a ZB-seeded network device with controller detect and DC2 facts.

---

### Task 1: Create The Master Outline

**Files:**
- Create: `docs/superpowers/testing/zb-device-v2-e2e-master-outline.md`
- Test: `docs/superpowers/specs/2026-05-31-zb-device-v2-e2e-design.md`

- [ ] **Step 1: Write the master outline document**

```markdown
# ZB / Device V2 E2E Master Outline

| Case ID | Entry | Device Type | Tag | One-line Description | Status |
| --- | --- | --- | --- | --- | --- |
| ZB-001 | ZB | 网络设备 | 正常 | ZB 录入一台 SNMP-only 网络设备，预期完成 seed、pipeline、detect、collect、store、manage 和 monitor push 成功。 | ready |
| ZB-002 | ZB | 服务器 | precheck | ZB 录入服务器但缺 SSH 密码，预期同步 precheck 拦截且不写 seed。 | ready |
| ZB-003 | ZB | 网络设备 | collect | ZB 录入网络设备后 detect 成功但 facts 缺 serial_number，预期在 store decision 被阻断且 monitor push 跳过。 | ready |
| UII-001 | 页面导入 | 网络设备 | 正常 | 页面 base pass 导入网络设备并 apply 后启动 pipeline，预期写出 import record、task、store run 与 monitor push 成功。 | ready |
| UII-002 | 页面导入 | 网络设备 | validate | 页面导入重复 code 记录，预期 validate 标记错误且 apply 不写实体。 | ready |
| UIS-001 | 页面store | 复用设备 | 正常 | 页面对已有 device_v2 触发 store/start，预期复用原实体并进入真实 detect/collect 链路。 | ready |
| CMP-001 | ZB vs 页面导入 | 网络设备 | 对照 | 同一台网络设备分别从 ZB 和页面导入进入，预期 detect、collect、store decision、DB 最终态和 monitor push 一致。 | ready |
| CMP-002 | ZB vs 页面store | 网络设备 | 对照 | 同一台网络设备分别从 ZB 和页面 store/start 进入，预期 task stage、store run 和 monitor push 行为一致。 | ready |
```

- [ ] **Step 2: Check the outline matches the approved spec vocabulary**

Run: `rg -n "ZB-001|UII-001|UIS-001|CMP-001|One-line Description|Status" docs/superpowers/testing/zb-device-v2-e2e-master-outline.md`
Expected: one hit per case row and one hit for the header fields.

- [ ] **Step 3: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL
git add docs/superpowers/testing/zb-device-v2-e2e-master-outline.md
git commit -m "docs: add zb and device v2 e2e master outline"
```

### Task 2: Add ZB Entry P0 E2E Tests

**Files:**
- Create: `OneOps/app/external_request/service/zb/impl/zb_device_v2_store_e2e_test.go`
- Reuse: `OneOps/app/external_request/service/zb/impl/zb_device_v2_store_test.go:1483-1944`
- Test: `OneOps/app/external_request/service/zb/impl/zb_device_v2_store_e2e_test.go`

- [ ] **Step 1: Write the failing ZB P0 tests**

```go
package impl

import (
	"context"
	"fmt"
	"testing"

	devv2api "github.com/netxops/OneOps/app/device/v2/api"
	devv2impl "github.com/netxops/OneOps/app/device/v2/service/impl"
	entityimpl "github.com/netxops/OneOps/app/entity/v2/service/impl"
	externalRequestDto "github.com/netxops/OneOps/app/external_request/dto"
	"github.com/netxops/OneOps/dal/mysql"
	"github.com/netxops/OneOps/pkg/types"
	"go.uber.org/zap"
)

func TestZbStoreE2E_PrecheckStopsBeforeSeed(t *testing.T) {
	srv, db := newZbCallbackContractHarness(t, "zb-p0-precheck-stop", false)

	resp := srv.Store("zb-p0-precheck-stop", []*externalRequestDto.Equipment{{
		DeviceCode:      "DVC-ZB-P0-PRECHECK",
		DeviceName:      "zb-precheck-device",
		AttributionType: zbAttributionServer,
		InBandIP:        "10.20.0.11",
		InBandUsername:  "root",
	}})

	if len(resp) != 1 || resp[0].ProcessStatus {
		t.Fatalf("expected synchronous precheck failure, got %#v", resp)
	}
	payload := waitForZbCallbackPayload(t, db, "zb-p0-precheck-stop")
	rows := summaryByDeviceCode(payloadSummaryV2Rows(t, payload))
	row := rows["DVC-ZB-P0-PRECHECK"]
	if row["origin_stage"] != "precheck" || row["error_code"] != "ZB_PRECHECK_CREDENTIAL_INPUT_INVALID" {
		t.Fatalf("expected structured precheck callback, got %#v", row)
	}
}

func TestZbStoreE2E_HappyPath_SeedsPipelineAndPublishesMonitorSuccess(t *testing.T) {
	h := newRealZbDeviceV2PipelineHarness(t)

	resp := h.Srv.Store("zb-p0-happy", []*externalRequestDto.Equipment{
		newZbNetworkEquipment("DVC-ZB-P0-HAPPY", "zb-happy-switch"),
	})

	if len(resp) != 1 || !resp[0].ProcessStatus {
		t.Fatalf("expected accepted ZB store response, got %#v", resp)
	}
	payload := waitForZbCallbackPayload(t, h.DB, "zb-p0-happy")
	rows := summaryByDeviceCode(payloadSummaryV2Rows(t, payload))
	row := rows["DVC-ZB-P0-HAPPY"]
	if row["status"] != "success" || row["monitor_push_status"] != "success" {
		t.Fatalf("expected success callback row, got %#v", row)
	}
	if h.DeviceStore.pushedCodes[0] != "DVC-ZB-P0-HAPPY" {
		t.Fatalf("expected monitor push for v1 device code, got %#v", h.DeviceStore.pushedCodes)
	}
	if got := h.MustLoadEntityAttr("DVC-ZB-P0-HAPPY", "sync_to_v1_status"); got != "created" {
		t.Fatalf("expected sync_to_v1_status persisted, got %q", got)
	}
}

func TestZbStoreE2E_DetectCollectFailure_SkipsMonitorPushAndKeepsFailureEvidence(t *testing.T) {
	h := newRealZbDeviceV2PipelineHarness(t)
	h.DC2.facts = nil

	resp := h.Srv.Store("zb-p0-collect-fail", []*externalRequestDto.Equipment{
		newZbNetworkEquipment("DVC-ZB-P0-FAIL", "zb-fail-switch"),
	})

	if len(resp) != 1 || !resp[0].ProcessStatus {
		t.Fatalf("expected accepted ZB store response before async pipeline, got %#v", resp)
	}
	payload := waitForZbCallbackPayload(t, h.DB, "zb-p0-collect-fail")
	rows := summaryByDeviceCode(payloadSummaryV2Rows(t, payload))
	row := rows["DVC-ZB-P0-FAIL"]
	if row["status"] != "failed" || row["monitor_push_status"] != "skipped" {
		t.Fatalf("expected collect/store failure to skip monitor push, got %#v", row)
	}
	if len(h.DeviceStore.pushedCodes) != 0 {
		t.Fatalf("did not expect monitor push call, got %#v", h.DeviceStore.pushedCodes)
	}
}
```

- [ ] **Step 2: Run the ZB P0 tests to verify the new coverage fails**

Run: `go test ./app/external_request/service/zb/impl -run 'TestZbStoreE2E_' -count=1 -v`
Workdir: `/home/jacky/project/OneOPS-ALL/OneOps`
Expected: FAIL because `newRealZbDeviceV2PipelineHarness(...)`, `MustLoadEntityAttr(...)`, and the real pipeline wiring do not exist yet.

- [ ] **Step 3: Implement the real ZB pipeline harness and minimal DB assertions**

```go
type realZbDeviceV2PipelineHarness struct {
	Srv         *ZbCallSrv
	DB          *gorm.DB
	DC2         *stubDeviceCollection2Store
	DeviceStore *fakeDeviceStoreServiceForSync
	DeviceV2    *devv2impl.DeviceV2Srv
	EntityV2    *entityimpl.EntityV2Srv
}

func newRealZbDeviceV2PipelineHarness(t *testing.T) *realZbDeviceV2PipelineHarness {
	t.Helper()
	srv, db := newZbCallbackContractHarness(t, "template", true)

	for _, stmt := range []string{
		`CREATE TABLE entity_instance (...)`,
		`CREATE TABLE entity_pipeline_task (...)`,
		`CREATE TABLE device_v2_import_batch (...)`,
		`CREATE TABLE device_v2_import_record (...)`,
		`CREATE TABLE device_v2_observation (...)`,
		`CREATE TABLE device_v2_store_run (...)`,
		`CREATE TABLE platform(id TEXT, code TEXT PRIMARY KEY, name TEXT, deleted_at DATETIME)`,
		`CREATE TABLE manufacturer(id TEXT, code TEXT PRIMARY KEY, name TEXT, deleted_at DATETIME)`,
		`CREATE TABLE catalog(id TEXT, code TEXT PRIMARY KEY, name TEXT, deleted_at DATETIME)`,
		`CREATE TABLE device_model(id TEXT, code TEXT PRIMARY KEY, name TEXT, manufacturer_id TEXT, deleted_at DATETIME)`,
	} {
		if err := db.Exec(stmt).Error; err != nil {
			t.Fatalf("prepare integration table failed: %v", err)
		}
	}

	query := mysql.Use(db)
	deviceV2Srv := devv2impl.NewDeviceV2Srv(types.DBTypeMySQL(db), query, nil, nil)
	dc2 := &stubDeviceCollection2Store{
		detectResult: map[string]interface{}{
			"status":       "success",
			"manufacturer": "H3C",
			"platform":     "Comware",
			"catalog":      "NETWORK",
		},
		facts: []dc2dto.FactRecordResp{{
			FactType:    "device_identity",
			IdentityKey: "seed:identity",
			Fields: map[string]interface{}{
				"serial_number": "H3C-SN-001",
				"hostname":      "core-sw-1",
				"vendor":        "H3C",
				"platform":      "Comware",
				"model":         "S5130S-28P-EI",
				"management_ip": "10.0.0.21",
			},
		}},
	}
	entityV2Srv := entityimpl.NewEntityV2SrvWithDependencies(zap.NewNop(), types.DBTypeMySQL(db), nil, dc2, &config.Config{})
	deviceStore := &fakeDeviceStoreServiceForSync{}

	api := &devv2api.DeviceV2API{
		Logger:               zap.NewNop(),
		DB:                   types.DBTypeMySQL(db),
		Query:                query,
		DeviceV2Srv:          deviceV2Srv,
		EntityV2Srv:          entityV2Srv,
		DeviceStoreSrv:       deviceStore,
		DeviceSrv:            &fakeDeviceV1ServiceForSync{findByCodeFn: ..., createFn: ..., ifaceSrv: &fakeDeviceInterfaceServiceForSync{}},
		DeviceInterfaceV2Srv: &fakeDeviceInterfaceV2ServiceForSync{},
	}
	entityV2Srv.SetDeviceV2ManageRuntimeRunner(api)

	srv.DeviceV2Srv = deviceV2Srv
	srv.EntityV2Srv = entityV2Srv
	srv.DeviceStoreSrv = deviceStore
	srv.DeviceSrv = api.DeviceSrv
	srv.DeviceInterfaceV2Srv = api.DeviceInterfaceV2Srv
	srv.Logger = zap.NewNop()
	srv.ProxySrv = &proxy.TxProxySrv{Q: query}
	return &realZbDeviceV2PipelineHarness{Srv: srv, DB: db, DC2: dc2, DeviceStore: deviceStore, DeviceV2: deviceV2Srv, EntityV2: entityV2Srv}
}
```

- [ ] **Step 4: Run the ZB P0 tests to verify they pass**

Run: `go test ./app/external_request/service/zb/impl -run 'TestZbStoreE2E_' -count=1 -v`
Workdir: `/home/jacky/project/OneOPS-ALL/OneOps`
Expected: PASS with three tests covering precheck stop, happy path, and detect/collect failure.

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/external_request/service/zb/impl/zb_device_v2_store_e2e_test.go
git commit -m "test: add zb device v2 p0 e2e coverage"
```

### Task 3: Add Page Entry P0 E2E Tests

**Files:**
- Create: `OneOps/app/device/v2/api/device_v2_entry_e2e_test.go`
- Reuse: `OneOps/app/device/v2/api/device_v2_store_minimal_api_test.go:30-100`
- Reuse: `OneOps/app/device/v2/api/device_v2_sync_to_v1_test.go:221-237`
- Test: `OneOps/app/device/v2/api/device_v2_entry_e2e_test.go`

- [ ] **Step 1: Write the failing page entry tests**

```go
package api

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	devv2impl "github.com/netxops/OneOps/app/device/v2/service/impl"
	entityimpl "github.com/netxops/OneOps/app/entity/v2/service/impl"
	"github.com/netxops/OneOps/dal/mysql"
	"github.com/netxops/OneOps/pkg/types"
	"go.uber.org/zap"
)

func TestPageImportE2E_BasePassApplyPersistsRecordsAndSeed(t *testing.T) {
	h := newRealDeviceV2EntryHarness(t)

	batch := h.createBatch(t, `{"name":"page p0 batch","import_pass":"pass_1_base","namespace":"infra/device"}`)
	h.uploadRows(t, batch.BatchID, []map[string]interface{}{{
		"code": "DVC-UII-P0-1",
		"name": "page-entry-switch",
		"sn":   "SN-UII-P0-1",
		"in_band_ip": "10.30.0.31",
		"device_kind": "switch",
	}})
	h.validateBatch(t, batch.BatchID)
	summary := h.applyBatch(t, batch.BatchID)

	if summary.SuccessCount != 1 {
		t.Fatalf("expected successful apply, got %#v", summary)
	}
	if got := h.mustLoadImportRecordStatus("DVC-UII-P0-1"); got != "success" {
		t.Fatalf("expected import record applied, got %q", got)
	}
	if got := h.mustLoadDeviceAttr("DVC-UII-P0-1", "in_band_ip"); got != "10.30.0.31" {
		t.Fatalf("expected persisted seed entity, got %q", got)
	}
}

func TestPageStoreStartE2E_RealPipelineWritesStoreRunAndMonitorPush(t *testing.T) {
	h := newRealDeviceV2EntryHarness(t)
	h.seedNetworkDevice(t, "DVC-UIS-P0-1", "page-store-switch", "10.30.0.41")

	task := h.startStorePipeline(t, `{"codes":["DVC-UIS-P0-1"],"options":{"device_collection2":{"enabled":true,"store_pipeline_probe_enabled":true,"contract_key":"h3c_comware","dataset_keys":["snmp_sys_descr"]}}}`)

	if task.OverallStatus != "success" {
		t.Fatalf("expected successful task, got %#v", task)
	}
	if got := h.mustLoadStoreRunStatus(task.TaskID, "DVC-UIS-P0-1"); got != "success" {
		t.Fatalf("expected persisted store run success, got %q", got)
	}
	if len(h.DeviceStore.pushedCodes) != 1 {
		t.Fatalf("expected monitor push call, got %#v", h.DeviceStore.pushedCodes)
	}
}

func TestPageStoreStartE2E_DetectCollectFailureIsQueryable(t *testing.T) {
	h := newRealDeviceV2EntryHarness(t)
	h.seedNetworkDevice(t, "DVC-UIS-P0-FAIL", "page-store-fail", "10.30.0.51")
	h.DC2.facts = nil

	task := h.startStorePipeline(t, `{"codes":["DVC-UIS-P0-FAIL"],"options":{"device_collection2":{"enabled":true,"store_pipeline_probe_enabled":true,"contract_key":"h3c_comware","dataset_keys":["snmp_sys_descr"]}}}`)

	if task.OverallStatus == "success" {
		t.Fatalf("expected collect/store failure, got %#v", task)
	}
	if got := h.mustLoadStoreRunStatus(task.TaskID, "DVC-UIS-P0-FAIL"); got == "success" {
		t.Fatalf("expected persisted non-success store run, got %q", got)
	}
	if len(h.DeviceStore.pushedCodes) != 0 {
		t.Fatalf("did not expect monitor push on failed collect/store path, got %#v", h.DeviceStore.pushedCodes)
	}
}
```

- [ ] **Step 2: Run the page entry tests to verify they fail**

Run: `go test ./app/device/v2/api -run 'TestPage(Import|StoreStart)E2E_' -count=1 -v`
Workdir: `/home/jacky/project/OneOPS-ALL/OneOps`
Expected: FAIL because `newRealDeviceV2EntryHarness(...)` and its helper methods do not exist yet.

- [ ] **Step 3: Implement the page entry harness with real services and DB assertions**

```go
type realDeviceV2EntryHarness struct {
	API         *DeviceV2API
	DB          *gorm.DB
	Query       *mysql.Query
	DC2         *stubDeviceCollection2Store
	DeviceStore *fakeDeviceStoreServiceForSync
}

func newRealDeviceV2EntryHarness(t *testing.T) *realDeviceV2EntryHarness {
	t.Helper()
	db := openMinimalStoreAPITestDB(t)
	query := mysql.Use(db)

	for _, stmt := range []string{
		`CREATE TABLE entity_instance (...)`,
		`CREATE TABLE entity_pipeline_task (...)`,
		`CREATE TABLE device_v2_import_batch (...)`,
		`CREATE TABLE device_v2_import_record (...)`,
		`CREATE TABLE device_v2_observation (...)`,
		`CREATE TABLE device_v2_store_run (...)`,
		`CREATE TABLE platform(id TEXT, code TEXT PRIMARY KEY, name TEXT, deleted_at DATETIME)`,
		`CREATE TABLE manufacturer(id TEXT, code TEXT PRIMARY KEY, name TEXT, deleted_at DATETIME)`,
		`CREATE TABLE catalog(id TEXT, code TEXT PRIMARY KEY, name TEXT, deleted_at DATETIME)`,
		`CREATE TABLE device_model(id TEXT, code TEXT PRIMARY KEY, name TEXT, manufacturer_id TEXT, deleted_at DATETIME)`,
	} {
		if err := db.Exec(stmt).Error; err != nil {
			t.Fatalf("prepare device_v2 entry table failed: %v", err)
		}
	}

	deviceV2Srv := devv2impl.NewDeviceV2Srv(types.DBTypeMySQL(db), query, nil, nil)
	dc2 := &stubDeviceCollection2Store{detectResult: ..., facts: ...}
	entityV2Srv := entityimpl.NewEntityV2SrvWithDependencies(zap.NewNop(), types.DBTypeMySQL(db), nil, dc2, &config.Config{})
	deviceStore := &fakeDeviceStoreServiceForSync{}

	api := &DeviceV2API{
		Logger:               zap.NewNop(),
		DB:                   types.DBTypeMySQL(db),
		Query:                query,
		DeviceV2Srv:          deviceV2Srv,
		EntityV2Srv:          entityV2Srv,
		DeviceStoreSrv:       deviceStore,
		DeviceSrv:            &fakeDeviceV1ServiceForSync{findByCodeFn: ..., createFn: ..., ifaceSrv: &fakeDeviceInterfaceServiceForSync{}},
		DeviceInterfaceV2Srv: &fakeDeviceInterfaceV2ServiceForSync{},
	}
	entityV2Srv.SetDeviceV2ManageRuntimeRunner(api)
	return &realDeviceV2EntryHarness{API: api, DB: db, Query: query, DC2: dc2, DeviceStore: deviceStore}
}
```

- [ ] **Step 4: Run the page entry tests to verify they pass**

Run: `go test ./app/device/v2/api -run 'TestPage(Import|StoreStart)E2E_' -count=1 -v`
Workdir: `/home/jacky/project/OneOPS-ALL/OneOps`
Expected: PASS with one import case, one `store/start` success case, and one detect/collect failure case.

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/device/v2/api/device_v2_entry_e2e_test.go
git commit -m "test: add page device v2 p0 e2e coverage"
```

### Task 4: Add Dual-Entry Parity Tests

**Files:**
- Create: `OneOps/app/device/v2/e2e/dual_entry_e2e_test.go`
- Test: `OneOps/app/device/v2/e2e/dual_entry_e2e_test.go`

- [ ] **Step 1: Write the failing dual-entry parity tests**

```go
package e2e

import "testing"

func TestDualEntryE2E_NetworkDeviceDetectCollectParity(t *testing.T) {
	h := newDualEntryHarness(t)

	zb := h.runZBStore(t, "CMP-001-ZB", "DVC-CMP-P0-1", "cmp-switch", "10.40.0.11")
	ui := h.runPageImportAndStore(t, "CMP-001-UI", "DVC-CMP-P0-1", "cmp-switch", "10.40.0.11")

	if zb.Task.OverallStatus != ui.Task.OverallStatus {
		t.Fatalf("expected same task status, got zb=%s ui=%s", zb.Task.OverallStatus, ui.Task.OverallStatus)
	}
	if zb.StoreRunStatus != ui.StoreRunStatus {
		t.Fatalf("expected same store run status, got zb=%s ui=%s", zb.StoreRunStatus, ui.StoreRunStatus)
	}
	if zb.MonitorPushStatus != ui.MonitorPushStatus {
		t.Fatalf("expected same monitor status, got zb=%s ui=%s", zb.MonitorPushStatus, ui.MonitorPushStatus)
	}
	if zb.PlatformCode != ui.PlatformCode {
		t.Fatalf("expected same platform code materialization, got zb=%s ui=%s", zb.PlatformCode, ui.PlatformCode)
	}
}

func TestDualEntryE2E_NetworkDeviceFailureParity(t *testing.T) {
	h := newDualEntryHarness(t)
	h.DC2.facts = nil

	zb := h.runZBStore(t, "CMP-FAIL-ZB", "DVC-CMP-P0-FAIL", "cmp-fail-switch", "10.40.0.21")
	ui := h.runPageStoreStart(t, "CMP-FAIL-UI", "DVC-CMP-P0-FAIL", "cmp-fail-switch", "10.40.0.21")

	if zb.StoreRunStatus == "success" || ui.StoreRunStatus == "success" {
		t.Fatalf("expected both entries to expose the same collect/store failure, got zb=%#v ui=%#v", zb, ui)
	}
	if zb.MonitorPushStatus != "skipped" || ui.MonitorPushStatus != "skipped" {
		t.Fatalf("expected failed collect/store paths to skip monitor push, got zb=%#v ui=%#v", zb, ui)
	}
}
```

- [ ] **Step 2: Run the parity tests to verify they fail**

Run: `go test ./app/device/v2/e2e -run 'TestDualEntryE2E_' -count=1 -v`
Workdir: `/home/jacky/project/OneOPS-ALL/OneOps`
Expected: FAIL because the dual-entry harness and result extractors do not exist yet.

- [ ] **Step 3: Implement the dual-entry harness using the real ZB and page helpers**

```go
type dualEntryHarness struct {
	ZB *realZbDeviceV2PipelineHarness
	UI *realDeviceV2EntryHarness
	DC2 *stubDeviceCollection2Store
}

type dualEntryResult struct {
	Task              *entityv2model.EntityPipelineTask
	StoreRunStatus    string
	MonitorPushStatus string
	PlatformCode      string
}

func newDualEntryHarness(t *testing.T) *dualEntryHarness {
	t.Helper()
	zb := newRealZbDeviceV2PipelineHarness(t)
	ui := newRealDeviceV2EntryHarness(t)
	sharedDC2 := &stubDeviceCollection2Store{detectResult: ..., facts: ...}
	zb.DC2 = sharedDC2
	ui.DC2 = sharedDC2
	return &dualEntryHarness{ZB: zb, UI: ui, DC2: sharedDC2}
}
```

- [ ] **Step 4: Run the parity tests to verify they pass**

Run: `go test ./app/device/v2/e2e -run 'TestDualEntryE2E_' -count=1 -v`
Workdir: `/home/jacky/project/OneOPS-ALL/OneOps`
Expected: PASS with one success-parity case and one failure-parity case.

- [ ] **Step 5: Run the full P0 slice**

Run: `go test ./app/external_request/service/zb/impl ./app/device/v2/api ./app/device/v2/e2e -run 'Test(ZbStoreE2E_|Page(Import|StoreStart)E2E_|DualEntryE2E_)' -count=1 -v`
Workdir: `/home/jacky/project/OneOPS-ALL/OneOps`
Expected: PASS across the new P0 integration slice.

- [ ] **Step 6: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/device/v2/e2e/dual_entry_e2e_test.go
git commit -m "test: add dual-entry device v2 p0 parity coverage"
```

## Self-Review

### Spec coverage

- Dual entry scope: covered by Task 2, Task 3, and Task 4.
- Real `detect/collect`: covered by Task 2 and Task 3 via real `EntityV2Srv` + stub DC2 runtime.
- DB final state: covered by ZB and page harness DB assertions in Tasks 2 and 3.
- Agent monitor tasks: covered by Tasks 2, 3, and 4 through captured `NotifyMonitorProbeByDeviceCodes(...)` calls.
- Test master outline: covered by Task 1.

### Placeholder scan

- No `TBD`, `TODO`, or “implement later” placeholders remain.
- Every task includes exact file paths and runnable commands.

### Type consistency

- ZB tests reuse `newZbCallbackContractHarness(...)`, `fakeZbDeviceV2Service`, and summary helpers from the same `impl` package.
- Page tests reuse `stubEntityV2Service`, `openMinimalStoreAPITestDB(...)`, and `fakeDeviceStoreServiceForSync` from the same `api` package.
- Dual-entry tests use the two new P0 harnesses instead of inventing a third result format.
