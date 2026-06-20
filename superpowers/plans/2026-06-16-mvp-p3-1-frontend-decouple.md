# P3-1 前端脱钩:策略集详情抽屉降只读 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 把 `StrategySetDetailDrawer.vue` 从"编辑/生成/录制"界面降为**只读详情**,删除 6 个仅供其使用的 SNMP 生成/录制状态模块,并精简 `teleabs.ts` 中对应的 13 个生成/录制 API 函数——为后续后端拆除(P3-2+)先脱钩。

**Architecture:** 纯删除式重构。抽屉只保留只读元数据 + 策略项表;删除的状态模块与 teleabs 函数经全仓 grep 确认**零外部消费者**。验证靠 `vue-tsc` typecheck(无悬空引用)+ build。

**Tech Stack:** Vue 3 + TypeScript + Vite + ant-design-vue。

**约束(硬):** 仅改 `OneOPS-UI`(分支 `snmp_metric`)相对 `main` 特有的文件——目标文件 `StrategySetDetailDrawer.vue`、`teleabs.ts` 及 6 个 `snmp*State.ts`(全为 snmp_metric 新增)均已核实在可改面内。命令在 `/home/jacky/project/OneOPS-ALL/OneOPS-UI` 下执行,提交落 `snmp_metric` 分支。

**不在本计划:** index.vue 的 Tab 调整(含"SNMP 指标分组"Tab)留更后;后端 API/服务/表(P3-2~P3-5)单独计划。

---

## 文件结构

- 改:`src/views/platform/StrategyTemplate/StrategySetDetailDrawer.vue` —— 移除生成/录制/树/模板/预检的 template 段、imports、computed/列定义/状态实例、相关函数。
- 删:`src/views/platform/StrategyTemplate/` 下 6 文件 —— `snmpStrategySetRecordingRuleState.ts`、`snmpStrategySetFormalClosureState.ts`、`snmpStrategySetGrafanaDashboardSave.ts`、`snmpStrategySetDashboardTreeState.ts`、`snmpStrategySetTargetPanelPreview.ts`、`snmpGrafanaDashboardTemplateManagement.ts`。
- 改:`src/api/platform/teleabs.ts` —— 删除 13 个生成/录制函数。
- 改:`package.json` + 删 `scripts/*` —— 移除引用被删功能的孤儿 smoke 脚本。

> 说明:工作以**语义锚点**(章节注释、函数名、import 名)定位,不要死认行号——删除会移动行号,务必自上而下或按锚点删。下方行号仅为参考。

---

### Task 1: 抽屉降只读 + 删除 6 个状态模块

**Files:**
- Modify: `src/views/platform/StrategyTemplate/StrategySetDetailDrawer.vue`
- Delete: 上述 6 个 `snmp*State.ts`

> 抽屉是这 6 模块的唯一消费者,故"删模块"与"精简抽屉"必须同一提交,避免中间态编译失败。

- [ ] **Step 1: 全仓确认 6 模块零外部消费者**

Run:
```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
grep -rln "snmpStrategySetRecordingRuleState\|snmpStrategySetFormalClosureState\|snmpStrategySetGrafanaDashboardSave\|snmpStrategySetDashboardTreeState\|snmpStrategySetTargetPanelPreview\|snmpGrafanaDashboardTemplateManagement" src/ scripts/
```
Expected: 仅 `StrategySetDetailDrawer.vue`(及待删的 smoke 脚本)。若出现其他 `src/views`/组件,**停止并报告**(范围超出预期)。

- [ ] **Step 2: 精简抽屉 template —— 删除生成/录制/树/模板/预检整段**

在 `StrategySetDetailDrawer.vue` 中删除 `<div v-if="isSelectorMode" class="target-panel-preview">` 起、到该块结束 `</div>` 为止的整段(参考行 55–657):包含"目标面板能力预检"标题、所有动作按钮(预览/生成YAML/发布规则/加载模板树/解析模板链/保存到平台/保存并同步/Open Grafana)、formal-closure 状态、录制规则结果、仪表盘保存结果、树试点节点表+批次历史、模板管理表单、目标面板预检结果。

**保留**:行 2–54 的只读元数据区 与 行 659–681 的策略项表(`default_params` 展开)。按锚点 `class="target-panel-preview"` 定位起点,确保删到与之匹配的闭合 `</div>`。

- [ ] **Step 3: 删除抽屉 script 中的相关 import**

删除从 6 个状态模块的 import(参考行 724–732):`createStrategySetTargetPanelPreviewState/panelCapabilityStateColor/panelCapabilityStateLabel`、`createStrategySetRecordingRuleState`、`createStrategySetGrafanaDashboardSaveState`、`createStrategySetDashboardTreeState`、`createSnmpGrafanaDashboardTemplateManagementState`、`createStrategySetFormalClosureState/isSuccessfulRecordingRulePublishStatus`。
删除从 `./teleabs`(或 `@/api/platform/teleabs`)import 的 13 个生成/录制函数(参考行 690–705),**保留** `previewTeleabsStrategySetPanelCapabilitySupportByTarget`、`grafanaDashboardBasicURLReq` 等只读项。

- [ ] **Step 4: 删除抽屉 script 中相关的 computed / 列定义 / 状态实例 / 函数**

删除(参考行号):
- 行 771–891:`dashboardTreePilotEnabled`、目标预检/录制就绪/发布状态相关 computed、列定义(`panelSupportColumns`/`dashboardTemplateColumns`/`dashboardTreeColumns`/`dashboardTreeBatchColumns`/`recordingRuleColumns`)、状态实例(`targetPanelPreviewInput`/`targetPanelPreview`/`recordingRuleState`/`grafanaDashboardSave`/`formalClosureState`/`dashboardTreeState`/`dashboardTemplateManagement`)。
- 行 949–1131:全部 28 个动作函数(`loadTargetPanelPreview`、`previewRecordingRules`、`materializeRecordingRules`、`publishRecordingRules`、`loadRecordingRuleReadiness`、`saveGrafanaDashboard`、`saveAndSyncGrafanaDashboard`、`runGrafanaDashboardFormalSaveGuard`、`previewGrafanaDashboardTree`、`saveGrafanaDashboardTree`、各 `*GrafanaDashboardTreeSaveBatch*`、`openGrafanaDashboard`、`*GrafanaDashboardTemplate*` 等)。
- 行 893–905:若 watch 仅做这些状态的 reset,则整删;若 watch 还保留其他逻辑,则只删被删状态的 `.reset()` 调用与 `targetPanelPreviewInput` 重置。

- [ ] **Step 5: 删除 6 个状态模块文件**

```bash
git rm src/views/platform/StrategyTemplate/snmpStrategySetRecordingRuleState.ts \
       src/views/platform/StrategyTemplate/snmpStrategySetFormalClosureState.ts \
       src/views/platform/StrategyTemplate/snmpStrategySetGrafanaDashboardSave.ts \
       src/views/platform/StrategyTemplate/snmpStrategySetDashboardTreeState.ts \
       src/views/platform/StrategyTemplate/snmpStrategySetTargetPanelPreview.ts \
       src/views/platform/StrategyTemplate/snmpGrafanaDashboardTemplateManagement.ts
```

- [ ] **Step 6: typecheck 通过(无悬空引用)**

Run: `npm run typecheck`
Expected: 通过。若报"未使用变量/未定义符号",回到 Step 3–4 清掉残留引用(常见:漏删某个 computed 仍引用已删状态,或 template 里残留对已删函数的 `@click`)。

- [ ] **Step 7: 提交**

```bash
git add -A src/views/platform/StrategyTemplate/
git commit -m "refactor(ui): 策略集详情抽屉降为只读，删除SNMP生成/录制/树状态模块"
```

---

### Task 2: 精简 teleabs.ts 生成/录制 API

**Files:**
- Modify: `src/api/platform/teleabs.ts`

> 前置:Task 1 已删除抽屉对这些函数的唯一引用。

- [ ] **Step 1: 再次确认 13 函数零引用**

Run:
```bash
grep -rln "materializeTeleabsStrategySetGrafanaDashboard\|materializeTeleabsStrategySetRecordingRules\|publishTeleabsStrategySetRecordingRules\|previewTeleabsStrategySetRecordingRules\|getTeleabsStrategySetTargetRecordingRuleReadiness\|saveTeleabsStrategySetGrafanaDashboard\|saveAndSyncTeleabsStrategySetGrafanaDashboard\|getTeleabsStrategySetGrafanaDashboardTreeSaveSummaryByBatch\|listTeleabsStrategySetGrafanaDashboardTreeSaveBatches\|listSnmpGrafanaDashboardTemplates\|resolveSnmpGrafanaDashboardTemplateByTarget\|upsertSnmpGrafanaDashboardTemplate" src/ scripts/
```
Expected: 仅待删 smoke 脚本(若有);`src/` 内无引用。若 `src/` 仍有引用,停止并报告。

- [ ] **Step 2: 删除 13 个导出函数**

在 `src/api/platform/teleabs.ts` 删除这些 `export const`(参考行 265–495):`previewTeleabsStrategySetRecordingRulesByTarget`、`materializeTeleabsStrategySetRecordingRulesByTarget`、`publishTeleabsStrategySetRecordingRulesByTarget`、`getTeleabsStrategySetTargetRecordingRuleReadiness`、`materializeTeleabsStrategySetGrafanaDashboardByTarget`、`materializeTeleabsStrategySetGrafanaDashboardTreeByTarget`、`saveTeleabsStrategySetGrafanaDashboardTreeByTarget`、`getTeleabsStrategySetGrafanaDashboardTreeSaveSummaryByBatch`、`listTeleabsStrategySetGrafanaDashboardTreeSaveBatches`、`saveTeleabsStrategySetGrafanaDashboardByTarget`、`saveAndSyncTeleabsStrategySetGrafanaDashboardByTarget`、`listSnmpGrafanaDashboardTemplates`、`resolveSnmpGrafanaDashboardTemplateByTarget`、`upsertSnmpGrafanaDashboardTemplate`。
删除随之仅被这些函数使用的、不再引用的局部类型/import(若有)。**保留** CRUD 与只读:`listTeleabsStrategySets`、`getTeleabsStrategySet`、`getTeleabsStrategySetMetricContract`、`previewTeleabsStrategySetPanelCapabilitySupportByTarget`、`create/update/deleteTeleabsStrategySet`。

- [ ] **Step 3: typecheck 通过**

Run: `npm run typecheck`
Expected: 通过。若报某被删函数仍被引用 → 回 Task 1 查残留;若报删后某 import/type 未使用 → 一并清理。

- [ ] **Step 4: 提交**

```bash
git add src/api/platform/teleabs.ts
git commit -m "refactor(api): 删除 teleabs 生成/录制相关API（前端已脱钩）"
```

---

### Task 3: 清理孤儿 smoke 脚本

**Files:**
- Modify: `package.json`
- Delete: `scripts/` 下对应 smoke 脚本

- [ ] **Step 1: 定位引用被删功能的 smoke 脚本**

Run:
```bash
grep -rln "RecordingRuleState\|FormalClosureState\|DashboardTreeState\|GrafanaDashboardSave\|GrafanaDashboardTemplateManagement\|TargetPanelPreview\|recording-rule\|dashboard-tree" scripts/ | sort -u
```
列出文件;再在 `package.json` 的 `scripts` 段找到引用这些文件的 `smoke:*` 条目(例如 `smoke:snmp-strategy-set-recording-rule-*`、`smoke:snmp-strategy-set-formal-closure-state`、`smoke:snmp-strategy-set-dashboard-tree-*`、`smoke:snmp-strategy-set-grafana-dashboard-save-action`、`smoke:snmp-grafana-dashboard-template-management`)。

- [ ] **Step 2: 删除这些 smoke 脚本文件及其 package.json 条目**

`git rm` 对应 `scripts/*.ts`;在 `package.json` 删除对应 `smoke:*` 行(注意 JSON 逗号合法性)。仅删确认引用被删功能的;其余 smoke 保留。

- [ ] **Step 3: 校验 package.json 合法 + typecheck**

Run: `node -e "require('./package.json')" && npm run typecheck`
Expected: 均通过。

- [ ] **Step 4: 提交**

```bash
git add -A package.json scripts/
git commit -m "chore: 移除已删SNMP生成/录制功能的孤儿smoke脚本"
```

---

### Task 4: 整体验证

**Files:** 无,仅验证。

- [ ] **Step 1: typecheck + build**

Run: `npm run typecheck && npm run build`
Expected: 均成功。

- [ ] **Step 2: 越界校验(仅改 snmp_metric 特有文件)**

Run:
```bash
git diff --name-only main...snmp_metric -- src/views/platform/StrategyTemplate/StrategySetDetailDrawer.vue src/api/platform/teleabs.ts && echo "目标文件均在可改面内"
```
Expected: 两文件列出。被删的 6 个 `snmp*State.ts` 为 snmp_metric 新增,删除合规。

- [ ] **Step 3: 人工冒烟(可选)**

启动前端,打开 策略集 Tab → 点某策略集详情抽屉:应只显示只读元数据 + 策略项表,无任何"预览/发布/保存/同步/模板"按钮,且无报错。

---

## 自检结论(Spec/草案 覆盖)

- 草案 P3-1「详情抽屉降只读 + 删 snmp*State.ts + 删 teleabs.ts 待删函数」→ Task 1+2 ✅
- 草案验证「typecheck/build 通过、策略集详情只读正常」→ Task 4 ✅
- 草案 P3-1「index.vue 收 Tab」→ **本计划明确延后**(测绘确认 Tab 与抽屉解耦,单独处理)✅
- 决策点①(前端可改面基线)→ 以 `snmp_metric vs main` 判定,目标文件已核实在内 ✅
- 孤儿 smoke 脚本清理(测绘新发现)→ Task 3 ✅
