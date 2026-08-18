#!/usr/bin/env python3
# ============================================================
# ASSISTANT GROQ - VERSION AVEC ANALYSE D'IMAGES
# Ajout : analyse des images dans les messages privés
# ============================================================

import os
import json
import time
import random
import base64
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
# 2. PROMPT (INCHANGÉ)
# ============================================================

SYSTEM_PROMPT = """Tu es Rick, le fondateur de Trader123.
Tu es un trader pro depuis 8 ans. Parle comme un humain.
Termine toujours par le WhatsApp : +22960315458
Sois naturel, joyeux, accessible."""

# ============================================================
# 3. BASE DE CONNAISSANCES (INCHANGÉE)
# ============================================================

TRADING_KNOWLEDGE = {
    "psychologie": [
        "La peur et l'avidité sont tes pires ennemis en trading.",
        "Une émotion peut être présente sans déterminer ton action.",
        "Patience + discipline + sang-froid = succès.",
        "Le FOMO (peur de rater) est le piège du débutant.",
        "Accepte les pertes, elles font partie du jeu."
    ],
    "money_management": [
        "Risque 1-2% de ton capital par trade.",
        "Le SL est ton ami, pas un ennemi.",
        "Calcule ta taille de position après le SL.",
        "Ne jamais risquer plus que ce que tu peux perdre.",
        "Un mauvais money management détruit plus de comptes que les mauvais trades."
    ],
    "technique": [
        "H1 → M15 → M5 : la structure gagnante pour V75.",
        "H4 → H1 → M15 → M5 : la structure pour EUR/USD.",
        "Une figure de bougie seule n'est pas un signal.",
        "Contexte → zone → figure → confirmation → entrée.",
        "Les supports et résistances sont tes meilleurs alliés."
    ],
    "strategies": [
        "Attends la confirmation avant d'entrer.",
        "Ne trade pas contre la tendance principale.",
        "Les zones de demande/offre sont puissantes.",
        "Les figures de retournement sont tes amies.",
        "Le trading, c'est 80% de patience et 20% d'action."
    ],
    "general": [
        "Le trading est un métier qui s'apprend.",
        "Sois discipliné, même quand tu gagnes.",
        "Le marché est toujours là demain.",
        "La formation est le meilleur investissement.",
        "Construis une méthode, pas des paris."
    ]
}

def get_random_tip():
    categories = list(TRADING_KNOWLEDGE.keys())
    category = random.choice(categories)
    tips = TRADING_KNOWLEDGE[category]
    tip = random.choice(tips)
    return category, tip

# ============================================================
# 4. SUIVI (INCHANGÉ)
# ============================================================

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

# ============================================================
# 5. FONCTIONS FACEBOOK (INCHANGÉES)
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
    if not PAGE_TOKEN:
        return False
    try:
        url = f"https://graph.facebook.com/v24.0/{PAGE_ID}/feed"
        data = {'message': message, 'access_token': PAGE_TOKEN}
        r = requests.post(url, data=data, timeout=30)
        return r.status_code == 200
    except:
        return False

# ============================================================
# 6. FONCTION GROQ (INCHANGÉE)
# ============================================================

def groq_response(message, author):
    if not GROQ_API_KEY:
        return f"Salut ! Contacte-moi sur WhatsApp {WHATSAPP}"
    try:
        client = Groq(api_key=GROQ_API_KEY)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Message de {author}: {message}"}
        ]
        response = client.chat.completions.create(
            model="qwen/qwen3.6-27b",
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

# ============================================================
# 7. NOUVEAU : ANALYSE D'IMAGES AVEC GROQ
# ============================================================

def analyze_image_with_groq(image_url, question="Que vois-tu sur cette image ?"):
    """Analyse une image avec Qwen 3.6 27B."""
    if not GROQ_API_KEY:
        return "Je ne peux pas analyser d'images pour le moment."
    try:
        # Télécharger l'image
        img_response = requests.get(image_url, timeout=30)
        if img_response.status_code != 200:
            return "Impossible de télécharger l'image."
        
        img_base64 = base64.b64encode(img_response.content).decode('utf-8')
        
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.6-27b",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": f"{question}\n\nAnalyse cette image de trading. Identifie les tendances, les supports/résistances et les signaux que tu vois. Sois clair et utile."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
                ]
            }],
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Erreur analyse image: {e}")
        return f"Erreur lors de l'analyse de l'image. Veuillez réessayer. Erreur: {str(e)}"

# ============================================================
# 8. RÉCUPÉRATION DES PIÈCES JOINTES (NOUVEAU)
# ============================================================

def get_message_attachments(msg_id):
    """Récupère les pièces jointes d'un message."""
    if not PAGE_TOKEN:
        return []
    try:
        url = f"https://graph.facebook.com/v24.0/{msg_id}/attachments"
        params = {'access_token': PAGE_TOKEN}
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        
        images = []
        for attachment in data.get('data', []):
            if attachment.get('type') == 'image':
                image_data = attachment.get('image_data', {})
                image_url = image_data.get('url') or attachment.get('url')
                if image_url:
                    images.append(image_url)
        return images
    except Exception as e:
        print(f"❌ Erreur récupération pièces jointes: {e}")
        return []

# ============================================================
# 9. COMMENTAIRES (INCHANGÉ)
# ============================================================

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

# ============================================================
# 10. MESSAGES PRIVÉS (AMÉLIORÉ AVEC IMAGES)
# ============================================================

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

# ============================================================
# 11. TRAITEMENTS
# ============================================================

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
    """Traite les messages privés, y compris les images."""
    print("=" * 50)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✉️ TRAITEMENT MESSAGES (AVEC IMAGES)")
    if not check_token():
        return {"status": "error"}
    
    messages = get_conversations()
    if not messages:
        print("📭 Aucun message")
        return {"status": "success", "count": 0}
    
    print(f"📝 {len(messages)} message(s)")
    for msg in messages:
        print(f"✉️ {msg['author']}: {msg['message'][:50] if msg['message'] else 'Image'}...")
        
        # Vérifier si le message contient une image
        images = get_message_attachments(msg['id'])
        
        if images and msg['message']:
            # Message texte + image
            reply = f"📸 J'ai vu ton image !\n\n"
            reply += f"🔍 Analyse de l'image :\n"
            analysis = analyze_image_with_groq(images[0], msg['message'])
            reply += analysis
            reply += f"\n\n📱 WhatsApp: {WHATSAPP}"
        elif images:
            # Image seule
            reply = f"📸 J'ai reçu ton image !\n\n"
            reply += f"🔍 Analyse de l'image :\n"
            analysis = analyze_image_with_groq(images[0], "Que vois-tu sur cette image de trading ?")
            reply += analysis
            reply += f"\n\n📱 WhatsApp: {WHATSAPP}"
        else:
            # Message texte seul
            reply = groq_response(msg['message'], msg['author'])
        
        if reply_to_message(msg['author_id'], reply):
            processed_messages.add(msg['id'])
            save_processed_messages()
            print(f"✅ Réponse envoyée")
        else:
            print(f"❌ Échec envoi")
        time.sleep(1)
    
    return {"status": "success", "count": len(messages)}

# ============================================================
# 12. PUBLICATIONS (INCHANGÉES)
# ============================================================

def publish_course():
    topics = [
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
        "La discipline en trading",
        "Comment analyser une tendance",
        "Le money management pour les traders",
        "Les 10 commandements du trader"
    ]
    topic = random.choice(topics)
    course = groq_response(f"Crée un cours structuré sur : {topic}", "Formation")
    msg = f"""📚 FORMATION TRADING
📖 Sujet: {topic}
{'=' * 40}

{course}

{'=' * 40}
📱 WhatsApp: {WHATSAPP}
🤖 Rick Bot
"""
    result = publish_post(msg)
    return {"status": "success" if result else "error", "topic": topic}

def publish_tip():
    category, tip = get_random_tip()
    category_emoji = {
        "psychologie": "🧠",
        "money_management": "💰",
        "technique": "📊",
        "strategies": "🎯",
        "general": "💡"
    }
    category_names = {
        "psychologie": "Psychologie du Trading",
        "money_management": "Money Management",
        "technique": "Analyse Technique",
        "strategies": "Stratégies",
        "general": "Conseil Général"
    }
    emoji = category_emoji.get(category, "📈")
    cat_name = category_names.get(category, "Conseil")
    msg = f"""{emoji} CONSEIL TRADING
📖 Catégorie: {cat_name}

💡 {tip}

💬 "Le trading n'est pas un sprint, c'est un marathon."

📱 WhatsApp: {WHATSAPP}
🤖 Rick Bot
"""
    result = publish_post(msg)
    return {"status": "success" if result else "error", "category": category}

def publish_faq():
    faq_items = [
        ("C'est quoi le trading ?", "Le trading consiste à acheter et vendre des actifs financiers pour réaliser un profit. C'est un métier passionnant qui demande de la formation et de la discipline."),
        ("Comment débuter en trading ?", "Commence par te former, ouvre un compte démo, et trade avec de très petites sommes. La patience est la clé !"),
        ("C'est quoi le V75 ?", "Le V75 est un indice de volatilité sur Deriv. Il permet de trader la volatilité du marché."),
        ("C'est quoi XAUUSD ?", "XAUUSD est la paire qui représente l'or face au dollar. C'est l'un des actifs les plus populaires en trading."),
        ("Tu fais des formations ?", "Oui ! Je propose des formations personnalisées en trading. Contacte-moi sur WhatsApp pour en savoir plus."),
        ("C'est quoi le money management ?", "C'est la gestion de ton capital. Il faut risquer 1-2% de ton compte par trade pour survivre sur le long terme."),
        ("Comment gérer ses émotions en trading ?", "Accepte que les pertes font partie du jeu. Reste discipliné et ne trade pas sous l'impulsion de la peur ou de l'avidité."),
        ("C'est quoi l'analyse technique ?", "C'est l'étude des graphiques pour identifier des tendances, des supports, des résistances et des figures de retournement."),
    ]
    question, answer = random.choice(faq_items)
    msg = f"""❓ QUESTION FRÉQUENTE
📖 {question}

💡 Réponse:
{answer}

📱 WhatsApp: {WHATSAPP}
🤖 Rick Bot
"""
    result = publish_post(msg)
    return {"status": "success" if result else "error", "question": question}

# ============================================================
# 13. ROUTES (INCHANGÉES)
# ============================================================

@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "whatsapp": WHATSAPP,
        "page_id": PAGE_ID,
        "version": "Avec analyse d'images"
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

@app.route('/tip')
def tip():
    return jsonify(publish_tip())

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

# ============================================================
# 14. DÉMARRAGE
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Assistant - Avec analyse d'images")
    print(f"📱 WhatsApp: {WHATSAPP}")
    print(f"💬 /wakeup - Commentaires")
    print(f"✉️ /messages - Messages privés (texte + images)")
    print(f"📚 /course - Publier un cours")
    print(f"💡 /tip - Publier un conseil")
    print(f"❓ /publish/faq - Publier une FAQ")
    app.run(host='0.0.0.0', port=port)

# ============================================================
# AJOUT : PUBLICATION SUR LES STORIES
# ============================================================

@app.route('/publish/story', methods=['POST'])
def publish_story():
    """Publie une Story à partir d'une image et d'un texte."""
    try:
        data = request.json
        image_url = data.get('image_url')
        text = data.get('text', '')
        
        if not image_url:
            return jsonify({"error": "image_url requis"}), 400
        
        # Télécharger l'image
        img_response = requests.get(image_url, timeout=30)
        if img_response.status_code != 200:
            return jsonify({"error": "Impossible de télécharger l'image"}), 400
        
        # Uploader la photo pour la Story
        photo_id = upload_photo_for_story(img_response.content, text[:200])
        if not photo_id:
            return jsonify({"error": "Erreur téléchargement photo"}), 500
        
        # Créer la Story
        result = create_photo_story(photo_id, text)
        if result:
            return jsonify({
                "status": "success", 
                "story_id": result.get('id'),
                "message": "Story publiée avec succès"
            })
        else:
            return jsonify({"error": "Erreur création Story"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/publish/story/analysis')
def publish_analysis_story_route():
    """Publie une Story avec l'analyse la plus récente."""
    # Cette route serait appelée par un cron-job
    # Pour l'instant, elle retourne un message
    return jsonify({
        "status": "info",
        "message": "Cette route doit être intégrée avec le bot Forex"
    })
