from yt_dlp import YoutubeDL
import os

def YoutubeDownload(url):
    # オプション
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # 最良の画質と音質をダウンロード
        'outtmpl': 'Download/video.%(ext)s',  # ダウンロードファイル名
        'postprocessors': [{  # MP4に変換するためのオプション
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',  # MP4形式に変換
        }],
        'postprocessor_args': [
            '-crf', '18',  # クオリティ設定 (数値が低いほど高品質)
        ],
        'prefer_ffmpeg': True,  # FFmpegを使用して変換
    }
    
    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)  # 情報を取得し、ダウンロードも行う
        title = info_dict.get('title', None)
        file_path = ydl.prepare_filename(info_dict)  # ダウンロードしたファイルのパス
        
        print(f"ダウンロード完了: {file_path}")
        
    # ダウンロードしたファイルのパスを返す
    return file_path, title
