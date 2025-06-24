from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import re

API_ID = "28588693"     # ← replace with your API ID
API_HASH = "fac94f1f1aa4aa395280a670ddf9c0f2"   # ← replace with your API hash
BOT_TOKEN = "7867961929:AAE2TMkj5eSQQvR13_P3D5KXTQs3F_tksrc" # ← replace with your Bot token

app = Client("tttbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

games = {}  # {chat_id: game_data}
invites = {}  # {inviter_id: invited_user_id}

def create_board(board):
    keyboard = []
    for i in range(3):
        row = []
        for j in range(3):
            val = board[i][j]
            text = val if val else "⬜"
            row.append(InlineKeyboardButton(text, callback_data=f"move|{i}|{j}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def check_winner(board):
    for row in board:
        if row[0] and row.count(row[0]) == 3:
            return row[0]
    for col in range(3):
        if board[0][col] and all(board[row][col] == board[0][col] for row in range(3)):
            return board[0][col]
    if board[0][0] and all(board[i][i] == board[0][0] for i in range(3)):
        return board[0][0]
    if board[0][2] and all(board[i][2 - i] == board[0][2] for i in range(3)):
        return board[0][2]
    return None

def board_full(board):
    return all(cell for row in board for cell in row)

@app.on_message(filters.command("start"))
async def start(_, m: Message):
    await m.reply("Welcome to Tic Tac Toe Bot!\nUse /newgame or /invite @user in a group to start playing.")

@app.on_message(filters.command("newgame") & filters.group)
async def new_game(_, m: Message):
    chat_id = m.chat.id
    if chat_id in games:
        await m.reply("⚠️ A game is already active in this group.")
        return
    board = [[None]*3 for _ in range(3)]
    games[chat_id] = {
        "board": board,
        "players": [m.from_user.id, None],
        "turn": 0,
        "message_id": None,
        "symbols": ["❌", "⭕"]
    }
    msg = await m.reply(f"Tic Tac Toe Game Started!\n{m.from_user.mention} is ❌\nWaiting for second player...",
        reply_markup=create_board(board))
    games[chat_id]["message_id"] = msg.message_id

@app.on_message(filters.command("endgame") & filters.group)
async def end_game(_, m: Message):
    if m.chat.id in games:
        del games[m.chat.id]
        await m.reply("🛑 Game ended by admin.")
    else:
        await m.reply("❌ No active game to end.")

@app.on_message(filters.command("invite") & filters.group)
async def invite(_, m: Message):
    if len(m.command) < 2 or not re.match(r"^@[\w\d_]+$", m.command[1]):
        await m.reply("Usage: /invite @username")
        return

    if m.chat.id in games:
        await m.reply("⚠️ A game is already running in this group.")
        return

    target = m.command[1].lstrip("@")
    invites[m.from_user.id] = target
    await m.reply(f"🎯 Invitation sent to @{target}. Ask them to type /accept.")

@app.on_message(filters.command("accept") & filters.group)
async def accept_invite(_, m: Message):
    user = m.from_user
    for inviter_id, invited_username in invites.items():
        if invited_username.lower() == user.username.lower():
            board = [[None]*3 for _ in range(3)]
            games[m.chat.id] = {
                "board": board,
                "players": [inviter_id, user.id],
                "turn": 0,
                "message_id": None,
                "symbols": ["❌", "⭕"]
            }
            del invites[inviter_id]
            msg = await m.reply(
                f"✅ Match started between [User](tg://user?id={inviter_id}) and {user.mention}!",
                reply_markup=create_board(board))
            games[m.chat.id]["message_id"] = msg.message_id
            return
    await m.reply("❌ You don't have any active invite.")

@app.on_callback_query()
async def handle_move(_, q: CallbackQuery):
    chat_id = q.message.chat.id
    user_id = q.from_user.id

    if chat_id not in games:
        await q.answer("No active game here.", show_alert=True)
        return

    game = games[chat_id]
    if user_id not in game["players"]:
        await q.answer("You're not in this game.", show_alert=True)
        return

    turn = game["turn"]
    if user_id != game["players"][turn]:
        await q.answer("Not your turn!", show_alert=True)
        return

    _, i, j = q.data.split("|")
    i, j = int(i), int(j)
    if game["board"][i][j]:
        await q.answer("Already taken!", show_alert=True)
        return

    symbol = game["symbols"][turn]
    game["board"][i][j] = symbol

    winner = check_winner(game["board"])
    if winner:
        await q.message.edit_text(
            f"{symbol} wins! 🎉",
            reply_markup=create_board(game["board"]))
        del games[chat_id]
    elif board_full(game["board"]):
        await q.message.edit_text("🤝 It's a draw!", reply_markup=create_board(game["board"]))
        del games[chat_id]
    else:
        game["turn"] = 1 - turn
        await q.message.edit_text(
            f"{game['symbols'][game['turn']]}'s turn",
            reply_markup=create_board(game["board"]))

app.run()