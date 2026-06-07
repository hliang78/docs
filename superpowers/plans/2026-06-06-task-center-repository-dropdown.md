# Task Center Repository Dropdown Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace manual repository/path entry in the task center create modal with dropdown selection and graceful fallback.

**Architecture:** Add a focused helper for repository dropdown option construction and fallback predicates. Update `TaskManagement.vue` to use repository select options and load repository files through the existing Script Studio API. Keep task template catalog data free of deployment-specific repository URLs; resolve addresses from repository records.

**Tech Stack:** Vue 3, Ant Design Vue, TypeScript, esbuild smoke test.

---

### Task 1: Helper and Smoke Test

**Files:**
- Create: `OneOps-UI/src/views/platform/taskRepositoryDropdown.ts`
- Create: `OneOps-UI/scripts/task-repository-dropdown-smoke.ts`
- Modify: `OneOps-UI/package.json`

- [ ] Write a smoke test that imports `buildRepositoryDropdownOptions`, `repositoryDropdownKey`, and `shouldUsePathDropdown`.
- [ ] Run `npm run smoke:task-repository-dropdown` and confirm it fails because the helper does not exist.
- [ ] Implement the helper with deterministic de-duplication and default-first ordering.
- [ ] Run `npm run smoke:task-repository-dropdown` and confirm it passes.

### Task 2: Task Form UI

**Files:**
- Modify: `OneOps-UI/src/views/platform/TaskManagement.vue`

- [ ] Import `listScriptStudioRepositoryFilesReq` and the new helper functions.
- [ ] Add state for repository file options, loading, error, and loaded key.
- [ ] Replace the custom repository URL input with a repository dropdown when options exist; keep the input fallback when options are empty.
- [ ] Replace the playbook/path input with a searchable path dropdown when repository file browsing is available; keep the input fallback when disabled or failed.
- [ ] Clear stale file options when repository, branch, app type, Git credential, or project changes.
- [ ] Remove deployment-specific `repo_url` values from the quick-env task template catalog.

### Task 3: Verification

**Files:**
- `OneOps-UI/src/views/platform/TaskManagement.vue`
- `OneOps-UI/src/views/platform/taskRepositoryDropdown.ts`
- `OneOps-UI/scripts/task-repository-dropdown-smoke.ts`

- [ ] Run `npm run smoke:task-repository-dropdown`.
- [ ] Run `npm run typecheck`.
- [ ] Report any pre-existing dirty files separately from this change.
