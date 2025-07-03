import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from slack_exporter.load.uploader import Uploader
from slack_exporter.logger_config import logger


class GoogleDriveUploader(Uploader):
    """This class handles uploading files to Google Drive using the Google Drive API.

    Attributes:
        credentials (str): The path to the OAuth 2.0 credentials JSON file.
    """

    def __init__(self, credentials: str = './credentials.json'):
        super().__init__(credentials)

    def authenticate(self, credentials: str) -> bool:
        """This method uses OAuth 2.0 to authenticate the user and obtain credentials.
        It checks for existing credentials in 'token.json' and refreshes them if necessary.
        If no valid credentials are found, it prompts the user to log in and authorizes the application.

        Returns:
            bool: True if authentication was successful, False otherwise.
        """
        try:
            SCOPES = ['https://www.googleapis.com/auth/drive.file']
            
            creds = None
            token_path = 'token.json'
            
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(credentials, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('drive', 'v3', credentials=creds)
            return True
            
        except Exception as e:
            logger.error(f"Google Drive configuration error: {e}")
            return False
    
    def upload_folder(self, local_folder_path: Path, remote_folder_id: str) -> bool:
        """Uploads a folder and its structure to Google Drive"""
        logger.info(f"Authenticating to Google Drive...")
        if not self.authenticate():
            logger.error("Authentication failed. Cannot upload to Google Drive.")
            return False

        try:

            # Check if the provided local_folder_path exists on Google Drive and return its ID
            root_folder_id = self._find_folder_id_by_name(local_folder_path.name, remote_folder_id)
            if not root_folder_id:
                logger.error(f"Local folder {local_folder_path} does not exist on Google Drive.")
                
                # Create the root folder on Drive
                root_folder_metadata = {
                    'name': str(local_folder_path),
                    'parents': [remote_folder_id],
                    'shared_drive_id': remote_folder_id if remote_folder_id else None,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                root_folder = self.service.files().create(body=root_folder_metadata, fields='id').execute()
                root_folder_id = root_folder.get('id')

                logger.info(f"Created folder on Google Drive: {root_folder_id}")

            else:
                logger.info(f"Found remote folder ID: {root_folder_id}")

            # map local paths to Drive folder IDs
            path_to_drive_id = {str(local_folder_path.resolve()): root_folder_id}

            logger.info("Creating folder structure on Google Drive...")
            for root, dirs, _ in os.walk(local_folder_path):
                resolved_root = str(Path(root).resolve())
                parent_folder_id = path_to_drive_id[resolved_root]
                

                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    resolved_dir_path = str(Path(dir_path).resolve())

                    folder_metadata = {
                        'name': dir_name,
                        'parents': [parent_folder_id],
                        'mimeType': 'application/vnd.google-apps.folder',
                        'supportsAllDrives': True
                    }
                    folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                    new_folder_id = folder.get('id')
                    path_to_drive_id[resolved_dir_path] = new_folder_id
                    logger.info(f"Folder created on Drive: {new_folder_id}")

            logger.info("Uploading files...")
            for root, _, files in os.walk(local_folder_path):
                resolved_root = str(Path(root).resolve())
                parent_folder_id = path_to_drive_id[resolved_root]

                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    
                    file_metadata = {
                        'name': file_name,
                        'parents': [parent_folder_id]
                    }
                    
                    media = MediaFileUpload(file_path, resumable=True)
                    self.service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields='id'
                    ).execute()
                    
                    relative_path = os.path.relpath(file_path, local_folder_path)
                    logger.info(f"File uploaded: {relative_path}")
            
            logger.info(f"Full folder uploaded to Google Drive: {remote_folder_id}")
            return True
            
        except Exception as e:
            logger.error(f"Google Drive upload error: {e}")
            return False

    def _find_folder_id_by_name(self, folder_name: str, parent_id: str = None) -> str | None:
        """Finds the ID of a folder by its name in Google Drive and within a given parent_id"""
        if not self.service:
            logger.error("Google Drive service not initialized. Please authenticate first.")
            return None
        
        query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}'"
        if parent_id:
            query += f" and '{parent_id}' in parents"

        response = self.service.files().list(q=query, fields='files(id)').execute()

        folders = response.get('files', [])

        return folders[0].get('id') if folders else None
    