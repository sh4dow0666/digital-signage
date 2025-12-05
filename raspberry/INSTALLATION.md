# 📦 Procédure complète d'installation

## Vue d'ensemble

Ce document décrit la procédure **complète et détaillée** pour installer et configurer le système Digital Signage sur un Raspberry Pi 3.

---

## 🎯 Résumé du fonctionnement

### Au premier démarrage

1. **Le système détecte qu'il n'est pas configuré**
2. **Deux cas possibles :**
   - ✅ **Réseau disponible** → Affiche l'IP pour accéder au wizard
   - ❌ **Pas de réseau** → Crée un point d'accès WiFi automatiquement

3. **Le wizard s'affiche en plein écran** sur le Raspberry Pi
4. **L'utilisateur configure** :
   - Les rôles du dispositif (Contrôleur/Player)
   - Les paramètres d'écran si mode Player
   - L'URL du contrôleur si nécessaire

5. **Après configuration** : Le système redémarre et fonctionne normalement

### Aux démarrages suivants

- ✅ Pas de wizard (déjà configuré)
- 🚀 Démarrage automatique des services
- 📺 Si Player : Affiche les infos d'écran pendant 10s puis connecte au contrôleur
- 🎮 Si Contrôleur : Démarre le serveur Flask

---

## 📋 PARTIE 1 : Préparation (20 min)

### Étape 1.1 : Matériel nécessaire

- [ ] Raspberry Pi 3 Model B ou B+
- [ ] Carte microSD 16GB+ (Classe 10)
- [ ] Alimentation 5V/2.5A
- [ ] Câble HDMI
- [ ] Écran/TV
- [ ] Clavier USB (temporaire)
- [ ] Accès Internet

### Étape 1.2 : Préparer la carte SD

**Sur votre ordinateur :**

1. Télécharger [Raspberry Pi Imager](https://www.raspberrypi.com/software/)

2. Lancer Raspberry Pi Imager

3. **Choisir l'OS** :
   ```
   Raspberry Pi OS (other)
   → Raspberry Pi OS (32-bit) with desktop
   ou
   → Raspberry Pi OS (64-bit) with desktop

   💡 Les deux versions fonctionnent parfaitement.
      Le 64-bit offre de légères performances supplémentaires.
   ```

4. **Choisir la carte SD**

5. **Cliquer sur l'icône ⚙️** (paramètres) :

   ```
   ✅ Set hostname: raspberrypi
   ✅ Enable SSH
      ☑ Use password authentication
   ✅ Set username and password
      Username: pi
      Password: [votre-mot-de-passe]
   ✅ Configure wireless LAN (si WiFi disponible)
      SSID: [votre-wifi]
      Password: [mot-de-passe-wifi]
      Wireless LAN country: FR
   ✅ Set locale settings
      Time zone: Europe/Paris
      Keyboard layout: fr
   ```

6. Cliquer **SAVE** puis **WRITE**

7. Attendre la fin de l'écriture (~10 min)

### Étape 1.3 : Démarrage initial du Raspberry Pi

1. **Insérer la carte SD** dans le Raspberry Pi

2. **Connecter** :
   - Écran HDMI
   - Clavier USB
   - Câble réseau Ethernet (recommandé pour l'installation)
   - Alimentation (en dernier)

3. **Attendre le démarrage** (2-3 minutes)

4. **Connexion automatique** (si configurée dans Imager)

### Étape 1.4 : Configuration initiale du Raspberry Pi

**Dans le terminal du Raspberry Pi :**

```bash
# Mettre à jour le système
sudo apt update
sudo apt upgrade -y
```

**⏱ Durée : 5-10 minutes**

```bash
# Configurer le système
sudo raspi-config
```

**Dans le menu raspi-config :**

1. **Display Options** → **Screen Blanking** → **No**
   - Désactive la mise en veille de l'écran

2. **Boot Options** → **Desktop / CLI** → **Desktop Autologin**
   - Active la connexion automatique au démarrage

3. **System Options** → **Boot / Auto Login** → **Desktop Autologin**
   - Confirme le login automatique

4. **Localisation Options** → **WLAN Country**
   - Renseigner le pays pour le wifi

5. **Finish** → **Yes** pour redémarrer

---

## 📥 PARTIE 2 : Installation Digital Signage (15 min)

### Étape 2.1 : Télécharger le projet

```bash
# Se placer dans le dossier home
cd ~

# Cloner le projet (si sur Git)
git clone https://github.com/votre-repo/digital-signage.git DS

# OU copier les fichiers depuis une clé USB
# cp -r /media/usb/digital-signage ~/DS
```

**Si Git n'est pas installé :**
```bash
sudo apt install git -y
```

### Étape 2.2 : Vérifier les fichiers

```bash
cd ~/DS
ls -la
```

**Vous devez voir :**
```
- gestion_raspberry.py
- templates/
- static/
- raspberry/
  - install.sh
  - scripts/
  - wizard/
  - config/
```

### Étape 2.3 : Lancer l'installation

```bash
# Rendre le script exécutable
chmod +x raspberry/install.sh

# Lancer l'installation (NÉCESSITE SUDO)
cd raspberry
sudo ./install.sh
```

**Ce que fait le script :**

1. ✅ Vérifie les permissions root
2. ✅ Met à jour le système
3. ✅ Installe les dépendances :
   - Python3 et pip
   - Chromium browser
   - Outils réseau (hostapd, dnsmasq)
   - Bibliothèques Python (Flask, Flask-SocketIO)
4. ✅ Copie les fichiers dans `/opt/digital-signage`
5. ✅ Crée le fichier de configuration
6. ✅ Configure le service systemd
7. ✅ Configure l'autostart X11
8. ✅ Active le service

**⏱ Durée : 10-15 minutes**

**Sortie attendue :**
```
╔════════════════════════════════════════════════════════════╗
║  Installation Digital Signage pour Raspberry Pi 3         ║
╚════════════════════════════════════════════════════════════╝

📦 Mise à jour du système...
✅ Fait

📦 Installation des dépendances...
✅ Fait

📁 Création du répertoire d'installation...
✅ Fait

... [autres étapes]

╔════════════════════════════════════════════════════════════╗
║  ✅ Installation terminée avec succès !                    ║
╚════════════════════════════════════════════════════════════╝
```

### Étape 2.4 : Redémarrer

```bash
sudo reboot
```

---

## ⚙️ PARTIE 3 : Configuration (5 min)

### Au redémarrage...

**Le Raspberry Pi va automatiquement :**

1. Démarrer le service Digital Signage
2. Détecter qu'il n'est pas configuré
3. Lancer le wizard de configuration

### Cas A : Réseau disponible

**L'écran affiche :**

```
╔═══════════════════════════════════════════════╗
║   Configuration Digital Signage               ║
╚═══════════════════════════════════════════════╝

🌐 Connexion réseau détectée

📍 Accédez au wizard :
   http://192.168.1.XXX:8080

   (Remplacer XXX par l'IP affichée)
```

**Le wizard s'ouvre AUTOMATIQUEMENT en plein écran sur le Pi**

### Cas B : Pas de réseau

**L'écran affiche :**

```
╔═══════════════════════════════════════════════╗
║   Configuration Digital Signage               ║
╚═══════════════════════════════════════════════╝

📶 Point d'accès WiFi créé

Connectez-vous au réseau :
   SSID     : DigitalSignage-Setup
   Password : signage2024

Puis accédez à :
   http://192.168.4.1:8080
```

**Actions :**
1. Se connecter au WiFi avec un smartphone/ordinateur
2. Ouvrir le navigateur sur `http://192.168.4.1:8080`
3. Suivre le wizard

---

## 🧙 PARTIE 4 : Wizard de configuration

### Écran 1 : Bienvenue

- Lecture des informations
- Clic sur **Suivant**

### Écran 2 : Choix du rôle

**Sélectionner un ou plusieurs rôles :**

#### ✅ Rôle Contrôleur
- Interface web de gestion des écrans
- Accessible sur le port 5000
- Peut gérer plusieurs players

#### ✅ Rôle Player
- Affichage du contenu en plein écran
- Se connecte à un contrôleur
- Nécessite une configuration supplémentaire

**Exemples de configuration :**

| Cas d'usage | Contrôleur | Player | Description |
|-------------|-----------|--------|-------------|
| **Setup simple** | ✅ | ✅ | Un seul Pi qui gère et affiche |
| **Serveur central** | ✅ | ❌ | Pi qui gère uniquement |
| **Écran distant** | ❌ | ✅ | Pi qui affiche uniquement |

### Écran 3 : Configuration Player (si Player activé)

**Remplir les champs :**

#### ID unique de l'écran *
```
Exemple : ecran1, salon, accueil, etage2
```
- Identifiant technique unique
- Lettres, chiffres, tirets uniquement
- Pas d'espaces

#### Nom de l'écran *
```
Exemple : Écran Principal, Salle d'attente, Réception
```
- Nom d'affichage convivial
- Visible dans l'interface de gestion

#### Emplacement
```
Exemple : RDC, Étage 1, Bâtiment A
```
- Localisation physique
- Optionnel mais recommandé

#### Adresse du contrôleur *
```
Si contrôleur sur le même Pi : http://localhost:5000
Si contrôleur distant : http://192.168.1.100:5000
```

**💡 Astuce :** Si vous avez coché "Contrôleur", l'URL est pré-remplie avec `localhost`

### Écran 4 : Récapitulatif

- Vérifier toutes les informations
- Corriger si nécessaire avec **Précédent**
- Cliquer sur **Terminer**

### Écran 5 : Terminé !

```
Configuration enregistrée ✅
Redémarrage dans 3 secondes...
```

Le système redémarre automatiquement.

---

## 🚀 PARTIE 5 : Premier lancement

### Au démarrage (après configuration)

#### Si mode Player activé

**L'écran affiche pendant 10 secondes :**

```
╔═══════════════════════════════════════════════╗
║        🖥️ Digital Signage                     ║
╚═══════════════════════════════════════════════╝

📌 ID Écran    : ecran1
📺 Nom         : Écran Principal
📍 Emplacement : RDC
🎮 Contrôleur  : http://localhost:5000

⏳ Démarrage dans 10 secondes...
```

**Puis :**
- Le navigateur se connecte au contrôleur
- L'écran affiche "En attente de contenu" jusqu'à ce qu'un contenu soit assigné

#### Si mode Contrôleur activé

**Le serveur Flask démarre :**
- Interface accessible sur `http://[IP-DU-PI]:5000`
- Logs visibles dans `/opt/digital-signage/logs/`

---

## ✅ PARTIE 6 : Vérification

### Vérifier que tout fonctionne

```bash
# Vérifier le statut du service
sudo systemctl status digital-signage

# Doit afficher :
● digital-signage.service - Digital Signage Service
   Loaded: loaded
   Active: active (running)
```

### Accéder à l'interface de gestion

**Depuis le Pi lui-même :**
```
http://localhost:5000
```

**Depuis un autre appareil :**
```bash
# Trouver l'IP du Pi
hostname -I
# Affiche : 192.168.1.XXX

# Puis accéder à :
http://192.168.1.XXX:5000
```

### Voir les logs

```bash
# Logs du service
journalctl -u digital-signage -n 50

# Logs applicatifs
tail -f /opt/digital-signage/logs/service.log
```

---

## 🎯 PARTIE 7 : Premiers contenus (optionnel)

### Ajouter un contenu

1. Aller sur `http://[IP]:5000`
2. Section **Bibliothèque** → **+ Ajouter**
3. Remplir :
   - Nom : "Test Google"
   - Type : Page Web (URL)
   - URL : https://www.google.com
   - Durée : 00:00:30
4. **Sauvegarder**

### Créer une playlist

1. Section **Playlists** → **+ Ajouter**
2. Nom : "Playlist Test"
3. Ajouter le contenu "Test Google"
4. **Sauvegarder la Playlist**

### Planifier sur un écran

1. Cliquer sur **📅 Planning** sur un écran
2. Choisir "Playlist Test"
3. Heure de début : 00:00
4. Heure de fin : 23:59
5. **Ajouter au Planning**

**L'écran affiche maintenant le contenu !**

---

## 📞 Support et dépannage

### Commandes utiles

```bash
# Menu de maintenance
sudo ds-maintenance

# Redémarrer le service
sudo systemctl restart digital-signage

# Voir les logs en direct
journalctl -u digital-signage -f

# Connaître l'IP
hostname -I

# Redémarrer le Pi
sudo reboot
```

### En cas de problème

**Le wizard ne s'affiche pas :**
```bash
sudo ds-maintenance
# → Option 4 : Relancer le wizard
```

**L'écran reste noir :**
```bash
sudo systemctl restart digital-signage
```

**Erreur réseau :**
```bash
sudo ds-maintenance
# → Option 7 : Mode Debug
```

---

## 📚 Documentation

- **README.md** : Documentation complète
- **QUICKSTART.md** : Guide rapide 5 minutes
- **INSTALLATION.md** : Ce fichier (procédure complète)

---

## ✅ Checklist finale

- [ ] Raspberry Pi OS installé
- [ ] Système mis à jour
- [ ] Boot auto-login configuré
- [ ] Script d'installation exécuté sans erreur
- [ ] Système redémarré
- [ ] Wizard de configuration complété
- [ ] Configuration enregistrée
- [ ] Service démarre automatiquement
- [ ] Interface web accessible
- [ ] Écran affiche correctement (si mode Player)
- [ ] Contenu de test créé et affiché

---

**🎉 Félicitations ! Votre système Digital Signage est opérationnel !**

**Temps total estimé : 35-45 minutes**
