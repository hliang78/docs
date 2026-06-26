# OneOPS Platform Testing Baseline Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the approved platform testing baseline spec into shared docs, domain appendix skeletons, a platform coverage matrix, and repo-local `PR core` gate scaffolding for `OneOPS` and `OneOPS-UI`.

**Architecture:** Keep shared guidance and evidence assets in the `docs` repo because the workspace root is not a git repository, then add execution-facing gate entrypoints and GitHub Actions workflows in the `OneOPS` and `OneOPS-UI` repos separately. Reuse existing `device_v2` fixtures, `device_v2_envtest`, Go tests, and front-end smoke commands instead of inventing a parallel test system.

**Tech Stack:** Markdown, GitHub Actions YAML, Bash, Go test, Python `device_v2_envtest`, Node/npm smoke scripts, existing docs/test assets under `docs/superpowers/testing`, `OneOPS`, and `OneOPS-UI`.

---

### Task 1: Create the shared baseline document set in the `docs` repo

**Files:**
- Create: `docs/superpowers/testing/platform-testing-baseline/README.md`
- Create: `docs/superpowers/testing/platform-testing-baseline/pr-core-gate-definition.md`
- Create: `docs/superpowers/testing/platform-testing-baseline/findings-and-boundaries.md`
- Modify: `docs/superpowers/specs/2026-06-26-oneops-platform-testing-baseline-design.md`
- Test: `docs/superpowers/testing/platform-testing-baseline/README.md`

- [ ] **Step 1: Create the baseline landing page with shared navigation**

```md
# OneOPS Platform Testing Baseline

## Contents

- [Platform Baseline Spec](../../specs/2026-06-26-oneops-platform-testing-baseline-design.md)
- [Platform Coverage Matrix](./platform-coverage-matrix.md)
- [Asset Inventory](./asset-inventory.md)
- [Network Devices Appendix](./appendix-network-devices.md)
- [Server Devices Appendix](./appendix-server-devices.md)
- [Firewall Devices Appendix](./appendix-firewall-devices.md)
- [PR Core Gate Definition](./pr-core-gate-definition.md)
- [Findings And Boundaries](./findings-and-boundaries.md)
```

- [ ] **Step 2: Create the PR core gate definition doc**

```md
## Gate Contract

- `OneOPS` backend gate runs Go core tests plus `device_v2_envtest` dry/local core replay.
- `OneOPS-UI` gate runs selected smoke scripts for device ingest, device detail/read-model, precheck display, and monitoring task workbench signals.
- Combined target budget: 10 minutes.
- Failing status classes: `failed`, `finding` on P0/P1, missing required evidence.
```

- [ ] **Step 3: Create the findings and boundaries ledger template**

```md
| ID | Domain | Status | Type | Summary | Source Evidence | Next Action |
| --- | --- | --- | --- | --- | --- | --- |
| FB-001 | device-v2 | open | boundary | Example boundary entry | link | classify |
```

- [ ] **Step 4: Add a “where to continue” pointer back into the approved spec**

```md
## Implementation Artifacts

Phase 1 implementation artifacts live under `docs/superpowers/testing/platform-testing-baseline/`.
```

- [ ] **Step 5: Verify the shared document set is linked correctly**

Run: `cd /Users/huangliang/project/OneOPS-ALL/docs && rg -n "Platform Coverage Matrix|PR Core Gate Definition|Findings And Boundaries" superpowers/testing/platform-testing-baseline superpowers/specs/2026-06-26-oneops-platform-testing-baseline-design.md`
Expected: PASS with matches in the new baseline docs and the spec pointer.

- [ ] **Step 6: Commit the shared baseline doc set**

```bash
git -C /Users/huangliang/project/OneOPS-ALL/docs add \
  superpowers/specs/2026-06-26-oneops-platform-testing-baseline-design.md \
  superpowers/testing/platform-testing-baseline/README.md \
  superpowers/testing/platform-testing-baseline/pr-core-gate-definition.md \
  superpowers/testing/platform-testing-baseline/findings-and-boundaries.md
git -C /Users/huangliang/project/OneOPS-ALL/docs commit -m "docs: add platform testing baseline hub"
```

### Task 2: Add the platform coverage matrix and current asset inventory

**Files:**
- Create: `docs/superpowers/testing/platform-testing-baseline/platform-coverage-matrix.md`
- Create: `docs/superpowers/testing/platform-testing-baseline/asset-inventory.md`
- Test: `docs/superpowers/testing/platform-testing-baseline/platform-coverage-matrix.md`

- [ ] **Step 1: Create the platform coverage matrix with the agreed dimensions**

```md
| Domain | Chain | Entry | Protocol | State | Truth Layer | Gate Level | Current Coverage | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Network | ingest -> collect -> monitor | ZB | SNMP | success | source + projection + runtime | PR core candidate | existing device-v2 harness | network owner |
| Server | ingest -> collect -> monitor | page store/start | SSH/IPMI | blocked | source + detail + runtime | nightly | gap | server owner |
| Firewall | import -> collect -> config facts | page import | SSH/API | success | source + detail | nightly | existing smoke/docs | firewall owner |
```

- [ ] **Step 2: Create the asset inventory from current repo reality**

```md
## Current Assets

- `OneOPS`: Go tests in `app/**`, `pkg/**`, `cmd/**`
- `OneOPS/tools/device_v2_envtest`: replay runner and report generation
- `OneOPS-UI`: smoke commands in `package.json`
- `docs/superpowers/testing/zb-device-v2-e2e-*.md`: harnessed + real-chain case inventory
- `docs/superpowers/acceptance/*.md`: acceptance checklists
```

- [ ] **Step 3: Record the three-repo execution topology explicitly**

```md
## Repo Topology Constraint

- shared docs live in `docs`
- backend gate executes in `OneOPS`
- frontend gate executes in `OneOPS-UI`
- workspace root is not a git repo, so no root-level GitHub Actions workflow should be created
```

- [ ] **Step 4: Verify matrix and inventory contain the mandatory sections**

Run: `cd /Users/huangliang/project/OneOPS-ALL/docs && rg -n "Repo Topology Constraint|Current Assets|Gate Level|Truth Layer" superpowers/testing/platform-testing-baseline/platform-coverage-matrix.md superpowers/testing/platform-testing-baseline/asset-inventory.md`
Expected: PASS with all four section labels present.

- [ ] **Step 5: Commit the matrix and inventory**

```bash
git -C /Users/huangliang/project/OneOPS-ALL/docs add \
  superpowers/testing/platform-testing-baseline/platform-coverage-matrix.md \
  superpowers/testing/platform-testing-baseline/asset-inventory.md
git -C /Users/huangliang/project/OneOPS-ALL/docs commit -m "docs: add testing baseline matrix and inventory"
```

### Task 3: Create the three domain appendix skeletons for parallel preparation

**Files:**
- Create: `docs/superpowers/testing/platform-testing-baseline/appendix-network-devices.md`
- Create: `docs/superpowers/testing/platform-testing-baseline/appendix-server-devices.md`
- Create: `docs/superpowers/testing/platform-testing-baseline/appendix-firewall-devices.md`
- Test: `docs/superpowers/testing/platform-testing-baseline/appendix-network-devices.md`

- [ ] **Step 1: Create the shared appendix skeleton structure**

```md
## Domain Scope
## Critical Journeys
## Device / Protocol / Capability Matrix
## Failure Modes And Boundaries
## P0 / P1 / P2 Scenario List
## Fixture And Sample Requirements
## Local Integration And Real-World Validation
## Gate Eligibility
```

- [ ] **Step 2: Seed the network appendix with network-specific starters**

```md
## Critical Journeys

- device ingest -> SNMP collect -> monitor push -> runtime health
- device ingest -> SSH collect -> identity correction -> monitor push
```

- [ ] **Step 3: Seed the server appendix with server-specific starters**

```md
## Critical Journeys

- device ingest -> SSH collect -> monitor push
- device ingest -> IPMI / OOB collect -> monitor template selection
```

- [ ] **Step 4: Seed the firewall appendix with firewall-specific starters**

```md
## Critical Journeys

- page import -> online collection -> fact parse -> detail/read-model verification
- config/object workflow -> precheck -> collection result display
```

- [ ] **Step 5: Verify every appendix has the full template**

Run: `cd /Users/huangliang/project/OneOPS-ALL/docs && for f in superpowers/testing/platform-testing-baseline/appendix-*.md; do echo "== $f =="; rg -n "Domain Scope|Critical Journeys|Failure Modes And Boundaries|Gate Eligibility" "$f"; done`
Expected: PASS with all headings matched in all three appendix files.

- [ ] **Step 6: Commit the appendix skeletons**

```bash
git -C /Users/huangliang/project/OneOPS-ALL/docs add superpowers/testing/platform-testing-baseline/appendix-*.md
git -C /Users/huangliang/project/OneOPS-ALL/docs commit -m "docs: add testing baseline domain appendix skeletons"
```

### Task 4: Add backend PR-core entrypoints in `OneOPS`

**Files:**
- Create: `OneOPS/scripts/platform-testing-core.sh`
- Create: `OneOPS/.github/workflows/platform-testing-core.yml`
- Modify: `OneOPS/tools/device_v2_envtest/README.md`
- Test: `OneOPS/scripts/platform-testing-core.sh`

- [ ] **Step 1: Add a backend core gate script with explicit phases**

```bash
#!/usr/bin/env bash
set -euo pipefail

go test ./app/device/... -count=1
go test ./app/platform/api -count=1
go test ./app/platform/service/impl -run 'TestMonitoringV2|Test.*DeviceV2' -count=1
(cd tools/device_v2_envtest && python3 -m unittest discover -s tests -p 'test_*.py')
```

- [ ] **Step 2: Add a GitHub Actions workflow for the self-hosted runner**

```yaml
name: platform-testing-core
on:
  pull_request:
    branches: [ main ]
jobs:
  backend-core:
    runs-on: [self-hosted, linux, oneops]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version-file: go.mod
      - name: Run backend core gate
        run: bash scripts/platform-testing-core.sh
```

- [ ] **Step 3: Document the backend core script in `device_v2_envtest` README**

```md
## PR Core Usage

Backend PR core uses `scripts/platform-testing-core.sh` and intentionally runs only local, fixture-backed checks suitable for self-hosted PR gating.
```

- [ ] **Step 4: Verify the backend gate script is syntactically valid**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS && bash -n scripts/platform-testing-core.sh`
Expected: PASS with no shell syntax errors.

- [ ] **Step 5: Verify the workflow references the self-hosted runner and gate script**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS && rg -n "self-hosted|platform-testing-core.sh|pull_request" .github/workflows/platform-testing-core.yml`
Expected: PASS with the three required workflow signals present.

- [ ] **Step 6: Commit the backend gate scaffolding**

```bash
git -C /Users/huangliang/project/OneOPS-ALL/OneOPS add \
  .github/workflows/platform-testing-core.yml \
  scripts/platform-testing-core.sh \
  tools/device_v2_envtest/README.md
git -C /Users/huangliang/project/OneOPS-ALL/OneOPS commit -m "ci: add backend platform testing core gate"
```

### Task 5: Add frontend PR-core entrypoints in `OneOPS-UI`

**Files:**
- Modify: `OneOPS-UI/package.json`
- Create: `OneOPS-UI/scripts/platform-testing-core.sh`
- Create: `OneOPS-UI/.github/workflows/platform-testing-core.yml`
- Test: `OneOPS-UI/scripts/platform-testing-core.sh`

- [ ] **Step 1: Add an aggregate frontend core npm command**

```json
"smoke:platform-testing-core": "npm run smoke:precheck-display && npm run smoke:device-v2-error-display && npm run smoke:device-v2-ops-status-cell && npm run smoke:device-v2-detail-collection-model"
```

- [ ] **Step 2: Add a frontend core gate wrapper**

```bash
#!/usr/bin/env bash
set -euo pipefail

npm ci
npm run smoke:platform-testing-core
```

- [ ] **Step 3: Add the frontend GitHub Actions workflow**

```yaml
name: platform-testing-core
on:
  pull_request:
    branches: [ main ]
jobs:
  frontend-core:
    runs-on: [self-hosted, linux, oneops-ui]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - name: Run frontend core gate
        run: bash scripts/platform-testing-core.sh
```

- [ ] **Step 4: Verify the frontend wrapper is syntactically valid**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && bash -n scripts/platform-testing-core.sh`
Expected: PASS with no shell syntax errors.

- [ ] **Step 5: Verify the aggregate npm command is discoverable**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && rg -n '"smoke:platform-testing-core"' package.json`
Expected: PASS with one match in `package.json`.

- [ ] **Step 6: Commit the frontend gate scaffolding**

```bash
git -C /Users/huangliang/project/OneOPS-ALL/OneOPS-UI add \
  package.json \
  scripts/platform-testing-core.sh \
  .github/workflows/platform-testing-core.yml
git -C /Users/huangliang/project/OneOPS-ALL/OneOPS-UI commit -m "ci: add frontend platform testing core gate"
```

### Task 6: Link the docs and gate entrypoints into one executable Phase 1 baseline

**Files:**
- Modify: `docs/superpowers/testing/platform-testing-baseline/pr-core-gate-definition.md`
- Modify: `docs/superpowers/testing/platform-testing-baseline/asset-inventory.md`
- Modify: `docs/superpowers/testing/platform-testing-baseline/platform-coverage-matrix.md`
- Test: `docs/superpowers/testing/platform-testing-baseline/pr-core-gate-definition.md`

- [ ] **Step 1: Document the exact backend gate command**

```md
### Backend Gate Entry

`cd /Users/huangliang/project/OneOPS-ALL/OneOPS && bash scripts/platform-testing-core.sh`
```

- [ ] **Step 2: Document the exact frontend gate command**

```md
### Frontend Gate Entry

`cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && bash scripts/platform-testing-core.sh`
```

- [ ] **Step 3: Tag PR-core matrix rows explicitly**

```md
| Network | ingest -> collect -> monitor | page store/start | SNMP | blocked | source + detail + runtime | PR core | planned |
```

- [ ] **Step 4: Verify the docs reference both repo-local gate commands**

Run: `cd /Users/huangliang/project/OneOPS-ALL/docs && rg -n "OneOPS-UI && bash scripts/platform-testing-core.sh|OneOPS && bash scripts/platform-testing-core.sh" superpowers/testing/platform-testing-baseline`
Expected: PASS with both backend and frontend gate entries documented.

- [ ] **Step 5: Commit the final doc wiring**

```bash
git -C /Users/huangliang/project/OneOPS-ALL/docs add superpowers/testing/platform-testing-baseline/pr-core-gate-definition.md superpowers/testing/platform-testing-baseline/asset-inventory.md superpowers/testing/platform-testing-baseline/platform-coverage-matrix.md
git -C /Users/huangliang/project/OneOPS-ALL/docs commit -m "docs: wire baseline docs to repo core gates"
```

## Self-Review

### Spec Coverage

- Shared total guidance: covered by Tasks 1, 2, and 6.
- Domain appendix skeletons for network/server/firewall: covered by Task 3.
- Existing asset takeover and matrix framing: covered by Task 2.
- PR-core gate definition and self-hosted runner path: covered by Tasks 4, 5, and 6.
- Shared evidence and findings path: covered by Task 1.

No spec requirement was intentionally left without a task. Real-device validation and performance expansion remain outside Phase 1 implementation scope by design.

### Placeholder Scan

- No `TBD`
- No `TODO`
- No “similar to previous task”
- All tasks name exact files and exact commands

### Consistency Check

- Shared docs always live in `docs/superpowers/testing/platform-testing-baseline/`
- Backend gate always lives in `OneOPS/scripts/platform-testing-core.sh`
- Frontend gate always lives in `OneOPS-UI/scripts/platform-testing-core.sh`
- Repo topology constraint is explicit: no root-level workflow because workspace root is not a git repo
