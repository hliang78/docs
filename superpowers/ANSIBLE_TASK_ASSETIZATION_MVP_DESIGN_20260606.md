# Ansible 任务资产化 MVP 设计

本文档定义 OneOps 围绕 Ansible 任务资产化的 MVP 方案。

MVP 选择 **网络设备配置备份** 作为第一条打穿主线。目标不是新增一个简单的 Ansible 执行入口，而是把 `network-config-backup` 这类 Playbook 变成 OneOps 可理解、可校验、可治理、可归档、可回写的运维能力资产。

## 1. 背景

OneOps 当前已经具备以下基础：

1. 任务中心支持 `ansible`、`shell`、`terraform`、`tofu`、`terragrunt` 等任务类型。
2. `ExecutionEnvelopeV2` 已经把执行参数拆成 `scope`、`script`、`target`、`repository`、`params`、`runtime`、`credential`。
3. Ansible 任务已经支持 `device_codes` 扇出，并限制该能力只用于 Ansible。
4. 单设备 fanout inventory 已经可以根据设备画像注入 `vendor_family`、`ansible_connection`、`ansible_network_os`、`ansible_command_timeout`。
5. `quick_env` 示例仓库中已经有 `ansible/network-config-backup/site.yml`，并能输出配置文件、summary JSON 和 artifact manifest。

当前主要缺口不在“能否执行 Ansible”，而在于：

1. Playbook 缺少平台级运行契约。
2. 设备选择后的适配检查不够产品化。
3. 执行产物还没有沉淀为配置备份资产。
4. 父子任务结果还缺少面向设备维度的聚合视图。

## 2. MVP 目标

MVP 只打穿一条主线：

```text
选择网络配置备份任务资产
  -> 选择设备
  -> 执行前适配检查
  -> 生成 Ansible inventory
  -> 执行 network-config-backup Playbook
  -> 读取 artifact manifest
  -> 归档 cfg/json 产物
  -> 回写设备配置备份状态
  -> 按设备展示成功/失败/产物
```

MVP 完成后，用户应能回答：

1. 哪些设备可以执行配置备份，哪些不能，原因是什么。
2. 每台设备使用哪个访问平面、哪个地址、哪个凭据引用、哪个 Ansible 连接画像。
3. 每台设备是否备份成功，失败原因是什么。
4. 成功设备的备份文件在哪里，是否可下载，是否敏感。
5. 设备最近一次配置备份状态、时间、任务 ID、配置 hash 是什么。

## 3. MVP 非目标

本期不做：

1. 通用 Ansible 编排器。
2. 所有 Playbook 的资产化治理。
3. 复杂审批流引擎。
4. 自动配置 diff 和漂移告警。
5. 配置变更下发、失败回滚和多步骤场景编排。
6. Terraform/IaC 任务资产化。
7. Script Studio 全量契约生成能力。

这些能力可以在网络配置备份主线稳定后继续扩展。

## 4. 核心概念

### 4.1 Ansible 任务资产

Ansible 任务资产是一个可复用的 Playbook 能力定义。

最小字段：

1. 名称：如“网络配置备份”
2. 类型：`ansible`
3. 入口：`ansible/network-config-backup/site.yml`
4. 仓库：任务脚本仓库 URL 和分支
5. 适用目标：支持的设备类型、厂商族、访问平面
6. 参数契约：可选和必填变量
7. 凭据契约：需要 SSH/API 登录凭据，但禁止写入 inventory 明文
8. 风险契约：只读、可定时、低风险、无需审批
9. 输出契约：配置文件、summary JSON、artifact manifest

### 4.2 Ansible 运行契约

运行契约建议通过 `oneops.contract.json` 表达。MVP 先为 `network-config-backup` 提供一份标准契约。

示例：

```json
{
  "apiVersion": "oneops.runtime/v1",
  "kind": "ansible_task_contract",
  "name": "network-config-backup",
  "script": {
    "type": "ansible",
    "entrypoint": "ansible/network-config-backup/site.yml"
  },
  "target": {
    "device_types": ["switch", "router", "firewall", "load_balancer"],
    "vendor_families": ["cisco_ios", "cisco_nxos", "huawei_ce", "h3c_cli", "f5_bigip"],
    "access_planes": ["in_band", "out_band"],
    "requires_address": true
  },
  "inventory": {
    "required_host_vars": ["ansible_host", "vendor_family"],
    "optional_host_vars": [
      "ansible_connection",
      "ansible_network_os",
      "ansible_ssh_common_args",
      "ansible_command_timeout"
    ],
    "forbidden_host_vars": [
      "ansible_user",
      "ansible_password",
      "ansible_ssh_pass",
      "ansible_become_password",
      "ansible_ssh_private_key_file"
    ]
  },
  "credential": {
    "required": true,
    "source": "credential_ref",
    "forbid_inline_secret": true
  },
  "runtime": {
    "read_only": true,
    "idempotent": true,
    "safe_for_schedule": true,
    "supports_check_mode": false
  },
  "outputs": {
    "artifacts": [
      {
        "path": "network-backups/*.cfg",
        "kind": "text",
        "sensitive": true
      },
      {
        "path": "network-config-backup-*.json",
        "kind": "json",
        "sensitive": false
      }
    ],
    "manifest": "ONEOPS_ARTIFACT_MANIFEST"
  },
  "risk": {
    "level": "low",
    "approval_required": false
  }
}
```

### 4.3 设备适配结果

执行前必须形成设备级适配结果。

状态：

1. `ready`：可执行
2. `blocked`：不可执行
3. `warning`：可执行但有风险提示

阻断原因：

1. 设备不存在或不可读取
2. 缺少访问地址
3. 缺少凭据引用
4. 无法解析 `vendor_family`
5. 解析出的厂商族不在任务契约支持范围
6. 访问平面不支持

### 4.4 配置备份记录

配置备份记录是 Ansible 执行结果回写后的平台资产。

最小字段：

1. `device_code`
2. `task_id`
3. `parent_task_id`
4. `run_id`
5. `vendor_family`
6. `access_plane`
7. `backup_status`
8. `backup_time`
9. `artifact_name`
10. `artifact_storage_key`
11. `artifact_size`
12. `artifact_sha256`
13. `config_hash`
14. `summary_json`
15. `error_message`

MVP 可以先复用现有任务 runtime artifact 能力保存文件，再增加一张轻量索引表或服务层投影，用于设备详情和配置备份列表查询。

## 5. 核心流程

### 5.1 创建任务资产

管理员导入或创建“网络配置备份”任务资产。

绑定内容：

1. `app_type = ansible`
2. `playbook_path = ansible/network-config-backup/site.yml`
3. `repo_url`
4. `repo_branch`
5. `credential_ref` 可为空，由设备绑定优先提供
6. `oneops.contract.json`
7. 默认变量，如 `network_backup_tag`

### 5.2 选择目标设备

用户从设备清单、设备分组或查询结果选择设备。

MVP 首先支持显式 `device_codes`。分组和灵活查询可以在 UI 层解析后转成 `device_codes`。

### 5.3 执行前适配检查

平台读取设备数据后逐台检查：

1. 设备是否存在。
2. 按 `access_plane` 解析 `in_band_ip` 或 `out_band_ip`。
3. 解析设备绑定凭据，优先设备绑定，兜底任务级 `credential_ref`。
4. 调用 Ansible 设备画像解析，得到 `vendor_family`、`ansible_connection`、`ansible_network_os`。
5. 按 contract 判断厂商族、访问平面、凭据是否满足。

输出示例：

```json
{
  "total": 20,
  "ready": 18,
  "blocked": 2,
  "items": [
    {
      "device_code": "SW001",
      "status": "ready",
      "access_plane": "in_band",
      "target_address": "10.0.0.1",
      "vendor_family": "cisco_ios",
      "ansible_connection": "network_cli",
      "ansible_network_os": "ios",
      "credential_source": "device_binding"
    },
    {
      "device_code": "SW009",
      "status": "blocked",
      "reason": "missing credential_ref"
    }
  ]
}
```

### 5.4 生成 Inventory

MVP 继续沿用每台设备生成一个子任务的 fanout 方式。

单设备 inventory 示例：

```ini
[all]
SW001 ansible_host=10.0.0.1 vendor_family=cisco_ios ansible_connection=network_cli ansible_network_os=ios ansible_command_timeout=120
```

后续可以升级为批量 inventory：

```ini
[cisco_ios]
SW001 ansible_host=10.0.0.1 vendor_family=cisco_ios ansible_connection=network_cli ansible_network_os=ios ansible_command_timeout=120

[huawei_ce]
SW002 ansible_host=10.0.0.2 vendor_family=huawei_ce ansible_connection=network_cli ansible_network_os=ce ansible_command_timeout=120
```

敏感字段不得写入 inventory。

### 5.5 执行 Playbook

每台设备创建一个子任务，子任务继承父任务的资产定义和参数。

子任务独立解析凭据，生成执行画像，并由 Controller/Agent 执行 Ansible。

Playbook 运行时必须提供：

1. `ONEOPS_TASK_ID`
2. `ONEOPS_OUTPUT_DIR`
3. `ONEOPS_RESULT_FILE`
4. `ONEOPS_ARTIFACT_MANIFEST`

### 5.6 读取产物

任务完成后，平台读取 artifact manifest。

期望产物：

1. `network-backups/<host>-<tag>.cfg`
2. `network-config-backup-<host>.json`

其中 `.cfg` 视为敏感产物，默认只允许有权限用户下载；`.json` summary 可用于页面展示和回写。

### 5.7 结果回写

平台根据 summary JSON 和 artifact 元数据生成配置备份记录。

回写内容：

1. 设备最近配置备份状态。
2. 设备最近配置备份时间。
3. 最近配置备份任务 ID。
4. 备份文件引用。
5. 备份文件大小和 hash。
6. 厂商族和访问平面。

设备详情页和配置备份列表可查询这些记录。

### 5.8 父任务聚合

父任务展示：

1. 总设备数
2. 可执行设备数
3. 阻断设备数
4. 成功数
5. 失败数
6. 已归档备份数
7. 失败原因分布
8. 每台设备的子任务 ID、状态、产物入口

## 6. 数据模型建议

### 6.1 任务资产契约

短期方案：

1. 将 `oneops.contract.json` 放在脚本仓库。
2. 模板导入时读取并保存到 `platform_task_template` 的扩展字段或新增 `contract_json` 字段。
3. 若暂不改表，可先把 contract 放入模板 `extra_vars_json` 的保留 key，作为过渡方案。

推荐新增字段：

```text
platform_task_template.contract_json text
platform_task_template.asset_category varchar(64)
platform_task_template.risk_level varchar(32)
platform_task_template.lifecycle_status varchar(32)
```

### 6.2 设备适配预检结果

推荐新增轻量表：

```text
platform_task_target_precheck
  id
  task_id
  device_code
  status
  access_plane
  target_address
  vendor_family
  ansible_connection
  ansible_network_os
  credential_ref
  credential_source
  reason
  created_at
```

MVP 也可以先通过父任务日志保存预检摘要，但页面聚合会受限。

### 6.3 配置备份记录

推荐新增表：

```text
platform_device_config_backup
  id
  device_code
  task_id
  parent_task_id
  controller_id
  vendor_family
  access_plane
  backup_status
  backup_time
  artifact_name
  artifact_storage_key
  artifact_size
  artifact_sha256
  config_hash
  summary_json
  error_message
  created_at
  updated_at
```

索引：

```text
idx_device_config_backup_device_time(device_code, backup_time)
idx_device_config_backup_task(task_id)
idx_device_config_backup_parent(parent_task_id)
```

## 7. API 建议

### 7.1 预检接口

```http
POST /api/v1/platform/task-assets/:template_id/ansible/precheck
```

请求：

```json
{
  "device_codes": ["SW001", "SW002"],
  "access_plane": "in_band",
  "credential_ref": ""
}
```

响应：

```json
{
  "total": 2,
  "ready": 1,
  "blocked": 1,
  "items": []
}
```

### 7.2 创建备份任务

沿用现有任务创建接口，传入：

```json
{
  "template_id": "network-config-backup",
  "app_type": "ansible",
  "device_codes": ["SW001", "SW002"],
  "access_plane": "in_band",
  "extra_vars_json": "{\"network_backup_tag\":\"manual\"}"
}
```

### 7.3 查询父任务聚合

```http
GET /api/v1/platform/tasks/:task_id/target-summary
```

响应包含设备维度状态、子任务、产物和错误原因。

### 7.4 查询设备配置备份

```http
GET /api/v1/device/v2/:device_code/config-backups
```

返回该设备历史备份记录。

## 8. 前端建议

MVP 页面不需要新建复杂编排器，建议做三处增强：

1. 任务资产详情页：展示 Ansible contract、适用设备、风险等级、输出产物。
2. 发起执行页：选择设备、选择访问平面、执行预检、只允许提交 ready 设备。
3. 任务详情页：展示父任务聚合、设备维度结果、备份文件下载、summary JSON 预览。

设备详情页增加“配置备份”标签页：

1. 最近备份状态
2. 最近备份时间
3. 最近备份任务
4. 历史备份列表
5. 下载入口

## 9. 安全规则

MVP 必须满足：

1. inventory 中禁止出现 `ansible_password`、`ansible_ssh_pass`、`ansible_become_password`、`token`、`private_key` 等敏感字段。
2. 凭据只通过 `credential_ref` 和执行画像解析。
3. 配置备份 `.cfg` 默认标记为敏感产物。
4. 任务日志不得打印明文凭据。
5. artifact 下载必须走权限校验。
6. 预检结果中的 `credential_ref` 可以展示引用名，但不能展示解析后的用户名、密码、私钥。

## 10. 验收标准

MVP 通过的标准：

1. 能从任务资产发起网络配置备份。
2. 能选择至少 2 台不同厂商或不同平台画像的设备。
3. 执行前能输出 ready/blocked 设备列表。
4. ready 设备生成的 inventory 包含 `vendor_family`、`ansible_connection`、`ansible_network_os`。
5. inventory 不包含任何明文凭据。
6. 成功设备生成 `.cfg` 和 summary JSON。
7. 平台能读取 artifact manifest 并展示产物。
8. 设备维度能看到成功/失败状态。
9. 设备详情能看到最近一次配置备份状态和时间。
10. 失败设备能展示清晰失败原因。

## 11. 分阶段计划

### Phase 1：契约和预检

1. 为 `network-config-backup` 增加 `oneops.contract.json`。
2. 增加 contract 加载和校验能力。
3. 增加设备适配预检服务。
4. 输出 ready/blocked 设备列表。

### Phase 2：Inventory 和执行

1. 统一设备 Ansible inventory 生成逻辑。
2. 复用 `ResolveAnsibleDeviceProfile`。
3. 确保敏感字段不进入 inventory。
4. 从预检结果创建 fanout 子任务。

### Phase 3：产物归档

1. 读取 `ONEOPS_ARTIFACT_MANIFEST`。
2. 归档 `.cfg` 和 `.json`。
3. 标记敏感产物。
4. 在任务详情页展示产物入口。

### Phase 4：结果回写和展示

1. 新增配置备份记录。
2. 回写设备最近备份状态。
3. 增加父任务设备维度聚合。
4. 增加设备详情配置备份入口。

## 12. 风险和注意事项

1. 网络设备连接方式差异较大，`ansible_network_os` 的候选值需要在真实环境持续校准。
2. H3C 等设备可能需要特殊 SSH 参数，已有 `ansible_ssh_common_args` 逻辑应继续保留。
3. F5 走 local provider 方式，与普通 `network_cli` 设备不同，预检和凭据注入要单独验证。
4. 配置文件属于敏感资产，下载、展示、日志都要保守处理。
5. Playbook 输出契约必须稳定，否则结果回写会脆弱。

## 13. 后续扩展

网络配置备份 MVP 打通后，可以按同一模式扩展：

1. `network-multi-vendor-baseline`：巡检结果回写设备画像和报告。
2. `network-batch-command`：增加命令风险识别和审批。
3. `network-snippet-deploy`：强制备份、审批、分批、验证。
4. `linux-baseline`：服务器基线巡检和整改任务生成。
5. `remote-tcpdump`：诊断产物归档和有效期管理。

核心原则保持不变：每个 Ansible Playbook 都必须具备目标契约、变量契约、凭据契约、风险契约和输出契约。
