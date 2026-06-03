# Device V2 Detail And Collection Drawer Verification

## Scope

- Device detail is rendered from structured sections.
- Server and network devices use type-specific sections.
- Collection result drawer shows task overview, device result list, structured collected data, field details, and technical evidence.
- Batch collection triggers and batch task workbench behavior were not changed.

## Files

- `OneOPS-UI/src/views/device/device-v2-management/detail-section-model.ts`
- `OneOPS-UI/src/views/device/device-v2-management/collection-result-model.ts`
- `OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue`
- `OneOPS-UI/scripts/device-v2-detail-collection-model-smoke.ts`

## Validation

- `npm run smoke:device-v2-detail-collection-model`
- `npm run typecheck:d2`

## Preserved Behaviors

- Manual refresh remains available in the collection drawer.
- Running collection task auto-refresh remains available.
- Batch task restoration remains available through `restoreBatchWorkbenches`.
- Diagnostic log download remains available through `downloadCollectDiagnosticLogs`.
- Latest DC2 collection detail jump remains available through `openSelectedDeviceLastCollectionWorkbench` and `openDc2CollectionDetail`.

## Risk

No backend contract changes are included. Existing Device V2 attributes, metadata, labels, latest collection, run, observation, and plan fields are reorganized for display only.
