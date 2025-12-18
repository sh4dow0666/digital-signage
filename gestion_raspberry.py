"""
Système de gestion d'affichage pour Raspberry Pi
Interface web pour contrôler plusieurs écrans à distance
VERSION CORRIGÉE - Playlists fonctionnelles
"""

from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for, flash
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
from functools import wraps
import json
import os
from datetime import datetime
import requests
import re
import isodate
import subprocess
import bcrypt
import pyotp
import qrcode
import io
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre-cle-secrete-ici'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max file size
socketio = SocketIO(app, cors_allowed_origins="*")

# Fichiers de sauvegarde
DATA_DIR = 'data'
SCREENS_FILE = os.path.join(DATA_DIR, 'screens.json')
CONTENT_FILE = os.path.join(DATA_DIR, 'content.json')
PLAYLISTS_FILE = os.path.join(DATA_DIR, 'playlists.json')
SCHEDULES_FILE = os.path.join(DATA_DIR, 'schedules.json')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')

# Dossier pour les uploads
UPLOAD_DIR = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg'}

# Créer les dossiers s'ils n'existent pas
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ===== GESTION UTILISATEURS ET AUTHENTIFICATION =====

def load_users():
    """Charge les utilisateurs depuis le fichier"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Erreur lors du chargement des utilisateurs: {e}")
    return []

def save_users(users):
    """Sauvegarde les utilisateurs dans le fichier"""
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"⚠️ Erreur lors de la sauvegarde des utilisateurs: {e}")
        return False

def create_user(username, password):
    """Crée un nouvel utilisateur avec un mot de passe haché"""
    users = load_users()

    # Vérifier si l'utilisateur existe déjà
    if any(u['username'] == username for u in users):
        return None, "L'utilisateur existe déjà"

    # Hasher le mot de passe
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Générer un secret pour 2FA
    totp_secret = pyotp.random_base32()

    user = {
        'username': username,
        'password_hash': password_hash,
        'totp_secret': totp_secret,
        '2fa_enabled': False,
        'created_at': datetime.now().isoformat()
    }

    users.append(user)
    save_users(users)

    return user, None

def verify_password(username, password):
    """Vérifie le mot de passe d'un utilisateur"""
    users = load_users()
    user = next((u for u in users if u['username'] == username), None)

    if not user:
        return False

    return bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8'))

def verify_totp(username, token):
    """Vérifie le code TOTP (Google Authenticator)"""
    users = load_users()
    user = next((u for u in users if u['username'] == username), None)

    if not user or not user.get('2fa_enabled'):
        return True  # Si 2FA n'est pas activé, considérer comme valide

    totp = pyotp.TOTP(user['totp_secret'])
    return totp.verify(token, valid_window=1)

def enable_2fa(username):
    """Active la 2FA pour un utilisateur"""
    users = load_users()
    for user in users:
        if user['username'] == username:
            user['2fa_enabled'] = True
            save_users(users)
            return True
    return False

def get_user(username):
    """Récupère un utilisateur par son nom"""
    users = load_users()
    return next((u for u in users if u['username'] == username), None)

def update_user_password(username, new_password):
    """Met à jour le mot de passe d'un utilisateur"""
    users = load_users()
    for user in users:
        if user['username'] == username:
            user['password_hash'] = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            save_users(users)
            return True
    return False

def update_user(old_username, new_username=None, new_password=None):
    """Met à jour le nom d'utilisateur et/ou le mot de passe d'un utilisateur"""
    users = load_users()

    # Vérifier si le nouveau nom d'utilisateur existe déjà (si différent de l'ancien)
    if new_username and new_username != old_username:
        if any(u['username'] == new_username for u in users):
            return False, "Ce nom d'utilisateur est déjà utilisé"

    for user in users:
        if user['username'] == old_username:
            # Mettre à jour le nom d'utilisateur si fourni
            if new_username and new_username != old_username:
                user['username'] = new_username

            # Mettre à jour le mot de passe si fourni
            if new_password:
                user['password_hash'] = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            save_users(users)
            return True, new_username if new_username else old_username

    return False, "Utilisateur introuvable"

def delete_user(username):
    """Supprime un utilisateur"""
    users = load_users()
    users = [u for u in users if u['username'] != username]
    save_users(users)
    return True

def toggle_user_2fa(username, enable):
    """Active ou désactive la 2FA pour un utilisateur"""
    users = load_users()
    for user in users:
        if user['username'] == username:
            # Toujours générer un nouveau secret (que ce soit pour activer ou désactiver)
            user['totp_secret'] = pyotp.random_base32()
            user['2fa_enabled'] = enable
            save_users(users)
            return True
    return False

def generate_new_2fa_secret(username):
    """Génère un nouveau secret 2FA pour un utilisateur (sans changer le statut enabled)"""
    users = load_users()
    for user in users:
        if user['username'] == username:
            user['totp_secret'] = pyotp.random_base32()
            save_users(users)
            return True
    return False

def set_2fa_enabled(username, enable):
    """Active ou désactive la 2FA pour un utilisateur (sans toucher au secret)"""
    users = load_users()
    for user in users:
        if user['username'] == username:
            user['2fa_enabled'] = enable
            save_users(users)
            return True
    return False

def login_required(f):
    """Decorator pour protéger les routes nécessitant une authentification"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ===== FIN GESTION UTILISATEURS =====

# Stockage en mémoire
screens = {}
content_library = []
playlists = {}  # Format: {playlist_id: {name, items, created_at}}
schedules = {}  # Format: {screen_id: [{start, end, playlist_id}]}

def load_data():
    """Charge les données depuis les fichiers"""
    global screens, content_library, playlists, schedules
    
    # Charger les contenus
    if os.path.exists(CONTENT_FILE):
        try:
            with open(CONTENT_FILE, 'r', encoding='utf-8') as f:
                content_library = json.load(f)
            print(f"✅ {len(content_library)} contenu(s) chargé(s)")
        except Exception as e:
            print(f"⚠️ Erreur lors du chargement des contenus: {e}")
            content_library = []
    
    # Charger les écrans
    if os.path.exists(SCREENS_FILE):
        try:
            with open(SCREENS_FILE, 'r', encoding='utf-8') as f:
                saved_screens = json.load(f)
                for screen_id, screen_data in saved_screens.items():
                    screens[screen_id] = {
                        'id': screen_data.get('id', screen_id),
                        'name': screen_data.get('name', f'Écran {screen_id}'),
                        'location': screen_data.get('location', 'Non défini'),
                        'default_content_id': screen_data.get('default_content_id', None),
                        'idle_behavior': screen_data.get('idle_behavior', 'show_default'),
                        'show_clock': screen_data.get('show_clock', False),
                        'status': 'offline',
                        'current_content': None,
                        'last_seen': None,
                        'sid': None
                    }
            print(f"✅ {len(screens)} écran(s) chargé(s)")
        except Exception as e:
            print(f"⚠️ Erreur lors du chargement des écrans: {e}")
            screens = {}
    
    # Charger les playlists
    if os.path.exists(PLAYLISTS_FILE):
        try:
            with open(PLAYLISTS_FILE, 'r', encoding='utf-8') as f:
                playlists = json.load(f)
            print(f"✅ {len(playlists)} playlist(s) chargée(s)")
        except Exception as e:
            print(f"⚠️ Erreur lors du chargement des playlists: {e}")
            playlists = {}
    
    # Charger les plannings
    if os.path.exists(SCHEDULES_FILE):
        try:
            with open(SCHEDULES_FILE, 'r', encoding='utf-8') as f:
                schedules = json.load(f)
            print(f"✅ Planning chargé pour {len(schedules)} écran(s)")
        except Exception as e:
            print(f"⚠️ Erreur lors du chargement des plannings: {e}")
            schedules = {}

def save_content():
    """Sauvegarde les contenus"""
    try:
        with open(CONTENT_FILE, 'w', encoding='utf-8') as f:
            json.dump(content_library, f, ensure_ascii=False, indent=2)
        print(f"💾 Contenus sauvegardés: {len(content_library)} élément(s)")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde des contenus: {e}")

def save_screens():
    """Sauvegarde les informations des écrans"""
    try:
        screens_to_save = {}
        for screen_id, screen_data in screens.items():
            screens_to_save[screen_id] = {
                'id': screen_data['id'],
                'name': screen_data['name'],
                'location': screen_data['location'],
                'default_content_id': screen_data.get('default_content_id', None),
                'idle_behavior': screen_data.get('idle_behavior', 'show_default'),
                'show_clock': screen_data.get('show_clock', False)
            }

        with open(SCREENS_FILE, 'w', encoding='utf-8') as f:
            json.dump(screens_to_save, f, ensure_ascii=False, indent=2)
        print(f"💾 Écrans sauvegardés: {len(screens_to_save)} élément(s)")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde des écrans: {e}")

def save_playlists():
    """Sauvegarde les playlists"""
    try:
        with open(PLAYLISTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(playlists, f, ensure_ascii=False, indent=2)
        print(f"💾 Playlists sauvegardées: {len(playlists)} élément(s)")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde des playlists: {e}")

def save_schedules():
    """Sauvegarde les plannings"""
    try:
        with open(SCHEDULES_FILE, 'w', encoding='utf-8') as f:
            json.dump(schedules, f, ensure_ascii=False, indent=2)
        print(f"💾 Plannings sauvegardés")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde des plannings: {e}")

# Charger les données au démarrage
load_data()

# ===== ROUTES D'AUTHENTIFICATION =====

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion avec support 2FA"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        totp_code = request.form.get('totp_code')

        # Étape 1: Vérification username + password
        if not totp_code:
            if verify_password(username, password):
                user = get_user(username)
                if user and user.get('2fa_enabled'):
                    # 2FA activé, demander le code et afficher le QR code
                    session['pending_username'] = username

                    # Générer le QR code
                    totp_uri = pyotp.TOTP(user['totp_secret']).provisioning_uri(
                        name=username,
                        issuer_name='DS MCO'
                    )
                    qr = qrcode.QRCode(version=1, box_size=10, border=5)
                    qr.add_data(totp_uri)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="black", back_color="white")
                    buffer = io.BytesIO()
                    img.save(buffer, format='PNG')
                    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

                    return render_template('login.html',
                                         show_2fa_step=True,
                                         info="Entrez votre code d'authentification",
                                         qr_code=f'data:image/png;base64,{qr_base64}',
                                         secret=user['totp_secret'])
                else:
                    # Pas de 2FA, connexion directe
                    session['username'] = username
                    return redirect(url_for('index'))
            else:
                return render_template('login.html', error="Nom d'utilisateur ou mot de passe incorrect")

        # Étape 2: Vérification du code 2FA
        else:
            pending_username = session.get('pending_username')
            if not pending_username:
                return render_template('login.html', error="Session expirée, veuillez recommencer")

            if verify_totp(pending_username, totp_code):
                session['username'] = pending_username
                session.pop('pending_username', None)
                return redirect(url_for('index'))
            else:
                # Régénérer le QR code pour le réafficher en cas d'erreur
                user = get_user(pending_username)
                if user:
                    totp_uri = pyotp.TOTP(user['totp_secret']).provisioning_uri(
                        name=pending_username,
                        issuer_name='DS MCO'
                    )
                    qr = qrcode.QRCode(version=1, box_size=10, border=5)
                    qr.add_data(totp_uri)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="black", back_color="white")
                    buffer = io.BytesIO()
                    img.save(buffer, format='PNG')
                    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

                    return render_template('login.html',
                                         show_2fa_step=True,
                                         error="Code d'authentification incorrect",
                                         qr_code=f'data:image/png;base64,{qr_base64}',
                                         secret=user['totp_secret'])
                else:
                    return render_template('login.html', show_2fa_step=True, error="Code d'authentification incorrect")

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Déconnexion"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/setup_2fa', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    """Configuration de la double authentification"""
    username = session.get('username')
    user = get_user(username)

    if not user:
        return redirect(url_for('login'))

    # Générer le QR code
    totp_uri = pyotp.TOTP(user['totp_secret']).provisioning_uri(
        name=username,
        issuer_name='DS MCO'
    )

    # Créer le QR code en base64
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Convertir en base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    if request.method == 'POST':
        totp_code = request.form.get('totp_code')

        if verify_totp(username, totp_code):
            enable_2fa(username)
            # Ajouter un message de succès
            flash('✅ Double authentification activée avec succès!', 'success')
            # Rediriger vers l'index après activation réussie
            return redirect(url_for('index'))
        else:
            return render_template('setup_2fa.html',
                                   qr_code=qr_base64,
                                   secret_key=user['totp_secret'],
                                   error="Code incorrect, veuillez réessayer")

    return render_template('setup_2fa.html',
                           qr_code=qr_base64,
                           secret_key=user['totp_secret'])

@app.route('/create_admin', methods=['GET', 'POST'])
def create_admin():
    """Création du premier utilisateur administrateur"""
    users = load_users()

    # Si des utilisateurs existent déjà, rediriger vers login
    if users:
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        if not username or not password:
            return render_template('create_admin.html', error="Veuillez remplir tous les champs")

        if password != password_confirm:
            return render_template('create_admin.html', error="Les mots de passe ne correspondent pas")

        if len(password) < 8:
            return render_template('create_admin.html', error="Le mot de passe doit contenir au moins 8 caractères")

        user, error = create_user(username, password)

        if error:
            return render_template('create_admin.html', error=error)

        # Connexion automatique et redirection vers setup 2FA
        session['username'] = username
        return redirect(url_for('setup_2fa'))

    return render_template('create_admin.html')

# ===== FIN ROUTES D'AUTHENTIFICATION =====

@app.route('/')
def index():
    """Route racine qui vérifie s'il faut créer un admin ou se connecter"""
    users = load_users()

    # Si aucun utilisateur n'existe, rediriger vers la création admin
    if not users:
        return redirect(url_for('create_admin'))

    # Si pas connecté, rediriger vers login
    if 'username' not in session:
        return redirect(url_for('login'))

    # Sinon, rediriger vers le manager
    return redirect(url_for('manager'))

@app.route('/manager')
@login_required
def manager():
    """Interface de gestion"""
    return render_template("manager.html")

@app.route('/display')
def display():
    """Page d'affichage pour les Raspberry Pi"""
    return render_template("display.html")

@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    """Upload une image et retourne l'URL"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Aucun fichier fourni'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Nom de fichier vide'
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'Type de fichier non autorisé. Extensions autorisées: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Créer un nom de fichier unique avec timestamp
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{name}_{timestamp}{ext}"

        # Sauvegarder le fichier
        filepath = os.path.join(UPLOAD_DIR, unique_filename)
        file.save(filepath)

        # Retourner l'URL relative
        url = f"/static/uploads/{unique_filename}"

        print(f"✅ Image uploadée: {unique_filename}")

        return jsonify({
            'success': True,
            'url': url,
            'filename': unique_filename
        })

    except Exception as e:
        print(f"❌ Erreur lors de l'upload: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erreur lors de l\'upload: {str(e)}'
        }), 500

@app.route('/api/youtube-metadata/<video_id>')
def get_youtube_metadata(video_id):
    """Récupère les métadonnées d'une vidéo YouTube"""
    # Lire la clé API depuis l'environnement ou un fichier de config
    api_key = os.environ.get('YOUTUBE_API_KEY', '')

    if not api_key:
        # Essayer de lire depuis un fichier de config
        config_file = os.path.join(DATA_DIR, 'config.json')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    api_key = config.get('youtube_api_key', '')
            except:
                pass

    if not api_key:
        return jsonify({
            'error': 'Clé API YouTube non configurée',
            'help': 'Créez un fichier data/config.json avec: {"youtube_api_key": "VOTRE_CLE_API"}'
        }), 400

    # Appeler l'API YouTube
    url = f'https://www.googleapis.com/youtube/v3/videos?id={video_id}&part=snippet,contentDetails&key={api_key}'

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get('items'):
            return jsonify({'error': 'Vidéo non trouvée'}), 404

        video_info = data['items'][0]
        title = video_info['snippet']['title']
        duration_iso = video_info['contentDetails']['duration']

        # Convertir la durée ISO 8601 en secondes
        duration_seconds = int(isodate.parse_duration(duration_iso).total_seconds())

        return jsonify({
            'title': title,
            'duration': duration_seconds,
            'thumbnail': video_info['snippet']['thumbnails']['default']['url']
        })

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Erreur lors de la requête à l\'API YouTube: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Erreur lors du traitement des données: {str(e)}'}), 500

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Récupère les paramètres de configuration"""
    config_file = os.path.join(DATA_DIR, 'config.json')
    settings = {
        'youtube_api_key': ''
    }

    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                settings['youtube_api_key'] = config.get('youtube_api_key', '')
        except Exception as e:
            print(f"⚠️ Erreur lors de la lecture de la configuration: {e}")

    return jsonify(settings)

@app.route('/api/settings', methods=['POST'])
def save_settings():
    """Sauvegarde les paramètres de configuration"""
    config_file = os.path.join(DATA_DIR, 'config.json')

    try:
        data = request.get_json()
        youtube_api_key = data.get('youtube_api_key', '')

        # Charger la config existante ou créer une nouvelle
        config = {}
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except:
                pass

        # Mettre à jour la clé API
        config['youtube_api_key'] = youtube_api_key

        # Sauvegarder
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        print(f"💾 Paramètres sauvegardés: Clé API YouTube {'configurée' if youtube_api_key else 'supprimée'}")

        return jsonify({'success': True, 'message': 'Paramètres sauvegardés avec succès'})

    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde des paramètres: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def get_git_repo_path():
    """Trouve le chemin du dépôt Git (normalement /home/$USER/DS)"""
    import pwd

    # Si on tourne depuis /opt/digital-signage, le dépôt Git est ailleurs
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Essayer de détecter l'utilisateur qui a lancé le service
    try:
        # Récupérer l'utilisateur qui possède le répertoire de travail
        stat_info = os.stat(current_dir)
        user_info = pwd.getpwuid(stat_info.st_uid)
        username = user_info.pw_name
    except:
        # Fallback: utiliser $USER ou l'utilisateur actuel
        username = os.environ.get('USER', 'pi')

    # Chercher le dépôt Git dans l'ordre de préférence
    possible_paths = [
        f'/home/{username}/DS',
        current_dir,  # Au cas où on soit déjà dans le dépôt
    ]

    for path in possible_paths:
        if os.path.exists(os.path.join(path, '.git')):
            return path

    return None

@app.route('/api/check-update', methods=['GET'])
def check_update():
    """Vérifie si une mise à jour est disponible depuis le dépôt Git"""
    try:
        # Trouver le dépôt Git
        git_repo_path = get_git_repo_path()

        if not git_repo_path:
            return jsonify({
                'available': False,
                'error': 'Dépôt Git introuvable. Vérifiez que le projet a été cloné dans /home/$USER/DS',
                'is_git_repo': False
            })

        # Vérifier que nous sommes dans un dépôt Git
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            cwd=git_repo_path,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return jsonify({
                'available': False,
                'error': f'{git_repo_path} n\'est pas un dépôt Git',
                'is_git_repo': False
            })

        # Récupérer les informations du dépôt distant
        subprocess.run(
            ['git', 'fetch'],
            cwd=git_repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )

        # Obtenir le hash du commit local
        local_result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=git_repo_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        local_hash = local_result.stdout.strip()

        # Obtenir le hash du commit distant
        remote_result = subprocess.run(
            ['git', 'rev-parse', '@{u}'],
            cwd=git_repo_path,
            capture_output=True,
            text=True,
            timeout=5
        )

        if remote_result.returncode != 0:
            return jsonify({
                'available': False,
                'error': 'Impossible de récupérer les informations du dépôt distant',
                'is_git_repo': True,
                'current_commit': local_hash[:7],
                'git_repo_path': git_repo_path
            })

        remote_hash = remote_result.stdout.strip()

        # Vérifier s'il y a des commits en avance
        if local_hash != remote_hash:
            # Compter le nombre de commits en retard
            commits_result = subprocess.run(
                ['git', 'rev-list', '--count', f'HEAD..@{{u}}'],
                cwd=git_repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            commits_behind = int(commits_result.stdout.strip()) if commits_result.returncode == 0 else 0

            # Obtenir le message du dernier commit distant
            log_result = subprocess.run(
                ['git', 'log', '@{u}', '-1', '--pretty=format:%s'],
                cwd=git_repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            latest_message = log_result.stdout.strip() if log_result.returncode == 0 else ''

            return jsonify({
                'available': True,
                'is_git_repo': True,
                'current_commit': local_hash[:7],
                'remote_commit': remote_hash[:7],
                'commits_behind': commits_behind,
                'latest_message': latest_message,
                'git_repo_path': git_repo_path
            })
        else:
            return jsonify({
                'available': False,
                'is_git_repo': True,
                'current_commit': local_hash[:7],
                'message': 'Vous êtes à jour',
                'git_repo_path': git_repo_path
            })

    except subprocess.TimeoutExpired:
        return jsonify({
            'available': False,
            'error': 'Timeout lors de la vérification de la mise à jour'
        }), 500
    except Exception as e:
        return jsonify({
            'available': False,
            'error': f'Erreur lors de la vérification: {str(e)}'
        }), 500

@app.route('/api/apply-update', methods=['POST'])
def apply_update():
    """Applique la mise à jour en effectuant un git pull et copie les fichiers vers /opt/digital-signage"""
    try:
        # Trouver le dépôt Git
        git_repo_path = get_git_repo_path()

        if not git_repo_path:
            return jsonify({
                'success': False,
                'error': 'Dépôt Git introuvable. Vérifiez que le projet a été cloné dans /home/$USER/DS'
            }), 400

        # Vérifier qu'il n'y a pas de modifications locales non commitées
        status_result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=git_repo_path,
            capture_output=True,
            text=True,
            timeout=5
        )

        if status_result.stdout.strip():
            return jsonify({
                'success': False,
                'error': 'Des modifications locales non commitées existent dans le dépôt Git. Veuillez les commiter ou les annuler avant de mettre à jour.'
            }), 400

        # Effectuer le git pull
        pull_result = subprocess.run(
            ['git', 'pull'],
            cwd=git_repo_path,
            capture_output=True,
            text=True,
            timeout=60
        )

        if pull_result.returncode != 0:
            return jsonify({
                'success': False,
                'error': f'Erreur lors du git pull: {pull_result.stderr}'
            }), 500

        # Obtenir le nouveau hash de commit
        hash_result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=git_repo_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        new_hash = hash_result.stdout.strip()

        print(f"✅ Git pull effectué avec succès: {new_hash[:7]}")

        # Copier les fichiers vers /opt/digital-signage si nécessaire
        install_dir = '/opt/digital-signage'
        current_dir = os.path.dirname(os.path.abspath(__file__))

        files_copied = False
        if current_dir.startswith(install_dir) and git_repo_path != install_dir:
            print(f"📝 Copie des fichiers de {git_repo_path} vers {install_dir}...")

            try:
                # Copier tous les fichiers sauf le dossier data et logs
                copy_result = subprocess.run(
                    [
                        'rsync', '-av', '--progress',
                        '--exclude', 'data/',
                        '--exclude', 'logs/',
                        '--exclude', '.git/',
                        '--exclude', '__pycache__/',
                        '--exclude', '*.pyc',
                        f'{git_repo_path}/',
                        f'{install_dir}/'
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if copy_result.returncode != 0:
                    # Si rsync n'est pas disponible, utiliser cp
                    print("⚠️ rsync non disponible, utilisation de cp...")
                    copy_result = subprocess.run(
                        ['cp', '-r', f'{git_repo_path}/.', install_dir],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )

                    if copy_result.returncode != 0:
                        return jsonify({
                            'success': False,
                            'error': f'Erreur lors de la copie des fichiers: {copy_result.stderr}'
                        }), 500

                files_copied = True
                print(f"✅ Fichiers copiés avec succès vers {install_dir}")

            except subprocess.TimeoutExpired:
                return jsonify({
                    'success': False,
                    'error': 'Timeout lors de la copie des fichiers'
                }), 500
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Erreur lors de la copie des fichiers: {str(e)}'
                }), 500

        return jsonify({
            'success': True,
            'message': 'Mise à jour appliquée avec succès',
            'new_commit': new_hash[:7],
            'output': pull_result.stdout,
            'files_copied': files_copied,
            'requires_restart': True  # Indiquer qu'un redémarrage peut être nécessaire
        })

    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Timeout lors de l\'application de la mise à jour'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur lors de l\'application de la mise à jour: {str(e)}'
        }), 500

# ===== ROUTES API GESTION UTILISATEURS =====

@app.route('/api/users', methods=['GET'])
@login_required
def get_users_api():
    """Récupère la liste des utilisateurs (sans les mots de passe)"""
    users = load_users()
    # Enlever les informations sensibles
    safe_users = []
    for user in users:
        safe_users.append({
            'username': user['username'],
            '2fa_enabled': user.get('2fa_enabled', False),
            'created_at': user.get('created_at', 'N/A')
        })
    return jsonify({
        'success': True,
        'users': safe_users,
        'current_user': session.get('username')
    })

@app.route('/api/users', methods=['POST'])
@login_required
def create_user_api():
    """Crée un nouvel utilisateur"""
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({
            'success': False,
            'error': 'Nom d\'utilisateur et mot de passe requis'
        }), 400

    if len(password) < 8:
        return jsonify({
            'success': False,
            'error': 'Le mot de passe doit contenir au moins 8 caractères'
        }), 400

    user, error = create_user(username, password)

    if error:
        return jsonify({
            'success': False,
            'error': error
        }), 400

    return jsonify({
        'success': True,
        'message': f'Utilisateur {username} créé avec succès'
    })

@app.route('/api/users/<username>', methods=['PUT'])
@login_required
def update_user_api(username):
    """Met à jour un utilisateur (nom d'utilisateur et/ou mot de passe)"""
    data = request.json
    new_username = data.get('username', '').strip()
    new_password = data.get('password', '')

    # Au moins un champ doit être fourni
    if not new_username and not new_password:
        return jsonify({
            'success': False,
            'error': 'Nouveau nom d\'utilisateur ou mot de passe requis'
        }), 400

    # Valider le nouveau nom d'utilisateur si fourni
    if new_username and len(new_username) == 0:
        return jsonify({
            'success': False,
            'error': 'Le nom d\'utilisateur ne peut pas être vide'
        }), 400

    # Valider le nouveau mot de passe si fourni
    if new_password and len(new_password) < 8:
        return jsonify({
            'success': False,
            'error': 'Le mot de passe doit contenir au moins 8 caractères'
        }), 400

    success, result = update_user(
        username,
        new_username if new_username else None,
        new_password if new_password else None
    )

    if success:
        # Si l'utilisateur a modifié son propre nom d'utilisateur, mettre à jour la session
        if session.get('username') == username and new_username and new_username != username:
            session['username'] = result

        changes = []
        if new_username and new_username != username:
            changes.append(f'nom d\'utilisateur → {result}')
        if new_password:
            changes.append('mot de passe')

        return jsonify({
            'success': True,
            'message': f'Modifications effectuées : {", ".join(changes)}',
            'new_username': result
        })
    else:
        return jsonify({
            'success': False,
            'error': result
        }), 400

@app.route('/api/users/<username>', methods=['DELETE'])
@login_required
def delete_user_api(username):
    """Supprime un utilisateur"""
    # Empêcher la suppression de l'utilisateur connecté
    if session.get('username') == username:
        return jsonify({
            'success': False,
            'error': 'Vous ne pouvez pas supprimer votre propre compte'
        }), 403

    # Vérifier qu'il reste au moins un utilisateur
    users = load_users()
    if len(users) <= 1:
        return jsonify({
            'success': False,
            'error': 'Impossible de supprimer le dernier utilisateur'
        }), 403

    if delete_user(username):
        return jsonify({
            'success': True,
            'message': f'Utilisateur {username} supprimé'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la suppression'
        }), 500

@app.route('/api/users/<username>/toggle-2fa', methods=['POST'])
@login_required
def toggle_2fa_api(username):
    """Active ou désactive la 2FA pour un utilisateur"""
    data = request.json
    enable = data.get('enable', False)
    totp_code = data.get('totp_code', '')

    # Vérifier que seul l'utilisateur lui-même peut ACTIVER sa 2FA
    # Mais tout le monde peut DÉSACTIVER la 2FA de n'importe quel utilisateur
    if enable and session.get('username') != username:
        return jsonify({
            'success': False,
            'error': 'Vous ne pouvez activer la 2FA que pour votre propre compte'
        }), 403

    # Si on active avec code TOTP, vérifier le code avant d'activer
    if enable and totp_code:
        user = get_user(username)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Utilisateur introuvable'
            }), 404

        # Vérifier le code TOTP directement (ne pas utiliser verify_totp car la 2FA n'est pas encore activée)
        totp = pyotp.TOTP(user['totp_secret'])
        if not totp.verify(totp_code, valid_window=1):
            return jsonify({
                'success': False,
                'error': 'Code d\'authentification invalide'
            }), 400

    # Si on désactive, le faire directement
    if not enable:
        if toggle_user_2fa(username, enable):
            return jsonify({
                'success': True,
                'message': f'Double authentification désactivée pour {username}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Utilisateur introuvable'
            }), 404

    # Si on active sans code TOTP (première étape), générer le QR code
    if enable and not totp_code:
        # Utiliser le secret existant (déjà généré à la création ou lors de la dernière désactivation)
        user = get_user(username)

        if not user:
            return jsonify({
                'success': False,
                'error': 'Utilisateur introuvable'
            }), 404

        # Générer l'URI pour Google Authenticator
        totp_uri = pyotp.TOTP(user['totp_secret']).provisioning_uri(
            name=username,
            issuer_name='DS MCO'
        )

        # Générer le QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # Convertir en base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return jsonify({
            'success': True,
            'needs_confirmation': True,
            'qr_code': f'data:image/png;base64,{qr_base64}',
            'secret': user['totp_secret']
        })

    # Si on active avec code TOTP (deuxième étape), activer la 2FA sans toucher au secret
    if enable and totp_code:
        if set_2fa_enabled(username, True):
            return jsonify({
                'success': True,
                'message': f'Double authentification activée pour {username}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Utilisateur introuvable'
            }), 404

# ===== FIN ROUTES API GESTION UTILISATEURS =====

@app.route('/restart-system', methods=['POST'])
def restart_system():
    """Redémarre le système après un délai"""
    import threading
    import time

    def delayed_restart():
        """Fonction exécutée en arrière-plan pour redémarrer le système"""
        time.sleep(2)  # Attendre 2 secondes pour que la réponse HTTP soit envoyée
        print("🔄 Redémarrage du système...")

        try:
            subprocess.run(
                ['sudo', 'reboot'],
                capture_output=True,
                text=True,
                timeout=10
            )
        except Exception as e:
            print(f"❌ Erreur lors du redémarrage du système: {str(e)}")

    try:
        print("🔄 Redémarrage du système programmé dans 2 secondes...")

        # Lancer le redémarrage dans un thread séparé
        restart_thread = threading.Thread(target=delayed_restart, daemon=True)
        restart_thread.start()

        # Retourner immédiatement la réponse au client
        return jsonify({
            'success': True,
            'message': 'Le redémarrage du système sera effectué dans 2 secondes.'
        })

    except Exception as e:
        print(f"❌ Erreur lors de la programmation du redémarrage du système: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erreur inattendue: {str(e)}'
        }), 500
    
@app.route('/stop-system', methods=['POST'])
def stop_system():
    """Arrête le système après un délai"""
    import threading
    import time

    def delayed_shutdown():
        """Fonction exécutée en arrière-plan pour arrêter le système"""
        time.sleep(2)  # Attendre 2 secondes pour que la réponse HTTP soit envoyée
        print("🛑 Arrêt du système...")

        try:
            subprocess.run(
                ['sudo', 'shutdown', 'now'],
                capture_output=True,
                text=True,
                timeout=10
            )
        except Exception as e:
            print(f"❌ Erreur lors de l'arrêt du système: {str(e)}")

    try:
        print("🛑 Arrêt du système programmé dans 2 secondes...")

        # Lancer l'arrêt dans un thread séparé
        shutdown_thread = threading.Thread(target=delayed_shutdown, daemon=True)
        shutdown_thread.start()

        # Retourner immédiatement la réponse au client
        return jsonify({
            'success': True,
            'message': 'L\'arrêt du système sera effectué dans 2 secondes.'
        })

    except Exception as e:
        print(f"❌ Erreur lors de la programmation de l'arrêt du système: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erreur inattendue: {str(e)}'
        }), 500

@socketio.on('register_screen')
def handle_register_screen(data):
    """Enregistre un nouvel écran"""
    screen_id = data.get('screen_id')

    if screen_id in screens:
        screens[screen_id]['status'] = 'online'
        screens[screen_id]['sid'] = request.sid
        screens[screen_id]['last_seen'] = datetime.now().strftime('%H:%M:%S')
    else:
        screens[screen_id] = {
            'id': screen_id,
            'name': data.get('name', f'Écran {screen_id}'),
            'location': data.get('location', 'Non défini'),
            'default_content_id': None,
            'idle_behavior': 'show_default',
            'show_clock': False,
            'status': 'online',
            'current_content': None,
            'last_seen': datetime.now().strftime('%H:%M:%S'),
            'sid': request.sid
        }
        save_screens()

    # Envoyer l'état complet à tous les clients
    emit('state_update', {
        'screens': screens,
        'content': content_library,
        'playlists': playlists,
        'schedules': schedules
    }, broadcast=True)
    
    # Envoyer les playlists et contenus à l'écran qui vient de se connecter
    emit('send_full_playlist_list', {
        'screen_id': screen_id,
        'playlists': playlists
    }, room=request.sid)

    emit('send_content_library', {
        'screen_id': screen_id,
        'content': content_library
    }, room=request.sid)
    
    # Envoyer le planning à l'écran
    if screen_id in schedules:
        emit('update_schedule', {
            'screen_id': screen_id,
            'schedule': schedules[screen_id]
        }, room=request.sid)

    # Envoyer la configuration de l'écran
    emit('config_updated', {
        'screen_id': screen_id,
        'default_content_id': screens[screen_id].get('default_content_id', None),
        'idle_behavior': screens[screen_id].get('idle_behavior', 'show_default'),
        'show_clock': screens[screen_id].get('show_clock', False)
    }, room=request.sid)

@socketio.on('get_state')
def handle_get_state():
    """Récupère l'état actuel"""
    emit('state_update', {
        'screens': screens,
        'content': content_library,
        'playlists': playlists,
        'schedules': schedules
    })

@socketio.on('add_content')
def handle_add_content(data):
    """Ajoute un contenu à la bibliothèque"""
    content_library.append(data)
    save_content()
    emit('state_update', {
        'screens': screens,
        'content': content_library,
        'playlists': playlists,
        'schedules': schedules
    }, broadcast=True)

    # Envoyer la bibliothèque mise à jour aux écrans
    emit('send_content_library', {
        'content': content_library
    }, broadcast=True)

@socketio.on('delete_content')
def handle_delete_content(data):
    """Supprime un contenu"""
    global content_library
    content_library = [c for c in content_library if c['id'] != data['content_id']]
    save_content()
    emit('state_update', {
        'screens': screens,
        'content': content_library,
        'playlists': playlists,
        'schedules': schedules
    }, broadcast=True)

    # Envoyer la bibliothèque mise à jour aux écrans
    emit('send_content_library', {
        'content': content_library
    }, broadcast=True)

@socketio.on('update_content')
def handle_update_content(data):
    """Met à jour un contenu existant"""
    global content_library, playlists

    # Récupérer l'ancien contenu pour comparer la durée (faire une copie pour éviter les références)
    old_content = next((c for c in content_library if c['id'] == data['id']), None)
    if old_content:
        old_content = old_content.copy()  # Copie pour préserver l'ancienne durée

    # Mettre à jour le contenu dans la bibliothèque
    for i, content in enumerate(content_library):
        if content['id'] == data['id']:
            content_library[i] = data
            break

    # Mettre à jour les playlists qui contiennent ce contenu
    if old_content:
        playlists_updated = False
        for playlist_id, playlist in playlists.items():
            for item in playlist['items']:
                # Si l'item contient le contenu modifié
                if item['content']['id'] == data['id']:
                    print(f"🔄 Mise à jour du contenu '{data['name']}' dans la playlist '{playlist['name']}'")
                    print(f"   Ancienne durée item: {item['duration']}s | Ancienne durée contenu: {old_content['duration']}s")
                    print(f"   Nouvelle durée contenu: {data['duration']}s")

                    # Mettre à jour toutes les propriétés du contenu sauf la durée
                    item['content']['name'] = data['name']
                    item['content']['type'] = data['type']
                    item['content']['url'] = data['url']

                    # Pour la durée : si c'était la durée par défaut du contenu, mettre à jour
                    # Sinon garder la durée personnalisée de la playlist
                    if item['duration'] == old_content['duration']:
                        item['duration'] = data['duration']
                        print(f"   ✅ Durée de l'item mise à jour: {item['duration']}s")
                        playlists_updated = True
                    else:
                        print(f"   ⚠️  Durée personnalisée conservée: {item['duration']}s")

                    # Mettre à jour aussi la durée dans l'objet content de l'item
                    item['content']['duration'] = data['duration']

        if playlists_updated:
            save_playlists()
            print(f"💾 Playlists sauvegardées avec les mises à jour")
        else:
            print(f"ℹ️  Aucune playlist à mettre à jour (durées personnalisées ou contenu non trouvé)")

    save_content()

    # Envoyer l'état complet mis à jour (inclut playlists, contenu, etc.)
    emit('state_update', {
        'screens': screens,
        'content': content_library,
        'playlists': playlists,
        'schedules': schedules
    }, broadcast=True)

    # Envoyer la bibliothèque mise à jour aux écrans display
    emit('send_content_library', {
        'content': content_library
    }, broadcast=True)

@socketio.on('display_content')
def handle_display_content(data):
    """Affiche un contenu sur un écran"""
    screen_id = data['screen_id']
    content_id = data['content_id']
    priority = data.get('priority', False)
    custom_duration = data.get('custom_duration', None)

    content = next((c for c in content_library if c['id'] == content_id), None)
    if content and screen_id in screens:
        screens[screen_id]['current_content'] = content['name']

        # Si c'est un affichage prioritaire avec durée personnalisée
        content_to_send = content.copy()
        if priority and custom_duration is not None:
            content_to_send['duration'] = custom_duration

        emit('show_content', {
            'content': content_to_send,
            'priority': priority
        }, room=screens[screen_id]['sid'])

        emit('state_update', {
            'screens': screens,
            'content': content_library,
            'playlists': playlists,
            'schedules': schedules
        }, broadcast=True)

@socketio.on('clear_screen')
def handle_clear_screen(data):
    """Efface l'écran"""
    screen_id = data['screen_id']
    if screen_id in screens:
        screens[screen_id]['current_content'] = None
        emit('clear_content', room=screens[screen_id]['sid'])
        emit('state_update', {
            'screens': screens,
            'content': content_library,
            'playlists': playlists,
            'schedules': schedules
        }, broadcast=True)

@socketio.on('reload_screen')
def handle_reload_screen(data):
    """Force le rechargement d'un écran"""
    screen_id = data.get('screen_id')
    if screen_id in screens and screens[screen_id]['status'] == 'online':
        emit('reload_page', room=screens[screen_id]['sid'])
        print(f"🔄 Rechargement demandé pour l'écran {screen_id}")

@socketio.on('bulk_display')
def handle_bulk_display(data):
    """Affiche plusieurs contenus sur plusieurs écrans"""
    screen_ids = data['screen_ids']
    content_ids = data['content_ids']
    
    for screen_id in screen_ids:
        if screen_id not in screens:
            continue
            
        for content_id in content_ids:
            content = next((c for c in content_library if c['id'] == content_id), None)
            if content:
                screens[screen_id]['current_content'] = content['name']
                emit('show_content', content, room=screens[screen_id]['sid'])
    
    emit('state_update', {
        'screens': screens,
        'content': content_library,
        'playlists': playlists,
        'schedules': schedules
    }, broadcast=True)

@socketio.on('create_playlist')
def handle_create_playlist(data):
    """Crée une playlist globale (sans l'affecter à un écran)"""
    playlist_name = data.get('name', 'Playlist')
    playlist_items = data['items']
    
    playlist_id = f"pl_{int(datetime.now().timestamp())}"
    
    playlists[playlist_id] = {
        'id': playlist_id,
        'name': playlist_name,
        'items': playlist_items,
        'created_at': datetime.now().isoformat()
    }
    save_playlists()
    
    emit('state_update', {
        'screens': screens,
        'content': content_library,
        'playlists': playlists,
        'schedules': schedules
    }, broadcast=True)

@socketio.on('update_playlist')
def handle_update_playlist(data):
    """Modifie une playlist existante"""
    playlist_id = data['id']
    if playlist_id in playlists:
        playlists[playlist_id]['name'] = data.get('name', playlists[playlist_id]['name'])
        playlists[playlist_id]['items'] = data.get('items', playlists[playlist_id]['items'])
        save_playlists()
        
        emit('state_update', {
            'screens': screens,
            'content': content_library,
            'playlists': playlists,
            'schedules': schedules
        }, broadcast=True)

@socketio.on('start_playlist')
def handle_start_playlist(data):
    """Lance une playlist sur un écran (pour test manuel)"""
    screen_id = data['screen_id']
    playlist_id = data['playlist_id']
    priority = data.get('priority', False)
    custom_duration = data.get('custom_duration', None)

    if screen_id not in screens or playlist_id not in playlists:
        return

    playlist = playlists[playlist_id]
    screens[screen_id]['current_content'] = f"Playlist: {playlist['name']}"

    # Log pour debug
    print(f"🔵 START_PLAYLIST: screen={screen_id}, playlist={playlist['name']}, priority={priority}, custom_duration={custom_duration}")
    if priority and custom_duration is not None and custom_duration > 0:
        print(f"   ⏱️ Durée TOTALE de la playlist: {custom_duration}s")

    # Envoyer les items avec leur durée normale + la durée totale personnalisée
    emit('start_playlist', {
        'id': playlist_id,
        'name': playlist['name'],
        'items': playlist['items'],
        'priority': priority,
        'custom_duration': custom_duration  # Durée TOTALE de la playlist
    }, room=screens[screen_id]['sid'])
    
    emit('state_update', {
        'screens': screens,
        'content': content_library,
        'playlists': playlists,
        'schedules': schedules
    }, broadcast=True)

@socketio.on('update_schedule')
def handle_update_schedule(data):
    """Met à jour le planning d'un écran"""
    screen_id = data['screen_id']
    schedule = data['schedule']
    
    schedules[screen_id] = schedule
    save_schedules()
    
    # Envoyer le planning à l'écran concerné
    if screen_id in screens and screens[screen_id]['sid']:
        emit('update_schedule', {
            'screen_id': screen_id,
            'schedule': schedule
        }, room=screens[screen_id]['sid'])
    
    # Mettre à jour tous les gestionnaires
    emit('state_update', {
        'screens': screens,
        'content': content_library,
        'playlists': playlists,
        'schedules': schedules
    }, broadcast=True)

@socketio.on('delete_playlist')
def handle_delete_playlist(data):
    """Supprime une playlist"""
    playlist_id = data['playlist_id']
    
    if playlist_id in playlists:
        del playlists[playlist_id]
        save_playlists()
        
        # Nettoyer les plannings qui utilisent cette playlist
        for screen_id in schedules:
            schedules[screen_id] = [s for s in schedules[screen_id] if s.get('playlist_id') != playlist_id]
        save_schedules()
        
        emit('state_update', {
            'screens': screens,
            'content': content_library,
            'playlists': playlists,
            'schedules': schedules
        }, broadcast=True)

@socketio.on('update_screen_config')
def handle_update_screen_config(data):
    """Met à jour la configuration d'un écran (contenu par défaut et comportement)"""
    screen_id = data['screen_id']

    if screen_id in screens:
        screens[screen_id]['default_content_id'] = data.get('default_content_id', None)
        screens[screen_id]['idle_behavior'] = data.get('idle_behavior', 'show_default')
        screens[screen_id]['show_clock'] = data.get('show_clock', False)
        save_screens()

        # Envoyer la config mise à jour à l'écran concerné
        if screens[screen_id]['sid']:
            emit('config_updated', {
                'screen_id': screen_id,
                'default_content_id': screens[screen_id]['default_content_id'],
                'idle_behavior': screens[screen_id]['idle_behavior'],
                'show_clock': screens[screen_id]['show_clock']
            }, room=screens[screen_id]['sid'])

        # NE PAS envoyer de state_update complet pour les changements de config
        # Cela évite d'interrompre les playlists prioritaires en cours
        # Les gestionnaires recevront la mise à jour via le prochain state_update normal

@socketio.on('update_debug_info')
def handle_update_debug_info(data):
    """Met à jour les informations de debug d'un écran"""
    screen_id = data.get('screen_id')

    if screen_id in screens:
        # Stocker les infos de debug dans l'objet screen
        screens[screen_id]['debug_info'] = {
            'current_playlist_name': data.get('current_playlist_name'),
            'current_content_name': data.get('current_content_name'),
            'playlist_index': data.get('playlist_index'),
            'playlist_length': data.get('playlist_length'),
            'elapsed_time': data.get('elapsed_time'),
            'current_duration': data.get('current_duration'),
            'is_priority_active': data.get('is_priority_active', False)
        }

        # Stocker aussi is_priority_active au niveau principal pour un accès facile
        screens[screen_id]['is_priority_active'] = data.get('is_priority_active', False)

        # Mettre à jour current_content et current_playlist pour l'affichage
        screens[screen_id]['current_content'] = data.get('current_content_name') or None
        screens[screen_id]['current_playlist'] = data.get('current_playlist_name') or None

        # Mettre à jour le timestamp
        screens[screen_id]['last_seen'] = datetime.now().strftime('%H:%M:%S')

        # Broadcaster la mise à jour (légère, seulement si nécessaire)
        emit('state_update', {
            'screens': screens,
            'content': content_library,
            'playlists': playlists,
            'schedules': schedules
        }, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    """Gère la déconnexion"""
    for screen_id, screen in screens.items():
        if screen.get('sid') == request.sid:
            screen['status'] = 'offline'
            emit('state_update', {
                'screens': screens,
                'content': content_library,
                'playlists': playlists,
                'schedules': schedules
            }, broadcast=True)
            break

if __name__ == '__main__':
    print("=" * 60)
    print("🖥️  SYSTÈME DE GESTION D'AFFICHAGE MULTI-ÉCRANS")
    print("=" * 60)
    print("\n📋 Instructions de démarrage:\n")
    print("1. Installez les dépendances:")
    print("   pip install flask flask-socketio python-socketio requests isodate\n")
    print("2. Lancez le serveur sur votre réseau local\n")
    print("3. Interface de gestion:")
    print("   http://VOTRE_IP:5000/\n")
    print("4. Sur chaque Raspberry Pi, ouvrez Chromium en plein écran:")
    print("   chromium-browser --kiosk --noerrdialogs \\")
    print("   http://VOTRE_IP:5000/display?id=ecran1&name=Cuisine&location=RDC\n")
    print("=" * 60)
    print("\n💾 Système de sauvegarde activé:")
    print(f"   - Contenus: {CONTENT_FILE}")
    print(f"   - Écrans: {SCREENS_FILE}")
    print(f"   - Playlists: {PLAYLISTS_FILE}")
    print(f"   - Plannings: {SCHEDULES_FILE}")
    print("   Les données seront conservées après redémarrage!\n")
    print("=" * 60)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)