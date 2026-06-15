import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from data_fetch import get_current_data, get_historical_prices, search_financial_news
from gemini_agent import ask_gemini_pro

_SYSTEM_MESSAGE = (
    "Tu es LarPal, l'assistant financier personnel de Vince. Tu l'aides à suivre et analyser "
    "son portefeuille boursier (PEA et CTO), à surveiller l'actualité des marchés, à évaluer "
    "ses risques et à prendre de meilleures décisions d'investissement.\n\n"
    "TU PEUX :\n"
    "- Analyser la performance, la diversification et les risques du portefeuille\n"
    "- Rechercher l'actualité financière d'un titre ou d'un secteur\n"
    "- Suggérer des pistes de diversification (secteurs, zones géographiques, titres)\n"
    "- Recommander de renforcer ou d'alléger une position selon le contexte\n"
    "- Répondre à toute question financière ou boursière, même complexe ou multi-étapes\n"
    "- Utiliser le contexte de la conversation pour répondre aux questions de suivi\n\n"
    "OUTILS DISPONIBLES :\n"
    "- 'get_portfolio_status' : données en temps réel du PEA et du CTO\n"
    "- 'search_financial_news' : actualités récentes sur un titre ou le marché\n"
    "- 'deep_financial_analysis' : analyse fondamentale approfondie via Gemini Pro\n\n"
    "VOCABULAIRE : En français financier, 'action(s)' = titre(s) boursier(s). "
    "'Alléger' = réduire une position. 'Renforcer' = augmenter une position.\n\n"
    "Réponds en français, de façon claire et directe. Si une analyse nécessite plusieurs outils, "
    "utilise-les tous avant de synthétiser. Tu peux exprimer un avis et formuler des recommandations concrètes."
)


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PORTFOLIO_PATH = os.path.join(os.path.dirname(__file__), "portfolio.json")

def load_portfolio():
    with open(PORTFOLIO_PATH, "r") as f:
        return json.load(f)

def get_portfolio_status(account_type: str = None):
    """Calcule la performance actuelle du portefeuille avec gestion des devises."""
    portfolio = load_portfolio()
    accounts = [account_type] if account_type else portfolio.keys()
    
    report = {}
    for acc in accounts:
        tickers = list(portfolio[acc].keys())
        market_data = get_current_data(tickers)
        
        acc_report = []
        for t, data in portfolio[acc].items():
            current = market_data.get(t, {})
            price = current.get("price", 0)
            price_eur = current.get("price_eur", price)
            
            perf = ((price - data["avg_cost"]) / data["avg_cost"]) * 100 if price else 0
            acc_report.append({
                "ticker": t,
                "name": data.get("name", t),
                "quantity": data["quantity"],
                "avg_cost": data["avg_cost"],
                "price": price,
                "price_eur": price_eur,
                "currency": current.get("currency", "?"),
                "performance_pct": round(perf, 2),
                "day_change_pct": current.get("change_pct", 0),
                "volatility": current.get("volatility", 0)
            })
        report[acc] = acc_report
    return json.dumps(report, indent=2)

def run_financial_agent(user_query: str, history: list = None):
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_portfolio_status",
                "description": (
                    "TOUJOURS appeler pour toute question sur le portefeuille : performance, positions, "
                    "plus-values, diversification, risques, comparaison PEA/CTO. "
                    "Retourne les prix en temps réel, les quantités, le coût moyen et la performance de chaque ligne."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_type": {"type": "string", "enum": ["PEA", "CTO"], "description": "Laisser vide pour tout le portefeuille"}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_financial_news",
                "description": (
                    "Recherche des actualités récentes sur un titre, un secteur ou le marché. "
                    "Appeler dès qu'une question mentionne 'news', 'actualité', 'récent', 'aujourd'hui', "
                    "ou demande pourquoi un titre monte/baisse."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Sujet de recherche précis (ex: 'LVMH résultats 2025', 'risques secteur tech')"}
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "deep_financial_analysis",
                "description": (
                    "Analyse fondamentale et stratégique approfondie par Gemini. Appeler pour : "
                    "diversification, analyse de risque à moyen/long terme, recommandations sectorielles, "
                    "comparaison de titres, ou toute analyse complexe nécessitant un raisonnement poussé."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "La question ou l'analyse à effectuer"},
                        "context": {"type": "string", "description": "Données du portefeuille ou news à inclure dans l'analyse"}
                    },
                    "required": ["prompt"]
                }
            }
        }
    ]

    messages = [{"role": "system", "content": _SYSTEM_MESSAGE}]
    if history:
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_query})

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    if tool_calls:
        available_functions = {
            "get_portfolio_status": get_portfolio_status,
            "search_financial_news": search_financial_news,
            "deep_financial_analysis": ask_gemini_pro
        }
        messages.append(response_message)
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            if function_name not in available_functions:
                # Rejette silencieusement les noms de fonction non autorisés (prompt injection)
                continue
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(**function_args)
            
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_response,
            })
        
        second_response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        return second_response.choices[0].message.content
    
    return response_message.content
