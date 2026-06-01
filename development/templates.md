# OneOPS 开发文档模板

本文档提供常用正式开发文档模板。新模块、新接口、新测试批次可以直接复制对应章节使用。

模板正文必须保持中文；英文只保留给代码标识、字段名、状态值、enum、命令、文件路径和必要关键概念。

## 需求概要模板

````markdown
# 【需求概要】<系统或模块>_V1.0

## 1. 文档信息

| 项目 | 内容 |
|---|---|
| 系统/模块 | <名称> |
| 版本 | V1.0 |
| 创建日期 | YYYY-MM-DD |
| 需求来源 | <用户/PRD/问题/evidence> |
| 状态 | blocked-human-confirmation |
| 人工确认人 | [待人工确认: 项目负责人] |
| 人工确认日期 | [待人工确认: 项目负责人] |
| 未解决占位数 | <数字> |

## 0. 人工确认占位

- [待人工确认: 产品负责人] <业务目标/验收口径>
- [待人工确认: 架构负责人] <系统边界/模块边界>
- [待人工确认: 测试负责人] <测试范围/通过标准>

## 2. 背景与目标

### 2.1 背景

<为什么要做>

### 2.2 目标

- <目标 1>
- <目标 2>

## 3. 用户角色

| 角色 | 描述 | 主要职责 |
|---|---|---|
| <角色> | <描述> | <职责> |

## 4. 功能范围

### 4.1 <模块一>

- <功能点>
- <功能点>

### 4.2 <模块二>

- <功能点>
- <功能点>

## 5. 非功能需求

- 性能: <响应时间/并发/数据量>
- 可用性: <可用性目标>
- 安全: <权限/tenant/secret>
- 可扩展性: <扩展方向>
- 可观测性: <日志/指标/trace/evidence>

## 6. 关键业务规则

1. <规则>
2. <规则>

## 7. 边界与约束

- 本次包含: <范围>
- 本次不包含: <非目标>
- 依赖: <依赖系统/数据/权限>
- [待人工确认: <角色>]: <待确认项>

## 8. 验收标准

- <可验证结果>
- <测试/evidence 要求>
````

## 概要设计模板

````markdown
# 【概要设计】<系统或模块>_V1.0

## 1. 文档信息

| 项目 | 内容 |
|---|---|
| 模块 | <名称> |
| 版本 | V1.0 |
| 关联需求 | <需求文档> |
| 状态 | blocked-human-confirmation |
| 人工确认人 | [待人工确认: 项目负责人] |
| 人工确认日期 | [待人工确认: 项目负责人] |
| 未解决占位数 | <数字> |

## 0. 人工确认占位

- [待人工确认: 架构负责人] <核心架构/模块职责>
- [待人工确认: 后端负责人] <接口/数据模型/Service 边界>
- [待人工确认: 运维/安全负责人] <外部系统/设备/凭证边界>

## 2. 设计目标

- <目标>

## 3. 模块边界

| 模块 | 职责 | 不负责 |
|---|---|---|
| <模块> | <职责> | <非职责> |

## 4. 核心流程

```text
<入口>
  -> <步骤>
  -> <步骤>
  -> <结果>
```

## 5. 数据模型

- <实体/字段/来源>

## 6. API/任务/事件

| 类型 | 名称 | 说明 | 副作用 |
|---|---|---|---|
| API/Task/Event | <名称> | <说明> | read-only/write/task-trigger |

## 7. 权限与安全

- 权限点:
- tenant/device 边界:
- secret handling:
- approval boundary:

## 8. 测试策略

- 单元测试:
- 接口测试:
- 集成测试:
- 探索 probe:

## 9. 风险与待确认

- H0/H1 风险:
- [待人工确认: <角色>]:
````

## 数据库设计模板

````markdown
# 【数据库设计】<系统>_<模块>_V1.0

## 1. 文档信息

| 项目 | 内容 |
|---|---|
| 系统 | <系统> |
| 模块 | <模块> |
| 版本 | V1.0 |
| 关联文档 | <需求/设计> |
| 状态 | blocked-human-confirmation |
| 人工确认人 | [待人工确认: 项目负责人] |
| 人工确认日期 | [待人工确认: 项目负责人] |
| 未解决占位数 | <数字> |

## 0. 人工确认占位

- [待人工确认: 架构负责人] <实体关系/数据边界>
- [待人工确认: 后端负责人] <字段类型/索引/迁移策略>
- [待人工确认: 运维/安全负责人] <生产迁移/回滚策略>

## 2. 实体关系概览

```text
<实体A>(1) ----< <实体B>(n): <关系说明>
```

## 3. 表结构总览

| 表名 | 中文名称 | 说明 |
|---|---|---|
| `<table_name>` | <中文名> | <用途> |

## 4. 详细表结构

### 4.1 `<table_name>` (<中文名>)

**表说明:** <业务用途>

| 字段名 | 类型 | 长度 | 允许空 | 默认值 | 约束 | 注释 |
|---|---|---:|---|---|---|---|
| `id` | bigint/string | - | 否 | - | PRIMARY KEY | 主键 |
| `create_time` | datetime | - | 否 | CURRENT_TIMESTAMP | - | 创建时间 |
| `update_time` | datetime | - | 否 | CURRENT_TIMESTAMP | - | 更新时间 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| `idx_xxx` | 普通索引 | `xxx` | <用途> |

## 5. 数据字典

| 枚举 | 取值 | 含义 | 字段 |
|---|---|---|---|
| status | active | 启用 | `<table>.status` |

## 6. 迁移与兼容

- migration:
- 回滚:
- 兼容旧数据:
- [待人工确认: <角色>]:
````

## API 文档模板

````markdown
# 【接口文档】<系统>_<模块>_V1.0

## 1. 文档信息

| 项目 | 内容 |
|---|---|
| 系统 | <系统> |
| 模块 | <模块> |
| 基准地址 | <base url> |
| 版本 | V1.0 |
| 状态 | blocked-human-confirmation |
| 人工确认人 | [待人工确认: 项目负责人] |
| 人工确认日期 | [待人工确认: 项目负责人] |
| 未解决占位数 | <数字> |

## 0. 人工确认占位

- [待人工确认: 后端负责人] <实际 path/DTO/响应结构>
- [待人工确认: 产品负责人] <业务成功判定/错误口径>
- [待人工确认: 安全负责人] <认证/权限/tenant 边界>

## 2. 通用说明

- 认证:
- 通用请求头:
- 通用响应结构:
- 业务成功判定:

## 3. 接口详情

### 3.1 <接口名称>

**业务目的:** <说明>

**副作用:** read-only/write/task-trigger/external-system/device-action

| 项目 | 内容 |
|---|---|
| Method | `GET/POST/...` |
| Path | `/api/...` |
| 权限 | <权限点> |

**请求参数**

| 参数 | 位置 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|---|
| `id` | path | string | 是 | 非空 | 资源 ID |

**成功响应**

```json
{
  "success": true,
  "data": {}
}
```

**失败响应**

```json
{
  "success": false,
  "message": "参数错误"
}
```

**测试要点**

- 正常路径:
- 参数缺失:
- 权限不足:
- tenant/device 越界:
- 空结果:
````

## 测试用例模板

```markdown
# 【测试用例】<系统>_<模块>_V1.0

## 1. 文档信息

| 项目 | 内容 |
|---|---|
| 系统 | <系统> |
| 模块 | <模块> |
| 关联接口 | <接口文档> |
| 测试环境 | <环境> |
| 状态 | blocked-human-confirmation |
| 人工确认人 | [待人工确认: 项目负责人] |
| 人工确认日期 | [待人工确认: 项目负责人] |
| 未解决占位数 | <数字> |

## 0. 人工确认占位

- [待人工确认: 测试负责人] <测试范围/fixture/通过标准>
- [待人工确认: 运维/安全负责人] <环境/凭证/外部系统边界>

## 2. 测试目标

- <目标>

## 3. 测试数据与 fixture

| fixture | 类型 | 用途 | 安全性 |
|---|---|---|---|
| `<fixture>` | device/tenant/user | <用途> | test-only |

## 4. 功能测试用例

| 用例编号 | 用例名称 | 前置条件 | 步骤 | 输入 | 预期结果 | 状态 | evidence |
|---|---|---|---|---|---|---|---|
| TC_001 | 正常路径 | <条件> | <步骤> | <输入> | <业务结果> | - | - |

## 5. 边界与异常

- 必填为空:
- 长度超限:
- 数据不存在:
- 权限不足:
- 重复提交:

## 6. 性能测试

| 场景 | 并发 | 时长 | 目标 TPS | 目标响应时间 | 错误率 |
|---|---:|---|---:|---:|---:|
| 查询 | 50 | 5m | [待人工确认] | [待人工确认] | <=0.1% |
```

## 探索 evidence 模板

```json
{
  "schema_version": "oneops.exploration-evidence.v1",
  "record_id": "<record id>",
  "story_id": "<story id>",
  "flow_line": "device|monitoring|logging|topology|cross",
  "question": "<one concrete question>",
  "final_goal": "<final business proof>",
  "probe": {
    "id": "<probe id>",
    "level": "static|read-only-db|read-only-api|read-only-observability|read-only-script-inspection|dry-run|controlled-action|end-goal-proof",
    "action_class": "static|read-only|dry-run|test-data-write|controlled-action|external-device-action"
  },
  "critical_environments": [],
  "fixtures": [],
  "weak_points": [
    {
      "id": "<weak point id>",
      "harm_class": "H0|H1|H2|H3",
      "status": "PASS|FAIL|BLOCKED|APPROVAL|SKIPPED",
      "decision": "continue|open-repair|补fixture|request-approval|defer|stop"
    }
  ],
  "status": {
    "overall": "PASS|FAIL|BLOCKED|APPROVAL|SKIPPED",
    "reason": "<one line>"
  },
  "evidence_paths": [],
  "sanitization": {
    "credential_values_persisted": false,
    "raw_output_persisted": false
  },
  "next_decision": {
    "decision": "continue|open-repair|补fixture|request-approval|defer|stop",
    "one_line": "<next step>"
  }
}
```
