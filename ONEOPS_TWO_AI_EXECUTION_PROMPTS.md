# OneOPS 双 AI 首轮执行 Prompt 模板

本文档用于把当前 OneOPS 的主线工作直接下发给两个 AI。

使用方式：

- 将对应 AI 的 prompt 原文直接发送给它
- 不要额外再加大段背景
- 如果要补充信息，只补当前代码位置、当前限制、当前阶段目标

本文档与以下文档配套：

- [ONEOPS_COLLECTION_AND_PROCESSING_FOUNDATION_GAP_ANALYSIS.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_COLLECTION_AND_PROCESSING_FOUNDATION_GAP_ANALYSIS.md)
- [ONEOPS_TOPOLOGY_FOUNDATION_FOR_RCA_GAP_ANALYSIS.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_TOPOLOGY_FOUNDATION_FOR_RCA_GAP_ANALYSIS.md)
- [ONEOPS_TWO_AI_MAINLINE_TASK_SPLIT.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_TWO_AI_MAINLINE_TASK_SPLIT.md)

---

## 1. 使用前说明

这两个 prompt 的目标不是让 AI 各自自由发挥，而是要求它们：

- 只沿主线推进
- 不过度设计
- 不过度泛化
- 不额外衍生平台
- 错误尽早暴露
- 不吃错误
- 不兜底
- 不“智能猜测”

当前阶段的唯一目标是打通最小闭环：

1. 一次 L2 采集产生 `collection_run`
2. 同时产生可引用的 `observation_batch`
3. 一次处理 run 显式引用该 batch
4. `DevicePorts` 先完成批次化处理
5. 处理侧具备 `processing_run`
6. L2 具备最小 `topology_snapshot` 挂载能力
7. 前端可看到 collect run、processing run、snapshot 的状态与错误

本阶段不要求：

- 完整 L2 拓扑平台
- L3 正式接入
- 安全拓扑正式接入
- 大而全前端工作台

---

## 2. 发给 AI-1 的 Prompt

以下内容可直接原样发给 AI-1。

```text
你负责 OneOPS 当前主线中的“采集基座”部分。

你的任务不是泛化平台，也不是重构所有采集逻辑，而是围绕当前主线把“采集任务”推进为“可被处理层明确引用的 observation batch 生产线”。

你必须严格遵守以下原则：

1. 只沿主线推进，不做额外平台化延展。
2. 不过度设计，不为未来 L3、安全、云资源等场景提前做复杂抽象。
3. 不冗余，不保留两套同义逻辑并行长期存在。
4. 不降级，不兜底，不智能，不靠猜测补齐关键数据。
5. 有错误尽早保留，不吃错误，不只打日志不返回错误。

你本轮只负责采集主线，不负责处理主线和拓扑重构。

你可修改的主要范围：

- OneOps/app/data_collection/**
- OneOps/app/job/tasks/acquisition/**
- OneOps/app/job/tasks/register.go
- 与 collection run / observation batch / device collection result 直接相关的 model、dto、service、migration、api

你不要改：

- OneOps/app/analysis_l2/** 的业务处理主逻辑
- topology snapshot 发布逻辑
- RCA 逻辑

你的本轮目标只有六件事：

1. 建立最小 CollectionRun 模型
2. 建立最小设备级采集结果模型
3. 建立最小 ObservationBatch 概念
4. 让采集 runner 产出结构化结果，而不是只打日志
5. 给处理层暴露 batch 读取接口
6. 给前端暴露采集 run / batch / device result 的最小 API

你必须优先围绕下面这个最小闭环工作：

- 先支持一次 IfTable 采集
- 该采集产生一个 collection_run
- 该采集产生一个 observation_batch
- 每台设备的采集结果有状态和错误分类
- observation_batch 可以被后续 processing run 引用

你必须遵守以下实现约束：

1. 不要引入复杂抽象层。
2. 不要一次性重写所有历史存储。
3. 当前阶段允许复用现有 recorder/raw storage，但必须增加 batch 边界。
4. 当前阶段不允许靠“取最近一条记录”来冒充 observation batch。
5. 空结果不能静默当成功。
6. 保存失败不能只打日志。
7. panic 不能吞掉。

你需要优先关注这些文件：

- OneOps/app/data_collection/service/impl/acquisition.go
- OneOps/app/job/tasks/acquisition/acquisition.go
- OneOps/app/data_collection/service/impl/data_collect.go
- OneOps/app/data_collection/service/impl/data_auto_collect.go
- OneOps/app/data_collection/api/data_collection.go
- OneOps/app/job/tasks/register.go

你需要特别注意这些当前问题：

- AcquisitionReq 当前采集和处理语义混合
- 周期配置同步和调度动作耦合
- 一次性任务借道 cron job
- 采集结果主要是 raw append，不是正式 observation batch
- 当前更多依赖“最近一条记录”，不是批次化读取

你本轮不要做的事：

- 不要尝试统一所有采集类型
- 不要引入大型工作流引擎
- 不要做“智能补偿”“自动修复”“失败自动降级”
- 不要偷偷 fallback 回旧逻辑并静默继续

你需要交付的内容必须包括：

1. 实际代码改动
2. 最小 migration 或模型变更
3. 最小 API 契约
4. 最小测试或验证
5. 一段清晰说明：
   - 新增了什么模型
   - batch 如何被唯一标识
   - 哪些错误会显式暴露
   - 处理层将如何读取 batch

你的结果必须能回答下面五个问题：

- 本次采集 run 是谁？
- 本次采集批次是谁？
- 哪些设备成功，哪些失败？
- 失败原因是什么？
- 处理层接下来应该引用哪个 batch？

如果这五个问题仍答不出来，说明你这轮任务没有完成。

开始前先快速阅读：

- docs/ONEOPS_COLLECTION_AND_PROCESSING_FOUNDATION_GAP_ANALYSIS.md
- docs/ONEOPS_TWO_AI_MAINLINE_TASK_SPLIT.md

然后直接动手，不要只停留在分析。
```

---

## 3. 发给 AI-2 的 Prompt

以下内容可直接原样发给 AI-2。

```text
你负责 OneOPS 当前主线中的“处理与拓扑发布”部分。

你的任务不是泛化整个平台，也不是一次性做完 L2/L3/安全统一拓扑，而是围绕当前主线把“处理任务”推进为“显式消费 observation batch，并形成最小 topology snapshot 挂载能力”的主线实现。

你必须严格遵守以下原则：

1. 只沿主线推进，不做额外平台化延展。
2. 不过度设计，不提前为 L3、安全等场景做复杂抽象。
3. 不冗余，不保留两套同义逻辑长期并存。
4. 不降级，不兜底，不智能，不靠猜测补齐关键事实。
5. 有错误尽早保留，不吃错误，不只打日志不返回错误。

你本轮只负责处理主线与最小前端可见化，不负责采集侧内部实现。

你可修改的主要范围：

- OneOps/app/analysis_l2/**
- OneOps/app/job/tasks/process_cache/**
- OneOps/app/job/tasks/register.go
- 与 processing run / topology snapshot 直接相关的 model、dto、service、migration、api
- OneOPS-UI/** 中与采集/处理/snapshot 主线可见化直接相关的页面

你不要重做：

- observation batch 生成逻辑
- collection run 生成逻辑
- 采集侧错误分类逻辑

你只能依赖采集侧正式提供的 batch 查询接口，不允许自己再实现一套“最近数据读取逻辑”。

你本轮目标只有七件事：

1. 建立最小 ProcessingRun 模型
2. 改造 AnalysisProcessCommon，返回结构化结果和 error
3. 改造 ProcessAnalysisServer.Main，使作业状态与真实处理结果一致
4. 让处理任务显式消费 observation batch
5. 先让 DevicePorts 支持 batch 化处理
6. 建立最小 L2 TopologySnapshot 挂载能力
7. 提供最小前端页面，展示 collect run / processing run / snapshot 状态与错误

你必须优先围绕下面这个最小闭环工作：

- 处理 run 显式引用 observation_batch_id
- DevicePorts 先完成批次化输入消费
- 形成 processing_run
- 至少具备一个 L2 topology_snapshot 雏形或挂载点
- 前端能看到 collect run、processing run、snapshot 的状态和错误

你必须遵守以下实现约束：

1. 不允许继续无条件 return nil。
2. 不支持的任务必须直接返回错误。
3. 不能继续使用 fmt.Println 作为主错误路径。
4. 不允许默认取“最近一批”数据作为处理输入。
5. 如果 batch 未指定或 not_ready，要直接报错或显式 not_ready。
6. 当前阶段不要做复杂拓扑图可视化，只做最小状态页。
7. 当前阶段不要大改所有 L2 任务业务，只先把主入口、错误语义、batch 输入边界和 snapshot 边界改对。

你需要优先关注这些文件：

- OneOps/app/analysis_l2/service/impl/analysis_l2.go
- OneOps/app/job/tasks/process_cache/process_analysis.go
- OneOps/app/analysis_l2/service/adapter/device_ports.go
- OneOps/app/analysis_l2/service/adapter/newL2NodeMapServe.go
- OneOps/app/analysis_l2/service/adapter/newArpTableServerV2.go
- OneOps/app/job/tasks/register.go

你需要特别注意这些当前问题：

- AnalysisProcessCommon 当前只是 switch 分发，不返回 error
- ProcessAnalysisServer.Main 当前无条件 return nil
- 处理侧当前与 observation batch 没有明确绑定
- L2 任务内部大量静默吞错
- 直接落库关系还没有 snapshot 边界

你本轮不要做的事：

- 不要开始完整重构 L3
- 不要开始完整重构安全拓扑
- 不要做大而全图数据库抽象
- 不要做复杂交互式拓扑工作台
- 不要自己定义另一套采集状态枚举

前端方面你只做最小页面：

- 采集运行页
- 处理运行页
- L2 snapshot 状态页

每个页面只要有：

- 列表
- 详情
- 状态
- readiness
- error summary
- 手动触发入口

不需要：

- 图渲染
- 拖拽
- 高级过滤器
- 多视图分析台

你需要交付的内容必须包括：

1. 实际代码改动
2. 最小 migration 或模型变更
3. 最小 API 契约
4. 最小前端页面或页面骨架
5. 最小测试或验证
6. 一段清晰说明：
   - processing run 如何引用 batch
   - 哪些错误现在会显式抛出
   - snapshot 当前具备了什么最小能力
   - 前端页面如何对应正式状态字段

你的结果必须能回答下面五个问题：

- 本次处理 run 是谁？
- 它消费的是哪个 observation batch？
- DevicePorts 是否已经按 batch 输入运行？
- 当前是否生成了可引用的 L2 snapshot？
- 前端现在能从哪里看到 run 和 snapshot 的状态与错误？

如果这五个问题仍答不出来，说明你这轮任务没有完成。

开始前先快速阅读：

- docs/ONEOPS_COLLECTION_AND_PROCESSING_FOUNDATION_GAP_ANALYSIS.md
- docs/ONEOPS_TOPOLOGY_FOUNDATION_FOR_RCA_GAP_ANALYSIS.md
- docs/ONEOPS_TWO_AI_MAINLINE_TASK_SPLIT.md

然后直接动手，不要只停留在分析。
```

---

## 4. 建议你对两个 AI 追加的一句统一要求

建议在两个 prompt 之后，再补这一小段：

```text
你需要尽量减少与你同伴 AI 的接口摩擦。
如果你准备新增状态枚举、错误分类、DTO 字段、API 字段，请优先复用已有正式定义，不要重新发明一套。
如果发现当前主线缺少关键契约，请先把契约补齐，再继续实现，不要绕开契约硬做。
```

---

## 5. 第一轮完成后的验收方式

第一轮结束后，你不应该只看“代码多不多”，而应该只看这六件事：

1. 是否真的出现了 `collection_run`
2. 是否真的出现了 `observation_batch`
3. `processing_run` 是否真的引用某个 batch
4. `DevicePorts` 是否真的不再读“最近一条”
5. 是否已有最小 `topology_snapshot` 挂载能力
6. 前端是否能看到 run / batch / snapshot 的状态和错误

只要这六件事成立，第一轮就是成功的。

---

## 6. 第二轮建议

如果第一轮打通，第二轮建议继续按这个顺序推进：

1. `IfTable` 之外扩展到 `LLDP/CDP`
2. 再接 `ARP/MAC`
3. 再收敛 `L2nodeMapServer`
4. 再逐步从 `DevicePorts` 走向最小 L2 snapshot 发布

不要在第一轮就冲完整拓扑平台。
