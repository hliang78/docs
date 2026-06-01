# Device V2 上线验收 OpenClaw 极简手册

## 发布 Batch

```bash
cd /Users/huangliang/project/OneOPS-ALL
```

```bash
python3 /Users/huangliang/.codex/skills/prd-autodev-loop/scripts/publish_story_batch.py \
  --package /Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/d2-launch-acceptance/story-packages/batch-001.json \
  --task-id d2-fe
```

```bash
python3 /Users/huangliang/.codex/skills/prd-autodev-loop/scripts/publish_story_batch.py \
  --package /Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/d2-launch-acceptance/story-packages/batch-001-backend-contract-addendum.json \
  --task-id d2-be
```

如果 d2-be 因 story 过大或等待 AI 返回超时而 BLOCKED，改用后端小切片包：

```bash
python3 /Users/huangliang/.codex/skills/prd-autodev-loop/scripts/publish_story_batch.py \
  --package /Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/d2-launch-acceptance/story-packages/backend-small-slices.json \
  --task-id d2-be
```

```bash
python3 /Users/huangliang/.codex/skills/prd-autodev-loop/scripts/publish_story_batch.py \
  --package /Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/d2-launch-acceptance/story-packages/batch-002-import.json \
  --task-id d2-fe
```

```bash
python3 /Users/huangliang/.codex/skills/prd-autodev-loop/scripts/publish_story_batch.py \
  --package /Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/d2-launch-acceptance/story-packages/batch-003-store-phases.json \
  --task-id d2-fe
```

```bash
python3 /Users/huangliang/.codex/skills/prd-autodev-loop/scripts/publish_story_batch.py \
  --package /Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/d2-launch-acceptance/story-packages/batch-004-lifecycle-cleanup.json \
  --task-id d2-fe
```

```bash
python3 /Users/huangliang/.codex/skills/prd-autodev-loop/scripts/publish_story_batch.py \
  --package /Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/d2-launch-acceptance/story-packages/batch-005-readiness-report.json \
  --task-id d2-fe
```

## 查看 Story

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh stories d2-fe
```

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh stories d2-be
```

## Batch 002 顺序

Batch 002 必须按顺序推进：

```text
D2LA-002A -> D2LA-002B -> D2LA-002C -> D2LA-002D -> D2LA-002E
```

如果 `D2LA-002E` 提前执行并提示 `0 D2LA_% cloned records`，不要排查 store。先完成 `D2LA-002C/D2LA-002D` 的 upload/apply/handoff。

`D2LA-002B` 需要先有：

```text
docs/openclaw-autodev/evidence/d2-fe/D2LA-IMPORT/sample-set.json
```

该文件应由 `D2LA-002A` 产出。

更详细的阶段释放命令见：

```bash
open /Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/d2-launch-acceptance/ORCHESTRATION.md
```

## 查看状态

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh status d2-fe
```

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh status d2-be
```

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-state-manager.mjs status d2-fe
```

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-state-manager.mjs status d2-be
```

## 启动/继续

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh start d2-fe
```

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh start d2-be
```

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh pool start
```

## 停止

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh stop d2-fe
```

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh stop d2-be
```

## 清理卡住状态

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-state-manager.mjs cleanup all
```

## 关键文档

```bash
open /Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/d2-launch-acceptance/decisions.md
```

```bash
open /Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/d2-launch-acceptance/program-plan.md
```

```bash
open /Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/d2-launch-acceptance/story-packages
```
