# AI 交接文档（Template Debug V3 - Stage 拆分与扩展）

更新时间：2026-03-19（含 target.type 单组调试对齐）  
适用范围：`OneOPS-UI`（`template-debug-v3`）

## 1. 本轮目标与结果

本轮按“先交界、再拆分、再扩展”推进，已完成：

1. 新增 stage 注册中心：`stageRegistry.ts`，把 stage 元信息/默认配置/判断 helper 收敛到单一入口。  
2. `stageTypeOptions` 与节点默认配置改为从 registry 派生，降低新增 stage 时的改动面。  
3. 关键流程中的硬编码 `stage_type === 'xxx'` 已替换为 registry helper，避免后续 stage 扩展时遗漏。

### 1.1 2026-03-19 增量对齐（跨栈优先级）

1. `Attentions` 内按 `target.type` 存在多组 pipeline，调试入口需改为“单组选择 + 单组加载”。
2. UI 的 stage 扩展工作需与 `target_type` 请求/响应契约同步推进，避免在混合 graph 基线上继续叠加复杂度。
3. 先完成 `target.type` 下拉与单组重载，再继续新增 stage 的 inspector 细节。
4. 统一方案文档：`docs/TEMPLATE_DEBUG_V3_TARGET_TYPE_SINGLE_PIPELINE_PLAN_2026-03-19.md`。

---

## 2. 本轮已落地代码（可作为下一会话基线）

新增文件：
- `OneOPS-UI/src/views/platform/template-debug-v3/stageRegistry.ts`
- `OneOPS-UI/src/views/platform/template-debug-v3/usePageSnapshotState.ts`
- `OneOPS-UI/src/views/platform/template-debug-v3/usePreviewGraphBuilder.ts`
- `OneOPS-UI/src/views/platform/template-debug-v3/useInspectorPanelState.ts`

核心能力：
- Stage 常量：`STAGE_TYPE_*`（`dataref/alivecheck/collect/parse/textfsm/snmpprocess/transform/derive/join`）
- 元信息中心：`StageDescriptor`
- 统一输出：`stageTypeOptions`
- 统一默认配置：`getStageDefaultConfig(stageType)`
- 统一判断：`normalizeStageType/isDataRefStage/isSnmpProcessStage/isTransformStage`

已接入文件：
- `constants.ts`：`stageTypeOptions` 改为 re-export registry 结果
- `stageNodeDefaults.ts`：`createDefaultNodeConfig` 改为使用 registry
- `useCanvasInteraction.ts`：新增节点时使用 `normalizeStageType + STAGE_TYPE_TRANSFORM`
- `useNodeEditorActions.ts`：节点应用逻辑改用 `isDataRefStage/isSnmpProcessStage/isTransformStage`
- `usePageState.ts`：默认 stage 与关键 watcher 判断改为 stage helper
- `stageGraph.ts` / `useStageIOTypeTracker.ts`：统一 `normalizeStageType` 来源
- `useSnmpProcessInspector.ts` / `useTransformInspector.ts` / `useTransformDebugState.ts` / `previewPayload.ts`：关键 stage 判断改为 helper
- `usePageState.ts`：页面快照、payload 构建、节点检查器状态改为调用独立 composable

---

## 3. 当前“大文件拆分”现状与建议

当前主要体量：
- `TemplateDebugPipelineEditorV3.vue`：1328 行
- `usePageState.ts`：1297 行
- `useTransformInspector.ts`：773 行
- `useTransformDebugState.ts`：639 行

建议拆分顺序（低风险到高收益）：

1. 先拆 `usePageState.ts`（优先）
- 拆成：
  - `usePageSnapshotState.ts`（快照保存/恢复/自动保存）
  - `useInspectorPanelState.ts`（选中节点编辑态）
  - `usePreviewGraphBuilder.ts`（preview payload 图构建）
- 原则：只做“状态搬运 + 依赖注入”，不改业务语义。

2. 再拆 `TemplateDebugPipelineEditorV3.vue`
- 先抽两个组件：
  - `TemplateDebugWorkspaceToolbar.vue`
  - `TemplateDebugNodeInspector.vue`
- 再抽调试弹窗：
  - `TransformMappingDebugModal.vue`
- 原则：先抽纯展示组件，后抽带逻辑组件，避免 scoped style 一次性连锁。

3. 最后拆 transform 相关逻辑
- `useTransformInspector.ts` 继续按“primitive/rules/state-actions”分层
- `useTransformDebugState.ts` 拆出“payload builder / response parser / ui state”

---

## 4. 后续 stage 开发约定（重要）

新增 stage 时，先改 registry，再扩展能力：

1. 在 `stageRegistry.ts` 增加 descriptor
- `type`
- `label`
- `inspectorKind`
- `createDefaultConfig`（如有结构化配置）

2. 若是结构化 stage（类似 snmpprocess/transform）
- 在 `useNodeEditorActions.ts` 增加 apply 分支
- 在 inspector 区域新增 composable（避免把逻辑继续塞回 `usePageState.ts`）

3. 若是伪节点/不下发后端执行 stage
- 在 `previewPayload.ts` 明确是否参与 payload 过滤和 pseudo node 结果生成

4. 每次 stage 增加必须补齐
- 节点新增默认配置检查
- 编辑器 apply 生效检查
- preview payload 构造检查

---

## 5. 与既有交接文档关系

前置文档：
- `docs/AI_HANDOFF_TEMPLATE_DEBUG_V3_WHOLE_TABLE_2026-03-18.md`
- `docs/TEMPLATE_DEBUG_V3_TRANSFORM_WHOLE_TABLE_UPGRADE_PLAN_2026-03-18.md`
- `docs/TEMPLATE_DEBUG_V3_TARGET_TYPE_SINGLE_PIPELINE_PLAN_2026-03-19.md`

本文件定位：
- 聚焦 UI 代码结构与 stage 扩展入口治理
- 不替代整表（tableTransform）语义方案文档

---

## 6. 下一会话建议执行清单（可直接开工）

1. 先完成 `target.type` 单组调试接线（下拉选择、load 携带 `target_type`、缺失空态）。  
2. 抽 `TemplateDebugNodeInspector.vue`（先只承接 dataref/snmpprocess/transform 三块）。  
3. 为 stage registry 增加 `isExecutableStage` 能力，并在 `previewPayload` 中集中处理“伪节点过滤规则”。  
4. 新增一个 stage 开发 smoke 测试脚本（至少覆盖：新增节点、apply、preview payload 构建）。  
5. 继续拆 `usePageState.ts`：优先拆 runtime 结果浏览（timeline + node preview）相关逻辑。

---

## 7. 验证命令

在 `OneOPS-UI` 目录执行：

- `npx eslint src/views/platform/template-debug-v3/*.ts src/views/platform/TemplateDebugPipelineEditorV3.vue`
- `NODE_OPTIONS=--max-old-space-size=8192 npx vue-tsc --noEmit --skipLibCheck`
