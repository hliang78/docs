# OneOPS 双 AI 第一轮验收 Checklist

本文档用于验收两个 AI 的第一轮交付结果。

本文档不关心：

- 代码写了多少
- 提交了多少文件
- 讲了多少概念

本文档只关心：

- 主线有没有推进
- 边界有没有立住
- 有没有偷兜底
- 有没有把错误吃掉
- 有没有形成最小闭环

配套文档：

- [ONEOPS_COLLECTION_AND_PROCESSING_FOUNDATION_GAP_ANALYSIS.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_COLLECTION_AND_PROCESSING_FOUNDATION_GAP_ANALYSIS.md)
- [ONEOPS_TOPOLOGY_FOUNDATION_FOR_RCA_GAP_ANALYSIS.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_TOPOLOGY_FOUNDATION_FOR_RCA_GAP_ANALYSIS.md)
- [ONEOPS_TWO_AI_MAINLINE_TASK_SPLIT.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_TWO_AI_MAINLINE_TASK_SPLIT.md)
- [ONEOPS_TWO_AI_EXECUTION_PROMPTS.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_TWO_AI_EXECUTION_PROMPTS.md)

---

## 1. 第一轮唯一验收目标

第一轮只验收下面这个最小闭环是否成立：

1. 一次 L2 采集可以产生 `collection_run`
2. 同时产生一个可被引用的 `observation_batch`
3. 一次处理 run 可以显式引用该 `observation_batch`
4. `DevicePorts` 已经按 batch 输入执行
5. 处理侧具备 `processing_run`
6. L2 侧具备最小 `topology_snapshot` 挂载能力
7. 前端能看到 collect run、processing run、snapshot 的状态与错误

如果这 7 件事里缺 2 件以上，第一轮不算通过。

---

## 2. 验收总规则

### 2.1 验收时不接受“理论上已经支持”

必须能看到至少一种真实证据：

- 代码路径
- API 返回
- 数据模型
- 测试
- 页面展示

如果只有口头说明，没有可验证证据，视为未完成。

### 2.2 验收时不接受“后面再补错误处理”

第一轮就必须满足：

- 错误不再被静默吞掉
- 关键路径返回 error
- 空结果不再被默认为成功

如果还是“先跑通，错误以后再补”，视为不通过。

### 2.3 验收时不接受“继续用最近一条记录”

如果处理侧仍然依赖：

- 最近一条
- 最新一批猜测
- 自动 fallback 到历史旧数据

则视为主线未推进。

---

## 3. AI-1 验收 Checklist：采集主线

## 3.1 模型层

必须成立：

- 存在 `CollectionRun` 或等价正式模型
- 存在 `ObservationBatch` 或等价正式模型
- 存在设备级采集结果模型

不要求：

- 完整大而全 schema

但至少要能表达：

- run id
- batch id
- collect name / l2 service id
- state
- total devices
- success devices
- failed devices

验收问题：

1. 本次采集 run 的唯一标识是什么？
2. 本次 observation batch 的唯一标识是什么？
3. 设备级结果挂在哪个 run 或 batch 下？

如果回答不清，AI-1 不通过。

## 3.2 采集执行层

必须成立：

- `AcquisitionServer.Main()` 或等价执行主链不再只是日志驱动
- 采集结果有结构化状态
- 空结果不会静默记为成功
- 保存失败能显式暴露

验收问题：

1. 一台设备超时后，系统如何记录？
2. 一台设备采集为空结果后，系统如何记录？
3. recorder 或存储 append 失败后，run 会发生什么？

如果答案仍是“打日志继续”，AI-1 不通过。

## 3.3 batch 边界

必须成立：

- observation batch 是正式概念，不是说明文档里的概念
- 处理层可以显式引用 batch
- 不能只靠 `UpdatedAt.Desc()` 取最近一条冒充 batch

验收问题：

1. 处理层现在如何拿到输入 batch？
2. 如果不给 batch id，会自动取最近一条吗？

正确预期：

- 必须显式引用
- 不允许隐式 fallback

## 3.4 API 层

至少应有最小接口支持：

- 查询 collection run
- 查询 observation batch
- 查询设备级采集结果

前端必须能拿到：

- state
- readiness 或等价字段
- error summary 或错误列表

验收问题：

1. 前端怎么查某次 collect run？
2. 前端怎么查 batch 详情？
3. 前端怎么知道哪些设备失败？

如果还要靠查日志，AI-1 不通过。

---

## 4. AI-2 验收 Checklist：处理与拓扑主线

## 4.1 处理入口

必须成立：

- `AnalysisProcessCommon` 或等价入口返回结构化结果和 error
- `ProcessAnalysisServer.Main()` 不再无条件 `return nil`
- 不支持的任务直接失败

验收问题：

1. 当前处理入口失败时，job 状态会怎样？
2. 当前处理入口如何区分 success / partial / failed？
3. 当前是否还存在只 `fmt.Println` 不返回错误的关键路径？

若仍存在主入口吞错，AI-2 不通过。

## 4.2 processing run

必须成立：

- 存在 `ProcessingRun` 或等价正式模型
- 它能显式记录：
  - 处理哪个任务
  - 输入哪个 observation batch
  - 当前状态是什么

验收问题：

1. 本次 processing run 的唯一标识是什么？
2. 它引用的 batch id 是什么？
3. 它失败时会落什么状态？

如果这些信息还散落在日志里，AI-2 不通过。

## 4.3 DevicePorts 主线

第一轮只要求先把 `DevicePorts` 改对。

必须成立：

- `DevicePorts` 已经按 batch 输入工作
- 不再隐式读“最近一条”
- 空结果和失败区分
- 关键存储失败显式报错

验收问题：

1. `DevicePorts` 当前的数据输入来自哪里？
2. 如果输入 batch 不存在，会怎样？
3. 如果 batch 状态 not_ready，会怎样？

正确预期：

- 直接失败或显式 not_ready
- 不允许悄悄找最近数据继续

## 4.4 topology snapshot

第一轮不要求完整拓扑平台，但必须有最小快照挂载能力。

必须成立：

- 存在 `TopologySnapshot` 或等价正式模型
- 至少能挂住：
  - source_processing_run_id
  - source_observation_batch_id
  - topology_type
  - state / readiness

验收问题：

1. 当前 snapshot 的唯一标识是什么？
2. 它来自哪个 processing run？
3. 当前 snapshot 至少表达了哪些 readiness 或 state？

如果还只是“文档上说准备做 snapshot”，AI-2 不通过。

## 4.5 前端页面

第一轮只验最小可见化，不验复杂体验。

必须成立：

- 前端能看到 collect run 状态
- 前端能看到 processing run 状态
- 前端能看到 L2 snapshot 状态
- 前端能看到错误摘要或错误列表

不要求：

- 拓扑图渲染
- 高级交互
- 复杂筛选

验收问题：

1. 页面上能不能看到 collect run 的状态？
2. 页面上能不能看到 processing run 引用了哪个 batch？
3. 页面上能不能看到 snapshot 是否 ready？
4. 页面上能不能看到错误，而不是只显示“失败”？

如果只是有个入口按钮，没有状态面，AI-2 不通过。

---

## 5. 联合验收 Checklist：两个 AI 的接口是否对齐

这是最容易翻车的地方。

必须成立：

- 采集侧只有一套正式 batch 标识
- 处理侧引用的 batch 字段就是采集侧正式字段
- 前端使用的状态枚举与后端一致
- 错误分类不重复发明两套

验收问题：

1. `observation_batch_id` 是否只有一套正式定义？
2. `processing_run.input_observation_batch_id` 是否直接复用该定义？
3. 前端状态是否来自 API 正式字段，而不是页面自己推断？
4. 采集失败错误分类和前端显示文案是否一致？

若答案是否定的，说明两个 AI 已经开始分叉。

---

## 6. 明确判定为“不通过”的行为

只要出现下面任意一项，就应直接打回。

### 6.1 吃错误

例如：

- 只打日志不返回 error
- panic recover 后继续当成功
- 空结果默认 success

### 6.2 偷 fallback

例如：

- batch 不存在时自动读最近一批
- 新模型失败时回退旧逻辑继续运行
- 前端字段取不到时自己猜状态

### 6.3 假性完成

例如：

- 加了 DTO，但主链没用上
- 加了 model，但没有实际落 run
- 页面有入口，但没有真实状态数据

### 6.4 过度设计

例如：

- 第一轮就搞大而全统一拓扑平台
- 第一轮就抽象 L2/L3/安全统一超级 schema
- 第一轮就引入复杂通用工作流引擎

---

## 7. 验收建议顺序

建议按这个顺序验收，不要乱跳。

1. 先验 AI-1 的 run 与 batch 是否真实存在
2. 再验 AI-2 是否显式引用 batch
3. 再验 `DevicePorts` 是否脱离“最近一条”模式
4. 再验最小 `topology_snapshot`
5. 最后验前端是否能看见状态与错误

这样最容易发现主线有没有真正打通。

---

## 8. 最终通过标准

第一轮通过，不要求漂亮，只要求真实。

只要下面六件事同时成立，就可以判定第一轮通过：

1. 采集 run 是正式模型，不再只是 job 的附属概念
2. observation batch 是正式模型，不再只是“最近记录”
3. 处理 run 明确引用 batch，不再隐式读旧数据
4. `DevicePorts` 成为第一条 batch 化处理链路
5. L2 具备最小 snapshot 挂载能力
6. 前端能看到 run / batch / snapshot 的状态与错误

如果这六件事真实成立，就说明主线已经从“任务模式”迈出第一步了。

---

## 9. 第二轮前的复盘问题

第一轮通过后，建议马上问两个 AI 这五个问题：

1. 当前最小真相源已经固定在哪里？
2. 还有哪些地方仍在偷偷使用“最近一条”？
3. 哪些错误现在已经显式暴露，哪些还没改完？
4. `L2nodeMapServer` 下一轮改造的最大阻碍是什么？
5. 当前 snapshot 是挂载能力，还是已经具备发布能力？

这五个问题会直接决定第二轮能不能继续稳步推进。
