# -*- coding: utf-8 -*-
"""
管理后台 - FastAPI Web 应用
层级：渠道 → 账号 → 监控群组

运行方式：
    python admin_app.py
    uvicorn admin_app:app --host 0.0.0.0 --port 8000
"""
import logging
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from admin_db import AdminDatabase
from tg_manager import TelegramClientManager, SESSIONS_DIR
from server import router as api_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

db = AdminDatabase()


async def on_new_message(phone: str, message):
    """收到消息时：自动存库 + 自动加入监控群组。"""
    account = db.get_account_by_phone(phone)
    if not account:
        return

    account_id = account['id']

    try:
        chat = await message.get_chat()
        sender = await message.get_sender()
    except Exception as exc:
        logger.warning("on_new_message: failed to get chat/sender for %s: %s", phone, exc)
        return

    chat_id = message.chat_id
    chat_name = (getattr(chat, 'title', None)
                 or getattr(chat, 'first_name', None)
                 or str(chat_id))
    chat_type = type(chat).__name__.lower()

    # 自动加入监控群组
    db.ensure_monitored_chat(account_id, chat_id, chat_name, chat_type)

    # 存消息
    first = getattr(sender, 'first_name', '') or ''
    last = getattr(sender, 'last_name', '') or ''
    sender_name = f"{first} {last}".strip() or getattr(sender, 'title', '') or ''
    db.save_message(
        account_id=account_id,
        chat_id=chat_id,
        chat_name=chat_name,
        chat_type=chat_type,
        sender_id=getattr(sender, 'id', None),
        sender_name=sender_name,
        sender_username=getattr(sender, 'username', None),
        text=message.text or '',
        date=message.date,
        direction='in',
    )


manager = TelegramClientManager(message_callback=on_new_message)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 将 manager 挂到 app.state，供 API 路由通过依赖注入获取
    app.state.manager = manager

    # 启动时重连所有 active 账号
    for account in db.get_accounts():
        if account['status'] == 'active':
            try:
                await manager.reconnect(
                    account['phone'],
                    int(account['api_id']),
                    account['api_hash'],
                )
                webhook_url = account.get('channel_webhook_url')
                if webhook_url and account['phone'] in manager.sessions:
                    manager.register_webhook(account['phone'], webhook_url)
                logger.info("Reconnected %s", account['phone'])
            except Exception as exc:
                logger.warning("Could not reconnect %s: %s", account['phone'], exc)
                db.update_account_status(account['id'], 'error')
    yield
    await manager.shutdown()


app = FastAPI(title="TG MTProto 管理后台", lifespan=lifespan)
app.include_router(api_router)
templates = Jinja2Templates(directory="templates")

STATUS_LABELS = {
    'active':   '运行中',
    'inactive': '未启动',
    'pending':  '待验证',
    'error':    '异常',
}

CHAT_TYPE_LABELS = {
    'private':    '私聊',
    'group':      '群组',
    'supergroup': '超级群组',
    'channel':    '频道',
    'unknown':    '未知',
}


# ── Dashboard ──────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, msg: str = None, msg_type: str = "success"):
    stats = db.get_stats()
    channels = db.get_channels()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "stats": stats,
        "channels": channels,
        "msg": msg,
        "msg_type": msg_type,
    })


# ── Channels（渠道）────────────────────────────────────────────────────────────

@app.get("/channels", response_class=HTMLResponse)
async def channels_list(request: Request, msg: str = None, msg_type: str = "success"):
    channels = db.get_channels()
    return templates.TemplateResponse("channels.html", {
        "request": request,
        "channels": channels,
        "msg": msg,
        "msg_type": msg_type,
    })


@app.post("/channels/add")
async def add_channel(
    name: str = Form(...),
    description: str = Form(default=""),
    webhook_url: str = Form(default=""),
):
    try:
        db.add_channel(
            name=name.strip(),
            description=description.strip() or None,
            webhook_url=webhook_url.strip() or None,
        )
        return RedirectResponse("/channels?msg=渠道添加成功&msg_type=success", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/channels?msg={e}&msg_type=danger", status_code=303)


@app.post("/channels/{channel_id}/edit")
async def edit_channel(
    channel_id: int,
    name: str = Form(...),
    description: str = Form(default=""),
    webhook_url: str = Form(default=""),
):
    try:
        new_webhook = webhook_url.strip() or None
        db.update_channel(
            channel_id,
            name=name.strip(),
            description=description.strip() or None,
            webhook_url=new_webhook,
        )
        # 同步更新该渠道下所有在线账号的 webhook
        if new_webhook:
            for acc in db.get_accounts(channel_id=channel_id):
                if acc['phone'] in manager.sessions:
                    manager.register_webhook(acc['phone'], new_webhook)
        return RedirectResponse("/channels?msg=渠道已更新&msg_type=success", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/channels?msg={e}&msg_type=danger", status_code=303)


@app.post("/channels/{channel_id}/delete")
async def delete_channel(channel_id: int):
    # 断开该渠道下所有在线账号
    for acc in db.get_accounts(channel_id=channel_id):
        phone = acc['phone']
        if phone in manager.sessions:
            try:
                await manager.sessions[phone].client.disconnect()
                del manager.sessions[phone]
            except Exception:
                pass
    db.delete_channel(channel_id)
    return RedirectResponse("/channels?msg=渠道已删除（关联账号一并删除）&msg_type=warning", status_code=303)


# ── Accounts（账号）────────────────────────────────────────────────────────────

@app.get("/accounts", response_class=HTMLResponse)
async def accounts_list(
    request: Request,
    channel_id: Optional[int] = None,
    msg: str = None,
    msg_type: str = "success",
):
    accounts = db.get_accounts(channel_id=channel_id)
    channels = db.get_channels()
    return templates.TemplateResponse("accounts.html", {
        "request": request,
        "accounts": accounts,
        "channels": channels,
        "selected_channel_id": channel_id,
        "status_labels": STATUS_LABELS,
        "msg": msg,
        "msg_type": msg_type,
    })


@app.post("/accounts/add")
async def add_account(
    channel_id: int = Form(...),
    phone: str = Form(...),
    api_id: str = Form(...),
    api_hash: str = Form(...),
    session_name: str = Form(default=""),
    proxy_host: str = Form(default=""),
    proxy_port: str = Form(default=""),
    use_proxy: str = Form(default=""),
    note: str = Form(default=""),
):
    account_id = None
    try:
        account_id = db.add_account(
            channel_id=channel_id,
            phone=phone.strip(),
            api_id=api_id.strip(),
            api_hash=api_hash.strip(),
            session_name=session_name.strip() or None,
            proxy_host=proxy_host.strip() or None,
            proxy_port=int(proxy_port) if proxy_port.strip() else None,
            use_proxy=use_proxy == "on",
            note=note.strip() or None,
        )
        # 发送验证码，触发登录流程
        await manager.send_code(phone.strip(), int(api_id.strip()), api_hash.strip())
        db.update_account_status(account_id, 'pending')
        return RedirectResponse(f"/accounts/{account_id}/verify", status_code=303)
    except Exception as e:
        if account_id:
            db.delete_account(account_id)
        return RedirectResponse(f"/accounts?msg={e}&msg_type=danger", status_code=303)


@app.get("/accounts/{account_id}/verify", response_class=HTMLResponse)
async def verify_form(
    request: Request,
    account_id: int,
    msg: str = None,
    msg_type: str = "success",
):
    account = db.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    return templates.TemplateResponse("enter_code.html", {
        "request": request,
        "account": account,
        "msg": msg,
        "msg_type": msg_type,
    })


@app.post("/accounts/{account_id}/verify")
async def verify_code(
    account_id: int,
    code: str = Form(...),
    password: str = Form(default=""),
):
    account = db.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    try:
        user = await manager.sign_in(account['phone'], code.strip(), password.strip() or None)
        db.update_account_status(account_id, 'active')
        # 注册 webhook（如果渠道配置了）
        webhook_url = account.get('channel_webhook_url')
        if webhook_url and account['phone'] in manager.sessions:
            manager.register_webhook(account['phone'], webhook_url)
        logger.info("Signed in %s (user_id=%s)", account['phone'], user.id)
        return RedirectResponse(
            f"/accounts?msg=账号 {account['phone']} 登录成功&msg_type=success",
            status_code=303,
        )
    except Exception as e:
        return RedirectResponse(
            f"/accounts/{account_id}/verify?msg={e}&msg_type=danger",
            status_code=303,
        )


@app.post("/accounts/{account_id}/send_code")
async def resend_code(account_id: int):
    account = db.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    try:
        await manager.send_code(account['phone'], int(account['api_id']), account['api_hash'])
        db.update_account_status(account_id, 'pending')
        return RedirectResponse(
            f"/accounts/{account_id}/verify?msg=验证码已重新发送&msg_type=success",
            status_code=303,
        )
    except Exception as e:
        return RedirectResponse(
            f"/accounts/{account_id}/verify?msg={e}&msg_type=danger",
            status_code=303,
        )


@app.get("/accounts/{account_id}/edit", response_class=HTMLResponse)
async def edit_account_form(request: Request, account_id: int):
    account = db.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    channels = db.get_channels()
    return templates.TemplateResponse("account_edit.html", {
        "request": request,
        "account": account,
        "channels": channels,
    })


@app.post("/accounts/{account_id}/edit")
async def edit_account(
    account_id: int,
    channel_id: int = Form(...),
    phone: str = Form(...),
    api_id: str = Form(...),
    api_hash: str = Form(...),
    session_name: str = Form(default=""),
    proxy_host: str = Form(default=""),
    proxy_port: str = Form(default=""),
    use_proxy: str = Form(default=""),
    note: str = Form(default=""),
):
    try:
        db.update_account(
            account_id=account_id,
            channel_id=channel_id,
            phone=phone.strip(),
            api_id=api_id.strip(),
            api_hash=api_hash.strip(),
            session_name=session_name.strip(),
            proxy_host=proxy_host.strip() or None,
            proxy_port=int(proxy_port) if proxy_port.strip() else None,
            use_proxy=use_proxy == "on",
            note=note.strip() or None,
        )
        return RedirectResponse("/accounts?msg=账号已更新&msg_type=success", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/accounts?msg={e}&msg_type=danger", status_code=303)


@app.post("/accounts/{account_id}/delete")
async def delete_account(account_id: int):
    account = db.get_account(account_id)
    if account:
        phone = account['phone']
        if phone in manager.sessions:
            try:
                await manager.sessions[phone].client.disconnect()
                del manager.sessions[phone]
                logger.info("Disconnected %s on delete", phone)
            except Exception as exc:
                logger.warning("Error disconnecting %s: %s", phone, exc)
    db.delete_account(account_id)
    return RedirectResponse("/accounts?msg=账号已删除&msg_type=warning", status_code=303)


# ── Groups（监控群组）─────────────────────────────────────────────────────────

@app.get("/groups", response_class=HTMLResponse)
async def groups_list(
    request: Request,
    account_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    msg: str = None,
    msg_type: str = "success",
):
    chats = db.get_chats(account_id=account_id, channel_id=channel_id)
    accounts = db.get_accounts()
    channels = db.get_channels()
    return templates.TemplateResponse("groups.html", {
        "request": request,
        "chats": chats,
        "accounts": accounts,
        "channels": channels,
        "selected_account_id": account_id,
        "selected_channel_id": channel_id,
        "chat_type_labels": CHAT_TYPE_LABELS,
        "msg": msg,
        "msg_type": msg_type,
    })


@app.post("/groups/add")
async def add_group(
    account_id: int = Form(...),
    chat_name: str = Form(...),
    chat_type: str = Form(default="unknown"),
):
    try:
        db.add_chat(account_id=account_id, chat_name=chat_name.strip(), chat_type=chat_type)
        return RedirectResponse("/groups?msg=群组添加成功&msg_type=success", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/groups?msg={e}&msg_type=danger", status_code=303)


@app.post("/groups/{chat_id}/toggle")
async def toggle_group(chat_id: int, enabled: str = Form(...)):
    db.toggle_chat(chat_id, enabled == "1")
    state = "已启用" if enabled == "1" else "已停用"
    return RedirectResponse(f"/groups?msg=群组{state}&msg_type=success", status_code=303)


@app.post("/groups/{chat_id}/delete")
async def delete_group(chat_id: int):
    db.delete_chat(chat_id)
    return RedirectResponse("/groups?msg=群组已删除&msg_type=warning", status_code=303)


# ── Messages（消息查看 & 回复）────────────────────────────────────────────────

@app.get("/messages", response_class=HTMLResponse)
async def messages_view(
    request: Request,
    account_id: int,
    chat_id: int,
    msg: str = None,
    msg_type: str = "success",
):
    account = db.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    messages = db.get_messages(account_id=account_id, chat_id=chat_id, limit=200)
    messages.reverse()  # 时间正序展示
    # 取聊天元信息（名称等）
    chat_info = next(
        (c for c in db.get_chats(account_id=account_id) if c['chat_id'] == chat_id),
        None,
    )
    return templates.TemplateResponse("messages.html", {
        "request": request,
        "account": account,
        "chat_id": chat_id,
        "chat_info": chat_info,
        "messages": messages,
        "msg": msg,
        "msg_type": msg_type,
    })


@app.post("/messages/send")
async def send_message_ui(
    account_id: int = Form(...),
    chat_id: int = Form(...),
    text: str = Form(...),
):
    account = db.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    redirect_base = f"/messages?account_id={account_id}&chat_id={chat_id}"
    try:
        msg = await manager.send_message(account['phone'], chat_id, text.strip())
        db.save_message(
            account_id=account_id,
            chat_id=chat_id,
            chat_name='',
            chat_type='',
            sender_id=None,
            sender_name=account['phone'],
            sender_username=None,
            text=text.strip(),
            date=msg.date,
            direction='out',
        )
        return RedirectResponse(redirect_base, status_code=303)
    except Exception as e:
        logger.exception("send_message_ui failed for account %s", account_id)
        return RedirectResponse(
            f"{redirect_base}&msg={e}&msg_type=danger", status_code=303
        )


if __name__ == "__main__":
    uvicorn.run("admin_app:app", host="0.0.0.0", port=8000, reload=False)
