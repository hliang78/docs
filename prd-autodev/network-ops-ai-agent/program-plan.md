---
topic: network-ops-ai-agent
kind: full-stack
title: 网络运维智能体融入 OneOPS
createdAt: 2026-06-18T11:00:42+0800
program: true
---

# Program Plan

## Objective

调研并规划“网络运维智能体”如何融入 OneOPS，形成可审阅的架构方向、组件选型、阶段路线和第一批可自动化故事边界。

## Definition Of Done

- 完成本地 OneOPS 现有能力梳理。
- 完成第三方开源组件调研。
- 给出 2 到 3 条集成路线和推荐路线。
- 明确 MVP 范围、非目标、风险和审批边界。
- 在用户确认后，再生成第一批 OpenClaw 自动化故事。

## Scope

### In Scope

- AI 运维问答入口。
- 知识库上传、解析、抽取、检索与引用。
- 告警/日志/设备异常 RCA 辅助分析。
- OneOPS `rca3`、日志、拓扑、设备、采集数据的 AI 编排方式。
- 开源组件选型与接入边界。

### Out Of Scope

- 第一阶段自动执行修复命令。
- 用外部 SoT 替换 OneOPS 设备主数据。
- 用 LLM 替换现有 RCA 计算内核。
- 未经确认发布 OpenClaw 实施故事。

## Workstreams

| ID | Workstream | Lane | Status | Notes |
|---|---|---|---|---|
| 01 | AI 入口与诊断报告体验 | d2-fe | draft | 告警详情入口 vs 独立智能体入口待确认 |
| 02 | AIOps Orchestrator 与工具接口 | d2-be | draft | 意图识别、工具规划、证据聚合、报告生成 |
| 03 | 知识库摄取与 RAG 服务 | d2-be | draft | Dify/RAGFlow PoC 或自研服务边界 |
| 04 | RCA/日志/拓扑证据适配 | d2-be | draft | 接 `rca3`、Loki/Prometheus、Topology Snapshot |
| 05 | 权限、审计、评测与回归 | ct | draft | 租户隔离、证据引用、幻觉检测、样例集 |

## Dependency Map

- 依赖 OneOPS 统一对象底座：设备、接口、Agent、监控目标、拓扑节点 ID 对齐。
- 依赖统一时序底座：collection run、observation batch、processing run、snapshot、change event。
- 依赖统一可信底座：证据质量、来源、冲突、过期状态。
- 依赖知识库权限模型：文档、段落、抽取知识、召回结果均需可追溯。

## Risk Register

| Severity | Risk | Decision Needed |
|---|---|---|
| P0 | LLM 幻觉导致错误排障或误判根因 | 必须规定事实/推断/建议分层和证据引用 |
| P0 | 私有知识或设备日志越权泄露 | 必须确认租户、角色、文档权限边界 |
| P1 | 外部 RAG 平台过重，侵入 OneOPS 产品模型 | 需确认 PoC 与长期内核分离 |
| P1 | 自动命令执行风险 | MVP 是否允许只读 show 命令需确认 |
| P2 | 知识库质量差、过期、冲突 | 需要质量状态和人工反馈机制 |

## Batch Plan

| Batch | Goal | Target Lanes | Status | Gate |
|---|---|---|---|---|
| batch-001 | 产出 OneOPS AI 运维智能体 MVP PRD 和 PoC 组件选择 | d2-be,d2-fe,ct | draft | 用户确认调研方向和 MVP 入口 |
| batch-002 | 实现只读 AI 诊断入口与报告骨架 | d2-fe,d2-be | draft | batch-001 PRD 审阅通过 |
| batch-003 | 接入知识库 PoC 与 RCA/日志证据适配 | d2-be,ct | draft | PoC 组件确认 |

## Approval Boundaries

- Writes outside allowed paths.
- Dependency changes.
- Backend contract or persistence changes without explicit approval.
- Production config, migrations, credentials, auth, tenant logic, deploy, commit, push, merge, PR.
