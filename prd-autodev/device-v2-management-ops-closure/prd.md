---
topic: device-v2-management-ops-closure
kind: frontend
title: Device V2 设备管理页运维闭环分析
createdAt: 2026-05-21T00:21:44+0800
---

# Device V2 设备管理页第一阶段闭环 PRD

## 1. Background

当前 `/device/device-v2-management` 已经完成从旧工作台叙事向“设备管理正式页”的切换，页面主结构已收敛为左侧设备分组、中间设备清单、右侧设备详情，编辑也已迁入本页实现。

当前最大问题不再是“有没有页面”，而是“页面是否真正适合运维日常使用”。一线运维在这个页上的核心动作，不是看流程，而是：

- 快速定位设备
- 判断当前是否可继续处理
- 修正设备信息
- 发起采集或监控
- 在重要但低频的监控下发场景里，知道成功结果、失败原因，并在需要时查看最后一次采集的详细数据

用户已明确三条边界：

- 第一批暂不考虑新增设备
- 动作结果默认在右侧详情里做简明复核
- 采集必须提供“查看最后一次采集详细数据”的入口

另外，页面还有大量细节问题需要整改，尤其是阅读语义问题：尽量不用编码作为主阅读信息，像 `0001-01-01 08:05` 这种无意义时间不能继续暴露。页面美化重要，但应排在基础功能和语义正确之后。

## 2. Goals

- 让 `监控未下发` 设备的采集/监控动作具备最小可用闭环：成功有显示，失败知原因，可在当前页继续处理。
- 明确区分采集和监控的真实能力模型：采集是 task 型链路，监控当前主要是 `sync-to-v1 + monitor push` 聚合结果型链路。
- 让右侧详情成为“简明复核面板”，而不是只有概览和动作按钮。
- 为采集场景补一个“最后一次采集详细数据”查看入口，满足少数需要下钻的运维场景。
- 建立采集 / 继续纳管 / 监控推送的分层错误协同表达，让页面既不生抛原始错误，也不吞掉关键线索。
- 补齐并发采集 / 并发监控推送时的设备级状态表达和重复触发控制，避免旧页里“任务提了但人看不清”的问题继续继承。
- 保留旧实现中对排障重要的过程数据，但通过分层承接避免新页重新变成操作台。
- 重构编辑弹窗，使其更宽、更顺手、下拉优先、布局更贴近运维填写路径。
- 修正页面阅读语义：名称优先于编码，业务名称优先于技术字段，零值时间和无意义占位信息不再直接展示。
- 在不回退到旧工作台叙事的前提下，挖矿复用旧页已验证过的任务结果承载能力。

## 3. Non-Goals

- 第一批不提供新增设备入口。
- 第一批不把页面扩展成“设备治理平台”或“综合工作台”。
- 第一批不重做左侧分组为全量后端聚合树，只处理阅读语义和必要交互细节。
- 第一批不把大量采集明细默认塞进右侧详情常驻区域。
- 第一批不优先追求视觉美化，视觉打磨服从基础可用性和语义正确性。
- 第一批不把旧页中大量过程性原始数据默认平铺在主页面或右侧详情中。

## 4. Target Users / Systems

- 一线运维工程师：查看设备、编辑设备、执行采集、执行监控、复核动作结果。
- 二线平台/CMDB 运维：修正字段、核对位置归属、排查动作异常。

涉及系统与模块：

- 前端页面：[DeviceV2ManagementRedesign.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:1)
- 旧页参考：[DeviceV2Management.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2Management.vue:912)
- 前端 API：[device-v2.ts](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/api/device/device-v2.ts:330)
- 分组配置后端：[device_v2_schema.go](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/service/impl/device_v2_schema.go:62)
- 交互方案稿：[interaction-design.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/device-v2-management-ops-closure/interaction-design.md)
- 字段级方案：[detail-and-drawer-spec.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/device-v2-management-ops-closure/detail-and-drawer-spec.md)
- 能力研究：[collect-monitor-research.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/device-v2-management-ops-closure/collect-monitor-research.md)
- 错误可定位化研究：[failure-diagnostics-research.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/device-v2-management-ops-closure/failure-diagnostics-research.md)
- 后端全过程失败地图：[backend-process-failure-map.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/device-v2-management-ops-closure/backend-process-failure-map.md)
- 参与方与关键方法地图：[participant-method-map.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/device-v2-management-ops-closure/participant-method-map.md)
- 参与方到前端承接矩阵：[participant-expression-matrix.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/device-v2-management-ops-closure/participant-expression-matrix.md)
- 错误协同模型：[error-coordination-model.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/device-v2-management-ops-closure/error-coordination-model.md)
- 错误字段协同表：[error-field-matrix.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/device-v2-management-ops-closure/error-field-matrix.md)
- 错误字段契约草案：[error-contract-draft.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/device-v2-management-ops-closure/error-contract-draft.md)
- 错误 UI 承接方案：[error-ui-spec.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/device-v2-management-ops-closure/error-ui-spec.md)

## 5. Current Findings

Frontend:

- `DeviceV2ManagementRedesign.vue` 已经接入 store task summary、runs、plans 与 `last-store-collection-dc2`，但采集失败的主承接仍以压平摘要为主，原始证据只在 JSON 面板里。
  - 参考：[DeviceV2ManagementRedesign.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:636)
  - 参考：[DeviceV2ManagementRedesign.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:894)
- 单设备 `继续纳管` 已经拿到 `onboarding evidence / actions / blocked_actions / failed_actions`，但当前只用于 toast，没有稳定渲染成错误诊断区块。
  - 参考：[DeviceV2ManagementRedesign.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:4215)
- 右侧详情当前已经能展示设备静态 `credential_refs.*`，但没有把这类信息与“本次正式链路失败到底用了哪条凭据引用”关联起来。
  - 参考：[DeviceV2ManagementRedesign.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue:342)
- 页面阅读语义仍有明显问题：
  - 分组候选项仍偏编码导向
  - 类型、位置等区域仍可能优先显示编码
  - `updated_at` 零值会显示成 `0001-01-01 08:05`
  - 这部分仍沿用既有整改方向，但不再是本轮最优先主题。

Backend / API:

- 分组配置已可后端保存，第一批不需要新增后端能力。
  - 参考：[device-v2.ts](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/api/device/device-v2.ts:1011)
- 旧 API 已提供可复用的动作闭环能力，但采集和监控不是同一类契约：
  - 采集：`store/start` + `task summary` + `runs` + `observations` + `last-store-collection-dc2`
  - 监控：`sync-to-v1` 返回批量结果，并回写 `monitor_push_status / monitor_push_error`
  - 另有 `onboarding plan / ensure` 可提供更结构化的监控动作信息，当前页其实已经接入，但还没渲染成稳定结果区块
  - 参考：[device-v2.ts](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/api/device/device-v2.ts:362)
  - 参考：[device-v2.ts](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/api/device/device-v2.ts:373)
- `buildMinimalCollectionExecutionLayer` 当前会把很多“未成功执行的 DC2”统一压成“本次未发起 DC2 采集”，这会掩盖 `controller_detect_failed`、`no_data_collected` 等失败线索。
  - 参考：[device_v2_store_minimal_api.go](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_store_minimal_api.go:1014)
- `classifyCollectDecision` 对 `D2_STORE_CONTROLLER_DETECT_FAILED` 与 `D2_STORE_DC2_REQUIRED_FAILED` 仍是通用失败文案，没有把“凭据引用异常优先”前置出来。
  - 参考：[device_v2_store_minimal_api.go](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_store_minimal_api.go:802)
- 后端全过程已经证明采集、`sync-to-v1`、`monitor push`、`onboarding ensure` 是多段异构失败面，不能继续被前端当成同一种“动作失败”承接。
  - 参考：[backend-process-failure-map.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/device-v2-management-ops-closure/backend-process-failure-map.md)
- 当前已能为第一版实现整理出“来源优先级、降级规则、static/runtime 区分”的字段契约，不必再靠页面临时拼判断。
  - 参考：[error-contract-draft.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/device-v2-management-ops-closure/error-contract-draft.md)
- `onboarding action evidence` 里已经包含 `device_collection2 / decision / store_summary`，但前端当前没有继续展开这些诊断字段。
  - 参考：[device_v2_onboarding_api.go](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_onboarding_api.go:406)
- `last-store-collection-dc2` 当前只够做“最近一次采集入口”判断，不足以单独支撑失败原因诊断。
  - 参考：[device_v2_store_minimal_api.go](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_store_minimal_api.go:412)
- 旧页已经证明这些能力能在 UI 中承载为结果抽屉和执行明细，而不是只弹 toast。
  - 参考：[DeviceV2Management.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2Management.vue:1466)
  - 参考：[DeviceV2Management.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2Management.vue:4553)

## 6. Requirements

### R1. 右侧详情提供动作简明复核

- Description:
  - 当用户从列表进入设备详情后，右侧详情需要清晰展示当前设备的动作状态，尤其是 `监控未下发` 场景。
  - 采集、监控动作执行后，右侧详情要能在当前上下文内展示简明结果，但要按两类动作的真实语义分开承接。
  - 复核内容至少包括：当前监控状态、最近一次采集结论、最近一次监控下发结论/失败原因、下一步建议。
  - 监控复核要明确区分：`sync-to-v1` 失败、`monitor push` 失败、已提交但待后续验证，不允许把它们糊成一个“监控失败”。
- Acceptance:
  - 对 `监控未下发` 设备，右侧能说明“是否可直接下发监控”。
  - 监控下发失败后，用户无需离开当前页即可看到失败原因摘要。
  - 采集动作完成后，右侧能刷新并显示最新采集结论。
  - 详情默认仍保持“简明复核”而不是展开全部明细。
- Validation:
  - 在浏览器中打开目标页面，选择一台 `监控未下发` 设备，点击“详情”，核对右侧复核信息。
  - 对一台设备执行采集或监控，验证右侧复核内容刷新。
- Evidence:
  - 页面截图：详情默认态、采集后态、监控失败态。

### R2. 采集场景提供“最后一次采集详细数据”查看入口

- Description:
  - 右侧详情默认只展示采集结论摘要。
  - 当设备存在最近一次采集记录时，页面需要提供“查看最后一次采集详细数据”的显式入口。
  - 详细数据应使用右栏之外的独立查看层承载，优先采用抽屉，避免把右侧详情做成信息墙。
  - 详细数据优先复用已有 API，例如 `last-store-collection-dc2`、task summary、runs、observations、collection plans。
  - 目标不是把旧页整套过程数据直接摊开，而是在不打断主页面叙事的前提下，为排障保留必要下钻入口。
- Acceptance:
  - 对存在最近采集记录的设备，右侧出现查看入口。
  - 打开后可看到最后一次采集相关的关键明细：任务关联、执行状态、核心 observations 或 summary。
  - 对没有采集记录的设备，不展示误导性的查看入口。
- Validation:
  - 在浏览器中选择一台已有采集数据的设备，验证查看入口与明细展示。
  - 选择一台无采集记录设备，验证入口缺失或禁用文案正确。
- Evidence:
  - 页面截图：有采集数据设备的入口与明细视图。

### R3. 采集/监控动作后的结果承接与回流

- Description:
  - 继续保留当前页内发起采集/监控的交互，但不能只依赖顶部 notice。
  - 动作后页面要保留当前设备或当前筛选上下文，避免用户失去工作位置。
  - 旧页中已验证有效的能力可迁移，但要改写成设备管理页叙事，不出现工作台式语言。
  - 采集承接允许基于 task 维度展开；监控承接则优先基于设备级回写状态与批量 item 结果，不伪造不存在的监控 task 详情。
  - 对排障有价值的大量过程数据应保留在独立查看层或深链接里，而不是默认铺在主页面。
- Acceptance:
  - 执行采集后，用户能在当前设备上下文中看到结果摘要，并可继续查看最后一次采集详细数据。
  - 执行监控后，成功和失败都能给出明确状态反馈，并能看出是 V1 同步问题还是监控推送问题。
  - 动作完成后，不丢失当前分组、搜索、设备选中状态。
- Validation:
  - 人工执行一次单设备采集、一次单设备监控，验证动作承接。
  - 对批量动作至少验证 notice 与当前筛选上下文不丢失。
- Evidence:
  - 页面截图：动作前后同一设备的右侧复核变化。

### R4. 并发采集 / 并发监控推送的状态与冲突控制

- Description:
  - 第一批必须明确处理并发动作，而不是默认沿用旧页的模糊状态承接。
  - 页面需要区分“采集进行中”“监控推送进行中”以及“两类动作同时存在”的设备级状态。
  - 同一设备在同一动作未结束时，应避免重复触发同类动作，至少要给出清晰的禁用态或进行中提示。
  - 批量动作执行后，需要能清楚区分：哪些设备采集进行中、哪些设备监控推送失败、哪些设备已完成，避免结果串台。
  - 右侧详情和列表中的状态表达要保持同一语义，不允许右栏显示采集中而列表仍可继续误触发同类动作。
  - 采集并发控制和监控并发控制应分别设计，不共享一套模糊“动作中”标记。
- Acceptance:
  - 同一设备在采集进行中时，不能无感重复发起同类采集。
  - 同一设备在监控推送进行中时，不能无感重复发起同类监控推送。
  - 当同一批设备上并发存在采集与监控动作时，用户仍能分清每类动作的当前状态和结果归属。
  - 批量动作部分成功、部分失败时，页面能给出分类型摘要，而不是只给一条笼统提示。
  - 用户切换筛选、切换设备后，再回到当前设备时，仍能看清这台设备的动作进行中状态。
- Validation:
  - 对同一设备连续触发两次采集，验证第二次触发的禁用或提示逻辑。
  - 对同一设备连续触发两次监控推送，验证第二次触发的禁用或提示逻辑。
  - 对同一批设备分别执行采集和监控，验证列表、右栏和结果提示的状态归属一致。
- Evidence:
  - 页面截图：同一设备采集中状态、监控推送中状态、批量部分成功部分失败状态。

### R5. 单设备采集保留必要的高级参数入口

- Description:
  - 默认采集入口保持轻量，适合列表批量与单设备快速发起。
  - 但旧页中已验证有效的单设备高级采集参数不能完全丢失，尤其是临时覆盖采集目标、凭证和采集方式的能力。
  - 第一批不要求把旧页整块大表单原样搬回，但应保留一个受控的“高级采集参数”入口，仅在单设备场景下启用。
- Acceptance:
  - 单设备默认可直接快速采集。
  - 当设备缺少接入目标、缺少凭证或用户主动选择高级采集时，页面存在高级采集参数入口。
  - 批量采集不提供统一覆盖凭证，继续遵守按设备自身已保存接入信息执行的约束。
- Validation:
  - 选一台具备接入条件的设备，验证可以快速发起采集。
  - 选一台缺少凭证或接入目标的设备，验证页面不会误导性直接成功，而是提供补充或高级采集入口。
- Evidence:
  - 页面截图：默认快速采集态、高级采集入口态。

### R6. 编辑弹窗重构为更顺手的正式页表单

- Description:
  - 编辑是高频动作，第一批必须重点优化。
  - 弹窗需要加宽，字段布局按运维填写路径重组，而不是按实现堆叠。
  - 优先使用下拉、可搜索选择、枚举，不鼓励用户手填技术编码。
  - 将字段分成更清晰的区块，例如：
    - 核心识别信息
    - 位置与归属
    - 推荐维护字段
    - 高级属性 / 扩展数据
  - `labels / metadata` 需要进一步降低阅读和填写负担，保留高级编辑能力但不让其压住主流程。
- Acceptance:
  - 弹窗宽度显著改善，常见设备在首屏能看到更多关键字段。
  - 平台、类别、租户、区域、机房、机柜等优先采用下拉选择。
  - 用户能明显区分“建议维护字段”和“高级扩展信息”。
  - metadata 很重的设备下，用户仍能快速完成常见字段修改。
- Validation:
  - 浏览器中打开编辑弹窗，验证布局、宽度、下拉和分层。
  - 使用一台 metadata 较多的设备验证首屏可读性。
- Evidence:
  - 页面截图：编辑弹窗首屏、展开高级区后的状态。

### R7. 名称优先、编码退后的阅读语义整改

- Description:
  - 正式页尽量不用编码作为主阅读信息。
  - 左侧分组候选项、列表次信息、详情事实块、hover 文案都要优先显示业务名称或业务语义。
  - 编码可保留，但必须退到次级位置，例如灰色副文案、tooltip、复制入口。
- Acceptance:
  - 分组下拉不再以“机房编码 / 机柜编码 / 平台编码”作为主展示语义。
  - 列表中的设备类型、位置等区域优先显示名称或业务含义。
  - tooltip / hover 文案不再把“设备型号编码”之类技术名词作为主提示。
- Validation:
  - 打开左侧分组编辑器，核对候选项文案。
  - 检查列表与详情中的类型、位置、平台等显示。
- Evidence:
  - 页面截图：分组下拉、列表行、详情事实块。

### R8. 零值时间和无意义占位信息清理

- Description:
  - 类似 `0001-01-01 08:05` 的零值时间不能在正式页直接显示。
  - 对无有效更新时间、无采集时间、无平台名称等情况，应改用明确的业务化空态表达，例如 `-`、`暂无记录`、`待补充`。
- Acceptance:
  - 列表“最近更新时间”不再出现零值时间。
  - 详情中的时间字段不再出现无意义占位值。
  - 空态文案统一且可理解。
- Validation:
  - 浏览器检查当前已有零值样本设备。
- Evidence:
  - 页面截图：问题前后对比。

### R9. 采集 / 继续纳管错误承接要分层协同

- Description:
  - 当前 `DeviceV2ManagementRedesign.vue` 已经能拿到不少失败证据，但默认只把它们承接成摘要或 toast。
  - 第一批目标不是让前端直接“做诊断”，而是建立统一的分层错误承接：
    - 结果层：这次是否完成
    - 阶段层：停在哪一环
    - 优先核对项：下一步先查什么
    - 证据锚点：排障时双方靠什么对齐
    - 原始返回：默认收起，仅排障时展开
  - 采集失败场景至少要补 3 类前置信息：
    - 本次正式链路的接入摘要，例如 `credential_ref_in_band / target_id / contract_key`
    - 对 `controller_detect_failed + no_data_collected` 的专门分流表达，优先提示核对凭据引用或正式链路接入配置
    - `snapshot_id / dc2_reason / detect route / store_run_id / dc2_run_id` 这类 evidence 锚点的前置展示
  - 单设备 `继续纳管` 当前已经持有 `actions / blocked_actions / failed_actions / unknown_actions`，第一批要把这类结构化结果从 toast 提升为页面内稳定可复核区块。
  - 当后端没有返回“本次正式链路实际使用的 credential ref”时，前端要明确说明自己展示的是设备当前保存值或候选值，而不是假装精准命中运行态。
- Acceptance:
  - 对 `controller_detect_failed`、`no_data_collected`、`D2_STORE_CONTROLLER_DETECT_FAILED`、`D2_STORE_DC2_REQUIRED_FAILED` 等场景，页面能把用户带向更接近真实排查方向的优先核对项。
  - 若后端 summary / evidence 中存在 `credential_ref_in_band`、`snapshot_id`、`dc2_reason` 等字段，前端能在主错误承接区优先展示，而不是只留在原始 JSON。
  - 单设备继续纳管失败后，用户无需只看 toast，即可在页面内看到动作标签、失败状态、关键 reason 与 controller/DC2 证据锚点。
  - 若后端没有返回足够字段，页面会明确提示“当前缺少本次正式链路的协同字段”，而不是猜造结论。
- Validation:
  - 使用一台已知“手工明文探测成功、正式链路失败”的样本设备，验证前端提示优先怀疑凭据引用而不是设备不可采。
  - 验证 `store` 抽屉与单设备继续纳管结果都能显示结构化失败证据。
  - 验证无稳定协同字段返回时的降级文案。
- Evidence:
  - 页面截图：凭据引用优先提示态、controller detect failed 态、单设备继续纳管失败态。

## 7. States And Edge Cases

- Empty:
  - 当前分组下无设备时，列表与右侧详情需明确显示空态，不保留旧设备残影。
- Loading:
  - 详情、采集详细数据、编辑下拉选项加载时，需要清楚的局部 loading。
- Success:
  - 采集或监控成功后，右侧详情摘要即时更新。
- Failure:
  - 监控失败展示失败原因摘要；采集失败展示失败结论和下钻入口（如有数据）。
  - 若采集失败来自正式链路的凭据引用问题，页面应优先提示核对 `credential_ref_in_band` 或当前正式链路接入配置，而不是笼统提示设备 SSH 不通。
  - 单设备继续纳管失败不能只依赖 toast；页面内需要存在可复核的失败承接区。
- Concurrent:
  - 同一设备可明确区分采集进行中、监控推送进行中和两类动作并存，不出现状态覆盖或结果串台。
  - 同类动作进行中时，重复触发应被拦截或明确提示。
  - 监控批量返回后，设备上持久化的 `monitor_push_status / error` 与列表展示需保持一致。
- Missing dependency:
  - 若最后一次采集任务关联不存在或 observations 不可读，仍要给出“暂无可查看详细数据”的清晰说明。
- Invalid data:
  - 后端返回零值时间、缺名称只有编码、字段值缺失时，前端必须做显示层兜底。

## 8. UX / API Contract

Frontend:

- 右侧详情承载“简明复核”，不承载整页级工作流。
- 采集详细数据使用单独抽屉或弹层，避免压垮右栏。
  - 默认推荐抽屉，只有在信息结构明显更适合弹层时才考虑弹层。
- 并发动作状态优先做设备级表达，不依赖单条全局 notice 充当唯一反馈。
- 采集详细承接基于 task 体系；监控详细承接基于设备级状态与批量 item 结果，不伪造任务详情概念。
- 单设备继续纳管已接入 `onboarding plan / ensure`，第一批应把现有结构化 evidence 渲染出来，而不是继续停留在 toast 级反馈。
- 对排障非常重要但低频使用的过程数据，采用“默认收起、需要时下钻、必要时深链接”的承接策略。
- 对错误提示，第一层优先展示“结果 / 阶段 / 优先核对项 / 证据锚点”，第二层再展示原始 JSON；不能让用户先下钻 JSON 才知道该怀疑凭据引用。
- 编辑弹窗默认更宽，优先双列或分区布局，并在窄屏下自然退化。
- 名称优先、编码退后；技术字段不作为主标题和主标签。
- 美化延后，但基础层面需要先解决信息层级、空态、文案和密度问题。

Backend / API:

- 第一批优先复用现有接口，但允许为“错误分层协同”补一个小范围稳定结构。
- 重点复用：
  - `getDeviceV2LastStoreCollectionDc2Req`
  - `getDeviceV2StoreTaskSummaryReq`
  - `listDeviceV2StoreRunsReq`
  - `listDeviceV2StoreObservationsReq`
- 补充可选：
  - 若现有 `summary / device_collection2 / onboarding action evidence` 中没有稳定字段路径，允许后端补稳定协同结构，用于承接 `used_credential_ref_in_band / dc2_reason / snapshot_id / detect_route / failure_class`。
- 若现有接口不足以支撑“最后一次采集详细数据”或“错误分层协同”的最小可用展示，前端实现需明确返回缺口，不得猜造数据。

## 9. Risks And Approval Boundaries

- Requires approval:
  - 若需要为“最后一次采集详细数据”新增后端接口或调整响应契约，需要先回到 PRD 复核。
  - 若需要新增稳定协同契约以返回运行态凭据引用、snapshot 或 detect route，需要先确认字段边界和脱敏规则。
- Known blockers:
  - 现有 API 是否足以支撑“最后一次采集详细数据”的最小可用展示，仍需前端接线验证。
  - 运行态里的 `credential_ref_in_band / snapshot_id / dc2_reason` 当前是否已有稳定字段路径，仍需以真实失败样本校验。
- Residual risks:
  - 旧页结果承载逻辑较重，迁移时如果不严格控范围，容易把新页重新做成工作台。
  - 如果没有明确的并发动作规则，新页很容易继续继承旧页“重复提交、状态串台、结果归属不清”的问题。
  - 名称优先展示依赖部分字段在现有数据中是否真的有名称值，前端可能需要做多级回退。
  - 如果只改前端文案，不补阶段 / 证据锚点，用户仍可能继续被误导去怀疑设备或网络，而不是先核对正式链路凭据引用。

## 10. Test And Evidence Plan

- Commands:
  - `npx eslint src/views/device/DeviceV2ManagementRedesign.vue src/api/device/device-v2.ts --ext .vue,.ts --fix`
  - `npm run typecheck`
- Browser/API checks:
  - 打开 `http://192.168.100.122:3001/#/device/device-v2-management`
  - 检查左侧分组候选项是否减少编码直出
  - 检查列表“最近更新时间”是否清理零值时间
  - 选择一台 `监控未下发` 设备，检查右侧复核信息
  - 对一台设备执行采集，验证“最后一次采集详细数据”入口
  - 对一台“手工明文探测成功、正式链路失败”的设备执行采集，验证页面会优先提示正式链路凭据引用或接入配置问题
  - 对一批设备执行监控，验证列表和右栏能区分 V1 同步失败与监控推送失败
  - 对一台设备执行单设备继续纳管，验证失败 evidence 不只出现在 toast 中
  - 对同一设备重复触发采集 / 监控，验证并发控制
  - 对同一批设备并发执行采集与监控，验证设备级状态与结果归属
  - 打开编辑弹窗，验证宽度、布局、下拉优先与字段分层
- Evidence files:
  - `docs/prd-autodev/device-v2-management-ops-closure/evidence/` 下保存截图与结果说明

## 11. OpenClaw Story Package

```json
{
  "program": "device-v2-management-ops-closure",
  "batch": "batch-001",
  "title": "动作闭环与编辑体验第一批",
  "status": "reviewed",
  "executionMode": "dependency-chain",
  "targetTaskIds": ["d2-fe"],
  "stories": [
    {
      "id": "D2FE-DVM-001",
      "title": "收敛设备管理页主阅读语义",
      "lanes": ["d2-fe"],
      "status": "open",
      "priority": 90,
      "risk": "Low",
      "scope": "调整左侧分组候选项、列表次信息、详情事实块的名称/编码展示优先级，并清理零值时间与无意义占位信息，确保正式页默认以业务语义为主阅读信息。",
      "nonGoals": "不做大规模视觉美化，不改左侧分组的后端聚合模式。",
      "allowedPaths": [
        "OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue"
      ],
      "acceptance": [
        "分组候选项不再以编码型文案作为主展示。",
        "列表与详情的类型、位置、平台优先展示名称或业务语义。",
        "最近更新时间不再显示 0001-01-01 08:05 之类零值时间。"
      ],
      "validation": [
        "npx eslint src/views/device/DeviceV2ManagementRedesign.vue --ext .vue,.ts --fix"
      ],
      "notes": [
        "PRD: docs/prd-autodev/device-v2-management-ops-closure/prd.md",
        "需要产出整改后页面截图。"
      ]
    },
    {
      "id": "D2FE-DVM-002",
      "title": "补右侧详情动作复核摘要",
      "lanes": ["d2-fe"],
      "status": "open",
      "dependsOn": ["D2FE-DVM-001"],
      "priority": 95,
      "risk": "Medium",
      "scope": "让右侧详情围绕监控未下发设备提供简明复核，承接采集和监控动作后的成功、失败、下一步建议，并保持当前筛选和设备上下文。",
      "nonGoals": "不把旧工作台整套任务结果直接搬进右栏，不默认展开大量技术明细。",
      "allowedPaths": [
        "OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue"
      ],
      "acceptance": [
        "详情右栏能显示当前监控状态、最近采集结论、监控失败原因摘要。",
        "执行采集或监控后，右栏摘要能在当前设备上下文中更新。",
        "动作完成后不丢失当前分组、搜索和已选设备上下文。"
      ],
      "validation": [
        "npx eslint src/views/device/DeviceV2ManagementRedesign.vue --ext .vue,.ts --fix"
      ],
      "notes": [
        "PRD: docs/prd-autodev/device-v2-management-ops-closure/prd.md",
        "优先复用现有 process_result 与 monitor_push_error 字段。",
        "实现时需要与并发动作状态表达保持一致，不要让右栏和列表状态打架。"
      ]
    },
    {
      "id": "D2FE-DVM-003",
      "title": "增加最后一次采集详细数据查看",
      "lanes": ["d2-fe"],
      "status": "open",
      "dependsOn": ["D2FE-DVM-002"],
      "priority": 93,
      "risk": "Medium",
      "scope": "在设备详情中为存在采集记录的设备提供最后一次采集详细数据查看入口，并使用独立查看层展示 task summary、process result、runs、observations、collection plans 与最近一次 DC2 关联信息。",
      "nonGoals": "不新增设备创建流程，不默认在右栏常驻展示全部采集原始数据。",
      "allowedPaths": [
        "OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue",
        "OneOPS-UI/src/api/device/device-v2.ts"
      ],
      "acceptance": [
        "有最近采集记录的设备在详情中出现查看入口。",
        "打开后能看到最后一次采集的关键明细数据。",
        "无采集记录设备不出现误导性入口。"
      ],
      "validation": [
        "npx eslint src/views/device/DeviceV2ManagementRedesign.vue src/api/device/device-v2.ts --ext .vue,.ts --fix"
      ],
      "notes": [
        "PRD: docs/prd-autodev/device-v2-management-ops-closure/prd.md",
        "优先复用 last-store-collection-dc2、task summary、runs、observations、collection plans。",
        "监控不要伪造 task detail，优先基于 sync-to-v1 批量结果和设备回写状态承接。"
      ]
    },
    {
      "id": "D2FE-DVM-004",
      "title": "补单设备高级采集入口",
      "lanes": ["d2-fe"],
      "status": "open",
      "dependsOn": ["D2FE-DVM-003"],
      "priority": 91,
      "risk": "Medium",
      "scope": "保持默认采集入口轻量，同时为单设备场景补受控的高级采集入口，用于缺少接入目标、缺少凭证或用户主动选择高级参数时覆盖采集目标、凭证和采集方式。",
      "nonGoals": "不恢复旧页整块大工作台式采集表单，不为批量采集提供统一凭证覆盖。",
      "allowedPaths": [
        "OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue",
        "OneOPS-UI/src/api/device/device-v2.ts"
      ],
      "acceptance": [
        "单设备默认仍可快速采集。",
        "缺少接入目标或凭证时，页面存在明确的高级采集参数入口。",
        "批量采集继续只使用设备已保存的接入信息。"
      ],
      "validation": [
        "npx eslint src/views/device/DeviceV2ManagementRedesign.vue src/api/device/device-v2.ts --ext .vue,.ts --fix"
      ],
      "notes": [
        "PRD: docs/prd-autodev/device-v2-management-ops-closure/prd.md",
        "参数范围以旧页已验证有效的 host、SNMP、SSH、DC2 baseline 为上限，不继续膨胀。"
      ]
    },
    {
      "id": "D2FE-DVM-005",
      "title": "补并发动作状态控制",
      "lanes": ["d2-fe"],
      "status": "open",
      "dependsOn": ["D2FE-DVM-002"],
      "priority": 96,
      "risk": "Medium",
      "scope": "补齐采集 / 监控并发触发时的设备级状态表达、重复触发控制和结果归属展示，并区分 V1 同步失败与监控推送失败。",
      "nonGoals": "不伪造监控 task 详情，不把所有动作都塞进同一个全局 notice 语义。",
      "allowedPaths": [
        "OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue",
        "OneOPS-UI/src/api/device/device-v2.ts"
      ],
      "acceptance": [
        "同一设备的重复采集或重复监控推送具备明确拦截或进行中提示。",
        "并发存在采集与监控动作时，列表、右栏和结果提示的归属一致。",
        "监控失败时能区分 V1 同步失败与监控推送失败。"
      ],
      "validation": [
        "npx eslint src/views/device/DeviceV2ManagementRedesign.vue src/api/device/device-v2.ts --ext .vue,.ts --fix"
      ],
      "notes": [
        "PRD: docs/prd-autodev/device-v2-management-ops-closure/prd.md",
        "优先基于 sync-to-v1 批量结果、monitor_push_status/error 与 process_result 承接。"
      ]
    },
    {
      "id": "D2FE-DVM-006",
      "title": "重构设备编辑弹窗布局",
      "lanes": ["d2-fe"],
      "status": "open",
      "dependsOn": ["D2FE-DVM-001"],
      "priority": 94,
      "risk": "Low",
      "scope": "加宽编辑弹窗，重组字段分区，提升下拉优先级，并把推荐维护字段与高级扩展信息做更清晰的层级组织，降低高频编辑的阅读和填写负担。",
      "nonGoals": "不做新增设备入口，不重写 SchemaForm 的通用渲染协议。",
      "allowedPaths": [
        "OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue",
        "OneOPS-UI/src/components/schema-driven/SchemaForm.vue"
      ],
      "acceptance": [
        "编辑弹窗宽度与首屏信息密度明显改善。",
        "平台、类别、位置归属等优先使用可搜索下拉。",
        "用户能明显区分推荐维护字段与高级扩展数据。"
      ],
      "validation": [
        "npx eslint src/views/device/DeviceV2ManagementRedesign.vue src/components/schema-driven/SchemaForm.vue --ext .vue,.ts --fix"
      ],
      "notes": [
        "PRD: docs/prd-autodev/device-v2-management-ops-closure/prd.md",
        "需要产出编辑弹窗重构前后截图。"
      ]
    },
    {
      "id": "D2FE-DVM-007",
      "title": "收敛采集与继续纳管错误为分层协同提示",
      "lanes": ["d2-fe"],
      "status": "open",
      "dependsOn": ["D2FE-DVM-002", "D2FE-DVM-003"],
      "priority": 98,
      "risk": "Medium",
      "scope": "在 DeviceV2ManagementRedesign.vue 的 store 抽屉与单设备继续纳管结果承接里，针对 controller_detect_failed、no_data_collected、credential_ref_in_band 等线索增加凭据引用优先的错误分流、证据锚点展示和结构化失败复核，不再只依赖 toast 或原始 JSON。",
      "nonGoals": "不在本故事内深挖 Vault 运行态，不把页面扩展成控制器调试台，不一次性引入完整双轨对照系统。",
      "allowedPaths": [
        "OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue",
        "OneOPS-UI/src/api/device/device-v2.ts"
      ],
      "acceptance": [
        "采集失败时，页面能优先展示正式链路接入摘要、关键 reason 与证据锚点，而不是统一落成设备不可采。",
        "单设备继续纳管失败后，页面内存在稳定的结构化失败复核区，而不是只弹 toast。",
        "若后端没有返回足够协同字段，页面明确提示当前缺少运行态协同字段，不猜造结论。"
      ],
      "validation": [
        "npx eslint src/views/device/DeviceV2ManagementRedesign.vue src/api/device/device-v2.ts --ext .vue,.ts --fix"
      ],
      "notes": [
        "PRD: docs/prd-autodev/device-v2-management-ops-closure/prd.md",
        "Research: docs/prd-autodev/device-v2-management-ops-closure/failure-diagnostics-research.md",
        "Model: docs/prd-autodev/device-v2-management-ops-closure/error-coordination-model.md",
        "Matrix: docs/prd-autodev/device-v2-management-ops-closure/error-field-matrix.md",
        "UI: docs/prd-autodev/device-v2-management-ops-closure/error-ui-spec.md",
        "若运行态 credential_ref 或 snapshot_id 缺少稳定字段路径，可回到 PRD 申请小范围稳定协同契约。"
      ]
    }
  ]
}
```
