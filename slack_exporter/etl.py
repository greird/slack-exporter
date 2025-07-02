import json
import shutil
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from slack_exporter.logging import logger
from slack_exporter.extract.slack_exporter import SlackExporter
from slack_exporter.load.google_drive_uploader import GoogleDriveUploader
from slack_exporter.load.mega_uploader import MegaUploader
from slack_exporter.load.uploader import Uploader
from slack_exporter.transform.tools import (
    check_and_compress_file,
    get_files_in_folder
)


class SlackETL(ABC):
    """Abstract base class for Slack ETL processes."""
    
    def __init__(
            self, 
            local_dir: str, 
            remote_dir: str, 
            credentials: dict[str, str],
            file_suffix: str = None,
            oldest_timestamp: datetime.timestamp = None
        ):
        self.local_dir = Path(local_dir)
        self.remote_dir = remote_dir
        self.credentials = credentials
        self.file_suffix = file_suffix
        self.oldest_timestamp = oldest_timestamp

    def _extract(self, exporter: SlackExporter, oldest_timestamp: datetime.timestamp = None) -> Path:
        """Extracts data from Slack"""
        
        try:
            self.local_dir.mkdir(parents=True, exist_ok=True)

            # Récupérer la liste des conversations
            conversations = exporter.get_channels_list()
            with open(self.local_dir / f"channels.json", 'w') as f:
                json.dump(conversations, f, indent=2)
            
            for conv in conversations:
                
                conv_id = conv["id"]
                conv_name = conv.get("name", conv_id)

                history = exporter.get_history(channel_id=conv_id, oldest=oldest_timestamp)

                if history.get("ok"):
                    # Sauvegarder l'historique
                    with open(self.local_dir / f"{conv_name}.json", 'w') as f:
                        json.dump(history, f, indent=2)

            # Download all attachments from the exported data
            exporter.download_attachments(
                export_path=self.local_dir, 
                file_suffix=self.file_suffix
                )

            logger.info(f"Export created: {self.local_dir}")
            return self.local_dir

        except Exception as e:
            logger.error(f"Error creating manual export: {e}")
            return None

    def _transform(self):
        """Transforms the extracted data"""
        logger.info("Transforming extracted data...")
    

        files = get_files_in_folder(folder_path=self.local_dir)
        for file in files:
            check_and_compress_file(file_path=file, max_size=100*1000000, replace=True)

    def _load(self, uploader: Uploader, cleanup: bool = True) -> bool:
        """Loads the transformed data into the desired format or storage"""
        logger.info(f"Loading transformed data...")

        if uploader.upload_folder(
            local_folder_path=self.local_dir, 
            remote_folder_id=self.remote_dir
            ):
            logger.info("Backup uploaded to cloud storage")

            if cleanup:
                logger.info("Cleaning up local directory...")
                shutil.rmtree(self.local_dir)
        else:
            logger.error("Cloud storage upload error")
        
        logger.info("=== Backup completed successfully ===")
        return True
    
    @abstractmethod
    def run(self):
        """Runs the ETL process"""
        pass


class SlackToMega(SlackETL):

    def run(self):
        self._extract(exporter=SlackExporter(), oldest_timestamp=self.oldest_timestamp) # TODO: Move auth to parameters
        self._transform()
        self._load(uploader=MegaUploader(credentials=self.credentials))


class SlackToGoogleDrive(SlackETL):
    
    def run(self):
        self._extract(exporter=SlackExporter(), oldest_timestamp=self.oldest_timestamp)
        self._transform()
        self._load(uploader=GoogleDriveUploader(credentials=self.credentials))

class SlackToLocal(SlackETL):
    """Slack ETL process that saves data locally without uploading to cloud storage."""

    def run(self):
        self._extract(exporter=SlackExporter(), oldest_timestamp=self.oldest_timestamp)
        self._transform()
        logger.info(f"Data saved locally at {self.local_dir}")
        return self.local_dir
    
class SlackToLocalWithCompression(SlackETL):
    """Slack ETL process that saves data locally and compresses it."""

    def run(self):
        self._extract(exporter=SlackExporter(), oldest_timestamp=self.oldest_timestamp)
        self._transform()
        compressed_file = check_and_compress_file(
            file_path=self.local_dir, 
            max_size=100*1000000, 
            replace=True
        )
        logger.info(f"Data saved and compressed locally at {compressed_file}")
        return compressed_file
    
class UploadFolderToGoogleDrive(SlackETL):
    """Uploads a local folder to Google Drive."""

    def run(self):
        self._load(uploader=GoogleDriveUploader(credentials=self.credentials), cleanup=False)