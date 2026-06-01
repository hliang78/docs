---
topic: secret-hub-frontend-design
kind: frontend
title: SecretHub 前端规划设计
createdAt: 2026-05-28T17:03:32+0800
---

# PRD

## Summary

SecretHub 前端 MVP 是一个独立运行的 SecretHub Console，由 `secrethub/frontend` 承载，直接面向 `secrethub/backend`。它用于管理 Vault provider、规范化 credential catalog、执行受控 secret 更新、查看最近审计，并向 OneOPS 等外部系统提供稳定凭证中枢。

该页面应专业、简洁、克制，优先表现“状态是否可靠”和“动作是否安全”，而不是做成泛后台 CRUD 页面。

## Users

- 平台管理员：配置 Vault provider、检查连接健康、导出兼容 catalog。
- 运维管理员：创建和维护 credential catalog，更新 secret material。
- 审计/排障人员：查看最近 SecretHub 操作和 resolve 事件，不接触明文。

## Goals

- 新建独立 `secrethub/frontend` Console。
- 使用 Vue 3 + Vite + TypeScript + Ant Design Vue 作为 MVP 前端栈。
- 提供 SecretHub provider/catalog/audit 的独立管理入口。
- 让用户无需手写 Vault catalog JSON 即可创建和维护可被外部系统消费的凭证引用。
- 明确 secret material 的安全边界：只允许受控写入，不允许列表/详情明文查看。
- 支持 SecretHub backend 原生 JSON API、独立鉴权策略和独立部署路径。
- 为后续独立运行验证、后端 API 补齐和 UI 实现提供明确切片。

## Non-Goals

- 不嵌入 OneOPS-UI。
- 不依赖 OneOPS 的登录态、菜单、路由、store、API envelope 或后端代理。
- 不实现完整 IAM、RBAC、租户隔离或审批流。
- 不提供明文 secret 查看器。
- 不承诺 provider delete、credential delete、sync preview/apply、referrers 等后端尚未实现功能。
- 不通过自动化开发框架创建 story 或任务。

## Architecture

```text
secrethub/frontend
  standalone SPA
  own router, auth gate, API client, design tokens
  production path: /
        |
        | same-origin session cookie
        v
secrethub/backend
  /healthz
  /api/v1/secrethub/*
  native login/session
        |
        v
Vault / future providers

OneOPS and other systems
  external consumers of SecretHub APIs
```

Production topology is confirmed as same-origin: `/` serves the frontend and `/api/v1/secrethub/*` reaches SecretHub backend. This avoids cross-origin session complexity and keeps service tokens out of browser storage.

## Recommended Repository Layout

```text
secrethub/
  backend/
  frontend/
    package.json
    vite.config.ts
    src/
      api/
        client.ts
        providers.ts
        credentials.ts
        audit.ts
      app/
        App.vue
        router.ts
      components/
      views/
        Overview.vue
        SecretSources.vue
        CredentialCatalog.vue
        AuditTrail.vue
      styles/
        tokens.css
```

## Information Architecture

推荐独立路由：

- `/`：Overview。
- `/sources`：Secret Sources。
- `/credentials`：Credential Catalog。
- `/audit`：Audit Trail。
- `/settings` 或 settings drawer：运行配置和健康信息。

页面由 4 个主区域构成：

- `Overview`：总览状态、异常提示、最近审计。
- `Secret Sources`：Provider 管理和连接测试。
- `Credential Catalog`：凭证目录管理和 secret 更新。
- `Audit Trail`：最近审计记录和脱敏详情。

## Requirements

### R1. Standalone App Shell

- 顶部显示 `SecretHub Console`、当前环境、backend health、认证状态和全局刷新。
- 主导航独立于 OneOPS，支持直接访问和刷新恢复。
- 生产 API 使用同源相对路径 `/api/v1/secrethub/*`；本地开发可用 `VITE_SECRETHUB_API_BASE_URL` 或 Vite proxy 指向 backend。
- 页面保持单层布局，使用 top nav 或 left nav，不做多级复杂导航。
- 空数据、加载中、错误状态都必须有明确文案。

### R2. Auth And Runtime Boundary

- Production 采用 SecretHub native login/session，前端使用同源 session cookie。
- Local dev 可以临时支持一次性输入 API token，并只保存在内存中；该模式不进入生产。
- service token 不得放在 localStorage、源码、静态配置或浏览器长期存储里。
- 401、403、backend offline、session expired、CORS 或 dev proxy 错误需要有独立错误状态。
- Native auth 需要后端补充登录、登出、当前用户/session 状态接口，并明确 cookie、SameSite、过期时间和 CSRF 策略。

### R3. Overview

- 显示 backend health，调用 `GET /healthz`。
- 显示 provider health 摘要，unhealthy/unknown 排在前面。
- 显示 credential status 汇总：`active`、`disabled`、`needs_review`、`orphaned`。
- 显示最近 audit 事件，点击可跳转 Audit tab 并打开详情。
- 显示当前后端限制提示，例如“当前审计为最近 N 条”。

### R4. Secret Sources

- 使用 `GET /api/v1/secrethub/providers` 加载 provider 列表。
- 支持创建 Vault provider：`id`、`name`、`type`、`endpoint`、`namespace`、`default_mount`、`auth_ref`。
- 使用 `POST /api/v1/secrethub/providers` 创建 provider。
- 使用 `POST /api/v1/secrethub/providers/{id}:test` 测试连接。
- 表格展示 `auth_ref` 引用名，不展示真实 token。
- 不展示编辑和删除按钮；后端支持前只显示只读详情。

### R5. Credential Catalog

- 使用 `GET /api/v1/secrethub/credentials` 加载凭证列表。
- 支持筛选：`keyword`、`type`、`usage`、`provider_id`、`provider_type`、`status`。
- 支持创建 credential：`code`、`name`、`type`、`usage`、`provider_id`、`secret_path`、`field_mapping`、`description`、`status`、`tags`、`secret_data`。
- 使用 `POST /api/v1/secrethub/credentials` 创建 credential。
- 支持 metadata 更新，使用 `PUT /api/v1/secrethub/credentials/{code}`。
- 支持 secret 更新，使用 `POST /api/v1/secrethub/credentials/{code}:update-secret`。
- `secret_data` 表单提交成功后必须清空，不在详情、日志、通知中回显。
- 每行提供复制 `credential_ref`，值为 `code`。

### R6. Validate And Compatibility

- 可选提供 `Validate credential_ref` 小工具，调用 `POST /api/v1/secrethub/credentials:validate`，只返回 valid/type/usage/message。
- 可选提供 `Export Vault Index` 入口，调用 `POST /api/v1/secrethub/credentials:export-vault-index`，明确标注“外部系统兼容导出”。
- 不提供普通用户可点击的 `credentials:resolve` 明文入口。
- `material:resolve` 不在前端 MVP 中暴露。

### R7. Audit Trail

- 使用 `GET /api/v1/secrethub/audit?limit=100` 加载最近审计。
- 表格展示 `created_at`、`event_type`、`actor`、`provider_id`、`credential_code`、`subject_type`、`subject_id`、`request_id`、`result`。
- 详情抽屉展示 `message` 和 `metadata`，前端对 `password`、`token`、`secret`、`private_key`、`community` 等 key 做脱敏。
- 当前后端没有分页/筛选时，前端只能做本地轻筛，并在 UI 中标注范围。

### R8. Security UX

- 列表、详情、审计不展示 secret 明文。
- 危险或敏感动作使用独立抽屉，不混在详情里。
- 更新 secret 前展示说明：“提交后不可查看原值，只记录审计”。
- 失败错误不吞掉，展示可行动的信息，但不展示敏感 payload。
- token、secret、private_key、community 等字段不进入 URL、localStorage、日志或通知。

### R9. Responsive And Accessibility

- 桌面优先，支持 1366px 宽度；表格可横向滚动。
- 平板宽度下 Overview 区块改为单列，表格保留核心列。
- 状态不能只依赖颜色，必须有文字 label。
- 表单字段提供 helper text，尤其是 `auth_ref`、`secret_path`、`field_mapping`。

## API Contract

当前 MVP 使用已实现 API：

```text
GET  /healthz
GET  /api/v1/secrethub/providers
POST /api/v1/secrethub/providers
POST /api/v1/secrethub/providers/{id}:test
GET  /api/v1/secrethub/credentials
POST /api/v1/secrethub/credentials
PUT  /api/v1/secrethub/credentials/{code}
POST /api/v1/secrethub/credentials/{code}:update-secret
POST /api/v1/secrethub/credentials:validate
POST /api/v1/secrethub/credentials:export-vault-index
GET  /api/v1/secrethub/audit
```

SecretHub frontend API client 需要直接处理：

- 原生 JSON 响应。
- HTTP status 和 `{error,message}` 错误格式。
- 生产 session cookie 鉴权。
- 本地开发临时 token 模式，支持 `Authorization: Bearer <token>` 或 `X-SecretHub-Token`，但只保存在内存中。
- backend offline、timeout、session expired、dev CORS/proxy 和 unauthorized 状态。

## Visual Design Direction

- Anchor：Swiss。
- Surface：`#F7F7F8`。
- Accent：Yves Klein Blue `#002FA7`。
- Typography：Helvetica Neue、Söhne 或等价 sans。
- Structure：清晰网格、编号分区、1px hairline rules、紧凑表格、右侧抽屉。
- Components：tabs/nav、table、drawer、form、alert、tag、statistic、empty state。
- Copy：短句、工程化、明确动作结果，例如“连接测试失败”“已更新 metadata”“secret 已写入，明文未回显”。

## Implementation Slices

这些切片只作为当前会话规划，不发布到自动化框架。

- Slice 0：补齐 SecretHub native login/session 契约，包括 login/logout/me、cookie、SameSite、过期和 CSRF 策略。
- Slice 1：新建 `secrethub/frontend` Vue 3 + Vite + TypeScript + Ant Design Vue app、设计 tokens、路由和独立 app shell。
- Slice 2：新增 SecretHub API client，默认同源 `/api/v1/secrethub/*`，先接 `healthz`、providers、credentials、audit 只读。
- Slice 3：实现 Overview 和只读表格，覆盖 loading、empty、error、unauthorized。
- Slice 4：Provider 创建和连接测试抽屉。
- Slice 5：Credential 创建、metadata 更新、secret 更新抽屉。
- Slice 6：Audit 详情抽屉、metadata 脱敏和本地筛选。
- Slice 7：兼容导出和 validate 工具，视权限策略决定是否进入 MVP。
- Slice 8：standalone compose 和 UI smoke，确保 frontend/backend 可作为 SecretHub 独立交付物一起运行。

## Acceptance Criteria

- SecretHub Console 可独立运行，不依赖 OneOPS-UI。
- SecretHub frontend 位于 `secrethub/frontend`，采用 Vue 3 + Vite + TypeScript + Ant Design Vue。
- 生产前端与 backend 同域运行，API 使用同源 `/api/v1/secrethub/*`。
- 生产鉴权使用 native session cookie，不在浏览器长期保存 service token。
- 页面能清楚回答“SecretHub 是否健康、有哪些 provider、有哪些 credential、最近发生了什么”。
- Provider 和 credential 列表不出现明文 secret 或 provider token。
- 创建/更新 secret 的表单提交成功后不保留 secret 输入值。
- 后端未实现的能力不会以可点击主操作出现。
- 前端能清楚处理 unauthorized、backend offline、CORS/timeout 和 API error。
- 页面在 1366px 桌面宽度下可读，无大面积无意义空白。

## Risks

- 如果 native session/auth 契约实现不完整，前端可能退回 token 输入模式，必须防止该模式进入生产。
- 如果 audit API 不补分页/筛选，生产数据量下 Audit Trail 只能是最近视图。
- 如果 provider/catalog ownership 没有制度约束，SecretHub 与外部系统导入导出可能发生目录冲突。

## Open Decisions

- 前端静态资源与 backend 是否同容器发布。
- 是否将 `Export Vault Index` 放入 MVP。
- 是否在实现前先补 SecretHub backend 的 audit pagination/filter 和 provider update/delete。
