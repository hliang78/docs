# OneOPS RCA 机制说明

本文已压缩为归档入口，不再维护旧版长篇机制说明。

原因：

- 当前 RCA 主路径已经收敛到 `LayeredObservationV2 + AnalyzeLayeredObservationV2`。
- 旧文档依赖的大量阶段划分、补充说明、场景母稿已经和现代码边界脱节。
- 继续保留大篇幅机制解释，只会把后续精简工作重新拉回已经删除的心智模型。

当前只保留下面几份文档作为有效入口：

- [RCA_PLATFORM_AGNOSTIC_MINIMAL_CONTRACT.md](/home/jacky/project/OneOPS-ALL/docs/RCA_PLATFORM_AGNOSTIC_MINIMAL_CONTRACT.md)
- [MONITORING_RCA_SEMANTICS_CONTRACT_20260401.md](/home/jacky/project/OneOPS-ALL/OneOps/docs/MONITORING_RCA_SEMANTICS_CONTRACT_20260401.md)
- [MONITORING_RCA_CORE_GAP_ANALYSIS_20260401.md](/home/jacky/project/OneOPS-ALL/OneOps/docs/MONITORING_RCA_CORE_GAP_ANALYSIS_20260401.md)
- [MONITORING_RCA_REFACTOR_TASKLIST_20260401.md](/home/jacky/project/OneOPS-ALL/OneOps/docs/MONITORING_RCA_REFACTOR_TASKLIST_20260401.md)

当前代码入口：

- `OneOps/pkg/rca/layered_contract_v2.go`
- `OneOps/pkg/rca/layered_engine_v2.go`
- `OneOps/pkg/rca/layered_projection_v2.go`
- `OneOps/app/platform/rootcause/application/observation_builder.go`
- `OneOps/app/platform/rootcause/application/analysis_session.go`
- `OneOps/app/platform/service/impl/monitoring_root_cause_layered_analyze_session.go`
