# OneOPS 双 AI 主线推进工作包总入口

本文档是当前 OneOPS “采集 -> 处理 -> 拓扑基座”主线的总入口。

如果你准备使用两个 AI 并行推进这条主线，建议先从本文档开始。

本文档只回答四个问题：

1. 当前主线是什么
2. 先看哪些文档
3. 两个 AI 怎么开工
4. 你如何验收第一轮结果

---

## 1. 当前主线

当前阶段只推进下面这条最小主线：

1. L2 采集产生 `collection_run`
2. 同时产生可引用的 `observation_batch`
3. 处理任务显式引用该 `observation_batch`
4. `DevicePorts` 先成为第一条 batch 化处理链路
5. 处理侧形成 `processing_run`
6. L2 侧形成最小 `topology_snapshot` 挂载能力
7. 前端能看到 collect run、processing run、snapshot 的状态与错误

当前阶段不推进：

- 完整 L2 平台
- L3 正式拓扑
- 安全拓扑正式建设
- 大而全前端工作台
- 自动推断、自动补偿、智能化修复

一句话概括：

- 先把“任务模式”推进成“批次输入 + 处理运行 + 快照输出”的最小闭环

---

## 2. 文档阅读顺序

建议严格按下面顺序阅读。

### 第 1 份：问题背景

- [ONEOPS_COLLECTION_AND_PROCESSING_FOUNDATION_GAP_ANALYSIS.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_COLLECTION_AND_PROCESSING_FOUNDATION_GAP_ANALYSIS.md)

这份文档回答：

- 为什么采集和处理当前都还是任务化
- 为什么必须一起推进

### 第 2 份：拓扑侧背景

- [ONEOPS_TOPOLOGY_FOUNDATION_FOR_RCA_GAP_ANALYSIS.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_TOPOLOGY_FOUNDATION_FOR_RCA_GAP_ANALYSIS.md)

这份文档回答：

- 为什么当前 L2 处理还不足以成为拓扑基座

### 第 3 份：任务拆分

- [ONEOPS_TWO_AI_MAINLINE_TASK_SPLIT.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_TWO_AI_MAINLINE_TASK_SPLIT.md)

这份文档回答：

- 两个 AI 分别负责什么
- 前后端怎么一起考虑

### 第 4 份：执行 prompt

- [ONEOPS_TWO_AI_EXECUTION_PROMPTS.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_TWO_AI_EXECUTION_PROMPTS.md)

这份文档回答：

- 直接发给两个 AI 的首轮指令是什么

### 第 5 份：协作协议

- [ONEOPS_TWO_AI_COLLABORATION_PROTOCOL.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_TWO_AI_COLLABORATION_PROTOCOL.md)

这份文档回答：

- 两个 AI 如何避免接口打架

### 第 6 份：第一轮验收

- [ONEOPS_TWO_AI_FIRST_ROUND_ACCEPTANCE_CHECKLIST.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_TWO_AI_FIRST_ROUND_ACCEPTANCE_CHECKLIST.md)

这份文档回答：

- 第一轮完成后你怎么判断有没有偏离主线

---

## 3. 两个 AI 的定位

当前建议不是按“前端 AI / 后端 AI”拆，而是按主线拆。

### AI-1

负责：

- 采集主线
- `CollectionRun`
- `ObservationBatch`
- 设备级采集结果
- 采集相关 API

它要解决的是：

- 采集结果不再只是任务副作用

### AI-2

负责：

- 处理与拓扑主线
- `ProcessingRun`
- 最小 `TopologySnapshot`
- 最小前端状态页

它要解决的是：

- 处理输入不再隐式读取历史数据
- 处理输出不再只是直接落副作用

### 为什么这样拆

因为当前阶段真正难的是：

- 批次边界
- 处理输入边界
- 快照边界

而不是 UI 本身。

---

## 4. 开工方式

建议你按下面方式启动。

### 第一步

把下面两份文档先给两个 AI 都看：

- [ONEOPS_COLLECTION_AND_PROCESSING_FOUNDATION_GAP_ANALYSIS.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_COLLECTION_AND_PROCESSING_FOUNDATION_GAP_ANALYSIS.md)
- [ONEOPS_TWO_AI_MAINLINE_TASK_SPLIT.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_TWO_AI_MAINLINE_TASK_SPLIT.md)

### 第二步

把对应 prompt 原样发给两个 AI：

- AI-1 使用 [ONEOPS_TWO_AI_EXECUTION_PROMPTS.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_TWO_AI_EXECUTION_PROMPTS.md) 中的 AI-1 prompt
- AI-2 使用 [ONEOPS_TWO_AI_EXECUTION_PROMPTS.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_TWO_AI_EXECUTION_PROMPTS.md) 中的 AI-2 prompt

### 第三步

把协作协议也发给两个 AI：

- [ONEOPS_TWO_AI_COLLABORATION_PROTOCOL.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_TWO_AI_COLLABORATION_PROTOCOL.md)

不要让两个 AI 自己决定协作方式。

### 第四步

明确告诉他们：

- 第一轮只做最小闭环
- 不允许自己额外扩展平台
- 不允许隐式 fallback
- 不允许吃错误

---

## 5. 你需要盯住的最少事项

你不需要每天读完所有代码。

你只要盯下面这些点就够了。

### 5.1 采集侧

你要确认：

- 是否真的有 `collection_run`
- 是否真的有 `observation_batch`
- 是否真的有设备级失败记录

### 5.2 处理侧

你要确认：

- 是否真的有 `processing_run`
- `processing_run` 是否真的引用 `observation_batch`
- `DevicePorts` 是否真的不再读最近一条

### 5.3 拓扑侧

你要确认：

- 是否真的有最小 `topology_snapshot`
- 它是否挂住 source processing run 和 source batch

### 5.4 前端侧

你要确认：

- 页面能不能看到 run 状态
- 页面能不能看到 snapshot 状态
- 页面能不能看到错误，而不只是“失败”

---

## 6. 第一轮通过标准

第一轮通过，不要求系统很漂亮，只要求主线真实推进。

只要下面六件事同时成立，就可以认为第一轮成功：

1. 采集 run 是正式模型
2. observation batch 是正式模型
3. processing run 显式引用 batch
4. `DevicePorts` 成为第一条 batch 化处理链路
5. L2 具备最小 snapshot 挂载能力
6. 前端能看到 run / batch / snapshot 的状态与错误

如果这六件事中有两件以上没有真实证据，第一轮不通过。

---

## 7. 明确不要做的事

当前阶段最容易失控的是“顺手做大”。

下面这些内容第一轮都不要做：

- 完整 L2/L3/安全统一超级模型
- 大而全拓扑图平台
- 通用工作流引擎
- 自动补数据
- 自动纠错
- 智能推荐
- 复杂拖拽式前端平台

如果两个 AI 开始讨论这些内容，说明已经偏离主线。

---

## 8. 第一轮结束后怎么做

第一轮结束后，你应该做三件事。

### 8.1 用验收 checklist 快速过一遍

使用：

- [ONEOPS_TWO_AI_FIRST_ROUND_ACCEPTANCE_CHECKLIST.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_TWO_AI_FIRST_ROUND_ACCEPTANCE_CHECKLIST.md)

### 8.2 看协作有没有分叉

重点确认：

- `observation_batch_id` 是否只有一套
- state/readiness 是否只有一套
- 前端是否在猜状态

### 8.3 再决定第二轮

如果第一轮通过，第二轮建议顺序是：

1. 扩到 `LLDP/CDP`
2. 再扩 `ARP/MAC`
3. 再推进 `L2nodeMapServer`
4. 再从最小 snapshot 走向正式 L2 发布能力

---

## 9. 一句话执行建议

当前这套工作包的核心不是“让两个 AI 多写代码”，而是：

- 让采集从任务副作用变成批次输入
- 让处理从隐式读取变成显式运行
- 让拓扑从直接落库变成最小快照输出

只要这条线打通，后面 L2、L3、安全拓扑才有稳定基座可以继续往上长。
