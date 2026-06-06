# Ansible Task Assetization E2E Acceptance Design

## Goal

Drive the Ansible task assetization MVP as one end-to-end product lane, not as separate backend and frontend tasks. The network configuration backup asset is accepted only when an operator can start from the task asset, precheck target devices, execute ready devices, inspect parent-task device results, and see the resulting backup history on the device.

## Scope

The MVP lane covers one task asset:

```text
network-config-backup
```

The accepted user path is:

```text
Task asset detail
  -> select devices and access plane
  -> run Ansible target precheck
  -> submit ready devices
  -> inspect parent task device results
  -> download or reject sensitive artifacts through governed endpoints
  -> inspect device config backup history
```

This lane does not create a generic Ansible orchestrator, a full approval workflow, configuration diff, drift alerting, or config deployment. Those features belong after this backup asset proves the contract, artifact, projection, and UI pattern.

## Product Principles

The frontend must present the feature as a governed operational asset, not as a raw Ansible execution form.

- The center of the experience is device-level readiness and outcome, not logs.
- Blocked devices remain visible with clear reasons, so operators can repair device data or credential bindings.
- Sensitive config files are never previewed by default.
- Credential references may be shown as references, but resolved usernames, passwords, tokens, private keys, and auth material are never returned or displayed.
- A successful run must leave an inspectable device asset record, not just a completed task row.

## Delivery Surfaces

### Task Asset / Template Surface

Enhance the current task template or task asset surface to show contract metadata for the network backup asset.

Required information:

- asset name and template ID
- `app_type=ansible`
- lifecycle status
- risk level
- asset category
- playbook path
- repository and branch
- supported device types
- supported vendor families
- supported access planes
- credential contract
- output contract
- sensitive artifact note
- actions: start backup, create schedule, view raw contract

This can be implemented as a task template detail drawer or a task asset detail page. The first implementation should prefer a detail drawer if that matches the current OneOps UI pattern.

### Asset Execution Surface

Add an asset-specific start flow for network config backup. This flow can be a modal, drawer, or dedicated route, but it must be precheck-driven.

Required steps:

1. Select the network backup asset.
2. Select explicit `device_codes`.
3. Select `access_plane`.
4. Optionally select a fallback `credential_ref`.
5. Run precheck.
6. Review ready, warning, and blocked devices.
7. Submit only ready devices.

The submit action is disabled until precheck has completed for the selected device set. If the selection changes after precheck, the page must mark the precheck result stale and require a new precheck.

### Task Detail Device Results Surface

Enhance the existing task detail drawer in `OneOps-UI/src/views/platform/TaskManagement.vue` with a device-result tab for parent backup tasks.

Required summary metrics:

- total devices
- ready count
- blocked count
- success count
- failed count
- archived artifact count
- failure reason distribution

Required device row fields:

- device code
- precheck status when available
- runtime status
- child task ID
- access plane
- target address when safe to show
- vendor family
- Ansible connection profile
- credential source
- artifact entry
- error message

The row action should let operators open the child task, download governed artifacts, and jump to the device backup history.

### Device Detail Config Backup Surface

Enhance the device detail drawer or device detail route with a config backup tab or block.

Required summary:

- latest backup status
- latest backup time
- latest task ID
- latest parent task ID
- latest config hash

Required history table fields:

- backup time
- backup status
- task ID
- parent task ID
- vendor family
- access plane
- artifact name
- artifact size
- artifact SHA256
- config hash
- error message

The history table must not show `.cfg` contents inline. Download actions use governed artifact endpoints and must surface permission failures clearly.

## API And UI Matrix

| User need | API | Frontend owner | Acceptance |
| --- | --- | --- | --- |
| Inspect task asset contract | `GET /api/v1/platform/task-templates/:id` | task template or task asset detail | Contract metadata is visible and raw JSON is available on demand. |
| Precheck selected devices | `POST /api/v1/platform/task-assets/:template_id/ansible/precheck` | asset execution flow | Ready, warning, and blocked counts match response; blocked reasons are visible. |
| Submit ready devices | existing task creation API with `template_id`, `device_codes`, `access_plane`, `credential_ref` | asset execution flow | Submitted payload contains only ready devices unless the operator explicitly rechecks a changed selection. |
| Inspect parent device results | `GET /api/v1/platform/tasks/:taskID/device-results` | task detail device-result tab | Parent task shows per-device rows, counts, child task IDs, artifacts, and errors. |
| Inspect device backup history | `GET /api/v1/platform/devices/:code/config-backups` or `GET /api/v1/device/v2/:code/config-backups` | device detail config backup tab | Device shows latest backup summary and descending history. |
| Download artifact | existing runtime artifact download endpoint | task result and device backup history | Sensitive artifacts require governed download and never render inline by default. |

## Backend Acceptance Matrix

| Area | Acceptance criteria | Evidence |
| --- | --- | --- |
| Contract metadata | `contract_json`, `asset_category`, `risk_level`, and `lifecycle_status` persist and round trip through template APIs. | Focused Go tests and template import smoke. |
| Precheck | Ready devices include target address, vendor family, Ansible connection profile, credential source; blocked devices include stable reasons. | Service tests and API tests for ready, missing device, missing address, missing credential, unsupported vendor. |
| Secret handling | No inline credential material appears in inventory, logs, precheck responses, device results, or config backup history. | Unit tests plus grep-style response inspection in E2E smoke. |
| Fanout execution | Parent task creates device child tasks using the existing device fanout path. | Task creation/fanout tests and one real or simulated task run. |
| Artifact projection | Runtime output projects `.cfg` and summary JSON into `platform_device_config_backup`. | Projection tests with sensitive `.cfg` artifact and summary JSON. |
| Parent aggregation | `device-results` returns counts, failure reason distribution, child task IDs, artifacts, and per-device errors. | API test seeded with parent, child tasks, and backup rows. |
| Device history | `config-backups` returns only the requested device records in descending backup time order. | API test for paging, sorting, and device isolation. |

## Frontend Acceptance Matrix

| Surface | Acceptance criteria | Evidence |
| --- | --- | --- |
| Asset detail | Contract summary, risk, supported targets, credential contract, and output contract are readable without opening raw JSON. | Component or smoke test plus screenshot review. |
| Start flow | Submit is blocked until precheck completes; changed selections invalidate prior precheck; ready and blocked rows are separated. | Component or Playwright smoke. |
| Precheck result | Blocked reasons are visible and actionable; credential references never expose resolved material. | Component assertions and manual response inspection. |
| Task detail device results | Parent task displays aggregate metrics and per-device rows; child task navigation and artifact entry are available. | Playwright smoke against fixture or dev API. |
| Device backup tab | Latest backup summary and history table render from API; empty, loading, error, and permission-denied states are present. | Component or Playwright smoke. |
| Responsive behavior | Tables remain usable in the current Ant Design Vue layout at desktop and narrow widths. | Browser screenshot checks for task detail and device detail drawers. |

## Security Acceptance Matrix

| Risk | Required behavior | Rejection condition |
| --- | --- | --- |
| Credential leakage | Responses and UI only show credential references or source labels. | Any username, password, token, private key, auth pass, or resolved secret appears in UI or logs. |
| Sensitive config exposure | `.cfg` artifacts are marked sensitive and are download-only by default. | `.cfg` contents are previewed inline or exposed through a non-governed URL. |
| Permission failure | Download permission failure shows a clear operator message. | The UI silently fails or suggests the file does not exist when the user lacks permission. |
| Inventory leakage | Generated inventory excludes forbidden credential host vars. | Inventory includes `ansible_password`, `ansible_ssh_pass`, `ansible_become_password`, token, or private key data. |
| Auditability | Task ID, child task ID, parent task ID, device code, and artifact metadata remain traceable. | A backup record cannot be traced back to its task and device. |

## Implementation Phases

### Phase 1: Backend Contract And API Readiness

Confirm or complete the backend implementation for contract metadata, precheck, device results, config backup history, and sensitive artifact projection. This phase is accepted only after focused Go API/service tests pass.

### Phase 2: Frontend API And Types

Add TypeScript types and request functions for precheck, device results, and config backup history. This phase is accepted only after typecheck passes and the API helpers match the documented response shapes.

### Phase 3: Task Detail Device Results

Add the device-result tab to the existing task detail drawer. This is the highest-value frontend step because it turns a parent task into a device outcome view.

### Phase 4: Device Config Backup History

Add the config backup tab or block to the device detail surface. This proves that a backup run becomes a device asset record.

### Phase 5: Asset Detail And Precheck-Driven Start Flow

Add contract-aware task asset detail and the precheck-driven start flow. This phase improves operator entry and prevents invalid submissions.

### Phase 6: End-To-End Acceptance

Run one accepted scenario with at least two selected devices:

- one ready device
- one blocked or failed device
- one successful backup artifact projection
- visible parent device results
- visible device backup history
- no secret leakage in inspected responses, inventory, logs, or UI

## Review Gates

Each phase must pass a review gate before the next phase starts:

1. Design gate: requirements, API fields, and UI states are explicit.
2. Test gate: focused backend or frontend tests are run fresh.
3. Security gate: secret and sensitive artifact handling is inspected.
4. UX gate: the page answers the operator's next action without relying on logs.
5. Code review gate: critical and important findings are fixed before proceeding.

## Open Decisions

The following decisions are intentionally constrained for MVP:

- The canonical device backup history route can be either platform device route or device v2 route, but the frontend should prefer the device v2 route when operating inside device v2 detail.
- The first asset execution surface can be a drawer or modal. A dedicated route is not required unless the existing modal becomes too dense.
- Blocked devices are not submitted in MVP. A later version can add an explicit override policy if governance requires it.

