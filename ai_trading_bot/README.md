# 🤖 AI Trading Bot & Real-Time Dashboard

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Status](https://img.shields.io/badge/Status-Active-green)

Un système de trading algorithmique autonome intégrant l'IA **Grok** pour l'analyse de sentiment et un dashboard de supervision en temps réel.

## 🚀 Fonctionnalités

* **Acquisition & Scraping :** Module de récupération de données non structurées sur le web et connexion API (Yahoo Finance).
* **Intelligence Artificielle :** Intégration de l'IA **Grok** pour analyser le sentiment de marché (Bullish/Bearish) et influencer les décisions.
* **Trading Algorithmique :** Bot autonome gérant les ordres d'achat/vente avec gestion du risque (Stop Loss / Take Profit dynamiques).
* **Dashboard Live :** Interface interactive (**Streamlit/Plotly**) permettant de visualiser l'Equity Curve et les positions actives sur des graphiques boursiers.

## 🛠️ Installation

1.  Cloner le projet :
    ```bash
    git clone [https://github.com/joshualoz/ai-trading-bot.git](https://github.com/ton-pseudo/ai-trading-bot.git)
    cd ai-trading-bot
    ```

2.  Installer les dépendances :
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuration (Variables d'environnement) :**
    * Renommez le fichier `.env.example` en `.env`.
    * Ouvrez le fichier `.env` et ajoutez votre clé API Grok (xAI) :
        ```text
        GROK_API_KEY=votre_cle_ici
        ```
## 💻 Usage

* **Lancer le Bot :**
    ```bash
    python main.py
    ```
* **Lancer le Dashboard :**
    ```bash
    streamlit run dashboard.py
    ```

## ⚠️ Avertissement
Ce projet est à but éducatif. Le trading comporte des risques financiers.

## 👤 Auteur
**Joshua LOZANO** - [Mon LinkedIn](https://www.linkedin.com/in/joshua-lozano-ing/)
