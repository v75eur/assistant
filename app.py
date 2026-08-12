#!/usr/bin/env python3
# ============================================================
# ASSISTANT GROQ - SERVEUR FLASK POUR RENDER
# Version : 3.1 - Réponse rapide (sans délai artificiel)
# ============================================================

import os
import sys
import time
import random
import threading
import json
from datetime import datetime, timedelta
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
# 2. MÉMOIRE DES CONVERSATIONS
# ============================================================

memory = {}
MEMORY_FILE = "/tmp/assistant_memory.json"
MAX_HISTORY = 10

def load_memory():
    global memory
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r') as f:
                memory = json.load(f)
    except Exception as e:
        print(f"⚠️ Erreur chargement mémoire: {e}")

def save_memory():
    try:
        with open(MEMORY_FILE, 'w') as f:
            json.dump(memory, f)
    except Exception as e:
        print(f"⚠️ Erreur sauvegarde mémoire: {e}")

def get_user_memory(user_id, user_name=None):
    if user_id not in memory:
        memory[user_id] = {
            "name": user_name or "Visiteur",
            "history": [],
            "last_seen": datetime.now().isoformat(),
            "last_comment": ""
        }
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
    
    memory[user_id]["history"].append({
        "time": datetime.now().isoformat(),
        "user": comment,
        "assistant": reply
    })
    
    if len(memory[user_id]["history"]) > MAX_HISTORY:
        memory[user_id]["history"] = memory[user_id]["history"][-MAX_HISTORY:]
    
    save_memory()

def build_context(user_id):
    user_data = get_user_memory(user_id)
    history = user_data.get("history", [])
    
    if not history:
        return None
    
    context = "Historique de la conversation avec cet utilisateur :\n"
    for entry in history[-5:]:
        context += f"- Utilisateur : {entry['user']}\n"
        context += f"- Réponse : {entry['assistant']}\n"
    
    return context

# ============================================================
# 3. ANTI-DOUBLON
# ============================================================

processed_comments = set()
PROCESSED_FILE = "/tmp/processed_comments.json"

def load_processed():
    global processed_comments
    try:
        if os.path.exists(PROCESSED_FILE):
            with open(PROCESSED_FILE, 'r') as f:
                processed_comments = set(json.load(f))
    except Exception as e:
        print(f"⚠️ Erreur chargement processed: {e}")

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

# ============================================================
# 4. PROMPT SYSTÈME
# ============================================================

BASE_SYSTEM_PROMPT = """Tu es Rick, le fondateur et l'âme de Trader123.

========================================
TON IDENTITÉ :
========================================
Tu es un créateur, un bâtisseur, un visionnaire.
Tu as construit Trader123 pour aider les gens à comprendre les marchés, proposer des formations, et automatiser avec des bots et assistants IA.

Tu es :
- Un trader professionnel depuis 8 ans
- Un développeur autodidacte
- Un formateur passionné
- Un entrepreneur qui voit grand
- Un humain joyeux, accessible, inspirant

========================================
TON STYLE D'ÉCRITURE :
========================================
- Naturel, chaleureux, sans filtre
- Expressions : "tu vois", "en vrai", "franchement", "du coup"
- Fautes de frappe (1-2 par message)
- Léger, joyeux, positif
- Inspirant, motivant, ambitieux

========================================
CE QUE TU PROPOSES :
========================================
✅ Bots Forex (automatisation, analyses 24h/24)
✅ Assistants IA (réponse humaine, gestion de communauté)
✅ Formations trading (débutant à avancé)
✅ Accompagnement personnalisé
✅ Développement sur mesure (bots, sites, assistants)

========================================
CE QUE TU NE FAIS PAS :
========================================
❌ Promettre des gains financiers garantis
❌ Donner des conseils financiers précis sans contexte
❌ Être négatif, triste, agressif
❌ Insulter ou rabaisser
❌ Faire du spam ou de la publicité forcée

========================================
COMMENT TU FINIS :
========================================
- "📱 WhatsApp : +22960315458"
- "On construit ensemble ? WhatsApp +22960315458"
- "Viens en privé, je te montre ce que je prépare +22960315458"
- "Hésite pas, je réponds toujours +22960315458"
"""

def get_system_prompt(user_id):
    context = build_context(user_id)
    
    if context:
        return BASE_SYSTEM_PROMPT + "\n\n========================================\nCONTEXTE DE LA CONVERSATION :\n" + context + "\n========================================\n\nUtilise ce contexte pour personnaliser ta réponse. Si l'utilisateur a déjà posé des questions, fais référence à ses précédents échanges pour montrer que tu te souviens de lui."
    
    return BASE_SYSTEM_PROMPT

# ============================================================
# 5. FONCTIONS GROQ ET FACEBOOK
# ============================================================

def get_groq_response(comment, author, user_id=None):
    """Génère une réponse humaine avec Groq et contexte."""
    if not GROQ_API_KEY:
        return f"Salut ! Je suis dispo sur WhatsApp pour en parler {WHATSAPP}"

    user_data = get_user_memory(user_id, author) if user_id else None
    
    client = Groq(api_key=GROQ_API_KEY)
    system_prompt = get_system_prompt(user_id) if user_id else BASE_SYSTEM_PROMPT

    messages = [
        {"role": "system", "content": system_prompt},
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
        
        if user_id:
            update_user_memory(user_id, comment, reply)
        
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
        params = {
            'fields': 'id,message,comments{id,message,from{name,id}}',
            'limit': limit,
            'access_token': PAGE_TOKEN
        }
        response = requests.get(url, params=params, timeout=30)
        data = response.json()

        comments = []
        for post in data.get('data', []):
            if 'comments' in post:
                for comment in post['comments'].get('data', []):
                    author = comment.get('from', {}).get('name', 'Inconnu')
                    author_id = comment.get('from', {}).get('id', '')
                    comment_id = comment.get('id', '')

                    if author_id == PAGE_ID:
                        continue

                    if is_comment_processed(comment_id):
                        continue

                    comments.append({
                        'id': comment_id,
                        'message': comment.get('message', ''),
                        'author': author,
                        'author_id': author_id
                    })
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
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def process_comments():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 👤 Assistant activé")

    if not check_token_valid():
        print("❌ Token invalide")
        return

    comments = get_comments(limit=5)

    if not comments:
        print("📭 Aucun nouveau commentaire")
        return

    print(f"📝 {len(comments)} nouveau(x) commentaire(s) trouvé(s)")

    for c in comments:
        if not c['message'] or len(c['message']) < 3:
            continue

        print(f"💬 {c['author']}: {c['message'][:50]}...")

        # PAS DE DÉLAI ! Réponse instantanée
        reply = get_groq_response(c['message'], c['author'], c['author_id'])
        success = reply_to_comment(c['id'], reply)

        if success:
            print(f"✅ Réponse: {reply[:80]}...")
            mark_comment_processed(c['id'])
        else:
            print(f"❌ Échec réponse")

        # Pas de pause entre les commentaires non plus

    print("✅ Terminé")

def background_worker():
    while True:
        try:
            process_comments()
        except Exception as e:
            print(f"❌ Erreur: {e}")
        time.sleep(300)  # 5 minutes

# Charger la mémoire au démarrage
load_memory()
load_processed()

# Démarrer le thread
thread = threading.Thread(target=background_worker, daemon=True)
thread.start()

# ============================================================
# 6. ROUTES FLASK
# ============================================================

@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "message": "🤖 Assistant Groq - Trader123",
        "time": datetime.now().isoformat(),
        "check_interval": "5 minutes",
        "version": "3.1 - Réponse rapide",
        "whatsapp": WHATSAPP,
        "users_in_memory": len(memory)
    })

@app.route('/ping')
def ping():
    return jsonify({"status": "alive", "time": datetime.now().isoformat()})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/wakeup')
def wakeup():
    try:
        process_comments()
        return jsonify({"status": "success", "message": "Vérification effectuée"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/memory')
def view_memory():
    return jsonify({
        "total_users": len(memory),
        "memory": memory
    })

@app.route('/clear_memory')
def clear_memory():
    global memory
    memory = {}
    save_memory()
    return jsonify({"status": "success", "message": "Mémoire effacée"})

@app.route('/comment', methods=['POST'])
def comment():
    try:
        data = request.json
        comment = data.get('comment', '')
        author = data.get('author', 'Visiteur')
        user_id = data.get('user_id', None)
        if not comment:
            return jsonify({"error": "Commentaire vide"}), 400
        reply = get_groq_response(comment, author, user_id)
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================
# 7. DÉMARRAGE
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Assistant Groq v3.1 démarré sur le port {port}")
    print(f"🔄 Vérification des commentaires toutes les 5 minutes")
    print(f"📱 WhatsApp: {WHATSAPP}")
    print(f"🧠 Mémoire chargée: {len(memory)} utilisateurs")
    app.run(host='0.0.0.0', port=port)
