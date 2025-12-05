#!/bin/bash
# Script de démarrage du système Digital Signage

set -e

# Variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$BASE_DIR/config/device.conf"
WIZARD_PORT=8080

# Charger la configuration
source $CONFIG_FILE

# Fonction pour obtenir l'IP locale
get_local_ip() {
    hostname -I | awk '{print $1}'
}

# Fonction pour vérifier la connexion réseau
check_network() {
    if ping -c 1 -W 2 8.8.8.8 > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Premier lancement - Configuration nécessaire
if [ "$CONFIGURED" = "false" ]; then
    echo "🔧 Premier lancement détecté - Lancement du wizard de configuration..."

    # Vérifier la connexion réseau
    if check_network; then
        echo "✅ Connexion réseau détectée"
        LOCAL_IP=$(get_local_ip)

        # Lancer le wizard sur le réseau existant
        cd $BASE_DIR/wizard
        python3 wizard_server.py --port $WIZARD_PORT --ip "$LOCAL_IP" &
        WIZARD_PID=$!

        # Afficher la page de configuration dans Chromium
        sleep 3
        DISPLAY=:0 chromium \
            --kiosk \
            --noerrdialogs \
            --disable-infobars \
            --no-first-run \
            --disable-restore-session-state \
            --password-store=basic \
            --start-maximized \
            "http://$LOCAL_IP:$WIZARD_PORT" &

        # Attendre la fin du wizard
        wait $WIZARD_PID

    else
        echo "⚠️  Aucune connexion réseau - Création du point d'accès WiFi..."

        # Créer le point d'accès WiFi
        sudo $SCRIPT_DIR/setup-ap.sh start

        # Lancer le wizard sur le point d'accès
        cd $BASE_DIR/wizard
        python3 wizard_server.py --port $WIZARD_PORT --ip "192.168.4.1" &
        WIZARD_PID=$!

        # Afficher la page de configuration
        sleep 3
        DISPLAY=:0 chromium \
            --kiosk \
            --noerrdialogs \
            --disable-infobars \
            --no-first-run \
            --disable-restore-session-state \
            --password-store=basic \
            --start-maximized \
            "http://192.168.4.1:$WIZARD_PORT" &

        # Attendre la fin du wizard
        wait $WIZARD_PID

        # Arrêter le point d'accès
        sudo $SCRIPT_DIR/setup-ap.sh stop
    fi

    # Recharger la configuration
    source $CONFIG_FILE

    # Redémarrer pour appliquer la nouvelle configuration
    echo "🔄 Configuration terminée - Redémarrage..."
    sudo reboot
fi

# Configuration terminée - Démarrage normal
echo "🚀 Démarrage du système Digital Signage..."

# Démarrer le contrôleur si le rôle est activé
if [ "$ROLE_CONTROLLER" = "true" ]; then
    echo "🎮 Démarrage du contrôleur..."
    cd $BASE_DIR
    python3 gestion_raspberry.py &
    CONTROLLER_PID=$!
    echo "✅ Contrôleur démarré (PID: $CONTROLLER_PID)"
fi

# Démarrer le player si le rôle est activé
if [ "$ROLE_PLAYER" = "true" ]; then
    echo "📺 Démarrage du player..."

    # Attendre quelques secondes pour que le contrôleur démarre
    if [ "$ROLE_CONTROLLER" = "true" ]; then
        sleep 5
    fi

    # Construire l'URL du display
    DISPLAY_URL="${CONTROLLER_URL}/display?id=${SCREEN_ID}&name=${SCREEN_NAME}&location=${SCREEN_LOCATION}"

    # Afficher d'abord la page d'information pendant 10 secondes
    DISPLAY=:0 chromium \
        --kiosk \
        --noerrdialogs \
        --disable-infobars \
        --no-first-run \
        --disable-restore-session-state \
        --password-store=basic \
        --start-maximized \
        "file://$BASE_DIR/raspberry/wizard/screen_info.html?id=${SCREEN_ID}&name=${SCREEN_NAME}&location=${SCREEN_LOCATION}&controller=${CONTROLLER_URL}" &

    sleep 10

    # Tuer Chromium et relancer avec l'URL du display
    pkill -f chromium
    sleep 2

    DISPLAY=:0 chromium \
        --kiosk \
        --noerrdialogs \
        --disable-infobars \
        --no-first-run \
        --disable-restore-session-state \
        --password-store=basic \
        --start-maximized \
        "$DISPLAY_URL" &

    echo "✅ Player démarré avec l'URL: $DISPLAY_URL"
fi

# Garder le script actif
wait
