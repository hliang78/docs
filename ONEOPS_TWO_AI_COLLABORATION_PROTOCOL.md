# OneOPS 双 AI 协作协议与同步模板

本文档用于约束两个 AI 在同一主线下并行开发时的协作方式。

目标只有三个：

1. 不重复建设
2. 不相互踩接口
3. 不偏离主线

配套文档：

- [ONEOPS_TWO_AI_MAINLINE_TASK_SPLIT.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_TWO_AI_MAINLINE_TASK_SPLIT.md)
- [ONEOPS_TWO_AI_EXECUTION_PROMPTS.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_TWO_AI_EXECUTION_PROMPTS.md)
- [ONEOPS_TWO_AI_FIRST_ROUND_ACCEPTANCE_CHECKLIST.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_TWO_AI_FIRST_ROUND_ACCEPTANCE_CHECKLIST.md)

---

## 1. 协作总原则

### 1.1 同一语义只能有一个真相源

以下内容只允许有一套正式定义：

- `observation_batch_id`
- `collection_run.state`
- `processing_run.state`
- `topology_snapshot.state`
- readiness 枚举
- 错误分类枚举

谁先负责定义，谁就拥有主维护权。
另一方只能复用，不能再发明一套。

### 1.2 契约优先于实现

如果某一方发现缺少关键契约，应该先把契约补齐，再继续实现。

禁止：

- 先绕开契约硬做
- 先在本地写一套“临时字段”
- 先用字符串拼装状态，等以后再统一

### 1.3 前端必须晚于契约冻结

前端相关工作必须建立在：

- API 返回结构已定
- 状态字段已定
- 错误字段已定

之后再推进。

禁止：

- 前端先做页面，再倒逼后端状态字段
- 页面靠多个字段组合推断业务状态

### 1.4 先暴露问题，再继续实现

如果出现下面任一情况，必须先停下来对齐：

- 两边都准备新增状态枚举
- 两边都准备新增相似 DTO
- 一方准备 fallback 到旧逻辑
- 一方准备改动对方主维护的真相源

---

## 2. 角色与所有权

## 2.1 AI-1 所有权

AI-1 拥有主维护权的内容：

- `CollectionRun`
- `ObservationBatch`
- 设备级采集结果模型
- 采集相关状态枚举
- 采集相关错误分类
- 采集相关 API 契约

AI-2 不应直接重写这些定义。

## 2.2 AI-2 所有权

AI-2 拥有主维护权的内容：

- `ProcessingRun`
- `TopologySnapshot`
- 处理相关状态枚举
- 处理入口错误返回语义
- snapshot 相关 API 契约
- 最小前端状态页

AI-1 不应直接重写这些定义。

## 2.3 共享内容

以下内容需要双方共同遵守，但必须明确唯一文件或唯一包作为真相源：

- readiness 枚举
- API 错误响应格式
- 主线文档中的命名

建议：

- 共享枚举放在一个正式公共位置
- 不要在两个模块里各自 copy 一份

---

## 3. 接口冻结规则

## 3.1 第一轮必须冻结的接口

第一轮只冻结以下最小接口：

### 采集侧

- 创建 collect run
- 查询 collect run
- 查询 observation batch
- 查询设备级采集结果

### 处理侧

- 创建 processing run
- 查询 processing run
- 查询 processing run 对应的 input batch
- 查询 topology snapshot

### 前端侧

- 列表接口
- 详情接口
- 错误摘要字段
- readiness 字段

第一轮不要冻结更多内容。

## 3.2 冻结后允许改什么

冻结后只允许改：

- 字段实现
- 内部存储结构
- 错误信息内容细化

冻结后不允许随意改：

- 字段名
- 状态值
- readiness 语义
- id 字段含义

如果必须改，必须走“变更说明”。

---

## 4. 每日同步格式

两个 AI 每轮都必须输出统一格式的同步信息。

建议固定为下面五段。

## 4.1 今日推进

格式：

- 我推进了哪一步主线
- 改动了哪几个核心文件
- 当前结果是什么

示例：

```text
今日推进：
- 已落 CollectionRun 最小模型
- 已让 IfTable 采集生成 observation_batch
- 已补 collect run 查询接口
```

## 4.2 当前真相源

格式：

- 当前我主维护的模型或契约在哪里

示例：

```text
当前真相源：
- observation batch 模型：xxx
- collection run state 枚举：xxx
- collect run API 契约：xxx
```

## 4.3 对对方的依赖

格式：

- 我还依赖对方补什么
- 没有这些我无法继续推进哪一步

示例：

```text
对方依赖：
- 需要 processing run 明确 input_observation_batch_id 字段
- 没有该字段，前端无法联通 run 详情页
```

## 4.4 当前阻塞

格式：

- 当前阻塞是什么
- 是契约阻塞、数据阻塞，还是实现阻塞

示例：

```text
当前阻塞：
- snapshot readiness 枚举尚未冻结
- 如果现在继续写前端状态页，后续会返工
```

## 4.5 明日计划

格式：

- 明天只做哪一小步

示例：

```text
明日计划：
- 只补 observation batch 详情接口
- 不扩展新的采集类型
```

---

## 5. 变更说明模板

如果任一方要修改对方依赖的契约，必须给出最小变更说明。

模板如下：

```text
变更说明：
- 变更对象：
- 变更前：
- 变更后：
- 变更原因：
- 对你影响的文件/接口：
- 你是否需要同步修改：
```

示例：

```text
变更说明：
- 变更对象：processing run 状态字段
- 变更前：status
- 变更后：state
- 变更原因：与 collection run / snapshot 统一
- 对你影响的接口：processing run 列表接口、详情接口
- 你是否需要同步修改：前端页面字段映射需要调整
```

未发变更说明就直接改契约，视为违规。

---

## 6. 冲突处理规则

## 6.1 同时发现同一问题

如果两边同时发现同一个问题，只允许：

- 由拥有主维护权的一方修
- 另一方只记录依赖，不重做

## 6.2 接口未冻结时发生分歧

优先级如下：

1. 是否更贴近第一轮最小闭环
2. 是否能减少后续返工
3. 是否减少吞错和 fallback
4. 是否更少字段、更少状态、更少抽象

也就是说：

- 选更小的
- 选更明确的
- 不选更“通用”的

## 6.3 一方发现另一方在做过度设计

应直接指出，并用一句话收敛：

- “这个改动不直接服务第一轮最小闭环，建议延后”

不要再展开新平台讨论。

---

## 7. 前后端协作规则

## 7.1 后端先冻结最小状态语义

前端只能消费正式字段：

- `state`
- `readiness`
- `error_summary`
- `input_observation_batch_id`

前端不允许自己推断：

- “有 finished_at 就算成功”
- “列表为空就算成功”
- “有 id 就算已经发布”

## 7.2 前端页面优先级

第一轮前端页面优先级固定为：

1. collect run 列表 / 详情
2. processing run 列表 / 详情
3. topology snapshot 列表 / 详情

第一轮不做：

- 复杂图谱页
- 高级筛选器
- 配置中心
- 统一控制台

## 7.3 前端验收标准

前端页面最少要做到：

- 能看见状态
- 能看见 readiness
- 能看见错误摘要
- 能看见关键关联 id

如果页面只是“有个按钮”，不算完成。

---

## 8. 阻塞升级规则

下面这些阻塞不能拖，要立即升级：

### 8.1 P0 阻塞

- batch id 语义不一致
- state 枚举不一致
- API 字段名冲突
- 一方准备 fallback 到旧逻辑
- 一方继续吞错

处理方式：

- 立即暂停相关实现
- 先对齐契约

### 8.2 P1 阻塞

- 前端页面依赖的字段尚未冻结
- 错误摘要结构尚未定
- readiness 语义尚未定

处理方式：

- 后端先出最小契约
- 前端暂缓

### 8.3 P2 阻塞

- 文案不统一
- 页面样式细节
- 列表筛选项扩展

处理方式：

- 第一轮先不阻塞主线

---

## 9. 第一轮禁止扩展清单

两个 AI 都不要主动扩展下面这些内容：

- L3 forwarding 正式模型
- 安全拓扑正式模型
- 多租户复杂隔离抽象
- 通用规则引擎
- 自动重试编排中心
- 复杂拓扑图可视化
- 智能诊断建议
- 自动补数据
- 自动纠错

如果有人开始做这些，说明已经跑偏。

---

## 10. 第一轮完成后的联合复盘模板

第一轮结束后，两个 AI 都要各自按下面模板汇报。

```text
第一轮复盘：
- 我负责的最小闭环部分是否已打通：
- 当前正式真相源在哪里：
- 我仍然发现的主线缺口：
- 我为了避免兜底而选择显式失败的点：
- 下一轮最小建议：
```

---

## 11. 你作为协调者要重点盯的四件事

你不需要每天读完所有代码。

你只需要重点盯下面四件事：

1. `observation_batch_id` 有没有分叉
2. `processing_run.input_observation_batch_id` 有没有真的接上
3. `DevicePorts` 有没有还在偷偷走“最近一条”
4. 前端是不是在自己猜状态

只要这四件事没有跑偏，整体大概率就在主线上。

---

## 12. 最终判断

双 AI 并行最大的风险不是谁写得慢，而是：

- 各自开始补自己的“合理抽象”
- 最后接口没对齐

所以这个阶段最重要的不是“多做”，而是：

- 少做
- 做准
- 做同一条主线

只要双方能把：

- collection run
- observation batch
- processing run
- topology snapshot

这四个边界立住，后面的 L2、L3、安全拓扑扩展才会稳。
