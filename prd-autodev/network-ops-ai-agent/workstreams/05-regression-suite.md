---
topic: network-ops-ai-agent
kind: full-stack
title: 网络运维智能体融入 OneOPS
createdAt: 2026-06-18T11:00:42+0800
program: true
---

# Regression Suite

## Purpose

定义网络运维智能体的回归、评测和质量门禁。

## Findings

- AI 能力不能只靠手工体验验收，需要固定样例集和输出结构检查。
- 网络运维场景应重点测证据引用、拒答、缺证据提示、权限隔离和工具调用边界。

## Requirements

- 建立故障样例集：接口 flap、光模块衰减、策略 deny 激增。
- 建立知识库召回样例：错误码、命令、SOP、厂商手册。
- 建立报告结构校验：必须有 summary、evidence、candidates、steps、missing_evidence。
- 建立安全校验：跨租户召回、敏感字段、命令执行拒绝。

## Acceptance

- 每个样例有输入、期望证据、禁用输出、人工评分项。
- 回归结果能保存为证据文件。
- 不通过 P0 样例时不能发布后续自动化故事。

## Validation

- 运行 fixture 测试。
- 人工抽查至少 3 份报告。
- 对比知识召回 top-k 是否包含预期来源。

## Candidate Stories

- 建立 AI 诊断评测样例目录。
- 编写报告 JSON schema 和基础校验脚本。
