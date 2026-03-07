# -*- coding: utf-8 -*-
"""
FastAPI HTTP service exposing Telegram login, messaging, and webhook registration.

Run:
    python server.py
    uvicorn server:app --host 0.0.0.0 --port 8000
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from tg_manager import TelegramClientManager, SESSIONS_DIR
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

manager = TelegramClientManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: reconnect sessions that already have saved session files
    for session_file in SESSIONS_DIR.glob("*.session"):
        phone = "_" + session_file.stem  # stems are like _85295523742
        # Convert sanitized name back to phone format
        phone = session_file.stem.replace("_", "+", 1)  # first _ → +
        try:
            await manager.reconnect(phone)
            logger.info("Auto-reconnected session: %s", phone)
        except Exception as exc:
            logger.warning("Could not reconnect %s: %s", phone, exc)

    yield

    # Shutdown: disconnect all clients
    await manager.shutdown()


app = FastAPI(title="TG MTProto HTTP Service", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class CreateChannelRequest(BaseModel):
    webhook_url: str


class CreateChannelResponse(BaseModel):
    status: str
    channel_id: str


class AssignChannelRequest(BaseModel):
    phone: str
    channel_id: str


class AssignChannelResponse(BaseModel):
    status: str


class SendCodeRequest(BaseModel):
    phone: str
    api_id: int | None = None
    api_hash: str | None = None
    channel_id: str | None = None   # auto-assign channel at login time


class SendCodeResponse(BaseModel):
    status: str
    phone_code_hash: str


class SignInRequest(BaseModel):
    phone: str
    code: str
    password: str | None = None


class SignInResponse(BaseModel):
    status: str
    user_id: int
    username: str | None


class SendMessageRequest(BaseModel):
    phone: str
    peer: str
    text: str


class SendMessageResponse(BaseModel):
    status: str
    message_id: int


class RegisterWebhookRequest(BaseModel):
    phone: str
    webhook_url: str


class RegisterWebhookResponse(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/auth/send_code", response_model=SendCodeResponse)
async def send_code(req: SendCodeRequest):
    try:
        phone_code_hash = await manager.send_code(req.phone, req.api_id, req.api_hash, req.channel_id)
    except Exception as exc:
        logger.exception("send_code failed for %s", req.phone)
        raise HTTPException(status_code=500, detail=str(exc))
    return SendCodeResponse(status="code_sent", phone_code_hash=phone_code_hash)


@app.post("/auth/sign_in", response_model=SignInResponse)
async def sign_in(req: SignInRequest):
    try:
        user = await manager.sign_in(req.phone, req.code, req.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("sign_in failed for %s", req.phone)
        raise HTTPException(status_code=500, detail=str(exc))
    return SignInResponse(
        status="ok",
        user_id=user.id,
        username=getattr(user, "username", None),
    )


@app.post("/messages/send", response_model=SendMessageResponse)
async def send_message(req: SendMessageRequest):
    try:
        message = await manager.send_message(req.phone, req.peer, req.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("send_message failed for %s", req.phone)
        raise HTTPException(status_code=500, detail=str(exc))
    return SendMessageResponse(status="ok", message_id=message.id)


@app.post("/webhook/register", response_model=RegisterWebhookResponse)
async def register_webhook(req: RegisterWebhookRequest):
    try:
        manager.register_webhook(req.phone, req.webhook_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return RegisterWebhookResponse(status="ok")


@app.post("/channel/create", response_model=CreateChannelResponse)
async def create_channel(req: CreateChannelRequest):
    channel_id = manager.create_channel(req.webhook_url)
    return CreateChannelResponse(status="ok", channel_id=channel_id)


@app.post("/channel/assign", response_model=AssignChannelResponse)
async def assign_channel(req: AssignChannelRequest):
    try:
        manager.assign_channel(req.phone, req.channel_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return AssignChannelResponse(status="ok")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
