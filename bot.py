from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import date
import json
import os

# 🔴 CHANGE KARNA
API_ID = 30884966
API_HASH = "9cc40478343e0ef328f7a577b293ac57"
BOT_TOKEN = "8272441247:AAGLeR2KouANpOXB_AKNnZn6eM2EMG36K-o"
OWNER_ID = 8423209227

app = Client("auto_accept_bot",
             api_id=API_ID,
             api_hash=API_HASH,
             bot_token=BOT_TOKEN)

# Stats file
STATS_FILE = "stats.json"

def load_stats():
    if not os.path.exists(STATS_FILE):
        return {}
    with open(STATS_FILE, "r") as f:
        return json.load(f)

def save_stats(data):
    with open(STATS_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Active users set
users = set()


# ✅ Pending Request Auto Accept + Welcome Message
@app.on_chat_join_request()
async def approve_request(client, req):
    await client.approve_chat_join_request(req.chat.id, req.from_user.id)

    # --- Per-channel statistics ---
    stats = load_stats()
    chat_id = str(req.chat.id)
    today_str = str(date.today())
    month_str = today_str[:7]  # YYYY-MM

    if chat_id not in stats:
        stats[chat_id] = {"today": {}, "monthly": {}, "total": 0}

    stats[chat_id]["today"][today_str] = stats[chat_id]["today"].get(today_str, 0) + 1
    stats[chat_id]["monthly"][month_str] = stats[chat_id]["monthly"].get(month_str, 0) + 1
    stats[chat_id]["total"] += 1

    save_stats(stats)
    # --------------------------------

    users.add(req.from_user.id)

    await client.send_message(
        req.from_user.id, f"""Hello {req.from_user.first_name},

Your Request to Join {req.chat.title} has been Approved.

Send /start to know more.""")


# ✅ /start command with buttons
@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    users.add(message.from_user.id)

    buttons = InlineKeyboardMarkup([
        # Top button
        [
            InlineKeyboardButton("📢 Bot Updates Channel",
                                 url="https://t.me/AutoAccepter")
        ],
        # Middle buttons (left & right)
        [
            InlineKeyboardButton(
                "➕ Add To Group",
                url=
                "https://t.me/AutoAccepter121bot?startgroup=AdBots&admin=invite_users+manage_chat"
            ),
            InlineKeyboardButton(
                "➕ Add To Channel",
                url=
                "https://t.me/AutoAccepter121bot?startchannel=AdBots&admin=invite_users+manage_chat"
            )
        ],
        # Bottom button
        [InlineKeyboardButton("📊 Statistics", callback_data="stats")]
    ])

    await message.reply(
        "Add @AutoAccepter121bot To Your Channels To Accept Join Requests Automatically 😊",
        reply_markup=buttons)


# ✅ Callback for Statistics (per-channel) + Back button
@app.on_callback_query(filters.regex("stats"))
async def stats_cb(client, cb):
    stats = load_stats()
    chat_id = str(cb.message.chat.id)
    today_str = str(date.today())
    month_str = today_str[:7]

    if chat_id not in stats:
        await cb.message.edit_text("No data available for this channel.")
        return

    today_count = stats[chat_id]["today"].get(today_str, 0)
    month_count = stats[chat_id]["monthly"].get(month_str, 0)
    total_count = stats[chat_id]["total"]

    # InlineKeyboard with Back button
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="start_page")]
    ])

    await cb.message.edit_text(
        f"📊 **Channel Statistics**\n\n"
        f"✅ Today Accepted: {today_count}\n"
        f"📅 Monthly Accepted: {month_count}\n"
        f"📈 Total Accepted: {total_count}",
        reply_markup=buttons
    )


# ✅ Back button handler → show main start buttons
@app.on_callback_query(filters.regex("start_page"))
async def back_to_start(client, cb):
    buttons = InlineKeyboardMarkup([
        # Top button
        [
            InlineKeyboardButton("📢 Bot Updates Channel",
                                 url="https://t.me/AutoAccepter")
        ],
        # Middle buttons
        [
            InlineKeyboardButton(
                "➕ Add To Group",
                url=
                "https://t.me/AutoAccepter121bot?startgroup=AdBots&admin=invite_users+manage_chat"
            ),
            InlineKeyboardButton(
                "➕ Add To Channel",
                url=
                "https://t.me/AutoAccepter121bot?startchannel=AdBots&admin=invite_users+manage_chat"
            )
        ],
        # Bottom button
        [InlineKeyboardButton("📊 Statistics", callback_data="stats")]
    ])

    await cb.message.edit_text(
        "Add @AutoAccepter121bot To Your Channels To Accept Join Requests Automatically 😊",
        reply_markup=buttons
    )


# ✅ Owner command → total active users
@app.on_message(filters.command("users") & filters.user(OWNER_ID))
async def total_users(client, message):
    await message.reply(f"👥 Total Active Users: {len(users)}")


# ✅ Owner command → broadcast message to all users
@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast(client, message):
    if not message.reply_to_message:
        return await message.reply("Reply to a message to broadcast.")

    sent = 0
    for user in users:
        try:
            await message.reply_to_message.copy(user)
            sent += 1
        except:
            pass

    await message.reply(f"✅ Broadcast sent to {sent} users")


# ✅ Run the bot
app.run()
