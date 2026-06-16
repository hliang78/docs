# 2026-06-13 SNMP OID Online Test Design

## 1. Goal

This spec defines the first implementation slice for SNMP OID online testing inside the existing SNMP metric-group editor.

The goal is not to introduce a large new debug system.
The goal is to make new-device adaptation smoother by letting a user:

```text
select group
fill OID
test OID against a real target device
repair failures
save strategy
```

The primary UX requirement is simplicity:

- minimal explanation text;
- clear local buttons;
- test actions placed next to the OID being edited;
- save remains available but is not the primary next step.

## 2. Problem

The current SNMP metric-group page supports semantic editing, recording-rule preview/publish, and Grafana-related operations, but it does not provide a direct "fill OID then test it on a real device" loop.

That creates friction during new-device adaptation:

1. users can edit `oid`, but cannot immediately verify it on the page;
2. users do not know whether a newly added OID is actually readable on the target device;
3. save becomes visually more prominent than test/verify;
4. users are forced to rely on external tools or indirect debug paths.

For new-device adaptation, this is backward.
The correct sequence is:

```text
verify collection fact
then organize semantic contract
then save
```

## 3. Scope

This spec defines only the first in-page online test loop.

Included:

- a target-device input for the SNMP metric-group page;
- field-level OID test action;
- group-level batch test action;
- field-level test status;
- minimal backend API dedicated to this page;
- save-state interaction with untested OIDs.

Not included:

- full inventory-wide SNMP diagnostics;
- auto-remediation or OID suggestion;
- long-term test history;
- automatic publish of recording rules or dashboards after test;
- strategy-wide batch test across all groups;
- reuse of the full `template-debug-v2` pipeline/node UX inside the strategy page.

## 4. Product Principle

The page must guide by button hierarchy, not by large volumes of text.

This means:

- field-level `测试` is the strongest local action after an OID changes;
- group-level `测试本组待测项` supports batch confirmation after several edits;
- page-level `保存策略` remains available but is a closing action, not the immediate next action;
- status is shown with small visual markers and short labels rather than long explanations.

## 5. User Workflow

Canonical workflow:

1. user opens `SNMP 指标分组`;
2. user selects a metric group on the left;
3. user edits one or more `oid` fields in the center editor;
4. each edited field becomes `未测`;
5. user clicks field-level `测试` or group-level `测试本组待测项`;
6. results are shown inline next to the affected fields;
7. if any field fails, the UI automatically focuses the first failed field;
8. user repairs and re-tests;
9. user saves the strategy.

This workflow is intentionally local and repetitive.
It should feel like:

```text
edit
test
repair
re-test
save
```

not:

```text
edit
read many warnings
guess
save
```

## 6. Frontend UX Design

### 6.1 Page-Level Task Bar

The SNMP form page gets one compact task bar at the top of the main editor lane.

It should contain only:

- `target_part` input;
- one short readiness tag;
- page-level `保存策略`.

This bar defines test context and save state.
It must not also carry group-scoped test actions.

The readiness tag should stay minimal:

- `先输入目标设备`
- `待测试 N`
- `当前分组已就绪`

Long instructional sentences should not be the primary mechanism here.
The page should communicate flow through button placement and short status labels.

### 6.2 Page-Level Target Input

The task bar contains one light `target_part` input near the top of the editor context.

Purpose:

- define which real target device will be used for OID tests;
- make the test context explicit;
- avoid hiding target selection inside a modal or secondary page.

Rules:

- empty `target_part` means OID test buttons can still be visible, but testing fails fast with a short inline error;
- changing `target_part` invalidates all previous test statuses and resets them to `未测`.

### 6.3 Field-Level OID Test

Each editable OID row in `SnmpMetricGroupEditor.vue` gets:

- OID input;
- `测试` button;
- small status marker;
- one-line local feedback area.

This button is the main local action after an OID changes.

Field-level `测试` remains the primary action in the refined UI because the dominant new-device adaptation loop is:

```text
change one OID
test that OID immediately
repair if needed
continue
```

### 6.4 Group-Level Batch Test

The group editor header gets:

- `测试本组待测项`

Purpose:

- support users who fill several OIDs first and then verify them together;
- reduce repetitive single-field clicks;
- preserve a simple mental model.

The batch action only tests fields in the current group that are currently marked `未测`.

In the refined layout, this action belongs in the current group header rather than the page-level task bar.
It is a group-scoped accelerator, not the main page action.

### 6.5 Group Header Action Layout

The current group header becomes the local action bar for the active group.

Recommended action order:

- `新增字段`
- `加载 MIB 字段`
- `测试本组待测项`
- `继承/覆盖/禁用`

This keeps edit actions and group-level verification together, without competing with the page-level save bar.

### 6.6 Status Model

Field-level status values:

- `untested`
- `success`
- `failed`
- `testing`

Suggested display:

- gray: `未测`
- blue/spinner: `测试中`
- green: `通过`
- red: `失败`

The UI should not require a large status panel to understand this state.

### 6.7 Save Interaction

`保存策略` remains clickable even when some OIDs are untested.

Rules:

- save is not blocked by untested status;
- page-level save affordance shows a short degraded hint such as `待测试 N`;
- the presence of untested OIDs should reduce visual emphasis of save, but not disable it.

This is deliberate.
Users should be guided toward testing first, but not trapped.

### 6.8 Failure Navigation

When a group batch test contains failures:

- the UI automatically jumps to or focuses the first failed field;
- local error feedback stays near the field itself;
- failures should not be pushed into a large global alert stack by default.

### 6.9 Information De-Emphasis

To keep the OID test loop direct, the page should further reduce default competition from non-local information.

Recommended de-emphasis rules:

- left-side `策略上下文` should default to the most decision-relevant items such as current strategy, parent strategy, and inheritance state;
- manufacturer, platform, and model can remain available but should not dominate the first screen;
- contract-source and fallback details should remain accessible without acting like the main workflow;
- right-side compatibility and legacy alerts should stay secondary to the active group editor;
- `SnmpDashboardImpactPreview` should not visually outrank the OID edit-and-test area.

The page should feel like:

```text
set target
edit field
test field
optionally batch-test group
save
```

not like:

```text
scan sidebars
read system explanations
then discover where to test
```

## 7. Backend API Design

The strategy page should not be forced to consume the full `template-debug-v2` pipeline/node abstraction.

Instead, a dedicated API is introduced for this one narrow product action.

### 7.1 Endpoint

```text
POST /platform/metrics/teleabs/strategies/:id/snmp-metric/oid-test/by-target
```

This endpoint is strategy-scoped and target-scoped.

### 7.2 Request Modes

Two request modes are needed:

- `field`
- `group`

Field example:

```json
{
  "target_part": "SW-1",
  "group_key": "interface_basic",
  "metric_key": "if_in_rate",
  "base_oid": ".1.3.6.1.2.1.2.2.1",
  "oid": ".1.3.6.1.2.1.31.1.1.1.6",
  "mode": "field"
}
```

Group example:

```json
{
  "target_part": "SW-1",
  "group_key": "interface_basic",
  "mode": "group",
  "fields": [
    {
      "metric_key": "if_in_rate",
      "oid": ".1.3.6.1.2.1.31.1.1.1.6"
    },
    {
      "metric_key": "if_out_rate",
      "oid": ".1.3.6.1.2.1.31.1.1.1.10"
    }
  ]
}
```

### 7.3 Response Shape

The response should stay minimal and page-friendly.

Example:

```json
{
  "strategy_id": "strategy-1",
  "target_part": "SW-1",
  "group_key": "interface_basic",
  "results": [
    {
      "metric_key": "if_in_rate",
      "status": "success",
      "value_kind": "table",
      "sample_value": "123456",
      "message": "OID 可读取",
      "tested_at": "2026-06-13T10:00:00Z"
    },
    {
      "metric_key": "if_out_rate",
      "status": "failed",
      "value_kind": "error",
      "message": "设备上未返回该 OID",
      "tested_at": "2026-06-13T10:00:01Z"
    }
  ]
}
```

### 7.4 Response Semantics

`status` values:

- `success`
- `failed`

`value_kind` values:

- `scalar`
- `table`
- `empty`
- `error`

The backend does not need to expose a large debug transcript in this first round.
It only needs to return enough information for inline page feedback.

## 8. Backend Behavior Rules

### 8.1 Real Target Required

OID test is performed against a real device resolved by `target_part`.

If `target_part` cannot be resolved, the API returns a clear error.

No frontend metadata fallback is introduced for this path.

### 8.2 Missing OID

If an input field has no `oid`, the API must not guess.
It should return a failed result with a short message describing the missing input.

### 8.3 Partial Group Failure

For group mode:

- one field failure must not discard all successful sibling results;
- response remains per-field;
- frontend decides how to focus the first failure.

### 8.4 No Side Effects

This API is test-only.

It must not:

- mutate strategy data;
- publish recording rules;
- publish dashboards;
- write device facts as persistent contract state.

## 9. Frontend State Model

The editor needs a local state object keyed by:

```text
group_key + metric_key + target_part
```

Each key stores:

- `status`
- `message`
- `value_kind`
- `sample_value`
- `tested_at`

Rules:

1. editing `oid` resets that field to `untested`;
2. changing `target_part` invalidates all previous field states;
3. switching groups does not clear state by itself;
4. batch test updates only the fields included in the response.

## 10. Why Not Reuse Template Debug V2 Directly

The codebase already has a `snmp-item-preview` capability under `template-debug-v2`, but that system is shaped around:

- pipeline IDs;
- node IDs;
- snapshot IDs;
- preview stages;
- debug-session concepts.

That is too heavy for the SNMP strategy editing page.

This spec intentionally chooses a narrower dedicated endpoint because:

- the page action is simpler than pipeline debugging;
- the user mental model is "test this OID on that device", not "debug a staged runtime graph";
- introducing pipeline/node vocabulary into the strategy editor would make the UX less direct.

Implementation may still reuse lower-level backend collection/runtime helpers internally, but the page contract must stay simple.

## 11. Testing Strategy

### 11.1 Backend

Add targeted tests for:

- field-mode success;
- field-mode failed target resolution;
- field-mode failed missing OID;
- group-mode mixed success/failure;
- no-side-effect guarantee on test path.

### 11.2 Frontend

Add smoke coverage for:

- field edit resets status to `未测`;
- field test button wiring;
- group batch test button wiring;
- page-level task bar uses compact readiness states instead of long guidance text;
- first failed field auto-focus behavior;
- save summary showing short `待测试 N` style hint.

### 11.3 Manual Acceptance

Manual acceptance should verify:

1. user can enter `target_part`;
2. edit one OID and test it inline;
3. fill several OIDs and batch-test current group;
4. failed field is focused automatically;
5. save still works while untested items remain;
6. page-level task bar stays compact and action-oriented rather than explanation-heavy.

## 12. Intentional Deferrals

This first round intentionally defers:

- test history timeline;
- cross-group batch test;
- auto-detecting best target device;
- OID recommendation from MIB metadata;
- richer result typing such as index-level row diffs;
- direct coupling to recording-rule or Grafana publication;
- large right-side status boards for OID test results.

## 13. Success Criteria

This design is successful when:

1. users can test a single edited OID on a real target without leaving the SNMP metric-group page;
2. users can batch-test the current group’s untested OIDs;
3. failures are visible and actionable inline;
4. save remains available but no longer feels like the immediate next action after OID edits;
5. the main editor lane stays visually centered on `target_part -> field test -> group test -> save`;
6. the implementation does not import `template-debug-v2` complexity into the main SNMP strategy editor UX.
