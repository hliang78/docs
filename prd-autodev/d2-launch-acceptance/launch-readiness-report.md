# Device V2 Launch Readiness Report

GeneratedAt: 2026-05-15T08:31+08:00  
Story: D2LA-005B  
Scope: final launch-readiness synthesis from Batch 001-004 evidence and `evidence-index.md`. This report is docs-only: no browser flow, API write, cleanup, import, or product-code change was executed in this story.

## Executive decision

**Recommendation: BLOCKED for full 5-device launch acceptance.**

Device V2 has a proven, production-shaped slice for **2 approved imported `D2LA_*` clones**: import/apply, management handoff, field reconciliation, credential-ref preservation, store start, real observations, task evidence, and latest DC2 evidence are present. However, the intended full 5-device sample is incomplete: **3 candidates remain blocked** by missing authoritative platform/catalog/rack enrichment and were not safely imported or collected.

The launch can move forward only if a human explicitly records one of these decisions:

1. **Fix-before-launch:** provide authoritative enrichment or replacement devices, then rerun import/apply/store/parallel evidence for the missing 3 candidates.
2. **Accepted risk:** explicitly accept reduced 2/5 launch evidence and the unproven full-sample parallel collection scope.

Without that human decision, the correct final status is **BLOCKED**, not PASS.

## Page-level conclusions

| Page | Status | Conclusion |
| --- | --- | --- |
| Device V2 入库工作台 | BLOCKED | The approved 2-row path is proven through Excel/import upload, validate/apply, batch retention, handoff, and field reconciliation. Full launch scope remains blocked because 3/5 rows were skipped for missing authoritative enrichment and the final cleanup/delete report is not complete. |
| 设备 V2 清册管理 | BLOCKED | Management list/handoff, field reconciliation, store readiness, store start, task summary, runs, observations, and latest DC2 are proven for 2 approved clones. UI edit evidence and clone delete cleanup evidence are not present; 5-device parallel collection is incomplete. |

## P0/P1 risk table

| Risk | Priority | Status | Evidence / decision needed |
| --- | ---: | --- | --- |
| Full 5-device sample incomplete | P0 | BLOCKED | 3 candidates (`D2LA_DVCAF43808B5905`, `D2LA_DVC862491EB7313`, `D2LA_DVC28EE7B73D8DE`) lack authoritative platform/catalog/rack enrichment and were not imported or collected. |
| 5-device parallel collection not proven | P0 | BLOCKED | Batch 003 proves real observations/latest DC2 for 2/5 only; remaining 3/5 are environment/enrichment-blocked. Human must either unblock data or accept reduced evidence risk. |
| UI edit/update on D2LA clone not evidenced | P0 | BLOCKED | `evidence-index.md` records Edit as NOT RUN for cloned D2LA devices. Needs before/after persisted detail evidence, or explicit accepted risk. |
| Clone delete cleanup not evidenced | P0 | BLOCKED | Delete cleanup and cleanup report are NOT RUN. Import batch records should be retained, but cloned-device deletion requires a dedicated cleanup story after evidence retention decision. |
| Original record platform-code delta | P0 | ACCEPTED RISK | D2LA-004B records one original-record platform-code delta on `DVCE5B9B461254F` and operator acceptance. |
| Error states and invalid rows | P0 | PASS | Invalid/unusable rows were skipped or surfaced with explicit blockers; no silent defaults or pseudo-success are claimed. |
| Import batch retention | P0 | PASS | Batch/task/row records are retained as evidence; no purge was executed. |
| Permissions / non-admin launch role | P1 | BLOCKED | Test matrix still needs target role decision/evidence. Current launch evidence is admin-oriented. |
| Collection plans / retry decision/execution | P1 | BLOCKED | Required for broader operational confidence but not fully evidenced in Batch 001-004 launch index. |

## Must fix before launch

1. Resolve the 3 blocked sample candidates by supplying authoritative platform/catalog/rack enrichment, choosing replacement devices, or recording a human `ACCEPTED RISK` for reduced 2-device coverage.
2. Produce either 5-device parallel collection evidence or a signed-off accepted-risk note for not proving it.
3. Run and record UI edit/update evidence on cloned `D2LA_*` devices only, or explicitly accept the missing edit evidence risk.
4. Decide clone cleanup timing, then run cleanup/delete evidence for cloned devices only; never delete originals and never purge import batch evidence.
5. Confirm the intended launch role/permission posture beyond `admin/admin@123`, or explicitly scope launch acceptance to admin-only operation.

## Post-launch watch list

1. Watch import validation failures for skipped/enrichment-sensitive platform/catalog/rack fields.
2. Watch store task classifications for `environment-blocked`, `credential-blocked`, `network-blocked`, and `unknown` outcomes.
3. Monitor latest DC2 freshness for the approved clone path and any later replacement devices.
4. Keep import batch/task/row records available for audit and avoid destructive purge until retention policy is confirmed.
5. Track any UI action that remains disabled or pending-contract so it is not mistaken for production-ready functionality.

## Evidence basis

- `docs/prd-autodev/d2-launch-acceptance/evidence-index.md`
- Batch 001 DB-derived sample/export evidence
- Batch 002 Excel/import/handoff/reconciliation evidence
- Batch 003 store readiness/start/task/runs/observations/latest DC2 evidence
- Batch 004 original safety and error/permission blocker evidence

## Final readiness status

**Final status: BLOCKED** until either the missing 3-device evidence is produced or a human explicitly accepts the reduced 2/5 launch evidence risk.

## Validation

Docs-only validation planned for this story: `npm run typecheck:d2` and `/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-d2-runtime.sh ensure-backend`. No product code changed.

Latest worker validation (2026-05-15T12:05+08:00):

- `npm run typecheck:d2` — PASS.
- `/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-d2-runtime.sh ensure-backend` — PASS; backend running from `/Users/huangliang/project/OneOPS-ALL/OneOPS` at `http://127.0.0.1:8080`.
