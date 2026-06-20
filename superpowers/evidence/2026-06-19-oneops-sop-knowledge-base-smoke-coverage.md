# OneOPS SOP Knowledge Base Smoke Coverage

Date: 2026-06-19

## Longest Covered Path

The current full smoke covers the MVP path below:

1. Backend migrates knowledge/SOP models into an empty SQLite database.
2. Operator creates a knowledge space.
3. Operator creates a `manual_text` Markdown document.
4. Backend parses the document into cited chunks.
5. Operator creates a runbook with a `show_suggestion` step and chunk citation.
6. Operator publishes the runbook.
7. Retrieval searches by query plus `vendor`, `device_type`, and `protocol`.
8. Retrieval returns the published runbook, document chunk, and citation.
9. Backend API tests cover route/handler wrappers for the same long path.
10. Frontend smoke confirms types, API wrappers, route fallback, page controls, row selection, and space-switch state cleanup.

## Verification Commands

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
./scripts/aiops_sop_knowledge_full_smoke.sh
```

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npm run typecheck
```

## Explicitly Covered

- DTO validation for documents, runbooks, safe `show_suggestion`, task-template approval, and retrieval defaults.
- GORM models and SQLite AutoMigrate for knowledge spaces, documents, chunks, runbooks, and steps.
- Parser heading preservation, chunk refs, keyword extraction, and stable content hash.
- Parse failure for empty manual text.
- Parse failure for unloaded `upload` / `local_ref` document sources.
- Transactional replacement of parsed chunks on successful parse.
- Tenant-scoped retrieval.
- Published-only runbook retrieval.
- Parsed-only chunk retrieval.
- Metadata filters for `vendor`, `device_type`, and `protocol`.
- False-positive guard so metadata filters do not match incidental body prose.
- Backend API route consistency with frontend wrappers.
- Frontend route fallback for AIOps "知识与SOP".
- Frontend page controls for create space, create document, parse, view chunks, create runbook, publish, and search.
- Frontend row selection uses Ant Design Vue `custom-row`.
- Frontend space switching clears stale document/runbook/chunk/search state.

## Not Yet Covered

- Real MySQL migration execution against a MySQL server.
- Real file upload or local file content loading for `upload` and `local_ref`; these now fail explicitly until a loader is implemented.
- Browser-driven click smoke with a live backend and screenshots.
- Actual alert detail "AI 分析" enrichment with retrieved SOP/knowledge. This is intentionally later than the independent knowledge/SOP track.
- LLM/Ollama extraction or semantic query expansion.
- PDF/DOCX parsing.
- Full task-template lookup validation for `task_template_reference`; current MVP validates `task_template_id` and approval but does not verify template existence.
- Fine-grained RBAC/permission checks beyond tenant IDs supplied in requests.
