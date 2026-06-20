---
topic: network-ops-ai-agent
kind: full-stack
title: 网络运维智能体融入 OneOPS
createdAt: 2026-06-18T11:00:42+0800
program: true
---

# Backend API Contracts

## Purpose

定义 AIOps Orchestrator、RAG 服务、RCA 适配器、可观测适配器和设备工具适配器的后端契约。

## Findings

- OneOPS `rca3` 已有 `EvidenceNormalizer`、`LayerDecisionEngine`、`Presenter` 等适合复用的接口边界。
- AI 编排服务应做工具规划和报告生成，不应直接绕过 OneOPS 数据权限。
- 外部 Dify/RAGFlow 可作为旁路 PoC，但 OneOPS 需要自己的稳定 API 层。

## Requirements

- 新增诊断请求契约：alert_id、device_code、time_window、question、context_refs。
- 新增诊断报告契约：summary、evidence、candidates、steps、recommendations、missing_evidence、citations。
- 所有工具调用必须经过权限校验、参数校验、审计记录。
- RAG 召回结果必须包含 doc_id、chunk_id、source、version、score、permission_scope。

## Acceptance

- 后端契约能支持告警详情 AI 分析 MVP。
- RCA 候选和知识库引用在报告中可追溯。
- 未配置外部 RAG 平台时，系统能返回明确能力不可用错误。

## Validation

- 契约 fixture 测试。
- 使用静态样例构造一份诊断报告。
- 权限失败、证据缺失、RAG 不可用三类错误测试。

## Candidate Stories

- 起草 AIOps diagnosis API 契约。
- 建立 `rca3` 诊断 facade 的 fixture。
- 定义 RAG 召回结果标准 DTO。
