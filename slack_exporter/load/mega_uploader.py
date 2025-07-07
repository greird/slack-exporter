import subprocess

from slack_exporter.load.uploader import Uploader
from slack_exporter.logger_config import logger


class MegaUploader(Uploader):
    """This class handles uploading files to Mega.io using the megacmd command-line tool.
    It requires `megacmd` to be installed and available in the system's PATH.

    Attributes:
        credentials (dict[str, str]): A dictionary containing 'login' and 'password' for Mega.io authentication.
    """
    
    def __init__(self, credentials: dict[str, str]):
        super().__init__(credentials)

        try:
            mega_version = subprocess.run('mega-version', check=True, capture_output=True)
            logger.info(f"{mega_version.stdout.decode().strip()} is available.")

        except subprocess.CalledProcessError as e:
            raise FileNotFoundError("megacmd not found. Please ensure it is installed and in your system's PATH.")

    def authenticate(self, credentials: dict[str, str]) -> bool:
        """This method uses the `mega-login` command from megacmd to authenticate.

        Raises:
            CalledProcessError: Error with MegaCmd CLI tool
            ConnectionError: Unknown error preventing authentication

        Returns:
            bool: True if authentication was successful.
        """

        try:
            command = [
                "mega-login",
                credentials["login"],
                credentials["password"]
            ]
 
            result = subprocess.run(command, check=True, capture_output=True, text=True)

        except subprocess.CalledProcessError as e:
            if e.returncode == 54:
                logger.info("Already authenticated to Mega.io.")
                return True
            else:
                raise subprocess.CalledProcessError(f"Error running MegaCmd: {e}")
        except Exception as e:
                raise ConnectionError(f"Mega.io login failed: {e}")

        logger.info(f"{result.stdout.strip()}")
        return True

    def upload_folder(self, local_folder_path: str, remote_folder_id: str = "") -> None:
        """Uploads a folder and its structure to Mega.io using megacmd.

        Args:
            local_folder_path: The local path to the folder to upload.
            remote_folder_id: The ID of the remote folder in Mega.io where the folder will be uploaded.

        Raises:
            CalledProcessError: Any error related to MegaCmd CLI.

        Returns:
            bool: True if authentication was successful, False otherwise.
        """

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
    