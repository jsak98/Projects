"""
Telegram Patient Registration Listener
=======================================
Run this script once to process all pending START messages from patients.
It matches patients by their phone number and saves their Telegram chat_id to the DB.

How it works:
1. Patient opens Telegram → searches your bot → presses START
2. Bot receives the /start message with their chat_id
3. Bot replies asking for their phone number
4. Patient sends their phone number
5. This script matches phone → patient in DB → saves chat_id
6. Patient receives a welcome message

Run manually:
    python services/telegram_listener.py

Or run continuously (recommended — keep terminal open):
    python services/telegram_listener.py --poll
"""

import urllib.request
import urllib.parse
import json
import os
import sys
import time

# Fix module path so 'db' and other modules are found
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# In-memory store for pending registrations {chat_id: "awaiting_phone"}
pending = {}


def api_call(method: str, data: dict = None) -> dict:
    url  = f"{BASE_URL}/{method}"
    body = urllib.parse.urlencode(data or {}).encode() if data else None
    req  = urllib.request.Request(url, data=body)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def send_message(chat_id, text: str):
    api_call("sendMessage", {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})


def save_chat_id(phone: str, chat_id: int) -> bool:
    """Match phone number to patient in DB and save chat_id."""
    try:
        from db.connection import DBConn
        # Normalize phone
        clean = phone.strip().replace(" ", "").replace("-", "").lstrip("+")
        with DBConn() as conn:
            with conn.cursor() as cur:
                # Try exact match first, then last 10 digits
                cur.execute(
                    "UPDATE patients SET telegram_chat_id = %s WHERE phone = %s RETURNING full_name",
                    (chat_id, phone.strip())
                )
                row = cur.fetchone()
                if not row and len(clean) >= 10:
                    last10 = clean[-10:]
                    cur.execute(
                        "UPDATE patients SET telegram_chat_id = %s WHERE phone LIKE %s RETURNING full_name",
                        (chat_id, f"%{last10}")
                    )
                    row = cur.fetchone()
                return row[0] if row else None
    except Exception as e:
        print(f"DB error: {e}")
        return None


def process_update(update: dict):
    msg = update.get("message", {})
    if not msg:
        return

    chat_id = msg["chat"]["id"]
    text    = msg.get("text", "").strip()
    name    = msg["chat"].get("first_name", "there")

    if text == "/start":
        pending[chat_id] = "awaiting_phone"
        send_message(chat_id,
            f"👋 Hello {name}! Welcome to the clinic bot.\n\n"
            f"Please reply with your *registered phone number* to link your account "
            f"and receive appointment confirmations and reports."
        )

    elif chat_id in pending and pending[chat_id] == "awaiting_phone":
        patient_name = save_chat_id(text, chat_id)
        if patient_name:
            del pending[chat_id]
            send_message(chat_id,
                f"✅ *Account linked successfully!*\n\n"
                f"Hello {patient_name}! You'll now receive appointment confirmations "
                f"and consultation reports here. 🏥"
            )
            print(f"✅ Linked chat_id {chat_id} to patient: {patient_name}")
        else:
            send_message(chat_id,
                f"❌ Phone number not found in our records.\n\n"
                f"Please check the number and try again, or contact the clinic."
            )


def poll():
    """Long-poll for updates continuously."""
    print("🤖 Telegram bot is running... (Ctrl+C to stop)")
    offset = None
    while True:
        try:
            params = {"timeout": 30, "allowed_updates": ["message"]}
            if offset:
                params["offset"] = offset
            result = api_call("getUpdates", params)
            for update in result.get("result", []):
                process_update(update)
                offset = update["update_id"] + 1
        except KeyboardInterrupt:
            print("\nBot stopped.")
            break
        except Exception as e:
            err = str(e)
            if "timed out" in err.lower() or "timeout" in err.lower():
                pass  # Normal for long polling — ignore silently
            else:
                print(f"Poll error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set in .env")
        sys.exit(1)

    print("🤖 Starting Telegram registration bot...")
    poll()
