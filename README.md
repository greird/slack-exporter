# Slack Exporter & Backup

This project automates the backup of Slack workspace files to a local folder, with options to upload the backup folder to Google Drive or Mega.io.

It follows a very simple Extract, Transform, Load process.

1. Extract (download) data from a Slack Workspace into local storage
2. Transform this data, typically sorting and/or compressing files
3. Load (upload) the data into a remote storage (Mega or Google Drive)

This system can be extended to other service simply by subclassing the [ETL](/slack_exporter/etl.py), [Exporter](/slack_exporter/extract/exporter.py) and [Uploader](/slack_exporter/load/uploader.py) classes.


## DISCLAIMER

This project is a work in progress and is meant to run locally. Some of the authentication process is not secure enough.

Gemini CLI and Github Copilot have been used extensively to write the code in this repository, especiall the API interfaces and documentation.

## Installation

1.  **Clone the project**:
    ```bash
    git clone git@github.com:greird/slack-exporter.git
    cd slack-exporter
    ```

2.  **Create a Slack App**:
    Your Slack App should have a Bot Token with the following permissions
    - channels:history
    - channels:read
    - files:read
    - groups:history
    - groups:read
    - links:read

    For a conversation to be part of the export, the Slack App bot should be added to it.

3.  **Configure your Cloud service if needed**
    See [Cloud configuration](#cloud-configuration) section below.

4.  **Create a .env file with the following informationn**
    ```dotenv
    SLACK_BOT_TOKEN=''

    GOOGLE_DRIVE_PARENT_FOLDER='' # this must be the ID as found in the URL of the folder
    GOOGLE_CREDENTIALS_PATH='credentials.json'

    MEGA_PARENT_FOLDER=''
    MEGA_EMAIL=''
    MEGA_PASSWORD=''
    ```

5.  **Edit `main.py` to configure your pipeline**
    Edit the [main.py](/slack_exporter/main.py) file with your own configuration.

6.  **Use Docker or install dependencies manunally.**

    With Docker:
    ```bash
    docker build -t "slack-exporter" .
    docker run slack-exporter
    ```

    With Poetry:
    ```bash
    poetry install
    poetry run python slack_exporter/main.py
    ```

    See [Mega.io Configuration](#megaio-configuration) for MegaCmd installation.

## Cloud configuration

### Google Drive Configuration

To upload files to Google Drive, you need to enable the Google Drive API and obtain credentials.

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new project.
3.  Enable the **Google Drive API** for this project.
4.  Create **OAuth consent screen** credentials.
    - Configure it for **External** use and add your own email address as a test user.
5.  Create new **OAuth client ID** credentials for a **Desktop app**.
6.  Download the JSON file containing your credentials and save it as `./credentials.json` at the root of this directoy.

During the first run, the script will prompt you to authenticate via your browser to authorize access to your Google Drive.

### Mega.io Configuration

To upload files to Mega.io, you need to have `megacmd` [installed](https://github.com/meganz/megacmd) and configured. The `MegaUploader` class relies on `megacmd` being available in your system's PATH and will run `mega-login $MEGA_EMAIL $MEGA_PASSWORD` to authenticate.

## Editing `main.py`

A few preconfiguration exists:
- SlackToGoogleDrive: Export from Slack andupload to Google Drive.
- SlackToMega: Export from Slack and upload to Mega.
- SlackToLocal: Export from Slack and keep the files locally.
- UploadFolderToGoogleDrive: Upload a local folder to Google Drive.

Edit `main.py` to use one of the pre-existing configuration or build a new subclass of ETL.

```py
# main.py
from dotenv import load_dotenv, find_dotenv

from slack_exporter.etl import ETL
from slack_exporter.extract.slack_exporter import SlackExporter
from slack_exporter.load.mega_uploader import MegaUploader

class SlackToMega(ETL):
    def run(self):
        self._extract(SlackExporter())
        self._transform()
        self._load(MegaUploader(self.credentials))

if __name__ == "__main__":

    SlackToMega(
        local_dir="./backup",
        remote_dir="", # upload at root
        credentials={"login": "my_login", "password": "my_password"}
    ).run()

```
