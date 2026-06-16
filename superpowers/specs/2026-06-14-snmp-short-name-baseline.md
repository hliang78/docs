# SNMP Short Name Baseline

Date: 2026-06-14

## Goal

This note defines a short-name baseline for the SNMP dashboard-family work.

The goal is simple:

- names should be short;
- names should carry one meaning;
- names should be readable on first sight.

This note does not rename code by itself.
It provides the preferred vocabulary for future docs, reviews, and implementation work.

## Naming Rules

### Rule 1. Prefer Object Names Over Long Phrases

Prefer:

- `RootNode`
- `StrategyNode`
- `NodeOwner`
- `PanelSlot`

Do not prefer long compound phrases when a short object name is enough.

### Rule 2. One Name, One Layer

A name should not mix:

- definition layer
- runtime layer
- audit meaning

in one identifier if those are actually different things.

Example:

- `LeafMatch` is runtime evidence
- `NodeOwner` is logical ownership

These should stay separate.

### Rule 3. Runtime Audit Names Should Sound Like Audit

Audit-only objects should not sound like business ownership.

Good examples:

- `SaveBatch`
- `ContentDiff`
- `BindingDiff`

These sound like runtime/audit facts, not like logical model nodes.

### Rule 4. Booleans Should Read Like Booleans

Prefer:

- `isRuleReady`
- `isRuleStale`
- `hasTarget`

Avoid very long boolean names when a short predicate is enough.

### Rule 5. Keep Original Field Names At Boundaries

When talking about current API or DB fields, keep the real field name at the boundary,
but map it immediately to the short name.

Example:

```text
owner_strategy_id -> NodeOwner
matched_strategy_ids -> LeafMatch
save_batch_id -> SaveBatch
```

## Preferred Core Terms

These are the preferred short terms for current discussion.

### Definition Layer

- `StrategyTree`
- `DashboardTree`
- `TemplateTree`
- `RootNode`
- `StrategyNode`
- `NodeOwner`
- `PanelSlot`

### Runtime Layer

- `DashboardInstance`
- `RuleRun`
- `LeafMatch`

### Audit Layer

- `SaveBatch`
- `ContentDiff`
- `BindingDiff`

## Field Mapping Table

| Current field / phrase | Preferred short name | Meaning |
|---|---|---|
| `dashboard_role = root` | `RootNode` | root dashboard node |
| `dashboard_role = strategy` | `StrategyNode` | strategy-owned dashboard node |
| `owner_strategy_id` | `NodeOwner` | strategy owner of a node |
| `matched_strategy_ids` | `LeafMatch` | runtime matched leaf strategy evidence |
| `parent_dashboard_code` | `ParentCode` | runtime parent instance link |
| `root_dashboard_code` | `RootCode` | runtime root instance link |
| `save_batch_id` | `SaveBatch` | runtime audit batch |
| `dashboard_content_changed` | `ContentDiff` | runtime dashboard content diff |
| `panel_bindings_changed` | `BindingDiff` | runtime panel-binding diff |
| `currentViewedBatchId` | `ViewBatch` | currently replayed save batch |
| `currentSaveBatchId` | `LastBatch` | latest saved batch in memory |
| `recordingRuleReadiness` | `RuleReady` | readiness payload for current target |
| `recordingRuleReadinessVersionMismatchForCurrentTarget` | `isRuleStale` | current target rule version mismatch |

## Preferred Method Names

When future code is changed, prefer short verbs plus short objects.

Good direction:

- `loadTree`
- `saveTree`
- `loadBatch`
- `showCurrent`
- `loadReadiness`
- `saveRule`
- `resolveOwner`

Less preferred direction:

- names that repeat the whole business sentence;
- names that include current screen, source, target, and state all at once.

## Preferred Discussion Style

In docs and review comments, prefer:

```text
RootNode owns summary panels.
StrategyNode owns interface_basic.*.
LeafMatch is runtime evidence only.
SaveBatch is audit only.
```

Instead of:

```text
the currently matched_strategy_ids-derived runtime target-scoped owner inference
```

## Hard Boundaries

These short names must still preserve real distinctions.

### 1. `LeafMatch` Is Not `NodeOwner`

- `LeafMatch` = runtime evidence
- `NodeOwner` = logical owner

They must not collapse into one term.

### 2. `RootCode` Is Not `RootNode`

- `RootCode` = runtime instance link/code
- `RootNode` = logical node concept

They must not collapse into one term.

### 3. `SaveBatch` Is Not Part Of The Business Model

- `SaveBatch` = audit grouping
- not dashboard definition identity
- not node ownership

## Immediate Use

From now on, new notes in this line should prefer these short names first,
and only mention the longer current field names when needed for exact implementation references.
