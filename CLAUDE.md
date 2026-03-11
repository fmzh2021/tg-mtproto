# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A multi-account Telegram monitoring service using the MTProto protocol (via Telethon). Designed for customer service chat monitoring and compliance auditing. Exposes an HTTP API for account management and real-time message forwarding via webhooks.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill in API credentials
```

Required `.env` variables:
- `API_ID` — from https://my.telegram.org/apps (default fallback)
- `API_HASH` — from https://my.telegram.org/apps (default fallback)
- `USE_PROXY` / `PROXY_HOST` / `PROXY_PORT` — optional SOCKS5 proxy

## Running

```bash
# HTTP API service (multi-account)
python server.py
# or
uvicorn server:app --host 0.0.0.0 --port 8000

# Admin web UI (configuration management)
python admin_app.py
```

## Tests

```bash
python test_proxy.py    # proxy configuration check
```

## Architecture

| Module | Responsibility |
|--------|---------------|
| `config.py` | Loads `.env` vars via python-dotenv |
| `tg_manager.py` | `TelegramClientManager` — multi-account Telethon lifecycle, login, webhook dispatch |
| `server.py` | FastAPI HTTP API — auth, messaging, webhook registration, channel management |
| `admin_app.py` | FastAPI web admin UI — channels/accounts/monitored groups CRUD |
| `admin_db.py` | `AdminDatabase` — SQLite CRUD for `admin.db` (channels → accounts → monitored_chats) |

**Data flow:** HTTP request → `server.py` → `tg_manager.py` → Telegram MTProto → webhook POST

**Hierarchy:** Channel (渠道) → Account (账号) → Monitored Chat (监控群组)

**Async pattern:** all Telegram API calls use `async/await` with `asyncio`.

## Key Files

- `admin.db` — SQLite config database (runtime, git-ignored)
- `sessions/` — Telethon session files per account (contain auth tokens, git-ignored)
- `.env` — credentials (git-ignored)

## Proxy Support

SOCKS5 proxy can be configured in `.env`. See `PROXY_SETUP.md` for details. `test_proxy.py` validates proxy config without a live connection.
