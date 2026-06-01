---
topic: oneops-poc-concern-autotest
kind: full-stack
title: OneOps PoC 关注方向自动测试闭环
createdAt: 2026-05-14T10:47:34+0800
program: true
sourceDoc: /Users/huangliang/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/wxid_7323973239612_4510/temp/drag/上海移动研究院自动化运维平台POC测试方案_V1.1(1).docx
---

# Program Context Brief

## Goal

从上海移动研究院自动化运维平台 PoC 测试方案中提取你对 OneOps 平台的核心关注方向，并把这些关注方向转化为 OneOps 自身可持续运行的自动测试/验证闭环。

重要边界：这不是执行该 PoC，也不是按客户现场条件补齐验收材料；PoC 文档只作为关注点输入。

## Background

PoC 文档反映的运维痛点集中在：监控与日志分散、告警噪声高、凭据分散且难审计、例行变更依赖人工、防火墙策略变更链路信息不一致、资产/监控/配置库之间缺少闭环同步。OneOps 当前仓库已经存在多个相关能力面和验证资产，因此适合以“程序化 PRD + 分批 OpenClaw 故事 + 证据回写”的方式推进。

## Extracted Concern Directions

1. 设备与纳管：设备入库、字段完整性、站点/机房/机柜/型号/IP 等基础对象绑定、编码唯一性。
2. 监控与日志：自动发现/采集、指标入库、日志监听/转发、集中监控看板、集中日志检索。
3. 网络拓扑：设备节点、邻接链路、接口/机柜钻取、拓扑快照、采集结果预览与落库。
4. 分布式执行面：集中 OneOps、区域 Controller、区域 Agent 的部署、升级、健康、任务分发与跨安全域通信。
5. 告警管理：告警触发、列表呈现、通知送达、分责订阅/升级、抑制、维护窗口、恢复闭环。
6. 操作安全域：Vault/密钥设施引用式凭据、远程任务不落明文密码、操作日志按人/时间/业务对象检索与导出。
7. 自动化与脚本：模板/变量集驱动巡检、定时任务、AI 辅助脚本草稿、凭证驱动远程试跑、沙箱日志。
8. 防火墙工单：Excel/表格录入、策略解析/对比/生成、推送执行反馈、策略查询与对账。
9. 测试证据体系：每一类能力都需要可复核证据，而不是只看页面可达、HTTP 200 或一次性截图。

## Current Repository Anchors

- Frontend pages/API: `OneOPS-UI/src/views/device`, `OneOPS-UI/src/views/platform`, `OneOPS-UI/src/views/alert`, `OneOPS-UI/src/views/dashboard`, `OneOPS-UI/src/views/firewall`, `OneOPS-UI/src/views/maintenance`, `OneOPS-UI/src/api`.
- Backend modules: `OneOPS/app/device`, `OneOPS/app/device_collection`, `OneOPS/app/device_collection2`, `OneOPS/app/obsflow`, `OneOPS/app/monitor`, `OneOPS/app/topology`, `OneOPS/app/agent`, `OneOPS/app/alert`, `OneOPS/app/alert_engine`, `OneOPS/app/credential`, `OneOPS/app/firewall`, `OneOPS/app/dashboard`.
- Existing validation assets include D2 real-operation smoke, monitoring/log scripts, Platform2 Agent/Controller scripts, Vault catalog smoke, alert RCA smoke, firewall smoke, task-center smoke, and backend Go tests.
- Existing OpenClaw lanes: `d2-fe`, `d2-be`, `ct`. The first automation wave should probably be CT-led discovery/validation, then split FE/BE remediation only after gaps are evidenced.

## Boundaries

- Do not treat the customer PoC as the deliverable.
- Do not require real customer devices, credentials, notification channels, or production firewall access for the first PRD.
- Do not create or publish OpenClaw stories before the PRD direction and first batch are confirmed.
- Do not broaden existing OpenClaw write permissions without explicit approval.
- Do not run destructive operations, migrations, deploys, credential changes, or real external integrations.

## Priority Focus

Confirmed focus for the first exploration slice: device onboarding / monitoring / logging / topology as an online quality gate.

The user allows use of existing OneOPS / OneOPS-UI development services and test database, and wants combination evidence rather than a single evidence type.

## Concerns

- The PoC spans too many domains for one story queue; batching is mandatory.
- Some domains likely need seeded fixture data or controlled test services before meaningful automation is possible.
- A pure UI smoke would be misleading; each direction needs a contract for what evidence counts.
- Existing automation lanes have narrow allowed writes, so remediation work may need separate story batches by lane.
- Although the environment is a test environment, automation should still classify actions as read-only, test-data write, task trigger, or external push so the quality gate is explicit and auditable.

## Open Questions

See `questions.md`.
