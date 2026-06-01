---
topic: generic-ai-autodev-platform
kind: evidence
title: 业务编排内部状态对自动化执行的影响分析
createdAt: 2026-05-18T02:40:00+0800
program: true
---

# Business Orchestration State Impact Analysis

## Purpose

- 这份文档不再讨论 runtime/provider/tooling 这一层。
- 这里专门回答一个更容易被低估的问题：
  - 业务编排内部状态，本身就会严重影响自动化执行。
- 也就是说：
  - 自动化失败不一定先从模型、provider、浏览器、权限开始。
  - 很多失败在更上层就已经埋下了：
    - program/batch/story 的状态语义
    - blocker route
    - approval/repair/planner 边界
    - readiness / acceptance / publish gate

## Core Conclusion

- 从 `019e1946` 开始到现在的会话看，业务编排状态不是“给人看的标签”。
- 它实际上直接决定了：
  - 当前该执行什么
  - 不该执行什么
  - 应该回流 PRD 还是进入 repair
  - 哪个 batch 能被编译
  - 哪个 story 能被 worker 消费
  - 哪个结果能推进到 `done`
  - 哪个结论能终止循环
- 如果这些状态语义不稳，runtime 再强也会被上游错误状态喂坏。

## What The Sessions Actually Showed

## 1. 业务编排状态会直接改变“当前执行目标”

### 真实表现

- 会话里反复出现：
  - queue 选的是当前 story
  - 但 worker 实际被旧 handoff、旧 current-story、旧 current-prompt 牵走
- 这不是单纯的残留文件问题。
- 更上层的本质是：
  - “当前有效业务状态”没有压过“历史交接状态”。

### 为什么影响执行

- 对自动化来说，`selected story` 不是展示字段，而是当前执行目标。
- 一旦“当前 story”与“历史 handoff”争夺权威：
  - worker 会执行错对象
  - evidence 会挂到错对象
  - repair 也会修到错对象

### 会话证据

- [session-mining-from-019e1946-to-now.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/evidence/session-mining-from-019e1946-to-now.md)
  - Phase 4 明确提到：
    - `queue 选择正确，但 worker 被旧 handoff 牵引`
    - `story 注入和 handoff 注入混线`
- [weekly-session-mining-2026-05-17.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/evidence/weekly-session-mining-2026-05-17.md)
  - 明确记录：
    - `修正 handoff 牵引旧 story`
    - `清 stale current-story/current-prompt/current-execution-pack`

## 2. 业务编排状态会直接改变“blocked 之后去哪里”

### 真实表现

- 历史里出现过：
  - runtime blocker 回流 PRD
  - approval/repair/planner 都来抢 blocked 控制权
  - `plannerOnBlockedReviewed` 先打开，后面又不得不收紧

### 为什么影响执行

- `blocked` 不是一个中性状态。
- 对自动化来说，`blocked` 背后其实是下一步执行路线：
  - 回 PRD
  - 走 repair
  - 等 approval
  - 直接 stop
- 路由错了，执行链就会被上层状态机带偏。

### 会话证据

- [weekly-session-mining-2026-05-17.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/evidence/weekly-session-mining-2026-05-17.md)
  - 第 4 点直接写到：
    - `runtime blocker 也被回流到 PRD`
    - `repair、approval、planner 都在抢 blocked 场景的控制权`
    - 后来又收紧为 `blocked/approval 不自动回流 PRD`
- [problem-extraction-from-019e1946-to-now.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/evidence/problem-extraction-from-019e1946-to-now.md)
  - P-20、P-21、P-27 都能看到这种错路由带来的连锁后果

## 3. 业务编排状态会直接改变“story 能否被稳定消费”

### 真实表现

- 会话里多次暴露：
  - story 粒度过粗
  - 混合 lane 被当单能力 worker 消费
  - PRD 过早拆成微 story
  - batch/story 虽存在，但其状态不具备稳定下发条件

### 为什么影响执行

- worker 实际消费的不是 prose，而是“被编排状态约束后的任务”。
- 如果 story/batch 还是：
  - lane 不清
  - dependsOn 不清
  - acceptance/validation 不清
  - release gate 不清
- 那执行层拿到的就不是任务，而是半成品。

### 会话证据

- [session-mining-from-019e1946-to-now.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/evidence/session-mining-from-019e1946-to-now.md)
  - Phase 3 提出：
    - Program / Workstreams / Story Batches
    - PRD 到自动化发布要有确定性脚本
  - Phase 7 提到：
    - `worker profile`
    - `execution pack`
    - `blocker route`
- [weekly-session-mining-2026-05-17.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/evidence/weekly-session-mining-2026-05-17.md)
  - 第 3 点明确写到：
    - `d2on` 这种混合 lane 被当成单一 worker 任务消费
    - `先把 story 编译成 execution pack，再给 worker`

## 4. 业务编排状态会直接改变“执行结果是否被承认”

### 真实表现

- 历史里反复出现：
  - report 写 `DONE`
  - readiness 仍 blocked
  - approval 已给，但旧 blocked 又覆盖回来
  - 旧 report / 旧 handoff / 旧 summary 压过新结论

### 为什么影响执行

- 自动化真正怕的不是失败，而是假 closure。
- `done / blocked / approval / reviewed / ready` 这些状态一旦语义混线：
  - worker 以为完成
  - controller 以为还没完成
  - PRD 以为需要继续
  - human 看到的又可能是第三种状态

### 会话证据

- [weekly-session-mining-2026-05-17.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/evidence/weekly-session-mining-2026-05-17.md)
  - 第 5 点写到：
    - `报告可能写 DONE，但 readiness 仍 blocked`
    - `worker 自报完成，但真实业务闭环未通`
  - 第 7 点写到：
    - `修正旧 report/old blocked 覆盖新 approval`
- [problem-extraction-from-019e1946-to-now.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/evidence/problem-extraction-from-019e1946-to-now.md)
  - P-16、P-18、P-26、P-27、P-29 都是这一类

## 5. 业务编排状态会直接改变“循环是否继续”

### 真实表现

- 会话后期已经非常明显：
  - 单个 story done 不等于 program close
  - 单个 batch 完成不等于 PRD 验收
  - 什么时候 draft next batch、promote next batch、close program，本质上都是编排状态决定的

### 为什么影响执行

- 自动化不是单 turn 执行器，而是多轮循环系统。
- 只要循环状态语义不对：
  - 会过早结束
  - 会重复执行
  - 会在错误的 batch 上继续投入
  - 会让 repair、planner、worker 互相覆盖彼此的完成标准

### 会话证据

- [session-mining-from-019e1946-to-now.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/evidence/session-mining-from-019e1946-to-now.md)
  - Phase 7 已经明确写出：
    - `d2on -> d2on-prd` 循环
- [prd-autodev-bidirectional-loop-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/prd-autodev-bidirectional-loop-freeze.md)
  - 已正式把：
    - `CycleBackfeed`
    - `PRDAcceptanceDecision`
    - `accept-and-close`
    冻成新的规划层对象

## 6. 业务编排状态会直接改变“前端和消息控制面看到什么”

### 真实表现

- 会话里你多次追着修的，其实都不是样式，而是状态协议：
  - result banner
  - decision rail
  - blockers / missing fields / release gate
  - docs/batch mode 切换后的对象记忆
- 这些都说明：
  - 前端不是纯展示层，它在承接业务编排状态。

### 为什么影响执行

- 前端和手机消息面如果读错状态：
  - human 会批错
  - 会 promote 错 batch
  - 会在 blocked 时误以为可继续
  - 会在 ready 时误以为还要继续补文档

### 会话证据

- [frontend-final-alignment-checklist.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/frontend-final-alignment-checklist.md)
  - 大部分最终确认项其实都是状态读模型与状态展示协议
- [human-ops-message-projection.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/human-ops-message-projection.md)
  - 明确消息只能读结构化状态投影，不能从 prose 反推

## The Deeper Pattern

- 从这些会话看，业务编排内部状态至少同时扮演了 6 个角色：
  1. 选择当前执行目标
  2. 决定 blocked 路由
  3. 决定是否允许 compile / publish / execute
  4. 决定结果是否被承认
  5. 决定循环是否继续
  6. 决定 human/front-end/message 面看到的控制信号
- 所以“业务编排状态”不能继续被理解成：
  - 文档 metadata
  - UI badge
  - 方便人工阅读的摘要
- 它本质上是：
  - `automation control input`

## Direct Design Requirement For The New Platform

基于这些会话证据，自动驾驶系统至少必须满足：

1. 业务编排状态必须是强对象，而不是零散字段。
2. 业务编排状态必须能压过旧 handoff、旧 report、旧 cache。
3. `blocked / approval / reviewed / ready / done / accepted` 必须分层，不能混跑。
4. execution 只能消费“已被编排状态正式放行”的对象。
5. planning 只能基于结构化 backfeed 改下一轮，而不能直接读执行 prose。
6. 最终 acceptance close 必须回到 PRD/planning plane。

## What This Means For Current Freeze Work

- 这条分析进一步证明，前面新增的几份冻结文档并不是可选增强，而是必要补丁：
  - [readiness-decision-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/readiness-decision-freeze.md)
  - [prd-autodev-bidirectional-loop-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/prd-autodev-bidirectional-loop-freeze.md)
  - [evidence-verifier-contract.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/evidence-verifier-contract.md)
  - [object-state-freeze-checklist.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/object-state-freeze-checklist.md)
- 还说明一个额外结论：
  - 后续如果不把“业务编排状态 contract”继续下沉成 schema/reducer/API，
  - 自动驾驶系统很可能再次出现“runtime 看起来正常，但自动化还是跑偏”的旧病。
