# Device V2 上线验收 Decisions

UpdatedAt: 2026-05-14T13:25:00+0800

## WS1: DB sample and redacted export

Status: confirmed

1. Sample size: 5 real Device V2 records.
2. Selection rule: pick 1 device from each available device type, prioritizing records with management endpoint/access points, credential refs, and clear protocol/port data.
3. Data access: d2-be/d2-fe workers may use read-only DB/API access to inspect current Device V2 data and produce a redacted sample artifact.
4. Credential boundary: only credential references, credential roles, protocols, ports, and access point relationships may be exported. Plaintext passwords, tokens, community secrets, and private keys are not allowed in prompt, docs, Excel, logs, or evidence.
5. Import code strategy: default to cloned codes using `D2LA_<orig_code>`, preserving original-code mapping and avoiding overwrite of original real-device records.

## WS2: DB-derived Excel import

Status: confirmed

1. Import entry: use the "Device V2 入库工作台" upload UI as the primary acceptance path, not direct API-only import.
2. Cloned Excel field scope: include code, name, type, platform, status, management IP, access_points, credential refs, protocol/port, labels, metadata, and original-code mapping.
3. Original-code mapping: write the source code to `labels.d2la_orig_code`.
4. Incomplete data policy: incomplete rows/types may be included to test validation behavior. Unusable device types may be skipped, but must be recorded as exclusions with reasons.
5. Import lifecycle: upload/validate is itself an acceptance item. Run upload/validate first; only apply after validation succeeds or expected validation failures are documented.

## WS3: Backend contract/test gate

Status: confirmed

1. Test permission: d2-be may run `go test ./app/device/v2/...` and `go test ./app/device/v2/ingest/...`.
2. Small backend fixes are allowed when DB-derived import exposes Device V2 field gaps, DTO mapping gaps, unclear error messages, or missing read-only export fields.
3. Backend write boundary: only Device V2 related paths are approved, especially `app/device/v2/**` and `app/device/v2/ingest/**`. Do not change migrations, production config, credential-system implementation, auth, tenant logic, or broad external integrations without approval.
4. Contract evidence: produce `backend-contract-snapshot.md` with routes, DTO fields, import fields, store evidence APIs, error semantics, and API example responses where useful.
5. Environment failures: if tests or validation depend on real DB/external collection infrastructure and fail because of environment, classify as `environment-blocked` instead of expanding the same story into broad environment debugging.

## WS4: Real collection evidence

Status: confirmed

1. Collection protocol selection: do not force SNMP/SSH/WinRM/DC2 in stories. Collection is driven by the controller detect mechanism. Acceptance must ensure credential refs, access_points, endpoint, protocol/port hints, and related metadata are prepared for detect.
2. Execution scale: first run store collection on 1 imported cloned device to prove the path. After the single-device path is proven, run a 5-device parallel collection test using the confirmed sample set.
3. Trigger entry: prefer triggering store/start from the 设备 V2 清册管理 UI. If UI is blocked, API trigger with the same login/session context is allowed, but the reason must be recorded.
4. Polling/time budget: each story polls only within its time budget. If the task is still pending, write `task_id`, current status, and the next polling command/artifact, then stop without expanding scope.
5. Empty evidence classification: observations/DC2 empty states should be classified as `business-empty`, `credential-blocked`, `network-blocked`, `backend-contract-blocked`, `environment-blocked`, or `unknown`.

## WS5: Edit/delete/cleanup policy

Status: confirmed

1. Cloned device cleanup: `D2LA_*` cloned devices may be deleted at the end of acceptance. The desired final state is clean teardown, so all cloned devices should be deleted after evidence is captured.
2. Original real-device safety: original real Device V2 records must not be deleted. They may only be checked read-only for safety/reconciliation unless separately approved.
3. Edit/update testing: editing and modification must be tested on cloned `D2LA_*` devices only. Low-risk fields such as name, labels, metadata, and status are preferred.
4. Import Batch cleanup: do not purge import batch records. Keep import batch/task/row records as launch acceptance evidence.
5. Retention policy: no planned retention of cloned devices after acceptance. If deletion fails, record the exact blocker; do not silently leave clones behind.

## WS6: Launch readiness report

Status: confirmed

1. Go/no-go standard: P0 may go live with explicit `ACCEPTED RISK`, but the risk must be named, evidenced, and accepted by a human.
2. Report artifacts: produce `evidence-index.md`, `launch-readiness-report.md`, a P0/P1 risk table, and final status values `PASS`, `BLOCKED`, or `ACCEPTED RISK`.
3. Page-level conclusion: the final report must distinguish Device V2 入库工作台 from 设备 V2 清册管理.
4. Parallel collection failures: if 5-device parallel collection partially fails while the single-device path passes, the worker must not auto-PASS. It should present evidence and leave final PASS/BLOCKED/ACCEPTED RISK to human decision.
5. Required lists: include both "must fix before launch" and "post-launch watch list".
