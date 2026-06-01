# OneOPS SecretHub 与 OneOps 集成开发说明

## 1. 文档目的

本文面向后续开发者，说明独立的 `OneOPS SecretHub` 如何与现有 OneOps 统一凭证体系协作。

阅读顺序建议：

1. `SECRET_HUB_MVP_DESIGN.md`：产品与 MVP 总体设计。
2. 本文：OneOps 侧集成边界、接口契约、迁移路径。
3. `SECRET_HUB_AI_HANDOFF.md`：下一轮 AI 或工程师的任务交接。

本文的核心结论：

1. SecretHub 是统一秘密管理中台，负责 Vault 等第三方平台的连接、目录、同步、审计。
2. OneOps 只保存和传递 `credential_ref`，不直接承担 Vault 运维细节。
3. MVP 先走兼容模式，后续再切到 SecretHub 直连列表和解析。

## 2. 现有 OneOps 凭证基线

现有 OneOps 已经具备统一凭证入口和 Vault catalog 能力，SecretHub 不需要从零替换。

### 2.1 后端关键文件

```text
OneOPS/app/credential/api/credential.go
OneOPS/app/credential/router/credential.go
OneOPS/app/credential/dto/request_response.go
OneOPS/app/credential/service/i_credential_resolver.go
OneOPS/app/credential/service/impl/resolver_adapter.go
OneOPS/app/credential/service/impl/vault_provider.go
OneOPS/app/credential/credential_model/vault_catalog.go
OneOPS/app/platform/service/impl/task_execution_profile_resolver.go
```

### 2.2 前端关键文件

```text
OneOPS-UI/src/views/setting/CredentialUnified.vue
OneOPS-UI/src/api/credential.ts
OneOPS-UI/src/typings/credential.ts
```

### 2.3 当前 OneOps 可复用能力

1. `POST /api/v1/credential/list`：统一凭证列表，无明文。
2. `GET /api/v1/credential/vault/catalog`：Vault catalog 列表。
3. `POST /api/v1/credential/vault/catalog:sync`：从 Vault catalog index 强制同步。
4. `POST /api/v1/credential/vault/catalog`：新增 Vault catalog 目录项并可写 secret。
5. `PUT /api/v1/credential/vault/catalog`：更新 catalog metadata，并可局部更新 secret。
6. `DELETE /api/v1/credential/vault/catalog/:code`：删除 catalog 目录项。
7. Task Center、任务模板、计划任务已开始使用 `credential_ref` 语义，并兼容旧 `credential_code`。

### 2.4 当前约束

1. OneOps 仍然理解 Vault path、KV v2、field mapping、catalog index。
2. 部分执行链路仍会在后端解析明文材料后透传给 Controller 或 Agent。
3. `Secret` / `Community` 旧模型仍存在，短期不能一次性移除。
4. SecretHub 与 OneOps 不应同时作为 catalog owner，否则容易出现目录冲突。

## 3. 集成原则

1. SecretHub owns catalog：SecretHub 负责统一凭证目录、第三方 provider 元数据、同步策略。
2. Provider owns material：Vault 等第三方平台负责保存真实 secret material。
3. OneOps consumes ref：OneOps 业务模块只消费 `credential_ref` 和标准摘要。
4. No plaintext in list：列表、下拉、引用查询都不得返回明文。
5. Resolve is auditable：任何解析材料的动作必须记录审计。
6. Compatibility first：MVP 先兼容现有 OneOps Vault catalog，再逐步替换为 SecretHub API。

## 4. 分阶段接入路线

### Phase 0：文档与契约冻结

目标：先统一字段、接口和责任边界，避免开发时分叉。

交付：

1. 确定 SecretHub 目录结构。
2. 确定 OneOps 兼容接口返回格式。
3. 确定 Vault path 规范和 `field_mapping` 规范。
4. 确定 `credential_ref` 继续以 catalog `code` 作为主标识。

验收：

1. OneOps、SecretHub、UI 三方字段命名一致。
2. 文档中不再混用 `secret_code`、`credential_code`、`credential_ref` 作为不同语义。

### Phase 1：Vault catalog index 兼容模式

目标：SecretHub 先不改 OneOps 主链路，通过写入或导出 Vault catalog index，让 OneOps 继续同步。

流程：

```text
SecretHub 创建/导入凭证
        |
        v
Vault secret + Vault catalog index
        |
        v
OneOps POST /credential/vault/catalog:sync
        |
        v
OneOps credential_vault_catalog
        |
        v
设备入库 / 任务 / 采集下拉可选
```

OneOps 侧需要做的事：

1. 保持现有 `POST /api/v1/credential/vault/catalog:sync` 可用。
2. 确认 quick env 默认配置有 `catalog_sync_path`。
3. 保持 `CredentialUnified.vue` 的同步按钮可用。
4. 设备入库和任务页面继续从 `POST /api/v1/credential/list` 获取候选项。

SecretHub 侧需要做的事：

1. 创建 Vault provider。
2. 写入 secret material 到 Vault。
3. 维护 catalog index，支持简化格式和展开格式。
4. 提供导出 index 或直接写 index 的能力。

风险：

1. OneOps 仍然持有 Vault 访问配置。
2. SecretHub 与 OneOps 都可能编辑 catalog，需要约定 Phase 1 期间以 SecretHub 为主。

### Phase 2：OneOps 直接拉取 SecretHub 凭证列表

目标：OneOps 的统一凭证列表从 SecretHub 获取，不再依赖 Vault catalog index 同步。

推荐新增 OneOps 配置：

```yaml
credential:
  providers:
    secrethub:
      enabled: true
      base_url: "http://secrethub:8080"
      token: "${SECRET_HUB_TOKEN}"
      timeout_seconds: 5
      list_cache_seconds: 30
      # 默认只接入列表；解析委托需要显式开启。
      resolve_enabled: false
      # 开启解析后默认建议使用 material_handle，避免 OneOps 后端长期持有明文。
      resolve_response_mode: "material_handle"
```

OneOps 新增或改造点：

1. 新增 `SecretHubCredentialProvider`，实现现有 `ListCredentials` 摘要接口。
2. `resolver_adapter.go` 合并本地 Secret、Community、Vault、SecretHub 的摘要。
3. 相同 `code` 冲突时，优先级建议为：SecretHub > Vault DB catalog > Vault config catalog > legacy Secret/Community。
4. UI 不需要先大改，仍然调用 `POST /api/v1/credential/list`。

当前 OneOps 统一凭证列表已支持按来源和状态筛选：

```json
{
  "type": "ssh_account",
  "provider": "secrethub",
  "status": "active"
}
```

`status` 默认按 `active` 处理；可传 `all`、`disabled`、`needs_review`、`orphaned` 查看 SecretHub 暴露的非 active 目录项。Vault 与 legacy OneOps 摘要按 `active` 处理。

SecretHub 列表接口建议：

```http
GET /api/v1/secrethub/credentials?keyword=&type=&usage=&status=active
```

响应：

```json
{
  "items": [
    {
      "code": "vault_linux_ops2",
      "name": "Linux Ops 2",
      "type": "ssh_account",
      "usage": "inband",
      "provider": "vault-prod",
      "provider_type": "vault",
      "masked": true,
      "status": "active",
      "updated_at": "2026-05-28T00:00:00Z"
    }
  ],
  "total": 1
}
```

OneOps 映射到现有 `CredentialSummary`：

```text
code          -> code
name          -> name
type          -> type
usage         -> usage
provider      -> source/provider
masked        -> masked
status        -> status
```

### Phase 3：OneOps 解析委托给 SecretHub

目标：OneOps 执行链路不再直接读 Vault，由 SecretHub 负责 resolve 和审计。

SecretHub 解析接口：

```http
POST /api/v1/secrethub/credentials:resolve
```

请求：

```json
{
  "credential_ref": "vault_linux_ops2",
  "usage": "inband",
  "subject_type": "task",
  "subject_id": "task-001",
  "caller": "oneops",
  "request_id": "audit-001",
  "response_mode": "material_handle"
}
```

MVP 响应：

```json
{
  "credential_code": "vault_linux_ops2",
  "provider": "vault-prod",
  "credentials": {
    "username": "ops",
    "password": "******"
  }
}
```

长期响应：

```json
{
  "credential_code": "vault_linux_ops2",
  "provider": "vault-prod",
  "material_handle": "secrethub:v1:...",
  "secret_fingerprint": "5cf7..."
}
```

`secret_fingerprint` 是 SecretHub 基于映射后的秘密材料生成的稳定 HMAC/Hash，用于 OneOps `ContentHash` 判断。不要直接用 `material_handle` 计算内容指纹，因为 handle 含 nonce、TTL，每次签发都会变化。

OneOps 改造点：

1. `ResolverAdapter.ResolveReference` 在 `resolve_enabled=true` 时优先调用 SecretHub resolve。
2. `TaskExecutionProfileResolver` 已允许 SecretHub 返回 handle-only 响应，profile 使用 `connector_fetch`。
3. `secrethub:v1:*` handle 会通过 SecretHub `material:resolve` 消费，而不是当作 Vault handle 解析。
4. 404 表示 SecretHub 未命中，可继续走 Vault/legacy；4xx 配置或用途错误应显式失败。
5. 所有 resolve 请求携带 `subject_type / subject_id / request_id`，便于审计追踪。

### Phase 4：Material handle 和最小明文暴露

目标：减少 OneOps 后端和 Controller/Agent 的明文停留时间。

改造方向：

1. SecretHub 返回短时、单次使用的 `material_handle`。
2. Controller 或 Agent 使用 handle 换取材料。
3. handle 有 TTL、用途、主体、调用方签名。
4. 审计记录 handle 创建、消费、过期和拒绝。

当前切片已完成 SecretHub handle 签发、单次消费、稳定 `secret_fingerprint` 返回和 OneOps handle-only profile 兼容；后续还需要补 UI 状态展示。

## 5. 字段与数据映射

### 5.1 SecretHub catalog 到 OneOps credential summary

| SecretHub 字段 | OneOps 字段 | 说明 |
| --- | --- | --- |
| `code` | `code` / `credential_ref` | 全局唯一引用 |
| `name` | `name` | 展示名称 |
| `type` | `type` | 如 `ssh_account`、`snmp_community` |
| `usage` | `usage` | 如 `inband`、`snmp_inband` |
| `provider_id` | `provider` | 展示或过滤用 |
| `provider_type` | `source` | `vault`、`aws_secrets_manager` 等 |
| `status` | `status` | `active` 才可选择 |
| `field_mapping` | 不直接暴露给 UI | resolve 时使用 |

### 5.2 SecretHub catalog 到 OneOps Vault catalog index

SecretHub 内部：

```json
{
  "code": "vault_linux_ops2",
  "name": "Linux Ops 2",
  "type": "ssh_account",
  "usage": "inband",
  "provider_id": "vault-prod",
  "secret_path": "kv/data/oneops/credentials/vault_linux_ops2",
  "field_mapping": {
    "username": "username",
    "password": "password"
  }
}
```

导出给当前 OneOps 的展开格式：

```json
{
  "items": [
    {
      "code": "vault_linux_ops2",
      "name": "Linux Ops 2",
      "type": "ssh_account",
      "usage": "inband",
      "path": "kv/data/oneops/credentials",
      "field_mapping": {
        "username": "username",
        "password": "password"
      }
    }
  ]
}
```

注意：当前 OneOps 的物理路径规则是 `path + "/" + code`。如果 SecretHub 内部保存完整 `secret_path`，导出 index 时要拆成 `path` 和 `code`。

## 6. OneOps 侧开发清单

### 6.1 后端

第一批最小改动：

1. 新增 SecretHub client 配置结构。
2. 新增 SecretHub HTTP client，包含超时、错误归一化、token 注入。
3. 新增 `SecretHubCredentialProvider`，接入 `ListCredentials`。
4. 给 `TaskExecutionProfileResolver` 增加 SecretHub resolve 分支。
5. 给 resolve 增加审计字段：`caller`、`request_id`、`subject_type`、`subject_id`。

建议文件：

```text
OneOPS/config/credential.go
OneOPS/app/credential/service/impl/secrethub_provider.go
OneOPS/app/credential/service/impl/secrethub_client.go
OneOPS/app/platform/service/impl/task_execution_profile_resolver.go
```

### 6.2 前端

MVP 阶段不要求 OneOps UI 直接管理 SecretHub 全部功能。OneOps UI 只需要能消费候选凭证。

保留页面：

```text
OneOPS-UI/src/views/setting/CredentialUnified.vue
```

后续增强：

1. 在统一凭证列表增加 `source/provider/status` 过滤。
2. 对 SecretHub 来源的凭证，仅提供查看引用和跳转 SecretHub，不在 OneOps 内编辑 secret。
3. 保留 Vault catalog 页面作为过渡能力，标记为兼容模式。

### 6.3 quick_env

quick_env 的职责只保留为 OneOPS 平台快速部署环境，并在该环境中拉起 Vault。
SecretHub 不应被加入 quick_env 的 compose，不在 quick_env 中初始化
SecretHub DB，也不通过 quick_env 提供 SecretHub Console 入口。

需要保留：

1. quick_env 启动 Vault，并完成 OneOPS 侧 Vault bootstrap。
2. OneOPS 可以继续使用 quick_env 内置 Vault 作为快速部署依赖。
3. SecretHub 如需联调 quick_env 中的 Vault，应把它当作外部 Vault provider，
   通过 endpoint、mount 和 `auth_ref` 接入，而不是依赖 quick_env 启动 SecretHub。

明确排除以下 quick_env 改造范围：把 SecretHub 后端、SecretHub 数据库初始化、
SecretHub Console 静态资源、SecretHub 反向代理或 SecretHub 专用 seed/smoke
流程加入 quick_env。

### 6.4 测试

后端测试：

1. SecretHub list 超时不影响 legacy provider 列表。
2. SecretHub 与 Vault catalog 同 code 冲突时优先级符合约定。
3. SecretHub resolve 成功时 `execution_profile` 填充材料或 handle。
4. SecretHub resolve 失败时 fallback 行为符合 `TaskAuthPolicy`。
5. 列表接口不返回 `password/token/private_key/community`。

前端测试：

1. 统一凭证下拉能展示 SecretHub 来源。
2. SecretHub 来源凭证不出现 secret 编辑入口。
3. Provider/status/type/usage 过滤可用。

联调测试：

1. SecretHub 创建 Vault SSH 凭证。
2. OneOps 设备入库选择该 `credential_ref`。
3. Task Center 使用该 `credential_ref` 创建任务。
4. OneOps 通过 SecretHub resolve 获取执行材料。
5. SecretHub 审计中出现 resolve 记录。

## 7. API 契约建议

### 7.1 List credentials

```http
GET /api/v1/secrethub/credentials
```

查询参数：

```text
keyword
type
usage
provider_id
provider_type
status
page
page_size
```

约束：

1. 只返回 metadata。
2. `status != active` 默认不返回给 OneOps 选择器。
3. 不返回 provider token 或任何 secret material。

### 7.2 Resolve credential

```http
POST /api/v1/secrethub/credentials:resolve
```

约束：

1. 只允许 OneOps 后端等可信调用方访问。
2. 请求必须携带 `credential_ref` 和调用上下文。
3. 响应可以在 MVP 返回材料，但必须写审计。
4. 后续优先切为 `material_handle`。
5. 响应应返回稳定 `secret_fingerprint`，供 OneOps 计算任务内容哈希。

### 7.3 Validate credential ref

```http
POST /api/v1/secrethub/credentials:validate
```

用途：

1. 设备入库保存前校验。
2. 任务模板保存前校验。
3. 批量导入 dry-run 校验。

响应：

```json
{
  "valid": true,
  "credential_ref": "vault_linux_ops2",
  "type": "ssh_account",
  "usage": "inband",
  "message": ""
}
```

### 7.4 Export Vault catalog index

```http
POST /api/v1/secrethub/credentials:export-vault-index
```

用途：

1. Phase 1 兼容当前 OneOps。
2. 生成或写入 Vault catalog index。
3. 支持 dry-run，便于确认导出内容。

## 8. 安全底线

开发时必须遵守：

1. 列表接口不返回明文。
2. 日志不打印 secret payload。
3. 审计 metadata 不写入 secret value。
4. Provider token 不通过 GET 接口回显。
5. SecretHub provider token 不应明文落库；本地开发可先用环境变量。
6. OneOps 调 SecretHub 的 token 要可轮换。
7. Resolve API 必须限制来源和权限。
8. UI 表格不展示 password、token、private_key、community。

## 9. 冲突与降级策略

### 9.1 Code 冲突

推荐优先级：

```text
SecretHub > OneOps Vault DB catalog > OneOps Vault config catalog > legacy Secret/Community
```

如果冲突来源不同但 metadata 不一致：

1. 列表返回 SecretHub 项。
2. 后端记录 warning。
3. 管理页标记 `needs_review`。

### 9.2 SecretHub 不可用

列表场景：

1. 使用短 TTL 缓存。
2. 缓存没有命中时，只返回 legacy provider。
3. UI 显示 SecretHub source 异常，但不阻断其他凭证。

执行场景：

1. 如果任务显式要求 SecretHub 来源凭证，resolve 失败应失败任务。
2. 如果配置允许 fallback，可回退 legacy provider。
3. fallback 必须写审计。

## 10. MVP 完成标准

OneOps 侧认为 SecretHub 集成 MVP 完成，需要满足：

1. SecretHub 创建 Vault 凭证后，OneOps 能看到该凭证。
2. OneOps 设备入库、任务模板、计划任务可以保存该 `credential_ref`。
3. OneOps 任务执行前可以通过 SecretHub resolve 获取材料。
4. 列表和页面不展示明文。
5. SecretHub 审计能看到 create、update、list、resolve 或 sync 记录。
6. SecretHub 不可用时，OneOps legacy 凭证列表不被整体拖垮。
7. quick_env 能拉起 OneOPS 快速部署所需的 Vault；SecretHub 作为独立服务通过外部 provider 方式连接该 Vault。

## 11. 后续开发入口

建议下一轮按这个顺序开工：

1. 在 `OneOPS-ALL/secrethub/backend` scaffold 后端。
2. 先实现 Vault provider 和 credentials CRUD。
3. 实现 `export-vault-index`，打通 Phase 1。
4. 在 OneOps 增加 SecretHub list provider，打通 Phase 2。
5. 在 `TaskExecutionProfileResolver` 增加 SecretHub resolve，打通 Phase 3。
6. 最后再做 SecretHub 前端的 Secret Sources、Credentials、Sync Jobs、Audit 四个页面。
