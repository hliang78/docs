## Gate Contract

- `OneOPS` backend gate runs Go core tests plus `device_v2_envtest` dry/local core replay.
- `OneOPS-UI` gate runs selected smoke scripts for device ingest, device detail/read-model, precheck display, and monitoring task workbench signals.
- Combined target budget: 10 minutes.
- Failing status classes: `failed`, `finding` on P0/P1, missing required evidence.
