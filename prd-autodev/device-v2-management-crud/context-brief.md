---
topic: device-v2-management-crud
kind: frontend
title: Device V2 管理页 CRUD 优化
updatedAt: 2026-05-21T18:30:00+0800
status: research
---

# Context Brief

## 用户原始诉求

- 继续优化 `DeviceV2ManagementGrouped.vue`。
- 当前页面已经增加采集、监控等能力，但设备以及设备相关关键因素的增删改查没有处理完整。
- 按 `prd-autodev-loop` 的方式先研究、对齐、形成 PRD，再直接在当前 Codex 会话中实现。
- 当前回合不通过自动化框架。

## 当前真实代码事实

### 1. 管理页并非完全没有 CRUD，但闭环不完整

- 页面文件是 [DeviceV2ManagementGrouped.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue)。
- 当前页已经接入：
  - `listDeviceV2Req`
  - `getDeviceV2Req`
  - `updateDeviceV2Req`
  - `deleteDeviceV2Req`
  - `startDeviceV2StorePipelineReq`
  - `syncDeviceV2ToV1Req`
- 当前页已经支持：
  - 列表查询（仅关键词 + 监控状态 + 分组）
  - 单台详情
  - 编辑设备
  - 批量删除
  - 批量采集
  - 批量监控
  - 分组配置
- 当前页尚未支持或支持不足：
  - 手工新增设备入口
  - 更细粒度的关键因素筛选
  - 单台删除显式入口
  - 删除时对 V1 联动影响的表达
  - 导入来源与关键因素补齐之间的清晰承接

### 2. 当前“编辑设备”更像补录表单，不像完整设备管理工作台

- 编辑弹窗已覆盖：
  - 基础信息：名称、平台、设备类别、状态
  - 位置与归属：租户、区域、机房、机架
  - 动态属性：SchemaForm
  - 标签、分组标签、元数据
- 但现有设计更偏“打开后一次性补很多字段”，不够强调：
  - 哪些字段是纳管关键因素
  - 哪些字段影响采集
  - 哪些字段影响监控同步到 V1
  - 哪些字段只是补充信息

### 3. 导入页已经是本轮更合适的“新增入口”

- 页面文件是 [DeviceV2IngestPipelineRedesign.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2IngestPipelineRedesign.vue)。
- 当前导入页已支持：
  - Excel 上传
  - 手工添加草稿行
  - 历史导入批次加载
  - 草稿编辑
  - 草稿校验
  - 提交到 Device V2 清册
- 当前草稿“可纳管”判断逻辑：
  - 带内 IP + 任一凭据
  - 或带外 IP + 带外凭据
- 当前草稿问题判断逻辑主要关注：
  - 缺少身份定位字段
  - 重复身份字段
  - 状态值非法
- 也就是说：
  - 导入页已经在做“创建前工作台”
  - 但它对“后续为什么能采集、能监控、能分组、能删除联动”表达还不够

### 4. 导入字段很多，但关键因素没有被明确分层

- 当前导入映射已承接的字段不止位置类字段，还包括：
  - 身份类：`code` `biz_code` `hostname` `sn` `asset_number`
  - 网络接入类：`in_band_ip` `out_band_ip`
  - 凭据类：`credential_ref_in_band` `credential_ref_out_band` `snmp_credential_ref` `winrm_credential_ref`
  - 分类归属类：`platform_code` `catalog_code` `tenant/region/site/rack`
  - 资产与软硬件类：`vendor` `model` `system_version` `os_version` `cpu_model` `memory_total` 等
  - 来源溯源类：`source` `batch_id` `task_id` `run_id` `original_code`
- 但当前前端还没有把这些字段整理成稳定的“关键因素模型”：
  - 身份定位因子
  - 采集可达因子
  - 纳管同步因子
  - 分组展示因子
  - 资产归档因子
  - 来源追溯因子

### 5. 删除 Device V2 已补成“可选联动删 V1”

- 前端已有 `DELETE /device/v2/:code` 对应的 `deleteDeviceV2Req`。
- 当前仓库检索结果里能确认：
  - 存在 `POST /device/v2/sync-to-v1`
  - 存在 `POST /device/v2/sync-from-v1`
  - 存在 V1 bridge ensure 能力
- 当前已确认并已实现的删除契约：
  - V2 删除入口：`DELETE /device/v2/:code`
  - V1 独立删除入口：`DELETE /device/inventory/:code`
  - V2 删除新增可选参数：`DELETE /device/v2/:code?delete_v1=true`
- 当前行为：
  - 默认仍只删除 V2
  - 当 `delete_v1=true` 且设备已关联 `device_v1_code` 时，后端会继续调用 V1 独立删除接口对应的 service
  - 若 V2 已删除但 V1 删除失败，接口返回成功 envelope，并在 data 中明确返回 `device_v1_deleted=false` 与失败信息，供前端提示部分失败

## AI 推导建议

### 建议把“关键因素”显式拆成 6 组

1. 身份定位
- `code`
- `biz_code`
- `hostname`
- `sn`
- `asset_number`

2. 采集接入
- `in_band_ip`
- `out_band_ip`
- `credential_ref_in_band`
- `credential_ref_out_band`
- `snmp_credential_ref`
- `winrm_credential_ref`
- `winrm_port`

3. 纳管同步
- `platform_code`
- `catalog_code`
- `tenant_code`
- `region_code`
- `site_code`
- `rack_code`
- `device_v1_code`

4. 分组与检索
- `group_tags`
- 常用 `labels`
- 用于分层的核心 attributes

5. 资产与设备事实
- `vendor`
- `model`
- `device_kind`
- `rack_position`
- `system_version`
- `os_version`
- `cpu_model`
- `memory_total`

6. 来源与追溯
- `source`
- `batch_id`
- `task_id`
- `run_id`
- `original_code`

### 建议把这轮优化拆成两个前端工作面

1. 导入页优化
- 目标：让用户在提交前就知道哪些设备只是“能登记”，哪些已经“具备采集/监控前置条件”，哪些关键因素缺失。

2. 管理页优化
- 目标：让用户在入库后能快速筛选、补齐、删除、追踪关键因素，而不是只看到一张能采集/监控的设备表。

## 规划缺口

- 用户尚未最终确认“关键因素”范围。
- 暂未确认“同步删 V1”的后端能力是否存在。
- 暂未确认本轮是否需要把导入页的“手工新增一台设备”保留、弱化，还是直接隐藏。

## 当前建议的下一步对齐项

1. 先确认“关键因素”的最终分组，尤其是：
- 是否把身份、接入、纳管、资产、来源都算进来
- 是否把 `device_v1_code` 视为关键因素之一

2. 再确认删除策略：
- 仅删除 V2
- 删除 V2 时可勾选同步删 V1
- 仅当设备已绑定 `device_v1_code` 时才展示同步删 V1

3. 方向确认后，进入 PRD 和代码实现：
- 导入页先做关键因素工作台
- 管理页再做关键因素筛选、展示、补齐和删除闭环
