---
topic: generic-ai-autodev-platform
kind: evidence
title: 本周会话挖矿分析
createdAt: 2026-05-17T12:40:00+0800
program: true
---

# Weekly Session Mining

## Scope

- 时间范围：重点覆盖 `2026-05-15` 到 `2026-05-17` 的 `auto dev`、`prd-autodev`、`openclaw`、`d2on`、`qwen worker` 相关会话。
- 主要本地证据源：
  - `~/.codex/sessions/2026/05/16/*.jsonl`
  - `~/.codex/sessions/2026/05/17/*.jsonl`
  - `~/.codex/archived_sessions/*.jsonl`
  - `~/.codex/.codex-global-state.json`
- 可确认事实：Codex 本地会话元数据中存在 `model_provider: "packycode"`，因此本地 Codex 证据已覆盖 `pacycode` 账号使用痕迹。
- 当前边界：未找到可直接完整还原 `ChatGPT Pro` 历史全文会话的本地明文仓库。已发现 `com.openai.chat` 桌面桥接痕迹和 Chrome `chatgpt.com` IndexedDB，但当前只能确认存在 `ConversationsDatabase`，还不能稳定提取完整旧会话正文。

## High Confidence Findings

- 旧体系最大问题不是单点 bug，而是“没有先规划 contract，再靠运行中补丁修复”。补丁主要集中在状态真相、进程生命周期、blocker 路由、弱 worker 约束、PRD 与执行边界这五大方向。
- `qwen` 适配过程证明了一点：弱模型不是不能用，而是不能裸跑成通用 autonomous agent，必须被压缩到“小任务、少上下文、强验证、强恢复”的 worker 轨道内。
- `d2on` 的多轮真实运行暴露出大量非代码类故障：旧进程残留、daemon 双实例、stale current story、状态回写污染、浏览器策略阻断、gateway token 缺失、provider/session 卡死。这些都说明平台设计不能只围绕“AI 写代码”。
- `prd-autodev` 与 `openclaw` 的职责边界在这周内被反复修正：PRD 应负责“大方向、大轮次、批次规划”，执行引擎负责具体 stories，`repair/approval/runtime` 问题不能无差别回流 PRD。
- 还有一个更底层的问题被反复触发：大量关键信息分散在不同文件中，由脚本、worker、planner、人工操作分别读写，很多决策又依赖这些文件内容，因此天然容易出现不同步、不一致、旧文件污染新轮次的问题。过去大量修复其实是在补这类“文件分布式真相”的债。

## Timeline Summary

- `2026-05-16 00:35` `019e2c7e...`
  - 聚焦远程访问工具、主循环/worker 模型拆分、本地 `ollama/qwen3.6` 可行性。
  - 结论：需要为弱 worker 建独立 harness，不应默认所有 lane 都共享同一模型和同一执行心智。
- `2026-05-16 15:27` `019e2fae...`
  - 聚焦 qwen 真实复杂测试。
  - 关键修补开始落在 `唯一真源`、`story 聚合`、`BLOCKED 不可误写 DONE`、`prompt stuck` 收敛。
- `2026-05-16 17:11` `019e300e...`
  - 从 qwen 问题上升到 OpenClaw 控制面是否仍有价值。
  - 结论：控制面仍有价值，但执行面不能依赖弱模型自由发挥，必须工程化收束。
- `2026-05-16 19:52` `019e30a1...`
  - 将 qwen 经验抽象成通用 worker 适配原则、worker profile、execution pack。
  - 结论：`d2on` 不是单一 worker story lane，而是混合编排 lane。
- `2026-05-16 21:18` `019e30ef...`
  - 真实运行 `d2on`，暴露旧进程、daemon 单实例、状态摘要不一致等问题。
  - 关键修补开始落在启动锁、runtime owner 锁、残留清理。
- `2026-05-17 00:25` `019e319b...`
  - 继续处理“daemon 活着但状态已发散”的真实故障。
  - 结论：需要把 orphan session、空 state 文件、半启动残留纳入一等公民问题。
- `2026-05-17 00:59` `019e31ba...`
  - 审阅第一轮自动化开发质量，并优化弱 worker 的阻塞交互与微信回复路径。
  - 结论：第一轮完成度偏低，存在“看起来做了很多，但闭环没真打通”的风险。
- `2026-05-17 08:12` `019e3346...`
  - 打通 `d2on -> d2on-prd` 多轮循环。
  - 关键修补开始落在 `POST_BLOCK_COMMAND`、stale pointer 清理、自动回流规划器。
- `2026-05-17 09:13` `019e337e...`
  - 继续修正 blocker 路由语义。
  - 结论：环境/runtime blocker 不应自动回流 PRD，应进入 `repair / approval / wait-human`。

## Recurring Failure Categories

### 1. 状态真相分裂

- 真实表现：
  - `story.json`、`state.json`、status 摘要、detail、session 结束态彼此打架。
  - 已经 `BLOCKED/APPROVAL` 的 story 被后续“no selectable story”冲成 `DONE`。
  - 控制器合成票据如 `blocked-story-pending`、`story-selection-failed` 覆盖真实 blocker。
- 本周补丁：
  - `openclaw-state-manager` 复用 `stories.mjs` 聚合逻辑。
  - 阻断合成 ticket 回写真实 story。
  - orphan session 与 ended session 判断收紧。
- 根因判断：
  - 系统内存在多套事实源和多套 reducer。
  - 控制信号、执行信号、展示信号没有先分层定义。
- 对自动驾驶系统的要求：
  - 必须只有一个 `truth reducer`。
  - `command state`、`execution report`、`story truth`、`UI summary` 必须严格分层。
  - 任何展示页都只能读归并后的真相，不能各自推断。

### 2. 进程与会话生命周期失控

- 真实表现：
  - 旧复杂任务残留。
  - daemon 重启瞬间出现双实例。
  - daemon 存活但没有真实 worker 子进程。
  - stale `current-story/current-prompt/current-execution-pack` 污染下一轮。
- 本周补丁：
  - 启动互斥锁。
  - runtime owner 锁。
  - ad hoc start 的 stop 补充清理锁持有者和 model-slot owner。
  - turn 前自动清 stale 指针。
- 根因判断：
  - 平台最初把“进程存在”近似成“任务还在正确执行”。
  - session、pid、lock、artifact、story pointer 缺少统一生命周期模型。
- 对自动驾驶系统的要求：
  - 把 `daemon/session/turn/worker/artifact` 设计成显式状态机。
  - 任何重启、repair、retry 前必须先做 preflight residue cleanup。
  - 单实例保证不能只靠“检查 pid 文件是否存在”。

### 3. Worker 与任务类型不匹配

- 真实表现：
  - `qwen` 在混合任务 lane 上频繁卡死、跑偏、无事件。
  - `d2on` 这种混合 discovery + browser + backend + docs + evidence 的 lane 被当成单一 worker 任务消费。
- 本周补丁：
  - 增加 `worker-profile-mapping`。
  - 增加多类 profile 与 execution pack 示例。
- 根因判断：
  - 没有先定义 task taxonomy 和 worker capability schema。
  - 默认把“一个 story”当作“一个模型都能接”的 story。
- 对自动驾驶系统的要求：
  - 先有 `worker capability profile`，再有任务分发。
  - 先把 story 编译成 execution pack，再给 worker。
  - 混合编排 lane 与单能力 worker lane 必须分开。

### 4. PRD、执行、Repair 三条链路边界不清

- 真实表现：
  - runtime blocker 也被回流到 PRD。
  - PRD story 拆得过小，失去批次规划意义。
  - `repair`、`approval`、`planner` 都在抢 blocked 场景的控制权。
- 本周补丁：
  - 先打开 `plannerOnBlockedReviewed`，后又收紧为：blocked/approval 不自动回流 PRD。
  - blocker 分类修正为 `environment.runtime` 时显示 `WaitingRepair`。
  - repair agent 模型与 runtime env 支持按 task 配置。
- 根因判断：
  - 早期缺少明确 lane contract。
  - “一切 blocked 都回 PRD”是控制边界偷懒。
- 对自动驾驶系统的要求：
  - 规划平面只处理“下一轮业务/产品/验证任务是什么”。
  - 控制平面只处理“当前批次/故事如何执行、验真、推进”。
  - repair 平面只处理 runtime/tooling/env/auth/classified blocker。

### 5. 验证与 evidence 不是第一公民

- 真实表现：
  - 报告可能写 `DONE`，但 readiness 仍 blocked。
  - 某些路径只落摘要，不落原始 evidence，导致“假成功”。
  - worker 自报完成，但真实业务闭环未通。
- 本周补丁：
  - 强调 controller verify、语法检查、类型检查、evidence 输出。
  - 修掉 discovery helper 从截断 summary 解析成功与否的问题。
  - 增强 blocked evidence 与 handoff。
- 根因判断：
  - 初版更偏“让模型完成任务”，而不是“让系统证明任务完成”。
- 对自动驾驶系统的要求：
  - evidence contract 必须先于 story contract。
  - `DONE` 必须由验证器和真相 reducer 共同确认，不能靠模型 footer。
  - `report` 与 `truth` 不一致时，默认以 verifier/truth 为准。

### 6. 运行环境与账号能力没有被产品化

- 真实表现：
  - 浏览器策略、DevTools 会话、gateway token、远程访问凭据、provider 接入方式经常在运行时才暴露。
  - repair agent、planner、worker、主循环需要不同模型/环境，但初版没有角色级 profile。
- 本周补丁：
  - repair agent 模型改为可配置。
  - `d2on.conf` 切到 `packyapi/gpt-5.4 high`。
  - 开始讨论 remote access 工具与 profile 配置面。
- 根因判断：
  - 账号、模型、runtime env、工具能力没有作为平台配置对象来管理。
- 对自动驾驶系统的要求：
- 前端必须有 profile/config 管理。
- 不同 lane/role 使用不同 model profile、runtime env、tool permission。
- 所有外部能力都要先做 preflight probe，再发任务。

### 7. 文件分布式真相导致天然不同步

- 真实表现：
  - story、batch、state、progress、handoff、approval、current-story、current-prompt、execution-pack、evidence summary 分散在不同文件。
  - 决策链经常是“读某个文件 -> 做判断 -> 再写另一个文件”，而不是围绕统一对象事务流转。
  - 旧轮次残留文件、空文件、过期 handoff、被污染的 current-story 会继续影响新一轮选择与判断。
  - 很多修复都在做“清 stale 文件”“避免旧文件覆盖新状态”“不要从被截断/过期文件反推真相”。
- 本周补丁：
  - 清 stale `current-story/current-prompt/current-execution-pack`
  - 修正旧 report/old blocked 覆盖新 approval
  - 修正 handoff 牵引旧 story
  - 收紧 monitor/status/detail 读取口径
- 根因判断：
  - 当前体系虽然已经开始强调真相源，但物理载体仍然是大量分散文件，缺少统一对象存储与统一变更流。
  - 文件既承担“持久化”，又承担“协作接口”，又承担“状态真相”，导致角色耦合过深。
- 对自动驾驶系统的要求：
  - 文件应尽量退到 `artifact/evidence/export/cache` 层，而不是继续承担核心对象真相。
  - `Program/Batch/Story/ExecutionPack/Blocker/Repair/EvidenceTruth` 应有统一对象存储和统一更新入口。
  - 所有决策都应基于对象读取，而不是基于“约定俗成的一堆文件路径”读取。
  - 必须定义“哪些文件只是导出物，哪些对象才是真相”，禁止反向从导出物重建真相。

## Patch Style Anti-Patterns

- 先跑起来，再补分类。
  - 结果是 `DONE/BLOCKED/APPROVAL/WaitingRepair` 语义后补，越补越复杂。
- 先给大 story，再靠模型自由拆。
  - 结果是 story 粒度混乱，弱 worker 无法稳定成功。
- 先让多处文件各自写状态，再补唯一真源。
  - 结果是大量“状态看起来对，其实真相不对”的假稳定。
- 先让 PRD、执行、repair 共用一套 blocked 处理，再补路由。
  - 结果是业务问题、环境问题、授权问题混流。
- 先默认一个模型/账号跑所有角色，再补 profile。
  - 结果是 controller、worker、repair、planner 的约束无法独立调优。
- 先让大量文件同时承担状态、交接、缓存、导出，再补唯一真源。
  - 结果是脚本、人工、worker 都在绕文件做决定，最终不停修“不同步”和“旧文件污染”。

## Guidance For New Platform

### 必须前置设计的 10 个约束

1. 先定义三平面 contract：`PRD planning plane`、`OpenClaw control plane`、`execution/repair plane`。
2. 先定义 `truth model`：story truth、batch truth、turn truth、repair truth 的唯一归并规则。
3. 先定义 `worker capability schema` 与 `execution pack schema`，禁止裸 story 下发。
4. 先定义 `blocker taxonomy` 与 route matrix，明确哪些回 PRD，哪些进 repair，哪些等 approval。
5. 先定义 `process/session/daemon` 生命周期与 residue cleanup 规则。
6. 先定义 evidence contract 与最小 verifier contract，没有 evidence 就不能 `DONE`。
7. 先定义 role-based model/profile 体系：planner、controller、worker、repair 分离。
8. 先定义统一对象存储与文件导出边界，避免核心真相继续分散在大量文件中。
9. 先定义 runtime preflight：浏览器、远程访问、DB、gateway、provider、token、workspace 污染检查。
10. 先定义 batch-first planning 规则，避免 PRD 过早拆成大量微型 story。
11. 先定义 human ops UX：微信/前端上的 repair、approval、retry、detail 必须是低心智负担操作。

### MVP 阶段最值得落地的对象

- `Program`
- `PRD document`
- `Story package / batch`
- `Worker profile`
- `Execution pack`
- `Runtime env profile`
- `Repair ticket`
- `Evidence set`

## What This Means For Current Planning

- 现在继续做“平台规划与标准化”是对的，因为旧体系最深的问题就是很多 contract 没有先冻结。
- 前端首期不应该急着做 AI 聊天式生成，而应该优先承载这些对象：
  - Program / PRD / batch 管理
  - profile 管理
  - blocker route 与 repair/approval 状态观察
  - evidence/readiness 审阅
- 在你补充下一轮关键人工要求之前，任何 implementation batch 都不应该 promote。

## Coverage Limitation

- 已完整分析本地可读的 Codex 周内相关会话，且这些会话已覆盖当前 `pacycode` 使用痕迹。
- `ChatGPT Pro` 旧会话当前只能确认存在桌面桥接目录和浏览器 IndexedDB，不足以稳定恢复完整历史正文，因此本分析对 `ChatGPT Pro` 的覆盖不完整。
- 如果后续能提供：
  - `ChatGPT Pro` 导出的会话文本
  - 可读的浏览器会话导出
  - 账号侧 conversation export
  则需要补做一次“跨账号统一挖矿”。
