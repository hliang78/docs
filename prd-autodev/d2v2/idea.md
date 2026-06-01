---
topic: d2v2
kind: full-stack
title: Device V2 运维入口迁移
createdAt: 2026-05-15T19:08:51+0800
program: true
---

# Idea

## Original Input

在设备 V2 清册围绕单台设备增加监控、WebShell、操作审计，并预留 Loki 日志；GPU 和带外日志不迁移；先同步 V2 到 V1，功能完全调用旧实现；前后端均可改旧代码但不得改变旧行为；不做兜底/降级/智能推断，问题尽早暴露；创建新的 OpenClaw 项目目录和短任务名方便微信指令。

## Known Constraints

- TBD
