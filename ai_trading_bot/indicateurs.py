import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# === 1. Récupération & Nettoyage ===
def get_clean_data(ticker, period='1y'): # 1 an pour bien calculer l'EMA 200
    try:
        df = yf.download(ticker, period=period, progress=False)
        
        # CORRECTION DU BUG YAHOO (Multi-Index)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        if df.empty:
            return None
        return df
    except Exception as e:
        print(f"Erreur de téléchargement : {e}")
        return None

# === 2. Calcul des Indicateurs Avancés ===
def calculate_advanced_indicators(df):
    # --- A. Moyennes Mobiles (Tendance) ---
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()

    # --- B. RSI de Wilder (Le "Vrai" RSI) ---
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # --- C. MACD (Momentum) ---
    df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # --- D. Bandes de Bollinger (Volatilité) ---
    # SMA 20
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    # Écart type
    df['STD_20'] = df['Close'].rolling(window=20).std()
    # Bandes
    df['BB_Upper'] = df['SMA_20'] + (df['STD_20'] * 2)
    df['BB_Lower'] = df['SMA_20'] - (df['STD_20'] * 2)

    # --- E. ATR (Gestion du risque / Stop Loss) ---
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df['ATR'] = true_range.rolling(window=14).mean()

    return df

# === 3. Analyse & Stratégie ===
def analyze_market_structure(df):
    if df is None: return "Pas de données."
    
    latest = df.iloc[-1]
    prev = df.iloc[-2] # Pour voir les croisements
    
    score = 0
    reasons = []

    # 1. TENDANCE DE FOND (Poids Fort: 2 points)
    if latest['Close'] > latest['EMA_200']:
        if latest['EMA_50'] > latest['EMA_200']:
            score += 2
            reasons.append("✅ Tendance Haussière Saine (Prix > EMA200 & Golden Cross)")
        else:
            score += 1
            reasons.append("✅ Prix au-dessus de EMA200 (Reprise possible)")
    else:
        reasons.append("🔴 Tendance Baissière (Sous EMA200)")

    # 2. RSI (Poids Moyen: 1 point)
    if 30 < latest['RSI'] < 70:
        if latest['RSI'] > 50:
            score += 0.5
            reasons.append(f"💪 RSI Haussier ({latest['RSI']:.0f})")
    elif latest['RSI'] <= 30:
        score += 2 # Signal d'achat fort (Rebond)
        reasons.append(f"🟢 SURVENTE (RSI {latest['RSI']:.0f}) -> Opportunité d'achat")
    elif latest['RSI'] >= 70:
        score -= 2 # Danger
        reasons.append(f"⚠️ SURACHAT (RSI {latest['RSI']:.0f}) -> Risque de chute")

    # 3. BOLLINGER BANDS (Cassure)
    if latest['Close'] < latest['BB_Lower']:
        score += 1
        reasons.append("💎 Prix sous la Bollinger Basse (Statistiquement pas cher)")
    elif latest['Close'] > latest['BB_Upper']:
        reasons.append("🔥 Prix crève la Bollinger Haute (Surchauffe)")

    # 4. MACD (Croisement)
    # On vérifie si ça vient JUSTE de croiser à la hausse
    if latest['MACD'] > latest['MACD_signal'] and prev['MACD'] <= prev['MACD_signal']:
        score += 1.5
        reasons.append("🚀 CROISEMENT MACD HAUSSIER CONFIRMÉ")
    elif latest['MACD'] > latest['MACD_signal']:
        score += 0.5
        reasons.append("✅ MACD positif")

    # === CONCLUSION & GESTION DU RISQUE ===
    print("\n" + "="*50)
    print(f"📊 ANALYSE TECHNIQUE AVANCÉE : {latest.name.strftime('%Y-%m-%d')}")
    print("="*50)
    print(f"PRIX ACTUEL : {latest['Close']:.2f}$")
    print("-" * 20)
    
    for r in reasons:
        print(r)
    
    print("-" * 20)
    
    # Calcul des objectifs (Stop Loss / Take Profit) basé sur l'ATR
    # Stratégie classique : Stop Loss à 2x ATR, Take Profit à 3x ATR
    stop_loss = latest['Close'] - (2 * latest['ATR'])
    take_profit = latest['Close'] + (3 * latest['ATR'])
    
    if score >= 3.5:
        print(f"🔵 VERDICT : ACHAT FORT (Score: {score})")
        print(f"   🛡️ Stop Loss suggéré : {stop_loss:.2f}$")
        print(f"   🎯 Take Profit suggéré : {take_profit:.2f}$")
    elif score >= 1.5:
        print(f"🟡 VERDICT : NEUTRE / FAIBLE ACHAT (Score: {score})")
    else:
        print(f"🔴 VERDICT : VENTE / RESTER À L'ÉCART (Score: {score})")

    return df

# === 4. Execution ===
if __name__ == "__main__":
    ticker = input("Ticker : ").upper()
    data = get_clean_data(ticker)
    
    if data is not None:
        processed_data = calculate_advanced_indicators(data)
        analyze_market_structure(processed_data)
        
        # Plot rapide Bollinger + EMA
        plt.figure(figsize=(12,6))
        plt.plot(processed_data['Close'], label='Prix', color='black', alpha=0.5)
        plt.plot(processed_data['BB_Upper'], label='Bollinger Haut', color='green', linestyle='--', alpha=0.3)
        plt.plot(processed_data['BB_Lower'], label='Bollinger Bas', color='red', linestyle='--', alpha=0.3)
        plt.plot(processed_data['EMA_200'], label='EMA 200 (Tendance)', color='blue', linewidth=2)
        plt.fill_between(processed_data.index, processed_data['BB_Upper'], processed_data['BB_Lower'], color='gray', alpha=0.1)
        plt.title(f"Structure de Prix : {ticker}")
        plt.legend()
        plt.show()