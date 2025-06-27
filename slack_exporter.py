import requests

from config import CONFIG, logger


class SlackExporter:
    def __init__(self):
        self.slack_token = CONFIG["slack_token"]
        self.headers = {"Authorization": f"Bearer {self.slack_token}"}
    
    def get_workspace_info(self):
        """Récupère les informations du workspace"""
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
        """Récupère la liste des channels"""
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