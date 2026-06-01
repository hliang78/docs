---
topic: oneops-operation-audit
kind: backend
title: OneOPS 操作审计轻量化设计
createdAt: 2026-05-21T11:55:18+0800
---

# Discovery

## Findings

- OneOPS 当前没有单一统一操作审计中心，而是多套分域留痕并存。
- 老设备侧已有 `device_history`，能看变更前后与 diff，但缺少 `operator`、`source`、`request_id`、审批链路等统一审计字段。
- Device V2 已具备较成熟的结构化变更事件模型，包含 `operator`、`source`、`risk_level`、`status`、字段级 delta，是最接近统一审计骨架的现有能力。
- 终端模块的 `terminal_records` 更偏会话审计/取证，能回答谁登录过哪台设备、会话多久、录像在哪。
- Monitoring V2 的 `platform_monitoring_v2_credential_audit` 是结构化敏感行为审计，已经具备较好的追责字段。
- 任务系统的部分审计信息存在于 `platform_task_log` 文本 output 中，属于“日志承载审计”，可查询但不够结构化。
- AIOps 的 `aiops_incident_analysis_record` 更偏 AI 决策留痕，不是第一阶段统一操作审计的核心来源。
- 一个关键发现是：系统里已有 `log_record` 这张“老统一日志表”，并且账号、组织、用户、站点等后台管理 API 已经在写它，还存在统一查询接口和前端查看入口。
- 因此，第一阶段最自然的方向不是废弃 `log_record`，而是在其基础上新增一个轻量统一审计查询层，把 `log_record` 与其他高价值审计来源一起聚合。
- 旧统一日志 `log_record` 的结构性问题很明显：
  - 时间字段 `CreatedTime` 和耗时字段 `ProcessTime` 都是字符串，不是标准时间/数值类型；
  - `PageList` 先全量查出所有记录，再在内存里分页，无法支撑增长后的审计量；
  - 记录缺少 `request_id`、请求路径、HTTP 方法、客户端 IP、来源系统、资源主键、租户等关键追责字段；
  - `RequestInfo` / `ResponseInfo` 是大文本，无法稳定做结构化筛选，且容易混入敏感信息；
  - 记录模型偏“后台管理操作日志”，无法自然承载 Device V2 字段级变更、终端会话、凭证使用、任务审计等异构场景；
  - 登录日志当前只记录成功登录，不记录失败登录，追责链条不完整。
- 旧设备历史 `device_history` 也存在明显问题：
  - 没有 `operator`、`source`、`request_id`、审批信息；
  - `confirm` 只有布尔值，没有“谁确认、何时确认、备注什么”；
  - 模型更偏“数据差异快照”，不是真正的责任审计事件；
  - 查询维度偏少，难以直接支持统一追责检索。
- 旧记录层面的共性问题：
  - 来源分散，字段语义不统一；
  - 很多记录没有稳定的 `resource_type` / `resource_id`；
  - 有些记录适合人看，不适合机器筛选；
- 不同来源的成功/失败/状态表达方式不一致；
- 老记录保留了事实，但不容易回答跨模块问题，例如“某个人今天到底改了哪些东西”。
- 用户已确认第一阶段可以暂缓处理 `device_history`，因为当前真正需要关注的资产操作入口在 Device V2，且 Device V2 入库后还会同步到 V1。这个判断能显著降低第一阶段统一审计的复杂度。

## Evidence

- 老设备历史：
  - `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/service/impl/device_history.go`
  - `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/device_model/device_history.go`
- Device V2 变更：
  - `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/service/impl/device_v2_change_history.go`
  - `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/model/device_v2_change_event.go`
  - `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/model/device_v2_change_field.go`
- 关系变更补写：
  - `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/platform/api/entity_relation.go`
- 终端会话记录：
  - `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/terminal/service/impl/terminal.go`
  - `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/terminal/terminal_model/terminal_record.go`
- 凭证行为审计：
  - `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/platform/service/impl/monitoring_task_v3_credential_audit_store.go`
  - `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/platform/platform_model/monitoring_v2_credential_audit_record.go`
- 任务日志审计摘要：
  - `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/platform/service/impl/task_log_audit_parser.go`
  - `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/platform/service/impl/oneops_bidi_service.go`
- 老统一日志：
  - `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/sys/service/impl/log_record.go`
  - `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/sys/sys_model/log_record.go`
  - `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/sys/api/log_record.go`
  - `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/security/access/api/login.go`
  - `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/sys/AllLogRecord.vue`
  - `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/components/LogRecord/LogModal.vue`
  - `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/account/api/account.go`

## Open Questions

- 第一阶段统一查询结果是否需要做严格分页，还是先接受“每个来源限流后内存合并排序”的轻量实现。
- 第一阶段是否要给 `log_record` 之外的来源补统一资源分类字段映射。
- 第一阶段是否顺手补一个统一查询 API 即可，暂不做统一写入表。
