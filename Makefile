# Makefile pour le projet ML API
# Commandes pour faciliter le développement, les tests et le déploiement

.PHONY: help install install-dev clean lint format test test-coverage run-api run-redis docker-build docker-up docker-down logs

# Variables
PYTHON := python
VENV := .venv
VENV_BIN := $(VENV)/bin
UV := uv
API_HOST := 0.0.0.0
API_PORT := 8000
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
	@echo "  make test             - Lance les tests"
	@echo "  make test-coverage    - Lance les tests avec couverture"
	@echo ""
	@echo "$(GREEN)Développement:$(NC)"
	@echo "  make run-api          - Lance l'API FastAPI"
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
	@$(VENV_BIN)/pytest tests/ -v || \
		(echo "$(RED)✗ Tests échoués$(NC)" && exit 1)
	@echo "$(GREEN)✓ Tous les tests passent$(NC)"

## test-coverage: Lance les tests avec couverture
test-coverage:
	@echo "$(BLUE)Lancement des tests avec couverture...$(NC)"
	@$(VENV_BIN)/pytest tests/ --cov=src --cov-report=html \
		--cov-report=term || \
		(echo "$(RED)✗ Tests échoués$(NC)" && exit 1)
	@echo "$(GREEN)✓ Rapport de couverture généré dans htmlcov/$(NC)"

## run-api: Lance l'API FastAPI
run-api:
	@echo "$(BLUE)Démarrage de l'API FastAPI...$(NC)"
	@echo "$(YELLOW)API disponible sur http://$(API_HOST):$(API_PORT)$(NC)"
	@echo "$(YELLOW)Documentation sur http://$(API_HOST):$(API_PORT)/docs$(NC)"
	@$(VENV_BIN)/uvicorn src.api.main:app \
		--host $(API_HOST) \
		--port $(API_PORT) \
		--reload

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
			"CHEST PAIN": 1 \
		}' | $(PYTHON) -m json.tool

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

## ci: Commandes pour CI/CD
ci: lint test
	@echo "$(GREEN)✓ CI/CD checks passed$(NC)"

# Cibles par défaut
.DEFAULT_GOAL := help
