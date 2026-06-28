# EVE-NG Huawei USG 防火墙标准模板

更新时间：2026-06-28  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份文档把当前已经在真实设备上落证的 `Huawei USG` 最小模板收敛成统一标准。

它回答的不是“设备理论上怎么配”，而是：

1. 当前这台 `USG` 在 EVE 里哪些字段已经可以进入标准模板
2. 哪些配置块已经在真实设备上写入、保存、重启复验
3. 哪些语法仍然不能被平台默认假设直接套用

## 2. 当前模板结论

截至 `2026-06-28`，`Huawei USG` 当前可进入 OneOPS 第一阶段标准模板的范围如下：

1. 管理模板：`已实证`
2. 业务接口模板：`已实证`
3. 地址对象模板：`已实证`
4. 服务对象模板：`已实证`
5. `permit security-policy` 模板：`已实证`
6. `deny security-policy` 模板：`已实证`
7. `DNAT` 模板：`已实证，但存在真实语法边界`
8. `SNAT easy-ip` 模板：`已实证`
9. `SNAT_POOL` 模板：`已实证`

## 3. 标准输入

### 3.1 节点规格

```text
template=huaweiusg6kv
image=huaweiusg6kv-V500R005C10SPC300
cpu=2
ram=4096
console=telnet
ethernet=6
qemu_nic=virtio-net-pci
```

### 3.2 管理平面输入

```text
hostname=USG1
mgmt_interface=GigabitEthernet0/0/0
mgmt_vrf=MGT
mgmt_ip=172.32.2.13/24
mgmt_gateway=172.32.2.254
login_username=admin
login_password=admin@123
```

### 3.3 业务模板输入

下面这组字段已经足够支撑当前最小 `policy + nat` 实机模板：

```text
inside_interface=GigabitEthernet1/0/0
inside_zone=trust
inside_ip=172.32.64.13/24

outside_interface=GigabitEthernet1/0/1
outside_zone=untrust
outside_ip=172.32.65.13/24

permit_src_object=ONEOPS_SRC_NET
permit_src_network=192.168.10.0/24
permit_dst_object=ONEOPS_DST_NET
permit_dst_network=10.10.10.0/24
permit_service_object=ONEOPS_WEB80
permit_service=tcp/80
permit_policy_name=ONEOPS_TEST_POLICY

deny_src_object=ONEOPS_DENY_SRC
deny_src_network=192.168.20.0/24
deny_dst_object=ONEOPS_DENY_DST
deny_dst_network=10.20.20.0/24
deny_service_object=ONEOPS_SSH22
deny_service=tcp/22
deny_policy_name=ONEOPS_TEST_DENY

dnat_rule_name=ONEOPS_TEST_DNAT
dnat_source_zone=untrust
dnat_source_network=172.16.10.0/24
dnat_public_ip=203.0.113.10/32
dnat_service_object=ONEOPS_WEB80
dnat_real_ip=10.10.10.10
dnat_real_port=8080

snat_easy_ip_rule_name=ONEOPS_TEST_SNAT
snat_pool_rule_name=ONEOPS_TEST_SNAT_POOL
snat_source_zone=trust
snat_destination_zone=untrust
snat_src_object=ONEOPS_SRC_NET
snat_dst_object=ONEOPS_DST_NET
snat_service_object=ONEOPS_WEB80
snat_pool_id=11
snat_pool_ip=198.51.100.11
```

## 4. 标准渲染结果

### 4.1 管理模板

```text
screen-length 0 temporary

system-view
ip vpn-instance MGT
 ipv4-family
 quit
 quit

interface GigabitEthernet0/0/0
 ip binding vpn-instance MGT
 ip address 172.32.2.13 255.255.255.0
 service-manage enable
 service-manage https permit
 service-manage ping permit
 service-manage ssh permit
 quit

aaa
 manager-user admin
  service-type ssh terminal web
  state active
 quit
 quit

ssh user admin
ssh user admin authentication-type password
ssh user admin service-type stelnet
stelnet server enable

ip route-static vpn-instance MGT 0.0.0.0 0.0.0.0 172.32.2.254
sysname USG1
save
```

### 4.2 业务接口与安全域模板

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

### 4.3 对象模板

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

### 4.4 安全策略模板

```text
security-policy
 rule name ONEOPS_TEST_POLICY
  source-zone trust
  destination-zone untrust
  source-address address-set ONEOPS_SRC_NET
  destination-address address-set ONEOPS_DST_NET
  service ONEOPS_WEB80
  action permit
 rule name ONEOPS_TEST_DENY
  source-zone trust
  destination-zone untrust
  source-address address-set ONEOPS_DENY_SRC
  destination-address address-set ONEOPS_DENY_DST
  service ONEOPS_SSH22
  action deny
#
```

### 4.5 `DNAT` 标准模板

当前真实设备可接受的 `DNAT` 模板如下：

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

### 4.6 `SNAT easy-ip` 标准模板

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

### 4.7 `SNAT_POOL` 标准模板

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

## 5. 当前必须固化的模板边界

### 5.1 管理平面边界

1. 当前稳定规格只有 `ethernet=6`
2. 当前标准管理口固定为专用 `GigabitEthernet0/0/0`
3. 当前不能把这台设备纳入“最后一个业务口做管理口”的统一规则

### 5.2 `DNAT` 边界

当前真实设备不接受下面这类平台既有假设：

```text
destination-zone trust
action destination-nat address 10.10.10.10 8080
```

设备实际返回：

```text
Error: The destination-zone or egress-interface configuration conflicts with the Destination NAT action.
```

因此：

1. `Huawei USG DNAT` 模板当前不能默认强带 `destination-zone`
2. 如果后续平台生成逻辑继续输出这一形态，就必须视为模板缺陷，而不是设备例外

### 5.3 `SNAT` 边界

当前已经实证可用的 `SNAT` 形态是：

1. `action source-nat easy-ip`
2. `action source-nat address-group <id>`

当前还没有在真实设备上落证的，不应直接并入标准模板：

1. 更复杂的 `SNAT_POOL` 多地址段组合
2. 更复杂的多服务、多对象复用策略

### 5.4 平台侧已发现薄弱点

当前配套单测虽然是绿色，但日志已经明确暴露：

```text
rule name [执行错误] ... undefined: NAT_POLICY
```

因此当前模板标准必须额外记录：

1. `nat-policy` 规则名称模板仍存在平台侧变量求值异常
2. 这不影响当前真机手工模板成立
3. 但会影响后续自动生成模板的可交付质量

## 6. 标准进入条件

`Huawei USG` 当前之所以可以算“已进入第一阶段标准模板”，是因为下面几项同时满足：

1. 管理面可稳定进入
2. 管理配置可保存并重启复验
3. `permit policy` 已有真实设备样本
4. `deny policy` 已有真实设备样本
5. `DNAT` 已有真实设备样本
6. `SNAT` 已有真实设备样本

## 7. 关联文档

1. [EVE-NG Huawei USG 防火墙标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-usg-firewall-standard-operation.md)
2. [EVE-NG Huawei USG 策略与 NAT 实机验证记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-usg-policy-nat-live-validation.md)
