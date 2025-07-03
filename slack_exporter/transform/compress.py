import gzip
from pathlib import Path

from slack_exporter.logger_config import logger

class FileCompressor:
    """Class for compressing files that exceed a specified size limit."""
    
    def __init__(self, max_size: int = 0):
        self.max_size = max_size

    def check_file_size(self, file_path: Path) -> bool:
        """Checks if the file size exceeds the maximum size.

        Returns:
            True if the file size exceeds the maximum size, False otherwise.
        """

        file_size = file_path.stat().st_size
        return file_size > self.max_size

    def compress_file(self, file_path: Path, replace: bool = False) -> Path | None:
        """Checks a file's size and compresses it if it's above a given threshold.

        Args:
            file_path: The path to the file to check and compress.
            replace: Whether to replace the original file with the compressed one.

        Returns:
            The path to the new compressed file if succeeded.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            RuntimeError: If compression fails.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if self.check_file_size(file_path):
            
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
            