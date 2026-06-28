---
topic: aidc-business-workbench-rollout
kind: frontend
title: AIDC 全业务页面工作台统一改造
createdAt: 2026-06-25T11:11:00+0800
program: true
---

# Logic Review

## P0 Blockers

- None yet

## P1 Risks

- `outreach` 和 `radar` 的状态与详情逻辑较重，可能需要后续拆出补充故事。
- 后端接口波动会影响真实浏览器验证，但不应阻止前端结构改造。
- 若共享组件抽象过早，可能拖慢剩余页面落地。

## P2 Suggestions

- 保持“先按页面落地，再做横向收口”的策略。
- 让最终一致性批次专门承担轻量修补，不把它混入首批页面故事。
