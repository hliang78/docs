---
topic: secret-hub-frontend-design
kind: frontend
title: SecretHub 前端规划设计
createdAt: 2026-05-28T17:03:32+0800
---

# Question Round 001

## Purpose

先在当前 Codex 会话内完成 SecretHub 独立前端规划设计，不通过 OpenClaw、story loop 或其他自动化开发框架推进。

## Answers And Assumptions

- SecretHub 是独立产品，前端和后端都独立于 OneOPS 运行。
- 本轮聚焦 `secrethub/frontend` 独立 Console，而不是 OneOPS-UI 菜单页或 OneOPS 业务侧凭证选择下拉。
- 成功标准是产出可执行的独立页面规划、交互边界、视觉方向、API 依赖、鉴权风险和实现切片。
- 必须不改变 OneOPS 作为外部消费方的定位；OneOPS 后续通过 SecretHub API 消费 `credential_ref`、list、resolve，不承载 SecretHub 管理台。
- 最大风险是独立前端把 SecretHub service token 暴露在浏览器长期存储中，或把 resolve 做成明文查看器。
- 主要用户是平台/运维管理员，主要运行形态是 SecretHub backend + SecretHub frontend 独立部署。

## Planning Assumptions

- 前端目录建议为 `secrethub/frontend`，独立构建、独立路由、独立部署。
- 前端直接面向 SecretHub backend API，不依赖 OneOPS `/api/v1` envelope。
- MVP 只承诺当前 `secrethub/backend` 已实现的 API 能力，不在界面上提供后端尚未支持的删除、同步预演、同步应用、referrer 查询等真实动作。
- UI 不展示任何 plaintext secret；创建和更新 secret 只在表单中一次性输入，提交后即清空，不做详情回显。
- 当前会话只做规划设计和文档沉淀，不发布自动化故事，不创建 OpenClaw 任务。

## Decisions To Confirm

- 推荐路线是 `A. Standalone SecretHub Console`，由 `secrethub/frontend` 承载。
- 已确认前端承载方式采用 `1A`：新建 `secrethub/frontend` 独立 SPA，SecretHub 自己运行。
- 已确认前端技术栈采用 `2A`：Vue 3 + Vite + TypeScript + Ant Design Vue；选择 Vue 是为了复用团队已有经验，不代表依赖 OneOPS-UI。
- 已确认部署拓扑采用 `3A`：前端独立构建，生产同域部署，`/` 给 frontend，`/api/v1/secrethub/*` 反代或直达 SecretHub backend。
- 已确认生产鉴权采用 `4A`：SecretHub backend 增加 native login/session，前端使用 session cookie，不在浏览器长期保存 service token。
- 已确认 `5A`：MVP 不暴露明文 `resolve` UI，只保留 validate 和审计展示。
- 已确认 `6A`：MVP 只做当前 backend 已实现能力，不把未来能力画成可点击主流程。
- “专业、简洁”的视觉方向采用 Swiss control-room：纯净表面、清晰网格、编号分区、少装饰、强状态表达。

## Non-Blocking Open Questions

- SecretHub 独立 Console 的正式访问路径是 `/`、`/console`，还是由网关挂载到 `/secrethub/`。
- OneOPS 是否需要提供跳转到 SecretHub credential 详情的外链；这属于集成体验，不影响 SecretHub 独立运行。
