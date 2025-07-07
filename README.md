# Slack Exporter

This project automates the backup of Slack workspace files to a local folder, with options to upload the backup folder to Google Drive or Mega.io.

It follows a very simple Extract, Transform, Load process.

1. Extract (download) data from a Slack Workspace into local storage
2. Transform this data, typically sorting and/or compressing files
3. Load (upload) the data into a remote storage (Mega or Google Drive)

This system can be extended to other service simply by subclassing the [ETL](/slack_exporter/etl.py), [Exporter](/slack_exporter/extract/exporter.py) and [Uploader](/slack_exporter/load/uploader.py) classes.


## DISCLAIMER

This project is a work in progress and is meant to run locally. Some of the authentication process is not secure enough.

Gemini CLI, Github Copilot and Claude have been used extensively to write the code in this repository, especiall the API interfaces and documentation.

## Installation

### 1. Clone the project

```bash
git clone git@github.com:greird/slack-exporter.git
cd slack-exporter
```

### 2. Create a Slack App

Your Slack App should have a Bot Token with the following permissions
- channels:history
- channels:read
- files:read
- groups:history
- groups:read
- links:read

For a conversation to be part of the export, the Slack App bot should be added to it.

### 3. Configure your Cloud service if needed

#### Google Drive

To upload files to Google Drive, you need to enable the Google Drive API and obtain credentials.

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new project.
3.  Enable the **Google Drive API** for this project.
4.  Create **OAuth consent screen** credentials.
    - Configure it for **External** use and add your own email address as a test user.
5.  Create new **OAuth client ID** credentials for a **Desktop app**.
6.  Download the JSON file containing your credentials and save it as `./credentials.json` at the root of this directoy.

During the first run, the script will prompt you to authenticate via your browser to authorize access to your Google Drive.

#### Mega

To upload files to Mega.io, you need to install `megacmd`. If you use Docker you can skip this step as the installation is part of the Dockerfile. 
Otherwise follow the [documentation](https://github.com/meganz/megacmd) to install it manually.

### 4. Create a .env file with the following informationn

```dotenv
SLACK_BOT_TOKEN='YOUR_SLACKBOT_TOKEN'
```

You can also use this method to store your meta and google drive credentials if needed.

### 5. Edit `main.py` to configure your pipeline

Edit [main.py](/slack_exporter/main.py) to use one of the pre-existing configuration or build a new subclass of ETL to create your own.

### 6. Use Docker or install dependencies manunally

#### With Docker

```bash
docker build -t "slack-exporter" .
docker run slack-exporter
```

#### Without Docker

Use Poetry to install python dependencies
```bash
poetry install
poetry run python slack_exporter/main.py
```

Or use pip/pipx to install dependencies from [requirements.txt](requirements.txt).
