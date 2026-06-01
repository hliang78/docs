---
topic: generic-ai-autodev-platform
kind: full-stack
title: 后端框架与进程模型决策稿
createdAt: 2026-05-17T17:55:00+0800
program: true
status: draft
---

# Backend Framework And Process Decision

## Purpose

- 这份文档专门冻结 `generic-ai-autodev/backend/` 的两个问题：
  - 首期后端到底用什么框架
  - 首期后端到底采用什么进程模型

## Current Code Facts

- `dagengine` 是 `Go 1.24.6`
- `dagengine` 当前 API 框架是 `gin`
- `dagengine` 已具备：
  - API server 骨架
  - process/task/ticket/execution 领域
  - MySQL driver 依赖
- 当前仓库没有现成的 `generic-ai-autodev` 后端实现，只有新目录壳和规划文档

## Recommendation

## 1. Language

- 首期后端采用：`Go`

### Why

- 与 `dagengine` 同语言，复用成本最低
- 避免再造一层 Node/Java 中间 API 去适配 Go 内核
- 对 `ProcessDefinition / Task / Ticket / Execution` 的调用可以直接走库级适配，而不是跨服务桥接

## 2. Web Framework

- 首期后端框架采用：`Gin`

### Why

- `dagengine` 已经在使用 `gin`
- API 分组风格、handler 组织方式、middleware 心智都能保持一致
- 首期重点不是框架创新，而是 planning/control/ops governance 对象落位

一句话：

- `generic-ai-autodev/backend/` 首期推荐为 `Go + Gin`

## 3. Process Model

- 首期采用：`单进程模块化单体`

### 含义

- 一个主 HTTP API 进程
- 一个代码库里的多模块分层
- 不拆成多个常驻服务
- 不引入额外消息队列 worker 进程

## 4. Recommended Process Shape

```text
backend/
├── cmd/
│   ├── server/
│   ├── migrate/
│   ├── seed/
│   └── readiness-recalc/
├── src/
│   ├── app/
│   ├── modules/
│   ├── adapters/
│   ├── domain/
│   └── shared/
└── scripts/
```

### `cmd/server`

- 唯一常驻 HTTP API 入口
- 对前端暴露：
  - program
  - documents
  - batches
  - readiness
  - profile summary
  - incident summary

### `cmd/migrate`

- 数据库迁移入口
- 不与主 API 进程耦合

### `cmd/seed`

- 开发阶段种子数据入口

### `cmd/readiness-recalc`

- 首期如果需要批量重算 readiness，可先用命令式入口
- 不急着做常驻异步 worker

## 5. Why Not Multi-Process First

如果首期就拆成：

- API 进程
- readiness worker
- repair orchestrator daemon
- ops governance service

会立刻引入：

- 多端口
- 多日志源
- 多配置文件
- 多启动脚本
- 多健康检查
- 多部署顺序

这和首期要解决的问题不匹配。

首期当前真正要解决的是：

1. 对象和状态冻结
2. 前端工作台闭环
3. `dagengine` 内核适配
4. profile / incident / readiness 的统一读取

这些都不需要先拆多进程。

## 6. How To Handle Async In MVP

- 首期默认不引入 `BullMQ`
- 首期默认不引入独立后台 worker 服务

如果出现轻异步需求，优先级按下面走：

1. 同进程同步处理
2. 同代码库 CLI 命令处理
3. 同进程轻量 goroutine / job dispatcher
4. 最后再考虑独立异步进程或队列

## 7. Repair Process Recommendation

- `SuperRepairCoordinator` 首期不作为独立常驻服务
- 它先作为 `backend/modules/repair` 内的模块存在
- 由以下入口触发：
  - API 调用
  - CLI 命令
  - 后续需要时再升级成后台任务

这能避免 repair 在 MVP 阶段提前演变成第二套平台。

## 8. Dagengine Integration Recommendation

- 首期优先采用：`库级适配`
- 即：
  - `backend/adapters/dagengine`
  - 直接在 Go 代码里调用 `dagengine` 能力

首期不优先采用：

- 先把 `dagengine` 当远程独立服务再 HTTP 调用

### Why

- 同语言同进程更容易稳定
- 少一层网络、鉴权、重试、错误映射
- 更适合当前仍在代码前冻结 contract 的阶段

## 9. API Runtime Model

- 首期一个 HTTP API 进程即可
- 不做 gateway + internal services 拆分

建议 API 分组：

- `/api/v1/programs`
- `/api/v1/documents`
- `/api/v1/batches`
- `/api/v1/reviews`
- `/api/v1/profiles`
- `/api/v1/ops-summary`

但这些都由同一个后端进程暴露。

## 10. Logging And Config Recommendation

- 首期配置集中在 `backend/` 单一配置体系
- 不分裂成多服务配置
- 日志也优先集中输出

这样对 repair、incident、probe 的排查更友好。

## 11. Current Recommendation

1. 首期后端语言采用 `Go`
2. 首期 Web 框架采用 `Gin`
3. 首期进程模型采用 `单进程模块化单体`
4. `SuperRepairCoordinator` 首期先做模块，不做独立常驻服务
5. `dagengine` 首期优先做库级适配，不先做远程服务桥接

## 12. Remaining Decisions

1. `backend/` 的具体目录命名是否接受 `cmd/ + src/ + scripts/`
2. 数据库迁移工具使用什么方案
3. `dagengine` 是直接 vendor/import，还是通过主仓相对引用方式接入
