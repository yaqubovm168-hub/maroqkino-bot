import os

import requests
from flask import Flask, request

TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"
MOVIES_API = f"{SUPABASE_URL}/rest/v1/movies"

app = Flask(__name__)


def telegram(method, data):
    response = requests.post(
        f"{TELEGRAM_API}/{method}",
        json=data,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def send_text(chat_id, text):
    telegram(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
        },
    )


def supabase_headers(extra=None):
    headers = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json",
    }

    if extra:
        headers.update(extra)

    return headers


def get_movie(code):
    response = requests.get(
        MOVIES_API,
        params={
            "code": f"eq.{code}",
            "select": "code,file_id,media_type",
            "limit": "1",
        },
        headers=supabase_headers(),
        timeout=30,
    )

    response.raise_for_status()
    movies = response.json()

    if movies:
        return movies[0]

    return None


def save_movie(code, file_id, media_type):
    response = requests.post(
        MOVIES_API,
        params={
            "on_conflict": "code",
        },
        headers=supabase_headers(
            {
                "Prefer": "resolution=merge-duplicates,return=minimal",
            }
        ),
        json={
            "code": code,
            "file_id": file_id,
            "media_type": media_type,
        },
        timeout=30,
    )

    response.raise_for_status()


def delete_movie(code):
    response = requests.delete(
        MOVIES_API,
        params={
            "code": f"eq.{code}",
        },
        headers=supabase_headers(),
        timeout=30,
    )

    response.raise_for_status()


@app.route("/", methods=["GET"])
def home():
    return "Maroqkino bot Supabase bilan ishlayapti", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
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
                    "❌ Video yoki faylga reply qilib /add 1001 yozing.",
                )
                return "OK", 200send_text(
                chat_id,
                f"✅ Kino doimiy bazaga qo‘shildi.\nKodi: {code}",
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
            delete_movie(code)

            send_text(
                chat_id,
                f"✅ {code} kodi o‘chirildi.",
            )
            return "OK", 200

        if text.isdigit():
            movie = get_movie(text)

            if not movie:
                send_text(chat_id, "❌ Bunday kino kodi topilmadi.")
                return "OK", 200

            if movie["media_type"] == "video":
                telegram(
                    "sendVideo",
                    {
                        "chat_id": chat_id,
                        "video": movie["file_id"],
                        "caption": f"🎬 Kino kodi: {text}",
                    },
                )

            else:
                telegram(
                    "sendDocument",
                    {
                        "chat_id": chat_id,
                        "document": movie["file_id"],
                        "caption": f"🎬 Kino kodi: {text}",
                    },
                )

            return "OK", 200

        send_text(
            chat_id,
            "❌ Kino kodini raqam bilan yuboring.",
        )
        return "OK", 200

    except requests.RequestException as error:
        print(f"API xatosi: {error}", flush=True)
        return "OK", 200

    except Exception as error:
        print(f"Bot xatosi: {error}", flush=True)
        return "OK", 200

            save_movie(code, file_id, media_type)
