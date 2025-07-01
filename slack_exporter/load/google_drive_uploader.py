import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from slack_exporter.config import logger
from slack_exporter.load.uploader import Uploader


class GoogleDriveUploader(Uploader):
    def __init__(self, credentials: str):
        self.credentials = credentials
        super().__init__(credentials=self.credentials)

    def authenticate(self) -> bool:
        """Configures Google Drive credentials"""
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
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('drive', 'v3', credentials=creds)
            return True
            
        except Exception as e:
            logger.error(f"Google Drive configuration error: {e}")
            return False
    
    def upload_folder(self, local_folder_path, remote_folder_id):
        """Uploads a folder and its structure to Google Drive"""
        logger.info(f"Authenticating to Google Drive...")
        if not self.authenticate():
            logger.error("Authentication failed. Cannot upload to Google Drive.")
            return False

        try:
            # Créer le dossier racine pour cette sauvegarde sur Drive
            root_folder_metadata = {
                'name': remote_folder_id,
                'parents': ['1tTgu6ObGVESuGMD9Gj4d_qFWpxB5Kfpw'],
                'mimeType': 'application/vnd.google-apps.folder'
            }
            root_folder = self.service.files().create(body=root_folder_metadata, fields='id').execute()
            root_folder_id = root_folder.get('id')

            # Dictionnaire pour mapper les chemins locaux aux IDs de dossier Drive
            path_to_drive_id = {str(Path(local_folder_path).resolve()): root_folder_id}

            # 1. Créer l'arborescence des dossiers sur Google Drive
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
                        'mimeType': 'application/vnd.google-apps.folder'
                    }
                    folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                    new_folder_id = folder.get('id')
                    path_to_drive_id[resolved_dir_path] = new_folder_id
                    logger.info(f"Folder created on Drive: {os.path.relpath(dir_path, local_folder_path)}")

            # 2. Uploader les fichiers dans les bons dossiers
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