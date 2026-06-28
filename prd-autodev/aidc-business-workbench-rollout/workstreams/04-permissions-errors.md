---
topic: aidc-business-workbench-rollout
kind: frontend
title: AIDC 全业务页面工作台统一改造
createdAt: 2026-06-25T11:11:00+0800
program: true
---

# Permissions And Error States

## Purpose

统一页面在权限不足、空数据、加载中、接口失败时的工作台表达。

## Findings

- 多个页面依赖 `demo session`。
- `workflows` 有权限门槛。
- 一些页面存在 message focus、详情缺失、接口失败等状态分支。

## Requirements

- 这些状态必须也遵循工作台风格：短信息、明确下一步、不生成大段说明卡。
- 错误态必须准确反映真实后端阻塞。

## Acceptance

- 空态、错误态、权限态不会破坏页面结构。
- 角色无权限时能快速说明下一步。

## Validation

- 浏览器状态验证
- 代码检查

## Candidate Stories

- 嵌入 `AIDCWB-001..007` 的页面状态验证
