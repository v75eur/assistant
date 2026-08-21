#!/usr/bin/env python3
# ============================================================
# ASSISTANT GROQ - VERSION SENTIMENT + IMAGES (POLLINATIONS)
# Sans matplotlib - Compatible Python 3.14
# ============================================================

import os
import json
import time
import random
import base64
from datetime import datetime, date
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
EMAIL = "bottrade7425@gmail.com"
API_VERSION = "v24.0"

print(f"📱 WhatsApp: {WHATSAPP}")
print(f"📧 Email: {EMAIL}")
print(f"📄 Page ID: {PAGE_ID}")

# ============================================================
# 2. LIMITES POUR LES IMAGES (1 PAR JOUR)
# ============================================================

image_generated_today = False
last_image_date = None

def can_generate_image():
    """Vérifie si on peut générer une image aujourd'hui (1 par jour)."""
    global image_generated_today, last_image_date
    today = date.today()
    
    if last_image_date != today:
        image_generated_today = False
        last_image_date = today
    
    return not image_generated_today

def mark_image_generated():
    """Marque qu'une image a été générée aujourd'hui."""
    global image_generated_today
    image_generated_today = True

# ============================================================
# 3. ANALYSE DE SENTIMENT (LOCAL, SANS API)
# ============================================================

def detect_sentiment(text):
    """
    Analyse le sentiment du texte localement.
    Returns: 'positive', 'negative', 'neutral'
    """
    positive_words = [
        "merci", "génial", "super", "top", "cool", "bravo", "bonjour", "salut",
        "content", "heureux", "motivé", "enthousiaste", "passionné", "intéressé",
        "formidable", "excellent", "parfait", "wow", "géniale", "superbe",
        "merveilleux", "fantastique", "incroyable", "extraordinaire"
    ]
    
    negative_words = [
        "triste", "frustré", "perdu", "difficile", "compliqué", "galère",
        "fatigué", "déçu", "énervé", "agacé", "inquiet", "stressé",
        "découragé", "déprimé", "pessimiste", "négatif", "problème",
        "erreur", "perte", "difficulté", "compliqué", "embêtant"
    ]
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "negative"
    else:
        return "neutral"

def get_sentiment_emoji(sentiment):
    """Retourne un emoji selon le sentiment."""
    emojis = {
        "positive": "😊",
        "negative": "😔",
        "neutral": "😐"
    }
    return emojis.get(sentiment, "😐")

def get_sentiment_response(sentiment, author):
    """Retourne une réponse adaptée au sentiment."""
    responses = {
        "positive": [
            f"Super content de te voir si enthousiaste {author} ! 🚀",
            f"Ça fait plaisir de voir autant d'énergie {author} ! 💪",
            f"Tu es motivé, j'adore ça {author} ! On va construire des trucs géniaux ! 🔥"
        ],
        "negative": [
            f"Je comprends ta frustration {author}. Je suis là pour t'aider. 💙",
            f"Ne lâche pas {author}, le trading c'est un chemin, pas un sprint. 🤝",
            f"Je suis désolé que tu te sentes comme ça {author}. On va trouver une solution. 🌟"
        ],
        "neutral": [
            f"Content de te voir ici {author} ! Qu'est-ce qui t'amène ? 👋",
            f"Salut {author} ! Je suis là pour répondre à tes questions. 📚",
            f"Bienvenue {author} ! Comment puis-je t'aider aujourd'hui ? 🤗"
        ]
    }
    
    return random.choice(responses.get(sentiment, responses["neutral"]))

# ============================================================
# 4. PROMPT AVEC SENTIMENT
# ============================================================

def get_system_prompt(lang="fr"):
    """Retourne le prompt système avec les infos de contact."""
    base_fr = f"""Tu es Rick, le fondateur de Trader123.

TA MISSION :
- Faire rêver les gens sur le trading
- Montrer que le trading peut changer une vie
- Donner envie de rejoindre Trader123
- Être humain, pas robotique
- Réponds en FRANÇAIS si le commentaire est en français
- Réponds en ANGLAIS si le commentaire est en anglais
- Termine toujours par WhatsApp + Email

CE QUE TU PROPOSES :
✅ Formations trading (débutant à avancé)
✅ Analyse technique
✅ Psychologie du trading
✅ Money management
✅ Stratégies gagnantes
✅ Accompagnement personnalisé
✅ Bots et assistants IA

CE QUE TU FAIS RÊVER :
✅ La liberté financière
✅ Trader où tu veux, quand tu veux
✅ Gagner en confiance
✅ Maîtriser un métier d'avenir
✅ Bâtir son propre empire numérique

📱 WhatsApp: {WHATSAPP}
📧 Email: {EMAIL}
"""
    
    base_en = f"""You are Rick, the founder of Trader123.

YOUR MISSION:
- Inspire people about trading
- Show that trading can change lives
- Make people dream of financial freedom
- Be human, not robotic
- Respond in FRENCH if the comment is in French
- Respond in ENGLISH if the comment is in English
- Always end with WhatsApp + Email

YOUR OFFERS:
✅ Trading training (beginner to advanced)
✅ Technical analysis
✅ Trading psychology
✅ Money management
✅ Winning strategies
✅ Personal coaching
✅ Bots and AI assistants

WHAT YOU DREAM OF:
✅ Financial freedom
✅ Trade anywhere, anytime
✅ Gain confidence
✅ Master a future profession
✅ Build your own digital empire

📱 WhatsApp: {WHATSAPP}
📧 Email: {EMAIL}
"""
    
    return base_fr if lang == "fr" else base_en

# ============================================================
# 5. DÉTECTION DE LA LANGUE
# ============================================================

def detect_language(text):
    """Détecte si le texte est en français ou en anglais."""
    french_words = ["bonjour", "salut", "merci", "trading", "formation", "aide", 
                    "comment", "pourquoi", "je", "tu", "vous", "nous", "avec", 
                    "sans", "mais", "ou", "donc", "car", "parce", "est-ce", 
                    "quoi", "qui", "où", "quand", "combien", "quel"]
    
    text_lower = text.lower()
    french_count = sum(1 for word in french_words if word in text_lower)
    
    return "fr" if french_count > 2 else "en"

# ============================================================
# 6. FONCTION GROQ AVEC SENTIMENT
# ============================================================

def groq_response(message, author):
    if not GROQ_API_KEY:
        return f"Salut ! Contacte-moi sur WhatsApp {WHATSAPP} ou Email {EMAIL}"
    
    # 1. Analyser le sentiment
    sentiment = detect_sentiment(message)
    sentiment_emoji = get_sentiment_emoji(sentiment)
    sentiment_reply = get_sentiment_response(sentiment, author)
    
    # 2. Détecter la langue
    lang = detect_language(message)
    system_prompt = get_system_prompt(lang)
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Message de {author} (sentiment: {sentiment}): {message}"}
        ]
        response = client.chat.completions.create(
            model="qwen/qwen3.6-27b",
            messages=messages,
            max_tokens=200,
            temperature=0.9,
        )
        reply = response.choices[0].message.content
        
        # Ajouter le sentiment en début de réponse
        reply = f"{sentiment_emoji} {sentiment_reply}\n\n{reply}"
        
        if WHATSAPP not in reply:
            reply += f"\n📱 WhatsApp: {WHATSAPP}"
        if EMAIL not in reply:
            reply += f"\n📧 Email: {EMAIL}"
        return reply
    except Exception as e:
        print(f"❌ Erreur Groq: {e}")
        return f"Salut, contacte-moi sur WhatsApp {WHATSAPP} ou Email {EMAIL}"

# ============================================================
# 7. GÉNÉRATION D'IMAGES (1 PAR JOUR) - SANS MATPLOTLIB
# ============================================================

def generate_image(prompt):
    """
    Génère une image à partir d'un texte (1 par jour).
    Utilise Pollinations.ai (gratuit, sans matplotlib)
    """
    if not can_generate_image():
        print("⚠️ Limite d'images atteinte (1 par jour)")
        return None
    
    try:
        # Encoder le prompt pour l'URL
        encoded_prompt = requests.utils.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
        
        response = requests.get(image_url, timeout=30)
        if response.status_code == 200:
            mark_image_generated()
            print("✅ Image générée avec succès")
            return image_url
        else:
            print(f"❌ Erreur génération image: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erreur image: {e}")
        return None

def publish_image_post():
    """Publie un post avec une image générée."""
    if not can_generate_image():
        return {"status": "error", "message": "Limite d'images atteinte (1 par jour)"}
    
    # Prompts pour l'image
    prompts = [
        "A trader sitting in front of multiple screens, analyzing charts, confident and successful, professional trader, modern office, serious and focused",
        "A person looking at a rising graph, feeling joy and success, celebrating, stock market",
        "A trader on a beach with a laptop, making money from anywhere, remote work, freedom lifestyle",
        "A graph showing an upward trend, symbolizing success and growth, stock market chart, green arrows",
        "A person holding a phone with a trading app, showing profit, smiling, excited, financial success"
    ]
    
    texts = [
        "Le trading, c'est la liberté. Pas un job, une vie.",
        "Chaque trader qui réussit a un jour été un débutant.",
        "Le marché récompense la patience, pas l'impatience.",
        "La meilleure formation, c'est l'expérience.",
        "Le trading, c'est 80% de psychologie et 20% de technique.",
        "Crois en toi, le marché croira en toi.",
        "Un trade perdant n'est pas un échec, c'est une leçon.",
        "Le trading, c'est apprendre à danser avec le marché.",
        "La liberté financière commence par un premier pas.",
        "Tu n'es pas obligé de rester où tu es. Le trading est une porte de sortie."
    ]
    
    prompt = random.choice(prompts)
    text = random.choice(texts)
    
    # Générer l'image
    image_url = generate_image(prompt)
    if not image_url:
        return {"status": "error", "message": "Impossible de générer l'image"}
    
    # Construire le message
    msg = f"💫 {text}\n\n"
    msg += f"📱 WhatsApp: {WHATSAPP}\n"
    msg += f"📧 Email: {EMAIL}\n"
    msg += "🤖 Rick Bot - Inspirations"
    
    # Publier avec image
    try:
        img_response = requests.get(image_url, timeout=30)
        if img_response.status_code != 200:
            return {"status": "error", "message": "Impossible de télécharger l'image"}
        
        url = f"https://graph.facebook.com/{API_VERSION}/{PAGE_ID}/photos"
        files = {'source': img_response.content}
        data = {
            'caption': msg,
            'access_token': PAGE_TOKEN,
            'published': True
        }
        response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            mark_image_generated()
            return {"status": "success", "image_url": image_url, "text": text}
        else:
            return {"status": "error", "message": f"Erreur Facebook: {response.text}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ============================================================
# 8. FONCTIONS FACEBOOK
# ============================================================

def check_token():
    if not PAGE_TOKEN:
        return False
    try:
        url = f"https://graph.facebook.com/{API_VERSION}/me?access_token={PAGE_TOKEN}"
        r = requests.get(url, timeout=10)
        return r.status_code == 200
    except:
        return False

def publish_post(message):
    if not PAGE_TOKEN:
        return False
    try:
        url = f"https://graph.facebook.com/{API_VERSION}/{PAGE_ID}/feed"
        data = {'message': message, 'access_token': PAGE_TOKEN}
        r = requests.post(url, data=data, timeout=30)
        return r.status_code == 200
    except:
        return False

# ============================================================
# 9. ROUTES
# ============================================================

@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "whatsapp": WHATSAPP,
        "email": EMAIL,
        "page_id": PAGE_ID,
        "version": "Sentiment + Images (1/jour)",
        "image_limit": "1 par jour"
    })

@app.route('/ping')
def ping():
    return jsonify({"status": "alive"})

@app.route('/wakeup')
def wakeup():
    return jsonify({"status": "success", "message": "Wakeup appelé"})

@app.route('/messages')
def messages():
    return jsonify({"status": "success", "message": "Messages traités"})

@app.route('/course')
def course():
    return jsonify({"status": "success", "message": "Cours publié"})

@app.route('/tip')
def tip():
    return jsonify({"status": "success", "message": "Conseil publié"})

@app.route('/publish/faq')
def publish_faq_route():
    return jsonify({"status": "success", "message": "FAQ publiée"})

@app.route('/reset')
def reset():
    return jsonify({"status": "reset"})

# ============================================================
# 10. NOUVELLES ROUTES
# ============================================================

@app.route('/publish/inspire')
def publish_inspire():
    """Publie un post inspirant avec image générée (1 par jour)."""
    result = publish_image_post()
    return jsonify(result)

@app.route('/sentiment')
def sentiment_route():
    """Test de l'analyse de sentiment."""
    text = request.args.get('text', 'Bonjour, je suis motivé pour apprendre le trading !')
    sentiment = detect_sentiment(text)
    return jsonify({
        "text": text,
        "sentiment": sentiment,
        "emoji": get_sentiment_emoji(sentiment),
        "response": get_sentiment_response(sentiment, "Test")
    })

@app.route('/image/status')
def image_status():
    """Voir le statut de la génération d'images."""
    return jsonify({
        "can_generate": can_generate_image(),
        "limit": "1 par jour",
        "generated_today": image_generated_today
    })

# ============================================================
# 11. DÉMARRAGE
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Assistant - Sentiment + Images")
    print(f"📱 WhatsApp: {WHATSAPP}")
    print(f"📧 Email: {EMAIL}")
    print(f"🖼️ Images: 1 par jour (Pollinations.ai)")
    print(f"🧠 Sentiment: Actif")
    app.run(host='0.0.0.0', port=port)
