# -*- coding: utf-8 -*-
"""
Multi-account Telegram client lifecycle management.
"""
import os
import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import socks
import httpx
from telethon import TelegramClient, events
from telethon.tl.types import User, Message

import config

logger = logging.getLogger(__name__)

SESSIONS_DIR = Path(__file__).parent / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

CHANNELS_FILE = SESSIONS_DIR / "channels.json"
# format: { "channels": {"uuid": "https://..."}, "assignments": {"+86...": "uuid"} }


def _sanitize_phone(phone: str) -> str:
    return phone.replace("+", "_").replace(" ", "_")


@dataclass
class ClientSession:
    client: TelegramClient
    webhook_url: str | None = None      # per-account (legacy/fallback)
    channel_id: str | None = None       # channel-level webhook (preferred)
    phone_code_hash: str | None = None


class TelegramClientManager:
    def __init__(self):
        self.sessions: dict[str, ClientSession] = {}
        self.channels: dict[str, str] = {}         # channel_id → webhook_url
        self.account_channels: dict[str, str] = {} # phone → channel_id
        self._load_channels()

    def _load_channels(self):
        if CHANNELS_FILE.exists():
            data = json.loads(CHANNELS_FILE.read_text())
            self.channels = data.get("channels", {})
            self.account_channels = data.get("assignments", {})

    def _save_channels(self):
        CHANNELS_FILE.write_text(json.dumps({
            "channels": self.channels,
            "assignments": self.account_channels,
        }, indent=2))

    def create_channel(self, webhook_url: str) -> str:
        """Create a new channel with a shared webhook URL. Returns channel_id."""
        channel_id = str(uuid.uuid4())
        self.channels[channel_id] = webhook_url
        self._save_channels()
        logger.info("Channel created: %s → %s", channel_id, webhook_url)
        return channel_id

    def assign_channel(self, phone: str, channel_id: str):
        """Assign a logged-in account to a channel."""
        if phone not in self.sessions:
            raise ValueError(f"Account {phone} not logged in.")
        if channel_id not in self.channels:
            raise ValueError(f"Channel {channel_id} does not exist.")
        self.sessions[phone].channel_id = channel_id
        self.account_channels[phone] = channel_id
        self._save_channels()
        logger.info("Account %s assigned to channel %s", phone, channel_id)

    def update_channel(self, channel_id: str, webhook_url: str):
        """Update the webhook URL for an existing channel."""
        if channel_id not in self.channels:
            raise ValueError(f"Channel {channel_id} does not exist.")
        self.channels[channel_id] = webhook_url
        self._save_channels()
        logger.info("Channel %s webhook updated → %s", channel_id, webhook_url)

    def _session_path(self, phone: str) -> str:
        return str(SESSIONS_DIR / _sanitize_phone(phone))

    def _make_client(self, phone: str, api_id: int, api_hash: str) -> TelegramClient:
        proxy = None
        if config.USE_PROXY:
            proxy = (socks.SOCKS5, config.PROXY_HOST, config.PROXY_PORT)
        return TelegramClient(
            self._session_path(phone),
            api_id,
            api_hash,
            proxy=proxy,
        )

    async def send_code(self, phone: str, api_id: int | None, api_hash: str | None, channel_id: str | None = None) -> str:
        """Step 1 of login: request SMS/app code. Returns phone_code_hash."""
        api_id = api_id or config.API_ID
        api_hash = api_hash or config.API_HASH

        # Disconnect existing client for this phone if any
        if phone in self.sessions:
            try:
                await self.sessions[phone].client.disconnect()
            except Exception:
                pass

        client = self._make_client(phone, api_id, api_hash)
        await client.connect()

        result = await client.send_code_request(phone)
        self.sessions[phone] = ClientSession(
            client=client,
            phone_code_hash=result.phone_code_hash,
            channel_id=channel_id,  # stored for auto-assign after sign_in
        )
        return result.phone_code_hash

    async def sign_in(self, phone: str, code: str, password: str | None = None) -> User:
        """Step 2 of login: submit code (and optional 2FA password). Returns Telethon User."""
        if phone not in self.sessions:
            raise ValueError(f"No pending login for {phone}. Call send_code first.")

        session = self.sessions[phone]
        client = session.client

        try:
            user = await client.sign_in(
                phone=phone,
                code=code,
                phone_code_hash=session.phone_code_hash,
            )
        except Exception as exc:
            # Handle 2FA
            if password and "SessionPasswordNeeded" in type(exc).__name__:
                user = await client.sign_in(password=password)
            else:
                raise

        session.phone_code_hash = None
        self._register_handler(phone, session)

        # Finalize channel assignment if one was pre-specified during send_code
        if session.channel_id:
            if session.channel_id in self.channels:
                self.account_channels[phone] = session.channel_id
                self._save_channels()
                logger.info("Auto-assigned %s to channel %s", phone, session.channel_id)
            else:
                logger.warning("Channel %s not found; clearing assignment for %s", session.channel_id, phone)
                session.channel_id = None

        logger.info("Signed in %s as user_id=%s", phone, user.id)
        return user

    async def reconnect(self, phone: str, api_id: int | None = None, api_hash: str | None = None):
        """Reconnect an existing session file (e.g. after server restart)."""
        api_id = api_id or config.API_ID
        api_hash = api_hash or config.API_HASH

        client = self._make_client(phone, api_id, api_hash)
        await client.connect()

        if not await client.is_user_authorized():
            await client.disconnect()
            raise RuntimeError(f"Session for {phone} is not authorized")

        session = ClientSession(client=client)
        session.channel_id = self.account_channels.get(phone)
        self.sessions[phone] = session
        self._register_handler(phone, session)
        logger.info("Reconnected existing session for %s (channel=%s)", phone, session.channel_id)

    def _register_handler(self, phone: str, session: ClientSession):
        """Attach a NewMessage event handler to the client."""
        client = session.client

        # Remove previous handlers to avoid duplicates on reconnect
        client.remove_event_handler(None)

        @client.on(events.NewMessage)
        async def handler(event):
            await self._fire_webhook(phone, event.message)

    async def send_message(self, phone: str, peer: str, text: str) -> Message:
        """Send a message from the given account."""
        if phone not in self.sessions:
            raise ValueError(f"Account {phone} not logged in.")

        client = self.sessions[phone].client
        message = await client.send_message(peer, text)
        return message

    def register_webhook(self, phone: str, url: str):
        """Store the webhook URL for a given account."""
        if phone not in self.sessions:
            raise ValueError(f"Account {phone} not logged in.")
        self.sessions[phone].webhook_url = url
        logger.info("Webhook registered for %s → %s", phone, url)

    async def _fire_webhook(self, phone: str, message: Message):
        """POST message payload to registered webhook URL (best-effort)."""
        session = self.sessions.get(phone)
        if not session:
            return

        # Prefer channel webhook, fall back to per-account webhook
        if session.channel_id and session.channel_id in self.channels:
            webhook_url = self.channels[session.channel_id]
        elif session.webhook_url:
            webhook_url = session.webhook_url
        else:
            return  # no webhook configured

        try:
            chat = await message.get_chat()
            sender = await message.get_sender()

            chat_name = getattr(chat, "title", None) or getattr(chat, "first_name", "") or ""
            chat_type = type(chat).__name__.lower()
            sender_name = getattr(sender, "first_name", "") or ""
            last = getattr(sender, "last_name", None)
            if last:
                sender_name = f"{sender_name} {last}".strip()
            sender_username = getattr(sender, "username", None)

            payload = {
                "account": phone,
                "message_id": message.id,
                "chat_id": message.chat_id,
                "chat_name": chat_name,
                "chat_type": chat_type,
                "sender_id": message.sender_id,
                "sender_name": sender_name,
                "sender_username": sender_username,
                "text": message.text or "",
                "date": message.date.isoformat() if message.date else None,
            }

            async with httpx.AsyncClient(timeout=10) as http:
                resp = await http.post(webhook_url, json=payload)
                logger.debug("Webhook %s → %s: %s", phone, webhook_url, resp.status_code)
        except Exception as exc:
            logger.warning("Webhook delivery failed for %s: %s", phone, exc)

    async def shutdown(self):
        """Disconnect all clients gracefully."""
        for phone, session in list(self.sessions.items()):
            try:
                await session.client.disconnect()
                logger.info("Disconnected %s", phone)
            except Exception as exc:
                logger.warning("Error disconnecting %s: %s", phone, exc)
