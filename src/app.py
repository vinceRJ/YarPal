import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import re
from openai_agent import run_financial_agent, load_portfolio, get_portfolio_status, PORTFOLIO_PATH
from data_fetch import get_historical_prices

TICKER_RE = re.compile(r'^[A-Z0-9]{1,6}(\.[A-Z]{1,2})?$')

st.set_page_config(page_title="LarPal - Votre Allié Financier", page_icon="🌤️", layout="wide")

# --- AUTHENTICATION SYSTEM ---
def check_password():
    """Returns True if the user had the correct password."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    # Show input for password
    st.title("🌤️ Bienvenue sur LarPal")
    st.markdown("---")
    pwd = st.text_input("Veuillez saisir le code d'accès LarPal pour continuer :", type="password")
    
    # Check against environment variable
    master_pwd = os.getenv("LARPAL_PASSWORD")  # Pas de valeur par défaut — doit être défini explicitement

    if st.button("Déverrouiller LarPal"):
        if not master_pwd:
            st.error("⚠️ Variable LARPAL_PASSWORD non configurée. Définissez-la dans votre fichier .env.")
        elif pwd == master_pwd:
            st.session_state["password_correct"] = True
            st.success("Accès autorisé ! Chargement de LarPal...")
            st.rerun()
        else:
            st.error("😕 Code incorrect. Veuillez réessayer.")

    st.info("💡 Définissez la variable 'LARPAL_PASSWORD' dans votre fichier .env ou vos secrets de déploiement.")
    return False

if not check_password():
    st.stop()

# --- CUSTOM CSS: WARM & FRIENDLY STYLE ---
st.markdown("""
    <style>
    /* Palette LarPal : Fond crème, texte gris doux, accents ambre/vert */
    [data-testid="stAppViewContainer"] { 
        background-color: #fdfbf7; 
        color: #4a4a4a; 
    }
    [data-testid="stSidebar"] { 
        background-color: #fff9f0; 
        border-right: 1px solid #f0e6d2;
    }
    .stMetric { 
        background-color: #ffffff; 
        border: none;
        padding: 20px; 
        border-radius: 15px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    .stDataFrame { 
        border-radius: 15px; 
        overflow: hidden;
    }
    h1, h2, h3 { 
        color: #2d3436 !important; 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 600;
    }
    /* Style des bulles de chat LarPal */
    .stChatMessage { 
        background-color: #ffffff; 
        border: 1px solid #f1f2f6; 
        border-radius: 20px; 
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
        margin-bottom: 15px;
        padding: 15px;
    }
    /* Boutons arrondis LarPal */
    .stButton>button {
        border-radius: 20px;
        background-color: #ff9f43;
        color: white;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #ee5253;
        transform: scale(1.02);
    }
    </style>
    """, unsafe_allow_html=True)

def save_portfolio(data):
    with open(PORTFOLIO_PATH, "w") as f:
        json.dump(data, f, indent=4)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🌤️ Menu LarPal")
    portfolio = load_portfolio()
    selected_account = st.selectbox("Afficher mes placements", ["Vue d'ensemble", "Mon PEA", "Mon CTO"])
    
    st.markdown("---")
    with st.expander("📝 Gérer mes actifs"):
        # Utilisation de clés session_state pour réinitialiser
        acc_type = st.selectbox("Quel compte ?", ["PEA", "CTO"], key="add_acc_type")
        new_ticker = st.text_input("Symbole boursier (ex: MC.PA)", key="add_ticker").upper().strip()
        new_name = st.text_input("Nom de l'entreprise", key="add_name")
        new_qty = st.number_input("Nombre de titres", min_value=0.0, key="add_qty")
        new_cost = st.number_input("Prix d'achat moyen", min_value=0.0, key="add_cost")
        
        if st.button("Enregistrer dans LarPal"):
            if new_ticker and new_name:
                if not TICKER_RE.match(new_ticker):
                    st.error("Symbole boursier invalide. Utilisez uniquement des lettres, chiffres et un point optionnel (ex: MC.PA, NVDA).")
                elif len(new_name) > 100:
                    st.error("Nom trop long (100 caractères max).")
                else:
                    portfolio[acc_type][new_ticker] = {"name": new_name[:100], "quantity": new_qty, "avg_cost": new_cost}
                    save_portfolio(portfolio)
                    st.success("C'est fait ! LarPal a mis à jour votre portefeuille. ✨")
                    # Reset des champs dans session_state
                    st.session_state["add_ticker"] = ""
                    st.session_state["add_name"] = ""
                    st.session_state["add_qty"] = 0.0
                    st.session_state["add_cost"] = 0.0
                st.rerun()

    with st.expander("🗑️ Retirer un actif"):
        del_acc = st.selectbox("Choisir le compte", ["PEA", "CTO"])
        if portfolio[del_acc]:
            ticker_to_del = st.selectbox("L'actif à supprimer", list(portfolio[del_acc].keys()))
            if st.button("Confirmer le retrait"):
                del portfolio[del_acc][ticker_to_del]
                save_portfolio(portfolio)
                st.warning(f"{ticker_to_del} n'est plus suivi par LarPal.")
                st.rerun()
        else:
            st.write("Rien à supprimer ici !")

# --- MAIN INTERFACE ---
st.title("Ravi de vous revoir ! ☕")
st.subheader("Jetons un œil à la santé de vos finances aujourd'hui.")
st.markdown("---")

status_raw = get_portfolio_status(None if selected_account == "Vue d'ensemble" else selected_account.replace("Mon ", ""))
status_data = json.loads(status_raw)

all_assets = []
for acc, assets in status_data.items():
    for a in assets:
        a['Compte'] = acc
        all_assets.append(a)

df = pd.DataFrame(all_assets)

if not df.empty:
    # --- SECURITE : Nettoyage des données ---
    for col in ['price_eur', 'quantity', 'avg_cost', 'volatility', 'performance_pct']:
        if col not in df.columns:
            df[col] = 0
    df = df.fillna(0)

    # Advanced Metrics
    df['Valeur Actuelle'] = df['price_eur'] * df['quantity']
    df['Valeur (Investi)'] = df['avg_cost'] * df['quantity']
    df['Plus-value (EUR)'] = df['Valeur Actuelle'] - df['Valeur (Investi)']
    
    total_market_val = df['Valeur Actuelle'].sum()
    total_profit = df['Plus-value (EUR)'].sum()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Capital total", f"{total_market_val:,.2f} €")
    m2.metric("Plus-value globale", f"{total_profit:,.2f} €", delta=f"{(total_profit/total_market_val*100 if total_market_val > 0 else 0):.2f}%")
    m3.metric("Actifs suivis", len(df))

    st.markdown("---")

    # Portfolio Table with Highlight
    st.subheader("Le détail de vos positions")
    
    def style_negative(v):
        if isinstance(v, (int, float)) and v < 0:
            return 'background-color: #ffeef0; color: #d63031; font-weight: bold;'
        return ''

    df_display = df[['Compte', 'name', 'ticker', 'quantity', 'avg_cost', 'Valeur (Investi)', 'price_eur', 'performance_pct', 'Plus-value (EUR)']]
    
    # Application du style
    styled_df = df_display.style.applymap(style_negative, subset=['performance_pct', 'Plus-value (EUR)'])
    
    st.dataframe(
        styled_df,
        column_config={
            "name": "Nom de l'action",
            "avg_cost": st.column_config.NumberColumn("Prix d'achat", format="%.2f €"),
            "Valeur (Investi)": st.column_config.NumberColumn("Valeur (Investi)", format="%.2f €"),
            "price_eur": st.column_config.NumberColumn("Prix actuel (€)", format="%.2f €"),
            "performance_pct": st.column_config.NumberColumn("Perf %", format="%.2f%%"),
            "Plus-value (EUR)": st.column_config.NumberColumn("Gain/Perte", format="%.2f €")
        },
        use_container_width=True, hide_index=True
    )

    # Charts
    c1, c2 = st.columns(2)
    with c1:
        fig_alloc = px.pie(df, values='Valeur Actuelle', names='name', 
                           title="Répartition de mon capital", 
                           hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_alloc.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_alloc, use_container_width=True)
    with c2:
        fig_perf = px.bar(df, x='name', y='performance_pct', 
                          color='performance_pct', title="Performance par action",
                          color_continuous_scale='Emrld', range_color=[-20, 20])
        fig_perf.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_perf, use_container_width=True)

st.markdown("---")

# --- CONVIVIAL CHAT ---
st.subheader("💬 Une question pour LarPal ?")
if "messages" not in st.session_state:
    st.session_state.messages = []

def get_clean_hist(ticker):
    hist = get_historical_prices(ticker)
    if not hist.empty:
        # Corrige l'erreur MultiIndex si présente
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)
        return hist
    return pd.DataFrame()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "chart_ticker" in message:
            hist = get_clean_hist(message["chart_ticker"])
            if not hist.empty:
                fig = px.line(hist, y="Close", title=f"Évolution de {message['chart_ticker']}")
                fig.update_layout(template="simple_white")
                st.plotly_chart(fig, use_container_width=True)

if prompt := st.chat_input("Ex: LarPal, peux-tu analyser mes positions sur le PEA ?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("🔮 LarPal réfléchit...", expanded=True) as status:
            st.write("📡 Récupération des cours en temps réel...")
            # On pourrait ici ajouter de la logique pour détecter quel outil est utilisé, 
            # mais on simule le flux pour l'UX
            response = run_financial_agent(prompt)
            st.write("🔍 Analyse des actualités et du contexte...")
            st.write("🧠 Synthèse stratégique finale...")
            status.update(label="✨ Analyse terminée !", state="complete", expanded=False)

        st.markdown(response)

        
        # Détection de ticker pour graphique auto — uniquement sur des symboles valides du portefeuille
        portfolio_tickers = {t for acc in load_portfolio().values() for t in acc}
        words = prompt.upper().split()
        potential_ticker = next((w for w in words if TICKER_RE.match(w) and w in portfolio_tickers), None)
        
        msg_to_save = {"role": "assistant", "content": response}
        if potential_ticker:
            hist = get_clean_hist(potential_ticker)
            if not hist.empty:
                fig = px.line(hist, y="Close", title=f"Historique : {potential_ticker}")
                fig.update_layout(template="simple_white")
                st.plotly_chart(fig, use_container_width=True)
                msg_to_save["chart_ticker"] = potential_ticker
        
        st.session_state.messages.append(msg_to_save)

# --- FOOTER & LEGAL ---
st.markdown("---")
st.caption("⚠️ **Avertissement :** LarPal utilise des Intelligences Artificielles qui peuvent commettre des erreurs. Les informations et conseils fournis ne constituent pas des conseils financiers officiels. Vérifiez toujours les données avant de prendre une décision d'investissement.")
