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

Before you begin, ensure you have the following prerequisites:

- **Python >=3.11**
- **Poetry**
- **megacmd** (if using Mega.io for uploads): Command-line tool for Mega.io. 
- **Slack Bot Token**

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
3. **Create a Slack App**:
    Your Slack App should have a Bot Token with the following permissions
    - channels:history
    - channels:read
    - files:read
    - groups:history
    - groups:read
    - links:read

    For a conversation to be part of the export, the Slack App bot should be added to it.

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

## Usage

To run one of the existing ETL, edit and run `slack_exporter/main.py`.

```bash
python slack_exporter/main.py
```

Or create your own pipeline. 
Below is an example implementation to export all data from Slack, process them and upload them to Mega.

```py
# main.py

from slack_exporter.etl import ETL
from slack_exporter.extract.slack_exporter import SlackExporter

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
