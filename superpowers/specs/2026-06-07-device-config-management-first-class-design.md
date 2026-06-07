# Config Management First-Class Design

Date: 2026-06-07

## Positioning

Configuration management is a first-class OneOPS domain.

Config backup is not only a task artifact and not only a row in task history. A successful backup or collection should become an immutable configuration version that OneOPS can compare, baseline, review, audit, and govern. Task execution remains the producer. Assets remain the operational context. Config management owns the lifecycle of configuration facts.

This design extends the task assetization MVP. The existing Ansible `network-config-backup` lane already projects runtime artifacts into device config backup history. The next step is to turn those backup records into a configuration version system.

Although the first implemented lane is network device backup, the domain must not be limited to network devices. Servers, middleware, and application runtime configuration should also become governed configuration assets. Network device configuration is the first collection source; configuration management is the cross-asset control plane.

## Current State

The current implementation has:

- Task asset precheck and start flow for Ansible network config backup.
- Runtime artifact projection into `platform_device_config_backup`.
- Config version projection from device backup records.
- Device config version list and redacted diff APIs.
- A development entry from Device V2 management into an independent config management page.
- Device detail config backup history.
- Task detail device-result rows with config hash, artifact metadata, and backup-history navigation.

The current implementation does not yet have:

- a cross-asset configuration model for servers and applications;
- server configuration collection and versioning;
- baseline selection;
- drift status;
- review state for expected or unexpected changes in a full workflow;
- audit trail for config viewing and diffing.

## Goals

1. Treat each successful backup or collection as a durable config version.
2. Detect whether a new version changed from the previous successful version.
3. Allow operators to compare any two historical versions.
4. Allow operators to compare the current version against a baseline.
5. Keep raw config content governed and hidden by default.
6. Support network devices first, then servers and application configuration through the same lifecycle.
7. Produce change facts that other domains can consume: device detail, server detail, config center, alerting, audit, and future policy.

## Non-Goals For MVP

- Full compliance policy engine.
- Approval workflow.
- Automatic rollback or config deployment.
- Multi-vendor semantic parser.
- Deep server hardening benchmark checks.
- Application-specific semantic configuration parser.
- CMDB-wide compliance reporting.
- Ticketing integration.
- Real-time drift alert push.

Those capabilities should build on top of the version and diff foundation.

## Domain Model

### Asset Scope

Configuration management should use a cross-asset identity, even if MVP keeps compatibility fields for Device V2.

Recommended identity fields:

- `asset_type`: `network_device`, `server`, `application`, future `database`, `middleware`
- `asset_code`: canonical asset code, such as `device_code` or server code
- `asset_name`
- `config_scope`: the configuration domain captured by this version
- `collector_type`: `netlink`, `ansible`, `shell`, `powershell`, `agent_collect`, `manual_import`, `external_sync`
- `collection_plane`: `in_band`, `out_band`, `agent`, `local`, `unknown`

MVP can keep `device_code` in APIs and tables for network devices, but new service and UI concepts should speak in terms of assets. `device_code` should be treated as the Device V2 compatibility alias for `asset_code`.

Supported `config_scope` values should start small:

- `network_running_config`: network device running configuration.
- `server_system_snapshot`: OS, kernel, hostname, DNS, NTP, timezone, users, services, packages, firewall, scheduled jobs.
- `server_config_file`: governed file content such as SSH, sudoers, resolver, chrony, nginx, redis, mysql, agent, or application config files.
- `application_config`: application runtime or deployment configuration collected from an application asset.
- `package_manifest`: package inventory when it is treated as configuration drift input.
- `service_manifest`: service enablement and running-state inventory.

This keeps the model broad enough for servers without forcing every configuration type into one undifferentiated text file.

### ConfigVersion

Represents one immutable configuration snapshot for one asset and one configuration scope.

Core fields:

- `id`
- `tenant_id`
- `asset_type`
- `asset_code`
- `asset_name`
- `config_scope`
- `collector_type`
- `collection_plane`
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

`device_code`, `device_name`, `app_type`, `vendor_family`, and `access_plane` remain useful for Device V2 compatibility. For servers and applications, the normalized fields should be the source of truth.

Immutability rule:

- Config content identity fields cannot be updated after creation: artifact key, artifact sha, config hash, backup time, source task.
- Review and derived status may be stored in separate tables or append-only event records.

### ConfigBaseline

Represents the accepted baseline version for one asset or a scoped asset group.

Core fields:

- `id`
- `tenant_id`
- `asset_type`
- `scope_type`: `asset`, `asset_group`, `vendor_family`, `server_role`, future `policy_scope`
- `scope_id`
- `asset_code` when scope is asset
- `version_id`
- `config_hash`
- `baseline_name`
- `set_by`
- `set_reason`
- `set_at`
- `status`: `active`, `replaced`, `retired`

MVP should support asset-level baseline only. Group-level baseline can wait.

### ConfigDiff

Represents a computed comparison between two versions. It may be cached.

Core fields:

- `id`
- `tenant_id`
- `asset_type`
- `asset_code`
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
- `asset_type`
- `asset_code`
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

### Network Backup Projection To Version

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

### Server Collection Projection To Version

Server configuration management should use the same versioning path, with a different producer.

```text
server asset
  -> collection task or agent command
  -> precheck: agent reachable, credential usable, collection scope supported
  -> collector output manifest
  -> governed artifact files
  -> ConfigVersion per collected scope
  -> compare with previous successful ConfigVersion for same asset and scope
  -> ConfigChangeEvent when changed
  -> compare with active ConfigBaseline when present
  -> update derived drift status
```

For Linux servers, the first useful scopes are:

- `server_system_snapshot`: hostname, OS release, kernel, interfaces summary, DNS, NTP/timezone, users, groups, sudoers presence, SSH settings summary, package manifest, service manifest, firewall summary, crontab summary, agent status.
- `server_config_file`: explicit governed files such as `/etc/ssh/sshd_config`, `/etc/sudoers`, `/etc/hosts`, `/etc/resolv.conf`, `/etc/chrony.conf`, and service-specific config files selected by server role.

For Windows servers, the equivalent producer can use PowerShell collection:

- OS and patch summary.
- local users and groups.
- services.
- scheduled tasks.
- firewall rules.
- selected registry keys and application configuration files.

Server collection should not scrape the entire filesystem. Operators should define scopes and file allowlists. This keeps the blast radius predictable and avoids accidentally storing secrets or very large artifacts.

### Generic Collection Record

`platform_device_config_backup` is the right compatibility table for Device V2 network backup history, but it should not become the long-term generic table for all assets.

Recommended evolution:

- Keep `platform_device_config_backup` for network-device task provenance and existing UI compatibility.
- Add a generic `platform_config_collection_record` when server or application collection is implemented.
- Project both device backup records and generic collection records into `ConfigVersion`.

This lets configuration management remain cross-asset without breaking the already implemented network-device path.

### Change Detection

When a new successful backup or collection is projected:

1. Find latest previous successful version for the same `tenant_id + asset_type + asset_code + config_scope + collection_plane` before this collection time.
2. If none exists, mark `change_status = first_backup`.
3. If `config_hash` equals previous `config_hash`, mark `no_change`.
4. If hashes differ, mark `changed` and create `ConfigChangeEvent`.
5. If hash is missing or artifact metadata is incomplete, mark `compare_failed`.

Hash comparison is a fast signal. It does not replace diff. It tells the system whether diff is worth computing.

### Baseline Drift

When a new version is created:

1. Find active asset baseline for the same asset and configuration scope.
2. If no baseline exists, mark `baseline_status = no_baseline`.
3. If version hash equals baseline hash, mark `matches_baseline`.
4. If different, mark `drifted`.
5. If required data is missing, mark `baseline_compare_failed`.

This keeps drift detection cheap for MVP. Semantic drift policies can come later.

## API Design

### Global Config Management Overview

```http
GET /api/v1/config-management/overview?asset_type=network_device|server|application
```

Response should return actionable counters, not only decoration:

```json
{
  "changed_today": 3,
  "unreviewed_changes": 2,
  "drifted_assets": 1,
  "assets_without_baseline": 12,
  "failed_collections": 1,
  "stale_assets": 5
}
```

Each counter should map to a filtered list view so the operator can continue the workflow.

### List Config Versions

```http
GET /api/v1/config-management/versions?asset_type=server&asset_code=SRV001&config_scope=server_system_snapshot&page=1&page_size=20
```

This is the generic API for new surfaces. Device-specific APIs can remain for Device V2 compatibility.

### List Change Events

```http
GET /api/v1/config-management/change-events?asset_type=server&review_status=unreviewed&page=1&page_size=20
```

### Trigger Collection

```http
POST /api/v1/config-management/collect
```

Request:

```json
{
  "asset_type": "server",
  "asset_codes": ["SRV001", "SRV002"],
  "collector_type": "agent_collect",
  "config_scopes": ["server_system_snapshot", "server_config_file"],
  "collection_plane": "agent",
  "credential_ref": "optional-fallback",
  "dry_run": false
}
```

The response should return the parent task id and precheck result. The UI should always lead operators through precheck before execution for multi-asset collection.

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

### Server-Specific Convenience APIs

Server detail pages may expose convenience routes such as:

```http
GET /api/v1/server/:code/config-versions
POST /api/v1/server/:code/config-versions/:version_id/diff-previous
```

These routes should delegate to the generic config management service and should not introduce a separate server-only lifecycle.

## Diff And Redaction

The diff service should:

1. Resolve both versions.
2. Verify both versions belong to the requested asset and tenant.
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

Config management needs an independent page because it owns cross-asset work: recent changes, unreviewed changes, drift, missing baselines, failed collections, and stale collections. Device detail and server detail remain per-asset contexts, but they should not be the only places where operators discover configuration risk.

Development-stage navigation should be intentionally narrow:

- Build an independent `配置管理` page as the future center surface.
- Do not add the page to the formal menu structure yet.
- Add a top-level `配置管理` button on the Device V2 management page as the temporary entry point.
- If the frontend router requires a route for the page, register it as a hidden or non-menu route and navigate to it from the Device V2 button.
- After the capability is implemented and validated, decide whether the final menu entry belongs under device operations, platform operations, or a dedicated configuration domain.

### Config Management Center

The independent page should become the operator's daily workspace. It should not be a passive dashboard.

Primary tabs:

- `总览`: actionable counters and recent risk summary.
- `资产配置`: all assets with current version, baseline, stale status, and latest collection result.
- `变化审计`: changed versions and review state.
- `基线治理`: assets without baseline, drifted assets, and baseline operations.
- `采集任务`: collection/backup task runs, failures, retries, and precheck results.

Global filters:

- asset type: network device, server, application;
- config scope;
- environment or business system when available;
- status: changed, no change, drifted, no baseline, failed, stale;
- review status.

Action principle:

- Every summary card must route to a filtered list.
- Every list row must expose the next likely action: diff, review, set baseline, retry collection, view task, or open asset detail.
- The page should show risk and work queues first, then historical detail.

### Network Device Daily Closed Loop

Network devices are the first operational example for the config management center. The daily path should be visible and executable from the page, not hidden behind task history.

Closed-loop path:

1. `发现工作项`: the operator starts from actionable counters such as changed devices, backup failures, missing baselines, stale backups, and drifted assets.
2. `确认范围`: the operator narrows the queue by device, vendor family, access plane, config scope, and latest work status.
3. `执行预检`: before backup or retry, the system checks netlink or Ansible reachability, credential availability, access plane, collector support, and artifact storage readiness.
4. `发起备份`: the selected devices are collected through netlink or Ansible and linked to a task run.
5. `版本入库`: every successful collection becomes an immutable config version with source task, artifact, hash, timestamp, and previous-version relation.
6. `差异审查`: changed versions are compared with the previous successful version or active baseline. The UI should show redacted diff, summary counts, and task provenance.
7. `基线/修复`: the operator accepts expected change as the new baseline, records an expected change, creates or links a repair task for unexpected change, or leaves it unreviewed with a reason.
8. `复采关闭`: after baseline update or repair, the operator triggers or waits for another backup. The loop closes only when the latest version is stable, diff status is reviewed, and baseline status is acceptable.

Frontend closure rules:

- A summary card must lead to a filtered work queue.
- A selected row must show the current stage, current evidence, and the next likely action.
- The page must keep the operator on the same workspace while drilling into device detail or task detail.
- If the backend write action is not available yet, the UI should mark the action as pending instead of pretending it completed.
- A work item is considered closed only when the latest collection result, diff status, baseline status, and review state all agree.

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

### Server Detail Config View

Server detail should have the same configuration management block as network device detail, but with server scopes.

Sections:

- current system snapshot version;
- latest collection status;
- selected config file versions;
- package and service manifest versions when enabled;
- change status from previous version;
- baseline status;
- version history table by scope.

Server row actions:

- `与上一版对比`
- `选择为对比起点`
- `选择为对比目标`
- `设为基线`
- `重新采集`
- `查看任务`

Server diff should show the scope clearly. A change in `/etc/ssh/sshd_config` and a change in package manifest should not look like the same kind of event.

### Closed-Loop Operation Path

The product workflow must close the loop from discovery to verification.

1. Discover scope.
   - Operator enters config management from Device V2 during development or from the future formal menu.
   - Operator filters by asset type, status, business system, or config scope.
2. Precheck collection.
   - Operator selects assets and collection scopes.
   - System checks reachability, agent status, credential availability, collector support, and previous collection state.
3. Execute backup or collection.
   - Network devices use netlink or Ansible backup.
   - Servers use agent, shell, Ansible, or PowerShell collection depending on platform and access model.
4. Project facts.
   - Runtime artifacts become collection records.
   - Collection records become immutable config versions.
   - Version comparison derives changed, no change, first backup, failed, stale, and drift status.
5. Inspect difference.
   - Operator opens changed assets from the work queue.
   - Diff viewer shows redacted unified diff and summary counts.
6. Classify change.
   - Operator marks change as expected, unexpected, acknowledged, or ignored.
   - Operator can attach maintenance reason or future ticket id.
7. Remediate or accept.
   - Expected change can become the new baseline.
   - Unexpected change can create a remediation task or external ticket later.
   - Collection failure can be retried after fixing credential, agent, or reachability.
8. Verify closure.
   - Operator triggers a new collection after remediation.
   - If the latest version matches baseline or expected state, the event moves out of the active queue.
   - The audit trail keeps who saw, compared, reviewed, and accepted the change.

This is the minimum closed loop: collect, version, compare, review, act, re-collect, and close.

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

Server collection should add a producer layer without changing version semantics:

- collector service owns precheck and task creation;
- Linux collector owns command or agent payload definitions;
- Windows collector owns PowerShell payload definitions;
- projection service owns converting output manifests into config versions;
- config management service remains asset-type agnostic.

## Migration Strategy

1. Create config version tables.
2. Backfill versions from existing `platform_device_config_backup`.
3. For each device, sort successful records by backup time and assign `version_index`.
4. Derive `previous_version_id`.
5. Derive `change_status` by `config_hash` comparison.
6. Leave baseline empty initially.

Backfill should not require reading artifact content. Artifact content is needed only for diff.

### Server Migration And Bootstrap

Server configuration management needs bootstrap rather than pure migration.

1. Identify server assets eligible for config management.
2. Mark supported collection methods per server: agent, shell, Ansible, PowerShell.
3. Create default collection scopes by OS and role.
4. Run dry-run precheck to classify unavailable agents, missing credentials, unsupported OS, and unreachable assets.
5. Run first collection for eligible servers.
6. Project first successful collection as `first_backup` for compatibility with the existing status vocabulary.
7. Keep ineligible servers visible as `not_ready` instead of silently excluding them.

The center should show unsupported or not-ready assets because they are part of governance risk.

## MVP Acceptance Criteria

### Backend

- A successful network config backup creates or updates a backup record and creates an immutable config version.
- A successful server system snapshot collection creates an immutable config version for the server asset.
- A successful governed server config file collection creates one version per configured file or file group scope.
- First successful version for an asset and scope is marked `first_backup`.
- Same-hash next version is marked `no_change`.
- Different-hash next version is marked `changed`.
- Changed version creates a change event.
- Version list API returns records ordered by backup time descending.
- Diff API compares two versions of the same asset and scope and returns redacted unified diff.
- Diff API rejects cross-asset, cross-scope, or cross-tenant comparisons.
- Missing artifacts return `compute_status = artifact_missing` or an equivalent error response.
- Generic config management APIs can list versions and change events by asset type, asset code, and config scope.
- Failed collection is visible as a collection/task fact and can be retried.

### Frontend

- Device V2 management page has a top `配置管理` button that opens the independent config management page.
- The independent config management page exists but is not added to the final menu structure during development.
- The independent page can filter by asset type and show network devices and servers in one work queue.
- Summary cards are actionable and open filtered lists.
- Device detail shows current config version and version history.
- Server detail can show system snapshot and governed config file version history.
- Version history clearly shows `first_backup`, `no_change`, and `changed`.
- Operator can compare a version with previous version.
- Operator can select two versions and open a diff drawer.
- Diff drawer shows redaction notice and summary counts.
- Raw config content is never displayed by default.
- Operators have a clear path from failed collection or detected change to retry, diff, review, baseline, or task detail.

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

### Phase 2: Historical Diff And Work Queues

- Add diff API.
- Add redaction service.
- Add diff drawer.
- Add compare with previous and arbitrary two-version compare.
- Add actionable config management overview counters and filtered lists.

### Phase 3: Server Configuration Management

- Add generic collection record or equivalent projection source.
- Add server system snapshot collection.
- Add governed config file allowlist collection.
- Project server collection into `ConfigVersion`.
- Show server configuration versions in the config management center.

### Phase 4: Baseline And Drift

- Add asset-level baseline for network devices.
- Add server asset-level baseline.
- Compare current version with baseline.
- Show drift state.
- Allow setting baseline from a version.

### Phase 5: Review And Governance

- Add change events and review workflow.
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
5. Whether `platform_device_config_backup` evolves into a generic table.
   - Recommendation: keep it as network-device provenance and add `platform_config_collection_record` for generic assets.
6. Which server scopes enter the first server MVP.
   - Recommendation: `server_system_snapshot` and a small allowlist of critical config files.
7. Whether application config belongs under server or application assets.
   - Recommendation: collect host-local files under server scope first; model application-declared runtime config as `application_config` when application assets are ready.

## Success Definition

OneOPS should be able to answer these questions from first-class configuration facts:

- What is the current known config version of this asset?
- Did the latest backup or collection change anything?
- What changed between these two versions?
- Is the current config different from the accepted baseline?
- Who reviewed or accepted the change?
- Which assets changed recently and still need attention?
- Which servers are missing collection coverage, baseline, or successful recent snapshots?

When these questions are answerable without reading task logs, configuration management has become a first-class capability.
