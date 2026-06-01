---
documentStatus: blocked-human-confirmation
topic: generic-ai-autodev-platform
template: 01-需求概要模板
createdAt: 2026-05-17
sourceType: planning-mining
---

# 【需求概要】通用AI自动化平台_V1.0

## 1. 文档信息

| 项目 | 内容 |
|------|------|
| 系统名称 | 通用 AI 自动化平台 |
| 版本号 | V1.0 |
| 创建日期 | 2026-05-17 |
| 需求来源 | 基于 `dagengine` 重构通用 AI 自动化体系，并对 `prd-autodev`、`openclaw-autodev` 做挖矿重构 |
| 编写人 | Codex |

## 2. 业务背景与目标

### 2.1 业务背景

OneOPS 当前已经存在：

- `docs/prd-autodev` 的规划资产
- `docs/openclaw-autodev` 的执行控制资产
- `dagengine` 的执行引擎资产

但这些能力仍分散在不同目录、脚本、文档和运行模式中，缺少统一的通用平台承载。当前最直接的问题不是“再做一个功能页”，而是要先把规划平面、控制平面、执行平面分层抽象出来，再逐步沉淀成平台。

### 2.2 业务目标

| 目标编号 | 业务目标 | 价值说明 | 衡量方式 |
|----------|----------|----------|----------|
| G-001 | 构建首期可跑通的通用 AI 自动化平台 MVP | 形成统一规划与后续自动开发入口 | 形成 reviewed planning slice 与第一批可执行 OpenClaw batch ready |
| G-002 | 用前端承接 `program -> docs -> batch` 最小闭环 | 让规划者在 Web 界面中完成审阅、状态推进、发布准备 | 首页可完成 program 列表、文档浏览、batch 审核 |
| G-003 | 将 `dagengine` 固定为执行引擎内核 | 避免平台边界反复摇摆 | 后端规划明确可复用内核与新增对象边界 |
| G-004 | 用标准模板约束需求/开发/测试文档 | 让 AI 与人协作过程可持续沉淀 | 首批 `01-07` 候选文档形成并允许后续修订 |
| G-005 | 把 worker 执行环境治理对象化 | 避免目录、账号、工具、env vars、helper tools 再次隐式漂移 | 冻结 profile / probe / incident 对象与边界 |
| G-006 | 分离业务层与基础设施层 blocker | 避免 PRD、执行、repair 继续混流 | blocker taxonomy 与 route matrix 固化 |
| G-007 | 预留超级修复代理机制 | 平台机制中断时可恢复、可审计、可升级 | 定义 `SuperRepairCoordinator` 与 incident/repair 流程 |

## 3. 用户角色

| 角色 | 描述 | 主要职责 | 使用终端 |
|------|------|----------|----------|
| 规划者 | 负责整理需求、审阅 PRD、拆分 batch 的用户 | 查看 program、审阅文档、推进 batch readiness | Web |
| 架构负责人 | 负责确认 planning/control/runtime 边界 | 审核对象模型、接口边界、内核映射 | Web/文档 |
| 前端负责人 | 负责确认前端闭环与页面信息架构 | 审阅原型、页面状态、交互约束 | Web/文档 |
| 后端负责人 | 负责确认 `dagengine` 复用边界与平台后端结构 | 审阅内核映射、API 契约、开发设计 | Web/文档 |
| 测试负责人 | 负责确认测试文档和后续验证闭环 | 审阅测试矩阵、测试用例、自动化脚本说明 | Web/文档 |
| 平台运维负责人 | 负责确认运行环境、账号、工具链、修复机制边界 | 审阅 profile、probe、incident、repair 方案 | Web/文档 |

## 4. 功能需求

### 4.1 首期规划管理闭环

- 功能点1：展示 `topic/program` 列表与详情。
- 功能点2：展示 `context-brief`、`program-plan`、`workstreams`、`test-matrix`、`review`、`final-readiness` 等规划文档。
- 功能点3：展示 batch/stories 状态与 readiness。

### 4.2 文档审阅与状态推进

- 功能点1：识别 `draft/reviewed/ready for OpenClaw` 等状态。
- 功能点2：支持只读审阅、待确认事项提醒。
- 功能点3：支持 review / blocked-human-confirmation / publish-ready 相关状态推进。

### 4.3 运行环境与配置治理

- 功能点1：首批展示 worker、workspace、toolchain、credential、runtime env 等 profile 摘要，并为后续完整管理留出承载位。
- 功能点2：在 story 执行前提供 preflight probe 结果。
- 功能点3：把 helper tools 纳入结构化治理，而不是散落在脚本和备注里。

### 4.4 平台后端重构规划

- 功能点1：明确 `dagengine` 内核复用边界。
- 功能点2：明确 `openclaw` 控制平面对象。
- 功能点3：明确 `prd` 规划平面对象。

### 4.5 平台修复与恢复治理

- 功能点1：分类基础设施 blocker 与机制性 incident。
- 功能点2：提供 repair run 跟踪与恢复结果。
- 功能点3：预留 `SuperRepairCoordinator` 的状态观察与升级入口。

## 5. 非功能需求概要

### 5.1 性能需求

| 指标 | 要求 | 备注 |
|------|------|------|
| Program 首页响应 | [待确认: 前端负责人] | 首期以可用性优先 |
| 文档切换响应 | [待确认: 前端负责人] | 首期以可读性优先 |

### 5.2 可用性需求

首期平台要优先保证规划流程清晰、状态可识别、文档可追踪，而不是覆盖所有控制台能力。

### 5.3 可恢复性需求

- 平台必须能区分业务失败与基础设施失败。
- 修复后必须重新 probe，不能直接无验证重试。
- 超级修复代理的动作必须可审计。

### 5.4 安全性需求

- 首期不开放高风险运行控制。
- credentials 不允许散落在 markdown、story、report 中。
- AI 优化与轻量编辑都应有边界，不得绕过人工确认。

### 5.5 可扩展性需求

平台后续需要扩展到：

- 模型/profile 配置管理
- OpenClaw 运行控制
- approval/repair 可视化

## 6. 关键业务规则

| 规则编号 | 业务规则 | 触发场景 | 处理要求 |
|----------|----------|----------|----------|
| R-001 | 规划阶段优先多轮、多角度挖矿 | 进入新平台重构 program 时 | 先 research/抽象/标准化，再进入开发 |
| R-002 | `dagengine` 首期只作为执行引擎内核 | 后端架构设计 | 不把它直接当成完整平台替身 |
| R-003 | 首期前端聚焦 `PRD/story 文档与批次管理` | 前端 MVP 设计 | 不混入模型/profile 配置主线 |
| R-004 | 首批标准文档优先 `01-07` | 文档路线设计 | `08-10` 后续阶段补齐 |
| R-005 | 文件不是核心真相层 | 存储与状态设计 | 核心对象进 MySQL，文件只做 evidence/export/cache |
| R-006 | 基础设施 blocker 不回流 PRD | blocked / repair 场景 | 默认进入 `Repair / SuperRepair` |
| R-007 | 首批代码切片不包含 AI 优化与轻量编辑 | 前端 batch-001 | 先把工作台与状态闭环跑通 |

## 7. 系统边界与约束

### 7.1 系统边界

| 范围 | 内容 |
|------|------|
| 包含范围 | 规划闭环、文档审阅、batch readiness、内核映射 |
| 不包含范围 | 首期不做完整 OpenClaw 运行台；不做 AI 优化/轻量编辑；不做全量运行控制 |
| 外部依赖 | `dagengine`、`docs/prd-autodev`、`docs/openclaw-autodev`、`docs/development-doc-templates` |

### 7.2 约束条件

| 约束类型 | 约束内容 | 影响 |
|----------|----------|------|
| 技术约束 | 必须以 `dagengine` 为执行内核候选 | 后端结构不能完全另起炉灶 |
| 过程约束 | reviewed PRD/batch 前不启动 OpenClaw 正式开发 | 必须先补足 planning slice |

## 8. 用户故事

### 8.1 规划者用户故事

#### 8.1.1 浏览与推进一个 program

- Web：规划者打开首页查看 program 列表与当前阶段。
- Web：进入某个 program 后阅读 context-brief、program-plan、workstream、test-matrix。
- Web：打开 batch 审核视图，判断是否 ready for OpenClaw。

#### 8.1.2 审阅运行环境 readiness

- Web：平台运维负责人查看某个 lane 绑定的 `WorkerProfile / RuntimeEnvProfile`。
- Web：查看最近一次 preflight probe 和 incident 摘要。
- Web：判断当前 batch 是否具备进入执行阶段的环境前提。

## 9. 关键业务名词

| 名词 | 解释 | 备注 |
|------|------|------|
| Program | 一个独立规划主题的根对象 | 对应一个 topic 目录 |
| StoryBatch | 规划平面下发给执行平面的批次切片 | 进入 OpenClaw 前需 reviewed |
| RuntimeStory | 执行控制平面的最小 bounded story | 不等于 planning batch |
| ExecutionPack | story 编译后的真实 worker 输入 | 来自控制平面 |
| RuntimeEnvProfile | 对某条 lane 生效的运行环境画像 | 组合目录、工具、凭据、能力 |
| PlatformIncident | 平台机制层事故 | 不等于业务 blocker 备注 |

## 10. 待确认事项

| 序号 | 待确认内容 | 影响范围 | 负责人 | 状态 |
|------|------------|----------|--------|------|
| 1 | Program 工作台的路由/多标签模式 | 前端架构 | 前端负责人 | 待确认 |
| 2 | 首期显示 profile / incident 的只读摘要入口 | 前端信息架构 | 产品负责人 | 已确认 |
| 3 | reviewed batch ready 的最终判定界面表现 | 前端/规划 | 产品负责人 | 待确认 |
| 4 | `WorkspaceProfile / ToolchainProfile / CredentialBinding` 独立建模 | 后端/运维 | 架构负责人 | 已确认 |
| 5 | `SuperRepairCoordinator` 只处理平台机制恢复，不处理业务 scope | 平台机制 | 架构负责人 | 已确认 |

## 11. 当前真实规划事实

- 首期是 MVP。
- 前端首期优先 `PRD/story 文档与批次管理`。
- `dagengine` 被限定为执行引擎内核。
- 标准文档首批优先 `01-07`。
- 当前阶段先做到代码阶段前，不启动正式开发。
- 首批代码切片只做 `只读 + 审阅 + 状态推进`。
- 运行环境治理、业务/基础设施分层、超级 repair agent 已上升为架构级约束。

## 12. AI 推导建议

- 首页可采用工作台型信息架构，而不是多系统菜单型入口。[待人工确认: 产品负责人]
- planning/control/runtime/evidence 四平面应在后续文档中持续保持一致命名。[待人工确认: 架构负责人]
- profile / incident 摘要作为首期只读能力已确认，复杂编辑台后移到后续 batch。

## 13. 规划缺口

- 首期 API 资源边界还未最终定稿。
- 首期候选 lane 的职责粒度仍需再收束。
- `profile / incident` 只读摘要挂在右栏还是独立 `Ops Mode`，仍待前端专题讨论。

## 14. 代码事实来源清单

### 已读取关键文件

- `docs/prd-autodev/generic-ai-autodev-platform/program-plan.md`
- `docs/prd-autodev/generic-ai-autodev-platform/context-brief.md`
- `docs/prd-autodev/generic-ai-autodev-platform/alignment.md`
- `docs/prd-autodev/generic-ai-autodev-platform/dagengine-kernel-mapping.md`
- `docs/prd-autodev/generic-ai-autodev-platform/openclaw-control-plane-mapping.md`
- `docs/prd-autodev/generic-ai-autodev-platform/runtime-governance-and-super-repair.md`

### 文件对应事实类型

- program 边界
- planning/control/runtime 抽象
- 首期 MVP 已确认决策

### 仍未读取或无法确认的范围

- 实际前端代码承载位置
- profile 只读摘要与后续编辑边界的最终取舍
