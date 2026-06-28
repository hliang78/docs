# OneOps Execution Observatory Manual Launch Design

## 1. Goal

Add a lightweight page-level entry in the execution observatory so an operator or developer can launch one real multi-agent closure execution from the UI and immediately inspect the live runtime in the existing execution detail debugger.

This is a usability bridge between the current command-line acceptance flow and the already working observability pages.

## 2. Scope

### Included

- one manual launch button in the execution observatory page
- fixed MVP launch payload for the existing `multi-agent-closure` template
- unique `alert_code` and `ticket_code` generation on the client side
- success redirect to the existing execution detail debugger route
- minimal success and failure feedback
- one smoke test for the UI behavior

### Excluded

- template selection UI
- parameter form or advanced launch options
- approval handling changes
- new backend APIs
- scheduler, worker, or runtime behavior changes
- generic "run any orchestration template" control center

## 3. User Experience

### 3.1 Entry placement

The new entry lives in the `ExecutionObservatory` page header `extra` area beside the existing refresh action.

Suggested button label:

- `发起真实多Agent闭环`

### 3.2 Launch behavior

Clicking the button should immediately call the existing execution start API with a fixed payload:

- `template_code = multi-agent-closure`
- `environment = prod`
- `trigger_source = execution_observatory_manual_launch`
- `context.alert_code = <generated unique value>`
- `context.ticket_code = <generated unique value>`

The client-generated codes only need to be unique enough for local/operator debugging and acceptance-style tracing.

### 3.3 Success behavior

After a successful API response:

- show a success toast
- optionally refresh local list state only if cheap
- navigate directly to `ExecutionDetailDebugger`
- target route: `/#/platform/execution-observatory/:executionId`

The redirect is part of the feature, not an optional enhancement. The whole point is to move the user from "launch" into "observe and operate" immediately.

### 3.4 Failure behavior

If the launch request fails:

- show a concise error toast
- do not navigate
- keep the user on the observatory page

No retry workflow or recovery drawer is needed for this MVP slice.

## 4. Architecture

### 4.1 Frontend-only change

This feature should stay entirely in the existing UI layer and reuse the current orchestration execution API surface.

No new backend route is needed. The page should call the same execution creation API already used by acceptance scripts:

- `POST /orchestration/executions`

### 4.2 API wrapper

If the current UI API module does not already expose a create-execution request helper, add one in the orchestration execution API wrapper rather than calling the request utility inline from the page.

That keeps page logic small and aligns with existing `getExecutionReq`, `getExecutionGraphReq`, and related wrappers.

### 4.3 Route reuse

Execution detail navigation must reuse the existing route name and page:

- route name: `ExecutionDetailDebugger`
- page: `ExecutionDetailDebugger.vue`

This avoids introducing a duplicate "launch result" page.

## 5. Data Contract

The manual launch request should follow the current execution start payload shape:

```json
{
  "template_code": "multi-agent-closure",
  "environment": "prod",
  "trigger_source": "execution_observatory_manual_launch",
  "context": {
    "alert_code": "OBS-ALERT-<unique>",
    "ticket_code": "OBS-TICKET-<unique>"
  }
}
```

The exact unique suffix format is not important as long as:

- it is deterministic enough for debugging
- it does not require backend coordination
- it remains readable in the execution list

## 6. Implementation Boundaries

This button is intentionally opinionated and non-generic.

That means:

- no dropdown for template choice
- no environment override
- no editable JSON context
- no modal unless the page absolutely needs a confirmation step

The design goal is one-click real execution, not a new orchestration launch console.

If future work needs controlled launch parameters, that should be a separate spec and should not be folded into this MVP entry.

## 7. Testing

### 7.1 Smoke test

Add one smoke-style UI test that verifies:

- the observatory page renders the new button
- clicking the button triggers the execution creation request
- a successful response causes navigation to `ExecutionDetailDebugger`

### 7.2 Manual verification

The real operator check remains:

1. open the execution observatory page
2. click `发起真实多Agent闭环`
3. observe redirect into the execution detail debugger
4. confirm runtime graph, events, and agent tasks begin to populate with real data

## 8. Risks and Non-Goals

### 8.1 Risk

The button creates a real execution, so repeated clicking will create repeated real records.

For this MVP, that is acceptable because the purpose of the page is runtime verification with real executions. A future guardrail such as button cooldown or confirmation can be added only if real operator behavior shows it is necessary.

### 8.2 Non-goal

This feature does not solve "visual orchestration authoring" or "generic orchestration launch management." It only shortens the path from real launch to real runtime observation.
