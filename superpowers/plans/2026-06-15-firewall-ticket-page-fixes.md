# Firewall Ticket Page Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the firewall ticket page so status filters are usable, batch delete works, and stale row selections are cleared after destructive actions.

**Architecture:** Keep the fix local to the firewall ticket page component. Reuse the page's existing status enum data for filter options, wire selected values into the list request, and use the existing `ProTable` expose API to clear selection after delete flows instead of changing shared table behavior.

**Tech Stack:** Vue 3 SFC, TypeScript, Ant Design Vue, existing smoke-script workflow, vue-tsc.

---

### Task 1: Confirm page ownership and request shape

**Files:**
- Modify: `OneOPS-UI/src/views/ticket/FirewallTicket.vue`
- Modify: `OneOPS-UI/src/typings/ticket/firewall_ticket.ts`

- [ ] **Step 1: Inspect the route and page request type**

Run: `rg -n "ticket/firewall|FirewallTicket" OneOPS-UI/src && nl -ba OneOPS-UI/src/typings/ticket/firewall_ticket.ts | sed -n '1,80p'`
Expected: confirm `/ticket/firewall` resolves to `FirewallTicket.vue` and the list request type currently lacks `approval_status`.

- [ ] **Step 2: Update the request type to match page query usage**

Add `approval_status?: number` and make `execute_status` optional in `FirewallTicketPageReq` so the UI can omit empty filters cleanly.

- [ ] **Step 3: Re-run type-aware inspection mentally against current page code**

Expected: the page can construct a request with `code`, `name`, `execute_status`, and `approval_status` without type assertion hacks.

### Task 2: Make the filters usable

**Files:**
- Modify: `OneOPS-UI/src/views/ticket/FirewallTicket.vue`

- [ ] **Step 1: Write the failing behavior down from reproduction**

Expected failures before the fix:
- both status dropdowns render empty option lists
- `pageQuery()` always sends `execute_status: undefined`
- `approval_status` never reaches `firewallTicketPageReq()`

- [ ] **Step 2: Implement minimal filter wiring**

Use `workOrderStatusEnums` for `工单状态` options and derive an `approvalStatusOptions` array from approval-related statuses (`待批准`, `审核中`, `审批通过`, `已驳回`). Pass both arrays into the two `<a-select>` controls.

- [ ] **Step 3: Update `pageQuery()` to send real filter values**

Construct the request with:
- `execute_status: queryState.execute_status`
- `approval_status: queryState.approval_status`
Expected: clearing either field omits it naturally; selecting either field sends the chosen number.

### Task 3: Implement batch delete and clear stale selection

**Files:**
- Modify: `OneOPS-UI/src/views/ticket/FirewallTicket.vue`

- [ ] **Step 1: Reuse the table expose API**

Add a `table` ref for `<pro-table>` and read `selectedListCodes` from it, matching the pattern used in other pages.

- [ ] **Step 2: Implement `batchDeleteOrder()` with existing delete API**

If no row is selected, show `message.warning('请选择要删除的工单')`. Otherwise call the existing single-delete request for each selected code, wait for all requests to finish, then show one success toast summarizing the count.

- [ ] **Step 3: Clear selection after destructive actions**

Call `table.value?.clearSelection()` after single delete and after batch delete, then refresh the list. Expected: after the table empties, the footer no longer shows stale selection counts.

### Task 4: Verify with existing project checks

**Files:**
- Modify: `OneOPS-UI/scripts/firewall-ticket-page-smoke.ts` if missing, otherwise skip file changes

- [ ] **Step 1: Run focused static verification**

Run: `cd OneOPS-UI && npm run typecheck`
Expected: PASS for the updated page and typings.

- [ ] **Step 2: Run the closest existing firewall-ticket smoke helper**

Run: `cd OneOPS-UI && npm run smoke:firewall-ticket-precheck-page-helpers`
Expected: PASS, confirming the surrounding firewall ticket helper code still bundles and runs.

- [ ] **Step 3: Re-check the real page manually**

Open `/ticket/firewall` and verify:
- both dropdowns show options
- filtering sends selected statuses in the request body
- batch delete triggers delete requests and refreshes the list
- deleting the last row leaves no stale `已选择 N 项`
