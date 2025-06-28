import json
import shutil
from datetime import datetime
from pathlib import Path
from datetime import datetime, timedelta

from config import CONFIG, logger
from google_drive_uploader import GoogleDriveUploader
from slack_exporter import SlackExporter
from tools import run_bash_script, get_files_in_folder, check_and_compress_file


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
        """Cleans up temporary files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)

    def create_manual_export(self):
        """Creates a manual export via the Slack API"""
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
                oldest_ts = (datetime.now() - timedelta(days=90)).timestamp()
                history = self.exporter.get_history(channel_id=conv_id, oldest=oldest_ts)
                
                if history.get("ok"):
                    # Sauvegarder l'historique
                    with open(export_dir / f"{conv_name}.json", 'w') as f:
                        json.dump(history, f, indent=2)

    
            logger.info(f"Manual export created: {export_dir}")
            return str(export_dir)
            
        except Exception as e:
            logger.error(f"Error creating manual export: {e}")
            return None
    
    def run_backup(self):
        """Runs the complete backup process"""
        logger.info("=== Starting Slack backup ===")
        
        try:     
            # 1. Créer un export (manuel pour l'instant)
            export_path = self.create_manual_export()
            if not export_path:
                logger.error("Could not create export")
                return False
            
            # 2. Préparer le dossier de sauvegarde
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_folder = self.backup_dir / f"slack_backup_{timestamp}"
            shutil.copytree(export_path, backup_folder)
            
            # 3. Exécuter le script de téléchargement des pièces jointes
            script_path = Path(CONFIG["download_script_path"])
            if not run_bash_script(
                script_path=script_path, 
                params=f"-p {str(backup_folder)}", 
                capture_output=False
            ):
                logger.warning("Error downloading attachments")

            # 4. Compress files when needed
            files = get_files_in_folder(backup_folder)
            for file in files:
                check_and_compress_file(file_path=file, max_size=100*1000000, replace=True)

            # 5. Upload vers Google Drive
            if self.uploader.setup_credentials():
                drive_folder_name = f"Slack_Backup_{timestamp}"
                if self.uploader.upload_folder(str(backup_folder), drive_folder_name):
                    logger.info("Backup uploaded to Google Drive")

                    # 6. Nettoyer
                    self.cleanup_temp_files()
                else:
                    logger.error("Google Drive upload error")
            
            logger.info("=== Backup completed successfully ===")
            return True
            
        except Exception as e:
            logger.error(f"Error during backup: {e}")
            return False