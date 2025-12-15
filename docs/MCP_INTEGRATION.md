# Intégration MCP dans le Chatbot LangGraph

## Vue d'ensemble

Le chatbot LangGraph a été intégré avec le serveur MCP (Model Context Protocol) pour permettre aux utilisateurs d'effectuer des actions directement depuis le chatbot, comme créer des utilisateurs ou des documents.

## Architecture

### Composants

1. **Serveur MCP** (`mcp_server/server.py`)
   - Expose des endpoints REST pour les actions
   - Gère les permissions et la validation
   - Actions disponibles : `create_user`, `create_document`

2. **Outils LangChain** (`src/tools/mcp_tools.py`)
   - Wrappers LangChain pour appeler le serveur MCP
   - Gestion automatique des permissions
   - Messages d'erreur en français

3. **Chatbot LangGraph** (`src/langgraph_chatbot.py`)
   - Intègre les outils MCP via LangChain
   - Détection automatique des intentions d'action
   - Exécution des outils et génération de réponse

## Fonctionnalités

### Création d'utilisateurs

**Permission requise** : Manager ou supérieur

**Exemple d'utilisation** :
```
Utilisateur: "Crée un nouvel utilisateur nommé Marie Dubois avec l'email 
marie.dubois@company.com dans le département IT avec le niveau employee"

Chatbot: ✅ Utilisateur créé avec succès ! ID: emp_abc123, Nom: Marie Dubois, 
Email: marie.dubois@company.com, Département: IT
```

### Création de documents

**Permission requise** : Tous les employés

**Exemple d'utilisation** :
```
Utilisateur: "Crée un nouveau document avec le titre 'Guide de sécurité' et 
le contenu 'Ce guide décrit les procédures de sécurité...' 
Le document doit être accessible à tous les employés."

Chatbot: ✅ Document créé avec succès ! ID: doc_xyz789, Titre: Guide de sécurité
```

## Flux de traitement

```
1. Utilisateur pose une question ou demande une action
   ↓
2. Chatbot analyse l'intention (question ou action)
   ↓
3. Si action détectée:
   - Charge les outils MCP disponibles selon les permissions
   - Appelle le LLM avec les outils bindés
   - LLM décide d'appeler l'outil approprié
   ↓
4. Exécution de l'outil:
   - Appel HTTP au serveur MCP
   - Vérification des permissions côté serveur
   - Exécution de l'action
   ↓
5. Retour du résultat au LLM
   ↓
6. Génération de la réponse finale avec le résultat
```

## Configuration

### Variables d'environnement

- `MCP_SERVER_URL` : URL du serveur MCP (défaut: `http://localhost:8080`)

### Activation des outils MCP

Par défaut, les outils MCP sont activés. Pour les désactiver :

```python
chatbot = LangGraphChatbot(
    es_client=es_client,
    enable_mcp_tools=False  # Désactiver les outils MCP
)
```

## Gestion des permissions

Les outils sont automatiquement filtrés selon le niveau de permission de l'employé :

- **create_user** : Disponible uniquement pour Manager, Director, Executive
- **create_document** : Disponible pour tous les employés

Si un employé sans permission essaie d'utiliser un outil, le serveur MCP retourne une erreur 403 qui est convertie en message d'erreur compréhensible par le chatbot.

## Exemples

Voir `examples/mcp_chatbot_example.py` pour des exemples complets d'utilisation.

## Dépannage

### Le chatbot ne détecte pas les actions

- Vérifier que `enable_mcp_tools=True` est défini
- Vérifier que le serveur MCP est démarré (`python run_mcp_server.py`)
- Vérifier la variable `MCP_SERVER_URL`

### Erreur de permission

- Vérifier le niveau de permission de l'employé
- Pour créer des utilisateurs, le niveau Manager ou supérieur est requis

### Erreur de connexion au serveur MCP

- Vérifier que le serveur MCP est démarré sur le port 8080
- Vérifier la variable `MCP_SERVER_URL` dans `.env`

## Extension

Pour ajouter de nouvelles actions MCP :

1. Ajouter l'endpoint dans `mcp_server/server.py`
2. Créer l'outil LangChain dans `src/tools/mcp_tools.py`
3. Ajouter l'outil dans `get_mcp_tools()` avec les permissions appropriées
4. Mettre à jour `mcp_server/mcp.yaml` avec la nouvelle action

