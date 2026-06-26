# PR Core Gate Definition

Purpose: define the Phase 1 PR core gate contract for the shared platform testing baseline.

## Gate Contract

- `OneOPS` backend gate runs Go core tests plus `device_v2_envtest` dry/local core replay.
- `OneOPS-UI` gate runs selected smoke scripts for device ingest, device detail/read-model, precheck display, and monitoring task workbench signals.
- Combined target budget: 10 minutes.
- Failing status classes: `failed`, `finding` on P0/P1, missing required evidence.

## Execution Commands

- From workspace root, run backend local gate: `cd OneOPS && bash scripts/platform-testing-core.sh`
- From workspace root, run frontend local gate: `cd OneOPS-UI && bash scripts/platform-testing-core.sh`

## Verification Snapshot

- On June 26, 2026, `cd OneOPS-UI && bash scripts/platform-testing-core.sh` passed locally after fixing nested `precheck_display` extraction precedence in `extractPrecheckDisplay`.
- On June 26, 2026, backend Go segments passed locally; the envtest Python suite proved it still depends on a Python 3.12 environment plus `device_v2_envtest` package dependencies.
- Backend CI now bootstraps Python 3.12 and installs `./tools/device_v2_envtest` before running `scripts/platform-testing-core.sh`, so the workflow contract matches the package's declared runtime needs.
