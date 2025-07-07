from abc import ABC, abstractmethod


class Uploader(ABC):
    """Abstract base class for uploaders that defines the structure for uploading data to remote storage.
    
    This class should be subclassed to implement specific upload logic for different storage services.

    Attributes:
        authenticated (bool): Indicates whether the uploader is authenticated.
        credentials (str | dict[str, str]): Credentials for accessing remote storage. This can be a path to a credentials file or a dictionary containing login and password.

    Raises:
        ConnectionError if authentication to Uploader service failed.
    """

    def __init__(self, credentials: str | dict[str, str] = None):
        """Initializes the uploader"""
        if not self.authenticate(credentials):
            raise ConnectionError("Could not authenticate to uploader service.")

    @abstractmethod
    def authenticate(self, credentials: str | dict[str, str]) -> bool:
        """Authenticates the exporter. Returns True if successful, False otherwise.
        This method should be implemented by subclasses to handle specific authentication logic.
        
        Returns:
            bool: True if authentication was successful.
        """
        ...


    @abstractmethod
    def upload_folder(self, local_folder_path: str, remote_folder_id: str = "") -> bool:
        """Uploads a folder and its structure to the remote storage

        Args:
            local_folder_path (str): The local path to the folder to upload.
            remote_folder_id (str, optional): The ID of the remote folder where the local folder will be uploaded.

        Returns:
            bool: True if the upload was successful, False otherwise
        """
        ...