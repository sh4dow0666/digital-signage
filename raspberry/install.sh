#!/bin/bash
# Script d'installation pour Raspberry Pi Digital Signage
# Compatible avec Raspberry Pi 3

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
INSTALL_DIR="/opt/digital-signage"
SERVICE_NAME="digital-signage"

# recupere le user actuel
USER=$(logname 2>/dev/null || echo $USER)

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Installation Digital Signage pour Raspberry Pi 3         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Vérifier si l'utilisateur est root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Ce script doit être exécuté en tant que root (sudo)${NC}"
    exit 1
fi

echo -e "${YELLOW}📦 Mise à jour du système...${NC}"
apt-get update
apt-get upgrade -y

echo -e "${YELLOW}⚙️  Configuration automatique de raspi-config...${NC}"
# Configuration du boot automatique en mode desktop
if command -v raspi-config >/dev/null 2>&1; then
    echo -e "${BLUE}   → Activation de l'autologin...${NC}"
    systemctl set-default multi-user.target
    mkdir -p /etc/systemd/system/getty@tty1.service.d
    cat <<EOF | sudo tee /etc/systemd/system/getty@tty1.service.d/autologin.conf >/dev/null
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $USER --noclear %I \$TERM
EOF

    echo -e "${BLUE}   → Désactivation du screen blanking...${NC}"
    raspi-config nonint do_blanking 1 2>/dev/null || echo -e "${YELLOW}   ⚠️  Configuration screen blanking manuelle requise${NC}"

    echo -e "${BLUE}   → Configuration du pays pour le wifi...${NC}"
    raspi-config nonint do_wifi_country FR 2>/dev/null || echo -e "${YELLOW}   ⚠️  Configuration pays wifi manuelle requise${NC}"

    echo -e "${GREEN}   ✅ Configuration raspi-config terminée${NC}"
else
    echo -e "${YELLOW}   ⚠️  raspi-config non disponible (pas sur Raspberry Pi ?)${NC}"
fi

echo -e "${YELLOW}📦 Installation des dépendances...${NC}"
apt-get install -y \
    --no-install-recommends xserver-xorg xorg xinit \
    python3 \
    python3-pip \
    chromium \
    xdotool \
    unclutter \
    sed \
    hostapd \
    dnsmasq \
    dhcpcd5 \
    git \
    fail2ban iptables

# Désactiver hostapd et dnsmasq par défaut (seront activés si besoin)
# D'abord unmask si nécessaire, puis arrêter et désactiver
systemctl unmask hostapd 2>/dev/null || true
systemctl unmask dnsmasq 2>/dev/null || true
systemctl stop hostapd 2>/dev/null || true
systemctl stop dnsmasq 2>/dev/null || true
systemctl disable hostapd 2>/dev/null || true
systemctl disable dnsmasq 2>/dev/null || true
systemctl enable fail2ban --now

echo -e "${YELLOW}📦 Installation des dépendances Python...${NC}"
pip3 install flask flask-socketio python-socketio requests isodate pyotp qrcode pillow --break-system-packages

echo -e "${YELLOW}📁 Création du répertoire d'installation...${NC}"
mkdir -p $INSTALL_DIR
mkdir -p $INSTALL_DIR/data
mkdir -p $INSTALL_DIR/logs
mkdir -p $INSTALL_DIR/raspberry/config

echo -e "${YELLOW}📝 Copie des fichiers...${NC}"
# Déterminer le répertoire source du projet
SOURCE_DIR="/home/$USER/DS"
if [ ! -d "$SOURCE_DIR" ]; then
    # Si on n'est pas dans le répertoire par défaut, utiliser le répertoire du script
    SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

# Copier tous les fichiers du projet
echo -e "${BLUE}   → Source: $SOURCE_DIR${NC}"
echo -e "${BLUE}   → Destination: $INSTALL_DIR${NC}"
cp -r "$SOURCE_DIR"/* $INSTALL_DIR/
chmod +x $INSTALL_DIR/raspberry/scripts/*.sh

echo -e "${YELLOW}⚙️  Configuration des fichiers de configuration...${NC}"
# Créer le fichier de configuration s'il n'existe pas
if [ ! -f "$INSTALL_DIR/raspberry/config/device.conf" ]; then
    cat > $INSTALL_DIR/raspberry/config/device.conf << 'EOF'
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
    chown $USER:$USER $INSTALL_DIR/raspberry/config/device.conf
fi

echo -e "${YELLOW}🖥️  Configuration du démarrage automatique en mode kiosk...${NC}"
# Configuration de l'environnement graphique
cat > /home/$USER/.xinitrc << 'EOF'
#!/bin/bash

xset -dpms
xset s off
xset s noblank

# cacher le curseur
unclutter -idle 0.1 &

/bin/bash /opt/digital-signage/raspberry/scripts/startup.sh
EOF

chmod +x /home/$USER/.xinitrc

# demarrage auomatique de xinit
cat >> /home/$USER/.bash_profile << 'EOF'
if [[ -z $DISPLAY ]] && [[ $(tty) = /dev/tty1 ]]; then
  startx
fi
EOF

chown -R $USER:$USER /home/$USER/.config

echo -e "${YELLOW}🔐 Configuration des permissions...${NC}"
chown -R $USER:$USER $INSTALL_DIR
chmod -R 755 $INSTALL_DIR/raspberry/scripts

echo -e "${YELLOW}📱 Installation du script de maintenance...${NC}"
cp $INSTALL_DIR/raspberry/scripts/maintenance.sh /usr/local/bin/ds-maintenance
chmod +x /usr/local/bin/ds-maintenance

echo -e "${YELLOW}🚀 Configuration de fail2ban...${NC}"
awk '
BEGIN { in_sshd=0 }
/^\[sshd\]/ {
    print "[sshd]"
    print "enabled = true"
    print "port    = ssh"
    print "logpath = %(sshd_log)s"
    print "backend = %(sshd_backend)s"
    print "maxretry = 5"
    print "bantime  = 1h"
    print "findtime = 10m"
    print "filter = sshd"
    print "banaction = iptables-multiport"
    in_sshd=1
    next
}
/^\[/ {
    if (in_sshd) in_sshd=0
}
!in_sshd
' "/etc/fail2ban/jail.conf" > "/etc/fail2ban/jail.local"
systemctl restart fail2ban

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ Installation terminée avec succès !                    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📝 Prochaines étapes :${NC}"
echo ""
echo -e "  1️⃣  Redémarrer le Raspberry Pi : ${YELLOW}sudo reboot${NC}"
echo ""
echo -e "  2️⃣  Au démarrage, le wizard de configuration s'affichera automatiquement"
echo ""
echo -e "  3️⃣  Pour accéder au script de maintenance : ${YELLOW}sudo ds-maintenance${NC}"
echo ""
echo -e "${BLUE}📋 Logs disponibles dans : ${YELLOW}$INSTALL_DIR/logs/${NC}"
echo ""
