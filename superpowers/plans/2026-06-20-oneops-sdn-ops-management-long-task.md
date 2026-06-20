# OneOPS SDN Ops Management Long Task Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver SDN 运维管理 as one coordinated long task while allowing resource management, controller health, alarms, and configuration-plan scaffolding to move forward in parallel.

**Architecture:** OneOPS owns controller inventory, normalized resource projection, snapshot history, diff, health/alarm/config-plan APIs, UI, permissions, and audit. CtrlHub owns vendor-specific ACI/Huawei/H3C interaction, diagnostics, alarm collection, and configuration execution. OneOPS must only send vendor-neutral requests to CtrlHub and consume normalized responses.

**Tech Stack:** Go, GORM, MySQL, gorilla/mux-style OneOPS routing, Wire provider sets, Vue 3, TypeScript, Ant Design Vue, CtrlHub Go SDN adapters.

---

## Governing Foundation

This long task is constrained by:

- `docs/superpowers/specs/2026-06-20-oneops-sdn-ops-management-design.md`
- `docs/superpowers/specs/2026-06-20-oneops-sdn-controller-snapshot-mvp-design.md`
- `docs/superpowers/plans/2026-06-20-oneops-sdn-controller-snapshot-mvp.md`

Current completed baseline:

- OneOPS has SDN controller CRUD, test, sync, latest snapshot, and history APIs.
- OneOPS UI has `OneOPS-UI/src/views/device/SdnControllerManagement.vue`.
- CtrlHub has ACI and Huawei snapshot adapters under `ctrlhub/controller/pkg/sdn`.
- ACI live sync has succeeded through OneOPS -> CtrlHub -> APIC.

Non-negotiable boundary:

- OneOPS must not add ACI/Huawei/H3C API clients.
- OneOPS must not persist provider passwords in SDN controller config, resource projection, alarms, plans, or logs.
- Configuration apply must not be enabled before plan, approval, audit, and post-apply sync are in place.

## Operating Contract

Default execution rule:

- Continue within the active workstream when the next step is covered by this plan.
- Use subagents for independent workstreams.
- Keep commits scoped by repo and workstream.
- Do not revert unrelated dirty files in `OneOPS`, `OneOPS-UI`, `ctrlhub`, or `docs`.
- Report progress using the status block below.

Status block:

```text
【SDN长任务状态】
当前工作流：
- W<N>: <name>

本轮完成：
- <completed item>

验证：
- <verification command and result>

阻塞/风险：
- <blocking condition or "none">

下一步：
- <next planned step>
```

## Consent Gates

Stop and ask the user before continuing if any item below occurs:

- A change requires real production APIC/Huawei/H3C write access.
- A change would execute configuration apply against a live controller.
- A migration would rewrite or delete existing SDN snapshot/history records.
- CtrlHub needs a new third-party SDK dependency for a vendor adapter.
- OneOPS needs a new broad permission model instead of reusing existing device/platform permissions.
- A subagent proposes adding vendor-specific API logic in OneOPS.
- Live testing needs credentials not already provided in the current secure environment.
- A failing test outside the active SDN files requires touching unrelated modules.
- Existing dirty changes in the same file conflict with SDN changes and cannot be isolated by patching only SDN hunks.

Everything else can proceed by default.

## Parallel Workstreams

The long task runs as four parallel workstreams. W1 is the data foundation and should land first when a later workstream needs persisted resources. W2, W3, and W4 can advance with mocked contracts while W1 is finishing.

### W1: SDN Resource Projection And Snapshot Diff

Purpose:

- Turn normalized snapshot JSON into queryable OneOPS resources.
- Compute snapshot-to-snapshot diffs.

Primary repo:

- `/Users/huangliang/project/OneOPS-ALL/OneOPS`

Files:

- Modify `app/platform/platform_model/sdn_controller.go`
- Modify `app/platform/dto/sdn_controller.go`
- Modify `app/platform/service/i_sdn_controller.go`
- Modify `app/platform/service/impl/sdn_controller.go`
- Modify `app/platform/service/impl/sdn_controller_test.go`
- Modify `app/platform/api/sdn_controller.go`
- Modify `app/platform/router/sdn_controller.go`
- Modify `initialize/mysql.go`
- Modify `boot/provider/api.go`
- Modify `boot/provider/service_groups.go`
- Modify `cmd/wire_gen.go` only when necessary and only with SDN-related hunks.

Deliverables:

- `platform_sdn_resource` model and AutoMigrate registration.
- `platform_sdn_snapshot_diff` model and AutoMigrate registration.
- Resource projection on successful sync.
- Diff calculation against previous successful snapshot.
- Resource list/detail APIs.
- Snapshot diff APIs.

Task steps:

- [ ] **W1.1 Write projection and diff tests**

Add tests in `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/platform/service/impl/sdn_controller_test.go`:

```go
func TestSDNResourceProjectionExtractsQueryableFields(t *testing.T) {
	store := newTestSDNControllerStore(t)
	controller := seedSDNController(t, store, "aci")
	snapshot := sampleSDNSnapshot(map[string]any{
		"endpoints": []any{
			map[string]any{
				"id": "ep-1", "name": "00:11:22:33:44:55", "tenant": "TenantA",
				"dn": "uni/tn-TenantA/ap-App/epg-Web/cep-00:11:22:33:44:55",
				"provider_type": "fvCEp",
				"attributes": map[string]any{
					"ip": "10.1.1.10", "mac": "00:11:22:33:44:55",
					"network": "BD-Web", "switch": "leaf101", "port": "eth1/1",
				},
			},
		},
	})

	record := seedSuccessfulSDNSnapshot(t, store, controller.ID, snapshot)
	require.NoError(t, store.projectSnapshotResources(context.Background(), controller, record))

	resources, total, err := store.ListResources(context.Background(), controller.ID, dto.SDNResourceQuery{
		ResourceType: "endpoint",
		Keyword:      "10.1.1.10",
		Page:         1,
		PageSize:     20,
	})
	require.NoError(t, err)
	require.Equal(t, int64(1), total)
	require.Equal(t, "10.1.1.10", resources[0].IP)
	require.Equal(t, "00:11:22:33:44:55", resources[0].MAC)
	require.Equal(t, "leaf101", resources[0].SwitchName)
	require.Equal(t, "eth1/1", resources[0].PortName)
}

func TestSDNSnapshotDiffDetectsAddedRemovedAndChanged(t *testing.T) {
	store := newTestSDNControllerStore(t)
	controller := seedSDNController(t, store, "aci")
	before := seedProjectedResource(t, store, controller.ID, "snap-1", "network", "uni/tn-TenantA/BD-Web", map[string]any{"name": "BD-Web", "vrf": "VRF-A"})
	afterChanged := before
	afterChanged.SnapshotID = "snap-2"
	afterChanged.AttributesJSON = `{"name":"BD-Web","vrf":"VRF-B"}`
	afterAdded := seedProjectedResourceValue(controller.ID, "snap-2", "endpoint", "uni/tn-TenantA/epg-Web/cep-aa", map[string]any{"ip": "10.1.1.20"})

	diffs, err := store.computeSnapshotDiff(context.Background(), controller.ID, "snap-1", "snap-2", []platform_model.SDNResource{afterChanged, afterAdded})
	require.NoError(t, err)
	require.Len(t, diffs, 2)
	require.Contains(t, diffTypes(diffs), "changed")
	require.Contains(t, diffTypes(diffs), "added")
}
```

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/platform/service/impl -run 'TestSDNResourceProjectionExtractsQueryableFields|TestSDNSnapshotDiffDetectsAddedRemovedAndChanged' -count=1
```

Expected before implementation: fail because projection/diff helpers do not exist.

- [ ] **W1.2 Add resource and diff models**

Add to `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/platform/platform_model/sdn_controller.go`:

```go
type SDNResource struct {
	commonModel.Common
	TenantScoped
	ControllerID   string    `gorm:"type:varchar(36);index;not null;comment:控制器ID"`
	SnapshotID     string    `gorm:"type:varchar(36);index;not null;comment:快照ID"`
	Provider       string    `gorm:"type:varchar(32);index;not null;comment:SDN provider"`
	ResourceType   string    `gorm:"type:varchar(32);index;not null;comment:资源类型"`
	ResourceID     string    `gorm:"type:varchar(256);index;comment:厂商归一化ID"`
	Name           string    `gorm:"type:varchar(512);index;comment:资源名称"`
	TenantName     string    `gorm:"type:varchar(256);index;comment:SDN租户"`
	VRFName        string    `gorm:"type:varchar(256);index;comment:VRF"`
	NetworkName    string    `gorm:"type:varchar(256);index;comment:网络"`
	DN             string    `gorm:"type:varchar(1024);index;comment:厂商DN"`
	IP             string    `gorm:"type:varchar(128);index;comment:IP"`
	MAC            string    `gorm:"type:varchar(128);index;comment:MAC"`
	SwitchName     string    `gorm:"type:varchar(256);index;comment:交换机"`
	PortName       string    `gorm:"type:varchar(256);index;comment:端口"`
	ProviderType   string    `gorm:"type:varchar(128);comment:厂商对象类型"`
	AttributesJSON string    `gorm:"type:text;comment:归一化扩展属性"`
	CollectedAt    time.Time `gorm:"index;comment:采集时间"`
}

func (*SDNResource) TableName() string {
	return "platform_sdn_resource"
}

type SDNSnapshotDiff struct {
	commonModel.Common
	TenantScoped
	ControllerID   string `gorm:"type:varchar(36);index;not null;comment:控制器ID"`
	FromSnapshotID string `gorm:"type:varchar(36);index;not null;comment:源快照ID"`
	ToSnapshotID   string `gorm:"type:varchar(36);index;not null;comment:目标快照ID"`
	ResourceType   string `gorm:"type:varchar(32);index;not null;comment:资源类型"`
	ChangeType     string `gorm:"type:varchar(32);index;not null;comment:变化类型"`
	ResourceKey    string `gorm:"type:varchar(1024);index;not null;comment:稳定比较键"`
	BeforeJSON     string `gorm:"type:longtext;comment:变化前"`
	AfterJSON      string `gorm:"type:longtext;comment:变化后"`
	SummaryJSON    string `gorm:"type:text;comment:差异摘要"`
}

func (*SDNSnapshotDiff) TableName() string {
	return "platform_sdn_snapshot_diff"
}
```

- [ ] **W1.3 Add DTOs and service methods**

Add DTOs to `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/platform/dto/sdn_controller.go`:

```go
type SDNResourceQuery struct {
	ResourceType string `json:"resource_type" form:"resource_type"`
	Keyword      string `json:"keyword" form:"keyword"`
	TenantName   string `json:"tenant_name" form:"tenant_name"`
	VRFName      string `json:"vrf_name" form:"vrf_name"`
	NetworkName  string `json:"network_name" form:"network_name"`
	Page         int    `json:"page" form:"page"`
	PageSize     int    `json:"page_size" form:"page_size"`
}

type SDNResourceResp struct {
	ID             string         `json:"id"`
	ControllerID   string         `json:"controller_id"`
	SnapshotID     string         `json:"snapshot_id"`
	Provider       SDNProvider    `json:"provider"`
	ResourceType   string         `json:"resource_type"`
	ResourceID     string         `json:"resource_id"`
	Name           string         `json:"name"`
	TenantName     string         `json:"tenant_name"`
	VRFName        string         `json:"vrf_name"`
	NetworkName    string         `json:"network_name"`
	DN             string         `json:"dn"`
	IP             string         `json:"ip"`
	MAC            string         `json:"mac"`
	SwitchName     string         `json:"switch_name"`
	PortName       string         `json:"port_name"`
	ProviderType   string         `json:"provider_type"`
	Attributes     map[string]any `json:"attributes"`
	CollectedAt    time.Time      `json:"collected_at"`
}

type SDNSnapshotDiffQuery struct {
	ResourceType string `json:"resource_type" form:"resource_type"`
	ChangeType   string `json:"change_type" form:"change_type"`
	Keyword      string `json:"keyword" form:"keyword"`
	Page         int    `json:"page" form:"page"`
	PageSize     int    `json:"page_size" form:"page_size"`
}

type SDNSnapshotDiffResp struct {
	ID             string         `json:"id"`
	ControllerID   string         `json:"controller_id"`
	FromSnapshotID string         `json:"from_snapshot_id"`
	ToSnapshotID   string         `json:"to_snapshot_id"`
	ResourceType   string         `json:"resource_type"`
	ChangeType     string         `json:"change_type"`
	ResourceKey    string         `json:"resource_key"`
	Before         map[string]any `json:"before"`
	After          map[string]any `json:"after"`
	Summary        map[string]any `json:"summary"`
}
```

Extend `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/platform/service/i_sdn_controller.go` with:

```go
ListResources(ctx context.Context, controllerID string, query dto.SDNResourceQuery) ([]dto.SDNResourceResp, int64, error)
GetResource(ctx context.Context, controllerID string, resourceID string) (*dto.SDNResourceResp, error)
ListSnapshotDiffs(ctx context.Context, controllerID string, snapshotID string, query dto.SDNSnapshotDiffQuery) ([]dto.SDNSnapshotDiffResp, int64, error)
```

- [ ] **W1.4 Implement projection, query, and diff**

Implement in `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/platform/service/impl/sdn_controller.go`:

```go
func sdnResourceKey(resourceType, id, dn, name string) string {
	if strings.TrimSpace(dn) != "" {
		return strings.TrimSpace(dn)
	}
	if strings.TrimSpace(id) != "" {
		return strings.TrimSpace(resourceType) + ":" + strings.TrimSpace(id)
	}
	return strings.TrimSpace(resourceType) + ":" + strings.TrimSpace(name)
}
```

Projection rules:

- endpoint attributes map `ip`, `mac`, `network`, `switch`, `port` to first-class columns.
- subnet attributes map `cidr` or `ip` to `IP`.
- all resource types preserve `attributes_json`.
- resource rows for the same `controller_id + snapshot_id` are replaced atomically inside the sync transaction boundary available in the current store pattern.

Diff rules:

- Compare previous and current projected resources by `resource_type + resource_key`.
- `added` when key exists only in current.
- `removed` when key exists only in previous.
- `changed` when normalized comparable JSON differs.
- Exclude volatile fields from comparison: OneOPS internal ID, created/updated timestamps, snapshot ID, collected time.

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/platform/service/impl -run 'TestSDNResourceProjectionExtractsQueryableFields|TestSDNSnapshotDiffDetectsAddedRemovedAndChanged' -count=1
```

Expected after implementation: pass.

- [ ] **W1.5 Add API and router coverage**

Add handlers to `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/platform/api/sdn_controller.go`:

```go
func (a *SDNControllerAPI) ListResources(c *gin.Context) {}
func (a *SDNControllerAPI) GetResource(c *gin.Context) {}
func (a *SDNControllerAPI) ListSnapshotDiffs(c *gin.Context) {}
```

Register routes in `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/platform/router/sdn_controller.go`:

```go
sdnGroup.GET("/controllers/:id/resources", sdnAPI.ListResources)
sdnGroup.GET("/controllers/:id/resources/:resource_id", sdnAPI.GetResource)
sdnGroup.GET("/controllers/:id/snapshots/:snapshot_id/diffs", sdnAPI.ListSnapshotDiffs)
```

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/platform/api ./app/platform/router ./app/platform/service/impl -run 'TestSDN|TestSdn|TestSDNResource|TestSDNSnapshotDiff' -count=1
```

Expected: pass.

Exit criteria:

- Resource projection is persisted after successful sync.
- Resource list/detail APIs return paged data.
- Diff APIs return added/removed/changed records.
- Existing controller CRUD/test/sync tests still pass.

### W2: OneOPS UI Resource, History, And Diff Workbench

Purpose:

- Make synchronized SDN data browsable and useful to operators.

Primary repo:

- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI`

Files:

- Modify `src/typings/platform/sdn-controller.ts`
- Modify `src/api/platform/sdn-controller.ts`
- Modify `src/views/device/SdnControllerManagement.vue`
- Modify or create smoke script under `scripts/` for SDN resources.

Deliverables:

- Resource tabs in the latest snapshot drawer or detail view.
- Searchable paged resource table.
- Snapshot history drawer.
- Diff view with added/removed/changed filters.

Task steps:

- [ ] **W2.1 Add frontend types and APIs**

Add to `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/typings/platform/sdn-controller.ts`:

```ts
export interface SDNResourceQuery {
  resource_type?: string;
  keyword?: string;
  tenant_name?: string;
  vrf_name?: string;
  network_name?: string;
  page?: number;
  page_size?: number;
}

export interface SDNResource {
  id: string;
  controller_id: string;
  snapshot_id: string;
  provider: SDNProvider;
  resource_type: string;
  resource_id: string;
  name: string;
  tenant_name?: string;
  vrf_name?: string;
  network_name?: string;
  dn?: string;
  ip?: string;
  mac?: string;
  switch_name?: string;
  port_name?: string;
  provider_type?: string;
  attributes?: Record<string, unknown>;
  collected_at?: string;
}

export interface SDNSnapshotDiffQuery {
  resource_type?: string;
  change_type?: 'added' | 'removed' | 'changed';
  keyword?: string;
  page?: number;
  page_size?: number;
}

export interface SDNSnapshotDiff {
  id: string;
  controller_id: string;
  from_snapshot_id: string;
  to_snapshot_id: string;
  resource_type: string;
  change_type: 'added' | 'removed' | 'changed';
  resource_key: string;
  before?: Record<string, unknown>;
  after?: Record<string, unknown>;
  summary?: Record<string, unknown>;
}
```

Add to `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/api/platform/sdn-controller.ts`:

```ts
export const sdnControllerResourceListReq = async (id: string, params: SDNResourceQuery) => request.get({
  url: `/sdn/controllers/${id}/resources`,
  params,
});

export const sdnControllerResourceGetReq = async (id: string, resourceId: string) => request.get({
  url: `/sdn/controllers/${id}/resources/${resourceId}`,
});

export const sdnControllerSnapshotDiffListReq = async (
  id: string,
  snapshotId: string,
  params: SDNSnapshotDiffQuery,
) => request.get({
  url: `/sdn/controllers/${id}/snapshots/${snapshotId}/diffs`,
  params,
});
```

- [ ] **W2.2 Extend resource drawer**

In `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/SdnControllerManagement.vue`:

- Keep the existing summary.
- Add tabs for `tenant`, `vrf`, `network`, `subnet`, `segment`, `endpoint`, `switch`, `port`, `contract`, `filter`.
- Add compact resource-specific columns:
  - endpoint: name, ip, mac, tenant_name, network_name, switch_name, port_name, dn.
  - subnet: name, ip, tenant_name, vrf_name, network_name, dn.
  - default: name, tenant_name, provider_type, dn.
- Add keyword search with no automatic query until user clicks search or presses Enter.

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npx prettier --check src/views/device/SdnControllerManagement.vue src/api/platform/sdn-controller.ts src/typings/platform/sdn-controller.ts
```

Expected: pass.

- [ ] **W2.3 Add history and diff UI**

In the same Vue file:

- Add a “同步历史” action next to “最近快照”.
- The history drawer calls the existing snapshot history API.
- Successful history rows expose “查看差异”.
- Diff view calls `sdnControllerSnapshotDiffListReq`.
- Show tags for added, removed, changed.
- For changed rows, show before/after key values from `summary`.

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npx prettier --check src/views/device/SdnControllerManagement.vue
```

Expected: pass.

- [ ] **W2.4 Add UI smoke coverage**

Create `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/scripts/sdn-resource-workbench-smoke.ts` with a route-level smoke that:

- opens the SDN controller page,
- verifies the controller list renders,
- opens latest snapshot if available,
- verifies resource tabs exist,
- opens history drawer,
- handles empty data without throwing.

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npx prettier --check scripts/sdn-resource-workbench-smoke.ts
```

Expected: pass.

Exit criteria:

- Operator can browse ACI resources by type.
- Operator can search endpoint/network/subnet data.
- Operator can inspect history and diffs.
- UI remains usable when resource APIs return empty lists.

### W3: CtrlHub Diagnostics, Health, And Alarm Contracts

Purpose:

- Advance stage 2 and stage 3 in parallel without blocking on OneOPS UI.

Primary repo:

- `/Users/huangliang/project/OneOPS-ALL/ctrlhub`

Files:

- Modify `controller/pkg/sdn/model.go`
- Create `controller/pkg/sdn/diagnostics.go`
- Create `controller/pkg/sdn/diagnostics_test.go`
- Modify `controller/pkg/sdn/aci/adapter.go`
- Modify `controller/pkg/sdn/huawei/adapter.go`
- Modify `controller/pkg/controller/api/sdn.go`
- Add tests under `controller/pkg/controller/api`.

Deliverables:

- Vendor-neutral diagnostic model.
- CtrlHub API for diagnostics.
- Vendor-neutral alarm model.
- CtrlHub API contract for alarms with ACI first implementation or fixture-backed contract test.

Task steps:

- [ ] **W3.1 Add diagnostic model and core tests**

Add to `/Users/huangliang/project/OneOPS-ALL/ctrlhub/controller/pkg/sdn/model.go`:

```go
type DiagnosticStage string

const (
	DiagnosticStageTCP      DiagnosticStage = "tcp"
	DiagnosticStageTLS      DiagnosticStage = "tls"
	DiagnosticStageLogin    DiagnosticStage = "login"
	DiagnosticStageQuery    DiagnosticStage = "query"
	DiagnosticStageCluster  DiagnosticStage = "cluster"
)

type DiagnosticStatus string

const (
	DiagnosticStatusSuccess DiagnosticStatus = "success"
	DiagnosticStatusFailed  DiagnosticStatus = "failed"
	DiagnosticStatusSkipped DiagnosticStatus = "skipped"
)

type DiagnosticCheck struct {
	Stage      DiagnosticStage  `json:"stage"`
	Status     DiagnosticStatus `json:"status"`
	DurationMS int64            `json:"duration_ms"`
	Message    string           `json:"message,omitempty"`
}

type DiagnosticResponse struct {
	Provider    Provider          `json:"provider"`
	Host        string            `json:"host"`
	Status      DiagnosticStatus  `json:"status"`
	Checks      []DiagnosticCheck `json:"checks"`
	CollectedAt time.Time         `json:"collected_at"`
}
```

Create `/Users/huangliang/project/OneOPS-ALL/ctrlhub/controller/pkg/sdn/diagnostics_test.go`:

```go
func TestDiagnosticResponseFailsWhenAnyRequiredCheckFails(t *testing.T) {
	resp := NewDiagnosticResponse(ProviderACI, "apic.example")
	resp.AddCheck(DiagnosticStageTCP, DiagnosticStatusSuccess, 10, "")
	resp.AddCheck(DiagnosticStageTLS, DiagnosticStatusFailed, 20, "handshake timeout")
	require.Equal(t, DiagnosticStatusFailed, resp.Status)
	require.Contains(t, resp.Checks[1].Message, "handshake timeout")
}
```

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/ctrlhub
go test ./controller/pkg/sdn -run TestDiagnosticResponseFailsWhenAnyRequiredCheckFails -count=1
```

Expected before implementation: fail because helpers do not exist.

- [ ] **W3.2 Add diagnostic API**

Add request/handler in `/Users/huangliang/project/OneOPS-ALL/ctrlhub/controller/pkg/controller/api/sdn.go`:

```go
type SDNDiagnoseRequest struct {
	Provider sdn.Provider `json:"provider"`
	Endpoint sdn.Endpoint `json:"endpoint"`
}
```

Expose:

```text
POST /api/v1/sdn/diagnose
```

Behavior:

- Always redact endpoint password in logs.
- Run TCP/TLS/login/query checks in order.
- Stop cluster check when login or query fails.
- Return HTTP 200 with diagnostic status when request is valid; use non-2xx only for malformed request/provider unsupported.

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/ctrlhub
go test ./controller/pkg/sdn ./controller/pkg/controller/api -run 'TestDiagnostic|TestSDNDiagnose' -count=1
```

Expected: pass.

- [ ] **W3.3 Add alarm model and ACI contract**

Add to `/Users/huangliang/project/OneOPS-ALL/ctrlhub/controller/pkg/sdn/model.go`:

```go
type AlarmSeverity string

const (
	AlarmSeverityCritical AlarmSeverity = "critical"
	AlarmSeverityMajor    AlarmSeverity = "major"
	AlarmSeverityMinor    AlarmSeverity = "minor"
	AlarmSeverityWarning  AlarmSeverity = "warning"
	AlarmSeverityInfo     AlarmSeverity = "info"
)

type AlarmStatus string

const (
	AlarmStatusActive   AlarmStatus = "active"
	AlarmStatusCleared  AlarmStatus = "cleared"
)

type Alarm struct {
	ID              string        `json:"id"`
	Provider        Provider      `json:"provider"`
	Severity        AlarmSeverity `json:"severity"`
	Status          AlarmStatus   `json:"status"`
	ResourceType    string        `json:"resource_type"`
	ResourceID      string        `json:"resource_id"`
	Tenant          string        `json:"tenant,omitempty"`
	Code            string        `json:"code"`
	Message         string        `json:"message"`
	FirstSeenAt     time.Time     `json:"first_seen_at"`
	LastSeenAt      time.Time     `json:"last_seen_at"`
	ClearedAt       *time.Time    `json:"cleared_at,omitempty"`
	DN              string        `json:"dn,omitempty"`
	ProviderType    string        `json:"provider_type,omitempty"`
}

type AlarmResponse struct {
	Provider    Provider  `json:"provider"`
	CollectedAt time.Time `json:"collected_at"`
	Alarms      []Alarm   `json:"alarms"`
}
```

ACI implementation should map APIC `faultInst` fields to this model. Huawei may return an empty supported response until a live contract is verified.

Exit criteria:

- CtrlHub diagnostic API exists and is covered by tests.
- CtrlHub alarm model exists.
- ACI alarm collection has parser tests or fixture-backed adapter tests.

### W4: OneOPS Health, Alarm, And Config-Plan Scaffolding

Purpose:

- Move stages 2, 3, and 4 forward in OneOPS without enabling unsafe live configuration apply.

Primary repos:

- `/Users/huangliang/project/OneOPS-ALL/OneOPS`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI`

Files:

- Modify OneOPS SDN DTO/model/service/API/router files.
- Modify OneOPS UI SDN types/API/page.

Deliverables:

- OneOPS API calls CtrlHub diagnose and stores latest health summary.
- OneOPS persists SDN alarms and displays alarm list.
- OneOPS can create config plans in draft/dry-run state.
- Config execution endpoint remains disabled behind explicit approval gate.

Task steps:

- [ ] **W4.1 Add OneOPS health model and API**

Add model in `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/platform/platform_model/sdn_controller.go`:

```go
type SDNControllerHealthCheck struct {
	commonModel.Common
	TenantScoped
	ControllerID string    `gorm:"type:varchar(36);index;not null;comment:控制器ID"`
	Provider     string    `gorm:"type:varchar(32);index;not null;comment:SDN provider"`
	Status       string    `gorm:"type:varchar(32);index;not null;comment:健康状态"`
	ChecksJSON   string    `gorm:"type:longtext;comment:分步诊断结果"`
	ErrorSummary string    `gorm:"type:text;comment:错误摘要"`
	CheckedAt    time.Time `gorm:"index;comment:检查时间"`
}

func (*SDNControllerHealthCheck) TableName() string {
	return "platform_sdn_controller_health_check"
}
```

Expose:

```text
POST /api/v1/sdn/controllers/{id}/diagnose
GET /api/v1/sdn/controllers/{id}/health/latest
```

- [ ] **W4.2 Add alarm persistence and API**

Add model:

```go
type SDNAlarm struct {
	commonModel.Common
	TenantScoped
	ControllerID  string     `gorm:"type:varchar(36);index;not null;comment:控制器ID"`
	Provider      string     `gorm:"type:varchar(32);index;not null;comment:SDN provider"`
	AlarmID       string     `gorm:"type:varchar(256);index;not null;comment:厂商告警ID"`
	Severity      string     `gorm:"type:varchar(32);index;not null;comment:级别"`
	Status        string     `gorm:"type:varchar(32);index;not null;comment:状态"`
	ResourceType  string     `gorm:"type:varchar(64);index;comment:资源类型"`
	ResourceID    string     `gorm:"type:varchar(256);index;comment:资源ID"`
	TenantName    string     `gorm:"type:varchar(256);index;comment:SDN租户"`
	Code          string     `gorm:"type:varchar(128);index;comment:告警码"`
	Message       string     `gorm:"type:text;comment:告警消息"`
	DN            string     `gorm:"type:varchar(1024);index;comment:厂商DN"`
	FirstSeenAt   time.Time  `gorm:"index;comment:首次发现"`
	LastSeenAt    time.Time  `gorm:"index;comment:最近发现"`
	ClearedAt     *time.Time `gorm:"comment:恢复时间"`
	AttributesJSON string   `gorm:"type:text;comment:扩展属性"`
}

func (*SDNAlarm) TableName() string {
	return "platform_sdn_alarm"
}
```

Expose:

```text
POST /api/v1/sdn/controllers/{id}/alarms/sync
GET /api/v1/sdn/controllers/{id}/alarms
```

- [ ] **W4.3 Add config-plan draft model without live apply**

Add model:

```go
type SDNConfigPlan struct {
	commonModel.Common
	TenantScoped
	ControllerID     string     `gorm:"type:varchar(36);index;not null;comment:控制器ID"`
	Provider         string     `gorm:"type:varchar(32);index;not null;comment:SDN provider"`
	PlanType         string     `gorm:"type:varchar(64);index;not null;comment:计划类型"`
	Status           string     `gorm:"type:varchar(32);index;not null;comment:状态"`
	IntentJSON       string     `gorm:"type:longtext;comment:配置意图"`
	DryRunResultJSON string     `gorm:"type:longtext;comment:Dry-run结果"`
	ErrorSummary     string     `gorm:"type:text;comment:错误摘要"`
	ApprovedAt       *time.Time `gorm:"comment:审批时间"`
	ExecutedAt       *time.Time `gorm:"comment:执行时间"`
}

func (*SDNConfigPlan) TableName() string {
	return "platform_sdn_config_plan"
}
```

Expose draft/dry-run endpoints only:

```text
POST /api/v1/sdn/controllers/{id}/config-plans
GET /api/v1/sdn/controllers/{id}/config-plans
GET /api/v1/sdn/controllers/{id}/config-plans/{plan_id}
POST /api/v1/sdn/controllers/{id}/config-plans/{plan_id}/dry-run
```

Do not expose live execute in this workstream. If an execute route is needed for UI shape, it must return HTTP 409 with message `SDN配置执行尚未启用，请先完成审批与回滚设计`.

Exit criteria:

- Health APIs can store latest diagnostic response.
- Alarm APIs can sync and list normalized alarms.
- Config-plan APIs can create draft and dry-run records.
- No live config apply is possible.

### W5: Integration, Acceptance, And Long-Task Closure

Purpose:

- Keep the parallel workstreams coherent and prove they work together.

Files:

- Create evidence docs under `/Users/huangliang/project/OneOPS-ALL/docs/superpowers/evidence/`.
- Create or update smoke scripts in `OneOPS-UI/scripts`.

Task steps:

- [ ] **W5.1 Verify backend suites**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/platform/service/impl ./app/platform/api ./app/platform/router ./app/platform/dto ./app/platform/platform_model
```

Expected: pass.

- [ ] **W5.2 Verify CtrlHub suites**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/ctrlhub
go test ./controller/pkg/sdn ./controller/pkg/sdn/aci ./controller/pkg/sdn/huawei ./controller/pkg/controller/api
```

Expected: pass.

- [ ] **W5.3 Verify frontend formatting and smoke**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npx prettier --check src/views/device/SdnControllerManagement.vue src/api/platform/sdn-controller.ts src/typings/platform/sdn-controller.ts scripts/sdn-resource-workbench-smoke.ts
```

Expected: pass.

- [ ] **W5.4 Live ACI acceptance**

Using the existing configured ACI controller in the OneOPS UI:

- Run sync.
- Open resource browser.
- Confirm totals match summary.
- Open endpoint tab and search by a known endpoint IP or MAC.
- Run a second sync.
- Open diff view and confirm no unexpected changes.
- If APIC test data can be safely changed, add one low-risk object and confirm `added` diff appears.

Record evidence in:

```text
/Users/huangliang/project/OneOPS-ALL/docs/superpowers/evidence/2026-06-20-oneops-sdn-ops-management-acceptance.md
```

## Commit Strategy

Use repo-local commits:

- `OneOPS`: `feat: add sdn resource projection and diff`
- `OneOPS-UI`: `feat: add sdn resource workbench`
- `ctrlhub`: `feat: add sdn diagnostics and alarms`
- `docs`: `docs: plan oneops sdn ops long task`

Do not stage unrelated dirty files. Use pathspecs for each commit.

## Recommended Agent Allocation

Run these in parallel after this plan is approved:

- Agent A: W1 backend resource projection and diff in `OneOPS`.
- Agent B: W2 UI resource/history/diff workbench in `OneOPS-UI`, initially using mocked API responses if W1 is not ready.
- Agent C: W3 CtrlHub diagnostics and alarm contracts in `ctrlhub`.
- Agent D: W4 OneOPS health/alarm/config-plan scaffolding in `OneOPS`, using fake CtrlHub servers in tests.
- Main agent: W5 integration review, conflict resolution, commits, and live ACI acceptance.

## First Execution Batch

Start with these concrete tasks:

1. Agent A implements W1.1 to W1.4 and reports tests.
2. Agent B implements W2.1 to W2.2 behind empty-state-friendly UI.
3. Agent C implements W3.1 to W3.2 without alarm collection yet.
4. Agent D implements W4.3 config-plan draft model and tests with execute disabled.

This batch gives immediate resource usability, health diagnostics, and safe config-plan scaffolding without enabling production writes.
