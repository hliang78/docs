# USG Example Firewall Ticket E2E Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repeatable flow that converts `usg example` cases into real firewall ticket workbooks, uploads them through the existing firewall ticket APIs, and reconciles actual ticket results against the `usg example` expected outcomes.

**Architecture:** Keep parsing, workbook generation, and reconciliation logic in one focused script library under `OneOPS-UI/scripts/`, then add one generator CLI and one real-API acceptance CLI on top of that shared library. Use `test_policy.yaml` as the traffic-intent source, `test_policy_report.html` as the expected-result source, exact blueprint-tag label matching for node selection, and work-order item `remark` markers plus `matched_cli/generated_cli/item_status` for result reconciliation.

**Tech Stack:** TypeScript, Node.js, `js-yaml`, `xlsx`, existing `npx esbuild ... && node .tmp/...` script pattern, firewall ticket HTTP APIs.

---

## File Structure

- Create: `OneOPS-UI/scripts/usg-example-firewall-ticket-lib.ts`
  - Shared parsing, workbook generation, blueprint-tag resolution, actual-result classification, and Markdown/JSON report helpers.
- Create: `OneOPS-UI/scripts/usg-example-firewall-ticket-lib-smoke.ts`
  - Fast contract test for YAML parsing, HTML parsing, workbook row generation, and actual/oracle classification.
- Create: `OneOPS-UI/scripts/usg-example-firewall-ticket-generate.ts`
  - CLI that reads `test_policy.yaml` and `test_policy_report.html`, resolves blueprint tags, generates one workbook per node, and writes a manifest plus preview report.
- Create: `OneOPS-UI/scripts/usg-example-firewall-ticket-real-api-acceptance.ts`
  - CLI that uploads generated workbooks, creates firewall tickets, waits for stable results, fetches ticket details and route decisions, and writes the final reconciliation report.
- Modify: `OneOPS-UI/package.json`
  - Add one smoke script, one generation script, and one real-API acceptance script so the workflow is discoverable and repeatable.
- Create: `docs/superpowers/testing/usg-example-firewall-ticket-e2e/README.md`
  - Explain required env vars, output directories, and the exact command order for future reruns.

### Task 1: Build the shared parser and reconciliation library

**Files:**
- Create: `OneOPS-UI/scripts/usg-example-firewall-ticket-lib.ts`
- Create: `OneOPS-UI/scripts/usg-example-firewall-ticket-lib-smoke.ts`

- [ ] **Step 1: Write the failing smoke test for the source contracts**

Create `OneOPS-UI/scripts/usg-example-firewall-ticket-lib-smoke.ts` with these assertions:

```ts
import assert from 'node:assert/strict';
import {
  buildTraceRemark,
  classifyActualItem,
  classifyOracleCase,
  parseUsgExampleHtmlReport,
  parseUsgExampleYaml,
} from './usg-example-firewall-ticket-lib';

const yamlText = `
- Name: NODE-A
  TestGroups:
    - GroupName: group1
      Policy:
        - PolicyName: existing-rule
          PolicyCli: |
            rule 1 name existing-rule
      TestCase:
        - name: 精确匹配
          src: 10.0.0.1/32
          dst: 10.0.0.2/32
          service:
            protocol: tcp
            port: 443
`;

const htmlText = `
<table>
  <tr>
    <th>节点名称</th><th>测试组</th><th>场景</th><th>测试用例</th>
    <th>测试数据</th><th>策略CLI</th><th>匹配策略数</th><th>匹配的策略详情</th>
    <th>生成策略数</th><th>生成的策略详情</th>
  </tr>
  <tr>
    <td>NODE-A</td>
    <td>group1</td>
    <td><span>精确匹配</span></td>
    <td>#1</td>
    <td>源: 10.0.0.1/32<br>目: 10.0.0.2/32<br>服务: tcp:443</td>
    <td><div>rule 1 name existing-rule</div></td>
    <td>1</td>
    <td><div>策略名称: existing-rule</div></td>
    <td>0</td>
    <td><em>无生成策略</em></td>
  </tr>
</table>
`;

const yamlNodes = parseUsgExampleYaml(yamlText);
assert.equal(yamlNodes.length, 1);
assert.equal(yamlNodes[0].name, 'NODE-A');
assert.equal(yamlNodes[0].groups[0].cases[0].service.protocol, 'tcp');
assert.equal(yamlNodes[0].groups[0].cases[0].service.port, '443');

const reportRows = parseUsgExampleHtmlReport(htmlText);
assert.equal(reportRows.length, 1);
assert.equal(reportRows[0].nodeName, 'NODE-A');
assert.equal(reportRows[0].caseIndex, 1);
assert.equal(reportRows[0].matchedCount, 1);
assert.equal(reportRows[0].generatedCount, 0);

assert.equal(classifyOracleCase(reportRows[0]), 'matched_only');
assert.equal(
  buildTraceRemark({
    nodeName: 'NODE-A',
    groupName: 'group1',
    caseIndex: 1,
    scenarioName: '精确匹配',
  }),
  'USG_E2E|NODE-A|group1|#1|精确匹配',
);

assert.equal(
  classifyActualItem({
    item_status: 4,
    configs: [{ matched_cli: 'rule 1', generated_cli: '' }],
  }),
  'matched_only',
);
assert.equal(
  classifyActualItem({
    item_status: 3,
    configs: [{ matched_cli: '', generated_cli: 'security-policy ip' }],
  }),
  'generated_only',
);
assert.equal(
  classifyActualItem({
    item_status: 14,
    configs: [{ matched_cli: 'rule 1', generated_cli: 'service tcp 443' }],
  }),
  'mixed',
);

console.log('✅ usg example firewall ticket lib smoke passed');
```

- [ ] **Step 2: Run the smoke test to confirm the library does not exist yet**

Run:

```bash
cd OneOPS-UI
npx esbuild scripts/usg-example-firewall-ticket-lib-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/usg-example-firewall-ticket-lib-smoke.mjs >/dev/null && node .tmp/usg-example-firewall-ticket-lib-smoke.mjs
```

Expected: FAIL with `Could not resolve "./usg-example-firewall-ticket-lib"` or missing exported function errors.

- [ ] **Step 3: Implement the shared source and classification types**

Create `OneOPS-UI/scripts/usg-example-firewall-ticket-lib.ts` and start with these exact types and helpers:

```ts
import { load as loadYAML } from 'js-yaml';

export type OracleClass = 'matched_only' | 'generated_only' | 'mixed' | 'error';
export type ActualClass = OracleClass | 'unclassified_actual';

export interface UsgExampleCase {
  scenarioName: string;
  description: string;
  src: string;
  dst: string;
  service: {
    protocol: string;
    port: string;
  };
  caseIndex: number;
}

export interface UsgExampleGroup {
  groupName: string;
  cases: UsgExampleCase[];
}

export interface UsgExampleNode {
  name: string;
  groups: UsgExampleGroup[];
}

export interface UsgExampleReportRow {
  nodeName: string;
  groupName: string;
  scenarioName: string;
  caseIndex: number;
  matchedCount: number;
  generatedCount: number;
  matchedDetails: string;
  generatedDetails: string;
}

export interface TraceRemarkParts {
  nodeName: string;
  groupName: string;
  caseIndex: number;
  scenarioName: string;
}

export interface ActualConfigLike {
  matched_cli?: string;
  generated_cli?: string;
}

export interface ActualItemLike {
  item_status: number;
  configs: ActualConfigLike[];
}

export const ERROR_ITEM_STATUSES = new Set([2, 5, 6, 7, 8, 9, 10, 11, 12, 13]);

export const buildTraceRemark = (parts: TraceRemarkParts) =>
  `USG_E2E|${parts.nodeName}|${parts.groupName}|#${parts.caseIndex}|${parts.scenarioName}`;

export const classifyOracleCase = (row: UsgExampleReportRow): OracleClass => {
  if (row.matchedCount > 0 && row.generatedCount > 0) return 'mixed';
  if (row.matchedCount > 0) return 'matched_only';
  if (row.generatedCount > 0) return 'generated_only';
  return 'error';
};

export const classifyActualItem = (item: ActualItemLike): ActualClass => {
  if (ERROR_ITEM_STATUSES.has(item.item_status)) return 'error';
  const hasMatched = item.configs.some(config => Boolean(config.matched_cli && config.matched_cli.trim()));
  const hasGenerated = item.configs.some(config => Boolean(config.generated_cli && config.generated_cli.trim()));
  if (hasMatched && hasGenerated) return 'mixed';
  if (hasMatched) return 'matched_only';
  if (hasGenerated) return 'generated_only';
  return 'unclassified_actual';
};
```

- [ ] **Step 4: Implement YAML parsing exactly against `test_policy.yaml`**

Add this parser to `OneOPS-UI/scripts/usg-example-firewall-ticket-lib.ts`:

```ts
interface RawYamlCase {
  name?: string;
  description?: string;
  src?: string;
  dst?: string;
  service?: { protocol?: string; port?: string | number };
  meta_data?: { description?: string };
}

interface RawYamlGroup {
  GroupName?: string;
  TestCase?: RawYamlCase[];
}

interface RawYamlNode {
  Name?: string;
  TestGroups?: RawYamlGroup[];
}

export const parseUsgExampleYaml = (yamlText: string): UsgExampleNode[] => {
  const raw = (loadYAML(yamlText) as RawYamlNode[]) || [];
  return raw.map(node => ({
    name: String(node.Name || '').trim(),
    groups: (node.TestGroups || []).map(group => ({
      groupName: String(group.GroupName || '').trim(),
      cases: (group.TestCase || []).map((testCase, index) => ({
        scenarioName: String(testCase.name || '').trim(),
        description: String(testCase.description || testCase.meta_data?.description || '').trim(),
        src: String(testCase.src || '').trim(),
        dst: String(testCase.dst || '').trim(),
        service: {
          protocol: String(testCase.service?.protocol || '').trim(),
          port: String(testCase.service?.port || '').trim(),
        },
        caseIndex: index + 1,
      })),
    })),
  }));
};
```

- [ ] **Step 5: Implement HTML report parsing for the current static table shape**

Add these helpers to `OneOPS-UI/scripts/usg-example-firewall-ticket-lib.ts`:

```ts
const stripTags = (value: string) =>
  value
    .replace(/<br\\s*\\/?>/gi, '\n')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/\\s+/g, ' ')
    .trim();

const extractCells = (rowHtml: string) =>
  Array.from(rowHtml.matchAll(/<td>([\\s\\S]*?)<\\/td>/g)).map(match => stripTags(match[1]));

export const parseUsgExampleHtmlReport = (htmlText: string): UsgExampleReportRow[] => {
  const detailTableMatch = htmlText.match(
    /<h2>详细测试结果<\\/h2>[\\s\\S]*?<table>([\\s\\S]*?)<\\/table>/i,
  );
  if (!detailTableMatch) return [];

  return Array.from(detailTableMatch[1].matchAll(/<tr>([\\s\\S]*?)<\\/tr>/g))
    .slice(1)
    .map(match => extractCells(match[1]))
    .filter(cells => cells.length >= 10)
    .map(cells => ({
      nodeName: cells[0],
      groupName: cells[1],
      scenarioName: cells[2],
      caseIndex: Number(cells[3].replace('#', '')),
      matchedCount: Number(cells[6]),
      generatedCount: Number(cells[8]),
      matchedDetails: cells[7],
      generatedDetails: cells[9],
    }));
};
```

- [ ] **Step 6: Re-run the smoke test and require a clean pass**

Run:

```bash
cd OneOPS-UI
npx esbuild scripts/usg-example-firewall-ticket-lib-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/usg-example-firewall-ticket-lib-smoke.mjs >/dev/null && node .tmp/usg-example-firewall-ticket-lib-smoke.mjs
```

Expected: PASS with `✅ usg example firewall ticket lib smoke passed`.

- [ ] **Step 7: Commit the library contract**

Run:

```bash
git add OneOPS-UI/scripts/usg-example-firewall-ticket-lib.ts OneOPS-UI/scripts/usg-example-firewall-ticket-lib-smoke.ts
git commit -m "feat: add usg example firewall ticket parsing library"
```

### Task 2: Generate per-node firewall ticket workbooks and a preview manifest

**Files:**
- Create: `OneOPS-UI/scripts/usg-example-firewall-ticket-generate.ts`
- Modify: `OneOPS-UI/scripts/usg-example-firewall-ticket-lib.ts`
- Modify: `OneOPS-UI/package.json`

- [ ] **Step 1: Write the failing generator smoke case inside the existing smoke file**

Append this to `OneOPS-UI/scripts/usg-example-firewall-ticket-lib-smoke.ts`:

```ts
import { buildWorkbookRowsForNode } from './usg-example-firewall-ticket-lib';

const workbookRows = buildWorkbookRowsForNode({
  nodeName: 'NODE-A',
  cases: [
    {
      scenarioName: '精确匹配',
      description: '',
      src: '10.0.0.1/32',
      dst: '10.0.0.2/32',
      service: { protocol: 'tcp', port: '443' },
      caseIndex: 1,
    },
  ],
  groupName: 'group1',
});

assert.deepEqual(workbookRows, [
  ['情景2：出向策略工单 - NODE-A'],
  ['访问源(必填)', '访问目标地址(必填)', '访问目标端口', '协议(必填)', 'SNAT', '备注'],
  ['10.0.0.1/32', '10.0.0.2/32', '443', 'tcp', '', 'USG_E2E|NODE-A|group1|#1|精确匹配'],
]);
```

- [ ] **Step 2: Re-run the smoke test and confirm the missing workbook helper fails**

Run:

```bash
cd OneOPS-UI
npx esbuild scripts/usg-example-firewall-ticket-lib-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/usg-example-firewall-ticket-lib-smoke.mjs >/dev/null && node .tmp/usg-example-firewall-ticket-lib-smoke.mjs
```

Expected: FAIL with `No matching export for import "buildWorkbookRowsForNode"` or equivalent.

- [ ] **Step 3: Add the workbook-row builder and manifest helpers**

Extend `OneOPS-UI/scripts/usg-example-firewall-ticket-lib.ts` with:

```ts
export interface WorkbookRowCase extends UsgExampleCase {
  groupName: string;
  nodeName: string;
}

export const buildWorkbookRowsForNode = ({
  nodeName,
  groupName,
  cases,
}: {
  nodeName: string;
  groupName: string;
  cases: UsgExampleCase[];
}) => {
  return [
    [`情景2：出向策略工单 - ${nodeName}`],
    ['访问源(必填)', '访问目标地址(必填)', '访问目标端口', '协议(必填)', 'SNAT', '备注'],
    ...cases.map(testCase => [
      testCase.src,
      testCase.dst,
      testCase.service.port,
      testCase.service.protocol,
      '',
      buildTraceRemark({
        nodeName,
        groupName,
        caseIndex: testCase.caseIndex,
        scenarioName: testCase.scenarioName,
      }),
    ]),
  ];
};

export const slugifyNodeName = (nodeName: string) =>
  nodeName.replace(/[^A-Za-z0-9._-]+/g, '_');
```

- [ ] **Step 4: Create the generator CLI**

Create `OneOPS-UI/scripts/usg-example-firewall-ticket-generate.ts` with this exact structure:

```ts
import fs from 'node:fs';
import path from 'node:path';
import * as XLSX from 'xlsx';
import {
  buildWorkbookRowsForNode,
  classifyOracleCase,
  parseUsgExampleHtmlReport,
  parseUsgExampleYaml,
  slugifyNodeName,
} from './usg-example-firewall-ticket-lib';

const repoRoot = path.resolve(__dirname, '../..');
const yamlPath = process.env.USG_EXAMPLE_YAML_PATH || path.join(repoRoot, 'ctrlhub/controller/pkg/nodemap/example/usg_example/test_policy.yaml');
const reportPath =
  process.env.USG_EXAMPLE_REPORT_PATH || path.join(repoRoot, 'ctrlhub/controller/pkg/nodemap/example/usg_example/test_policy_report.html');
const blueprintPath = process.env.USG_EXAMPLE_BLUEPRINT_JSON_PATH || path.join(repoRoot, 'OneOPS-UI/.tmp/usg-example-blueprints.json');
const outDir =
  process.env.USG_EXAMPLE_OUT_DIR || path.join(repoRoot, 'docs/superpowers/testing/usg-example-firewall-ticket-e2e/generated');

const yamlNodes = parseUsgExampleYaml(fs.readFileSync(yamlPath, 'utf8'));
const reportRows = parseUsgExampleHtmlReport(fs.readFileSync(reportPath, 'utf8'));
const blueprints = JSON.parse(fs.readFileSync(blueprintPath, 'utf8')) as Array<{ label: string; value: string }>;
fs.mkdirSync(outDir, { recursive: true });

const manifest = yamlNodes.map(node => {
  const matches = blueprints.filter(item => item.label === node.name);
  const blueprintStatus =
    matches.length === 1 ? 'resolved' : matches.length === 0 ? 'missing_blueprint_tag' : 'ambiguous_blueprint_tag';
  const workbookPath = path.join(outDir, `${slugifyNodeName(node.name)}.xlsx`);
  const nodeCases = node.groups.flatMap(group =>
    group.cases.map(testCase => {
      const reportRow = reportRows.find(
        row =>
          row.nodeName === node.name &&
          row.groupName === group.groupName &&
          row.caseIndex === testCase.caseIndex &&
          row.scenarioName === testCase.scenarioName,
      );
      if (!reportRow) throw new Error(`missing oracle row for ${node.name} ${group.groupName} #${testCase.caseIndex}`);
      return {
        ...testCase,
        groupName: group.groupName,
        oracleClass: classifyOracleCase(reportRow),
      };
    }),
  );

  if (matches.length === 1) {
    const rows = buildWorkbookRowsForNode({
      nodeName: node.name,
      groupName: node.groups[0]?.groupName || 'group1',
      cases: nodeCases,
    });
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, XLSX.utils.aoa_to_sheet(rows), '工单');
    XLSX.writeFile(workbook, workbookPath);
  }

  return {
    node_name: node.name,
    blueprint_status: blueprintStatus,
    blueprint_tag_code: matches[0]?.value || '',
    workbook_path: matches.length === 1 ? workbookPath : '',
    row_count: nodeCases.length,
    cases: nodeCases.map(item => ({
      group_name: item.groupName,
      case_index: item.caseIndex,
      scenario_name: item.scenarioName,
      oracle_class: item.oracleClass,
    })),
  };
});

fs.writeFileSync(path.join(outDir, 'manifest.json'), JSON.stringify(manifest, null, 2));
console.log(JSON.stringify({ ok: true, out_dir: outDir, nodes: manifest.length }, null, 2));
```

- [ ] **Step 5: Add package scripts for smoke and generation**

Modify `OneOPS-UI/package.json` and add these exact entries under `scripts`:

```json
"smoke:usg-example-firewall-ticket-lib": "npx esbuild scripts/usg-example-firewall-ticket-lib-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/usg-example-firewall-ticket-lib-smoke.mjs >/dev/null && node .tmp/usg-example-firewall-ticket-lib-smoke.mjs",
"generate:usg-example-firewall-ticket-workorders": "npx esbuild scripts/usg-example-firewall-ticket-generate.ts --bundle --platform=node --format=esm --outfile=.tmp/usg-example-firewall-ticket-generate.mjs >/dev/null && node .tmp/usg-example-firewall-ticket-generate.mjs"
```

- [ ] **Step 6: Run the focused smoke check and a generation dry run**

Run:

```bash
cd OneOPS-UI
npm run smoke:usg-example-firewall-ticket-lib
```

Expected: PASS.

Run:

```bash
cd OneOPS-UI
printf '%s\n' '[{"label":"NODE-A","value":"BP-001"}]' > .tmp/usg-example-blueprints.json
cat <<'EOF' > /tmp/usg-example-test-policy.yaml
- Name: NODE-A
  TestGroups:
    - GroupName: group1
      TestCase:
        - name: 精确匹配
          src: 10.0.0.1/32
          dst: 10.0.0.2/32
          service:
            protocol: tcp
            port: 443
EOF
cat <<'EOF' > /tmp/usg-example-test-report.html
<h2>详细测试结果</h2>
<table>
  <tr>
    <th>节点名称</th><th>测试组</th><th>场景</th><th>测试用例</th>
    <th>测试数据</th><th>策略CLI</th><th>匹配策略数</th><th>匹配的策略详情</th>
    <th>生成策略数</th><th>生成的策略详情</th>
  </tr>
  <tr>
    <td>NODE-A</td>
    <td>group1</td>
    <td><span>精确匹配</span></td>
    <td>#1</td>
    <td>源: 10.0.0.1/32<br>目: 10.0.0.2/32<br>服务: tcp:443</td>
    <td><div>rule 1 name existing-rule</div></td>
    <td>1</td>
    <td><div>策略名称: existing-rule</div></td>
    <td>0</td>
    <td><em>无生成策略</em></td>
  </tr>
</table>
EOF
USG_EXAMPLE_BLUEPRINT_JSON_PATH=$PWD/.tmp/usg-example-blueprints.json npm run generate:usg-example-firewall-ticket-workorders
```

Expected: `manifest.json` plus one `.xlsx` per resolved node under the output directory.

- [ ] **Step 7: Commit the generator workflow**

Run:

```bash
git add OneOPS-UI/scripts/usg-example-firewall-ticket-lib.ts OneOPS-UI/scripts/usg-example-firewall-ticket-lib-smoke.ts OneOPS-UI/scripts/usg-example-firewall-ticket-generate.ts OneOPS-UI/package.json
git commit -m "feat: generate firewall ticket workorders from usg example"
```

### Task 3: Execute real uploads and reconcile actual ticket results

**Files:**
- Create: `OneOPS-UI/scripts/usg-example-firewall-ticket-real-api-acceptance.ts`
- Modify: `OneOPS-UI/scripts/usg-example-firewall-ticket-lib.ts`
- Modify: `OneOPS-UI/package.json`

- [ ] **Step 1: Add failing classification coverage for real item reconciliation**

Append this to `OneOPS-UI/scripts/usg-example-firewall-ticket-lib-smoke.ts`:

```ts
import { parseTraceRemark, reconcileCaseResult } from './usg-example-firewall-ticket-lib';

assert.deepEqual(parseTraceRemark('USG_E2E|NODE-A|group1|#1|精确匹配'), {
  nodeName: 'NODE-A',
  groupName: 'group1',
  caseIndex: 1,
  scenarioName: '精确匹配',
});

assert.deepEqual(
  reconcileCaseResult({
    source: {
      nodeName: 'NODE-A',
      groupName: 'group1',
      caseIndex: 1,
      scenarioName: '精确匹配',
      oracleClass: 'matched_only',
    },
    actualClass: 'matched_only',
    workOrderCode: 'WOF20260615001',
    itemCode: 'ITEM-001',
  }),
  {
    nodeName: 'NODE-A',
    groupName: 'group1',
    caseIndex: 1,
    scenarioName: '精确匹配',
    oracleClass: 'matched_only',
    actualClass: 'matched_only',
    consistent: true,
    workOrderCode: 'WOF20260615001',
    itemCode: 'ITEM-001',
  },
);
```

- [ ] **Step 2: Confirm the new helper exports are missing**

Run:

```bash
cd OneOPS-UI
npm run smoke:usg-example-firewall-ticket-lib
```

Expected: FAIL with missing `parseTraceRemark` or `reconcileCaseResult`.

- [ ] **Step 3: Add trace parsing and reconciliation helpers**

Extend `OneOPS-UI/scripts/usg-example-firewall-ticket-lib.ts` with:

```ts
export interface ParsedTraceRemark {
  nodeName: string;
  groupName: string;
  caseIndex: number;
  scenarioName: string;
}

export interface ReconcileSourceCase {
  nodeName: string;
  groupName: string;
  caseIndex: number;
  scenarioName: string;
  oracleClass: OracleClass;
}

export interface ReconciledCaseResult extends ReconcileSourceCase {
  actualClass: ActualClass | 'item_not_found';
  consistent: boolean;
  workOrderCode: string;
  itemCode: string;
}

export const parseTraceRemark = (remark: string): ParsedTraceRemark => {
  const match = remark.match(/^USG_E2E\\|(.+?)\\|(.+?)\\|#(\\d+)\\|(.+)$/);
  if (!match) throw new Error(`invalid trace remark: ${remark}`);
  return {
    nodeName: match[1],
    groupName: match[2],
    caseIndex: Number(match[3]),
    scenarioName: match[4],
  };
};

export const reconcileCaseResult = ({
  source,
  actualClass,
  workOrderCode,
  itemCode,
}: {
  source: ReconcileSourceCase;
  actualClass: ActualClass | 'item_not_found';
  workOrderCode: string;
  itemCode: string;
}): ReconciledCaseResult => ({
  ...source,
  actualClass,
  consistent: source.oracleClass === actualClass,
  workOrderCode,
  itemCode,
});
```

- [ ] **Step 4: Create the real-API acceptance CLI**

Create `OneOPS-UI/scripts/usg-example-firewall-ticket-real-api-acceptance.ts` with this exact execution shape:

```ts
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {
  classifyActualItem,
  parseTraceRemark,
  reconcileCaseResult,
} from './usg-example-firewall-ticket-lib';

const apiBase = process.env.ONEOPS_API_BASE_URL || 'http://127.0.0.1:3001/api/v1';
const token = process.env.ONEOPS_API_TOKEN || process.env.ONEOPS_UI_REAL_TOKEN || '';
const generatedDir =
  process.env.USG_EXAMPLE_OUT_DIR ||
  path.resolve(__dirname, '../../docs/superpowers/testing/usg-example-firewall-ticket-e2e/generated');

if (!token) {
  console.error('ONEOPS_API_TOKEN or ONEOPS_UI_REAL_TOKEN is required');
  process.exit(1);
}

const postMultipart = async (url: string, filePath: string) => {
  const form = new FormData();
  form.append('file', new Blob([fs.readFileSync(filePath)]), path.basename(filePath));
  const res = await fetch(url, { method: 'POST', headers: { 'X-Auth-Token': token }, body: form });
  return res.json();
};

const postJson = async (url: string, body: unknown) => {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Auth-Token': token },
    body: JSON.stringify(body),
  });
  return res.json();
};

const getJson = async (url: string) => {
  const res = await fetch(url, { headers: { 'X-Auth-Token': token } });
  return res.json();
};

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

const manifest = JSON.parse(fs.readFileSync(path.join(generatedDir, 'manifest.json'), 'utf8')) as Array<{
  node_name: string;
  blueprint_status: string;
  blueprint_tag_code: string;
  workbook_path: string;
  cases: Array<{ group_name: string; case_index: number; scenario_name: string; oracle_class: 'matched_only' | 'generated_only' | 'mixed' | 'error' }>;
}>;

const run = async () => {
  const results = [];
  for (const node of manifest.filter(item => item.blueprint_status === 'resolved')) {
    const upload = await postMultipart(`${apiBase}/ticket/firewallTicket/upload-file`, node.workbook_path);
    assert.ok(upload.code, `${node.node_name} missing upload file code`);

    const create = await postJson(`${apiBase}/ticket/firewallTicket`, {
      name: `USG E2E ${node.node_name} ${new Date().toISOString().slice(0, 19)}`,
      file_code: upload.code,
      file_object_name: upload.object_name || undefined,
      blueprint_tag_code: node.blueprint_tag_code,
      description: `USG example E2E validation for ${node.node_name}`,
    });
    assert.equal(create.code, 0, `${node.node_name} create failed: ${create.msg}`);

    const workOrderCode = create.data.code;
    let details = create.data;
    for (let i = 0; i < 30; i += 1) {
      await sleep(2000);
      details = await getJson(`${apiBase}/ticket/firewallTicket/details/${workOrderCode}`);
      if (Array.isArray(details.items) && details.items.length > 0) break;
    }

    const itemResults = [];
    for (const item of details.items || []) {
      const trace = parseTraceRemark(item.remark || '');
      const source = node.cases.find(
        testCase =>
          testCase.group_name === trace.groupName &&
          testCase.case_index === trace.caseIndex &&
          testCase.scenario_name === trace.scenarioName,
      );
      assert.ok(source, `missing manifest case for ${node.node_name} ${item.remark || item.code}`);
      const actualClass = classifyActualItem(item);
      itemResults.push(
        reconcileCaseResult({
          source: {
            nodeName: trace.nodeName,
            groupName: trace.groupName,
            caseIndex: trace.caseIndex,
            scenarioName: trace.scenarioName,
            oracleClass: source.oracle_class,
          },
          actualClass,
          workOrderCode,
          itemCode: item.code,
        }),
      );
    }

    results.push({
      node_name: node.node_name,
      work_order_code: workOrderCode,
      item_results: itemResults,
    });
  }

  fs.writeFileSync(path.join(generatedDir, 'reconciliation.json'), JSON.stringify(results, null, 2));
  console.log(JSON.stringify({ ok: true, nodes: results.length, output: path.join(generatedDir, 'reconciliation.json') }, null, 2));
};

run().catch(error => {
  console.error(error);
  process.exit(1);
});
```

- [ ] **Step 5: Add the real-API acceptance script to `package.json`**

Modify `OneOPS-UI/package.json` and add:

```json
"acceptance:usg-example-firewall-ticket-real-api": "npx esbuild scripts/usg-example-firewall-ticket-real-api-acceptance.ts --bundle --platform=node --format=esm --outfile=.tmp/usg-example-firewall-ticket-real-api-acceptance.mjs >/dev/null && node .tmp/usg-example-firewall-ticket-real-api-acceptance.mjs"
```

- [ ] **Step 6: Run the local smoke test again**

Run:

```bash
cd OneOPS-UI
npm run smoke:usg-example-firewall-ticket-lib
```

Expected: PASS, including trace parsing and reconciliation.

- [ ] **Step 7: Run a one-node real-API acceptance trial**

Prepare env and run:

```bash
cd OneOPS-UI
ONEOPS_API_TOKEN='<real-token>' \
USG_EXAMPLE_OUT_DIR=/home/jacky/project/OneOPS-ALL/docs/superpowers/testing/usg-example-firewall-ticket-e2e/generated \
npm run acceptance:usg-example-firewall-ticket-real-api
```

Expected:
- a work order is created for each resolved node workbook
- `reconciliation.json` is written
- every reconciled item includes `oracleClass`, `actualClass`, `consistent`, `workOrderCode`, and `itemCode`

- [ ] **Step 8: Commit the real-API acceptance workflow**

Run:

```bash
git add OneOPS-UI/scripts/usg-example-firewall-ticket-lib.ts OneOPS-UI/scripts/usg-example-firewall-ticket-real-api-acceptance.ts OneOPS-UI/package.json
git commit -m "feat: add firewall ticket usg example real-api validation"
```

### Task 4: Write operator-facing usage docs and final verification rules

**Files:**
- Create: `docs/superpowers/testing/usg-example-firewall-ticket-e2e/README.md`
- Modify: `OneOPS-UI/scripts/usg-example-firewall-ticket-real-api-acceptance.ts`

- [ ] **Step 1: Extend the acceptance script to emit a Markdown summary**

Add this formatter to `OneOPS-UI/scripts/usg-example-firewall-ticket-real-api-acceptance.ts` after `results` are assembled:

```ts
const markdownLines = [
  '# USG Example Firewall Ticket E2E Validation Report',
  '',
  `- Generated at: ${new Date().toISOString()}`,
  `- Nodes executed: ${results.length}`,
  '',
  '| 节点 | 工单号 | case | 场景 | 预期 | 实际 | 一致 |',
  '| --- | --- | --- | --- | --- | --- | --- |',
];

for (const node of results) {
  for (const item of node.item_results) {
    markdownLines.push(
      `| ${item.nodeName} | ${node.work_order_code} | #${item.caseIndex} | ${item.scenarioName} | ${item.oracleClass} | ${item.actualClass} | ${item.consistent ? 'yes' : 'no'} |`,
    );
  }
}

fs.writeFileSync(path.join(generatedDir, 'reconciliation.md'), `${markdownLines.join('\n')}\n`);
```

- [ ] **Step 2: Write the rerun guide**

Create `docs/superpowers/testing/usg-example-firewall-ticket-e2e/README.md` with this exact content:

```md
# USG Example Firewall Ticket E2E Validation

## Required Inputs

- `ctrlhub/controller/pkg/nodemap/example/usg_example/test_policy.yaml`
- `ctrlhub/controller/pkg/nodemap/example/usg_example/test_policy_report.html`
- Blueprint tag option dump saved to `OneOPS-UI/.tmp/usg-example-blueprints.json`
- `ONEOPS_API_TOKEN` or `ONEOPS_UI_REAL_TOKEN`

## Command Order

1. Generate a blueprint-tag dump from the live environment and save it as `OneOPS-UI/.tmp/usg-example-blueprints.json`.
2. Run `cd OneOPS-UI && npm run smoke:usg-example-firewall-ticket-lib`.
3. Run `cd OneOPS-UI && npm run generate:usg-example-firewall-ticket-workorders`.
4. Run `cd OneOPS-UI && ONEOPS_API_TOKEN='<token>' npm run acceptance:usg-example-firewall-ticket-real-api`.

## Outputs

- `docs/superpowers/testing/usg-example-firewall-ticket-e2e/generated/manifest.json`
- `docs/superpowers/testing/usg-example-firewall-ticket-e2e/generated/reconciliation.json`
- `docs/superpowers/testing/usg-example-firewall-ticket-e2e/generated/reconciliation.md`
- one `.xlsx` workbook per resolved node
```

- [ ] **Step 3: Run the focused verification commands**

Run:

```bash
cd OneOPS-UI
npm run smoke:usg-example-firewall-ticket-lib
```

Expected: PASS.

Run:

```bash
cd OneOPS-UI
npm run typecheck
```

Expected: PASS for the newly added scripts and package metadata. If unrelated pre-existing type errors remain, record them explicitly in the final execution notes instead of suppressing them.

- [ ] **Step 4: Commit the operator docs**

Run:

```bash
git add docs/superpowers/testing/usg-example-firewall-ticket-e2e/README.md OneOPS-UI/scripts/usg-example-firewall-ticket-real-api-acceptance.ts
git commit -m "docs: add firewall ticket usg example validation runbook"
```
