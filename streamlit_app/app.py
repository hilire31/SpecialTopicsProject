import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Ajouter le répertoire parent du projet au path (pour importer `src`)
# `app.py` se trouve dans `streamlit_app/`, donc on ajoute le parent parent
# (le répertoire racine du dépôt) pour que `import src...` fonctionne.
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.elasticsearch_client import ElasticsearchClient
from src.langgraph_chatbot import LangGraphChatbot
from src.models.permissions import Employee, PermissionLevel


# -------------------------------------------------------
# 1) Chargement des variables d'environnement
# -------------------------------------------------------
load_dotenv()


# -------------------------------------------------------
# 2) Fonctions utilitaires
# -------------------------------------------------------
def create_example_employee() -> Employee:
    """Crée un employé fictif (remplaçable plus tard par un login réel)."""
    return Employee(
        user_id="emp_001",
        name="Jean Dupont",
        email="jean.dupont@entreprise.com",
        department="RH",
        permission_level=PermissionLevel.EXECUTIVE
    )


def init_chatbot():
    """Initialise le client Elasticsearch et le chatbot."""
    es_client = ElasticsearchClient(
        es_url=os.getenv("ELASTICSEARCH_URL", "http://localhost:9200"),
        index_name=os.getenv("ELASTICSEARCH_INDEX", "company_documents")
    )

    chatbot = LangGraphChatbot(
        es_client=es_client,
        llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini")
    )

    return chatbot


# -------------------------------------------------------
# 3) Configuration Streamlit
# -------------------------------------------------------
st.set_page_config(
    page_title="Chatbot Enterprise",
    page_icon="🤖",
    layout="centered",
)

st.title("🤖 Chatbot d'entreprise — Interface utilisateur")
st.markdown("Interrogez les documents internes avec permissions gérées automatiquement.")


# -------------------------------------------------------
# 4) Initialisation des éléments de session (persistants)
# -------------------------------------------------------
if "employee" not in st.session_state:
    st.session_state.employee = create_example_employee()

if "chatbot" not in st.session_state:
    st.session_state.chatbot = init_chatbot()

if "history" not in st.session_state:
    st.session_state.history = []


employee = st.session_state.employee
chatbot = st.session_state.chatbot
history = st.session_state.history


# -------------------------------------------------------
# 5) Affichage profil employé
# -------------------------------------------------------
with st.sidebar:
    st.header("👤 Employé connecté")
    st.write(f"**Nom :** {employee.name}")
    st.write(f"**Email :** {employee.email}")
    st.write(f"**Département :** {employee.department}")
    st.write(f"**Permission :** `{employee.permission_level.value}`")
    st.markdown("---")
    st.caption("Ces informations pourront être remplacées plus tard par un vrai système d'authentification.")


# -------------------------------------------------------
# 6) Zone de chat
# -------------------------------------------------------
st.subheader("💬 Discussion")

# Afficher l'historique
for msg in history:
    role = "🧑 Vous" if msg["role"] == "user" else "🤖 Assistant"
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# -------------------------------------------------------
# 7) Input utilisateur
# -------------------------------------------------------
query = st.chat_input("Écrivez votre message...")

if query:
    # Afficher immédiatement le message
    st.chat_message("user").markdown(query)
    history.append({"role": "user", "content": query})

    # Traitement par le chatbot
    with st.chat_message("assistant"):
        with st.spinner("Analyse des documents..."):
            response = chatbot.chat(
                query=query,
                employee=employee,
                conversation_history=history
            )

        st.markdown(response)
        history.append({"role": "assistant", "content": response})
