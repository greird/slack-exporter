import os
import json
import time
import shutil
import subprocess
import requests
from datetime import datetime, timedelta
from pathlib import Path

from config import CONFIG, logger
from slack_exporter import SlackExporter
from google_drive_uploader import GoogleDriveUploader

class Orchestration:
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
    
    @staticmethod
    def run_attachment_script(export_path):
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