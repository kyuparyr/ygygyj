# =========================================================
# ⛧⃟ LOFI PAPA GC TOOL — FINAL + ADMIN SECURITY ⛧⃟
# Ultra Fast • Stable • Admin Locked
# =========================================================

import asyncio
import json
import os
import io
import logging
from typing import Dict

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.error import RetryAfter, TimedOut
from gtts import gTTS

# ---------------- CONFIG ----------------
TOKENS = [
    "7648527008:AAHj47lOd6GOCw3iNPnqSooq6mrUDtVYKv0",
    "8313155600:AAH0y7wlc1G_3XdPr_U7ubcf9BAIGhv-ZRo",
    "8359976836:AAH91_m57K2nMdj6VAyY7587ox7Tw_VM1G0",
    "8383716273:AAGi94iyKbDoEpb652d18uLNOkxVG9y1rZE",
    "8359614490:AAEllJnufmEIKDzztF1UxfzCNHC6MJSZBbM",
]

OWNER_ID = 6416341860
SUDO_FILE = "sudo.json"

# ---------------- RAID DATA ----------------
RAID_TEXTS = [
    "⛧⃟𓆩𓆪⛧", "𓆩🩸𓆪", "☠︎︎𓆩𓆪☠︎︎", "𓆰⚔𓆪", "𓆩𓂀𓆪",
    "𓆩☣𓆪", "𓆩𓃵𓆪", "𓆩𓃭𓆪", "⸸𓆩𓆪⸸", "𓆩☠︎︎𓆪",
]

SPAM_PATTERNS = [
    "[ any text ] 💀" * 40,
    "[ any text ] ⚡" * 40,
]

logging.basicConfig(level=logging.INFO)

# ---------------- ADMIN SYSTEM ----------------
def load_sudo():
    if os.path.exists(SUDO_FILE):
        try:
            with open(SUDO_FILE, "r") as f:
                return set(json.load(f))
        except:
            pass
    return {OWNER_ID}

def save_sudo():
    with open(SUDO_FILE, "w") as f:
        json.dump(list(SUDO_USERS), f)

def is_admin(uid: int) -> bool:
    return uid == OWNER_ID or uid in SUDO_USERS

SUDO_USERS = load_sudo()

def only_admin(func):
    async def wrap(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not user or not is_admin(user.id):
            return
        return await func(update, context)
    return wrap

# ---------------- STATE ----------------
apps = []
bots = []

group_tasks: Dict[int, Dict[str, asyncio.Task]] = {}
voice_tasks: Dict[int, asyncio.Task] = {}
spam_tasks: Dict[int, asyncio.Task] = {}
reply_mode: Dict[int, str] = {}
reply_idx: Dict[int, int] = {}

VOICE_CACHE = []

# ---------------- CORE LOOPS ----------------
async def nc_loop(bot, chat_id, base, start, step):
    i = start
    while True:
        try:
            await bot.set_chat_title(chat_id, f"{base} {RAID_TEXTS[i % len(RAID_TEXTS)]}")
            i += step
            await asyncio.sleep(1)
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after)
        except:
            continue

async def generate_voice_cache():
    if VOICE_CACHE:
        return
    for t in RAID_TEXTS:
        bio = io.BytesIO()
        gTTS(text=t, lang="en").write_to_fp(bio)
        bio.seek(0)
        VOICE_CACHE.append(bio.read())

async def voice_loop(bot, chat_id):
    i = 0
    while True:
        try:
            v = io.BytesIO(VOICE_CACHE[i % len(VOICE_CACHE)])
            v.seek(0)
            await bot.send_voice(chat_id, voice=v)
            i += 1
            await asyncio.sleep(1)
        except:
            continue

async def spam_loop(bot, chat_id, base):
    i = 0
    while True:
        try:
            msg = SPAM_PATTERNS[i % len(SPAM_PATTERNS)].replace("[ any text ]", base)
            await bot.send_message(chat_id, msg)
            i += 1
            await asyncio.sleep(0.2)
        except:
            continue

# ---------------- COMMANDS ----------------
@only_admin
async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = int(context.args[0])
        SUDO_USERS.add(uid)
        save_sudo()
        await update.message.reply_text(f"✅ ADMIN ADDED: `{uid}`")
    except:
        pass

@only_admin
async def deladmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = int(context.args[0])
        if uid != OWNER_ID:
            SUDO_USERS.discard(uid)
            save_sudo()
            await update.message.reply_text(f"🗑 ADMIN REMOVED: `{uid}`")
    except:
        pass

@only_admin
async def ncloop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    base = " ".join(context.args)
    cid = update.message.chat_id
    group_tasks.setdefault(cid, {})
    step = len(bots)

    for i, bot in enumerate(bots):
        if bot.token not in group_tasks[cid]:
            group_tasks[cid][bot.token] = asyncio.create_task(
                nc_loop(bot, cid, base, i, step)
            )
    await update.message.reply_text("✅ NC STARTED")

@only_admin
async def stopgcnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.message.chat_id
    if cid in group_tasks:
        for t in group_tasks[cid].values():
            t.cancel()
        group_tasks[cid] = {}
    await update.message.reply_text("🛑 NC STOPPED")

@only_admin
async def spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.message.chat_id
    if cid in spam_tasks:
        spam_tasks[cid].cancel()
    spam_tasks[cid] = asyncio.create_task(
        spam_loop(context.bot, cid, " ".join(context.args))
    )
    await update.message.reply_text("💥 SPAM STARTED")

@only_admin
async def stopspam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.message.chat_id
    if cid in spam_tasks:
        spam_tasks[cid].cancel()
        spam_tasks.pop(cid)
    await update.message.reply_text("🛑 SPAM STOPPED")

# ---------------- BUILD ----------------
def build_app(token):
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("addadmin", addadmin))
    app.add_handler(CommandHandler("deladmin", deladmin))
    app.add_handler(CommandHandler("ncloop", ncloop))
    app.add_handler(CommandHandler("stopgcnc", stopgcnc))
    app.add_handler(CommandHandler("spam", spam))
    app.add_handler(CommandHandler("stopspam", stopspam))
    return app

async def run_all():
    await generate_voice_cache()
    for t in TOKENS:
        app = build_app(t)
        apps.append(app)

    for app in apps:
        asyncio.create_task(app.run_polling(close_loop=False))
        bots.append(app.bot)
        await asyncio.sleep(0.5)

    print("🚀 LOFI PAPA LIVE — ADMIN LOCK ENABLED")
    await asyncio.Event().wait()
