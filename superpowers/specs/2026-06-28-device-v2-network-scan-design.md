# Device V2 Network Scan Design

Date: 2026-06-28

## Goal

在现有 Device V2 管理页中，将前端 `设备探测` demo 收敛成一条真实可执行的链路：

1. 用户手工选择 `function_area`
2. 输入 `IP / IP range / CIDR`
3. 由对应区域的 controller 使用 `nmap` 执行真实扫描
4. 扫描结果以待审核候选设备形式进入 Device V2
5. 用户确认后进入正式设备清单
6. 继续复用现有采集与入库链路完成真实采集

本设计的核心不是引入一个全新的资产发现平台，而是在现有 Device V2、controller 和 DC2/ingest/store 能力之上，补齐“扫描发现”这一前置阶段。

## Non-Goals

本次不纳入：

- L2 `ARP` 扫描
- `LLDP/CDP` 邻居扩展发现
- 自动推断 `function_area`
- 自动直接入库
- 自动直接采集
- IPv6 扫描
- 全端口扫描
- `OS fingerprint`、大规模 `NSE` 脚本执行
- 将扫描结果直接落为正式 Device V2 设备

## Existing Context

### Current Frontend State

当前前端已经有 `设备探测` 抽屉与 demo 交互，主要位于：

- `OneOPS-UI/src/views/device/components/DeviceDiscoveryDrawer.vue`
- `OneOPS-UI/src/views/device/device-discovery-workbench.ts`
- `OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue`

当前问题是：

- 抽屉中的执行记录、待入库设备和“入设备清单”都来自本地模拟状态；
- `simulateDiscoveryExecution(...)` 生成固定结果；
- 管理页对 `设备探测` 来源设备存在本地 demo 特判逻辑；
- 与真实 controller、真实扫描、真实 Device V2 ingest 没有闭环。

### Backend Reality

现有后端具备这些相关能力：

- `function_area -> controller` 已有成熟路由机制；
- Device V2 已有正式 ingest/store/start 采集链路；
- `/api/v1/device/detect` 适合做“已知目标识别/采集”，不等于网段扫描；
- `network_scan` 已在 Device V2 source 类型中预留，但后端尚未真正实现扫描编排层。

这意味着本次设计要解决的关键缺口是：

- 真实扫描任务模型
- controller 执行真实 `nmap`
- 扫描结果持久化
- 扫描结果与 Device V2 ingest 的正式衔接

## Product Decision

### Discovery Mode

首期仅支持：

- `controller + nmap`
- `L3/L4` 主动发现
- `IPv4`
- `subnet discovery`

`设备种子 / 邻居扩展` 在页面层可保留占位，但不进入首期真实实现范围。

### Function Area Rule

用户发起扫描时，必须手工选择 `function_area`。

首期不做自动归属判断，原因是当前主数据里的 `Prefix` 并不天然绑定 `function_area`。如果系统自动猜测区域，极易将扫描下发到错误的 controller，导致网络不可达、权限不符或跨区误扫。

首期固定规则：

- `IP / range / CIDR` 仅表示扫描范围
- `function_area` 决定 controller 归属
- controller 仅通过现有 `function_area -> controller` 机制选取

## User Journey

1. 用户进入 Device V2 管理页。
2. 点击 `设备探测` 打开右侧抽屉。
3. 在抽屉中创建或编辑一条 `网段探测计划`。
4. 用户填写：
   - 计划名称
   - `function_area`
   - 扫描范围：`IP / IP range / CIDR`
   - 排除范围
   - 端口策略
5. 用户点击 `立即执行`。
6. 后端创建扫描 run，并路由到对应 controller。
7. controller 使用 `nmap` 执行真实扫描并回传结果。
8. OneOps 将结果保存为 `待审核候选设备`。
9. 抽屉的 `待入库设备` 页签展示这些候选设备。
10. 用户点击 `入设备清单`。
11. 后端将候选设备映射到现有 Device V2 ingest。
12. 设备进入 Device V2 正式清单，状态为 `已入清单，待采集`。
13. 用户继续复用现有页面上的 `采集` 动作，进入真实采集与存储链路。

## Recommended Architecture

### Boundary

系统边界固定为：

- `OneOps 中心侧`
  - 计划管理
  - 范围校验
  - `function_area` 选择
  - controller 路由
  - 结果持久化
  - 审核与入库编排
- `controller`
  - 扫描执行
  - 并发控制
  - 超时与取消
  - 结果解析
  - 进度与完成回传
- `nmap`
  - 主机发现
  - 少量管理端口探测
  - 基础 service/version 识别

### Principle

`nmap` 只负责“发现谁在那儿”，不负责正式资产建档；Device V2 仍然是资产真相来源，扫描结果必须先经过审核后才能进入正式设备清单。

## Data Model

### DiscoveryPlan

用于承接抽屉中的 `探测计划`。

建议字段：

- `code`
- `name`
- `function_area`
- `scope_type`：`single_ip | ip_range | cidr`
- `scope_text`
- `exclude_text`
- `port_profile`
- `enabled`
- `schedule`
- `last_run_at`
- `last_run_status`

### DiscoveryRun

用于承接抽屉中的 `执行记录`。

建议字段：

- `code`
- `plan_code`
- `function_area`
- `controller_id`
- `controller_url`
- `requested_scope`
- `normalized_targets`
- `status`：`queued | dispatching | running | parsing | completed | failed | cancelled`
- `started_at`
- `completed_at`
- `discovered_count`
- `candidate_count`
- `error_message`
- `raw_result_ref`

### DiscoveryCandidate

用于承接抽屉中的 `待入库设备`。

建议字段：

- `code`
- `run_code`
- `function_area`
- `ip`
- `hostname`
- `alive`
- `open_ports`
- `service_fingerprints`
- `platform_hint`
- `model_hint`
- `summary`
- `review_status`：`pending_review | ignored | approved`
- `ingest_status`：`not_ingested | ingesting | ingested | duplicate_existing | ingest_failed`
- `device_v2_code`
- `dedupe_key`
- `observed_at`

## Data Flow

### 1. Plan Creation

前端保存 `DiscoveryPlan`。首期可以先支持“手工执行计划”，定时调度字段保留但不要求首批上线。

### 2. Run Creation

点击 `立即执行` 后：

1. 后端校验 `function_area` 必填。
2. 校验输入类型属于 `single_ip / ip_range / cidr`。
3. 规范化范围与排除范围。
4. 计算最终目标集合。
5. 校验最大地址数。
6. 创建 `DiscoveryRun`，状态设为 `queued`。
7. 解析对应 controller 并下发执行。

### 3. Controller Execution

controller 接收请求后，执行两阶段扫描：

1. `host discovery`
   - 先找出存活主机
2. `service probe`
   - 仅对存活主机继续扫描少量管理端口

首期推荐能力：

- `nmap -sn` 用于主机发现
- 对存活主机扫描少量管理端口
- 使用 `-sV` 做基础 service/version 探测

首期默认不支持：

- 全端口扫描
- 激进扫描
- 大规模 `NSE`
- OS 探测
- traceroute

### 4. Result Parsing

controller 应使用结构化输出并在本地完成解析。首期推荐 `XML` 作为 `nmap` 输出格式。

controller 将解析后的标准结果回传给 OneOps，OneOps 写入 `DiscoveryCandidate`，并更新 `DiscoveryRun` 汇总字段。

### 5. Review And Ingest

用户在 `待入库设备` 中点击 `入设备清单` 后：

1. 后端先按 `function_area + in_band_ip` 查重。
2. 若已存在 Device V2：
   - 标记 candidate 为 `duplicate_existing`
   - 不重复建设备
3. 若不存在：
   - 将 candidate 映射为 `DeviceV2 ingest` 请求
   - `source_type` 固定为 `network_scan`
   - metadata 补充：
     - `discovery_run_code`
     - `discovery_candidate_code`
     - `discovery_plan_name`
     - `discovery_source = nmap`
4. ingest 成功后，candidate 状态改为 `ingested`
5. 新设备在 Device V2 页面上显示为 `已入清单，待采集`

### 6. Collection

“入设备清单”和“采集”分成两个独立动作：

- `扫描发现 -> 入设备清单`
- `设备清单 -> 发起采集`

首期不做“扫描后自动采集”，以避免误判结果直接进入正式采集链路。

## Frontend Design

### Device Discovery Drawer

保留当前抽屉结构：

- `计划详情`
- `执行记录`
- `待入库设备`

但做这些调整：

- 首期只真实支持 `网段探测`
- `设备种子` 不进入首批真实范围
- `function_area` 成为必填字段
- `subnetTargets / excludeTargets / 端口策略` 使用真实接口
- 移除本地 `simulateDiscoveryExecution(...)`
- 执行状态、结果列表和入库动作全部改为读取后端真实数据

### Device V2 Management Page

保留当前主页面入口和整体旅程，但移除 demo 特判逻辑：

- 不再依赖本地 `localStorage` 的 `discovery demo state`
- 不再将“设备探测来源设备”当成本地伪设备处理
- `入设备清单` 改为真实 ingest
- `采集` 继续走现有真实 collect/store API

## Controller Design

### Internal Responsibilities

controller 建议拆分为四类责任：

- `DiscoveryTaskReceiver`
- `NmapExecutor`
- `NmapResultParser`
- `DiscoveryResultReporter`

这样后续增加 `ARP`、`SNMP` 或邻居发现时，可以在现有 discovery 结构上增量扩展，而不是重写 controller 主流程。

### Interface Semantics

至少需要三类语义：

- `StartDiscoveryRun`
- `ReportDiscoveryProgress`
- `CompleteDiscoveryRun`

通信方式可遵循现有 controller 体系，不强制限定为 HTTP 或 RPC，但运行态必须支持：

- run 状态可见
- 失败原因可回传
- 可取消
- 可限流

## Validation Rules

首期规则固定如下：

- 仅支持 `IPv4`
- 必须手工选择 `function_area`
- 每次扫描限制最大地址数
- 排除范围在最终目标集合上生效
- 前端不能直接传入原始 `nmap` 参数
- `nmap` 命令参数必须由后端白名单生成
- 同一 controller 上必须限制 discovery 并发 run 数
- run 必须支持超时和取消

## Error Handling

### User-Level Errors

这些错误直接在前端表单或 run 状态中暴露：

- 缺少 `function_area`
- 范围格式非法
- 超过最大地址数
- 目标集合为空
- controller 未找到
- controller 不在线

### Execution Errors

这些错误进入 `DiscoveryRun.error_message`，并在执行记录中可见：

- `nmap` 不存在或不可执行
- 扫描超时
- controller 进程取消
- XML 解析失败
- 结果回传失败

### Ingest Errors

这些错误写入 `DiscoveryCandidate.ingest_status`：

- 设备已存在
- ingest 校验失败
- ingest 调用失败

## Testing Strategy

### Backend

- 范围解析测试：
  - 单 IP
  - IP range
  - CIDR
  - 排除范围
  - 最大地址数限制
- 查重测试：
  - 同 `function_area + IP` 命中既有设备
  - 不命中时成功创建 ingest 请求
- 状态机测试：
  - `queued -> running -> completed`
  - `queued -> failed`
  - `pending_review -> ingested`

### Controller

- `nmap` 命令构造测试
- `nmap XML` 解析测试
- 超时/取消测试
- 进度上报测试

### Frontend

- 抽屉真实接口接入测试
- 执行记录刷新测试
- 待入库设备列表测试
- “入设备清单”与“采集”分阶段动作测试

### End-To-End

至少完成一条真实验收链路：

1. 创建 `CIDR + function_area` 计划
2. controller 执行真实 `nmap`
3. 前端展示真实 candidate
4. 用户确认 `入设备清单`
5. 新设备进入 Device V2 管理页
6. 用户继续发起真实采集

## Implementation Phases

### Phase 1: OneOps Discovery Backbone

先实现：

- `DiscoveryPlan / DiscoveryRun / DiscoveryCandidate`
- 相关 API
- 范围校验
- 去重
- 与 Device V2 ingest 的映射

### Phase 2: Controller Nmap Execution

再实现：

- discovery 执行入口
- `nmap` 两阶段扫描
- XML 解析
- 进度和完成回传

### Phase 3: Frontend Reality Pass

最后替换前端 demo：

- `DeviceDiscoveryDrawer.vue`
- `DeviceV2ManagementGrouped.vue`
- discovery API 封装
- 下线本地模拟状态

### Phase 4: E2E Validation

完成真实环境联调与验收，确认整条链路从扫描到 Device V2 采集均可执行。

## Decision Summary

本设计固定以下决策：

- 扫描执行放在 controller
- 首期扫描引擎固定为 `nmap`
- 用户必须手工选择 `function_area`
- 首期只做 `扫描 -> 审核入清单 -> 再采集`
- 扫描结果必须先落为 `DiscoveryCandidate`
- 正式资产仍以 Device V2 为唯一真相来源
- 首期前端尽量沿用当前 demo 交互，但全部替换为真实接口和真实状态
