# Digital Signage pour Raspberry Pi 3

## Documentation complète d'installation et de configuration

---

## 📋 Table des matières

1. [Prérequis](#prérequis)
2. [Préparation du Raspberry Pi](#préparation-du-raspberry-pi)
3. [Installation du système](#installation-du-système)
4. [Premier démarrage et configuration](#premier-démarrage-et-configuration)
5. [Utilisation](#utilisation)
6. [Maintenance](#maintenance)
7. [Dépannage](#dépannage)

---

## 🔧 Prérequis

### Matériel requis

- **Raspberry Pi 3 Model B ou B+**
- Carte microSD de **minimum 16 GB** (Classe 10 recommandée)
- Alimentation 5V/2.5A
- Câble HDMI
- Écran/TV avec entrée HDMI
- Clavier USB (pour la première installation)
- Connexion Internet (WiFi ou Ethernet)

### Logiciels requis (pour la préparation)

- [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
- Un ordinateur pour préparer la carte SD

---

## 📱 Préparation du Raspberry Pi

### Étape 1 : Installation de Raspberry Pi OS

1. **Télécharger Raspberry Pi Imager** sur votre ordinateur

2. **Insérer la carte microSD** dans votre ordinateur

3. **Lancer Raspberry Pi Imager** et :
   - Choisir l'OS : **Raspberry Pi OS (32-bit) with desktop** ou **Raspberry Pi OS (64-bit) with desktop**
     > 💡 Les deux versions fonctionnent parfaitement. Le 64-bit offre de légères performances supplémentaires.
   - Choisir la carte SD
   - Cliquer sur l'icône ⚙️ (paramètres avancés)

4. **Configurer les options avancées** :
   ```
   ✅ Activer SSH
   ✅ Définir un nom d'utilisateur : pi
   ✅ Définir un mot de passe : [votre mot de passe]
   ✅ Configurer le WiFi (si disponible)
   ✅ Définir le fuseau horaire
   ✅ Activer le clavier en français
   ```

5. **Écrire** l'image sur la carte SD

6. **Insérer la carte SD** dans le Raspberry Pi

### Étape 2 : Premier démarrage du Raspberry Pi

1. **Connecter** :
   - Écran HDMI
   - Clavier USB
   - Alimentation

2. **Attendre** que le système démarre (2-3 minutes)

3. **Se connecter** avec les identifiants configurés :
   - Utilisateur : `pi`
   - Mot de passe : [celui que vous avez défini]

4. **Mettre à jour le système** :
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

5. **Configurer le système** :
   ```bash
   sudo raspi-config
   ```

   Dans le menu :
   - **Display Options** → **Screen Blanking** → **No** (désactiver la mise en veille)
   - **Boot Options** → **Desktop / CLI** → **Desktop Autologin** (connexion automatique)
   - **Finish** et redémarrer

---

## 💿 Installation du système Digital Signage

### Étape 1 : Télécharger le projet

```bash
cd ~
git clone https://github.com/votre-repo/digital-signage.git DS
cd DS
```

> **Note :** Si vous n'avez pas Git, installez-le :
> ```bash
> sudo apt install git -y
> ```

### Étape 2 : Rendre le script d'installation exécutable

```bash
chmod +x raspberry/install.sh
```

### Étape 3 : Lancer l'installation

```bash
cd raspberry
sudo ./install.sh
```

Le script va :
- ✅ Mettre à jour le système
- ✅ Installer toutes les dépendances
- ✅ Configurer les services
- ✅ Préparer l'environnement

**Durée estimée : 10-15 minutes**

### Étape 4 : Redémarrer

```bash
sudo reboot
```

---

## 🚀 Premier démarrage et configuration

### Scénario 1 : Avec connexion réseau

Au redémarrage, le système va :

1. **Détecter la connexion réseau**
2. **Afficher automatiquement** le wizard de configuration en plein écran
3. **Afficher les informations de connexion** :
   - Adresse IP du dispositif
   - Instructions pour accéder au wizard

**Page affichée :**
```
╔═══════════════════════════════════════╗
║  Configuration Digital Signage        ║
╚═══════════════════════════════════════╝

🌐 Connexion réseau détectée

📍 Accédez au wizard sur :
   http://192.168.1.XXX:8080

Depuis un autre appareil connecté au même réseau
```

### Scénario 2 : Sans connexion réseau

Au redémarrage, le système va :

1. **Détecter l'absence de réseau**
2. **Créer automatiquement un point d'accès WiFi**
3. **Afficher les informations de connexion** :

**Page affichée :**
```
╔═══════════════════════════════════════╗
║  Configuration Digital Signage        ║
╚═══════════════════════════════════════╝

📶 Point d'accès WiFi créé

Connectez-vous au réseau :
   SSID     : DigitalSignage-Setup
   Password : signage2024

Puis accédez à :
   http://192.168.4.1:8080
```

### Configuration via le Wizard

Le wizard vous guide à travers 4 étapes :

#### **Étape 1 : Bienvenue**
- Informations de connexion affichées
- Cliquer sur **Suivant**

#### **Étape 2 : Choix du rôle**

Sélectionnez un ou plusieurs rôles :

**Option A : Contrôleur uniquement**
- ✅ Interface de gestion des écrans
- ❌ Pas d'affichage de contenu
- 💡 Utilisation : Serveur central de gestion

**Option B : Player uniquement**
- ❌ Pas d'interface de gestion
- ✅ Affichage du contenu
- 💡 Utilisation : Écran d'affichage simple

**Option C : Contrôleur + Player** _(Recommandé pour un setup simple)_
- ✅ Interface de gestion
- ✅ Affichage du contenu
- 💡 Utilisation : Dispositif autonome

#### **Étape 3 : Configuration Player** _(uniquement si Player sélectionné)_

Remplir les informations :

| Champ | Description | Exemple |
|-------|-------------|---------|
| **ID unique** | Identifiant technique | `ecran1`, `salon`, `reception` |
| **Nom** | Nom d'affichage | `Écran Principal`, `Salle d'attente` |
| **Emplacement** | Lieu physique | `RDC`, `Étage 1`, `Accueil` |
| **URL Contrôleur** | Adresse du serveur | `http://localhost:5000` (si contrôleur local)<br>`http://192.168.1.100:5000` (si contrôleur distant) |

#### **Étape 4 : Récapitulatif**
- Vérifier la configuration
- Cliquer sur **Terminer**

### Après la configuration

Le système va :
1. ✅ Sauvegarder la configuration
2. 🔄 Redémarrer automatiquement
3. 🚀 Démarrer en mode normal

---

## 📺 Utilisation

### Mode Player

Au démarrage, l'écran affiche pendant **10 secondes** :

```
╔═══════════════════════════════════════╗
║     🖥️ Digital Signage                ║
╚═══════════════════════════════════════╝

📌 ID Écran    : ecran1
📺 Nom         : Écran Principal
📍 Emplacement : RDC
🎮 Contrôleur  : http://localhost:5000

⏳ Démarrage dans 10 secondes...
```

Puis le navigateur se connecte automatiquement au contrôleur et commence l'affichage.

### Mode Contrôleur

Accéder à l'interface de gestion :

**Depuis le Raspberry Pi lui-même :**
```
http://localhost:5000
```

**Depuis un autre appareil sur le réseau :**
```
http://[IP-DU-RASPBERRY]:5000
```

Pour connaître l'IP du Raspberry Pi :
```bash
hostname -I
```

---

## 🔧 Maintenance

### Script de maintenance interactif

Accéder au menu de maintenance :

```bash
sudo ds-maintenance
```

### Options disponibles

#### 1. Afficher la configuration actuelle
- Visualiser tous les paramètres du système

#### 2. Redémarrer le service
- Redémarrer Digital Signage sans redémarrer le Pi

#### 3. Voir les logs
- **Logs en direct** : Surveillance en temps réel
- **50 dernières lignes** : Historique récent
- **Logs d'erreur** : Uniquement les erreurs

#### 4. Relancer le wizard
- Réinitialiser la configuration
- Relancer le wizard au prochain démarrage

#### 5. Configuration manuelle
- Modifier directement les paramètres sans wizard
- Pour utilisateurs avancés

#### 6. Factory Reset
- ⚠️ **ATTENTION : Action irréversible**
- Supprime toutes les données
- Réinitialise aux paramètres d'usine

#### 7. Mode Debug
- Affiche l'état complet du système :
  - État du service
  - Connexion réseau
  - Espace disque
  - Température CPU
  - Derniers logs

#### 8. État du système
- Vue d'ensemble du statut
- Processus actifs
- Connectivité

---

## 🛠️ Dépannage

### Le wizard ne s'affiche pas

**Vérifier l'état du service :**
```bash
sudo systemctl status digital-signage
```

**Voir les logs :**
```bash
sudo ds-maintenance
# Puis option 3 : Voir les logs
```

**Forcer le relancement du wizard :**
```bash
sudo ds-maintenance
# Puis option 4 : Relancer le wizard
```

### L'écran reste noir

**Vérifier Chromium :**
```bash
ps aux | grep chromium
```

**Redémarrer le service :**
```bash
sudo systemctl restart digital-signage
```

### Pas de connexion au contrôleur

**Vérifier la connexion réseau :**
```bash
ping -c 4 [IP-DU-CONTROLEUR]
```

**Vérifier l'URL du contrôleur :**
```bash
sudo ds-maintenance
# Option 1 : Afficher la configuration
```

**Corriger l'URL si nécessaire :**
```bash
sudo ds-maintenance
# Option 5 : Configuration manuelle
```

### Le WiFi ne fonctionne pas

**Scanner les réseaux :**
```bash
sudo iwlist wlan0 scan | grep ESSID
```

**Vérifier wpa_supplicant :**
```bash
cat /etc/wpa_supplicant/wpa_supplicant.conf
```

**Reconfigurer le WiFi :**
```bash
sudo raspi-config
# System Options → Wireless LAN
```

### Température élevée

**Vérifier la température :**
```bash
vcgencmd measure_temp
```

**Solutions :**
- Ajouter un dissipateur thermique
- Améliorer la ventilation
- Utiliser un boîtier avec ventilateur

### Logs pour diagnostic

**Logs du service :**
```bash
journalctl -u digital-signage -n 100
```

**Logs applicatifs :**
```bash
tail -f /opt/digital-signage/logs/service.log
tail -f /opt/digital-signage/logs/service-error.log
```

---

## 📂 Structure des fichiers

```
/opt/digital-signage/
├── gestion_raspberry.py          # Application Flask principale
├── templates/                    # Templates HTML
│   ├── manager.html
│   └── display.html
├── static/                       # Fichiers statiques
│   └── css/
├── data/                         # Données persistantes
│   ├── screens.json
│   ├── content.json
│   ├── playlists.json
│   └── schedules.json
├── logs/                         # Logs
│   ├── service.log
│   └── service-error.log
└── raspberry/                    # Scripts Raspberry Pi
    ├── config/
    │   └── device.conf           # Configuration du dispositif
    ├── scripts/
    │   ├── startup.sh            # Script de démarrage
    │   ├── setup-ap.sh           # Gestion WiFi AP
    │   └── maintenance.sh        # Script de maintenance
    └── wizard/
        ├── wizard_server.py      # Serveur du wizard
        ├── templates/
        │   └── wizard.html       # Interface du wizard
        └── screen_info.html      # Page d'info au démarrage
```

---

## 🔐 Sécurité

### Mots de passe par défaut

⚠️ **À changer en production !**

- **WiFi AP** :
  - SSID : `DigitalSignage-Setup`
  - Password : `signage2024`

- **Utilisateur Pi** :
  - User : `pi`
  - Password : [défini lors de l'installation]

### Recommandations

1. **Changer les mots de passe par défaut**
2. **Désactiver SSH** si non utilisé
3. **Mettre à jour régulièrement** le système
4. **Utiliser un réseau WiFi sécurisé**

---

## 📞 Support

### Fichiers de configuration

**Configuration du dispositif :**
```bash
/opt/digital-signage/raspberry/config/device.conf
```

**Service systemd :**
```bash
/etc/systemd/system/digital-signage.service
```

### Commandes utiles

```bash
# Voir le statut du service
sudo systemctl status digital-signage

# Redémarrer le service
sudo systemctl restart digital-signage

# Voir les logs en direct
journalctl -u digital-signage -f

# Accéder à la maintenance
sudo ds-maintenance

# Redémarrer le Raspberry Pi
sudo reboot

# Éteindre le Raspberry Pi
sudo shutdown -h now
```

---

## 📝 Notes importantes

- ✅ Le système démarre **automatiquement** au boot
- ✅ Le mode kiosk est **toujours actif** (plein écran)
- ✅ Pas besoin de clavier/souris après configuration
- ✅ Le wizard ne s'affiche qu'au **premier lancement**
- ✅ Les configurations sont **persistantes** après redémarrage

---

## 🎯 Cas d'usage typiques

### Configuration 1 : Un seul Raspberry Pi autonome

**Rôle :** Contrôleur + Player

1. Installer le système
2. Configurer en mode Contrôleur + Player
3. Gérer le contenu via http://localhost:5000
4. L'écran affiche automatiquement le contenu

### Configuration 2 : Un contrôleur central + plusieurs players

**Contrôleur (Raspberry Pi 1) :**
- Rôle : Contrôleur uniquement
- IP fixe recommandée : ex. 192.168.1.100

**Players (Raspberry Pi 2, 3, 4...) :**
- Rôle : Player uniquement
- URL contrôleur : http://192.168.1.100:5000
- Chaque player a son ID unique

### Configuration 3 : Plusieurs zones indépendantes

Chaque zone a son propre Raspberry Pi en mode Contrôleur + Player :
- Zone 1 : Accueil
- Zone 2 : Salle d'attente
- Zone 3 : Restaurant

---

## ✅ Checklist d'installation

- [ ] Raspberry Pi OS installé et à jour
- [ ] Script d'installation exécuté
- [ ] Système redémarré
- [ ] Wizard de configuration complété
- [ ] Écran affiche correctement
- [ ] Interface de gestion accessible
- [ ] Contenu de test ajouté
- [ ] Playlist créée et testée
- [ ] Connexion réseau stable
- [ ] Mots de passe changés

---

**Version :** 1.0
**Date :** Décembre 2024
**Compatibilité :** Raspberry Pi 3 Model B/B+
