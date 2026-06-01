---
documentStatus: blocked-human-confirmation
topic: generic-ai-autodev-platform
template: 02-功能清单模板
createdAt: 2026-05-17
sourceType: planning-mining
---

# 【功能清单】通用AI自动化平台_规划管理子系统_V1.0

## 1. 文档信息

| 项目 | 内容 |
|------|------|
| 系统名称 | 通用 AI 自动化平台 |
| 版本号 | V1.0 |
| 创建日期 | 2026-05-17 |
| 关联文档 | 【需求概要】通用AI自动化平台_V1.0.md |

## 2. 功能模块清单

| 模块编号 | 模块名称 | 功能项 | 优先级 | 说明 |
|----------|----------|--------|--------|------|
| F-01 | Program 管理 | Program 列表与详情 | P0 | 首期首页最小闭环入口 |
| F-02 | 文档管理 | `context-brief/program-plan/workstreams/test-matrix/review` 浏览与状态识别 | P0 | 首期以只读审阅为主 |
| F-03 | Batch 管理 | batch/stories 浏览、状态推进、发布准备 | P0 | 首期形成 batch readiness 闭环 |
| F-04 | AI 优化入口 | 多轮对话驱动 AI 提供建议 | P1 | 不替代人工确认 |
| F-05 | 轻量编辑 | 局部文本或字段修订 | P1 | 不是富文本编辑器 |
| F-06 | 控制平面标准化 | story/execution pack/worker profile/approval profile 抽象 | P0 | 后续代码阶段前必备 |
| F-07 | 规划平面标准化 | program/workstream/story batch/readiness/cycle 抽象 | P0 | 后续代码阶段前必备 |
| F-08 | 执行内核映射 | `dagengine` 内核能力与缺口映射 | P0 | 后续后端设计基座 |
| F-09 | 程序根目录承接 | 冻结 `generic-ai-autodev/` 下前后端、artifacts、runtime-cache、schemas、scripts 的承载结构 | P0 | 防止代码阶段目录语义继续摇摆 |

## 3. 当前真实规划事实

- 首期优先级明确落在 Program、文档、Batch 的规划闭环。
- 模型/profile 配置管理不属于首批主线。
- `01-07` 标准文档需要先行。
- `generic-ai-autodev/` 已存在，可作为新程序根目录承载新实现。

## 4. 候选功能内容

- Program 工作台可在一个界面承接多类规划文档和 batch 审核。
- Batch 管理首期更接近“发布准备台”，不是执行运行台。
- 新实现目录建议采用单根目录 monorepo，而不是多服务散落目录。

## 5. AI 推导建议

- 可把 `F-01/F-02/F-03` 视为同一前端 MVP vertical slice。[待人工确认: 产品负责人]
- 可把 `F-06/F-07/F-08` 视为同一后端规划 vertical slice。[待人工确认: 架构负责人]

## 6. 规划缺口

- 功能项对应的页面与 API 编号还未正式绑定。
- 轻量编辑的字段边界还未冻结。

## 7. 代码事实来源清单

- `docs/prd-autodev/generic-ai-autodev-platform/program-plan.md`
- `docs/prd-autodev/generic-ai-autodev-platform/workstreams/01-frontend-pages.md`
- `docs/prd-autodev/generic-ai-autodev-platform/dagengine-kernel-mapping.md`
- `docs/prd-autodev/generic-ai-autodev-platform/openclaw-control-plane-mapping.md`
