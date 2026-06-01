---
topic: device-v2-management-ops-closure
kind: frontend
title: Device V2 设备管理页交互方案稿
createdAt: 2026-05-21T02:24:00+0800
---

# Device V2 设备管理页交互方案稿

## 1. 目标

这份方案稿只解决一个问题：

- 在不把页面做回“操作台”的前提下，如何把采集、监控推送相关的高价值结果和排障数据，合理地承接进当前设备管理页。

目标页面仍然是：

- 左侧：设备分组
- 中间：设备清单
- 右侧：设备详情

不改变页面主叙事，不增加副标题，不回退到工作台式页面。

## 2. 交互总原则

### 2.1 分层承接

页面采用四层承接：

1. 列表层：保持普通设备列表
2. 右侧详情层：给简明复核
3. 独立查看层：给排障数据
4. 深链接层：给更专业、更深的原始结果入口

### 2.2 默认克制，按需下钻

默认不展示：

- 大段过程数据
- 全量 observations
- 全量 collection plans
- 大块 JSON
- 强过程导向阶段信息

默认展示：

- 普通设备列表所需字段
- 当前监控状态
- 常规操作入口
- 明确的查看详情入口

### 2.3 采集与监控分开设计

采集：

- 结果中心是 `task / process_result / runs / observations`
- 适合“简明复核 + 查看详细数据”

监控：

- 结果中心是 `sync-to-v1` item 结果 + `monitor_push_status/error`
- 适合“设备级状态回写 + 失败归因 + 必要时查看本次结果”

不能共用同一套结果 UI 模型。

## 3. 页面层级设计

## 3.1 列表层

列表层就是正常的设备列表页，不承担“下一步处理引导”职责。

所有需要进一步动作处理的设备，统一通过：

- `监控未下发` 清单

进入，而不是在列表中额外设计一套“待处理 / 可继续 / 有风险”的信号体系。

### 建议保留的主列

1. 设备
2. 设备类型
3. 位置
4. 监控状态
5. 最近更新时间
6. 操作

当前页已经接近这个结构，不需要大改列数。

### 建议调整点

#### 监控状态列

显示优先级：

1. `监控已下发`
2. `监控推送失败`
3. `监控下发中`
4. `监控未下发`

辅助信息只放一行短文案，例如：

- `已写回监控状态`
- `V1 同步失败`
- `监控推送失败`
- `待执行监控`

不要在列表里直接暴露整段错误文本。

#### 最近更新时间列

只承担普通列表字段职责：

- 显示真实最近更新时间
- 清理零值时间
- 不叠加过程状态文案

#### 操作列

仍然保留：

- 详情
- 编辑
- 采集
- 监控

列表层不额外承担“为什么该点哪个动作”的引导职责。

### 列表层禁止项

- 不展示 observation 条数
- 不展示 collection plan 全量项数
- 不展示过程步骤
- 不展示长错误堆栈
- 不展示大段编码信息
- 不展示“下一步建议”
- 不展示“可继续处理 / 需补资料 / 存在失败”这类流程性信号

## 3.2 右侧详情层

右侧详情是“简明复核面板”，不是结果中心。

建议分 5 块。

### 块 1：设备头部

保留：

- 设备名称
- 设备编码
- 当前监控状态 tag
- 一句简短状态说明

状态说明示例：

- `最近采集有记录`
- `监控尚未下发`
- `监控推送失败`

### 块 2：基础信息

保留当前模式，但改成名称优先、编码退后。

### 块 3：采集复核

这块是右栏最重要的新内容之一。

建议字段：

1. 最近采集结论
2. 最近采集时间
3. 采集状态
4. 简短说明
5. 查看最后一次采集详细数据入口

展示示例：

- `最近采集结论：采集被阻塞`
- `原因：缺少访问凭据`
- `说明：需要补充访问凭据`

如果存在最近一次 DC2 记录：

- 出现 `查看最后一次采集详细数据`

如果不存在：

- 不出现入口

### 块 4：监控复核

这块需要明确拆开两个失败来源：

1. V1 同步结果
2. 监控推送结果

建议字段：

1. 当前监控状态
2. 最近一次推送结果
3. 失败原因摘要
4. 简短说明
5. 如本次动作刚执行，允许查看“本次监控结果”

展示示例：

- `当前监控状态：未下发`
- `最近结果：V1 同步失败`
- `原因：缺少机柜信息`
- `说明：需先补齐位置信息`

或：

- `当前监控状态：推送失败`
- `最近结果：监控任务已创建失败`
- `原因：monitor push 返回错误`
- `说明：请检查监控推送配置`

### 块 5：设备操作

仍然只放：

- 采集
- 监控
- 编辑

但按钮下可出现很轻的上下文提示：

- 采集：`最近失败，可重试`
- 监控：`缺少前提，建议先编辑`

不要把按钮区变成操作导航墙。

## 3.3 独立查看层

建议拆成两个查看层，而不是一个万能结果抽屉。

### A. 最后一次采集详细数据抽屉

入口：

- 右侧详情“查看最后一次采集详细数据”

标题建议：

- `最后一次采集详细数据`

信息结构建议：

1. 顶部摘要
2. 过程结论
3. 设备采集证据
4. 判断事实
5. 后续可采集项
6. 深链接

#### 顶部摘要

展示：

- task id
- store run id
- dc2 run id
- overall status
- headline

#### 过程结论

来源：

- `process_result.steps`

只展示 3 步：

1. 前置准备
2. 执行采集
3. 写入结果

每步展示：

- 状态
- 用户可读信息
- 下一步建议

#### 设备采集证据

来源：

- `layers.collection_execution`
- `last-store-collection-dc2`

只展示摘要：

- 是否执行 DC2
- 是否有 run id
- 是否有事实写入
- 关键 message

#### 判断事实

来源：

- observations

默认不展示全部，只展示：

- 总数
- 关键 capability 分布
- 关键字段样本

并提供“展开更多”或分页表格。

#### 后续可采集项

来源：

- collection plans

默认只展示：

- 总数
- 当前可执行数
- 第一条 next action

再允许展开明细表。

#### 深链接

若存在 `dc2_run_id`：

- 提供 `查看 DC2 运行详情`

不要在当前页重建完整 DC2 专业视图。

### B. 本次监控结果抽屉

入口：

- 只在用户刚执行过单设备或批量监控后出现
- 或右侧详情中存在最近一次失败结果时出现“查看本次结果”

标题建议：

- 单设备：`本次监控结果`
- 批量：`批量监控结果`

信息结构建议：

1. 顶部汇总
2. 失败归因
3. 设备结果列表

#### 顶部汇总

来源：

- `syncDeviceV2ToV1Req` 返回体

展示：

- 总数
- created
- updated
- skipped
- failed
- monitor_push_status

#### 失败归因

明确拆开：

- `V1 同步失败`
- `monitor push 失败`

不要只给一条总错误。

#### 设备结果列表

来源：

- `items`

每台只展示：

- 设备编码 / 名称
- 同步结果
- 监控结果
- message

支持一键把失败设备回流筛选到当前列表。

## 3.4 深链接层

只处理当前页不适合承载的深数据。

建议保留深链接：

1. `查看 DC2 运行详情`
2. `查看更完整采集结果`
3. 未来若存在专业监控结果页，可跳转过去

原则是：

- 当前页解决设备管理
- 深页面解决专业排障

## 4. 动作流程设计

## 4.1 单设备采集

### 默认路径

1. 用户点 `采集`
2. 若设备具备基础条件，直接快速发起
3. 右侧详情刷新为 `采集中`
4. 采集完成后，右侧刷新结论
5. 若需要排障，点击 `查看最后一次采集详细数据`

### 条件不足路径

1. 用户点 `采集`
2. 页面识别缺少接入目标或凭证
3. 不直接提示“失败结束”
4. 引导进入 `高级采集参数` 或编辑修正

## 4.2 批量采集

1. 用户在列表选择设备
2. 点 `批量采集`
3. 弹确认框，明确说明只使用设备已保存接入信息
4. 发起任务
5. 列表中对应设备出现 `采集中`
6. 批量不自动展开大结果面板
7. 用户如需排障，可从具体设备右栏进入详细数据

## 4.3 单设备监控

1. 用户点 `监控`
2. 发起 `sync-to-v1 + monitor push`
3. 右侧详情刷新监控复核
4. 若失败，明确区分：
   - V1 同步失败
   - monitor push 失败
5. 如是当前动作触发，可点 `查看本次监控结果`

## 4.4 批量监控

1. 用户选择设备
2. 点 `批量监控`
3. 发起 `sync-to-v1 + monitor push`
4. 页面顶部只给一条摘要 notice
5. 同时生成一个可再次打开的 `批量监控结果` 查看入口
6. 列表设备状态更新
7. 失败设备可一键回流筛选

## 5. 并发与状态设计

## 5.1 设备级动作状态

建议统一成 4 种局部状态：

1. `idle`
2. `collect_running`
3. `monitor_running`
4. `collect_and_monitor_running`

状态作用范围：

- 列表操作按钮
- 右侧详情按钮
- 右侧复核文案

### 按钮规则

- `collect_running` 时禁用再次采集
- `monitor_running` 时禁用再次监控
- 另一类动作是否允许并发，要显式提示而不是默许

建议第一批：

- 同设备同类动作禁止重复触发
- 不强行禁止异类动作，但要明确显示另一动作正在进行

## 5.2 结果归属

必须能回答：

- 这次结果属于哪台设备
- 属于采集还是监控
- 是当前动作还是上一次动作

因此建议页面保存最近动作上下文：

- `device_code`
- `action_type`
- `task_id` 或动作返回体
- `started_at`

用于避免串台。

## 6. 文案策略

文案必须从“系统动作”转向“运维判断”。

推荐：

- `最近采集成功，但仍有数据待补采`
- `监控未下发，原因是缺少 V1 同步前提`
- `监控推送失败，建议先检查同步结果`
- `已存在最近采集记录，可查看详细数据`

避免：

- `任务已创建`
- `monitor push submitted`
- `查看结果`
- `过程结果`
- `推进`

## 7. 第一批实现边界

### 必须实现

1. 列表层字段与状态语义
2. 右侧采集复核块
3. 右侧监控复核块
4. 最后一次采集详细数据抽屉
5. 本次监控结果抽屉
6. 并发状态表达
7. 失败设备回流筛选

### 可以简化

1. 采集详细数据抽屉里的 observations 默认只展示摘要 + 少量样本
2. collection plans 默认只展示汇总 + 第一条建议
3. 监控结果抽屉第一批先用当前动作返回体，不额外补后端新接口

### 暂不做

1. 把 onboarding 全量引入主流程
2. 还原旧页整块结果工作台
3. 在主页面常驻展示深过程数据

## 8. 与代码的直接映射

### 采集相关

- 触发：`startDeviceV2StorePipelineReq`
  - [device-v2.ts](/Users/huangliang/project/OneOPS-ALL/OneOps-UI/src/api/device/device-v2.ts:653)
- 任务：`getDeviceV2StoreTaskReq`
  - [device-v2.ts](/Users/huangliang/project/OneOPS-ALL/OneOps-UI/src/api/device/device-v2.ts:748)
- 摘要：`getDeviceV2StoreTaskSummaryReq`
  - [device-v2.ts](/Users/huangliang/project/OneOPS-ALL/OneOps-UI/src/api/device/device-v2.ts:759)
- runs：`listDeviceV2StoreRunsReq`
  - [device-v2.ts](/Users/huangliang/project/OneOPS-ALL/OneOps-UI/src/api/device/device-v2.ts:772)
- observations：`listDeviceV2StoreObservationsReq`
  - [device-v2.ts](/Users/huangliang/project/OneOPS-ALL/OneOps-UI/src/api/device/device-v2.ts:822)
- plans：`listDeviceV2StoreCollectionPlansReq`
  - [device-v2.ts](/Users/huangliang/project/OneOPS-ALL/OneOps-UI/src/api/device/device-v2.ts:857)
- 最近 DC2：`getDeviceV2LastStoreCollectionDc2Req`
  - [device-v2.ts](/Users/huangliang/project/OneOPS-ALL/OneOps-UI/src/api/device/device-v2.ts:809)

### 监控相关

- 触发：`syncDeviceV2ToV1Req`
  - [device-v2.ts](/Users/huangliang/project/OneOPS-ALL/OneOps-UI/src/api/device/device-v2.ts:946)
- 结构化增强预留：`planDeviceV2OnboardingReq / ensureDeviceV2OnboardingReq`
  - [device-v2.ts](/Users/huangliang/project/OneOPS-ALL/OneOps-UI/src/api/device/device-v2.ts:692)

### 新页当前动作入口

- 采集： [DeviceV2ManagementGrouped.vue](/Users/huangliang/project/OneOPS-ALL/OneOps-UI/src/views/device/DeviceV2ManagementGrouped.vue:2031)
- 监控： [DeviceV2ManagementGrouped.vue](/Users/huangliang/project/OneOPS-ALL/OneOps-UI/src/views/device/DeviceV2ManagementGrouped.vue:2068)

## 9. 下一步建议

基于这份方案，字段级拆解已经继续沉淀到：

- [detail-and-drawer-spec.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/device-v2-management-ops-closure/detail-and-drawer-spec.md)

下一步可以直接进入实施顺序和 story 精修。
