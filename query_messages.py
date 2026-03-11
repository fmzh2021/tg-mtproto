# -*- coding: utf-8 -*-
"""
消息查询和导出工具
用于审计和监管目的
"""
import sqlite3
import csv
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict


class MessageQuery:
    """消息查询类"""
    
    def __init__(self, db_path: str = "messages.db"):
        self.db_path = db_path
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def search_messages(
        self,
        keyword: Optional[str] = None,
        sender: Optional[str] = None,
        chat_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        chat_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """搜索消息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM messages WHERE 1=1"
        params = []
        
        if keyword:
            query += " AND message_text LIKE ?"
            params.append(f"%{keyword}%")
        
        if sender:
            query += " AND (sender_name LIKE ? OR sender_username LIKE ?)"
            params.extend([f"%{sender}%", f"%{sender}%"])
        
        if chat_name:
            query += " AND chat_name LIKE ?"
            params.append(f"%{chat_name}%")
        
        if start_date:
            query += " AND message_date >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND message_date <= ?"
            params.append(end_date.isoformat())
        
        if chat_type:
            query += " AND chat_type = ?"
            params.append(chat_type)
        
        query += " ORDER BY message_date DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def get_user_messages(self, user_id: int, limit: int = 100) -> List[Dict]:
        """获取特定用户的所有消息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM messages 
            WHERE sender_id = ? 
            ORDER BY message_date DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def get_chat_messages(self, chat_id: int, limit: int = 100) -> List[Dict]:
        """获取特定聊天室的所有消息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM messages 
            WHERE chat_id = ? 
            ORDER BY message_date DESC 
            LIMIT ?
        ''', (chat_id, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # 总消息数
        cursor.execute("SELECT COUNT(*) FROM messages")
        stats['total_messages'] = cursor.fetchone()[0]
        
        # 按聊天类型统计
        cursor.execute('''
            SELECT chat_type, COUNT(*) as count 
            FROM messages 
            GROUP BY chat_type
        ''')
        stats['by_chat_type'] = {row['chat_type']: row['count'] for row in cursor.fetchall()}
        
        # 活跃用户统计
        cursor.execute('''
            SELECT sender_name, COUNT(*) as count 
            FROM messages 
            GROUP BY sender_id 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        stats['top_senders'] = [dict(row) for row in cursor.fetchall()]
        
        # 活跃聊天统计
        cursor.execute('''
            SELECT chat_name, COUNT(*) as count 
            FROM messages 
            GROUP BY chat_id 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        stats['top_chats'] = [dict(row) for row in cursor.fetchall()]
        
        # 最近 7 天消息趋势
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        cursor.execute('''
            SELECT DATE(message_date) as date, COUNT(*) as count 
            FROM messages 
            WHERE message_date >= ? 
            GROUP BY DATE(message_date) 
            ORDER BY date
        ''', (seven_days_ago,))
        stats['daily_trend'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return stats
    
    def export_to_csv(self, output_path: str, filters: Optional[Dict] = None):
        """导出消息到 CSV"""
        messages = self.search_messages(**filters) if filters else self.search_messages(limit=10000)
        
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=messages[0].keys() if messages else [])
            writer.writeheader()
            writer.writerows(messages)
        
        print(f"已导出 {len(messages)} 条消息到 {output_path}")
    
    def export_to_json(self, output_path: str, filters: Optional[Dict] = None):
        """导出消息到 JSON"""
        messages = self.search_messages(**filters) if filters else self.search_messages(limit=10000)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        
        print(f"已导出 {len(messages)} 条消息到 {output_path}")


def main():
    """主函数 - 演示查询功能"""
    query = MessageQuery()
    
    print("="*80)
    print("消息查询和导出工具")
    print("="*80)
    
    # 获取统计信息
    print("\n统计信息:")
    stats = query.get_statistics()
    print(f"总消息数：{stats['total_messages']}")
    print(f"\n按聊天类型:")
    for chat_type, count in stats['by_chat_type'].items():
        print(f"  {chat_type}: {count}")
    
    print(f"\n最活跃用户:")
    for sender in stats['top_senders'][:5]:
        print(f"  {sender['sender_name']}: {sender['count']} 条消息")
    
    print(f"\n最活跃聊天:")
    for chat in stats['top_chats'][:5]:
        print(f"  {chat['chat_name']}: {chat['count']} 条消息")
    
    # 示例搜索
    print("\n" + "="*80)
    print("搜索示例:")
    
    # 搜索包含特定关键词的消息
    results = query.search_messages(keyword="你好", limit=5)
    if results:
        print(f"\n包含'你好'的消息 ({len(results)} 条):")
        for msg in results[:3]:
            print(f"  [{msg['message_date']}] {msg['sender_name']}: {msg['message_text'][:50]}...")
    
    # 导出示例
    print("\n" + "="*80)
    print("导出示例:")
    query.export_to_csv("export_messages.csv", {'limit': 100})
    query.export_to_json("export_messages.json", {'limit': 100})


if __name__ == '__main__':
    main()
