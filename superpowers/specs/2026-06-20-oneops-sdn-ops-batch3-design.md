# OneOPS SDN Ops Batch 3 Design

## Context

Batch 1 made SDN controller snapshots operational: resources, history, and diffs.
Batch 2 added diagnostics, current alarms, and guarded configuration plans with
dry-run. Batch 3 turns those one-shot operations into auditable operations data.

The user explicitly excluded a monitoring dashboard for this batch. Controller
health is therefore limited to diagnostic history and latest status fields. No
trend page, overview dashboard, alert chart, or independent health console is in
scope.

## Goals

- Persist SDN alarms collected through CtrlHub.
- Support current alarm refresh, alarm history query, and stable alarm state
  updates.
- Keep OneOPS vendor-neutral. ACI, Huawei, and later H3C adaptation remains in
  CtrlHub.
- Add configuration plan approval and rollback-plan records.
- Keep real SDN configuration execution disabled unless a later explicit safety
  gate enables it.
- Preserve tenant isolation, credential redaction, and auditability.

## Non-Goals

- No monitoring dashboard or health trend page.
- No real configuration apply to APIC/Huawei/H3C.
- No real rollback execution.
- No vendor-specific controller clients inside OneOPS.
- No broad refactor of device, IPAM, NetPath, or topology work.

## Architecture

OneOPS remains the system of record for operations state. CtrlHub remains the
vendor adapter. The data flow is:

1. Operator triggers alarm refresh or scheduled job triggers it later.
2. OneOPS resolves the SDN controller and credential reference.
3. OneOPS calls CtrlHub `/api/v1/sdn/alarms`.
4. CtrlHub returns normalized alarms.
5. OneOPS upserts alarms into a tenant-scoped history table.
6. UI reads current and historical alarms from OneOPS.

Configuration planning stays as:

1. Operator creates draft intent in OneOPS.
2. Dry-run validates and stores preview result.
3. An approval endpoint marks the plan approved with approver metadata.
4. A rollback plan is stored as structured JSON before any future execution.
5. Execute remains disabled and returns the existing conflict response until a
   later batch designs real apply.

## Alarm Persistence

Add `platform_sdn_alarm` as a tenant-scoped table.

Recommended fields:

- `id`
- `tenant_code`
- `controller_id`
- `provider`
- `alarm_key`: stable dedupe key. Prefer provider alarm ID, then DN/code/resource.
- `provider_alarm_id`
- `severity`
- `status`
- `resource_type`
- `resource_name`
- `resource_dn`
- `code`
- `title`
- `message`
- `tags_json`
- `attributes_json`
- `raw_json`: optional, sanitized and only when safe.
- `first_seen_at`
- `last_seen_at`
- `cleared_at`
- `acknowledged_at`
- `created_at`
- `updated_at`

Upsert behavior:

- New alarm key creates a row with `first_seen_at` and `last_seen_at`.
- Existing alarm key updates severity, status, message, resource fields,
  attributes, and `last_seen_at`.
- If current refresh no longer returns an alarm that was previously open for the
  same controller, mark it `cleared` and set `cleared_at`.
- Preserve historical rows instead of deleting them.
- Do not persist credentials or request payloads.

## Alarm APIs

Add OneOPS APIs:

- `POST /api/v1/sdn/controllers/:id/alarms/refresh`
  - Calls CtrlHub and persists/upserts alarms.
  - Returns current alarm summary and rows.

- `GET /api/v1/sdn/controllers/:id/alarms`
  - Reads persisted alarms.
  - Query: `severity`, `status`, `resource_type`, `keyword`, `page`,
    `page_size`.
  - Defaults to current open/acknowledged alarms unless `status=all`.

- `GET /api/v1/sdn/controllers/:id/alarms/:alarm_id`
  - Reads one persisted alarm detail under tenant scope.

The existing `POST /api/v1/sdn/controllers/:id/alarms` current-fetch API may
remain as compatibility. The UI should prefer persisted list plus explicit
refresh.

## Diagnostic History

Because the dashboard is out of scope, diagnostics only need a small persistence
layer:

- Store latest diagnostic result per controller.
- Optionally store recent diagnostic history rows with overall status, checked
  time, duration, and stage summaries.
- UI can show latest diagnostic result inside the existing drawer.

This is not a dashboard; it is operational evidence tied to a controller.

## Config Plan Approval And Rollback Records

Extend `platform_sdn_config_plan`.

Recommended fields:

- `approved_by`
- `approved_at`
- `approval_comment`
- `rollback_plan_json`
- `rollback_summary`

Status rules:

- `draft`: created but not dry-run ready.
- `dry_run_ready`: dry-run passed and can be approved.
- `dry_run_failed`: dry-run failed and cannot be approved.
- `approved`: approved, but real execution remains disabled.
- `executed` and `failed`: reserved for future real apply.

Add APIs:

- `POST /api/v1/sdn/config-plans/:id/approve`
  - Requires tenant-scoped plan.
  - Requires status `dry_run_ready`.
  - Stores approver/account from context and optional comment.
  - Stores rollback plan if provided by dry-run result or generated scaffold.

- `POST /api/v1/sdn/config-plans/:id/rollback/dry-run`
  - Returns stored rollback plan and a dry-run-style response.
  - Does not perform live rollback.

Real execution remains:

- `POST /api/v1/sdn/config-plans/:id/execute`
  - Still returns HTTP 409 disabled.

## UI Behavior

Use the existing SDN controller management page under device management.

Alarm drawer:

- Show persisted alarm list.
- Add explicit refresh button that calls `alarms/refresh`.
- Add filters: severity, status, keyword.
- Show current row count and last refresh time.
- Alarm detail can remain inline/drawer-light for this batch.

Config plan drawer:

- Add approve action after dry-run ready.
- Show approval metadata.
- Show rollback plan summary after dry-run.
- Add rollback dry-run action that only previews stored rollback content.
- Keep execute visually disabled unless the backend explicitly enables it later.

No dashboard layout or separate monitoring page should be added.

## Testing

OneOPS backend:

- Alarm refresh upserts new alarms.
- Alarm refresh marks missing open alarms cleared.
- Alarm list filters by severity/status/keyword and respects tenant scope.
- Config plan approve rejects non-dry-run-ready plans.
- Config plan approve stores approver and comment.
- Rollback dry-run returns stored rollback plan without live apply.
- CtrlHub errors are redacted in persisted summaries.

OneOPS-UI:

- Smoke covers persisted alarm list, refresh call, filters, approve action, and
  rollback dry-run preview.
- Existing resource workbench smoke remains green.

CtrlHub:

- No new vendor behavior is required unless OneOPS needs an additional response
  field. Keep normalized alarm response stable.

## Acceptance

- ACI current alarms can be refreshed and then queried from OneOPS persistence.
- Cleared alarm state is visible after a refresh no longer returns the alarm.
- Operators can approve a dry-run-ready config plan.
- Operators can view a rollback plan preview.
- Real execute remains disabled.
- No monitoring dashboard is introduced.
- Verification passes for focused OneOPS, UI, and CtrlHub SDN tests.
