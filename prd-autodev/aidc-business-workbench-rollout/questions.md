---
topic: aidc-business-workbench-rollout
kind: frontend
title: AIDC 全业务页面工作台统一改造
createdAt: 2026-06-25T11:11:00+0800
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

- 本 program 的顶层目标是把 `aidc-web` 的九个业务页统一成工作台，并支持后续自动化分批推进。
- 确定在 scope 内的页面是：`companies`、`messages`、`hunts`、`contracts`、`collections`、`outreach`、`radar`、`supply`、`workflows`。
- 当前显式 out of scope：登录页、系统设置页、全局壳层再次重做、后端接口扩展。
- 最高风险流包括：`outreach` 草稿工作区、`radar` 接管/转触达、`supply` 导入链路、`workflows` 归档深链。
- 每个 batch 都需要至少提供代码验证和浏览器/页面证据，后一批再继续发布。
- 首个 lane 只用 `aidc-fe`。
- 自动化必须尊重不改后端、不加依赖、不 commit/push/merge 的边界。

## Context Brief

### Goal

将全部业务页统一成专业、简洁、列表优先的工作台。

### Scope

剩余 5 页改造 + 已完成 4 页一致性回归。

### Boundaries

不改后端，不改登录与系统页，不自动推送代码。

### Priority Focus

先把剩余页工作台化，再做跨页一致性和最终回归。

### Concerns

复杂页面的工作区重排和后端可用性会影响节奏。

### Open Questions

暂无新的阻塞问题。
