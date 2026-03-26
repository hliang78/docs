# AI 交接文档（Template Debug V3）

更新时间：2026-03-19（含 target.type 单组调试增量）  
适用范围：`OneOPS-UI`、`OneOps`、`ctrlhub/controller`、`bidi` 相关链路

## 1. 本轮目标与结论

### 1.1 目标
- 将 Template Debug V3 的采集结果改为更易查看的 UI（折叠 + 侧边抽屉）。
- 支持“Collect 部分失败时，成功数据仍可用于后续 pipeline 调试”。
- 采集结果展示同时包含成功数据与失败信息。

### 1.2 关键结论
- 当前最终策略：**不做前端兜底解析**，只按后端明确协议处理返回结果。
- “在线 controller 查询失败”问题最后确认为：**controller 端引用了错误配置**（非代码缺陷）。
- `bidi` 升级后曾出现 `invalid character '\x00'` 的 RPC 解析错误，已定位为底层分包读写问题并在 `bidi` 侧按 `io.ReadFull + writeFull` 修复（见第 4 节）。

### 1.3 2026-03-19 增量结论（本轮重点）
- `Attentions` 中实际包含多组 pipeline（按 `target.type` 区分），调试应切换为“每次单组”而非全量混合。
- 已新增设计文档：`docs/TEMPLATE_DEBUG_V3_TARGET_TYPE_SINGLE_PIPELINE_PLAN_2026-03-19.md`。
- OneOps 当前已落地一部分基础能力：
  - `load-template-v3` 请求 DTO 增加 `target_type` 字段（用于后续单组过滤）。
  - attention graph 生成时已支持从模板文件内容解析 collect `oid/command`，并将 method 归一化为 controller 可执行 token（`snmp_* / ssh_* / telnet_*`）。
- 当前剩余工作：按 `target_type` 做 attention graph 过滤、返回 `target_types` 给 UI 下拉、补缺失场景提示与联调闭环。

---

## 2. 已完成改动（按仓库）

## 2.1 OneOPS-UI

### 已完成
- 页面定位并重构：`TemplateDebugPipelineEditorV3.vue`
  - 采集区块支持折叠。
  - 新增“采集结果”侧边抽屉（默认不占主页面）。
  - 抽屉可展示：
    - structured_fields
    - raw_fragments
    - trace / summary
    - stage trace 表格
    - 部分失败信息卡片
    - JSON 复制/导出
- “采集结果”按钮改为可点击（不再灰掉）。
- 删除 V2 固化采集中的 `ssh_ip_a -> ip a` 预置项：
  - `src/views/platform/template-debug-v2/ui-preset.ts`

### 2026-03-17 当日新增（V3 画布/调试链路）
- 引入 `dataref` 数据伪节点（前端节点类型）：
  - 画布可添加 `stage_type=dataref` 节点并绑定 `structured_fields` 的 key。
  - 节点展示 `bind: <key>`。
  - 伪节点语义：只供数，不参与后端真实 stage 执行。
- 伪节点编译策略（前端完成，后端零改动）：
  - Preview 发包前，将 `dataref` 绑定值注入 `initial_snapshot`。
  - 同时从 payload graph 中剔除 `dataref` 节点及其相关边，避免后端 `unknown stage_type` 报错。
  - 冲突策略：同名 key 采用“伪节点值覆盖”。
- `initial_snapshot` 快捷注入能力增强：
  - 注入采集 `structured_fields` 全量。
  - 注入采集 `structured_fields` 指定 key。
  - 注入指定 preview 节点 output。
  - 新增“清空 initial_snapshot”按钮。
- Preview 交互修复：
  - “运行调试(Preview)”按钮改为 `session_id` 存在即可可点。
  - 运行 Preview 时若无 `pipeline_id` 自动创建 pipeline。
- 节点结果统一呈现：
  - 前端合并后端 `node_results` 与伪节点 runtime 结果（伪节点 `status=success`，`timing_ms=0`）。
  - 时间线/节点选中均可定位到伪节点结果。
- 数据预览 UI 迭代（最新）：
  - 右侧 `Stage 输入/输出` 不再承载大数据详情（避免挤压）。
  - 每个画布节点新增“预览”按钮，点击打开弹窗查看该节点输入/输出。
  - 右侧保留“打开当前节点数据预览”入口按钮。
  - 弹窗采用 `Input/Output` 双 Tab + 大视口 JSON 区域。
- 数据类型收敛（用于预览展示）：
  - 仅展示 `string`、`map[string]string`、`[]map[string]string`、`[]string`。
  - 其他类型不在预览 JSON 中输出。

### 最终落地原则（已确认）
- 前端不从异常对象猜测提取采集结果，不注入 fallback 数据。
- 仅处理后端明确返回结构。

---

## 2.2 OneOps

### 已完成
- `CollectV3Session` 扩展了采集响应落库与返回字段，包含：
  - `structured_fields`
  - `raw_fragments`
  - `trace`
  - `summary`
  - `execution_id`
- 在 `CollectPipelineV3` 返回 `success=false` 但包含 `data` 时，按“部分失败可用”路径继续落库与返回（而非直接失败中断）。
- 增加/更新了 V3 相关测试，覆盖：
  - 部分失败仍可创建 snapshot/pipeline
  - 无数据失败仍按错误返回

### 主要文件
- `OneOps/app/platform/service/impl/template_debug_v3.go`
- `OneOps/app/platform/service/impl/template_debug_v3_session_pipeline_test.go`

---

## 2.3 ctrlhub/controller

### 已完成
- `CollectPipelineV3` 在采集阶段有错误时，若存在部分成功数据，仍返回 `data`：
  - `status`（可能为 `partial_failed`）
  - `structured_fields`
  - `raw_fragments`
  - `trace`
  - `summary`
  - `execution_id`
  - `collected_at`
- 增加对应单测，验证“部分失败仍返回数据”。

### 主要文件
- `ctrlhub/controller/cmd/controller/template_debug_v3_rpc.go`
- `ctrlhub/controller/cmd/controller/template_debug_v3_collect_rpc_test.go`

---

## 2.4 bidi

### 背景
- 线上出现过报错：
  - `rpc client read response failed ... invalid character '\x00' in string literal`

### 根因
- 流式读写使用单次 `Read/Write`，在分包情况下可能读到半包，导致 JSON 负载被污染。

### 修复方向
- 读：`io.ReadFull`
- 写：全量写 `writeFull`
- 并补充分片场景测试用例验证

### 备注
- 你当前反馈的 controller 离线问题已确认为配置错误，不是这段修复导致。

---

## 3. 关键决策（给下一轮 AI）

1. 不要再加“前端异常兜底解析采集结果”逻辑。  
2. 部分失败可用性必须由后端协议显式提供。  
3. 调试时优先看 `CollectPipelineV3` 实际响应体是否带 `data.structured_fields/raw_fragments`。  
4. controller 在线状态问题先查配置与进程实例，不先改代码。  

---

## 4. 当前工作区状态（本机）

### OneOps（有改动）
- `app/platform/service/impl/template_debug_v3.go`
- `app/platform/service/impl/template_debug_v3_session_pipeline_test.go`
- `go.mod`
- `go.sum`

### ctrlhub（有改动）
- `controller/cmd/controller/template_debug_v3_rpc.go`
- `controller/cmd/controller/template_debug_v3_collect_rpc_test.go`
- `go.mod`
- `go.sum`

### OneOPS-UI（有改动）
- `src/views/platform/TemplateDebugPipelineEditorV3.vue`
- `src/views/platform/template-debug-v3/*`
- `src/views/platform/template-debug-v2/ui-preset.ts`
- `src/api/platform/template-debug-v3.ts`
- `src/typings/platform/template-debug-v3.ts`
- 以及 `src/router/utils.ts`（已有本地改动）

---

## 5. 已执行验证（本轮）

- `go test ./app/platform/service/impl -run V3 -count=1`（OneOps）通过  
- `go test ./cmd/controller -run CollectPipelineV3 -count=1`（ctrlhub/controller）通过  
- UI 全量 `typecheck` 仍被既有 V2 类型问题阻塞（与本次 V3 主改动无直接关系）
- V3 相关本地验证结论：
  - 未新增 V3 类型报错。
  - 当前报错集中在 `template-debug-v2/*` 既有类型问题。

---

## 6. 下一轮 AI 建议接手顺序

1. 先阅读并遵循：`docs/TEMPLATE_DEBUG_V3_TARGET_TYPE_SINGLE_PIPELINE_PLAN_2026-03-19.md`。  
2. OneOps：实现 `target_type` 单组过滤与 `summary.target_types/selected_target_type/target_type_missing` 返回。  
3. OneOPS-UI：新增 `target.type` 下拉，切换后携带 `target_type` 重载 graph。  
4. 保持 collect 可执行性：method 仅使用 controller 支持前缀（snmp/ssh/telnet），并优先从模板内容回填 `oid/command`。  
5. 再做跨厂商“同名 target.type 复制”辅助交互（先 UI 层加载与复制，不强依赖后端新增写接口）。  

---

## 7. 与你当前页面一致的可见行为（用于快速核对）

1. 画布节点按钮区包含：`起点`、`连到此`、`预览`。  
2. 右侧 `Stage 输入/输出` 面板不直接显示大段数据。  
3. 点击节点 `预览` 会弹出“节点数据预览”窗口，可切换 `Input`/`Output`。  
4. `dataref` 节点可在右侧绑定 `structured_fields key`，并显示 `bind:` 文案。  
