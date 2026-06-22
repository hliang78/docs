# 共享底座从触发到消费的完整链路

## 先说总图

你现在关心的“共享底座”主线，其实可以压成下面这一条：

1. 入口触发采集
2. DC2 执行采集和标准化
3. DC2 产出并持久化 `CanonicalFact`
4. obsflow 把 fact 重组为 bundle / snapshot
5. netpath / ipam / topology 按各自方式消费

如果只记一句话，就是：

**触发在 bridge / API，事实生产在 DC2，事实再利用在 obsflow、netpath、ipam、topology。**

---

## 一、触发从哪里进来

### 路径 A：直接走 DC2 API

这是最“原生”的路径。

入口在：

- [device_collection2.go](/home/jacky/project/OneOPS-ALL/OneOps/app/device_collection2/api/device_collection2.go)
- [device_collection2.go](/home/jacky/project/OneOPS-ALL/OneOps/app/device_collection2/router/device_collection2.go)

关键入口有：

1. `POST /device-collection2/process-facts`
2. `POST /device-collection2/collect-standardize-process`
3. `POST /device-collection2/runs/manual`
4. `POST /device-collection2/policies/:policy_id/run`

其中最关键的是：

- `CollectStandardizeProcess`
- `RunManual`
- `RunPolicy`

它们分别对应：

1. 单个 target / dataset 的同步流水线
2. 面向一组 target 的手动运行
3. 面向 policy scope 的批量运行

### 路径 B：走 obsflow 兼容桥

入口在：

- [trigger_api.go](/home/jacky/project/OneOPS-ALL/OneOps/app/obsflow/bridge/trigger_api.go)
- [runtime_ports.go](/home/jacky/project/OneOPS-ALL/OneOps/app/obsflow/bridge/runtime_ports.go)

关键入口有：

1. `TriggerCollectionRun`
2. `TriggerProcessingRun`
3. `Collect`
4. `Process`

这里的本质不是自己做采集，而是：

**把旧兼容入口翻译成 obsflow / DC2 新主线能理解的请求。**

特别是 `dc2_only` 模式下，`triggerDC2CollectionLaunch()` 会直接生成一个 `runID`，然后异步调用 DC2 的 `RunManual()`。

也就是说：

`obsflow bridge` -> `DC2 RunManual`

这条链是现实存在的。

---

## 二、DC2 是怎么把原始采集变成 fact 的

### 第 1 步：采集原始数据

核心在 [device_collection2.go](/home/jacky/project/OneOPS-ALL/OneOps/app/device_collection2/service/impl/device_collection2.go) 的：

- `Collect()`
- `collectRaw()`
- `postController()`

这里的逻辑是：

1. 先根据 contract 选中 dataset
2. 再根据 dataset 的 `protocol` 决定是 `cli` / `snmp` / `winrm`
3. 最后调用 controller 接口拿原始结果

所以真正的外部执行点不是底座自己 ssh/snmp，而是：

**DC2 通过 controller 执行原始采集。**

### 第 2 步：标准化

还是在同一个文件里：

- `Standardize()`
- `CollectStandardize()`

它把 controller 返回的 raw payload 转成统一的标准行。

这一步的产物还不是 fact，而是 `StandardRow` 的前置形态。

### 第 3 步：生成 canonical facts

关键函数：

- `ProcessFacts()`

它会把请求里的 rows 包装成 `fact.StandardRow`，然后调用：

- `s.FactProcessors.Process(ctx, dataset.Key, rows)`

也就是说：

1. `datasetKey` 决定选哪个 processor
2. processor 决定产出什么 `FactType`
3. 最后生成 `CanonicalFact` 和 `FactIssue`

这一步就是共享底座真正成立的地方。

### 第 4 步：持久化 facts 和 latest facts

关键函数：

- `persistFacts()`
- `replaceLatestFactsForDataset()`
- `upsertLatestFacts()`

对应模型在：

- [fact.go](/home/jacky/project/OneOPS-ALL/OneOps/app/device_collection2/model/fact.go)

持久化时会写三类数据：

1. `FactRecord`
2. `FactIssueRecord`
3. `FactLatestRecord`

其中最重要的是 `FactLatestRecord`。

因为之后的消费者，大多不是读“某次历史运行的全部 fact”，而是读：

**某个 target 当前最新、有效的事实视图。**

---

## 三、批量运行时这条流水线怎么被串起来

入口在：

- [device_collection2_run.go](/home/jacky/project/OneOPS-ALL/OneOps/app/device_collection2/service/impl/device_collection2_run.go)

关键函数：

- `RunManual()`
- `RunPolicy()`
- `RunDuePolicies()`

它们的作用不是发明新的 fact 逻辑，而是把前面的单步流水线批量化、调度化：

1. 解析 target 集合
2. 决定要跑哪些 dataset
3. 为每个 target 执行 collect -> standardize -> process -> persist
4. 记录 `RunRecord` / `RunDeviceRecord`

所以 `RunManual` / `RunPolicy` 本质上是：

**共享底座的批处理编排层。**

---

## 四、obsflow 怎么消费共享底座

### 1. 先把 DC2 结果包装成 batch

关键文件：

- [dc2_fact_bundle_store.go](/home/jacky/project/OneOPS-ALL/OneOps/app/obsflow/adapters/dc2_fact_bundle_store.go)

关键函数：

- `LoadBatches()`
- `GetBatches()`
- `observationsForRef()`

它做的事情非常关键：

1. 先解析形如 `dc2:<runID>:<collectionName>` 的 batch code
2. 再从 DC2 的 `FactRecord` / `RunRecord` / `RunDeviceRecord` 里取数
3. 然后把 fact 映射成 obsflow 能吃的 `Observation`

也就是说：

**obsflow 并不直接理解 CanonicalFact，而是把 CanonicalFact 再翻译成自己的 observation bundle。**

### 2. 再进入 obsflow kernel

关键文件：

- [process_launch_service.go](/home/jacky/project/OneOPS-ALL/OneOps/app/obsflow/app/process_launch_service.go)
- [kernel_service.go](/home/jacky/project/OneOPS-ALL/OneOps/app/obsflow/app/kernel_service.go)

关键流程：

1. `ProcessLaunchService.Trigger()` 先校验 batch 是否 ready
2. 然后解析 tenant、查重、加锁
3. 再调用 `KernelService.Process()`

`KernelService.Process()` 会做：

1. 从 bundle store 重建 observations
2. 根据 task name 取任务实现
3. 执行 task
4. 生成 snapshot
5. 持久化 processing_run 和 snapshot

所以 obsflow 这一层不是生产 fact，而是：

**把共享底座提供的事实重新组织成“处理任务输入”和“任务产物 snapshot”。**

---

## 五、netpath / ipam / topology 分别怎么消费

### 1. netpath：按 factType 直接读 latest facts

关键文件：

- [sdk_enabled.go](/home/jacky/project/OneOPS-ALL/OneOps/app/netpath/runtime/sdk_enabled.go)
- [facts.go](/home/jacky/project/OneOPS-ALL/OneOps/app/netpath/snapshot/provider/facts.go)

关键动作：

`readFactSet()` 会针对多个 `factType` 逐个调用：

- `ListLatestFacts()`
- `ListLatestFactsByField()`

然后拼成 `FactSet`，再交给 assembler / validator。

所以 netpath 是最“平台化”的消费者：

**它直接面向 latest facts 读，不依赖旧采集表。**

### 2. ipam：把 latest facts 投影成 IPAM 事实表

关键文件：

- [ip_address_fact.go](/home/jacky/project/OneOPS-ALL/OneOps/app/ipam/api/ip_address_fact.go)
- [ip_address_fact.go](/home/jacky/project/OneOPS-ALL/OneOps/app/ipam/service/impl/ip_address_fact.go)

关键动作：

`ProjectCanonicalLatest()` 会：

1. 先调用 DC2 的 `ListLatestFacts()`
2. 取 `interface_ip` / `arp_entry` 之类事实
3. 再用 `ProjectDC2FactRecords()` 投影成 IPAM 自己的 `IPAddressFact`

所以 IPAM 不是直接“在线查询 facts 后就返回”，而是：

**把共享事实再投影成 IPAM 自己的业务表。**

### 3. topology：优先读取 obsflow snapshot，旧 Nacos 为兜底

关键文件：

- [snapshot.go](/home/jacky/project/OneOPS-ALL/OneOps/app/topology/service/impl/snapshot.go)

关键动作：

`GetSnapshot()` / `ResolveSnapshot()` 会优先走：

- `getSnapshotFromL2TopologySnapshot()`

也就是从：

- `SnapshotLookup.GetLatestReadyByTenantAndTask(..., "L2nodeMapServer")`

读取 obsflow 产出的 snapshot。

只有读不到时，才回退到旧的 Nacos snapshot。

这说明 topology 当前处在：

**新 snapshot 主线优先，旧 snapshot 主线兜底。**

---

## 六、把整条链路压成一张时序图

### 场景 1：直接跑 DC2

`API/Policy` -> `RunManual/RunPolicy` -> `Collect` -> `postController` -> `Standardize` -> `ProcessFacts` -> `persistFacts` -> `FactLatestRecord`

### 场景 2：从 obsflow 兼容入口触发采集

`TriggerCollectionRun` -> `triggerDC2CollectionLaunch` -> `DC2 RunManual` -> `FactLatestRecord` -> `DC2FactBundleStore`

### 场景 3：从 obsflow 触发处理

`TriggerProcessingRun` -> `ProcessLaunchService.Trigger` -> `LoadBatches/GetBatches` -> `KernelService.Process` -> `Snapshot`

### 场景 4：分析 / 查询 / 拓扑消费

1. `netpath`：读 `ListLatestFacts` -> `FactSet` -> `AnalysisSnapshot`
2. `ipam`：读 `ListLatestFacts` -> `ProjectDC2FactRecords` -> `IPAddressFact`
3. `topology`：读 `SnapshotLookup` -> `L2 snapshot`

---

## 七、真正的“平台边界”在哪里

如果从这条时序看，共享底座真正的边界不是 obsflow，也不是 topology，而是这三层：

1. `CanonicalFact` 契约
2. `FactLatestRecord` 最新事实视图
3. `ListLatestFacts` / `ListLatestFactsByField` 这类统一读取接口

因为：

- 生产端可以变
- 触发方式可以变
- 消费者也可以继续增加

但只要这三层稳定，共享底座就成立。

---

## 八、最重要的判断

现在这套代码已经说明一件事：

**OneOps 里真正正在平台化的，不是“采集任务中心”，而是“共享事实底座”。**

采集触发仍然比较杂：

- 有 DC2 原生入口
- 有 obsflow bridge 入口
- 有 compat / once / launch 多条路径

但 facts 的生产和消费，已经开始收敛到一套共享语义上了。

这也是你为什么会感觉“代码很复杂，但方向又很清楚”。
