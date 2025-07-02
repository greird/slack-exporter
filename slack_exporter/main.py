from datetime import datetime, timedelta

from slack_exporter.config import CONFIG, logger
from slack_exporter.etl import SlackToGoogleDrive, SlackToMega


def export_slack_to_mega(since_days: int = 90):
    SlackToMega(
        local_dir=CONFIG['backup_dir'],
        remote_dir=CONFIG["mega_parent_folder"],
        credentials=CONFIG["mega_credentials"],
        file_suffix=f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        oldest_timestamp=(datetime.now() - timedelta(days=since_days)).timestamp()
    ).run()

def export_slack_to_googledrive(since_days: int = 90):
    SlackToGoogleDrive(
        local_dir=CONFIG['backup_dir'] + f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        remote_dir=CONFIG["google_drive_parent_folder_id"],
        credentials=CONFIG["google_credentials_path"],
        oldest_timestamp=(datetime.now() - timedelta(days=since_days)).timestamp()
    ).run()

if __name__ == "__main__":
    logger.info("=== Starting Slack backup ===")
    # Uncomment the line below to run the Mega.io export
    # export_slack_to_mega()
    # Uncomment the line below to run the Google Drive export
    export_slack_to_googledrive()
    logger.info("=== Slack backup completed ===")
