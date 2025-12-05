#!/bin/bash
# Script de désinstallation du service Digital Signage

set -e

echo "🛑 Désinstallation du service Digital Signage..."
echo ""

# Vérifier si on est root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté en tant que root (sudo)"
    echo "   Usage: sudo ./uninstall-service.sh"
    exit 1
fi

# Charger la configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/install-config.sh"

echo ""
read -p "❓ Confirmer la désinstallation ? (o/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[OoYy]$ ]]; then
    echo "❌ Désinstallation annulée"
    exit 1
fi

# 1. Arrêter et désactiver le service
echo ""
echo "⚙️  Arrêt du service..."
systemctl stop $SERVICE_NAME.service 2>/dev/null || true
systemctl disable $SERVICE_NAME.service 2>/dev/null || true
rm -f /etc/systemd/system/$SERVICE_NAME.service
systemctl daemon-reload
echo "✅ Service désinstallé"

# 2. Supprimer le fichier sudoers
echo ""
echo "📝 Suppression de la configuration sudo..."
rm -f /etc/sudoers.d/digital-signage
echo "✅ Configuration sudo supprimée"

# 3. Désactiver l'autologin
echo ""
echo "🖥️  Désactivation de l'autologin..."
rm -f /etc/systemd/system/getty@tty1.service.d/override.conf
rmdir /etc/systemd/system/getty@tty1.service.d 2>/dev/null || true

# 4. Supprimer les fichiers de configuration utilisateur
rm -f "$USER_HOME/.xinitrc"

# Supprimer les lignes startx de .bash_profile
if [ -f "$USER_HOME/.bash_profile" ]; then
    sed -i '/# Lancer X automatiquement/,/fi/d' "$USER_HOME/.bash_profile"
fi

echo "✅ Autologin désactivé"

# 5. Réactiver le bureau graphique
echo ""
echo "🔧 Réactivation du bureau graphique..."
systemctl set-default graphical.target

if systemctl list-unit-files | grep -q lightdm; then
    systemctl enable lightdm
    echo "✅ LightDM réactivé"
elif systemctl list-unit-files | grep -q gdm; then
    systemctl enable gdm
    echo "✅ GDM réactivé"
elif systemctl list-unit-files | grep -q gdm3; then
    systemctl enable gdm3
    echo "✅ GDM3 réactivé"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║  ✅ Désinstallation terminée avec succès !                     ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "🔄 Pour appliquer les changements, redémarrez le Raspberry Pi :"
echo "   sudo reboot"
echo ""
