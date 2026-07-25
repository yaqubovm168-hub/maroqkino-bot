import json
import os
from pathlib import Path

import requests
from flask import Flask, request

TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

DATA_FILE = Path("movies.json")


def load_movies():
    if not DATA_FILE.exists():
        return {}

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}


def save_movies(movies):
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(movies, file, ensure_ascii=False, indent=2)


MOVIES = load_movies()


def telegram(method, data):
    response = requests.post(
        f"{API_URL}/{method}",
        json=data,
        timeout=30,
    )
    return response.json()


def send_text(chat_id, text):
    telegram(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
        },
    )


@app.route("/", methods=["GET"])
def home():
    return "Maroqkino bot ishlayapti", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}
    message = update.get("message") or {}

    chat = message.get("chat") or {}
    sender = message.get("from") or {}

    chat_id = chat.get("id")
    user_id = sender.get("id")

    if not chat_id:
        return "OK", 200

    text = (message.get("text") or "").strip()

    if text == "/start":
        send_text(
            chat_id,
            "🎬 Kino kodini yuboring.\nMasalan: 1001",
        )
        return "OK", 200

    if text == "/myid":
        send_text(
            chat_id,
            f"Sizning Telegram ID raqamingiz:\n{user_id}",
        )
        return "OK", 200

    if text.startswith("/add "):
        if ADMIN_ID == 0:
            send_text(
                chat_id,
                "❌ ADMIN_ID hali Renderga qo‘shilmagan.\n"
                "Avval /myid yuboring.",
            )
            return "OK", 200

        if user_id != ADMIN_ID:
            send_text(chat_id, "❌ Siz admin emassiz.")
            return "OK", 200

        parts = text.split(maxsplit=1)

        if len(parts) != 2:
            send_text(chat_id, "❌ Masalan: /add 1001")
            return "OK", 200

        code = parts[1].strip()

        if not code.isdigit():
            send_text(chat_id, "❌ Kod faqat raqam bo‘lsin.")
            return "OK", 200

        reply = message.get("reply_to_message") or {}

        if reply.get("video"):
            file_id = reply["video"]["file_id"]
            media_type = "video"

        elif reply.get("document"):
            file_id = reply["document"]["file_id"]
            media_type = "document"

        else:
            send_text(
                chat_id,
                "❌ Video yoki faylga javob qilib /add 1001 yozing.",
            )
            return "OK", 200

        MOVIES[code] = {
            "file_id": file_id,
            "type": media_type,
        }

        save_movies(MOVIES)

        send_text(
            chat_id,
            f"✅ Kino qo‘shildi.\nKodi: {code}",
        )
        return "OK", 200

    if text.startswith("/delete "):
        if user_id != ADMIN_ID:
            send_text(chat_id, "❌ Siz admin emassiz.")
            return "OK", 200

        parts = text.split(maxsplit=1)

        if len(parts) != 2:
            send_text(chat_id, "❌ Masalan: /delete 1001")
            return "OK", 200

        code = parts[1].strip()

        if code in MOVIES:
            del MOVIES[code]
            save_movies(MOVIES)
            send_text(chat_id, f"✅ {code} kodi o‘chirildi.")
        else:
            send_text(chat_id, "❌ Bunday kod topilmadi.")

        return "OK", 200

    if text in MOVIES:
        movie = MOVIES[text]
        file_id = movie["file_id"]
        media_type = movie["type"]
        if media_type == "video":
            telegram(
                "sendVideo",
                {
                    "chat_id": chat_id,
                    "video": file_id,
                    "caption": f"🎬 Kino kodi: {text}",
                },
            )
        else:
            telegram(
                "sendDocument",
                {
                    "chat_id": chat_id,
                    "document": file_id,
                    "caption": f"🎬 Kino kodi: {text}",
                },
            )

        return "OK", 200

    send_text(chat_id, "❌ Bunday kino kodi topilmadi.")
    return "OK", 200
