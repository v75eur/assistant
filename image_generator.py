# ============================================================
# GÉNÉRATION D'IMAGES ÉDUCATIVES AVEC TRACÉS
# Pour les analyses Forex
# ============================================================

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch
import io
import base64
import random
import numpy as np
from datetime import datetime

def generate_educational_chart(pair, price, trend, resistances, supports, channel=None):
    """
    Génère un graphique éducatif avec tracés (flèches, zones, annotations).
    
    Args:
        pair (str): Nom de la paire
        price (float): Prix actuel
        trend (str): 'HAUSSIERE', 'BAISSIERE', 'LATERALE'
        resistances (list): Niveaux de résistance
        supports (list): Niveaux de support
        channel (dict): Canal avec 'upper', 'lower', 'slope'
    
    Returns:
        bytes: Données de l'image
    """
    fig, ax = plt.subplots(figsize=(16, 10))
    fig.patch.set_facecolor('#0a0a0a')
    ax.set_facecolor('#0d1117')
    
    # Générer des données de prix simulées
    days = 50
    base_price = price
    volatility = price * 0.05
    
    if trend == "HAUSSIERE":
        trend_line = np.linspace(base_price * 0.98, base_price * 1.05, days)
        noise = np.random.normal(0, volatility * 0.3, days)
        prices = trend_line + noise
    elif trend == "BAISSIERE":
        trend_line = np.linspace(base_price * 1.05, base_price * 0.95, days)
        noise = np.random.normal(0, volatility * 0.3, days)
        prices = trend_line + noise
    else:
        trend_line = np.full(days, base_price)
        noise = np.random.normal(0, volatility * 0.4, days)
        prices = trend_line + noise
    
    # Créer des bougies fictives
    candles = []
    for i in range(days):
        open_price = prices[i] + np.random.normal(0, volatility * 0.05)
        close_price = prices[i] + np.random.normal(0, volatility * 0.05)
        high_price = max(open_price, close_price) + abs(np.random.normal(0, volatility * 0.1))
        low_price = min(open_price, close_price) - abs(np.random.normal(0, volatility * 0.1))
        candles.append({
            'o': open_price,
            'c': close_price,
            'h': high_price,
            'l': low_price
        })
    
    # Dessiner les bougies
    for i, c in enumerate(candles):
        color = '#26a69a' if c['c'] >= c['o'] else '#ef5350'
        ax.plot([i, i], [c['l'], c['h']], color=color, lw=1.5)
        ax.add_patch(plt.Rectangle(
            (i - 0.35, min(c['o'], c['c'])),
            0.7,
            abs(c['c'] - c['o']) or 0.0001,
            facecolor=color,
            edgecolor=color,
            alpha=0.9
        ))
    
    # ============================================================
    # TRACÉS ÉDUCATIFS
    # ============================================================
    
    # 1. CANAL (si fourni)
    if channel:
        if channel.get('upper') and channel.get('lower'):
            upper = channel['upper']
            lower = channel['lower']
            ax.axhline(upper, color='#a371f7', ls='--', lw=3, alpha=0.8, label='Canal supérieur')
            ax.axhline(lower, color='#a371f7', ls='--', lw=3, alpha=0.8, label='Canal inférieur')
            ax.fill_between(range(days), [upper]*days, [lower]*days, color='#a371f7', alpha=0.08)
            # Flèche de direction du canal
            if channel.get('slope', 0) > 0:
                ax.annotate('↗', xy=(days*0.8, (upper+lower)/2), color='#a371f7', fontsize=30, ha='center')
                ax.text(days*0.85, (upper+lower)/2, 'CANAL HAUSSIER', color='#a371f7', fontsize=14, fontweight='bold')
            else:
                ax.annotate('↘', xy=(days*0.8, (upper+lower)/2), color='#a371f7', fontsize=30, ha='center')
                ax.text(days*0.85, (upper+lower)/2, 'CANAL BAISSIER', color='#a371f7', fontsize=14, fontweight='bold')
    
    # 2. RÉSISTANCES
    for i, r in enumerate(resistances[:3]):
        ax.axhline(r, color='#f85149', ls=':', lw=2.5, alpha=0.8)
        ax.text(days-2, r, f'  R{i+1}: {r:.2f}', color='#f85149', fontsize=12, va='bottom', ha='right', fontweight='bold')
        # Flèche vers le bas (blocage)
        ax.annotate('↓', xy=(days*0.7, r), color='#f85149', fontsize=20, ha='center', va='top')
        ax.text(days*0.65, r + (price*0.01), 'Résistance', color='#f85149', fontsize=10, ha='center')
    
    # 3. SUPPORTS
    for i, s in enumerate(supports[:3]):
        ax.axhline(s, color='#3fb950', ls=':', lw=2.5, alpha=0.8)
        ax.text(days-2, s, f'  S{i+1}: {s:.2f}', color='#3fb950', fontsize=12, va='top', ha='right', fontweight='bold')
        # Flèche vers le haut (rebond)
        ax.annotate('↑', xy=(days*0.7, s), color='#3fb950', fontsize=20, ha='center', va='bottom')
        ax.text(days*0.65, s - (price*0.01), 'Support', color='#3fb950', fontsize=10, ha='center')
    
    # 4. PRIX ACTUEL
    ax.axhline(price, color='#f59e0b', ls='-.', lw=3)
    ax.text(2, price, f' ► Prix actuel: {price:.2f}', color='#f59e0b', fontsize=14, va='bottom', fontweight='bold')
    
    # 5. TENDANCE (flèche globale)
    if trend == "HAUSSIERE":
        ax.annotate('📈 TENDANCE HAUSSIÈRE', xy=(days*0.5, max(prices)*1.02), color='#26a69a', fontsize=18, ha='center', fontweight='bold')
        # Flèche de tendance
        ax.annotate('', xy=(days*0.8, min(prices)*1.1), xytext=(days*0.2, min(prices)*0.9),
                   arrowprops=dict(arrowstyle='->', color='#26a69a', lw=4))
    elif trend == "BAISSIERE":
        ax.annotate('📉 TENDANCE BAISSIÈRE', xy=(days*0.5, max(prices)*1.02), color='#ef5350', fontsize=18, ha='center', fontweight='bold')
        ax.annotate('', xy=(days*0.8, min(prices)*0.9), xytext=(days*0.2, min(prices)*1.1),
                   arrowprops=dict(arrowstyle='->', color='#ef5350', lw=4))
    else:
        ax.annotate('➡️ TENDANCE LATÉRALE', xy=(days*0.5, max(prices)*1.02), color='#8f8f8f', fontsize=18, ha='center', fontweight='bold')
    
    # 6. ANNOTATIONS ÉDUCATIVES
    # Zone d'achat
    if supports:
        buy_zone = supports[0]
        ax.axhspan(buy_zone - price*0.005, buy_zone + price*0.005, color='#3fb950', alpha=0.15)
        ax.text(days*0.1, buy_zone, 'ZONE D\'ACHAT', color='#3fb950', fontsize=12, ha='center', fontweight='bold')
        ax.annotate('💰', xy=(days*0.1, buy_zone - price*0.02), color='#3fb950', fontsize=20, ha='center')
    
    # Zone de vente
    if resistances:
        sell_zone = resistances[0]
        ax.axhspan(sell_zone - price*0.005, sell_zone + price*0.005, color='#f85149', alpha=0.15)
        ax.text(days*0.9, sell_zone, 'ZONE DE VENTE', color='#f85149', fontsize=12, ha='center', fontweight='bold')
        ax.annotate('💵', xy=(days*0.9, sell_zone - price*0.02), color='#f85149', fontsize=20, ha='center')
    
    # 7. INFORMATIONS
    ax.set_title(f"📊 {pair} - Analyse éducative", color='white', fontsize=18, fontweight='bold', pad=20)
    ax.set_xlabel("Temps (bougies horaires)", color='white', fontsize=13)
    ax.set_ylabel("Prix", color='white', fontsize=13)
    ax.tick_params(colors='white', labelsize=11)
    ax.grid(True, alpha=0.08, color='gray')
    for sp in ax.spines.values():
        sp.set_color('#333333')
    
    # 8. LÉGENDE
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(color='#26a69a', label='Bougie haussière'),
        Patch(color='#ef5350', label='Bougie baissière'),
        Patch(color='#f85149', label='Résistance'),
        Patch(color='#3fb950', label='Support'),
        Patch(color='#a371f7', label='Canal'),
        Patch(color='#f59e0b', label='Prix actuel')
    ]
    ax.legend(handles=legend_elements, loc='upper left', facecolor='#1a1a2e', edgecolor='#555', labelcolor='white', fontsize=12, framealpha=0.9)
    
    # 9. FOOTER ÉDUCATIF
    ax.text(days*0.5, min(prices)*0.92, 
            "📚 Formations trading | WhatsApp: +22960315458 | Email: bottrade7425@gmail.com",
            color='white', fontsize=11, ha='center', bbox=dict(boxstyle='round,pad=0.5', facecolor='#1a1a2e', alpha=0.9))
    
    plt.tight_layout(pad=1.5)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, facecolor='#0a0a0a')
    buf.seek(0)
    plt.close()
    
    return buf.getvalue()

def generate_educational_post(pair, price, trend, resistances, supports, channel=None):
    """
    Génère une image éducative + un texte explicatif.
    
    Returns:
        dict: {'image': bytes, 'text': str}
    """
    # Générer l'image
    image_data = generate_educational_chart(pair, price, trend, resistances, supports, channel)
    
    # Générer le texte explicatif
    trend_emoji = "📈" if trend == "HAUSSIERE" else "📉" if trend == "BAISSIERE" else "➡️"
    trend_text = "haussière" if trend == "HAUSSIERE" else "baissière" if trend == "BAISSIERE" else "latérale"
    
    text = f"📊 {pair} - Analyse éducative\n\n"
    text += f"💰 Prix actuel: {price:.2f}\n"
    text += f"{trend_emoji} Tendance: {trend_text.upper()}\n\n"
    
    if resistances:
        text += "🔴 RÉSISTANCES (blocages):\n"
        for i, r in enumerate(resistances[:3]):
            text += f"   R{i+1}: {r:.2f}\n"
        text += "\n"
    
    if supports:
        text += "🟢 SUPPORTS (rebonds):\n"
        for i, s in enumerate(supports[:3]):
            text += f"   S{i+1}: {s:.2f}\n"
        text += "\n"
    
    if channel:
        direction = "HAUSSIER ↑" if channel.get('slope', 0) > 0 else "BAISSIER ↓"
        text += f"📏 Canal: {direction}\n\n"
    
    text += "💡 INTERPRÉTATION:\n"
    if trend == "HAUSSIERE":
        text += "👉 Le prix est en tendance haussière.\n"
        text += "👉 Les supports sont des zones d'achat potentielles.\n"
        text += "👉 Les résistances sont des objectifs de profit.\n"
    elif trend == "BAISSIERE":
        text += "👉 Le prix est en tendance baissière.\n"
        text += "👉 Les résistances sont des zones de vente potentielles.\n"
        text += "👉 Les supports sont des objectifs de profit.\n"
    else:
        text += "👉 Le prix évolue dans un range.\n"
        text += "👉 Achat près du support, vente près de la résistance.\n"
    
    text += "\n📚 Formations disponibles sur WhatsApp!\n"
    text += f"📱 WhatsApp: +22960315458\n"
    text += f"📧 Email: bottrade7425@gmail.com\n"
    text += "🤖 Rick Bot - Analyses éducatives"
    
    return {
        'image': image_data,
        'text': text
    }
