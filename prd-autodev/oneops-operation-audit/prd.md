---
topic: oneops-operation-audit
kind: backend
title: OneOPS 操作审计 PRD
createdAt: 2026-05-21T15:10:00+0800
---

# OneOPS 操作审计 PRD

## 当前真实代码事实

- 旧后台日志主入口是 `log_record`，接口与页面分别在：
  - [log_record.go](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/sys/api/log_record.go)
  - [LegacyLogRecord.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/sys/LegacyLogRecord.vue)
- Device V2 已有结构化变更审计：
  - [device_v2_change_event.go](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/model/device_v2_change_event.go)
  - [device_v2_change_field.go](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/model/device_v2_change_field.go)
- 终端会话已有 `terminal_records`：
  - [terminal_record.go](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/terminal/terminal_model/terminal_record.go)
- Monitoring V2 已有凭证审计：
  - [monitoring_v2_credential_audit_record.go](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/platform/platform_model/monitoring_v2_credential_audit_record.go)
- 任务材料解析审计摘要存在于 `platform_task_log`：
  - [platform_task_log.go](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/platform/platform_model/platform_task_log.go)
  - [task_log_audit_parser.go](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/platform/service/impl/task_log_audit_parser.go)
- 当前资产变更主入口已经迁移到 Device V2；`device_history` 暂不作为第一阶段重点来源。

## 目标

- 提供一个统一查询入口，能跨来源回答“谁改了什么”。
- 第一阶段避免做成新平台，只做轻量聚合查询层。
- 前端以正式“操作审计”页承载统一查询，同时保留 legacy 兼容页。

## 非目标

- 不新建复杂审计中心、消息队列、异步事件总线。
- 不改写现有各模块写入逻辑。
- 不新建复杂前端子系统。
- 不处理 `device_history` 兼容收敛。

## 第一阶段范围

### 后端来源

1. `device_v2_change_event`
2. `log_record`
3. `terminal_records`
4. `platform_monitoring_v2_credential_audit`
5. `platform_task_log` 中 `task_material_resolve`

### 前端交付

- 正式页面文件：[OperationAudit.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/sys/OperationAudit.vue)
- 兼容页面文件：[LegacyLogRecord.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/sys/LegacyLogRecord.vue)
- 新 API 文件
- 新 typings 文件
- 兼容隐藏路由：`/#/sys/log-record-legacy`

## 统一审计模型

统一列表项字段：

- `source_type`：来源表/来源类型
- `module`：统一模块域
- `action`：操作动作
- `operator`：操作者
- `resource_type`：资源类型
- `resource_id`：资源标识
- `summary`：人可读摘要
- `status`：来源状态
- `risk_level`：风险等级（优先给 Device V2）
- `source`：来源子类型
- `source_label`：来源子类型中文描述
- `occurred_at`：发生时间
- `raw_ref`：原始表 + 原始主键
- `detail`：预览详情

## 查询条件

- `page_num`
- `page_size`
- `module`
- `source_type`
- `operator`
- `resource_type`
- `status`
- `keyword`
- `start_time`
- `end_time`

## 页面策略

操作审计页承担：

- 统一筛选
- 统一列表
- 展开预览详情

不承担：

- 审计治理闭环
- 复杂统计报表

## 技术方案

### 后端

- 新增 `sys/unifiedAudit` 路由组
- 新增 `UnifiedAuditAPI`
- 新增 `UnifiedAuditSrv`
- 使用现有数据库连接按来源聚合查询
- 各来源先做读时标准化映射，再统一排序分页

### 前端

- 正式页为 `OperationAudit.vue`
- 兼容页为 `LegacyLogRecord.vue`
- 动态路由层把现有 `LogRecord` 菜单重写到新页
- legacy 页通过隐藏路由保留

## 风险

- 各来源状态语义不同，第一阶段只做轻量统一，不强制同义。
- `log_record` 与任务日志的结构化质量较弱，详情以预览为主。
- 第一阶段已经完成菜单切换，但仍然不是最终审计平台终态。

## 验收标准

1. 后端存在新的统一审计查询接口。
2. 至少能查询并返回 5 类来源的标准化列表项。
3. 前端存在正式操作审计页和 legacy 兼容页。
4. 现有 `LogRecord` 菜单已完成切换，旧日志页可通过隐藏路由回退。
5. 可以按时间、模块、来源、操作者、关键字进行基础筛选。

## OpenClaw Story Package

```json
{
  "program": "oneops-operation-audit",
  "batch": "batch-001",
  "title": "操作审计最小实现",
  "status": "draft",
  "stories": [
    {
      "id": "AUDIT-001",
      "title": "实现统一操作审计聚合查询接口",
      "status": "open",
      "lanes": ["d2-be"],
      "scope": "新增 sys/unifiedAudit 接口，聚合 Device V2、log_record、terminal_records、monitoring credential audit、platform_task_log(task_material_resolve) 五类来源，并返回统一列表项。",
      "nonGoals": ["统一写入", "旧 device_history 收敛", "复杂报表"],
      "allowedPaths": [
        "OneOPS/app/sys/api",
        "OneOPS/app/sys/router",
        "OneOPS/app/sys/service/impl",
        "OneOPS/app/sys/dto",
        "OneOPS/boot/provider",
        "OneOPS/initialize",
        "OneOPS/cmd"
      ],
      "acceptance": [
        "存在新的统一查询接口",
        "统一结果包含来源表标识与原始引用",
        "支持基础过滤与时间倒序"
      ],
      "validation": [
        "cd /Users/huangliang/project/OneOPS-ALL/OneOPS && go test ./app/sys/..."
      ]
    },
    {
      "id": "AUDIT-002",
      "title": "实现操作审计正式页与 legacy 兼容页",
      "status": "open",
      "lanes": ["d2-fe"],
      "scope": "新增 OperationAudit.vue、保留 LegacyLogRecord.vue、完成 LogRecord 菜单入口切换，并保留隐藏兼容路由。",
      "nonGoals": ["重做整套审计 UX", "完全下线 legacy 日志页"],
      "allowedPaths": [
        "OneOPS-UI/src/views/sys",
        "OneOPS-UI/src/api/sys",
        "OneOPS-UI/src/typings/sys",
        "OneOPS-UI/src/router"
      ],
      "acceptance": [
        "正式操作审计页存在且作为主入口可访问",
        "legacy 兼容页可通过隐藏路由访问",
        "页面支持基础筛选和展开详情"
      ],
      "validation": [
        "cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run build"
      ]
    }
  ]
}
```
