# Device Config Management First-Class Acceptance

Date: 2026-06-07

## Scope

- [x] Backend config version models and DTOs were added.
- [x] Successful device config backup projection now derives immutable config versions when the config version table is available.
- [x] Version change status is derived from previous successful backup hash: `first_backup`, `no_change`, `changed`, or `compare_failed`.
- [x] Config change events are created for changed versions.
- [x] Redacted historical diff service was added.
- [x] Device V2 config version list and diff APIs were exposed.
- [x] Frontend Device V2 API helpers were added.
- [x] Device V2 management page now has a development-stage top `配置管理` entry button.
- [x] Device detail now shows config versions and supports previous-version or selected-version diff.
- [x] Independent `配置管理` page shell was added as a hidden route for development access.

## Branch And Commit Evidence

- Backend repo `/OneOPS/OneOps`: branch `feature/device-v2-platform-core-optimization`, HEAD `b5fc909f`.
- Backend commits under acceptance:
  - `fc0669a6 feat: add config management models`
  - `dffe9b58 feat: derive config versions from backups`
  - `0214e192 feat: project config backups into versions`
  - `76f015ae feat: add redacted config diff service`
  - `b5fc909f feat: expose config version APIs`
- Frontend repo `/OneOPS/OneOps-UI`: branch `main`, HEAD `ed87805`.
- Frontend commits under acceptance:
  - `180af4b feat: add config version frontend api`
  - `ed87805 feat: add config management entry page`
- Docs repo `/OneOPS/docs`: branch `main`, checklist added after docs baseline `3a8a13e`.

## Backend Verification Evidence

- `go test ./app/device/v2/api ./app/platform/service/impl ./app/platform/service -run 'TestDeviceV2API(ListConfigVersions|DiffConfigVersions|ListConfigBackups)|Test(ConfigVersionService|ConfigDiffService|ProjectDeviceConfigBackupFromRuntimeOutput)' -count=1` -> exit 0.
  - `ok github.com/netxops/OneOps/app/device/v2/api 0.039s`
  - `ok github.com/netxops/OneOps/app/platform/service/impl 0.083s`
  - `ok github.com/netxops/OneOps/app/platform/service 0.010s [no tests to run]`
- `go test ./cmd -run '^$'` -> exit 0, `ok github.com/netxops/OneOps/cmd (cached) [no tests to run]`.

## Frontend Verification Evidence

- `npm run typecheck` -> exit 0.
- `npm run build:force` -> exit 0.
- Build output included `12203 modules transformed` and `built in 3m 39s`.
- Build warning retained: `Some chunks are larger than 500 kB after minification`. This is an existing bundle-size warning and was not addressed in this acceptance scope.

## Secret / Sensitive Information Check

- Backend diff range checked: `origin/feature/device-v2-platform-core-optimization..HEAD`.
- Backend secret-like grep matched only redaction implementation and test fixtures:
  - redaction regex for `password`, `token`, `community`, `private_key`, and related keys.
  - test fixture strings `oldsecret` and `newsecret`.
  - test assertion that diff output must not leak those values.
- Frontend diff range checked: `origin/main..HEAD`.
- Frontend secret-like grep returned no matches.
- Acceptance result: no real credential, token, or private key literal was found in the accepted frontend/backend changes.

## User-Facing Flow Acceptance

- Device V2 management page has a top `配置管理` button for development-stage entry.
- `配置管理` route is registered as hidden/non-menu, so it does not decide final menu placement yet.
- Device detail config version section shows latest version metadata and version history.
- Operators can compare a version with its previous version.
- Operators can choose two historical versions as base and target, then open a redacted diff drawer.
- Diff drawer shows change summary, redaction warning, and unified diff text.

## Deferred Scope

- Final sidebar/menu route placement.
- Global cross-device config change aggregation API.
- Baseline selection and baseline drift policy.
- Review workflow for expected/unexpected changes.
- Alerting and ticket integration.
- Full authenticated browser E2E against a live backend.
- Full backend and full frontend test suites.
