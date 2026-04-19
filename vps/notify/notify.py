#!/usr/bin/env python3
"""Уведомления в Telegram. Использование: python3 notify.py success|failure|info "текст"

Требует: OPENCLAW_TG_BOT и TG_NOTIFY_CHAT_ID в окружении (из /root/.env).
"""
import os
import sys
import requests

BOT_TOKEN = os.environ.get("OPENCLAW_TG_BOT", "")
CHAT_ID = os.environ.get("TG_NOTIFY_CHAT_ID", "")

if not BOT_TOKEN or not CHAT_ID:
    sys.exit(0)

level = sys.argv[1] if len(sys.argv) > 1 else "info"
message = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

icons = {"success": "✅", "failure": "❌", "info": "ℹ️"}
icon = icons.get(level, "📢")

tg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
requests.post(tg_url, json={"chat_id": CHAT_ID, "text": f"{icon} {message}"}, timeout=10)
