# -*- coding: utf-8 -*-
"""
Telegram API 配置信息
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram API 配置
API_ID = int(os.getenv("API_ID", "39031401"))
API_HASH = os.getenv("API_HASH", "0a8c8d190ea6eae4b19b3a754ad3e3ff")
PHONE = os.getenv("PHONE", "+85295523742")

# 会话名称（用于存储登录信息）
SESSION_NAME = os.getenv("SESSION_NAME", "customer_service_sync")

# 代理配置
PROXY_HOST = os.getenv("PROXY_HOST", "127.0.0.1")
PROXY_PORT = int(os.getenv("PROXY_PORT", "10808"))
USE_PROXY = os.getenv("USE_PROXY", "true").lower() == "true"
