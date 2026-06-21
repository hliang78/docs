# GPU Server Inspection And Go-Live Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a OneOPS-native runbook for GPU server inspection and go-live readiness.

**Architecture:** Convert the original SOP checks and test items into a single staged operator document: static checks, runtime checks, and acceptance validation. Keep specialized recovery work delegated to the existing BMC, IB/ROCE, and OS reinstall runbooks.

**Tech Stack:** Markdown docs, repo-local document linking

---

### Task 1: Define the runbook scope

**Files:**
- Create: `docs/superpowers/specs/2026-06-21-gpu-server-inspection-go-live-design.md`
- Create: `docs/superpowers/plans/2026-06-21-gpu-server-inspection-go-live-plan.md`

- [ ] Confirm the runbook covers inspection, go-live readiness, and acceptance only.
- [ ] Confirm recovery-heavy content stays in the existing specialized runbooks.

### Task 2: Write the inspection and go-live runbook

**Files:**
- Create: `docs/runbooks/gpu-server-inspection-and-go-live-readiness.md`

- [ ] Add staged sections for entry conditions, static checks, runtime checks, validation tests, acceptance grading, and evidence closure.
- [ ] Include only focused command examples that help operators verify state.
- [ ] Keep the document OneOPS-first and avoid copying sensitive source details.

### Task 3: Wire the document into the doc set

**Files:**
- Modify: `docs/knowledge/gpu-ops-sop-source-map-2026-06-21.md`
- Modify: `docs/runbooks/gpu-server-fault-response.md`
- Modify: `docs/runbooks/gpu-server-os-reinstall-and-baseline.md`

- [ ] Add links from the source map and related runbooks to the new document.
- [ ] Make sure the doc set now reads as overview -> inspection/readiness -> response -> specialized recovery.

### Task 4: Verify

**Files:**
- Review: `docs/runbooks/gpu-server-inspection-and-go-live-readiness.md`

- [ ] Check headings, file placement, and link targets.
- [ ] Run a sensitive-string scan to confirm no raw credentials or internal download details leaked in.
