# -*- coding: utf-8 -*-
"""
消息存储模块 - 将同步的消息保存到数据库
"""
import sqlite3
from datetime import datetime
from typing import Optional, List
from telethon.tl.types import Message, User, Chat, Channel


class MessageDatabase:
    """消息数据库管理类"""
    
    def __init__(self, db_path: str = "messages.db"):
        """初始化数据库连接"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
    
    def _create_tables(self):
        """创建数据库表"""
        cursor = self.conn.cursor()
        
        # 创建消息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                chat_name TEXT,
                chat_type TEXT,
                sender_id INTEGER,
                sender_name TEXT,
                sender_username TEXT,
                message_text TEXT,
                message_date TIMESTAMP,
                has_media INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(message_id, chat_id)
            )
        ''')
        
        # 创建聊天表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER UNIQUE NOT NULL,
                chat_name TEXT,
                chat_type TEXT,
                participant_count INTEGER,
                last_sync TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                is_bot INTEGER,
                last_seen TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def save_message(self, message: Message):
        """保存单条消息"""
        cursor = self.conn.cursor()
        
        # 获取聊天信息
        chat = message.chat
        chat_type = self._get_chat_type(chat)
        chat_name = self._get_chat_name(chat)
        
        # 获取发送者信息
        sender = message.sender
        sender_name = self._get_sender_name(sender)
        sender_username = getattr(sender, 'username', None) if sender else None
        sender_id = sender.id if sender else None
        
        # 插入消息
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO messages 
                (message_id, chat_id, chat_name, chat_type, sender_id, sender_name, 
                 sender_username, message_text, message_date, has_media)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message.id,
                chat.id if chat else None,
                chat_name,
                chat_type,
                sender_id,
                sender_name,
                sender_username,
                message.text,
                message.date,
                1 if message.media else 0
            ))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"保存消息失败：{e}")
    
    def save_user(self, user: User):
        """保存用户信息"""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, username, first_name, last_name, phone, is_bot, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user.id,
                user.username,
                user.first_name,
                user.last_name,
                user.phone,
                1 if user.bot else 0,
                datetime.now()
            ))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"保存用户失败：{e}")
    
    def save_chat(self, chat):
        """保存聊天信息"""
        cursor = self.conn.cursor()
        
        chat_type = self._get_chat_type(chat)
        chat_name = self._get_chat_name(chat)
        participant_count = getattr(chat, 'participants_count', None)
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO chats 
                (chat_id, chat_name, chat_type, participant_count, last_sync)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                chat.id,
                chat_name,
                chat_type,
                participant_count,
                datetime.now()
            ))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"保存聊天失败：{e}")
    
    def get_messages(self, chat_id: Optional[int] = None, limit: int = 100) -> List[dict]:
        """获取消息记录"""
        cursor = self.conn.cursor()
        
        if chat_id:
            cursor.execute('''
                SELECT * FROM messages 
                WHERE chat_id = ? 
                ORDER BY message_date DESC 
                LIMIT ?
            ''', (chat_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM messages 
                ORDER BY message_date DESC 
                LIMIT ?
            ''', (limit,))
        
        columns = ['id', 'message_id', 'chat_id', 'chat_name', 'chat_type', 
                   'sender_id', 'sender_name', 'sender_username', 'message_text', 
                   'message_date', 'has_media', 'created_at']
        
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def _get_chat_type(self, chat) -> str:
        """获取聊天类型"""
        if isinstance(chat, User):
            return 'private'
        elif isinstance(chat, Chat):
            return 'group'
        elif isinstance(chat, Channel):
            if chat.broadcast:
                return 'channel'
            else:
                return 'supergroup'
        return 'unknown'
    
    def _get_chat_name(self, chat) -> Optional[str]:
        """获取聊天名称"""
        if not chat:
            return None
        return getattr(chat, 'title', None) or getattr(chat, 'username', None)
    
    def _get_sender_name(self, sender) -> Optional[str]:
        """获取发送者名称"""
        if not sender:
            return None
        if isinstance(sender, User):
            return sender.first_name or sender.username or 'Unknown'
        return getattr(sender, 'title', None) or 'Unknown'
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
