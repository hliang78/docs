---
topic: secret-hub-frontend-design
kind: frontend
title: SecretHub 前端规划设计
createdAt: 2026-05-28T17:03:32+0800
---

# Alignment

## Proposed Direction

推荐采用 **A. Standalone SecretHub Console**。

SecretHub 前端应作为 `secrethub/frontend` 独立应用运行，直接面向 SecretHub backend，而不是嵌入 OneOPS-UI。OneOPS 是外部消费方，可以通过 API 或外链与 SecretHub 集成，但 SecretHub Console 自己拥有路由、鉴权、布局、错误处理和部署边界。

部署与鉴权已确认：生产采用同域部署，`/` 服务 frontend，`/api/v1/secrethub/*` 访问 backend；生产鉴权采用 SecretHub native login/session 和 session cookie。

设计语言选择 **Swiss**：表面使用中性 `#F7F7F8`，字体使用 Helvetica Neue、Söhne 或同类干净 sans，主强调色使用 Yves Klein Blue `#002FA7`，结构依赖 1px hairline rules、左对齐和编号分区。这个方向足够专业、简洁，也不会滑向普通 SaaS 后台的模板感。

核心模块：

- `Overview`：来源健康、目录规模、异常状态、最近审计。
- `Secret Sources`：Provider 列表、创建 Vault provider、测试连接。
- `Credential Catalog`：凭证目录、筛选、创建、metadata 更新、secret 更新。
- `Audit Trail`：最近审计、按 event/result/provider/credential 做前端轻筛，详情抽屉脱敏展示 metadata。
- `Runtime Settings`：API base URL、当前环境、鉴权状态、backend health，只放必要运行信息。

## Wireframe

```text
SecretHub Console                                            env: standalone
Independent secret control plane                     backend: http://host:8080

[ API Health: OK ] [ Providers 3 / unhealthy 1 ] [ Active Credentials 128 ] [ Recent Audit 24h ]

01 Overview   02 Secret Sources   03 Credential Catalog   04 Audit Trail
──────────────────────────────────────────────────────────────────────────────
OVERVIEW

Source Health                         Credential Inventory
──────────────────────────────        ───────────────────────────────────────
vault-prod      active                active        118
vault-dev       unhealthy             needs_review  6
vault-lab       unknown               disabled      3

Recent Audit
──────────────────────────────────────────────────────────────────────────────
17:12  credential.secret_updated   vault_linux_ops   success
17:08  provider.tested             vault-prod        failed

右侧抽屉用于 create/update/test/detail，敏感动作只在抽屉内二次确认。
```

## Page Model

### App Shell

- 独立顶栏：产品名、当前环境、backend health、当前认证状态。
- 主导航：Overview、Secret Sources、Credential Catalog、Audit Trail。
- 可选 Settings 抽屉：展示 API base URL、版本号、healthz、auth mode，不承载业务配置。
- 页面不依赖 OneOPS layout、Pinia store、route guard 或 API envelope。

### Overview

- 顶部只放 4 个关键状态，不堆叠大仪表盘。
- Provider health 使用可扫描列表，突出 unhealthy/unknown。
- Credential inventory 按 status 汇总，`needs_review` 和 `orphaned` 明显但不刺眼。
- Recent audit 展示最近动作，点击进入审计 tab 并打开详情。

### Secret Sources

- 表格字段：`id`、`name`、`type`、`endpoint`、`namespace`、`default_mount`、`auth_ref`、`status`、`last_checked_at`、`last_error`。
- 操作：创建 provider、测试连接、刷新列表。
- 不提供编辑/删除，直到后端实现对应 API。
- `auth_ref` 展示为引用，例如 `env:SECRETHUB_VAULT_DEV_TOKEN`，永不展示 token value。

### Credential Catalog

- 表格字段：`code`、`name`、`type`、`usage`、`provider_id`、`provider_type`、`masked`、`status`、`updated_at`。
- 筛选：keyword、type、usage、provider_id、provider_type、status。
- 操作：创建 credential、更新 metadata、更新 secret、复制 `credential_ref`。
- `update-secret` 独立抽屉，提交后立即清空输入，成功后只展示 fingerprint/更新时间，不回显明文。
- `resolve` 不作为普通 UI 操作暴露；如需要调试，必须另行设计只读 validate/handle 状态入口。

### Audit Trail

- MVP 展示最近 N 条，默认 `limit=100`。
- 字段：`created_at`、`event_type`、`actor`、`provider_id`、`credential_code`、`subject_type`、`subject_id`、`request_id`、`result`。
- 详情抽屉展示 message 和 metadata，metadata 进入前端脱敏渲染。
- 明确标注“当前为最近审计视图”，避免暗示完整审计检索已可用。

## Interaction Matrix

| Scenario | Entry | API | UI Pattern | Guardrail |
| --- | --- | --- | --- | --- |
| 检查 backend | App shell | `GET /healthz` | health chip | 不需要 token |
| 查看来源 | Secret Sources | `GET /api/v1/secrethub/providers` | compact table | token/auth_ref 不回显 |
| 创建来源 | Secret Sources / 新增 | `POST /api/v1/secrethub/providers` | drawer form | 只支持 Vault KV v2 |
| 测试来源 | row action | `POST /api/v1/secrethub/providers/{id}:test` | inline loading + result tag | failed 显示 last_error |
| 查看凭证 | Credential Catalog | `GET /api/v1/secrethub/credentials` | table + filters | 无明文字段 |
| 创建凭证 | Catalog / 新增 | `POST /api/v1/secrethub/credentials` | drawer form | secret_data 一次性输入 |
| 更新 metadata | row action | `PUT /api/v1/secrethub/credentials/{code}` | drawer form | 不混入 secret 更新 |
| 更新 secret | row action | `POST /api/v1/secrethub/credentials/{code}:update-secret` | guarded drawer | 提交后清空，不回显 |
| 校验引用 | optional utility | `POST /api/v1/secrethub/credentials:validate` | small side panel | 不 resolve 明文 |
| 导出 Vault index | admin action | `POST /api/v1/secrethub/credentials:export-vault-index` | confirm + JSON preview | 标注兼容模式 |
| 查看审计 | Audit Trail | `GET /api/v1/secrethub/audit?limit=100` | table + detail drawer | metadata 脱敏 |

## Visual System

- Surface: `#F7F7F8`。
- Accent: `#002FA7`，只用于 active nav、primary action、focus ring 和少量关键状态。
- Typography: Helvetica Neue、Söhne 或等价 sans；左对齐，数字使用 tabular numerics。
- Structure: 1px hairline rules、编号 tab、紧凑表格、无嵌套卡片。
- Motion: 仅使用抽屉进入、loading skeleton、状态变更 150-220ms ease-out。
- Accessibility: 状态色必须配文字；危险动作需要明确文案和二次确认；键盘可达。

## Options

- A. Standalone SecretHub Console。推荐。优点是符合独立产品边界，部署、鉴权、路由和 UI 演进都不被 OneOPS 绑住。
- B. OneOPS-UI 内嵌 SecretHub 页面。不采用。它违背“SecretHub 完全独立运行”的架构边界。
- C. Server-rendered minimal admin。不优先。实现可能快，但后续交互、表格、抽屉和独立产品体验会受限。

## User Decisions

- 已确认 SecretHub 前后端都独立于 OneOPS 运行。
- 已确认前端承载方式采用 `1A`：新建 `secrethub/frontend` 独立 SPA。
- 已确认前端技术栈采用 `2A`：Vue 3 + Vite + TypeScript + Ant Design Vue。
- 已确认部署拓扑采用 `3A`：frontend 与 backend 生产同域，API 走同源 `/api/v1/secrethub/*`。
- 已确认生产鉴权采用 `4A`：SecretHub native login/session，前端不长期保存 service token。
- 已确认 `5A`：MVP 不暴露 plaintext resolve UI。
- 已确认 `6A`：MVP 只做当前 backend 已实现能力，所有未实现后端能力只作为路线图。
