---
topic: generic-ai-autodev-platform
kind: full-stack
title: 首期验证基线决策稿
createdAt: 2026-05-17T22:30:00+0800
program: true
status: draft
---

# Validation Baseline Decision

## Purpose

- 这份文档专门冻结首期 `generic-ai-autodev` 的验证基线：
  - story `validation` 应如何写
  - 前后端分别跑什么层级的校验
  - 是否直接写底层命令，还是统一走项目包装脚本

## Current Problem

- 旧系统的大量问题来自：
  - 环境命令不统一
  - 不同 story 直接写各自 shell
  - 工具链变化后，validation 文本和实际执行方式失同步
- 当前自动驾驶系统又明确把：
  - `WorkspaceProfile`
  - `ToolchainProfile`
  - `RuntimeEnvProfile`
  作为独立治理对象

因此验证命令不能再继续是“每个 story 自己临时发挥”。

## Recommendation

- 首期采用：
  - `项目级 wrapper scripts 作为 validation contract`

## Confirmed Human Direction

- 最新人工确认已经接受：
  - `项目级 wrapper scripts 作为 validation contract`
- 因此验证 contract 形式已经冻结，当前未冻结的只剩脚本内部命令与落地顺序。

一句话结论：

- story 的 `validation` 不直接写零散 `npm/go/mysql/curl` 命令，而是统一引用 `generic-ai-autodev/scripts/` 下的稳定入口。

## Recommended Validation Layout

```text
generic-ai-autodev/
└── scripts/
    ├── validate-frontend.sh
    ├── validate-backend.sh
    ├── validate-migrations.sh
    └── validate-mvp-readonly.sh
```

## Validation Contract

### `validate-frontend.sh`

职责：

- 承接前端 slice 的统一校验入口
- 内部再调用实际前端工具链命令

最低目标：

- 依赖完整性检查
- 类型检查
- lint
- build

### `validate-backend.sh`

职责：

- 承接后端 slice 的统一校验入口

最低目标：

- `go test ./...`
- 必要的静态检查
- API/模块编译通过

### `validate-migrations.sh`

职责：

- 检查 migration 文件可执行
- 检查数据库连接与迁移状态入口可用

最低目标：

- 指向自动驾驶系统独立数据库
- 执行迁移状态检查
- 在安全模式下验证 up/down 链可解释

### `validate-mvp-readonly.sh`

职责：

- 组合前端、后端、迁移和只读工作台 smoke test

首期目标：

- 证明 `Program -> Docs -> StoryBatch`
  的只读 + 审阅 + 状态推进主线至少具备基础通过条件

## Why Wrapper Scripts Are Required

## 1. 隔离工具链摇摆

- 前端未来即便从 `npm` 改成 `pnpm`
- 或后端从单命令改成多命令组合
- story `validation` 也不必全量返工

## 2. 适合 worker 自动执行

- worker 更适合收到稳定、短小、项目自带的命令
- 不适合每条 story 都手写一长串环境相关脚本

## 3. 与环境治理对象一致

- `ToolchainProfile` 管底层命令
- `validation` 引用项目级 contract
- 二者职责分离更清楚

## Validation Writing Rule

首期 story `validation` 应优先写成：

- `generic-ai-autodev/scripts/validate-frontend.sh`
- `generic-ai-autodev/scripts/validate-backend.sh`
- `generic-ai-autodev/scripts/validate-migrations.sh`
- `generic-ai-autodev/scripts/validate-mvp-readonly.sh`

而不是：

- 长串 `cd ... && npm run ...`
- 长串 `go test && go vet && curl ...`
- 临时写到 story 里的一次性 shell

## Temporary Rule Before Code Starts

- 在这些 wrapper scripts 尚未真正存在之前：
  - implementation batch 只能保持 `draft`
  - 不允许把 validation 文本伪装成已冻结可执行命令
- 也就是说：
  - 现在可以冻结“验证 contract 的形式”
  - 但不能假装“验证脚本已完成”

## Current Recommendation

1. validation 以项目级 wrapper scripts 为权威入口
2. 前端、后端、迁移、MVP 主线分别有独立验证脚本
3. story 不直接持有长串底层命令
4. wrapper 内部命令可随工具链演进，但 story contract 保持稳定
5. wrapper scripts 未落地前，implementation batch 继续保持 `draft`

## Remaining Decisions

1. 前端内部具体采用 `npm` 还是 `pnpm`
2. 后端静态检查组合是否包含 `go vet`
3. MVP 只读 smoke test 采用 CLI、API 还是 Browser 自动化为主
