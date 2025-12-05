#!/bin/bash
# Script de maintenance interactif pour Digital Signage

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Variables
BASE_DIR="/opt/digital-signage"
CONFIG_FILE="$BASE_DIR/raspberry/config/device.conf"
SERVICE_NAME="digital-signage"

# Vérifier si root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Ce script doit être exécuté avec sudo${NC}"
    exit 1
fi

show_menu() {
    clear
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║        Digital Signage - Menu de Maintenance              ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}1.${NC} Afficher la configuration actuelle"
    echo -e "${YELLOW}2.${NC} Redémarrer le service"
    echo -e "${YELLOW}3.${NC} Voir les logs"
    echo -e "${YELLOW}4.${NC} Relancer le wizard de configuration"
    echo -e "${YELLOW}5.${NC} Configuration manuelle"
    echo -e "${YELLOW}6.${NC} Factory Reset"
    echo -e "${YELLOW}7.${NC} Mode Debug"
    echo -e "${YELLOW}8.${NC} État du système"
    echo -e "${YELLOW}9.${NC} Quitter"
    echo ""
    echo -n "Votre choix: "
}

show_config() {
    echo -e "${BLUE}═══ Configuration actuelle ═══${NC}"
    echo ""
    if [ -f "$CONFIG_FILE" ]; then
        cat $CONFIG_FILE
    else
        echo -e "${RED}Fichier de configuration introuvable${NC}"
    fi
    echo ""
    read -p "Appuyez sur Entrée pour continuer..."
}

restart_service() {
    echo -e "${YELLOW}🔄 Redémarrage du service...${NC}"
    systemctl restart $SERVICE_NAME
    sleep 2
    systemctl status $SERVICE_NAME --no-pager
    echo ""
    read -p "Appuyez sur Entrée pour continuer..."
}

show_logs() {
    clear
    echo -e "${BLUE}═══ Logs du service (Ctrl+C pour quitter) ═══${NC}"
    echo ""
    echo -e "${YELLOW}1.${NC} Logs en direct"
    echo -e "${YELLOW}2.${NC} 50 dernières lignes"
    echo -e "${YELLOW}3.${NC} Logs d'erreur"
    echo -e "${YELLOW}4.${NC} Retour"
    echo ""
    read -p "Votre choix: " log_choice

    case $log_choice in
        1)
            journalctl -u $SERVICE_NAME -f
            ;;
        2)
            journalctl -u $SERVICE_NAME -n 50
            ;;
        3)
            tail -n 50 $BASE_DIR/logs/service-error.log
            ;;
        *)
            return
            ;;
    esac
    echo ""
    read -p "Appuyez sur Entrée pour continuer..."
}

relaunch_wizard() {
    echo -e "${YELLOW}⚠️  Relancer le wizard de configuration${NC}"
    echo ""
    echo "Cela va marquer le système comme non configuré et relancer le wizard au prochain démarrage."
    echo ""
    read -p "Êtes-vous sûr? (o/N): " confirm

    if [ "$confirm" = "o" ] || [ "$confirm" = "O" ]; then
        sed -i 's/CONFIGURED=.*/CONFIGURED="false"/' $CONFIG_FILE
        echo -e "${GREEN}✅ Configuration réinitialisée${NC}"
        echo ""
        read -p "Redémarrer maintenant? (o/N): " reboot_now
        if [ "$reboot_now" = "o" ] || [ "$reboot_now" = "O" ]; then
            reboot
        fi
    fi
    echo ""
    read -p "Appuyez sur Entrée pour continuer..."
}

manual_config() {
    echo -e "${BLUE}═══ Configuration manuelle ═══${NC}"
    echo ""

    # Charger la config actuelle
    source $CONFIG_FILE

    echo "Configuration actuelle du rôle:"
    echo "  Contrôleur: $ROLE_CONTROLLER"
    echo "  Player: $ROLE_PLAYER"
    echo ""

    read -p "Activer le rôle Contrôleur? (o/n): " ctrl
    read -p "Activer le rôle Player? (o/n): " play

    if [ "$play" = "o" ] || [ "$play" = "O" ]; then
        read -p "ID écran: " screen_id
        read -p "Nom écran: " screen_name
        read -p "Emplacement: " screen_location
        read -p "URL contrôleur: " controller_url
    fi

    # Sauvegarder (convertir o/n en true/false et ajouter guillemets)
    ctrl_value=$( [ "$ctrl" = "o" ] || [ "$ctrl" = "O" ] && echo "true" || echo "false" )
    play_value=$( [ "$play" = "o" ] || [ "$play" = "O" ] && echo "true" || echo "false" )
    sed -i "s/ROLE_CONTROLLER=.*/ROLE_CONTROLLER=\"${ctrl_value}\"/" $CONFIG_FILE
    sed -i "s/ROLE_PLAYER=.*/ROLE_PLAYER=\"${play_value}\"/" $CONFIG_FILE

    if [ "$play" = "o" ] || [ "$play" = "O" ]; then
        sed -i "s/SCREEN_ID=.*/SCREEN_ID=\"$screen_id\"/" $CONFIG_FILE
        sed -i "s/SCREEN_NAME=.*/SCREEN_NAME=\"$screen_name\"/" $CONFIG_FILE
        sed -i "s/SCREEN_LOCATION=.*/SCREEN_LOCATION=\"$screen_location\"/" $CONFIG_FILE
        sed -i "s|CONTROLLER_URL=.*|CONTROLLER_URL=\"$controller_url\"|" $CONFIG_FILE
    fi

    echo -e "${GREEN}✅ Configuration mise à jour${NC}"
    echo ""
    read -p "Redémarrer le service? (o/N): " restart
    if [ "$restart" = "o" ] || [ "$restart" = "O" ]; then
        restart_service
    fi
    echo ""
    read -p "Appuyez sur Entrée pour continuer..."
}

factory_reset() {
    echo -e "${RED}⚠️  FACTORY RESET ⚠️${NC}"
    echo ""
    echo "Cette action va:"
    echo "  - Supprimer toute la configuration"
    echo "  - Supprimer les données"
    echo "  - Réinitialiser aux paramètres d'usine"
    echo ""
    read -p "Êtes-vous VRAIMENT sûr? (tapez 'RESET' pour confirmer): " confirm

    if [ "$confirm" = "RESET" ]; then
        echo -e "${YELLOW}🔄 Reset en cours...${NC}"

        # Arrêter le service
        systemctl stop $SERVICE_NAME

        # Supprimer les données
        rm -rf $BASE_DIR/data/*
        rm -rf $BASE_DIR/logs/*

        # Réinitialiser la config
        cat > $CONFIG_FILE << 'EOF'
# Configuration du dispositif Digital Signage
CONFIGURED="false"
ROLE_CONTROLLER="false"
ROLE_PLAYER="false"
SCREEN_ID=""
SCREEN_NAME=""
SCREEN_LOCATION=""
CONTROLLER_URL="http://localhost:5000"
WIFI_SSID="DigitalSignage-Setup"
WIFI_PASSWORD="signage2024"
EOF

        echo -e "${GREEN}✅ Factory Reset terminé${NC}"
        echo ""
        read -p "Redémarrer maintenant? (o/N): " reboot_now
        if [ "$reboot_now" = "o" ] || [ "$reboot_now" = "O" ]; then
            reboot
        fi
    else
        echo -e "${YELLOW}❌ Reset annulé${NC}"
    fi
    echo ""
    read -p "Appuyez sur Entrée pour continuer..."
}

debug_mode() {
    clear
    echo -e "${BLUE}═══ Mode Debug ═══${NC}"
    echo ""

    echo -e "${YELLOW}📊 État du système:${NC}"
    echo "  Service: $(systemctl is-active $SERVICE_NAME)"
    echo "  Uptime: $(uptime -p)"
    echo ""

    echo -e "${YELLOW}🌐 Réseau:${NC}"
    ip addr show wlan0 | grep "inet " || echo "  Pas de connexion WiFi"
    echo ""

    echo -e "${YELLOW}💾 Espace disque:${NC}"
    df -h / | tail -1
    echo ""

    echo -e "${YELLOW}🔥 Température:${NC}"
    temp=$(vcgencmd measure_temp | cut -d= -f2)
    echo "  CPU: $temp"
    echo ""

    echo -e "${YELLOW}📁 Fichiers de configuration:${NC}"
    ls -lh $BASE_DIR/raspberry/config/
    echo ""

    echo -e "${YELLOW}📝 Dernières lignes des logs:${NC}"
    tail -n 10 $BASE_DIR/logs/service.log 2>/dev/null || echo "  Pas de logs"
    echo ""

    read -p "Appuyez sur Entrée pour continuer..."
}

system_status() {
    clear
    echo -e "${BLUE}═══ État du système ═══${NC}"
    echo ""

    # État du service
    echo -e "${YELLOW}Service Digital Signage:${NC}"
    systemctl status $SERVICE_NAME --no-pager | head -15
    echo ""

    # Processus en cours
    echo -e "${YELLOW}Processus actifs:${NC}"
    ps aux | grep -E "python3.*gestion|chromium" | grep -v grep
    echo ""

    # Connexion réseau
    echo -e "${YELLOW}Connexion réseau:${NC}"
    ping -c 1 -W 2 8.8.8.8 > /dev/null 2>&1 && echo "  ✅ Internet accessible" || echo "  ❌ Pas d'internet"
    echo ""

    read -p "Appuyez sur Entrée pour continuer..."
}

# Boucle principale
while true; do
    show_menu
    read choice

    case $choice in
        1) show_config ;;
        2) restart_service ;;
        3) show_logs ;;
        4) relaunch_wizard ;;
        5) manual_config ;;
        6) factory_reset ;;
        7) debug_mode ;;
        8) system_status ;;
        9)
            echo -e "${GREEN}Au revoir!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Choix invalide${NC}"
            sleep 1
            ;;
    esac
done
