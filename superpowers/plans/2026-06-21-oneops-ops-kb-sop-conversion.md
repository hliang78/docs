# OneOPS Ops KB/SOP Conversion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the provided external SOP Word document and incident workbook into OneOPS-native knowledge-base and runbook documents.

**Architecture:** Extract source structure first, then split the result into three Markdown deliverables with clear responsibilities: source map, incident-pattern knowledge, and an execution-oriented runbook. Use OneOPS capabilities as the main operational flow and keep legacy tools as fallback paths only.

**Tech Stack:** Markdown docs, repo-local shell tooling, bundled Python runtime for DOCX/XLSX extraction

---

### Task 1: Lock the target document set

**Files:**
- Create: `docs/superpowers/specs/2026-06-21-oneops-ops-kb-sop-design.md`
- Create: `docs/superpowers/plans/2026-06-21-oneops-ops-kb-sop-conversion.md`

- [ ] Confirm the spec states the three target deliverables and their responsibilities.
- [ ] Confirm the plan matches the approved approach: `docs/knowledge` for reusable knowledge and `docs/runbooks` for the operator procedure.

### Task 2: Summarize the source SOP taxonomy

**Files:**
- Create: `docs/knowledge/gpu-ops-sop-source-map-2026-06-21.md`

- [ ] Capture the original Word outline as compact section bullets.
- [ ] Map each major chapter into OneOPS-facing knowledge or runbook usage.
- [ ] Note what is intentionally not migrated, such as image-heavy hardware panels or raw screenshot guidance.

### Task 3: Extract incident patterns from the workbook

**Files:**
- Create: `docs/knowledge/gpu-server-fault-patterns-from-incident-log-2026-06-21.md`

- [ ] Summarize workbook scope: record count, fault vs event split, major server models.
- [ ] Extract top cause-to-solution pairs and per-model differences.
- [ ] Convert the raw frequencies into reusable operational guidance: top recurring fault classes, first actions, escalation triggers, and knowledge gaps.

### Task 4: Write the OneOPS runbook

**Files:**
- Create: `docs/runbooks/gpu-server-fault-response.md`

- [ ] Organize the runbook around the real operator lifecycle: trigger, triage, evidence collection, fault classification, remediation, validation, and knowledge closure.
- [ ] Rewrite the old SOP steps so the primary path uses OneOPS modules, with Zabbix/BMC/system commands as supporting evidence paths.
- [ ] Include focused command examples only where they materially help execution.

### Task 5: Verify and align

**Files:**
- Review: `docs/knowledge/gpu-ops-sop-source-map-2026-06-21.md`
- Review: `docs/knowledge/gpu-server-fault-patterns-from-incident-log-2026-06-21.md`
- Review: `docs/runbooks/gpu-server-fault-response.md`

- [ ] Re-read the generated docs and confirm they reflect the original SOP chapters and workbook patterns.
- [ ] Run a lightweight repo-style check by reading the files and verifying headings, tone, and path placement.
- [ ] Report any remaining gaps, especially sections that still depend on original screenshots or vendor-only procedures.
