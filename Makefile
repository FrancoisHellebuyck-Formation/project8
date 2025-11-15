# Makefile pour le projet ML API
# Commandes pour faciliter le développement, les tests et le déploiement

.PHONY: help install install-dev clean lint format test test-coverage test-api test-model test-gradio-api test-gradio-api-local test-gradio-api-hf run-api run-ui run-redis stop-redis docker-build docker-up docker-down docker-logs logs health predict-test simulate simulate-quick simulate-load simulate-drift simulate-drift-progressive drift-analyze

# Variables
PYTHON := python
VENV := .venv
VENV_BIN := $(VENV)/bin
UV := uv
API_HOST := 0.0.0.0
API_PORT := 8000
GRADIO_HOST := 0.0.0.0
GRADIO_PORT := 7860
GRADIO_LOCAL_URL := http://localhost:7860
GRADIO_HF_URL := https://francoisformation-oc-project8.hf.space
REDIS_PORT := 6379

# Couleurs pour l'affichage
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

## help: Affiche ce message d'aide
help:
	@echo "$(BLUE)Commandes disponibles:$(NC)"
	@echo ""
	@echo "$(GREEN)Installation et configuration:$(NC)"
	@echo "  make install          - Installe les dépendances de production"
	@echo "  make install-dev      - Installe toutes les dépendances (dev inclus)"
	@echo "  make clean            - Nettoie les fichiers temporaires"
	@echo ""
	@echo "$(GREEN)Qualité du code:$(NC)"
	@echo "  make lint             - Vérifie le code avec flake8"
	@echo "  make format           - Formate le code (placeholder)"
	@echo "  make test             - Lance tous les tests"
	@echo "  make test-coverage    - Lance les tests avec couverture"
	@echo "  make test-api         - Lance les tests de l'API uniquement"
	@echo "  make test-model       - Lance les tests du modèle uniquement"
	@echo "  make test-gradio-api-local  - Test l'API Gradio (local)"
	@echo "  make test-gradio-api-hf     - Test l'API Gradio (HuggingFace)"
	@echo ""
	@echo "$(GREEN)Développement:$(NC)"
	@echo "  make run-api          - Lance l'API FastAPI"
	@echo "  make run-ui           - Lance l'interface Gradio"
	@echo "  make run-redis        - Lance Redis avec Docker"
	@echo "  make stop-redis       - Arrête le conteneur Redis"
	@echo ""
	@echo "$(GREEN)Docker:$(NC)"
	@echo "  make docker-build     - Construit les images Docker"
	@echo "  make docker-up        - Lance tous les conteneurs"
	@echo "  make docker-down      - Arrête tous les conteneurs"
	@echo "  make docker-logs      - Affiche les logs des conteneurs"
	@echo ""
	@echo "$(GREEN)Utilitaires:$(NC)"
	@echo "  make logs             - Affiche les logs de l'API via endpoint"
	@echo "  make health           - Vérifie la santé de l'API"
	@echo "  make predict-test     - Test une prédiction"
	@echo ""
	@echo "$(GREEN)Simulation:$(NC)"
	@echo "  make simulate         - Simule des requêtes (config depuis .env)"
	@echo "  make simulate-quick   - Simule 20 requêtes avec 5 utilisateurs"
	@echo "  make simulate-load    - Test de charge (500 requêtes, 50 users)"
	@echo "  make simulate-drift   - Simule avec data drift immédiat (75 ans)"
	@echo "  make simulate-drift-progressive - Drift progressif (50%-100%)"
	@echo "  make drift-analyze    - Analyse le data drift"
	@echo ""

## install: Installe les dépendances de production
install:
	@echo "$(BLUE)Installation des dépendances...$(NC)"
	@test -d $(VENV) || python -m venv $(VENV)
	@$(VENV_BIN)/pip install --upgrade pip
	@$(VENV_BIN)/pip install uv
	@$(VENV_BIN)/uv pip install -e .
	@echo "$(GREEN)✓ Dépendances installées$(NC)"

## install-dev: Installe toutes les dépendances (dev inclus)
install-dev:
	@echo "$(BLUE)Installation des dépendances de développement...$(NC)"
	@test -d $(VENV) || python -m venv $(VENV)
	@$(VENV_BIN)/pip install --upgrade pip
	@$(VENV_BIN)/pip install uv
	@$(VENV_BIN)/uv pip install -e ".[dev]"
	@echo "$(GREEN)✓ Dépendances de développement installées$(NC)"

## clean: Nettoie les fichiers temporaires
clean:
	@echo "$(BLUE)Nettoyage des fichiers temporaires...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Nettoyage terminé$(NC)"

## lint: Vérifie le code avec flake8
lint:
	@echo "$(BLUE)Vérification du code avec flake8...$(NC)"
	@$(VENV_BIN)/flake8 src/ tests/ || \
		(echo "$(RED)✗ Erreurs de linting détectées$(NC)" && exit 1)
	@echo "$(GREEN)✓ Code conforme aux standards$(NC)"

## format: Formate le code
format:
	@echo "$(YELLOW)⚠ Formatage non implémenté (TODO: black/ruff)$(NC)"

## test: Lance les tests
test:
	@echo "$(BLUE)Lancement des tests...$(NC)"
	@$(UV) run pytest tests/ -v || \
		(echo "$(RED)✗ Tests échoués$(NC)" && exit 1)
	@echo "$(GREEN)✓ Tous les tests passent$(NC)"

## test-coverage: Lance les tests avec couverture
test-coverage:
	@echo "$(BLUE)Lancement des tests avec couverture...$(NC)"
	@$(UV) run pytest tests/ --cov=src --cov-report=html \
		--cov-report=term-missing --cov-report=xml || \
		(echo "$(RED)✗ Tests échoués$(NC)" && exit 1)
	@echo "$(GREEN)✓ Rapport de couverture généré dans htmlcov/ et coverage.xml$(NC)"

## test-api: Lance les tests de l'API uniquement
test-api:
	@echo "$(BLUE)Lancement des tests API...$(NC)"
	@$(UV) run pytest tests/api/ -v || \
		(echo "$(RED)✗ Tests API échoués$(NC)" && exit 1)
	@echo "$(GREEN)✓ Tests API passent$(NC)"

## test-model: Lance les tests du modèle uniquement
test-model:
	@echo "$(BLUE)Lancement des tests du modèle...$(NC)"
	@$(UV) run pytest tests/model/ -v || \
		(echo "$(RED)✗ Tests modèle échoués$(NC)" && exit 1)
	@echo "$(GREEN)✓ Tests modèle passent$(NC)"

## test-gradio-api-local: Test l'API Gradio en local
test-gradio-api-local:
	@echo "$(BLUE)Test de l'API Gradio (local)...$(NC)"
	@echo "$(YELLOW)URL: $(GRADIO_LOCAL_URL)$(NC)"
	@echo "$(YELLOW)Assurez-vous que l'API et Gradio tournent localement$(NC)"
	@GRADIO_URL=$(GRADIO_LOCAL_URL) $(PYTHON) test_gradio_api.py || \
		(echo "$(RED)✗ Tests Gradio API échoués$(NC)" && exit 1)
	@echo "$(GREEN)✓ Tests Gradio API passent$(NC)"

## test-gradio-api-hf: Test l'API Gradio sur HuggingFace Spaces
test-gradio-api-hf:
	@echo "$(BLUE)Test de l'API Gradio (HuggingFace Spaces)...$(NC)"
	@echo "$(YELLOW)URL: $(GRADIO_HF_URL)$(NC)"
	@if [ -f .env ]; then \
		echo "$(YELLOW)Chargement de HF_TOKEN depuis .env...$(NC)"; \
		export $$(cat .env | grep -v '^#' | grep HF_TOKEN | xargs) && \
		GRADIO_URL=$(GRADIO_HF_URL) $(PYTHON) test_gradio_api.py || \
		(echo "$(RED)✗ Tests Gradio API échoués$(NC)" && exit 1); \
	else \
		echo "$(YELLOW)⚠️  Fichier .env non trouvé, test sans token$(NC)"; \
		GRADIO_URL=$(GRADIO_HF_URL) $(PYTHON) test_gradio_api.py || \
		(echo "$(RED)✗ Tests Gradio API échoués$(NC)" && exit 1); \
	fi
	@echo "$(GREEN)✓ Tests Gradio API passent$(NC)"

## run-api: Lance l'API FastAPI
run-api:
	@echo "$(BLUE)Démarrage de l'API FastAPI...$(NC)"
	@echo "$(YELLOW)API disponible sur http://$(API_HOST):$(API_PORT)$(NC)"
	@echo "$(YELLOW)Documentation sur http://$(API_HOST):$(API_PORT)/docs$(NC)"
	@$(VENV_BIN)/uvicorn src.api.main:app \
		--host $(API_HOST) \
		--port $(API_PORT) \
		--reload

## run-ui: Lance l'interface Gradio
run-ui:
	@echo "$(BLUE)Démarrage de l'interface Gradio...$(NC)"
	@echo "$(YELLOW)Interface disponible sur http://$(GRADIO_HOST):$(GRADIO_PORT)$(NC)"
	@$(VENV_BIN)/python -m src.ui.app

## run-redis: Lance Redis avec Docker
run-redis:
	@echo "$(BLUE)Démarrage de Redis...$(NC)"
	@docker run -d \
		--name redis-ml-api \
		-p $(REDIS_PORT):6379 \
		redis:latest \
		2>/dev/null || \
		(docker start redis-ml-api 2>/dev/null || true)
	@sleep 2
	@echo "$(GREEN)✓ Redis en cours d'exécution sur le port $(REDIS_PORT)$(NC)"

## stop-redis: Arrête le conteneur Redis
stop-redis:
	@echo "$(BLUE)Arrêt de Redis...$(NC)"
	@docker stop redis-ml-api 2>/dev/null || true
	@echo "$(GREEN)✓ Redis arrêté$(NC)"

## docker-build: Construit les images Docker
docker-build:
	@echo "$(BLUE)Construction des images Docker...$(NC)"
	@cd docker && docker-compose build
	@echo "$(GREEN)✓ Images construites$(NC)"

## docker-up: Lance tous les conteneurs
docker-up:
	@echo "$(BLUE)Démarrage des conteneurs Docker...$(NC)"
	@cd docker && docker-compose up -d
	@echo "$(GREEN)✓ Conteneurs démarrés$(NC)"
	@echo "$(YELLOW)API: http://localhost:$(API_PORT)$(NC)"
	@echo "$(YELLOW)Redis: localhost:6379$(NC)"
	@echo "$(YELLOW)Logs: http://localhost:$(API_PORT)/logs$(NC)"

## docker-down: Arrête tous les conteneurs
docker-down:
	@echo "$(BLUE)Arrêt des conteneurs Docker...$(NC)"
	@cd docker && docker-compose down
	@echo "$(GREEN)✓ Conteneurs arrêtés$(NC)"

## docker-down-volumes: Arrête les conteneurs et supprime les volumes
docker-down-volumes:
	@echo "$(BLUE)Arrêt des conteneurs et suppression des volumes...$(NC)"
	@cd docker && docker-compose down -v
	@echo "$(GREEN)✓ Conteneurs et volumes supprimés$(NC)"

## docker-logs: Affiche les logs des conteneurs
docker-logs:
	@cd docker && docker-compose logs -f

## docker-logs-api: Affiche les logs de l'API uniquement
docker-logs-api:
	@cd docker && docker-compose logs -f api

## docker-logs-redis: Affiche les logs de Redis uniquement
docker-logs-redis:
	@cd docker && docker-compose logs -f redis

## docker-restart: Redémarre tous les conteneurs
docker-restart: docker-down docker-up

## logs: Affiche les logs de l'API via endpoint
logs:
	@echo "$(BLUE)Récupération des logs de l'API...$(NC)"
	@curl -s http://localhost:$(API_PORT)/logs?limit=50 | \
		$(PYTHON) -m json.tool || \
		echo "$(RED)✗ Impossible de récupérer les logs$(NC)"

## health: Vérifie la santé de l'API
health:
	@echo "$(BLUE)Vérification de la santé de l'API...$(NC)"
	@curl -s http://localhost:$(API_PORT)/health | \
		$(PYTHON) -m json.tool || \
		echo "$(RED)✗ API non disponible$(NC)"

## predict-test: Test une prédiction
predict-test:
	@echo "$(BLUE)Test d'une prédiction...$(NC)"
	@curl -X POST http://localhost:$(API_PORT)/predict \
		-H "Content-Type: application/json" \
		-d '{ \
			"AGE": 65, \
			"GENDER": 1, \
			"SMOKING": 1, \
			"ALCOHOL CONSUMING": 1, \
			"PEER_PRESSURE": 0, \
			"YELLOW_FINGERS": 1, \
			"ANXIETY": 0, \
			"FATIGUE": 1, \
			"ALLERGY": 0, \
			"WHEEZING": 1, \
			"COUGHING": 1, \
			"SHORTNESS OF BREATH": 1, \
			"SWALLOWING DIFFICULTY": 0, \
			"CHEST PAIN": 1, \
			"CHRONIC DISEASE": 0 \
		}' | python3 -m json.tool

## simulate: Simule des requêtes (utilise la config du .env)
simulate:
	@echo "$(BLUE)Simulation d'utilisateurs...$(NC)"
	@$(UV) run python -m src.simulator

## simulate-quick: Simule 20 requêtes avec 5 utilisateurs (override .env)
simulate-quick:
	@echo "$(BLUE)Simulation rapide...$(NC)"
	@$(UV) run python -m src.simulator -r 20 -u 5 -v

## simulate-load: Test de charge avec 500 requêtes et 50 utilisateurs (override .env)
simulate-load:
	@echo "$(BLUE)Test de charge...$(NC)"
	@$(UV) run python -m src.simulator -r 500 -u 50

## simulate-drift: Simule avec data drift immédiat sur l'âge (vers 75 ans)
simulate-drift:
	@echo "$(BLUE)Simulation avec data drift immédiat...$(NC)"
	@echo "$(YELLOW)⚠️  Drift vers 75 ans sur toute la simulation$(NC)"
	@$(UV) run python -m src.simulator -r 200 -u 10 --enable-age-drift \
		--age-drift-target 75

## simulate-drift-progressive: Drift progressif (50% à 100% de la simulation)
simulate-drift-progressive:
	@echo "$(BLUE)Simulation avec data drift progressif...$(NC)"
	@echo "$(YELLOW)⚠️  Drift vers 80 ans entre 50% et 100%$(NC)"
	@$(UV) run python -m src.simulator -r 300 -u 15 --enable-age-drift \
		--age-drift-target 80 --age-drift-start 50 --age-drift-end 100

## drift-analyze: Analyse le comportement du data drift
drift-analyze:
	@echo "$(BLUE)Analyse du data drift...$(NC)"
	@$(UV) run python -m src.simulator.drift_analyzer

## setup: Configuration initiale du projet
setup: install-dev
	@echo "$(BLUE)Configuration initiale du projet...$(NC)"
	@test -f .env || cp .env.example .env
	@echo "$(GREEN)✓ Fichier .env créé$(NC)"
	@echo "$(YELLOW)⚠ Pensez à configurer vos variables d'environnement$(NC)"
	@echo "$(GREEN)✓ Configuration terminée$(NC)"

## dev: Environnement de développement complet
dev: setup run-redis
	@echo "$(GREEN)✓ Environnement de développement prêt$(NC)"
	@echo "$(YELLOW)Lancez 'make run-api' dans un autre terminal$(NC)"
	@echo "$(YELLOW)Lancez 'make run-ui' dans un troisième terminal$(NC)"

## ci: Commandes pour CI/CD
ci: lint test
	@echo "$(GREEN)✓ CI/CD checks passed$(NC)"

# Cibles par défaut
.DEFAULT_GOAL := help
