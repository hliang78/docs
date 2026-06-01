---
topic: device-v2-management-ops-closure
kind: frontend
title: Device V2 错误协同 UI 承接方案
createdAt: 2026-05-21T13:10:00+0800
---

# Device V2 错误协同 UI 承接方案

## 1. 目标

这份文档只回答一个实现前问题：

- `DeviceV2ManagementRedesign.vue` 里，复杂链路错误具体放在哪展示
- 哪些区域承接采集失败
- 哪些区域承接继续纳管失败
- 哪些默认展示，哪些只在展开态显示

## 2. 当前页面锚点判断

### 2.1 采集失败主承接区

当前最佳承接点是：

- `store` 抽屉

代码锚点：

- [store drawer](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:636)

原因：

- 这里已经有任务上下文
- 已经能拿到 `task summary / runs / observations / plans / last-store-collection-dc2`
- 用户心智上也接受“采集详情”在这里看

### 2.2 单设备继续纳管失败主承接区

当前最佳承接点不是 toast，而是：

- 右侧详情的“最近结果”下方新增一块轻量结果承接区
- 必要时配合一个小型折叠面板或弹层

代码锚点：

- 右侧详情“最近结果”：[DeviceV2ManagementRedesign.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:280)

原因：

- 继续纳管是单设备动作
- 当前页执行后会保留 `selectedDevice`
- 用户需要的是“当前这台设备到底为什么没继续下去”，而不是再开一个大工作台

### 2.3 右侧详情不适合作为采集完整排障区

右侧详情应该继续保持：

- 简明复核

不适合：

- 承接整套 store 运行明细
- 默认展示大段原始 evidence
- 变成第二个采集抽屉

## 3. 采集失败 UI 方案

## 3.1 抽屉总体结构

建议在现有 `store` 抽屉中保留现有结构，但新增一个更靠前的区块：

1. 顶部 meta
2. hero 结论区
3. `失败承接卡`
4. process steps
5. diagnostics collapse
6. runs / observations
7. decision
8. raw

其中新增重点是第 3 块。

## 3.2 新增区块：失败承接卡

位置：

- 放在 hero 区下方
- 在 process steps 上方

显示条件：

- 当前结论不是成功
- 或存在明确失败 / blocked / unknown 线索

卡片内部固定分成 4 行：

1. `当前结果`
2. `当前阶段`
3. `优先核对项`
4. `证据锚点`

### 当前结果

示例：

- `本次采集未完成`
- `本次采集被阻塞`

来源：

- `storeValidationConclusion.title`
- `process_result.overall_status`

### 当前阶段

示例：

- `准备资料`
- `controller 探测`
- `执行采集`
- `写入结果`

来源优先级：

1. `process_result.steps` 中第一个非 success step
2. `selectedStoreRun.current_step`
3. `layers.collection_execution`

### 优先核对项

示例：

- `优先核对正式链路使用的带内凭据引用`
- `优先核对接入目标地址与登录方式`
- `优先补齐设备基础资料`

来源优先级：

1. 结构化规则映射
2. 后端未来可能补的 `next_check_items`
3. 保守降级文案

### 证据锚点

展示形式：

- 小号 key-value tags / fact chips

优先项：

- `credential_ref_in_band`
- `target_id`
- `contract_key`
- `snapshot_id`
- `store_run_id`
- `dc2_run_id`
- `dc2_reason`

展示规则：

- 最多默认展示 4 到 6 个
- 为空不展示
- 若值来自设备静态字段而非运行态，要加 `当前保存值` 标记

## 3.3 diagnostics 折叠区调整

当前已有：

- `diagnostics` collapse

建议保留，但角色变化为：

- 从“主要失败说明”
- 变成“扩展排障说明”

这一区更适合放：

- 详细阻断项
- 多条 next actions
- 更完整的 operator message

而不是第一眼就让用户从这里找结论。

## 3.4 runs / observations 区保持技术复核属性

这一区继续保留：

- run select
- observations
- execution facts

但不承担：

- 第一层错误解释

## 3.5 raw 区规则

继续保留原始 JSON，但：

- 默认收起
- 标题继续写 `排障用`
- 不允许主流程文案引用这里的长段 message 作为唯一解释

## 4. 单设备继续纳管 UI 方案

## 4.1 承接位置

建议在右侧详情新增一块：

- `继续处理结果`

位置：

- 放在 `最近结果` 后面
- 放在 `扩展资料` 前面

理由：

- 与设备当前动作最相关
- 不挤进基础信息区
- 用户执行“继续处理”后回看路径自然

## 4.2 区块结构

同样采用 4 行固定结构：

1. `当前结果`
2. `当前阶段`
3. `优先核对项`
4. `证据锚点`

外加两个动作：

- `查看原始结果`
- `重新获取结果`

## 4.3 当前结果

示例：

- `本次继续纳管未完成`
- `本次继续纳管已完成`

来源：

- `onboardingEvidence.overall_status`
- `actions / blocked_actions / failed_actions / unknown_actions`

## 4.4 当前阶段

来源优先级：

1. `controller_stage`
2. action label 推断
3. `sync_to_v1` / `monitor_push` 固定映射

示例：

- `controller 阶段`
- `同步到 V1`
- `监控推送`

## 4.5 优先核对项

来源：

- action `reason`
- action `message`
- 若含 `device_collection2`，则复用采集矩阵

关键要求：

- 这里不要只重复 toast 文案
- 要能稳定保留给用户回看

## 4.6 证据锚点

优先项：

- `task_id`
- `store_run_id`
- `controller_stage`
- `device_collection2.*`
- `decision.code`

## 4.7 原始结果查看方式

建议不是新开大抽屉，而是：

- 右侧区块内一个小折叠
- 或弹出小 modal

因为继续纳管结果通常比采集详情轻。

## 5. 列表与 toast 的角色

## 5.1 列表

列表继续只承担：

- 当前状态
- 当前情况
- 待处理

不承担：

- 复杂错误明细

## 5.2 toast

toast 只承担：

- 动作已触发
- 动作成功 / 失败的即时反馈

不承担：

- 完整失败说明

建议规则：

- toast 最多一句话
- 页面内区块负责完整复核

## 6. 默认展开策略

### 采集抽屉

默认展开：

- hero
- 失败承接卡
- process steps

默认收起：

- diagnostics
- decision
- raw

### 继续纳管结果

默认展示：

- 当前结果
- 当前阶段
- 优先核对项
- 证据锚点

默认收起：

- 原始 evidence

## 7. 当前最适合先实现的两块

1. `store` 抽屉失败承接卡
2. 右侧详情 `继续处理结果` 区块

这两块一旦做出来，就已经能显著改善：

- 错误不再只剩 toast
- 用户不必先钻原始 JSON
- 前后端可以围绕统一锚点排障
