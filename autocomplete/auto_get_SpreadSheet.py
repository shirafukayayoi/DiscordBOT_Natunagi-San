import pickle
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import discord
from discord import app_commands
from typing import List
from dotenv import load_dotenv

async def autocomplete_getspreadsheet(
    interaction: discord.Interaction,
    current: str
) -> List[app_commands.Choice[str]]:
    load_dotenv()
    drive = GoogleDriveAuth()
    spreadsheets = drive.get_spreadsheet(os.getenv('BOOKWALKER_FOLDER_ID'))
    
    # 取得したスプレッドシートの名前を fruits に追加
    choices = []
    for spreadsheet in spreadsheets:
        if current.lower() in spreadsheet['name'].lower():
            choices.append(app_commands.Choice(name=spreadsheet['name'], value=spreadsheet['name']))
    return choices

class GoogleDriveAuth:
    SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']

    def __init__(self, token_path='token.pickle', credentials_path='drive_credentials.json'):
        self.token_path = token_path
        self.credentials_path = credentials_path
        self.creds = None
        self.drive_service = None
        self.sheets_service = None

        # OAuth2認証とサービスインスタンスの初期化
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            elif os.path.exists(self.credentials_path):
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            with open(self.token_path, 'wb') as token:
                pickle.dump(self.creds, token)

        if self.creds and self.creds.valid:
            self.drive_service = build('drive', 'v3', credentials=self.creds)
            self.sheets_service = build('sheets', 'v4', credentials=self.creds)
        else:
            print('GoogleDriveに接続できませんでした。')

    def get_spreadsheet(self, folder_id):
        if not self.drive_service:
            print('Drive service is not available.')
            return []

        results = self.drive_service.files().list(
            q=f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet'",
            fields='files(id, name)').execute()
        items = results.get('files', [])

        if not items:
            print('No files found.')
        else:
            return items