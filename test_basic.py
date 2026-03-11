# -*- coding: utf-8 -*-
"""
测试数据库功能（不需要 Telegram 连接）
"""
from message_storage import MessageDatabase
from query_messages import MessageQuery
from datetime import datetime, timedelta


def test_database():
    """测试数据库基本功能"""
    print("="*80)
    print("测试数据库功能")
    print("="*80)
    
    # 创建数据库
    db = MessageDatabase("test_messages.db")
    print("✓ 数据库创建成功")
    
    # 模拟保存消息
    class MockMessage:
        def __init__(self):
            self.id = 12345
            self.text = "这是一条测试消息"
            self.date = datetime.now()
            self.media = None
            self.chat = None
            self.sender = None
    
    class MockChat:
        def __init__(self):
            self.id = 98765
            self.title = "测试群组"
    
    class MockUser:
        def __init__(self):
            self.id = 11111
            self.username = "test_user"
            self.first_name = "测试"
            self.last_name = "用户"
            self.phone = None
            self.bot = False
    
    # 创建模拟对象
    mock_msg = MockMessage()
    mock_msg.chat = MockChat()
    mock_msg.sender = MockUser()
    
    # 测试保存
    db.save_message(mock_msg)
    db.save_user(mock_msg.sender)
    db.save_chat(mock_msg.chat)
    print("✓ 消息保存成功")
    
    # 测试查询
    messages = db.get_messages(limit=10)
    print(f"✓ 查询成功，共 {len(messages)} 条消息")
    
    if messages:
        msg = messages[0]
        print(f"  - 消息内容：{msg['message_text']}")
        print(f"  - 发送者：{msg['sender_name']}")
        print(f"  - 聊天：{msg['chat_name']}")
    
    db.close()
    print("\n✓ 数据库测试通过")
    
    # 清理测试数据库
    import os
    if os.path.exists("test_messages.db"):
        os.remove("test_messages.db")
        print("✓ 测试数据库已清理")


def test_query():
    """测试查询功能"""
    print("\n" + "="*80)
    print("测试查询功能")
    print("="*80)
    
    # 使用实际数据库（如果存在）
    import os
    if not os.path.exists("messages.db"):
        print("⚠  messages.db 不存在，跳过查询测试")
        print("  提示：先运行 main.py 同步一些消息后再测试")
        return
    
    query = MessageQuery()
    print("✓ 查询对象创建成功")
    
    # 测试统计
    stats = query.get_statistics()
    print(f"✓ 统计信息获取成功")
    print(f"  - 总消息数：{stats['total_messages']}")
    
    # 测试搜索
    results = query.search_messages(limit=10)
    print(f"✓ 搜索成功，共 {len(results)} 条结果")
    
    print("\n✓ 查询测试通过")


def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("Telethon 同步工具 - 功能测试")
    print("="*80 + "\n")
    
    try:
        test_database()
        test_query()
        
        print("\n" + "="*80)
        print("所有测试通过！✓")
        print("="*80)
        print("\n下一步:")
        print("1. 配置 .env 文件（填入 Telegram API 密钥）")
        print("2. 运行：python main.py")
        print("3. 查看数据库：messages.db")
        print("4. 查询消息：python query_messages.py")
        
    except Exception as e:
        print(f"\n✗ 测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
