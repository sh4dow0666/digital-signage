# Installation Rapide - Digital Signage sur Raspberry Pi 3

## 🚀 Installation en 5 étapes

### 1. Préparer le Raspberry Pi

```bash
# Mettre à jour le système
sudo apt-get update && sudo apt-get upgrade -y

# Installer Git
sudo apt-get install -y git
```

### 2. Récupérer le projet

```bash
cd ~
git clone <URL_REPOSITORY> DS
# OU transférer les fichiers manuellement
```

### 3. Créer le fichier de configuration

```bash
mkdir -p ~/DS/raspberry/config
cat > ~/DS/raspberry/config/device.conf << 'EOF'
CONFIGURED=false
ROLE_CONTROLLER=false
ROLE_PLAYER=false
SCREEN_ID=""
SCREEN_NAME=""
SCREEN_LOCATION=""
CONTROLLER_URL=""
WIFI_SSID="DigitalSignage-Setup"
WIFI_PASSWORD="raspberry123"
EOF
```

### 4. Installer le service

```bash
cd ~/DS/raspberry/scripts
sudo ./install-service.sh
```

Le script détecte automatiquement :
- ✅ L'utilisateur actuel
- ✅ Le chemin d'installation
- ✅ Installe toutes les dépendances manquantes

### 5. Redémarrer

```bash
sudo reboot
```

---

## 📖 Documentation Complète

Pour plus de détails, consultez :
- **README-RASPBERRY-PI.md** - Guide complet avec dépannage
- **README-SERVICE.md** - Documentation technique du service

---

## ✅ Ce qui se passe après le reboot

1. Login automatique en console
2. Lancement de X11 (pas de bureau)
3. **Chromium en plein écran uniquement**
4. Wizard de configuration au premier démarrage
5. Point d'accès WiFi si pas de réseau

---

## 🔧 Commandes Utiles

```bash
# Voir les logs
journalctl -u digital-signage.service -f

# Arrêter/redémarrer le service
sudo systemctl stop digital-signage.service
sudo systemctl restart digital-signage.service

# Désinstaller
cd ~/DS/raspberry/scripts
sudo ./uninstall-service.sh
```

---

## 🆘 Problèmes Courants

**Le service ne démarre pas :**
```bash
journalctl -u digital-signage.service -n 50
```

**Chromium ne s'affiche pas :**
```bash
ps aux | grep chromium
echo $DISPLAY  # Doit afficher :0
```

**hostapd masked :**
```bash
sudo systemctl unmask hostapd
```

**Accéder au terminal :**
```bash
ssh pi@<IP>  # Via SSH
# OU Ctrl+Alt+F2 pour tty2
```

---

**C'est tout ! Le système fonctionne de manière autonome. 🎉**
