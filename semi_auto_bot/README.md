## 📱 Mode Semi-Automatique (Signaux Telegram)

Le projet propose une version "Assistant" interactive. Au lieu de laisser l'IA gérer tout le Machine Learning, ce mode vous envoie des signaux sur Telegram et attend votre validation manuelle (`ACHAT` ou `NON`) avant d'agir.

### Fonctionnalités de ce mode
* **Analyse Hybride :** Combine l'IA Grok (Sentiment) et Yahoo Finance (Technique).
* **Validation Humaine :** Vous recevez une alerte, vous décidez.
* **Gestion Automatique :** Une fois validé, le bot gère seul la sortie (Take Profit / Stop Loss).

### 🎮 Commandes Telegram
| Commande | Exemple | Description |
| :--- | :--- | :--- |
| **Valider** | `ACHAT AMD` | Le bot achète et surveille la position. |
| **Refuser** | `NON AMD` | Le bot ignore ce signal pour le moment. |
| **Bilan** | `STATS` | Affiche vos gains/pertes (P&L) actuels. |

---

### ⚙️ Installation du Mode Telegram

Ce mode utilise une version allégée du bot (sans le module d'entraînement lourd). Voici comment l'activer :

1.  **Préparation :**
    * Allez dans le dossier principal `ai_trading_bot`.
    * Supprimez (ou déplacez ailleurs) les fichiers lourds : `ml_manager.py` et `entrainement_bot.py`.

2.  **Activation :**
    * Copiez le fichier `bot.py` (fourni dans le dossier `semi_auto_bot` ou à la racine).
    * Collez-le à la place des anciens fichiers.

3.  **Lancement :**
    Lancez simplement ce script :
    ```bash
    python bot.py
    ```

> **Note :** Assurez-vous d'avoir bien configuré votre Token Telegram dans le fichier `.env` ou `config.py` avant de lancer ce mode.
