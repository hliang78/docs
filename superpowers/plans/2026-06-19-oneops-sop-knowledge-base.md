# OneOPS SOP Knowledge Base Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an independent OneOPS "知识与SOP" MVP with document parsing, cited SOP/runbook management, deterministic retrieval, frontend closure, and an internal retrieval contract usable by alert AI.

**Architecture:** Keep the MVP inside the existing `app/aiops` boundary. Store source documents, chunks, runbooks, and steps in MySQL through GORM models; retrieve with deterministic keyword and metadata scoring; expose AIOps APIs and a dense Vue operational page. Alert AI integration uses a service contract first, so the feature remains independently usable.

**Tech Stack:** Go 1.25, Gin, GORM, MySQL/SQLite tests, existing OneOPS tenant scoping patterns, Vue 3, TypeScript, Ant Design Vue, esbuild smoke scripts.

---

## File Structure

Backend files:

- Create: `OneOPS/app/aiops/dto/knowledge.go` - public DTOs, constants, and validation helpers for spaces, documents, chunks, runbooks, retrieval, and citations.
- Create: `OneOPS/app/aiops/dto/knowledge_test.go` - DTO validation and fixture tests.
- Create: `OneOPS/app/aiops/aiops_model/knowledge.go` - GORM models for knowledge spaces, documents, chunks, runbooks, and runbook steps.
- Modify: `OneOPS/initialize/mysql.go` - add new AIOps knowledge models to AutoMigrate list next to `IncidentAnalysisRecord`.
- Create: `OneOPS/migrations/add_aiops_sop_knowledge_base.sql` - explicit MySQL DDL for controlled environments.
- Modify: `OneOPS/app/aiops/service/service.go` - add `KnowledgeService` and `KnowledgeRetriever` interfaces.
- Create: `OneOPS/app/aiops/service/impl/knowledge_parser.go` - text/Markdown parsing, heading preservation, chunking, keyword/entity extraction.
- Create: `OneOPS/app/aiops/service/impl/knowledge_parser_test.go` - parser/chunker/entity tests.
- Create: `OneOPS/app/aiops/service/impl/mysql_knowledge_service.go` - CRUD, parse persistence, runbook validation, retrieval ranking.
- Create: `OneOPS/app/aiops/service/impl/mysql_knowledge_service_test.go` - SQLite-backed persistence, tenant scoping, retrieval, and safety tests.
- Modify: `OneOPS/app/aiops/service/impl/module.go` - wire `MySQLKnowledgeService` to `KnowledgeService` and `KnowledgeRetriever`.
- Modify: `OneOPS/app/aiops/api/aiops.go` - add handlers for spaces, documents, chunks, runbooks, publish, search, and contract smoke endpoint.
- Create: `OneOPS/app/aiops/api/knowledge_test.go` - API handler tests.
- Modify: `OneOPS/app/aiops/router/aiops.go` - register knowledge and runbook routes.
- Create: `OneOPS/scripts/aiops_sop_knowledge_long_chain_smoke.go` - backend longest-chain smoke through service APIs.

Frontend files:

- Modify: `OneOPS-UI/src/typings/aiops.ts` - add knowledge/runbook/retrieval types.
- Modify: `OneOPS-UI/src/api/aiops.ts` - add knowledge API functions.
- Create: `OneOPS-UI/src/views/aiops/AIOpsKnowledgeSOP.vue` - operational page with document, runbook, and search tabs.
- Modify: `OneOPS-UI/src/router/utils.ts` - add AIOps "知识与SOP" fallback menu/route.
- Create: `OneOPS-UI/scripts/aiops-knowledge-sop-smoke.ts` - frontend helper smoke for API wrappers, result grouping, and route/menu injection.
- Modify: `OneOPS-UI/package.json` - add `smoke:aiops-knowledge-sop`.

Combined smoke:

- Create: `OneOPS/scripts/aiops_sop_knowledge_full_smoke.sh` - combined backend/frontend smoke entry.

---

## Task 1: Backend DTOs And Validation

**Files:**

- Create: `OneOPS/app/aiops/dto/knowledge.go`
- Create: `OneOPS/app/aiops/dto/knowledge_test.go`

- [ ] **Step 1: Write failing DTO validation tests**

Add tests covering:

```go
func TestKnowledgeDocumentCreateReqValidation(t *testing.T) {
	req := KnowledgeDocumentCreateReq{
		TenantID:    "TENANT-A",
		SpaceID:     "space-default",
		Title:       "BGP Troubleshooting Notes",
		SourceType:  KnowledgeSourceManualText,
		ContentType: KnowledgeContentMarkdown,
		ManualText:  "# BGP\nNeighbor Idle hold timer expired",
		Tags:        []string{"cisco", "bgp"},
	}
	if err := ValidateKnowledgeDocumentCreateReq(req); err != nil {
		t.Fatalf("expected valid document request, got %v", err)
	}
}

func TestKnowledgeDocumentCreateReqRejectsEmptyManualText(t *testing.T) {
	req := KnowledgeDocumentCreateReq{
		TenantID:    "TENANT-A",
		SpaceID:     "space-default",
		Title:       "empty",
		SourceType:  KnowledgeSourceManualText,
		ContentType: KnowledgeContentMarkdown,
	}
	err := ValidateKnowledgeDocumentCreateReq(req)
	if err == nil || !strings.Contains(err.Error(), "manual_text is required") {
		t.Fatalf("expected manual text error, got %v", err)
	}
}

func TestRunbookValidationRejectsUnsafeShowSuggestion(t *testing.T) {
	req := RunbookCreateReq{
		TenantID: "TENANT-A",
		SpaceID:  "space-default",
		Title:    "Unsafe Step",
		Scenario: "interface check",
		Steps: []RunbookStepReq{{
			Order:         1,
			ActionType:    RunbookStepShowSuggestion,
			Title:         "bad command",
			Instruction:   "do not execute",
			SuggestedShow: "configure terminal",
		}},
	}
	err := ValidateRunbookCreateReq(req)
	if err == nil || !strings.Contains(err.Error(), "suggested_show must be read-only") {
		t.Fatalf("expected read-only error, got %v", err)
	}
}

func TestRetrievalRequestDefaults(t *testing.T) {
	req := RetrievalRequest{TenantID: "TENANT-A", Query: "BGP hold timer"}
	normalized, err := NormalizeRetrievalRequest(req)
	if err != nil {
		t.Fatalf("expected valid retrieval request, got %v", err)
	}
	if normalized.Limit != 10 || !normalized.IncludeRunbooks || !normalized.IncludeChunks {
		t.Fatalf("unexpected defaults: %+v", normalized)
	}
}
```

Run:

```bash
cd OneOPS && go test ./app/aiops/dto -run 'TestKnowledge|TestRunbook|TestRetrieval' -count=1
```

Expected: FAIL with undefined knowledge DTOs and validators.

- [ ] **Step 2: Implement DTOs and validators**

Create `knowledge.go` with these exact public names:

```go
package dto

import (
	"fmt"
	"strings"
)

const (
	KnowledgeSourceUpload     = "upload"
	KnowledgeSourceLocalRef   = "local_ref"
	KnowledgeSourceManualText = "manual_text"

	KnowledgeContentText     = "text"
	KnowledgeContentMarkdown = "markdown"
	KnowledgeContentUnknown  = "unknown"

	KnowledgeParsePending = "pending"
	KnowledgeParseParsed  = "parsed"
	KnowledgeParseFailed  = "failed"

	RunbookStatusDraft     = "draft"
	RunbookStatusPublished = "published"
	RunbookStatusArchived  = "archived"

	RunbookRiskLow    = "low"
	RunbookRiskMedium = "medium"
	RunbookRiskHigh   = "high"

	RunbookStepObserve               = "observe"
	RunbookStepShowSuggestion        = "show_suggestion"
	RunbookStepManualCheck           = "manual_check"
	RunbookStepTaskTemplateReference = "task_template_reference"
)

type KnowledgeSpaceResp struct {
	ID          string `json:"id"`
	TenantID    string `json:"tenant_id"`
	Name        string `json:"name"`
	Description string `json:"description,omitempty"`
	Visibility  string `json:"visibility"`
	Owner       string `json:"owner,omitempty"`
	Status      string `json:"status"`
	CreatedAt   string `json:"created_at,omitempty"`
	UpdatedAt   string `json:"updated_at,omitempty"`
}

type KnowledgeSpaceCreateReq struct {
	TenantID     string `json:"tenant_id"`
	Name         string `json:"name"`
	Description  string `json:"description,omitempty"`
	Visibility   string `json:"visibility,omitempty"`
	Owner        string `json:"owner,omitempty"`
}

type KnowledgeDocumentCreateReq struct {
	TenantID    string   `json:"tenant_id"`
	SpaceID     string   `json:"space_id"`
	Title       string   `json:"title"`
	SourceType  string   `json:"source_type"`
	FileRef     string   `json:"file_ref,omitempty"`
	ContentType string   `json:"content_type"`
	ManualText  string   `json:"manual_text,omitempty"`
	Tags        []string `json:"tags,omitempty"`
}

type KnowledgeDocumentResp struct {
	ID           string   `json:"id"`
	TenantID     string   `json:"tenant_id"`
	SpaceID      string   `json:"space_id"`
	Title        string   `json:"title"`
	SourceType   string   `json:"source_type"`
	FileRef      string   `json:"file_ref,omitempty"`
	ContentType  string   `json:"content_type"`
	Checksum     string   `json:"checksum,omitempty"`
	Version      int      `json:"version"`
	Tags         []string `json:"tags,omitempty"`
	ParserStatus string   `json:"parser_status"`
	ParserError  string   `json:"parser_error,omitempty"`
	CreatedAt    string   `json:"created_at,omitempty"`
	UpdatedAt    string   `json:"updated_at,omitempty"`
	ParsedAt     string   `json:"parsed_at,omitempty"`
}

type KnowledgeChunkResp struct {
	ID          string   `json:"id"`
	TenantID    string   `json:"tenant_id"`
	SpaceID     string   `json:"space_id"`
	DocumentID  string   `json:"document_id"`
	ChunkIndex  int      `json:"chunk_index"`
	Heading     string   `json:"heading,omitempty"`
	Content     string   `json:"content"`
	SourceRef   string   `json:"source_ref"`
	Keywords    []string `json:"keywords,omitempty"`
	Entities    []string `json:"entities,omitempty"`
	ContentHash string   `json:"content_hash"`
}

type RunbookCreateReq struct {
	TenantID         string           `json:"tenant_id"`
	SpaceID          string           `json:"space_id"`
	Title            string           `json:"title"`
	Scenario         string           `json:"scenario"`
	ApplicableAssets []string         `json:"applicable_assets,omitempty"`
	Severity         string           `json:"severity,omitempty"`
	RiskLevel        string           `json:"risk_level,omitempty"`
	Tags             []string         `json:"tags,omitempty"`
	Triggers         []string         `json:"triggers,omitempty"`
	RequiredEvidence []string         `json:"required_evidence,omitempty"`
	CitationIDs      []string         `json:"citation_ids,omitempty"`
	Steps            []RunbookStepReq `json:"steps"`
}

type RunbookStepReq struct {
	Order            int      `json:"order"`
	ActionType       string   `json:"action_type"`
	Title            string   `json:"title"`
	Instruction      string   `json:"instruction"`
	SuggestedShow    string   `json:"suggested_show,omitempty"`
	TaskTemplateID   string   `json:"task_template_id,omitempty"`
	RequiresApproval bool     `json:"requires_approval"`
	RiskNote         string   `json:"risk_note,omitempty"`
	CitationIDs      []string `json:"citation_ids,omitempty"`
}

type RunbookResp struct {
	ID               string            `json:"id"`
	TenantID         string            `json:"tenant_id"`
	SpaceID          string            `json:"space_id"`
	Title            string            `json:"title"`
	Scenario         string            `json:"scenario"`
	ApplicableAssets []string          `json:"applicable_assets,omitempty"`
	Severity         string            `json:"severity"`
	RiskLevel        string            `json:"risk_level"`
	Status           string            `json:"status"`
	Tags             []string          `json:"tags,omitempty"`
	Triggers         []string          `json:"triggers,omitempty"`
	RequiredEvidence []string          `json:"required_evidence,omitempty"`
	CitationIDs      []string          `json:"citation_ids,omitempty"`
	Steps            []RunbookStepResp `json:"steps,omitempty"`
	CreatedAt        string            `json:"created_at,omitempty"`
	UpdatedAt        string            `json:"updated_at,omitempty"`
	PublishedAt      string            `json:"published_at,omitempty"`
}

type RunbookStepResp struct {
	ID               string   `json:"id"`
	RunbookID        string   `json:"runbook_id"`
	Order            int      `json:"order"`
	ActionType       string   `json:"action_type"`
	Title            string   `json:"title"`
	Instruction      string   `json:"instruction"`
	SuggestedShow    string   `json:"suggested_show,omitempty"`
	TaskTemplateID   string   `json:"task_template_id,omitempty"`
	RequiresApproval bool     `json:"requires_approval"`
	RiskNote         string   `json:"risk_note,omitempty"`
	CitationIDs      []string `json:"citation_ids,omitempty"`
}

type RetrievalFilters struct {
	SpaceID    string `json:"space_id,omitempty" form:"space_id"`
	Vendor     string `json:"vendor,omitempty" form:"vendor"`
	DeviceType string `json:"device_type,omitempty" form:"device_type"`
	Protocol   string `json:"protocol,omitempty" form:"protocol"`
}

type RetrievalRequest struct {
	TenantID         string           `json:"tenant_id" form:"tenant_id"`
	Query            string           `json:"query" form:"query"`
	Filters          RetrievalFilters `json:"filters,omitempty"`
	Limit            int              `json:"limit,omitempty" form:"limit"`
	IncludeRunbooks  bool             `json:"include_runbooks"`
	IncludeChunks    bool             `json:"include_chunks"`
	PublishedOnly    bool             `json:"published_only"`
}

type RetrievalCitation struct {
	SourceType string `json:"source_type"`
	SourceID   string `json:"source_id"`
	Title      string `json:"title"`
	Ref        string `json:"ref"`
	Snippet    string `json:"snippet"`
	Score      int    `json:"score"`
}

type RetrievalRunbookResult struct {
	ID           string              `json:"id"`
	Title        string              `json:"title"`
	Score        int                 `json:"score"`
	MatchedSteps []int               `json:"matched_steps,omitempty"`
	Citations    []RetrievalCitation `json:"citations,omitempty"`
}

type RetrievalChunkResult struct {
	ID        string `json:"id"`
	Title     string `json:"title"`
	Ref       string `json:"ref"`
	Snippet   string `json:"snippet"`
	Score     int    `json:"score"`
	SourceRef string `json:"source_ref,omitempty"`
}

type RetrievalResponse struct {
	QueryTerms []string                 `json:"query_terms"`
	Runbooks   []RetrievalRunbookResult `json:"runbooks"`
	Chunks     []RetrievalChunkResult   `json:"chunks"`
	Gaps       []string                 `json:"gaps,omitempty"`
}
```

Implement validators with these rules:

- `tenant_id`, `space_id`, `title`, and document/runbook identifiers are trimmed and required where used.
- Manual text documents require non-empty `manual_text`.
- Upload/local ref documents require non-empty `file_ref`.
- `RunbookStepShowSuggestion` must pass the existing read-only boundary: accept strings starting with `show`, `display`, `get`, or `kubectl get`; reject `configure`, `delete`, `rm`, `write`, `reload`, `restart`, `set`, and `commit`.
- `RunbookStepTaskTemplateReference` requires `task_template_id` and `requires_approval=true`.
- Retrieval limit defaults to 10, maxes at 50, and defaults both include flags to true when both are false.

- [ ] **Step 3: Run DTO tests**

Run:

```bash
cd OneOPS && go test ./app/aiops/dto -run 'TestKnowledge|TestRunbook|TestRetrieval' -count=1
```

Expected: PASS.

- [ ] **Step 4: Commit DTO task**

```bash
git -C OneOPS add app/aiops/dto/knowledge.go app/aiops/dto/knowledge_test.go
git -C OneOPS commit -m "feat(aiops): add knowledge SOP DTO contracts"
```

---

## Task 2: Backend Models, Migration, Parser, And Retrieval Core

**Files:**

- Create: `OneOPS/app/aiops/aiops_model/knowledge.go`
- Modify: `OneOPS/initialize/mysql.go`
- Create: `OneOPS/migrations/add_aiops_sop_knowledge_base.sql`
- Modify: `OneOPS/app/aiops/service/service.go`
- Create: `OneOPS/app/aiops/service/impl/knowledge_parser.go`
- Create: `OneOPS/app/aiops/service/impl/knowledge_parser_test.go`
- Create: `OneOPS/app/aiops/service/impl/mysql_knowledge_service.go`
- Create: `OneOPS/app/aiops/service/impl/mysql_knowledge_service_test.go`
- Modify: `OneOPS/app/aiops/service/impl/module.go`

- [ ] **Step 1: Write failing parser tests**

Create parser tests that assert heading-aware chunks, stable source refs, and operational token extraction:

```go
func TestParseKnowledgeTextPreservesHeadingsAndOperationalTokens(t *testing.T) {
	doc := "# BGP\nNeighbor Idle hold timer expired on Gi1/0/24\n\n## Checks\nshow bgp summary\n"
	chunks := ParseKnowledgeText("doc-1", doc, KnowledgeParseOptions{MaxChunkChars: 120})
	if len(chunks) != 2 {
		t.Fatalf("expected heading chunks, got %d: %+v", len(chunks), chunks)
	}
	if chunks[0].Heading != "BGP" || chunks[1].Heading != "Checks" {
		t.Fatalf("unexpected headings: %+v", chunks)
	}
	joined := strings.Join(chunks[0].Keywords, " ")
	for _, want := range []string{"bgp", "idle", "hold", "timer", "gi1/0/24"} {
		if !strings.Contains(joined, want) {
			t.Fatalf("expected token %q in %q", want, joined)
		}
	}
}

func TestParseKnowledgeTextRejectsEmptyContent(t *testing.T) {
	chunks := ParseKnowledgeText("doc-1", "  \n\t", KnowledgeParseOptions{MaxChunkChars: 120})
	if len(chunks) != 0 {
		t.Fatalf("expected no chunks, got %+v", chunks)
	}
}
```

Run:

```bash
cd OneOPS && go test ./app/aiops/service/impl -run 'TestParseKnowledge' -count=1
```

Expected: FAIL with undefined parser.

- [ ] **Step 2: Implement GORM models and migration**

Create models with table names:

- `aiops_knowledge_space`
- `aiops_knowledge_document`
- `aiops_knowledge_chunk`
- `aiops_runbook`
- `aiops_runbook_step`

Model implementation requirements:

- Use `uuid.NewString()` in `BeforeCreate`.
- Use `datatypes.JSON` for tag arrays, entity arrays, citation id arrays, and required evidence arrays.
- Include `TenantID`, `SpaceID`, status fields, timestamps, and `gorm.DeletedAt`.
- Add indexes for tenant, space, document, runbook, parse status, runbook status, and deleted_at.
- Add all five models to `Models()` in `OneOPS/initialize/mysql.go` immediately after `aiops_model.IncidentAnalysisRecord{}`.

The SQL migration must create all five tables with `utf8mb4`, primary keys, the same indexes, and JSON columns for arrays. Keep it idempotent with `CREATE TABLE IF NOT EXISTS`.

- [ ] **Step 3: Implement parser and keyword extraction**

Create `KnowledgeParseOptions`, `ParsedKnowledgeChunk`, `ParseKnowledgeText`, `ExtractKnowledgeKeywords`, and `KnowledgeContentHash`.

Required behavior:

- Normalize CRLF to LF.
- Markdown headings begin with one or more `#` characters.
- Plain text with no headings becomes chunk heading `General`.
- Chunk size defaults to 1600 characters and never emits empty chunks.
- Source refs use `chunk:<index>` at minimum and `lines:<start>-<end>` when line numbers are known.
- Keywords are lowercase, deduplicated, and preserve useful network tokens.

- [ ] **Step 4: Write failing service tests**

Tests must cover:

- Create default space.
- Register manual Markdown document.
- Parse document into chunks and mark status `parsed`.
- Persist parser failure for empty manual text.
- Create runbook with a cited chunk.
- Reject unsafe `suggested_show`.
- Publish runbook.
- Search returns only same-tenant results.
- Search ranks published runbook and chunk for `BGP hold timer`.
- Internal retrieval contract returns query terms and citation refs.

Run:

```bash
cd OneOPS && go test ./app/aiops/service/impl -run 'TestMySQLKnowledge|TestKnowledgeRetrieval|TestRunbook' -count=1
```

Expected: FAIL with undefined service.

- [ ] **Step 5: Implement `KnowledgeService` and `KnowledgeRetriever`**

Add these interfaces to `OneOPS/app/aiops/service/service.go`:

```go
type KnowledgeService interface {
	CreateKnowledgeSpace(ctx context.Context, req dto.KnowledgeSpaceCreateReq) (*dto.KnowledgeSpaceResp, error)
	ListKnowledgeSpaces(ctx context.Context, tenantID string) ([]dto.KnowledgeSpaceResp, error)
	CreateKnowledgeDocument(ctx context.Context, req dto.KnowledgeDocumentCreateReq) (*dto.KnowledgeDocumentResp, error)
	ListKnowledgeDocuments(ctx context.Context, tenantID, spaceID string) ([]dto.KnowledgeDocumentResp, error)
	ParseKnowledgeDocument(ctx context.Context, tenantID, documentID string) (*dto.KnowledgeDocumentResp, error)
	ListKnowledgeChunks(ctx context.Context, tenantID, documentID string) ([]dto.KnowledgeChunkResp, error)
	CreateRunbook(ctx context.Context, req dto.RunbookCreateReq) (*dto.RunbookResp, error)
	ListRunbooks(ctx context.Context, tenantID, spaceID string) ([]dto.RunbookResp, error)
	GetRunbook(ctx context.Context, tenantID, id string) (*dto.RunbookResp, error)
	PublishRunbook(ctx context.Context, tenantID, id string) (*dto.RunbookResp, error)
	SearchKnowledge(ctx context.Context, req dto.RetrievalRequest) (*dto.RetrievalResponse, error)
}

type KnowledgeRetriever interface {
	RetrieveKnowledge(ctx context.Context, req dto.RetrievalRequest) (*dto.RetrievalResponse, error)
}
```

Implement `MySQLKnowledgeService` using `types.DBTypeMySQL`.

Persistence requirements:

- Tenant filtering appears in every query.
- `ListRunbooks` returns drafts and published for API users; `SearchKnowledge` returns published runbooks by default.
- `ParseKnowledgeDocument` deletes old chunks for that tenant/document before inserting new chunks.
- Empty parse sets status `failed` and stores parser error.
- `SearchKnowledge` scores title/tag/trigger matches above content-only matches.
- `RetrieveKnowledge` delegates to `SearchKnowledge`.
- `RunbookStepTaskTemplateReference` validates only the id and approval requirement in this task; live task-template existence can be added by API wiring if the service dependency is available.

- [ ] **Step 6: Wire service**

Modify `module.go`:

```go
NewMySQLKnowledgeService,
wire.Bind(new(aiopsService.KnowledgeService), new(*MySQLKnowledgeService)),
wire.Bind(new(aiopsService.KnowledgeRetriever), new(*MySQLKnowledgeService)),
```

- [ ] **Step 7: Run backend core tests**

Run:

```bash
cd OneOPS && go test ./app/aiops/dto ./app/aiops/service/impl -run 'TestKnowledge|TestRunbook|TestMySQLKnowledge|TestParseKnowledge' -count=1
```

Expected: PASS.

- [ ] **Step 8: Commit backend core**

```bash
git -C OneOPS add app/aiops/aiops_model/knowledge.go initialize/mysql.go migrations/add_aiops_sop_knowledge_base.sql app/aiops/service/service.go app/aiops/service/impl/knowledge_parser.go app/aiops/service/impl/knowledge_parser_test.go app/aiops/service/impl/mysql_knowledge_service.go app/aiops/service/impl/mysql_knowledge_service_test.go app/aiops/service/impl/module.go
git -C OneOPS commit -m "feat(aiops): add SOP knowledge retrieval core"
```

---

## Task 3: Backend API, Router, And Longest-Chain Backend Smoke

**Files:**

- Modify: `OneOPS/app/aiops/api/aiops.go`
- Create: `OneOPS/app/aiops/api/knowledge_test.go`
- Modify: `OneOPS/app/aiops/router/aiops.go`
- Create: `OneOPS/scripts/aiops_sop_knowledge_long_chain_smoke.go`

- [ ] **Step 1: Write failing API tests**

Cover these handlers directly with `gin.CreateTestContext`:

- `CreateKnowledgeSpace`
- `ListKnowledgeSpaces`
- `CreateKnowledgeDocument`
- `ParseKnowledgeDocument`
- `ListKnowledgeChunks`
- `CreateRunbook`
- `PublishRunbook`
- `SearchKnowledge`

Add a fake service implementing `aiopsService.KnowledgeService`. The search test should verify query params are mapped into `RetrievalRequest`:

```go
ctx, recorder := newAIOpsTestContext(t, http.MethodGet, "/aiops/knowledge/search?tenant_id=TENANT-A&query=BGP%20hold%20timer&space_id=space-default", "")
api.SearchKnowledge(ctx)
if fake.lastSearch.Query != "BGP hold timer" || fake.lastSearch.Filters.SpaceID != "space-default" {
	t.Fatalf("unexpected search request: %+v", fake.lastSearch)
}
```

Run:

```bash
cd OneOPS && go test ./app/aiops/api -run 'TestAIOpsKnowledge|TestAIOpsRunbook' -count=1
```

Expected: FAIL with undefined handlers/service field.

- [ ] **Step 2: Add API field and handlers**

Modify `AIOpsAPI`:

```go
KnowledgeService aiopsService.KnowledgeService
```

Handler behavior:

- Return `"aiops knowledge service 未初始化"` when missing.
- Use `ShouldBindJSON` for POST/PUT style handlers.
- Use `ctx.Query` for list/search filters.
- Keep response format as `response.OkWithData`.
- Use path params named `id`.

Handler names:

- `CreateKnowledgeSpace`
- `ListKnowledgeSpaces`
- `CreateKnowledgeDocument`
- `ListKnowledgeDocuments`
- `ParseKnowledgeDocument`
- `ListKnowledgeChunks`
- `CreateRunbook`
- `ListRunbooks`
- `GetRunbook`
- `PublishRunbook`
- `SearchKnowledge`

- [ ] **Step 3: Register routes**

Modify `OneOPS/app/aiops/router/aiops.go`:

```go
group.GET("knowledge/spaces", aiopsAPI.ListKnowledgeSpaces)
group.POST("knowledge/spaces", aiopsAPI.CreateKnowledgeSpace)
group.GET("knowledge/documents", aiopsAPI.ListKnowledgeDocuments)
group.POST("knowledge/documents", aiopsAPI.CreateKnowledgeDocument)
group.POST("knowledge/documents/:id/parse", aiopsAPI.ParseKnowledgeDocument)
group.GET("knowledge/documents/:id/chunks", aiopsAPI.ListKnowledgeChunks)
group.GET("knowledge/search", aiopsAPI.SearchKnowledge)
group.GET("runbooks", aiopsAPI.ListRunbooks)
group.POST("runbooks", aiopsAPI.CreateRunbook)
group.GET("runbooks/:id", aiopsAPI.GetRunbook)
group.POST("runbooks/:id/publish", aiopsAPI.PublishRunbook)
```

- [ ] **Step 4: Add backend long-chain smoke**

Create a Go script that:

1. Opens an in-memory SQLite DB.
2. AutoMigrates the five knowledge models.
3. Creates `MySQLKnowledgeService`.
4. Creates a `TENANT-A` space.
5. Registers a Markdown BGP document.
6. Parses it.
7. Creates a runbook with one `show_suggestion` step and one citation id.
8. Publishes the runbook.
9. Searches `BGP hold timer`.
10. Calls `RetrieveKnowledge`.
11. Inserts a `TENANT-B` document and proves it is not returned for `TENANT-A`.

Print this success line:

```text
aiops SOP knowledge long-chain smoke passed
```

- [ ] **Step 5: Run API and smoke verification**

Run:

```bash
cd OneOPS && go test ./app/aiops/api -run 'TestAIOpsKnowledge|TestAIOpsRunbook' -count=1
cd OneOPS && go run ./scripts/aiops_sop_knowledge_long_chain_smoke.go
```

Expected: both PASS and the smoke line appears.

- [ ] **Step 6: Commit API task**

```bash
git -C OneOPS add app/aiops/api/aiops.go app/aiops/api/knowledge_test.go app/aiops/router/aiops.go scripts/aiops_sop_knowledge_long_chain_smoke.go
git -C OneOPS commit -m "feat(aiops): expose SOP knowledge APIs"
```

---

## Task 4: Frontend API, Types, Page, Route, And Smoke

**Files:**

- Modify: `OneOPS-UI/src/typings/aiops.ts`
- Modify: `OneOPS-UI/src/api/aiops.ts`
- Create: `OneOPS-UI/src/views/aiops/AIOpsKnowledgeSOP.vue`
- Modify: `OneOPS-UI/src/router/utils.ts`
- Create: `OneOPS-UI/scripts/aiops-knowledge-sop-smoke.ts`
- Modify: `OneOPS-UI/package.json`

- [ ] **Step 1: Write failing frontend smoke**

Create a smoke script that:

- Reads `src/typings/aiops.ts` and asserts knowledge/runbook interfaces exist.
- Reads `src/api/aiops.ts` and asserts all knowledge API wrappers exist.
- Reads `src/views/aiops/AIOpsKnowledgeSOP.vue` and asserts the three tab labels exist: `知识文档`, `标准操作`, `检索`.
- Reads `src/router/utils.ts` and asserts route/menu names include `AIOpsKnowledgeSOP`.

Expected command:

```bash
cd OneOPS-UI && npx esbuild scripts/aiops-knowledge-sop-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/aiops-knowledge-sop-smoke.mjs >/dev/null && node .tmp/aiops-knowledge-sop-smoke.mjs
```

Expected: FAIL until files and package script exist.

- [ ] **Step 2: Add TypeScript types**

Add interfaces matching backend JSON names:

- `AIOpsKnowledgeSpaceResp`
- `AIOpsKnowledgeSpaceCreateReq`
- `AIOpsKnowledgeDocumentCreateReq`
- `AIOpsKnowledgeDocumentResp`
- `AIOpsKnowledgeChunkResp`
- `AIOpsRunbookCreateReq`
- `AIOpsRunbookStepReq`
- `AIOpsRunbookResp`
- `AIOpsRunbookStepResp`
- `AIOpsRetrievalFilters`
- `AIOpsRetrievalRequest`
- `AIOpsRetrievalCitation`
- `AIOpsRetrievalRunbookResult`
- `AIOpsRetrievalChunkResult`
- `AIOpsRetrievalResponse`

- [ ] **Step 3: Add API wrappers**

Add these functions to `src/api/aiops.ts`:

- `listAIOpsKnowledgeSpacesReq`
- `createAIOpsKnowledgeSpaceReq`
- `listAIOpsKnowledgeDocumentsReq`
- `createAIOpsKnowledgeDocumentReq`
- `parseAIOpsKnowledgeDocumentReq`
- `listAIOpsKnowledgeChunksReq`
- `searchAIOpsKnowledgeReq`
- `listAIOpsRunbooksReq`
- `createAIOpsRunbookReq`
- `getAIOpsRunbookReq`
- `publishAIOpsRunbookReq`

Use the same `requestEnvelope` and `assertAIOpsEnvelope` style as existing AIOps functions.

- [ ] **Step 4: Build the page**

Page requirements:

- It starts as a working surface, not a landing page.
- Header title is `知识与SOP`.
- First tab `知识文档` shows document list, parse status, tags, parser error, and parse/retry action.
- Second tab `标准操作` shows runbook list, status, scenario, risk, linked step count, and publish action.
- Third tab `检索` has query input, tenant/space filters, search button, runbook results, chunk results, citation refs, and empty coverage state.
- Create forms support manual Markdown/text document registration and runbook creation with at least one step.
- The page must not trigger task execution. Task template references are displayed as manual links/text only.
- Use existing Ant Design Vue components and compact operations-page styling.

- [ ] **Step 5: Add route and fallback menu**

Modify `router/utils.ts` by generalizing the AIOps fallback injection:

- Keep existing `AIOpsWorkbench`.
- Add `AIOpsKnowledgeSOP`.
- Route path: `aiops/knowledge-sop`.
- Component: `@/views/aiops/AIOpsKnowledgeSOP.vue`.
- Menu title: `知识与SOP`.
- Icon: `BookOutlined`.

- [ ] **Step 6: Add package smoke script**

Add to `package.json`:

```json
"smoke:aiops-knowledge-sop": "npx esbuild scripts/aiops-knowledge-sop-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/aiops-knowledge-sop-smoke.mjs >/dev/null && node .tmp/aiops-knowledge-sop-smoke.mjs"
```

- [ ] **Step 7: Run frontend verification**

Run:

```bash
cd OneOPS-UI && yarn smoke:aiops-knowledge-sop
cd OneOPS-UI && npm run typecheck
```

Expected: both PASS.

- [ ] **Step 8: Commit frontend task**

```bash
git -C OneOPS-UI add src/typings/aiops.ts src/api/aiops.ts src/views/aiops/AIOpsKnowledgeSOP.vue src/router/utils.ts scripts/aiops-knowledge-sop-smoke.ts package.json
git -C OneOPS-UI commit -m "feat(aiops): add knowledge SOP workspace"
```

---

## Task 5: Combined Longest-Chain Smoke And Alert-AI Retrieval Contract

**Files:**

- Create: `OneOPS/scripts/aiops_sop_knowledge_full_smoke.sh`
- Modify: `docs/superpowers/specs/2026-06-19-oneops-sop-knowledge-base-design.md`

- [ ] **Step 1: Create combined smoke script**

The script must run:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "$ROOT/OneOPS"
go test ./app/aiops/dto ./app/aiops/service/impl ./app/aiops/api -run 'TestKnowledge|TestRunbook|TestAIOpsKnowledge|TestAIOpsRunbook|TestParseKnowledge|TestMySQLKnowledge' -count=1
go run ./scripts/aiops_sop_knowledge_long_chain_smoke.go

cd "$ROOT/OneOPS-UI"
yarn smoke:aiops-knowledge-sop
npm run typecheck

echo "aiops SOP knowledge frontend/backend long-chain smoke passed"
```

- [ ] **Step 2: Document covered and uncovered nodes**

Append a verification note to the spec with exact coverage:

Covered by longest-chain smoke:

- Knowledge space creation.
- Manual Markdown document registration.
- Parse into chunks.
- Citation-capable chunk listing.
- Runbook creation.
- Safe `show_suggestion` validation.
- Manual task-template-reference validation.
- Runbook publish.
- Tenant-scoped search.
- Internal `RetrieveKnowledge` contract.
- Frontend API/type/route/page static closure.

Not covered by longest-chain smoke:

- Authenticated live browser click through a running OneOPS UI.
- Real file upload through storage service.
- PDF/DOCX extraction.
- Ollama query expansion.
- Real task template existence validation through platform service.
- Alert AI report rendering with knowledge citations.

- [ ] **Step 3: Run combined verification**

Run:

```bash
cd OneOPS && ./scripts/aiops_sop_knowledge_full_smoke.sh
```

Expected:

```text
aiops SOP knowledge frontend/backend long-chain smoke passed
```

- [ ] **Step 4: Commit smoke/docs task**

```bash
git -C docs add superpowers/specs/2026-06-19-oneops-sop-knowledge-base-design.md
git -C docs commit -m "docs: add SOP knowledge smoke coverage"
git -C OneOPS add scripts/aiops_sop_knowledge_full_smoke.sh
git -C OneOPS commit -m "test(aiops): add SOP knowledge long-chain smoke"
```

---

## Final Verification

Run the complete verification set:

```bash
cd OneOPS && go test ./app/aiops/... -count=1
cd OneOPS && go test ./cmd -run '^$' -count=1
cd OneOPS && go run ./scripts/aiops_sop_knowledge_long_chain_smoke.go
cd OneOPS-UI && yarn smoke:aiops-knowledge-sop
cd OneOPS-UI && npm run typecheck
cd OneOPS && ./scripts/aiops_sop_knowledge_full_smoke.sh
```

Expected:

- All Go tests pass.
- Backend smoke prints `aiops SOP knowledge long-chain smoke passed`.
- Frontend smoke passes.
- Typecheck passes.
- Combined smoke prints `aiops SOP knowledge frontend/backend long-chain smoke passed`.

## Completion Evidence Checklist

- `OneOPS/app/aiops/dto/knowledge.go` defines the MVP contract.
- `OneOPS/app/aiops/aiops_model/knowledge.go` and `OneOPS/migrations/add_aiops_sop_knowledge_base.sql` define persistence.
- `OneOPS/app/aiops/service/impl/mysql_knowledge_service.go` implements independent SOP/KB operation and retrieval.
- `OneOPS/app/aiops/api/aiops.go` and `OneOPS/app/aiops/router/aiops.go` expose the API.
- `OneOPS-UI/src/views/aiops/AIOpsKnowledgeSOP.vue` closes the frontend journey.
- `OneOPS/scripts/aiops_sop_knowledge_full_smoke.sh` proves the longest MVP path.
