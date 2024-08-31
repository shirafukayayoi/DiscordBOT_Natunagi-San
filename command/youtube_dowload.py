from yt_dlp import YoutubeDL
import os

def YoutubeDownload(url):
    # オプション
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # 最良の画質と音質をダウンロード
        'outtmpl': 'Download/video.%(ext)s'  # ダウンロードファイル名
    }
    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)  # 情報を取得するがダウンロードはしない
        title = info_dict.get('title', None)
        ext = info_dict.get('ext', 'webm')
        file_path = f"Download/video.{ext}"
        
        # 実際にダウンロードを行う
        ydl.download(url)
        print(f"ダウンロード完了: {file_path}")
    # ダウンロードしたファイルのパスを返す
    return file_path, title