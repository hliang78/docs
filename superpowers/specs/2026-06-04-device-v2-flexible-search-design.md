# Device V2 Flexible Search Design

Date: 2026-06-04

## Context

`/#/device/device-v2-management` currently renders `OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue`. The list query panel is still shaped like the legacy device list: a fixed set of inputs for name, IP, tenant, serial number, code, category, platform, model, site, and rack, plus a monitor dispatch quick filter.

The API layer already exposes these fixed query parameters through `listDeviceV2Req`, and the backend list endpoint supports them plus one label filter and one attribute filter:

- `label_key` / `label_value`
- `attribute_key` / `attribute_value`

This is not enough for flexible multi-condition search across all Device V2 fields.

## Goal

Refactor the Device V2 management list query experience so users can build multi-condition AND searches across Device V2 fields.

The query UI should prefer dropdown controls when the field has reliable options, but it should keep text input for fields where dropdowns would be incomplete, misleading, or operationally clumsy.

## Non-Goals

- No saved query templates in this iteration.
- No nested OR groups in this iteration.
- No arbitrary JSONPath editor.
- No full-text search engine migration.
- No broad redesign of the surrounding grouping tree, table, drawers, or batch actions.

## Recommended Approach

Add a structured filter model for the Device V2 list endpoint and replace the fixed query form with a condition builder.

Existing query parameters remain supported for compatibility. The new UI will use the structured filter model.

## Frontend Design

### Query Panel

Replace the hard-coded legacy query grid with a multi-row condition builder:

- Field selector
- Operator selector
- Value control
- Remove row button
- Add condition button
- Query button
- Reset button

Each condition row maps to one structured filter clause.

The panel keeps the existing monitor quick filter buttons, but internally they can become a structured clause or continue using `monitor_status` if that remains simpler.

### Field Sources

The field selector groups fields by source:

- Basic fields: root-level fields and operational projections such as `code`, `name`, `status`, `manage_status`, `monitor_push_status`.
- Standard attributes: fields from `schema/current.attributes_schema` plus established Device V2 field-model keys.
- Labels: fields from `schema/current.labels_schema`.
- Metadata: known metadata keys from existing field models, plus schema-visible metadata if added later.

Each field option has:

- `source`: `root`, `attributes`, `labels`, or `metadata`
- `key`
- `label`
- `type`
- optional `options`
- optional `preferredControl`

### Dropdown Rules

Use dropdowns where options are reliable:

- Schema `type=enum` or `options` exists: use select.
- Boolean fields: use select with true/false.
- Status-like fields: use select.
- Tenant, region, site, rack: use the existing location option sources when available.
- Platform and catalog: use existing platform/catalog option sources when available.
- Credential reference fields: use existing vault credential option sources when available.
- Monitor dispatch status: use select.

Use text input where dropdowns would hurt usability:

- IP address fields.
- Serial number.
- Hostname.
- Device code unless filtering by exact code list.
- Model, firmware, patch, version, asset number.
- Free-form metadata fields without schema options.

If a select field has no loaded options, fall back to text input instead of showing an empty dropdown.

### Operators

Supported operators:

- `eq`: equals
- `contains`: contains
- `in`: one of
- `exists`: field exists
- `prefix`: starts with

Operator availability depends on field type:

- Enum/select/boolean/status: `eq`, `in`, `exists`
- Text/IP/SN/hostname: `contains`, `eq`, `exists`
- Path-like fields: `prefix`, `eq`, `exists`
- Labels: `eq`, `contains`, `exists`

### Active Filters

The active filter strip renders all structured clauses with human-friendly labels, for example:

- `平台 = linux`
- `机房 包含 上海`
- `标签 env = prod`
- `属性 sn 包含 ABC`

### Route Handoff

Existing route handoff via `codes` and `task_id` remains unchanged. Handoff code filtering is still applied as a scope constraint, separate from user-entered search clauses.

## Backend Design

### API Contract

Extend the Device V2 list query request with a structured filter payload.

Preferred initial transport:

`GET /device/v2/list?filters=<url-encoded-json>`

The payload:

```json
[
  {
    "source": "attributes",
    "key": "platform_code",
    "operator": "eq",
    "value": "linux"
  },
  {
    "source": "labels",
    "key": "env",
    "operator": "eq",
    "value": "prod"
  }
]
```

This keeps the endpoint stable and avoids introducing a second list path. If URL length becomes a real problem later, add a POST search endpoint using the same payload shape.

### Filter Semantics

All structured clauses are combined with AND.

Supported sources:

- `root`: safe direct columns/projection fields.
- `attributes`: first-level JSON key under `attributes`.
- `labels`: first-level JSON key under `labels`.
- `metadata`: first-level JSON key under `metadata`.

Supported operators:

- `exists`: JSON extract is not null or root field is not empty.
- `eq`: exact string match after JSON extraction.
- `contains`: SQL LIKE `%value%`.
- `prefix`: SQL LIKE `value%`.
- `in`: exact match against a finite list.

### Safety

Structured clauses must be validated before building SQL:

- `source` must be one of the allowed sources.
- `operator` must be one of the allowed operators.
- `key` must be a safe field key.
- JSON keys initially support first-level keys matching `^[a-zA-Z0-9_]+$`.
- Root keys must be mapped through an explicit allowlist, not interpolated directly.
- `in` lists should have a reasonable length limit.
- Empty clauses are ignored by the frontend before submission.
- Submitted structured clauses that are incomplete or invalid are rejected by the backend with a request validation error.

### Compatibility

Existing parameters remain supported:

- `keyword`
- `code`
- `name`
- `ip`
- `tenant`
- `sn`
- `category`
- `platform`
- `model`
- `site`
- `rack`
- `monitor_status`
- `label_key` / `label_value`
- `attribute_key` / `attribute_value`
- management and location filters

When both legacy parameters and structured filters are present, backend applies both with AND semantics.

## Data Flow

1. Page loads current Device V2 schema and existing option sources.
2. Page builds a field catalog from schema, field-model descriptors, and known operational fields.
3. User adds one or more filter clauses.
4. UI picks each value control from the field descriptor and available options.
5. On query, frontend serializes non-empty clauses to `filters`.
6. Backend validates the clauses.
7. Backend applies legacy filters and structured filters to the list query.
8. Page renders results and active filter tags.

## Error Handling

Frontend:

- Do not submit incomplete clauses except `exists`.
- Show field-level validation for missing value.
- If a schema/options request fails, keep the query builder usable with text inputs.

Backend:

- Return standardized Device V2 request validation errors for invalid filter JSON, unsafe keys, unsupported source/operator, or invalid value shape.
- Log invalid filter details at warning level without logging sensitive values from credential-like fields.

## Testing

Frontend tests or smoke checks should cover:

- Add/remove multiple query clauses.
- Enum/status field renders select.
- Tenant/site/rack field uses select when options exist.
- IP/SN/hostname fields render text input.
- Active filter strip renders structured clauses.
- Reset clears all structured clauses and monitor quick filter.
- Route handoff `codes` continues to scope results.

Backend tests should cover:

- `filters` JSON binding and validation.
- Root field `eq` and `contains`.
- Attribute `eq`, `contains`, `exists`, `in`.
- Label `eq`, `contains`, `exists`.
- Metadata `eq` and `contains`.
- Multiple clauses combine with AND.
- Legacy parameters and structured filters combine with AND.
- Unsafe keys/operators are rejected.

## Implementation Notes

Likely frontend files:

- `OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue`
- `OneOPS-UI/src/api/device/device-v2.ts`
- Optional helper under `OneOPS-UI/src/views/device/device-v2-management/`

Likely backend files:

- `OneOps/app/device/v2/dto/device_v2.go`
- `OneOps/app/device/v2/api/device_v2.go`
- `OneOps/app/device/v2/service/impl/device_v2_minimal_read.go`
- Existing Device V2 list tests under `OneOps/app/device/v2/...`

## Open Decisions Resolved

- Multi-condition search is required.
- Use the structured filter DSL approach.
- Prefer dropdowns when a field has reliable options, but do not force dropdowns for free-form fields.
- Start with AND-only semantics.
