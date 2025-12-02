FROM python:3.11-slim

WORKDIR /app

# Copier les requirements globaux
COPY requirements.txt /app/requirements.txt

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code Streamlit
COPY streamlit_app/ /app/

# Copier le backend
COPY src/ /app/src/

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
