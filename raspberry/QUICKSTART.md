# 🚀 Guide de démarrage rapide

## Installation en 5 minutes

### 1️⃣ Préparer la carte SD

```bash
# Utiliser Raspberry Pi Imager
# - OS: Raspberry Pi OS (32 ou 64-bit) with desktop
#   → Les deux versions fonctionnent parfaitement
# - Activer SSH, définir utilisateur/mot de passe
# - Configurer WiFi si possible
```

### 2️⃣ Premier boot du Raspberry Pi

```bash
# Se connecter
ssh pi@raspberrypi.local
# ou via écran/clavier

# Mettre à jour
sudo apt update && sudo apt upgrade -y

# Configurer le démarrage automatique
sudo raspi-config
# → Boot Options → Desktop Autologin
# → Display Options → Screen Blanking → No
```

### 3️⃣ Installer Digital Signage

```bash
# Cloner le projet
cd ~
git clone [URL_DU_REPO] DS
cd DS

# Installer
chmod +x raspberry/install.sh
sudo raspberry/install.sh

# Redémarrer
sudo reboot
```

### 4️⃣ Configuration initiale

**Au redémarrage, le wizard s'affiche automatiquement !**

#### Si connecté au réseau :
- Note l'IP affichée : `http://192.168.X.X:8080`
- Suis le wizard à l'écran

#### Si pas de réseau :
- Le Pi crée un WiFi : `DigitalSignage-Setup`
- Mot de passe : `signage2024`
- Connecte-toi et va sur : `http://192.168.4.1:8080`

### 5️⃣ Choisir la configuration

#### Option A : Pi autonome (recommandé pour débuter)
```
✅ Rôle Contrôleur
✅ Rôle Player
ID: ecran1
Nom: Mon écran
URL: http://localhost:5000
```

#### Option B : Pi contrôleur uniquement
```
✅ Rôle Contrôleur
❌ Rôle Player
```

#### Option C : Pi player uniquement
```
❌ Rôle Contrôleur
✅ Rôle Player
ID: ecran1
Nom: Écran salle 1
URL: http://[IP-DU-CONTROLEUR]:5000
```

### 6️⃣ C'est fini !

Le Pi redémarre et est opérationnel !

---

## 🎯 Premiers pas

### Ajouter du contenu

1. Accéder à : `http://[IP-DU-PI]:5000`
2. Cliquer sur **+ Ajouter** dans la section Bibliothèque
3. Remplir :
   - Nom : "Ma première page"
   - Type : Page Web
   - URL : https://www.google.com
   - Durée : 00:00:30

### Créer une playlist

1. Cliquer sur **+ Ajouter** dans la section Playlists
2. Donner un nom : "Ma playlist"
3. Ajouter des contenus
4. Sauvegarder

### Planifier l'affichage

1. Cliquer sur **📅 Planning** sur un écran
2. Choisir une playlist
3. Définir Heure de début : 08:00
4. Définir Heure de fin : 18:00
5. Cliquer **Ajouter au Planning**

---

## 🔧 Commandes essentielles

```bash
# Accéder à la maintenance
sudo ds-maintenance

# Voir les logs
journalctl -u digital-signage -f

# Redémarrer le service
sudo systemctl restart digital-signage

# Connaître l'IP
hostname -I

# Redémarrer le Pi
sudo reboot
```

---

## ❓ Problèmes courants

### L'écran reste noir
```bash
sudo systemctl restart digital-signage
```

### Le wizard ne s'affiche pas
```bash
sudo ds-maintenance
# → Option 4 : Relancer le wizard
```

### Pas d'accès réseau
```bash
sudo ds-maintenance
# → Option 7 : Mode Debug
```

---

## 📚 Documentation complète

Voir `raspberry/README.md` pour la documentation détaillée.

---

**Temps total d'installation : ~15 minutes**
**Temps de configuration : ~5 minutes**
**Total : ~20 minutes pour être opérationnel !**
