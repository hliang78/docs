---
topic: aidc-business-workbench-rollout
kind: frontend
title: AIDC 全业务页面工作台统一改造
createdAt: 2026-06-25T11:11:00+0800
program: true
---

# AIDC 全业务页面工作台统一改造 PRD

## 1. Background

`aidc-web` 已经完成了企业画像、消息中心、猎单管理、合同回款四个页面的工作台化，但其余业务页仍保留更偏展示或功能堆叠的旧结构，导致产品在跨页使用时节奏不一致。用户已经明确要求把所有业务页统一改造成“专业、简洁、以列表为主的工作台”。

## 2. Goals

1. 完成剩余五个业务页面的工作台化改造。
2. 把全部九个业务页统一到同一视觉和交互节奏。
3. 让关键列表和详情成为主角，摘要和说明退居辅助。
4. 用文件化 program、故事批次和证据来支持持续自动化推进。

## 3. Non-Goals

1. 不新增后端接口。
2. 不重做登录页、系统设置页和全局壳层。
3. 不把这轮工作扩成全站设计系统重构。
4. 不自动 commit、push、merge、发 PR。

## 4. Target Users / Systems

1. 商务、管理员、只读/审计角色。
2. `aidc-web` 的九个业务页。
3. OpenClaw 前端任务 `aidc-fe`。

## 5. Current Findings

Frontend 当前事实：

1. 已有工作台页：`companies`、`messages`、`hunts`、`contracts`。
2. `collections` 以概览卡片开头，尚未进入稳定工作台骨架。
3. `outreach` 已经有重逻辑列表与详情，但页面层级需要重新压实。
4. `radar` 已有列表和详情双区雏形，但外部搜索和主操作仍偏混杂。
5. `supply` 是“列表 + 编辑 + 导入”的天然工作台页，尚未完成统一表达。
6. `workflows` 仍偏摘要台，不够“队列优先”。

Backend 当前事实：

1. 前端页面已有真实接口依赖。
2. 运行期曾出现 `127.0.0.1:18084` 代理错误。
3. 本轮不改后端，但需要如实记录阻塞。

## 6. Requirements

### R1. Remaining pages must enter the shared workbench rhythm

- Description: `collections`、`outreach`、`radar`、`supply`、`workflows` 必须改造成短头部、列表优先、动作集中、详情辅助的工作台页。
- Acceptance:
  - 每页都有稳定的页面头、主体列表区和辅助详情/操作区。
  - 首屏不再被展示型摘要卡墙占据。
  - 原有关键行为入口仍保留。
- Validation:
  - `cd /Users/huangliang/project/aidc_hunt/apps/aidc-web && pnpm typecheck`
  - `cd /Users/huangliang/project/aidc_hunt/apps/aidc-web && pnpm test`
- Evidence:
  - `docs/openclaw-autodev/evidence/aidc-fe/AIDCWB-001..005/`

### R2. Existing workbench pages must be regression-checked

- Description: 已完成的四个页面要纳入同轮一致性回归，必要时补做轻量节奏修补。
- Acceptance:
  - 标题区、密度、列表优先级没有明显风格断层。
  - 不为了新页面而让旧页面回退。
- Validation:
  - 浏览器对比检查
  - `cd /Users/huangliang/project/aidc_hunt/apps/aidc-web && pnpm test`
- Evidence:
  - `docs/openclaw-autodev/evidence/aidc-fe/AIDCWB-006/`

### R3. Critical page flows must stay usable

- Description: 页面改造不能破坏采集、触达、雷达接管、供应链导入、归档入口等关键路径。
- Acceptance:
  - 每个页面至少一个关键主流程有浏览器级证据。
  - 深链、筛选参数和回链保留。
- Validation:
  - 浏览器交互验证
- Evidence:
  - 页面故事下的 `summary.md` 和截图

### R4. Permission, empty, and error states must also be workbench-native

- Description: 权限不足、空态、加载态、接口失败时，也要保持短信息、明确下一步和工作台语气。
- Acceptance:
  - 不重新长出大说明卡或默认欢迎 Hero。
  - 错误和空态能解释当前限制与下一步。
- Validation:
  - 代码检查
  - 浏览器状态验证
- Evidence:
  - 页面故事证据

### R5. The program must be automation-safe

- Description: 任务拆分要足够小，能在 OpenClaw 中逐批、安全、可回滚地推进。
- Acceptance:
  - 首批只进入三页故事。
  - 后续批次保留为 draft，等待前一批证据。
  - 任务默认禁用。
- Validation:
  - loop config 存在
  - story file 存在
  - task pool 可见
- Evidence:
  - `docs/openclaw-autodev/loops/aidc-fe.conf`
  - `docs/openclaw-autodev/stories/aidc-fe.json`

## 7. States And Edge Cases

- Empty: 页面无数据时仍保留工作台骨架，并给出可执行下一步。
- Loading: 列表、详情、辅助区加载要分层表达，不用整页跳闪。
- Success: 成功提示要紧凑，优先挂靠相关动作区。
- Failure: 接口失败时保留页面结构并说明受影响区域。
- Permission denied: 无权限时使用紧凑阻断卡，不用大面积营销式文案。
- Missing dependency: 后端不可用时要记录真实报错并停止伪验证。

## 8. UX / API Contract

Frontend：

1. 页面头保持短。
2. 列表永远先于说明。
3. 详情、导入、草稿、外部搜索等复杂区块降为辅助区。
4. 保留 message-center deep link、URL query 和关键 CTA。

Backend：

1. 以现有接口为权威。
2. 不扩展契约。
3. 新发现的阻塞只记录，不私自弥补。

## 9. Risks And Approval Boundaries

- Requires approval:
  - 依赖变更
  - 后端改动
  - 超出 `apps/aidc-web` 与任务文档目录的写入
  - commit / push / merge / PR
- Known blockers:
  - 后端代理错误可能影响浏览器验证
  - `outreach`、`radar` 的复杂交互可能让故事继续拆分
- Residual risks:
  - 过度抽象共享组件
  - 新旧页面节奏仍有轻微割裂，需要最终一致性批次收口

## 10. Test And Evidence Plan

- Commands:
  - `cd /Users/huangliang/project/aidc_hunt/apps/aidc-web && pnpm typecheck`
  - `cd /Users/huangliang/project/aidc_hunt/apps/aidc-web && pnpm test`
  - `cd /Users/huangliang/project/aidc_hunt/apps/aidc-web && pnpm build`
- Browser/API checks:
  - 九个业务页首屏结构
  - 各页一个关键主路径
  - 深链与回链
- Evidence files:
  - `docs/openclaw-autodev/evidence/aidc-fe/AIDCWB-001..007/`

## 11. OpenClaw Story Package

```json
{
  "program": "aidc-business-workbench-rollout",
  "batch": "batch-001",
  "title": "Collections, outreach, and radar workbench rollout",
  "status": "reviewed",
  "targetTaskIds": ["aidc-fe"],
  "stories": [
    {
      "id": "AIDCWB-001",
      "title": "Convert collections page into a list-first workbench",
      "lanes": ["aidc-fe"],
      "status": "open",
      "priority": 40,
      "risk": "Medium",
      "scope": "Restructure `/business/collections` into a compact workbench with short header, action rail, list-first task area, and supporting diagnostics while preserving collection run, enrichment rerun, and runtime check actions.",
      "nonGoals": "Do not add backend behavior, new data sources, or broad shell changes.",
      "allowedPaths": [
        "apps/aidc-web/app/(platform)/business/collections/**",
        "apps/aidc-web/components/**",
        "apps/aidc-web/lib/**",
        "docs/superpowers/**",
        "/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/evidence/aidc-fe/**"
      ],
      "acceptance": [
        "Collections page uses a workbench layout instead of a dashboard-first card wall.",
        "Run, rerun enrichment, and runtime check actions remain reachable.",
        "Task list and runtime state are visually prioritized over description text.",
        "Typecheck and tests pass."
      ],
      "validation": [
        "cd /Users/huangliang/project/aidc_hunt/apps/aidc-web && pnpm typecheck",
        "cd /Users/huangliang/project/aidc_hunt/apps/aidc-web && pnpm test"
      ],
      "notes": [
        "PRD: /Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/aidc-business-workbench-rollout/prd.md",
        "Evidence: /Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/evidence/aidc-fe/AIDCWB-001/summary.md"
      ]
    }
  ]
}
```
