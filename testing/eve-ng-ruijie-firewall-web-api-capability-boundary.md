# EVE-NG Ruijie 防火墙 Web API 能力与边界

## 1. 结论

截至 `2026-06-28`，当前 `Ruijiefirewall-V1.03` 已确认：

1. 设备本机存在可工作的 Web 管理后端。
2. 后端不是简单静态页，而是 `nginx + uWSGI + Django REST` 结构。
3. 本机存在大量 `/api/v1/...` 风格接口，可覆盖登录、接口、路由、策略、NAT、监控、诊断等模块。
4. 当前没有证据表明这些接口属于“公开承诺、长期稳定、厂商正式开放”的防火墙 OpenAPI。
5. 对 OneOPS 来说，更准确的定位应是：
   - `存在可研究和可适配的本机内部 Web API`
   - `不应直接定义成已确认的官方公开 API 能力`

因此，当前阶段建议把锐捷防火墙的接入策略固定为：

1. 主通道仍以 `SSH/CLI` 为准。
2. Web API 作为增强路径和专项适配对象推进。
3. 所有基于 Web API 的对接都必须带上“内部接口可能变动”的风险标识。

## 2. 核心证据

### 2.1 Web 反向代理结构

离线读取 `etc/nginx/conf.d/eweb.conf` 已确认：

1. `443` 为主 Web 入口。
2. `/` 指向前端静态资源目录 `/eweb/www/dist`。
3. `/api` 被转发到 `uwsgi`：

```nginx
location /api {
    include uwsgi_params;
    uwsgi_pass  unix:///tmp/.uwsgi.sock;
    uwsgi_param  UWSGI_CHDIR /eweb/www/;
    uwsgi_param  UWSGI_SCRIPT eweb.wsgi;
}
```

这说明当前锐捷 Web 管理面不是纯前端调用本地 CGI，而是完整的 Python Web 后端。

### 2.2 Django 工程结构

离线解包后的代码目录位于：

`/eweb/www`

已确认存在：

1. `eweb/www/eweb/settings.py`
2. `eweb/www/eweb/urls.py`
3. 大量独立 Django app：
   - `user`
   - `interface`
   - `network_router`
   - `policy`
   - `nat`
   - `device_monitoring`
   - `flow_monitor`
   - `fault_diagnosis`
   - `ssl_proxy`
   - `sslvpn`
   - `threat_intelligence`
   - `quickly_start`

### 2.3 认证与会话模型

离线读取 `user/urls.py` 与 `user/views/user.py` 后，已确认登录主入口为：

1. `/api/v1/captcha/`
2. `/api/v1/public_key/`
3. `/api/v1/login/`
4. `/api/v1/logout/`

`loginV2` 的已知特点：

1. 登录请求需要用户名、密码。
2. 支持验证码校验。
3. 支持公钥/RSA 或 AES 解密流程。
4. 成功后返回 `sessionid`。
5. session 还会绑定来源地址与服务器端口。

这意味着它更像“浏览器会话式后台接口”，不是天然面向第三方系统的无状态 token API。

## 3. 已确认的接口主干

离线读取 `eweb/www/eweb/urls.py`，已确认主路由前缀为 `/api/v1/`，并挂载了大量业务模块。

### 3.1 用户与基础控制

1. `/api/v1/login/`
2. `/api/v1/logout/`
3. `/api/v1/user/`
4. `/api/v1/role/`
5. `/api/v1/user_auth/`
6. `/api/v1/opslog/`

### 3.2 接口与网络

1. `/api/v1/interface/`
2. `/api/v1/network_router/`
3. `/api/v1/linkdetection/`
4. `/api/v1/isp/`
5. `/api/v1/vrrp/`

其中已经实证从前端 bundle 中能提取到这类实际调用：

1. `/v1/interface/get_all_interface/`
2. `/v1/interface/get_physical_interface/`
3. `/v1/interface/bridge/config/`
4. `/v1/interface/bridge/delete/`
5. `/v1/interface/switch_state/`

### 3.3 安全策略与对象

1. `/api/v1/policy/`
2. `/api/v1/nat/`
3. `/api/v1/service/`
4. `/api/v1/object/`
5. `/api/v1/security_rule/`
6. `/api/v1/content_template/`
7. `/api/v1/ips/`
8. `/api/v1/ssl/`
9. `/api/v1/cert/`

### 3.4 监控、日志与运行态

1. `/api/v1/device_monitoring/`
2. `/api/v1/flow_monitor/`
3. `/api/v1/log/`
4. `/api/v1/log/systemlog/`
5. `/api/v1/fault_diagnosis/`
6. `/api/v1/reputation_center/`

### 3.5 运维与系统维护

1. `/api/v1/system_maintenance/`
2. `/api/v1/setting/`
3. `/api/v1/feature_library/`
4. `/api/v1/quickly_start/`

## 4. 是否存在真正的 OpenAPI

当前应区分两层概念。

### 4.1 广义上“有 API”

是的，这台设备本机确实存在大量 Web API。

### 4.2 是否存在“正式公开 OpenAPI”

当前不能成立，原因如下：

1. 现场访问 `/swagger`、`/swagger-ui`、`/openapi.json`、`/v2/api-docs` 时，没有拿到可用接口文档，只拿到前端页或 `403` 跳转。
2. `eweb/www/eweb/urls.py` 中 `api/v1/apidocs` 路由是注释状态，没有对外启用：

```python
# re_path("^api/v1/apidocs/(?P<path>.*)$", serve, {'document_root': settings.APIDOC_ROOT}),
```

3. `settings.py` 虽然定义了 `APIDOC_ROOT`，但现场并未形成对外可访问的 API 文档入口。
4. 当前发现的绝大多数接口都绑定在浏览器登录态、验证码、公钥、session 校验这套管理后台模型上。

因此，当前更准确的判断是：

1. `存在本机内部 Web API`
2. `未确认存在对外正式开放的防火墙 OpenAPI`

## 5. 当前唯一显式命名为 openapi 的接口

在 `quickly_start` 模块里，确实存在少量显式命名为 `openapi` 的接口：

1. `/api/v1/quickly_start/openapi/clearBridgeIntfArea/`
2. `/api/v1/quickly_start/openapi/clearBridgeIntfLanWan/`
3. `/api/v1/quickly_start/openapi/timestampSetTime/`

但这三条接口目前只能说明：

1. 厂商内部代码中存在“openapi”命名习惯。
2. 个别场景存在面向外部流程调用的专项接口。
3. 还不足以推出“整台防火墙已经提供完整公开 API 平台”。

## 6. 对 OneOPS 的使用建议

### 6.1 当前推荐策略

1. 设备纳管、配置采集、策略分析仍以 `SSH/CLI` 为主。
2. Web API 先作为增强能力线推进：
   - 接口/路由/对象只读查询
   - 页面同构数据抓取
   - 诊断、运行态、监控类快速读接口
3. 对 Web API 的写操作必须谨慎，优先只读验证，再逐步扩大。

### 6.2 适合优先研究的接口组

1. `user`
   - 登录、session、权限模型
2. `interface`
   - 物理口、子接口、bridge、聚合口
3. `network_router`
   - 静态路由、策略路由、路由表
4. `policy`
   - 安全策略、命中计数、模拟、优化
5. `nat`
   - NAT 策略、地址池、转换关系
6. `device_monitoring` 与 `flow_monitor`
   - 运行态指标、接口流量、会话趋势
7. `fault_diagnosis`
   - 诊断任务、抓包、探测、任务结果

### 6.3 风险提示

1. 当前这套 API 更像“Web 后台内部接口”，不是“稳定对接合同”。
2. 升级版本后，路径、字段、认证流程都可能变化。
3. 很多写接口背后可能直接下发设备配置或触发后端任务，必须在实验环境中逐条验证幂等性与副作用。

## 7. 共享口径

针对当前 `Ruijiefirewall-V1.03`，团队内建议统一使用下面这句话：

`Ruijie 防火墙当前已确认存在可利用的本机 Web 内部 API，但暂不视为已确认的官方公开 OpenAPI；OneOPS 第一阶段仍以 SSH/CLI 为主，Web API 作为增强适配路径推进。`
