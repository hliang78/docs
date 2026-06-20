---
topic: network-ops-ai-agent
kind: full-stack
title: 网络运维智能体融入 OneOPS
createdAt: 2026-06-18T11:00:42+0800
program: true
---

# Program Question Round 001

## Purpose

Enrich the rough program input before planning, workstreams, or story batches.

## Questions

1. What is the top-level outcome or release/readiness decision this program should support?
2. Which modules, pages, APIs, roles, environments, or data sets are definitely in scope?
3. Which areas are explicitly out of scope for now?
4. What are the highest-risk flows or failures you are worried about?
5. What evidence should each batch produce before the next batch starts?
6. Which lanes should participate first: frontend, backend, CT, or full-stack?
7. What approval boundaries must automation respect?

## Answers

- 初始用户输入已说明目标：希望在 OneOPS 中融入网络运维智能体，支持自然语言问答、网络/安全设备参数与运维知识库、日志告警/设备异常 RCA、排障步骤、解决方案、私有知识文档自动学习，并可考虑第三方开源平台。
- 当前假设：先做调研分析和方向收敛，不直接进入实现。
- 当前建议：以告警/设备异常 RCA 辅助诊断为 MVP，而不是先做通用聊天入口。

## Context Brief

### Goal

形成 OneOPS 网络运维智能体的调研、候选架构、开源组件选型和后续 PRD 边界。

### Scope

AI 问答、知识库、RCA 辅助、日志/告警/拓扑/设备事实接入、开源组件评估。

### Boundaries

不做自动修复闭环，不让 LLM 替代 RCA 内核，不用外部平台替换 OneOPS 主数据。

### Priority Focus

告警详情 AI 分析、私有知识引用、结构化诊断报告。

### Concerns

权限泄露、LLM 幻觉、知识过期冲突、外部平台侵入、命令执行风险。

### Open Questions

1. MVP 入口优先做告警详情按钮还是独立智能体页面？
2. PoC 优先 Dify 还是 RAGFlow？
3. 是否要求完全本地化模型与知识库？
4. 第一阶段是否允许触发只读 show 命令？
5. 首批故障样例选哪几个？
