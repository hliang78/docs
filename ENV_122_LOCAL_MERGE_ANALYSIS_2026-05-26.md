# 122 与 local 环境数据合并分析（2026-05-26）

## 结论先看

本次范围按最新口径收敛为：

- 不考虑 `device_v2` 设备台账本身
- 只关注“模板、规则、策略配置”这类可复用配置资产
- 不把工作台过程数据、任务历史、采集运行态结果纳入最终权威数据

按这个口径，真正需要看的核心对象只有两类：

1. MySQL 中落库的模板/规则表
2. Nacos / 启动配置中的配置驱动规则

### 模板/规则口径下的最终建议

| 分类 | 对象 | 存储位置 | 建议权威来源 | 说明 |
| --- | --- | --- | --- | --- |
| 脚本模板 | `platform_task_template` | MySQL | 以 `122` 新增模板增量并入 local | 122 有 42 条，local 有 34 条；共享模板主要差在 `repo_url` |
| 脚本变量组 | `platform_variable_set` | MySQL | 以 local 为主，人工确认 1 条差异 | 两边 27 条，只有 1 条变量内容不同 |
| 脚本仓库定义 | `platform_repository` | MySQL | 以 local 为主 | 同一条记录但 URL 指向不同环境 |
| 采集标准字段 | `device_collection2_standard_field` | MySQL | 两边一致 | 130 条，校验和一致 |
| 采集策略 | `device_collection2_policy` | MySQL | 以 local 为主 | 逻辑基本一致，但 `mib_tree_file` 路径是环境字段 |
| 采集契约 | `device_collection2_contract` | MySQL | 不作为本次 DB 合并重点 | 两边都为 0，代码显示更多依赖内置/配置生成 |
| DC2 profile 规则 | `device_collection2.collection_profiles` | Nacos / 启动配置 | 需要单独比对配置源 | 不在当前 MySQL 表里 |
| obsflow 闭环采集规则 | `attentions` / obsflow contract config | Nacos / 启动配置 | 需要单独比对配置源 | 主要不是 MySQL 表 |

### 明确不纳入“模板/规则”合并范围

| 对象 | 原因 |
| --- | --- |
| `platform_script_studio_session` / `message` / `draft` / `test_run` / `publish_run` | 属于工作台过程数据，不是最终模板规则 |
| `platform_scheduled_task` | 属于调度运行配置，本轮已明确不需要 |
| `platform_task` / `platform_task_log` | 属于执行历史，不是模板规则 |
| `device_collection2_fact*` / `run*` / `collection_run` / `processing_run` / `snapshot_workflow` | 属于采集运行态结果 |
| `observation_batch` / `l2_topology_snapshot` | 属于 obsflow 运行结果 |

最终建议的“本地权威数据”来源如下：

| 领域 | 代表表 | 建议权威来源 | 说明 |
| --- | --- | --- | --- |
| 脚本工作台运行数据 | `platform_script_studio_*` | 不纳入本次模板/规则合并 | 它们是工作台过程数据，不是最终模板规则 |
| 脚本模板增量 | `platform_task_template` | 以 `122` 为主，但不能全表覆盖 | 122 比本地多 8 条模板，但共享模板里的 `repo_url` 是环境相关字段 |
| 脚本变量组 | `platform_variable_set` | 以本地为主，人工比对 1 条差异 | 27 条数量一致，仅 1 条变量内容不同 |
| 脚本仓库配置 | `platform_repository` | 以本地为主或迁入后改写 URL | 两边是同一条记录、同一 ID，但 URL 指向不同环境 |
| 定时任务 | `platform_scheduled_task` | 不纳入本次合并 | 本地为空，122 有 17 条，但当前明确不需要 |
| 任务执行历史 | `platform_task` / `platform_task_log` | 不纳入本次合并 | 本地为空，122 有大量历史数据，但当前明确不需要 |
| 采集标准字段 | `device_collection2_standard_field` | 两边一致 | 校验和一致，可不处理 |
| 采集策略 | `device_collection2_policy` | 以本地为主 | 逻辑相同，但 `scope_json.mib_tree_file` 路径是环境相关字段 |
| 采集契约 | `device_collection2_contract` | 暂不做 DB 合并 | 两边表内都是 0，代码显示可由内置逻辑/配置生成 |
| obsflow 闭环契约 | 非主要存库 | 以本地配置/Nacos 为主 | 代码显示为配置驱动，不是主要 DB 合并对象 |
| obsflow / DC2 运行态数据 | `device_collection2_fact*`、`collection_run`、`processing_run`、`snapshot_workflow` 等 | 本地 | 本地更完整，122 主要是部分运行痕迹 |

### 额外确认：其它看起来像“规则表”的对象当前都没有实际数据

两边都为 `0` 的表：

- `platform_data_quality_rule`
- `platform_grouping_selection_set`
- `platform_monitoring_v2_selection_set`
- `platform_snmp_collection_strategy`
- `platform_metric_metadata`

这说明本轮“模板、规则”合并不需要把这些表纳入重点范围。

## 关键发现

### 1. `platform` 脚本管理数据里，真正与模板有关的核心是模板/变量组/仓库

122 中存在而本地为空的 `script_studio` 数据很多：

- `platform_script_studio_session`: 21
- `platform_script_studio_message`: 4
- `platform_script_studio_draft`: 9
- `platform_script_studio_test_run`: 13
- `platform_script_studio_publish_run`: 11
- `platform_scheduled_task`: 17
- `platform_task`: 16680
- `platform_task_log`: 337109 左右

但按“模板、规则”口径，这些不作为本次核心合并对象。

真正需要关注的是：

- `platform_task_template`
- `platform_variable_set`
- `platform_repository`

### 2. `platform_repository` 不能直接覆盖

两边是同一条仓库记录、同一 ID：

- `id = 509091e4-2bdc-11f1-b198-0050569b3ce3`

但 URL 不同：

- local: `http://127.0.0.1:3004/netxops/task-center-example-scripts.git`
- 122: `http://192.168.100.122:3104/netxops/task-center-example-scripts.git`

这类字段是明显的环境字段，不建议直接用 `122` 全量覆盖本地。

### 3. `platform_task_template` 不能直接全表覆盖

现状：

- local: 34 条
- 122: 42 条

分析结果：

- 34 条共享模板基本是同一批模板
- 共享模板的主要差异不是模板逻辑，而是 `repo_url` 指向了 122 的仓库地址
- 122 额外多 8 条模板，主要是：
  - `reuse-shell-smoke-20260524`
  - `reuse-python-smoke-20260524`
  - `reuse-ansible-smoke-20260524`
  - `reuse-terraform-smoke-20260524`
  - `reuse-tofu-smoke-20260524`
  - `reuse-terragrunt-smoke-20260524`
  - `script-template-chatgpt_test_shell_session`
  - `2c11a0ec-58e9-11f1-ac4d-0050569b3ce3` 这条记录字段基本为空，需要人工确认是否应保留

建议：

- 共享的 34 条模板不要直接用 122 覆盖本地
- 只把 122 的“新增模板”按需迁入本地
- 迁入时统一改写 `repo_url`
- 其中 `script-template-chatgpt_test_shell_session` 需要结合 local Gitea 同步状态再判定，不能只凭 local 仓库当前缺失就直接排除

### 4. `platform_variable_set` 基本一致，但有 1 条实质差异

两边都是 27 条。

唯一发现的内容差异：

- `task-center-ansible-switch-baseline-defaults`

差异点在 `huawei_ce_baseline_commands`：

- local: `display lldp neighbor verbose`
- 122: `display lldp neighbor`

这不是环境字段，而是规则内容差异，不能自动判断谁更权威，建议人工确认后再决定保留哪版。

### 5. `platform_scheduled_task` 本次不纳入合并

本地为空，122 有 17 条，且都引用 122 新增的 3 个模板：

- `de29845f-5758-11f1-8dfb-0050569b3ce3`
- `f1882e66-5758-11f1-8dfb-0050569b3ce3`
- `f25ff969-5758-11f1-8dfb-0050569b3ce3`

这说明它们在 122 内部是自洽的，但按当前口径，这批定时任务不进入本次 local 权威数据。

### 6. `device_collection2_standard_field` 两边完全一致

校验结果：

- local: `130 / ca0c9e220f5e70334b02839d19cdaeaa`
- 122: `130 / ca0c9e220f5e70334b02839d19cdaeaa`

这张表可以视为一致，不需要专项合并。

### 7. `device_collection2_policy` 逻辑基本一致，但路径字段不同

两边都是 11 条，名称、策略参数、数据集定义基本一致。

主要差异来自 `scope_json` 中的 `mib_tree_file` 路径：

- local: `/home/jacky/project/OneOPS-ALL/quick_env/init-data/mib_tree.json`
- 122: `/home/jacky/zero/quick_env/.runtime/demo9/init-data/mib_tree.json`

这说明：

- 这些策略多数是由启动/bootstrap 逻辑生成的
- 差异是运行环境路径，不是业务规则差异

所以这张表不建议从 122 覆盖到本地，本地版本更适合本机运行。

### 8. `device_collection2_contract` 不是当前主要 DB 合并对象

两边数据库里都是 0 条。

代码显示：

- `obsflow` 的闭环采集 contract 主要来自配置
- `device_collection2` 的 contract 可由内置逻辑、MIB tree 配置或导入逻辑生成

因此它更像“配置/引导产物”，不是现在最关键的库表合并对象。

### 9. `obsflow` / `device_collection2` 的一部分关键规则在配置里，不在 MySQL

代码位置：

- `OneOps/app/obsflow/adapters/config_collection_contract_store.go`

说明 `obsflow` 闭环采集规则主要来自配置对象，而不是这些 MySQL 运行表。

仓库内可以确认的配置来源有：

- `OneOps/config/nacos-device_collection2.merge.yaml`
- `OneOps/example_config.yaml` 中的 `device_collection2`
- `OneOps/example_config.yaml` / 启动配置中的 `attentions`

其中 `device_collection2.collection_profiles` 明确描述了：

- 按 `catalog_names` / `platform_names` 匹配 profile
- 每个 profile 绑定 `contract_key`
- 每个 profile 绑定 `dataset_keys`

这部分才是更接近“采集规则模板”的真实配置源。

因此如果你这次主要关心“模板、规则”，除了 MySQL 表，还应该把以下配置源纳入最终比对：

- `device_collection2.collection_profiles`
- `observationMIB.treeFile`
- `attentions`

数据库现状上，本地明显更完整：

- `observation_batch`
- `processing_run`
- `l2_topology_snapshot`
- `snapshot_workflow`

122 基本为空或接近为空。

所以：

- `obsflow` 运行态数据保留本地
- 真正要比对的是 Nacos/配置，而不是主要依赖 MySQL 合并

## 建议的合并策略

### A. 直接以 122 为准迁入本地

适合整表迁入：

备注：

- 按“模板、规则”口径，本轮不建议迁 `platform_script_studio_*`
- 本次明确不迁 `platform_scheduled_task`
- 本次明确不迁 `platform_task` / `platform_task_log`

### B. 只做增量迁入，不做覆盖

建议增量迁入：

- `platform_task_template`

规则：

- 只迁 122 独有模板
- 迁入前人工确认是否排除空模板 `2c11a0ec-58e9-11f1-ac4d-0050569b3ce3`
- 迁入后统一把 `repo_url` 改成本地可用地址

### C. 保留本地，不从 122 覆盖

建议保留本地版本：

- `platform_repository`
- `device_collection2_policy`
- `device_collection2_standard_field`
- `platform_script_studio_session`
- `platform_script_studio_message`
- `platform_script_studio_draft`
- `platform_script_studio_test_run`
- `platform_script_studio_publish_run`
- `device_collection2_fact`
- `device_collection2_fact_latest`
- `device_collection2_run`
- `device_collection2_run_device`
- `collection_run`
- `observation_batch`
- `processing_run`
- `l2_topology_snapshot`
- `snapshot_workflow`

### D. 人工确认后再决定

- `platform_variable_set`

尤其是：

- `task-center-ansible-switch-baseline-defaults`

## 最终迁移清单（仅模板 / 规则）

### 1. 建议直接迁入 local 的模板

以下 7 条建议从 `122` 增量迁入 local：

- `de29845f-5758-11f1-8dfb-0050569b3ce3` `reuse-shell-smoke-20260524`
- `f1882e66-5758-11f1-8dfb-0050569b3ce3` `reuse-python-smoke-20260524`
- `f25ff969-5758-11f1-8dfb-0050569b3ce3` `reuse-ansible-smoke-20260524`
- `f3242b55-5758-11f1-8dfb-0050569b3ce3` `reuse-terraform-smoke-20260524`
- `f3eea34e-5758-11f1-8dfb-0050569b3ce3` `reuse-tofu-smoke-20260524`
- `f4b23008-5758-11f1-8dfb-0050569b3ce3` `reuse-terragrunt-smoke-20260524`
- `cf71fe4a-57ef-11f1-98c3-0050569b3ce3` `script-template-chatgpt_test_shell_session`

迁入理由：

- 它们只存在于 `122`
- 与 local 现有 34 条共享模板没有非环境字段冲突
- 共享模板对比结果显示：除了 `repo_url` 外没有其它结构差异

迁入注意：

- 统一把 `repo_url` 从 `http://192.168.100.122:3104/...` 改写为 local 可访问仓库地址
- 当前确认可用的 local 地址为 `http://127.0.0.1:3004/netxops/task-center-example-scripts.git`

### 2. 建议不要迁入的模板

以下 1 条建议排除：

- `2c11a0ec-58e9-11f1-ac4d-0050569b3ce3`

排除理由：

- 名称、`app_type`、`repo_url`、`playbook_path` 等关键字段为空
- 只剩一段 `extra_vars_json`
- 在“模板资产”口径下更像残留记录，不适合作为权威模板迁入

### 3. 建议保留 local 的模板相关对象

- `platform_repository`
- `platform_variable_set`

其中：

- `platform_repository` 两边是同一条记录，只差环境地址，保留 local 最稳
- `platform_variable_set` 27 条里仅 1 条有真实规则差异

### 4. 变量组差异的最终决定

最终按 `122 -> local` 处理的对象：

- `583f754a-2cd7-11f1-b70a-0050569b3ce3`
- 名称：`task-center-ansible-switch-baseline-defaults`

差异字段：

- `huawei_ce_baseline_commands`

差异内容：

- local: `display lldp neighbor verbose`
- 122: `display lldp neighbor`

最终决定：

- 采用 `122` 版本覆盖 local
- 即：`huawei_ce_baseline_commands` 采用 `display lldp neighbor`

### 5. 采集规则最终结论

MySQL 侧：

- `device_collection2_standard_field`：两边完全一致，不处理
- `device_collection2_policy`：保留 local
- `device_collection2_contract`：两边都为 0，不作为本次迁移对象

配置侧：

- `device_collection2` 整段在 local 与 122 的 `cipher-aes-start-config` 中完全一致
- `device_collection2.collection_profiles`：两边完全一致，共 10 条 profile
- `observationMIB.treeFile`：仅路径不同，应保留 local 路径

### 6. `attentions` 规则差异

`attentions` 并非完全一致：

- local: 12 条
- 122: 11 条

唯一发现的差异是 local 比 122 多 1 条：

- `manufacturer = Huawei`
- `platform = VRP`

这说明：

- local 的闭环采集规则覆盖面比 122 更完整
- 在“规则权威版本”口径下，`attentions` 应以 local 为主

### 7. 可以直接执行的最小合并动作

如果现在只做最小且安全的模板/规则合并，建议动作只有这 3 个：

1. 从 `122` 增量导入上面列出的 7 条 `platform_task_template`
2. 导入前把这些模板的 `repo_url` 改写为 local 仓库地址
3. 将 `task-center-ansible-switch-baseline-defaults` 按 `122 -> local` 覆盖

### 8. Nacos 配置的最终处理口径

已实际对比两边 Nacos 中 `tenant=ONEOPS_PROD`、`group=DEFAULT_GROUP`、`dataId=cipher-aes-start-config` 的内容。

结果如下：

- `device_collection2` 整段：两边完全一致
- `device_collection2.collection_profiles`：两边完全一致，共 10 条
- `observationMIB.treeFile`：仅文件路径不同
- `attentions`：local 比 `122` 多 1 条 `Huawei / VRP` 规则

因此，Nacos 配置不建议整段从 `122` 覆盖到 local。

建议的最终处理方式：

1. `device_collection2`：不迁，保持 local 现状
2. `collection_profiles`：不迁，保持 local 现状
3. `observationMIB.treeFile`：保留 local 路径
4. `attentions`：保留 local 现状，不用 122 覆盖

换句话说，这次 `122 -> local` 的主动作发生在 MySQL 模板/变量组，不发生在 Nacos 主配置。

## 导入后验证

### 数据库验证

可直接执行：

- [2026-05-26_post_merge_validation.sql](/home/jacky/project/OneOPS-ALL/docs/sql/2026-05-26_post_merge_validation.sql)

重点验证项：

- 7 条模板是否已存在
- 7 条模板的 `repo_url` 是否已改为 local 地址
- `task-center-ansible-switch-baseline-defaults` 是否已采用 `122` 版本

### 前端 / API 验证

前端页面：

- `platform/task-templates`
- `platform/variable-sets`

对应 API：

- `GET /platform/task-templates`
- `GET /platform/variable-sets`
- `GET /platform/task-templates/:id`
- `GET /platform/variable-sets/:id`

建议核对：

1. 模板列表中出现新增的 7 条模板
2. 模板详情中的 `repo_url` 为 local 地址
3. 变量组详情中的 `huawei_ce_baseline_commands` 为 `display lldp neighbor`

### 仓库可达性注意事项

本次导入时，模板的 `repo_url` 已按决策改写为：

- `http://127.0.0.1:3004/netxops/task-center-example-scripts.git`

但从当前执行环境的实测结果看：

- `http://127.0.0.1:3004/...` 可返回 `200`
- `http://192.168.100.122:3104/...` 可返回 `200`

这说明：

- 数据已经按你的决策改成了 local 地址
- 当前确认 `127.0.0.1:3004` 从这台机器上是可达的

因此后续如果模板执行失败，第一优先排查项应是：

- `127.0.0.1:3004` 对 OneOps 进程是否可达
- 本机 Gitea / 3004 端口服务状态

除此之外，其余模板/规则对象建议保持 local 现状不动。

## 推荐执行顺序

1. 备份本地 `UniOPS`
2. 先迁 `platform_task_template` 的 122 独有模板，并改写 `repo_url`
3. 不迁 `platform_script_studio_*`
4. 不迁 `platform_scheduled_task`
5. 不迁 `platform_task` / `platform_task_log`
6. 保留本地 `device_collection2_policy` 与 `device_collection2_standard_field`
7. 单独人工确认 `platform_variable_set` 那 1 条差异
8. 单独补做 Nacos / 启动配置里的 `device_collection2.collection_profiles`、`attentions`、`observationMIB.treeFile` 对比

## 追加根因结论

针对报错：

- `读取仓库文件内容失败: open /tmp/oneops-script-studio-read-.../shell/chatgpt/chatgpt_test_shell_session: no such file or directory`

重新核实后，根因已经明确，不是模板数据本身坏，而是 **local Gitea 仓库内容落后于 122**。

### 证据 1：122 的模板记录和 122 的仓库内容是对得上的

在 `122` 环境中，下面这些模板路径都真实存在：

- `shell/chatgpt/chatgpt_test_shell_session`
- `shell/smoke/run.sh`
- `python/smoke/run.py`
- `ansible/smoke/site.yml`
- `terraform/smoke/main.tf`
- `tofu/smoke/main.tf`
- `terragrunt/smoke/terragrunt.hcl`

也就是说，`script-template-chatgpt_test_shell_session` 不是坏模板；此前把它判定为坏模板，是因为当时只验证了 local Gitea。

### 证据 2：local 和 122 的 Gitea 仓库不是同一个版本

两边仓库 HEAD 不一致：

- local `127.0.0.1:3004`：`61e01783c6c9aee85e7dbe5ec8587d8ff40598d8`
- `122` `192.168.100.122:3104`：`50565a094350232bfce5546f60b830912db51cbb`

时间上也明显落后：

- local 最新提交时间：`2026-03-31 14:44:57 +0000`
- `122` 最新提交时间：`2026-05-26 11:11:37 +0000`

### 证据 3：缺失目录正好就是报错与新增模板依赖的目录

`122` 仓库中存在、但 local 仓库中缺失的关键目录包括：

- `shell/chatgpt`
- `shell/smoke`
- `python`
- `ansible/smoke`
- `terraform/smoke`
- `tofu/smoke`
- `terragrunt/smoke`

因此，只要 local 模板或脚本工作台会话引用这些路径，后端在读取仓库文件时就一定会报：

- `open /tmp/oneops-script-studio-read-.../<path>: no such file or directory`

### 根因归位

这次问题的根因不是：

- MySQL 模板记录乱码
- `playbook_path` 字段损坏
- 前端随意拼错路径

真正根因是：

- `122` 的模板数据已经演进到依赖 `2026-05-26` 那版仓库内容
- 但 local Gitea 仍停留在 `2026-03-31` 的旧提交
- 我们把 `122` 的模板迁到 local 后，又把 `repo_url` 指向了 local Gitea
- 于是模板记录引用的新路径，在 local 仓库里根本不存在，最终触发当前报错

### 影响面

受影响的不只有 `chatgpt_test_shell_session`，还包括本次新增导入的 6 条模板，因为它们依赖的 `smoke` / `python` / `terraform` / `tofu` / `terragrunt` 目录也都只存在于 `122` 仓库。

## 最终建议

如果目标是“在 local 中形成最权威的模板、规则配置”，最稳妥的做法不是把 122 全库同步过来，而是：

- `platform` 侧只迁“122 独有模板”
- `platform_variable_set` 只人工处理那 1 条真实差异
- `platform_repository` 保留本地
- `device_collection2_policy` 保留本地
- `device_collection2_standard_field` 视为已一致
- `obsflow` / `device_collection2` 的配置驱动规则再单独对比 Nacos / 启动配置

这样得到的是“122 的模板增量 + local 的规则主版本 + 本地化环境配置”的组合，更接近你要的最终权威配置集。
