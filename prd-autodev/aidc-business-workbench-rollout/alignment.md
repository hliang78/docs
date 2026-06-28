---
topic: aidc-business-workbench-rollout
kind: frontend
title: AIDC 全业务页面工作台统一改造
createdAt: 2026-06-25T11:11:00+0800
program: true
---

# Alignment

## Program Decisions

- 这轮工作是一个前端长任务，不是单次小修。
- 程序目标是“剩余页面改造 + 已完成页面一致性回归”，而不是只完成某一个页面。
- 统一延续 `AIDC Workbench Shell Redesign` 的冷静蓝灰、紧凑专业、短标题区原则。
- 新建专用 OpenClaw 任务 `aidc-fe`，默认保持禁用态。

## Batch Decisions

- `batch-001` 先覆盖 `collections`、`outreach`、`radar`，并直接进入任务队列。
- `batch-002` 预留给 `supply`、`workflows`。
- `batch-003` 用于九页一致性回归和最终验证。
