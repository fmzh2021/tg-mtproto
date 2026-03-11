# 代理配置指南

## 为什么需要代理？

在中国大陆地区，Telegram 的服务被防火墙屏蔽，需要通过代理服务器才能连接。本项目支持配置 HTTP/SOCKS 代理。

## 代理配置方法

### 方法 1: 使用环境变量（推荐）

编辑 `.env` 文件：

```env
# 启用代理
USE_PROXY=true

# 代理服务器地址
PROXY_HOST=127.0.0.1

# 代理端口
PROXY_PORT=7890
```

### 方法 2: 在代码中直接配置

#### quick_start.py
```python
USE_PROXY = True  # 启用代理
PROXY_HOST = '127.0.0.1'
PROXY_PORT = 7890
```

#### main.py
自动从 `config.py` 读取代理配置。

## 常见代理软件配置

### ClashX / ClashX Pro

默认配置：
- 代理地址：`127.0.0.1`
- HTTP 端口：`7890`
- SOCKS5 端口：`7891`

在 `.env` 中配置：
```env
USE_PROXY=true
PROXY_HOST=127.0.0.1
PROXY_PORT=7890
```

### Shadowsocks

默认配置：
- 代理地址：`127.0.0.1`
- 端口：`1080`（默认）

在 `.env` 中配置：
```env
USE_PROXY=true
PROXY_HOST=127.0.0.1
PROXY_PORT=1080
```

### V2Ray / Trojan

默认配置：
- 代理地址：`127.0.0.1`
- HTTP 端口：`10809`（常见）
- SOCKS5 端口：`10808`（常见）

在 `.env` 中配置：
```env
USE_PROXY=true
PROXY_HOST=127.0.0.1
PROXY_PORT=10809
```

## 测试代理连接

### 方法 1: 使用 curl 测试

```bash
# 测试 HTTP 代理
curl -x http://127.0.0.1:7890 https://www.google.com

# 测试 SOCKS5 代理
curl -x socks5://127.0.0.1:7890 https://www.google.com
```

### 方法 2: 运行项目测试

```bash
source venv/bin/activate
python quick_start.py
```

如果代理配置正确，程序会显示：
```
使用代理：127.0.0.1:7890
已登录！
```

## 代理类型说明

### HTTP 代理
- 适用于 HTTP/HTTPS 协议
- Telethon 支持 HTTP 代理
- 配置格式：`(host, port)`

### SOCKS5 代理
- 更通用的代理协议
- 需要额外安装依赖：`pip install pysocks`
- 配置格式：`(socks.SOCKS5, host, port)`

### MTProxy
- Telegram 专用的代理协议
- 需要额外配置
- 不推荐用于本项目

## 常见问题

### Q1: 如何知道我的代理端口是多少？

查看代理软件的设置界面，通常会显示 HTTP 和 SOCKS 端口。

### Q2: 代理不工作怎么办？

1. 检查代理软件是否运行
2. 确认端口号是否正确
3. 测试代理是否可用：`curl -x http://127.0.0.1:7890 https://www.google.com`
4. 检查防火墙设置

### Q3: 如何禁用代理？

将 `USE_PROXY` 设置为 `false`：

```env
USE_PROXY=false
```

或在代码中：
```python
USE_PROXY = False
```

### Q4: 使用代理后连接超时？

1. 确认代理服务器正常工作
2. 检查代理地址和端口
3. 尝试更换代理节点
4. 增加超时时间

### Q5: 支持哪些代理格式？

Telethon 支持以下格式：

```python
# HTTP 代理
proxy = ('127.0.0.1', 7890)

# SOCKS5 代理（需要 pysocks）
import socks
proxy = (socks.SOCKS5, '127.0.0.1', 7890)

# 带认证的代理
proxy = ('http', '127.0.0.1', 7890, True, 'username', 'password')
```

## 高级配置

### 使用 SOCKS5 代理

1. 安装依赖：
```bash
pip install pysocks
```

2. 修改 `config.py`：
```python
import socks

PROXY_TYPE = socks.SOCKS5
PROXY_HOST = '127.0.0.1'
PROXY_PORT = 7890
```

3. 修改 `main.py`：
```python
from config import PROXY_TYPE, PROXY_HOST, PROXY_PORT

if USE_PROXY:
    client = TelegramClient(
        SESSION_NAME, 
        API_ID, 
        API_HASH,
        proxy=(PROXY_TYPE, PROXY_HOST, PROXY_PORT)
    )
```

### 使用代理认证

如果代理需要用户名和密码：

```python
# 在 config.py 中
PROXY_USERNAME = 'your_username'
PROXY_PASSWORD = 'your_password'

# 在 main.py 中
if USE_PROXY:
    proxy = (
        'http',
        PROXY_HOST,
        PROXY_PORT,
        True,
        PROXY_USERNAME,
        PROXY_PASSWORD
    )
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH, proxy=proxy)
```

## 推荐设置

对于大多数用户，建议使用以下配置：

```env
# 启用代理
USE_PROXY=true

# 代理地址（本地）
PROXY_HOST=127.0.0.1

# 代理端口（根据使用的软件调整）
# ClashX: 7890
# Shadowsocks: 1080
# V2Ray: 10809
PROXY_PORT=7890
```

## 安全提醒

⚠️ **注意**：
1. 不要将包含真实代理配置的 `.env` 文件提交到 Git
2. 使用 `.gitignore` 忽略 `.env` 文件
3. 定期更新代理软件以确保安全
4. 选择可信的代理服务提供商

## 相关资源

- [Telethon 代理文档](https://docs.telethon.dev/en/latest/misc/proxy.html)
- [ClashX 官网](https://github.com/yichengchen/clashX)
- [Shadowsocks 官网](https://shadowsocks.org/)

---

配置完成后，运行 `python quick_start.py` 测试连接！
