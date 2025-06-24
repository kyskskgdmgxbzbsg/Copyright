from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import re

API_ID = "28588693"  # Replace with your API ID
API_HASH = "fac94f1f1aa4aa395280a670ddf9c0f2"
BOT_TOKEN = "7867961929:AAE2TMkj5eSQQvR13_P3D5KXTQs3F_tksrc"

app = Client("multi_game_ttt", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

games = {}
invites = {}

WIN_STICKER = "CAACAgUAAxkBAAEHUt5lkoDqj8ZT8KwGxH4AJT9KDgvzOQACVQoAAhZCwFYbnk5Pg9xvwzUE"
DRAW_STICKER = "CAACAgUAAxkBAAEHUt9lkoEGMJWUzBe6W70oQVG7w0KfZQACVgoAAhZCwFYodfy74Xq8uTUE"

def create_board(board, game_id):
    keyboard = []
    for i in range(3):
        row = []
        for j in range(3):
            val = board[i][j]
            text = val if val else "⬜"
            row.append(InlineKeyboardButton(text, callback_data=f"{game_id}|{i}|{j}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def check_winner(board):
    for row in board:
        if row[0] and row.count(row[0]) == 3:
            return row[0]
    for col in range(3):
        if board[0][col] and all(board[r][col] == board[0][col] for r in range(3)):
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
    await m.reply("🎮 Welcome to Multi-Game Tic Tac Toe Bot!\nCommands:\n/newgame\n/invite (reply or @username)\n/accept\n/endgame")

@app.on_message(filters.command("newgame") & filters.group)
async def new_game(_, m: Message):
    chat_id = m.chat.id
    user_id = m.from_user.id
    game_id = f"{user_id}:{m.message_id}"

    board = [[None]*3 for _ in range(3)]
    if chat_id not in games:
        games[chat_id] = {}

    games[chat_id][game_id] = {
        "board": board,
        "players": [user_id, None],
        "turn": 0,
        "symbols": ["❌", "⭕"]
    }

    msg = await m.reply(
        f"New game started!\n{m.from_user.mention} is ❌\nWaiting for second player...",
        reply_markup=create_board(board, game_id)
    )

@app.on_message(filters.command("invite") & filters.group)
async def invite(_, m: Message):
    chat_id = m.chat.id
    inviter_id = m.from_user.id

    if m.reply_to_message:
        invited_user = m.reply_to_message.from_user
    elif len(m.command) >= 2 and re.match(r"^@[\w\d_]+$", m.command[1]):
        username = m.command[1].lstrip("@")
        try:
            invited_user = await app.get_users(username)
        except:
            return await m.reply("❌ Invalid username.")
    else:
        return await m.reply("⚠️ Use /invite by replying to a user or providing a valid @username.")

    if chat_id not in invites:
        invites[chat_id] = {}
    invites[chat_id][inviter_id] = invited_user.id
    await m.reply(f"📨 Invite sent to {invited_user.mention}. They can /accept.")

@app.on_message(filters.command("accept") & filters.group)
async def accept(_, m: Message):
    user = m.from_user
    chat_id = m.chat.id

    if chat_id not in invites:
        return await m.reply("No invites found.")

    for inviter_id, invited_id in list(invites[chat_id].items()):
        if invited_id == user.id:
            game_id = f"{inviter_id}:{user.id}"
            board = [[None]*3 for _ in range(3)]
            if chat_id not in games:
                games[chat_id] = {}
            games[chat_id][game_id] = {
                "board": board,
                "players": [inviter_id, user.id],
                "turn": 0,
                "symbols": ["❌", "⭕"]
            }
            del invites[chat_id][inviter_id]
            msg = await m.reply(
                f"✅ Game started between [Player1](tg://user?id={inviter_id}) and {user.mention}!",
                reply_markup=create_board(board, game_id)
            )
            return
    await m.reply("❌ You were not invited.")

@app.on_message(filters.command("endgame") & filters.group)
async def endgame(_, m: Message):
    chat_id = m.chat.id
    user_id = m.from_user.id
    if chat_id not in games:
        return await m.reply("No active games.")

    ended = False
    for gid in list(games[chat_id].keys()):
        if user_id in games[chat_id][gid]["players"]:
            del games[chat_id][gid]
            ended = True

    if ended:
        await m.reply("🛑 Your game(s) ended.")
    else:
        await m.reply("❌ You're not in any game.")

@app.on_callback_query()
async def on_button(_, q: CallbackQuery):
    chat_id = q.message.chat.id
    user_id = q.from_user.id

    try:
        game_id, i, j = q.data.split("|")
        i, j = int(i), int(j)
    except:
        return await q.answer("Invalid!", show_alert=True)

    if chat_id not in games or game_id not in games[chat_id]:
        return await q.answer("Game not found.", show_alert=True)

    game = games[chat_id][game_id]
    if user_id not in game["players"]:
        return await q.answer("You're not a player!", show_alert=True)

    turn = game["turn"]
    if user_id != game["players"][turn]:
        return await q.answer("⏳ Not your turn!", show_alert=True)

    if game["board"][i][j]:
        return await q.answer("❌ Already taken!", show_alert=True)

    symbol = game["symbols"][turn]
    game["board"][i][j] = symbol

    winner = check_winner(game["board"])
    if winner:
        winner_user_id = game["players"][turn]
        await q.message.edit_text(f"{symbol} wins! 🏆", reply_markup=create_board(game["board"], game_id))
        await app.send_message(chat_id, f"🏆 Congratulations [Player](tg://user?id={winner_user_id})!")
        await app.send_sticker(chat_id, WIN_STICKER)
        del games[chat_id][game_id]
    elif board_full(game["board"]):
        await q.message.edit_text("🤝 It's a draw!", reply_markup=create_board(game["board"], game_id))
        await app.send_sticker(chat_id, DRAW_STICKER)
        del games[chat_id][game_id]
    else:
        game["turn"] = 1 - turn
        await q.message.edit_text(
            f"{game['symbols'][game['turn']]}'s turn",
            reply_markup=create_board(game["board"], game_id))

app.run()