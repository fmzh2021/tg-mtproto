# Telethon 客服人员聊天同步工具

基于 Telethon 的 Telegram 聊天信息同步工具，用于客服人员聊天信息的审计和监管。

## 功能特性

- ✅ 同步私聊和群聊历史消息
- ✅ 实时监听新消息
- ✅ 消息存储到 SQLite 数据库
- ✅ 支持消息搜索和过滤
- ✅ 导出消息到 CSV/JSON 格式
- ✅ 统计分析和报告

## 项目结构

```
tg-mtproto/
├── main.py              # 主程序 - 消息同步和监听
├── config.py            # 配置文件
├── message_storage.py   # 消息存储模块
├── query_messages.py    # 消息查询和导出工具
├── requirements.txt     # Python 依赖
├── .env.example         # 环境变量示例
└── README.md           # 说明文档
```

## 安装步骤

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 获取 Telegram API 密钥

1. 访问 https://my.telegram.org/apps
2. 登录你的 Telegram 账号
3. 创建一个新的应用
4. 获取 `API ID` 和 `API HASH`

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并填入你的配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
API_ID=your_api_id
API_HASH=your_api_hash
PHONE=your_phone_number
SESSION_NAME=customer_service_sync
```

## 使用方法

### 同步聊天消息

运行主程序同步所有聊天消息：

```bash
python main.py
```

程序会：
1. 连接到 Telegram
2. 同步所有对话的历史消息（默认每个对话 50 条）
3. 将消息存储到 `messages.db` 数据库
4. 可选择实时监听新消息

### 查询和导出消息

使用查询工具搜索和导出消息：

```bash
python query_messages.py
```

### 编程方式使用

```python
from query_messages import MessageQuery
from datetime import datetime, timedelta

query = MessageQuery()

# 搜索消息
results = query.search_messages(
    keyword="客服",
    start_date=datetime.now() - timedelta(days=7),
    limit=100
)

# 获取统计信息
stats = query.get_statistics()
print(f"总消息数：{stats['total_messages']}")

# 导出到 CSV
query.export_to_csv("messages.csv")

# 导出到 JSON
query.export_to_json("messages.json")
```

## 数据库结构

### messages 表
- `message_id`: Telegram 消息 ID
- `chat_id`: 聊天 ID
- `chat_name`: 聊天名称
- `chat_type`: 聊天类型（私聊/群组/频道）
- `sender_id`: 发送者 ID
- `sender_name`: 发送者名称
- `message_text`: 消息内容
- `message_date`: 消息时间

### users 表
- `user_id`: 用户 ID
- `username`: 用户名
- `first_name`: 名字
- `last_name`: 姓氏
- `is_bot`: 是否为机器人

### chats 表
- `chat_id`: 聊天 ID
- `chat_name`: 聊天名称
- `chat_type`: 聊天类型
- `participant_count`: 成员数量

## 高级配置

### 修改同步消息数量

在 `main.py` 中修改 `limit_per_chat` 参数：

```python
await sync_all_messages(limit_per_chat=100)  # 每个对话同步 100 条消息
```

### 过滤特定聊天

可以修改 `sync_all_messages` 函数添加过滤逻辑：

```python
for dialog in dialogs:
    # 只同步群组消息
    if not isinstance(dialog.entity, (Chat, Channel)):
        continue
    
    # 只同步特定关键词的聊天
    chat_name = get_chat_name(dialog.entity)
    if "客服" not in chat_name:
        continue
```

### 自定义消息处理

修改 `process_message` 函数添加自定义逻辑：

```python
async def process_message(message: Message):
    # 添加敏感词检测
    sensitive_words = ["密码", "银行卡", "身份证"]
    if any(word in message.text for word in sensitive_words):
        print(f"[警告] 检测到敏感词：{message.text}")
    
    # 保存到数据库
    db.save_message(message)
```

## 注意事项

1. **速率限制**: Telegram 有 API 调用限制，程序已添加延迟避免触发限制
2. **隐私合规**: 请确保使用符合当地法律法规和 Telegram 服务条款
3. **数据安全**: 数据库文件包含敏感信息，请妥善保管
4. **会话管理**: 首次运行需要手机验证码，之后会保存会话文件

## 常见问题

### Q: 如何停止程序？
A: 按 `Ctrl+C` 可以安全停止程序

### Q: 会话文件在哪里？
A: 会话文件保存在项目根目录，文件名由 `SESSION_NAME` 配置决定

### Q: 如何清空数据库？
A: 删除 `messages.db` 文件即可

### Q: 支持导出图片/视频吗？
A: 当前版本只支持文本消息，媒体文件需要额外开发

## 扩展开发

### 添加消息审计规则

```python
# 在 process_message 函数中添加
async def audit_message(message: Message):
    """消息审计"""
    # 敏感词检测
    sensitive_patterns = [...]
    
    # 频率检测
    # 检测短时间内大量消息
    
    # 关键词告警
    # 特定关键词触发通知
```

### 集成告警系统

```python
# 发送邮件告警
def send_alert(message_text, sender_name):
    import smtplib
    # 发送邮件到管理员
```

## 许可证

本项目仅供学习和研究使用。

## 技术支持

如有问题，请查看 Telethon 官方文档：https://docs.telethon.dev/
