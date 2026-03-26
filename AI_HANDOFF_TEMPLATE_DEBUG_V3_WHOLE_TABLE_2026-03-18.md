# AI 交接文档（Template Debug V3 - Transform 整表模式）

更新时间：2026-03-18  
适用范围：`netlink`、`OneOps`、`OneOPS-UI`

## 1. 本轮目标与结果

本轮重点完成：

1. 明确了 Transform V3 在整表输入（`[]map[string]string`）下的能力边界。  
2. 已实现并可用：调试弹窗内“应用到当前 Mapping”回写。  
3. 产出“整表 3 模式 + 多源合并”的升级方案文档（见第 6 节）。

结论：
- 如果要完整支持“列投影/列替换/列追加 + 多源合并”，`netlink` 必须升级。
- 当前仅“单源整表表达式”基础能力可用，尚未产品化为显式 mode。

---

## 2. 当前代码状态（交界边界）

## 2.1 netlink

工作区状态：**clean（无未提交改动）**。

说明：
- 本次交界点不包含新的 netlink 未提交修改。
- 下一会话可直接从方案文档落地阶段 A（新增 `tableTransform` 结构 + 执行分支 + 单测）。

## 2.2 OneOPS-UI

工作区状态：**dirty（存在未提交改动）**。

当前改动集中在：
- `src/views/platform/TemplateDebugPipelineEditorV3.vue`
- `src/views/platform/template-debug-v3/usePageState.ts`
- `src/views/platform/template-debug-v3/useTransformInspector.ts`
- 以及同目录其他 v3 文件（快照/调试 UI 相关）

本轮新增并已验证的关键能力：
- 调试弹窗新增按钮“应用到当前 Mapping”。
- 仅在 mapping scope 可用，点击后回写 `inputField/outputField/regex(expr)`。

关键代码位置：
- 回写可用性：
  - `OneOPS-UI/src/views/platform/template-debug-v3/usePageState.ts:1007`
- 回写执行函数：
  - `OneOPS-UI/src/views/platform/template-debug-v3/usePageState.ts:1497`
- 暴露到页面状态：
  - `OneOPS-UI/src/views/platform/template-debug-v3/usePageState.ts:2120`
- 按钮入口：
  - `OneOPS-UI/src/views/platform/TemplateDebugPipelineEditorV3.vue:1042`

---

## 3. 本轮已完成验证

## 3.1 OneOPS-UI

执行并通过：
- `npx eslint src/views/platform/template-debug-v3/usePageState.ts src/views/platform/TemplateDebugPipelineEditorV3.vue`
- `NODE_OPTIONS=--max-old-space-size=8192 npx vue-tsc --noEmit --skipLibCheck`

## 3.2 netlink

执行并通过：
- `go test ./pipeline -run TestTransformStageV3_Process -count=1`

---

## 4. 当前未完成（留给下一会话）

1. `netlink` 尚未引入显式整表模式配置（`tableTransform` 等）。
2. `OneOps` 尚未增加整表模式字段透传/校验。
3. `OneOPS-UI` 尚未提供“整表模式向导化配置”组件（目前仍以 regex/expr 为主）。
4. 多源合并策略（row_align/aggregate/key_join + 冲突策略）尚未实现。

---

## 5. 下一会话推荐执行顺序（强建议）

1. 先做 `netlink` 阶段 A：
- 扩展 `FieldMapping`（新增 `tableTransform` 可选对象）。
- 在 `TransformStageV3.processSliceValue` 增加三模式执行分支。
- 先补单测：`column_project` / `column_inplace` / `column_append`。

2. 再做 `OneOps`：
- DTO + decode + validate 支持 `tableTransform`。
- 增加错误码与 field_path 定位。

3. 最后做 `OneOPS-UI`：
- mapping 区新增整表模式编辑器。
- 调试弹窗支持整表模式回写（复用已做的“应用到当前 Mapping”能力）。

---

## 6. 关联文档

升级方案主文档：
- [`docs/TEMPLATE_DEBUG_V3_TRANSFORM_WHOLE_TABLE_UPGRADE_PLAN_2026-03-18.md`](/home/jacky/project/OneOPS-ALL/docs/TEMPLATE_DEBUG_V3_TRANSFORM_WHOLE_TABLE_UPGRADE_PLAN_2026-03-18.md)

历史交接文档（更早阶段）：
- `docs/AI_HANDOFF_TEMPLATE_DEBUG_V3_2026-03-17.md`

---

## 7. 对下一位 AI 的约束说明

1. 不要破坏现有 `source#subField` 语义与旧模板兼容性。  
2. 整表模式第一版建议限定“单源 + 单 mapping”，先保证可解释性。  
3. 多源合并不要隐式推断，必须有显式策略字段。  
4. 优先先写测试再改执行器，避免行为漂移。

