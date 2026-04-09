"""
Quick test to verify Telegram bot is working.
Run: python test_telegram.py
"""
import urllib.request
import urllib.parse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = 789661454   # your chat_id from DB

def test():
    print(f"Token: {TOKEN[:20]}...")
    print(f"Chat ID: {CHAT_ID}")

    # 1. Check bot info
    url = f"https://api.telegram.org/bot{TOKEN}/getMe"
    with urllib.request.urlopen(url) as r:
        info = json.loads(r.read())
        print(f"Bot name: {info['result']['first_name']} (@{info['result']['username']})")

    # 2. Send plain text (no HTML, no Markdown)
    url  = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text":    "Test message from clinic app!"
    }).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req) as r:
        result = json.loads(r.read())
        if result.get("ok"):
            print("✅ Telegram message sent successfully!")
        else:
            print(f"❌ Failed: {result}")

try:
    test()
except Exception as e:
    print(f"❌ Error: {e}")
