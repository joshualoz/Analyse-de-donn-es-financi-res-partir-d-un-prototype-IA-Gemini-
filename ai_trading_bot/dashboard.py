import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="🤖 Cockpit Trading Pro", layout="wide", page_icon="📈")

# --- CSS : Forcer l'affichage des axes ---
st.markdown("""
    <style>
    .js-plotly-plot .plotly .xaxislayer-above, .js-plotly-plot .plotly .yaxislayer-above {
        opacity: 1 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Titre
col_title, col_btn = st.columns([3, 1])
with col_title:
    st.title("⚡ Mon Cockpit de Trading")
with col_btn:
    if st.button('🔄 Actualiser (Live)'):
        st.rerun()

# --- FONCTIONS ---
def charger_json(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except:
        return [] if 'history' in filename else {}

def get_historical_data(ticker):
    try:
        # On télécharge 5 jours
        df = yf.download(ticker, period="5d", interval="60m", progress=False)
        return df
    except:
        return pd.DataFrame()

# =========================================================
# 1. CALCULS P&L
# =========================================================
history = charger_json('trades_history.json')
portfolio = charger_json('portfolio.json')

total_realise = 0
if history:
    for t in history:
        entry_p = float(t.get('entry_price', 0))
        exit_p = float(t.get('exit_price', 0))
        if 'profit_loss_amount' in t:
            total_realise += float(t['profit_loss_amount'])
        elif entry_p > 0:
            total_realise += (exit_p - entry_p)

total_latent = 0
if portfolio:
    for ticker, data in portfolio.items():
        info = yf.Ticker(ticker).fast_info
        current_price = info.last_price if info.last_price else float(data['entry_price'])
        total_latent += (current_price - float(data['entry_price']))

total_pnl = total_realise + total_latent

# =========================================================
# 2. COURBE GLOBALE (EQUITY)
# =========================================================
st.markdown("### 🏆 Performance Globale")
col1, col2, col3 = st.columns(3)
col1.metric("💰 Gains Réalisés", f"{total_realise:.2f} $")
col2.metric("⏳ Gains Latents", f"{total_latent:.2f} $")
col3.metric("🚀 RÉSULTAT NET", f"{total_pnl:.2f} $")

try:
    df_equity = pd.read_csv('equity_log.csv')
    if not df_equity.empty:
        fig_eq = go.Figure()
        fig_eq.add_trace(go.Scatter(
            x=df_equity['Date'], y=df_equity['Total_PNL'],
            fill='tozeroy', mode='lines+markers', marker=dict(size=6),
            line=dict(color='#00CC96', width=3), name='Capital'
        ))
        fig_eq.update_layout(
            height=350, margin=dict(l=20, r=20, t=20, b=30),
            yaxis=dict(tickprefix="$", showgrid=True, automargin=True, showticklabels=True),
            xaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig_eq, use_container_width=True)
    else:
        st.info("La courbe se construit...")
except:
    st.warning("Fichier equity_log.csv manquant.")

st.divider()

# =========================================================
# 3. POSITIONS ACTIVES (VERSION BLINDÉE 🛡️)
# =========================================================
st.markdown("### 🔭 Surveillance des Positions")

if not portfolio:
    st.info("Aucune position en cours.")
else:
    cols = st.columns(2)
    for i, (ticker, data) in enumerate(portfolio.items()):
        col = cols[i % 2]
        with col:
            with st.container(border=True):
                # Récupération Données
                df_ticker = get_historical_data(ticker)
                
                # --- A. PRÉPARATION DES DATES ET PRIX ---
                now = datetime.now()
                
                if not df_ticker.empty:
                    current_price = float(df_ticker['Close'].iloc[-1])
                    # On prend les dates réelles du graphe
                    last_date = df_ticker.index[-1]
                    # Conversion timezone si nécessaire pour éviter les bugs de calcul
                    if last_date.tzinfo is None:
                        last_date = last_date.replace(tzinfo=None)
                    else:
                        last_date = last_date.replace(tzinfo=None) # On simplifie tout en "naïf"
                        
                else:
                    current_price = float(data['entry_price'])
                    last_date = now

                # --- B. LE SECRET : ON FORCE UNE FENÊTRE DE TEMPS LARGE ---
                # On crée artificiellement un début (il y a 4h) et une fin (dans 4h)
                # Cela garantit que les lignes SL/TP feront au moins 8 heures de long sur l'écran
                line_start = last_date - timedelta(hours=4)
                line_end = last_date + timedelta(hours=4)

                entry = float(data['entry_price'])
                tp = float(data['take_profit'])
                sl = float(data['stop_loss'])
                
                pct = ((current_price - entry) / entry) * 100
                color_t = "green" if pct >= 0 else "red"
                
                st.markdown(f"**{ticker}** : <span style='color:{color_t}'>{pct:.2f}%</span> | Prix: **{current_price:.2f}$**", unsafe_allow_html=True)

                # --- C. CONSTRUCTION DU GRAPHIQUE ---
                fig = go.Figure()

                # 1. Courbe du Prix (Historique)
                if not df_ticker.empty:
                    fig.add_trace(go.Scatter(
                        x=df_ticker.index, y=df_ticker['Close'],
                        mode='lines+markers', line=dict(color='blue', width=2),
                        marker=dict(size=4), name='Prix'
                    ))
                
                # 2. Point Actuel (Gros point)
                fig.add_trace(go.Scatter(
                    x=[last_date], y=[current_price],
                    mode='markers', marker=dict(size=12, color='blue', line=dict(width=2, color='white')),
                    showlegend=False
                ))

                # 3. TRACAGE DES LIGNES SUR LA FENÊTRE ÉLARGIE (Start -> End)
                
                # Take Profit (Vert)
                fig.add_trace(go.Scatter(
                    x=[line_start, line_end], y=[tp, tp],
                    mode='lines', line=dict(color='#00CC96', width=2, dash='dash'), name='TP'
                ))
                
                # Stop Loss (Rouge)
                fig.add_trace(go.Scatter(
                    x=[line_start, line_end], y=[sl, sl],
                    mode='lines', line=dict(color='#EF553B', width=2, dash='dash'), name='SL'
                ))
                
                # Entrée (Gris)
                fig.add_trace(go.Scatter(
                    x=[line_start, line_end], y=[entry, entry],
                    mode='lines', line=dict(color='gray', width=1, dash='dot'), name='Entrée'
                ))

                # --- D. MISE EN PAGE AXES ---
                vals = [current_price, sl, tp, entry]
                y_min, y_max = min(vals), max(vals)
                padding = (y_max - y_min) * 0.2 # 20% de marge

                fig.update_layout(
                    height=300,
                    margin=dict(l=10, r=10, t=30, b=20),
                    showlegend=False,
                    # On force la vue sur notre fenêtre élargie en X
                    xaxis=dict(
                        range=[line_start, line_end], 
                        showgrid=False
                    ),
                    # On force la vue en Y pour voir les SL/TP
                    yaxis=dict(
                        range=[y_min - padding, y_max + padding],
                        tickprefix="$",
                        tickformat=".2f",
                        showticklabels=True,
                        automargin=True, # Empêche de couper les prix
                        showline=True,
                        linecolor="black",
                        ticks="outside",
                        fixedrange=False
                    )
                )
                
                # Annotations Texte
                fig.add_annotation(x=line_end, y=tp, text="TP", xanchor="right", yshift=10, showarrow=False, font=dict(color="#00CC96"))
                fig.add_annotation(x=line_end, y=sl, text="SL", xanchor="right", yshift=-10, showarrow=False, font=dict(color="#EF553B"))
                
                st.plotly_chart(fig, use_container_width=True)