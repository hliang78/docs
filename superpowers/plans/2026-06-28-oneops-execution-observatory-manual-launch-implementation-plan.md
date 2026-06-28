# OneOps Execution Observatory Manual Launch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one lightweight UI action in the execution observatory that launches a real `multi-agent-closure` execution and redirects straight into the existing execution detail debugger.

**Architecture:** Keep this as a frontend-only slice. Reuse the existing `POST /orchestration/executions` backend contract, add a typed UI request helper, wire a single launch button into `ExecutionObservatory.vue`, and verify behavior with the repo's existing smoke-script pattern plus one real manual flow.

**Tech Stack:** Vue 3, TypeScript, Ant Design Vue, existing `request` API wrapper, existing orchestration execution typings, existing smoke scripts

---

## File Structure

### Existing files to modify

- `OneOPS-UI/src/api/orchestration/execution.ts`
  - add a typed `createExecutionReq` wrapper for `POST /orchestration/executions`
- `OneOPS-UI/src/typings/orchestration/execution.ts`
  - add request/response interfaces for manual execution launch
- `OneOPS-UI/src/views/platform/ExecutionObservatory.vue`
  - add the new page-header button, launch handler, lightweight loading state, unique code generation, success redirect, and failure messaging
- `OneOPS-UI/scripts/execution-observatory-smoke.ts`
  - extend the existing string-based smoke test to cover the new launch entry and route navigation
- `docs/runbooks/alert-to-ticket-dagengine-mvp.md`
  - document the page-level manual launch path so operators know how to trigger the real flow from the UI

### No new backend files

- this plan intentionally does not touch `OneOps` backend code

## Task 1: Add Typed Execution Launch API Contract

**Files:**
- Modify: `OneOPS-UI/src/typings/orchestration/execution.ts`
- Modify: `OneOPS-UI/src/api/orchestration/execution.ts`
- Modify: `OneOPS-UI/scripts/execution-observatory-smoke.ts`
- Test: `OneOPS-UI/scripts/execution-observatory-smoke.ts`

- [ ] **Step 1: Write the failing smoke assertions for the new API contract**

Add these assertions to `OneOPS-UI/scripts/execution-observatory-smoke.ts`:

```ts
  assert.match(
    apiSource,
    /export const createExecutionReq = async/,
    'should export createExecutionReq',
  );

  assert.match(
    typingSource,
    /export interface CreateExecutionReq/,
    'should define CreateExecutionReq',
  );

  assert.match(
    typingSource,
    /export interface CreateExecutionResp/,
    'should define CreateExecutionResp',
  );
```

- [ ] **Step 2: Run the smoke script to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
npm run smoke:execution-observatory
```

Expected:

```text
AssertionError [ERR_ASSERTION]: should export createExecutionReq
```

- [ ] **Step 3: Add minimal execution launch typings**

Append these interfaces to `OneOPS-UI/src/typings/orchestration/execution.ts` near the existing execution request/response types:

```ts
export interface CreateExecutionReq {
  template_code: string;
  environment: string;
  trigger_source: string;
  context?: Record<string, unknown>;
}

export interface CreateExecutionResp {
  id: string;
  template_code: string;
  environment: string;
  status: string;
  waiting_node_id?: string;
  wait_type?: string;
  resume_token?: string;
  created_at: string;
  updated_at: string;
}
```

- [ ] **Step 4: Add the minimal request wrapper**

Update the import list and append this helper to `OneOPS-UI/src/api/orchestration/execution.ts`:

```ts
import type {
  ApprovalDecisionReq,
  CallbackResumeReq,
  CreateExecutionReq,
  CreateExecutionResp,
  ExecutionActionRequiredResp,
  ExecutionAgentTaskResp,
  ExecutionEventResp,
  ExecutionGraphResp,
  ExecutionListReq,
  ExecutionListResp,
  ExecutionResp,
  ResumeResp,
  ExecutionSummaryResp,
} from '@/typings/orchestration/execution';
```

```ts
export const createExecutionReq = async (data: CreateExecutionReq) => {
  return request<CreateExecutionResp>({
    url: '/orchestration/executions',
    method: HTTP_POST,
    data,
  });
};
```

- [ ] **Step 5: Run the smoke script to verify the contract passes**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
npm run smoke:execution-observatory
```

Expected:

```text
✅ Execution observatory smoke passed
```

- [ ] **Step 6: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git add src/typings/orchestration/execution.ts src/api/orchestration/execution.ts scripts/execution-observatory-smoke.ts
git commit -m "feat: add execution launch api contract"
```

## Task 2: Add Manual Launch Entry To Execution Observatory

**Files:**
- Modify: `OneOPS-UI/src/views/platform/ExecutionObservatory.vue`
- Modify: `OneOPS-UI/scripts/execution-observatory-smoke.ts`
- Test: `OneOPS-UI/scripts/execution-observatory-smoke.ts`

- [ ] **Step 1: Write the failing smoke assertions for the page behavior**

Extend `OneOPS-UI/scripts/execution-observatory-smoke.ts` with these assertions:

```ts
  assert.match(viewSource, /发起真实多Agent闭环/, 'view should include manual launch button');
  assert.match(viewSource, /createExecutionReq/, 'view should use createExecutionReq');
  assert.match(viewSource, /execution_observatory_manual_launch/, 'view should use manual launch trigger source');
  assert.match(viewSource, /OBS-ALERT-/, 'view should generate observatory alert code');
  assert.match(viewSource, /OBS-TICKET-/, 'view should generate observatory ticket code');
  assert.match(
    viewSource,
    /name:\s*'ExecutionDetailDebugger'/,
    'view should navigate to ExecutionDetailDebugger after launch',
  );
```

- [ ] **Step 2: Run the smoke script to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
npm run smoke:execution-observatory
```

Expected:

```text
AssertionError [ERR_ASSERTION]: view should include manual launch button
```

- [ ] **Step 3: Add minimal launch state and helper functions**

In `OneOPS-UI/src/views/platform/ExecutionObservatory.vue`, add:

```ts
const manualLaunchSubmitting = ref(false);

function uniqueSuffix() {
  return Date.now().toString(36);
}

function buildManualLaunchPayload() {
  const suffix = uniqueSuffix();
  return {
    template_code: 'multi-agent-closure',
    environment: 'prod',
    trigger_source: 'execution_observatory_manual_launch',
    context: {
      alert_code: `OBS-ALERT-${suffix}`,
      ticket_code: `OBS-TICKET-${suffix}`,
    },
  };
}
```

Also extend the API imports:

```ts
import {
  approveExecutionReq,
  createExecutionReq,
  getExecutionReq,
  listExecutionAgentTasksReq,
  listExecutionEventsReq,
  listActionRequiredExecutionsReq,
  listExecutionsReq,
  rejectExecutionReq,
  resumeExecutionCallbackReq,
  getExecutionSummaryReq,
} from '@/api/orchestration/execution';
```

- [ ] **Step 4: Add the launch handler and redirect behavior**

In the same file, add:

```ts
async function handleManualLaunch() {
  manualLaunchSubmitting.value = true;
  try {
    const created = await createExecutionReq(buildManualLaunchPayload());
    message.success('真实多Agent闭环已发起，正在进入执行详情页');
    void router.push({
      name: 'ExecutionDetailDebugger',
      params: { executionId: created.id },
    });
  } catch (error) {
    message.error(error instanceof Error ? error.message : '发起真实多Agent闭环失败');
  } finally {
    manualLaunchSubmitting.value = false;
  }
}
```

- [ ] **Step 5: Add the page-header button without adding a modal**

In the page header `extra` block, add this button beside the existing refresh action:

```vue
<a-button type="primary" :loading="manualLaunchSubmitting" @click="handleManualLaunch">
  发起真实多Agent闭环
</a-button>
```

Keep the existing refresh button and do not add any confirmation modal in this MVP task.

- [ ] **Step 6: Run the smoke script to verify the page behavior passes**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
npm run smoke:execution-observatory
```

Expected:

```text
✅ Execution observatory smoke passed
```

- [ ] **Step 7: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git add src/views/platform/ExecutionObservatory.vue scripts/execution-observatory-smoke.ts
git commit -m "feat: add observatory manual launch entry"
```

## Task 3: Document And Verify The Real Flow

**Files:**
- Modify: `docs/runbooks/alert-to-ticket-dagengine-mvp.md`
- Test: `OneOPS-UI/scripts/execution-observatory-smoke.ts`

- [ ] **Step 1: Add the manual launch path to the runbook**

Append a short subsection under the observatory verification area in `docs/runbooks/alert-to-ticket-dagengine-mvp.md`:

```md
### Observatory Manual Launch

After the local stack is running, operators can start one real multi-agent closure execution directly from the page:

1. Open `http://127.0.0.1:3001/#/platform/execution-observatory`
2. Click `发起真实多Agent闭环`
3. Wait for the redirect into the execution detail debugger
4. Inspect runtime graph, agent tasks, and wait/resume actions on the returned execution

This page action uses the fixed MVP template `multi-agent-closure` in `prod` and is intended for real runtime verification rather than generic orchestration launch management.
```

- [ ] **Step 2: Re-run the smoke script to guard against regressions**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
npm run smoke:execution-observatory
```

Expected:

```text
✅ Execution observatory smoke passed
```

- [ ] **Step 3: Perform one real local verification**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
./scripts/start_multi_agent_closure_stack.sh start
```

Then open:

```text
http://127.0.0.1:3001/#/platform/execution-observatory
```

Manual expectation:

- the new button is visible
- clicking it creates a real execution
- the page redirects to `ExecutionDetailDebugger`
- the detail page begins showing real runtime state for the new execution

- [ ] **Step 4: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL
git -C OneOPS-UI add scripts/execution-observatory-smoke.ts src/views/platform/ExecutionObservatory.vue src/api/orchestration/execution.ts src/typings/orchestration/execution.ts
git -C OneOps add ../docs/runbooks/alert-to-ticket-dagengine-mvp.md
git -C OneOPS-UI commit -m "docs: capture observatory manual launch flow"
```

## Self-Review

### Spec coverage

- page header button: covered by Task 2
- fixed `multi-agent-closure` launch payload: covered by Task 2
- unique `alert_code` and `ticket_code`: covered by Task 2
- redirect to existing detail debugger route: covered by Task 2
- minimal success/failure feedback: covered by Task 2
- one smoke test: covered by Tasks 1 and 2 through the existing observatory smoke script
- runbook/operator verification: covered by Task 3

### Placeholder scan

- no `TODO`, `TBD`, or “similar to”
- every code-edit step includes concrete code
- every verification step includes exact commands and expected outcomes

### Type consistency

- `createExecutionReq` uses `CreateExecutionReq` and `CreateExecutionResp`
- `ExecutionObservatory.vue` calls `createExecutionReq` and navigates with route name `ExecutionDetailDebugger`
- launch payload keys match the current backend contract: `template_code`, `environment`, `trigger_source`, `context`

Plan complete and saved to `docs/superpowers/plans/2026-06-28-oneops-execution-observatory-manual-launch-implementation-plan.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
