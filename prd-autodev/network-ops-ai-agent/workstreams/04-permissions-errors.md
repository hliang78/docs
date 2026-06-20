---
topic: network-ops-ai-agent
kind: full-stack
title: 网络运维智能体融入 OneOPS
createdAt: 2026-06-18T11:00:42+0800
program: true
---

# Permissions And Error States

## Purpose

定义 AI 运维智能体涉及的权限、错误、审计和安全边界。

## Findings

- 私有知识、设备日志、告警和拓扑都是敏感数据，不能让外部 RAG 平台绕过 OneOPS 权限。
- 自动工具调用的风险高于普通问答，即使是只读 show 命令也要审计。
- LLM 输出需要明确风险等级，不能把建议动作包装成已执行事实。

## Requirements

- 所有诊断请求必须绑定用户、租户、角色、上下文对象。
- RAG 检索必须按文档权限过滤。
- 设备工具调用必须有白名单、参数模板、审批级别和审计日志。
- 错误状态包括 no_permission、missing_context、rag_unavailable、rca_unavailable、tool_denied、insufficient_evidence。

## Acceptance

- 跨租户文档不会被召回。
- 无设备权限时不能查看设备日志或生成包含该设备事实的报告。
- 证据不足时报告给出缺口，不输出确定根因。

## Validation

- 租户隔离测试。
- 角色权限测试。
- 外部平台不可用和工具拒绝测试。

## Candidate Stories

- 定义 AI 诊断权限矩阵。
- 定义诊断错误码和审计事件。
