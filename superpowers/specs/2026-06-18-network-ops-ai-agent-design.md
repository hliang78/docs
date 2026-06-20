# OneOPS Network Operations AI Agent Design

## Purpose

This design adds a first AI-assisted network operations capability to OneOPS.

The MVP is an "AI analysis" action inside the alert detail page. It uses the current alert, related device facts, real logs, RCA output, optional read-only `show` command evidence, and local private knowledge to produce a structured diagnosis report.

The feature is intentionally evidence-first. The LLM explains and organizes findings, but it does not become the root-cause engine. OneOPS remains the source of truth for devices, topology, alerts, logs, permissions, RCA contracts, and audit.

## Confirmed Decisions

- MVP entry point: alert detail page, via an AI analysis action.
- Deployment model: local deployment.
- LLM runtime: local Ollama.
- PoC preference: low deployment difficulty.
- Device command boundary: only read-only `show` commands are allowed.
- Initial evidence set: real logs provided by the user.

## Scope

### In Scope

- Alert-detail AI analysis entry.
- Local Ollama-backed diagnosis generation.
- Lightweight local RAG over real logs and private knowledge documents.
- OneOPS RCA integration, using existing `rca3`/`rca2` contracts where possible.
- Log evidence ingestion from real log samples and later from OneOPS log sources.
- Read-only device `show` command suggestions and controlled execution path.
- Structured diagnosis report with evidence citations.
- Permission, audit, and safety boundaries for diagnosis requests and tool calls.

### Out of Scope

- Autonomous remediation.
- Non-`show` configuration commands.
- Replacing OneOPS device master data, topology snapshots, or RCA engine with an external platform.
- Making Dify, RAGFlow, Open WebUI, or AnythingLLM a required production dependency.
- A full general-purpose chatbot as the first screen.
- Full document-management productization beyond what is needed for MVP evidence retrieval.

## Design Principle

The feature should behave like a senior operations assistant reading OneOPS evidence, not like an unconstrained chatbot.

Every important statement in the report must be classified as one of:

- Fact: directly observed in OneOPS data, logs, RCA output, or `show` output.
- Inference: reasoned from cited facts.
- Recommendation: suggested next step.
- Gap: missing evidence or unresolved uncertainty.

This classification is the main defense against LLM hallucination.

## Recommended PoC Stack

### Primary MVP Stack

- OneOPS backend module or small `aiops-service`.
- Ollama for local LLM inference.
- Local embedding model through Ollama or another local embedding runtime.
- Lightweight local vector store or hybrid index.
- Existing OneOPS data sources and RCA packages.

This path has the lowest product lock-in and keeps deployment simple.

### Optional Local Knowledge UI

Open WebUI or AnythingLLM may be used as a local PoC aid for manual log/document experimentation, but not as a hard product dependency.

These are lighter than Dify/RAGFlow for local Ollama experiments. Dify and RAGFlow remain useful references, but their service stacks are heavier and should not define the MVP architecture.

## Existing OneOPS Fit

### RCA

OneOPS already has useful RCA boundaries:

- `OneOPS/pkg/rca2/contract.go` defines `Observation`, `Path`, `NodeFact`, `Profile`, and explainable `Candidate` output.
- `OneOPS/pkg/rca3/types.go` defines `AnalyzeRequest`, layered topology, alert bindings, evidence, incident context, candidates, and final decision.
- `OneOPS/pkg/rca3/interfaces.go` separates topology loading, path resolving, alert binding, evidence normalization, layer decision, cross-layer reduction, and presentation.

The AI agent should call or wrap these capabilities. It should not independently decide root cause from raw text.

### Data Foundation

The feature depends on the existing OneOPS direction of:

- Unified object identity.
- Unified time/version semantics.
- Unified evidence quality.
- Unified consumption layer.

The MVP can operate with partial versions of these foundations, but the report must show when a missing foundation weakens the conclusion.

### Logs

Real logs are the first available evidence source. MVP log handling should start from uploaded or locally staged log samples, then later connect to OneOPS log sources such as Loki or Mongo-backed device logs if available.

Logs should be normalized into an evidence model:

```json
{
  "kind": "log",
  "source": "uploaded_log",
  "observed_at": "2026-06-18T10:00:00+08:00",
  "device_ref": "device-code-or-hostname",
  "summary": "Interface Gi1/0/24 changed state to down",
  "raw_ref": "log-file:line-range",
  "confidence": 70,
  "attributes": {
    "interface": "Gi1/0/24",
    "severity": "warning",
    "vendor": "unknown"
  }
}
```

## Architecture

```text
Alert Detail Page
  -> AI Analysis API
    -> Context Builder
      -> Alert / Device / Topology / Time Window
      -> Real Log Evidence
      -> Optional Knowledge Retrieval
      -> Optional RCA Request
      -> Optional Show Command Plan
    -> Evidence Normalizer
    -> RCA Adapter
    -> Local RAG Retriever
    -> Ollama Report Generator
    -> Diagnosis Report Presenter
```

### Components

#### Alert Detail UI

Adds a single AI analysis action and a read-only report panel.

The panel should show:

- Analysis status.
- Alert and time window used.
- Evidence list.
- Root-cause candidates.
- Troubleshooting steps.
- Recommended next actions.
- Missing evidence.
- Citations to logs, RCA output, knowledge snippets, and `show` output.

#### AI Analysis API

Receives the alert id and optional user question.

It should not accept arbitrary device commands. It may return a proposed `show` command plan for approval or controlled execution.

Request shape:

```json
{
  "alert_id": "alert-123",
  "question": "为什么这个端口频繁 down/up?",
  "time_window": {
    "from": "2026-06-18T09:00:00+08:00",
    "to": "2026-06-18T11:00:00+08:00"
  },
  "options": {
    "include_logs": true,
    "include_rca": true,
    "include_knowledge": true,
    "allow_show_plan": true
  }
}
```

#### Context Builder

Builds a stable incident context:

- Alert attributes and labels.
- Device and interface references.
- Time window.
- Topology snapshot reference when available.
- Related logs.
- Related knowledge snippets.
- Related RCA result.

The context builder must also record missing data.

#### Local RAG Retriever

Retrieves from:

- Uploaded real logs.
- Internal runbooks.
- Vendor manual snippets.
- Historical incident notes.

For MVP, retrieval may be simple:

- Parse and chunk logs/documents.
- Store metadata: source, line range, device, timestamp, vendor, type.
- Use keyword + vector retrieval.
- Return top-k snippets with source references.

Hybrid retrieval is preferred because network operations rely heavily on exact tokens such as interface names, error codes, ACL names, and vendor log mnemonics.

#### RCA Adapter

Maps alert, topology, paths, and evidence into existing OneOPS RCA contracts.

The adapter should keep a clear line:

- RCA candidates are produced by OneOPS logic.
- LLM summarizes why candidates matter.

#### Show Command Planner

The planner may suggest only read-only `show` commands. It must not invent executable free-form commands.

Each command should be selected from a whitelist:

```json
{
  "vendor": "cisco_like",
  "commands": [
    "show interface {interface}",
    "show logging | include {interface}",
    "show ip route {prefix}",
    "show ip ospf neighbor",
    "show version"
  ]
}
```

The MVP may stop at command suggestions. If execution is enabled, it must go through OneOPS controlled device adapters, audit, and permission checks.

#### Ollama Report Generator

The LLM receives a compact evidence packet, not raw unbounded logs.

The prompt must require:

- No root-cause claim without cited evidence.
- Mark uncertainty.
- Separate facts, inferences, recommendations, and gaps.
- Use operator-safe language.
- Never produce configuration commands in MVP.

## Diagnosis Report Contract

```json
{
  "report_id": "aiops-report-123",
  "alert_id": "alert-123",
  "status": "completed",
  "summary": "端口 Gi1/0/24 在 10:02 到 10:15 间多次 down/up。",
  "facts": [
    {
      "text": "日志显示 Gi1/0/24 多次 link down/up。",
      "citations": ["uploaded_log:network.log:120-138"]
    }
  ],
  "root_cause_candidates": [
    {
      "candidate": "物理链路或光模块异常",
      "source": "rca_and_logs",
      "confidence": "medium",
      "evidence": ["log-1", "rca-candidate-1"],
      "why": "flap pattern matches physical/link instability."
    }
  ],
  "troubleshooting_steps": [
    {
      "risk": "read_only",
      "action": "检查接口计数器和物理状态",
      "suggested_show": "show interface Gi1/0/24",
      "requires_approval": true
    }
  ],
  "recommendations": [
    {
      "risk": "manual_review",
      "text": "若 CRC/input error 持续增长，建议现场检查光模块、尾纤或对端端口。"
    }
  ],
  "missing_evidence": [
    "缺少 show interface 输出",
    "缺少同时间窗对端设备日志"
  ],
  "citations": [
    {
      "id": "log-1",
      "type": "log",
      "source": "uploaded_log",
      "ref": "network.log:120-138"
    }
  ]
}
```

## MVP User Flow

1. User opens alert detail.
2. User clicks AI analysis.
3. OneOPS builds alert context.
4. OneOPS retrieves relevant real logs.
5. OneOPS optionally calls RCA.
6. OneOPS retrieves matching local knowledge snippets.
7. AI generator produces a structured report.
8. User reviews evidence, candidates, steps, and missing evidence.
9. If needed, user approves or manually runs suggested `show` checks.

## Real Log First Workflow

Because the first available evidence is real logs, the first implementation plan should start with log sample handling:

1. Define a local evidence directory for sample logs.
2. Add a parser that preserves file name and line numbers.
3. Extract timestamps, hostname/device, severity, interface, and message when possible.
4. Keep raw lines even when parsing is incomplete.
5. Build retrieval over parsed logs.
6. Use one real log incident as the first golden test.

This lets the MVP produce useful diagnosis before full Loki or document ingestion is ready.

## Safety And Permissions

### Permissions

AI analysis must check:

- User can view the alert.
- User can view the related device.
- User can view related logs.
- User can access retrieved private knowledge.
- User can request or execute read-only show commands if that path is enabled.

### Audit

Record:

- User id.
- Alert id.
- Time window.
- Data sources used.
- Knowledge snippets returned.
- RCA request id.
- Prompt/report version.
- Suggested show commands.
- Executed show commands, if execution is later enabled.

### Command Boundary

Allowed:

- `show ...`
- Equivalent vendor read-only display commands if explicitly whitelisted later.

Denied:

- `configure`, `conf t`, `set`, `delete`, `clear`, `reload`, `reset`, `write`, `copy`, `commit`, `save`, or any command with side effects.

The command boundary must be enforced before any device adapter call, not by prompt wording alone.

## Error States

- `alert_not_found`
- `permission_denied`
- `logs_unavailable`
- `rca_unavailable`
- `knowledge_unavailable`
- `ollama_unavailable`
- `insufficient_evidence`
- `show_not_allowed`
- `report_generation_failed`

Error responses should still be useful. For example, if Ollama is unavailable, the API can return collected evidence and explain that report generation failed.

## Testing Strategy

### Golden Scenarios

Use real logs to build at least one golden case first. Recommended scenario categories:

- Interface flap.
- Optics or physical layer degradation.
- Firewall or ACL deny spike.
- Routing neighbor flap if present in logs.

### Unit Tests

- Log parser preserves source line references.
- Evidence normalizer emits stable evidence objects.
- Show command whitelist rejects side-effect commands.
- Report schema validation catches missing facts/citations.

### Integration Tests

- Alert id -> context -> log retrieval -> RCA adapter -> Ollama report.
- Missing logs still returns a report with explicit gaps.
- Ollama unavailable returns a controlled error.
- Cross-permission knowledge is not retrieved.

### Manual Review

For each golden report, review:

- Are root-cause candidates evidence-backed?
- Are uncertainties visible?
- Are steps operationally safe?
- Are citations useful enough for an engineer to verify?

## Implementation Slices

### Slice 1: Evidence Packet And Report Schema

- Define diagnosis request and report DTO.
- Define normalized log evidence.
- Add fixture based on one real log sample.
- Add schema validation.

### Slice 2: Local Ollama Report Generation

- Add local Ollama client wrapper.
- Generate report from fixture evidence.
- Enforce fact/inference/recommendation/gap format.

### Slice 3: Alert Detail Entry

- Add AI analysis action to alert detail.
- Render diagnosis report.
- Render loading, error, insufficient evidence, and citation states.

### Slice 4: RCA And Knowledge Retrieval

- Add `rca3` adapter facade.
- Add lightweight local RAG over real logs and documents.
- Merge RCA candidates and retrieval snippets into evidence packet.

### Slice 5: Show Command Plan

- Define show command whitelist.
- Generate suggested show checks from report gaps.
- Keep execution disabled or approval-gated until explicitly enabled.

## Open Questions

- Where should real log samples live for MVP fixtures?
- Which alert/detail page implementation is the current canonical UI surface?
- Which Ollama model should be the default for Chinese network operations reports?
- Should embeddings also use Ollama, or should the first MVP use keyword retrieval plus later embeddings?
- Should show command execution be included in MVP, or only suggested as manual next steps?

## Acceptance Criteria

- From an alert detail context, a user can request AI analysis.
- The system produces a structured report using local Ollama.
- The report cites real log evidence by source and line reference.
- The report includes root-cause candidates only when backed by OneOPS RCA output or explicit evidence.
- The report distinguishes facts, inferences, recommendations, and gaps.
- The system never emits or executes non-show commands.
- Ollama unavailable, missing logs, and insufficient evidence states are handled cleanly.
- The first real-log golden scenario can be rerun as a regression check.

## References

- `OneOPS/pkg/rca2/contract.go`
- `OneOPS/pkg/rca3/types.go`
- `OneOPS/pkg/rca3/interfaces.go`
- `docs/RCA_PLATFORM_AGNOSTIC_MINIMAL_CONTRACT.md`
- `docs/ONEOPS_DATA_APPLICATION_FOUNDATION_CAPABILITY_MAP_2026-04-10.md`
- `docs/prd-autodev/network-ops-ai-agent/research.md`

## Implementation Status

- MVP implementation slice completed: alert-detail AI analysis request/report contract, uploaded log evidence parser, show command guard, local Ollama report generator, backend diagnosis endpoint, and frontend read-only drawer.
- Show command execution remains disabled; the MVP only suggests approved read-only `show` commands.
- Post-review hardening completed: diagnosis citations are bound back to server-generated normalized evidence, suggested `show` commands use an approved read-only whitelist, free-text troubleshooting guidance is checked for unsafe operational actions, and the diagnosis generator selects an enabled `type=ollama` provider by default.
- RCA connection inside the alert diagnosis endpoint remains conservative and uses a placeholder conclusion until the next slice connects full `rca3` context assembly.
- Regression status on 2026-06-18: backend `go test ./app/aiops/...` passed; LLM prompt registry focused tests passed; `go test ./cmd -run '^$'` passed; frontend alert diagnosis smoke passed; scoped `vue-tsc --noEmit -p tsconfig.vitest.json --composite false` passed. Full `npm run typecheck` is currently blocked by pre-existing `scripts/usg-example-firewall-*` type errors outside this MVP slice.
