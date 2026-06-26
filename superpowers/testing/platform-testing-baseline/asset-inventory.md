# Asset Inventory

This inventory records the current testing-adjacent assets already present across the shared docs, backend repo, and frontend repo. It is scoped to what exists now so follow-on gate work can start from real artifacts instead of placeholders.

## Current Assets

- `OneOPS`: Go tests in `app/**`, `pkg/**`, `cmd/**`
- `OneOPS/tools/device_v2_envtest`: replay runner, seeded cases, and report generation
- `OneOPS-UI`: smoke commands in `package.json`
- `docs/superpowers/testing/zb-device-v2-e2e-*.md`: device-v2 e2e planning, handoff, and overlooked-factor notes
- `docs/superpowers/acceptance/*.md`: acceptance checklists

## Current Repo Reality

- `docs/superpowers/testing/zb-device-v2-e2e-master-outline.md` and `docs/superpowers/testing/zb-device-v2-e2e-overlooked-factors.md` already describe network-device e2e coverage boundaries from the shared docs side.
- `OneOPS/tools/device_v2_envtest` already includes suite configs, executable cases such as SNMP, SSH, IPMI, and Redfish, plus HTML/JSON/Markdown reporters.
- `OneOPS-UI/package.json` already exposes many smoke commands, including device-v2, firewall, D2, and netpath-oriented flows.
- `docs/superpowers/acceptance` already contains checklist-style acceptance assets that can anchor human validation before automation is promoted.

## Landed Repo-Level Gate Entrypoints

- Backend local script: `OneOPS/scripts/platform-testing-core.sh`
- Backend workflow: `OneOPS/.github/workflows/platform-testing-core.yml`
- Frontend local script: `OneOPS-UI/scripts/platform-testing-core.sh`
- Frontend workflow: `OneOPS-UI/.github/workflows/platform-testing-core.yml`

## Repo Topology Constraint

- shared docs live in `docs`
- backend gate executes in `OneOPS`
- frontend gate executes in `OneOPS-UI`
- workspace root is not a git repo, so no root-level GitHub Actions workflow should be created
