#!/bin/bash
# Script d'installation du service Digital Signage pour Raspberry Pi

set -e

echo "🚀 Installation du service Digital Signage pour Raspberry Pi..."
echo ""

# Vérifier si on est root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté en tant que root (sudo)"
    echo "   Usage: sudo ./install-service.sh"
    exit 1
fi

# Charger la configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/install-config.sh"

echo ""
read -p "❓ Confirmer l'installation avec cette configuration ? (o/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[OoYy]$ ]]; then
    echo "❌ Installation annulée"
    exit 1
fi

echo ""
echo "🔧 Début de l'installation..."

# 1. Vérifier que les dépendances sont installées
echo ""
echo "📦 Vérification des dépendances..."

MISSING_DEPS=()

if ! command -v chromium &> /dev/null && ! command -v chromium-browser &> /dev/null; then
    MISSING_DEPS+=("chromium-browser")
fi

if ! command -v python3 &> /dev/null; then
    MISSING_DEPS+=("python3")
fi

if ! dpkg -l | grep -q "python3-flask"; then
    MISSING_DEPS+=("python3-flask")
fi

if ! dpkg -l | grep -q "python3-flask-socketio"; then
    MISSING_DEPS+=("python3-flask-socketio")
fi

if ! dpkg -l | grep -q "hostapd"; then
    MISSING_DEPS+=("hostapd")
fi

if ! dpkg -l | grep -q "dnsmasq"; then
    MISSING_DEPS+=("dnsmasq")
fi

if ! dpkg -l | grep -q "xinit"; then
    MISSING_DEPS+=("xinit")
fi

if ! dpkg -l | grep -q "xserver-xorg"; then
    MISSING_DEPS+=("xserver-xorg")
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo "⚠️  Dépendances manquantes détectées : ${MISSING_DEPS[*]}"
    read -p "❓ Voulez-vous installer les dépendances manquantes ? (o/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[OoYy]$ ]]; then
        echo "📥 Installation des dépendances..."
        apt-get update
        apt-get install -y "${MISSING_DEPS[@]}"
        echo "✅ Dépendances installées"
    else
        echo "⚠️  Installation sans dépendances. Le système peut ne pas fonctionner correctement."
    fi
else
    echo "✅ Toutes les dépendances sont installées"
fi

# 2. Générer le fichier sudoers depuis le template
echo ""
echo "📝 Configuration de sudo..."
sed -e "s|__INSTALL_USER__|$INSTALL_USER|g" \
    -e "s|__INSTALL_DIR__|$INSTALL_DIR|g" \
    "$SCRIPT_DIR/digital-signage-sudoers.template" > /tmp/digital-signage-sudoers

# Vérifier la syntaxe du fichier sudoers
if visudo -c -f /tmp/digital-signage-sudoers > /dev/null 2>&1; then
    cp /tmp/digital-signage-sudoers /etc/sudoers.d/digital-signage
    chmod 0440 /etc/sudoers.d/digital-signage
    rm /tmp/digital-signage-sudoers
    echo "✅ Configuration sudo installée"
else
    echo "❌ Erreur dans la syntaxe du fichier sudoers"
    rm /tmp/digital-signage-sudoers
    exit 1
fi

# 3. Démasquer et configurer hostapd
echo ""
echo "📡 Configuration de hostapd..."
systemctl unmask hostapd 2>/dev/null || true
echo "✅ hostapd démasqué"

# 4. Générer et installer le service systemd depuis le template
echo ""
echo "⚙️  Installation du service systemd..."
sed -e "s|__INSTALL_USER__|$INSTALL_USER|g" \
    -e "s|__USER_HOME__|$USER_HOME|g" \
    -e "s|__INSTALL_DIR__|$INSTALL_DIR|g" \
    "$SCRIPT_DIR/digital-signage.service.template" > /etc/systemd/system/$SERVICE_NAME.service

systemctl daemon-reload
systemctl enable $SERVICE_NAME.service
echo "✅ Service systemd installé et activé"

# 5. Configurer l'autologin en mode console
echo ""
echo "🖥️  Configuration de l'autologin sans bureau..."

# Créer le fichier xinitrc pour l'utilisateur
cat > "$USER_HOME/.xinitrc" << EOF
#!/bin/bash
# Désactiver l'économiseur d'écran et la mise en veille
xset s off
xset -dpms
xset s noblank

# Cacher le curseur de la souris
unclutter -idle 0.1 &

# Lancer le script de démarrage
exec $INSTALL_DIR/raspberry/scripts/startup.sh
EOF
chown $INSTALL_USER:$INSTALL_USER "$USER_HOME/.xinitrc"
chmod +x "$USER_HOME/.xinitrc"

# Configurer l'autologin en console (tty1) avec systemd
mkdir -p /etc/systemd/system/getty@tty1.service.d
cat > /etc/systemd/system/getty@tty1.service.d/override.conf << EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $INSTALL_USER --noclear %I \$TERM
EOF

# Ajouter le lancement automatique de X dans .bash_profile
if ! grep -q "startx" "$USER_HOME/.bash_profile" 2>/dev/null; then
    cat >> "$USER_HOME/.bash_profile" << EOF

# Lancer X automatiquement au login sur tty1
if [ -z "\$DISPLAY" ] && [ "\$(tty)" = "/dev/tty1" ]; then
    exec startx
fi
EOF
    chown $INSTALL_USER:$INSTALL_USER "$USER_HOME/.bash_profile"
fi

echo "✅ Autologin configuré"

# 6. Désactiver le gestionnaire de bureau graphique (si présent)
echo ""
echo "🔧 Désactivation du bureau graphique..."
if systemctl is-active lightdm &>/dev/null || systemctl is-enabled lightdm &>/dev/null; then
    systemctl disable lightdm 2>/dev/null || true
    systemctl stop lightdm 2>/dev/null || true
    echo "✅ LightDM désactivé"
elif systemctl is-active gdm &>/dev/null || systemctl is-enabled gdm &>/dev/null; then
    systemctl disable gdm 2>/dev/null || true
    systemctl stop gdm 2>/dev/null || true
    echo "✅ GDM désactivé"
elif systemctl is-active gdm3 &>/dev/null || systemctl is-enabled gdm3 &>/dev/null; then
    systemctl disable gdm3 2>/dev/null || true
    systemctl stop gdm3 2>/dev/null || true
    echo "✅ GDM3 désactivé"
else
    echo "   Aucun gestionnaire de bureau à désactiver"
fi

# Définir le mode multi-user (console) comme cible par défaut
systemctl set-default multi-user.target
echo "✅ Mode console configuré"

# 7. Rendre les scripts exécutables
echo ""
echo "🔐 Configuration des permissions..."
chmod +x "$INSTALL_DIR/raspberry/scripts/startup.sh"
chmod +x "$INSTALL_DIR/raspberry/scripts/setup-ap.sh"
chown -R $INSTALL_USER:$INSTALL_USER "$INSTALL_DIR"
echo "✅ Permissions configurées"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║  ✅ Installation terminée avec succès !                        ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 Résumé de la configuration :"
echo "   • Utilisateur    : $INSTALL_USER"
echo "   • Installation   : $INSTALL_DIR"
echo "   • Service        : $SERVICE_NAME.service"
echo ""
echo "📋 Modifications appliquées :"
echo "   ✅ Service systemd installé et activé"
echo "   ✅ Permissions sudo configurées (pas de mot de passe)"
echo "   ✅ hostapd démasqué"
echo "   ✅ Autologin en console activé"
echo "   ✅ Bureau graphique désactivé"
echo "   ✅ Chromium se lancera automatiquement en plein écran"
echo ""
echo "🔄 Pour appliquer les changements, redémarrez le Raspberry Pi :"
echo "   sudo reboot"
echo ""
echo "📖 Pour plus d'informations, consultez :"
echo "   $SCRIPT_DIR/README-RASPBERRY-PI.md"
echo ""
