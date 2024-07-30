from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def CalendarMain(eventname, eventdate):
    Calendar_id = os.environ['CALENDAR_ID']
    google_calendar = GoogleCalendar(eventname, eventdate)   # initを実行するために必要
    google_calendar.Add_event(Calendar_id)

class GoogleCalendar:
    def __init__(self, eventname, eventdate):
        self.creds = None   # 認証情報の初期化
        if os.path.exists('token.json'):    # credentials.json ファイルに保存された認証情報をロードする
            self.creds = Credentials.from_authorized_user_file('token.json')
        
        # 認証情報(token.json)がない場合や期限切れの場合は、ユーザーに認証を求める
        if not self.creds or not self.creds.valid:   # cerds.validはtrueかfalseを返し、切れている場合はtrue
            if self.creds and self.creds.expired and self.creds.refresh_token:  # tokenがあった場合、期限切れかどうかを確認
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(   # tokenがない場合、認証を行う
                    'Calendar_credentials.json', ['https://www.googleapis.com/auth/calendar.events'])
                self.creds = flow.run_local_server(port=0)
            # 認証情報を保存する
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())   # 認証情報が入っているself.credsをjson形式に変換して保存する
        self.service = build('calendar', 'v3', credentials=self.creds)
        print("Google Calendarに接続しました")
        self.eventname = eventname
        self.eventdete = eventdate

    # Googleカレンダーにイベントを追加する
    def Add_event(self, Calendar_id):
        event_name = self.eventname
        event_date = self.eventdete
        date_obj = datetime.strptime(event_date, '%Y%m%d')
        formatted_date = date_obj.strftime('%Y-%m-%d')
        event = {   # イベントの情報を辞書形式でまとめる
            'summary': event_name,
            'start': {  # 開始時間
                'date': formatted_date,
                'timeZone': 'Asia/Tokyo'
            },
            'end': {    # 終了時間
                'date': formatted_date,
                'timeZone': 'Asia/Tokyo'
            },
        }
        self.service.events().insert(
            calendarId= Calendar_id,
            body=event
        ).execute()
        print(f"イベントを追加しました: {event_name})")