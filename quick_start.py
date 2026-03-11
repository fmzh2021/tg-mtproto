# -*- coding: utf-8 -*-
"""
快速启动示例 - 最简单的聊天同步示例
支持代理配置
"""
from telethon import TelegramClient
import asyncio

# API 配置（请替换为你自己的）
API_ID = 39031401  # 替换为你的 API ID
API_HASH = '0a8c8d190ea6eae4b19b3a754ad3e3ff'  # 替换为你的 API HASH
PHONE = '+85295523742'  # 替换为你的手机号

# 会话名称（可选）
SESSION_NAME = 'customer_service_sync'

# 代理配置
USE_PROXY = True  # 设置为 True 启用代理
PROXY_HOST = '127.0.0.1'
PROXY_PORT = 7890

# 创建客户端
client = TelegramClient('quick_start', API_ID, API_HASH,proxy=("socks5",PROXY_HOST, PROXY_PORT))


async def main():
    """主函数"""
    # 启动客户端（带代理）
    if USE_PROXY:
        print(f"使用代理：{PROXY_HOST}:{PROXY_PORT}")
        await client.start(phone=PHONE)
    else:
        await client.start(phone=PHONE)
    
    print("已登录！")
    print(f"用户：{await client.get_me()}")
    
    # 获取所有对话
    dialogs = await client.get_dialogs()
    print(f"\n找到 {len(dialogs)} 个对话\n")
    
    # 显示前 10 个对话
    for i, dialog in enumerate(dialogs[:10], 1):
        print(f"{i}. {dialog.name} - {dialog.unread_count} 条未读消息")
    
    # 获取第一个对话的消息
    if dialogs:
        first_dialog = dialogs[0]
        print(f"\n从 {first_dialog.name} 获取最近 5 条消息:")
        
        messages = await client.get_messages(first_dialog.entity, limit=5)
        for msg in messages:
            if msg.text:
                print(f"  - {msg.text[:50]}")
    
    # 断开连接
    await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
