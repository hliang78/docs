---
topic: generic-ai-autodev-platform
kind: full-stack
title: 后端迁移工具决策稿
createdAt: 2026-05-17T22:10:00+0800
program: true
status: draft
---

# Migration Tool Decision

## Purpose

- 这份文档专门冻结 `generic-ai-autodev/backend/` 的数据库迁移方式：
  - 是否复用 `dagengine` 现有自带迁移逻辑
  - 是否引入标准迁移工具
  - 迁移文件、执行入口、worker validation 应如何约束

## Current Code Facts

- 自动驾驶系统数据库边界已确认采用：
  - `同一 MySQL 实例 + 独立数据库`
- 自动驾驶系统核心真相层采用：
  - `MySQL + 文件系统`
- `dagengine` 当前并没有为自动驾驶系统直接提供可复用的独立迁移体系：
  - `v2/` 目录是执行内核，不等于自动驾驶系统 metadata schema
  - `it_ops/platform/database/connection.go` 中存在自定义迁移逻辑，但它绑定了旧平台初始化方式和内联 SQL
- 当前仓库没有统一采用 `goose`、`golang-migrate`、`atlas` 之类的现成标准作为通用规范

## Options

### Option A - 复用 `dagengine` 自定义迁移逻辑

不推荐。

原因：

- 现有逻辑绑定 `it_ops` 语义，不是为 `generic-ai-autodev` 设计
- 迁移定义偏内联，不利于 PRD/标准文档/代码评审同步
- 容易把旧平台历史结构和自动驾驶系统对象边界再次搅在一起

### Option B - 直接采用 ORM Auto-Migrate

不推荐。

原因：

- 当前阶段最需要的是结构化、可审阅、可追溯的 schema 演进
- Auto-migrate 容易把真实 DDL 变化藏进代码推断里
- 不利于后续 OpenClaw worker 做稳定、可重复的迁移校验

### Option C - 采用 SQL 文件 + 标准迁移引擎

推荐。

其中首选：

- `golang-migrate`

## Recommendation

- 首期采用：
  - `golang-migrate + 线性 SQL migrations + Go 命令包装入口`

## Confirmed Human Direction

- 最新人工确认已经接受：
  - `golang-migrate + 线性 SQL migrations`
- 因此迁移工具方向已从“推荐方向”升级为“当前冻结方向”。

一句话结论：

- 不复用 `dagengine` 的旧迁移实现，不使用 auto-migrate，首期用标准 SQL migration 链承接自动驾驶系统数据库演进。

## Why This Is The Best MVP Choice

## 1. 适合当前“对象先于代码”的节奏

- 当前我们已经先冻结了对象、状态、边界
- 用 SQL 文件能让表结构和对象决策一一对应
- 更方便把 `candidate-05` 与实际 schema 演进对齐

## 2. 对 worker 更稳定

- worker 执行迁移时，最怕“代码推断式 schema 演进”
- 明确的 migration 文件和固定命令更适合自动化执行、回放与验收
- 也更利于 `PlatformIncident` 排查数据库问题

## 3. 不把旧平台历史债带进来

- `dagengine` 当前包含 `old/`、`it_ops/`、`v2/` 等多套历史形态
- 如果复用旧迁移机制，容易把旧平台初始化思路连带继承
- 自动驾驶系统现在更需要干净、独立、最小化的 schema 纪律

## Recommended Shape

```text
generic-ai-autodev/
└── backend/
    ├── cmd/
    │   └── migrate/
    └── migrations/
        ├── 000001_init_core_tables.up.sql
        ├── 000001_init_core_tables.down.sql
        ├── 000002_add_profile_tables.up.sql
        └── 000002_add_profile_tables.down.sql
```

## Execution Recommendation

推荐执行入口：

- `generic-ai-autodev/backend/cmd/migrate`

推荐职责：

- 读取环境配置
- 指向独立数据库
- 执行 `up/down/version/status`
- 作为 worker validation 的统一迁移入口

推荐原则：

- OpenClaw story 的 `validation` 不直接调用零散 SQL
- 一律调用程序内统一迁移入口或其包装脚本

## File Strategy

- migration 文件采用纯 SQL
- 编号保持线性递增
- 不做多分支图式迁移
- 首期不引入复杂 schema diff 平台

## What Not To Do

### 1. 不复用 `it_ops` 的 migration table 设计

- 自动驾驶系统自己维护迁移状态
- 不和旧平台 migration history 混用

### 2. 不把 migration 藏进 seed 或 server 启动

- `server` 启动不自动做 destructive schema 变更
- schema 变化必须通过显式迁移入口执行

### 3. 不让 story 直接写初始化 SQL 到 shell 里

- 真实 DDL 变更必须进入 `backend/migrations/`
- 否则文档、代码、数据库三者仍会失同步

## Current Recommendation

1. 采用 `golang-migrate`
2. migration 文件放在 `generic-ai-autodev/backend/migrations/`
3. `backend/cmd/migrate` 作为唯一迁移执行入口
4. 采用线性 SQL migrations，不采用 auto-migrate
5. 不复用 `dagengine` 旧迁移逻辑或旧 migration history

## Remaining Decisions

1. 首个初始化 migration 的表切分顺序
2. `cmd/migrate` 是直接调用 `golang-migrate` library 还是包一层极薄 shell wrapper
