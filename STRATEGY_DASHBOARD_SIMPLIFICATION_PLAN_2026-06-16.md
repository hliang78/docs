# 策略 × 仪表盘 简化改造执行计划

> 日期：2026-06-16
> 配套文档：`STRATEGY_DASHBOARD_SIMPLIFICATION_DESIGN_2026-06-16.md`（现状评估）
> 依据：`docs/superpowers/specs/` 下 6/10–6/15 的 SNMP 演进 spec（已冻结目标模型）
> 范围：Teleabs 监控策略 + Grafana 仪表盘。不含 Alert。
> 状态：**计划待确认**

---

## 0. 一句话目标

> spec 已经把目标模型想清楚了（**策略结构即仪表盘结构 / 定义先于运行 / 责任先于数据**），但**代码还停在"按设备拍平"的旧机制**。
> 本计划 = 让代码追上 spec，**并顺手砍掉 spec 的赘肉**，落成 **1 棵树 / 2 类归属 / 2 个动作 / 2 层落库**。

---

## 1. Spec 目标模型 ↔ 现有代码 差距表

| 维度 | Spec 目标（已冻结） | 现有代码实况 | 差距 | 难度 |
|------|-------------------|-------------|------|------|
| **生成主键** | suite/策略集 → root，策略 → node，**target 只绑定** | `resolveTreeGeneration(setID, **TargetPart, DashboardVariant**)` 仍以 `(set, target, variant)` 拍平 | ❌ 核心未改 | 高 |
| **定义层** | StrategyTree / DashboardLogicalTree / NodeOwner / PanelSlot，**非 target 即成立** | 代码中**无这些概念**；树在运行时、带 target 才生成 | ❌ 完全缺失 | 高 |
| **树的数量** | spec 列 3 棵（策略/模板/实例）；简化目标=**1 棵+实例** | 运行时单棵树，混在 resolver 里 | 🟡 需重构归位 | 中 |
| **面板归属** | 仅 2 类 owner（strategy/root），**定义层定死** | `OwnerStrategyID` 在 `metric_capability_contract_resolver.go` **运行时晚推断** | ❌ spec 自认的头号缺口 | 中 |
| **核心实现** | 清晰分层 | `metric_capability_contract_resolver.go` = **10,619 行 / 352 函数**单体 | ❌ 巨石 | 高 |
| **recording-rule 管线** | 简化目标=预览+应用 | preview / dry-run / publish 三段 + 6 步状态机 | 🟡 可收敛 | 中 |
| **仪表盘 API** | 简化目标=preview+apply | materialize/save/tree/save-and-sync/by-target ~10 接口 | 🟡 可收敛 | 中 |
| **绑定落库** | 简化目标=2 表 | 5 表（Binding/Panel/Target/Snapshot/SaveSummary）110+ 列 | 🟡 可并表 | 中高 |
| **双 mode** | 单一模型 | `Mode: template_bundle/strategy_selector` 仍贯穿前后端 | 🟡 可去分叉 | 中 |
| **变体 variant** | 先做一套 | `dashboard_variant` 已是必填入参 | 🟡 可先冻结为单值 | 低 |
| **前端** | 模板/策略/策略集 三页 + store | 1298 行单页 4 Tab + 55KB 抽屉 + **6 个 SNMP 状态文件**，全键于 target/variant | ❌ 巨石+散状态 | 高 |
| **死代码** | — | legacy metric strategy 4 表 / `alert_policy.js` / `MetricStrategyManagement.vue` | ✅ 可直接删 | 低 |

**结论**：差距集中在两点——① **生成主键仍是拍平的**(target/variant),没有定义层；② **核心逻辑是 1 万行巨石**。其余(管线/API/表/mode/前端)都是围绕这两点长出来的赘肉,主键一改,赘肉才好砍。

---

## 2. 简化目标（落地形态)

```
定义层（配一次，不带设备）                     运行层（设备来了，对号出图）
┌──────────────────────────────┐             ┌────────────────────────┐
策略集 ─> 策略(父子) ─> 面板槽(归属固定)          +目标设备 ─> 预览 ─> 应用
   └── 1 棵树：策略结构 = 仪表盘结构              target 只绑定，不建树     │
                                                                  生成Grafana
   2 类归属：明细→策略 / 总览导航→策略集                              + 1 条绑定
   2 个动作：preview / apply
   2 层落库：DashboardLink(定义绑定) + 仪表盘实例(运行)
```

---

## 3. 分阶段执行计划

> 原则：**先零风险净化 → 再立定义层骨架 → 再收敛赘肉 → 最后动前端**。每阶段可独立交付、可回退。

### P0 净化（零风险，1–2 天）
- 删 legacy metric strategy（4 表 + `//go:build legacy_metric_strategy`）— `platform_model/metric_strategy_legacy.go` 及相关 DAL。
- 删前端 `api/alert/alert_policy.js`、`views/platform/MetricStrategyManagement.vue`（先 grep 确认零调用方）。
- 删未用的 SNMP/Template 旧策略模型。
- **交付物**：一个纯删除 PR，编译+测试通过,代码量先降一截。

### P1 立定义层骨架（核心，1–2 周）★最关键
- 新增定义层模型(非 target)：`StrategyDashboardNode`(= 策略节点→仪表盘逻辑节点,带 `NodeOwner`)、`PanelSlot`(带显式 owner: strategy/root)。
- 从 `metric_capability_contract_resolver.go` **抽出"定义层求解"**：输入策略集→输出逻辑树(root/strategy 节点 + 面板槽归属),**不带 target**。
- 归属规则按 spec 决策表硬编码两类：`interface_basic.*/system_basic.*/路由族 → strategy`;`平台/证据/导航/汇总 → strategy_set`。
- **交付物**：定义层可单测——给一个策略集,不给设备,就能算出完整的"仪表盘逻辑树 + 面板归属"。这一步把 spec 头号缺口(归属晚推断)补上。

### P2 运行层改为"绑定而非建树"（1 周）
- 把 `resolveTreeGeneration(set, target, variant)` 改成：**读 P1 的定义层逻辑树 → 按 target 实例化**(填数据源/设备变量),target 不再决定树形。
- `dashboard_variant` 先冻结为单一默认值,从必填入参降为可选/内部常量。
- **交付物**：同一策略集对多台设备产出**结构一致**的仪表盘,差异只在数据。

### P3 收敛 API 与表（1 周）
- API：新增 `POST strategy-sets/:id/dashboard/preview` + `apply`,旧 ~10 条路径内部转发并标 deprecated。
- 表：`Binding + TargetBinding → DashboardLink`;`PanelBinding` 折成 `DashboardLink.trace_json` 或删;`Snapshot/SaveSummary` 降级为应用日志。写迁移脚本。
- recording-rule：preview/dry-run 合并为 preview,publish 保留(真副作用),6 步状态机收敛成 成功/失败。
- **交付物**：2 接口 + 2 表 + 预览/应用两段管线。

### P4 去双 mode（0.5 周）
- 选 `strategy_selector` 为唯一模型,写迁移把现存 `template_bundle` 转等价 selector 项。
- 删 model `Mode` 字段 + service/前端所有 `if mode==` 分支。
- **交付物**：单一策略集模型。

### P5 前端拆分（1–2 周）
- `StrategyTemplate/index.vue` 4 Tab → 模板库 / 策略集 / 策略 三独立路由页;SNMP 指标分组并入策略详情。
- 6 个 `snmpStrategySet*State.ts` + 组件级 ref → 1 个 `pinia/modules/strategyDashboard.ts`。
- 仪表盘交互对接 P3 的 preview/apply 两动作;`StrategySetDetailDrawer.vue`(55KB)随 mode/变体去除瘦身。
- **交付物**：三页 + 一个 store + 预览/应用两步交互。

### 依赖顺序
```
P0 ──> P1 ──> P2 ──> P3 ──> P5
              └────> P4 ──┘
```
P0 可立即做;P1 是地基,P2 依赖 P1;P3/P4 可并行;P5 收尾。

---

## 4. 工作量与风险一览

| 阶段 | 工作量 | 风险 | 主要触及文件 |
|------|--------|------|-------------|
| P0 | 1–2 天 | 极低 | `metric_strategy_legacy.go`、`alert_policy.js`、`MetricStrategyManagement.vue` |
| P1 | 1–2 周 | 中（新模型设计） | `metric_capability_contract_resolver.go`(抽取)、新增定义层 model |
| P2 | 1 周 | 中高（改生成主键） | `snmp_grafana_switch_dashboard_*.go`、`teleabs_strategy_set.go` |
| P3 | 1 周 | 中高（并表+迁移） | `teleabs_strategy_set.go`(model)、`router/platform.go`、`api/teleabs.go` |
| P4 | 0.5 周 | 中（数据迁移） | `teleabs_strategy_set.go`、前端表单 |
| P5 | 1–2 周 | 中 | `StrategyTemplate/*`、新增 pinia store |

**最大风险点**：P1 抽取定义层 = 要从 10,619 行的 resolver 里剥出干净边界。建议 P1 用"**先平行新建、再切流量、后删旧**"的方式,不在巨石里原地改。

---

## 5. 仍需你拍板的决策点

1. **变体 variant**：确认现网是否只用单一变体?(决定 P2 能否直接冻结为单值,省掉一整条维度)
2. **可追溯/审计**:`PanelBinding/Snapshot/SaveSummary` 业务上还要不要?(要→折成 trace 字段;不要→P3 直接删,收益最大)
3. **`template_bundle` 弃用**:现网有多少 bundle 策略集?(决定 P4 迁移成本)
4. **仪表盘是否仍只服务 SNMP 交换机**?(若是,P1/P2 可大胆去"通用"外壳,直接 switch 化,反而更简单)
5. **迁移窗口**:能否一次性灰度迁移?(决定 P3/P4 能否激进并表而非长期双写)

---

## 6. 建议的第一刀

**先做 P0(零风险净化)+ 启动 P1 的定义层模型设计**。
P0 立即让代码瘦身、建立信心;P1 是整个改造的地基,且与 spec 已冻结模型一一对应,最值得先投入。
其余阶段在 P1 骨架立住后,都是"砍赘肉",风险与范围都可控。
