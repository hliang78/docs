---
topic: network-ops-ai-agent
kind: full-stack
title: 网络运维智能体融入 OneOPS
createdAt: 2026-06-18T11:00:42+0800
program: true
---

# Alignment

## Program Decisions

- 推荐路线：OneOPS 自己保留事实源、RCA 合约、权限和审计；外部开源平台优先作为 RAG/Agent PoC 或旁路服务。
- 推荐 MVP：从“告警详情 AI 分析 + 私有知识引用 + RCA 解释报告”开始，而不是先做全局聊天机器人。
- 推荐技术边界：LLM 做解释、检索、追问和报告；根因候选由 OneOPS `rca3`/证据适配器输出。
- 推荐组件 PoC：Dify 或 RAGFlow 二选一；向量/混合检索优先 Qdrant 或 OpenSearch；设备工具优先复用 OneOPS netlink/adapter。

## Batch Decisions

- batch-001 暂不发布自动化故事，等待用户确认 MVP 入口、PoC 平台、模型部署和是否允许只读采集。
- 第一批故事应只覆盖 PRD、接口契约和 PoC 验证，不直接改生产主链路。
