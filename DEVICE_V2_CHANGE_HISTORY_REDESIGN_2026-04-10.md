# Device V2 变更记录底层重构方案

## 结论

当前 `device_history` 机制不适合作为 `device v2` 的变更记录底座。

问题不在前端展示，而在于：

1. 变更事件的生产方式是分散式、附着式、副作用式的。
2. 存储模型只有一张粗粒度表，无法表达 v2 的实体化、动态属性化、关系化结构。
3. 差异计算是文本 diff，不是语义 diff。
4. “确认”被建模成历史记录本身的状态，而不是独立的确认动作。
5. `device v2 / entity v2` 当前没有统一的历史生产管线，继续复用只会放大不一致。

因此建议：

- 不再把 `device_history` 直接扩展到 `device v2`。
- 新建一套面向 `entity/device v2` 的“变更事件 + 字段变更 + 确认动作”模型。
- 先从 `device v2` 的写入边界接入，再逐步接采集、同步、投影、关系变化。

## 现状问题

### 1. 历史生成点分散，缺少统一边界

当前历史记录是业务代码里“顺手调用”的副作用：

- `OneOps/app/device/service/impl/device.go`
- `OneOps/app/job/tasks/meta/node/save_meta.go`
- `OneOps/app/job/tasks/server_oob/node/gpu_process.go`
- `OneOps/app/job/tasks/l2nodemap2/node/port_process.go`
- `OneOps/app/device/service/impl/device_store_controller.go`

这会导致：

- 同一类变更在不同链路里格式不一致
- 某些路径会漏记，某些路径会重复记
- 很难保证 old/new 数据来自同一个事务边界
- 无法知道一条历史到底来自人工修改、导入、同步、采集还是投影

### 2. 存储模型过于粗糙

当前表结构见：

- `OneOps/app/device/device_model/device_history.go`

只有这些核心字段：

- `event`
- `device_code`
- `device_name`
- `source`
- `new_data`
- `diff`
- `confirm`

这对 v2 明显不够，缺少：

- `entity_type`
- `entity_id`
- `subject_type`
- `subject_key`
- `change_source`
- `actor_type / actor_id`
- `request_id / task_id / correlation_id`
- `happened_at`
- `recorded_at`
- `field_path`
- `before_value / after_value`
- `change_summary`
- `severity`

结果就是：

- 只能“看到一坨前后 JSON”
- 不能按字段、来源、子对象、责任链查询
- 不能表达 access point、credential ref、relation、runtime projection 等 v2 场景

### 3. Diff 是文本 diff，不是结构化 diff

当前 diff 逻辑见：

- `OneOps/app/common/diff/diff.go`
- `OneOps/app/device/service/impl/device_history.go`

现有做法是对 JSON 字符串做 unified diff。

问题：

- 字段顺序变化也会造成噪音
- 缩进、空值、序列化差异会污染结果
- 前端无法直接做“字段级摘要”
- 无法稳定支持筛选“哪些字段变了”

### 4. Confirm 机制建模错误

当前确认逻辑见：

- `OneOps/app/device/service/impl/device_history.go`
- `OneOps/app/device/api/device_history.go`

问题：

- `confirm` 被直接存在历史记录上，历史记录不再是不可变事实
- 没有 `confirmed_by / confirmed_at / reason / scope`
- `PageList` 只能查 `confirm=true` 或 `confirm=false`，没有“全部”语义
- 确认动作本身没有审计记录

这更像“待办状态”，不是“历史事实”。

### 5. 机制已经出现明显漂移

`OneOps/app/device/service/impl/device_store_controller.go` 中 `generateDeviceHistory()` 会构造带 `Code` 的 `DeviceHistoryReq` 再调用 `Create()`。

但 `Create()` 在 `OneOps/app/device/service/impl/device_history.go` 中明确要求：

- `Code` 不能为空值前提不成立
- 如果传入非空 `Code` 会直接报错

这说明当前机制已经不是一个稳定、统一、可预期的历史系统，而是多个时期残留逻辑叠在一起。

## Device V2 的正确目标

`device v2` 的变更记录，不应该只是“设备表前后对比”，而应该是：

1. 记录实体事实变更
2. 可区分变更来源
3. 可定位到字段和子对象
4. 可关联执行链路
5. 可被确认，但确认是独立动作
6. 可为前端时间线、摘要卡、差异面板稳定供数

换句话说，底层应该是“事件模型”，不是“快照拼接表”。

## 建议的新模型

### A. 事件主表 `entity_change_event`

建议字段：

- `event_id`
- `entity_type`
- `entity_id`
- `entity_code`
- `subject_type`
- `subject_key`
- `event_type`
- `change_source`
- `actor_type`
- `actor_id`
- `actor_name`
- `request_id`
- `task_id`
- `run_id`
- `correlation_id`
- `summary`
- `severity`
- `happened_at`
- `recorded_at`
- `idempotency_key`

说明：

- `entity_type` 例如 `device_v2`
- `subject_type` 例如 `entity`, `access_point`, `credential_ref`, `relation`, `runtime_projection`, `observation`
- `subject_key` 用于标识某个子对象，例如 `access_points[in_band:ssh@10.0.0.1]`

### B. 字段变更表 `entity_change_field`

建议字段：

- `event_id`
- `field_path`
- `change_kind`
- `before_value`
- `after_value`
- `before_hash`
- `after_hash`
- `display_before`
- `display_after`

说明：

- `field_path` 例如 `attributes.hostname`
- `field_path` 例如 `attributes.access_points[in_band:ssh].ip`
- `field_path` 例如 `relation.connected_to[target=device-002]`

### C. 快照表 `entity_change_snapshot`

可选，用于保存事件发生时的结构化快照：

- `event_id`
- `snapshot_kind` (`before` / `after`)
- `payload`

用途：

- 前端需要完整上下文时可以展开
- 排查复杂问题时不依赖重算

### D. 确认动作表 `entity_change_ack`

建议字段：

- `ack_id`
- `event_id`
- `ack_by`
- `ack_by_name`
- `ack_at`
- `ack_reason`
- `ack_scope`

说明：

- 历史事件保持不可变
- “确认”是对事件的附加动作，不覆盖原事实

## 建议的事件分类

不要再只用 `device_update / gpu_update / port_update` 这种混合命名。

建议拆成两层：

### 业务事件类型

- `entity.created`
- `entity.updated`
- `entity.deleted`
- `relation.added`
- `relation.removed`
- `access_point.added`
- `access_point.updated`
- `access_point.removed`
- `credential_ref.bound`
- `credential_ref.unbound`
- `projection.updated`
- `runtime.observed_change`

### 变更来源

- `manual_edit`
- `device_v1_sync`
- `device_v2_ingest`
- `device_v2_store_pipeline`
- `controller_detect`
- `controller_collect`
- `collector_meta_job`
- `collector_gpu_job`
- `collector_port_job`
- `system_backfill`

这样前端就能同时回答两个问题：

- 发生了什么变化
- 这变化是由谁/哪条链路带来的

## Device V2 的接入边界

### 第一阶段必须接入

1. `device v2` 手工创建/编辑/删除
2. `device v2 ingest` 导入执行结果落库
3. `device v2` 从 v1 同步
4. `device v2 store/start` 最终对实体属性的写入
5. 关系新增/删除

### 第二阶段接入

1. controller detect 识别结果导致的属性修正
2. access point / credential ref 变化
3. runtime projection 导致的 metadata 回填

### 第三阶段再考虑

1. 观测类变化，如端口状态、GPU 运行态、meta 采集波动

这里建议单独归类为“观测变化”，不要和“台账变更”混为一谈。

这是当前历史机制最大的混乱来源之一。

## 关键设计原则

### 1. 台账变更和观测变化分层

- 台账变更：用户关心“设备定义被改了什么”
- 观测变化：用户关心“设备运行状态发生了什么”

如果继续放在同一层，v2 详情页的“变更记录”会永远很吵。

### 2. 事件不可变

事件一旦产生，不再修改。

允许新增：

- ack
- tags
- comments

不允许直接改原事件的事实部分。

### 3. 变更必须可追踪到来源

每条记录至少要能回答：

- 谁触发的
- 从哪条链路来的
- 属于哪个任务/请求
- 发生在什么时候

### 4. 差异必须结构化

前端最终要的不是一段大 diff 文本，而是：

- 变化摘要
- 变化字段列表
- 前后值
- 需要时再看完整快照

## 推荐的落地路径

### Phase 1: 新表与新服务

新增：

- `entity_change_event`
- `entity_change_field`
- `entity_change_ack`
- 可选 `entity_change_snapshot`

新增服务：

- `ChangeRecorder`
- `ChangeDiffBuilder`
- `ChangeQueryService`

### Phase 2: Device V2 双写

在 `device v2` 的写入边界双写：

- 老 `device_history` 不动
- 新 `entity_change_*` 开始写入

先覆盖：

- create
- update
- delete
- ingest apply
- v1 sync

### Phase 3: UI 改读新模型

前端的“变更记录”页签改成读新接口：

- 先展示摘要
- 再展开字段差异
- 再查看完整快照

### Phase 4: 老机制退场

确认新链路稳定后：

- `device_history` 只保留 legacy 查询
- v2 完全切到新模型

## 对前端的直接影响

在底层完成之前，不建议继续深入打磨 v2 详情页里的“变更记录”视觉。

原因：

- 现在能拿到的数据模型本身不可靠
- 任何 UI 设计都绕不开“事件语义不清”和“字段级信息缺失”
- 最终会返工

前端现在最多只应该做：

- 一个占位的历史入口
- 明确区分“台账变更”和“观测变化”
- 等待新接口契约稳定后再做正式工作台

## 建议的下一步

下一步不应该先改 UI，而应该先做以下三件事：

1. 设计 `entity_change_event / entity_change_field / entity_change_ack` 的 Go model 与 SQL
2. 在 `device v2` 的 `create/update/delete/ingest/sync` 路径接第一版 `ChangeRecorder`
3. 给前端一个最小可用查询接口：
   - `按 entity_code 查事件列表`
   - `按 event_id 查字段差异`
   - `按 event_id 查 before/after 快照`

如果继续推进，我建议我下一步直接开始：

- 先补新表 model 与 DTO
- 再加 recorder 接口和最小实现
- 最后把 `device v2` 的写路径接进去
