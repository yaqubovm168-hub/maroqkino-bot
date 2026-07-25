import os
import requests
from flask import Flask, request

TOKEN = os.environ["BOT_TOKEN"]
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app app = Flask(__name__)

# Kino kodi va Telegram video file_id
MOVIES = {
    "1001": "",
}


def telegram(method, data):
    requests.post(
        f"{API_URL}/{method}",
        json=data,
        timeout=30
    )


def send_text(chat_id, text):
    telegram(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text
        }
    )


@app.route("/", methods=["GET"])
def home():
    return "Maroqkino bot ishlayapti", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}
    message = update.get("message") or {}

    chat = message.get("chat") or {}
    chat_id = chat.get("id")

    if not chat_id:
        return "OK", 200

    text = (message.get("text") or "").strip()

    if text == "/start":
        send_text(
            chat_id,
            "🎬 Kino kodini yuboring.\nMasalan: 1001"
        )
        return "OK", 200

    if text == "/id":
        reply = message.get("reply_to_message") or {}
        video = reply.get("video") or {}
        file_id = video.get("file_id")

        if file_id:
            send_text(
                chat_id,
                f"Video file_id:\n{file_id}"
            )
        else:
            send_text(
                chat_id,
                "Videoga javob qilib /id yozing."
            )

        return "OK", 200

    if text in MOVIES:
        file_id = MOVIES[text]

        if file_id:
            telegram(
                "sendVideo",
                {
                    "chat_id": chat_id,
                    "video": file_id,
                    "caption": f"🎬 Kino kodi: {text}"
                }
            )
        else:
            send_text(
                chat_id,
                f"{text} kodi bor, lekin kino hali qo‘shilmagan."
            )

        return "OK", 200

    send_text(
        chat_id,
        "❌ Bunday kino kodi topilmadi."
    )

    return "OK", 200
