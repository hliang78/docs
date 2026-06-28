---
topic: aidc-business-workbench-rollout
kind: frontend
title: AIDC 全业务页面工作台统一改造
createdAt: 2026-06-25T11:11:00+0800
program: true
---

# Regression Suite

## Purpose

在五个剩余页面落地后，对全部九个业务页做统一回归。

## Findings

- 当前已有四个页面完成工作台化，但尚未与其余页面形成完整统一面。
- 新旧页面在标题区、列表优先级、辅助区位置上可能出现细微断层。

## Requirements

- 检查页面头高度、列表首屏、动作区位置、视觉层级的一致性。
- 必要时做轻量修补，但不重开大范围设计讨论。

## Acceptance

- 九页都能被看作同一套工作台产品面。
- 最终有浏览器证据、测试证据和构建证据。

## Validation

- `cd /Users/huangliang/project/aidc_hunt/apps/aidc-web && pnpm typecheck`
- `cd /Users/huangliang/project/aidc_hunt/apps/aidc-web && pnpm test`
- `cd /Users/huangliang/project/aidc_hunt/apps/aidc-web && pnpm build`

## Candidate Stories

- `AIDCWB-006`
- `AIDCWB-007`
