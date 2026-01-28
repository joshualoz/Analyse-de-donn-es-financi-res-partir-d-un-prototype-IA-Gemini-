import yfinance as yf
import pandas as pd
import numpy as np

# ==============================================================================
# ANALYSE SWING (MOYEN TERME - SÉCURITÉ)
# ==============================================================================
def analyse_moyen_terme(ticker):
    print(f"   📅 [SWING] Analyse Moyen Terme pour {ticker}...")
    try:
        # On télécharge 2 ans de données hebdo
        df = yf.download(ticker, period="2y", interval="1wk", progress=False)
        
        # Correction Bug Yahoo (Multi-index)
        if isinstance(df.columns, pd.MultiIndex): 
            df.columns = df.columns.get_level_values(0)
        
        if df.empty or len(df) < 30: 
            return {"valid": False, "verdict": "INCONNU", "details": []}

        # Indicateurs
        df['SMA_30'] = df['Close'].rolling(window=30).mean()
        
        # RSI Hebdo
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        latest = df.iloc[-1]
        
        # Verdict simple
        verdict = "HAUSSIER" if latest['Close'] > latest['SMA_30'] else "BAISSIER"
        details = [f"RSI Hebdo: {latest['RSI']:.0f}"]
        
        if verdict == "BAISSIER": details.append("Sous MM30 Hebdo")
        
        return {
            "valid": True, 
            "verdict": verdict, 
            "prix": latest['Close'],
            "details": details,
            "color": "🟢" if verdict == "HAUSSIER" else "🔴"
        }
    except Exception as e:
        print(f"❌ Erreur Swing: {e}")
        return {"valid": False}

# ==============================================================================
# SNIPER TRADING (COURT TERME H1 - TIMING)
# ==============================================================================
def agent_financier_yahoo_pro(ticker):
    print(f"   📉 [H1] Analyse Hybride (Trend + Cross) pour {ticker}...")
    try:
        # On télécharge assez de données pour les calculs
        df = yf.download(ticker, period="10d", interval="60m", progress=False, threads=False)
        
        if df is None or df.empty: return {"success": False}
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        # --- CALCULS INDICATEURS ---
        # EMA 20 (Rapide) et EMA 50 (Lente)
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # ATR (Volatilité pour SL/TP)
        df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()

        # On regarde la bougie actuelle (latest) et la précédente (prev)
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        atr = latest['ATR'] if not np.isnan(latest['ATR']) else latest['Close'] * 0.02
        
        signal = "NEUTRE"
        score = 0
        reasons = []

        # --- LOGIQUE HYBRIDE ---

        # 1. LA BASE : TENDANCE SAINE (Trend Following)
        # Si le prix est au-dessus de la moyenne mobile 50, c'est haussier.
        # C'est la condition minimale pour acheter.
        if latest['Close'] > latest['EMA_50']:
            score += 2
            reasons.append("Tendance Haussière (Prix > EMA50)")
            
            # On vérifie que le RSI n'est pas en surchauffe
            if latest['RSI'] < 70:
                signal = "ACHAT" # On valide l'achat de base
            else:
                reasons.append("Mais RSI trop haut")

        # 2. LE BONUS : LE CROISEMENT (Golden Cross)
        # Si la ligne rapide (20) passe au-dessus de la lente (50) MAINTENANT
        ema_cross_now = (latest['EMA_20'] > latest['EMA_50']) and (prev['EMA_20'] <= prev['EMA_50'])
        
        if ema_cross_now:
            score += 3 # BOOM ! Gros bonus de score
            signal = "ACHAT FORT" # On upgrade le signal
            reasons.append("⚡ GOLDEN CROSS (Signal Puissant)")
        
        # 3. LE BONUS : DÉMARRAGE DE TENDANCE
        # Si le prix vient juste de casser l'EMA 50 à la hausse
        price_cross_now = (latest['Close'] > latest['EMA_50']) and (prev['Close'] <= prev['EMA_50'])
        
        if price_cross_now:
            score += 1
            reasons.append("Breakout EMA50")

        # 4. GESTION DES REFUS (RSI)
        if latest['RSI'] > 75:
            signal = "ATTENDRE"
            score = 0
            reasons.append("⛔ Surchauffe RSI")
        
        # 5. OPPORTUNITÉ "DIP" (Contre-tendance)
        # Si le RSI est très bas, on achète même si la tendance est moche
        if latest['RSI'] < 30:
            signal = "ACHAT (DIP)"
            score += 2
            reasons.append("💎 Survente extrême")

        return {
            "success": True,
            "signal": signal,
            "score": score,
            "prix": latest['Close'],
            "stop_loss": latest['Close'] - (2 * atr),
            "take_profit": latest['Close'] + (3 * atr), # Ratio 1.5
            "rsi": latest['RSI'],
            "reasons": reasons
        }

    except Exception as e:
        return {"success": False}