#!/bin/bash

# Script pour exécuter les tests de charge JMeter
# Usage: ./run_load_test.sh [scenario] [host] [port] [protocol]

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Vérifier que JMeter est installé
if ! command -v jmeter &> /dev/null; then
    echo -e "${RED}❌ JMeter n'est pas installé${NC}"
    echo "Installation:"
    echo "  macOS: brew install jmeter"
    echo "  Linux: wget https://dlcdn.apache.org//jmeter/binaries/apache-jmeter-5.6.3.tgz && tar -xzf apache-jmeter-5.6.3.tgz"
    exit 1
fi

# Paramètres
SCENARIO=${1:-basic}
HOST=${2:-localhost}
PORT=${3:-7860}
PROTOCOL=${4:-http}

# Configuration des scénarios
case $SCENARIO in
    basic)
        USERS=10
        RAMPUP=5
        DURATION=60
        DESC="Test de base (10 users, 1 min)"
        ;;
    load)
        USERS=50
        RAMPUP=30
        DURATION=300
        DESC="Test de charge (50 users, 5 min)"
        ;;
    stress)
        USERS=100
        RAMPUP=60
        DURATION=600
        DESC="Test de stress (100 users, 10 min)"
        ;;
    endurance)
        USERS=20
        RAMPUP=60
        DURATION=3600
        DESC="Test d'endurance (20 users, 1h)"
        ;;
    quick)
        USERS=5
        RAMPUP=2
        DURATION=30
        DESC="Test rapide (5 users, 30s)"
        ;;
    hf)
        USERS=20
        RAMPUP=10
        DURATION=120
        HOST="francoisformation-oc-project8.hf.space"
        PORT=443
        PROTOCOL="https"
        DESC="Test HuggingFace Spaces (20 users, 2 min)"
        ;;
    *)
        echo -e "${RED}❌ Scénario inconnu: $SCENARIO${NC}"
        echo "Scénarios disponibles:"
        echo "  basic     - Test de base (10 users, 1 min)"
        echo "  load      - Test de charge (50 users, 5 min)"
        echo "  stress    - Test de stress (100 users, 10 min)"
        echo "  endurance - Test d'endurance (20 users, 1h)"
        echo "  quick     - Test rapide (5 users, 30s)"
        echo "  hf        - Test HuggingFace Spaces (20 users, 2 min)"
        exit 1
        ;;
esac

# Créer le dossier de résultats
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="jmeter/results_${SCENARIO}_${TIMESTAMP}"
mkdir -p "$RESULTS_DIR"

# Afficher la configuration
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          Tests de charge JMeter - ML API                 ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}📊 Scénario:${NC} $DESC"
echo -e "${YELLOW}🌐 Hôte:${NC} $PROTOCOL://$HOST:$PORT"
echo -e "${YELLOW}👥 Utilisateurs:${NC} $USERS"
echo -e "${YELLOW}⏱️  Ramp-up:${NC} ${RAMPUP}s"
echo -e "${YELLOW}⏰ Durée:${NC} ${DURATION}s"
echo -e "${YELLOW}📁 Résultats:${NC} $RESULTS_DIR"
echo ""

# Vérifier que l'API est accessible
echo -e "${BLUE}🔍 Vérification de la connexion à l'API...${NC}"
if curl -s -f -o /dev/null "$PROTOCOL://$HOST:$PORT/api/health"; then
    echo -e "${GREEN}✅ API accessible${NC}"
else
    echo -e "${RED}❌ API inaccessible${NC}"
    echo "Veuillez démarrer l'API avant de lancer le test:"
    echo "  make run-api"
    echo "  make run-ui-fastapi"
    exit 1
fi

echo ""
echo -e "${BLUE}🚀 Lancement du test de charge...${NC}"
echo ""

# Lancer le test JMeter
jmeter -n -t jmeter/API_Load_Test.jmx \
    -Jhost="$HOST" \
    -Jport="$PORT" \
    -Jprotocol="$PROTOCOL" \
    -Jusers="$USERS" \
    -Jrampup="$RAMPUP" \
    -Jduration="$DURATION" \
    -l "$RESULTS_DIR/results.jtl" \
    -e -o "$RESULTS_DIR/report"

# Vérifier le résultat
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║               ✅ Test terminé avec succès                ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Analyser les résultats
    echo -e "${BLUE}📊 Analyse des résultats...${NC}"
    echo ""

    # Extraire les statistiques du fichier JTL
    TOTAL_REQUESTS=$(grep -c "^[0-9]" "$RESULTS_DIR/results.jtl")
    ERROR_REQUESTS=$(grep -c ",false," "$RESULTS_DIR/results.jtl" || echo "0")
    ERROR_RATE=$(awk "BEGIN {printf \"%.2f\", ($ERROR_REQUESTS / $TOTAL_REQUESTS) * 100}")

    # Calculer le temps de réponse moyen (colonne 2 du CSV)
    AVG_RESPONSE=$(awk -F',' 'NR>1 {sum+=$2; count++} END {if(count>0) print int(sum/count); else print 0}' "$RESULTS_DIR/results.jtl")

    echo -e "${YELLOW}📈 Statistiques globales:${NC}"
    echo -e "  - Requêtes totales: ${GREEN}$TOTAL_REQUESTS${NC}"
    echo -e "  - Requêtes en erreur: ${RED}$ERROR_REQUESTS${NC}"
    echo -e "  - Taux d'erreur: ${RED}${ERROR_RATE}%${NC}"
    echo -e "  - Temps de réponse moyen: ${GREEN}${AVG_RESPONSE}ms${NC}"
    echo ""

    # Vérifier les seuils
    if (( $(echo "$ERROR_RATE > 1" | bc -l) )); then
        echo -e "${RED}⚠️  AVERTISSEMENT: Taux d'erreur élevé (> 1%)${NC}"
    fi

    if [ "$AVG_RESPONSE" -gt 1000 ]; then
        echo -e "${RED}⚠️  AVERTISSEMENT: Temps de réponse élevé (> 1000ms)${NC}"
    fi

    echo ""
    echo -e "${BLUE}📁 Résultats disponibles:${NC}"
    echo -e "  - Fichier JTL: ${YELLOW}$RESULTS_DIR/results.jtl${NC}"
    echo -e "  - Rapport HTML: ${YELLOW}$RESULTS_DIR/report/index.html${NC}"
    echo ""
    echo -e "${GREEN}💡 Ouvrir le rapport:${NC}"
    echo -e "  open $RESULTS_DIR/report/index.html"
    echo ""

else
    echo ""
    echo -e "${RED}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                  ❌ Test échoué                          ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Consultez les logs pour plus de détails."
    exit 1
fi
