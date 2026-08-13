#!/usr/bin/env python3
# ============================================================
# ASSISTANT GROQ - VERSION 5.0
# Auto (00) + FAQ + Stats + Graphiques (30) + MESSENGER
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
# 2. BASE DE CONNAISSANCES (FAQ)
# ============================================================

FAQ = {
    "trading": "Le trading consiste à acheter et vendre des actifs financiers. J'enseigne les bases sur WhatsApp ! 📱",
    "formation": "Je propose des formations personnalisées en trading et développement. Contacte-moi sur WhatsApp !",
    "bot": "Oui, je suis un assistant IA créé pour aider les traders. Je suis géré par Rick, trader pro depuis 8 ans.",
    "xauusd": "XAUUSD est la paire Or/Dollar. C'est mon actif préféré ! 📈",
    "v75": "Le V75 (Volatility 75) est un indice de volatilité sur Deriv.",
    "forex": "Le Forex est le marché des devises. Paires principales : EURUSD, GBPUSD, USDJPY.",
    "analyse": "J'utilise l'analyse technique : supports, résistances, canaux, tendances.",
    "signal": "Je partage des signaux en privé sur WhatsApp. Contacte-moi !",
    "prix": "Les prix sont actualisés en temps réel sur mes analyses.",
    "tendance": "Les tendances sont identifiées avec des indicateurs techniques.",
}

def answer_faq(question):
    question_lower = question.lower()
    for key, answer in FAQ.items():
        if key in question_lower:
            return answer
    return None

# ============================================================
# 3. STATISTIQUES
# ============================================================

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

def generate_chart_image():
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
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"❌ Erreur graphique: {e}")
        return None

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
    if not PAGE_TOKEN:
        return False
    try:
        url = f"https://graph.facebook.com/v24.0/{PAGE_ID}/feed"
        data = {'message': message, 'access_token': PAGE_TOKEN}
        r = requests.post(url, data=data, timeout=30)
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def get_comments():
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
                    if author_id != PAGE_ID and comment_id not in processed_comments:
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
# 5. NOUVEAU : MESSAGES PRIVÉS (MESSENGER)
# ============================================================

def get_conversations():
    """Récupère les conversations Messenger."""
    if not PAGE_TOKEN:
        return []
    
    conversations = []
    try:
        url = f"https://graph.facebook.com/v24.0/{PAGE_ID}/conversations"
        params = {
            'fields': 'id,participants,messages{id,message,from{name,id}}',
            'limit': 20,
            'access_token': PAGE_TOKEN
        }
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        
        print(f"📄 {len(data.get('data', []))} conversations trouvées")
        
        for conv in data.get('data', []):
            if 'messages' in conv:
                for msg in conv['messages'].get('data', []):
                    msg_id = msg.get('id', '')
                    author = msg.get('from', {}).get('name', 'Inconnu')
                    author_id = msg.get('from', {}).get('id', '')
                    
                    if author_id != PAGE_ID and msg_id not in processed_messages:
                        conversations.append({
                            'id': msg_id,
                            'message': msg.get('message', ''),
                            'author': author,
                            'author_id': author_id,
                            'conversation_id': conv.get('id', '')
                        })
        return conversations
    except Exception as e:
        print(f"❌ Erreur conversations: {e}")
        return []

def reply_to_message(recipient_id, message):
    """Envoie un message privé via Messenger."""
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
        if r.status_code == 200:
            print(f"✅ Message envoyé à {recipient_id}")
            return True
        else:
            print(f"❌ Erreur envoi message: {r.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def process_messages():
    """Traite les messages privés."""
    print("=" * 50)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✉️ TRAITEMENT DES MESSAGES PRIVÉS")
    
    if not check_token():
        print("❌ Token invalide")
        return {"status": "error"}
    
    conversations = get_conversations()
    if not conversations:
        print("📭 Aucun nouveau message")
        return {"status": "success", "message": "Aucun message", "count": 0}
    
    print(f"📝 {len(conversations)} message(s) à traiter")
    
    for msg in conversations:
        print(f"✉️ {msg['author']}: {msg['message'][:50]}...")
        
        # Vérifier si c'est une question FAQ
        faq_answer = answer_faq(msg['message'])
        if faq_answer:
            reply = faq_answer + f"\n\n📱 WhatsApp: {WHATSAPP}"
        else:
            reply = groq_response(msg['message'], msg['author'], "message")
        
        if reply_to_message(msg['author_id'], reply):
            processed_messages.add(msg['id'])
            save_processed_messages()
        time.sleep(1)
    
    return {"status": "success", "message": "Terminé", "count": len(conversations)}

# ============================================================
# 6. SUIVI
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
# 7. FONCTION GROQ
# ============================================================

def groq_response(message, author, prompt_type="commentaire"):
    if not GROQ_API_KEY:
        return f"Salut ! Contacte-moi sur WhatsApp {WHATSAPP}"
    
    prompts = {
        "commentaire": """Tu es Rick, le fondateur de Trader123.
Tu es un trader pro depuis 8 ans. Parle comme un humain.
Termine toujours par le WhatsApp : +22960315458
Sois naturel, joyeux, accessible.""",
        
        "message": """Tu es Rick. Réponds à ce message privé de manière professionnelle et chaleureuse.
Termine toujours par le WhatsApp : +22960315458
Sois utile et encourageant.""",
        
        "faq": """Tu es Rick. Réponds de manière claire et utile.
Termine toujours par le WhatsApp : +22960315458
Sois précis et concis."""
    }
    
    prompt = prompts.get(prompt_type, prompts["commentaire"])
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Message de {author}: {message}"}
        ]
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=200,
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
# 8. TRAITEMENT DES COMMENTAIRES
# ============================================================

def process_comments():
    print("=" * 50)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 TRAITEMENT DES COMMENTAIRES")
    
    if not check_token():
        print("❌ Token invalide")
        return {"status": "error"}
    
    comments = get_comments()
    if not comments:
        print("📭 Aucun commentaire")
        return {"status": "success", "message": "Aucun commentaire", "count": 0}
    
    print(f"📝 {len(comments)} commentaire(s) à traiter")
    
    for c in comments:
        print(f"💬 {c['author']}: {c['message'][:50]}...")
        reply = groq_response(c['message'], c['author'], "commentaire")
        if reply_to_comment(c['id'], reply):
            processed_comments.add(c['id'])
            save_processed_comments()
        time.sleep(1)
    
    return {"status": "success", "message": "Terminé", "count": len(comments)}

# ============================================================
# 9. PUBLICATION À 30 MINUTES
# ============================================================

def publish_at_30():
    print("=" * 50)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🕐 PUBLICATION À 30 MINUTES")
    
    if not check_token():
        print("❌ Token invalide")
        return {"status": "error"}
    
    types = ["faq", "stats", "chart"]
    chosen = random.choice(types)
    
    if chosen == "faq":
        return publish_faq()
    elif chosen == "stats":
        return publish_stats()
    else:
        return publish_chart_post()

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
    img_base64 = generate_chart_image()
    if not img_base64:
        return {"status": "error", "message": "Erreur graphique"}
    msg = f"""📊 VISUALISATION DE L'ENGAGEMENT
📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}

📈 Évolution de l'engagement cette semaine

📱 WhatsApp: {WHATSAPP}
🤖 Rick Bot
"""
    try:
        url = f"https://graph.facebook.com/v24.0/{PAGE_ID}/photos"
        files = {'source': ('chart.png', base64.b64decode(img_base64), 'image/png')}
        data = {'caption': msg, 'access_token': PAGE_TOKEN, 'published': True}
        r = requests.post(url, files=files, data=data, timeout=30)
        return {"status": "success" if r.status_code == 200 else "error", "type": "chart"}
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return {"status": "error", "message": str(e)}

# ============================================================
# 10. ROUTES
# ============================================================

@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "whatsapp": WHATSAPP,
        "page_id": PAGE_ID,
        "version": "5.0 - Avec Messenger",
        "modes": ["commentaires", "messages privés", "faq (30)", "stats (30)", "graphique (30)"],
        "processed_comments": len(processed_comments),
        "processed_messages": len(processed_messages)
    })

@app.route('/ping')
def ping():
    return jsonify({"status": "alive"})

@app.route('/wakeup')
def wakeup():
    """Mode Auto : Traite les commentaires."""
    result = process_comments()
    return jsonify(result)

@app.route('/messages')
def messages():
    """Mode Messenger : Traite les messages privés."""
    result = process_messages()
    return jsonify(result)

@app.route('/publish')
def publish():
    """Publie aléatoirement à 30."""
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
        "version": "5.0"
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
    print(f"🚀 Assistant v5.0 - Avec Messenger")
    print(f"📱 WhatsApp: {WHATSAPP}")
    print(f"📚 Commentaires: /wakeup")
    print(f"✉️ Messages privés: /messages")
    print(f"📚 FAQ (30): /publish/faq")
    print(f"📊 Stats (30): /publish/stats")
    print(f"📈 Graphique (30): /publish/chart")
    app.run(host='0.0.0.0', port=port)
