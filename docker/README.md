# Docker - Configuration et Déploiement

Ce répertoire contient les fichiers de configuration Docker pour déployer l'API ML avec Redis.

## 📦 Architecture

L'application est déployée avec Docker Compose et comprend deux services :

### 1. Service API (`api`)
- **Image** : Construite depuis `Dockerfile`
- **Port** : 8000
- **Fonction** : API FastAPI + Modèle ML
- **Caractéristiques** :
  - Chargement du modèle au démarrage (Singleton)
  - Logging configuré vers Redis
  - Health check intégré
  - Utilisateur non-root pour la sécurité

### 2. Service Redis (`redis`)
- **Image** : `redis:7-alpine`
- **Port** : 6379
- **Fonction** : Stockage des logs en mémoire
- **Configuration** :
  - Mémoire max : 256 MB
  - Politique d'éviction : allkeys-lru
  - Données persistées dans un volume Docker

## 🚀 Utilisation

### Commandes Make (recommandé)

```bash
# Construire les images
make docker-build

# Lancer les services
make docker-up

# Voir les logs
make docker-logs

# Arrêter les services
make docker-down
```

### Commandes Docker Compose directes

```bash
# Depuis le répertoire docker/
cd docker

# Construire les images
docker-compose build

# Lancer les services en arrière-plan
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Arrêter les services
docker-compose down

# Arrêter et supprimer les volumes
docker-compose down -v
```

## 🔧 Configuration

### Variables d'environnement

Les variables d'environnement sont définies dans `docker-compose.yml` :

```yaml
environment:
  # API
  - API_HOST=0.0.0.0
  - API_PORT=8000

  # Modèle
  - MODEL_PATH=/app/model/model.pkl

  # Redis
  - REDIS_HOST=redis
  - REDIS_PORT=6379
  - REDIS_DB=0

  # Logging
  - LOG_LEVEL=INFO
  - LOGGING_HANDLER=redis

  # Environnement
  - ENV=production
```

### Personnalisation

Pour personnaliser la configuration, modifiez `docker-compose.yml` ou créez un fichier `.env` :

```bash
# .env
API_PORT=8080
LOG_LEVEL=DEBUG
REDIS_LOGS_MAX_SIZE=5000
```

## 📊 Monitoring et Health Checks

### Health Check API

L'API expose un endpoint de health check :

```bash
curl http://localhost:8000/health
```

**Réponse** :
```json
{
  "status": "healthy",
  "model_loaded": true,
  "redis_connected": true,
  "version": "1.0.0"
}
```

### Health Check Docker

Les deux services ont des health checks configurés :

```bash
# Vérifier le statut des services
docker-compose ps

# Exemple de sortie
NAME            STATUS                     PORTS
ml-api          Up (healthy)              0.0.0.0:8000->8000/tcp
ml-api-redis    Up (healthy)              0.0.0.0:6379->6379/tcp
```

## 📝 Logs

### Consulter les logs

```bash
# Tous les services
make docker-logs

# API uniquement
make docker-logs-api

# Redis uniquement
make docker-logs-redis

# Via l'API
curl http://localhost:8000/logs?limit=50
```

### Format des logs

Les logs sont formatés de manière standard :

```
2024-11-10 16:00:00 - api - INFO - Démarrage de l'API...
2024-11-10 16:00:01 - api - INFO - Modèle chargé avec succès
2024-11-10 16:00:15 - api - INFO - Prédiction effectuée: 1 (prob=0.85)
```

## 🔐 Sécurité

### Bonnes pratiques implémentées

1. **Utilisateur non-root** : L'application s'exécute avec l'utilisateur `appuser` (UID 1000)
2. **Volumes limités** : Seules les données nécessaires sont montées
3. **Réseau isolé** : Les services communiquent via un réseau Docker dédié
4. **Limites de ressources** : Redis est limité à 256 MB de mémoire
5. **Health checks** : Surveillance automatique de l'état des services

### Recommandations pour la production

1. **Secrets** : Utiliser Docker secrets ou un gestionnaire de secrets
2. **TLS/SSL** : Configurer HTTPS avec un reverse proxy (nginx, traefik)
3. **Limites CPU/RAM** : Ajouter des limites de ressources dans docker-compose.yml
4. **Backup Redis** : Configurer une persistence si nécessaire
5. **Logging centralisé** : Utiliser un système comme ELK ou Loki

## 🛠️ Dépannage

### Problème : L'API ne démarre pas

```bash
# Voir les logs de l'API
docker-compose logs api

# Vérifier si le modèle existe
docker-compose exec api ls -la /app/model/

# Redémarrer l'API
docker-compose restart api
```

### Problème : Redis non accessible

```bash
# Vérifier que Redis est en cours d'exécution
docker-compose ps redis

# Tester la connexion Redis
docker-compose exec redis redis-cli ping

# Redémarrer Redis
docker-compose restart redis
```

### Problème : Port déjà utilisé

```bash
# Vérifier les ports utilisés
lsof -i :8000
lsof -i :6379

# Modifier le port dans docker-compose.yml
ports:
  - "8080:8000"  # API sur le port 8080
```

### Problème : Erreur de build

```bash
# Nettoyer les images et rebuild
docker-compose down
docker system prune -a
make docker-build
```

## 📈 Performance

### Configuration Redis

Redis est configuré avec :
- **maxmemory** : 256 MB (ajustable selon les besoins)
- **maxmemory-policy** : allkeys-lru (éviction automatique des anciennes entrées)

Pour augmenter la mémoire :

```yaml
command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### Scalabilité

Pour scaler l'API horizontalement :

```bash
# Lancer plusieurs instances de l'API
docker-compose up -d --scale api=3
```

**Note** : Nécessite un load balancer (nginx, traefik) pour distribuer les requêtes.

## 🔄 Mise à jour

### Mettre à jour l'image

```bash
# 1. Arrêter les services
make docker-down

# 2. Mettre à jour le code
git pull

# 3. Rebuilder les images
make docker-build

# 4. Relancer les services
make docker-up
```

### Rolling update (sans downtime)

```bash
# Avec Docker Swarm ou Kubernetes
docker stack deploy -c docker-compose.yml ml-api
```

## 📚 Ressources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Redis Configuration](https://redis.io/docs/manual/config/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

## 🆘 Support

Pour toute question ou problème :

1. Vérifier les logs : `make docker-logs`
2. Consulter la documentation : [../README.md](../README.md)
3. Vérifier les issues GitHub
