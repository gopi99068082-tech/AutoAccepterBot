from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import date

# 🔴 CHANGE KARNA
API_ID = 30884966
API_HASH = "9cc40478343e0ef328f7a577b293ac57"
BOT_TOKEN = "8272441247:AAGLeR2KouANpOXB_AKNnZn6eM2EMG36K-o"
OWNER_ID = 8423209227

app = Client("auto_accept_bot",
             api_id=API_ID,
             api_hash=API_HASH,
             bot_token=BOT_TOKEN)

# Stats dictionary
stats = {
    "today": 0,
    "month": 0,
    "total": 0,
    "date": date.today(),
    "month_no": date.today().month
}

# Active users set
users = set()


# ✅ Pending Request Auto Accept + Welcome Message
@app.on_chat_join_request()
async def approve_request(client, req):
    global stats
    await client.approve_chat_join_request(req.chat.id, req.from_user.id)

    today = date.today()
    if stats["date"] != today:
        stats["today"] = 0
        stats["date"] = today
    if stats["month_no"] != today.month:
        stats["month"] = 0
        stats["month_no"] = today.month

    stats["today"] += 1
    stats["month"] += 1
    stats["total"] += 1

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


# ✅ Callback for Statistics
@app.on_callback_query(filters.regex("stats"))
async def stats_cb(client, cb):
    await cb.message.edit_text(f"""📊 Statistics

Today Accepted: {stats['today']}
Monthly Accepted: {stats['month']}
Total Accepted: {stats['total']}""")


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
