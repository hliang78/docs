# luzhou -> local Ruijie 配置迁移记录（2026-05-26）

## 迁移目标

仅吸收 `luzhou` 环境中与 Ruijie 相关的 `device_collection2 / device v2 candidate engine` 配置成果，不迁移运行态数据，不覆盖 `local` 的其他厂商规则。

## 已执行迁移

### 1. MySQL

表：`device_collection2_policy`

对象：

- `DC2 Profile Collection net-ruijie`

变更：

- `dataset_keys_json`
  - 迁移前：`["snmp_sys_descr","snmp_if_table","cli_interface_brief"]`
  - 迁移后：`["snmp_sys_descr","snmp_if_table","cli_lldp_neighbors"]`

保留本地字段：

- `scope_json.mib_tree_file`
  - 保持 `local` 本地路径
  - `/home/jacky/project/OneOPS-ALL/quick_env/init-data/mib_tree.json`

### 2. Nacos

#### dataId=`cipher-aes-start-config`

对象：

- `device_collection2.collection_profiles[id=net-ruijie]`

变更：

- `dataset_keys`
  - 迁移前：`["snmp_sys_descr","snmp_if_table","cli_interface_brief"]`
  - 迁移后：`["snmp_sys_descr","snmp_if_table","cli_lldp_neighbors"]`

未变更：

- `match.catalog_names`
- `match.platform_names`
- `contract_key`
- `priority`

#### dataId=`device_v2_candidate_engine`

新增 / 同步的 Ruijie 规则：

- `prepared_fact_extractors`
  - 新增 `ruijie_vendor_backfill`
- `fields.catalog.match_rules`
  - 新增 `identity.vendor=ruijie` 的 `sys_descr` 判型规则
  - `EASY GATEWAY / Gateway / gateway -> ROUTER`
  - `Wireless Switch / Switch / switch -> SWITCH`
- `fields.platform.match_rules`
  - 新增 `identity.vendor=ruijie` 的平台识别规则
  - `Ruijie / RGOS -> Ruijie`

未迁移项：

- `attentions`
  - `local` 与 `luzhou` 的 Ruijie attention 规则内容一致
  - 因此本次未修改

## 备份与脚本

SQL：

- [2026-05-26_merge_luzhou_ruijie_into_local.sql](./sql/2026-05-26_merge_luzhou_ruijie_into_local.sql)
- [2026-05-26_rollback_luzhou_ruijie_into_local.sql](./sql/2026-05-26_rollback_luzhou_ruijie_into_local.sql)

Nacos 备份：

- [2026-05-26_local_cipher-aes-start-config.before_luzhou_ruijie_merge.yaml](./nacos/2026-05-26_local_cipher-aes-start-config.before_luzhou_ruijie_merge.yaml)
- [2026-05-26_local_device_v2_candidate_engine.before_luzhou_ruijie_merge.yaml](./nacos/2026-05-26_local_device_v2_candidate_engine.before_luzhou_ruijie_merge.yaml)
- [2026-05-26_local_cipher-aes-start-config.after_luzhou_ruijie_merge.yaml](./nacos/2026-05-26_local_cipher-aes-start-config.after_luzhou_ruijie_merge.yaml)
- [2026-05-26_local_device_v2_candidate_engine.after_luzhou_ruijie_merge.yaml](./nacos/2026-05-26_local_device_v2_candidate_engine.after_luzhou_ruijie_merge.yaml)

## 验证结果

### 配置回读

已确认 `local` 当前生效配置为：

- `net-ruijie.dataset_keys = ["snmp_sys_descr","snmp_if_table","cli_lldp_neighbors"]`
- `device_v2_candidate_engine` 中存在 `ruijie_vendor_backfill`
- `catalog` 中存在 `EASY GATEWAY` 判型规则
- `platform` 中存在 `RGOS -> Ruijie` 判型规则

### 代码级验证

已执行测试：

- `go test ./app/device_collection2/collectionplan ./app/device/v2/candidateengine -run Test -count=1`
- `go test ./app/device/v2/candidateengine -run 'Ruijie|ruijie' -count=1 -v`

结果：

- 全部通过
- 其中锐捷相关测试覆盖了：
  - `ruijie_vendor_backfill`
  - `Ruijie Switch -> SWITCH`
  - `Ruijie EASY GATEWAY -> ROUTER`
  - `Ruijie / RGOS -> platform=Ruijie`

## 生效方式

- `cipher-aes-start-config` 通过 Nacos watcher 热更新
- `device_v2_candidate_engine` 在 device v2 prepare/store runtime 中按调用从 Nacos 读取

因此本次迁移后不需要额外重启服务。
