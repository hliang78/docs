---
topic: device-v2-onboarding-observability
kind: full-stack
title: Device V2 纳管观测闭环
createdAt: 2026-05-15T20:57:53+0800
program: true
---

# Idea

## Original Input

采集验证实际是采集入库。入库后自动同步 Device V1，并触发监控任务下发。还缺日志采集：服务器需部署 agent 后下发日志转发计划；网络设备需区域 agent 开启 syslog+snmp trap 监听，并远程配置设备指向该 agent；最后需验证 Prometheus 和 Loki 已收到指标、日志或 trap。

## Known Constraints

- TBD
