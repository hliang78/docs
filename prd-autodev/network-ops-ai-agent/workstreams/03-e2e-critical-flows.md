---
topic: network-ops-ai-agent
kind: full-stack
title: 网络运维智能体融入 OneOPS
createdAt: 2026-06-18T11:00:42+0800
program: true
---

# End-to-End Critical Flows

## Purpose

定义从用户问题到诊断报告的关键端到端路径。

## Findings

- MVP 应避免泛化多轮聊天，先用固定上下文诊断链路降低不确定性。
- 最小链路需要串起告警、设备、拓扑、日志/指标、知识库、RCA、报告生成。

## Requirements

- Flow A：告警详情 -> AI 分析 -> RCA/知识/日志证据 -> 诊断报告。
- Flow B：设备异常问题 -> 设备上下文解析 -> 知识召回 -> 排查步骤。
- Flow C：上传私有文档 -> 解析/抽取/索引 -> 问答引用。

## Acceptance

- 每条 Flow 都有样例输入、预期输出和证据清单。
- 缺证据、无权限、外部平台不可用时都有可读错误。
- 报告生成过程可审计。

## Validation

- 用接口 flap、光模块衰减、策略 deny 激增三个样例验证。
- 记录每条样例的输入、调用链、输出和人工判断。

## Candidate Stories

- 整理 3 个 E2E 样例 fixture。
- 生成诊断报告验收清单。
