# OneOPS Alert AI Disposal Workbench Design

## Goal

Build a front-end-first OneOPS demo around a new alert-driven disposal workbench that turns three requirement threads into one coherent journey:

- natural-language AI Q&A for operations troubleshooting
- alert and symptom-driven root cause analysis with concrete evidence and next steps
- automatic learning from tenant-private documents, with extracted knowledge flowing back into the same Q&A experience

This is a demo-oriented slice. The primary objective is not to finish full productization, but to make the experience feel like a credible OneOPS capability that already belongs inside the platform.

## Confirmed Scope

### Primary audience

- first-line engineers, who care about operational speed, evidence, and the shortest path to action

### Secondary audience

- operations leads and architects, who care about closed-loop handling, collaboration, and knowledge accumulation

### Primary narrative

- alert-driven disposal

### Chosen solution direction

- create a new `告警处置工作台` as a shell page
- keep `告警中心列表` as the main entry
- reuse existing OneOPS pages, APIs, and data contracts wherever possible
- move AI from a side drawer toy into the center of the handling flow
- make knowledge learning visible in the same journey instead of hiding it inside a standalone knowledge page

## Problem Statement

Current OneOPS UI assets already cover many relevant domains:

- alert list and alert detail
- AI diagnosis drawer
- device logs
- network path and topology
- knowledge and SOP management
- unified monitoring operations

But the current experience is still fragmented:

- AI diagnosis is mostly rendered as a report, not a conversational investigation flow
- knowledge and SOP capabilities exist, but the learning loop is not visible during incident handling
- evidence and linked context are distributed across separate pages
- the user journey does not yet feel like a single operator workspace

The demo should solve that fragmentation without pretending OneOPS is a completely different product.

## Design Principles

### 1. Start from a real operator entry

The main entry remains the alert list. The user should enter from a familiar operational object, not from an abstract AI homepage.

### 2. AI must live inside the handling flow

AI should not appear as an isolated chat toy or a detached analytics panel. It should help the user investigate the current alert, explain evidence, answer follow-up questions, and suggest the next read-only troubleshooting step.

### 3. Reuse existing OneOPS evidence chains

The demo must continue to rely on existing OneOPS domains:

- alert data
- device identity and parameters
- logs
- topology and path context
- SOP and knowledge retrieval

This keeps the demo credible and minimizes fake data seams.

### 4. Automatic learning must be visible

The private-document learning loop must be demonstrable:

- upload document
- parse and extract
- write into tenant knowledge space
- hit the current Q&A flow with newly learned content

### 5. Demo data must feel operationally plausible

Avoid inflated global metrics and vague platform slogans. Prefer a single believable incident with specific devices, timestamps, business impact, confidence levels, citations, and steps.

## Reference Patterns

The chosen interaction direction is informed by several official product patterns:

- Datadog Bits AI SRE investigation flow, which centers AI on issue investigation and operational context
- Dynatrace Assist / Dynatrace Intelligence, which emphasizes natural-language exploration of environment data and suggested troubleshooting guides
- ServiceNow Service Operations Workspace, which organizes incident handling in a single workspace with contextual actions and post-incident carry-through
- Elastic AI Assistant for Observability, which combines chat, environment data, and proprietary/runbook knowledge

These references influence the shape of the journey, not the visual identity. OneOPS should still look like an extension of its own platform.

Reference links:

- [Datadog Bits AI SRE investigate issues](https://docs.datadoghq.com/bits_ai/bits_ai_sre/investigate_issues/)
- [Dynatrace Intelligence agentic and generative AI](https://docs.dynatrace.com/docs/dynatrace-intelligence/agentic-and-generative-ai)
- [Dynatrace Assist](https://docs.dynatrace.com/docs/dynatrace-intelligence/agentic-and-generative-ai/chat-with-dynatrace-assist)
- [Service Operations Workspace](https://www.servicenow.com/products/service-operations-workspace.html)
- [ServiceNow incident management in Service Operations Workspace](https://www.servicenow.com/docs/r/it-service-management/service-operations-workspace/incident-sow.html)
- [Elastic AI Assistant for Observability](https://www.elastic.co/docs/solutions/observability/ai/observability-ai-assistant)
- [Elastic AI Assistant product page](https://www.elastic.co/elasticsearch/ai-assistant)

## User Journey

### End-to-end flow

```text
告警中心列表
  -> 进入处置工作台
  -> 查看 AI 首轮诊断
  -> 继续追问
  -> 查看设备 / 日志 / 路径 / 相似案例 / SOP 命中
  -> 上传私有文档并触发学习
  -> 用新知识继续追问
  -> 标记处置结论
  -> 沉淀知识或 SOP
  -> 返回告警闭环
```

### Detailed operator sequence

1. The user opens `告警中心列表` and sees a believable high-priority network incident.
2. The user clicks `进入处置工作台`.
3. The workbench lands on a ready-made AI first answer rather than an empty chat state.
4. The user reads:
   - what happened
   - likely root cause
   - cited evidence
   - the shortest next step
5. The user asks follow-up questions in natural language.
6. The workbench responds using current alert context plus linked platform evidence.
7. The user opens device, log, path, and knowledge evidence from the same page.
8. The user uploads a private troubleshooting document and sees parse/extract status.
9. The user asks another question and sees the newly learned private knowledge cited in the answer.
10. The user records a handling conclusion and optionally promotes the result into SOP knowledge.

## Information Architecture

### Entry structure

- primary entry: `告警中心列表`
- secondary entry from alert detail: `进入处置工作台`
- supporting entry: `AIOps > 知识与SOP`

The new workbench is not a replacement for the alert list. It is a handling destination for selected incidents.

### Page structure

#### Top summary bar

Purpose:

- establish incident identity and urgency in one screen
- avoid forcing the user to reconstruct the alert context from scattered sections

Content:

- alert title
- severity
- affected business scope
- target device
- first observed time
- current handling state
- assignee
- one-sentence AI first judgment

#### Action area

Purpose:

- keep operational actions obvious and close to the incident

Actions:

- acknowledge
- transfer
- create collaboration ticket
- mark mitigated
- mark resolved
- write to knowledge

#### Core area: AI conversational investigation flow

This is the primary visual center of the page.

Content:

- AI first answer
- follow-up message stream
- root cause explanation
- cited evidence cards embedded in answers
- shortest read-only troubleshooting steps
- missing-evidence prompts

The chat must never be generic. Every answer should feel grounded in the current incident and OneOPS evidence context.

#### Evidence side cards

Purpose:

- make context review fast without forcing hard page switches

Cards:

- device parameters
- recent logs
- metric snapshot
- network path / topology
- similar incident history
- change history if available

#### Learning side cards

Purpose:

- make automatic learning visible inside the same journey

Cards:

- private document upload
- parsing status
- extraction status
- chunk preview
- tenant knowledge-space inclusion
- knowledge hit list for the current incident

#### Bottom record area

Purpose:

- support closure and governance

Content:

- handling timeline
- operator notes
- evidence viewed
- AI questions asked
- final conclusion
- SOP / knowledge write-back action

## Core Experience Behavior

### AI first answer behavior

The workbench should not open with a blank prompt. It should open with a first answer generated from the selected alert context.

The first answer should include:

- incident summary
- likely primary cause
- alternative cause if confidence is not decisive
- key citations
- shortest recommended next check

### Follow-up Q&A behavior

Example prompts:

- `为什么判断是 BGP 邻居抖动，而不是链路中断？`
- `只看这台设备最近 15 分钟日志`
- `给我最短排查步骤，限制在只读命令`
- `这个问题历史上怎么处理过？`
- `新上传的手册里有没有针对这个现象的建议？`

Expected behavior:

- each follow-up should stay anchored to the same incident context
- answers may pull in logs, device metadata, topology evidence, and knowledge hits
- citations should remain visible and traceable
- suggested commands remain read-only and approval-aware

### Learning behavior

The learning loop must be visible in the demo:

1. upload a private document
2. show parse and extraction state
3. preview extracted chunks
4. confirm they are attached to the tenant knowledge space
5. let the next AI answer cite the learned content

This behavior is essential to satisfy the automatic learning requirement.

## Demo Data Strategy

The demo should center on one believable incident rather than broad synthetic dashboards.

### Recommended incident

- title: `华东一区核心出口 BGP 邻居抖动，触发业务路径收敛异常`
- severity: `P2`
- first observed time: `2026-06-21 09:42:17`
- current duration: `18 分钟`
- target device: `BJ-DC1-LEAF-07`
- related business scope:
  - 统一认证
  - 工单门户
  - 南北向 API
- related alerts in last 15 minutes: `6`

### Recommended AI fields

- confidence: `0.78` to `0.84`
- primary cause candidates: `2` to `3`
- private knowledge hits: `2`
- platform knowledge hits: `3`
- SOP hits: `1`

### Recommended evidence wording

- `近 15 分钟未观察到接口 down 事件，但 BFD 会话出现 3 次 flap`
- `边界设备 BGP 邻居 172.21.14.1 在 09:39 至 09:46 间发生 4 次重新建立`
- `网络路径快照显示出口收敛延迟集中在 BJ-DC1-LEAF-07 至 PE-02 区段`
- `已命中租户私有文档《出口链路抖动排查手册》2 个片段`

### Content style

Avoid:

- empty transformation slogans
- exaggerated platform-wide numbers
- confidence claims that look fabricated

Prefer:

- short operational sentences
- evidence-led conclusions
- explicit uncertainty when appropriate
- language that sounds like an engineer speaking to another engineer

## Copy Direction

### Good examples

- `更可能是边界 BGP 邻居抖动，不支持“链路物理中断”为首因`
- `建议先执行只读排查：show bgp peer summary`
- `当前证据不足以确认对端运营商侧异常，建议补看 09:35 到 09:50 的邻居状态变化`
- `已命中 SOP《出口路径收敛异常首轮排查》`

### Avoid

- `智能赋能运维闭环`
- `大模型驱动平台价值升级`
- `自动化提效 80%`

## Mapping to Existing OneOPS UI Assets

### Reuse directly

- alert list and current detail interactions from `src/views/alert/Alarm.vue`
- AI diagnosis content model from `src/views/alert/AlarmAIDiagnosisDrawer.vue`
- alert-to-diagnosis request builder from `src/views/alert/alarm_ai_diagnosis.ts`
- knowledge and SOP lifecycle from `src/views/aiops/AIOpsKnowledgeSOP.vue`
- AI analysis workbench ideas from `src/views/aiops/AIOpsWorkbench.vue`
- device log domain from `src/views/device/DeviceLog.vue`
- network path entry from `src/views/topology/NetPathMvp.vue`
- workbench-like interaction framing from `src/views/platform/UnifiedMonitoringOperations.vue`

### Wrap or adapt

- existing AI diagnosis drawer content should be re-rendered into a conversational flow rather than only a drawer report
- device log data should be displayed as a contextual side card before sending the user to the full page
- knowledge search and SOP hit lists should be embedded as lightweight evidence cards

### New front-end pieces

- `src/views/aiops/AlertDisposalWorkbench.vue`
- conversation-flow component for AI answers and follow-up prompts
- evidence card group for device, logs, metrics, path, and history
- knowledge-learning card group for upload, parse, extract, and hit preview
- shared state layer for current incident, conversation, evidence, and learning status

## Route And Navigation Proposal

### Route

Add a new route under the existing AIOps or Alert-facing navigation, but keep the practical entry attached to alerts.

Recommended path:

- `/aiops/alert-disposal-workbench`

Recommended launch behavior:

- the alert list passes alert code and minimal context into the workbench
- the workbench loads the AI first answer automatically

### Entry actions

Add `进入处置工作台` to:

- high-priority alert row actions
- alert detail action area
- AI diagnosis drawer optional deep-link action if needed

## Implementation Tiers

### P0: demo shell version

Recommended for this task.

Shape:

- build the new workbench shell page
- reuse existing APIs and views as much as possible
- use front-end orchestration and carefully prepared demo data for continuity
- focus on complete user journey and credible interactions

Why:

- fastest path to a convincing demo
- lowest delivery risk
- enough freedom to make the flow feel finished

### P1: semi-real linked version

Shape:

- replace more stitched data with real linked API calls
- reduce manually composed answer state
- strengthen actual retrieval, logs, and knowledge hits

Why:

- improves credibility
- lowers risk during live demos

### P2: productized version

Shape:

- formal conversational AI contract
- stronger knowledge-learning state machine
- persistent audit and handling records
- cleaner backend aggregation seams

Why:

- suitable for long-term productization
- out of scope for the immediate front-end demo

## Recommended Implementation Direction

Proceed with `P0 demo shell version`.

Why this is the best fit:

- it satisfies the user's priority on front-end completeness and journey smoothness
- it maximizes reuse of the current OneOPS platform
- it allows realistic data and wording control
- it is the highest-probability path to a convincing result in a short timeframe

## Risks And Controls

### Risk: AI feels like a static report

Control:

- render the main area as a conversation flow
- provide meaningful follow-up prompt chips or free input

### Risk: learning flow feels tacked on

Control:

- place upload and extraction status in the workbench side rail
- show the new document cited by the next answer

### Risk: page becomes overloaded

Control:

- keep the top summary tight
- show only the highest-value side cards by default
- defer full-detail pages to deep links

### Risk: fake-looking data hurts credibility

Control:

- use one incident with specific fields
- keep counts low and believable
- avoid impossible precision and inflated impact claims

## Testing And Demo Readiness

The front-end demo should be considered ready when the following are true:

- entering from the alert list feels natural
- the workbench first screen answers `what happened`, `why`, and `what next`
- at least 2 to 3 follow-up questions feel context-aware
- log, device, path, and SOP evidence are visible without hunting
- private document learning is demonstrated end-to-end
- closure actions and knowledge write-back are visible
- copy feels like real operations language

## Out Of Scope For This Slice

- fully generalized multi-incident case management
- broad platform-wide AI homepage
- backend-heavy re-architecture of the diagnosis pipeline
- unrestricted command execution from AI output
- long-tail governance workflows beyond the visible demo closure

## Final Decision Summary

The confirmed design is:

- keep alerts as the primary entry
- add a new alert disposal workbench shell
- center the page on conversational AI investigation
- surface evidence and private-document learning in the same handling flow
- close the loop through knowledge and SOP accumulation
- implement the demo in a front-end-first P0 mode using maximum OneOPS reuse
