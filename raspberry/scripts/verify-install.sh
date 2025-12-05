#!/bin/bash
# Script de vérification de l'installation Digital Signage

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Vérification de l'installation Digital Signage           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Fonction de vérification
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅${NC} Fichier présent : $1"
        return 0
    else
        echo -e "${RED}❌${NC} Fichier manquant : $1"
        ((ERRORS++))
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✅${NC} Dossier présent : $1"
        return 0
    else
        echo -e "${RED}❌${NC} Dossier manquant : $1"
        ((ERRORS++))
        return 1
    fi
}

check_executable() {
    if [ -x "$1" ]; then
        echo -e "${GREEN}✅${NC} Exécutable : $1"
        return 0
    else
        echo -e "${YELLOW}⚠️${NC}  Non exécutable : $1"
        ((WARNINGS++))
        return 1
    fi
}

check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✅${NC} Commande disponible : $1"
        return 0
    else
        echo -e "${RED}❌${NC} Commande manquante : $1"
        ((ERRORS++))
        return 1
    fi
}

check_service() {
    if systemctl list-unit-files | grep -q "$1"; then
        echo -e "${GREEN}✅${NC} Service configuré : $1"
        return 0
    else
        echo -e "${RED}❌${NC} Service non configuré : $1"
        ((ERRORS++))
        return 1
    fi
}

# Vérification de la structure
echo -e "${YELLOW}📂 Vérification de la structure des dossiers...${NC}"
check_dir "$(dirname "$0")/.."
check_dir "$(dirname "$0")/../config"
check_dir "$(dirname "$0")/../scripts"
check_dir "$(dirname "$0")/../wizard"
check_dir "$(dirname "$0")/../wizard/templates"
echo ""

# Vérification des fichiers de documentation
echo -e "${YELLOW}📚 Vérification de la documentation...${NC}"
check_file "$(dirname "$0")/../README.md"
check_file "$(dirname "$0")/../QUICKSTART.md"
check_file "$(dirname "$0")/../INSTALLATION.md"
check_file "$(dirname "$0")/../FICHIERS_CREES.md"
echo ""

# Vérification des scripts
echo -e "${YELLOW}🔧 Vérification des scripts...${NC}"
check_file "$(dirname "$0")/../install.sh"
check_executable "$(dirname "$0")/../install.sh"
check_file "$(dirname "$0")/startup.sh"
check_executable "$(dirname "$0")/startup.sh"
check_file "$(dirname "$0")/setup-ap.sh"
check_executable "$(dirname "$0")/setup-ap.sh"
check_file "$(dirname "$0")/maintenance.sh"
check_executable "$(dirname "$0")/maintenance.sh"
echo ""

# Vérification du wizard
echo -e "${YELLOW}🧙 Vérification du wizard...${NC}"
check_file "$(dirname "$0")/../wizard/wizard_server.py"
check_executable "$(dirname "$0")/../wizard/wizard_server.py"
check_file "$(dirname "$0")/../wizard/templates/wizard.html"
check_file "$(dirname "$0")/../wizard/screen_info.html"
echo ""

# Vérification des dépendances système
echo -e "${YELLOW}📦 Vérification des dépendances système...${NC}"
check_command python3
check_command pip3
check_command chromium-browser
check_command hostapd
check_command dnsmasq
echo ""

# Vérification des dépendances Python
echo -e "${YELLOW}🐍 Vérification des dépendances Python...${NC}"
if python3 -c "import flask" 2>/dev/null; then
    echo -e "${GREEN}✅${NC} Module Python : flask"
else
    echo -e "${RED}❌${NC} Module Python manquant : flask"
    ((ERRORS++))
fi

if python3 -c "import flask_socketio" 2>/dev/null; then
    echo -e "${GREEN}✅${NC} Module Python : flask-socketio"
else
    echo -e "${RED}❌${NC} Module Python manquant : flask-socketio"
    ((ERRORS++))
fi
echo ""

# Vérification du service systemd (si installé)
if [ -f "/etc/systemd/system/digital-signage.service" ]; then
    echo -e "${YELLOW}⚙️  Vérification du service systemd...${NC}"
    check_service "digital-signage.service"

    if systemctl is-enabled digital-signage.service &> /dev/null; then
        echo -e "${GREEN}✅${NC} Service activé au démarrage"
    else
        echo -e "${YELLOW}⚠️${NC}  Service non activé au démarrage"
        ((WARNINGS++))
    fi

    if systemctl is-active digital-signage.service &> /dev/null; then
        echo -e "${GREEN}✅${NC} Service en cours d'exécution"
    else
        echo -e "${YELLOW}⚠️${NC}  Service non démarré"
        ((WARNINGS++))
    fi
    echo ""
fi

# Vérification de la configuration (si installé)
if [ -f "/opt/digital-signage/raspberry/config/device.conf" ]; then
    echo -e "${YELLOW}⚙️  Vérification de la configuration...${NC}"
    check_file "/opt/digital-signage/raspberry/config/device.conf"

    source /opt/digital-signage/raspberry/config/device.conf
    if [ "$CONFIGURED" = "true" ]; then
        echo -e "${GREEN}✅${NC} Système configuré"
        echo -e "   Rôle Contrôleur: $ROLE_CONTROLLER"
        echo -e "   Rôle Player: $ROLE_PLAYER"
        if [ "$ROLE_PLAYER" = "true" ]; then
            echo -e "   ID Écran: $SCREEN_ID"
            echo -e "   Nom: $SCREEN_NAME"
        fi
    else
        echo -e "${YELLOW}⚠️${NC}  Système non encore configuré"
        ((WARNINGS++))
    fi
    echo ""
fi

# Résumé
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ Installation complète et correcte !${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Installation complète avec $WARNINGS avertissement(s)${NC}"
    exit 0
else
    echo -e "${RED}❌ Installation incomplète : $ERRORS erreur(s), $WARNINGS avertissement(s)${NC}"
    exit 1
fi
