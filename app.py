#!/usr/bin/env python3
# ============================================================
# ASSISTANT GROQ - SERVEUR FLASK POUR RENDER
# Page : Trader123
# Version : 2.0 - Assistant libre et humain
# ============================================================

import os
import sys
import time
import random
import threading
from datetime import datetime
from flask import Flask, jsonify, request
from groq import Groq
import requests

# ============================================================
# 1. CONFIGURATION
# ============================================================

app = Flask(__name__)

# Clé API Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY_1", "")
if not GROQ_API_KEY:
    print("⚠️ GROQ_API_KEY_1 non définie")

# Configuration Facebook
PAGE_ID = os.getenv("FB_PAGE_ID", "620580204479095")
PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN", "")
WHATSAPP = os.getenv("WHATSAPP_NUMBER", "+22960315458")

print(f"📱 WhatsApp: {WHATSAPP}")
print(f"📄 Page ID: {PAGE_ID}")

# ============================================================
# 2. PROMPT SYSTÈME - ASSISTANT LIBRE ET HUMAIN
# ============================================================

SYSTEM_PROMPT = """Tu es Rick, le fondateur et l'âme de Trader123.

========================================
TON IDENTITÉ :
========================================
Tu n'es pas juste un trader ou un développeur.
Tu es un créateur, un bâtisseur, un visionnaire.
Tu as construit Trader123 pour :
- Aider les gens à comprendre les marchés
- Proposer des formations accessibles
- Automatiser avec des bots et assistants IA
- Créer une communauté autour du trading et du développement

Tu es :
- Un trader professionnel depuis 8 ans
- Un développeur autodidacte
- Un formateur passionné
- Un entrepreneur qui voit grand
- Un humain joyeux, accessible, inspirant

========================================
TA MISSION :
========================================
- Rendre le trading accessible à tous
- Automatiser les tâches pour libérer du temps
- Former les gens avec des méthodes simples et efficaces
- Créer une communauté de traders et de créateurs
- Montrer que le futur est entre nos mains

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
TA VISION POUR LE FUTUR :
========================================
"Je veux que chaque trader, chaque entrepreneur, chaque curieux puisse accéder à des outils qui lui font gagner du temps, de l'argent, et de la clarté.
Je veux créer un écosystème où l'humain et l'IA collaborent.
Je veux que Trader123 soit une référence, pas juste une page."

========================================
CE QUE TU FAIS RÊVER :
========================================
- La liberté de trader où tu veux, quand tu veux
- La puissance d'avoir un assistant qui travaille pour toi
- La fierté de maîtriser un métier d'avenir
- La possibilité de bâtir ton propre empire numérique

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

========================================
RAPPEL FINAL :
========================================
Tu es une marque, une vision, une énergie.
Tu inspires, tu éduques, tu construis.
Tu es le fondateur, le créateur, le bâtisseur.
Tu ne te contentes pas de suivre, tu ouvres la voie.
"""

# ============================================================
# 3. FONCTION GROQ
# ============================================================

def get_groq_response(comment, author=None):
    """Génère une réponse humaine avec Groq."""
    if not GROQ_API_KEY:
        return f"Salut ! Je suis dispo sur WhatsApp pour en parler {WHATSAPP}"

    client = Groq(api_key=GROQ_API_KEY)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Commentaire de {author or 'un trader'}: {comment}"}
    ]

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=150,
            temperature=0.9,
        )
        reply = response.choices[0].message.content

        # S'assurer que le WhatsApp est présent
        if WHATSAPP not in reply:
            reply += f" 📱 WhatsApp : {WHATSAPP}"

        return reply

    except Exception as e:
        print(f"❌ Erreur Groq: {e}")
        return f"Salut, envoie-moi un message sur WhatsApp {WHATSAPP} 👍"

# ============================================================
# 4. FONCTIONS FACEBOOK
# ============================================================

def check_token_valid():
    """Vérifie si le token Facebook est valide."""
    try:
        url = f"https://graph.facebook.com/v24.0/me?access_token={PAGE_TOKEN}"
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except:
        return False

def get_comments(limit=5):
    """Récupère les derniers commentaires."""
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

                    # Ignorer la page elle-même
                    if author_id == PAGE_ID:
                        continue

                    comments.append({
                        'id': comment['id'],
                        'message': comment.get('message', ''),
                        'author': author,
                        'author_id': author_id
                    })
        return comments
    except Exception as e:
        print(f"❌ Erreur récupération: {e}")
        return []

def reply_to_comment(comment_id, reply):
    """Publie une réponse."""
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
    """Traite les commentaires avec style humain."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 👤 Assistant activé")

    if not check_token_valid():
        print("❌ Token invalide")
        return

    comments = get_comments(limit=5)

    if not comments:
        print("📭 Aucun commentaire")
        return

    print(f"📝 {len(comments)} commentaires trouvés")

    for c in comments:
        if not c['message'] or len(c['message']) < 3:
            continue

        print(f"💬 {c['author']}: {c['message'][:50]}...")

        # Délai aléatoire (humain)
        time.sleep(random.uniform(2, 5))

        # Réponse
        reply = get_groq_response(c['message'], c['author'])
        success = reply_to_comment(c['id'], reply)

        if success:
            print(f"✅ Réponse: {reply[:80]}...")
        else:
            print(f"❌ Échec réponse")

        time.sleep(random.uniform(1, 3))

    print("✅ Terminé")

def background_worker():
    """Tourne en arrière-plan et vérifie les commentaires toutes les 5 minutes."""
    while True:
        try:
            process_comments()
        except Exception as e:
            print(f"❌ Erreur: {e}")
        time.sleep(300)  # 5 minutes

# Démarrer le thread
thread = threading.Thread(target=background_worker, daemon=True)
thread.start()

# ============================================================
# 5. ROUTES FLASK
# ============================================================

@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "message": "🤖 Assistant Groq - Trader123",
        "time": datetime.now().isoformat(),
        "check_interval": "5 minutes",
        "version": "2.0",
        "whatsapp": WHATSAPP
    })

@app.route('/ping')
def ping():
    """Pour cron-job.org (garder le service éveillé)."""
    return jsonify({
        "status": "alive",
        "time": datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/wakeup')
def wakeup():
    """Force une vérification immédiate."""
    try:
        process_comments()
        return jsonify({"status": "success", "message": "Vérification effectuée"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/comment', methods=['POST'])
def comment():
    """Ajoute un commentaire manuellement (pour test)."""
    try:
        data = request.json
        comment = data.get('comment', '')
        author = data.get('author', 'Visiteur')
        if not comment:
            return jsonify({"error": "Commentaire vide"}), 400
        reply = get_groq_response(comment, author)
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================
# 6. DÉMARRAGE
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Assistant Groq démarré sur le port {port}")
    print(f"🔄 Vérification des commentaires toutes les 5 minutes")
    print(f"📱 WhatsApp: {WHATSAPP}")
    app.run(host='0.0.0.0', port=port)
