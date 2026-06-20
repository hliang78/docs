---
topic: network-ops-ai-agent
kind: full-stack
title: 网络运维智能体融入 OneOPS
createdAt: 2026-06-18T11:00:42+0800
program: true
---

# Frontend Pages And Controls

## Purpose

定义 OneOPS 中网络运维智能体的用户入口和诊断报告展示方式。

## Findings

- MVP 更适合从告警详情页内嵌 AI 分析开始，因为告警天然携带对象、时间窗和严重级别。
- 独立聊天页适合 Phase 2 后承接跨设备、跨知识库、多轮追问，但第一阶段上下文成本更高。
- 前端必须展示证据来源和缺失证据，不能只展示一段自然语言结论。

## Requirements

- 告警详情页提供 AI 分析入口。
- 展示诊断报告：现象摘要、证据、根因候选、排查步骤、建议动作、缺失证据。
- 支持查看引用的知识库片段、日志片段、RCA 候选理由。
- 清晰标识“建议/推断/事实”，高风险动作不提供直接执行按钮。

## Acceptance

- 用户能从一条告警进入 AI 分析。
- 报告中每个关键结论至少能追溯到 RCA、日志、指标、拓扑或知识库来源之一。
- 证据不足时界面显示缺失项，而不是给确定性结论。

## Validation

- 使用 2 到 3 条样例告警手工验收。
- 截图验证报告布局、加载态、失败态、空证据态。
- API mock 下验证字段缺失时前端不崩溃。

## Candidate Stories

- 设计告警详情 AI 分析入口与诊断报告 UI schema。
- 实现 AI 报告只读展示组件和状态处理。
