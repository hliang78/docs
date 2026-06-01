# Platform 脚本执行前端重构 - Discovery

## 当前真实代码事实

### 1. 页面入口与文件规模

- `任务中心` 页面文件 [TaskManagement.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/platform/TaskManagement.vue) 约 `3789` 行。
- `脚本模板工作台` 页面文件 [ScriptTemplateStudio.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/platform/ScriptTemplateStudio.vue) 约 `3655` 行。
- `任务模板管理` 页面文件 [TaskTemplateManagement.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/platform/TaskTemplateManagement.vue) 约 `774` 行。
- `定时任务管理` 页面文件 [ScheduledTaskManagement.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/platform/ScheduledTaskManagement.vue) 约 `963` 行。

结论：业务执行链路中的 2 个主页面已经演变成超大单文件页面，另外 2 个页面规模较小，但承担了大量重复字段和重复校验逻辑。

### 2. 路由与业务串联关系

路由定义位于 [utils.ts](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/router/utils.ts)：

- `platform/task-center` -> `TaskManagement`
- `platform/task-templates` -> `TaskTemplateManagement`
- `platform/script-template-studio` -> `ScriptTemplateStudio`
- `platform/scheduled-tasks` -> `ScheduledTaskManagement`
- 邻接调试页：
  - `platform/template-debug-v2`
  - `platform/template-debug-v3`

页面之间存在明显互跳：

- `TaskManagement` 可跳到模板、变量组、定时任务、脚本工作台
- `TaskTemplateManagement` 可直接跳去创建任务、创建定时任务、打开脚本工作台
- `ScheduledTaskManagement` 可跳回任务中心、模板页、变量组、脚本工作台
- `ScriptTemplateStudio` 可通过 query 或按钮回流到任务中心

结论：当前不是“一个中心页面 + 若干辅助页”，而是一组互相耦合的页面网络。

### 3. 共享领域模型已经存在，但前端未抽象成共享配置层

任务执行核心类型定义集中在：

- [task.ts](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/typings/platform/task.ts)
- [script_studio.ts](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/typings/platform/script_studio.ts)

关键模型：

- `ExecutionEnvelopeV2`
- `TaskAuthPolicy`
- `ParameterSpecV2`
- `inventory_grouping_selection_set_id`
- `run_on_agent / agent_code`

结论：后端契约层已经有统一执行模型，但前端页面仍然各自组装字段，没有沉淀成共享的表单 schema、字段分组或 composable。

### 4. 字段和逻辑重复非常明显

在 `任务中心 / 任务模板 / 定时任务 / 脚本工作台` 中反复出现的字段包括：

- `variable_set_id`
- `inventory_content`
- `inventory_grouping_selection_set_id`
- `repo_url`
- `repo_branch`
- `extra_vars_json`
- `parameter_specs_json`
- `arguments`
- `run_on_agent`
- `agent_code`
- `credential_ref`
- `function_area`
- `project_id`

重复函数也已经出现：

- `validateJSONObject`
- `parseParameterSpecsJSON`
- `onRunTargetChange`
- `onInventorySourceChange`
- 跨页面导航函数

结论：当前重构收益最大的区域不是“单页视觉优化”，而是“抽出共享执行配置层”。

### 5. `任务中心` 同时承担了过多职责

[TaskManagement.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/platform/TaskManagement.vue) 当前同时包含：

1. 主线推荐入口卡片
2. 列表筛选与分页
3. 任务列表
4. 日志抽屉
5. SSE 日志流
6. 创建任务弹窗
7. 模板预填、变量组预填、推荐 Agent、示例仓库、主线提示
8. `ExecutionEnvelopeV2` 组装逻辑

这里已经不是一个“列表页”，而是“任务执行门户 + 任务详情 + 任务创建器”叠在一起。

### 6. `脚本模板工作台` 是另一处复合型超页面

[ScriptTemplateStudio.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/platform/ScriptTemplateStudio.vue) 当前在一个页面内串起：

1. 会话创建
2. 多轮对话
3. 草稿版本
4. 编辑器
5. 参数协议展示
6. 本地校验 / 执行测试
7. 发布模板
8. 设备分组构建器
9. query 驱动的会话恢复
10. 日志拉取与轮询

结论：这不是单一页面，而更像一个 mini workbench。问题不是功能少，而是工作台内缺少更清晰的分区和阶段化组织。

### 7. `任务模板` 与 `定时任务` 已经形成重复的“执行配置表单”

[TaskTemplateManagement.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/platform/TaskTemplateManagement.vue) 和 [ScheduledTaskManagement.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/platform/ScheduledTaskManagement.vue) 都包含接近同构的字段组：

- 模板 / 项目 / 区域
- Inventory / 库存来源
- 仓库地址 / 分支
- Extra Vars
- Parameter Specs
- Arguments
- 执行位置 / Agent
- 凭证

结论：这两页已经具备抽象成共享 `ExecutionConfigForm` 的条件。

### 8. 模板调试页与执行页的成熟度不一致

`template-debug-v2/v3` 虽然复杂，但已经比执行页更模块化：

- [TemplateDebugPipelineEditorV2.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/platform/TemplateDebugPipelineEditorV2.vue) 主页面约 `349` 行，主要依赖 composable 和子组件。
- [TemplateDebugPipelineEditorV3.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/platform/TemplateDebugPipelineEditorV3.vue) 主页面约 `939` 行，核心状态被拆入 [usePageState.ts](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/platform/template-debug-v3/usePageState.ts) 等模块。

结论：同属 `platform` 的相邻复杂页面，调试页已经在做模块化治理，而“执行链路页”还停留在重页面堆叠阶段。

## 前端体验观察

这些观察基于模板结构、状态组织和页面职责，不依赖后端运行结果。

### 1. 信息架构更像“功能堆叠”，不是“任务流程”

- 工作台页把创建会话、对话、编辑、测试、发布全部平铺在一个纵向页面里。
- 任务中心把推荐入口、过滤、列表、日志、创建任务都塞进一个页面。

用户必须自己理解：

- 什么时候该去工作台
- 什么时候该回模板页
- 什么时候该在任务中心创建即时任务
- 什么时候该转去定时任务

### 2. 页面帮助文案很多，但阶段边界不够清晰

当前页面有不少提示文案，说明业务知识已经很强；问题不在“没有说明”，而在“说明出现的位置太分散，且和输入控件混在一起”。

### 3. 同一个执行概念在不同页面的入口不一致

比如 inventory、repo、参数、Agent、凭证、提权策略，在不同页面有不同的默认值、不同的校验方式、不同的文案上下文。

这会导致：

- 用户迁移心智成本高
- 页面之间不容易复用
- 以后每次加字段都要多点同步修改

## AI 推导建议

### 方向 A：先做“结构性重构”，不急着大改视觉

优先把现在的一组页面改成统一工作流：

1. `脚本产出`
2. `模板沉淀`
3. `即时执行`
4. `周期执行`

每个阶段页面只保留自己最核心的职责，避免一个页面同时做 4 件事。

### 方向 B：先抽共享执行配置层

先不大改页面布局，而是先抽：

- `ExecutionConfigForm`
- `ExecutionConfigPreview`
- `useExecutionConfig`
- `useParameterSpecEditor`
- `useInventorySource`
- `useRunTarget`

这样可以先降低重复代码，再决定是否重排信息架构。

### 方向 C：做“轻工作台 + 详情侧栏”模式

对于 `任务中心` 和 `脚本模板工作台`，可以考虑：

- 主区域只保留当前阶段主任务
- 次要说明、日志、历史记录进入侧栏或分步区域
- 把“推荐入口”“帮助提示”“结果明细”从主编辑流中解耦

## 规划缺口

1. 是否把 `template-debug-v2/v3` 纳入这次重构主范围
2. 是否接受页面级工作流重排，而不只是组件级拆分
3. 这次优先级更偏：
   - 降低单文件复杂度
   - 统一执行配置模型
   - 优化用户路径
   - 统一视觉层
