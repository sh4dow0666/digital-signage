# Dossier d'Architecture Technique d'Implémentation – INFRA / MCO

## DS - Digital Signage Management System

**Version:** 1.0
**Date:** 19 décembre 2025

---

| **Version** | 1.0 du 19/12/2025 |
|-------------|-------------------|
| **Communication** | Accès réservé aux membres de la Direction des Systèmes d'Information |
| **Rédacteur principal** | [Nom] (Expert SI) |
| **Approbateur 1** | [Prénom NOM] (CTO) |
| **Approbateur 2** | [Prénom NOM] (RSSI) |

| Version | Auteur | Commentaire |
|---------|--------|-------------|
| 1.0     | MCO    | Version initiale |

---

## Table des matières

1. [Description fonctionnelle de DS](#1-description-fonctionnelle-de-ds)
   - 1.1 [Contexte, objectifs et périmètre](#11-contexte-objectifs-et-périmètre)
   - 1.2 [Fonctionnement des flux](#12-fonctionnement-des-flux)
   - 1.3 [Objectifs](#13-objectifs)

2. [Architecture technique](#2-architecture-technique)
   - 2.1 [Description des zones réseau](#21-description-des-zones-réseau)
   - 2.2 [Schéma d'architecture technique global](#22-schéma-darchitecture-technique-global)
   - 2.3 [Ressources matérielles](#23-ressources-matérielles)
   - 2.4 [Principes de fonctionnement technique](#24-principes-de-fonctionnement-technique)
   - 2.5 [Sécurité](#25-sécurité)
   - 2.6 [Matrice des risques](#26-matrice-des-risques)

3. [Référentiels techniques](#3-référentiels-techniques)
   - 3.1 [Composants internes](#31-composants-internes)
   - 3.2 [Composants "Off-the-shelf"](#32-composants-off-the-shelf)
   - 3.3 [Services externes utilisés](#33-services-externes-utilisés)
   - 3.4 [Versions OS](#34-versions-os)
   - 3.5 [IP et entrées DNS publiques et règles](#35-ip-et-entrées-dns-publiques-et-règles)
   - 3.6 [Certificats (MCO)](#36-certificats-mco)
   - 3.7 [Matrice des flux](#37-matrice-des-flux)
   - 3.8 [NAT](#38-nat)
   - 3.9 [Fichiers de configuration](#39-fichiers-de-configuration)

4. [Principes techniques (MCO)](#4-principes-techniques-mco)
   - 4.1 [Sécurité](#41-sécurité)
   - 4.2 [Authentification](#42-authentification)
   - 4.3 [Stockage](#43-stockage)
   - 4.4 [Supervision](#44-supervision)
   - 4.5 [Logs](#45-logs)
   - 4.6 [Backups](#46-backups)
   - 4.7 [Scalabilité](#47-scalabilité)
   - 4.8 [Haute disponibilité](#48-haute-disponibilité)
   - 4.9 [PRA / PCA](#49-pra--pca)

5. [Exploitation (MCO & DevOps)](#5-exploitation-mco--devops)
   - 5.1 [Prérequis de mise en œuvre](#51-prérequis-de-mise-en-œuvre)
   - 5.2 [Procédures d'exploitation](#52-procédures-dexploitation)
   - 5.3 [Déploiement](#53-déploiement)
   - 5.4 [Arrêt / Démarrage](#54-arrêt--démarrage)
   - 5.5 [Configuration de la solution](#55-configuration-de-la-solution)

6. [Rédaction et listing des changements](#6-rédaction-et-listing-des-changements)

---

## 1. Description fonctionnelle de DS

### 1.1 Contexte, objectifs et périmètre

**Contexte:** Le système DS (Digital Signage Management) a été développé pour répondre aux besoins de gestion centralisée d'affichage dynamique sur Raspberry Pi. Cette solution permet le contrôle à distance de multiples écrans via une interface web unifiée.

**Périmètres:** Nous détaillerons dans ce document chacune des briques constituant la solution. À savoir :

- Architecture réseau et flux
- Serveur Flask + SocketIO
- Gestion authentification et sécurité (2FA)
- Système de gestion de contenu
- Système de playlists
- Système de planification (schedules)
- Clients Raspberry Pi (display)

**Volumétrie:**
- Support de 50+ écrans simultanés
- Bibliothèque de contenus : illimitée (contrainte disque)
- Playlists : illimitées
- Plannings : 1 planning par écran avec entrées horaires multiples
- Types de contenus : 4 (URL, Vidéo, Image, YouTube)

### 1.2 Fonctionnement des flux

Le workflow logique de gestion d'affichage est le suivant :

#### Workflow de connexion et enregistrement

```
┌────────────────────┐
│  Manager Web UI    │
│  (Navigateur)      │
└──────────┬─────────┘
           │ 1. Authentification
           │    (username/password + 2FA)
           │
           ▼
┌──────────────────────────────┐
│    Serveur Flask + SocketIO  │
│  - Vérification credentials   │
│  - Vérification code TOTP     │
│  - Création session           │
│  - Connexion WebSocket        │
└──────────┬───────────────────┘
           │ 2. Broadcast state_update
           ▼
┌───────────────────────────────┐
│   Clients Display (RPi)       │
│   - Enregistrement screen     │
│   - Réception état initial    │
│   - Écoute événements temps   │
│     réel                      │
└───────────────────────────────┘
```

#### Workflow d'affichage de contenu

```
┌────────────────────┐
│  Manager Web UI    │
│  Action: Afficher  │
│  contenu sur écran │
└──────────┬─────────┘
           │ Socket: 'display_content'
           │ {screen_id, content_id, duration}
           │
           ▼
┌──────────────────────────────┐
│    Serveur Flask + SocketIO  │
│  - Récupération contenu       │
│  - Mise à jour état écran     │
│  - Sauvegarde screens.json    │
└──────────┬───────────────────┘
           │ Socket: 'show_content'
           │ {content, duration}
           │
           ▼
┌───────────────────────────────┐
│   Client Display (RPi)        │
│   - Réception commande        │
│   - Affichage contenu         │
│   - Gestion timer durée       │
└───────────────────────────────┘
```

#### Workflow de playlist planifiée

```
┌───────────────────────────────┐
│   Client Display (RPi)        │
│   Timer: check toutes les 30s │
└──────────┬────────────────────┘
           │ Vérification horaire actuel
           │ vs schedule écran
           ▼
┌───────────────────────────────┐
│   Si dans plage horaire:      │
│   - Lancement playlist        │
│   - Mode automatique          │
│                               │
│   Si hors plage horaire:      │
│   - Arrêt playlist planifiée  │
│   - Retour mode normal        │
└───────────────────────────────┘
```

### 1.3 Objectifs

**Objectifs à court terme :**
- Gestion centralisée de multiples écrans distants
- Diffusion de contenus variés (web, vidéo, image, YouTube)
- Planification automatisée des affichages
- Authentification sécurisée avec 2FA
- Interface d'administration intuitive

**Objectifs à long terme :**
- Support de 100+ écrans simultanés
- Système de statistiques d'affichage
- Gestion avancée des rôles utilisateurs
- API REST complète pour intégrations tierces
- Migration vers base de données relationnelle
- Support multi-zones (split screen)
- Clustering pour haute disponibilité

---

## 2. Architecture technique

### 2.1 Description des zones réseau

L'architecture réseau de DS est composée de trois zones principales :

**Zone Manager (Interface Web):**
- Navigateurs clients (Chrome, Firefox, Safari, Edge)
- Accès HTTPS/WSS vers serveur central
- Port 5000 par défaut (configurable)

**Zone Serveur (Backend Flask):**
- Serveur Flask + SocketIO
- Stockage fichiers JSON (data/)
- Stockage uploads (static/uploads/)
- Communication bidirectionnelle WebSocket

**Zone Display (Clients Raspberry Pi):**
- Raspberry Pi 3B+ minimum, Pi 4/5 recommandé
- Chromium en mode kiosk
- Connexion WebSocket persistante vers serveur
- Affichage fullscreen sans interaction utilisateur

### 2.2 Schéma d'architecture technique global

```
                        INTERNET / LAN
                              │
                              ▼
                    ┌─────────────────┐
                    │  Reverse Proxy  │
                    │ (nginx/Apache)  │
                    │  SSL/TLS        │
                    └────────┬────────┘
                             │ Port 5000
                             ▼
            ┌────────────────────────────────┐
            │    Serveur Flask + SocketIO    │
            │  ┌──────────────────────────┐  │
            │  │  Routes HTTP             │  │
            │  │  - /login                │  │
            │  │  - /manager              │  │
            │  │  - /display              │  │
            │  │  - /api/*                │  │
            │  └──────────────────────────┘  │
            │  ┌──────────────────────────┐  │
            │  │  WebSocket Handlers      │  │
            │  │  - register_screen       │  │
            │  │  - display_content       │  │
            │  │  - create_playlist       │  │
            │  │  - update_schedule       │  │
            │  └──────────────────────────┘  │
            │  ┌──────────────────────────┐  │
            │  │  Authentification        │  │
            │  │  - bcrypt                │  │
            │  │  - TOTP (pyotp)          │  │
            │  └──────────────────────────┘  │
            └────────┬───────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌───────────────┐         ┌───────────────┐
│  Stockage     │         │  Stockage     │
│  JSON         │         │  Uploads      │
│  - users      │         │  - images     │
│  - screens    │         │  - videos     │
│  - content    │         │               │
│  - playlists  │         │               │
│  - schedules  │         │               │
└───────────────┘         └───────────────┘
        │
        │ WebSocket (WSS)
        │
        ▼
┌─────────────────────────────────────────┐
│         Clients Display (N écrans)      │
│  ┌─────────────────────────────────┐   │
│  │  Raspberry Pi 1                 │   │
│  │  - Chromium kiosk               │   │
│  │  - display.html                 │   │
│  │  - ID: ecran1                   │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  Raspberry Pi 2                 │   │
│  │  - Chromium kiosk               │   │
│  │  - display.html                 │   │
│  │  - ID: ecran2                   │   │
│  └─────────────────────────────────┘   │
│  ...                                    │
│  ┌─────────────────────────────────┐   │
│  │  Raspberry Pi N                 │   │
│  │  - Chromium kiosk               │   │
│  │  - display.html                 │   │
│  │  - ID: ecranN                   │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### 2.3 Ressources matérielles

#### Environnement de préproduction

| Nom de la VM | Adresse IP | RAM (GB) | CPU (nb) | Espace disque principal (GB) | Espace disque additionnel (GB) | Description |
|--------------|------------|----------|----------|------------------------------|-------------------------------|-------------|
| DS-PREPROD-SERVER | 192.168.1.100 | 4 | 2 | 50 | 50 | Serveur Flask préproduction |

#### Environnement de production

| Nom de la VM | Adresse IP | RAM (GB) | CPU (nb) | Espace disque principal (GB) | Espace disque additionnel (GB) | Description |
|--------------|------------|----------|----------|------------------------------|-------------------------------|-------------|
| DS-PROD-SERVER | 10.x.x.x | 4 | 4 | 50 | 100 | Serveur Flask production |

#### Clients Raspberry Pi (Display)

| Modèle | RAM | Stockage | Réseau | Description |
|--------|-----|----------|--------|-------------|
| Raspberry Pi 3B+ | 1GB | 16GB SD | WiFi/Ethernet | Minimum supporté |
| Raspberry Pi 4 | 2GB+ | 16GB SD | WiFi/Ethernet | Recommandé |
| Raspberry Pi 5 | 4GB+ | 32GB SD | WiFi/Ethernet | Optimal |

### 2.4 Principes de fonctionnement technique

#### 2.4.1 Serveur Flask + SocketIO

L'application serveur est construite sur Flask avec l'extension Flask-SocketIO pour la communication temps réel.

**Caractéristiques principales:**
- **Framework:** Flask 2.x
- **Communication temps réel:** Flask-SocketIO (wrapper de python-socketio)
- **Transport:** WebSocket avec fallback sur polling
- **Sessions:** Flask sessions (cookie signé)
- **Threads:** eventlet ou gevent pour async

**Gestion de l'état:**
```python
# État en mémoire (runtime)
screens = {}              # {screen_id: screen_data}
content_library = []      # Liste contenus
playlists = {}           # {playlist_id: playlist_data}
schedules = {}           # {screen_id: schedule_entries}

# Persistance (fichiers JSON)
data/screens.json
data/content.json
data/playlists.json
data/schedules.json
data/users.json
```

**Workflow sauvegarde:**
1. Modification état mémoire
2. Appel fonction `save_*()` appropriée
3. Écriture JSON sur disque
4. Broadcast `state_update` aux clients connectés

#### 2.4.2 Système d'authentification

**Authentification par mot de passe:**
- Hash: bcrypt avec salt automatique
- Validation minimum: 8 caractères
- Stockage: Hash uniquement, jamais en clair

**Double authentification (2FA):**
- Protocole: TOTP (Time-based One-Time Password, RFC 6238)
- Algorithme: SHA-1
- Période: 30 secondes
- Window: ±1 période (validation flexible)
- Secret: Base32, 32 caractères
- QR Code: Provisioning URI compatible Google Authenticator

**Workflow connexion:**
```
1. Utilisateur saisit username/password
2. Serveur vérifie hash bcrypt
3. Si 2FA activé:
   3.1. Affichage page code TOTP
   3.2. Vérification code (window=1)
4. Création session Flask
5. Redirection vers /manager
```

#### 2.4.3 Clients Display (Raspberry Pi)

Les clients display sont des Raspberry Pi exécutant Chromium en mode kiosk, chargés sur la page `/display`.

**Configuration URL:**
```
http://SERVER_IP:5000/display?id=ecran1&name=Cuisine&location=RDC
```

**Paramètres:**
- `id` (requis): Identifiant unique écran
- `name` (optionnel): Nom affichage
- `location` (optionnel): Localisation physique

**Logique d'affichage:**

1. **Enregistrement initial:**
   - Connexion WebSocket au serveur
   - Envoi événement `register_screen` avec paramètres URL
   - Réception état initial et configuration

2. **Modes d'affichage:**
   - **Mode prioritaire:** Contenu/playlist lancé manuellement, bloque planification
   - **Mode planifié:** Playlist lancée automatiquement selon schedule
   - **Mode normal:** En attente de commande

3. **Vérification planning:**
   - Timer: Toutes les 30 secondes
   - Comparaison horaire actuel vs schedule écran
   - Lancement automatique si dans plage horaire
   - Arrêt automatique si hors plage horaire

4. **Gestion configuration:**
   - Affichage horloge (overlay configurable)
   - Luminosité (si supportée par écran)
   - Autres paramètres display

#### 2.4.4 Système de contenus

**Types de contenus supportés:**

| Type | Description | Rendu | Durée |
|------|-------------|-------|-------|
| `url` | Page web | iframe | Configurable |
| `video` | Fichier vidéo | HTML5 video | Configurable |
| `image` | Image statique | img tag | Configurable |
| `youtube` | Vidéo YouTube | iframe autoplay | Configurable |

**Structure contenu:**
```json
{
  "id": "1734607200000",
  "name": "Météo locale",
  "type": "url",
  "url": "https://meteo.example.com",
  "duration": 30
}
```

**Durée = 0:** Affichage infini (jusqu'à commande effacement)

#### 2.4.5 Système de playlists

Une playlist est une collection ordonnée de contenus avec durées individuelles.

**Structure playlist:**
```json
{
  "id": "playlist_123",
  "name": "Informations matinales",
  "items": [
    {
      "content": { /* objet contenu complet */ },
      "duration": 20
    },
    {
      "content": { /* objet contenu complet */ },
      "duration": 15
    }
  ],
  "created_at": "2025-12-19T08:00:00"
}
```

**Fonctionnement:**
1. Lancement playlist → Affichage premier item
2. Après durée item → Affichage item suivant
3. Fin playlist → Boucle automatique (retour au début)
4. Arrêt: Commande manuelle ou fin durée globale

**Options lancement:**
- **Durée globale:** Limite temps total playlist (optionnel)
- **Mode prioritaire:** Bloque interventions planification

#### 2.4.6 Système de planification

Le système de planification permet le lancement automatique de playlists selon horaires définis.

**Structure schedule:**
```json
{
  "ecran1": [
    {
      "start": "08:00",
      "end": "12:00",
      "playlist_id": "playlist_123"
    },
    {
      "start": "14:00",
      "end": "18:00",
      "playlist_id": "playlist_456"
    }
  ]
}
```

**Logique vérification (côté display):**
```javascript
function checkSchedule() {
  const now = new Date();
  const currentTime = `${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}`;

  for (const entry of schedule) {
    if (currentTime >= entry.start && currentTime < entry.end) {
      // Lancer playlist si pas déjà active
      if (activeScheduledPlaylistId !== entry.playlist_id) {
        launchScheduledPlaylist(entry.playlist_id);
      }
      return;
    }
  }

  // Aucune entrée active: arrêter playlist planifiée
  if (activeScheduledPlaylistId) {
    stopScheduledPlaylist();
  }
}

setInterval(checkSchedule, 30000); // Toutes les 30 secondes
```

### 2.5 Sécurité

#### 2.5.1 Authentification et autorisation

**Mécanismes de sécurité:**
- Hashing mots de passe: bcrypt (salt automatique, coût adaptatif)
- Double authentification: TOTP (RFC 6238)
- Sessions: Cookie Flask signé avec secret key
- Protection CSRF: Intégrée Flask
- Protection routes: Décorateur `@login_required`

**Permissions utilisateurs:**
- Création utilisateur: Tous utilisateurs connectés
- Modification nom/MDP: Tous utilisateurs (même les autres)
- Suppression: Interdite si utilisateur courant ou dernier utilisateur
- Activation 2FA: Uniquement pour soi-même
- Désactivation 2FA: Tous utilisateurs (admin reset)

#### 2.5.2 Communication réseau

**Protocoles:**
- HTTP/HTTPS pour routes web
- WebSocket/WSS pour communication temps réel
- CORS: Configurable (actuellement ouvert `*` en développement)

**Recommandations production:**
- Reverse proxy obligatoire (nginx/Apache)
- Certificat SSL/TLS (Let's Encrypt ou commercial)
- CORS restreint aux domaines autorisés
- Rate limiting sur routes sensibles (/login)

#### 2.5.3 Stockage et données

**Fichiers JSON:**
- Permissions fichiers: 600 (rw-------)
- Propriétaire: Utilisateur exécutant Flask
- Emplacement: `data/` (relatif à application)

**Uploads:**
- Limite taille: 50MB par fichier
- Types autorisés: Images (jpg, png, gif, webp)
- Validation: Extension et MIME type
- Stockage: `static/uploads/` avec nom unique (timestamp)

#### 2.5.4 Validation des entrées

**Côté serveur (Python):**
```python
# Username: Non vide, trim espaces
username = username.strip()
if not username:
    return error

# Mot de passe: Minimum 8 caractères
if len(password) < 8:
    return error

# Code TOTP: 6 chiffres
if not re.match(r'^[0-9]{6}$', code):
    return error
```

**Côté client (JavaScript/HTML):**
```html
<!-- Pattern HTML5 -->
<input type="text" pattern="[0-9]{6}" maxlength="6">

<!-- Validation JavaScript -->
if (password.length < 8) {
    alert("Mot de passe trop court");
    return false;
}
```

### 2.6 Matrice des risques

| Risque | Impact | Probabilité | Mitigation |
|--------|--------|-------------|------------|
| Perte mot de passe admin | Élevé | Faible | Procédure reset via accès serveur |
| Corruption fichiers JSON | Élevé | Faible | Sauvegardes régulières, write atomique |
| Attaque brute force login | Moyen | Moyen | Rate limiting, monitoring logs |
| Déconnexion displays | Faible | Moyen | Reconnexion automatique Socket.IO |
| Remplissage disque (uploads) | Moyen | Faible | Quotas, monitoring espace disque |
| Secret 2FA compromis | Élevé | Faible | Régénération secret, révocation |
| Faille CORS (dev) | Moyen | Élevé | Configuration stricte production |
| Secret key Flask faible | Élevé | Moyen | Variable environnement production |

---

## 3. Référentiels techniques

### 3.1 Composants internes

#### 3.1.1 Backend (gestion_raspberry.py)

**Modules principaux:**
- **Routes HTTP:** Gestion authentification, interface web, API REST
- **WebSocket handlers:** Événements Socket.IO temps réel
- **Gestion utilisateurs:** CRUD, vérification credentials, 2FA
- **Gestion données:** Lecture/écriture JSON, state management
- **Configuration:** Paramètres système, YouTube API

**Langages et frameworks:**
- Python 3.8+
- Flask 2.x
- Flask-SocketIO 5.x

#### 3.1.2 Frontend Manager (manager.html)

**Composants:**
- Interface authentification (login, setup 2FA)
- Dashboard écrans (liste, statut, actions)
- Bibliothèque contenus (CRUD, filtres)
- Gestion playlists (éditeur, drag & drop)
- Gestion plannings (éditeur horaires)
- Modal paramètres (utilisateurs, configuration)

**Technologies:**
- HTML5
- CSS3
- JavaScript (Vanilla, pas de framework)
- Socket.IO client

#### 3.1.3 Frontend Display (display.html)

**Composants:**
- Container affichage contenu
- Overlay horloge (configurable)
- Debug panel (informations temps réel)
- Indicateur mode prioritaire

**Technologies:**
- HTML5
- CSS3
- JavaScript (Vanilla)
- Socket.IO client

### 3.2 Composants "Off-the-shelf"

#### Flask
- **Lien:** https://flask.palletsprojects.com/
- **License:** BSD-3-Clause
- **Version:** 2.0.0+
- **Langage:** Python

#### Flask-SocketIO
- **Lien:** https://flask-socketio.readthedocs.io/
- **License:** MIT
- **Version:** 5.0.0+
- **Langage:** Python

#### Socket.IO (client JavaScript)
- **Lien:** https://socket.io/
- **License:** MIT
- **Version:** 4.x
- **Langage:** JavaScript

#### bcrypt
- **Lien:** https://github.com/pyca/bcrypt/
- **License:** Apache-2.0
- **Version:** 4.0.0+
- **Langage:** Python (binding C)

#### pyotp
- **Lien:** https://github.com/pyauth/pyotp
- **License:** MIT
- **Version:** 2.9.0+
- **Langage:** Python

#### qrcode + Pillow
- **Lien:** https://github.com/lincolnloop/python-qrcode
- **License:** BSD
- **Version:** 7.4.0+ (qrcode), 10.0.0+ (Pillow)
- **Langage:** Python

#### requests
- **Lien:** https://requests.readthedocs.io/
- **License:** Apache-2.0
- **Version:** 2.25.0+
- **Langage:** Python

#### isodate
- **Lien:** https://github.com/gweis/isodate
- **License:** BSD
- **Version:** 0.6.0+
- **Langage:** Python

### 3.3 Services externes utilisés

#### YouTube Data API v3 (optionnel)
- **Service:** API REST YouTube
- **Utilisation:** Récupération métadonnées vidéos (titre, durée, miniature)
- **Authentification:** API Key (configurable dans paramètres)
- **Endpoint:** `https://www.googleapis.com/youtube/v3/videos`
- **Licence:** Gratuit (quota quotidien)

**Note:** API YouTube optionnelle, fonctionnement dégradé si non configurée (pas de métadonnées automatiques).

### 3.4 Versions OS

#### Serveur
- **OS recommandé:** Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)
- **Compatibilité:** Windows, macOS (développement uniquement)
- **Python:** 3.8, 3.9, 3.10, 3.11, 3.12

#### Clients Display (Raspberry Pi)
- **OS recommandé:** Raspberry Pi OS (anciennement Raspbian)
- **Version:** Bullseye (11) ou Bookworm (12)
- **Browser:** Chromium 90+

### 3.5 IP et entrées DNS publiques et règles

#### Préproduction

- **Type:** A
- **Nom de domaine:** ds-preprod.example.com
- **Adresse IP:** 192.168.1.100
- **Port:** 5000

#### Production

- **Type:** A
- **Nom de domaine:** ds.example.com
- **Adresse IP:** X.X.X.X (IP publique)
- **Port:** 443 (HTTPS) → 5000 (backend via reverse proxy)

### 3.6 Certificats (MCO)

#### Certificat SSL/TLS (Production)

- **Type:** SSL/TLS
- **Utilisation:** Chiffrement HTTPS/WSS
- **Émetteur:** Let's Encrypt (gratuit, auto-renouvelable) ou autorité commerciale
- **Domaine:** ds.example.com
- **Validité:** 90 jours (Let's Encrypt), renouvellement automatique
- **Stockage:** Nginx/Apache (reverse proxy)

**Renouvellement:**
```bash
# Let's Encrypt (certbot)
sudo certbot renew
sudo systemctl reload nginx
```

### 3.7 Matrice des flux

#### 3.7.1 Flux Manager → Serveur

| Source | Destination | Port | Protocol | Rôle / Objectif |
|--------|-------------|------|----------|-----------------|
| Navigateur client | Serveur Flask | 5000 | HTTP/HTTPS | Routes web (login, manager, API) |
| Navigateur client | Serveur Flask | 5000 | WebSocket/WSS | Communication temps réel |

#### 3.7.2 Flux Display → Serveur

| Source | Destination | Port | Protocol | Rôle / Objectif |
|--------|-------------|------|----------|-----------------|
| Raspberry Pi | Serveur Flask | 5000 | HTTP/HTTPS | Chargement page /display |
| Raspberry Pi | Serveur Flask | 5000 | WebSocket/WSS | Enregistrement écran, réception commandes |

#### 3.7.3 Flux Serveur → Services externes

| Source | Destination | Port | Protocol | Rôle / Objectif |
|--------|-------------|------|----------|-----------------|
| Serveur Flask | YouTube API | 443 | HTTPS | Récupération métadonnées vidéos (optionnel) |

#### 3.7.4 Flux internes serveur

| Source | Destination | Rôle / Objectif |
|--------|-------------|-----------------|
| Flask app | Fichiers JSON (data/) | Lecture/écriture données persistantes |
| Flask app | Uploads (static/uploads/) | Lecture/écriture images uploadées |

### 3.8 NAT

#### Production

**Mapping externe → interne:**
- **Port externe:** 443 (HTTPS)
- **Port interne:** 5000 (Flask)
- **Protocole:** TCP
- **Adresse publique:** X.X.X.X (IP publique firewall)
- **Adresse privée:** 10.x.x.x (serveur Flask)

**Configuration firewall:**
```
DNAT: 0.0.0.0:443 → 10.x.x.x:5000 (via reverse proxy nginx:443)
```

### 3.9 Fichiers de configuration

#### 3.9.1 Configuration Flask (gestion_raspberry.py)

```python
# Configuration principale
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'votre-cle-secrete-ici')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# Configuration SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins="*",  # À restreindre en production
    async_mode='eventlet'
)
```

#### 3.9.2 Configuration systemd (optionnel)

```ini
[Unit]
Description=DS Digital Signage Management System
After=network.target

[Service]
Type=simple
User=ds-user
Group=ds-user
WorkingDirectory=/opt/DS
Environment="SECRET_KEY=random_secret_key_here"
Environment="FLASK_ENV=production"
ExecStart=/opt/DS/venv/bin/python gestion_raspberry.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 3.9.3 Configuration nginx (reverse proxy)

```nginx
server {
    listen 443 ssl http2;
    server_name ds.example.com;

    ssl_certificate /etc/letsencrypt/live/ds.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ds.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 3.9.4 Configuration autostart Raspberry Pi

```bash
# ~/.config/lxsession/LXDE-pi/autostart
@xset s off
@xset -dpms
@xset s noblank
@chromium-browser --kiosk --noerrdialogs \
  --disable-infobars \
  --disable-session-crashed-bubble \
  "http://SERVER_IP:5000/display?id=ecran1&name=Cuisine&location=RDC"
```

---

## 4. Principes techniques (MCO)

### 4.1 Sécurité

#### Accès

**Protocoles utilisés:**
- HTTP/HTTPS (routes web)
- WebSocket/WSS (communication temps réel)

**Reverse proxy:**
- Nginx ou Apache recommandé en production
- Gestion SSL/TLS
- Rate limiting (optionnel mais recommandé)

**Firewall:**
- Autoriser uniquement port 443 (HTTPS) en entrée
- Bloquer port 5000 direct (accès uniquement via reverse proxy)

#### Mot de passe / Tokens / Certificats

**Mots de passe:**
- Hashing: bcrypt (coût 12 par défaut)
- Stockage: Hash uniquement dans users.json
- Validation: Minimum 8 caractères

**Tokens TOTP (2FA):**
- Secret: Base32, 32 caractères, généré aléatoirement
- Stockage: Chiffré dans users.json (à améliorer: chiffrement base niveau supérieur)
- Validité: 30 secondes par code, window ±1

**Certificats SSL/TLS:**
- Let's Encrypt (gratuit, auto-renouvelable)
- Renouvellement automatique via certbot
- Stockage: /etc/letsencrypt/

#### Chiffrement des données

**En transit:**
- HTTPS/WSS obligatoire en production
- TLS 1.2+ minimum
- Ciphers modernes recommandés

**Au repos:**
- Fichiers JSON: Permissions restrictives (600)
- Mots de passe: Hash bcrypt irréversible
- Secrets 2FA: À chiffrer niveau application (amélioration future)

#### Autres

**Sessions Flask:**
- Cookie signé avec secret key
- HttpOnly activé (protection XSS)
- Secure activé en production (HTTPS uniquement)

**Protection CSRF:**
- Intégrée Flask pour formulaires
- Token CSRF dans forms

### 4.2 Authentification

**Workflow complet:**

1. **Première connexion système:**
   - Aucun utilisateur existant
   - Redirection automatique vers `/create_admin`
   - Création premier administrateur

2. **Connexion standard:**
   - Saisie username + password
   - Vérification hash bcrypt
   - Si 2FA activé: Demande code TOTP
   - Création session Flask
   - Redirection vers `/manager`

3. **Protection routes:**
   - Décorateur `@login_required` sur routes sensibles
   - Vérification `session.get('username')`
   - Redirection `/login` si non authentifié

4. **Déconnexion:**
   - Suppression session Flask
   - Redirection `/login`

### 4.3 Stockage

**Besoins de stockage:**

| Composant | Taille estimée | Volumétrie | Croissance |
|-----------|----------------|------------|------------|
| Application | 5 MB | Fixe | Mises à jour occasionnelles |
| Dépendances Python | 50 MB | Fixe | Mises à jour occasionnelles |
| users.json | < 1 MB | 10-100 utilisateurs | Lente |
| screens.json | < 1 MB | 50-200 écrans | Lente |
| content.json | < 5 MB | 100-1000 contenus | Moyenne |
| playlists.json | < 5 MB | 50-500 playlists | Moyenne |
| schedules.json | < 1 MB | 50-200 schedules | Lente |
| Uploads (images) | Variable | 10-1000 fichiers | Rapide |

**Volumétrie production (estimation):**
- Serveur minimal: 10 GB (système + application + marge)
- Serveur recommandé: 50 GB (uploads importants)
- Serveur optimal: 100 GB (marge confortable, logs)

**Performance disque:**
- SSD recommandé pour serveur (latence I/O)
- SD Card classe 10 minimum pour Raspberry Pi

### 4.4 Supervision

**Supervision serveur:**

À implémenter (amélioration future):
- Monitoring uptime serveur
- Monitoring nombre connexions WebSocket actives
- Monitoring espace disque
- Monitoring charge CPU/RAM
- Alertes si service down

**Supervision écrans:**

Actuellement disponible:
- Statut online/offline (interface manager)
- Dernier heartbeat (last_seen)
- Contenu/playlist actuel
- Erreurs logs (debug panel display)

### 4.5 Logs

**Logs serveur (stdout):**
```python
print(f"✅ Utilisateur {username} connecté")
print(f"⚠️ Tentative connexion échouée: {username}")
print(f"❌ Erreur sauvegarde fichier: {e}")
```

**Logs display (console JavaScript):**
```javascript
console.log("✅ Connexion WebSocket établie");
console.log("📺 Affichage contenu:", content.name);
console.log("⏰ Vérification planning");
console.error("❌ Erreur chargement contenu:", error);
```

**Amélioration future:**
- Logs structurés (JSON)
- Rotation logs automatique
- Centralisation logs (ELK, Graylog)
- Niveaux logs (DEBUG, INFO, WARNING, ERROR)

### 4.6 Backups

**Stratégie de sauvegarde:**

**Données critiques:**
- `data/users.json` (comptes utilisateurs)
- `data/screens.json` (registre écrans)
- `data/content.json` (bibliothèque contenus)
- `data/playlists.json` (définitions playlists)
- `data/schedules.json` (plannings écrans)
- `static/uploads/*` (images uploadées)

**Fréquence recommandée:**
- Quotidienne: Fichiers JSON
- Hebdomadaire: Uploads
- Avant mise à jour: Snapshot complet

**Procédure sauvegarde manuelle:**
```bash
# Sauvegarde complète
cd /opt/DS
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz data/ static/uploads/

# Sauvegarde vers destination externe
rsync -avz data/ user@backup-server:/backups/DS/data/
rsync -avz static/uploads/ user@backup-server:/backups/DS/uploads/
```

**Restauration:**
```bash
# Restauration complète
tar -xzf backup_YYYYMMDD_HHMMSS.tar.gz

# Restauration sélective
tar -xzf backup_YYYYMMDD_HHMMSS.tar.gz data/users.json
```

**Amélioration future:**
- Script automatique (cron)
- Sauvegarde incrémentielle
- Rétention configurable (7 jours, 4 semaines, 12 mois)
- Notification échec sauvegarde

### 4.7 Scalabilité

**Scalabilité verticale (serveur unique):**

| Charge | Écrans | CPU | RAM | Recommandation |
|--------|--------|-----|-----|----------------|
| Faible | 1-10 | 2 cores | 2 GB | Raspberry Pi 4 suffisant |
| Moyenne | 10-50 | 4 cores | 4 GB | VM standard |
| Élevée | 50-100 | 8 cores | 8 GB | VM puissante ou serveur dédié |

**Scalabilité horizontale (clustering):**

Non supporté actuellement. Amélioration future:
- Load balancer (nginx/HAProxy)
- Session sticky ou partagée (Redis)
- Synchronisation état (Redis pub/sub)
- Base de données centralisée (PostgreSQL)

**Limitations actuelles:**
- État en mémoire (non partagé multi-instance)
- Fichiers JSON (non adapté haute concurrence)
- Pas de cache distribué

### 4.8 Haute disponibilité

**Actuellement:**
Pas de haute disponibilité native. Serveur unique = SPOF (Single Point of Failure).

**Amélioration future:**

1. **Serveurs redondants:**
   - 2+ serveurs Flask derrière load balancer
   - Session partagée via Redis
   - Heartbeat entre serveurs

2. **Base de données:**
   - Migration vers PostgreSQL
   - Réplication master-slave ou multi-master

3. **Stockage:**
   - NAS ou SAN partagé pour uploads
   - Réplication fichiers uploads

4. **Monitoring:**
   - Détection panne serveur
   - Failover automatique

### 4.9 PRA / PCA

**Plan de Reprise d'Activité (PRA):**

**Objectifs:**
- RTO (Recovery Time Objective): 1 heure
- RPO (Recovery Point Objective): 24 heures (backup quotidien)

**Procédure:**

1. **Détection incident:**
   - Monitoring indique serveur down
   - Validation panne (ping, HTTP check)

2. **Restauration serveur:**
   - Démarrage serveur de secours (VM ou physique)
   - Installation application via bootstrap.sh
   - Restauration backup données (dernier backup quotidien)

3. **Reconfiguration réseau:**
   - Mise à jour DNS vers nouvelle IP
   - Configuration firewall/NAT

4. **Vérification:**
   - Test connexion manager
   - Test connexion displays
   - Vérification état système

5. **Communication:**
   - Notification utilisateurs (si coupure prolongée)
   - Post-mortem incident

**Plan de Continuité d'Activité (PCA):**

**Mode dégradé:**
Si serveur indisponible, displays:
- Maintiennent dernier contenu affiché
- Tentent reconnexion automatique
- Planning local (si implémenté) continue fonctionner

**Amélioration future:**
- Serveur de backup automatique (warm standby)
- Synchronisation temps réel données vers backup
- Failover automatique (keepalived, VRRP)

---

## 5. Exploitation (MCO & DevOps)

### 5.1 Prérequis de mise en œuvre

#### Serveur

**Système d'exploitation:**
- Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)
- Python 3.8+ pré-installé ou disponible

**Packages système:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git

# CentOS/RHEL
sudo yum install -y python3 python3-pip git
```

**Réseau:**
- Port 5000 disponible (ou port configuré)
- Accès sortant vers Internet (pip, git, YouTube API)
- Accès entrant depuis displays et managers

**Permissions:**
- Utilisateur non-root pour exécution (sécurité)
- Droits écriture sur répertoire application

#### Clients Display (Raspberry Pi)

**Système d'exploitation:**
- Raspberry Pi OS (Bullseye ou Bookworm)
- Chromium pré-installé (normalement inclus)

**Configuration:**
```bash
# Désactivation économiseur d'écran
sudo apt-get install -y xscreensaver
# Configuration manuelle via GUI ou autostart

# Installation dépendances supplémentaires (si nécessaire)
sudo apt-get install -y chromium-browser
```

**Réseau:**
- Connexion stable vers serveur (WiFi ou Ethernet)
- Résolution DNS fonctionnelle

### 5.2 Procédures d'exploitation

#### Procédure P1: Création d'un nouvel utilisateur

**Via interface web:**
1. Connexion `/manager` avec compte admin
2. Clic bouton "⚙️ Paramètres"
3. Onglet "Gestion des utilisateurs"
4. Clic "➕ Créer un utilisateur"
5. Saisie username, password, confirmation
6. Validation formulaire
7. Utilisateur créé (2FA désactivé par défaut)

**Via API:**
```bash
curl -X POST http://SERVER_IP:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{"username":"newuser","password":"SecurePass123"}'
```

#### Procédure P2: Activation 2FA pour soi-même

**Via interface web:**
1. Connexion `/manager` avec son compte
2. Clic bouton "⚙️ Paramètres"
3. Onglet "Gestion des utilisateurs"
4. Clic "🔐 Activer 2FA" sur sa propre ligne
5. Scan QR code avec application authenticator
6. Saisie code TOTP pour validation
7. 2FA activé (secret conservé)

#### Procédure P3: Enregistrement d'un nouvel écran

**Configuration Raspberry Pi:**
1. Installation OS Raspberry Pi
2. Configuration réseau (WiFi ou Ethernet)
3. Configuration autostart Chromium:
   ```bash
   nano ~/.config/lxsession/LXDE-pi/autostart
   # Ajouter ligne:
   @chromium-browser --kiosk --noerrdialogs \
     "http://SERVER_IP:5000/display?id=UNIQUE_ID&name=NOM&location=LIEU"
   ```
4. Redémarrage Raspberry Pi
5. Écran apparaît automatiquement dans interface manager

#### Procédure P4: Création et lancement d'une playlist

**Via interface web:**
1. Connexion `/manager`
2. Section "📋 Playlists"
3. Clic "➕ Créer une playlist"
4. Saisie nom playlist
5. Drag & drop contenus depuis bibliothèque
6. Configuration durée pour chaque item
7. Validation "Créer la playlist"
8. Pour lancer: Clic écran → "▶️ Lancer playlist" → Sélection playlist → Durée totale (optionnel) → "Lancer"

#### Procédure P5: Configuration d'un planning automatique

**Via interface web:**
1. Connexion `/manager`
2. Section "📅 Planning"
3. Sélection écran dans dropdown
4. Clic "➕ Ajouter horaire"
5. Configuration:
   - Heure début (ex: 08:00)
   - Heure fin (ex: 12:00)
   - Playlist associée
6. Validation "Ajouter au planning"
7. Répéter pour autres plages horaires
8. Planning envoyé automatiquement à l'écran

#### Procédure P6: Mise à jour application

**Via interface web:**
1. Badge "🔄 Mise à jour disponible" affiché (si MAJ dispo)
2. Clic badge → Modal confirmation
3. Clic "Installer la mise à jour"
4. Redémarrage service recommandé après MAJ

**Via ligne de commande:**
```bash
cd /opt/DS  # Ou chemin application
git pull origin main
sudo systemctl restart ds.service  # Si service systemd
```

### 5.3 Déploiement

#### Déploiement automatique (recommandé)

**Script bootstrap:**
```bash
curl -fsSL https://raw.githubusercontent.com/sh4dow0666/digital-signage/main/bootstrap.sh | bash
```

**Actions du script:**
1. Vérification prérequis (Python, git)
2. Clonage repository GitHub
3. Création environnement virtuel Python
4. Installation dépendances (pip install -r requirements.txt)
5. Création répertoires (data/, static/uploads/)
6. Configuration permissions
7. Lancement application

#### Déploiement manuel

```bash
# 1. Clonage repository
git clone https://github.com/sh4dow0666/digital-signage.git /opt/DS
cd /opt/DS

# 2. Environnement virtuel
python3 -m venv venv
source venv/bin/activate

# 3. Installation dépendances
pip install -r requirements.txt

# 4. Création répertoires
mkdir -p data static/uploads

# 5. Lancement
python gestion_raspberry.py
```

#### Déploiement production avec systemd

```bash
# 1. Déploiement application (voir ci-dessus)

# 2. Création fichier service
sudo nano /etc/systemd/system/ds.service
# Copier contenu section 3.9.2

# 3. Activation service
sudo systemctl daemon-reload
sudo systemctl enable ds.service
sudo systemctl start ds.service

# 4. Vérification
sudo systemctl status ds.service
```

#### Déploiement avec reverse proxy nginx

```bash
# 1. Déploiement application (voir ci-dessus)

# 2. Installation nginx
sudo apt-get install -y nginx certbot python3-certbot-nginx

# 3. Configuration site
sudo nano /etc/nginx/sites-available/ds
# Copier contenu section 3.9.3

# 4. Activation site
sudo ln -s /etc/nginx/sites-available/ds /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 5. Certificat SSL (Let's Encrypt)
sudo certbot --nginx -d ds.example.com
```

### 5.4 Arrêt / Démarrage

#### Service systemd

**Démarrage:**
```bash
sudo systemctl start ds.service
```

**Arrêt:**
```bash
sudo systemctl stop ds.service
```

**Redémarrage:**
```bash
sudo systemctl restart ds.service
```

**Statut:**
```bash
sudo systemctl status ds.service
```

**Logs:**
```bash
sudo journalctl -u ds.service -f
```

#### Mode manuel (développement)

**Démarrage:**
```bash
cd /opt/DS
source venv/bin/activate
python gestion_raspberry.py
```

**Arrêt:**
```bash
# Ctrl+C dans terminal
# ou
pkill -f gestion_raspberry.py
```

### 5.5 Configuration de la solution

#### Configuration initiale

**Première connexion:**
1. Accès `http://SERVER_IP:5000`
2. Redirection automatique `/create_admin`
3. Création premier administrateur
4. Connexion avec compte créé

**Configuration paramètres:**
1. Connexion `/manager`
2. Clic "⚙️ Paramètres"
3. Onglet "Configuration"
4. Configuration YouTube API Key (optionnel)
5. Sauvegarde

#### Configuration utilisateurs

Voir procédures P1 (création) et P2 (2FA) section 5.2.

#### Configuration écrans

**Enregistrement:** Voir procédure P3 section 5.2.

**Configuration écran:**
1. Section "📺 Écrans connectés"
2. Clic "⚙️" sur écran
3. Configuration:
   - Affichage horloge (toggle)
   - Autres paramètres (futurs)
4. Validation

#### Configuration contenus

**Ajout contenu:**
1. Section "📚 Bibliothèque de contenus"
2. Clic "➕ Ajouter un contenu"
3. Sélection type (URL, Vidéo, Image, YouTube)
4. Configuration:
   - Nom
   - URL ou upload fichier
   - Durée affichage (0 = infini)
5. Validation

**Modification contenu:**
1. Clic "✏️" sur contenu
2. Modification champs
3. Validation

**Suppression contenu:**
1. Clic "🗑️" sur contenu
2. Confirmation

#### Configuration playlists

Voir procédure P4 section 5.2.

#### Configuration plannings

Voir procédure P5 section 5.2.

---

## 6. Rédaction et listing des changements

### Historique des changements

| Date | Version | Auteur | Type | Description |
|------|---------|--------|------|-------------|
| 2025-12-19 | 1.0 | MCO | Initial | Création document DAT initial |
| - | - | - | - | - |

### Changements planifiés (roadmap)

**Court terme (Q1 2026):**
- Migration base de données PostgreSQL
- Implémentation rate limiting
- Amélioration logs (JSON structuré, rotation)
- Backup automatique quotidien

**Moyen terme (Q2-Q3 2026):**
- Système de rôles utilisateurs (admin/user)
- Statistiques d'affichage (vues, durées)
- API REST complète (documentation OpenAPI)
- Support multi-zones (split screen)

**Long terme (Q4 2026+):**
- Clustering haute disponibilité
- Support audio
- Flux RTSP/streaming
- Templates playlists
- Monitoring Prometheus/Grafana

---

**Fin du Document d'Architecture Technique d'Implémentation – INFRA / MCO**

*Document version 1.0 - 19 décembre 2025*
