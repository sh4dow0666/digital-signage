# Configuration de l'API YouTube

Pour activer la récupération automatique des métadonnées YouTube (titre et durée), vous devez configurer une clé API YouTube.

## Étapes pour obtenir une clé API YouTube

### 1. Créer un projet Google Cloud

1. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
2. Connectez-vous avec votre compte Google
3. Cliquez sur "Créer un projet" ou sélectionnez un projet existant
4. Donnez un nom à votre projet (ex: "Gestion Écrans")

### 2. Activer l'API YouTube Data v3

1. Dans le menu de gauche, allez dans **APIs & Services** > **Library**
2. Recherchez "YouTube Data API v3"
3. Cliquez sur "YouTube Data API v3"
4. Cliquez sur le bouton **ENABLE** (Activer)

### 3. Créer une clé API

1. Allez dans **APIs & Services** > **Credentials** (Identifiants)
2. Cliquez sur **+ CREATE CREDENTIALS** (Créer des identifiants)
3. Sélectionnez **API key** (Clé API)
4. Une clé API sera générée (ex: `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`)
5. (Optionnel) Cliquez sur "Restrict Key" pour sécuriser votre clé :
   - **Application restrictions** : Sélectionnez "IP addresses" et ajoutez l'IP de votre serveur
   - **API restrictions** : Sélectionnez "Restrict key" et choisissez uniquement "YouTube Data API v3"

### 4. Configurer la clé dans l'application

**Méthode 1 : Fichier de configuration (Recommandé)**

1. Créez un fichier `data/config.json` avec le contenu suivant :
   ```json
   {
     "youtube_api_key": "VOTRE_CLE_API_ICI"
   }
   ```

2. Remplacez `VOTRE_CLE_API_ICI` par votre clé API

**Méthode 2 : Variable d'environnement**

1. Définissez la variable d'environnement `YOUTUBE_API_KEY` :
   ```bash
   export YOUTUBE_API_KEY="VOTRE_CLE_API_ICI"
   ```

2. Lancez ensuite votre application normalement

## Utilisation

Une fois la clé API configurée :

1. Ouvrez l'interface de gestion
2. Cliquez sur "+ Ajouter" dans la section Bibliothèque
3. Sélectionnez le type **YouTube**
4. Collez l'URL d'une vidéo YouTube (ex: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`)
5. Cliquez en dehors du champ URL
6. Le titre et la durée seront automatiquement récupérés ! ✨

## Quota et limites

L'API YouTube Data v3 a un quota gratuit de **10,000 unités par jour**.
- Chaque requête pour récupérer les métadonnées coûte **1 unité**
- Vous pouvez donc récupérer les métadonnées de **10,000 vidéos par jour** gratuitement

## Dépannage

### Erreur : "Clé API YouTube non configurée"
- Vérifiez que le fichier `data/config.json` existe et contient la bonne clé
- Ou vérifiez que la variable d'environnement `YOUTUBE_API_KEY` est définie

### Erreur : "Vidéo non trouvée"
- Vérifiez que l'URL YouTube est correcte
- La vidéo peut être privée ou supprimée

### Erreur : "API key not valid"
- Vérifiez que votre clé API est correcte
- Vérifiez que l'API YouTube Data v3 est bien activée dans Google Cloud Console
- Vérifiez les restrictions d'IP si vous en avez configurées

## Sécurité

⚠️ **Important** : Ne partagez jamais votre clé API publiquement !
- Ajoutez `data/config.json` à votre `.gitignore` si vous utilisez Git
- Utilisez les restrictions d'IP dans Google Cloud Console pour limiter l'utilisation
