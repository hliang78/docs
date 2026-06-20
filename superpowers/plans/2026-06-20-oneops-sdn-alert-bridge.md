# OneOPS SDN Alert Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Project persisted SDN alarms into OneOPS unified `alert_alarm` records while keeping `platform_sdn_alarm` as the SDN evidence layer.

**Architecture:** CtrlHub remains vendor-only. OneOPS refreshes SDN alarms into `platform_sdn_alarm`, then synchronously bridges each changed alarm row into `alert_alarm` using stable `sdn:<controller_id>:<alarm_key>` identity. Ticket creation stays disabled by default because the bridge calls `AlertAlarmSrv.Create` directly and does not call `AlertTicketSrv.CreateFromAlert`.

**Tech Stack:** Go, Gin, GORM, OneOPS tenant scoping, existing alert services, Vue 3, TypeScript, Ant Design Vue, SDN smoke scripts.

---

## File Structure

Backend files in `/Users/huangliang/project/OneOPS-ALL/OneOPS`:

- Modify `app/platform/platform_model/sdn_controller.go`
  - Add bridge metadata fields to `SDNAlarm`.
- Modify `app/platform/dto/sdn_controller.go`
  - Return bridge metadata to API/UI.
- Modify `app/platform/service/impl/sdn_controller.go`
  - Add alert bridge dependency and production constructor.
  - Call bridge after refresh upsert/clear.
- Create `app/platform/service/impl/sdn_alert_bridge.go`
  - Build and upsert unified `alert_alarm` records.
- Modify `app/platform/service/impl/sdn_controller_test.go`
  - Add RED/GREEN tests for model/DTO fields and refresh bridge behavior.
- Modify `initialize/mysql.go`
  - AutoMigrate new SDN alarm bridge fields through model.
- Modify `cmd/wire_gen.go`
  - Wire `NewSDNControllerStoreWithAlertBridge` with `AlertAlarmSrv`.

Frontend files in `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI`:

- Modify `src/typings/platform/sdn-controller.ts`
  - Add alert bridge fields to `AlarmRecord`.
- Modify `src/views/device/SdnControllerManagement.vue`
  - Render bridge status and link to `/alert/alarm?code=<alert_alarm_code>`.
- Modify `scripts/sdn-resource-workbench-smoke.ts`
  - Assert unified alert code/status rendering.

Docs:

- This plan is the implementation source for the bridge.

## Safety Rules

- Do not add vendor-specific SDN clients to OneOPS.
- Do not modify CtrlHub for this bridge.
- Do not create alert tickets by default.
- Do not revert unrelated dirty files.
- Stage only SDN bridge files.
- Preserve existing confirmation fields when updating `alert_alarm`.
- Redact bridge errors before storing them on SDN alarm rows.

## Task 1: Backend Model And DTO Bridge Metadata

**Files:**

- Modify: `app/platform/platform_model/sdn_controller.go`
- Modify: `app/platform/dto/sdn_controller.go`
- Modify: `app/platform/service/impl/sdn_controller_test.go`

- [ ] **Step 1: Write failing model/DTO test**

Append this test in `app/platform/service/impl/sdn_controller_test.go` near `TestSDNAlarmModelAndDTOFields`:

```go
func TestSDNAlarmBridgeMetadataFields(t *testing.T) {
	t.Parallel()

	now := time.Date(2026, 6, 20, 17, 0, 0, 0, time.UTC)
	row := platformModel.SDNAlarm{
		ControllerID:     "ctrl-1",
		AlarmKey:         "ctrl-1|fault-1",
		AlertAlarmCode:   "AAM20260620000001",
		AlertSyncStatus:  "synced",
		AlertSyncError:   "",
		AlertSyncedAt:    &now,
	}
	if row.AlertAlarmCode != "AAM20260620000001" || row.AlertSyncedAt == nil {
		t.Fatalf("unexpected bridge metadata row %#v", row)
	}

	resp := dto.SDNAlarmRecord{
		ID:              "sdn-alarm-1",
		AlertAlarmCode:  "AAM20260620000001",
		AlertSyncStatus: "synced",
		AlertSyncedAt:   &now,
	}
	if resp.AlertAlarmCode == "" || resp.AlertSyncStatus != "synced" || resp.AlertSyncedAt == nil {
		t.Fatalf("unexpected bridge metadata resp %#v", resp)
	}
}
```

- [ ] **Step 2: Run RED**

Run:

```bash
go test ./app/platform/service/impl -run TestSDNAlarmBridgeMetadataFields -count=1
```

Expected: fail with missing `AlertAlarmCode`, `AlertSyncStatus`, `AlertSyncError`, and `AlertSyncedAt` fields.

- [ ] **Step 3: Add model fields**

In `app/platform/platform_model/sdn_controller.go`, extend `SDNAlarm`:

```go
	AlertAlarmCode  string     `gorm:"type:varchar(32);index;comment:统一告警编码"`
	AlertSyncedAt   *time.Time `gorm:"comment:统一告警同步时间"`
	AlertSyncStatus string     `gorm:"type:varchar(32);index;comment:统一告警同步状态"`
	AlertSyncError  string     `gorm:"type:text;comment:统一告警同步错误"`
```

Place these after `AcknowledgedAt`.

- [ ] **Step 4: Add DTO fields**

In `app/platform/dto/sdn_controller.go`, extend `SDNAlarmRecord`:

```go
	AlertAlarmCode  string     `json:"alert_alarm_code,omitempty"`
	AlertSyncedAt   *time.Time `json:"alert_synced_at,omitempty"`
	AlertSyncStatus string     `json:"alert_sync_status,omitempty"`
	AlertSyncError  string     `json:"alert_sync_error,omitempty"`
```

Place these after `AcknowledgedAt`.

- [ ] **Step 5: Map model to DTO**

In `sdnAlarmToDTO` inside `app/platform/service/impl/sdn_controller.go`, add:

```go
		AlertAlarmCode:  row.AlertAlarmCode,
		AlertSyncedAt:   row.AlertSyncedAt,
		AlertSyncStatus: row.AlertSyncStatus,
		AlertSyncError:  row.AlertSyncError,
```

- [ ] **Step 6: Run GREEN**

Run:

```bash
go test ./app/platform/service/impl -run TestSDNAlarmBridgeMetadataFields -count=1
```

Expected: pass.

## Task 2: Backend Alert Bridge Projection

**Files:**

- Modify: `app/platform/service/impl/sdn_controller.go`
- Create: `app/platform/service/impl/sdn_alert_bridge.go`
- Modify: `app/platform/service/impl/sdn_controller_test.go`
- Modify: `cmd/wire_gen.go`

- [ ] **Step 1: Write failing bridge tests**

Append these tests in `app/platform/service/impl/sdn_controller_test.go`:

```go
func TestSDNAlarmRefreshProjectsUnifiedAlert(t *testing.T) {
	store, db, server := newTestSDNControllerStoreWithAlertBridge(t)
	defer server.Close()

	ctx := platformTenant.WithCode(t.Context(), "tenant-a")
	controller := seedTestSDNController(t, ctx, db, "ctrl-alert-bridge", server.URL)

	resp, err := store.RefreshAlarms(ctx, controller.ID)
	if err != nil {
		t.Fatalf("RefreshAlarms: %v", err)
	}
	if resp.Total != 1 || len(resp.Alarms) != 1 {
		t.Fatalf("unexpected alarm refresh response %#v", resp)
	}
	if resp.Alarms[0].AlertAlarmCode == "" || resp.Alarms[0].AlertSyncStatus != "synced" {
		t.Fatalf("expected unified alert metadata, got %#v", resp.Alarms[0])
	}

	var alertRows []alertModel.AlertAlarm
	if err := db.Table((&alertModel.AlertAlarm{}).TableName()).Find(&alertRows).Error; err != nil {
		t.Fatalf("query alert rows failed: %v", err)
	}
	if len(alertRows) != 1 {
		t.Fatalf("expected exactly one unified alert, got %d", len(alertRows))
	}
	if alertRows[0].DatasourceType != "sdn" || alertRows[0].RuleCode != "sdn-controller" {
		t.Fatalf("unexpected unified alert source fields %#v", alertRows[0])
	}
	if alertRows[0].State != alertEnum.AlertStateFiring {
		t.Fatalf("expected firing alert, got %q", alertRows[0].State)
	}
	if alertRows[0].ResolvedAt != nil {
		t.Fatalf("new open alert should not be resolved: %#v", alertRows[0].ResolvedAt)
	}
}

func TestSDNAlarmRefreshBridgeIsIdempotentAndClearsUnifiedAlert(t *testing.T) {
	store, db, server := newTestSDNControllerStoreWithAlertBridge(t)
	defer server.Close()

	ctx := platformTenant.WithCode(t.Context(), "tenant-a")
	controller := seedTestSDNController(t, ctx, db, "ctrl-alert-clear", server.URL)

	first, err := store.RefreshAlarms(ctx, controller.ID)
	if err != nil {
		t.Fatalf("first RefreshAlarms: %v", err)
	}
	alertCode := first.Alarms[0].AlertAlarmCode
	if alertCode == "" {
		t.Fatalf("expected first refresh to return alert code: %#v", first)
	}

	second, err := store.RefreshAlarms(ctx, controller.ID)
	if err != nil {
		t.Fatalf("second RefreshAlarms: %v", err)
	}
	if second.Alarms[0].AlertAlarmCode != alertCode {
		t.Fatalf("expected idempotent alert code %q, got %#v", alertCode, second.Alarms[0])
	}
	var count int64
	if err := db.Table((&alertModel.AlertAlarm{}).TableName()).Count(&count).Error; err != nil {
		t.Fatalf("count alert rows failed: %v", err)
	}
	if count != 1 {
		t.Fatalf("expected one unified alert after repeated refresh, got %d", count)
	}

	server.SetAlarmPayload(`{"success":true,"data":{"alarms":[]}}`)
	cleared, err := store.RefreshAlarms(ctx, controller.ID)
	if err != nil {
		t.Fatalf("clear RefreshAlarms: %v", err)
	}
	if cleared.Alarms[0].Status != dto.SDNAlarmStatusCleared {
		t.Fatalf("expected SDN alarm cleared, got %#v", cleared.Alarms[0])
	}

	var alert alertModel.AlertAlarm
	if err := db.Table((&alertModel.AlertAlarm{}).TableName()).Where("code = ?", alertCode).First(&alert).Error; err != nil {
		t.Fatalf("load unified alert failed: %v", err)
	}
	if alert.State != alertEnum.AlertStateInactive || alert.ResolvedAt == nil {
		t.Fatalf("expected resolved inactive unified alert, got state=%q resolved=%v", alert.State, alert.ResolvedAt)
	}
}
```

Add imports to the same test file:

```go
	"github.com/alicebob/miniredis/v2"
	"github.com/redis/go-redis/v9"
	alertModel "github.com/netxops/OneOps/app/alert/alert_model"
	alertEnum "github.com/netxops/OneOps/app/alert/enum"
	alertImpl "github.com/netxops/OneOps/app/alert/service/impl"
	baseModel "github.com/netxops/OneOps/app/base/base_model"
	baseImpl "github.com/netxops/OneOps/app/base/service/impl"
	"github.com/netxops/OneOps/app/common/codec"
	"github.com/netxops/OneOps/pkg/types"
```

If aliases conflict with existing imports, keep the aliases shown above.

- [ ] **Step 2: Add bridge test helper**

Add this helper near `newTestSDNControllerStoreWithAlarmServer`:

```go
func newTestSDNControllerStoreWithAlertBridge(t *testing.T) (*SDNControllerStore, *gorm.DB, *mutableAlarmServer) {
	t.Helper()
	store, db, server := newTestSDNControllerStoreWithAlarmServer(t)
	if err := db.AutoMigrate(&baseModel.Tenant{}, &alertModel.AlertDatasource{}, &alertModel.AlertRule{}, &alertModel.AlertAlarm{}); err != nil {
		t.Fatalf("migrate alert bridge tables failed: %v", err)
	}
	miniRedis, err := miniredis.Run()
	if err != nil {
		t.Fatalf("start miniredis failed: %v", err)
	}
	t.Cleanup(miniRedis.Close)
	redisClient := redis.NewClient(&redis.Options{Addr: miniRedis.Addr()})
	t.Cleanup(func() { _ = redisClient.Close() })

	alertSrv := &alertImpl.AlertAlarmSrv{
		DB:     types.DBTypeMySQL(db),
		Logger: zap.NewNop(),
		GenerateCodeSrv: &codec.GenerateCodeSrv{
			RedisClient: redisClient,
			Logger:      zap.NewNop(),
		},
		ProxySrv: &proxy.TxProxySrv{Q: mysql.Use(db)},
	}
	alertSrv.TenantSrv = &baseImpl.TenantSrv{ProxySrv: alertSrv.ProxySrv, Logger: zap.NewNop()}
	store.AlertAlarmSrv = alertSrv
	return store, db, server
}
```

- [ ] **Step 3: Run RED**

Run:

```bash
go test ./app/platform/service/impl -run 'TestSDNAlarmRefreshProjectsUnifiedAlert|TestSDNAlarmRefreshBridgeIsIdempotentAndClearsUnifiedAlert' -count=1
```

Expected: fail because `SDNControllerStore.AlertAlarmSrv`, bridge metadata, and projection do not exist yet.

- [ ] **Step 4: Add store dependency and production constructor**

In `app/platform/service/impl/sdn_controller.go`, add imports:

```go
	alertService "github.com/netxops/OneOps/app/alert/service"
```

Extend `SDNControllerStore`:

```go
	AlertAlarmSrv alertService.IAlertAlarm
```

Keep the existing constructor for tests:

```go
func NewSDNControllerStore(logger *zap.Logger, proxySrv *proxy.TxProxySrv, secretSrv settingService.ISecret) *SDNControllerStore {
	return &SDNControllerStore{Logger: logger, ProxySrv: proxySrv, SecretSrv: secretSrv}
}
```

Add production constructor:

```go
func NewSDNControllerStoreWithAlertBridge(
	logger *zap.Logger,
	proxySrv *proxy.TxProxySrv,
	secretSrv settingService.ISecret,
	alertAlarmSrv alertService.IAlertAlarm,
) *SDNControllerStore {
	store := NewSDNControllerStore(logger, proxySrv, secretSrv)
	store.AlertAlarmSrv = alertAlarmSrv
	return store
}
```

Update `SDNControllerStoreSet`:

```go
var SDNControllerStoreSet = wire.NewSet(
	NewSDNControllerStoreWithAlertBridge,
	wire.Bind(new(service.ISDNControllerStore), new(*SDNControllerStore)),
)
```

- [ ] **Step 5: Make refresh return changed rows for bridge**

Change `upsertSDNAlarm` signature:

```go
func (s *SDNControllerStore) upsertSDNAlarm(ctx context.Context, controller *platformModel.SDNController, alarm *dto.SDNAlarmRecord, alarmKey string, now time.Time) (*platformModel.SDNAlarm, error)
```

For new rows, after `Create(row)` return `row, nil`.

For existing rows, after `Updates(updates)`, reload and return:

```go
	if err := s.alarmDB(ctx).Where("id = ?", existing.ID).Updates(updates).Error; err != nil {
		return nil, err
	}
	var updated platformModel.SDNAlarm
	if err := s.alarmDB(ctx).Where("id = ?", existing.ID).First(&updated).Error; err != nil {
		return nil, err
	}
	return &updated, nil
```

Change `clearMissingSDNAlarms` signature:

```go
func (s *SDNControllerStore) clearMissingSDNAlarms(ctx context.Context, controllerID string, seen map[string]struct{}, now time.Time) ([]platformModel.SDNAlarm, error)
```

Before updating, load rows to clear:

```go
	var rows []platformModel.SDNAlarm
	if err := query.Find(&rows).Error; err != nil {
		return nil, err
	}
	if len(rows) == 0 {
		return rows, nil
	}
	ids := make([]string, 0, len(rows))
	for _, row := range rows {
		ids = append(ids, row.ID)
	}
	if err := s.alarmDB(ctx).Where("id IN ?", ids).Updates(map[string]any{
		"status":     dto.SDNAlarmStatusCleared,
		"cleared_at": &now,
	}).Error; err != nil {
		return nil, err
	}
	for i := range rows {
		rows[i].Status = dto.SDNAlarmStatusCleared
		rows[i].ClearedAt = &now
	}
	return rows, nil
```

Update `RefreshAlarms` to collect changed rows:

```go
	changedRows := make([]*platformModel.SDNAlarm, 0, len(current.Alarms))
	for i := range current.Alarms {
		key := stableSDNAlarmKey(row.ID, &current.Alarms[i])
		seen[key] = struct{}{}
		alarmRow, err := s.upsertSDNAlarm(ctx, row, &current.Alarms[i], key, now)
		if err != nil {
			return nil, err
		}
		if alarmRow != nil {
			changedRows = append(changedRows, alarmRow)
		}
	}
	clearedRows, err := s.clearMissingSDNAlarms(ctx, row.ID, seen, now)
	if err != nil {
		return nil, err
	}
	for i := range clearedRows {
		changedRows = append(changedRows, &clearedRows[i])
	}
	s.bridgeSDNAlarmsToUnifiedAlert(ctx, changedRows, now)
```

Do not return bridge errors from `RefreshAlarms`; the bridge records per-row status.

- [ ] **Step 6: Create bridge implementation**

Create `app/platform/service/impl/sdn_alert_bridge.go`:

```go
package impl

import (
	"context"
	"crypto/md5"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/netxops/OneOps/app/alert/alert_model"
	alertEnum "github.com/netxops/OneOps/app/alert/enum"
	platformModel "github.com/netxops/OneOps/app/platform/platform_model"
	"go.uber.org/zap"
	"gorm.io/gorm"
)

const (
	sdnUnifiedAlertDatasourceType = "sdn"
	sdnUnifiedAlertDatasourceCode = "sdn"
	sdnUnifiedAlertRuleCode       = "sdn-controller"
	sdnAlertSyncStatusSynced      = "synced"
	sdnAlertSyncStatusFailed      = "failed"
	sdnAlertSyncStatusSkipped     = "skipped"
)

func (s *SDNControllerStore) bridgeSDNAlarmsToUnifiedAlert(ctx context.Context, rows []*platformModel.SDNAlarm, now time.Time) {
	if s == nil || s.AlertAlarmSrv == nil || len(rows) == 0 {
		return
	}
	for _, row := range rows {
		if row == nil || strings.TrimSpace(row.ID) == "" {
			continue
		}
		code, status, err := s.bridgeOneSDNAlarmToUnifiedAlert(ctx, row, now)
		s.recordSDNAlertBridgeResult(ctx, row.ID, code, status, err, now)
	}
}

func (s *SDNControllerStore) bridgeOneSDNAlarmToUnifiedAlert(ctx context.Context, row *platformModel.SDNAlarm, now time.Time) (string, string, error) {
	md5Value := sdnUnifiedAlertMD5(row)
	existing, err := s.AlertAlarmSrv.FindByMD5AndNotResolved(md5Value, ctx)
	if err != nil && !errors.Is(err, gorm.ErrRecordNotFound) {
		return "", sdnAlertSyncStatusFailed, err
	}
	if strings.EqualFold(strings.TrimSpace(row.Status), "cleared") {
		if existing == nil {
			return row.AlertAlarmCode, sdnAlertSyncStatusSkipped, nil
		}
		applySDNAlarmToUnifiedAlert(existing, row, now)
		existing.State = alertEnum.AlertStateInactive
		existing.ResolvedAt = nonNilTime(row.ClearedAt, now)
		if _, err := s.AlertAlarmSrv.Update(existing, ctx); err != nil {
			return existing.Code, sdnAlertSyncStatusFailed, err
		}
		return existing.Code, sdnAlertSyncStatusSynced, nil
	}
	if existing == nil {
		alarm := buildUnifiedAlertFromSDNAlarm(row, now)
		if err := s.AlertAlarmSrv.Create(alarm, ctx); err != nil {
			return "", sdnAlertSyncStatusFailed, err
		}
		return alarm.Code, sdnAlertSyncStatusSynced, nil
	}
	applySDNAlarmToUnifiedAlert(existing, row, now)
	existing.State = alertEnum.AlertStateFiring
	existing.ResolvedAt = nil
	if _, err := s.AlertAlarmSrv.Update(existing, ctx); err != nil {
		return existing.Code, sdnAlertSyncStatusFailed, err
	}
	return existing.Code, sdnAlertSyncStatusSynced, nil
}

func buildUnifiedAlertFromSDNAlarm(row *platformModel.SDNAlarm, now time.Time) *alert_model.AlertAlarm {
	firedAt := row.FirstSeenAt
	if firedAt.IsZero() {
		firedAt = now
	}
	alarm := &alert_model.AlertAlarm{
		Value:          sdnAlarmSeverityValue(row.Severity),
		State:          alertEnum.AlertStateFiring,
		Description:    sdnUnifiedAlertDescription(row),
		DatasourceCode: sdnUnifiedAlertDatasourceCode,
		DatasourceType: sdnUnifiedAlertDatasourceType,
		RuleCode:       sdnUnifiedAlertRuleCode,
		Summary:        sdnUnifiedAlertSummary(row),
		TenantName:     strings.TrimSpace(row.TenantCode),
		ExprSnapshot:   fmt.Sprintf("sdn_alarm{%s}", sdnUnifiedAlertMD5(row)),
		Flag:           sdnUnifiedAlertFlag(row),
		MD5:            sdnUnifiedAlertMD5(row),
		Labels:         mustRawJSON(sdnUnifiedAlertLabels(row)),
		Annotations:    mustRawJSON(sdnUnifiedAlertAnnotations(row)),
		ActiveAt:       &firedAt,
		FiredAt:        &firedAt,
		LastSentAt:     &now,
	}
	return alarm
}

func applySDNAlarmToUnifiedAlert(alarm *alert_model.AlertAlarm, row *platformModel.SDNAlarm, now time.Time) {
	alarm.Value = sdnAlarmSeverityValue(row.Severity)
	alarm.Description = sdnUnifiedAlertDescription(row)
	alarm.DatasourceCode = sdnUnifiedAlertDatasourceCode
	alarm.DatasourceType = sdnUnifiedAlertDatasourceType
	alarm.RuleCode = sdnUnifiedAlertRuleCode
	alarm.Summary = sdnUnifiedAlertSummary(row)
	alarm.TenantName = strings.TrimSpace(row.TenantCode)
	alarm.ExprSnapshot = fmt.Sprintf("sdn_alarm{%s}", sdnUnifiedAlertMD5(row))
	alarm.Flag = sdnUnifiedAlertFlag(row)
	alarm.MD5 = sdnUnifiedAlertMD5(row)
	alarm.Labels = mustRawJSON(sdnUnifiedAlertLabels(row))
	alarm.Annotations = mustRawJSON(sdnUnifiedAlertAnnotations(row))
	if row.FirstSeenAt.IsZero() {
		alarm.FiredAt = &now
	} else {
		alarm.FiredAt = &row.FirstSeenAt
	}
	alarm.LastSentAt = &now
}

func (s *SDNControllerStore) recordSDNAlertBridgeResult(ctx context.Context, alarmID, code, status string, bridgeErr error, now time.Time) {
	updates := map[string]any{
		"alert_synced_at":   &now,
		"alert_sync_status": status,
		"alert_sync_error":  "",
	}
	if strings.TrimSpace(code) != "" {
		updates["alert_alarm_code"] = strings.TrimSpace(code)
	}
	if bridgeErr != nil {
		updates["alert_sync_status"] = sdnAlertSyncStatusFailed
		updates["alert_sync_error"] = truncateSDNAlertBridgeError(sanitizeSDNAlarmValue("error", bridgeErr.Error()))
		if s.Logger != nil {
			s.Logger.Warn("sdn alert bridge failed", zap.String("sdn_alarm_id", alarmID), zap.Error(bridgeErr))
		}
	}
	_ = s.alarmDB(ctx).Where("id = ?", alarmID).Updates(updates).Error
}

func sdnUnifiedAlertMD5(row *platformModel.SDNAlarm) string {
	identity := "sdn:" + strings.TrimSpace(row.ControllerID) + ":" + strings.TrimSpace(row.AlarmKey)
	sum := md5.Sum([]byte(identity))
	return hex.EncodeToString(sum[:])
}

func sdnUnifiedAlertLabels(row *platformModel.SDNAlarm) map[string]string {
	return map[string]string{
		"source":            "sdn",
		"controller_id":     strings.TrimSpace(row.ControllerID),
		"provider":          strings.TrimSpace(row.Provider),
		"alarm_key":         strings.TrimSpace(row.AlarmKey),
		"provider_alarm_id": strings.TrimSpace(row.ProviderAlarmID),
		"resource_type":     strings.TrimSpace(row.ResourceType),
		"resource_name":     strings.TrimSpace(row.ResourceName),
		"resource_dn":       strings.TrimSpace(row.ResourceDN),
		"tenant":            strings.TrimSpace(row.TenantCode),
		"hostname":          strings.TrimSpace(firstNonEmpty(row.ResourceName, row.ResourceDN, row.ProviderAlarmID, row.AlarmKey)),
	}
}

func sdnUnifiedAlertAnnotations(row *platformModel.SDNAlarm) map[string]string {
	return map[string]string{
		"summary":        sdnUnifiedAlertSummary(row),
		"description":    sdnUnifiedAlertDescription(row),
		"sdn_alarm_id":   strings.TrimSpace(row.ID),
		"sdn_alarm_code": strings.TrimSpace(row.Code),
		"severity":       strings.TrimSpace(row.Severity),
	}
}

func sdnUnifiedAlertSummary(row *platformModel.SDNAlarm) string {
	return firstNonEmpty(strings.TrimSpace(row.Title), strings.TrimSpace(row.Message), strings.TrimSpace(row.Code), "SDN alarm")
}

func sdnUnifiedAlertDescription(row *platformModel.SDNAlarm) string {
	return firstNonEmpty(strings.TrimSpace(row.Message), strings.TrimSpace(row.Title), strings.TrimSpace(row.ResourceDN), strings.TrimSpace(row.AlarmKey))
}

func sdnUnifiedAlertFlag(row *platformModel.SDNAlarm) string {
	return firstNonEmpty(strings.TrimSpace(row.ResourceName), strings.TrimSpace(row.ResourceDN), strings.TrimSpace(row.ProviderAlarmID), strings.TrimSpace(row.AlarmKey))
}

func sdnAlarmSeverityValue(severity string) float64 {
	switch strings.ToLower(strings.TrimSpace(severity)) {
	case "critical":
		return 5
	case "major":
		return 4
	case "minor", "warning", "warn":
		return 3
	case "info", "informational":
		return 1
	default:
		return 2
	}
}

func mustRawJSON(value any) json.RawMessage {
	data, err := json.Marshal(value)
	if err != nil {
		return json.RawMessage(`{}`)
	}
	return data
}

func nonNilTime(value *time.Time, fallback time.Time) *time.Time {
	if value != nil {
		return value
	}
	return &fallback
}

func truncateSDNAlertBridgeError(value any) string {
	text := strings.TrimSpace(fmt.Sprint(value))
	if len(text) <= 512 {
		return text
	}
	return text[:512]
}

```

- [ ] **Step 7: Wire production constructor**

In `cmd/wire_gen.go`, replace:

```go
sdnControllerStore := impl24.NewSDNControllerStore(logger, txProxySrv, secretSrv)
```

with:

```go
sdnControllerStore := impl24.NewSDNControllerStoreWithAlertBridge(logger, txProxySrv, secretSrv, alertAlarmSrv)
```

Do not run `wire` unless the repo already expects generated rewrites in this task.

- [ ] **Step 8: Run GREEN**

Run:

```bash
go test ./app/platform/service/impl -run 'TestSDNAlarmRefreshProjectsUnifiedAlert|TestSDNAlarmRefreshBridgeIsIdempotentAndClearsUnifiedAlert' -count=1
```

Expected: pass.

- [ ] **Step 9: Run focused backend regression**

Run:

```bash
go test ./app/platform/api ./app/platform/router ./app/platform/service/impl ./app/platform/dto ./app/platform/platform_model -count=1
```

Expected: pass.

- [ ] **Step 10: Commit backend**

Run:

```bash
git add app/platform/platform_model/sdn_controller.go app/platform/dto/sdn_controller.go app/platform/service/impl/sdn_controller.go app/platform/service/impl/sdn_alert_bridge.go app/platform/service/impl/sdn_controller_test.go cmd/wire_gen.go
git commit -m "feat: bridge sdn alarms to unified alerts"
```

If `initialize/mysql.go` only contains unrelated NetPath changes, do not stage it.

## Task 3: Frontend Bridge Metadata Display

**Files:**

- Modify: `src/typings/platform/sdn-controller.ts`
- Modify: `src/views/device/SdnControllerManagement.vue`
- Modify: `scripts/sdn-resource-workbench-smoke.ts`

- [ ] **Step 1: Write failing smoke assertions**

In `scripts/sdn-resource-workbench-smoke.ts`, add these source checks in the existing typings/page source assertion section:

```ts
    'alert_alarm_code?: string;',
    'alert_sync_status?: string;',
    'alert_synced_at?: string;',
    '统一告警',
    '同步失败',
```

In the seeded `alarmHistoryByControllerId` first alarm, add:

```ts
            alert_alarm_code: 'AAM20260620000001',
            alert_sync_status: 'synced',
            alert_synced_at: '2026-06-20T09:20:00Z',
```

In the second alarm, add:

```ts
            alert_sync_status: 'failed',
            alert_sync_error: 'projection failed',
```

After `assert(alarmText.includes('统一告警'), ...)`, add:

```ts
  assert(alarmText.includes('AAM20260620000001'), 'unified alert code should render');
  assert(alarmText.includes('同步失败'), 'failed alert bridge status should render');
```

- [ ] **Step 2: Run RED**

Run:

```bash
npm run smoke:sdn-resource-workbench
```

Expected: fail because typings and rendering are missing bridge fields/status.

- [ ] **Step 3: Add TS fields**

In `src/typings/platform/sdn-controller.ts`, extend `AlarmRecord`:

```ts
  alert_alarm_code?: string;
  alert_sync_status?: 'pending' | 'synced' | 'failed' | 'skipped' | string;
  alert_sync_error?: string;
  alert_synced_at?: string;
```

- [ ] **Step 4: Normalize bridge fields**

In `normalizeAlarmRecord` inside `src/views/device/SdnControllerManagement.vue`, add:

```ts
    alert_ref:
      stringValue(record.alert_alarm_code || record.alert_ref || record.alert_id || record.unified_alert_ref) || undefined,
    alert_link: stringValue(record.alert_link || record.alert_url || record.unified_alert_link) || undefined,
    alert_alarm_code: stringValue(record.alert_alarm_code) || undefined,
    alert_sync_status: stringValue(record.alert_sync_status) || undefined,
    alert_sync_error: stringValue(record.alert_sync_error) || undefined,
    alert_synced_at: stringValue(record.alert_synced_at) || undefined,
```

Replace the existing `alert_ref` and `alert_link` assignments with the block above.

- [ ] **Step 5: Render status and link**

Change the `alarmColumns` unified alert column width to `180` and add a status column:

```ts
  { title: 'unified_alert', dataIndex: 'alert_ref', key: 'alert_ref', width: 180 },
  { title: 'bridge_status', dataIndex: 'alert_sync_status', key: 'alert_sync_status', width: 140 },
```

In the body cell template, replace the `alert_ref` block:

```vue
            <template v-else-if="column.key === 'alert_ref'">
              <a
                v-if="(record as AlarmRecord).alert_alarm_code"
                :href="`#/alert/alarm?code=${encodeURIComponent((record as AlarmRecord).alert_alarm_code || '')}`"
              >
                {{ (record as AlarmRecord).alert_alarm_code }}
              </a>
              <a v-else-if="(record as AlarmRecord).alert_link" :href="(record as AlarmRecord).alert_link">统一告警</a>
              <span v-else-if="(record as AlarmRecord).alert_ref">{{ (record as AlarmRecord).alert_ref }}</span>
              <span v-else>-</span>
            </template>
            <template v-else-if="column.key === 'alert_sync_status'">
              <a-tag :color="alarmBridgeStatusColor((record as AlarmRecord).alert_sync_status)">
                {{ alarmBridgeStatusLabel((record as AlarmRecord).alert_sync_status) }}
              </a-tag>
              <span v-if="(record as AlarmRecord).alert_sync_error" class="alarm-sync-error">
                {{ sanitizeText((record as AlarmRecord).alert_sync_error, '') }}
              </span>
            </template>
```

Add helper functions near `alarmStatusLabel`:

```ts
function alarmBridgeStatusLabel(status?: string) {
  switch (String(status || '').toLowerCase()) {
    case 'synced':
      return '已接入';
    case 'failed':
      return '同步失败';
    case 'skipped':
      return '已跳过';
    case 'pending':
      return '待同步';
    default:
      return status || '-';
  }
}

function alarmBridgeStatusColor(status?: string) {
  switch (String(status || '').toLowerCase()) {
    case 'synced':
      return 'green';
    case 'failed':
      return 'red';
    case 'skipped':
      return 'default';
    case 'pending':
      return 'blue';
    default:
      return 'default';
  }
}
```

Add compact styling if needed:

```css
.alarm-sync-error {
  display: block;
  margin-top: 4px;
  color: #ff4d4f;
  font-size: 12px;
}
```

- [ ] **Step 6: Run GREEN**

Run:

```bash
npm run smoke:sdn-resource-workbench
npx prettier --check src/views/device/SdnControllerManagement.vue src/typings/platform/sdn-controller.ts scripts/sdn-resource-workbench-smoke.ts
```

Expected: both pass.

- [ ] **Step 7: Commit frontend**

Run:

```bash
git add src/typings/platform/sdn-controller.ts src/views/device/SdnControllerManagement.vue scripts/sdn-resource-workbench-smoke.ts
git commit -m "feat: show sdn unified alert bridge status"
```

## Task 4: Final Verification

**Files:**

- No code files unless verification finds a defect.

- [ ] **Step 1: Verify OneOPS backend**

Run:

```bash
go test ./app/platform/api ./app/platform/router ./app/platform/service/impl ./app/platform/dto ./app/platform/platform_model -count=1
```

Expected: pass.

- [ ] **Step 2: Verify OneOPS UI**

Run:

```bash
npm run smoke:sdn-resource-workbench
npx prettier --check src/views/device/SdnControllerManagement.vue src/api/platform/sdn-controller.ts src/typings/platform/sdn-controller.ts scripts/sdn-resource-workbench-smoke.ts
```

Expected: pass.

- [ ] **Step 3: Confirm CtrlHub untouched**

Run:

```bash
git -C /Users/huangliang/project/OneOPS-ALL/ctrlhub status --short
```

Expected: no SDN bridge changes required in CtrlHub. Existing unrelated dirty files, if any, must not be touched.

- [ ] **Step 4: Report commits and residual risks**

Final report must include:

- Backend commit hash.
- Frontend commit hash.
- Verification commands and pass/fail result.
- Note that tickets are not auto-created by this bridge.
- Note any unrelated dirty files left alone.
