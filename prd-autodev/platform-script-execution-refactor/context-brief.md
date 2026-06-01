# Platform 脚本执行前端重构 - Context Brief

## 用户原始诉求

请对 `platform` 的脚本执行相关前端页面做一轮重构，先分析前端，再沟通重构思路。

## 当前判断

- 类型：`frontend`
- 当前阶段：`research / alignment`
- 本轮目标：先确认现有页面边界、前端实现结构、交互流程和主要问题，不直接进入实现。

## 暂定研究范围

围绕 `platform` 脚本执行链路，当前确认的核心页面：

1. `任务中心`
   - 路由：`/platform/task-center`
   - 页面：[TaskManagement.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/platform/TaskManagement.vue)
2. `脚本模板工作台`
   - 路由：`/platform/script-template-studio`
   - 页面：[ScriptTemplateStudio.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/platform/ScriptTemplateStudio.vue)
3. `任务模板管理`
   - 路由：`/platform/task-templates`
   - 页面：[TaskTemplateManagement.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/platform/TaskTemplateManagement.vue)
4. `定时任务管理`
   - 路由：`/platform/scheduled-tasks`
   - 页面：[ScheduledTaskManagement.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/platform/ScheduledTaskManagement.vue)

## 邻接页面

以下页面与“脚本执行”强相关，但更偏模板调试/采集调试，暂列为二级范围：

1. `模板调试 V2`
   - 页面：[TemplateDebugPipelineEditorV2.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/platform/TemplateDebugPipelineEditorV2.vue)
2. `模板调试 V3`
   - 页面：[TemplateDebugPipelineEditorV3.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/platform/TemplateDebugPipelineEditorV3.vue)

## 业务流初步理解

当前前端试图覆盖一整条链路：

1. 在 `脚本模板工作台` 创建会话并通过对话生成草稿
2. 在工作台内完成测试、校验、发布
3. 将产物沉淀为 `任务模板`
4. 在 `任务中心` 从模板或手工字段创建即时任务
5. 在 `定时任务管理` 复用模板创建周期执行

## 本轮已确认的重点问题方向

1. 页面职责偏重，多个页面同时承担“引导 + 配置 + 执行 + 结果查看”。
2. 执行配置字段在多处重复，领域模型共享但 UI 结构没有共享。
3. 页面之间通过 query 参数和按钮跳转互相串联，形成较强的前端耦合。
4. 当前信息架构更像“功能堆叠”，不是“工作流驱动”。

## 暂未确认的问题

1. 本次重构是否只覆盖上述 4 个核心业务页，还是也要纳入 `template-debug-v2/v3`
2. 重构重点更偏：
   - 代码可维护性
   - 页面信息架构和用户路径
   - 视觉层统一
   - 全部一起做
3. 是否允许在现有 Ant Design Vue 风格上做较明显的信息架构调整
