---
topic: network-ops-ai-agent
kind: full-stack
title: 网络运维智能体融入 OneOPS
createdAt: 2026-06-18T11:00:42+0800
program: true
---

# Final Readiness

## Summary

- 未达到最终实施 readiness。本阶段只完成调研和方向草案。
- 当前建议方向是：OneOPS 保留事实源/RCA/权限/审计，外部 RAG/Agent 平台先做 PoC，长期沉淀自有 `aiops-service`。

## Residual Risks

- MVP 入口未确认。
- Dify 与 RAGFlow 的 PoC 选择未确认。
- 模型和知识库是否必须本地化未确认。
- 只读设备命令是否允许由智能体触发未确认。
- 首批真实故障样例未确认。
