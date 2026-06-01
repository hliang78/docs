# 【后端开发设计】OneOPS_DeviceV2纳管观测_v0.1

## 1. 文档信息

| 项目 | 内容 |
| --- | --- |
| 系统名称 | OneOPS |
| 模块名称 | Device V2 纳管观测 |
| 版本号 | v0.1 |
| 文档状态 | 草案 |
| 关联文档 | 【需求概要】OneOPS_v0.1.md<br>【数据库设计】OneOPS_DeviceV2纳管观测_v0.1.md<br>【接口文档】OneOPS_DeviceV2纳管观测_v0.1.md |

## 2. 工程结构

### 2.1 标准业务模块结构

```text
OneOPS/app/device/v2/
  api/
  dto/
  router/
  service/
```

### 2.2 标准工具模块结构

```text
docs/openclaw-autodev/tools/d2on/
  d2on-discovery.py
  README.md
  test-targets.md
```

工具模块仅用于开发测试和真实设备探索，不得被业务代码调用。`d2on-discovery.py` 可在运行时读取只读 MySQL 连接环境变量、查询 `platform_devices_v2` 候选设备，并优先通过 controller `/api/v1/remote/run` 执行有界只读探测；直接 SSH 路径只保留为开发回退。它产生的证据只写入 `docs/openclaw-autodev/evidence/d2on/`，不得进入业务链路。

## 3. 分层职责

| 层级 | 路径 | 职责 | 命名 |
| --- | --- | --- | --- |
| API/Router | `api/`, `router/` | HTTP 入口、参数校验、响应 | 复用 Device V2 风格 |
| Service | `service/` | 纳管计划、执行、证据合并 | Onboarding 相关命名 |
| DTO | `dto/` | 请求/响应结构 | Onboarding DTO |
| Test Tool | `docs/openclaw-autodev/tools/d2on/` | 开发测试探索 | 不进入业务依赖 |

## 4. Controller 设计

| Service 接口 | Controller | 根路径 | 说明 |
| --- | --- | --- | --- |
| OnboardingService | 待实现 | 待实现 | 单设备纳管摘要、计划、执行 |

### 4.1 方法映射规则

- 方法必须显式表达单设备语义。
- 参数缺失、设备不唯一、服务器监控模式未选择必须返回错误。
- 批量执行请求必须拒绝或仅返回计划。

### 4.2 响应封装

复用现有 Device V2 响应封装，不引入全局响应结构变化。

## 5. Service 设计

### 5.1 Service 接口清单

| 接口 | 方法 | 入参 | 返回值 | 说明 |
| --- | --- | --- | --- | --- |
| OnboardingService | GetSummary | 单设备标识 | Summary | 读取 action 摘要 |
| OnboardingService | BuildPlan | 单设备标识、用户选择 | Plan | 生成继续纳管计划 |
| OnboardingService | EnsureActions | 单设备标识、actionIds | Result | 执行 ensure action |

### 5.2 基础方法要求

- 不做 fallback 或智能推断。
- 缺少配置、模板、controller API 或 netlink 契约时返回明确错误。
- 业务远程服务器操作只通过 controller API。

### 5.3 边界校验规则

| 场景 | 处理 |
| --- | --- |
| 多设备执行 | 拒绝执行 |
| success action 重试 | 跳过，不再执行 |
| failed/unknown action 重试 | 允许执行 |
| 无 agent 的服务器日志 | 生成 SSH 配置计划 |
| 网络设备无 syslog 模板 | failed/BLOCKED，记录 template_required evidence，不回退猜测命令 |

## 6. 数据访问设计

### 6.1 Mapper 方法清单

不新增 Mapper。

### 6.2 Repository 方法清单

复用现有 Device V2 store run 读取和保存能力；若不存在明确能力，必须先补齐局部服务方法。

## 7. 对象转换

| 来源 | 目标 | 说明 |
| --- | --- | --- |
| summary_json | OnboardingSummary | 解析 action |
| OnboardingPlan | summary_json | 保存 planned/skipped/action 结果 |
| controller API 响应 | ActionEvidence | 保存真实执行结果 |

## 8. 事务、缓存与异常

- 保存 action 证据应保持单设备原子更新。
- 不引入缓存。
- 远程执行错误必须保留 error code/message。

## 9. 文件输出清单

| 类型 | 文件 | 路径 |
| --- | --- | --- |
| 后端服务 | 待实现 | `OneOPS/app/device/v2/**` |
| 前端接口 | 待实现 | `OneOPS-UI/src/api/device/**` |
| 开发测试工具 | 待实现 | `docs/openclaw-autodev/tools/d2on/**` |
| 证据 | 每个 story summary | `docs/openclaw-autodev/evidence/d2on/**` |

## 10. 代码规范

- 遵循现有 Device V2 包结构。
- 不新增全局依赖或全局配置。
- 测试覆盖 action 合并、重试选择、错误暴露、controller API 边界。
