---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶系统
createdAt: 2026-05-17T10:40:32+0800
status: draft
---

# 标准模板 01-07 阶段化映射

## 1. 目的

把 `docs/development-doc-templates` 的 `01-07` 模板与当前挖矿产物做显式映射，确保后续不是“重新想一遍文档”，而是从已确认的 planning 资产稳定生成标准文档。

## 2. 映射原则

- 标准模板是输出形态，不是信息来源。
- 信息来源优先来自当前 program 的 research/alignment/mapping/workstream 产物。
- 每类模板都要区分：
  - 当前真实规划事实
  - 候选文档内容
  - AI 推导建议
  - 规划缺口
- `01-07` 在代码前先形成 `blocked-human-confirmation` 版本。
- `08-10` 不在本轮补齐，但要为后续测试与自动化阶段保留输入位。

## 3. 模板映射表

| 模板 | 当前候选文档 | 主要输入来源 | 产出阶段 | 进入代码前要求 |
|---|---|---|---|---|
| `01-需求概要模板` | `docs/development/generic-ai-autodev-platform/candidate-01-requirements-summary.md` | `context-brief.md`、`alignment.md`、`program-plan.md` | 需求冻结前 | 必须有首期目标、边界、角色、关键业务规则 |
| `02-功能清单模板` | `docs/development/generic-ai-autodev-platform/candidate-02-function-list.md` | `workstreams/01-frontend-pages.md`、`program-plan.md`、`alignment.md` | 需求冻结前 | 必须有 MVP 功能项与优先级 |
| `03-实体属性清单模板` | `docs/development/generic-ai-autodev-platform/candidate-03-entity-attribute-list.md` | `prd-planning-plane-mapping.md`、`openclaw-control-plane-mapping.md`、`dagengine-kernel-mapping.md` | 架构抽象阶段 | 必须有 planning/control/runtime 核心对象 |
| `04-原型清单模板` | `docs/development/generic-ai-autodev-platform/candidate-04-prototype-list.md` | `workstreams/01-frontend-pages.md`、`test-matrix.md` | 前端方案阶段 | 必须有页面清单、层级、导航、待确认项 |
| `05-数据库设计模板` | `docs/development/generic-ai-autodev-platform/candidate-05-database-design.md` | `candidate-03-entity-attribute-list.md`、三平面 mapping 文档 | 开发前设计阶段 | 必须有候选存储分层方向与未决事项 |
| `06-接口文档模板` | `docs/development/generic-ai-autodev-platform/candidate-06-api-documentation.md` | `workstreams/02-backend-api-contracts.md`、`workstreams/04-permissions-errors.md`、`test-matrix.md` | 开发前设计阶段 | 必须有首页闭环 API 面与权限边界 |
| `07-后端开发设计模板` | `docs/development/generic-ai-autodev-platform/candidate-07-backend-development-design.md` | `dagengine-kernel-mapping.md`、`openclaw-control-plane-mapping.md`、`prd-planning-plane-mapping.md` | 开发前设计阶段 | 必须有分层、目录建议、复用边界 |

## 4. 输入到输出的依赖链

1. `questions/context-brief/alignment`
   - 负责冻结首期目标、边界、优先级。
2. `program-plan/workstreams/test-matrix`
   - 负责把目标转成前端、后端、流程、权限、回归等切片。
3. 三个 mapping 文档
   - 负责把 `dagengine`、`openclaw-autodev`、`prd-autodev` 的矿脉抽成对象模型。
4. `candidate-01` 到 `candidate-07`
   - 负责把挖矿结果装进标准模板。
5. `review.md` + `evidence/final-readiness.md`
   - 负责判断是否允许进入代码阶段。

## 5. 代码前最小要求

- `01-04` 需要支撑产品和前端讨论。
- `05-07` 需要支撑后端与架构讨论。
- 以上文档都可以继续修订，但在进入代码前不能再出现“文档壳已建、核心内容未装”的状态。

## 6. 后续 08-10 预埋关系

| 后续模板 | 未来输入来源 |
|---|---|
| `08-测试用例模板` | `test-matrix.md`、`workstreams/05-regression-suite.md`、后续 CT evidence |
| `09-接口调用文档模板` | `candidate-06-api-documentation.md`、真实接口实现 evidence |
| `10-自动化测试脚本说明模板` | `workstreams/05-regression-suite.md`、OpenClaw/CT 执行脚本与 evidence |

## 7. 当前结论

- `01-07` 的首轮模板映射关系已经建立。
- 当前已具备进入“代码前最后一次人工对齐”的标准化基础。
- 仍未冻结的不是模板结构，而是前端形态细节、首批代码切片策略、以及首批运行时 contract。
