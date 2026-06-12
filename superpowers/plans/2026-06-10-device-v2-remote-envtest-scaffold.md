# Device V2 Remote Envtest Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first runnable Python CLI scaffold for the remote Device V2 environment test pack so it can load environment and suite YAML, execute a minimal OneOps API + MySQL evidence flow, and emit JSON/Markdown/HTML reports.

**Architecture:** Keep the test pack isolated under `OneOps/tools/device_v2_envtest`, with small modules for models, YAML loading, probes, orchestration, artifact writing, and report rendering. The first version stays intentionally small: one CLI command, a generic request submitter, a generic MySQL evidence collector, simple result classification, and fixture-free `unittest` coverage.

**Tech Stack:** Python 3.12, stdlib `argparse`/`dataclasses`/`json`/`subprocess`/`urllib`, PyYAML, `unittest`

---

### Task 1: Create failing tests for the scaffold contract

**Files:**
- Create: `OneOps/tools/device_v2_envtest/tests/test_case_loader.py`
- Create: `OneOps/tools/device_v2_envtest/tests/test_runner.py`
- Create: `OneOps/tools/device_v2_envtest/tests/test_reporters.py`

- [ ] **Step 1: Write the failing loader test**

```python
import tempfile
import textwrap
import unittest
from pathlib import Path

from device_v2_envtest.case_loader import load_env_config, load_suite


class CaseLoaderTest(unittest.TestCase):
    def test_load_env_and_suite_with_case_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "cases").mkdir()
            (root / "cases" / "ic_01.yaml").write_text(
                textwrap.dedent(
                    """
                    id: IC-01
                    title: Linux SSH baseline
                    request:
                      request_id: zb-case-01
                      body:
                        hello: world
                    expect:
                      allow_expected_runtime_error: false
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            (root / "env.yaml").write_text(
                textwrap.dedent(
                    """
                    name: lab-a
                    oneops:
                      base_url: http://127.0.0.1:20060
                    mysql:
                      host: 127.0.0.1
                      port: 20058
                      database: UniOPS
                      username: UniOPS
                      password: secret
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            (root / "suite.yaml").write_text(
                textwrap.dedent(
                    """
                    name: baseline
                    cases:
                      - cases/ic_01.yaml
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            env = load_env_config(root / "env.yaml")
            suite = load_suite(root / "suite.yaml")

            self.assertEqual(env.name, "lab-a")
            self.assertEqual(env.oneops.base_url, "http://127.0.0.1:20060")
            self.assertEqual(len(suite.cases), 1)
            self.assertEqual(suite.cases[0].id, "IC-01")
            self.assertEqual(suite.cases[0].request.request_id, "zb-case-01")
```

- [ ] **Step 2: Run the loader test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps/tools/device_v2_envtest && python3 -m unittest tests.test_case_loader -v
```

Expected: FAIL with `ModuleNotFoundError` or missing loader symbols because the scaffold does not exist yet.

- [ ] **Step 3: Write the failing runner classification test**

```python
import tempfile
import unittest
from pathlib import Path

from device_v2_envtest.models import (
    CaseExpect,
    EnvConfig,
    MySQLConfig,
    OneOpsConfig,
    RequestConfig,
    SuiteCase,
)
from device_v2_envtest.runner import EnvTestRunner


class FakeOneOpsProbe:
    def submit(self, env, case):
        return {"status_code": 200, "body": {"ok": True}}


class FakeMySQLProbe:
    def fetch_request_log(self, env, request_id):
        return {"request_id": request_id, "status": "Success"}

    def fetch_pipeline_task(self, env, request_id):
        return {"task_id": "entv2_1", "overall_status": "partial"}


class RunnerTest(unittest.TestCase):
    def test_expected_runtime_error_maps_to_pass_with_expected_runtime_error(self) -> None:
        env = EnvConfig(
            name="lab",
            oneops=OneOpsConfig(base_url="http://127.0.0.1:20060"),
            mysql=MySQLConfig(
                host="127.0.0.1",
                port=20058,
                database="UniOPS",
                username="UniOPS",
                password="secret",
            ),
        )
        case = SuiteCase(
            id="IC-08",
            title="OOB IPMI shadow target",
            source_path="cases/ic_08.yaml",
            request=RequestConfig(request_id="zb-ic08", body={"x": 1}),
            expect=CaseExpect(allow_expected_runtime_error=True),
        )
        with tempfile.TemporaryDirectory() as tmp:
            runner = EnvTestRunner(
                oneops_probe=FakeOneOpsProbe(),
                mysql_probe=FakeMySQLProbe(),
                output_root=Path(tmp),
            )
            result = runner.run_case(env, case)

        self.assertEqual(result.final_result, "pass_with_expected_runtime_error")
        self.assertEqual(result.platform_acceptance, "pass")
        self.assertEqual(result.runtime_acceptance, "expected_error")
```

- [ ] **Step 4: Run the runner test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps/tools/device_v2_envtest && python3 -m unittest tests.test_runner -v
```

Expected: FAIL because the runner and models do not exist yet.

- [ ] **Step 5: Write the failing report generation test**

```python
import json
import tempfile
import unittest
from pathlib import Path

from device_v2_envtest.models import CaseResult
from device_v2_envtest.reporters.json_report import write_json_report
from device_v2_envtest.reporters.markdown_report import write_markdown_report


class ReporterTest(unittest.TestCase):
    def test_json_and_markdown_reports_are_written(self) -> None:
        result = CaseResult(
            case_id="IC-01",
            title="Linux SSH baseline",
            request_id="zb-1",
            platform_acceptance="pass",
            runtime_acceptance="pass",
            final_result="pass",
            reason="ok",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            json_path = write_json_report(root, [result])
            md_path = write_markdown_report(root, [result])

            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["total"], 1)
            self.assertIn("IC-01", md_path.read_text(encoding="utf-8"))
```

- [ ] **Step 6: Run the reporter test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps/tools/device_v2_envtest && python3 -m unittest tests.test_reporters -v
```

Expected: FAIL because the reporter modules do not exist yet.

### Task 2: Implement the minimal scaffold to satisfy the tests

**Files:**
- Create: `OneOps/tools/device_v2_envtest/README.md`
- Create: `OneOps/tools/device_v2_envtest/pyproject.toml`
- Create: `OneOps/tools/device_v2_envtest/configs/env.example.yaml`
- Create: `OneOps/tools/device_v2_envtest/configs/suites/baseline.yaml`
- Create: `OneOps/tools/device_v2_envtest/cases/ic_01_linux_ssh.yaml`
- Create: `OneOps/tools/device_v2_envtest/device_v2_envtest/__init__.py`
- Create: `OneOps/tools/device_v2_envtest/device_v2_envtest/models.py`
- Create: `OneOps/tools/device_v2_envtest/device_v2_envtest/case_loader.py`
- Create: `OneOps/tools/device_v2_envtest/device_v2_envtest/artifacts.py`
- Create: `OneOps/tools/device_v2_envtest/device_v2_envtest/probes/oneops_api.py`
- Create: `OneOps/tools/device_v2_envtest/device_v2_envtest/probes/mysql_probe.py`
- Create: `OneOps/tools/device_v2_envtest/device_v2_envtest/reporters/json_report.py`
- Create: `OneOps/tools/device_v2_envtest/device_v2_envtest/reporters/markdown_report.py`
- Create: `OneOps/tools/device_v2_envtest/device_v2_envtest/reporters/html_report.py`
- Create: `OneOps/tools/device_v2_envtest/device_v2_envtest/runner.py`
- Create: `OneOps/tools/device_v2_envtest/device_v2_envtest/cli.py`

- [ ] **Step 1: Implement the typed models**

Key requirements:

```python
@dataclass(slots=True)
class OneOpsConfig:
    base_url: str
    submit_path: str = "/api/v1/external-request/zb/device-v2/store"
    method: str = "POST"
    timeout_seconds: int = 30
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class MySQLConfig:
    host: str
    port: int
    database: str
    username: str
    password: str
    mysql_bin: str = "mysql"


@dataclass(slots=True)
class RequestConfig:
    request_id: str
    headers: dict[str, str] = field(default_factory=dict)
    body: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CaseExpect:
    allow_expected_runtime_error: bool = False


@dataclass(slots=True)
class CaseResult:
    case_id: str
    title: str
    request_id: str
    platform_acceptance: str
    runtime_acceptance: str
    final_result: str
    reason: str
    request_log: dict[str, Any] | None = None
    pipeline_task: dict[str, Any] | None = None
```

- [ ] **Step 2: Implement YAML loading**

Requirements:

```python
def load_env_config(path: Path) -> EnvConfig: ...
def load_suite(path: Path) -> SuiteConfig: ...
```

Behavior:
- Read YAML via `yaml.safe_load`
- Resolve suite case paths relative to the suite file
- Convert to typed dataclasses

- [ ] **Step 3: Implement OneOps API probe**

Requirements:

```python
class OneOpsAPIProbe:
    def submit(self, env: EnvConfig, case: SuiteCase) -> dict[str, Any]:
        ...
```

Behavior:
- Compose URL from `base_url + submit_path`
- Merge default headers, case headers, and `RequestID`
- POST JSON body with stdlib `urllib.request`
- Return `status_code`, `body`, and `response_headers`

- [ ] **Step 4: Implement MySQL evidence probe**

Requirements:

```python
class MySQLProbe:
    def fetch_request_log(self, env: EnvConfig, request_id: str) -> dict[str, Any] | None:
        ...

    def fetch_pipeline_task(self, env: EnvConfig, request_id: str) -> dict[str, Any] | None:
        ...
```

Behavior:
- Use `subprocess.run` with `mysql -N -B -e`
- Issue generic SQL for `external_request_log`
- Issue generic SQL for `entity_pipeline_task` by `options LIKE '%"request_id":"...%'`
- Return dictionaries or `None`

- [ ] **Step 5: Implement runner and classification**

Requirements:

```python
class EnvTestRunner:
    def run_case(self, env: EnvConfig, case: SuiteCase) -> CaseResult:
        ...
```

Classification rules:
- If request log exists and pipeline task exists:
  - `allow_expected_runtime_error=True` => `platform_acceptance=pass`, `runtime_acceptance=expected_error`, `final_result=pass_with_expected_runtime_error`
  - else => `platform_acceptance=pass`, `runtime_acceptance=pass`, `final_result=pass`
- Else => `final_result=fail`

Also write per-case artifact JSON files.

- [ ] **Step 6: Implement JSON / Markdown / HTML reporters**

Requirements:
- JSON report includes summary counts by `final_result`
- Markdown report includes a summary table
- HTML report can be a simple escaped wrapper around the Markdown content

- [ ] **Step 7: Implement CLI**

Command:

```bash
python3 -m device_v2_envtest.cli run --env configs/env.example.yaml --suite configs/suites/baseline.yaml --output-dir out
```

Behavior:
- Load env + suite
- Run all cases
- Emit report paths

- [ ] **Step 8: Add README and example configs**

README should explain:
- purpose
- required access
- example env file
- example suite file
- example command

### Task 3: Run and verify the scaffold

**Files:**
- Verify only

- [ ] **Step 1: Run all scaffold tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps/tools/device_v2_envtest && python3 -m unittest discover -s tests -v
```

Expected: PASS

- [ ] **Step 2: Run the CLI against example files**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps/tools/device_v2_envtest && python3 -m device_v2_envtest.cli run --env configs/env.example.yaml --suite configs/suites/baseline.yaml --output-dir /tmp/device_v2_envtest_smoke
```

Expected:
- command exits 0
- emits JSON / Markdown / HTML report paths
- if example env is placeholder-only, case results may be `fail`, but report generation must succeed

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-06-10-device-v2-remote-envtest-design.md docs/superpowers/plans/2026-06-10-device-v2-remote-envtest-scaffold.md docs/knowledge/device-v2-ingest-testdata-guide.md OneOps/tools/device_v2_envtest
git commit -m "feat: add device v2 remote envtest scaffold"
```
