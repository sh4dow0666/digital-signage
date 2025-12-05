#!/usr/bin/env python3
"""
Serveur du wizard de configuration pour Digital Signage
"""

from flask import Flask, render_template, request, jsonify
import os
import subprocess
import argparse

app = Flask(__name__)

# Chemins
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, 'config', 'device.conf')

def read_config():
    """Lire le fichier de configuration"""
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"')
    return config

def write_config(config):
    """Écrire le fichier de configuration"""
    with open(CONFIG_FILE, 'w') as f:
        f.write('# Configuration du dispositif Digital Signage\n')
        for key, value in config.items():
            if isinstance(value, bool):
                value = 'true' if value else 'false'
            # Mettre les valeurs entre guillemets pour gérer les espaces
            f.write(f'{key}="{value}"\n')

@app.route('/')
def index():
    """Page principale du wizard"""
    config = read_config()
    return render_template('wizard.html',
                         ssid=config.get('WIFI_SSID', 'DigitalSignage-Setup'),
                         password=config.get('WIFI_PASSWORD', 'signage2024'),
                         server_ip=request.host.split(':')[0])

@app.route('/api/config', methods=['GET'])
def get_config():
    """Obtenir la configuration actuelle"""
    config = read_config()
    return jsonify(config)

@app.route('/system', methods=['POST'])
def system_action():
    """Effectuer une action système (reboot, shutdown)"""
    data = request.json
    action = data.get('action')

    try:
        if action == 'reboot':
            subprocess.run(['sudo', 'reboot'], check=True)
            return jsonify({'success': True, 'message': 'Redémarrage en cours...'})
        elif action == 'shutdown':
            subprocess.run(['sudo', 'shutdown', 'now'], check=True)
            return jsonify({'success': True, 'message': 'Arrêt en cours...'})
        else:
            return jsonify({'error': 'Action inconnue'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['POST'])
def save_config():
    """Sauvegarder la configuration"""
    data = request.json

    # Valider les données
    config = {
        'CONFIGURED': True,
        'ROLE_CONTROLLER': data.get('role_controller', False),
        'ROLE_PLAYER': data.get('role_player', False),
        'SCREEN_ID': data.get('screen_id', ''),
        'SCREEN_NAME': data.get('screen_name', ''),
        'SCREEN_LOCATION': data.get('screen_location', ''),
        'CONTROLLER_URL': data.get('controller_url', 'http://localhost:5000'),
        'WIFI_SSID': data.get('wifi_ssid', 'DigitalSignage-Setup'),
        'WIFI_PASSWORD': data.get('wifi_password', 'signage2024')
    }

    # Validation
    if config['ROLE_PLAYER']:
        if not config['SCREEN_ID'] or not config['SCREEN_NAME']:
            return jsonify({'error': 'ID et nom d\'écran requis pour le mode player'}), 400

    if not config['ROLE_CONTROLLER'] and not config['ROLE_PLAYER']:
        return jsonify({'error': 'Au moins un rôle doit être sélectionné'}), 400

    # Sauvegarder
    write_config(config)

    return jsonify({'success': True, 'message': 'Configuration sauvegardée'})

@app.route('/api/network/scan', methods=['GET'])
def scan_networks():
    """Scanner les réseaux WiFi disponibles"""
    try:
        result = subprocess.run(['sudo', 'iwlist', 'wlan0', 'scan'],
                              capture_output=True, text=True, timeout=10)
        # Parser les résultats (simplifié)
        networks = []
        for line in result.stdout.split('\n'):
            if 'ESSID:' in line:
                ssid = line.split('ESSID:')[1].strip().strip('"')
                if ssid:
                    networks.append({'ssid': ssid})
        return jsonify(networks)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/network/connect', methods=['POST'])
def connect_network():
    """Connecter à un réseau WiFi"""
    data = request.json
    ssid = data.get('ssid')
    password = data.get('password')

    # Créer la configuration wpa_supplicant
    try:
        config = f'''
network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
'''
        with open('/tmp/wpa_supplicant_temp.conf', 'w') as f:
            f.write(config)

        # Ajouter au wpa_supplicant
        subprocess.run(['sudo', 'sh', '-c',
                       'cat /tmp/wpa_supplicant_temp.conf >> /etc/wpa_supplicant/wpa_supplicant.conf'],
                      check=True)

        # Redémarrer le WiFi
        subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'reconfigure'], check=True)

        return jsonify({'success': True, 'message': 'Connexion en cours...'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--ip', type=str, default='0.0.0.0')
    args = parser.parse_args()

    app.run(host=args.ip, port=args.port, debug=False)
