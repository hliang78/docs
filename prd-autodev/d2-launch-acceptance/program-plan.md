# Device V2 上线验收测试闭环 Program Plan

UpdatedAt: 2026-05-14T21:21:25+0800
Status: automation-linked-in-progress

Automation Sync: `evidence/automation-sync.md`

## Objective

在 Device V2 入库工作台和设备 V2 清册管理上线前，形成可回放、可审计、可清理的验收证据，证明：

- 可从当前 Device V2 数据库抽取真实设备样本，脱敏导出关键字段和凭证引用。
- 真实设备样本可以被转成入库工作台 Excel，并通过 UI 重新导入到 Device V2 清册。
- 清册管理可以对导入样本进行查看、搜索、编辑、修改、删除或受控保留。
- store/start 可以基于导入样本真实驱动采集，且证据抽屉能展示 task、runs、observations、collection plans、latest DC2 或明确业务空态。
- Import Batch 生命周期可以创建、上传 Excel、validate、apply、retry，并能解释失败。
- 前后端错误、权限、空态、禁用态和清理策略清楚，不存在 mock success 或 page-local-only success。

## Definition Of Done

- 验收矩阵中 P0 场景全部 `PASS` 或有用户确认的 `ACCEPTED RISK`。
- 完成一次 DB-derived real-device round trip：DB 抽样 -> 脱敏导出 -> Excel -> UI 导入 -> 清册对账 -> 真实采集 -> 证据归档。
- 所有 P0 操作都有证据文件：页面文本、截图、关键网络请求、响应摘要、console 结果、后端测试或日志引用。
- 真实设备采集验收至少覆盖 1 台 DB 抽样设备；如 observations/DC2 为空，必须判断为业务空态、设备不可达、凭证问题或采集链路问题。
- 所有测试数据有 cleanup 结论：已删除、保留并标记、或不能删除的原因。
- 不导出、不记录、不提交明文凭证或 secret material。
- 不以截图、HTTP 200、页面标题、typecheck 作为唯一完成标准。

## In Scope

- DB 只读抽样：从当前 Device V2 数据中选择真实设备样本。
- 脱敏导出：设备关键字段、管理地址、协议、端口、凭证引用、access points、主数据映射。
- Device V2 入库工作台：Excel 上传、手工新增、提交基础入库、任务结果、管理页跳转。
- Device V2 清册管理：列表、详情、创建、编辑、删除、搜索/keyword handoff、任务证据抽屉。
- Import Batch 生命周期：create/upload/validate/apply/retry/summary/records。
- store/start 和 store/retry：真实 task 创建、summary/runs/observations/plans/latest DC2 证据。
- 错误语义：后端 `code:-1`、业务空态、权限/凭证/网络不可达、删除失败、导入校验失败。
- 数据隔离：默认以 `D2LA_<orig_code>` 生成克隆样本，保留 `orig_code` 映射，避免直接覆盖原生产记录。

## Out Of Scope Until Approved

- 正式生产数据批量导入。
- 明文凭证导出、明文密码写入 Excel、日志或 OpenClaw evidence。
- 原始真实设备记录的删除、批量 purge 或未经快照的同 code 更新。
- 大范围 saved-view/source/collection facets、监控跳转、V1 sync、credential binding、change-history 工作流扩展。
- 新依赖、生产配置、迁移、提交/推送/部署。

## Workstreams

| Workstream | Lane | Purpose |
|---|---|---|
| WS1 DB sample and redacted export | d2-be + d2-fe | 只读识别真实 Device V2 样本，定义导出字段、凭证引用和脱敏证据格式。 |
| WS2 DB-derived Excel import | d2-fe | 生成入库模板 Excel，通过 UI 上传、校验、提交并记录 handoff。 |
| WS3 Backend contract/test gate | d2-be | 复核 route/DTO/service/test，保证抽样、导入、采集证据问题可定位。 |
| WS4 Real collection evidence | d2-fe + d2-be | 采集由 controller detect 机制决定；先 1 台打通，再 5 台并行采集。分段验证 store readiness、store/start、task polling、runs、observations、plans、latest DC2，不把完整采集闭环放进一个 worker turn。 |
| WS5 Edit/delete/cleanup policy | d2-fe + d2-be | 克隆样本编辑/修改并在验收后全部删除；原始真实设备禁止删除；Import Batch 不 purge，作为验收证据保留。 |
| WS6 Launch readiness report | d2-fe | 汇总证据、风险、go/no-go 建议。 |

## Store Granularity Rule

真实采集链路上下文重、耗时长，不能写成一个粗粒度 story。store 相关 story 必须遵守：

- 每个 worker turn 只处理一个明确阶段：readiness、start、task summary、runs、observations、collection plans、latest DC2、retry、classification、report 之一。
- 第一轮 store 只处理 1 台设备；单设备路径证明后，允许发布专门的 5 台并行采集 story，但仍然按 start、polling、classification 分阶段。
- store story 不指定采集协议；必须准备好 credential refs、access_points、endpoint、协议/端口提示和 metadata，让 controller detect 机制决定采集方式。
- 后续 story 只能读取上一阶段的 compact handoff 文件，例如 `sample-set.json`、`store-task-id.txt`、`store-summary.json`、`store-observation-classification.md`。
- 不能要求 worker 在同一 story 内同时做 UI 导入、真实采集、异常排查、retry 和最终报告。
- 如果 task 轮询超过单 turn 时间预算，story 必须写入当前 `task_id`、最近状态和下一步轮询命令，然后结束为 `CONTINUE` 或 `BLOCKED`。

## Dependency Map

- WS1 read-only DB/API access is approved. It should select 5 real Device V2 records, preferably 1 per device type, and export credential references only.
- WS2 depends on WS1 exported sample and import template mapping.
- WS2 import must use the Device V2 入库工作台 upload UI. Upload/validate is a first-class acceptance step; apply runs only after validation succeeds or expected validation failures are documented.
- WS3 may run `go test ./app/device/v2/...` and `go test ./app/device/v2/ingest/...`, and may make small fixes inside Device V2 backend paths when DB-derived acceptance exposes contract gaps.
- WS4 depends on reachable device endpoints and valid credential references in the existing credential system. Protocol selection is delegated to controller detect.
- WS5 cleanup is confirmed: exact-code delete all `D2LA_*` cloned devices after evidence; never delete original real records; do not purge import batches.
- WS6 depends on WS1/WS2/WS3/WS4/WS5 evidence. It may report P0 `ACCEPTED RISK`, but partial 5-device parallel collection failures require human PASS/BLOCKED/ACCEPTED RISK decision.

## Risk Register

| Risk | Severity | Why It Matters | Mitigation |
|---|---:|---|---|
| DB sample lacks credential refs or access points | P0 | Cannot prove real collection even if import works. | Sample only devices with usable management endpoint and credential refs; record exclusions. |
| Credential secrets leak into evidence | P0 | Security incident risk. | Export refs only; mask values; evidence review forbids plaintext secret fields. |
| Store/start returns task but no observations | P0 | May prove orchestration but not real collection. | Treat explicit business-empty as blocker unless user accepts. |
| Reimport overwrites real records | P0 | Production data mutation risk. | Default clone code `D2LA_<orig_code>`; same-code update requires approval and snapshot. |
| Deletion/purge could affect real assets | P0 | Data loss risk. | Exact-code cleanup only for cloned samples unless explicit approval. |
| Import batch applies partial/failed rows | P1 | Launch users need repair semantics. | Include invalid row and retry path in matrix. |
| Permission mismatch between admin and real operators | P1 | Admin-only pass may hide launch issue. | Confirm target role or include operator-role check. |

## Batch Plan

The PRD covers the full launch acceptance program. Reviewed packages are now wired to the OpenClaw story queue as dependency-chain stories; the scheduler may receive the whole reviewed chain, but execution remains gated by `dependsOn` so later cleanup and readiness stories cannot run before store and lifecycle evidence exists.

| Batch | Purpose | Primary Output | Publish Condition | Completion Gate |
|---|---|---|---|---|
| Batch 001 | DB-derived contract and harness preparation | sample/export contract, frontend mapping, store phase plan | user confirms DB-derived direction | safe plan exists; no plaintext secret path |
| Batch 002 | DB sample export and real import through UI | `sample-set.json`, DB-derived xlsx, import task evidence, reconciliation report | Batch 001 complete and sample/cleanup policy confirmed | imported cloned records reconcile with source sample |
| Batch 003 | Fine-grained real store collection | readiness/start/task/runs/observations/DC2/plans artifacts | Batch 002 imported sample exists and collection protocol approved | collection evidence classified for at least 1 device |
| Batch 004 | Management lifecycle and cleanup | edit/delete/retain evidence, original-record safety check, error/permission notes | Batch 002 complete; destructive boundary confirmed | cloned samples handled; originals safe |
| Batch 005 | Launch readiness decision | go/no-go report and residual risk list | Batches 001-004 have evidence or accepted blockers | user can decide launch/pass/block/accepted risk |

Current queue linkage:

- Reviewed package story count: 26.
- OpenClaw linked reviewed stories: 26.
- Active reviewed stories remaining: 18.
- Draft/not-reviewed addendum: `batch-001-backend-contract-addendum.json` remains intentionally unpublished unless Batch 001 evidence shows the backend addendum is still needed.
- Final readiness is pending until Batch 003-005 evidence is produced and indexed.

### Batch 001: contract and harness preparation

Analysis/verification only and non-destructive:

1. Build a DB-derived launch acceptance inventory: identify Device V2 DB/API fields, credential reference fields, import template mapping, and sample selection criteria.
2. Produce a redacted sample export plan and evidence schema. Do not export plaintext secret values.
3. Confirm the sample contract selects 5 records, 1 per device type where available, using only read-only DB/API access.
4. Produce a go/no-go prereq report for real import and real collection.

Planned story package: `story-packages/batch-001.json`.

### Batch 002: DB sample export and real import

Runs after user confirms sample/cleanup policy:

1. Read-only export of 5 DB sample records into a redacted `sample-set.json`.
2. Generate DB-derived Excel using cloned `D2LA_<orig_code>` codes and `labels.d2la_orig_code` original-code mapping.
3. Run UI upload/validate as a standalone acceptance phase.
4. Apply only validated rows, or stop and document expected validation failures for intentionally incomplete rows.
5. Compare imported records with original DB sample key fields.

Planned story package: `story-packages/batch-002-import.json`.

### Batch 003: real store collection, fine-grained

Starts real collection, but only one narrow phase at a time:

1. `003A` store readiness gate for selected cloned sample.
2. `003B` store/start only: trigger collection and persist `task_id`.
3. `003C` task summary/runs polling only.
4. `003D` observations/latest DC2 evidence classification only.
5. `003E` collection plans and retry decision only, if needed.
6. `003F-003H` after single-device path passes, run 5-device parallel start/poll/classification in separate stories.

Planned story package: `story-packages/batch-003-store-phases.json`.

### Batch 004: management lifecycle and cleanup

Runs after import evidence exists and destructive boundaries are explicit:

1. Edit/update cloned sample and verify persistence.
2. Verify original DB sample remains safe.
3. Delete all cloned samples after evidence is captured.
4. Capture operator permission and negative/error cases that affect launch.

Planned story package: `story-packages/batch-004-lifecycle-cleanup.json`.

### Batch 005: final readiness decision

Closes launch acceptance:

1. Read all evidence summaries from Batches 001-004.
2. Produce a go/no-go table for every P0 matrix item.
3. List residual risks as `PASS`, `BLOCKED`, or `ACCEPTED RISK`.
4. State separate conclusions for Device V2 入库工作台 and 设备 V2 清册管理.
5. Include "must fix before launch" and "post-launch watch list".

Planned story package: `story-packages/batch-005-readiness-report.json`.

## Launch Acceptance Harness Artifacts And Handoffs

All Batch 002-004 evidence is written under `docs/openclaw-autodev/evidence/d2-fe/D2LA-IMPORT/` or `docs/openclaw-autodev/evidence/d2-fe/D2LA-STORE/<device-code>/`. Files must be compact, redacted, and reusable by the next worker turn. D2P2 local fixture smoke remains a fallback health gate only; it can prove the local UI/backend harness is alive, but it is not real-device launch proof.

### Batch 002 import artifacts

| Phase | Required artifacts | Purpose | Stop/hold condition |
|---|---|---|---|
| DB sample export | `sample-set.json`, `sample-selection.md`, `redaction-checklist.md` | Carries source candidates, original code mapping, endpoint/access point presence, credential-ref names/ids/roles only, and selection/exclusion reasons. | Missing credential refs, no reachable endpoint/access point, plaintext secret present, or sample policy not approved. |
| Excel generation dry-run | `db-derived-import.xlsx`, `import-mapping.json`, `template-field-support.md` | Confirms cloned `D2LA_<orig_code>` rows match ingest template before any UI upload. | Unsupported required template field, accidental same-code overwrite risk, or plaintext secret would be written. |
| UI upload/validate | `upload-validation.json`, `upload-network.har.json` or compact request/response JSON, `upload-validation-screenshot.png`, `validation-row-errors.json` | Proves the real ingest UI accepts/rejects DB-derived rows explicitly before apply. | Core cloned rows fail unexpectedly, upload contract mismatch, auth/session failure, or validation result is unavailable. |
| Import apply/handoff | `import-task.json`, `import-result.json`, `imported-codes.txt`, `management-handoff.json`, `management-list-network.json` | Applies only validated rows and records the management route/list evidence for exact cloned codes. | Apply before validation, missing task/result id, no management handoff, or any attempt to overwrite original records without approval. |
| Management reconciliation | `reconciliation.md`, `ready-for-store.json`, `source-vs-imported-fields.json` | Compares imported cloned records with source samples and selects the next store candidate. | Endpoint/protocol/credential-ref mismatch, imported code absent, unexplained field drift, or readiness data missing. |

### Batch 003 fine-grained store handoffs

| Phase | Input handoff | Output handoff/evidence | Worker-turn boundary | Stop/hold condition |
|---|---|---|---|---|
| `003A` readiness | `sample-set.json`, `imported-codes.txt`, `ready-for-store.json` | `D2LA-STORE/<device-code>/readiness.json`, `readiness-network.json`, optional `readiness-screenshot.png` | Check exactly one selected cloned device; do not start store. | Missing credential refs, missing/unreachable endpoint, permission/API error, or readiness response blocks controller detect. |
| `003B` start | `readiness.json` | `store-start.json`, `store-task-id.txt`, start request/response with secrets redacted | Trigger store/start once for the readiness-passed device; persist only the returned task id. | No `task_id`, UI/API start error, long synchronous request, or wrong/original device code. |
| `003C` summary/runs | `store-task-id.txt` | `store-summary.json`, `store-runs.json`, `task-polling-note.md` | Poll/load summary and runs only, with bounded waiting. | Task remains long-running near budget, summary/runs endpoint unavailable, or failed task needs classification before retry. |
| `003D` observations/latest DC2 | `store-summary.json`, `store-runs.json`, `ready-for-store.json` | `store-observations.json`, `latest-dc2.json`, `collection-classification.md` | Classify evidence only; do not retry/start/edit. | Empty observations/DC2 without business-empty explanation, backend contract gap, credential/network/environment blocker, or unknown state. |
| `003E` collection plans/retry decision | prior store artifacts | `collection-plans.json`, `retry-decision.md` | Decide retry/no-retry; execute retry only when clearly safe and authorized by current story. | Retry would mask missing credentials, task is still running, destructive side effect unclear, or human approval required. |
| `003F+` parallel start/poll/classify | single-device pass artifacts + confirmed 5-device sample | `parallel-store-start.json`, `parallel-store-status.json`, `parallel-collection-classification.md` | Split start, polling, and classification into separate stories. | Single-device proof absent, user has not approved broader collection, or global environment outage. |

### Batch 004 lifecycle/cleanup artifacts

- Edit/delete evidence must use exact cloned `D2LA_*` codes only: `edit-before.json`, `edit-after.json`, `delete-results.json`, `post-delete-list.json`.
- Original-record safety must be explicit: `original-record-safety.md` and a redacted before/after snapshot proving source records still exist.
- Import Batch records are retained as evidence: write `import-batch-retention.md`; do not purge batches.
- Cleanup stops if exact cloned-code matching is ambiguous, delete would touch original records, backend denies delete, or human approval is needed for any destructive action outside cloned sample cleanup.

## Stop Conditions

- A task needs plaintext credentials in prompt, docs, Excel, logs, or evidence.
- DB sample has no reachable endpoint or usable credential reference.
- Any destructive action outside exact cloned sample cleanup is required but not approved.
- Backend returns concrete contract failure that needs product/API decision.
- Backend validation depends on real DB/external collection infrastructure and is blocked by environment; classify as `environment-blocked` and stop the current story.
- UI enables an operation that cannot be proven by network/backend evidence.
- 5-device parallel collection partially fails and no human has accepted PASS/BLOCKED/ACCEPTED RISK classification.
