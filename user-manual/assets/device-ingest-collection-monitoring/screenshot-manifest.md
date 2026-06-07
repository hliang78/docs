# 设备入库、采集和监控纳管截图清单

本文记录用户手册需要的截图、截图来源、标注要求和发布状态。手册正文只引用 `annotated/` 下的标注图；`raw/` 下保留原图，便于后续重做标注。

## 标注规则

- 每张截图保留原图和标注图。
- 标注图用红框突出关键按钮、菜单、状态或字段。
- 同一张图最多标 3 个点；超过 3 个点时拆成多张图。
- 编号从左到右、从上到下排列。
- 不遮挡用户需要读取的状态和字段值。
- 发布前必须脱敏 IP、设备编码、账号、凭据引用、组织名和内部主机名。

## 后续补图规则

- 优先根据使用反馈补图。当使用者明确说“不知道点哪里”“不知道是否成功”“不知道失败后补什么”时，把该页面作为下一张候选截图。
- 每张新增截图必须能回答一个判断问题，例如“是否已入库”“是否已确认采集”“失败设备缺哪些字段”“监控任务是否可追踪”。
- 不为了覆盖所有按钮而补图。一个页面如果没有造成误解，暂不增加截图。
- 截图中不得出现密码、Community、Secret、完整凭据引用、客户文件名或可识别客户环境的信息。
- 新手反馈截图可先作为内部素材保留；发布到客户手册前必须重拍或脱敏，并再次检查页面文案是否适合客户阅读。

## 新手反馈补图优先级

| 优先级 | 页面/入口 | 截图时机 | 红框/编号标注 | 判断目的 | 状态 |
| --- | --- | --- | --- | --- | --- |
| P0 | 设备导入结果页 | 上传完成并看到入库统计后 | 1 已提交数量；2 已入库/可采集/需修改数量；3 查看设备清册入口 | 判断入库是否完成，以及是否能进入设备清单继续采集/监控 | 内部素材 15，待脱敏后发布 |
| P0 | 采集结果抽屉 | 采集任务返回失败或部分完成后 | 1 任务状态；2 成功/失败数量；3 失败说明 | 判断下一步是补资料、查凭据，还是联系管理员 | 内部素材 18，待脱敏后发布 |
| P0 | 监控结果页 | 监控结果出现待补资料后 | 1 推送状态；2 需补齐字段；3 去编辑入口 | 判断用户是否知道要补平台、设备类别等字段 | 内部素材 20，待脱敏后发布 |
| P1 | 设备清单页 | 从入库结果回到设备清单后 | 1 设备总数；2 目标设备行；3 批量采集/批量监控按钮 | 判断选中的是否是刚入库设备，以及下一步入口在哪里 | 内部素材 16，待脱敏后发布 |
| P1 | 批量采集确认弹窗 | 点击批量采集后、确认执行前 | 1 已选设备数量；2 影响范围；3 开始采集按钮 | 判断采集任务是否真的被确认创建 | 内部素材 17，待脱敏后发布 |
| P1 | 批量监控确认弹窗 | 点击批量监控后、确认执行前 | 1 将创建监控任务的设备数量；2 影响范围；3 开始监控按钮 | 判断监控任务是否真的被确认创建并保存到工作台 | 内部素材 19，待脱敏后发布 |
| P2 | 监控任务管理页 | 监控下发后进入任务管理 | 1 任务状态；2 同步状态；3 最近变更或详情入口 | 判断监控纳管是否可以被追踪 | 内部素材 21，待脱敏后发布 |

## 必需截图

| 序号 | 标注图 | 原图 | 页面/入口 | 截图时机 | 红框/编号标注 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 01 | `annotated/01-device-list-key-actions.png` | `raw/01-device-list-key-actions.png` | `/#/device/device-v2-management` | 设备清单加载完成 | 1 设备导入入口；2 搜索/筛选区；3 批量操作区 | 已标注 |
| 02 | `annotated/02-device-import-entry.png` | `raw/02-device-import-entry.png` | 设备清单“设备导入”入口 | 准备导入设备 | 1 入库页面位置；2 导入动作入口 | 已标注 |
| 03 | `annotated/03-device-list-filter.png` | `raw/03-device-list-filter.png` | `/#/device/device-v2-management` | 已添加查询条件 | 1 筛选条件；2 查询按钮；3 命中的设备行 | 已标注 |
| 04 | `annotated/04-single-device-collect-action.png` | `raw/04-single-device-collect-action.png` | `/#/device/device-v2-management` | 打开单设备操作菜单 | 1 目标设备；2 采集菜单项 | 已标注 |
| 05 | `annotated/05-collection-confirm-modal.png` | `raw/05-collection-confirm-modal.png` | 设备清单采集确认弹窗 | 点击单设备采集后 | 1 采集确认；2 开始采集按钮 | 已标注 |
| 06 | `annotated/06-collection-result-drawer.png` | `raw/06-collection-result-drawer.png` | 采集结果抽屉 | 采集任务创建后 | 1 结果状态；2 证据操作；3 结果摘要 | 已标注 |
| 07 | `annotated/07-single-device-monitor-action.png` | `raw/07-single-device-monitor-action.png` | `/#/device/device-v2-management` | 打开单设备操作菜单 | 1 目标设备；2 监控菜单项 | 已标注 |
| 08 | `annotated/08-monitor-result-workbench.png` | `raw/08-monitor-result-workbench.png` | 设备清单批量任务工作台 | 监控下发任务创建后 | 1 结果操作；2 批量任务工作台 | 已标注 |
| 09 | `annotated/09-monitoring-task-list.png` | `raw/09-monitoring-task-list.png` | `/#/platform/monitoring-tasks` | 监控任务列表加载完成 | 1 任务态势；2 筛选区；3 任务列表 | 已标注 |
| 10 | `annotated/10-monitoring-task-detail.png` | `raw/10-monitoring-task-detail.png` | `/#/platform/monitoring-tasks` | 打开任务诊断抽屉 | 1 任务详情；2 排障信息 | 已标注 |

## 可选截图

| 序号 | 标注图 | 原图 | 页面/入口 | 截图时机 | 红框/编号标注 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 11 | `annotated/11-batch-collect-confirm.png` | `raw/11-batch-collect-confirm.png` | `/#/device/device-v2-management` | 批量采集确认前 | 1 已选设备；2 批量采集；3 确认执行 | 可选 |
| 12 | `annotated/12-batch-monitor-confirm.png` | `raw/12-batch-monitor-confirm.png` | `/#/device/device-v2-management` | 批量监控确认前 | 1 已选设备；2 批量监控；3 确认执行 | 可选 |
| 13 | `annotated/13-edit-missing-monitor-fields.png` | `raw/13-edit-missing-monitor-fields.png` | 设备编辑抽屉 | 监控失败提示缺字段后 | 1 需补齐字段；2 保存后重新监控 | 可选 |
| 14 | `annotated/14-download-collection-log.png` | `raw/14-download-collection-log.png` | 采集结果抽屉或设备操作列 | 需要排障日志时 | 1 下载采集日志 | 可选 |

## 新手反馈截图

| 序号 | 标注图 | 原图 | 页面/入口 | 截图时机 | 红框/编号标注 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 15 | `annotated/15-novice-ingest-completion.png` | `raw/15-novice-ingest-completion.png` | `/#/device/device-v2-ingest-pipeline-redesign` | 入库任务完成后 | 1 下一步提示；2 已入清册/可采集数量；3 查看设备清册 | 内部素材，正文暂不引用 |
| 16 | `annotated/16-novice-batch-selection.png` | `raw/16-novice-batch-selection.png` | `/#/device/device-v2-management` | 勾选少量设备后 | 1 已选设备提示；2 批量采集；3 批量监控 | 内部素材，正文暂不引用 |
| 17 | `annotated/17-novice-batch-collect-confirm.png` | `raw/17-novice-batch-collect-confirm.png` | 批量采集确认弹窗 | 点击批量采集后、确认前 | 1 影响范围；2 开始采集；3 未确认不保存说明 | 内部素材，正文暂不引用 |
| 18 | `annotated/18-novice-collection-result.png` | `raw/18-novice-collection-result.png` | 采集结果抽屉 | 采集出现失败且仍有设备执行中 | 1 批量采集工作台；2 失败/执行数量；3 采集前探测处理建议 | 内部素材，正文暂不引用 |
| 19 | `annotated/19-novice-batch-monitor-confirm.png` | `raw/19-novice-batch-monitor-confirm.png` | 批量监控确认弹窗 | 点击批量监控后、确认前 | 1 影响范围；2 开始监控；3 未确认不保存说明 | 内部素材，正文暂不引用 |
| 20 | `annotated/20-novice-monitor-result.png` | `raw/20-novice-monitor-result.png` | 监控结果抽屉 | 监控下发提示待补资料后 | 1 推送状态；2 需补齐字段；3 去编辑 | 内部素材，正文暂不引用 |
| 21 | `annotated/21-novice-monitoring-task-list.png` | `raw/21-novice-monitoring-task-list.png` | `/#/platform/monitoring-tasks` | 进入监控任务管理页 | 1 任务列表；2 任务状态；3 同步状态/详情入口 | 内部素材，正文暂不引用 |

## 发布检查

- [x] 必需截图 01-10 已有标注图。
- [x] 所有标注图已使用手册演示设备和保留地址，未包含凭据。
- [x] 手册正文的图片引用都指向 `annotated/` 目标文件。
- [x] 新手反馈截图 15-21 已标为内部素材，正文暂不引用。
- [x] 未完成截图在复核文件中标为发布阻塞项；当前无必需截图阻塞项。
