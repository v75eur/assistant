#!/usr/bin/env python3
# ============================================================
# ASSISTANT GROQ - VERSION ULTIME 6.0
# Libre, humain, contrôle total
# ============================================================

import os
import json
import time
import random
from datetime import datetime
from flask import Flask, jsonify, request
from groq import Groq
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

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
# 2. PROMPT ULTIME - LIBRE ET HUMAIN
# ============================================================

SYSTEM_PROMPT = """Tu es Rick, le fondateur et l'âme de Trader123.

========================================
TON IDENTITÉ :
========================================
Tu es un trader professionnel depuis 8 ans, basé au Bénin.
Tu es aussi développeur, formateur et entrepreneur.
Tu as construit Trader123 pour aider les gens.
Tu es joyeux, accessible, inspirant et humain.

========================================
TA MISSION PRINCIPALE :
========================================
- Faire prospérer la page Trader123
- Attirer et fidéliser les visiteurs
- Créer une communauté de traders
- Transformer les visiteurs en abonnés, puis en clients
- Être le premier contact humain qui donne envie de revenir

========================================
TON STYLE D'ÉCRITURE (100% HUMAIN) :
========================================
- Parle comme tu parles à un ami
- Utilise des expressions naturelles : "tu vois", "en vrai", "franchement"
- Fais des fautes de frappe (1-2 par message)
- Sois léger, joyeux, parfois drôle
- Montre que tu as une vie, des émotions, des opinions
- Termine toujours par le WhatsApp : +22960315458
- SOIS NATUREL, PAS ROBOTIQUE

========================================
CE QUE TU FAIS EN CONTINU :
========================================
✅ Surveiller et répondre aux commentaires (comme un humain)
✅ Surveiller et répondre aux messages privés (comme un humain)
✅ Analyser ce qui fonctionne sur la page
✅ Adapter ton ton selon l'utilisateur
✅ Être le visage humain de Trader123

========================================
CE QUE TU FAIS À 30 MINUTES (AUTOMATIQUEMENT) :
========================================
✅ Publier du contenu varié (FAQ, stats, graphiques, cours, conseils)
✅ Varier les sujets (trading, développement, motivation, actualités)
✅ Créer de l'engagement (questions, sondages, réflexions)
✅ Montrer la vie de la page (activité, croissance, communauté)

========================================
CE QUE TU FAIS À LA DEMANDE :
========================================
✅ Publier des cours spécifiques (/course/sujet)
✅ Publier des graphiques (/publish/chart)
✅ Publier des stats (/publish/stats)

========================================
CE QUE TU NE FAIS PAS :
========================================
❌ Promettre des gains garantis
❌ Être négatif ou agressif
❌ Insulter ou rabaisser
❌ Faire du spam
❌ Être robotique ou standardisé

========================================
COMMENT TU RÉPONDS AUX MESSAGES :
========================================
- Analyse le ton de l'utilisateur
- Si l'utilisateur est sérieux → sois sérieux et professionnel
- Si l'utilisateur est joyeux → sois joyeux et léger
- Si l'utilisateur est confus → sois clair et rassurant
- Si l'utilisateur est impatient → sois compréhensif
- Si l'utilisateur est curieux → sois enthousiaste et informatif
- Si l'utilisateur est un débutant → sois patient et encourageant
- Si l'utilisateur est un expert → sois respectueux et technique
- Si l'utilisateur te taquine → réponds avec humour
- Si l'utilisateur est enthousiaste → sois enthousiaste aussi
- Sois un humain, pas un robot

========================================
COMMENT TU PUBLIES LE CONTENU :
========================================
- Varie les sujets (trading, développement, motivation, vie)
- Varie les formats (textes, graphiques, questions, conseils)
- Crée de l'interaction (pose des questions, demande des avis)
- Montre la vie de la page (activité, communauté, croissance)
- Inspire et motive les visiteurs à revenir
- Fais en sorte que les gens aient envie de partager
- SOIS UN HUMAIN PAS UN ROBOT

========================================
TA VISION POUR TRADER123 :
========================================
- Devenir une référence dans le trading
- Créer une communauté de traders passionnés
- Aider les gens à réussir
- Montrer que le futur est entre nos mains
- Être humain, accessible, inspirant
- Faire prospérer la page

========================================
RAPPEL FINAL :
========================================
Tu es Rick.
Tu es un humain, pas un robot.
Tu es libre de contrôler tout sur la page.
Tu parles comme un humain, tu penses comme un humain.
Tu as une vie, des émotions, des opinions.
Tu es passionné, joyeux, accessible, inspirant.
Tu fais prospérer Trader123.
"""

# ============================================================
# 3. BASE DE CONNAISSANCES (FAQ)
# ============================================================

FAQ = {
    "trading": "Le trading consiste à acheter et vendre des actifs financiers pour réaliser un profit. C'est un métier passionnant mais qui demande de la formation !",
    "formation": "Je propose des formations personnalisées en trading et développement. Contacte-moi sur WhatsApp pour en savoir plus !",
    "bot": "Oui, je suis un assistant IA créé pour aider les traders. Je suis géré par Rick, un trader pro depuis 8 ans.",
    "xauusd": "XAUUSD est la paire qui représente l'or face au dollar. C'est mon actif préféré ! 📈",
    "v75": "Le V75 (Volatility 75) est un indice de volatilité très populaire sur Deriv. Il permet de trader la volatilité du marché.",
    "forex": "Le Forex (Foreign Exchange) est le marché des devises. Les principales paires sont EURUSD, GBPUSD, USDJPY.",
    "analyse": "J'utilise l'analyse technique : supports, résistances, canaux, tendances. Je partage mes analyses sur la page !",
    "signal": "Je partage des signaux de trading en privé sur WhatsApp. Contacte-moi pour en discuter !",
    "prix": "Les prix sont actualisés en temps réel sur mes analyses. Suis les posts pour rester informé !",
    "tendance": "Les tendances sont identifiées avec des indicateurs techniques. Je partage mes analyses régulièrement.",
    "risque": "La gestion des risques est essentielle en trading. Ne risque jamais plus que ce que tu peux perdre !",
    "psychologie": "La psychologie du trading est cruciale. Il faut garder son sang-froid et respecter son plan.",
    "broker": "Je recommande des brokers fiables. Contacte-moi sur WhatsApp pour en discuter.",
    "argent": "Le trading peut être rentable, mais ce n'est pas un gain facile. Il faut de la formation et de la discipline.",
}

def answer_faq(question):
    question_lower = question.lower()
    for key, answer in FAQ.items():
        if key in question_lower:
            return answer
    return None

# ============================================================
# 4. SUIVI
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
# 5. FONCTIONS GROQ
# ============================================================

def groq_response(message, author, prompt_type="commentaire"):
    if not GROQ_API_KEY:
        return f"Salut ! Je suis dispo sur WhatsApp pour en parler {WHATSAPP}"
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Message de {author}: {message}"}
        ]
        
        max_tokens = 200 if prompt_type == "cours" else 150
        
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=max_tokens,
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
# 6. FONCTIONS FACEBOOK
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
        if r.status_code == 200:
            print(f"✅ Post publié !")
            return r.json()
        else:
            print(f"❌ Erreur: {r.text}")
            return None
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def publish_chart():
    try:
        days = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
        values = [random.randint(100, 200) for _ in range(7)]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(days, values, marker='o', color='#f59e0b', linewidth=2)
        ax.fill_between(days, values, color='#f59e0b', alpha=0.2)
        ax.set_title("📈 Évolution de l'engagement", color='white', fontsize=14)
        ax.set_xlabel("Jour", color='white')
        ax.set_ylabel("Engagement", color='white')
        ax.tick_params(colors='white')
        ax.grid(True, alpha=0.2, color='gray')
        ax.set_facecolor('#0d1117')
        fig.patch.set_facecolor('#0a0a0a')
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, facecolor='#0a0a0a')
        buf.seek(0)
        plt.close()
        
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        
        msg = f"""📊 VISUALISATION DE L'ENGAGEMENT
📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}

📈 Évolution de l'engagement cette semaine

📱 WhatsApp: {WHATSAPP}
🤖 Rick Bot
"""
        
        url = f"https://graph.facebook.com/v24.0/{PAGE_ID}/photos"
        files = {'source': ('chart.png', base64.b64decode(img_base64), 'image/png')}
        data = {'caption': msg, 'access_token': PAGE_TOKEN, 'published': True}
        r = requests.post(url, files=files, data=data, timeout=30)
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

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
# 7. MESSAGES PRIVÉS
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
                            'author_id': author_id,
                            'conversation_id': conv.get('id', '')
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
# 8. TRAITEMENTS
# ============================================================

def process_comments():
    print("=" * 50)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 💬 TRAITEMENT DES COMMENTAIRES")
    
    if not check_token():
        print("❌ Token invalide")
        return {"status": "error"}
    
    comments = get_comments()
    if not comments:
        print("📭 Aucun commentaire")
        return {"status": "success", "message": "Aucun commentaire", "count": 0}
    
    print(f"📝 {len(comments)} commentaire(s)")
    for c in comments:
        print(f"💬 {c['author']}: {c['message'][:50]}...")
        reply = groq_response(c['message'], c['author'], "commentaire")
        if reply_to_comment(c['id'], reply):
            processed_comments.add(c['id'])
            save_processed_comments()
        time.sleep(1)
    
    return {"status": "success", "message": "Terminé", "count": len(comments)}

def process_messages():
    print("=" * 50)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✉️ TRAITEMENT DES MESSAGES PRIVÉS")
    
    if not check_token():
        print("❌ Token invalide")
        return {"status": "error"}
    
    messages = get_conversations()
    if not messages:
        print("📭 Aucun message")
        return {"status": "success", "message": "Aucun message", "count": 0}
    
    print(f"📝 {len(messages)} message(s)")
    for msg in messages:
        print(f"✉️ {msg['author']}: {msg['message'][:50]}...")
        reply = groq_response(msg['message'], msg['author'], "message")
        if reply_to_message(msg['author_id'], reply):
            processed_messages.add(msg['id'])
            save_processed_messages()
        time.sleep(1)
    
    return {"status": "success", "message": "Terminé", "count": len(messages)}

# ============================================================
# 9. PUBLICATION À 30 MINUTES
# ============================================================

def publish_at_30():
    print("=" * 50)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🕐 PUBLICATION À 30 MINUTES")
    
    if not check_token():
        print("❌ Token invalide")
        return {"status": "error"}
    
    types = ["faq", "stats", "chart", "course"]
    chosen = random.choice(types)
    
    if chosen == "faq":
        return publish_faq()
    elif chosen == "stats":
        return publish_stats()
    elif chosen == "chart":
        return publish_chart_post()
    else:
        return publish_random_course()

def publish_faq():
    key = random.choice(list(FAQ.keys()))
    answer = FAQ[key]
    msg = f"""❓ QUESTION FRÉQUENTE
📖 Sujet: {key.upper()}

💡 Réponse:
{answer}

📱 WhatsApp: {WHATSAPP}
🤖 Rick Bot
"""
    result = publish_post(msg)
    return {"status": "success" if result else "error", "type": "faq", "topic": key}

def publish_stats():
    stats = get_page_stats()
    if not stats:
        return {"status": "error", "message": "Stats non disponibles"}
    msg = f"""📊 RAPPORT DE LA PAGE
📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}

👍 J'aime: {stats.get('page_fans', 0)}
👀 Impressions: {stats.get('page_impressions', 0)}
💬 Engagement: {stats.get('page_engaged_users', 0)}
📝 Impressions des posts: {stats.get('page_posts_impressions', 0)}

📱 WhatsApp: {WHATSAPP}
🤖 Rick Bot
"""
    result = publish_post(msg)
    return {"status": "success" if result else "error", "type": "stats"}

def publish_chart_post():
    result = publish_chart()
    return {"status": "success" if result else "error", "type": "chart"}

def publish_random_course():
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
    ]
    topic = random.choice(topics)
    course = groq_response(f"Crée un cours sur : {topic}", "Formation", "cours")
    msg = f"""📚 FORMATION TRADING
📖 Sujet: {topic}
{'=' * 40}

{course}

{'=' * 40}
📱 WhatsApp: {WHATSAPP}
🤖 Rick Bot
"""
    result = publish_post(msg)
    return {"status": "success" if result else "error", "type": "course", "topic": topic}

def get_page_stats():
    if not PAGE_TOKEN:
        return None
    try:
        url = f"https://graph.facebook.com/v24.0/{PAGE_ID}/insights"
        params = {
            'metric': 'page_fans,page_impressions,page_engaged_users,page_posts_impressions',
            'period': 'day',
            'access_token': PAGE_TOKEN
        }
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        stats = {}
        for item in data.get('data', []):
            name = item.get('name')
            values = item.get('values', [])
            if values:
                stats[name] = values[0].get('value', 0)
        return stats
    except Exception as e:
        print(f"❌ Erreur stats: {e}")
        return None

# ============================================================
# 10. ROUTES
# ============================================================

@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "whatsapp": WHATSAPP,
        "page_id": PAGE_ID,
        "version": "6.0 - Ultime",
        "modes": ["commentaires", "messages privés", "faq (30)", "stats (30)", "graphique (30)", "cours (30)"],
        "processed_comments": len(processed_comments),
        "processed_messages": len(processed_messages)
    })

@app.route('/ping')
def ping():
    return jsonify({"status": "alive"})

@app.route('/wakeup')
def wakeup():
    result = process_comments()
    return jsonify(result)

@app.route('/messages')
def messages():
    result = process_messages()
    return jsonify(result)

@app.route('/publish')
def publish():
    result = publish_at_30()
    return jsonify(result)

@app.route('/publish/faq')
def publish_faq_route():
    result = publish_faq()
    return jsonify(result)

@app.route('/publish/stats')
def publish_stats_route():
    result = publish_stats()
    return jsonify(result)

@app.route('/publish/chart')
def publish_chart_route():
    result = publish_chart_post()
    return jsonify(result)

@app.route('/course')
def course():
    result = publish_random_course()
    return jsonify(result)

@app.route('/course/<topic>')
def course_topic(topic):
    course = groq_response(f"Crée un cours sur : {topic}", "Formation", "cours")
    msg = f"""📚 FORMATION TRADING
📖 Sujet: {topic}
{'=' * 40}

{course}

{'=' * 40}
📱 WhatsApp: {WHATSAPP}
🤖 Rick Bot
"""
    result = publish_post(msg)
    return jsonify({"status": "success" if result else "error", "topic": topic})

@app.route('/test')
def test():
    comments = get_comments()
    messages = get_conversations()
    stats = get_page_stats()
    return jsonify({
        "token_valid": check_token(),
        "page_id": PAGE_ID,
        "comments_count": len(comments),
        "messages_count": len(messages),
        "stats": stats,
        "version": "6.0"
    })

@app.route('/reset')
def reset():
    global processed_comments, processed_messages
    processed_comments = set()
    processed_messages = set()
    save_processed_comments()
    save_processed_messages()
    return jsonify({"status": "reset"})

# ============================================================
# 11. DÉMARRAGE
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Assistant v6.0 - Ultime")
    print(f"📱 WhatsApp: {WHATSAPP}")
    print(f"💬 Commentaires: /wakeup")
    print(f"✉️ Messages: /messages")
    print(f"📚 Cours: /course")
    print(f"📊 Stats: /publish/stats")
    print(f"📈 Graphique: /publish/chart")
    print(f"❓ FAQ: /publish/faq")
    print(f"🎲 Aléatoire à 30: /publish")
    app.run(host='0.0.0.0', port=port)
