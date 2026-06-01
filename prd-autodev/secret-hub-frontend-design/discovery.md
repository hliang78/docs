---
topic: secret-hub-frontend-design
kind: frontend
title: SecretHub 前端规划设计
createdAt: 2026-05-28T17:03:32+0800
---

# Discovery

## Findings

### Current Frontend Status

- SecretHub 目前没有独立前端目录；`secrethub/` 下只有 backend 相关结构。
- SecretHub 前端应新建为 `secrethub/frontend`，独立构建、独立路由、独立部署。
- OneOPS-UI 现有统一凭证工作台只作为外部集成参考，不作为 SecretHub Console 的承载目标。

### Current SecretHub Backend Slice

- 已实现 provider 列表、创建、连接测试。
- 已实现 credential 列表、创建、metadata 更新、secret 更新、validate、resolve、Vault index export。
- 已实现 material handle 签发和单次消费，并返回稳定 `secret_fingerprint`。
- 已实现 audit 最近列表，但只支持 `limit`，缺少分页、筛选和详情端点。
- 认证支持 `Authorization: Bearer <token>` 或 `X-SecretHub-Token`；未实现用户登录、RBAC 和 tenant isolation。
- Backend API 返回原生 JSON，独立前端需要自己的 API client 和错误处理，不应套用 OneOPS envelope 假设。

### OneOPS Relationship

- OneOPS 是 SecretHub 的外部消费方，不是 SecretHub 前端运行容器。
- OneOPS 后续可以通过 SecretHub API 消费 credential list、validate、resolve 或 material handle。
- OneOPS 可以提供跳转到 SecretHub Console 的外链，但 SecretHub Console 应能在没有 OneOPS 的环境中完整运行。

### Design Constraints

- 视觉方向应服务 SecretHub 自身产品定位：独立密钥中枢、可信、克制、显式状态、少装饰。
- “专业、简洁”不应等于空白大卡片；SecretHub 页面需要高密度但可读的运维信息层级。
- 交互上应优先使用表格、抽屉、状态标签、确认提示和分段导航；避免复杂画布和花哨动画。
- 敏感字段必须默认脱敏；`auth_ref` 可以展示引用名，不能展示 provider token。

### Backend Gaps That Affect UI Scope

- Provider update/delete 未实现。
- Credential delete 未实现。
- Sync preview/apply 未实现为 API，文档有路线但当前 handler 没有。
- Credential detail/referrers 未实现。
- Audit 缺少服务端筛选、分页、详情端点。
- SecretHub 生产级浏览器鉴权未实现；已确认需要补 native login/session 后再进入生产前端。

## Evidence

- SecretHub backend API: `secrethub/backend/internal/httpapi/handler.go`
- SecretHub domain model/status: `secrethub/backend/internal/domain/types.go`
- SecretHub service request/response DTO: `secrethub/backend/internal/service/service.go`
- SecretHub current limits: `secrethub/backend/README.md`
- SecretHub MVP design: `docs/secret_hub/SECRET_HUB_MVP_DESIGN.md`
- OneOPS integration plan, as external integration reference: `docs/secret_hub/SECRET_HUB_ONEOPS_INTEGRATION.md`

## Open Questions

- native auth/session 的接口契约、cookie 策略和 CSRF 策略需要在实现前冻结。
- 是否把 frontend 静态资源由 backend 同进程托管，或保持独立 Nginx/static web 容器。
- 是否补齐 SecretHub 后端分页/筛选，以便 audit/credential/provider 页支持生产数据量。
