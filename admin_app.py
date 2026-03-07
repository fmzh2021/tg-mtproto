# -*- coding: utf-8 -*-
"""
管理后台 - FastAPI Web 应用
层级：渠道 → 账号 → 监控群组

运行方式：
    python admin_app.py
"""
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import uvicorn

from admin_db import AdminDatabase

app = FastAPI(title="TG MTProto 管理后台")
templates = Jinja2Templates(directory="templates")
db = AdminDatabase()

STATUS_LABELS = {
    'active': '运行中',
    'inactive': '未启动',
    'error': '异常',
}

CHAT_TYPE_LABELS = {
    'private': '私聊',
    'group': '群组',
    'supergroup': '超级群组',
    'channel': '频道',
    'unknown': '未知',
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
):
    try:
        db.add_channel(name=name.strip(), description=description.strip() or None)
        return RedirectResponse("/channels?msg=渠道添加成功&msg_type=success", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/channels?msg={e}&msg_type=danger", status_code=303)


@app.post("/channels/{channel_id}/edit")
async def edit_channel(
    channel_id: int,
    name: str = Form(...),
    description: str = Form(default=""),
):
    try:
        db.update_channel(channel_id, name=name.strip(), description=description.strip() or None)
        return RedirectResponse("/channels?msg=渠道已更新&msg_type=success", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/channels?msg={e}&msg_type=danger", status_code=303)


@app.post("/channels/{channel_id}/delete")
async def delete_channel(channel_id: int):
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
    try:
        db.add_account(
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
        return RedirectResponse("/accounts?msg=账号添加成功&msg_type=success", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/accounts?msg={e}&msg_type=danger", status_code=303)


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


@app.post("/accounts/{account_id}/status")
async def update_status(account_id: int, status: str = Form(...)):
    db.update_account_status(account_id, status)
    label = STATUS_LABELS.get(status, status)
    return RedirectResponse(f"/accounts?msg=状态已更新为「{label}」&msg_type=success", status_code=303)


@app.post("/accounts/{account_id}/delete")
async def delete_account(account_id: int):
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


if __name__ == "__main__":
    uvicorn.run("admin_app:app", host="0.0.0.0", port=8000, reload=True)
