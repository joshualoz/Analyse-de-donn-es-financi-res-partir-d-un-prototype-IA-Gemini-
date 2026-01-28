import os
import json
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()
client = OpenAI(api_key=os.getenv("XAI_API_KEY"), base_url="https://api.x.ai/v1")

# ==============================================================================
# AGENT 1 : ÉCLAIREUR (Grok)
# ==============================================================================
def agent_eclaireur():
    print("\n🔭 [AGENT 1] Scan Grok (Mode : Volatilité & Volume)...")
    prompt = """
    Tu es un screener de marché professionnel. Donne-moi une liste de 8 à 10 actions (Stocks US) qui connaissent une forte volatilité ou un volume anormalement élevé AUJOURD'HUI.
    
    CRITÈRES :
    1. Focus sur la "Hype" du moment, les "Breakouts" ou les résultats financiers récents.
    2. PEU IMPORTE la taille (Large Cap acceptées si elles bougent fort).
    3. Exclure uniquement les Penny Stocks (< 5$).
    
    Format JSON strict : { "liste_tickers": ["SYMBOLE1", "SYMBOLE2", ...] }
    """
    try:
        response = client.chat.completions.create(
            model="grok-3", messages=[{"role": "system", "content": prompt}], temperature=0.7
        )
        content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        
        # Gestion robuste des formats de réponse
        if isinstance(data, dict):
            for key in data:
                if isinstance(data[key], list): return data[key]
        elif isinstance(data, list): return data
        return []
    except Exception as e:
        print(f"❌ Erreur Eclaireur : {e}")
        return []

# ==============================================================================
# AGENT 2 : ANALYSTE (Grok)
# ==============================================================================
def agent_analyste(ticker):
    prompt = f"""
    Analyse tweets récents sur : ${ticker}.
    1. Estime le VOLUME (0.1 à 1.0).
    2. Analyse le SENTIMENT (-1.0 à 1.0).
    3. Sépare le SPAM.
    Format JSON :
    {{
        "spam_ratio": (float 0.0 à 1.0),
        "sentiment_score": (float -1.0 à 1.0),
        "volume_score": (float 0.1 à 1.0),
        "sujet_principal": "Résumé court"
    }}
    """
    try:
        response = client.chat.completions.create(
            model="grok-3", messages=[{"role": "user", "content": prompt}], temperature=0.2
        )
        return json.loads(response.choices[0].message.content.replace("```json", "").replace("```", "").strip())
    except: return None

# ==============================================================================
# AGENT 3 : DÉTECTEUR HUMANITÉ (Grok)
# ==============================================================================
def agent_detecteur_organique(ticker, sujet):
    prompt = f"""
    Analyse tweets sur "${ticker}" (Sujet: {sujet}).
    OBJECTIF : Déterminer si ce sont de VRAIS HUMAINS ou des BOTS.
    Note sur 10 :
    1. CHAOS LINGUISTIQUE (Humains = bordéliques/argot).
    2. CONTEXTE PRÉCIS (Humains = détails techniques).
    3. INTERACTION (Humains = réponses/débats).
    Renvoie JSON :
    {{
        "note_chaos": (int 0-10),
        "note_contexte": (int 0-10),
        "note_interaction": (int 0-10),
        "type_foule": ("Retail", "Bots", "Mixte"),
        "explication": "Pourquoi"
    }}
    """
    try:
        response = client.chat.completions.create(
            model="grok-3", messages=[{"role": "user", "content": prompt}], temperature=0.2
        )
        content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        total = data['note_chaos'] + data['note_contexte'] + data['note_interaction']
        data['authenticite_score'] = round(total / 30, 2)
        return data
    except: return None

def agent_chasseur_diversification():
    print("\n🌍 [AGENT 2] Scan Grok (Mode : Diversification & Valeur)...")
    prompt = """
    Tu es un expert en diversification de portefeuille. 
    Le secteur Tech est saturé. Trouve-moi 5 actions intéressantes DANS D'AUTRES SECTEURS (Santé, Énergie, Industrie, Biens de consommation, Finance).
    
    CRITÈRES :
    1. EXCLURE totalement le secteur Technologie / AI / Semi-conducteurs.
    2. Chercher des configurations solides ou des actions sous-évaluées (Value Investing).
    3. Entreprises rentables ou leaders de leur secteur (Ex: Coca-Cola, Pfizer, CAT, etc.).
    
    Format JSON strict : { "liste_tickers": ["SYMBOLE1", "SYMBOLE2", ...] }
    """
    try:
        # Note: Assure-toi d'utiliser ton client OpenAI/Grok configuré comme dans l'autre fonction
        # Je remets la structure standard ici, adapte si ton client a un nom différent
        response = client.chat.completions.create(
            model="grok-3", # ou ton modèle habituel
            messages=[{"role": "system", "content": prompt}], 
            temperature=0.6
        )
        content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        
        if isinstance(data, dict):
            for key in data:
                if isinstance(data[key], list): return data[key]
        elif isinstance(data, list): return data
        return []
    except Exception as e:
        print(f"❌ Erreur Chasseur Diversification : {e}")
        return []