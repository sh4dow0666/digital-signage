#!/bin/bash
# Configuration pour l'installation du service Digital Signage
# Ce fichier sera sourcé par les scripts d'installation

# Détecter l'utilisateur qui installe (si lancé via sudo, récupérer le vrai utilisateur)
if [ -n "$SUDO_USER" ]; then
    INSTALL_USER="$SUDO_USER"
else
    INSTALL_USER="$(whoami)"
fi

# Détecter le répertoire d'installation (répertoire parent du dossier scripts)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Répertoire home de l'utilisateur
USER_HOME="$(eval echo ~$INSTALL_USER)"

# Nom du service
SERVICE_NAME="digital-signage"

# Afficher la configuration détectée
echo "📋 Configuration détectée :"
echo "   Utilisateur : $INSTALL_USER"
echo "   Répertoire d'installation : $INSTALL_DIR"
echo "   Home utilisateur : $USER_HOME"
echo "   Nom du service : $SERVICE_NAME"
