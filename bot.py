import os
import random
import json
import asyncio
from telegram import Bot

TOKEN = os.getenv("TELEGRAM_TOKEN")

IMAGES_FOLDER = "images"
USERS_FILE = "users.json"
USED_FILE = "used_images.json"


# ---------- USER STORAGE ----------

def load_users():
    if not os.path.exists(USERS_FILE):
        return []

    try:
        with open(USERS_FILE, "r") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except:
        return []


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)


# ---------- USED IMAGES STORAGE ----------

def load_used_images():
    if not os.path.exists(USED_FILE):
        return []

    try:
        with open(USED_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_used_images(used):
    with open(USED_FILE, "w") as f:
        json.dump(used, f)


# ---------- FETCH NEW USERS ----------

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

    if new_offset:
        await bot.get_updates(offset=new_offset, timeout=0)

    save_users(users)
    print("Finished checking users.")


# ---------- IMAGE SELECTION LOGIC ----------

def get_random_image():
    if not os.path.exists(IMAGES_FOLDER):
        return None

    all_images = os.listdir(IMAGES_FOLDER)

    if not all_images:
        return None

    used_images = load_used_images()

    available_images = list(set(all_images) - set(used_images))

    # If all images used → reset cycle
    if not available_images:
        print("♻ All images used. Resetting cycle.")
        used_images = []
        available_images = all_images

    selected = random.choice(available_images)

    used_images.append(selected)
    save_used_images(used_images)

    return selected


# ---------- SEND IMAGE ----------

async def send_image_to_all(bot):
    users = load_users()

    if not users:
        print("⚠ No subscribed users found. Skipping image send.")
        return

    image_name = get_random_image()

    if not image_name:
        print("⚠ No images available.")
        return

    image_path = os.path.join(IMAGES_FOLDER, image_name)

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

    print(f"✅ Image '{image_name}' sent successfully.")


# ---------- MAIN ----------

async def main():
    os.makedirs(IMAGES_FOLDER, exist_ok=True)

    bot = Bot(token=TOKEN)

    await fetch_new_users(bot)
    await send_image_to_all(bot)

    print("Bot execution finished.")


if __name__ == "__main__":
    asyncio.run(main())