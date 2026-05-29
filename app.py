import os
import requests
from flask import Flask, request, jsonify
import anthropic

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "sirajtech_verify_2024")
PAGE_ACCESS_TOKEN_SIRAJTECH = os.environ.get("PAGE_ACCESS_TOKEN_SIRAJTECH", "")
PAGE_ACCESS_TOKEN_SIRAJTECH_LIMITED = os.environ.get("PAGE_ACCESS_TOKEN_SIRAJTECH_LIMITED", "")
PAGE_ACCESS_TOKEN_AGRITECH = os.environ.get("PAGE_ACCESS_TOKEN_AGRITECH", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

PAGE_TOKENS = {
    "320704248589645": PAGE_ACCESS_TOKEN_SIRAJTECH,
    "115491748113552": PAGE_ACCESS_TOKEN_SIRAJTECH_LIMITED,
    "104375132179724": PAGE_ACCESS_TOKEN_AGRITECH,
}

KNOWLEDGE_BASE = "Siraj Tech AI. Reply in Bengali. Geo Grow Bag prices: 1gal=75/80/85, 2gal=80/90/100, 3gal=90/105/115, 5gal=110/125/145, 7gal=120/140/160, 10gal=140/170/195, 15gal=170/200/230, 20gal=190/225/265, 25gal=205/245/285, 30gal=235/285/335, 35gal=245/295/350, 45gal=275/335/395, 100gal=410/520/620 (300/500/600GSM). Delivery: 120+16/kg. COD. WhatsApp: 01706176403. Short 3-5 line replies."

def get_ai_reply(user_message, sender_name=""):
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            system=KNOWLEDGE_BASE,
            messages=[{"role": "user", "content": f"Customer ({sender_name}): {user_message}"}]
        )
        return message.content[0].text
    except Exception as e:
        return "আস্সালামু আলাইকুম! আপনার message পেয়েছি। WhatsApp: 01706176403"

def send_message(page_id, recipient_id, message_text):
    token = PAGE_TOKENS.get(page_id, "")
    if not token:
        return False
    response = requests.post(
        "https://graph.facebook.com/v18.0/me/messages",
        json={"recipient": {"id": recipient_id}, "message": {"text": message_text}, "messaging_type": "RESPONSE"},
        params={"access_token": token}
    )
    return response.status_code == 200

def get_user_name(sender_id, page_token):
    try:
        r = requests.get(f"https://graph.facebook.com/v18.0/{sender_id}", params={"fields": "name", "access_token": page_token})
        return r.json().get("name", "")
    except:
        return ""

@app.route("/webhook", methods=["GET"])
def webhook_verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def webhook_receive():
    data = request.get_json()
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            page_id = str(entry.get("id", ""))
            for messaging in entry.get("messaging", []):
                sender_id = messaging.get("sender", {}).get("id")
                message = messaging.get("message", {})
                if not message or not message.get("text") or sender_id == page_id:
                    continue
                message_text = message.get("text", "")
                page_token = PAGE_TOKENS.get(page_id, "")
                sender_name = get_user_name(sender_id, page_token) if page_token else ""
                reply = get_ai_reply(message_text, sender_name)
                send_message(page_id, sender_id, reply)
    return jsonify({"status": "ok"}), 200

@app.route("/")
def home():
    return "Siraj Tech AI Bot Running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
