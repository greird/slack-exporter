import json
import shutil
from datetime import datetime
from pathlib import Path
from datetime import datetime, timedelta

from slack_exporter.config import CONFIG, logger
from slack_exporter.uploader.google_drive_uploader import GoogleDriveUploader
from slack_exporter.uploader.mega_uploader import MegaUploader
from slack_exporter.exporter.slack_exporter import SlackExporter
from slack_exporter.tools import get_files_in_folder, check_and_compress_file


class Orchestration:
    def __init__(self):
        self.exporter = SlackExporter()
        if CONFIG["uploader_service"] == "google_drive":
            self.uploader = GoogleDriveUploader()
        elif CONFIG["uploader_service"] == "mega":
            self.uploader = MegaUploader()
        else:
            raise ValueError("Invalid uploader service specified in config.py")
        self.backup_dir = Path(CONFIG["backup_dir"])
        
        # Créer les dossiers nécessaires
        self.backup_dir.mkdir(exist_ok=True)
    
    def cleanup_temp_files(self):
        """Cleans up temporary files"""
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)

    def create_manual_export(self, export_path: Path) -> Path:
        """Creates a manual export via the Slack API"""
        try:
            export_path.mkdir(exist_ok=True)

            # Récupérer la liste des conversations
            conversations = self.exporter.get_channels_list()
            with open(export_path / f"channels.json", 'w') as f:
                json.dump(conversations, f, indent=2)
            
            for conv in conversations:
                
                conv_id = conv["id"]
                conv_name = conv.get("name", conv_id)

                # La limite ici est la taille du lot par page
                oldest_ts = (datetime.now() - timedelta(days=15)).timestamp()
                history = self.exporter.get_history(channel_id=conv_id, oldest=oldest_ts)
                
                if history.get("ok"):
                    # Sauvegarder l'historique
                    with open(export_path / f"{conv_name}.json", 'w') as f:
                        json.dump(history, f, indent=2)

            logger.info(f"Manual export created: {export_path}")
            return export_path

        except Exception as e:
            logger.error(f"Error creating manual export: {e}")
            return None
    
    def run_backup(self):
        """Runs the complete backup process"""
        logger.info("=== Starting Slack backup ===")
        
        try:     
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_folder = self.backup_dir / f"slack_backup_{timestamp}"

            # 1. Créer un export (manuel pour l'instant)
            export_path = self.create_manual_export(export_path=backup_folder)
            if not export_path:
                logger.error("Could not create export")
                return False
            
            # 3. Exécuter le script de téléchargement des pièces jointes
            self.exporter.download_attachments(export_path)

            # 4. Compress files when needed
            files = get_files_in_folder(export_path)
            for file in files:
                check_and_compress_file(file_path=file, max_size=100*1000000, replace=True)

            # 5. Upload vers Google Drive
            if self.uploader.setup_credentials():
                cloud_folder_name = f"Slack_Backup_{timestamp}"
                if self.uploader.upload_folder(str(export_path), cloud_folder_name):
                    logger.info("Backup uploaded to cloud storage")

                    # 6. Nettoyer
                    self.cleanup_temp_files()
                else:
                    logger.error("Cloud storage upload error")
            
            logger.info("=== Backup completed successfully ===")
            return True
            
        except Exception as e:
            logger.error(f"Error during backup: {e}")
            return False