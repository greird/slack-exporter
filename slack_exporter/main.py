from datetime import datetime, timedelta

from slack_exporter.config import CONFIG, logger
from slack_exporter.etl import SlackToGoogleDrive, SlackToMega


def export_slack_to_mega():
    logger.info("=== Starting Slack backup ===")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info(f"Local backup directory: {CONFIG['backup_dir']}")

    export_slack_to_mega = SlackToMega(
        local_dir=CONFIG['backup_dir'],
        remote_dir=CONFIG["mega_parent_folder"],
        credentials=CONFIG["mega_credentials"],
        file_suffix=f"_{timestamp}",
        oldest_timestamp=(datetime.now() - timedelta(days=30)).timestamp()
    )
    export_slack_to_mega.run()

def export_slack_to_googledrive():
    logger.info("=== Starting Slack backup ===")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info(f"Local backup directory: {CONFIG['backup_dir']}")

    export_slack_to_googledrive = SlackToGoogleDrive(
        local_dir=CONFIG['backup_dir'] + f"_{timestamp}",
        remote_dir=CONFIG["google_drive_parent_folder_id"],
        credentials=CONFIG["google_credentials_path"],
        oldest_timestamp=(datetime.now() - timedelta(days=90)).timestamp()
    )
    export_slack_to_googledrive.run()
