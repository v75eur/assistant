#!/usr/bin/env python3
# ============================================================
# ASSISTANT GROQ - VERSION AMÉLIORÉE
# Récupère tous les commentaires récents
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
Sois naturel, joyeux, accessible."""

# ============================================================
# 3. SUIVI DES COMMENTAIRES (ANTI-DOUBLON)
# ============================================================

processed = set()
PROCESSED_FILE = "/tmp/processed_comments.json"

def load_processed():
    global processed
    try:
        if os.path.exists(PROCESSED_FILE):
            with open(PROCESSED_FILE, 'r') as f:
                processed = set(json.load(f))
                print(f"📝 {len(processed)} commentaires déjà traités")
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

def get_all_comments(limit=20):
    """Récupère les commentaires de plusieurs posts."""
    if not PAGE_TOKEN:
        return []
    
    all_comments = []
    try:
        # Récupérer les posts récents
        url = f"https://graph.facebook.com/v24.0/{PAGE_ID}/feed"
        params = {
            'fields': 'id,message,comments{id,message,from{name,id,email}}',
            'limit': limit,
            'access_token': PAGE_TOKEN
        }
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        
        for post in data.get('data', []):
            if 'comments' in post:
                for c in post['comments'].get('data', []):
                    author = c.get('from', {}).get('name', 'Inconnu')
                    author_id = c.get('from', {}).get('id', '')
                    comment_id = c.get('id', '')
                    
                    if author_id == PAGE_ID:
                        continue
                    
                    if comment_id in processed:
                        continue
                    
                    all_comments.append({
                        'id': comment_id,
                        'message': c.get('message', ''),
                        'author': author,
                        'author_id': author_id
                    })
        
        return all_comments
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return []

def reply(comment_id, message):
    if not PAGE_TOKEN:
        return False
    try:
        url = f"https://graph.facebook.com/v24.0/{comment_id}/comments"
        data = {'message': message, 'access_token': PAGE_TOKEN}
        r = requests.post(url, data=data, timeout=30)
        return r.status_code == 200
    except:
        return False

def groq_response(comment, author):
    if not GROQ_API_KEY:
        return f"Salut ! Contacte-moi sur WhatsApp {WHATSAPP}"
    try:
        client = Groq(api_key=GROQ_API_KEY)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Commentaire de {author}: {comment}"}
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

def process():
    print("=" * 50)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 TRAITEMENT")
    
    if not check_token():
        print("❌ Token invalide")
        return {"status": "error"}
    
    comments = get_all_comments(limit=20)
    if not comments:
        print("📭 Aucun commentaire")
        return {"status": "success", "message": "Aucun commentaire", "count": 0}
    
    print(f"📝 {len(comments)} commentaire(s)")
    for c in comments:
        print(f"💬 {c['author']}: {c['message'][:50]}...")
        msg = groq_response(c['message'], c['author'])
        if reply(c['id'], msg):
            print("✅ Réponse envoyée")
            processed.add(c['id'])
            save_processed()
        else:
            print("❌ Échec")
        time.sleep(1)
    
    return {"status": "success", "message": "Terminé", "count": len(comments)}

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
        "processed": len(processed)
    })

@app.route('/ping')
def ping():
    return jsonify({"status": "alive"})

@app.route('/wakeup')
def wakeup():
    result = process()
    return jsonify(result)

@app.route('/test')
def test():
    comments = get_all_comments(limit=20)
    return jsonify({
        "token_valid": check_token(),
        "page_id": PAGE_ID,
        "comments_count": len(comments),
        "comments": comments[:5]
    })

@app.route('/reset')
def reset():
    global processed
    processed = set()
    save_processed()
    return jsonify({"status": "reset", "message": "Mémoire effacée"})

# ============================================================
# 6. DÉMARRAGE
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Assistant v3.2")
    print(f"📱 WhatsApp: {WHATSAPP}")
    app.run(host='0.0.0.0', port=port)
