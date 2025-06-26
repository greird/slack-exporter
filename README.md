# Slack Attachment Exporter & Backup

Ce projet automatise la sauvegarde de l'historique des conversations et des pièces jointes d'un espace de travail Slack vers un dossier local, avec une option pour uploader la sauvegarde sur Google Drive.

## Fonctionnalités

- **Export de l'historique** : Récupère l'historique des conversations des canaux publics et privés.
- **Téléchargement des pièces jointes** : Parcourt l'historique exporté et télécharge toutes les pièces jointes référencées.
- **Sauvegarde locale** : Organise les exports et les pièces jointes dans un dossier de sauvegarde horodaté.
- **Upload sur Google Drive** : Uploade l'intégralité du dossier de sauvegarde sur un dossier Google Drive spécifié, en conservant l'arborescence.
- **Automatisation** : Peut être exécuté une seule fois ou de manière périodique (tous les 3 mois par défaut).
- **Gestion des erreurs** : Gère les erreurs courantes comme les limites de débit de l'API Slack (`rate limiting`).

## Prérequis

Avant de commencer, assurez-vous d'avoir installé les outils suivants :

- **Python >=3.10** 
- **Poetry** 
- **jq** : Un processeur JSON en ligne de commande. Indispensable pour le script de téléchargement.
  - Pour l'installer sur macOS : `brew install jq`
  - Pour d'autres systèmes, suivez les [instructions d'installation de jq](https://stedolan.github.io/jq/download/).

## Installation

1.  **Clonez le projet** :
    ```bash
    git clone <URL_DU_PROJET>
    cd slack-exporter
    ```

2.  **Installez les dépendances Python** :
    Ce projet utilise `Poetry` pour gérer ses dépendances. Si vous n'avez pas Poetry, installez-le. Ensuite, exécutez :
    ```bash
    poetry install
    ```
    Si vous n'utilisez pas Poetry, vous pouvez installer les paquets listés dans `pyproject.toml` manuellement avec `pip`.

3.  **Configurez les variables d'environnement** :
    Créez un fichier `.env` à la racine du projet en vous basant sur l'exemple ci-dessous :

    ```
    # .env
    SLACK_BOT_TOKEN="xoxb-VOTRE_TOKEN_BOT_SLACK"
    GOOGLE_DRIVE_FOLDER_ID="ID_DU_DOSSIER_GOOGLE_DRIVE"
    GOOGLE_CREDENTIALS_PATH="./credentials.json"
    ```

    - `SLACK_BOT_TOKEN` : Le token de votre bot Slack. [Comment en obtenir un](https://api.slack.com/authentication/basics).
    - `GOOGLE_DRIVE_FOLDER_ID` : L'ID du dossier Google Drive où les sauvegardes seront uploadées.
    - `GOOGLE_CREDENTIALS_PATH` : Le chemin vers votre fichier d'identifiants Google API.

## Configuration de l'API Google Drive

Pour uploader des fichiers sur Google Drive, vous devez activer l'API Google Drive et obtenir des identifiants.

1.  Allez sur la [console Google Cloud](https://console.cloud.google.com/).
2.  Créez un nouveau projet.
3.  Activez l'**API Google Drive** pour ce projet.
4.  Créez des **identifiants** de type **"Écran de consentement OAuth"**.
    - Configurez-le pour un usage **Externe** et ajoutez votre propre adresse email comme utilisateur de test.
5.  Créez de nouveaux **identifiants** de type **"ID client OAuth"** pour une **Application de bureau**.
6.  Téléchargez le fichier JSON contenant vos identifiants. Renommez-le `credentials.json` et placez-le à la racine de ce projet.

Lors de la première exécution, le script vous demandera de vous authentifier via votre navigateur pour autoriser l'accès à votre Google Drive.

## Utilisation

Le script principal est `main.py`.

### Exécution unique

Pour lancer une sauvegarde complète une seule fois, utilisez le flag `--run-once` :

```bash
python main.py --run-once
```

### Exécution périodique

Pour lancer le script en mode service, qui effectuera une sauvegarde tous les 90 jours :

```bash
python main.py
```

Le script s'exécutera en continu et lancera une nouvelle sauvegarde à la fin de chaque période.

## Scripts du projet

- `main.py` : Le script principal qui orchestre tout le processus : nettoyage, export, téléchargement des pièces jointes, et upload.
- `download_attachments.sh` : Un script shell qui prend en entrée le chemin d'un export Slack et télécharge toutes les pièces jointes qu'il trouve.
