import requests
import time
import json
from pathlib import Path

from config import CONFIG, logger


class SlackExporter:
    def __init__(self):
        self.slack_token = CONFIG["slack_token"]
        self.headers = {"Authorization": f"Bearer {self.slack_token}"}
    
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

    def get_channels_list(self):
        """Retrieves the list of channels"""
        try:
            response = requests.get(
                "https://slack.com/api/users.conversations",
                headers=self.headers
            )
            data = response.json()
            if data.get("ok"):
                return data["channels"]
            else:
                logger.error(f"Erreur API Slack: {data.get('error')}")
                return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des channels: {e}")
            return None
        
    def get_history(self, channel_id: str, limit: int = 15, oldest: str = 0, cursor: str = None, messages: list = None):
        """Retrieves the complete history of a channel with pagination."""
        
        logger.info(f"Retrieving history for channel {channel_id}...")
        if not messages:
            messages = []
        
        try:
            params = {
                "channel": channel_id,
                "limit": limit, 
                "oldest": oldest
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
                        time.sleep(1)  # Attendre 1 seconde entre les requêtes pour être respectueux

                        return self.get_history(
                            channel_id=channel_id,
                            limit=limit,
                            oldest=oldest,
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

    def download_attachments(self, export_path: Path):
        """Downloads attachments from exported Slack messages."""
        logger.info(f"Starting attachment download for {export_path}...")
        
        for json_file in export_path.rglob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                messages = data.get("messages", [])
                
                for message in messages:
                    if "files" in message:
                        for file_info in message["files"]:
                            if "url_private_download" in file_info:
                                download_url = file_info["url_private_download"]
                                file_name = file_info["name"]
                                
                                # Create a directory for attachments within the export folder
                                # e.g., <export_path>/attachments/<channel_name>/
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
