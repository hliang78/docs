---
topic: aidc-business-workbench-rollout
kind: frontend
title: AIDC 全业务页面工作台统一改造
createdAt: 2026-06-25T11:11:00+0800
program: true
---

# End-to-End Critical Flows

## Purpose

确保页面改造覆盖关键主流程，而不只是停留在视觉整理。

## Findings

- `collections` 的主流程是运行采集、补全重跑、查看任务结果。
- `outreach` 的主流程是筛选任务、查看详情、编辑草稿。
- `radar` 的主流程是筛选、接管、转触达、外部导入。
- `supply` 的主流程是编辑单品和批量导入。
- `workflows` 的主流程是查看待归档队列并回链相关页面。

## Requirements

- 每页至少一个关键用户路径要在证据中出现。
- 深链与筛选参数必须保留。

## Acceptance

- 页面改造后，关键动作仍在首屏或一跳内可达。
- 没有因为重排而破坏 message-center 回链和 URL 参数语义。

## Validation

- 浏览器交互验证
- 页面参数和回链检查

## Candidate Stories

- 主流程验证附着在 `AIDCWB-001..005`
- 最终横向验证附着在 `AIDCWB-007`
