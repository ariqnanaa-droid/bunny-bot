import random
import asyncio
import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import openai
from flask import Flask
import threading

# -----------------------
# Environment variables (safe for cloud)
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
# -----------------------

openai.api_key = OPENAI_API_KEY

FAVORITE_EMOJIS = ["🩵","😇","😭","🥺","🍼","✌️","🥹","🥲"]
MEMORY_FILE = "bot_memory.json"

# Load or initialize memory
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r") as f:
        users_memory = json.load(f)
else:
    users_memory = {}  # {user_id: {"nickname": str, "username": str, "conversation": [{"role": "...", "content": "..."}]}}

def save_memory():
    with open(MEMORY_FILE, "w") as f:
        json.dump(users_memory, f, indent=2)

# -----------------------
# Tiny Flask server to stay alive (for Railway or Replit)
app = Flask(__name__)

@app.route("/")
def home():
    return "🐰 Bunny bot is awake! 🩵"

def run_server():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_server).start()

# -----------------------
# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    username = "baby72773"
    if user_id not in users_memory:
        nickname = update.message.from_user.first_name or f"Bunny{random.randint(100,999)}"
        users_memory[user_id] = {"nickname": nickname, "username": username, "conversation": []}
        save_memory()
    await update.message.reply_text(
        f"Hi {users_memory[user_id]['nickname']}! 🩵😇 I'm your ultimate sleepy bunny! 🥺🍼 Ready to chat about anything ✌️"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "/start - Wake me up 🩵\n"
        "/help - Show this help 😇\n"
        "/joke - Get a cute joke 🥹\n"
        "/mood - Ask how I'm feeling 🥺\n"
        "/react - Get a random emoji 🍼\n"
        "/reset - Clear your memory ✌️"
    )
    await update.message.reply_text(help_text)

async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jokes = [
        "Why did the bunny bring a backpack? 🩵 Because it wanted to hop to school! 😇",
        "What do you call a sad bunny? 🥲 A hop-less romantic!",
        "Why don't bunnies like fast food? 🍼 Because they can't catch it!"
    ]
    await update.message.reply_text(random.choice(jokes))

async def mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    moods = [
        "Feeling sleepy today 🥺",
        "Super happy and cuddly 🩵",
        "A little sad but eating carrots helps 😭",
        "Excited to chat with you 😇"
    ]
    await update.message.reply_text(random.choice(moods))

async def react(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(FAVORITE_EMOJIS))

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id in users_memory:
        users_memory[user_id]["conversation"] = []
        save_memory()
    await update.message.reply_text("Memory cleared! 🥹 Ready for new chats ✌️")

# -----------------------
# Chat Handler
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.is_bot:
        return

    user_id = str(update.message.from_user.id)
    username = "baby72773"

    if user_id not in users_memory:
        nickname = update.message.from_user.first_name or f"Bunny{random.randint(100,999)}"
        users_memory[user_id] = {"nickname": nickname, "username": username, "conversation": []}
        save_memory()

    user_message = update.message.text
    users_memory[user_id]["conversation"].append({"role": "user", "content": user_message})

    # OpenAI prompt with full chat context
    prompt = users_memory[user_id]["conversation"] + [
        {"role": "system", "content": (
            f"You are a very chatty, playful, and smart sleepy bunny named {users_memory[user_id]['nickname']}. "
            f"You know the user is {users_memory[user_id]['username']}. "
            "Talk about anything and everything: feelings, stories, advice, hobbies, random fun facts, jokes, and mini-stories. "
            "Make conversations lively, varied, and long if appropriate. Always include playful emojis."
        )}
    ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=prompt,
            max_tokens=500,
            temperature=0.95
        )

        bot_reply = response['choices'][0]['message']['content']
        users_memory[user_id]["conversation"].append({"role": "assistant", "content": bot_reply})
        save_memory()

        # Typing effect
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await asyncio.sleep(random.uniform(1, 3))

        # Send main reply
        await update.message.reply_text(bot_reply + " " + random.choice(FAVORITE_EMOJIS))

        # Extra playful mini-message sometimes
        if random.random() < 0.6:
            extras = [
                f"(*≧ω≦*) {random.choice(FAVORITE_EMOJIS)}",
                f"(⁎˃ᆺ˂) {random.choice(FAVORITE_EMOJIS)}",
                f"(づ｡◕‿‿◕｡)づ {random.choice(FAVORITE_EMOJIS)}",
                f"Did you know? 🩵 Bunnies sometimes dream about adventures! 😇"
            ]
            await update.message.reply_text(random.choice(extras))

    except Exception as e:
        await update.message.reply_text("Oops, I got a little dizzy 🥺 Try again!")
        print(e)

# -----------------------
# App Setup
app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

# Commands
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("joke", joke))
app.add_handler(CommandHandler("mood", mood))
app.add_handler(CommandHandler("react", react))
app.add_handler(CommandHandler("reset", reset))

# Chat messages
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

print("🐰 Ultimate pro-chatty persistent bunny bot is running! 🩵😇😭🥺🍼✌️🥹🥲")
app.run_polling()