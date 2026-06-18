# OneOPS SOP And Knowledge Base MVP Design

## Purpose

This design adds an independent "knowledge and SOP center" to OneOPS.

The capability lets operators register private operations documents, parse them into searchable knowledge chunks, create standardized SOP/runbooks with cited evidence, and search for troubleshooting guidance by symptom, device type, vendor keyword, log phrase, or error code.

The MVP is independent from alert AI diagnosis. It can be used directly from a dedicated operations page. Alert AI can later call the same retrieval contract to enrich RCA reports with cited SOP and document evidence.

## Confirmed Decisions

- This track is advanced independently from the alert detail "AI analysis" entry.
- Deployment must stay simple for local environments.
- Local Ollama is available and may be used for optional summarization or extraction.
- Heavy third-party RAG platforms are allowed only as references or optional PoC helpers, not required production dependencies.
- AI output and SOP guidance must stay read-only in the first version. It may recommend `show` style checks or link to manually executed task templates, but it must not execute remediation automatically.
- The design must reuse OneOPS where practical: file storage, task templates, existing AIOps API style, tenant scoping, and current frontend conventions.

## Scope

### In Scope

- A lightweight SOP/runbook registry.
- A private knowledge document registry.
- Text document parsing and deterministic chunking.
- Citation-first search over documents and runbooks.
- A dedicated frontend page for knowledge documents, runbooks, and search.
- Runbook steps that can link to existing OneOPS task templates without executing them.
- A backend retrieval contract that alert AI can consume later.
- Tenant scoped storage and retrieval.
- Smoke tests for the longest MVP path.

### Out Of Scope

- Autonomous remediation.
- Direct execution of configuration commands.
- A general-purpose chatbot as the first screen.
- Making Dify, RAGFlow, Open WebUI, AnythingLLM, pgvector, or Elasticsearch a required dependency.
- Full document collaboration, rich document editing, or version diff UI.
- Full PDF/DOCX layout extraction in the first implementation. These can be added after the text and Markdown path is stable.

## User Journeys

### Journey 1: Register A Knowledge Document

An operations engineer opens "知识与SOP", creates or selects a knowledge space, uploads or registers a text or Markdown document, and starts parsing.

OneOPS stores the raw file reference, creates a document record, chunks the text, extracts lightweight metadata, and shows parse status. Each chunk has a stable citation reference such as document title, section heading, chunk index, and line range when available.

Success means the engineer can search for a phrase from the document and see cited results.

### Journey 2: Create A Standard Runbook

An operations engineer creates a runbook for a common scenario such as interface flapping, BGP neighbor down, disk usage high, certificate expiry, or firewall policy hit mismatch.

The engineer fills scenario, applicable device types, risk level, required evidence, and ordered steps. Each step is one of:

- `observe`: inspect OneOPS facts or logs.
- `show_suggestion`: suggest a read-only command or query.
- `manual_check`: describe a manual verification step.
- `task_template_reference`: link an existing OneOPS task template for manual launch.

The engineer links citations from knowledge chunks to the runbook and publishes it after review.

### Journey 3: Search By Symptom Or Log Phrase

An operator enters a symptom, error code, log phrase, command output phrase, vendor name, protocol, or device type.

OneOPS returns matching runbooks and knowledge chunks together. Results prioritize exact operational tokens such as interface names, BGP states, OSPF neighbor states, SNMP OIDs, syslog mnemonics, and vendor error codes.

The result page shows citations first, then runbook steps. It does not hide uncertainty. If no strong match exists, it says which search terms were used and suggests adding or parsing more knowledge.

### Journey 4: Alert AI Consumes Knowledge Later

Alert AI diagnosis sends alert labels, device facts, time window, log terms, RCA candidate labels, and optional user question to the retrieval contract.

The knowledge service returns top cited chunks and relevant published runbooks. Alert AI may include those references in its report, but it must keep generated claims separate from cited facts.

### Journey 5: Review Parse Failures

An admin opens failed documents, sees parse error reason, file metadata, checksum, and retry action. The admin can retry parsing after fixing the file format or replacing the document.

## Recommended Approach

Use an internal lightweight implementation first.

OneOPS already has enough platform pieces for an MVP:

- `OneOPS/app/aiops` can host the service boundary and retrieval contract.
- `OneOPS/app/file` and `OneOPS/app/storage` can store or reference uploaded source documents.
- `OneOPS/app/platform` task templates can be referenced by SOP steps.
- `OneOPS/app/llm` and local Ollama can be used later for optional extraction, summarization, and query expansion.
- `OneOPS-UI/src/views/aiops` and `OneOPS-UI/src/api/aiops.ts` establish the frontend/API style.

The first version should avoid a mandatory vector store. Network operations search depends heavily on exact strings, so deterministic keyword and metadata retrieval is useful immediately and lowers deployment cost.

## Architecture

```text
Knowledge And SOP Page
  -> AIOps Knowledge API
    -> Knowledge Document Service
      -> Source File Reference
      -> Parser
      -> Chunker
      -> Metadata Extractor
    -> Runbook Service
      -> Runbook CRUD
      -> Step Validation
      -> Task Template Link Validation
    -> Retrieval Service
      -> Keyword Index
      -> Metadata Filter
      -> Citation Builder
      -> Optional Ollama Query Expansion

Alert AI Diagnosis, later
  -> Retrieval Service
  -> Cited Knowledge Context
```

## Data Model

### KnowledgeSpace

Represents a tenant-scoped container for documents and runbooks.

Fields:

- `id`: stable code.
- `tenant_id`: tenant scope.
- `name`: display name.
- `description`: short purpose.
- `visibility`: `tenant` or `private`.
- `owner`: creator or owning team.
- `status`: `active` or `archived`.
- `created_at`, `updated_at`.

### KnowledgeDocument

Represents a registered source document.

Fields:

- `id`: stable code.
- `tenant_id`.
- `space_id`.
- `title`.
- `source_type`: `upload`, `local_ref`, or `manual_text`.
- `file_ref`: existing OneOPS file or storage object reference.
- `content_type`: `text`, `markdown`, or `unknown`.
- `checksum`.
- `version`.
- `tags`: vendor, protocol, device type, product, scenario.
- `parser_status`: `pending`, `parsed`, `failed`.
- `parser_error`.
- `created_at`, `updated_at`, `parsed_at`.

### KnowledgeChunk

Represents a searchable and citable text fragment.

Fields:

- `id`: stable code.
- `tenant_id`.
- `space_id`.
- `document_id`.
- `chunk_index`.
- `heading`.
- `content`.
- `source_ref`: page, section, line range, or chunk ref.
- `keywords`: normalized exact tokens.
- `entities`: extracted vendor, protocol, command, error code, device type, interface, metric name.
- `content_hash`.
- `created_at`.

### Runbook

Represents a standardized operation guide.

Fields:

- `id`: stable code.
- `tenant_id`.
- `space_id`.
- `title`.
- `scenario`.
- `applicable_assets`: device types, vendors, systems, protocols.
- `severity`: `info`, `minor`, `major`, or `critical`.
- `risk_level`: `low`, `medium`, or `high`.
- `status`: `draft`, `published`, or `archived`.
- `tags`.
- `triggers`: alert names, log phrases, metrics, symptoms.
- `required_evidence`.
- `citation_ids`.
- `created_at`, `updated_at`, `published_at`.

### RunbookStep

Represents one ordered SOP step.

Fields:

- `id`.
- `runbook_id`.
- `step_order`.
- `action_type`: `observe`, `show_suggestion`, `manual_check`, or `task_template_reference`.
- `title`.
- `instruction`.
- `suggested_show`: read-only command or query text when action type is `show_suggestion`.
- `task_template_id`: optional OneOPS task template id.
- `requires_approval`: always true for task template references.
- `risk_note`.
- `citation_ids`.

### Citation

Represents a stable evidence reference.

Fields:

- `source_type`: `document_chunk` or `runbook`.
- `source_id`.
- `title`.
- `ref`: document title plus section, line, chunk, or runbook step.
- `snippet`.
- `score`.

### RetrievalRequest

Internal service request shape:

```json
{
  "tenant_id": "tenant-a",
  "query": "BGP neighbor went Idle hold timer expired",
  "filters": {
    "space_id": "default",
    "vendor": "cisco",
    "device_type": "router",
    "protocol": "bgp"
  },
  "limit": 10,
  "include_runbooks": true,
  "include_chunks": true
}
```

### RetrievalResponse

Internal service response shape:

```json
{
  "query_terms": ["bgp", "neighbor", "idle", "hold timer expired"],
  "runbooks": [
    {
      "id": "rb-bgp-neighbor-down",
      "title": "BGP Neighbor Down Standard Check",
      "score": 92,
      "matched_steps": [1, 2, 3],
      "citations": ["cit-001"]
    }
  ],
  "chunks": [
    {
      "id": "chunk-001",
      "title": "BGP Troubleshooting Notes",
      "ref": "BGP Troubleshooting Notes > Hold Timer > chunk 3",
      "snippet": "Hold timer expiry often indicates packet loss, policy mismatch, or peer reachability problems.",
      "score": 88
    }
  ],
  "gaps": []
}
```

## Parsing And Indexing

MVP parser support:

- Plain text.
- Markdown.
- Manual pasted text.

Parser behavior:

- Normalize line endings and whitespace.
- Preserve headings.
- Chunk by heading first, then by maximum character budget.
- Store line ranges when the source supports them.
- Extract keywords through deterministic tokenization.
- Extract entities with simple rules for vendors, protocols, command words, error codes, interface-like tokens, and common alert terms.
- Compute document checksum and chunk content hash.

Optional local Ollama use:

- Generate a document summary.
- Suggest tags.
- Suggest candidate runbook scenarios.
- Expand user search query with synonyms.

Ollama output must be treated as enrichment, not as the source of truth. Search results still cite stored chunks and runbooks.

## Retrieval Strategy

MVP retrieval is hybrid without mandatory vector infrastructure:

- Exact token match for operational strings.
- Metadata filtering by tenant, space, vendor, protocol, device type, and status.
- Runbook trigger matching.
- Basic score composition from term frequency, title match, tag match, trigger match, and recency.

Stage 2 can add local embeddings through Ollama and a local vector index. That stage should be optional and must not break the deterministic keyword path.

## API Sketch

External API:

- `GET /api/v1/aiops/knowledge/spaces`
- `POST /api/v1/aiops/knowledge/spaces`
- `GET /api/v1/aiops/knowledge/documents`
- `POST /api/v1/aiops/knowledge/documents`
- `POST /api/v1/aiops/knowledge/documents/:id/parse`
- `GET /api/v1/aiops/knowledge/documents/:id/chunks`
- `GET /api/v1/aiops/knowledge/search`
- `GET /api/v1/aiops/runbooks`
- `POST /api/v1/aiops/runbooks`
- `GET /api/v1/aiops/runbooks/:id`
- `PUT /api/v1/aiops/runbooks/:id`
- `POST /api/v1/aiops/runbooks/:id/publish`

Internal service contract:

- `RetrieveKnowledge(ctx, req) (RetrievalResponse, error)`

The internal contract is the stable integration point for alert AI diagnosis and future incident workflows.

## Frontend Experience

Add a dedicated "知识与SOP" operational page under the AIOps or operations navigation area.

The first screen is the working surface, not a landing page.

Tabs:

- `知识文档`: document list, parse status, tags, parser errors, parse/retry action.
- `标准操作`: runbook list, status, scenario, risk, linked task template count, publish state.
- `检索`: search input, filters, cited results, matching runbooks, matching chunks.

Runbook detail layout:

- Summary band with scenario, risk, status, tags, applicable assets.
- Required evidence.
- Ordered step list.
- Citations attached to each step.
- Linked task template shown as a manual action. It does not auto-run.

Search result layout:

- Top matches grouped by runbook and document chunk.
- Each item shows score, citation ref, snippet, tags, and source document.
- Empty state shows searched terms and missing coverage instead of generic failure text.

## Safety And Governance

- Every query is tenant scoped.
- Only published runbooks are returned to normal operator searches by default.
- Draft runbooks are visible only to editors and admins.
- `show_suggestion` steps are read-only guidance.
- `task_template_reference` steps must require manual launch and existing OneOPS permissions.
- Search results must include citations for knowledge claims.
- Generated summaries must be labeled as generated and linked back to source chunks.
- Cross-tenant document leakage is a release blocker.

## Longest MVP Smoke Path

The longest path should verify:

1. Create a knowledge space.
2. Register a Markdown document with BGP or interface troubleshooting content.
3. Parse the document.
4. Verify chunks and citations were created.
5. Create a runbook that links one chunk and one existing task template id or a mocked task template reference.
6. Publish the runbook.
7. Search with a log phrase or symptom.
8. Verify the response contains the runbook, document chunk, citation refs, query terms, and no cross-tenant results.
9. Load the frontend page.
10. Verify the document list, runbook list, and search result render without console errors.
11. Call the internal retrieval contract with an alert-style request and verify cited context is returned.

## Test Plan

Backend unit tests:

- Chunker preserves headings and creates stable chunk indexes.
- Parser stores failed status and error text for unsupported or empty content.
- Keyword extractor keeps operational tokens such as `BGP`, `OSPF`, `Gi1/0/24`, `LINK-3-UPDOWN`, and `hold timer`.
- Retrieval ranks title, trigger, tag, and exact phrase matches above weak content-only matches.
- Tenant scoping prevents cross-tenant retrieval.
- Runbook validation rejects non-read-only command actions and missing manual approval for task template references.

Backend API tests:

- Create/list knowledge space.
- Register/parse document.
- List chunks.
- Create/update/publish runbook.
- Search returns cited chunks and published runbooks.

Frontend smoke tests:

- Knowledge document tab loads and shows parse states.
- Runbook tab loads and shows draft/published status.
- Search tab submits a query and renders citations.
- Empty search result displays searched terms and coverage gap.

Integration smoke:

- Internal retrieval contract returns cited knowledge for an alert-style query.

## Acceptance Criteria

- A user can register a text or Markdown knowledge document and parse it into searchable chunks.
- A user can create and publish a runbook with ordered steps and citations.
- Search returns cited runbooks and document chunks for a real operations phrase.
- Results are tenant scoped.
- SOP steps do not auto-execute remediation.
- Linked task templates remain manual actions.
- Alert AI can later consume the internal retrieval contract without depending on UI state.
- The MVP can run without deploying Dify, RAGFlow, Open WebUI, AnythingLLM, Elasticsearch, or pgvector.

## Implementation Phasing

### Phase 1: Internal Data And Retrieval Core

Create backend DTOs, models, parser, chunker, keyword extraction, runbook validation, retrieval ranking, and tests.

### Phase 2: API Surface

Expose knowledge space, document, parse, chunk, runbook, publish, and search APIs in the AIOps API style.

### Phase 3: Frontend Operational Page

Add the "知识与SOP" page with documents, runbooks, and search tabs. Keep the UI dense and operational.

### Phase 4: Alert AI Contract Hook

Expose the internal retrieval service to alert AI diagnosis as an optional context provider. The first integration may be contract-level only, then UI report citations can follow.

## Open Design Choices Fixed For MVP

- First parser formats are text, Markdown, and manual text.
- First retrieval mode is deterministic keyword plus metadata search.
- Vector embeddings are stage 2.
- Third-party RAG platforms are not part of required deployment.
- Runbook task template links are manual references only.
- Frontend starts as one page with three tabs.
