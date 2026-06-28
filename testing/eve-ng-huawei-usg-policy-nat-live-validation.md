# EVE-NG Huawei USG 策略与 NAT 实机验证记录

更新时间：2026-06-28  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份记录不是重复初始化手册，而是专门回答一个更关键的问题：

1. OneOPS 当前已经支持的 `Huawei USG` `对象 / security-policy / nat-policy` 语义，放到真实设备上到底能不能成立
2. 如果不能完全成立，真实设备的边界到底是什么

## 2. 本轮验证范围

本轮只验证配置面，不验证真实业务流量转发。

验证目标如下：

1. 业务接口与安全域绑定
2. 地址对象与服务对象
3. `security-policy` 的 `permit` 与 `deny` 最小规则
4. `nat-policy` 的 `DNAT` 与 `SNAT` 最小规则
5. 保存与重启后的持久化

## 3. 验证对象

1. 节点：`USG1`
2. 管理地址：`172.32.2.13/24`
3. 管理方式：`SSH`
4. 设备镜像：`huaweiusg6kv-V500R005C10SPC300`
5. 当前稳定规格：`ethernet=6`

## 4. 本轮实配最小业务配置

### 4.1 业务接口与安全域

```text
interface GigabitEthernet1/0/0
 ip address 172.32.64.13 255.255.255.0
#
interface GigabitEthernet1/0/1
 ip address 172.32.65.13 255.255.255.0
#
firewall zone trust
 add interface GigabitEthernet1/0/0
#
firewall zone untrust
 add interface GigabitEthernet1/0/1
#
```

### 4.2 地址对象与服务对象

```text
ip address-set ONEOPS_SRC_NET type object
 address 192.168.10.0 mask 255.255.255.0
#
ip address-set ONEOPS_DST_NET type object
 address 10.10.10.0 mask 255.255.255.0
#
ip service-set ONEOPS_WEB80 type object
 service protocol tcp destination-port 80
#
```

### 4.3 安全策略最小规则

```text
security-policy
 rule name ONEOPS_TEST_POLICY
  source-zone trust
  destination-zone untrust
  source-address address-set ONEOPS_SRC_NET
  destination-address address-set ONEOPS_DST_NET
  service ONEOPS_WEB80
  action permit
#
 rule name ONEOPS_TEST_DENY
  source-zone trust
  destination-zone untrust
  source-address address-set ONEOPS_DENY_SRC
  destination-address address-set ONEOPS_DENY_DST
  service ONEOPS_SSH22
  action deny
#
```

配套对象如下：

```text
ip address-set ONEOPS_DENY_SRC type object
 address 192.168.20.0 mask 255.255.255.0
#
ip address-set ONEOPS_DENY_DST type object
 address 10.20.20.0 mask 255.255.255.0
#
ip service-set ONEOPS_SSH22 type object
 service protocol tcp destination-port 22
#
```

### 4.4 `DNAT` 最终可落地规则

最终被真实设备接受并在重启后仍保留的 `DNAT` 规则为：

```text
nat-policy
 rule name ONEOPS_TEST_DNAT
  source-zone untrust
  source-address 172.16.10.0 mask 255.255.255.0
  destination-address 203.0.113.10 mask 255.255.255.255
  service ONEOPS_WEB80
  action destination-nat address 10.10.10.10 8080
#
```

### 4.5 `SNAT easy-ip` 最终可落地规则

```text
nat-policy
 rule name ONEOPS_TEST_SNAT
  source-zone trust
  destination-zone untrust
  source-address address-set ONEOPS_SRC_NET
  destination-address address-set ONEOPS_DST_NET
  service ONEOPS_WEB80
  action source-nat easy-ip
#
```

### 4.6 `SNAT_POOL` 最终可落地规则

```text
nat address-group 11 0
 section 0 198.51.100.11 198.51.100.11
#
nat-policy
 rule name ONEOPS_TEST_SNAT_POOL
  source-zone trust
  destination-zone untrust
  source-address address-set ONEOPS_SRC_NET
  destination-address address-set ONEOPS_DST_NET
  service ONEOPS_WEB80
  action source-nat address-group 11
#
```

## 5. 真实设备结果

### 5.1 已实证通过

下面这些点已经在真实设备上写入、保存、重启后回读确认：

1. `GigabitEthernet1/0/0` 与 `GigabitEthernet1/0/1` 可作为业务接口写入三层地址
2. `trust` 与 `untrust` 可挂接对应业务接口
3. `ip address-set ... type object` 可正常创建并被策略引用
4. `ip service-set ... type object` 可正常创建并被策略引用
5. `security-policy` 的 `permit` 规则可正常创建
6. `security-policy` 的 `deny` 规则可正常创建
7. `nat-policy` 的 `DNAT` 规则可正常创建
8. `nat-policy` 的 `SNAT easy-ip` 规则可正常创建
9. `nat address-group + source-nat address-group` 这条 `SNAT_POOL` 形态也可正常创建
10. 上述配置 `save` 后，节点重启仍可回读到完整配置

### 5.2 明确打到的设备边界

这轮最重要的边界不是猜测，而是设备现场直接报出来的：

1. 当 `nat-policy` 规则同时带有：
   - `destination-zone trust`
   - `action destination-nat address 10.10.10.10 8080`
2. 设备会直接报错：

```text
Error: The destination-zone or egress-interface configuration conflicts with the Destination NAT action.
```

这说明在当前这台 `USG` 上：

1. 平台测试里常见的“`DNAT` 规则带 `destination-zone`”假设，并不能直接照搬到真实设备
2. 当前可稳定落地的 `DNAT` 规则，应按“`source-zone + source-address + destination-address + service + action`”这条结构来理解

### 5.3 当前已确认的 `SNAT` 设备事实

这轮在真实设备上又确认了两条 `SNAT` 事实：

1. `source-zone trust + destination-zone untrust + action source-nat easy-ip` 可被真实设备接受
2. `nat address-group 11 0 + action source-nat address-group 11` 也可被真实设备接受

这说明当前这台 `USG` 的 `SNAT` 至少存在两条真实可落地路径：

1. `INTERFACE / easy-ip`
2. `SNAT_POOL / address-group`

### 5.4 当前暴露出的平台侧薄弱点

本轮配套跑了 `agent/pkg/nodemap/node/device/firewall/usg` 的定向单测：

```text
go test ./pkg/nodemap/node/device/firewall/usg -run 'TestUsgV4NatPolicySNAT' -count=1 -v
```

结果虽然是 `PASS`，但日志同时暴露出一个不应忽略的问题：

```text
rule name [执行错误] ... undefined: NAT_POLICY
```

这说明当前平台侧至少还有一个需要单列跟踪的质量点：

1. `nat-policy` 规则名称模板存在变量求值异常
2. 现有单测之所以仍为绿色，是因为当前断言重点还没把“规则名称生成质量”纳入失败条件
3. 这类问题非常适合作为第一阶段测试中的“弱点发现”样本，而不能因为测试总结果是绿的就忽略

## 6. 对 OneOPS 的直接意义

### 6.1 已经可以作为第一阶段实机基线的能力

1. `Huawei USG` 的地址对象、服务对象、`security-policy` 已经可以进入真实设备验证链
2. `Huawei USG` 的 `permit / deny` 两类安全策略都已经有真实设备样本
3. `Huawei USG` 的 `DNAT` 已经不是“完全不可用”，而是“真实语法边界需要适配”
4. `Huawei USG` 的 `SNAT` 已经同时拿到了 `easy-ip` 与 `address-group` 两条真实设备样本
5. `display current-configuration | begin security-policy`
6. `display current-configuration | begin nat-policy`

上面两类配置块现在都已经有了真实设备样本，可直接用于平台采集与解析回归

### 6.2 当前必须共享的适配缺口

当前最需要在平台侧单列跟踪的缺口是：

1. `Huawei USG nat-policy` 生成逻辑不能默认强带 `destination-zone`
2. `DNAT` 规则的真实设备约束，需要和当前模板生成、解析、策略回显逻辑逐项对齐
3. `nat-policy` 规则名称模板当前还暴露出 `NAT_POLICY` 变量求值异常

如果这条边界不单列，后续就会出现一种假通过：

1. 模板单测是绿的
2. 规则文本也“看起来像对的”
3. 但真机一落配置就冲突

## 7. 关键验证命令

```text
display current-configuration interface GigabitEthernet1/0/0
display current-configuration interface GigabitEthernet1/0/1
display current-configuration | begin security-policy
display current-configuration | begin nat-policy
display current-configuration | include ONEOPS_SRC_NET|ONEOPS_DST_NET|ONEOPS_WEB80|ONEOPS_TEST_POLICY|ONEOPS_TEST_DNAT|ONEOPS_TEST_SNAT|ONEOPS_TEST_SNAT_POOL|ONEOPS_TEST_DENY|ONEOPS_DENY_SRC|ONEOPS_DENY_DST|ONEOPS_SSH22
```

## 8. 本轮结论

本轮可以把 `Huawei USG` 的阶段性结论明确写成下面三句：

1. `对象 + permit policy + deny policy + DNAT + SNAT` 已经全部在真实设备上拿到最小样本，可作为 OneOPS 第一阶段防火墙测试的有效主线
2. `DNAT` 已落证，但当前真实设备不接受“`destination-zone + destination-nat`”这类平台既有假设
3. `SNAT` 已同时落证 `easy-ip` 与 `address-group` 两种形态，说明平台后续可以围绕这两条真机路径继续细化适配
4. 下一步不该再泛泛而谈 `USG 是否支持 NAT`，而应该直接进入 `对象复用 / 策略查询命中 / 平台生成 CLI 与真机语法一致性` 的针对性专项验证
