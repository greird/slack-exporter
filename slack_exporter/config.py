import logging
import os
import sys

CONFIG = {
    "backup_dir": "./slack_backups",
    "google_credentials_path": os.getenv("GOOGLE_CREDENTIALS_PATH"),
    "google_drive_folder_id": os.getenv("GOOGLE_DRIVE_FOLDER_ID", '1nFlVku9UCtKgc0yhqBZilfi5hZlEF36i'),
    "log_file": "./slack_automation.log",
    "mega_credentials": {"login": os.getenv("MEGA_EMAIL"), "password": os.getenv("MEGA_PASSWORD")},
    "remote_folder_id": os.getenv("REMOTE_FOLDER_ID"),
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