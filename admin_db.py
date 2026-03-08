# -*- coding: utf-8 -*-
"""
管理后台数据库
层级：渠道 → 账号 → 监控群组
"""
import sqlite3
from datetime import datetime
from typing import List, Optional

ADMIN_DB_PATH = "admin.db"


class AdminDatabase:
    def __init__(self, db_path: str = ADMIN_DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()
        self._migrate()

    def _create_tables(self):
        cursor = self.conn.cursor()

        # 渠道（顶层）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                webhook_url TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 账号（归属于渠道）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                api_id TEXT NOT NULL,
                api_hash TEXT NOT NULL,
                session_name TEXT NOT NULL,
                status TEXT DEFAULT 'inactive',
                proxy_host TEXT,
                proxy_port INTEGER,
                use_proxy INTEGER DEFAULT 0,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE
            )
        ''')

        # 监控群组（归属于账号）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitored_chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                chat_id INTEGER,
                chat_name TEXT NOT NULL,
                chat_type TEXT DEFAULT 'unknown',
                enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
                UNIQUE(account_id, chat_name)
            )
        ''')

        # 消息记录
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                chat_name TEXT,
                chat_type TEXT,
                sender_id INTEGER,
                sender_name TEXT,
                sender_username TEXT,
                text TEXT,
                date TIMESTAMP,
                direction TEXT DEFAULT 'in',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
            )
        ''')

        self.conn.commit()

    def _migrate(self):
        cursor = self.conn.cursor()

        # 兼容旧版 accounts 表（无 channel_id 列）
        cursor.execute("PRAGMA table_info(accounts)")
        acc_cols = [row[1] for row in cursor.fetchall()]
        if 'channel_id' not in acc_cols:
            cursor.execute(
                "INSERT OR IGNORE INTO channels (name, description) VALUES ('默认渠道', '迁移自旧版本')"
            )
            self.conn.commit()
            default_id = cursor.lastrowid or 1
            cursor.execute(
                f"ALTER TABLE accounts ADD COLUMN channel_id INTEGER DEFAULT {default_id}"
            )
            self.conn.commit()

        # 兼容旧版 channels 表（无 webhook_url 列）
        cursor.execute("PRAGMA table_info(channels)")
        ch_cols = [row[1] for row in cursor.fetchall()]
        if 'webhook_url' not in ch_cols:
            cursor.execute("ALTER TABLE channels ADD COLUMN webhook_url TEXT")
            self.conn.commit()

    # ── Channels ───────────────────────────────────────────────────────────────

    def get_channels(self) -> List[dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT c.*,
                   COUNT(DISTINCT a.id) AS account_count
            FROM channels c
            LEFT JOIN accounts a ON a.channel_id = c.id
            GROUP BY c.id
            ORDER BY c.created_at DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]

    def get_channel(self, channel_id: int) -> Optional[dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM channels WHERE id=?', (channel_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def add_channel(self, name: str, description: str = None, webhook_url: str = None) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO channels (name, description, webhook_url) VALUES (?, ?, ?)',
            (name.strip(), description or None, webhook_url or None)
        )
        self.conn.commit()
        return cursor.lastrowid

    def update_channel(self, channel_id: int, name: str, description: str = None, webhook_url: str = None):
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE channels SET name=?, description=?, webhook_url=? WHERE id=?',
            (name.strip(), description or None, webhook_url or None, channel_id)
        )
        self.conn.commit()

    def delete_channel(self, channel_id: int):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM channels WHERE id=?', (channel_id,))
        self.conn.commit()

    # ── Accounts ───────────────────────────────────────────────────────────────

    def get_accounts(self, channel_id: int = None) -> List[dict]:
        cursor = self.conn.cursor()
        if channel_id:
            cursor.execute('''
                SELECT a.*, c.name AS channel_name,
                       COUNT(mc.id) AS chat_count
                FROM accounts a
                JOIN channels c ON a.channel_id = c.id
                LEFT JOIN monitored_chats mc ON mc.account_id = a.id
                WHERE a.channel_id = ?
                GROUP BY a.id
                ORDER BY a.created_at DESC
            ''', (channel_id,))
        else:
            cursor.execute('''
                SELECT a.*, c.name AS channel_name,
                       COUNT(mc.id) AS chat_count
                FROM accounts a
                JOIN channels c ON a.channel_id = c.id
                LEFT JOIN monitored_chats mc ON mc.account_id = a.id
                GROUP BY a.id
                ORDER BY a.created_at DESC
            ''')
        return [dict(row) for row in cursor.fetchall()]

    def get_account(self, account_id: int) -> Optional[dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT a.*, c.name AS channel_name, c.webhook_url AS channel_webhook_url
            FROM accounts a
            JOIN channels c ON a.channel_id = c.id
            WHERE a.id=?
        ''', (account_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_account_by_phone(self, phone: str) -> Optional[dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT a.*, c.name AS channel_name, c.webhook_url AS channel_webhook_url
            FROM accounts a
            JOIN channels c ON a.channel_id = c.id
            WHERE a.phone=?
        ''', (phone,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def add_account(self, channel_id: int, phone: str, api_id: str, api_hash: str,
                    session_name: str = None, proxy_host: str = None,
                    proxy_port: int = None, use_proxy: bool = False,
                    note: str = None) -> int:
        if not session_name:
            session_name = "session_" + phone.replace('+', '').replace(' ', '')
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO accounts
                (channel_id, phone, api_id, api_hash, session_name,
                 proxy_host, proxy_port, use_proxy, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (channel_id, phone, api_id, api_hash, session_name,
              proxy_host, proxy_port, 1 if use_proxy else 0, note))
        self.conn.commit()
        return cursor.lastrowid

    def update_account(self, account_id: int, channel_id: int, phone: str,
                       api_id: str, api_hash: str, session_name: str,
                       proxy_host: str, proxy_port: int, use_proxy: bool, note: str):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE accounts
            SET channel_id=?, phone=?, api_id=?, api_hash=?, session_name=?,
                proxy_host=?, proxy_port=?, use_proxy=?, note=?, updated_at=?
            WHERE id=?
        ''', (channel_id, phone, api_id, api_hash, session_name,
              proxy_host, proxy_port, 1 if use_proxy else 0,
              note, datetime.now(), account_id))
        self.conn.commit()

    def update_account_status(self, account_id: int, status: str):
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE accounts SET status=?, updated_at=? WHERE id=?',
            (status, datetime.now(), account_id)
        )
        self.conn.commit()

    def delete_account(self, account_id: int):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM accounts WHERE id=?', (account_id,))
        self.conn.commit()

    # ── Messages ───────────────────────────────────────────────────────────────

    def save_message(self, account_id: int, chat_id: int, chat_name: str,
                     chat_type: str, sender_id: int, sender_name: str,
                     sender_username: str, text: str, date, direction: str = 'in'):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO messages
                (account_id, chat_id, chat_name, chat_type, sender_id,
                 sender_name, sender_username, text, date, direction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (account_id, chat_id, chat_name, chat_type, sender_id,
              sender_name, sender_username, text, date, direction))
        self.conn.commit()

    def get_messages(self, account_id: int = None, chat_id: int = None,
                     limit: int = 100) -> List[dict]:
        cursor = self.conn.cursor()
        query = 'SELECT * FROM messages WHERE 1=1'
        params = []
        if account_id is not None:
            query += ' AND account_id=?'
            params.append(account_id)
        if chat_id is not None:
            query += ' AND chat_id=?'
            params.append(chat_id)
        query += ' ORDER BY date DESC LIMIT ?'
        params.append(limit)
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    # ── Monitored chats ────────────────────────────────────────────────────────

    def get_chats(self, account_id: int = None, channel_id: int = None) -> List[dict]:
        cursor = self.conn.cursor()
        if account_id:
            cursor.execute('''
                SELECT mc.*, a.phone AS account_phone, c.name AS channel_name
                FROM monitored_chats mc
                JOIN accounts a ON mc.account_id = a.id
                JOIN channels c ON a.channel_id = c.id
                WHERE mc.account_id = ?
                ORDER BY mc.created_at DESC
            ''', (account_id,))
        elif channel_id:
            cursor.execute('''
                SELECT mc.*, a.phone AS account_phone, c.name AS channel_name
                FROM monitored_chats mc
                JOIN accounts a ON mc.account_id = a.id
                JOIN channels c ON a.channel_id = c.id
                WHERE c.id = ?
                ORDER BY mc.created_at DESC
            ''', (channel_id,))
        else:
            cursor.execute('''
                SELECT mc.*, a.phone AS account_phone, c.name AS channel_name
                FROM monitored_chats mc
                JOIN accounts a ON mc.account_id = a.id
                JOIN channels c ON a.channel_id = c.id
                ORDER BY mc.created_at DESC
            ''')
        return [dict(row) for row in cursor.fetchall()]

    def ensure_monitored_chat(self, account_id: int, chat_id: int,
                              chat_name: str, chat_type: str):
        """收到消息时自动将该聊天加入监控列表（已存在则跳过）。"""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT id FROM monitored_chats WHERE account_id=? AND chat_id=?',
            (account_id, chat_id)
        )
        if cursor.fetchone() is None:
            cursor.execute('''
                INSERT OR IGNORE INTO monitored_chats
                    (account_id, chat_id, chat_name, chat_type)
                VALUES (?, ?, ?, ?)
            ''', (account_id, chat_id, chat_name or str(chat_id), chat_type or 'unknown'))
            self.conn.commit()

    def add_chat(self, account_id: int, chat_name: str,
                 chat_id: int = None, chat_type: str = None) -> int:
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO monitored_chats
                (account_id, chat_id, chat_name, chat_type)
            VALUES (?, ?, ?, ?)
        ''', (account_id, chat_id, chat_name, chat_type or 'unknown'))
        self.conn.commit()
        return cursor.lastrowid

    def toggle_chat(self, chat_id: int, enabled: bool):
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE monitored_chats SET enabled=? WHERE id=?',
            (1 if enabled else 0, chat_id)
        )
        self.conn.commit()

    def delete_chat(self, chat_id: int):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM monitored_chats WHERE id=?', (chat_id,))
        self.conn.commit()

    # ── Stats ──────────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM channels')
        total_channels = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM accounts')
        total_accounts = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE status='active'")
        active_accounts = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM monitored_chats WHERE enabled=1')
        active_chats = cursor.fetchone()[0]
        return {
            'total_channels': total_channels,
            'total_accounts': total_accounts,
            'active_accounts': active_accounts,
            'active_chats': active_chats,
        }

    def close(self):
        self.conn.close()
