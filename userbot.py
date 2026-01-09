from telethon import TelegramClient, events
import asyncio, random, os, uuid
from gtts import gTTS
from pydub import AudioSegment

# ---------- CONFIG ----------
api_id = 39472210
api_hash = "7f5b22842cd94f8e737455d427d5a816"
OWNER_ID = 7510461579

TEXT_DELAY = 1.2
VOICE_DELAY = 1.2
VOICE_COUNT = 10
# ----------------------------

client = TelegramClient("user_session", api_id, api_hash)

swipe_tasks = {}   # chat_id -> task
voice_tasks = {}   # chat_id -> task

# 👉 RAID / SWIPE TEXT (tum yahan edit kar sakte ho)
SWIPE_TEXTS = [
   "tmr rndy",
    "kya tbkc kali?",
    "reply cr rndky fast",
    "reply dena meh dar ra mdrchod",
    "scene kya chal raha haitry maa ka",
    "thoda try maa chod du",
    "bagg mt beti",
    "aaj mood try maa chodke mar dunga",
    "chal roke dikha tmr",
    "itna haklata q h bitch",
    "cya re bhn ke land",
    "i like your mom",
    "apni maa ka givway kab kr ra",
    "bagg mat rndiputra",
    "hakla tmkc"
]

# ---------- SWIPE ----------
@client.on(events.NewMessage(pattern=r'^/swipe\s+(\w+)$'))
async def cmd_swipe(event):
    if event.sender_id != OWNER_ID:
        return

    chat_id = event.chat_id
    if chat_id in swipe_tasks:
        await event.reply("Swipe already running.")
        return

    name = event.pattern_match.group(1).strip()

    reply_to = None
    if event.is_reply:
        r = await event.get_reply_message()
        reply_to = r.id

    async def swipe_loop():
        try:
            for _ in range(10):
                text = random.choice(SWIPE_TEXTS)
                msg = f"{name} {text}"
                await client.send_message(chat_id, msg, reply_to=reply_to)
                await asyncio.sleep(TEXT_DELAY)
        except asyncio.CancelledError:
            pass

    task = asyncio.create_task(swipe_loop())
    swipe_tasks[chat_id] = task

    await event.reply(f"✓ Swipe started for {name}")

# ---------- STOP SWIPE ----------
@client.on(events.NewMessage(pattern=r'^/stop$'))
async def cmd_stop(event):
    if event.sender_id != OWNER_ID:
        return

    chat_id = event.chat_id
    task = swipe_tasks.pop(chat_id, None)
    if task:
        task.cancel()
        await event.reply("✗ Swipe stopped.")

# ---------- TEXT → VOICE ----------
def text_to_voice(text: str) -> str:
    uid = uuid.uuid4().hex
    mp3 = f"/tmp/{uid}.mp3"
    ogg = f"/tmp/{uid}.ogg"

    gTTS(text=text, lang="en").save(mp3)
    AudioSegment.from_mp3(mp3).export(
        ogg, format="ogg", codec="libopus"
    )
    os.remove(mp3)
    return ogg

# ---------- VOICE LOOP ----------
async def voice_loop(chat_id, ogg_path):
    try:
        for _ in range(VOICE_COUNT):
            await client.send_file(chat_id, ogg_path, voice_note=True)
            await asyncio.sleep(VOICE_DELAY)
    except asyncio.CancelledError:
        pass
    finally:
        if os.path.exists(ogg_path):
            os.remove(ogg_path)

# ---------- /voice ----------
@client.on(events.NewMessage(pattern=r'^/voice\s+(.+)$'))
async def cmd_voice(event):
    if event.sender_id != OWNER_ID:
        return

    chat_id = event.chat_id
    if chat_id in voice_tasks:
        await event.reply("Voice already running.")
        return

    text = event.pattern_match.group(1).strip()
    ogg = text_to_voice(text)

    task = asyncio.create_task(voice_loop(chat_id, ogg))
    voice_tasks[chat_id] = task

    await event.reply("✓ Voice started (10x)")

# ---------- STOP VOICE ----------
@client.on(events.NewMessage(pattern=r'^/stopvoice$'))
async def cmd_stopvoice(event):
    if event.sender_id != OWNER_ID:
        return

    chat_id = event.chat_id
    task = voice_tasks.pop(chat_id, None)
    if task:
        task.cancel()
        await event.reply("✗ Voice stopped.")

# ---------- START ----------
client.start()
print("Userbot running (final build)...")
client.run_until_disconnected()
