---
topic: secret-hub-frontend-design
kind: frontend
title: SecretHub 前端规划设计
createdAt: 2026-05-28T17:03:32+0800
---

# Idea

## Original Input

请先对secrethub的前端进行规划设计，要求页面专业、简洁。请在当前codex会话中进行，不要通过自动化框架实现。

## Known Constraints

- 当前会话内规划，不通过 OpenClaw、story loop 或其他自动化开发框架实现。
- 优先规划前端信息架构和视觉/交互方向，暂不写 Vue 实现代码。
- 页面需要专业、简洁，适合 SecretHub 作为密钥中枢的运维控制台。
- SecretHub 完全独立运行，前端和后端都独立于 OneOPS。
- 当前 SecretHub 只有 `secrethub/backend`，需要新增独立 `secrethub/frontend`。
- 前端能力必须尊重当前 backend 已实现 API，不能把未实现能力包装为 MVP 主流程。
- 列表、详情和审计不得展示 plaintext secret 或 provider token。
