import gzip
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

def check_and_compress_file(file_path: Path, max_size: int, replace: bool = False) -> Path | None:
    """Checks a file's size and compresses it if it's above a given threshold.

    Args:
        file_path: The path to the file to check and compress.
        max_size: The maximum allowed size in bytes before compression.

    Returns:
        The path to the new compressed file if succeeded.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        RuntimeError: If compression fails.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size = file_path.stat().st_size

    if file_size > max_size:
        logger.info(f"{file_size=}")
        compressed_file_path = file_path.with_suffix(file_path.suffix + ".gz")
        try:
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_file_path, 'wb') as f_out:
                    f_out.writelines(f_in)
            logger.info(f"Compressed {file_path} to {compressed_file_path}")

            if replace:
                file_path.unlink() 

            return compressed_file_path
        except Exception as e:
            raise RuntimeError(f"Failed to compress file {file_path}: {e}")

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