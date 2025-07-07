import os
from datetime import datetime, timedelta
from dotenv import load_dotenv, find_dotenv

from slack_exporter.logger_config import logger
from slack_exporter.etl import (
    SlackToGoogleDrive, 
    SlackToLocal,
    SlackToMega,
    UploadFolderToGoogleDrive
)

load_dotenv(dotenv_path=find_dotenv(raise_error_if_not_found=True))

# GLOBAL CONFIG
local_dir = f"./slack_backups_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
oldest_timestamp = (datetime.now() - timedelta(days=90)).timestamp() # last 90 days of data

# MEGA CONFIG
mega_credentials = {
    "login": os.getenv("MEGA_EMAIL"), 
    "password": os.getenv("MEGA_PASSWORD")
}

# GOOGLE DRIVE CONFIG
google_drive_parent_dir = os.getenv("GOOGLE_DRIVE_PARENT_FOLDER_ID")
google_drive_credentials_path = os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH")

if __name__ == "__main__":
    logger.info("=== Starting Slack backup ===")

    # Uncomment the lines below to run the export of your choice

    # # Export and store data locally
    # SlackToLocal(
    #     local_dir=local_dir,
    #     oldest_timestamp=oldest_timestamp
    # ).run()

    # Export all in a slack_backup folder, add a timestamp as a suffix to each file and upload at the root of the Mega directory.
    SlackToMega(
        local_dir="./slack_backup",
        remote_dir="",
        credentials=mega_credentials,
        file_suffix=f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        oldest_timestamp=oldest_timestamp
    ).run()

    # # Export and upload local_dir to a remote_folder in Google Drive.
    # SlackToGoogleDrive(
    #     local_dir=local_dir,
    #     remote_dir=google_drive_parent_dir,
    #     credentials=google_drive_credentials_path,
    #     oldest_timestamp=oldest_timestamp
    # ).run()

    logger.info("=== Slack backup completed ===")
