---
topic: aidc-business-workbench-rollout
kind: frontend
title: AIDC 全业务页面工作台统一改造
createdAt: 2026-06-25T11:11:00+0800
program: true
---

# Backend API Contracts

## Purpose

记录会影响工作台改造和浏览器验证的真实后端阻塞，但不在本 program 内实施后端开发。

## Findings

- 页面已经依赖真实接口。
- 运行期曾出现 `127.0.0.1:18084` 代理错误。
- 这轮目标是前端结构统一，不是扩后端能力。

## Requirements

- 不允许为完成视觉改造而加入 mock、假成功或吞错。
- 所有新的契约缺口都必须写入证据或 review 文件。

## Acceptance

- 页面在接口失败时仍保留清晰工作台骨架。
- 证据中能看出阻塞来自哪里、影响哪一页。

## Validation

- 页面级浏览器验证
- 代码检查与错误态确认

## Candidate Stories

- 嵌入 `AIDCWB-001..007` 的证据记录，不单独发布后端故事。
