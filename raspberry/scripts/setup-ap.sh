#!/bin/bash
# Script de gestion du point d'accès WiFi

set -e

# Variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$BASE_DIR/config/device.conf"

# Charger la configuration
source $CONFIG_FILE

start_ap() {
    echo "🔧 Configuration du point d'accès WiFi..."

    # Arrêter les services
    sudo systemctl stop dhcpcd 2>/dev/null || true
    sudo systemctl stop dnsmasq 2>/dev/null || true
    sudo systemctl stop hostapd 2>/dev/null || true

    # Configuration de l'interface wlan0
    sudo ip addr flush dev wlan0
    sudo ip addr add 192.168.4.1/24 dev wlan0
    sudo ip link set wlan0 up

    # Configuration de dnsmasq
    sudo tee /etc/dnsmasq.conf > /dev/null << EOF
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
domain=local
address=/digitalsignage.local/192.168.4.1
EOF

    # Configuration de hostapd
    sudo tee /etc/hostapd/hostapd.conf > /dev/null << EOF
interface=wlan0
driver=nl80211
ssid=$WIFI_SSID
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$WIFI_PASSWORD
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

    # Pointer vers la configuration hostapd
    sudo sed -i 's|#DAEMON_CONF=""|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd

    # Activer le routage IP
    echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward > /dev/null

    # Démarrer les services
    sudo systemctl start dnsmasq
    sudo systemctl start hostapd

    echo "✅ Point d'accès WiFi démarré"
    echo "   SSID: $WIFI_SSID"
    echo "   Password: $WIFI_PASSWORD"
    echo "   IP: 192.168.4.1"
}

stop_ap() {
    echo "🛑 Arrêt du point d'accès WiFi..."

    # Arrêter les services
    sudo systemctl stop hostapd 2>/dev/null || true
    sudo systemctl stop dnsmasq 2>/dev/null || true

    # Restaurer la configuration réseau normale
    sudo ip addr flush dev wlan0
    sudo systemctl start dhcpcd

    echo "✅ Point d'accès WiFi arrêté"
}

case "$1" in
    start)
        start_ap
        ;;
    stop)
        stop_ap
        ;;
    restart)
        stop_ap
        sleep 2
        start_ap
        ;;
    *)
        echo "Usage: $0 {start|stop|restart}"
        exit 1
        ;;
esac
