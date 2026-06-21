# Alert AI Disposal Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a front-end-first `告警处置工作台` that starts from the alert list, opens with an AI first answer, supports follow-up investigation, and visibly demonstrates private-document learning inside the same operator journey.

**Architecture:** Add one new `aiops` route and one new workbench view, keep the alert list as the launch point, and drive the first version with curated demo state plus real OneOPS alert diagnosis and knowledge APIs where they already exist. The workbench should reuse existing alert, AI diagnosis, knowledge, and netpath seams instead of inventing parallel contracts.

**Tech Stack:** Vue 3 `<script setup>`, TypeScript, Ant Design Vue, existing OneOPS router/menu system, existing `api/aiops.ts` contracts, existing alert route state, source-based smoke scripts, `vue-tsc`.

---

### Task 1: Lock the route and smoke contract

**Files:**
- Create: `OneOPS-UI/scripts/alert-disposal-workbench-smoke.ts`
- Modify: `OneOPS-UI/package.json`
- Modify: `OneOPS-UI/src/router/utils.ts`
- Test: `OneOPS-UI/scripts/alert-disposal-workbench-smoke.ts`

- [ ] **Step 1: Write the failing smoke script**

```ts
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) {
    throw new Error(message);
  }
}

const root = resolve(process.cwd(), 'src');
const routerSource = readFileSync(resolve(root, 'router/utils.ts'), 'utf8');
const alarmSource = readFileSync(resolve(root, 'views/alert/Alarm.vue'), 'utf8');
const pageSource = readFileSync(resolve(root, 'views/aiops/AlertDisposalWorkbench.vue'), 'utf8');

assert(routerSource.includes("name: 'AlertDisposalWorkbench'"), 'missing AlertDisposalWorkbench route');
assert(routerSource.includes("path: 'aiops/alert-disposal-workbench'"), 'missing alert disposal workbench path');
assert(alarmSource.includes('进入处置工作台'), 'missing alert workbench entry action');
assert(pageSource.includes('AI 对话调查流'), 'missing conversational investigation section');
assert(pageSource.includes('自动学习卡组'), 'missing learning side rail');

console.log('alert disposal workbench smoke passed');
```

- [ ] **Step 2: Run smoke to verify it fails**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && node scripts/alert-disposal-workbench-smoke.ts`
Expected: FAIL because the smoke file is not bundled or the new route/page does not exist yet.

- [ ] **Step 3: Add the package command**

```json
"smoke:alert-disposal-workbench": "npx esbuild scripts/alert-disposal-workbench-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/alert-disposal-workbench-smoke.mjs >/dev/null && node .tmp/alert-disposal-workbench-smoke.mjs"
```

- [ ] **Step 4: Register the new hidden route**

```ts
const alertDisposalWorkbenchRoute: RouteRecordRaw = {
  path: 'aiops/alert-disposal-workbench',
  name: 'AlertDisposalWorkbench',
  component: () => import('@/views/aiops/AlertDisposalWorkbench.vue'),
  meta: {
    title: '告警处置工作台',
    requiresAuth: true,
    hideInMenu: true,
  },
};
```

- [ ] **Step 5: Add the route to the dynamic children list**

```ts
if (
  !children.some(
    route => route.path === alertDisposalWorkbenchRoute.path || route.name === alertDisposalWorkbenchRoute.name,
  )
) {
  children.push(alertDisposalWorkbenchRoute);
}
```

- [ ] **Step 6: Re-run smoke and keep it failing for the right reason**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run smoke:alert-disposal-workbench`
Expected: FAIL on missing page source or missing alert entry action, not on script syntax.

### Task 2: Build the seeded workbench shell and page data contract

**Files:**
- Create: `OneOPS-UI/src/views/aiops/alert-disposal-workbench-data.ts`
- Create: `OneOPS-UI/src/views/aiops/AlertDisposalWorkbench.vue`
- Test: `OneOPS-UI/scripts/alert-disposal-workbench-smoke.ts`

- [ ] **Step 1: Create the local seeded data model**

```ts
export interface DisposalWorkbenchMessage {
  id: string;
  role: 'assistant' | 'user';
  kind: 'summary' | 'follow_up' | 'evidence';
  text: string;
  citations?: string[];
}

export interface DisposalWorkbenchEvidenceCard {
  key: 'device' | 'logs' | 'metrics' | 'netpath' | 'history';
  title: string;
  summary: string;
  actionLabel: string;
}

export interface DisposalWorkbenchLearningCard {
  uploadName: string;
  parseStatus: 'idle' | 'parsed' | 'extracted';
  extractionSummary: string;
  hitSummary: string;
}

export function buildAlertDisposalWorkbenchSeed() {
  return {
    alertTitle: '华东一区核心出口 BGP 邻居抖动，触发业务路径收敛异常',
    severity: 'P2',
    targetDeviceName: 'BJ-DC1-LEAF-07',
    firstObservedAt: '2026-06-21 09:42:17',
    durationText: '持续 18 分钟',
    businessImpact: ['统一认证', '工单门户', '南北向 API'],
    aiJudgement: '更可能是边界 BGP 邻居抖动，不支持“链路物理中断”为首因',
    messages: [
      {
        id: 'assistant-first-answer',
        role: 'assistant',
        kind: 'summary',
        text: '综合当前告警、日志样本与 RCA 证据，更可能是 BJ-DC1-LEAF-07 的 BGP 邻居抖动导致出口路径收敛异常。建议先查看邻居稳定性，再确认是否存在对端抖动。',
        citations: ['rca:v2:candidate:device:BJ-DC1-LEAF-07', 'uploaded-log:sample-01'],
      },
    ] satisfies DisposalWorkbenchMessage[],
    evidenceCards: [
      { key: 'device', title: '设备参数', summary: '边界交换机，双上联，BFD 已启用', actionLabel: '查看设备详情' },
      { key: 'logs', title: '最近日志', summary: '15 分钟内 4 次邻居重建，未见接口 down', actionLabel: '查看日志片段' },
      { key: 'metrics', title: '指标快照', summary: 'BFD flap 与路由收敛延时同时抬升', actionLabel: '查看指标证据' },
      { key: 'netpath', title: '网络路径', summary: '异常集中在 LEAF-07 至 PE-02 区段', actionLabel: '查看网络路径' },
      { key: 'history', title: '相似案例', summary: '近 30 天同类事件 2 次，均与邻居抖动相关', actionLabel: '查看历史案例' },
    ] satisfies DisposalWorkbenchEvidenceCard[],
    learningCard: {
      uploadName: '出口链路抖动排查手册-v3.docx',
      parseStatus: 'idle',
      extractionSummary: '尚未上传私有文档',
      hitSummary: '当前仅命中平台知识与 SOP',
    } satisfies DisposalWorkbenchLearningCard,
    suggestedPrompts: [
      '为什么判断是 BGP 邻居抖动，而不是链路中断？',
      '只看这台设备最近 15 分钟日志',
      '给我最短排查步骤，限制在只读命令',
    ],
  };
}
```

- [ ] **Step 2: Implement the workbench shell page**

```vue
<template>
  <div class="alert-disposal-workbench page-container">
    <section class="workbench-header">
      <div>
        <h1>告警处置工作台</h1>
        <p>从当前告警出发，围绕证据、追问和知识沉淀完成一次处置闭环。</p>
      </div>
      <a-space>
        <a-button @click="markMitigated">标记已缓解</a-button>
        <a-button type="primary" @click="openKnowledgeWriteback">沉淀知识</a-button>
      </a-space>
    </section>

    <section class="summary-bar">
      <a-card :bordered="false">
        <strong>{{ seed.alertTitle }}</strong>
        <div>{{ seed.severity }} · {{ seed.targetDeviceName }} · {{ seed.firstObservedAt }} · {{ seed.durationText }}</div>
        <div>{{ seed.aiJudgement }}</div>
      </a-card>
    </section>

    <section class="content-grid">
      <a-card title="AI 对话调查流" :bordered="false">
        <div class="message-list"></div>
        <a-input v-model:value="promptInput" placeholder="继续追问当前告警，例如：只看这台设备最近 15 分钟日志" />
      </a-card>
      <div class="side-rails">
        <a-card title="证据联动卡组" :bordered="false">
          <div class="evidence-card-list"></div>
        </a-card>
        <a-card title="自动学习卡组" :bordered="false">
          <div class="learning-card-panel"></div>
        </a-card>
      </div>
    </section>
  </div>
</template>
```

- [ ] **Step 3: Render the seeded message stream, prompt chips, and evidence cards**

```ts
const seed = reactive(buildAlertDisposalWorkbenchSeed());
const promptInput = ref('');

function applySuggestedPrompt(prompt: string) {
  promptInput.value = prompt;
}
```

```vue
<a-space wrap>
  <a-tag v-for="prompt in seed.suggestedPrompts" :key="prompt" class="prompt-chip" @click="applySuggestedPrompt(prompt)">
    {{ prompt }}
  </a-tag>
</a-space>

<div v-for="message in seed.messages" :key="message.id" class="message-card">
  <div class="message-role">{{ message.role === 'assistant' ? 'AI' : '工程师' }}</div>
  <div class="message-text">{{ message.text }}</div>
  <a-space v-if="message.citations?.length" wrap>
    <a-tag v-for="citation in message.citations" :key="citation">{{ citation }}</a-tag>
  </a-space>
</div>
```

- [ ] **Step 4: Re-run the smoke script**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run smoke:alert-disposal-workbench`
Expected: FAIL only on the missing alert launch action if the route and page now exist.

### Task 3: Wire alert-list handoff and AI first-answer hydration

**Files:**
- Create: `OneOPS-UI/src/views/aiops/alert-disposal-workbench-handoff.ts`
- Modify: `OneOPS-UI/src/views/aiops/AlertDisposalWorkbench.vue`
- Modify: `OneOPS-UI/src/views/alert/Alarm.vue`
- Test: `OneOPS-UI/scripts/alert-disposal-workbench-smoke.ts`
- Test: `OneOPS-UI/scripts/alert-ai-diagnosis-smoke.ts`

- [ ] **Step 1: Add a route-query handoff helper**

```ts
import type { AlertAlarmResp } from '@/typings';

export interface AlertDisposalWorkbenchRouteQuery {
  alertCode: string;
  tenantID: string;
  targetID: string;
  targetName: string;
  observedAt: string;
  summary: string;
}

export function buildAlertDisposalWorkbenchRouteQuery(record: AlertAlarmResp): AlertDisposalWorkbenchRouteQuery {
  return {
    alertCode: String(record.code || ''),
    tenantID: String(record.tenant_code || record.labels?.tenant_code || ''),
    targetID: String(record.rca_identity?.target_id || record.labels?.device_code || ''),
    targetName: String(record.labels?.device_name || record.labels?.hostname || ''),
    observedAt: String(record.fired_at || record.active_at || record.sample_ts || ''),
    summary: String(record.summary || record.description || ''),
  };
}
```

- [ ] **Step 2: Add the alert launch action in `Alarm.vue`**

```ts
import { useRouter } from 'vue-router';
import { buildAlertDisposalWorkbenchRouteQuery } from '@/views/aiops/alert-disposal-workbench-handoff';

const router = useRouter();

function openAlertDisposalWorkbench(record: AlertAlarmResp) {
  router.push({
    name: 'AlertDisposalWorkbench',
    query: buildAlertDisposalWorkbenchRouteQuery(record),
  });
}
```

```vue
<a-button type="link" size="small" @click="openAlertDisposalWorkbench(record)">进入处置工作台</a-button>
```

- [ ] **Step 3: Hydrate the workbench from route query and auto-run alert diagnosis**

```ts
import { useRoute, useRouter } from 'vue-router';
import { diagnoseAIOpsAlertReq } from '@/api/aiops';
import type { AIOpsAlertDiagnosisReq } from '@/typings/aiops';

const route = useRoute();
const router = useRouter();
const diagnosisLoading = ref(false);

function buildDiagnosisRequestFromRoute(): AIOpsAlertDiagnosisReq | null {
  const alertID = String(route.query.alertCode || '');
  const tenantID = String(route.query.tenantID || '');
  const targetID = String(route.query.targetID || '');
  const targetName = String(route.query.targetName || targetID || '');
  const observedAt = String(route.query.observedAt || '');
  const summary = String(route.query.summary || '');
  if (!alertID || !tenantID || !targetID || !observedAt) return null;
  return {
    alert_id: alertID,
    tenant_id: tenantID,
    observed_at: observedAt,
    target: { type: 'device', id: targetID, name: targetName },
    metadata: summary ? { summary } : undefined,
  };
}
```

- [ ] **Step 4: Merge the diagnosis response into the message stream**

```ts
async function hydrateFirstAnswer() {
  const req = buildDiagnosisRequestFromRoute();
  if (!req) return;
  diagnosisLoading.value = true;
  try {
    const resp = await diagnoseAIOpsAlertReq(req);
    seed.messages = [
      {
        id: 'assistant-first-answer',
        role: 'assistant',
        kind: 'summary',
        text: resp.report.summary,
        citations: resp.report.citations.map(item => item.id),
      },
    ];
  } finally {
    diagnosisLoading.value = false;
  }
}
```

- [ ] **Step 5: Re-run smoke plus the existing alert diagnosis smoke**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run smoke:alert-disposal-workbench && npm run smoke:alert-ai-diagnosis`
Expected: PASS for the new smoke and PASS for the existing alert diagnosis smoke.

### Task 4: Add follow-up Q&A, evidence actions, and learning flow

**Files:**
- Modify: `OneOPS-UI/src/views/aiops/AlertDisposalWorkbench.vue`
- Modify: `OneOPS-UI/src/views/aiops/alert-disposal-workbench-data.ts`
- Test: `OneOPS-UI/scripts/alert-disposal-workbench-smoke.ts`
- Test: `OneOPS-UI/scripts/aiops-knowledge-sop-smoke.ts`
- Test: `OneOPS-UI/scripts/netpath-route-smoke.ts`

- [ ] **Step 1: Add local follow-up message append behavior**

```ts
function submitFollowUp() {
  const text = promptInput.value.trim();
  if (!text) return;
  seed.messages.push({ id: `user-${Date.now()}`, role: 'user', kind: 'follow_up', text });
  seed.messages.push({
    id: `assistant-${Date.now()}`,
    role: 'assistant',
    kind: 'follow_up',
    text: text.includes('15 分钟日志')
      ? '近 15 分钟未观察到接口 down，但 BFD 会话出现 3 次 flap，09:39 至 09:46 之间 BGP 邻居完成 4 次重建。'
      : text.includes('只读命令')
        ? '建议先执行只读排查：show bgp peer summary，然后查看 show bfd session peer。'
        : '当前更支持“邻居抖动”而不是“物理链路中断”，因为日志和 RCA 候选都没有出现接口 down 证据。',
    citations: text.includes('15 分钟日志')
      ? ['uploaded-log:sample-01']
      : ['rca:v2:candidate:device:BJ-DC1-LEAF-07'],
  });
  promptInput.value = '';
}
```

- [ ] **Step 2: Add side-card actions for full-page deep links**

```ts
function openEvidenceCard(key: DisposalWorkbenchEvidenceCard['key']) {
  if (key === 'netpath') {
    router.push({ name: 'NetworkPathIndex' });
    return;
  }
  if (key === 'history') {
    router.push({ name: 'AIOpsKnowledgeSOP', query: { tenant_id: route.query.tenantID || '' } });
    return;
  }
}
```

- [ ] **Step 3: Add the visible learning flow using existing AIOps knowledge APIs**

```ts
import {
  createAIOpsKnowledgeDocumentReq,
  createAIOpsKnowledgeSpaceReq,
  listAIOpsKnowledgeSpacesReq,
  listAIOpsKnowledgeChunksReq,
  parseAIOpsKnowledgeDocumentReq,
  searchAIOpsKnowledgeReq,
} from '@/api/aiops';

async function runLearningDemo() {
  const tenantID = String(route.query.tenantID || 'TENANT-A');
  const spaces = await listAIOpsKnowledgeSpacesReq(tenantID);
  const space = spaces[0] || (await createAIOpsKnowledgeSpaceReq({ tenant_id: tenantID, name: '网络故障知识空间' }));
  const document = await createAIOpsKnowledgeDocumentReq({
    tenant_id: tenantID,
    space_id: space.id,
    title: '出口链路抖动排查手册-v3',
    tags: ['bgp', 'edge', 'flap'],
    manual_text: '当 BGP 邻居短时间内多次重建，且未观察到接口 down 时，应优先检查 BFD 会话抖动与对端 keepalive 差异。',
  });
  await parseAIOpsKnowledgeDocumentReq(tenantID, document.id);
  const chunks = await listAIOpsKnowledgeChunksReq(tenantID, document.id);
  const hit = await searchAIOpsKnowledgeReq({
    tenant_id: tenantID,
    query: 'BGP 邻居抖动但接口未 down 时应该先看什么',
  });
  seed.learningCard = {
    uploadName: document.title,
    parseStatus: chunks.length > 0 ? 'extracted' : 'parsed',
    extractionSummary: `已抽取 ${chunks.length} 个知识切片`,
    hitSummary: `当前问答已命中 ${hit.chunks.length} 条私有文档片段`,
  };
}
```

- [ ] **Step 4: Re-run smoke plus knowledge and netpath smoke**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run smoke:alert-disposal-workbench && npm run smoke:aiops-knowledge-sop && npm run smoke:netpath-route`
Expected: PASS for the new workbench smoke and PASS for both existing reuse-path smokes.

### Task 5: Verify compile safety and ship the plan slice

**Files:**
- Modify: `OneOPS-UI/package.json`
- Modify: `OneOPS-UI/src/router/utils.ts`
- Modify: `OneOPS-UI/src/views/alert/Alarm.vue`
- Create: `OneOPS-UI/src/views/aiops/AlertDisposalWorkbench.vue`
- Create: `OneOPS-UI/src/views/aiops/alert-disposal-workbench-data.ts`
- Create: `OneOPS-UI/src/views/aiops/alert-disposal-workbench-handoff.ts`
- Create: `OneOPS-UI/scripts/alert-disposal-workbench-smoke.ts`
- Test: `OneOPS-UI/package.json`

- [ ] **Step 1: Run scoped type safety**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run typecheck`
Expected: PASS, or only pre-existing unrelated failures that are already reproducible before this feature branch.

- [ ] **Step 2: Run the focused smoke pack**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run smoke:alert-disposal-workbench && npm run smoke:alert-ai-diagnosis && npm run smoke:aiops-knowledge-sop && npm run smoke:netpath-route`
Expected: PASS for all four commands.

- [ ] **Step 3: Run the production build if typecheck is clean**

Run: `cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run build`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git -C /Users/huangliang/project/OneOPS-ALL/OneOPS-UI add package.json scripts/alert-disposal-workbench-smoke.ts src/router/utils.ts src/views/alert/Alarm.vue src/views/aiops/AlertDisposalWorkbench.vue src/views/aiops/alert-disposal-workbench-data.ts src/views/aiops/alert-disposal-workbench-handoff.ts
git -C /Users/huangliang/project/OneOPS-ALL/OneOPS-UI commit -m "feat: add alert ai disposal workbench demo"
```
