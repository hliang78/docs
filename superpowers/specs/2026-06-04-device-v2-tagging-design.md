# Device V2 Tagging Design

Date: 2026-06-04

## Context

Device V2 already stores two tag-like structures:

- `labels: Record<string, string>`: structured key-value labels, suitable for search, grouping, policies, and operational semantics.
- `group_tags: string[]`: lightweight short tags, suitable for temporary batches, business groups, network zones, and fast manual grouping.

The current Device V2 management page can edit both through the full device edit modal under "标签与扩展". This works for one device, but it is too deep for common operations:

- Tagging several selected devices.
- Tagging all devices in a filtered or grouped result.
- Quickly adding/removing one tag from a single row.
- Correcting labels after import, collection, or monitoring triage.

The flexible search work already makes labels searchable. The missing piece is a convenient, safe way to apply labels.

## Goal

Make it easy to tag Device V2 devices from the management list without opening the full edit form.

The first iteration should support:

- Batch adding/removing `group_tags` on selected devices.
- Batch setting/clearing key-value `labels` on selected devices.
- A single-row shortcut that uses the same tagging editor for one device.
- A clear preview and result summary so operators understand what changed.
- Immediate compatibility with existing Device V2 search and grouping behavior.

## Non-Goals

- No automatic rule engine for tags.
- No tag approval workflow.
- No dedicated tag taxonomy administration page in this iteration.
- No historical diff viewer beyond existing Device V2 change history behavior.
- No bulk operation against arbitrary million-row result sets without an explicit selected scope.

## Recommended Approach

Add a dedicated batch tagging API and a focused tagging editor in the Device V2 management page.

This is preferred over looping existing `PUT /device/v2/:code` calls from the frontend because tagging is naturally a batch operation. A backend batch API can apply consistent validation, partial failure reporting, and future change-history/audit semantics in one place.

## UX Design

### Entry Points

Add two entry points on `/#/device/device-v2-management`:

1. **Batch toolbar button**

   Label: `打标签`

   Enabled when at least one row is selected. It opens the tagging modal/drawer for `selectedRowKeys`.

2. **Row action menu item**

   Label: `标签`

   Added under each row's `操作` menu. It opens the same tagging modal/drawer with a one-device scope.

Future extension:

- A "tag current filtered results" action can be added later, but this iteration should stay scoped to selected devices. This avoids accidental broad edits while the operator workflow is still being validated.

### Tagging Editor

Use a compact drawer or modal. A modal is enough for the first iteration because the task is short and bounded.

Header:

- Title: `设备打标签`
- Subtitle: `将应用到 N 台设备`

Body sections:

1. **短标签**

   Uses a `mode="tags"` select:

   - Add tags by typing and pressing Enter.
   - Suggested options come from selected devices plus current loaded list rows.
   - Tags are normalized by trimming whitespace.
   - Empty tags are ignored.
   - Duplicate tags are removed.

   Operation mode:

   - `追加标签` (default)
   - `移除标签`
   - `替换为这些标签`

2. **键值标签**

   Uses a small key/value editor:

   - Key input supports schema-derived suggestions from `labels_schema`.
   - Value input is text in the first iteration.
   - Repeated keys in the editor are rejected before submit.

   Each row has an operation:

   - `设置`
   - `清除`

3. **Preview**

   The preview does not need to diff every selected device in the first iteration. It should show the exact operations that will be sent:

   - `追加短标签：core, hx-mm`
   - `移除短标签：legacy`
   - `设置标签：env=prod`
   - `清除标签：owner`

Footer:

- `取消`
- `确认打标签`

### Result Feedback

After submit:

- If all succeeded, show success toast and reload the device list.
- If some failed, show a result modal or alert with:
  - total count
  - success count
  - failed count
  - failed device code and message

The result should not hide partial failure behind a generic toast.

## API Design

Add a new endpoint:

`POST /device/v2/batch-labels`

Request:

```json
{
  "codes": ["DVC001", "DVC002"],
  "group_tag_action": {
    "mode": "append",
    "tags": ["core", "hx-mm"]
  },
  "label_actions": [
    {
      "op": "set",
      "key": "env",
      "value": "prod"
    },
    {
      "op": "unset",
      "key": "owner"
    }
  ]
}
```

Allowed `group_tag_action.mode`:

- `append`
- `remove`
- `replace`

Allowed `label_actions[].op`:

- `set`
- `unset`

Response:

```json
{
  "total": 2,
  "success": 2,
  "failed": 0,
  "items": [
    {
      "code": "DVC001",
      "success": true
    },
    {
      "code": "DVC002",
      "success": true
    }
  ]
}
```

Failure item shape:

```json
{
  "code": "DVC003",
  "success": false,
  "message": "设备不存在"
}
```

## Backend Semantics

For each device:

1. Load the current Device V2 entity by code.
2. Clone current `labels` and `group_tags`.
3. Apply `group_tag_action` if present.
4. Apply each `label_actions` item.
5. Reuse existing schema validation for labels.
6. Persist through the same service update path used by normal Device V2 update.
7. Record per-device success/failure.

Partial success is allowed. A failure on one device must not stop the whole batch unless the request itself is invalid.

Request-level validation failures:

- `codes` is empty.
- Too many codes in one request.
- Tag/action payload is empty.
- Label key is invalid.
- `set` action has an empty value.
- Duplicate label actions for the same key.
- Unsupported action mode or op.

Suggested first limit:

- Up to 200 device codes per request.

## Frontend Data Flow

1. User selects rows or opens row action.
2. Page opens tagging editor with target codes.
3. Editor builds a request payload from short-tag and key-value sections.
4. Frontend validates empty/duplicate inputs before submit.
5. Frontend calls `batchUpdateDeviceV2LabelsReq`.
6. Backend returns per-device results.
7. Frontend shows summary and reloads list/grouping data.

Reload behavior:

- Reload device list after any success.
- Refresh grouping tree if grouping levels include labels or if short tags become a grouping source later.

## Search and Grouping Compatibility

Structured `labels` are already part of flexible search. After tagging, operators should be able to filter by:

- `标签 env = prod`
- `标签 owner 存在`

`group_tags` are not currently first-class structured filters. In this iteration, they are for human grouping/annotation and should be displayed in detail/edit contexts. If operators need to search `group_tags`, add a later structured filter source or a dedicated root field.

## Display Improvements

To make tagging discoverable, add a compact tag summary in one of these places:

Recommended first iteration:

- Show tags in the device detail drawer under a "标签" section.
- Keep the main table unchanged to avoid visual crowding.

Optional later:

- Add a hidden-by-default or configurable table column for tags.
- Add active tag chips to selected rows only when horizontal space allows.

## Error Handling

Frontend:

- Disable submit if no target devices.
- Disable submit if no operations were configured.
- Warn on duplicate label keys.
- Warn on empty label key/value.
- Show partial failure details.

Backend:

- Validate request shape before processing devices.
- Validate label schema during each device update.
- Return per-device errors for missing devices, validation failures, or persistence failures.
- Do not report success for a device whose labels were not saved.

## Testing

Backend tests:

- Batch append short tags.
- Batch remove short tags.
- Batch replace short tags.
- Set and unset key-value labels.
- Reject duplicate label actions.
- Reject invalid label keys.
- Return partial failure when one code is missing.
- Preserve existing attributes, metadata, status, and platform fields.

Frontend Playwright tests:

- Selected devices can open the tagging editor.
- Append a short tag and verify it persists through detail/edit retrieval.
- Set a key-value label and verify it appears in flexible search.
- Remove/unset operations update the device.
- Partial failure result is shown when one selected code no longer exists.

## Open Decisions

The design makes these assumptions:

- First implementation is selected-device scoped, not "all filtered results".
- Batch size limit starts at 200 codes.
- `group_tags` remain lightweight annotations, while `labels` remain searchable structured labels.
- Main table does not add a tags column in the first pass.

These can be changed before implementation if the desired workflow is broader.
