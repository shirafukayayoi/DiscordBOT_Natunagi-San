import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv

def get_novel_data(credentials_file='sheet_credentials.json'):
    load_dotenv()
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(credentials_file, scopes=scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(os.getenv('NOVEL_SPREADSHEET_KEY'))
    sheet = spreadsheet.sheet1  # 最初のシートにアクセス

    # シートの全データを取得
    all_data = sheet.get_all_values()
    
    if not all_data:
        return []  # データがない場合は空リストを返す
    
    # ヘッダー行を取得
    headers = all_data[0]
    
    # 必要な列のインデックスを特定
    try:
        title_index = headers.index('タイトル＼巻数')
        url_index = headers.index('URL')
        total_index = headers.index('total')
        sum_index = headers.index('合計')
    except ValueError as e:
        print(f"エラー: 必要なヘッダーが見つかりません。{e}")
        return []

    # データ行から必要な列だけを抽出
    filtered_data = [
        [row[title_index], row[url_index], row[total_index], row[sum_index]]
        for row in all_data[1:]  # 1行目はヘッダーなのでスキップ
    ]
    
    return filtered_data

def get_manga_data(credentials_file='sheet_credentials.json'):
    load_dotenv()
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(credentials_file, scopes=scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(os.getenv('NOVEL_SPREADSHEET_KEY'))
    
    # シートのインデックスを確認して2つ目のシートにアクセス
    sheet = spreadsheet.get_worksheet(1)  # 0が最初のシート、1が2つ目のシート

    # シートの全データを取得
    all_data = sheet.get_all_values()
    
    if not all_data:
        return []  # データがない場合は空リストを返す
    
    # ヘッダー行を取得
    headers = all_data[0]
    
    # 必要な列のインデックスを特定
    try:
        title_index = headers.index('タイトル＼巻数')
        url_index = headers.index('URL')
        total_index = headers.index('total')
        sum_index = headers.index('合計')
    except ValueError as e:
        print(f"エラー: 必要なヘッダーが見つかりません。{e}")
        return []

    # データ行から必要な列だけを抽出
    filtered_data = [
        [row[title_index], row[url_index], row[total_index], row[sum_index]]
        for row in all_data[1:]  # 1行目はヘッダーなのでスキップ
    ]
    
    return filtered_data