import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

def get_spreadsheet(folder_id, token_path='token.pickle', credentials_path='drive_credentials.json'):
    SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
    creds = None
    drive_service = None
    sheets_service = None

    # OAuth2認証とサービスインスタンスの初期化
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif os.path.exists(credentials_path):
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    if creds and creds.valid:
        drive_service = build('drive', 'v3', credentials=creds)
        sheets_service = build('sheets', 'v4', credentials=creds)
    else:
        print('Drive or Sheets auth failed.')
        return None

    if not drive_service:
        print('Drive service is not available.')
        return None

    results = drive_service.files().list(
        q=f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet'",
        fields='files(id, name)').execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        return items
