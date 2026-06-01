---
topic: device-v2-management-ops-closure
kind: full-stack
title: Device V2 采集与监控错误协同模型
createdAt: 2026-05-21T12:52:00+0800
---

# Device V2 采集与监控错误协同模型

## 1. 核心定义

这次要建设的，不是“前端诊断系统”，而是“采集 / 继续纳管 / 监控推送链路的分层错误协同模型”。

前端不负责替后端或排障人员判定最终根因，但前端必须把后端返回的复杂失败承接成：

1. 用户能理解当前发生了什么
2. 用户知道失败停在哪一环
3. 用户知道下一步优先核对什么
4. 平台 / 开发能对齐同一组排障证据

## 2. 要避免的两种失败

### 2.1 生抛错误

表现：

- 原始后端错误直接展示
- controller / Vault / DC2 / V1 的技术细节原封不动压给用户

问题：

- 用户无法区分“技术现象”和“当前该做什么”
- 文案不稳定，前后端口径会不断漂移

### 2.2 吞掉错误

表现：

- 所有复杂失败都收敛成一句统一人话
- 不展示阶段，不展示优先核对项，不展示证据锚点

问题：

- 用户被误导去错误方向排查
- 平台和开发也难以从页面直接复现问题语境

## 3. 推荐的五层表达

### 层 1：结果层

回答：

- 这次到底成没成功

示例：

- `本次采集未完成`
- `本次继续纳管未完成`
- `本次监控推送未完成`

### 层 2：阶段层

回答：

- 卡在哪一环

推荐阶段集合：

- `prepare`
- `controller_detect`
- `dc2_run_collection`
- `persist_result`
- `sync_to_v1`
- `monitor_push`

前端不一定展示内部枚举值，但必须展示用户可理解的阶段名。

### 层 3：优先核对项

回答：

- 下一步先查什么

这里不要求前端给“最终诊断”，只要求给“当前优先核对项”。

示例：

- `优先核对正式链路使用的带内凭据引用`
- `优先核对接入目标地址与控制器可达性`
- `优先核对 V1 同步是否已成功生成目标设备`

### 层 4：证据锚点

回答：

- 排障时双方靠什么对齐

推荐锚点：

- `store_run_id`
- `dc2_run_id`
- `controller_stage`
- `reason_code`
- `credential_ref_in_band`
- `snapshot_id`
- `target_id`
- `contract_key`
- `route`

### 层 5：原始返回

回答：

- 需要更深排障时看什么

要求：

- 默认收起
- 不作为主说明
- 但必须可展开、可复制、可对照

## 4. 前后端职责边界

### 4.1 后端职责

后端应尽量稳定提供结构化失败事实，而不是只返回一段 `error`。

推荐最小字段：

- `status`
- `stage`
- `reason_code`
- `user_message`
- `operator_message`
- `next_check_items`
- `retryable`
- `evidence`
- `correlation_ids`

其中：

- `user_message` 用于业务层结论
- `operator_message` 用于排障补充
- `next_check_items` 用于前端展示“优先核对项”
- `evidence` 用于证据锚点

### 4.2 前端职责

前端负责：

- 统一渲染上述结构
- 把技术字段翻译成稳定的 UI 分层
- 做字段缺失时的降级

前端不负责：

- 推断最终根因
- 猜测后端没有明确返回的运行态
- 把偶然出现的原始 message 当成稳定契约

## 5. 当前链路的协同重点

### 5.1 采集链路

对采集失败，前端当前最需要协同的是：

- 不把“未成功执行 DC2”统一显示成“未发起 DC2”
- 不把 `controller_detect_failed` 直接翻译成“设备 SSH 不通”
- 在有 `credential_ref_in_band` 线索时，优先展示“正式链路接入配置”相关核对项

### 5.2 继续纳管 / 监控链路

对继续纳管失败，前端当前最需要协同的是：

- 不只弹 toast
- 把 `controller-backed` action evidence 稳定展示成页面内结果区
- 明确区分：
  - `sync_to_v1`
  - `monitor_push`
  - `controller-backed store/DC2`

## 6. 字段契约建议

若现有字段路径不稳定，建议后端考虑补一个统一结构，例如：

```json
{
  "status": "failed",
  "stage": "controller_detect",
  "reason_code": "controller_detect_failed",
  "user_message": "本次采集未完成。",
  "operator_message": "controller 未通过当前接入配置取到可识别数据。",
  "next_check_items": [
    "核对正式链路使用的 credential_ref_in_band",
    "确认目标地址与登录方式是否匹配当前设备"
  ],
  "retryable": true,
  "evidence": {
    "credential_ref_in_band": "vault_ssh_xxx",
    "target_id": "DVC631D6B2EB0FB",
    "snapshot_id": "snap-xxx",
    "dc2_run_id": "dc2-xxx",
    "store_run_id": "run-xxx",
    "route": "POST /api/v1/device/detect"
  }
}
```

这个结构不要求一步到位覆盖全链路，但应至少能覆盖：

- store 抽屉的采集失败承接
- 单设备继续纳管失败承接

## 7. 当前适合先落地的范围

第一批建议：

1. 先统一前端展示层级
2. 尽量复用当前已有字段
3. 用真实失败样本确认哪些字段路径稳定
4. 只对缺失最严重的点申请后端补充稳定字段

不建议第一批做的事：

1. 直接上“自动诊断”
2. 在前端写大量 hardcode 文案规则去猜后端隐含语义
3. 把页面扩成 controller / Vault 调试台

## 8. 与本轮 PRD 的关系

本模型对应 PRD 中最关键的新要求：

- `R9. 错误承接要分层协同`

它同时约束：

- 采集抽屉
- 单设备继续纳管结果承接
- 后端后续若需要补稳定字段时的契约边界
