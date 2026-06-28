# EVE-NG Ruijie 防火墙离线启动模板标准操作

更新时间：2026-06-28  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`  
适用镜像：`Ruijiefirewall-V1.03`

## 1. 目的

这份文档用于把当前已经打通的锐捷防火墙离线启动模板路径整理成标准操作。

它服务于两个目标：

1. 把已经实证可行的动作沉淀成可复用流程。
2. 把当前仍未补齐的能力边界明确写出来，避免后续测试建立在错误前提上。

截至 `2026-06-28`，这份文档的共享状态应固定为：

1. Ruijie 防火墙当前标准化模板已经完成收口。
2. 当前标准模板固定为：
   - `Ge0/0 + main`
   - 管理地址与默认路由
   - `SSH`
   - 离线启动模板改写与回灌流程
3. `VRF` 不再属于这台设备当前标准模板的一部分。
4. `get_deploy_mode` 这类单点 Web API 红灯，不再影响“标准化模板完成”这个结论。
5. 后续如果继续补 Ruijie，只属于增强适配，不再属于模板收口前置项。

当前应把这条标准理解为：

1. `Ge0/0` 首口管理模型已经实证。
2. 通过离线替换启动 `LYB` 文件拉起标准管理地址和 `SSH` 已经实证。
3. 当前镜像真实可复现的离线闭环应走 `yams --sysrepo-startup` + `sysrepocfg -X/-I`，不应把 `startup2xml` 当作这版镜像的标准入口。
4. 管理默认路由仍可继续沿这条链路补强。
5. 独立管理 `VRF` 不再作为当前标准化目标；锐捷防火墙当前按“`Ge0/0` 固定留在 `main`”收口。
6. 第一阶段标准先冻结为“`Ge0/0` 直连 Cisco 网关交换机管理桥并留在 `main`”，不再把“最后一个口转正式管理口”作为当前标准化目标。
7. 当前共享口径固定为：Ruijie 防火墙不纳入 OneOPS 的 `VRF` 支持范围，后续测试全部基于 `main` 管理模型推进。

## 2. 前置条件

执行前必须满足：

1. 已有一台可正常启动的 `Ruijiefirewall-V1.03` 节点。
2. 该节点默认管理口确认接在第一个口，对应设备侧 `Ge0/0`。
3. 已准备实验统一口令：`admin / admin@123`。
4. 已有可回退的基线启动文件目录。
5. 已能访问 EVE 宿主机并具备离线查看节点磁盘内容的能力。
6. 已有厂商运行时环境，可用于处理 `flash:/sysrepo/startup/*.startup` 的 `LYB` 文件。

当前已实证可用的离线相关能力包括：

1. `libyang`
2. `yanglint`
3. `sysrepocfg`
4. `yams --sysrepo-startup`
5. 厂商根文件系统内的 `YANG` 模块目录

当前要明确的版本边界：

1. 这版镜像内 `YANG_VERSION_INFO` 为 `1.5.40`。
2. 按厂商脚本逻辑，这版镜像的标准导入导出路径应使用 `sysrepocfg`，不是 `startup2xml`。
3. 直接执行 `startup2xml` 读取 `/mnt/flash/sysrepo/startup/ntos.startup` 时，当前已观察到 `Invalid LYB format version "0x00", expected "0x04"`，所以它不应继续作为这版镜像的主路径。

## 3. 输入参数说明

当前脚本原型围绕下面 6 个核心字段工作：

1. `mgmt_interface`
   当前锐捷固定使用 `Ge0/0`，这是对“最后一个口作为管理口”统一规则的厂商例外。
2. `mgmt_ip`
   管理地址，例如 `172.32.2.11`
3. `mgmt_prefix`
   管理地址前缀，例如 `24`
4. `mgmt_gateway`
   管理默认网关，目标值通常为 `172.32.2.254`
5. `mgmt_vrf_name`
   目标管理 `VRF` 名称，通常为 `MGT`
6. `ssh_enabled`
   是否启用管理面 `SSH`

这里要把当前边界写清楚：

1. 这 6 个字段仍足够支撑“首口管理地址 + `SSH` + 默认路由”的离线模板。
2. 但 `mgmt_vrf_name=MGT` 目前还不能自动推出“真实可用的独立管理 `VRF`”。
3. 在没有新的厂商级管理口绑定机制被找到前，不应把“把 `Ge0/0` 迁到 `MGT`”写成脚本当前已支持能力。

建议的最小输入文件：

```json
{
  "mgmt_interface": "Ge0/0",
  "mgmt_ip": "172.32.2.11",
  "mgmt_prefix": 24,
  "mgmt_gateway": "172.32.2.254",
  "mgmt_vrf_name": "MGT",
  "ssh_enabled": true
}
```

## 4. 基线文件准备

标准化前，先准备一份只读基线目录，例如：

```text
/abs/path/to/ruijie-baseline/
  ntos-interface.startup
  ntos-routing.startup
  ntos.startup
  ntos-xvrf.startup
```

要求：

1. 这 4 个文件必须来自已经能正常启动的同型号节点。
2. 基线目录只作为输入，不允许原地覆盖。
3. 如果只是继续沿用当前已实证路径，最关键的基线文件仍是 `ntos-interface.startup`。
4. `ntos.startup` 负责顶层 `VRF` 列表，不应再错误归到 `ntos-xvrf.startup`。
5. `ntos-xvrf.startup` 当前仍建议保留在基线目录中作为审计参考，但不要默认把它当成管理 `VRF` 的入口。

## 5. 启动模板渲染

### 5.1 当前脚本原型

当前仓库内的脚本原型命令如下：

```bash
python3 /Users/huangliang/project/OneOPS-ALL/scripts/ruijie-startup-template.py \
  --input /abs/path/to/ruijie-input.json \
  --baseline-dir /abs/path/to/ruijie-baseline \
  --output-dir /abs/path/to/ruijie-output
```

当前这版脚本已经完成并通过单测验证的内容是：

1. 输入合同校验
2. 基线文件存在性校验
3. 管理地址、`SSH`、管理默认路由、管理 `VRF` 的 XML 映射函数
4. 把管理 `VRF` 渲染到 `ntos.startup` 对应的 `ntos.xml`
5. 把 `ntos-xvrf.startup` 保留为当前未启用模块的审计副本
6. 从基线模块直接渲染 XML 审计产物
7. 输出目录审计文件落盘
8. 针对管理接口，补齐一部分已从真实设备导出中观察到的默认子节点

当前这版脚本稳定产出的审计文件是：

1. `render-input.json`
2. `render-summary.json`
3. `xml/ntos-interface.xml`
4. `xml/ntos-routing.xml`
5. `xml/ntos.xml`
6. `xml/ntos-xvrf.xml`

建议执行后立刻检查：

```bash
find /abs/path/to/ruijie-output -maxdepth 2 -type f | sort
cat /abs/path/to/ruijie-output/render-summary.json
sed -n '1,120p' /abs/path/to/ruijie-output/xml/ntos-routing.xml
```

当前状态说明：

1. 单测当前为 `15/15 PASS`。
2. 这说明“参数合同、模块校验、XML 渲染、渲染摘要、输出落盘、模块边界建模纠偏”已经进入可持续迭代状态。
3. 当前脚本默认把 `ntos.startup` 视为管理 `VRF` 的真实入口，不再错误地把它落到 `ntos-xvrf.startup`。
4. 这不等于“真实 `LYB` 四模块自动重生成已经全部打通”。
5. 单测当前验证的是 XML 渲染职责，不代表“独立管理 `VRF` 已在真实设备上打通”。
6. 当前渲染器已经开始对齐真实设备导出的管理接口结构，会为目标管理口补齐这组更完整的默认 profile：
   - `enabled`
   - `working-mode=route`
   - `reverse-path=true`
   - `local-defend/access-control`
   - `if-mon/monitor`
   - `ipv4/enabled`
   - `ipv4/pppoe`
   - `ipv6/enabled`
   - `ipv6/nd`
   - `network-stack/ipv4`
   - `network-stack/ipv6`
   - `upload-bandwidth`
   - `download-bandwidth`
   - `ethernet`
   - `isp-config`
7. 当某个源 `VRF` 下只剩这一个被迁移的物理口时，渲染器还会移除迁移后留下的空 `interface` 容器，避免生成明显偏离设备习惯的空壳结构。
8. 本地库里已经补了 `render_full_ntos_xml()`，可以直接对 `sysrepocfg -X` 导出的整库 `ntos.xml` 一次性应用：
   - `VRF` 渲染
   - 管理口迁移与管理地址渲染
   - 管理默认路由渲染

### 5.2 `nc-cli` 真实行为补充

在真实设备上又补了一轮 `nc-cli` 行为验证，当前应固定下来的结论是：

1. 设备前台登录入口虽然就是 `nc-cli`，但它没有开启 `edit running` 所需的 `-e` 开关。
2. 从厂商二进制帮助信息可确认：
   - `nc-cli -e` 才会启用 `edit running`
   - 当前控制台前端没有把这个能力暴露出来
3. 因此，当前登录入口下这些命令都会直接失败：
   - `edit`
   - `edit running`
   - `load`
   - `save`
   - `commit`
4. 这不是配置路径写错，而是前端能力被裁掉。

同时也确认了设备前端仍然保留的一条文件配置链：

1. `copy xml running file <name>` 可用
2. `copy xml startup file <name>` 可用
3. 生成的文件位于：
   - `/home/admin/.config/nc-cli/conf/<name>`
4. `show config file <name> ...` 可直接读取这些设备原生 XML 文件
5. `validate file <name>` 可直接校验这些文件

当前还要写清楚一条限制：

1. `copy xml file <name> startup` 当前会被拒绝
2. 设备返回：
   - `ERROR: To update 'startup', source must be 'running'`
3. 这说明即使我们拿到了设备原生 XML 文件，当前受限前端下仍缺少“把修改后的 file 重新装回 running/staging 再 commit”的最后一步

### 5.3 当前真实可复现的 `LYB` 闭环

截至 2026-06-27，已经实证可行的真实离线路径是：

1. 从节点磁盘中复制出完整 `sysrepo` 工作目录，而不是只拿单个 `startup` 文件。
2. 在厂商根文件系统 `chroot` 里，把这份 `sysrepo` 目录绑定到 `/mnt/flash/sysrepo`。
3. 先执行 `yams --sysrepo-startup`，把 `startup` 数据装载到 `sysrepo` 运行态。
4. 使用 `sysrepocfg -X` 导出可读 XML。
5. 修改目标 XML。
6. 使用 `sysrepocfg -I` 把 XML 替换导回 `startup` 数据。
7. 再次执行 `yams --sysrepo-startup` 和 `sysrepocfg -X` 做重导出校验。
8. 覆盖节点磁盘内对应的 `startup` 文件。
9. 重启节点验证。

当前已经实证成功的是：

1. `ntos-interface.startup`
2. 管理地址改为 `172.32.2.11/24`
3. 管理面 `SSH` 打开
4. 重启后 `ping` 与 `SSH` 均成功
5. 在独立克隆 `sysrepo` 副本中，使用 `sysrepocfg -I` 可把 `Ge0/0` 管理地址从 `172.32.2.11/24` 干净替换为 `172.32.2.77/24`
6. 该替换会真实落盘到 `ntos-interface.startup`
7. 在独立克隆 `sysrepo` 副本中，一次性导入包含 `MGT VRF + Ge0/0 + 0.0.0.0/0 -> 172.32.2.254` 的整库 XML 后，`ntos.startup`、`ntos-interface.startup`、`ntos-routing.startup` 三个模块都会同步发生真实落盘变化
8. 重导出的整库 XML 已证明：
   - `ntos.startup` 中出现 `<vrf><name>MGT</name></vrf>`
   - `ntos-interface.startup` 中 `Ge0/0` 已落入 `MGT` VRF
   - `ntos-routing.startup` 中已出现 `MGT` VRF 下的默认路由

当前仍应视为待补强项的是：

1. 把这组三模块结果替换进真实节点后做回启验证
2. 验证设备启动后是否能在 CLI 中看到预期的 `MGT VRF` 与默认路由
3. 自动化串联“基线 `LYB` -> XML -> 新 `LYB`”的完整脚本

### 5.3 当前标准命令骨架

下面这组命令是当前已经跑通的标准骨架，重点不是固定目录名，而是固定动作顺序：

```bash
ROOT=/tmp/rgfw-rootfs2
WORK=/tmp/ruijie-roundtrip-import

rm -rf "$WORK"
mkdir -p "$WORK"
cp -a /tmp/ruijie-work/sysrepo "$WORK/sysrepo"

umount "$ROOT/mnt/flash/sysrepo" 2>/dev/null || true
mount --bind "$WORK/sysrepo" "$ROOT/mnt/flash/sysrepo"
mountpoint -q "$ROOT/proc" || mount -t proc proc "$ROOT/proc"
mountpoint -q "$ROOT/sys" || mount --bind /sys "$ROOT/sys"
mountpoint -q "$ROOT/run" || mount --bind /run "$ROOT/run"
mkdir -p "$ROOT/dev/shm"
mountpoint -q "$ROOT/dev" || mount --bind /dev "$ROOT/dev"
mountpoint -q "$ROOT/dev/shm" || mount --bind /dev/shm "$ROOT/dev/shm"

rm -f /dev/shm/sr*
chroot "$ROOT" /usr/bin/yams --sysrepo-startup
chroot "$ROOT" /usr/bin/sysrepocfg -X/tmp/before.xml -m ntos -d startup -f xml -v3 -t 600

sed 's|172.32.2.11/24|172.32.2.77/24|g' "$ROOT/tmp/before.xml" > "$ROOT/tmp/after.xml"

chroot "$ROOT" /usr/bin/sysrepocfg -I/tmp/after.xml -m ntos -d startup -f xml -v3 -t 600

rm -f /dev/shm/sr*
chroot "$ROOT" /usr/bin/yams --sysrepo-startup
chroot "$ROOT" /usr/bin/sysrepocfg -X/tmp/after-export.xml -m ntos -d startup -f xml -v3 -t 600
```

这一组命令当前已经验证出 3 个重要事实：

1. `-X` 可以稳定导出整份 `ntos` 配置 XML。
2. `-I` 可以把修改后的 XML 干净替换回 `startup` 数据。
3. `ntos-interface.startup` 会发生真实哈希变化，而 `ntos.startup` 在本轮接口地址改动里保持不变。

当前对模块职责的最新判断也应固定下来：

1. `ntos.startup` 负责顶层 `VRF` 列表。
2. `ntos-interface.startup` 负责接口所在 `VRF` 下的物理接口配置。
3. `ntos-routing.startup` 负责各 `VRF` 下的静态路由配置。
4. `ntos-xvrf.startup` 当前更接近跨 `VRF` 逻辑接口能力，不应默认当作“管理口放入 MGT VRF”的主入口。
5. `ntos-routing` 相关节点在 XML 中应落入 `urn:ruijie:ntos:params:xml:ns:yang:routing` 命名空间，不能继续按无命名空间或 `ntos` 根命名空间误建。
6. `ntos-interface` 下的 `physical/port` 叶子确实存在，但对 `Ge0/0` 来说，仅补 `port pci-b0s3` 仍不足以让独立 `MGT VRF` 进入可用运行态。
7. 设备自己通过 `copy xml running file` 导出的接口 XML，比我们当前离线原型包含更多默认子节点，例如：
   - `ipv4/pppoe`
   - `ipv6/nd`
   - `network-stack`
   - `upload-bandwidth`
   - `download-bandwidth`
   - `ethernet`
   - `isp-config`

这条差异当前还不能直接定义为根因，但它是后续比对离线模板与设备原生配置时必须盯住的重点。

同时，2026-06-28 又补出一个更细的结论：

1. `copy xml running file` 导出的“设备原生文件视图”和 `sysrepocfg -X` 导出的“整库 `ntos` 视图”不是完全同一层表示。
2. 在真实离线 roundtrip 中，把 `Ge0/1` 迁入 `MGT VRF` 时，即使候选整库 XML 中显式带上了：
   - `pppoe`
   - `nd`
   - `upload-bandwidth`
   - `download-bandwidth`
   - `ethernet`
   - `isp-config`
3. `sysrepocfg -I` 仍会成功接受该 XML。
4. 但 `yams --sysrepo-startup + sysrepocfg -X` 重导出后，这些接口级默认节点会被厂商链路自动规整掉，只保留核心运行表达，例如：
   - `enabled`
   - `working-mode`
   - `ipv4/address`
   - `ipv6/enabled`
   - `reverse-path`
   - `monitor`
   - `access-control`
5. 这说明对当前镜像来说：
   - 设备前台文件导出更接近“富默认值视图”
   - `sysrepocfg` 整库导出更接近“规范化视图”
6. 因此后续离线模板工作应把“整库 `ntos` roundtrip 可接受并能稳定重导出”作为更高优先级的判断标准，而不是强求最终重导出必须保留所有前台文件视图中的默认空节点。

同时也要把错误路径写清楚：

1. `sysrepocfg -E` 是 merge 语义，不适合作为这条标准的默认回写命令。
2. 当前已实测，使用 `-E` 改管理地址会在 `Ge0/0` 下留下两个 `<address>`，形成脏配置。
3. 因此，这条标准当前必须使用 `-I`，不能默认使用 `-E`。

## 6. 替换到 EVE 节点

当前已实证可用的替换方式是离线覆盖节点磁盘中的启动文件。

建议先做节点停机，再执行替换。示例命令如下：

```bash
guestfish --rw -a /opt/unetlab/tmp/<tenant>/<lab>/<node>/hda.qcow2 <<'EOF'
run
mount /dev/sda6 /
upload /abs/path/to/output/ntos-interface.startup /sysrepo/startup/ntos-interface.startup
EOF
```

说明：

1. 上面这条只对应当前已经实证成功的 `ntos-interface.startup` 替换路径。
2. `ntos-routing.startup` 和 `ntos-xvrf.startup` 在没有真实回启验证前，不应写成“标准已完成”。
3. 如果后续补齐了真实 `LYB` 生成结果，再把这两个文件纳入同一替换段。
4. 截至 2026-06-28，在独立克隆 `sysrepo` 副本中，`Ge0/1 -> MGT VRF -> 172.32.2.21/24 -> 0.0.0.0/0 via 172.32.2.254` 这一整库 XML 已实证可被 `sysrepocfg -I` 接受并成功重导出。
5. 该 roundtrip 的模块变化仍然只落在：
   - `ntos.startup`
   - `ntos-interface.startup`
   - `ntos-routing.startup`
6. `ntos-xvrf.startup` 在这轮 `Ge0/1` 管理 `VRF` roundtrip 中保持不变。
7. 截至 2026-06-28，另一个更激进的整库候选也已在独立克隆 `sysrepo` 副本中通过 roundtrip：
   - `physical enp0s22`
   - `port pci-b0s22`
   - `172.32.2.22/24`
   - `vrf MGT`
   - `0.0.0.0/0 -> 172.32.2.254`
8. 这条“最后一个口”候选在离线 roundtrip 中同样只改动：
   - `ntos.startup`
   - `ntos-interface.startup`
   - `ntos-routing.startup`
9. `ntos-xvrf.startup` 在这条“最后一个口” roundtrip 中同样保持不变。

## 7. 重启与验证

替换完成后，启动节点并执行最小验证。

当前已实证验证项：

```bash
ping -c 1 172.32.2.11
ssh admin@172.32.2.11
```

当前“通过”标准必须分开判断：

1. 已实证通过
   - 管理地址生效
   - `SSH` 登录成功
   - 首口管理模型成立
   - `sysrepocfg -X/-I` 离线 XML 闭环成立
2. 待补实证
   - 独立管理 `VRF` 可见
   - 管理默认路由位于预期 `VRF`
   - `Ge0/0` 是否存在厂商专用的管理口迁移机制
   - 最后一个口是否能承载完整 `SSH/HTTPS` 管理服务

因此，只有当下面 4 项都被真实回启验证后，锐捷模板才应升级为“完整标准化”：

1. 管理地址可达
2. `SSH` 可达
3. 独立管理 `VRF` 可见
4. 管理默认路由可见且位置正确

2026-06-28 的真实回启又补出一条必须单独保留的结论：

1. 把 `RG-FW1` 的连线从接口 `id=0` 切到接口 `id=19`，同时保持 `network_id=8` 不变，意味着它仍然连在 Cisco `GW-SW e1/3` 上。
2. 离线写入 `enp0s22 + port pci-b0s22 + 172.32.2.22/24 + vrf MGT + default route` 后：
   - `show config xml running vrf MGT interface physical enp0s22` 成立
   - `cmd ping 172.32.2.254 count 2 vrf MGT` 成立
   - 从 Cisco 管理桥侧强制走 `vnet0_8` 时，`ping 172.32.2.22` 成立
3. 但 `SSH/HTTPS` 没有成立：
   - `172.32.2.22:22` 超时
   - `172.32.2.22:443` 超时
   - 抓包只看到 `SYN` 发出，没有看到 `SYN-ACK` 或 `RST`
4. 同时，`show state xml vrf MGT interface physical enp0s22` 仍返回 `No data`
5. 因此这条“最后一个口”路径当前只能归类为：
   - `L3/ICMP 已打通`
   - `SSH/HTTPS 管理服务未打通`
   - `不能取代 Ge0/0 成为当前稳定标准管理口`

在当前这轮实验之后，还应额外保留一句明确提醒：

1. 已做过一次“只补 `port pci-b0s3`”的最小实验。
2. 该实验让 `Ge0/0` 从 `main` 运行态消失，但并没有进入 `MGT` 运行态。
3. 因此，当前不应继续把“只差补一个 `port` 叶子”当作锐捷管理 `VRF` 的默认修复方向。

## 8. 证据留存

每次执行这条标准操作，至少保留：

1. 输入文件 `ruijie-input.json`
2. 输出目录中的 `render-input.json`
3. 输出目录中的 `render-summary.json`
4. 输出目录中的 XML 审计文件
5. 被替换的 `startup` 文件副本
6. 节点重启前后的操作记录
7. `ping` 结果
8. `SSH` 登录结果
9. 如果失败，保留失败模块名、报错信息和当前边界说明

## 9. 已支持字段

截至 2026-06-27，当前已进入标准化流程的字段分层如下：

1. 已实证生效
   - `mgmt_interface=Ge0/0`
   - `mgmt_ip`
   - `mgmt_prefix`
   - `ssh_enabled`
2. 已有渲染设计与单测，但尚未完成真实回启闭环
   - `ntos.startup` 层的 `mgmt_vrf_name`
   - `mgmt_gateway`
3. 预留但未纳入当前脚本合同
   - 业务三层互联批量生成
   - `OSPF`
   - 主机名
   - 管理员密码离线替换

## 10. 当前边界

这条标准当前最重要的边界是：

1. 当前镜像的默认稳定管理口仍是首口 `Ge0/0`。
2. `ethernet=20` 不等于 `20` 个统一防火墙业务口，当前只有前 `8` 个口进入标准防火墙接口命名。
3. 官方备份包真实载荷仍是加密内容，不适合作为当前标准化入口。
4. 这版镜像的标准离线路径当前应理解为 `yams --sysrepo-startup` + `sysrepocfg -X/-I`，而不是 `startup2xml`。
5. `sysrepocfg -E` 是 merge，不适合作为默认回写命令，否则会把管理地址叠加成脏状态。
6. 当前脚本原型已把 `ntos/interface/routing/xvrf` 的模块边界纠偏，但还没有接通真实 `LYB` 全自动重生成。
7. 不再把管理 `VRF` 列为当前标准化验收项，后续只保留为边界证据。
8. 最新实证表明 `Ge0/0` 带有特殊管理口属性；即使把 `port pci-b0s3` 补进 `MGT` 配置，它也不会自动成为可用的 `MGT` 物理接口。
9. 最新实证同时表明：最后一个口 `enp0s22` 可以通过离线整库方式进入 `MGT VRF` 并形成到 Cisco 网关的 `L3/ICMP` 连通，但当前仍未形成 `SSH/HTTPS` 管理服务。
10. 因此当前阶段不继续扩展多管理口模板合同，标准输入仍固定围绕 `mgmt_interface=Ge0/0` 收敛。
11. 如果目标是让 `172.32.2.11` 对 `172.32.2.0/24` 之外的来源形成稳定回程，不能先假定现场已经存在 `MGT` 默认路由；最新 live 备份解密显示当前 `startup.xml` 与 `running.xml` 仍只有 `main`，因此必须先区分“离线候选曾被接受”与“现场当前实际生效配置”。

## 10. 2026-06-28 补充结果

围绕“`vrf MGT` 的默认路由必须补齐”又补了一轮真实节点排查，当前应固定下来的结果是：

1. 当前节点原始整库 `ntos` 导出中只有 `main`，没有 `MGT`。
2. 已基于该基线生成过“只补 `MGT VRF + default route`、不迁移 `Ge0/0`”的新整库 XML。
3. 厂商离线链路确实接受过这份候选：
   - 重导出后可看到 `MGT`
   - 可看到 `0.0.0.0/0`
   - 可看到 `172.32.2.254`
   - 同时仍保留 `Ge0/0 172.32.2.11/24`
4. 节点按该方向重启后，`172.32.2.11:22` 一度保持可达，且管理桥侧 `ICMP` 仍成立。
5. 但最新又拿到了更直接的现场证据：
   - 设备原生 `backup-config` 导出的 `running-cfg-20260628092809.tar.gz` 已可通过厂商 `libconf_compress.so` 离线解密
   - 解密后的 `startup.xml` 与 `running.xml` 中都只有 `vrf main`
   - 两个文件中都可见 `Ge0/0` 与 `172.32.2.11/24`
   - 两个文件中都看不到 `MGT`
   - 两个文件中也看不到 `0.0.0.0/0 -> 172.32.2.254`
6. 同时，live CLI 也与这份导出互相印证：
   - `show config vrf MGT` 为空
   - `show ipv4-routes` 只有 `172.32.2.0/24 is directly connected, Ge0/0`
7. 这说明一个必须纠偏的事实：
   - “离线候选曾被接受”成立
   - 但“当前现场 startup/running 已经存在 `MGT` 默认路由”不成立
   - 因此不能再把“`MGT` 路由已补齐”当作当前真实节点事实
8. 这轮之后又补出一个更关键的结构性结论：
   - 在独立 `sysrepo` 克隆里，`Ge0/0 -> MGT + 172.32.2.11/24 + 0.0.0.0/0 -> 172.32.2.254` 的整库候选其实可以通过厂商 `sysrepocfg -I/-X` roundtrip
   - 这说明“把 `Ge0/0` 放进 `MGT`”并不是单纯在 YANG/import 阶段就被拒绝
9. 同版本正常启动时，`yang_install` 不会再次执行 `sysrepo_pre_startup`
   - 它会进入 `Keep old yang data, starting...`
   - 只执行 `sysrepo_pre_running`
10. `sysrepo_pre_running` 对应 `yams.__main__.sysrepo_running()`
    - 它会遍历所有 service
    - 对每个 service 调用 `config_file_path('running')`
    - 然后把返回的 XML 再 merge 进 `running`
11. 对物理接口服务来说：
    - `PhysicalInterfaceService.config_file_path('running')` 返回 `/tmp/iface_running.xml`
    - 这个文件由 `devcap_generate_iface_config(ds='running', ...)` 生成
    - 其根 `vrf` 被硬编码为 `main`
12. 已用一份最小伪造 `interfaces.xml` 做过离线复现实验，结果进一步坐实了这一点：
    - 当 `Ge0/0` 被标成 `is_mgmt=1` 且携带 `172.32.2.11/24` 时
    - `devcap_generate_iface_config(ds='startup')` 生成的是 `vrf main + physical Ge0/0 + access-control + 172.32.2.11/24`
    - `devcap_generate_iface_config(ds='running')` 生成的是 `vrf main + physical Ge0/0/Ge0/1` 的纯骨架
13. live CLI 的 `debug-support` 白名单也补出了一层运行期旁证：
    - `cmd debug-support cmd exec lsof | match 6212` 可见主 YAMS 进程是 `6212 /usr/bin/python3.9`
    - 该进程持有大量 `/dev/shm/srsub_ntos.running`
    - 这与 `sysrepo_running()` 在运行阶段反复围绕 `running` 数据面工作的代码路径一致
14. 因此，当前更准确的根因方向已经从“是否缺少 `MGT` 默认路由”收敛为：
    - `Ge0/0` 的 `MGT` 迁移在离线 startup 数据层并非绝对不成立
    - 但运行阶段很可能又根据 `devcap/is_mgmt` 相关逻辑，把物理口骨架重新并入 `main`
    - 后续如果继续排查，应优先追 `interfaces.xml -> iface_running.xml -> sysrepo_running -> physical apply/netns` 这条链，而不是继续盲目补通用静态路由
15. 2026-06-28 又补了一轮更直接的业务口 live 验证：
    - 保留 `Ge0/0` 在 `main`
    - 把真实业务口 `Ge0/1` 也接到 `network_id=8`
    - 离线整库写入 `vrf MGT + Ge0/1 + 172.32.2.21/24 + 0.0.0.0/0 -> 172.32.2.254`
16. 这一轮 live 结果说明：
    - `show config vrf MGT` 成立
    - `show state xml vrf MGT` 成立
    - `show interface name Ge0/1 vrf MGT` 可见 `172.32.2.21/24`
    - 但 `show state xml vrf MGT interface physical Ge0/1` 仍是 `No data`
    - `show ipv4-routes vrf MGT` 为空
    - `cmd ping 172.32.2.254 count 2 vrf MGT` 仍报 `Network is unreachable`
17. 同时，桥侧抓包又证明这不是“完全无响应”：
    - 外部探测 `172.32.2.21` 时，可看到设备发出 `ARP who-has 172.32.2.254 tell 172.32.2.21`
    - Cisco 网关也回了 `ARP Reply`
    - 但最终没有形成 `ICMP` 回包，也没有 `SSH/HTTPS` 建连
18. 因此，当前对“锐捷是否支持 `VRF`”的共享口径应固定为：
    - 镜像存在部分 `VRF` 配置能力
    - 但这版镜像下 `VRF` 的真实接口运行态/路由安装/管理服务仍不完整
    - OneOPS 当前不把 Ruijie 防火墙纳入 `VRF` 支持范围
    - 后续初始化、采集、监控、策略与自动化测试统一按 `Ge0/0 + main` 管理模型执行
