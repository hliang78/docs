# Device V2 Tagging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add convenient selected-device tagging to Device V2 management, covering short `group_tags` and structured key-value `labels`.

**Architecture:** Add a backend batch-label endpoint that applies tag mutations per device through the existing Device V2 update path, returning per-code results for partial failure handling. Add a focused frontend tagging modal that can be opened from the batch toolbar or a row action and calls the new API. Keep the first iteration scoped to explicitly selected devices.

**Tech Stack:** Go/Gin/Gorm backend, Vue 3 + Ant Design Vue frontend, Playwright E2E tests, existing Device V2 API/request helpers.

---

## File Structure

- Modify `OneOps/app/device/v2/dto/device_v2.go`: add request/response DTOs for batch labels.
- Modify `OneOps/app/device/v2/service/i_device_v2.go`: add service method for batch label application.
- Modify `OneOps/app/device/v2/service/impl/device_v2_minimal_attributes.go`: implement label/group tag mutation helpers and batch application on `DeviceV2Srv`.
- Modify `OneOps/app/device/v2/api/device_v2.go`: add API handler `BatchLabels`.
- Modify `OneOps/app/device/v2/router/device_v2.go`: register `POST /device/v2/batch-labels`.
- Create `OneOps/app/device/v2/service/impl/device_v2_batch_labels_test.go`: service-level tests for mutations, validation, partial failure, and field preservation.
- Create or extend `OneOps/app/device/v2/api/device_v2_batch_labels_api_test.go`: API validation and route tests.
- Modify `OneOPS-UI/src/api/device/device-v2.ts`: add TypeScript request/response types and `batchUpdateDeviceV2LabelsReq`.
- Modify `OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue`: add toolbar button, row action, modal state, form validation, submit/result handling.
- Create `OneOps/scripts/platform2_multi_agent_test/agents/device_v2_tagging.spec.ts`: Playwright tests for batch/row tagging and flexible-search verification.
- Modify `OneOps/scripts/platform2_multi_agent_test/package.json`: add `test:device-v2:tagging`.

---

## Task 1: Backend DTOs And Service Contract

**Files:**
- Modify: `OneOps/app/device/v2/dto/device_v2.go`
- Modify: `OneOps/app/device/v2/service/i_device_v2.go`

- [x] **Step 1: Add DTO types**

Add these types near `DeviceV2UpdateReq` in `OneOps/app/device/v2/dto/device_v2.go`:

```go
const (
	DeviceV2GroupTagModeAppend  = "append"
	DeviceV2GroupTagModeRemove  = "remove"
	DeviceV2GroupTagModeReplace = "replace"

	DeviceV2LabelActionSet   = "set"
	DeviceV2LabelActionUnset = "unset"
)

type DeviceV2BatchGroupTagAction struct {
	Mode string   `json:"mode"`
	Tags []string `json:"tags"`
}

type DeviceV2BatchLabelAction struct {
	Op    string `json:"op"`
	Key   string `json:"key"`
	Value string `json:"value,omitempty"`
}

type DeviceV2BatchLabelsReq struct {
	Codes          []string                       `json:"codes"`
	GroupTagAction *DeviceV2BatchGroupTagAction  `json:"group_tag_action,omitempty"`
	LabelActions   []DeviceV2BatchLabelAction    `json:"label_actions,omitempty"`
}

type DeviceV2BatchLabelsItemResp struct {
	Code    string `json:"code"`
	Success bool   `json:"success"`
	Message string `json:"message,omitempty"`
}

type DeviceV2BatchLabelsResp struct {
	Total   int                           `json:"total"`
	Success int                           `json:"success"`
	Failed  int                           `json:"failed"`
	Items   []DeviceV2BatchLabelsItemResp `json:"items"`
}
```

- [x] **Step 2: Add service method to interface**

Add this method to `IDeviceV2` in `OneOps/app/device/v2/service/i_device_v2.go`:

```go
	BatchLabels(ctx context.Context, req dto.DeviceV2BatchLabelsReq) (dto.DeviceV2BatchLabelsResp, error)
```

- [x] **Step 3: Run compile check and expect missing implementation**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/device/v2/service/... ./app/device/v2/api/...
```

Expected: FAIL with errors that `DeviceV2Srv` or test stubs do not implement `BatchLabels`.

---

## Task 2: Service Validation And Mutation Tests

**Files:**
- Create: `OneOps/app/device/v2/service/impl/device_v2_batch_labels_test.go`
- Modify: `OneOps/app/device/v2/service/impl/device_v2_minimal_attributes.go`

- [x] **Step 1: Write failing service tests**

Create `OneOps/app/device/v2/service/impl/device_v2_batch_labels_test.go` with these tests:

```go
package impl

import (
	"context"
	"strings"
	"testing"

	devv2dto "github.com/netxops/OneOps/app/device/v2/dto"
	devv2model "github.com/netxops/OneOps/app/device/v2/model"
	"github.com/netxops/OneOps/types"
)

func seedBatchLabelDevice(t *testing.T, srv *DeviceV2Srv, code string, labels map[string]string, attrs map[string]interface{}, groupTags []string) {
	t.Helper()
	if attrs == nil {
		attrs = map[string]interface{}{
			"platform_code": "linux",
			"catalog_code":  "server",
			"site_code":     "SITE-A",
			"rack_code":     "RACK-A",
		}
	}
	_, err := srv.Create(context.Background(), code, code, "Batch Label "+code, "linux", "active", labels, attrs, map[string]interface{}{"owner": "seed"}, groupTags)
	if err != nil {
		t.Fatalf("seed device %s failed: %v", code, err)
	}
}

func TestDeviceV2Srv_BatchLabelsAppendsAndSetsLabels(t *testing.T) {
	db := openDeviceV2ProjectionTestDB(t)
	srv := NewDeviceV2Srv(types.DBTypeMySQL(db), nil, nil, nil)
	seedBatchLabelDevice(t, srv, "DVC-BATCH-LABEL-A", map[string]string{"env": "dev"}, nil, []string{"old"})
	seedBatchLabelDevice(t, srv, "DVC-BATCH-LABEL-B", map[string]string{}, nil, []string{})

	resp, err := srv.BatchLabels(context.Background(), devv2dto.DeviceV2BatchLabelsReq{
		Codes: []string{"DVC-BATCH-LABEL-A", "DVC-BATCH-LABEL-B"},
		GroupTagAction: &devv2dto.DeviceV2BatchGroupTagAction{
			Mode: devv2dto.DeviceV2GroupTagModeAppend,
			Tags: []string{"core", "old", "core"},
		},
		LabelActions: []devv2dto.DeviceV2BatchLabelAction{
			{Op: devv2dto.DeviceV2LabelActionSet, Key: "env", Value: "prod"},
			{Op: devv2dto.DeviceV2LabelActionSet, Key: "owner", Value: "ops"},
		},
	})
	if err != nil {
		t.Fatalf("BatchLabels failed: %v", err)
	}
	if resp.Total != 2 || resp.Success != 2 || resp.Failed != 0 {
		t.Fatalf("unexpected response: %+v", resp)
	}

	for _, code := range []string{"DVC-BATCH-LABEL-A", "DVC-BATCH-LABEL-B"} {
		got, err := srv.GetByCode(context.Background(), code)
		if err != nil || got == nil {
			t.Fatalf("load %s failed: %v", code, err)
		}
		if got.Labels["env"] != "prod" || got.Labels["owner"] != "ops" {
			t.Fatalf("unexpected labels for %s: %+v", code, got.Labels)
		}
		if strings.Join(got.GroupTags, ",") != "old,core" && strings.Join(got.GroupTags, ",") != "core,old" {
			t.Fatalf("unexpected group tags for %s: %+v", code, got.GroupTags)
		}
		if got.Attributes["catalog_code"] != "server" || got.Metadata["owner"] != "seed" || got.PlatformCode != "linux" {
			t.Fatalf("batch labels should preserve existing fields: %+v", got)
		}
	}
}

func TestDeviceV2Srv_BatchLabelsRemoveReplaceAndUnset(t *testing.T) {
	db := openDeviceV2ProjectionTestDB(t)
	srv := NewDeviceV2Srv(types.DBTypeMySQL(db), nil, nil, nil)
	seedBatchLabelDevice(t, srv, "DVC-BATCH-LABEL-C", map[string]string{"env": "prod", "owner": "ops"}, nil, []string{"old", "core"})

	resp, err := srv.BatchLabels(context.Background(), devv2dto.DeviceV2BatchLabelsReq{
		Codes: []string{"DVC-BATCH-LABEL-C"},
		GroupTagAction: &devv2dto.DeviceV2BatchGroupTagAction{
			Mode: devv2dto.DeviceV2GroupTagModeReplace,
			Tags: []string{"new-zone"},
		},
		LabelActions: []devv2dto.DeviceV2BatchLabelAction{
			{Op: devv2dto.DeviceV2LabelActionUnset, Key: "owner"},
		},
	})
	if err != nil {
		t.Fatalf("BatchLabels failed: %v", err)
	}
	if resp.Success != 1 || resp.Failed != 0 {
		t.Fatalf("unexpected response: %+v", resp)
	}
	got, err := srv.GetByCode(context.Background(), "DVC-BATCH-LABEL-C")
	if err != nil || got == nil {
		t.Fatalf("load device failed: %v", err)
	}
	if got.Labels["env"] != "prod" {
		t.Fatalf("env should remain, labels=%+v", got.Labels)
	}
	if _, ok := got.Labels["owner"]; ok {
		t.Fatalf("owner should be unset, labels=%+v", got.Labels)
	}
	if len(got.GroupTags) != 1 || got.GroupTags[0] != "new-zone" {
		t.Fatalf("tags should be replaced: %+v", got.GroupTags)
	}
}

func TestDeviceV2Srv_BatchLabelsValidationAndPartialFailure(t *testing.T) {
	db := openDeviceV2ProjectionTestDB(t)
	srv := NewDeviceV2Srv(types.DBTypeMySQL(db), nil, nil, nil)
	seedBatchLabelDevice(t, srv, "DVC-BATCH-LABEL-D", map[string]string{}, nil, []string{})

	_, err := srv.BatchLabels(context.Background(), devv2dto.DeviceV2BatchLabelsReq{
		Codes: []string{"DVC-BATCH-LABEL-D"},
		LabelActions: []devv2dto.DeviceV2BatchLabelAction{
			{Op: devv2dto.DeviceV2LabelActionSet, Key: "env", Value: "prod"},
			{Op: devv2dto.DeviceV2LabelActionUnset, Key: "env"},
		},
	})
	if err == nil || !strings.Contains(err.Error(), "重复") {
		t.Fatalf("expected duplicate label action error, got %v", err)
	}

	resp, err := srv.BatchLabels(context.Background(), devv2dto.DeviceV2BatchLabelsReq{
		Codes: []string{"DVC-BATCH-LABEL-D", "DVC-BATCH-LABEL-MISSING"},
		GroupTagAction: &devv2dto.DeviceV2BatchGroupTagAction{
			Mode: devv2dto.DeviceV2GroupTagModeAppend,
			Tags: []string{"ops"},
		},
	})
	if err != nil {
		t.Fatalf("partial batch should not return request error: %v", err)
	}
	if resp.Total != 2 || resp.Success != 1 || resp.Failed != 1 || len(resp.Items) != 2 {
		t.Fatalf("unexpected partial response: %+v", resp)
	}
	if !resp.Items[0].Success || resp.Items[1].Success || resp.Items[1].Message == "" {
		t.Fatalf("unexpected item results: %+v", resp.Items)
	}
}

var _ = devv2model.EntityTypeDeviceV2
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/device/v2/service/impl -run 'TestDeviceV2Srv_BatchLabels' -count=1
```

Expected: FAIL because `BatchLabels` is undefined.

- [x] **Step 3: Implement service helpers**

Add these helpers near `buildEntitySourceForWrite` in `OneOps/app/device/v2/service/impl/device_v2_minimal_attributes.go`:

```go
const deviceV2BatchLabelsLimit = 200

func normalizeDeviceV2BatchStringList(values []string) []string {
	seen := map[string]struct{}{}
	out := make([]string, 0, len(values))
	for _, value := range values {
		value = strings.TrimSpace(value)
		if value == "" {
			continue
		}
		if _, ok := seen[value]; ok {
			continue
		}
		seen[value] = struct{}{}
		out = append(out, value)
	}
	return out
}

func validateDeviceV2LabelKey(key string) error {
	key = strings.TrimSpace(key)
	if key == "" {
		return fmt.Errorf("标签键不能为空")
	}
	for _, r := range key {
		if (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z') || (r >= '0' && r <= '9') || r == '_' || r == '-' || r == '.' {
			continue
		}
		return fmt.Errorf("标签键 %q 包含非法字符", key)
	}
	return nil
}

func validateDeviceV2BatchLabelsReq(req devv2dto.DeviceV2BatchLabelsReq) ([]string, error) {
	codes := normalizeDeviceV2BatchStringList(req.Codes)
	if len(codes) == 0 {
		return nil, fmt.Errorf("请选择至少一台设备")
	}
	if len(codes) > deviceV2BatchLabelsLimit {
		return nil, fmt.Errorf("单次最多支持 %d 台设备", deviceV2BatchLabelsLimit)
	}
	hasOperation := false
	if req.GroupTagAction != nil {
		mode := strings.TrimSpace(req.GroupTagAction.Mode)
		if mode != devv2dto.DeviceV2GroupTagModeAppend && mode != devv2dto.DeviceV2GroupTagModeRemove && mode != devv2dto.DeviceV2GroupTagModeReplace {
			return nil, fmt.Errorf("短标签操作模式非法")
		}
		if len(normalizeDeviceV2BatchStringList(req.GroupTagAction.Tags)) == 0 && mode != devv2dto.DeviceV2GroupTagModeReplace {
			return nil, fmt.Errorf("短标签不能为空")
		}
		hasOperation = true
	}
	seenLabelKeys := map[string]struct{}{}
	for _, action := range req.LabelActions {
		op := strings.TrimSpace(action.Op)
		key := strings.TrimSpace(action.Key)
		if op != devv2dto.DeviceV2LabelActionSet && op != devv2dto.DeviceV2LabelActionUnset {
			return nil, fmt.Errorf("标签操作非法")
		}
		if err := validateDeviceV2LabelKey(key); err != nil {
			return nil, err
		}
		if _, ok := seenLabelKeys[key]; ok {
			return nil, fmt.Errorf("标签 %s 存在重复操作", key)
		}
		seenLabelKeys[key] = struct{}{}
		if op == devv2dto.DeviceV2LabelActionSet && strings.TrimSpace(action.Value) == "" {
			return nil, fmt.Errorf("标签 %s 的值不能为空", key)
		}
		hasOperation = true
	}
	if !hasOperation {
		return nil, fmt.Errorf("请至少配置一项标签操作")
	}
	return codes, nil
}

func applyDeviceV2GroupTagAction(current []string, action *devv2dto.DeviceV2BatchGroupTagAction) []string {
	if action == nil {
		return normalizeDeviceV2BatchStringList(current)
	}
	tags := normalizeDeviceV2BatchStringList(action.Tags)
	switch strings.TrimSpace(action.Mode) {
	case devv2dto.DeviceV2GroupTagModeReplace:
		return tags
	case devv2dto.DeviceV2GroupTagModeRemove:
		remove := map[string]struct{}{}
		for _, tag := range tags {
			remove[tag] = struct{}{}
		}
		out := make([]string, 0, len(current))
		for _, tag := range normalizeDeviceV2BatchStringList(current) {
			if _, ok := remove[tag]; !ok {
				out = append(out, tag)
			}
		}
		return out
	default:
		return normalizeDeviceV2BatchStringList(append(normalizeDeviceV2BatchStringList(current), tags...))
	}
}

func applyDeviceV2LabelActions(current map[string]string, actions []devv2dto.DeviceV2BatchLabelAction) map[string]string {
	next := cloneStringMap(current)
	if next == nil {
		next = map[string]string{}
	}
	for _, action := range actions {
		key := strings.TrimSpace(action.Key)
		if strings.TrimSpace(action.Op) == devv2dto.DeviceV2LabelActionUnset {
			delete(next, key)
			continue
		}
		next[key] = strings.TrimSpace(action.Value)
	}
	return next
}
```

- [x] **Step 4: Implement `BatchLabels`**

Add this method in `OneOps/app/device/v2/service/impl/device_v2_minimal_attributes.go`:

```go
func (s *DeviceV2Srv) BatchLabels(ctx context.Context, req devv2dto.DeviceV2BatchLabelsReq) (devv2dto.DeviceV2BatchLabelsResp, error) {
	codes, err := validateDeviceV2BatchLabelsReq(req)
	if err != nil {
		return devv2dto.DeviceV2BatchLabelsResp{}, err
	}
	resp := devv2dto.DeviceV2BatchLabelsResp{
		Total: len(codes),
		Items: make([]devv2dto.DeviceV2BatchLabelsItemResp, 0, len(codes)),
	}
	for _, code := range codes {
		item := devv2dto.DeviceV2BatchLabelsItemResp{Code: code}
		current, err := s.GetByCode(ctx, code)
		if err != nil {
			item.Message = err.Error()
		} else if current == nil {
			item.Message = "设备不存在"
		} else {
			nextLabels := applyDeviceV2LabelActions(current.Labels, req.LabelActions)
			nextGroupTags := applyDeviceV2GroupTagAction(current.GroupTags, req.GroupTagAction)
			updated, err := s.Update(ctx, code, current.Name, current.PlatformCode, current.Status, nextLabels, current.Attributes, current.Metadata, nextGroupTags)
			if err != nil {
				item.Message = err.Error()
			} else if updated == nil {
				item.Message = "设备不存在"
			} else {
				item.Success = true
			}
		}
		if item.Success {
			resp.Success += 1
		} else {
			resp.Failed += 1
		}
		resp.Items = append(resp.Items, item)
	}
	return resp, nil
}
```

Ensure the file imports the DTO package with alias:

```go
devv2dto "github.com/netxops/OneOps/app/device/v2/dto"
```

- [x] **Step 5: Run service tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/device/v2/service/impl -run 'TestDeviceV2Srv_BatchLabels' -count=1
```

Expected: PASS.

---

## Task 3: API Handler And Route

**Files:**
- Create: `OneOps/app/device/v2/api/device_v2_batch_labels_api_test.go`
- Modify: `OneOps/app/device/v2/api/device_v2.go`
- Modify: `OneOps/app/device/v2/router/device_v2.go`
- Modify: Device V2 API test stubs that implement `IDeviceV2`

- [x] **Step 1: Write failing API tests**

Create `OneOps/app/device/v2/api/device_v2_batch_labels_api_test.go`:

```go
package api

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"

	devv2dto "github.com/netxops/OneOps/app/device/v2/dto"
	devv2model "github.com/netxops/OneOps/app/device/v2/model"
	"github.com/gin-gonic/gin"
)

func TestDeviceV2API_BatchLabelsReturnsServiceResult(t *testing.T) {
	gin.SetMode(gin.TestMode)
	captured := devv2dto.DeviceV2BatchLabelsReq{}
	api := &DeviceV2API{
		DeviceV2Srv: &deviceV2ServiceStub{
			batchLabelsFn: func(ctx context.Context, req devv2dto.DeviceV2BatchLabelsReq) (devv2dto.DeviceV2BatchLabelsResp, error) {
				captured = req
				return devv2dto.DeviceV2BatchLabelsResp{
					Total: 2, Success: 1, Failed: 1,
					Items: []devv2dto.DeviceV2BatchLabelsItemResp{
						{Code: "DVC001", Success: true},
						{Code: "DVC404", Success: false, Message: "设备不存在"},
					},
				}, nil
			},
		},
	}
	body := bytes.NewBufferString(`{"codes":["DVC001","DVC404"],"group_tag_action":{"mode":"append","tags":["core"]},"label_actions":[{"op":"set","key":"env","value":"prod"}]}`)
	ctx, recorder := createGinTestContext(http.MethodPost, "/device/v2/batch-labels", body)
	api.BatchLabels(ctx)

	if recorder.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d body=%s", recorder.Code, recorder.Body.String())
	}
	if len(captured.Codes) != 2 || captured.Codes[0] != "DVC001" || captured.LabelActions[0].Key != "env" {
		t.Fatalf("unexpected captured request: %+v", captured)
	}
	var payload struct {
		Code int                          `json:"code"`
		Data devv2dto.DeviceV2BatchLabelsResp `json:"data"`
	}
	if err := json.Unmarshal(recorder.Body.Bytes(), &payload); err != nil {
		t.Fatalf("decode response failed: %v", err)
	}
	if payload.Code != 0 || payload.Data.Success != 1 || payload.Data.Failed != 1 {
		t.Fatalf("unexpected payload: %+v", payload)
	}
}

func TestDeviceV2API_BatchLabelsRejectsServiceValidationError(t *testing.T) {
	gin.SetMode(gin.TestMode)
	api := &DeviceV2API{
		DeviceV2Srv: &deviceV2ServiceStub{
			batchLabelsFn: func(ctx context.Context, req devv2dto.DeviceV2BatchLabelsReq) (devv2dto.DeviceV2BatchLabelsResp, error) {
				return devv2dto.DeviceV2BatchLabelsResp{}, errors.New("请选择至少一台设备")
			},
		},
	}
	ctx, recorder := createGinTestContext(http.MethodPost, "/device/v2/batch-labels", bytes.NewBufferString(`{"codes":[]}`))
	api.BatchLabels(ctx)
	if recorder.Code == http.StatusOK {
		t.Fatalf("expected failure response, got %s", recorder.Body.String())
	}
}

func createGinTestContext(method, path string, body *bytes.Buffer) (*gin.Context, *httptest.ResponseRecorder) {
	recorder := httptest.NewRecorder()
	ctx, _ := gin.CreateTestContext(recorder)
	ctx.Request = httptest.NewRequest(method, path, body)
	ctx.Request.Header.Set("Content-Type", "application/json")
	return ctx, recorder
}

var _ = devv2model.EntityTypeDeviceV2
```

- [x] **Step 2: Extend API test stubs**

Find `deviceV2ServiceStub` in `OneOps/app/device/v2/api/device_v2_migration_api_test.go` and add:

```go
	batchLabelsFn func(ctx context.Context, req devv2dto.DeviceV2BatchLabelsReq) (devv2dto.DeviceV2BatchLabelsResp, error)
```

Add this method:

```go
func (s *deviceV2ServiceStub) BatchLabels(ctx context.Context, req devv2dto.DeviceV2BatchLabelsReq) (devv2dto.DeviceV2BatchLabelsResp, error) {
	if s.batchLabelsFn != nil {
		return s.batchLabelsFn(ctx, req)
	}
	return devv2dto.DeviceV2BatchLabelsResp{}, nil
}
```

Apply the same method to any other local fake that must satisfy `IDeviceV2`, such as base-reference-check fakes.

- [x] **Step 3: Run API tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/device/v2/api -run 'TestDeviceV2API_BatchLabels' -count=1
```

Expected: FAIL because `DeviceV2API.BatchLabels` is undefined or the route is not registered.

- [x] **Step 4: Implement API handler**

Add this method to `OneOps/app/device/v2/api/device_v2.go` near `Update`:

```go
func (a *DeviceV2API) BatchLabels(ctx *gin.Context) {
	var req dto.DeviceV2BatchLabelsReq
	if ok := bind.JSON(&req, ctx); !ok {
		return
	}
	c := a.requestContextWithDeviceV2Audit(ctx, ctx.Request.Context(), model.DeviceV2ChangeSourceManualAPI)
	result, err := a.DeviceV2Srv.BatchLabels(c, req)
	if err != nil {
		failWithDeviceV2OutputError(ctx, standardizeDeviceV2RequestValidationError(err.Error(), "device_v2", "batch_labels", "标签操作参数错误，请检查后重试。"))
		return
	}
	response.OkWithData(result, ctx)
}
```

- [x] **Step 5: Register route**

Add this route before `g.POST("", deviceV2API.Create)` in `OneOps/app/device/v2/router/device_v2.go`:

```go
	g.POST("batch-labels", deviceV2API.BatchLabels)
```

- [x] **Step 6: Run API tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/device/v2/api -run 'TestDeviceV2API_BatchLabels' -count=1
```

Expected: PASS.

---

## Task 4: Frontend API Client

**Files:**
- Modify: `OneOPS-UI/src/api/device/device-v2.ts`

- [x] **Step 1: Add frontend types**

Add these interfaces after `DeviceV2UpdateReq`:

```ts
export type DeviceV2GroupTagMode = 'append' | 'remove' | 'replace';
export type DeviceV2LabelActionOp = 'set' | 'unset';

export interface DeviceV2BatchGroupTagAction {
  mode: DeviceV2GroupTagMode;
  tags: string[];
}

export interface DeviceV2BatchLabelAction {
  op: DeviceV2LabelActionOp;
  key: string;
  value?: string;
}

export interface DeviceV2BatchLabelsReq {
  codes: string[];
  group_tag_action?: DeviceV2BatchGroupTagAction;
  label_actions?: DeviceV2BatchLabelAction[];
}

export interface DeviceV2BatchLabelsItemResp {
  code: string;
  success: boolean;
  message?: string;
}

export interface DeviceV2BatchLabelsResp {
  total: number;
  success: number;
  failed: number;
  items: DeviceV2BatchLabelsItemResp[];
}
```

- [x] **Step 2: Add response assertion and request helper**

Add this helper near other Device V2 request helpers:

```ts
function assertDeviceV2BatchLabelsResp(value: unknown): DeviceV2BatchLabelsResp {
  if (!value || typeof value !== 'object') {
    throw new Error('Device V2 批量标签返回格式错误：缺少响应对象');
  }
  const resp = value as DeviceV2BatchLabelsResp;
  if (typeof resp.total !== 'number' || typeof resp.success !== 'number' || typeof resp.failed !== 'number') {
    throw new Error('Device V2 批量标签返回格式错误：缺少统计字段');
  }
  if (!Array.isArray(resp.items)) {
    throw new Error('Device V2 批量标签返回格式错误：缺少 items');
  }
  return resp;
}

export const batchUpdateDeviceV2LabelsReq = async (data: DeviceV2BatchLabelsReq) => {
  const envelope = await requestEnvelope<DeviceV2BatchLabelsResp>({
    url: `${BASE}/batch-labels`,
    method: HTTP_POST,
    data,
  });
  if (!envelope || envelope.code !== 0) {
    throw new Error(envelope?.msg || '批量打标签失败：后端未返回错误消息');
  }
  return assertDeviceV2BatchLabelsResp(envelope.data);
};
```

- [x] **Step 3: Run frontend typecheck**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
npm run typecheck:d2
```

Expected: PASS.

---

## Task 5: Frontend Playwright Test

**Files:**
- Create: `OneOps/scripts/platform2_multi_agent_test/agents/device_v2_tagging.spec.ts`
- Modify: `OneOps/scripts/platform2_multi_agent_test/package.json`

- [x] **Step 1: Add failing Playwright spec**

Create `OneOps/scripts/platform2_multi_agent_test/agents/device_v2_tagging.spec.ts`:

```ts
import { test, expect } from '@playwright/test';
import { playwrightLogin } from '../shared/playwright_login';
import { getAuthToken } from '../shared/frontend_task_execution_real';
import { buildDeviceV2CrudSeed, deleteDeviceV2IfExists, ensureDeviceV2, getDeviceV2 } from '../shared/device_v2_api';

test.describe('Device V2 tagging', () => {
  test('selected devices can receive short tags and key-value labels', async ({ page }) => {
    const code = `E2E_D2_TAG_${Date.now()}`;
    await playwrightLogin(page);
    const token = await getAuthToken(page);
    const seed = buildDeviceV2CrudSeed(code);
    seed.labels = { env: 'dev' };
    seed.group_tags = ['old-tag'];
    await ensureDeviceV2(page, token, seed);

    try {
      await page.goto(`/#/device/device-v2-management?codes=${encodeURIComponent(code)}`);
      const row = page.locator('.device-table tbody tr').filter({ hasText: code }).first();
      await expect(row).toBeVisible({ timeout: 60000 });
      await row.locator('input[type="checkbox"]').check({ force: true });

      await page.getByRole('button', { name: '打标签' }).click();
      const dialog = page.getByRole('dialog', { name: '设备打标签' });
      await expect(dialog).toBeVisible();

      await dialog.getByLabel('短标签操作').click();
      await page.getByRole('option', { name: '追加标签' }).click();
      await dialog.locator('.tagging-group-tags .ant-select-selector').click();
      await page.keyboard.type('core');
      await page.keyboard.press('Enter');

      await dialog.getByPlaceholder('标签键，如 env').fill('env');
      await dialog.getByPlaceholder('标签值，如 prod').fill('prod');
      await dialog.getByRole('button', { name: '确认打标签' }).click();
      await expect(page.getByText(/打标签完成|已为/)).toBeVisible({ timeout: 60000 });

      const saved = await getDeviceV2(page, token, code);
      expect(saved?.labels?.env).toBe('prod');
      expect(saved?.group_tags || []).toContain('old-tag');
      expect(saved?.group_tags || []).toContain('core');

      await page.getByRole('button', { name: '添加条件' }).click();
      const firstRow = page.locator('.query-builder__row').first();
      await firstRow.locator('.query-builder__field').click();
      await page.getByRole('option', { name: /env/ }).click();
      await firstRow.locator('.query-builder__value input').fill('prod');
      await page.getByRole('button', { name: '查询' }).click();
      await expect(page.getByText(code)).toBeVisible({ timeout: 60000 });
    } finally {
      await deleteDeviceV2IfExists(page, token, code);
    }
  });
});
```

- [x] **Step 2: Add npm script**

Add to `OneOps/scripts/platform2_multi_agent_test/package.json`:

```json
"test:device-v2:tagging": "playwright test agents/device_v2_tagging.spec.ts"
```

- [x] **Step 3: Run spec to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps/scripts/platform2_multi_agent_test
ONEOPS_UI_URL=http://127.0.0.1:3001 ONEOPS_API_URL=http://127.0.0.1:8280/api/v1 npm run test:device-v2:tagging
```

Expected: FAIL because the `打标签` button and modal do not exist yet.

---

## Task 6: Frontend Tagging Modal Implementation

**Files:**
- Modify: `OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue`

- [x] **Step 1: Import new API and types**

Extend the import from `@/api/device/device-v2`:

```ts
  batchUpdateDeviceV2LabelsReq,
  type DeviceV2BatchLabelAction,
  type DeviceV2BatchLabelsResp,
  type DeviceV2GroupTagMode,
```

- [x] **Step 2: Add batch toolbar and row action entry**

In the batch toolbar near `批量删除`, add:

```vue
            <a-button :disabled="!selectedRowKeys.length" @click="openBatchTagging(selectedCodes)">
              打标签
            </a-button>
```

In the row action menu after `编辑`, add:

```vue
                    <a-menu-item key="tagging" @click="openBatchTagging([record.code])">标签</a-menu-item>
```

- [x] **Step 3: Add modal template**

Add this modal near existing edit/delete modals:

```vue
    <a-modal
      v-model:open="taggingModalVisible"
      title="设备打标签"
      width="640px"
      :confirm-loading="taggingSubmitting"
      ok-text="确认打标签"
      cancel-text="取消"
      @ok="submitTagging"
      @cancel="closeTaggingModal"
    >
      <div class="tagging-editor">
        <a-alert
          type="info"
          show-icon
          :message="`将应用到 ${taggingTargetCodes.length} 台设备`"
          style="margin-bottom: 12px"
        />
        <section class="tagging-editor__section">
          <div class="tagging-editor__title">短标签</div>
          <a-form layout="vertical">
            <a-form-item label="短标签操作">
              <a-select
                v-model:value="taggingGroupTagMode"
                aria-label="短标签操作"
                :options="taggingGroupTagModeOptions"
              />
            </a-form-item>
            <a-form-item label="短标签">
              <a-select
                v-model:value="taggingGroupTags"
                class="tagging-group-tags"
                mode="tags"
                :options="taggingGroupTagOptions"
                placeholder="输入后回车，例如 core、hx-mm"
              />
            </a-form-item>
          </a-form>
        </section>
        <section class="tagging-editor__section">
          <div class="tagging-editor__title">键值标签</div>
          <div class="tagging-label-rows">
            <div v-for="row in taggingLabelRows" :key="row.id" class="tagging-label-row">
              <a-select v-model:value="row.op" :options="taggingLabelOpOptions" class="tagging-label-row__op" />
              <a-auto-complete
                v-model:value="row.key"
                :options="taggingLabelKeyOptions"
                class="tagging-label-row__key"
                placeholder="标签键，如 env"
              />
              <a-input
                v-if="row.op === 'set'"
                v-model:value="row.value"
                class="tagging-label-row__value"
                placeholder="标签值，如 prod"
              />
              <span v-else class="tagging-label-row__unset">清除该标签</span>
              <a-button type="text" danger @click="removeTaggingLabelRow(row.id)">
                <template #icon><DeleteOutlined /></template>
              </a-button>
            </div>
          </div>
          <a-button type="dashed" size="small" @click="addTaggingLabelRow">添加键值标签</a-button>
        </section>
        <section class="tagging-editor__section">
          <div class="tagging-editor__title">操作预览</div>
          <a-empty v-if="!taggingPreviewLines.length" :image="false" description="尚未配置标签操作" />
          <ul v-else class="tagging-preview">
            <li v-for="line in taggingPreviewLines" :key="line">{{ line }}</li>
          </ul>
        </section>
      </div>
    </a-modal>
```

- [x] **Step 4: Add reactive state and helpers**

Add script state near other edit modal refs:

```ts
interface TaggingLabelRow {
  id: string;
  op: 'set' | 'unset';
  key: string;
  value: string;
}

const taggingModalVisible = ref(false);
const taggingSubmitting = ref(false);
const taggingTargetCodes = ref<string[]>([]);
const taggingGroupTagMode = ref<DeviceV2GroupTagMode>('append');
const taggingGroupTags = ref<string[]>([]);
const taggingLabelRows = ref<TaggingLabelRow[]>([]);
const taggingResult = ref<DeviceV2BatchLabelsResp | null>(null);
let taggingRowSeed = 0;

const taggingGroupTagModeOptions: SelectOption[] = [
  { label: '追加标签', value: 'append' },
  { label: '移除标签', value: 'remove' },
  { label: '替换为这些标签', value: 'replace' },
];
const taggingLabelOpOptions: SelectOption[] = [
  { label: '设置', value: 'set' },
  { label: '清除', value: 'unset' },
];
const taggingGroupTagOptions = computed<SelectOption[]>(() => {
  const tags = new Set<string>();
  sourceDevices.value.forEach(device => (device.group_tags || []).forEach(tag => tags.add(String(tag || '').trim())));
  return Array.from(tags)
    .filter(Boolean)
    .sort((left, right) => left.localeCompare(right, 'zh-Hans-CN'))
    .map(tag => ({ label: tag, value: tag }));
});
const taggingLabelKeyOptions = computed<SelectOption[]>(() =>
  (deviceSchema.value?.labels_schema || [])
    .map(item => String(item.key || '').trim())
    .filter(Boolean)
    .map(key => ({ label: key, value: key })),
);
```

Add helper functions:

```ts
function createTaggingLabelRow(): TaggingLabelRow {
  taggingRowSeed += 1;
  return { id: `tagging-label-${taggingRowSeed}`, op: 'set', key: '', value: '' };
}

function normalizedTaggingTags() {
  return Array.from(new Set((taggingGroupTags.value || []).map(item => String(item || '').trim()).filter(Boolean)));
}

function normalizedTaggingLabelActions(): DeviceV2BatchLabelAction[] {
  return taggingLabelRows.value
    .map(row => ({
      op: row.op,
      key: String(row.key || '').trim(),
      value: row.op === 'set' ? String(row.value || '').trim() : undefined,
    }))
    .filter(action => action.key);
}

const taggingPreviewLines = computed(() => {
  const lines: string[] = [];
  const tags = normalizedTaggingTags();
  if (tags.length) {
    const label = taggingGroupTagMode.value === 'remove' ? '移除短标签' : taggingGroupTagMode.value === 'replace' ? '替换短标签为' : '追加短标签';
    lines.push(`${label}：${tags.join('、')}`);
  }
  normalizedTaggingLabelActions().forEach(action => {
    lines.push(action.op === 'unset' ? `清除标签：${action.key}` : `设置标签：${action.key}=${action.value || ''}`);
  });
  return lines;
});

function openBatchTagging(codes: string[]) {
  taggingTargetCodes.value = Array.from(new Set(codes.map(code => String(code || '').trim()).filter(Boolean)));
  taggingGroupTagMode.value = 'append';
  taggingGroupTags.value = [];
  taggingLabelRows.value = [createTaggingLabelRow()];
  taggingResult.value = null;
  taggingModalVisible.value = true;
}

function closeTaggingModal() {
  taggingModalVisible.value = false;
  taggingSubmitting.value = false;
}

function addTaggingLabelRow() {
  taggingLabelRows.value.push(createTaggingLabelRow());
}

function removeTaggingLabelRow(id: string) {
  taggingLabelRows.value = taggingLabelRows.value.filter(row => row.id !== id);
  if (!taggingLabelRows.value.length) taggingLabelRows.value = [createTaggingLabelRow()];
}

function validateTaggingPayload(actions: DeviceV2BatchLabelAction[], tags: string[]) {
  if (!taggingTargetCodes.value.length) return '请选择需要打标签的设备';
  const activeActions = actions.filter(action => action.key);
  if (!tags.length && !activeActions.length) return '请至少配置一项标签操作';
  const seen = new Set<string>();
  for (const action of activeActions) {
    if (seen.has(action.key)) return `标签 ${action.key} 存在重复操作`;
    seen.add(action.key);
    if (action.op === 'set' && !String(action.value || '').trim()) return `请填写标签 ${action.key} 的值`;
  }
  return '';
}
```

- [x] **Step 5: Add submit handling**

Add:

```ts
async function submitTagging() {
  const tags = normalizedTaggingTags();
  const labelActions = normalizedTaggingLabelActions();
  const validationMessage = validateTaggingPayload(labelActions, tags);
  if (validationMessage) {
    message.warning(validationMessage);
    return;
  }
  taggingSubmitting.value = true;
  try {
    const result = await batchUpdateDeviceV2LabelsReq({
      codes: taggingTargetCodes.value,
      group_tag_action: tags.length ? { mode: taggingGroupTagMode.value, tags } : undefined,
      label_actions: labelActions.length ? labelActions : undefined,
    });
    taggingResult.value = result;
    if (result.failed) {
      Modal.warning({
        title: '部分设备打标签失败',
        content: h(
          'div',
          {},
          result.items
            .filter(item => !item.success)
            .map(item => h('p', { key: item.code }, `${item.code}：${item.message || '失败'}`)),
        ),
      });
    } else {
      message.success(`已为 ${result.success} 台设备打标签`);
    }
    closeTaggingModal();
    await reloadDevices();
    if (savedGroupingLevels.value.some(level => level.source === 'label')) {
      await performGrouping(savedGroupingLevels.value, { reloadList: false, resetSelection: false });
    }
  } catch (error) {
    message.error(error instanceof Error ? error.message : '批量打标签失败');
  } finally {
    taggingSubmitting.value = false;
  }
}
```

- [x] **Step 6: Add modal CSS**

Add styles near edit modal CSS:

```css
.tagging-editor {
  display: grid;
  gap: 14px;
}

.tagging-editor__section {
  display: grid;
  gap: 10px;
  padding: 12px;
  border: 1px solid #eef2f6;
  border-radius: 8px;
  background: #fff;
}

.tagging-editor__title {
  color: #1f2329;
  font-size: 13px;
  font-weight: 700;
}

.tagging-label-rows {
  display: grid;
  gap: 8px;
}

.tagging-label-row {
  display: grid;
  grid-template-columns: 88px minmax(120px, 1fr) minmax(150px, 1fr) 32px;
  gap: 8px;
  align-items: center;
}

.tagging-label-row__op,
.tagging-label-row__key,
.tagging-label-row__value {
  min-width: 0;
}

.tagging-label-row__unset {
  color: #667085;
  font-size: 13px;
}

.tagging-preview {
  margin: 0;
  padding-left: 18px;
  color: #475467;
  font-size: 13px;
  line-height: 1.7;
}
```

- [x] **Step 7: Run frontend checks**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
npm run typecheck:d2
```

Expected: PASS.

---

## Task 7: End-To-End Verification And Regression

**Files:**
- Verify only.

- [x] **Step 1: Run backend service/API tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/device/v2/service/impl -run 'TestDeviceV2Srv_BatchLabels' -count=1
go test ./app/device/v2/api -run 'TestDeviceV2API_BatchLabels' -count=1
```

Expected: PASS.

- [x] **Step 2: Run broader Device V2 backend tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/device/v2/...
```

Expected: PASS.

- [x] **Step 3: Run frontend typecheck**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
npm run typecheck:d2
```

Expected: PASS.

- [x] **Step 4: Run Playwright tagging test**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps/scripts/platform2_multi_agent_test
ONEOPS_UI_URL=http://127.0.0.1:3001 ONEOPS_API_URL=http://127.0.0.1:8280/api/v1 npm run test:device-v2:tagging
```

Expected: PASS.

- [x] **Step 5: Run related Device V2 frontend regressions**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps/scripts/platform2_multi_agent_test
ONEOPS_UI_URL=http://127.0.0.1:3001 ONEOPS_API_URL=http://127.0.0.1:8280/api/v1 npm run test:device-v2:crud
ONEOPS_UI_URL=http://127.0.0.1:3001 ONEOPS_API_URL=http://127.0.0.1:8280/api/v1 npm run test:device-v2:flexible-search
ONEOPS_UI_URL=http://127.0.0.1:3001 ONEOPS_API_URL=http://127.0.0.1:8280/api/v1 npm run test:device-v2:grouping-fields
ONEOPS_UI_URL=http://127.0.0.1:3001 ONEOPS_API_URL=http://127.0.0.1:8280/api/v1 npm run test:device-v2:table-text
```

Expected: all PASS.

- [x] **Step 6: Run whitespace checks**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git diff --check
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git diff --check
```

Expected: no output.

---

## Self-Review

- Spec coverage:
  - Batch `group_tags` add/remove/replace: Task 2, Task 6.
  - Batch key-value `labels` set/unset: Task 2, Task 6.
  - Row shortcut: Task 6.
  - Backend batch API with per-device result: Task 1, Task 2, Task 3.
  - Frontend result handling and reload: Task 6.
  - Tests: Task 2, Task 3, Task 5, Task 7.
- Scope is selected-device only, matching the design's first iteration.
- No automatic tagging rules, taxonomy management, or all-filtered-result bulk action is included.
- Type names are consistent across DTO, service, API client, and UI plan sections.
