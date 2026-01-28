import sys
# Force l'encodage UTF-8 pour la console Windows (Empêche le crash des émojis)
sys.stdout.reconfigure(encoding='utf-8')

import time
from datetime import datetime
import yfinance as yf
import json 
# === IMPORTATION DE TES MODULES ===
from ai_agent import agent_eclaireur, agent_analyste, agent_detecteur_organique, agent_chasseur_diversification
from finance_agents import agent_financier_yahoo_pro, analyse_moyen_terme
from telegram_bot import envoyer_alerte_telegram, lire_ordres_telegram

# Import des nouvelles fonctions de gestion de portefeuille
from portfolio_manager import (
    charger_portfolio, sauvegarder_trade, supprimer_trade, 
    archiver_trade_termine, generer_rapport_performance
)

# === MÉMOIRE GLOBALE ===
TICKERS_DEJA_SIGNALES = []       
MEMOIRE_SIGNAUX_EN_ATTENTE = {}  

# ------------------------------------------------------
# 1. SURVEILLANCE DU PORTEFEUILLE (Vérifie SL et TP)
# ------------------------------------------------------
def surveiller_positions():
    portfolio = charger_portfolio()
    if not portfolio: return

    # Petit indicateur de vie
    print(".", end="", flush=True)

    for ticker, data in list(portfolio.items()):
        try:
            # Vérification rapide (15m pour éviter blocage Yahoo)
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(period="1d", interval="15m")
            if hist.empty: continue
            current_price = hist['Close'].iloc[-1]
            
            # --- SCÉNARIO 1 : TAKE PROFIT (GAGNÉ) ---
            if current_price >= data['take_profit']:
                profit = ((current_price - data['entry_price']) / data['entry_price']) * 100
                msg = (
                    f"💰 <b>TAKE PROFIT : {ticker}</b>\n"
                    f"💵 Vente : {current_price:.2f}$\n"
                    f"📈 Gain : +{profit:.2f}%\n"
                    f"✅ Position clôturée avec succès."
                )
                envoyer_alerte_telegram(msg)
                
                # On archive le succès et on supprime du portefeuille actif
                archiver_trade_termine(ticker, data, current_price, "TAKE PROFIT")
                supprimer_trade(ticker)
                
                print(f"\n💰 {ticker} VENDU (Gain +{profit:.2f}%) !")

            # --- SCÉNARIO 2 : STOP LOSS (PERDU) ---
            elif current_price <= data['stop_loss']:
                perte = ((current_price - data['entry_price']) / data['entry_price']) * 100
                msg = (
                    f"🛡️ <b>STOP LOSS : {ticker}</b>\n"
                    f"🩸 Sortie : {current_price:.2f}$\n"
                    f"📉 Perte : {perte:.2f}%\n"
                    f"❌ Position fermée (Protection)."
                )
                envoyer_alerte_telegram(msg)
                
                # On archive la perte
                archiver_trade_termine(ticker, data, current_price, "STOP LOSS")
                supprimer_trade(ticker)
                
                print(f"\n🛡️ {ticker} VENDU (Perte {perte:.2f}%) !")
                
        except Exception: pass

# ------------------------------------------------------
# 2. GESTION DE TES RÉPONSES & COMMANDES
# ------------------------------------------------------
def traiter_reponses_utilisateur():
    global TICKERS_DEJA_SIGNALES
    messages = lire_ordres_telegram()
    
    for msg in messages:
        # --- COMMANDE SPÉCIALE : STATS ---
        if msg in ["STATS", "BILAN", "STATISTIQUES"]:
            print("\n📊 Demande de rapport reçue...")
            rapport = generer_rapport_performance()
            envoyer_alerte_telegram(rapport)
            continue
            
        # --- COMMANDES D'ACHAT (ACHAT PLTR) ---
        parts = msg.split()
        if len(parts) < 2: continue
        
        action = parts[0] 
        ticker = parts[1] 
        
        if ticker in MEMOIRE_SIGNAUX_EN_ATTENTE:
            if action in ["ACHAT", "OUI", "BUY"]:
                data = MEMOIRE_SIGNAUX_EN_ATTENTE[ticker]
                
                # Préparation des données complètes
                save_data = {
                    "entry_price": data['prix'],
                    "stop_loss": data['stop_loss'],
                    "take_profit": data['take_profit'],
                    "date_entry": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                
                sauvegarder_trade(ticker, save_data)
                envoyer_alerte_telegram(f"✅ <b>{ticker}</b> ajouté au portefeuille ! Je surveille la sortie.")
                del MEMOIRE_SIGNAUX_EN_ATTENTE[ticker]
                print(f"\n✅ Ordre confirmé pour {ticker}")
                
            elif action in ["NON", "NO"]:
                envoyer_alerte_telegram(f"🗑️ <b>{ticker}</b> ignoré.")
                if ticker in TICKERS_DEJA_SIGNALES: TICKERS_DEJA_SIGNALES.remove(ticker)
                del MEMOIRE_SIGNAUX_EN_ATTENTE[ticker]
                print(f"\n🗑️ Ordre annulé pour {ticker}")

# ------------------------------------------------------
# 3. LE SCANNER COMPLET (BAVARD)
# ------------------------------------------------------
def lancer_scan_complet():
    global MEMOIRE_SIGNAUX_EN_ATTENTE, TICKERS_DEJA_SIGNALES
    print("\n🔭 Lancement du Scan de marché...")
    
    cibles = agent_eclaireur()
    if not cibles: 
        print("❌ Grok n'a rien trouvé d'intéressant.")
        return

    print(f"🎯 Cibles identifiées : {cibles}")
    
    for ticker in cibles:
        # Anti-Spam : On ne re-analyse pas une action déjà traitée dans la session
        if ticker in TICKERS_DEJA_SIGNALES: 
            continue
        
        print(f"\n⚡ Analyse approfondie de : {ticker}")
        
        # A. ANALYSE SOCIALE
        analyse = agent_analyste(ticker)
        if not analyse:
            print("      ❌ Erreur Grok (Pas de réponse).")
            continue
        
        print(f"      🧠 Sentiment: {analyse['sentiment_score']} | Sujet: {analyse['sujet_principal']}")
        
        if abs(analyse['sentiment_score']) < 0.1:
            print("      🚫 Sentiment trop neutre. Ignoré.")
            continue
        
        verif = agent_detecteur_organique(ticker, analyse['sujet_principal'])
        if not verif or verif['authenticite_score'] < 0.45: 
            print(f"      🚫 Trop de bots (Auth: {verif['authenticite_score'] if verif else 0}). Ignoré.")
            continue
        
        # B. ANALYSE TECHNIQUE
        print("      📉 Audit Technique (Yahoo)...")
        swing = analyse_moyen_terme(ticker)
        tech = agent_financier_yahoo_pro(ticker)
        
        if not tech or not tech['success']: 
            print("      ❌ Erreur données Yahoo.")
            continue
        
        # C. DÉCISION ET RAPPORT
        print(f"      📊 Résultat : {tech['signal']} (Score: {tech['score']}/5)")
        print(f"      📝 Raison   : {', '.join(tech['reasons'])}")

        if "ACHAT" in tech['signal']:
            MEMOIRE_SIGNAUX_EN_ATTENTE[ticker] = {
                "prix": tech['prix'],
                "take_profit": tech['take_profit'], 
                "stop_loss": tech['stop_loss']
            }
            TICKERS_DEJA_SIGNALES.append(ticker)
            
            trend = swing['verdict'] if swing['valid'] else "?"
            emoji = "🚀" if trend == "HAUSSIER" else "⚠️"
            
            msg = (
                f"{emoji} <b>SIGNAL DÉTECTÉ : {ticker}</b> ({tech['prix']:.2f}$)\n"
                f"----------------------------\n"
                f"📈 <b>Signal H1 :</b> {tech['signal']} ({tech['score']}/5)\n"
                f"📅 <b>Fond (W) :</b> {trend}\n"
                f"🧠 <b>Info :</b> {analyse['sujet_principal']}\n"
                f"----------------------------\n"
                f"🛡️ SL: {tech['stop_loss']:.2f}$ | 🎯 TP: {tech['take_profit']:.2f}$\n\n"
                f"👉 Réponds: 'ACHAT {ticker}' ou 'NON {ticker}'"
            )
            envoyer_alerte_telegram(msg)
            print(f"      ✅ ALERTE ENVOYÉE SUR TELEGRAM !")
        else:
            print("      ⏳ Pas d'alerte (Critères non remplis).")

# ------------------------------------------------------
# 4. BOUCLE PRINCIPALE (RUN)
# ------------------------------------------------------
if __name__ == "__main__":
    print("🤖 BOT DE TRADING - VERSION P&L & STATS")
    envoyer_alerte_telegram("🤖 <b>Bot Connecté</b>. Tape 'STATS' pour voir tes gains.")
    
    dernier_scan = 0
    INTERVALLE_SCAN = 1800 # 30 minutes
    
    while True:
        try:
            # 1. Tâches rapides (Toutes les 10s)
            surveiller_positions()
            traiter_reponses_utilisateur()
            
            # 2. Tâches lentes (Toutes les 30min)
            now = time.time()
            if now - dernier_scan > INTERVALLE_SCAN:
                lancer_scan_complet()
                dernier_scan = now
                print(f"\n💤 Pause Scan ({INTERVALLE_SCAN/60}min)... Surveillance active.")
            
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\n🛑 Arrêt manuel du bot.")
            break
        except Exception as e:
            print(f"\n❌ Erreur boucle principale : {e}")
            time.sleep(60)