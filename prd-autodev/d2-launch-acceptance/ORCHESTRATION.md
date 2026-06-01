# Device V2 上线验收 Story 编排

## 原则

自动化 pool 不应同时接收一串有强依赖的 `open` story。后续阶段先保持 `disabled`，等前置证据存在后再释放为 `open`。

## Batch 002 当前编排

```text
D2LA-002A open      d2-be  只读导出 sample-set.json
D2LA-002B disabled  d2-fe  生成 Excel
D2LA-002C disabled  d2-fe  upload/validate
D2LA-002D disabled  d2-fe  apply/handoff
D2LA-002E disabled  d2-be  reconciliation
```

## 释放下一步

释放 `D2LA-002B`：

```bash
cd /Users/huangliang/project/OneOPS-ALL
node - <<'NODE'
const fs = require('fs');
const p = 'docs/openclaw-autodev/stories/d2.json';
const j = JSON.parse(fs.readFileSync(p, 'utf8'));
const s = j.stories.find(x => x.id === 'D2LA-002B');
s.status = 'open';
s.updatedAt = new Date().toISOString();
j.updatedAt = s.updatedAt;
fs.writeFileSync(p, JSON.stringify(j, null, 2) + '\n');
NODE
```

释放 `D2LA-002C`：

```bash
cd /Users/huangliang/project/OneOPS-ALL
node - <<'NODE'
const fs = require('fs');
const p = 'docs/openclaw-autodev/stories/d2.json';
const j = JSON.parse(fs.readFileSync(p, 'utf8'));
const s = j.stories.find(x => x.id === 'D2LA-002C');
s.status = 'open';
s.updatedAt = new Date().toISOString();
j.updatedAt = s.updatedAt;
fs.writeFileSync(p, JSON.stringify(j, null, 2) + '\n');
NODE
```

释放 `D2LA-002D`：

```bash
cd /Users/huangliang/project/OneOPS-ALL
node - <<'NODE'
const fs = require('fs');
const p = 'docs/openclaw-autodev/stories/d2.json';
const j = JSON.parse(fs.readFileSync(p, 'utf8'));
const s = j.stories.find(x => x.id === 'D2LA-002D');
s.status = 'open';
s.updatedAt = new Date().toISOString();
j.updatedAt = s.updatedAt;
fs.writeFileSync(p, JSON.stringify(j, null, 2) + '\n');
NODE
```

释放 `D2LA-002E`：

```bash
cd /Users/huangliang/project/OneOPS-ALL
node - <<'NODE'
const fs = require('fs');
const p = 'docs/openclaw-autodev/stories/d2.json';
const j = JSON.parse(fs.readFileSync(p, 'utf8'));
const s = j.stories.find(x => x.id === 'D2LA-002E');
s.status = 'open';
s.updatedAt = new Date().toISOString();
j.updatedAt = s.updatedAt;
fs.writeFileSync(p, JSON.stringify(j, null, 2) + '\n');
NODE
```

## 启动对应 worker

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh start d2-be
```

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh start d2-fe
```

## 检查状态

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh stories d2-fe
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh stories d2-be
```
