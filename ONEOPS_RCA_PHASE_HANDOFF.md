# OneOPS RCA 阶段交接单

本文档只用于阶段交接。

不重新解释机制。
不重新展开设计。
不追加新能力。

---

## 1. 当前阶段结论

当前阶段已经完成的事只有这些：

1. `pkg/rca` 平台无关机制已抽离
2. OneOps 只保留入口归一化、字段映射、日志证据挂载
3. 平台无关夹具已落地
4. OneOps 侧伪集成夹具已落地
5. API 入口回归已落地
6. 监控地图最小读取已落地
7. 监控地图关系已接入 layered RCA
8. 监控地图 readiness 已接入 layered RCA 拒判原因
9. 基线脚本已可一键执行并通过

当前还应固定一条机制结论：

- 真实网络中，多路径通常是常态，不是例外
- 因此当前主线不以树形拓扑、唯一路径为默认前提
- 多路径歧义时，宁可不输出桥接候选，也不伪造唯一桥接根因
- 上述多路径判定适用于任意两台失败设备之间，不要求整张图是树
- 若多条最短路径存在公共桥接边/点，允许输出这部分确定性候选

当前再补一条适配结论：

- `application_hosted_on_server` 已自动映射为 layered `hosting`
- `application_depends_on_application` 已自动映射为 layered `dependency`
- 若监控地图已返回目标 readiness 项，但缺少监控任务、层级关系或 active path 事实，RCA 当前直接返回 `unable_to_conclude_yet`
- 没有 readiness 项时，不伪造这类缺失事实

当前阶段明确不再继续：

- 真实数据执行
- 新的 RCA 能力开发
- 机制扩展设计

当前补充一条展示边界：

- 若后续启动动画展示，只能把它视为 RCA 结果播放层，不视为机制扩展

当前再补一条场景边界：

- 后续文档与动画，不再沿用“同质节点 + 最短路径 + 直接看边状态”的简化口径
- 已统一切换为“监控源点出发、基于实际转发路径、对网络/服务器/应用分层排除”的场景理解

---

## 1.1 已核对一致的场景口径

当前已经核对一致，后续若继续，只按以下口径推进：

1. 节点不是同质的，至少分为网络设备、服务器、应用
2. 拓扑不只包含网络连接，还包含服务器承载关系、应用依赖关系、应用到应用依赖关系
3. 监控从某个监控器部署点发起，不是全图无源观测
4. 边不能被直接监控
5. 边状态只能结合节点接口状态与“该边是否命中实际监控路径”来推断
6. 路径不是默认最短路径；复杂环境下应以二层、三层转发表推导出的实际转发路径为准
7. 定位顺序固定为：
   - 先看实际路径是否阻断
   - 再看服务器是否异常
   - 再看上游应用依赖是否异常
   - 最后才收敛到当前应用自身异常
8. 后续可扩展分布式监控源点，但当前阶段只保留这个边界，不进入实现

这一口径当前只用于：

- 文档边界统一
- demo 动画重构

当前不意味着：

- `pkg/rca` 立即扩机制
- 真实 OneOps 数据已经接入
- 当前阶段重新打开主线开发

---

## 2. 当前统一执行入口

统一执行入口固定为：

```bash
bash /home/jacky/project/OneOPS-ALL/OneOps/scripts/run_rca_fixture_checks.sh
```

它会依次执行：

1. `pkg/rca` 平台无关机制夹具
2. `app/platform/service/impl` OneOps 侧伪集成夹具
3. `app/platform/api` 与 `app/alert/api` 入口回归

若其中任一步失败，先修基线，不进入下一动作。

这里补一条执行边界：

- 不用 `go test ./app/platform/service/impl` 全量包结果替代 RCA 基线结果
- 原因是该包内还包含大量与 RCA 无关的测试，可能出现独立失败
- RCA 当前阶段只以 `run_rca_fixture_checks.sh` 的结果作为主线验收结论

---

## 3. 当前主要文档

当前只保留以下文档作为有效边界：

1. [ONEOPS_DOWHY_AND_TOPOLOGY_ROOT_CAUSE_ANALYSIS.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_DOWHY_AND_TOPOLOGY_ROOT_CAUSE_ANALYSIS.md)
2. [RCA_PLATFORM_AGNOSTIC_MINIMAL_CONTRACT.md](/home/jacky/project/OneOPS-ALL/docs/RCA_PLATFORM_AGNOSTIC_MINIMAL_CONTRACT.md)
3. [ONEOPS_RCA_ADAPTER_MAPPING.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_RCA_ADAPTER_MAPPING.md)
4. [ONEOPS_ROOT_CAUSE_TEST_DATASET.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_ROOT_CAUSE_TEST_DATASET.md)
5. [ONEOPS_RCA_REAL_ACCEPTANCE_TEMPLATE.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_RCA_REAL_ACCEPTANCE_TEMPLATE.md)
6. [ONEOPS_RCA_NEXT_STAGE_BOUNDARY.md](/home/jacky/project/OneOPS-ALL/docs/ONEOPS_RCA_NEXT_STAGE_BOUNDARY.md)

这六份之外，不再新增主线说明文档。

---

## 4. 当前代码边界

当前代码边界固定为：

1. `OneOps/pkg/rca` 承担机制本体
2. `OneOps/app/platform/service/impl/monitoring_root_cause_adapter.go` 承担字段映射
3. `OneOps/app/platform/service/impl/monitoring_root_cause_service.go` 承担适配流程
4. `OneOps/app/platform/api/monitoring_root_cause_adapter.go` 承担 platform 入口归一化
5. `OneOps/app/alert/api/alert_alarm_root_cause_adapter.go` 承担 alert 入口归一化

当前不再调整这些边界。

### 当前代码与夹具定位

关键代码文件：

1. `OneOps/pkg/rca/contract.go`
2. `OneOps/pkg/rca/analyzer.go`
3. `OneOps/pkg/rca/layered_contract.go`
4. `OneOps/pkg/rca/layered_analyzer.go`
5. `OneOps/app/platform/service/impl/monitoring_map_reader.go`
6. `OneOps/app/platform/service/impl/monitoring_map_relation_source.go`
7. `OneOps/app/platform/service/impl/monitoring_root_cause_service.go`
8. `OneOps/app/platform/service/impl/monitoring_root_cause_adapter.go`
9. `OneOps/app/platform/api/monitoring_root_cause.go`
10. `OneOps/app/platform/api/monitoring_root_cause_adapter.go`
11. `OneOps/app/alert/api/alert_alarm.go`
12. `OneOps/app/alert/api/alert_alarm_root_cause_adapter.go`

当前展示层最小 demo 落点：

1. `OneOps/static/rca-demo/index.html`
2. `OneOps/static/rca-demo/fixtures.js`
3. `OneOps/static/rca-demo/app.js`

这里补一条状态说明：

- 当前 demo 只承担“统一场景理解回放”
- 当前 demo 不再要求严格复刻旧版 `pkg/rca` 最短路径夹具语义
- 当前 demo 的目标是把监控源、实际路径、边状态推断、分层排除过程讲清楚

当前 demo 打开方式固定为：

1. 直接打开 `OneOps/static/rca-demo/index.html`
2. 若 OneOps 服务已启动，访问 `/static/rca-demo/index.html`

关键夹具文件：

1. `OneOps/pkg/rca/testdata/direct_failed_edge.json`
2. `OneOps/pkg/rca/testdata/unique_bridge.json`
3. `OneOps/pkg/rca/testdata/ambiguous_shortest_path.json`
4. `OneOps/pkg/rca/testdata/multi_path_common_bridge.json`
5. `OneOps/pkg/rca/testdata/invalid_topology_contract.json`
6. `OneOps/pkg/rca/testdata/layered/layered_path_edge_root_cause.json`
7. `OneOps/pkg/rca/testdata/layered/layered_server_root_cause.json`
8. `OneOps/pkg/rca/testdata/layered/layered_application_dependency_root_cause.json`
9. `OneOps/pkg/rca/testdata/layered/layered_application_self_root_cause.json`
10. `OneOps/pkg/rca/testdata/layered/layered_unable_to_conclude_yet.json`
11. `OneOps/app/platform/service/impl/testdata/analyze_alerts_success_with_log.json`
12. `OneOps/app/platform/service/impl/testdata/analyze_alerts_ambiguous_path.json`
13. `OneOps/app/platform/service/impl/testdata/analyze_alerts_multi_path_common_bridge.json`
14. `OneOps/app/platform/service/impl/testdata/analyze_alerts_invalid_topology.json`
15. `OneOps/app/platform/service/impl/testdata/analyze_alerts_layered_path_edge_root_cause.json`
16. `OneOps/app/platform/service/impl/testdata/analyze_alerts_layered_server_root_cause.json`
17. `OneOps/app/platform/service/impl/testdata/analyze_alerts_layered_application_dependency_root_cause.json`
18. `OneOps/app/platform/service/impl/testdata/analyze_alerts_layered_readiness_incomplete.json`

统一执行脚本：

1. `OneOps/scripts/run_rca_fixture_checks.sh`

---

## 5. 若后续继续，只允许两种动作

后续若继续，只允许以下两种动作：

1. 修复基线失败
2. 在真实数据窗口开启后，按模板做真实验收记录

除此之外，不进入新开发。

若当前只是进入下一阶段维护，则执行顺序固定为：

1. 运行 `OneOps/scripts/run_rca_fixture_checks.sh`
2. 若失败，修基线
3. 若通过，停止开发动作

---

## 6. 未来重启条件

只有同时满足以下条件，才允许重启下一轮工作：

1. 业务确认可以开始真实数据验收
2. 基线脚本仍然通过
3. 真实验收模板已确认沿用

满足后，再进入：

1. 真实租户验收
2. 真实告警验收
3. 真实日志证据验收
4. 真实阻塞点记录
