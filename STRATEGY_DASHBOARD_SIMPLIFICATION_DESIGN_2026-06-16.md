# Teleabs 监控策略 × Grafana 仪表盘 体系简化改造方案

> 日期：2026-06-16
> 范围：Teleabs 监控策略体系（`OneOps/app/platform`）+ Grafana 仪表盘体系（`OneOps/app/grafana` + 平台生成管线）
> 不在本次范围：Alert 告警策略体系（`OneOps/app/alert`）
> 状态：**设计待确认（先方案、不动代码）**

---

## 0. 一句话结论

当前"策略集 → 策略 → 仪表盘"被实现成一条**为 SNMP 交换机定制、却用通用名字包装**的重管线：双 mode 分叉、5 张仪表盘绑定表、34 个 REST handler、前端 4000+ 行的页面与 6 个独立状态文件。简化的核心不是"再加抽象",而是**砍分叉、并表、收敛所有权、删死代码**。

---

## 1. 现状评估（量化）

### 1.1 后端数据模型

| 模型 | 文件 | 表 | 说明 |
|------|------|----|------|
| `TeleabsStrategySet` | `app/platform/platform_model/teleabs_strategy_set.go:12` | `platform_teleabs_strategy_set` | 策略集，含 `mode` 双模式分叉 |
| `TeleabsStrategySetItem` | 同上 `:34` | `..._item` | 模板引用 + 默认参数 |
| `TeleabsStrategy` | `app/platform/platform_model/teleabs_strategy.go` | `platform_teleabs_strategy` | 策略，含 `scope_type`、`parent_id` 父子 |
| `TeleabsStrategySetDashboardBinding` | `teleabs_strategy_set.go:48` | `..._dashboard_binding` | 策略集→仪表盘 code（1:1） |
| `TeleabsStrategySetDashboardPanelBinding` | `teleabs_strategy_set.go:60` | `..._dashboard_panel_binding` | **28 列**，面板→策略/指标/规则追溯 |
| `TeleabsStrategySetDashboardTargetBinding` | 同文件 | `..._dashboard_target_binding` | 每设备仪表盘实例 |
| `TeleabsStrategySetDashboardSnapshot` | 同文件 | `..._dashboard_snapshot` | 覆盖前历史快照 |
| `TeleabsStrategySetDashboardSaveSummary` | 同文件 | `..._dashboard_save_summary` | 保存事务日志 |
| `GrafanaDashboard` | `app/grafana/grafana_model/dashboard.go:9` | `grafana_dashboard` | 仪表盘本体（树形 parent_id） |
| `legacy metric strategy` ×4 表 | `platform_model/metric_strategy_legacy.go` | `platform_metric_strategy_{global,group,instance}` 等 | **死代码**，`//go:build legacy_metric_strategy` |

> 单"策略集↔仪表盘"一个关注点用了 **5 张表 / 110+ 列**。

### 1.2 后端 API（`app/platform/router/platform.go`）

- Teleabs 路由共 **34 个 handler**（`teleabs.go`）。
- 仪表盘生成管线路径极度冗长，例如：
  - `POST strategy-sets/:id/metric-contract/grafana/dashboards/materialize/dry-run/by-target`
  - `POST strategy-sets/:id/metric-contract/grafana/dashboard-tree/save/by-target`
  - `GET  strategy-sets/:id/metric-contract/grafana/dashboard-tree/save-summary/by-batch/:save_batch_id`
  - 另有 `dashboards/save`、`dashboard-tree/save`、`save-and-sync`、`save-batches` 等近 10 条同源变体。
- 生成逻辑实质是 **SNMP/交换机专用**：`service/impl/snmp_grafana_switch_dashboard_*.go`（persistence service 17KB）、`snmp_grafana_switch_baseline_module.go`。"通用 Teleabs"外壳下是单一设备类型实现。
- `teleabs_strategy_set.go` service 单文件 **1116 行**。

### 1.3 前端（`OneOPS-UI/src`）

| 文件 | 行数/大小 | 问题 |
|------|----------|------|
| `views/platform/StrategyTemplate/index.vue` | 1298 行 | 4 Tab（模板库/策略集/策略列表/SNMP指标分组）全塞一页 |
| `.../StrategySetDetailDrawer.vue` | 55 KB | 单组件巨石 |
| `.../StrategySetFormModal.vue` | 33 KB | 双 mode 表单分叉 |
| `views/grafana/Dashboard.vue` | 2033 行 | root/strategy/reference 三种 kind |
| `.../plugin-forms/PluginForm*.vue` | 27 个 | 每插件一表单 |
| `snmpStrategySet{DashboardTree,FormalClosure,GrafanaDashboardSave,RecordingRule}State.ts` | 4 个独立状态文件 | 生成流程状态散落、SNMP 专用 |
| `api/platform/teleabs.ts` | 521 行 | 对应 34 个后端 handler |

- 无 Pinia store，全靠组件级 `ref`，跨 Tab/抽屉状态难追踪。
- 遗留死代码：`api/alert/alert_policy.js`（旧 JS）、`views/platform/MetricStrategyManagement.vue`（标注"已迁移"仍保留）。

### 1.4 仪表盘"三处所有权"

1. `app/grafana/` —— 仪表盘 CRUD / import / batchSync。
2. `app/platform/teleabs` —— 由策略集 materialize 生成仪表盘 + 5 张绑定表。
3. `views/dashboard/Monitor.vue` —— iframe 嵌入大盘。

→ 仪表盘的"创建/更新"分散在两个后端模块,边界不清。

---

## 2. 核心问题诊断

1. **双 mode 分叉（template_bundle / strategy_selector）**：贯穿 model、service、前端表单,几乎所有分支都要写两遍。
2. **5 张仪表盘绑定表过度建模**：Binding/Panel/Target/Snapshot/SaveSummary 跨表事务一致性脆弱,且大部分仅服务于"可追溯/审计"次要诉求。
3. **"通用"名 + "SNMP 专用"实现的错配**：命名暗示通用,实现 `snmp_grafana_switch_*` 只覆盖交换机,扩展即破。
4. **API 沿 materialize/dry-run/save/save-and-sync/tree/by-target 笛卡尔展开**:近 10 条同源路径,前端要逐一对接。
5. **死代码未清**：legacy metric strategy（编译隔离 4 表）、`alert_policy.js`、`MetricStrategyManagement.vue`。
6. **前端巨石组件 + 散状态**:55KB 抽屉 / 1298 行页面 / 6 个状态文件,无 store。

---

## 3. 改造目标与原则

- **目标**：让"配一组采集策略 → 一键得到设备仪表盘"这条主链路在数据模型、API、UI 三层都最短。
- **原则**：
  1. 一条主路径（去 mode 分叉,选定 selector 为唯一模型,bundle 作为其特例）。
  2. 表能并就并（5 → 2）。
  3. 仪表盘所有权单一化（生成与 CRUD 都归 grafana 模块,platform 只产 JSON）。
  4. API 收敛为"预览 + 应用"两个动词,去掉 dry-run/tree/by-target 组合爆炸。
  5. 先删死代码,再谈重构(零风险净化)。

---

## 4. 目标架构设计（建议）

### 4.1 数据模型：5 张绑定表 → 2 张

```
保留：
  StrategySet ─1:N─ StrategySetItem ─ refs ─> Strategy ─ refs ─> Template
  StrategySet ─1:N─ DashboardLink   (合并 Binding + TargetBinding)
       字段: strategy_set_id, dashboard_code, target_device_code(空=模板级),
             role(root|strategy), parent_dashboard_code, owner_strategy_id

合并/降级：
  PanelBinding  → 折成 DashboardLink.trace_json（仅在需要追溯时落)，或彻底移除
  Snapshot      → 用 grafana_dashboard 自身版本/或对象存储,不单列表
  SaveSummary   → 降为应用日志(已有日志体系),不建专表
```

> 收益:策略集↔仪表盘从 5 表降到 2 表,删除约 80+ 列与对应 DAL/迁移。

### 4.2 去掉 mode 分叉

- 选 `strategy_selector` 为唯一模型（更通用,auto-apply 能力依赖它）。
- `template_bundle` 视为"selector 项已固定"的特例,迁移脚本把现有 bundle 转成等价 selector 项。
- 删除 model `Mode` 字段及 service/前端所有 `if mode == ...` 分支。

### 4.3 API 收敛

把近 10 条仪表盘路径收敛为 2 个：

```
POST strategy-sets/:id/dashboard/preview   { target? }   // 取代所有 materialize/dry-run(/tree)(/by-target)
POST strategy-sets/:id/dashboard/apply     { target? }   // 取代所有 save / save-and-sync / tree/save
```

- `target` 可选:空=模板级预览,有值=按设备。
- `tree` 作为返回结构而非独立端点。
- save-summary/save-batches 若保留审计,改为 `GET .../dashboard/apply-records`(与现有 apply-records 风格一致)。

### 4.4 仪表盘所有权单一化

- `platform/teleabs` 只负责:由策略集 + 设备 → 生成 Grafana dashboard JSON（纯函数,无落库)。
- 落库 / sync / 状态 / 树 全部回归 `app/grafana`,复用其 `Create/Update/BatchSync`。
- 删除 `snmp_grafana_switch_dashboard_persistence_service.go` 的落库职责,只留生成器。

### 4.5 前端简化

- `StrategyTemplate/index.vue` 4 Tab → 拆成独立路由页(模板库 / 策略集 / 策略),SNMP指标分组并入策略详情。
- 引入 `pinia/modules/strategy.ts` 统一策略集/策略/生成流程状态,替代 6 个散状态文件。
- `StrategySetFormModal` 去 mode 分支后预计可瘦身 30–40%。
- 仪表盘生成交互:`预览 → 应用` 两步,对接收敛后的 2 个 API。

---

## 5. 分阶段执行计划

| 阶段 | 内容 | 风险 | 可独立交付 |
|------|------|------|-----------|
| **P0 净化** | 删 legacy metric strategy 4 表+build flag、`alert_policy.js`、`MetricStrategyManagement.vue`;盘点真实调用方 | 极低 | ✅ |
| **P1 API 收敛** | 新增 `dashboard/preview`+`apply`,旧路径标注 deprecated 并内部转发;前端切到新 API | 中 | ✅ |
| **P2 表合并** | Binding+TargetBinding→DashboardLink;Panel/Snapshot/Summary 降级;写迁移脚本 | 中高 | ✅ |
| **P3 去 mode** | bundle→selector 迁移,删 Mode 分支(前后端) | 中高 | ✅ |
| **P4 所有权收敛** | 生成器与落库解耦,仪表盘落库回归 grafana | 中 | ✅ |
| **P5 前端拆分** | Tab 拆页 + 引入 store + 巨石组件拆分 | 中 | ✅ |

> 建议顺序 P0 → P1 → P2/P3 → P4 → P5;P0 可立即做且零风险。

---

## 6. 待确认的关键取舍（决策点）

1. **保留多少"可追溯/审计"能力？** Panel/Snapshot/SaveSummary 是为审计而生。若业务上不强依赖,可直接删,简化收益最大;若需保留,折成 1 个 trace 字段/复用日志。
2. **是否接受弃用 `template_bundle`？** 需确认现网是否有大量 bundle 模式策略集依赖。
3. **仪表盘生成是否仍只服务 SNMP 交换机？** 若短期不会扩展到其他设备类型,可大胆移除"通用"外壳,直接命名为 switch dashboard,反而更清晰。
4. **迁移窗口**：是否允许一次性数据迁移(停机/灰度),决定 P2/P3 能否激进合并而非长期双写。

---

## 7. 附:关键文件索引

后端:
- `app/platform/platform_model/teleabs_strategy_set.go`
- `app/platform/service/impl/teleabs_strategy_set.go`（1116 行）
- `app/platform/service/impl/snmp_grafana_switch_dashboard_persistence_service.go`
- `app/platform/api/teleabs.go`（34 handler）
- `app/platform/router/platform.go:435-468`
- `app/grafana/grafana_model/dashboard.go`

前端:
- `src/views/platform/StrategyTemplate/index.vue`（1298 行）+ `StrategySetDetailDrawer.vue`（55KB）
- `src/views/grafana/Dashboard.vue`（2033 行）
- `src/api/platform/teleabs.ts`（521 行）
- `src/views/platform/StrategyTemplate/snmpStrategySet*State.ts`（4 个状态文件）
