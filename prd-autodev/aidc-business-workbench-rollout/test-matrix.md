---
topic: aidc-business-workbench-rollout
kind: frontend
title: AIDC 全业务页面工作台统一改造
createdAt: 2026-06-25T11:11:00+0800
program: true
---

# Test Matrix

| Area | Surface/API | Scenario | Role/Data | Expected | Evidence | Lane | Priority | Status |
|---|---|---|---|---|---|---|---|---|
| Collections | `/business/collections` | 首屏进入后先看到概览、任务列表、运行操作，而不是展示型大卡墙 | admin / business | 短标题区、运行入口、任务列表与运行诊断分区清晰 | `evidence/aidc-fe/AIDCWB-001/summary.md` | aidc-fe | P1 | planned |
| Collections | `/business/collections` | 数据源诊断、重跑补全、立即运行采集的按钮状态可读 | admin / business | loading、disabled、success、error 提示稳定 | `evidence/aidc-fe/AIDCWB-001/browser.png` | aidc-fe | P1 | planned |
| Outreach | `/business/outreach` | 任务列表、状态过滤、详情编辑区保持列表优先且不丢草稿语义 | business / message deep link | 列表、详情、草稿工作区节奏清晰 | `evidence/aidc-fe/AIDCWB-002/summary.md` | aidc-fe | P0 | planned |
| Outreach | `/business/outreach` | `noticeContact` / message focus 进入页面后仍能正确聚焦 | message-center deep link | 焦点、筛选和返回消息中心链接不失效 | `evidence/aidc-fe/AIDCWB-002/browser.png` | aidc-fe | P1 | planned |
| Radar | `/business/radar` | 列表筛选、接管、转触达、外部导入入口工作台化 | business / admin | 首屏以雷达列表和详情为主，外部搜索是辅助区 | `evidence/aidc-fe/AIDCWB-003/summary.md` | aidc-fe | P0 | planned |
| Radar | `/business/radar` | 消息中心 focus、评分筛选、noticeContactOnly 仍可用 | message deep link | URL 参数和聚焦滚动逻辑保留 | `evidence/aidc-fe/AIDCWB-003/browser.png` | aidc-fe | P1 | planned |
| Supply | `/business/supply` | 产品列表、编辑表单、批量导入预校验进入统一工作台节奏 | business / admin | 列表、表单、导入结果分区明确 | `evidence/aidc-fe/AIDCWB-004/summary.md` | aidc-fe | P1 | planned |
| Supply | `/business/supply` | 模板下载、问题行导出、导入确认的状态表达清晰 | business / admin | 成功、错误、待修正状态可扫描 | `evidence/aidc-fe/AIDCWB-004/browser.png` | aidc-fe | P1 | planned |
| Workflows | `/business/workflows` | 合同后段流程、待归档队列、归档批次摘要列表优先 | business / admin | 首屏能快速进入流程队列，不再依赖展示型头图 | `evidence/aidc-fe/AIDCWB-005/summary.md` | aidc-fe | P1 | planned |
| Workflows | `/business/workflows` | 来自消息中心的 archive-ready focus 仍可滚动定位 | message deep link | 聚焦和回链保留 | `evidence/aidc-fe/AIDCWB-005/browser.png` | aidc-fe | P1 | planned |
| Baseline Pages | `companies/messages/hunts/contracts` | 与新增页面进行标题、密度、列表优先级一致性回归 | mixed | 九页在页面头、筛选区、列表区节奏上无明显割裂 | `evidence/aidc-fe/AIDCWB-006/summary.md` | aidc-fe | P0 | planned |
| Full FE Gate | `apps/aidc-web` | 类型检查与测试通过 | repo local data | `pnpm typecheck`、`pnpm test` 通过 | `evidence/aidc-fe/AIDCWB-007/verification.txt` | aidc-fe | P0 | planned |
| Final FE Gate | `apps/aidc-web` | 生产构建通过 | repo local data | `pnpm build` 通过 | `evidence/aidc-fe/AIDCWB-007/build.txt` | aidc-fe | P0 | planned |
