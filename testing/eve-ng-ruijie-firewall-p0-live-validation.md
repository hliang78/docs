# EVE-NG Ruijie 防火墙 P0 接口实测回执

## 1. 目的

这份文档记录 `2026-06-28` 在当前实验环境里，对 `Ruijiefirewall-V1.03` Web 管理面 `P0` 只读接口做的第一轮 live 验证结果。

它回答的不是“代码里看起来有没有接口”，而是：

1. 哪些接口已经真实可调用
2. 哪些接口在当前基线下返回空数据但链路正常
3. 哪些接口当前存在参数或后端实现问题
4. OneOPS 现在可以先接哪一批能力

## 2. 验证环境

1. EVE 宿主机：`192.168.100.20`
2. 设备镜像：`Ruijiefirewall-V1.03`
3. 设备管理地址：`172.32.2.11/24`
4. 管理模型：`Ge0/0 + main`
5. 验证入口：`https://172.32.2.11`

## 3. 登录链路实测

### 3.1 已确认事实

1. `GET /api/v1/public_key/` 返回 `200`，可取到 RSA 公钥。
2. `GET /api/v1/captcha/` 返回 `200`，且 `enable=1`，说明当前 `443` 口登录链路仍启用验证码。
3. 用 `RSA(username/password) + hashkey + captcha` 提交 `POST /api/v1/login/` 后，设备真实返回：
   - `code=20000`
   - `sessionid`
   - `csrftoken` 与 `sessionid` cookie
4. 当前从实验机到设备的 `20099` 端口未打通，因此现阶段不能把“免验证码 AES 登录分支”当作 OneOPS 默认入口。

### 3.2 当前边界

1. 登录自动化已经可行，但 `captcha` 目前仍是前置条件。
2. 这意味着 OneOPS 第一轮如果要直接走 Web API：
   - 要么补一个验证码识别/人工辅助环节
   - 要么先把登录态获取做成预热动作
3. 因为 `20099` 当前不可达，所以不能假设锐捷这条线已经具备“纯无验证码自动登录”能力。

## 4. `interface` 组 live 结果

### 4.1 已实测通过

1. `GET /api/v1/interface/get_all_interface/`
   - 返回 `code=20000`
   - 当前基线共 `9` 个条目
   - 已见到 `Ge0/0` 到 `Ge0/7`
   - 已见到 `br0`，且带 `type=bridge`
2. `GET /api/v1/interface/get_physical_interface/`
   - 返回 `code=20000`
   - `Ge0/0` 当前实测字段包括：
     - `ip=172.32.2.11/24`
     - `is_mgmt=true`
     - `connect_type=STATIC`
     - `allows=[HTTPS, PING, SSH]`
     - `link_state=true`
     - `slot=0`
     - `port=0`
   - 说明这条接口已经可以支撑 OneOPS 的接口资产基线采集
3. `GET /api/v1/interface/search_iface/?kw=Ge0/0`
   - 返回 `code=20000`
   - 可按关键字稳定定位管理口
4. `GET /api/v1/interface/port_panel/`
   - 返回 `code=20000`
   - 当前返回 `productName=NSE-FireWall`
   - 当前面板视图为 `2 x 4` 口阵列
5. `GET /api/v1/interface/get_bridge_fdb/?iface_name=br0&param=fdb`
   - 返回 `code=20000`
   - 当前返回 `details="br0-vr0:"`
   - 说明这条接口已经打通，只是当前基线下还没有更多桥转发表项

### 4.2 返回空数据但链路正常

1. `GET /api/v1/interface/get_sub_interface/`
   - 返回 `code=20000`
   - `list=[]`
   - `total=0`
2. 这说明当前基线设备没有子接口配置，但接口本身已可用。

### 4.3 当前存在问题的接口

1. `GET /api/v1/interface/get_deploy_mode/`
   - 不带参数时返回 `5004`
   - 带 `mode=working-mode` 时返回 `10000`
   - 返回体里出现 `list indices must be integers or slices, not str`
   - 说明当前接口存在后端实现或返回结构处理问题，不能直接作为稳定采集源

### 4.4 当前建议的替代口径

1. `get_deploy_mode` 当前不稳定，但 `get_physical_interface` 已稳定返回每个口的 `link_model` 与 `bridge`。
2. 当前基线下所有物理口都返回：
   - `link_model=ROUTE`
   - `bridge=""`
3. 因此当前 OneOPS 可以先按“全口路由模式、无桥绑定”的事实来解释这台设备。
4. 设备内部代码还显示，锐捷自己的开局逻辑会直接使用底层 `show-port-panel-info` 返回里的 `working-mode` 字段，而不是依赖 `get_deploy_mode`。
5. 这说明 `get_deploy_mode` 不是当前阶段唯一入口，也不应继续阻塞主线采集。

## 5. `network_router` 组 live 结果

### 5.1 已实测通过

1. `GET /api/v1/route/static/`
   - 返回 `code=20000`
   - 当前拿到 `1` 条静态路由
   - 实测默认路由为 `0.0.0.0/0 -> 172.32.2.254`
2. `GET /api/v1/route/table/`
   - 返回 `code=20000`
   - 当前拿到 `2` 条 IPv4 路由
   - 已见：
     - `0.0.0.0/0`，协议 `static`
     - `172.32.2.0/24`，协议 `connected`
3. `GET /api/v1/routePolicy/list/`
   - 返回 `code=20000`
   - 当前 `policy-total=0`
4. 这说明当前路由面只读采集已经具备最小可用性，且能区分：
   - 已配置静态路由
   - 已生效转发表
   - 当前无策略路由

## 6. 对 OneOPS 的直接意义

### 6.1 当前就可以纳入 P0 的能力

1. 登录链路可打通：
   - `public_key`
   - `captcha`
   - `login`
   - `session cookie`
2. 接口资产基线可采：
   - `get_all_interface`
   - `get_physical_interface`
   - `search_iface`
   - `port_panel`
   - `get_bridge_fdb`
3. 路由资产基线可采：
   - `route/static`
   - `route/table`
   - `routePolicy/list`

### 6.2 当前不能直接当作稳定输入的能力

1. `get_deploy_mode`
2. `20099` 免验证码登录链路

### 6.3 必须写进适配层的护栏

1. “返回空”不能等于“接口失败”。
2. “参数缺失报错”要与“后端自身异常”分开处理。
3. 锐捷防火墙当前 Web 采集应按“`Ge0/0 + main` 管理模型”解释，不要套用 `MGT VRF` 假设。
4. 登录态需要独立管理，不要把验证码前置链路和业务查询混在同一个采集动作里。
5. `get_bridge_fdb` 当前正确参数名是 `iface_name`，不要继续按 `name` 调用。

## 7. 下一步建议

1. 把当前已打通的登录与只读查询链路收敛成 OneOPS 侧最小探针。
2. 给 `get_deploy_mode` 单独建边界排查任务，但不要卡住主线采集接入。
3. 下一轮继续推进：
   - NAT
   - 安全策略
   - 地址对象
   - 系统日志与监控类接口
4. 当这些能力也完成 live 验证后，再把 Ruijie 从“候选适配”升级到“可交付适配”。
