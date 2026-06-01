# 【接口文档】OneOPS_DeviceV2纳管观测_v0.1

## 1. 文档信息

| 项目 | 内容 |
| --- | --- |
| 系统名称 | OneOPS |
| 模块名称 | Device V2 纳管观测 |
| 版本号 | v0.1 |
| 接口基准地址 | 待实现时以现有 Device V2 路由为准 |
| 文档状态 | 草案 |
| 关联文档 | 【需求概要】OneOPS_v0.1.md<br>【数据库设计】OneOPS_DeviceV2纳管观测_v0.1.md |

## 2. 通用说明

### 2.1 通用请求头

| Header | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| Authorization | string | 是 | 复用现有登录态/token |
| Content-Type | string | 是 | `application/json` |

### 2.2 通用响应结构

复用现有 OneOPS API 响应结构。若现有 Device V2 API 有固定封装，以实现时实际代码为准，不新增全局响应格式。

### 2.3 状态码说明

| 状态码 | 说明 |
| --- | --- |
| 200 | 请求成功 |
| 400 | 参数错误或缺少明确选择 |
| 500 | 后端执行失败 |
| 待确认 | 现有权限错误码以项目实现为准 |

## 3. 接口列表

### 3.1 获取单设备纳管摘要

**接口描述**：读取单台 Device V2 设备的 onboarding action 摘要。

| 项目 | 内容 |
| --- | --- |
| 接口URL | `/device/v2/:code/onboarding` |
| 请求方式 | GET |
| 是否登录 | 是 |

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| deviceV2Id 或 deviceCode | string | 是 | 必须唯一定位单台设备 |

**响应数据**：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| actions | array | 纳管 action 列表 |
| retryableActions | array | failed/unknown ensure action |
| actions[].action | string | 监控 controller-backed 动作固定为 `monitor_controller_stage` |
| actions[].evidence.controller_backed | boolean | 固定为 controller-backed 证据 |
| actions[].evidence.controller_stage | string | controller 当前阶段 |
| actions[].evidence.store_run_status | string | `device_v2_store_run.status` |
| actions[].evidence.core_store_status | string | `device_v2_store_run.core_store_status` |
| actions[].evidence.manageable_status | string | `device_v2_store_run.manageable_status` |
| actions[].evidence.task_id | string | 对应 task ID |
| actions[].evidence.store_run_id | string | 对应 store run ID |

### 3.2 生成单设备继续纳管计划

**接口描述**：根据设备类型、agent 状态、区域基础服务和用户选择生成纳管计划。

| 项目 | 内容 |
| --- | --- |
| 接口URL | 待实现 |
| 请求方式 | POST |
| 是否登录 | 是 |

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| deviceV2Id 或 deviceCode | string | 是 | 单设备标识 |
| serverMonitorMode | string | 服务器必填 | `agent` 或 `snmp` |

**业务规则**：

- 缺少服务器监控模式时返回错误。
- 批量设备不得执行，仅可生成逐台计划。
- 缺少区域 syslog listener 时返回错误。

### 3.3 执行单设备继续纳管

**接口描述**：执行明确的 ensure action，并保存结果。

| 项目 | 内容 |
| --- | --- |
| 接口URL | `/device/v2/:code/onboarding/ensure` |
| 请求方式 | POST |
| 是否登录 | 是 |

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| deviceV2Id 或 deviceCode | string | 是 | 单设备标识 |
| actionIds | array | 是 | 要执行的 ensure action |
| serverMonitorMode | string | 服务器必填 | `agent` 或 `snmp` |

**约束**：

- 只执行 failed/unknown 或尚未执行的 ensure action。
- success action 不重复执行。
- 业务远程服务器操作必须调用 controller API。
- 开发测试工具不得被业务接口调用。

### 3.4 区域 listener service 合同（平台 log-forward 包装）

**接口描述**：平台侧独立的区域 listener 管理入口首期复用现有 `/platform/metrics/log-forward/plans` 持久化与发布链，不新建第二套 publish engine；但响应必须显式暴露 area listener service contract，供后续独立页面与 single-device onboarding rerun 共同消费。

**首期 listener service type**：

- `server_syslog_listener`
- `network_syslog_listener`
- `snmp_trap_listener`

**合同约束**：

- listener service type 通过现有 `target_scope.listener_service_type` / `target_scope.listener_service.service_type` 持久化到 `log_forward_plan` 包装层；前端 area-listener CRUD 在保存时同步透传顶层 `listener_service_type`。
- 若当前后端仍未把这些 listener 字段原样回写到列表/明细，前端允许基于“本次用户明确保存的合同”按 `plan_id` 写入页面本地 overlay，用于恢复同一 row 的编辑/发布入口；不得据名称、描述或其他弱信号猜测 listener type。
- `server_syslog_listener` 与 `network_syslog_listener` 首期统一映射到现有 `plan_type=remote_syslog` 发布链。
- `snmp_trap_listener` 本轮只定义“区域 listener 管理”合同，不扩展到设备侧 trap target 下发。
- 当调用方读取 plan 明细/列表时，响应必须显式返回：
  - `listener_service_type`
  - `listener_service_contract.scope`
  - 若历史数据或后端暂未显式回填顶层 `listener_service_type`，页面只允许从 `target_scope.listener_service_type` / `target_scope.listener_service.service_type` 或同一 `plan_id` 的本地 overlay 恢复同一合同语义，但不得猜测不存在的类型。
  - `listener_service_contract.listener_protocol`
  - `listener_service_contract.adapter_status`
  - `listener_service_contract.adapter_gap`（若存在）
- 对 `snmp_trap_listener` 执行 dry-run / preflight / apply 时，后端必须返回精确 adapter gap，不能伪装成沿用 `remote_syslog` 成功。

**响应语义补充**：

- `listener_service_contract.adapter_status=mapped`：表示当前 listener service type 已准确复用到既有 `log_forward_plan` / `remote_syslog` 链路。
- `listener_service_contract.adapter_status=adapter_gap`：表示该 listener service type 当前只落合同，不存在可执行发布适配器。
- `listener_service_contract.adapter_status=legacy_unspecified`：表示历史 `remote_syslog` plan 尚未补齐明确 listener service type，后续 onboarding rerun 不得把它当成“精确 area listener 合同”。

## 4. 接口汇总表

| 序号 | 功能 | 请求方式 | 接口地址 | 是否需要登录 | 说明 |
| --- | --- | --- | --- | --- | --- |
| 1 | 获取纳管摘要 | GET | 待实现 | 是 | 单设备 |
| 2 | 生成纳管计划 | POST | 待实现 | 是 | 单设备 |
| 3 | 执行继续纳管 | POST | 待实现 | 是 | 单设备 |

**返回约束补充**：

- `GET /device/v2/:code/onboarding` 与 `POST /device/v2/:code/onboarding/ensure` 都要返回同一条 controller-backed 监控动作：`monitor_controller_stage`。
- 前端展示必须直接读取该 action 的 `controller_stage`、`store_run_status`、`core_store_status`、`manageable_status`、`task_id`、`store_run_id`，不能退化成只显示通用 message。
- 当 `ensure` 的日志纳管配置来源缺失时，接口仍要返回正常 onboarding payload；精确 blocker 必须落在 failed log action 的 `reason/error_detail` 中，而不能把整个响应降级成 `data=null`。
- `ensure` 解析日志纳管 listener 时必须优先使用设备自身 `function_area`；仅当设备未显式携带区域时，才回退到 `DefaultArea`。

## 5. 待确认事项

| 序号 | 待确认内容 | 影响接口 | 状态 |
| --- | --- | --- | --- |
| 1 | 具体路由命名 | 全部 | 待实现时确认 |
| 2 | 现有权限错误码 | 全部 | 待确认 |
| 3 | 单设备 continue-onboarding 的真实 controller-backed 执行结果 | 生成/执行接口 | 仍缺失：当前仅有本地契约与证据结构验证，未拿到可复用的真实远程执行结果 |
