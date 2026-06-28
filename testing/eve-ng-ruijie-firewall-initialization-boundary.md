# EVE-NG Ruijie 防火墙首轮初始化与边界记录

更新时间：2026-06-28  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份文档记录 `Ruijiefirewall-V1.03` 在当前 EVE 环境中的第一轮初始化结果。

后续标准化操作统一参照：
[EVE-NG Ruijie 防火墙离线启动模板标准操作](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-ruijie-firewall-offline-startup-template-standard.md)

当前目标不是把它直接定义成“已完全标准化模板”，而是先把下面几件事落清楚：

1. 镜像是否能稳定启动。
2. 默认登录入口是什么。
3. 管理口模型是什么。
4. `ethernet=20` 扩展后是否仍符合 OneOPS 的统一设备规则。
5. 哪些部分已经打通，哪些部分目前还是边界。

## 2. 当前结论

截至 2026-06-27，`Ruijiefirewall-V1.03` 在当前 EVE 环境中已经确认：

1. 镜像可以稳定启动。
2. 默认控制台登录可用。
3. 首登默认账号为 `admin / firewall`。
4. 首登可以把密码改为实验统一口令 `admin@123`。
5. 默认管理平面落在第一个口 `Ge0/0`，默认地址为 `192.168.1.200/24`。
6. 把管理连线接到第一个口后，宿主机侧可以实际 `ping` 通默认管理地址。
7. 默认已经开放 `HTTPS` 与 `ping` 管理访问，但默认 `ssh` 为关闭状态。
8. 官方 `backup-config -> import-config` 配置回灌链路已经实证可用。
9. `flash:/sysrepo/startup/*.startup` 已实证可以离线解码为可读 XML，并重新生成 `LYB` 启动文件。
10. 已实证通过离线替换 `ntos-interface.startup`，让设备直接以 `172.32.2.11/24` 启动，并成功通过 `SSH` 登录。

同时也已经确认了重要边界：

1. 在 `ethernet=20` 形态下，这台设备并没有形成“20 个统一可管理防火墙接口”。
2. 只有前 8 个口进入了标准防火墙接口命名：`Ge0/0` 到 `Ge0/7`。
3. 后 12 个口虽然以虚拟网卡形式存在，但在设备状态里仍表现为 Linux 风格接口名，例如 `enp0s11` 到 `enp0s22`。
4. 按 OneOPS 统一规则把管理网络接到“最后一个口”时，默认管理面不能直接使用。
5. Web 管理面已实证可达，但验证码机制使浏览器自动化登录暂时不适合作为标准初始化主路径。
6. `Ge0/0` 对应的真实物理端口是 `pci-b0s3`，并且 `show interface port state` 显示它带有 `is-mgmt true` 标记。
7. 已实证把 `Ge0/0` 迁入独立 `MGT VRF` 后，即使补了 `port pci-b0s3` 绑定，管理地址与默认路由仍不会进入可用运行态。
8. 当前阶段正式冻结为：`Ge0/0` 固定留在 `main`，Ruijie 防火墙不纳入 OneOPS 的 `VRF` 支持范围。

因此，这台设备当前应标记为：

1. `已实证默认启动与默认管理入口`
2. `已实证首口管理模型`
3. `20 口扩展存在接口模型边界`
4. `已实证官方备份包回灌链路`
5. `已实证离线启动模板改写路径`
6. `已确认 Ge0/0 特殊管理口边界`
7. `待补参数化模板与默认路由标准化`
8. `已形成离线启动模板标准操作草案，脚本原型单测已全绿`
9. `第一阶段标准已冻结为 Ge0/0 管理，不继续把最后一个口作为正式管理口推进`

## 3. 本次实验规格

### 3.1 节点规格

1. EVE 模板：`Ruijiefirewall`
2. 镜像：`Ruijiefirewall-V1.03`
3. CPU：`2`
4. RAM：`2048`
5. `qemu_nic`：`virtio-net-pci`
6. 节点 `ethernet`：`20`

### 3.2 管理拓扑

1. 网关设备：Cisco IOL `GW-SW`
2. 管理网络：独立 `bridge`
3. 第一轮错误连线：把管理口接到最后一个口
4. 修正后连线：把管理口接到第一个口

## 4. 已验证事实

### 4.1 默认登录

控制台启动完成后，出现：

1. `Welcome to NTOS`
2. `firewall login:`

已验证：

1. 默认用户名：`admin`
2. 默认密码：`firewall`
3. 首登强制改密
4. 新口令 `admin@123` 可直接接受

## 4.2 默认配置特征

通过 `show config` 已看到：

1. 默认物理管理口：`physical Ge0/0`
2. 默认地址：`192.168.1.200/24`
3. 默认访问控制：
   - `https true`
   - `ping true`
   - `ssh false`
4. 全局 `ssh-server` 已存在
5. `user-password-policy` 中 `first-login-modify-password false`

## 4.3 接口模型

通过 `show state network-port` 已看到：

1. 前 8 个口被识别为：
   - `Ge0_0`
   - `Ge0_1`
   - `Ge0_2`
   - `Ge0_3`
   - `Ge0_4`
   - `Ge0_5`
   - `Ge0_6`
   - `Ge0_7`
2. 后续扩展口则仍显示为 Linux 风格接口名，例如：
   - `enp0s11`
   - `enp0s12`
   - `...`
   - `enp0s22`

这说明 `ethernet=20` 只是把 20 张虚拟网卡拉起来了，但设备配置树并没有把它们全部收敛成统一的防火墙端口模型。

进一步实证还看到：

1. `Ge0/0` 对应 `network-port pci-b0s3`
2. `Ge0/0` 的 `port-attr is-mgmt` 为 `true`

这说明首口不仅是“默认管理口”，还很可能是镜像内部定义的“特殊管理口”。

## 4.4 管理口验证结果

### 4.4.1 把管理口接到最后一个口时

验证结果：

1. 默认管理地址 `192.168.1.200/24` 无法从宿主机侧 `ping` 通。
2. 说明“最后一个口作为管理口”的统一规则，在这台锐捷镜像上不能直接套用。

### 4.4.2 把管理口改接到第一个口时

验证结果：

1. 把连线改到节点第一个口后，宿主机 `vnet0_8` 上对 `192.168.1.200` 的 `ping` 实际成功。
2. 说明默认管理面模型与 `Ge0/0` 一致。

## 4.5 Web 管理面

已验证：

1. `https://192.168.1.200` 可达。
2. Web 登录页可正常打开。
3. 自动化登录过程中，验证码是当前最大阻碍。

当前结论：

1. Web 管理面本身不是边界。
2. 验证码机制让“浏览器自动化初始化”暂时不适合作为首选标准路径。

## 4.6 配置导出与回灌能力

已验证：

1. 设备支持 `cmd export-config`。
2. 设备支持 `cmd backup-config`，会在 `flash:/config/backup` 生成官方备份包。
3. 设备支持 `cmd import-config location <path>`，可从本地任意 `.tar.gz` 路径回灌。
4. 设备本地可看到 `flash:/config` 目录。
5. 设备本地可看到：
   - `startup_version.conf`
   - `running_version.conf`
6. 设备本地可看到：
   - `flash:/config/backup/running-cfg-20260627203152.tar.gz`
   - `tmp:/config/export-startup.tar.gz`
7. 已实测把设备自己导出的备份包通过：
   - `cmd xml import-config location /mnt/flash/config/backup/running-cfg-20260627203152.tar.gz`
   成功回灌到设备。

这说明锐捷这条线至少已经具备“官方导出包生成”和“官方导出包回灌”的闭环能力。

## 4.7 备份包与启动配置落盘结构

已验证：

1. 官方备份包虽然命名为 `.tar.gz`，实际外层是普通 `tar` 包。
2. 外层包当前至少包含：
   - `Config.tar.gz.en`
   - `Config_backup.ver`
3. `Config.tar.gz.en` 当前识别为加密载荷，不能直接按明文配置包修改。
4. `flash:/sysrepo/startup` 下存在按模块拆分的启动配置文件，例如：
   - `ntos-interface.startup`
   - `ntos-local-defend.startup`
   - `ntos-ssh-server.startup`
   - `ntos-system.startup`
5. 这些 `.startup` 文件当前识别为 `LYB` 二进制格式，不是可直接手改的明文文本。

这说明当前真正的边界不是“设备没有回灌能力”，而是“设备把正式配置封装成了加密备份包和 `LYB` 启动数据，离线模板改造还需要继续解码或转化”。

## 4.8 `LYB` 解码与离线启动模板改写

截至 2026-06-27，已经进一步实证：

1. 通过解包镜像根文件系统，可以在厂商原生运行时里找到：
   - `libyang`
   - `yanglint`
   - `sysrepocfg`
   - `/usr/share/yams/yang/*.yang`
2. 在 `chroot` 到厂商根文件系统后，`libyang` 已实证可以加载全部 YANG 模块，并成功解析：
   - `ntos-interface.startup`
   - `ntos-local-defend.startup`
   - `ntos-ssh-server.startup`
   - `ntos-system.startup`
3. 已读出的关键默认配置包括：
   - `Ge0/0` 默认地址 `192.168.1.200/24`
   - `Ge0/0` 默认 `https true`
   - `Ge0/0` 默认 `ping true`
   - `Ge0/0` 默认 `ssh false`
   - 全局 `ssh-server enabled true`
   - `admin` 用户密码哈希已随首登改密同步进启动配置
4. 已通过“导出 XML -> 修改 `Ge0/0` 管理地址与 `ssh` 标志 -> 重新生成 `LYB` -> 覆盖 `flash:/sysrepo/startup/ntos-interface.startup` -> 重启节点”完成一次离线模板闭环。
5. 本次闭环的实测结果是：
   - 设备重启后直接以 `172.32.2.11/24` 响应
   - 宿主机侧 `ping 172.32.2.11` 成功
   - `admin / admin@123` 的实际 `SSH` 登录成功
6. 已进一步确认：
   - `ntos-routing.startup` 当前只有 `main` VRF 占位内容
   - `ntos-xvrf.startup` 当前基本为空
   - 这说明“默认路由”和“额外管理 VRF”这两部分目前还没有进入现成启动模板，后续需要单独补建

这条结果非常关键，因为它说明当前锐捷镜像虽然不能直接明文改官方备份包，但已经具备“通过启动 `LYB` 文件做离线标准化初始化”的可行路径。

## 4.9 管理 VRF 跟进实验

围绕“是否能把首口管理面迁入独立 `MGT VRF`”又做了一轮最小实验，结论如下：

1. 从当前节点导出的整库 XML 中，已确认 `ntos-interface` 模型下确实存在可配置的 `physical/port` 叶子。
2. `Ge0/0` 对应的真实端口名是 `pci-b0s3`。
3. 已做过最小补丁实验：
   - 保留 `MGT VRF`
   - 保留 `Ge0/0 172.32.2.11/24`
   - 保留 `0.0.0.0/0 -> 172.32.2.254`
   - 只新增 `port pci-b0s3`
4. 该补丁真实落盘到 `ntos-interface.startup` 后，配置面能看到 `show config xml running vrf MGT interface physical Ge0/0` 中存在 `port pci-b0s3`。
5. 但运行态没有变成可用管理面：
   - `show state xml vrf MGT` 中没有 `Ge0/0` 物理接口
   - `show state xml vrf main` 中也不再出现 `Ge0/0`
   - `cmd ping 172.32.2.254 count 2 vrf MGT` 返回 `Network is unreachable`
   - 宿主机侧对 `172.32.2.11` 的 `ping` 与 `22/tcp` 都失败
6. 实验后已把节点恢复到上一份可用启动基线，并再次实证：
   - `ping 172.32.2.11` 恢复成功
   - `22/tcp` 恢复成功

当前更稳妥的结论应写清楚：

1. `Ge0/0` 不是普通业务物理口，它至少带有“特殊管理口”属性。
2. 仅靠 `VRF + 接口 + 路由 + port` 这组通用 `sysrepo` 节点，当前还不能把它稳定迁入非 `main` VRF。
3. 后续如果继续追管理 `VRF`，应把方向改成：
   - 寻找厂商是否还存在单独的“管理口绑定机制”
   - 或接受当前镜像的现实边界：`Ge0/0` 只适合继续留在 `main`

## 4.10 `nc-cli` 文件链与当前前端限制

围绕“是否能先通过设备 CLI 改配置，再导出底层文件”又补了一轮实证，当前应固定下来的结论如下：

1. 当前控制台前端虽然就是 `nc-cli`，但没有开启 `edit running` 所需的 `-e` 开关。
2. 从厂商二进制帮助信息可确认：
   - `nc-cli -e` 才会启用 `edit running`
   - 当前前台登录入口没有把这条编辑链暴露出来
3. 因此，在当前登录入口下这些命令都会直接失败：
   - `edit`
   - `edit running`
   - `load`
   - `save`
   - `commit`
4. 这说明当前阻塞点不是命令写错，而是前端能力本身被裁掉了。

同时也确认了一个仍然可用的设备原生文件链：

1. `copy xml running file <name>` 可用。
2. `copy xml startup file <name>` 可用。
3. 生成的设备原生 XML 文件位于：
   - `/home/admin/.config/nc-cli/conf/<name>`
4. `show config file <name> ...` 可直接读取这些文件。
5. `validate file <name>` 可直接校验这些文件。

当前还要把限制写清楚：

1. `copy xml file <name> startup` 当前会被拒绝。
2. 设备返回：
   - `ERROR: To update 'startup', source must be 'running'`
3. 这说明即使已经拿到设备原生 XML，当前受限前端下仍缺少“把修改后的 file 回装到 running/staging 再 commit”的最后一步。

这轮文件导出还补出一个很重要的比对点：

1. 设备自己导出的 `Ge0/1` 接口 XML，比当前离线原型包含更多默认子节点，例如：
   - `ipv4/pppoe`
   - `ipv6/nd`
   - `network-stack`
   - `upload-bandwidth`
   - `download-bandwidth`
   - `ethernet`
   - `isp-config`
2. 这条差异当前还不能直接定义为 `MGT VRF` 失败的根因。
3. 但它已经成为后续离线模板与设备原生配置做逐项比对时必须重点盯住的结构差异。

## 4.11 最后一个口连 Cisco 网关的真实回启验证

围绕“是否能把最后一个口真正做成带外管理口”，又做了一轮更贴近目标拓扑的真实回启验证。这一轮不是把设备单独挂云，而是明确保持它连在 Cisco 网关上：

1. `RG-FW1` 的 EVE 连线从接口 `id=0` 改成接口 `id=19`。
2. `network_id` 保持为 `8` 不变。
3. 这意味着实际仍然连在同一条管理桥上：
   - `GW-SW e1/3`
   - `RG-FW1 最后一个口`
4. 离线写入的真实候选配置是：
   - `vrf MGT`
   - `physical enp0s22`
   - `port pci-b0s22`
   - `172.32.2.22/24`
   - `0.0.0.0/0 -> 172.32.2.254`

这一轮实测结果必须分层写清楚：

1. 配置面成立：
   - `show config xml running vrf MGT interface physical enp0s22` 可看到
     `port pci-b0s22`
   - `172.32.2.22/24`
   - `https/ping/ssh true`
2. 设备内三层连通成立：
   - `cmd ping 172.32.2.254 count 2 vrf MGT` 成功
3. 从 Cisco 管理桥侧发起 `ICMP` 也成立：
   - 在 EVE 宿主机强制走 `vnet0_8` 探测时，`ping 172.32.2.22` 成功
4. 但管理服务没有起来：
   - 从 `vnet0_8` 对 `172.32.2.22:22` 和 `:443` 的探测都超时
   - `tcpdump` 只看到 `SYN` 发出，没有任何 `SYN-ACK` 或 `RST` 回包
5. 运行态仍有明显缺口：
   - `show state xml vrf MGT interface physical enp0s22` 返回 `No data`

因此，这轮实验的准确结论不是“最后一个口完全不可用”，也不是“最后一个口已经打通”，而应写成：

1. 最后一个口在当前镜像上可以被离线纳入 `MGT VRF` 配置树。
2. 它可以形成设备内部到 Cisco 网关的三层连通。
3. 它也可以对同一管理桥上的 `ICMP` 做出响应。
4. 但它当前还不能提供完整的管理服务入口，至少 `SSH/HTTPS` 没有形成可用回包。
5. 所以它目前只能归类为：
   - `L3/ICMP 已成立`
   - `管理服务未成立`
   - `不能替代 Ge0/0 作为当前稳定标准管理口`

## 5. 当前最重要的边界

这台设备当前最关键的边界有两条：

1. `20` 口扩展不等于 `20` 个统一防火墙业务口。
2. OneOPS 统一规则中的“最后一个口作为带外管理口”，在当前锐捷镜像上不成立。
3. 官方备份包中的真实配置载荷是加密文件，当前还不能直接按备份包方式离线改写。
4. `flash:/sysrepo/startup` 中的启动配置虽然是 `LYB` 二进制格式，但已经实证可以离线解码与重生成；当前未完成的是参数化模板、默认路由与管理 VRF 的标准化。
5. 对当前镜像来说，`Ge0/0` 很可能是只能留在 `main` 的特殊管理口，不能直接按普通物理口逻辑迁移到 `MGT VRF`。
6. 当前前台 `nc-cli` 只开放了“导出/查看/校验文件”的子集，没有开放“编辑/装回/提交”的完整文件回写链。
7. 设备原生导出的接口 XML 与当前离线原型之间，已经观察到默认子节点层面的真实结构差异。
8. 最后一个口 `enp0s22` 即使通过离线整库配置被纳入 `MGT VRF`，当前也只打通了 `L3/ICMP`，没有打通 `SSH/HTTPS` 管理服务。
9. 因此，当前阶段的标准管理口只保留 `Ge0/0`，最后一个口实验只作为边界证据保留，不纳入标准初始化模板。
10. 曾经做过“只补 `MGT VRF + default route`、不迁移 `Ge0/0`”的离线候选与真实节点写回尝试，但最新 live 备份解密显示当前 `startup.xml` 与 `running.xml` 仍只有 `main`；因此不能再把“现场已经存在 `MGT` 默认路由对象”当作当前事实。
11. 最新离线 roundtrip 进一步说明：`sysrepo` 本身其实接受过把 `Ge0/0` 放进 `MGT`，所以问题不能再简单归类为“`Ge0/0` 永远不能进入 `MGT`”。
12. 当前更像是运行阶段边界，而不是导入阶段边界：
    - 同版本正常启动走 `sysrepo-running`
    - 不会重新走 `sysrepo-startup`
13. `physinterface` 的 running 生成链会把物理接口骨架重新生成到 `main`
    - `config_file_path('running') -> /tmp/iface_running.xml`
    - `devcap_generate_iface_config(ds='running', ...)`
    - 根 `vrf` 硬编码为 `main`
14. 这一点已经被离线最小复现实验直接验证：
    - 伪造 `interfaces.xml` 后，`devcap_generate_iface_config(ds='startup')` 会为 `is_mgmt=1` 的 `Ge0/0` 生成 `vrf main + 172.32.2.11/24 + https/ping`
    - 同一份输入生成的 `running` 文件仍然是 `vrf main` 下的物理口骨架
15. live `debug-support` 白名单也提供了运行期旁证：
    - `cmd debug-support cmd exec lsof | match 6212` 可见主 YAMS 进程是 `6212 /usr/bin/python3.9`
    - 同一进程持有大量 `/dev/shm/srsub_ntos.running`
    - 这与“运行阶段持续围绕 `running` 数据面工作”的代码路径相互印证
16. 结合 `PhysicalLinkManager` 的“move to proper netns”实现，当前最需要防范的是：
    - startup 数据层已经放进 `MGT`
    - 但 running 阶段又把同一物理口按管理口/主 VRF 逻辑重新并回 `main`
17. 因此，这台设备当前最准确的边界描述应更新为：
    - `MGT` 路由对象作为离线候选可以被接受
    - `Ge0/0 -> MGT` 在离线数据层可以成立
    - 但最新现场导出的 `startup.xml/running.xml` 仍是 `vrf main + Ge0/0 + 172.32.2.11/24`
    - 现场稳定行为仍受运行期 `main` 回填/管理口绑定机制影响
    - 不再把“补路由”当作默认修复方向

更准确地说，这台设备目前更接近：

1. `默认首口管理`
2. `前 8 口是标准防火墙口`
3. `后续扩展口属于未完全适配状态`

## 6. 对 OneOPS 测试推进的意义

这轮结果虽然还没完成最终标准化，但已经非常有价值：

1. 证明锐捷防火墙镜像不是“完全不可用”。
2. 证明它存在可达的默认管理平面。
3. 证明后续可以围绕首口管理模型继续推进。
4. 同时也提前暴露了与统一 20 口规则的偏差，不会让后续测试设计建立在错误前提上。

## 4.12 业务口 `Ge0/1` 的 live `VRF` 实证

围绕“这台锐捷到底是否支持业务口 `VRF`”又做了一轮更贴近当前稳定现场的真实验证。这一轮刻意不再动 `Ge0/0`，而是：

1. 保留 `Ge0/0 -> network_id=8` 作为当前稳定管理入口。
2. 在同一台 `RG-FW1` 上新增 `id=1 -> network_id=8`，让真实业务口 `Ge0/1` 也接到 Cisco 管理桥。
3. 通过离线整库 `ntos` roundtrip，把 `Ge0/1` 从 `main` 迁入 `vrf MGT`，并写入：
   - `172.32.2.21/24`
   - `0.0.0.0/0 -> 172.32.2.254`
   - `https/ping/ssh true`

这一轮必须把“配置层”“运行层”“转发表层”“外侧探测层”分开看：

1. 配置层成立：
   - `sysrepocfg -I` 接受候选 XML。
   - 重导出的 `ntos` 中可看到：
     - `vrf MGT`
     - `physical Ge0/1`
     - `172.32.2.21/24`
     - `0.0.0.0/0 -> 172.32.2.254`
2. 运行层部分成立：
   - `show state xml vrf MGT` 不再是空，说明 `MGT` 运行态对象本身已经出现。
   - `show interface name Ge0/1 vrf MGT` 可见：
     - `Ge0/1`
     - `172.32.2.21/24`
     - `State UNKNOWN`
3. 但更细的接口运行态仍未真正落地：
   - `show state xml vrf MGT interface physical Ge0/1` 返回 `No data`
4. 转发表层未成立：
   - `show ipv4-routes vrf MGT` 为空
   - `cmd ping 172.32.2.254 count 2 vrf MGT` 返回 `Network is unreachable`
5. 外侧抓包又说明它不是“完全没活”：
   - 从外部对 `172.32.2.21` 发起 `SSH/HTTPS/ICMP` 时，`vnet0_8` 上能看到入方向探测报文
   - 同时还能看到设备侧发出的 `ARP who-has 172.32.2.254 tell 172.32.2.21`
   - Cisco 网关也回了 `ARP Reply`
6. 但最终仍没有形成真正的数据面/管理面回包：
   - `172.32.2.21` 对外部 `ICMP` 不回包
   - `172.32.2.21:22` 不建立
   - `172.32.2.21:443` 不建立

因此，这轮 `Ge0/1` live 实证应收敛为：

1. 这台镜像不是“完全不支持业务口 `VRF`”。
2. `Ge0/1 -> MGT` 可以进入：
   - 配置树
   - 部分运行视图
   - 邻居发现起步阶段
3. 但当前还没有进入：
   - 真实接口运行态
   - `VRF` 转发表
   - 完整 `ICMP/TCP` 管理可达
4. 所以当前最准确的判断应更新为：
   - `业务口 VRF 配置能力存在`
   - `业务口 VRF 运行/转发链路未完全成立`
   - `不能把它记成“VRF 已稳定可用”`
5. 这也说明当前边界不只属于 `Ge0/0` 特殊管理口，普通业务口 `Ge0/1` 在这版镜像上同样存在“配置已进、运行未实装”的缺口。

## 7. 下一步建议

后续如果继续推进这台锐捷，建议顺序如下：

1. 把当前“单次离线改 `LYB` 成功”的过程整理成参数化模板生成步骤。
2. 固化 `Ge0/0 + main + 172.32.2.11/24 + default route` 这条稳定管理模型。
3. 如果仍保留 `ethernet=20`，明确区分：
   - 前 8 个可管理防火墙口
   - 后 12 个扩展口的真实支持边界
4. 如果目标是尽快进入 OneOPS 主线流程测试，可先把它作为：
   - `首口管理`
   - `main` 管理平面
   - `8 口稳定`
   - `离线启动模板可改写`
   - `SSH 已实证`
   的锐捷防火墙模板草案。
5. 后续执行离线标准化时，统一按：
   [EVE-NG Ruijie 防火墙离线启动模板标准操作](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-ruijie-firewall-offline-startup-template-standard.md)
   来固化输入、替换、验证和证据留存。
