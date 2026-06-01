# 【数据库设计】OneOPS_DeviceV2纳管观测_v0.1

## 1. 文档信息

| 项目 | 内容 |
| --- | --- |
| 系统名称 | OneOPS |
| 模块名 | Device V2 纳管观测 |
| 版本号 | v0.1 |
| 文档状态 | 草案 |
| 关联文档 | 【需求概要】OneOPS_v0.1.md |

## 2. 设计原则

- 首期不新增数据库表，不新增迁移。
- 复用 `device_v2_store_run.summary_json` 保存纳管证据。
- 数据缺失或格式非法必须暴露错误，不做静默默认值。
- action 记录必须可重放、可审计、可支持 failed/unknown 重试。

## 3. 业务实体关系概览

### 3.1 核心实体识别

| 实体 | 中文名 | 业务含义 | 来源 |
| --- | --- | --- | --- |
| device_v2_store_run | Device V2 入库运行记录 | 保存采集入库及后续纳管证据 | 现有表 |
| onboarding.actions | 纳管动作证据 | 记录监控、日志、远程配置 action 结果 | summary_json |
| area_service_config | 区域基础服务配置 | 描述区域 agent 的 syslog/snmp trap 服务能力 | 配置文件 |

### 3.2 ER 关系说明

首期不新增实体关系。纳管动作作为 `device_v2_store_run.summary_json` 下的结构化 JSON 字段存在。

## 4. 数据表清单

### 4.1 表结构总览

| 表名 | 中文名称 | 变更类型 | 说明 |
| --- | --- | --- | --- |
| device_v2_store_run | Device V2 入库运行记录 | 复用 | 使用 `summary_json.onboarding.actions` |

### 4.2 详细表结构

#### 4.2.1 device_v2_store_run（Device V2 入库运行记录）

**本期字段变更**：无表结构变更。

**JSON 结构约定**：

```json
{
  "onboarding": {
    "actions": [
      {
        "id": "monitor.ensure",
        "category": "monitor",
        "target": "device",
        "method": "agent|snmp|syslog|ssh_plan",
        "status": "success|failed|unknown|skipped|planned",
        "timestamp": "2026-05-15T00:00:00+08:00",
        "evidence": {},
        "error": {
          "code": "string",
          "message": "string"
        }
      }
    ]
  }
}
```

**索引设计**：不新增索引。

## 5. 数据字典

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| category | string | `monitor` 或 `log` |
| method | string | 纳管方式，如 `agent`、`snmp`、`syslog`、`ssh_plan` |
| status | string | `success`、`failed`、`unknown`、`skipped`、`planned` |
| evidence | object | 下发、远程执行、配置计划等证据 |
| error | object | 失败或 unknown 的明确错误 |

## 6. 关键业务规则的数据支撑

| 规则 | 数据支撑 |
| --- | --- |
| 只重试 failed/unknown | action.status |
| 不重复执行 success | action.status |
| 无 agent 生成 SSH 计划 | action.status=planned + evidence.plan |
| 配置成功即成功 | action.status=success + evidence.result |

## 7. 数据量预估与扩展性说明

### 7.1 数据量预估

首期单设备手动执行，单次纳管 action 数量预计小于 10。

### 7.2 扩展性设计

若后续批量执行或 action 数量显著增长，再评估独立 action 表。本期不提前引入复杂状态表。

## 8. 待确认事项

| 序号 | 待确认内容 | 影响 |
| --- | --- | --- |
| 1 | syslog/snmp trap 是否升级为区域一级服务 | area_service_config 来源 |
| 2 | SNMP trap 模板结构 | action.evidence 字段 |
