# Device Config Management First-Class Design

Date: 2026-06-07

## Positioning

Configuration management is a first-class OneOPS domain.

Config backup is not only a task artifact and not only a row in task history. A successful backup should become an immutable configuration version that OneOPS can compare, baseline, review, audit, and govern. Task execution remains the producer. Device assets remain the operational context. Config management owns the lifecycle of configuration facts.

This design extends the task assetization MVP. The existing Ansible `network-config-backup` lane already projects runtime artifacts into device config backup history. The next step is to turn those backup records into a configuration version system.

## Current State

The current implementation has:

- Task asset precheck and start flow for Ansible network config backup.
- Runtime artifact projection into `platform_device_config_backup`.
- Device detail config backup history.
- Task detail device-result rows with config hash, artifact metadata, and backup-history navigation.

The current implementation does not yet have:

- immutable config version semantics;
- automatic change detection against previous successful backup;
- baseline selection;
- drift status;
- historical diff API;
- redacted diff rendering;
- review state for expected or unexpected changes;
- audit trail for config viewing and diffing.

## Goals

1. Treat each successful backup as a durable config version.
2. Detect whether a new version changed from the previous successful version.
3. Allow operators to compare any two historical versions.
4. Allow operators to compare the current version against a baseline.
5. Keep raw config content governed and hidden by default.
6. Produce change facts that other domains can consume: device detail, config center, alerting, audit, and future policy.

## Non-Goals For MVP

- Full compliance policy engine.
- Approval workflow.
- Automatic rollback or config deployment.
- Multi-vendor semantic parser.
- CMDB-wide compliance reporting.
- Ticketing integration.
- Real-time drift alert push.

Those capabilities should build on top of the version and diff foundation.

## Domain Model

### ConfigVersion

Represents one immutable configuration snapshot for one device.

Core fields:

- `id`
- `tenant_id`
- `device_code`
- `device_name`
- `app_type`
- `vendor_family`
- `access_plane`
- `source_type`: `task_backup`, `agent_collect`, `manual_import`, `external_sync`
- `source_task_id`
- `source_child_task_id`
- `backup_record_id`
- `artifact_name`
- `artifact_storage_key`
- `artifact_sha256`
- `artifact_size`
- `config_hash`
- `backup_time`
- `version_index`
- `previous_version_id`
- `change_status`: `first_backup`, `no_change`, `changed`, `compare_failed`
- `baseline_status`: `no_baseline`, `matches_baseline`, `drifted`, `baseline_compare_failed`
- `created_at`
- `updated_at`

Immutability rule:

- Config content identity fields cannot be updated after creation: artifact key, artifact sha, config hash, backup time, source task.
- Review and derived status may be stored in separate tables or append-only event records.

### ConfigBaseline

Represents the accepted baseline version for one device or a scoped device group.

Core fields:

- `id`
- `tenant_id`
- `scope_type`: `device`, `device_group`, `vendor_family`, future `policy_scope`
- `scope_id`
- `device_code` when scope is device
- `version_id`
- `config_hash`
- `baseline_name`
- `set_by`
- `set_reason`
- `set_at`
- `status`: `active`, `replaced`, `retired`

MVP should support device-level baseline only. Group-level baseline can wait.

### ConfigDiff

Represents a computed comparison between two versions. It may be cached.

Core fields:

- `id`
- `tenant_id`
- `device_code`
- `base_version_id`
- `target_version_id`
- `base_config_hash`
- `target_config_hash`
- `changed`
- `added_lines`
- `removed_lines`
- `modified_lines`
- `redaction_applied`
- `diff_storage_key` or inline short `diff_text`
- `computed_at`
- `compute_status`: `success`, `artifact_missing`, `read_failed`, `redaction_failed`, `too_large`

MVP can compute on demand without persistent cache. Cache should be added if diff becomes slow or frequently reused.

### ConfigChangeEvent

Represents a meaningful configuration change fact.

Core fields:

- `id`
- `tenant_id`
- `device_code`
- `version_id`
- `previous_version_id`
- `change_status`
- `config_hash`
- `previous_config_hash`
- `summary_added_lines`
- `summary_removed_lines`
- `summary_modified_lines`
- `severity`: `info`, `warning`, `critical`
- `review_status`: `unreviewed`, `expected`, `unexpected`, `acknowledged`, `ignored`
- `created_at`

MVP can create events only for `changed` versions. `no_change` remains visible on the version.

### ConfigReview

Represents human handling of a change event.

Core fields:

- `id`
- `tenant_id`
- `change_event_id`
- `review_status`
- `reviewer`
- `reason`
- `related_ticket`
- `reviewed_at`

MVP can defer this table and use `review_status` on `ConfigChangeEvent`; however, append-only review history is better for audit.

## Data Flow

### Backup Projection To Version

```text
task runtime output
  -> artifact manifest
  -> platform_device_config_backup
  -> ConfigVersion
  -> compare with previous successful ConfigVersion
  -> ConfigChangeEvent when changed
  -> compare with active ConfigBaseline when present
  -> update derived drift status
```

The existing backup record remains useful as task provenance. `ConfigVersion` becomes the configuration management fact.

### Change Detection

When a new successful backup is projected:

1. Find latest previous successful version for the same `tenant_id + device_code + access_plane` before this backup time.
2. If none exists, mark `change_status = first_backup`.
3. If `config_hash` equals previous `config_hash`, mark `no_change`.
4. If hashes differ, mark `changed` and create `ConfigChangeEvent`.
5. If hash is missing or artifact metadata is incomplete, mark `compare_failed`.

Hash comparison is a fast signal. It does not replace diff. It tells the system whether diff is worth computing.

### Baseline Drift

When a new version is created:

1. Find active device baseline.
2. If no baseline exists, mark `baseline_status = no_baseline`.
3. If version hash equals baseline hash, mark `matches_baseline`.
4. If different, mark `drifted`.
5. If required data is missing, mark `baseline_compare_failed`.

This keeps drift detection cheap for MVP. Semantic drift policies can come later.

## API Design

### List Device Config Versions

```http
GET /api/v1/device/v2/:code/config-versions?page=1&page_size=20
```

Response:

```json
{
  "list": [
    {
      "id": "ver-1",
      "device_code": "SW001",
      "backup_time": "2026-06-07T10:00:00+08:00",
      "source_task_id": "task-1",
      "artifact_name": "network-config-backup-SW001.cfg",
      "artifact_sha256": "sha",
      "artifact_size": 1234,
      "config_hash": "hash",
      "vendor_family": "huawei_ce",
      "access_plane": "in_band",
      "change_status": "changed",
      "baseline_status": "drifted",
      "previous_version_id": "ver-0"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

### Diff Versions

```http
POST /api/v1/device/v2/:code/config-versions/diff
```

Request:

```json
{
  "base_version_id": "ver-old",
  "target_version_id": "ver-new",
  "context_lines": 3
}
```

Response:

```json
{
  "device_code": "SW001",
  "base_version_id": "ver-old",
  "target_version_id": "ver-new",
  "base_config_hash": "oldhash",
  "target_config_hash": "newhash",
  "changed": true,
  "summary": {
    "added_lines": 12,
    "removed_lines": 4,
    "modified_lines": 8
  },
  "redaction_applied": true,
  "diff_format": "unified",
  "diff_text": "--- old\n+++ new\n@@ ...",
  "warnings": []
}
```

Security rule:

- The API returns redacted diff only.
- It must not return raw config content by default.
- Large diff responses may be truncated with a `truncated` flag and server-side storage key for governed download.

### Compare With Previous

```http
POST /api/v1/device/v2/:code/config-versions/:version_id/diff-previous
```

This is convenience over the generic diff API. It uses `previous_version_id`.

### Set Baseline

```http
POST /api/v1/device/v2/:code/config-baseline
```

Request:

```json
{
  "version_id": "ver-1",
  "reason": "confirmed after maintenance window"
}
```

### Review Change Event

```http
POST /api/v1/device/v2/:code/config-change-events/:event_id/review
```

Request:

```json
{
  "review_status": "expected",
  "reason": "approved VLAN change",
  "related_ticket": "CHG-123"
}
```

This can wait until after MVP if needed.

## Diff And Redaction

The diff service should:

1. Resolve both versions.
2. Verify both versions belong to the requested device and tenant.
3. Read config artifact content from governed storage.
4. Normalize line endings.
5. Apply redaction before diff:
   - password-like commands;
   - SNMP community strings;
   - tokens;
   - private keys;
   - shared secrets;
   - known vendor secret patterns.
6. Generate unified diff.
7. Count added, removed, and modified lines.
8. Audit the access.

Redaction happens before diff so secrets do not leak through changed lines.

MVP redaction can be regex-based and vendor-agnostic. Future versions can add vendor-specific redaction packs.

## Frontend Design

### Page Ownership And Development Entry

Config management needs an independent page because it owns cross-device work: recent changes, unreviewed changes, drift, missing baselines, failed backups, and stale backups. Device detail remains the per-device context, but it should not be the only place where operators discover configuration risk.

Development-stage navigation should be intentionally narrow:

- Build an independent `配置管理` page as the future center surface.
- Do not add the page to the formal menu structure yet.
- Add a top-level `配置管理` button on the Device V2 management page as the temporary entry point.
- If the frontend router requires a route for the page, register it as a hidden or non-menu route and navigate to it from the Device V2 button.
- After the capability is implemented and validated, decide whether the final menu entry belongs under device operations, platform operations, or a dedicated configuration domain.

### Device Detail Config View

The existing config backup block should evolve into a config management block.

Sections:

- current config version summary;
- latest backup status;
- change status from previous version;
- baseline status;
- version history table;
- row actions.

Version history row actions:

- `与上一版对比`
- `选择为对比起点`
- `选择为对比目标`
- `设为基线`
- `查看任务`

The table should show:

- backup time;
- status;
- change status;
- baseline status;
- config hash;
- task id;
- artifact metadata;
- reviewer state when available.

### Diff Drawer

A right-side drawer should show:

- base version and target version metadata;
- summary counts;
- redaction warning;
- unified diff viewer;
- copy/download redacted diff action if allowed.

It must not show raw config preview as the default state.

### Config Management Center

An independent config management page is required for the domain. During development it should be reachable from the Device V2 management page through the top `配置管理` button, not from the final sidebar menu.

The MVP version of this page can start as an operational overview and discovery surface. It does not need the full governance workflow, but it should establish the page shape that future baseline, drift, review, and alerting features will grow into.

Views:

- changed devices today;
- unreviewed changes;
- drifted devices;
- devices without baseline;
- failed backups;
- stale devices with no recent backup.

## Backend Implementation Shape

Suggested packages:

- `app/platform/model/config_version.go`
- `app/platform/model/config_baseline.go`
- `app/platform/model/config_change_event.go`
- `app/platform/dto/config_management.go`
- `app/platform/service/impl/config_version_service.go`
- `app/platform/service/impl/config_diff_service.go`
- `app/platform/api/config_management_api.go`

The existing `device_config_backup_projection.go` should call a new projection service after creating or updating the backup record.

The new service boundary should keep responsibilities clear:

- backup projection owns converting runtime output into backup/version records;
- version service owns previous-version lookup and status derivation;
- diff service owns artifact read, redaction, diff, and audit;
- API layer owns auth, request validation, and response shape.

## Migration Strategy

1. Create config version tables.
2. Backfill versions from existing `platform_device_config_backup`.
3. For each device, sort successful records by backup time and assign `version_index`.
4. Derive `previous_version_id`.
5. Derive `change_status` by `config_hash` comparison.
6. Leave baseline empty initially.

Backfill should not require reading artifact content. Artifact content is needed only for diff.

## MVP Acceptance Criteria

### Backend

- A successful network config backup creates or updates a backup record and creates an immutable config version.
- First successful version for a device is marked `first_backup`.
- Same-hash next version is marked `no_change`.
- Different-hash next version is marked `changed`.
- Changed version creates a change event.
- Version list API returns records ordered by backup time descending.
- Diff API compares two versions of the same device and returns redacted unified diff.
- Diff API rejects cross-device or cross-tenant comparisons.
- Missing artifacts return `compute_status = artifact_missing` or an equivalent error response.

### Frontend

- Device V2 management page has a top `配置管理` button that opens the independent config management page.
- The independent config management page exists but is not added to the final menu structure during development.
- Device detail shows current config version and version history.
- Version history clearly shows `first_backup`, `no_change`, and `changed`.
- Operator can compare a version with previous version.
- Operator can select two versions and open a diff drawer.
- Diff drawer shows redaction notice and summary counts.
- Raw config content is never displayed by default.

### Security

- Secret-like content is redacted before diff generation.
- Config content download and diff access are audited.
- API responses do not expose artifact storage internals beyond governed identifiers or download URLs.

## Phasing

### Phase 1: Version And Change Detection

- Add `ConfigVersion`.
- Project backups into versions.
- Derive previous-version status by hash.
- Update device detail to show version/change state.
- Add the independent config management page shell and the Device V2 top entry button.

### Phase 2: Historical Diff

- Add diff API.
- Add redaction service.
- Add diff drawer.
- Add compare with previous and arbitrary two-version compare.

### Phase 3: Baseline And Drift

- Add device-level baseline.
- Compare current version with baseline.
- Show drift state.
- Allow setting baseline from a version.

### Phase 4: Review And Governance

- Add change events and review workflow.
- Add config management center.
- Add notification hooks and future policy integration.

## Open Decisions

1. Whether MVP stores `ConfigDiff` records or computes diff on demand.
   - Recommendation: compute on demand first, cache only if needed.
2. Whether baselines are part of MVP.
   - Recommendation: no. Add after version and diff are stable.
3. Whether config content can ever be previewed.
   - Recommendation: not by default. Only redacted diff is shown in normal UI.
4. Whether change events are created for `no_change`.
   - Recommendation: no. Store status on version; create events only for `changed` and compare failures.

## Success Definition

OneOPS should be able to answer these questions from first-class configuration facts:

- What is the current known config version of this device?
- Did the latest backup change anything?
- What changed between these two versions?
- Is the current config different from the accepted baseline?
- Who reviewed or accepted the change?
- Which devices changed recently and still need attention?

When these questions are answerable without reading task logs, configuration management has become a first-class capability.
