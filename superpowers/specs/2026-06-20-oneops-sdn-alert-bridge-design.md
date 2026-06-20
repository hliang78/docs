# OneOPS SDN Alert Bridge Design

## Context

OneOPS now persists SDN alarms in `platform_sdn_alarm` as the SDN evidence
layer. The existing alert center uses `alert_alarm` as the unified operational
entry point, including confirmation, history, ticket integration, and RCA
workflows.

This design connects SDN alarms to the unified alert center without moving vendor
adaptation into OneOPS. CtrlHub remains responsible for collecting and
normalizing ACI, Huawei, and later H3C alarms. OneOPS owns persistence,
projection, tenant scoping, and alert lifecycle integration.

## Decision

Use Scheme A: a synchronous OneOPS bridge.

After SDN alarm refresh upserts rows into `platform_sdn_alarm`, OneOPS projects
those rows into `alert_alarm` in the same user operation. The SDN table remains
the source-of-truth/evidence layer. `alert_alarm` becomes the unified
operations-management entry.

The first version writes unified alert records but does not automatically create
tickets unless an explicit bridge option enables it. This prevents a large APIC
fault burst from creating hundreds of tickets during the first integration.

## Goals

- Project SDN open and acknowledged alarms into unified `alert_alarm`.
- Mark projected unified alerts inactive/resolved when SDN alarms clear.
- Keep projection idempotent across repeated SDN refreshes.
- Preserve links from SDN alarm rows to unified alert records.
- Keep CtrlHub vendor-only and free of OneOPS alert-center writes.
- Keep SDN alarm history useful even when unified alert projection fails.
- Make ticket creation opt-in, not default.

## Non-Goals

- No vendor-specific SDN clients in OneOPS.
- No direct CtrlHub writes to `alert_alarm`.
- No monitoring dashboard.
- No real SDN configuration apply or rollback execution.
- No broad redesign of the existing alert engine or ticket model.

## Data Model

Extend `platform_sdn_alarm` with bridge metadata:

- `alert_alarm_code`: unified alert code when projection succeeds.
- `alert_synced_at`: last bridge attempt time that reached a terminal result.
- `alert_sync_status`: `pending`, `synced`, `failed`, or `skipped`.
- `alert_sync_error`: redacted short error string for troubleshooting.

The bridge uses the existing `alert_alarm` table as-is.

Unified alert identity:

- `DatasourceType`: `sdn`
- `DatasourceCode`: `sdn`
- `RuleCode`: `sdn-controller`
- `MD5`: SHA or MD5 of `sdn:<controller_id>:<alarm_key>`
- `Flag`: resource name, DN, provider alarm ID, or alarm key.

Labels JSON should include:

- `source`: `sdn`
- `controller_id`
- `provider`
- `alarm_key`
- `provider_alarm_id`
- `resource_type`
- `resource_name`
- `resource_dn`
- `tenant`

Annotations JSON should include:

- `summary`
- `description`
- `sdn_alarm_id`
- `sdn_alarm_code`
- `severity`

## Lifecycle Mapping

SDN to unified alert state:

- `open` -> `firing`
- `acknowledged` -> `firing`
- `cleared` -> `inactive` with `resolved_at`

For a new open or acknowledged SDN alarm:

1. Build the stable bridge MD5 from `controller_id` and `alarm_key`.
2. Find an unresolved `alert_alarm` by MD5.
3. If missing, create a new `alert_alarm`.
4. Update `platform_sdn_alarm.alert_alarm_code`, `alert_synced_at`, and
   `alert_sync_status=synced`.

For an existing open or acknowledged SDN alarm:

1. Update the unresolved `alert_alarm` by MD5.
2. Refresh severity-derived value, summary, description, labels, annotations,
   and timing fields.
3. Preserve existing confirmation fields on the unified alert.

For a cleared SDN alarm:

1. Find an unresolved `alert_alarm` by MD5.
2. If found, set `state=inactive`, `resolved_at`, labels, annotations, and
   latest description.
3. If not found, mark `platform_sdn_alarm.alert_sync_status=skipped`.

## Ticket Behavior

Default behavior: do not automatically create alert tickets from SDN bridge
projection.

The bridge should support an internal option such as
`CreateTicketOnNewAlert bool`. In this first version it remains false from the
SDN refresh path. A later operations policy can enable it after noise controls
and severity filters are agreed.

## Error Handling

Bridge projection should be best-effort per alarm:

- SDN refresh should still succeed if a subset of alert projections fails.
- Each failed row stores `alert_sync_status=failed` and a redacted
  `alert_sync_error`.
- The refresh response can include existing alarm rows without failing the whole
  request.
- Sensitive values in labels, annotations, and errors must be redacted.

## API Behavior

Existing SDN alarm APIs remain:

- `POST /sdn/controllers/:id/alarms/refresh`
- `GET /sdn/controllers/:id/alarms`
- `GET /sdn/controllers/:id/alarms/:alarm_id`

Enhance returned SDN alarm records with:

- `alert_alarm_code`
- `alert_sync_status`
- `alert_synced_at`

The UI can use `alert_alarm_code` to link to the unified alert center.

## UI Behavior

The SDN controller page should:

- Show unified alert status/reference in the alarm history drawer.
- Render a link to the alert center when `alert_alarm_code` exists.
- Keep SDN alarm details visible even if bridge projection failed.
- Show a compact failed/skipped sync marker without turning the SDN page into a
  dashboard.

The unified alert list can already filter by `DatasourceType`. If needed, a
later UI pass can add a quick filter for `datasource_type=sdn`.

## Testing

Backend tests:

- Open SDN alarm creates one unified `alert_alarm`.
- Re-refreshing the same SDN alarm updates the same unified alert, not a new
  one.
- Cleared SDN alarm marks the unified alert inactive/resolved.
- Bridge failure records `alert_sync_status=failed` on the SDN row and does not
  fail the whole refresh.
- Ticket creation is disabled by default.
- Tenant scoping is preserved.

UI smoke tests:

- SDN alarm history renders `alert_alarm_code`.
- SDN alarm row shows a unified alert jump target when available.
- Failed/skipped bridge status renders without breaking the drawer.

## Acceptance

- ACI SDN alarm refresh creates unified alerts for open/acknowledged alarms.
- Repeated refreshes are idempotent.
- Cleared SDN alarms resolve their unified alert records.
- SDN page can jump to the unified alert record.
- Ticket creation does not happen by default.
- CtrlHub remains unchanged for this bridge.
- Focused OneOPS and OneOPS-UI SDN tests pass.
