#!/usr/bin/env python3
"""
Automatisation de la sauvegarde des pièces jointes Slack
Exporte automatiquement l'historique Slack et télécharge les pièces jointes
"""

import os
import sys
import json
import time
import shutil
import subprocess
import requests
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configuration
CONFIG = {
    "slack_token": os.getenv("SLACK_BOT_TOKEN"),  # Token bot Slack
    "google_drive_folder_id": os.getenv("GOOGLE_DRIVE_FOLDER_ID"),
    "google_credentials_path": os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json"),
    "download_script_path": "./download_attachments.sh",  # Chemin vers votre script
    "temp_dir": "./temp_slack_export",
    "backup_dir": "./slack_backups",
    "log_file": "./slack_automation.log"
}

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(CONFIG["log_file"]),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SlackExporter:
    def __init__(self):
        self.slack_token = CONFIG["slack_token"]
        self.headers = {"Authorization": f"Bearer {self.slack_token}"}
    
    def get_workspace_info(self):
        """Récupère les informations du workspace"""
        try:
            response = requests.get(
                "https://slack.com/api/team.info",
                headers=self.headers
            )
            data = response.json()
            print(data)
            if data.get("ok"):
                return data["team"]
            else:
                logger.error(f"Erreur API Slack: {data.get('error')}")
                return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos workspace: {e}")
            return None

    def get_channels_list(self):
        """Récupère la liste des channels"""
        try:
            response = requests.get(
                "https://slack.com/api/users.conversations",
                headers=self.headers
            )
            data = response.json()
            if data.get("ok"):
                return data["channels"]
            else:
                logger.error(f"Erreur API Slack: {data.get('error')}")
                return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des channels: {e}")
            return None

class GoogleDriveUploader:
    def __init__(self):
        self.credentials_path = CONFIG["google_credentials_path"]
        self.google_drive_folder_id = "1nFlVku9UCtKgc0yhqBZilfi5hZlEF36i" # CONFIG["google_drive_folder_id"]
    
    def setup_credentials(self):
        """Configure les credentials Google Drive"""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            
            SCOPES = ['https://www.googleapis.com/auth/drive.file']
            
            creds = None
            token_path = 'token.json'
            
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('drive', 'v3', credentials=creds)
            return True
            
        except Exception as e:
            logger.error(f"Erreur configuration Google Drive: {e}")
            return False
    
    def upload_folder(self, local_folder_path, drive_folder_name):
        """Upload un dossier et sa structure vers Google Drive"""
        try:
            from googleapiclient.http import MediaFileUpload

            # Créer le dossier racine pour cette sauvegarde sur Drive
            root_folder_metadata = {
                'name': drive_folder_name,
                'parents': [self.google_drive_folder_id],
                'mimeType': 'application/vnd.google-apps.folder'
            }
            root_folder = self.service.files().create(body=root_folder_metadata, fields='id').execute()
            root_folder_id = root_folder.get('id')

            # Dictionnaire pour mapper les chemins locaux aux IDs de dossier Drive
            path_to_drive_id = {str(Path(local_folder_path).resolve()): root_folder_id}

            # 1. Créer l'arborescence des dossiers sur Google Drive
            logger.info("Création de l'arborescence des dossiers sur Google Drive...")
            for root, dirs, _ in os.walk(local_folder_path):
                resolved_root = str(Path(root).resolve())
                parent_folder_id = path_to_drive_id[resolved_root]
                
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    resolved_dir_path = str(Path(dir_path).resolve())

                    folder_metadata = {
                        'name': dir_name,
                        'parents': [parent_folder_id],
                        'mimeType': 'application/vnd.google-apps.folder'
                    }
                    folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                    new_folder_id = folder.get('id')
                    path_to_drive_id[resolved_dir_path] = new_folder_id
                    logger.info(f"Dossier créé sur Drive: {os.path.relpath(dir_path, local_folder_path)}")

            # 2. Uploader les fichiers dans les bons dossiers
            logger.info("Upload des fichiers...")
            for root, _, files in os.walk(local_folder_path):
                resolved_root = str(Path(root).resolve())
                parent_folder_id = path_to_drive_id[resolved_root]

                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    
                    file_metadata = {
                        'name': file_name,
                        'parents': [parent_folder_id]
                    }
                    
                    media = MediaFileUpload(file_path, resumable=True)
                    self.service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields='id'
                    ).execute()
                    
                    relative_path = os.path.relpath(file_path, local_folder_path)
                    logger.info(f"Fichier uploadé: {relative_path}")
            
            logger.info(f"Dossier complet uploadé vers Google Drive: {drive_folder_name}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur upload Google Drive: {e}")
            return False

class SlackBackupAutomation:
    def __init__(self):
        self.exporter = SlackExporter()
        self.uploader = GoogleDriveUploader()
        self.temp_dir = Path(CONFIG["temp_dir"])
        self.backup_dir = Path(CONFIG["backup_dir"])
        
        # Créer les dossiers nécessaires
        self.temp_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
    
    def cleanup_temp_files(self):
        """Nettoie les fichiers temporaires"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
    
    def run_attachment_script(self, export_path):
        """Exécute le script de téléchargement des pièces jointes"""
        try:
            script_path = Path(CONFIG["download_script_path"])
            print(script_path)
            if not script_path.exists():
                logger.error(f"Script non trouvé: {script_path}")
                return False
            
            # Rendre le script exécutable
            os.chmod(script_path, 0o755)
            
            # Exécuter le script avec le chemin d'export
            result = subprocess.run([
                "bash",
                str(script_path),
                "-p",
                str(export_path)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Script d'attachements exécuté avec succès")
                return True
            else:
                logger.error(f"Erreur script: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur exécution script: {e}")
            return False
        
    def get_history(self, channel_id: str, limit: int = 15, since_days: str = 0):
        """Récupère l'historique complet d'un canal avec pagination."""
        all_messages = []
        cursor = None
        oldest = (datetime.now() - timedelta(days=since_days)).timestamp()
        
        logger.info(f"Récupération de l'historique pour le canal {channel_id}...")
        
        while True:
            try:
                params = {
                    "channel": channel_id,
                    "limit": limit, 
                    "oldest": oldest
                }
                if cursor:
                    params["cursor"] = cursor

                response = requests.get(
                    "https://slack.com/api/conversations.history",
                    headers=self.exporter.headers,
                    params=params
                )
                
                if response.status_code == 429: # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited. Attente de {retry_after} secondes...")
                    time.sleep(retry_after)
                    continue

                response.raise_for_status()
                data = response.json()

                if data.get("ok"):
                    all_messages.extend(data.get("messages", []))
                    
                    if data.get("has_more"):
                        cursor = data.get("response_metadata", {}).get("next_cursor")
                        if not cursor:
                            logger.warning("has_more is true, mais aucun next_cursor trouvé. Arrêt de la pagination.")
                            break
                        logger.info(f"Page suivante pour le canal {channel_id}...")
                        time.sleep(1)  # Attendre 1 seconde entre les requêtes pour être respectueux
                    else:
                        break
                else:
                    logger.error(f"Erreur API Slack pour le canal {channel_id}: {data.get('error')}")
                    break

            except requests.exceptions.RequestException as e:
                logger.error(f"Erreur de requête lors de la récupération de l'historique pour {channel_id}: {e}")
                break
            except Exception as e:
                logger.error(f"Erreur inattendue dans get_history pour {channel_id}: {e}")
                break

        logger.info(f"{len(all_messages)} messages récupérés pour le canal {channel_id}.")
        return {"ok": True, "messages": all_messages, "has_more": False}

    def create_manual_export(self):
        """Crée un export manuel via l'API Slack"""
        try:
            export_dir = self.temp_dir / "manual_export"
            export_dir.mkdir(exist_ok=True)
            
            # Récupérer la liste des conversations
            conversations = self.exporter.get_channels_list()
            with open(export_dir / f"channels.json", 'w') as f:
                json.dump(conversations, f, indent=2)
            
            for conv in conversations:
                
                conv_id = conv["id"]
                conv_name = conv.get("name", conv_id)

                # La limite ici est la taille du lot par page
                history = self.get_history(channel_id=conv_id, since_days=30)
                
                if history.get("ok"):
                    # Sauvegarder l'historique
                    with open(export_dir / f"{conv_name}.json", 'w') as f:
                        json.dump(history, f, indent=2)

    
            logger.info(f"Export manuel créé: {export_dir}")
            return str(export_dir)
            
        except Exception as e:
            logger.error(f"Erreur création export manuel: {e}")
            return None
    
    def run_backup(self):
        """Exécute le processus complet de sauvegarde"""
        logger.info("=== Début de la sauvegarde Slack ===")
        
        try:     
            # 1. Créer un export (manuel pour l'instant)
            export_path = self.create_manual_export()
            if not export_path:
                logger.error("Impossible de créer l'export")
                return False
            
            # 2. Préparer le dossier de sauvegarde
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_folder = self.backup_dir / f"slack_backup_{timestamp}"
            shutil.copytree(export_path, backup_folder)
            
            # 3. Exécuter le script de téléchargement des pièces jointes
            if not self.run_attachment_script(backup_folder):
                logger.warning("Erreur lors du téléchargement des pièces jointes")

            # 4. Upload vers Google Drive
            if self.uploader.setup_credentials():
                drive_folder_name = f"Slack_Backup_{timestamp}"
                if self.uploader.upload_folder(str(backup_folder), drive_folder_name):
                    logger.info("Sauvegarde uploadée vers Google Drive")

                    # 5. Nettoyer
                    self.cleanup_temp_files()
                else:
                    logger.error("Erreur upload Google Drive")
            
            logger.info("=== Sauvegarde terminée avec succès ===")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            return False

def main():
    """Fonction principale"""
    automation = SlackBackupAutomation()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--run-once":
        # Exécution unique
        automation.run_backup()
    else:
        # Exécution périodique (tous les 3 mois)
        logger.info("Mode automatique activé - sauvegarde tous les 3 mois")
        
        while True:
            automation.run_backup()
            
            # Attendre 3 mois (90 jours)
            next_run = datetime.now() + timedelta(days=90)
            logger.info(f"Prochaine sauvegarde: {next_run}")
            
            # Attendre 3 mois
            time.sleep(90 * 24 * 60 * 60)  # 90 jours en secondes

if __name__ == "__main__":
    main()
