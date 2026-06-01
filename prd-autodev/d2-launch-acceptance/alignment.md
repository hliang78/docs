# Device V2 上线验收 Alignment Draft

UpdatedAt: 2026-05-14T12:20:00+0800
Status: waiting-for-user-alignment-db-derived-real-device

## 发现摘要

1. 已有 D2P2 证据证明本地确定性链路可以跑通。
   - `npm run smoke:d2-real-ops` 覆盖 login、management CRUD、manual ingest、import batch、store/start、store/retry、task evidence。
   - 证据使用 `D2P2_SMOKE_*` 命名空间，属于本地夹具，不等同于真实设备上线验收。

2. 现在真实设备来源已经明确。
   - 当前 Device V2 数据库里的设备就是真实设备。
   - 验收可以从 DB 抽样，导出关键字段和凭证引用，生成入库 Excel，再通过入库工作台真实导入。

3. 凭证必须走引用关系。
   - 前端 ingest contract 已有 `credential_ref_in_band`、`credential_ref_out_band`、`snmp_credential_ref`、`winrm_credential_ref`、`credential_refs`、`access_points[].credential_ref`。
   - OpenClaw story 和证据只允许出现这些引用和协议/端口关系，不允许出现明文 secret。

4. 上线验收最大缺口从“有没有真实设备”变成“如何安全抽样和不污染原记录”。
   - 默认采用 `D2LA_<orig_code>` 克隆导入，真实 endpoint 和 credential refs 仍来自原设备。
   - 同 code update 或删除原始真实设备必须单独批准。

5. destructive 边界必须先确认。
   - exact-code 删除 `D2LA_*` 克隆样本是建议策略。
   - 原始真实设备删除、import batch purge、批量清理都不能默认执行。

## 建议方向

### Direction 1: DB-derived sample gate

先发布一批小 story，只读分析 DB/API 字段、导出映射和凭证引用脱敏规则，产出可执行样本计划。

适合：立刻让 d2-fe/d2-be 继续工作，但不碰 destructive 操作。

### Direction 2: Real import gate

确认抽样和 cleanup 策略后，生成 DB-derived Excel，通过入库工作台上传、校验、提交、handoff，并对清册结果做字段对账。

适合：证明入库工作台和清册管理真实可用。

### Direction 3: Real collection gate

对导入样本触发真实采集，但必须拆成多个小 gate：readiness、start、summary/runs、observations、latest DC2、collection plans、retry decision。没有 observations/DC2 时必须单独分类原因，不能让同一个 worker 一边等待采集一边做全链路排查和最终报告。

适合：真正决定能否上线。

### Direction 4: Go/No-Go report

把 DB-derived import、real collection、edit/delete/cleanup 的证据汇总为上线建议：PASS / BLOCKED / ACCEPTED RISK。

## 建议第一批 Stories（暂不发布）

Batch 001 只做准备和非破坏性验收，但 PRD 已经规划到最终上线报告，不只停在第一轮：

1. `D2LA-001` DB-derived real device sample and redacted export contract。
2. `D2LA-002` Frontend ingest/import template mapping for DB-derived sample。
3. `D2LA-003` Launch acceptance harness plan, with store split into small handoff-driven phases。

等你确认抽样规模、克隆/同 code、采集协议和 cleanup 边界后，再发布 Batch 002 执行真实导入。真实 store 从 Batch 003 开始，但每个 story 只处理一个阶段。

## 整体推进计划

| Batch | 目标 | Story Package |
|---|---|---|
| Batch 001 | DB-derived contract、脱敏规则、导入映射、store 分段计划 | `story-packages/batch-001.json` |
| Batch 002 | 真实 DB 样本导出、生成 Excel、UI 上传/校验/提交、清册对账 | `story-packages/batch-002-import.json` |
| Batch 003 | 真实 store 分阶段采集：readiness/start/summary/runs/observations/DC2/plans/retry | `story-packages/batch-003-store-phases.json` |
| Batch 004 | 清册编辑/修改/删除或保留、原记录安全、错误/权限阻塞项 | `story-packages/batch-004-lifecycle-cleanup.json` |
| Batch 005 | 汇总证据，产出上线 PASS/BLOCKED/ACCEPTED RISK 结论 | `story-packages/batch-005-readiness-report.json` |

执行策略是：PRD 一次性覆盖完整上线验收，OpenClaw 按 batch 和依赖逐步发布，避免 worker 拿到过大的上下文。

## 需要你确认

请回答 `questions.md` Round 001。确认后再把 draft story 包发布到 OpenClaw；当前不会直接启动自动化。
