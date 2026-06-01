# OneOPS API 文档规范

本文档定义 OneOPS API 文档与接口实现的基本契约。

## 目标

API 文档应服务三类场景：

- 前后端联调。
- 自动化测试生成。
- 长期维护和问题定位。

它不应该只是接口列表，而应该说明业务含义、参数约束、权限、副作用、响应判定和错误处理。

## 使用门禁

API 文档只有在状态为 `reviewed` 或 `active` 时，才能作为前后端联调、测试自动化、Controller/handler 实现和 autodev story 发布依据。

如果 API 文档状态为 `blocked-human-confirmation`：

- 不得按其中的 path、DTO、权限、响应结构直接实现接口。
- 不得生成执行类测试或发布执行类 story。
- AI/autodev worker 只能整理待确认项，例如实际 path、业务成功判定、权限边界、错误码、响应结构。

如果 API 文档状态为 `draft`：

- 只能用于人工评审和联调讨论。
- 不得作为验收依据。

## 文档位置与命名

推荐位置：

```text
docs/api/
```

推荐命名：

```text
【接口文档】<系统>_<模块>_V<版本号>.md
```

对自动化更友好的文件也可以使用英文 slug：

```text
device-v2-api.md
monitoring-v2-api.md
log-forward-api.md
topology-api.md
```

## 文档结构

每份 API 文档应包含：

1. 文档信息。
2. 通用说明。
3. 认证与权限。
4. 通用响应结构。
5. 状态码与业务错误码。
6. 接口详情。
7. 接口汇总表。
8. 测试与联调说明。
9. 变更记录。

## 文档信息

| 项目 | 内容 |
|---|---|
| 系统名称 | `[待人工确认: 产品负责人]` |
| 模块名称 | `[待人工确认: 产品负责人]` |
| 版本号 | `V1.0` |
| 创建日期 | `YYYY-MM-DD` |
| 最近更新 | `YYYY-MM-DD` |
| 接口基准地址 | `[待人工确认: 后端负责人]` |
| 关联需求/设计 | `[待人工确认: 产品负责人]` |
| 维护人 | `[待人工确认: 项目负责人]` |
| 状态 | `blocked-human-confirmation` |

## 通用请求头

| Header | 必填 | 说明 |
|---|---|---|
| `Content-Type` | 是 | 通常为 `application/json` |
| `Authorization` | 视接口而定 | `Bearer <token>` 或项目既有认证方式 |
| `X-Request-Id` | 建议 | 便于链路追踪 |
| `X-Tenant-Code` | 视模块而定 | 多租户/fixture 场景必须明确 |

## 通用响应结构

项目中可能存在不同历史响应结构，API 文档必须写清楚当前接口实际使用哪一种。

常见结构 A：

```json
{
  "code": 200,
  "message": "success",
  "data": {},
  "timestamp": 1700000000000
}
```

常见结构 B：

```json
{
  "timestamp": 1700000000000,
  "responseCode": 0,
  "success": true,
  "message": "操作成功",
  "errorMsg": null,
  "data": {}
}
```

测试和联调必须注意：**HTTP 200 不等于业务成功**。必须同时检查 `success`、`code`、`responseCode` 或模块约定的业务状态字段。

## 接口详情模板

```markdown
### <接口名称>

**业务目的:** <该接口解决什么业务问题>

**副作用:** read-only / write / task-trigger / external-system / device-action

**权限要求:** <角色、权限点、tenant/device 约束>

**请求信息**

| 项目 | 内容 |
|---|---|
| Method | `GET/POST/PUT/PATCH/DELETE` |
| Path | `/api/...` |
| Content-Type | `application/json` |
| 认证 | 是/否 |

**请求参数**

| 参数名 | 位置 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|---|
| `id` | path/query/body | string | 是 | 非空 | 资源 ID |

**请求示例**

```json
{
  "name": "example"
}
```

**响应示例 - 成功**

```json
{
  "success": true,
  "data": {}
}
```

**响应示例 - 失败**

```json
{
  "success": false,
  "message": "参数错误"
}
```

**业务成功判定**

- HTTP status: `200`
- 业务字段: `success=true` 或 `code=200/0`
- 关键 data 字段: `<字段说明>`

**测试要点**

- 正常路径。
- 必填参数缺失。
- 权限不足。
- tenant/device 越界。
- 空结果。
- 重复提交。
- 外部依赖不可用。
```

## Method 与 path 设计

- 查询资源：优先 `GET`。
- 创建资源：优先 `POST`。
- 更新资源：优先 `PUT/PATCH`。
- 删除资源：优先 `DELETE`；若项目已有软删除操作 API，按现有风格。
- 批量操作必须说明批大小限制、失败策略和幂等策略。
- 任务触发类接口必须说明是否异步、如何查询任务状态。
- 设备/外部系统动作必须标记 `device-action` 或 `external-system`。

## 副作用分类

API 文档必须给每个接口标注副作用等级：

| 分类 | 说明 |
|---|---|
| `read-only` | 只读，不改变系统状态 |
| `write` | 写入 DB 或修改业务状态 |
| `task-trigger` | 触发后台任务、采集、同步、下发 |
| `external-system` | 调用外部服务并可能改变外部状态 |
| `device-action` | 触碰真实设备或网络命令 |

自动化测试默认只能执行 `read-only`。其他分类需要 story scope 或 approval 明确允许。

## 接口汇总表

| 序号 | 功能 | Method | Path | 副作用 | 权限 | 测试状态 |
|---|---|---|---|---|---|---|
| 1 | 查询列表 | `GET` | `/api/...` | `read-only` | `[待人工确认: 安全负责人]` | `[待人工确认: 测试负责人]` |

## 变更记录

| 日期 | 版本 | 变更 | 影响 | 作者 |
|---|---|---|---|---|
| YYYY-MM-DD | V1.0 | 初始版本 | `[待人工确认: 项目负责人]` | `[待人工确认: 项目负责人]` |
