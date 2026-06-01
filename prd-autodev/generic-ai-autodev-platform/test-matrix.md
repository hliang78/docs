---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶系统
createdAt: 2026-05-17T10:40:32+0800
program: true
---

# Test Matrix

| Area | Surface/API | Scenario | Role/Data | Expected | Evidence | Lane | Priority | Status |
|---|---|---|---|---|---|---|---|---|
| Frontend planning shell | Web UI / program home | Open homepage and navigate from program list to program detail, docs view, batch review view | planner user / sample program | 首页形成 `Program -> Docs -> StoryBatch` 最小闭环 | 信息架构稿、页面层级说明、导航流说明 | frontend-planning | P0 | draft |
| Document review | Docs panel | Read `context-brief/program-plan/workstream/test-matrix` and identify draft/reviewed/readiness status | planner user / one program | 文档状态可识别，可进入审阅与状态推进 | 页面状态说明、对象清单 | frontend-planning | P0 | draft |
| Batch readiness | Batch review view | Inspect one batch and decide whether it can enter `ready-for-openclaw` | planner user / one batch | 能区分 `draft/reviewed/ready-for-openclaw` | batch readiness 规则稿 | planning | P0 | draft |
| Backend core mapping | dagengine analysis | Map existing `dagengine` process/task/ticket/persistence/api` to MVP scope | architect/planner | 明确可复用能力与缺口 | 能力清单、缺口清单 | backend-planning | P0 | draft |
| Control plane mapping | openclaw analysis | Map story/execution pack/worker profile/handoff/recovery into platform control objects | architect/planner | 明确控制面一等对象与候选 lane | 控制面映射稿、lane 草案 | planning | P0 | draft |
| Template rollout | docs/development-doc-templates | Define first-phase standard documents using `01-07` | planner | 形成阶段化文档路线，不混入一次性 01-10 全产出 | 文档路线说明 | planning | P1 | draft |
| Permissions boundary | Web UI / API | Verify read-only, review, state progression, and forbidden actions are clearly separated | planner/owner | 首期主线不误扩成运行控制或全量编辑 | 权限矩阵、禁用动作清单 | planning | P0 | draft |
| Error handling | Docs panel / batch view | Missing doc, invalid story field, dependency conflict, readiness-not-met | planner | 用户能知道是缺资料、状态冲突还是禁止动作 | 错态定义、阻断规则 | planning | P0 | draft |
| Regression baseline | Planning shell / API contracts | Define minimum smoke suite before code starts | ct-owner | 后续首批代码不偏离当前规划闭环 | 回归层级与验证候选 | ct | P1 | draft |
