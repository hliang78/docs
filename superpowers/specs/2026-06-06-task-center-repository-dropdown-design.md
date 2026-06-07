# Task Center Repository Dropdown Design

## Goal

The task creation modal should let operators select repository and playbook/script paths from dropdowns instead of manually typing URL, branch, and path fields.

## Scope

This change is limited to the task center create modal in `OneOps-UI`. It does not change the task creation API payload. The UI will continue submitting `repo_url`, `repo_branch`, and `playbook_path`.

## Design

When repository source is `自定义仓库`, the main form shows a repository dropdown sourced from repository records and any known runtime repository records. Selecting a repository fills `repo_url` and `repo_branch`; if there are no dropdown options, the form falls back to the existing URL input.

Task template catalog data must not store deployment-specific repository addresses. Template catalog entries keep `playbook_path` and branch-like metadata only; the actual repository address comes from the environment-specific repository record.

When a repository is selected and a path field is visible, the path field becomes a searchable dropdown. It loads repository files from the existing Script Studio repository-files API using the selected repository, branch, app type, Git credential, and project. Selecting an item fills `playbook_path`.

If file loading fails, the path field falls back to the existing text input and shows a short hint. This keeps task creation usable when the repository browser API is unavailable.

## Testing

Add a small smoke test for the option-builder helper:

- repository records deduplicate by URL and branch;
- default example repository sorts first;
- the UI can decide to fall back to manual path input after a file-list error.
