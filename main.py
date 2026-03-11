# -*- coding: utf-8 -*-
"""
Telethon 基础示例 - 同步客服人员聊天信息
用于信息审计和监管

功能：
1. 同步所有私聊和群聊的历史消息
2. 实时监听新消息
3. 将消息存储到 SQLite 数据库
4. 支持导出消息记录
"""
import asyncio
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import Message, Channel, Chat, User
from config import API_ID, API_HASH, PHONE, SESSION_NAME, USE_PROXY, PROXY_HOST, PROXY_PORT
from message_storage import MessageDatabase


# 创建 Telegram 客户端
if USE_PROXY:
    print(f"使用代理配置：{PROXY_HOST}:{PROXY_PORT}")
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH, proxy=(PROXY_HOST, PROXY_PORT))
else:
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# 创建数据库实例
db = MessageDatabase("messages.db")


async def process_message(message: Message):
    """处理单条消息 - 打印并存储"""
    if not message.text:
        return
    
    # 获取聊天信息
    chat = await message.get_chat()
    chat_type = get_chat_type(chat)
    chat_name = get_chat_name(chat)
    
    # 获取发送者信息
    sender = await message.get_sender()
    sender_name = get_sender_name(sender)
    sender_username = getattr(sender, 'username', None) if sender else None
    
    # 打印消息信息
    print(f"\n{'='*80}")
    print(f"时间：{message.date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"聊天：{chat_name} (类型：{chat_type})")
    print(f"发送者：{sender_name} (@{sender_username})")
    print(f"消息 ID: {message.id}")
    print(f"内容：{message.text[:200]}{'...' if len(message.text) > 200 else ''}")
    print(f"{'='*80}")
    
    # 保存到数据库
    db.save_message(message)
    
    # 保存发送者信息
    if sender and isinstance(sender, User):
        db.save_user(sender)
    
    # 保存聊天信息
    if chat:
        db.save_chat(chat)


def get_chat_type(chat) -> str:
    """获取聊天类型"""
    if isinstance(chat, User):
        return '私聊'
    elif isinstance(chat, Chat):
        return '群组'
    elif isinstance(chat, Channel):
        if getattr(chat, 'broadcast', False):
            return '频道'
        else:
            return '超级群组'
    return '未知'


def get_chat_name(chat) -> str:
    """获取聊天名称"""
    if not chat:
        return '未知'
    return getattr(chat, 'title', None) or getattr(chat, 'username', None) or '未知'


def get_sender_name(sender) -> str:
    """获取发送者名称"""
    if not sender:
        return '未知'
    if isinstance(sender, User):
        return sender.first_name or sender.last_name or sender.username or '未知'
    return getattr(sender, 'title', None) or '未知'


async def sync_all_messages(limit_per_chat: int = 100):
    """同步所有聊天的历史消息"""
    print("\n" + "="*80)
    print("开始同步历史消息...")
    print("="*80)
    
    # 获取所有对话
    dialogs = await client.get_dialogs()
    print(f"找到 {len(dialogs)} 个对话")
    
    synced_count = 0
    error_count = 0
    
    for i, dialog in enumerate(dialogs, 1):
        # 跳过已删除的账户
        if isinstance(dialog.entity, User) and getattr(dialog.entity, 'deleted', False):
            continue
        
        # 获取聊天信息
        chat_name = get_chat_name(dialog.entity)
        chat_type = get_chat_type(dialog.entity)
        
        print(f"\n[{i}/{len(dialogs)}] 正在处理：{chat_name} ({chat_type})")
        
        try:
            # 获取消息
            messages = await client.get_messages(dialog.entity, limit=limit_per_chat)
            
            for message in messages:
                if message.text:  # 只处理有文本内容的消息
                    await process_message(message)
                    synced_count += 1
            
            # 添加小延迟避免触发速率限制
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"处理 {chat_name} 时出错：{e}")
            error_count += 1
    
    print("\n" + "="*80)
    print(f"同步完成!")
    print(f"成功：{synced_count} 条消息")
    print(f"失败：{error_count} 个聊天")
    print("="*80)


@client.on(events.NewMessage())
async def handle_new_message(event):
    """实时监听新消息"""
    message = event.message
    print("\n[新消息] ", end="")
    await process_message(message)


async def main():
    """主函数"""
    print("="*80)
    print("Telethon 客服人员聊天同步工具")
    print("="*80)
    
    # 连接到 Telegram
    print("\n正在连接到 Telegram...")
    
    # 获取当前用户信息
    me = await client.get_me()
    print(f"✓ 已登录：{me.first_name} (@{me.username})")
    print(f"  用户 ID: {me.id}")
    
    # 同步历史消息
    print("\n请选择操作模式:")
    print("1. 仅同步历史消息")
    print("2. 仅实时监听新消息")
    print("3. 两者都执行")
    
    # 默认执行模式 1（同步历史消息）
    mode = 1
    
    if mode == 1 or mode == 3:
        await sync_all_messages(limit_per_chat=50)
    
    if mode == 2 or mode == 3:
        print("\n开始实时监听新消息... (按 Ctrl+C 停止)")
        print("="*80)
        await client.run_until_disconnected()


if __name__ == '__main__':
    try:
        # 启动客户端并运行主函数
        with client:
            client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n\n程序已中断")
    finally:
        db.close()
        print("数据库连接已关闭")
