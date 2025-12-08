"""
Système de gestion d'affichage pour Raspberry Pi
Interface web pour contrôler plusieurs écrans à distance
VERSION CORRIGÉE - Playlists fonctionnelles
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import json
import os
from datetime import datetime
import requests
import re
import isodate

app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre-cle-secrete-ici'
socketio = SocketIO(app, cors_allowed_origins="*")

# Fichiers de sauvegarde
DATA_DIR = 'data'
SCREENS_FILE = os.path.join(DATA_DIR, 'screens.json')
CONTENT_FILE = os.path.join(DATA_DIR, 'content.json')
PLAYLISTS_FILE = os.path.join(DATA_DIR, 'playlists.json')
SCHEDULES_FILE = os.path.join(DATA_DIR, 'schedules.json')

# Créer le dossier data s'il n'existe pas
os.makedirs(DATA_DIR, exist_ok=True)

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
                'idle_behavior': screen_data.get('idle_behavior', 'show_default')
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

@app.route('/')
def manager():
    """Interface de gestion"""
    return render_template("manager.html")

@app.route('/display')
def display():
    """Page d'affichage pour les Raspberry Pi"""
    return render_template("display.html")

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
        'idle_behavior': screens[screen_id].get('idle_behavior', 'show_default')
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
    global content_library
    for i, content in enumerate(content_library):
        if content['id'] == data['id']:
            content_library[i] = data
            break

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

@socketio.on('display_content')
def handle_display_content(data):
    """Affiche un contenu sur un écran"""
    screen_id = data['screen_id']
    content_id = data['content_id']
    
    content = next((c for c in content_library if c['id'] == content_id), None)
    if content and screen_id in screens:
        screens[screen_id]['current_content'] = content['name']
        
        emit('show_content', content, room=screens[screen_id]['sid'])
        
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
    
    if screen_id not in screens or playlist_id not in playlists:
        return
    
    playlist = playlists[playlist_id]
    screens[screen_id]['current_content'] = f"Playlist: {playlist['name']}"
    
    emit('start_playlist', {
        'name': playlist['name'],
        'items': playlist['items']
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
        save_screens()

        # Envoyer la config mise à jour à l'écran concerné
        if screens[screen_id]['sid']:
            emit('config_updated', {
                'screen_id': screen_id,
                'default_content_id': screens[screen_id]['default_content_id'],
                'idle_behavior': screens[screen_id]['idle_behavior']
            }, room=screens[screen_id]['sid'])

        # Mettre à jour tous les gestionnaires
        emit('state_update', {
            'screens': screens,
            'content': content_library,
            'playlists': playlists,
            'schedules': schedules
        }, broadcast=True)

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
            'current_duration': data.get('current_duration')
        }

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