# Device Ingest Collection Monitoring User Manual Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a repeatable OneOps user manual package for device import, device collection, and monitoring onboarding, including screenshot guidance, novice review, and a later skill extraction gate.

**Architecture:** Keep the manual as a small documentation package under `docs/user-manual/`. The main manual explains the customer path, the screenshot manifest controls visual evidence, and the review file records novice-readability and release checks. The reusable Codex skill is not created until the first manual flow has passed review.

**Tech Stack:** Markdown, existing OneOps UI routes, existing docs, existing Playwright/UX screenshots when current, optional manual screenshot annotation.

---

## File Structure

Create these files and directories:

```text
docs/user-manual/
  device-ingest-collection-monitoring.md
  device-ingest-collection-monitoring-review.md
  assets/
    device-ingest-collection-monitoring/
      screenshot-manifest.md
      raw/
      annotated/
```

Use these existing sources:

```text
docs/superpowers/specs/2026-06-07-device-ingest-collection-monitoring-user-manual-design.md
docs/development/device-v2-onboarding-observability/01-需求概要-OneOPS_DeviceV2纳管观测_v0.1.md
docs/development/device-v2-onboarding-observability/02-功能清单-OneOPS_DeviceV2纳管观测_v0.1.md
docs/productization/user-flows/CORE_FLOWS.md
OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue
OneOPS-UI/src/views/platform/MonitoringTaskManagement.vue
OneOPS-UI/src/views/platform/CollectionTargetManagement.vue
OneOPS-UI/src/router/utils.ts
OneOps/scripts/platform2_multi_agent_test/agents/device_v2_flexible_search.spec.ts
```

Do not document deprecated Device V2 onboarding APIs as user operations.

## Task 1: Create Manual Asset Directories

**Files:**
- Create directory: `docs/user-manual/assets/device-ingest-collection-monitoring/raw/`
- Create directory: `docs/user-manual/assets/device-ingest-collection-monitoring/annotated/`

- [ ] **Step 1: Create the asset directories**

Run:

```bash
mkdir -p docs/user-manual/assets/device-ingest-collection-monitoring/raw docs/user-manual/assets/device-ingest-collection-monitoring/annotated
```

Expected: command exits with status `0`.

- [ ] **Step 2: Verify the directories exist**

Run:

```bash
test -d docs/user-manual/assets/device-ingest-collection-monitoring/raw
test -d docs/user-manual/assets/device-ingest-collection-monitoring/annotated
```

Expected: both commands exit with status `0`.

## Task 2: Create Screenshot Manifest

**Files:**
- Create: `docs/user-manual/assets/device-ingest-collection-monitoring/screenshot-manifest.md`

- [ ] **Step 1: Write the manifest**

Create `docs/user-manual/assets/device-ingest-collection-monitoring/screenshot-manifest.md` with this content:

```markdown
# 设备入库、采集和监控纳管截图清单

本文记录用户手册需要的截图、截图来源、标注要求和发布状态。手册正文只引用 `annotated/` 下的标注图；`raw/` 下保留原图，便于后续重做标注。

## 标注规则

- 每张截图保留原图和标注图。
- 标注图用红框突出关键按钮、菜单、状态或字段。
- 同一张图最多标 3 个点；超过 3 个点时拆成多张图。
- 编号从左到右、从上到下排列。
- 不遮挡用户需要读取的状态和字段值。
- 发布前必须脱敏 IP、设备编码、账号、凭据引用、组织名和内部主机名。

## 必需截图

| 序号 | 标注图 | 原图 | 页面/入口 | 截图时机 | 红框/编号标注 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 01 | `annotated/01-device-list-key-actions.png` | `raw/01-device-list.png` | `/#/device/device-v2-management` | 设备清单加载完成 | 1 设备导入入口；2 搜索/筛选区；3 设备操作列 | 待截图 |
| 02 | `annotated/02-device-import-entry.png` | `raw/02-device-import-entry.png` | `/#/device/device-v2-management` 或 `/#/device/device-v2-ingest-pipeline-redesign` | 准备导入设备 | 1 设备导入按钮；2 导入页面标题或上传区 | 待截图 |
| 03 | `annotated/03-device-list-filter.png` | `raw/03-device-list-filter.png` | `/#/device/device-v2-management` | 已输入设备编码或 IP 条件 | 1 添加条件；2 查询按钮；3 命中的设备行 | 待截图 |
| 04 | `annotated/04-single-device-collect-action.png` | `raw/04-single-device-collect-action.png` | `/#/device/device-v2-management` | 打开单设备操作菜单 | 1 操作按钮；2 采集菜单项 | 待截图 |
| 05 | `annotated/05-collection-result-drawer.png` | `raw/05-collection-result-drawer.png` | 设备清单采集结果抽屉 | 采集任务返回结果 | 1 采集状态；2 设备采集结果表；3 查看详情或下载日志入口 | 待截图 |
| 06 | `annotated/06-structured-collection-result.png` | `raw/06-structured-collection-result.png` | 采集结果抽屉 | 打开结构化采集结果 | 1 当前设备结构化采集结果；2 报错或原始数据区域 | 待截图 |
| 07 | `annotated/07-single-device-monitor-action.png` | `raw/07-single-device-monitor-action.png` | `/#/device/device-v2-management` | 打开单设备操作菜单 | 1 操作按钮；2 监控菜单项 | 待截图 |
| 08 | `annotated/08-monitor-result-drawer.png` | `raw/08-monitor-result-drawer.png` | 设备清单监控结果抽屉 | 监控下发完成或失败 | 1 监控任务推送状态；2 失败需补齐字段；3 查看本次监控结果 | 待截图 |
| 09 | `annotated/09-monitoring-task-list.png` | `raw/09-monitoring-task-list.png` | `/#/platform/monitoring-tasks` | 监控任务列表加载完成 | 1 同步快照；2 任务状态；3 详情入口 | 待截图 |
| 10 | `annotated/10-monitoring-task-detail.png` | `raw/10-monitoring-task-detail.png` | `/#/platform/monitoring-tasks` | 打开监控任务详情 | 1 同步状态；2 最近下发；3 任务节点或运行态摘要 | 待截图 |

## 可选截图

| 序号 | 标注图 | 原图 | 页面/入口 | 截图时机 | 红框/编号标注 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 11 | `annotated/11-batch-collect-confirm.png` | `raw/11-batch-collect-confirm.png` | `/#/device/device-v2-management` | 批量采集确认前 | 1 已选设备；2 批量采集；3 确认执行 | 可选 |
| 12 | `annotated/12-batch-monitor-confirm.png` | `raw/12-batch-monitor-confirm.png` | `/#/device/device-v2-management` | 批量监控确认前 | 1 已选设备；2 批量监控；3 确认执行 | 可选 |
| 13 | `annotated/13-edit-missing-monitor-fields.png` | `raw/13-edit-missing-monitor-fields.png` | 设备编辑抽屉 | 监控失败提示缺字段后 | 1 需补齐字段；2 保存后重新监控 | 可选 |
| 14 | `annotated/14-download-collection-log.png` | `raw/14-download-collection-log.png` | 采集结果抽屉或设备操作列 | 需要排障日志时 | 1 下载采集日志 | 可选 |

## 发布检查

- [ ] 必需截图 01-10 已有标注图，或已在手册中保留明确的截图占位说明。
- [ ] 所有标注图都已脱敏。
- [ ] 手册正文引用路径都指向 `assets/device-ingest-collection-monitoring/annotated/`。
- [ ] 未完成截图在复核文件中标为发布阻塞项。
```

- [ ] **Step 2: Verify required screenshot rows exist**

Run:

```bash
rg -n "01-device-list-key-actions|10-monitoring-task-detail|发布检查" docs/user-manual/assets/device-ingest-collection-monitoring/screenshot-manifest.md
```

Expected: output includes all three searched strings.

## Task 3: Create Novice Review File

**Files:**
- Create: `docs/user-manual/device-ingest-collection-monitoring-review.md`

- [ ] **Step 1: Write the review file**

Create `docs/user-manual/device-ingest-collection-monitoring-review.md` with this content:

```markdown
# 设备入库、采集和监控纳管手册复核记录

本文用于复核 `device-ingest-collection-monitoring.md` 是否适合首次接触 OneOps 的客户使用。

## 新手可读性检查

| 检查项 | 结果 | 说明 |
| --- | --- | --- |
| 每章开头说明用户会完成什么 | 未检查 | 等手册初稿完成后填写 |
| 每个流程都有开始前确认 | 未检查 | 等手册初稿完成后填写 |
| 每一步写清页面、按钮、字段和成功状态 | 未检查 | 等手册初稿完成后填写 |
| 没有只写“配置相关参数”这类泛化表达 | 未检查 | 等手册初稿完成后填写 |
| 每个主操作都有用户可见的成功标准 | 未检查 | 等手册初稿完成后填写 |
| 失败路径写清错误在哪里、先检查什么 | 未检查 | 等手册初稿完成后填写 |
| 必做步骤和可选能力已分开 | 未检查 | 等手册初稿完成后填写 |
| 单设备和批量操作的选择建议清楚 | 未检查 | 等手册初稿完成后填写 |
| 术语第一次出现时有短解释 | 未检查 | 等手册初稿完成后填写 |
| 主流程可以从头走到尾，不依赖跳读 | 未检查 | 等手册初稿完成后填写 |
| 截图出现在新手容易迷路的位置 | 未检查 | 等手册初稿完成后填写 |
| 完成检查能确认入库、采集、监控、任务状态 | 未检查 | 等手册初稿完成后填写 |

## 截图发布检查

| 检查项 | 结果 | 说明 |
| --- | --- | --- |
| 必需截图 01-10 已列入 manifest | 已通过 | 见 `assets/device-ingest-collection-monitoring/screenshot-manifest.md` |
| 必需截图 01-10 已有标注图 | 未检查 | 没有本地环境时可先保留占位，但发布前必须补齐 |
| 标注图没有遮挡关键状态或字段 | 未检查 | 等截图完成后填写 |
| 标注图已脱敏 | 未检查 | 发布前必须确认 |
| 手册正文只引用 `annotated/` 图片 | 未检查 | 等手册初稿完成后填写 |

## Humanizer 复核

| 检查项 | 结果 | 说明 |
| --- | --- | --- |
| 删除开发文档腔和宣传腔 | 未检查 | 等手册初稿完成后填写 |
| 删除空泛表达，例如“完整闭环”“提升效率” | 未检查 | 等手册初稿完成后填写 |
| 保留短句和具体操作 | 未检查 | 等手册初稿完成后填写 |
| 没有把内部实现词写成用户必须理解的概念 | 未检查 | 等手册初稿完成后填写 |

## 发布阻塞项

当前发布阻塞项：

- 必需截图尚未实际采集和标注。
- 手册正文尚未完成。
- 新手可读性检查尚未执行。
- `humanizer` 复核尚未执行。
```

- [ ] **Step 2: Verify review sections exist**

Run:

```bash
rg -n "新手可读性检查|截图发布检查|Humanizer 复核|发布阻塞项" docs/user-manual/device-ingest-collection-monitoring-review.md
```

Expected: output includes all four section titles.

## Task 4: Create the Main Manual Skeleton

**Files:**
- Create: `docs/user-manual/device-ingest-collection-monitoring.md`

- [ ] **Step 1: Write the manual skeleton with concrete first-draft content**

Create `docs/user-manual/device-ingest-collection-monitoring.md` with this structure:

```markdown
# 设备入库、采集和监控纳管使用手册

这份手册带你完成一台设备从进入 OneOps，到采集设备信息，再到下发监控任务的主流程。第一次使用时，建议先按单台设备走通，再使用批量操作。

## 1. 新手先看：这三件事分别是什么

你会完成什么：
先分清入库、采集和监控纳管三件事，避免把“设备出现在列表里”误认为“已经开始监控”。

开始前确认：
- 你可以登录 OneOps。
- 你知道要接入哪一台设备。

操作步骤：
1. 先把设备入库。入库表示 OneOps 有了这台设备的资产记录。
2. 再执行采集。采集表示 OneOps 去读取设备信息，例如基础属性、接口信息或配置摘要。
3. 最后执行监控纳管。监控纳管表示平台把监控任务下发到可用的执行目标，让设备进入监控范围。

怎么看是否成功：
- 设备入库后，你能在设备清单中找到这台设备。
- 采集成功后，你能看到采集结果、采集时间或结构化结果。
- 监控纳管成功后，你能看到监控下发结果，并能在监控任务管理里追踪任务状态。

如果失败：
- 不要先刷新很多次。先打开结果抽屉或任务详情，看失败原因。
- 常见原因是设备信息不完整、凭据不正确、网络不通、设备类型或平台字段缺失。

## 2. 准备设备资料

你会完成什么：
准备好后续入库、采集和监控需要用到的设备信息。

开始前确认：
- 你知道设备名称或设备编码。
- 你知道设备 IP，至少有一个可访问地址。
- 你知道设备类型，例如服务器、交换机、路由器、防火墙或通用设备。
- 如果需要采集，你已经准备好登录凭据或 SNMP 信息。
- 如果需要监控，你知道这台设备应该归属哪个区域、分组或标签。

操作步骤：
1. 把设备基础信息整理到一处：设备名称、设备编码、IP、设备类型、平台、所属组织或分组。
2. 把访问方式整理清楚：SSH、SNMP、Agent 或其它方式。
3. 确认凭据只保存在平台允许的位置，不要把密码写进手册、备注或截图。

怎么看是否成功：
- 你能回答“这台设备用哪个地址访问”“属于哪类设备”“用什么方式采集”。

如果失败：
- 缺 IP 或凭据时，先不要继续采集。
- 缺设备类型时，可以先作为通用设备入库，但后续监控模板可能需要补齐类型信息。

## 3. 导入或创建设备

你会完成什么：
把设备加入 OneOps，并能在设备清单中看到它。

开始前确认：
- 已准备好设备基础信息。
- 你有设备管理权限。

操作步骤：
1. 打开 `/#/device/device-v2-management`。
2. 点击“设备导入”。
3. 按页面提示填写或上传设备信息。
4. 提交后回到设备清单。

截图：
![设备清单中的设备导入入口](assets/device-ingest-collection-monitoring/annotated/02-device-import-entry.png)

怎么看是否成功：
- 设备清单中能搜索到这台设备。
- 列表中显示设备编码、名称、平台或 IP 等基础信息。

如果失败：
- 先查看页面提示的失败原因。
- 如果是必填字段缺失，补齐设备编码、IP、设备类型或平台字段后再提交。
- 如果是重复设备，先确认是否已经存在，不要重复创建。

## 4. 在设备清单中找到设备

你会完成什么：
用搜索或筛选找到刚入库的设备，并确认它是下一步要操作的目标。

开始前确认：
- 设备已经提交入库。
- 你知道设备编码、名称或 IP 中的至少一个。

操作步骤：
1. 打开 `/#/device/device-v2-management`。
2. 在查询区域添加设备编码、名称或 IP 条件。
3. 点击“查询”。
4. 在结果列表中确认设备信息。

截图：
![用设备编码或 IP 查询设备](assets/device-ingest-collection-monitoring/annotated/03-device-list-filter.png)

怎么看是否成功：
- 列表中只出现目标设备，或目标设备在结果中清楚可见。

如果失败：
- 换用设备编码、IP、名称分别查询。
- 如果仍然查不到，回到导入结果确认设备是否提交成功。

## 5. 执行设备采集

你会完成什么：
对单台设备发起采集，让平台读取这台设备的可用信息。

开始前确认：
- 设备在清单中可见。
- 设备 IP、平台、设备类型和凭据已经尽量补齐。
- 网络和端口允许平台或执行目标访问设备。

操作步骤：
1. 在设备清单中找到目标设备。
2. 点击该行的“操作”。
3. 点击“采集”。
4. 等待采集结果抽屉打开或任务状态刷新。

截图：
![从单台设备操作菜单发起采集](assets/device-ingest-collection-monitoring/annotated/04-single-device-collect-action.png)

怎么看是否成功：
- 采集结果中显示成功、完成时间或结构化采集结果。

如果失败：
- 打开采集结果抽屉查看失败说明。
- 先检查凭据、网络连通性、端口和设备类型。

## 6. 查看采集结果和采集日志

你会完成什么：
确认采集是否完成，并知道失败时去哪里看详情。

开始前确认：
- 已经发起过采集。

操作步骤：
1. 查看采集结果抽屉中的设备采集结果。
2. 如果有“查看详情”，点击后查看当前设备的结构化采集结果。
3. 如果需要排障，下载采集日志。

截图：
![查看采集结果和日志入口](assets/device-ingest-collection-monitoring/annotated/05-collection-result-drawer.png)

怎么看是否成功：
- 你能看到采集状态、采集时间、协议或结果说明。
- 有结构化结果时，可以看到平台整理后的设备信息。

如果失败：
- 先读错误说明，不要只看“失败”两个字。
- 如果错误指向凭据，修正凭据后重新采集。
- 如果错误指向网络或超时，先确认设备地址、端口和访问路径。

## 7. 执行监控纳管

你会完成什么：
对设备发起监控下发，让它进入平台监控范围。

开始前确认：
- 设备已经入库。
- 建议先完成一次采集。
- 平台、设备类别、机房、机架等监控所需字段已经尽量补齐。

操作步骤：
1. 在设备清单中找到目标设备。
2. 点击该行的“操作”。
3. 点击“监控”。
4. 等待监控结果抽屉打开。

截图：
![从单台设备操作菜单发起监控](assets/device-ingest-collection-monitoring/annotated/07-single-device-monitor-action.png)

怎么看是否成功：
- 监控结果显示已下发或没有新增任务需要下发。
- 设备的监控下发状态变为已下发。

如果失败：
- 查看监控结果中的“需补齐字段”。
- 按提示编辑设备，补齐平台、设备类别、机房、机架等字段后再重新监控。

## 8. 查看监控下发结果

你会完成什么：
判断本次监控动作是否真的完成，以及是否有设备需要补充信息。

开始前确认：
- 已经发起过监控。

操作步骤：
1. 查看监控结果抽屉。
2. 阅读监控任务推送状态。
3. 如果表格中有失败设备，查看“需补齐字段”和说明。
4. 如果页面提供“去编辑”，点击后补齐字段并保存。

截图：
![查看监控下发结果](assets/device-ingest-collection-monitoring/annotated/08-monitor-result-drawer.png)

怎么看是否成功：
- 结果中显示监控下发完成。
- 失败列表为空，或失败原因已经处理。

如果失败：
- 缺字段时先补字段。
- 找不到可用执行目标或 Agent 时，联系平台管理员确认区域、Agent 和采集能力配置。

## 9. 在监控任务管理中确认状态

你会完成什么：
从任务视角确认监控任务的同步状态、最近下发时间和运行态信息。

开始前确认：
- 已经执行过监控纳管。

操作步骤：
1. 打开 `/#/platform/monitoring-tasks`。
2. 在监控任务列表中查找相关任务。
3. 查看任务状态、同步状态和最近下发时间。
4. 打开任务详情，查看任务节点或运行态摘要。

截图：
![在监控任务管理中查看任务状态](assets/device-ingest-collection-monitoring/annotated/09-monitoring-task-list.png)

怎么看是否成功：
- 任务列表中能看到相关任务。
- 任务详情中能看到同步状态和最近下发时间。

如果失败：
- 如果任务只存在平台侧，优先重新下发或执行对账。
- 如果任务只存在运行态，先确认来源，再决定是否删除或修复。

## 10. 批量操作怎么用

你会完成什么：
知道什么时候使用批量采集或批量监控，以及如何降低误操作风险。

开始前确认：
- 你已经用单台设备走通过入库、采集和监控。
- 批量设备的类型、平台、凭据和网络条件相近。

操作步骤：
1. 在设备清单勾选多台设备。
2. 点击“批量采集”或“批量监控”。
3. 查看确认信息，确认影响范围。
4. 执行后回到批量任务工作台查看结果。

怎么看是否成功：
- 批量任务工作台显示当前批量任务状态。
- 每台设备有自己的结果，不需要猜是哪一台失败。

如果失败：
- 先处理失败设备，不要重复执行全部设备。
- 批量失败数量较多时，先选一台失败设备按单台流程排查。

## 11. 常见问题

### 设备已经入库，为什么还不能监控？

入库只表示平台有了设备资产记录。监控还需要平台、设备类别、访问方式、执行目标或 Agent 等条件。

### 采集失败先查什么？

先查凭据、网络、端口和设备类型。大多数采集失败都和这些信息有关。

### 监控结果提示缺少字段怎么办？

点击设备编辑，按提示补齐字段，保存后重新执行监控。

### 为什么建议先单台走通，再做批量？

单台流程更容易定位问题。单台成功后，再批量操作可以减少大面积失败。

## 12. 完成检查清单

- [ ] 设备已经出现在设备清单中。
- [ ] 可以通过设备编码、名称或 IP 找到设备。
- [ ] 已经执行过一次采集，并能看到采集结果或失败原因。
- [ ] 已经执行过监控，并能看到监控下发结果。
- [ ] 能在监控任务管理中查看任务状态。
- [ ] 失败设备有明确下一步处理动作。
```

- [ ] **Step 2: Verify the manual has all required chapters**

Run:

```bash
rg -n "^## (1|2|3|4|5|6|7|8|9|10|11|12)\\." docs/user-manual/device-ingest-collection-monitoring.md
```

Expected: 12 chapter headings are printed.

## Task 5: Mark Screenshot Placeholders in Review File

**Files:**
- Modify: `docs/user-manual/device-ingest-collection-monitoring-review.md`

- [ ] **Step 1: Update the release blockers after skeleton creation**

Replace the `当前发布阻塞项` list with:

```markdown
当前发布阻塞项：

- 必需截图 01-10 尚未实际采集和标注。
- 手册正文仍使用截图占位路径，发布前必须补齐 `annotated/` 图片。
- 新手可读性检查尚未执行。
- `humanizer` 复核尚未执行。
```

- [ ] **Step 2: Verify screenshot blockers are explicit**

Run:

```bash
rg -n "必需截图 01-10|截图占位路径|humanizer" docs/user-manual/device-ingest-collection-monitoring-review.md
```

Expected: output includes the three searched phrases.

## Task 6: Run Structure and Link Checks

**Files:**
- Verify: `docs/user-manual/device-ingest-collection-monitoring.md`
- Verify: `docs/user-manual/assets/device-ingest-collection-monitoring/screenshot-manifest.md`
- Verify: `docs/user-manual/device-ingest-collection-monitoring-review.md`

- [ ] **Step 1: Check required files exist**

Run:

```bash
test -f docs/user-manual/device-ingest-collection-monitoring.md
test -f docs/user-manual/device-ingest-collection-monitoring-review.md
test -f docs/user-manual/assets/device-ingest-collection-monitoring/screenshot-manifest.md
```

Expected: all commands exit with status `0`.

- [ ] **Step 2: Check manual image references point to annotated assets**

Run:

```bash
rg -n "assets/device-ingest-collection-monitoring/annotated/" docs/user-manual/device-ingest-collection-monitoring.md
```

Expected: output includes at least the screenshots for sections 3, 4, 5, 6, 7, 8, and 9.

- [ ] **Step 3: Check the manual does not document deprecated APIs as user operations**

Run:

```bash
rg -n "onboarding/ensure|onboarding/plan|/api/|DTO|runtime projector|ledger" docs/user-manual/device-ingest-collection-monitoring.md
```

Expected: no output.

- [ ] **Step 4: Check for unresolved plan placeholders**

Run:

```bash
rg -n "TBD|TODO|待确认|填写.*后补|xx-name" docs/user-manual docs/superpowers/plans/2026-06-07-device-ingest-collection-monitoring-user-manual.md
```

Expected: no output from `docs/user-manual/`. The plan file may include `xx-name` only if quoting the design spec; it should not appear in the user manual.

## Task 7: Humanizer Review Pass

**Files:**
- Modify: `docs/user-manual/device-ingest-collection-monitoring.md`
- Modify: `docs/user-manual/device-ingest-collection-monitoring-review.md`

- [ ] **Step 1: Scan for AI-like or developer-only writing**

Run:

```bash
rg -n "完整闭环|提升效率|关键|重要|链路|编排|模型|DTO|Controller|ledger|runtime|orchestration|pipeline" docs/user-manual/device-ingest-collection-monitoring.md
```

Expected: no output, except UI-visible words if the page itself uses them. If a hit is not UI-visible, rewrite the sentence.

- [ ] **Step 2: Apply the humanizer rules manually**

Rewrite any paragraph that:

1. Sounds like a development design document.
2. Uses broad claims instead of a visible result.
3. Says "配置相关参数" without naming the field.
4. Uses implementation words that the UI does not show.

Example rewrite:

```markdown
Before:
完成监控纳管后，设备进入统一观测闭环。

After:
监控下发成功后，你可以在监控任务管理里看到相关任务和最近下发时间。
```

- [ ] **Step 3: Mark humanizer checks in the review file**

In `docs/user-manual/device-ingest-collection-monitoring-review.md`, update the `Humanizer 复核` rows from `未检查` to either `已通过` or `需修改`, with one short reason in the `说明` column.

- [ ] **Step 4: Re-run the scan**

Run:

```bash
rg -n "完整闭环|提升效率|关键|重要|链路|编排|模型|DTO|Controller|ledger|runtime|orchestration|pipeline" docs/user-manual/device-ingest-collection-monitoring.md
```

Expected: no non-UI-visible terms remain.

## Task 8: Novice Review Pass

**Files:**
- Modify: `docs/user-manual/device-ingest-collection-monitoring-review.md`
- Modify: `docs/user-manual/device-ingest-collection-monitoring.md` if review finds issues

- [ ] **Step 1: Apply each novice checklist row**

Read `docs/user-manual/device-ingest-collection-monitoring.md` from top to bottom. For each row in `新手可读性检查`, update:

```markdown
| 每章开头说明用户会完成什么 | 已通过 | 每章使用“你会完成什么”说明可见结果 |
```

Use `需修改` only when the issue remains after one revision attempt.

- [ ] **Step 2: Fix any `需修改` rows that can be fixed without screenshots**

Typical fixes:

1. Add a missing `开始前确认`.
2. Add a visible success standard.
3. Replace a vague action with a button or field name.
4. Move an optional advanced note out of the main path.

- [ ] **Step 3: Re-check the final checklist**

Run:

```bash
rg -n "设备已经出现在设备清单|已经执行过一次采集|已经执行过监控|监控任务管理" docs/user-manual/device-ingest-collection-monitoring.md
```

Expected: output includes all four phrases.

## Task 9: Decide Whether to Create the Reusable Skill

**Files:**
- Read: `docs/user-manual/device-ingest-collection-monitoring-review.md`
- Possible future create: `$CODEX_HOME/skills/oneops-user-manual-generator/SKILL.md`

- [ ] **Step 1: Check if skill extraction is allowed**

Only proceed to skill creation if all are true:

1. The manual structure is accepted.
2. The screenshot manifest format works.
3. Novice review rows are `已通过` or have explicit non-blocking reasons.
4. Humanizer rows are `已通过` or have explicit non-blocking reasons.
5. The user explicitly asks to create the skill after this first run.

- [ ] **Step 2: If not allowed, record the status**

Add this note to `docs/user-manual/device-ingest-collection-monitoring-review.md`:

```markdown
## Skill 固化状态

当前不创建 `oneops-user-manual-generator` 技能。原因：第一版手册还没有完成截图、复核和发布检查。等这些检查通过后，再按 `skill-creator` 和 `writing-skills` 流程创建技能。
```

- [ ] **Step 3: If allowed later, use skill-creator**

When the user explicitly approves skill creation after the manual is validated, use `skill-creator` and `writing-skills`. The skill should live at:

```text
$CODEX_HOME/skills/oneops-user-manual-generator/SKILL.md
```

The first skill draft should include only reusable workflow instructions, manual templates, manifest template, novice checklist, and screenshot annotation checklist. It must not include project screenshots or the final manual text.

## Self-Review Checklist

After completing the plan:

- [ ] Every required deliverable from the design spec maps to at least one task.
- [ ] The plan creates the main manual, screenshot manifest, review file, and asset directories.
- [ ] The plan includes screenshot red-box annotation rules.
- [ ] The plan includes `humanizer` and novice review gates.
- [ ] The plan does not ask an agent to document deprecated APIs as user operations.
- [ ] The reusable skill is gated until the first manual flow is validated.
- [ ] No manual release is claimed while required screenshots remain placeholders.
