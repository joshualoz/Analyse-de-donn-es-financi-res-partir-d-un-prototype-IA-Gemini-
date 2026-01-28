import pandas as pd
import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime

FICHIER_DATASET = "ml_dataset.csv"
FICHIER_MODELE = "cerveau_ia.pkl"

def enregistrer_features(ticker, features):
    """Enregistre le contexte (Météo) avant l'achat"""
    data = features.copy()
    data['ticker'] = ticker
    data['date'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    data['resultat'] = None 
    
    if os.path.exists(FICHIER_DATASET):
        df = pd.read_csv(FICHIER_DATASET)
        df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    else:
        df = pd.DataFrame([data])
    df.to_csv(FICHIER_DATASET, index=False)

def update_resultat_ia(ticker, resultat):
    """Note la copie (1=Gagné, 0=Perdu) après la vente"""
    if not os.path.exists(FICHIER_DATASET): return
    df = pd.read_csv(FICHIER_DATASET)
    
    # On cherche la dernière occurrence sans résultat
    for i in range(len(df) - 1, -1, -1):
        if df.at[i, 'ticker'] == ticker and pd.isna(df.at[i, 'resultat']):
            df.at[i, 'resultat'] = int(resultat)
            df.to_csv(FICHIER_DATASET, index=False)
            entrainer_modele() # On révise la leçon immédiatement
            return

def entrainer_modele():
    """L'IA apprend des erreurs passées"""
    if not os.path.exists(FICHIER_DATASET): return
    df = pd.read_csv(FICHIER_DATASET)
    df_clean = df.dropna(subset=['resultat'])
    
    if len(df_clean) < 10: return # Pas assez d'expérience

    X = df_clean.drop(columns=['ticker', 'date', 'resultat'], errors='ignore')
    y = df_clean['resultat'].astype(int)
    
    try:
        model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        model.fit(X, y)
        joblib.dump(model, FICHIER_MODELE)
    except: pass

def predire_succes(features):
    """Donne un avis sur un nouveau trade (Probabilité de gain)"""
    if not os.path.exists(FICHIER_MODELE): return None
    try:
        model = joblib.load(FICHIER_MODELE)
        return model.predict_proba(pd.DataFrame([features]))[0][1]
    except: return None