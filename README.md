# 🌤️ YarPal : Votre copilote d'investissement intelligent

Bienvenue dans l'univers de **YarPal**, un assistant financier personnel conçu pour simplifier la gestion de vos portefeuilles **PEA** et **CTO**. Né d'un besoin de clarté et d'analyse en temps réel, YarPal utilise la puissance des agents autonomes (GPT-4o et Gemini 1.5 Pro) pour transformer vos données boursières en décisions stratégiques.

## 🌟 Pourquoi utiliser YarPal ?
- **Tout au même endroit** : Visualisez votre PEA et votre CTO dans une interface unique, chaleureuse et fluide.
- **L'intelligence à votre service** : YarPal ne se contente pas d'afficher des chiffres. Il explique les hauts et les bas du marché grâce à ses agents IA.
- **Analyse sans limite** : Profitez de la fenêtre contextuelle géante de Gemini pour des rapports de fond sur vos actifs.

## 🚀 Prêt à commencer ?

### 1. Installation
Récupérez le projet sur votre machine :
```bash
git clone https://github.com/vinceRJ/YarPal.git
cd financial_assistant
pip install -r requirements.txt
```

### 2. Configurez vos "cerveaux" (Clés API)
Pour que YarPal puisse réfléchir et chercher des infos, il a besoin de ses clés API. Chaque clé apporte un "super-pouvoir" spécifique :

*   **OpenAI Key (GPT-4o)** : C'est le **Chef d'Orchestre**. Il gère l'interface, discute avec vous et pilote les autres outils.
    *   👉 [Créer ma clé OpenAI](https://platform.openai.com/api-keys)
*   **Gemini Key (1.5 Pro)** : C'est **l'Analyste Expert**. Grâce à sa mémoire géante, il traite les rapports financiers très longs et les analyses de fond.
    *   👉 [Créer ma clé Google Gemini (Gratuit)](https://aistudio.google.com/)
*   **Tavily Key (Standard)** : Ce sont les **Yeux de YarPal**. Elle lui permet de fouiller le Web pour trouver les news qui font bouger vos actions.
    *   👉 [Créer ma clé Tavily (Gratuit)](https://tavily.com/)
*   **Perplexity Key (Premium)** : Si vous avez un abonnement Pro, utilisez cette clé pour obtenir des **analyses de news de niveau professionnel**, déjà synthétisées et sourcées.
    *   👉 [Créer ma clé Perplexity API](https://www.perplexity.ai/settings/api)

**Installation des clés :**
1. À la racine du projet, créez un fichier `.env`.
2. Copiez et remplissez les lignes suivantes :
   ```env
   OPENAI_API_KEY=votre_cle_openai
   GEMINI_API_KEY=votre_cle_google
   TAVILY_API_KEY=votre_cle_tavily
   PERPLEXITY_API_KEY=votre_cle_perplexity # Optionnel (Premium)
   YARPAL_PASSWORD=votre_code_secret
   USER_NAME=VotrePrenom
   ```

### 3. Lancez YarPal
```bash
python -m streamlit run src/app.py
```

## 🛠️ Dans les coulisses
- **Langage** : Python
- **Interface** : Streamlit
- **Intelligence** : OpenAI GPT-4o & Google Gemini 1.5 Pro
- **Données** : Yahoo Finance (via yfinance) & Tavily Search

## ☁️ Déploiement en ligne (Streamlit Community Cloud)

Chaque utilisateur peut déployer **sa propre instance privée** de YarPal gratuitement.

### Étapes

1. **Forkez** ce dépôt sur votre compte GitHub.
2. Connectez-vous sur [share.streamlit.io](https://share.streamlit.io) avec votre compte GitHub.
3. Créez une nouvelle app en pointant vers `src/app.py` de votre fork.
4. Dans **Settings → Secrets**, ajoutez vos clés au format TOML :
   ```toml
   OPENAI_API_KEY = "sk-..."
   GEMINI_API_KEY = "AIza..."
   TAVILY_API_KEY = "tvly-..."
   YARPAL_PASSWORD = "votre_mot_de_passe_fort"
   USER_NAME = "VotrePrenom"
   ```
5. Cliquez sur **Deploy** — votre YarPal est en ligne en moins de 2 minutes.

### ⚠️ Limitation importante : persistance du portefeuille

Sur Streamlit Cloud, les fichiers écrits localement (`portfolio.json`) **sont effacés à chaque redémarrage** de l'app. Pour contourner cela :
- **Solution simple** : utilisez YarPal en local (`streamlit run src/app.py`) et conservez votre `portfolio.json` sur votre machine.
- **Solution avancée** (prochaine évolution) : connecter une base de données Supabase (gratuite) pour une persistance des données en ligne. Voir [supabase.com](https://supabase.com).

---

## 🛡️ Sécurité & Confidentialité

Votre vie privée est sacrée. YarPal est conçu pour que vos données de portefeuille (`portfolio.json`) et vos clés API (`.env`) restent **exclusivement sur votre machine**. Elles ne sont jamais envoyées sur GitHub.

### Protection contre les injections de prompt

YarPal intègre plusieurs défenses contre les tentatives de manipulation des agents IA :

- **Détection de patterns malveillants** : les requêtes contenant des tentatives de redéfinition de rôle ("ignore previous instructions", "system message addendum", etc.) sont bloquées avant d'atteindre les modèles.
- **Délimiteurs structurels** : les entrées utilisateur et les données externes (news, marchés) sont encapsulées dans des balises XML pour les isoler des instructions système.
- **Messages système durcis** : les deux agents (GPT-4o et Gemini Pro) reçoivent des instructions explicites pour ignorer toute directive présente dans les données qu'ils traitent.
- **Validation des tool calls** : seules les fonctions prédéfinies peuvent être appelées par les agents — toute tentative d'appel de fonction inconnue est rejetée.

> Ces défenses réduisent significativement le risque, mais aucun système n'est à 100 % inviolable. Ne laissez pas YarPal accéder à des données sensibles non liées à vos finances.
