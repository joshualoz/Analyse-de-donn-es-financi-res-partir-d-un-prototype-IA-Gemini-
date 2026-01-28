import os
import requests
from dotenv import load_dotenv

# Charge les clés depuis le .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Variable globale interne au module pour suivre la lecture
DERNIER_UPDATE_ID = 0

def envoyer_alerte_telegram(message):
    """Envoie un message simple"""
    if not TELEGRAM_TOKEN: return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": message, 
        "parse_mode": "HTML"
    }
    
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"❌ Erreur Telegram: {e}")

def lire_ordres_telegram():
    """Lit les derniers messages (ACHAT/NON)"""
    global DERNIER_UPDATE_ID
    if not TELEGRAM_TOKEN: return []
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"offset": DERNIER_UPDATE_ID + 1, "timeout": 5}
    
    try:
        resp = requests.get(url, params=params).json()
        if not resp.get("ok"): return []

        resultats = resp.get("result", [])
        ordres = []
        
        for update in resultats:
            DERNIER_UPDATE_ID = update["update_id"]
            # On vérifie qu'il y a bien du texte
            if "message" in update and "text" in update["message"]:
                texte = update["message"]["text"].upper().strip()
                ordres.append(texte)
        return ordres
    except: return []