---
topic: aidc-business-workbench-rollout
kind: frontend
title: AIDC 全业务页面工作台统一改造
createdAt: 2026-06-25T11:11:00+0800
program: true
---

# Program Plan

## Objective

将 `aidc-web` 的全部业务页面统一改造成专业、简洁、列表优先的产品型工作台，并把这项工作组织成一个可持续推进、可证据化验收、可安全调度的前端长任务。

## Definition Of Done

1. `collections`、`outreach`、`radar`、`supply`、`workflows` 五个页面完成工作台化改造。
2. `companies`、`messages`、`hunts`、`contracts` 四个已完成页面经过一致性复查，必要时补做轻量收口。
3. 工作台页面都符合“短标题区 + 列表优先主体 + 右侧或下方辅助详情”的统一节奏。
4. 不存在新的展示型 Hero、驾驶舱卡墙或过度解释型首屏。
5. `apps/aidc-web` 的 `pnpm typecheck`、`pnpm test`、`pnpm build` 通过。
6. 九个业务页面都有浏览器级证据，且后端阻塞被如实记录而不是被掩盖。

## Scope

### In Scope

1. 业务页面 `collections`、`outreach`、`radar`、`supply`、`workflows` 的页面结构重排。
2. 共享工作台组件、页面级 helper、测试与文档的补充。
3. 已完成页面 `companies`、`messages`、`hunts`、`contracts` 的一致性回归和必要轻量修正。
4. 页面级空态、加载态、错误态、权限态的工作台化表达。
5. 浏览器验证、截图证据、故事批次和回归计划。

### Out Of Scope

1. 新增后端接口、变更数据库或引入新的外部集成。
2. 重做登录页、系统设置页或全局壳层。
3. 新增与工作台目标无关的大功能。
4. 自动提交、推送、合并、发 PR。

## Workstreams

| ID | Workstream | Lane | Status | Notes |
|---|---|---|---|---|
| 01 | Frontend Pages And Controls | aidc-fe | ready | 完成剩余 5 页的结构改造与共享组件落地。 |
| 02 | Backend API Contracts | aidc-fe | ready | 不做后端开发，只记录真实阻塞与前端受影响点。 |
| 03 | End-to-End Critical Flows | aidc-fe | ready | 覆盖采集、触达、雷达接管、供应链导入、归档流程入口。 |
| 04 | Permissions And Error States | aidc-fe | ready | 收口角色权限、空数据、错误提示和不可用状态。 |
| 05 | Regression Suite | aidc-fe | ready | 全页面浏览器证据、测试和最终回归。 |

## Dependency Map

1. `01 Frontend Pages And Controls` 是主干工作流。
2. `02 Backend API Contracts` 伴随每个页面故事执行，不单独阻塞结构改造。
3. `03 End-to-End Critical Flows` 依赖每个页面的首版工作台结构已经落地。
4. `04 Permissions And Error States` 允许随页面故事并行，但需要在最终回归前完成。
5. `05 Regression Suite` 依赖前四个工作流已形成可验证页面。

## Risk Register

| Severity | Risk | Decision Needed |
|---|---|---|
| P0 | 后端代理或真实接口不可用，导致浏览器验证无法覆盖真实数据流。 | 继续前端结构落地，同时把阻塞写入证据，不允许用 mock 掩盖。 |
| P1 | `outreach`、`radar` 页面交互与详情逻辑较重，单故事可能超预算。 | 必要时继续拆成补充故事，不强压一轮完成。 |
| P1 | 过早抽象共享工作台组件，反而拖慢 5 页落地。 | 先按页面落地，第二批或第三批再做共性收口。 |
| P2 | 已完成页面与新页面在标题、间距、侧栏节奏上出现风格断层。 | 用最终一致性批次统一修正。 |

## Batch Plan

| Batch | Goal | Target Lanes | Status | Gate |
|---|---|---|---|---|
| batch-001 | `collections`、`outreach`、`radar` 三页工作台落地 | aidc-fe | reviewed | 已按用户指令生成，可进入队列但任务默认禁用 |
| batch-002 | `supply`、`workflows` 两页工作台落地 | aidc-fe | draft | 需先看 batch-001 证据 |
| batch-003 | 九页一致性回归、关键浏览器验证、证据收口 | aidc-fe | draft | 需 batch-001 与 batch-002 都完成 |

## Approval Boundaries

- 不允许写入 `apps/aidc-web` 之外的业务代码目录，除了任务证据与 PRD 文档。
- Writes outside allowed paths.
- Dependency changes.
- Backend contract or persistence changes without explicit approval.
- Production config, migrations, credentials, auth, tenant logic, deploy, commit, push, merge, PR.

## Stop Conditions

1. 需要新增依赖或升级依赖。
2. 需要改动非 `aidc-web` 业务代码。
3. 发现后端契约缺失且前端无法继续安全落地。
4. 某页面故事已经混入实现、回归、文档、清理等多重目标而失去单回合边界。

## Task Generation Plan

- `task-id`: `aidc-fe`
- `project-root`: `/Users/huangliang/project/aidc_hunt`
- `charter-doc`: `/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/aidc-business-workbench-rollout/prd.md`
- `coordination-doc`: `/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/aidc-business-workbench-rollout/program-plan.md`
- `story-file`: `/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/stories/aidc-fe.json`
- `evidence-dir`: `/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/evidence/aidc-fe`
- `validation-command`: `cd /Users/huangliang/project/aidc_hunt/apps/aidc-web && pnpm typecheck && pnpm test`
- `final-regression-command`: `cd /Users/huangliang/project/aidc_hunt/apps/aidc-web && pnpm build`
- `default-enabled`: `false`
