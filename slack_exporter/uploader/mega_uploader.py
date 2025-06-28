import subprocess

from config import CONFIG, logger


class MegaUploader:
    def __init__(self):
        """Initializes the MegaUploader."""
        # self.mega_email = CONFIG["mega_email"]
        # self.mega_password = CONFIG["mega_password"]
        self.mega_folder_id = CONFIG["mega_folder_id"]
        self.megacmd_path = "megacmd" # Assuming megacmd is in PATH
    
    def setup_credentials(self):
        """Configures Mega.io credentials using megacmd. 
        Assumes megacmd is already configured or login details are in environment variables.
        """
        try:
            # Test if megacmd is available
            subprocess.run('mega-version', check=True, capture_output=True)
            logger.info("megacmd is available.")
            # For megacmd, authentication is usually handled by `mega-cmd-server` or `mega-login`
            # We'll assume it's already logged in or configured via environment variables.
            return True
        except FileNotFoundError:
            logger.error(f"megacmd not found. Please ensure it is installed and in your system's PATH.")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Error checking megacmd version: {e.stderr.decode().strip()}")
            return False
        except Exception as e:
            logger.error(f"Mega.io configuration error: {e}")
            return False
    
    def upload_folder(self, local_folder_path: str, mega_folder_name: str):
        """Uploads a folder and its structure to Mega.io using megacmd.

        Args:
            local_folder_path: The local path to the folder to upload.
            mega_folder_name: The name of the folder to create on Mega.io.
        """
        try:
            # Construct the remote path. We'll upload into the specified mega_folder_id
            # and create a subfolder with mega_folder_name.
            remote_path = f"/{self.mega_folder_id}/{mega_folder_name}"

            logger.info(f"Uploading folder {local_folder_path} to Mega.io at {remote_path}...")
            
            # Use 'megacmd put -r' to recursively upload the folder
            command = [
                "mega-put",
                "-c",
                local_folder_path,
                remote_path
            ]
            
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            logger.info(f"megacmd output: {result.stdout.strip()}")
            
            logger.info(f"Full folder uploaded to Mega.io: {mega_folder_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Mega.io upload error (megacmd exited with code {e.returncode}): {e.stderr.strip()}")
            return False
        except Exception as e:
            logger.error(f"Mega.io upload error: {e}")
            return False