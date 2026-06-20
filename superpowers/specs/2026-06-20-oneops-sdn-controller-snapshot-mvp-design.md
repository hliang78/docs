# OneOPS SDN Controller Snapshot MVP Design

## Purpose

Build the first OneOPS-side SDN integration loop for ACI and Huawei through the controller snapshot API that already exists in `ctrlhub/controller`.

The first phase lets an operator configure SDN controllers in OneOPS, test connectivity, trigger a read-only snapshot sync, store the result, and inspect normalized SDN resources in the OneOPS UI. OneOPS must not implement ACI, Huawei, or H3C device/controller API adaptation. Vendor adaptation stays in `ctrlhub/controller`.

## Scope

This phase covers backend and simple UI:

- OneOPS backend SDN controller configuration.
- OneOPS backend calls to `ctrlhub/controller` `POST /api/v1/sdn/snapshot`.
- Snapshot sync status and latest snapshot persistence.
- UI for controller list, create/edit form, connection test, manual sync, and latest snapshot resource inspection.
- Basic summary counts for tenants, VRFs, networks, subnets, segments, endpoints, switches, ports, contracts, and filters.

This phase does not cover:

- SDN object create, update, delete, or repair.
- H3C support.
- OneOPS-side ACI/Huawei/H3C API clients.
- Automatic diff, approval, or deployment.
- Deep business-object binding between OneOPS networks/subnets and SDN resources.
- Making raw vendor payload a dependency of OneOPS business logic.

## Architecture

The integration path is:

```text
OneOPS-UI
  -> OneOPS backend SDN API
  -> ctrlhub/controller POST /api/v1/sdn/snapshot
  -> ACI or Huawei SDN controller
```

OneOPS backend owns configuration, credential lookup, audit-friendly request handling, snapshot persistence, and UI-facing projection. `ctrlhub/controller` owns provider-specific authentication, provider-specific collection, normalization, and provider API error handling.

The existing legacy `agent/pkg/l2service` SDN code can be used as historical context, but new OneOPS phase-one work must not add or revive vendor-specific adaptation there.

## Backend Components

### SDN Controller Store

Add a backend module dedicated to SDN controller configuration and snapshot records. The module should avoid mixing SDN controller configuration into generic controller objects because SDN snapshots need their own lifecycle, status, and resource summary.

Recommended package shape in the agent backend:

- `pkg/controller/sdn/model.go`
  - SDN controller config and snapshot model structs.
- `pkg/controller/sdn/service.go`
  - Validation, credential resolution boundary, call to ctrlhub, persistence, and summary building.
- `pkg/controller/sdn/client.go`
  - Minimal HTTP client for `ctrlhub/controller` SDN snapshot API.
- `pkg/controller/api/sdn.go`
  - HTTP handlers and response wrappers.
- `pkg/controller/api/sdn_test.go`
  - Handler tests using fake service or fake ctrlhub server.

If the repository already has a stronger local convention for API/service/model files during implementation, follow that convention while preserving these responsibilities.

### SDN Controller Config Model

The SDN controller config stored by OneOPS should include:

- `id`: stable UUID.
- `name`: operator-facing name.
- `provider`: `aci` or `huawei`.
- `enabled`: whether the config is active.
- `ctrlhub_base_url`: base URL of the controller service that exposes `/api/v1/sdn/snapshot`.
- `sdn_scheme`: `http` or `https`, default `https`.
- `sdn_host`: ACI APIC or Huawei SDN controller host.
- `sdn_port`: optional provider endpoint port.
- `credential_ref`: reference to an existing OneOPS credential/secret entry.
- `insecure_skip_verify`: whether TLS certificate verification is skipped for the provider endpoint.
- `timeout_seconds`: snapshot request timeout, default inherited from controller when omitted.
- `area`: optional area/region label.
- `site`: optional site label.
- `tenant`: optional tenant scope label.
- `description`: optional text.
- `last_sync_status`: `never_synced`, `success`, or `failed`.
- `last_sync_at`: timestamp of the latest sync attempt.
- `last_success_at`: timestamp of the latest successful sync.
- `last_error`: sanitized summary for the latest failed sync.
- `last_summary`: resource counts from the latest successful snapshot.
- `created_at`, `updated_at`.

Secrets are not stored in this model. The backend resolves `credential_ref` at call time and only sends username/password to `ctrlhub/controller` over the backend-to-backend request.

### Snapshot Record Model

Persist snapshot records separately from controller configs:

- `id`: stable UUID.
- `controller_id`.
- `provider`.
- `collected_at`: timestamp from ctrlhub response.
- `synced_at`: timestamp when OneOPS completed the sync.
- `duration_ms`: ctrlhub collection duration.
- `status`: `success` or `failed`.
- `error_summary`: sanitized error text for failures.
- `resource_summary`: counts per normalized collection.
- `snapshot`: normalized snapshot JSON for success records.
- `metadata`: source and provider version from ctrlhub snapshot response.

The first implementation can store the latest successful snapshot and recent history. If storage cost is a concern, keep full `snapshot` only for the latest record and keep summary-only history.

### Backend API

Expose OneOPS backend endpoints for the UI:

- `GET /api/v1/sdn/controllers`
  - List controller configs with status and latest summary.
- `POST /api/v1/sdn/controllers`
  - Create controller config.
- `GET /api/v1/sdn/controllers/{id}`
  - Read controller config without secrets.
- `PUT /api/v1/sdn/controllers/{id}`
  - Update controller config.
- `DELETE /api/v1/sdn/controllers/{id}`
  - Disable or delete controller config according to existing backend convention. Prefer soft disable if the codebase commonly preserves audit history.
- `POST /api/v1/sdn/controllers/{id}/test`
  - Resolve credential and call ctrlhub snapshot API with the stored config.
  - Do not persist full snapshot.
  - Return success, duration, provider, and resource counts.
- `POST /api/v1/sdn/controllers/{id}/sync`
  - Resolve credential, call ctrlhub snapshot API, persist result, update controller latest status.
- `GET /api/v1/sdn/controllers/{id}/snapshots/latest`
  - Return latest successful normalized snapshot and summary.
- `GET /api/v1/sdn/controllers/{id}/snapshots`
  - Return recent sync history with status and summary only.

Response wrappers should follow existing OneOPS backend style, with `success`, `message`, `data`, and `error` fields when that is consistent with nearby APIs.

### Ctrlhub Request Contract

OneOPS backend sends:

```json
{
  "provider": "aci",
  "endpoint": {
    "scheme": "https",
    "host": "apic.example.internal",
    "port": 443,
    "username": "resolved-user",
    "password": "resolved-password",
    "use_https": true,
    "insecure_skip_verify": false,
    "timeout_seconds": 30
  },
  "include_raw": false,
  "metadata": {
    "source": "oneops",
    "provider_version": ""
  }
}
```

OneOPS backend must not expose `endpoint.password` in logs, persistence, or UI responses. When logging requests, log controller config ID, provider, and sanitized host only.

## UI Design

Create a simple operational page rather than a landing page. The first screen should be the SDN controller work surface.

Recommended files:

- `src/typings/platform/sdn-controller.ts`
  - Types for controller config, summary, snapshot, resources, and API responses.
- `src/api/platform/sdn-controller.ts`
  - API calls for list/create/update/delete/test/sync/latest/history.
- `src/views/platform/SdnControllerManagement.vue`
  - Main page.
- Add a route/menu entry using the existing dynamic menu pattern or a local route injection if that is the established pattern for unfinished menu-backed features.

### Page Structure

Use the existing Ant Design Vue / OneOPS style:

- Top toolbar:
  - Provider filter.
  - Status filter.
  - Area/site filter if the existing UI has a standard selector.
  - Search input for name/host.
  - Create button.
- Controller table:
  - Name.
  - Provider badge.
  - SDN endpoint host.
  - Area/site.
  - Enabled state.
  - Last sync status.
  - Last sync time.
  - Summary count.
  - Actions: Test, Sync, View Snapshot, Edit.
- Right drawer or detail panel:
  - Controller metadata.
  - Latest sync summary.
  - Resource tabs.

Resource tabs:

- Tenants
- VRFs
- Networks
- Subnets
- Segments
- Endpoints
- Switches
- Ports
- Contracts
- Filters

Each resource table should show normalized fields first:

- `name`
- `id`
- `tenant`
- `provider_type`
- `dn`

Raw payload is hidden by default. If included later, it should be a debug-only expandable panel and gated by permission.

### UI States

The UI should handle:

- Empty controller list.
- Controller exists but never synced.
- Test/sync running.
- Test/sync failure with sanitized message.
- Latest snapshot unavailable.
- Latest snapshot exists but a resource group is empty.

The first phase does not need background polling. Test and sync can be synchronous request/response operations with loading indicators.

## Security And Permissions

Security rules:

- Never store provider password in the SDN controller config.
- Never return provider password to UI.
- Never log provider password.
- Do not persist raw provider response unless `include_raw` is explicitly supported and access-controlled.
- Keep `include_raw` false by default for test and sync.
- Sanitize ctrlhub and provider errors before saving `last_error`.

Recommended permission split:

- View SDN controllers.
- Manage SDN controllers.
- Run SDN connection test.
- Run SDN sync.
- View raw snapshot payload.

If the existing permission system makes new fine-grained permissions expensive, first implement feature-level guarding and leave raw payload hidden.

## Error Handling

Validation errors:

- Missing `name`, `provider`, `ctrlhub_base_url`, `sdn_host`, or `credential_ref` returns 400.
- Unsupported provider returns 400.
- Invalid URL or invalid scheme returns 400.

Runtime errors:

- Credential not found returns a sanitized 400 or 404 according to existing backend convention.
- Ctrlhub timeout returns 504 if the backend convention supports it; otherwise return a structured failure with `error_type=timeout`.
- Ctrlhub 401/403 from provider authentication is returned as sanitized authentication failure.
- Other ctrlhub/provider failures are stored as sanitized sync failure.

The controller config should update `last_sync_status=failed`, `last_sync_at`, and `last_error` for failed sync attempts. Connection test failures do not need to update sync status unless product owners want a separate `last_test_status`.

## Testing Strategy

Backend tests:

- Config validation rejects missing required fields.
- Create/list/get/update handlers do not expose secrets.
- Test endpoint calls fake ctrlhub server and returns counts without persisting full snapshot.
- Sync endpoint calls fake ctrlhub server, persists latest snapshot, updates summary and status.
- Sync failure stores sanitized `last_error` and does not leak provider password.
- Unsupported provider is rejected before ctrlhub call.

UI tests or smoke checks:

- API client builds correct request paths.
- Controller table renders empty, success, and failure states.
- Snapshot drawer renders resource tabs and normalized fields.
- Password fields are write-only in forms and not displayed after save.

Manual verification:

- Configure an ACI controller using a secret-backed credential.
- Run Test Connection successfully.
- Run Sync successfully.
- Open latest snapshot and confirm tenants/networks/endpoints render.
- Confirm browser responses and backend logs do not include provider password.

## Acceptance Criteria

The phase is complete when:

- OneOPS UI can create an ACI or Huawei SDN controller config without storing the password in the config.
- OneOPS UI can test connectivity through the OneOPS backend.
- OneOPS UI can trigger a manual snapshot sync through the OneOPS backend.
- OneOPS backend stores latest successful normalized snapshot and recent sync status.
- OneOPS UI can inspect normalized resource groups from the latest snapshot.
- OneOPS code does not contain ACI/Huawei provider API calls beyond calling `ctrlhub/controller` unified snapshot API.
- Passwords are not returned in API responses, logs, or persisted config.

## Future Phases

Future work should build on the stored normalized snapshot:

- OneOPS business object association.
- Snapshot-to-OneOPS matching suggestions.
- Diff view between OneOPS expected state and SDN actual state.
- Precheck and dry-run for proposed SDN changes.
- Approval workflow.
- Write operations through `ctrlhub/controller`, still keeping provider adaptation outside OneOPS.
