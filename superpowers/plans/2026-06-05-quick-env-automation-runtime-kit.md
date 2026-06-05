# Quick Env Automation Runtime Kit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a quick_env command that generates a manually copyable automation runtime kit for controller and agent target servers.

**Architecture:** Add a Python 3.6-compatible kit builder under `quick_env/scripts/`, shell templates under `quick_env/templates/automation-runtime-kit/`, and a `manage.sh runtime-kit` entry point. Tests verify builder output, rendered README content, executable scripts, and Python 3.6 compatibility.

**Tech Stack:** Bash, Python 3.6-compatible stdlib, unittest, existing quick_env shell tests.

---

### Task 1: Builder Test

**Files:**
- Create: `quick_env/tests/test_runtime_kit_builder.py`
- Create later: `quick_env/scripts/build_runtime_kit.py`

- [ ] **Step 1: Write the failing builder test**

```python
def test_build_runtime_kit_creates_copyable_target_server_bundle(self):
    runtime_dir = Path(self.temp_dir) / "runtime"
    runtime_dir.mkdir()
    (runtime_dir / ".instance.env.sh").write_text(
        "\n".join([
            "export INSTANCE_NAME='demo-a'",
            "export ONEOPS_INFRA_HOST='192.0.2.10'",
            "export ONEOPS_GITEA_PORT='3104'",
        ]) + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_runtime_kit.py"),
            "--quick-env-root",
            str(ROOT),
            "--runtime-dir",
            str(runtime_dir),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    self.assertEqual(completed.returncode, 0, completed.stderr)
    kit = runtime_dir / "automation-runtime-kit"
    self.assertTrue((kit / "README.md").is_file())
    self.assertTrue((kit / "preflight.sh").is_file())
    self.assertTrue((kit / "install-task-runtime-prereqs.sh").is_file())
    self.assertTrue((kit / "smoke-task-center.sh").is_file())
    self.assertTrue((kit / "source-repo" / "run-local-smoke.sh").is_file())
    self.assertTrue((kit / "packages").is_dir())
    self.assertIn("http://192.0.2.10:3104/netxops/task-center-example-scripts.git", (kit / "README.md").read_text(encoding="utf-8"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 quick_env/tests/test_runtime_kit_builder.py -v`
Expected: FAIL because `quick_env/scripts/build_runtime_kit.py` does not exist.

### Task 2: Builder Implementation

**Files:**
- Create: `quick_env/scripts/build_runtime_kit.py`
- Create: `quick_env/templates/automation-runtime-kit/README.md.template`
- Create: `quick_env/templates/automation-runtime-kit/preflight.sh`
- Create: `quick_env/templates/automation-runtime-kit/smoke-task-center.sh`
- Copy source: `/OneOPS/install-task-runtime-prereqs.sh`
- Test: `quick_env/tests/test_runtime_kit_builder.py`

- [ ] **Step 1: Implement Python builder**

Implement these functions in `build_runtime_kit.py`:

```python
def parse_shell_env(path):
    ...

def render_text(content, replacements):
    ...

def copy_tree(src, dst):
    ...

def build_runtime_kit(quick_env_root, runtime_dir):
    ...
```

The builder must create `automation-runtime-kit`, render README variables, copy scripts, copy `init-configs/gitea/source-repo`, copy `/OneOPS/install-task-runtime-prereqs.sh` or a quick_env-local equivalent, create `packages`, chmod shell scripts executable, and print the kit path.

- [ ] **Step 2: Implement kit shell templates**

Create `preflight.sh` with `--role`, `--gitea-url`, `--controller-workspace`, `--agent-workspace`, `--agent-upload-dir`, and `--help`. It must print PASS / WARN / FAIL lines and exit nonzero when required checks fail.

Create `smoke-task-center.sh` with `--role`, `--with-tofu`, `--with-terragrunt`, `--repo-url`, and `--help`. It must run source-repo smoke subsets from the kit and use isolated Terraform family cache directories.

- [ ] **Step 3: Run builder test**

Run: `python3 quick_env/tests/test_runtime_kit_builder.py -v`
Expected: PASS.

### Task 3: Manage Command

**Files:**
- Modify: `quick_env/manage.sh`
- Test: `quick_env/tests/test_runtime_kit_builder.py`

- [ ] **Step 1: Add manage test for command help**

Add a test that runs `bash quick_env/manage.sh --help` and asserts `runtime-kit` is present.

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 quick_env/tests/test_runtime_kit_builder.py -v`
Expected: FAIL because help does not mention `runtime-kit`.

- [ ] **Step 3: Implement manage command**

Update `usage`, command validation, and main dispatch. `runtime-kit` should load the instance and execute:

```bash
"${PYTHON_CMD}" "${QUICK_ENV_ROOT}/scripts/build_runtime_kit.py" \
  --quick-env-root "${QUICK_ENV_ROOT}" \
  --runtime-dir "${RUNTIME_DIR}"
```

- [ ] **Step 4: Run manage test**

Run: `python3 quick_env/tests/test_runtime_kit_builder.py -v`
Expected: PASS.

### Task 4: Compatibility And Integration Verification

**Files:**
- Modify: `quick_env/tests/test_python36_compat.py`
- Modify: `quick_env/README.md`

- [ ] **Step 1: Add build script to Python 3.6 compatibility test**

Add `ROOT / "scripts" / "build_runtime_kit.py"` to `FILES`.

- [ ] **Step 2: Document runtime-kit in README**

Add a short section explaining `./manage.sh runtime-kit --instance <name>` and manual copy to controller / agent target servers.

- [ ] **Step 3: Run verification**

Run:

```bash
bash quick_env/tests/test_runtime_helpers.sh
bash quick_env/tests/test_validate_python_resolution.sh
python3 quick_env/tests/test_python36_compat.py -v
python3 quick_env/tests/test_runtime_kit_builder.py -v
```

Expected: all commands exit 0.
