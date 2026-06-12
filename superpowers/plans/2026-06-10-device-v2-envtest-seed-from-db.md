# Device V2 Envtest Seed-From-DB Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `seed-from-db` command that reads `external_request_log` store requests from MySQL and generates envtest cases, a suite, and a seed report without reusing original request IDs.

**Architecture:** Extend the existing CLI with a second subcommand, add one focused module for reading and transforming DB rows into seed cases, and keep file generation isolated from query logic. Request IDs must be regenerated from the source request ID plus current time so generated runs do not collide with historical records.

**Tech Stack:** Python 3.12, standard library, existing `PyYAML`, existing unittest test suite

---

### Task 1: Add parsing and generation tests

**Files:**
- Modify: `OneOps/tools/device_v2_envtest/tests/test_case_loader.py`
- Create: `OneOps/tools/device_v2_envtest/tests/test_seed_from_db.py`
- Test: `OneOps/tools/device_v2_envtest/tests/test_seed_from_db.py`

- [ ] **Step 1: Write the failing test**

```python
def test_build_seed_case_regenerates_request_id():
    row = {
        "request_id": "zb-old-1",
        "params": '{"ext_sys":"zb","resource":"store","params":[{"device_code":"AST-1","device_name":"demo","in_band_ip":"192.0.2.10"}]}',
    }
    case = build_seed_case(row, now=1700000000)
    assert case["request"]["request_id"] != "zb-old-1"
    assert case["request"]["request_id"].startswith("zb-old-1-replay-")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd OneOps/tools/device_v2_envtest && python3 -m unittest tests.test_seed_from_db -v`
Expected: FAIL because `build_seed_case` and the seed module do not exist yet

- [ ] **Step 3: Write minimal implementation**

Create a seed module with:

```python
def build_seed_case(row: dict, now: int) -> dict:
    ...
```

and return a dict that contains a regenerated `request_id`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd OneOps/tools/device_v2_envtest && python3 -m unittest tests.test_seed_from_db -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add OneOps/tools/device_v2_envtest/tests/test_seed_from_db.py OneOps/tools/device_v2_envtest/device_v2_envtest/seed_from_db.py
git commit -m "test: add seed-from-db generation coverage"
```

### Task 2: Add CLI and file output support

**Files:**
- Modify: `OneOps/tools/device_v2_envtest/device_v2_envtest/cli.py`
- Modify: `OneOps/tools/device_v2_envtest/device_v2_envtest/models.py`
- Create: `OneOps/tools/device_v2_envtest/device_v2_envtest/seed_from_db.py`
- Test: `OneOps/tools/device_v2_envtest/tests/test_seed_from_db.py`

- [ ] **Step 1: Write the failing test**

```python
def test_generate_seed_files_writes_cases_suite_and_report(tmp_path):
    rows = [...]
    result = generate_seed_files(rows, tmp_path, ext_sys="zb", now=1700000000)
    assert (tmp_path / "cases").exists()
    assert (tmp_path / "suites" / "from-db.yaml").exists()
    assert (tmp_path / "seed_report.json").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd OneOps/tools/device_v2_envtest && python3 -m unittest tests.test_seed_from_db -v`
Expected: FAIL because `generate_seed_files` does not exist yet

- [ ] **Step 3: Write minimal implementation**

Add:

```python
def generate_seed_files(rows: list[dict], output_dir: Path, ext_sys: str, now: int) -> dict:
    ...
```

and wire a `seed-from-db` parser branch in `cli.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd OneOps/tools/device_v2_envtest && python3 -m unittest tests.test_seed_from_db -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add OneOps/tools/device_v2_envtest/device_v2_envtest/cli.py OneOps/tools/device_v2_envtest/device_v2_envtest/seed_from_db.py OneOps/tools/device_v2_envtest/tests/test_seed_from_db.py
git commit -m "feat: add envtest seed-from-db command"
```

### Task 3: Add DB query integration and verify end-to-end

**Files:**
- Modify: `OneOps/tools/device_v2_envtest/device_v2_envtest/probes/mysql_probe.py`
- Modify: `OneOps/tools/device_v2_envtest/tests/test_seed_from_db.py`
- Modify: `OneOps/tools/device_v2_envtest/README.md`
- Test: `OneOps/tools/device_v2_envtest/tests/test_seed_from_db.py`

- [ ] **Step 1: Write the failing test**

```python
def test_fetch_seed_rows_queries_store_requests_only():
    probe = FakeSeedRowsProbe(...)
    rows = probe.fetch_seed_rows(...)
    assert rows[0]["resource"] == "store"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd OneOps/tools/device_v2_envtest && python3 -m unittest tests.test_seed_from_db -v`
Expected: FAIL because `fetch_seed_rows` does not exist

- [ ] **Step 3: Write minimal implementation**

Add:

```python
def fetch_seed_rows(self, env: EnvConfig, *, ext_sys: str, status: str, limit: int) -> list[dict[str, str]]:
    ...
```

and document the command in `README.md`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd OneOps/tools/device_v2_envtest && python3 -m unittest tests.test_seed_from_db -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add OneOps/tools/device_v2_envtest/device_v2_envtest/probes/mysql_probe.py OneOps/tools/device_v2_envtest/tests/test_seed_from_db.py OneOps/tools/device_v2_envtest/README.md
git commit -m "docs: document envtest seed-from-db workflow"
```

### Task 4: Full verification

**Files:**
- Modify: `docs/superpowers/plans/2026-06-10-device-v2-envtest-seed-from-db.md`
- Test: `OneOps/tools/device_v2_envtest/tests/test_case_loader.py`
- Test: `OneOps/tools/device_v2_envtest/tests/test_runner.py`
- Test: `OneOps/tools/device_v2_envtest/tests/test_seed_from_db.py`

- [ ] **Step 1: Run targeted tests**

Run: `cd OneOps/tools/device_v2_envtest && python3 -m unittest tests.test_seed_from_db -v`
Expected: PASS

- [ ] **Step 2: Run the full envtest suite**

Run: `cd OneOps/tools/device_v2_envtest && python3 -m unittest discover -s tests -v`
Expected: PASS

- [ ] **Step 3: Smoke the CLI help**

Run: `cd OneOps/tools/device_v2_envtest && python3 -m device_v2_envtest.cli --help`
Expected: output includes `seed-from-db`

- [ ] **Step 4: Commit**

```bash
git add OneOps/tools/device_v2_envtest
git commit -m "chore: verify envtest seed-from-db flow"
```
