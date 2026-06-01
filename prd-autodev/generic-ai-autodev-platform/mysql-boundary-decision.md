---
topic: generic-ai-autodev-platform
kind: full-stack
title: MySQL 边界决策稿
createdAt: 2026-05-17T18:15:00+0800
program: true
status: draft
---

# MySQL Boundary Decision

## Purpose

- 这份文档专门冻结自动驾驶系统的 MySQL 边界：
  - 是否与现有 OneOPS 共库
  - 是否独立库
  - 是否需要独立 MySQL 实例

## Important Clarification

- 在 MySQL 语义里，`schema` 与 `database` 基本等价。
- 所以前面文档里写的“独立 schema”，在这里统一按“独立数据库”理解。

也就是说，当前真正有意义的 3 个选项是：

1. 同实例、同数据库、只靠表前缀隔离
2. 同实例、独立数据库
3. 独立 MySQL 实例

## Recommendation

- 首期采用：`同一 MySQL 实例 + 独立数据库`

当前确认命名：

- `oneops_ai_autodev`

一句话结论：

- 不共库表，不新起独立实例，先走“同实例独立数据库”。

## Confirmed Human Direction

- 最新人工确认已经接受：
  - `同实例独立库`
- 因此这份决策文档中的数据库边界已经从“推荐方向”升级为“当前冻结方向”。
- 当前已进一步确认：
  - 数据库命名采用 `oneops_ai_autodev`
  - 迁移工具采用 `golang-migrate + 线性 SQL migrations`
  - validation contract 采用项目级 wrapper scripts
- 当前仍未最终冻结的仅剩：
  - 首批初始化 migration 的切分顺序
  - 首批验证脚本的具体落地顺序

## Why This Is The Best MVP Choice

## 1. 比共库更安全

如果采用“同数据库共表”：

- 会污染现有 OneOPS 业务库语义
- 容易出现表名、迁移、权限、脚本误操作冲突
- 自动驾驶系统对象边界会被旧系统历史债拖住

而自动驾驶系统当前最需要的是：

- 独立对象真相层
- 独立迁移节奏
- 独立 repair / incident / readiness 模型

这些都不适合和现有业务表混在一个数据库里。

## 2. 比独立实例更轻

如果首期直接独立 MySQL 实例：

- 运维成本会明显增加
- 连接、备份、权限、监控、迁移都要先多一套
- 对当前 MVP 的收益不够大

当前阶段更需要：

- 先把对象层和文档层分清
- 先把程序目录和后端进程模型收稳
- 先把 program/docs/batch 工作台跑通

所以独立实例太重。

## 3. 保留未来升级空间

同实例独立数据库的好处是：

- 现在轻
- 后续若数据量、安全边界、团队边界需要升级，再迁到独立实例也不晚

这和当前整体策略一致：

- 先做边界清楚的 MVP
- 不提前做重运维架构

## What This Means

## A. 数据库边界

- 自动驾驶系统所有 authoritative objects 都进入新数据库
- 不复用旧 OneOPS 业务库里的表
- 不允许把自动驾驶系统核心对象直接插进现有历史表体系

## B. 迁移边界

- `generic-ai-autodev/backend/cmd/migrate` 只管理新数据库
- 不修改主仓旧业务库迁移链
- 自动驾驶系统迁移编号、表命名、回滚策略独立维护

## C. 权限边界

- 建议独立 DB user
- 该 user 只对新数据库有 DDL / DML 权限
- 不直接复用主业务库高权限账号

## D. 表命名边界

- 既然已独立数据库，就不需要过度依赖超长表前缀
- 仍建议采用清楚但简洁的对象名：
  - `programs`
  - `planning_documents`
  - `story_batches`
  - `worker_profiles`
  - `platform_incidents`

## E. 连接边界

- 应允许和现有 OneOPS 共用同一个 MySQL server 地址
- 但连接串中的 database 必须指向新数据库

## What Not To Do

以下方案首期不推荐：

### 1. 共库共表

- 不推荐
- 原因：边界太脆弱

### 2. 共库但大量表前缀隔离

- 不推荐
- 原因：表前缀不能替代数据库边界

### 3. 一开始独立 MySQL 实例

- 不推荐
- 原因：MVP 阶段运维重量过高

## Naming Recommendation

当前已确认数据库名：

- `oneops_ai_autodev`

原因：

- 相比更长的命名更简洁
- 仍然保留 `OneOPS + AI AutoDev` 的归属感与识别度

## Migration Recommendation

- 迁移文件放在：
  - `generic-ai-autodev/backend/migrations/`
- 迁移执行入口：
  - `generic-ai-autodev/backend/cmd/migrate/`
- 首期先保持简单线性迁移，不急着做复杂多分支迁移图

## Current Recommendation

1. 接受“同一 MySQL 实例 + 独立数据库”
2. 不接受“同数据库共表”
3. 首期不要求独立 MySQL 实例
4. 数据库命名采用 `oneops_ai_autodev`
5. 自动驾驶系统 migrations 独立维护，不挂入旧 OneOPS 迁移链
