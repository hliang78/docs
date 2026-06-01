# WS-07 跨域自动测试证据与回归体系

## Focus

把所有关注方向统一纳入“矩阵 -> 批次 -> evidence -> 下一批”的闭环，避免自动化结果散落在脚本日志里不可复核。

## Repository Anchors

- PRD program: `docs/prd-autodev/oneops-poc-concern-autotest`.
- OpenClaw evidence: `docs/openclaw-autodev/evidence`.
- Existing CT loop: `docs/openclaw-autodev/loops/ct.conf`.

## Draft Acceptance Shape

- 每个故事必须声明矩阵行、验证命令、允许写入路径和证据文件。
- 每批结束后更新 `evidence/batch-###-summary.md`。
- DONE/BLOCKED/APPROVAL 状态要能直接支撑下一批决策。
- 证据摘要使用固定中文格式，方便日报阅读。
- 每批结束后自动回写 `test-matrix.md` 状态。
- 输出一页管理层 readiness 总览。
- 输出机器可读 JSON，支持后续自动判断能否上线。

## Confirmed Planning Decisions

- 证据摘要需要固定中文格式，面向日报阅读。
- 需要生成一页管理层 readiness 总览。
- 每个 batch 结束后要求自动回写 `test-matrix.md` 状态。
- 证据文件统一放在 PRD program 下的 `evidence/`。
- 最终门禁结果需要机器可读 JSON。

## Evidence Artifacts

- `evidence/batch-###-summary.md`: 固定中文格式批次摘要。
- `evidence/batch-###-status.json`: 机器可读批次状态。
- `evidence/readiness-summary.md`: 管理层 readiness 总览。
- `evidence/final-gate-result.json`: 机器可读最终门禁结果。
- `test-matrix.md`: 每批结束后回写状态。

## Status Vocabulary

- `PASS`: 验证通过。
- `FAIL`: 产品或自动化验证失败。
- `BLOCKED`: 环境、fixture、权限、外部依赖阻塞。
- `APPROVAL`: 需要人工审批后才能继续。
- `SKIPPED`: 明确声明暂不覆盖，并记录原因。

## Remaining Open Questions

- 需要定义固定中文摘要模板字段。
- 需要定义 `final-gate-result.json` schema。
- 需要定义 readiness 总览的阈值，例如多少 P0 `FAIL/BLOCKED/APPROVAL` 会判定不可上线。
