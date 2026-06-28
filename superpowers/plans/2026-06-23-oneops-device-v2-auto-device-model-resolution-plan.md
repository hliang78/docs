# OneOPS Device V2 Auto Device Model Resolution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatically resolve or create a `device_model` during Device V2 -> V1 normalization when manufacturer and model are known but `device_model_code` is missing, so downstream V1 and monitoring flows receive structured model identity.

**Architecture:** Extend the existing `normalizeDeviceV2ForV1Sync` path in `app/device/v2/api/device_v2_sync_to_v1.go` with one focused helper that looks up the manufacturer, reuses an existing device model by name, or creates a new one and writes the resulting `device_model_code` back into normalized Device V2 attributes/metadata. Keep the rest of the V1 sync path unchanged, and prove behavior with unit tests plus sqlite-backed normalization tests that reuse the current `openDeviceV2EntryE2EDB` fixture style.

**Tech Stack:** Go, GORM, sqlite-backed Go tests, existing `base/service` manufacturer and device-model services, existing Device V2 sync-to-V1 API/tests.

---

## File Structure

**Files:**
- Modify: `OneOps/app/device/v2/api/device_v2.go`
- Modify: `OneOps/app/device/v2/api/device_v2_sync_to_v1.go`
- Modify: `OneOps/app/device/v2/api/device_v2_sync_to_v1_test.go`
- Modify: `OneOps/cmd/wire_gen.go`
- Verify: `OneOps/app/base/service/i_manufacturer.go`
- Verify: `OneOps/app/base/service/i_device_model.go`

**Responsibilities:**
- `app/device/v2/api/device_v2.go`
  - Inject the base manufacturer/device-model services into `DeviceV2API`.
- `app/device/v2/api/device_v2_sync_to_v1.go`
  - Add one normalization helper for model resolution/creation and call it from `normalizeDeviceV2ForV1Sync`.
  - Add structured logs for reuse/create/skip/fail decisions.
- `app/device/v2/api/device_v2_sync_to_v1_test.go`
  - Add pure unit tests for skip/reuse/create/error paths.
  - Add sqlite-backed normalization tests proving `device_model_code` gets written back.
- `cmd/wire_gen.go`
  - Thread existing constructed `manufacturerSrv` and `deviceModelSrv` into `DeviceV2API`.

---

### Task 1: Lock the Behavior with Failing Tests

**Files:**
- Modify: `OneOps/app/device/v2/api/device_v2_sync_to_v1_test.go`
- Verify: `OneOps/app/device/v2/api/device_v2_entry_e2e_test.go`

- [ ] **Step 1: Add fake base-service stubs for manufacturer and device-model lookups**

Add focused test doubles near the existing `fakeDeviceV1ServiceForSync` definitions:

```go
type fakeManufacturerServiceForSync struct {
	basesvc.IManufacturer
	findByNameFn func(name string, ctx context.Context) (*basedto.ManufacturerResp, error)
}

func (f *fakeManufacturerServiceForSync) FindByName(name string, ctx context.Context) (*basedto.ManufacturerResp, error) {
	if f.findByNameFn != nil {
		return f.findByNameFn(name, ctx)
	}
	return nil, nil
}

type fakeDeviceModelServiceForSync struct {
	basesvc.IDeviceModel
	findByNameFn func(name string, ctx context.Context) (*basedto.DeviceModelResp, error)
	createFn     func(r basedto.DeviceModelReq, ctx context.Context) (*basedto.DeviceModelResp, error)
	createCalls  []basedto.DeviceModelReq
}

func (f *fakeDeviceModelServiceForSync) FindByName(name string, ctx context.Context) (*basedto.DeviceModelResp, error) {
	if f.findByNameFn != nil {
		return f.findByNameFn(name, ctx)
	}
	return nil, nil
}

func (f *fakeDeviceModelServiceForSync) Create(r basedto.DeviceModelReq, ctx context.Context) (*basedto.DeviceModelResp, error) {
	f.createCalls = append(f.createCalls, r)
	if f.createFn != nil {
		return f.createFn(r, ctx)
	}
	return nil, nil
}
```

- [ ] **Step 2: Add unit tests for skip and reuse behavior**

Add tests that prove normalization does nothing when it should skip, and reuses existing models when available:

```go
func TestNormalizeDeviceV2ForV1SyncSkipsAutoModelWhenCodeAlreadyPresent(t *testing.T) {
	api := &DeviceV2API{
		ManufacturerSrv: &fakeManufacturerServiceForSync{},
		DeviceModelSrv:  &fakeDeviceModelServiceForSync{},
	}
	device := &devv2model.DeviceV2{
		Attributes: map[string]interface{}{
			"device_model_code": "DM-EXISTING",
			"device_model_name": "VSR1000",
			"manufacturer_name": "H3C",
		},
	}

	got, err := api.normalizeDeviceV2ForV1Sync(context.Background(), device)
	if err != nil {
		t.Fatalf("normalize returned error: %v", err)
	}
	if got.Attributes["device_model_code"] != "DM-EXISTING" {
		t.Fatalf("expected existing model code preserved, got %+v", got.Attributes)
	}
}

func TestNormalizeDeviceV2ForV1SyncReusesExistingDeviceModelByName(t *testing.T) {
	api := &DeviceV2API{
		ManufacturerSrv: &fakeManufacturerServiceForSync{
			findByNameFn: func(name string, ctx context.Context) (*basedto.ManufacturerResp, error) {
				return &basedto.ManufacturerResp{Common: commonDTO.Common{ID: "mf-h3c"}, Name: "H3C"}, nil
			},
		},
		DeviceModelSrv: &fakeDeviceModelServiceForSync{
			findByNameFn: func(name string, ctx context.Context) (*basedto.DeviceModelResp, error) {
				return &basedto.DeviceModelResp{Code: "DM-VSR1000", Name: "VSR1000", ManufacturerID: "mf-h3c"}, nil
			},
		},
	}
	device := &devv2model.DeviceV2{
		Attributes: map[string]interface{}{"platform_code": "PLT-COMWARE"},
		Metadata: map[string]interface{}{
			"catalog_code":      "CAT-NETWORK",
			"site_code":         "SITE-1",
			"rack_code":         "RACK-1",
			"manufacturer_name": "H3C",
			"device_model_name": "VSR1000",
		},
	}

	got, err := api.normalizeDeviceV2ForV1Sync(context.Background(), device)
	if err != nil {
		t.Fatalf("normalize returned error: %v", err)
	}
	if got.Metadata["device_model_code"] != "DM-VSR1000" {
		t.Fatalf("expected reused model code, got %+v", got.Metadata)
	}
}
```

- [ ] **Step 3: Add unit tests for create, skip-on-missing-manufacturer, and error paths**

Add tests covering the new decisions:

```go
func TestNormalizeDeviceV2ForV1SyncCreatesDeviceModelWhenMissing(t *testing.T) {
	modelSrv := &fakeDeviceModelServiceForSync{
		findByNameFn: func(name string, ctx context.Context) (*basedto.DeviceModelResp, error) { return nil, nil },
		createFn: func(r basedto.DeviceModelReq, ctx context.Context) (*basedto.DeviceModelResp, error) {
			return &basedto.DeviceModelResp{Code: "DM-VSR1000", Name: r.Name, ManufacturerID: r.ManufacturerID}, nil
		},
	}
	api := &DeviceV2API{
		ManufacturerSrv: &fakeManufacturerServiceForSync{
			findByNameFn: func(name string, ctx context.Context) (*basedto.ManufacturerResp, error) {
				return &basedto.ManufacturerResp{Common: commonDTO.Common{ID: "mf-h3c"}, Name: "H3C"}, nil
			},
		},
		DeviceModelSrv: modelSrv,
	}
	device := &devv2model.DeviceV2{
		Attributes: map[string]interface{}{"platform_code": "PLT-COMWARE", "catalog_code": "CAT-NETWORK", "site_code": "SITE-1", "rack_code": "RACK-1"},
		Metadata: map[string]interface{}{"manufacturer_name": "H3C", "device_model_name": "VSR1000"},
	}

	got, err := api.normalizeDeviceV2ForV1Sync(context.Background(), device)
	if err != nil {
		t.Fatalf("normalize returned error: %v", err)
	}
	if len(modelSrv.createCalls) != 1 || modelSrv.createCalls[0].ManufacturerID != "mf-h3c" {
		t.Fatalf("expected one model create call, got %+v", modelSrv.createCalls)
	}
	if got.Attributes["device_model_code"] != "DM-VSR1000" {
		t.Fatalf("expected created model code written back, got %+v", got.Attributes)
	}
}

func TestNormalizeDeviceV2ForV1SyncSkipsAutoModelWhenManufacturerMissing(t *testing.T) {
	modelSrv := &fakeDeviceModelServiceForSync{}
	api := &DeviceV2API{DeviceModelSrv: modelSrv}
	device := &devv2model.DeviceV2{
		Attributes: map[string]interface{}{"platform_code": "PLT-COMWARE", "catalog_code": "CAT-NETWORK", "site_code": "SITE-1", "rack_code": "RACK-1"},
		Metadata: map[string]interface{}{"device_model_name": "VSR1000"},
	}

	got, err := api.normalizeDeviceV2ForV1Sync(context.Background(), device)
	if err != nil {
		t.Fatalf("normalize returned error: %v", err)
	}
	if got.Metadata["device_model_code"] != nil {
		t.Fatalf("did not expect device_model_code to be synthesized, got %+v", got.Metadata)
	}
	if len(modelSrv.createCalls) != 0 {
		t.Fatalf("did not expect create call, got %+v", modelSrv.createCalls)
	}
}

func TestNormalizeDeviceV2ForV1SyncReturnsErrorWhenModelCreateFails(t *testing.T) {
	api := &DeviceV2API{
		ManufacturerSrv: &fakeManufacturerServiceForSync{
			findByNameFn: func(name string, ctx context.Context) (*basedto.ManufacturerResp, error) {
				return &basedto.ManufacturerResp{Common: commonDTO.Common{ID: "mf-h3c"}, Name: "H3C"}, nil
			},
		},
		DeviceModelSrv: &fakeDeviceModelServiceForSync{
			findByNameFn: func(name string, ctx context.Context) (*basedto.DeviceModelResp, error) { return nil, nil },
			createFn: func(r basedto.DeviceModelReq, ctx context.Context) (*basedto.DeviceModelResp, error) {
				return nil, errors.New("insert failed")
			},
		},
	}
	device := &devv2model.DeviceV2{
		Attributes: map[string]interface{}{"platform_code": "PLT-COMWARE", "catalog_code": "CAT-NETWORK", "site_code": "SITE-1", "rack_code": "RACK-1"},
		Metadata: map[string]interface{}{"manufacturer_name": "H3C", "device_model_name": "VSR1000"},
	}

	_, err := api.normalizeDeviceV2ForV1Sync(context.Background(), device)
	if err == nil {
		t.Fatalf("expected create failure to be returned")
	}
}
```

- [ ] **Step 4: Run the focused test slice and verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/device/v2/api -run 'TestNormalizeDeviceV2ForV1Sync(SkipsAutoModelWhenCodeAlreadyPresent|ReusesExistingDeviceModelByName|CreatesDeviceModelWhenMissing|SkipsAutoModelWhenManufacturerMissing|ReturnsErrorWhenModelCreateFails)' -count=1
```

Expected:

```text
FAIL
... DeviceV2API has no field or method ManufacturerSrv / DeviceModelSrv ...
... normalizeDeviceV2ForV1Sync does not synthesize device_model_code ...
```

- [ ] **Step 5: Commit the red tests**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/device/v2/api/device_v2_sync_to_v1_test.go
git commit -m "test: lock device model auto-resolution behavior"
```

---

### Task 2: Inject Base Services and Implement the Normalization Helper

**Files:**
- Modify: `OneOps/app/device/v2/api/device_v2.go`
- Modify: `OneOps/app/device/v2/api/device_v2_sync_to_v1.go`
- Modify: `OneOps/cmd/wire_gen.go`

- [ ] **Step 1: Add the two base-service dependencies to `DeviceV2API`**

Update `DeviceV2APISet` and `DeviceV2API`:

```go
var DeviceV2APISet = wire.NewSet(wire.Struct(new(DeviceV2API),
	"Logger",
	"DB",
	"Config",
	"ImportExcelSrv",
	"DeviceV2Srv",
	"DeviceSrv",
	"DeviceStoreSrv",
	"DeviceInterfaceV2Srv",
	"DeviceV2SchemaSrv",
	"PrefixSrv",
	"EntityV2Srv",
	"CredentialResolver",
	"MonitoringTaskProjectionServiceV2",
	"DeviceConfigBackupSrv",
	"ConfigVersionSrv",
	"ConfigDiffSrv",
	"ConfigBaselineSrv",
	"ManufacturerSrv",
	"DeviceModelSrv",
	"Query",
	"RelationCleaner",
))

type DeviceV2API struct {
	// existing fields ...
	ManufacturerSrv                 baseService.IManufacturer
	DeviceModelSrv                  baseService.IDeviceModel
	Query                           *mysql.Query
	RelationCleaner                 RelationCleaner
}
```

- [ ] **Step 2: Thread the services through `cmd/wire_gen.go`**

Update the generated constructor block for `DeviceV2API`:

```go
	deviceV2API := &api.DeviceV2API{
		Logger:                            logger,
		DB:                                dbTypeMySQL,
		Config:                            configConfig,
		ImportExcelSrv:                    importExcelSrv,
		DeviceV2Srv:                       deviceV2Srv,
		DeviceSrv:                         deviceSrv,
		DeviceStoreSrv:                    deviceStoreSrv,
		DeviceInterfaceV2Srv:              deviceInterfaceV2Srv,
		DeviceV2SchemaSrv:                 deviceV2SchemaSrv,
		PrefixSrv:                         prefixSrv,
		EntityV2Srv:                       entityV2Srv,
		CredentialResolver:                credentialResolver,
		MonitoringTaskProjectionServiceV2: monitoringTaskProjectionServiceV2,
		DeviceConfigBackupSrv:             deviceConfigBackupSrv,
		ConfigVersionSrv:                  configVersionSrv,
		ConfigDiffSrv:                     configDiffSrv,
		ConfigBaselineSrv:                 configBaselineSrv,
		ManufacturerSrv:                   manufacturerSrv,
		DeviceModelSrv:                    deviceModelSrv,
		Query:                             query,
		RelationCleaner:                   relationCleaner,
	}
```

- [ ] **Step 3: Add one focused helper to resolve or create the device model**

In `device_v2_sync_to_v1.go`, add a helper that keeps the new behavior isolated:

```go
func (a *DeviceV2API) resolveDeviceModelCodeForV1Sync(ctx context.Context, attrs, meta map[string]interface{}) (string, error) {
	if a == nil || a.ManufacturerSrv == nil || a.DeviceModelSrv == nil {
		return "", nil
	}

	manufacturerName := firstNonEmpty(
		stringFromAnyMap(attrs, "manufacturer_name"),
		stringFromAnyMap(meta, "manufacturer_name"),
		stringFromAnyMap(attrs, "manufacturer"),
		stringFromAnyMap(meta, "manufacturer"),
		stringFromAnyMap(attrs, "vendor"),
		stringFromAnyMap(meta, "vendor"),
	)
	modelName := firstNonEmpty(
		stringFromAnyMap(attrs, "device_model_name"),
		stringFromAnyMap(meta, "device_model_name"),
		stringFromAnyMap(attrs, "model"),
		stringFromAnyMap(meta, "model"),
	)
	if manufacturerName == "" || modelName == "" {
		return "", nil
	}

	manufacturer, err := a.ManufacturerSrv.FindByName(manufacturerName, ctx)
	if err != nil {
		return "", fmt.Errorf("resolve manufacturer for device model sync: %w", err)
	}
	if manufacturer == nil || strings.TrimSpace(manufacturer.ID) == "" {
		return "", nil
	}

	existing, err := a.DeviceModelSrv.FindByName(modelName, ctx)
	if err != nil {
		return "", fmt.Errorf("find device model by name for sync: %w", err)
	}
	if existing != nil && strings.TrimSpace(existing.Code) != "" {
		return strings.TrimSpace(existing.Code), nil
	}

	created, err := a.DeviceModelSrv.Create(basedto.DeviceModelReq{
		Name:           modelName,
		ManufacturerID: manufacturer.ID,
		Description:    "auto-created from device_v2 sync",
		UHeight:        1,
		Support:        true,
	}, ctx)
	if err != nil {
		reused, lookupErr := a.DeviceModelSrv.FindByName(modelName, ctx)
		if lookupErr == nil && reused != nil && strings.TrimSpace(reused.Code) != "" {
			return strings.TrimSpace(reused.Code), nil
		}
		return "", fmt.Errorf("create device model for sync: %w", err)
	}
	if created == nil {
		return "", nil
	}
	return strings.TrimSpace(created.Code), nil
}
```

- [ ] **Step 4: Call the helper from `normalizeDeviceV2ForV1Sync` and write back the result**

Add the new normalization branch after the existing platform/catalog/site/rack resolution:

```go
	if strings.TrimSpace(stringFromAnyMap(normalized.Attributes, "device_model_code")) == "" {
		deviceModelCode, err := a.resolveDeviceModelCodeForV1Sync(ctx, normalized.Attributes, normalized.Metadata)
		if err != nil {
			return nil, err
		}
		if deviceModelCode != "" {
			setAnyMapString(normalized.Attributes, "device_model_code", deviceModelCode)
			setAnyMapString(normalized.Metadata, "device_model_code", deviceModelCode)
		}
	}
```

Add structured logs around skip/reuse/create paths:

```go
if a.Logger != nil {
	a.Logger.Info("device_v2 sync device_model auto_created",
		zap.String("manufacturer_name", manufacturerName),
		zap.String("device_model_name", modelName),
		zap.String("device_model_code", created.Code))
}
```

- [ ] **Step 5: Run the same focused test slice and verify it passes**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/device/v2/api -run 'TestNormalizeDeviceV2ForV1Sync(SkipsAutoModelWhenCodeAlreadyPresent|ReusesExistingDeviceModelByName|CreatesDeviceModelWhenMissing|SkipsAutoModelWhenManufacturerMissing|ReturnsErrorWhenModelCreateFails)' -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/app/device/v2/api	0.xxxs
```

- [ ] **Step 6: Commit the implementation core**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/device/v2/api/device_v2.go app/device/v2/api/device_v2_sync_to_v1.go cmd/wire_gen.go
git commit -m "feat: auto-resolve device model during v2 sync"
```

---

### Task 3: Prove sqlite-backed Normalization and Request Propagation

**Files:**
- Modify: `OneOps/app/device/v2/api/device_v2_sync_to_v1_test.go`
- Verify: `OneOps/app/device/v2/api/device_v2_entry_e2e_test.go`

- [ ] **Step 1: Add a sqlite-backed test for creating a missing model and writing it back**

Add a test using `openDeviceV2EntryE2EDB` and `seedDeviceV2EntryRuntimeReferenceData`:

```go
func TestBuildDeviceV1SyncReqFromDeviceV2AutoCreatesDeviceModelFromManufacturerAndModelName(t *testing.T) {
	db := openDeviceV2EntryE2EDB(t)
	seedDeviceV2EntryRuntimeReferenceData(t, db)

	api := &DeviceV2API{
		DB: types.DBTypeMySQL(db),
		ManufacturerSrv: impl.NewManufacturerSrv(zap.NewNop(), codec.NewGenerateCodeSrv(), validate.NewFieldValidatorSrv(), proxy.NewTxProxySrv(db)),
		DeviceModelSrv:  impl.NewDeviceModelSrv(zap.NewNop(), codec.NewGenerateCodeSrv(), validate.NewFieldValidatorSrv(), impl.NewManufacturerSrv(zap.NewNop(), codec.NewGenerateCodeSrv(), validate.NewFieldValidatorSrv(), proxy.NewTxProxySrv(db)), proxy.NewTxProxySrv(db)),
	}
	device := &devv2model.DeviceV2{
		Code: "DVC-VSR1000",
		Name: "router-vsr1000",
		Attributes: map[string]interface{}{
			"platform_name": "Comware",
			"catalog_name":  "NETWORK",
		},
		Metadata: map[string]interface{}{
			"manufacturer_name": "H3C",
			"device_model_name": "VSR1000",
			"site_code":         "SITE-1",
			"rack_code":         "RACK-1",
		},
	}

	req, err := api.buildDeviceV1SyncReqFromDeviceV2(context.Background(), device, nil)
	if err != nil {
		t.Fatalf("build req failed: %v", err)
	}
	if req.DeviceModelCode == "" {
		t.Fatalf("expected device_model_code synthesized, got %#v", req)
	}
}
```

- [ ] **Step 2: Add a sqlite-backed idempotency test**

Add a second test that runs normalization twice and asserts only one row exists:

```go
func TestNormalizeDeviceV2ForV1SyncDoesNotCreateDuplicateDeviceModelRows(t *testing.T) {
	db := openDeviceV2EntryE2EDB(t)
	seedDeviceV2EntryRuntimeReferenceData(t, db)

	api := newDeviceV2APISyncTestWithBaseServices(t, db)
	device := &devv2model.DeviceV2{
		Code: "DVC-VSR1000-IDEMPOTENT",
		Attributes: map[string]interface{}{
			"platform_code": "PLT-COMWARE",
			"catalog_code":  "CAT-NETWORK",
			"site_code":     "SITE-1",
			"rack_code":     "RACK-1",
		},
		Metadata: map[string]interface{}{
			"manufacturer_name": "H3C",
			"device_model_name": "VSR1000",
		},
	}

	for i := 0; i < 2; i++ {
		if _, err := api.normalizeDeviceV2ForV1Sync(context.Background(), device); err != nil {
			t.Fatalf("normalize run %d failed: %v", i, err)
		}
	}

	var count int64
	if err := db.Table("device_model").Where("LOWER(name)=LOWER(?)", "VSR1000").Count(&count).Error; err != nil {
		t.Fatalf("count device_model failed: %v", err)
	}
	if count != 1 {
		t.Fatalf("expected exactly one VSR1000 row, got %d", count)
	}
}
```

- [ ] **Step 3: Add a tiny test helper for constructing base services against sqlite**

Define one helper in the same test file so the two sqlite tests stay readable:

```go
func newDeviceV2APISyncTestWithBaseServices(t *testing.T, db *gorm.DB) *DeviceV2API {
	t.Helper()
	txProxy := proxy.NewTxProxySrv(db)
	generateCodeSrv := codec.NewGenerateCodeSrv()
	fieldValidatorSrv := validate.NewFieldValidatorSrv()
	manufacturerSrv := impl.NewManufacturerSrv(zap.NewNop(), generateCodeSrv, fieldValidatorSrv, txProxy)
	deviceModelSrv := impl.NewDeviceModelSrv(zap.NewNop(), generateCodeSrv, fieldValidatorSrv, manufacturerSrv, txProxy)
	return &DeviceV2API{
		DB:              types.DBTypeMySQL(db),
		Logger:          zap.NewNop(),
		ManufacturerSrv: manufacturerSrv,
		DeviceModelSrv:  deviceModelSrv,
	}
}
```

- [ ] **Step 4: Run the sqlite-backed normalization tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/device/v2/api -run 'Test(BuildDeviceV1SyncReqFromDeviceV2AutoCreatesDeviceModelFromManufacturerAndModelName|NormalizeDeviceV2ForV1SyncDoesNotCreateDuplicateDeviceModelRows)' -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/app/device/v2/api	0.xxxs
```

- [ ] **Step 5: Commit the sqlite-backed regression coverage**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/device/v2/api/device_v2_sync_to_v1_test.go
git commit -m "test: cover auto-created device model normalization"
```

---

### Task 4: Full Verification and Regression Notes

**Files:**
- Modify: `OneOps/app/device/v2/api/device_v2_sync_to_v1.go`
- Modify: `OneOps/app/device/v2/api/device_v2_sync_to_v1_test.go`
- Modify: `OneOps/app/device/v2/api/device_v2.go`
- Modify: `OneOps/cmd/wire_gen.go`

- [ ] **Step 1: Run the full sync-to-V1 API test file**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/device/v2/api -run 'Test(BuildDeviceV1SyncReqFromDeviceV2|NormalizeDeviceV2ForV1Sync|FindExistingDeviceV1ForBackfill)' -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/app/device/v2/api	0.xxxs
```

- [ ] **Step 2: Run a package-level regression pass**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/device/v2/api ./app/base/service/impl -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/app/device/v2/api	...
ok  	github.com/netxops/OneOps/app/base/service/impl	...
```

- [ ] **Step 3: Sanity-check the generated wiring compiles**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./cmd -run TestDoesNotExist -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/cmd	0.xxxs [no tests to run]
```

- [ ] **Step 4: Record the two real-device verification queries for manual follow-up**

Keep these commands in the execution notes after code lands:

```bash
mysql -h127.0.0.1 -P3606 -uUniOPS -p'UniOPS@Passw0rd' UniOPS -e "SELECT code,name,device_model_code,platform_code,catalog_code FROM device WHERE code IN ('DEV20260619000009','DEV20260623000001')"

mysql -h127.0.0.1 -P3606 -uUniOPS -p'UniOPS@Passw0rd' UniOPS -e "SELECT code,name,manufacturer_id FROM device_model WHERE LOWER(name)=LOWER('VSR1000')"
```

Expected:

```text
device.device_model_code is no longer NULL for the two target V1 rows
device_model contains exactly one VSR1000 row bound to the H3C manufacturer
```

- [ ] **Step 5: Commit the final verified state**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/device/v2/api/device_v2.go app/device/v2/api/device_v2_sync_to_v1.go app/device/v2/api/device_v2_sync_to_v1_test.go cmd/wire_gen.go
git commit -m "feat: backfill missing device models during v2 sync"
```

---

## Self-Review

### Spec coverage

- Auto-create only when manufacturer exists and model is known: covered in Task 1 tests and Task 2 implementation.
- No automatic manufacturer creation: covered in Task 1 skip test and Task 2 helper logic.
- Write `device_model_code` back into normalized Device V2 data: covered in Task 2 Step 4 and Task 3 sqlite test.
- Structured diagnostics: covered in Task 2 Step 4.
- Idempotency and duplicate avoidance: covered in Task 1 create/retry path plus Task 3 duplicate-row test.
- Real-sample follow-up commands: covered in Task 4 Step 4.

### Placeholder scan

- No `TODO` / `TBD` markers remain.
- Every code-writing step includes concrete snippets.
- Every verification step includes exact commands and expected output.

### Type consistency

- Uses `baseService.IManufacturer` and `baseService.IDeviceModel` on `DeviceV2API`, matching the interfaces already exposed by `app/base/service`.
- Uses `basedto.ManufacturerResp` / `basedto.DeviceModelResp` / `basedto.DeviceModelReq` consistently in tests and helper logic.
- Keeps `normalizeDeviceV2ForV1Sync` as the single integration point, matching the approved design.
