import subprocess

from slack_exporter.config import logger
from slack_exporter.load.uploader import Uploader


class MegaUploader(Uploader):
    def __init__(self, credentials: dict[str, str]):
        """Initializes the MegaUploader."""
        self.credentials = credentials
        super().__init__(credentials=self.credentials)

        try:
            mega_version = subprocess.run('mega-version', check=True, capture_output=True)
            logger.info(f"{mega_version.stdout.decode().strip()} is available.")

        except subprocess.CalledProcessError as e:
            logger.error(f"megacmd not found. Please ensure it is installed and in your system's PATH.")
            return False

    def authenticate(self) -> bool:
        """Configures Mega.io credentials using megacmd."""

        try:
            command = [
                "mega-login",
                self.credentials["login"],
                self.credentials["password"]
            ]
 
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            logger.info(f"{result.stdout.strip()}")

            return True

        except subprocess.CalledProcessError as e:
            if e.returncode == 54:
                logger.info("Already authenticated to Mega.io.")
                return True
            else:
                logger.error("Mega.io login failed. Please check your credentials.")
                return False

    def upload_folder(self, local_folder_path: str, remote_folder_id: str = "") -> bool:
        """Uploads a folder and its structure to Mega.io using megacmd.

        Args:
            local_folder_path: The local path to the folder to upload.
            remote_folder_id: The ID of the remote folder in Mega.io where the folder will be uploaded.
        """
        logger.info(f"Authenticating to Mega.io...")
        self.authenticate()  # Ensure we are authenticated before uploading

        try:

            logger.info(f"Uploading folder {local_folder_path} to Mega.io in {remote_folder_id}...")
            
            command = [
                "mega-put",
                "-c",
                local_folder_path,
                remote_folder_id
            ]
            
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            logger.info(f"{result.stdout.strip()}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Mega.io upload error (megacmd exited with code {e.returncode}): {e.stderr.strip()}")
            return False
        except Exception as e:
            logger.error(f"Mega.io upload error: {e}")
            return False