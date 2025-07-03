import shutil
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from slack_exporter.extract.exporter import Exporter
from slack_exporter.extract.slack_exporter import SlackExporter
from slack_exporter.load.google_drive_uploader import GoogleDriveUploader
from slack_exporter.load.mega_uploader import MegaUploader
from slack_exporter.load.uploader import Uploader
from slack_exporter.logger_config import logger
from slack_exporter.transform.compress import FileCompressor
from slack_exporter.transform.organize import FileOrganizer
from slack_exporter.transform.tools import get_files_in_folder


class ETL(ABC):
    """
    This class defines the basic structure for ETL operations, including extract, transform, and load methods.
    Subclasses should implement the run method to execute the ETL process.

    Attributes:
        local_dir (Path): The local directory where data will be stored.
        remote_dir (str): The remote directory where data will be uploaded.
        credentials (dict[str, str]): Credentials for accessing remote storage.
        file_suffix (str): Optional suffix for files to be processed.
        oldest_timestamp (datetime.timestamp): Optional timestamp to filter data.
    """
    
    def __init__(
            self, 
            local_dir: str, 
            remote_dir: str = None, 
            credentials: dict[str, str] = None,
            file_suffix: str = None,
            oldest_timestamp: datetime.timestamp = None
        ):
        self.local_dir = Path(local_dir)
        self.remote_dir = remote_dir
        self.credentials = credentials
        self.file_suffix = file_suffix
        self.oldest_timestamp = oldest_timestamp

    def _extract(self, exporter: Exporter) -> Path:
        """Extracts data from a source using the provided exporter.
        
        Args:
            exporter: An instance of an exporter class to handle data extraction.

        Returns:
            Path: The path to the exported data or None if an error occurred.
        """
        
        try:
            return exporter.export(
                export_path=self.local_dir,
                oldest_timestamp=self.oldest_timestamp,
                file_suffix=self.file_suffix
            )

        except Exception as e:
            logger.error(f"Error creating export: {e}")
            return None

    def _transform(self):
        """Transforms the extracted data by compressing files and organizing them into folders."""

        logger.info("Transforming extracted data...")
    
        for file in get_files_in_folder(folder_path=self.local_dir):
            FileCompressor(max_size=100*1000000).compress_file(file_path=file, replace=True)

        FileOrganizer(self.local_dir).organize_files()

    def _load(self, uploader: Uploader, cleanup: bool = True) -> bool:
        """Loads the transformed data into the desired storage location using the provided uploader.

        Args:
            uploader: An instance of an Uploader class to handle data upload.
            cleanup (bool): Whether to remove the local directory after upload.
            
        Returns:
            bool: True if the upload was successful, False otherwise."""
        
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
        """This method should be implemented by subclasses to define the specific ETL workflow. For instance, it may call the extract, transform, and load methods in sequence.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        pass


class SlackToMega(ETL):

    def run(self):
        self._extract(exporter=SlackExporter())
        self._transform()
        self._load(uploader=MegaUploader(credentials=self.credentials))


class SlackToGoogleDrive(ETL):
    
    def run(self):
        self._extract(exporter=SlackExporter())
        self._transform()
        self._load(uploader=GoogleDriveUploader(credentials=self.credentials))

class SlackToLocal(ETL):
    """Slack ETL process that saves data locally without uploading to cloud storage."""

    def run(self):
        self._extract(exporter=SlackExporter())
        self._transform()
        logger.info(f"Data saved locally at {self.local_dir}")
        return self.local_dir
    
class SlackToLocalWithCompression(ETL):
    """Slack ETL process that saves data locally and compresses it."""

    def run(self):
        self._extract(exporter=SlackExporter())
        self._transform()
        compressed_file = FileCompressor(max_size=100*1000000).compress_file(file_path=self.local_dir, replace=True)
        logger.info(f"Data saved and compressed locally at {compressed_file}")
        return compressed_file
    
class UploadFolderToGoogleDrive(ETL):
    """Uploads a local folder to Google Drive."""

    def run(self):
        self._load(uploader=GoogleDriveUploader(credentials=self.credentials), cleanup=False)