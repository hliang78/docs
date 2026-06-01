# 【原型清单】OneOPS_DeviceV2_入库与设备管理_V1.0

## 1. 文档信息

| 项目 | 内容 |
|------|------|
| 系统名称 | OneOPS |
| 子系统名称 | 设备管理 |
| 功能模块名称 | Device V2 入库与设备管理 |
| 版本号 | V1.0 |
| 创建日期 | 2026-05-15 |
| 文档状态 | `blocked-human-confirmation` |
| 关联需求文档 | 【需求概要】OneOPS_DeviceV2_V1.0.md |
| 编写说明 | 基于当前前端路由、页面组件和 request wrapper 反向整理的候选原型清单；不可直接作为产品原型、UI 验收或上线依据。 |

## 2. 模块概述

### 2.1 业务目标

Device V2 前端当前提供设备清册、入库工作台、导入批次、schema 设计、store/采集 evidence 查看等页面入口。本文档只记录当前真实页面/组件事实，并将其整理为候选原型清单，供产品、前端、测试人工确认。

### 2.2 功能范围

- 当前真实代码事实：前端路由存在 `DeviceV2Management`、`DeviceV2ManagementRedesign`、`DeviceV2SchemaDesign`、`DeviceV2ImportBatches`、`DeviceV2IngestPipelineRedesign` 五个 Device V2 页面入口。
- 候选文档内容：本文按 04 模板整理页面统计、页面清单、层级结构、公共组件、导航关系和关联模块。
- AI 推导建议：正式原型可将“设备清册”和“导入设备清单/新入库”作为两个主流程，schema 和导入批次作为配置/历史辅助入口。
- 规划缺口：正式菜单可见性、页面名称、按钮权限、危险动作二次确认、错误提示、验收路径、移动端适配均 `[待人工确认]`。

## 3. 页面统计

| 类型 | 数量 |
|------|------|
| 主页面 | 2 |
| 子页面 | 3 |
| 弹窗/抽屉 | `[待补充]` 当前已确认 schema 页面有属性/关系编辑 modal，管理页和入库页存在多种交互区；完整弹窗数量未逐项确认 |
| 统计/分析页 | 0 |
| 合计 | 5 个路由页面 + 若干页面内弹窗/操作区 |

## 4. 页面清单

| 页面名称 | 页面类型 | 功能描述 | 核心功能要点 | 关联页面/组件 |
|----------|----------|----------|--------------|----------------|
| 设备 V2 管理（`DeviceV2Management`） | 主页面 | 当前设备 V2 管理入口，包含列表、筛选、导入入口、schema 跳转、测试/变更辅助区域等。 | - 查询设备列表<br>- 新导入入口<br>- 手工新增入口<br>- 流程引导<br>- 状态筛选<br>- 最近导入结果<br>- schema 跳转<br>- 测试/变更辅助区域 | `DeviceV2SchemaDesign`、`DeviceV2ImportBatches`、`DeviceV2IngestPipelineRedesign`、`DeviceV2ManagementRedesign` |
| 设备清册（`DeviceV2ManagementRedesign`） | 主页面/预览页 | 设备清册重构预览页，承接入库 handoff query，支持清册筛选和后续操作候选。 | - 根据 `codes/task_id` query 承接入库结果<br>- 支持路由 query 清理/替换<br>- 可跳转 schema 设计<br>- 与 Device V2 list/get/store 等 wrapper 关联 | `DeviceV2IngestPipelineRedesign`、`DeviceV2SchemaDesign` |
| 设备 V2 新入库（`DeviceV2ImportBatches`） | 子页面 | 新入库工作台/导入批次入口，包含下载模板、上传文件、最近任务、继续草稿和跳转清册。 | - 下载导入模板<br>- 上传文件<br>- 最近任务/最新 task 展示<br>- 继续草稿<br>- 提交导入批次<br>- 短轮询刷新 task<br>- 跳转清册 | `DeviceV2Management`、Device V2 ingest wrapper |
| 导入设备清单（`DeviceV2IngestPipelineRedesign`） | 子页面/预览页 | 入库流程重构页，包含上传设备清单、新增草稿行、历史入库单、提交入库、handoff 到清册。 | - 上传 Excel<br>- 下载模板<br>- 新增草稿行<br>- 修正草稿问题<br>- 历史入库单搜索/加载<br>- 查看执行结果<br>- 提交到设备清册<br>- Handoff 到清册 | `DeviceV2ManagementRedesign`、Device V2 ingest wrapper |
| 设备 V2 模型配置（`DeviceV2SchemaDesign`） | 子页面/配置页 | schema 设计页，管理 attributes、labels、relation_types，支持导入 schema 文件和保存。 | - 查询当前 schema<br>- 属性定义表<br>- 标签定义表<br>- 关系类型定义表<br>- 导入 schema 文件<br>- 从 V1 结构生成 schema<br>- 保存 schema<br>- precheck UI 当前标注临时关闭 | `DeviceV2Management`、schema wrapper |

## 5. 页面层级结构

- 设备 V2 管理（`DeviceV2Management`）
  - 设备列表/筛选区
  - 新导入入口
    - 设备 V2 新入库（`DeviceV2ImportBatches`）
    - 导入设备清单（`DeviceV2IngestPipelineRedesign`）
  - 设备清册重构预览入口（`DeviceV2ManagementRedesign`）
    - 入库 handoff query：`codes`、`task_id`
  - 设备 V2 模型配置（`DeviceV2SchemaDesign`）
    - 属性定义（attributes）
      - 属性编辑弹窗 `[当前真实代码事实: a-modal]`
    - 标签定义（labels）
      - 标签编辑弹窗 `[当前真实代码事实: a-modal]`
    - 关系类型定义（relation_types）
      - 关系类型编辑弹窗 `[当前真实代码事实: a-modal]`
- 设备 V2 新入库（`DeviceV2ImportBatches`）
  - 上传文件
  - 下载模板
  - 最近/最新入库 task
  - 草稿继续/提交
  - 跳转设备管理
- 导入设备清单（`DeviceV2IngestPipelineRedesign`）
  - 清单上传
  - 草稿编辑
  - 历史入库单
  - 提交入库
  - 跳转设备清册

## 6. 公共组件

| 组件名称 | 适用范围 | 功能描述 |
|----------|----------|----------|
| Ant Design Vue `a-card` | Device V2 管理、入库、schema 页面 | 页面分区卡片容器。 |
| Ant Design Vue `a-table` | schema、入库执行结果、候选列表区域 | 展示属性/标签/关系、执行结果、列表数据。 |
| Ant Design Vue `a-modal` | schema 设计页；其他页面弹窗待继续确认 | schema 属性/关系编辑弹窗。 |
| Ant Design Vue `a-button` / `a-tag` / `a-alert` / `a-descriptions` | Device V2 多页面 | 操作按钮、状态标识、风险提示和详情摘要。 |
| `DeviceV2IngestDraft` 相关组合逻辑 | DeviceV2ImportBatches、DeviceV2IngestPipelineRedesign | 入库草稿、最新 task、设备清单修正和继续操作候选。 |
| request wrapper：`device-v2.ts` | 管理/清册/store/schema 页面 | 封装 `/device/v2` 设备列表、详情、schema、store、task、observations、latest DC2 等请求。 |
| request wrapper：`device-v2-ingest.ts` | 入库页面 | 封装 `/device/v2/ingest` capabilities、template、submit/upload/list/get task 请求。 |
| request wrapper：`device-v2-import.ts` | 导入批次页面 | 封装 `/device/v2/import/batches` create/upload/validate/apply/retry/list/purge/records/template/anchor-basis 请求。 |

## 7. 页面导航关系

### 7.1 模块内部导航关系

| 源页面 | 触发动作 | 目标页面 | 备注 |
|--------|----------|----------|------|
| DeviceV2Management | 点击 schema/模型配置入口 | DeviceV2SchemaDesign | 当前代码：`router.push({ name: 'DeviceV2SchemaDesign' })` |
| DeviceV2Management | 点击新导入/导入批次入口 | DeviceV2ImportBatches | 当前代码：`router.push({ name: 'DeviceV2ImportBatches' })` |
| DeviceV2Management | 点击入库 pipeline 入口 | DeviceV2IngestPipelineRedesign | 当前代码：`router.push({ name: 'DeviceV2IngestPipelineRedesign' })` |
| DeviceV2Management | 点击清册重构预览入口 | DeviceV2ManagementRedesign | 当前代码存在跳转，可携带 query；正式入口 `[待人工确认: 前端负责人]` |
| DeviceV2ImportBatches | 点击返回/跳转清册 | DeviceV2Management | 当前代码存在 `router.push({ name: 'DeviceV2Management' })` 和携带 query 跳转。 |
| DeviceV2IngestPipelineRedesign | 点击 handoff 到清册 | DeviceV2ManagementRedesign | 当前代码可携带 `codes`、`task_id` query。 |
| DeviceV2SchemaDesign | 点击返回 | DeviceV2Management | 当前代码：`router.push({ name: 'DeviceV2Management' })` |
| DeviceV2ManagementRedesign | 点击 schema 设计 | DeviceV2SchemaDesign | 当前代码存在 schema 跳转。 |

### 7.2 模块间导航关系

| 源页面 | 触发动作 | 目标模块/页面 | 备注 |
|--------|----------|---------------|------|
| Device V2 管理/清册 | store/start、task、observations、latest DC2 相关操作 | 后端 Device V2 store/task API | 页面内展示路径和按钮权限 `[待人工确认: 产品负责人/安全负责人]` |
| Device V2 schema 页面 | 从 V1 结构生成 schema | Device V1/后端 schema API | 当前页面有“从 V1 结构体生成 schema”逻辑；正式治理流程 `[待人工确认]` |
| Device V2 入库页面 | 提交/上传入库任务 | 后端 Device V2 ingest API | 上传、提交属于写入操作；需权限和确认。 |
| Device V2 导入批次页面 | validate/apply/retry/purge 导入批次 | 后端 Device V2 import API | purge/应用等危险动作默认不可由 AI 确认。 |

## 8. 与其他模块的关联

| 关联模块 | 关联方式 | 说明 |
|----------|----------|------|
| Device V1 | schema 生成、V1/V2 sync、launch 兼容 | 当前存在 `sync-from-v1`、`sync-to-v1`、schema 从 V1 结构生成的代码入口；正式策略待确认。 |
| Entity V2 / flexible-grouping | 数据模型、动态属性、标签、关系类型 | DeviceV2 model、schema 和 service 使用 entity/flexible-grouping 相关能力。 |
| Credential/凭据模块 | credential_ref 字段展示与导入 | 入库 device 类型含多类 credential ref；明文展示和权限 `[待人工确认: 安全/权限负责人]`。 |
| Device Collection / Store Pipeline | store/start、runs、observations、latest DC2 | Device V2 管理/验收证据依赖 store task 与 observations。 |
| 权限/登录模块 | 路由 requiresAuth、token 下载模板 | Device V2 路由均 `requiresAuth: true`；模板下载 URL 带 token query。正式权限矩阵待确认。 |

## 9. 待确认事项

| 序号 | 待确认内容 | 影响页面 | 状态 |
|------|------------|----------|------|
| 1 | 五个 Device V2 页面中哪些为正式生产入口，哪些仅为重构预览/临时入口 | 全部 Device V2 页面 | 待人工确认 |
| 2 | 菜单可见性、角色权限、按钮级权限和危险动作二次确认 | 管理、清册、入库、导入批次、schema | 待人工确认 |
| 3 | DeviceV2Management 与 DeviceV2ManagementRedesign 的长期关系：替代、并存或下线 | 管理/清册 | 待人工确认 |
| 4 | DeviceV2ImportBatches 与 DeviceV2IngestPipelineRedesign 的长期关系：新旧入口、迁移或合并 | 入库页面 | 待人工确认 |
| 5 | schema/precheck 当前前端标注“临时关闭”，是否恢复、隐藏或改为后端门禁 | Schema 设计页 | 待人工确认 |
| 6 | store/start、retry、apply、purge、delete 等写入/危险动作在 UI 上的展示、禁用和审批规则 | 管理/入库/导入批次 | 待人工确认 |
| 7 | UI edit/update、clone cleanup、非 admin 权限 evidence 缺失是否阻塞 launch | 管理/清册 | 待人工确认 |

## 10. 代码事实来源清单

详见 `docs/openclaw-autodev/evidence/dev-docs/DEV-DOCS-003B-device-v2-03-04-code-facts.md`。本文档状态保持 `blocked-human-confirmation`，不可直接作为产品原型、开发、测试、上线、story 发布或验收依据。
