import re
import asyncio
import time
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import FloodWait, ChatAdminRequired
from pyrogram.raw.functions.channels import GetParticipants
from pyrogram.raw.types import ChannelParticipantsAdmins
import logging

# --------- CONFIGURATION ---------
API_ID = "22243185"
API_HASH = "39d926a67155f59b722db787a23893ac"
BOT_TOKEN = "8020578503:AAFWeiecAUXOmzoOIzzTvnZ8BdcluskMSVk"

LOG_GROUP_ID = "-1002100433415"
OWNER_USERNAME = "silent_era"
SUPPORT_USERNAME = "frozenTools"

ABUSE_WORDS = [
    "madarchod", "bhenchodd", "lund", "chut", "gaand", "bsdk", "bahanchod",
    "ncert", "allen", "porn", "xxx", "sex", "NCERT", "XII", "page", "Ans",
    "meiotic", "divisions", "System.in", "Scanner", "void", "nextInt"
]

LINK_REGEX = re.compile(r"(https?://|t.me/|telegram.me/|www\.)", re.IGNORECASE)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Client(
    "GroupSecurityBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    parse_mode=enums.ParseMode.HTML
)

WELCOME_IMAGE_URL = "https://envs.sh/52H.jpg"
WELCOME_CAPTION = (
    "🤖 𝖦𝗋𝗈𝗎𝗉 𝖲𝖾𝖼𝗎𝗋𝗂𝗍𝗒 𝖱𝗈𝖻𝗈𝗍 🛡️\n\n"
    "𝖶𝖾𝗅𝖼𝗈𝗆𝖾 𝗍𝗈 𝖦𝗋𝗈𝗎𝗉𝖲𝖾𝖼𝗎𝗋𝗂𝗍𝗒𝖱𝗈𝖻𝗈𝗍, 𝗒𝗈𝗎𝗋 𝗏𝗂𝗀𝗂𝗅𝖺𝗇𝗍 𝗀𝗎𝖺𝗋𝖽𝗂𝖺𝗇..."
)

WELCOME_BUTTONS = InlineKeyboardMarkup([
    [InlineKeyboardButton(f"Owner @{OWNER_USERNAME}", url=f"https://t.me/{OWNER_USERNAME}")],
    [InlineKeyboardButton(f"Support @{SUPPORT_USERNAME}", url=f"https://t.me/{SUPPORT_USERNAME}")],
    [InlineKeyboardButton("➕ Add to Group", url="https://t.me/YourBotUsername?startgroup=true")]
])

PING_BUTTONS = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("Close", callback_data="close_ping"),
        InlineKeyboardButton("Add", url="https://t.me/YourBotUsername?startgroup=true"),
    ]
])

STATS_BUTTONS = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("Close", callback_data="close_stats"),
        InlineKeyboardButton("Add", url="https://t.me/YourBotUsername?startgroup=true"),
    ]
])

active_chats = set()
active_users = set()


@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    user = message.from_user
    active_users.add(user.id)
    await message.reply_photo(
        photo=WELCOME_IMAGE_URL,
        caption=WELCOME_CAPTION,
        reply_markup=WELCOME_BUTTONS
    )
    total_users = len(active_users)
    log_text = (
        f"🤖 Bot started by new user\n\n"
        f"Name: {user.mention}\n"
        f"Username: @{user.username or 'N/A'}\n"
        f"UserID: <code>{user.id}</code>\n"
        f"Total users: <b>{total_users}</b>"
    )
    try:
        await client.send_message(LOG_GROUP_ID, log_text)
    except Exception as e:
        logger.error(f"Error sending start log: {e}")


@bot.on_chat_member_updated()
async def member_update(client, chat_member_updated):
    if chat_member_updated.new_chat_member.user.is_self and chat_member_updated.old_chat_member.status == enums.ChatMemberStatus.LEFT:
        chat = chat_member_updated.chat
        active_chats.add(chat.id)
        log_text = (
            f"➕ Bot added in new group\n\n"
            f"Name: {chat.title}\n"
            f"Username: @{chat.username or 'N/A'}\n"
            f"Chat ID: <code>{chat.id}</code>"
        )
        try:
            await client.send_message(LOG_GROUP_ID, log_text)
        except Exception as e:
            logger.error(f"Error sending group add log: {e}")


@bot.on_message(filters.text | filters.document)
async def monitor_messages(client: Client, message: Message):
    try:
        member = await client.get_chat_member(message.chat.id, message.from_user.id)
        if member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            return
    except Exception:
        pass

    text = message.text or ""
    user_mention = message.from_user.mention

    if len(text) > 200:
        try:
            await message.delete()
            await message.reply_text(f"{user_mention} 200 characters msg isn't allowed.")
        except Exception:
            pass
        return

    if message.document:
        if message.document.mime_type == "application/pdf":
            try:
                await message.delete()
                await message.reply_text(f"{user_mention} PDF file isn't allowed.")
            except Exception:
                pass
            return

    if message.edit_date:
        try:
            await message.delete()
            await message.reply_text(f"{user_mention} Editing msg isn't allowed.")
        except Exception:
            pass
        return

    if LINK_REGEX.search(text):
        try:
            await message.delete()
            await message.reply_text(f"{user_mention} Links aren't allowed.")
        except Exception:
            pass
        return

    lower_text = text.lower()
    if any(word in lower_text for word in ABUSE_WORDS):
        try:
            await message.delete()
            await message.reply_text(f"{user_mention} Please avoid abusive words.")
        except Exception:
            pass
        return


@bot.on_edited_message(filters.text | filters.document)
async def handle_edited_message(client, message):
    try:
        await message.delete()
        await message.reply_text(f"{message.from_user.mention} Editing msg isn't allowed.")
    except Exception:
        pass


@bot.on_message(filters.new_chat_members)
async def welcome_new_members(client: Client, message: Message):
    for new_user in message.new_chat_members:
        if new_user.is_bot:
            continue

        try:
            user_info = await client.get_users(new_user.id)
            bio = user_info.bio or ""
            if LINK_REGEX.search(bio):
                await client.restrict_chat_member(
                    message.chat.id,
                    new_user.id,
                    permissions=enums.ChatPermissions(
                        can_send_messages=False,
                        can_send_media_messages=False,
                        can_send_other_messages=False,
                        can_add_web_page_previews=False,
                    )
                )
                await message.reply_text(f"{new_user.mention} Bio link isn't allowed. You are muted.")
        except Exception:
            pass


@bot.on_message(filters.command("broadcast") & filters.user(OWNER_USERNAME))
async def broadcast_handler(client: Client, message: Message):
    args = message.text.split(None, 1)
    if len(args) < 2:
        await message.reply_text("Usage: /broadcast <message>")
        return

    broadcast_text = args[1]
    success_count = 0
    fail_count = 0

    async for dialog in client.get_dialogs():
        chat = dialog.chat
        try:
            await client.send_message(chat.id, broadcast_text)
            success_count += 1
        except Exception:
            fail_count += 1

    await message.reply_text(f"Broadcast completed.\nSuccess: {success_count}\nFailed: {fail_count}")


@bot.on_message(filters.command("ping"))
async def ping_handler(client: Client, message: Message):
    start = time.time()
    rep = await message.reply_text("Pinging...")
    end = time.time()
    ms = int((end - start) * 1000)
    await rep.edit_text(f"🤖 **PONG**: `{ms}`ᴍs", reply_markup=PING_BUTTONS)


@bot.on_callback_query(filters.regex("close_"))
async def close_callback(client, callback_query):
    await callback_query.message.delete()
    await callback_query.answer()


@bot.on_message(filters.command("stats"))
async def stats_handler(client: Client, message: Message):
    total_groups = len(active_chats)
    total_users = len(active_users)

    text = (
        f"📊 <b>Bot Stats</b> 📊\n\n"
        f"Total groups where bot is active: <b>{total_groups}</b>\n"
        f"Total unique users interacted: <b>{total_users}</b>"
    )

    await message.reply_photo(
        photo=WELCOME_IMAGE_URL,
        caption=text,
        reply_markup=STATS_BUTTONS
    )


print("Bot is starting...")
bot.run()