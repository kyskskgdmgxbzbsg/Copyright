from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
import re
import datetime
import time
import asyncio
from pyrogram import idle  # ये import जरूर करें

BOT_TOKEN = "7952459394:AAEO3O1L053GlA8qtCi6_H7BxYOZ7t4QhOY"
API_ID = "22243185"
API_HASH = "39d926a67155f59b722db787a23893ac"
MONGO_URL = "mongodb+srv://manoranjanhor43:somuxd@manoranjan.wsglmdq.mongodb.net/?retryWrites=true&w=majority&appName=Manoranjan"
# सबसे बेहतर: username वाला लॉग ग्रुप इस्तेमाल करें (अगर उपलब्ध हो)
LOGS_GROUP = "-1002100433415"  # या -1001234567890 अगर ID ही इस्तेमाल करना है
ADMINS = "6908972904"

client = Client("groupSecurityBot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)
mongo = MongoClient(MONGO_URL)
db = mongo.bot
stats = db.stats

abuse_words = ["madarchod", "bhenchodd", "lund", "chut", "gaand", "bsdk", "bahanchod", "ncert", "allen", "porn", "xxx", "sex", "NCERT", "XII", "page", "Ans", "meiotic", "divisions", "System.in", "Scanner", "void", "nextInt"]
link_pattern = re.compile(r"https?://|www\.|t\.me/|telegram\.me")

@client.on_message(filters.private & filters.command("start"))
async def start(client, message):
    user = message.from_user
    stats.update_one({"_id": "users"}, {"$addToSet": {"list": user.id}}, upsert=True)
    count = len(stats.find_one({"_id": "users"})["list"])
    await client.send_photo(
        chat_id=message.chat.id,
        photo="https://envs.sh/52H.jpg",
        caption="""🤖 𝖦𝗋𝗈𝗎𝗉 𝖲𝖾𝖼𝗎𝗋𝗂𝗍𝗒 𝖱𝗈𝖻𝗈𝗍 🛡️

𝖶𝖾𝗅𝖼𝗈𝗆𝖾 𝗍𝗈 𝖦𝗋𝗈𝗎𝗉𝖲𝖾𝖼𝗎𝗋𝗂𝗍𝗒𝖱𝗈𝖻𝗈𝗍...

Owner @moh_maya_official
Support @frozenTools""",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("➕ Add to Group", url="https://t.me/YourBotUsername?startgroup=true")]]
        )
    )
    await client.send_message(LOGS_GROUP, f"**Bot started by new user**\nName: {user.first_name}\nUsername: @{user.username}\nID: `{user.id}`\nTotal users: {count}")

@client.on_message(filters.new_chat_members)
async def new_group(client, message):
    for user in message.new_chat_members:
        if user.id == (await client.get_me()).id:
            stats.update_one({"_id": "groups"}, {"$addToSet": {"list": message.chat.id}}, upsert=True)
            group_link = f"@{message.chat.username}" if message.chat.username else "No username"
            await client.send_message(LOGS_GROUP, f"**Bot added in new group**\nName: {message.chat.title}\nGroup ID: `{message.chat.id}`\nUsername: {group_link}")

@client.on_message(filters.group, group=1)
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

@client.on_message(filters.group & filters.new_chat_members)
async def check_bio(client, message):
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
                except:
                    pass

@client.on_message(filters.command("ping") & filters.group)
async def ping(client, message):
    start = time.time()
    m = await message.reply_photo("https://envs.sh/r-v.jpg", caption="Pinging...")
    end = time.time()
    await m.edit_caption(
        f"Pong: `{round((end-start)*1000)} ms`",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Me", url="https://t.me/YourBotUsername?startgroup=true"),
             InlineKeyboardButton("❌ Close", callback_data="close")]
        ])
    )

@client.on_callback_query(filters.regex("close"))
async def close_btn(client, callback_query):
    await callback_query.message.delete()

@client.on_message(filters.command("broadcast") & filters.user(ADMINS))
async def broadcast(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: /broadcast your message")
    text = message.text.split(None, 1)[1]
    users = stats.find_one({"_id": "users"})["list"]
    for uid in users:
        try:
            await client.send_message(uid, text)
        except:
            pass
    await message.reply("Broadcast sent.")

async def send_start_log():
    bot = await client.get_me()
    now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    await client.send_message(
        chat_id=LOGS_GROUP,
        text=f"✅ **Bot Started**\n\nName: `{bot.first_name}`\nUsername: @{bot.username}\nTime: `{now}`"
    )

async def main():
    await client.start()
    await send_start_log()
    print("Bot is running...")
    await idle()

if __name__ == "__main__":
    asyncio.run(main())