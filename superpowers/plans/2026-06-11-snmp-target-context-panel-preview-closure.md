# SNMP Target Context Panel Preview Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the strict backend/frontend data closure from a real device target to strategy-set metric contract resolution and base panel capability preview, without Grafana work.

**Architecture:** Add one strict by-target path: `strategy_set_id + target_part -> platform_devices_v2 -> normalized strategy context -> existing strategy-set contract resolver -> existing default base panel requirements -> supports + support_summary`. Target/device business semantics are translated only in the backend target context resolver; the frontend calls the by-target endpoint and displays/consumes the returned data. This plan intentionally does not add fallback/degradation branches, does not generate Grafana JSON, does not manage Prometheus recording rules, and does not broaden metric standardization.

**Tech Stack:** Go service/API/router in `/OneOPS/OneOps`; TypeScript API/types in `/OneOPS/OneOps-UI`; TDD with focused Go resolver/API tests plus frontend smoke/typecheck.

---

## Scope Lock

This plan only closes one data path:

```text
target_part + strategy_set_id
  -> resolve device row from platform_devices_v2
  -> derive SnmpMetricStrategySetContractOptions
  -> resolve matching strategy-set item contracts
  -> evaluate backend default base SNMP panel requirements
  -> return effective_contract, supports, support_summary, and resolved target context
```

Strict non-goals:

- no Grafana dashboard JSON generation;
- no Prometheus recording-rule lifecycle;
- no page layout or visual dashboard implementation;
- no legacy inventory fallback;
- no IP expansion or dashboard-binding fallback;
- no frontend-side target context resolver;
- no silent empty success when the target, required context, or matching strategy-set items are missing.

Strict failure rules:

- empty `strategy_set_id` returns an error;
- empty `target_part` returns an error;
- no row in `platform_devices_v2` for `code = target_part OR id = target_part` returns an error;
- missing required target context fields returns an error;
- strategy-set contract resolution with zero selected item contracts returns an error;
- no automatic fallback to caller-provided context in the by-target path.

Required target context fields for this closure:

```text
catalog_name
manufacturer_name
platform_name
device_model_name
system_version
```

Optional but returned when present:

```text
function_area
catalog_id
```

---

## File Structure

Backend DTOs and interfaces:

- Modify `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
  - Add target-context DTOs and by-target panel preview request/response.
- Modify `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
  - Add strict by-target resolver method to the existing contract resolver interface.

Backend implementation:

- Modify `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
  - Inject `proxy.IQueryProxy`.
  - Resolve `target_part` from `platform_devices_v2`.
  - Convert device metadata to `SnmpMetricStrategySetContractOptions`.
  - Reuse existing strategy-set contract and panel support functions.
  - Return errors for the strict failure rules above.
- Modify `/OneOPS/OneOps/cmd/wire_gen.go`
  - Pass the existing query proxy into `NewMetricCapabilityContractResolver`.
- Modify `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
  - Add focused tests for target context resolution and strict by-target preview.

Backend API/router:

- Modify `/OneOPS/OneOps/app/platform/api/teleabs.go`
  - Add handler for strict by-target preview.
- Modify `/OneOPS/OneOps/app/platform/router/platform.go`
  - Register the route in normal platform router.
- Modify `/OneOPS/OneOps/app/platform/router/platform_bidi.go`
  - Register the same route in bidi router.

Frontend:

- Modify `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
  - Add by-target request/response types.
- Modify `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`
  - Add typed API wrapper.

Docs:

- Modify `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`
  - Add the new strict by-target closure and remaining deferred items.

---

### Task 1: Backend DTO Contract

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`

- [ ] **Step 1: Add strict target context DTOs**

Add these types after `SnmpStrategySetPanelCapabilityPreviewResponse`:

```go
type SnmpMetricResolvedTargetContext struct {
	TargetPart      string                               `json:"target_part"`
	DeviceID        string                               `json:"device_id"`
	DeviceCode      string                               `json:"device_code"`
	Context          SnmpMetricStrategySetContractOptions `json:"context"`
	MissingFields    []string                             `json:"missing_fields,omitempty"`
	MetadataSource   string                               `json:"metadata_source"`
}

type SnmpStrategySetTargetPanelCapabilityPreviewRequest struct {
	TargetPart string `json:"target_part"`
}

type SnmpStrategySetTargetPanelCapabilityPreviewResponse struct {
	StrategySetID     string                              `json:"strategy_set_id"`
	Target            SnmpMetricResolvedTargetContext     `json:"target"`
	Source            string                              `json:"source"`
	ItemContracts     []SnmpMetricStrategySetItemContract `json:"item_contracts"`
	EffectiveContract SnmpMetricContractEnvelope          `json:"effective_contract"`
	Supports          []SnmpPanelCapabilitySupport        `json:"supports"`
	SupportSummary    SnmpPanelCapabilitySupportSummary   `json:"support_summary"`
}
```

- [ ] **Step 2: Commit DTO contract**

```bash
cd /OneOPS/OneOps
git add app/platform/dto/snmp_metric_contract.go
git commit -m "feat: add snmp target panel preview dto"
```

---

### Task 2: Backend Strict Target Context Resolution Tests

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Write failing tests for target metadata conversion**

Add tests that create a resolver with a fake query proxy backed by an in-memory `platform_devices_v2` table. The tests must assert:

- valid device metadata becomes `SnmpMetricStrategySetContractOptions`;
- `catalog_name`, `manufacturer_name`, `platform_name`, `device_model_name`, and `system_version` are required;
- empty `target_part` fails;
- missing device fails.

Use expected context:

```go
dto.SnmpMetricStrategySetContractOptions{
	FunctionArea:     "core",
	CatalogID:        "switch",
	CatalogName:      "Switch",
	ManufacturerName: "H3C",
	PlatformName:     "Comware",
	DeviceModelName:  "S6520",
	SystemVersion:    "7.1",
}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolverResolvesTargetContext|TestMetricCapabilityContractResolverRejectsInvalidTargetContext' -count=1
```

Expected: FAIL because the target context resolver does not exist yet.

---

### Task 3: Backend Target Context Resolver Implementation

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/cmd/wire_gen.go`

- [ ] **Step 1: Inject query proxy into the resolver**

Update imports to include:

```go
"github.com/netxops/OneOps/app/common/proxy"
"github.com/netxops/OneOps/app/platform/pkg/deviceidentity"
```

Update struct and constructor:

```go
type MetricCapabilityContractResolver struct {
	Logger         *zap.Logger
	ProxySrv       proxy.IQueryProxy
	StrategySrv    service.ITeleabsStrategy
	StrategySetSrv service.ITeleabsStrategySet
}

func NewMetricCapabilityContractResolver(
	logger *zap.Logger,
	proxySrv proxy.IQueryProxy,
	strategySrv service.ITeleabsStrategy,
	strategySetSrv service.ITeleabsStrategySet,
) *MetricCapabilityContractResolver {
	return &MetricCapabilityContractResolver{
		Logger:         logger,
		ProxySrv:       proxySrv,
		StrategySrv:    strategySrv,
		StrategySetSrv: strategySetSrv,
	}
}
```

- [ ] **Step 1a: Update generated wire constructor call**

Update `/OneOPS/OneOps/cmd/wire_gen.go` so the existing query proxy is passed into the constructor:

```go
metricCapabilityContractResolver := impl24.NewMetricCapabilityContractResolver(logger, txProxySrv, teleabsStrategySrv, teleabsStrategySetSrv)
```

- [ ] **Step 2: Add target row loading**

Add a private row type and loader:

```go
type snmpMetricTargetDeviceRow struct {
	ID             string `gorm:"column:id"`
	Code           string `gorm:"column:code"`
	Type           string `gorm:"column:type"`
	PlatformCode   string `gorm:"column:platform_code"`
	Status         string `gorm:"column:status"`
	AttributesJSON string `gorm:"column:attributes_json"`
	MetadataJSON   string `gorm:"column:metadata_json"`
}

func (r *MetricCapabilityContractResolver) loadTargetDeviceRow(ctx context.Context, targetPart string) (*snmpMetricTargetDeviceRow, error) {
	targetPart = strings.TrimSpace(targetPart)
	if targetPart == "" {
		return nil, fmt.Errorf("target_part is required")
	}
	db, err := platformTenantScopedTableDB(ctx, r.ProxySrv, "platform_devices_v2")
	if err != nil {
		return nil, err
	}
	rows := make([]snmpMetricTargetDeviceRow, 0, 1)
	if err := db.
		Select("id, code, type, platform_code, status, attributes_json, metadata_json").
		Where("code = ? OR id = ?", targetPart, targetPart).
		Limit(1).
		Find(&rows).Error; err != nil {
		return nil, err
	}
	if len(rows) == 0 {
		return nil, fmt.Errorf("target device not found: %s", targetPart)
	}
	return &rows[0], nil
}
```

- [ ] **Step 3: Add strict metadata merge and validation**

Add helpers:

```go
func snmpMetricTargetMetadata(row *snmpMetricTargetDeviceRow) (map[string]interface{}, error) {
	if row == nil {
		return nil, fmt.Errorf("target device row is empty")
	}
	merged := make(map[string]interface{})
	for _, raw := range []string{row.AttributesJSON, row.MetadataJSON} {
		raw = strings.TrimSpace(raw)
		if raw == "" {
			continue
		}
		var m map[string]interface{}
		if err := json.Unmarshal([]byte(raw), &m); err != nil {
			return nil, fmt.Errorf("parse target device metadata failed: %w", err)
		}
		for key, value := range m {
			if strings.TrimSpace(snmpMetricStringAny(merged[key])) != "" {
				continue
			}
			merged[key] = value
		}
	}
	if strings.TrimSpace(snmpMetricStringAny(merged["platform_code"])) == "" {
		merged["platform_code"] = strings.TrimSpace(row.PlatformCode)
	}
	if strings.TrimSpace(snmpMetricStringAny(merged["status"])) == "" {
		merged["status"] = strings.TrimSpace(row.Status)
	}
	return merged, nil
}

func snmpMetricTargetContextFromMetadata(targetPart string, row *snmpMetricTargetDeviceRow, meta map[string]interface{}) (dto.SnmpMetricResolvedTargetContext, error) {
	resolved := deviceidentity.ResolveMetadata(meta, strings.TrimSpace(row.Type))
	target := dto.SnmpMetricResolvedTargetContext{
		TargetPart:    strings.TrimSpace(targetPart),
		DeviceID:      strings.TrimSpace(row.ID),
		DeviceCode:    strings.TrimSpace(row.Code),
		MetadataSource: "platform_devices_v2",
		Context: dto.SnmpMetricStrategySetContractOptions{
			FunctionArea:     strings.TrimSpace(resolved.FunctionArea),
			CatalogID:        strings.TrimSpace(resolved.CatalogCode),
			CatalogName:      strings.TrimSpace(resolved.CatalogName),
			ManufacturerName: strings.TrimSpace(resolved.Manufacturer),
			PlatformName:     strings.TrimSpace(resolved.PlatformName),
			DeviceModelName:  strings.TrimSpace(resolved.DeviceModelName),
			SystemVersion:    strings.TrimSpace(resolved.SystemVersion),
		},
	}
	target.MissingFields = snmpMetricMissingTargetContextFields(target.Context)
	if len(target.MissingFields) > 0 {
		return target, fmt.Errorf("target context missing required fields: %s", strings.Join(target.MissingFields, ", "))
	}
	return target, nil
}

func snmpMetricMissingTargetContextFields(ctx dto.SnmpMetricStrategySetContractOptions) []string {
	missing := make([]string, 0, 5)
	if strings.TrimSpace(ctx.CatalogName) == "" {
		missing = append(missing, "catalog_name")
	}
	if strings.TrimSpace(ctx.ManufacturerName) == "" {
		missing = append(missing, "manufacturer_name")
	}
	if strings.TrimSpace(ctx.PlatformName) == "" {
		missing = append(missing, "platform_name")
	}
	if strings.TrimSpace(ctx.DeviceModelName) == "" {
		missing = append(missing, "device_model_name")
	}
	if strings.TrimSpace(ctx.SystemVersion) == "" {
		missing = append(missing, "system_version")
	}
	return missing
}

func snmpMetricStringAny(v interface{}) string {
	if s, ok := v.(string); ok {
		return strings.TrimSpace(s)
	}
	return ""
}
```

- [ ] **Step 4: Add public target context method**

```go
func (r *MetricCapabilityContractResolver) ResolveTargetContext(ctx context.Context, targetPart string) (dto.SnmpMetricResolvedTargetContext, error) {
	row, err := r.loadTargetDeviceRow(ctx, targetPart)
	if err != nil {
		return dto.SnmpMetricResolvedTargetContext{}, err
	}
	meta, err := snmpMetricTargetMetadata(row)
	if err != nil {
		return dto.SnmpMetricResolvedTargetContext{}, err
	}
	return snmpMetricTargetContextFromMetadata(targetPart, row, meta)
}
```

- [ ] **Step 5: Run target context tests**

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolverResolvesTargetContext|TestMetricCapabilityContractResolverRejectsInvalidTargetContext' -count=1
```

Expected: PASS.

- [ ] **Step 6: Commit target context resolver**

```bash
cd /OneOPS/OneOps
git add app/platform/service/impl/metric_capability_contract_resolver.go app/platform/service/impl/metric_capability_contract_resolver_test.go cmd/wire_gen.go
git commit -m "feat: resolve snmp target metric context"
```

---

### Task 4: Backend Strict By-Target Panel Preview Resolver

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Extend resolver interface**

Add:

```go
ResolveStrategySetTargetPanelCapabilityPreview(ctx context.Context, strategySetID string, request dto.SnmpStrategySetTargetPanelCapabilityPreviewRequest) (*dto.SnmpStrategySetTargetPanelCapabilityPreviewResponse, error)
```

- [ ] **Step 2: Write failing strict preview tests**

Add tests asserting:

- `target_part` resolves to context and selects the matching strategy item;
- response includes `Target.Context`;
- backend default panel requirements are used;
- zero selected item contracts returns an error.

The positive test should expect:

```go
preview.Target.Context.ManufacturerName == "H3C"
preview.Target.Context.PlatformName == "Comware"
preview.SupportSummary.Total == 7
len(preview.ItemContracts) > 0
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverPreviewsStrategySetPanelCapabilitySupportByTarget -count=1
```

Expected: FAIL because the by-target resolver method does not exist yet.

- [ ] **Step 4: Implement strict by-target resolver**

Add:

```go
func (r *MetricCapabilityContractResolver) ResolveStrategySetTargetPanelCapabilityPreview(
	ctx context.Context,
	strategySetID string,
	request dto.SnmpStrategySetTargetPanelCapabilityPreviewRequest,
) (*dto.SnmpStrategySetTargetPanelCapabilityPreviewResponse, error) {
	if strings.TrimSpace(strategySetID) == "" {
		return nil, fmt.Errorf("strategy set id is required")
	}
	target, err := r.ResolveTargetContext(ctx, request.TargetPart)
	if err != nil {
		return nil, err
	}
	resolution, err := r.ResolveStrategySetContractWithOptions(ctx, strategySetID, target.Context)
	if err != nil {
		return nil, err
	}
	if resolution == nil {
		return nil, fmt.Errorf("strategy set contract resolution is empty")
	}
	if len(resolution.ItemContracts) == 0 {
		return nil, fmt.Errorf("strategy set has no matched metric contract items for target: %s", strings.TrimSpace(request.TargetPart))
	}
	supports := r.ResolvePanelCapabilitySupports(resolution.EffectiveContract, r.DefaultPanelCapabilityRequirements())
	return &dto.SnmpStrategySetTargetPanelCapabilityPreviewResponse{
		StrategySetID:     resolution.StrategySetID,
		Target:            target,
		Source:            resolution.Source,
		ItemContracts:     resolution.ItemContracts,
		EffectiveContract: resolution.EffectiveContract,
		Supports:          supports,
		SupportSummary:    r.SummarizePanelCapabilitySupports(supports),
	}, nil
}
```

- [ ] **Step 5: Run focused preview tests**

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverPreviewsStrategySetPanelCapabilitySupportByTarget -count=1
```

Expected: PASS.

- [ ] **Step 6: Commit strict by-target resolver**

```bash
cd /OneOPS/OneOps
git add app/platform/service/i_metric_capability_contract_resolver.go app/platform/service/impl/metric_capability_contract_resolver.go app/platform/service/impl/metric_capability_contract_resolver_test.go
git commit -m "feat: preview snmp panel support by target"
```

---

### Task 5: Backend API And Routes

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/api/teleabs.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform_bidi.go`

- [ ] **Step 1: Add strict API handler**

Add to `teleabs.go`:

```go
// PreviewTeleabsStrategySetPanelCapabilitySupportByTarget previews base panel support for a real target device.
func (a *TeleabsAPI) PreviewTeleabsStrategySetPanelCapabilitySupportByTarget(ctx *gin.Context) {
	id := ctx.Param("id")
	if id == "" {
		response.FailWithMsg("策略集 ID 不能为空", ctx)
		return
	}
	if a.MetricContractResolver == nil {
		response.FailWithMsg("指标能力契约解析服务未初始化", ctx)
		return
	}
	var body dto.SnmpStrategySetTargetPanelCapabilityPreviewRequest
	if err := ctx.ShouldBindJSON(&body); err != nil {
		response.FailWithMsg("请求参数错误: "+err.Error(), ctx)
		return
	}
	result, err := a.MetricContractResolver.ResolveStrategySetTargetPanelCapabilityPreview(monitoringV2RequestContextWithAuth(ctx), id, body)
	if err != nil {
		a.Logger.Error("PreviewTeleabsStrategySetPanelCapabilitySupportByTarget 失败", zap.String("id", id), zap.String("target_part", body.TargetPart), zap.Error(err))
		response.FailWithMsg(err.Error(), ctx)
		return
	}
	response.OkWithData(result, ctx)
}
```

- [ ] **Step 2: Register route in both routers**

Add in `/OneOPS/OneOps/app/platform/router/platform.go` near the existing strategy-set metric-contract routes:

```go
teleabsGroup.POST("strategy-sets/:id/metric-contract/panel-support/by-target", teleabsAPI.PreviewTeleabsStrategySetPanelCapabilitySupportByTarget)
```

Add in `/OneOPS/OneOps/app/platform/router/platform_bidi.go` near the existing strategy-set metric-contract routes:

```go
metrics.POST("teleabs/strategy-sets/:id/metric-contract/panel-support/by-target", teleabsAPI.PreviewTeleabsStrategySetPanelCapabilitySupportByTarget)
```

- [ ] **Step 3: Run backend compile checks**

```bash
cd /OneOPS/OneOps
go test ./app/platform/api ./app/platform/service/impl ./cmd -run 'TestMetricCapabilityContractResolver|^$' -count=1
```

Expected: PASS.

- [ ] **Step 4: Commit API route**

```bash
cd /OneOPS/OneOps
git add app/platform/api/teleabs.go app/platform/router/platform.go app/platform/router/platform_bidi.go
git commit -m "feat: expose snmp target panel preview api"
```

---

### Task 6: Frontend Typed API Wrapper

**Files:**

- Modify: `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- Modify: `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`

- [ ] **Step 1: Add frontend types**

Add to `snmp-metric-contract.ts`:

```ts
export interface SnmpMetricResolvedTargetContext {
  target_part: string;
  device_id: string;
  device_code: string;
  context: SnmpMetricStrategySetContractContext;
  missing_fields?: string[];
  metadata_source: string;
}

export interface SnmpStrategySetTargetPanelCapabilityPreviewRequest {
  target_part: string;
}

export interface SnmpStrategySetTargetPanelCapabilityPreviewResponse {
  strategy_set_id: string;
  target: SnmpMetricResolvedTargetContext;
  source: 'backend_resolver' | string;
  item_contracts: SnmpMetricStrategySetItemContract[];
  effective_contract: SnmpMetricContractEnvelope;
  supports: SnmpPanelCapabilitySupport[];
  support_summary: SnmpPanelCapabilitySupportSummary;
}
```

- [ ] **Step 2: Add frontend API wrapper**

Update imports in `teleabs.ts` to include:

```ts
SnmpStrategySetTargetPanelCapabilityPreviewRequest,
SnmpStrategySetTargetPanelCapabilityPreviewResponse,
```

Add wrapper:

```ts
/** 预览真实目标设备在策略集下的基础 SNMP 面板能力支持状态 */
export const previewTeleabsStrategySetPanelCapabilitySupportByTarget = async (
  id: string,
  body: SnmpStrategySetTargetPanelCapabilityPreviewRequest,
) => {
  return request<SnmpStrategySetTargetPanelCapabilityPreviewResponse>({
    url: `${BASE}/strategy-sets/${encodeURIComponent(id)}/metric-contract/panel-support/by-target`,
    method: HTTP_POST,
    data: body,
  });
};
```

- [ ] **Step 3: Run frontend checks**

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-metric-contract
npm run typecheck
```

Expected: PASS.

- [ ] **Step 4: Commit frontend API wrapper**

```bash
cd /OneOPS/OneOps-UI
git add src/typings/platform/snmp-metric-contract.ts src/api/platform/teleabs.ts
git commit -m "feat: add snmp target panel preview api"
```

---

### Task 7: Documentation Update

**Files:**

- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [ ] **Step 1: Add strict closure section**

Append a new section:

````markdown
### 10. Target-Based Strategy-Set Panel Preview Closure

The next strict closure adds one by-target data path:

```text
strategy_set_id + target_part
  -> platform_devices_v2
  -> resolved_target_context
  -> ResolveStrategySetContractWithOptions
  -> effective_contract
  -> backend default base panel requirements
  -> supports[]
  -> support_summary
```

The business semantics translation happens in the backend target context resolver. It reads Device V2 metadata from `platform_devices_v2`, normalizes it through `deviceidentity.ResolveMetadata`, and maps it into `SnmpMetricStrategySetContractOptions`.

The frontend does not infer manufacturer, platform, model, catalog, or version. It calls:

```text
POST /platform/metrics/teleabs/strategy-sets/:id/metric-contract/panel-support/by-target
```

Request:

```json
{ "target_part": "DEVICE-CODE-OR-ID" }
```

Strict behavior:

- missing target, missing required context, or zero matched strategy-set items returns an error;
- no legacy inventory fallback is used;
- no frontend target-context fallback is used;
- no Grafana JSON generation is included in this closure.
````

- [ ] **Step 2: Verify docs**

```bash
cd /OneOPS
rg -n "Target-Based Strategy-Set Panel Preview Closure|panel-support/by-target|platform_devices_v2" docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md docs/superpowers/plans/2026-06-11-snmp-target-context-panel-preview-closure.md
```

Expected: both the handoff and this plan mention the strict by-target closure. Do not run a docs commit from `/OneOPS` in this workspace because `/OneOPS` is not a git repository.

---

### Task 8: Final Verification

**Files:**

- No production file changes.

- [ ] **Step 1: Backend focused tests**

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolver -count=1
```

Expected: PASS.

- [ ] **Step 2: Backend compile checks**

```bash
cd /OneOPS/OneOps
go test ./app/platform/api ./app/platform/service/impl ./cmd -run 'TestMetricCapabilityContractResolver|^$' -count=1
```

Expected: PASS.

- [ ] **Step 3: Frontend checks**

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-metric-contract
npm run smoke:snmp-workspace-view
npm run smoke:snmp-profile-resolution
npm run typecheck
```

Expected: PASS.

- [ ] **Step 4: Verify strict scope**

Run:

```bash
cd /OneOPS
rg -n "panel-support/by-target|ResolveStrategySetTargetPanelCapabilityPreview|SnmpStrategySetTargetPanelCapabilityPreview" OneOps OneOps-UI docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md
```

Expected:

- backend DTO/interface/resolver/API/router references exist;
- frontend type/API wrapper references exist;
- handoff documentation references exist;
- no Grafana files are modified by this plan.

---

## Completion Criteria

The closure is complete only when all of the following are true:

- a caller can send `strategy_set_id + target_part` to the new by-target endpoint;
- backend resolves target metadata from `platform_devices_v2`;
- backend converts target metadata into strategy-set matching context;
- backend returns an error for missing target, missing required context, or zero matched item contracts;
- backend returns `effective_contract`, default base panel `supports`, `support_summary`, and the resolved target context for valid input;
- frontend has a typed API wrapper for the new endpoint;
- all verification commands in Task 8 pass.
