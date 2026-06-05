# Quick Env Automation Runtime Kit Design

## Objective

为 quick_env 增加一套可拷贝到 controller / agent 服务器执行的自动化运行时准备包，用于测试 OneOps 平台对 Ansible、Terraform、OpenTofu、Terragrunt 等任务类型的执行能力。

quick_env 本身只负责拉起 OneOps 依赖服务和生成准备包，不假设 Ansible / Terraform 等 CLI 安装在 quick_env 所在服务器上。真正的运行时依赖准备和验证发生在部署 controller / agent 的目标服务器上。

## Problem

当前 quick_env 已经内置任务中心示例仓库和 smoke 脚本，但自动化 CLI 依赖没有纳入 quick_env 的交付链路：

- controller / agent 任务执行侧会调用 `ansible-playbook`、`terraform`、`tofu`、`terragrunt`。
- quick_env 启动服务器通常不是最终执行任务的 controller / agent 服务器。
- 部署现场可能是 Linux kernel 3.10、4.19 或更新内核，OS、glibc、Python、OpenSSL、包管理器能力差异很大。
- 现场人员更适合手动拷贝脚本包到目标服务器执行，而不是由 quick_env 远程 SSH 登录目标服务器。

因此设计目标不是让 quick_env 机器变成 automation runner，而是让 quick_env 产出可重复、可诊断、适配新旧环境的 runtime kit。

## Recommended Approach

新增 quick_env automation runtime kit 生成流程：

```text
quick_env/.runtime/<instance>/automation-runtime-kit/
  README.md
  preflight.sh
  install-task-runtime-prereqs.sh
  smoke-task-center.sh
  source-repo/
  packages/
```

现场人员将 `automation-runtime-kit` 拷贝到 controller 或 agent 目标服务器后执行：

```bash
bash preflight.sh --role agent
bash install-task-runtime-prereqs.sh --role agent --install-tofu --install-terragrunt
bash smoke-task-center.sh --role agent
```

controller 目标服务器执行：

```bash
bash preflight.sh --role controller
bash install-task-runtime-prereqs.sh --role controller --install-tofu --install-terragrunt
bash smoke-task-center.sh --role controller
```

`preflight.sh` 和 `smoke-task-center.sh` 只检查目标服务器本地状态。它们不会 SSH 到其它机器，也不会修改 quick_env 的运行状态。

## Role Boundaries

quick_env 服务器：

- 启动 OneOps 依赖服务。
- 启动本地 Gitea 并导入任务中心示例仓库。
- 根据实例渲染 `automation-runtime-kit`。
- 在 README 中写明 Gitea URL、示例 repo、推荐 controller / agent 工作目录。
- 可选执行本机 local smoke，但本机 smoke 只证明示例仓库可用，不代表 controller / agent 目标机可用。

controller 服务器：

- 需要具备 `git`、`ssh`、对应任务 CLI，以及 controller 任务工作目录权限。
- 默认 controller 工作目录为 `/tmp/ctrlhub/repos`。
- 执行平台本地任务或作为任务分发控制面时，应通过 preflight 和 smoke。

agent 服务器：

- 需要具备 `git`、`ssh`、对应任务 CLI，以及 agent 任务工作目录和上传目录权限。
- 默认 agent 工作目录为 `$HOME/app/agent`。
- 默认 agent 上传目录为 `/tmp/agent/uploads`。
- 当 OneOps 任务设置 `run_on_agent=true` 时，最终依赖检查以 agent 服务器为准。

## Kit Contents

### `preflight.sh`

负责只读诊断，输出清晰的 PASS / WARN / FAIL 报告。

检查项：

- OS：读取 `/etc/os-release`。
- kernel：读取 `uname -r`，识别 3.10、4.19、更新内核。
- 架构：支持 `x86_64` / `amd64`、`aarch64` / `arm64`。
- glibc：通过 `getconf GNU_LIBC_VERSION` 或 `ldd --version` 探测。
- Python：检查 `python3`，要求 Python 3.6+。
- OpenSSL：输出版本，用于排查 Python / Ansible TLS 问题。
- 包管理器：识别 `apt-get`、`dnf`、`yum`。
- 基础命令：`bash`、`sh`、`curl` 或 `wget`、`unzip`、`git`、`ssh`。
- 自动化 CLI：`ansible-playbook`、`terraform`、可选 `tofu`、可选 `terragrunt`。
- 工作目录权限：按 `--role` 检查 controller / agent 默认目录是否可创建、可写、可删除测试文件。
- Gitea 连通性：如 README 或环境变量提供 quick_env Gitea URL，则检查 HTTP 可达。

结果分级：

- `FAIL`：缺少必需命令、工作目录不可写、架构不支持、Python 低于 3.6。
- `WARN`：kernel 3.10、glibc 较旧、OpenSSL 较旧、缺少可选工具、无法访问 quick_env Gitea。
- `PASS`：满足目标角色的基础要求。

kernel 策略：

- kernel 3.10：不直接判失败，但报告为 legacy kernel，并提示优先使用系统包管理器或随 kit 附带的兼容二进制。
- kernel 4.19：报告为 stable legacy，继续检查 glibc、Python、OpenSSL。
- 更新内核：报告为 modern kernel，仍以 CLI 是否可执行为准。

### `install-task-runtime-prereqs.sh`

复用并迁移现有 `/OneOPS/install-task-runtime-prereqs.sh` 的能力，放入 kit 中作为目标机安装入口。

保留能力：

- `--role <controller|agent|both>`
- `--controller-workspace <path>`
- `--agent-workspace <path>`
- `--agent-upload-dir <path>`
- `--install-tofu`
- `--install-terragrunt`
- `--skip-terraform`
- `--terraform-version <version>`
- `--tofu-version <version>`
- `--terragrunt-version <version>`

增强要求：

- 优先使用 `packages/` 内的离线包。
- 离线包缺失时再使用公网下载 URL。
- 安装前输出目标 OS、kernel、arch、glibc。
- 安装后自动调用轻量版 preflight。
- 不静默覆盖已有 CLI；如果目标命令已存在，输出路径和版本后跳过。

### `smoke-task-center.sh`

负责验证目标服务器能执行任务中心核心示例。

默认 smoke：

- `shell/hello-world`
- `shell/with-args`
- `ansible/hello-world`
- `terraform/basic-output`

可选 smoke：

- `tofu/basic-output`
- `terragrunt/basic-stack`

执行策略：

- 使用 kit 内置的 `source-repo/`，不依赖目标机能从 Gitea clone。
- Terraform family 使用临时 `TF_DATA_DIR`、`TF_PLUGIN_CACHE_DIR`、`TG_DOWNLOAD_DIR`，避免污染目标机全局目录。
- smoke 默认只执行 `init -backend=false`、`plan` 或本地输出，不创建真实云资源。
- 若用户显式传 `--repo-url`，可额外验证目标机能从 quick_env Gitea clone 示例仓库。

## Quick Env Integration

新增 quick_env 管理命令：

```bash
./manage.sh runtime-kit --instance demo-a
```

行为：

1. 加载 `quick_env/.runtime/<instance>/.instance.env.sh`。
2. 创建或刷新 `quick_env/.runtime/<instance>/automation-runtime-kit`。
3. 复制安装脚本、preflight 脚本、smoke 脚本。
4. 复制 `quick_env/init-configs/gitea/source-repo/` 到 kit 的 `source-repo/`。
5. 渲染 README，写入当前实例的 Gitea 地址、repo clone URL、controller / agent 推荐命令。

README 中明确说明：

- 拷贝整个 `automation-runtime-kit` 到目标服务器。
- 在 controller 服务器使用 `--role controller`。
- 在 agent 服务器使用 `--role agent`。
- 若任务最终在 agent 执行，以 agent 服务器 smoke 结果为准。
- quick_env 本机 smoke 不代表远端目标机可用。

## Error Handling

- preflight 不做破坏性操作，只创建并删除临时探测文件。
- install 脚本遇到不支持 OS、架构、包管理器时立即失败，并保留可读错误。
- smoke 失败时保留临时日志目录路径。
- Terraform family smoke 使用隔离 cache 和 data dir，失败时报告具体 CLI、工作目录、命令参数。
- Ansible smoke 只使用 `localhost ansible_connection=local`，避免误连远端资产。

## Compatibility Policy

兼容性判断按能力而不是只按 kernel 版本：

- kernel 是提示维度。
- glibc 决定二进制可运行风险。
- Python / OpenSSL 决定 Ansible 和 TLS 风险。
- 包管理器决定在线安装路径。
- `packages/` 离线包决定无公网现场能否完成安装。

预期输出示例：

```text
[PASS] role: agent
[WARN] kernel: 3.10.0 legacy kernel, continue with capability checks
[PASS] arch: amd64
[PASS] python3: 3.6.8
[WARN] glibc: 2.17, use compatible terraform package when possible
[FAIL] ansible-playbook: missing
[PASS] terraform: /usr/local/bin/terraform 1.9.8
[PASS] workspace: /home/oneops/app/agent writable
```

## Acceptance Criteria

- `./manage.sh runtime-kit --instance <name>` 生成完整 kit。
- kit 可被手动拷贝到 controller / agent 服务器独立执行。
- `preflight.sh --role controller` 能报告 controller 目标机依赖和目录权限。
- `preflight.sh --role agent` 能报告 agent 目标机依赖和目录权限。
- `install-task-runtime-prereqs.sh` 能在目标机安装或复用 Ansible / Terraform / OpenTofu / Terragrunt。
- `smoke-task-center.sh` 能在目标机使用 kit 内置示例跑通 shell、ansible、terraform 基础 smoke。
- README 明确 quick_env、本机 smoke、controller 目标机、agent 目标机之间的边界。
- 老内核环境不会仅因 kernel 3.10 失败，但会给出 legacy 风险提示。

## Out of Scope

- 不让 quick_env 通过 SSH 自动登录 controller / agent 服务器。
- 不改变 controller / agent 当前直接调用本机 CLI 的执行模型。
- 不引入容器化 automation runner。
- 不在 smoke 中创建真实云资源。
- 不处理具体业务凭据、云账号或网络设备账号配置。
