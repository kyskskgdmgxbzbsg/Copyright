import re
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import FloodWait, ChatAdminRequired
from pyrogram.raw.functions.channels import GetParticipants
from pyrogram.raw.types import ChannelParticipantsAdmins
import logging

# --------- CONFIGURATION ---------
API_ID = "22243185"               # आपका api_id
API_HASH = "39d926a67155f59b722db787a23893ac"     # आपका api_hash
BOT_TOKEN = "8020578503:AAFWeiecAUXOmzoOIzzTvnZ8BdcluskMSVk"   # आपका bot_token

LOG_GROUP_ID = "-1002100433415"  # आपका logs group का chat id (negative for supergroups)
OWNER_USERNAME = "silent_era"
SUPPORT_USERNAME = "frozenTools"

# Abuse words list
ABUSE_WORDS = [
    "madarchod", "bhenchodd", "lund", "chut", "gaand", "bsdk", "bahanchod",
    "ncert", "allen", "porn", "xxx", "sex", "NCERT", "XII", "page", "Ans",
    "meiotic", "divisions", "System.in", "Scanner", "void", "nextInt"
]

# Regex for detecting links in messages and bio
LINK_REGEX = re.compile(r"(https?://|t.me/|telegram.me/|www\.)", re.IGNORECASE)

# ----------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Client(
    "GroupSecurityBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    parse_mode=enums.ParseMode.HTML
)

# ---- Welcome image caption and buttons ----
WELCOME_IMAGE_URL = "https://envs.sh/52H.jpg"
WELCOME_CAPTION = (
    "🤖 𝖦𝗋𝗈𝗎𝗉 𝖲𝖾𝖼𝗎𝗋𝗂𝗍𝗒 𝖱𝗈𝖻𝗈𝗍 🛡️\n\n"
    "𝖶𝖾𝗅𝖼𝗈𝗆𝖾 𝗍𝗈 𝖦𝗋𝗈𝗎𝗉𝖲𝖾𝖼𝗎𝗋𝗂𝗍𝗒𝖱𝗈𝖻𝗈𝗍, 𝗒𝗈𝗎𝗋 𝗏𝗂𝗀𝗂𝗅𝖺𝗇𝗍 𝗀𝗎𝖺𝗋𝖽𝗂𝖺𝗇 𝗂𝗇 𝗍𝗁𝗂𝗌 𝖳𝖾𝗅𝖾𝗀𝗋𝖺𝗆 𝗌𝗉𝖺𝖼𝖾! 𝖮𝗎𝗋 𝗆𝗂𝗌𝗌𝗂𝗈𝗇 𝗂𝗌 𝗍𝗈 𝖾𝗇𝗌𝗎𝗋𝖾 𝖺 𝗌𝖾𝖼𝗎𝗋𝖾 𝖺𝗇𝖽 𝗉𝗅𝖾𝖺𝗌𝖺𝗇𝗍 𝖾𝗇𝗏𝗂𝗋𝗈𝗇𝗆𝖾𝗇𝗍 𝖿𝗈𝗋 𝖾𝗏𝖾𝗋𝗒𝗈𝗇𝖾.\n\n"
    "𝖥𝗋𝗈𝗆 𝖼𝗈𝗉𝗒𝗋𝗂𝗀𝗁𝗍 𝗉𝗋𝗈𝗍𝖾𝖼𝗍𝗂𝗈𝗇 𝗍𝗈 𝗆𝖺𝗂𝗇𝗍𝖺𝗂𝗇𝗂𝗇𝗀 𝖽𝖾𝖼𝗈𝗋𝗎𝗆, 𝗐𝖾'𝗏𝖾 𝗀𝗈𝗍 𝗂𝗍 𝖼𝗈𝗏𝖾𝗋𝖾𝖽. 𝖥𝖾𝖾𝗅 𝖿𝗋𝖾𝖾 𝗍𝗈 𝗋𝖾𝗉𝗈𝗋𝗍 𝖺𝗇𝗒 𝖼𝗈𝗇𝖼𝖾𝗋𝗇𝗌, 𝖺𝗇𝖽 𝗅𝖾𝗍'𝗌 𝗐𝗈𝗋𝗄 𝗍𝗈𝗀𝖾𝗍𝗁𝖾𝗋 𝗍𝗈 𝗆𝖺𝗄𝖾 𝗍𝗁𝗂𝗌 𝖼𝗈𝗆𝗆𝗎𝗇𝗂𝗍𝗒 𝗍𝗁𝗋𝗂𝗏𝖾! 🤝🔐"
)

WELCOME_BUTTONS = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(f"Owner @{OWNER_USERNAME}", url=f"https://t.me/{OWNER_USERNAME}")],
        [InlineKeyboardButton(f"Support @{SUPPORT_USERNAME}", url=f"https://t.me/{SUPPORT_USERNAME}")],
        [InlineKeyboardButton("➕ Add to Group", url="https://t.me/YourBotUsername?startgroup=true")]
    ]
)

PING_IMAGE_URL = "https://envs.sh/r-v.jpg"
PING_BUTTONS = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("Close", callback_data="close_ping"),
            InlineKeyboardButton("Add", url="https://t.me/YourBotUsername?startgroup=true"),
        ]
    ]
)

STATS_BUTTONS = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("Close", callback_data="close_stats"),
            InlineKeyboardButton("Add", url="https://t.me/YourBotUsername?startgroup=true"),
        ]
    ]
)

# Store total users and groups dynamically
# For demo, we'll track in memory, but ideally store in DB
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

    # Log bot started by user to LOG_GROUP_ID
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
    # When bot is added to new group
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


@bot.on_message(filters.text | filters.document | filters.edited)
async def monitor_messages(client: Client, message: Message):
    # Ignore messages from admins or bots
    try:
        member = await client.get_chat_member(message.chat.id, message.from_user.id)
        if member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            return
    except Exception:
        # If failed to get member status, proceed anyway
        pass

    text = message.text or ""
    user_mention = message.from_user.mention

    # 1. Delete messages longer than 200 characters
    if len(text) > 200:
        try:
            await message.delete()
            await message.reply_text(f"{user_mention} 200 characters msg isn't allowed.")
        except Exception:
            pass
        return

    # 2. Remove PDFs
    if message.document:
        if message.document.mime_type == "application/pdf":
            try:
                await message.delete()
                await message.reply_text(f"{user_mention} PDF file isn't allowed.")
            except Exception:
                pass
            return

    # 3. Delete edited messages and reply
    if message.edit_date:
        try:
            await message.delete()
            await message.reply_text(f"{user_mention} Editing msg isn't allowed.")
        except Exception:
            pass
        return

    # 4. Remove messages containing links
    if LINK_REGEX.search(text):
        try:
            await message.delete()
            await message.reply_text(f"{user_mention} Links aren't allowed.")
        except Exception:
            pass
        return

    # 6. Remove messages with abusive words
    lower_text = text.lower()
    if any(word in lower_text for word in ABUSE_WORDS):
        try:
            await message.delete()
            await message.reply_text(f"{user_mention} Please avoid abusive words.")
        except Exception:
            pass
        return


@bot.on_message(filters.new_chat_members)
async def welcome_new_members(client: Client, message: Message):
    # Check bio for new members, mute if bio contains link
    for new_user in message.new_chat_members:
        if new_user.is_bot:
            continue

        try:
            user_info = await client.get_users(new_user.id)
            bio = user_info.bio or ""
            if LINK_REGEX.search(bio):
                # Restrict user in chat (mute)
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


# Broadcast command (admin only)
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


# Ping command with image and inline buttons
@bot.on_message(filters.command("ping"))
async def ping_handler(client: Client, message: Message):
    await message.reply_photo(
        photo=PING_IMAGE_URL,
        caption="Pong! Bot is alive and responsive.",
        reply_markup=PING_BUTTONS
    )


# Close callback queries for ping and stats
@bot.on_callback_query(filters.regex("close_"))
async def close_callback(client, callback_query):
    await callback_query.message.delete()
    await callback_query.answer()


# Stats command showing total groups and users with buttons
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


# Run bot
print("Bot is starting...")
bot.run()