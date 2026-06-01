# ZB External Store And Device V2 Inbound E2E Test Design

## 1. 背景

当前需要验证的不是单一接口或单一服务，而是两条真实业务入口驱动的同一条主链路：

1. `ZB` 外部调用入口
2. 页面 `device v2` 入库入口

目标不是“接口能返回成功”，而是：

- 尽量多走真实 `detect`、真实采集、真实 `store/manage` 链路
- 主动通过修改数据、注入脏数据、制造事实冲突，压出平时不易自然出现的问题
- 对暴露的问题进行修复，并将修复固化到可重复执行的端到端测试体系中

当前运行环境允许：

- 注入脏数据
- 修改过程数据
- 验证数据库最终态
- 验证 agent 侧监控任务下发结果

因此本方案按“全真联调优先 + 可控注错补足”的方式设计。

---

## 2. 设计目标

本方案目标分为四层：

### 2.1 业务目标

验证以下两个入口都能驱动真实入库主链：

1. `ZB Store`
2. 页面 `device v2` 入库

并确认它们进入同一主链后，核心行为一致：

- `prepare`
- `detect`
- `collect`
- `store`
- `manage`
- `sync_to_v1`
- `monitor_push`

### 2.2 质量目标

验证系统在正常数据和脏数据下都具备：

- 正确成功
- 正确失败
- 正确阻断
- 正确归因
- 正确回调或展示
- 正确恢复与重试

### 2.3 可观测目标

每条场景都必须能同时从以下多个面拿到证据：

- 入口返回
- seed / 导入中间态
- pipeline 过程态
- detect / collect 过程证据
- 数据库最终态
- agent 监控任务
- 外部 callback 或页面可见结果

### 2.4 体系目标

沉淀一份可长期扩展的测试总纲：

- 每条用例有稳定编号
- 每条用例先用一句话描述
- 后续可持续追加新 case
- 追加后可逐条展开为详细造数、执行、断言与修复任务

---

## 3. 被测范围

### 3.1 入口范围

#### 入口 A：ZB 外部调用

主链：

`ZB Store -> precheck -> credential/community 构造或复用 -> UpsertSeed -> StartPipeline -> prepare -> detect -> collect -> store -> manage -> sync_to_v1 -> monitor_push -> callback`

#### 入口 B：页面 device v2 入库

页面入口拆分为两类：

1. 页面导入链路
   `CreateBatch -> Upload -> Validate -> Apply -> 进入 device_v2 主链`
2. 页面 store/start 链路
   `store/start -> StartPipeline -> prepare -> detect -> collect -> store -> manage -> sync_to_v1 -> monitor_push`

### 3.2 主链范围

无论从哪个入口进入，一旦进入 `entity_v2 pipeline`，都属于统一主链范围：

- `pre_register`
- `prepare`
- `detect`
- `device_collection2 / manual collect`
- `facts / observation`
- `store decision`
- `core store`
- `manage`
- `sync_to_v1`
- `monitor_push`

### 3.3 关键数据范围

至少覆盖以下数据层：

- `entity_instance`
- `entity_pipeline_task`
- `device_v2`
- `device_v2_store_run`
- `device_v2_observation`
- `device_v2_import_batch`
- `device_v2_import_record`
- 必要时的 `device_v1`
- Secret / Community / credential refs
- 站点、机柜、租户、前缀等引用表
- agent 监控任务相关落点

---

## 4. 不纳入本轮核心范围的内容

以下内容不作为本轮 P0 核心，但可在后续总纲中持续增加：

- 全量前端 UI 交互细节
- 非入库主线的 schema 编辑能力
- 历史迁移类工具
- 与本轮目标无直接关系的只读报表能力

说明：

不是永久排除，而是不在本轮“真实 detect/采集 + 双入口对照”的第一优先级中。

---

## 5. 主链业务定义

本轮 E2E 的核心不是单接口成功，而是“一台设备在整条链上的命运”。

### 5.1 统一业务主链

一台设备从进入系统到完成闭环，至少经过以下阶段：

1. 入口接收
2. 最小建档或导入中间态
3. pipeline 启动
4. `prepare`
5. `detect`
6. `collect`
7. `facts / observation / prepared resources`
8. `store decision`
9. `core store`
10. `manage`
11. `sync_to_v1`
12. `monitor_push`
13. 外部 callback 或页面结果呈现

### 5.2 单设备作为最小测试单位

每条详细用例最终都要回答：

- 这台设备进入了哪条入口
- 在哪一段成功或失败
- 为什么成功或失败
- 数据落成了什么样
- agent 是否收到了正确任务
- callback 或页面结果是否真实反映内部状态

---

## 6. 多面观测模型

每条场景必须从以下八个观测面同时验证：

### 6.1 入口面

- `ZB Store` 同步返回
- 页面 `CreateBatch/Upload/Validate/Apply/store/start` 返回

### 6.2 中间态面

- `ZB seed` 写入结果
- 页面导入 batch / record 状态

### 6.3 pipeline 面

- `entity_pipeline_task`
- `stages_json`
- `result_json`

### 6.4 detect / collect 面

- detect 执行结果
- DC2/manual collect 是否真实发生
- dataset / contract / facts 是否符合预期

### 6.5 store / 决策面

- `device_v2_store_run`
- `decision`
- `store_gate`
- `core_store_status`

### 6.6 数据库最终态面

- `entity_instance`
- `device_v2`
- `device_v1`
- 相关附属表

### 6.7 agent 面

必须验证：

- agent 是否收到监控任务
- 任务是否发给正确 agent
- 任务内容是否正确
- 平台状态与 agent 真实结果是否一致

### 6.8 外部呈现面

- `ZB callback`
- 页面查询接口 / 页面任务视图

### 6.9 一致性目标

每条用例最终要验证：

`入口返回 = pipeline状态 = DB最终态 = agent任务结果 = callback/页面结果`

只要其中一面不一致，就判定该用例发现问题，而不是通过。

---

## 7. 测试策略

### 7.1 总体策略

采用双轨方案：

1. 全真联调主轨
   - 尽量真实触发 `detect`
   - 尽量真实触发采集
   - 尽量真实走 `store/manage/sync/monitor`

2. 可控注错辅轨
   - 通过改入参、改 seed、改引用表、改 facts、改中间态数据等手段模拟复杂事故

### 7.2 策略原则

不是所有错误都要前置拦截。

需要同时覆盖三种形态：

1. 前置拦截
2. 带病进入中段后失败
3. 主链成功但闭环失败

这样才能覆盖真实生产场景。

---

## 8. 双入口设计

### 8.1 入口独立验证

#### ZB 专属验证

- `precheck`
- `credential/community` 构造
- `UpsertSeed`
- `callback`
- 外部字段映射到 seed / entity 的正确性

#### 页面专属验证

- `CreateBatch`
- `Upload`
- `Validate`
- `Apply`
- namespace / import pass 策略
- 页面触发 `store/start` 的 pipeline 参数

### 8.2 主链共性验证

对两个入口统一验证：

- `prepare`
- `detect`
- `collect`
- `store`
- `manage`
- `sync_to_v1`
- `monitor_push`
- DB 最终态
- agent 任务结果

### 8.3 双入口对照验证

对同一类设备、同一类脏数据，分别从：

- `ZB`
- 页面导入
- 页面 `store/start`

触发验证，比较以下是否一致：

- detect 分类
- collect 行为
- facts 结果
- store decision
- DB 最终态
- agent 监控任务

---

## 9. 场景分层

### 9.1 黄金成功样本

至少准备以下基线样本：

1. `ZB-Server-SSH`
2. `ZB-Network-SNMP`
3. `ZB-Network-SSH+SNMP`
4. `ZB-Reuse-Existing-DeviceV2`
5. `ZB-Partial-Manage`
6. `ZB-Monitor-Push-Success`
7. 页面导入正常网络设备
8. 页面导入正常服务器
9. 页面 `store/start` 正常复用已有 `device_v2`

### 9.2 detect / collect 分歧样本

至少覆盖：

1. detect 正确识别网络设备
2. detect 正确识别服务器
3. detect 信息不足无法分类
4. detect 成功但 contract 或 dataset 选错
5. collect 失败
6. collect 成功但 facts 缺关键 identity
7. facts 与 seed 冲突
8. candidate engine 改写画像

### 9.3 脏数据注入样本

至少覆盖：

1. `site_code` 不存在
2. `rack_code` 不存在
3. `rack/site` 不匹配
4. credential ref 缺失
5. SNMP community 错误
6. 重复 `in_band_ip`
7. 重复 `sn`
8. `hostname` 命中多个设备
9. seed `metadata` 与 `attributes` 冲突
10. facts 与 seed 冲突

### 9.4 稀有现场模拟样本

至少覆盖：

1. 同设备多锚点命中多个 `device_v2`
2. 错误复用到旧设备
3. prepare success 但 store blocked
4. store success 但不进入 manage
5. manage success 但 `sync_to_v1` 失败
6. `sync_to_v1` success 但 `monitor_push` 失败
7. agent 收到任务但任务内容错误
8. callback 成功但内部实际 partial

### 9.5 恢复与幂等样本

至少覆盖：

1. 修 seed 后 retry
2. 修 facts 后 retry
3. 修凭据后 retry
4. 部分成功批次局部重跑
5. 同一设备重复触发
6. 监控推送失败后补推
7. callback 失败后重新汇总

---

## 10. 错误注入模型

### 10.1 ZB 入参层

适合注入：

- 缺 `device_code`
- 缺 `device_name`
- 缺 `site_code/rack_code`
- 非法 `attribution_type`
- 服务器缺 SSH 密码
- 网络设备缺 `in_band_ip/community`

目标：

- 验证 `precheck`
- 验证同步拒绝
- 验证不写 seed、不起 pipeline

### 10.2 引用数据层

适合注入：

- 错 `site_code`
- 错 `rack_code`
- `rack` 不属于 `site`
- tenant / prefix / function area 失配
- credential/community 指向错误对象

目标：

- 验证基础引用校验
- 验证入口与中段不同层次的拦截逻辑

### 10.3 seed 实体层

适合注入：

- `attributes.attribution_type` 与 `metadata.zb_attribution_type` 不一致
- `code` / `biz_code` / `zb_requested_device_code` 冲突
- credential refs 层级不一致
- `hostname/sn/ip` 形成复用歧义
- `labels.source` 与 `metadata.source` 冲突

目标：

- 验证最小建档边界
- 验证 prepare / detect / store 是否被错误引导

### 10.4 detect / facts 层

适合注入：

- detect 分类错误
- dataset 缺失
- facts 缺关键 identity
- facts vendor/platform/model 冲突
- facts 与 seed 冲突
- candidate engine 改写错误画像

目标：

- 验证 detect/collect 是否真实生效
- 验证 decision 是否可解释

### 10.5 store / manage 后置层

适合注入：

- `readyForManage=false`
- manage 依赖缺失
- `sync_to_v1` 失败
- `monitor_push` 失败
- agent 任务内容错误

目标：

- 验证闭环问题不会被“入库成功”掩盖

### 10.6 外围一致性层

适合注入：

- callback 内容错
- agent 收到任务但 DB 标记失败
- monitor push 成功但任务内容错误
- 页面任务视图与 DB 不一致

目标：

- 验证多面一致性

---

## 11. 双入口场景矩阵

### 11.1 ZB 专属场景

#### precheck 类

- 缺基础必填
- 引用基础信息缺失
- 归属类型非法
- 服务器 SSH 凭据不完整
- 网络设备 SNMP 资料不完整

#### seed 类

- 正常 seed
- 复用已有 `device_v2`
- 多候选冲突
- Secret / Community 创建失败

#### callback 类

- 全成功
- partial
- seed 失败
- pipeline 启动失败
- monitor push 失败
- callback 与内部状态不一致

### 11.2 页面专属场景

#### 导入链路类

- 正常 `CreateBatch/Upload/Validate/Apply`
- Validate 因重复 code 失败
- Apply 部分成功
- Retry 指定 record
- Update records 后重校验重应用

#### namespace / pass 类

- `infra/device`
- `infra/application`
- base anchor 仅 warn
- relation pass 行为

#### store/start 类

- 已有设备触发 pipeline
- 非法 options
- legacy option 拒绝
- 正常进入 detect / collect

### 11.3 双入口对照场景

#### 正常对照

- 服务器正常成功
- 网络设备 SNMP-only 正常成功
- 网络设备 SSH+SNMP 正常成功

#### detect / collect 异常对照

- detect 模糊
- dataset 缺失
- facts 缺 identity
- facts 与 seed 冲突
- candidate engine 改写画像

#### 数据冲突对照

- 重复 `sn`
- 重复 `ip`
- 复用已有 `device_v2`
- 多锚点命中

#### 闭环对照

- manage partial
- `sync_to_v1` failure
- `monitor_push` failure
- agent 任务内容错误

---

## 12. 验收断言模板

每条详细用例统一按以下九组断言收口。

### 12.1 入口断言

- 是否按预期同步接受、拒绝或部分接受
- 返回的阶段和错误码是否正确

### 12.2 seed / 导入中间态断言

ZB：

- `labels.source=zb`
- `minimal_registration.mode=zb_seeded`
- 关键字段保真

页面：

- batch / record 状态
- `normalized_patch`
- `resolved_entity_id`

### 12.3 pipeline 断言

- `entity_pipeline_task`
- `current_stage`
- `overall_status`
- `stages_json`
- `result_json`

### 12.4 prepare / detect 断言

- detect 是否触发
- detect 结果是否符合预期
- candidate engine 是否正确运行
- `prepare_summary` / `prepare_device_runs`

### 12.5 collect / facts / observation 断言

- collect 是否真实执行
- dataset / contract 是否正确
- `device_v2_observation`
- facts 是否完整或按预期冲突

### 12.6 store / 决策断言

- `device_v2_store_run`
- `decision`
- `store_gate`
- `core_store_status`
- `manageable_status`

### 12.7 manage / sync_to_v1 断言

- `manage_device_runs`
- `sync_to_v1_status`
- `device_v1_code`

### 12.8 agent 监控任务断言

必须验证：

- agent 是否收到任务
- 任务投递目标是否正确
- 任务内容是否正确
- 平台与 agent 结果是否一致

### 12.9 外部呈现断言

ZB：

- callback 顶层状态
- `summary`
- `summary_v2`

页面：

- batch/task 查询接口
- 页面任务视图对应数据

### 12.10 最终结论格式

每条用例收口四个结论：

1. 业务结果
2. 阶段结果
3. 数据结果
4. 一致性结果

只要一致性结果失败，该用例就判定发现问题。

---

## 13. 测试总纲

### 13.1 设计目标

在详细用例之外，单独维护一份“测试总纲”，用于长期驱动新增场景。

总纲不是执行步骤文档，而是用例目录。

### 13.2 每条总纲记录字段

每条用例固定包含：

- `Case ID`
- `入口`
- `设备类型`
- `场景标签`
- `一句话描述`
- `当前状态`

### 13.3 编号规则

- `ZB-001` 起：ZB 外部调用
- `UII-001` 起：页面导入链路
- `UIS-001` 起：页面 `store/start`
- `CMP-001` 起：双入口对照场景

### 13.4 一句话描述规范

格式：

`[对象] 在 [条件/异常] 下，预期 [结果/卡点]`

示例：

- `ZB-001 | ZB | 网络设备 | 正常 | ZB 录入一台 SNMP-only 网络设备，预期完整走到 monitor push 成功 | planned`
- `ZB-006 | ZB | 服务器 | precheck | ZB 录入服务器但缺 SSH 密码，预期同步 precheck 拦截且不写 seed | planned`
- `UII-004 | 页面导入 | 网络设备 | collect | 页面导入网络设备后 detect 成功但 facts 缺 serial_number，预期在 store decision 被阻断 | planned`
- `UIS-003 | 页面store | 复用设备 | 正常 | 页面直接对已有 device_v2 触发 store/start，预期复用原实体并成功进入 manage | planned`
- `CMP-002 | ZB vs 页面导入 | 网络设备 | 对照 | 同一台网络设备分别从 ZB 和页面导入进入，预期 detect、collect、store decision 和 agent 任务一致 | planned`

### 13.5 总纲与详细用例的关系

分两层维护：

1. 总纲
   - 只放目录和一句话描述
   - 适合持续追加

2. 详细用例
   - 只对进入 `ready/running` 的 case 展开
   - 展开内容包括造数、注错、执行、DB 检查、agent 检查、callback/页面检查、修复记录

未来新增用例时，先加总纲，再逐条展开，不会打散当前体系。

---

## 14. 首批优先级

### 14.1 P0

首批必须优先落地：

- ZB 正常成功场景 2 到 3 条
- 页面正常成功场景 2 到 3 条
- 双入口正常成功对照 2 条
- detect / collect 异常对照 3 条
- agent 任务成功 / 失败各 1 条
- DB 最终态一致性检查全覆盖

### 14.2 P1

强烈建议落地：

- seed 复用冲突
- facts 冲突
- manage partial
- `sync_to_v1` failure
- `monitor_push` failure
- callback 不一致

### 14.3 P2

高价值扩展：

- 多锚点命中
- candidate engine 错误改写
- namespace / relation 边角
- callback 成功但内部 partial
- agent 任务下发成功但内容错误

---

## 15. 执行建议

本设计通过后，下一阶段应做两件事：

1. 先把测试总纲落成正式清单
2. 再挑选 P0 用例，逐条展开为可执行测试计划

展开时每条详细用例必须明确：

- 样本数据
- 注错点
- 执行入口
- 预期阶段
- DB 断言
- agent 断言
- callback / 页面断言
- 恢复方式

---

## 16. 一句话结论

本轮测试不是“补几个接口用例”，而是建立一套围绕 `ZB 外部调用` 和 `页面 device v2 入库` 双入口的、以真实 `detect/collect` 为核心、以 DB/agent/callback/页面一致性为验收标准、可长期扩展的端到端测试体系。
