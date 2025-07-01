import subprocess

from slack_exporter.config import logger
from slack_exporter.load.uploader import Uploader


class MegaUploader(Uploader):
    def __init__(self, credentials: dict[str, str]):
        """Initializes the MegaUploader."""
        self.credentials = credentials
        super().__init__(credentials=self.credentials)

    def authenticate(self) -> bool:
        """Configures Mega.io credentials using megacmd."""
        try:
            mega_version = subprocess.run('mega-version', check=True, capture_output=True)
            logger.info(f"{mega_version.stdout.decode().strip()} is available.")


            command = [
                "mega-login",
                self.credentials["login"],
                self.credentials["password"]
            ]
            
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            logger.info(f"{result.stdout.strip()}")

            return True
        except FileNotFoundError:
            logger.error(f"megacmd not found. Please ensure it is installed and in your system's PATH.")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Error checking megacmd version: {e}") # TODO status 54 is OK!
            return False
        except Exception as e:
            logger.error(f"Mega.io configuration error: {e}")
            return False

    def upload_folder(self, local_folder_path: str, remote_folder_id: str) -> bool:
        """Uploads a folder and its structure to Mega.io using megacmd.

        Args:
            local_folder_path: The local path to the folder to upload.
        """
        logger.info(f"Authenticating to Mega.io...")
        self.authenticate()  # Ensure we are authenticated before uploading

        try:
            # Construct the remote path. We'll upload into the specified mega_folder_id
            # and create a subfolder with mega_folder_name.
            remote_path = f"/{remote_folder_id}"

            logger.info(f"Uploading folder {local_folder_path} to Mega.io at {remote_path}...")
            
            command = [
                "mega-put",
                "-c",
                local_folder_path,
                remote_path
            ]
            
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            logger.info(f"megacmd output: {result.stdout.strip()}")
            
            logger.info(f"Full folder uploaded to Mega.io: {remote_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Mega.io upload error (megacmd exited with code {e.returncode}): {e.stderr.strip()}")
            return False
        except Exception as e:
            logger.error(f"Mega.io upload error: {e}")
            return False