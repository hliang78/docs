---
topic: generic-ai-autodev-platform
kind: full-stack
title: dagengine 接入组织决策稿
createdAt: 2026-05-17T22:20:00+0800
program: true
status: draft
---

# Dagengine Integration Decision

## Purpose

- 这份文档专门冻结自动驾驶系统如何接入 `dagengine`：
  - 接入到什么层
  - 复用哪些包
  - 明确不复用哪些历史形态
  - Go module import 关系如何组织

## Current Code Facts

- `dagengine` 是独立 Go module：
  - `module github.com/netxops/dagengine`
- `dagengine` 当前工程内部并不完全“纯内核”：
  - `cmd/server` 混有 `old`、`it_ops`、基础设施启动逻辑
  - `v2/api` 提供了一套自己的 HTTP API server
  - `v2/engine`、`v2/interfaces` 更接近我们要复用的执行内核层
- 自动驾驶系统当前方向已明确：
  - `dagengine` 只是执行引擎内核
  - 前端与规划/控制对象不直接耦合 `dagengine` 原始 API
  - 自动驾驶系统 authoritative truth 不写回 `dagengine` 充当业务真相层

## Recommendation

- 首期采用：
  - `库级接入 + 本地 adapter anti-corruption layer`

## Confirmed Human Direction

- 最新人工确认已经接受：
  - `dagengine 只做库级接入`
- 因此这份接入策略中的高层边界已经冻结：
  - 不复用 `dagengine` 现成 server
  - 不把 `dagengine` 直接暴露成前端 contract

一句话结论：

- 自动驾驶系统不嵌入 `dagengine` 的现成 server，也不直接把 `v2/api` 暴露给前端，而是在 `backend/src/adapters/dagengine/` 中选择性吸收执行内核能力。

## What To Reuse

首期优先复用的目标层：

- `github.com/netxops/dagengine/v2/engine`
- `github.com/netxops/dagengine/v2/interfaces`
- `github.com/netxops/dagengine/pkg/logging`

后续按需谨慎评估：

- `v2/task`
- `v2/ticket`
- `v2/scheduler`

## What Not To Reuse Directly

首期明确不直接复用：

- `dagengine/cmd/server`
- `dagengine/v2/api`
- `dagengine/old`
- `dagengine/it_ops`
- 任意把 MongoDB、Redis、Etcd、旧 Web UI 一起拉进来的启动路径

原因：

- 这些层包含大量历史平台语义和基础设施假设
- 会把自动驾驶系统重新拖回“大而混”的结构
- 与当前“规划面/控制面在上，执行内核在下”的架构方向冲突

## Recommended Adapter Shape

```text
generic-ai-autodev/backend/src/adapters/dagengine/
├── compiler/
├── runner/
├── query/
├── mapping/
└── internal/
```

## Role Of Each Adapter Part

### `compiler/`

- 把 `RuntimeStory / ExecutionPack` 编译为 `dagengine` 可执行定义
- 负责自动驾驶系统对象到 DAG process/node 的映射

### `runner/`

- 启动执行
- 查询执行状态
- 停止或取消执行

### `query/`

- 读取执行结果、执行摘要、节点状态投影
- 输出给 planning/control/readiness 层消费

### `mapping/`

- 统一字段转换
- 不允许业务模块到处直接操作 `dagengine` 原始结构

### `internal/`

- 放 adapter 私有 glue code
- 不向业务模块直接暴露

## Module Import Recommendation

推荐自动驾驶系统后端作为独立 Go module，并在 MVP 阶段采用本地 `replace`：

```go
require github.com/netxops/dagengine v0.0.0

replace github.com/netxops/dagengine => ../../dagengine
```

原因：

- 保持 `generic-ai-autodev/backend` 依赖边界独立
- 不需要复制 `dagengine` 源码
- 比相对路径 import 或手工 vendor 更干净
- 后续如果 `dagengine` 抽到独立版本仓，迁移成本更低

## API Boundary Recommendation

- 前端只调用：
  - `planner/control API`
- `planner/control API` 再调用：
  - `backend/src/adapters/dagengine/*`
- 不允许前端直接消费 `dagengine/v2/api`
- 不允许把 `dagengine` route shape 当成前端 contract

## Persistence Boundary Recommendation

- planning/control/governance truth 存自动驾驶系统 MySQL
- `dagengine` 只承接 execution kernel data
- 如需 execution 投影，先经 adapter/query 做映射后再进入自动驾驶系统 summary

## Why This Is The Best MVP Choice

## 1. 保住三平面边界

- `PRD/planning`
- `OpenClaw/control`
- `dagengine/execution`

三者如果直接共用一套 server 或 route，会再次混成补丁式平台。

## 2. 降低历史包袱渗透

- `dagengine` 当前历史目录很多
- adapter 层是必要的隔离带
- 否则任何一次 `dagengine` 内部改动都可能直接冲击自动驾驶系统 API

## 3. 更适合后续 repair 与 readiness

- 自动驾驶系统需要自己的 `PlatformIncident`、`PreflightProbe`、`RepairRun`
- 这些对象不能被 `dagengine` 既有 server 语义绑架

## Current Recommendation

1. 自动驾驶系统只做库级接入，不复用 `dagengine` 现成 server
2. 仅选择性复用 `v2/engine`、`v2/interfaces`、`pkg/logging`
3. 在 `backend/src/adapters/dagengine/` 建立 anti-corruption layer
4. `backend/go.mod` 通过 `replace github.com/netxops/dagengine => ../../dagengine` 接本地源码
5. `dagengine` 执行状态必须经 adapter 投影后再进入前端或 readiness

## Remaining Decisions

1. 首期是否需要直接复用 `v2/task` / `v2/ticket`
2. 首个 compiler 只覆盖哪一类 execution pack
3. `dagengine` 执行 persistence 是否读取现成能力，还是首期只做最小查询投影
