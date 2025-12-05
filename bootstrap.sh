#!/bin/bash
# Script de bootstrap - Installation Digital Signage en une commande
# Usage: curl -fsSL https://raw.githubusercontent.com/sh4dow0666/digital-signage/main/bootstrap.sh | bash

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
REPO_URL="https://github.com/sh4dow0666/digital-signage.git"
INSTALL_DIR="$HOME/DS"
BRANCH="main"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Digital Signage - Installation automatique        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Vérifier si on est sur un Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null && ! grep -q "BCM" /proc/cpuinfo 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Attention: Ce script est conçu pour Raspberry Pi${NC}"
    echo -e "${YELLOW}   Continuer quand même ? (y/N)${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo -e "${RED}Installation annulée${NC}"
        exit 1
    fi
fi

# Vérifier si l'utilisateur est root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}❌ Ne pas exécuter ce script en tant que root${NC}"
    echo -e "${YELLOW}   Utilisez: bash bootstrap.sh${NC}"
    echo -e "${YELLOW}   Le script demandera sudo quand nécessaire${NC}"
    exit 1
fi

# Vérifier la connexion internet
echo -e "${YELLOW}🌐 Vérification de la connexion internet...${NC}"
if ! ping -c 1 github.com >/dev/null 2>&1; then
    echo -e "${RED}❌ Pas de connexion internet${NC}"
    echo -e "${YELLOW}   Veuillez vérifier votre connexion réseau${NC}"
    exit 1
fi

# Installer git si nécessaire
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}📦 Installation de git...${NC}"
    sudo apt-get update
    sudo apt-get install -y git
fi

# Nettoyer l'ancien répertoire si existant
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}🗑️  Nettoyage de l'ancienne installation...${NC}"
    rm -rf "$INSTALL_DIR"
fi

# Cloner le repository
echo -e "${YELLOW}📥 Téléchargement du projet depuis GitHub...${NC}"
git clone -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR"

if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${RED}❌ Erreur lors du clonage du repository${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Projet téléchargé avec succès${NC}"
echo ""

# Rendre les scripts exécutables
echo -e "${YELLOW}🔧 Configuration des permissions...${NC}"
find "$INSTALL_DIR" -name "*.sh" -type f -exec chmod +x {} \;

# Fixer les fins de lignes (au cas où le clonage ait causé des problèmes)
echo -e "${YELLOW}🔧 Normalisation des fins de lignes...${NC}"
if command -v dos2unix &> /dev/null; then
    find "$INSTALL_DIR" -name "*.sh" -type f -exec dos2unix {} \; 2>/dev/null || true
else
    # Utiliser sed si dos2unix n'est pas disponible
    find "$INSTALL_DIR" -name "*.sh" -type f -exec sed -i 's/\r$//' {} \;
fi
echo -e "${GREEN}✅ Fins de lignes normalisées${NC}"

# Lancer l'installation complète
echo -e "${YELLOW}🚀 Lancement de l'installation complète...${NC}"
echo ""
cd "$INSTALL_DIR"
sudo "$INSTALL_DIR/raspberry/install.sh"
