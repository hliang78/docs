# Device V2 Ingest Usability Optimization Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce the mental load for first-time users importing Device V2 devices from existing customer Excel files.

**Architecture:** Keep the backend ingest contracts stable. Let the frontend recognize legacy/customer headers, normalize them into Device V2 draft rows, and submit normalized payloads when the original Excel cannot be safely uploaded to the backend.

**Tech Stack:** Vue 3, Ant Design Vue, TypeScript, XLSX, existing Device V2 ingest APIs.

---

## Product Direction

The import page should behave like an intake assistant, not a strict schema gate. A new user with a customer-provided device spreadsheet should not need to learn every internal field before seeing a successful import. The page should translate common customer terms, preserve ambiguous legacy fields as traceable notes, and explain only the decisions the user must make.

## Current Increment

- [x] Recognize common Chinese headers from customer-provided device spreadsheets.
- [x] Preserve `归属类别` and `虚拟区域` by merging them into `remark` with source labels.
- [x] Default SNMPv2c helper fields when `snmp_community` is present.
- [x] Submit normalized draft payloads for alias-based files instead of uploading raw unsupported headers to the backend.
- [x] Add compact frontend guidance for credential catalog choices and `biz_code` versus system Code.
- [x] Add a smoke test for the customer Excel header mapping.
- [x] Add a credential creation shortcut from the import page for users who choose the manual credential path.
- [x] Expose business code and system Code side by side in the Device V2 list.
- [x] Add a repeatable novice-agent reset script that clears Device V2 devices and SSH/SNMP credentials before each test.
- [x] Clarify in the user manual that upload/import is not the end of onboarding; novice users must continue into collection and monitoring.
- [x] Clarify that the batch task workbench is saved only after the user confirms execution and a task is created.
- [x] Display monitor missing required fields from structured task details, not only from legacy message text.
- [x] Add screenshot decision points for novice users, and defer new screenshot assets until real novice feedback identifies the confusing pages.
- [x] Humanize collection detect-failure messages in both process cards and collection result rows.
- [x] Make batch selection count and selected-device scope visible before batch collection or monitoring.
- [x] Clarify batch confirm dialogs: tasks are created and saved to the workbench only after the user clicks start.
- [x] Keep the ingest result panel visible and add an explicit next-step prompt to continue collection and monitoring.
- [x] Capture novice-feedback screenshots 15-21 after the product copy and hint updates.

## Next Product Increments

- [ ] Provide a recent batch task entry point so users can recover created collection/monitoring workbenches after navigation or login recovery.
- [ ] Add a mapping preview drawer before submit: source column, normalized field, sample value, and whether the value will be stored as credential, attribute, or remark.
- [ ] Show generated credential references in the import result summary without exposing secrets.
- [ ] Expose business code and system Code side by side in import results and device list search hints.
- [ ] Move the Chinese alias map into a backend-shared config or API endpoint so frontend and backend cannot drift.

## Validation

- `npm run smoke:d2-company-excel-import`
- `npm run typecheck:d2`
- Before every novice-agent run, execute `OneOps/scripts/platform2_multi_agent_test/reset_device_v2_novice_env.sh` and confirm Device V2 devices, Device V2 entities, registry rows, and active SSH/SNMP credentials are all zero.
- Novice agents must act as non-developer operations users and continue past upload/import into Device V2 collection and monitoring onboarding. Stopping at “device list uploaded” is not a complete validation run.
- When validating batch collection, treat an unconfirmed confirmation dialog as unsaved. Only a created task should appear in the batch task workbench after navigation or login recovery.
- Novice agents should report where a screenshot would have helped. Add or refresh screenshots only for those real decision points.
- Latest novice feedback screenshot targets have been captured as `15-novice-*` through `21-novice-*` in the user-manual assets directory.
- Manual browser upload with a 1-row Chinese-header workbook when Playwright/CDP tooling is available in the environment.
