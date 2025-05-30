
import telebot
from telebot import types

# ===== BOT CONFIG =====
BOT_TOKEN = '7999151899:AAEej0JnxG8pgAHvwjzXfSKDSeNdvz8NkO8'
ADMIN_ID = 7929115529
bot = telebot.TeleBot(BOT_TOKEN)

# ===== USER DATA =====
user_balances = {}
worked_users = {}
awaiting_withdraw = set()
pending_tasks = {}
referrals = {}
joined_users = set()
task_list = []

# ===== START COMMAND =====
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    args = message.text.split()
    if user_id not in joined_users:
        if len(args) > 1:
            try:
                referrer_id = int(args[1])
                if referrer_id != user_id:
                    referrals[user_id] = referrer_id
                    user_balances[referrer_id] = user_balances.get(referrer_id, 0) + 5
                    bot.send_message(referrer_id, f"🎉 You earned ₹5 for referring user {user_id}!")
            except:
                pass
        joined_users.add(user_id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📋 Task", "📤 Submit Proof")
    markup.row("💰 Balance", "🏧 Withdraw")
    markup.row("🔗 Referral")
    bot.send_message(
        message.chat.id,
        "👋 Welcome to *Earn Money Bot!*
Choose an option below:",
        parse_mode="Markdown",
        reply_markup=markup
    )

# ===== INLINE BUTTONS =====
def generate_approval_markup(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"))
    markup.add(types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}"))
    return markup

def generate_task_removal_markup():
    markup = types.InlineKeyboardMarkup()
    for index, task in enumerate(task_list):
        markup.add(types.InlineKeyboardButton(f"❌ Remove Task {index + 1}", callback_data=f"remove_{index}"))
    return markup

# ===== TEXT HANDLER =====
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_message(message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    username = message.from_user.username or "NoUsername"
    text = message.text.strip()

    if user_id in awaiting_withdraw:
        parts = text.split()
        if len(parts) != 2:
            bot.reply_to(message, "⚠️ Invalid format. Use like: `upi@bank 50.5`", parse_mode="Markdown")
        else:
            upi_id, amount_str = parts
            try:
                amount = float(amount_str)
                balance = user_balances.get(user_id, 0)
                if amount > balance:
                    bot.reply_to(message, "❌ You don't have enough balance.")
                else:
                    user_balances[user_id] -= amount
                    bot.reply_to(message, "✅ Withdraw request sent to admin.")
                    bot.send_message(
                        ADMIN_ID,
                        f"📤 *Withdraw Request*
👤 Name: {name}
🆔 ID: {user_id}
💳 UPI: `{upi_id}`
💰 Amount: ₹{amount:.2f}",
                        parse_mode="Markdown"
                    )
            except ValueError:
                bot.reply_to(message, "⚠️ Amount must be a number.")
        awaiting_withdraw.remove(user_id)
        return

    if text == "📋 Task":
        if task_list:
            all_tasks = "\n".join([f"{i+1}. {task}" for i, task in enumerate(task_list)])
            bot.reply_to(message, f"📝 *Today's Tasks:*\n{all_tasks}", parse_mode="Markdown")
        else:
            bot.reply_to(message, "📭 No task is currently available.")
    elif text == "📤 Submit Proof":
        worked_users[user_id] = name
        bot.reply_to(message, "📸 Please send your proof (screenshot).")
    elif text == "💰 Balance":
        bal = user_balances.get(user_id, 0)
        bot.reply_to(message, f"💰 Your balance: ₹{bal:.2f}")
    elif text == "🏧 Withdraw":
        awaiting_withdraw.add(user_id)
        bot.reply_to(message, "🔐 Send your UPI ID and amount.\nFormat: `upi@bank 50.5`", parse_mode="Markdown")
    elif text == "🔗 Referral":
        ref_link = f"https://t.me/{{bot.get_me().username}}?start={{user_id}}"
        bot.reply_to(message, f"🔗 *Your Referral Link:*\n`{ref_link}`\n\n🎁 Earn ₹5 per referral!", parse_mode="Markdown")

    if user_id == ADMIN_ID:
        if text.startswith("/addbalance"):
            try:
                _, target_id, amount = text.split()
                target_id = int(target_id)
                amount = float(amount)
                user_balances[target_id] = user_balances.get(target_id, 0) + amount
                bot.send_message(ADMIN_ID, f"✅ ₹{amount} added to {target_id}")
            except:
                bot.reply_to(message, "⚠️ Usage: /addbalance user_id amount")
        elif text.startswith("/balance"):
            try:
                _, target_id = text.split()
                target_id = int(target_id)
                bal = user_balances.get(target_id, 0)
                bot.send_message(ADMIN_ID, f"💰 Balance of {target_id}: ₹{bal}")
            except:
                bot.reply_to(message, "⚠️ Usage: /balance user_id")
        elif text.startswith("/addtask"):
            task = text.replace("/addtask", "", 1).strip()
            if task:
                task_list.append(task)
                bot.send_message(ADMIN_ID, f"✅ Task added:\n{task}")
            else:
                bot.reply_to(message, "⚠️ Usage: /addtask your task here")
        elif text == "/tasks":
            if task_list:
                all_tasks = "\n".join([f"{i+1}. {task}" for i, task in enumerate(task_list)])
                bot.send_message(ADMIN_ID, f"🗒 *Current Tasks:*\n{all_tasks}", parse_mode="Markdown")
            else:
                bot.send_message(ADMIN_ID, "📭 No task available.")
        elif text == "/removetask":
            if task_list:
                bot.send_message(ADMIN_ID, "🗑 Select a task to remove:", reply_markup=generate_task_removal_markup())
            else:
                bot.send_message(ADMIN_ID, "📭 No task to remove.")

    if text in ["📋 Task", "📤 Submit Proof", "💰 Balance", "🏧 Withdraw", "🔗 Referral"]:
        bot.send_message(
            ADMIN_ID,
            f"📥 *User Activity*\n👤 Name: {name}\n🔗 Username: @{username}\n🆔 ID: {user_id}\n💬 Option: *{text}*\n💰 Balance: ₹{user_balances.get(user_id, 0):.2f}",
            parse_mode="Markdown"
        )

# ===== PHOTO SUBMISSION =====
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    if user_id in worked_users:
        file_id = message.photo[-1].file_id
        pending_tasks[user_id] = file_id
        bot.send_photo(
            ADMIN_ID,
            photo=file_id,
            caption=f"📤 *New Task Submission*\n👤 User ID: {user_id}\n📝 Approve this task?",
            parse_mode='Markdown',
            reply_markup=generate_approval_markup(user_id)
        )
        bot.reply_to(message, "✅ Proof submitted! Please wait for admin approval.")
        worked_users.pop(user_id, None)

# ===== CALLBACK HANDLER =====
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data.startswith("approve_"):
        uid = int(call.data.split("_")[1])
        user_balances[uid] = user_balances.get(uid, 0) + 10
        bot.send_message(uid, "✅ Your task has been approved. ₹10 added to your balance. Please wait 2 minutes.")
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=f"✅ Approved! ₹10 added to user {uid}."
        )
    elif call.data.startswith("reject_"):
        uid = int(call.data.split("_")[1])
        bot.send_message(uid, "❌ Your task proof was rejected.")
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=f"❌ Rejected task submission from user {uid}."
        )
    elif call.data.startswith("remove_"):
        index = int(call.data.split("_")[1])
        if 0 <= index < len(task_list):
            removed = task_list.pop(index)
            bot.edit_message_text(
                f"🗑 Removed Task:\n{removed}",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )

# ===== RUN BOT =====
print("🤖 Bot is running...")
bot.infinity_polling()
