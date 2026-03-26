# OneOPS 采集与处理基座联合差距分析

本文档聚焦一个更完整的问题：

- 为什么当前 OneOps 的采集链路和处理链路都还主要停留在“任务模式”
- 为什么这会限制拓扑基座和 RCA 的稳定性
- 采集与处理应该如何作为一条统一主线推进

本文档是以下文档的补充：

- [ONEOPS_TOPOLOGY_FOUNDATION_FOR_RCA_GAP_ANALYSIS.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_TOPOLOGY_FOUNDATION_FOR_RCA_GAP_ANALYSIS.md)

上一篇文档重点分析了处理侧和拓扑侧。
本文档重点补齐采集侧，并把采集与处理放到同一条流水线上看。

---

## 1. 总结论

当前 OneOps 在“采集”和“处理”两端存在相同的结构性问题：

- 都是通过 job 调度触发
- 都是任务内部直接做核心业务
- 都缺少统一的领域契约
- 都缺少稳定的快照与发布语义
- 都缺少质量分级、部分成功、降级成功的统一表达

因此，当前系统更像：

- 一批可独立运行的采集任务
- 一批可独立运行的处理任务
- 中间通过“某些数据已经被写到了某些存储里”来形成弱耦合

而不是：

- 一条平台化的数据采集与处理流水线

如果不把采集和处理一起升级，后续拓扑和 RCA 会持续遇到同一类问题：

- 观测是否完整不知道
- 本次处理使用的是哪一批观测不知道
- 采集成功但数据不可信，平台看不出来
- 处理成功但输入已过期，平台看不出来
- 当前拓扑是完整快照还是半成品，平台看不出来

---

## 2. 当前采集链路的真实形态

当前采集主入口在：

- `OneOps/app/data_collection/service/impl/acquisition.go`

实际执行器在：

- `OneOps/app/job/tasks/acquisition/acquisition.go`

辅助能力和缓存查询在：

- `OneOps/app/data_collection/service/impl/data_auto_collect.go`
- `OneOps/app/data_collection/service/impl/data_collect.go`

整体链路大致是：

1. `AcquisitionSrv` 负责建 job、发通知、触发立即执行或周期执行
2. notifier 把参数传给 job control
3. `AcquisitionServer` 在 job runner 中构建设备列表并发采集
4. 采集结果直接写 recorder / raw storage
5. 处理任务在另一个调度链路中独立执行

这条链路能把事情跑起来，但还不是“采集基座”。

---

## 3. AcquisitionSrv 当前本质上是调度适配层，不是采集领域层

文件：

- `OneOps/app/data_collection/service/impl/acquisition.go`

当前 `AcquisitionSrv` 的主要职责其实是：

- 同步周期 job
- 创建一次性 job
- 生成 code
- 调 notifier
- 调 run now / reschedule

它并没有真正承接采集领域里最关键的问题，例如：

- 采集对象范围
- 采集源定义
- 采集协议定义
- 观测批次定义
- 数据质量定义
- 部分成功表达
- 观测快照发布

这意味着它虽然名为 `AcquisitionSrv`，但目前更接近：

- `CollectionJobSchedulerAdapter`

而不是：

- `CollectionFoundationService`

---

## 4. 当前采集侧的关键问题

## 4.1 采集和处理使用同一套混合请求模型

文件：

- `OneOps/app/data_collection/dto/acquisition.go`

当前 `AcquisitionReq` 同时包含：

- `L2ServiceID`
- `L2Task`
- `TenantCode`
- `Expression`

这说明一个 DTO 同时承担了：

- 采集任务参数
- 处理任务参数
- 调度参数
- 租户范围参数

这类混合模型在任务系统里可以工作，但在平台基座里会带来两个问题：

1. 语义边界不清晰
2. 无法稳定扩展

采集和处理建议至少拆为两类独立契约：

- `CollectionRunRequest`
- `ProcessingRunRequest`

否则后续再接入批次号、观测范围、输入快照、回放模式时，这个 DTO 会越来越难维护。

---

## 4.2 周期配置同步和运行时调度动作耦合在一起

文件：

- `OneOps/app/data_collection/service/impl/acquisition.go`

`SetPeriodCollect()` 和 `SetPeriodProcessCache()` 最终都会进入：

- `syncCollectJob()`
- `syncProcessCacheJob()`

这两个函数除了创建或更新 job 记录，还会立刻调用：

- `acquisitionPeriodsExecuteFn()`

而 notifier 的 `PeriodsExecute()` 又会直接调用：

- `JobControlSrv.RescheduleByCode(...)`

这说明当前存在一个明显耦合：

- “配置同步”
- “运行时调度变更”

被放在了一起。

更直白一点说，当前系统里“加载配置”这件事，会直接触发“改 scheduler 行为”。

这种模式的问题在于：

- 缺少 dry-run
- 缺少 staged config
- 缺少 configuration revision
- 缺少“先校验后发布”的流程

它适合作为早期工程实现，但不适合作为长期采集基座。

---

## 4.3 周期 job 的持久配置和运行态调度不是同一个真相源

文件：

- `OneOps/app/data_collection/service/impl/acquisition.go`

在 `syncCollectJob()` 和 `syncProcessCacheJob()` 中，若 job 已存在，`Update()` 时写回的 `Expression` 使用的是：

- `res.Expression`

而不是新的：

- `collectConfig.Cron`
- `cron`

同时又会通过 `RescheduleByCode()` 使用新的 cron 去改调度器。

这意味着系统可能出现：

- job 数据库存的 cron
- 实际 scheduler 生效的 cron

两者不一致。

这类“双真相源”问题在采集基座里影响很大，因为它会让你很难回答：

- 当前采集到底按哪个频率在跑
- 配置是否已经发布成功
- 当前处理读到的数据是否符合预期采集窗口

---

## 4.4 OneExecute 带有明显的临时调试特征

文件：

- `OneOps/app/data_collection/service/impl/acquisition.go`

`OneExecute()` 中硬编码了：

- `l2Task := "L2nodeMapServer"`
- `TenantCode: "TENANT-SHDXFSZX"`
- `job name: l2Task + "-test"`

这说明当前采集服务里仍然混有明显的调试路径。

从基座视角，这类逻辑应该：

- 移出正式服务
- 或至少明确标记为 debug / dev only

否则它会不断模糊：

- 生产能力边界
- 运行方式边界
- 调试入口边界

---

## 4.5 CollectLayer 中存在未完成的“动态设备视图”设计痕迹

文件：

- `OneOps/app/data_collection/service/impl/acquisition.go`

`CollectLayer` 中保留了：

- `deviceList [][]interface{}`
- `currentIndex`
- `UpdateAllDevice()`

但在当前 `Run()` 主流程中，这些能力并没有真正进入采集执行面。

这说明当前设计曾经想过：

- 设备集动态切换
- 双缓冲式设备列表更新

但最后没有沉到正式采集机制里。

这不是小问题，因为采集基座必须回答：

- 本次采集针对哪一批设备
- 范围是全量还是增量
- 设备集变更何时生效
- 设备列表是按标签、租户、区域还是静态配置生成

当前这一层实际上还没有闭合。

---

## 4.6 一次性采集任务本质上还是“借道 cron job”

文件：

- `OneOps/app/data_collection/service/impl/acquisition.go`

`RunCollectOnce()` 和 `RunProcessOnce()` 都会创建一个 job，并设置：

- `manualOnceExpression = "0 0 0 * * *"`

然后再通过：

- `submitOnce()`

去立刻执行或延迟执行。

这说明“一次性任务”本质上并不是独立的运行模型，而是：

- 借用 cron job 作为运行壳

这在工程上可以接受，但在平台能力上会带来几个含糊点：

- 一次性任务和周期任务没有明确分层
- 创建的 job 本身并不天然表达“one-shot”
- cleanup 依赖 `cleanup_after_run`
- 可观测性和运行语义仍然继承自周期 job

更长期的方向通常是：

- 周期任务是一类运行模型
- 一次性任务是一类运行模型
- 回放任务是一类运行模型

而不是全部折叠到 cron job。

---

## 5. AcquisitionServer 当前仍是“按设备并发执行脚本”

文件：

- `OneOps/app/job/tasks/acquisition/acquisition.go`

当前 `AcquisitionServer.Main()` 做的事情本质上是：

1. 构建设备列表
2. 按并发数起 goroutine
3. 每台设备构建请求体
4. 按区域选择 controller
5. 调 `/api/v1/execute`
6. 把 raw data append 到 recorder

这是一种典型的“设备级并发采集任务”实现。

它的问题不是不能工作，而是它还没有形成采集基座应该具备的更高层抽象。

---

## 5.1 设备范围默认是全量，而不是显式采集范围

文件：

- `OneOps/app/job/tasks/acquisition/acquisition.go`
- `OneOps/app/job/tasks/register.go`

`acquisition.Config.Build()` 当前直接使用：

- `CommonBuildByAllSwitchAndRouterAndFirewall(...)`

来构建设备列表。

这意味着当前采集 runner 的默认语义是：

- 全量网络设备采集

它没有直接承接：

- tag scope
- tenant scope
- area scope
- device scope
- changed-only scope

即便上游 job 有 mapping 或 tag，当前采集 runner 本身并没有像处理 runner 那样明确消费这些范围。

这对平台来说是很大的限制，因为采集基座必须能表达：

- 这次采集采了谁
- 为什么采这些设备
- 是否只采某个租户或某个区域

否则后面处理链路很难和具体观测批次对齐。

---

## 5.2 当前采集结果主要是 raw append，不是正式 observation 发布

文件：

- `OneOps/app/job/tasks/acquisition/acquisition.go`

当前采集成功后主要执行：

- `GetRecorderSrv().Append(commonEnum.MongoCollection(t.L2ServiceID), ...)`

这说明当前结果落库语义更接近：

- 将设备本次采集原始结果追加到某个记录集合

而不是：

- 发布一批带 batch id、quality、scope、version 的 observation

这种 append 模式的典型问题是：

- 缺少观测批次号
- 缺少一次采集运行的全局 run id
- 缺少每批结果的完成态
- 缺少“本批次采集是否完整”
- 缺少“某设备失败是否导致整批不可用”

后续处理链路如果直接读 recorder，会面临：

- 读到的是最近一条
- 还是最近一批
- 还是某台设备最近成功但其他设备老数据

这些都不明确。

---

## 5.3 当前采集只有设备级执行，没有批次级事务语义

文件：

- `OneOps/app/job/tasks/acquisition/acquisition.go`

当前实现里，每台设备采集：

- 单独开始
- 单独超时
- 单独记录日志
- 单独写 recorder

这对提高吞吐是有帮助的。

但系统缺少一个更高层的批次概念，例如：

- `collection_run_id`
- `collection_batch_id`
- `device_total`
- `device_success`
- `device_failed`
- `run_state`
- `published_at`

没有这层之后，平台就无法知道：

- 本次采集是已完成还是仅完成一部分
- 当前处理能不能消费这次采集
- 某次 RCA 对应的是哪一批观测

---

## 5.4 采集结果没有统一的质量和错误分类

当前 `AcquisitionServer.Main()` 对设备失败主要是记录日志，然后继续。

缺少统一表达：

- credential_error
- timeout
- controller_unreachable
- empty_result
- partial_result
- parser_error
- unsupported_collect_type

如果没有这些分类，平台就无法做：

- 失败归因
- 质量评分
- 自动重试策略
- 降级处理
- readiness 评估

对 RCA 来说，这种信息同样重要，因为“拓扑不可信”很多时候并不是处理问题，而是采集问题。

---

## 5.5 buildReqBody 和 supportCollectType 仍然是硬编码驱动

文件：

- `OneOps/app/job/tasks/acquisition/acquisition.go`

当前 `buildReqBody()` 和 `supportCollectType()` 表明：

- 采集能力由配置中的 `Attentions` 和硬编码枚举共同决定
- 支持类型列表是写死的
- 设备商 / 平台 / catalog 的映射规则分散在运行代码里

这在早期是正常的，但长期看会带来：

- 能力扩展成本高
- 不同采集类型难以统一治理
- 可视化平台难以准确解释当前采集合同

更好的方向通常是：

- 采集目标模型
- 采集方法模型
- 协议模板模型
- 运行时渲染与执行模型

三层分开。

---

## 6. DataAutoCollect 与 DataCollect 当前更多是“缓存与兼容辅助层”

文件：

- `OneOps/app/data_collection/service/impl/data_auto_collect.go`
- `OneOps/app/data_collection/service/impl/data_collect.go`

这两层当前已经提供了一些有价值的能力，例如：

- expire 检查
- 缓存读取
- remote / agent 调用回退
- 按设备读取采集结果

但从平台视角看，它们还没有真正成为统一观测层，原因主要有三点。

### 6.1 结果读取主要依赖“最新记录”

`FindByNameAndDevID()` 和相关方法基本都基于：

- `UpdatedAt.Desc()`

取最近一条记录。

这说明当前系统默认认为：

- 最近一条就是正确采集结果

但对于平台基座，这个假设太弱了。

我们真正需要的是：

- 最近一个成功发布快照
- 最近一个完整批次
- 或某个指定运行的结果集

而不是简单的“最近一条”。

### 6.2 expire 判断是时间驱动，不是批次驱动

`CheckExpireTime()` 当前依据：

- 周期配置中的 `Expire`
- 单设备最近更新时间

来判断是否过期。

这适合作为缓存命中策略。
但它不等价于平台化采集 readiness，因为它回答不了：

- 该设备所在批次是否完成
- 同一拓扑处理所需的其他设备是否同样在有效窗口内
- 当前是否是一个可消费的一致视图

### 6.3 采集结果的数据形态仍偏轻量，不足以作为正式 observation

当前 `DataCollectReq` / `DataCollectResp` 核心字段仍然是：

- `Name`
- `Code`
- `DevID`
- `CollectRecords`
- `RawData`

还缺少：

- `run_id`
- `batch_id`
- `scope`
- `source`
- `observed_at`
- `quality`
- `error_class`
- `publish_state`

所以它更像“采集记录表”，还不是“观测基座表”。

---

## 7. 当前采集与处理之间的最大平台断层

最关键的问题不是采集弱或处理弱，而是：

- 两边之间没有“确定的批次边界”

当前处理任务大多是按自己的调度周期独立运行。
当前采集任务也按自己的调度周期独立运行。

但系统缺少一个稳定机制来保证：

- 这次处理用的是哪次采集结果
- 这次采集结果是否完整
- 采集与处理是否来自同一窗口
- 本次拓扑发布是否建立在完整观测之上

于是就会出现一个典型问题：

- 采集侧是“最近可用数据”
- 处理侧是“当前开始处理”

中间没有被显式绑定。

这对拓扑和 RCA 都是高风险的。

---

## 8. 采集与处理应该升级为统一流水线

建议把当前“采集 job + 处理 job”的模式，逐步升级为下面这条主线：

1. `collection plan`
2. `collection run`
3. `observation staging`
4. `observation publish`
5. `processing run`
6. `topology snapshot publish`
7. `rca consume`

这里最关键的是两个发布边界：

- observation publish
- topology snapshot publish

只有把这两个边界建立起来，RCA 才能读取到稳定输入。

---

## 9. 建议的目标模型

建议至少补齐以下核心对象。

### 9.1 采集侧

- `CollectionPlan`
- `CollectionScope`
- `CollectionRun`
- `CollectionRunDeviceResult`
- `ObservationBatch`
- `ObservationRecord`
- `ObservationPublish`

### 9.2 处理侧

- `ProcessingPlan`
- `ProcessingRun`
- `ProcessingInputBatch`
- `TopologyCandidate`
- `TopologySnapshot`
- `TopologyPublish`

### 9.3 两者之间的绑定关系

建议明确：

- `ProcessingRun.input_observation_batch_id`
- `TopologySnapshot.source_processing_run_id`
- `TopologySnapshot.source_observation_batch_id`

这样后续 RCA 才能追溯：

- 当前结论依赖哪批观测
- 当时采集是否完整
- 当时处理是否降级

---

## 10. 建议的状态与质量语义

### 10.1 采集侧

`CollectionRun.state` 建议支持：

- `pending`
- `running`
- `partial_success`
- `success`
- `failed`
- `published`

`CollectionRunDeviceResult.error_class` 建议支持：

- `timeout`
- `credential_error`
- `controller_unreachable`
- `empty_result`
- `parser_error`
- `unsupported`
- `panic`

`ObservationRecord.quality` 建议支持：

- `trusted`
- `partial`
- `suspect`
- `stale`
- `synthetic`

### 10.2 处理侧

`ProcessingRun.state` 建议支持：

- `pending`
- `running`
- `partial_success`
- `success`
- `failed`
- `published`

`TopologySnapshot.readiness` 建议支持：

- `ready`
- `partial`
- `suspect`
- `not_ready`

---

## 11. 建议的分阶段推进顺序

## 11.1 第一阶段：先把采集与处理结果语义补齐

优先做：

1. 采集 runner 返回结构化结果
2. 处理 runner 返回结构化结果
3. job 状态不再只表示“任务跑没跑完”，而要表达“数据能不能被消费”
4. 统一记录设备级成功/失败/空结果/超时分类

这一阶段先解决“平台看不见真实状态”的问题。

## 11.2 第二阶段：引入 collection run 和 observation batch

优先做：

1. 每次采集生成 `collection_run_id`
2. 每次采集生成 `observation_batch_id`
3. 处理侧只消费指定 batch
4. 不再直接用“最近一条记录”作为处理输入

这一阶段先解决“采集和处理之间没有确定边界”的问题。

## 11.3 第三阶段：引入 processing run 和 topology snapshot

优先做：

1. 每次处理明确输入 observation batch
2. 处理输出 topology snapshot
3. snapshot 发布采用原子切换
4. 发布失败不覆盖旧快照

这一阶段先解决“拓扑是半成品还是可消费成品”的问题。

## 11.4 第四阶段：让 RCA 只消费发布态结果

RCA 应只读取：

- observation publish 状态
- topology snapshot
- quality/readiness
- evidence

不应直接消费采集中间态或任务内部临时数据。

---

## 12. 对当前代码的直接判断

当前采集链路的问题，不是单纯的“任务多”或“代码旧”，而是：

- 采集服务仍主要承担调度适配职责
- 采集执行仍主要承担设备级脚本执行职责
- 数据存储仍主要承担“最近记录缓存”和“原始结果堆积”职责

这三者组合起来，可以跑任务，但还不足以形成采集基座。

处理侧同样如此。

因此，下一步不应把采集和处理分开各自做“小修小补”，而应该明确按一条主线推进：

- 先建立采集基座
- 再建立处理基座
- 最后由 RCA 消费两者的正式发布结果

只有这样，OneOps 的拓扑和根因定位能力才会真正稳定下来。

---

## 13. 建议的后续文档

基于本文档，建议继续补三份设计稿：

1. `OneOPS Collection Run 与 Observation Batch 设计`
2. `OneOPS Processing Run 与 Topology Snapshot 设计`
3. `OneOPS Collection -> Processing -> RCA 统一发布契约`

本文档的任务只完成到这里：

- 先把“为什么采集和处理都还是任务化问题，而不是两个独立小问题”讲清楚。
