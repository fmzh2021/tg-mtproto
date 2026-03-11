# 使用指南

## 快速开始（5 分钟上手）

### 步骤 1: 获取 Telegram API 密钥

1. 访问 https://my.telegram.org/apps
2. 使用手机号登录 Telegram
3. 点击 "API development tools"
4. 创建新应用（应用名称随意填写）
5. 记录 `App api_id` 和 `App api_hash`

### 步骤 2: 配置项目

1. 复制环境变量示例文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的 API 信息：
```env
API_ID=12345678
API_HASH=abcdef1234567890
PHONE=+861234567890
SESSION_NAME=customer_service_sync
```

### 步骤 3: 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Mac/Linux
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 步骤 4: 运行示例

#### 方式 1: 运行最简单的示例（推荐先测试）

编辑 `quick_start.py`，填入你的 API 信息：

```python
API_ID = 123456  # 你的 API ID
API_HASH = 'your_api_hash'  # 你的 API HASH
PHONE = '+1234567890'  # 你的手机号
```

运行：
```bash
python quick_start.py
```

首次运行会要求输入手机验证码，输入后即可完成登录。

#### 方式 2: 运行完整的同步程序

```bash
python main.py
```

程序会：
1. 自动读取 `.env` 配置文件
2. 连接到 Telegram
3. 同步所有聊天的历史消息
4. 保存到 `messages.db` 数据库

### 步骤 5: 查询和导出消息

```bash
# 查看统计信息和导出示例
python query_messages.py
```

## 功能详解

### 1. 同步历史消息

`main.py` 会自动同步所有对话的消息：

```python
# 同步每个对话的前 50 条消息
await sync_all_messages(limit_per_chat=50)

# 同步更多消息
await sync_all_messages(limit_per_chat=200)
```

### 2. 实时监听新消息

启用实时监听模式：

```python
@client.on(events.NewMessage())
async def handle_new_message(event):
    """新消息到达时自动调用"""
    message = event.message
    await process_message(message)
```

### 3. 搜索消息

```python
from query_messages import MessageQuery
from datetime import datetime, timedelta

query = MessageQuery()

# 搜索包含关键词的消息
results = query.search_messages(
    keyword="客服",
    limit=100
)

# 按时间范围搜索
results = query.search_messages(
    start_date=datetime.now() - timedelta(days=7),
    end_date=datetime.now(),
    limit=100
)

# 按发送者搜索
results = query.search_messages(
    sender="张三",
    limit=50
)

# 按聊天类型搜索
results = query.search_messages(
    chat_type="private",  # 私聊
    # chat_type="group",  # 群组
    limit=100
)
```

### 4. 导出消息

```python
# 导出到 CSV
query.export_to_csv("messages.csv", {
    'keyword': '客服',
    'limit': 1000
})

# 导出到 JSON
query.export_to_json("messages.json", {
    'start_date': datetime.now() - timedelta(days=30),
    'limit': 5000
})
```

### 5. 获取统计信息

```python
stats = query.get_statistics()

print(f"总消息数：{stats['total_messages']}")
print(f"按聊天类型：{stats['by_chat_type']}")
print(f"最活跃用户：{stats['top_senders']}")
print(f"最活跃聊天：{stats['top_chats']}")
print(f"每日趋势：{stats['daily_trend']}")
```

## 高级用法

### 过滤特定聊天

只同步包含特定关键词的聊天：

```python
async def sync_all_messages(limit_per_chat: int = 100):
    dialogs = await client.get_dialogs()
    
    for dialog in dialogs:
        chat_name = get_chat_name(dialog.entity)
        
        # 只同步包含"客服"的聊天
        if "客服" not in chat_name:
            continue
        
        # 处理消息...
```

### 敏感词检测

```python
async def process_message(message: Message):
    # 敏感词列表
    sensitive_words = ["密码", "银行卡", "身份证", "转账"]
    
    if message.text:
        for word in sensitive_words:
            if word in message.text:
                print(f"[警告] 检测到敏感词：{word}")
                print(f"消息内容：{message.text}")
                # 可以发送邮件或推送通知
    
    # 保存到数据库
    db.save_message(message)
```

### 只同步特定用户

```python
# 指定要同步的用户 ID 列表
TARGET_USER_IDS = [123456, 789012]

async def sync_all_messages(limit_per_chat: int = 100):
    dialogs = await client.get_dialogs()
    
    for dialog in dialogs:
        # 只同步指定用户
        if hasattr(dialog.entity, 'id'):
            if dialog.entity.id not in TARGET_USER_IDS:
                continue
        
        # 处理消息...
```

### 导出媒体文件

```python
from telethon import TelegramClient

async def download_media(message, output_dir='media'):
    """下载消息中的媒体文件"""
    if message.media:
        await client.download_media(
            message,
            file=f"{output_dir}/{message.id}"
        )
```

## 数据库结构

### messages 表 - 消息记录

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 自增主键 |
| message_id | INTEGER | Telegram 消息 ID |
| chat_id | INTEGER | 聊天 ID |
| chat_name | TEXT | 聊天名称 |
| chat_type | TEXT | 聊天类型（私聊/群组/频道） |
| sender_id | INTEGER | 发送者 ID |
| sender_name | TEXT | 发送者名称 |
| sender_username | TEXT | 发送者用户名 |
| message_text | TEXT | 消息内容 |
| message_date | TIMESTAMP | 消息时间 |
| has_media | INTEGER | 是否包含媒体 |
| created_at | TIMESTAMP | 创建时间 |

### users 表 - 用户信息

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 自增主键 |
| user_id | INTEGER | Telegram 用户 ID |
| username | TEXT | 用户名 |
| first_name | TEXT | 名字 |
| last_name | TEXT | 姓氏 |
| phone | TEXT | 手机号 |
| is_bot | INTEGER | 是否为机器人 |
| last_seen | TIMESTAMP | 最后活跃时间 |

### chats 表 - 聊天信息

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 自增主键 |
| chat_id | INTEGER | Telegram 聊天 ID |
| chat_name | TEXT | 聊天名称 |
| chat_type | TEXT | 聊天类型 |
| participant_count | INTEGER | 成员数量 |
| last_sync | TIMESTAMP | 最后同步时间 |

## 常见问题

### Q1: 首次运行提示输入验证码？
A: 这是正常的，Telegram 需要验证身份。输入你手机号收到的验证码即可。

### Q2: 如何切换账号？
A: 修改 `.env` 中的 `PHONE` 和 `SESSION_NAME`，然后删除旧的会话文件。

### Q3: 同步速度慢？
A: 可以减少 `limit_per_chat` 的值，或者添加过滤条件只同步特定聊天。

### Q4: 消息不完整？
A: Telegram API 有速率限制，程序已添加延迟。如需更多消息，可以多次运行程序。

### Q5: 如何清空数据？
A: 删除 `messages.db` 文件即可重新开始。

### Q6: 支持导出图片/视频吗？
A: 当前版本只保存文本消息。可以使用 `client.download_media()` 方法下载媒体文件。

## 最佳实践

1. **定期同步**: 设置定时任务（如 cron）定期运行同步程序
2. **数据备份**: 定期备份 `messages.db` 数据库文件
3. **隐私保护**: 确保数据库文件权限设置正确，防止未授权访问
4. **速率限制**: 不要频繁调用 API，避免被 Telegram 限制
5. **错误处理**: 添加日志记录和错误处理，便于问题排查

## 示例项目结构

```
tg-mtproto/
├── main.py              # 主程序 - 消息同步和监听
├── config.py            # 配置文件
├── message_storage.py   # 消息存储模块
├── query_messages.py    # 消息查询和导出工具
├── quick_start.py       # 快速启动示例
├── test_basic.py        # 基础功能测试
├── requirements.txt     # Python 依赖
├── .env                 # 环境变量配置（需要自己创建）
├── .env.example         # 环境变量示例
├── messages.db          # SQLite 数据库（运行后自动生成）
├── venv/                # Python 虚拟环境
└── README.md           # 项目说明
```

## 下一步

- 添加 Web 界面查看消息
- 集成邮件/短信告警功能
- 添加数据分析和可视化
- 支持多账号同时同步
- 添加消息分类和标签功能
