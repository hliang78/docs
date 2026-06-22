# NetPath / IPAM 闭环剩余项对照表

Date: 2026-06-22

## 目的

这份短文档只回答一个问题：

```text
NetPath 和 IPAM 距离“闭环”各还差多远？
```

这里的“闭环”不按单个接口或单个页面判断，而按“用户能否从入口一路走到结果，并让系统对后续动作负责”来判断。

## 当前总体判断

一句话结论：

- `IPAM` 更接近“可上线闭环”。
- `NetPath` 更接近“可演示闭环”，但离真正生产闭环还远于 IPAM。

粗粒度判断：

| 方向 | 当前阶段 | 粗略完成度 |
| --- | --- | --- |
| `IPAM` | 上线前硬化阶段 | `70%-80%`（生产闭环视角） |
| `NetPath` | 产品化闭环阶段 | `50%-60%`（生产闭环视角） |

如果只看“可演示”：

| 方向 | 可演示闭环完成度 |
| --- | --- |
| `IPAM` | `80%-90%` |
| `NetPath` | `70%-80%` |

## 闭环定义

### NetPath 的闭环

NetPath 的最小闭环不是“engine 出结果”，而是：

```text
snapshot
  -> analyze
  -> result
  -> evidence
  -> probe/ticket downstream action
  -> action feedback / review outcome
```

只有当分析结果能被查看、被追溯、被消费，并且后续动作能回写状态，NetPath 才算真正闭环。

### IPAM 的闭环

IPAM 的最小闭环不是“能建地址池”，而是：

```text
planning / prefix / pool
  -> allocation
  -> release / reclaim
  -> observed facts projection
  -> audit finding
  -> resolve / relaunch acceptance
```

只有当资源、分配、回收、事实、稽核几段都可操作、可验证、可验收，IPAM 才算真正闭环。

## NetPath：还差什么

### 已经比较接近闭合的部分

- durable snapshot persistence 已有
- snapshot-first analyze 主链已落地
- workflow handoff 已有
- ticket draft 已有
- monitor-probe draft 已有
- baseline compare context 已经开始向下游 consumer 传播

这意味着 NetPath 已经不是“能不能跑”的问题，而是“后续链路什么时候真正接住”的问题。

### 还没闭合的重点

#### 1. policy minimal closure

当前最大的功能缺口仍然是策略面闭环不足。

至少还要补齐：

- ACL / firewall policy 最小判断链
- 对未覆盖策略家族保持 fail-closed 或 review-required
- 不让上层误把“路径可达”理解成“策略允许”

#### 2. result / evidence 闭环

现在更像后端链路先行，前端结果闭环还不够完整。

还需要把这些串成一个可演示入口：

- snapshot 列表
- snapshot 详情
- analysis result 页面
- evidence drill-down

没有这层，NetPath 很难形成稳定的产品入口。

#### 3. probe / ticket 真闭环

目前：

- `workflow-handoff` 更像 orchestration seam
- `ticket-draft` 更像下游说明书
- `monitor-probe-draft` 更像下游映射草案

真正还差的是：

- 是否真正执行
- 执行到哪一层
- 执行成功/失败
- 结果如何回写到 NetPath run / snapshot / review 状态

这一步没补上之前，它仍然更像“分析 + handoff”，还不是“分析闭环”。

#### 4. rollout / observability / guardrail

这部分不影响演示，但影响生产落地：

- rollout 顺序
- 运行期观测
- fail-closed guardrail
- 质量门禁与灰度策略

### NetPath 判断

如果目标是下一阶段收敛，我会把 NetPath 剩余项压成两波：

#### 波次 1：可演示闭环

- `policy minimal closure`
- `result / evidence 闭环`

#### 波次 2：可生产闭环

- `probe / ticket execution feedback`
- `rollout / observability / guardrail`

## IPAM：还差什么

### 已经比较接近闭合的部分

从已有文档和 checkpoint 看，IPAM 已经基本具备：

- resource closure
- allocation closure
- reclaim closure
- audit closure
- canonical fact projection entry
- frontend smoke / backend smoke 基线

它的问题不是主链不存在，而是生产硬化还没完全收口。

### 还没闭合的重点

#### 1. projection -> fact -> finding 最终稳定化

IPAM 和 shared facts 真正接起来的关键不是页面，而是：

```text
interface_ip / arp / mac
  -> ipam_address_fact
  -> audit finding
```

这条链已经开头了，但还需要更稳定的契约边界、事实质量和投影行为。

#### 2. allocation / reclaim / audit 最终 smoke

现在有相当多 smoke 和 checkpoint，但上线前还需要把这些再稳定一遍：

- 分配成功
- 释放成功
- 回收成功
- finding 生成成功
- finding resolve 成功

重点不只是“跑过”，而是“可重复、可追踪、可作为验收证据”。

#### 3. production launch gate

IPAM 真正还差的是发布门禁而不是大功能：

- mutation smoke 稳定性
- 浏览器 smoke 稳定性
- 页面错误反馈完整性
- 数据刷新与结果可见性
- 发布前 evidence 收口

### IPAM 判断

IPAM 更像只差一个波次：

#### 波次 1：上线前硬化

- projection / finding 稳定化
- allocation / reclaim / audit 最终 smoke
- launch gate / evidence 收口

## 对照结论

把两者放在一起看：

| 项目 | 更接近什么 | 还缺的核心 |
| --- | --- | --- |
| `NetPath` | 可演示闭环 | policy、result/evidence、execution feedback |
| `IPAM` | 可上线闭环 | projection/finding 稳定化、最终 smoke、launch gate |

所以：

- `IPAM` 更适合作为第一个“上线闭环样板”
- `NetPath` 更适合作为第一个“分析闭环样板”

## 推荐推进顺序

如果只按闭环收益排序，我建议：

1. 先把 `IPAM` 收成第一个“可上线闭环样板”
2. 再把 `NetPath` 收成第一个“可演示分析闭环样板”
3. 同步只补最小 `dc2 contract/dataset` 字典，先服务这两条线

最小字典优先锁定：

- `route_table`
- `interface_ip`
- `arp / mac`
- `topology adjacency`
- `policy seed`

## 最后判断

当前最不该做的事情，不是继续补更多分支功能，而是同时把：

- NetPath 的 `policy / result / evidence / probe / ticket`
- IPAM 的 `projection / audit / smoke / launch gate`
- `dc2` 的全量 contract 设计

一起摊开并行推进。

更有效的方式是：

```text
IPAM 先收上线闭环
  -> NetPath 再收演示闭环
  -> dc2 最小契约最后补成稳定底座
```

这样更容易让 OneOPS 先出现两个真正可讲清楚的样板：

- 一个是“资源治理闭环”样板
- 一个是“路径分析闭环”样板
