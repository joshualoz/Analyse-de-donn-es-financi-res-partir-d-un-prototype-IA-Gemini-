import sys
sys.stdout.reconfigure(encoding='utf-8')
import time
from datetime import datetime
import yfinance as yf
import os       
import csv
import json 
# Imports des modules existants
from ai_agent import agent_eclaireur, agent_analyste, agent_detecteur_organique, agent_chasseur_diversification
from finance_agents import agent_financier_yahoo_pro, analyse_moyen_terme
from telegram_bot import envoyer_alerte_telegram, lire_ordres_telegram
from portfolio_manager import charger_portfolio, sauvegarder_trade, supprimer_trade, archiver_trade_termine, generer_rapport_performance
from ml_manager import enregistrer_features, update_resultat_ia, predire_succes

# === CONFIGURATION DU ROBOT ===
MAX_POSITIONS = 5          # Limite de sécurité : pas plus de 5 actions en même temps
TICKERS_DEJA_SIGNALES = [] # Mémoire tampon pour la session
INTERVALLE_SCAN = 1800     # Scan toutes les 30 minutes

# ------------------------------------------------------
# FONCTION 1 : LE GARDIEN (Vérifie SL et TP)
# ------------------------------------------------------
def surveiller_positions():
    portfolio = charger_portfolio()
    if not portfolio: return

    print(".", end="", flush=True)

    for ticker, data in list(portfolio.items()):
        try:
            # Vérification rapide du prix
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(period="1d", interval="15m")
            if hist.empty: continue
            current_price = hist['Close'].iloc[-1]
            
            # --- SCÉNARIO 1 : TAKE PROFIT (GAIN) ---
            if current_price >= data['take_profit']:
                profit = ((current_price - data['entry_price']) / data['entry_price']) * 100
                
                # 1. Enregistrement ML (Victoire = 1)
                update_resultat_ia(ticker, 1)
                
                # 2. Archivage
                archiver_trade_termine(ticker, data, current_price, "TAKE PROFIT")
                
                # 3. Notification
                envoyer_alerte_telegram(
                    f"💰 <b>AUTO-VENTE : {ticker}</b>\n"
                    f"💵 Prix : {current_price:.2f}$\n"
                    f"📈 Gain : +{profit:.2f}%\n"
                    f"✅ Objectif atteint."
                )
                supprimer_trade(ticker)

            # --- SCÉNARIO 2 : STOP LOSS (PROTECTION) ---
            elif current_price <= data['stop_loss']:
                perte = ((current_price - data['entry_price']) / data['entry_price']) * 100
                
                # 1. Enregistrement ML (Défaite = 0)
                update_resultat_ia(ticker, 0)
                
                # 2. Archivage
                archiver_trade_termine(ticker, data, current_price, "STOP LOSS")
                
                # 3. Notification
                envoyer_alerte_telegram(
                    f"🛡️ <b>AUTO-VENTE : {ticker}</b>\n"
                    f"🩸 Prix : {current_price:.2f}$\n"
                    f"📉 Perte : {perte:.2f}%\n"
                    f"❌ Stop Loss touché."
                )
                supprimer_trade(ticker)
                
        except Exception: pass

# ------------------------------------------------------
# FONCTION 2 : LE CHASSEUR AUTOMATIQUE
# ------------------------------------------------------
def execution_automatique():
    global TICKERS_DEJA_SIGNALES
    
    # 1. VÉRIFICATION ET CHOIX DU MODE
    portfolio = charger_portfolio()
    nb_positions = len(portfolio)
    
    # --- AIGUILLAGE ---
    if nb_positions >= MAX_POSITIONS:
        MODE_OBSERVATEUR = True
        print(f"\n🚫 Portefeuille plein ({nb_positions}/{MAX_POSITIONS}). Passage en MODE OBSERVATION 🔭.")
        # On lance le nouveau chasseur (Diversification)
        cibles = agent_chasseur_diversification()
    else:
        MODE_OBSERVATEUR = False
        print(f"\n🚀 Portefeuille ouvert ({nb_positions}/{MAX_POSITIONS}). Passage en MODE CHASSEUR 🔫.")
        # On lance le chasseur classique (Ta logique d'origine)
        cibles = agent_eclaireur()

    if not cibles: return

    for ticker in cibles:
        # 2. VÉRIFICATION DE SÉCURITÉ (Uniquement en mode Chasseur)
        # Si on est là pour acheter, on doit vérifier qu'on n'a pas rempli le bag entre temps
        if not MODE_OBSERVATEUR:
            portfolio_a_jour = charger_portfolio()
            if len(portfolio_a_jour) >= MAX_POSITIONS:
                print(f"   ⛔ Limite atteinte ({len(portfolio_a_jour)}/{MAX_POSITIONS}). Stop Achats.")
                break # <--- TA SÉCURITÉ ABSOLUE EST ICI (Conservée)
        
        # 3. VÉRIFICATION DES DOUBLONS (Conservée et valable pour les 2 modes)
        # (On utilise portfolio_a_jour si dispo, sinon portfolio, pour être sûr)
        current_pf = portfolio_a_jour if not MODE_OBSERVATEUR else portfolio
        if ticker in TICKERS_DEJA_SIGNALES or ticker in current_pf: 
            continue
        
        print(f"\n⚡ Analyse ({'OBS' if MODE_OBSERVATEUR else 'AUTO'}) : {ticker}")
        
        # A. GROK (Conservé)
        analyse = agent_analyste(ticker)
        if not analyse or abs(analyse['sentiment_score']) < 0.1: continue
        
        # B. VERIF ORGANIQUE (Conservée mais assouplie en mode Observation pour voir les grosses caps)
        if not MODE_OBSERVATEUR:
            verif = agent_detecteur_organique(ticker, analyse['sujet_principal'])
            if not verif or verif['authenticite_score'] < 0.45: continue
        
        # C. YAHOO (Conservé)
        tech = agent_financier_yahoo_pro(ticker)
        if not tech or not tech['success']: continue

        # D. IA FEATURES (Conservé)
        features_ia = {
            "sentiment": analyse['sentiment_score'],
            "auth_score": 0.8 if MODE_OBSERVATEUR else verif['authenticite_score'], # Valeur par défaut en Obs
            "rsi": tech['rsi'],
            "score_tech": tech['score'],
            "volatilite": (tech['take_profit'] - tech['prix']) / tech['prix']
        }
        
        proba_succes = predire_succes(features_ia)
        
        # --- DÉCISION FINALE ---
        if "ACHAT" in tech['signal']:
            
            # CAS 1 : MODE OBSERVATEUR (On est plein, on regarde juste)
            if MODE_OBSERVATEUR:
                msg = (
                    f"👀 <b>IDÉE DIVERSIFICATION : {ticker}</b>\n"
                    f"🏢 Secteur : Hors-Tech\n"
                    f"💵 Prix : {tech['prix']:.2f}$\n"
                    f"🗣️ <b>Grok Score : {analyse['sentiment_score']:.2f}</b>\n"
                    f"📊 Signal : {tech['signal']}\n"
                    f"💡 <i>Le portefeuille est plein, mais surveille ça !</i>"
                )
                envoyer_alerte_telegram(msg)
                print(f"      👀 Idée envoyée sur Telegram.")
                TICKERS_DEJA_SIGNALES.append(ticker)
            
            # CAS 2 : MODE CHASSEUR (On achète) -> TON CODE EXACT EST ICI
            else:
                # FILTRE IA (Ta logique d'origine)
                if proba_succes is not None and proba_succes < 0.30:
                    print(f"      ⛔ Veto IA (Confiance {proba_succes*100:.0f}% trop faible).")
                    continue 
                
                # EXÉCUTION (Ta logique d'origine)
                print(f"      ✅ ACHAT AUTOMATIQUE DÉCLENCHÉ !")
                
                data_trade = {
                    "entry_price": tech['prix'],
                    "stop_loss": tech['stop_loss'],
                    "take_profit": tech['take_profit'],
                    "date_entry": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                sauvegarder_trade(ticker, data_trade)
                enregistrer_features(ticker, features_ia)
                
                conf_str = f"{proba_succes*100:.0f}%" if proba_succes is not None else "N/A"
                msg = (f"🤖 <b>ACHAT AUTO : {ticker}</b>\n"
                       f"💵 Prix : {tech['prix']:.2f}$\n"
                       f"🗣️ <b>Grok Score : {analyse['sentiment_score']:.2f}</b>\n"
                       f"🧠 Confiance IA : {conf_str}")
                envoyer_alerte_telegram(msg)
                
                TICKERS_DEJA_SIGNALES.append(ticker)


def update_equity_curve():
    """
    Calcule le P&L Total (Argent gagné + Argent latent) et l'enregistre pour le graphique.
    """
    try:
        # 1. Calcul des gains RÉALISÉS (Historique)
        try:
            with open('trades_history.json', 'r') as f:
                history = json.load(f)
        except:
            history = []
            
        total_realise = 0
        if history:
            for t in history:
                # On gère les différents formats possibles de ton historique
                gain = t.get('profit_loss_amount', 0)
                if gain == 0 and 'exit_price' in t:
                    gain = t['exit_price'] - t['entry_price']
                total_realise += gain

        # 2. Calcul des gains LATENTS (Positions en cours)
        try:
            with open('portfolio.json', 'r') as f:
                portfolio = json.load(f)
        except:
            portfolio = {}
            
        total_latent = 0
        if portfolio:
            tickers = list(portfolio.keys())
            if tickers:
                try:
                    # Téléchargement rapide des prix
                    data = yf.download(tickers, period="1d", progress=False)['Close'].iloc[-1]
                    
                    # Petit hack car yfinance réagit différemment avec 1 seul ticker
                    if len(tickers) == 1:
                        current_prices = {tickers[0]: float(data)}
                    else:
                        current_prices = data.to_dict()

                    for ticker, info in portfolio.items():
                        # On compare le prix actuel au prix d'entrée
                        prix_actuel = current_prices.get(ticker, info['entry_price'])
                        total_latent += (prix_actuel - info['entry_price'])
                except Exception as e:
                    print(f"⚠️ Erreur prix latent : {e}")

        # 3. Total Global
        total_equity = total_realise + total_latent
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 4. Enregistrement dans le CSV
        file_exists = os.path.isfile('equity_log.csv')
        
        with open('equity_log.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            # Si le fichier est nouveau, on écrit les titres des colonnes
            if not file_exists:
                writer.writerow(['Date', 'Total_PNL', 'Realise', 'Latent']) 
            
            # On écrit les données
            writer.writerow([timestamp, total_equity, total_realise, total_latent])
            
    except Exception as e:
        print(f"❌ Erreur Log Equity: {e}")


# ------------------------------------------------------
# FONCTION 3 : GESTION COMMANDES (STATS)
# ------------------------------------------------------
def ecouter_commandes():
    """Permet juste de demander 'STATS' sur Telegram"""
    msgs = lire_ordres_telegram()
    for msg in msgs:
        if msg in ["STATS", "BILAN"]:
            envoyer_alerte_telegram(generer_rapport_performance())

# ------------------------------------------------------
# BOUCLE PRINCIPALE
# ------------------------------------------------------
if __name__ == "__main__":
    print("🤖 BOT FULL-AUTO ACTIVÉ 🚀")
    envoyer_alerte_telegram("🤖 <b>Mode 100% Autonome Activé.</b> Je gère tout.")
    
    # --- 1. INITIALISATION IMMÉDIATE DU GRAPHIQUE ---
    # On force la création du fichier CSV tout de suite pour que le Dashboard marche
    print("   📈 Initialisation de la courbe de performance...")
    try:
        update_equity_curve()
    except Exception as e:
        print(f"⚠️ Erreur Init Graphique : {e}")
    # ------------------------------------------------
    
    dernier_scan = 0
    
    while True:
        try:
            # 1. Gestion des positions (Priorité absolue)
            # C'est ici que le bot surveille les Stop Loss / Take Profit en temps réel
            surveiller_positions()
            
            # 2. Écoute si tu demandes les stats sur Telegram
            ecouter_commandes()
            
            # 3. Scan & Achat Auto + Mise à jour Graphique
            now = time.time()
            
            # Si le délai d'attente est écoulé (ex: 15 min), on lance le scan
            if now - dernier_scan > INTERVALLE_SCAN:
                
                # A. On met à jour la courbe de performance (Equity Curve)
                print("   📈 Enregistrement de la performance...")
                update_equity_curve()
                
                # B. On lance le chasseur (Grok + Yahoo)
                execution_automatique()
                
                # On réinitialise le chronomètre
                dernier_scan = now
                print(f"\n💤 Repos ({INTERVALLE_SCAN/60}min)...")
            
            time.sleep(10) # Petite pause de 10s pour ne pas surchauffer le processeur
            
        except KeyboardInterrupt:
            print("\n🛑 Arrêt manuel.")
            break
        except Exception as e:
            print(f"\n❌ Erreur dans la boucle principale : {e}")
            time.sleep(60) # En cas de crash, on attend 1 minute avant de réessayer