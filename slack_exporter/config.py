import logging
import os
import sys

CONFIG = {
    "slack_token": os.getenv("SLACK_BOT_TOKEN"),
    "google_drive_folder_id": os.getenv("GOOGLE_DRIVE_FOLDER_ID", "1nFlVku9UCtKgc0yhqBZilfi5hZlEF36i"),
    "google_credentials_path": os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json"),
    "backup_dir": "./slack_backups",
    "log_file": "./slack_automation.log",
    "mega_folder_id": os.getenv("MEGA_FOLDER_ID", "slack_backups"),
    "uploader_service": os.getenv("UPLOADER_SERVICE", "mega")
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