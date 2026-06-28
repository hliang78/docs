# M1 Live Operator Triage Closeout Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing execution detail debugger into a live operator triage page that is good enough for the M1 closure mainline pilot.

**Architecture:** Keep the current observatory + detail page structure. Enrich the execution detail contract with operator-facing metadata, then use the existing page to present a concise triage summary and live refresh behavior.

**Tech Stack:** Go, GORM, existing orchestration execution APIs, Vue 3, Ant Design Vue, existing smoke scripts.

## Scope

- enrich `GET /orchestration/executions/:executionId`
- keep current runtime graph and event timeline
- add live polling on the detail page
- add operator summary and recommended next action

## Tasks

- [ ] Add execution detail contract fields needed for operator triage:
  - `trigger_source`
  - `alert_code`
  - `ticket_code`
  - `action_required`
- [ ] Extend backend tests to verify the enriched detail response.
- [ ] Add detail page live polling and clear it on unmount/route change.
- [ ] Add an operator summary block showing:
  - alert / ticket
  - trigger source
  - current blocking state
  - latest key event
  - recommended next action
- [ ] Extend smoke coverage so the new live-triage behavior is asserted.

## Exit Criteria

- [ ] The detail page updates automatically after manual launch.
- [ ] An operator can understand the execution’s current business context without opening raw JSON first.
- [ ] Smoke tests pass for the updated detail page contract and UI.
