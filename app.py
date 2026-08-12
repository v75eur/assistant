#!/usr/bin/env python3
# ============================================================
# ASSISTANT GROQ - VERSION ASYNCHRONE
# Réponse instantanée + traitement en arrière-plan
# ============================================================

import os
import time
import random
import threading
import json
from datetime import datetime
from flask import Flask, jsonify, request
from groq import Groq
import requests

# ============================================================
# 1. CONFIGURATION
# ============================================================

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY_1", "")
PAGE_ID = os.getenv("FB_PAGE_ID", "620580204479095")
PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN", "")
WHATSAPP = os.getenv("WHATSAPP_NUMBER", "+22960315458")

# ============================================================
# 2. MÉMOIRE ET ANTI-DOUBLON
# ============================================================

memory = {}
MEMORY_FILE = "/tmp/assistant_memory.json"
MAX_HISTORY = 10
processed_comments = set()
PROCESSED_FILE = "/tmp/processed_comments.json"

def load_memory():
    global memory
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r') as f:
                memory = json.load(f)
    except Exception as e:
        print(f"⚠️ Erreur mémoire: {e}")

def save_memory():
    try:
        with open(MEMORY_FILE, 'w') as f:
            json.dump(memory, f)
    except Exception as e:
        print(f"⚠️ Erreur sauvegarde mémoire: {e}")

def load_processed():
    global processed_comments
    try:
        if os.path.exists(PROCESSED_FILE):
            with open(PROCESSED_FILE, 'r') as f:
                processed_comments = set(json.load(f))
    except Exception as e:
        print(f"⚠️ Erreur processed: {e}")

def save_processed():
    try:
        with open(PROCESSED_FILE, 'w') as f:
            json.dump(list(processed_comments), f)
    except Exception as e:
        print(f"⚠️ Erreur sauvegarde processed: {e}")

def is_comment_processed(comment_id):
    return comment_id in processed_comments

def mark_comment_processed(comment_id):
    processed_comments.add(comment_id)
    if len(processed_comments) > 500:
        to_remove = list(processed_comments)[0]
        processed_comments.remove(to_remove)
    save_processed()

def get_user_memory(user_id, user_name=None):
    if user_id not in memory:
        memory[user_id] = {"name": user_name or "Visiteur", "history": [], "last_seen": "", "last_comment": ""}
        save_memory()
    if user_name and memory[user_id]["name"] == "Visiteur":
        memory[user_id]["name"] = user_name
        save_memory()
    return memory[user_id]

def update_user_memory(user_id, comment, reply):
    if user_id not in memory:
        memory[user_id] = {"name": "Visiteur", "history": [], "last_seen": "", "last_comment": ""}
    memory[user_id]["last_seen"] = datetime.now().isoformat()
    memory[user_id]["last_comment"] = comment
    memory[user_id]["history"].append({"time": datetime.now().isoformat(), "user": comment, "assistant": reply})
    if len(memory[user_id]["history"]) > MAX_HISTORY:
        memory[user_id]["history"] = memory[user_id]["history"][-MAX_HISTORY:]
    save_memory()

def build_context(user_id):
    if user_id not in memory or not memory[user_id].get("history"):
        return None
    context = "Historique de la conversation :\n"
    for entry in memory[user_id]["history"][-5:]:
        context += f"- Utilisateur : {entry['user']}\n- Réponse : {entry['assistant']}\n"
    return context

# ============================================================
# 3. PROMPT SYSTÈME
# ============================================================

BASE_SYSTEM_PROMPT = """Tu es Rick, le fondateur de Trader123.

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

def get_system_prompt(user_id):
    context = build_context(user_id)
    if context:
        return BASE_SYSTEM_PROMPT + f"\n\nCONTEXTE :\n{context}\n\nFais référence à cette conversation pour personnaliser ta réponse."
    return BASE_SYSTEM_PROMPT

# ============================================================
# 4. FONCTIONS GROQ ET FACEBOOK
# ============================================================

def get_groq_response(comment, author, user_id=None):
    if not GROQ_API_KEY:
        return f"Salut ! Je suis dispo sur WhatsApp {WHATSAPP}"
    
    client = Groq(api_key=GROQ_API_KEY)
    messages = [
        {"role": "system", "content": get_system_prompt(user_id)},
        {"role": "user", "content": f"Commentaire de {author}: {comment}"}
    ]
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=150,
            temperature=0.9,
        )
        reply = response.choices[0].message.content
        if WHATSAPP not in reply:
            reply += f" 📱 WhatsApp : {WHATSAPP}"
        return reply
    except Exception as e:
        print(f"❌ Erreur Groq: {e}")
        return f"Salut, envoie-moi un message sur WhatsApp {WHATSAPP} 👍"

def check_token_valid():
    try:
        url = f"https://graph.facebook.com/v24.0/me?access_token={PAGE_TOKEN}"
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except:
        return False

def get_comments(limit=5):
    if not PAGE_TOKEN:
        return []
    try:
        url = f"https://graph.facebook.com/v24.0/{PAGE_ID}/feed"
        params = {'fields': 'id,message,comments{id,message,from{name,id}}', 'limit': limit, 'access_token': PAGE_TOKEN}
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        comments = []
        for post in data.get('data', []):
            if 'comments' in post:
                for comment in post['comments'].get('data', []):
                    author = comment.get('from', {}).get('name', 'Inconnu')
                    author_id = comment.get('from', {}).get('id', '')
                    comment_id = comment.get('id', '')
                    if author_id == PAGE_ID or is_comment_processed(comment_id):
                        continue
                    comments.append({'id': comment_id, 'message': comment.get('message', ''), 'author': author, 'author_id': author_id})
        return comments
    except Exception as e:
        print(f"❌ Erreur récupération: {e}")
        return []

def reply_to_comment(comment_id, reply):
    if not PAGE_TOKEN:
        return False
    try:
        url = f"https://graph.facebook.com/v24.0/{comment_id}/comments"
        data = {'message': reply, 'access_token': PAGE_TOKEN}
        response = requests.post(url, data=data, timeout=30)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def process_comments():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Vérification...")
    if not check_token_valid():
        print("❌ Token invalide")
        return
    comments = get_comments(limit=5)
    if not comments:
        print("📭 Aucun nouveau commentaire")
        return
    print(f"📝 {len(comments)} commentaire(s) trouvé(s)")
    for c in comments:
        print(f"💬 {c['author']}: {c['message'][:50]}...")
        reply = get_groq_response(c['message'], c['author'], c['author_id'])
        success = reply_to_comment(c['id'], reply)
        if success:
            print(f"✅ Réponse envoyée")
            mark_comment_processed(c['id'])
        else:
            print(f"❌ Échec")
    print("✅ Terminé")

def background_worker():
    while True:
        try:
            process_comments()
        except Exception as e:
            print(f"❌ Erreur: {e}")
        time.sleep(300)  # 5 minutes

# ============================================================
# 5. ROUTES FLASK (RÉPONSE INSTANTANÉE)
# ============================================================

@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "version": "3.1 - Réponse instantanée",
        "whatsapp": WHATSAPP,
        "users_in_memory": len(memory)
    })

@app.route('/ping')
def ping():
    return jsonify({"status": "alive"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/wakeup')
def wakeup():
    """Déclenche la vérification en ARRIÈRE-PLAN et retourne immédiatement."""
    threading.Thread(target=process_comments, daemon=True).start()
    return jsonify({"status": "success", "message": "Vérification lancée en arrière-plan"})

@app.route('/memory')
def view_memory():
    return jsonify({"total_users": len(memory), "memory": memory})

@app.route('/comment', methods=['POST'])
def comment():
    data = request.json
    comment = data.get('comment', '')
    author = data.get('author', 'Visiteur')
    user_id = data.get('user_id', None)
    if not comment:
        return jsonify({"error": "Commentaire vide"}), 400
    reply = get_groq_response(comment, author, user_id)
    return jsonify({"reply": reply})

# ============================================================
# 6. DÉMARRAGE
# ============================================================

if __name__ == '__main__':
    load_memory()
    load_processed()
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Assistant v3.1 - Réponse instantanée")
    print(f"📱 WhatsApp: {WHATSAPP}")
    app.run(host='0.0.0.0', port=port)
