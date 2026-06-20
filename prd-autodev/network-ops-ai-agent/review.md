---
topic: network-ops-ai-agent
kind: full-stack
title: 网络运维智能体融入 OneOPS
createdAt: 2026-06-18T11:00:42+0800
program: true
---

# Logic Review

## P0 Blockers

- None yet

## P1 Risks

- 外部 RAG/Agent 平台能力完整但模型较重，深度嵌入会和 OneOPS 用户、权限、知识库、审计模型重叠。
- 网络运维知识需要混合检索和结构化抽取，仅做向量切片容易漏掉错误码、命令、接口名、设备型号等关键线索。
- 如果缺少统一对象、时序、可信底座，AI 诊断会难以证明“当前回答基于哪批事实”。
- 只读采集工具一旦开放给智能体，也需要命令白名单、审批边界和审计记录。

## P2 Suggestions

- MVP 优先选择告警详情 AI 分析入口，便于天然携带告警、设备、拓扑和时间窗上下文。
- PoC 阶段用 Dify 或 RAGFlow 快速验证知识库与工作流，产品化阶段沉淀 OneOPS 自有 `aiops-service`。
- 首批样例建议覆盖接口 flap、光模块衰减、ACL/策略 deny 激增三个网络/安全典型场景。
- 在 PRD 中明确诊断报告 schema：现象、证据、根因候选、排查步骤、建议动作、缺失证据。
