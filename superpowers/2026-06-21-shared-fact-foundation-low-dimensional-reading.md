# 共享事实底座降维阅读

## 这套东西到底是什么

如果不看大段实现，先把它理解成一句话：

```text
把采集到的网络数据，变成“多个上层应用都能复用的统一事实”
```

它不是一个普通业务模块，更像 OneOps 内部的数据语义底座。

它要解决的问题不是“把数据存下来”，而是：

- 这条数据到底代表什么对象
- 它是不是可信
- 它从哪来
- 多次采集后哪条算最新
- 坏数据怎么留痕
- 上层应用怎么稳定复用

## 为什么读起来会复杂

因为它同时做了三件事：

1. 把采集数据做标准化
2. 把标准化结果治理成 canonical fact
3. 把这些 fact 提供给 IPAM、NetPath、Topology 等模块消费

所以你看到的不是一个单流程模块，而是一条“事实生产线”。

## 5 个核心对象

### 1. `StandardRow`

它表示“已经过基础标准化的一行输入数据”。

代码位置：
[types.go](/home/jacky/project/OneOPS-ALL/OneOps/app/device_collection2/fact/types.go)

它携带的不是业务结论，而是原始上下文：

- `contract_key`
- `dataset_key`
- `vendor`
- `platform`
- `target_id`
- `row_index`
- `fields`
- `observed_at`

可以把它理解为：

```text
采集结果里的一个标准化输入行
```

### 2. `CanonicalFact`

这是共享底座真正想生产出来的东西。

同样在：
[types.go](/home/jacky/project/OneOPS-ALL/OneOps/app/device_collection2/fact/types.go)

关键字段：

- `fact_type`
- `target_id`
- `identity_key`
- `fields`
- `quality`
- `provenance`
- `observed_at`

可以把它理解为：

```text
关于某个对象的一条“统一命名、可复用”的事实
```

例如：

- 某设备的一个接口
- 某接口上的一个 IP
- 某设备上的一条路由
- 某设备发现的一条拓扑邻居关系

### 3. `FactQuality`

它解决“这条事实能不能信”的问题。

字段很少，但很关键：

- `valid`
- `confidence`
- `issues`

也就是说，共享底座不是只给“值”，还给“质量判断”。

### 4. `FactProvenance`

它解决“这条事实从哪来”的问题。

关键字段：

- `contract_key`
- `dataset_key`
- `source_fields`
- `processor_key`
- `processor_version`

这层非常重要，因为上层应用如果要做证据钻取、审计、回放、差异比对，都离不开 provenance。

### 5. `FactIssue`

它表示“这行数据有问题，不能安全变成 fact”。

也就是说，这套底座不是“出错就丢”，而是：

- 好数据进 `CanonicalFact`
- 坏数据进 `FactIssue`

这样上层系统才知道问题出在采集、解析、归一化还是字段缺失。

## 3 张关键表

代码位置：
[fact.go](/home/jacky/project/OneOPS-ALL/OneOps/app/device_collection2/model/fact.go)

### 1. `device_collection2_fact`

这是历史事实表。

作用：

- 保留事实历史
- 允许回看过去某次采集的结果
- 为后续比对和审计提供证据

### 2. `device_collection2_fact_latest`

这是当前最新事实表。

作用：

- 按 `target_id + fact_type + identity_key` 保留最新一条
- 给上层应用快速读取

这是共享底座最重要的“服务层数据”。

### 3. `device_collection2_fact_issue`

这是异常数据表。

作用：

- 保留无法接受为 canonical fact 的输入行
- 记录错误码、错误信息、上下文

## 2 条主流程

### 流程 1：事实生产流程

这是底座最核心的主线。

```text
raw/standardized rows
  -> StandardRow
  -> processor
  -> CanonicalFact / FactIssue
  -> persist history
  -> update latest
```

对应入口：
[device_collection2.go](/home/jacky/project/OneOPS-ALL/OneOps/app/device_collection2/service/impl/device_collection2.go:1415)

也就是 `ProcessFacts(...)`。

它做的事情可以压缩成 4 步：

1. 把输入行装配成 `StandardRow`
2. 按 dataset 选择 processor
3. processor 输出 facts 和 issues
4. 持久化到 history / latest / issue

### 流程 2：事实消费流程

这条流程是给上层应用用的。

```text
latest facts
  -> filter by target / fact type / valid
  -> application projection or snapshot
  -> business module consumption
```

对应接口：
[device_collection2.go](/home/jacky/project/OneOPS-ALL/OneOps/app/device_collection2/service/impl/device_collection2.go:1685)

也就是 `ListLatestFacts(...)`。

这个接口说明了一件事：

```text
共享底座不是只会“写入事实”，也会“以统一方式提供事实”
```

## 3 个消费方向

### 1. IPAM：把 canonical facts 投影成地址事实

代码位置：
[ip_address_fact.go](/home/jacky/project/OneOPS-ALL/OneOps/app/ipam/api/ip_address_fact.go)

`ProjectCanonicalLatest(...)` 会从 DC2 latest 里拉：

- `interface_ip`
- `arp_entry`

然后投影成 IPAM 自己的地址事实。

这说明 IPAM 并不想直接继承底座全部语义，而是：

```text
共享底座提供“基础事实”
IPAM 再生成“IPAM 业务事实”
```

### 2. NetPath：把 canonical facts 装配成分析快照

代码位置：
[facts.go](/home/jacky/project/OneOPS-ALL/OneOps/app/netpath/snapshot/provider/facts.go)

NetPath 需要的 fact family 很多，包括：

- `device_identity`
- `interface`
- `interface_ip`
- `topology_neighbor`
- `route_table`
- `security_zone_binding`
- `acl_rule`
- `firewall_policy`
- `nat_rule`
- `pbr_rule`

它不是直接分析原始采集数据，而是先读取共享底座，再组装成自己的 analysis snapshot。

### 3. Topology：读取 snapshot，而不是直接读任意事实

代码位置：
[snapshot.go](/home/jacky/project/OneOPS-ALL/OneOps/app/topology/service/impl/snapshot.go)

Topology 这条线说明共享底座上面还存在一层：

```text
fact -> snapshot -> topology
```

也就是说，不是所有应用都直接消费 latest facts。
有些应用更适合消费发布后的 snapshot。

## 一张最小脑图

如果你只记一张图，建议记这个：

```text
采集数据
  -> StandardRow
  -> Processor
  -> CanonicalFact / FactIssue
  -> fact(history)
  -> fact_latest(current)
  -> fact_issue(problem rows)

上层消费：
  -> IPAM: projection
  -> NetPath: analysis snapshot
  -> Topology: published snapshot
```

## 它为什么不像一个简单模块

因为它不是“功能代码”，而是“约束代码”。

它要同时约束：

- 命名
- 身份
- 可信度
- 溯源
- 历史与最新态
- 坏数据处理方式
- 上层消费方式

所以你读起来会觉得它像：

- 一部分是数据模型
- 一部分是 ETL
- 一部分是规则引擎
- 一部分是应用中台

这种感觉是正常的。

## 现在最应该怎样理解它

不要把它理解成“一个已经完工的独立平台”，而要理解成：

```text
OneOps 内部正在成形的共享事实层
```

它现在最成熟的部分是：

- fact envelope
- history/latest/issue 三分结构
- 一批 processor
- latest fact 读取接口

它还在继续收敛的部分是：

- canonical fact registry 的冻结
- tenant scope
- snapshot 复用语义
- route / policy fact families
- 多应用真正统一接入

## 一句话结论

如果降到最简单的理解：

```text
共享事实底座 = 把设备采集结果变成“可追溯、可判质、可复用”的统一事实，
再把这些事实稳定供给 IPAM、NetPath、Topology 等上层模块。
```
