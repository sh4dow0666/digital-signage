# 🚀 Installation Express Digital Signage

## Installation Automatique en 1 Commande

### Sur Raspberry Pi

```bash
curl -fsSL https://raw.githubusercontent.com/sh4dow0666/digital-signage/main/bootstrap.sh | bash
```

Puis après l'installation :
```bash
sudo reboot
```

**C'EST TOUT !** 🎉

## Ce que fait le script automatiquement

✅ Clone le repository GitHub
✅ Installe Git et toutes les dépendances
✅ Configure raspi-config (autologin + désactive screen blanking)
✅ Copie les fichiers dans /opt/digital-signage
✅ Configure le service systemd
✅ Configure le mode kiosk
✅ Normalise les fins de lignes (fixe les problèmes CRLF)
✅ Configure les permissions

## Après le redémarrage

Le **wizard de configuration** s'affiche automatiquement et vous guide pour :

1. Choisir le rôle (Contrôleur / Player / Les deux)
2. Configurer les paramètres de l'écran
3. Connecter au serveur central (si Player)

## Temps d'installation

- **Préparation carte SD** : 10 min
- **Premier boot** : 5 min
- **Installation automatique** : 10-15 min
- **Configuration wizard** : 2 min

**Total : ~30 minutes**

## Prérequis

- Raspberry Pi 3 Model B/B+ ou supérieur
- Carte SD 8GB minimum
- Connexion internet (WiFi ou Ethernet)
- Raspberry Pi OS (32 ou 64-bit) with desktop

## Commandes utiles

```bash
# Menu de maintenance
sudo ds-maintenance

# État du service
sudo systemctl status digital-signage

# Logs en direct
journalctl -u digital-signage -f

# Redémarrer le service
sudo systemctl restart digital-signage

# IP du Raspberry Pi
hostname -I
```

## Accès à l'interface web

Une fois installé et configuré :

```
http://[IP_DU_PI]:5000
```

## Support

- Documentation complète : `PROCEDURE_COMPLETE.md`
- Documentation Raspberry Pi : `raspberry/README.md`
- Scripts : `raspberry/scripts/`

## Dépannage

Si le wizard ne s'affiche pas :
```bash
sudo ds-maintenance
# Choisir option 4 : Réinitialiser la configuration
```

Si problème de fins de lignes :
```bash
cd ~/DS
find . -name "*.sh" -exec sed -i 's/\r$//' {} \;
```

## Installation Alternative (Sans Internet)

1. Télécharger le ZIP depuis GitHub sur un autre PC
2. Copier sur clé USB
3. Sur le Raspberry Pi :
```bash
cd ~
unzip digital-signage-main.zip
mv digital-signage-main DS
cd DS
find . -name "*.sh" -exec chmod +x {} \;
find . -name "*.sh" -exec sed -i 's/\r$//' {} \;
sudo raspberry/install.sh
sudo reboot
```

---

**Projet** : Digital Signage pour Raspberry Pi
**Repository** : https://github.com/sh4dow0666/digital-signage
**License** : Open Source
