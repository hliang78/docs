# OneOPS Device V2 自动补齐设备型号设计

Date: 2026-06-23

## 背景

当前 Device V2 到 Device V1 的同步链路中，`platform`、`catalog`、`site`、`rack` 已经支持按编码或名称归一化，但 `device_model` 仍然要求上游直接提供 `device_model_code`。

这带来一个明显断点：

- 采集链路已经识别出 `manufacturer/platform/catalog/model/version`；
- Device V2 元数据里已经保存了 `manufacturer_name`、`device_model_name`；
- 但如果基础主数据表里没有对应 `device_model`，V1 设备仍会以 `device_model_code = NULL` 入库；
- 后续依赖 V1 结构化型号信息的监控策略选择、厂商归因、能力投影就可能降级或失真。

本次问题样本中，`DVCCF907BD02C79` 和 `DVCA55373B28C80` 已识别到：

- `manufacturer_name = H3C`
- `platform_name = Comware`
- `catalog_name = ROUTER`
- `device_model_name = VSR1000`

但库中不存在 `VSR1000` 对应的 `device_model` 记录，导致 V1 设备 `device_model_code` 为空，最终监控只落到了 `ping-basic`，没有进入预期的 `snmp-passthrough` 选择结果。

## 设计目标

### 产品目标

只要系统已经稳定识别出：

- 明确厂商；
- 明确设备型号；

那它就不应该因为缺少预置 `device_model` 主数据而中断后续链路。系统应自动补齐结构化设备型号，并关联到已存在厂商。

### 功能目标

在 Device V2 同步到 V1 前，自动完成以下动作：

1. 识别 Device V2 中的厂商名与型号名；
2. 命中现有 `device_model` 时直接复用；
3. 未命中时自动创建新的 `device_model`；
4. 创建时绑定已存在厂商；
5. 将新得到的 `device_model_code` 回填到同步上下文；
6. 让后续 V1 同步、监控选择、厂商归因自然复用现有链路。

### 诊断目标

整个自动补型号过程必须可追踪，出现问题时能快速区分：

- 没识别到厂商；
- 没识别到型号；
- 厂商不存在；
- 型号已存在并被复用；
- 型号不存在且自动创建成功；
- 型号创建失败；
- 型号已创建但未成功回填到 V1 同步请求。

## 范围

### 本次纳入设计

- Device V2 同步到 V1 时的 `device_model` 自动解析与自动创建
- 仅基于已存在厂商自动创建新型号
- 自动创建过程的诊断日志
- 单元测试与 sqlite 集成测试补齐

### 本次不纳入设计

- 自动创建新厂商
- 监控策略选择器整体重构
- `device_model` 表结构改造
- 采集候选引擎规则重写
- 历史设备批量回填修复任务

## 总体方案

采用：

- `厂商必须已存在`
- `仅自动创建设备型号`
- `同步前归一化补齐`
- `先查后建，幂等复用`
- `全过程诊断日志`

不采用：

- 厂商不存在时自动建厂商
- 监控下发阶段临时按文本厂商/型号兜底
- 仅打日志不修复主数据

原因：

- 自动创建设备型号是最小必要补齐，风险远低于自动创建厂商；
- 在同步前补齐结构化型号，可以复用现有 V1、监控、投影链路，不需要再引入第二套“文本身份识别”分支；
- 只打日志不能解决当前“识别到了，但仍推不下去”的产品问题。

## 触发规则

自动补型号仅在以下条件同时满足时触发：

1. `device_model_code` 为空；
2. `device_model_name` 非空；
3. `manufacturer_name` 非空；
4. 当前操作处于 Device V2 同步到 V1 的归一化阶段。

以下情况不触发自动创建：

- 已有 `device_model_code`
- 缺少 `device_model_name`
- 缺少 `manufacturer_name`
- 厂商名无法命中现有 `manufacturer`

## 数据来源

型号与厂商解析优先使用 Device V2 已有归一化元数据，推荐顺序：

### 型号名

1. `attributes.device_model_name`
2. `metadata.device_model_name`
3. `attributes.model`
4. `metadata.model`

### 厂商名

1. `attributes.manufacturer_name`
2. `metadata.manufacturer_name`
3. `attributes.manufacturer`
4. `metadata.manufacturer`
5. `attributes.vendor`
6. `metadata.vendor`

设计原则：

- 优先使用已经归一化过的字段；
- 兼容历史字段；
- 一旦命中有效值，后续链路只使用标准化结果，不再重复自由文本判断。

## 实现位置

主实现入口放在：

- `OneOps/app/device/v2/api/device_v2_sync_to_v1.go`

具体落点：

- `normalizeDeviceV2ForV1Sync`

原因：

- 这里已经承担了 `platform/catalog/site/rack` 的归一化职责；
- `buildDeviceV1SyncReqFromDeviceV2` 已直接读取归一化后的 `device_model_code`；
- 在这里补齐，能最小化对现有 V1 创建/更新逻辑的侵入。

## 处理流程

### Step 1：读取当前归一化上下文

从 Device V2 的 `Attributes` 与 `Metadata` 中读取：

- `device_model_code`
- `device_model_name`
- `manufacturer_name`

如果已存在 `device_model_code`，直接结束，不做额外处理。

### Step 2：解析厂商

按厂商名调用现有基础服务查询：

- 命中：拿到 `manufacturer_id`
- 未命中：不自动建厂商，记录诊断日志，结束自动建模流程

### Step 3：查找现有型号

按型号名调用现有 `DeviceModel` 查询：

- 命中：复用现有型号编码
- 未命中：进入创建流程

### Step 4：创建新型号

使用现有基础服务 `Create` 新建设备型号，字段规则如下：

- `name = 识别到的 device_model_name`
- `manufacturer_id = 已命中的 manufacturer.id`
- `description = "auto-created from device_v2 sync"`
- `support = true`
- `u_height = 1`
- `sub_device_role = 空`

`u_height = 1` 不是业务事实声明，而是满足当前基础服务必填约束的最小默认值。后续若基础主数据要求更严格，可再单独收紧。

### Step 5：回填归一化结果

将最终得到的 `device_model_code` 回填到：

- `normalized.Attributes["device_model_code"]`
- `normalized.Metadata["device_model_code"]`

如有必要，也同步补齐：

- `normalized.Metadata["device_model_name"]`
- `normalized.Metadata["manufacturer_name"]`

### Step 6：沿用现有同步链路

后续 `buildDeviceV1SyncReqFromDeviceV2` 保持不变，直接读取补齐后的 `device_model_code`，让 V1 设备获得结构化型号。

## 幂等规则

自动补型号必须满足以下幂等性要求：

1. 同一型号名若已存在，不重复创建；
2. 重复同步同一 Device V2，不重复创建；
3. 同一批次多个设备识别出同一型号，不应创建多条同名记录；
4. 型号创建成功后，后续重试应直接复用。

实现上允许使用：

- 先查后建；
- 若并发下创建撞唯一约束，再二次查询回收已有记录。

## 诊断日志设计

自动补型号过程中的关键节点必须全部进入诊断日志或常规结构化日志，至少包含：

### 开始阶段

- `device_v2_code`
- `device_v1_code`（若已知）
- `manufacturer_name`
- `device_model_name`
- `existing_device_model_code`

### 厂商解析阶段

- 是否命中厂商
- `manufacturer_id`
- 未命中原因

### 型号解析阶段

- 是否命中已有型号
- 命中的 `device_model_code`

### 自动创建阶段

- 是否进入自动创建
- 创建参数摘要
- 创建成功后的 `device_model_code`
- 创建失败错误

### 回填阶段

- 是否成功回填到归一化设备对象
- 最终同步请求中的 `device_model_code`

### 推荐日志语义

建议使用明确、可 grep 的事件名，例如：

- `device_v2 sync device_model resolve start`
- `device_v2 sync manufacturer resolved`
- `device_v2 sync device_model reused`
- `device_v2 sync device_model auto_created`
- `device_v2 sync device_model resolve skipped`
- `device_v2 sync device_model resolve failed`

## 错误处理

### 可跳过错误

以下情况不应阻断整个 V1 同步，只应记录诊断并允许链路继续：

- 未识别到厂商名
- 未识别到型号名
- 厂商未命中

原因：

- 这些情况属于“自动增强失败”，不是同步基础必填字段错误；
- 继续同步至少能保留当前已有能力，不应因为增强失败把整条链路打死。

### 应阻断错误

以下情况建议阻断本次归一化并返回错误：

- 查询基础表失败
- 创建 `device_model` 时数据库报错且无法通过二次查询回收

原因：

- 这类错误属于系统执行异常，不是单纯数据缺失；
- 若静默吞掉，后续行为会不稳定且更难定位。

## 测试设计

### 单元测试

覆盖以下最小场景：

1. 已有 `device_model_code`
- 不查厂商
- 不查型号
- 不创建新型号

2. 缺少 `manufacturer_name`
- 跳过自动建模
- 保持原行为

3. 缺少 `device_model_name`
- 跳过自动建模
- 保持原行为

4. 厂商存在，型号已存在
- 复用已有 `device_model_code`
- 不创建新记录

5. 厂商存在，型号不存在
- 自动创建新型号
- 正确关联厂商
- 回填 `device_model_code`

6. 厂商不存在
- 不自动建厂商
- 记录跳过日志

7. 创建时撞唯一约束
- 通过二次查询成功回收已有型号

8. 创建成功后
- `buildDeviceV1SyncReqFromDeviceV2` 读到正确 `device_model_code`

### sqlite 集成测试

建议补一组 sqlite 测试，验证：

- `manufacturer` 预置存在；
- `device_model` 不存在；
- 调用归一化后自动创建；
- 最终 V1 同步请求带上新 `device_model_code`；
- 同一数据重复执行不会产生第二条 `device_model` 记录。

### 真实样本回归

优先用当前问题样本回归：

- `DVCCF907BD02C79`
- `DVCA55373B28C80`

预期：

- 自动创建或复用 `VSR1000`
- 对应 V1 设备补上 `device_model_code`
- 后续监控选择恢复到带 SNMP 的预期路径

## 回归风险

### 风险 1：错误厂商绑定

若上游识别到的厂商名本身错误，会把型号绑定到错误厂商。

缓解：

- 不自动创建厂商；
- 记录完整日志；
- 后续如发现误判，可按基础主数据治理处理。

### 风险 2：全局同名型号冲突

当前 `device_model.name` 为全局唯一，不是厂商内唯一。

这意味着：

- 不同厂商若存在同名型号，会发生结构性冲突；
- 当前方案只能先遵从现有表结构；
- 中长期建议评估改为 `manufacturer_id + name` 联合唯一。

本次不在实现中改表，只把它明确列为已知弱点。

### 风险 3：主数据污染

若候选识别噪声较大，可能自动创建低质量型号名。

缓解：

- 仅在厂商与型号都明确时触发；
- 仅在同步到 V1 时触发，不扩大触发面；
- 完整落日志，便于后续治理；
- 后续如有需要，可加入命名合法性规则白名单或最小长度限制。

## 兼容性

该方案对现有链路的兼容方式是：

- 不改 V1 设备接口合同；
- 不改监控下发接口合同；
- 不改 Device V2 候选引擎输出合同；
- 只在同步归一化阶段补齐缺失的结构化型号信息。

因此它应当是一次“补主数据缺口”的局部增强，而不是新链路。

## 成功标准

满足以下条件即视为设计达标：

1. 采集已识别出厂商与型号时，V1 同步后能拿到结构化 `device_model_code`；
2. 未预置的型号会被自动创建，并绑定到已存在厂商；
3. 不会自动创建新厂商；
4. 整个过程有可检索诊断日志；
5. 重复执行不产生重复型号；
6. 当前 `VSR1000/H3C` 样本能恢复到正确的 SNMP 监控选择路径。

## 后续计划建议

本设计完成后，下一步实施计划应聚焦：

1. 在 `normalizeDeviceV2ForV1Sync` 增加型号解析/创建辅助函数；
2. 给 `DeviceV2API` 注入 `ManufacturerSrv` 与 `DeviceModelSrv`；
3. 为自动补型号补齐单元测试与 sqlite 集成测试；
4. 在真实样本上完成回归验证；
5. 单独登记 `device_model.name` 全局唯一的结构弱点，作为后续基础模型治理项。
