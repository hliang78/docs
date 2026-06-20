# MVP 策略-仪表盘体系简化 设计

> 日期：2026-06-16
> 范围：OneOps 后端的 Teleabs 监控策略 + Grafana 仪表盘"展示发现"路径
> 子仓库：`OneOps`（当前分支 `snmp_metric`）
> 状态：设计待用户评审

---

## 1. 目标与原则

把"策略集 → 仪表盘"的**展示主线**用 MVP 理念简化:**保留现有主线逻辑,只把"展示发现"从重型生成管线切换为轻量绑定查询**。不重写、不新造体系。

MVP 北极星(已与用户对齐):

> **一个策略集 = 一个仪表盘(现成种子盘),通过 `strategy_set ↔ dashboard_code` 绑定关联;设备作为 Grafana 变量传入;监控中心按绑定加载展示。**

种子分析已证明:`quick_env` 里 17 个现成仪表盘 + 策略集↔盘绑定已存在并跑通 MVP,**无需生成管线**。

---

## 2. 硬约束:可改代码面

**只能修改 `snmp_metric` 分支相对 `feature/device-v2-platform-core-optimization` 特有/不同的文件**(merge-base = 2026-06-11 21:26)。

- ⛔ **禁动**:6/11 之前的共享代码、device-v2 相关代码、**下发(dispatch)核心链路**。
- ✅ **可改**:`snmp_metric` 分支 6/11 后新增/修改的 91 个文件。本设计涉及的目标文件已全部核实在可改面内。
- **种子同样受约束**:不修改 6/11 之前 / 与 device-v2 共享的既有 `quick_env` 种子文件;补绑定只能通过**新增种子文件**或本分支特有的种子实现,不动旧种子。
- 重要巧合:需简化/移除的"SNMP 仪表盘生成管线 + 审计三表"**正是分支特有代码**,可改;而被禁动的恰是用户要保留的部分。约束与方案天然一致。

---

## 3. 保留的主线(三段,不改)

```
① 种子    quick_env 预置：策略集 + 策略 + 现成仪表盘 + strategy_set↔dashboard 绑定 + (record rule 手工/种子)
② 下发    选设备+策略集 → 生成 Telegraf → 推 agent → 写 StrategyApplyRecord(strategy_set_id ↔ 设备)   【完整保留，禁改】
③ 展示    监控中心：选设备 → 查该设备的策略集 → 按绑定取盘 → Grafana 带 device 变量加载
```

- **下发(②)**:完整保留,本设计不触碰(即使部分文件在可改面内,也不改)。
- **设备↔策略集 关联**:沿用 `StrategyApplyRecord.strategy_set_id`,不新增机制。
- **设备作 Grafana 变量**:已实现(`GrafanaDashboard.vue` 拼 `var-device_code` 等),不改。

---

## 4. 本次唯一核心改动:展示发现路径 重型生成 → 轻量绑定

### 现状(重)
`app/platform/api/metric_strategy.go` 的 `ListDeviceBoundDashboardsByTargetPart`
→ 调 `resolveDashboardTreesForStrategySet()`
→ 进入 `metric_capability_contract_resolver.go`(10,619 行)**物化仪表盘树 / by-target 生成**才返回盘。

### MVP(轻)
```
设备 target_part
  → StrategyApplyRecord 查 strategy_set_id（该设备下发过的策略集）
  → platform_teleabs_strategy_set_dashboard_binding 取 dashboard_code（种子已绑）
  → 查 grafana_dashboard 返回盘(uid/code/name)
  → 前端带 device 变量加载
```
**不再触发任何树物化 / by-target 生成。** 只改"展示发现"这一处函数的实现,返回结构对前端保持兼容(字段可空)。

### 影响文件(均在可改面)
- `app/platform/api/metric_strategy.go` — `ListDeviceBoundDashboardsByTargetPart` 改为绑定查询。
- 绑定读取复用现有 `platform_teleabs_strategy_set_dashboard_binding` + `grafana_dashboard`。

---

## 5. 关键决策(已对齐)

| 项 | 决策 |
|----|------|
| **下发 dispatch** | 完整保留,禁改 |
| **前端(4 Tab + 详情抽屉)** | 暂不动,留作输入/测试入口,最后收尾 |
| **双 mode(bundle/selector)** | **不动**——mode 是下发在用,与展示绑定无关 |
| **variant** | 冻结为单值 `operations`,不作为展示维度 |
| **recording rule** | **方案 A**:种子/手工预置,MVP 不做运行时"预览→发布"管线 |
| **审计三件套**(PanelBinding/Snapshot/SaveSummary) | 砍——但因前端详情抽屉仍在调,**实际删除留到最后收尾**,本期仅让主线不依赖它们 |
| **仪表盘生成管线**(`snmp_grafana_switch_dashboard_*` 等) | 移出主线;前端仍可调,**代码删除留到最后随前端收尾** |

---

## 6. 落地顺序

```
P1  展示发现路径切到"简单绑定"               ← 本期核心，单点后端改动
      · 改 ListDeviceBoundDashboardsByTargetPart
      · 不再调 resolveDashboardTreesForStrategySet
      · 返回结构对前端兼容
P2  种子绑定补齐                              ← 给主要 SNMP 策略集都补 strategy_set↔盘 绑定
      · 仅通过【新增种子文件】实现，不改既有/共享种子
      · 验证：种子起库后，监控中心选设备能直接出盘
P3  （最后收尾，本设计不含）                  ← 删生成管线 + 审计三表 + 前端重编辑入口
```

本期交付 = **P1 + P2**:监控中心展示走轻量绑定,种子端到端跑通。P3 留待前端收尾时统一处理。

---

## 7. 验收标准

1. 种子起库后,监控中心选一台已下发的 SNMP 交换机 → 自动加载其策略集绑定的种子盘,设备变量正确注入,出图有数据。
2. 展示发现路径**不再进入** `metric_capability_contract_resolver` 的树物化逻辑(可通过日志/调用链确认)。
3. 下发链路、前端页面行为**零回归**(现有接口表面不破坏)。
4. 改动文件全部落在可改面内(`snmp_metric` vs `device-v2` 差异集),无越界。

---

## 8. 明确不做(Out of Scope)

- 不改下发/采集链路。
- 不改前端(本期)。
- 不删生成管线与审计表代码(留最后收尾)。
- 不动 mode、不做 recording rule 运行时管线。
- 不碰 device-v2 及 6/11 前共享代码。
