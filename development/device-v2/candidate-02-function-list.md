# 【功能清单】OneOPS_DeviceV2_V1.0

## 1. 文档信息

| 项目 | 内容 |
|------|------|
| 系统名称 | OneOPS |
| 版本号 | V1.0 |
| 创建日期 | 2026-05-15 |
| 文档状态 | `blocked-human-confirmation` |
| 关联需求文档 | 【需求概要】OneOPS_DeviceV2_V1.0.md |

## 2. 需求理解摘要

Device V2 当前代码覆盖设备主记录管理、入库任务、导入批次、store pipeline、schema、V1/V2 同步和辅助证据查询。本文档基于源码反向生成候选功能清单，功能优先级和验收标准需人工确认后定稿。

## 3. 功能清单

| 功能ID | 功能名称 | 功能描述 | 优先级 | 依赖功能ID | 验收标准 | 备注 |
|--------|----------|----------|--------|------------|----------|------|
| F-001 | 查询设备列表 | 按分页、关键字、编码、IP、标签、属性、位置、纳管状态查询 Device V2 清册 | P0 - 清册管理入口 | 无 | GET `/device/v2/list` 返回 `list/total/page/page_size` | 真实 wrapper: `listDeviceV2Req` |
| F-002 | 查看设备详情 | 按设备编码查看 Device V2 主记录和扩展字段 | P0 - 管理闭环必需 | F-001 | GET `/device/v2/{code}` 返回含 `code/name` 的设备对象 | 真实 wrapper: `getDeviceV2Req` |
| F-003 | 创建设备 | 创建 Device V2 主记录 | P1 - 手工维护需要 | 无 | POST `/device/v2` 成功返回设备对象 | 生产权限待确认 |
| F-004 | 更新设备 | 按 code 更新 Device V2 主记录 | P1 - 手工维护需要 | F-002 | PUT `/device/v2/{code}` 成功返回设备对象 | 字段可编辑范围待确认 |
| F-005 | 删除设备 | 按 code 删除 Device V2 设备 | P1 - 管理能力存在但高风险 | F-002 | DELETE `/device/v2/{code}` 返回成功 | 删除策略和权限待确认 |
| F-006 | 查询变更历史 | 查看设备字段变更事件和字段级差异 | P1 - 审计与排障需要 | F-002 | GET `/device/v2/{code}/change-history` 返回 history 列表 | 状态处理规则待确认 |
| F-007 | 更新变更历史状态 | 将变更事件标记为 acknowledged/resolved 等状态 | P2 - 审计协作增强 | F-006 | POST `/device/v2/{code}/change-history/{id}/status` 成功 | 状态枚举待确认 |
| F-008 | 查询网络概览 | 查看设备接口、IP、MAC、邻居、ARP 等网络视图 | P1 - 排障和采集验证需要 | F-002 | GET `/device/v2/{code}/network-overview` 返回网络结构 | 前端入口待确认 |
| F-009 | 查询 store readiness | 判断设备是否具备启动 store pipeline 的候选条件 | P0 - store 前置检查 | F-002 | GET `/device/v2/{code}/store-readiness` 返回 readiness payload | 正式判定规则待确认 |
| F-010 | 启动 store pipeline | 对设备启动 store pipeline | P0 - store/采集闭环核心 | F-001/F-009 | POST `/device/v2/store/start` 返回 `task_id` | `task-trigger`，自动化需审批 |
| F-011 | 重试 store pipeline | 按 task/stage/codes 重试 store pipeline | P1 - 失败恢复需要 | F-010 | POST `/device/v2/store/retry` 返回 task | 幂等和并发语义待确认 |
| F-012 | 查询 store task 详情 | 查询 store task 当前状态和阶段 | P0 - evidence 追踪必需 | F-010 | GET `/device/v2/tasks/{taskId}` 返回 task | read-only |
| F-013 | 查询 store task summary | 查询 store task 汇总、highlight、layer 信息 | P0 - evidence 追踪必需 | F-010 | GET `/device/v2/tasks/{taskId}/summary` 返回 summary | read-only |
| F-014 | 查询 store runs | 查询单设备 store run 结果 | P0 - 失败定位必需 | F-010 | GET `/device/v2/tasks/{taskId}/runs` 返回分页结果 | read-only |
| F-015 | 查询 observations | 查询 store/采集观测字段 | P0 - 采集证据必需 | F-010 | GET `/device/v2/tasks/{taskId}/observations` 返回分页结果 | read-only |
| F-016 | 查询 latest DC2 | 查询设备最近一次 DC2 采集视图 | P1 - 验收证据候选 | F-010 | GET `/device/v2/{code}/last-store-collection-dc2` 返回 found/task/run 信息 | 是否作为验收待确认 |
| F-017 | 提交 ingest task | 通过 JSON payload 提交 Device V2 入库任务 | P0 - 新入库链路核心 | 无 | POST `/device/v2/ingest/tasks` 返回 ingest task | `write/task-trigger` |
| F-018 | 上传 ingest Excel | 上传 Excel 并创建 ingest task | P0 - 批量入库核心 | 无 | POST `/device/v2/ingest/tasks/upload` 返回 ingest task | 表单字段 `excel` |
| F-019 | 查询 ingest task | 按 taskId 查询 ingest task 详情 | P0 - 入库追踪必需 | F-017/F-018 | GET `/device/v2/ingest/tasks/{taskId}` 返回 task | read-only |
| F-020 | 查询 ingest capabilities | 查询入库框架版本、支持 source、状态、阶段 | P1 - 前端动态能力展示 | 无 | GET `/device/v2/ingest/capabilities` 返回 capabilities | read-only |
| F-021 | 下载 ingest Excel 模板 | 下载 Device V2 ingest Excel 模板 | P1 - Excel 入库辅助 | 无 | GET `/device/v2/ingest/template/excel` 返回 xlsx | token query 规则待确认 |
| F-022 | 管理 import batch | 创建、上传、校验、应用、重试、更新、查询、清理导入批次 | P1 - 历史/多次导入链路 | 无 | `/device/v2/import/**` 接口可追踪批次和记录 | 与 ingest task 边界待确认 |
| F-023 | 管理 schema | 查询、预检查和保存 Device V2 schema | P1 - 动态字段治理 | F-001/F-002 | `/device/v2/schema/**` 可返回/保存 schema | 发布门禁待确认 |
| F-024 | V1/V2 同步 | 支持从 V1 到 V2、V2 到 V1 同步 | P1 - 兼容旧台账 | 无 | POST sync 接口返回 created/updated/failed | 覆盖策略待确认 |
| F-025 | base reference check | 校验 Device V2 对 app/base 的引用合法性 | P1 - 数据质量治理 | F-001 | POST `/device/v2/base-reference-check` 返回 ready/issues | strict/warn 使用规则待确认 |

## 4. 非功能性需求清单

| 需求ID | 类型 | 需求描述 | 优先级 | 验收标准 | 备注 |
|--------|------|----------|--------|----------|------|
| NF-001 | 安全 | 删除、purge、sync、store/start、ingest submit/upload 必须有权限和审批边界 | P0 - 避免生产误操作 | `[待确认]` | 不得由 AI 自动确认 |
| NF-002 | 可追溯 | 入库、store、sync 等操作必须能追踪 task、run、record、error | P0 - 排障和验收需要 | `[待确认]` | 当前已有 task/run/record 模型 |
| NF-003 | 可维护 | 动态字段通过 schema、attributes、metadata、labels 管理 | P1 - 支撑扩展 | `[待确认]` | schema 发布策略待确认 |
| NF-004 | 性能 | 列表、runs、observations、records 需要分页并限制 page_size | P1 - 大数据量可用性 | `[待确认]` | 部分接口已有后端分页上限 |
| NF-005 | 自动化安全 | 默认自动化仅执行 read-only 接口 | P0 - 防止误写 | `[待确认]` | 写入接口需 story scope 或人工批准 |

## 5. 功能依赖关系

| 功能ID | 前置功能 | 后续影响功能 | 说明 |
|--------|----------|--------------|------|
| F-001 | 无 | F-002/F-004/F-005/F-010 | 设备列表是管理页入口 |
| F-002 | F-001 | F-006/F-008/F-009/F-016 | 详情是查看证据和辅助信息入口 |
| F-009 | F-002 | F-010 | readiness 是启动 store 的候选前置检查 |
| F-010 | F-001/F-009 | F-012/F-013/F-014/F-015/F-016 | store/start 产生 task 和 evidence |
| F-017/F-018 | 无 | F-019/F-001 | ingest 产生任务，后续回到设备清册或任务详情 |
| F-022 | 无 | F-001/F-010 | import apply 可产生或更新设备，并可能启动 pipeline |
| F-023 | F-001/F-002 | F-003/F-004/F-001 | schema 影响表单、列表、详情和动态属性 |
| F-024 | 无 | F-001/F-002 | V1/V2 同步影响设备主记录 |

## 6. 优先级定义

| 优先级 | 定义 |
|--------|------|
| P0 | 必须实现，否则 Device V2 入库、清册或 store evidence 核心流程不可用 |
| P1 | 强烈建议实现，支撑维护、审计、兼容和失败恢复 |
| P2 | 增强体验或协作效率，资源允许时实现 |


## 7. 代码事实来源清单

> 本节为 DEV-DOCS-003A 追加的代码事实来源清单。本文档状态仍为 `blocked-human-confirmation`，不可直接作为开发、测试、上线、story 发布、API 契约或验收依据。

| 分类 | 源码路径 / 材料 | 对应事实 | 待人工确认 |
|------|----------------|----------|------------|
| 标准文档结构 | `docs/development-doc-templates/02-功能清单模板.md` | 本文保留 02 模板的文档信息、需求理解摘要、功能清单、非功能性需求清单、功能依赖关系、优先级定义结构。 | `[待人工确认: 项目负责人]` 是否进入人工 review。 |
| route/router | `OneOPS/app/device/v2/router/device_v2.go`、`OneOPS/app/device/v2/ingest/router/device_v2_ingest.go` | F-001 到 F-025 的接口候选来自当前真实 router method/path/handler。 | `[待人工确认: 后端负责人]` 哪些 route 纳入正式功能范围。 |
| handler/controller | `OneOPS/app/device/v2/api/device_v2.go`、`device_v2_store_minimal_api.go`、`device_v2_import_minimal_api.go`、`device_v2_change_history.go` | 功能项的读写边界来自 handler 绑定、service 调用和错误处理。 | `[待人工确认: 安全/权限负责人]` 写入、清理和同步动作权限。 |
| DTO/model/service | `OneOPS/app/device/v2/dto/device_v2.go`、`dto/device_v2_import.go`、`model/device_v2.go`、`model/device_v2_import_batch.go`、`service/i_device_v2.go`、`service/i_device_v2_import.go` | 功能输入输出候选来自 DTO、模型字段和 service interface；验收标准只引用当前代码返回形态，不确认正式契约。 | `[待人工确认: 后端负责人]` DTO 字段、状态枚举和响应结构定稿。 |
| service implementation / DAO | `OneOPS/app/device/v2/service/impl/device_v2_minimal_import_lifecycle.go`、`device_v2_minimal_import_record_flow.go`、`device_v2_minimal_store.go` | import validate/apply/retry、store start/retry 和 run/observation 事实来自实现与 GORM 持久化逻辑。 | `[待人工确认: 后端负责人]` 幂等、重试、事务和失败处理规则。 |
| frontend wrapper/page | `OneOPS-UI/src/api/device/device-v2.ts`、`device-v2-import.ts`、`device-v2-ingest.ts`、`src/router/utils.ts`、`src/views/device/DeviceV2Management.vue`、`DeviceV2IngestPipelineRedesign.vue` | 功能项备注中的 wrapper/page 来源于当前前端真实调用和页面入口。 | `[待人工确认: 前端负责人]` 页面正式入口和菜单可见性。 |
| tests/evidence | `docs/prd-autodev/d2-launch-acceptance/evidence-index.md`、`launch-readiness-report.md` | launch evidence 只证明局部 2/5 设备切片；UI edit、cleanup、完整 5-device、非 admin 权限未证明。 | `[待人工确认: 测试负责人]` 哪些功能可进入验收/回归。 |

- 当前真实代码事实：功能清单中的 path、wrapper 和部分返回形态来自已读源码。
- 候选文档内容：本文将当前真实能力拆为 F-001 至 F-025，但优先级和验收标准仍为候选。
- AI 推导建议：P0/P1/P2 仅按当前入口、核心链路和 evidence 重要性初步提炼。
- 规划缺口：正式范围、业务优先级、权限模型、验收标准、fixture、性能目标、删除与 purge 策略均待人工确认。
