# OneOps Orchestration Execution Detail Debugger Design

## 1. Goal

Build a real runtime debugging surface for one orchestration execution.

This design extends the existing execution observatory work. The observatory remains the list and entry surface. The new execution detail debugger becomes the focused page for understanding one execution end to end.

The page must help two user groups at the same time:

- operators who need to know where the execution is stuck, whether action is required, and what they can safely do next
- engineers who need to know which node ran, which agent task returned, which wait path was taken, and why the execution ended up in its current state

This is not a visual orchestration designer. It is a read-mostly runtime debugger with explicit resume actions for real waiting executions.

## 2. Scope

Included in this design:

- a dedicated execution detail page linked from the existing execution observatory
- a runtime graph for one execution
- a dual-view page structure for operations and debugging
- real approve, reject, and callback resume actions for waiting executions
- a lightweight backend graph projection API
- reuse of existing execution detail, event, and agent-task APIs

Excluded from this design:

- drag-and-drop template authoring
- online template mutation
- full execution context diff browser in phase 1
- multi-execution comparison
- visualization of hidden model reasoning or chain-of-thought
- introducing new runtime semantics beyond the existing execution model

## 3. Relationship To Existing Runtime Work

This project is parallel to, not inside, the `agentruntime` production-hardening work.

Recommended project split:

- `agentruntime-first-production-implementation-plan`
  - durable task execution
  - callback retry
  - recovery
  - service-to-service runtime behavior
- `execution-detail-debugger`
  - runtime observability for one execution
  - runtime graph projection
  - operator and engineer debugging surface

This keeps execution semantics owned by the existing orchestration runtime while adding a clearer runtime observation layer.

## 4. User Roles

### 4.1 Operations

Operations users primarily ask:

- what state is this execution in right now
- where is it waiting
- does it need human action
- if I approve, reject, or resume, what path will it follow

### 4.2 Engineering

Engineering users primarily ask:

- which node is current
- which nodes already completed or failed
- what agent tasks were created and what statuses they reached
- what events happened in time order
- what payload or error explains the current state

## 5. UX Positioning

The existing observatory remains the overview page:

- `/platform/execution-observatory`

The new execution detail debugger becomes the single-execution page:

- `/platform/execution-observatory/:executionId`

The observatory should continue to support a lightweight drawer if desired, but the primary debugging workflow should move to the dedicated page because the runtime graph and dual-view detail surface will outgrow the current drawer.

## 6. Page Architecture

The execution detail page should be organized in this order:

1. header summary
2. runtime main view
3. dual-view detail region
4. node inspector

This ordering intentionally follows the user journey:

`current state -> path -> action -> explanation`

### 6.1 Header Summary

The header shows:

- `execution_id`
- `template_code`
- `environment`
- `status`
- `alert_code`
- `ticket_code`
- `waiting_node_id`
- `wait_type`
- `action_required`

Actions:

- back to observatory list
- refresh
- open related alert or ticket when routes exist

### 6.2 Runtime Main View

The center of the page is split into two panes.

Left pane:

- execution runtime graph

Right pane:

- execution state panel
- wait and resume panel
- route explanation panel

The left pane answers:

- where the execution is now
- which path has already been taken
- which fallback routes exist

The right pane answers:

- why the execution is in the current state
- what actions are available
- where the execution will go next if an action is taken

### 6.3 Dual-View Detail Region

Use tabs to separate roles cleanly.

`Ops View` should emphasize:

- action required items
- current blocking reason
- escalation reason
- recommended next action
- recent key events

`Debug View` should emphasize:

- agent task timeline
- execution event timeline
- node error summary
- payload and result summaries

### 6.4 Node Inspector

Clicking a node in the runtime graph opens a focused node inspector that shows:

- `node_id`
- `node_type`
- runtime status
- wait type when relevant
- route fields
- related agent task summary
- related event summaries
- latest error and latest output summary

This inspector should stay compact in phase 1 and should not dump full raw blobs by default.

## 7. Runtime Graph Model

The runtime graph is an execution-instance graph, not a template editor graph.

### 7.1 Node Model

Each node should expose:

- `node_id`
- `node_name`
- `node_type`
- `runtime_status`
- `execution_status_hint`
- `is_current`
- `is_waiting`
- `is_action_required`
- `wait_type`
- `agent_task`
- `route`
- `summary`
- `last_error`
- `updated_at`

`runtime_status` should remain compact:

- `pending`
- `running`
- `waiting`
- `completed`
- `failed`
- `skipped`

Execution-wide states such as `waiting_approval`, `waiting_callback`, and `escalated` remain execution-level states and should appear as hints or page-level emphasis rather than exploding node status values.

### 7.2 Edge Model

Each edge should expose:

- `source`
- `target`
- `kind`
- `is_active`
- `is_taken`

`kind` should initially support:

- `next`
- `on_failure`
- `on_timeout`

This is enough for phase 1 to explain normal flow and operational fallbacks.

## 8. Graph Projection API

Add a dedicated lightweight read API:

- `GET /orchestration/executions/:executionId/graph`

The response should contain three sections:

- `execution`
- `nodes`
- `edges`

### 8.1 Execution Section

The execution section should contain the top-level runtime projection:

- `execution_id`
- `template_code`
- `environment`
- `status`
- `current_node_id`
- `waiting_node_id`
- `wait_type`
- `resume_token`
- `action_required`

### 8.2 Node Section

Each node should include:

- static route information
- runtime status projection
- lightweight agent-task summary when relevant
- one-line summary text for direct UI display

The graph API must not become the universal detail endpoint. Full payloads, raw event bodies, and large context snapshots remain on existing detail APIs.

### 8.3 Edge Section

Edges should allow the UI to distinguish:

- template structure
- current active path
- already taken path
- failure and timeout alternatives

## 9. Backend Projection Design

The backend implementation should be a thin projection service, not a new execution engine.

Conceptually:

`Execution + Loaded Template + Compiled Process + Events + AgentTasks + Wait State -> ExecutionGraphResp`

Recommended steps:

1. load execution record
2. load template bundle by `template_code` and `environment`
3. compile bundle into process structure
4. derive static nodes and edges
5. overlay execution state, wait state, events, and agent-task summaries
6. return graph DTO

Recompiling the template for this read path is acceptable in phase 1 because this is a debugging projection endpoint, not a hot execution path.

## 10. Frontend Design

The frontend should reuse the current observatory and the existing graph technology stack where it helps, but should not inherit editing complexity from template-debug tooling.

Recommended frontend structure:

- `ExecutionDetailPage`
- `ExecutionSummaryHeader`
- `ExecutionRuntimeGraph`
- `ExecutionOpsPanel`
- `ExecutionDebugPanel`
- `ExecutionNodeInspector`

Implementation principles:

- reuse the observatory as entry and navigation context
- render the execution graph as a read-only graph
- do not support drag, save-layout, or editing interactions in phase 1
- use backend projection as the source of runtime truth

## 11. Acceptance Criteria

Phase 1 is complete when all of the following are true:

1. users can navigate from the observatory list to a dedicated execution detail page
2. the page renders a real runtime graph for a real execution
3. the graph clearly shows the current node, waiting node, completed nodes, and failure or timeout route directions
4. the page can perform real `approve`, `reject`, and `resume callback` actions for waiting executions
5. the page shows both agent-task timeline and execution-event timeline
6. the page explains `waiting_approval`, `waiting_callback`, and `escalated` in operator-readable language instead of only raw status strings

## 12. Risks And Non-Goals

### 12.1 Do Not Build A Second Orchestration Designer

This page is for runtime diagnosis and control of waiting executions. It is not a design surface.

### 12.2 Do Not Turn Graph API Into A Blob API

Keep the graph API small and focused on structure plus runtime projection. Large raw detail stays on existing APIs.

### 12.3 Do Not Make The Frontend Infer Runtime Semantics

The backend must project node and edge runtime meaning. The frontend should render the projection rather than reconstruct orchestration semantics from scattered APIs.

## 13. Recommendation

Build this now, before expanding coordinator-style multi-agent behavior.

As multi-agent orchestration becomes richer, runtime observability becomes more important, not less. A lightweight execution detail debugger gives the platform a stable operational view before more autonomy is introduced.
