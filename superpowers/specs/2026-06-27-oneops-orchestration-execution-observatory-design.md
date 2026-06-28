# OneOps Orchestration Execution Observatory Design

## 1. Goal

Build a real, operator-usable observability page for orchestration executions in test/pre-production environments.

This is not a mock demo. The page must read real execution data, reflect real execution progress, and allow operators to understand:

- what executions are currently running
- what executions are waiting
- what executions have escalated into manual action
- how a specific execution progressed over time

The first phase focuses on visibility and safe navigation, not direct in-page mutation of execution state.

## 2. Scope

Included in this design:

- a hidden real-environment UI entry in `OneOPS-UI`
- an execution overview page organized by orchestration `execution`
- summary cards, filtered execution list, and execution detail drawer
- an `Action Required` tab for `execution_action_required` items
- lightweight backend list and summary APIs required by the page
- polling-based refresh for real test/pre environments

Excluded from this design:

- production rollout
- SSE or WebSocket live streaming
- direct approve/reject/resume actions on the overview page
- full-blown orchestration designer/editor
- new runtime semantics beyond current MVP

## 3. Primary User Experience

The first page a user sees must answer one question immediately:

`Is orchestration actually running in this environment right now?`

The page therefore starts with:

1. status summary cards
2. a filtered execution list
3. a detail drawer opened from a selected execution

The same page also includes an `Action Required` tab so operators can quickly switch from passive observation to manual follow-up discovery.

## 4. UI Placement

Phase 1 should be a hidden route in `OneOPS-UI`, available only for test/pre environments or explicit internal access.

Recommended route:

- `/platform/execution-observatory`

This avoids polluting the formal production-facing menu while still making the page easy to access for real validation and staged rollout.

## 5. Page Structure

### 5.1 Single-page two-tab layout

The page should be implemented as one page with two tabs:

- `Executions`
- `Action Required`

This is preferred over multiple independent pages because:

- rollout is faster
- demo and validation are more focused
- users keep context while switching from observation to action discovery

### 5.2 `Executions` tab

The tab contains four regions:

1. environment banner
2. status summary cards
3. filter toolbar
4. execution list with detail drawer

#### Environment banner

Show a clear label such as:

- `Test Environment`
- `Pre-Production Environment`

This reduces the chance of misreading the page as a production control console.

#### Status summary cards

Cards:

- `Running`
- `Waiting`
- `Escalated`
- `Completed / Failed`

Cards are interactive filters. Clicking a card narrows the execution list.

#### Filter toolbar

Initial filters:

- `status`
- `template_code`
- `keyword`
- `time range`
- `auto refresh`

The filter bar should stay compact and operational, not analytics-heavy.

#### Execution list

Each row represents one real orchestration execution.

Initial columns:

- `execution_id`
- `status`
- `template_code`
- `last_node`
- `wait_type`
- `alert_code`
- `ticket_code`
- `updated_at`

Behavior:

- `execution_id` opens detail drawer
- `status` uses strong visual color coding
- `waiting_*` and `escalated` rows should be visually more prominent
- `ticket_code` and `alert_code` can link to existing pages when those routes already exist

### 5.3 Execution detail drawer

The drawer is the core debugging surface for one execution.

It should be split into three sections:

#### Current summary

- execution id
- status
- template code
- environment
- current or last node
- waiting node
- wait type
- alert code
- ticket code
- created at
- updated at

#### Key context

Do not dump raw JSON first.

Show important fields first:

- `alert_code`
- `ticket_code`
- `approval_decision`
- `approval_operator`
- `vendor_ticket_code`
- `terminal_outcome.status`
- `terminal_outcome.route_field`

Then provide an expandable raw JSON viewer for full context.

#### Event timeline

Timeline items come from persisted execution events.

Important event types include:

- `execution_started`
- `node_waiting`
- `node_resumed`
- `execution_completed`
- `execution_failed`
- `execution_escalated`
- `execution_action_required`

Each item should show:

- time
- event type
- node id
- short human-readable summary
- expandable raw payload

### 5.4 `Action Required` tab

This tab is an operator workbench, not a general workflow page.

Its responsibilities are:

1. show which executions require manual attention
2. explain why they require attention
3. route the operator to the correct next page

Initial table columns:

- `ticket_code`
- `execution_id`
- `execution_status`
- `action_key`
- `route_field`
- `reason`
- `node_id`
- `occurred_at`

Initial actions:

- open execution detail
- open related ticket
- open related alert when available

The page should not directly perform approve/reject/resume in phase 1.

## 6. Refresh Model

Use polling in phase 1.

Recommended default:

- refresh every 15 seconds

User controls:

- pause refresh
- resume refresh
- show last refresh time

Polling is preferred because it is reliable, easy to operate in test/pre, and much cheaper to implement than push-based real-time delivery.

## 7. Backend Contract

### 7.1 Existing APIs reused

- `GET /orchestration/executions/:executionId`
- `GET /orchestration/executions/:executionId/events`
- `GET /orchestration/executions/action-required`
- `GET /alert/ticket/:code/orchestration-actions`

### 7.2 New APIs required

#### `GET /orchestration/executions/summary`

Purpose:

- power top summary cards efficiently

Response:

- `running_count`
- `waiting_count`
- `escalated_count`
- `completed_count`
- `failed_count`
- `updated_at`

#### `GET /orchestration/executions`

Purpose:

- power the main execution table

Query parameters:

- `status`
- `template_code`
- `keyword`
- `time_from`
- `time_to`
- `page`
- `page_size`

Each row should include:

- `execution_id`
- `status`
- `template_code`
- `waiting_node_id`
- `wait_type`
- `alert_code`
- `ticket_code`
- `last_node`
- `created_at`
- `updated_at`

### 7.3 Stability requirement

The `action-required` response should guarantee these fields in phase 1:

- `execution_id`
- `template_code`
- `execution_status`
- `ticket_code`
- `alert_code`
- `action_key`
- `action_status`
- `route_field`
- `reason`
- `occurred_at`

## 8. Frontend Implementation Shape

Recommended files:

- `src/views/platform/ExecutionObservatory.vue`
- `src/api/orchestration/execution.ts`
- `src/typings/orchestration/execution.ts`

The first phase should stay as a single-page implementation with tabs, not a nested route tree.

The page should follow established `OneOPS-UI` patterns:

- `Ant Design Vue`
- existing `ProTable`-style list patterns
- right-side detail drawers
- explicit empty/error/loading states

## 9. Safety Boundaries

This page reads and navigates real state, so the safety model must be explicit:

- page is hidden or restricted in test/pre
- page clearly labels the environment
- page does not directly mutate execution state in phase 1
- action tabs route operators to the existing or dedicated handling pages instead of performing silent inline actions

## 10. Error Handling

### 10.1 Summary failure

If summary loading fails:

- show inline warning
- keep list usable

### 10.2 List failure

If execution list loading fails:

- show explicit error state
- provide retry button

### 10.3 Drawer failure

If detail loading fails:

- keep overview page intact
- show drawer-local error state

### 10.4 Empty state

When no executions match filters:

- show clear empty state text
- do not display misleading zero-like cards as success

## 11. Verification Strategy

The page must be validated with real environment data in test/pre.

Minimum acceptance scenarios:

1. load page and see non-mock execution data
2. click a summary card and see filtered execution rows
3. open an execution drawer and see real event timeline data
4. switch to `Action Required` and see pending manual items when they exist
5. open an alert ticket and confirm `orchestration-actions` can show ticket-specific items

Recommended smoke coverage:

- backend contract tests for new list and summary APIs
- frontend smoke for page load and tab switching
- one real-environment acceptance run using actual seeded or naturally occurring executions

## 12. Rollout Order

Recommended implementation order:

1. backend `summary` and `execution list` APIs
2. frontend execution overview page shell
3. execution detail drawer with event timeline
4. `Action Required` tab
5. hidden route registration and test/pre environment gating

## 13. Recommendation

The preferred phase-1 solution is:

- hidden test/pre route
- single-page `Execution Observatory`
- two tabs: `Executions` and `Action Required`
- polling refresh
- real backend data only
- navigation-first operator flow instead of direct in-page state mutation

This gives OneOps a real, credible orchestration runtime observation surface quickly, while keeping scope and operational risk under control.
