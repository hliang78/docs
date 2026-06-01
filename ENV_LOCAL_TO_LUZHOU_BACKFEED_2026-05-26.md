# local -> luzhou 回灌准备记录（2026-05-26）

## 目标

将 `local` 当前更权威的 `DC2 / 采集入库 / obsflow` 关键配置反哺到 `luzhou`。

本次准备范围：

- `device_collection2_policy`（MySQL）
- `cipher-aes-start-config` 中的：
  - `device_collection2`
  - `attentions`
- 独立 Nacos dataId：
  - `device_v2_candidate_engine`

## 执行状态

本次已在 `2026-05-26` 通过恢复后的本地转发入口完成 `local -> luzhou` 回灌：

- Nacos：`127.0.0.1:36911`
- MySQL：`127.0.0.1:45385`

执行前已完成远端备份，执行后已完成 MySQL / Nacos 回读校验。

## 已准备文件

### 1. MySQL 回灌 SQL

- [2026-05-26_backfeed_local_dc2_policies_into_luzhou.sql](./sql/2026-05-26_backfeed_local_dc2_policies_into_luzhou.sql)

说明：

- 来源：`local` 当前 `device_collection2_policy`
- 覆盖范围：11 条 policy
- 已将 `mib_tree_file` 适配为 `luzhou` 路径：
  - `/home/ubuntu/project/quick_env/init-data/mib_tree.json`

### 2. Nacos 主文件回灌候选

- [2026-05-26_luzhou_cipher-aes-start-config.backfeed_from_local.yaml](./nacos/2026-05-26_luzhou_cipher-aes-start-config.backfeed_from_local.yaml)

说明：

- 基底：之前备份的 `luzhou` 主文件
- 替换段：
  - `device_collection2`
  - `attentions`
- 保留段：
  - `observationMIB`
  - `license / mysql / minio / mongodb / vault` 等环境字段

### 3. candidate engine 回灌候选

- [2026-05-26_luzhou_device_v2_candidate_engine.backfeed_from_local.yaml](./nacos/2026-05-26_luzhou_device_v2_candidate_engine.backfeed_from_local.yaml)

说明：

- 直接采用 `local` 当前权威版本
- 适合在 `luzhou` 的 `device_v2_candidate_engine` dataId 上整份发布

## 本次实际备份

### 1. MySQL policy 备份

- [2026-05-26_luzhou_device_collection2_policy.before_backfeed.sql](./sql/2026-05-26_luzhou_device_collection2_policy.before_backfeed.sql)

说明：

- 来源：回灌前 `luzhou` 的 `device_collection2_policy`
- 使用 `--no-tablespaces` 导出，避免账号缺少 `PROCESS` 权限时报错

### 2. Nacos 主文件备份

- [2026-05-26_luzhou_cipher-aes-start-config.before_backfeed.yaml](./nacos/2026-05-26_luzhou_cipher-aes-start-config.before_backfeed.yaml)

### 3. Candidate engine 备份

- [2026-05-26_luzhou_device_v2_candidate_engine.before_backfeed.yaml](./nacos/2026-05-26_luzhou_device_v2_candidate_engine.before_backfeed.yaml)

## 本次实际回读

### 1. Nacos 主文件回读

- [2026-05-26_luzhou_cipher-aes-start-config.after_backfeed.yaml](./nacos/2026-05-26_luzhou_cipher-aes-start-config.after_backfeed.yaml)

### 2. Candidate engine 回读

- [2026-05-26_luzhou_device_v2_candidate_engine.after_backfeed.yaml](./nacos/2026-05-26_luzhou_device_v2_candidate_engine.after_backfeed.yaml)

## 执行结果

### MySQL

- `device_collection2_policy` 已按 `local` 当前权威版本覆盖到 `luzhou`
- 总条数保持为 `11`
- `dc2p-default-profile-net-ruijie` 当前值为：
  - `contract_key = ruijie_ruijie`
  - `dataset_keys_json = ["snmp_sys_descr","snmp_if_table","cli_lldp_neighbors"]`
  - `scope_json.mib_tree_file = /home/ubuntu/project/quick_env/init-data/mib_tree.json`

### Nacos 主文件

- 已发布 [2026-05-26_luzhou_cipher-aes-start-config.backfeed_from_local.yaml](./nacos/2026-05-26_luzhou_cipher-aes-start-config.backfeed_from_local.yaml)
- 发布后回读文件与目标文件 `SHA256` 完全一致
- 说明：
  - `device_collection2` 已按 `local` 反哺
  - `attentions` 已按 `local` 反哺
  - `observationMIB` 以及环境相关字段仍保留 `luzhou`

### Candidate Engine

- 已发布 [2026-05-26_luzhou_device_v2_candidate_engine.backfeed_from_local.yaml](./nacos/2026-05-26_luzhou_device_v2_candidate_engine.backfeed_from_local.yaml)
- 发布后回读文件与目标文件 `SHA256` 完全一致
- 已确认包含：
  - `ruijie_vendor_backfill`
  - `Ruijie / RGOS -> Ruijie` 平台识别
  - 锐捷相关 `catalog` 判型规则

## 校验结论

- 本次 MySQL 回灌执行成功
- 本次 Nacos 两个 dataId 发布成功
- Nacos 发布后回读内容与目标文件字节级一致
- 回读文件均可按 `UTF-8` 正常解码，本次未引入乱码

## 本次没有做的事

- 没有覆盖 `luzhou` 运行态数据
  - `fact`
  - `run`
  - `collection_run`
  - `processing_run`
  - `snapshot_workflow`
- 没有整份覆盖 `cipher-aes-start-config`
  - 避免误伤 `luzhou` 的环境连接信息
