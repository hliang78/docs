# Device V2 Launch Acceptance Evidence Index

GeneratedAt: 2026-05-15T08:24+08:00  
Story: D2LA-005A  
Scope: compact index for P0 rows in `test-matrix.md`, using Batches 001-004 evidence only. Docs-only; no tests, browser flows, API writes, cleanup, or product-code changes were run.

## Overall posture

- **Launch readiness is not auto-PASS.** The full intended 5-device sample remains incomplete.
- **Safe proven slice:** 2 approved imported `D2LA_*` clones have import/apply, management handoff, field reconciliation, credential-ref preservation, store start, real observations, and latest DC2 evidence.
- **Human decision required:** the remaining 3 candidates lack authoritative platform/catalog/rack enrichment and were not safely imported or collected. Final go/no-go must be `BLOCKED` or explicit human `ACCEPTED RISK`; this index records them as `BLOCKED`, not pass.
- **Accepted risk already recorded:** one original-record platform-code delta on `DVCE5B9B461254F` was explicitly operator-accepted in D2LA-004B evidence.

## Source evidence by batch

| Batch | Evidence | Result used here |
| --- | --- | --- |
| Batch 001 | `docs/openclaw-autodev/evidence/d2-be/D2LA-001-DB-DERIVED-SAMPLE-CONTRACT/summary.md`; `docs/prd-autodev/d2-launch-acceptance/evidence/batch-001-summary.md` | DB-derived sample/export contract exists for 5 real devices; PRD batch summary is still TBD, so row-level evidence relies on D2LA-001 summary. |
| Batch 002 | `docs/openclaw-autodev/evidence/d2-fe/D2LA-002/summary.md`; `docs/openclaw-autodev/evidence/d2-fe/D2LA-IMPORT/summary.md`; `docs/openclaw-autodev/evidence/d2-fe/D2LA-IMPORT/d2la-002d-summary.md`; `docs/openclaw-autodev/evidence/d2-be/D2LA-002E/reconciliation.md` | Excel/import mapping supports traceability; concrete XLSX generated with 5 source rows / 2 import rows / 3 skipped; fresh 2-row import/apply and reconciliation ready. |
| Batch 003 | `docs/openclaw-autodev/evidence/d2-fe/D2LA-003/summary.md`; `docs/openclaw-autodev/evidence/d2-fe/D2LA-003A/readiness.json`; `docs/openclaw-autodev/evidence/d2-be/D2LA-003F/parallel-store-start.json`; `docs/openclaw-autodev/evidence/d2-be/D2LA-003H/parallel-collection-classification.md` | Store/collection evidence proves 2/5 with real observations/latest DC2; 3/5 not attempted and blocked by enrichment/import readiness. |
| Batch 004 | `docs/openclaw-autodev/evidence/d2-be/D2LA-004B/original-safety-check.md`; `docs/openclaw-autodev/evidence/d2-be/D2LA-004D/error-permission-blockers.md` | Original safety accepted after explicit operator approval; cleanup/destructive boundaries and remaining blockers are explicit. |

## P0 test matrix index

Status values are limited to `PASS`, `BLOCKED`, `NOT RUN`, or `ACCEPTED RISK`.

| P0 row | Status | Evidence / blocker |
| --- | --- | --- |
| DB sample | PASS | D2LA-001 selected 5 real candidates and documented exclusions/type distribution. `batch-001-summary.md` remains TBD, but D2LA-001 is concrete row evidence. |
| Credential refs | PASS | D2LA-001 exports credential refs only as set/unset or hashes; D2LA-002E fresh reconciliation proves the 2 approved clones preserve credential refs without plaintext. |
| Excel generation | PASS | `D2LA-IMPORT/summary.md`: XLSX artifact generated, 5 source rows, 2 import rows, 3 skipped, `labels.d2la_orig_code` present. |
| Login | PASS | Covered by prior D2 real-operation/local smoke evidence and D2LA import/UI handoff evidence; no fresh login rerun in this docs-only story. |
| Import upload | PASS | D2LA-002/D2LA-IMPORT evidence records UI/import upload path and artifact lifecycle for the approved 2-row import. |
| Import validate | PASS | D2LA-IMPORT and `d2la-002d-summary.md` record validation/apply flow; skipped rows are explicit rather than defaulted. |
| Import apply | PASS | D2LA-002E fresh import/apply recovery confirms both approved clones exist and preserve endpoint/protocol/credential refs. |
| Import batch | PASS | D2LA-IMPORT/d2la-002d and D2LA-002E evidence record batch lifecycle for approved rows; batch records retained. |
| Handoff | PASS | D2LA-002 summary states handoff preserves cloned codes/task_id; D2LA-002E fresh batch was uploaded, validated, applied, and handed off through management. |
| Management list | PASS | D2LA-002E read-only reconciliation confirms imported clones present; D2LA handoff evidence covers management search for approved clones. |
| Field reconciliation | PASS | D2LA-002E confirms endpoint/protocol/port and credential refs match for both approved clones; 3 skipped candidates remain separate blockers, not mismatches. |
| Edit | NOT RUN | No Batch 001-004 evidence found for UI edit/update of a cloned `D2LA_*` device. Missing evidence is explicit. |
| Store readiness | PASS | D2LA-002E fresh reconciliation says store readiness restored for approved 2-row D2LA scope; D2LA-003A readiness artifacts exist. |
| Store start | PASS | D2LA-003F/003H evidence records store tasks for the 2 approved clones. |
| Store task summary | PASS | D2LA-003H records task summary for both tasks with `collection_execution.status=dc2_executed`, `dc2_status=success`, and fact counts. |
| Runs | PASS | D2LA-003H records run status/evidence for approved tasks, including one explicit `run status success`; full raw run evidence is in Batch 003 artifacts. |
| Observations | PASS | D2LA-003H: both approved clones have observations endpoint total/list_len = 9/9. |
| Latest DC2 | PASS | D2LA-003H: both approved clones have `latest DC2 found=true` and concrete `dc2_run_id`. |
| Parallel collection start | BLOCKED | 5-device parallel did not run for all 5. D2LA-003H classified only 2/5 as collected; 3/5 were not attempted due to enrichment/import readiness. Human decision required for full-scope launch. |
| Parallel collection classification | BLOCKED | D2LA-003H classifies 2/5 `real-observations-present`, 3/5 `environment-blocked` pending authoritative platform/catalog/rack enrichment. Not auto-PASS. |
| Delete cleanup | NOT RUN | No cleanup/delete evidence found in Batch 001-004. D2LA-004D retains cleanup as an operational/destructive boundary; import batch purge remains disallowed. |
| Original record safety | ACCEPTED RISK | D2LA-004B: 5/5 originals returned; one `DVCE5B9B461254F` platform-code delta was explicitly operator-approved; all other checked fields match. |
| Import Batch retention | PASS | Decisions and D2LA-004D require keeping import batch/task/row records as evidence; no purge was executed. |
| Backend test gate | PASS | D2LA-002E records `go test ./app/device/v2/...` and `go test ./app/device/v2/ingest/...` pass after backend import fix. |
| Error states | PASS | D2LA-004D records concrete P0/P1/P2 blockers and D2LA-IMPORT skipped invalid/unusable rows instead of defaulting; user-facing validation failures are explicit in import evidence. |
| Cleanup report | NOT RUN | No final cleanup report exists; cloned-device deletion was not performed in Batch 001-004. |
| Evidence index | PASS | This file. |
| Page readiness | NOT RUN | `launch-readiness-report.md` has not been produced in D2LA-005A. |
| Launch action lists | NOT RUN | Must-fix/post-launch watch lists belong in the final readiness report and are not yet produced here. |

## Full 5-device sample decision points

| Item | Status | Required human/product action |
| --- | --- | --- |
| Three remaining candidates: `D2LA_DVCAF43808B5905`, `D2LA_DVC862491EB7313`, `D2LA_DVC28EE7B73D8DE` | BLOCKED | Supply authoritative platform/catalog/rack values, approve replacement devices, or explicitly accept reduced 2-device launch evidence as `ACCEPTED RISK`. |
| 5-device parallel collection | BLOCKED | Do not mark PASS unless the remaining 3 are enriched/imported/collected, or a human explicitly accepts the partial 2/5 result as launch risk. |
| Cleanup/delete of cloned devices | NOT RUN | Needs explicit cleanup story/action after evidence retention decision; never delete originals. |

## Missing evidence called out explicitly

- UI edit/update evidence for cloned D2LA devices.
- Delete cleanup evidence for cloned D2LA devices.
- Final cleanup report.
- Final `launch-readiness-report.md`, P0/P1 risk table, must-fix list, and post-launch watch list.
- Full 5-device import/apply/store evidence for the 3 candidates blocked by authoritative platform/catalog/rack enrichment.

## Validation

Docs-only validation. This turn wrote only `docs/prd-autodev/d2-launch-acceptance/evidence-index.md`; no product code changed and no tests were rerun.
