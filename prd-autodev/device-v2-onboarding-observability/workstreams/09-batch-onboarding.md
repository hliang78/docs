# Workstream 09 - Batch Onboarding

## Goal

Extend the closed single-device onboarding path into a bounded batch flow without changing the single-device success contract.

## Current Code Facts

- Backend routes now expose explicit-code batch onboarding:
  - `POST /api/v1/device/v2/onboarding/batch/plan`
  - `POST /api/v1/device/v2/onboarding/batch/ensure`
- Single-device routes remain unchanged:
  - `POST /api/v1/device/v2/:code/onboarding/plan`
  - `POST /api/v1/device/v2/:code/onboarding/ensure`
- `DeviceV2ManagementRedesign.vue` uses a guarded batch flow for multi-select `继续纳管` and renders per-device results.
- Server monitor-mode policy is explicit in batch mode; the flow does not silently choose a mode for multiple servers.
- Evidence is stored in each device's latest `DeviceV2StoreRun.summary_json.onboarding`.

## Requirements

- Add a batch request contract that accepts explicit `codes[]`; do not infer from current page filters.
- Default execution must be sequential and bounded; do not introduce broad remote parallelism in the first batch scope.
- Return per-device results with the same action/evidence shape as single-device onboarding.
- Preserve per-device retry semantics: success actions stay success, failed/unknown actions remain retryable.
- Server devices in a batch must have an explicit monitor-mode policy before `ensure` runs.
- The aggregate response must include counts by `success`, `failed`, `unknown`, `blocked`, and `skipped`, plus per-device evidence pointers.

## Non-Goals

- No bulk concurrent remote configuration.
- No new onboarding DAG.
- No filter-driven "all devices matching query" execution.
- No raw controller response bodies in aggregate evidence.

## Acceptance Shape

- Backend batch `plan` and `ensure` endpoints exist and have focused contract tests. Closed by `D2ON-043`.
- Frontend batch entry opens a guarded confirmation flow and renders per-device results. Closed by `D2ON-044`.
- A live bounded batch probe records exact per-device outcomes without claiming all devices succeeded when one device blocks. Closed by `D2ON-048`.

## 2026-05-18 All-Device Collection Gate

- Owner added a prerequisite before continuing trap target delivery: run collection validation/store for every current Device V2 device.
- Live task `entv2_1779094092855556000` used 17 explicit codes and `options.device_collection2_mode=dc2_only`.
- Result was truthful partial success: 11 devices reached `success/ready`; 6 devices stayed `blocked/unready`.
- Five blocked devices failed controller detection (`device_collection2_required:target_detect_failed`) and are treated as expected per-device blockers for currently unreachable/non-detectable targets.
- One blocked device (`DVC4909DF02CB18`) collected DC2 facts but is blocked by `schema_required_missing:platform_code`.

## 2026-05-18 Batch Closure

- `D2ON-048` ran a bounded explicit batch ensure against one ready H3C/Comware device: `DVCD25E1C13D3C3`.
- The final batch summary was `total=1`, `success=1`, `failed=0`, `unknown=0`, `blocked=0`.
- The probe intentionally did not run broad fleet onboarding and did not select blocked/unready devices from the collection gate.
- Workstream status: completed for explicit-code batch mechanics and bounded live validation.
