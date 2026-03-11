# 5 分钟快速开始指南

> 本指南将帮助你在 5 分钟内完成项目配置和首次运行

## 第一步：获取 Telegram API 密钥（2 分钟）

1. 打开浏览器访问：https://my.telegram.org/apps
2. 使用手机号登录 Telegram
3. 点击 **"API development tools"**
4. 填写应用信息（随意填写）：
   - Application title: `Customer Service Sync`
   - Short name: `cs_sync`
   - Platform: `Desktop`
   - Description: 留空即可
5. 点击 **Create application**
6. 记录以下信息：
   - **App api_id**: `12345678`（示例）
   - **App api_hash**: `abcdef1234567890abcdef`（示例）

## 第二步：配置项目（1 分钟）

打开终端，执行：

```bash
# 进入项目目录
cd /Users/apple/Data/workspace/company/tg-mtproto

# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件
nano .env  # 或使用你喜欢的编辑器
```

在 `.env` 文件中填入你的 API 信息：

```env
API_ID=12345678
API_HASH=abcdef1234567890abcdef
PHONE=+861234567890
SESSION_NAME=customer_service_sync

# 代理配置（中国大陆用户建议启用）
USE_PROXY=true
PROXY_HOST=127.0.0.1
PROXY_PORT=7890
```

保存并退出。

## 第三步：安装依赖（1 分钟）

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

## 第四步：运行测试（1 分钟）

```bash
# 运行基础功能测试（不需要 Telegram 连接）
python test_basic.py
```

你应该看到：
```
✓ 数据库创建成功
✓ 消息保存成功
✓ 查询成功
✓ 所有测试通过！
```

## 第五步：运行示例（1 分钟）

### 方式 A: 运行简单示例（推荐）

编辑 `quick_start.py`，填入你的 API 信息：

```python
API_ID = 12345678  # 你的 API ID
API_HASH = 'abcdef1234567890abcdef'  # 你的 API HASH
PHONE = '+861234567890'  # 你的手机号
```

运行：
```bash
python quick_start.py
```

### 方式 B: 运行完整程序

```bash
python main.py
```

**首次运行会要求输入验证码：**
1. 程序会显示：`Please enter the verification code:`
2. 查看 Telegram 收到的验证码
3. 输入验证码并回车

**成功登录后会显示：**
```
✓ 已登录：Your Name (@your_username)
  用户 ID: 123456789
```

## 完成！🎉

现在你已经成功运行了项目。接下来可以：

### 查看同步结果

```bash
# 查看数据库文件
ls -lh messages.db

# 查看统计信息
python query_messages.py
```

### 导出数据

```python
# 在 Python 中
from query_messages import MessageQuery

query = MessageQuery()

# 导出前 100 条消息
query.export_to_csv("messages.csv", {'limit': 100})
query.export_to_json("messages.json", {'limit': 100})
```

### 搜索消息

```python
# 搜索包含关键词的消息
results = query.search_messages(keyword="客服", limit=50)

for msg in results:
    print(f"{msg['sender_name']}: {msg['message_text']}")
```

## 常见问题

### Q: 验证码收不到怎么办？
A: 等待 1-2 分钟后重新运行，或尝试在 Telegram App 中查看是否有官方渠道发来的消息。

### Q: 如何切换账号？
A: 修改 `.env` 中的 `PHONE` 和 `SESSION_NAME`，然后删除旧的 `.session` 文件。

### Q: 同步速度慢？
A: 修改 `main.py` 中的 `limit_per_chat` 参数，减少每个聊天的消息数量。

### Q: 如何停止程序？
A: 按 `Ctrl+C` 即可安全停止。

## 下一步

- 📖 查看 [USAGE.md](USAGE.md) 了解详细功能
- 🔧 修改 `main.py` 添加自定义过滤逻辑
- 📊 使用 `query_messages.py` 分析数据
- 🚀 部署到服务器定期运行

## 需要帮助？

- 查看 [README.md](README.md) 了解项目概况
- 查看 [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) 了解完整架构
- 访问 [Telethon 官方文档](https://docs.telethon.dev/)

---

**祝你使用愉快！** 🎊
