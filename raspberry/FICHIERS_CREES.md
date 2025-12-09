# 📁 Fichiers créés pour le projet Raspberry Pi

## Structure complète

```
raspberry/
├── README.md                          # Documentation complète
├── QUICKSTART.md                      # Guide de démarrage rapide (5 min)
├── INSTALLATION.md                    # Procédure détaillée d'installation
├── FICHIERS_CREES.md                  # Ce fichier - Liste de tous les fichiers
│
├── install.sh                         # ⭐ Script d'installation principal
│
├── config/
│   └── device.conf                    # Configuration du dispositif (créée par install.sh)
│
├── scripts/
│   ├── startup.sh                     # ⭐ Script de démarrage automatique
│   ├── setup-ap.sh                    # Gestion du point d'accès WiFi
│   └── maintenance.sh                 # ⭐ Script de maintenance interactif
│
└── wizard/
    ├── wizard_server.py               # Serveur Flask du wizard
    ├── screen_info.html               # Page d'info au démarrage de l'écran
    └── templates/
        └── wizard.html                # Interface du wizard de configuration
```

---

## 📄 Description détaillée des fichiers

### 📚 Documentation (3 fichiers)

#### 1. `README.md` (Documentation complète)
- **Rôle** : Documentation principale exhaustive
- **Contenu** :
  - Prérequis matériel et logiciel
  - Guide de préparation du Raspberry Pi
  - Installation complète pas à pas
  - Configuration du wizard
  - Guide d'utilisation
  - Maintenance et dépannage
  - Structure des fichiers
  - Sécurité
  - Cas d'usage
  - Checklist d'installation
- **Quand l'utiliser** : Pour une compréhension complète du système

#### 2. `QUICKSTART.md` (Guide rapide)
- **Rôle** : Installation rapide en 5 minutes
- **Contenu** :
  - Installation en 5 étapes
  - Premiers pas
  - Commandes essentielles
  - Problèmes courants
- **Quand l'utiliser** : Pour une installation rapide si vous connaissez déjà les bases

#### 3. `INSTALLATION.md` (Procédure détaillée)
- **Rôle** : Guide d'installation étape par étape très détaillé
- **Contenu** :
  - Vue d'ensemble du fonctionnement
  - 7 parties détaillées de la préparation à l'utilisation
  - Captures d'écran des messages attendus
  - Checklist finale
- **Quand l'utiliser** : Pour une première installation ou si vous rencontrez des problèmes

---

### 🔧 Scripts d'installation et démarrage (2 fichiers)

#### 4. `install.sh` ⭐ (Script d'installation principal)
- **Rôle** : Installation automatisée du système
- **Exécution** : `sudo ./install.sh`
- **Actions** :
  1. Vérifie les permissions root
  2. Met à jour le système
  3. Installe les dépendances (Python, Chromium, outils réseau)
  4. Crée les répertoires dans `/opt/digital-signage`
  5. Copie tous les fichiers du projet
  6. Crée le fichier de configuration initiale
  7. Configure le service systemd
  8. Configure l'autostart X11 pour le mode kiosk
  9. Active le service
  10. Installe le script de maintenance
- **Sortie** : Messages colorés de progression
- **Durée** : 10-15 minutes
- **Utilisation** : Une seule fois lors de l'installation initiale

#### 5. `startup.sh` ⭐ (Script de démarrage)
- **Rôle** : Démarrage automatique du système
- **Exécution** : Automatique via systemd au boot
- **Logique** :
  ```
  SI non configuré :
    → Vérifier connexion réseau
    → SI réseau disponible :
        → Lancer wizard sur IP locale
    → SINON :
        → Créer point d'accès WiFi
        → Lancer wizard sur 192.168.4.1
    → Attendre fin du wizard
    → Redémarrer

  SINON (déjà configuré) :
    → SI rôle Contrôleur :
        → Démarrer Flask (gestion_raspberry.py)
    → SI rôle Player :
        → Afficher page d'info 10 secondes
        → Lancer Chromium en kiosk vers le contrôleur
  ```
- **Sortie** : Logs dans `/opt/digital-signage/logs/`
- **Utilisation** : À chaque démarrage du Raspberry Pi

---

### 📡 Scripts réseau et maintenance (2 fichiers)

#### 6. `setup-ap.sh` (Gestion point d'accès WiFi)
- **Rôle** : Créer/arrêter le point d'accès WiFi
- **Exécution** :
  ```bash
  sudo ./setup-ap.sh start   # Démarrer le point d'accès
  sudo ./setup-ap.sh stop    # Arrêter le point d'accès
  sudo ./setup-ap.sh restart # Redémarrer le point d'accès
  ```
- **Actions (start)** :
  1. Configure l'interface wlan0 avec IP 192.168.4.1
  2. Configure dnsmasq pour le DHCP (192.168.4.2-20)
  3. Configure hostapd avec le SSID et mot de passe
  4. Active le routage IP
  5. Démarre les services
- **Configuration** :
  - SSID : `DigitalSignage-Setup` (défini dans device.conf)
  - Password : `signage2024` (défini dans device.conf)
  - IP : 192.168.4.1
  - Plage DHCP : 192.168.4.2 → 192.168.4.20
- **Utilisation** : Automatique si pas de réseau au premier démarrage

#### 7. `maintenance.sh` ⭐ (Script de maintenance)
- **Rôle** : Menu interactif de maintenance
- **Exécution** : `sudo ds-maintenance` (commande globale installée)
- **Menu** :
  1. **Afficher la configuration** : Voir device.conf
  2. **Redémarrer le service** : Redémarre sans reboot
  3. **Voir les logs** :
     - Logs en direct
     - 50 dernières lignes
     - Logs d'erreur uniquement
  4. **Relancer le wizard** : Marque comme non configuré
  5. **Configuration manuelle** : Éditer les paramètres sans wizard
  6. **Factory Reset** : ⚠️ Supprime tout et réinitialise
  7. **Mode Debug** : État système complet
  8. **État du système** : Vue d'ensemble
  9. **Quitter**
- **Interface** : Menu coloré avec navigation
- **Utilisation** : Maintenance, dépannage, reconfiguration

---

### 🧙 Wizard de configuration (3 fichiers)

#### 8. `wizard_server.py` (Serveur du wizard)
- **Rôle** : Serveur Flask pour le wizard de première configuration
- **Port** : 8080
- **Endpoints** :
  - `GET /` : Page principale du wizard
  - `GET /api/config` : Récupérer la configuration actuelle
  - `POST /api/config` : Sauvegarder la configuration
  - `GET /api/network/scan` : Scanner les réseaux WiFi
  - `POST /api/network/connect` : Connecter à un réseau
- **Actions** :
  - Lit/écrit device.conf
  - Valide les données de configuration
  - Gère la connexion WiFi
- **Exécution** : Automatique par startup.sh
- **Arguments** :
  ```bash
  python3 wizard_server.py --port 8080 --ip 192.168.1.100
  ```

#### 9. `wizard.html` (Interface du wizard)
- **Rôle** : Interface web du wizard de configuration
- **Technologie** : HTML/CSS/JavaScript pur
- **Design** : Interface moderne avec animations
- **Étapes** :
  1. **Bienvenue** : Infos de connexion (SSID, IP)
  2. **Choix du rôle** : Contrôleur et/ou Player
  3. **Configuration Player** : ID, nom, emplacement, URL contrôleur
  4. **Récapitulatif** : Vérification avant sauvegarde
  5. **Terminé** : Confirmation et redémarrage
- **Validation** :
  - Au moins un rôle sélectionné
  - Champs obligatoires si Player
  - Feedback visuel
- **Responsive** : S'adapte à tous les écrans
- **Variables Jinja** :
  - `{{ ssid }}` : SSID du point d'accès
  - `{{ password }}` : Mot de passe du point d'accès
  - `{{ server_ip }}` : IP du serveur wizard

#### 10. `screen_info.html` (Page d'information écran)
- **Rôle** : Page affichée 10 secondes au démarrage d'un player
- **Technologie** : HTML/CSS/JavaScript pur
- **Design** : Plein écran avec dégradé violet
- **Informations affichées** :
  - 📌 ID de l'écran
  - 📺 Nom de l'écran
  - 📍 Emplacement
  - 🎮 URL du contrôleur
  - ⏳ Compte à rebours (10 → 0)
- **Paramètres URL** :
  ```
  ?id=ecran1
  &name=Écran%20Principal
  &location=RDC
  &controller=http://localhost:5000
  ```
- **Animation** : Compte à rebours animé
- **Durée** : 10 secondes puis Chromium recharge vers le contrôleur

---

### ⚙️ Configuration (1 fichier)

#### 11. `device.conf` (Configuration du dispositif)
- **Rôle** : Stocke la configuration du dispositif
- **Format** : Fichier shell source-able (KEY=VALUE)
- **Emplacement** : `/opt/digital-signage/raspberry/config/device.conf`
- **Création** : Automatique par install.sh
- **Modification** :
  - Via le wizard lors de la première configuration
  - Via le script de maintenance (option 5)
  - Manuellement (pour utilisateurs avancés)
- **Paramètres** :
  ```bash
  CONFIGURED=false              # true après configuration
  ROLE_CONTROLLER=false         # true si rôle contrôleur actif
  ROLE_PLAYER=false            # true si rôle player actif
  SCREEN_ID=""                 # ID unique de l'écran
  SCREEN_NAME=""               # Nom d'affichage
  SCREEN_LOCATION=""           # Emplacement physique
  CONTROLLER_URL=""            # URL du contrôleur
  WIFI_SSID=""                 # SSID du point d'accès
  WIFI_PASSWORD=""             # Mot de passe du point d'accès
  ```
- **Lecture** : Source dans les scripts bash
  ```bash
  source /opt/digital-signage/raspberry/config/device.conf
  echo $SCREEN_ID
  ```

---

## 🔄 Flux d'exécution

### Installation (une fois)

```
1. install.sh
   ├─> Installe dépendances
   ├─> Copie fichiers vers /opt/digital-signage
   ├─> Crée device.conf (CONFIGURED=false)
   ├─> Configure service systemd
   └─> Active service
```

### Premier démarrage

```
2. Systemd démarre digital-signage.service
   └─> Exécute startup.sh

3. startup.sh
   ├─> Lit device.conf
   ├─> Détecte CONFIGURED=false
   ├─> Vérifie réseau
   │
   SI réseau OK:
   ├─> Lance wizard_server.py sur IP locale
   └─> Ouvre Chromium en kiosk sur wizard
   │
   SI pas de réseau:
   ├─> Exécute setup-ap.sh start
   ├─> Lance wizard_server.py sur 192.168.4.1
   └─> Ouvre Chromium en kiosk sur wizard

4. Utilisateur configure via wizard.html
   └─> wizard_server.py sauvegarde dans device.conf

5. startup.sh détecte fin du wizard
   └─> Redémarre le système
```

### Démarrages suivants

```
6. Systemd démarre digital-signage.service
   └─> Exécute startup.sh

7. startup.sh
   ├─> Lit device.conf
   ├─> Détecte CONFIGURED=true
   │
   SI ROLE_CONTROLLER=true:
   └─> Lance gestion_raspberry.py (Flask)
   │
   SI ROLE_PLAYER=true:
   ├─> Ouvre Chromium sur screen_info.html (10s)
   └─> Ouvre Chromium en kiosk sur ${CONTROLLER_URL}/display
```

---

## 🎯 Fichiers à personnaliser

### Avant installation

1. **install.sh** (optionnel) :
   - Changer `USER="pi"` si autre utilisateur
   - Modifier `INSTALL_DIR` pour autre emplacement

### Après installation

1. **device.conf** :
   - Via le wizard (recommandé)
   - Via `sudo ds-maintenance` option 5
   - Manuellement si nécessaire

2. **wizard.html** (optionnel) :
   - Personnaliser les couleurs/logos
   - Modifier les textes d'aide

---

## 🛡️ Permissions des fichiers

```bash
# Scripts exécutables
chmod +x install.sh
chmod +x scripts/*.sh
chmod +x wizard/wizard_server.py

# Configuration lisible/modifiable
chmod 644 config/device.conf

# Documentation lisible
chmod 644 *.md
```

---

## 📊 Tailles approximatives

```
README.md          : ~25 KB
QUICKSTART.md      : ~5 KB
INSTALLATION.md    : ~20 KB
install.sh         : ~7 KB
startup.sh         : ~3 KB
setup-ap.sh        : ~2 KB
maintenance.sh     : ~8 KB
wizard_server.py   : ~4 KB
wizard.html        : ~15 KB
screen_info.html   : ~3 KB
device.conf        : <1 KB

TOTAL              : ~92 KB
```

---

## ✅ Checklist de vérification

Après création de tous les fichiers :

- [ ] Tous les fichiers `.sh` sont exécutables
- [ ] Tous les fichiers `.py` sont exécutables
- [ ] La structure de dossiers est complète
- [ ] Les documentations sont cohérentes
- [ ] Les chemins dans les scripts sont corrects
- [ ] Les variables sont bien définies
- [ ] Les services systemd sont correctement configurés

---

**Total : 11 fichiers créés**

**Documentation : 3 fichiers**
**Scripts : 5 fichiers**
**Wizard : 3 fichiers**
**Configuration : 1 fichier (généré)**
