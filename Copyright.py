import re
import datetime
import time
import asyncio

from pyrogram import Client, filters, errors
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus, ParseMode
from pymongo import MongoClient

# --- CONFIGURATION ---
BOT_TOKEN = "7952459394:AAEO3O1L053GlA8qtCi6_H7BxYOZ7t4QhOY"
API_ID = "22243185"
API_HASH = "39d926a67155f59b722db787a23893ac"
MONGO_URL = "mongodb+srv://manoranjanhor43:somuxd@manoranjan.wsglmdq.mongodb.net/?retryWrites=true&w=majority&appName=Manoranjan"
LOGS_GROUP = "-1002100433415"  # Your logs group's chat ID (must be integer, starts with -100 for supergroups)
ADMINS = "6908972904"  # List of admin user IDs allowed to broadcast etc.

# Connect to MongoDB
mongo = MongoClient(MONGO_URL)
db = mongo.bot
stats = db.stats

# Regex patterns
link_pattern = re.compile(r"https?://|www\.|t\.me/|telegram\.me")
abuse_words = [
    "madarchod", "bhenchodd", "lund", "chut", "gaand", "bsdk", "bahanchod",
    "ncert", "allen", "porn", "xxx", "sex", "NCERT", "XII", "page", "Ans",
    "meiotic", "divisions", "System.in", "Scanner", "void", "nextInt"
]

# --- CLIENT SETUP ---
class GroupSecurityBot(Client):
    def __init__(self):
        super().__init__(
            "groupSecurityBot",
            bot_token=BOT_TOKEN,
            api_id=API_ID,
            api_hash=API_HASH,
            parse_mode=ParseMode.HTML
        )

    async def start(self):
        await super().start()

        me = await self.get_me()
        self.id = me.id
        self.name = me.first_name + " " + (me.last_name or "")
        self.username = me.username
        self.mention = me.mention

        # Send "Bot started" message to logs group
        try:
            await self.send_message(
                chat_id=LOGS_GROUP,
                text=(
                    f"<b>✅ Bot Started</b>\n\n"
                    f"<b>Name:</b> {self.name}\n"
                    f"<b>Username:</b> @{self.username}\n"
                    f"<b>ID:</b> <code>{self.id}</code>\n"
                    f"<b>Time:</b> {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
                )
            )
        except (errors.ChannelInvalid, errors.PeerIdInvalid):
            print("Error: Bot can't access the logs group/channel. Add the bot to the group and make it admin.")
            await self.stop()
            exit()
        except Exception as e:
            print(f"Error: Failed to send start log message. Reason: {type(e).__name__}")
            await self.stop()
            exit()

        # Check if bot is admin in logs group
        member = await self.get_chat_member(LOGS_GROUP, self.id)
        if member.status != ChatMemberStatus.ADMINISTRATOR:
            print("Error: Bot is not admin in logs group. Please promote it as admin.")
            await self.stop()
            exit()

        print(f"Bot started successfully as {self.name}")

# Initialize bot
bot = GroupSecurityBot()

# --- HANDLERS ---

@bot.on_message(filters.private & filters.command("start"))
async def start(client, message: Message):
    user = message.from_user
    stats.update_one({"_id": "users"}, {"$addToSet": {"list": user.id}}, upsert=True)
    count = len(stats.find_one({"_id": "users"})["list"])
    await client.send_photo(
        chat_id=message.chat.id,
        photo="https://envs.sh/52H.jpg",
        caption="""🤖 Group Security Robot 🛡️

Welcome to GroupSecurityRobot...

Owner @moh_maya_official
Support @frozenTools""",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("➕ Add to Group", url="https://t.me/YourBotUsername?startgroup=true")]]
        )
    )
    await client.send_message(LOGS_GROUP, f"**Bot started by new user**\nName: {user.first_name}\nUsername: @{user.username}\nID: `{user.id}`\nTotal users: {count}")

@bot.on_message(filters.new_chat_members)
async def new_group(client, message: Message):
    for user in message.new_chat_members:
        if user.id == (await client.get_me()).id:
            stats.update_one({"_id": "groups"}, {"$addToSet": {"list": message.chat.id}}, upsert=True)
            group_link = f"@{message.chat.username}" if message.chat.username else "No username"
            await client.send_message(
                LOGS_GROUP,
                f"**Bot added in new group**\nName: {message.chat.title}\nGroup ID: `{message.chat.id}`\nUsername: {group_link}"
            )

@bot.on_message(filters.group, group=1)
async def filter_messages(client, message: Message):
    text = message.text or ""
    if len(text) > 200:
        await message.delete()
    elif message.document and message.document.mime_type == "application/pdf":
        await message.delete()
    elif message.edit_date:
        await message.delete()
    elif link_pattern.search(text.lower()):
        await message.delete()
    elif any(word.lower() in text.lower() for word in abuse_words):
        await message.delete()

@bot.on_message(filters.group & filters.new_chat_members)
async def check_bio(client, message: Message):
    for member in message.new_chat_members:
        if member.username:
            user = await client.get_users(member.id)
            if user.bio and link_pattern.search(user.bio):
                try:
                    await client.restrict_chat_member(
                        message.chat.id,
                        member.id,
                        permissions={}
                    )
                    await message.reply_text(f"{member.mention} muted for link in bio.")
                except Exception:
                    pass

@bot.on_message(filters.command("ping") & filters.group)
async def ping(client, message: Message):
    start = time.time()
    m = await message.reply_photo("https://envs.sh/r-v.jpg", caption="Pinging...")
    end = time.time()
    await m.edit_caption(
        f"Pong: `{round((end - start) * 1000)} ms`",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ Add Me", url="https://t.me/YourBotUsername?startgroup=true"),
                InlineKeyboardButton("❌ Close", callback_data="close")
            ]
        ])
    )

@bot.on_callback_query(filters.regex("close"))
async def close_btn(client, callback_query):
    await callback_query.message.delete()

@bot.on_message(filters.command("broadcast") & filters.user(ADMINS))
async def broadcast(client, message: Message):
    if len(message.command) < 2:
        return await message.reply("Usage: /broadcast your message")
    text = message.text.split(None, 1)[1]
    users = stats.find_one({"_id": "users"})["list"]
    for uid in users:
        try:
            await client.send_message(uid, text)
        except Exception:
            pass
    await message.reply("Broadcast sent.")

# --- RUN BOT ---
async def main():
    await bot.start()
    print("Bot is running...")
    await bot.idle()

asyncio.run(main())