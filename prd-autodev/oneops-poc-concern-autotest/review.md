---
topic: oneops-poc-concern-autotest
kind: full-stack
title: OneOps PoC 关注方向自动测试闭环
createdAt: 2026-05-14T10:47:34+0800
program: true
---

# Logic Review

## P0 Blockers Before Publishing Batch-001

- None. User confirmed batch-001 scope, DB secret injection boundary, evidence path, and matrix update permission on 2026-05-14.

## Publishing Guardrail

- Batch-001 is reviewed and ready, but should only be published on explicit user instruction.
- 测试 DB 密码不能写入 PRD、story package 或 evidence；必须由环境变量或本机密钥提供。

## P1 Risks

- WS-01 fixture 如果没有稳定 `ONEOPS_GATE_*` 数据，会影响后续监控、日志、拓扑、告警链路。
- 真实设备关闭、真实远程执行、真实 LLM、真实测试凭据写入等动作都已进入 P0 规划，后续 story 必须有恢复策略和风险分级。
- 防火墙推送和真实防火墙测试已明确延后，不能被 batch story 偷偷纳入 P0。
- Agent 卸载/重装如果失败，会阻断后续依赖 Agent 的门禁，需要显式 timeout/retry/recovery。

## P2 Suggestions

- 优先把 WS-07 证据 schema 与 WS-01 batch-001 一起落地，避免后续每批 evidence 格式漂移。
- 每个真实动作 story 都应包含 `precheck -> action -> evidence -> recovery -> matrix update` 五段式 acceptance。
- `test-matrix.md` 的状态建议统一为 `draft/PASS/FAIL/BLOCKED/APPROVAL/SKIPPED`，其中 `draft` 仅用于尚未执行。
