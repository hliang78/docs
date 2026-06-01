---
topic: secret-hub-frontend-design
kind: frontend
title: SecretHub 前端规划设计
createdAt: 2026-05-28T17:03:32+0800
---

# Context Brief

## Goal

为独立运行的 SecretHub 设计专业、简洁、可实现的前端 Console，明确信息架构、视觉方向、交互边界、API 依赖、鉴权策略和后续实现切片。

核心目标不是嵌入 OneOPS，而是让 SecretHub 自己成为可靠的密钥控制台：能看清来源健康、凭证目录、敏感更新动作和审计痕迹，同时不泄露明文。

## Boundaries

- 本轮只做当前 Codex 会话内的规划设计，不使用 OpenClaw 或自动化开发框架。
- SecretHub 前端和后端均独立于 OneOPS 运行，规划目标是 `secrethub/frontend` 独立应用。
- 不开始写 Vue 页面、API client 或构建配置，除非后续用户明确要求进入实现。
- 不设计超出当前后端能力太远的 MVP 操作；路线图能力可以标注，但不能混进验收范围。
- 不展示、复制、下载任何 secret 明文。

## Focus

- 第一优先级：独立 SecretHub Console 的信息架构和 MVP 页面范围。
- 第二优先级：独立运行所需的 API base URL、鉴权/session、部署路径和环境配置边界。
- 第三优先级：安全交互边界，包括创建/更新 secret、resolve/handle、审计详情的展示规则。
- 第四优先级：后续可实现切片，让开发可以按小步交付。

## Background

- `secrethub/backend` 已存在，并提供第一批文件存储后端、Vault KV v2 provider、credential catalog、resolve/material handle 和 audit API。
- `secrethub/frontend` 当前不存在，需要新建独立前端。
- SecretHub backend 当前返回原生 JSON，不是 OneOPS API envelope。
- OneOPS 是 SecretHub 的外部集成方，后续可以消费 SecretHub 的 list/resolve/validate，但不承载 SecretHub 管理界面。
- quick_env 是 OneOPS 平台快速部署环境，不作为 SecretHub 默认测试、交付或运行路径。
- SecretHub 本身使用独立 backend/frontend、本地同源 compose 和生产 compose 做验证；OneOPS 后续接入时再在 OneOPS 侧验证集成链路。
- 2026-05-28 已确认 SecretHub 独立运行边界：不嵌入 OneOPS compose，不依赖 OneOPS UI，不把 quick_env 作为 SecretHub Console 的入口。

## Concerns

- SecretHub 独立前端如果直接暴露 `resolve` 能力，容易把运维控制台变成明文查看器；MVP 应避免。
- 当前 SecretHub 后端缺少 provider update/delete、credential delete、sync preview/apply、referrers 和审计分页搜索，页面必须避免出现“看似可用但实际不可用”的按钮。
- 当前 backend 只有 service-level API token；生产已确认走 SecretHub native login/session，浏览器不得长期保存 service token。
- 独立前端生产同域部署，`/` 服务 frontend，`/api/v1/secrethub/*` 访问 backend；本地开发仍需处理 API base URL、CORS 或 Vite dev proxy。
- Vite 本地首页请求要模拟浏览器 `Accept: text/html`；`Accept: application/json` 访问 `/` 会返回 404，这是 Vite fallback 行为，不代表 SecretHub Console 不可访问。

## Open Questions

- 前端是否随 backend 同容器发布，还是独立 Nginx/静态站点发布。
- 审计列表是否需要后端先补分页、筛选和按主体查询；如果不补，前端只能做最近 N 条展示。
