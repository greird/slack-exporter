from pathlib import Path

from abc import ABC, abstractmethod

class Exporter(ABC):
    """
    Abstract base class for exporters that defines the structure for exporting data. 

    Methods:
        authenticate(): Authenticates the exporter. Returns True if successful, False otherwise.
        export(): Exports all data and returns the path to the exported data.
    """

    def __init__(self):
        self.authenticated = self.authenticate()

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticates the exporter. Returns True if successful, False otherwise.
        This method should be implemented by subclasses to handle specific authentication logic.
        
        Returns:
            bool: True if authentication was successful, False otherwise.
        """
        pass

    @abstractmethod
    def export(self, export_path: Path, file_suffix: str = None, oldest_timestamp: float = None) -> str:
        """Exports all data and returns the path to the exported data.
        This method should be implemented by subclasses to handle specific export logic.
        
        Args:
            export_path (Path): The path where the exported data will be saved.
            file_suffix (str, optional): Optional suffix for files to be processed.
            oldest_timestamp (float, optional): Optional timestamp to filter data. If provided, only data older than this timestamp will be exported.
            
        Returns:
            str: The path to the exported data.
        """
        pass