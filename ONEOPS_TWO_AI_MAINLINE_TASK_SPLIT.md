# OneOPS 双 AI 主线任务拆分

本文档用于把当前 OneOPS 的“采集 -> 处理 -> 拓扑基座”主线拆给两个 AI 并行推进。

目标不是把工作无限拆散，而是：

- 围绕主线推进
- 不过度设计
- 不过度泛化
- 不衍生额外平台
- 先形成最小闭环

本文档默认当前阶段只推进：

- L2 主线
- 采集批次化
- 处理输入显式化
- L2 拓扑快照雏形
- 面向上述主线的最小前端操作与可视化面

不在本阶段推进：

- L3 拓扑正式建设
- 安全拓扑正式建设
- 大一统图平台
- 复杂规则引擎
- 自动推断与智能补偿机制

---

## 1. 总原则

两个 AI 必须共同遵守以下原则。

### 1.1 只沿主线做事

主线固定为：

1. 采集结果必须从“任务副作用”升级为“可引用的 observation batch”
2. 处理任务必须显式消费指定 observation batch
3. 拓扑输出必须从“直接落库关系”升级为“可发布的 topology snapshot”

凡是不直接服务这三件事的工作，本阶段不做。

### 1.2 不过度设计

本阶段不做：

- 大而全统一抽象
- 提前为 L3 / 安全 / 云资源 / 应用依赖做复杂泛化
- 为未来未知场景预埋大量层次

只允许做：

- 当前 L2 主线必需的最小抽象
- 后续扩展不会推翻的稳定边界

### 1.3 代码不冗余

禁止：

- 平行实现两套同义逻辑
- 用新代码包一层旧代码但不收敛旧入口
- 多处复制相同 DTO / 状态 / 判定分支

要求：

- 相同语义只保留一处真相源
- 新旧兼容期也要明确唯一主入口

### 1.4 不降级、不兜底、不智能

这里的含义要统一：

- 不降级：不要在关键路径上“静默改走旧逻辑”
- 不兜底：不要为了让流程继续就吞掉错误或伪造关键结果
- 不智能：不要引入猜测式自动修复、自动补全、模糊匹配扩大解释面

允许的行为只有：

- 显式失败
- 显式标记缺失
- 显式标记未就绪
- 显式返回错误

### 1.5 错误尽早保留，不吃错误

禁止：

- 只记日志不返回错误
- panic 后继续吞掉
- 空结果当成功
- 假数据当真数据

要求：

- 所有关键路径函数返回明确错误
- 区分 `success / partial_success / failed`
- 错误要可落库、可追踪、可引用

### 1.6 前后端都要围绕同一主线

当前阶段前端不是独立产品线，而是主线的操作面和可见面。

前端只服务下面四件事：

1. 发起采集
2. 发起处理
3. 查看 run / batch / snapshot 状态
4. 查看错误与 readiness

本阶段前端不做：

- 大而全拓扑工作台
- 通用低代码编排器
- 多视角图分析平台
- 复杂可视化设计系统

要求：

- 后端先定最小契约
- 前端只消费正式 API 契约
- 前端不能自定义一套状态语义

---

## 1.7 当前阶段不建议按“前端 AI / 后端 AI”拆

如果只有两个 AI，不建议简单拆成：

- AI-1 做后端
- AI-2 做前端

原因是当前阶段主线的核心难点不在 UI，而在：

- 采集 batch 边界
- 处理输入边界
- snapshot 发布边界

如果前端过早独立推进，很容易出现：

- 后端模型还没稳定
- 前端已经自建状态枚举
- API 契约反复返工

因此更合理的拆法是：

- AI-1 主攻采集后端，同时定义采集相关 API 契约
- AI-2 主攻处理与拓扑后端，同时落最小前端页面

也就是说：

- 按主线拆
- 但每条主线都把对应的前端面一起考虑进去

---

## 2. 两个 AI 的职责总览

建议分成：

- AI-1：采集主线
- AI-2：处理与拓扑主线

拆分原则不是按目录平均分，而是按“领域边界 + 写入边界”分。

---

## 3. AI-1 负责范围：采集主线

AI-1 只负责把“采集任务”推进为“观测批次生产线”。

### 3.1 AI-1 核心目标

形成最小能力闭环：

- 每次采集有 `collection_run`
- 每次采集产生 `observation_batch`
- 每台设备有明确的设备级采集结果
- 错误分类清晰
- 处理层可以显式引用某个 batch

### 3.2 AI-1 允许修改的主范围

- `OneOps/app/data_collection/**`
- `OneOps/app/job/tasks/acquisition/**`
- `OneOps/app/job/tasks/register.go`
- 与采集 run / batch 查询直接相关的 API 层
- 与采集 run / batch / result 直接相关的 model、dto、service、migration

### 3.3 AI-1 不负责的范围

- `analysis_l2` 业务处理逻辑重构
- L2 拓扑落库逻辑重构
- Neo4j 同步重构
- RCA 适配逻辑

AI-1 可以定义处理层需要消费的输入契约，但不能替 AI-2 改处理主流程。

### 3.4 AI-1 的具体任务

#### 任务 A1：建立采集运行模型

目标：

- 引入最小 `CollectionRun`
- 明确一次 run 的状态
- 为后续 `ObservationBatch` 提供挂载点

最低要求：

- run id
- collect name / l2 service id
- scope summary
- total devices
- success devices
- failed devices
- state
- started_at / finished_at

#### 任务 A2：建立设备级采集结果模型

目标：

- 每台设备的采集结果可追溯

最低要求：

- collection_run_id
- device_id / device_code
- state
- error_class
- error_message
- observed_at

错误分类先只做最小集合：

- `timeout`
- `empty_result`
- `controller_unreachable`
- `credential_error`
- `request_build_error`
- `storage_error`
- `panic`

#### 任务 A3：建立 observation batch 概念

目标：

- 采集结果不再只是 raw append
- 而是“一个可被引用的批次”

最低要求：

- observation_batch_id
- source_collection_run_id
- l2_service_id
- state
- published_at

注意：

- 当前阶段 observation record 可以仍复用现有 recorder/raw storage
- 但必须新增 batch 层引用关系
- 不要求第一阶段重写所有历史存储

#### 任务 A4：改造 AcquisitionSrv 语义

目标：

- `AcquisitionSrv` 不再只是 job 调度适配器
- 它至少要成为采集运行入口的编排层

最低要求：

- 采集请求和处理请求 DTO 分离
- 周期 collect 和 process 不再共用混合语义结构
- `RunCollectOnce` 只表达采集
- `RunProcessOnce` 只表达处理

#### 任务 A5：改造 AcquisitionServer.Main 返回结果

目标：

- 采集 runner 不能只打日志
- 必须产出结构化结果

最低要求：

- `Main()` 返回错误
- 设备级结果可统计
- 空结果不能静默当成功
- 保存失败必须返回错误或标记 run 失败

#### 任务 A6：给处理层暴露 batch 读取接口

目标：

- AI-2 可以明确按 batch 拉处理输入

最低要求：

- 查询指定 observation batch
- 查询 batch 下设备结果
- 查询 batch readiness

AI-1 在这个任务里只做接口和实现，不做处理逻辑消费。

#### 任务 A7：提供采集主线最小 API 契约

目标：

- 前端和处理层都能基于正式接口工作

最低要求：

- 创建一次性采集 run
- 查询 collection run 详情
- 查询 observation batch 列表 / 详情
- 查询设备级采集结果

要求：

- API 返回正式状态枚举
- 错误信息结构化
- 不返回“看日志去查”

#### 任务 A8：明确采集前端只需要哪些字段

目标：

- 让前端不猜
- 让字段最小化

最低要求：

- run 列表字段
- run 详情字段
- 设备失败列表字段
- batch readiness 字段

### 3.5 AI-1 完成标志

AI-1 完成后必须能回答：

- 本次采集 run 是谁
- 本次采集采了哪些设备
- 哪些设备成功，哪些失败
- 失败原因是什么
- 当前处理要消费哪一个 observation batch

如果这五个问题答不出来，AI-1 还不算完成。

---

## 4. AI-2 负责范围：处理与拓扑主线

AI-2 只负责把“处理任务”推进为“显式消费 observation batch，并发布 L2 topology snapshot”。

### 4.1 AI-2 核心目标

形成最小能力闭环：

- 处理任务必须显式指定输入 batch
- 处理结果必须是结构化 processing run
- L2 处理结果必须沉淀为 topology snapshot 雏形
- RCA 未来可只读 snapshot，而不碰任务中间态

### 4.2 AI-2 允许修改的主范围

- `OneOps/app/analysis_l2/**`
- `OneOps/app/job/tasks/process_cache/**`
- `OneOps/app/job/tasks/register.go`
- `OneOps/app/data_collection/api/**` 中与处理主线相关的接口
- `OneOPS-UI/**` 或当前前端工程中与采集/处理/拓扑状态展示直接相关的页面
- 与 processing run、topology snapshot 直接相关的 model、dto、service、migration

### 4.3 AI-2 不负责的范围

- 采集 runner 内部实现
- observation batch 内部生成逻辑
- 采集错误分类逻辑

AI-2 可以要求 AI-1 提供必要查询接口，但不自己重做采集侧存储。

### 4.4 AI-2 的具体任务

#### 任务 B1：建立处理运行模型

目标：

- 每次处理有 `ProcessingRun`
- 明确它消费哪一个 observation batch

最低要求：

- processing_run_id
- l2_task
- input_observation_batch_id
- state
- total devices
- success devices
- failed devices
- started_at / finished_at

#### 任务 B2：改造 AnalysisProcessCommon

目标：

- 不再只是 `switch-case` 分发
- 必须返回结构化结果与错误

最低要求：

- `AnalysisProcessCommon(...)` 返回 `result, error`
- 不支持的任务直接报错
- 内部任务失败不能只 `fmt.Println`

#### 任务 B3：改造 ProcessAnalysisServer.Main

目标：

- 作业状态必须和处理真实结果一致

最低要求：

- `Main()` 根据处理结果返回真实错误
- 不能无条件 `return nil`
- processing run 状态要能落库

#### 任务 B4：让处理任务显式消费 observation batch

目标：

- 处理输入不再依赖“最近数据”

最低要求：

- `L2nodeMapServer`
- `DevicePorts`
- `ArpTableServerV2`

至少先支持通过 processing run 显式引用一个 input batch。

当前阶段可以先做到：

- 若未指定 batch，则直接报错或明确 `not_ready`

不要做自动找“最近一批”的隐式行为。

#### 任务 B5：建立 L2 topology snapshot 雏形

目标：

- 当前阶段先不做全域拓扑平台
- 只把 L2 做成“可发布快照”

最低要求：

- topology_snapshot_id
- source_processing_run_id
- source_observation_batch_id
- topology_type = `l2`
- state / readiness
- generated_at

当前阶段不要求马上重构全部边表，但必须先把“快照边界”立起来。

#### 任务 B6：约束现有 L2 任务不再静默吞错

重点改造：

- `DevicePorts`
- `L2nodeMapServer`
- `ArpTableServerV2`

最低要求：

- 空结果与失败区分
- 落库失败返回错误
- 清空旧数据前必须处于受控流程
- 不能通过假数据维持主链可运行

注意：

- 当前阶段可先不彻底重构所有业务细节
- 但必须先把错误语义和输入边界改对

#### 任务 B7：提供处理与拓扑最小 API 契约

目标：

- 前端可以明确展示 processing run 和 topology snapshot

最低要求：

- 创建一次性 processing run
- 查询 processing run 详情
- 查询 processing run 引用的 observation batch
- 查询 topology snapshot 列表 / 当前激活快照
- 查询 snapshot readiness / error summary

#### 任务 B8：落最小前端页面

目标：

- 不做大平台
- 只做主线可见化

最低要求：

- 采集运行页
- 处理运行页
- L2 topology snapshot 状态页

每页只需支持：

- 列表
- 详情抽屉或详情页
- 关键状态
- 错误摘要
- 手动触发入口

本阶段不要求：

- 复杂拓扑图渲染
- 拖拽编排
- 多标签高级联动
- 自定义仪表盘

### 4.5 AI-2 完成标志

AI-2 完成后必须能回答：

- 本次处理 run 是谁
- 它消费的是哪个 observation batch
- 哪个 L2 任务处理成功，哪个失败
- 当前是否生成了可引用的 L2 snapshot
- RCA 未来应该从哪里读取 L2 发布态结果

如果这五个问题答不出来，AI-2 还不算完成。

---

## 5. 两个 AI 之间的固定接口

为了避免互相打架，两个 AI 之间只通过下面这些契约协作。

### 5.1 AI-1 提供给 AI-2

AI-1 必须提供：

- `ObservationBatch` 标识
- batch 查询接口
- batch readiness 查询接口
- batch 下设备结果查询接口

AI-2 只能依赖这些正式接口，不要直接读 AI-1 的内部表结构细节。

### 5.2 AI-2 提供给 AI-1 的约束

AI-2 必须明确告诉 AI-1：

- 处理侧消费 batch 至少需要哪些字段
- 哪些错误状态会导致处理拒绝执行
- 哪些 readiness 状态允许进入处理

例如：

- `not_ready` 直接拒绝处理
- `partial` 是否允许处理，需要明确规则

### 5.3 禁止事项

禁止：

- AI-1 自己实现 processing run
- AI-2 自己实现 observation batch 生成
- 两边各自定义一套状态枚举
- 两边各自定义一套 error class
- 前端自己发明一套状态文案和颜色语义
- 前端直接拼接内部字段猜业务状态

状态与错误枚举必须共用一套真相源。

---

## 5.4 前端契约固定规则

前端相关工作必须遵守下面几条：

1. 前端只认 API 返回的正式状态字段
2. 前端不根据多个字段自行推断“应该算成功还是失败”
3. 前端不把空数组、空对象自动解释成成功
4. 前端必须展示后端返回的 readiness / state / error_summary
5. 当前阶段前端只做主线状态展示，不做复杂可视化推理

---

## 6. 建议的实际执行顺序

两个 AI 虽然并行，但不是完全独立。

建议顺序如下。

### 第 1 步：AI-1 先定义 observation batch 最小契约

只做最小字段，不做大而全。

AI-2 先不要开写处理消费逻辑，先等这个契约落定。

### 第 2 步：AI-2 同步定义 processing run 最小契约

重点是明确：

- input batch id
- state
- 失败语义

### 第 3 步：AI-1 完成采集 run 与 batch 落地

这一步完成后，系统至少能稳定标识“采集产物”。

### 第 4 步：AI-2 改造处理入口

这一步只改：

- `AnalysisProcessCommon`
- `ProcessAnalysisServer.Main`

先把错误语义和 run 语义纠正。

### 第 5 步：AI-2 改造一个最小 L2 任务消费 batch

建议先选：

- `DevicePorts`

因为它更接近资产基础事实，副作用比 `L2nodeMapServer` 小。

### 第 6 步：AI-2 再改造 `L2nodeMapServer`

这一步再推进拓扑 snapshot 雏形。

### 第 7 步：AI-2 再接最小前端页面

只有在以下内容稳定后才接前端：

- observation batch API 已定
- processing run API 已定
- snapshot API 已定

这样前端只需要贴着稳定契约做最小页面，不会反复返工。

---

## 7. 当前阶段的最小交付闭环

本阶段不要求两个 AI 把所有历史问题都解决。

只要求形成下面这个最小闭环：

1. 采集一次 `IfTable`
2. 生成一个 `collection_run`
3. 生成一个 `observation_batch`
4. 处理任务显式引用这个 batch
5. `DevicePorts` 成功处理并产出 `processing_run`
6. L2 侧形成一个最小 `topology_snapshot` 雏形或至少具备快照挂载能力
7. 前端能看到这次 collect run、processing run 和 snapshot 的状态与错误

如果这个闭环打通，后续再扩到：

- LLDP/CDP
- ARP/MAC
- L2 邻接

就会顺很多。

---

## 8. AI 交付要求

每个 AI 每次交付都必须包含：

### 8.1 必须说清楚

- 改了哪些文件
- 新增了哪些模型 / 接口 / 状态
- 主线推进了哪一步
- 哪些问题仍未解决
- 若涉及前端，必须说明依赖哪个 API 契约版本

### 8.2 必须验证

- 至少有最小测试或最小可运行验证
- 不能只说“理论上可行”

### 8.3 必须保留真实错误

若链路未打通：

- 直接报错
- 明确缺口

禁止：

- 编假数据让测试过
- 吞错让任务成功
- 靠 fallback 假装兼容

---

## 9. 最后判断

当前这项工作适合双 AI 并行，但前提是：

- 边界清楚
- 真相源唯一
- 先把最小契约固定

不然两个 AI 很容易做成：

- 一个在做采集抽象平台
- 一个在做处理重构平台
- 最后两边接口对不上

正确做法不是“平均拆目录”，而是：

- AI-1 只负责把采集结果变成可引用输入
- AI-2 只负责把处理结果变成可发布输出

中间通过固定契约连接。

这才是当前阶段最稳、最快、最不容易失控的拆法。
