---
topic: generic-ai-autodev-platform
kind: full-stack
title: 前端最终对齐清单
createdAt: 2026-05-17T23:35:00+0800
program: true
status: draft
---

# Frontend Final Alignment Checklist

## Purpose

- 这份清单只服务“代码前最后一次前端对齐”。
- 不再讨论大方向，只压缩剩余的交互与切片级问题。

## Already Frozen

1. 前端采用显式 `React` 工作台栈：
   - `React + TypeScript + Vite + TanStack Router + TanStack Query + shadcn/ui + XState`
2. 只借鉴 `React-Admin` 的工作台模式，不直接采用其脚手架。
3. 顶层路由采用：
   - `/programs`
   - `/programs/:programId`
4. 工作台内部采用：
   - query 驱动
   - 左侧目录树切换
   - 中部主工作区
   - 右侧决策栏
5. 首期只做：
   - `只读 + 审阅 + 状态推进`
6. `profile / incident` 摘要挂在右侧决策栏。
7. `ready-for-openclaw` 以前端 summary panel 为主表达。
8. 首页保留后续能力入口占位，但不纳入首批主线。
9. 文档正文采用：
   - `markdown + structured metadata`
10. review transition 确认交互采用：
   - `modal`
11. `docs` / `batch` mode 切换时：
   - 保留同一 program 内上一次选中的 `doc` / `batch`
12. 左侧导航树采用：
   - 按当前 mode 默认展开 + 记忆用户上次展开状态
13. `readiness-check` 反馈采用：
   - `临时结果条 + 右栏同步`
   - `passed` 自动消失 `5s`
   - `blocked/error` 不自动消失
14. review modal 采用：
   - 仅展示状态推进关键字段
15. Batch 审核面板固定显示：
   - blockers 总数
   - missing fields 总数
   - release gate 摘要
16. 右侧决策栏后续必须能容纳：
   - AI 司机当前意图
   - 最新学习结论
   - 活动中的接管状态
   - 最新结束信号摘要
   - 融合后的风险/置信度摘要

## Remaining Alignment Items

### Minor Copy Details

1. summary panel 文案与标签命名
2. review modal 按钮文案与备注提示
3. readiness result banner 标题与摘要文案
4. 文档 structured metadata 的字段展示顺序
5. 接管提示文案与按钮文案
6. 结束信号摘要在右栏与详情头部的露出文案

## Recommendation

我建议如果还继续讨论前端，只讨论下面 5 个文案级细节：

1. summary panel 文案与标签命名
2. review modal 按钮与备注提示文案
3. readiness result banner 标题与摘要文案
4. structured metadata 字段顺序
5. takeover 提示与接管动作文案
6. 结束信号摘要与风险置信度标签文案

## Current Conclusion

- 前端已经不再缺信息架构。
- 主要交互、读模型与状态归属都已完成代码前对齐。
- 剩下的是文案、字段排序，以及接管提示的动作命名级细节，当前仍不进入代码。

## Recommended Defaults

### 1. Workbench Data Loading

建议采用：

- 首屏并行读取：
  - `program header`
  - `nav tree source`
  - `decision rail summary`
  - 当前 mode 的主内容
- 非当前 mode 不阻塞首屏
- 页面稳定后，只低优先级预取另一 mode 的 meta，不预取完整内容

原因：

- 首屏足够快
- 右栏能尽早给出决策信息
- 不会因为一次性拉全量 docs/batches 正文拖慢工作台

### 2. Mode Switching Memory

建议采用：

- 在同一个 `program` 内，记住用户上一次选中的：
  - `doc`
  - `batch`
- 当用户在 `docs` 和 `batch` 之间切换时：
  - 回到该 mode 上一次选中的对象
- 只有在首次进入某个 mode、且没有历史选择时，才使用默认落点

默认落点建议：

- `docs` 首次默认落到 `review`
- 如果 `review` 不存在，则回退到 `final-readiness`
- `batch` 首次默认落到最新一个 batch

原因：

- 用户切换 mode 时，通常希望回到“刚才看的那个对象”，而不是每次被打回固定入口
- 这样既保留工作连续性，又不会把 URL 和状态机搞复杂

### 3. Nav Tree Expansion Strategy

建议采用：

- 首次进入 program 时：
  - `Program 概览` 默认展开
  - 当前 mode 对应分组默认展开
  - 非当前 mode 分组默认收起
- 在同一个 program 内：
  - 记忆用户上一次的展开/收起状态

具体建议：

- `mode=docs`：
  - 展开 `文档目录`
  - 收起 `Batch 列表`
- `mode=batch`：
  - 展开 `Batch 列表`
  - 收起 `文档目录`

原因：

- 不建议默认全展开，信息噪音太大
- 也不建议每次只强制展开当前项，容易让用户失去上下文
- “按 mode 默认展开 + 记忆用户选择”最稳

### 4. Summary Panel Priority

建议采用：

1. 顶部 `ready / blocked` 主状态标签
2. `next action`
3. top blockers 列表
4. supporting counts：
   - missing docs
   - invalid fields
   - release gate 摘要
5. 最新结束信号摘要
6. 底部紧凑 `profile / incident` 摘要

原因：

- 用户进入工作台时，最先要回答的是“现在能不能继续推进”
- 第二优先是“下一步该做什么”
- 最新结束信号会直接影响“是否真的结束了某一步”，所以优先级高于一般运维背景信息
- 细节支撑信息应放在后面，而不是抢主视觉

### 5. Batch Review Fixed Summary

建议固定显示：

1. blockers 总数
2. missing fields 总数
3. release gate 摘要

展示位置建议：

- `BatchMetaBar` 下方的紧凑 summary strip
- 不占用主表空间
- 不与右栏决策栏重复堆叠长文本

原因：

- 进入 Batch Mode 时，用户要先快速判断“这一批是否具备继续推进的基本条件”
- 这 3 项比 story 明细更适合作为批次级摘要常驻显示

### 6. Readiness-Check Result Feedback

建议采用：

- `临时结果条 + 右栏同步`

结果条信息密度建议：

- 状态图标
- 简短标题：
  - `Readiness Check Passed`
  - `Blocked For OpenClaw`
  - `Check Failed`
- 1 行摘要
  - 成功时：说明“已满足进入下一步的基础条件”
  - blocked 时：显示 blocker 数量与最关键 1 个原因
  - error 时：显示失败类型
- 一个轻量提示：
  - `查看右侧详情`

停留时长建议：

- `passed`：
  - 自动消失，`5s`
- `blocked`：
  - 不自动消失，直到用户手动关闭或触发下一次 check
- `error`：
  - 不自动消失，直到用户手动关闭

原因：

- 成功结果是轻提醒，不应长期占屏
- `blocked/error` 是阻断性信息，必须确保用户看见

### 7. Review Modal Fields

建议采用：

按“少字段但足够决策”的原则，首期 modal 只展示：

1. 对象标题
   - 文档名或 batch 名
2. 当前状态 -> 目标状态
3. 简短影响说明
   - 例如：`reviewed 后可进入下一步 readiness 判断`
4. 关键摘要
   - pending items count
   - blockers count
   - last updated time
5. 可选备注输入框
   - moving to `blocked-human-confirmation` 时建议必填
   - moving to `reviewed` 时可选
6. 底部确认按钮
   - `取消`
   - `确认推进`

原因：

- 首期是 `只读 + 审阅 + 状态推进`
- modal 目标是“确认动作”，不是把整个对象详情再复制一遍
- 字段过多会让确认动作变成第二个阅读页
