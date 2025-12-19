# Document d'Architecture Technique (DAT)
## Système de Gestion d'Affichage Multi-Écrans - DS MCO

**Version:** 2.0
**Date:** 19 Décembre 2025
**Auteur:** Système DS MCO

---

## 1. Vue d'ensemble

### 1.1 Description du système
DS MCO est un système de gestion d'affichage numérique pour Raspberry Pi permettant le contrôle centralisé de multiples écrans à distance via une interface web. Le système permet la diffusion de contenus variés (pages web, vidéos, images, YouTube) avec gestion de playlists et planification horaire.

### 1.2 Objectifs
- Contrôle centralisé de multiples écrans distants
- Communication temps réel bidirectionnelle
- Gestion de contenu multi-format
- Planification automatisée
- Authentification sécurisée avec 2FA
- Interface d'administration intuitive

### 1.3 Technologies principales
- **Backend:** Python 3, Flask 2.x, Flask-SocketIO
- **Communication:** WebSocket (Socket.IO)
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **Stockage:** JSON (fichiers plats)
- **Authentification:** bcrypt, pyotp (TOTP)
- **QR Code:** qrcode, Pillow

---

## 2. Architecture globale

### 2.1 Diagramme de composants

```
┌─────────────────────────────────────────────────────────────┐
│                    Interface Web Manager                     │
│  ┌──────────┬──────────┬──────────┬──────────┬───────────┐ │
│  │ Contenus │ Playlist │ Planning │ Écrans   │ Paramètres│ │
│  └──────────┴──────────┴──────────┴──────────┴───────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS/WSS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Serveur Flask + SocketIO                  │
│  ┌────────────┬─────────────┬──────────────┬─────────────┐ │
│  │   Routes   │  WebSocket  │ Authentif.   │   API       │ │
│  │   HTTP     │  Handlers   │  2FA/bcrypt  │   REST      │ │
│  └────────────┴─────────────┴──────────────┴─────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │  JSON    │  │  JSON    │  │  JSON    │
    │  Files   │  │  Session │  │  Users   │
    └──────────┘  └──────────┘  └──────────┘
          │              │              │
          └──────────────┴──────────────┘
                         │ WSS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Clients Display (Raspberry Pi)                  │
│  ┌──────────┬──────────┬──────────┬──────────────────────┐ │
│  │  WebView │  Player  │ Schedule │  Config (horloge)    │ │
│  │ Chromium │  Engine  │  Checker │                      │ │
│  └──────────┴──────────┴──────────┴──────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Flux de données

1. **Connexion Manager → Serveur:**
   - Authentification (username/password + TOTP)
   - Établissement session HTTP
   - Connexion WebSocket persistante

2. **Connexion Display → Serveur:**
   - Enregistrement via Socket.IO (ID, nom, location)
   - Réception état initial
   - Écoute événements temps réel

3. **Diffusion contenu:**
   - Manager envoie commande → Serveur
   - Serveur broadcast → Display(s) ciblé(s)
   - Display affiche contenu

---

## 3. Backend - Architecture détaillée

### 3.1 Structure des fichiers

```
DS/
├── gestion_raspberry.py          # Application principale Flask
├── requirements.txt              # Dépendances Python
├── data/                         # Données persistantes
│   ├── screens.json             # Registre des écrans
│   ├── content.json             # Bibliothèque de contenus
│   ├── playlists.json           # Définitions des playlists
│   ├── schedules.json           # Plannings horaires
│   └── users.json               # Comptes utilisateurs
├── static/
│   ├── css/
│   │   ├── style.css           # Styles manager
│   │   └── player.css          # Styles display
│   └── uploads/                # Images uploadées
└── templates/
    ├── manager.html             # Interface gestionnaire
    ├── display.html             # Interface client display
    ├── login.html               # Page de connexion
    ├── setup_2fa.html           # Configuration 2FA
    └── create_admin.html        # Création admin initial
```

### 3.2 Gestion des utilisateurs

#### 3.2.1 Structure utilisateur (users.json)
```json
{
  "username": "admin",
  "password_hash": "bcrypt_hash...",
  "totp_secret": "BASE32_SECRET",
  "2fa_enabled": true,
  "created_at": "2025-12-19T10:30:00"
}
```

#### 3.2.2 Fonctions principales
- `create_user(username, password)` - Création avec hash bcrypt
- `verify_password(username, password)` - Vérification bcrypt
- `verify_totp(username, token)` - Validation code TOTP
- `generate_new_2fa_secret(username)` - Génération nouveau secret
- `set_2fa_enabled(username, enable)` - Activation/désactivation 2FA
- `update_user(old_username, new_username, new_password)` - Mise à jour
- `delete_user(username)` - Suppression avec protections

#### 3.2.3 Workflow 2FA
1. **Activation:**
   - Génération secret TOTP (32 char base32)
   - Affichage QR code (modal interface admin)
   - Validation code → activation
   - Secret conservé tant que 2FA active

2. **Désactivation:**
   - Confirmation utilisateur
   - Génération nouveau secret (ancien oublié)
   - Désactivation flag 2FA

3. **Connexion:**
   - Étape 1: Vérification username/password
   - Étape 2 (si 2FA): Validation code TOTP (window=1)

### 3.3 Routes HTTP principales

#### 3.3.1 Authentification
```python
GET  /                           # Redirection selon état
GET  /login                      # Page connexion
POST /login                      # Traitement connexion
GET  /logout                     # Déconnexion
GET  /create_admin               # Création premier admin
POST /create_admin               # Traitement création admin
GET  /setup_2fa                  # Configuration 2FA
POST /setup_2fa                  # Activation 2FA
```

#### 3.3.2 Interface principale
```python
GET  /manager                    # Interface gestionnaire (protégée)
GET  /display                    # Interface client display
```

#### 3.3.3 API REST
```python
# Gestion utilisateurs
GET    /api/users                # Liste utilisateurs
POST   /api/users                # Création utilisateur
PUT    /api/users/<username>     # Modification (nom/MDP)
DELETE /api/users/<username>     # Suppression
POST   /api/users/<username>/toggle-2fa  # Toggle 2FA

# Configuration
GET    /api/settings             # Récupération paramètres
POST   /api/settings             # Sauvegarde paramètres

# Mise à jour système
GET    /api/check-update         # Vérification MAJ disponible
POST   /api/apply-update         # Application MAJ (git pull)

# Upload
POST   /api/upload-image         # Upload image
GET    /api/youtube-metadata/<video_id>  # Métadonnées YouTube
```

### 3.4 WebSocket - Événements Socket.IO

#### 3.4.1 Client → Serveur
```python
# Enregistrement
'register_screen'        # Enregistrement écran display
  → { id, name, location, config }

# État
'get_state'             # Demande état complet système

# Gestion contenu
'add_content'           # Ajout contenu bibliothèque
'update_content'        # Modification contenu
'delete_content'        # Suppression contenu

# Affichage
'display_content'       # Affichage contenu sur écran(s)
  → { screen_id, content_id, duration }
'clear_screen'          # Effacement écran
'bulk_display'          # Affichage multiple écrans

# Playlists
'create_playlist'       # Création playlist
'update_playlist'       # Modification playlist
'delete_playlist'       # Suppression playlist
'start_playlist'        # Lancement manuel playlist
  → { screen_id, playlist_id, duration, priority }

# Planning
'update_schedule'       # Mise à jour planning écran
  → { screen_id, schedule }

# Configuration écran
'update_screen_config'  # Maj config écran (ex: horloge)
  → { screen_id, config }
```

#### 3.4.2 Serveur → Client(s)
```python
# Broadcast général
'state_update'          # Diffusion état complet
  → { screens, content_library, playlists, schedules }

# Commandes display
'show_content'          # Affichage contenu
  → { content, duration }
'clear_content'         # Effacement affichage
'start_playlist'        # Démarrage playlist
  → { playlist, duration, isPriority }
'update_schedule'       # Mise à jour planning
  → { schedule }
'send_full_playlist_list'  # Envoi liste complète playlists
  → { playlists }
'config_updated'        # Configuration modifiée
  → { config }
```

### 3.5 Structures de données

#### 3.5.1 Écran (screens.json)
```json
{
  "ecran1": {
    "id": "ecran1",
    "name": "Cuisine",
    "location": "RDC",
    "status": "online",
    "current_content": null,
    "current_playlist": null,
    "sid": "socket_id_xyz",
    "last_seen": "2025-12-19T10:30:00",
    "config": {
      "show_clock": true,
      "brightness": 100
    }
  }
}
```

#### 3.5.2 Contenu (content.json)
```json
{
  "id": "1734607200000",
  "name": "Météo",
  "type": "url",
  "url": "https://meteo.example.com",
  "duration": 30
}
```

Types supportés:
- `url` - Page web (iframe)
- `video` - Vidéo (HTML5 video)
- `image` - Image (img tag)
- `youtube` - Vidéo YouTube (iframe autoplay)

#### 3.5.3 Playlist (playlists.json)
```json
{
  "playlist_123": {
    "id": "playlist_123",
    "name": "Informations",
    "items": [
      {
        "content": { /* objet contenu */ },
        "duration": 20
      }
    ],
    "created_at": "2025-12-19T10:00:00"
  }
}
```

#### 3.5.4 Planning (schedules.json)
```json
{
  "ecran1": [
    {
      "start": "08:00",
      "end": "12:00",
      "playlist_id": "playlist_123"
    }
  ]
}
```

---

## 4. Frontend - Architecture détaillée

### 4.1 Manager (manager.html)

#### 4.1.1 Composants principaux
1. **Header:**
   - Menu Alimentation (power-menu)
     - Redémarrer service
     - Arrêter service
     - Déconnexion
   - Badge mise à jour
   - Bouton Paramètres

2. **Section Écrans:**
   - Liste écrans temps réel
   - Indicateur statut (online/offline)
   - Boutons actions (afficher, effacer, playlist)
   - Configuration écran (horloge, etc.)

3. **Section Bibliothèque:**
   - Liste contenus avec filtres
   - Boutons actions (modifier, supprimer, afficher)
   - Modal ajout/modification contenu

4. **Section Playlists:**
   - Liste playlists
   - Éditeur playlist drag & drop
   - Gestion durées individuelles

5. **Section Planning:**
   - Vue planning par écran
   - Éditeur horaires
   - Association playlist/horaire

6. **Modal Paramètres:**
   - Configuration YouTube API
   - Gestion utilisateurs
     - Liste avec tri (utilisateur connecté en premier)
     - CRUD utilisateurs
     - Gestion 2FA (uniquement pour soi-même)

#### 4.1.2 État global JavaScript
```javascript
let screens = {};              // État écrans
let content_library = [];      // Bibliothèque contenus
let playlists = {};           // Playlists disponibles
let schedules = {};           // Plannings
let currentUsers = [];        // Utilisateurs (modal params)
let currentUserUsername = ''; // Utilisateur connecté
```

#### 4.1.3 Fonctions principales
```javascript
// WebSocket
socket.on('state_update', updateUI)
socket.emit('display_content', data)

// Gestion contenu
addContent(type, name, url, duration)
updateContent(id, data)
deleteContent(id)

// Gestion playlists
createPlaylist(name, items)
editPlaylist(id)
deletePlaylist(id)
startPlaylistOnScreen(screenId, playlistId, duration, priority)

// Gestion planning
updateSchedule(screenId, schedule)

// Gestion utilisateurs
loadUsers()
displayUsersList()  // Tri: utilisateur connecté en premier
openCreateUserModal()
openEditUserModal(username)
submitUserForm()    // Création ou modification
deleteUser(username)
toggleUser2FA(username, enable)
```

### 4.2 Display (display.html)

#### 4.2.1 Paramètres URL
```
/display?id=ecran1&name=Cuisine&location=RDC
```
- `id` (requis): Identifiant unique
- `name` (optionnel): Nom affichage
- `location` (optionnel): Localisation

#### 4.2.2 Composants
1. **Container principal:**
   - Zone affichage contenu
   - Overlay horloge (configurable)
   - Indicateur mode prioritaire

2. **Debug panel:**
   - Informations temps réel
   - État playlist/contenu
   - Logs système

#### 4.2.3 État local JavaScript
```javascript
let screenId = '';                    // ID écran
let currentPlaylist = [];             // Playlist en cours
let currentPlaylistIndex = 0;         // Index item actuel
let currentPlaylistId = null;         // ID playlist
let isPriorityActive = false;         // Mode prioritaire
let activeScheduledPlaylistId = null; // Playlist planning active
let playlistInterval = null;          // Timer items
let contentTimeout = null;            // Timer contenu
```

#### 4.2.4 Logique de priorité
1. **Contenu/Playlist prioritaire:**
   - Flag `isPriorityActive = true`
   - Bloque interventions planning
   - Nécessite effacement manuel

2. **Contenu planifié:**
   - Vérification toutes les 30s
   - Lancement automatique selon horaires
   - Arrêt automatique hors plage horaire

3. **Gestion configuration:**
   - Modification config (ex: horloge) sans interruption si prioritaire/planifié

#### 4.2.5 Workflow affichage contenu
```javascript
// Contenu simple
showContent(content, duration) {
  1. Clear timeouts existants
  2. Générer HTML selon type
  3. Injecter dans container
  4. Si duration > 0: setTimeout pour effacer
}

// Playlist
startPlaylist(playlist, duration, isPriority) {
  1. Stocker variables globales
  2. Si duration global: setTimeout arrêt complet
  3. Lancer premier item: playNextInPlaylist()
}

playNextInPlaylist() {
  1. Récupérer item actuel
  2. showContent(item.content, item.duration)
  3. setTimeout vers item suivant (ou loop)
}
```

---

## 5. Sécurité

### 5.1 Authentification

#### 5.1.1 Mots de passe
- **Hashing:** bcrypt (salt automatique)
- **Stockage:** Hash uniquement, jamais clair
- **Validation:** Minimum 8 caractères

#### 5.1.2 Double authentification (2FA)
- **Protocole:** TOTP (RFC 6238)
- **Algorithme:** SHA-1
- **Window:** ±1 période (30s)
- **Secret:** Base32, 32 caractères
- **QR Code:** Provisioning URI standard

#### 5.1.3 Sessions
- **Gestion:** Flask sessions (cookie signé)
- **Secret key:** Configurable (`app.config['SECRET_KEY']`)
- **Protection:** `@login_required` decorator sur routes sensibles

### 5.2 Protection des routes

#### 5.2.1 Routes publiques
- `/login` (GET/POST)
- `/create_admin` (GET/POST) - Uniquement si aucun utilisateur

#### 5.2.2 Routes protégées
Toutes les autres routes nécessitent authentification:
- Vérification `session['username']`
- Redirection `/login` si non authentifié

### 5.3 Validation des entrées

#### 5.3.1 Côté serveur
```python
# Validation username
username.strip()  # Trim espaces
len(username) > 0 # Non vide

# Validation mot de passe
len(password) >= 8

# Validation 2FA
pattern="[0-9]{6}"  # 6 chiffres
totp.verify(code, valid_window=1)
```

#### 5.3.2 Côté client
```html
<!-- Pattern HTML5 -->
<input pattern="[0-9]{6}" maxlength="6">

<!-- Validation JavaScript -->
if (!password || password.length < 8) return error;
if (password !== passwordConfirm) return error;
```

### 5.4 Permissions utilisateurs

#### 5.4.1 Gestion utilisateurs
- **Création:** Tout utilisateur connecté
- **Modification nom/MDP:** Tout utilisateur (même les autres)
- **Suppression:** Interdite si utilisateur courant ou dernier utilisateur
- **Activation 2FA:** Uniquement pour soi-même
- **Désactivation 2FA:** Tout utilisateur (admin reset)

#### 5.4.2 Vérifications backend
```python
# Suppression
if session.get('username') == username:
    return error("Impossible supprimer son compte")
if len(users) <= 1:
    return error("Impossible supprimer dernier utilisateur")

# Activation 2FA
if enable and session.get('username') != username:
    return error("Activation 2FA uniquement pour soi")
```

### 5.5 Points d'attention sécurité

⚠️ **À améliorer pour production:**

1. **Secret key:**
   ```python
   # Actuel (développement)
   app.config['SECRET_KEY'] = 'votre-cle-secrete-ici'

   # Production recommandée
   app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
   ```

2. **CORS:**
   ```python
   # Actuel (développement)
   socketio = SocketIO(app, cors_allowed_origins="*")

   # Production recommandée
   socketio = SocketIO(app, cors_allowed_origins=[
       "https://domain.com"
   ])
   ```

3. **HTTPS:**
   - Déploiement production: Utiliser reverse proxy (nginx/Apache)
   - Certificat SSL/TLS obligatoire

4. **Rate limiting:**
   - Implémenter limitation tentatives login
   - Protection brute force

---

## 6. Déploiement

### 6.1 Prérequis

#### 6.1.1 Serveur central
- Python 3.8+
- Réseau accessible par displays
- Port 5000 disponible (ou configuré)

#### 6.1.2 Clients display (Raspberry Pi)
- Raspberry Pi 3/4/5
- Raspbian OS
- Chromium browser
- Réseau stable vers serveur

### 6.2 Installation serveur

```bash
curl -fsSL https://raw.githubusercontent.com/sh4dow0666/digital-signage/main/bootstrap.sh | bash
```

#### 6.2.1 Service systemd (optionnel)
```ini
[Unit]
Description=DS MCO Display Manager
After=network.target

[Service]
Type=simple
User=user
WorkingDirectory=/home/user/DS
ExecStart=/home/user/DS/venv/bin/python gestion_raspberry.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 6.3 Configuration clients display

#### 6.3.1 Lancement Chromium kiosk
```bash
chromium-browser --kiosk --noerrdialogs \
  --disable-infobars \
  --disable-session-crashed-bubble \
  "http://SERVER_IP:5000/display?id=ecran1&name=Cuisine&location=RDC"
```

#### 6.3.2 Auto-start (autostart desktop)
```bash
# ~/.config/lxsession/LXDE-pi/autostart
@chromium-browser --kiosk --noerrdialogs \
  "http://SERVER_IP:5000/display?id=ecran1&name=Cuisine&location=RDC"
```

### 6.4 Mise à jour système

#### 6.4.1 Via interface web
1. Clic bouton "🔄 Mise à jour disponible" (si affiché)
2. Vérification mises à jour
3. Clic "Installer la mise à jour"
4. Redémarrage service recommandé

#### 6.4.2 Processus backend
```python
# Vérification
git fetch origin main
git rev-list --count HEAD..origin/main  # Commits en retard

# Application
git pull origin main
# + rsync vers /opt/digital-signage si applicable
```

---

## 7. Performances et optimisations

### 7.1 Backend

#### 7.1.1 Socket.IO
- **Événements ciblés:** Émission vers SID spécifique plutôt que broadcast
- **State updates:** Envoi uniquement si changement réel
- **Heartbeat:** Détection déconnexion automatique

#### 7.1.2 Fichiers JSON
- **Lecture:** À la demande (non en mémoire constante)
- **Écriture:** Atomic write (sécurité corruption)
- **Taille:** Limitée (pas de pagination nécessaire)

### 7.2 Frontend

#### 7.2.1 Manager
- **DOM Updates:** Minimisation reflow (innerHTML batch)
- **Event listeners:** Delegation si multiple éléments
- **Modals:** Lazy load si contenu lourd

#### 7.2.2 Display
- **Video autoplay:** Politique navigateur respectée
- **Iframe:** Sandbox pour isolation
- **Timers:** Cleanup systématique (memory leaks)

### 7.3 Réseau

#### 7.3.1 WebSocket
- **Reconnexion:** Automatique (Socket.IO)
- **Compression:** Activable via nginx/Apache

#### 7.3.2 Médias
- **Images uploadées:** Limite 50MB
- **YouTube:** Embed uniquement (pas de téléchargement)
- **Vidéos:** Servies via static (pas de streaming)

---

## 8. Maintenance et monitoring

### 8.1 Logs

#### 8.1.1 Serveur
```python
print(f"✅ {message}")  # Succès
print(f"⚠️ {message}")  # Avertissement
print(f"❌ {message}")  # Erreur
```

#### 8.1.2 Display
- Console JavaScript (F12)
- Debug panel (visible sur display)

### 8.2 Santé du système

#### 8.2.1 Indicateurs serveur
- Nombre écrans connectés
- Dernier heartbeat écrans
- Erreurs Socket.IO

#### 8.2.2 Indicateurs display
- Statut connexion (online/offline)
- Playlist active
- Erreurs chargement contenu

### 8.3 Sauvegarde

#### 8.3.1 Données critiques
```bash
# Sauvegarde complète
tar -czf backup_$(date +%Y%m%d).tar.gz data/

# Restauration
tar -xzf backup_YYYYMMDD.tar.gz
```

#### 8.3.2 Fichiers à sauvegarder
- `data/*.json` (tous)
- `static/uploads/*` (images)
- Configuration serveur (si custom)

---

## 9. Évolutions futures

### 9.1 Fonctionnalités
- [ ] Statistiques affichage (vues, durées)
- [ ] Templates playlists
- [ ] Multi-zones (split screen)
- [ ] Gestion rôles utilisateurs (admin/user)
- [ ] API REST complète pour intégrations
- [ ] Support audio
- [ ] Flux RTSP/streaming

### 9.2 Technique
- [ ] Migration base de données (SQLite/PostgreSQL)
- [ ] Cache Redis pour performances
- [ ] Clustering serveurs (HA)
- [ ] CDN pour médias
- [ ] Tests automatisés (pytest)
- [ ] CI/CD pipeline
- [ ] Monitoring (Prometheus/Grafana)
- [ ] Logs structurés (JSON)

### 9.3 Sécurité
- [ ] Authentification OAuth2/SAML
- [ ] Chiffrement end-to-end
- [ ] Audit logs
- [ ] CSP (Content Security Policy)
- [ ] Rate limiting
- [ ] Backup automatique

---

## 10. Annexes

### 10.1 Dépendances Python (requirements.txt)

```
flask>=2.0.0
flask-socketio>=5.0.0
python-engineio>=4.0.0
python-socketio>=5.0.0
requests>=2.25.0
isodate>=0.6.0
pyotp>=2.9.0
bcrypt>=4.0.0
qrcode>=7.4.0
pillow>=10.0.0
```

### 10.2 Variables d'environnement recommandées

```bash
# Production
export SECRET_KEY="random_secret_key_here"
export FLASK_ENV="production"
export SERVER_PORT="5000"
export ALLOWED_ORIGINS="https://domain.com"

# Développement
export FLASK_ENV="development"
export FLASK_DEBUG="1"
```

### 10.3 Ports utilisés

- **5000** - HTTP/WebSocket serveur Flask (configurable)
- **80/443** - Si reverse proxy (production)

### 10.4 Compatibilité navigateurs

#### Manager
- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

#### Display
- Chromium 90+ (Raspberry Pi)

### 10.5 Ressources matérielles

#### Serveur minimal
- CPU: 2 cores
- RAM: 2GB
- Disque: 10GB
- Réseau: 100Mbps

#### Serveur recommandé (50+ écrans)
- CPU: 4 cores
- RAM: 4GB
- Disque: 50GB SSD
- Réseau: 1Gbps

#### Raspberry Pi (Display)
- Modèle: Pi 3B+ minimum, Pi 4/5 recommandé
- RAM: 2GB minimum, 4GB recommandé
- Stockage: 16GB SD card minimum

---

## 11. Contact et support

**Projet:** DS MCO - Digital Signage Management
**Documentation:** CLAUDE.md (instructions projet)
**Architecture:** DAT.md (ce document)

**Maintenance:**
- Vérifier logs serveur régulièrement
- Sauvegarder données hebdomadairement
- Tester mises à jour en environnement test
- Surveiller espace disque (uploads)

---

**Fin du Document d'Architecture Technique**
*Document généré automatiquement - Version 2.0*
