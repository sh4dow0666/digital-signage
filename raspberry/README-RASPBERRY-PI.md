# Guide d'Installation Complet - Digital Signage sur Raspberry Pi 3

Ce guide vous accompagne pas à pas pour installer et configurer le système Digital Signage sur un Raspberry Pi 3.

## 📋 Prérequis

### Matériel nécessaire
- **Raspberry Pi 3** (Model B ou B+)
- Carte microSD (minimum 8 Go, recommandé 16 Go ou plus)
- Alimentation 5V 2.5A pour Raspberry Pi
- Écran avec entrée HDMI
- Câble HDMI
- Clavier et souris (uniquement pour l'installation initiale)
- Connexion Internet (Ethernet ou WiFi)

### Logiciels nécessaires (sur votre PC)
- [Raspberry Pi Imager](https://www.raspberrypi.com/software/) pour créer la carte SD

---

## 🚀 Installation Complète

### Étape 1 : Préparer la carte SD

1. **Télécharger Raspberry Pi OS Lite** (version sans bureau recommandée)
   - Ouvrez Raspberry Pi Imager
   - Choisissez "Raspberry Pi OS Lite (64-bit)" ou "Raspberry Pi OS Lite (32-bit)"

2. **Configurer l'OS avant installation**
   - Cliquez sur l'icône ⚙️ (paramètres)
   - Activez SSH
   - Configurez le nom d'utilisateur et mot de passe (ex: `pi`)
   - Configurez le WiFi si nécessaire
   - Configurez la locale (fr_FR.UTF-8) et le clavier (fr)

3. **Flasher la carte SD**
   - Sélectionnez votre carte SD
   - Cliquez sur "Écrire"
   - Attendez la fin du processus

### Étape 2 : Premier démarrage du Raspberry Pi

1. **Insérer la carte SD** dans le Raspberry Pi
2. **Brancher l'écran HDMI** et l'alimentation
3. **Attendre le démarrage** (1-2 minutes)
4. **Se connecter** avec les identifiants configurés

### Étape 3 : Configuration initiale du système

```bash
# Mettre à jour le système
sudo apt-get update
sudo apt-get upgrade -y

# Installer Git
sudo apt-get install -y git

# Configurer le fuseau horaire
sudo timedatectl set-timezone Europe/Paris

# Étendre le système de fichiers (si pas déjà fait)
sudo raspi-config --expand-rootfs
```

### Étape 4 : Cloner le projet

```bash
# Se placer dans le répertoire home
cd ~

# Cloner le projet (remplacez l'URL par votre repository)
git clone <URL_DE_VOTRE_REPOSITORY> DS

# Ou si vous transférez les fichiers manuellement :
# mkdir -p ~/DS
# scp -r /chemin/local/vers/DS/* pi@<IP_RASPBERRY>:~/DS/
```

### Étape 5 : Installer les dépendances

Le script d'installation peut installer automatiquement les dépendances, mais vous pouvez aussi les installer manuellement :

```bash
# Installer les dépendances système
sudo apt-get install -y \
    chromium-browser \
    xserver-xorg \
    xinit \
    x11-xserver-utils \
    unclutter \
    python3 \
    python3-pip \
    hostapd \
    dnsmasq

# Installer les dépendances Python
pip3 install flask flask-socketio python-socketio eventlet

# OU installer via apt (recommandé pour Raspberry Pi)
sudo apt-get install -y \
    python3-flask \
    python3-flask-socketio
```

### Étape 6 : Créer le fichier de configuration

```bash
# Créer le répertoire de configuration
mkdir -p ~/DS/raspberry/config

# Créer le fichier device.conf
cat > ~/DS/raspberry/config/device.conf << 'EOF'
# Configuration du dispositif Digital Signage

# État de configuration
CONFIGURED=false

# Rôles du dispositif
ROLE_CONTROLLER=false
ROLE_PLAYER=false

# Configuration écran (si ROLE_PLAYER=true)
SCREEN_ID=""
SCREEN_NAME=""
SCREEN_LOCATION=""
CONTROLLER_URL=""

# Configuration WiFi AP (pour premier démarrage)
WIFI_SSID="DigitalSignage-Setup"
WIFI_PASSWORD="raspberry123"
EOF
```

### Étape 7 : Installer le service de démarrage automatique

```bash
# Aller dans le répertoire des scripts
cd ~/DS/raspberry/scripts

# Rendre le script d'installation exécutable
chmod +x install-service.sh

# Lancer l'installation (nécessite sudo)
sudo ./install-service.sh
```

Le script va automatiquement :
- ✅ Détecter l'utilisateur et les chemins d'installation
- ✅ Vérifier et installer les dépendances manquantes
- ✅ Configurer sudo pour ne pas demander de mot de passe
- ✅ Installer le service systemd
- ✅ Démasquer hostapd
- ✅ Configurer l'autologin en console
- ✅ Désactiver le bureau graphique
- ✅ Configurer le lancement automatique de Chromium

**Exemple de sortie :**
```
🚀 Installation du service Digital Signage pour Raspberry Pi...

📋 Configuration détectée :
   Utilisateur : pi
   Répertoire d'installation : /home/pi/DS
   Home utilisateur : /home/pi
   Nom du service : digital-signage

❓ Confirmer l'installation avec cette configuration ? (o/N) o

🔧 Début de l'installation...
...
✅ Installation terminée avec succès !
```

### Étape 8 : Redémarrer le Raspberry Pi

```bash
sudo reboot
```

---

## 🎯 Première Utilisation

### Scénario A : Avec connexion réseau

Si votre Raspberry Pi est connecté au réseau (Ethernet ou WiFi) :

1. **Le système démarre automatiquement**
2. **Le wizard de configuration s'affiche** dans Chromium
3. **Accédez au wizard via l'écran** ou depuis un autre appareil :
   - URL : `http://<IP_DU_RASPBERRY>:8080`
   - Trouvez l'IP avec : `hostname -I`

4. **Configurez le dispositif** :
   - Choisissez le rôle : Contrôleur, Player, ou les deux
   - Si Player : configurez l'ID, nom et emplacement de l'écran
   - Si Contrôleur : laissez les paramètres par défaut

5. **Le système redémarre** et lance l'application configurée

### Scénario B : Sans connexion réseau (premier démarrage)

Si aucun réseau n'est disponible :

1. **Un point d'accès WiFi est créé automatiquement**
   - SSID : `DigitalSignage-Setup` (configurable dans device.conf)
   - Mot de passe : `raspberry123` (configurable dans device.conf)

2. **Connectez-vous au WiFi** depuis un smartphone ou PC

3. **Accédez au wizard** :
   - URL : `http://192.168.4.1:8080`

4. **Configurez le dispositif** comme dans le scénario A

5. **Le système redémarre** et se connecte au réseau configuré

---

## 📺 Modes d'utilisation

### Mode Contrôleur uniquement

Le Raspberry Pi héberge le serveur Flask et l'interface de gestion :
- Interface accessible via `http://<IP>:5000`
- Gère les écrans, contenus, playlists et plannings
- Peut tourner en headless (sans écran)

### Mode Player uniquement

Le Raspberry Pi affiche du contenu en plein écran :
- Se connecte à un contrôleur distant
- Affiche Chromium en mode kiosk
- Pas de bureau visible

### Mode Hybride (Contrôleur + Player)

Le Raspberry Pi fait les deux :
- Héberge le serveur
- Affiche également du contenu localement
- Idéal pour une configuration autonome

---

## 🔧 Dépannage

### Le service ne démarre pas

```bash
# Vérifier le statut du service
systemctl status digital-signage.service

# Voir les logs
journalctl -u digital-signage.service -n 50

# Tester le script manuellement
/home/pi/DS/raspberry/scripts/startup.sh
```

### Chromium ne s'affiche pas

```bash
# Vérifier que X11 est lancé
ps aux | grep X

# Vérifier la variable DISPLAY
echo $DISPLAY  # Doit afficher :0

# Vérifier les processus Chromium
ps aux | grep chromium

# Relancer X manuellement
startx
```

### Le point d'accès WiFi ne fonctionne pas

```bash
# Vérifier que hostapd n'est pas masked
systemctl status hostapd

# Démasquer hostapd si nécessaire
sudo systemctl unmask hostapd

# Vérifier les logs
journalctl -u hostapd -n 50

# Tester le script AP manuellement
sudo /home/pi/DS/raspberry/scripts/setup-ap.sh start
```

### Accéder au terminal

**Option 1 : SSH** (recommandé)
```bash
ssh pi@<IP_DU_RASPBERRY>
```

**Option 2 : TTY alternatif**
- Appuyez sur `Ctrl+Alt+F2` pour accéder à tty2
- Connectez-vous avec vos identifiants
- Retour à X : `Ctrl+Alt+F1` ou `Ctrl+Alt+F7`

**Option 3 : Arrêter le service temporairement**
```bash
sudo systemctl stop digital-signage.service
```

### Reconfigurer le système

```bash
# Modifier le fichier de configuration
nano ~/DS/raspberry/config/device.conf

# Changer CONFIGURED à false pour relancer le wizard
# CONFIGURED=false

# Redémarrer
sudo reboot
```

---

## 🛠️ Commandes Utiles

### Gestion du service

```bash
# Voir le statut
systemctl status digital-signage.service

# Arrêter le service
sudo systemctl stop digital-signage.service

# Démarrer le service
sudo systemctl start digital-signage.service

# Redémarrer le service
sudo systemctl restart digital-signage.service

# Désactiver le démarrage automatique
sudo systemctl disable digital-signage.service

# Réactiver le démarrage automatique
sudo systemctl enable digital-signage.service

# Voir les logs en temps réel
journalctl -u digital-signage.service -f
```

### Logs système

```bash
# Logs du service depuis le dernier boot
journalctl -u digital-signage.service -b

# Logs des 100 dernières lignes
journalctl -u digital-signage.service -n 100

# Logs en temps réel avec filtre
journalctl -u digital-signage.service -f | grep ERROR
```

### Réseau

```bash
# Voir l'adresse IP
hostname -I

# Tester la connexion Internet
ping -c 4 8.8.8.8

# Voir les interfaces réseau
ip addr show

# Redémarrer le réseau
sudo systemctl restart dhcpcd
```

---

## 🔄 Désinstallation

Pour revenir à une configuration normale avec bureau graphique :

```bash
cd ~/DS/raspberry/scripts
sudo ./uninstall-service.sh
sudo reboot
```

Cela va :
- Désinstaller le service
- Réactiver le bureau graphique
- Désactiver l'autologin
- Supprimer les configurations sudo

---

## 📁 Structure des Fichiers

```
~/DS/
├── gestion_raspberry.py          # Serveur Flask principal
├── templates/
│   ├── manager.html               # Interface de gestion
│   └── display.html               # Interface player
├── static/
│   └── css/
│       ├── style.css              # Styles manager
│       └── player.css             # Styles player
├── data/                          # Données persistantes (créé auto)
│   ├── screens.json
│   ├── content.json
│   ├── playlists.json
│   └── schedules.json
└── raspberry/
    ├── config/
    │   └── device.conf            # Configuration du dispositif
    ├── wizard/
    │   ├── wizard_server.py       # Serveur de configuration
    │   ├── index.html             # Interface wizard
    │   └── screen_info.html       # Page d'info écran
    └── scripts/
        ├── startup.sh             # Script de démarrage principal
        ├── setup-ap.sh            # Gestion du point d'accès WiFi
        ├── install-service.sh     # Installation du service
        ├── uninstall-service.sh   # Désinstallation
        ├── install-config.sh      # Configuration auto
        ├── digital-signage.service.template
        └── digital-signage-sudoers.template
```

---

## 🔐 Sécurité

### Recommandations

1. **Changer les mots de passe par défaut**
   ```bash
   passwd  # Changer le mot de passe utilisateur
   ```

2. **Changer le SSID et mot de passe WiFi du point d'accès**
   ```bash
   nano ~/DS/raspberry/config/device.conf
   # Modifier WIFI_SSID et WIFI_PASSWORD
   ```

3. **Activer le pare-feu** (optionnel)
   ```bash
   sudo apt-get install ufw
   sudo ufw allow 22/tcp   # SSH
   sudo ufw allow 5000/tcp # Flask
   sudo ufw allow 8080/tcp # Wizard
   sudo ufw enable
   ```

4. **Utiliser SSH avec clés** au lieu de mots de passe
   ```bash
   ssh-copy-id pi@<IP_RASPBERRY>
   ```

---

## 📊 Performances et Optimisation

### Optimiser pour Raspberry Pi 3

```bash
# Augmenter la mémoire GPU (pour Chromium)
sudo raspi-config
# Performance Options > GPU Memory > 128

# Désactiver les services inutiles
sudo systemctl disable bluetooth
sudo systemctl disable cups

# Overclocker (optionnel, à vos risques)
sudo nano /boot/config.txt
# Ajouter :
# arm_freq=1350
# over_voltage=2
```

### Surveillance

```bash
# Température du CPU
vcgencmd measure_temp

# Utilisation CPU/RAM
htop

# Espace disque
df -h
```

---

## 📞 Support et Documentation

### Fichiers de documentation
- `README-SERVICE.md` - Documentation du service systemd
- `CLAUDE.md` - Vue d'ensemble du projet

### Logs importants
- Service : `journalctl -u digital-signage.service`
- X11 : `~/.xsession-errors`
- Système : `journalctl -xe`

### Commandes de diagnostic

```bash
# Vérifier la configuration complète
~/DS/raspberry/scripts/install-config.sh

# Tester le wizard manuellement
cd ~/DS/raspberry/wizard
python3 wizard_server.py --port 8080

# Tester le contrôleur manuellement
cd ~/DS
python3 gestion_raspberry.py
```

---

## ✅ Checklist de Vérification

Après installation, vérifiez que :

- [ ] Le Raspberry Pi démarre sans intervention
- [ ] Chromium s'affiche en plein écran automatiquement
- [ ] Aucun bureau graphique n'est visible
- [ ] Aucun mot de passe n'est demandé
- [ ] Le wizard s'affiche au premier démarrage
- [ ] Le point d'accès WiFi fonctionne sans réseau
- [ ] Le service redémarre automatiquement en cas de plantage
- [ ] Les logs sont accessibles via journalctl
- [ ] Le SSH fonctionne pour l'administration à distance

---

## 🎓 Conseils Avancés

### Déploiement sur plusieurs Raspberry Pi

1. **Créer une image master**
   ```bash
   # Sur le premier Raspberry Pi configuré
   sudo dd if=/dev/mmcblk0 of=~/digital-signage-master.img bs=4M status=progress

   # Copier l'image sur votre PC
   scp pi@<IP>:~/digital-signage-master.img .

   # Flasher sur d'autres cartes SD
   sudo dd if=digital-signage-master.img of=/dev/sdX bs=4M status=progress
   ```

2. **Reconfigurer chaque Raspberry Pi**
   ```bash
   # Sur chaque nouveau Pi, réinitialiser la config
   nano ~/DS/raspberry/config/device.conf
   # Mettre CONFIGURED=false
   sudo reboot
   ```

### Mise à jour du code

```bash
cd ~/DS
git pull origin main
sudo systemctl restart digital-signage.service
```

### Sauvegarde des données

```bash
# Sauvegarder la configuration et les données
tar -czf digital-signage-backup-$(date +%Y%m%d).tar.gz \
    ~/DS/raspberry/config/device.conf \
    ~/DS/data/

# Restaurer
tar -xzf digital-signage-backup-YYYYMMDD.tar.gz -C ~/
```

---

**Bonne installation ! 🚀**
