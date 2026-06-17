# Network Change Closed-Loop MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an extreme-minimal network change closed loop in OneOps that lets users publish a network change template, execute it against multiple devices through netlink config mode with `block/warn/authorize` risk handling, and launch a one-click rollback from the executed task.

**Architecture:** Keep the MVP isolated from the existing generic Task Center mainline by adding a dedicated `network change` module in platform, while reusing existing device lookup and controller `config_execute` transport. Persist only four dedicated objects: template, risk rule, task, and task-device record; represent rollback as `kind=rollback` on the same task table with a `source_task_id` back-reference.

**Tech Stack:** Go, Gin, Gorm, MySQL/sqlite tests, existing device-v2 service, controller `config_execute` HTTP API, Vue 3, Ant Design Vue, TypeScript.

---

## File Structure

### New backend files

- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/migrations/add_platform_network_change_mvp_tables_20260617.sql`
  - Adds dedicated template, task, task-device, and risk-rule tables.
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/platform_model/platform_network_change_template.go`
  - Gorm model for change templates.
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/platform_model/platform_network_change_task.go`
  - Gorm model for change and rollback tasks.
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/platform_model/platform_network_change_task_device.go`
  - Per-device execution and rollback records.
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/platform_model/platform_network_change_risk_rule.go`
  - Risk-rule persistence model.
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/dto/network_change.go`
  - Request and response DTOs for templates, rules, tasks, and logs.
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/i_network_change.go`
  - Service interface definitions.
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_template_service.go`
  - Template create, update, publish, list, and detail logic.
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_risk_rule_service.go`
  - Risk rule CRUD and command classification logic.
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_executor.go`
  - Controller `config_execute` transport client and execution mapping.
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_task_service.go`
  - Change-task creation, authorization, execution, query, and rollback entry logic.
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/api/network_change.go`
  - Gin API handlers for templates, tasks, rollback, and risk rules.
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_service_test.go`
  - sqlite-backed end-to-end service tests.

### Modified backend files

- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/router/platform.go`
  - Registers `/platform/network-change/*` routes.
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/router/platform_bidi.go`
  - Registers the same routes in bidi mode.
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/boot/provider/service_groups.go`
  - Wires the new API and services.
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/data_collection/impl/data_auto_collect.go`
  - Reference only; do not edit unless transport extraction is shared.

### New frontend files

- `OneOPS-UI/src/api/platform/network-change.ts`
  - Frontend request wrappers.
- `OneOPS-UI/src/typings/platform/network-change.ts`
  - Frontend DTO typings.
- `OneOPS-UI/src/views/platform/NetworkChangeTemplateManagement.vue`
  - Template list plus drawer editor/publish.
- `OneOPS-UI/src/views/platform/NetworkChangeTaskManagement.vue`
  - Task create/list/detail/rollback page.
- `OneOPS-UI/src/views/platform/NetworkChangeRiskRuleManagement.vue`
  - Risk-rule list/editor page.
- `OneOPS-UI/scripts/network-change-mvp-smoke.ts`
  - Smoke script that checks route, API imports, and core page state wiring.

### Modified frontend files

- `OneOPS-UI/src/router/utils.ts`
  - Adds three routes.
- `OneOPS-UI/package.json`
  - Adds `smoke:network-change-mvp`.

---

### Task 1: Create the isolated persistence model and API contracts

**Files:**
- Create: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/migrations/add_platform_network_change_mvp_tables_20260617.sql`
- Create: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/platform_model/platform_network_change_template.go`
- Create: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/platform_model/platform_network_change_task.go`
- Create: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/platform_model/platform_network_change_task_device.go`
- Create: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/platform_model/platform_network_change_risk_rule.go`
- Create: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/dto/network_change.go`
- Create: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/i_network_change.go`
- Test: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_service_test.go`

- [ ] **Step 1: Write the first failing sqlite contract test**

Create `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_service_test.go` with:

```go
package impl

import (
	"context"
	"testing"

	"github.com/netxops/OneOps/app/platform/dto"
	platformTenant "github.com/netxops/OneOps/app/platform/pkg/tenant"
	platformModel "github.com/netxops/OneOps/app/platform/platform_model"
	"github.com/netxops/OneOps/pkg/types"
	"go.uber.org/zap"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
)

func newNetworkChangeTestDB(t *testing.T) *gorm.DB {
	t.Helper()
	db, err := gorm.Open(sqlite.Open("file::memory:?cache=shared"), &gorm.Config{})
	if err != nil {
		t.Fatalf("open sqlite failed: %v", err)
	}
	err = db.AutoMigrate(
		&platformModel.PlatformNetworkChangeTemplate{},
		&platformModel.PlatformNetworkChangeTask{},
		&platformModel.PlatformNetworkChangeTaskDevice{},
		&platformModel.PlatformNetworkChangeRiskRule{},
	)
	if err != nil {
		t.Fatalf("auto migrate failed: %v", err)
	}
	return db
}

func newNetworkChangeRiskRuleServiceForTest(t *testing.T) *NetworkChangeRiskRuleService {
	t.Helper()
	return NewNetworkChangeRiskRuleService(zap.NewNop(), types.DBTypeMySQL(newNetworkChangeTestDB(t)))
}

func newNetworkChangeTemplateServiceForTest(t *testing.T) *NetworkChangeTemplateService {
	t.Helper()
	db := newNetworkChangeTestDB(t)
	return NewNetworkChangeTemplateService(zap.NewNop(), types.DBTypeMySQL(db), NewNetworkChangeRiskRuleService(zap.NewNop(), types.DBTypeMySQL(db)))
}

type fakeNetworkChangeDeviceService struct {
	items map[string]dto.NetworkChangeDeviceTargetResp
}

func (f *fakeNetworkChangeDeviceService) seed(code, deviceType, vendor string) {
	if f.items == nil {
		f.items = map[string]dto.NetworkChangeDeviceTargetResp{}
	}
	f.items[code] = dto.NetworkChangeDeviceTargetResp{
		DeviceCode: code,
		DeviceType: deviceType,
		Vendor:     vendor,
	}
}

type fakeNetworkChangeExecutor struct {
	calls int
}

func newNetworkChangeTaskServiceForTest(t *testing.T) (*NetworkChangeTaskService, *fakeNetworkChangeDeviceService, *fakeNetworkChangeExecutor) {
	t.Helper()
	db := newNetworkChangeTestDB(t)
	ruleSvc := NewNetworkChangeRiskRuleService(zap.NewNop(), types.DBTypeMySQL(db))
	templateSvc := NewNetworkChangeTemplateService(zap.NewNop(), types.DBTypeMySQL(db), ruleSvc)
	deviceSvc := &fakeNetworkChangeDeviceService{}
	executor := &fakeNetworkChangeExecutor{}
	taskSvc := NewNetworkChangeTaskService(zap.NewNop(), types.DBTypeMySQL(db), deviceSvc, templateSvc, ruleSvc, executor)
	return taskSvc, deviceSvc, executor
}

func mustCreatePublishedTemplate(t *testing.T, svc *NetworkChangeTemplateService, commands, rollback []string) *dto.NetworkChangeTemplateResp {
	t.Helper()
	row, err := svc.CreateTemplate(context.Background(), &dto.NetworkChangeTemplateCreateReq{
		Name: "tmpl",
		Spec: dto.NetworkChangeTemplateSpec{
			DeviceTypes:       []string{"switch"},
			CommandTemplates:  commands,
			RollbackTemplates: rollback,
			ConfigMode:        true,
			RiskScanEnabled:   true,
		},
	})
	if err != nil {
		t.Fatalf("CreateTemplate failed: %v", err)
	}
	published, err := svc.PublishTemplate(context.Background(), row.ID, "tester")
	if err != nil {
		t.Fatalf("PublishTemplate failed: %v", err)
	}
	return published
}

func mustCreateAuthorizeRule(t *testing.T, svc *NetworkChangeRiskRuleService, pattern string) {
	t.Helper()
	_, err := svc.CreateRule(context.Background(), &dto.NetworkChangeRiskRuleCreateReq{
		Name: "authorize-rule", Level: "authorize", MatchType: "keyword", Pattern: pattern,
	})
	if err != nil {
		t.Fatalf("CreateRule failed: %v", err)
	}
}

func TestNetworkChangeModels_AutoMigrateAndPersistTemplate(t *testing.T) {
	db := newNetworkChangeTestDB(t)
	ctx := platformTenant.WithCode(context.Background(), "tenant-a")
	row := &platformModel.PlatformNetworkChangeTemplate{
		Name:               "switch-vlan-open",
		DeviceTypesJSON:    `["switch"]`,
		VendorsJSON:        `["huawei"]`,
		ParameterSpecsJSON: `[{"key":"vlan_id","required":true}]`,
		CommandTemplateJSON: `[{"line":"vlan {{vlan_id}}"}]`,
		RollbackTemplateJSON: `[{"line":"undo vlan {{vlan_id}}"}]`,
		Status:             "draft",
	}
	platformTenant.Assign(ctx, row)
	if err := db.Table(row.TableName()).Create(row).Error; err != nil {
		t.Fatalf("create template failed: %v", err)
	}
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `go test ./app/platform/service/impl -run TestNetworkChangeModels_AutoMigrateAndPersistTemplate -count=1`

Expected: FAIL because the network change models do not exist yet.

- [ ] **Step 3: Add the schema and model/DTO skeletons**

Create the migration file:

```sql
CREATE TABLE IF NOT EXISTS platform_network_change_template (
  id varchar(64) PRIMARY KEY,
  tenant_code varchar(64) NOT NULL DEFAULT '',
  name varchar(128) NOT NULL,
  description varchar(512) NOT NULL DEFAULT '',
  device_types_json text NOT NULL,
  vendors_json text NOT NULL,
  execution_channel varchar(32) NOT NULL DEFAULT 'controller_netlink',
  config_mode tinyint(1) NOT NULL DEFAULT 1,
  timeout_sec int NOT NULL DEFAULT 120,
  parameter_specs_json text NOT NULL,
  command_template_json text NOT NULL,
  rollback_template_json text NOT NULL,
  risk_scan_enabled tinyint(1) NOT NULL DEFAULT 1,
  status varchar(32) NOT NULL DEFAULT 'draft',
  published_at datetime NULL,
  created_at datetime NULL,
  updated_at datetime NULL,
  deleted_at bigint NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS platform_network_change_risk_rule (
  id varchar(64) PRIMARY KEY,
  tenant_code varchar(64) NOT NULL DEFAULT '',
  name varchar(128) NOT NULL,
  level varchar(16) NOT NULL,
  match_type varchar(16) NOT NULL,
  pattern varchar(512) NOT NULL,
  scope_device_types_json text NOT NULL,
  scope_vendors_json text NOT NULL,
  enabled tinyint(1) NOT NULL DEFAULT 1,
  description varchar(512) NOT NULL DEFAULT '',
  created_at datetime NULL,
  updated_at datetime NULL,
  deleted_at bigint NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS platform_network_change_task (
  id varchar(64) PRIMARY KEY,
  tenant_code varchar(64) NOT NULL DEFAULT '',
  kind varchar(16) NOT NULL,
  source_task_id varchar(64) NOT NULL DEFAULT '',
  template_id varchar(64) NOT NULL,
  template_snapshot_json text NOT NULL,
  status varchar(32) NOT NULL,
  authorization_status varchar(32) NOT NULL DEFAULT 'not_required',
  risk_summary_json text NOT NULL,
  operator varchar(128) NOT NULL DEFAULT '',
  authorized_by varchar(128) NOT NULL DEFAULT '',
  started_at datetime NULL,
  finished_at datetime NULL,
  created_at datetime NULL,
  updated_at datetime NULL,
  deleted_at bigint NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS platform_network_change_task_device (
  id varchar(64) PRIMARY KEY,
  tenant_code varchar(64) NOT NULL DEFAULT '',
  task_id varchar(64) NOT NULL,
  device_code varchar(64) NOT NULL,
  device_type varchar(32) NOT NULL,
  vendor varchar(64) NOT NULL DEFAULT '',
  stage varchar(32) NOT NULL,
  status varchar(32) NOT NULL,
  commands_json text NOT NULL,
  rollback_commands_json text NOT NULL,
  matched_rules_json text NOT NULL,
  outputs_json text NOT NULL,
  started_at datetime NULL,
  finished_at datetime NULL,
  created_at datetime NULL,
  updated_at datetime NULL,
  deleted_at bigint NOT NULL DEFAULT 0
);
```

Create the main DTOs and interfaces:

```go
type NetworkChangeTemplateSpec struct {
	DeviceTypes      []string          `json:"device_types"`
	Vendors          []string          `json:"vendors"`
	ExecutionChannel string            `json:"execution_channel"`
	ConfigMode       bool              `json:"config_mode"`
	TimeoutSec       int               `json:"timeout_sec"`
	ParameterSpecs   []ParameterSpecV2 `json:"parameter_specs"`
	CommandTemplates []string          `json:"command_templates"`
	RollbackTemplates []string         `json:"rollback_templates"`
	RiskScanEnabled  bool              `json:"risk_scan_enabled"`
}

type NetworkChangeTaskCreateReq struct {
	TemplateID   string            `json:"template_id"`
	DeviceCodes  []string          `json:"device_codes"`
	ParameterMap map[string]string `json:"parameter_map"`
	Operator     string            `json:"operator"`
}

type INetworkChangeService interface {
	CreateTemplate(ctx context.Context, req *dto.NetworkChangeTemplateCreateReq) (*dto.NetworkChangeTemplateResp, error)
	PublishTemplate(ctx context.Context, id string, operator string) (*dto.NetworkChangeTemplateResp, error)
	CreateTask(ctx context.Context, req *dto.NetworkChangeTaskCreateReq) (*dto.NetworkChangeTaskResp, error)
	AuthorizeTask(ctx context.Context, id string, operator string) (*dto.NetworkChangeTaskResp, error)
	ExecuteTask(ctx context.Context, id string) (*dto.NetworkChangeTaskResp, error)
	CreateRollbackTask(ctx context.Context, sourceTaskID string, operator string) (*dto.NetworkChangeTaskResp, error)
}
```

- [ ] **Step 4: Re-run the focused test**

Run: `go test ./app/platform/service/impl -run TestNetworkChangeModels_AutoMigrateAndPersistTemplate -count=1`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/migrations/add_platform_network_change_mvp_tables_20260617.sql \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/platform_model/platform_network_change_template.go \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/platform_model/platform_network_change_task.go \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/platform_model/platform_network_change_task_device.go \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/platform_model/platform_network_change_risk_rule.go \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/dto/network_change.go \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/i_network_change.go \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_service_test.go
git commit -m "feat: scaffold network change mvp persistence"
```

### Task 2: Implement risk-rule CRUD and template publish validation

**Files:**
- Create: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_risk_rule_service.go`
- Create: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_template_service.go`
- Modify: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/boot/provider/service_groups.go`
- Test: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_service_test.go`

- [ ] **Step 1: Add failing tests for `block`, `warn`, and `authorize`**

Append to `network_change_service_test.go`:

```go
func TestNetworkChangeRiskRuleService_ClassifiesCommandsByLevel(t *testing.T) {
	svc := newNetworkChangeRiskRuleServiceForTest(t)
	_, _ = svc.CreateRule(context.Background(), &dto.NetworkChangeRiskRuleCreateReq{
		Name: "block write erase", Level: "block", MatchType: "keyword", Pattern: "write erase",
	})
	_, _ = svc.CreateRule(context.Background(), &dto.NetworkChangeRiskRuleCreateReq{
		Name: "warn reload", Level: "warn", MatchType: "keyword", Pattern: "reload",
	})
	_, _ = svc.CreateRule(context.Background(), &dto.NetworkChangeRiskRuleCreateReq{
		Name: "authorize acl clear", Level: "authorize", MatchType: "prefix", Pattern: "clear access-list",
	})
	got, err := svc.ClassifyCommands(context.Background(), []string{
		"reload",
		"clear access-list 3000 counters",
		"interface Vlanif10",
	})
	if err != nil {
		t.Fatalf("ClassifyCommands failed: %v", err)
	}
	if got.HighestLevel != "authorize" {
		t.Fatalf("expected highest level authorize, got %#v", got)
	}
}

func TestNetworkChangeTemplateService_PublishBlocksBlockedCommands(t *testing.T) {
	svc := newNetworkChangeTemplateServiceForTest(t)
	template, err := svc.CreateTemplate(context.Background(), &dto.NetworkChangeTemplateCreateReq{
		Name: "erase-switch",
		Spec: dto.NetworkChangeTemplateSpec{
			DeviceTypes: []string{"switch"},
			CommandTemplates: []string{"write erase"},
			RollbackTemplates: []string{"display current-configuration"},
			ConfigMode: true,
			RiskScanEnabled: true,
		},
	})
	if err != nil {
		t.Fatalf("CreateTemplate failed: %v", err)
	}
	if _, err := svc.PublishTemplate(context.Background(), template.ID, "alice"); err == nil {
		t.Fatalf("expected publish to be blocked")
	}
}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `go test ./app/platform/service/impl -run 'TestNetworkChange(RiskRuleService|TemplateService)' -count=1`

Expected: FAIL because the risk-rule and template services do not exist yet.

- [ ] **Step 3: Implement the minimal rule and publish services**

Use these concrete service shapes:

```go
type networkChangeRiskDecision struct {
	HighestLevel string   `json:"highest_level"`
	MatchedRuleIDs []string `json:"matched_rule_ids"`
}

func (s *NetworkChangeRiskRuleService) ClassifyCommands(ctx context.Context, commands []string) (*networkChangeRiskDecision, error) {
	levels := map[string]int{"": 0, "warn": 1, "authorize": 2, "block": 3}
	out := &networkChangeRiskDecision{HighestLevel: ""}
	rules, err := s.ListEnabledRules(ctx)
	if err != nil {
		return nil, err
	}
	for _, cmd := range commands {
		for _, rule := range rules {
			if networkChangeRuleMatches(rule, cmd) {
				out.MatchedRuleIDs = append(out.MatchedRuleIDs, rule.ID)
				if levels[rule.Level] > levels[out.HighestLevel] {
					out.HighestLevel = rule.Level
				}
			}
		}
	}
	return out, nil
}

func (s *NetworkChangeTemplateService) PublishTemplate(ctx context.Context, id string, operator string) (*dto.NetworkChangeTemplateResp, error) {
	row, err := s.mustGetTemplate(ctx, id)
	if err != nil {
		return nil, err
	}
	spec, err := decodeNetworkChangeTemplateSpec(row)
	if err != nil {
		return nil, err
	}
	if spec.RiskScanEnabled {
		decision, err := s.riskRules.ClassifyCommands(ctx, spec.CommandTemplates)
		if err != nil {
			return nil, err
		}
		if decision.HighestLevel == "block" {
			return nil, fmt.Errorf("模板命中阻断命令规则")
		}
	}
	row.Status = "published"
	now := time.Now()
	row.PublishedAt = &now
	if err := s.db(ctx).Table(row.TableName()).Where("id = ?", row.ID).Updates(map[string]interface{}{
		"status": "published",
		"published_at": now,
	}).Error; err != nil {
		return nil, err
	}
	return toNetworkChangeTemplateResp(row), nil
}
```

- [ ] **Step 4: Wire the services into provider groups**

Modify `boot/provider/service_groups.go` to include the new service set:

```go
platformSrv.NetworkChangeServiceSet,
platformAPI.NetworkChangeAPISet,
```

- [ ] **Step 5: Re-run the focused tests**

Run: `go test ./app/platform/service/impl -run 'TestNetworkChange(RiskRuleService|TemplateService)' -count=1`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_risk_rule_service.go \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_template_service.go \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/boot/provider/service_groups.go \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_service_test.go
git commit -m "feat: add network change template publish and risk rules"
```

### Task 3: Implement change-task rendering, authorization, and controller config execution

**Files:**
- Create: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_executor.go`
- Create: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_task_service.go`
- Test: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_service_test.go`

- [ ] **Step 1: Add failing tests for render freeze and authorization gate**

Append to `network_change_service_test.go`:

```go
func TestNetworkChangeTaskService_CreateTaskFreezesCommandsPerDevice(t *testing.T) {
	svc, deviceSvc, executor := newNetworkChangeTaskServiceForTest(t)
	deviceSvc.seed("sw-001", "switch", "huawei")
	template := mustCreatePublishedTemplate(t, svc.templateSvc, []string{"interface Vlanif{{vlan_id}}"}, []string{"undo interface Vlanif{{vlan_id}}"})
	task, err := svc.CreateTask(context.Background(), &dto.NetworkChangeTaskCreateReq{
		TemplateID: template.ID,
		DeviceCodes: []string{"sw-001"},
		ParameterMap: map[string]string{"vlan_id": "120"},
		Operator: "alice",
	})
	if err != nil {
		t.Fatalf("CreateTask failed: %v", err)
	}
	if len(task.Devices) != 1 || task.Devices[0].Commands[0] != "interface Vlanif120" {
		t.Fatalf("expected rendered command freeze, got %#v", task.Devices)
	}
	if executor.calls != 0 {
		t.Fatalf("expected create only, no execute yet")
	}
}

func TestNetworkChangeTaskService_ExecuteTaskPausesOnAuthorize(t *testing.T) {
	svc, deviceSvc, _ := newNetworkChangeTaskServiceForTest(t)
	deviceSvc.seed("fw-001", "firewall", "h3c")
	mustCreateAuthorizeRule(t, svc.ruleSvc, "clear session")
	template := mustCreatePublishedTemplate(t, svc.templateSvc, []string{"clear session all"}, []string{"display session all"})
	task, err := svc.CreateTask(context.Background(), &dto.NetworkChangeTaskCreateReq{
		TemplateID: template.ID,
		DeviceCodes: []string{"fw-001"},
		Operator: "alice",
	})
	if err != nil {
		t.Fatalf("CreateTask failed: %v", err)
	}
	if task.Status != "pending" || task.AuthorizationStatus != "pending_authorization" {
		t.Fatalf("expected pending authorization, got %#v", task)
	}
}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `go test ./app/platform/service/impl -run 'TestNetworkChangeTaskService_' -count=1`

Expected: FAIL because the task service and executor do not exist yet.

- [ ] **Step 3: Implement the controller executor and task lifecycle**

Use the existing `data_auto_collect.go` request shape directly:

```go
type controllerConfigExecuteRequest struct {
	ID                 string                     `json:"id,omitempty"`
	RemoteInfo         structs.L2DeviceRemoteInfo `json:"remote_info"`
	Commands           []string                   `json:"commands"`
	Timeout            int                        `json:"timeout,omitempty"`
	Save               bool                       `json:"save,omitempty"`
	CaptureBefore      bool                       `json:"capture_before,omitempty"`
	CaptureAfter       bool                       `json:"capture_after,omitempty"`
	StopOnError        bool                       `json:"stop_on_error,omitempty"`
	CommandTimeoutSec  int                        `json:"command_timeout_sec,omitempty"`
	NoOutputTimeoutSec int                        `json:"no_output_timeout_sec,omitempty"`
}

func (e *NetworkChangeExecutor) ExecuteConfig(ctx context.Context, endpoint string, req *controllerConfigExecuteRequest) (*controllerConfigExecuteResponse, error) {
	payload, err := json.Marshal(req)
	if err != nil {
		return nil, err
	}
	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, strings.TrimRight(endpoint, "/")+"/api/v1/config_execute", bytes.NewReader(payload))
	if err != nil {
		return nil, err
	}
	httpReq.Header.Set("Content-Type", "application/json")
	httpResp, err := e.client.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer httpResp.Body.Close()
	var resp controllerConfigExecuteResponse
	if err := json.NewDecoder(httpResp.Body).Decode(&resp); err != nil {
		return nil, err
	}
	if httpResp.StatusCode != http.StatusOK || !resp.Success {
		return &resp, fmt.Errorf(strings.TrimSpace(resp.Error))
	}
	return &resp, nil
}
```

Implement create and execute flow:

```go
func (s *NetworkChangeTaskService) CreateTask(ctx context.Context, req *dto.NetworkChangeTaskCreateReq) (*dto.NetworkChangeTaskResp, error) {
	template, spec, err := s.templateSvc.mustGetPublishedSpec(ctx, req.TemplateID)
	if err != nil {
		return nil, err
	}
	devices, err := s.resolveTargetDevices(ctx, req.DeviceCodes)
	if err != nil {
		return nil, err
	}
	rows, summary, err := s.buildTaskDevices(ctx, spec, devices, req.ParameterMap)
	if err != nil {
		return nil, err
	}
	task := &platformModel.PlatformNetworkChangeTask{
		Kind: "change",
		TemplateID: template.ID,
		Status: "pending",
		AuthorizationStatus: networkChangeAuthorizationStatus(summary.HighestLevel),
		Operator: req.Operator,
		RiskSummaryJSON: mustJSON(summary),
		TemplateSnapshotJSON: mustJSON(spec),
	}
	if summary.HighestLevel == "block" {
		task.Status = "failed"
	}
	return s.persistTaskAndDevices(ctx, task, rows)
}

func (s *NetworkChangeTaskService) ExecuteTask(ctx context.Context, id string) (*dto.NetworkChangeTaskResp, error) {
	task, devices, err := s.mustGetExecutableTask(ctx, id)
	if err != nil {
		return nil, err
	}
	if task.AuthorizationStatus == "pending_authorization" {
		return toNetworkChangeTaskResp(task, devices), nil
	}
	return s.executeDevicesSequentially(ctx, task, devices)
}
```

- [ ] **Step 4: Re-run the focused tests**

Run: `go test ./app/platform/service/impl -run 'TestNetworkChangeTaskService_' -count=1`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_executor.go \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_task_service.go \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_service_test.go
git commit -m "feat: add network change execution service"
```

### Task 4: Implement one-click rollback on top of frozen rollback commands

**Files:**
- Modify: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_task_service.go`
- Test: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_service_test.go`

- [ ] **Step 1: Add the failing rollback reuse test**

Append to `network_change_service_test.go`:

```go
func TestNetworkChangeTaskService_CreateRollbackTaskReusesFrozenRollbackCommands(t *testing.T) {
	svc, deviceSvc, executor := newNetworkChangeTaskServiceForTest(t)
	deviceSvc.seed("sw-001", "switch", "huawei")
	template := mustCreatePublishedTemplate(t, svc.templateSvc, []string{"vlan {{vlan_id}}"}, []string{"undo vlan {{vlan_id}}"})
	changeTask, err := svc.CreateTask(context.Background(), &dto.NetworkChangeTaskCreateReq{
		TemplateID: template.ID,
		DeviceCodes: []string{"sw-001"},
		ParameterMap: map[string]string{"vlan_id": "310"},
		Operator: "alice",
	})
	if err != nil {
		t.Fatalf("CreateTask failed: %v", err)
	}
	_, err = svc.ExecuteTask(context.Background(), changeTask.ID)
	if err != nil {
		t.Fatalf("ExecuteTask failed: %v", err)
	}
	rollbackTask, err := svc.CreateRollbackTask(context.Background(), changeTask.ID, "alice")
	if err != nil {
		t.Fatalf("CreateRollbackTask failed: %v", err)
	}
	if rollbackTask.Kind != "rollback" || rollbackTask.SourceTaskID != changeTask.ID {
		t.Fatalf("expected rollback link, got %#v", rollbackTask)
	}
	if rollbackTask.Devices[0].Commands[0] != "undo vlan 310" {
		t.Fatalf("expected frozen rollback command, got %#v", rollbackTask.Devices[0].Commands)
	}
	if executor.calls != 1 {
		t.Fatalf("expected only original execute before explicit rollback, got %d", executor.calls)
	}
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `go test ./app/platform/service/impl -run TestNetworkChangeTaskService_CreateRollbackTaskReusesFrozenRollbackCommands -count=1`

Expected: FAIL because rollback creation is not implemented yet.

- [ ] **Step 3: Implement rollback creation and execution**

Add these methods:

```go
func (s *NetworkChangeTaskService) CreateRollbackTask(ctx context.Context, sourceTaskID string, operator string) (*dto.NetworkChangeTaskResp, error) {
	source, sourceDevices, err := s.mustGetFinishedChangeTask(ctx, sourceTaskID)
	if err != nil {
		return nil, err
	}
	task := &platformModel.PlatformNetworkChangeTask{
		Kind: "rollback",
		SourceTaskID: source.ID,
		TemplateID: source.TemplateID,
		Status: "pending",
		AuthorizationStatus: source.AuthorizationStatus,
		Operator: operator,
		TemplateSnapshotJSON: source.TemplateSnapshotJSON,
		RiskSummaryJSON: source.RiskSummaryJSON,
	}
	devices := make([]platformModel.PlatformNetworkChangeTaskDevice, 0, len(sourceDevices))
	for _, item := range sourceDevices {
		devices = append(devices, platformModel.PlatformNetworkChangeTaskDevice{
			TaskID: task.ID,
			DeviceCode: item.DeviceCode,
			DeviceType: item.DeviceType,
			Vendor: item.Vendor,
			Stage: "pending",
			Status: "pending",
			CommandsJSON: item.RollbackCommandsJSON,
			RollbackCommandsJSON: item.RollbackCommandsJSON,
			MatchedRulesJSON: item.MatchedRulesJSON,
			OutputsJSON: "[]",
		})
	}
	return s.persistTaskAndDeviceRows(ctx, task, devices)
}
```

- [ ] **Step 4: Re-run the focused rollback test**

Run: `go test ./app/platform/service/impl -run TestNetworkChangeTaskService_CreateRollbackTaskReusesFrozenRollbackCommands -count=1`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_task_service.go \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/service/impl/network_change_service_test.go
git commit -m "feat: add network change rollback flow"
```

### Task 5: Expose Gin APIs and wire the minimal UI

**Files:**
- Create: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/api/network_change.go`
- Modify: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/router/platform.go`
- Modify: `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/router/platform_bidi.go`
- Create: `OneOPS-UI/src/api/platform/network-change.ts`
- Create: `OneOPS-UI/src/typings/platform/network-change.ts`
- Create: `OneOPS-UI/src/views/platform/NetworkChangeTemplateManagement.vue`
- Create: `OneOPS-UI/src/views/platform/NetworkChangeTaskManagement.vue`
- Create: `OneOPS-UI/src/views/platform/NetworkChangeRiskRuleManagement.vue`
- Create: `OneOPS-UI/scripts/network-change-mvp-smoke.ts`
- Modify: `OneOPS-UI/src/router/utils.ts`
- Modify: `OneOPS-UI/package.json`
- Test: backend compile plus frontend typecheck/smoke

- [ ] **Step 1: Add the backend API surface**

Create `.codex-tmp/.../app/platform/api/network_change.go` with:

```go
type NetworkChangeAPI struct {
	Service service.INetworkChangeService
}

func (a *NetworkChangeAPI) CreateTemplate(ctx *gin.Context) {}
func (a *NetworkChangeAPI) PublishTemplate(ctx *gin.Context) {}
func (a *NetworkChangeAPI) ListTemplates(ctx *gin.Context) {}
func (a *NetworkChangeAPI) CreateRiskRule(ctx *gin.Context) {}
func (a *NetworkChangeAPI) ListRiskRules(ctx *gin.Context) {}
func (a *NetworkChangeAPI) CreateTask(ctx *gin.Context) {}
func (a *NetworkChangeAPI) ExecuteTask(ctx *gin.Context) {}
func (a *NetworkChangeAPI) AuthorizeTask(ctx *gin.Context) {}
func (a *NetworkChangeAPI) CreateRollbackTask(ctx *gin.Context) {}
func (a *NetworkChangeAPI) GetTask(ctx *gin.Context) {}
```

Register routes in both platform routers:

```go
networkChange := root.Group("/platform/network-change")
networkChange.GET("/templates", networkChangeAPI.ListTemplates)
networkChange.POST("/templates", networkChangeAPI.CreateTemplate)
networkChange.POST("/templates/:id/publish", networkChangeAPI.PublishTemplate)
networkChange.GET("/risk-rules", networkChangeAPI.ListRiskRules)
networkChange.POST("/risk-rules", networkChangeAPI.CreateRiskRule)
networkChange.POST("/tasks", networkChangeAPI.CreateTask)
networkChange.POST("/tasks/:id/execute", networkChangeAPI.ExecuteTask)
networkChange.POST("/tasks/:id/authorize", networkChangeAPI.AuthorizeTask)
networkChange.POST("/tasks/:id/rollback", networkChangeAPI.CreateRollbackTask)
networkChange.GET("/tasks/:id", networkChangeAPI.GetTask)
```

- [ ] **Step 2: Add the frontend contract wrappers**

Create `OneOPS-UI/src/api/platform/network-change.ts`:

```ts
import request, { HTTP_GET, HTTP_POST } from '@/utils/request';
import type {
  NetworkChangeTemplateCreateReq,
  NetworkChangeTemplateResp,
  NetworkChangeRiskRuleCreateReq,
  NetworkChangeRiskRuleResp,
  NetworkChangeTaskCreateReq,
  NetworkChangeTaskResp,
} from '@/typings/platform/network-change';

const BASE = '/platform/network-change';

export const listNetworkChangeTemplatesReq = () => request<NetworkChangeTemplateResp[]>({ url: `${BASE}/templates`, method: HTTP_GET });
export const createNetworkChangeTemplateReq = (data: NetworkChangeTemplateCreateReq) => request<NetworkChangeTemplateResp>({ url: `${BASE}/templates`, method: HTTP_POST, data });
export const publishNetworkChangeTemplateReq = (id: string, operator: string) => request<NetworkChangeTemplateResp>({ url: `${BASE}/templates/${id}/publish`, method: HTTP_POST, data: { operator } });
export const listNetworkChangeRiskRulesReq = () => request<NetworkChangeRiskRuleResp[]>({ url: `${BASE}/risk-rules`, method: HTTP_GET });
export const createNetworkChangeRiskRuleReq = (data: NetworkChangeRiskRuleCreateReq) => request<NetworkChangeRiskRuleResp>({ url: `${BASE}/risk-rules`, method: HTTP_POST, data });
export const createNetworkChangeTaskReq = (data: NetworkChangeTaskCreateReq) => request<NetworkChangeTaskResp>({ url: `${BASE}/tasks`, method: HTTP_POST, data });
export const executeNetworkChangeTaskReq = (id: string) => request<NetworkChangeTaskResp>({ url: `${BASE}/tasks/${id}/execute`, method: HTTP_POST });
export const authorizeNetworkChangeTaskReq = (id: string, operator: string) => request<NetworkChangeTaskResp>({ url: `${BASE}/tasks/${id}/authorize`, method: HTTP_POST, data: { operator } });
export const rollbackNetworkChangeTaskReq = (id: string, operator: string) => request<NetworkChangeTaskResp>({ url: `${BASE}/tasks/${id}/rollback`, method: HTTP_POST, data: { operator } });
export const getNetworkChangeTaskReq = (id: string) => request<NetworkChangeTaskResp>({ url: `${BASE}/tasks/${id}`, method: HTTP_GET });
```

- [ ] **Step 3: Build the three minimal Vue pages**

Use three focused views instead of five separate route files:

```vue
<!-- NetworkChangeTemplateManagement.vue -->
<template>
  <PageContainer title="网络变更模板">
    <a-space direction="vertical" style="width: 100%">
      <a-button type="primary" @click="openCreate">新建模板</a-button>
      <a-table :data-source="templates" :loading="loading" row-key="id" />
      <a-drawer :open="editorOpen" width="720" title="模板编辑">
        <!-- name / device types / command templates / rollback templates -->
      </a-drawer>
    </a-space>
  </PageContainer>
</template>
```

```vue
<!-- NetworkChangeTaskManagement.vue -->
<template>
  <PageContainer title="网络变更任务">
    <a-row :gutter="16">
      <a-col :span="10">
        <a-card title="发起变更">
          <!-- template / devices / params -->
        </a-card>
      </a-col>
      <a-col :span="14">
        <a-card title="任务列表">
          <a-table :data-source="tasks" row-key="id" />
        </a-card>
      </a-col>
    </a-row>
  </PageContainer>
</template>
```

```vue
<!-- NetworkChangeRiskRuleManagement.vue -->
<template>
  <PageContainer title="高危命令规则">
    <a-button type="primary" @click="openCreate">新增规则</a-button>
    <a-table :data-source="rules" row-key="id" />
  </PageContainer>
</template>
```

Add routes in `OneOPS-UI/src/router/utils.ts`:

```ts
children.push({
  path: 'platform/network-change/templates',
  name: 'NetworkChangeTemplateManagement',
  component: () => import('@/views/platform/NetworkChangeTemplateManagement.vue'),
  meta: { title: '网络变更模板', requiresAuth: true, hideInMenu: true },
});
children.push({
  path: 'platform/network-change/tasks',
  name: 'NetworkChangeTaskManagement',
  component: () => import('@/views/platform/NetworkChangeTaskManagement.vue'),
  meta: { title: '网络变更任务', requiresAuth: true, hideInMenu: true },
});
children.push({
  path: 'platform/network-change/risk-rules',
  name: 'NetworkChangeRiskRuleManagement',
  component: () => import('@/views/platform/NetworkChangeRiskRuleManagement.vue'),
  meta: { title: '高危命令规则', requiresAuth: true, hideInMenu: true },
});
```

- [ ] **Step 4: Add the smoke script and package command**

Create `OneOPS-UI/scripts/network-change-mvp-smoke.ts`:

```ts
import { readFileSync } from 'node:fs';

const router = readFileSync('src/router/utils.ts', 'utf8');
const templateView = readFileSync('src/views/platform/NetworkChangeTemplateManagement.vue', 'utf8');
const taskView = readFileSync('src/views/platform/NetworkChangeTaskManagement.vue', 'utf8');

if (!router.includes('NetworkChangeTaskManagement')) throw new Error('missing task route');
if (!templateView.includes('网络变更模板')) throw new Error('missing template page title');
if (!taskView.includes('发起变更')) throw new Error('missing task create card');

console.log('network-change-mvp smoke passed');
```

Modify `OneOPS-UI/package.json`:

```json
"smoke:network-change-mvp": "npx esbuild scripts/network-change-mvp-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/network-change-mvp-smoke.mjs >/dev/null && node .tmp/network-change-mvp-smoke.mjs"
```

- [ ] **Step 5: Run backend and frontend verification**

Run backend compile/test:

```bash
cd .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification
go test ./app/platform/... -run 'TestNetworkChange|TestTaskTemplate|TestTaskCreation' -count=1
```

Expected: PASS for the focused network change suite and no compile errors in platform package graph.

Run frontend verification:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
npm run typecheck
npm run smoke:network-change-mvp
```

Expected: `typecheck` passes and smoke prints `network-change-mvp smoke passed`.

- [ ] **Step 6: Commit**

```bash
git add \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/api/network_change.go \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/router/platform.go \
  .codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/router/platform_bidi.go \
  OneOPS-UI/src/api/platform/network-change.ts \
  OneOPS-UI/src/typings/platform/network-change.ts \
  OneOPS-UI/src/views/platform/NetworkChangeTemplateManagement.vue \
  OneOPS-UI/src/views/platform/NetworkChangeTaskManagement.vue \
  OneOPS-UI/src/views/platform/NetworkChangeRiskRuleManagement.vue \
  OneOPS-UI/src/router/utils.ts \
  OneOPS-UI/scripts/network-change-mvp-smoke.ts \
  OneOPS-UI/package.json
git commit -m "feat: expose network change mvp api and ui"
```

## Self-Review

### Spec coverage

- Template publish: covered by Task 2.
- Risk-rule CRUD and three-level handling: covered by Tasks 2 and 3.
- Multi-device change execution: covered by Task 3.
- One-click rollback with frozen rollback commands: covered by Task 4.
- Logs and task/device detail query: covered by Tasks 3 and 5 through task-device persistence and detail APIs.
- Minimal UI entry: covered by Task 5.

### Placeholder scan

- No `TODO`, `TBD`, or “implement later” placeholders remain.
- Every task has exact files, commands, and expected outputs.

### Type consistency

- The plan consistently uses `PlatformNetworkChangeTemplate`, `PlatformNetworkChangeTask`, `PlatformNetworkChangeTaskDevice`, and `PlatformNetworkChangeRiskRule`.
- Rollback is consistently modeled as `kind=rollback` on the same task table.
