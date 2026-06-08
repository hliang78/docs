# Config Version Compare Selection Design

Date: 2026-06-08

## Goal

Make the `配置管理` page's `版本对比` action work naturally from the current queue selection.

## Behavior

- When exactly one selected asset has a current version and previous version, open the diff drawer with `previousVersionId` as the left version and `versionId` as the right version.
- When exactly two selected assets both have current versions, open the diff drawer with the first selected asset's current version as the left version and the second selected asset's current version as the right version. The backend center diff endpoint already allows cross-device comparison.
- When no asset is selected, more than two assets are selected, or the selected rows do not provide enough version ids, open the existing manual version picker.

## Scope

This is a frontend interaction refinement. The existing backend service and center diff API already support both same-device and cross-device version comparison.

## Testing

Add a small helper-level smoke test that verifies selected-row compare intent for one-row, two-row, and manual fallback cases.
