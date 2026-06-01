# D2 Redesign Rollout Context

UpdatedAt: 2026-05-13
Source: `/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/D2_REDESIGN_AI_AUTODEV_GUIDE.md`

This is the compact D2 rollout context for agent-loop workers. Prefer this file
over reading the full guide unless a specific story requires a precise section.

## Product Goal

Make the two D2 redesign pages the real production entrypoints for device import,
ingest, collection, inventory management, and lifecycle maintenance.

Formal entrypoints:

- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2IngestPipelineRedesign.vue`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue`

The old pages may be referenced and migrated from, but they are not the final
entrypoints.

## Document Priority

1. `docs/openclaw-autodev/D2_INGEST_BASE_FIELD_TABLE.md`
2. `docs/openclaw-autodev/D2_REDESIGN_AI_AUTODEV_GUIDE.md`
3. `docs/openclaw-autodev/D2_FE_INGEST_MANAGEMENT_REDESIGN_PLAN.md`
4. `docs/openclaw-autodev/D2_FE_P0_IMPLEMENTATION_TASKS.md`
5. `docs/openclaw-autodev/D2_FE_REDESIGN_GAP_ANALYSIS.md`
6. `docs/openclaw-autodev/D2_BACKEND_DEVICE_V2_INGEST_FIELD_AUDIT.md`

If docs and code disagree, inspect the real code/API behavior first, then update
evidence or record the gap.

## Hard Rules

- Do not fake import, detect, collection, store, or success evidence.
- Do not add mocks, pseudo-success, swallowed errors, silent defaults, or broad
  fallbacks for missing backend capability.
- `access_points` are first-class data and must not be reduced to a naked IP.
- `credential_refs` are references only; never display or persist secrets.
- `catalog` is independent; do not substitute `device_kind/vendor/model`.
- Keep entity status, ingest result status, store readiness, and attributes
  status separate.
- If the backend does not return a field, show a clear missing/blocked state
  instead of deriving it from drafts.
- Advanced JSON is allowed only as an advanced escape hatch; core fields need
  structured UI.

## Required Field Groups

- Identity: `code/biz_code/name/biz_name/sn/asset_number/hostname`
- Platform/catalog: `platform/platform_code/platform_name/catalog/catalog_code/catalog_name`
- Access points: `access_points[]`
- Credential references: `credential_ref_*`, `credential_refs`
- Status layers: `status/manageable/manage_status/manageable_status/core_store_status`
- Location: `tenant/region/site/rack/location_node_code`
- System profile: `system_version/patch_version/firmware_version/kernel_version/os_name/os_version/architecture`
- Hardware profile: `cpu_arch/cpu_model/cpu_cores/cpu_sockets/memory_total/memory_total_bytes/memory_slots/hardware`
- Source: `source/batch_id/task_id/run_id/matched_by/row_no`

## FE Implementation Shape

Prefer small modules under:

```text
src/views/device/device-v2-redesign/
  field-model.ts
  lifecycle.ts
  store-task.ts
  import-flow.ts
  management-mappers.ts
  validation.ts
  components/
```

Do not copy thousands of lines from old pages into redesign pages. Migrate
behavior into composables/helpers/components where practical.

## Backend Contract Surface

Confirmed API groups:

- Ingest: `/device/v2/ingest/capabilities`, template, tasks, upload, task detail.
- Import batch: create/upload/validate/apply/retry/update records/list/summary/records/anchor/templates.
- Management: list/create/detail/update/delete/status/store-readiness/network/interfaces/change-history.
- Store/collection: `store/start`, `store/retry`, task detail/summary/runs/observations/collection-plans, last DC2 collection.

Backend workers should verify and extend real contracts only when a concrete FE
story needs it. Do not invent API behavior for unconfirmed UI controls.

## Rollout Phases

A. Field model foundation:
Create shared FE field helpers/types and attach both redesign pages lightly.

B. Ingest page productionization:
Support base fields, access points, credential refs, catalog, system/hardware,
local validation, submit/upload result truth, and management handoff.

C. Management inventory productionization:
Server-side list, details by field group, structured edit drawer, delete, source
and status layering.

D. Store and collection evidence:
Migrate real store/start, task result drawer, runs, observations,
collection-plans, and DC2 evidence display.

E. Import batch fusion:
Integrate or clearly expose import batch validate/apply/records/summary and
pass_1_base/pass_2_access/pass_3_credential/pass_4_relation.

F. Go-live closure:
Finish loading/empty/error/permission/confirmation states, remove fake pending
contract controls, and record manual validation evidence.

## Validation

Frontend:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npm run typecheck:d2
```

Backend:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/device/v2/...
go test ./app/device/v2/ingest/...
```

Runtime/browser validation:

- Ensure backend through `/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-d2-runtime.sh ensure-backend`.
- Use login `admin/admin@123`.
- Prefer deterministic browser evidence through `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run smoke:d2-redesign-browser`.
- Record page, network, console, and interaction evidence when a FE story changes visible behavior.
