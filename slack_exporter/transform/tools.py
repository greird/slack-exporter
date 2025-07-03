import os
from pathlib import Path

from slack_exporter.logger_config import logger


def create_folder_if_not_exists(folder_path: str) -> bool:
    """Creates a folder if it does not exist"""
    try:
        Path(folder_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Folder creation error {folder_path}: {e}")
        return False

def get_files_in_folder(folder_path: Path, file_list: list[Path] = None) -> list[Path]:
    """Returns a list of all files (as paths) inside a given folder and its subdirectories.

    Args:
        folder_path: The path to the folder to search.

    Returns:
        A list of Path objects, each representing a file.
    """
    if not folder_path.is_dir():
        raise NotADirectoryError(f"Folder not found or is not a directory: {folder_path}")

    if not file_list:
        file_list = []

    for root, subdir, files in os.walk(folder_path):
        for file in files:
            file_list.append(Path(root) / file)

        if subdir:
            for dir in subdir:
                folder_path = Path(root) / dir
                return get_files_in_folder(folder_path, file_list)
        
    return file_list
