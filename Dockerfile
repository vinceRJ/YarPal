# --- ÉTAPE 1 : Image de base légère ---
FROM python:3.11-slim

# Variables d'environnement Python — empêche la création de .pyc et bufferise stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# --- ÉTAPE 2 : Installation des dépendances système ---
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# --- ÉTAPE 3 : Utilisateur non-root (principe du moindre privilège) ---
RUN groupadd --gid 1001 larpal && \
    useradd --uid 1001 --gid larpal --shell /bin/bash --create-home larpal

# --- ÉTAPE 4 : Configuration du répertoire de travail ---
WORKDIR /app

# --- ÉTAPE 5 : Installation des dépendances Python ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- ÉTAPE 6 : Copie du code source et attribution des droits ---
COPY . .
RUN chown -R larpal:larpal /app

# Passage à l'utilisateur non-root
USER larpal

# --- ÉTAPE 7 : Exposition du port Streamlit ---
EXPOSE 8501

# --- ÉTAPE 8 : Healthcheck ---
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# --- ÉTAPE 9 : Lancement de LarPal ---
ENTRYPOINT ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
