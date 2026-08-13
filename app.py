#!/usr/bin/env python3
# ============================================================
# ASSISTANT GROQ - VERSION 4.0 COMPLÈTE
# Gère : Commentaires + Réponses + Messages Privés
# ============================================================

import os
import json
import time
from datetime import datetime
from flask import Flask, jsonify, request
from groq import Groq
import requests

app = Flask(__name__)

# ============================================================
# 1. CONFIGURATION
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY_1", "")
PAGE_ID = os.getenv("FB_PAGE_ID", "620580204479095")
PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN", "")
WHATSAPP = os.getenv("WHATSAPP_NUMBER", "+22960315458")

print(f"📱 WhatsApp: {WHATSAPP}")
print(f"📄 Page ID: {PAGE_ID}")
print(f"🔑 Groq: {'✅' if GROQ_API_KEY else '❌'}")
print(f"🔑 Facebook: {'✅' if PAGE_TOKEN else '❌'}")

# ============================================================
# 2. PROMPT
# ============================================================

SYSTEM_PROMPT = """Tu es Rick, le fondateur de Trader123.
Tu es un trader pro depuis 8 ans. Parle comme un humain.
Termine toujours par le WhatsApp : +22960315458
Sois naturel, joyeux, accessible.
Continue la conversation naturellement."""

# ============================================================
# 3. SUIVI
# ============================================================

processed = set()
PROCESSED_FILE = "/tmp/processed_comments.json"

def load_processed():
    global processed
    try:
        if os.path.exists(PROCESSED_FILE):
            with open(PROCESSED_FILE, 'r') as f:
                processed = set(json.load(f))
    except:
        pass

def save_processed():
    try:
        with open(PROCESSED_FILE, 'w') as f:
            json.dump(list(processed), f)
    except:
        pass

load_processed()

# ============================================================
# 4. FONCTIONS
# ============================================================

def check_token():
    if not PAGE_TOKEN:
        return False
    try:
        url = f"https://graph.facebook.com/v24.0/me?access_token={PAGE_TOKEN}"
        r = requests.get(url, timeout=10)
        return r.status_code == 200
    except:
        return False

# ----- 4.1 COMMENTAIRES -----
def get_comments_and_replies():
    """Récupère tous les commentaires et réponses."""
    if not PAGE_TOKEN:
        return []
    
    all_comments = []
    try:
        url = f"https://graph.facebook.com/v24.0/{PAGE_ID}/feed"
        params = {
            'fields': 'id,message,comments{id,message,from{name,id},comments{id,message,from{name,id}}}',
            'limit': 30,
            'access_token': PAGE_TOKEN
        }
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        
        for post in data.get('data', []):
            if 'comments' in post:
                for c in post['comments'].get('data', []):
                    author_id = c.get('from', {}).get('id', '')
                    comment_id = c.get('id', '')
                    
                    if author_id != PAGE_ID and comment_id not in processed:
                        all_comments.append({
                            'id': comment_id,
                            'message': c.get('message', ''),
                            'author': c.get('from', {}).get('name', 'Inconnu'),
                            'author_id': author_id
                        })
                    
                    if 'comments' in c:
                        for reply in c['comments'].get('data', []):
                            reply_id = reply.get('id', '')
                            reply_author_id = reply.get('from', {}).get('id', '')
                            if reply_author_id != PAGE_ID and reply_id not in processed:
                                all_comments.append({
                                    'id': reply_id,
                                    'message': reply.get('message', ''),
                                    'author': reply.get('from', {}).get('name', 'Inconnu'),
                                    'author_id': reply_author_id
                                })
        return all_comments
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return []

# ----- 4.2 MESSAGES PRIVÉS -----
def get_conversations():
    """Récupère les conversations Messenger."""
    if not PAGE_TOKEN:
        return []
    
    conversations = []
    try:
        url = f"https://graph.facebook.com/v24.0/{PAGE_ID}/conversations"
        params = {
            'fields': 'id,participants,messages{id,message,from{name,id}}',
            'limit': 10,
            'access_token': PAGE_TOKEN
        }
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        
        for conv in data.get('data', []):
            if 'messages' in conv:
                for msg in conv['messages'].get('data', []):
                    msg_id = msg.get('id', '')
                    if msg_id not in processed:
                        conversations.append({
                            'id': msg_id,
                            'message': msg.get('message', ''),
                            'author': msg.get('from', {}).get('name', 'Inconnu'),
                            'author_id': msg.get('from', {}).get('id', '')
                        })
        return conversations
    except Exception as e:
        print(f"❌ Erreur conversations: {e}")
        return []

# ----- 4.3 RÉPONSES -----
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

def reply_to_message(conversation_id, message):
    """Répond à un message privé."""
    if not PAGE_TOKEN:
        return False
    try:
        url = f"https://graph.facebook.com/v24.0/{PAGE_ID}/messages"
        data = {
            'recipient': {'id': conversation_id},
            'message': {'text': message},
            'access_token': PAGE_TOKEN
        }
        r = requests.post(url, json=data, timeout=30)
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Erreur envoi message: {e}")
        return False

# ----- 4.4 GROQ -----
def groq_response(comment, author):
    if not GROQ_API_KEY:
        return f"Salut ! Contacte-moi sur WhatsApp {WHATSAPP}"
    try:
        client = Groq(api_key=GROQ_API_KEY)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Message de {author}: {comment}"}
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

# ----- 4.5 TRAITEMENT -----
def process_all():
    print("=" * 50)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 TRAITEMENT COMPLET")
    
    if not check_token():
        print("❌ Token invalide")
        return {"status": "error"}
    
    total = 0
    
    # 1. Traiter les commentaires
    comments = get_comments_and_replies()
    for c in comments:
        print(f"💬 {c['author']}: {c['message'][:30]}...")
        reply = groq_response(c['message'], c['author'])
        if reply_to_comment(c['id'], reply):
            processed.add(c['id'])
            total += 1
            save_processed()
        time.sleep(1)
    
    # 2. Traiter les messages privés
    messages = get_conversations()
    for m in messages:
        print(f"✉️ {m['author']}: {m['message'][:30]}...")
        reply = groq_response(m['message'], m['author'])
        if reply_to_message(m['author_id'], reply):
            processed.add(m['id'])
            total += 1
            save_processed()
        time.sleep(1)
    
    return {"status": "success", "message": "Terminé", "count": total}

# ============================================================
# 5. ROUTES
# ============================================================

@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "whatsapp": WHATSAPP,
        "page_id": PAGE_ID,
        "groq": bool(GROQ_API_KEY),
        "facebook": bool(PAGE_TOKEN),
        "processed": len(processed),
        "version": "4.0 Complète"
    })

@app.route('/ping')
def ping():
    return jsonify({"status": "alive"})

@app.route('/wakeup')
def wakeup():
    result = process_all()
    return jsonify(result)

@app.route('/test')
def test():
    comments = get_comments_and_replies()
    messages = get_conversations()
    return jsonify({
        "token_valid": check_token(),
        "page_id": PAGE_ID,
        "comments_count": len(comments),
        "messages_count": len(messages)
    })

@app.route('/reset')
def reset():
    global processed
    processed = set()
    save_processed()
    return jsonify({"status": "reset"})

# ============================================================
# 6. DÉMARRAGE
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Assistant v4.0 - Contrôle total")
    print(f"📱 WhatsApp: {WHATSAPP}")
    app.run(host='0.0.0.0', port=port)
