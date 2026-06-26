# PR Core Gate Definition

Purpose: define the Phase 1 PR core gate contract for the shared platform testing baseline.

## Gate Contract

- `OneOPS` backend gate runs Go core tests plus `device_v2_envtest` dry/local core replay.
- `OneOPS-UI` gate runs selected smoke scripts for device ingest, device detail/read-model, precheck display, and monitoring task workbench signals.
- Combined target budget: 10 minutes.
- Failing status classes: `failed`, `finding` on P0/P1, missing required evidence.

## Execution Commands

- Backend local gate: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS && bash scripts/platform-testing-core.sh`
- Frontend local gate: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && bash scripts/platform-testing-core.sh`
