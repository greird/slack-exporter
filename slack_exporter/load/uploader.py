from abc import ABC, abstractmethod


class Uploader(ABC):
    def __init__(self, credentials: str | dict):
        """Initializes the uploader"""
        self.credentials = credentials

    @abstractmethod
    def authenticate(self) -> bool:
        """Sets up the credentials for the uploader"""
        ...

    def upload_folder(self, local_folder_path: str, remote_folder_id: str) -> bool:
        """Uploads a folder and its structure to the remote storage"""
        ...