# 📋 PROCÉDURE COMPLÈTE - DIGITAL SIGNAGE RASPBERRY PI 3

## ⚡ VUE D'ENSEMBLE EN 3 PHASES

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: PRÉPARATION (20 min)                                  │
│ → Installer Raspberry Pi OS sur carte SD                       │
│ → Premier boot + configuration initiale                         │
├─────────────────────────────────────────────────────────────────┤
│ PHASE 2: INSTALLATION (15 min)                                 │
│ → Télécharger le projet                                        │
│ → Exécuter install.sh                                          │
│ → Redémarrer                                                    │
├─────────────────────────────────────────────────────────────────┤
│ PHASE 3: CONFIGURATION (5 min)                                 │
│ → Wizard s'affiche automatiquement                             │
│ → Choisir le(s) rôle(s)                                        │
│ → Configurer les paramètres                                    │
│ → C'EST FINI !                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔥 INSTALLATION EXPRESS

### 1️⃣ Préparer la carte SD (PC)

```bash
# Utiliser Raspberry Pi Imager
# → OS: Raspberry Pi OS (32 ou 64-bit) with desktop
#   💡 Les deux versions fonctionnent parfaitement
# → Paramètres avancés (⚙️):
#   ✅ Activer SSH
#   ✅ User: pi, Password: [choisir]
#   ✅ WiFi: [configurer si disponible]
#   ✅ Locale: FR, Europe/Paris
```

### 2️⃣ Premier boot (Raspberry Pi)

```bash
# Connecter écran + clavier + alimentation

# Mettre à jour
sudo apt update && sudo apt upgrade -y

# Configurer
sudo raspi-config
# → Boot Options → Desktop Autologin
# → Display Options → Screen Blanking → No
# → Finish → Reboot
```

### 3️⃣ Installer Digital Signage

```bash
cd ~
git clone [URL_REPO] DS
cd DS
chmod +x raspberry/install.sh
sudo raspberry/install.sh
sudo reboot
```

### 4️⃣ Configuration automatique

**Le wizard s'affiche automatiquement !**

- Avec réseau → Affiche l'IP pour accéder
- Sans réseau → Crée WiFi "DigitalSignage-Setup" (mdp: signage2024)

**Suivre le wizard :**
1. Choisir rôle(s) : Contrôleur / Player
2. Si Player : ID, Nom, Emplacement, URL contrôleur
3. Valider → Redémarrage automatique

**✅ C'EST FINI !**

---

## 📂 FICHIERS CRÉÉS

```
raspberry/
├── 📚 Documentation
│   ├── README.md              # Doc complète
│   ├── QUICKSTART.md          # Guide 5 min
│   ├── INSTALLATION.md        # Procédure détaillée
│   └── FICHIERS_CREES.md      # Liste des fichiers
│
├── ⭐ Scripts principaux
│   ├── install.sh             # Installation
│   └── scripts/
│       ├── startup.sh         # Démarrage auto
│       ├── setup-ap.sh        # WiFi AP
│       ├── maintenance.sh     # Maintenance
│       └── verify-install.sh  # Vérification
│
└── 🧙 Wizard
    ├── wizard_server.py       # Serveur config
    ├── screen_info.html       # Page info écran
    └── templates/
        └── wizard.html        # Interface wizard
```

---

## 🎯 CONFIGURATIONS TYPES

### Option A : Pi autonome (1 seul Pi)
```
Rôles : ✅ Contrôleur + ✅ Player
Usage : Gère et affiche sur le même Pi
Config : URL contrôleur = http://localhost:5000
```

### Option B : Serveur central (1 Pi central)
```
Rôles : ✅ Contrôleur
Usage : Gère plusieurs écrans distants
Config : Rien de spécial
```

### Option C : Écran distant (plusieurs Pi)
```
Rôles : ✅ Player
Usage : Affiche le contenu
Config : URL contrôleur = http://[IP_SERVEUR]:5000
        ID unique pour chaque Pi
```

---

## 🔧 COMMANDES ESSENTIELLES

```bash
# Menu de maintenance (PRINCIPAL)
sudo ds-maintenance

# État du service
sudo systemctl status digital-signage

# Redémarrer le service
sudo systemctl restart digital-signage

# Voir logs en direct
journalctl -u digital-signage -f

# Voir logs fichiers
tail -f /opt/digital-signage/logs/service.log

# IP du Pi
hostname -I

# Vérifier l'installation
cd ~/DS/raspberry/scripts
./verify-install.sh

# Redémarrer le Pi
sudo reboot

# Arrêter le Pi
sudo shutdown -h now
```

---

## 🛠️ DÉPANNAGE EXPRESS

| Problème | Solution |
|----------|----------|
| Wizard ne s'affiche pas | `sudo ds-maintenance` → Option 4 |
| Écran noir | `sudo systemctl restart digital-signage` |
| Pas de réseau | `sudo ds-maintenance` → Option 7 (Debug) |
| Erreur service | `journalctl -u digital-signage -n 50` |
| Reconfigurer | `sudo ds-maintenance` → Option 4 ou 5 |
| Factory reset | `sudo ds-maintenance` → Option 6 ⚠️ |

---

## 📍 EMPLACEMENTS IMPORTANTS

```
# Installation
/opt/digital-signage/              # Dossier principal

# Configuration
/opt/digital-signage/raspberry/config/device.conf

# Logs
/opt/digital-signage/logs/service.log
/opt/digital-signage/logs/service-error.log

# Service
/etc/systemd/system/digital-signage.service

# Données
/opt/digital-signage/data/screens.json
/opt/digital-signage/data/content.json
/opt/digital-signage/data/playlists.json
/opt/digital-signage/data/schedules.json
```

---

## 🚀 PREMIERS PAS APRÈS INSTALLATION

### 1. Accéder à l'interface

```
http://[IP_DU_PI]:5000
```

### 2. Ajouter un contenu

```
Section "Bibliothèque" → + Ajouter
→ Nom: "Test"
→ Type: Page Web
→ URL: https://www.google.com
→ Durée: 00:00:30
→ Sauvegarder
```

### 3. Créer une playlist

```
Section "Playlists" → + Ajouter
→ Nom: "Ma playlist"
→ Ajouter "Test"
→ Sauvegarder
```

### 4. Planifier

```
Cliquer sur écran → 📅 Planning
→ Playlist: "Ma playlist"
→ Début: 00:00
→ Fin: 23:59
→ Ajouter au Planning
```

**L'écran affiche maintenant le contenu ! 🎉**

---

## ⏱️ TEMPS ESTIMÉS

| Phase | Durée |
|-------|-------|
| Préparation carte SD | 15 min |
| Premier boot + config | 10 min |
| Installation DS | 15 min |
| Configuration wizard | 5 min |
| **TOTAL** | **~45 min** |

---

## ✅ CHECKLIST RAPIDE

```
□ Carte SD préparée avec Raspberry Pi OS
□ Raspberry Pi démarre et se connecte
□ raspi-config: Autologin + No screen blanking
□ Projet téléchargé dans ~/DS
□ install.sh exécuté avec succès
□ Système redémarré
□ Wizard complété
□ Service actif: systemctl status digital-signage
□ Interface accessible: http://[IP]:5000
□ Contenu test créé et affiché
```

---

## 📞 SUPPORT

### Documentation

- **Guide rapide** : `raspberry/QUICKSTART.md`
- **Installation détaillée** : `raspberry/INSTALLATION.md`
- **Documentation complète** : `raspberry/README.md`
- **Liste des fichiers** : `raspberry/FICHIERS_CREES.md`

### Outils

```bash
# Maintenance interactive
sudo ds-maintenance

# Vérifier l'installation
./raspberry/scripts/verify-install.sh
```

---

## 🎯 POINTS CLÉS À RETENIR

1. ✅ **Premier lancement = Wizard automatique**
   - Avec réseau : note l'IP affichée
   - Sans réseau : connecte-toi au WiFi "DigitalSignage-Setup"

2. ✅ **Démarrage automatique au boot**
   - Pas besoin de clavier/souris après config
   - Mode kiosk plein écran

3. ✅ **Maintenance facile**
   - Une seule commande : `sudo ds-maintenance`
   - Menu interactif pour tout faire

4. ✅ **Mode Player affiche les infos 10 secondes**
   - Avant de se connecter au contrôleur
   - Utile pour déboguer

5. ✅ **Logs accessibles**
   - Temps réel : `journalctl -u digital-signage -f`
   - Fichiers : `/opt/digital-signage/logs/`

---

## 🎊 SUCCÈS !

**Votre système Digital Signage est maintenant opérationnel !**

```
┌─────────────────────────────────────────┐
│  📺 Écran(s) connecté(s) et fonctionnel │
│  🎮 Interface de gestion accessible     │
│  📋 Playlists et plannings actifs       │
│  🚀 Démarrage automatique configuré     │
│  ✅ SYSTÈME OPÉRATIONNEL                │
└─────────────────────────────────────────┘
```

**Temps total : ~45 minutes**
**Prochaine étape : Ajouter du contenu et créer des playlists !**

---

**Version :** 1.0
**Date :** Décembre 2024
**Compatible :** Raspberry Pi 3 Model B/B+
