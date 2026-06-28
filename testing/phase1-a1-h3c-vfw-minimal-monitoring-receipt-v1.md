# A1 H3C VFW 最小监控任务回执（待实测）

更新时间：2026-06-28  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目标

这份回执用于承接 `A1` 的第一条最小监控任务补证。

当前选择 `H3C VFW` 作为第一条执行对象，原因是：

1. 当前在线
2. 管理地址、SSH、身份回读已经实测通过
3. 当前 `A1` 真正缺口正是“最小监控任务”

上层依据：

1. [A1 最小监控任务补证标准](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-a1-minimal-monitoring-task-evidence.md)
2. [A1 逐设备标准回执](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-a1-per-device-standard-receipts.md)

## 2. 设备基线

1. 设备：`H3C-FW2`
2. 管理地址：`172.32.2.17`
3. 标准登录入口：`SSH`
4. 当前稳定口令：`admin / Admin@1234`
5. 当前已确认前置：
   - `ping` 可达
   - `TCP/22` 可达
   - SSH 可登录
   - 版本与运行时间可回读

## 3. 本次最小任务定义

第一条最小监控任务固定为：

1. 管理面存活 + 系统摘要采集

本轮不包含：

1. 大规模策略集
2. NAT/策略解析联动
3. 批量并发任务

## 4. 四层证据回执

### 4.1 平台计划层

待补字段：

1. 使用的监控模板或任务类型：
2. 计划编译结果：
3. 计划应用结果：
4. 若失败，失败原因：

### 4.2 平台任务层

待补字段：

1. 监控任务 ID：
2. 目标设备编码/名称：
3. 任务状态：
4. 是否能在监控任务管理页看到：
5. 若失败，失败原因：

### 4.3 Agent 运行层

待补字段：

1. Agent 编码：
2. Agent 能力匹配结果：
3. Agent 侧任务存在性：
4. Agent 侧任务状态：
5. 若失败，失败原因：

### 4.4 目标结果层

待补字段：

1. 第一条有效数据时间：
2. 第一条有效数据内容：
3. 是否可解释为“系统摘要已回收”：
4. 若失败，失败原因：

## 5. 通过标准

只有下面 4 条都成立，才能记为通过：

1. 平台计划成功
2. 平台任务可见
3. Agent 侧任务存在
4. 目标结果层出现至少一条有效数据

如果只到平台任务层，应记为：

1. 任务已创建，但未证明生效

如果只到 Agent 运行层，应记为：

1. 任务已下发，但未证明采到有效数据

## 6. 当前状态

截至 `2026-06-28`，当前状态应记为：

1. 回执框架已建立
2. 设备接入前置已满足
3. 最小监控任务尚未实测

## 7. 实测后回写位置

实测完成后，至少同步回写到：

1. [A1 单设备接入基线回执（第一版）](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-a1-single-device-baseline-receipt-v1.md)
2. [A1 逐设备标准回执](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-a1-per-device-standard-receipts.md)
3. [EVE-NG H3C VFW 防火墙标准操作手册（草案）](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-h3c-vfw-firewall-standard-operation.md)
