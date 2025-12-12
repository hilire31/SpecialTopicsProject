# Guide de démarrage rapide

Ce guide vous aidera à démarrer rapidement avec le chatbot entreprise.

## 🚀 Étapes de démarrage

### 1. Prérequis

Assurez-vous d'avoir installé:
- Python 3.9 ou supérieur
- Docker et Docker Compose
- Une clé API OpenAI

### 2. Installation

```bash
# Installer les dépendances
pip install -r requirements.txt

# Copier et configurer les variables d'environnement
cp .env.example .env
# Éditer .env et ajouter votre clé API OpenAI
```

### 3. Démarrer Elasticsearch

```bash
docker-compose up -d
```

Attendez quelques secondes que Elasticsearch soit prêt. Vous pouvez vérifier avec:
```bash
curl http://localhost:9200
```

### 4. Indexer des documents d'exemple

```bash
python scripts/index_documents.py
```

Vous devriez voir:
```
📚 Indexation des documents d'exemple...
Indexation de 5 documents...
✅ 5 documents indexés avec succès!
```

### 5. Lancer le chatbot

```bash
python src/main.py
```

### 6. Lancer le serveur MCP (optionnel)

```bash
# Run the MCP server to expose the protocol endpoints
uvicorn mcp_server.server:app --reload --port 8080
```

## 📝 Exemples d'utilisation

### Exemple basique

```python
from src.elasticsearch_client import ElasticsearchClient
from src.langgraph_chatbot import LangGraphChatbot
from src.models.permissions import Employee, PermissionLevel

# Créer un employé
employee = Employee(
    user_id="emp_001",
    name="Jean Dupont",
    email="jean.dupont@entreprise.com",
    department="RH",
    permission_level=PermissionLevel.MANAGER
)

# Initialiser le chatbot
es_client = ElasticsearchClient()
chatbot = LangGraphChatbot(es_client=es_client)

# Poser une question
response = chatbot.chat(
    query="Quelle est la politique de congés payés?",
    employee=employee
)
print(response)
```

### Exécuter les exemples complets

```bash
python examples/example_usage.py
```

## 🔍 Vérification

Pour vérifier que tout fonctionne:

1. **Vérifier Elasticsearch**: `curl http://localhost:9200/_cat/indices`
2. **Vérifier les documents indexés**: `curl http://localhost:9200/company_documents/_search?pretty`
3. **Tester le chatbot**: Lancer `python src/main.py` et poser une question

## 🐛 Dépannage

### Elasticsearch ne démarre pas

- Vérifiez que le port 9200 n'est pas déjà utilisé
- Vérifiez les logs: `docker-compose logs elasticsearch`
- Assurez-vous d'avoir au moins 1GB de RAM disponible

### Erreur "OpenAI API key not found"

- Vérifiez que votre fichier `.env` contient `OPENAI_API_KEY=your_key_here`
- Assurez-vous que le fichier `.env` est dans le répertoire racine du projet

### Aucun document trouvé

- Vérifiez que les documents ont été indexés: `python scripts/index_documents.py`
- Vérifiez les permissions de l'employé (certains documents nécessitent un niveau élevé)

## 📚 Prochaines étapes

1. **Ajouter vos propres documents**: Modifiez `scripts/index_documents.py` ou créez votre propre script
2. **Personnaliser les permissions**: Ajustez les niveaux de permission selon vos besoins
3. **Intégrer dans votre application**: Utilisez le chatbot comme service dans votre application

## 💡 Conseils

- Les documents sont indexés avec des embeddings vectoriels pour une recherche sémantique
- Les permissions sont vérifiées à deux niveaux: dans Elasticsearch et dans le code Python
- Vous pouvez personnaliser le modèle LLM dans `.env` (par défaut: `gpt-4o-mini`)

