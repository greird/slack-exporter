import os
from pathlib import Path

from slack_exporter.logger_config import logger
from slack_exporter.transform.tools import get_files_in_folder, create_folder_if_not_exists

class FileOrganizer:
    """Class for organizing files in a directory."""
    
    def __init__(self, base_folder: Path):
        """Initializes the FileOrganizer with a base folder.

        Args:
            base_folder: The Path object representing the base folder where files are organized.
        """
        if not base_folder.is_dir():
            raise NotADirectoryError(f"Base folder is not a directory: {base_folder}")
        
        self.base_folder = base_folder

    def organize_files(self) -> None:
        """Organizes files in the specified target folder by their extension."""
        existing_folders_path_list = [f for f in self.base_folder.iterdir() if f.is_dir()]
        for folder_path in existing_folders_path_list:
            files = get_files_in_folder(folder_path)
            files_by_extension = self.sort_files_by_extension(files)

            for ext, file_list in files_by_extension.items():
                target_folder = folder_path.joinpath(ext)
                
                create_folder_if_not_exists(str(target_folder))

                self.move_files_to_folder(
                    files=file_list, 
                    target_folder=target_folder
                )

    @staticmethod
    def sort_files_by_extension(files: list[Path]) -> dict[str, list[Path]]:
        """Sorts a list of files by their extension.

        Args:
            files: A list of Path objects representing the files to sort.

        Returns:
            A dictionary where the keys are file extensions and the values are lists of files with that extension.
        """
        sorted_files = {}
        for file in files:
            ext = file.suffix[1:]  # Get the file extension without the dot
            if ext not in sorted_files:
                sorted_files[ext] = []
            sorted_files[ext].append(file)

        return sorted_files

    @staticmethod
    def move_files_to_folder(files: list[Path], target_folder: Path) -> None:
        """Moves a list of files to a specified target folder.

        Args:
            files: A list of Path objects representing the files to move.
            target_folder: The Path object representing the target folder.

        Raises:
            FileNotFoundError: If any file does not exist.
            NotADirectoryError: If the target folder is not a directory.
        """
        if not target_folder.is_dir():
            raise NotADirectoryError(f"Target folder is not a directory: {target_folder}")
        
        for file in files:
            if not file.exists():
                raise FileNotFoundError(f"File not found: {file}")
            
            new_path = target_folder / file.name
            file.rename(new_path)
            logger.info(f"Moved {file} to {new_path}")