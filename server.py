# -*- coding: utf-8 -*-
"""
FastAPI APIRouter — Telegram 登录、发消息、Webhook 注册、渠道管理。

本模块不独立运行，由 admin_app.py 挂载。
路由前缀：/api
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from tg_manager import TelegramClientManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["API"])


# ---------------------------------------------------------------------------
# 依赖：从 app.state 获取共享 manager 实例
# ---------------------------------------------------------------------------

def get_manager(request: Request) -> TelegramClientManager:
    return request.app.state.manager


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
    channel_id: str | None = None


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

@router.post("/auth/send_code", response_model=SendCodeResponse)
async def send_code(req: SendCodeRequest, manager: TelegramClientManager = Depends(get_manager)):
    try:
        phone_code_hash = await manager.send_code(req.phone, req.api_id, req.api_hash, req.channel_id)
    except Exception as exc:
        logger.exception("send_code failed for %s", req.phone)
        raise HTTPException(status_code=500, detail=str(exc))
    return SendCodeResponse(status="code_sent", phone_code_hash=phone_code_hash)


@router.post("/auth/sign_in", response_model=SignInResponse)
async def sign_in(req: SignInRequest, manager: TelegramClientManager = Depends(get_manager)):
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


@router.post("/messages/send", response_model=SendMessageResponse)
async def send_message(req: SendMessageRequest, manager: TelegramClientManager = Depends(get_manager)):
    try:
        message = await manager.send_message(req.phone, req.peer, req.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("send_message failed for %s", req.phone)
        raise HTTPException(status_code=500, detail=str(exc))
    return SendMessageResponse(status="ok", message_id=message.id)


@router.post("/webhook/register", response_model=RegisterWebhookResponse)
async def register_webhook(req: RegisterWebhookRequest, manager: TelegramClientManager = Depends(get_manager)):
    try:
        manager.register_webhook(req.phone, req.webhook_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return RegisterWebhookResponse(status="ok")


@router.post("/channel/create", response_model=CreateChannelResponse)
async def create_channel(req: CreateChannelRequest, manager: TelegramClientManager = Depends(get_manager)):
    channel_id = manager.create_channel(req.webhook_url)
    return CreateChannelResponse(status="ok", channel_id=channel_id)


@router.post("/channel/assign", response_model=AssignChannelResponse)
async def assign_channel(req: AssignChannelRequest, manager: TelegramClientManager = Depends(get_manager)):
    try:
        manager.assign_channel(req.phone, req.channel_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return AssignChannelResponse(status="ok")
