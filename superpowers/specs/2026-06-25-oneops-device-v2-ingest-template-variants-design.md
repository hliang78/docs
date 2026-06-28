# OneOPS Device V2 导入模板多形态下载设计

Date: 2026-06-25

## 背景

当前 `导入设备清单` 页的“下载导入模板”只区分：

- 英文表头模板
- 中文表头模板

后端实际模板下载接口为：

- `GET /api/v1/device/v2/ingest/template/excel?header_lang=en|zh`

这意味着所有用户都会拿到同一套全量字段模板，其中同时包含：

- 台账与位置字段
- 凭证引用字段
- 明文账密字段
- 扩展结构字段（`credential_refs`、`access_points`）
- 一批非首轮导入必填的扩展资产字段

问题在于：

- 对只想走“凭证引用”模式的用户来说，模板里出现账密列会增加误填风险；
- 对只想走“账密”模式的用户来说，模板里出现多组凭证引用列会增加理解成本；
- 现有下载入口只能区分表头语言，不能表达“导入方式”；
- 如果让前端自己维护多份模板字段，后续容易与后端真实解析能力漂移。

因此，这次设计目标不是重做导入逻辑，而是在现有下载链路上增加“模板类型”维度，给用户提供更聚焦的模板。

## 设计目标

### 产品目标

让设备导入页支持下载 3 类模板：

1. 全量字段模板
2. 凭证引用模板
3. 账密模板

并且每类模板都支持：

- 英文表头
- 中文表头

### 体验目标

- 用户能在下载前清楚知道模板适用于哪种导入方式；
- 模板默认尽量少放无关列，减少误填；
- 已经使用全量模板的用户不受影响。

### 工程目标

- 模板字段来源只有一份事实源；
- 上传解析能力不因模板形态增加而分叉；
- 前端只负责传参和呈现，不复制后端字段契约。

## 范围

### 本次纳入设计

- Device V2 导入模板下载接口增加模板类型参数
- 后端按模板类型动态裁剪表头与文件名
- 前端下载菜单扩展为“模板类型 x 表头语言”
- 覆盖新模板类型的下载测试

### 本次不纳入设计

- Excel 上传解析规则大改
- 导入页草稿表格字段编辑能力重构
- 凭证校验逻辑重写
- 按租户、设备类别、平台进一步细分模板

## 总体方案

采用：

- `B1 后端模板类型参数化`

不采用：

- `A1 前端本地生成多份模板`
- `C1 六个独立硬编码下载接口`

原因如下。

### 采用 B1 的原因

- 模板字段与真实上传解析契约都由后端控制，不会出现前后端两套字段清单；
- 模板形态只是字段投影视图变化，不需要引入新的上传接口；
- 后续如果再加模板类型，只需要扩展一套后端元数据和前端菜单项；
- 自动化测试可以直接校验下载产物，覆盖更完整。

### 不采用 A1 的原因

- 前端一旦开始本地维护字段清单，就会和 `dto.DeviceV2IngestExcelHeaders` 出现双份定义；
- 后续新增、改名、兼容旧列头时，容易出现下载模板和上传解析不一致；
- 浏览器生成 Excel 也会让模板示例数据、文件名、Sheet 名等规则分散。

### 不采用 C1 的原因

- 六个固定接口或六个固定文件分支会放大重复代码；
- 这种做法不利于后续继续增加模板类型；
- 语言和模板类型本质上是两个维度，应该通过参数表达，而不是接口爆炸。

## 模板类型定义

### 1. 全量字段模板

定位：

- 保持当前模板能力；
- 提供完整导入列；
- 适合复杂导入、一次性补齐较多信息的场景。

特征：

- 保留现有全部字段；
- 同时包含凭证引用列与账密列；
- 保留 `credential_refs`、`access_points` 等高级列。

兼容性要求：

- 这是默认模板类型；
- 不传 `template_type` 时，行为必须与当前线上一致。

### 2. 凭证引用模板

定位：

- 适合统一凭证平台已经准备好的场景；
- 用户只填写设备识别、位置、接入 IP 和各类凭证引用。

保留字段原则：

- 保留基础识别字段；
- 保留位置与资产归属字段；
- 保留接入相关的非敏感字段；
- 保留所有 `*_credential_ref` 字段；
- 不保留任何 `*_username` 或 `*_password` 字段。

明确不包含：

- `in_band_username`
- `in_band_password`
- `out_band_username`
- `out_band_password`
- `snmp_username`
- `snmp_auth_password`
- `snmp_priv_password`
- `ipmi_username`
- `ipmi_password`
- `redfish_username`
- `redfish_password`

### 3. 账密模板

定位：

- 适合统一凭证暂未沉淀、需要直接提供账号密码的场景；
- 用户只填写设备识别、位置、接入 IP 和账密字段。

保留字段原则：

- 保留基础识别字段；
- 保留位置与资产归属字段；
- 保留接入相关的非敏感字段；
- 保留 `*_username` / `*_password` 字段；
- 不保留任何 `*_credential_ref` 字段。

明确不包含：

- `credential_ref_in_band`
- `credential_ref_out_band`
- `snmp_credential_ref`
- `winrm_credential_ref`
- `credential_refs`

说明：

- `access_points` 作为高级结构列仍保留在全量模板中；
- 凭证引用模板与账密模板不暴露 `access_points`，避免把“简化模板”又变成结构化高级模板。

## 字段分组设计

为避免把 3 套模板直接写成 3 份静态数组，后端字段定义拆成以下几组：

### A. 基础字段组

所有模板共享，包含：

- 设备识别字段，如 `code`、`biz_code`、`biz_name`
- 基础接入字段，如 `in_band_ip`、`out_band_ip`、`login_method`、`login_port`
- 基础位置字段，如 `tenant_name`、`region_name`、`site_name`、`rack_name`、`rack_position`
- 设备基础属性，如 `hostname`、`asset_number`、`platform`、`catalog`、`status`、`vendor`、`model`、`sn`
- 必要的来源与说明字段，如 `source`、`batch_id`、`original_code`、`remark`

### B. 凭证引用字段组

仅 `full` 与 `credential_ref` 模板使用，包含：

- `credential_ref_in_band`
- `credential_ref_out_band`
- `snmp_credential_ref`
- `winrm_credential_ref`
- `credential_refs`

### C. 账密字段组

仅 `full` 与 `account_password` 模板使用，包含：

- `in_band_username`
- `in_band_password`
- `out_band_username`
- `out_band_password`
- `snmp_username`
- `snmp_auth_password`
- `snmp_priv_password`
- `ipmi_username`
- `ipmi_password`
- `redfish_username`
- `redfish_password`

说明：

- `snmp_auth_protocol`、`snmp_priv_protocol`、`snmp_version`、`snmp_community`、`snmp_plane` 属于接入参数，不属于敏感账密，因此保留在共享基础组。

### D. 全量扩展字段组

仅 `full` 模板使用，包含：

- `access_points`
- 软硬件扩展字段，如 `system_version`、`patch_version`、`firmware_version`、`kernel_version`
- 资源规格字段，如 `os_name`、`os_version`、`architecture`、`cpu_arch`、`cpu_model`、`cpu_cores`、`cpu_sockets`
- 容量字段，如 `memory_total`、`memory_total_bytes`、`memory_slots`
- 结构化扩展字段，如 `hardware`

## 后端设计

### 接口契约

现有接口保持不变：

- `GET /api/v1/device/v2/ingest/template/excel`

新增查询参数：

- `template_type=full|credential_ref|account_password`

查询参数组合为：

- `header_lang=en|zh`
- `template_type=full|credential_ref|account_password`

兼容策略：

- `template_type` 为空时，默认按 `full` 处理；
- 未识别的 `template_type` 也回退到 `full`，避免破坏旧调用方；
- `header_lang` 继续沿用现有兼容逻辑。

### 服务层

将 `DownloadExcelTemplate(ctx, headerLang string)` 扩展为：

- `DownloadExcelTemplate(ctx, headerLang, templateType string)`

模板生成流程为：

1. 解析模板类型
2. 根据模板类型得到标准字段 key 列表
3. 按 `header_lang` 映射为英文表头或中文表头
4. 生成文件名
5. 依据字段顺序写入表头和示例行

### DTO 层

在 `device_v2_ingest_excel.go` 中新增：

- 模板类型常量
- 模板类型到字段组的映射
- 基于字段 key 生成中文表头数组的辅助方法
- 基于字段 key 生成示例行的辅助方法

避免继续依赖“整套字段顺序数组 + 全量示例行切片按索引对齐”的单一模式，因为现在需要按子集投影。

### 文件名

建议文件名如下：

- `device_v2_ingest_template.xlsx`
- `device_v2_ingest_template_zh.xlsx`
- `device_v2_ingest_template_credential_ref.xlsx`
- `device_v2_ingest_template_credential_ref_zh.xlsx`
- `device_v2_ingest_template_account_password.xlsx`
- `device_v2_ingest_template_account_password_zh.xlsx`

要求：

- 文件名能表达模板类型；
- 中文表头与英文表头继续通过 `_zh` 区分；
- 默认全量模板名称尽量保持现有命名习惯，降低影响。

### 示例数据

示例行不再直接依赖“整行定长数组”，而是基于字段 key 映射动态投影。

要求：

- 基础识别和位置字段示例继续保留；
- 凭证相关示例默认保持空值，避免误导用户写入伪密码；
- 对不存在于某模板中的字段，不输出空列占位。

## 前端设计

### 下载入口

现有“下载导入模板”按钮保留，但下拉菜单从 2 项扩展为 6 项：

1. 下载全量字段模板（英文）
2. 下载全量字段模板（中文）
3. 下载凭证引用模板（英文）
4. 下载凭证引用模板（中文）
5. 下载账密模板（英文）
6. 下载账密模板（中文）

### URL 构造

前端 URL builder 从仅接收 `headerLang`，扩展为接收：

- `headerLang`
- `templateType`

拼接规则：

- `header_lang=en|zh`
- `template_type=full|credential_ref|account_password`

其余 token、时间戳、下载触发逻辑保持不变。

### 文案

页内辅助文案从：

- `模板包含当前支持的导入字段，可选择中文或英文表头。`

调整为能同时表达两个维度，例如：

- `可按字段范围与表头语言下载模板，支持全量字段、凭证引用、账密三种方式。`

要求：

- 不额外增加说明卡片；
- 不在主界面引入大段解释文字；
- 靠菜单项命名让用户理解差异。

## 上传解析与兼容策略

这次设计只改变“下载模板的字段组合”，不改变上传解析的兼容范围。

明确要求：

- 继续允许用户上传包含更多列的 Excel；
- 继续兼容旧中文列头、别名列头；
- 不因为选择了某类模板，就在上传时强制拒绝出现其他凭证字段；
- 模板类型只影响“推荐填写哪些列”，不影响上传 API 数据模型。

原因：

- 下载模板是引导能力，不应在这次设计中升级成强校验能力；
- 先让模板更贴合用户场景，再决定是否需要更细粒度的导入模式校验。

## 测试设计

### 后端测试

补充下载模板测试，至少覆盖：

1. 默认不传 `template_type` 时返回全量模板
2. `template_type=full` 返回全量字段
3. `template_type=credential_ref` 不包含账密字段
4. `template_type=account_password` 不包含凭证引用字段
5. 中文表头模板与英文表头模板字段数量一致
6. 各模板文件名正确
7. 示例数据在裁剪字段后仍然列位对齐

测试重点不是只比较字段数量，而是验证：

- 包含哪些列
- 不包含哪些列
- 关键示例字段没有错位

### 前端测试

补充轻量测试覆盖：

1. 下载菜单出现 6 个选项
2. 点击不同菜单项时，URL 中 `header_lang` 与 `template_type` 组合正确
3. 按钮在能力受限时仍保持当前禁用逻辑

## 风险与约束

### 风险 1：字段分组切错

如果把某些非敏感接入字段误分到凭证字段组，会让简化模板失去必要参数。

缓解方式：

- 明确“凭证字段”和“接入参数字段”的边界；
- 用测试校验典型字段是否出现在正确模板中。

### 风险 2：示例行错位

当前实现基于“整行数组按索引写列”，改成多模板后，最容易出现表头与示例值错位。

缓解方式：

- 改为基于字段 key 动态投影示例值；
- 在测试中校验 `in_band_ip`、`out_band_ip`、`hostname` 等关键列。

### 风险 3：前端菜单膨胀后不易理解

如果菜单文案不够清楚，用户可能不知道“凭证引用”和“账密”区别。

缓解方式：

- 菜单项名称必须把模板类型说完整；
- 面板提示只补一句，不再堆说明文案。

## 落地顺序

1. 重构后端模板字段元数据与模板类型解析
2. 先补后端下载测试，锁定 3 类模板字段边界
3. 修改模板下载实现与文件名输出
4. 扩展前端下载 URL builder 与下拉菜单
5. 补前端轻量测试
6. 手动验证 6 个下载组合均可生成可打开的 Excel

## 预期结果

完成后，设备导入页的模板下载能力应满足：

- 默认下载仍然兼容当前全量模板；
- 用户可以明确选择“全量字段 / 凭证引用 / 账密”三种模板；
- 中文与英文表头仍保持现有体验；
- 模板字段更聚焦，但上传兼容性不收紧；
- 前后端模板字段契约仍由后端单点维护。
