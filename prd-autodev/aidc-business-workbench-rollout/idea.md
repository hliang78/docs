---
topic: aidc-business-workbench-rollout
kind: frontend
title: AIDC 全业务页面工作台统一改造
createdAt: 2026-06-25T11:11:00+0800
program: true
---

# Idea

## Original Input

将 aidc-web 所有业务页面统一改造成专业、简洁、列表优先的工作台。当前 companies、messages、hunts、contracts 已完成，剩余 collections、outreach、radar、supply、workflows 需要接入同一工作台语言，并补齐跨页面一致性与回归验证。

## Known Constraints

- 目标是前端业务页统一，不扩展后端能力。
- 自动化任务默认禁用，不自动启用执行。
- 执行过程必须保留真实接口错误，不允许使用 mock 或伪成功掩盖阻塞。
- 不自动 commit、push、merge、发 PR。
