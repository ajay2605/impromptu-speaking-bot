import os
import random
import shutil
import json
import asyncio
from telegram import Bot

TOKEN = os.getenv("TELEGRAM_TOKEN")

IMAGES_FOLDER = "images"
TEMP_FOLDER = "temp"
USERS_FILE = "users.json"


# ---------- USER STORAGE ----------

def load_users():
    if not os.path.exists(USERS_FILE):
        print("users.json not found. Creating new file.")
        return []

    try:
        with open(USERS_FILE, "r") as f:
            content = f.read().strip()

            if not content:
                print("users.json is empty.")
                return []

            return json.loads(content)

    except json.JSONDecodeError:
        print("users.json is corrupted. Resetting.")
        return []

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)


# ---------- FETCH NEW USERS (NO LONG POLLING) ----------

async def fetch_new_users(bot):
    print("Checking for new subscribers...")

    updates = await bot.get_updates(
        timeout=0,
        limit=100,
        allowed_updates=["message"]
    )

    users = load_users()
    new_offset = None

    for update in updates:
        new_offset = update.update_id + 1

        if update.message and update.message.text == "/start":
            chat_id = update.message.chat.id
            if chat_id not in users:
                users.append(chat_id)
                print(f"New user added: {chat_id}")

    # Mark updates as processed
    if new_offset:
        await bot.get_updates(offset=new_offset, timeout=0)

    save_users(users)
    print("Finished checking users.")


# ---------- IMAGE LOGIC ----------

def get_random_image():
    images = os.listdir(IMAGES_FOLDER)

    if images:
        return random.choice(images), IMAGES_FOLDER

    temp_images = os.listdir(TEMP_FOLDER)

    if temp_images:
        return random.choice(temp_images), TEMP_FOLDER

    print("❌ No images found in both folders.")
    return None, None

async def send_image_to_all(bot):
    users = load_users()

    if not users:
        print("⚠ No subscribed users found. Skipping image send.")
        return

    image_name, source_folder = get_random_image()

    if not image_name:
        print("⚠ No images available. Skipping send.")
        return

    image_path = os.path.join(source_folder, image_name)

    for user in users:
        try:
            with open(image_path, "rb") as photo:
                await bot.send_photo(
                    chat_id=user,
                    photo=photo,
                    caption="🎤 Daily Impromptu Speaking Prompt"
                )
        except Exception as e:
            print(f"Failed sending to {user}: {e}")

    # Rotate image
    if source_folder == IMAGES_FOLDER:
        shutil.move(image_path, os.path.join(TEMP_FOLDER, image_name))
    else:
        shutil.move(image_path, os.path.join(IMAGES_FOLDER, image_name))

    print("✅ Image sent successfully.")
# ---------- MAIN ----------

async def main():
    
    # Ensure folders exist
    os.makedirs(IMAGES_FOLDER, exist_ok=True)
    os.makedirs(TEMP_FOLDER, exist_ok=True)
    
    bot = Bot(token=TOKEN)

    await fetch_new_users(bot)
    await send_image_to_all(bot)

    print("Bot execution finished.")


if __name__ == "__main__":
    asyncio.run(main())