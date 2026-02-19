import os
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import date
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import FloodWait
from pymongo import MongoClient

# ================== RENDER PORT TIMEOUT FIX ==================
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running on Render!")

def run_server():
    # Render automatically ek PORT variable assign karta hai
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheck)
    server.serve_forever()

# Ise ek alag thread mein chalayenge taaki bot ki speed par asar na pade
threading.Thread(target=run_server, daemon=True).start()

# ================== ENV VARIABLES ==================
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
MONGO_URL = os.getenv("MONGO_URL")

# ================== BOT CLIENT ==================
app = Client(
    "auto_request_accept_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ================== MONGODB ==================
mongo = MongoClient(MONGO_URL)
db = mongo["autoreqacceptbot"]

users_col = db.users          # /start users
stats_col = db.stats          # stats storage

# ================== INIT STATS ==================
today = date.today()

if not stats_col.find_one({"_id": "stats"}):
    stats_col.insert_one({
        "_id": "stats",
        "today": 0,
        "month": 0,
        "total": 0,
        "date": today.isoformat(),
        "month_no": today.month
    })

# ================== AUTO ACCEPT JOIN REQUEST ==================
@app.on_chat_join_request()
async def approve_request(client, req):
    try:
        # Request accept karne ki koshish karega
        await client.approve_chat_join_request(req.chat.id, req.from_user.id)
    except Exception:
        # Agar user pehle se join hai ya request cancel ho gayi, toh error ignore karega aur wapas jayega
        return

    stats = stats_col.find_one({"_id": "stats"})
    today = date.today()

    # reset daily
    if stats["date"] != today.isoformat():
        stats_col.update_one(
            {"_id": "stats"},
            {"$set": {"today": 0, "date": today.isoformat()}}
        )

    # reset monthly
    if stats["month_no"] != today.month:
        stats_col.update_one(
            {"_id": "stats"},
            {"$set": {"month": 0, "month_no": today.month}}
        )

    stats_col.update_one(
        {"_id": "stats"},
        {"$inc": {"today": 1, "month": 1, "total": 1}}
    )

    try:
        # Naya Bold Message + Button
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("ADULT 18+ ONLY", url="https://tezlnk.in/")]
        ])
        
        await client.send_message(
            req.from_user.id,
            f"**Hello {req.from_user.first_name},**\n\n"
            f"**Your Request To Join {req.chat.title} Has Been Approved Successful Using @AutoAccepter121bot.**\n\n"
            f"**Send /start To Use This Bot.**",
            reply_markup=buttons
        )
    except:
        pass

# ================== /START ==================
@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    user_id = message.from_user.id

    # save user permanently
    users_col.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id}},
        upsert=True
    )

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Bot Updates", url="https://t.me/+Q6XLvkj1xTQyOWRl")],
        [
            InlineKeyboardButton(
                "➕Add To Group",
                url="https://t.me/AutoAccepter121bot?startgroup=true&admin=invite_users+manage_chat"
            ),
            InlineKeyboardButton(
                "➕Add To Channel",
                url="https://t.me/AutoAccepter121bot?startchannel=true&admin=invite_users+manage_chat"
            )
        ],
        [InlineKeyboardButton("📊 Statistics", callback_data="stats")]
    ])

    await message.reply(
        "Add **@autoaccepter121bot** to your Channel/Group to auto accept join requests 😊",
        reply_markup=buttons
    )

# ================== STATS BUTTON ==================
@app.on_callback_query(filters.regex("^stats$"))
async def stats_cb(client, cb):
    stats = stats_col.find_one({"_id": "stats"})

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅ Back", callback_data="back")]
    ])

    await cb.message.edit_text(
        f"📊 **Statistics**\n\n"
        f"Today Accepted: `{stats['today']}`\n"
        f"Monthly Accepted: `{stats['month']}`\n"
        f"Total Accepted: `{stats['total']}`",
        reply_markup=buttons
    )

# ================== BACK BUTTON ==================
@app.on_callback_query(filters.regex("^back$"))
async def back_cb(client, cb):
    await start_cmd(client, cb.message)

# ================== /USERS (OWNER ONLY) ==================
@app.on_message(filters.command("users") & filters.user(OWNER_ID))
async def users_cmd(client, message):
    total = users_col.count_documents({})
    await message.reply(f"👥 Total Users (Started Bot): `{total}`")

# ================== /BROADCAST (OWNER ONLY - OPTIMIZED) ==================
@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_cmd(client, message):
    if not message.reply_to_message:
        return await message.reply("❌ Reply to a message to broadcast")

    await message.reply("⏳ **Broadcast Started in Background!**\nBot will continue accepting requests normally.")

    async def run_broadcast():
        sent = 0
        removed = 0
        failed = 0

        for user in users_col.find():
            user_id = user["user_id"]
            try:
                await message.reply_to_message.copy(user_id)
                sent += 1
            except FloodWait as e:
                # Anti-ban logic
                await asyncio.sleep(e.value + 1)
                try:
                    await message.reply_to_message.copy(user_id)
                    sent += 1
                except:
                    failed += 1
            except Exception:
                # Agar blocked/deleted hai
                users_col.delete_one({"user_id": user_id})
                removed += 1

            # 20 msg/sec speed limiter
            if (sent + removed + failed) % 20 == 0:
                await asyncio.sleep(1)

        # Broadcast report to Owner
        await client.send_message(
            OWNER_ID,
            f"✅ **Broadcast Completed**\n\n"
            f"🟢 Sent: `{sent}`\n"
            f"🔴 Removed (Blocked/Deleted): `{removed}`\n"
            f"🟡 Failed: `{failed}`"
        )

    # Ise background thread/task mein daal diya taaki bot freeze na ho
    asyncio.create_task(run_broadcast())

# ================== RUN ==================
print("Starting bot...")
app.run()
