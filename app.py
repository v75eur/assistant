#!/usr/bin/env python3
# ============================================================
# ASSISTANT GROQ - VERSION DEBUG
# Traitement en direct pour voir les erreurs
# ============================================================

import os
import json
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
# 2. PROMPT SYSTÈME
# ============================================================

SYSTEM_PROMPT = """Tu es Rick, le fondateur de Trader123.

Tu es un trader pro depuis 8 ans, développeur, formateur.
Parle comme un humain : naturel, chaleureux, joyeux.
Utilise "tu vois", "en vrai", "franchement", "du coup".
Fais 1-2 fautes de frappe par message.
Termine toujours par le WhatsApp : +22960315458

Tu proposes :
✅ Bots Forex (analyses 24h/24)
✅ Assistants IA
✅ Formations trading
✅ Accompagnement personnalisé
✅ Développement sur mesure

Ne promets jamais de gains garantis. Ne donne pas de conseils financiers précis.
Redirige vers WhatsApp pour les questions techniques."""

# ============================================================
# 3. FONCTIONS FACEBOOK
# ============================================================

def check_token_valid():
    try:
        url = f"https://graph.facebook.com/v24.0/me?access_token={PAGE_TOKEN}"
        response = requests.get(url, timeout=10)
        print(f"🔍 Token Facebook: {'✅ Valide' if response.status_code == 200 else '❌ Invalide'}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erreur token: {e}")
        return False

def get_comments(limit=5):
    if not PAGE_TOKEN:
        print("❌ Pas de token Facebook")
        return []

    try:
        url = f"https://graph.facebook.com/v24.0/{PAGE_ID}/feed"
        params = {
            'fields': 'id,message,comments{id,message,from{name,id}}',
            'limit': limit,
            'access_token': PAGE_TOKEN
        }
        print(f"🔍 Récupération des commentaires...")
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        print(f"📄 Réponse Facebook: {data}")

        comments = []
        for post in data.get('data', []):
            if 'comments' in post:
                for comment in post['comments'].get('data', []):
                    author = comment.get('from', {}).get('name', 'Inconnu')
                    author_id = comment.get('from', {}).get('id', '')
                    comment_id = comment.get('id', '')

                    if author_id == PAGE_ID:
                        print(f"⏭️ Ignoré: {author} (page elle-même)")
                        continue

                    comments.append({
                        'id': comment_id,
                        'message': comment.get('message', ''),
                        'author': author,
                        'author_id': author_id
                    })
                    print(f"💬 Commentaire trouvé: {author} -> {comment.get('message', '')[:50]}...")
        return comments
    except Exception as e:
        print(f"❌ Erreur récupération: {e}")
        return []

def reply_to_comment(comment_id, reply):
    if not PAGE_TOKEN:
        return False

    try:
        url = f"https://graph.facebook.com/v24.0/{comment_id}/comments"
        data = {
            'message': reply,
            'access_token': PAGE_TOKEN
        }
        response = requests.post(url, data=data, timeout=30)
        if response.status_code == 200:
            print(f"✅ Réponse publiée: {reply[:50]}...")
            return True
        else:
            print(f"❌ Erreur réponse: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

# ============================================================
# 4. FONCTION GROQ
# ============================================================

def get_groq_response(comment, author):
    if not GROQ_API_KEY:
        return f"Salut ! Je suis dispo sur WhatsApp {WHATSAPP}"
    
    client = Groq(api_key=GROQ_API_KEY)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Commentaire de {author}: {comment}"}
    ]
    
    try:
        print(f"🤖 Appel Groq pour: {comment[:50]}...")
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=150,
            temperature=0.9,
        )
        reply = response.choices[0].message.content
        if WHATSAPP not in reply:
            reply += f" 📱 WhatsApp : {WHATSAPP}"
        print(f"✅ Réponse Groq: {reply[:50]}...")
        return reply
    except Exception as e:
        print(f"❌ Erreur Groq: {e}")
        return f"Salut, envoie-moi un message sur WhatsApp {WHATSAPP} 👍"

# ============================================================
# 5. TRAITEMENT PRINCIPAL (EN DIRECT)
# ============================================================

def process_comments_direct():
    """Traite les commentaires en direct avec logs détaillés."""
    print("=" * 50)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 TRAITEMENT EN DIRECT")
    print("=" * 50)
    
    if not check_token_valid():
        print("❌ Token invalide - Arrêt")
        return {"status": "error", "message": "Token invalide"}
    
    comments = get_comments(limit=5)
    
    if not comments:
        print("📭 Aucun nouveau commentaire")
        return {"status": "success", "message": "Aucun commentaire", "comments": []}
    
    print(f"📝 {len(comments)} commentaire(s) trouvé(s)")
    
    results = []
    for c in comments:
        print(f"\n💬 {c['author']}: {c['message'][:50]}...")
        reply = get_groq_response(c['message'], c['author'])
        success = reply_to_comment(c['id'], reply)
        results.append({
            "author": c['author'],
            "message": c['message'],
            "reply": reply,
            "success": success
        })
    
    print("\n✅ Traitement terminé")
    return {"status": "success", "message": "Traitement terminé", "results": results}

# ============================================================
# 6. ROUTES FLASK
# ============================================================

@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "version": "3.1 - Debug",
        "whatsapp": WHATSAPP,
        "groq_configured": bool(GROQ_API_KEY),
        "facebook_configured": bool(PAGE_TOKEN)
    })

@app.route('/ping')
def ping():
    return jsonify({"status": "alive"})

@app.route('/wakeup')
def wakeup():
    """Traite les commentaires en DIRECT (avec logs)."""
    result = process_comments_direct()
    return jsonify(result)

@app.route('/test_facebook')
def test_facebook():
    """Teste la connexion Facebook."""
    return jsonify({
        "token_valid": check_token_valid(),
        "page_id": PAGE_ID
    })

@app.route('/comment', methods=['POST'])
def comment():
    data = request.json
    comment = data.get('comment', '')
    author = data.get('author', 'Visiteur')
    if not comment:
        return jsonify({"error": "Commentaire vide"}), 400
    reply = get_groq_response(comment, author)
    return jsonify({"reply": reply})

# ============================================================
# 7. DÉMARRAGE
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Assistant v3.1 - Debug")
    print(f"📱 WhatsApp: {WHATSAPP}")
    print(f"🔍 Mode DEBUG activé - Les logs seront affichés")
    app.run(host='0.0.0.0', port=port)
