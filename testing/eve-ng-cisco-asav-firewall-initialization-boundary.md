# EVE-NG Cisco ASAv 防火墙首轮初始化与边界记录

更新时间：2026-06-28  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份文档记录 Cisco ASAv 在当前 EVE 环境里，首轮为什么会卡住、后来又是怎样被真正打通的。

它的重点不是重复标准步骤，而是把那些会直接影响判断的初始化边界保留下来，避免团队后面把 ASAv 误当成“和普通路由器一样，起机就能直接配”的镜像。

当前已经形成了可复验的标准化初始化路径，标准步骤统一参照：

1. [EVE-NG Cisco ASAv 防火墙标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-cisco-asav-firewall-standard-operation.md)

## 2. 当前结论

截至 2026-06-28，`asav-9.22.1.1-PLR-Licensed` 在当前 EVE 环境中已经不是“只会起机的候选镜像”，而是已经打通了第一条真实可复验管理面闭环的 Cisco 防火墙模板。

但它必须带着下面这些清晰边界使用：

1. 首次启动会自动触发一次 `clone reboot`。
2. 仅靠默认控制台进入 `ciscoasa>`，拿不到可直接用的特权态初始化闭环。
3. 必须显式走一次 `GRUB -> with no configuration load` 的恢复启动路径。
4. EVE 删除节点后，节点 `tmp` 覆盖目录不一定自动清理，旧状态可能被复用。
5. 统一实验口令 `admin/admin@123` 不符合 ASA 当前密码策略，不能直接作为标准口令。
6. 用 Console 给本地用户重置密码后，首次 SSH 登录会再触发一次“必须改密”流程。
7. SSH 客户端需要兼容 `ssh-rsa` host key。

## 3. 本次最终落地结果

### 3.1 已打通的能力

本次已经真实打通：

1. EVE API 建节点、建网络、挂线、启动
2. `Mgmt0/0 + Gi0/0 .. Gi0/6` 接口模型确认
3. `GRUB -> with no configuration load` 恢复启动
4. 管理口 `172.32.2.18/24`
5. 管理默认路由 `172.32.2.254`
6. 本地管理员 `admin`
7. SSH 实际登录
8. 正常启动后的重启持久化复验

### 3.2 最终稳定状态

本轮最后一次复验时，设备已经处于下面这个稳定状态：

1. `Management0/0 = 172.32.2.18/24`
2. `route management 0.0.0.0 0.0.0.0 172.32.2.254 1`
3. `username admin ... privilege 15`
4. `aaa authentication ssh console LOCAL`
5. `ssh 0.0.0.0 0.0.0.0 management`
6. SSH 登录后可 `enable` 到 `priv 15`
7. 重启后再次 SSH 验证，上述状态仍然存在

### 3.3 最终复验证据

正常启动后的最终回读已经实测通过：

1. SSH 以 `admin` 成功登录
2. `enable` 成功进入 `ciscoasa#`
3. `show curpriv` 返回：
   - `Username : enable_15`
   - `Current privilege level : 15`
4. `show interface ip brief` 返回：
   - `Management0/0 172.32.2.18 up/up`
5. `show running-config route` 返回：
   - `route management 0.0.0.0 0.0.0.0 172.32.2.254 1`
6. `show running-config username` 返回：
   - `username admin password ***** pbkdf2 privilege 15`

## 4. 为什么一开始会卡住

### 4.1 控制台默认进入的是 `enable_1`

这轮排查已经确认：

1. 正常启动后，控制台会自动显示 `User enable_1 logged in to ciscoasa`
2. `show curpriv` 显示当前权限只有 `priv 1`
3. 这时不能把它误判成“已经可以直接做完整初始化”

### 4.2 默认口令不能靠猜

之前卡住的根因之一，是把脚本内置参数误当成这台现场设备当前真实可用的默认口令。

本轮已经确认：

1. EVE 自带 `config_asav.py` 里的常见登录参数，不能直接当成当前设备真实有效默认口令
2. 清空节点后单纯重建，也不会自动回到“空 `enable` 密码可用”的状态
3. 继续盲猜 `admin/cisco` 或空 `enable`，只会浪费时间

### 4.3 `tmp` 覆盖目录会污染“首次启动”判断

这次额外确认了一个关键现场坑：

1. API 删除节点和网络成功
2. 不代表 `/opt/unetlab/tmp/<tenant>/<lab>/<node_id>` 一定已经清理
3. 同一个 `node id` 重新创建设备时，旧覆盖盘状态可能继续被复用

本次就实际看到：

1. `node 9` 删除后，对应 `tmp` 目录仍然存在
2. 必须手工清理，才能真正回到干净现场

## 5. 当前已经收敛出的正确路径

这次最终打通的关键不是“再猜一次口令”，而是换成正确入口：

1. 先让节点正常首启一次，生成 overlay
2. 显式修改 overlay 里的 `/grub.conf`
3. 把第一启动项切到 `with no configuration load`
4. 用恢复模式拿到可控的 `enable` 初始化入口
5. 写入管理口、路由、本地用户、SSH
6. 保存配置
7. 再把 `/grub.conf` 切回正常启动
8. 重启并做 SSH/`enable`/接口状态复验

也就是说，当前 ASAv 的真实初始化入口不是“默认启动后直接配”，而是“恢复启动拿控制权，正常启动做持久化复验”。

## 6. 当前边界

### 6.1 统一实验口令 `admin/admin@123` 不成立

这条边界现在已经明确，不再是推测。

本次真实配置时，设备直接返回：

1. `username admin password admin@123 privilege 15`
   被拒绝
2. `enable password admin@123`
   被拒绝

报错根因一致：

1. `123` 被识别为连续 ASCII 序列
2. 当前 `password-policy` 可见命令里，没有直接放开这条限制的选项

因此 ASAv 当前不能纳入统一实验口令 `admin/admin@123`。

### 6.2 首次 SSH 登录会再触发一次改密

本次已经真实遇到：

```text
Your password was reset by the administrator.
Please change your password before proceeding.
```

这意味着：

1. 通过 Console 配置 `username admin password <临时口令>` 后
2. 首次 SSH 登录不是直接进入稳定态
3. 还要再完成一次用户自改密

因此当前更稳妥的标准化做法是：

1. Console 阶段先设置一个合规临时口令
2. 首次 SSH 登录时改成最终稳定口令
3. 再把 `enable password` 同步到同一个最终稳定口令

### 6.3 SSH 兼容参数是必需项

当前设备只实证提供了 `ssh-rsa` host key。

所以宿主机侧必须使用：

```text
ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAuthentication=no admin@172.32.2.18
```

如果客户端默认禁用了 `ssh-rsa`，会直接失败。

### 6.4 当前仍是未授权许可状态

控制台仍会显示：

1. `ASAv platform license state is Unlicensed`

这不影响当前第一阶段做管理面、配置采集、策略样本和基础自动化验证，但后续如果要压更深的吞吐、连接数或高级功能边界，仍要把许可状态单独纳入风险说明。

## 7. 对第一阶段测试推进的意义

这次排查把 ASAv 从“镜像能启动，但初始化没收敛”推进成了“已有标准化初始化路径，但有厂商侧密码和恢复启动边界”的状态。

这对后续第一阶段测试的意义很直接：

1. Cisco 防火墙路线已经有了真实可落地入口
2. OneOPS 后续可以把 ASAv 纳入配置采集、策略解析、策略查询、NAT/ACL 样本和自动化脚本测试池
3. 但测试框架必须显式接受它的特殊初始化前置，而不能继续套统一路由器模板

## 8. 建议

后续围绕 ASAv 推进 OneOPS 真实设备测试时，建议固定下面几条约束：

1. 先按标准手册完成初始化，不要跳过恢复启动步骤
2. 每次销毁重建前，都检查节点 `tmp` 覆盖目录是否已清空
3. 把“密码策略不接受 `admin@123`”写成共享边界，不要让不同人重复碰撞
4. 把首次 SSH 改密流程也纳入自动化初始化设计
5. 在进入策略/NAT/对象类测试前，先固定一套可长期复用的合规实验口令
