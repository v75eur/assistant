#!/usr/bin/env python3
# ============================================================
# ASSISTANT GROQ - VERSION SIMPLIFIÉE
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
# 3. FONCTIONS
# ============================================================

def check_token():
    """Vérifie si le token Facebook est valide."""
    if not PAGE_TOKEN:
        return False
    try:
        url = f"https://graph.facebook.com/v24.0/me?access_token={PAGE_TOKEN}"
        r = requests.get(url, timeout=10)
        print(f"🔍 Token Facebook: {'✅' if r.status_code == 200 else '❌'} ({r.status_code})")
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Erreur token: {e}")
        return False

def get_comments():
    """Récupère les commentaires."""
    if not PAGE_TOKEN:
        print("❌ Pas de token")
        return []
    try:
        url = f"https://graph.facebook.com/v24.0/{PAGE_ID}/feed"
        params = {
            'fields': 'id,comments{id,message,from{name,id}}',
            'limit': 5,
            'access_token': PAGE_TOKEN
        }
        print("🔍 Récupération des commentaires...")
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        print(f"📄 Réponse Facebook reçue")
        
        comments = []
        for post in data.get('data', []):
            for c in post.get('comments', {}).get('data', []):
                author = c.get('from', {}).get('name', 'Inconnu')
                author_id = c.get('from', {}).get('id', '')
                if author_id != PAGE_ID:
                    comments.append({
                        'id': c['id'],
                        'message': c.get('message', ''),
                        'author': author,
                        'author_id': author_id
                    })
                    print(f"💬 {author}: {c.get('message', '')[:50]}...")
        return comments
    except Exception as e:
        print(f"❌ Erreur récupération: {e}")
        return []

def reply(comment_id, message):
    """Répond à un commentaire."""
    if not PAGE_TOKEN:
        return False
    try:
        url = f"https://graph.facebook.com/v24.0/{comment_id}/comments"
        data = {'message': message, 'access_token': PAGE_TOKEN}
        r = requests.post(url, data=data, timeout=30)
        print(f"✅ Réponse envoyée" if r.status_code == 200 else f"❌ Erreur: {r.text}")
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Erreur réponse: {e}")
        return False

def groq_response(comment, author):
    """Génère une réponse avec Groq."""
    if not GROQ_API_KEY:
        return f"Salut ! Contacte-moi sur WhatsApp {WHATSAPP}"
    try:
        client = Groq(api_key=GROQ_API_KEY)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Commentaire de {author}: {comment}"}
        ]
        print(f"🤖 Appel Groq...")
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
    """Traite les commentaires."""
    print("=" * 50)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 TRAITEMENT")
    print("=" * 50)
    
    if not check_token():
        print("❌ Token invalide")
        return {"status": "error", "message": "Token invalide"}
    
    comments = get_comments()
    if not comments:
        print("📭 Aucun commentaire")
        return {"status": "success", "message": "Aucun commentaire", "count": 0}
    
    print(f"📝 {len(comments)} commentaire(s)")
    for c in comments:
        print(f"\n💬 {c['author']}: {c['message'][:50]}...")
        msg = groq_response(c['message'], c['author'])
        print(f"📝 Réponse: {msg[:80]}...")
        success = reply(c['id'], msg)
        if success:
            print("✅ Réponse publiée")
        else:
            print("❌ Échec publication")
        time.sleep(1)
    
    return {"status": "success", "message": "Terminé", "count": len(comments)}

# ============================================================
# 4. ROUTES
# ============================================================

@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "whatsapp": WHATSAPP,
        "page_id": PAGE_ID,
        "groq": bool(GROQ_API_KEY),
        "facebook": bool(PAGE_TOKEN)
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
    return jsonify({
        "token_valid": check_token(),
        "page_id": PAGE_ID,
        "comments": get_comments()
    })

# ============================================================
# 5. DÉMARRAGE
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Assistant v3.1")
    print(f"📱 WhatsApp: {WHATSAPP}")
    app.run(host='0.0.0.0', port=port)
