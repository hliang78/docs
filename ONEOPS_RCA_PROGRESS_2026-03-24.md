# OneOPS RCA 当前进度快照 2026-03-24

本文档只记录当前已经完成的主线进度，供后续继续开发时快速接手。

不回滚旧结论。
不重写背景设计。
不替代正式方案文档。

---

## 1. 当前主线已经完成的能力

### 1.1 平台无关 RCA 机制

已完成：

1. `pkg/rca` 平台无关连通性分析
2. `pkg/rca` 分层 RCA 机制
3. 分层结论固定为：
   - `path_edge_root_cause`
   - `server_root_cause`
   - `application_dependency_root_cause`
   - `application_self_root_cause`
   - `unable_to_conclude_yet`
4. 多路径下不强行伪造唯一桥接候选
5. 唯一最短路径辅助能力已抽出，可供适配层复用

### 1.2 OneOps 适配层

已完成：

1. `monitoring_root_cause_service` 已接入平台无关 RCA
2. `monitoring_root_cause_adapter` 已完成字段映射
3. `platform/api` 与 `alert/api` 两个入口已接通 RCA
4. `AnalyzeAlerts` 与 `AnalyzeConnectivity` 两条主链都可执行

### 1.3 分层输入自动归一化

已完成：

1. `node_observations` 已可从 Prometheus 读取
2. 当前使用指标：`ping_result_code`
3. 当前使用标签：`device_code`
4. 当前状态映射：
   - `0 -> up`
   - 非 `0 -> down`
5. 当前只自动回填 `server` 与 `network` 两类节点观测

### 1.4 monitor node 自动补齐

已完成：

1. 已支持从 `monitoring_map.sources[0]` 反查 `monitor_node_id`
2. 当前依赖 `platform_agent -> device` 映射
3. 兼容历史 `platform_agent.device_id` 既可能是 `device.id`，也可能直接是 `device.code`
4. 当前仅在“单一监控源”场景下自动补齐

### 1.5 monitoring map 最小事实视图

已完成：

1. `sources`
2. `tasks`
3. `targets`
4. `relations`
5. `readiness`
6. `observed_paths`

其中：

1. `relations` 已支持：
   - `application_hosted_on_server`
   - `application_depends_on_application`
   - `server_attached_to_network`
   - `network_connected_to_network`
2. `readiness` 已接入：
   - `HasMonitorSource`
   - `HasMonitorTask`
   - `HasTopologyRelation`
   - `HasNodeObservation`
   - `HasActivePath`
   - `HasBlockedPathOrLogEvidence`

当前已明确的职责边界：

1. 控制面事实
   - 当前优先来源仍是：
   - `wizard_plan`
   - `strategy_apply_record`
2. 控制面事实当前主要负责：
   - `sources`
   - `tasks`
   - `targets`
   - `readiness.HasMonitorSource`
   - `readiness.HasMonitorTask`
3. 观测面事实
   - 当前优先来源是 Prometheus 指标与标签
4. 观测面事实当前主要负责：
   - `node_observations`
5. 路径事实
   - 当前优先来源是真实路径证据
   - 例如 `observed_paths`
6. 不采用的简化方式：
   - 不以 Prometheus 标签单独替代控制面 coverage 基线
   - 原因是“没有指标”不等于“没有任务 / 没有目标 / 没有监控源”

### 1.6 observed_paths 主线

已完成：

1. `observed_paths` 已成为正式主线通道
2. `MonitoringRootCauseObservationNormalizer` 会优先消费 `observed_paths`
3. 当前真实来源已接入一类：
   - `L2NodeMap + Arp` 的“服务器唯一挂接交换机直连接入边”
4. `MonitoringMapReader` 已支持 observed path source 组合器
5. 已增加未来扩展位：
   - `L2ForwardingMonitoringMapObservedPathSource`
   - `L3ForwardingMonitoringMapObservedPathSource`

当前这两个 forwarding source 只定义输入契约，不产出真实数据。

### 1.7 场景构造主线骨架

已完成：

1. 场景 JSON 最小契约已落文档
2. 已新增最小场景结构与校验代码
3. 已支持：
   - `scenario -> MonitoringMapReadResp`
   - `scenario -> MonitoringRootCauseLayeredAnalyzeInput`
   - `scenario -> rca.LayeredObservation`
4. 已支持最小 Prometheus 样本发生器
5. 当前只生成主线已消费的指标：
   - `ping_result_code`
6. 已落成前期标准场景夹具：
   - `path_edge_root_cause`
   - `server_root_cause`
   - `application_dependency_root_cause`
   - `application_self_root_cause`
   - `unable_to_conclude_yet`
7. 已落成中期第一版多路径场景夹具：
   - `multi_path_common_blocked_edge`
   - `multi_path_healthy_unable_to_conclude`
8. 场景 JSON 当前按严格模式装载，未知字段直接报错
9. 已固定“未来路径组语义”只作为预留边界，当前不启用字段
10. 已新增最小场景编辑器静态页：
   - `OneOps/static/rca-scenario/index.html`
11. 已新增场景夹具同步脚本：
   - `OneOps/scripts/sync_rca_scenario_fixtures.sh`
12. 场景编辑器当前优先读取：
   - `OneOps/static/rca-scenario/fixtures/index.json`
13. 场景编辑器已支持 Prometheus 样本预览
14. 场景编辑器导出文件名已按 `scenario_id` 规范化
15. 场景编辑器已支持 Monitoring Map 事实预览
16. 场景编辑器已支持 Layered Input 预览
17. 场景编辑器已支持一轮 RCA 摘要预览
18. 场景编辑器已支持最小快速编辑动作：
   - 新增节点
   - 新增关系边
   - 新增目标绑定
   - 写入节点观测
   - 追加路径事实
19. 当前快速编辑器只支持增量写入，不支持页面内删除：
   - 删除仍通过直接编辑 JSON 完成
20. 场景编辑器已支持从空白骨架初始化场景
21. 场景编辑器已支持回写基础字段：
   - `scenario_id`
   - `scenario_name`
   - `tenant_code`
   - `observed_at`
   - `monitor_source`
   - `expected_rca.target_id`
   - `expected_rca.conclusion`
22. 场景编辑器已支持最小删除动作：
   - 删除节点
   - 删除关系边
   - 删除目标绑定
   - 删除节点观测
   - 删除路径事实
23. 删除动作当前只做必要直接引用清理：
   - 删除 forwarding 边时同步清理 path facts
   - 删除节点/目标时同步清理直接挂接观测与路径
24. 已新增场景导入脚本：
   - `OneOps/scripts/import_rca_scenario_fixture.sh`
25. 当前页面化数据入库主线已固定为：
   - 页面导出 JSON
   - 脚本导入到 `testdata/scenarios`
   - 脚本自动同步到 `static/rca-scenario/fixtures`
26. 已新增一键导入并校验脚本：
   - `OneOps/scripts/import_and_check_rca_scenario_fixture.sh`
27. 当前页面化新增夹具的最短闭环已固定为：
   - 导出 JSON
   - 执行一键导入并校验脚本
   - 进入 `TestMonitoringRootCauseScenario(Fixtures)?`
28. 场景编辑器已支持五类固定模板按钮：
   - 路径阻断
   - 服务器异常
   - 依赖应用异常
   - 应用自身异常
   - 无法继续收敛
29. 当前模板按钮只生成最小可编辑骨架，不做参数化模板系统
30. 场景编辑器页面内已补最短闭环说明：
   - 模板/初始化
   - 编辑事实
   - 预览结果
   - 导出并执行一键导入校验脚本
31. 已完成一轮真实脚本链路验证：
   - `import_and_check_rca_scenario_fixture.sh` 已实际执行通过
   - 后续已清理验证过程中产生的重复 fixture
32. `sync_rca_scenario_fixtures.sh` 已补陈旧静态 fixture 清理：
   - 删除源夹具后，静态目录不再残留旧副本
33. 场景编辑器页面内已补步骤编号标记：
   - 步骤 1 模板/初始化
   - 步骤 2 基础字段
   - 步骤 3 节点/边/目标
   - 步骤 4 节点观测
   - 步骤 5 路径事实
   - 删除动作单列为可选修正
34. 场景编辑器页面内已补概念关系说明：
   - `monitor_source`
   - `target_bindings`
   - `observed_paths`
   - `expected_rca.target_id`
   - `RCA result candidates`
35. 页面与契约文档已固定路径事实边界：
   - 没有真实路径证据时，不得仅凭拓扑边写入 `active_path_edges`
   - `blocked_path_edges` 不得脱离已知 `active_path_edges` 单独出现
36. `path_edge_root_cause` 类模板当前应理解为：
   - 已拿到预解析路径事实的机制层模板
   - 不是当前平台“采集即所得”的自然模板

### 1.8 topology fallback 当前边界

已完成但边界严格受控：

1. 本地监控点场景可直接通过
2. 直接单跳可回填 `active_path_edges`
3. 唯一最短多跳路径可回填 `active_path_edges`

当前明确不做：

1. 把 topology fallback 当作真实转发路径
2. 在多路径场景下强行回填 active path
3. 基于 topology fallback 推导 blocked path

---

## 2. 当前一致的机制顺序

当前执行顺序已经固定：

1. 真实 `observed_paths` 优先
2. 若无真实路径事实，才允许受控 topology fallback
3. 若路径事实仍不足，则返回 `unable_to_conclude_yet`
4. 不再伪造“应该有路径”

当前分层判定顺序固定为：

1. 先看实际路径是否阻断
2. 再看承载服务器是否异常
3. 再看依赖应用是否异常
4. 最后才判断当前应用自身异常

---

## 3. 当前关键代码文件

### 3.1 平台无关机制

1. `OneOps/pkg/rca/analyzer.go`
2. `OneOps/pkg/rca/analyzer_test.go`
3. `OneOps/pkg/rca/layered_analyzer.go`
4. `OneOps/pkg/rca/layered_contract.go`

### 3.2 OneOps 适配主链

1. `OneOps/app/platform/service/impl/monitoring_root_cause_service.go`
2. `OneOps/app/platform/service/impl/monitoring_root_cause_service_test.go`
3. `OneOps/app/platform/service/impl/monitoring_root_cause_adapter.go`
4. `OneOps/app/platform/service/impl/monitoring_root_cause_observation_normalizer.go`
5. `OneOps/app/platform/service/impl/monitoring_root_cause_observation_normalizer_test.go`
6. `OneOps/app/platform/service/impl/monitoring_root_cause_node_observation_source.go`
7. `OneOps/app/platform/service/impl/monitoring_root_cause_node_observation_source_test.go`
8. `OneOps/app/platform/service/impl/monitoring_root_cause_monitor_node_resolver.go`

### 3.3 monitoring map 主线

1. `OneOps/app/platform/dto/monitoring_map.go`
2. `OneOps/app/platform/service/impl/monitoring_map_reader.go`
3. `OneOps/app/platform/service/impl/monitoring_map_reader_test.go`
4. `OneOps/app/platform/service/impl/monitoring_map_relation_source.go`
5. `OneOps/app/platform/service/impl/monitoring_map_observed_path_source.go`
6. `OneOps/app/platform/service/impl/monitoring_map_observed_path_source_test.go`

### 3.4 场景构造主线

1. `OneOps/app/platform/service/impl/monitoring_root_cause_scenario.go`
2. `OneOps/app/platform/service/impl/monitoring_root_cause_scenario_test.go`
3. `OneOps/app/platform/service/impl/monitoring_root_cause_scenario_fixture_test.go`
4. `OneOps/app/platform/service/impl/testdata/scenarios/server_root_cause_minimal.json`
5. `OneOps/app/platform/service/impl/testdata/scenarios/path_edge_root_cause_minimal.json`
6. `OneOps/app/platform/service/impl/testdata/scenarios/application_dependency_root_cause_minimal.json`
7. `OneOps/app/platform/service/impl/testdata/scenarios/application_self_root_cause_minimal.json`
8. `OneOps/app/platform/service/impl/testdata/scenarios/unable_to_conclude_minimal.json`
9. `OneOps/app/platform/service/impl/testdata/scenarios/multi_path_common_blocked_edge.json`
10. `OneOps/app/platform/service/impl/testdata/scenarios/multi_path_healthy_unable_to_conclude.json`

### 3.5 最小场景编辑器

1. `OneOps/static/rca-scenario/index.html`
2. `OneOps/static/rca-scenario/fixtures.js`
3. `OneOps/static/rca-scenario/app.js`
4. `OneOps/static/rca-scenario/fixtures/index.json`
5. `OneOps/scripts/sync_rca_scenario_fixtures.sh`
6. `OneOps/scripts/import_rca_scenario_fixture.sh`
7. `OneOps/scripts/import_and_check_rca_scenario_fixture.sh`

### 3.6 当前真实路径数据相关代码边界

1. `OneOps/app/analysis_l2/service/impl/analysis_l2.go`
2. `OneOps/app/analysis_l2/service/adapter/newArpTableServerV2.go`
3. `OneOps/app/nodemap/phy_node_map/service/i_phy_node_map.go`
4. `OneOps/app/nodemap/phy_node_map/service/impl/phy_node_map.go`
5. `OneOps/app/topology/service/impl/topology.go`

---

## 4. 当前已经验证通过的测试

当前至少已反复通过：

1. `GOCACHE=/tmp/go-build go test ./app/platform/service/impl -run 'Test(MonitoringMapReader|MonitoringRootCauseObservationNormalizer|MonitoringRootCause)'`
2. `GOCACHE=/tmp/go-build go test ./app/platform/service/impl -run 'Test(CompositeMonitoringMapObservedPathSource|L2ForwardingMonitoringMapObservedPathSource|L3ForwardingMonitoringMapObservedPathSource|L2ArpMonitoringMapObservedPathSource|MonitoringMapReader|MonitoringRootCause)'`
3. `GOCACHE=/tmp/go-build go test ./app/platform/api ./app/alert/api -run 'Test(MonitoringRootCauseAPIAnalyzeAlerts|AlertAlarmAPIAnalyzeRootCause)'`
4. `bash /home/jacky/project/OneOPS-ALL/OneOps/scripts/run_rca_fixture_checks.sh`
5. `GOCACHE=/tmp/go-build go test ./app/platform/service/impl -run 'TestMonitoringRootCauseScenarioFixtures|TestMonitoringRootCauseScenario'`
6. `node --check OneOps/static/rca-scenario/app.js`
7. `node --check OneOps/static/rca-scenario/fixtures.js`
8. `bash OneOps/scripts/sync_rca_scenario_fixtures.sh`
9. `bash -n OneOps/scripts/import_rca_scenario_fixture.sh`
10. `bash -n OneOps/scripts/import_and_check_rca_scenario_fixture.sh`
11. `GOCACHE=/tmp/go-build go test -run 'TestMonitoringRootCauseScenario(Fixtures)?' -v ./app/platform/service/impl`

---

## 5. 当前明确的边界

### 5.1 已完成但不能误解的部分

1. `observed_paths` 通道已经建立
2. 当前只有一类真实 observed path source 真正产出数据
3. forwarding source 只是占位，不代表已经接入 L2/L3 真实路径

### 5.2 当前仍未完成的部分

1. 二层 forwarding 真实路径 reader
2. 三层 forwarding 真实路径 reader
3. 多跳真实转发路径推导
4. 多路径真实转发路径推导
5. blocked path 的真实来源接入
6. 面向测试/演示的数据构造器与可视化配置页面
7. 场景到真实 Prometheus 服务的联通
8. 监控控制面真正幂等实现

### 5.3 当前新增的重要风险与前置项

1. 当前监控控制面仍存在严重幂等性问题
2. 在控制面没有真正实现幂等前：
   - `wizard_plan`
   - `strategy_apply_record`
   - 以及由它们推导出的 coverage 事实
   都不能被视为绝对稳定基线
3. 这会直接影响：
   - `sources / tasks / targets` 的可信度
   - `readiness.HasMonitorSource / HasMonitorTask` 的可信度
4. 因此，后续若要把 monitoring map 作为 RCA 正式事实底座，监控控制面的幂等实现是前置项，不是可选优化
8. 页面化场景编辑器

---

## 6. 后续开发最自然的接续点

后续继续开发时，建议按这个顺序推进：

1. 先补测试/演示数据构造体系
2. 再补页面化拓扑与设备配置能力
3. 再补 Prometheus 指标发生器
4. 再让这些构造数据直接喂给 RCA 前期与中期测试
5. 在此之后，再接真实 forwarding reader

原因很简单：

1. 当前 RCA 主线已经有稳定入口
2. 缺的是持续可控的数据输入，不是下一层机制抽象
3. 没有前期/中期可控测试数据，后续 forwarding 接入会很难验证

---

## 7. 当前快照结论

一句话总结当前状态：

当前 RCA 主线已经从“纯机制 + 夹具”推进到“真实 observed_paths 通道已建立、OneOps 最小真实路径来源已接入、场景构造骨架与最小指标发生器已经落地、未来 forwarding 接入口已固定”的阶段。

下一阶段最优先的工作，不是继续扩机制，而是建设一套可视化、可构造、可驱动 Prometheus 和拓扑/标签事实的数据测试体系。
