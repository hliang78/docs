# Template Debug V3 按 `target.type` 单组调试方案（2026-03-19）

适用范围：`OneOPS-UI`、`OneOps`、`ctrlhub/controller`

## 1. 背景与问题

当前 `Attentions` 配置中，一个厂商/平台会包含多个 `target.type`（例如 `IsAlive`、`NetworkDevicePorts` 等），每个 `target.type` 实际代表一组标准化 pipeline 定义。

现状问题：

1. 调试接口默认把所有 `target.type` 混合构图返回，前端画布一次看到多组 pipeline，调试焦点不清晰。
2. 前端缺少“按标准 pipeline 名称（`target.type`）选择单组调试”的入口。
3. 当当前厂商缺少某个标准 pipeline 时，缺少明确的“跨厂商复制再修改”操作指引。

## 2. 核心目标

1. 每次调试只针对一个 `target.type`。
2. UI 提供 `target.type` 下拉选择。
3. 后端明确返回当前可选 `target_types`，支持前端构建下拉。
4. 当所选 `target.type` 缺失时，返回明确状态，不混入其它 type 的 graph。
5. 支持“参考其它厂商同名 `target.type` pipeline”并复制到当前编辑上下文。

## 3. 术语约定

1. 标准 pipeline 名称：`Attention.DeviceCollect.Target[].Type`，即 `target.type`。
2. 单组调试：一次请求仅生成一个 `target.type` 对应的 `pipeline_graph / ui_graph / collect_params`。

## 4. 接口与数据约定

## 4.1 Load 请求（OneOps）

`POST /api/v1/platform/template-debug-v3/sessions/:sessionID/pipeline-template/load`

请求新增字段：

1. `target_type`（string，可选）
   - 语义：本次调试指定的标准 pipeline 名称（`target.type`）。

说明：`target_type` 已在 `OneOps` DTO 中预留（`TemplateDebugV3PipelineTemplateLoadReq.TargetType`）。

## 4.2 Load 响应（建议）

在 `data.summary` 中新增：

1. `target_types`: 当前 vendor/platform/version 命中后可调试的 type 列表（去重、有序）。
2. `selected_target_type`: 本次生效的 type（可能来自请求或默认选择）。
3. `target_type_missing`: bool，表示请求了 type 但未命中。
4. `graph_scope`: `single_target_type` 或 `all_target_types`（兼容旧行为时可用）。

## 5. 生成规则（OneOps attention graph）

1. 匹配规则仍以 `vendor/platform/versionRange` 为第一层过滤。
2. 当 `target_type` 非空：
   - 仅保留 `target.type == target_type` 的分支构图。
   - 若无匹配，返回空 graph + `target_type_missing=true`，不回退成全量 graph。
3. 当 `target_type` 为空：
   - 为兼容历史，可先保留全量行为；推荐 UI 首次加载后自动选中一个 `target_type` 再发起单组请求。
4. collect 参数生成：
   - 优先从 controller `template_files.content` 解析 `name/method/target/fields` 回填 `oid/command/output_field`。
   - `method` 归一化到 controller 可执行 token（`snmp_* / ssh_* / telnet_*`）。

## 6. UI 交互方案（OneOPS-UI）

1. 在 V3 调试页增加 `target.type` 下拉（数据源为 `summary.target_types`）。
2. 切换下拉后重新调用 load 接口，携带 `target_type`。
3. 画布只渲染返回的单组 pipeline。
4. 当 `target_type_missing=true`：
   - 显示“当前厂商缺少该标准 pipeline”的空态提示。
   - 提供“从其它厂商复制”入口（见第 7 节）。

## 7. 跨厂商复制建议流程

1. 选择“源厂商/平台 + 相同 `target.type`”加载其单组 pipeline。
2. 在前端编辑器复制节点/边配置到当前厂商上下文。
3. 保存为当前厂商模板（后续可扩展为显式“保存为新模板”动作）。

注：当前阶段优先实现“加载 + 编辑 + 调试”闭环，复制可先做前端编辑层能力，不强绑后端新增写接口。

## 8. 分阶段落地

1. Phase A（后端最小闭环）
   - Load 接口支持 `target_type` 过滤。
   - 响应带 `target_types/selected_target_type/target_type_missing`。
2. Phase B（前端单组选型）
   - UI 下拉接入，按 `target_type` 重载 graph。
3. Phase C（复制辅助）
   - UI 提供跨厂商加载与复制引导。

## 9. 验收标准

1. 同一 `vendor/platform` 下，切换不同 `target.type`，画布节点和连线明显变化且互不混杂。
2. `ui_graph` 不包含 collect 节点，collect 参数完整可执行（`oid/command`）。
3. 请求不存在的 `target_type` 返回空图和明确提示，不返回混合图。
4. 单测覆盖：
   - `target_type` 命中。
   - `target_type` 不命中。
   - 未传 `target_type` 的兼容行为。

