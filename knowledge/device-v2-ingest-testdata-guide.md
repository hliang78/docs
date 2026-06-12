# Device V2 入库测试数据指引

这份指引只做一件事：把当前已经暴露过、且最容易反复出错的点，整理成后续测试数据生成的最小清单。

## 0. 先钉住“数据真源”分层

后续补测试前，先统一一个判断原则：**不是所有写进 Device V2 attributes 的字段，都属于同一层真源。**

建议按下面 5 层来理解整条链路：

| 层级 | 典型内容 | 是不是主真源 | 说明 |
| --- | --- | --- | --- |
| 输入层 | ingest API/Excel/外部 payload | 否 | 只是候选事实，入库前还会匹配、补数、归一化 |
| 主数据层 | Device V2 持久化后的 `attributes` / projection | 是 | 设备主档案的当前真相，应作为后续判断基础 |
| 兼容层 | legacy top-level 凭据字段、V1 映射字段 | 否 | 兼容旧入口或旧链路，不应反向定义主数据 |
| 桥接层 | `device_v1_code`、`sync_to_v1_status` | 否 | 只是 V2 到 V1 的桥接结果 |
| 运行层 | `monitor_push_status`、`monitor_push_error`、store run readiness | 否 | 只是某次动作/当前运行态结果，不是设备主档案事实 |

### 0.1 当前最接近“主真源”的对象

当前代码里，最接近主真源的是：

1. **归一化后的 Device V2 attributes**
   - 决定 `manageable` / `manage_status`
   - 决定后续 access point / credential 的协议归属
2. **Device V2 projection / entity**
   - 是主数据的持久化载体
   - 但 entity 顶层状态与 attrs 内状态不是一回事

### 0.2 目前最容易混淆真源的几组字段

#### A. 接入与凭据

同一能力现在可能同时出现在三处：

1. legacy top-level 字段
   - `credential_ref_in_band`
   - `credential_ref_out_band`
   - `snmp_credential_ref`
   - `winrm_credential_ref`
2. structured 字段
   - `credential_refs.in_band`
   - `credential_refs.in_band:ssh`
   - `credential_refs.in_band:snmp`
   - `credential_refs.in_band:winrm`
   - `credential_refs.out_band`
   - `credential_refs.out_band:ipmi`
   - `credential_refs.out_band:redfish`
   - `credential_refs.out_band:snmp`
3. endpoint 字段
   - `access_points[*].plane`
   - `access_points[*].login_method/protocol`
   - `access_points[*].credential_ref`

建议测试时把它们看成：

- `access_points + credential_refs` 是**标准模型**
- legacy top-level 字段是**兼容输入/兼容残留**
- 任何 case 都要断言：**归一化后，标准模型必须稳定，legacy 字段不能反客为主**

#### B. manage 状态

当前至少并存四层状态：

1. `entity.manage_status = success/pending`
2. `attrs.manage_status = manageable/registered_only`
3. `execution.device_results[].manage_status = manageable/registered_only/failed/unknown`
4. `manageable_status = unknown/pending/ready/unready`

建议测试时把它们看成：

- `attrs.manage_status` 才是**设备主数据层的可纳管结论**
- `entity.manage_status` 是**entity 生命周期状态**
- `execution.device_results[].manage_status` 是**本次入库动作结果**
- `manageable_status` 是 **store run readiness**

不要用后 3 者反推第 1 者。

#### C. V1 与监控状态

下面这些字段都不应视为设备主数据真源：

- `device_v1_code`
- `sync_to_v1_status`
- `sync_to_v1_message`
- `monitor_push_status`
- `monitor_push_error`
- `monitor_push_at`

它们的意义是：

1. 是否已桥接到 V1
2. 这次 monitor push 是否成功
3. 当前运维链路是否顺利

它们**不能**用来反推：

1. 设备主档案是否正确
2. 协议型接入模型是否正确
3. `manageable` 是否应该为 true

### 0.3 真源风险最高的 5 个位置

后续测试优先围绕这 5 个风险点造数：

1. **多表示法并存**
   - 同一个 credential 在 top-level、structured、endpoint 三处同时出现，且值不一致
2. **旧值 merge 残留**
   - existing 有脏 generic ref，新输入有正确 structured ref，merge 后旧值未清掉
3. **外部来源补数**
   - D2LA/source-original 会把源设备凭据补进当前请求，使“请求”不再是唯一输入真源
4. **身份匹配多入口**
   - code / registry / biz_code / asset_number / tenant-scoped IP 可能分别命中不同对象
5. **运行态回写主档案**
   - monitor push / sync-to-v1 结果会写回 attrs，容易与主数据字段混仓

### 0.4 用这套分层来指导测试断言

每条测试数据，建议至少做 3 层断言：

1. **输入层断言**
   - 当前 case 使用了哪些入口字段
   - 是否故意制造冲突/残留/缺项
2. **主数据层断言**
   - 归一化后的 `attributes`
   - 归一化后的 `access_points`
   - 归一化后的 `credential_refs`
   - `manageable` / `attrs.manage_status`
3. **桥接/运行层断言**
   - `sync_to_v1_status`
   - `monitor_push_status`
   - `execution.device_results[].manage_status`

这里最关键的一条经验规则是：

**桥接层和运行层的异常，不应直接推翻主数据层的入库结论；主数据层的正确与否，也不能仅靠桥接层/运行层是否成功来判断。**

### 0.5 字段归属表

后续做测试时，建议先问一句：**这个字段到底属于哪一层，它有没有资格支配判断结果？**

可以直接按下面这张表来分：

| 字段族 | 所属层 | 主写入阶段 | 能否作为主判断依据 | 测试重点 |
| --- | --- | --- | --- | --- |
| `code` | 主数据层 | ingest target resolve / create | 是 | 冲突、大小写、direct vs registry |
| `biz_code` / `asset_number` / `tenant_code` | 输入层 + 主数据层定位键 | resolveExistingDevice / resolveTarget | 有条件可以 | 租户优先、歧义拒绝、不可跨租户误更新 |
| `platform_code` / `catalog_code` / `region_code` / `site_code` / `rack_code` | 主数据层 | normalize / resolve refs | 是 | 显式 code 优先；错 code 必须失败，不能偷偷退回 name |
| `platform` / `catalog` / `region` / `site` / `rack` name | 输入层辅助字段 | normalize / resolve refs | 否，除非唯一命中后转成 code | 重名、歧义、与 code 冲突 |
| `access_points[*]` | 主数据层标准模型 | write normalize | 是 | plane / protocol / ip / credential_ref 是否归位正确 |
| `credential_refs.*` | 主数据层标准模型 | write normalize / copy-from-source | 是 | structured ref 是否保真、是否错误折叠成 generic |
| `credential_ref_in_band` / `credential_ref_out_band` / `snmp_credential_ref` / `winrm_credential_ref` | 兼容层 | 输入补缺 / merge residue | 否，不应单独支配最终判断 | 只能补缺，不能覆盖 structured truth；脏残留要能被清理 |
| `manageable` / `attrs.manage_status` | 主数据层派生字段 | normalize entity state / post-check | 是 | 只能由地址 + 凭据模型推导，不能由 monitor push 反推 |
| `entity.manage_status` | entity 生命周期层 | entity state build | 否 | success/pending 与 attrs.manage_status 不能混读 |
| `execution.device_results[].manage_status` | 运行层（本次入库动作） | executor result | 否 | 反映这次执行，不等于设备最终主状态 |
| `manageable_status` / `core_store_status` | store run readiness 层 | store run normalize | 否 | ready/unready 不等于 manageable/registered_only |
| `device_v1_code` / `sync_to_v1_*` | 桥接层 | sync-to-v1 workflow | 否 | 桥接成功与否不能改写主数据真相 |
| `monitor_push_*` | 运行层 | monitor workflow write-back | 否 | push 失败不应推翻入库成功；push 成功也不能证明主数据干净 |
| `code_registry` | 辅助索引层 | create/update sync | 否 | 可辅助命中，不可独立定义 live target |

#### 0.5.1 哪些字段可以“支配最终判断”

严格来说，只有下面两组字段应该支配“设备当前是否可纳管、监控模型是否正确”：

1. **身份与层级主数据**
   - `code`
   - `tenant_code`
   - `platform/site/rack/...` 的归一化 code
2. **标准接入模型**
   - `access_points`
   - `credential_refs`

也就是说，后续测试凡是看到这些情况，都应该提高警惕：

1. legacy top-level 凭据字段把 structured ref 顶掉了
2. name 命中结果盖过了显式 code
3. `monitor_push_status=success` 被当作主数据正确的证据
4. `sync_to_v1_status=failed` 被当作入库失败的证据

#### 0.5.2 哪些字段只能当“旁证”

下面这些字段在测试里可以断言，但只能当旁证，不能当真源：

1. `execution.device_results[].manage_status`
2. `entity.manage_status`
3. `sync_to_v1_status`
4. `monitor_push_status`
5. `code_registry`
6. selector / binding / probe 的中间命中结果

它们适合回答的是：

- “这次动作有没有跑通”
- “桥接有没有成功”
- “监控任务有没有下发”
- “辅助索引有没有同步”

它们不适合回答的是：

- “设备主档案现在到底是什么”
- “当前协议型接入模型最终是什么”
- “这个设备应不应该被判成 manageable”

#### 0.5.3 用字段归属表来生成测试数据

后续造数时，可以直接套这个顺序：

1. 先选 **主判断字段**
   - 比如 `access_points + credential_refs`
   - 或 `platform_code/site_code/rack_code`
2. 再加一层 **兼容/脏态字段**
   - 比如 top-level legacy credential
   - 或错误 name、孤儿 registry
3. 最后决定要不要附带 **桥接/运行态字段**
   - `sync_to_v1_status`
   - `monitor_push_status`

这样每条 case 都会变成一种清晰结构：

1. 主真源是什么
2. 干扰项是什么
3. 最终谁应该赢

这比单纯堆协议组合更容易发现“字段越权”类缺陷。

### 0.6 真源优先级矩阵

如果后续时间有限，不需要一次把所有组合补满，建议先补“最容易发生字段越权”的优先级矩阵。

#### 0.6.1 接入模型优先级

这一组最值得先补，因为它最容易直接影响 `manageable`、monitor selector、binding gate 和后续 monitor push。

建议优先级固定为：

1. **endpoint 显式值**
   - `access_points[*].credential_ref`
2. **structured ref**
   - `credential_refs.<plane[:method]>`
3. **generic structured ref**
   - `credential_refs.in_band`
   - `credential_refs.out_band`
   - `credential_refs.default`
4. **legacy top-level ref**
   - `credential_ref_in_band`
   - `credential_ref_out_band`
   - `snmp_credential_ref`
   - `winrm_credential_ref`

也就是说：

- endpoint 显式 ref 不得被 structured/generic/legacy 冲掉
- structured 协议型 ref 不得被 generic ref 冲掉
- generic ref 不得被 legacy 残留反向升级成协议型能力

最小回归矩阵建议如下：

| 编号 | 主真源 | 干扰项 | 预期 |
| --- | --- | --- | --- |
| AP-01 | 只有 endpoint 显式 `credential_ref` | 无 | 以 endpoint 为准 |
| AP-02 | endpoint 显式 `credential_ref=A` | `credential_refs` 给 `B` | 仍以 endpoint `A` 为准 |
| AP-03 | `credential_refs.in_band:ssh=A` | `credential_refs.in_band=B` | 以 `in_band:ssh=A` 为准 |
| AP-04 | `credential_refs.in_band:winrm=A` | `credential_ref_in_band=B` | 以 winrm structured ref 为准 |
| AP-05 | `credential_refs.out_band:ipmi=A` | `credential_ref_out_band=B` | 以 ipmi structured ref 为准；不得退化成 generic OOB |
| AP-06 | `credential_refs.out_band:redfish=A` | `credential_refs.out_band=B` | 以 redfish structured ref 为准 |
| AP-07 | `credential_refs.out_band:snmp=A` | generic `out_band=B` | 以 OOB SNMP structured ref 为准 |
| AP-08 | 只有 legacy `credential_ref_in_band=A` | 无 structured / endpoint | 可补缺生成可用标准模型，但不得产生错误协议升级 |
| AP-09 | 只有 legacy `credential_ref_out_band=A` | 无 structured / endpoint | 只能代表 generic OOB，不得自动变成 ipmi/redfish |
| AP-10 | structured 与 legacy 同值重复 | merge/update | 归一化后保留 structured truth，清理可清理残留 |

#### 0.6.2 主数据层级优先级

这组优先级主要针对主数据引用归一化：

1. 显式 `*_code`
2. 唯一可解析的 `*_name`
3. 历史残留/metadata 中的同类字段

这里最重要的规则是：

- **显式 code 一旦给出，就要么成功命中，要么明确失败**
- 不能因为 name 正好可解析，就偷偷忽略错误 code

最小矩阵建议如下：

| 编号 | 主真源 | 干扰项 | 预期 |
| --- | --- | --- | --- |
| MD-01 | `platform_code=PLT-A` | `platform=Platform-B` | 以 code 为准 |
| MD-02 | `site_code=SITE-A` | `site=Site-B` | 以 code 为准 |
| MD-03 | `rack_code=RACK-A` | `rack=Rack-B` | 以 code 为准 |
| MD-04 | 错误 `platform_code=BAD` | `platform=Platform-A` 可命中 | 必须失败，不能退回 name |
| MD-05 | 未给 `site_code` | `site=Site-A` 唯一命中 | 可接受并归一化成 code |
| MD-06 | 未给 `site_code` | `site=Site-A` 多命中 | 必须报歧义 |

#### 0.6.3 身份解析优先级

这组决定“这条数据到底写到哪台设备上”，风险非常高。

建议优先级理解为：

1. `code` 直接命中 live target
2. registered code / alias 命中
3. tenant-scoped locator 命中
4. tenantless fallback

但注意：**这不是盲目回退链，而是“每一步都必须保证唯一且可信”。**

最小矩阵建议如下：

| 编号 | 主真源 | 干扰项 | 预期 |
| --- | --- | --- | --- |
| ID-01 | `code=DEV-A` direct 命中 | 无 | 更新 DEV-A |
| ID-02 | `code=DEV-A` direct miss，registry 命中 DEV-A | 无 | 更新 DEV-A |
| ID-03 | `code=DEV-A` direct 命中 DEV-A，registry 指向 DEV-B | 冲突 | 必须失败 |
| ID-04 | `biz_code=X` + `tenant=T1` | T2 也有同 biz_code | 只能命中 T1 |
| ID-05 | `asset_number=X` 无 tenant | tenantless 历史数据存在 | 仅在规则允许时 fallback |
| ID-06 | locator 命中多台 projection | 无 | 必须报歧义 |

#### 0.6.4 运行态不得反向支配主数据

这组不是为了验证功能本身，而是为了防止“状态字段越权”。

最小矩阵建议如下：

| 编号 | 主真源 | 干扰项 | 预期 |
| --- | --- | --- | --- |
| RT-01 | 主数据完整，可判 `manageable` | `monitor_push_status=failed` | 仍应入库成功，主数据结论不变 |
| RT-02 | 主数据不完整，只能 `registered_only` | `monitor_push_status=success` | 不得反推成 `manageable` |
| RT-03 | V2 主数据正确 | `sync_to_v1_status=failed` | 不得反推入库失败 |
| RT-04 | 本次 execution result 为 failed | 历史持久化主数据仍存在 | 要区分“本次动作失败”与“当前主档案真相” |

#### 0.6.5 推荐先补的顺序

如果我们准备把这些矩阵真正落成测试，建议顺序是：

1. `AP-*` 接入模型优先级矩阵
2. `MD-*` 主数据层级优先级矩阵
3. `ID-*` 身份解析优先级矩阵
4. `RT-*` 运行态越权防护矩阵

这个顺序的好处是：

- 先把最容易污染 `manageable` 和 monitor onboarding 的问题钉死
- 再处理主数据归一化
- 然后处理更新目标判定
- 最后处理运行态状态混读

这样补出来的测试，命中率会比平均铺开高很多。

## 1. 先按“数据形态”分组，不要只按接口分组

后续造数建议优先覆盖这 6 类数据形态：

1. 干净新建：entity / projection / code_registry 都不存在
2. 正常存量：entity / projection / code_registry 都存在且一致
3. 半漂移：三者只剩其一或其二
4. 脏引用：名称、编码、层级、租户、凭证之间存在歧义或冲突
5. 监控特化：设备能入库，但监控条件不完整或只具备部分条件
6. 历史脏态：大小写不一致、孤儿 registry、旧字段残留、租户缺失

## 2. 当前最容易出错的点

### A. 标识解析类

- `code`、`registered code`、`biz_code`、`asset_number` 可能指向不同设备
- `code` 大小写不同但语义相同
- `code` 直接命中一台，registry 又指向另一台
- selector 或 locator 命中后，entity 与 projection 实际命中的是两台不同设备

测试数据至少要有：

- 直接命中
- alias 命中
- direct / registry 冲突
- entity / projection split-view 冲突
- 大小写变体

### B. 主数据归一化类

- platform / catalog / site / rack 可能传 code，也可能传 name
- name 可能重名
- rack 必须受 site 约束，site 必须受 region 约束
- import 链路和 formal ingest 链路容易一边修了一边没修

测试数据至少要有：

- code 优先于 name
- name 唯一命中
- name 多命中报歧义
- site 正确但 rack 落在别的 site
- region 正确但 site 落在别的 region

### C. 半漂移 / 自愈类

- 只有 projection，没有 entity
- 只有 entity，没有 projection
- 只有 registry，没有 entity / projection
- dead letter 还在，但后续一次成功写入应该自动 resolve

测试数据至少要有：

- projection-only 自愈
- entity-only 自愈
- orphan registry 不得支配入库
- pending dead letter 成功后变 resolved

建议也像主数据一样，保留一层基础矩阵：

1. `projection-only`
   - 预期：补回 entity，刷新 projection，补齐 primary registry
2. `entity-only`
   - 预期：保留并更新 entity，补回 projection，补齐 primary registry
3. `orphan-registry`
   - 预期：不得把 registry 当真相源，不得复活旧 entity
4. `pending-dead-letter`
   - 预期：后续一次成功写入后自动 resolve

### D. 租户边界类

- 同一个 `biz_code` / `asset_number` / IP 在不同租户重复出现
- 历史数据可能没有 `tenant_code`

测试数据至少要有：

- 同租户命中
- 跨租户不得误更新
- 租户优先，tenantless 仅作 legacy fallback

建议也保留一层 locator 维度矩阵：

1. locator 类型：
   - `biz_code`
   - `asset_number`
   - `in_band_ip`
   - `out_band_ip`
2. 租户模式：
   - 同租户命中并更新既有设备
   - 跨租户不得误更新，应创建新设备
   - 仅当历史数据没有 `tenant_code` 时，才允许 tenantless fallback

### E. 监控/纳管解耦类

- 入库成功不应因为监控下发失败而整体失败
- “纳管”表示已进入监控状态，不等于“允许入库”
- 有 IPMI 凭证只推 IPMI；有 Redfish 凭证只推 Redfish；有带外 SNMP 只推带外 SNMP
- selector 命中但因缺少绑定全部跳过，不应回过头阻断入库
- 同一种带外协议，不能因为入口不同而归一化结果不同

测试数据至少要有：

- 仅 IPMI
- 仅 Redfish
- 仅带外 SNMP
- 监控条件不足但入库成功
- monitor push 失败但 store / sync 仍成功

建议补一层协议化带外矩阵：

1. 协议类型：
   - `out_band:ipmi`
   - `out_band:redfish`
   - `out_band:snmp`
2. 输入形态：
   - 只给 `credential_refs`
   - `credential_refs + access_points(不显式带 credential_ref)`
   - inline 凭据自动生成引用
3. 预期：
   - `post_check.manageable = true`
   - `device_result.manage_status = manageable`
   - 持久化后的 `access_points` 自动补齐协议默认端口
   - 协议型凭证不得错误折叠成通用 `out_band`

建议再补一层“字段 -> gate -> 失败点”矩阵：

| 标准化字段 | 主要消费 gate | 典型作用 | 常见失败点 |
| --- | --- | --- | --- |
| `credential_ref_in_band` | `post_check` | 判定带内是否具备基础纳管条件 | 有带内 IP，但没有生成 ref |
| `credential_ref_out_band` | `post_check` | 判定通用带外 SSH/Telnet 基础纳管条件 | 被错误当成协议型带外能力 |
| `credential_refs.out_band:snmp` | binding gate / selector gate / SNMP probe gate | 命中 OOB SNMP 监控要求 | 被折叠成 in-band；probe 失败后仍误推 |
| `credential_refs.out_band:ipmi` | binding gate / selector gate | 命中 OOB IPMI 监控要求 | 只生成 ref，未补 `access_points` |
| `credential_refs.out_band:redfish` | binding gate / selector gate | 命中 OOB Redfish 监控要求 | 被错误折叠成 generic `out_band` |
| `access_points[*].plane/login_method/credential_ref` | selector gate | 精确识别协议和平面 | plane 错、method 错、缺少 credential_ref |
| `oob_snmp_probe_status` | SNMP probe gate | 决定 OOB SNMP 能否真正 apply | probe 成功被误跳过，probe 失败仍误推 |

对应的最小回归建议：

1. `inline -> 标准模型`
   - 仅 in-band SSH
   - 仅 OOB SNMP
   - 仅 IPMI
   - 仅 Redfish
   - top-level `winrm_credential_ref + winrm_port` 应自动生成 WinRM access_point，不得退化成 SSH
   - 明文清除，不得落库
2. `标准模型 -> post_check`
   - 有 IP + 有 ref -> `manageable`
   - 有 ref 无对应 IP -> `registered_only`
   - 仅 `out_band:ipmi/redfish/snmp` 时仍应可进入 `manageable`
   - `access_points[*].ip` 也属于“对应 IP”，不能只盯顶层 `in_band_ip/out_band_ip`
   - `in_band` 的 `ssh/snmp/winrm` 也要覆盖 “只有 access_points 提供地址” 的矩阵
   - 协议专属 ref 与 generic ref 同时存在时，必须优先命中协议专属 ref（如 `in_band:ssh` > `in_band/default`，`winrm` > `in_band/default`，`out_band:ipmi` > `out_band`）
3. `标准模型 -> binding gate`
   - `out_band:ipmi` 满足 `ipmi_outband`
   - `out_band:redfish` 满足 `redfish_outband`
   - `out_band:snmp` 满足 `snmp_outband`
   - generic `out_band` 不得冒充协议型带外能力
   - structured `credential_refs.out_band` 也只能代表 generic OOB，不能让 `ipmi/redfish` 误入 `manageable`
   - `ssh/winrm` 可回退到 generic `in_band/default`；`ipmi/redfish` 不得回退到 generic `out_band`
   - legacy `credential_ref_out_band` 也不得被折叠升级成 `out_band:ipmi/redfish`；它只能代表 generic OOB，不能让协议型带外设备误入 `manageable`
   - legacy top-level 凭据字段只可补缺，不能覆盖已存在的 structured `credential_refs`
4. `标准模型 -> selector gate`
   - `plane=out_band, method=ipmi/redfish/snmp` 时应精确命中对应协议
   - `plane=in_band, method=ipmi` 不得命中 OOB IPMI
   - access_point 已显式携带 `credential_ref` 时，应高于 `credential_refs` 与 legacy top-level 字段
   - 多个 `access_points` 同时存在时，某个 endpoint 的显式 `credential_ref` 不得串到其他 endpoint；structured ref 也必须按各自协议/平面独立命中
   - 同一设备内若同时混有 explicit endpoint ref、structured ref、legacy top-level 字段，优先级必须逐 endpoint 独立生效，不能被别的 endpoint 或 generic legacy 字段冲掉
5. `标准模型 -> probe gate`
   - `out_band:snmp + probe success` -> apply
   - `out_band:snmp + probe failed` -> skip
   - IPMI/Redfish 不应被 SNMP probe gate 误伤

### F. 历史兼容 / 脏字段类

- 旧字段与新字段同时存在，值互相打架
- 通用 `out_band` 凭证残留，但当前真实协议已经是 `out_band:snmp`
- top-level code 字段被误塞 name

测试数据至少要有：

- 旧字段残留被清理
- 新字段优先覆盖旧字段
- 不同入口对同一份历史数据结果一致
- D2LA / 源设备凭据复制链路中，structured `in_band:snmp` 也必须能被正确抽取并保留下来，不能只识别 legacy `snmp_credential_ref`
- 同样地，structured `in_band:winrm` 也必须能被正确抽取并保留下来，不能只识别 legacy `winrm_credential_ref`
- 同理，structured `in_band:telnet` 也必须能被正确抽取并保留下来，不能只识别 generic `credential_ref_in_band`
- out-band 侧也要做同样检查，尤其是 structured `out_band:telnet` 必须能被正确抽取并保留下来，不能只识别 generic `credential_ref_out_band`
- 当同一源设备同时带多种 structured refs 时，D2LA 复制链路必须做到“各自归位、互不覆盖”；如果目标侧某个 legacy 字段或 structured key 已显式给值，源设备同名能力不得覆盖它
- 对 update-clean / heal-drift 场景，还要覆盖“existing 里残留的 generic OOB 字段与 source 的 `out_band:snmp` 同值重复”时，merge + normalize 之后必须清掉这些旧残留
- 对应地，existing 里残留的 generic in-band 字段（如 `credential_ref_in_band` / `in_band` / `default` / `in_band:ssh`）如果只是与 source 的 `in_band:winrm` / `in_band:snmp` 同值重复，也必须在 merge + normalize 后清掉
- 再往前一步，还要覆盖“双侧同时残留”的组合脏态：existing 同时残留 in-band generic 和 out-band generic，source 同时带 `in_band:winrm` 与 `out_band:snmp` 时，一次 merge + normalize 应该能双侧同时洗净

## 3. 每组测试数据都要明确“预期类别”

不要只断言“成功/失败”，建议每条数据先标注成下面 5 类之一：

1. `create-clean`：全新创建
2. `update-clean`：正常更新
3. `heal-drift`：修复半漂移
4. `reject-ambiguous`：因歧义/冲突拒绝
5. `store-success-manage-partial`：入库成功，但监控/纳管部分未完成

## 4. 生成测试数据时的优先顺序

建议后续按这个顺序补：

1. 标识冲突与歧义
2. 主数据层级约束
3. 半漂移自愈
4. 租户边界
5. 监控解耦
6. 历史脏态兼容

## 4.1 建议先落一层基础矩阵

最值得先稳定的是“主数据显式 code 规则矩阵”，因为它最容易被后续修改误伤。

建议把下面两个维度交叉：

1. 主数据类型：
   - `platform`
   - `catalog`
   - `region`
   - `site`
   - `rack`
2. 校验模式：
   - 显式 `*_code` 大小写不同，但应成功解析
   - 显式 `*_code` 与 `*_name` 冲突时，必须以 code 为准
   - 显式 `*_code` 错误时，必须失败，不能退回 `*_name`

这层矩阵一旦稳定，后面所有“导入脏数据是否被偷偷吃掉”的问题都会更容易发现。

实践上，建议把它拆成两组基础矩阵长期保留：

1. 正向矩阵：显式 `*_code` 大小写兼容且可成功归一化
2. 反向矩阵：显式 `*_code` 错误时，即使 `*_name` 能命中也必须失败

## 5. 一条经验规则

凡是下面这些“看起来像辅助索引”或“后续运行结果”的东西，都不能直接当真相源：

- `code_registry`
- projection
- name 命中
- 历史 tenantless 数据
- selector 命中结果
- `sync_to_v1_status`
- `monitor_push_status`
- `execution.device_results[].manage_status`

它们都必须回到“是否存在真实 live target、是否唯一、是否层级一致、是否租户一致”再做最后判定。

## 6. 按 request_log 梳理 ZB call 最长链条

前面几节更偏“字段真源”和“主数据约束”。如果目标是**详细测试一次 ZB call 的完整入库链条**，还需要再补一层：按 `request_id` 把外部请求、V2 pipeline、回调结果串起来。

这一层最关键的原则是：

**`external_request_log` 不是整条链路的唯一真源，它只能证明“外层 ZB 请求处理到了哪里”；真正的主入库与纳管结果，要继续下钻到 `entity_pipeline_task.result_json`。**

### 6.1 一条 ZB store 请求的阶段分层

建议把一次 `zb -> store` 调用拆成 7 段：

1. **请求接入**
   - 收到 HTTP 请求，拿到 `ES` / `RequestID` / `Resource`
2. **外层请求日志初始落库**
   - `external_request_log` 先 upsert 一条 `status=Success`
3. **precheck / seed**
   - 校验设备是否可接受、是否能形成 accepted device
4. **启动 Device V2 store pipeline**
   - 创建 `entity_pipeline_task`
5. **主入库阶段**
   - `result_json.device_runs[*]`
6. **后置纳管阶段**
   - `result_json.manage_device_runs[*]`
   - 典型包括 `sync_to_v1`、`monitor_push`
7. **回调 ZB**
   - 生成 `callback_detail`
   - 发送回调并记录 `callback_response`

### 6.2 各阶段的数据真源

| 阶段 | 主看哪里 | 说明 | 常见误判 |
| --- | --- | --- | --- |
| 请求接入 | `external_request_log.params` | ZB 原始输入真源 | 把归一化后结果误当成原始请求 |
| precheck / seed | `external_request_log.process_detail` | 外层 workflow 只够说明前半段是否接受设备 | 误以为这里成功就代表整条入库成功 |
| pipeline 启动 | `entity_pipeline_task.options` | 确认是否真的启动了 V2 store pipeline，以及开了哪些 gate | 只看 request_log，不确认 task 是否存在 |
| 主入库 | `result_json.device_runs[*]` | 设备识别、detect、persist core 的真源 | 用 callback 的 `store=failed` 反推主入库失败 |
| 后置纳管 | `result_json.manage_device_runs[*]` | sync-to-v1、monitor push 的真源 | 用 `process_detail` 判断 monitor push |
| 对外回调 | `external_request_log.callback_detail` | 对 ZB 的标准化对外口径 | 把它当底层运行明细 |
| 回调出口 | `external_request_log.callback_response` | 只说明“有没有回调出去” | 把回调发送失败当成业务处理失败 |

### 6.3 `request_log` 视角最容易漏掉的 4 个问题

1. **`process_detail` 只覆盖前半段**
   - 它通常只能证明“成功保存基础信息阶段”之类的前置结果。
   - 不能据此判断 `sync_to_v1`、`monitor_push` 是否成功。

2. **`status=Success` 只代表外层 Dispatcher 成功**
   - 见 [external_request.go](/home/jacky/project/OneOPS-ALL/OneOps/app/external_request/api/external_request.go:43)。
   - 它不等于“全部设备完整入库并完成纳管”。

3. **callback 的 `store=failed` 可能是“后段 partial”**
   - 见 [zb_device_v2_store.go](/home/jacky/project/OneOPS-ALL/OneOps/app/external_request/service/zb/impl/zb_device_v2_store.go:126)。
   - callback 是外部兼容口径，里面的 `store` 不是 `device_runs.status` 的原样透传。

4. **`callback_response` 和 `callback_detail` 是两回事**
   - `callback_detail` 是准备发给 ZB 的内容。
   - `callback_response` 是 ZB 是否收到了这份内容。

### 6.4 最长链条优先的测试矩阵

如果时间有限，不要先把大量早期失败 case 堆满。应该先补**能走到最深处**的 case，因为它最容易暴露“前面看着成功，后面其实坏了”的缺陷。

| 编号 | 场景 | 目标链路深度 | 预期观察点 |
| --- | --- | --- | --- |
| RL-01 | 单设备全成功 | 走完整 7 段 | `request_log.status=Success`，`task.overall_status=success`，`summary_v2.status=success` |
| RL-02 | precheck 失败 | 止于第 3 段 | 无 `entity_pipeline_task`；`callback_detail.summary_v2.pipeline_status=precheck_failed` |
| RL-03 | seed 失败 / accepted=0 | 止于第 3 段 | `process_detail` 有前置失败；无有效 pipeline task |
| RL-04 | pipeline 创建成功但主入库失败 | 走到第 5 段 | `device_runs.status=failed`；`manage_device_runs` 为空或无效 |
| RL-05 | 主入库成功，`sync_to_v1` 失败 | 走到第 6 段 | `device_runs.status=success`；`manage.sync_to_v1_status=failed` |
| RL-06 | 主入库成功，`sync_to_v1` 成功，`monitor_push` 失败 | 走到第 6/7 段 | `manage.monitor_push_status=failed`；callback 为 partial |
| RL-07 | selector 命中但全部 skip | 走到第 6 段 | 主入库成功；monitor 侧应是 skip/partial，但不应被误报成主入库失败 |
| RL-08 | 批量混合：1 成功 1 precheck fail 1 monitor_push fail | 走完整 7 段 | 顶层 `ZB_STORE_PARTIAL_FAILED`；逐设备 `summary_v2` 正确分流 |
| RL-09 | 业务链成功，但 callback 外发失败 | 走完整 7 段 | `callback_detail` 正常；`callback_response=callback_request_failed` |
| RL-10 | request_log 存在，但 pipeline task 丢失/查不到 | 走到第 7 段诊断分支 | 诊断接口必须 fallback 到原始日志片段 |

### 6.5 最值得优先打透的“最长链条”样本

优先顺序建议固定成下面 4 条：

1. **全成功标准样本**
   - 用来给所有字段和状态做基准对照。

2. **主入库成功 + `monitor_push` 失败**
   - 这是最典型的“request_log 看起来没问题，但纳管后段失败”的缺陷入口。

3. **批量 mixed case**
   - 一个 precheck fail、一个主入库成功、一个 monitor_push fail。
   - 最容易暴露 `summary` / `summary_v2` 聚合错误。

4. **callback 外发失败**
   - 业务本身正常，但外部通知失败。
   - 最容易被误判成整条入库失败。

### 6.6 每条 `request_id` 的固定排查顺序

后续拿到一条 ZB 单号，建议固定按这个顺序查，不要跳步：

1. 先看 `external_request_log`
   - `request_id`
   - `status`
   - `params`
   - `process_detail`
   - `callback_detail`
   - `callback_response`
   - `reason`

2. 再查对应 `entity_pipeline_task`
   - 通过 `options.request_id` 或 `options.operation_key=zb-store:<request_id>`
   - 看 `task_id`
   - 看 `overall_status`
   - 看 `current_stage`
   - 看 `message`

3. 再下钻 `result_json`
   - `device_runs[*].status`
   - `device_runs[*].decision.code`
   - `manage_device_runs[*].status`
   - `manage_device_runs[*].sync_to_v1_status`
   - `manage_device_runs[*].monitor_push_status`
   - `manage_device_runs[*].error_code`
   - `manage_device_runs[*].origin_stage`
   - `manage_device_runs[*].origin_sub_stage`

4. 最后再对照 callback
   - `summary`
   - `summary_v2`
   - 顶层 `code/message/success`

### 6.7 可直接复用的 SQL 模板

#### A. 查外层 request log

```sql
SELECT
  request_id,
  resource,
  status,
  params,
  process_detail,
  callback_detail,
  callback_response,
  reason
FROM external_request_log
WHERE request_id = 'zb_xxx';
```

#### B. 查对应 pipeline task

```sql
SELECT
  task_id,
  overall_status,
  current_stage,
  message,
  options,
  result_json
FROM entity_pipeline_task
WHERE entity_type = 'device_v2'
  AND options LIKE '%"request_id":"zb_xxx"%'
ORDER BY created_at DESC;
```

#### C. 快速抽取主入库与后置纳管状态

```sql
SELECT
  task_id,
  overall_status,
  JSON_UNQUOTE(JSON_EXTRACT(result_json, '$.device_runs[0].status'))               AS device_run_status,
  JSON_UNQUOTE(JSON_EXTRACT(result_json, '$.device_runs[0].decision.code'))        AS device_run_decision,
  JSON_UNQUOTE(JSON_EXTRACT(result_json, '$.manage_device_runs[0].status'))        AS manage_status,
  JSON_UNQUOTE(JSON_EXTRACT(result_json, '$.manage_device_runs[0].sync_to_v1_status')) AS sync_to_v1_status,
  JSON_UNQUOTE(JSON_EXTRACT(result_json, '$.manage_device_runs[0].monitor_push_status')) AS monitor_push_status,
  JSON_UNQUOTE(JSON_EXTRACT(result_json, '$.manage_device_runs[0].error_code'))    AS error_code,
  JSON_UNQUOTE(JSON_EXTRACT(result_json, '$.manage_device_runs[0].origin_stage'))  AS origin_stage,
  JSON_UNQUOTE(JSON_EXTRACT(result_json, '$.manage_device_runs[0].origin_sub_stage')) AS origin_sub_stage
FROM entity_pipeline_task
WHERE task_id = 'entv2_xxx';
```

### 6.8 真实样本：`zb1780986495125`

这个样本值得保留成标准回归样本，因为它正好证明了“外层成功不等于全链路成功”：

1. `external_request_log.status = Success`
2. `process_detail` 只显示“成功保存基础信息阶段”
3. `entity_pipeline_task.overall_status = partial`
4. `result_json.device_runs[0].status = success`
5. `result_json.manage_device_runs[0].status = partial`
6. `manage_device_runs[0].error_code = MONITOR_PUSH_APPLY_FAILED`
7. `callback_detail.code = ZB_STORE_PARTIAL_FAILED`

这个 case 的诊断结论应当固定写成：

- **主入库成功**
- **sync-to-v1 已完成**
- **失败发生在 monitor push 的 apply_monitoring_strategy 阶段**
- **因此它是“store-success-manage-partial”，不是“基础入库失败”**

## 7. 真实输入组合测试总表

如果后续要在独立环境里做**真实设备测试**，优先级应该从“最长链条”切换成“输入组合”。目标不是先找最深的两三条路径，而是验证：

1. **同一种接入意图，不同写法是否会被解释成相同结果**
2. **冲突写法出现时，系统最终到底采用了哪一个输入**
3. **这个解释结果是否真正驱动了采集入库、监控推送、监控任务落地**

### 7.1 每条真实 case 都要验证的 5 个问题

每次在远端环境里跑一条 case，最后都要能回答：

1. 输入被解释成了什么协议与 plane
2. 采集是否按这个解释实际执行
3. 主入库是否成功
4. 监控是否按这个解释被推送
5. 监控任务是否真实落地且可确认

### 7.2 真实测试的 4 层观察面

| 观察层 | 主看什么 | 要回答的问题 |
| --- | --- | --- |
| 输入层 | 原始 payload / request_log.params | 用户到底是怎么写的 |
| 解释层 | 持久化后的 `access_points` / `credential_refs` / attrs | 系统最终把它解释成了什么 |
| 动作层 | `device_runs` / `manage_device_runs` / dc2 run | 采集、入库、监控是否真的执行 |
| 落地层 | 监控任务列表 / 对账结果 / callback | 任务是否真实存在并进入可确认状态 |

### 7.3 输入组合优先级

真实测试时，建议先按下面 5 个维度选样本，而不是按设备类型无穷展开：

1. **地址来源**
   - legacy top-level
   - `access_points` generic
   - `access_points` protocol-specific
2. **凭据来源**
   - inline
   - legacy ref
   - structured generic ref
   - structured protocol ref
   - endpoint 显式 ref
3. **使用意图**
   - 采集 + 入库 + 监控
   - 只做监控
   - 带内优先
   - 带外优先
4. **协议类型**
   - `ssh`
   - `snmp`
   - `winrm`
   - `ipmi`
   - `redfish`
5. **冲突形态**
   - 单一输入
   - 多写法一致
   - 多写法冲突
   - generic 与 protocol-specific 并存
   - endpoint ref 与全局 ref 并存

### 7.4 第一轮真实测试建议矩阵

第一轮不要追求全排列，先固定一层“最容易打出解释器缺陷”的矩阵。

| 编号 | 场景 | 输入形式 | 预期解释 | 采集期望 | 监控期望 | 任务确认期望 |
| --- | --- | --- | --- | --- | --- | --- |
| IC-01 | Linux SSH 基准 | `in_band_ip` + inline ssh | 解释为 `in_band:ssh` | dc2 采集成功，主入库成功 | 监控推送成功 | 任务可见，可对账 |
| IC-02 | Linux SSH structured ref | `access_points[in_band:ssh]` + `credential_refs.in_band:ssh` | 解释为 `in_band:ssh` | 与 IC-01 等价 | 与 IC-01 等价 | 与 IC-01 等价 |
| IC-03 | Linux SSH generic ref | `access_points[in_band]` + `credential_refs.in_band` | 解释为 `in_band/default`，并正确落到 ssh 采集 | dc2 可采集 | 监控可推送 | 任务可见 |
| IC-04 | endpoint ref 覆盖 global ref | endpoint `credential_ref` + generic/global ref 冲突 | 以 endpoint ref 为准 | 用 endpoint 凭据执行 | 推送不被 global ref 带偏 | 任务按 endpoint 解释落地 |
| IC-05 | Windows WinRM 基准 | `access_points[in_band:winrm]` + `credential_refs.in_band:winrm` | 解释为 `in_band:winrm` | WinRM 采集 / 入库成功 | 监控推送成功 | 任务可见，可对账 |
| IC-06 | Network SNMP 基准 | `access_points[in_band:snmp]` + `credential_refs.in_band:snmp` | 解释为 `in_band:snmp` | 设备可入库；采集按 SNMP | 监控按 SNMP 推送 | 任务可见，可对账 |
| IC-07 | monitor-only，无 SSH | 仅 SNMP 或 OOB 输入，无 ssh 凭据 | 不应因缺 SSH 失败；解释为监控型接入 | 可允许采集受限或跳过，但主入库成功 | 监控仍可推送 | 任务真实存在，可确认 |
| IC-08 | OOB IPMI 基准 | `access_points[out_band:ipmi]` + `credential_refs.out_band:ipmi` | 解释为 `out_band:ipmi` | 主入库成功 | 按 IPMI 模型推送监控 | 任务可见，可对账 |
| IC-09 | OOB Redfish 基准 | `access_points[out_band:redfish]` + `credential_refs.out_band:redfish` | 解释为 `out_band:redfish` | 主入库成功 | 按 Redfish 模型推送监控 | 任务可见，可对账 |
| IC-10 | generic OOB 与 IPMI/Redfish 并存 | `out_band` + `out_band:ipmi` 或 `out_band:redfish` | 协议型 ref 优先，不得折叠成 generic | 主入库成功 | 监控按协议型推送 | 任务按正确协议落地 |
| IC-11 | legacy 与 structured 一致 | legacy 字段 + structured 字段同值 | 归一化结果唯一且稳定 | 行为与纯 structured 一致 | 行为一致 | 任务一致 |
| IC-12 | legacy 与 structured 冲突 | legacy 与 structured 值不同 | 必须按既定优先级定胜负，不能随机 | 采集走胜出的输入 | 监控走胜出的输入 | 任务体现胜出的输入 |

### 7.5 四类最有价值的真实缺陷

这张矩阵重点不是为了“多测几条”，而是为了尽快把下面 4 类缺陷打出来：

1. **协议解释错误**
   - 明明给了 `in_band:snmp`，却被 generic `in_band` 或旧字段误解释成 ssh
2. **凭据优先级错误**
   - endpoint ref 没有赢过 global ref
   - structured ref 没有赢过 legacy ref
3. **monitor-only 场景被错误阻断**
   - 用户不给 SSH，只做监控，但主入库被误判失败
4. **监控任务假成功**
   - `monitor_push_status=success`，但任务管理页里没有真实可确认任务

### 7.6 真实测试时的固定记录模板

建议每个真实 case 都按同一模板记录，不然跑多了以后很难回头比较：

| 字段 | 示例 | 说明 |
| --- | --- | --- |
| case_id | `IC-07` | 输入组合编号 |
| request_id | `zbxxxx` | 本次外部请求编号 |
| device_code | `ASTxxxx` | 设备编号 |
| input_form | `snmp-only / no-ssh` | 本次输入形态摘要 |
| expected_interpretation | `in_band:snmp monitor-only` | 预期解释 |
| actual_interpretation | `...` | 实际解释 |
| device_run_status | `success/failed` | 主入库动作结果 |
| manage_run_status | `success/partial/failed` | 后置纳管结果 |
| sync_to_v1_status | `created/skipped/failed` | V1 桥接结果 |
| monitor_push_status | `success/skipped/failed` | 监控推送结果 |
| monitoring_task_visible | `yes/no` | 任务列表是否可见 |
| reconcile_available | `yes/no` | 是否可对账 |
| final_conclusion | `pass/fail` | 最终结论 |

### 7.7 建议的远端执行顺序

如果独立环境时间有限，建议先跑下面 6 条：

1. `IC-01` Linux SSH 基准
2. `IC-06` Network SNMP 基准
3. `IC-07` monitor-only，无 SSH
4. `IC-08` OOB IPMI 基准
5. `IC-09` OOB Redfish 基准
6. `IC-12` legacy 与 structured 冲突

这 6 条已经足够帮助判断当前问题主要落在：

1. 输入解释错误
2. 采集执行错误
3. 监控推送错误
4. 任务落地/对账错误

### 7.8 第一轮真实测试的通过标准

真实测试不要只看“接口返回 success”，建议统一按下面标准判定：

1. **解释正确**
   - 最终 `access_points` / `credential_refs` / attrs 与预期一致
2. **动作正确**
   - 采集 / 入库 / 监控动作按预期协议执行
3. **状态正确**
   - `device_runs` / `manage_device_runs` 与实际现象一致
4. **落地正确**
   - 监控任务真实存在，且可在任务管理中确认或对账

只满足前 2 条，不满足第 4 条，不能算真正通过；那只是“平台声称已推送”，还不是“任务真实落地成功”。

#### 7.8.1 预期运行态错误也可验收

对部分真实环境 case，测试目标不是“末端一定采集成功”，而是“平台是否把正确任务真实下发到正确位置”。

因此，下面这类 case 允许按**可验收**处理：

1. 没有真实 OOB 目标，但任务已成功下发到 Agent
2. monitor-only 演练对象故意不可达
3. 为验证下发与运行态错误路径而故意构造的 shadow target
4. 其它“故意没有真实目标，但希望验证平台编排链路”的演练型 case

这类 case 的通过标准不是“Prometheus / Loki 一定有数据”，而是：

1. 输入解释正确
2. 主入库成功
3. 监控推送成功
4. 监控任务真实存在
5. Agent 上确实有任务
6. 后续运行报错符合预期

建议在记录模板里把这类 case 的最终结论单独标成：

- `pass_with_expected_runtime_error`

不要把它误记成普通 `fail`，否则大版本回归时会把“平台链路已通过、末端目标本来就不存在”的 case 错算成版本缺陷。
