import gzip
import os
from pathlib import Path

from slack_exporter.config import logger


def create_folder_if_not_exists(folder_path: str):
    """Creates a folder if it does not exist"""
    try:
        Path(folder_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Folder creation error {folder_path}: {e}")
        return False

def check_and_compress_file(file_path: Path, max_size: int, replace: bool = False) -> Path:
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
    else:
        return file_path

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