# -*- coding: utf-8 -*-
"""
FastAPI APIRouter — Telegram 登录、发消息、Webhook 注册、渠道管理。

本模块不独立运行，由 admin_app.py 挂载。
路由前缀：/api
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

import config
from admin_db import AdminDatabase
from tg_manager import TelegramClientManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["API"])


# ---------------------------------------------------------------------------
# 依赖：从 app.state 获取共享 manager 实例
# ---------------------------------------------------------------------------

def get_manager(request: Request) -> TelegramClientManager:
    return request.app.state.manager


def get_db(request: Request) -> AdminDatabase:
    return request.app.state.db


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class CreateChannelRequest(BaseModel):
    name: str
    webhook_url: str | None = None
    api_id: int | None = None
    api_hash: str | None = None


class CreateChannelResponse(BaseModel):
    status: str
    app_id: str


class AssignChannelRequest(BaseModel):
    phone: str
    channel_id: str


class AssignChannelResponse(BaseModel):
    status: str


class SendCodeRequest(BaseModel):
    app_id: str
    phone: str


class SendCodeResponse(BaseModel):
    status: str
    phone_code_hash: str


class SignInRequest(BaseModel):
    app_id: str
    phone: str
    code: str
    password: str | None = None


class SignInResponse(BaseModel):
    status: str
    account_id: int
    app_id: str
    phone: str
    user_id: int
    username: str | None
    first_name: str | None
    last_name: str | None


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
async def send_code(
    req: SendCodeRequest,
    manager: TelegramClientManager = Depends(get_manager),
    db: AdminDatabase = Depends(get_db),
):
    channel = db.get_channel_by_app_id(req.app_id)
    if not channel:
        raise HTTPException(status_code=404, detail=f"渠道 {req.app_id} 不存在")
    api_id = int(channel["api_id"]) if channel.get("api_id") else config.API_ID
    api_hash = channel["api_hash"] if channel.get("api_hash") else config.API_HASH
    try:
        phone_code_hash = await manager.send_code(req.phone, api_id, api_hash)
    except Exception as exc:
        logger.exception("send_code failed for %s", req.phone)
        raise HTTPException(status_code=500, detail=str(exc))
    return SendCodeResponse(status="code_sent", phone_code_hash=phone_code_hash)


@router.post("/auth/sign_in", response_model=SignInResponse)
async def sign_in(
    req: SignInRequest,
    manager: TelegramClientManager = Depends(get_manager),
    db: AdminDatabase = Depends(get_db),
):
    channel = db.get_channel_by_app_id(req.app_id)
    if not channel:
        raise HTTPException(status_code=404, detail=f"渠道 {req.app_id} 不存在")
    try:
        user = await manager.sign_in(req.phone, req.code, req.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("sign_in failed for %s", req.phone)
        raise HTTPException(status_code=500, detail=str(exc))

    # 登录成功后创建或更新账号记录
    tg_api_id = channel["api_id"] if channel.get("api_id") else str(config.API_ID)
    tg_api_hash = channel["api_hash"] if channel.get("api_hash") else config.API_HASH
    existing = db.get_account_by_phone(req.phone)
    if existing:
        account_id = existing["id"]
        db.update_account_status(account_id, "active")
    else:
        account_id = db.add_account(
            channel_id=channel["id"],
            phone=req.phone,
            api_id=tg_api_id,
            api_hash=tg_api_hash,
        )
        db.update_account_status(account_id, "active")

    # 注册渠道 webhook
    webhook_url = channel.get("webhook_url")
    if webhook_url and req.phone in manager.sessions:
        manager.register_webhook(req.phone, webhook_url)

    return SignInResponse(
        status="ok",
        account_id=account_id,
        app_id=req.app_id,
        phone=req.phone,
        user_id=user.id,
        username=getattr(user, "username", None),
        first_name=getattr(user, "first_name", None),
        last_name=getattr(user, "last_name", None),
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
async def create_channel(
    req: CreateChannelRequest,
    manager: TelegramClientManager = Depends(get_manager),
    db: AdminDatabase = Depends(get_db),
):
    db_channel_id = db.add_channel(
        name=req.name,
        webhook_url=req.webhook_url,
        api_id=str(req.api_id) if req.api_id else None,
        api_hash=req.api_hash,
    )
    channel = db.get_channel(db_channel_id)
    return CreateChannelResponse(status="ok", app_id=channel["app_id"])


@router.post("/channel/assign", response_model=AssignChannelResponse)
async def assign_channel(req: AssignChannelRequest, manager: TelegramClientManager = Depends(get_manager)):
    try:
        manager.assign_channel(req.phone, req.channel_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return AssignChannelResponse(status="ok")
