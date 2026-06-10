# Docker Grafana 外部访问无响应：调整 inotify 后触发 sysctl 重新加载导致 ip_forward 关闭

日期：2026-06-10

## 背景

前端本地启动 Vite 时出现：

```text
Error: ENOSPC: System limit for number of file watchers reached
```

当时系统参数为：

```bash
fs.inotify.max_user_watches = 16384
fs.inotify.max_user_instances = 128
```

为解决 Vite 文件监听数量不足，执行了：

```bash
sudo tee /etc/sysctl.d/99-inotify.conf >/dev/null <<'EOF'
fs.inotify.max_user_watches=524288
fs.inotify.max_user_instances=1024
EOF

sudo sysctl --system
```

随后容器中的 Grafana 出现异常：本机访问 `3000` 有响应，但外部访问 `http://10.0.110.251:3000` 无响应。

## 现象

外部来源 `10.175.1.201` 访问宿主机 `10.0.110.251:3000`，宿主机抓包只看到 SYN 进来，没有看到正常 SYN-ACK 回包：

```bash
sudo tcpdump -i any "port 3000 and host 10.175.1.201" -c 200 -n
```

典型输出：

```text
10.175.1.201.37930 > 10.0.110.251.3000: Flags [S]
10.175.1.201.37930 > 10.0.110.251.3000: Flags [S]
10.175.1.201.37930 > 10.0.110.251.3000: Flags [S]
```

本机访问正常：

```bash
curl -sS -o /dev/null -w 'local:%{http_code}\n' http://127.0.0.1:3000/
curl -sS -o /dev/null -w 'hostip:%{http_code}\n' http://10.0.110.251:3000/
```

均返回：

```text
200
```

## 关键结论

`fs.inotify.max_user_watches` 本身不会影响 Grafana 或 Docker 端口映射。

真正原因是执行 `sysctl --system` 时，系统重新加载了既有 sysctl 配置，其中包含：

```bash
net.ipv4.ip_forward=0
```

Docker 发布端口 `0.0.0.0:3000->3000/tcp` 对外部请求会走 DNAT/转发到容器地址，例如：

```text
10.0.110.251:3000 -> 172.20.0.4:3000
```

当 `net.ipv4.ip_forward=0` 时，外部流量进入宿主机后无法正常转发到容器网络，表现为外部 SYN 进来但连接无响应。

## 排查命令

### 1. 确认内核参数

```bash
sysctl \
  fs.inotify.max_user_watches \
  fs.inotify.max_user_instances \
  net.ipv4.ip_forward \
  net.ipv4.conf.all.rp_filter \
  net.ipv4.conf.default.rp_filter
```

异常时关键值：

```text
net.ipv4.ip_forward = 0
```

### 2. 确认宿主机端口监听

```bash
ss -lntp '( sport = :3000 )'
```

正常应看到：

```text
LISTEN *:3000
```

### 3. 确认 Docker 容器和端口映射

```bash
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}'
```

Grafana 正常映射示例：

```text
demo-core-grafana  grafana.netxops:latest  0.0.0.0:3000->3000/tcp  Up ... (healthy)
```

查看容器网络和端口：

```bash
docker inspect demo-core-grafana \
  --format '{{json .NetworkSettings.Networks}} {{json .HostConfig.PortBindings}}'
```

典型信息：

```text
IPAddress: 172.20.0.4
PortBindings: 3000/tcp -> HostPort 3000
```

### 4. 确认 Docker NAT 规则

```bash
sudo iptables -S FORWARD
sudo iptables -t nat -S | grep -E '3000|DOCKER|PREROUTING|POSTROUTING'
```

正常会看到类似：

```text
-A DOCKER ! -i br-... -p tcp -m tcp --dport 3000 -j DNAT --to-destination 172.20.0.4:3000
```

### 5. 查找是谁把 ip_forward 设为 0

```bash
grep -R -n 'ip_forward\|inotify\|max_user' /etc/sysctl.conf /etc/sysctl.d/*.conf
```

本次命中的配置：

```text
/etc/sysctl.conf:net.ipv4.ip_forward=0
/etc/sysctl.d/99-sysctl.conf:net.ipv4.ip_forward=0
/etc/sysctl.d/99-inotify.conf:fs.inotify.max_user_watches=524288
/etc/sysctl.d/99-inotify.conf:fs.inotify.max_user_instances=1024
```

## 修复步骤

### 1. 临时恢复 Docker 外部访问

```bash
sudo sysctl -w net.ipv4.ip_forward=1
```

验证：

```bash
sysctl net.ipv4.ip_forward
```

期望：

```text
net.ipv4.ip_forward = 1
```

### 2. 永久修复

将所有会覆盖该值的 sysctl 配置改为 `1`。本次涉及：

```bash
sudo cp -a /etc/sysctl.conf /etc/sysctl.conf.bak-$(date +%Y%m%d%H%M%S)
sudo cp -a /etc/sysctl.d/99-sysctl.conf /etc/sysctl.d/99-sysctl.conf.bak-$(date +%Y%m%d%H%M%S)

sudo sed -i 's/^net\.ipv4\.ip_forward=0$/net.ipv4.ip_forward=1/' /etc/sysctl.conf
sudo sed -i 's/^net\.ipv4\.ip_forward=0$/net.ipv4.ip_forward=1/' /etc/sysctl.d/99-sysctl.conf

sudo sysctl --system
```

再次确认：

```bash
sysctl net.ipv4.ip_forward fs.inotify.max_user_watches fs.inotify.max_user_instances
```

期望：

```text
net.ipv4.ip_forward = 1
fs.inotify.max_user_watches = 524288
fs.inotify.max_user_instances = 1024
```

### 3. 验证 Grafana

本机验证：

```bash
curl -sS -o /dev/null -w 'local:%{http_code}\n' http://127.0.0.1:3000/
curl -sS -o /dev/null -w 'hostip:%{http_code}\n' http://10.0.110.251:3000/
```

外部验证：

```bash
curl -v --connect-timeout 5 http://10.0.110.251:3000/
```

如果仍不通，重新抓包。正常情况下应看到外部 SYN 后有 SYN-ACK 回包。

```bash
sudo tcpdump -i any "port 3000 and host 10.175.1.201" -c 50 -n
```

## 避坑提示

- `ENOSPC: System limit for number of file watchers reached` 不是磁盘空间不足，是 inotify watcher 数量不足。
- 只写入 `/etc/sysctl.d/99-inotify.conf` 不会直接影响 Docker 网络。
- 风险点在 `sudo sysctl --system`：它会重新加载 `/usr/lib/sysctl.d`、`/run/sysctl.d`、`/etc/sysctl.d` 以及 `/etc/sysctl.conf` 中的所有配置。
- 如果系统里原本存在 `net.ipv4.ip_forward=0`，重新加载后会关闭 Docker 外部访问所需的 IPv4 转发。
- 对 Docker 宿主机，建议固定保留：

```bash
net.ipv4.ip_forward=1
```

## 快速诊断口诀

外部访问 Docker 端口无响应，但本机访问正常时：

1. 看端口：`ss -lntp '( sport = :3000 )'`
2. 看容器：`docker ps`
3. 看转发：`sysctl net.ipv4.ip_forward`
4. 看 NAT：`sudo iptables -t nat -S | grep 3000`
5. 看包：`sudo tcpdump -i any "port 3000 and host <client-ip>" -n`

如果抓包只有 SYN 没有 SYN-ACK，且 `ip_forward=0`，优先恢复 `net.ipv4.ip_forward=1`。
