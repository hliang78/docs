# 第一阶段设备登录凭据基线

更新时间：2026-06-28  
适用范围：OneOPS 第一阶段真实设备测试

## 1. 目的

这份文档用于收敛第一阶段主线设备的登录凭据基线。

当前共享口径固定为：

1. 不再要求所有设备共用同一套账号或口令
2. 每类设备都必须有“标准登录入口 + 标准账号口令 + 首登行为说明 + 兼容性边界”
3. 测试判断依据是“是否已文档化、可复现、可回执”，不是“是否完全统一”

上层依据：

1. [Testing Objective Basis](/Users/huangliang/project/OneOPS-ALL/docs/superpowers/testing/platform-testing-baseline/testing-objective-basis.md)
2. [EVE-NG 设备初始化模板标准](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-device-initialization-template-standard.md)
3. [A1 单设备接入基线回执（第一版）](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-a1-single-device-baseline-receipt-v1.md)

## 2. 判定规则

某设备的登录基线要被视为“已成立”，至少要满足：

1. 已明确首选登录入口
2. 已明确标准账号和口令
3. 如果存在首登改密、临时口令、密码策略、SSH 算法兼容参数，必须显式记录
4. 至少有一条真实登录证据

如果当前在线节点与标准模板不一致，应区分两种情况：

1. 已记录例外
   可以继续推进测试
2. 未记录漂移
   需要先记为风险点，再决定是回拉旧模板，还是收敛成新模板

## 3. 主线设备凭据矩阵

| 设备 | 首选登录入口 | 标准账号 | 标准口令 | 首登行为 | 关键边界 |
| --- | --- | --- | --- | --- | --- |
| Cisco Gateway Switch | `SSH` | `admin` | `admin@123` | 无额外改密 | 客户端需兼容老 IOS SSH 算法 |
| Huawei AR | `SSH` | `admin` | `admin@123` | 首次 Console 创建账号后，必须重新登录一次 | 需补 `ssh server permit interface` |
| H3C VSR | `SSH` | `admin` | `admin@123` | 需先放宽密码策略并完成 SSH 初始化 | 客户端需兼容 `ssh-rsa` |
| Huawei USG | `SSH` | `admin` | `admin@123` | 默认内置 `admin/Admin@123`，首次 Console 强制改密到 `admin@123` | `HTTPS 443` 仍未形成稳定外部访问 |
| H3C VFW | `SSH` | `admin` | `Admin@1234` | `admin@123` 只作为首登触发口令，稳定口令需收敛到 `Admin@1234` | 管理面需显式放通 `Management <-> Local` |
| Ruijie Firewall | `SSH` | `admin` | `admin@123` | 当前标准模板基于离线启动文件；真实运行节点允许存在设备级例外 | 当前在线节点已漂移到 `qwerASDF!@34` |
| Cisco ASAv | `SSH` | `admin` | `Adm1n@134` | 先用临时口令 `Adm1n@132`，首次 SSH 强制改密到 `Adm1n@134` | `enable` 口令需同步；客户端需兼容 `ssh-rsa` |
| Ubuntu Server | `SSH` | `admin` | `admin@123` | 无额外改密 | `root/admin@123` 作为回退入口 |
| Debian Server | `SSH` | `admin` | `admin@123` | 无额外改密 | `root/admin@123` 作为回退入口 |
| Kylin Server | `SSH` | `admin` | `admin@123` | 无额外改密 | `root/admin@123` 作为回退入口；串口控制台不稳定 |

## 4. 设备级说明

### 4.1 Cisco Gateway Switch

1. 标准凭据：`admin/admin@123`
2. 真实 SSH 登录已完成实证
3. 若客户端直接失败，优先排查是否缺少老算法兼容参数

参考文档：

1. [EVE-NG Cisco 网关交换机标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-cisco-gateway-standard-operation.md)

### 4.2 Huawei AR

1. 首次不是默认内置账号模型，而是 Console 首登创建 `admin/admin@123`
2. 创建完成后串口会主动退出，必须第二次登录
3. `SSH` 真实可用前，还必须补 `ssh server permit interface`

参考文档：

1. [EVE-NG Huawei AR 路由器标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-ar-router-standard-operation.md)

### 4.3 H3C VSR

1. 当前可以收敛到 `admin/admin@123`
2. 但这不是镜像默认天然接受的口令，而是依赖密码策略放宽
3. `SSH` 真实登录已实证，但客户端需兼容 `ssh-rsa`

参考文档：

1. [EVE-NG H3C VSR 路由器标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-h3c-vsr-router-standard-operation.md)

### 4.4 Huawei USG

1. 默认账号是 `admin/Admin@123`
2. 首次 Console 登录后必须强制改密
3. 当前标准测试口令收敛为 `admin/admin@123`
4. `SSH` 已稳定可复用，`HTTPS 443` 仍不应视为已稳定支持

参考文档：

1. [EVE-NG Huawei USG 防火墙标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-usg-firewall-standard-operation.md)

### 4.5 H3C VFW

1. `admin@123` 只能作为首登触发口令
2. 当前稳定可复用的标准 SSH 口令例外值是 `Admin@1234`
3. 如果后续又把密码回设为 `admin@123`，下一次 SSH 仍会再次进入强制改密

参考文档：

1. [EVE-NG H3C VFW 防火墙标准操作手册（草案）](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-h3c-vfw-firewall-standard-operation.md)

### 4.6 Ruijie Firewall

1. 当前标准模板仍按 `admin/admin@123` 记录
2. 这条标准来自离线启动模板闭环，而不是统一口令假设
3. `2026-06-28` 当前在线节点的真实可用口令已实测为 `admin/qwerASDF!@34`
4. 因此它当前应视为“模板漂移样本”，不是“设备不可登录”
5. 后续要二选一：
   - 把在线节点拉回 `admin/admin@123`
   - 或把 `qwerASDF!@34` 收敛成新的设备标准凭据

参考文档：

1. [EVE-NG Ruijie 防火墙离线启动模板标准操作](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-ruijie-firewall-offline-startup-template-standard.md)
2. [A1 单设备接入基线回执（第一版）](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-a1-single-device-baseline-receipt-v1.md)

### 4.7 Cisco ASAv

1. `admin@123` 不符合当前镜像密码策略
2. 当前标准路径应先使用临时口令 `Adm1n@132`
3. 首次 SSH 登录后，再改成最终稳定口令 `Adm1n@134`
4. `enable password` 也应同步到同一个最终稳定口令

参考文档：

1. [EVE-NG Cisco ASAv 防火墙标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-cisco-asav-firewall-standard-operation.md)

### 4.8 服务器设备

Ubuntu、Debian、Kylin 当前都可按同一组服务器基线推进：

1. 标准账号：`admin/admin@123`
2. 回退账号：`root/admin@123`
3. 主验证入口：`SSH`
4. 其中 Kylin 当前只把 SSH 视为稳定入口，串口控制台仍属边界

参考文档：

1. [EVE-NG Linux Server 标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-server-standard-operation.md)
2. [EVE-NG Debian Server 标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-debian-server-standard-operation.md)
3. [EVE-NG Kylin Server 标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-kylin-server-standard-operation.md)

## 5. 当前执行建议

后续执行 `A1/B1/C1/C2` 时，登录相关动作统一按下面顺序处理：

1. 先查本表，确定设备标准登录入口
2. 再查对应设备手册，确认是否存在首登改密或 SSH 兼容参数
3. 如果现场凭据与本表不一致，先判断是不是已记录例外
4. 只有未记录漂移才中断主线并单独落风险回执
