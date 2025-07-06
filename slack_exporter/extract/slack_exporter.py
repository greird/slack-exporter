import json
import os
import time
from pathlib import Path

import requests

from slack_exporter.extract.exporter import Exporter
from slack_exporter.logger_config import logger

class SlackExporter(Exporter):
    """Class to export Slack channels history and files.

    This class handles authentication, retrieving channel lists, fetching channel history,
    and downloading attachments from Slack channels.
        
    Methods:
        authenticate(): Authenticates the Slack API using the bot token.
        get_workspace_info(): Retrieves workspace information.
        get_channels_list(): Retrieves the list of channels in the workspace.
        get_channel_history(channel_id, limit=15, cursor=None, messages=None): Retrieves the complete history of a channel with pagination.
        download_attachments(): Downloads attachments from exported Slack messages.
        export(): Exports all channels history and files."""

    def __init__(self):
        super().__init__()

    def authenticate(self) -> bool:
        """Authenticates the Slack API using the bot token."""

        self.slack_token = os.getenv("SLACK_BOT_TOKEN")
        self.headers = {"Authorization": f"Bearer {self.slack_token}"}

        if not self.slack_token:
            raise ValueError("SLACK_BOT_TOKEN environment variable is not set.")

        try:
            response = requests.get(
                "https://slack.com/api/auth.test",
                headers=self.headers
            )
            data = response.json()
            if data.get("ok"):
                logger.info("Slack authentication successful.")
                return True
            else:
                logger.error(f"Slack authentication failed: {data.get('error')}")
                return False
        except Exception as e:
            logger.error(f"Error during Slack authentication: {e}")
            return False
    
    def get_workspace_info(self):
        """Retrieves workspace information"""
        try:
            response = requests.get(
                "https://slack.com/api/team.info",
                headers=self.headers
            )
            data = response.json()
            if data.get("ok"):
                return data["team"]
            else:
                logger.error(f"Erreur API Slack: {data.get('error')}")
                return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos workspace: {e}")
            return None

    def get_channels_list(self) -> list:
        """Retrieves the list of channels"""
        channels = []

        try:
            response = requests.get(
                "https://slack.com/api/users.conversations",
                headers=self.headers
            )
            data = response.json()

            if data.get("ok"):
                channels = data["channels"]
            else:
                logger.error(f"Erreur API Slack: {data.get('error')}")

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des channels: {e}")

        return channels
        
    def get_channel_history(
            self, 
            channel_id: str, 
            limit: int = 15, 
            cursor: str = None, 
            messages: list = None,
            oldest_timestamp: float = 0
        ) -> dict:
        """Retrieves the complete history of a channel with pagination.

        Args:
            channel_id (str): The ID of the channel to retrieve history from.
            limit (int): The maximum number of messages to retrieve per request.
            cursor (str): The cursor for pagination, if any.
            messages (list): A list to accumulate messages across multiple requests.    
            oldest_timestamp (float): The timestamp to start retrieving messages from.

        Returns:
            dict: A dictionary containing the messages and a boolean indicating if there are more messages to retrieve.
        """

        logger.info(f"Retrieving history for channel {channel_id}...")
        if not messages:
            messages = []
        
        try:
            params = {
                "channel": channel_id,
                "limit": limit, 
                "oldest": oldest_timestamp
            }
            if cursor:
                params["cursor"] = cursor

            response = requests.get(
                "https://slack.com/api/conversations.history",
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 429: # Rate limited
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Waiting for {retry_after} seconds...")
                time.sleep(retry_after)


            response.raise_for_status()
            data = response.json()

            if data.get("ok"):
                messages.extend(data.get("messages", []))
                
                if data.get("has_more"):
                    cursor = data.get("response_metadata", {}).get("next_cursor")

                    if cursor:
                        logger.info(f"Next page for channel {channel_id}...")
                        time.sleep(1)

                        return self.get_history(
                            channel_id=channel_id,
                            limit=limit,
                            oldest=oldest_timestamp,
                            cursor=cursor,
                            messages=messages
                        )
                
                    else:
                        logger.warning("has_more is true, but no next_cursor found. Stopping pagination.")

            else:
                logger.error(f"Slack API error for channel {channel_id}: {data.get('error')}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error while retrieving history for {channel_id}: {e}")

        except Exception as e:
            logger.error(f"Unexpected error in get_history for {channel_id}: {e}")

        logger.info(f"{len(messages)} messages retrieved for channel {channel_id}.")
        return {"ok": True, "messages": messages, "has_more": False}

    def download_attachments(self, export_path: Path, file_suffix: str = None) -> None:
        """Downloads attachments from exported Slack messages.

        This method iterates through all JSON files in the export path, checks for messages with attachments,
        and downloads each attachment to a corresponding directory named after the channel.
        The downloaded files will have a suffix added before the file extension if specified.
        
        Args:
            export_path (Path): The path where the exported data is stored.
            file_suffix (str): A suffix to add to the filenames of downloaded attachments.
        """

        logger.info(f"Starting attachment download for {export_path}...")

        for json_file in export_path.rglob("*.json"):
            if json_file.name == "channels.json":
                continue

            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                messages = data.get("messages", [])
                
                for message in messages:
                    if "files" in message:
                        for file_info in message["files"]:
                            if "url_private_download" in file_info:
                                download_url = file_info["url_private_download"]

                                # Insert file_suffix before the file extension
                                original_name = file_info["name"]
                                if file_suffix:
                                    if "." in original_name:
                                        basename, extension = original_name.rsplit(".", 1)
                                        file_name = basename + file_suffix + "." + extension
                                    else:
                                        file_name = original_name + file_suffix
                                else:
                                    file_name = original_name

                                relative_path = json_file.relative_to(export_path)
                                channel_name = relative_path.stem

                                attachment_dir = export_path / channel_name
                                attachment_dir.mkdir(parents=True, exist_ok=True)
                                
                                file_path = attachment_dir / file_name
                                
                                try:
                                    response = requests.get(download_url, headers=self.headers, stream=True)
                                    response.raise_for_status()
                                    
                                    with open(file_path, 'wb') as f_out:
                                        for chunk in response.iter_content(chunk_size=8192):
                                            f_out.write(chunk)
                                    logger.info(f"Downloaded attachment: {file_path}")
                                    
                                except requests.exceptions.RequestException as e:
                                    logger.error(f"Error downloading {file_name} from {download_url}: {e}")
                                except Exception as e:
                                    logger.error(f"Unexpected error saving {file_name}: {e}")
            except Exception as e:
                logger.error(f"Error processing JSON file {json_file}: {e}")
        
        logger.info("Attachment download complete.")

    def export(self, 
               export_path: Path, 
               file_suffix: str = None, 
               oldest_timestamp: float = None
        ) -> Path | None:
        """Exports all channels history and files.

        Args:
            export_path (Path): The path where the exported data will be saved.
            file_suffix (str): A suffix to add to the filenames of downloaded attachments.
            oldest_timestamp (float): The timestamp to start retrieving messages from.

        Returns:
            Path | None: The path to the exported data or None if the export failed.
        """

        logger.info(f"Creating export at {export_path}...")

        if not export_path.exists():
            export_path.mkdir(parents=True, exist_ok=True)

        workspace_info = self.get_workspace_info()
        if not workspace_info:
            raise RuntimeError("Failed to retrieve workspace information. Please check your Slack token and permissions.")

        channels = self.get_channels_list()
        if not channels:
            raise RuntimeWarning("No channels found in the workspace. Please check your Slack token and permissions.")

        for channel in channels:
            channel_id = channel["id"]
            channel_name = channel["name"]
            logger.info(f"Exporting channel: {channel_name} ({channel_id})")

            history = self.get_channel_history(
                channel_id=channel_id, 
                oldest_timestamp=oldest_timestamp
                )

            if not history.get("ok"):
                logger.error(f"Failed to retrieve history for channel {channel_name}: {history.get('error')}")
                continue

            channel_export_path = export_path / f"{channel_name}.json"
            with open(channel_export_path, 'w') as f:
                json.dump(history, f, indent=4)
            
            logger.info(f"Channel {channel_name} exported to {channel_export_path}")

        self.download_attachments(export_path, file_suffix)

        logger.info("Export completed successfully.")

        return export_path
