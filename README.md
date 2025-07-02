# Slack Exporter & Backup

This project automates the backup of Slack workspace files to a local folder, with options to upload the backup folder to Google Drive or Mega.io.

## Features

- **History Export**: Retrieves conversation history from public and private channels.
- **Attachment Download**: Iterates through exported history and downloads all referenced attachments.
- **Local Backup**: Organizes exports and attachments into a timestamped backup folder.
- **File Compression**: Compresses large files within the backup folder if they exceed a specified size threshold.
- **Cloud Upload**: Uploads the entire backup folder to either Google Drive or Mega.io, preserving the directory structure.

## Prerequisites

Before you begin, ensure you have the following tools installed:

- **Python >=3.11**
- **Poetry**
- **megacmd** (if using Mega.io for uploads): Command-line tool for Mega.io. Follow the [megacmd installation instructions](https://github.com/meganz/megacmd).
- **Slack Bot Token**

## Installation

1.  **Clone the project**:
    ```bash
    git clone git@github.com:greird/slack-exporter.git
    cd slack-exporter
    ```

2.  **Install Python dependencies**:
    This project uses `Poetry` for dependency management. If you don't have Poetry, install it first. Then, run:
    ```bash
    poetry install
    ```

3.  **Configure environment variables**:
    Create a `.env` file at the root of your project based on the example below. 

    ```dotenv
    SLACK_BOT_TOKEN="YOUR_SLACK_BOT_TOKEN"

    # --- Google Drive Configuration ---
    GOOGLE_DRIVE_PARENT_FOLDER="YOUR_GOOGLE_DRIVE_FOLDER_ID"
    GOOGLE_CREDENTIALS_PATH="./credentials.json"

    # --- Mega.io Configuration ---
    MEGA_PARENT_FOLDER="YOUR_MEGA_FOLDER_ID" # This is the ID of the parent folder on Mega.io
    MEGA_EMAIL="YOUR_MEGA_EMAIL"
    MEGA_PASSWORD="YOUR_MEGA_PASSWORD"
    ```

    - `SLACK_BOT_TOKEN`: Your Slack bot token. [How to get one](https://api.slack.com/authentication/basics).
    - `GOOGLE_DRIVE_PARENT_FOLDER`: The ID of the Google Drive folder where backups will be uploaded.
    - `GOOGLE_CREDENTIALS_PATH`: The path to your Google API credentials file.
    - `MEGA_FOLDER_ID`: The ID of the parent folder on Mega.io where backups will be uploaded.
    - `MEGA_EMAIL`: The email you use to login to your Mega account.
    - `MEGA_PASSWORD`: Your Mega password.

## Cloud configuration

### Google Drive Configuration

To upload files to Google Drive, you need to enable the Google Drive API and obtain credentials.

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new project.
3.  Enable the **Google Drive API** for this project.
4.  Create **OAuth consent screen** credentials.
    - Configure it for **External** use and add your own email address as a test user.
5.  Create new **OAuth client ID** credentials for a **Desktop app**.
6.  Download the JSON file containing your credentials and update your `GOOGLE_CREDENTIALS_PATH` env var accordingly.

During the first run, the script will prompt you to authenticate via your browser to authorize access to your Google Drive.

### Mega.io Configuration

To upload files to Mega.io, you need to have `megacmd` installed and configured. The `MegaUploader` class relies on `megacmd` being available in your system's PATH and will run `mega-login $MEGA_EMAIL $MEGA_PASSWORD` to authenticate.

### Your own

Expand on the [Uploader](/slack_exporter/load/uploader.py) class to create your own Cloud storage configuration.

## Usage

To run one of the existing ETL, use one of these Poetry command.

```bash
poetry run export_slack_to_googledrive
poetry run export_slack_to_mega
```

Edit `main.py` to create your own configuration.

## Project Structure

- `slack_exporter/main.py`: Main endpoints definition.
- `slack_exporter/etl.py`: The main class that orchestrates the entire process: cleanup, export, attachment download, compression, and upload.
- `slack_exporter/config.py`: Configuration settings for Slack API tokens, Google Drive/Mega.io IDs, and file paths.
- `slack_exporter/extract/slack_exporter.py`: Handles Slack API interactions, including fetching channel lists, conversation history, and downloading attachments.
- `slack_exporter/load/google_drive_uploader.py`: Manages uploading files and folders to Google Drive.
- `slack_exporter/load/mega_uploader.py`: Manages uploading files and folders to Mega.io using `megacmd`.
- `slack_exporter/transform/tools.py`: Contains utility functions such as file compression used during the "transform" stage of the pipeline.