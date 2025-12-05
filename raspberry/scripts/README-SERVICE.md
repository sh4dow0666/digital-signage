# Installation du Service Digital Signage

Ce guide explique comment installer et configurer le service Digital Signage pour qu'il démarre automatiquement au boot du Raspberry Pi, sans bureau graphique et sans demander de mot de passe.

## Problèmes résolus

✅ Le service démarre automatiquement au boot
✅ Aucun mot de passe n'est demandé
✅ Pas de bureau graphique visible, uniquement Chromium
✅ hostapd.service n'est plus "masked"
✅ Gestion automatique du réseau et du point d'accès WiFi

## Installation

### 1. Exécuter le script d'installation

```bash
cd /home/maxime/DS/raspberry/scripts
sudo ./install-service.sh
```

Le script va automatiquement :
- Configurer sudo pour ne pas demander de mot de passe
- Installer le service systemd `digital-signage.service`
- Démasquer `hostapd.service`
- Configurer l'autologin en mode console
- Désactiver le bureau graphique
- Configurer le lancement automatique de X11 et Chromium

### 2. Redémarrer le Raspberry Pi

```bash
sudo reboot
```

## Après le redémarrage

Le système va :
1. Démarrer en mode console (pas de bureau graphique)
2. Se connecter automatiquement avec l'utilisateur `maxime`
3. Lancer X11 automatiquement
4. Exécuter le script `startup.sh`
5. Afficher Chromium en mode kiosk plein écran

**Vous ne verrez que Chromium, rien d'autre !**

## Vérifier le statut du service

```bash
# Voir si le service est actif
systemctl status digital-signage.service

# Voir les logs en temps réel
journalctl -u digital-signage.service -f

# Voir les logs depuis le boot
journalctl -u digital-signage.service -b
```

## Commandes utiles

### Arrêter le service temporairement

```bash
sudo systemctl stop digital-signage.service
```

### Redémarrer le service

```bash
sudo systemctl restart digital-signage.service
```

### Désactiver le service (ne démarre plus au boot)

```bash
sudo systemctl disable digital-signage.service
```

### Réactiver le service

```bash
sudo systemctl enable digital-signage.service
```

## Désinstallation

Si vous voulez revenir à la configuration normale avec bureau graphique :

```bash
cd /home/maxime/DS/raspberry/scripts
sudo ./uninstall-service.sh
sudo reboot
```

Cela va :
- Désinstaller le service
- Réactiver le bureau graphique
- Désactiver l'autologin automatique

## Dépannage

### Le service ne démarre pas

```bash
# Vérifier les logs d'erreur
journalctl -u digital-signage.service -n 50

# Tester le script manuellement
/home/maxime/DS/raspberry/scripts/startup.sh
```

### Chromium ne s'affiche pas

```bash
# Vérifier que X11 est lancé
echo $DISPLAY  # Doit afficher :0

# Vérifier les processus Chromium
ps aux | grep chromium

# Vérifier les permissions
ls -la /home/maxime/.Xauthority
```

### hostapd ne démarre pas

```bash
# Vérifier que hostapd n'est pas masked
systemctl status hostapd

# Si toujours masked, démasquer manuellement
sudo systemctl unmask hostapd

# Vérifier les logs
journalctl -u hostapd -n 50
```

### Accès au terminal

Si vous avez besoin d'accéder au terminal :

**Option 1 : SSH**
Connectez-vous via SSH depuis un autre ordinateur :
```bash
ssh maxime@<ip_du_raspberry>
```

**Option 2 : TTY**
Appuyez sur `Ctrl+Alt+F2` pour accéder à tty2 et vous connecter

**Option 3 : Arrêter le service temporairement**
```bash
# Via SSH
sudo systemctl stop digital-signage.service
```

## Architecture

### Fichiers installés

- `/etc/systemd/system/digital-signage.service` - Service systemd
- `/etc/sudoers.d/digital-signage` - Configuration sudo
- `/etc/systemd/system/getty@tty1.service.d/override.conf` - Autologin
- `/home/maxime/.xinitrc` - Configuration X11
- `/home/maxime/.bash_profile` - Lancement automatique de X

### Flux de démarrage

```
Boot Raspberry Pi
    ↓
Console login automatique (tty1)
    ↓
.bash_profile lance startx
    ↓
.xinitrc lance startup.sh
    ↓
startup.sh démarre :
    - Wizard de config (si CONFIGURED=false)
    - Point d'accès WiFi (si pas de réseau)
    - Contrôleur Flask (si ROLE_CONTROLLER=true)
    - Player Chromium (si ROLE_PLAYER=true)
```

## Notes importantes

- **Pas de mot de passe** : Les commandes sudo nécessaires sont configurées pour ne pas demander de mot de passe
- **Pas de bureau** : Le système démarre en mode console puis lance uniquement X11 minimal + Chromium
- **Redémarrage automatique** : Si le service plante, il redémarre automatiquement après 10 secondes
- **Logs** : Tous les logs sont disponibles via `journalctl`

## Support

Pour plus d'informations, consultez :
- `startup.sh` - Script principal de démarrage
- `setup-ap.sh` - Gestion du point d'accès WiFi
- `digital-signage.service` - Configuration du service systemd
