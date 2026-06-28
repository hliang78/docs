---
topic: aidc-business-workbench-rollout
kind: frontend
title: AIDC 全业务页面工作台统一改造
createdAt: 2026-06-25T11:11:00+0800
program: true
---

# Frontend Pages And Controls

## Purpose

完成剩余五个业务页的工作台化改造，并为每页提供清晰的列表优先工作节奏。

## Findings

- `collections` 当前仍以概览卡片为起点，任务队列不是绝对主角。
- `outreach` 已有列表、详情、草稿工作区，但页面层级还不够稳定。
- `radar` 已具备列表与详情双区思路，但外部搜索和主操作区优先级仍偏混杂。
- `supply` 是“列表 + 表单 + 导入结果”的典型工作台页。
- `workflows` 更像摘要台，还不够队列优先。

## Requirements

- 每页都采用短头部、主列表、辅助详情/操作区的节奏。
- 保留原有关键主流程和深链。
- 不引入新的展示型 Hero 或卡墙。

## Acceptance

- 五个页面都能被识别为同一产品语言下的工作台页。
- 页面首屏优先看到列表、状态和动作，而不是说明性内容。
- 类型检查和测试通过。

## Validation

- `cd /Users/huangliang/project/aidc_hunt/apps/aidc-web && pnpm typecheck`
- `cd /Users/huangliang/project/aidc_hunt/apps/aidc-web && pnpm test`

## Candidate Stories

- `AIDCWB-001`
- `AIDCWB-002`
- `AIDCWB-003`
- `AIDCWB-004`
- `AIDCWB-005`
