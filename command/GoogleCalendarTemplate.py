from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def CalendarPush(eventname, eventdate):
    Calendar_id = os.environ['CALENDAR_ID']
    google_calendar = GoogleCalendar()   # initを実行するために必要
    google_calendar.Add_event(Calendar_id, eventname, eventdate)

def YoutubePush(title, scheduled_start_time_tokyo, youtube_url):
    google_calendar = GoogleCalendar(title, scheduled_start_time_tokyo)   # initを実行するために必要
    Calendar_id = os.environ['CALENDAR_ID']
    google_calendar.Add_Youtube(Calendar_id, youtube_url)

class GoogleCalendar:
    def __init__(self, title, scheduled_start_time_tokyo):
        self.creds = None   # 認証情報の初期化
        if os.path.exists('token.json'):    # credentials.json ファイルに保存された認証情報をロードする
            self.creds = Credentials.from_authorized_user_file('token.json')
        
        # 認証情報(token.json)がない場合や期限切れの場合は、ユーザーに認証を求める
        if not self.creds or not self.creds.valid:   # creds.validはTrueかFalseを返し、切れている場合はFalse
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
        self.title = title
        self.scheduled_start_time_tokyo = scheduled_start_time_tokyo

    def Add_Youtube(self, Calendar_id, youtube_url):
        event_name = self.title
        scheduled_start_time = self.scheduled_start_time_tokyo

        # イベントの情報を辞書形式でまとめる
        event = {
            'summary': event_name,
            'description': youtube_url,
            'start': {
                'dateTime': scheduled_start_time,
                'timeZone': 'Asia/Tokyo'
            },
            'end': {
                'dateTime': scheduled_start_time,
                'timeZone': 'Asia/Tokyo'
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 1},  # 1分前に通知
                    {'method': 'popup', 'minutes': 60},  # 1分前に通知
                ],
            },
        }

        try:
            # Googleカレンダーにイベントを追加
            self.service.events().insert(
                calendarId=Calendar_id,
                body=event
            ).execute()
            print(f"イベントを追加しました: {event_name}")
        except Exception as e:
            print(f"Googleカレンダーへのイベント追加でエラーが発生しました: {str(e)}")
            return event_name, scheduled_start_time