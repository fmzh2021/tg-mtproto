# -*- coding: utf-8 -*-
"""
Telegram API 配置信息
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram API 配置
API_ID = int(os.getenv("API_ID", "1390314011"))
API_HASH = os.getenv("API_HASH", "10a8c8d190ea6eae4b19b3a754ad3e3ff1")
PHONE = os.getenv("PHONE", "+852955237421")

# 会话名称（用于存储登录信息）
SESSION_NAME = os.getenv("SESSION_NAME", "customer_service_sync")

# 代理配置
PROXY_HOST = os.getenv("PROXY_HOST", "127.0.0.1")
PROXY_PORT = int(os.getenv("PROXY_PORT", "7890"))
USE_PROXY = os.getenv("USE_PROXY", "false").lower() == "true"
