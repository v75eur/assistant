#!/usr/bin/env python3
# ============================================================
# ASSISTANT GROQ - VERSION SIMPLIFIÉE
# Sans matplotlib - Compatible Python 3.14
# ============================================================

import os
import json
import time
import random
from datetime import datetime
from flask import Flask, jsonify, request
from groq import Groq
import requests

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY_1", "")
PAGE_ID = os.getenv("FB_PAGE_ID", "620580204479095")
PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN", "")
WHATSAPP = os.getenv("WHATSAPP_NUMBER", "+22960315458")

print(f"📱 WhatsApp: {WHATSAPP}")
print(f"📄 Page ID: {PAGE_ID}")

SYSTEM_PROMPT = """Tu es Rick, le fondateur de Trader123.
Tu es un trader pro depuis 8 ans. Parle comme un humain.
Termine toujours par le WhatsApp : +22960315458
Sois naturel, joyeux, accessible."""

FAQ = {
    "trading": "Le trading consiste à acheter et vendre des actifs. Contacte-moi sur WhatsApp pour en savoir plus !",
    "formation": "Je propose des formations personnalisées. WhatsApp : +22960315458",
    "xauusd": "XAUUSD est l'Or/Dollar. Mon actif préféré !",
    "v75": "Le V75 est un indice de volatilité sur Deriv.",
    "forex": "Le Forex est le marché des devises.",
}

processed_comments = set()
processed_messages = set()
COMMENTS_FILE = "/tmp/processed_comments.json"
MESSAGES_FILE = "/tmp/processed_messages.json"

def load_processed_comments():
    global processed_comments
    try:
        if os.path.exists(COMMENTS_FILE):
            with open(COMMENTS_FILE, 'r') as f:
                processed_comments = set(json.load(f))
    except:
        pass

def save_processed_comments():
    try:
        with open(COMMENTS_FILE, 'w') as f:
            json.dump(list(processed_comments), f)
    except:
        pass

def load_processed_messages():
    global processed_messages
    try:
        if os.path.exists(MESSAGES_FILE):
            with open(MESSAGES_FILE, 'r') as f:
                processed_messages = set(json.load(f))
    except:
        pass

def save_processed_messages():
    try:
        with open(MESSAGES_FILE, 'w') as f:
            json.dump(list(processed_messages), f)
    except:
        pass

load_processed_comments()
load_processed_messages()

def check_token():
    if not PAGE_TOKEN:
        return False
    try:
        url = f"https://graph.facebook.com/v24.0/me?access_token={PAGE_TOKEN}"
        r = requests.get(url, timeout=10)
        return r.status_code == 200
    except:
        return False

def publish_post(message):
    if not PAGE_TOKEN:
        return False
    try:
        url = f"https://graph.facebook.com/v24.0/{PAGE_ID}/feed"
        data = {'message': message, 'access_token': PAGE_TOKEN}
        r = requests.post(url, data=data, timeout=30)
        return r.status_code == 200
    except:
        return False

def groq_response(message, author):
    if not GROQ_API_KEY:
        return f"Salut ! Contacte-moi sur WhatsApp {WHATSAPP}"
    try:
        client = Groq(api_key=GROQ_API_KEY)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Message de {author}: {message}"}
        ]
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=150,
            temperature=0.9,
        )
        reply = r.choices[0].message.content
        if WHATSAPP not in reply:
            reply += f" 📱 WhatsApp : {WHATSAPP}"
        return reply
    except Exception as e:
        print(f"❌ Groq: {e}")
        return f"Salut, envoie-moi un message sur WhatsApp {WHATSAPP} 👍"

def get_comments():
    if not PAGE_TOKEN:
        return []
    try:
        url = f"https://graph.facebook.com/v24.0/{PAGE_ID}/feed"
        params = {
            'fields': 'id,message,comments{id,message,from{name,id}}',
            'limit': 30,
            'access_token': PAGE_TOKEN
        }
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        comments = []
        for post in data.get('data', []):
            if 'comments' in post:
                for c in post['comments'].get('data', []):
                    author_id = c.get('from', {}).get('id', '')
                    comment_id = c.get('id', '')
                    if author_id != PAGE_ID and comment_id not in processed_comments:
                        comments.append({
                            'id': comment_id,
                            'message': c.get('message', ''),
                            'author': c.get('from', {}).get('name', 'Inconnu'),
                            'author_id': author_id
                        })
        return comments
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return []

def reply_to_comment(comment_id, message):
    if not PAGE_TOKEN:
        return False
    try:
        url = f"https://graph.facebook.com/v24.0/{comment_id}/comments"
        data = {'message': message, 'access_token': PAGE_TOKEN}
        r = requests.post(url, data=data, timeout=30)
        return r.status_code == 200
    except:
        return False

def get_conversations():
    if not PAGE_TOKEN:
        return []
    try:
        url = f"https://graph.facebook.com/v24.0/{PAGE_ID}/conversations"
        params = {
            'fields': 'id,participants,messages{id,message,from{name,id}}',
            'limit': 20,
            'access_token': PAGE_TOKEN
        }
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        messages = []
        for conv in data.get('data', []):
            if 'messages' in conv:
                for msg in conv['messages'].get('data', []):
                    msg_id = msg.get('id', '')
                    author_id = msg.get('from', {}).get('id', '')
                    if author_id != PAGE_ID and msg_id not in processed_messages:
                        messages.append({
                            'id': msg_id,
                            'message': msg.get('message', ''),
                            'author': msg.get('from', {}).get('name', 'Inconnu'),
                            'author_id': author_id
                        })
        return messages
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return []

def reply_to_message(recipient_id, message):
    if not PAGE_TOKEN:
        return False
    try:
        url = f"https://graph.facebook.com/v24.0/{PAGE_ID}/messages"
        data = {
            'recipient': {'id': recipient_id},
            'message': {'text': message},
            'access_token': PAGE_TOKEN
        }
        r = requests.post(url, json=data, timeout=30)
        return r.status_code == 200
    except:
        return False

def process_comments():
    print("=" * 50)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 💬 TRAITEMENT COMMENTAIRES")
    if not check_token():
        return {"status": "error"}
    comments = get_comments()
    if not comments:
        return {"status": "success", "count": 0}
    for c in comments:
        reply = groq_response(c['message'], c['author'])
        if reply_to_comment(c['id'], reply):
            processed_comments.add(c['id'])
            save_processed_comments()
        time.sleep(1)
    return {"status": "success", "count": len(comments)}

def process_messages():
    print("=" * 50)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✉️ TRAITEMENT MESSAGES")
    if not check_token():
        return {"status": "error"}
    messages = get_conversations()
    if not messages:
        return {"status": "success", "count": 0}
    for msg in messages:
        reply = groq_response(msg['message'], msg['author'])
        if reply_to_message(msg['author_id'], reply):
            processed_messages.add(msg['id'])
            save_processed_messages()
        time.sleep(1)
    return {"status": "success", "count": len(messages)}

def publish_faq():
    key = random.choice(list(FAQ.keys()))
    answer = FAQ[key]
    msg = f"❓ {key.upper()}\n\n{answer}\n\n📱 WhatsApp: {WHATSAPP}"
    result = publish_post(msg)
    return {"status": "success" if result else "error"}

def publish_course():
    topics = [
        "Les bases du trading",
        "Analyse technique",
        "Gestion des risques",
        "Psychologie du trading",
        "Stratégies gagnantes"
    ]
    topic = random.choice(topics)
    course = groq_response(f"Crée un cours sur {topic}", "Formation")
    msg = f"📚 FORMATION\n📖 {topic}\n\n{course}\n\n📱 WhatsApp: {WHATSAPP}"
    result = publish_post(msg)
    return {"status": "success" if result else "error"}

@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "whatsapp": WHATSAPP,
        "page_id": PAGE_ID,
        "version": "6.0 - Simplifiée"
    })

@app.route('/ping')
def ping():
    return jsonify({"status": "alive"})

@app.route('/wakeup')
def wakeup():
    return jsonify(process_comments())

@app.route('/messages')
def messages():
    return jsonify(process_messages())

@app.route('/course')
def course():
    return jsonify(publish_course())

@app.route('/publish/faq')
def publish_faq_route():
    return jsonify(publish_faq())

@app.route('/reset')
def reset():
    global processed_comments, processed_messages
    processed_comments = set()
    processed_messages = set()
    save_processed_comments()
    save_processed_messages()
    return jsonify({"status": "reset"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Assistant v6.0 - Simplifiée")
    print(f"📱 WhatsApp: {WHATSAPP}")
    app.run(host='0.0.0.0', port=port)
