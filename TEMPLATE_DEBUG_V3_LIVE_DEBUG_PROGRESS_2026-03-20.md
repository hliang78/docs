# TEMPLATE DEBUG V3 联调进展（2026-03-20）

## 1. 当前目标
- 进入“边调试业务功能、边修改代码”的连续迭代阶段。
- 约束原则：不兜底、不降级、不智能推断，严格按显式数据与配置执行。

## 2. 已完成进展（Checkpoint）

### 2.1 后端（OneOps + Controller）
- 修复 `LoadV3PipelineTemplate` 的 attention overlay 覆盖问题：
  - 不再用 attention graph 覆盖 `resp.CollectParams`。
  - `collect_params` 仅使用 controller 返回结果。
- 结果：前端不再被 `sysversion` 这类 method 污染（采集 method 语义回归为 collect 语义）。

### 2.2 前端（template-debug-v3）
- 强化模板返回的 `collect_params` 严格校验：
  - `stage` 必须为 `collect`。
  - `method` 必须可识别为 `snmp/ssh/telnet` 家族。
  - `snmp` 必填 `oid`；`ssh/telnet` 必填 `command`。
  - `timeout_sec` 必须 `> 0`。
- 模板图加载改造：
  - 若 `pipeline_graph` 缺少 collect 节点，则按 `collect_params.stages` 严格补齐 collect 节点。
  - collect 节点按 `output_field -> downstream.input_fields` 精确连线。
  - collect 节点写入 `collectConfig`，默认 `useCachedDataInPreview: true`。
- 画布布局改造：
  - 有 collect 节点时，不再预留顶部空行。
  - 无 collect 节点时，保留顶部一行给伪数据节点。

## 3. 已验证结果
- `npx eslint src/views/platform/template-debug-v3/templateGraphLoader.ts` 通过。
- `npm run -s smoke:template-debug-v3` 通过。
- `npm run -s smoke:template-debug-v3-runtime` 通过（已同步 collect 节点新断言）。

## 4. 联调工作流（从现在开始执行）
- 每轮只做一个业务闭环：一个真实问题 -> 一次定点改造 -> 一次回归验证。
- 每轮固定输出 4 项：
  - 现象（接口/页面/日志）
  - 根因（精确到文件与函数）
  - 修改（改了什么，不改什么）
  - 验证（命令与结果）
- 每轮结束后，把增量写回本文件，形成连续进展日志。

## 5. 下一轮建议起点
- 以真实业务调试路径继续：
  - `加载模板图 -> 选择 target.type -> 检查 collect->下游连线与 input_fields -> 预览运行`
- 若出现异常，优先提供三类信息：
  - 前端报错文本（完整）
  - `pipeline-template/load` 响应片段（`pipeline_graph` + `collect_params`）
  - OneOps / controller 对应时段日志

## 6. 变更范围（本阶段）
- OneOps:
  - `OneOps/app/platform/service/impl/template_debug_v3_load_template.go`
- OneOPS-UI:
  - `OneOPS-UI/src/views/platform/template-debug-v3/templateGraphLoader.ts`
  - `OneOPS-UI/scripts/template-debug-v3-runtime-actions-smoke.ts`

## 7. 本轮联调记录（12:37 错误闭环）
- 现象：
  - 预览报错：`errors occurred during SNMP processing: [input field snmpIpAddrEntry is not in the expected format]`
- 根因：
  - `collect_params.method` 在模板加载后是 protocol-only（`snmp`），采集构建时缺少显式类型，导致 SNMP 结果被按单值处理，后续 `snmpprocess` 期望 `[]map[string]string` 时类型不匹配。
- 修改：
  - controller `collect_params` 增加并回传 `expected_type`（`SNMPList/SNMPSingle/Text`）。
  - collect 执行构建时优先使用 `expected_type`；`method=snmp` 且缺少 `expected_type` 直接报错，不再隐式猜测。
  - 前端模板加载与 collect_plan JSON 解析增加 `expected_type` 严格校验并透传。
  - 前端校验与后端规则对齐：仅 `method=snmp`（protocol-only）强制 `expected_type`，`snmp_xxx` 不强制。
  - collect 节点配置写入 `expected_type`，用于运行态保持一致。
  - collect 提交前增加二次硬校验（`handleCollect`），确保 `method=snmp` 且缺少/非法 `expected_type` 时前端直接拦截，不提交后端。
  - `collect_plan` 输入改为 YAML 文本（默认值/模板回填/超时更新均为 YAML），并增加 YAML 解析校验提示。
  - `initial_snapshot` 输入补充多行 placeholder（示例 + 约束 + 提示）。
- 验证：
  - `go test ./cmd/controller -run TestNonExistent` 通过。
  - `go test ./app/platform/service/impl -run TestNonExistent` 通过。
  - `npm run -s smoke:template-debug-v3` 通过。
  - `npm run -s smoke:template-debug-v3-runtime` 通过。

## 8. 本轮联调记录（collect_plan 仍显示 JSON 闭环）
- 现象：
  - 页面标题与 placeholder 已改为 YAML，但恢复页面快照后 `collect_plan` 仍显示历史 JSON 文本。
- 根因：
  - `applyPageSnapshotState` 直接回填 `state.collectPlanJSON` 原文本，没有做 YAML 规范化。
- 修改：
  - 新增 `normalizeCollectPlanYAMLText`（严格按 collect_plan 结构解析，成功后统一 `dump` 为 YAML）。
  - `snapshot restore` 时改为：先规范化，再写回 `collectPlanJSON`；无效文本不写入。
  - 这条链路不做智能推断，不做降级，不做兜底。
- 验证：
  - `npx -y eslint src/views/platform/template-debug-v3/useCollectConfig.ts src/views/platform/template-debug-v3/usePageSnapshotCodec.ts src/views/platform/template-debug-v3/usePageState.ts` 通过。
  - `npm run -s smoke:template-debug-v3` 通过。
  - `npm run -s smoke:template-debug-v3-runtime` 通过。

## 9. 本轮联调记录（采集工作台弹窗化 + 单条采集）
- 现象：
  - 顶部 `collect_plan` 内容过长，编辑与结果查看挤占画布空间。
  - 需要在一个独立弹窗内同时完成：编辑采集配置、整体采集、单条采集、结果查看。
- 设计与约束：
  - 保持现有后端接口不变：仍使用 `POST /template-debug-v3/sessions/:sessionID/collect`。
  - 单条采集采用“提交单 stage collect_plan”实现，不做降级、不做兜底、不做智能推断。
  - 结果展示与采集入口合并在同一工作台，避免双入口重复。
- 修改：
  - 新增独立组件：`CollectWorkbenchModal.vue`（配置编辑 + stage 列表 + 单条采集按钮 + 结果视图）。
  - 主页面移除旧的采集结果 drawer 入口，改为统一“采集工作台”入口。
  - 采集逻辑新增 `handleCollectSingleStage(stageIndex)`，并抽象公共执行函数，整体采集与单条采集共享同一请求链路。
  - `collect_plan` 顶部区域改为摘要卡，详细编辑迁移至弹窗。
- 验证：
  - `npx -y eslint src/views/platform/TemplateDebugPipelineEditorV3.vue src/views/platform/template-debug-v3/CollectWorkbenchModal.vue src/views/platform/template-debug-v3/usePageState.ts src/views/platform/template-debug-v3/useDebugRuntimeActions.ts` 通过。
  - `npm run -s smoke:template-debug-v3` 通过。
  - `npm run -s smoke:template-debug-v3-runtime` 通过。

## 10. 本轮联调记录（去冗余：移除旧 collect drawer 链路）
- 目标：
  - 保留“采集工作台”单一路径，删除旧 drawer 状态与动作透传，降低维护复杂度。
- 修改：
  - 移除 `collectDrawerOpen / collectDrawerActiveKeys / handleOpenCollectDrawer` 相关状态与函数。
  - `usePageSnapshotCodec` 不再编码/恢复上述旧字段。
  - `useRuntimeDebugActionsFacade` 与 `useDebugRuntimeActions` 移除旧 drawer 透传参数。
  - `usePageState` 清理旧字段与旧 action 暴露，仅保留采集工作台逻辑。
  - 修正采集工作台中端口输入行为：仅 `timeout_sec` 变更触发 `handleTimeoutSecChange`，端口变更不再误触发。
- 结果：
  - 采集入口、执行、结果展示统一到 `CollectWorkbenchModal.vue`，无双轨逻辑。
- 验证：
  - `npx -y eslint src/views/platform/template-debug-v3/useDebugRuntimeActions.ts src/views/platform/template-debug-v3/useRuntimeDebugActionsFacade.ts src/views/platform/template-debug-v3/usePageSnapshotCodec.ts src/views/platform/template-debug-v3/usePageState.ts src/views/platform/TemplateDebugPipelineEditorV3.vue src/views/platform/template-debug-v3/CollectWorkbenchModal.vue` 通过。
  - `npm run -s smoke:template-debug-v3` 通过。
  - `npm run -s smoke:template-debug-v3-runtime` 通过。

## 11. 本轮联调记录（单条采集结果聚焦 + 采集中锁定编辑）
- 目标：
  - 单条采集后在工作台明确显示执行范围，并高亮对应 stage，提升定位效率。
  - 采集请求进行中锁定配置编辑，避免请求中途改参导致结果语义不一致。
- 修改：
  - 新增执行范围状态：`collectExecutionMode`（`all/single`）与 `collectExecutionStageIndex`。
  - `handleCollect` / `handleCollectSingleStage` 在提交前写入执行范围状态，并在创建新 session 时重置。
  - 工作台新增 `scope` 展示（顶部 tag + 结果卡），单条采集时 stage 表高亮命中行。
  - 采集中禁改：credential、端口、timeout、collect_plan YAML 全部 `disabled`。
  - 采集中禁关闭工作台（禁用右上角关闭与 ESC）。
- 结果：
  - 单条采集完成后，可直观看到“当前结果对应哪个 stage”。
  - 采集进行中不会出现配置漂移。
- 验证：
  - `npx -y eslint src/views/platform/template-debug-v3/usePageState.ts src/views/platform/template-debug-v3/useRuntimeDebugActionsFacade.ts src/views/platform/template-debug-v3/useDebugRuntimeActions.ts src/views/platform/template-debug-v3/CollectWorkbenchModal.vue src/views/platform/TemplateDebugPipelineEditorV3.vue` 通过。
  - `npm run -s smoke:template-debug-v3` 通过。
  - `npm run -s smoke:template-debug-v3-runtime` 通过。

## 12. 本轮联调记录（调试结果输出：采集导入严格化 + 模板导出对齐）
- 目标：
  - 采集数据支持“下载 -> 导入 -> 继续调试”闭环，且导入格式必须严格受控。
  - 画布调试完成后，导出 templates YAML 包，主入口格式对齐 controller 约定。
- 修改：
  - 采集导入：
    - 新增严格解析器 `collectImportCodec.ts`，仅接受系统导出的固定 JSON 键集合（缺键/多键都报错）。
    - 工作台新增“导入采集 JSON”入口；导入后回填 `collectResult/snapshot_id/keyword` 并复位执行范围状态。
  - 模板导出：
    - 导出来源固定为“当前画布节点 + 当前连线 + 当前节点配置”。
    - 导出包改为多 YAML：
      - 主入口：`config.yaml`（`pipeline + stage config + $include`）。
      - 兼容文件：`config.pipeline.generated.yaml`（内容与主入口一致，保留历史工具链兼容）。
      - stage 文件：`alive|collect|parse|textfsm|snmp|transform|join|derive` 的 `*/base/*.yaml`。
    - 导出 zip 根路径：`{vendor}/{platform}/...`（沿用现有导出结构）。
- 验证：
  - `npx eslint src/views/platform/template-debug-v3/templatePackageExporter.ts src/views/platform/template-debug-v3/useDebugRuntimeActions.ts` 通过。
  - `npm run -s smoke:template-debug-v3` 通过。
  - `npm run -s smoke:template-debug-v3-runtime` 通过。
