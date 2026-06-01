---
topic: generic-ai-autodev-platform
kind: evidence
title: 从 019e1946 起到现在的问题提取
createdAt: 2026-05-17T23:58:00+0800
program: true
---

# Problem Extraction From 019e1946 To Now

## Scope

- 起点会话：`019e1946-2012-7e41-9f3d-42bfbc37cbb0`
- 时间范围：`2026-05-12` 到 `2026-05-17`
- 目的：先如实提取问题，不先做机制设计，不急着给解法。
- 本轮主要证据源：
  - `~/.codex/sessions/2026/05/12/*.jsonl` 到 `~/.codex/sessions/2026/05/17/*.jsonl`
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/session-mining-from-019e1946-to-now.md`
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/weekly-session-mining-2026-05-17.md`
  - `docs/openclaw-autodev/stories/d2on.json`
  - `docs/openclaw-autodev/state/**`
  - `docs/prd-autodev/device-v2-onboarding-observability/evidence/final-readiness.md`

## Reading Rule

- 这里的“问题”包含：
  - 已经真实发生的故障
  - 反复暴露的结构性缺口
  - 由人工多次追问才被补上的控制面能力
  - 现在虽然被补丁压住，但未来平台如果不机制化仍会复发的点
- 有些问题已经在旧体系里被局部修复。
- 但只要它曾经多次暴露、且根因仍属于对象模型/状态模型/runtime contract 缺位，就继续视为“真实问题”，不能因为补过一次就当不存在。

## A. 入口与控制面问题

### P-01 自然语言入口不能等价替代命令入口

- 真实表现：
  - 用户很早就明确要“从微信启动长期自动开发”，但系统最初并没有把这类输入视为严格命令，而更像聊天请求。
  - 后来不得不补出显式的前缀命令、路由脚本、启动/停止/状态/现场/审批映射。
- 为什么这是问题：
  - 一旦把“控制”交给自然语言碰运气，长时任务就没有稳定的控制语义。
  - 聊天入口和任务控制入口混在一起，会把命令歧义、误启动、误停止引进系统。
- 证据：
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/session-mining-from-019e1946-to-now.md`
  - `/Users/huangliang/project/OneOPS-ALL/AGENTS.md`

### P-02 控制面需要手机友好的短格式回报，而不是长文报告

- 真实表现：
  - 微信指挥链路一建立，系统立刻暴露“长报告不适合手机阅读”的问题。
  - 后面多次强调状态、进度、审批、阻断都要是极短、结构化、可扫读格式。
- 为什么这是问题：
  - 如果回报格式不受控，人工就很难及时做审批、修复、继续/停止判断。
  - 这不是 UI 文案问题，而是控制面交互协议问题。
- 证据：
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/session-mining-from-019e1946-to-now.md`

### P-03 人工审批不是附属动作，而是系统一级对象

- 真实表现：
  - 批准范围、有效期、允许范围、禁止范围、证据要求、凭据边界，后面都被写成了结构化审批块。
  - 审批信息不只是“人说过同意”，而是会影响能否继续执行、能否使用浏览器、能否碰真实凭据。
- 为什么这是问题：
  - 如果审批不是正式对象，就会被旧 blocked 状态、旧 handoff 或模糊语义覆盖。
  - 审批记录必须能被 controller、worker、repair、UI 共同读取，而不是只留在聊天历史里。
- 证据：
  - `docs/openclaw-autodev/stories/d2on.json`
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/weekly-session-mining-2026-05-17.md`

## B. Provider / Profile / Runtime 配置问题

### P-04 provider 名称、模型 profile、harness 入口最初不稳定

- 真实表现：
  - 最早阶段出现 `openai:default` 与 `openai-codex:*` 不匹配、provider 名不对、harness 入口不一致。
  - 同一链路里又出现“验证确认走 `provider=openai model=gpt-5.5 agentHarnessId=codex`，但 turn 超时并留下 aborted 记录”的情况。
- 为什么这是问题：
  - 模型身份、provider、harness 一旦不一致，控制器以为在调用 A，实际 worker 在跑 B。
  - 这会直接破坏重试、对账、限额判断和故障定位。
- 证据：
  - `~/.codex/sessions/2026/05/12/rollout-2026-05-12T07-01-26-019e1946-2012-7e41-9f3d-42bfbc37cbb0.jsonl`
  - `docs/openclaw-autodev/worker-adaptation-principles.md`

### P-05 模型额度、订阅限制、超时会直接击穿整条自动链

- 真实表现：
  - 从最早阶段开始就撞到 usage limit / timeout / aborted。
  - 不是任务逻辑错，而是 provider 层能力没有稳定承接。
- 为什么这是问题：
  - 如果控制面不知道 provider 的真实容量和失败类型，就会把 runtime 失败误判成业务失败或 story 失败。
  - 这类问题天然要求 profile 分层和 provider preflight。
- 证据：
  - `~/.codex/sessions/2026/05/12/rollout-2026-05-12T07-01-26-019e1946-2012-7e41-9f3d-42bfbc37cbb0.jsonl`
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/session-mining-from-019e1946-to-now.md`

### P-06 不同角色共享同一模型心智会导致全链不稳定

- 真实表现：
  - 主循环、worker、repair、planner 后面都被要求拆 profile。
  - `qwen` 适配尤其放大了问题：弱模型在混合 lane 中频繁卡住、跑偏、无事件。
- 为什么这是问题：
  - 角色不同，任务形态不同，允许的工具、上下文体积、失败恢复方式都不同。
  - “一个模型跑所有角色”在演示阶段能勉强工作，在真实长时自动化里会持续放大问题。
- 证据：
  - `docs/openclaw-autodev/worker-profile-mapping.md`
  - `docs/openclaw-autodev/strict-worker-profile.md`
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/weekly-session-mining-2026-05-17.md`

### P-07 外部能力没有先产品化，运行时才暴露缺口

- 真实表现：
  - 浏览器策略、gateway token、远程访问、数据库读权限、DevTools、provider token，很多都在 story 执行时才暴露。
  - `GatewayClientRequestError: HTTP 401: Your authentication token has been invalidated`、`browser navigation blocked by policy` 都是在执行阶段爆出来。
- 为什么这是问题：
  - 平台没有把“可用能力”当作前置条件，而是把它们混进 story 执行期才发现。
  - 这会让同一个 story 在不同 runtime 下表现完全不同，还难以重现。
- 证据：
  - `docs/openclaw-autodev/stories/d2on.json`
  - `~/.codex/sessions/2026/05/16/rollout-2026-05-16T21-18-04-019e30ef-d55f-7613-8afc-84173f9aedc3.jsonl`

### P-08 权限与系统级前提缺失时，系统缺少统一 preflight 语义

- 真实表现：
  - 最初的微信验证就被 macOS 辅助功能权限阻断，报出“不允许辅助访问”。
  - 后续浏览器验证又被 worker context policy 阻断。
- 为什么这是问题：
  - 这些都不是代码 bug，但会直接中断自动化。
  - 如果没有统一 preflight 和 blocker taxonomy，系统只会留下分散的失败日志。
- 证据：
  - `~/.codex/sessions/2026/05/12/rollout-2026-05-12T07-01-26-019e1946-2012-7e41-9f3d-42bfbc37cbb0.jsonl`
  - `docs/openclaw-autodev/stories/d2on.json`

## C. 会话、进程、生命周期问题

### P-09 进程存在不等于任务真的在正确执行

- 真实表现：
  - 多次出现 daemon 还在、但子 worker 已失联或状态已发散。
  - 会话里有非常具体的现场：`daemon none / lock stale`、`childAlive: true` 但 `rawSize: 0`、`lastEvent: prompt.submitted`。
- 为什么这是问题：
  - 旧体系曾把“有 pid / 有 daemon”近似当成“任务还活着”。
  - 这会误导 monitor、status、detail、人工判断。
- 证据：
  - `~/.codex/sessions/2026/05/16/rollout-2026-05-16T21-18-04-019e30ef-d55f-7613-8afc-84173f9aedc3.jsonl`
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/weekly-session-mining-2026-05-17.md`

### P-10 stale lock / stale gateway process / stale pointer 是高频系统病灶

- 真实表现：
  - 原始会话里直接出现 `killing 1 stale gateway process(es)`。
  - `lock stale owner=12383`、`stale current-story/current-prompt/current-execution-pack` 成为反复修补点。
- 为什么这是问题：
  - 它说明旧残留不是边角问题，而是长期运行下的常态风险。
  - 任何新 turn、repair、retry 都可能被上一个残留污染。
- 证据：
  - `~/.codex/sessions/2026/05/12/rollout-2026-05-12T07-01-26-019e1946-2012-7e41-9f3d-42bfbc37cbb0.jsonl`
  - `~/.codex/sessions/2026/05/16/rollout-2026-05-16T21-18-04-019e30ef-d55f-7613-8afc-84173f9aedc3.jsonl`
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/weekly-session-mining-2026-05-17.md`

### P-11 daemon 双实例、半启动、孤儿会话都曾真实发生

- 真实表现：
  - 本周挖矿明确提到 daemon 双实例、orphan session、半启动残留。
  - 后续才补启动互斥锁、runtime owner 锁、清理逻辑。
- 为什么这是问题：
  - 这说明生命周期模型不是先设计好的，而是在事故中被反向补出来。
  - 没有显式状态机时，重启、恢复、repair 都会互相踩踏。
- 证据：
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/weekly-session-mining-2026-05-17.md`

### P-12 `prompt.submitted` 后长时间没有有效进展，是弱 worker 的典型失效形态

- 真实表现：
  - 会话和挖矿都提到 `prompt.submitted` 后无任何 tool/event 或只有空 toolResult。
  - 这类 turn 很难从“还在思考”与“已经卡死”中区分。
- 为什么这是问题：
  - 如果系统不把“提交 prompt 之后的首个有效进展”作为正式信号，就会出现假活跃。
  - 对长时调度来说，这种 silent hang 比显式失败更糟。
- 证据：
  - `~/.codex/sessions/2026/05/16/rollout-2026-05-16T21-18-04-019e30ef-d55f-7613-8afc-84173f9aedc3.jsonl`
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/session-mining-from-019e1946-to-now.md`

### P-13 0B 状态文件说明“状态存在”与“状态可用”是两回事

- 真实表现：
  - 原始会话里出现 `20260516-211817-turn-1.json` 为 `0` 字节。
  - `rawSize: 0` 与 `sessionExists: true` 同时存在。
- 为什么这是问题：
  - 很多脚本只检查文件是否存在，但没有检查内容是否可用、是否完成落盘、是否属于当前 turn。
  - 这会直接污染 truth 汇总和 UI 摘要。
- 证据：
  - `~/.codex/sessions/2026/05/16/rollout-2026-05-16T21-18-04-019e30ef-d55f-7613-8afc-84173f9aedc3.jsonl`

## D. 状态真相与对象归并问题

### P-14 状态真相分裂是旧体系最核心的问题之一

- 真实表现：
  - `story.json`、`state.json`、progress、monitor summary、detail、最终 report 彼此打架。
  - 已经 `BLOCKED/APPROVAL` 的 story 会被后续别的结果冲成 `DONE`。
- 为什么这是问题：
  - 当 reducer 不唯一时，所有人都可能在“各自看起来对”的状态上做错误决策。
  - 这比单点代码 bug 更难定位，因为每一层都拿得到某种“看似合理”的答案。
- 证据：
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/weekly-session-mining-2026-05-17.md`
  - `docs/openclaw-autodev/references/runtime-rules.md`

### P-15 monitor / status / detail 曾经不是同一真源

- 真实表现：
  - 用户明确指出过 `monitor/status/detail` 读的不是同一套真源。
  - 后续才围绕“唯一真源”与聚合逻辑统一做修补。
- 为什么这是问题：
  - 只要展示层和控制层的读口径不同，人工看到的“现场”就可能已经失真。
- 证据：
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/session-mining-from-019e1946-to-now.md`

### P-16 旧 blocked / 旧 report / 旧 handoff 会覆盖新结论

- 真实表现：
  - 审批会被旧 blocked 结果覆盖。
  - 旧 session 的 blocker 可能压过新 approval 或新 reviewed 状态。
- 为什么这是问题：
  - 系统没有把“时间上更新”自动等价成“语义上更权威”。
  - 新结论与旧残留之间缺乏强制仲裁规则。
- 证据：
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/weekly-session-mining-2026-05-17.md`

### P-17 合成 ticket 会污染真实业务 ticket

- 真实表现：
  - 出现过 `blocked-story-pending`、`story-selection-failed`、`stale-technical-release` 这类控制器合成票据。
  - 合成票据一度可能覆盖真实业务 story 的判断。
- 为什么这是问题：
  - 控制器需要内部诊断票据，但这些票据不应回写成业务对象的最终真相。
  - 否则 story 会被框架自身的故障语义替代。
- 证据：
  - `docs/openclaw-autodev/stories/d2on.json`
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/weekly-session-mining-2026-05-17.md`

### P-18 `reviewed` / `draft` / `open` / `done` / `blocked` / `approval` 语义曾长期混线

- 真实表现：
  - story status、batch status、review status、loop status、UI summary status 混在一起使用。
  - 用户后来明确指出“story 编排一致性比较差”，并要求修复状态真源和状态命名。
- 为什么这是问题：
  - 这些状态属于不同层级，不应该在同一字段或同一视觉语义里直接混用。
- 证据：
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/session-mining-from-019e1946-to-now.md`
  - `docs/prd-autodev/oneops-poc-concern-autotest/review.md`

## E. Story 编排、批次治理、lane boundary 问题

### P-19 当前 story 注入会被旧 handoff 牵着走

- 真实表现：
  - 会话挖矿明确指出：queue 选对了，但 worker 被旧 handoff 牵引。
  - 后来大量问题被归因为“真正执行的不是当前队列想执行的 story”。
- 为什么这是问题：
  - 这会让调度器、队列和执行器之间失去基本一致性。
  - 选故事和执行故事变成两套现实。
- 证据：
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/session-mining-from-019e1946-to-now.md`
  - `docs/openclaw-autodev/worker-adaptation-principles.md`

### P-20 “没有可选 story”经常不是没活干，而是前一票语义没有被正确路由

- 真实表现：
  - `d2on.json` 多次记录 `Blocker: no selectable story because a prior story remains blocked`。
  - 这类问题常常不是 backlog 空，而是 blocked/approval/repair 没有走对路径。
- 为什么这是问题：
  - story selection 如果只看“可选性”而不看“为何不可选”，就会把流程问题伪装成排队问题。
- 证据：
  - `docs/openclaw-autodev/stories/d2on.json`

### P-21 PRD、执行、repair 三条链路的边界是后来才被迫修清的

- 真实表现：
  - runtime blocker 一度也回流 PRD。
  - planner、repair、approval 都抢 blocked 场景控制权。
  - 后来又收紧成：blocked/approval 不自动回 PRD，环境 blocker 去 `WaitingRepair`。
- 为什么这是问题：
  - 规划问题、执行问题、环境问题、权限问题混流后，系统很难判断下一步应该补文档、补代码、补环境还是等人。
- 证据：
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/weekly-session-mining-2026-05-17.md`

### P-22 PRD 过早拆成小 story 会丢掉 batch 规划价值

- 真实表现：
  - 后续明确提出 Program / Workstreams / Test Matrix / Story Batches，而不是粗暴直接出 story。
  - 周内总结再次强调 batch-first planning。
- 为什么这是问题：
  - 太早微切会让 planner 失去“轮次决策”能力，执行层又拿到太大或太碎的故事。
- 证据：
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/session-mining-from-019e1946-to-now.md`
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/weekly-session-mining-2026-05-17.md`

### P-23 混合 lane 被错误当成单能力 worker 任务下发

- 真实表现：
  - `d2on` 这种 discovery + browser + backend + docs + evidence 混合 lane，一度按单一 worker story 处理。
  - `qwen` 在这类 lane 上频繁卡死和跑偏。
- 为什么这是问题：
  - 混合编排 lane 应该由 controller 负责编译 execution pack，再拆给匹配能力的 worker。
  - 直接裸发给一个弱 worker 等于把编排责任偷偷下放给模型。
- 证据：
  - `docs/openclaw-autodev/worker-profile-mapping.md`
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/weekly-session-mining-2026-05-17.md`

### P-24 ticket 匹配与 story 命中曾经不精确

- 真实表现：
  - 用户指出 `Ticket` 无法精确命中 story，容易误挂前缀相似项。
- 为什么这是问题：
  - 精确票据命中是所有 repair、审批、detail、监控对账的前提。
  - 一旦命中错对象，后续所有操作都会看似成功、实则写错。
- 证据：
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/session-mining-from-019e1946-to-now.md`

## F. 验证、evidence、假完成问题

### P-25 “页面能打开/类型能过”曾多次被误当成真实完成

- 真实表现：
  - 从 D2 到 D2ON，用户不断收紧要求：不能只看 smoke，必须是真实业务链路、真实字段、真实验证。
  - 最后甚至明确“不要降级、兜底、假成功”。
- 为什么这是问题：
  - 如果 acceptance 不绑定真实证据，worker 很容易交付“看起来完成”的产物。
- 证据：
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/session-mining-from-019e1946-to-now.md`
  - `docs/openclaw-autodev/loops/d2on.conf`

### P-26 `DONE` 不能只靠模型 footer 决定

- 真实表现：
  - 周内总结直接指出：`report` 与 `truth` 不一致时，应以 verifier/truth 为准。
  - `D2ON-008` 这种故事里还专门出现“补缺失 evidence，替换 TBD，占位 blocker 不是 closure”。
- 为什么这是问题：
  - 模型可以说 done，但系统必须证明 done。
- 证据：
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/weekly-session-mining-2026-05-17.md`
  - `docs/openclaw-autodev/stories/d2on.json`

### P-27 blocker-only evidence 不是 closure

- 真实表现：
  - `d2on.json` 里明确写了：
  - 如果输出只有 blocker evidence，story 仍应 blocked，直到执行/repair 路径真正 rerun 或程序显式停止。
- 为什么这是问题：
  - 记录 blocker 是有价值的，但它不是业务完成。
- 证据：
  - `docs/openclaw-autodev/stories/d2on.json`

### P-28 浏览器可达性验证与真实执行验证不是一回事

- 真实表现：
  - `device-v2-onboarding-observability` 的 final readiness 明确说浏览器/只读层已验证，但 execute-path contract 仍未闭合。
  - 甚至特意说明本轮没有按 `开始执行`，因为那会跨到真实副作用。
- 为什么这是问题：
  - 容易把“读层可见”“UI 没问题”误当成“业务执行层已准备完毕”。
- 证据：
  - `docs/prd-autodev/device-v2-onboarding-observability/evidence/final-readiness.md`

### P-29 从截断 summary 反推成功与否是不可靠的

- 真实表现：
  - 周内总结专门提到修掉 discovery helper 从截断 summary 解析成功与否的问题。
- 为什么这是问题：
  - 这是典型的“读导出物推真相”，不是读真相源。
- 证据：
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/weekly-session-mining-2026-05-17.md`

### P-30 没有 durable evidence 文件时，历史成功声明不可被完全信任

- 真实表现：
  - `D2ON-008` 明确要求“补上之前标 done 但文件缺失的 durable artifacts”。
- 为什么这是问题：
  - 旧体系允许“报告说做了”，但文件层没留下足够证据。
  - 后续任何人都无法稳定复核。
- 证据：
  - `docs/openclaw-autodev/stories/d2on.json`

## G. Browser / 真实环境 / 凭据边界问题

### P-31 浏览器验证多次被 worker context 或 policy 阻断

- 真实表现：
  - `browser navigation blocked by policy`
  - `rerun from a browser-enabled context`
  - 即便审批通过，也可能因 worker context 不具备浏览器能力而无法执行。
- 为什么这是问题：
  - “有审批”不等于“当前 runtime 真能执行”。
  - 浏览器能力必须是 profile/runtime contract 的显式部分。
- 证据：
  - `docs/openclaw-autodev/stories/d2on.json`

### P-32 gateway token / auth token 失效会把真实验证直接打断

- 真实表现：
  - daemon log 出现 `HTTP 401: Your authentication token has been invalidated`。
  - 后续故事历史里又有 `gateway token synced to service config` 这类恢复说明。
- 为什么这是问题：
  - 鉴权失效不是偶发噪音，而是平台必须感知、分类、修复、回报的正式故障类。
- 证据：
  - `~/.codex/sessions/2026/05/16/rollout-2026-05-16T21-18-04-019e30ef-d55f-7613-8afc-84173f9aedc3.jsonl`
  - `docs/openclaw-autodev/stories/d2on.json`

### P-33 真实远程访问需求很早就存在，但工具与边界不是一开始就准备好的

- 真实表现：
  - `D2ON` 进入真设备、真 MySQL、真远程 discovery 后，远程访问工具、凭据边界、证据脱敏都成为重点。
- 为什么这是问题：
  - 这类能力不可能靠临时批准和临时脚本长期维持。
  - 需要稳定 runtime profile、凭据边界和 evidence redaction 约束。
- 证据：
  - `docs/openclaw-autodev/loops/d2on.conf`
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/session-mining-from-019e1946-to-now.md`

### P-34 敏感信息与 evidence 的边界需要系统强约束

- 真实表现：
  - 后期审批块和 loop 规则大量强调：token、cookie、密码、私钥、SNMP community 只能运行时使用，不能写入代码、文档、日志或 evidence。
- 为什么这是问题：
  - 一旦控制面、repair、browser 验证、远程登录都进入真实环境，凭据泄漏风险就从理论问题变成日常操作风险。
- 证据：
  - `docs/openclaw-autodev/loops/d2on.conf`
  - `docs/openclaw-autodev/stories/d2on.json`

## H. 文件分布式真相问题

### P-35 文件既当真相、又当缓存、又当交接、又当导出物

- 真实表现：
  - story、batch、state、progress、handoff、approval、current-story、current-prompt、execution-pack、evidence summary 分散在大量文件里。
  - 很多脚本、worker、人工步骤都在“读一个文件、判断、再写另一个文件”。
- 为什么这是问题：
  - 文件承担角色太多时，物理存在不等于语义正确，也很难形成事务边界。
- 证据：
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/weekly-session-mining-2026-05-17.md`

### P-36 从导出物反向重建真相是旧体系的系统债

- 真实表现：
  - 截断 summary 反推成功、旧 handoff 牵引新 story、status/detail 从不同文件拼出来，这些都属于“从投影层反推真相”。
- 为什么这是问题：
  - 一旦导出物不是强一致、不是原子生成、不是当前轮次，就会产生伪真相。
- 证据：
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/weekly-session-mining-2026-05-17.md`
  - `docs/openclaw-autodev/references/runtime-rules.md`

### P-37 文件残留会穿透轮次边界，污染新一轮调度

- 真实表现：
  - stale `current-story/current-prompt/current-execution-pack`
  - 旧 handoff、旧 report、空 state 文件持续影响新 turn
- 为什么这是问题：
  - 文件系统没有天然的“本轮对象隔离”与“旧轮失效”语义。
- 证据：
  - `docs/prd-autodev/generic-ai-autodev-platform/evidence/weekly-session-mining-2026-05-17.md`

## I. 前端与工作台层面的隐含问题

### P-38 现在前端虽然大方向已收口，但它承接的是旧体系里最难的对象

- 真实表现：
  - 当前前端收口文档已经把交互压到文案级细节。
  - 但它要展示的不是普通 CRUD，而是 `Program / docs / batch / readiness / blockers / profile / incident` 这些复杂对象。
- 为什么这是问题：
  - 如果对象真相和状态分层没先冻结，前端会被迫接住旧体系最混乱的字段。
  - 到那时前端不只是“页面还没定”，而是会被拿来补后端对象模型的漏洞。
- 证据：
  - `docs/prd-autodev/generic-ai-autodev-platform/frontend-final-alignment-checklist.md`
  - `docs/prd-autodev/generic-ai-autodev-platform/frontend-state-query-decision.md`
  - `docs/development/generic-ai-autodev-platform/candidate-04-prototype-list.md`

### P-39 `ready-for-openclaw` 本质上不是一个 badge，而是多对象归并结果

- 真实表现：
  - 前端文档已经把它收敛成 `summary panel`、`readiness-check result banner`、右侧 decision rail 同步。
  - 这恰好说明它不是单字段状态，而是文档、batch、blockers、missing fields、release gate 的聚合。
- 为什么这是问题：
  - 如果后端不给出稳定的 readiness truth，前端再好的交互也只能展示摇摆结果。
- 证据：
  - `docs/prd-autodev/generic-ai-autodev-platform/frontend-final-alignment-checklist.md`
  - `docs/prd-autodev/generic-ai-autodev-platform/frontend-workbench-decision.md`

## J. 这些问题为什么值得单独记下来

- 它们不是“旧系统烂，所以全推翻”的证据。
- 它们更像一组高价值矿脉：
  - 哪些对象必须先定义
  - 哪些状态必须严格分层
  - 哪些能力必须 preflight
  - 哪些失败不能再被伪装成业务完成
  - 哪些文件应该退回 artifact/export/cache 层
- 这份清单的价值不在于证明过去出过错，而在于：
  - 只要这些问题还没被机制化吸收，自动驾驶系统就极大概率会重演旧体系的补丁化路径。

## Immediate Takeaway

- 这一轮最真实的结论不是“已经找到一个大 bug”。
- 而是已经足够确认：旧体系反复出问题的核心，并不是单点实现差，而是以下 5 个层面长期缺少先验 contract：
  - 控制入口 contract
  - runtime/profile contract
  - 生命周期与 truth contract
  - lane / blocker / approval route contract
  - evidence / readiness contract
- 因此，下一步不该直接从实现切片开始，而应该先把这些问题反推成新的机制设计清单。
