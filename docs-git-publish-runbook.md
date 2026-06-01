# docs.git Publish Runbook

Use [scripts/sync-curated-docs-to-git.sh](/Users/huangliang/project/OneOPS-ALL/scripts/sync-curated-docs-to-git.sh) to copy a curated subset of this repo's `docs/` tree into a separate `docs.git` working copy.

The script intentionally excludes runtime-heavy material such as:

- `docs/openclaw-autodev/state/`
- `docs/openclaw-autodev/logs/`
- `docs/openclaw-autodev/memory/`
- `docs/openclaw-autodev/archive/`
- `docs/openclaw-autodev/evidence/`
- `.DS_Store`
- `*.sqlite*`
- `*.log`
- `__pycache__/`
- `oneops-backend`

Default mode is conservative: it merges curated files into the target repo and preserves target-only files. Use `--delete` only when you want a true mirror.

## Recommended Flow

```bash
scripts/sync-curated-docs-to-git.sh \
  --target-dir ~/work/docs-publish \
  --clone-if-missing \
  --branch import/oneops-docs-20260601
```

Then review the target repo:

```bash
git -C ~/work/docs-publish status --short
git -C ~/work/docs-publish diff --stat
```

When the diff looks right:

```bash
git -C ~/work/docs-publish add .
git -C ~/work/docs-publish commit -m "docs: sync curated OneOPS docs"
git -C ~/work/docs-publish push -u origin import/oneops-docs-20260601
```

## Dry Run

```bash
scripts/sync-curated-docs-to-git.sh \
  --target-dir ~/work/docs-publish \
  --dry-run
```

## Exclusion Rules

The active exclude list lives in [scripts/docs-publish.exclude](/Users/huangliang/project/OneOPS-ALL/scripts/docs-publish.exclude).
