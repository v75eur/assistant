#!/usr/bin/env python3
# ============================================================
# ASSISTANT GROQ - VERSION 4.2
# Mode Auto (analyses à 00) + Mode Cours (à 30) + Mode Libre
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

# ============================================================
# 1. CONFIGURATION
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY_1", "")
PAGE_ID = os.getenv("FB_PAGE_ID", "620580204479095")
PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN", "")
WHATSAPP = os.getenv("WHATSAPP_NUMBER", "+22960315458")

print(f"📱 WhatsApp: {WHATSAPP}")
print(f"📄 Page ID: {PAGE_ID}")

# ============================================================
# 2. SUIVI
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
# 3. PROMPTS
# ============================================================

PROMPT_COMMENTAIRE = """Tu es Rick, le fondateur de Trader123.
Tu es un trader pro depuis 8 ans. Parle comme un humain.
Termine toujours par le WhatsApp : +22960315458
Sois naturel, joyeux, accessible."""

PROMPT_COURS = """Tu es Rick, le fondateur de Trader123.
Tu vas publier un cours ou un conseil sur le trading.

Le contenu doit être :
- Éducatif et clair
- Structuré avec des points importants
- Adapté aux débutants
- Avec des conseils pratiques
- Inspirant et motivant

Sujets possibles (varie aléatoirement) :
- Les bases du trading
- Analyse technique (supports, résistances, tendances)
- Gestion des risques et money management
- Psychologie du trading
- Stratégies gagnantes
- Le trading de l'or (XAUUSD)
- Le trading des paires Forex
- Le trading de la volatilité (V75)
- Comment utiliser les bots de trading
- Développement d'assistants IA
- Conseils pour débuter en trading
- Les erreurs à éviter en trading
- La discipline en trading
- Comment lire les graphiques
- Les indicateurs techniques
- Le trading à long terme vs court terme
- Comment choisir un broker
- La diversification en trading
- Les news et leur impact sur les marchés
- Le trading automatique
"""

# ============================================================
# 4. FONCTIONS FACEBOOK
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

def publish_post(message):
    """Publie un post sur la page."""
    if not PAGE_TOKEN:
        return False
    try:
        url = f"https://graph.facebook.com/v24.0/{PAGE_ID}/feed"
        data = {'message': message, 'access_token': PAGE_TOKEN}
        r = requests.post(url, data=data, timeout=30)
        if r.status_code == 200:
            print(f"✅ Post publié !")
            return r.json()
        else:
            print(f"❌ Erreur: {r.text}")
            return None
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def get_comments():
    """Récupère les commentaires."""
    if not PAGE_TOKEN:
        return []
    
    all_comments = []
    try:
        url = f"https://graph.facebook.com/v24.0/{PAGE_ID}/feed"
        params = {
            'fields': 'id,message,comments{id,message,from{name,id}}',
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
        return all_comments
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

# ============================================================
# 5. FONCTION GROQ
# ============================================================

def groq_response(message, author, prompt_type="commentaire"):
    """Génère une réponse avec Groq selon le type."""
    if not GROQ_API_KEY:
        return f"Salut ! Contacte-moi sur WhatsApp {WHATSAPP}"
    
    prompt = PROMPT_COMMENTAIRE if prompt_type == "commentaire" else PROMPT_COURS
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Message de {author}: {message}"}
        ]
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=400 if prompt_type == "cours" else 150,
            temperature=0.9,
        )
        reply = r.choices[0].message.content
        if WHATSAPP not in reply:
            reply += f" 📱 WhatsApp : {WHATSAPP}"
        return reply
    except Exception as e:
        print(f"❌ Groq: {e}")
        return f"Salut, envoie-moi un message sur WhatsApp {WHATSAPP} 👍"

# ============================================================
# 6. GÉNÉRATION DE COURS
# ============================================================

COURS_TOPICS = [
    "Les bases du trading pour débutants",
    "Analyse technique : supports et résistances",
    "La gestion des risques en trading",
    "Psychologie du trading : garder son sang-froid",
    "Stratégies de trading gagnantes",
    "Comment trader l'or (XAUUSD)",
    "Le trading des paires Forex",
    "Le trading de la volatilité (V75)",
    "Comment utiliser les bots de trading",
    "Développer des assistants IA pour le trading",
    "Les erreurs à éviter en trading",
    "La discipline, clé du succès en trading",
    "Comment lire les graphiques en trading",
    "Les indicateurs techniques essentiels",
    "Trading à long terme vs court terme",
    "Comment choisir un broker fiable",
    "La diversification en trading",
    "Les news et leur impact sur les marchés",
    "Le trading automatique : avantages et risques",
    "Comment devenir un trader rentable",
    "Les 10 commandements du trader",
    "Comment analyser une tendance",
    "Le money management pour les traders",
    "Comment trader les annonces économiques"
]

def generate_course():
    """Génère un cours aléatoire."""
    topic = random.choice(COURS_TOPICS)
    course = groq_response(f"Crée un cours sur : {topic}", "Formation", "cours")
    return topic, course

def publish_course(custom_topic=None):
    """Publie un cours de formation."""
    print("=" * 50)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎓 PUBLICATION D'UN COURS")
    
    if not check_token():
        print("❌ Token invalide")
        return {"status": "error"}
    
    if custom_topic:
        topic = custom_topic
        course = groq_response(f"Crée un cours sur : {topic}", "Formation", "cours")
    else:
        topic, course = generate_course()
    
    # Construire le message
    msg = f"📚 FORMATION TRADING\n"
    msg += f"📖 Sujet: {topic}\n"
    msg += "=" * 40 + "\n\n"
    msg += course
    msg += "\n\n" + "=" * 40 + "\n"
    msg += f"🤖 Rick Bot - Formation\n"
    msg += f"📱 WhatsApp : {WHATSAPP}"
    
    # Publier
    result = publish_post(msg)
    if result:
        print(f"✅ Cours publié !")
        return {"status": "success", "message": "Cours publié", "topic": topic}
    else:
        return {"status": "error", "message": "Échec de la publication"}

# ============================================================
# 7. TRAITEMENT DES COMMENTAIRES
# ============================================================

def process_comments():
    """Traite les commentaires automatiquement."""
    print("=" * 50)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Traitement des commentaires")
    
    if not check_token():
        print("❌ Token invalide")
        return {"status": "error"}
    
    comments = get_comments()
    if not comments:
        print("📭 Aucun commentaire")
        return {"status": "success", "message": "Aucun commentaire", "count": 0}
    
    print(f"📝 {len(comments)} commentaire(s)")
    for c in comments:
        print(f"💬 {c['author']}: {c['message'][:30]}...")
        reply = groq_response(c['message'], c['author'], "commentaire")
        if reply_to_comment(c['id'], reply):
            processed.add(c['id'])
            save_processed()
        time.sleep(1)
    
    return {"status": "success", "message": "Terminé", "count": len(comments)}

# ============================================================
# 8. ROUTES
# ============================================================

@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "whatsapp": WHATSAPP,
        "page_id": PAGE_ID,
        "version": "4.2 - Auto + Cours (30) + Libre",
        "modes": ["auto (commentaires)", "cours (30)", "libre (à la demande)"]
    })

@app.route('/ping')
def ping():
    return jsonify({"status": "alive"})

@app.route('/wakeup')
def wakeup():
    """Mode Auto : Traite les commentaires."""
    result = process_comments()
    return jsonify(result)

@app.route('/course')
def course():
    """Mode Libre : Publie un cours aléatoire."""
    result = publish_course()
    return jsonify(result)

@app.route('/course/<topic>')
def course_topic(topic):
    """Mode Libre : Publie un cours sur un sujet spécifique."""
    result = publish_course(topic)
    return jsonify(result)

@app.route('/test')
def test():
    comments = get_comments()
    return jsonify({
        "token_valid": check_token(),
        "page_id": PAGE_ID,
        "comments_count": len(comments),
        "version": "4.2"
    })

@app.route('/reset')
def reset():
    global processed
    processed = set()
    save_processed()
    return jsonify({"status": "reset"})

# ============================================================
# 9. DÉMARRAGE
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Assistant v4.2 - Auto + Cours (30) + Libre")
    print(f"📱 WhatsApp: {WHATSAPP}")
    print(f"📚 Mode Auto (commentaires): /wakeup")
    print(f"📚 Mode Cours (30): /course (ou /course/sujet)")
    app.run(host='0.0.0.0', port=port)
