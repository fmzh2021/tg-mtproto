# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Telegram chat message synchronization tool using the MTProto protocol (via Telethon). Designed for customer service chat monitoring and compliance auditing. Syncs historical and real-time messages into a local SQLite database with search/export capabilities.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill in API credentials
```

Required `.env` variables:
- `API_ID` — from https://my.telegram.org/apps
- `API_HASH` — from https://my.telegram.org/apps
- `PHONE` — your Telegram phone number (with country code)

First run requires interactive phone verification code entry.

## Running

```bash
python main.py          # full sync + real-time monitoring
python query_messages.py  # search and export stored messages
python quick_start.py   # minimal connection test
```

## Tests

```bash
python test_basic.py    # database operations (no Telegram connection needed)
python test_proxy.py    # proxy configuration
```

## Architecture

| Module | Responsibility |
|--------|---------------|
| `config.py` | Loads `.env` vars via python-dotenv |
| `message_storage.py` | `MessageDatabase` class — SQLite CRUD for messages/users/chats |
| `main.py` | `sync_all_messages()`, `handle_new_message()` — Telethon client, async event loop |
| `query_messages.py` | `MessageQuery` class — keyword/sender/date search, CSV/JSON export |

**Data flow:** `.env` → Telethon client → dialogs → messages → SQLite (`messages.db`)

**Database tables:** `messages`, `users`, `chats`

**Async pattern:** all Telegram API calls use `async/await` with `asyncio`.

## Key Files

- `messages.db` — SQLite database (runtime, git-ignored)
- `*.session` — Telethon session files (contain auth tokens, git-ignored)
- `.env` — credentials (git-ignored)

## Proxy Support

SOCKS5 proxy can be configured in `.env`. See `PROXY_SETUP.md` for details. `test_proxy.py` validates proxy config without a live connection.
