---
topic: device-v2-onboarding-observability
kind: full-stack
title: Device V2 纳管观测闭环决策记录
status: confirmed
---

# Decisions

## 2026-05-15 基础方案确认

1. 首期 `继续纳管` 只对单台设备执行。批量只生成计划或逐台展示结果，不做并发远程配置。
2. 网络设备远程配置 syslog/trap target 后自动保存配置。
3. 网络设备日志纳管首期优先 syslog。SNMP trap 先做一级定义和 teleabs 模板缺口，不阻塞 syslog 首期。
4. 服务器监控方式由用户选择 agent / SNMP。
5. 服务器日志纳管：有 agent 时优先 agent；无 agent 时生成 SSH 配置计划。
6. Linux 系统日志默认文件：
   - `/var/log/syslog`
   - `/var/log/auth.log`
   - `/var/log/messages`
   - `/var/log/secure`
7. 系统日志策略模式为 `first_existing`：存在就采，不存在不报错。
8. FunctionArea 区域基础服务定义首期先放配置文件，不建表。
9. 再次点击 `继续纳管` 时，只重试 `failed` / `unknown` 的 ensure，不重复执行已成功 action。

## 暂缓决策

- 区域基础服务配置文件的最终路径和 schema。
- 网络设备各厂商 syslog 配置命令模板。
- 服务器 SNMP 开启模板。
- 服务器 SSH 日志转发配置模板。

## 2026-05-18 Scope 升级确认

1. `batch-012` 保持为配置/回读闭环完成，不重新打开。
2. 新范围要求数据面查询闭环：指标必须在 Prometheus 查询出来。
3. 日志数据面统一由 Loki 查询验证，至少覆盖：
   - 服务器本地日志
   - 服务器 syslog 日志
   - 网络设备 syslog 日志
   - 网络设备 SNMP trap 日志
4. Live 查询端点：
   - Prometheus: `http://192.168.0.164:9090`
   - Loki: `http://192.168.0.164:3100`
5. Prometheus/Loki 查询失败、无样本、标签无法定位、采集任务未产生数据必须分开记录为 evidence，不允许把配置成功直接 paraphrase 成数据面成功。
