# P3 收尾:删除生成管线 + 审计表 + 前端重编辑入口 —— 实施计划【草案】

> 日期：2026-06-16
> 状态：**草案(DRAFT)** —— 待用户确认范围与待决点后,再展开为完整 TDD 计划
> 前置：P1(展示路径轻量绑定)+ P2(种子绑定)已完成
> 配套 spec：`docs/superpowers/specs/2026-06-16-mvp-strategy-dashboard-simplification-design.md`

---

## 0. 目标

P1 已让**展示主线**不再依赖仪表盘生成管线。P3 把这些"现在没人(主线)用、但仍占着大量代码与表"的部分**安全拆除**:生成管线、审计三表、前端重编辑入口。最终把"策略→仪表盘"留成 P1 的极简形态。

**核心风险**:前端详情抽屉/状态文件仍在调生成与录制接口。**必须按"前端先脱钩 → 后端再拆"的顺序**,否则破坏页面。

---

## 1. 拆除清单(按依赖倒序)

### A. 前端重编辑入口(先做,先脱钩)
- `OneOPS-UI/src/views/platform/StrategyTemplate/StrategySetDetailDrawer.vue` —— 降为只读详情,移除:录制规则预览/物化/发布、仪表盘保存/同步、树试点(formal closure)、模板管理、能力预检。
- `OneOPS-UI/src/views/platform/StrategyTemplate/snmpStrategySetRecordingRuleState.ts`
- `OneOPS-UI/src/views/platform/StrategyTemplate/snmpStrategySetFormalClosureState.ts`
- `OneOPS-UI/src/views/platform/StrategyTemplate/snmpStrategySetGrafanaDashboardSave.ts`
- `OneOPS-UI/src/views/platform/StrategyTemplate/snmpStrategySetDashboardTreeState.ts`
- `OneOPS-UI/src/views/platform/StrategyTemplate/snmpStrategySetTargetPanelPreview.ts`
- `OneOPS-UI/src/views/platform/StrategyTemplate/snmpGrafanaDashboardTemplateManagement.ts`
- `OneOPS-UI/src/views/platform/StrategyTemplate/index.vue` —— 移除 "SNMP 指标分组" 等重编辑 Tab(保留 模板库/策略集/策略 三 Tab)。
- `OneOPS-UI/src/api/platform/teleabs.ts` —— 删除 materialize/save/dashboard-tree/recording-rules/panel-support 系列函数。

### B. 后端 API 与路由(前端脱钩后)
- `OneOps/app/platform/api/teleabs.go` —— 删除 by-target materialize/save、dashboard-tree、recording-rules preview/materialize/publish、panel-support 等 handler(保留策略/策略集/模板 CRUD)。
- `OneOps/app/platform/router/platform.go` —— 删除对应路由(第 449–464 等行段)。

### C. 后端生成/录制服务(API 删后)
- `OneOps/app/platform/service/impl/snmp_grafana_suite_dashboard_tree_module.go`
- `OneOps/app/platform/service/impl/snmp_grafana_switch_baseline_module.go`
- `OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_generator.go`
- `OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_persistence_service.go`
- `OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_service.go`
- `OneOps/app/platform/service/impl/snmp_grafana_target_class_module.go`
- `OneOps/config/snmp_recording_rule_publisher.go`
- `OneOps/cmd/snmp_dashboard_backfill/`(整目录)
- `OneOps/app/platform/service/impl/metric_capability_contract_resolver.go` —— 剥离树物化/by-target/面板归属相关代码(**最难,10,619 行,留最后**;P1 已不再调用其树路径,但仍有其他 metric-contract 能力,不能整删——需精细切分)。

### D. 数据模型与迁移(审计三件套)
- `OneOps/app/platform/platform_model/teleabs_strategy_set.go` —— 删除 `TeleabsStrategySetDashboardPanelBinding`、`...Snapshot`、`...SaveSummary`(及 `...TargetBinding`)结构;**保留** `TeleabsStrategySetDashboardBinding`(P1 主线在用)。
- `OneOps/app/platform/platform_model/snmp_recording_rule_publish_record.go` —— 删除。
- 迁移:新增 **drop** 迁移删除 `platform_teleabs_strategy_set_dashboard_panel_binding`、`..._snapshot`、`..._target_binding`、`platform_snmp_recording_rule_publish_records` 等表(不改既有迁移,只新增 drop 脚本)。

---

## 2. 安全拆除顺序(分阶段,每阶段可独立交付+回退)

```
P3-1  前端脱钩       详情抽屉降只读 + 删 snmp*State.ts + 删 teleabs.ts 待删函数 + index.vue 收 Tab
        验证：前端 typecheck/build 通过；策略集列表/创建/详情(只读)正常
P3-2  后端 API/路由  删 teleabs.go 生成/录制 handler + platform.go 路由
        验证：go build ./app/platform/...；teleabs 路由一致性测试更新
P3-3  后端服务       删 snmp_grafana_* 6 模块 + recording publisher + backfill cmd
        验证：go build；删除连带的 *_test.go
P3-4  resolver 切分  从 metric_capability_contract_resolver.go 剥离树/by-target/面板归属
        验证：保留的 metric-contract 能力测试仍过(最高风险，单独细化)
P3-5  表与模型       删审计结构 + 新增 drop 迁移
        验证：go build；迁移在新库可执行；P1 主线(绑定查询)不受影响
```

---

## 3. 验证基线(每阶段必过)

1. **P1 主线零回归**:`go test ./app/platform/api/ -run TestMetricStrategyAPIListDeviceBoundDashboards` 全过(展示路径只依赖 `TeleabsStrategySetDashboardBinding` + `grafana_dashboard`,不依赖被删项)。
2. **编译**:`go build ./app/platform/... ./app/grafana/...` exit 0。
3. **前端**:`yarn typecheck`(或 `npm run typecheck`)+ build 通过。
4. **越界校验**:后端改动文件全部在 `snmp_metric vs device-v2` 可改面内(P3 清单已核实均在);种子如涉及只新增 drop 迁移文件。

---

## 4. 风险与难点

| 风险 | 说明 | 缓解 |
|------|------|------|
| **resolver 切分(P3-4)** | 10,619 行单体,树物化与其他 metric-contract 能力交织,易误删 | 单独立细化计划;先标注"P1 已不调用"的死路径,逐函数确认调用方后再删;保留有测试覆盖的能力 |
| **前端隐藏依赖** | 抽屉/状态文件可能被其他页面间接引用 | P3-1 前先全局 grep 引用;typecheck 兜底 |
| **删表不可逆** | drop 迁移破坏性 | 只在确认 P1 主线与 `TeleabsStrategySetDashboardBinding` 无关后执行;drop 脚本加 `IF EXISTS`;保留数据备份说明 |
| **测试连带** | 删服务会留下悬空 `*_test.go` | 同阶段一并删除对应测试 |

---

## 5. 待用户确认的决策点

1. **前端可改面基线**:`OneOPS-UI` 无 `device-v2-platform-core-optimization` 分支。P3-1 改前端时,以哪个分支/提交为"只能动特有代码"的基线?(还是前端这批 SNMP 编辑文件确认可自由动?)
2. **resolver 切分深度**:`metric_capability_contract_resolver.go` 是否本期就切分(高风险),还是仅删独立的 snmp_grafana_* 模块、resolver 内死代码留作更后续?(建议:本草案 P3-4 单独延后,先做 P3-1/2/3/5)
3. **录制规则(recording rule)**:确认彻底删发布管线(`snmp_recording_rule_publisher` + publish_record 表)?(P1 已确定 record rule 走种子/手工)
4. **删表时机**:是否允许对现网/测试库执行 drop 迁移,还是仅提供脚本待运维择机执行?

---

## 6. 下一步

确认上述 4 个决策点后,我把 **P3-1(前端脱钩)** 先展开为完整 TDD 实施计划(其余阶段随后逐个展开),仍按 subagent 驱动 + Sonnet 经济执行。
