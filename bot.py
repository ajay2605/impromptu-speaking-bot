import os
import random
import shutil
import json
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")

IMAGES_FOLDER = "images"
TEMP_FOLDER = "temp"
USERS_FILE = "users.json"


# ---------- USER STORAGE ----------

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    users = load_users()

    if chat_id not in users:
        users.append(chat_id)
        save_users(users)

    await update.message.reply_text("🎤 You are added to Impromptu Speaking!")


# ---------- IMAGE LOGIC ----------

def get_random_image():
    images = os.listdir(IMAGES_FOLDER)

    if images:
        selected = random.choice(images)
        return selected, IMAGES_FOLDER

    temp_images = os.listdir(TEMP_FOLDER)

    if temp_images:
        selected = random.choice(temp_images)
        return selected, TEMP_FOLDER

    print("❌ No images found in both folders.")
    return None, None


async def send_image_to_all():
    users = load_users()
    if not users:
        print("No users found.")
        return

    image_name, source_folder = get_random_image()

    if not image_name:
        return

    image_path = os.path.join(source_folder, image_name)

    app = ApplicationBuilder().token(TOKEN).build()

    async with app:
        for user in users:
            try:
                await app.bot.send_photo(
                    chat_id=user,
                    photo=open(image_path, "rb"),
                    caption="🎤 Daily Impromptu Speaking Prompt"
                )
            except:
                continue

    # Move image to opposite folder
    if source_folder == IMAGES_FOLDER:
        shutil.move(image_path, os.path.join(TEMP_FOLDER, image_name))
    else:
        shutil.move(image_path, os.path.join(IMAGES_FOLDER, image_name))
# ---------- RUN MODES ----------

if __name__ == "__main__":
    import sys

    if "send" in sys.argv:
        asyncio.run(send_image_to_all())
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        print("Bot running...")
        app.run_polling()