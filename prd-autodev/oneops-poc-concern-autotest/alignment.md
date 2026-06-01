---
topic: oneops-poc-concern-autotest
kind: full-stack
title: OneOps PoC 关注方向自动测试闭环
createdAt: 2026-05-14T10:47:34+0800
program: true
---

# Alignment Draft

## Program Direction

采用“完整 PRD 规划 + workstream 逐步深入 + 小批次 OpenClaw 自动化”的路径。

当前 7 个 workstream 均已完成第一轮用户确认：

| Workstream | P0 Direction |
|---|---|
| WS-01 设备/监控/日志/拓扑 | 4 个独立上线子门禁，使用 `ONEOPS_GATE_*` 长期 fixture 和组合证据。 |
| WS-02 Agent/Controller | 单 Controller/Agent 链路，真实生命周期动作，真实最新安装包，卸载后重装恢复。 |
| WS-03 告警闭环 | 真实关闭测试设备触发告警，send log 作为通知证据，超时升级到上一级人员。 |
| WS-04 凭据与审计 | 真实写入测试凭据，真实远程执行，验证轮换/禁用、不暴露明文和审计。 |
| WS-05 自动化工作台 | 模板、变量集、定时、任务执行、脚本试跑、真实 LLM AI 辅助。 |
| WS-06 防火墙工单 | 工单导入、对象解析、预检查、CLI 推荐配置、策略查询/对账；推送和真实防火墙延后。 |
| WS-07 证据体系 | 固定中文摘要、矩阵回写、管理层 readiness、机器可读门禁 JSON。 |

## First Batch Recommendation

建议第一批仍从 WS-01 开始，但不要直接执行完整设备/监控/日志/拓扑门禁。第一批应该先做 **设备字段门禁基线准备**，因为它是后续监控、日志、拓扑和告警的对象基础。

Batch-001 建议目标：

- 从测试 DB 读取 `ONEOPS_GATE_*` fixture inventory。
- 基于 `D2_INGEST_BASE_FIELD_TABLE.md`、采集证据和平台字段，生成每台设备自己的最大可验证字段 manifest。
- 明确 Device V2 / DC2 / UI 证据入口。
- 建立固定中文摘要和机器可读 JSON 的第一版证据格式。

## Why Not Publish Broadly Yet

- 多数 workstream 已有清晰 P0 方向，但仍缺执行级 fixture、命令白名单、安装包位置、LLM 配置、send log 查询入口等细节。
- 这些细节适合作为 story 内探索输出，不适合在未确认的情况下批量启动真实 apply、远程执行或设备关闭。
- 第一批如果先把 WS-01 对象基线和 WS-07 证据格式打稳，后续每个门禁都能复用同一套 fixture 和 evidence contract。

## Decisions Still Needed

发布 batch-001 前已确认：

1. batch-001 只做 WS-01 设备字段门禁基线准备，而不是同时推进全部 4 个 WS-01 子门禁。
2. batch-001 允许只读访问测试 DB，但不把 DB 密码写入 story/package。
3. batch-001 写入 PRD program 下的 `evidence/` 和回写 `test-matrix.md`。

Status: ready to publish on explicit user instruction.
