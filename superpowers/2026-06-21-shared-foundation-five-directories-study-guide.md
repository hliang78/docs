# 共享底座五目录学习稿

## 一句话先说结论

这套“共享事实底座”本质上不是一个独立产品，而是一条跨模块复用的数据主线：

1. `device_collection2` 负责把设备原始采集结果变成稳定的 `CanonicalFact`
2. `obsflow` 负责把这些事实重新组织成面向处理任务的 bundle
3. `netpath`、`ipam`、`topology` 负责按各自场景消费这些事实

所以它更像一个“共享事实平台内核”，而不是一个已经完全独立部署的平台。

---

## 五个关键目录分别做什么

### 1. `app/device_collection2/`

这是共享底座的生产端。

它做四件核心事：

1. 定义事实契约
2. 执行采集与标准化
3. 生成 canonical facts
4. 把事实落库并维护 latest fact

关键文件：

- [types.go](/home/jacky/project/OneOPS-ALL/OneOps/app/device_collection2/fact/types.go)
- [fact.go](/home/jacky/project/OneOPS-ALL/OneOps/app/device_collection2/model/fact.go)
- [device_collection2.go](/home/jacky/project/OneOPS-ALL/OneOps/app/device_collection2/service/impl/device_collection2.go)

你可以把这里理解成：

`原始命令 / SNMP / 控制器返回` -> `标准行` -> `CanonicalFact` -> `FactLatestRecord`

这就是底座真正成立的地方。

### 2. `app/obsflow/`

这是共享底座的第一层消费与编排层。

它不重新定义事实，而是把 DC2 的事实整理成 obsflow 任务能直接消费的输入包，再驱动处理任务、快照和 workflow。

关键文件：

- [dc2_fact_bundle_store.go](/home/jacky/project/OneOPS-ALL/OneOps/app/obsflow/adapters/dc2_fact_bundle_store.go)
- [runtime_ports.go](/home/jacky/project/OneOPS-ALL/OneOps/app/obsflow/bridge/runtime_ports.go)
- [trigger_api.go](/home/jacky/project/OneOPS-ALL/OneOps/app/obsflow/bridge/trigger_api.go)

这里最重要的意义是：

它证明了“事实底座”不是只给 DC2 自己看的，而是已经被拿来驱动另一条业务主线。

### 3. `app/netpath/`

这是共享底座的分析型消费者。

它不是重新采集网络，而是从事实中拼出分析快照，再进行路径推演。

关键文件：

- [facts.go](/home/jacky/project/OneOPS-ALL/OneOps/app/netpath/snapshot/provider/facts.go)

一句话理解：

`netpath` 消费的不是设备命令，而是“已经标准化、可组合的事实”。

### 4. `app/ipam/`

这是共享底座的查询型消费者。

它把事实底座中的 IP / 接口 / 设备关系暴露成 IPAM 视角下的接口能力。

关键文件：

- [ip_address_fact.go](/home/jacky/project/OneOPS-ALL/OneOps/app/ipam/api/ip_address_fact.go)

所以 IPAM 这里不是自己维护一套独立采集结果，而是在复用底座的事实表达。

### 5. `app/topology/`

这是共享底座的快照型消费者。

它一边兼容旧快照体系，一边开始接入基于 obsflow / DC2 事实的新快照来源。

关键文件：

- [snapshot.go](/home/jacky/project/OneOPS-ALL/OneOps/app/topology/service/impl/snapshot.go)

它的角色很关键，因为它说明底座正在替换“旧快照输入”，但还没有完全替换完。

---

## 底座到底“共享”了什么

不是共享一个服务名，而是共享下面这几类东西：

1. 共享事实类型
2. 共享事实身份键
3. 共享质量与问题表达
4. 共享 latest fact 存储
5. 共享消费者读取方式

从代码上看，最核心的共享契约是：

- `StandardRow`
- `CanonicalFact`
- `FactQuality`
- `FactProvenance`
- `FactIssue`
- `Processor`

它们都在 [types.go](/home/jacky/project/OneOPS-ALL/OneOps/app/device_collection2/fact/types.go)。

这就是“事实底座”的真正边界。

---

## 为什么你会感觉它很复杂

因为它现在还处在“平台化过渡态”，不是纯净的独立架构。

复杂度主要来自三层叠加：

1. 生产层还带着 DC2 自己的采集执行、契约管理和控制器适配
2. 消费层要同时兼容 obsflow / topology 的旧路径
3. 触发层还存在 bridge 和 compat 入口，没有完全统一

所以你看到的不是一个干净的“事实中心”，而是：

`旧系统兼容 + 新底座沉淀 + 新消费者接入`

同时存在。

---

## 如果把它抽成一个独立平台，边界应该怎么画

最自然的抽法不是先拆 UI，也不是先拆任务编排，而是先把“事实能力”抽成独立边界：

1. 事实写入接口
2. 事实查询接口
3. latest fact 投影视图
4. 事实 schema / identity contract
5. 事实质量与溯源协议

然后让：

- DC2 只负责“生产事实”
- obsflow / netpath / ipam / topology 只负责“消费事实”

如果这一步完成，共享底座才真正具备独立平台形态。

---

## 最后的判断

从这五个目录看，共享底座已经真实存在，但仍然是“嵌在 OneOps 里的平台内核”，还不是彻底独立的平台。

它已经具备了三个平台特征：

1. 有统一事实契约
2. 有跨模块复用
3. 有多消费者接入

它还缺两个平台特征：

1. 统一触发入口
2. 明确的独立读写边界

所以更准确的说法是：

**现在它是一个正在形成中的共享事实平台底座。**
