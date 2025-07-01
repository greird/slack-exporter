import logging
import os
import sys

CONFIG = {
    "backup_dir": "./slack_backups",
    "google_credentials_path": os.getenv("GOOGLE_CREDENTIALS_PATH"),
    "google_drive_folder_id": os.getenv("GOOGLE_DRIVE_PARENT_FOLDER"),
    "log_file": "./slack_automation.log",
    "mega_credentials": {"login": os.getenv("MEGA_EMAIL"), "password": os.getenv("MEGA_PASSWORD")},
    "mega_parent_folder": os.getenv("MEGA_PARENT_FOLDER", ""),
    "slack_token": os.getenv("SLACK_BOT_TOKEN")
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(CONFIG["log_file"]),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)