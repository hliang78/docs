# OneOPS SDN Ops Batch 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist SDN alarms, add alarm history queries, and add config-plan approval plus rollback dry-run records without adding a monitoring dashboard or enabling live SDN apply.

**Architecture:** OneOPS stores tenant-scoped operational state and remains vendor-neutral. CtrlHub remains the vendor adapter and its normalized alarm contract stays stable. UI extends the existing device SDN controller page instead of creating a new dashboard.

**Tech Stack:** Go, Gin, GORM, OneOPS tenant scoping, Vue 3, TypeScript, Ant Design Vue, existing SDN smoke scripts.

---

## Baseline

- CtrlHub has `POST /api/v1/sdn/alarms` and ACI `faultInst/faultDelegate/faultRecord` collection.
- OneOPS has current alarm fetch through CtrlHub, diagnostics, resource projection, and config-plan draft/dry-run with execute disabled.
- OneOPS-UI has `src/views/device/SdnControllerManagement.vue` with resource, alarm, diagnostic, and config-plan drawers.
- Do not implement a monitoring dashboard in this batch.

## Safety Rules

- Do not add vendor-specific SDN clients to OneOPS.
- Do not persist or echo SDN passwords, tokens, private keys, or credential request payloads.
- Do not enable live config execution or rollback execution.
- Do not revert unrelated dirty files.
- Commit each repo separately and stage only SDN-related files.
- Do not directly write unified `alert_alarm` from CtrlHub or the current SDN
  sync path in this batch. Keep `platform_sdn_alarm` as the evidence layer and
  leave unified alert-center projection to the next bridge workstream.

## Follow-Up: Unified Alert Management Bridge

After this batch, add a dedicated bridge from `platform_sdn_alarm` to the
existing OneOPS alert center. The bridge should:

- Use stable source identity `sdn:<controller_id>:<alarm_key>` for idempotency.
- Map SDN severity and state into the existing alert lifecycle.
- Preserve the SDN row as evidence and store/link the unified alert reference.
- Reuse existing confirmation, ticket, notification, and RCA flows.
- Keep CtrlHub vendor-only and avoid vendor-specific clients in OneOPS.

## Workstream W9: OneOPS Alarm Persistence And History

**Repo:** `/Users/huangliang/project/OneOPS-ALL/OneOPS`

**Files:**
- Modify: `app/platform/platform_model/sdn_controller.go`
- Modify: `app/platform/dto/sdn_controller.go`
- Modify: `app/platform/service/i_sdn_controller.go`
- Modify: `app/platform/service/impl/sdn_controller.go`
- Modify: `app/platform/service/impl/sdn_controller_test.go`
- Modify: `app/platform/api/sdn_controller.go`
- Modify: `app/platform/router/sdn_controller.go`
- Modify: `app/platform/api/sdn_controller_test.go`
- Modify: `app/platform/router/sdn_controller_test.go`
- Modify: `initialize/mysql.go`

### Task W9.1: Add Alarm Model And DTOs

- [ ] **Step 1: Write model/DTO compile tests**

Add a test in `app/platform/service/impl/sdn_controller_test.go`:

```go
func TestSDNAlarmModelAndDTOFields(t *testing.T) {
	row := platformModel.SDNAlarm{
		ControllerID:    "ctrl-1",
		Provider:        "aci",
		AlarmKey:        "aci:uni/fabric/fault-F1",
		ProviderAlarmID: "F1",
		Severity:        "critical",
		Status:          "open",
		ResourceName:    "leaf-101",
		Code:            "F1",
		Title:           "Leaf down",
		Message:         "uplink down",
	}
	if row.TableName() != "platform_sdn_alarm" {
		t.Fatalf("unexpected table name %q", row.TableName())
	}
	resp := dto.SDNAlarmHistoryResp{Total: 1, Alarms: []dto.SDNAlarmRecord{{ID: "alarm-1"}}}
	if resp.Total != 1 || len(resp.Alarms) != 1 {
		t.Fatalf("unexpected resp %#v", resp)
	}
}
```

- [ ] **Step 2: Run the test and confirm RED**

Run:

```bash
go test ./app/platform/service/impl -run TestSDNAlarmModelAndDTOFields -count=1
```

Expected: fail because `platformModel.SDNAlarm` and `dto.SDNAlarmHistoryResp` do not exist.

- [ ] **Step 3: Add model and DTOs**

In `app/platform/platform_model/sdn_controller.go`, add:

```go
type SDNAlarm struct {
	BaseModel
	TenantCode      string     `json:"tenant_code" gorm:"size:128;index:idx_sdn_alarm_tenant_controller_status"`
	ControllerID    string     `json:"controller_id" gorm:"size:64;not null;index:idx_sdn_alarm_tenant_controller_status"`
	Provider        string     `json:"provider" gorm:"size:32;not null"`
	AlarmKey        string     `json:"alarm_key" gorm:"size:512;not null;index:idx_sdn_alarm_key,unique"`
	ProviderAlarmID string     `json:"provider_alarm_id" gorm:"size:256"`
	Severity        string     `json:"severity" gorm:"size:32;index"`
	Status          string     `json:"status" gorm:"size:32;index:idx_sdn_alarm_tenant_controller_status"`
	ResourceType    string     `json:"resource_type" gorm:"size:64"`
	ResourceName    string     `json:"resource_name" gorm:"size:512"`
	ResourceDN      string     `json:"resource_dn" gorm:"size:1024"`
	Code            string     `json:"code" gorm:"size:128"`
	Title           string     `json:"title" gorm:"size:512"`
	Message         string     `json:"message" gorm:"type:longtext"`
	TagsJSON        string     `json:"tags_json" gorm:"type:longtext"`
	AttributesJSON  string     `json:"attributes_json" gorm:"type:longtext"`
	RawJSON         string     `json:"raw_json" gorm:"type:longtext"`
	FirstSeenAt     time.Time  `json:"first_seen_at"`
	LastSeenAt      time.Time  `json:"last_seen_at"`
	ClearedAt       *time.Time `json:"cleared_at"`
	AcknowledgedAt  *time.Time `json:"acknowledged_at"`
}

func (SDNAlarm) TableName() string { return "platform_sdn_alarm" }
func (s *SDNAlarm) SetTenantCode(code string) { s.TenantCode = code }
```

In `app/platform/dto/sdn_controller.go`, add:

```go
type SDNAlarmHistoryQuery struct {
	Page         int    `form:"page"`
	PageSize     int    `form:"page_size"`
	Severity     string `form:"severity"`
	Status       string `form:"status"`
	ResourceType string `form:"resource_type"`
	Keyword      string `form:"keyword"`
}

type SDNAlarmHistoryResp struct {
	Total      int64            `json:"total"`
	Alarms     []SDNAlarmRecord `json:"alarms"`
	Page       int              `json:"page"`
	PageSize   int              `json:"page_size"`
	Refreshed  bool             `json:"refreshed,omitempty"`
	RefreshedAt *time.Time      `json:"refreshed_at,omitempty"`
}
```

Add `SDNAlarm{}` to `initialize/mysql.go` AutoMigrate near other SDN models.

- [ ] **Step 4: Run GREEN**

Run:

```bash
go test ./app/platform/service/impl -run TestSDNAlarmModelAndDTOFields -count=1
```

Expected: pass.

### Task W9.2: Persist Refresh Results

- [ ] **Step 1: Write failing refresh upsert test**

Add to `app/platform/service/impl/sdn_controller_test.go`:

```go
func TestSDNAlarmRefreshPersistsAndClearsMissingAlarms(t *testing.T) {
	svc, db, server := newTestSDNControllerStoreWithAlarmServer(t)
	defer server.Close()
	ctx := platformTenant.WithCode(context.Background(), "tenant-a")
	ctrl := seedTestSDNController(t, ctx, db, server.URL)

	first, err := svc.RefreshAlarms(ctx, ctrl.ID)
	if err != nil {
		t.Fatalf("RefreshAlarms first: %v", err)
	}
	if first.Total != 1 || first.Alarms[0].Status != dto.SDNAlarmStatusOpen {
		t.Fatalf("unexpected first refresh %#v", first)
	}

	server.SetAlarmPayload(`{"success":true,"data":{"alarms":[]}}`)
	second, err := svc.RefreshAlarms(ctx, ctrl.ID)
	if err != nil {
		t.Fatalf("RefreshAlarms second: %v", err)
	}
	if second.Total != 1 || second.Alarms[0].Status != dto.SDNAlarmStatusCleared {
		t.Fatalf("expected cleared alarm after missing refresh, got %#v", second)
	}
}
```

Provide local test helpers in the same file:

```go
type mutableAlarmServer struct {
	*httptest.Server
	mu      sync.Mutex
	payload string
}

func (s *mutableAlarmServer) SetAlarmPayload(payload string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.payload = payload
}
```

Reuse existing SDN controller test DB setup patterns. Seed a controller and fake secret like existing CtrlHub tests.

- [ ] **Step 2: Run RED**

Run:

```bash
go test ./app/platform/service/impl -run TestSDNAlarmRefreshPersistsAndClearsMissingAlarms -count=1
```

Expected: fail because `RefreshAlarms` does not exist.

- [ ] **Step 3: Add service interface and implementation**

In `app/platform/service/i_sdn_controller.go`, add:

```go
RefreshAlarms(ctx context.Context, id string) (*dto.SDNAlarmHistoryResp, error)
ListPersistedAlarms(ctx context.Context, id string, req dto.SDNAlarmHistoryQuery) (*dto.SDNAlarmHistoryResp, error)
GetPersistedAlarm(ctx context.Context, controllerID string, alarmID string) (*dto.SDNAlarmRecord, error)
```

In `app/platform/service/impl/sdn_controller.go`, implement:

```go
func (s *SDNControllerStore) RefreshAlarms(ctx context.Context, id string) (*dto.SDNAlarmHistoryResp, error) {
	current, err := s.ListAlarms(ctx, id)
	if err != nil {
		return nil, err
	}
	row, err := s.findController(ctx, id)
	if err != nil {
		return nil, err
	}
	now := time.Now()
	seen := map[string]bool{}
	for _, alarm := range current.Alarms {
		key := stableSDNAlarmKey(row.ID, &alarm)
		seen[key] = true
		if err := s.upsertSDNAlarm(ctx, row, &alarm, key, now); err != nil {
			return nil, err
		}
	}
	if err := s.clearMissingSDNAlarms(ctx, row.ID, seen, now); err != nil {
		return nil, err
	}
	resp, err := s.ListPersistedAlarms(ctx, id, dto.SDNAlarmHistoryQuery{Status: "all", Page: 1, PageSize: 100})
	if err != nil {
		return nil, err
	}
	resp.Refreshed = true
	resp.RefreshedAt = &now
	return resp, nil
}
```

Use `controllerDB(ctx)` or a small `alarmDB(ctx)` helper based on `platformTenant.ScopeDB`.

Stable key:

```go
func stableSDNAlarmKey(controllerID string, alarm *dto.SDNAlarmRecord) string {
	return strings.Join([]string{
		controllerID,
		firstNonEmpty(alarm.ID, alarm.DN, alarm.Code, alarm.ResourceName, alarm.Title),
	}, "|")
}
```

Persist only sanitized normalized fields.

- [ ] **Step 4: Run GREEN**

Run:

```bash
go test ./app/platform/service/impl -run TestSDNAlarmRefreshPersistsAndClearsMissingAlarms -count=1
```

Expected: pass.

### Task W9.3: Add Alarm History API And Routes

- [ ] **Step 1: Write failing API/router tests**

In `app/platform/api/sdn_controller_test.go`, add tests for:

```go
func TestSDNControllerAPIRefreshAlarmsCallsService(t *testing.T) { /* POST :id/alarms/refresh */ }
func TestSDNControllerAPIListPersistedAlarmsParsesFilters(t *testing.T) { /* GET :id/alarms */ }
```

In `app/platform/router/sdn_controller_test.go`, add route assertions for:

```go
POST /api/v1/sdn/controllers/ctrl-a/alarms/refresh
GET /api/v1/sdn/controllers/ctrl-a/alarms?status=all
GET /api/v1/sdn/controllers/ctrl-a/alarms/alarm-1
```

- [ ] **Step 2: Run RED**

Run:

```bash
go test ./app/platform/api ./app/platform/router -run 'TestSDNController.*Alarm' -count=1
```

Expected: fail because handlers/routes do not exist.

- [ ] **Step 3: Implement handlers and routes**

In `app/platform/api/sdn_controller.go`, add:

```go
func (a *SDNControllerAPI) RefreshControllerAlarms(ctx *gin.Context) {
	resp, err := a.SDNControllerStore.RefreshAlarms(ctx.Request.Context(), ctx.Param("id"))
	if err != nil {
		response.FailWithMsg(err.Error(), ctx)
		return
	}
	response.OkWithData(resp, ctx)
}

func (a *SDNControllerAPI) ListControllerAlarmHistory(ctx *gin.Context) {
	req := dto.SDNAlarmHistoryQuery{}
	_ = ctx.ShouldBindQuery(&req)
	resp, err := a.SDNControllerStore.ListPersistedAlarms(ctx.Request.Context(), ctx.Param("id"), req)
	if err != nil {
		response.FailWithMsg(err.Error(), ctx)
		return
	}
	response.OkWithData(resp, ctx)
}
```

In `app/platform/router/sdn_controller.go`, register specific routes before
generic alarm detail if needed:

```go
g.POST(":id/alarms/refresh", api.RefreshControllerAlarms)
g.GET(":id/alarms", api.ListControllerAlarmHistory)
g.GET(":id/alarms/:alarm_id", api.GetControllerAlarm)
```

Keep existing `POST :id/alarms` for compatibility.

- [ ] **Step 4: Run GREEN**

Run:

```bash
go test ./app/platform/api ./app/platform/router -run 'TestSDNController.*Alarm' -count=1
```

Expected: pass.

- [ ] **Step 5: Commit W9**

```bash
git add app/platform/platform_model/sdn_controller.go app/platform/dto/sdn_controller.go app/platform/service/i_sdn_controller.go app/platform/service/impl/sdn_controller.go app/platform/service/impl/sdn_controller_test.go app/platform/api/sdn_controller.go app/platform/api/sdn_controller_test.go app/platform/router/sdn_controller.go app/platform/router/sdn_controller_test.go initialize/mysql.go
git commit -m "feat: persist sdn alarm history"
```

## Workstream W10: OneOPS Config Plan Approval And Rollback Dry-Run

**Repo:** `/Users/huangliang/project/OneOPS-ALL/OneOPS`

**Files:**
- Modify: `app/platform/platform_model/sdn_config_plan.go`
- Modify: `app/platform/dto/sdn_config_plan.go`
- Modify: `app/platform/service/i_sdn_config_plan.go`
- Modify: `app/platform/service/impl/sdn_config_plan.go`
- Modify: `app/platform/service/impl/sdn_config_plan_test.go`
- Modify: `app/platform/api/sdn_config_plan.go`
- Modify: `app/platform/api/sdn_config_plan_test.go`
- Modify: `app/platform/router/sdn_config_plan.go`
- Modify: `app/platform/router/sdn_config_plan_test.go`
- Modify: `initialize/mysql.go`

### Task W10.1: Add Approval And Rollback Fields

- [ ] **Step 1: Write failing model/DTO test**

Add to `app/platform/service/impl/sdn_config_plan_test.go`:

```go
func TestSDNConfigPlanApprovalAndRollbackFieldsCompile(t *testing.T) {
	row := platformModel.SDNConfigPlan{
		Status:          string(dto.SDNConfigPlanStatusApproved),
		ApprovedBy:      "operator-a",
		ApprovalComment: "checked",
		RollbackPlanJSON: `{"steps":[]}`,
		RollbackSummary: "0 rollback steps",
	}
	if row.ApprovedBy != "operator-a" || row.RollbackSummary == "" {
		t.Fatalf("unexpected row %#v", row)
	}
	req := dto.SDNConfigPlanApproveReq{Comment: "approved"}
	if req.Comment != "approved" {
		t.Fatalf("unexpected approve req %#v", req)
	}
}
```

- [ ] **Step 2: Run RED**

```bash
go test ./app/platform/service/impl -run TestSDNConfigPlanApprovalAndRollbackFieldsCompile -count=1
```

Expected: fail because fields/types do not exist.

- [ ] **Step 3: Add fields and DTOs**

In `app/platform/platform_model/sdn_config_plan.go`, add:

```go
ApprovedBy       string     `json:"approved_by" gorm:"size:128"`
ApprovedAt       *time.Time `json:"approved_at"`
ApprovalComment  string     `json:"approval_comment" gorm:"type:longtext"`
RollbackPlanJSON string     `json:"rollback_plan_json" gorm:"type:longtext"`
RollbackSummary  string     `json:"rollback_summary" gorm:"type:longtext"`
```

In `app/platform/dto/sdn_config_plan.go`, add:

```go
type SDNConfigPlanApproveReq struct {
	Comment string `json:"comment"`
}

type SDNConfigPlanRollbackDryRunResp struct {
	Plan               *SDNConfigPlanResp   `json:"plan"`
	RollbackPlan       json.RawMessage      `json:"rollback_plan"`
	RollbackSummary    string               `json:"rollback_summary"`
	LiveApplyPerformed bool                 `json:"live_apply_performed"`
}
```

Extend `SDNConfigPlanResp` with approval and rollback summary fields.

- [ ] **Step 4: Run GREEN**

```bash
go test ./app/platform/service/impl -run TestSDNConfigPlanApprovalAndRollbackFieldsCompile -count=1
```

Expected: pass.

### Task W10.2: Approve And Rollback Service

- [ ] **Step 1: Write failing service tests**

Add tests:

```go
func TestSDNConfigPlanApproveRequiresDryRunReady(t *testing.T) { /* draft -> 409, dry_run_ready -> approved */ }
func TestSDNConfigPlanRollbackDryRunReturnsStoredPlanWithoutApply(t *testing.T) { /* no live execution */ }
```

Use `platformTenant.WithCode(context.Background(), "tenant-a")` and existing helper `newTestSDNConfigPlanService`.

- [ ] **Step 2: Run RED**

```bash
go test ./app/platform/service/impl -run 'TestSDNConfigPlanApprove|TestSDNConfigPlanRollback' -count=1
```

Expected: fail because service methods do not exist.

- [ ] **Step 3: Implement methods**

In `app/platform/service/i_sdn_config_plan.go`:

```go
Approve(ctx context.Context, id string, req *dto.SDNConfigPlanApproveReq) (*dto.SDNConfigPlanResp, error)
RollbackDryRun(ctx context.Context, id string) (*dto.SDNConfigPlanRollbackDryRunResp, error)
```

In `app/platform/service/impl/sdn_config_plan.go`:

```go
func (s *SDNConfigPlanService) Approve(ctx context.Context, id string, req *dto.SDNConfigPlanApproveReq) (*dto.SDNConfigPlanResp, error) {
	plan, err := s.getPlan(ctx, id)
	if err != nil { return nil, err }
	if plan.Status != string(dto.SDNConfigPlanStatusDryRunReady) {
		return nil, newSDNConfigPlanClientError(http.StatusConflict, "只有 dry_run_ready 的配置计划可以审批", nil)
	}
	now := time.Now()
	approver := sdnConfigPlanApprover(ctx)
	updates := map[string]any{
		"status": string(dto.SDNConfigPlanStatusApproved),
		"approved_by": approver,
		"approved_at": &now,
		"approval_comment": strings.TrimSpace(req.Comment),
	}
	if plan.RollbackPlanJSON == "" {
		updates["rollback_plan_json"] = buildRollbackPlanScaffold(plan)
		updates["rollback_summary"] = "rollback plan scaffold generated"
	}
	if err := s.db(ctx).Table(plan.TableName()).Where("id = ?", plan.ID).Updates(updates).Error; err != nil {
		return nil, err
	}
	return s.getPlanResponse(ctx, plan.ID)
}
```

Use account from `security_utils.CtxAccount`, fallback to `system`.

`RollbackDryRun` returns stored rollback JSON and `LiveApplyPerformed:false`.

- [ ] **Step 4: Run GREEN**

```bash
go test ./app/platform/service/impl -run 'TestSDNConfigPlanApprove|TestSDNConfigPlanRollback' -count=1
```

Expected: pass.

### Task W10.3: Add API And Routes

- [ ] **Step 1: Write failing API/router tests**

Add tests for:

```go
POST /api/v1/sdn/config-plans/:id/approve
POST /api/v1/sdn/config-plans/:id/rollback/dry-run
```

Assert service receives plan ID and approve comment.

- [ ] **Step 2: Run RED**

```bash
go test ./app/platform/api ./app/platform/router -run 'TestSDNConfigPlan.*Approve|TestSDNConfigPlan.*Rollback' -count=1
```

Expected: fail because routes/handlers do not exist.

- [ ] **Step 3: Implement handlers/routes**

In `app/platform/api/sdn_config_plan.go`, add `Approve` and `RollbackDryRun`.

In `app/platform/router/sdn_config_plan.go`, add:

```go
g.POST(":id/approve", api.Approve)
g.POST(":id/rollback/dry-run", api.RollbackDryRun)
```

- [ ] **Step 4: Run GREEN and commit W10**

```bash
go test ./app/platform/service/impl ./app/platform/api ./app/platform/router -run 'TestSDNConfigPlan' -count=1
git add app/platform/platform_model/sdn_config_plan.go app/platform/dto/sdn_config_plan.go app/platform/service/i_sdn_config_plan.go app/platform/service/impl/sdn_config_plan.go app/platform/service/impl/sdn_config_plan_test.go app/platform/api/sdn_config_plan.go app/platform/api/sdn_config_plan_test.go app/platform/router/sdn_config_plan.go app/platform/router/sdn_config_plan_test.go initialize/mysql.go
git commit -m "feat: add sdn config plan approval"
```

## Workstream W11: OneOPS-UI Alarm History And Approval UX

**Repo:** `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI`

**Files:**
- Modify: `src/api/platform/sdn-controller.ts`
- Modify: `src/typings/platform/sdn-controller.ts`
- Modify: `src/views/device/SdnControllerManagement.vue`
- Modify: `scripts/sdn-resource-workbench-smoke.ts`

### Task W11.1: Add API Types And Wrappers

- [ ] **Step 1: Write failing smoke source assertions**

In `scripts/sdn-resource-workbench-smoke.ts`, add assertions for:

```ts
'sdnControllerAlarmRefreshReq'
'sdnControllerAlarmHistoryReq'
'sdnConfigPlanApproveReq'
'sdnConfigPlanRollbackDryRunReq'
'export interface AlarmHistoryResp'
'export interface ConfigPlanApproveReq'
'RollbackDryRun'
```

- [ ] **Step 2: Run RED**

```bash
npm run smoke:sdn-resource-workbench
```

Expected: fail on missing wrappers/types.

- [ ] **Step 3: Add wrappers and types**

In `src/typings/platform/sdn-controller.ts`, add:

```ts
export interface AlarmHistoryQuery extends SDNPageQuery {
  severity?: AlarmSeverity | 'all';
  status?: AlarmStatus | 'all';
  resource_type?: SDNResourceType;
  keyword?: string;
}

export interface AlarmHistoryResp extends AlarmListResp {
  refreshed?: boolean;
  refreshed_at?: string;
}

export interface ConfigPlanApproveReq {
  comment?: string;
}

export interface ConfigPlanRollbackDryRunResp {
  plan?: ConfigPlan;
  rollback_plan?: Record<string, unknown> | null;
  rollback_summary?: string;
  live_apply_performed?: boolean;
}
```

In `src/api/platform/sdn-controller.ts`, add:

```ts
export const sdnControllerAlarmRefreshReq = async (id: string) => request<AlarmHistoryResp>({
  url: `/sdn/controllers/${encodeURIComponent(id)}/alarms/refresh`,
  method: HTTP_POST,
  timeout: SDN_CONTROLLER_OPERATION_TIMEOUT_MS,
});

export const sdnControllerAlarmHistoryReq = async (id: string, params: AlarmHistoryQuery) => request<AlarmHistoryResp>({
  url: `/sdn/controllers/${encodeURIComponent(id)}/alarms`,
  method: HTTP_GET,
  params,
  silentSuccess: true,
});
```

Add approve and rollback wrappers.

- [ ] **Step 4: Run GREEN**

```bash
npm run smoke:sdn-resource-workbench
```

Expected: pass source assertions or fail later on missing UI behavior.

### Task W11.2: Extend Existing Alarm Drawer

- [ ] **Step 1: Write failing smoke interaction**

In the smoke, change alarm drawer expectations to:

```ts
await clickButton(runtimeMount.rootNode, '告警');
assert(runtimeState?.alarmHistoryCalls.length === 1, 'alarm history should load on drawer open');
await clickButton(runtimeMount.rootNode, '刷新告警');
assert(runtimeState?.alarmRefreshCalls.length === 1, 'alarm refresh should call persisted refresh API');
```

- [ ] **Step 2: Run RED**

```bash
npm run smoke:sdn-resource-workbench
```

Expected: fail because the UI still calls only current alarm API.

- [ ] **Step 3: Implement UI**

In `SdnControllerManagement.vue`:

- Use persisted history API for drawer load.
- Use refresh API for explicit refresh button.
- Keep compatibility normalizer for `{alarms:[]}`.
- Add severity/status/keyword fields in alarm drawer if not too large; otherwise add keyword/status first and severity as a select.

- [ ] **Step 4: Run GREEN**

```bash
npx prettier --write src/views/device/SdnControllerManagement.vue src/api/platform/sdn-controller.ts src/typings/platform/sdn-controller.ts scripts/sdn-resource-workbench-smoke.ts
npm run smoke:sdn-resource-workbench
```

Expected: pass.

### Task W11.3: Approval And Rollback Preview UX

- [ ] **Step 1: Write failing smoke interaction**

Smoke should:

```ts
await clickButton(runtimeMount.rootNode, 'Dry-run');
await clickButton(runtimeMount.rootNode, '审批');
assert(runtimeState?.configPlanApproveCalls.length === 1, 'approve request should be issued');
await clickButton(runtimeMount.rootNode, '回滚预览');
assert(runtimeState?.configPlanRollbackDryRunCalls.length === 1, 'rollback dry-run request should be issued');
```

- [ ] **Step 2: Run RED**

```bash
npm run smoke:sdn-resource-workbench
```

Expected: fail because approval/rollback buttons do not exist.

- [ ] **Step 3: Implement UI**

In config plan drawer:

- Show `审批` button only for `dry_run_ready`.
- Call `sdnConfigPlanApproveReq`.
- Store returned plan.
- Show approval metadata.
- Show `回滚预览` button when a plan exists and has rollback summary or is approved.
- Call `sdnConfigPlanRollbackDryRunReq`.
- Render rollback summary/result in the drawer.
- Keep `执行（未启用）` disabled or guarded as today.

- [ ] **Step 4: Run GREEN and commit W11**

```bash
npx prettier --check src/views/device/SdnControllerManagement.vue src/api/platform/sdn-controller.ts src/typings/platform/sdn-controller.ts scripts/sdn-resource-workbench-smoke.ts package.json
npm run smoke:sdn-resource-workbench
git add src/views/device/SdnControllerManagement.vue src/api/platform/sdn-controller.ts src/typings/platform/sdn-controller.ts scripts/sdn-resource-workbench-smoke.ts
git commit -m "feat: add sdn alarm history and approval ui"
```

## Workstream W12: Contract Review And Final Verification

**Repos:** all three.

- [ ] Run OneOPS focused tests:

```bash
go test ./app/platform/service/impl ./app/platform/api ./app/platform/router -run 'TestSDNAlarm|TestSDNController.*Alarm|TestSDNConfigPlan' -count=1
go test ./app/platform/api ./app/platform/router ./app/platform/service/impl ./app/platform/dto ./app/platform/platform_model -count=1
go test ./cmd ./initialize -run TestDoesNotExist -count=1
```

- [ ] Run UI checks:

```bash
npx prettier --check src/views/device/SdnControllerManagement.vue src/api/platform/sdn-controller.ts src/typings/platform/sdn-controller.ts scripts/sdn-resource-workbench-smoke.ts package.json
npm run smoke:sdn-resource-workbench
```

- [ ] Run CtrlHub regression checks:

```bash
go test ./controller/pkg/sdn ./controller/pkg/sdn/aci ./controller/pkg/sdn/adapters ./controller/pkg/controller/api ./controller/cmd/controller -run 'Test.*Alarm|TestSDNAlarms|TestNewAlarmAdapter|TestDiagnostic|TestSDNDiagnose|^$' -count=1
```

- [ ] Review diffs and confirm:
  - No dashboard page added.
  - No OneOPS vendor-specific SDN client added.
  - Execute and rollback live apply remain disabled.
  - Sensitive values are redacted from errors and persisted summaries.

## Acceptance

- Alarm refresh persists current CtrlHub alarms.
- Alarm history can be queried with filters.
- Missing open alarms become cleared after refresh.
- Config plans can be approved only after `dry_run_ready`.
- Rollback dry-run returns stored rollback plan and never applies changes.
- UI exposes alarm history refresh, approval, and rollback preview in the existing SDN controller page.
- No monitoring dashboard is introduced.
