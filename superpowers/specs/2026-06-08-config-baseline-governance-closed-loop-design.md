# Config Baseline Governance Closed Loop Design

Date: 2026-06-08

## Positioning

Configuration baseline is a policy, not a full configuration snapshot.

A baseline defines the minimum configuration requirements that a class of assets or applications must satisfy. A collected configuration version is evaluated against the active baseline policy version that applies to its asset identity. If the configuration no longer satisfies the active policy, the asset has drifted even if the raw configuration diff is small.

The existing selected-version baseline flow remains as a compatibility path, but the governed baseline flow is rule-based and versioned.

## Current Gap

Current implementation stores `baseline_status` directly on each config version. Setting a baseline marks one complete config version as `matches_baseline` and clears other versions for the same asset. This is useful for simple device-by-device comparison, but it cannot express:

- baselines shared by a device class or application class;
- minimum required content instead of complete config equality;
- baseline versions that change when an application or platform version changes;
- persistent drift evaluation history;
- explicit findings explaining which requirement failed.

## MVP Scope

The first governed baseline increment adds:

- baseline policies scoped by asset identity and optional target match fields;
- baseline policy versions with a JSON rule list;
- manual baseline evaluation for one or more config versions;
- latest evaluation surfacing in the config management queue;
- frontend policy list, simple policy creation, and manual evaluation entry.

The MVP does not add a complex DSL, automatic scheduled evaluation, or automatic baseline generation from existing config. Those are follow-up increments.

## Data Model

`platform_config_baseline_policy`

- `id`: policy id.
- `name`: business name.
- `description`: operator-facing description.
- `asset_type`: `network_device`, `server`, `application`, or future values.
- `config_scope`: `running_config`, `server_config`, or future values.
- `collection_plane`: `inband`, `agent`, or future values.
- `vendor_family`: optional device vendor family selector.
- `app_type`: optional application type selector.
- `target_match_json`: optional selector extension for model, app version, environment, or labels.
- `status`: `draft`, `active`, or `retired`.
- `active_version_id`: current active policy version.
- timestamps.

`platform_config_baseline_policy_version`

- `id`: version id.
- `policy_id`: owning policy.
- `version_index`: monotonically increasing number within the policy.
- `status`: `draft`, `active`, or `retired`.
- `rules_json`: JSON array of baseline rules.
- `notes`: change notes.
- timestamps.

`platform_config_baseline_evaluation`

- `id`: evaluation id.
- `policy_id`: matched policy.
- `policy_version_id`: evaluated policy version.
- `config_version_id`: evaluated immutable config version.
- asset identity fields copied from the config version.
- `status`: `compliant`, `drifted`, `failed`, or `not_applicable`.
- `summary_json`: counts and failed rule details.
- `evaluated_at`: evaluation time.

## Rule Model

Each rule has:

- `id`
- `name`
- `type`: `required_text`, `forbidden_text`, `required_regex`, or `forbidden_regex`
- `pattern`
- `severity`: `info`, `warning`, or `critical`
- `description`

Evaluation semantics:

- `required_text`: drifted when normalized content does not contain `pattern`.
- `forbidden_text`: drifted when normalized content contains `pattern`.
- `required_regex`: drifted when regex does not match normalized content.
- `forbidden_regex`: drifted when regex matches normalized content.
- invalid regex or unreadable artifact returns `failed`.

## API

Device V2 config management gains:

- `GET /device/v2/config-management/baseline-policies`
- `POST /device/v2/config-management/baseline-policies`
- `POST /device/v2/config-management/baseline-policies/:policy_id/versions`
- `POST /device/v2/config-management/baseline-policies/:policy_id/activate`
- `POST /device/v2/config-management/baseline-evaluations:run`

Existing version list and asset queue APIs continue to work. Asset rows prefer latest rule evaluation status when one exists.

## Frontend

Configuration management adds a `基线管理` view inside the same page.

The queue keeps daily operations visible. The baseline view shows policies, active version, scope, rule count, and status. Operators can create a simple policy, add rules, activate it, and run evaluation on selected config versions.

The queue baseline column is renamed conceptually from "whether one version was set as baseline" to "baseline compliance":

- `未配置基线策略`
- `符合基线`
- `已漂移`
- `评估失败`

## Acceptance Criteria

- A policy with required and forbidden rules can be created and activated.
- A config version can be evaluated against the applicable active policy.
- Evaluation stores findings and returns `compliant` or `drifted`.
- Config management asset rows show latest evaluation status when present.
- Existing selected-version baseline APIs remain available.
- Frontend exposes policy management and manual evaluation without leaving configuration management.
