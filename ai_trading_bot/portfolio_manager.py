import json
import os
from datetime import datetime

FICHIER_PORTFOLIO = "portfolio.json"
FICHIER_HISTORIQUE = "trades_history.json"

# --- GESTION DU PORTEFEUILLE ACTIF ---
def charger_portfolio():
    if not os.path.exists(FICHIER_PORTFOLIO): return {}
    try:
        with open(FICHIER_PORTFOLIO, "r") as f: return json.load(f)
    except: return {}

def sauvegarder_trade(ticker, data_trade):
    portfolio = charger_portfolio()
    # On ajoute la date d'entrée si elle n'existe pas
    if "date_entry" not in data_trade:
        data_trade["date_entry"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    portfolio[ticker] = data_trade
    with open(FICHIER_PORTFOLIO, "w") as f: json.dump(portfolio, f, indent=4)
    print(f"   💾 {ticker} sauvegardé dans le portefeuille.")

def supprimer_trade(ticker):
    portfolio = charger_portfolio()
    if ticker in portfolio:
        del portfolio[ticker]
        with open(FICHIER_PORTFOLIO, "w") as f: json.dump(portfolio, f, indent=4)

# --- NOUVEAU : GESTION DE L'HISTORIQUE (P&L) ---

def archiver_trade_termine(ticker, data_trade, prix_sortie, raison):
    """
    Déplace un trade fini vers l'historique et calcule le profit
    """
    historique = []
    if os.path.exists(FICHIER_HISTORIQUE):
        try:
            with open(FICHIER_HISTORIQUE, "r") as f: historique = json.load(f)
        except: pass
    
    prix_entree = data_trade['entry_price']
    # Calcul du profit en % : ((Sortie - Entrée) / Entrée) * 100
    profit_percent = ((prix_sortie - prix_entree) / prix_entree) * 100
    
    entree_historique = {
        "ticker": ticker,
        "entry_price": prix_entree,
        "exit_price": prix_sortie,
        "profit_percent": round(profit_percent, 2),
        "date_entry": data_trade.get("date_entry", "?"),
        "date_exit": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "reason": raison # "TAKE PROFIT" ou "STOP LOSS"
    }
    
    historique.append(entree_historique)
    
    with open(FICHIER_HISTORIQUE, "w") as f:
        json.dump(historique, f, indent=4)
    
    print(f"   📜 Trade {ticker} archivé (P&L: {profit_percent:.2f}%)")

def generer_rapport_performance():
    """Calcule les stats globales"""
    if not os.path.exists(FICHIER_HISTORIQUE):
        return "📉 Aucun historique de trade pour le moment."
    
    try:
        with open(FICHIER_HISTORIQUE, "r") as f: historique = json.load(f)
    except: return "⚠️ Erreur lecture historique."

    if not historique: return "📉 Historique vide."

    total_trades = len(historique)
    wins = 0
    losses = 0
    total_percent_gain = 0
    
    details_str = ""

    # On parcourt les 5 derniers trades pour le détail
    for trade in historique[-5:]:
        icon = "✅" if trade['profit_percent'] > 0 else "❌"
        details_str += f"{icon} {trade['ticker']}: {trade['profit_percent']}%\n"

    # Calcul des totaux
    for trade in historique:
        p = trade['profit_percent']
        total_percent_gain += p
        if p > 0: wins += 1
        else: losses += 1
    
    win_rate = (wins / total_trades) * 100
    
    rapport = (
        f"📊 <b>RAPPORT DE PERFORMANCE</b>\n"
        f"---------------------------\n"
        f"🔢 Total Trades : {total_trades}\n"
        f"🏆 Gagnés : {wins} | 🗑️ Perdus : {losses}\n"
        f"🎯 <b>Win Rate : {win_rate:.1f}%</b>\n"
        f"📈 <b>Performance cumulée : {total_percent_gain:.2f}%</b>\n"
        f"---------------------------\n"
        f"🕒 <i>Derniers trades :</i>\n"
        f"{details_str}"
    )
    return rapport