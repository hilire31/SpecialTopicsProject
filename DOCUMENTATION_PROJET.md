# Documentation Complète du Projet - Chatbot Entreprise

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture du projet](#architecture-du-projet)
3. [Installation et démarrage](#installation-et-démarrage)
4. [Description des composants](#description-des-composants)
5. [Modes d'utilisation](#modes-dutilisation)
6. [Configuration](#configuration)
7. [Flux de données](#flux-de-données)

---

## Vue d'ensemble

Ce projet est un **chatbot intelligent pour entreprise** qui permet aux employés d'interroger une base de documents interne avec un système de gestion des permissions avancé. Le système utilise :

- **LangGraph** : Pour orchestrer le flux de conversation (recherche → génération)
- **Elasticsearch** : Pour le stockage et la recherche vectorielle des documents
- **OpenAI GPT** : Pour générer les réponses en langage naturel
- **Sentence Transformers** : Pour créer les embeddings des documents et requêtes

### Cas d'usage principaux

1. **Ajout de document** : Un utilisateur ajoute un document avec un niveau d'accès spécifique
2. **Requête avec accès compatible** : Un employé interroge le chatbot et obtient des informations selon son niveau hiérarchique
3. **Requête avec accès incompatible** : Un employé demande des informations qu'il ne peut pas voir → erreur de permission
4. **Gestion d'utilisateurs** : Un manager ou supérieur ajoute de nouveaux utilisateurs
5. **Modification de document** : Un utilisateur modifie un document auquel il a accès
6. **Suppression de document** : Un utilisateur supprime un document auquel il a accès

---

## Architecture du projet

### Structure des répertoires

```
SpecialTopicsProject/
│
├── src/                          # Code source principal
│   ├── api/                      # API REST complète
│   │   ├── server.py            # Serveur FastAPI principal (port 8000)
│   │   ├── models.py            # Modèles Pydantic pour l'API
│   │   └── README.md            # Documentation de l'API
│   │
│   ├── services/                 # Services métier
│   │   └── user_service.py     # Gestion des utilisateurs (stockage mémoire)
│   │
│   ├── models/                   # Modèles de données
│   │   ├── permissions.py       # Gestion des permissions (Employee, PermissionLevel)
│   │   └── document.py          # Modèle de document (CompanyDocument)
│   │
│   ├── elasticsearch_client.py   # Client Elasticsearch avec recherche vectorielle
│   ├── langgraph_chatbot.py     # Chatbot avec orchestration LangGraph
│   └── main.py                   # Application CLI interactive
│
├── mcp_server/                   # Serveur MCP (Model Context Protocol)
│   ├── server.py                # Serveur MCP (port 8080)
│   ├── mcp.yaml                 # Spécification MCP
│   └── README.md                # Documentation MCP
│
├── scripts/                      # Scripts utilitaires
│   └── index_documents.py       # Script d'indexation de documents d'exemple
│
├── examples/                     # Exemples d'utilisation
│   ├── example_usage.py         # Exemples d'utilisation du chatbot
│   └── mcp_client_example.py    # Exemples d'utilisation du serveur MCP
│
├── docker-compose.yml           # Configuration Docker (Elasticsearch + Kibana)
├── requirements.txt             # Dépendances Python
├── swagger.yaml                 # Spécification OpenAPI/Swagger
├── run_api.py                   # Script pour démarrer l'API REST
├── run_mcp_server.py            # Script pour démarrer le serveur MCP
│
├── README.md                     # Documentation principale (français)
├── README_EN.md                  # Documentation principale (anglais)
└── DOCUMENTATION_PROJET.md       # Ce document
```

---

## Installation et démarrage

### Prérequis

- **Python 3.9+**
- **Docker et Docker Compose**
- **Clé API OpenAI** (obtenue sur https://platform.openai.com/api-keys)

### Étapes d'installation

#### 1. Cloner le projet (si applicable)

```bash
git clone <repository-url>
cd SpecialTopicsProject
```

#### 2. Créer un environnement virtuel Python

```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Sur Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Sur Windows (CMD):
venv\Scripts\activate.bat

# Sur Linux/Mac:
source venv/bin/activate
```

#### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

#### 4. Configurer les variables d'environnement

Créer un fichier `.env` à la racine du projet :

```bash
# .env
OPENAI_API_KEY=sk-votre-clé-api-openai-ici
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=company_documents
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```

**Important** : Remplacez `sk-votre-clé-api-openai-ici` par votre vraie clé API OpenAI.

#### 5. Démarrer Elasticsearch et Kibana

```bash
docker-compose up -d
```

Cela démarre :
- **Elasticsearch** sur le port `9200`
- **Kibana** sur le port `5601` (interface web pour visualiser les données)

Attendez quelques secondes que les services soient prêts. Vous pouvez vérifier avec :

```bash
curl http://localhost:9200
```

#### 6. Indexer des documents d'exemple

```bash
python scripts/index_documents.py
```

Cela crée 5 documents d'exemple avec différents niveaux de permission.

---

## Description des composants

### 1. **src/models/** - Modèles de données

#### `permissions.py`
**Rôle** : Définit le système de permissions et les modèles d'employés

**Composants principaux** :
- `PermissionLevel` : Enum avec 4 niveaux (EMPLOYEE, MANAGER, DIRECTOR, EXECUTIVE)
- `DocumentPermission` : Permissions requises pour accéder à un document
- `Employee` : Modèle représentant un employé avec méthode `can_access()` pour vérifier les permissions

**Responsabilités** :
- Gérer la hiérarchie des permissions
- Vérifier si un employé peut accéder à un document

#### `document.py`
**Rôle** : Modèle de document d'entreprise

**Composants principaux** :
- `CompanyDocument` : Document avec titre, contenu, département, type, métadonnées et permissions

**Responsabilités** :
- Représenter un document dans le système
- Conversion vers/depuis le format Elasticsearch

---

### 2. **src/elasticsearch_client.py** - Client Elasticsearch

**Rôle** : Gérer toutes les interactions avec Elasticsearch

**Responsabilités principales** :
- **Création de l'index** : Crée automatiquement l'index avec le mapping approprié
- **Indexation de documents** : Indexe les documents avec leurs embeddings vectoriels
- **Recherche vectorielle** : Recherche sémantique avec similarité cosinus
- **Filtrage par permissions** : Filtre les résultats selon les permissions de l'employé
- **Gestion CRUD** : Créer, lire, mettre à jour, supprimer des documents

**Méthodes principales** :
- `index_document()` : Indexe un document unique
- `index_documents_bulk()` : Indexe plusieurs documents en une fois
- `search_documents()` : Recherche avec filtrage par permissions
- `get_document()` : Récupère un document par ID avec vérification de permission
- `list_documents()` : Liste les documents avec filtres (département, type, pagination)
- `update_document()` : Met à jour un document
- `delete_document()` : Supprime un document

**Technologies utilisées** :
- Elasticsearch 8.x pour le stockage
- Sentence Transformers pour générer les embeddings
- Recherche vectorielle avec similarité cosinus

---

### 3. **src/langgraph_chatbot.py** - Chatbot LangGraph

**Rôle** : Orchestrer le flux de conversation avec LangGraph

**Architecture** :
Le chatbot utilise un graphe LangGraph avec deux nœuds :
1. **`retrieve`** : Récupère les documents pertinents depuis Elasticsearch
2. **`generate`** : Génère la réponse avec le LLM en utilisant les documents récupérés

**Flux** :
```
Question → retrieve → generate → Réponse
```

**Méthodes principales** :
- `chat()` : Conversation simple (retourne uniquement la réponse)
- `chat_with_documents()` : Conversation avec documents récupérés (retourne réponse + documents)
- `_build_context()` : Construit le contexte formaté à partir des documents

**Responsabilités** :
- Orchestrer le workflow RAG (Retrieval-Augmented Generation)
- Construire les prompts système avec contexte
- Gérer l'historique de conversation
- Appeler le LLM OpenAI pour générer les réponses

---

### 4. **src/services/user_service.py** - Service de gestion des utilisateurs

**Rôle** : Gérer les utilisateurs du système

**Stockage** : En mémoire (peut être remplacé par une base de données)

**Méthodes principales** :
- `create_user()` : Crée un nouvel utilisateur
- `get_user()` : Récupère un utilisateur par ID
- `get_user_by_email()` : Récupère un utilisateur par email
- `list_users()` : Liste les utilisateurs avec filtres optionnels
- `get_user_data()` : Récupère les données brutes avec timestamps

**Utilisateurs par défaut** :
- `emp_001` : Jean Dupont (HR, Manager)
- `emp_002` : Marie Martin (IT, Employee)

---

### 5. **src/api/** - API REST complète

**Rôle** : Exposer une API REST complète conforme à la spécification Swagger

#### `server.py` - Serveur FastAPI principal

**Port** : `8000`

**Endpoints disponibles** :

**Documents** :
- `POST /documents` : Créer un document
- `GET /documents` : Lister les documents (avec filtres)
- `GET /documents/{doc_id}` : Obtenir un document spécifique
- `PUT /documents/{doc_id}` : Mettre à jour un document
- `DELETE /documents/{doc_id}` : Supprimer un document

**Chatbot** :
- `POST /chatbot/query` : Interroger le chatbot

**Utilisateurs** :
- `POST /users` : Créer un utilisateur (manager+ seulement)
- `GET /users` : Lister les utilisateurs (manager+ seulement)

**Authentification** :
- Utilise Bearer token (simplifié : user_id ou email comme token)
- Format : `Authorization: Bearer emp_001`

**Documentation interactive** :
- Swagger UI : `http://localhost:8000/docs`
- ReDoc : `http://localhost:8000/redoc`

#### `models.py` - Modèles API

**Rôle** : Définit tous les schémas Pydantic pour les requêtes/réponses API

**Modèles principaux** :
- `DocumentCreate`, `DocumentUpdate`, `DocumentResponse`
- `UserCreate`, `UserResponse`
- `ChatbotQuery`, `ChatbotResponse`
- `ErrorResponse`

---

### 6. **mcp_server/** - Serveur MCP (Model Context Protocol)

**Rôle** : Fournir une interface simplifiée pour les modèles IA et agents

**Port** : `8080`

**Endpoints** :
- `GET /mcp/spec` : Retourne la spécification MCP
- `POST /mcp/actions/retrieve_documents` : Récupère des documents
- `POST /mcp/actions/generate_response` : Génère une réponse
- `POST /mcp/actions/chat` : Action composite (récupération + génération)
- `GET /mcp/health` : Health check

**Différences avec l'API principale** :
- Pas d'authentification (l'employé est passé dans le body)
- Interface orientée actions plutôt que REST
- Conçu pour l'intégration avec des modèles IA

---

### 7. **scripts/index_documents.py** - Script d'indexation

**Rôle** : Créer et indexer des documents d'exemple

**Documents créés** :
1. Politique de congés payés (niveau: employee)
2. Manuel de sécurité informatique (niveau: employee)
3. Stratégie financière 2024 (niveau: director, département: Finance)
4. Plan de restructuration (niveau: executive)
5. Procédure de recrutement RH (niveau: manager, département: RH)

---

### 8. **src/main.py** - Application CLI interactive

**Rôle** : Interface en ligne de commande pour tester le chatbot

**Fonctionnalités** :
- Crée un employé d'exemple
- Boucle interactive pour poser des questions
- Affiche les réponses du chatbot
- Gère l'historique de conversation

---

## Modes d'utilisation

### Mode 1 : Application CLI interactive

```bash
python src/main.py
```

Permet de tester le chatbot en mode interactif avec un employé d'exemple.

### Mode 2 : API REST

**Démarrer le serveur** :
```bash
python run_api.py
```

**Utiliser l'API** :
```bash
# Lister les documents
curl -H "Authorization: Bearer emp_001" http://localhost:8000/documents

# Interroger le chatbot
curl -X POST http://localhost:8000/chatbot/query \
  -H "Authorization: Bearer emp_001" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Quelle est la politique de congés payés?",
    "conversation_history": []
  }'
```

**Documentation interactive** :
- Ouvrir `http://localhost:8000/docs` dans un navigateur

### Mode 3 : Serveur MCP

**Démarrer le serveur** :
```bash
python run_mcp_server.py
```

**Utiliser le serveur MCP** :
```bash
curl -X POST http://localhost:8080/mcp/actions/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the paid leave policy?",
    "employee": {
      "user_id": "emp_001",
      "name": "Jean Dupont",
      "email": "jean@company.com",
      "department": "HR",
      "permission_level": "manager"
    },
    "conversation_history": []
  }'
```

### Mode 4 : Utilisation programmatique

```python
from src.elasticsearch_client import ElasticsearchClient
from src.langgraph_chatbot import LangGraphChatbot
from src.models.permissions import Employee, PermissionLevel

# Créer un employé
employee = Employee(
    user_id="emp_001",
    name="Jean Dupont",
    email="jean@company.com",
    department="HR",
    permission_level=PermissionLevel.MANAGER
)

# Initialiser les services
es_client = ElasticsearchClient()
chatbot = LangGraphChatbot(es_client=es_client)

# Poser une question
response = chatbot.chat(
    query="Quelle est la politique de congés payés?",
    employee=employee
)
print(response)
```

---

## Configuration

### Variables d'environnement (.env)

| Variable | Description | Défaut |
|----------|-------------|--------|
| `OPENAI_API_KEY` | Clé API OpenAI (requis) | - |
| `ELASTICSEARCH_URL` | URL d'Elasticsearch | `http://localhost:9200` |
| `ELASTICSEARCH_INDEX` | Nom de l'index | `company_documents` |
| `LLM_MODEL` | Modèle LLM OpenAI | `gpt-4o-mini` |
| `EMBEDDING_MODEL` | Modèle d'embedding | `text-embedding-3-small` |

### Ports utilisés

| Service | Port | URL |
|---------|------|-----|
| Elasticsearch | 9200 | `http://localhost:9200` |
| Kibana | 5601 | `http://localhost:5601` |
| API REST | 8000 | `http://localhost:8000` |
| Serveur MCP | 8080 | `http://localhost:8080` |

---

## Flux de données

### Flux complet d'une requête chatbot

```
1. Utilisateur pose une question
   ↓
2. API reçoit la requête avec token d'authentification
   ↓
3. Extraction de l'employé depuis le token
   ↓
4. LangGraph démarre le workflow
   ↓
5. Nœud "retrieve" :
   - Génère l'embedding de la requête
   - Recherche dans Elasticsearch avec similarité vectorielle
   - Filtre les résultats par permissions de l'employé
   - Retourne les 5 documents les plus pertinents
   ↓
6. Nœud "generate" :
   - Construit le contexte à partir des documents
   - Crée le prompt système avec infos employé
   - Ajoute l'historique de conversation
   - Appelle OpenAI GPT
   - Génère la réponse
   ↓
7. Retourne la réponse + documents utilisés
```

### Système de permissions

**Hiérarchie** :
```
EMPLOYEE (1) < MANAGER (2) < DIRECTOR (3) < EXECUTIVE (4)
```

**Vérifications effectuées** :
1. **Niveau hiérarchique** : L'employé doit avoir un niveau >= niveau requis du document
2. **Département** : Si le document a des départements autorisés, l'employé doit être dans la liste
3. **Utilisateur spécifique** : Si le document a des utilisateurs autorisés, l'employé doit être dans la liste

**Double vérification** :
- Filtrage dans Elasticsearch (performance)
- Vérification dans le code Python (sécurité)

---

## Visualisation des données

### Kibana

Kibana permet de visualiser les documents indexés :

1. Ouvrir `http://localhost:5601`
2. Créer un index pattern : `company_documents`
3. Aller dans "Discover" pour voir les documents
4. Filtrer par département, type, niveau de permission, etc.

### Requêtes Elasticsearch directes

```bash
# Voir tous les documents
curl "http://localhost:9200/company_documents/_search?pretty"

# Rechercher un document spécifique
curl "http://localhost:9200/company_documents/_search?pretty" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "match": {
        "title": "congés"
      }
    }
  }'
```

---

## Dépannage

### Elasticsearch ne démarre pas

```bash
# Vérifier les logs
docker-compose logs elasticsearch

# Vérifier que le port 9200 n'est pas utilisé
netstat -an | findstr 9200  # Windows
lsof -i :9200                # Linux/Mac

# Redémarrer
docker-compose restart elasticsearch
```

### Erreur "OpenAI API key not found"

- Vérifier que le fichier `.env` existe à la racine
- Vérifier que `OPENAI_API_KEY` est défini
- Vérifier que le fichier est chargé (pas d'espaces avant/après)

### Erreur de module Python

```bash
# Réinstaller les dépendances
pip install -r requirements.txt

# Vérifier l'environnement virtuel
python --version
pip list
```

### Documents non trouvés

- Vérifier que les documents ont été indexés : `python scripts/index_documents.py`
- Vérifier les permissions de l'employé
- Vérifier dans Kibana que les documents existent

---

## Architecture technique détaillée

### Stack technologique

- **Backend** : Python 3.9+
- **Framework API** : FastAPI
- **Orchestration** : LangGraph
- **Base de données** : Elasticsearch 8.15.0
- **LLM** : OpenAI GPT (gpt-4o-mini par défaut)
- **Embeddings** : Sentence Transformers (all-MiniLM-L6-v2)
- **Validation** : Pydantic v2
- **Conteneurisation** : Docker Compose

### Recherche vectorielle

Le système utilise la recherche vectorielle pour trouver des documents pertinents :

1. **Indexation** : Chaque document est converti en vecteur d'embedding (384 dimensions)
2. **Requête** : La question de l'utilisateur est convertie en vecteur
3. **Similarité** : Calcul de la similarité cosinus entre le vecteur requête et les vecteurs documents
4. **Résultats** : Retourne les documents les plus similaires

### Sécurité

- **Authentification** : Bearer token (simplifié, à remplacer par JWT en production)
- **Autorisation** : Vérification des permissions à deux niveaux
- **Validation** : Validation des données avec Pydantic
- **Gestion d'erreurs** : Codes HTTP appropriés (400, 401, 403, 404, 500)

---

## Conclusion

Ce projet fournit une solution complète de chatbot d'entreprise avec :

✅ **Recherche sémantique** dans les documents  
✅ **Gestion fine des permissions** (niveau, département, utilisateur)  
✅ **API REST complète** conforme Swagger  
✅ **Interface MCP** pour intégration avec modèles IA  
✅ **Orchestration LangGraph** pour workflow RAG  
✅ **Documentation complète** et exemples  

Pour toute question ou problème, consultez les README individuels dans chaque répertoire ou la documentation Swagger à `http://localhost:8000/docs`.

