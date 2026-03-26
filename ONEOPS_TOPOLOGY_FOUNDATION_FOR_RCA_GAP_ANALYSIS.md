# OneOPS 面向 RCA 的拓扑基座差距分析

本文档只回答一个核心问题：

- 当前 `analysis_l2` 中的 `DevicePorts`、`L2nodeMapServer`、`ArpTableServer`、`PortChannelServer` 等任务，为什么还不足以成为 OneOps 的拓扑能力基座

本文档不做代码重写，不直接替代后续正式设计稿。
本文档的目标是把现状、问题、风险和演进方向先收敛清楚，作为后续拓扑重构和 RCA 接入的基线材料。

---

## 1. 结论先行

当前 `analysis_l2` 已经具备“把部分拓扑相关数据跑通”的能力，但整体上仍然属于：

- 面向任务执行的离线处理逻辑
- 面向单次作业的结果落库逻辑
- 面向局部数据源的关系拼接逻辑

还不属于：

- 面向平台的统一拓扑构建能力
- 面向 RCA 的稳定拓扑快照能力
- 面向异常场景的可观测、可回溯、可降级能力

换句话说，当前代码解决的是“任务能跑”，还没有解决“平台长期可信地维护一份可消费拓扑”。

---

## 2. RCA 对拓扑基座的真实要求

根因定位并不只需要“一张拓扑图”。

根因定位真正需要的是一份满足以下约束的拓扑基座：

- 拓扑实体有稳定身份，而不是依赖临时名称拼接
- 拓扑关系有证据来源，可以解释这条边为什么存在
- 拓扑关系有时间语义，可以知道关系何时观测到、何时失效
- 拓扑关系有质量语义，可以区分可信、可疑、冲突、过期
- 拓扑输出有发布语义，可以保证 RCA 读取的是一份完整快照，而不是构建过程中的半成品
- 拓扑构建对采集失败、网络抖动、脏数据、单批次设备不全等情况具备容错能力

如果没有这些能力，RCA 读到的不是“拓扑基座”，而只是“某些任务在某个时刻写出的一批关系副作用”。

---

## 3. 当前代码在系统中的位置

当前处理入口是：

- `OneOps/app/job/tasks/process_cache/process_analysis.go`
- `OneOps/app/analysis_l2/service/impl/analysis_l2.go`

其中：

1. 作业层通过 `ProcessAnalysisServer.Main()` 调用 `AnalysisProcessCommon()`
2. `AnalysisProcessCommon()` 根据任务名分发到不同 `adapter` 方法
3. 各任务内部直接访问多个服务并写数据库或下游图存储

这意味着当前整体形态是：

- 作业直接调任务
- 任务直接写状态
- 中间没有统一的拓扑领域层
- 平台没有统一的拓扑发布边界

这套模式适合做“批处理任务”，不适合做“拓扑基座”。

---

## 4. 当前任务链路现状

### 4.1 总入口只是任务分发，不是能力编排

`OneOps/app/analysis_l2/service/impl/analysis_l2.go`

当前入口 `AnalysisProcessCommon()` 的特点是：

- 只做 `switch-case` 分发
- 不返回结构化结果
- 不返回 `error`
- 不区分部分成功、降级成功、完全失败
- 不定义统一输入输出契约

这说明 `analysis_l2` 当前是“任务集合入口”，不是“拓扑能力入口”。

### 4.2 作业层拿不到真实失败语义

`OneOps/app/job/tasks/process_cache/process_analysis.go`

`ProcessAnalysisServer.Main()` 中直接调用：

```go
analysisSrv.AnalysisProcessCommon(t.L2Task, t.DeviceList, t.serviceCenterSrv, t.jobSrv.ProxySrv.Q, nil)
return nil
```

这带来的问题是：

- 即使任务内部失败，作业层也可能仍然显示成功
- 作业系统无法知道拓扑是否真的可用
- 后续 RCA 无法基于作业状态判断“是否存在可消费拓扑”

从平台角度看，这会造成“任务成功”和“拓扑可用”之间的语义脱钩。

---

## 5. 关键任务逐项分析

## 5.1 DevicePorts

文件：

- `OneOps/app/analysis_l2/service/adapter/device_ports.go`

当前职责包括：

- 同步设备接口
- 同步本地 MAC
- 同步接口与 IP 关系

这部分已经开始接近“资产侧拓扑底座”的能力，但当前实现仍存在几个关键问题。

### 5.1.1 以“本次采集结果”为准直接删旧接口

`saveSnmpIfIndexAndMac()` 中会拿数据库旧接口集合和本次采集结果做差异，并删除未在本次结果中出现的接口。

这在以下场景中风险很高：

- 采集不完整
- 某次 SNMP 超时
- 某些板卡或逻辑口暂时未返回
- 某个字段解析失败

在这些情况下，系统会把“暂时缺失的数据”当成“真实删除的数据”。

对于拓扑基座，这是非常危险的。

更合理的语义应该是：

- 先标记为 `stale` 或 `missing_in_this_snapshot`
- 只有连续多次确认消失后再进入删除流程

### 5.1.2 使用 fake MAC 填补空值

当前逻辑在 MAC 为空时会写入：

```go
0xfake+<deviceCode>+<portName>
```

这对任务跑通有帮助，但对拓扑基座有副作用：

- fake MAC 不是设备真实身份
- 它会进入后续关系链路
- 可能被误当成真实观察结果参与关联

对于 RCA 来说，伪造身份只能作为临时占位，不应与真实观测同层使用。

更合理的方式是：

- 明确标记为 `synthetic_identity`
- 不让其参与跨设备、跨租户、跨批次的真实关联

### 5.1.3 对租户和本地 MAC 存在高风险假设

当前代码直接使用：

- `deviceCodeTenantMap[device.DeviceCode()][0]`
- `deviceInterfaceResp.LocalMacs[0]`

这说明系统隐含假设：

- 每台设备一定能映射到租户
- 每个接口一定存在本地 MAC
- 第一个元素总是正确元素

一旦这些前提不成立，就会导致：

- 越界风险
- 错误租户归属
- 错误的 IP-MAC-Interface 绑定

拓扑基座不应建立在“列表第一个元素就是对的”这种假设上。

### 5.1.4 缺少快照和版本语义

`DevicePorts` 直接更新当前数据库状态，没有：

- snapshot id
- generation
- observed_at
- quality state

这意味着后续 RCA 无法回答：

- 当前接口状态来自哪次采集
- 这批端口数据是否完整
- 此时读到的数据是不是混合了多轮采集

---

## 5.2 L2nodeMapServer

文件：

- `OneOps/app/analysis_l2/service/adapter/newL2NodeMapServe.go`

当前职责包括：

- 从 `IfTable` 建端口节点
- 从 CDP / LLDP 构建邻居边
- 读取已有线缆关系
- 清空旧线缆并重建
- 同步到 Neo4j

这是当前离“拓扑图”最近的一段代码，但问题也最集中。

### 5.2.1 当前构图身份不稳定

当前很多节点 ID 来自：

- `neighborNameStandard(device.Hostname)`
- `standardDeviceName + "_" + interfaceName`

也就是：

- 设备名经过域名裁剪
- 再和接口名拼成节点 ID

这带来的问题包括：

- hostname 变更会导致身份漂移
- 域名裁剪可能让不同设备变成同名
- 设备别名和真实标识混用
- 接口名标准化不一致会导致断边或误连边

对于拓扑基座，更稳妥的方式是：

- 设备以稳定主键建模，例如 `device.id` 或 `device.code`
- 接口以稳定主键建模，例如 `interface.id` 或 `interface.code`
- hostname、management ip、alias 只作为属性，不作为核心身份

### 5.2.2 当前邻接构建偏向“连边成功”，缺少证据融合

CDP 和 LLDP 记录被标准化后直接建边。

但当前没有统一表达：

- 这条边来自 CDP 还是 LLDP
- 单边观测还是双边观测
- 是否和线缆数据一致
- 是否和 PortChannel 成员关系一致
- 是否与历史快照一致

这使得当前系统只能得到“有一条边”，却不能回答：

- 这条边有多可信
- 这条边为什么可信
- 这条边是否与其他证据冲突

RCA 对这类解释能力的依赖很高。

### 5.2.3 破坏式重建线缆关系

`processCableAndNeighbor()` 中先执行：

1. `clearCables()`
2. `addCableRelations()`
3. `syncToNeo4j()`

其中 `clearCables()` 会：

- 删除给定设备集合相关的所有线缆
- 清空接口上的 cable reference

这是当前最不适合成为平台基座的一点。

因为一旦出现以下情况：

- 本次设备列表不完整
- 部分设备采集失败
- 邻居数据缺失
- 中途事务失败
- 图同步失败

系统就会先把旧的正确关系删掉，再尝试重建新的关系。

对于任务来说，这也许能接受。
对于拓扑基座，这种发布模式风险过高。

更合理的方式是：

- 在新快照中构建候选关系
- 通过校验后再进行原子发布
- 发布失败时保留旧快照

### 5.2.4 多条连接场景被直接跳过

`addCableRelations()` 中统计了节点唯一度，若端口涉及多条边则直接：

- `Skipping port with multiple lines`

这说明当前系统无法正确处理：

- PortChannel
- 堆叠交换机
- 多邻居
- 旁路设备
- 中间透明设备

而真实网络中，多条连接是常态，不是异常。

如果这类关系被简单跳过，RCA 看到的图将是“过度简化图”，不是“真实生产图”。

### 5.2.5 PortChannel 仍未真正纳入主流程

虽然文件中存在 `portChannelToTree()`，但主流程里是注释状态。

另外：

- `PortChannelServer` 任务本身几乎未完成
- 当前拓扑主链没有把聚合链路作为一等实体

这意味着当前图模型缺少：

- `PortChannel`
- `member interface`
- `logical link` 和 `physical member link` 的分层

对于根因定位，这会导致：

- bundle 链路异常无法正确定位
- 成员口抖动与逻辑聚合口故障无法区分
- 单成员退化与整条逻辑链路中断混淆

### 5.2.6 图数据库同步仍是全量清空式

`syncToNeo4j()` 中先执行 `ClearNetworkTopologyData()`，再执行 `CreateNetworkTopology()`。

这进一步说明当前系统缺少：

- 图快照版本
- 灰度发布
- rollback
- 部分失败隔离

当 Neo4j 构建失败时，系统面临的是：

- 老数据已清空
- 新数据未完成
- 平台处于不可消费状态

这不符合 RCA 对拓扑稳定性的要求。

---

## 5.3 ArpTableServerV2

文件：

- `OneOps/app/analysis_l2/service/adapter/newArpTableServerV2.go`

这是当前几项任务里工程化程度最高的一段，实现了：

- 统计信息收集
- 设备级错误记录
- 部分数据质量检查
- 树结构中的接口-MAC 关系构建

这是一条好的方向，但它仍然属于“任务优化”，而不是“拓扑基座完成态”。

### 5.3.1 已有进步

这部分已经做对了几件事情：

- 开始显式记录数据质量统计
- 区分设备级状态
- 开始做字段标准化
- 开始将接口与 MAC 关系组织成结构化图

这些都说明代码已经在往“可治理”方向演进。

### 5.3.2 仍然缺少统一发布边界

即使统计信息已经比较丰富，当前结果仍然是：

- 在任务内直接处理
- 在任务内直接落关系
- 在任务内按租户写最终结果

中间依然缺少统一的：

- normalize
- reconcile
- validate
- publish

四段式拓扑发布流程。

### 5.3.3 租户保存逻辑存在污染风险

`processTenantData()` 中按租户循环后调用 `saveIpMacInterfaceV2()`，但传入的是全局 `arpTotalMap`。

这意味着当前存在明显风险：

- 每个租户可能都拿到了全量 ARP 观测数据
- 租户边界并未在保存前充分过滤

对于 RCA，这类租户污染会直接损伤证据可信度。

### 5.3.4 统计信息仍然不是平台状态

当前统计信息主要通过日志输出。

但平台真正需要的是：

- 可查询的构建状态
- 可持久化的质量报告
- 可关联到某次快照的质量分数
- 可作为 RCA 前置判断的 readiness 状态

否则统计日志看起来很丰富，但平台和上层模块仍然无法消费。

---

## 5.4 PortChannelServer

文件：

- `OneOps/app/analysis_l2/service/adapter/PortChannel.go`

当前基本现状是：

- 任务入口存在
- 能查询 `PortChannel` 原始表
- 但没有完成领域建模和持久化闭环

大量真实逻辑仍停留在注释代码中。

这说明当前系统对聚合链路的支持仍处于“设计意图存在、平台能力未落地”的状态。

如果不先补齐这一层，拓扑图在生产网络中的代表性会明显不足。

---

## 6. 当前问题的本质分类

把这些问题抽象后，当前差距主要落在五类。

### 6.1 领域边界问题

当前没有一个统一的拓扑领域层来承接：

- 实体定义
- 边定义
- 证据定义
- 快照定义
- 发布定义

所以各任务都在“边处理数据边写最终状态”。

### 6.2 发布模型问题

当前大多是：

- 直接删旧数据
- 直接写新数据
- 中间没有 staging snapshot

这使得拓扑更新过程不具备原子性和可回滚性。

### 6.3 质量治理问题

当前虽然部分任务有日志和统计，但系统仍缺少统一的数据质量模型，例如：

- `healthy`
- `partial`
- `suspect`
- `conflict`
- `stale`
- `unverified`

没有这些状态，RCA 很难区分“可信拓扑”和“当前仅供参考的拓扑”。

### 6.4 容错与抗干扰问题

当前代码对以下场景普遍防护不足：

- 采集超时
- 数据字段缺失
- 返回表为空
- 设备不在本次批次中
- 邻居单边可见
- 多设备同名
- 历史正确关系与当前错误观测冲突

一旦这些情况发生，当前逻辑更像“继续写”或“直接删”，缺少中间态。

### 6.5 可消费性问题

RCA 并不想直接消费多个任务各自的中间结果。

RCA 更需要的是统一输出：

- 拓扑快照
- 拓扑边界
- 节点和边的质量
- 关系证据
- 可解释性字段

当前系统尚未形成这类统一消费出口。

---

## 7. 面向 RCA 的目标形态

拓扑基座建议收敛为四层。

### 7.1 Observation 层

负责保存原始观测，不直接发布为最终拓扑。

例如：

- `snmp_ifentry_observation`
- `lldp_observation`
- `cdp_observation`
- `mac_table_observation`
- `arp_table_observation`
- `dcim_cable_observation`

这一层只回答：

- 看到了什么
- 从哪里看到
- 什么时候看到

### 7.2 Normalize 层

负责标准化和身份归一化，例如：

- 设备身份归一
- 接口身份归一
- hostname / alias / domain stripping 统一映射
- MAC / interface name / ifindex 格式统一

这一层不做最终业务判定，只做“可比对”。

### 7.3 Reconcile 层

负责把多源观测融合成候选拓扑关系，例如：

- CDP + LLDP 双向匹配
- 邻居关系与 DCIM 线缆关系比对
- PortChannel 与成员口映射
- MAC 挂载点和接口关系融合
- IP-MAC-Interface 的归属融合

这一层要显式产出：

- 候选边
- 证据来源
- 置信度
- 冲突状态

### 7.4 Publish 层

负责生成可消费拓扑快照并原子切换。

发布结果至少包含：

- `snapshot_id`
- `tenant_scope`
- `generated_at`
- `topology_quality_score`
- `readiness`
- `nodes`
- `edges`
- `edge_evidences`

RCA 应只读取 Publish 层的结果，不直接读取任务中间态。

---

## 8. 建议的最小领域模型

建议至少明确以下实体：

- `TopologySnapshot`
- `TopologyNode`
- `TopologyEdge`
- `TopologyEdgeEvidence`
- `Device`
- `DeviceInterface`
- `PortChannel`
- `MacAttachment`
- `IpOwnership`
- `TenantScope`

其中 `TopologyEdge` 应至少支持以下关系类型：

- `physical_cable`
- `l2_adjacency`
- `logical_bundle_member`
- `interface_hosts_mac`
- `mac_owns_ip`
- `server_attached_to_switch_port`

每条边建议带上：

- `edge_type`
- `source_kind`
- `source_record_id`
- `observed_at`
- `last_seen_at`
- `confidence`
- `state`

其中 `state` 至少建议支持：

- `active`
- `stale`
- `suspect`
- `conflict`
- `suppressed`

---

## 9. 建议的演进路线

## 9.1 第一阶段：先把任务语义变对

优先做：

1. `AnalysisProcessCommon()` 返回结构化结果和 `error`
2. `ProcessAnalysisServer.Main()` 根据任务结果更新真实状态
3. 所有任务统一输出：
   - 总设备数
   - 成功数
   - 失败数
   - 部分成功数
   - 数据质量摘要
4. 停止使用 `fmt.Println` 和临时 `Pretty()` 作为主要诊断手段

这一阶段的目标不是重构拓扑，而是先让平台知道“这次任务到底有没有产出可用结果”。

## 9.2 第二阶段：引入拓扑快照中间层

优先做：

1. 让 `DevicePorts`、`L2nodeMapServer`、`ArpTableServerV2` 不再直接发布最终拓扑
2. 让它们只写 observation 或 candidate relation
3. 增加 `topology_snapshot` 和 `topology_candidate_edge` 一类中间模型
4. 发布动作改成独立流程

这一阶段是从“任务集合”走向“拓扑流水线”的关键拐点。

## 9.3 第三阶段：补齐 PortChannel 和多链路能力

优先做：

1. 把 `PortChannel` 变成正式实体
2. 区分逻辑聚合口和成员口
3. 允许同一设备对之间存在多条边
4. 引入冲突消解和证据优先级

否则生产网络中的大量关键链路仍然无法被正确表达。

## 9.4 第四阶段：发布面向 RCA 的统一拓扑出口

建议由一个统一模块提供：

- 当前激活快照
- 指定时间点快照
- 拓扑质量状态
- 节点和边证据
- RCA 所需最小映射视图

这样 RCA 可以稳定依赖一处，而不是依赖多处任务落库结果。

---

## 10. 对当前 RCA 建设的直接建议

在拓扑基座未完全重构前，RCA 接入当前拓扑时应增加保护条件。

建议至少做到：

1. 读取拓扑时附带一份 `readiness` 信息
2. 当拓扑质量不足时，RCA 输出应允许进入：
   - `unable_to_conclude_yet`
   - `insufficient_topology_confidence`
3. 不把当前单次任务生成的邻接边直接视为绝对事实
4. 在多路径和聚合链路场景下，不强行输出唯一桥接根因
5. 对来自 fake MAC、单边 LLDP/CDP、脏接口名匹配的关系，降低证据权重

RCA 的准确性高度依赖拓扑可信度，因此在拓扑基座未稳定之前，必须允许“谨慎不给答案”。

---

## 11. 当前最关键的判断

当前 `analysis_l2` 的主要问题不是“代码写得不够优雅”，而是：

- 它的任务边界决定了它更像批处理脚本
- 它的发布方式决定了它不够稳定
- 它的数据模型决定了它还不是统一拓扑语言

因此，后续工作不应只停留在：

- 补几个异常处理
- 多打一些日志
- 再加几个 if-else

而应明确转向：

- 建立统一拓扑领域模型
- 建立 observation -> reconcile -> publish 流水线
- 建立快照、质量、证据和可回滚机制

只有这样，拓扑才能真正从“任务结果”升级为“平台基座”。

---

## 12. 后续文档建议

基于本文档，建议继续补三份文档：

1. `OneOPS 拓扑基座目标领域模型设计`
2. `OneOPS 拓扑快照与发布机制设计`
3. `OneOPS RCA 对拓扑消费契约`

本文档只完成了第一步：把“为什么当前还不是基座”这件事讲清楚。
