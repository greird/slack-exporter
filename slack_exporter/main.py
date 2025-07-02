import os
from datetime import datetime, timedelta

from slack_exporter.logging import logger
from slack_exporter.etl import (
    SlackToGoogleDrive, 
    SlackToLocal,
    SlackToLocalWithCompression,
    SlackToMega,
    UploadFolderToGoogleDrive
)

if __name__ == "__main__":
    logger.info("=== Starting Slack backup ===")
    # Uncomment the line below to run the Mega.io export
    SlackToMega(
        local_dir=f"./slack_backups_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        remote_dir="",
        credentials={"login": os.getenv("MEGA_EMAIL"), "password": os.getenv("MEGA_PASSWORD")},
        file_suffix=f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        oldest_timestamp=(datetime.now() - timedelta(days=90)).timestamp()
    ).run()

    # Uncomment the line below to run the Google Drive export
    # SlackToGoogleDrive(
    #     local_dir=f"./slack_backups_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    #     remote_dir='1Ylrd8evEMdc_LCEWER6wttdQqO8JZck2',
    #     credentials='credentials.json',
    #     oldest_timestamp=(datetime.now() - timedelta(days=90)).timestamp()
    # ).run()

    logger.info("=== Slack backup completed ===")
