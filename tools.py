import os
import subprocess
from pathlib import Path

from config import CONFIG, logger


def run_bash_script(script_path: str, params: str, capture_output: bool = True):

    try:
        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            return False
        
        # Rendre le script exécutable
        os.chmod(script_path, 0o755)
        
        # Exécuter le script avec le chemin d'export
        result = subprocess.run([
            "bash",
            script_path,
            *params.split()
        ], capture_output=capture_output, text=True)
        
        if result.returncode == 0:
            logger.info("Script executed successfully")
            return True
        else:
            logger.error(f"Script error: {result.stderr}")
            return False
        
    except Exception as e:
        logger.error(f"Script execution error: {e}")
        return False