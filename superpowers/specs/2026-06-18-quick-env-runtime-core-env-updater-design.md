# Quick Env Runtime Core / Env Updater 设计

> 日期：2026-06-18
> 范围：Quick Env 简化与在线更新重构
> 状态：设计待用户评审

---

## 1. 目标

本期目标不是继续扩张 `quick_env`，而是把它收敛成一个更容易理解、更容易维护、且更适合在线环境更新的体系。

本设计的核心目标：

- 保留当前主线调试所需的最小基础运行面。
- 把“启动环境”和“更新业务能力”彻底分离。
- 明确整理在线更新涉及的三类介质：
  - `mysql`
  - `nacos`
  - `record_rule`
- 支持两种更新粒度：
  - 功能集整体更新
  - 功能集内子模块更新
- 对现有 `quick_env` 在线实例提供部分兼容能力，不要求一次性全部迁走。

本期设计默认优先服务于：

- 在线环境更新更简单。
- quick env 结构更简单。
- 维护者更容易定位“运行问题”和“业务种子问题”分别在哪一层。

---

## 2. 设计结论

不建议继续把 `quick_env` 演进成一个更大的单体脚本集合。

推荐把它收敛成两层：

1. `runtime-core`
2. `env-updater`

### 2.1 runtime-core

`runtime-core` 只负责最小基础运行面：

- `mysql`
- `nacos`
- `victoria-metrics`
- `vmalert`
- `minio`
- `vault`

`runtime-core` 的职责是：

- 起基础服务。
- 渲染最小运行时配置。
- 暴露稳定的运行时目标信息。

`runtime-core` 不再承担：

- 业务 seed 导入。
- 在线补同步。
- 厂商能力拼装。
- 启动后顺手改业务表、改 dashboard、改 subject 绑定。

### 2.2 env-updater

`env-updater` 只负责业务能力更新：

- `mysql` 幂等 seed
- `nacos` patch 合并
- `record_rule` group 合并与 reload

`env-updater` 按 bundle/module 组织，既支持：

- 整个功能集更新
- 单个子模块更新

---

## 3. 范围边界

### 3.1 本期保留

本设计默认保留的基础运行能力：

- `MySQL`
- `Nacos`
- `VictoriaMetrics / vmalert`
- `MinIO`
- `Vault`

这几项构成 quick env 的最小 MVP 运行面。

### 3.2 本期不保留为 v2 核心

以下能力不作为 `runtime-core` 的核心组成：

- `Gitea`
- 本地一体化 `oneops-core` 运行能力
- 大量历史辅助脚本
- 启动链路中的业务级补同步逻辑

这些能力后续如需保留，也应作为附加层处理，而不是继续混入运行核心层。

### 3.3 厂商能力边界

厂商能力不单列横向包。

厂商差异必须内聚在业务功能集内部，主要落在：

- `device-discovery`
- `snmp-observability`
- `alerting-and-record-rules`

例如：

- `device-discovery/h3c`
- `snmp-observability/h3c`

而不是再引入单独的 `vendor-packs` 概念。

---

## 4. 目录结构

建议目录逐步收敛为：

```text
quick_env/
  runtime-core/
    compose/
    configs/
    templates/
    scripts/
  env-updater/
    bundles/
      base-core/
        bundle.yaml
        modules/
      device-discovery/
        bundle.yaml
        modules/
      snmp-observability/
        bundle.yaml
        modules/
      alerting-and-record-rules/
        bundle.yaml
        modules/
    adapters/
    scripts/
    state/
  compat/
    migrate-v1-runtime.sh
    import-v1-instance.sh
```

目录职责：

- `runtime-core/`：基础服务运行层
- `env-updater/bundles/`：业务能力更新定义
- `env-updater/adapters/`：目标环境适配
- `env-updater/state/`：更新记录、计划产物、执行状态
- `compat/`：迁移与过渡工具

---

## 5. Bundle / Module 模型

### 5.1 顶层功能集

本期推荐的 bundle 为：

- `base-core`
- `device-discovery`
- `snmp-observability`
- `alerting-and-record-rules`

### 5.2 更新粒度

系统必须同时支持两种粒度：

- bundle 级更新
- module 级更新

例如：

- 更新整个 `snmp-observability`
- 只更新 `snmp-observability/h3c`

### 5.3 bundle 清单

示例：

```yaml
api_version: quickenv/v2
kind: Bundle
name: snmp-observability

surfaces:
  - mysql
  - nacos
  - record_rule

modules:
  - name: common
    path: modules/common/module.yaml
  - name: h3c
    path: modules/h3c/module.yaml
    depends_on:
      - common
  - name: huawei
    path: modules/huawei/module.yaml
    depends_on:
      - common
```

### 5.4 module 清单

示例：

```yaml
api_version: quickenv/v2
kind: Module
name: snmp-observability/h3c

surfaces:
  mysql: required
  nacos: required
  record_rule: optional

mysql:
  schema: UniOPS
  files:
    - mysql/strategy.sql
    - mysql/dashboard.sql
    - mysql/binding.sql

nacos:
  patches:
    - data_id: cipher-aes-start-config
      file: nacos/cipher-aes-start-config.patch.yaml

record_rule:
  groups:
    - name: oneops_snmp_recording_rules
      file: record-rules/h3c-group.yaml
```

### 5.5 surface 显式声明规则

每个 module 都必须声明三类 surface 的适用性：

- `mysql`
- `nacos`
- `record_rule`

允许值：

- `required`
- `optional`
- `not_applicable`

约束：

- 不能省略某个 surface。
- `record_rule` 不是每个模块都必须有内容。
- 若为 `not_applicable`，则该块不得隐式修改对应目标。

这条规则的目的，是避免“模块实际上会改 Nacos 或 rule，但清单没有写出来”的隐性复杂度。

---

## 6. 三类更新介质规则

### 6.1 MySQL

`mysql` 更新必须使用幂等 seed SQL。

要求：

- 不使用整库 dump 覆盖在线环境。
- 尽量使用幂等写法，例如存在性判断、条件更新、可重复执行 insert/upsert。
- 一个 module 可声明多份 SQL，但都必须显式列出。

适用场景：

- 策略、策略集、dashboard、binding 等业务种子
- 发现侧业务定义与静态基线

### 6.2 Nacos

`nacos` 更新以 `dataId` 为最小变更单元，但更新方式应为结构化 patch 合并，而不是简单整份覆盖。

要求：

- patch 必须明确命中哪个 `dataId`。
- patch 只更新本模块负责的配置片段。
- 避免覆盖运行时地址、端口、token、实例渲染值等环境专属内容。

适用场景：

- `cipher-aes-start-config`
- `device_v2_candidate_engine`
- `device_collection2_contracts`

### 6.3 Record Rule

`record_rule` 更新以 rule group 为最小变更单元。

要求：

- 不要求每个 module 都有 rule group。
- 有 rule 的 module 必须显式声明受管 group。
- 更新动作应合并到运行中的 `vmalert-rule.yml`，而不是让每个模块维护一份完整总文件。
- 合并后统一触发 reload。

适用场景：

- `snmp-observability` 内需要新增或调整录制规则的模块
- `alerting-and-record-rules` 内与 vmalert group 直接相关的模块

---

## 7. 命令模型

推荐拆分为两套入口：

### 7.1 runtime-core

```bash
quick_env/runtime-core/up.sh
quick_env/runtime-core/down.sh
quick_env/runtime-core/status.sh
```

### 7.2 env-updater

```bash
quick_env/env-updater/update.sh plan <bundle|bundle/module>
quick_env/env-updater/update.sh apply <bundle|bundle/module>
quick_env/env-updater/update.sh verify <bundle|bundle/module>
quick_env/env-updater/update.sh rollout <bundle|bundle/module>
```

说明：

- `plan`：只预览，不落变更
- `apply`：执行更新
- `verify`：验证结果
- `rollout`：内部顺序固定为 `plan -> apply -> verify`

---

## 8. 计划、执行、验证三阶段

### 8.1 plan

`plan` 阶段必须输出：

- 目标 bundle/module
- 依赖模块
- 目标 `mysql` schema 与 SQL 文件
- 目标 `nacos` dataId
- 目标 `record_rule` group
- 风险提示

`plan` 不允许落任何线上变更。

### 8.2 apply

`apply` 固定顺序：

1. `mysql`
2. `nacos`
3. `record_rule`

要求：

- 任一步失败即停。
- 不把“部分成功”视为整体成功。
- 必须写本地执行记录。

执行记录至少包括：

- 时间
- 目标环境
- bundle/module
- 执行文件列表
- 成功/失败
- reload 结果

### 8.3 verify

`verify` 必须验证真实结果，而不是只看命令退出码。

至少包含：

- `mysql`：关键记录检查
- `nacos`：回读 `dataId` 检查
- `record_rule`：最终 rule 文件包含目标 group，且 reload 成功

---

## 9. 目标环境适配

由于本设计选择“部分兼容”现有在线环境，因此 `env-updater` 必须通过 adapter 访问目标环境，而不是与某种目录结构写死绑定。

adapter 至少需要解析三类信息：

- MySQL 连接信息
- Nacos 连接信息
- `vmalert-rule.yml` 路径与 reload URL

支持两类目标：

1. `quick_env v2 runtime`
2. 现有 `quick_env` 在线实例或等价运行环境

示例：

```yaml
target:
  type: quickenv_v1_runtime
  instance: demo-a
```

或：

```yaml
target:
  type: explicit
  mysql:
    host: 10.0.0.1
    port: 3306
  nacos:
    base_url: http://10.0.0.2:8848
  record_rule:
    file: /data/vmalert/vmalert-rule.yml
    reload_url: http://10.0.0.3:8880/-/reload
```

---

## 10. 迁移顺序

推荐按四步迁移：

### 10.1 第一步：抽出 env-updater

先不重写整个 `quick_env`，先把现有散在：

- `start.sh`
- `docker-entrypoint-initdb.d/*.sql`
- `init-configs/nacos/*.yaml`
- `config/vmalert/vmalert-rule.yml`

中的业务更新逻辑整理成 bundle/module。

### 10.2 第二步：收敛 runtime-core

把现有真正属于基础运行面的内容收进 `runtime-core`，并去掉业务级补同步职责。

### 10.3 第三步：补齐 v1 adapter

让 updater 可直接作用于现有在线实例。

### 10.4 第四步：冻结旧同步入口

逐步下线旧 `start.sh` 中的 `sync_*` 逻辑，使“启动”和“更新”彻底分离。

---

## 11. 建议主动删除的复杂度

如果目标是“简洁、好维护”，以下模式不应继续进入新体系：

- 用一个超大 `start.sh` 同时承担启动、seed、补同步、兼容逻辑
- 启动完成后顺手改业务表
- 把“首次初始化”和“在线更新”混成同一条链路
- 让 `cipher-aes-start-config` 持续承载过多业务补丁
- 让 `record_rule` 同时扮演模板、运行态文件、发布记录三种角色

---

## 12. 第一阶段验收标准

第一阶段成功标准定义为：

- `runtime-core` 可独立启动最小基础运行面
- `env-updater` 可识别 bundle/module
- 每个 module 可明确回答：
  - 改哪些 `mysql`
  - 改哪些 `nacos`
  - 是否涉及 `record_rule`
- 现有一个在线实例可通过 adapter 被更新
- 至少以下模块可完整走通：
  - `device-discovery/common`
  - `device-discovery/h3c`
  - `snmp-observability/common`
  - `snmp-observability/h3c`
- 旧 `start.sh` 中至少一批 `sync_*` 逻辑被迁出，不再继续膨胀

---

## 13. 最终建议

本设计最终建议是：

- 不继续放大单体 `quick_env`
- 把 quick env 收敛成：
  - `runtime-core`
  - `env-updater`
- 用 bundle/module 驱动在线更新
- 用显式 surface 模型约束：
  - `mysql`
  - `nacos`
  - `record_rule`
- 厂商差异只存在于功能集内部模块，不再单列横向包

这套模型的收益是：

- 启动层稳定、少变
- 更新层显式、可审计
- 在线环境更新支持整体与局部两种粒度
- 维护者更容易理解哪些问题属于 runtime，哪些问题属于 seed/update
