---
topic: device-v2-management-ops-closure
kind: full-stack
title: Device V2 采集与监控链路研究
createdAt: 2026-05-21T02:08:00+0800
---

# Device V2 采集与监控链路研究

## 1. 研究目的

这份文档只回答一个问题：

- `采集` 在旧页面和后端里到底是什么能力、怎么执行、怎么承接结果
- `推送监控` 在旧页面和后端里到底是什么能力、怎么执行、怎么承接结果

目标不是复刻旧页，而是先把真实能力边界认识清楚，再决定当前 `DeviceV2ManagementGrouped.vue` 应该如何重新规划，避免：

- 把两个不同性质的动作当成同一个模型处理
- 把旧页的偶然 UI 交互误当成后端真实契约
- 因为怕复杂而丢掉关键能力
- 因为怕漏掉而把当前页重新做回“重工作台”

## 2. 当前真实代码事实

### 2.1 当前页实际调用

当前新页的动作非常轻：

- 采集：直接调用 `startDeviceV2StorePipelineReq`
  - 代码：[DeviceV2ManagementGrouped.vue](/Users/huangliang/project/OneOPS-ALL/OneOps-UI/src/views/device/DeviceV2ManagementGrouped.vue:2039)
- 监控：直接调用 `syncDeviceV2ToV1Req({ monitor_push: true })`
  - 代码：[DeviceV2ManagementGrouped.vue](/Users/huangliang/project/OneOPS-ALL/OneOps-UI/src/views/device/DeviceV2ManagementGrouped.vue:2076)

当前页缺少的不是按钮，而是结果承接：

- 采集只返回“任务已创建”
- 监控只返回一条摘要 notice
- 没有把 `task summary / process result / item 级结果 / 最后一次 DC2 采集记录` 接起来

### 2.2 后端当前对这两类动作的契约并不相同

采集和监控不是一个模型：

- `采集`：异步任务型
  - 入口：`POST /device/v2/store/start`
  - 读取：`GET /device/v2/tasks/:taskId`
  - 摘要：`GET /device/v2/tasks/:taskId/summary`
  - 明细：`GET /device/v2/tasks/:taskId/runs`
  - 判断事实：`GET /device/v2/tasks/:taskId/observations`
  - 后续采集计划：`GET /device/v2/tasks/:taskId/collection-plans`
  - 最近一次 DC2：`GET /device/v2/:code/last-store-collection-dc2`
- `推送监控`：同步聚合结果型
  - 入口：`POST /device/v2/sync-to-v1`
  - 返回：批量结果 + `monitor_push_status / monitor_push_error / items`
  - 并没有当前页可直接复用的“监控推送任务详情接口”

路由证据：

- [device_v2.go](/Users/huangliang/project/OneOPS-ALL/OneOps/app/device/v2/router/device_v2.go:11)

## 3. 旧页面中的“采集”到底是什么

### 3.1 旧页入口不是一个简单按钮

旧页“继续入库”实际上是 `store/start` 的前端包装器，不只是“发起采集”。

它在单设备场景里允许用户配置：

- 采集目标 `IP / Host`
- 是否使用已绑定凭证，还是本次手工覆盖
- SNMP 参数
- SSH 参数
- MIB tree file
- 是否异步
- 是否启用 `Device Collection2` 基线采集

代码证据：

- 入口与表单：[DeviceV2Management.vue](/Users/huangliang/project/OneOPS-ALL/OneOps-UI/src/views/device/DeviceV2Management.vue:1240)
- 请求拼装：[DeviceV2Management.vue](/Users/huangliang/project/OneOPS-ALL/OneOps-UI/src/views/device/DeviceV2Management.vue:4001)

### 3.2 旧页批量采集和单设备采集不是同一种强度

旧页已经做了一个很重要的限制：

- 批量采集不支持统一覆盖凭证
- 批量采集只使用每台设备自身已保存的接入地址和绑定凭证

这说明旧页实际上已经默认：

- 单设备可以做“带人工干预的执行”
- 批量只能做“低风险批量触发”

这是一个应当保留的规划原则，不宜反向简化。

### 3.3 旧页结果承接非常重

旧页采集结果抽屉会承接这些层次：

- 任务状态
- 结果摘要
- 基础入库
- 设备采集证据
- 后续可采集数据
- 判断依据
- 连通性检查
- 设备检测
- 动作执行结果
- DC2 基线采集
- 基础入库结果

代码证据：

- 结果抽屉结构：[DeviceV2Management.vue](/Users/huangliang/project/OneOPS-ALL/OneOps-UI/src/views/device/DeviceV2Management.vue:1480)
- 任务明细加载：[DeviceV2Management.vue](/Users/huangliang/project/OneOPS-ALL/OneOps-UI/src/views/device/DeviceV2Management.vue:4072)

### 3.4 旧页“采集”的本质结论

旧页里的“采集”不是一个窄动作，而是一条：

- 前置检查
- 执行参数确认
- store pipeline 触发
- task summary / runs / observations 承接
- DC2 证据下钻

的完整链路。

所以如果新页只保留“采集按钮 + 已创建任务”，那不是简化，而是丢能力。

## 4. 后端中的“采集”到底返回什么

### 4.1 任务摘要是已经被整理过的，不需要前端自己硬拼

后端 `GetTaskSummary` 已经把任务聚合成了：

- `layers`
  - `core_store`
  - `collection_execution`
  - `collection_gap`
  - `observation_facts`
- `process_result`
  - `overall_status`
  - `headline`
  - `summary`
  - `steps`
- `highlights`
- `batch_overview`

代码证据：

- [GetTaskSummary](/Users/huangliang/project/OneOPS-ALL/OneOps/app/device/v2/api/device_v2.go:681)
- [buildMinimalStoreTaskSummary](/Users/huangliang/project/OneOPS-ALL/OneOps/app/device/v2/api/device_v2_store_minimal_api.go:535)

### 4.2 后端已经内置了“采集过程结果”语义

`process_result.steps` 至少拆了三步：

- `prepare`
- `run_collection`
- `persist_result`

每一步都已经有：

- `status`
- `error_code`
- `user_message`
- `operator_message`
- `next_action`
- `retryable`
- `details`

代码证据：

- [buildMinimalStoreRunProcessResult](/Users/huangliang/project/OneOPS-ALL/OneOps/app/device/v2/api/device_v2_store_minimal_api.go:612)
- [buildCollectPrepareStep](/Users/huangliang/project/OneOPS-ALL/OneOps/app/device/v2/api/device_v2_store_minimal_api.go:649)
- [buildCollectExecutionStep](/Users/huangliang/project/OneOPS-ALL/OneOps/app/device/v2/api/device_v2_store_minimal_api.go:699)
- [buildCollectPersistStep](/Users/huangliang/project/OneOPS-ALL/OneOps/app/device/v2/api/device_v2_store_minimal_api.go:740)

### 4.3 “最后一次采集详细数据”不是虚构需求，后端确实有落点

后端已经提供：

- 最近一次含 `dc2_run_id` 的 store run 定位
- 返回 `task_id / store_run_id / dc2_run_id / contract_key / target_id`

代码证据：

- [GetLastStoreCollectionDC2](/Users/huangliang/project/OneOPS-ALL/OneOps/app/device/v2/api/device_v2_store_minimal_api.go:407)

所以“查看最后一次采集详细数据”的合理实现应该是：

1. 先用 `last-store-collection-dc2` 判断是否存在最近采集
2. 再结合 `task summary / runs / observations`
3. 必要时跳到 DC2 run 详情或承接 DC2 run 信息

而不是自己拼一个假的“最近采集结果对象”。

### 4.4 后端还会把采集过程结果持久化到设备本身

`GetTaskSummary` 里会对每台设备调用 `persistDeviceV2ProcessResult`

这意味着：

- `process_result` 不只是任务详情里的临时结果
- 它也会回写到设备 `attributes / metadata`

代码证据：

- [GetTaskSummary](/Users/huangliang/project/OneOPS-ALL/OneOps/app/device/v2/api/device_v2.go:700)
- [persistDeviceV2ProcessResult](/Users/huangliang/project/OneOPS-ALL/OneOps/app/device/v2/api/device_v2_sync_to_v1.go:1248)

这对新页非常重要：右侧详情的“简明复核”可以直接读设备上的持久化结果，不一定每次都必须从 task 重新聚合。

## 5. 旧页面中的“推送监控”到底是什么

### 5.1 旧页监控入口非常轻

旧页批量监控本质上只做了这件事：

- 调 `syncDeviceV2ToV1Req({ codes, monitor_push: true })`

然后展示：

- 新增 / 回填 / 跳过 / 失败数量
- `monitor_push_status`
- `monitor_push_error`

代码证据：

- 入口：[DeviceV2Management.vue](/Users/huangliang/project/OneOPS-ALL/OneOps-UI/src/views/device/DeviceV2Management.vue:5161)
- 摘要文案：[DeviceV2Management.vue](/Users/huangliang/project/OneOPS-ALL/OneOps-UI/src/views/device/DeviceV2Management.vue:2979)

这说明旧页在“推送监控”上并没有和采集对等的结果明细系统。

### 5.2 旧页监控其实混合了两件事

这个动作不是纯“监控下发”：

1. 先同步到 `Device V1`
2. 同步成功后再推送监控任务

所以旧页里“监控”返回的失败，可能来自两类完全不同的问题：

- `sync-to-v1` 失败
- `monitor push` 失败

如果新页不把这两层分开，运维只能看到“监控失败”，但不知道该去修 V1 桥接还是修监控推送。

## 6. 后端中的“推送监控”到底是什么

### 6.1 当前主入口仍然是 `sync-to-v1`

后端 `SyncToV1` 的真实逻辑是：

1. 逐台执行 `syncOneDeviceV2ToV1`
2. 收集成功的 `device_v1_code`
3. 若 `monitor_push=true`，再调用 `NotifyMonitorProbeByDeviceCodes`
4. 汇总返回：
   - `created / updated / skipped / failed`
   - `monitor_push_status`
   - `monitor_push_error`
   - `items`

代码证据：

- [SyncToV1](/Users/huangliang/project/OneOPS-ALL/OneOps/app/device/v2/api/device_v2_sync_to_v1.go:181)

### 6.2 监控结果会回写到设备

后端会持久化：

- `monitor_push_status`
- `monitor_push_error`
- `monitor_push_at`

代码证据：

- [persistDeviceV2SyncToV1MonitorResult](/Users/huangliang/project/OneOPS-ALL/OneOps/app/device/v2/api/device_v2_sync_to_v1.go:1230)

这意味着新页右栏、列表、筛选都可以基于设备自身状态来表达“监控未下发 / 已下发 / 下发失败”。

### 6.3 后端其实还有更结构化的监控纳管链路

除了 `sync-to-v1`，后端还提供了：

- `GET /device/v2/:code/onboarding`
- `POST /device/v2/:code/onboarding/plan`
- `POST /device/v2/:code/onboarding/ensure`
- batch onboarding plan / ensure

这个 onboarding 契约包含：

- `actions`
- `blocked_actions`
- `failed_actions`
- `retryable_actions`
- `require_monitor_mode`
- `monitor_mode_options`

代码证据：

- 类型：[device-v2.ts](/Users/huangliang/project/OneOPS-ALL/OneOps-UI/src/api/device/device-v2.ts:245)
- 组装返回：[device_v2_onboarding_api.go](/Users/huangliang/project/OneOPS-ALL/OneOps/app/device/v2/api/device_v2_onboarding_api.go:519)
- 监控 ensure：[device_v2_onboarding_api.go](/Users/huangliang/project/OneOPS-ALL/OneOps/app/device/v2/api/device_v2_onboarding_api.go:1942)

### 6.4 这意味着“推送监控”其实存在两种前端接法

接法 A：轻量沿用 `sync-to-v1`

- 优点：当前页最容易接，和现有行为一致
- 缺点：只有批量聚合结果，没有 action 级结构化反馈，也没有 `monitor_mode` 规划能力

接法 B：单设备走 `onboarding plan/ensure`

- 优点：能拿到 `blocked / failed / retryable / require_monitor_mode`
- 缺点：会把“监控动作”升级成更重的纳管控制流，需要更谨慎地落在当前页

这也是为什么当前页不能想当然地把“监控”直接做成一个和“采集详情”一样重的结果体系。

## 7. 当前页重新规划时必须尊重的真实边界

### 7.1 采集和监控不能共用一个结果承载模型

采集：

- 有 task id
- 有 summary / runs / observations / collection plans
- 可以形成“详细数据查看”

监控：

- 当前主入口没有 task detail
- 主要是同步结果 + monitor push 聚合状态
- 更适合设备级状态回写 + 失败原因 + item 级摘要

### 7.2 单设备与批量动作不能做成同一深度

真实代码已经说明：

- 单设备采集可有更深参数和更深复核
- 批量采集应尽量轻，不做统一凭证覆盖
- 批量监控更适合聚合摘要 + 失败设备归因

### 7.3 新页不该把旧页重搬过来

旧页重在“任务结果工作台化承接”。

当前页应保留设备管理叙事，只把真正高价值的层次迁过来：

- 设备级复核摘要
- 失败原因
- 下一步建议
- 最后一次采集详细数据入口
- 批量动作的结果归属

不应迁入：

- 大量流程性阶段文案
- 强工作台感的任务大厅结构
- 需要用户在当前页长期盯任务刷新的厚交互

## 8. 面向当前页的重新规划

## 8.1 采集：推荐采用“两段式”

### 第一段：默认轻触发

适用：

- 列表批量采集
- 单设备已具备接入地址与凭证

行为：

- 直接触发 `store/start`
- 保持当前上下文
- 右侧详情刷新简明复核
- 若有 `task_id`，记录为最近采集任务上下文

### 第二段：必要时进入“高级采集”

只在这些场景出现：

- 单设备缺少采集目标
- 单设备缺少凭证
- 用户主动选择高级采集
- 后端 `process_result.next_action` 指向需要补充采集条件

承载建议：

- 不恢复旧页整块大弹窗为默认入口
- 但应保留一个“高级采集参数”入口
- 参数范围以旧页已证明有用的字段为上限，不继续扩张

这样既不丢掉关键救急能力，也不让正式页默认变重。

## 8.2 采集结果：右侧简明复核 + 独立详细数据查看

右侧详情只承接：

- 最近采集结论
- 当前采集状态
- 失败摘要
- 下一步建议
- “查看最后一次采集详细数据”入口

独立详细查看层承接：

- task summary layers
- process_result.steps
- runs
- observations
- collection plans
- 最近一次 DC2 run 关联信息

这是当前页最稳的平衡点。

## 8.3 监控：设备级复核优先，不做伪任务详情

第一批建议仍沿用 `sync-to-v1 + monitor_push` 作为执行入口，但设计上必须补三件事：

1. 区分 `sync-to-v1` 失败和 `monitor push` 失败
2. 把 item 级失败设备与失败原因挂回当前列表/右栏
3. 设备上持续展示 `monitor_push_status / error / at`

不建议第一批做：

- 虚构一个不存在的“监控任务详情”
- 把监控也套进采集式 task drawer

## 8.4 单设备监控的增强方向

若后续确认要支持更结构化的监控准备与模式选择，建议只对单设备引入：

- `onboarding/plan`
- `onboarding/ensure`

适用场景：

- 需要 `monitor_mode`
- 需要区分 blocked / failed / retryable
- 需要更强的运维判断语义

但这应作为受控增强，不应在第一批把所有监控交互整体切走。

## 8.5 并发设计必须分动作类型

采集并发关注：

- 同设备重复采集
- 批量采集过程中再次触发采集
- 最近 task 与当前 task 的归属

监控并发关注：

- 同设备重复监控推送
- 批量监控返回后与设备最新状态是否一致
- `sync-to-v1` 成功但 `monitor push` 失败的归属

两者不应共用一套笼统“动作进行中”状态。

## 9. 重规划建议

### 设计总原则

旧页里已经积累了很多采集、监控推送相关的过程数据，这些数据对排查问题非常重要，不能因为新页不想做成“操作台”就直接丢掉。

但这些数据也不应默认暴露在主页面常驻区域，否则会带来两个反作用：

- 设备管理页会重新退化成任务/过程工作台
- 高频用户在日常找设备、改信息、做简单动作时会被大量低频排障信息打断

所以第一原则不是“删掉过程数据”，而是：

- `保留数据`
- `收起默认暴露`
- `在需要排查时快速下钻`

更具体地说，新页应采用“分层承接”：

1. 主页面只承接判断结果
2. 右侧详情承接简明复核
3. 独立查看层承接排障数据
4. 真正超深的原始过程数据继续沿用原有入口或跳转

### 必做

1. 右侧详情增加设备级动作复核摘要
2. 接入 `process_result` 与 `monitor_push_status/error`
3. 采集增加“最后一次采集详细数据”查看层
4. 批量监控结果必须区分同步失败与监控失败
5. 并发状态表达按“采集中 / 监控推送中 / 两者并存”拆开

### 应做

1. 单设备采集保留“高级采集参数”后门
2. 批量动作结果支持回流筛选失败设备
3. 列表保持普通设备列表，不额外增加“下一步处理信号”

### 暂缓

1. 不把 onboarding 全量搬进第一批监控交互
2. 不把旧页整套采集结果工作台照搬进当前页
3. 不为监控伪造 task 详情概念

## 10. 数据分层承接建议

### 10.1 主页面层

主页面只放正常设备列表需要的信息：

- 当前监控状态
- 最近更新时间
- 基础设备信息

不放：

- 大段过程明细
- observation 列表
- collection plan 全量表
- 大量 controller / DC2 原始字段

### 10.2 右侧详情层

右侧详情承接“简明复核”，应该回答：

- 这台设备最近发生了什么
- 结果是成功、失败还是阻塞
- 失败大概因为什么
- 我下一步该怎么做

适合放：

- 采集结果 headline / status / next action
- 监控推送状态、失败原因摘要
- 最近一次采集是否存在真实 DC2 证据
- 一两个最关键的补救建议

不适合放：

- 大表格化的 observations
- 全部 runs
- 大段 JSON
- 所有 collection gap 明细

### 10.3 独立查看层

独立查看层就是“问题排查层”，它的价值不是日常浏览，而是：

- 当用户真的需要排查时，不必离开当前页重新找上下文

采集侧可承接：

- task summary layers
- process_result steps
- runs
- observations
- collection plans
- 最近一次 DC2 run 关联信息

监控侧第一批建议承接：

- 本次批量 / 单设备动作返回的 item 级结果
- `sync-to-v1` 结果
- `monitor_push_status / error`

如果未来再增强，再考虑引入单设备 `onboarding` 结构化视图。

### 10.4 深链接 / 原有入口层

对于真正偏平台侧、任务侧、控制器侧的超深数据，不建议全部在当前页重建。

应该保留：

- 跳转旧有详情入口
- 跳转 DC2 run 详情
- 跳转更专业的结果页

这样做的好处是：

- 设备管理页仍然保持克制
- 关键排障数据没有丢
- 专业问题仍然能落回最合适的页面

## 11. 对 PRD 的直接影响

新的 PRD 不应再把“采集”和“监控”统称为一个动作闭环，而应拆成：

- `采集闭环`
  - store/start
  - process_result
  - last-store-collection-dc2
  - 详细数据查看
- `监控闭环`
  - sync-to-v1
  - monitor_push_status/error
  - item 级失败归因
  - 后续必要时再引入 onboarding

这会让当前页既不失真，也不会过度复杂。
