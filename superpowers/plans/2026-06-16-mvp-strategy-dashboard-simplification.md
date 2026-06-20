# MVP 策略-仪表盘体系简化 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把监控中心"展示发现"路径从重型仪表盘树物化切换为轻量的 `策略集→绑定→种子盘` 查询,并补齐缺失的种子绑定,使 MVP 主线端到端跑通。

**Architecture:** 在 `MetricStrategyAPI` 上新增一个 `resolveBoundDashboardsForStrategySet`,仅按 `set.DashboardCodes`(来自 `platform_teleabs_strategy_set_dashboard_binding`)返回扁平的根盘节点——不展开子树、不做设备匹配(设备在展示层作为 Grafana 变量注入)。把 `ListDeviceBoundDashboardsByTargetPart` 改为调用它。不触碰下发链路、不触碰前端、不删除既有生成管线代码(留最后收尾)。

**Tech Stack:** Go 1.x + Gin + GORM(sqlite 用于单测)、MySQL 种子 SQL(quick_env)。

**约束(硬):** 仅修改 `OneOps` 子仓库 `snmp_metric` 分支相对 `feature/device-v2-platform-core-optimization` 特有的文件(merge-base 2026-06-11)。种子仅**新增文件**,不改既有/共享种子。所有命令在 `/home/jacky/project/OneOPS-ALL/OneOps` 下执行,git 操作落在 `snmp_metric` 分支。

---

## 文件结构

- 修改:`app/platform/api/metric_strategy.go` — 新增 `resolveBoundDashboardsForStrategySet`;`ListDeviceBoundDashboardsByTargetPart` 改调它(替换第 747 行对 `resolveDashboardTreesForStrategySet` 的调用)。
- 修改:`app/platform/api/metric_strategy_device_dashboards_test.go` — 新增 MVP 行为单测。
- 新建:`quick_env/docker-entrypoint-initdb.d/zzzzzzzzzzz-mvp-strategy-set-dashboard-binding-bootstrap.sql` — 给缺绑定的种子策略集补 `strategy_set↔dashboard` 绑定。

> 说明:`resolveDashboardTreesForStrategySet` 及生成管线代码**保留不动**(前端详情抽屉仍在用),本期只是让主线展示不再走它。

---

### Task 1: 新增轻量绑定解析并切换展示路径

**Files:**
- Modify: `app/platform/api/metric_strategy.go`(新增函数 + 改 `ListDeviceBoundDashboardsByTargetPart` 第 747 行附近)
- Test: `app/platform/api/metric_strategy_device_dashboards_test.go`

- [ ] **Step 1: 写失败测试**

在 `app/platform/api/metric_strategy_device_dashboards_test.go` 末尾追加。该测试构造一个携带 `DashboardCodes` 的策略集与一条该设备的应用记录,断言:返回**一个扁平根节点**、`DashboardRole=="root"`、`MatchedBy=="binding"`、且**没有 children**(即不再做树展开)。复用文件已有的 fake(`fakeTeleabsStrategySrvForDashboardTree`、`fakeStrategyApplyRecordStoreWithDBForAPI`)与建表/建 API 的既有模式(参照同文件 `TestMetricStrategyAPIListDeviceBoundDashboardsByTargetPart_IgnoresLegacySavedBindingsWithoutStaticStrategyTree` 的 setup 写法:sqlite 建 `grafana_dashboard`、构造 `MetricStrategyAPI{TeleabsStrategySetSrv, StrategyApplyRecordStore(带DB), Logger}`、用 httptest 发 `GET /platform/metrics/strategy/device-dashboards?target_part=...`)。

测试主体断言部分:

```go
func TestMetricStrategyAPIListDeviceBoundDashboardsByTargetPart_MVPReturnsFlatBoundRoot(t *testing.T) {
	t.Parallel()

	h := newDeviceDashboardsTestHarness(t) // 见 Step 3：从既有测试 setup 提炼的小工具；若不提炼则按既有测试内联写法构造
	h.seedGrafanaDashboard("GDB-SW-001", "网络设备监控")
	h.seedStrategySet("set-sw", "交换机策略集", []string{"GDB-SW-001"}, []string{"网络设备监控"})
	h.seedApplyRecord("dev-001", "set-sw")

	resp := h.callDeviceDashboards("dev-001")

	if len(resp.Trees) != 1 {
		t.Fatalf("want 1 tree, got %d: %+v", len(resp.Trees), resp.Trees)
	}
	node := resp.Trees[0]
	if node.DashboardCode != "GDB-SW-001" {
		t.Fatalf("want dashboard_code GDB-SW-001, got %q", node.DashboardCode)
	}
	if node.DashboardRole != "root" {
		t.Fatalf("want role root, got %q", node.DashboardRole)
	}
	if node.MatchedBy != "binding" {
		t.Fatalf("want matched_by binding, got %q", node.MatchedBy)
	}
	if len(node.Children) != 0 {
		t.Fatalf("MVP must not expand children, got %d", len(node.Children))
	}
}
```

> 若文件中尚无 `newDeviceDashboardsTestHarness`/`seed*`/`callDeviceDashboards` 这类工具,**直接照搬同文件既有测试的内联 setup 代码**(建库、建表、塞 `grafana_dashboard` 行、构造 fake set 与 apply record、httptest 调用并 `json.Unmarshal` 进 `deviceDashboardTreeResponseForTest`),不要引入未定义的辅助函数。

- [ ] **Step 2: 运行测试确认失败**

Run: `go test ./app/platform/api/ -run TestMetricStrategyAPIListDeviceBoundDashboardsByTargetPart_MVPReturnsFlatBoundRoot -v`
Expected: FAIL —— 当前 `ListDeviceBoundDashboardsByTargetPart` 仍走 `resolveDashboardTreesForStrategySet`,`MatchedBy` 不是 `"binding"`(或返回树/children 不为空)。

- [ ] **Step 3: 实现轻量绑定解析函数**

在 `app/platform/api/metric_strategy.go` 中(紧邻 `resolveDashboardTreesForStrategySet` 之后)新增:

```go
// resolveBoundDashboardsForStrategySet 返回策略集绑定的根盘扁平节点（MVP）：
// 仅按 set.DashboardCodes（来自 strategy_set_dashboard_binding）出盘，不展开子树、
// 不做设备匹配——设备在展示层作为 Grafana 变量注入，故每个绑定盘均视为匹配。
func (a *MetricStrategyAPI) resolveBoundDashboardsForStrategySet(
	ctx context.Context,
	strategySetID string,
	set *dto.TeleabsStrategySetDto,
) []deviceDashboardTreeNode {
	if set == nil || len(set.DashboardCodes) == 0 {
		return nil
	}
	rootCodes := make([]string, 0, len(set.DashboardCodes))
	nameByCode := make(map[string]string, len(set.DashboardCodes))
	for idx, code := range set.DashboardCodes {
		trimmed := strings.TrimSpace(code)
		if trimmed == "" {
			continue
		}
		rootCodes = append(rootCodes, trimmed)
		if idx < len(set.DashboardNames) {
			nameByCode[trimmed] = strings.TrimSpace(set.DashboardNames[idx])
		}
	}
	if len(rootCodes) == 0 {
		return nil
	}

	// 尽力从 grafana_dashboard 补全盘名；DB 不可用时仅用绑定名。
	if db := a.strategyApplyRecordDB(ctx); db != nil {
		var roots []*grafanaModel.GrafanaDashboard
		if err := db.Model(&grafanaModel.GrafanaDashboard{}).
			Where("deleted_at IS NULL").
			Where("code IN ?", rootCodes).
			Find(&roots).Error; err == nil {
			for _, root := range roots {
				if root == nil {
					continue
				}
				code := strings.TrimSpace(root.Code)
				if code != "" && strings.TrimSpace(nameByCode[code]) == "" {
					nameByCode[code] = strings.TrimSpace(root.Name)
				}
			}
		} else if a.Logger != nil {
			a.Logger.Warn("查询绑定仪表盘失败", zap.String("strategy_set_id", strategySetID), zap.Error(err))
		}
	}

	nodes := make([]deviceDashboardTreeNode, 0, len(rootCodes))
	for _, code := range rootCodes {
		name := strings.TrimSpace(nameByCode[code])
		nodes = append(nodes, deviceDashboardTreeNode{
			StrategySetID:     strategySetID,
			StrategySetName:   strings.TrimSpace(set.Name),
			RootDashboardCode: code,
			RootDashboardName: name,
			DashboardCode:     code,
			DashboardName:     name,
			DashboardRole:     "root",
			IsMatched:         true,
			MatchedBy:         "binding",
			MatchReason:       "strategy_set_dashboard_binding",
		})
	}
	return nodes
}
```

- [ ] **Step 4: 切换展示路径调用**

在 `app/platform/api/metric_strategy.go` 的 `ListDeviceBoundDashboardsByTargetPart` 中,把第 747 行:

```go
		resolvedTrees := a.resolveDashboardTreesForStrategySet(ctx.Request.Context(), setID, set, matchCtx)
```

改为:

```go
		resolvedTrees := a.resolveBoundDashboardsForStrategySet(ctx.Request.Context(), setID, set)
```

若改后 `matchCtx`(第 738 行 `a.dashboardDeviceMatchContext(...)`)变为未使用导致编译错误,则一并删除第 738 行该赋值。

- [ ] **Step 5: 运行新测试确认通过**

Run: `go test ./app/platform/api/ -run TestMetricStrategyAPIListDeviceBoundDashboardsByTargetPart_MVPReturnsFlatBoundRoot -v`
Expected: PASS

- [ ] **Step 6: 跑该包全部测试,确认无回归**

Run: `go test ./app/platform/api/ -run TestMetricStrategyAPIListDeviceBoundDashboards -v`
Expected: PASS(若既有的 legacy/tree 用例因语义变更而失败,说明它们断言的是旧"树展开"行为——按 MVP 语义更新这些用例的断言:期望扁平根节点、无 children;不要改回旧实现)。

- [ ] **Step 7: 提交**

```bash
git add app/platform/api/metric_strategy.go app/platform/api/metric_strategy_device_dashboards_test.go
git commit -m "feat(metric-strategy): MVP 展示路径改为轻量绑定查询，不再物化仪表盘树"
```

---

### Task 2: 补齐缺失的种子绑定(routing-capable 交换机策略集)

**Files:**
- Create: `quick_env/docker-entrypoint-initdb.d/zzzzzzzzzzz-mvp-strategy-set-dashboard-binding-bootstrap.sql`

种子分析显示策略集 `snmp_switch_routing_capable`(由 `zzzzzzzzzz-snmp-switch-routing-capable-strategy-set-bootstrap.sql` 创建)**没有**仪表盘绑定。新增**幂等**种子,把它绑到已存在的交换机种子盘 `GDB20250418000001`(网络设备监控)。文件名多一个 `z`,确保在策略集与盘的种子之后执行。

- [ ] **Step 1: 新建幂等绑定种子文件**

写入 `quick_env/docker-entrypoint-initdb.d/zzzzzzzzzzz-mvp-strategy-set-dashboard-binding-bootstrap.sql`:

```sql
-- MVP: 给缺失绑定的种子策略集补 strategy_set ↔ dashboard 绑定（幂等）。
-- 仅新增文件，不修改既有/共享种子。文件名排序在策略集与仪表盘种子之后。
INSERT INTO `platform_teleabs_strategy_set_dashboard_binding`
  (`id`, `created_at`, `updated_at`, `deleted_at`, `strategy_set_id`, `dashboard_code`, `tenant_code`)
SELECT
  'b1d00001-0000-4000-8000-000000000001', NOW(), NOW(), NULL,
  'snmp_switch_routing_capable', 'GDB20250418000001', ''
FROM DUAL
WHERE NOT EXISTS (
  SELECT 1 FROM `platform_teleabs_strategy_set_dashboard_binding`
  WHERE `strategy_set_id` = 'snmp_switch_routing_capable'
    AND `deleted_at` IS NULL
);
```

- [ ] **Step 2: 校验 SQL 语法(本地 MySQL 容器或 mysql client dry-run)**

Run: `mysql --help >/dev/null 2>&1 && echo "mysql available" || echo "skip: 用起库验证替代"`
说明:若本地无 mysql,改在 Step 3 用 quick_env 起库验证。

- [ ] **Step 3: 起库验证 —— 监控中心选设备能出盘**

依据 `quick_env/README.md` 起一套干净库(执行全部 initdb 脚本),随后:
1. 确认绑定已落库:
   `SELECT strategy_set_id, dashboard_code FROM platform_teleabs_strategy_set_dashboard_binding WHERE strategy_set_id='snmp_switch_routing_capable';`
   Expected:返回 1 行 → `GDB20250418000001`。
2. 对一台绑定了该策略集的 SNMP 交换机调用:
   `GET /platform/metrics/strategy/device-dashboards?target_part=<设备编码>`
   Expected:`trees` 含一个 `dashboard_code=GDB20250418000001`、`matched_by=binding` 的根节点。

- [ ] **Step 4: 提交**

```bash
git add quick_env/docker-entrypoint-initdb.d/zzzzzzzzzzz-mvp-strategy-set-dashboard-binding-bootstrap.sql
git commit -m "feat(seed): 给 snmp_switch_routing_capable 策略集补仪表盘绑定（幂等）"
```

> 注:`quick_env` 在外层 meta 仓库。提交时确认当前目录的 git 仓库归属;若该路径不属于 `OneOps` 子仓库,则在其所属仓库内提交,并保持"仅新增文件"。

---

### Task 3: 整体编译与回归验证

**Files:** 无新增,仅验证。

- [ ] **Step 1: 编译整个后端**

Run: `go build ./...`
Expected: 成功,无未使用变量/导入错误(尤其确认 Task 1 Step 4 删除 `matchCtx` 后无残留引用)。

- [ ] **Step 2: 跑平台 api 与 service 包测试**

Run: `go test ./app/platform/api/... ./app/platform/service/...`
Expected: PASS。失败项若源于"旧树展开语义"用例,按 MVP 扁平语义更新断言(不回退实现)。

- [ ] **Step 3: 确认改动未越界(可改面校验)**

Run:
```bash
git -C /home/jacky/project/OneOPS-ALL/OneOps diff --name-only feature/device-v2-platform-core-optimization...snmp_metric | grep -E "metric_strategy.go|metric_strategy_device_dashboards_test.go" && echo "在可改面内"
```
Expected: 两个文件均列出 → 改动在可改面内。

- [ ] **Step 4: 标记(可选)**

如需,记录本期完成 P1+P2;P3(删生成管线 + 审计三表 + 前端收尾)留待前端收尾阶段单独立计划。

---

## 自检结论(Spec 覆盖)

- spec §4 展示发现轻量化 → Task 1 ✅
- spec §6 P2 种子绑定补齐(仅新增文件) → Task 2 ✅
- spec §5 下发不动 / 前端不动 / mode 不动 / 生成管线不删 → 本计划无相关改动 ✅
- spec §7 验收(选设备出盘、不进树物化、零回归) → Task 2 Step 3 + Task 3 ✅
- spec §2 可改面约束 → Task 3 Step 3 ✅
- P3(删除生成管线/审计表/前端) → 明确不在本计划(留最后收尾) ✅
