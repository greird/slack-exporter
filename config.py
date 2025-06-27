import os
import sys
import logging

CONFIG = {
    "slack_token": os.getenv("SLACK_BOT_TOKEN"),  # Token bot Slack
    "google_drive_folder_id": os.getenv("GOOGLE_DRIVE_FOLDER_ID"),
    "google_credentials_path": os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json"),
    "download_script_path": "./download_attachments.sh",  # Chemin vers votre script
    "temp_dir": "./temp_slack_export",
    "backup_dir": "./slack_backups",
    "log_file": "./slack_automation.log"
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