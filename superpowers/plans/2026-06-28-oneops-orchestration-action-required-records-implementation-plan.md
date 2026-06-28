# OneOps Orchestration Action-Required Records Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn orchestration `execution_action_required` from an event-only signal into a real operator-takeover capability with persisted records, claim/resolve APIs, and record-backed UI state.

**Architecture:** Keep the existing execution path intact: `ExecutionSrv -> compiler -> DagengineAdapter -> ResumeSrv`. Add a first-class `orchestration_action_required_records` model owned by OneOps, persist it in the same transaction as escalated terminal event handling, then switch observatory/detail reads from raw event scans to record-backed state while preserving the current route shape.

**Tech Stack:** Go, GORM, existing OneOps orchestration services/APIs, Vue 3, Ant Design Vue, existing smoke and real-api acceptance scripts.

---

## Scope Decisions

- Keep `GET /orchestration/executions/action-required`; only its backing source changes from `ExecutionEvent` to `ActionRequiredRecord`.
- Add `claim` and `resolve` APIs now; do **not** add public `cancel` in this slice.
- Keep `execution_action_required` events for audit/timeline visibility.
- Do **not** build a separate workbench page in this slice; extend the existing observatory tab and execution detail page.
- Skip standalone `GET /orchestration/executions/action-required/:id` for now. Reuse list rows plus enriched execution detail state to stay MVP-tight.

## File Structure

**Create:**
- `OneOps/app/orchestration/orchestration_model/action_required_record.go`
- `OneOps/app/orchestration/service/impl/action_required_record.go`
- `OneOps/app/orchestration/dto/action_required.go`

**Modify:**
- `OneOps/initialize/mysql.go`
- `OneOps/initialize/mysql_test.go`
- `OneOps/app/orchestration/service/i_execution.go`
- `OneOps/app/orchestration/api/execution.go`
- `OneOps/app/orchestration/router/execution.go`
- `OneOps/app/orchestration/dto/execution.go`
- `OneOps/app/orchestration/service/impl/resume.go`
- `OneOps/app/orchestration/service/impl/execution.go`
- `OneOps/app/orchestration/service/impl/execution_graph.go`
- `OneOps/app/orchestration/service/impl/execution_test.go`
- `OneOps/app/orchestration/service/impl/resume_test.go`
- `OneOps/app/alert/api/alert_ticket.go`
- `OneOps/app/alert/api/alert_ticket_test.go`
- `OneOPS-UI/src/typings/orchestration/execution.ts`
- `OneOPS-UI/src/api/orchestration/execution.ts`
- `OneOPS-UI/src/views/platform/ExecutionObservatory.vue`
- `OneOPS-UI/src/views/platform/ExecutionDetailDebugger.vue`
- `OneOPS-UI/scripts/execution-observatory-smoke.ts`
- `OneOPS-UI/scripts/execution-detail-debugger-smoke.ts`
- `OneOPS-UI/scripts/execution-observatory-real-api-acceptance.ts`
- `docs/runbooks/alert-to-ticket-dagengine-mvp.md`

**Why this split:**
- Model stays isolated in `orchestration_model`.
- Runtime persistence logic stays focused in a new `action_required_record.go` helper instead of bloating `resume.go`.
- Mutation DTOs live in their own file so `dto/execution.go` does not become an all-purpose dump.

## Task 1: Add the Action-Required Record Model and Migration Coverage

**Files:**
- Create: `OneOps/app/orchestration/orchestration_model/action_required_record.go`
- Modify: `OneOps/initialize/mysql.go`
- Test: `OneOps/initialize/mysql_test.go`
- Test: `OneOps/app/orchestration/service/impl/execution_test.go`
- Test: `OneOps/app/orchestration/service/impl/resume_test.go`

- [ ] **Step 1: Write the failing migration test**

```go
func TestOrchestrationActionRequiredRecordAutoMigrate(t *testing.T) {
	db := newTestMySQLLikeDB(t)

	if err := db.AutoMigrate(&orchestrationmodel.ActionRequiredRecord{}); err != nil {
		t.Fatalf("auto migrate failed: %v", err)
	}

	if !db.Migrator().HasTable(&orchestrationmodel.ActionRequiredRecord{}) {
		t.Fatal("action required record table was not created")
	}

	if !db.Migrator().HasIndex(&orchestrationmodel.ActionRequiredRecord{}, "idx_orch_ar_source_event_id") {
		t.Fatal("source event unique index was not created")
	}
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd OneOps && go test ./initialize -run TestOrchestrationActionRequiredRecordAutoMigrate -count=1`

Expected: FAIL because `ActionRequiredRecord` does not exist yet.

- [ ] **Step 3: Add the new GORM model**

```go
type ActionRequiredRecord struct {
	ID             string     `gorm:"primaryKey;type:varchar(36)"`
	ExecutionID    string     `gorm:"type:varchar(36);index;not null"`
	NodeID         string     `gorm:"type:varchar(128);index;not null"`
	NodeType       string     `gorm:"type:varchar(64);index"`
	SourceEventID  string     `gorm:"type:varchar(36);uniqueIndex:idx_orch_ar_source_event_id;not null"`
	TemplateCode   string     `gorm:"type:varchar(128);index"`
	Environment    string     `gorm:"type:varchar(64);index"`
	AlertCode      string     `gorm:"type:varchar(128);index"`
	TicketCode     string     `gorm:"type:varchar(128);index"`
	ActionType     string     `gorm:"type:varchar(64);not null"`
	ActionKey      string     `gorm:"type:varchar(64);not null"`
	RouteField     string     `gorm:"type:varchar(32);index;not null"`
	TerminalStatus string     `gorm:"type:varchar(32);index;not null"`
	Reason         string     `gorm:"type:varchar(255)"`
	Status         string     `gorm:"type:varchar(32);index;not null"`
	ClaimedBy      string     `gorm:"type:varchar(64)"`
	ClaimedAt      *time.Time
	ResolvedBy     string     `gorm:"type:varchar(64)"`
	ResolvedAt     *time.Time
	ResolutionCode string     `gorm:"type:varchar(64)"`
	ResolutionNote string     `gorm:"type:text"`
	PayloadJSON    string     `gorm:"type:json;not null"`
	CreatedAt      time.Time  `gorm:"index"`
	UpdatedAt      time.Time  `gorm:"index"`
}

func (*ActionRequiredRecord) TableName() string {
	return "orchestration_action_required_records"
}
```

- [ ] **Step 4: Register the model in the unified MySQL model list and test DB migrations**

```go
// OneOps/initialize/mysql.go
orchestrationModel.ActionRequiredRecord{},
```

```go
// add to sqlite AutoMigrate call sites used by orchestration tests
&orchestrationModel.ActionRequiredRecord{},
```

- [ ] **Step 5: Re-run the migration test**

Run: `cd OneOps && go test ./initialize -run TestOrchestrationActionRequiredRecordAutoMigrate -count=1`

Expected: PASS.

## Task 2: Persist Action-Required Records in the Escalated Runtime Path

**Files:**
- Create: `OneOps/app/orchestration/service/impl/action_required_record.go`
- Modify: `OneOps/app/orchestration/service/impl/resume.go`
- Test: `OneOps/app/orchestration/service/impl/resume_test.go`

- [ ] **Step 1: Write failing runtime persistence tests for reject and timeout escalation**

```go
func TestResumeService_RejectEscalationPersistsActionRequiredRecord(t *testing.T) {
	record := loadSingleActionRequiredRecord(t, db, startResp.ID)
	if record.RouteField != "on_failure" {
		t.Fatalf("route_field = %q, want %q", record.RouteField, "on_failure")
	}
	if record.Status != "pending" {
		t.Fatalf("status = %q, want %q", record.Status, "pending")
	}
}

func TestResumeService_TimeoutEscalationPersistsActionRequiredRecord(t *testing.T) {
	record := loadSingleActionRequiredRecord(t, db, startResp.ID)
	if record.RouteField != "on_timeout" {
		t.Fatalf("route_field = %q, want %q", record.RouteField, "on_timeout")
	}
	if record.SourceEventID == "" {
		t.Fatal("source_event_id should not be empty")
	}
}
```

- [ ] **Step 2: Run the resume tests to verify they fail**

Run: `cd OneOps && go test ./app/orchestration/service/impl -run 'TestResumeService_(RejectEscalationPersistsActionRequiredRecord|TimeoutEscalationPersistsActionRequiredRecord)' -count=1`

Expected: FAIL because no record is persisted yet.

- [ ] **Step 3: Add a focused helper that persists records from emitted events inside the same transaction**

```go
func persistActionRequiredRecords(
	tx *gorm.DB,
	execution orchestrationModel.TemplateExecution,
	resultContext map[string]interface{},
	eventRows []orchestrationModel.ExecutionEvent,
) error {
	for _, eventRow := range eventRows {
		if strings.TrimSpace(eventRow.EventType) != "execution_action_required" {
			continue
		}

		payload, _ := decodeExecutionContextJSON(eventRow.PayloadJSON)
		record := orchestrationModel.ActionRequiredRecord{
			ID:             uuid.NewString(),
			ExecutionID:    execution.ID,
			NodeID:         eventRow.NodeID,
			NodeType:       eventRow.NodeType,
			SourceEventID:  eventRow.ID,
			TemplateCode:   execution.TemplateCode,
			Environment:    execution.Environment,
			AlertCode:      eventPayloadString(resultContext, "alert_code"),
			TicketCode:     eventPayloadString(resultContext, "ticket_code"),
			ActionType:     eventPayloadString(payload, "action_type"),
			ActionKey:      eventPayloadString(payload, "action_key"),
			RouteField:     eventPayloadString(payload, "route_field"),
			TerminalStatus: eventPayloadString(payload, "terminal_status"),
			Reason:         eventPayloadString(payload, "reason"),
			Status:         firstNonEmpty(eventPayloadString(payload, "action_status"), "pending"),
			PayloadJSON:    eventRow.PayloadJSON,
		}
		if err := tx.Create(&record).Error; err != nil {
			return err
		}
	}
	return nil
}
```

- [ ] **Step 4: Call the helper from `persistResumedExecution` after event rows are inserted and before commit**

```go
createdEvents := make([]orchestrationModel.ExecutionEvent, 0, len(result.Events))
for _, event := range result.Events {
	// build executionEvent
	createdEvents = append(createdEvents, *executionEvent)
}

if err := persistActionRequiredRecords(tx, *execution, result.Context, createdEvents); err != nil {
	tx.Rollback()
	return "", err
}
```

- [ ] **Step 5: Re-run the targeted resume tests**

Run: `cd OneOps && go test ./app/orchestration/service/impl -run 'TestResumeService_(RejectEscalationPersistsActionRequiredRecord|TimeoutEscalationPersistsActionRequiredRecord)' -count=1`

Expected: PASS.

## Task 3: Switch Backend Reads to Records and Expose Claim/Resolve APIs

**Files:**
- Create: `OneOps/app/orchestration/dto/action_required.go`
- Modify: `OneOps/app/orchestration/dto/execution.go`
- Modify: `OneOps/app/orchestration/service/i_execution.go`
- Modify: `OneOps/app/orchestration/service/impl/execution.go`
- Modify: `OneOps/app/orchestration/service/impl/execution_graph.go`
- Modify: `OneOps/app/orchestration/api/execution.go`
- Modify: `OneOps/app/orchestration/router/execution.go`
- Modify: `OneOps/app/alert/api/alert_ticket.go`
- Test: `OneOps/app/orchestration/service/impl/execution_test.go`
- Test: `OneOps/app/alert/api/alert_ticket_test.go`

- [ ] **Step 1: Add failing tests for record-backed list, summary, detail, claim, resolve, and alert compatibility**

```go
func TestExecutionService_ListActionRequiredRecords(t *testing.T) {}
func TestExecutionService_GetExecutionSummaryCountsOnlyOpenActionRequiredRecords(t *testing.T) {}
func TestExecutionService_GetExecutionIncludesOpenActionRequiredRecord(t *testing.T) {}
func TestExecutionService_ClaimActionRequiredRecord(t *testing.T) {}
func TestExecutionService_ResolveActionRequiredRecord(t *testing.T) {}
func TestAlertTicketAPI_ListOrchestrationActionsUsesActionRequiredRecords(t *testing.T) {}
```

The key assertions should be:

```go
if item.Status != "claimed" {
	t.Fatalf("status = %q, want %q", item.Status, "claimed")
}
if summary.ActionRequired != 1 {
	t.Fatalf("action required = %d, want %d", summary.ActionRequired, 1)
}
if resp.ActionRequiredDetail == nil || resp.ActionRequiredDetail.Status != "pending" {
	t.Fatalf("expected live action-required detail, got %#v", resp.ActionRequiredDetail)
}
```

- [ ] **Step 2: Run the targeted backend tests to verify they fail**

Run: `cd OneOps && go test ./app/orchestration/service/impl ./app/alert/api -run 'Test(ExecutionService_|AlertTicketAPI_)' -count=1`

Expected: FAIL because the service still reads raw events and has no mutation APIs.

- [ ] **Step 3: Add request/response DTOs and enrich execution detail state**

```go
type ClaimActionRequiredReq struct {
	Operator string `json:"operator"`
	Note     string `json:"note,omitempty"`
}

type ResolveActionRequiredReq struct {
	Operator       string `json:"operator"`
	ResolutionCode string `json:"resolution_code"`
	ResolutionNote string `json:"resolution_note,omitempty"`
}

type ExecutionActionRequiredStateResp struct {
	ID             string `json:"id"`
	Status         string `json:"status"`
	RouteField     string `json:"route_field,omitempty"`
	Reason         string `json:"reason,omitempty"`
	ClaimedBy      string `json:"claimed_by,omitempty"`
	ClaimedAt      string `json:"claimed_at,omitempty"`
	ResolvedBy     string `json:"resolved_by,omitempty"`
	ResolvedAt     string `json:"resolved_at,omitempty"`
	ResolutionCode string `json:"resolution_code,omitempty"`
	ResolutionNote string `json:"resolution_note,omitempty"`
}
```

```go
type ExecutionResp struct {
	// existing fields...
	ActionRequired       bool                            `json:"action_required,omitempty"`
	ActionRequiredDetail *ExecutionActionRequiredStateResp `json:"action_required_detail,omitempty"`
}
```

- [ ] **Step 4: Replace raw-event list/summary/detail logic with record-backed helpers**

```go
func (s *ExecutionSrv) ListActionRequiredRecords(ctx context.Context, limit int) ([]dto.ExecutionActionRequiredResp, error)
func (s *ExecutionSrv) openActionRequiredCount(ctx context.Context) (int64, error)
func (s *ExecutionSrv) loadOpenActionRequiredMap(ctx context.Context, executionIDs []string) (map[string]*orchestrationModel.ActionRequiredRecord, error)
```

Use these rules:

```go
Where("status IN ?", []string{"pending", "claimed"})
Order("created_at desc").
Order("updated_at desc")
```

```go
func actionRequiredRespFromModel(
	record orchestrationModel.ActionRequiredRecord,
	execution *orchestrationModel.TemplateExecution,
) dto.ExecutionActionRequiredResp
```

- [ ] **Step 5: Add claim/resolve service methods and route wiring**

```go
type IExecution interface {
	ListActionRequiredRecords(ctx context.Context, limit int) ([]dto.ExecutionActionRequiredResp, error)
	ClaimActionRequiredRecord(ctx context.Context, id string, req dto.ClaimActionRequiredReq) (*dto.ExecutionActionRequiredResp, error)
	ResolveActionRequiredRecord(ctx context.Context, id string, req dto.ResolveActionRequiredReq) (*dto.ExecutionActionRequiredResp, error)
}
```

```go
g.GET("action-required", api.ListActionRequiredRecords)
g.POST("action-required/:id/claim", api.ClaimActionRequiredRecord)
g.POST("action-required/:id/resolve", api.ResolveActionRequiredRecord)
```

For optimistic updates:

```go
result := tx.Model(&orchestrationModel.ActionRequiredRecord{}).
	Where("id = ? AND status = ?", id, "pending").
	Updates(map[string]interface{}{
		"status":     "claimed",
		"claimed_by": operator,
		"claimed_at": now,
	})
```

```go
result := tx.Model(&orchestrationModel.ActionRequiredRecord{}).
	Where("id = ? AND status IN ?", id, []string{"pending", "claimed"}).
	Updates(map[string]interface{}{
		"status":          "resolved",
		"resolved_by":     operator,
		"resolved_at":     now,
		"resolution_code": req.ResolutionCode,
		"resolution_note": req.ResolutionNote,
	})
```

- [ ] **Step 6: Update the alert ticket compatibility consumer**

```go
items, err := a.OrchestrationExecutionSrv.ListActionRequiredRecords(ctx, 200)
```

Keep the HTTP surface unchanged for alert-ticket callers; only the source method changes.

- [ ] **Step 7: Re-run the backend tests**

Run: `cd OneOps && go test ./app/orchestration/service/impl ./app/alert/api -run 'Test(ExecutionService_|AlertTicketAPI_)' -count=1`

Expected: PASS.

## Task 4: Update the Observatory and Detail Pages for Real Operator State

**Files:**
- Modify: `OneOPS-UI/src/typings/orchestration/execution.ts`
- Modify: `OneOPS-UI/src/api/orchestration/execution.ts`
- Modify: `OneOPS-UI/src/views/platform/ExecutionObservatory.vue`
- Modify: `OneOPS-UI/src/views/platform/ExecutionDetailDebugger.vue`
- Modify: `OneOPS-UI/scripts/execution-observatory-smoke.ts`
- Modify: `OneOPS-UI/scripts/execution-detail-debugger-smoke.ts`

- [ ] **Step 1: Add failing UI smoke assertions for record lifecycle fields and claim/resolve APIs**

```ts
assert.match(apiSource, /export const claimActionRequiredReq = async/, 'should export claim api wrapper');
assert.match(apiSource, /export const resolveActionRequiredReq = async/, 'should export resolve api wrapper');
assert.match(typingSource, /claimed_by\\?: string;/, 'should expose claimed_by');
assert.match(typingSource, /resolution_code\\?: string;/, 'should expose resolution_code');
assert.match(viewSource, /认领/, 'observatory should render claim action');
assert.match(viewSource, /Resolve/, 'observatory should render resolve action');
assert.match(detailSource, /action_required_detail/, 'detail page should consume live action-required detail');
```

- [ ] **Step 2: Run the smoke scripts to verify they fail**

Run: `cd OneOPS-UI && pnpm tsx scripts/execution-observatory-smoke.ts && pnpm tsx scripts/execution-detail-debugger-smoke.ts`

Expected: FAIL because new fields and actions are not present yet.

- [ ] **Step 3: Extend typings and request wrappers**

```ts
export interface ExecutionActionRequiredResp {
  id: string;
  event_id?: string;
  execution_id: string;
  status: 'pending' | 'claimed' | 'resolved' | 'cancelled';
  claimed_by?: string;
  claimed_at?: string;
  resolved_by?: string;
  resolved_at?: string;
  resolution_code?: string;
  resolution_note?: string;
  updated_at: string;
}

export interface ClaimActionRequiredReq {
  operator: string;
  note?: string;
}

export interface ResolveActionRequiredReq {
  operator: string;
  resolution_code: string;
  resolution_note?: string;
}
```

```ts
export const claimActionRequiredReq = async (id: string, data: ClaimActionRequiredReq) => { /* ... */ };
export const resolveActionRequiredReq = async (id: string, data: ResolveActionRequiredReq) => { /* ... */ };
```

- [ ] **Step 4: Update the observatory Action Required tab to show record state and actions**

Add columns for:

```ts
status
claimed_by
claimed_at
updated_at
```

Use simple operator actions:

```ts
<a @click="handleClaim(record as ExecutionActionRequiredResp)">认领</a>
<a @click="handleResolve(record as ExecutionActionRequiredResp)">Resolve</a>
```

Behavior:
- after claim/resolve succeeds, reload `summary`, `executions`, and `actionRequired`
- resolved items disappear from the open summary count

- [ ] **Step 5: Update the execution detail page to render live action-required state**

```ts
<a-descriptions-item label="Action Required Status">
  {{ execution?.action_required_detail?.status || (execution?.action_required ? 'open' : '-') }}
</a-descriptions-item>
<a-descriptions-item label="Claimed By">
  {{ execution?.action_required_detail?.claimed_by || '-' }}
</a-descriptions-item>
<a-descriptions-item label="Resolution">
  {{ execution?.action_required_detail?.resolution_code || '-' }}
</a-descriptions-item>
```

Keep the page focused on real runtime state, not a template designer.

- [ ] **Step 6: Re-run the smoke scripts**

Run: `cd OneOPS-UI && pnpm tsx scripts/execution-observatory-smoke.ts && pnpm tsx scripts/execution-detail-debugger-smoke.ts`

Expected: PASS.

## Task 5: Real Verification, Runbook Update, and Operator Closure Proof

**Files:**
- Modify: `OneOPS-UI/scripts/execution-observatory-real-api-acceptance.ts`
- Modify: `docs/runbooks/alert-to-ticket-dagengine-mvp.md`

- [ ] **Step 1: Extend the real-api acceptance script to exercise the new operator lifecycle**

Add the following flow after an escalated execution appears in the action-required list:

```ts
const items = await getJson<ExecutionActionRequiredResp[]>(
  token,
  '/orchestration/executions/action-required?limit=20',
  'action required list',
);
const item = items.find(row => row.execution_id === startedExecution.id);
assert.ok(item, 'expected action-required record for escalated execution');

await postJson(token, `/orchestration/executions/action-required/${encodeURIComponent(item.id)}/claim`, {
  operator: 'ops_acceptance',
}, 'claim action required');

await postJson(token, `/orchestration/executions/action-required/${encodeURIComponent(item.id)}/resolve`, {
  operator: 'ops_acceptance',
  resolution_code: 'ticket_handed_off',
  resolution_note: 'acceptance flow completed',
}, 'resolve action required');
```

- [ ] **Step 2: Run backend verification**

Run:

```bash
cd OneOps
go test ./initialize ./app/orchestration/service/impl ./app/alert/api -count=1
```

Expected: all targeted tests PASS.

- [ ] **Step 3: Run frontend verification**

Run:

```bash
cd OneOPS-UI
pnpm tsx scripts/execution-observatory-smoke.ts
pnpm tsx scripts/execution-detail-debugger-smoke.ts
```

Expected: both scripts PASS.

- [ ] **Step 4: Run real stack acceptance**

Run:

```bash
cd OneOPS-UI
pnpm tsx scripts/execution-observatory-real-api-acceptance.ts
```

Expected:
- an execution reaches `escalated`
- `/orchestration/executions/action-required` returns a persisted record
- claim succeeds
- resolve succeeds
- execution summary open `action_required` count decreases after resolve

- [ ] **Step 5: Update the operator runbook**

Document:
- where the action-required tab lives
- how `pending -> claimed -> resolved` works
- why execution state and operator follow-up state are separate
- which outcomes map to `on_failure` and `on_timeout`

## Exit Criteria

- [ ] An escalated orchestration path persists both audit event and action-required record.
- [ ] `GET /orchestration/executions/action-required` is record-backed, not raw-event-backed.
- [ ] Operators can claim and resolve items through real APIs.
- [ ] Execution summary and detail page show live record state.
- [ ] Alert-ticket compatibility still works against the new record source.
- [ ] Real-api acceptance proves the full operator-takeover slice with a running stack.

## Spec Coverage Check

- First-class persisted record: covered by Task 1 and Task 2.
- Atomic runtime integration in escalated path: covered by Task 2.
- Record-backed observatory/detail state: covered by Task 3 and Task 4.
- Claim/resolve lifecycle: covered by Task 3 and Task 5.
- MVP discipline with no generic workbench/cancel workflow: preserved by Scope Decisions.

