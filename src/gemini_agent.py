import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

_GEMINI_SYSTEM = (
    "Tu es un analyste financier expert. Tu fournis des analyses fondamentales et stratégiques "
    "approfondies sur les marchés boursiers, les secteurs, les titres et les portefeuilles. "
    "Réponds en français, de façon structurée et avec des recommandations concrètes."
)


def ask_gemini_pro(prompt: str, context: str = "") -> str:
    """Utilise Gemini Flash pour une analyse financière approfondie."""
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel(model_name="gemini-2.0-flash")

    full_prompt = (
        f"{_GEMINI_SYSTEM}\n\n"
        f"Contexte disponible :\n{context}\n\n"
        f"Question : {prompt}"
    ) if context else f"{_GEMINI_SYSTEM}\n\nQuestion : {prompt}"

    try:
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        print(f"Erreur Gemini: {e}")
        return f"[Gemini indisponible — réponds toi-même à partir des données du portefeuille disponibles]"
